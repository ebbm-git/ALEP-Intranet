import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const ROLE_LABELS = {
  admin: "Administrador",
  editor_chief: "Editor Principal",
  editor_a: "Editor A",
  editor_b: "Editor B",
  viewer: "Visualizador",
};

export default function UserMenu() {
  const { profile, signOut, isAdmin } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  if (!profile) return null;

  const initials = (profile.full_name || profile.email || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");

  return (
    <div className="user-menu" ref={ref}>
      <button
        className="user-menu-avatar"
        onClick={() => setOpen((v) => !v)}
        title={profile.email}
      >
        {initials || "U"}
      </button>
      {open && (
        <div className="user-menu-dropdown">
          <div className="user-menu-info">
            <strong>{profile.full_name || profile.email}</strong>
            <div className="muted small">{profile.email}</div>
            <div className="user-role">{ROLE_LABELS[profile.role] || profile.role}</div>
          </div>
          {isAdmin && (
            <Link
              to="/configuracoes"
              className="user-menu-link"
              onClick={() => setOpen(false)}
            >
              ⚙️ Configurações
            </Link>
          )}
          <button
            className="user-menu-link danger"
            onClick={() => {
              setOpen(false);
              signOut();
            }}
          >
            Terminar sessão
          </button>
        </div>
      )}
    </div>
  );
}
