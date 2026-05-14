# Database Migrations

Colony uses [Alembic](https://alembic.sqlalchemy.org/) for SQL schema
migrations. Every model change ships as a migration under
`backend/alembic/versions/` and is applied at deploy time by the Helm
chart's `run-migrations` init container.

The backend lifespan also calls `Base.metadata.create_all()` as a
dev-mode safety net so a fresh `docker compose up` works without a
manual step. In production this becomes a no-op because the init
container has already created every table via Alembic.

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

## How the init container handles deploys

The Helm chart's `run-migrations` init container invokes
`backend/scripts/run_migrations.py` before the backend starts. That
script:

1. Inspects the database for an `alembic_version` table.
2. If absent **and** legacy tables (e.g. `households`) already exist —
   i.e. the database was created by the pre-Alembic
   `Base.metadata.create_all()` path — it auto-stamps `0001_baseline`
   so the existing schema is treated as the baseline.
3. Runs `alembic upgrade head`, applying any pending migrations.

Result: **the same `helm upgrade` command works whether the cluster has
data or not.** No manual `alembic stamp` step is needed.

## Deploying for the first time with Alembic

Use your normal Helm command — `helm upgrade --install` covers both the
fresh-install and the upgrade case. Build **both** images: Alembic and
the new migrations ship in the backend image; the activity feed and
comments UI ship in the frontend image.

```bash
# 1. Build and push both images.
docker build -t <registry>/colony-backend:latest backend/
docker build -t <registry>/colony-frontend:latest frontend/
docker push <registry>/colony-backend:latest
docker push <registry>/colony-frontend:latest

# 2. (Recommended on first run) back up the database before the
#    auto-stamp + migration runs.
scripts/backup-db.sh colony-dev

# 3. Roll the chart out. The init container handles the migration.
helm upgrade --install colony ./helm/colony \
  --namespace colony-dev \
  --create-namespace \
  -f ~/homelab/colony-dev/my-values.yaml
```

For a cluster that previously ran a pre-Alembic build, the first
`run-migrations` init container will log:

```text
Detected pre-Alembic schema; stamping 0001_baseline so the activity-log
migration applies on top of the existing tables.
```

…and then apply `0002_activity_and_comments`. Subsequent deploys log:

```text
Alembic state present — applying any pending migrations.
```

## Verifying the migration state

```bash
kubectl exec -n colony-dev deploy/colony-backend -- \
  uv run alembic current
# Expected after the first upgrade:
# 0002_activity_and_comments (head)

kubectl logs -n colony-dev deploy/colony-backend -c run-migrations
# Should end with: "Migrations complete."
```

If the backend pod is stuck in `Init:CrashLoopBackOff`, the init
container is failing. Check its logs first:

```bash
kubectl logs -n colony-dev deploy/colony-backend -c run-migrations --previous
```

The deployment name follows the `colony.fullname` template. If your
release name isn't `colony`, find the actual name with:

```bash
kubectl get deploy -n colony-dev -l app.kubernetes.io/component=backend
```

## Rolling back

```bash
# Roll back the most recent migration:
kubectl exec -n colony-dev deploy/colony-backend -- \
  uv run alembic downgrade -1

# Roll back to a specific revision:
kubectl exec -n colony-dev deploy/colony-backend -- \
  uv run alembic downgrade 0001_baseline
```

Downgrades drop the corresponding tables. Back up first via
`scripts/backup-db.sh` — for a `colony-dev` namespace:

```bash
scripts/backup-db.sh colony-dev
```

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
DATABASE_URL=postgresql://... uv run python scripts/run_migrations.py
```
