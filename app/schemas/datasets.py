from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Description, MoneyOut

# --- datasets --------------------------------------------------------------------------------


class DatasetCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "capability_id": "cap_01m5n7gwqfa18zhpw1zwh7w2zy",
                    "name": "damage-det",
                    "description": "Training data for package damage detection.",
                }
            ]
        },
    )

    capability_id: str = Field(description="The capability this data trains. Sets the project.")
    name: str = Field(min_length=1, max_length=200, description="Unique within the project.")
    description: str = Description


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"description": "Conveyor cameras."}]}
    )

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)


class Dataset(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["dst_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    capability_id: str
    name: str = Field(examples=["damage-det"])
    description: str
    latest_version: int = Field(description="0 until a version is created.", examples=[3])
    created_at: datetime
    updated_at: datetime


# --- dataset versions ------------------------------------------------------------------------


class DatasetVersionCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "batch_ids": ["bat_01m5n7gwqfa18zhpw1zwh7w2zy"],
                    "notes": "Adds the shrink-wrapped deliveries from Surge and Mercor.",
                }
            ]
        },
    )

    batch_ids: list[str] = Field(
        default_factory=list,
        max_length=10_000,
        description="Accepted batches to add. Only accepted batches can go into a dataset.",
    )
    baseline_version_id: str | None = Field(
        None,
        description="The version this one is compared against (any version for the same "
        "capability). Leave it out to use this dataset's previous version; send null for none.",
    )
    include_baseline_batches: bool = Field(
        True, description="Start from the baseline's batches and add `batch_ids` to them."
    )
    notes: str = Field("", max_length=10_000)


class UnitTotal(BaseModel):
    unit: str = Field(examples=["images"])
    currency: str = Field(examples=["USD"])
    batch_count: int
    accepted_count: int = Field(examples=[11290])
    spend: MoneyOut


class DatasetVersion(BaseModel):
    id: str = Field(examples=["dsv_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    dataset_id: str
    capability_id: str
    version: int = Field(examples=[2])
    baseline_version_id: str | None
    batch_ids: list[str]
    totals: list[UnitTotal] = Field(description="All batches in this version.")
    new_vs_baseline: list[UnitTotal] = Field(
        description="Only batches the baseline didn't have: the spend that bought this "
        "version's eval change."
    )
    notes: str
    created_at: datetime


class ManifestFile(BaseModel):
    batch_id: str
    data_source_id: str
    source_kind: str = Field(examples=["human_vendor"])
    spec_version_id: str
    uri: str = Field(examples=["s3://acme-cv-intake/surge/b-2042/part-1.jsonl"])
    format: str
    sha256: str | None
    size_bytes: int | None
    record_count: int | None


class Manifest(BaseModel):
    dataset_version_id: str
    batch_count: int
    file_count: int
    files: list[ManifestFile]


# --- eval results ----------------------------------------------------------------------------


class EvalResultCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "dataset_version_id": "dsv_01m5n7gwqfa18zhpw1zwh7w2zy",
                    "metric": "recall@0.5",
                    "value": 0.857,
                    "run_name": "dmg-r50-1023",
                    "external_run_url": "https://wandb.ai/acme/damage-det/runs/dmg-r50-1023",
                }
            ]
        },
    )

    dataset_version_id: str
    metric: str | None = Field(
        None, max_length=200, description="Defaults to the capability's main eval metric."
    )
    value: float
    higher_is_better: bool | None = Field(
        None,
        description="Defaults to the capability's setting for its main metric. Required for "
        "other metrics.",
    )
    run_name: str = Field("", max_length=200)
    external_run_url: str | None = Field(None, max_length=2000, description="e.g. a W&B run.")
    recorded_at: datetime | None = Field(None, description="Defaults to now.")
    notes: str = Field("", max_length=10_000)


class EvalResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["evr_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    dataset_version_id: str
    capability_id: str
    metric: str = Field(examples=["recall@0.5"])
    value: float = Field(examples=[0.857])
    higher_is_better: bool
    run_name: str
    external_run_url: str | None
    recorded_at: datetime
    notes: str
    created_at: datetime


# --- coverage --------------------------------------------------------------------------------


class CoverageValue(BaseModel):
    value: str = Field(examples=["shrink_wrapped"])
    count: int = Field(examples=[1300])
    actual_share: float | None = Field(
        description="count ÷ items counted for this attribute.", examples=[0.27]
    )
    target_share: float | None = Field(examples=[0.35])
    gap: float | None = Field(description="actual − target.", examples=[-0.08])
    status: str = Field(
        description="`below` (more than the tolerance under target), `ok`, `no_target` (no "
        "target set for this value) or `no_data` (nothing counted for this attribute yet).",
        examples=["below"],
    )


class CoverageAttribute(BaseModel):
    attribute: str = Field(examples=["package_type"])
    counted: int = Field(description="Accepted items with a count for this attribute.")
    counted_share_of_accepted: float | None = Field(
        description="How much of the accepted data this attribute's counts cover."
    )
    values: list[CoverageValue]


class Coverage(BaseModel):
    spec_version_id: str
    tolerance: float = Field(examples=[0.05])
    accepted_count: int = Field(description="Accepted items in the batches considered.")
    batch_ids: list[str]
    attributes: list[CoverageAttribute]
    gaps: list[str] = Field(
        description="Short summaries of every value below target.",
        examples=[["package_type=shrink_wrapped: 27% vs 35% target"]],
    )
