"""The automated checks on a batch's files.

Reads every file once (streamed) and produces: files, format, schema, duplicates, stats,
attribute counts and acceptance rules, each with an outcome (passed / warning / failed /
skipped), a plain-language summary and details. A run fails if any check fails; warnings are
for a person to look at. Acceptance rules decide pass/fail for measured quality: e.g.
`schema_valid_rate >= 0.99` or `duplicate_rate <= 0.02`.

Metrics available to acceptance rules:
  record_count, parse_error_rate, schema_valid_rate, duplicate_rate, duplicates_in_batch,
  duplicates_in_project, empty_rate.<field>, plus anything the source reported in
  `reported_metrics` (e.g. agreement, or `agreement[package_type=shrink_wrapped]` for a rule
  with `applies_to`). Measured values win over reported ones.
"""

import csv
import hashlib
import io
import json
import operator
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from sqlalchemy import delete, insert, text
from sqlalchemy.orm import Session

from app.checks.storage import HashingReader, StorageError, open_artifact
from app.config import get_settings
from app.models import Batch, QualityRun, RecordFingerprint
from app.services import connectors

RECORD_FORMATS = ("jsonl", "csv")
EXAMPLES = 5
MAX_FIELDS = 200
SHARE_MISMATCH = 0.05  # reported vs counted attribute shares
OPERATORS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "==": operator.eq,
}


@dataclass
class Collected:
    """Everything learned from reading the files."""

    files: list[dict[str, Any]] = field(default_factory=list)
    records: int = 0
    parse_errors: int = 0
    parse_examples: list[str] = field(default_factory=list)
    schema_invalid: int = 0
    schema_examples: list[str] = field(default_factory=list)
    fields: set[str] = field(default_factory=set)
    nonempty: Counter[str] = field(default_factory=Counter)
    attribute_counts: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    fingerprints: set[int] = field(default_factory=set)
    duplicates_in_batch: int = 0
    truncated: bool = False
    unsupported: list[str] = field(default_factory=list)


