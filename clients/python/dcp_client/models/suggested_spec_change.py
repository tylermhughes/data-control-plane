from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.suggested_spec_change_coverage_targets import SuggestedSpecChangeCoverageTargets


T = TypeVar("T", bound="SuggestedSpecChange")


@_attrs_define
class SuggestedSpecChange:
    """
    Attributes:
        spec_id (str):
        from_spec_version (int):
        coverage_targets (SuggestedSpecChangeCoverageTargets): Suggested new targets: more weight on values below
            target, so future collection catches up; the rest scaled down to keep the same total.
        change_note (str):
    """

    spec_id: str
    from_spec_version: int
    coverage_targets: SuggestedSpecChangeCoverageTargets
    change_note: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        spec_id = self.spec_id

        from_spec_version = self.from_spec_version

        coverage_targets = self.coverage_targets.to_dict()

        change_note = self.change_note

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "spec_id": spec_id,
                "from_spec_version": from_spec_version,
                "coverage_targets": coverage_targets,
                "change_note": change_note,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.suggested_spec_change_coverage_targets import SuggestedSpecChangeCoverageTargets  # noqa: PLC0415

        d = dict(src_dict)
        spec_id = d.pop("spec_id")

        from_spec_version = d.pop("from_spec_version")

        coverage_targets = SuggestedSpecChangeCoverageTargets.from_dict(d.pop("coverage_targets"))

        change_note = d.pop("change_note")

        suggested_spec_change = cls(
            spec_id=spec_id,
            from_spec_version=from_spec_version,
            coverage_targets=coverage_targets,
            change_note=change_note,
        )

        suggested_spec_change.additional_properties = d
        return suggested_spec_change

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
