<!-- BEGIN:nextjs-agent-rules -->

# Frontend Agent Instructions

This is **Next.js 15 with App Router**. APIs, conventions, and file structure
differ from older Next.js. Read `node_modules/next/dist/docs/` if unsure;
heed deprecation notices.

---

## UI: Notebook Theme

The protected app (`app/(app)/`) uses a **handwritten-notebook aesthetic** —
not a standard dashboard layout. Key rules:

- The layout shell (`components/layout/layout.tsx`) renders: cover bar →
  spiral rings → nav tabs → ruled paper page. It does **not** use a Sidebar
  or Navbar component.
- All notebook CSS lives in `app/globals.css` as `nb-*` prefixed classes and
  `:root` CSS variables. Add new styles there with `nb-` prefix.
- **Do not** use HeroUI `Table`, `Modal`, `Select`, or `Input` inside the
  notebook shell. Use plain `<input>`, `<select>` with `nb-form-*` CSS classes
  and `nb-modal-*` for modals.
- HeroUI is still imported; use it in `components/shared/` and `(auth)` pages
  only.

## Component Pattern

Each feature uses a **single-file** approach:

```text
components/{feature}/
├── index.tsx    # Card list + modals + all local state
└── actions.ts   # Thin wrappers around lib/*.api.ts
```

`table.tsx` and `render-cell.tsx` exist in payment-methods and
recurrent-expenses as legacy artifacts — do not add new ones.

Implemented components: `auth`, `cycles`, `households` (admin-only),
`incomes`, `layout`, `payment-methods`, `recurrent-expenses`, `settings`,
`users` (admin-only).

### Household Selector (Settings)

`components/settings/index.tsx` renders a household selector when
`getMyHouseholdsAction()` returns more than one household. With only one
household it shows the name as read-only text. Switching calls
`setActiveHouseholdAction(id)` which hits `PUT /households/me/active`.

## Notebook CSS Classes (quick reference)

| Class               | Purpose                                       |
| ------------------- | --------------------------------------------- |
| `nb-page-title`     | Large Kalam heading                           |
| `nb-page-subtitle`  | Small subtitle                                |
| `nb-section-title`  | Divider heading with line                     |
| `nb-add-btn`        | Dashed "add" button (full width)              |
| `nb-modal-backdrop` | Full-screen modal overlay                     |
| `nb-modal`          | Modal paper box                               |
| `nb-modal-title`    | Modal heading                                 |
| `nb-form-group`     | Label + input wrapper                         |
| `nb-form-label`     | Small uppercase label                         |
| `nb-form-input`     | Underline-only text input                     |
| `nb-form-select`    | Bordered select                               |
| `nb-form-row`       | Flex row for side-by-side fields              |
| `nb-modal-actions`  | Right-aligned Cancel + Submit row             |
| `nb-btn-cancel`     | Ghost cancel button                           |
| `nb-btn-primary`    | Green submit button                           |
| `nb-empty`          | Centered empty-state block                    |
| `nb-payment-card`   | Payment method card row                       |
| `nb-template-card`  | Template card row                             |
| `nb-expense-row`    | Expense row (add status modifier — see below) |
| `nb-cycle-card`     | Cycle summary card                            |
| `nb-summary-strip`  | Dashed summary box in cycle detail            |

## Expense Status Colors

Apply as extra class on `.nb-expense-row`:

| Class           | Color                     | Meaning                                          |
| --------------- | ------------------------- | ------------------------------------------------ |
| `nb-paid`       | Green highlight + border  | Paid from tracked income                         |
| `nb-pending`    | Yellow highlight + border | Pending                                          |
| `nb-overdue`    | Red highlight + border    | Overdue                                          |
| `nb-cancelled`  | Grey, reduced opacity     | Cancelled                                        |
| `nb-paid-other` | Teal highlight + border   | Paid by third party (no impact on balance)       |
| `nb-skipped`    | Lavender, slightly dimmed | Not applicable this cycle (no impact on balance) |

## API Layer

- `lib/*.api.ts` — raw `apiClient` calls, no auth concerns
- `components/*/actions.ts` — thin async wrappers that inject the auth token
  via `getAuthToken()` from `@/actions/auth.action`
- Components call the `actions.ts` functions directly from `useEffect` or
  event handlers

### CRITICAL: Do NOT add `"use server"` to `components/*/actions.ts`

`actions/auth.action.ts` has `"use server"` because it reads `httpOnly`
cookies (a server-only API). The `components/*/actions.ts` files do **not**
have `"use server"` — they are plain async functions called from client
components.

If you add `"use server"` to a component actions file, the `apiClient` fetch
runs inside the Next.js server container, which cannot reach
`http://localhost:8000` (the backend container). The request never hits the
backend and returns "Network error". The browser calls the backend directly
via the Docker-exposed port, so `apiClient` must run on the client.

## Auth

- JWT stored in `httpOnly` cookie (`colony-token`) via `actions/auth.action.ts`
- `middleware.ts` blocks unauthenticated access to `(app)` routes server-side
- 401 from API → `apiClient` clears cookie and redirects to `/login`
- Login and registration use **username + password** (no email field).
- Default admin: `admin` / `colony-admin` (configurable via env vars on deploy).

## Validation Checklist Before Finishing

After implementing any frontend change, run prettier on every file you
modified. Prettier auto-formats TypeScript, TSX, CSS, JSON, and Markdown.
If you skip this step, the `git commit` hook will modify your files and
abort the commit, requiring re-staging.

Run from the **repo root** (where `.pre-commit-config.yaml` lives), not
from inside `frontend/`. Pass only the files you changed — do **not** use
`--all-files`, which processes the whole repo and can run out of memory:

```bash
# From repo root — list every frontend file you changed:
pre-commit run prettier --files frontend/components/cycles/index.tsx \
  frontend/app/globals.css frontend/helpers/types.ts
```

Also run markdownlint on any `.md` files you edited:

```bash
pre-commit run markdownlint --files frontend/AGENTS.md
```

Run TypeScript type checking from the `frontend/` directory:

```bash
cd frontend && npx tsc --noEmit
```

---

## Naming Conventions: UI vs Backend

The recurring expenses domain uses different names for the **start date** field
between the UI and the backend/database:

| Layer                           | Field name       |
| ------------------------------- | ---------------- |
| UI labels / validation messages | "Start Date"     |
| Internal TS field names         | `reference_date` |
| API request/response body       | `reference_date` |
| Database column                 | `reference_date` |
| Backend models / schemas        | `reference_date` |

The frontend keeps the internal field name as `reference_date` to match the
API contract. Only the **visible text** (form labels, validation messages)
uses "Start Date" for user clarity. Do not rename the internal `reference_date`
field in TypeScript — it must stay aligned with the backend API.

<!-- END:nextjs-agent-rules -->
