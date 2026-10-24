"""Recommendations v0: an allocation plan for a request, and a diagnosis for a capability.

Both are suggestions with their evidence; nothing is changed until someone acts on them.

Allocation plan
- Evidence per source (last 90 days): accept rate, cost per usable unit, usable units per day,
  open commitments, last quoted rate, and the attribute mix of its accepted deliveries.
- Sources are left out if their unit differs from the request's or their rights expire before
  the due date (or have already expired).
- Untested sources share a pilot of up to 10% of the remaining quantity.
- Proven sources share the rest in proportion to 1 / cost per usable unit, each capped by what
  its throughput can deliver by the due date (minus what it already owes); what no one can cover
  is reported as a shortfall.
- Order quantities add extra for expected rejects (needed / accept rate, at most double).

Diagnosis
- Scores each dataset version of the capability (version vs baseline, as in the portfolio).
- Flattening: the latest version's points per 10K < flattening_threshold x the average of the
  earlier versions (needs 2+ scored versions with spend).
- When flattening, checks the data mix of the latest version against its spec's coverage
  targets: gaps -> "refine the spec", with suggested targets; no gaps -> "investigate" (label
  quality, eval and model causes aren't checked yet, so it never says "cut spend").
"""

import math
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict
from app.models import Allocation, Batch, Dataset, DatasetVersion, DataSource
from app.models.base import utcnow
from app.schemas import recommendations as schemas
from app.schemas import specs as spec_schemas
from app.services import capabilities, coverage, portfolio, specs
from app.services import requests as request_service
from app.services.principal import Principal

LOOKBACK = timedelta(days=90)
PILOT_SHARE = 0.10
MIN_ACCEPT_RATE = 0.5  # never order more than double what's needed


# --- allocation plan -------------------------------------------------------------------------


def _evidence(session: Session, source: DataSource) -> schemas.SourceEvidence:
    since = utcnow() - LOOKBACK
    batches = session.scalars(
        select(Batch).where(Batch.data_source_id == source.id, Batch.received_at >= since)
    ).all()
    decided = [b for b in batches if b.status in ("accepted", "rejected")]
    delivered = sum(b.delivered_count for b in decided)
    accepted = sum(b.accepted_count or 0 for b in decided if b.status == "accepted")
    spend = sum((b.spend for b in batches), Decimal(0))

    first = min((b.received_at for b in batches), default=None)
    days = max(1.0, (utcnow() - first).total_seconds() / 86_400) if first else None

    allocations = session.scalars(
        select(Allocation)
        .where(Allocation.data_source_id == source.id)
        .order_by(Allocation.id.desc())
    ).all()
    open_commitments = sum(
        max(0, a.quantity - a.accepted_count) for a in allocations if a.status == "active"
    )
    last_quote = allocations[0] if allocations else None

    mix: dict[str, Counter[str]] = defaultdict(Counter)
    for b in decided:
        if b.status == "accepted":
            counts, _ = coverage.counts_for(b)
            for attr, values in counts.items():
                mix[attr].update(values)

    return schemas.SourceEvidence(
        batches_decided=len(decided),
        delivered=delivered,
        accepted=accepted,
        accept_rate=round(accepted / delivered, 4) if delivered else None,
        cost_per_usable_unit=(spend / accepted) if accepted else None,
        usable_per_day=round(accepted / days, 2) if days and accepted else None,
        open_commitments=open_commitments,
        last_quoted_rate=last_quote.quoted_unit_rate if last_quote else None,
        currency=last_quote.currency if last_quote else None,
        value_mix={
            attr: {v: round(n / sum(c.values()), 4) for v, n in sorted(c.items())}
            for attr, c in mix.items()
            if sum(c.values())
        },
    )


def _share_out(total: int, weights: dict[str, float], caps: dict[str, float]) -> dict[str, float]:
    """Split `total` by weight, never giving anyone more than their cap ("water-filling")."""
    given = {k: 0.0 for k in weights}
    open_ = {k for k in weights if caps[k] > 0}
    left = float(total)
    while left > 1e-9 and open_:
        weight_sum = sum(weights[k] for k in open_)
        round_left = left
        for k in list(open_):
            want = round_left * weights[k] / weight_sum
            take = min(want, caps[k] - given[k])
            given[k] += take
            left -= take
            if caps[k] - given[k] <= 1e-9:
                open_.discard(k)
        if abs(round_left - left) < 1e-9:
            break
    return given


