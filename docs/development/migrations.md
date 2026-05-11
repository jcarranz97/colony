# Database Migrations

Colony uses [Alembic](https://alembic.sqlalchemy.org/) for SQL schema
migrations. Every model change ships as a migration under
`backend/alembic/versions/` and is applied at deploy time by the Helm
chart's `run-migrations` init container.

The backend lifespan also calls `Base.metadata.create_all()` as a
dev-mode safety net so a fresh `docker compose up` works without a
manual step. In production this becomes a no-op because the init
container has already created every table via Alembic. For dev parity
with Alembic state, run `alembic stamp head` once after the first
`docker compose up`.

## Authoring a new migration

From `backend/`:

```bash
# After changing a SQLAlchemy model in app/<domain>/models.py:
uv run alembic revision --autogenerate -m "short description"

# Review the generated file in alembic/versions/ — autogenerate is a
# starting point, not a final answer. Fix any drift before committing.
uv run alembic upgrade head      # apply locally
uv run alembic downgrade -1      # roll back the latest revision
uv run alembic history           # list all revisions
uv run alembic current           # show the applied revision
```

## Deploying to a fresh environment

Brand-new databases run every migration from zero. The backend
deployment template (`helm/colony/templates/backend-deployment.yaml`)
declares a `run-migrations` init container that executes
`alembic upgrade head` before the API process starts. No manual step is
required:

```bash
helm upgrade --install colony ./helm/colony -f values.yaml
```

## Deploying to an environment that ALREADY has data

The first release that introduces Alembic ships two migrations:

| Revision                     | Purpose                                     |
| ---------------------------- | ------------------------------------------- |
| `0001_baseline`              | Captures the pre-Alembic schema             |
| `0002_activity_and_comments` | Adds the activity_log + comments tables     |

A database created by the old `Base.metadata.create_all()` path already
contains every table that `0001_baseline` would create. Running
migration `0001` against it would fail with "table already exists." Run
this **one-time** command instead, to mark `0001` as already applied:

```bash
kubectl exec -n <namespace> deploy/<release>-colony-backend -- \
  uv run alembic stamp 0001_baseline
```

Then either redeploy (the init container picks up from `0002`) or run:

```bash
kubectl exec -n <namespace> deploy/<release>-colony-backend -- \
  uv run alembic upgrade head
```

After the stamp is recorded, every future deploy is just `helm upgrade`
— the init container handles upgrades automatically.

### Verifying the migration state

```bash
kubectl exec -n <namespace> deploy/<release>-colony-backend -- \
  uv run alembic current
# Expected after the first upgrade:
# 0002_activity_and_comments (head)
```

## Rolling back

```bash
# Roll back the most recent migration:
kubectl exec -n <namespace> deploy/<release>-colony-backend -- \
  uv run alembic downgrade -1

# Roll back to a specific revision:
kubectl exec -n <namespace> deploy/<release>-colony-backend -- \
  uv run alembic downgrade 0001_baseline
```

Downgrades drop the corresponding tables. Use with care; back up first
via `scripts/backup-db.sh`.

## Test database

Tests use `Base.metadata.create_all()` against an ephemeral test DB
configured in `tests/conftest.py`. They do **not** run migrations,
because:

- Faster setup (no per-test alembic invocation).
- The test schema is recreated and dropped per test, so migration state
  is meaningless.

If you need a migration-applied test environment (e.g. to test a
migration script), run it manually against a scratch database:

```bash
DATABASE_URL=postgresql://... uv run alembic upgrade head
```
