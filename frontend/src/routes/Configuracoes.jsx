import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import ConfigUsers from "./ConfigUsers.jsx";
import ConfigPermissions from "./ConfigPermissions.jsx";

export default function Configuracoes() {
  return (
    <div className="config-area">
      <header className="config-header">
        <h1>Configurações</h1>
        <p className="muted">
          Área de administração — só visível para quem tem o papel{" "}
          <strong>Administrador</strong>.
        </p>
        <nav className="config-tabs">
          <NavLink
            to="utilizadores"
            className={({ isActive }) => "config-tab" + (isActive ? " active" : "")}
          >
            Utilizadores
          </NavLink>
          <NavLink
            to="permissoes"
            className={({ isActive }) => "config-tab" + (isActive ? " active" : "")}
          >
            Grelha de Permissões
          </NavLink>
        </nav>
      </header>
      <Routes>
        <Route index element={<Navigate to="utilizadores" replace />} />
        <Route path="utilizadores" element={<ConfigUsers />} />
        <Route path="permissoes" element={<ConfigPermissions />} />
      </Routes>
    </div>
  );
}
