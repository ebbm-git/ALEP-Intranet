import { useState, lazy, Suspense } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import MarkdownView from "./MarkdownView.jsx";
import VersionHistory from "./VersionHistory.jsx";
import { updateBlock, deleteBlock, queryKeys } from "../services/queries.js";
import { useCanEditPage, useCanDeletePage } from "../auth/AuthContext.jsx";

const MDEditor = lazy(() => import("@uiw/react-md-editor"));

export default function ContentBlock({ block, pagePath }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(block.body);
  const [showHistory, setShowHistory] = useState(false);
  const qc = useQueryClient();
  const canEdit = useCanEditPage(block.page_id);
  const canDelete = useCanDeletePage(block.page_id);

  const invalidate = () => qc.invalidateQueries({ queryKey: queryKeys.page(pagePath) });

  const save = useMutation({
    mutationFn: () => updateBlock({ id: block.id, body: draft }),
    onSuccess: () => {
      invalidate();
      setEditing(false);
    },
  });

  const remove = useMutation({
    mutationFn: () => deleteBlock(block.id),
    onSuccess: invalidate,
  });

  // For non-editors with no actions available, render the markdown clean,
  // no toolbar, no modals.
  const showToolbar = canEdit || canDelete;

  return (
    <section className="block">
      {editing && canEdit ? (
        <div className="block-editor">
          <Suspense fallback={<p>A carregar editor…</p>}>
            <MDEditor value={draft} onChange={(v) => setDraft(v ?? "")} height={320} />
          </Suspense>
          <div className="block-actions">
            <button
              className="btn primary"
              onClick={() => save.mutate()}
              disabled={save.isPending}
            >
              {save.isPending ? "A guardar…" : "Guardar"}
            </button>
            <button
              className="btn ghost"
              onClick={() => {
                setDraft(block.body);
                setEditing(false);
              }}
              disabled={save.isPending}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <>
          <MarkdownView>{block.body}</MarkdownView>
          {showToolbar && (
            <div className="block-toolbar">
              {canEdit && (
                <button
                  className="btn small"
                  onClick={() => setEditing(true)}
                  title="Editar"
                >
                  ✏️ Editar
                </button>
              )}
              {canEdit && (
                <button
                  className="btn small"
                  onClick={() => setShowHistory(true)}
                  title="Ver histórico de versões"
                >
                  🕒 Histórico{block.version > 1 ? ` (v${block.version})` : ""}
                </button>
              )}
              {canDelete && (
                <button
                  className="btn small danger"
                  onClick={() => {
                    if (confirm("Tem a certeza que pretende eliminar esta secção?")) {
                      remove.mutate();
                    }
                  }}
                  disabled={remove.isPending}
                  title="Eliminar"
                >
                  🗑 Eliminar
                </button>
              )}
            </div>
          )}
        </>
      )}

      {showHistory && (
        <VersionHistory
          blockId={block.id}
          pagePath={pagePath}
          onClose={() => setShowHistory(false)}
        />
      )}
    </section>
  );
}
