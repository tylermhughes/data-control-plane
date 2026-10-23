"""Requests: an ask for data to improve one capability.

Lifecycle: draft -> open -> closed, or cancelled from draft/open. Opening needs an approved
spec version. Closing cancels allocations that never started and is refused while any are
active. Cancelling also cancels planned and active allocations.
"""

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid
from app.ids import new_id
from app.models import Capability, Request, SpecVersion
from app.models.base import utcnow
from app.schemas import requests as schemas
from app.services import allocations, events, scoped
from app.services.principal import Principal

LABEL = "request"


def to_schema(req: Request) -> schemas.Request:
    totals: dict[tuple[str, str], list[Decimal]] = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for alloc in req.allocations:
        if alloc.status != "cancelled":
            total = totals[(alloc.unit, alloc.currency)]
            total[0] += alloc.quantity
            total[1] += alloc.quoted_cost
    version = req.spec_version
    return schemas.Request(
        id=req.id,
        project_id=req.project_id,
        capability_id=req.capability_id,
        title=req.title,
        requested_by=req.requested_by,
        priority=req.priority,
        rationale=req.rationale,
        target_metric=req.target_metric,
        quantity=req.quantity,
        unit=req.unit,
        due_date=req.due_date,
        spec_version_id=req.spec_version_id,
        spec_id=version.spec_id if version else None,
        spec_version=version.version if version else None,
        status=req.status,
        allocated=[
            schemas.AllocatedTotal(
                unit=unit, currency=currency, quantity=int(qty), quoted_cost=cost
            )
            for (unit, currency), (qty, cost) in sorted(totals.items())
        ],
        opened_at=req.opened_at,
        closed_at=req.closed_at,
        cancelled_at=req.cancelled_at,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


def _emit(session: Session, type: str, req: Request, actor: Principal) -> None:
    events.emit(
        session, type, to_schema(req), subject_id=req.id, project_id=req.project_id, actor=actor
    )


def list_requests(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    capability_id: str | None,
    status: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Request], str | None]:
    where = []
    if capability_id:
        where.append(Request.capability_id == capability_id)
    if status:
        where.append(Request.status == status)
    return scoped.list_scoped(
        session, actor, Request, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_request(session: Session, actor: Principal, req_id: str) -> Request:
    return scoped.get_scoped(session, actor, Request, req_id, LABEL)


def _check_spec_version(session: Session, project_id: str, spec_version_id: str) -> SpecVersion:
    version = session.get(SpecVersion, spec_version_id)
    if version is None or version.spec.project_id != project_id:
        raise Invalid(f"No spec version with id '{spec_version_id}' in this project.")
    return version


def create_request(session: Session, actor: Principal, body: schemas.RequestCreate) -> Request:
    actor.require_write()
    cap = session.get(Capability, body.capability_id)
    if cap is None or not actor.can_see_project(cap.project_id):
        raise Invalid(f"No capability with id '{body.capability_id}'.")
    if body.spec_version_id:
        _check_spec_version(session, cap.project_id, body.spec_version_id)
    req = Request(id=new_id("req"), project_id=cap.project_id, **body.model_dump())
    session.add(req)
    session.flush()
    session.refresh(req, ["spec_version", "allocations"])
    _emit(session, "request.created", req, actor)
    return req


def update_request(
    session: Session, actor: Principal, req_id: str, body: schemas.RequestUpdate
) -> Request:
    req = get_request(session, actor, req_id)
    actor.require_write()
    if req.status not in ("draft", "open"):
        raise Conflict(f"This request is {req.status} and can't change.")
    changes = body.model_dump(exclude_unset=True)
    # due_date and spec_version_id may be cleared with null; other fields ignore null.
    changes = {k: v for k, v in changes.items() if v is not None or k == "due_date"}
    if "spec_version_id" in body.model_fields_set:
        new_version = body.spec_version_id
        if new_version is None:
            if req.status == "open":
                raise Conflict("An open request must keep an approved spec version.")
            changes["spec_version_id"] = None
        else:
            version = _check_spec_version(session, req.project_id, new_version)
            if req.status == "open" and version.status != "approved":
                raise Conflict("An open request can only use an approved spec version.")
    scoped.apply_changes(req, changes)
    session.flush()
    session.refresh(req, ["spec_version"])
    _emit(session, "request.updated", req, actor)
    return req


def open_request(session: Session, actor: Principal, req_id: str) -> Request:
    req = get_request(session, actor, req_id)
    actor.require_write()
    if req.status != "draft":
        raise Conflict(f"Only draft requests can be opened; this one is {req.status}.")
    if req.spec_version is None or req.spec_version.status != "approved":
        raise Conflict("Attach an approved spec version (spec_version_id) before opening.")
    req.status, req.opened_at = "open", utcnow()
    session.flush()
    _emit(session, "request.opened", req, actor)
    return req


def close_request(session: Session, actor: Principal, req_id: str) -> Request:
    req = get_request(session, actor, req_id)
    actor.require_write()
    if req.status != "open":
        raise Conflict(f"Only open requests can be closed; this one is {req.status}.")
    active = [a.id for a in req.allocations if a.status == "active"]
    if active:
        raise Conflict(
            f"{len(active)} allocation(s) are still active ({', '.join(active)}). "
            "Complete or cancel them first."
        )
    for alloc in req.allocations:
        if alloc.status == "planned":
            allocations.mark_cancelled(session, alloc, actor)
    req.status, req.closed_at = "closed", utcnow()
    session.flush()
    _emit(session, "request.closed", req, actor)
    return req


def cancel_request(session: Session, actor: Principal, req_id: str) -> Request:
    req = get_request(session, actor, req_id)
    actor.require_write()
    if req.status not in ("draft", "open"):
        raise Conflict(f"This request is already {req.status}.")
    for alloc in req.allocations:
        if alloc.status in ("planned", "active"):
            allocations.mark_cancelled(session, alloc, actor)
    req.status, req.cancelled_at = "cancelled", utcnow()
    session.flush()
    _emit(session, "request.cancelled", req, actor)
    return req


def delete_request(session: Session, actor: Principal, req_id: str) -> None:
    req = get_request(session, actor, req_id)
    actor.require_write()
    if req.allocations:
        raise Conflict(f"This request has {len(req.allocations)} allocation(s). Cancel it instead.")
    _emit(session, "request.deleted", req, actor)
    session.delete(req)
    session.flush()
