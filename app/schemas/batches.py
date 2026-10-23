from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import Currency, Money, MoneyOut

BatchStatus = Literal["received", "accepted", "rejected"]
DecisionSource = Literal["dcp", "external"]
Count = Field(ge=0, le=1_000_000_000)
AttributeCounts = dict[str, dict[str, int]]


class Artifact(BaseModel):
    """A pointer to delivered data. DCP stores the pointer, not the data."""

    model_config = ConfigDict(extra="forbid")

    uri: str = Field(
        min_length=1,
        max_length=2000,
        description="Where the file is, e.g. s3://bucket/path/part-1.jsonl",
        examples=["s3://acme-cv-intake/surge/b-2042/part-1.jsonl"],
    )
    format: Literal["jsonl", "csv", "parquet", "images", "other"] = Field(examples=["jsonl"])
    sha256: str | None = Field(None, pattern=r"^[0-9a-f]{64}$")
    size_bytes: int | None = Field(None, ge=0)
    record_count: int | None = Field(None, ge=0)


class ExternalDecision(BaseModel):
    """For batches already accepted or rejected outside DCP (a vendor's QA, Labelbox, ...)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted", "rejected"]
    decided_by: str = Field(
        min_length=1,
        max_length=200,
        description="The system or person that decided, e.g. `labelbox`, `surge`.",
        examples=["surge"],
    )
    accepted_count: int | None = Field(None, ge=0, description="Required when accepted.")
    attribute_counts: AttributeCounts | None = None
    reason: str | None = Field(None, max_length=10_000, description="Required when rejected.")
    decided_at: datetime | None = Field(None, description="When it was decided. Defaults to now.")

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.status == "accepted" and self.accepted_count is None:
            raise ValueError("accepted_count is required when status is 'accepted'")
        if self.status == "rejected":
            if not self.reason:
                raise ValueError("reason is required when status is 'rejected'")
            if self.accepted_count or self.attribute_counts:
                raise ValueError("a rejected batch has no accepted items")
        return self


_EXAMPLE: dict[str, Any] = {
    "allocation_id": "alc_01m5n7gwqfa18zhpw1zwh7w2zy",
    "delivered_count": 12000,
    "spend": "18600.00",
    "contributor_count": 46,
    "artifacts": [
        {
            "uri": "s3://acme-cv-intake/surge/b-2042/part-1.jsonl",
            "format": "jsonl",
            "record_count": 12000,
        }
    ],
    "external_ref": "surge-delivery-2042",
}


class BatchCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                _EXAMPLE,
                {
                    **_EXAMPLE,
                    "external_ref": "labelbox-export-118",
                    "decision": {
                        "status": "accepted",
                        "decided_by": "labelbox",
                        "accepted_count": 11290,
                        "attribute_counts": {
                            "package_type": {"corrugated_box": 4100, "shrink_wrapped": 3300}
                        },
                    },
                },
            ]
        },
    )

    allocation_id: str = Field(description="Must be active.")
    received_at: datetime | None = Field(None, description="Defaults to now.")
    delivered_count: int = Count
    spend: Money = Field(description="What this delivery cost.")
    currency: Currency | None = Field(None, description="Defaults to the allocation's currency.")
    contributor_count: int | None = Field(None, ge=0, description="People who worked on it.")
    artifacts: list[Artifact] = Field(default_factory=list, max_length=1000)
    notes: str = Field("", max_length=10_000)
    external_ref: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="The source's own id for this delivery. Unique per data source: sending "
        "the same one again updates that batch instead of creating a new one.",
    )
    external_url: str | None = Field(None, max_length=2000)
    decision: ExternalDecision | None = Field(
        None, description="Include to import a batch already accepted or rejected elsewhere."
    )


class BatchUpdate(BaseModel):
    """Undecided batches: any field. Accepted or rejected batches: notes only."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"delivered_count": 12040, "notes": "40 late items."}]},
    )

    received_at: datetime | None = None
    delivered_count: int | None = Field(None, ge=0, le=1_000_000_000)
    spend: Money | None = None
    contributor_count: int | None = Field(None, ge=0)
    artifacts: list[Artifact] | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=10_000)
    external_url: str | None = Field(None, max_length=2000)


class BatchAccept(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "accepted_count": 11290,
                    "decided_by": "Dana Okafor",
                    "attribute_counts": {
                        "package_type": {"corrugated_box": 4100, "shrink_wrapped": 3300}
                    },
                }
            ]
        },
    )

    accepted_count: int = Field(ge=0, description="Items kept. Can be less than delivered.")
    attribute_counts: AttributeCounts | None = Field(
        None,
        description="Accepted items per attribute value, e.g. "
        '{"package_type": {"shrink_wrapped": 3300}}. Optional.',
    )
    decided_by: str = Field("", max_length=200, description="Who decided.")


class BatchReject(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "reason": "Rater agreement 0.81 on small dents, below the 0.85 target.",
                    "decided_by": "Dana Okafor",
                }
            ]
        },
    )

    reason: str = Field(min_length=1, max_length=10_000)
    decided_by: str = Field("", max_length=200)


class Batch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["bat_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    request_id: str
    allocation_id: str
    data_source_id: str
    spec_version_id: str = Field(description="The spec version this delivery was made under.")
    received_at: datetime
    status: BatchStatus
    delivered_count: int = Field(examples=[12000])
    accepted_count: int | None = Field(examples=[11290], description="Null until decided.")
    rejected_count: int | None = Field(examples=[710], description="delivered − accepted.")
    contributor_count: int | None = Field(examples=[46])
    spend: MoneyOut = Field(examples=["18600.00"])
    currency: str = Field(examples=["USD"])
    attribute_counts: AttributeCounts
    artifacts: list[Artifact]
    notes: str
    decision_source: DecisionSource | None = Field(
        description="`dcp` if decided here, `external` if imported already decided."
    )
    decided_by: str | None = Field(examples=["labelbox"])
    decided_by_key_id: str | None
    decided_at: datetime | None
    rejection_reason: str | None
    external_ref: str | None = Field(examples=["surge-delivery-2042"])
    external_url: str | None
    created_at: datetime
    updated_at: datetime
