import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminQueryKeys,
  createUser,
  deleteUser,
  fetchAdminUsers,
  updateUserRole,
} from "../services/queries.js";
import { useAuth } from "../auth/AuthContext.jsx";

const ROLES = [
  { value: "admin", label: "Administrador" },
  { value: "editor_chief", label: "Editor Principal (edita + apaga)" },
  { value: "editor_a", label: "Editor A (edita)" },
  { value: "editor_b", label: "Editor B (edita)" },
  { value: "viewer", label: "Visualizador (só leitura)" },
];

export default function ConfigUsers() {
  const { profile: currentProfile } = useAuth();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const { data: users = [], isLoading, isError, error } = useQuery({
    queryKey: adminQueryKeys.users,
    queryFn: fetchAdminUsers,
  });

  const changeRole = useMutation({
    mutationFn: updateUserRole,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminQueryKeys.users }),
  });

  const remove = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: adminQueryKeys.users }),
  });

  if (isLoading) return <p>A carregar utilizadores…</p>;
  if (isError) return <p className="error">Erro: {error.message}</p>;

  return (
    <div className="config-body">
      <div className="config-actions-bar">
        <p className="muted">
          {users.length} utilizador{users.length === 1 ? "" : "es"} registado
          {users.length === 1 ? "" : "s"}.
        </p>
        <button className="btn primary" onClick={() => setShowCreate(true)}>
          + Novo utilizador
        </button>
      </div>

      <table className="config-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Nome</th>
            <th>Papel</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.user_id}>
              <td>
                {u.email}
                {u.user_id === currentProfile?.user_id && (
                  <span className="muted small"> (você)</span>
                )}
              </td>
              <td>{u.full_name || <span className="muted">—</span>}</td>
              <td>
                <select
                  value={u.role}
                  onChange={(e) =>
                    changeRole.mutate({ userId: u.user_id, role: e.target.value })
                  }
                  disabled={changeRole.isPending}
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                {u.user_id !== currentProfile?.user_id && (
                  <button
                    className="btn small danger"
                    onClick={() => {
                      if (
                        confirm(
                          `Remover o perfil de ${u.email}? (A conta no Supabase Auth não é apagada — só o perfil local. O utilizador volta a ser criado como Visualizador se voltar a entrar.)`,
                        )
                      ) {
                        remove.mutate(u.user_id);
                      }
                    }}
                    disabled={remove.isPending}
                  >
                    Remover
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {showCreate && (
        <CreateUserDialog
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            qc.invalidateQueries({ queryKey: adminQueryKeys.users });
            setShowCreate(false);
          }}
        />
      )}
    </div>
  );
}

function CreateUserDialog({ onClose, onCreated }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await createUser({ email, password, fullName, role });
      onCreated();
    } catch (err) {
      const detail =
        err?.response?.data?.detail || err?.message || "Erro a criar utilizador";
      setError(detail);
    } finally {
      setBusy(false);
    }
  };

  const generatePassword = () => {
    const chars = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    const len = 14;
    const arr = new Uint32Array(len);
    crypto.getRandomValues(arr);
    setPassword(Array.from(arr, (n) => chars[n % chars.length]).join(""));
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-panel modal-narrow"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          <h2>Novo utilizador</h2>
          <button className="btn small ghost" onClick={onClose}>
            ✕
          </button>
        </header>
        <form className="modal-body create-user-form" onSubmit={submit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </label>
          <label>
            <span>Nome completo</span>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </label>
          <label>
            <span>Palavra-passe inicial</span>
            <div className="password-row">
              <input
                type="text"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="ex.: TempPa55!"
              />
              <button type="button" className="btn small" onClick={generatePassword}>
                Gerar
              </button>
            </div>
            <span className="muted small">
              O utilizador pode trocar depois via reset de palavra-passe.
            </span>
          </label>
          <label>
            <span>Papel</span>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          {error && <p className="auth-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn ghost" onClick={onClose} disabled={busy}>
              Cancelar
            </button>
            <button type="submit" className="btn primary" disabled={busy}>
              {busy ? "A criar…" : "Criar utilizador"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
