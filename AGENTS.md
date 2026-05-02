# Colony

Colony is a personal expense management web app replacing manual Excel
tracking. It organizes expenses into **billing cycles** aligned with pay
periods, supports USD/MXN multi-currency, and provides financial analytics.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.13+) |
| Database | PostgreSQL via SQLAlchemy 2.0+ |
| Validation | Pydantic 2.0+ |
| Auth | JWT (PyJWT) + Argon2ID password hashing |
| Frontend | Next.js 15 + HeroUI v3 (App Router, TypeScript) |
| UI Theme | Notebook/handwriting aesthetic — custom CSS vars + Caveat/Kalam fonts |
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
│   │   ├── recurrent_expenses/ # Recurrent expenses domain
│   │   ├── cycles/            # Cycles + expenses domain
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

For backend-specific conventions, patterns, and rules see
`backend/AGENTS.md`. For frontend-specific rules see `frontend/AGENTS.md`.

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
`recurrent_expenses`, `cycles`.

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

### Pre-commit hooks (run automatically on commit)

- Trailing whitespace, EOF newline
- JSON/YAML/Markdown validation
- Ruff lint + format (Python)
- Pyright type checking
- Hadolint for Dockerfiles
- markdownlint for `.md` files

Run manually: `pre-commit run --all-files`

### Markdown files

`markdownlint` runs on all `.md` files outside `docs/` on every commit.
Rules (configured in `.markdownlint.json`):

