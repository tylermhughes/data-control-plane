# Data Control Plane

A self-hosted control plane for AI training data. See [`docs/PRODUCT.md`](docs/PRODUCT.md)
for what it does and [`docs/PLAN.md`](docs/PLAN.md) for the build plan.

## Run it

You need Docker. Then:

```
cp .env.example .env        # then open .env and set POSTGRES_PASSWORD and DCP_SECRET_KEY
docker compose up --build
```

Generate a `DCP_SECRET_KEY` with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
Keep it stable and back it up: webhook signing secrets are derived from it.

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

## Run the north-star demo

With DCP running, this runs the whole loop from `docs/PRODUCT.md` through the API and prints the
portfolio (built-in Python 3.9+, nothing to install):

```
DCP_API_KEY=dcp_... python3 scripts/demo.py
```

## Quality checks on delivered files

When a batch lists files, the worker checks them automatically: format, schema, duplicates, stats,
attribute counts and the spec's acceptance rules. Local files go in `./data` and are referenced as
`file:///data/...`. For S3, set the AWS settings in `.env` (see `.env.example`).

## Automatic intake: inbound webhooks and bucket watching

- **Inbound webhooks** (`/v1/inbound-webhooks`): give a vendor a URL and secret, and they push signed
  delivery messages. Try it with `scripts/send_inbound.py`.
- **Bucket watching** (`/v1/connectors`): DCP checks a bucket folder about once a minute and turns each
  new file into a batch. To try it locally, start the dev profile, which adds a small S3 server
  serving `./data/s3` (each folder in it is a bucket):

  ```
  docker compose --profile dev up --build
  ```

  Use endpoint `http://s3:7070` with the access key and secret from `.env.example`.

## Try webhooks locally

`scripts/webhook_receiver.py` prints every webhook it receives and checks its signature:

```
python3 scripts/webhook_receiver.py --secret whsec_...      # add --fail to test retries
```

Register `http://host.docker.internal:9000/` as the endpoint URL. That's how DCP, running in Docker,
reaches your machine. If macOS asks whether Python may accept incoming connections, click **Allow**.

## Use it from scripts

- **Python client** (generated from `openapi.yaml`): `clients/python`
- **Command line**:
  ```
  cd clients/cli && uv sync
  export DCP_URL=http://localhost:8000 DCP_API_KEY=dcp_...
  uv run dcp list
  uv run dcp batches list-batches --status failed
  ```
- **Examples for CI**: `examples/record_training_run.py` (record a training run) and
  `examples/quality_gate.py` (refuse to train on a dataset version that isn't clean).

## Running it in production

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for backups, restores, upgrades and monitoring,
and [`CHANGELOG.md`](CHANGELOG.md) for what changed between versions.

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
