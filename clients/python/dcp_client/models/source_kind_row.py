from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.amount import Amount
    from ..models.sources import Sources
    from ..models.unit_cost import UnitCost
    from ..models.unit_count import UnitCount


T = TypeVar("T", bound="SourceKindRow")


@_attrs_define
class SourceKindRow:
    """
    Attributes:
        spend (list[Amount]): All batch spend in the period.
        usable_units (list[UnitCount]): Accepted items in the period.
        cost_per_usable_unit (list[UnitCost]):
        eval_change_points (float | None): Improvement on the main metric, in points (positive is better), summed over
            versions compared with their baseline. Null if nothing could be compared.
        scored_versions (int): Dataset versions with a comparable eval result.
        spend_on_scored_versions (list[Amount]): Spend on the batches each scored version added over its baseline.
        points_per_10k (float | None): eval_change_points per 10,000 of spend_on_scored_versions.
        sources (Sources): Where the row's numbers come from.
        notes (list[str]): Why a figure is missing or approximate.
        kind (str):
        is_estimate (bool): True: eval change is shared out between source types, not measured.
        attribution_method (str): `accepted_units_share`: each scored version's eval change is split by each source
            type's share of the items that version added.
    """

    spend: list[Amount]
    usable_units: list[UnitCount]
    cost_per_usable_unit: list[UnitCost]
    eval_change_points: float | None
    scored_versions: int
    spend_on_scored_versions: list[Amount]
    points_per_10k: float | None
    sources: Sources
    notes: list[str]
    kind: str
    is_estimate: bool
    attribution_method: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        spend = []
        for spend_item_data in self.spend:
            spend_item = spend_item_data.to_dict()
            spend.append(spend_item)

        usable_units = []
        for usable_units_item_data in self.usable_units:
            usable_units_item = usable_units_item_data.to_dict()
            usable_units.append(usable_units_item)

        cost_per_usable_unit = []
        for cost_per_usable_unit_item_data in self.cost_per_usable_unit:
            cost_per_usable_unit_item = cost_per_usable_unit_item_data.to_dict()
            cost_per_usable_unit.append(cost_per_usable_unit_item)

        eval_change_points: float | None
        eval_change_points = self.eval_change_points

        scored_versions = self.scored_versions

        spend_on_scored_versions = []
        for spend_on_scored_versions_item_data in self.spend_on_scored_versions:
            spend_on_scored_versions_item = spend_on_scored_versions_item_data.to_dict()
            spend_on_scored_versions.append(spend_on_scored_versions_item)

        points_per_10k: float | None
        points_per_10k = self.points_per_10k

        sources = self.sources.to_dict()

        notes = self.notes

        kind = self.kind

        is_estimate = self.is_estimate

        attribution_method = self.attribution_method

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "spend": spend,
                "usable_units": usable_units,
                "cost_per_usable_unit": cost_per_usable_unit,
                "eval_change_points": eval_change_points,
                "scored_versions": scored_versions,
                "spend_on_scored_versions": spend_on_scored_versions,
                "points_per_10k": points_per_10k,
                "sources": sources,
                "notes": notes,
                "kind": kind,
                "is_estimate": is_estimate,
                "attribution_method": attribution_method,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amount import Amount  # noqa: PLC0415
        from ..models.sources import Sources  # noqa: PLC0415
        from ..models.unit_cost import UnitCost  # noqa: PLC0415
        from ..models.unit_count import UnitCount  # noqa: PLC0415

        d = dict(src_dict)
        spend = []
        _spend = d.pop("spend")
        for spend_item_data in _spend:
            spend_item = Amount.from_dict(spend_item_data)

            spend.append(spend_item)

        usable_units = []
        _usable_units = d.pop("usable_units")
        for usable_units_item_data in _usable_units:
            usable_units_item = UnitCount.from_dict(usable_units_item_data)

            usable_units.append(usable_units_item)

        cost_per_usable_unit = []
        _cost_per_usable_unit = d.pop("cost_per_usable_unit")
        for cost_per_usable_unit_item_data in _cost_per_usable_unit:
            cost_per_usable_unit_item = UnitCost.from_dict(cost_per_usable_unit_item_data)

            cost_per_usable_unit.append(cost_per_usable_unit_item)

        def _parse_eval_change_points(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        eval_change_points = _parse_eval_change_points(d.pop("eval_change_points"))

        scored_versions = d.pop("scored_versions")

        spend_on_scored_versions = []
        _spend_on_scored_versions = d.pop("spend_on_scored_versions")
        for spend_on_scored_versions_item_data in _spend_on_scored_versions:
            spend_on_scored_versions_item = Amount.from_dict(spend_on_scored_versions_item_data)

            spend_on_scored_versions.append(spend_on_scored_versions_item)

        def _parse_points_per_10k(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        points_per_10k = _parse_points_per_10k(d.pop("points_per_10k"))

        sources = Sources.from_dict(d.pop("sources"))

        notes = cast(list[str], d.pop("notes"))

        kind = d.pop("kind")

        is_estimate = d.pop("is_estimate")

        attribution_method = d.pop("attribution_method")

        source_kind_row = cls(
            spend=spend,
            usable_units=usable_units,
            cost_per_usable_unit=cost_per_usable_unit,
            eval_change_points=eval_change_points,
            scored_versions=scored_versions,
            spend_on_scored_versions=spend_on_scored_versions,
            points_per_10k=points_per_10k,
            sources=sources,
            notes=notes,
            kind=kind,
            is_estimate=is_estimate,
            attribution_method=attribution_method,
        )

        source_kind_row.additional_properties = d
        return source_kind_row

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
