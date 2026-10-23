from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal["admin", "project"]
Access = Literal["read", "write"]


class ApiKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200, examples=["CI pipeline"])
    role: Role = Field(
        description="`admin`: everything, including keys and projects. "
        "`project`: only the project in `project_id`."
    )
    access: Access = Field("write", description="`read` can only look; `write` can change.")
    project_id: str | None = Field(None, description="Required for `project` keys only.")

    @model_validator(mode="after")
    def check_scope(self) -> Self:
        if self.role == "project" and not self.project_id:
            raise ValueError("project_id is required when role is 'project'")
        if self.role == "admin" and self.project_id:
            raise ValueError("project_id must be empty when role is 'admin'")
        return self


class ApiKeyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)


class ApiKey(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["key_01jbx4k9r2abcdefghjkmnpqrs"])
    name: str
    key_prefix: str = Field(description="First characters of the key, to tell keys apart.")
    role: Role
    access: Access
    project_id: str | None
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = Field(description="Approximate: updated at most once a minute.")
    revoked_at: datetime | None


class ApiKeyCreated(ApiKey):
    secret: str = Field(
        description="The full API key. Shown only once: store it now, it cannot be retrieved later."
    )
