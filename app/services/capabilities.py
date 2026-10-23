from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.ids import new_id
from app.models import Capability, Request
from app.schemas import capabilities as schemas
from app.services import events, scoped
from app.services.principal import Principal

LABEL = "capability"


def _emit(session: Session, type: str, cap: Capability, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.Capability.model_validate(cap),
        subject_id=cap.id,
        project_id=cap.project_id,
        actor=actor,
    )


def list_capabilities(
    session: Session, actor: Principal, *, project_id: str | None, limit: int, cursor: str | None
) -> tuple[Sequence[Capability], str | None]:
    return scoped.list_scoped(
        session, actor, Capability, project_id=project_id, limit=limit, cursor=cursor
    )


def get_capability(session: Session, actor: Principal, cap_id: str) -> Capability:
    return scoped.get_scoped(session, actor, Capability, cap_id, LABEL)


def create_capability(
    session: Session, actor: Principal, body: schemas.CapabilityCreate
) -> Capability:
    actor.require_write()
    project_id = scoped.resolve_project_id(session, actor, body.project_id)
    scoped.check_name_free(session, Capability, project_id, body.name, LABEL)
    cap = Capability(
        id=new_id("cap"), project_id=project_id, **body.model_dump(exclude={"project_id"})
    )
    session.add(cap)
    session.flush()
    _emit(session, "capability.created", cap, actor)
    return cap


def update_capability(
    session: Session, actor: Principal, cap_id: str, body: schemas.CapabilityUpdate
) -> Capability:
    cap = get_capability(session, actor, cap_id)
    actor.require_write()
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if changes.get("name", cap.name) != cap.name:
        scoped.check_name_free(session, Capability, cap.project_id, changes["name"], LABEL)
    scoped.apply_changes(cap, changes)
    session.flush()
    _emit(session, "capability.updated", cap, actor)
    return cap


def delete_capability(session: Session, actor: Principal, cap_id: str) -> None:
    cap = get_capability(session, actor, cap_id)
    actor.require_write()
    scoped.refuse_if_used(session, LABEL, {"request": Request.capability_id == cap.id})
    _emit(session, "capability.deleted", cap, actor)
    session.delete(cap)
    session.flush()
