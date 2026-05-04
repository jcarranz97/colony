# Colony Backend

FastAPI backend for Colony, a personal expense management app. Python 3.13+,
SQLAlchemy 2.0, Pydantic 2.0, PostgreSQL, JWT auth.

---

## Running Commands

```bash
# Start everything (recommended)
docker-compose up --build          # API at http://localhost:8000

# Backend only (no Docker)
cd backend
uv sync
uv run fastapi dev                 # hot reload

# Tests — PYTHONPATH=. is required; without it, system packages (e.g. ROS)
# can leak into the path and cause import errors at pytest startup.
PYTHONPATH=. uv run pytest                      # all tests
PYTHONPATH=. uv run pytest tests/cycles/        # single domain
PYTHONPATH=. uv run pytest -k test_name         # single test

# Linting & formatting
PYTHONPATH=. uv run ruff check . --fix
PYTHONPATH=. uv run ruff format .

# Type checking
PYTHONPATH=. uv run pyright .

# Migrations (Alembic)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

Pre-commit runs Ruff, Pyright, Hadolint, and YAML/JSON validators on every
commit — don't bypass with `--no-verify`.

---

## Project Layout

```text
backend/
├── app/
│   ├── main.py          # FastAPI app factory, CORS, router registration, exception handlers
│   ├── config.py        # Settings (env vars via Pydantic BaseSettings)
│   ├── database.py      # SQLAlchemy engine, SessionLocal, get_db()
│   ├── exceptions.py    # AppExceptionError base + global exception handlers
│   ├── dependencies.py  # Re-exports: CurrentActiveUser, CurrentUser, get_db
│   ├── models.py        # BaseModel (id UUID, created_at, updated_at, active bool)
│   ├── schemas.py       # Global Pydantic schemas
│   └── <domain>/        # auth | households | payment_methods | recurrent_expenses | cycles
├── alembic/             # DB migrations
├── tests/               # pytest suite (mirrors domain layout)
└── pyproject.toml
```

### Domain Module Layout

Every domain (`auth`, `households`, `payment_methods`, `recurrent_expenses`,
`cycles`) has exactly this structure — follow it when adding a new domain:

```text
app/<domain>/
├── router.py        # FastAPI routes — thin; delegates to service
├── schemas.py       # Pydantic request/response models
├── models.py        # SQLAlchemy ORM model (inherits BaseModel)
├── service.py       # All business logic; no HTTP concerns
├── dependencies.py  # Domain-level Depends() helpers
├── exceptions.py    # Domain-specific exceptions (inherit AppExceptionError)
├── constants.py     # Enums, error codes, business constants
└── utils.py         # Pure helper functions (present only in auth, cycles)
```

---

## Code Conventions

- **Type hints** on every function — no untyped code.
- **Google-style docstrings** on public functions.
- **88-character** line limit (Ruff enforces).
- **Double quotes** everywhere.
- **Dependency injection** via `Annotated[X, Depends(Y)]` pattern.
- All routes prefixed `/api/v1/`.
- JWT Bearer token in `Authorization` header.

### Router Pattern

```python
@router.post("/", response_model=FooResponse, status_code=201)
async def create_foo(
    payload: FooCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentActiveUser,
) -> FooResponse:
    return FooService.create_foo(db, payload, current_user.id)
```

- Routers are thin — no business logic, only call service methods.
- Always use `CurrentActiveUser` (not `CurrentUser`) unless the endpoint
  explicitly serves inactive users.
- For data endpoints (payment methods, cycles, etc.) use `CurrentActiveHousehold`
  (imported from `app.dependencies`) instead of extracting `user.id`.
  All domain data is owned by a household, not a user.

### Service Pattern

```python
class FooService:
    @staticmethod
    def create_foo(db: Session, payload: FooCreate, user_id: UUID) -> Foo:
        # business logic here
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
```

- Static methods only — no `self` / `cls` state.
- Raise domain exceptions, never HTTP exceptions.
- Always `db.commit()` + `db.refresh(obj)` after writes.

---

## Error Handling

All exceptions must inherit from `AppExceptionError` (defined in
`app/exceptions.py`). Global handlers in `main.py` convert every
`AppExceptionError` to the standard JSON envelope automatically.

```python
# app/exceptions.py — base class
class AppExceptionError(Exception):
    def __init__(self, error_code, message, status_code=400, details=None): ...

