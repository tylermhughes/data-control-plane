from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Currency, Description, Money, MoneyOut, ProjectIdIn

_EXAMPLE: dict[str, Any] = {
    "name": "Package damage detection",
    "description": "Find dents, tears and crushes on packages on the conveyor.",
    "eval_metric": "recall@0.5",
    "higher_is_better": True,
    "value_per_point": "25000.00",
    "point_size": 0.01,
    "currency": "USD",
}


class CapabilityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [_EXAMPLE]})

    project_id: str | None = ProjectIdIn
    name: str = Field(min_length=1, max_length=200, description="Unique within the project.")
    description: str = Description
    eval_metric: str = Field(
        min_length=1, max_length=200, description="The main eval metric for this capability."
    )
    higher_is_better: bool = Field(True, description="False for metrics like error rate.")
    value_per_point: Money = Field(
        description="Estimated business value of one point of improvement on the eval metric."
    )
    point_size: float = Field(
        1.0,
        gt=0,
        description="How much of the metric is one point. Use 0.01 for a 0–1 metric such as "
        "recall, so 0.812 → 0.857 is 4.5 points. Default 1: one unit as recorded.",
    )
    currency: Currency


class CapabilityUpdate(BaseModel):
    """Only the fields you send are changed. A capability can't move to another project."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"value_per_point": "30000.00"}]}
    )

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)
    eval_metric: str | None = Field(None, min_length=1, max_length=200)
    higher_is_better: bool | None = None
    value_per_point: Money | None = None
    point_size: float | None = Field(None, gt=0)
    currency: Currency | None = None


class Capability(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["cap_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str = Field(examples=["prj_01m5n7gwqfa18zhpw1zwh7w2zy"])
    name: str = Field(examples=[_EXAMPLE["name"]])
    description: str = Field(examples=[_EXAMPLE["description"]])
    eval_metric: str = Field(examples=["recall@0.5"])
    higher_is_better: bool
    value_per_point: MoneyOut
    point_size: float = Field(examples=[0.01])
    currency: str = Field(examples=["USD"])
    created_at: datetime
    updated_at: datetime
