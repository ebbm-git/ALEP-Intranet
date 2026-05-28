import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="notfound">
      <h1>Página não encontrada</h1>
      <p>
        O conteúdo que procura não existe ou foi movido. <Link to="/">Voltar ao início</Link>.
      </p>
    </div>
  );
}
