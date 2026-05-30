import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminQueryKeys,
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
      <p className="muted">
        Cada utilizador no Supabase Auth ganha automaticamente um perfil ao
        autenticar-se pela primeira vez. O primeiro utilizador da plataforma
        torna-se <strong>Administrador</strong> automaticamente.
      </p>
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
              <td>{u.email}</td>
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
    </div>
  );
}
