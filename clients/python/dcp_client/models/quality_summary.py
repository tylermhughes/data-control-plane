from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.quality_summary_status import QualitySummaryStatus

T = TypeVar("T", bound="QualitySummary")


@_attrs_define
class QualitySummary:
    """The latest quality run on a batch, in brief.

    Attributes:
        run_id (str):
        status (QualitySummaryStatus):
        failed_checks (list[str]):
        warnings (list[str]):
        finished_at (datetime.datetime | None):
    """

    run_id: str
    status: QualitySummaryStatus
    failed_checks: list[str]
    warnings: list[str]
    finished_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_id = self.run_id

        status = self.status.value

        failed_checks = self.failed_checks

        warnings = self.warnings

        finished_at: None | str
        if isinstance(self.finished_at, datetime.datetime):
            finished_at = self.finished_at.isoformat()
        else:
            finished_at = self.finished_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_id": run_id,
                "status": status,
                "failed_checks": failed_checks,
                "warnings": warnings,
                "finished_at": finished_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        run_id = d.pop("run_id")

        status = QualitySummaryStatus(d.pop("status"))

        failed_checks = cast(list[str], d.pop("failed_checks"))

        warnings = cast(list[str], d.pop("warnings"))

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

        quality_summary = cls(
            run_id=run_id,
            status=status,
            failed_checks=failed_checks,
            warnings=warnings,
            finished_at=finished_at,
        )

        quality_summary.additional_properties = d
        return quality_summary

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
