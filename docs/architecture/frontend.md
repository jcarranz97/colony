# Frontend Architecture

Colony's frontend is a Next.js 15 application that communicates with the Colony FastAPI backend over a JSON REST API. It uses HeroUI v3 as the component library, Tailwind CSS v4 for utility styling, and TypeScript throughout.

---

## Tech Stack

| Package | Version | Purpose |
|---|---|---|
| `next` | `^15.x` | App framework — App Router, Server Components, Server Actions |
| `react` / `react-dom` | `^19.x` | UI runtime (React 19 required by HeroUI v3) |
| `typescript` | `^5.x` | Static typing |
| `@heroui/react` | `^3.x` | Component library — Button, Input, Select, Table, Card, Modal, Chip, etc. |
| `@heroui/styles` | `^3.x` | HeroUI CSS styles (required alongside `@heroui/react`) |
| `tailwindcss` | `^4.x` | Utility CSS (Tailwind v4 required by HeroUI v3) |
| `next-themes` | `^0.3.x` | Dark/light mode switching |
| `clsx` | `^2.x` | Conditional className composition |
| `formik` | `^2.x` | Form state management |
| `yup` | `^1.x` | Schema-based form validation |
| `react-icons` | `^5.x` | Icon set |
| `date-fns` | `^3.x` | Date arithmetic — cycle length calculations, due date formatting |

---

## HeroUI Design Principles

