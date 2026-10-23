from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Currency, Money, MoneyOut

Priority = Literal["P0", "P1", "P2", "P3"]
RequestStatus = Literal["draft", "open", "closed", "cancelled"]
AllocationStatus = Literal["planned", "active", "complete", "cancelled"]
Quantity = Field(gt=0, le=1_000_000_000, examples=[10000])

# --- requests --------------------------------------------------------------------------------

_REQUEST_EXAMPLE: dict[str, Any] = {
    "capability_id": "cap_01m5n7gwqfa18zhpw1zwh7w2zy",
    "title": "Shrink-wrapped and glossy packaging",
    "requested_by": "Priya Nair",
    "priority": "P1",
    "rationale": "Recall drops to 0.64 on shrink-wrap; damaged cosmetics returns are spiking.",
    "target_metric": "recall@0.5, shrink-wrapped slice",
    "quantity": 10000,
    "unit": "images",
    "due_date": "2026-12-15",
}


class RequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [_REQUEST_EXAMPLE]})

    capability_id: str = Field(description="The capability this data should improve.")
    title: str = Field(min_length=1, max_length=200)
    requested_by: str = Field("", max_length=200, description="Who asked for the data.")
    priority: Priority = "P2"
    rationale: str = Field("", max_length=10_000, description="Why the data is needed.")
    target_metric: str = Field(
        "", max_length=200, description="The eval metric or slice to move, if narrower."
    )
    quantity: int = Quantity
    unit: str = Field("items", min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_ ]*$")
    due_date: date | None = None
    spec_version_id: str | None = Field(
        None,
        description="The spec version to use (an `spv_` id). Can be added later. "
        "Must be approved before the request is opened.",
    )


class RequestUpdate(BaseModel):
    """Draft and open requests only. Fields you send are changed; the rest are kept."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"spec_version_id": "spv_01m5n7gwqfa18zhpw1zwh7w2zy", "priority": "P0"}]
        },
    )

    title: str | None = Field(None, min_length=1, max_length=200)
    requested_by: str | None = Field(None, max_length=200)
    priority: Priority | None = None
    rationale: str | None = Field(None, max_length=10_000)
    target_metric: str | None = Field(None, max_length=200)
    quantity: int | None = Field(None, gt=0, le=1_000_000_000)
    unit: str | None = Field(None, min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_ ]*$")
    due_date: date | None = None
    spec_version_id: str | None = None


class AllocatedTotal(BaseModel):
    """Allocated so far (planned, active and complete allocations) for one unit and currency."""

    unit: str = Field(examples=["images"])
    currency: str = Field(examples=["USD"])
    quantity: int = Field(examples=[12000])
    quoted_cost: MoneyOut


class Request(BaseModel):
    id: str = Field(examples=["req_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    capability_id: str
    title: str = Field(examples=[_REQUEST_EXAMPLE["title"]])
    requested_by: str = Field(examples=["Priya Nair"])
    priority: Priority = Field(examples=["P1"])
    rationale: str
    target_metric: str
    quantity: int = Field(examples=[10000])
    unit: str = Field(examples=["images"])
    due_date: date | None
    spec_version_id: str | None
    spec_id: str | None = Field(description="The spec that `spec_version_id` belongs to.")
    spec_version: int | None = Field(description="The version number of `spec_version_id`.")
    status: RequestStatus
    allocated: list[AllocatedTotal] = Field(
        description="Allocated so far, per unit and currency (cancelled allocations excluded). "
        "May exceed `quantity`, e.g. to cover expected rejects."
    )
    opened_at: datetime | None
    closed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- allocations -----------------------------------------------------------------------------

_ALLOCATION_EXAMPLE: dict[str, Any] = {
    "request_id": "req_01m5n7gwqfa18zhpw1zwh7w2zy",
    "data_source_id": "src_01m5n7gwqfa18zhpw1zwh7w2zy",
    "quantity": 4000,
    "quoted_unit_rate": "1.55",
    "currency": "USD",
    "due_date": "2026-12-01",
    "notes": "Quote Q-2210, includes 5% gold images.",
}


class AllocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [_ALLOCATION_EXAMPLE]})

    request_id: str
    data_source_id: str = Field(description="Must be in the same project as the request.")
    quantity: int = Quantity
    unit: str | None = Field(
        None,
        min_length=1,
        max_length=32,
        pattern=r"^[a-z][a-z0-9_ ]*$",
        description="Defaults to the data source's `default_unit`.",
    )
    quoted_unit_rate: Money = Field(description="Quoted price per unit.")
    currency: Currency
    due_date: date | None = None
    notes: str = Field("", max_length=10_000)


class AllocationUpdate(BaseModel):
    """Planned allocations: any field. Active: only quantity, due date and notes.
    Complete or cancelled: nothing."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"quantity": 5000, "due_date": "2026-12-08"}]},
    )

    quantity: int | None = Field(None, gt=0, le=1_000_000_000)
    unit: str | None = Field(None, min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_ ]*$")
    quoted_unit_rate: Money | None = None
    currency: Currency | None = None
    due_date: date | None = None
    notes: str | None = Field(None, max_length=10_000)


class Allocation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["alc_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    request_id: str
    data_source_id: str
    spec_version_id: str = Field(
        description="The spec version this allocation was quoted against. Never changes."
    )
    quantity: int = Field(examples=[4000])
    unit: str = Field(examples=["images"])
    quoted_unit_rate: MoneyOut = Field(examples=["1.55"])
    currency: str = Field(examples=["USD"])
    quoted_cost: MoneyOut = Field(description="quantity × quoted_unit_rate.", examples=["6200.00"])
    due_date: date | None
    notes: str
    status: AllocationStatus
    activated_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
