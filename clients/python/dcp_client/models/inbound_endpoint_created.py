from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InboundEndpointCreated")


@_attrs_define
class InboundEndpointCreated:
    """
    Attributes:
        id (str):
        project_id (str):
        data_source_id (str):
        url_path (str): Where to POST messages, relative to DCP's address.
        description (str):
        enabled (bool):
        secret_version (int):
        secret_rotated_at (datetime.datetime | None):
        last_received_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        secret (str): Give this to the sender. Also available from `/secret`.
    """

    id: str
    project_id: str
    data_source_id: str
    url_path: str
    description: str
    enabled: bool
    secret_version: int
    secret_rotated_at: datetime.datetime | None
    last_received_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    secret: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        data_source_id = self.data_source_id

        url_path = self.url_path

        description = self.description

        enabled = self.enabled

        secret_version = self.secret_version

        secret_rotated_at: None | str
        if isinstance(self.secret_rotated_at, datetime.datetime):
            secret_rotated_at = self.secret_rotated_at.isoformat()
        else:
            secret_rotated_at = self.secret_rotated_at

        last_received_at: None | str
        if isinstance(self.last_received_at, datetime.datetime):
            last_received_at = self.last_received_at.isoformat()
        else:
            last_received_at = self.last_received_at

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        secret = self.secret

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "data_source_id": data_source_id,
                "url_path": url_path,
                "description": description,
                "enabled": enabled,
                "secret_version": secret_version,
                "secret_rotated_at": secret_rotated_at,
                "last_received_at": last_received_at,
                "created_at": created_at,
                "updated_at": updated_at,
                "secret": secret,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        data_source_id = d.pop("data_source_id")

        url_path = d.pop("url_path")

        description = d.pop("description")

        enabled = d.pop("enabled")

        secret_version = d.pop("secret_version")

        def _parse_secret_rotated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                secret_rotated_at_type_0 = datetime.datetime.fromisoformat(data)

                return secret_rotated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        secret_rotated_at = _parse_secret_rotated_at(d.pop("secret_rotated_at"))

        def _parse_last_received_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_received_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_received_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_received_at = _parse_last_received_at(d.pop("last_received_at"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        secret = d.pop("secret")

        inbound_endpoint_created = cls(
            id=id,
            project_id=project_id,
            data_source_id=data_source_id,
            url_path=url_path,
            description=description,
            enabled=enabled,
            secret_version=secret_version,
            secret_rotated_at=secret_rotated_at,
            last_received_at=last_received_at,
            created_at=created_at,
            updated_at=updated_at,
            secret=secret,
        )

        inbound_endpoint_created.additional_properties = d
        return inbound_endpoint_created

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
