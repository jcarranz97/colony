# Colony — CLAUDE.md

Colony is a personal expense management web app replacing manual Excel tracking.
It organizes expenses into **6-week cycles** aligned with bi-weekly pay periods,
supports USD/MXN multi-currency, and provides financial analytics.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.13+) |
| Database | PostgreSQL via SQLAlchemy 2.0+ |
| Validation | Pydantic 2.0+ |
| Auth | JWT (PyJWT) + Argon2ID password hashing |
| Frontend | Next.js + NextUI (planned) |
| Docs | MkDocs Material |
| Infra | Docker Compose |
| CI | GitHub Actions |

---

## Project Structure

```text
colony/
├── backend/
│   ├── app/
│   │   ├── auth/              # Auth domain
│   │   ├── payment_methods/   # Payment methods domain
│   │   ├── config.py          # Settings (env-based)
│   │   ├── database.py        # SQLAlchemy engine + sessions
│   │   ├── models.py          # Base ORM models
│   │   ├── exceptions.py      # Error handling infrastructure
│   │   ├── dependencies.py    # Global dependency exports
│   │   └── main.py            # FastAPI app factory
│   ├── tests/                 # pytest suite (mirrors domain structure)
│   ├── pyproject.toml         # Dependencies + Ruff + Pyright config
│   └── uv.lock
├── docs/                      # MkDocs documentation
│   ├── architecture/          # Backend, DB schema, API spec docs
│   ├── development/           # Setup + code quality guides
│   └── requirements.md
├── docker-compose.yml
├── mkdocs.yml
└── .pre-commit-config.yaml
```

---

## Domain Module Structure

Every business domain follows this internal layout:

```text
app/<domain>/
├── router.py        # HTTP endpoints
├── schemas.py       # Pydantic models (request/response)
├── models.py        # SQLAlchemy ORM models
├── service.py       # Business logic
├── dependencies.py  # Dependency injection
├── exceptions.py    # Domain-specific errors
├── constants.py     # Error codes and enums
└── utils.py         # Helper functions
```

Currently implemented domains: `auth`, `payment_methods`.

---

## Running Locally

### Docker (recommended)

```bash
docker-compose up --build
```

- Backend API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Docs site: <http://localhost:8001>

Hot reload is enabled: the `backend/` directory is mounted as a volume so
code changes are picked up automatically without restarting the container.

### Local (uv)

```bash
cd backend
uv sync
uv run fastapi dev
```

---

## Testing

```bash
cd backend
uv run pytest
```

Tests mirror the domain structure under `backend/tests/`.

---

## Code Quality

### Linting & Formatting (Ruff)

```bash
cd backend
uv run ruff check . --fix   # Lint with auto-fix
uv run ruff format .         # Format code
```

### Type Checking (Pyright)

```bash
cd backend
uv run pyright .
```

### Pre-commit hooks (run automatically on commit)

- Trailing whitespace, EOF newline
- JSON/YAML/Markdown validation
- Ruff lint + format
- Pyright type checking
- Hadolint for Dockerfiles

Run manually: `pre-commit run --all-files`

---

## Code Conventions

- **Type hints** required on all functions
- **Google-style docstrings**
- **88 character** line limit
- **Double quotes** preferred
- **Dependency injection** via FastAPI's `Annotated` + `Depends` pattern
- All API routes prefixed with `/api/v1/`
- JWT Bearer token in `Authorization` header

### Error Handling Pattern

- Raise domain-specific exceptions (inheriting from `AppExceptionError`)
- Global exception handlers in `main.py` convert to consistent JSON responses:

  ```json
  { "success": false, "error": { "code": "...", "message": "..." } }
  ```

---

## Database Conventions

- UUID primary keys
- Soft deletes via `active: bool` flag (preserve audit trail — do not hard delete)
- Timestamps: `created_at`, `updated_at` on all models
- JSONB for flexible recurrence pattern storage
- Multi-currency: store native currency + amount; convert to USD for reporting

### Recurrence Config (JSONB)

Expense templates support: `weekly`, `bi-weekly`, `monthly`, `custom` patterns
stored as structured JSON in `recurrence_config`.

---

## Architecture Notes

- **Domain-Driven Design**: Each feature is a self-contained module
- **Stateless auth**: JWT tokens, no server-side sessions
- **6-week expense cycles**: Core business concept — expenses live inside cycles
  aligned to pay periods
- **Fixed vs Variable expenses**: Core categorization; location implicitly
  derived from currency (USD = US, MXN = Mexico)

---

## CI/CD

- `.github/workflows/ci.yml` — runs Ruff + Pyright on every push/PR
- `.github/workflows/deploy-docs.yml` — deploys MkDocs to GitHub Pages

---

## Key Docs to Reference

- `docs/architecture/backend.md` — Detailed backend architecture
- `docs/architecture/database-schema.md` — DB design + recurrence patterns
- `docs/architecture/api-specification.md` — Full API endpoint specs
- `docs/development/setup.md` — Dev environment setup
- `docs/development/code-quality.md` — Code standards and tooling
- `docs/requirements.md` — Functional and non-functional requirements
