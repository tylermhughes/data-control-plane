from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import MoneyOut
from app.schemas.datasets import Coverage

# --- allocation plan -------------------------------------------------------------------------


class SourceEvidence(BaseModel):
    """What a source's recent deliveries show (last 90 days)."""

    batches_decided: int = Field(description="Accepted or rejected batches.")
    delivered: int
    accepted: int
    accept_rate: float | None = Field(description="accepted ÷ delivered.", examples=[0.94])
    cost_per_usable_unit: MoneyOut | None = Field(examples=["1.65"])
    usable_per_day: float | None = Field(description="Throughput.", examples=[410.5])
    open_commitments: int = Field(
        description="Units still owed on its active allocations (quantity − accepted)."
    )
    last_quoted_rate: MoneyOut | None = Field(examples=["1.55"])
    currency: str | None
    value_mix: dict[str, dict[str, float]] = Field(
        description="Share of each attribute value in its accepted deliveries.",
        examples=[{"package_type": {"shrink_wrapped": 0.38}}],
    )


class Suggestion(BaseModel):
    data_source_id: str
    name: str = Field(examples=["Surge"])
    kind: str = Field(examples=["human_vendor"])
    role: Literal["proven", "pilot"] = Field(
        description="`proven`: has a track record; `pilot`: untested, small trial share."
    )
    share: float = Field(description="Share of the remaining usable units.", examples=[0.42])
    expected_usable: int = Field(examples=[2520])
    order_quantity: int = Field(
        description="What to allocate, including extra for expected rejects.", examples=[2681]
    )
    expected_cost: MoneyOut | None = Field(examples=["4155.55"])
    currency: str | None
    capacity_by_due_date: int | None = Field(
        description="Usable units it can likely deliver by the due date (null: no due date)."
    )
    evidence: SourceEvidence
    notes: list[str]
    allocation: dict[str, Any] = Field(
        description="Ready to send to POST /v1/allocations as-is (adjust anything first)."
    )


class Excluded(BaseModel):
    data_source_id: str
    name: str
    reason: str = Field(examples=["Rights expire 2026-11-30, before the due date 2026-12-15."])


class AllocationPlan(BaseModel):
    request_id: str
    unit: str
    requested: int
    already_allocated: int = Field(description="Planned, active and complete allocations.")
    remaining: int = Field(description="Usable units still to plan for.")
    due_date: date | None
    suggestions: list[Suggestion]
    excluded: list[Excluded]
    shortfall: int = Field(
        description="Usable units no source can deliver by the due date, as far as DCP can tell."
    )
    coverage_gaps: list[str] = Field(description="The request's current coverage gaps.")
    method: str = Field(
        description="How the split was made, in plain language.",
        examples=["Shares in proportion to 1 ÷ cost per usable unit, capped by capacity."],
    )
    generated_at: datetime


# --- diagnosis -------------------------------------------------------------------------------


class ScoredVersion(BaseModel):
    dataset_version_id: str
    dataset_id: str
    version: int
    created_at: datetime
    eval_value: float
    baseline_eval_value: float
    points: float = Field(description="Improvement over its baseline (positive is better).")
    spend: list[dict[str, Any]] = Field(description="Spend on the batches it added.")
    points_per_10k: float | None


class CauseCheck(BaseModel):
    cause: Literal["data_mix", "label_quality", "eval", "model", "saturation"]
    status: Literal["found", "ok", "not_checked", "not_applicable"]
    summary: str


class SuggestedSpecChange(BaseModel):
    spec_id: str
    from_spec_version: int
    coverage_targets: dict[str, dict[str, float]] = Field(
        description="Suggested new targets: more weight on values below target, so future "
        "collection catches up; the rest scaled down to keep the same total."
    )
    change_note: str


class Diagnosis(BaseModel):
    capability_id: str
    eval_metric: str
    flattening_threshold: float
    versions: list[ScoredVersion] = Field(description="Scored dataset versions, oldest first.")
    trend: Literal["not_enough_data", "improving", "flattening"]
    latest_vs_earlier: float | None = Field(
        description="Latest points per 10K ÷ average of earlier versions.", examples=[0.31]
    )
    checks: list[CauseCheck]
    recommendation: Literal["not_enough_data", "keep_going", "refine_spec", "investigate"]
    summary: str = Field(description="The recommendation and why, in plain language.")
    coverage: Coverage | None = Field(description="The data-mix check behind it, if run.")
    suggested_spec_change: SuggestedSpecChange | None
    generated_at: datetime
