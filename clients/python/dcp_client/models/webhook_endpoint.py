from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WebhookEndpoint")


@_attrs_define
class WebhookEndpoint:
    """
    Attributes:
        id (str):
        project_id (None | str): Null for org-wide endpoints.
        url (str):
        description (str):
        event_types (list[str]):
        enabled (bool):
        secret_version (int): Goes up by one each time the secret is rotated.
        secret_rotated_at (datetime.datetime | None):
        last_success_at (datetime.datetime | None): Last message delivered.
        last_failure_at (datetime.datetime | None): Last failed attempt.
        last_failure_reason (None | str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: None | str
    url: str
    description: str
    event_types: list[str]
    enabled: bool
    secret_version: int
    secret_rotated_at: datetime.datetime | None
    last_success_at: datetime.datetime | None
    last_failure_at: datetime.datetime | None
    last_failure_reason: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id: None | str
        project_id = self.project_id

        url = self.url

        description = self.description

        event_types = self.event_types

        enabled = self.enabled

        secret_version = self.secret_version

        secret_rotated_at: None | str
        if isinstance(self.secret_rotated_at, datetime.datetime):
            secret_rotated_at = self.secret_rotated_at.isoformat()
        else:
            secret_rotated_at = self.secret_rotated_at

        last_success_at: None | str
        if isinstance(self.last_success_at, datetime.datetime):
            last_success_at = self.last_success_at.isoformat()
        else:
            last_success_at = self.last_success_at

        last_failure_at: None | str
        if isinstance(self.last_failure_at, datetime.datetime):
            last_failure_at = self.last_failure_at.isoformat()
        else:
            last_failure_at = self.last_failure_at

        last_failure_reason: None | str
        last_failure_reason = self.last_failure_reason

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "url": url,
                "description": description,
                "event_types": event_types,
                "enabled": enabled,
                "secret_version": secret_version,
                "secret_rotated_at": secret_rotated_at,
                "last_success_at": last_success_at,
                "last_failure_at": last_failure_at,
                "last_failure_reason": last_failure_reason,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        url = d.pop("url")

        description = d.pop("description")

        event_types = cast(list[str], d.pop("event_types"))

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

        def _parse_last_success_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_success_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_success_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_success_at = _parse_last_success_at(d.pop("last_success_at"))

        def _parse_last_failure_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_failure_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_failure_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_failure_at = _parse_last_failure_at(d.pop("last_failure_at"))

        def _parse_last_failure_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_failure_reason = _parse_last_failure_reason(d.pop("last_failure_reason"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        webhook_endpoint = cls(
            id=id,
            project_id=project_id,
            url=url,
            description=description,
            event_types=event_types,
            enabled=enabled,
            secret_version=secret_version,
            secret_rotated_at=secret_rotated_at,
            last_success_at=last_success_at,
            last_failure_at=last_failure_at,
            last_failure_reason=last_failure_reason,
            created_at=created_at,
            updated_at=updated_at,
        )

        webhook_endpoint.additional_properties = d
        return webhook_endpoint

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
