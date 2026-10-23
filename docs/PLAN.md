# Data Control Plane: Build Plan

Product intent: [`PRODUCT.md`](PRODUCT.md). Prototype: [`prototype/data-control-plane.html`](prototype/data-control-plane.html).
This file is kept up to date as each milestone moves forward (see the status table and decision log).

## Status

| # | Milestone | Status |
|---|---|---|
| M0 | Skeleton + Mac setup | ✅ Done (tested by Tyler 2026-10-23) |
| M1 | API keys + projects | ✅ Done (tested by Tyler 2026-10-23) |
| M2 | Capabilities, sources, versioned specs | ⚪ Not started |
| M3 | Requests + allocations | ⚪ Not started |
| M4a | Batches + manual accept/reject | ⚪ Not started |
| M4b | Events + outbound webhooks | ⚪ Not started |
| M5 | Datasets, evals, coverage, portfolio (north star) | ⚪ Not started |
| M6 | Automated file checks | ⚪ Not started |
| M7 | Inbound webhooks + S3 watcher | ⚪ Not started |
| M8 | Recommendations v0 | ⚪ Not started |
| M9 | Headless polish | ⚪ Not started |

## Architecture

- **Containers:** `postgres`, `api` (FastAPI) and `worker`. The worker uses the same image and runs checks, connectors and webhook sends. MinIO runs in the dev profile only.
- **Libraries:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 + Alembic, boto3, pyarrow/polars, uv.
- **Jobs:** a Postgres-backed job queue (`FOR UPDATE SKIP LOCKED`), so Postgres is the only stateful dependency.
- **Events:** an event outbox, written in the same transaction as each change. It feeds outbound webhooks and the audit trail.
- **OpenAPI:** the spec is generated from the Pydantic models, and the committed `openapi.yaml` is the contract. Checks fail if it is stale, and oasdiff blocks breaking changes.
- **API conventions:**
  - Routes live under `/v1`, and IDs are prefixed (`cap_`, `src_`, `spc_`, `req_`, `alc_`, `bat_`, `dsv_`, `evr_`).
  - Every resource gets full CRUD, and POSTs accept `Idempotency-Key`.
  - Lists use cursor pagination, and errors use the RFC 9457 format.
- **Webhooks:**
  - Outbound webhooks follow the Standard Webhooks headers (HMAC-SHA256), retry with backoff for about 24h, and have a delivery log and redeliver.
  - Inbound webhooks have a per-source URL and secret, verified with HMAC.
- **Secrets:** API keys are hashed, and connector and webhook secrets are encrypted with a master key from `.env`.
- **Money:** amounts are stored as `NUMERIC(14,4)` plus an ISO currency. There's no currency conversion in v0, so reports group by currency.
- **Metadata-first:** data stays in customer storage behind a `StorageBackend` interface.

## Data model

All objects belong to a **Project**.

| Object | Fields | Notes |
|---|---|---|
| **Capability** | name, eval_metric, higher_is_better, value_per_point, currency | |
| **DataSource** | name, kind, unit_default, license_type, consent_scope, rights_expires_at, pii_handling, notes, connector (nullable) | kind: `human_vendor, expert_network, synthetic, rl_environment, enterprise_workflow, beta_users, licensed_dataset` |
| **Spec → SpecVersion** | record_schema, guidelines, attributes, coverage_targets (attribute → value → target share), acceptance_rules, status `draft→approved`, approved_by, change_note | Immutable once approved. Allocations require an approved version. |
| **Request** | capability_id, title, requested_by, priority, rationale, target_metric, spec_version_id (nullable), quantity, due_date, status | The request comes first, then the spec. |
| **Allocation** | request_id, data_source_id, quantity, unit, quoted_unit_rate, currency, due_date, status `planned→active→complete / cancelled` | Quoted cost = quantity × rate |
| **Batch** | allocation_id, received_at, artifacts, status `received→checking→passed/failed→accepted/rejected`, spend, currency, delivered_count, accepted_count, contributor_count, attribute_counts | One delivery against an allocation |
| **QualityRun / Result** | batch_id, check, outcome, metrics, coverage_report | |
| **Dataset → DatasetVersion** | dataset: name, capability_id. version: batch_ids (accepted only), baseline_version_id, manifest | Immutable |
| **EvalResult** | dataset_version_id, capability_id, metric, value, higher_is_better, external_run_url, recorded_at | |
| Supporting | ApiKey, Event, WebhookEndpoint, WebhookDelivery, InboundWebhook | |

### Portfolio math (`GET /v1/reports/portfolio`, by capability and by source kind)
- **Cost per usable unit** = spend ÷ accepted_count.
- **Eval change** = the main metric on this version minus the baseline version. The sign is flipped when lower is better.
- **Spend for a version** = spend on batches that are new compared with the baseline.
- **Points per $10K** = eval change ÷ spend for the version × 10,000.
- **Value** = eval change × value_per_point. **ROI** = value ÷ spend.
- **By source kind:** eval change is split by share of newly accepted units, marked `is_estimate: true` with `attribution_method: "accepted_units_share"`.
- Every figure returns the IDs it came from. Usable units are also broken down by unit type.

