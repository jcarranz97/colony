---
name: restore-db
description: Restore a Colony PostgreSQL backup into a Kubernetes namespace using scripts/restore-db.sh. Asks the user which namespace and which backup file before running. Defaults to colony-dev because restore is destructive.
---

# Restore Colony Database

Run `scripts/restore-db.sh` against the namespace the user picks, with the
backup file they choose. The script drops and recreates every table in the
target database — **destructive operation, defaults to dev**.

## How to run

1. Use the AskUserQuestion tool to ask which namespace to restore into.
   Offer:
   - `colony-dev` (dev environment) — recommended default, label as
     "(Recommended)"
   - `colony-app` (production) — describe as "Destructive — will wipe
     production data" so the user understands the risk

   Use header "Namespace". The user may type a custom namespace via "Other".

2. List the available backup files so the user can pick one:

   ```bash
   ls -lt ~/.colony/db-backup/*.sql.gz 2>/dev/null | head -10
   ```

   Then use AskUserQuestion to let them pick. Always include the most
   recent file as the first option (label as "(Recommended)"). Header:
   "Backup file".

3. Run the restore script with the chosen namespace and file. Use `-y` to
   skip the script's interactive confirmation since the user already
   confirmed the namespace via AskUserQuestion:

   ```bash
   COLONY_NAMESPACE=<namespace> ./scripts/restore-db.sh -y <backup-path>
   ```

4. Report the result. On success the script prints
   `Restore OK into namespace '<ns>'.`. Keep the summary short.

## Notes

- The dumps were created with `pg_dump --clean --if-exists`, so they DROP
  every table before recreating. All current data in the target DB is
  replaced.
- If the user picks `colony-app`, double-confirm before running — that
  wipes production. Quote the chosen namespace in your confirmation message
  so they can spot a misclick.
- If the backend pod is serving traffic, restoring may briefly cause errors.
  This is usually fine for dev. For prod, mention scaling the backend to 0
  first (see `docs/development/database-backups.md`).
- If the script fails partway through, the database is in an inconsistent
  state. Surface the error verbatim and suggest re-running the restore once
  the cause is fixed.
