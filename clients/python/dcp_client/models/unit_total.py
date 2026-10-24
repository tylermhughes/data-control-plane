from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UnitTotal")


@_attrs_define
class UnitTotal:
    """
    Attributes:
        unit (str):
        currency (str):
        batch_count (int):
        accepted_count (int):
        spend (str):
    """

    unit: str
    currency: str
    batch_count: int
    accepted_count: int
    spend: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        unit = self.unit

        currency = self.currency

        batch_count = self.batch_count

        accepted_count = self.accepted_count

        spend = self.spend

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "unit": unit,
                "currency": currency,
                "batch_count": batch_count,
                "accepted_count": accepted_count,
                "spend": spend,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        unit = d.pop("unit")

        currency = d.pop("currency")

        batch_count = d.pop("batch_count")

        accepted_count = d.pop("accepted_count")

        spend = d.pop("spend")

        unit_total = cls(
            unit=unit,
            currency=currency,
            batch_count=batch_count,
            accepted_count=accepted_count,
            spend=spend,
        )

        unit_total.additional_properties = d
        return unit_total

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
