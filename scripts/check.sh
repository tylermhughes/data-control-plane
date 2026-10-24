#!/usr/bin/env bash
# Runs every check. If this passes, the work is done:
#   1. style (ruff)   2. types (mypy)   3. OpenAPI spec is up to date
#   4. no breaking API changes vs main (oasdiff)   5. Python client is up to date, CLI loads
#   6. tests (pytest, including API fuzz tests with Schemathesis)
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

step "No breaking API changes (oasdiff, compared with ${DCP_API_BASE_REF:-main})"
base_ref="${DCP_API_BASE_REF:-main}"
if git rev-parse --verify --quiet "$base_ref" >/dev/null \
  && git cat-file -e "$base_ref:openapi.yaml" 2>/dev/null; then
  tmp="$(mktemp -d)"
  git show "$base_ref:openapi.yaml" > "$tmp/base.yaml"
  cp openapi.yaml "$tmp/new.yaml"
  if ! docker run --rm -v "$tmp":/specs tufin/oasdiff:v1.33.0 \
      breaking /specs/base.yaml /specs/new.yaml --fail-on ERR; then
    echo "Breaking API change(s) above. CLAUDE.md rule 3: ask before making one."
    rm -rf "$tmp"
    exit 1
  fi
  rm -rf "$tmp"
else
  echo "Skipped: $base_ref has no openapi.yaml to compare with."
fi

step "Python client matches openapi.yaml, and the CLI loads"
tmp="$(mktemp -d)"
./scripts/generate_client.sh "$tmp/python"
if ! diff -r -q -x __pycache__ -x .ruff_cache clients/python "$tmp/python"; then
  echo "clients/python is out of date. Regenerate it with: ./scripts/generate_client.sh"
  rm -rf "$tmp"
  exit 1
fi
rm -rf "$tmp"
(cd clients/cli && uv run --quiet dcp list >/dev/null)

step "Tests (pytest, using a throwaway database)"
# Compose needs POSTGRES_PASSWORD to read the file, even though db-test doesn't use it.
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-not-used-by-tests}" \
  docker compose --profile test up -d --wait db-test s3-test
TEST_DATABASE_URL="postgresql+psycopg://dcp:dcp-test@127.0.0.1:55432/dcp_test" \
TEST_S3_ENDPOINT_URL="http://127.0.0.1:57070" \
  uv run pytest "$@"

printf '\n\033[1;32mAll checks passed.\033[0m\n'
