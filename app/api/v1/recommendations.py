from fastapi import APIRouter, status

from app.api.deps import PrincipalDep, SessionDep
from app.api.problems import READ_ERRORS, WRITE_ERRORS
from app.schemas.recommendations import AllocationPlan, Diagnosis
from app.schemas.specs import SpecVersion
from app.services import recommendations

router = APIRouter(tags=["recommendations"])


@router.get(
    "/requests/{request_id}/allocation-plan",
    summary="Suggest how to split a request across sources",
    responses=READ_ERRORS,
)
def allocation_plan(
    request_id: str, session: SessionDep, principal: PrincipalDep
) -> AllocationPlan:
    """A suggested split of the request's remaining units across the project's sources, from
    their last 90 days: cost per usable unit, accept rate, throughput, what they already owe,
    rights and attribute mix. Untested sources get a small pilot. Each suggestion includes an
    `allocation` ready for `POST /v1/allocations`. Nothing is created until you do that."""
    return recommendations.allocation_plan(session, principal, request_id)


@router.get(
    "/capabilities/{capability_id}/diagnosis",
    summary="Is the data spend still paying off, and if not, why?",
    responses=READ_ERRORS,
)
def diagnosis(capability_id: str, session: SessionDep, principal: PrincipalDep) -> Diagnosis:
    """Scores each dataset version (eval change vs its baseline, points per 10K). When the
    latest falls below the capability's `flattening_threshold` of the earlier average, checks
    the cause before suggesting cuts: a data mix short of the spec's coverage targets means
    **refine the spec** (with suggested targets). Other causes aren't checked yet, so without a
    data-mix problem it recommends investigating rather than cutting spend."""
    return recommendations.diagnose(session, principal, capability_id)


@router.post(
    "/capabilities/{capability_id}/diagnosis/draft-spec",
    status_code=status.HTTP_201_CREATED,
    summary="Draft the suggested spec change",
    responses=WRITE_ERRORS,
)
def draft_spec(capability_id: str, session: SessionDep, principal: PrincipalDep) -> SpecVersion:
    """Creates the diagnosis's suggested coverage targets as a new **draft** version of the
    spec, marked as drafted by DCP. A person reviews, edits and approves it as usual. Refused
    if the diagnosis doesn't recommend refining the spec, or the spec already has a draft."""
    out = SpecVersion.model_validate(recommendations.draft_spec(session, principal, capability_id))
    session.commit()
    return out
