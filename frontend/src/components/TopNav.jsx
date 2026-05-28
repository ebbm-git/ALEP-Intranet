import { NavLink } from "react-router-dom";

export default function TopNav({ tree, loading }) {
  if (loading) return <nav className="topnav muted">A carregar…</nav>;
  return (
    <nav className="topnav">
      {tree.map((node) => (
        <NavLink
          key={node.id}
          to={`/${node.slug}`}
          className={({ isActive }) => "topnav-item" + (isActive ? " active" : "")}
        >
          {node.title}
        </NavLink>
      ))}
    </nav>
  );
}
