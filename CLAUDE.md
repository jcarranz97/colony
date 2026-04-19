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
| Frontend | Next.js 15 + HeroUI v3 (App Router, TypeScript) |
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
├── frontend/                  # Next.js 15 frontend (App Router)
│   ├── app/                   # Route groups: (auth) public, (app) protected
│   ├── components/            # Feature-organized UI components
│   ├── lib/                   # API client layer (typed fetch wrappers)
│   ├── actions/               # Next.js Server Actions (auth cookie)
│   ├── helpers/               # TypeScript types, Yup schemas, formatters
│   └── middleware.ts          # Auth guard (cookie-based route protection)
├── docs/                      # MkDocs documentation
│   ├── architecture/          # Backend, frontend, DB schema, API spec docs
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

Currently implemented domains: `auth`, `payment_methods`,
`expense_templates`, `cycles`.

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

### Local (uv — backend only)

```bash
cd backend
uv sync
uv run fastapi dev
```

### Local (frontend)

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000
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
- Soft deletes via `active: bool` flag (preserve audit trail — no hard
  deletes)
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

## Frontend Architecture

The frontend lives in `frontend/` and is built with **Next.js 15 App Router**,
**HeroUI v3**, **Tailwind CSS v4**, and **TypeScript**.

### Key Design Decisions

- **Route groups**: `(auth)` for public pages (login, register);
  `(app)` for all protected pages
- **Auth**: JWT stored in `httpOnly` cookie (`colony-token`) via Next.js
  Server Actions — never accessible to JavaScript
- **Route protection**: `middleware.ts` enforces the auth boundary
  server-side before any render
- **API client**: `lib/api-client.ts` is the single typed fetch wrapper —
  injects `Authorization: Bearer` header, returns
  `{ success: true, data } | { success: false, error }`,
  intercepts 401 → redirects to `/login`
- **State**: `useState` everywhere; no Redux/Zustand/SWR —
  React Context only for sidebar collapsed state
- **Forms**: Formik + Yup throughout — all schemas in
  `helpers/schemas.ts`; all types in `helpers/types.ts`
- **HeroUI v3 setup**: CSS imports only — `@import "tailwindcss"` then
  `@import "@heroui/styles"` in `globals.css`; no Tailwind plugin required
- **Component pattern**: every feature follows
  `components/{feature}/index.tsx` + `table.tsx` + `render-cell.tsx`
  - `add-*.tsx` + `edit-*.tsx` + `actions.ts`
- **Soft deletes**: never hard-delete — call the DELETE endpoint which sets
  `active: false`; completed cycles are fully read-only

### Frontend Folder Structure

```text
frontend/
├── app/
│   ├── (auth)/         # /login, /register — no sidebar
│   └── (app)/          # Protected: /cycles, /payment-methods,
│                       #   /expense-templates, /settings
├── components/
│   ├── auth/           # Login + Register forms
│   ├── payment-methods/
│   ├── expense-templates/  # Includes recurrence-config-builder.tsx
│   ├── cycles/
│   │   ├── cycle-detail/   # Expenses table, filters, add/edit modals
│   │   └── cycle-summary/  # Financial summary cards
│   ├── layout/         # App shell + SidebarContext
│   ├── sidebar/
│   ├── navbar/
│   └── shared/         # StatusChip, CurrencyBadge, CategoryBadge,
│                       #   AmountDisplay, ConfirmModal, etc.
├── lib/                # api-client.ts + per-domain *.api.ts modules
├── actions/            # auth.action.ts (cookie helpers)
├── helpers/            # types.ts, schemas.ts, formatters.ts
└── middleware.ts
```

### HeroUI Usage Rules

- Use semantic color props: `color="primary"` / `color="danger"` /
  `color="success"` — never raw Tailwind colors on HeroUI components
- Use `classNames` prop for per-instance style overrides
- Use compound components (e.g., `<Table>` + `<TableBody>` + `<TableRow>`)
  — avoid config-only patterns
- Wrap HeroUI in `components/shared/` only when Colony-specific color
  logic must be centralized (e.g., `<StatusChip>`)

### Status Color Conventions

| Status / Value | HeroUI `color` |
|---|---|
| `draft` (cycle) | `default` |
| `active` (cycle) | `primary` |
| `completed` (cycle) | `success` |
| `pending` (expense) | `warning` |
| `paid` (expense) | `success` |
| `overdue` (expense) | `danger` |
| `cancelled` (expense) | `default` |
| `USD` | `primary` |
| `MXN` | `warning` |
| `fixed` (category) | `secondary` |
| `variable` (category) | `success` |

### Environment

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Frontend dev server: `cd frontend && npm run dev` → <http://localhost:3000>

---

## Key Docs to Reference

- `docs/architecture/frontend.md` — Frontend architecture + implementation plan
- `docs/architecture/backend.md` — Detailed backend architecture
- `docs/architecture/database-schema.md` — DB design + recurrence patterns
- `docs/architecture/api-specification.md` — Full API endpoint specs
- `docs/development/setup.md` — Dev environment setup
- `docs/development/code-quality.md` — Code standards and tooling
- `docs/requirements.md` — Functional and non-functional requirements
