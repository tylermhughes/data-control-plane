from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.urls import check_webhook_url

EventPattern = Field(
    pattern=r"^(\*|[a-z_]+(\.[a-z_]+)*(\.\*)?)$",
    description="An event type (`batch.accepted`), a group (`batch.*`) or everything (`*`).",
)


def _url(value: str) -> str:
    check_webhook_url(value)
    return value


class WebhookEndpointCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "project_id": "prj_01m5n7gwqfa18zhpw1zwh7w2zy",
                    "url": "http://host.docker.internal:9000/",
                    "description": "Local test receiver",
                    "event_types": ["batch.*", "request.opened"],
                }
            ]
        },
    )

    project_id: str | None = Field(
        None,
        description="Only this project's events. Admin keys may leave it empty for an "
        "org-wide endpoint that receives every project's events. Project keys always get "
        "their own project.",
    )
    url: str = Field(min_length=1, max_length=2000, description="http or https.")
    description: str = Field("", max_length=2_000)
    event_types: list[str] = Field(default_factory=lambda: ["*"], min_length=1, max_length=100)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        return _url(value)

    @field_validator("event_types")
    @classmethod
    def _patterns(cls, value: list[str]) -> list[str]:
        return [_pattern(v) for v in value]


class WebhookEndpointUpdate(BaseModel):
    """Only the fields you send are changed. `enabled: false` pauses delivery; messages
    wait and are sent once it's enabled again."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"enabled": False}]})

    url: str | None = Field(None, min_length=1, max_length=2000)
    description: str | None = Field(None, max_length=2_000)
    event_types: list[str] | None = Field(None, min_length=1, max_length=100)
    enabled: bool | None = None

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return _url(value) if value is not None else None

    @field_validator("event_types")
    @classmethod
    def _patterns(cls, value: list[str] | None) -> list[str] | None:
        return [_pattern(v) for v in value] if value is not None else None


class _Pattern(BaseModel):
    value: str = EventPattern


def _pattern(value: str) -> str:
    return _Pattern(value=value).value


class WebhookEndpoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["whk_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str | None = Field(description="Null for org-wide endpoints.")
    url: str = Field(examples=["http://host.docker.internal:9000/"])
    description: str
    event_types: list[str] = Field(examples=[["batch.*", "request.opened"]])
    enabled: bool
    secret_version: int = Field(description="Goes up by one each time the secret is rotated.")
    secret_rotated_at: datetime | None
    last_success_at: datetime | None = Field(description="Last message delivered.")
    last_failure_at: datetime | None = Field(description="Last failed attempt.")
    last_failure_reason: str | None = Field(examples=["HTTP 503"])
    created_at: datetime
    updated_at: datetime


class WebhookSecret(BaseModel):
    secret: str = Field(
        description="Use this to verify the `webhook-signature` header.",
        examples=["whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw"],
    )
    previous_secret_valid_until: datetime | None = Field(
        description="After a rotation, messages are also signed with the previous secret "
        "until this time, so receivers can switch over without missing any."
    )


class WebhookEndpointCreated(WebhookEndpoint):
    secret: str = Field(description="The signing secret. Also available from `/secret`.")


class DeliveryAttempt(BaseModel):
    at: datetime
    status_code: int | None = Field(description="Null if no response (timeout, refused).")
    error: str | None = Field(examples=["Connection refused"])
    duration_ms: int
    response_body: str = Field(description="The first 1,000 characters of the response.")


class WebhookDelivery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["dlv_01m5n7gwqfa18zhpw1zwh7w2zy"])
    endpoint_id: str
    project_id: str | None
    event_id: str = Field(description="Also sent as the `webhook-id` header.")
    event_type: str = Field(examples=["batch.accepted"])
    status: Literal["pending", "delivered", "failed"]
    attempt_count: int
    next_attempt_at: datetime | None = Field(description="When it will be tried next.")
    delivered_at: datetime | None
    attempts: list[DeliveryAttempt]
    redelivery_of: str | None = Field(description="The delivery this one re-sends, if any.")
    payload: dict[str, Any] = Field(description="The exact JSON body sent.")
    created_at: datetime
    updated_at: datetime

    @field_validator("next_attempt_at", mode="before")
    @classmethod
    def _only_when_pending(cls, value: Any, info: Any) -> Any:
        return value if info.data.get("status") == "pending" else None


class Event(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["evt_01m5n7gwqfa18zhpw1zwh7w2zy"])
    type: str = Field(examples=["batch.accepted"])
    subject_id: str = Field(description="The thing that changed.", examples=["bat_01m5n7"])
    project_id: str | None
    actor_key_id: str | None = Field(description="The API key that made the change.")
    data: dict[str, Any] = Field(description="The thing as it was right after the change.")
    created_at: datetime