# domain exceptions.py
class FooNotFoundExceptionError(AppExceptionError):
    def __init__(self, foo_id: UUID):
        super().__init__(
            error_code=ErrorCode.FOO_NOT_FOUND,
            message=f"Foo {foo_id} not found.",
            status_code=404,
        )
```

Standard error response (never construct manually):

```json
{ "success": false, "error": { "code": "FOO_NOT_FOUND", "message": "..." } }
```

Rules:

- **Never** raise `HTTPException` directly inside service methods.
- **Always** raise a domain-specific exception and let the global
  handler convert it.
- `ErrorCode` enums live in `constants.py`. Status codes: 400 validation,
  401 auth, 403 forbidden, 404 not found, 409 conflict, 422 unprocessable.
- If the right exception doesn't exist yet, add it to `exceptions.py` with
  a new `ErrorCode` in `constants.py`.

---

## Database Patterns

### Base Model

Every ORM model inherits `BaseModel` from `app/models.py`:

```python
class Foo(BaseModel):
    __tablename__ = "foos"
    household_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))
```

Key rules:

- **UUID primary keys** — always, inherited from BaseModel.
- **Soft deletes** — set `active = False`; never `db.delete()`.
- **Timestamps** — `created_at` and `updated_at` are auto-managed by BaseModel.
- **Cascade deletes** — household-owned data uses `ondelete="CASCADE"` on
  the `household_id` FK.

### Model Changes Require Migrations

Any change to a SQLAlchemy model requires an Alembic migration:

```bash
uv run alembic revision --autogenerate -m "short description"
uv run alembic upgrade head
```

- Adding a nullable column → safe migration.
- Adding a non-nullable column → requires a default or a two-step migration
  (add nullable, backfill, set NOT NULL).
- Renaming a column → **never rename** — add new + deprecate old, or confirm
  the migration is intentional.
- Changing an enum type → requires a PostgreSQL `ALTER TYPE` migration; Alembic
  does not autogenerate this — write it manually.

### Recurrence Config (JSONB — cycles domain)

Stored in `recurrence_config` JSONB column. Structure by type:

| `recurrence_type` | Required keys in `recurrence_config` |
|---|---|
| `weekly` | `day_of_week` (0=Mon … 6=Sun) |
| `bi_weekly` | `interval_days` (positive int) |
| `monthly` | `day_of_month` (1–31), `handle_month_end` (bool) |
| `custom` | `interval` (int), `unit` (days/weeks/months/years) |

Validation lives in `recurrent_expenses/schemas.py` (`_validate_*_config`
helpers). Calculation logic lives in `cycles/utils.py`.

### Multi-Currency

- Store `currency` (USD/MXN) + `amount` (native) + `amount_usd` (converted)
  on `CycleExpense`.
- `ExchangeRate` model holds daily rates; look up with
  `_get_usd_rate(db, from_currency)` in `cycles/service.py`.
- Reporting always aggregates in USD.
- Location is implicitly derived from currency: USD = US, MXN = Mexico.

---

## Authentication

```python
# Correct DI aliases (imported from app/dependencies.py)
from app.dependencies import CurrentActiveUser, CurrentUser

