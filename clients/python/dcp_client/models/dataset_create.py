from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetCreate")


@_attrs_define
class DatasetCreate:
    """
    Attributes:
        capability_id (str): The capability this data trains. Sets the project.
        name (str): Unique within the project.
        description (str | Unset):  Default: ''.
    """

    capability_id: str
    name: str
    description: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        capability_id = self.capability_id

        name = self.name

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "capability_id": capability_id,
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        capability_id = d.pop("capability_id")

        name = d.pop("name")

        description = d.pop("description", UNSET)

        dataset_create = cls(
            capability_id=capability_id,
            name=name,
            description=description,
        )

        return dataset_create
