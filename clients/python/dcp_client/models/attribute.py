from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Attribute")


@_attrs_define
class Attribute:
    """Something recorded about every item, with its allowed values.

    Attributes:
        name (str): Lowercase letters, digits and underscores, starting with a letter.
        values (list[str]):
        description (str | Unset):  Default: ''.
    """

    name: str
    values: list[str]
    description: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        values = self.values

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "values": values,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        values = cast(list[str], d.pop("values"))

        description = d.pop("description", UNSET)

        attribute = cls(
            name=name,
            values=values,
            description=description,
        )

        return attribute
