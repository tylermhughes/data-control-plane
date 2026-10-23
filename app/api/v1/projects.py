from fastapi import APIRouter, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.projects import Project, ProjectCreate, ProjectUpdate
from app.services import projects

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", summary="List projects", responses=READ_ERRORS)
def list_projects(
    session: SessionDep, principal: PrincipalDep, limit: Limit = 50, cursor: Cursor = None
) -> Page[Project]:
    """Admin keys see every project. Project keys see only their own."""
    rows, next_cursor = projects.list_projects(session, principal, limit=limit, cursor=cursor)
    return Page(data=[Project.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Project,
    summary="Create a project",
    responses=WRITE_ERRORS,
)
def create_project(
    body: ProjectCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Project | Response:
    """Needs an admin key with write access. Names must be unique."""
    if idem.replay:
        return idem.replay
    out = Project.model_validate(projects.create_project(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{project_id}", summary="Get a project", responses=READ_ERRORS)
def get_project(project_id: str, session: SessionDep, principal: PrincipalDep) -> Project:
    return Project.model_validate(projects.get_project(session, principal, project_id))


@router.patch("/{project_id}", summary="Update a project", responses=WRITE_ERRORS)
def update_project(
    project_id: str, body: ProjectUpdate, session: SessionDep, principal: PrincipalDep
) -> Project:
    """Needs an admin key with write access. Only the fields you send are changed."""
    out = Project.model_validate(projects.update_project(session, principal, project_id, body))
    session.commit()
    return out


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses=WRITE_ERRORS,
)
def delete_project(project_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Needs an admin key with write access. Revoke the project's API keys first."""
    projects.delete_project(session, principal, project_id)
    session.commit()
