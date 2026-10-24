"""The portfolio report: which data spend actually improved the models.

Per capability and per source type:
- spend, usable (accepted) units and cost per usable unit, from batches received in the period
  (all spend counts, so rework and rejects show up as a higher unit cost);
- eval change: for each dataset version created in the period that has a main-metric result
  and a baseline with one too, (version − baseline) in points, positive when better;
- the spend that bought it: what each scored version's new batches (vs its baseline) cost;
- points per 10K of that spend, and for capabilities value (points × value per point) and ROI.
Source-type eval change is an estimate: each version's change is split by each type's share of
the accepted items the version added.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Batch, Capability, DatasetVersion, DataSource, EvalResult
from app.models.base import utcnow
from app.schemas import portfolio as schemas
from app.services.principal import Principal

ATTRIBUTION_METHOD = "accepted_units_share"


@dataclass
class _Tally:
    """Running totals for one row."""

    spend: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    units: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    unit_spend: dict[tuple[str, str], Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    unit_accepted: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    batch_count: int = 0
    change: float | None = None
    scored_versions: set[str] = field(default_factory=set)
    scored_spend: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    eval_ids: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    def add_batch(self, b: Batch) -> None:
        unit = b.allocation.unit
        self.batch_count += 1
        self.spend[b.currency] += b.spend
        self.unit_spend[(unit, b.currency)] += b.spend
        if b.status == "accepted":
            self.units[unit] += b.accepted_count or 0
            self.unit_accepted[(unit, b.currency)] += b.accepted_count or 0

    def add_change(self, points: float, version_id: str, eval_ids: Iterable[str]) -> None:
        self.change = (self.change or 0.0) + points
        self.scored_versions.add(version_id)
        self.eval_ids.update(eval_ids)

    def row_fields(self) -> dict[str, object]:
        points_per_10k = None
        currencies = [c for c, amount in self.scored_spend.items() if amount > 0]
        if self.change is not None:
            if len(currencies) == 1:
                points_per_10k = round(
                    self.change / float(self.scored_spend[currencies[0]]) * 10_000, 4
                )
            elif len(currencies) > 1:
                self.notes.append("Scored spend is in several currencies; points per 10K skipped.")
            else:
                self.notes.append("The scored versions added no spend; points per 10K skipped.")
        return {
            "spend": _amounts(self.spend),
            "usable_units": [
                schemas.UnitCount(unit=u, count=n) for u, n in sorted(self.units.items())
            ],
            "cost_per_usable_unit": [
                schemas.UnitCost(unit=u, currency=c, amount=s / self.unit_accepted[(u, c)])
                for (u, c), s in sorted(self.unit_spend.items())
                if self.unit_accepted[(u, c)]
            ],
            "eval_change_points": round(self.change, 4) if self.change is not None else None,
            "scored_versions": len(self.scored_versions),
            "spend_on_scored_versions": _amounts(self.scored_spend),
            "points_per_10k": points_per_10k,
            "sources": schemas.Sources(
                dataset_version_ids=sorted(self.scored_versions),
                eval_result_ids=sorted(self.eval_ids),
                batch_count=self.batch_count,
            ),
            "notes": self.notes,
        }


def _amounts(by_currency: dict[str, Decimal]) -> list[schemas.Amount]:
    return [schemas.Amount(currency=c, amount=a) for c, a in sorted(by_currency.items())]


def _main_result(version: DatasetVersion, metric: str) -> EvalResult | None:
    results = [r for r in version.eval_results if r.metric == metric]
    return max(results, key=lambda r: (r.recorded_at, r.id)) if results else None


@dataclass(frozen=True)
class Score:
    """A dataset version's eval change against its baseline, in points (positive = better)."""

    points: float
    current: EvalResult
    baseline: EvalResult


def score(version: DatasetVersion, cap: Capability) -> Score | None:
    """None unless both the version and its baseline have a main-metric result."""
    current = _main_result(version, cap.eval_metric)
    base = _main_result(version.baseline, cap.eval_metric) if version.baseline else None
    if current is None or base is None:
        return None
    sign = 1.0 if current.higher_is_better else -1.0
    return Score(sign * (current.value - base.value) / cap.point_size, current, base)


def _in_window(when: datetime, since: datetime | None, until: datetime | None) -> bool:
    return (since is None or when >= since) and (until is None or when < until)


def build(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    since: datetime | None,
    until: datetime | None,
) -> schemas.Portfolio:
    def scoped[M: (Capability, Batch, DatasetVersion, DataSource)](model: type[M]) -> list[M]:
        stmt = select(model)
        if not actor.is_admin:
            stmt = stmt.where(model.project_id == actor.project_id)
        if project_id:
            stmt = stmt.where(model.project_id == project_id)
        return list(session.scalars(stmt.order_by(model.id)))

    capabilities = scoped(Capability)
    kinds = {s.id: s.kind for s in scoped(DataSource)}
    by_cap = {c.id: _Tally() for c in capabilities}
    by_kind: dict[str, _Tally] = defaultdict(_Tally)

    for b in scoped(Batch):
        if _in_window(b.received_at, since, until):
            by_cap[b.allocation.request.capability_id].add_batch(b)
            by_kind[kinds[b.data_source_id]].add_batch(b)

    caps = {c.id: c for c in capabilities}
    for version in scoped(DatasetVersion):
        if not _in_window(version.created_at, since, until):
            continue
        cap = caps[version.capability_id]
        scored = score(version, cap)
        if scored is None:
            continue
        points = scored.points
        added = version.new_batches()
        eval_ids = (scored.current.id, scored.baseline.id)

        cap_tally = by_cap[cap.id]
        cap_tally.add_change(points, version.id, eval_ids)
        for b in added:
            cap_tally.scored_spend[b.currency] += b.spend

        added_accepted = sum(b.accepted_count or 0 for b in added)
        for b in added:
            tally = by_kind[kinds[b.data_source_id]]
            share = (b.accepted_count or 0) / added_accepted if added_accepted else 0.0
            tally.add_change(points * share, version.id, eval_ids)
            tally.scored_spend[b.currency] += b.spend

    cap_rows = []
    for cap in capabilities:
        tally = by_cap[cap.id]
        fields = tally.row_fields()
        value = roi = None
        if tally.change is None:
            tally.notes.append(
                f"No dataset version has a '{cap.eval_metric}' result and a baseline with one "
                "to compare against."
            )
        else:
            value = Decimal(str(round(tally.change, 6))) * cap.value_per_point
            spent = tally.scored_spend.get(cap.currency, Decimal(0))
            if spent > 0 and set(tally.scored_spend) == {cap.currency}:
                roi = round(float(value / spent), 2)
            else:
                tally.notes.append(
                    f"ROI needs scored spend in the capability's currency ({cap.currency})."
                )
        cap_rows.append(
            schemas.CapabilityRow(
                capability_id=cap.id,
                name=cap.name,
                eval_metric=cap.eval_metric,
                point_size=cap.point_size,
                value_per_point=cap.value_per_point,
                currency=cap.currency,
                value=value,
                roi=roi,
                **fields,
            )
        )

    kind_rows = [
        schemas.SourceKindRow(
            kind=kind,
            is_estimate=True,
            attribution_method=ATTRIBUTION_METHOD,
            **tally.row_fields(),
        )
        for kind, tally in sorted(by_kind.items())
    ]
    return schemas.Portfolio(
        project_id=project_id,
        since=since,
        until=until,
        generated_at=utcnow(),
        by_capability=cap_rows,
        by_source_kind=kind_rows,
    )
