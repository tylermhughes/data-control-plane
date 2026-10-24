"""Coverage vs targets: does the accepted data have the mix the spec asks for?

Shares are computed from the attribute counts recorded on accepted batches, among the items
counted for each attribute (counts are optional, so the report says how many were counted).
A value is `below` when its share is more than the spec version's tolerance under target.
Counts taken from the files by a quality run are used when there are any; otherwise the counts
the source reported. `counts_from` says which, per batch.
"""

from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.errors import Conflict
from app.models import Batch, SpecVersion
from app.schemas import datasets as schemas
from app.services import batches as batch_service
from app.services import quality
from app.services import requests as request_service
from app.services.principal import Principal

EPSILON = 1e-9


def counts_for(batch: Batch) -> tuple[dict[str, dict[str, int]], str]:
    run = quality.latest_finished(batch)
    if run is not None and run.attribute_counts:
        return run.attribute_counts, "files"
    if batch.attribute_counts:
        return batch.attribute_counts, "reported"
    return {}, "none"


def compute(
    version: SpecVersion, batches: Iterable[Batch], *, include_undecided: bool = False
) -> schemas.Coverage:
    accepted = [b for b in batches if b.status == "accepted" or include_undecided]
    sources = {b.id: counts_for(b) for b in accepted}
    accepted_count = sum(b.accepted_count or 0 for b in accepted)
    tolerance = version.coverage_tolerance
    attributes, gaps = [], []

    for attr in version.attributes:
        name = attr["name"]
        counts: dict[str, int] = defaultdict(int)
        for b in accepted:
            for value, count in sources[b.id][0].get(name, {}).items():
                counts[value] += count
        counted = sum(counts.values())
        targets = version.coverage_targets.get(name, {})
        ordered = list(attr["values"]) + sorted(set(counts) - set(attr["values"]))

        values = []
        for value in ordered:
            count = counts.get(value, 0)
            target = targets.get(value)
            actual = count / counted if counted else None
            if target is None:
                status, gap = "no_target", None
            elif actual is None:
                status, gap = "no_data", None
            else:
                gap = round(actual - target, 4)
                status = "below" if actual < target - tolerance - EPSILON else "ok"
            if status == "below":
                gaps.append(f"{name}={value}: {actual:.0%} vs {target:.0%} target")
            values.append(
                schemas.CoverageValue(
                    value=value,
                    count=count,
                    actual_share=round(actual, 4) if actual is not None else None,
                    target_share=target,
                    gap=gap,
                    status=status,
                )
            )
        attributes.append(
            schemas.CoverageAttribute(
                attribute=name,
                counted=counted,
                counted_share_of_accepted=round(counted / accepted_count, 4)
                if accepted_count
                else None,
                values=values,
            )
        )

    return schemas.Coverage(
        spec_version_id=version.id,
        tolerance=tolerance,
        accepted_count=accepted_count,
        batch_ids=[b.id for b in accepted],
        counts_from={batch_id: source for batch_id, (_, source) in sources.items()},
        attributes=attributes,
        gaps=gaps,
    )


def for_batch(session: Session, actor: Principal, batch_id: str) -> schemas.Coverage:
    batch = batch_service.get_batch(session, actor, batch_id)
    return compute(batch.spec_version, [batch], include_undecided=True)


def for_request(session: Session, actor: Principal, request_id: str) -> schemas.Coverage:
    """All accepted batches of the request, against its current spec version's targets."""
    req = request_service.get_request(session, actor, request_id)
    if req.spec_version is None:
        raise Conflict("This request has no spec version, so there are no targets to compare.")
    batches = [b for alloc in req.allocations for b in alloc.batches]
    return compute(req.spec_version, batches)
