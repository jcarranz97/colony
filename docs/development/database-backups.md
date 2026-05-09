# Database Backups

Colony's PostgreSQL data lives inside the `colony-postgresql` pod in the
`colony-app` Kubernetes namespace. Pod storage is not automatically
backed up, and a wiped DB cannot be recovered without an external dump,
so the repo ships two small scripts you can run on demand:

- `scripts/backup-db.sh` — writes timestamped `pg_dump` archives to
  `~/.colony/db-backup/`.
- `scripts/restore-db.sh` — loads a backup back into a postgres pod
  (defaults to the dev namespace because restore drops every table).

Two matching Claude Code skills (`/backup-db` and `/restore-db`) wrap
the scripts behind a guided prompt — see
[Using the Claude Code skills](#using-the-claude-code-skills).

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

The dumps are plain `pg_dump` SQL gzipped. Use `scripts/restore-db.sh`
for in-cluster restores, or pipe straight into a local `psql` for
inspection.

### Restore into the cluster pod

The restore script mirrors `backup-db.sh`: it finds the postgres pod by
label (with a name-pattern fallback), reads DB credentials from the
pod's own environment, and pipes the gzipped dump into `psql` with
`ON_ERROR_STOP=1` so a single failed statement aborts the whole
restore.

It **defaults to the `colony-dev` namespace** because the dump is
applied with `--clean --if-exists`, which drops every table before
recreating it. Restoring into the wrong namespace is destructive — the
script prints the target and prompts you to type the namespace name to
confirm.

From the repo root:

```bash
./scripts/restore-db.sh ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz
```

Output:

```text
  ====================================================================
   RESTORE TARGET
  ====================================================================
   Namespace:  colony-dev
   Pod:        colony-dev-postgresql-5856895896-6tj5s
   Database:   colony_db (user: colony_user)
   Backup:     /home/<you>/.colony/db-backup/colony_db-...sql.gz
  ====================================================================

  This will DROP and recreate every table in 'colony_db', wiping all
  current data in namespace 'colony-dev'.

Type the namespace name to confirm: colony-dev
Restore OK into namespace 'colony-dev'.
```

#### Overrides

| Variable           | Default                             | Purpose                            |
| ------------------ | ----------------------------------- | ---------------------------------- |
| `COLONY_NAMESPACE` | `colony-dev`                        | Target namespace.                  |
| `COLONY_PG_LABEL`  | `app.kubernetes.io/name=postgresql` | Label selector for the pod lookup. |

| Flag | Effect                                         |
| ---- | ---------------------------------------------- |
| `-y` | Skip the confirmation prompt (for automation). |

Example — restore into a staging cluster unattended:

```bash
COLONY_NAMESPACE=colony-staging ./scripts/restore-db.sh -y \
  ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz
```

!!! warning "Stop the backend first when restoring into prod"
    Restoring while `colony-backend` is serving traffic can leave the
    app in an inconsistent state and may fight with table drops.
    Scale the deployment to zero, restore, then scale back up:

    ```bash
    kubectl scale -n colony-app deploy/colony-backend --replicas=0
    COLONY_NAMESPACE=colony-app ./scripts/restore-db.sh \
      ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz
    kubectl scale -n colony-app deploy/colony-backend --replicas=1
    ```

### Restore into a local Postgres (e.g., to inspect the dump)

```bash
# Create a throwaway DB and load the dump into it
createdb colony_inspect
gunzip -c ~/.colony/db-backup/colony_db-20260504T091522Z.sql.gz \
  | psql -d colony_inspect
```

## Using the Claude Code Skills

If you're working in [Claude Code](https://claude.com/claude-code), the
repo ships two slash-command skills that wrap the scripts behind a
guided prompt. They live under `.claude/skills/` and are auto-loaded
when Claude Code is invoked from the repo root.

### `/backup-db`

Asks which namespace to back up (defaults to `colony-app`), then runs
`scripts/backup-db.sh` and reports the output path and size.

```text
/backup-db
```

You can pre-fill the namespace as a free-form argument and skip the
prompt:

```text
/backup-db from my colony-app (production) namespace
/backup-db colony-dev
```

### `/restore-db`

Asks which namespace to restore into (defaults to `colony-dev`), then
asks which backup file to use (most recent first), then runs
`scripts/restore-db.sh -y` against your selection.

```text
/restore-db
```

Pre-fill both choices as a free-form argument to skip the prompts —
useful for the common "restore the latest prod backup into dev" case:

```text
/restore-db restore the latest database backup to my dev environment
```

Picking `colony-app` will trigger an extra confirmation step before the
script runs, since it wipes production data.

### Why skills instead of plain scripts?

The skills exist because:

- They make the namespace explicit at the prompt (you pick from a
  short list instead of remembering the env-var name).
- They reuse the scripts unchanged — the underlying tooling stays
  callable from CI or a plain shell with no dependency on Claude Code.
- For restore, they default to dev and reroute the destructive
  confirmation to the AskUserQuestion UI, so a misclick on a
  dropdown is much less likely than a misread of a typed namespace.

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
