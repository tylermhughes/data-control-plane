from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.spec_content_coverage_targets_additional_property import SpecContentCoverageTargetsAdditionalProperty


T = TypeVar("T", bound="SpecContentCoverageTargets")


@_attrs_define
class SpecContentCoverageTargets:
    """Target share of items per attribute value, as fractions (0.35 = 35%). Each attribute's shares must add up to 1 or
    less.

    """

    additional_properties: dict[str, SpecContentCoverageTargetsAdditionalProperty] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.spec_content_coverage_targets_additional_property import (
            SpecContentCoverageTargetsAdditionalProperty,  # noqa: PLC0415
        )

        d = dict(src_dict)
        spec_content_coverage_targets = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = SpecContentCoverageTargetsAdditionalProperty.from_dict(prop_dict)

            additional_properties[prop_name] = additional_property

        spec_content_coverage_targets.additional_properties = additional_properties
        return spec_content_coverage_targets

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> SpecContentCoverageTargetsAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: SpecContentCoverageTargetsAdditionalProperty) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
