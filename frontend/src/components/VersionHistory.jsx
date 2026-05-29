import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchVersions,
  restoreVersion,
  queryKeys,
} from "../services/queries.js";
import MarkdownView from "./MarkdownView.jsx";

const fmtDate = (iso) => {
  try {
    return new Date(iso).toLocaleString("pt-PT", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
};

export default function VersionHistory({ blockId, pagePath, onClose }) {
  const qc = useQueryClient();
  const { data: versions = [], isLoading, isError, error } = useQuery({
    queryKey: queryKeys.versions(blockId),
    queryFn: () => fetchVersions(blockId),
  });

  const [selectedVersion, setSelectedVersion] = useState(null);

  // Auto-select the most recent non-current version (the "previous" one)
  // when the list loads, so the preview pane has something useful by default.
  useEffect(() => {
    if (selectedVersion !== null) return;
    const candidate =
      versions.find((v) => !v.is_current) || versions[0] || null;
    if (candidate) setSelectedVersion(candidate);
  }, [versions, selectedVersion]);

  const restore = useMutation({
    mutationFn: ({ version }) => restoreVersion({ blockId, version }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.page(pagePath) });
      qc.invalidateQueries({ queryKey: queryKeys.versions(blockId) });
      onClose();
    },
  });

  // ESC to close
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>Histórico da Secção</h2>
          <button className="btn small ghost" onClick={onClose} title="Fechar">
            ✕
          </button>
        </header>

        {isLoading && <p className="modal-body">A carregar versões…</p>}
        {isError && (
          <p className="modal-body error">
            Erro a carregar versões: {error?.message}
          </p>
        )}

        {!isLoading && !isError && (
          <div className="version-layout">
            <aside className="version-list">
              <p className="version-list-hint">
                Até 5 versões são guardadas por secção. Versões mais antigas
                são automaticamente apagadas.
              </p>
              <ul>
                {versions.map((v) => (
                  <li key={v.id}>
                    <button
                      className={
                        "version-row" +
                        (selectedVersion?.id === v.id ? " selected" : "") +
                        (v.is_current ? " current" : "")
                      }
                      onClick={() => setSelectedVersion(v)}
                    >
                      <div className="version-row-top">
                        <span className="version-tag">v{v.version}</span>
                        {v.is_current && (
                          <span className="version-current-badge">actual</span>
                        )}
                      </div>
                      <div className="version-row-date">
                        {fmtDate(v.updated_at || v.created_at)}
                      </div>
                      <div className="version-row-preview">
                        {(v.body || "(vazio)").slice(0, 80).replace(/\n/g, " ")}…
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </aside>
            <section className="version-preview">
              {selectedVersion ? (
                <>
                  <header className="version-preview-header">
                    <div>
                      <strong>Versão {selectedVersion.version}</strong>
                      <span className="muted">
                        {" · "}
                        {fmtDate(selectedVersion.updated_at || selectedVersion.created_at)}
                      </span>
                    </div>
                    {!selectedVersion.is_current && (
                      <button
                        className="btn primary"
                        disabled={restore.isPending}
                        onClick={() => {
                          if (
                            confirm(
                              `Restaurar v${selectedVersion.version}? O conteúdo atual passará a ser histórico (mas pode ser restaurado depois enquanto estiver dentro das últimas 5 versões).`,
                            )
                          ) {
                            restore.mutate({ version: selectedVersion.version });
                          }
                        }}
                      >
                        {restore.isPending ? "A restaurar…" : `Restaurar esta versão`}
                      </button>
                    )}
                  </header>
                  <div className="version-preview-body">
                    <MarkdownView>{selectedVersion.body}</MarkdownView>
                  </div>
                </>
              ) : (
                <p className="muted">Seleciona uma versão à esquerda.</p>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
