from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import Cursor, Limit, PrincipalDep, ProjectFilter, SessionDep
from app.api.idempotency import IdempotencyDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.common import Page
from app.schemas.datasets import (
    Dataset,
    DatasetCreate,
    DatasetUpdate,
    DatasetVersion,
    DatasetVersionCreate,
    EvalResult,
    EvalResultCreate,
    Manifest,
)
from app.services import datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])
versions = APIRouter(prefix="/dataset-versions", tags=["datasets"])
evals = APIRouter(prefix="/eval-results", tags=["eval results"])


# --- datasets --------------------------------------------------------------------------------


@router.get("", summary="List datasets", responses=READ_ERRORS)
def list_datasets(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    capability_id: Annotated[str | None, Query(description="Only for this capability.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[Dataset]:
    rows, next_cursor = datasets.list_datasets(
        session,
        principal,
        project_id=project_id,
        capability_id=capability_id,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[datasets.dataset_schema(r) for r in rows], next_cursor=next_cursor)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Dataset,
    summary="Create a dataset",
    responses=WRITE_ERRORS,
)
def create_dataset(
    body: DatasetCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> Dataset | Response:
    """A dataset is a named line of training data for one capability. Its content lives in
    frozen, numbered versions."""
    if idem.replay:
        return idem.replay
    out = datasets.dataset_schema(datasets.create_dataset(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@router.get("/{dataset_id}", summary="Get a dataset", responses=READ_ERRORS)
def get_dataset(dataset_id: str, session: SessionDep, principal: PrincipalDep) -> Dataset:
    return datasets.dataset_schema(datasets.get_dataset(session, principal, dataset_id))


@router.patch("/{dataset_id}", summary="Rename or re-describe a dataset", responses=WRITE_ERRORS)
def update_dataset(
    dataset_id: str, body: DatasetUpdate, session: SessionDep, principal: PrincipalDep
) -> Dataset:
    out = datasets.dataset_schema(datasets.update_dataset(session, principal, dataset_id, body))
    session.commit()
    return out


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an empty dataset",
    responses=WRITE_ERRORS,
)
def delete_dataset(dataset_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    datasets.delete_dataset(session, principal, dataset_id)
    session.commit()


@router.post(
    "/{dataset_id}/versions",
    status_code=status.HTTP_201_CREATED,
    response_model=DatasetVersion,
    summary="Create the next version (frozen)",
    responses=WRITE_ERRORS,
)
def create_dataset_version(
    dataset_id: str,
    body: DatasetVersionCreate,
    session: SessionDep,
    principal: PrincipalDep,
    idem: IdempotencyDep,
) -> DatasetVersion | Response:
    """Freezes a set of **accepted** batches as the dataset's next version.

    By default it is compared against the dataset's previous version and starts from that
    version's batches, adding `batch_ids`. `new_vs_baseline` shows what the added batches
    cost: the spend behind this version's eval change."""
    if idem.replay:
        return idem.replay
    out = datasets.version_schema(datasets.create_version(session, principal, dataset_id, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


# --- versions --------------------------------------------------------------------------------


@versions.get("", summary="List dataset versions", responses=READ_ERRORS)
def list_dataset_versions(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    dataset_id: Annotated[str | None, Query(description="Only of this dataset.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[DatasetVersion]:
    rows, next_cursor = datasets.list_versions(
        session, principal, project_id=project_id, dataset_id=dataset_id, limit=limit, cursor=cursor
    )
    return Page(data=[datasets.version_schema(r) for r in rows], next_cursor=next_cursor)


@versions.get("/{version_id}", summary="Get a dataset version", responses=READ_ERRORS)
def get_dataset_version(
    version_id: str, session: SessionDep, principal: PrincipalDep
) -> DatasetVersion:
    return datasets.version_schema(datasets.get_version(session, principal, version_id))


@versions.get("/{version_id}/manifest", summary="Files in a version", responses=READ_ERRORS)
def get_manifest(version_id: str, session: SessionDep, principal: PrincipalDep) -> Manifest:
    """Every file pointer in the version, with the batch, source and spec version it came
    from. What a training pipeline downloads."""
    return datasets.manifest(session, principal, version_id)


@versions.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset version",
    responses=WRITE_ERRORS,
)
def delete_dataset_version(version_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    """Only versions with no eval results that no other version uses as a baseline."""
    datasets.delete_version(session, principal, version_id)
    session.commit()


# --- eval results ----------------------------------------------------------------------------


@evals.get("", summary="List eval results", responses=READ_ERRORS)
def list_evals(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    dataset_version_id: Annotated[str | None, Query(description="Only for this version.")] = None,
    capability_id: Annotated[str | None, Query(description="Only for this capability.")] = None,
    metric: Annotated[str | None, Query(description="Only this metric.")] = None,
    limit: Limit = 50,
    cursor: Cursor = None,
) -> Page[EvalResult]:
    rows, next_cursor = datasets.list_evals(
        session,
        principal,
        project_id=project_id,
        dataset_version_id=dataset_version_id,
        capability_id=capability_id,
        metric=metric,
        limit=limit,
        cursor=cursor,
    )
    return Page(data=[EvalResult.model_validate(r) for r in rows], next_cursor=next_cursor)


@evals.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EvalResult,
    summary="Record an eval result",
    responses=WRITE_ERRORS,
)
def record_eval(
    body: EvalResultCreate, session: SessionDep, principal: PrincipalDep, idem: IdempotencyDep
) -> EvalResult | Response:
    """What a dataset version did to one metric. `metric` and `higher_is_better` default to
    the capability's main metric. Record several metrics (e.g. slices) as separate results."""
    if idem.replay:
        return idem.replay
    out = EvalResult.model_validate(datasets.record_eval(session, principal, body))
    idem.save(session, status.HTTP_201_CREATED, out)
    session.commit()
    return out


@evals.get("/{eval_id}", summary="Get an eval result", responses=READ_ERRORS)
def get_eval(eval_id: str, session: SessionDep, principal: PrincipalDep) -> EvalResult:
    return EvalResult.model_validate(datasets.get_eval(session, principal, eval_id))


@evals.delete(
    "/{eval_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an eval result",
    responses=WRITE_ERRORS,
)
def delete_eval(eval_id: str, session: SessionDep, principal: PrincipalDep) -> None:
    datasets.delete_eval(session, principal, eval_id)
    session.commit()
