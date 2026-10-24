# Running Data Control Plane

For the people who install and look after DCP on their own server.

## What runs

| Container | What it does | Keeps data? |
|---|---|---|
| `db` | PostgreSQL 16: everything DCP knows | **Yes**: the `db-data` volume |
| `api` | The REST API on port 8000 (`DCP_PORT`); applies database changes on start | No |
| `worker` | Background work: quality checks, bucket watching, webhook delivery, housekeeping | No |

Only `db` holds data. You can run more than one `worker` (for example
`docker compose up --scale worker=2`); they share the work safely.

## Install

```
cp .env.example .env
```
Then edit `.env`:
- set `POSTGRES_PASSWORD` to a long random value
- set `DCP_SECRET_KEY`, generated with
  `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`

Then:
```
docker compose up -d --build
docker compose exec api python -m app.cli create-admin-key
```
Copy the key it prints (it's shown once), and open `http://<server>:8000/docs`.

## What to back up

1. **The database**, regularly:
   ```
   ./scripts/backup.sh                    # -> backups/dcp-YYYYmmdd-HHMMSS.dump
   ```
   Copy the file somewhere off the server, e.g. a backup bucket.
2. **`DCP_SECRET_KEY`** (from `.env`), once, somewhere safe like a password manager.
   Webhook signing secrets are derived from it, and connector credentials are encrypted
   with it. With the database but without this key, connectors and webhooks must be set up
   again.
3. **`./data`**, but only if you deliver files to DCP's local folder rather than to buckets.

## Restore

```
./scripts/restore.sh backups/dcp-20261023-120000.dump --yes
```
This **replaces everything** in the database with the backup. Without `--yes` it only
explains what it would do. Keep the same `DCP_SECRET_KEY` as when the backup was made.

## Upgrade

1. Back up first: `./scripts/backup.sh`.
2. Get the new version (e.g. `git pull`, or unpack the new release).
3. Read `CHANGELOG.md` for anything marked **Upgrade note**.
4. `docker compose up -d --build`. The API applies database changes on start; watch them
   with `docker compose logs api | grep "Running upgrade"`.
5. Check `http://<server>:8000/readyz` says `"database": "ok"`.

Database changes only go forward. To go back to an older version, restore the backup you
made in step 1, then start the older version.

## Keeping an eye on it

| What | Where |
|---|---|
| Is the API up? Can it reach the database? | `GET /healthz` and `GET /readyz` (503 if not) |
| Failed webhook deliveries | `GET /v1/webhook-deliveries?status=failed`, and `last_failure_reason` on each endpoint |
| Bucket watchers with problems | `last_error` on `GET /v1/connectors` |
| Rejected inbound messages | `GET /v1/inbound-webhooks/{id}/messages` |
| Worker errors | `docker compose logs worker` |

## Security notes

- API keys are stored hashed and shown once. Revoke unused ones (`DELETE /v1/api-keys/{id}`);
  DCP won't let you revoke the last admin key that can write.
- Rotate webhook secrets with `POST …/rotate-secret`; the old one keeps working for 24 hours.
- The database port isn't exposed outside Docker. Put DCP behind HTTPS (a reverse proxy or
  load balancer) before exposing it beyond a private network.
- Never commit `.env`.
