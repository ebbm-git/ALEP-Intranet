import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Signup() {
  const { signUp } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await signUp(email, password, fullName);
      setDone(true);
    } catch (err) {
      setError(err?.message || "Falha ao criar conta");
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>Conta criada</h1>
          <p>
            Verifica o teu email <strong>{email}</strong> para confirmar.
            Após confirmar, faz <Link to="/login">login</Link>.
          </p>
          <p className="muted small">
            (Se for o primeiro utilizador da plataforma, serás promovido
            automaticamente a administrador na primeira sessão.)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Criar Conta</h1>
        <label>
          <span>Nome completo</span>
          <input
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </label>
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
            autoComplete="new-password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "A criar…" : "Criar conta"}
        </button>
        <p className="muted small">
          Já tens conta? <Link to="/login">Iniciar sessão</Link>
        </p>
      </form>
    </div>
  );
}
