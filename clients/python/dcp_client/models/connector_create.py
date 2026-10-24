from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.s3_credentials import S3Credentials


T = TypeVar("T", bound="ConnectorCreate")


@_attrs_define
class ConnectorCreate:
    """
    Attributes:
        data_source_id (str): New files become batches of this source.
        bucket (str):
        type_ (Literal['s3_watch'] | Unset):  Default: 's3_watch'.
        description (str | Unset):  Default: ''.
        prefix (str | Unset): Only files under this path. Default: ''.
        endpoint_url (None | str | Unset): For S3-compatible storage. Empty for AWS S3.
        region (None | str | Unset):
        allocation_id (None | str | Unset): Allocation the batches belong to. If empty, the source's single active
            allocation is used at the time each file is found.
        poll_interval_seconds (int | Unset):  Default: 60.
        enabled (bool | Unset):  Default: True.
        credentials (None | S3Credentials | Unset): The bucket's access keys, stored encrypted and never shown again. If
            empty, DCP's own S3 access is used (its AWS settings or cloud role).
    """

    data_source_id: str
    bucket: str
    type_: Literal["s3_watch"] | Unset = "s3_watch"
    description: str | Unset = ""
    prefix: str | Unset = ""
    endpoint_url: None | str | Unset = UNSET
    region: None | str | Unset = UNSET
    allocation_id: None | str | Unset = UNSET
    poll_interval_seconds: int | Unset = 60
    enabled: bool | Unset = True
    credentials: None | S3Credentials | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.s3_credentials import S3Credentials  # noqa: PLC0415

        data_source_id = self.data_source_id

        bucket = self.bucket

        type_ = self.type_

        description = self.description

        prefix = self.prefix

        endpoint_url: None | str | Unset
        if isinstance(self.endpoint_url, Unset):
            endpoint_url = UNSET
        else:
            endpoint_url = self.endpoint_url

        region: None | str | Unset
        if isinstance(self.region, Unset):
            region = UNSET
        else:
            region = self.region

        allocation_id: None | str | Unset
        if isinstance(self.allocation_id, Unset):
            allocation_id = UNSET
        else:
            allocation_id = self.allocation_id

        poll_interval_seconds = self.poll_interval_seconds

        enabled = self.enabled

        credentials: dict[str, Any] | None | Unset
        if isinstance(self.credentials, Unset):
            credentials = UNSET
        elif isinstance(self.credentials, S3Credentials):
            credentials = self.credentials.to_dict()
        else:
            credentials = self.credentials

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "data_source_id": data_source_id,
                "bucket": bucket,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if description is not UNSET:
            field_dict["description"] = description
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if endpoint_url is not UNSET:
            field_dict["endpoint_url"] = endpoint_url
        if region is not UNSET:
            field_dict["region"] = region
        if allocation_id is not UNSET:
            field_dict["allocation_id"] = allocation_id
        if poll_interval_seconds is not UNSET:
            field_dict["poll_interval_seconds"] = poll_interval_seconds
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if credentials is not UNSET:
            field_dict["credentials"] = credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.s3_credentials import S3Credentials  # noqa: PLC0415

        d = dict(src_dict)
        data_source_id = d.pop("data_source_id")

        bucket = d.pop("bucket")

        type_ = cast(Literal["s3_watch"] | Unset, d.pop("type", UNSET))
        if type_ != "s3_watch" and not isinstance(type_, Unset):
            raise ValueError(f"type must match const 's3_watch', got '{type_}'")

        description = d.pop("description", UNSET)

        prefix = d.pop("prefix", UNSET)

        def _parse_endpoint_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        endpoint_url = _parse_endpoint_url(d.pop("endpoint_url", UNSET))

        def _parse_region(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        region = _parse_region(d.pop("region", UNSET))

        def _parse_allocation_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        allocation_id = _parse_allocation_id(d.pop("allocation_id", UNSET))

        poll_interval_seconds = d.pop("poll_interval_seconds", UNSET)

        enabled = d.pop("enabled", UNSET)

        def _parse_credentials(data: object) -> None | S3Credentials | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                credentials_type_0 = S3Credentials.from_dict(data)

                return credentials_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | S3Credentials | Unset, data)

        credentials = _parse_credentials(d.pop("credentials", UNSET))

        connector_create = cls(
            data_source_id=data_source_id,
            bucket=bucket,
            type_=type_,
            description=description,
            prefix=prefix,
            endpoint_url=endpoint_url,
            region=region,
            allocation_id=allocation_id,
            poll_interval_seconds=poll_interval_seconds,
            enabled=enabled,
            credentials=credentials,
        )

        return connector_create
