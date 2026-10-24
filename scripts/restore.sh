#!/usr/bin/env bash
# Replaces DCP's database with a backup made by ./scripts/backup.sh.
# This DELETES everything currently in the database, so it asks for --yes:
#   ./scripts/restore.sh backups/dcp-20261023-120000.dump --yes
# Use the same DCP_SECRET_KEY as when the backup was made.
set -euo pipefail
cd "$(dirname "$0")/.."
file="${1:-}"
if [ -z "$file" ] || [ ! -f "$file" ]; then
  echo "Usage: ./scripts/restore.sh <backup.dump> --yes"
  exit 2
fi
if [ "${2:-}" != "--yes" ]; then
  echo "This replaces EVERYTHING in DCP's database with $file."
  echo "If you're sure, run it again with --yes at the end."
  exit 2
fi
echo "Stopping the API and worker..."
docker compose stop api worker
echo "Restoring $file..."
docker compose exec -T db sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --exit-on-error' < "$file"
echo "Starting the API (it applies any newer database changes) and worker..."
docker compose start api worker
echo "Restored. Check http://localhost:${DCP_PORT:-8000}/readyz"