async def endpoint(current_user: CurrentActiveUser): ...
```

- `CurrentActiveUser` — resolves JWT → raises 401/403 if invalid/inactive.
- `CurrentUser` — resolves JWT → raises 401 if invalid (allows inactive).
- `CurrentActiveHousehold` — resolves `current_user.active_household_id` →
  `Household`; raises `UserHasNoActiveHouseholdExceptionError` if null.
  Use this in all data endpoints instead of `current_user.id`.
- Passwords hashed with Argon2ID via `pwdlib`.
- JWT signed with `SECRET_KEY` from config; `ALGORITHM` is HS256 by default.
- Auth uses **username + password** (no email). A default admin user is
  created automatically on first deploy from the `DEFAULT_ADMIN_USERNAME`
  and `DEFAULT_ADMIN_PASSWORD` env vars (defaults: `admin` / `colony-admin`).
- JWT `sub` claim holds the username.

---

## Testing

### Fixtures (backend/tests/conftest.py)

```python
db      # Session — fresh tables per test (create_all → test → drop_all)
client  # TestClient with get_db overridden to use the test session
```

Each domain has its own `tests/<domain>/conftest.py` with domain-specific
fixtures (users, payment methods, cycles, etc.).

### Conventions

- Test files mirror domain layout: `tests/<domain>/test_<layer>.py`
- Class per feature: `class TestCreateFoo:` with `def test_*` methods.
- Every new endpoint needs at least these tests:
  - `test_requires_auth` — 401 without token.
  - `test_<happy_path>` — 200/201 with valid data.
  - `test_not_found` — 404 for unknown ID.
  - `test_other_user_cannot_access` — ownership isolation.
  - `test_<conflict>` — 409 if the domain has uniqueness constraints.
- Use `client.post/get/put/delete("/api/v1/<route>", headers=auth_headers)`.
- Auth headers helper pattern:

```python
def get_auth_headers(client: TestClient, user: User) -> dict:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": RAW_PASSWORD},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
```

- Do not mock the database — tests use a real PostgreSQL test database.
- Do not use `db.delete()` in tests — use the service's soft-delete method.
- Never delete existing tests.

---

## Enums Reference

Defined per domain in `constants.py` but semantically identical across domains:

| Enum | Values |
|---|---|
| `CurrencyCode` | `USD`, `MXN` |
| `PaymentMethodType` | `debit`, `credit`, `cash`, `transfer` |
| `ExpenseCategory` | `fixed`, `variable` |
| `RecurrenceType` | `weekly`, `bi_weekly`, `monthly`, `custom` |
| `CycleStatus` | `draft`, `active`, `completed` |
| `ExpenseStatus` | `pending`, `paid`, `cancelled`, `overdue`, `paid_other`, `skipped` |

If you add a value to one domain's enum, add it to all domains that define the
same enum and update the corresponding database enum type via a migration.

---

## API Shape

All routes prefixed `/api/v1/`. Success responses return data directly
(Pydantic model). Error responses use the standard envelope above.

| Domain | Base path |
|---|---|
| Auth | `/api/v1/auth/` |
| Payment Methods | `/api/v1/payment-methods/` |
| Recurrent Expenses | `/api/v1/recurrent-expenses/` |
| Cycles + Expenses | `/api/v1/cycles/` |

Pagination (cycles list): `?page=1&per_page=20` query params; response
response shape: `{ cycles: [...], pagination: { page, per_page, total,
pages } }`.

Health checks at `/<domain>/health` and root `/health`.

---

## Key Business Rules

1. **Completed cycles are read-only** — the service rejects all mutations
   once `status == "completed"`.
2. **Remaining balance** is recalculated automatically on every expense
   write (`_recalculate_remaining_balance`). Statuses `cancelled`,
   `paid_other`, and `skipped` are all excluded from the expense total
   and therefore do not reduce the remaining balance.
3. **Generate from recurrent expenses** — `CycleCreate.generate_from_templates=true`
   triggers recurrence calculation via `cycles/utils.py` and bulk-creates
   `CycleExpense` rows from matching `RecurrentExpense` records.
4. **Overdue reclassification** — `CycleExpenseResponse` marks an expense
   overdue at serialization time if `due_date < today` and status is still
   `pending`.
5. **Data isolation** — every query filters by `user_id`; ownership is
   enforced in the service layer, not just the router.
6. **Soft deletes only** — never call `db.delete()`. Set `active = False`.

---

## Before You Write Any Code

1. **Read the relevant domain** — for any feature change, read the full domain
   folder (`router.py`, `schemas.py`, `models.py`, `service.py`,
   `exceptions.py`, `constants.py`) before editing anything.
2. **Check the test fixtures** — read `tests/conftest.py` and the matching
   `tests/<domain>/conftest.py` to understand what test data is already
   available.
3. **Understand the existing error codes** — check `constants.py` in the
   affected domain before adding new `ErrorCode` values so you don't
   duplicate or contradict existing ones.

---

## What You Can Change Freely

- Adding fields to existing Pydantic schemas — as long as new fields are
  `Optional` or have defaults to avoid breaking existing callers.
- Adding new service methods — pure business logic additions are safe.
- Adding new endpoints to an existing router — follow the established pattern.
- Adding new test cases — always welcome; never delete existing tests.
- Editing `constants.py` enums — safe if you add values; renaming or
  removing values requires a migration.

---

## Adding a New Domain

Follow this checklist in order:

1. Create `app/<domain>/` with all 7 files: `router.py`, `schemas.py`,
   `models.py`, `service.py`, `dependencies.py`, `exceptions.py`,
   `constants.py`. Add `__init__.py`.
2. Inherit the ORM model from `app.models.BaseModel`.
3. Define `ErrorCode` enum in `constants.py` first — name values as
   `DOMAIN_CONDITION` (e.g., `FOO_NOT_FOUND`).
4. Write exceptions in `exceptions.py` inheriting `AppExceptionError`.
5. Write service methods — static methods only, no HTTP types.
6. Write Pydantic schemas with `model_config = ConfigDict(from_attributes=True)`
   on response models.
7. Write the router using the existing domain routers as templates.
8. Register the router in `app/main.py`:

   ```python
   from app.<domain>.router import router as <domain>_router
   app.include_router(<domain>_router, prefix="/api/v1/<domain>", tags=["<domain>"])
   ```

9. Create `tests/<domain>/` with `__init__.py`, `conftest.py`,
   and at least one `test_router.py`.
10. Generate and apply the Alembic migration.

---

## Cross-Domain Rules

Domains do not import from each other's `service.py`. The only sanctioned
cross-domain dependency is a local `_verify_payment_method` helper that
`cycles/service.py` and `recurrent_expenses/service.py` each define
independently. If you need shared logic, add a local `_helper` function in
the calling domain's `service.py`.

---

## Validation Checklist Before Finishing

Run all of the following and fix every error before stopping:

```bash
cd backend
PYTHONPATH=. uv run ruff check . --fix
PYTHONPATH=. uv run ruff format .
PYTHONPATH=. uv run pyright .
PYTHONPATH=. uv run pytest
```

Pyright is strict — add type annotations to every function you write or
touch, including return types. Never use `Any` unless there is no alternative
and you add a comment explaining why.

### Pre-commit Hooks

Run pre-commit on every file you changed before finishing. Pre-commit hooks
run automatically on `git commit` and will abort the commit if they modify
any file (requiring re-staging). Catching this beforehand avoids that
disruption. Run from the **repo root** (where `.pre-commit-config.yaml`
lives), not from inside `backend/`:

```bash
# From repo root — list every backend file you changed:
pre-commit run --files backend/app/cycles/service.py backend/AGENTS.md
```

Do **not** use `--all-files`; it processes the entire frontend too and can
run out of memory. Pass only the files you touched.

### API Documentation

Whenever you add, remove, or change an API endpoint (path, method, request
body, response shape, or error codes), update
`docs/architecture/api-specification.md` in the same change. Specifically:

- Add a new subsection under the relevant domain heading for new endpoints.
- Update the request/response JSON examples to match the actual schema.
- Add any new error codes to the Error Codes table.

### Markdown Files

Pre-commit runs `markdownlint` on all `.md` files outside `docs/`. When you
create or edit any `.md` file, follow these rules or the commit will fail:

- **80-character line limit** on prose lines (MD013).
- Code blocks (` ``` `) and table rows are exempt from the line limit.
- No trailing spaces, files must end with a newline.
- Run `pre-commit run markdownlint --files <your .md files>` to check.

