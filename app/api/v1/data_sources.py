from fastapi import APIRouter, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.data_sources import DataSource, DataSourceCreate, DataSourceUpdate
from app.services import data_sources

router = APIRouter(prefix="/data-sources", tags=["data sources"])


@router.get("", summary="List data sources", responses=READ_ERRORS)
def list_sources(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[DataSource]:
    rows, next_cursor = data_sources.list_sources(
        session, principal, project_id=project_id, limit=limit, cursor=cursor
    )
    return Page(data=[DataSource.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataSource,
    summary="Create a data source",
    responses=WRITE_ERRORS,
)
def create_source(
    body: DataSourceCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> DataSource | Response:
    """A data source is anywhere data comes from: a vendor, an expert network, a synthetic
    pipeline, an RL environment, an internal workflow, beta users or a licensed dataset.
    Rights fields are recorded now and enforced by the training gate later."""
    if idem.replay:
        return idem.replay
    out = DataSource.model_validate(data_sources.create_source(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{source_id}", summary="Get a data source", responses=READ_ERRORS)
def get_source(source_id: str, session: SessionDep, principal: PrincipalDep) -> DataSource:
    return DataSource.model_validate(data_sources.get_source(session, principal, source_id))


@router.patch("/{source_id}", summary="Update a data source", responses=WRITE_ERRORS)
def update_source(
    source_id: str, body: DataSourceUpdate, session: SessionDep, principal: PrincipalDep
) -> DataSource:
    """Send `"rights_expires_at": null` to clear the expiry date."""
    out = DataSource.model_validate(data_sources.update_source(session, principal, source_id, body))
    session.commit()
    return out


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a data source",
    responses=WRITE_ERRORS,
)
def delete_source(source_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    data_sources.delete_source(session, principal, source_id)
    session.commit()
