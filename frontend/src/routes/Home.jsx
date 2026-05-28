import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchTree, queryKeys } from "../services/queries.js";

export default function Home() {
  const { data: tree, isLoading } = useQuery({
    queryKey: queryKeys.tree,
    queryFn: fetchTree,
  });

  return (
    <div className="home">
      <h1>Bem-vindo à Intranet ALEP</h1>
      <p className="lead">
        Plataforma interna baseada no <strong>Manual de Onboarding 2026 (v1.0)</strong>.
        Escolha uma das secções abaixo para começar.
      </p>
      {isLoading ? (
        <p>A carregar…</p>
      ) : (
        <ul className="home-grid">
          {(tree ?? []).map((t) => (
            <li key={t.id} className="home-card">
              <Link to={`/${t.slug}`}>
                <h2>{t.title}</h2>
                <p>
                  {t.children.length} {t.children.length === 1 ? "secção" : "secções"}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
