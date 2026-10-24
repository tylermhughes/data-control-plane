from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.quality_run_status import QualityRunStatus
from ..models.quality_run_trigger import QualityRunTrigger

if TYPE_CHECKING:
    from ..models.check import Check
    from ..models.quality_run_attribute_counts import QualityRunAttributeCounts
    from ..models.quality_run_metrics import QualityRunMetrics


T = TypeVar("T", bound="QualityRun")


@_attrs_define
class QualityRun:
    """
    Attributes:
        id (str):
        project_id (str):
        batch_id (str):
        status (QualityRunStatus): `failed` if any check failed; `error` if the checks couldn't run.
        trigger (QualityRunTrigger):
        started_at (datetime.datetime | None):
        finished_at (datetime.datetime | None):
        checks (list[Check]):
        metrics (QualityRunMetrics): Measured values, usable in acceptance rules: record_count, parse_error_rate,
            schema_valid_rate, duplicate_rate, duplicates_in_batch, duplicates_in_project, empty_rate.<field>.
        attribute_counts (QualityRunAttributeCounts): Counted from the records in the files (all delivered records).
        error (None | str):
        created_at (datetime.datetime):
    """

    id: str
    project_id: str
    batch_id: str
    status: QualityRunStatus
    trigger: QualityRunTrigger
    started_at: datetime.datetime | None
    finished_at: datetime.datetime | None
    checks: list[Check]
    metrics: QualityRunMetrics
    attribute_counts: QualityRunAttributeCounts
    error: None | str
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        batch_id = self.batch_id

        status = self.status.value

        trigger = self.trigger.value

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        finished_at: None | str
        if isinstance(self.finished_at, datetime.datetime):
            finished_at = self.finished_at.isoformat()
        else:
            finished_at = self.finished_at

        checks = []
        for checks_item_data in self.checks:
            checks_item = checks_item_data.to_dict()
            checks.append(checks_item)

        metrics = self.metrics.to_dict()

        attribute_counts = self.attribute_counts.to_dict()

        error: None | str
        error = self.error

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "batch_id": batch_id,
                "status": status,
                "trigger": trigger,
                "started_at": started_at,
                "finished_at": finished_at,
                "checks": checks,
                "metrics": metrics,
                "attribute_counts": attribute_counts,
                "error": error,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.check import Check  # noqa: PLC0415
        from ..models.quality_run_attribute_counts import QualityRunAttributeCounts  # noqa: PLC0415
        from ..models.quality_run_metrics import QualityRunMetrics  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        batch_id = d.pop("batch_id")

        status = QualityRunStatus(d.pop("status"))

        trigger = QualityRunTrigger(d.pop("trigger"))

        def _parse_started_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = datetime.datetime.fromisoformat(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        started_at = _parse_started_at(d.pop("started_at"))

        def _parse_finished_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finished_at_type_0 = datetime.datetime.fromisoformat(data)

                return finished_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        finished_at = _parse_finished_at(d.pop("finished_at"))

        checks = []
        _checks = d.pop("checks")
        for checks_item_data in _checks:
            checks_item = Check.from_dict(checks_item_data)

            checks.append(checks_item)

        metrics = QualityRunMetrics.from_dict(d.pop("metrics"))

        attribute_counts = QualityRunAttributeCounts.from_dict(d.pop("attribute_counts"))

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        quality_run = cls(
            id=id,
            project_id=project_id,
            batch_id=batch_id,
            status=status,
            trigger=trigger,
            started_at=started_at,
            finished_at=finished_at,
            checks=checks,
            metrics=metrics,
            attribute_counts=attribute_counts,
            error=error,
            created_at=created_at,
        )

        quality_run.additional_properties = d
        return quality_run

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