def fingerprint(record: dict[str, Any]) -> int:
    """64-bit fingerprint of a record's content (key order doesn't matter)."""
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()
    return int.from_bytes(hashlib.blake2b(canonical, digest_size=8).digest(), "big", signed=True)


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _records(reader: HashingReader, fmt: str, c: Collected) -> Iterator[dict[str, Any]]:
    buffered = io.BufferedReader(reader, buffer_size=1 << 20)
    if fmt == "jsonl":
        for number, line in enumerate(buffered, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("each line must be a JSON object")
            except (ValueError, UnicodeDecodeError) as exc:
                c.parse_errors += 1
                if len(c.parse_examples) < EXAMPLES:
                    c.parse_examples.append(f"line {number}: {exc}")
                continue
            yield record
    else:  # csv
        text_stream = io.TextIOWrapper(buffered, encoding="utf-8", newline="")
        try:
            for row in csv.DictReader(text_stream):
                # Cells beyond the header row come under a None key; give them a name.
                yield {(k if k is not None else "_extra_cells"): v for k, v in row.items()}
        except (UnicodeDecodeError, csv.Error) as exc:
            c.parse_errors += 1
            if len(c.parse_examples) < EXAMPLES:
                c.parse_examples.append(str(exc))
        finally:
            text_stream.detach()


def collect(batch: Batch, s3_clients: dict[str, Any] | None = None) -> Collected:
    c = Collected()
    version = batch.spec_version
    validator = Draft202012Validator(version.record_schema) if version.record_schema else None
    attribute_names = [a["name"] for a in version.attributes]
    limit = get_settings().dcp_check_max_records
    s3_clients = s3_clients or {}

    for artifact in batch.artifacts:
        uri, fmt = artifact["uri"], artifact["format"]
        info: dict[str, Any] = {"uri": uri, "format": fmt, "ok": True, "problems": []}
        c.files.append(info)
        records_in_file = 0
        try:
            with open_artifact(uri, s3_client=s3_clients.get(urlsplit(uri).netloc)) as reader:
                if fmt in RECORD_FORMATS:
                    for record in _records(reader, fmt, c):
                        if c.records >= limit:
                            c.truncated = True
                            break
                        records_in_file += 1
                        c.records += 1
                        if validator is not None:
                            errors = list(validator.iter_errors(record))
                            if errors:
                                c.schema_invalid += 1
                                if len(c.schema_examples) < EXAMPLES:
                                    where = "/".join(str(p) for p in errors[0].absolute_path)
                                    c.schema_examples.append(
                                        f"record {c.records}{' at ' + where if where else ''}: "
                                        f"{errors[0].message}"
                                    )
                        for key, value in record.items():
                            if key not in c.fields and len(c.fields) >= MAX_FIELDS:
                                continue  # very wide records: describe the first fields only
                            c.fields.add(key)
                            if not _is_empty(value):
                                c.nonempty[key] += 1
                        for name in attribute_names:
                            value = record.get(name)
                            if not _is_empty(value):
                                c.attribute_counts[name][str(value)] += 1
                        fp = fingerprint(record)
                        if fp in c.fingerprints:
                            c.duplicates_in_batch += 1
                        else:
                            c.fingerprints.add(fp)
                else:
                    c.unsupported.append(f"{uri} ({fmt})")
                if not c.truncated:
                    reader.drain()
                    _compare_file(info, artifact, reader, records_in_file, fmt)
        except StorageError as exc:
            info["ok"] = False
            info["problems"].append(str(exc))
        info["records"] = records_in_file if fmt in RECORD_FORMATS else None
    return c


def _compare_file(
    info: dict[str, Any], artifact: dict[str, Any], reader: HashingReader, records: int, fmt: str
) -> None:
    info["sha256"] = reader.sha256.hexdigest()
    info["size_bytes"] = reader.size
    if artifact.get("sha256") and artifact["sha256"] != info["sha256"]:
        info["ok"] = False
        info["problems"].append("checksum doesn't match (the file differs from what was declared)")
    if artifact.get("size_bytes") is not None and artifact["size_bytes"] != reader.size:
        info["ok"] = False
        info["problems"].append(
            f"size is {reader.size:,} bytes, declared {artifact['size_bytes']:,}"
        )
    declared = artifact.get("record_count")
    if fmt in RECORD_FORMATS and declared is not None and declared != records:
        info["record_count_mismatch"] = f"{records:,} records, declared {declared:,}"


def _check(name: str, outcome: str, summary: str, **details: Any) -> dict[str, Any]:
    return {"name": name, "outcome": outcome, "summary": summary, "details": details}


def _duplicates_in_project(session: Session, batch: Batch) -> int:
    return int(
        session.execute(
            text(
                """
                SELECT count(*) FROM record_fingerprints f
                WHERE f.batch_id = :batch AND EXISTS (
                    SELECT 1 FROM record_fingerprints g JOIN batches b ON b.id = g.batch_id
                    WHERE g.project_id = :project AND g.fingerprint = f.fingerprint
                      AND g.batch_id <> :batch AND b.status = 'accepted')
                """
            ),
            {"batch": batch.id, "project": batch.project_id},
        ).scalar_one()
    )


def _store_fingerprints(session: Session, batch: Batch, fingerprints: set[int]) -> None:
    session.execute(delete(RecordFingerprint).where(RecordFingerprint.batch_id == batch.id))
    rows = [
        {"batch_id": batch.id, "fingerprint": fp, "project_id": batch.project_id}
        for fp in fingerprints
    ]
    for start in range(0, len(rows), 10_000):
        session.execute(insert(RecordFingerprint), rows[start : start + 10_000])


def execute(session: Session, run: QualityRun) -> None:
    """Run every check and fill in `run` (status, checks, metrics, attribute counts)."""
    batch = session.get_one(Batch, run.batch_id)
    version = batch.spec_version
    c = collect(batch, connectors.s3_clients_for(session, batch))
    _store_fingerprints(session, batch, c.fingerprints)
    in_project = _duplicates_in_project(session, batch) if c.fingerprints else 0

    n = c.records
    metrics: dict[str, Any] = {
        "record_count": n,
        "parse_error_rate": round(c.parse_errors / (n + c.parse_errors), 4)
        if n + c.parse_errors
        else 0.0,
        "duplicates_in_batch": c.duplicates_in_batch,
        "duplicates_in_project": in_project,
        "duplicate_rate": round((c.duplicates_in_batch + in_project) / n, 4) if n else 0.0,
    }
    if version.record_schema:
        metrics["schema_valid_rate"] = round((n - c.schema_invalid) / n, 4) if n else 0.0
    for key in sorted(c.fields):
        metrics[f"empty_rate.{key}"] = round(1 - c.nonempty[key] / n, 4) if n else 0.0

    checks = [
        _files_check(c),
        _format_check(c),
        _schema_check(c, bool(version.record_schema)),
        _duplicates_check(c, in_project),
        _stats_check(c, metrics),
        _attribute_check(c, batch),
        _rules_check(version.acceptance_rules, metrics, batch.reported_metrics or {}),
    ]
    run.checks = checks
    run.metrics = metrics
    run.attribute_counts = {k: dict(v) for k, v in c.attribute_counts.items()}
    run.status = "failed" if any(ch["outcome"] == "failed" for ch in checks) else "passed"


def _files_check(c: Collected) -> dict[str, Any]:
    if not c.files:
        return _check("files", "skipped", "The batch lists no files.")
    bad = [f for f in c.files if not f["ok"]]
    if bad:
        return _check(
            "files",
            "failed",
            f"{len(bad)} of {len(c.files)} file(s) couldn't be read or don't match "
            "what was declared.",
            files=c.files,
        )
    return _check("files", "passed", f"All {len(c.files)} file(s) read.", files=c.files)


def _format_check(c: Collected) -> dict[str, Any]:
    readable = [f for f in c.files if f["format"] in RECORD_FORMATS and f["ok"]]
    notes = [
        f"{f['uri']}: {f['record_count_mismatch']}" for f in c.files if "record_count_mismatch" in f
    ]
    if c.truncated:
        notes.append(f"Stopped after {c.records:,} records (DCP_CHECK_MAX_RECORDS).")
    if c.unsupported:
        notes.append("Not read as records (format not supported yet): " + ", ".join(c.unsupported))
    if not readable:
        if c.unsupported:
            return _check("format", "warning", "No JSONL or CSV files to read.", notes=notes)
        return _check("format", "skipped", "No readable JSONL or CSV files.")
    if c.records == 0:
        return _check("format", "failed", "No records could be read.", examples=c.parse_examples)
    if c.parse_errors or notes:
        return _check(
            "format",
            "warning",
            f"{c.records:,} records read; {c.parse_errors:,} line(s) couldn't be parsed.",
            examples=c.parse_examples,
            notes=notes,
        )
    return _check(
        "format", "passed", f"{c.records:,} records read, all valid {'/'.join(RECORD_FORMATS)}."
    )


def _schema_check(c: Collected, has_schema: bool) -> dict[str, Any]:
    if not has_schema:
        return _check("schema", "skipped", "The spec version has no record format (record_schema).")
    if not c.records:
        return _check("schema", "skipped", "No records to check.")
    if c.schema_invalid:
        return _check(
            "schema",
            "warning",
            f"{c.schema_invalid:,} of {c.records:,} records don't match the record format.",
            examples=c.schema_examples,
        )
    return _check("schema", "passed", f"All {c.records:,} records match the record format.")


def _duplicates_check(c: Collected, in_project: int) -> dict[str, Any]:
    if not c.records:
        return _check("duplicates", "skipped", "No records to check.")
    if c.duplicates_in_batch or in_project:
        return _check(
            "duplicates",
            "warning",
            f"{c.duplicates_in_batch:,} repeated within this batch; {in_project:,} already in "
            "accepted batches of this project.",
        )
    return _check("duplicates", "passed", "No duplicate records found.")


def _stats_check(c: Collected, metrics: dict[str, Any]) -> dict[str, Any]:
    if not c.records:
        return _check("stats", "skipped", "No records to describe.")
    empty = {
        k.removeprefix("empty_rate."): v for k, v in metrics.items() if k.startswith("empty_rate.")
    }
    mostly_empty = sorted(k for k, v in empty.items() if v > 0)
    summary = f"{c.records:,} records, {len(empty)} fields."
    if mostly_empty:
        summary += f" Some values missing in: {', '.join(mostly_empty[:10])}."
    return _check("stats", "passed", summary, empty_rate=empty)


def _attribute_check(c: Collected, batch: Batch) -> dict[str, Any]:
    attrs = batch.spec_version.attributes
    if not attrs:
        return _check("attribute_counts", "skipped", "The spec version has no attributes.")
    if not c.records:
        return _check("attribute_counts", "skipped", "No records to count.")
    problems = []
    for attr in attrs:
        name, allowed = attr["name"], set(attr["values"])
        counts = c.attribute_counts.get(name, Counter())
        unknown = sorted(set(counts) - allowed)
        if unknown:
            problems.append(f"{name}: values not in the spec: {', '.join(unknown[:5])}")
        missing = c.records - sum(counts.values())
        if missing:
            problems.append(f"{name}: missing in {missing:,} records")
        reported = (batch.attribute_counts or {}).get(name)
        if reported and counts:
            rep_total, got_total = sum(reported.values()), sum(counts.values())
            for value in sorted(allowed):
                rep = reported.get(value, 0) / rep_total if rep_total else 0
                got = counts.get(value, 0) / got_total
                if abs(rep - got) > SHARE_MISMATCH:
                    problems.append(f"{name}={value}: {got:.0%} in the files, {rep:.0%} reported")
    counted = {k: dict(v) for k, v in c.attribute_counts.items()}
    if problems:
        return _check(
            "attribute_counts",
            "warning",
            "Counted from the files; some don't match the spec or what was reported.",
            problems=problems,
            counts=counted,
        )
    return _check("attribute_counts", "passed", "Counted from the files.", counts=counted)


def _rules_check(
    rules: list[dict[str, Any]], measured: dict[str, Any], reported: dict[str, float]
) -> dict[str, Any]:
    if not rules:
        return _check("acceptance_rules", "skipped", "The spec version has no acceptance rules.")
    results = []
    for rule in rules:
        key = rule["metric"]
        if rule.get("applies_to"):
            key += "[" + ",".join(f"{a}={v}" for a, v in sorted(rule["applies_to"].items())) + "]"
        if key in measured and not rule.get("applies_to"):
            value, source = measured[key], "measured"
        elif key in reported:
            value, source = reported[key], "reported"
        else:
            results.append({**rule, "key": key, "outcome": "not_evaluated", "value": None})
            continue
        ok = OPERATORS[rule["operator"]](value, rule["threshold"])
        results.append(
            {
                **rule,
                "key": key,
                "outcome": "passed" if ok else "failed",
                "value": value,
                "source": source,
            }
        )
    failed = [r for r in results if r["outcome"] == "failed"]
    unknown = [r for r in results if r["outcome"] == "not_evaluated"]
    if failed:
        described = "; ".join(
            f"{r['key']} = {r['value']} (needs {r['operator']} {r['threshold']})" for r in failed
        )
        return _check("acceptance_rules", "failed", f"Failed: {described}.", rules=results)
    if unknown:
        return _check(
            "acceptance_rules",
            "warning",
            f"{len(results) - len(unknown)} rule(s) passed; no value for "
            + ", ".join(r["key"] for r in unknown)
            + " (report it in reported_metrics).",
            rules=results,
        )
    return _check(
        "acceptance_rules", "passed", f"All {len(results)} rule(s) passed.", rules=results
    )
