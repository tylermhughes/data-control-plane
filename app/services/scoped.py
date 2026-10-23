"""Shared rules for things that live inside a project (capabilities, data sources, specs).

- Admin keys work in any project; project keys only in their own.
- Something in another project looks exactly like something that doesn't exist (404).
- Names are unique within a project.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid, NotFound
from app.models import Project
from app.models.base import ProjectScoped
from app.services.pagination import paginate
from app.services.principal import Principal


def resolve_project_id(session: Session, actor: Principal, project_id: str | None) -> str:
    """The project a new thing goes into: the one given, or the project key's own."""
    if project_id is None:
        if actor.project_id:
            return actor.project_id
        raise Invalid("project_id is required when using an admin key.")
    if not actor.can_see_project(project_id) or session.get(Project, project_id) is None:
        raise Invalid(f"No project with id '{project_id}'.")
    return project_id


def get_scoped[M: ProjectScoped](
    session: Session, actor: Principal, model: type[M], obj_id: str, label: str
) -> M:
    obj = session.get(model, obj_id)
    if obj is None or not actor.can_see_project(obj.project_id):
        raise NotFound(f"No {label} with id '{obj_id}'.")
    return obj


def list_scoped[M: ProjectScoped](
    session: Session,
    actor: Principal,
    model: type[M],
    *,
    project_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[M], str | None]:
    stmt = select(model)
    if not actor.is_admin:
        stmt = stmt.where(model.project_id == actor.project_id)
    if project_id:
        stmt = stmt.where(model.project_id == project_id)
    return paginate(session, stmt, model.id, limit=limit, cursor=cursor)


def check_name_free(
    session: Session, model: type[ProjectScoped], project_id: str, name: str, label: str
) -> None:
    taken = session.scalar(
        select(model.id).where(model.project_id == project_id, model.name == name)
    )
    if taken:
        raise Conflict(f"A {label} named '{name}' already exists in this project.")


def apply_changes(obj: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)
