# Colony

Personal expense management app — FastAPI backend + Next.js 15 frontend.
Docker Compose for local dev. See `backend/AGENTS.md` and `frontend/AGENTS.md`
for domain-specific instructions.

## Quick Start

```bash
docker-compose up --build
# Frontend → http://localhost:3000
# API   → http://localhost:8000
# Docs  → http://localhost:8001
```

## Commands

### Backend

```bash
cd backend
uv run fastapi dev                          # hot reload
PYTHONPATH=. uv run pytest                  # all tests
PYTHONPATH=. uv run pytest tests/cycles/    # single domain
PYTHONPATH=. uv run ruff check . --fix
PYTHONPATH=. uv run ruff format .
PYTHONPATH=. uv run pyright .
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
```

### Frontend

```bash
cd frontend
npm run dev
npx tsc --noEmit
```

### Pre-commit (from repo root)

```bash
# List only the files you changed — do NOT use --all-files (OOM risk):
pre-commit run --files backend/app/cycles/service.py
pre-commit run prettier --files frontend/components/cycles/index.tsx
pre-commit run markdownlint --files AGENTS.md
```

Ruff and Pyright are **not** pre-commit hooks — run them directly via `uv run`.

## Structure

```
backend/app/          # FastAPI domains: auth, households, payment_methods,
                      #   recurrent_expenses, cycles
frontend/app/         # (auth) = public, (app) = protected
frontend/components/  # {feature}/index.tsx + actions.ts (single-file pattern)
frontend/lib/         # apiClient + per-domain *.api.ts
frontend/actions/     # auth.action.ts (only file with "use server")
docs/                 # MkDocs Material
helm/                 # Kubernetes manifests
```

## Key Constraints

- **PYTHONPATH=.** required for all backend pytest/ruff/pyright invocations.
- **Never** add `"use server"` to `components/*/actions.ts` — they must run
  client-side so `apiClient` can reach `localhost:8000` from the browser.
- **Soft deletes only** — set `active = False`; never `db.delete()`.
- **Completed cycles are read-only** — all mutations rejected.
- **Domain isolation** — domains do not import each other's `service.py`.
- **No `HTTPException` in services** — raise domain exceptions (inherit
  `AppExceptionError`); global handler converts to JSON envelope.
- **80-char prose limit** on `.md` files outside `docs/` (markdownlint MD013).
- Code blocks and table rows are exempt from the 80-char limit.

## Validation Checklist

```bash
cd backend
PYTHONPATH=. uv run ruff check . --fix
PYTHONPATH=. uv run ruff format .
PYTHONPATH=. uv run pyright .
PYTHONPATH=. uv run pytest
cd ../frontend && npx tsc --noEmit
pre-commit run --files <changed files>
```

## Default Admin

`admin` / `colony-admin` (configurable via `DEFAULT_ADMIN_USERNAME` /
`DEFAULT_ADMIN_PASSWORD` env vars on deploy).

## Docs

- `docs/architecture/frontend.md` — frontend architecture
- `docs/architecture/backend.md` — backend architecture
- `docs/architecture/database-schema.md` — DB design + recurrence
- `docs/architecture/api-specification.md` — API endpoints
- `docs/development/setup.md` — dev setup
- `docs/development/code-quality.md` — code standards
- `docs/requirements.md` — functional + non-functional requirements
