import { useMutation, useQueryClient } from "@tanstack/react-query";
import { insertBlock, queryKeys } from "../services/queries.js";

export default function BlockInserter({ anchorId, where, pagePath }) {
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: () => insertBlock({ anchorId, where, body: "" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.page(pagePath) }),
  });

  return (
    <div className="block-inserter" onClick={() => m.mutate()} role="button">
      <span className="block-inserter-line" />
      <span className="block-inserter-label">+ Inserir secção {where === "above" ? "acima" : "abaixo"}</span>
      <span className="block-inserter-line" />
    </div>
  );
}
