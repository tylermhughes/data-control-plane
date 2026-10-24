from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.s3_credentials import S3Credentials


T = TypeVar("T", bound="ConnectorUpdate")


@_attrs_define
class ConnectorUpdate:
    """Only the fields you send are changed. Send `"credentials": null` to remove stored keys
    and use DCP's own S3 access instead.

        Attributes:
            description (None | str | Unset):
            prefix (None | str | Unset):
            endpoint_url (None | str | Unset):
            region (None | str | Unset):
            allocation_id (None | str | Unset):
            poll_interval_seconds (int | None | Unset):
            enabled (bool | None | Unset):
            credentials (None | S3Credentials | Unset):
    """

    description: None | str | Unset = UNSET
    prefix: None | str | Unset = UNSET
    endpoint_url: None | str | Unset = UNSET
    region: None | str | Unset = UNSET
    allocation_id: None | str | Unset = UNSET
    poll_interval_seconds: int | None | Unset = UNSET
    enabled: bool | None | Unset = UNSET
    credentials: None | S3Credentials | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.s3_credentials import S3Credentials  # noqa: PLC0415

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        prefix: None | str | Unset
        if isinstance(self.prefix, Unset):
            prefix = UNSET
        else:
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

        poll_interval_seconds: int | None | Unset
        if isinstance(self.poll_interval_seconds, Unset):
            poll_interval_seconds = UNSET
        else:
            poll_interval_seconds = self.poll_interval_seconds

        enabled: bool | None | Unset
        if isinstance(self.enabled, Unset):
            enabled = UNSET
        else:
            enabled = self.enabled

        credentials: dict[str, Any] | None | Unset
        if isinstance(self.credentials, Unset):
            credentials = UNSET
        elif isinstance(self.credentials, S3Credentials):
            credentials = self.credentials.to_dict()
        else:
            credentials = self.credentials

        field_dict: dict[str, Any] = {}

        field_dict.update({})
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

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_prefix(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prefix = _parse_prefix(d.pop("prefix", UNSET))

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

        def _parse_poll_interval_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        poll_interval_seconds = _parse_poll_interval_seconds(d.pop("poll_interval_seconds", UNSET))

        def _parse_enabled(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        enabled = _parse_enabled(d.pop("enabled", UNSET))

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

        connector_update = cls(
            description=description,
            prefix=prefix,
            endpoint_url=endpoint_url,
            region=region,
            allocation_id=allocation_id,
            poll_interval_seconds=poll_interval_seconds,
            enabled=enabled,
            credentials=credentials,
        )

        return connector_update
