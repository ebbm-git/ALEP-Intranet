# HIST_DEV — Histórico de Desenvolvimento

Registo cronológico de alterações ao projecto **ALEP Intranet** e gestão de erros conhecidos. Mantido pelo assistente IA. Última actualização: 2026-05-29.

> **Como ler:**
> - **Erros Pendentes** — problemas detectados que ainda não estão resolvidos. Itens com `[ ]` por fazer; `[x]` quando resolvidos (mas mantidos visíveis com referência ao commit/data).
> - **Histórico** — alterações concluídas com sucesso, do mais recente para o mais antigo.

---

## 🔴 Erros Pendentes

- [ ] **2026-05-29 — `VITE_API_URL` mal configurado no frontend Railway.**
  O bundle de produção contém o URL do *próprio* frontend (`frontend-production-372c.up.railway.app`) em vez do URL do backend (`backend-production-2684.up.railway.app`). Em runtime no browser, as chamadas `/api/v1/*` vão para sítio errado e a homepage carrega vazia.
  **Fix:** No Railway, serviço `frontend` → **Variables** → editar `VITE_API_URL` para um destes (qualquer um serve):
   - `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1` (com a referência cruzada)
   - `https://backend-production-2684.up.railway.app/api/v1` (hardcoded — mais à prova de bala)
  Depois salvar; o Railway redeploy automaticamente; aguardar build (~1-2 min) e re-correr `scripts/test_live_site.py`.

---

## 🟢 Histórico de Alterações

### 2026-05-29 — Frontend: build no arranque para sobreviver a qualquer builder do Railway
- **Problema:** O builder Railpack do Railway não estava a correr `npm run build`, deixando `dist/` vazio e o `serve` a devolver 404 da edge.
- **Fix:** `npm start` agora faz `vite build && serve -s dist -l tcp://0.0.0.0:${PORT:-3000}`; `vite` e `@vitejs/plugin-react` movidos para `dependencies`; `railway.toml` chama `npm start`.
- **Commit:** `65585b4` — `fix(frontend): build at start time so any Railway builder produces a working SPA`

### 2026-05-29 — Backend: `$PORT` não expandia + Python output buffering
- **Problema:** uvicorn arrancava em porta errada (Railway corre `startCommand` directamente sem shell em alguns casos); logs amortecidos pelo Python.
- **Fix:** `startCommand` envolto em `sh -c '...'`, fallback `${PORT:-8000}`, `PYTHONUNBUFFERED=1` em `nixpacks.toml`.
- **Commit:** `2f905a2` — `fix(backend): wrap startCommand in sh -c so $PORT expands + unbuffer Python`

### 2026-05-29 — Frontend: `serve` v14 rejeita `-l <port>` sem protocolo
- **Problema:** `serve -s dist -l $PORT` falhava com `Unknown --listen endpoint scheme`.
- **Fix:** `-l tcp://0.0.0.0:${PORT:-3000}` envolto em `sh -c`.
- **Commit:** `62bfcc8` — `fix(frontend): serve needs full tcp:// endpoint + force shell expansion`

### 2026-05-29 — Primeiro deploy ao Railway
- Repo inicializado e push para `github.com/ebbm-git/ALEP-Intranet`.
- Dois serviços criados no Railway (backend + frontend) a partir do mesmo repo.
- Domínios públicos: `backend-production-2684.up.railway.app`, `frontend-production-372c.up.railway.app`.
- Variáveis de ambiente configuradas em cada serviço (referências cruzadas `${{<svc>.RAILWAY_PUBLIC_DOMAIN}}`).
- **Commit:** `<inicial>` (preparação) + várias correcções subsequentes.

### 2026-05-29 — Migração de imagens para Supabase Storage (`MediaGeral`)
- 18 PNGs movidos de `frontend/public/intranet-images/` para o bucket `MediaGeral/intranet/` na Supabase Storage.
- URLs em Markdown na base de dados reescritos para apontar para `https://<ref>.supabase.co/storage/v1/object/public/MediaGeral/intranet/<file>`.
- Bucket tornado público para permitir `<img src>` direto.
- Pasta `frontend/public/intranet-images/` removida (obsoleta).

### 2026-05-28/29 — Importação de conteúdo real do PDF
- Extracção com PyMuPDF (texto, acentos preservados) + pdfplumber (tabelas).
- 16 secções importadas como Markdown (GFM com tabelas, listas, blockquotes).
- 18 imagens extraídas, servidas inicialmente em `frontend/public/intranet-images/`.
- Scripts: `scripts/extract_pdf_content.py`, `scripts/import_extracted_content.py`.

### 2026-05-28 — Frontend convertido para React + Router + TanStack Query
- Layout com header (top nav) + sidebar (sub nav) + outlet.
- Páginas: `Home`, `SectionPage` (genérica), `NotFound`.
- Componentes: `ContentBlock` (view + edit + delete), `BlockInserter` (acima/abaixo), `MarkdownView`.
- Editor Markdown: `@uiw/react-md-editor` (lazy-loaded).

### 2026-05-28 — Backend FastAPI: endpoints de páginas + blocos
- `GET /pages/tree` — árvore de navegação.
- `GET /pages/by-path/{path:path}` — página + blocos.
- `POST/PATCH/DELETE /content-blocks` + `POST .../insert-above|below` com renumeração de posições.

### 2026-05-28 — Esquema inicial em Supabase (Alembic)
- Tabelas: `users`, `pages` (auto-referencial com `parent_id` + `position`), `content_blocks` (FK→pages, `position`, `block_type`, `body` markdown).
- Migration: `70cddf6adcaf_initial_schema_users_pages_content_blocks.py`.

### 2026-05-28 — Scaffold inicial
- Backend FastAPI + SQLAlchemy + Alembic + venv.
- Frontend Vite + (inicialmente vanilla JS, depois React).
- `docker-compose.yml`, `Makefile`, `LICENSE`, `README.md`, `CHANGELOG.md`, `.gitignore`, `.editorconfig`.
- Configurações Railway/Nixpacks para ambos os serviços.
- Decisão de stack: hospedagem **Railway**, BD **Supabase Postgres**, imagens **Supabase Storage**.
