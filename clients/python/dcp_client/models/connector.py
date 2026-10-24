from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Connector")


@_attrs_define
class Connector:
    """
    Attributes:
        id (str):
        project_id (str):
        data_source_id (str):
        type_ (Literal['s3_watch']):
        description (str):
        bucket (str):
        prefix (str):
        endpoint_url (None | str):
        region (None | str):
        allocation_id (None | str):
        poll_interval_seconds (int):
        enabled (bool):
        has_credentials (bool): Whether keys are stored (they're never shown).
        access_key_hint (None | str): The last 4 characters of the stored access key id.
        next_poll_at (datetime.datetime):
        last_polled_at (datetime.datetime | None):
        last_found_at (datetime.datetime | None): When it last found a new file.
        last_error (None | str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    data_source_id: str
    type_: Literal["s3_watch"]
    description: str
    bucket: str
    prefix: str
    endpoint_url: None | str
    region: None | str
    allocation_id: None | str
    poll_interval_seconds: int
    enabled: bool
    has_credentials: bool
    access_key_hint: None | str
    next_poll_at: datetime.datetime
    last_polled_at: datetime.datetime | None
    last_found_at: datetime.datetime | None
    last_error: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        data_source_id = self.data_source_id

        type_ = self.type_

        description = self.description

        bucket = self.bucket

        prefix = self.prefix

        endpoint_url: None | str
        endpoint_url = self.endpoint_url

        region: None | str
        region = self.region

        allocation_id: None | str
        allocation_id = self.allocation_id

        poll_interval_seconds = self.poll_interval_seconds

        enabled = self.enabled

        has_credentials = self.has_credentials

        access_key_hint: None | str
        access_key_hint = self.access_key_hint

        next_poll_at = self.next_poll_at.isoformat()

        last_polled_at: None | str
        if isinstance(self.last_polled_at, datetime.datetime):
            last_polled_at = self.last_polled_at.isoformat()
        else:
            last_polled_at = self.last_polled_at

        last_found_at: None | str
        if isinstance(self.last_found_at, datetime.datetime):
            last_found_at = self.last_found_at.isoformat()
        else:
            last_found_at = self.last_found_at

        last_error: None | str
        last_error = self.last_error

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "data_source_id": data_source_id,
                "type": type_,
                "description": description,
                "bucket": bucket,
                "prefix": prefix,
                "endpoint_url": endpoint_url,
                "region": region,
                "allocation_id": allocation_id,
                "poll_interval_seconds": poll_interval_seconds,
                "enabled": enabled,
                "has_credentials": has_credentials,
                "access_key_hint": access_key_hint,
                "next_poll_at": next_poll_at,
                "last_polled_at": last_polled_at,
                "last_found_at": last_found_at,
                "last_error": last_error,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        data_source_id = d.pop("data_source_id")

        type_ = cast(Literal["s3_watch"], d.pop("type"))
        if type_ != "s3_watch":
            raise ValueError(f"type must match const 's3_watch', got '{type_}'")

        description = d.pop("description")

        bucket = d.pop("bucket")

        prefix = d.pop("prefix")

        def _parse_endpoint_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        endpoint_url = _parse_endpoint_url(d.pop("endpoint_url"))

        def _parse_region(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        region = _parse_region(d.pop("region"))

        def _parse_allocation_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        allocation_id = _parse_allocation_id(d.pop("allocation_id"))

        poll_interval_seconds = d.pop("poll_interval_seconds")

        enabled = d.pop("enabled")

        has_credentials = d.pop("has_credentials")

        def _parse_access_key_hint(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        access_key_hint = _parse_access_key_hint(d.pop("access_key_hint"))

        next_poll_at = datetime.datetime.fromisoformat(d.pop("next_poll_at"))

        def _parse_last_polled_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_polled_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_polled_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_polled_at = _parse_last_polled_at(d.pop("last_polled_at"))

        def _parse_last_found_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_found_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_found_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_found_at = _parse_last_found_at(d.pop("last_found_at"))

        def _parse_last_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_error = _parse_last_error(d.pop("last_error"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        connector = cls(
            id=id,
            project_id=project_id,
            data_source_id=data_source_id,
            type_=type_,
            description=description,
            bucket=bucket,
            prefix=prefix,
            endpoint_url=endpoint_url,
            region=region,
            allocation_id=allocation_id,
            poll_interval_seconds=poll_interval_seconds,
            enabled=enabled,
            has_credentials=has_credentials,
            access_key_hint=access_key_hint,
            next_poll_at=next_poll_at,
            last_polled_at=last_polled_at,
            last_found_at=last_found_at,
            last_error=last_error,
            created_at=created_at,
            updated_at=updated_at,
        )

        connector.additional_properties = d
        return connector

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
