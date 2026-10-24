"""The north-star demo from docs/PRODUCT.md, through the API alone. Built-in Python only.

    DCP_API_KEY=dcp_... python3 scripts/demo.py

It creates a fresh project and runs the whole loop:
  1. a capability, a spec with coverage targets, and three sources
  2. a request split across two vendors and one internal source
  3. batches with real delivery files, checked automatically (format, schema, duplicates,
     acceptance rules), and coverage gaps
  4. two dataset versions with eval results
  5. the portfolio: spend, cost per usable unit, eval change and points per $10K
  6. signed webhooks for every step, received and checked by this script
  7. (with --diagnosis) a third delivery that barely helps: the diagnosis says returns are
     flattening and the data mix is off, drafts a refined spec, and plans the next request

Options: DCP_URL (default http://localhost:8000), --no-webhooks, --port (default 9000).
Delivery files are written to ./data (which DCP sees as /data); see --data-dir.
Runs on Python 3.9 and later (macOS's built-in python3 works).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol

sys.path.insert(0, str(Path(__file__).parent))
from webhook_receiver import verify  # noqa: E402


class Api(Protocol):
    def __call__(self, method: str, path: str, body: Any = None) -> Any: ...


class DemoError(Exception):
    pass


def http_api(base_url: str, key: str) -> Api:
    def call(method: str, path: str, body: Any = None) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(  # noqa: S310 (the URL is the operator's own DCP)
            base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                raw = response.read()
        except urllib.error.HTTPError as exc:
            problem = json.loads(exc.read() or b"{}")
            detail = problem.get("detail", problem)
            raise DemoError(f"{method} {path} -> {exc.code}: {detail}") from None
        except urllib.error.URLError as exc:
            raise DemoError(
                f"Can't reach DCP at {base_url} ({exc.reason}). Is it running?"
            ) from None
        return json.loads(raw) if raw else None

    return call


# --- webhook capture -------------------------------------------------------------------------


class Inbox:
    def __init__(self, port: int) -> None:
        self.messages: list[tuple[dict[str, Any], dict[str, str], bytes]] = []
        inbox = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                inbox.messages.append((json.loads(body), dict(self.headers.items()), body))
                self.send_response(200)
                self.end_headers()

            def log_message(self, *_: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("0.0.0.0", port), Handler)  # noqa: S104
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


# --- delivery files --------------------------------------------------------------------------

RECORD_SCHEMA = {
    "type": "object",
    "required": ["id", "image_uri", "package_type", "severity"],
    "properties": {
        "id": {"type": "string"},
        "image_uri": {"type": "string"},
        "package_type": {"enum": ["box", "mailer", "shrink_wrapped"]},
        "severity": {"type": "integer", "minimum": 1, "maximum": 5},
    },
}


def make_records(source: str, mix: dict[str, int]) -> list[dict[str, Any]]:
    """One labelled image per record, with the given number of each package type."""
    records = []
    for package_type, count in mix.items():
        for _ in range(count):
            i = len(records)
            records.append(
                {
                    "id": f"{source}-{i:05d}",
                    "image_uri": f"s3://acme-cv-intake/{source}/img_{i:05d}.jpg",
                    "package_type": package_type,
                    "severity": 1 + i % 5,
                }
            )
    return records


class Files:
    """Writes delivery files where DCP can read them (DCP's /data is this machine's ./data)."""

    def __init__(self, data_dir: Path, uri_root: str, run_name: str) -> None:
        self.dir = data_dir / run_name
        self.uri_root = f"{uri_root.rstrip('/')}/{run_name}"
        self.dir.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        (self.dir / name).write_text("".join(json.dumps(r) + "\n" for r in records))
        return {
            "uri": f"file://{self.uri_root}/{name}",
            "format": "jsonl",
            "record_count": len(records),
        }


def wait_for_checks(api: Api, batch_id: str, timeout: float = 120) -> dict[str, Any]:
    deadline = time.time() + timeout
    while True:
        batch = api("GET", f"/v1/batches/{batch_id}")
        if batch["status"] != "checking" and batch["quality"]["status"] not in (
            "queued",
            "running",
        ):
            return batch
        if time.time() > deadline:
            raise DemoError(f"Checks on {batch_id} didn't finish. Is the worker running?")
        time.sleep(0.5)


def describe_checks(api: Api, batch: dict[str, Any]) -> str:
    run = api("GET", f"/v1/quality-runs/{batch['quality']['run_id']}")
    notes = [c["summary"] for c in run["checks"] if c["outcome"] in ("warning", "failed")]
    return f"checks {run['status']}" + (": " + " | ".join(notes) if notes else "")


# --- the demo --------------------------------------------------------------------------------


def money(value: str) -> str:
    return f"${float(value):,.2f}"


def run_diagnosis(
    api: Api,
    say: Any,
    files: Files,
    capability_id: str,
    spec_version_id: str,
    dataset_id: str,
    previous_version_id: str,
    allocs: dict[str, Any],
) -> dict[str, Any]:
    say("\n7. Diagnosis: is the spend still paying off?")
    records = make_records("surge2", {"box": 2400, "mailer": 450, "shrink_wrapped": 150})
    batch = api(
        "POST",
        "/v1/batches",
        {
            "allocation_id": allocs["Surge"]["id"],
            "artifacts": [files.write("surge-2.jsonl", records)],
            "delivered_count": 3000,
            "spend": "4650",
            "reported_metrics": {"agreement": 0.9},
        },
    )
    batch = wait_for_checks(api, batch["id"])
    api("POST", f"/v1/batches/{batch['id']}/accept", {"accepted_count": 2900})
    v3 = api(
        "POST",
        f"/v1/datasets/{dataset_id}/versions",
        {"batch_ids": [batch["id"]], "baseline_version_id": previous_version_id},
    )
    api("POST", "/v1/eval-results", {"dataset_version_id": v3["id"], "value": 0.861})
    say("   Surge delivered 3,000 more (mostly boxes); v3 moved recall only 0.857 -> 0.861")

    diag = api("GET", f"/v1/capabilities/{capability_id}/diagnosis")
    for v in diag["versions"]:
        say(f"   v{v['version']}: +{v['points']} points, {v['points_per_10k']} points per $10K")
    say(f"   Trend: {diag['trend']} -> recommendation: {diag['recommendation']}")
    say(f"   {diag['summary']}")
    if diag["suggested_spec_change"]:
        targets = diag["suggested_spec_change"]["coverage_targets"]
        say(f"   Suggested coverage targets: {targets}")
        draft = api("POST", f"/v1/capabilities/{capability_id}/diagnosis/draft-spec", {})
        say(f"   Drafted spec version {draft['version']} for review (not approved).")

    req = api(
        "POST",
        "/v1/requests",
        {
            "capability_id": capability_id,
            "title": "Next round",
            "quantity": 6000,
            "unit": "images",
            "spec_version_id": spec_version_id,
        },
    )
    plan = api("GET", f"/v1/requests/{req['id']}/allocation-plan")
    say("   Suggested split for the next 6,000 images:")
    for x in plan["suggestions"]:
        cost = money(x["expected_cost"]) if x["expected_cost"] else "?"
        say(
            f"     {x['name']:<15} {x['role']:<6} {x['expected_usable']:>5,} usable "
            f"(order {x['order_quantity']:,}, ~{cost})"
        )
    return {"diagnosis": diag, "plan": plan}


def run(
    api: Api,
    *,
    webhook_port: int | None = None,
    say: Any = print,
    data_dir: Path | None = None,
    uri_root: str = "/data",
    diagnosis: bool = False,
) -> dict[str, Any]:
    """Runs the north star. Returns the portfolio and webhook counts (used by the tests)."""
    files = Files(
        data_dir or Path(__file__).resolve().parents[1] / "data",
        uri_root,
        f"demo-{time.strftime('%Y%m%d-%H%M%S')}",
    )
    inbox = endpoint = None
    if webhook_port:
        inbox = Inbox(webhook_port)
        endpoint = api(
            "POST",
            "/v1/webhook-endpoints",
            {
                "url": f"http://host.docker.internal:{webhook_port}/",
                "description": "North-star demo (removed at the end)",
            },
        )

    try:
        say("\n1. Capability, spec with coverage targets, three sources")
        project = api(
            "POST", "/v1/projects", {"name": f"North-star demo {time.strftime('%H:%M:%S')}"}
        )
        pid = project["id"]
        cap = api(
            "POST",
            "/v1/capabilities",
            {
                "project_id": pid,
                "name": "Package damage detection",
                "eval_metric": "recall@0.5",
                "value_per_point": "25000",
                "point_size": 0.01,
                "currency": "USD",
            },
        )
        spec = api(
            "POST",
            "/v1/specs",
            {
                "project_id": pid,
                "name": "Package damage",
                "first_version": {
                    "guidelines": "Box every visible damaged area at least 12 px across.",
                    "attributes": [
                        {"name": "package_type", "values": ["box", "mailer", "shrink_wrapped"]}
                    ],
                    "coverage_targets": {
                        "package_type": {"box": 0.30, "mailer": 0.35, "shrink_wrapped": 0.35}
                    },
                    "coverage_tolerance": 0.05,
                    "record_schema": RECORD_SCHEMA,
                    "acceptance_rules": [
                        {"metric": "agreement", "operator": ">=", "threshold": 0.85},
                        {"metric": "duplicate_rate", "operator": "<=", "threshold": 0.02},
                        {"metric": "schema_valid_rate", "operator": ">=", "threshold": 0.99},
                    ],
                },
            },
        )
        v1 = api(
            "POST", f"/v1/specs/{spec['id']}/versions/1/approve", {"approved_by": "Priya Nair"}
        )
        sources = {
            name: api(
                "POST",
                "/v1/data-sources",
                {
                    "project_id": pid,
                    "name": name,
                    "kind": kind,
                    "default_unit": "images",
                    "license_type": license_type,
                },
            )["id"]
            for name, kind, license_type in (
                ("Surge", "human_vendor", "vendor_agreement"),
                ("Mercor", "human_vendor", "vendor_agreement"),
                ("Returns photos", "enterprise_workflow", "customer_terms"),
            )
        }
        say(f"   capability {cap['id']}, spec v1 approved, sources: {', '.join(sources)}")

        say("\n2. A request split across two vendors and one internal source")
        req = api(
            "POST",
            "/v1/requests",
            {
                "capability_id": cap["id"],
                "title": "Shrink-wrapped and glossy packaging",
                "requested_by": "Priya Nair",
                "priority": "P1",
                "quantity": 10000,
                "unit": "images",
                "spec_version_id": v1["id"],
            },
        )
        api("POST", f"/v1/requests/{req['id']}/open")
        allocs = {}
        for name, qty, rate in (
            ("Surge", 4000, "1.55"),
            ("Mercor", 4000, "1.65"),
            ("Returns photos", 3000, "0.20"),
        ):
            alloc = api(
                "POST",
                "/v1/allocations",
                {
                    "request_id": req["id"],
                    "data_source_id": sources[name],
                    "quantity": qty,
                    "quoted_unit_rate": rate,
                    "currency": "USD",
                },
            )
            allocs[name] = api("POST", f"/v1/allocations/{alloc['id']}/activate")
            say(f"   {name:<15} {qty:>6,} images at ${rate} = {money(alloc['quoted_cost'])}")

        say("\n3. Deliveries, checked automatically; coverage against targets")
        surge_records = make_records("surge", {"box": 1474, "mailer": 1368, "shrink_wrapped": 1158})
        # Mercor re-delivers 50 images Surge already delivered (a cross-batch duplicate).
        mercor_records = surge_records[:50] + make_records(
            "mercor", {"box": 1046, "mailer": 1405, "shrink_wrapped": 1499}
        )
        # The returns export repeats 30 rows and has 12 severities out of range.
        returns_records = make_records(
            "returns", {"box": 1028, "mailer": 1028, "shrink_wrapped": 914}
        )
        returns_records += returns_records[:30]
        for r in returns_records[100:112]:
            r["severity"] = 9

        surge = api(
            "POST",
            "/v1/batches",
            {
                "allocation_id": allocs["Surge"]["id"],
                "artifacts": [files.write("surge.jsonl", surge_records)],
                "delivered_count": 4000,
                "spend": "6200",
                "contributor_count": 46,
                "reported_metrics": {"agreement": 0.91},
            },
        )
        surge = wait_for_checks(api, surge["id"])
        say(f"   Surge: {surge['status']} ({describe_checks(api, surge)})")
        api(
            "POST",
            f"/v1/batches/{surge['id']}/accept",
            {"accepted_count": 3800, "decided_by": "Dana Okafor"},
        )

        mercor = api(  # accepted in the vendor's own QA, imported already decided
            "POST",
            "/v1/batches",
            {
                "allocation_id": allocs["Mercor"]["id"],
                "artifacts": [files.write("mercor.jsonl", mercor_records)],
                "delivered_count": 4000,
                "spend": "6600",
                "reported_metrics": {"agreement": 0.88},
                "external_ref": "mercor-delivery-118",
                "decision": {
                    "status": "accepted",
                    "decided_by": "mercor-qa",
                    "accepted_count": 3700,
                    "attribute_counts": {
                        "package_type": {"box": 1000, "mailer": 1300, "shrink_wrapped": 1400}
                    },
                },
            },
        )
        mercor = wait_for_checks(api, mercor["id"])
        say(f"   Mercor: {mercor['status']} by mercor-qa ({describe_checks(api, mercor)})")

        returns = api(
            "POST",
            "/v1/batches",
            {
                "allocation_id": allocs["Returns photos"]["id"],
                "artifacts": [files.write("returns.jsonl", returns_records)],
                "delivered_count": 3000,
                "spend": "600",
            },
        )
        returns = wait_for_checks(api, returns["id"])
        say(f"   Returns photos: {returns['status']} ({describe_checks(api, returns)})")
        api("POST", f"/v1/batches/{returns['id']}/accept", {"accepted_count": 2600})

        surge_cov = api("GET", f"/v1/batches/{surge['id']}/coverage")
        request_cov = api("GET", f"/v1/requests/{req['id']}/coverage")
        say(f"   Surge batch gaps: {surge_cov['gaps'] or 'none'}")
        say(f"   Whole request gaps: {request_cov['gaps'] or 'none (within tolerance)'}")

        say("\n4. Dataset versions and eval results")
        dataset = api("POST", "/v1/datasets", {"capability_id": cap["id"], "name": "damage-det"})
        ds_v1 = api(
            "POST",
            f"/v1/datasets/{dataset['id']}/versions",
            {"batch_ids": [surge["id"]], "notes": "Surge only."},
        )
        api(
            "POST",
            "/v1/eval-results",
            {"dataset_version_id": ds_v1["id"], "value": 0.812, "run_name": "dmg-r50-v1"},
        )
        ds_v2 = api(
            "POST",
            f"/v1/datasets/{dataset['id']}/versions",
            {
                "batch_ids": [mercor["id"], returns["id"]],
                "notes": "Adds Mercor and returns photos.",
            },
        )
        last_eval = api(
            "POST",
            "/v1/eval-results",
            {"dataset_version_id": ds_v2["id"], "value": 0.857, "run_name": "dmg-r50-v2"},
        )
        say(f"   v1 {ds_v1['id']}: recall 0.812   v2 {ds_v2['id']}: recall 0.857 (baseline v1)")

        say("\n5. Portfolio")
        report = api("GET", f"/v1/reports/portfolio?project_id={pid}")
        for row in report["by_capability"]:
            spend = ", ".join(money(a["amount"]) for a in row["spend"])
            unit_cost = ", ".join(
                f"{money(c['amount'])}/{c['unit'][:-1]}" for c in row["cost_per_usable_unit"]
            )
            say(f"   {row['name']}")
            usable = ", ".join(f"{u['count']:,} {u['unit']}" for u in row["usable_units"])
            say(f"     spend {spend}; usable {usable}; cost per usable {unit_cost}")
            say(
                f"     eval change +{row['eval_change_points']} points; "
                f"{row['points_per_10k']} points per $10K; "
                f"value {money(row['value'])}; ROI {row['roi']}x"
            )
        say("   By source type (estimate: split by share of added accepted items):")
        for row in report["by_source_kind"]:
            say(
                f"     {row['kind']:<20} spend {money(row['spend'][0]['amount']):>11}  "
                f"eval change {row['eval_change_points']:>7} pts  per $10K {row['points_per_10k']}"
            )

        counts: Counter[str] = Counter()
        if inbox and endpoint:
            say("\n6. Signed webhooks")
            # Wait until the last change made above has been delivered and nothing is still
            # queued. (The worker picks up new events about once a second.)
            last_event = api("GET", f"/v1/events?subject_id={last_eval['id']}")["data"][0]
            deadline = time.time() + 20
            while time.time() < deadline:
                ours = f"/v1/webhook-deliveries?endpoint_id={endpoint['id']}"
                last = api("GET", f"{ours}&event_id={last_event['id']}")["data"]
                pending = api("GET", f"{ours}&status=pending")["data"]
                if last and last[0]["status"] == "delivered" and not pending:
                    break
                time.sleep(0.5)
            others = 0
            for message, headers, body in inbox.messages:
                if message.get("project_id") != pid:
                    continue
                h = {k.lower(): v for k, v in headers.items()}
                ours = verify(
                    endpoint["secret"],
                    h["webhook-id"],
                    h["webhook-timestamp"],
                    body,
                    h["webhook-signature"],
                )
                if ours:
                    counts[message["type"]] += 1
                else:  # signed for another endpoint that points at the same port
                    others += 1
            total = sum(counts.values())
            say(f"   {total} messages received, every signature verified:")
            for event_type, n in sorted(counts.items()):
                say(f"     {event_type:<28} {n}")
            if others:
                say(
                    f"   ({others} more came from another webhook endpoint that also points at "
                    f"port {webhook_port}; they were ignored.)"
                )
            if not total:
                say(
                    "   None arrived. Is the worker running, and did macOS allow "
                    "incoming connections?"
                )

        diag = None
        if diagnosis:  # after the webhook check, so step 6 counts only steps 1-5
            diag = run_diagnosis(
                api, say, files, cap["id"], v1["id"], dataset["id"], ds_v2["id"], allocs
            )

        say(f"\nDone. Project {pid}: explore it at /docs.")
        return {"project_id": pid, "portfolio": report, "webhooks": dict(counts), "diagnosis": diag}
    finally:
        if endpoint:
            api("DELETE", f"/v1/webhook-endpoints/{endpoint['id']}")
        if inbox:
            inbox.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DCP north-star demo.")
    parser.add_argument("--no-webhooks", action="store_true", help="Skip step 6.")
    parser.add_argument(
        "--diagnosis", action="store_true", help="Add step 7: the diagnosis and a plan."
    )
    parser.add_argument("--port", type=int, default=9000, help="Port for receiving webhooks.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
        help="Where to write delivery files: the folder DCP reads as /data (default ./data).",
    )
    args = parser.parse_args()
    key = os.environ.get("DCP_API_KEY")
    if not key:
        print(
            "Set DCP_API_KEY to an admin API key, e.g. DCP_API_KEY=dcp_... python3 scripts/demo.py"
        )
        return 2
    api = http_api(os.environ.get("DCP_URL", "http://localhost:8000"), key)
    try:
        run(
            api,
            webhook_port=None if args.no_webhooks else args.port,
            data_dir=args.data_dir,
            diagnosis=args.diagnosis,
        )
    except DemoError as exc:
        print(f"\nStopped: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
