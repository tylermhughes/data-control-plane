from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict, NotFound
from app.ids import new_id
from app.models import ApiKey, Capability, DataSource, Project, Spec
from app.schemas import projects as schemas
from app.services import events
from app.services.pagination import paginate
from app.services.principal import Principal


def _emit(session: Session, type: str, project: Project, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.Project.model_validate(project),
        subject_id=project.id,
        project_id=project.id,
        actor=actor,
    )


def _check_name_free(session: Session, name: str) -> None:
    if session.scalar(select(Project.id).where(Project.name == name)):
        raise Conflict(f"A project named '{name}' already exists.")


def list_projects(
    session: Session, actor: Principal, *, limit: int, cursor: str | None
) -> tuple[Sequence[Project], str | None]:
    stmt = select(Project)
    if not actor.is_admin:
        stmt = stmt.where(Project.id == actor.project_id)
    return paginate(session, stmt, Project.id, limit=limit, cursor=cursor)


def get_project(session: Session, actor: Principal, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None or not actor.can_see_project(project_id):
        raise NotFound(f"No project with id '{project_id}'.")
    return project


def create_project(session: Session, actor: Principal, body: schemas.ProjectCreate) -> Project:
    actor.require_admin()
    actor.require_write()
    _check_name_free(session, body.name)
    project = Project(id=new_id("prj"), name=body.name, description=body.description)
    session.add(project)
    session.flush()
    _emit(session, "project.created", project, actor)
    return project


def update_project(
    session: Session, actor: Principal, project_id: str, body: schemas.ProjectUpdate
) -> Project:
    project = get_project(session, actor, project_id)
    actor.require_admin()
    actor.require_write()
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if "name" in changes and changes["name"] != project.name:
        _check_name_free(session, changes["name"])
    for field, value in changes.items():
        setattr(project, field, value)
    session.flush()
    _emit(session, "project.updated", project, actor)
    return project


def delete_project(session: Session, actor: Principal, project_id: str) -> None:
    project = get_project(session, actor, project_id)
    actor.require_admin()
    actor.require_write()
    active_keys = session.scalar(
        select(ApiKey.id).where(ApiKey.project_id == project_id, ApiKey.revoked_at.is_(None))
    )
    if active_keys:
        raise Conflict("This project still has active API keys. Revoke them first.")
    for model, label in (
        (Capability, "capabilities"),
        (DataSource, "data sources"),
        (Spec, "specs"),
    ):
        if session.scalar(select(model.id).where(model.project_id == project_id)):
            raise Conflict(f"This project still has {label}. Delete them first.")
    _emit(session, "project.deleted", project, actor)
    session.delete(project)
    session.flush()
