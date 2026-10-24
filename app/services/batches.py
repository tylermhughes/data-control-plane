"""Batches: deliveries against an allocation.

- New batches need an active allocation, and spend in the allocation's currency.
- Decisions made in DCP (accept/reject) are final: afterwards only notes can change.
- Batches decided outside DCP (vendor QA, Labelbox, ...) follow that system: importing the
  same external_ref again updates the batch and records what changed (`batch.reimported`).
  Identical re-imports change nothing.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid
from app.ids import new_id
from app.models import Allocation, Batch, SpecVersion
from app.models.base import utcnow
from app.models.batch import UNDECIDED
from app.schemas import batches as schemas
from app.services import events, quality, scoped
from app.services.principal import Principal

LABEL = "batch"
# Fields compared on re-import; updated_at always changes, so it's left out.
_TRACKED = tuple(f for f in schemas.Batch.model_fields if f != "updated_at")


def _emit(
    session: Session,
    type: str,
    batch: Batch,
    actor: Principal,
    extra: dict[str, Any] | None = None,
) -> None:
    events.emit(
        session,
        type,
        schemas.Batch.model_validate(batch),
        subject_id=batch.id,
        project_id=batch.project_id,
        actor=actor,
        extra=extra,
    )


def _snapshot(batch: Batch) -> dict[str, Any]:
    return schemas.Batch.model_validate(batch).model_dump(mode="json", include=set(_TRACKED))


def check_counts(
    version: SpecVersion,
    delivered: int,
    accepted: int | None,
    attribute_counts: dict[str, dict[str, int]] | None,
) -> None:
    """Accepted can't exceed delivered; attribute counts must use the spec's attributes and
    can't add up to more than the accepted count for any attribute."""
    if accepted is not None and accepted > delivered:
        raise Invalid(f"accepted_count ({accepted}) is more than delivered_count ({delivered}).")
    allowed = {a["name"]: set(a["values"]) for a in version.attributes}
    for attr, counts in (attribute_counts or {}).items():
        if attr not in allowed:
            raise Invalid(f"Attribute '{attr}' isn't in spec version {version.version}.")
        for value, count in counts.items():
            if value not in allowed[attr]:
                raise Invalid(f"'{value}' isn't an allowed value of '{attr}'.")
            if count < 0:
                raise Invalid(f"Count for {attr}={value} can't be negative.")
        if sum(counts.values()) > (accepted or 0):
            raise Invalid(
                f"Counts for '{attr}' add up to {sum(counts.values())}, "
                f"more than the {accepted or 0} accepted items."
            )


# --- reading ---------------------------------------------------------------------------------


