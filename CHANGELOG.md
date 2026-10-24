# Changelog

All notable changes to Data Control Plane. Versions follow semantic versioning; until 1.0,
breaking API changes are still possible but are always called out here.

## 0.9.0 (2026-10-23): first feature-complete preview

The whole loop from `docs/PRODUCT.md` works end to end through the API alone.

**Plan and source**
- API keys (admin / project, read / write) and projects.
- Capabilities, with a main eval metric, value per point, point size and flattening threshold.
- Data sources of every kind, with rights fields (license, consent, expiry, PII handling).
- Specs with immutable, approved versions: attributes, coverage targets, acceptance rules,
  record format.
- Requests split into allocations across sources, with quoted cost.

**Deliver and check**
- Batches registered through the API, imported already decided from vendor QA or labeling
  tools, pushed by signed inbound webhooks, or found automatically in watched S3 buckets.
- Automated quality checks on delivered files: format, schema, duplicates (within the batch
  and across the project), stats, attribute counts, and acceptance rules.
- Coverage against targets, per batch and per request.

**Measure and recommend**
- Frozen dataset versions with manifests, and eval results linked to training runs.
- Portfolio report: spend, cost per usable unit, eval change, points per $10K, value and ROI,
  by capability and by source type.
- Allocation plans for requests, and a diagnosis that recommends refining the spec when
  returns flatten because of a data-mix gap.

**Integrate and run**
- Signed outbound webhooks (Standard Webhooks) with retries and a delivery log; an event log
  API.
- A generated Python client (`clients/python`), the `dcp` command line (`clients/cli`), and
  examples for CI (`examples/`).
- Backup and restore scripts and an operations guide (`docs/OPERATIONS.md`).

**Upgrade note:** this release needs `DCP_SECRET_KEY` in `.env` (see `.env.example`).
