from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.coverage_value import CoverageValue


T = TypeVar("T", bound="CoverageAttribute")


@_attrs_define
class CoverageAttribute:
    """
    Attributes:
        attribute (str):
        counted (int): Accepted items with a count for this attribute.
        counted_share_of_accepted (float | None): How much of the accepted data this attribute's counts cover.
        values (list[CoverageValue]):
    """

    attribute: str
    counted: int
    counted_share_of_accepted: float | None
    values: list[CoverageValue]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        attribute = self.attribute

        counted = self.counted

        counted_share_of_accepted: float | None
        counted_share_of_accepted = self.counted_share_of_accepted

        values = []
        for values_item_data in self.values:
            values_item = values_item_data.to_dict()
            values.append(values_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "attribute": attribute,
                "counted": counted,
                "counted_share_of_accepted": counted_share_of_accepted,
                "values": values,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.coverage_value import CoverageValue  # noqa: PLC0415

        d = dict(src_dict)
        attribute = d.pop("attribute")

        counted = d.pop("counted")

        def _parse_counted_share_of_accepted(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        counted_share_of_accepted = _parse_counted_share_of_accepted(d.pop("counted_share_of_accepted"))

        values = []
        _values = d.pop("values")
        for values_item_data in _values:
            values_item = CoverageValue.from_dict(values_item_data)

            values.append(values_item)

        coverage_attribute = cls(
            attribute=attribute,
            counted=counted,
            counted_share_of_accepted=counted_share_of_accepted,
            values=values,
        )

        coverage_attribute.additional_properties = d
        return coverage_attribute

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
