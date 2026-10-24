from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.scored_version_spend_item import ScoredVersionSpendItem


T = TypeVar("T", bound="ScoredVersion")


@_attrs_define
class ScoredVersion:
    """
    Attributes:
        dataset_version_id (str):
        dataset_id (str):
        version (int):
        created_at (datetime.datetime):
        eval_value (float):
        baseline_eval_value (float):
        points (float): Improvement over its baseline (positive is better).
        spend (list[ScoredVersionSpendItem]): Spend on the batches it added.
        points_per_10k (float | None):
    """

    dataset_version_id: str
    dataset_id: str
    version: int
    created_at: datetime.datetime
    eval_value: float
    baseline_eval_value: float
    points: float
    spend: list[ScoredVersionSpendItem]
    points_per_10k: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_version_id = self.dataset_version_id

        dataset_id = self.dataset_id

        version = self.version

        created_at = self.created_at.isoformat()

        eval_value = self.eval_value

        baseline_eval_value = self.baseline_eval_value

        points = self.points

        spend = []
        for spend_item_data in self.spend:
            spend_item = spend_item_data.to_dict()
            spend.append(spend_item)

        points_per_10k: float | None
        points_per_10k = self.points_per_10k

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_version_id": dataset_version_id,
                "dataset_id": dataset_id,
                "version": version,
                "created_at": created_at,
                "eval_value": eval_value,
                "baseline_eval_value": baseline_eval_value,
                "points": points,
                "spend": spend,
                "points_per_10k": points_per_10k,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.scored_version_spend_item import ScoredVersionSpendItem  # noqa: PLC0415

        d = dict(src_dict)
        dataset_version_id = d.pop("dataset_version_id")

        dataset_id = d.pop("dataset_id")

        version = d.pop("version")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        eval_value = d.pop("eval_value")

        baseline_eval_value = d.pop("baseline_eval_value")

        points = d.pop("points")

        spend = []
        _spend = d.pop("spend")
        for spend_item_data in _spend:
            spend_item = ScoredVersionSpendItem.from_dict(spend_item_data)

            spend.append(spend_item)

        def _parse_points_per_10k(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        points_per_10k = _parse_points_per_10k(d.pop("points_per_10k"))

        scored_version = cls(
            dataset_version_id=dataset_version_id,
            dataset_id=dataset_id,
            version=version,
            created_at=created_at,
            eval_value=eval_value,
            baseline_eval_value=baseline_eval_value,
            points=points,
            spend=spend,
            points_per_10k=points_per_10k,
        )

        scored_version.additional_properties = d
        return scored_version

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
