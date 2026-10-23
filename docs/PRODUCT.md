# Data Control Plane — Product Brief

Read this before planning or building anything. It explains what the product is for.
The clickable prototype in `docs/prototype/data-control-plane.html` shows the intended
experience; open it in a browser. All names and numbers in it are sample data.

## One sentence

A vendor-neutral control plane for AI training data: it decides what data to get and
from where, checks it, gates what reaches training, and shows leaders which data spend
actually improved their models.

**Pitch:** Know what your training data is worth.

## Where it fits ("planes")

- **Data collection plane:** Mercor, Surge, Micro1, Scale, labeling tools, synthetic
  pipelines, RL environment vendors, internal systems.
- **Storage plane:** S3, GCS, Databricks, Snowflake.
- **Compute plane:** GPUs and training frameworks.
- **Model / experiment plane:** W&B, MLflow, eval tools.
- **Control plane (this product):** specs, sourcing plans, routing, quality and trust
  checks, training gate, cost and ROI. It reads from and writes to the planes above.
- **Management layer (this product):** the Executive Dashboard: data portfolio,
  audit pack, vendor and source benchmarks.

It is NOT a labeling tool, a data vendor, or an experiment tracker. It integrates with them.

## Who it's for

- **Buyer:** ML or AI leader (head of ML, VP of AI). Owns the data budget and model roadmap.
- **Daily user:** the human-data / data-ops PM who runs requests, specs and vendors.
- **Also:** ML researchers (request data, see results), legal/privacy/procurement
  (consent, rights, audit records).

## The core loop (must work end to end early)

1. A **capability** (for example "Package damage detection") has a main eval metric
   and an estimated business value per point.
2. A researcher files a **request** for data to improve that capability.
3. The PM writes a versioned **spec**: format, attributes to record (for example
   package_type, light_level), coverage targets per attribute, and acceptance rules.
4. The request is split into **allocations** across **sources** (vendors, synthetic,
   internal workflows, beta users, licensed sets, RL environments, experts), each with
   a quantity, quoted unit rate and due date. A planner recommends the split from
   capacity, past quality, cost and the deadline.
5. Sources deliver **batches**. Each batch is checked (format, schema, duplicates,
   coverage vs targets, acceptance rules) and records spend, delivered and accepted
   counts, and contributor count.
6. Accepted batches become an immutable **dataset version**.
7. An **eval result** (linked to a W&B or other run) records what that dataset
   version did to the capability's metric.
8. The **portfolio** reports, per capability and per source type: spend, usable
   units, cost per usable unit, eval change, eval points per $10K, and value per point.
9. **Recommendations** follow from a diagnosis, not just the trend. When returns
   flatten, check the cause before cutting budget: wrong data mix (refine the spec),
   label quality (fix labels), eval problem (fix the eval), model bottleneck (hand off
   to the model team), or true saturation (reduce spend).

## Data sources (all first-class)

Human vendors, expert networks, synthetic data, RL environments (unit = tasks),
enterprise workflows (for example returns photos, scan exceptions), in-house testers
and beta users, licensed datasets. Each source type has its own quality check and
rights terms, but they share one model: source → allocation → batch → dataset.

## Trust and rights (collect from day one, enforce later)

License type, consent scope, rights expiry, contributor counts, PII handling notes.
Later: a training gate that blocks dataset versions without QA pass and clear rights,
and an audit pack per model version.

## Product principles

- **API-first and headless.** Everything works through the REST API and OpenAPI spec,
  so it can be driven by scripts, CI and a future Terraform provider.
- **Self-hosted.** `docker compose up` on the customer's server. Postgres is the only
  stateful dependency.
- **Integrates, doesn't replace.** Built-in connectors plus generic signed webhooks
  (inbound and outbound) so any tool can plug in.
- **Metadata-first.** Data stays in the customer's storage; we store pointers,
  checksums, attributes, results and costs.
- **Every number has a source.** Reports show where figures came from and use ranges
  where attribution is uncertain.

## What "done" looks like for the first real demo (north star)

Through the API alone, a script can:

1. Create a capability, a spec with coverage targets, and three sources.
2. File a request and split it into allocations across two vendors and one internal source.
3. Register batches with spend and counts; checks run and report coverage gaps.
4. Build a dataset version and record an eval result against it.
5. Call `GET /v1/reports/portfolio` and get spend, cost per usable unit, eval change
   and points per $10K by capability and by source type.
6. Receive signed outbound webhooks for each step.
