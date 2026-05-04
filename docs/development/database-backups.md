# Database Backups

Colony's PostgreSQL data lives inside the `colony-postgresql` pod in the
`colony-app` Kubernetes namespace. Pod storage is not automatically
backed up, and a wiped DB cannot be recovered without an external dump,
so the repo ships a small backup script you can run on demand.

The script lives at `scripts/backup-db.sh` and writes timestamped
`pg_dump` archives to `~/.colony/db-backup/`.

## What the Script Does

1. Looks up the postgres pod in the target namespace by the
   `app.kubernetes.io/name=postgresql` label, with a name-pattern
   fallback so the pod's hash suffix never matters.
2. Reads the database name, user, and password from the pod's own
   environment (works for both the Bitnami chart and the vanilla
   `postgres` image).
3. Runs `pg_dump --clean --if-exists --no-owner` inside the pod and
   pipes the output through `gzip` on your local machine.
4. Writes the result to
   `~/.colony/db-backup/<dbname>-<UTC-timestamp>.sql.gz`.

`set -euo pipefail` is on, so a failed `pg_dump` aborts the script and
the partial file is removed.

## Prerequisites

- `kubectl` on `PATH` and pointed at the cluster that hosts Colony
  (verify with `kubectl get pods -n colony-app`).
- Read access to the `colony-app` namespace (the script never writes
  to the cluster).

## Usage

From the repo root:

```bash
./scripts/backup-db.sh
```

Output:

```text
Pod:        colony-postgresql-5dff48f8f4-7dv8z
Database:   colony_db (user: colony_user)
Output:     /home/<you>/.colony/db-backup/colony_db-20260504T091522Z.sql.gz

Backup OK (1.4M).
```

### Overrides

| Variable           | Default                                | Purpose                            |
| ------------------ | -------------------------------------- | ---------------------------------- |
| `COLONY_NAMESPACE` | `colony-app`                           | Target namespace.                  |
| `COLONY_PG_LABEL`  | `app.kubernetes.io/name=postgresql`    | Label selector for the pod lookup. |

Example — back up a staging cluster in a different namespace:

```bash
COLONY_NAMESPACE=colony-staging ./scripts/backup-db.sh
```

### Recommended Cadence

Run the script:

- Before any schema-changing migration.
- Before running destructive scripts or one-off `psql` sessions.
- On a regular cadence you're comfortable with (cron / systemd timer
  / manual). Backups are small — keeping daily archives for a few
  weeks is cheap.

## Restoring from a Backup

The dumps are plain `pg_dump` SQL gzipped, so you can restore them
through any `psql` connection. The two common cases:

### Restore into the cluster pod

```bash
# Variables you'll set
NAMESPACE=colony-app
POD=$(kubectl get pods -n "$NAMESPACE" \
  -l app.kubernetes.io/name=postgresql \
  -o jsonpath='{.items[0].metadata.name}')
DB_USER=colony_user
DB_NAME=colony_db
DB_PASS=$(kubectl exec -n "$NAMESPACE" "$POD" -- printenv POSTGRES_PASSWORD)
BACKUP=~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz

# Stream the gzipped dump straight into psql inside the pod
gunzip -c "$BACKUP" \
  | kubectl exec -i -n "$NAMESPACE" "$POD" -- \
      env PGPASSWORD="$DB_PASS" psql -U "$DB_USER" -d "$DB_NAME"
```

The dump was created with `--clean --if-exists`, so it will
`DROP TABLE IF EXISTS …` before recreating each table. Existing data
in the target DB will be replaced.

!!! warning "Stop the backend first"
    Restoring while `colony-backend` is serving traffic can leave the
    app in an inconsistent state and may fight with table drops.
    Scale the deployment to zero, restore, then scale back up:

    ```bash
    kubectl scale -n colony-app deploy/colony-backend --replicas=0
    # ...run the restore command above...
    kubectl scale -n colony-app deploy/colony-backend --replicas=1
    ```

### Restore into a local Postgres (e.g., to inspect the dump)

```bash
# Create a throwaway DB and load the dump into it
createdb colony_inspect
gunzip -c ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz \
  | psql -d colony_inspect
```

## Verifying a Backup

Quick sanity checks that don't require a restore:

```bash
# Make sure the file is non-empty and is a valid gzip stream
gzip -t ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz \
  && echo "gzip OK"

# Peek at the SQL header to confirm pg_dump produced it
gunzip -c ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz \
  | head -20
```

A healthy file starts with a `-- PostgreSQL database dump` comment
block and lists `SET` statements before any `CREATE TABLE` lines.

## Housekeeping

The script never deletes old backups. Periodically prune the folder
to reclaim disk:

```bash
# Keep the 30 most recent archives, delete the rest
ls -1t ~/.colony/db-backup/*.sql.gz | tail -n +31 | xargs -r rm --
```
