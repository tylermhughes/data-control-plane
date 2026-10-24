from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.coverage_attribute import CoverageAttribute
    from ..models.coverage_counts_from import CoverageCountsFrom


T = TypeVar("T", bound="Coverage")


@_attrs_define
class Coverage:
    """
    Attributes:
        spec_version_id (str):
        tolerance (float):
        accepted_count (int): Accepted items in the batches considered (for a single undecided batch: 0).
        batch_ids (list[str]):
        counts_from (CoverageCountsFrom): Per batch: `files` (counted by DCP's checks), `reported` (by the source) or
            `none`.
        attributes (list[CoverageAttribute]):
        gaps (list[str]): Short summaries of every value below target.
    """

    spec_version_id: str
    tolerance: float
    accepted_count: int
    batch_ids: list[str]
    counts_from: CoverageCountsFrom
    attributes: list[CoverageAttribute]
    gaps: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        spec_version_id = self.spec_version_id

        tolerance = self.tolerance

        accepted_count = self.accepted_count

        batch_ids = self.batch_ids

        counts_from = self.counts_from.to_dict()

        attributes = []
        for attributes_item_data in self.attributes:
            attributes_item = attributes_item_data.to_dict()
            attributes.append(attributes_item)

        gaps = self.gaps

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "spec_version_id": spec_version_id,
                "tolerance": tolerance,
                "accepted_count": accepted_count,
                "batch_ids": batch_ids,
                "counts_from": counts_from,
                "attributes": attributes,
                "gaps": gaps,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.coverage_attribute import CoverageAttribute  # noqa: PLC0415
        from ..models.coverage_counts_from import CoverageCountsFrom  # noqa: PLC0415

        d = dict(src_dict)
        spec_version_id = d.pop("spec_version_id")

        tolerance = d.pop("tolerance")

        accepted_count = d.pop("accepted_count")

        batch_ids = cast(list[str], d.pop("batch_ids"))

        counts_from = CoverageCountsFrom.from_dict(d.pop("counts_from"))

        attributes = []
        _attributes = d.pop("attributes")
        for attributes_item_data in _attributes:
            attributes_item = CoverageAttribute.from_dict(attributes_item_data)

            attributes.append(attributes_item)

        gaps = cast(list[str], d.pop("gaps"))

        coverage = cls(
            spec_version_id=spec_version_id,
            tolerance=tolerance,
            accepted_count=accepted_count,
            batch_ids=batch_ids,
            counts_from=counts_from,
            attributes=attributes,
            gaps=gaps,
        )

        coverage.additional_properties = d
        return coverage

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
