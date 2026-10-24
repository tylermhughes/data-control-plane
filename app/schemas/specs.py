from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import Description, ProjectIdIn


def identifier(example: str) -> Any:
    return Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Lowercase letters, digits and underscores, starting with a letter.",
        examples=[example],
    )


SHARE_TOLERANCE = 1e-9


class Attribute(BaseModel):
    """Something recorded about every item, with its allowed values."""

    model_config = ConfigDict(extra="forbid")

    name: str = identifier("package_type")
    description: str = Field("", max_length=2_000)
    values: list[str] = Field(
        min_length=1,
        max_length=200,
        examples=[["corrugated_box", "poly_mailer", "shrink_wrapped"]],
    )

    @model_validator(mode="after")
    def unique_values(self) -> Self:
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"attribute '{self.name}' lists the same value twice")
        if any(not v or len(v) > 100 for v in self.values):
            raise ValueError(f"attribute '{self.name}': values must be 1-100 characters")
        return self


class AcceptanceRule(BaseModel):
    """A pass/fail rule for batches, e.g. agreement >= 0.85. Checked automatically from M6."""

    model_config = ConfigDict(extra="forbid")

    metric: str = identifier("agreement")
    operator: Literal[">=", ">", "<=", "<", "=="] = Field(examples=[">="])
    threshold: float = Field(examples=[0.85])
    applies_to: dict[str, str] | None = Field(
        None,
        description="Limit the rule to items with these attribute values.",
        examples=[{"damage_size": "small_dent"}],
    )
    description: str = Field("", max_length=2_000)


class SpecContent(BaseModel):
    """The content of a spec version. Cross-checked: targets and rules must use real attributes."""

    model_config = ConfigDict(extra="forbid")

    guidelines: str = Field(
        "", max_length=200_000, description="Instructions, plain text or Markdown."
    )
    attributes: list[Attribute] = Field(default_factory=list, max_length=100)
    coverage_targets: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Target share of items per attribute value, as fractions (0.35 = 35%). "
        "Each attribute's shares must add up to 1 or less.",
        examples=[{"package_type": {"shrink_wrapped": 0.35, "poly_mailer": 0.35}}],
    )
    coverage_tolerance: float = Field(
        0.05,
        ge=0,
        le=1,
        description="How far below its target share a value may fall before it is flagged "
        "(0.05 = 5 points: target 35%, actual 29% is flagged; 33% is not).",
    )
    acceptance_rules: list[AcceptanceRule] = Field(default_factory=list, max_length=100)
    record_schema: dict[str, Any] | None = Field(
        None, description="Optional JSON Schema for each record. Checked against files from M6."
    )
    change_note: str = Field("", max_length=10_000, description="What changed in this version.")

    @model_validator(mode="after")
    def cross_check(self) -> Self:
        check_content(self.attributes, self.coverage_targets, self.acceptance_rules)
        return self


def check_content(
    attributes: list[Attribute],
    coverage_targets: dict[str, dict[str, float]],
    acceptance_rules: list[AcceptanceRule],
) -> None:
    allowed = {a.name: set(a.values) for a in attributes}
    if len(allowed) != len(attributes):
        raise ValueError("two attributes have the same name")
    for attr, shares in coverage_targets.items():
        if attr not in allowed:
            raise ValueError(f"coverage target for unknown attribute '{attr}'")
        for value, share in shares.items():
            if value not in allowed[attr]:
                raise ValueError(f"coverage target for unknown value '{value}' of '{attr}'")
            if not 0 <= share <= 1:
                raise ValueError(f"share for {attr}={value} must be between 0 and 1")
        if sum(shares.values()) > 1 + SHARE_TOLERANCE:
            raise ValueError(f"coverage targets for '{attr}' add up to more than 1 (100%)")
    for rule in acceptance_rules:
        for attr, value in (rule.applies_to or {}).items():
            if attr not in allowed or value not in allowed[attr]:
                raise ValueError(f"rule on '{rule.metric}' applies to unknown {attr}={value}")


_CONTENT_EXAMPLE: dict[str, Any] = {
    "guidelines": "Label every area of visible damage at least 12 px across. One box per area.",
    "attributes": [
        {"name": "package_type", "values": ["corrugated_box", "poly_mailer", "shrink_wrapped"]},
        {"name": "conveyor_zone", "values": ["induct", "sort", "outbound_dock"]},
    ],
    "coverage_targets": {
        "package_type": {"corrugated_box": 0.30, "poly_mailer": 0.35, "shrink_wrapped": 0.35},
        "conveyor_zone": {"induct": 0.50, "sort": 0.35, "outbound_dock": 0.15},
    },
    "acceptance_rules": [
        {"metric": "agreement", "operator": ">=", "threshold": 0.85},
        {"metric": "duplicate_rate", "operator": "<=", "threshold": 0.02},
    ],
    "change_note": "First version.",
}


class SpecCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Package damage",
                    "description": "Damage on packages at the conveyor.",
                    "first_version": _CONTENT_EXAMPLE,
                }
            ]
        },
    )

    project_id: str | None = ProjectIdIn
    name: str = Field(min_length=1, max_length=200, description="Unique within the project.")
    description: str = Description
    first_version: SpecContent = Field(
        default_factory=SpecContent, description="Content of version 1, created as a draft."
    )


class SpecUpdate(BaseModel):
    """Renames or re-describes the spec. Content changes go into versions."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"name": "Package damage (conveyor)"}]}
    )

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)


class SpecVersionUpdate(BaseModel):
    """For drafts only. Fields you send replace the draft's; the rest are kept."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "coverage_targets": {
                        "package_type": {
                            "corrugated_box": 0.25,
                            "poly_mailer": 0.30,
                            "shrink_wrapped": 0.45,
                        }
                    },
                    "change_note": "More shrink-wrapped: recall is weakest there.",
                }
            ]
        },
    )

    guidelines: str | None = Field(None, max_length=200_000)
    attributes: list[Attribute] | None = Field(None, max_length=100)
    coverage_targets: dict[str, dict[str, float]] | None = None
    coverage_tolerance: float | None = Field(None, ge=0, le=1)
    acceptance_rules: list[AcceptanceRule] | None = Field(None, max_length=100)
    record_schema: dict[str, Any] | None = None
    change_note: str | None = Field(None, max_length=10_000)


class SpecVersionApprove(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"approved_by": "Priya Nair"}]}
    )

    approved_by: str = Field(
        min_length=1, max_length=200, description="Name of the person approving this version."
    )


class SpecVersion(SpecContent):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["spv_01m5n7gwqfa18zhpw1zwh7w2zy"])
    spec_id: str = Field(examples=["spc_01m5n7gwqfa18zhpw1zwh7w2zy"])
    version: int = Field(examples=[2])
    status: Literal["draft", "approved"]
    approved_by: str | None = Field(examples=["Priya Nair"])
    approved_by_key_id: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class Spec(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["spc_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str = Field(examples=["prj_01m5n7gwqfa18zhpw1zwh7w2zy"])
    name: str = Field(examples=["Package damage"])
    description: str
    latest_version: int = Field(description="Highest version number, draft or approved.")
    latest_approved_version: int | None = Field(
        description="Highest approved version number. Null until one is approved."
    )
    draft_version: int | None = Field(description="The open draft's number, if there is one.")
    created_at: datetime
    updated_at: datetime
