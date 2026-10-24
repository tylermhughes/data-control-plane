#!/usr/bin/env bash
# Saves a copy of DCP's database. Run from anywhere while DCP is running:
#   ./scripts/backup.sh                       # -> backups/dcp-YYYYmmdd-HHMMSS.dump
#   ./scripts/backup.sh /path/to/file.dump
# Also keep DCP_SECRET_KEY (from .env) somewhere safe: without it, stored connector
# credentials and webhook secrets can't be used after a restore.
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-backups/dcp-$(date +%Y%m%d-%H%M%S).dump}"
mkdir -p "$(dirname "$out")"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$out"
echo "Saved the database to $out ($(du -h "$out" | awk '{print $1}'))."
echo "Reminder: keep a safe copy of DCP_SECRET_KEY from .env as well."
