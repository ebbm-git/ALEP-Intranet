# Architecture

High-level architecture for the ALEP Intranet.

## Components

- **Backend (FastAPI on Railway)** — REST API at `/api/v1/*`, JWT-based auth, SQLAlchemy ORM
- **Database (Supabase Postgres)** — primary data store; migrations via Alembic against the direct URL; app uses pooler URL
- **Frontend (Vite on Railway)** — SPA consuming the API; also talks to Supabase directly for Auth/Storage if enabled
- **TLS / domain** — handled by Railway (custom domain → `intranet.alep.pt` to be wired up)

## Data flow

```
Browser ─▶ Frontend (Railway) ─▶ FastAPI (Railway) ─▶ Supabase Postgres
                  │
                  └──▶ Supabase (Auth / Storage / Realtime, optional, direct)
```

## Authentication

JWT access tokens issued by `POST /api/v1/auth/login`. Tokens are sent in the
`Authorization: Bearer <token>` header.

## Environments

| Env         | Purpose                       |
|-------------|-------------------------------|
| development | Local dev, SQLite or local PG |
| staging     | Pre-production validation     |
| production  | Live alep.pt intranet         |
