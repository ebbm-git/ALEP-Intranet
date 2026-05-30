# HIST_DEV — Histórico de Desenvolvimento

Registo cronológico de alterações ao projecto **ALEP Intranet** e gestão de erros conhecidos. Mantido pelo assistente IA. Última actualização: 2026-05-29.

> **Como ler:**
> - **Erros Pendentes** — problemas detectados que ainda não estão resolvidos. Itens com `[ ]` por fazer; `[x]` quando resolvidos (mas mantidos visíveis com referência ao commit/data).
> - **Histórico** — alterações concluídas com sucesso, do mais recente para o mais antigo.

---

## 🔴 Erros Pendentes

- [x] ~~**2026-05-29 — `VITE_API_URL` mal configurado no frontend Railway.**~~
  ~~Bundle apontava para o próprio frontend em vez do backend.~~
  **Resolvido em 2026-05-29** pelo utilizador, substituindo o valor por `https://backend-production-2684.up.railway.app/api/v1` (hardcoded) no serviço Railway. Verificado por `scripts/test_live_site.py` (9/9 PASS).

---

## 🟢 Histórico de Alterações

### 2026-05-30 — Supabase Auth com 5 papéis e grelha de permissões ✅
- **5 papéis** (do mais alto ao mais baixo):
  - `admin` — tudo
  - `editor_chief` — edita + apaga blocos nas páginas com acesso, sem Configurações
  - `editor_a` — edita blocos nas páginas com acesso
  - `editor_b` — igual a `editor_a` (existe como segundo "carril" para o admin atribuir conjuntos diferentes de páginas a departamentos diferentes)
  - `viewer` — leitura nas páginas com acesso
- **Bootstrap**: o primeiro utilizador a autenticar-se torna-se automaticamente `admin`; signups seguintes começam como `viewer`.
- **Backend**:
  - JWT validado contra `<supabase>/auth/v1/user` (funciona com `sb_publishable`/`sb_secret` novos)
  - Tabelas novas: `user_profiles`, `role_page_permissions`
  - Endpoints `/api/v1/admin/users` (GET/PATCH/DELETE), `/api/v1/admin/permissions` (GET/POST/PUT-bulk), `/api/v1/auth/me`
  - Todos os endpoints de conteúdo passaram a requerer auth + check de permissão
  - `pages/tree` filtra ramos a que o utilizador não tem acesso (admins vêem tudo)
- **Frontend**:
  - `AuthProvider` + `useAuth()`/`useCanEditPage()`/`useCanDeletePage()`
  - Páginas `/login` + `/signup`
  - `ContentBlock` + `SectionPage` escondem botões consoante o papel + acesso
  - Menu top-right com avatar, papel actual e logout
  - `/configuracoes/utilizadores` (lista, mudar papel, remover) e `/configuracoes/permissoes` (grelha papéis × páginas, click para activar/desactivar, botão Guardar)
- **Migração**: `78d90d5310ad_auth_user_profiles_role_page_permissions.py`
- **Seed**: `seed_navigation.py` agora concede a cada papel não-admin acesso a todas as páginas por defeito (o admin restringe via grelha).
- **Tester**: `scripts/test_live_site.py` agora verifica que endpoints protegidos respondem 401 sem token. 9/9 PASS.
- **Commit:** `ef1933a` — `feat(auth): 5-tier Supabase Auth with per-page permission grid`

### 2026-05-29 — UI: modal de histórico de versões em cada bloco ✅
- Botão **"🕒 Histórico"** novo em cada `ContentBlock` (mostra "v2"/"v3"/etc quando há histórico).
- Modal full-screen com layout 2 colunas:
  - Esquerda: lista de versões (mais recente em cima), com tag de versão, data, preview de 2 linhas. A actual é marcada com badge "actual" e borda em accent.
  - Direita: preview Markdown completo da versão seleccionada + botão **"Restaurar esta versão"** (escondido na versão actual).
- Fecha com ESC ou click no backdrop.
- Restaurar chama `POST /api/v1/content-blocks/{id}/restore/{n}` e invalida queries do React Query para refresh imediato.
- Layout responsive: em ecrãs pequenos, lista fica no topo.
- 9/9 testes de live continuam a passar.
- **Commit:** `213e0f6` — `feat(frontend): version history modal — view + restore previous versions`

### 2026-05-29 — Versioning de conteúdo (até 5 versões por bloco) ✅
- Cada edição agora cria uma **nova linha** em `content_blocks` em vez de sobrescrever; o anterior fica marcado `is_current=false`. Pruning automático mantém no máximo 5 versões por bloco.
- 3 colunas novas:
  - `lineage_id` (UUID, NOT NULL) — identificador estável de um bloco entre edições; é o que programas externos devem referenciar para links permanentes.
  - `version` (INTEGER) — incrementa em cada edit (1, 2, 3, ...).
  - `is_current` (BOOLEAN) — o filtro fácil: `WHERE is_current = true` devolve o conteúdo visível.
- Endpoints novos:
  - `GET /api/v1/content-blocks/{id}/versions` — lista todas as versões da linhagem, mais recente primeiro (até 5).
  - `POST /api/v1/content-blocks/{id}/restore/{n}` — restaura a versão `n` (cria uma nova versão actual com o body antigo; o restore fica gravado em history).
- Migração Alembic: `a1afe2a8d505_content_block_versioning_lineage_id_.py` (com backfill: cada bloco existente fica com `lineage_id = id, version = 1, is_current = true`).
- Comportamento:
  - `list_for_page` filtra por `is_current = true` (só conteúdo visível).
  - Edição "no-op" (mesmo body + block_type) **não** cria nova versão — evita ruído.
  - Position é partilhada entre versões da mesma linhagem; insert above/below move todo o histórico em conjunto.
  - `delete_block` apaga a linhagem inteira (todas as versões).
- Smoke-test local + verificação em produção: tudo a verde; `scripts/test_live_site.py` continua 9/9.
- **Commit:** `9c6af9f` — `feat(content): copy-on-write versioning with up to 5 history rows per block`

### 2026-05-29 — Intranet 100% operacional em produção ✅
- Todos os 9 testes do `scripts/test_live_site.py` passam contra os domínios Railway.
- Resolvido o último erro pendente (`VITE_API_URL` hardcoded para o backend correto).
- Estado actual:
  - Backend: `https://backend-production-2684.up.railway.app` (FastAPI + Supabase Postgres)
  - Frontend: `https://frontend-production-372c.up.railway.app` (React SPA, builda no arranque)
  - Storage: bucket público `MediaGeral` na Supabase (18 imagens)
  - CORS preflight verificado a permitir o domínio do frontend.

### 2026-05-29 — Adicionado `scripts/test_live_site.py` + estrutura HIST_DEV.md
- 9 checks end-to-end: `/health`, `/api/v1/pages/tree`, página de exemplo, OpenAPI doc, HTML do frontend, bundle JS, wiring frontend→backend, imagem Storage pública, CORS preflight.
- Pode ser invocado a qualquer momento — agente de verificação ad-hoc.
- HIST_DEV.md criado com secções de Erros Pendentes + Histórico.

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
