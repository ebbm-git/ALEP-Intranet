import { NavLink } from "react-router-dom";

export default function SideNav({ top }) {
  return (
    <nav className="sidenav">
      <h3 className="sidenav-title">{top.title}</h3>
      <ul>
        {top.children.map((c) => (
          <li key={c.id}>
            <NavLink
              to={`/${top.slug}/${c.slug}`}
              className={({ isActive }) => "sidenav-item" + (isActive ? " active" : "")}
            >
              {c.title}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
