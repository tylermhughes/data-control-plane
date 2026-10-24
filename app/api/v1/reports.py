from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import PrincipalDep, ProjectFilter, SessionDep
from app.api.problems import READ_ERRORS
from app.schemas.portfolio import Portfolio
from app.services import portfolio

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/portfolio", summary="Which data spend improved the models", responses=READ_ERRORS)
def get_portfolio(
    session: SessionDep,
    principal: PrincipalDep,
    project_id: ProjectFilter = None,
    since: Annotated[
        datetime | None, Query(description="Only batches and versions from this time on.")
    ] = None,
    until: Annotated[datetime | None, Query(description="Only before this time.")] = None,
) -> Portfolio:
    """Per capability and per source type: spend, usable units, cost per usable unit, eval
    change (in points, positive is better), points per 10K of spend and, per capability,
    value and ROI.

    **Eval change** counts each dataset version with a main-metric result whose baseline has
    one too. Its spend is what that version's new batches cost. **By source type**, eval
    change is an estimate: each version's change is split by each type's share of the items
    it added (`is_estimate: true`). Every row lists the versions and eval results it's based
    on, and `notes` explains anything missing."""
    return portfolio.build(session, principal, project_id=project_id, since=since, until=until)
