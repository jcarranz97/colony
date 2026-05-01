# Frontend Architecture

Colony's frontend is a Next.js 15 application communicating with the Colony
FastAPI backend over a JSON REST API. It uses **HeroUI v3** as the component
library, **Tailwind CSS v4** for utilities, and a custom **notebook/handwriting
UI theme** for the protected app shell.

---

## Tech Stack

| Package | Version | Purpose |
|---|---|---|
| `next` | `^15.x` | App framework — App Router, Server Components, Server Actions |
| `react` / `react-dom` | `^19.x` | UI runtime |
| `typescript` | `^5.x` | Static typing |
| `@heroui/react` | `^3.x` | Component library (used in auth pages and shared components) |
| `@heroui/styles` | `^3.x` | HeroUI CSS styles |
| `tailwindcss` | `^4.x` | Utility CSS |
| `next-themes` | `^0.3.x` | Dark/light mode |
| `react-icons` | `^5.x` | Icon set |
| `date-fns` | `^3.x` | Date formatting |

---

## Notebook UI Theme

The entire protected app (`app/(app)/`) renders inside a handwritten-notebook
aesthetic designed to feel like a physical expense ledger.

### Visual Structure

```
┌─────────────────────────────────────────────────────────┐
│  [spiral]  Colony          household budget tracker  Sign out  ← cover bar (#2c4a3e)
│  ░░░ ──────────────────────────────────────────────────────
│  ░░░ │ 📅 Cycles    │                                    │
│  ░░░ │ 💳 Payments  │   (ruled notebook page)            │
│  ░░░ │ 📋 Templates │   content rendered here            │
│  ░░░ │ ⚙️ Settings  │                                    │
│  ░░░ └──────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

| Zone | Description |
|---|---|
| Cover bar | Dark green (`#2c4a3e`) with gold accent border. "Colony" in Kalam font. Sign-out button. |
| Spiral binding | 44 px decorative strip with grey ring dividers. |
| Nav tabs | 130 px left pane — cream paper (`#f5eed8`). Active tab has gold left border. |
| Ruled page | Cream paper (`#fdf8f0`), faint blue horizontal lines, red left margin line. |

### Fonts

Loaded from Google Fonts in `app/layout.tsx`:

- **Caveat** — body handwriting font (`--font-hand`)
- **Kalam** — heading handwriting font (`--font-title`)

### Expense Status Colors (Highlighter Effect)

Expense rows use translucent marker colours with a brush-texture overlay:

| Status | Background | Left border |
|---|---|---|
| Paid | `rgba(80,200,100,0.35)` | `#3aad55` |
| Pending | `rgba(255,210,60,0.45)` | `#d4a800` |
| Overdue | `rgba(240,80,70,0.30)` | `#d94040` |
| Cancelled | `rgba(180,180,180,0.28)` | `#aaa` |

Paid rows also show a strikethrough on the expense name.

---

## Project Structure

```text
frontend/
├── app/
│   ├── layout.tsx              # Root HTML — adds Google Fonts
│   ├── globals.css             # Tailwind + HeroUI + all nb-* notebook CSS
│   ├── providers.tsx           # HeroUIProvider + NextThemesProvider
│   ├── (auth)/                 # /login, /register — no notebook shell
│   │   ├── layout.tsx
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (app)/                  # Protected — requires auth cookie
│       ├── layout.tsx          # Uses AppLayout (notebook shell)
│       ├── cycles/page.tsx
│       ├── payment-methods/page.tsx
│       ├── expense-templates/page.tsx
│       └── settings/page.tsx
│
├── components/
│   ├── auth/                   # Login + Register forms (use HeroUI)
│   ├── cycles/                 # Full cycles feature
│   │   ├── index.tsx           # List + detail + expense rows + modals
│   │   └── actions.ts          # Server-action wrappers
│   ├── payment-methods/        # Payment methods feature
│   │   ├── index.tsx           # Notebook card list + modals
│   │   ├── actions.ts          # Server-action wrappers
│   │   └── (legacy)            # table.tsx, render-cell.tsx — superseded
│   ├── expense-templates/      # Expense templates feature
│   │   ├── index.tsx           # Notebook card list + modals
│   │   ├── actions.ts          # Server-action wrappers
│   │   └── (legacy)            # table.tsx, render-cell.tsx — superseded
│   ├── layout/
│   │   ├── layout.tsx          # AppLayout — renders full notebook shell
│   │   └── layout-context.ts   # SidebarContext (legacy, kept for compat)
│   ├── navbar/                 # Legacy — not rendered in current layout
│   ├── sidebar/                # Legacy — not rendered in current layout
│   └── shared/                 # HeroUI-based shared components
│       ├── status-chip.tsx
│       ├── currency-badge.tsx
│       ├── category-badge.tsx
│       ├── amount-display.tsx
│       ├── confirm-modal.tsx
│       ├── empty-state.tsx
│       └── loading-skeleton.tsx
│
├── lib/
│   ├── api-client.ts           # Generic fetch wrapper with auth + 401 handling
│   ├── auth.api.ts
│   ├── cycles.api.ts
│   ├── expense-templates.api.ts
│   └── payment-methods.api.ts
│
├── actions/
│   └── auth.action.ts          # httpOnly cookie read/write (server actions)
│
├── helpers/
│   ├── types.ts                # All TypeScript types and interfaces
│   ├── schemas.ts              # Yup validation schemas
│   └── formatters.ts           # Currency/date formatters
│
└── middleware.ts               # Auth guard — blocks (app) without cookie
```