- **80-character line limit** on prose lines (MD013).
- Code blocks (` ``` `) and table rows are exempt from the line limit.
- No trailing spaces; files must end with a newline.

When you create or edit any `.md` file in this repo, keep prose lines at or
under 80 characters or the commit hook will fail.

### Linting & Formatting (Ruff — Python)

```bash
cd backend
uv run ruff check . --fix
uv run ruff format .
```

### Type Checking (Pyright)

```bash
cd backend
uv run pyright .
```

---

## Architecture Notes

- **Domain-Driven Design**: Each feature is a self-contained module
- **Stateless auth**: JWT tokens, no server-side sessions
- **Billing cycles**: Core business concept — expenses live inside cycles
  aligned to pay periods
- **Fixed vs Variable expenses**: Core categorization; location implicitly
  derived from currency (USD = US, MXN = Mexico)

---

## CI/CD

- `.github/workflows/ci.yml` — runs Ruff + Pyright on every push/PR
- `.github/workflows/deploy-docs.yml` — deploys MkDocs to GitHub Pages

---

## Frontend Architecture

The frontend lives in `frontend/` and is built with **Next.js 15 App
Router**, **HeroUI v3**, **Tailwind CSS v4**, and **TypeScript**.

### Notebook UI Theme

The entire protected app is wrapped in a **notebook/handwriting aesthetic**:

- **Cover bar** — dark green (`#2c4a3e`) top strip with "Colony" title in
  Kalam font
- **Spiral binding** — decorative ring strip on the far left
- **Nav tabs** — cream paper tabs replacing a traditional sidebar
- **Ruled page** — faint blue horizontal lines + red left margin on the
  main content area
- **Handwriting fonts** — Caveat (body) and Kalam (headings) from Google
  Fonts
- **Highlighter status colors** — expense rows use translucent marker
  colors:
  - Paid → green (`rgba(80,200,100,0.35)`)
  - Pending → yellow (`rgba(255,210,60,0.45)`)
  - Overdue → red (`rgba(240,80,70,0.30)`)
  - Cancelled → grey (`rgba(180,180,180,0.28)`)

All notebook CSS lives in `frontend/app/globals.css` as `nb-*` prefixed
classes and `:root` CSS variables. Do **not** use HeroUI components for the
layout shell — the notebook uses plain HTML + custom CSS.

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
- **State**: `useState` everywhere; no Redux/Zustand/SWR
- **Forms**: simple controlled `<input>` / `<select>` with `nb-form-*` CSS
  classes; HeroUI form components (Formik/Yup) are **not** used inside the
  notebook shell
- **HeroUI v3 setup**: CSS imports only — `@import "tailwindcss"` then
  `@import "@heroui/styles"` in `globals.css`; no Tailwind plugin required
- **Soft deletes**: never hard-delete — call the DELETE endpoint which sets
  `active: false`; completed cycles are fully read-only

### Component Pattern

Features follow a **single-file pattern** for the notebook UI:

```text
components/{feature}/
├── index.tsx    # All UI: card list + modals + state management
└── actions.ts   # Server-action wrappers around lib/*.api.ts
```

`table.tsx` and `render-cell.tsx` files exist in payment-methods and
recurrent-expenses from an earlier implementation — they are superseded by
the inline notebook card rendering in `index.tsx` and can be ignored.

### Frontend Folder Structure

```text
frontend/
├── app/
│   ├── layout.tsx          # Root HTML — adds Google Fonts (Caveat, Kalam)
│   ├── globals.css         # Tailwind + HeroUI imports + ALL nb-* CSS
│   ├── (auth)/             # /login, /register — plain centered layout
│   └── (app)/              # Protected: /cycles, /payment-methods,
│                           #   /recurrent-expenses, /settings
├── components/
│   ├── auth/               # Login + Register forms
│   ├── payment-methods/    # Notebook card list + add/edit modals
│   ├── recurrent-expenses/  # Notebook card list + add/edit modals
│   ├── cycles/             # Full cycles implementation — list, detail,
│   │                       #   expense rows with highlighter, modals
│   ├── layout/             # AppLayout — notebook shell (cover, spiral, nav)
│   ├── navbar/             # Legacy — no longer rendered in AppLayout
│   ├── sidebar/            # Legacy — no longer rendered in AppLayout
│   └── shared/             # StatusChip, CurrencyBadge, etc. (HeroUI-based)
├── lib/                    # api-client.ts + per-domain *.api.ts modules
├── actions/                # auth.action.ts (cookie helpers)
├── helpers/                # types.ts, schemas.ts, formatters.ts
└── middleware.ts
```

### HeroUI Usage Rules

HeroUI is still imported and available. Use it in `components/shared/` and
`(auth)` pages. **Do not** use HeroUI Table, Modal, or form inputs inside
the notebook shell — use plain HTML with `nb-*` CSS classes instead.

When HeroUI is appropriate:

- `color="primary"` / `color="danger"` / `color="success"` — semantic
  colors
- Compound components (`<Table>` + `<TableBody>` + `<TableRow>`) in shared
  components
- `classNames` prop for per-instance overrides
- Wrap in `components/shared/` only when Colony-specific logic is
  centralized

### CSS Variable Reference

| Variable | Value | Usage |
|---|---|---|
| `--paper` | `#fdf8f0` | Page background (cream) |
| `--cover-bg` | `#2c4a3e` | Cover bar, active tab accent |
| `--cover-accent` | `#c9a84c` | Gold border, logo color |
| `--ink` | `#2c1810` | Primary text |
| `--ink-light` | `#5a4030` | Secondary text |
| `--font-hand` | `'Caveat', cursive` | Body handwriting font |
| `--font-title` | `'Kalam', cursive` | Heading handwriting font |
| `--hl-paid` | `rgba(80,200,100,0.35)` | Green highlighter |
| `--hl-pending` | `rgba(255,210,60,0.45)` | Yellow highlighter |
| `--hl-overdue` | `rgba(240,80,70,0.30)` | Red highlighter |

### Environment

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Frontend dev server: `cd frontend && npm run dev` → <http://localhost:3000>

---

## Key Docs to Reference

- `docs/architecture/frontend.md` — Frontend architecture
- `docs/architecture/backend.md` — Detailed backend architecture
- `docs/architecture/database-schema.md` — DB design + recurrence patterns
- `docs/architecture/api-specification.md` — Full API endpoint specs
- `docs/development/setup.md` — Dev environment setup
- `docs/development/code-quality.md` — Code standards and tooling
- `docs/requirements.md` — Functional and non-functional requirements
