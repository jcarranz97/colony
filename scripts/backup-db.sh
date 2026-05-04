#!/usr/bin/env bash
# Back up the Colony PostgreSQL database from a Kubernetes pod.
#
# Writes a timestamped, gzipped pg_dump to ~/.colony/db-backup/.
# Reads DB credentials from the pod's own environment so it works for
# both the Bitnami chart and the vanilla postgres image.
#
# Usage:   ./scripts/backup-db.sh
# Env:     COLONY_NAMESPACE  (default: colony-app)
#          COLONY_PG_LABEL   (default: app.kubernetes.io/name=postgresql)

set -euo pipefail

NAMESPACE="${COLONY_NAMESPACE:-colony-app}"
PG_LABEL="${COLONY_PG_LABEL:-app.kubernetes.io/name=postgresql}"
BACKUP_DIR="${HOME}/.colony/db-backup"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$BACKUP_DIR"

command -v kubectl >/dev/null || {
  echo "kubectl not found in PATH" >&2
  exit 1
}

POD="$(kubectl get pods -n "$NAMESPACE" -l "$PG_LABEL" \
  -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"

if [[ -z "$POD" ]]; then
  POD="$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null \
    | awk '/postgres/ {print $1; exit}')"
fi

if [[ -z "$POD" ]]; then
  echo "No postgres pod found in namespace '$NAMESPACE'" >&2
  exit 1
fi

read_env() {
  local var
  for var in "$@"; do
    local val
    val="$(kubectl exec -n "$NAMESPACE" "$POD" -- printenv "$var" 2>/dev/null \
      | tr -d '\r' || true)"
    if [[ -n "$val" ]]; then
      printf '%s' "$val"
      return 0
    fi
  done
}

DB_USER="$(read_env POSTGRES_USER POSTGRESQL_USERNAME)"
DB_NAME="$(read_env POSTGRES_DB POSTGRESQL_DATABASE)"
DB_PASS="$(read_env POSTGRES_PASSWORD POSTGRESQL_PASSWORD)"

: "${DB_USER:?Could not resolve DB user from pod env (POSTGRES_USER / POSTGRESQL_USERNAME)}"
: "${DB_NAME:?Could not resolve DB name from pod env (POSTGRES_DB / POSTGRESQL_DATABASE)}"

OUTPUT="$BACKUP_DIR/${DB_NAME}-${TIMESTAMP}.sql.gz"

echo "Pod:        $POD"
echo "Database:   $DB_NAME (user: $DB_USER)"
echo "Output:     $OUTPUT"
echo

kubectl exec -n "$NAMESPACE" "$POD" -- env "PGPASSWORD=$DB_PASS" \
  pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner \
  | gzip > "$OUTPUT"

if [[ ! -s "$OUTPUT" ]]; then
  echo "Backup is empty — pg_dump likely failed." >&2
  rm -f "$OUTPUT"
  exit 1
fi

SIZE="$(du -h "$OUTPUT" | awk '{print $1}')"
echo "Backup OK ($SIZE)."
