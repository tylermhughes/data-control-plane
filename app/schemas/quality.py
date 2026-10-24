from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Check(BaseModel):
    name: Literal[
        "files", "format", "schema", "duplicates", "stats", "attribute_counts", "acceptance_rules"
    ]
    outcome: Literal["passed", "warning", "failed", "skipped"]
    summary: str = Field(examples=["37 of 4,000 records don't match the record format."])
    details: dict[str, Any] = Field(description="Examples, per-file results, rule results, ...")


class QualityRun(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["qrn_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    batch_id: str
    status: Literal["queued", "running", "passed", "failed", "error"] = Field(
        description="`failed` if any check failed; `error` if the checks couldn't run."
    )
    trigger: Literal["auto", "manual"]
    started_at: datetime | None
    finished_at: datetime | None
    checks: list[Check]
    metrics: dict[str, Any] = Field(
        description="Measured values, usable in acceptance rules: record_count, "
        "parse_error_rate, schema_valid_rate, duplicate_rate, duplicates_in_batch, "
        "duplicates_in_project, empty_rate.<field>.",
        examples=[{"record_count": 4000, "duplicate_rate": 0.0125, "schema_valid_rate": 0.9991}],
    )
    attribute_counts: dict[str, dict[str, int]] = Field(
        description="Counted from the records in the files (all delivered records)."
    )
    error: str | None
    created_at: datetime


class QualitySummary(BaseModel):
    """The latest quality run on a batch, in brief."""

    run_id: str
    status: Literal["queued", "running", "passed", "failed", "error"]
    failed_checks: list[str] = Field(examples=[["acceptance_rules"]])
    warnings: list[str] = Field(examples=[["duplicates"]])
    finished_at: datetime | None
