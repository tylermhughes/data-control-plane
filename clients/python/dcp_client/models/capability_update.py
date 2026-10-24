from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CapabilityUpdate")


@_attrs_define
class CapabilityUpdate:
    """Only the fields you send are changed. A capability can't move to another project.

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        eval_metric (None | str | Unset):
        higher_is_better (bool | None | Unset):
        value_per_point (float | None | str | Unset):
        point_size (float | None | Unset):
        flattening_threshold (float | None | Unset):
        currency (None | str | Unset):
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    eval_metric: None | str | Unset = UNSET
    higher_is_better: bool | None | Unset = UNSET
    value_per_point: float | None | str | Unset = UNSET
    point_size: float | None | Unset = UNSET
    flattening_threshold: float | None | Unset = UNSET
    currency: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        eval_metric: None | str | Unset
        if isinstance(self.eval_metric, Unset):
            eval_metric = UNSET
        else:
            eval_metric = self.eval_metric

        higher_is_better: bool | None | Unset
        if isinstance(self.higher_is_better, Unset):
            higher_is_better = UNSET
        else:
            higher_is_better = self.higher_is_better

        value_per_point: float | None | str | Unset
        if isinstance(self.value_per_point, Unset):
            value_per_point = UNSET
        else:
            value_per_point = self.value_per_point

        point_size: float | None | Unset
        if isinstance(self.point_size, Unset):
            point_size = UNSET
        else:
            point_size = self.point_size

        flattening_threshold: float | None | Unset
        if isinstance(self.flattening_threshold, Unset):
            flattening_threshold = UNSET
        else:
            flattening_threshold = self.flattening_threshold

        currency: None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if eval_metric is not UNSET:
            field_dict["eval_metric"] = eval_metric
        if higher_is_better is not UNSET:
            field_dict["higher_is_better"] = higher_is_better
        if value_per_point is not UNSET:
            field_dict["value_per_point"] = value_per_point
        if point_size is not UNSET:
            field_dict["point_size"] = point_size
        if flattening_threshold is not UNSET:
            field_dict["flattening_threshold"] = flattening_threshold
        if currency is not UNSET:
            field_dict["currency"] = currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_eval_metric(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        eval_metric = _parse_eval_metric(d.pop("eval_metric", UNSET))

        def _parse_higher_is_better(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        higher_is_better = _parse_higher_is_better(d.pop("higher_is_better", UNSET))

        def _parse_value_per_point(data: object) -> float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | str | Unset, data)

        value_per_point = _parse_value_per_point(d.pop("value_per_point", UNSET))

        def _parse_point_size(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        point_size = _parse_point_size(d.pop("point_size", UNSET))

        def _parse_flattening_threshold(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        flattening_threshold = _parse_flattening_threshold(d.pop("flattening_threshold", UNSET))

        def _parse_currency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        capability_update = cls(
            name=name,
            description=description,
            eval_metric=eval_metric,
            higher_is_better=higher_is_better,
            value_per_point=value_per_point,
            point_size=point_size,
            flattening_threshold=flattening_threshold,
            currency=currency,
        )

        return capability_update
