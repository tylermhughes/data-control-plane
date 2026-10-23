from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

Name = Field(min_length=1, max_length=200, description="Unique name.")


class ProjectCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"name": "Fulfillment vision", "description": "Warehouse camera models"}]
        },
    )

    name: str = Name
    description: str = Field("", max_length=10_000)


class ProjectUpdate(BaseModel):
    """Only the fields you send are changed."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"name": "Fulfillment CV"}]}
    )

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=10_000)


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["prj_01jbx4k9r2abcdefghjkmnpqrs"])
    name: str = Field(examples=["Fulfillment vision"])
    description: str = Field(examples=["Warehouse camera models"])
    created_at: datetime
    updated_at: datetime
