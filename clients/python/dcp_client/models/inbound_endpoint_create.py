from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="InboundEndpointCreate")


@_attrs_define
class InboundEndpointCreate:
    """
    Attributes:
        data_source_id (str): Deliveries posted here are batches of this source.
        description (str | Unset):  Default: ''.
        enabled (bool | Unset):  Default: True.
    """

    data_source_id: str
    description: str | Unset = ""
    enabled: bool | Unset = True

    def to_dict(self) -> dict[str, Any]:
        data_source_id = self.data_source_id

        description = self.description

        enabled = self.enabled

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "data_source_id": data_source_id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        data_source_id = d.pop("data_source_id")

        description = d.pop("description", UNSET)

        enabled = d.pop("enabled", UNSET)

        inbound_endpoint_create = cls(
            data_source_id=data_source_id,
            description=description,
            enabled=enabled,
        )

        return inbound_endpoint_create
