import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await signIn(email, password);
      const redirectTo = loc.state?.from || "/";
      nav(redirectTo, { replace: true });
    } catch (err) {
      setError(err?.message || "Falha ao iniciar sessão");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>ALEP Intranet</h1>
        <p className="muted">Iniciar sessão</p>
        <label>
          <span>Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          <span>Palavra-passe</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "A entrar…" : "Entrar"}
        </button>
        <p className="muted small">
          Sem conta? <Link to="/signup">Criar conta</Link>
        </p>
      </form>
    </div>
  );
}
