# Data Control Plane

A self-hosted control plane for AI training data. See [`docs/PRODUCT.md`](docs/PRODUCT.md)
for what it does and [`docs/PLAN.md`](docs/PLAN.md) for the build plan.

## Run it

You need Docker. Then:

```
cp .env.example .env        # then open .env and set POSTGRES_PASSWORD
docker compose up --build
```

The first time, create an admin API key (it is shown only once, so copy it):

```
docker compose exec api python -m app.cli create-admin-key
```

Open **http://localhost:8000/docs** to see and try the API. Click **Authorize** and paste the key.
`http://localhost:8000/healthz` says whether the server is running, and `/readyz` says whether it can reach the database.

To stop it, press `Ctrl+C`, or run `docker compose down`. Your data is kept for next time.

## Set up a Mac for development

1. **Docker Desktop:** download "Mac – Apple Silicon" (or "Intel") from
   https://www.docker.com/products/docker-desktop/, drag it to Applications, open it,
   choose "Use recommended settings", and wait for "Engine running". Open a new
   Terminal window and check: `docker run --rm hello-world`.
2. **uv** (installs Python and the project's libraries):
   `curl -LsSf https://astral.sh/uv/install.sh | sh`, then open a new Terminal window and run
   `uv python install 3.12`.
3. **Project libraries:** in this folder, run `uv sync`.

## Check everything

```
./scripts/check.sh
```

This runs the style checks, type checks, OpenAPI spec check, and tests. Tests use a separate
throwaway database, so they never touch real data. Docker must be running.

## Layout

| Path | What's there |
|---|---|
| `app/main.py` | The API server |
| `app/api/` | API routes (`v1/` is the public versioned API) |
| `app/schemas/` | The shapes of API requests and responses |
| `app/models/` | Database tables |
| `app/services/` | Business rules |
| `app/worker/` | Background worker (checks, connectors, webhooks) |
| `migrations/` | Database changes, applied automatically on start |
| `openapi.yaml` | The API contract, generated from the code |
| `tests/` | Automated tests |
