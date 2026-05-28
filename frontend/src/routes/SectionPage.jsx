import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchPageByPath, queryKeys, appendBlock } from "../services/queries.js";
import ContentBlock from "../components/ContentBlock.jsx";
import BlockInserter from "../components/BlockInserter.jsx";

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

  if (isLoading) return <p>A carregar…</p>;
  if (isError) {
    if (error?.response?.status === 404) {
      // top-level page with no children landing handled here too
      nav("/404", { replace: true });
      return null;
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
            <button className="btn primary" onClick={handleAppend}>
              + Adicionar primeira secção
            </button>
          </div>
        ) : (
          blocks.map((b, i) => (
            <div key={b.id}>
              {i === 0 && <BlockInserter anchorId={b.id} where="above" pagePath={path} />}
              <ContentBlock block={b} pagePath={path} />
              <BlockInserter anchorId={b.id} where="below" pagePath={path} />
            </div>
          ))
        )}
      </div>
    </article>
  );
}