def allocation_plan(session: Session, actor: Principal, request_id: str) -> schemas.AllocationPlan:
    req = request_service.get_request(session, actor, request_id)
    today = utcnow().date()
    allocated = sum(
        a.quantity for a in req.allocations if a.status != "cancelled" and a.unit == req.unit
    )
    remaining = max(0, req.quantity - allocated)
    days_left = (req.due_date - today).days if req.due_date else None

    cov = None
    if req.spec_version is not None:
        cov = coverage.compute(req.spec_version, [b for a in req.allocations for b in a.batches])
    gaps = cov.gaps if cov else []
    below = [
        (a.attribute, v.value)
        for a in (cov.attributes if cov else [])
        for v in a.values
        if v.status == "below"
    ]

    sources = session.scalars(
        select(DataSource).where(DataSource.project_id == req.project_id).order_by(DataSource.id)
    ).all()
    excluded: list[schemas.Excluded] = []
    proven: dict[str, tuple[DataSource, schemas.SourceEvidence]] = {}
    untested: dict[str, tuple[DataSource, schemas.SourceEvidence]] = {}
    for src in sources:
        reason = None
        if src.default_unit != req.unit:
            reason = f"Delivers {src.default_unit}, not {req.unit}."
        elif src.rights_expires_at and src.rights_expires_at < today:
            reason = f"Rights expired on {src.rights_expires_at}."
        elif src.rights_expires_at and req.due_date and src.rights_expires_at < req.due_date:
            reason = f"Rights expire {src.rights_expires_at}, before the due date {req.due_date}."
        if reason:
            excluded.append(schemas.Excluded(data_source_id=src.id, name=src.name, reason=reason))
            continue
        ev = _evidence(session, src)
        if ev.accepted and ev.cost_per_usable_unit is not None:
            proven[src.id] = (src, ev)
        else:
            untested[src.id] = (src, ev)

    pilot_total = int(remaining * PILOT_SHARE) if untested and remaining else 0
    pilot_each = pilot_total // len(untested) if untested else 0
    to_proven = remaining - pilot_each * len(untested)

    capacity: dict[str, float] = {}
    for sid, (_, ev) in proven.items():
        if days_left is None:
            capacity[sid] = math.inf
        else:
            rate = ev.usable_per_day or 0.0
            capacity[sid] = max(0.0, rate * max(days_left, 0) - ev.open_commitments)
    weights = {
        sid: 1.0 / max(float(ev.cost_per_usable_unit or 0), 1e-6) for sid, (_, ev) in proven.items()
    }
    shares = _share_out(to_proven, weights, capacity) if proven else {}
    covered = sum(shares.values()) + pilot_each * len(untested)
    shortfall = max(0, round(remaining - covered))

    suggestions: list[schemas.Suggestion] = []
    for sid, (src, ev) in proven.items():
        usable = round(shares.get(sid, 0.0))
        if usable <= 0:
            continue
        rate = max(ev.accept_rate or 1.0, MIN_ACCEPT_RATE)
        order = math.ceil(usable / rate)
        notes = []
        if ev.accept_rate and ev.accept_rate < 1:
            notes.append(
                f"Orders {order - usable:,} extra to cover its {1 - ev.accept_rate:.0%} rejects."
            )
        if days_left is not None and usable >= capacity[sid] - 0.5:
            notes.append("Capped at what it can likely deliver by the due date.")
        suggestions.append(
            _suggestion(
                src, ev, "proven", usable, order, remaining, capacity.get(sid), req, below, notes
            )
        )
    for src, ev in untested.values():
        if pilot_each <= 0:
            continue
        pilot_note = ["No delivery history yet: a small pilot to build a track record."]
        suggestions.append(
            _suggestion(
                src, ev, "pilot", pilot_each, pilot_each, remaining, None, req, below, pilot_note
            )
        )

    return schemas.AllocationPlan(
        request_id=req.id,
        unit=req.unit,
        requested=req.quantity,
        already_allocated=allocated,
        remaining=remaining,
        due_date=req.due_date,
        suggestions=suggestions,
        excluded=excluded,
        shortfall=shortfall,
        coverage_gaps=gaps,
        method=(
            "Untested sources share a pilot of up to 10% of the remaining units. Proven sources "
            "share the rest in proportion to 1 / cost per usable unit (last 90 days), each "
            "capped by its throughput until the due date minus what it already owes. Order "
            "quantities add extra for expected rejects."
        ),
        generated_at=utcnow(),
    )


