from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict
from app.ids import new_id
from app.models import Allocation, Connector, DataSource, InboundEndpoint
from app.schemas import data_sources as schemas
from app.services import events, scoped
from app.services.principal import Principal

LABEL = "data source"


def default_unit_for(kind: str) -> str:
    return "tasks" if kind == "rl_environment" else "items"


def _emit(session: Session, type: str, src: DataSource, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.DataSource.model_validate(src),
        subject_id=src.id,
        project_id=src.project_id,
        actor=actor,
    )


def list_sources(
    session: Session, actor: Principal, *, project_id: str | None, limit: int, cursor: str | None
) -> tuple[Sequence[DataSource], str | None]:
    return scoped.list_scoped(
        session, actor, DataSource, project_id=project_id, limit=limit, cursor=cursor
    )


def get_source(session: Session, actor: Principal, src_id: str) -> DataSource:
    return scoped.get_scoped(session, actor, DataSource, src_id, LABEL)


def create_source(session: Session, actor: Principal, body: schemas.DataSourceCreate) -> DataSource:
    actor.require_write()
    project_id = scoped.resolve_project_id(session, actor, body.project_id)
    scoped.check_name_free(session, DataSource, project_id, body.name, LABEL)
    fields = body.model_dump(exclude={"project_id"})
    fields["default_unit"] = body.default_unit or default_unit_for(body.kind)
    src = DataSource(id=new_id("src"), project_id=project_id, **fields)
    session.add(src)
    session.flush()
    _emit(session, "data_source.created", src, actor)
    return src


def update_source(
    session: Session, actor: Principal, src_id: str, body: schemas.DataSourceUpdate
) -> DataSource:
    src = get_source(session, actor, src_id)
    actor.require_write()
    # rights_expires_at may be explicitly cleared with null; other fields ignore null.
    changes = {
        k: v
        for k, v in body.model_dump(exclude_unset=True).items()
        if v is not None or k == "rights_expires_at"
    }
    if changes.get("name", src.name) != src.name:
        scoped.check_name_free(session, DataSource, src.project_id, changes["name"], LABEL)
    scoped.apply_changes(src, changes)
    session.flush()
    _emit(session, "data_source.updated", src, actor)
    return src


def delete_source(session: Session, actor: Principal, src_id: str) -> None:
    src = get_source(session, actor, src_id)
    actor.require_write()
    scoped.refuse_if_used(session, LABEL, {"allocation": Allocation.data_source_id == src.id})
    for model, label in ((Connector, "connectors"), (InboundEndpoint, "inbound webhooks")):
        if session.scalar(select(model.id).where(model.data_source_id == src.id)):
            raise Conflict(f"This data source still has {label}. Delete them first.")
    _emit(session, "data_source.deleted", src, actor)
    session.delete(src)
    session.flush()
