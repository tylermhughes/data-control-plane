from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Capability")


@_attrs_define
class Capability:
    """
    Attributes:
        id (str):
        project_id (str):
        name (str):
        description (str):
        eval_metric (str):
        higher_is_better (bool):
        value_per_point (str):
        point_size (float):
        flattening_threshold (float):
        currency (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    name: str
    description: str
    eval_metric: str
    higher_is_better: bool
    value_per_point: str
    point_size: float
    flattening_threshold: float
    currency: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        name = self.name

        description = self.description

        eval_metric = self.eval_metric

        higher_is_better = self.higher_is_better

        value_per_point = self.value_per_point

        point_size = self.point_size

        flattening_threshold = self.flattening_threshold

        currency = self.currency

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "name": name,
                "description": description,
                "eval_metric": eval_metric,
                "higher_is_better": higher_is_better,
                "value_per_point": value_per_point,
                "point_size": point_size,
                "flattening_threshold": flattening_threshold,
                "currency": currency,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        name = d.pop("name")

        description = d.pop("description")

        eval_metric = d.pop("eval_metric")

        higher_is_better = d.pop("higher_is_better")

        value_per_point = d.pop("value_per_point")

        point_size = d.pop("point_size")

        flattening_threshold = d.pop("flattening_threshold")

        currency = d.pop("currency")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        capability = cls(
            id=id,
            project_id=project_id,
            name=name,
            description=description,
            eval_metric=eval_metric,
            higher_is_better=higher_is_better,
            value_per_point=value_per_point,
            point_size=point_size,
            flattening_threshold=flattening_threshold,
            currency=currency,
            created_at=created_at,
            updated_at=updated_at,
        )

        capability.additional_properties = d
        return capability

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
