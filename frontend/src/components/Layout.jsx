import { Link, Outlet, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import TopNav from "./TopNav.jsx";
import SideNav from "./SideNav.jsx";
import UserMenu from "./UserMenu.jsx";
import { fetchTree, queryKeys } from "../services/queries.js";

export default function Layout() {
  const { topSlug } = useParams();
  const { data: tree, isLoading } = useQuery({
    queryKey: queryKeys.tree,
    queryFn: fetchTree,
  });

  const activeTop = tree?.find((t) => t.slug === topSlug);

  return (
    <div className="layout">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-logo">ALEP</span>
          <span className="brand-sub">Intranet</span>
        </Link>
        <TopNav tree={tree ?? []} loading={isLoading} />
        <UserMenu />
      </header>
      <div className="body">
        <aside className="sidebar">
          {activeTop ? (
            <SideNav top={activeTop} />
          ) : (
            <p className="sidebar-hint">Escolha uma secção em cima.</p>
          )}
        </aside>
        <main className="content">
          <Outlet />
        </main>
      </div>
      <footer className="footer">
        <small>ALEP · Manual de Onboarding 2026 (v1.0) · Uso Interno</small>
      </footer>
    </div>
  );
}
