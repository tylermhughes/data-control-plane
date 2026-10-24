from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="EvalResultCreate")


@_attrs_define
class EvalResultCreate:
    """
    Attributes:
        dataset_version_id (str):
        value (float):
        metric (None | str | Unset): Defaults to the capability's main eval metric.
        higher_is_better (bool | None | Unset): Defaults to the capability's setting for its main metric. Required for
            other metrics.
        run_name (str | Unset):  Default: ''.
        external_run_url (None | str | Unset): e.g. a W&B run.
        recorded_at (datetime.datetime | None | Unset): Defaults to now.
        notes (str | Unset):  Default: ''.
    """

    dataset_version_id: str
    value: float
    metric: None | str | Unset = UNSET
    higher_is_better: bool | None | Unset = UNSET
    run_name: str | Unset = ""
    external_run_url: None | str | Unset = UNSET
    recorded_at: datetime.datetime | None | Unset = UNSET
    notes: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        dataset_version_id = self.dataset_version_id

        value = self.value

        metric: None | str | Unset
        if isinstance(self.metric, Unset):
            metric = UNSET
        else:
            metric = self.metric

        higher_is_better: bool | None | Unset
        if isinstance(self.higher_is_better, Unset):
            higher_is_better = UNSET
        else:
            higher_is_better = self.higher_is_better

        run_name = self.run_name

        external_run_url: None | str | Unset
        if isinstance(self.external_run_url, Unset):
            external_run_url = UNSET
        else:
            external_run_url = self.external_run_url

        recorded_at: None | str | Unset
        if isinstance(self.recorded_at, Unset):
            recorded_at = UNSET
        elif isinstance(self.recorded_at, datetime.datetime):
            recorded_at = self.recorded_at.isoformat()
        else:
            recorded_at = self.recorded_at

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "dataset_version_id": dataset_version_id,
                "value": value,
            }
        )
        if metric is not UNSET:
            field_dict["metric"] = metric
        if higher_is_better is not UNSET:
            field_dict["higher_is_better"] = higher_is_better
        if run_name is not UNSET:
            field_dict["run_name"] = run_name
        if external_run_url is not UNSET:
            field_dict["external_run_url"] = external_run_url
        if recorded_at is not UNSET:
            field_dict["recorded_at"] = recorded_at
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_version_id = d.pop("dataset_version_id")

        value = d.pop("value")

        def _parse_metric(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metric = _parse_metric(d.pop("metric", UNSET))

        def _parse_higher_is_better(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        higher_is_better = _parse_higher_is_better(d.pop("higher_is_better", UNSET))

        run_name = d.pop("run_name", UNSET)

        def _parse_external_run_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_run_url = _parse_external_run_url(d.pop("external_run_url", UNSET))

        def _parse_recorded_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                recorded_at_type_0 = datetime.datetime.fromisoformat(data)

                return recorded_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        recorded_at = _parse_recorded_at(d.pop("recorded_at", UNSET))

        notes = d.pop("notes", UNSET)

        eval_result_create = cls(
            dataset_version_id=dataset_version_id,
            value=value,
            metric=metric,
            higher_is_better=higher_is_better,
            run_name=run_name,
            external_run_url=external_run_url,
            recorded_at=recorded_at,
            notes=notes,
        )

        return eval_result_create
