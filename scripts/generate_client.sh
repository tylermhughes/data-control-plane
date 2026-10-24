#!/usr/bin/env bash
# Regenerates the Python client (clients/python) from openapi.yaml.
# Usage: ./scripts/generate_client.sh [output-dir]   (default: clients/python)
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-clients/python}"
uv run openapi-python-client generate \
  --path openapi.yaml \
  --config clients/python-client.config.yaml \
  --output-path "$out" \
  --overwrite \
  --meta uv >/dev/null
rm -rf "$out/.ruff_cache"  # left behind by the formatting hooks
