#!/usr/bin/env bash
# Runs every check. If this passes, the work is done:
#   1. style (ruff)   2. types (mypy)   3. OpenAPI spec is up to date   4. tests (pytest)
set -euo pipefail
cd "$(dirname "$0")/.."
# Test-only master key, so checks never depend on your personal .env.
export DCP_SECRET_KEY="${DCP_SECRET_KEY:-test-only-secret-key-not-for-real-use-0123456789}"

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

step "Style (ruff)"
uv run ruff check .
uv run ruff format --check .

step "Types (mypy)"
uv run mypy

step "OpenAPI spec matches the code"
if ! uv run python -m app.export_openapi | diff -u openapi.yaml - ; then
  echo "openapi.yaml is out of date. Regenerate it with:"
  echo "  uv run python -m app.export_openapi > openapi.yaml"
  exit 1
fi

step "Tests (pytest, using a throwaway database)"
# Compose needs POSTGRES_PASSWORD to read the file, even though db-test doesn't use it.
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-not-used-by-tests}" \
  docker compose --profile test up -d --wait db-test s3-test
TEST_DATABASE_URL="postgresql+psycopg://dcp:dcp-test@127.0.0.1:55432/dcp_test" \
TEST_S3_ENDPOINT_URL="http://127.0.0.1:57070" \
  uv run pytest "$@"

printf '\n\033[1;32mAll checks passed.\033[0m\n'
