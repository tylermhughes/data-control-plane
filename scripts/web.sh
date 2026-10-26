#!/usr/bin/env bash
# Runs npm for the web interface inside Docker, so no Node.js is needed on this machine.
#   ./scripts/web.sh ci            # install exactly what package-lock.json says
#   ./scripts/web.sh run build     # build web/dist
#   ./scripts/web.sh run dev       # dev server on http://localhost:5173 (API on :8000)
set -euo pipefail
cd "$(dirname "$0")/.."
NODE_IMAGE="node:24.21.0-alpine"  # LTS; its npm 11 handles vitest's optional peers
tty_flag=""; [ -t 0 ] && tty_flag="-it"
port_flag=""; [ "${1:-} ${2:-}" = "run dev" ] && port_flag="-p 127.0.0.1:5173:5173"
exec docker run --rm $tty_flag $port_flag \
  -v "$PWD":/repo -w /repo/web \
  -e DCP_API_PROXY="${DCP_API_PROXY:-http://host.docker.internal:8000}" \
  --add-host host.docker.internal:host-gateway \
  "$NODE_IMAGE" npm --no-update-notifier --no-fund --no-audit "$@"