def _suggestion(
    src: DataSource,
    ev: schemas.SourceEvidence,
    role: str,
    usable: int,
    order: int,
    remaining: int,
    cap: float | None,
    req: Any,
    below: list[tuple[str, str]],
    first_notes: list[str],
) -> schemas.Suggestion:
    rate = ev.last_quoted_rate
    cost = (
        (rate * order)
        if rate is not None
        else (ev.cost_per_usable_unit * usable if ev.cost_per_usable_unit is not None else None)
    )
    notes = list(first_notes)
    for attr, value in below:
        share = ev.value_mix.get(attr, {}).get(value)
        if share:
            notes.append(f"Delivers {share:.0%} {attr}={value}, which the request is short of.")
    allocation: dict[str, Any] = {
        "request_id": req.id,
        "data_source_id": src.id,
        "quantity": order,
        "unit": req.unit,
        "quoted_unit_rate": str(rate) if rate is not None else "0",
        "currency": ev.currency or "USD",
    }
    if req.due_date:
        allocation["due_date"] = req.due_date.isoformat()
    if rate is None:
        notes.append("No quote on record: set quoted_unit_rate before creating the allocation.")
    return schemas.Suggestion(
        data_source_id=src.id,
        name=src.name,
        kind=src.kind,
        role=role,
        share=round(usable / remaining, 4) if remaining else 0.0,
        expected_usable=usable,
        order_quantity=order,
        expected_cost=cost,
        currency=ev.currency,
        capacity_by_due_date=None if cap is None or math.isinf(cap) else int(cap),
        evidence=ev,
        notes=notes,
        allocation=allocation,
    )


# --- diagnosis -------------------------------------------------------------------------------


def diagnose(session: Session, actor: Principal, capability_id: str) -> schemas.Diagnosis:
    cap = capabilities.get_capability(session, actor, capability_id)
    versions = session.scalars(
        select(DatasetVersion)
        .join(Dataset, Dataset.id == DatasetVersion.dataset_id)
        .where(Dataset.capability_id == cap.id)
        .order_by(DatasetVersion.created_at, DatasetVersion.id)
    ).all()

    scored: list[tuple[DatasetVersion, schemas.ScoredVersion]] = []
    for v in versions:
        s = portfolio.score(v, cap)
        if s is None:
            continue
        spend: dict[str, Decimal] = defaultdict(Decimal)
        for b in v.new_batches():
            spend[b.currency] += b.spend
        positive = [c for c, amount in spend.items() if amount > 0]
        ppk = (
            round(s.points / float(spend[positive[0]]) * 10_000, 4) if len(positive) == 1 else None
        )
        scored.append(
            (
                v,
                schemas.ScoredVersion(
                    dataset_version_id=v.id,
                    dataset_id=v.dataset_id,
                    version=v.version,
                    created_at=v.created_at,
                    eval_value=s.current.value,
                    baseline_eval_value=s.baseline.value,
                    points=round(s.points, 4),
                    spend=[{"currency": c, "amount": str(a)} for c, a in sorted(spend.items())],
                    points_per_10k=ppk,
                ),
            )
        )

    with_ppk = [sv.points_per_10k for _, sv in scored if sv.points_per_10k is not None]
    trend, ratio = "not_enough_data", None
    if len(with_ppk) >= 2:
        earlier = sum(with_ppk[:-1]) / len(with_ppk[:-1])
        ratio = round(with_ppk[-1] / earlier, 4) if earlier > 0 else None
        flattening = ratio is not None and ratio < cap.flattening_threshold
        trend = "flattening" if flattening or earlier <= 0 else "improving"

    checks = [
        schemas.CauseCheck(cause=c, status="not_checked", summary=f"{label} isn't checked yet.")
        for c, label in (
            ("label_quality", "Label quality"),
            ("eval", "Whether the eval itself is the problem"),
            ("model", "A model bottleneck"),
            ("saturation", "True saturation"),
        )
    ]
    cov, change = None, None
    recommendation, summary = (
        "not_enough_data",
        (
            "Need at least two dataset versions with eval results (and their baselines) and spend "
            "to see a trend."
        ),
    )

    if trend == "improving":
        recommendation = "keep_going"
        summary = (
            f"Returns are holding up: the latest version gained {with_ppk[-1]} points per 10K "
            f"({ratio:.0%} of the earlier average). Keep going."
            if ratio is not None
            else "Returns are holding up. Keep going."
        )
        checks.insert(
            0,
            schemas.CauseCheck(
                cause="data_mix",
                status="not_applicable",
                summary="Not needed: returns aren't flattening.",
            ),
        )
    elif trend == "flattening":
        latest = scored[-1][0]
        cov, change = _data_mix(latest)
        if cov is not None and cov.gaps:
            recommendation = "refine_spec"
            summary = (
                f"Returns are flattening ({with_ppk[-1]} points per 10K, "
                f"{ratio:.0%} of the earlier average). The data mix is off: "
                + "; ".join(cov.gaps)
                + ". Refine the spec's coverage targets before cutting budget."
            )
            checks.insert(
                0, schemas.CauseCheck(cause="data_mix", status="found", summary="; ".join(cov.gaps))
            )
        else:
            recommendation = "investigate"
            change = None
            summary = (
                f"Returns are flattening ({ratio:.0%} of the earlier average) but the data mix "
                "matches the spec's targets. Check label quality, the eval and the model before "
                "cutting spend."
                if ratio is not None
                else "Returns are flattening but the data mix matches the spec's targets."
            )
            checks.insert(
                0,
                schemas.CauseCheck(
                    cause="data_mix",
                    status="ok" if cov is not None else "not_applicable",
                    summary="Coverage matches the targets."
                    if cov is not None
                    else "The latest version's spec has no coverage targets to compare with.",
                ),
            )

    return schemas.Diagnosis(
        capability_id=cap.id,
        eval_metric=cap.eval_metric,
        flattening_threshold=cap.flattening_threshold,
        versions=[sv for _, sv in scored],
        trend=trend,
        latest_vs_earlier=ratio,
        checks=checks,
        recommendation=recommendation,
        summary=summary,
        coverage=cov,
        suggested_spec_change=change,
        generated_at=utcnow(),
    )


