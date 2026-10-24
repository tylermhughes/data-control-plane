"""Shared rules for things that live inside a project (capabilities, data sources, specs).

- Admin keys work in any project; project keys only in their own.
- Something in another project looks exactly like something that doesn't exist (404).
- Names are unique within a project.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.errors import Conflict, Invalid, NotFound
from app.models import Allocation, Dataset, Project, Request
from app.models.base import InProject, ProjectScoped
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


def get_scoped[M: InProject](
    session: Session, actor: Principal, model: type[M], obj_id: str, label: str
) -> M:
    obj = session.get(model, obj_id)
    if obj is None or not actor.can_see_project(obj.project_id):
        raise NotFound(f"No {label} with id '{obj_id}'.")
    return obj


def list_scoped[M: InProject](
    session: Session,
    actor: Principal,
    model: type[M],
    *,
    project_id: str | None,
    limit: int,
    cursor: str | None,
    where: Sequence[ColumnElement[bool]] = (),
) -> tuple[Sequence[M], str | None]:
    stmt = select(model).where(*where)
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


def refuse_if_used(session: Session, what: str, users: dict[str, ColumnElement[bool]]) -> None:
    """Refuse a delete while other things still point at it, naming them.

    `users` maps a label (e.g. "request") to a condition selecting the rows that use it.
    """
    tables: dict[str, type[Request] | type[Allocation] | type[Dataset]] = {
        "request": Request,
        "allocation": Allocation,
        "dataset": Dataset,
    }
    for label, condition in users.items():
        ids = session.scalars(select(tables[label].id).where(condition).limit(4)).all()
        if ids:
            shown = ", ".join(ids[:3]) + (", ..." if len(ids) > 3 else "")
            raise Conflict(f"This {what} is used by {label}(s) {shown}. It can't be deleted.")


def apply_changes(obj: object, changes: dict[str, Any]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)
