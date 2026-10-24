from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CapabilityCreate")


@_attrs_define
class CapabilityCreate:
    """
    Attributes:
        name (str): Unique within the project.
        eval_metric (str): The main eval metric for this capability.
        value_per_point (float | str): Estimated business value of one point of improvement on the eval metric.
        currency (str): ISO 4217 code.
        project_id (None | str | Unset): Project to create this in. Optional for project keys (defaults to their
            project); required for admin keys.
        description (str | Unset):  Default: ''.
        higher_is_better (bool | Unset): False for metrics like error rate. Default: True.
        point_size (float | Unset): How much of the metric is one point. Use 0.01 for a 0–1 metric such as recall, so
            0.812 → 0.857 is 4.5 points. Default 1: one unit as recorded. Default: 1.0.
        flattening_threshold (float | Unset): The diagnosis calls returns 'flattening' when the latest dataset version's
            points per 10K fall below this share of the earlier versions' average. Default: 0.5.
    """

    name: str
    eval_metric: str
    value_per_point: float | str
    currency: str
    project_id: None | str | Unset = UNSET
    description: str | Unset = ""
    higher_is_better: bool | Unset = True
    point_size: float | Unset = 1.0
    flattening_threshold: float | Unset = 0.5

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        eval_metric = self.eval_metric

        value_per_point: float | str
        value_per_point = self.value_per_point

        currency = self.currency

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        description = self.description

        higher_is_better = self.higher_is_better

        point_size = self.point_size

        flattening_threshold = self.flattening_threshold

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "eval_metric": eval_metric,
                "value_per_point": value_per_point,
                "currency": currency,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if description is not UNSET:
            field_dict["description"] = description
        if higher_is_better is not UNSET:
            field_dict["higher_is_better"] = higher_is_better
        if point_size is not UNSET:
            field_dict["point_size"] = point_size
        if flattening_threshold is not UNSET:
            field_dict["flattening_threshold"] = flattening_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        eval_metric = d.pop("eval_metric")

        def _parse_value_per_point(data: object) -> float | str:
            return cast(float | str, data)

        value_per_point = _parse_value_per_point(d.pop("value_per_point"))

        currency = d.pop("currency")

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        description = d.pop("description", UNSET)

        higher_is_better = d.pop("higher_is_better", UNSET)

        point_size = d.pop("point_size", UNSET)

        flattening_threshold = d.pop("flattening_threshold", UNSET)

        capability_create = cls(
            name=name,
            eval_metric=eval_metric,
            value_per_point=value_per_point,
            currency=currency,
            project_id=project_id,
            description=description,
            higher_is_better=higher_is_better,
            point_size=point_size,
            flattening_threshold=flattening_threshold,
        )

        return capability_create
