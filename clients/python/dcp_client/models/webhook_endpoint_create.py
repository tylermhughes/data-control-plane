from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookEndpointCreate")


@_attrs_define
class WebhookEndpointCreate:
    """
    Attributes:
        url (str): http or https.
        project_id (None | str | Unset): Only this project's events. Admin keys may leave it empty for an org-wide
            endpoint that receives every project's events. Project keys always get their own project.
        description (str | Unset):  Default: ''.
        event_types (list[str] | Unset):
        enabled (bool | Unset):  Default: True.
    """

    url: str
    project_id: None | str | Unset = UNSET
    description: str | Unset = ""
    event_types: list[str] | Unset = UNSET
    enabled: bool | Unset = True

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        description = self.description

        event_types: list[str] | Unset = UNSET
        if not isinstance(self.event_types, Unset):
            event_types = self.event_types

        enabled = self.enabled

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "url": url,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if description is not UNSET:
            field_dict["description"] = description
        if event_types is not UNSET:
            field_dict["event_types"] = event_types
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        description = d.pop("description", UNSET)

        event_types = cast(list[str], d.pop("event_types", UNSET))

        enabled = d.pop("enabled", UNSET)

        webhook_endpoint_create = cls(
            url=url,
            project_id=project_id,
            description=description,
            event_types=event_types,
            enabled=enabled,
        )

        return webhook_endpoint_create