---

## Patterns to Follow

### Dependency Injection

```python
from typing import Annotated
from fastapi import Depends
from app.dependencies import CurrentActiveUser
from app.database import get_db
from sqlalchemy.orm import Session

@router.get("/{foo_id}", response_model=FooResponse)
async def get_foo(
    foo_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentActiveUser,
) -> FooResponse:
    foo = FooService.get_foo_by_id(db, foo_id, current_user.id)
    if foo is None:
        raise FooNotFoundExceptionError(foo_id)
    return foo
```

### Soft Delete

```python
@staticmethod
def delete_foo(db: Session, foo: Foo) -> None:
    foo.active = False
    db.commit()
```

### Pydantic Response Model

```python
from pydantic import BaseModel, ConfigDict

class FooResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime
```

### Listing with Ownership Filter

```python
@staticmethod
def get_foos(db: Session, user_id: UUID, active: bool | None = None) -> list[Foo]:
    query = db.query(Foo).filter(Foo.user_id == user_id)
    if active is not None:
        query = query.filter(Foo.active == active)
    return query.all()
```

---

## What NOT to Do

- Do not import `HTTPException` in service files.
- Do not use `db.delete()` anywhere — soft deletes only.
- Do not share service classes across domains.
- Do not add business logic to router functions.
- Do not skip `db.refresh(obj)` after `db.commit()` when the caller needs
  up-to-date computed values.
- Do not add endpoints without auth unless explicitly public
  (only `/auth/register`, `/auth/login`, `/health`).
- Do not use `Any` in type annotations without a comment.
- Do not rename or remove enum values without a Postgres migration.
- Do not hard-code user IDs or secrets — use fixtures and config.
