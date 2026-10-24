from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.urls import check_webhook_url

# --- inbound webhooks ------------------------------------------------------------------------


class InboundEndpointCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "data_source_id": "src_01m5n7gwqfa18zhpw1zwh7w2zy",
                    "description": "Surge delivery notifications",
                }
            ]
        },
    )

    data_source_id: str = Field(description="Deliveries posted here are batches of this source.")
    description: str = Field("", max_length=2_000)
    enabled: bool = True


class InboundEndpointUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"enabled": False}]})

    description: str | None = Field(None, max_length=2_000)
    enabled: bool | None = None


class InboundEndpoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["ihk_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    data_source_id: str
    url_path: str = Field(
        description="Where to POST messages, relative to DCP's address.",
        examples=["/v1/inbound/ihk_01m5n7gwqfa18zhpw1zwh7w2zy"],
    )
    description: str
    enabled: bool
    secret_version: int
    secret_rotated_at: datetime | None
    last_received_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InboundEndpointCreated(InboundEndpoint):
    secret: str = Field(description="Give this to the sender. Also available from `/secret`.")


class InboundMessageLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    endpoint_id: str
    message_id: str | None = Field(description="The sender's `webhook-id` header.")
    message_type: str | None = Field(examples=["batch.delivered"])
    status: Literal["processed", "rejected"]
    http_status: int
    error: str | None = Field(examples=["Signature doesn't match."])
    batch_id: str | None
    received_at: datetime


class InboundResult(BaseModel):
    message_id: str
    status: Literal["processed"]
    batch_id: str
    batch_status: str = Field(examples=["checking"])
    duplicate: bool = Field(description="True if this message was already processed earlier.")


# --- connectors ------------------------------------------------------------------------------


class S3Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_key_id: str = Field(min_length=1, max_length=256)
    secret_access_key: str = Field(min_length=1, max_length=1024)
    session_token: str | None = Field(None, max_length=4096)


def _check_endpoint(value: str | None) -> str | None:
    if value is not None:
        check_webhook_url(value)  # http(s) only; cloud metadata addresses blocked
    return value


class ConnectorCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "data_source_id": "src_01m5n7gwqfa18zhpw1zwh7w2zy",
                    "description": "Surge delivery bucket",
                    "bucket": "intake",
                    "prefix": "surge/",
                    "endpoint_url": "http://s3:7070",
                    "credentials": {
                        "access_key_id": "dcp-dev-access",
                        "secret_access_key": "dcp-dev-secret-change-me",
                    },
                }
            ]
        },
    )

    data_source_id: str = Field(description="New files become batches of this source.")
    type: Literal["s3_watch"] = "s3_watch"
    description: str = Field("", max_length=2_000)
    bucket: str = Field(min_length=3, max_length=255, pattern=r"^[A-Za-z0-9.\-_]+$")
    prefix: str = Field("", max_length=1024, description="Only files under this path.")
    endpoint_url: str | None = Field(
        None, max_length=2000, description="For S3-compatible storage. Empty for AWS S3."
    )
    region: str | None = Field(None, max_length=64, examples=["us-east-1"])
    allocation_id: str | None = Field(
        None,
        description="Allocation the batches belong to. If empty, the source's single active "
        "allocation is used at the time each file is found.",
    )
    poll_interval_seconds: int = Field(60, ge=15, le=86_400)
    enabled: bool = True
    credentials: S3Credentials | None = Field(
        None,
        description="The bucket's access keys, stored encrypted and never shown again. If "
        "empty, DCP's own S3 access is used (its AWS settings or cloud role).",
    )

    @field_validator("endpoint_url")
    @classmethod
    def _endpoint(cls, value: str | None) -> str | None:
        return _check_endpoint(value)


class ConnectorUpdate(BaseModel):
    """Only the fields you send are changed. Send `"credentials": null` to remove stored keys
    and use DCP's own S3 access instead."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"poll_interval_seconds": 300}]}
    )

    description: str | None = Field(None, max_length=2_000)
    prefix: str | None = Field(None, max_length=1024)
    endpoint_url: str | None = Field(None, max_length=2000)
    region: str | None = Field(None, max_length=64)
    allocation_id: str | None = None
    poll_interval_seconds: int | None = Field(None, ge=15, le=86_400)
    enabled: bool | None = None
    credentials: S3Credentials | None = None

    @field_validator("endpoint_url")
    @classmethod
    def _endpoint(cls, value: str | None) -> str | None:
        return _check_endpoint(value)


class Connector(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(examples=["cnx_01m5n7gwqfa18zhpw1zwh7w2zy"])
    project_id: str
    data_source_id: str
    type: Literal["s3_watch"]
    description: str
    bucket: str = Field(examples=["intake"])
    prefix: str = Field(examples=["surge/"])
    endpoint_url: str | None
    region: str | None
    allocation_id: str | None
    poll_interval_seconds: int
    enabled: bool
    has_credentials: bool = Field(description="Whether keys are stored (they're never shown).")
    access_key_hint: str | None = Field(
        description="The last 4 characters of the stored access key id.", examples=["…cess"]
    )
    next_poll_at: datetime
    last_polled_at: datetime | None
    last_found_at: datetime | None = Field(description="When it last found a new file.")
    last_error: str | None = Field(examples=["Access denied listing s3://intake/surge/"])
    created_at: datetime
    updated_at: datetime


class ConnectorObject(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(examples=["surge/delivery-2042.jsonl"])
    size_bytes: int
    etag: str
    last_modified: datetime
    batch_id: str | None
    error: str | None = Field(description="Why this file didn't become a batch, if it didn't.")
    created_at: datetime
    updated_at: datetime


class PollResult(BaseModel):
    connector_id: str
    files_listed: int
    new_batches: list[str]
    updated_files: list[str] = Field(description="Files that changed since last seen.")
    errors: list[str]
