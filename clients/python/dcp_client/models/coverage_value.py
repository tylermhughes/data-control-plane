from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CoverageValue")


@_attrs_define
class CoverageValue:
    """
    Attributes:
        value (str):
        count (int):
        actual_share (float | None): count ÷ items counted for this attribute.
        target_share (float | None):
        gap (float | None): actual − target.
        status (str): `below` (more than the tolerance under target), `ok`, `no_target` (no target set for this value)
            or `no_data` (nothing counted for this attribute yet).
    """

    value: str
    count: int
    actual_share: float | None
    target_share: float | None
    gap: float | None
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = self.value

        count = self.count

        actual_share: float | None
        actual_share = self.actual_share

        target_share: float | None
        target_share = self.target_share

        gap: float | None
        gap = self.gap

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "value": value,
                "count": count,
                "actual_share": actual_share,
                "target_share": target_share,
                "gap": gap,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        value = d.pop("value")

        count = d.pop("count")

        def _parse_actual_share(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        actual_share = _parse_actual_share(d.pop("actual_share"))

        def _parse_target_share(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        target_share = _parse_target_share(d.pop("target_share"))

        def _parse_gap(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        gap = _parse_gap(d.pop("gap"))

        status = d.pop("status")

        coverage_value = cls(
            value=value,
            count=count,
            actual_share=actual_share,
            target_share=target_share,
            gap=gap,
            status=status,
        )

        coverage_value.additional_properties = d
        return coverage_value

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
