from fastapi import APIRouter

from app.api.deps import PrincipalDep, SessionDep
from app.api.problems import READ_ERRORS
from app.schemas.quality import QualityRun
from app.services import quality

router = APIRouter(prefix="/quality-runs", tags=["batches"])


@router.get("/{run_id}", summary="Get a quality run", responses=READ_ERRORS)
def get_run(run_id: str, session: SessionDep, principal: PrincipalDep) -> QualityRun:
    """Every check's outcome, a plain-language summary, examples of problems, and the
    measured metrics that acceptance rules use."""
    return QualityRun.model_validate(quality.get_run(session, principal, run_id))
