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

## Notebook CSS Classes (quick reference)

| Class               | Purpose                                              |
| ------------------- | ---------------------------------------------------- |
| `nb-page-title`     | Large Kalam heading                                  |
| `nb-page-subtitle`  | Small subtitle                                       |
| `nb-section-title`  | Divider heading with line                            |
| `nb-add-btn`        | Dashed "add" button (full width)                     |
| `nb-modal-backdrop` | Full-screen modal overlay                            |
| `nb-modal`          | Modal paper box                                      |
| `nb-modal-title`    | Modal heading                                        |
| `nb-form-group`     | Label + input wrapper                                |
| `nb-form-label`     | Small uppercase label                                |
| `nb-form-input`     | Underline-only text input                            |
| `nb-form-select`    | Bordered select                                      |
| `nb-form-row`       | Flex row for side-by-side fields                     |
| `nb-modal-actions`  | Right-aligned Cancel + Submit row                    |
| `nb-btn-cancel`     | Ghost cancel button                                  |
| `nb-btn-primary`    | Green submit button                                  |
| `nb-empty`          | Centered empty-state block                           |
| `nb-payment-card`   | Payment method card row                              |
| `nb-template-card`  | Template card row                                    |
| `nb-expense-row`    | Expense row (add `.nb-paid/.nb-pending/.nb-overdue`) |
| `nb-cycle-card`     | Cycle summary card                                   |
| `nb-summary-strip`  | Dashed summary box in cycle detail                   |

## Expense Status Colors

Apply as extra class on `.nb-expense-row`:

| Class          | Color                     | Meaning   |
| -------------- | ------------------------- | --------- |
| `nb-paid`      | Green highlight + border  | Paid      |
| `nb-pending`   | Yellow highlight + border | Pending   |
| `nb-overdue`   | Red highlight + border    | Overdue   |
| `nb-cancelled` | Grey, reduced opacity     | Cancelled |

## API Layer

- `lib/*.api.ts` — raw `apiClient` calls, no auth concerns
- `components/*/actions.ts` — thin async wrappers that inject the auth token
  via `getAuthToken()` from `@/actions/auth.action`
- Components call the `actions.ts` functions directly from `useEffect` or
  event handlers

## Auth

- JWT stored in `httpOnly` cookie (`colony-token`) via `actions/auth.action.ts`
- `middleware.ts` blocks unauthenticated access to `(app)` routes server-side
- 401 from API → `apiClient` clears cookie and redirects to `/login`

<!-- END:nextjs-agent-rules -->