def _data_mix(
    version: DatasetVersion,
) -> tuple[Any, schemas.SuggestedSpecChange | None]:
    """Coverage of the version's batches against their (most used) spec version's targets."""
    by_spec = Counter(b.spec_version_id for b in version.batches)
    if not by_spec:
        return None, None
    spec_version = next(
        b.spec_version for b in version.batches if b.spec_version_id == by_spec.most_common(1)[0][0]
    )
    if not spec_version.coverage_targets:
        return None, None
    cov = coverage.compute(spec_version, version.batches)
    if not cov.gaps:
        return cov, None

    targets = {attr: dict(values) for attr, values in spec_version.coverage_targets.items()}
    for attr in cov.attributes:
        current = targets.get(attr.attribute)
        if not current:
            continue
        total = sum(current.values())
        raised = dict(current)
        for v in attr.values:
            if v.status == "below" and v.target_share is not None and v.actual_share is not None:
                # Aim past the target by the shortfall, so future collection catches up.
                raised[v.value] = min(1.0, v.target_share + (v.target_share - v.actual_share))
        scale = total / sum(raised.values())
        rounded = {k: round(x * scale, 2) for k, x in raised.items()}
        excess = round(sum(rounded.values()) - total, 2)
        if excess > 0:  # rounding pushed it over: take it off the largest value not raised
            unraised = [k for k in rounded if raised[k] == current[k]] or list(rounded)
            biggest = max(unraised, key=lambda k: rounded[k])
            rounded[biggest] = round(rounded[biggest] - excess, 2)
        targets[attr.attribute] = rounded
    return cov, schemas.SuggestedSpecChange(
        spec_id=spec_version.spec_id,
        from_spec_version=spec_version.version,
        coverage_targets=targets,
        change_note=(
            "Drafted by Data Control Plane from the diagnosis: returns are flattening and the "
            "data mix is off (" + "; ".join(cov.gaps) + "). Raises targets for the short values."
        ),
    )


def draft_spec(session: Session, actor: Principal, capability_id: str) -> Any:
    """Create the suggested spec change as a draft version, for a person to review."""
    actor.require_write()
    diagnosis = diagnose(session, actor, capability_id)
    change = diagnosis.suggested_spec_change
    if diagnosis.recommendation != "refine_spec" or change is None:
        raise Conflict(
            f"The diagnosis doesn't recommend refining the spec ({diagnosis.recommendation})."
        )
    return specs.create_version(
        session,
        actor,
        change.spec_id,
        spec_schemas.SpecVersionUpdate(
            coverage_targets=change.coverage_targets, change_note=change.change_note
        ),
    )