def list_batches(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    request_id: str | None,
    allocation_id: str | None,
    data_source_id: str | None,
    status: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Batch], str | None]:
    where: list[ColumnElement[bool]] = []
    if request_id:
        where.append(
            Batch.allocation_id.in_(
                select(Allocation.id).where(Allocation.request_id == request_id)
            )
        )
    if allocation_id:
        where.append(Batch.allocation_id == allocation_id)
    if data_source_id:
        where.append(Batch.data_source_id == data_source_id)
    if status:
        where.append(Batch.status == status)
    return scoped.list_scoped(
        session, actor, Batch, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_batch(session: Session, actor: Principal, batch_id: str) -> Batch:
    return scoped.get_scoped(session, actor, Batch, batch_id, LABEL)


# --- creating and importing ------------------------------------------------------------------


def create_batch(
    session: Session, actor: Principal, body: schemas.BatchCreate
) -> tuple[Batch, bool]:
    """Register a delivery, or import one decided elsewhere. Returns (batch, created).

    With an external_ref that the source already used, the existing batch is updated instead.
    """
    actor.require_write()
    alloc = session.get(Allocation, body.allocation_id)
    if alloc is None or not actor.can_see_project(alloc.project_id):
        raise Invalid(f"No allocation with id '{body.allocation_id}'.")
    currency = body.currency or alloc.currency
    if currency != alloc.currency:
        raise Invalid(
            f"Spend must be in the allocation's currency ({alloc.currency}), not {currency}."
        )

    if body.external_ref:
        existing = session.scalar(
            select(Batch).where(
                Batch.data_source_id == alloc.data_source_id,
                Batch.external_ref == body.external_ref,
            )
        )
        if existing is not None:
            return _reimport(session, actor, existing, alloc, body), False

    if alloc.status != "active":
        raise Conflict(
            f"Batches can only be added to active allocations; this one is {alloc.status}."
        )
    decision = body.decision
    check_counts(
        alloc.spec_version,
        body.delivered_count,
        decision.accepted_count if decision else None,
        decision.attribute_counts if decision else None,
    )
    batch = Batch(
        id=new_id("bat"),
        project_id=alloc.project_id,
        allocation=alloc,
        data_source_id=alloc.data_source_id,
        spec_version_id=alloc.spec_version_id,
        received_at=body.received_at or utcnow(),
        status="received",
        delivered_count=body.delivered_count,
        contributor_count=body.contributor_count,
        spend=body.spend,
        currency=currency,
        artifacts=[a.model_dump(mode="json") for a in body.artifacts],
        reported_metrics=body.reported_metrics,
        notes=body.notes,
        external_ref=body.external_ref,
        external_url=body.external_url,
    )
    session.add(batch)
    session.flush()
    _emit(session, "batch.received", batch, actor)
    if decision:
        _apply_external_decision(batch, decision)
        session.flush()
        _emit(session, f"batch.{batch.status}", batch, actor)
    if batch.artifacts:
        quality.queue_checks(session, batch, trigger="auto")
    return batch, True


def _apply_external_decision(batch: Batch, decision: schemas.ExternalDecision) -> None:
    batch.status = decision.status
    batch.decision_source = "external"
    batch.decided_by = decision.decided_by
    batch.decided_by_key_id = None
    batch.decided_at = decision.decided_at or batch.decided_at or utcnow()
    if decision.status == "accepted":
        batch.accepted_count = decision.accepted_count
        batch.attribute_counts = decision.attribute_counts or {}
        batch.rejection_reason = None
    else:
        batch.accepted_count = 0
        batch.attribute_counts = {}
        batch.rejection_reason = decision.reason


def _reimport(
    session: Session,
    actor: Principal,
    batch: Batch,
    alloc: Allocation,
    body: schemas.BatchCreate,
) -> Batch:
    if batch.allocation_id != alloc.id:
        raise Conflict(
            f"external_ref '{body.external_ref}' already belongs to batch {batch.id} "
            f"on allocation {batch.allocation_id}."
        )
    if batch.decision_source == "dcp":
        raise Conflict(f"Batch {batch.id} was {batch.status} in DCP, so an import can't change it.")
    before = _snapshot(batch)

    batch.delivered_count = body.delivered_count
    batch.spend = body.spend
    batch.contributor_count = body.contributor_count
    batch.artifacts = [a.model_dump(mode="json") for a in body.artifacts]
    batch.reported_metrics = body.reported_metrics
    batch.notes = body.notes
    batch.external_url = body.external_url
    if body.received_at:
        batch.received_at = body.received_at
    if body.decision:  # without one, an earlier external decision is kept
        if batch.decision_source is None and alloc.status != "active":
            raise Conflict("Decisions can only be added while the allocation is active.")
        _apply_external_decision(batch, body.decision)
    check_counts(
        batch.spec_version, batch.delivered_count, batch.accepted_count, batch.attribute_counts
    )

    after = _snapshot(batch)
    changes = {k: [before[k], after[k]] for k in after if before[k] != after[k]}
    if not changes:
        session.expire(batch)  # identical re-import: nothing changes, no event
        return batch
    session.flush()
    _emit(session, "batch.reimported", batch, actor, extra={"changes": changes})
    if "artifacts" in changes and batch.artifacts and batch.status != "checking":
        quality.queue_checks(session, batch, trigger="auto")
    return batch


# --- changing --------------------------------------------------------------------------------


def update_batch(
    session: Session, actor: Principal, batch_id: str, body: schemas.BatchUpdate
) -> Batch:
    batch = get_batch(session, actor, batch_id)
    actor.require_write()
    changes = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if batch.status == "checking":
        raise Conflict("Checks are running on this batch. Try again when they finish.")
    if batch.status not in UNDECIDED:
        frozen = sorted(set(changes) - {"notes"})
        if frozen:
            raise Conflict(
                f"This batch is {batch.status}, so only notes can change (not {', '.join(frozen)})."
            )
    files_changed = "artifacts" in changes
    if files_changed:
        changes["artifacts"] = [a.model_dump(mode="json") for a in body.artifacts or []]
    scoped.apply_changes(batch, changes)
    session.flush()
    _emit(session, "batch.updated", batch, actor)
    if files_changed and batch.artifacts:
        quality.queue_checks(session, batch, trigger="auto")
    return batch


def accept_batch(
    session: Session, actor: Principal, batch_id: str, body: schemas.BatchAccept
) -> Batch:
    batch = _undecided(session, actor, batch_id)
    if batch.status == "failed" and not body.override_reason:
        raise Conflict(
            "This batch failed its checks. To accept it anyway, give an override_reason."
        )
    check_counts(
        batch.spec_version, batch.delivered_count, body.accepted_count, body.attribute_counts
    )
    batch.override_reason = body.override_reason if batch.status == "failed" else None
    batch.status = "accepted"
    batch.accepted_count = body.accepted_count
    batch.attribute_counts = body.attribute_counts or {}
    _decided_here(batch, actor, body.decided_by)
    session.flush()
    _emit(session, "batch.accepted", batch, actor)
    return batch


def reject_batch(
    session: Session, actor: Principal, batch_id: str, body: schemas.BatchReject
) -> Batch:
    batch = _undecided(session, actor, batch_id)
    batch.status = "rejected"
    batch.accepted_count = 0
    batch.rejection_reason = body.reason
    _decided_here(batch, actor, body.decided_by)
    session.flush()
    _emit(session, "batch.rejected", batch, actor)
    return batch


def delete_batch(session: Session, actor: Principal, batch_id: str) -> None:
    batch = get_batch(session, actor, batch_id)
    actor.require_write()
    if batch.status not in UNDECIDED:
        raise Conflict(f"This batch is {batch.status}; only undecided batches can be deleted.")
    _emit(session, "batch.deleted", batch, actor)
    session.delete(batch)
    session.flush()


def _undecided(session: Session, actor: Principal, batch_id: str) -> Batch:
    batch = get_batch(session, actor, batch_id)
    actor.require_write()
    if batch.status == "checking":
        raise Conflict("Checks are still running on this batch. Decide when they finish.")
    if batch.status not in UNDECIDED:
        raise Conflict(f"This batch is already {batch.status}.")
    return batch


def _decided_here(batch: Batch, actor: Principal, decided_by: str) -> None:
    batch.decision_source = "dcp"
    batch.decided_by = decided_by or None
    batch.decided_by_key_id = actor.key_id
    batch.decided_at = utcnow()
