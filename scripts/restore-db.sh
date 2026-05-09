#!/usr/bin/env bash
# Restore a Colony PostgreSQL backup into a Kubernetes pod.
#
# Reads DB credentials from the pod's own environment so it works for both
# the Bitnami chart and the vanilla postgres image. Defaults to the dev
# namespace because restoring is destructive (--clean --if-exists in the
# dump drops every table).
#
# Usage:   ./scripts/restore-db.sh <backup.sql.gz>
# Env:     COLONY_NAMESPACE  (default: colony-dev)
#          COLONY_PG_LABEL   (default: app.kubernetes.io/name=postgresql)
# Flags:   -y                Skip confirmation prompt.

set -euo pipefail

NAMESPACE="${COLONY_NAMESPACE:-colony-dev}"
PG_LABEL="${COLONY_PG_LABEL:-app.kubernetes.io/name=postgresql}"

SKIP_CONFIRM=false
if [[ "${1:-}" == "-y" ]]; then
  SKIP_CONFIRM=true
  shift
fi

BACKUP="${1:-}"
if [[ -z "$BACKUP" ]]; then
  echo "Usage: $0 [-y] <backup.sql.gz>" >&2
  exit 1
fi

if [[ ! -f "$BACKUP" ]]; then
  echo "Backup file not found: $BACKUP" >&2
  exit 1
fi

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

cat <<EOF

  ====================================================================
   RESTORE TARGET
  ====================================================================
   Namespace:  $NAMESPACE
   Pod:        $POD
   Database:   $DB_NAME (user: $DB_USER)
   Backup:     $BACKUP
  ====================================================================

  This will DROP and recreate every table in '$DB_NAME', wiping all
  current data in namespace '$NAMESPACE'.

EOF

if [[ "$SKIP_CONFIRM" != true ]]; then
  read -r -p "Type the namespace name to confirm: " CONFIRM
  if [[ "$CONFIRM" != "$NAMESPACE" ]]; then
    echo "Aborted." >&2
    exit 1
  fi
fi

gunzip -c "$BACKUP" \
  | kubectl exec -i -n "$NAMESPACE" "$POD" -- \
      env "PGPASSWORD=$DB_PASS" \
      psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
      >/dev/null

echo "Restore OK into namespace '$NAMESPACE'."
