from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Description, ProjectIdIn

Kind = Literal[
    "human_vendor",
    "expert_network",
    "synthetic",
    "rl_environment",
    "enterprise_workflow",
    "beta_users",
    "licensed_dataset",
]
LicenseType = Literal[
    "owned",
    "vendor_agreement",
    "licensed",
    "customer_terms",
    "employee_notice",
    "open_license",
    "other",
]
Unit = Field(
    min_length=1,
    max_length=32,
    pattern=r"^[a-z][a-z0-9_ ]*$",
    description="What one unit of data is, e.g. images, tasks, reviews, records, flags.",
    examples=["images"],
)

_EXAMPLE: dict[str, Any] = {
    "name": "Surge",
    "kind": "human_vendor",
    "default_unit": "images",
    "license_type": "vendor_agreement",
    "consent_scope": "Contributor consent for model training on file with vendor.",
    "rights_expires_at": "2028-12-31",
    "pii_handling": "No faces or addresses; vendor blurs before delivery.",
    "notes": "MSA signed 2026-03; IP assigned to us.",
}


class DataSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [_EXAMPLE]})

    project_id: str | None = ProjectIdIn
    name: str = Field(min_length=1, max_length=200, description="Unique within the project.")
    description: str = Description
    kind: Kind
    default_unit: str | None = Field(
        None,
        min_length=1,
        max_length=32,
        pattern=r"^[a-z][a-z0-9_ ]*$",
        description="Defaults to `tasks` for RL environments and `items` for everything else.",
    )
    license_type: LicenseType = Field(description="Details go in `notes`.")
    consent_scope: str = Field("", max_length=10_000, description="What contributors agreed to.")
    rights_expires_at: date | None = Field(None, description="When the right to use it ends.")
    pii_handling: str = Field("", max_length=10_000)
    notes: str = Field("", max_length=10_000)


class DataSourceUpdate(BaseModel):
    """Only the fields you send are changed. `kind` and project can't change."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"rights_expires_at": "2029-06-30"}]}
    )

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)
    default_unit: str | None = Field(
        None, min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_ ]*$"
    )
    license_type: LicenseType | None = None
    consent_scope: str | None = Field(None, max_length=10_000)
    rights_expires_at: date | None = None
    pii_handling: str | None = Field(None, max_length=10_000)
    notes: str | None = Field(None, max_length=10_000)


class DataSource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["src_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str = Field(examples=["prj_01m5n7gwqfa18zhpw1zwh7w2zy"])
    name: str = Field(examples=["Surge"])
    description: str
    kind: Kind
    default_unit: str = Unit
    license_type: LicenseType = Field(examples=["vendor_agreement"])
    consent_scope: str = Field(examples=[_EXAMPLE["consent_scope"]])
    rights_expires_at: date | None = Field(examples=["2028-12-31"])
    pii_handling: str = Field(examples=[_EXAMPLE["pii_handling"]])
    notes: str = Field(examples=[_EXAMPLE["notes"]])
    created_at: datetime
    updated_at: datetime
