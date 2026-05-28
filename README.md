# ALEP Intranet

Intranet platform for ALEP — Associação do Alojamento Local em Portugal (alep.pt).

## Overview

Internal platform providing tools and resources for ALEP staff and members.

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI
- **Database:** Supabase (managed PostgreSQL)
- **ORM / Migrations:** SQLAlchemy + Alembic
- **Auth:** JWT (OAuth2) — can be swapped for Supabase Auth
- **Frontend:** Vite / vanilla JS scaffold (framework TBD) + `@supabase/supabase-js`
- **Hosting:** Railway (backend + frontend services)
- **Local dev:** docker-compose (no local DB — points at Supabase)

## Project Structure

```
ALEP Intranet/
├── backend/          # FastAPI application
│   ├── app/          # Source code (api, core, models, schemas, services)
│   ├── alembic/      # Database migrations
│   └── tests/        # Backend tests
├── frontend/         # Frontend application
│   └── src/          # Components, pages, services, styles
├── docs/             # Project documentation
├── scripts/          # Utility scripts
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend)
- Docker (optional, for containerized setup)

### Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then edit values
uvicorn app.main:app --reload
```

API will be available at <http://localhost:8000> and docs at <http://localhost:8000/docs>.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

- `backend/.env.example` — backend config (Supabase `DATABASE_URL`, JWT secret, etc.)
- `frontend/.env.example` — `VITE_API_URL` + Supabase anon key for client-side use

## Deployment (Railway)

The repo contains `railway.toml` files in both `backend/` and `frontend/`.

1. Create two services on Railway (backend + frontend), pointed at the corresponding folders.
2. Set environment variables in each Railway service from the matching `.env.example`.
3. For the backend, use the Supabase **pooler** URL (port 6543) as `DATABASE_URL` and the **direct** URL (port 5432) for migrations.
4. Railway injects `PORT` automatically — start commands already bind to `$PORT`.

## Database (Supabase)

- Create a Supabase project at <https://supabase.com>.
- Copy the Postgres connection strings (pooler + direct) and the API URL + anon key.
- Run migrations against the direct URL: `alembic upgrade head`.

## Contributing

Internal project — contact the ALEP tech team.

## License

Proprietary — ALEP. All rights reserved.
