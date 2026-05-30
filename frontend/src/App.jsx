import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Home from "./routes/Home.jsx";
import SectionPage from "./routes/SectionPage.jsx";
import NotFound from "./routes/NotFound.jsx";
import Login from "./routes/Login.jsx";
import Signup from "./routes/Signup.jsx";
import Configuracoes from "./routes/Configuracoes.jsx";
import { RequireAdmin, RequireAuth } from "./auth/RequireAuth.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Home />} />
        <Route
          path="configuracoes/*"
          element={
            <RequireAdmin>
              <Configuracoes />
            </RequireAdmin>
          }
        />
        <Route path=":topSlug" element={<SectionPage />} />
        <Route path=":topSlug/:childSlug" element={<SectionPage />} />
        <Route path="404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}
