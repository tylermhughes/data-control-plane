"""Allocations: part of a request given to one source, with a quoted rate and due date.

Lifecycle: planned -> active -> complete, or cancelled from planned/active. Activating needs
the request to be open. Planned allocations can change freely; active ones only in quantity,
due date and notes (the quoted rate, currency and unit are the commitment cost reports use).
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid
from app.ids import new_id
from app.models import Allocation, DataSource, Request
from app.models.base import utcnow
from app.schemas import requests as schemas
from app.services import events, scoped
from app.services.principal import Principal

LABEL = "allocation"
EDITABLE_WHEN_ACTIVE = frozenset({"quantity", "due_date", "notes"})


def _emit(session: Session, type: str, alloc: Allocation, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.Allocation.model_validate(alloc),
        subject_id=alloc.id,
        project_id=alloc.project_id,
        actor=actor,
    )


def list_allocations(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    request_id: str | None,
    data_source_id: str | None,
    status: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Allocation], str | None]:
    where = []
    if request_id:
        where.append(Allocation.request_id == request_id)
    if data_source_id:
        where.append(Allocation.data_source_id == data_source_id)
    if status:
        where.append(Allocation.status == status)
    return scoped.list_scoped(
        session, actor, Allocation, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_allocation(session: Session, actor: Principal, alloc_id: str) -> Allocation:
    return scoped.get_scoped(session, actor, Allocation, alloc_id, LABEL)


def create_allocation(
    session: Session, actor: Principal, body: schemas.AllocationCreate
) -> Allocation:
    actor.require_write()
    req = session.get(Request, body.request_id)
    if req is None or not actor.can_see_project(req.project_id):
        raise Invalid(f"No request with id '{body.request_id}'.")
    if req.status not in ("draft", "open"):
        raise Conflict(f"This request is {req.status}; it can't get new allocations.")
    if req.spec_version is None or req.spec_version.status != "approved":
        raise Conflict("The request needs an approved spec version before work can be allocated.")
    source = session.get(DataSource, body.data_source_id)
    if source is None or source.project_id != req.project_id:
        raise Invalid(f"No data source with id '{body.data_source_id}' in this project.")
    alloc = Allocation(
        id=new_id("alc"),
        project_id=req.project_id,
        spec_version_id=req.spec_version.id,
        **body.model_dump(exclude={"unit"}),
        unit=body.unit or source.default_unit,
        status="planned",
    )
    session.add(alloc)
    session.flush()
    _emit(session, "allocation.created", alloc, actor)
    return alloc


def update_allocation(
    session: Session, actor: Principal, alloc_id: str, body: schemas.AllocationUpdate
) -> Allocation:
    alloc = get_allocation(session, actor, alloc_id)
    actor.require_write()
    changes = body.model_dump(exclude_unset=True)
    # due_date may be cleared with null; other fields ignore null.
    changes = {k: v for k, v in changes.items() if v is not None or k == "due_date"}
    if alloc.status in ("complete", "cancelled"):
        raise Conflict(f"This allocation is {alloc.status} and can't change.")
    if alloc.status == "active":
        frozen = sorted(set(changes) - EDITABLE_WHEN_ACTIVE)
        if frozen:
            raise Conflict(
                f"This allocation is active, so {', '.join(frozen)} can't change. "
                "Only quantity, due_date and notes can."
            )
    scoped.apply_changes(alloc, changes)
    session.flush()
    _emit(session, "allocation.updated", alloc, actor)
    return alloc


def activate_allocation(session: Session, actor: Principal, alloc_id: str) -> Allocation:
    alloc = get_allocation(session, actor, alloc_id)
    actor.require_write()
    if alloc.status != "planned":
        raise Conflict(f"Only planned allocations can be activated; this one is {alloc.status}.")
    if alloc.request.status != "open":
        raise Conflict(f"Open the request first (it is {alloc.request.status}).")
    alloc.status, alloc.activated_at = "active", utcnow()
    session.flush()
    _emit(session, "allocation.activated", alloc, actor)
    return alloc


def complete_allocation(session: Session, actor: Principal, alloc_id: str) -> Allocation:
    alloc = get_allocation(session, actor, alloc_id)
    actor.require_write()
    if alloc.status != "active":
        raise Conflict(f"Only active allocations can be completed; this one is {alloc.status}.")
    alloc.status, alloc.completed_at = "complete", utcnow()
    session.flush()
    _emit(session, "allocation.completed", alloc, actor)
    return alloc


def cancel_allocation(session: Session, actor: Principal, alloc_id: str) -> Allocation:
    alloc = get_allocation(session, actor, alloc_id)
    actor.require_write()
    if alloc.status not in ("planned", "active"):
        raise Conflict(f"This allocation is already {alloc.status}.")
    mark_cancelled(session, alloc, actor)
    return alloc


def mark_cancelled(session: Session, alloc: Allocation, actor: Principal) -> None:
    """Cancel without permission checks (callers have done them). Also used by requests."""
    alloc.status, alloc.cancelled_at = "cancelled", utcnow()
    session.flush()
    _emit(session, "allocation.cancelled", alloc, actor)


def delete_allocation(session: Session, actor: Principal, alloc_id: str) -> None:
    alloc = get_allocation(session, actor, alloc_id)
    actor.require_write()
    if alloc.status != "planned":
        raise Conflict("Only planned allocations can be deleted; cancel this one instead.")
    _emit(session, "allocation.deleted", alloc, actor)
    session.delete(alloc)
    session.flush()
