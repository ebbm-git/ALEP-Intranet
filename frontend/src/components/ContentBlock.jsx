import { useState, lazy, Suspense } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import MarkdownView from "./MarkdownView.jsx";
import { updateBlock, deleteBlock, queryKeys } from "../services/queries.js";

const MDEditor = lazy(() => import("@uiw/react-md-editor"));

export default function ContentBlock({ block, pagePath }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(block.body);
  const qc = useQueryClient();

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

  return (
    <section className="block">
      {editing ? (
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
          <div className="block-toolbar">
            <button className="btn small" onClick={() => setEditing(true)} title="Editar">
              ✏️ Editar
            </button>
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
          </div>
        </>
      )}
    </section>
  );
}
