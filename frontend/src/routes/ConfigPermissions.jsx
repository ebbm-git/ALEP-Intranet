import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adminQueryKeys,
  bulkReplacePermissions,
  fetchPermissions,
  fetchTree,
  queryKeys,
} from "../services/queries.js";

const NON_ADMIN_ROLES = [
  { value: "editor_chief", label: "Editor Principal", capability: "ler + editar + apagar" },
  { value: "editor_a", label: "Editor A", capability: "ler + editar" },
  { value: "editor_b", label: "Editor B", capability: "ler + editar" },
  { value: "viewer", label: "Visualizador", capability: "ler" },
];

function flattenTree(nodes, depth = 0, out = []) {
  for (const n of nodes) {
    out.push({ id: n.id, title: n.title, depth });
    if (n.children?.length) flattenTree(n.children, depth + 1, out);
  }
  return out;
}

export default function ConfigPermissions() {
  const qc = useQueryClient();
  const { data: tree = [], isLoading: lt } = useQuery({
    queryKey: queryKeys.tree,
    queryFn: fetchTree,
  });
  const { data: existing = [], isLoading: lp } = useQuery({
    queryKey: adminQueryKeys.permissions,
    queryFn: fetchPermissions,
  });

  // Local grid state: Set of "role|page_id" strings = has access.
  const [grid, setGrid] = useState(new Set());
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (!existing) return;
    setGrid(new Set(existing.map((p) => `${p.role}|${p.page_id}`)));
    setDirty(false);
  }, [existing]);

  const flatPages = useMemo(() => flattenTree(tree), [tree]);

  const toggle = (role, pageId) => {
    const key = `${role}|${pageId}`;
    const copy = new Set(grid);
    if (copy.has(key)) copy.delete(key);
    else copy.add(key);
    setGrid(copy);
    setDirty(true);
  };

  const saveAll = useMutation({
    mutationFn: () => {
      const cells = [];
      for (const page of flatPages) {
        for (const r of NON_ADMIN_ROLES) {
          cells.push({
            role: r.value,
            page_id: page.id,
            has_access: grid.has(`${r.value}|${page.id}`),
          });
        }
      }
      return bulkReplacePermissions(cells);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adminQueryKeys.permissions });
      setDirty(false);
    },
  });

  if (lt || lp) return <p>A carregar grelha…</p>;

  return (
    <div className="config-body">
      <p className="muted">
        Marque na grelha que páginas cada papel pode aceder. O tipo de acesso
        (ler / editar / apagar) é determinado pelo papel — esta grelha define
        apenas <em>onde</em> cada papel pode aplicar essa capacidade.
        O <strong>Administrador</strong> tem acesso implícito a tudo e não é
        configurável aqui.
      </p>

      <div className="permissions-toolbar">
        <button
          className="btn primary"
          onClick={() => saveAll.mutate()}
          disabled={!dirty || saveAll.isPending}
        >
          {saveAll.isPending ? "A guardar…" : dirty ? "Guardar alterações" : "Sem alterações"}
        </button>
        {saveAll.isError && (
          <span className="error">Erro: {saveAll.error.message}</span>
        )}
        {saveAll.isSuccess && !dirty && (
          <span className="muted">Guardado ✓</span>
        )}
      </div>

      <div className="permissions-wrapper">
        <table className="permissions-grid">
          <thead>
            <tr>
              <th className="page-col">Página</th>
              {NON_ADMIN_ROLES.map((r) => (
                <th key={r.value} title={r.capability}>
                  <div>{r.label}</div>
                  <div className="role-cap">{r.capability}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {flatPages.map((p) => (
              <tr key={p.id} className={p.depth === 0 ? "top-level" : ""}>
                <td className="page-col" style={{ paddingLeft: 0.5 + p.depth * 1.5 + "rem" }}>
                  {p.depth > 0 && <span className="tree-marker">↳</span>}
                  {p.title}
                </td>
                {NON_ADMIN_ROLES.map((r) => {
                  const key = `${r.value}|${p.id}`;
                  const checked = grid.has(key);
                  return (
                    <td key={r.value} className="cell">
                      <label className="cell-toggle">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggle(r.value, p.id)}
                        />
                      </label>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
