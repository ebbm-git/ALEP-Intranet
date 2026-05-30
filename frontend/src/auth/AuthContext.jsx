import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { supabase } from "../services/supabase.js";
import { api } from "../services/api.js";

const AuthContext = createContext(null);

/**
 * Wraps the app and tracks:
 * - session (from Supabase Auth) — null until we've checked
 * - profile  (from our backend /auth/me) — { user_id, email, role, full_name, accessible_page_ids[] }
 *
 * Re-fetches the profile whenever the session changes (login, logout, refresh).
 */
export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setProfile(data);
    } catch (e) {
      setProfile(null);
    }
  }, []);

  useEffect(() => {
    // Initial session check.
    let mounted = true;
    supabase.auth.getSession().then(async ({ data }) => {
      if (!mounted) return;
      setSession(data?.session ?? null);
      if (data?.session) await loadProfile();
      setLoading(false);
    });
    // React to login/logout/refresh.
    const { data: listener } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      setSession(newSession);
      if (newSession) await loadProfile();
      else setProfile(null);
    });
    return () => {
      mounted = false;
      listener?.subscription?.unsubscribe?.();
    };
  }, [loadProfile]);

  const signIn = useCallback(async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }, []);

  const signUp = useCallback(async (email, password, fullName) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName || null } },
    });
    if (error) throw error;
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setProfile(null);
  }, []);

  const accessiblePageIds = useMemo(
    () => new Set(profile?.accessible_page_ids ?? []),
    [profile],
  );

  const value = useMemo(
    () => ({
      session,
      profile,
      loading,
      isAuthenticated: !!session && !!profile,
      isAdmin: profile?.role === "admin",
      canEdit:
        profile?.role === "admin" ||
        profile?.role === "editor_chief" ||
        profile?.role === "editor_a" ||
        profile?.role === "editor_b",
      canDelete: profile?.role === "admin" || profile?.role === "editor_chief",
      accessiblePageIds,
      signIn,
      signUp,
      signOut,
      refreshProfile: loadProfile,
    }),
    [session, profile, loading, accessiblePageIds, signIn, signUp, signOut, loadProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

/** True iff the user can edit blocks on the given page (admin OR editor with access). */
export function useCanEditPage(pageId) {
  const { profile, isAdmin, canEdit, accessiblePageIds } = useAuth();
  if (!profile) return false;
  if (isAdmin) return true;
  return canEdit && accessiblePageIds.has(pageId);
}

/** True iff the user can delete blocks on the given page (admin OR editor_chief with access). */
export function useCanDeletePage(pageId) {
  const { profile, isAdmin, canDelete, accessiblePageIds } = useAuth();
  if (!profile) return false;
  if (isAdmin) return true;
  return canDelete && accessiblePageIds.has(pageId);
}
