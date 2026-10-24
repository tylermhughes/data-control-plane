from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import MoneyOut


class Amount(BaseModel):
    currency: str = Field(examples=["USD"])
    amount: MoneyOut


class UnitCount(BaseModel):
    unit: str = Field(examples=["images"])
    count: int = Field(examples=[11290])


class UnitCost(BaseModel):
    unit: str = Field(examples=["images"])
    currency: str = Field(examples=["USD"])
    amount: MoneyOut = Field(description="spend ÷ usable (accepted) units.", examples=["1.65"])


class Sources(BaseModel):
    """Where the row's numbers come from."""

    dataset_version_ids: list[str] = Field(description="Versions whose eval change is counted.")
    eval_result_ids: list[str] = Field(description="The eval results compared.")
    batch_count: int = Field(description="Batches behind the spend and usable units.")


class Row(BaseModel):
    spend: list[Amount] = Field(description="All batch spend in the period.")
    usable_units: list[UnitCount] = Field(description="Accepted items in the period.")
    cost_per_usable_unit: list[UnitCost]
    eval_change_points: float | None = Field(
        description="Improvement on the main metric, in points (positive is better), summed "
        "over versions compared with their baseline. Null if nothing could be compared.",
        examples=[4.5],
    )
    scored_versions: int = Field(description="Dataset versions with a comparable eval result.")
    spend_on_scored_versions: list[Amount] = Field(
        description="Spend on the batches each scored version added over its baseline."
    )
    points_per_10k: float | None = Field(
        description="eval_change_points per 10,000 of spend_on_scored_versions.", examples=[6.25]
    )
    sources: Sources
    notes: list[str] = Field(description="Why a figure is missing or approximate.")


class CapabilityRow(Row):
    capability_id: str
    name: str = Field(examples=["Package damage detection"])
    eval_metric: str = Field(examples=["recall@0.5"])
    point_size: float = Field(examples=[0.01])
    value_per_point: MoneyOut
    currency: str = Field(examples=["USD"])
    value: MoneyOut | None = Field(
        description="eval_change_points × value_per_point.", examples=["112500.00"]
    )
    roi: float | None = Field(
        description="value ÷ spend_on_scored_versions, e.g. 15.6 means 15.6× return.",
        examples=[15.63],
    )


class SourceKindRow(Row):
    kind: str = Field(examples=["human_vendor"])
    is_estimate: bool = Field(
        description="True: eval change is shared out between source types, not measured."
    )
    attribution_method: str = Field(
        description="`accepted_units_share`: each scored version's eval change is split by "
        "each source type's share of the items that version added.",
        examples=["accepted_units_share"],
    )


class Portfolio(BaseModel):
    project_id: str | None
    since: datetime | None
    until: datetime | None
    generated_at: datetime
    by_capability: list[CapabilityRow]
    by_source_kind: list[SourceKindRow]
