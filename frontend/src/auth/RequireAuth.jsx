import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";

export function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="centered-loader">A carregar…</div>;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return children;
}

export function RequireAdmin({ children }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  if (loading) return <div className="centered-loader">A carregar…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/" replace />;
  return children;
}
