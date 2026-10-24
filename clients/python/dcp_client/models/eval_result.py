from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="EvalResult")


@_attrs_define
class EvalResult:
    """
    Attributes:
        id (str):
        project_id (str):
        dataset_version_id (str):
        capability_id (str):
        metric (str):
        value (float):
        higher_is_better (bool):
        run_name (str):
        external_run_url (None | str):
        recorded_at (datetime.datetime):
        notes (str):
        created_at (datetime.datetime):
    """

    id: str
    project_id: str
    dataset_version_id: str
    capability_id: str
    metric: str
    value: float
    higher_is_better: bool
    run_name: str
    external_run_url: None | str
    recorded_at: datetime.datetime
    notes: str
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        dataset_version_id = self.dataset_version_id

        capability_id = self.capability_id

        metric = self.metric

        value = self.value

        higher_is_better = self.higher_is_better

        run_name = self.run_name

        external_run_url: None | str
        external_run_url = self.external_run_url

        recorded_at = self.recorded_at.isoformat()

        notes = self.notes

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "dataset_version_id": dataset_version_id,
                "capability_id": capability_id,
                "metric": metric,
                "value": value,
                "higher_is_better": higher_is_better,
                "run_name": run_name,
                "external_run_url": external_run_url,
                "recorded_at": recorded_at,
                "notes": notes,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        dataset_version_id = d.pop("dataset_version_id")

        capability_id = d.pop("capability_id")

        metric = d.pop("metric")

        value = d.pop("value")

        higher_is_better = d.pop("higher_is_better")

        run_name = d.pop("run_name")

        def _parse_external_run_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        external_run_url = _parse_external_run_url(d.pop("external_run_url"))

        recorded_at = datetime.datetime.fromisoformat(d.pop("recorded_at"))

        notes = d.pop("notes")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        eval_result = cls(
            id=id,
            project_id=project_id,
            dataset_version_id=dataset_version_id,
            capability_id=capability_id,
            metric=metric,
            value=value,
            higher_is_better=higher_is_better,
            run_name=run_name,
            external_run_url=external_run_url,
            recorded_at=recorded_at,
            notes=notes,
            created_at=created_at,
        )

        eval_result.additional_properties = d
        return eval_result

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
