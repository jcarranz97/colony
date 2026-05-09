---
name: backup-db
description: Back up the Colony PostgreSQL database from a Kubernetes namespace using scripts/backup-db.sh. Asks the user which namespace to back up before running.
---

# Backup Colony Database

Run `scripts/backup-db.sh` against the namespace the user picks. The script
dumps the postgres pod in that namespace to a timestamped, gzipped file under
`~/.colony/db-backup/`.

## How to run

1. Use the AskUserQuestion tool to ask which namespace to back up. Offer:
   - `colony-app` (production) — recommended default, label as
     "(Recommended)"
   - `colony-dev` (dev environment)

   Use header "Namespace". The user may type a custom namespace via "Other".

2. Run the backup script with that namespace:

   ```bash
   COLONY_NAMESPACE=<namespace> ./scripts/backup-db.sh
   ```

3. Report the resulting backup file path (it's printed by the script as
   `Output:`) and the size (printed as `Backup OK (<size>)`). Keep the
   summary short — one or two sentences.

## Notes

- The script is read-only against the cluster — it only runs `pg_dump`. Safe
  to run anytime.
- Backups land in `~/.colony/db-backup/`. The script never deletes old
  files; if the user mentions disk pressure, suggest the housekeeping
  one-liner from `docs/development/database-backups.md`.
- If the script fails (e.g., wrong namespace, no postgres pod), surface the
  error message verbatim so the user can diagnose.