---

## Component Pattern

Each feature uses a **single-file** approach:

```text
components/{feature}/
├── index.tsx    # Card list + modals + all local state — no HeroUI inside
└── actions.ts   # Thin async wrappers calling lib/*.api.ts with token
```

**Avoid** `table.tsx` / `render-cell.tsx` split for new features — the
notebook card pattern renders everything inline in `index.tsx`.

---

## API Layer

```text
                ┌─────────────────────────┐
     Component  │  components/*/actions.ts │  ← async functions, inject token
                └───────────┬─────────────┘
                            │
                ┌───────────▼─────────────┐
                │    lib/*.api.ts          │  ← pure API calls, no auth logic
                └───────────┬─────────────┘
                            │
                ┌───────────▼─────────────┐
                │   lib/api-client.ts      │  ← fetch wrapper, 401 handling
                └─────────────────────────┘
```

- `getAuthToken()` in `actions/auth.action.ts` reads the httpOnly cookie
  server-side
- `apiClient` returns `{ success: true, data } | { success: false, error }`
- 401 responses clear the cookie and redirect to `/login`

---

## Auth Flow

1. User submits login form → `loginUser()` in `lib/api-client.ts`
2. Token stored in `httpOnly` cookie by `actions/auth.action.ts`
3. `middleware.ts` reads the cookie on every `(app)` request — redirects to
   `/login` if missing
4. Components call `actions.ts` functions which call `getAuthToken()` to
   inject the Bearer token into API requests

---

## CSS Architecture

All notebook styles live in `app/globals.css` in two sections:

1. **HeroUI + Tailwind imports** (first two lines — do not reorder)
2. **`:root` CSS variables** — notebook colour palette
3. **`nb-*` prefixed classes** — all notebook layout and component styles

Do **not** add notebook styles inline or in separate CSS files. Keep everything
in `globals.css` so the full design system is in one place.

### CSS Variable Reference

| Variable | Value | Role |
|---|---|---|
| `--paper` | `#fdf8f0` | Page background |
| `--paper-dark` | `#f5eed8` | Nav tab background |
| `--paper-lines` | `#b8c4e0` | Ruled line colour |
| `--cover-bg` | `#2c4a3e` | Cover bar, active nav |
| `--cover-accent` | `#c9a84c` | Gold border, logo |
| `--ink` | `#2c1810` | Primary text |
| `--ink-light` | `#5a4030` | Secondary text |
| `--font-hand` | `'Caveat', cursive` | Body font |
| `--font-title` | `'Kalam', cursive` | Heading font |
| `--hl-paid` | `rgba(80,200,100,0.35)` | Green highlighter |
| `--hl-pending` | `rgba(255,210,60,0.45)` | Yellow highlighter |
| `--hl-overdue` | `rgba(240,80,70,0.30)` | Red highlighter |
| `--hl-cancelled` | `rgba(180,180,180,0.28)` | Grey highlighter |

---

## Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Frontend dev server: `cd frontend && npm run dev` → <http://localhost:3000>
