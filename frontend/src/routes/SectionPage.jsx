import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchPageByPath, queryKeys, appendBlock } from "../services/queries.js";
import ContentBlock from "../components/ContentBlock.jsx";
import BlockInserter from "../components/BlockInserter.jsx";
import { useCanEditPage } from "../auth/AuthContext.jsx";

export default function SectionPage() {
  const { topSlug, childSlug } = useParams();
  const path = childSlug ? `${topSlug}/${childSlug}` : topSlug;
  const qc = useQueryClient();
  const nav = useNavigate();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.page(path),
    queryFn: () => fetchPageByPath(path),
    retry: false,
  });

  const canEdit = useCanEditPage(data?.page?.id);

  if (isLoading) return <p>A carregar…</p>;
  if (isError) {
    if (error?.response?.status === 404) {
      nav("/404", { replace: true });
      return null;
    }
    if (error?.response?.status === 403) {
      return (
        <div className="error">
          <h1>Sem acesso</h1>
          <p>Não tem permissão para ver esta página.</p>
        </div>
      );
    }
    return <p className="error">Erro a carregar a página: {error.message}</p>;
  }

  const { page, blocks } = data;

  const handleAppend = async () => {
    await appendBlock({ pageId: page.id, body: "" });
    qc.invalidateQueries({ queryKey: queryKeys.page(path) });
  };

  return (
    <article className="section-page">
      <header className="section-header">
        <nav className="breadcrumb">
          <Link to="/">Início</Link>
          {topSlug && (
            <>
              <span>›</span>
              <Link to={`/${topSlug}`}>{topSlug}</Link>
            </>
          )}
          {childSlug && (
            <>
              <span>›</span>
              <span>{page.title}</span>
            </>
          )}
        </nav>
        <h1>{page.title}</h1>
      </header>

      <div className="blocks">
        {blocks.length === 0 ? (
          <div className="empty">
            <p>Esta página ainda não tem conteúdo.</p>
            {canEdit && (
              <button className="btn primary" onClick={handleAppend}>
                + Adicionar primeira secção
              </button>
            )}
          </div>
        ) : (
          blocks.map((b, i) => (
            <div key={b.id}>
              {i === 0 && canEdit && (
                <BlockInserter anchorId={b.id} where="above" pagePath={path} />
              )}
              <ContentBlock block={b} pagePath={path} />
              {canEdit && <BlockInserter anchorId={b.id} where="below" pagePath={path} />}
            </div>
          ))
        )}
      </div>
    </article>
  );
}