## Milestones

Testing uses **`http://localhost:8000/docs` → "Try it out"**, with curl as a backup.

| # | Milestone | How you test it |
|---|---|---|
| **M0** | Skeleton: compose, `/healthz`, Alembic, `.env.example`, `.gitignore`, Mac setup steps, `./scripts/check.sh` | `docker compose up`, `/docs` opens, and `./scripts/check.sh` is all green. |
| **M1** | API keys + projects (bootstrap admin key printed on first start) | Authorize in `/docs` and create a project. A request without a key gets a 401. |
| **M2** | Capabilities, data sources with rights fields, versioned specs with attributes, coverage targets and approval | Approve v1, create v2, and see that v1 is unchanged. |
| **M3** | Requests + allocations with quoted cost | Split a request across 2 vendors and 1 internal source, and see the total quoted cost. |
| **M4a** | Batches via the API (spend, counts, attribute_counts), manual accept/reject | Register a batch, accept it, and see the allocation's totals and spend update. |
| **M4b** | Event outbox + signed outbound webhooks with retries, delivery log, redeliver | Accept a batch, see a signed `batch.accepted` at a test receiver, then stop the receiver and see retries. |
| **M5** | Dataset versions, eval results, coverage vs targets, portfolio report, `scripts/demo.py`. **North-star demo.** | Run the demo script and open the portfolio in `/docs`. |
| **M6** | Automated file checks (format, schema, duplicates, stats, acceptance rules). Attribute counts are computed from the files. | Upload a skewed file to MinIO and see the coverage gap and rule failures. |
| **M7** | Inbound webhooks + S3 bucket watcher | Drop a file in MinIO and watch a batch appear and get checked. |
| **M8** | Recommendations v0: allocation suggestions, plus a diagnosis of diminishing returns + coverage gaps that suggests "refine the spec" | Use seeded flattening evals and see a suggestion with evidence. |
| **M9** | Generated client/CLI, end-to-end example script, backup/upgrade docs, GitHub Actions | Run the example script on a clean install. |

### Later
- UI, Terraform provider, training gate, audit pack, SSO, more connectors.
- Batch flags (quality/integrity/privacy) and vendor scorecards.
- The other diagnoses: label quality, eval problem, model bottleneck, saturation.
- **Ablation-based attribution:** record dataset versions that leave out one source kind, with eval results, so the portfolio uses `attribution_method: "ablation"` instead of the unit-share estimate when that data exists.

## Decision log
- 2026-10-23: Auth is API keys only, with one org per install split into projects.
- 2026-10-23: The design is metadata-first, with a `StorageBackend` interface for later managed storage.
- 2026-10-23: Postgres-backed job queue, with no Redis.
- 2026-10-23: Source-kind attribution splits by share of accepted units (an estimate). Ablation comes later.
- 2026-10-23: Coverage vs targets moved into M5 using batch-reported `attribute_counts`, so the north-star demo is complete at M5.
- 2026-10-23: M4 split into M4a (batches) and M4b (events + webhooks).
- 2026-10-23 (M0): `/healthz` checks only that the server is running. `/readyz` also checks the database and returns 503 if the database is down.
- 2026-10-23 (M0): tests use a throwaway in-memory Postgres (`db-test`, compose profile `test`, localhost:55432 only). The real database port is never exposed.
- 2026-10-23 (M0): one Docker image for both api and worker. The api applies migrations on start. Containers run as a non-root user.
- 2026-10-23 (M0): the test HTTP client is `httpx2` (maintained by Pydantic, preferred by Starlette's TestClient), chosen by Tyler. No warning filter is needed.
- 2026-10-23 (M1): the first admin key comes from `docker compose exec api python -m app.cli create-admin-key`, which prints it to the terminal, instead of being printed in the server log (rule 7: never log secrets). The log shows a hint until an admin key exists.
- 2026-10-23 (M1): keys are `dcp_` + 43 random characters. Only a SHA-256 hash is stored, and the secret is shown once. Scopes are `admin` or `project` (one project), with `read` or `write` access. The last active admin write key can't be revoked.
- 2026-10-23 (M1): project keys get 404 (not 403) for other projects, so they can't tell those projects exist. Only admin keys can create, rename or delete projects. Project names are unique. A project can't be deleted while it has active keys.
- 2026-10-23 (M1): every create, update and delete writes an `events` row in the same transaction (`project.*`, `api_key.*`), ahead of webhooks in M4b.
- 2026-10-23 (M1): an `Idempotency-Key` replay returns the original response with `Idempotent-Replayed: true`. Reusing a key with a different body gives 422. Replaying an API-key creation never re-shows the secret. Records are kept indefinitely for now; cleanup comes with the worker job queue (M4b).
- 2026-10-23 (M1): successful `/healthz` and `/readyz` calls are left out of the access log. Failed ones still appear.
- 2026-10-23 (M0): MinIO is deferred to M6, the first milestone that reads files. oasdiff is deferred until there is a first release to compare against.
