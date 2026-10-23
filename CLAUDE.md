# Data Control Plane (DCP)

## What this is
A self-hosted, vendor-neutral control plane for AI training data. It decides what data
to get and from where, checks it, gates what reaches training, and shows which data
spend actually improved models. **`docs/PRODUCT.md` is the source of product intent.
Read it before planning any feature.** `docs/prototype/data-control-plane.html` shows
the intended experience (sample data only). `docs/PLAN.md` holds the milestone plan.

The founder (Tyler) is not an engineer and tests every milestone personally.

## The core loop (keep it working end to end)
Capability → Request → Spec (versioned) → Allocations across sources → Batches →
Dataset version → Eval result → Portfolio report → Recommendations.

## Product principles
- API-first and headless: everything works through the REST API. The UI comes later
  and uses only the public API. Every resource has a stable ID and full CRUD, and
  POSTs accept `Idempotency-Key` (Terraform-friendly).
- Self-hosted: `docker compose up`. Postgres is the only stateful dependency.
- Metadata-first: store pointers, checksums, attributes, results and costs, not data.
- Every number has a source: reports return the IDs behind each figure and mark
  estimates as estimates.

## Stack
Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16,
Postgres-backed job queue, boto3, pyarrow/polars, uv, pytest, ruff, mypy,
Schemathesis, oasdiff, Docker Compose.

## Layout
- `app/api/v1/`: thin routers. `app/schemas/`: Pydantic API models (the contract).
- `app/models/`: tables. `app/services/`: all business rules.
- `app/worker/`: jobs, checks, webhook sender. `app/connectors/`: one module per connector.
- `migrations/`, `openapi.yaml` (committed), `tests/` (mirrors `app/`, plus `tests/e2e/`).

## Commands
- Start: `docker compose up --build`
- All checks (lint, types, tests, spec): `./scripts/check.sh`
- Regenerate spec: `uv run python -m app.export_openapi > openapi.yaml`
- New migration: `uv run alembic revision --autogenerate -m "<what changed>"`

## Rules for Claude
1. **Explain in plain English** before and after each change: what, why, and how
   Tyler can test it. Prefer steps using "Try it out" at `localhost:8000/docs`, with
   copy-pasteable curl commands as a backup.
2. **One milestone at a time**, per `docs/PLAN.md`. Keep `docs/PLAN.md` updated
   (status, decisions, changes) as part of each milestone.
3. **OpenAPI is the contract.** Update `openapi.yaml` in the same commit as any API
   change. Ask before any breaking change. Add fields; don't rename or remove them.
4. **Tests with every change** (services, every endpoint including auth and validation
   failures, one e2e per milestone). Only call work done when `./scripts/check.sh`
   passes. If it fails, say so and show the output.
5. **Every state change emits an Event** in the same transaction. Never send webhooks
   directly from request handlers.
6. **Money** is Decimal + currency, never floats.
7. **Never commit secrets.** `.env` is gitignored, and `.env.example` documents every
   setting. Hash API keys and encrypt stored credentials. Never log secrets or file
   contents. Verify inbound signatures with constant-time comparison.
8. **Ask before deleting files or running destructive commands** (dropping data,
   `git reset --hard`, force-push, `docker compose down -v`, etc.).
9. **Migrations only.** Never change the database by hand. Migrations must work on
   installs that already contain data.
10. **Keep `docker compose up` working** on a clean machine.
11. **Ask, don't assume**, on product decisions, and check `docs/PRODUCT.md` first.
    Make routine engineering choices yourself and mention them. Explain any new
    dependency in plain English.
12. **Dependencies: ask first.** Never add, remove, swap or upgrade a dependency (Python
    package, Docker image, tool) without asking Tyler first and saying in plain English
    what it is, why it's needed, and what the alternative is. Use only well-established,
    widely used, actively maintained packages, never a newer fork or look-alike. Prefer
    fixing or narrowly filtering a warning over changing packages.
13. **Git:** use a branch per milestone with clear commits. Push or open PRs only when asked.