The following 10 principles from the [HeroUI documentation](https://heroui.com/docs/react/getting-started/design-principles) govern all component usage and customization decisions in this project.

| # | Principle | Application in Colony |
|---|---|---|
| 1 | **Semantic Intent Over Visual Style** | Use `color="primary"` / `color="danger"` / `color="success"` — never apply raw Tailwind color classes to HeroUI components |
| 2 | **Accessibility as Foundation** | HeroUI is built on React Aria — keyboard navigation and screen reader support come for free; never override ARIA attributes |
| 3 | **Composition Over Configuration** | Use compound components (e.g., `<Table>` + `<TableBody>` + `<TableRow>`) rather than monolithic config props |
| 4 | **Progressive Disclosure** | Start with the minimum required props; add `classNames`, `variant`, or `size` only when the default is insufficient |
| 5 | **Predictable Behavior** | Use the standard size set (`sm` / `md` / `lg`) and variant names consistently across all components |
| 6 | **Type Safety First** | HeroUI component props are fully typed — let TypeScript IntelliSense guide prop selection rather than guessing |
| 7 | **Separation of Styles and Logic** | Customize appearance via the `classNames` prop or CSS variables, not by wrapping components in extra `div`s |
| 8 | **Developer Experience Excellence** | Use HeroUI's descriptive error messages and component documentation when debugging display issues |
| 9 | **Complete Customization** | Use CSS variables (`--heroui-*`) for global theme overrides; use `classNames` for per-instance overrides |
| 10 | **Open and Extensible** | Wrap HeroUI components in `components/shared/` only when Colony-specific behavior (e.g., status color-coding) needs to be centralized |

---

## Project Structure

```
frontend/
├── app/                              # Next.js App Router root
│   ├── layout.tsx                    # Root HTML shell — wraps with <Providers>
│   ├── providers.tsx                 # HeroUIProvider + NextThemesProvider
│   ├── (auth)/                       # Public route group — no auth required
│   │   ├── layout.tsx                # Centered card layout, no sidebar
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   └── (app)/                        # Protected route group — requires auth cookie
│       ├── layout.tsx                # App shell — Sidebar + Navbar
│       ├── page.tsx                  # Redirect → /cycles
│       ├── payment-methods/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── expense-templates/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── cycles/
│       │   ├── page.tsx
│       │   └── [id]/
│       │       ├── page.tsx
│       │       └── summary/page.tsx
│       └── settings/
│           └── page.tsx
│
├── components/                       # Feature-organized UI components
│   ├── auth/
│   │   ├── login.tsx                 # Login form (Formik + Yup)
│   │   ├── register.tsx              # Registration form
│   │   └── auth-layout.tsx           # Split-panel auth shell
│   ├── payment-methods/
│   │   ├── index.tsx                 # List page root
│   │   ├── table.tsx                 # PaymentMethodsTable
│   │   ├── render-cell.tsx           # Per-column cell renderer
│   │   ├── add-payment-method.tsx    # Create modal
│   │   ├── edit-payment-method.tsx   # Edit modal
│   │   └── actions.ts                # fetch/create/update/delete helpers
│   ├── expense-templates/
│   │   ├── index.tsx
│   │   ├── table.tsx
│   │   ├── render-cell.tsx
│   │   ├── add-expense-template.tsx
│   │   ├── edit-expense-template.tsx
│   │   ├── recurrence-config-builder.tsx  # Dynamic recurrence form sub-component
│   │   └── actions.ts
│   ├── cycles/
│   │   ├── index.tsx                 # Cycle card grid
│   │   ├── cycle-card.tsx            # Per-cycle card component
│   │   ├── create-cycle.tsx          # Create cycle modal
│   │   ├── cycle-detail/
│   │   │   ├── index.tsx             # Cycle detail root
│   │   │   ├── cycle-header.tsx      # Name, dates, status, income
│   │   │   ├── expenses-table.tsx    # Filterable expense list
│   │   │   ├── expense-filters.tsx   # Filter bar (status, category, currency, method)
│   │   │   ├── add-expense.tsx       # Add manual expense modal
│   │   │   ├── edit-expense.tsx      # Edit expense modal
│   │   │   └── render-cell.tsx
│   │   ├── cycle-summary/
│   │   │   ├── index.tsx             # Summary page root
│   │   │   ├── financial-summary-cards.tsx
│   │   │   ├── payment-method-breakdown.tsx
│   │   │   ├── currency-stats.tsx
│   │   │   └── status-breakdown.tsx
│   │   └── actions.ts
│   ├── layout/
│   │   ├── layout.tsx                # App shell composition
│   │   └── layout-context.ts         # SidebarContext
│   ├── sidebar/
│   │   ├── sidebar.tsx
│   │   └── sidebar-item.tsx
│   ├── navbar/
│   │   ├── navbar.tsx
│   │   └── user-dropdown.tsx         # Avatar, profile link, logout
│   ├── settings/
│   │   └── index.tsx                 # Profile + password tabs
│   └── shared/
│       ├── status-chip.tsx           # CycleStatus / ExpenseStatus colored chip
│       ├── currency-badge.tsx        # USD / MXN badge
│       ├── category-badge.tsx        # fixed / variable badge
│       ├── amount-display.tsx        # Locale-formatted decimal
│       ├── confirm-modal.tsx         # Generic destructive-action confirmation
│       ├── empty-state.tsx           # Empty list placeholder
│       └── loading-skeleton.tsx      # Table/card loading state
│
├── actions/
│   └── auth.action.ts                # createAuthCookie / deleteAuthCookie / getAuthToken
│
├── lib/                              # API client layer
│   ├── api-client.ts                 # Base fetch wrapper — auth header injection + error normalization
│   ├── auth.api.ts
│   ├── payment-methods.api.ts
│   ├── expense-templates.api.ts
│   └── cycles.api.ts
│
├── helpers/
│   ├── schemas.ts                    # All Yup validation schemas
│   ├── types.ts                      # All TypeScript types and interfaces
│   └── formatters.ts                 # Currency, date, and balance formatters
│
├── config/
│   └── fonts.ts                      # Next.js Google Font declarations
│
├── styles/
│   └── globals.css                   # Tailwind + HeroUI CSS imports
│
├── public/
├── .env.local                        # Local dev environment variables
├── .env.example                      # Template for required env vars
├── middleware.ts                     # Auth guard (cookie check + route protection)
├── next.config.ts                    # Next.js config (standalone output)
├── tailwind.config.ts                # Tailwind config
├── postcss.config.js
├── tsconfig.json                     # TypeScript config with @/* path alias
└── Dockerfile                        # Multi-stage Docker build
```

---

## Routing

Route groups use Next.js App Router conventions. The `(auth)` group handles unauthenticated pages; the `(app)` group is protected by `middleware.ts`.

### Layout Nesting

```
app/layout.tsx                        ← HTML root + <Providers />
  ├── app/(auth)/layout.tsx           ← Centered auth layout
  │     ├── /login
  │     └── /register
  └── app/(app)/layout.tsx            ← Sidebar + Navbar shell
        ├── /                         → redirect to /cycles
        ├── /payment-methods
        ├── /payment-methods/[id]
        ├── /expense-templates
        ├── /expense-templates/[id]
        ├── /cycles
        ├── /cycles/[id]
        ├── /cycles/[id]/summary
        └── /settings
```

### Route Table

| URL | Use Cases | Notes |
|---|---|---|
| `/login` | UC-02 | Redirects to `/cycles` if already authenticated |
| `/register` | UC-01 | Redirects to `/cycles` if already authenticated |
| `/` | — | Redirects to `/cycles` |
| `/payment-methods` | UC-04, UC-06, UC-07 | Modal-driven inline CRUD |
| `/payment-methods/[id]` | UC-05 | Edit detail page |
| `/expense-templates` | UC-08, UC-10, UC-11 | Modal-driven inline CRUD |
| `/expense-templates/[id]` | UC-09 | Edit detail page |
| `/cycles` | UC-12, UC-13 | Card grid + create modal |
| `/cycles/[id]` | UC-14, UC-16–19 | Expense list with filters |
| `/cycles/[id]/summary` | UC-15 | Financial summary view |
| `/settings` | — | User profile + password change |

---

## Authentication

### JWT Storage

The backend issues a JWT with a 30-minute TTL. The frontend stores it in an `httpOnly` cookie named `colony-token`. This prevents JavaScript access, protecting against XSS attacks. The cookie is set server-side via a Next.js Server Action immediately after a successful login.

```
Login flow:
  1. User submits login form
  2. Client calls POST /api/v1/auth/login
  3. Backend returns { access_token, token_type, expires_in }
  4. createAuthCookie(token) Server Action sets:
       Set-Cookie: colony-token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/
  5. Browser redirects to /cycles
```

### Route Protection (Middleware)

`middleware.ts` runs before every render. It enforces the auth boundary with no reliance on client-side React:

- Unauthenticated requests to any `(app)` route → redirect to `/login`
- Authenticated requests to `/login` or `/register` → redirect to `/cycles`
- JWT signature validation is delegated to the API — if the API returns 401, the `apiClient` handles redirect

### Token Expiry

The `apiClient` base wrapper intercepts HTTP 401 responses:

1. Calls `deleteAuthCookie()` Server Action
2. Redirects to `/login`

There is no silent token refresh — the backend does not expose a refresh token endpoint.

### Server Actions

```typescript
// actions/auth.action.ts
"use server";
import { cookies } from "next/headers";

export const createAuthCookie = async (token: string) => {
  (await cookies()).set("colony-token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 60,  // match 30-minute backend TTL
  });
};

export const deleteAuthCookie = async () => {
  (await cookies()).delete("colony-token");
};

export const getAuthToken = async (): Promise<string | undefined> => {
  return (await cookies()).get("colony-token")?.value;
};
```

---

## API Client Layer

### Base Client

`lib/api-client.ts` is the single typed fetch wrapper used by all feature API modules.

**Responsibilities:**

- Reads `colony-token` cookie and injects `Authorization: Bearer <token>` header
- Sets `Content-Type: application/json`
- Calls `fetch(${NEXT_PUBLIC_API_URL}${path}, options)`
- Returns `{ success: true; data: T }` on success
- Returns `{ success: false; error: { code: string; message: string } }` on API error
- On HTTP 401: deletes cookie and redirects to `/login`

**Return type:**

```typescript
type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: { code: string; message: string } };
```

### Feature API Modules

Each module in `lib/` wraps `apiClient` with typed helpers for one domain:

| Module | Helpers |
|---|---|
| `lib/auth.api.ts` | `login`, `register`, `getMe`, `updateMe`, `updatePassword` |
| `lib/payment-methods.api.ts` | `fetchPaymentMethods`, `createPaymentMethod`, `updatePaymentMethod`, `deletePaymentMethod` |
| `lib/expense-templates.api.ts` | `fetchExpenseTemplates`, `createExpenseTemplate`, `updateExpenseTemplate`, `deleteExpenseTemplate` |
| `lib/cycles.api.ts` | `fetchCycles`, `createCycle`, `updateCycle`, `deleteCycle`, `getCycleSummary`, `fetchCycleExpenses`, `createCycleExpense`, `updateCycleExpense`, `deleteCycleExpense` |

---

## State Management

Colony uses `useState` as the primary state mechanism. React Context is used only for true cross-tree UI state (sidebar). There is no Redux, Zustand, or SWR.

| Data | Location | Reason |
|---|---|---|
| JWT token | `httpOnly` cookie | Security — inaccessible to JavaScript |
| Payment methods list | `useState` in payment methods page | Local to that feature |
| Templates list | `useState` in templates page | Local to that feature |
| Cycle list | `useState` in cycles page | Local to that feature |
| Cycle expenses | `useState` in cycle detail | Local to cycle detail |
| Cycle summary | `useState` in summary page | Local to summary page |
| Sidebar collapsed | `SidebarContext` | Cross-tree UI state |
| Form state | Formik internal | Managed by Formik |
| Modal open/close | `useState` in parent | Simple boolean |
| Active filters | `useState` in filter bar | Local UI state |

---

## Form Handling

All forms use **Formik** for state management and **Yup** for schema validation.

### Pattern

```typescript
<Formik initialValues={initialValues} validationSchema={SomeSchema} onSubmit={handleSubmit}>
  {({ values, errors, touched, handleChange, handleSubmit }) => (
    <Input
      value={values.fieldName}
      isInvalid={!!errors.fieldName && !!touched.fieldName}
      errorMessage={errors.fieldName}
      onChange={handleChange("fieldName")}
    />
  )}
</Formik>
```

### Validation Schemas (`helpers/schemas.ts`)

All Yup schemas live in a single file:

| Schema | Used In |
|---|---|
| `LoginSchema` | Login form |
| `RegisterSchema` | Registration form |
| `PaymentMethodSchema` | Create/edit payment method |
| `ExpenseTemplateSchema` | Create/edit expense template (includes recurrence_config sub-schema) |
| `CycleCreateSchema` | Create cycle (end_date auto-computed) |
| `CycleExpenseSchema` | Add/edit cycle expense |
| `UpdateProfileSchema` | Settings profile tab |
| `UpdatePasswordSchema` | Settings password tab |

The `ExpenseTemplateSchema` uses Yup `when()` to validate `recurrence_config` conditionally based on `recurrence_type`:

```typescript
recurrence_config: object().when("recurrence_type", {
  is: "weekly",
  then: (s) => s.shape({ day_of_week: number().min(0).max(6).required() }),
}).when("recurrence_type", {
  is: "bi_weekly",
  then: (s) => s.shape({ interval_days: number().positive().integer().required() }),
}).when("recurrence_type", {
  is: "monthly",
  then: (s) => s.shape({
    day_of_month: number().min(1).max(31).required(),
    handle_month_end: boolean().optional(),
  }),
}).when("recurrence_type", {
  is: "custom",
  then: (s) => s.shape({
    interval: number().positive().integer().required(),
    unit: mixed().oneOf(["days", "weeks", "months"]).required(),
  }),
}),
```

---

## Component Architecture

### Shared Components (`components/shared/`)

| Component | Props | Behavior |
|---|---|---|
| `<StatusChip status />` | `CycleStatus \| ExpenseStatus` | draft=gray, active=blue, completed=green, pending=yellow, paid=green, overdue=red, cancelled=gray |
| `<CurrencyBadge currency />` | `"USD" \| "MXN"` | USD=blue (primary), MXN=orange (warning) |
| `<CategoryBadge category />` | `"fixed" \| "variable"` | fixed=purple (secondary), variable=teal (success) |
| `<AmountDisplay amount currency />` | `string, string` | `Intl.NumberFormat` with locale currency symbol |
| `<ConfirmModal />` | `isOpen, onClose, onConfirm, title, message` | Two-button destructive-action confirmation |
| `<EmptyState />` | `message, icon` | Centered empty list placeholder |
| `<LoadingSkeleton />` | `rows` | Table row skeleton during loading |

### Feature Folder Pattern

Each feature mirrors the tienda-web convention:

```
components/{feature}/
  index.tsx         ← Page root: breadcrumb, header, action buttons
  table.tsx         ← HeroUI <Table> with column definitions
  render-cell.tsx   ← Switch on columnKey → returns JSX per cell
  add-{entity}.tsx  ← Create modal with Formik form
  edit-{entity}.tsx ← Edit modal pre-populated from existing record
  actions.ts        ← fetch/create/update/delete helpers (wraps lib/ modules)
```

### Recurrence Config Builder

`components/expense-templates/recurrence-config-builder.tsx` renders a different sub-form based on `recurrence_type`. It uses `useFormikContext()` to avoid prop-drilling Formik state, and resets `recurrence_config` to `{}` when `recurrence_type` changes.

```
weekly    → Day of Week select (Sunday=0 … Saturday=6)
bi_weekly → Interval Days number input (default: 14)
monthly   → Day of Month (1–31) + Handle Month End toggle
custom    → Every N + Unit (days/weeks/months) + optional Day of Month
```

### Expense Table Filters

`components/cycles/cycle-detail/expense-filters.tsx` renders a horizontal filter bar. Filter state lives in the parent `cycle-detail/index.tsx` and is passed as query parameters to `fetchCycleExpenses()` when changed:

| Filter | Options |
|---|---|
| Status | all, pending, paid, overdue, cancelled |
| Category | all, fixed, variable |
| Currency | all, USD, MXN |
| Payment Method | all, {user's payment methods} |

### Cycle Summary Layout

The `/cycles/[id]/summary` page is composed from four sub-components:

```
Row 1: [Income] [Total Expenses] [Net Balance]  ← green if positive, red if negative
Row 2: [Fixed Expenses] [Variable Expenses]
Row 3: [USA Expenses USD] [Mexico Expenses MXN→USD]

Row 4: Payment Method Breakdown Table
        Method | Total | Paid | Pending | Count

Row 5: Status Chips
        Pending(N)  Paid(N)  Overdue(N)  Cancelled(N)
```

---

## Styling

HeroUI v3 uses a **CSS import** approach — there is no Tailwind plugin.

### Installation

```bash
npm install @heroui/react @heroui/styles
```

### CSS Setup

Import order is mandatory — `tailwindcss` must come first:

```css
/* styles/globals.css */
@import "tailwindcss";
@import "@heroui/styles";
```

See the [HeroUI Quick Start](https://heroui.com/docs/react/getting-started/quick-start) for full setup details.

### Provider Setup

```typescript
// app/providers.tsx
"use client";
import { HeroUIProvider } from "@heroui/react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <HeroUIProvider>
      <NextThemesProvider defaultTheme="system" attribute="class">
        {children}
      </NextThemesProvider>
    </HeroUIProvider>
  );
}
```

### Dark Mode

`next-themes` sets the `class` attribute on `<html>`. HeroUI reads the `dark` class to switch its color tokens. The navbar includes a theme toggle button using `useTheme()` from `next-themes`.

### Color Conventions

| Status / Value | HeroUI `color` | Usage |
|---|---|---|
| `draft` | `default` (gray) | Cycle status |
| `active` | `primary` (blue) | Cycle status |
| `completed` | `success` (green) | Cycle status |
| `pending` | `warning` (yellow) | Expense status |
| `paid` | `success` (green) | Expense status |
| `overdue` | `danger` (red) | Expense status |
| `cancelled` | `default` (gray) | Expense status |
| `USD` | `primary` (blue) | Currency badge |
| `MXN` | `warning` (orange) | Currency badge |
| `fixed` | `secondary` (purple) | Category badge |
| `variable` | `success` (teal) | Category badge |

---

## Data Flow

### Read (List Page)

```
Component mounts
  → useEffect triggers actions.ts fetch helper
    → lib/*.api.ts calls apiClient(path, token)
      → fetch(NEXT_PUBLIC_API_URL + path) with Authorization header
        → API returns JSON list
  → apiClient returns { success: true, data: [...] }
  → setState(data) → React re-renders table
```

### Mutation (Create / Update)

```
User fills Formik form → Yup validates
  → handleSubmit calls create/updateXxx(values, token)
    → lib helper calls apiClient with POST/PUT
      → On success: close modal, refresh list (refetch or splice state)
      → On error: setError(error.message) displayed inline
```

### Mark Expense as Paid (UC-19)

```
User clicks paid toggle
  → updateCycleExpense(cycleId, expId, { paid: !paid }, token)
    → On success: optimistic local state update (no full re-fetch)
```

---

## Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

`NEXT_PUBLIC_API_URL` is the only required variable. The `NEXT_PUBLIC_` prefix exposes it to both Server Components and Client Components.

### Docker

`next.config.ts` must include `output: "standalone"` for Docker deployment:

```typescript
const nextConfig: NextConfig = {
  output: "standalone",
};
```

Add a `frontend` service to `docker-compose.yml`:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: colony-frontend
  environment:
    NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
  ports:
    - "3000:3000"
  depends_on:
    - backend
  restart: unless-stopped
```

---

## Implementation Plan

Each step is self-contained and can be executed independently in order.

### Step 1 — Scaffold the Project

**Goal**: Create the Next.js 15 project with TypeScript, Tailwind v4, and App Router inside `colony/frontend/`.

```bash
cd /home/jcarranz/repos/colony
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir=false \
  --import-alias "@/*"
cd frontend
```

Update `next.config.ts`:

```typescript
import type { NextConfig } from "next";
const nextConfig: NextConfig = { output: "standalone" };
export default nextConfig;
```

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Create `.env.example` with the same keys but no values.

**Verify**: `npm run dev` starts on port 3000 with no errors.

---

### Step 2 — Install HeroUI and Configure Styles

**Goal**: Install HeroUI v3, configure via CSS imports, set up Providers, and establish dark mode.

> HeroUI v3 uses a CSS-import approach — there is no Tailwind plugin or `tailwind.config.ts` changes needed.

```bash
npm install @heroui/react @heroui/styles next-themes clsx
npm install react-icons date-fns formik yup
npm install -D @types/node
```

Update `styles/globals.css` (import order is mandatory):

```css
@import "tailwindcss";
@import "@heroui/styles";
```

Create `app/providers.tsx` (see [Provider Setup](#provider-setup) above).

Update `app/layout.tsx` to wrap with `<Providers>` and apply the Inter font.

Create `config/fonts.ts`:

```typescript
import { Inter } from "next/font/google";
export const fontSans = Inter({ subsets: ["latin"], variable: "--font-sans" });
```

**Verify**: A HeroUI `<Button color="primary">Test</Button>` renders with correct HeroUI styling.

---

### Step 3 — Implement the API Client Layer

**Goal**: Build the typed fetch wrapper and all feature API modules.

Create `lib/api-client.ts`:

- Generic `apiClient<T>(path, options?)` returning `ApiResponse<T>`
- Injects `Authorization: Bearer <token>` and `Content-Type: application/json`
- Reads token from `colony-token` cookie (`document.cookie` on client; passed explicitly from Server Components)
- Returns `{ success: true; data: T }` or `{ success: false; error: { code, message } }`
- On 401: deletes cookie and redirects to `/login`

Create `helpers/types.ts` — TypeScript interfaces mirroring all backend schemas:

- `Token`, `UserResponse`, `UpdateUserRequest`, `UpdatePasswordRequest`
- `PaymentMethod`, `CreatePaymentMethodRequest`, `UpdatePaymentMethodRequest`
- `ExpenseTemplate`, `CreateExpenseTemplateRequest` with `RecurrenceConfig` discriminated union
- `Cycle`, `CreateCycleRequest`, `CycleSummary`
- `CycleExpense`, `CreateCycleExpenseRequest`, `CycleExpensesResponse`
- Enums: `CurrencyCode`, `PaymentMethodType`, `ExpenseCategory`, `RecurrenceType`, `CycleStatus`, `ExpenseStatus`

Create `helpers/formatters.ts`:

- `formatAmount(amount, currency)` — `Intl.NumberFormat` with locale currency symbol
- `formatDate(dateStr)` — `date-fns format(parseISO(dateStr), "MMM d, yyyy")`
- `formatDateShort(dateStr)` — `date-fns format(parseISO(dateStr), "MMM d")`
- `computeCycleEndDate(startDate)` — `date-fns addDays(parseISO(startDate), 41)` (6 weeks = 42 days, end = start + 41)

Create `lib/auth.api.ts`, `lib/payment-methods.api.ts`, `lib/expense-templates.api.ts`, `lib/cycles.api.ts` (see [Feature API Modules](#feature-api-modules) above).

**Verify**: `npx tsc --noEmit` — zero type errors.

---

### Step 4 — Auth Server Actions and Middleware

**Goal**: Set up the `httpOnly` JWT cookie and route protection.

Create `actions/auth.action.ts` (see [Server Actions](#server-actions) above).

Create `middleware.ts`:

```typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_PAGES = ["/login", "/register"];
const PROTECTED = ["/payment-methods", "/expense-templates", "/cycles", "/settings"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("colony-token");
  const { pathname } = request.nextUrl;

  const isAuthPage = AUTH_PAGES.some((p) => pathname.startsWith(p));
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p)) || pathname === "/";

  if (isAuthPage && token) return NextResponse.redirect(new URL("/cycles", request.url));
  if (isProtected && !token) return NextResponse.redirect(new URL("/login", request.url));
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/login", "/register", "/payment-methods/:path*", "/expense-templates/:path*", "/cycles/:path*", "/settings/:path*"],
};
```

**Verify**: Visiting `/cycles` without a cookie redirects to `/login`.

---

### Step 5 — Auth Pages (Login & Register)

**Goal**: Implement login and register pages to validate the full API → cookie → redirect flow.

Create:

- `app/(auth)/layout.tsx` — centered card layout, no sidebar
- `app/(auth)/login/page.tsx` → renders `<Login />`
- `app/(auth)/register/page.tsx` → renders `<Register />`

`components/auth/login.tsx`:

- Formik form with `LoginSchema` (email + password)
- On success: `createAuthCookie(token)` → `router.replace("/cycles")`
- On error: inline error message below form
- HeroUI: `Card`, `CardBody`, `Input`, `Button`
- Link to `/register`

`components/auth/register.tsx`:

- Formik form with `RegisterSchema` (email, password, first_name, last_name)
- On success: auto-login → `createAuthCookie()` → redirect to `/cycles`
- Link to `/login`

Create `helpers/schemas.ts` with `LoginSchema` and `RegisterSchema` (extended in later steps).

**Verify**: Login with seeded test user, confirm `colony-token` cookie is set in browser DevTools, confirm redirect to `/cycles`.

---

### Step 6 — App Shell (Layout, Sidebar, Navbar)

**Goal**: Create the full dashboard shell that wraps all `(app)` routes.

Create `components/layout/layout-context.ts` — `SidebarContext` with `collapsed` and `setCollapsed`.

Create `components/layout/layout.tsx`:

- `"use client"` component
- Provides `SidebarContext`
- Renders `<Sidebar />` (left) and `<Navbar />` (top)
- Main content area fills remaining space

Create `components/sidebar/sidebar.tsx`:

- Nav items: Cycles (`/cycles`), Payment Methods (`/payment-methods`), Expense Templates (`/expense-templates`), Settings (`/settings`)
- Active route highlighted via `usePathname()`
- Collapses on mobile

Create `components/navbar/navbar.tsx`:

- App title left, `<UserDropdown />` right
- Logout: `deleteAuthCookie()` + `router.push("/login")`
- Dark mode toggle using `useTheme()`

Create `app/(app)/layout.tsx` wrapping with `<Layout>`.

Create `app/(app)/page.tsx` redirecting to `/cycles`.

Create all `components/shared/` components (see [Shared Components](#shared-components) above).

**Verify**: After login, `/cycles` (empty page) shows the full sidebar + navbar shell without layout errors.

---

### Step 7 — Payment Methods Feature

**Goal**: Implement the simplest full CRUD feature — establishes and validates the table + modal + actions pattern.

Create (following the [Feature Folder Pattern](#feature-folder-pattern)):

- `components/payment-methods/actions.ts` — fetch, create, update, deactivate
- `components/payment-methods/table.tsx` — columns: Name, Type, Currency, Status, Actions
- `components/payment-methods/render-cell.tsx` — renders each column type
- `components/payment-methods/add-payment-method.tsx` — create modal with `PaymentMethodSchema`
- `components/payment-methods/edit-payment-method.tsx` — edit modal pre-populated from record
- `components/payment-methods/index.tsx` — list root with `useEffect` fetch, empty/loading states
- `app/(app)/payment-methods/page.tsx` → renders `<PaymentMethods />`
- `app/(app)/payment-methods/[id]/page.tsx` → renders `<EditPaymentMethod />`

Add `PaymentMethodSchema` to `helpers/schemas.ts`.

**Verify**: Create a payment method → appears in list. Edit it → changes persist. Deactivate it → shows as inactive. Backend returns 204 on deactivate.

---

### Step 8 — Expense Templates Feature

**Goal**: Implement the most complex form — validates the dynamic recurrence config builder pattern.

Create (following the [Feature Folder Pattern](#feature-folder-pattern)):

- `components/expense-templates/recurrence-config-builder.tsx` — dynamic sub-form using `useFormikContext()`
- `components/expense-templates/add-expense-template.tsx` — multi-field create modal
- `components/expense-templates/edit-expense-template.tsx` — edit modal pre-populated from record
- All other standard feature files (table, render-cell, actions, index)
- `app/(app)/expense-templates/page.tsx` and `[id]/page.tsx`

Add `ExpenseTemplateSchema` (with conditional `recurrence_config`) to `helpers/schemas.ts`.

**Verify**: Create a monthly "Rent" template (day_of_month=1) — verify recurrence config saved. Create a weekly "Groceries" template. Edit a template — verify recurrence builder pre-populates correctly.

---

### Step 9 — Cycles Feature

**Goal**: Implement the multi-page cycles feature — cycle list, detail with filterable expenses, and expense CRUD.

**9a — Cycle List** (`/cycles`):

- `components/cycles/cycle-card.tsx` — HeroUI `<Card>` with name, dates, status chip, income, expense count/balance
- `components/cycles/create-cycle.tsx` — Formik modal with `CycleCreateSchema`; `end_date` auto-computed via `computeCycleEndDate()` and displayed read-only
- `components/cycles/index.tsx` — responsive card grid, pagination (HeroUI `<Pagination>`), empty/loading states

**9b — Cycle Detail** (`/cycles/[id]`):

- `cycle-header.tsx` — name, dates, status chip, income, link to summary; lock notice if completed
- `expense-filters.tsx` — filter bar (status, category, currency, payment method); re-fetches on change
- `expenses-table.tsx` — all columns including paid toggle (`<Switch>`) and actions; actions hidden if `status === "completed"`
- `add-expense.tsx` and `edit-expense.tsx` — Formik modals with `CycleExpenseSchema`
- `cycle-detail/index.tsx` — fetches cycle + expenses; passes `isReadOnly` to table

Add `CycleCreateSchema` and `CycleExpenseSchema` to `helpers/schemas.ts`.

**Verify**: Create cycle with `generate_from_templates: true` → template expenses appear. Add manual expense. Mark one as paid. Filter by status. Edit an expense. Delete an expense. Confirm completed cycle is read-only.

---

### Step 10 — Cycle Summary Page

**Goal**: Implement the read-only financial analytics view.

Create:

- `components/cycles/cycle-summary/financial-summary-cards.tsx` — Income, Total Expenses, Net Balance (green/red); Fixed, Variable; USA, Mexico rows
- `components/cycles/cycle-summary/payment-method-breakdown.tsx` — table from `summary.by_payment_method[]`
- `components/cycles/cycle-summary/status-breakdown.tsx` — `<Chip>` row from `summary.status_breakdown`
- `components/cycles/cycle-summary/index.tsx` — fetches `getCycleSummary()`, composes sub-components, back button
- `app/(app)/cycles/[id]/summary/page.tsx`

**Verify**: Navigate to a cycle summary. All financial figures match the API response. Net Balance is green for surplus, red for deficit.

---

### Step 11 — Settings Page

**Goal**: Allow users to update their profile and change their password.

Create:

- `components/settings/index.tsx` — `"use client"` component; fetches `getMe()` on mount; two HeroUI `<Tabs>`:
    - **Profile tab**: pre-populated form (first_name, last_name, preferred_currency); uses `UpdateProfileSchema`; calls `updateMe()`
    - **Password tab**: empty form (current_password, new_password, confirm_password); uses `UpdatePasswordSchema`; calls `updatePassword()`
- Success feedback via HeroUI `addToast()` on save; inline error messages on failure
- `app/(app)/settings/page.tsx`

Add `UpdateProfileSchema` and `UpdatePasswordSchema` to `helpers/schemas.ts`.

**Verify**: Update first name → re-fetch confirms change persists. Change password → logout → login with new password succeeds.
