from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact import Artifact
    from ..models.batch_update_reported_metrics_type_0 import BatchUpdateReportedMetricsType0


T = TypeVar("T", bound="BatchUpdate")


@_attrs_define
class BatchUpdate:
    """Undecided batches (received, passed, failed): any field; changing `artifacts` re-runs the
    checks. While checks run: nothing. Accepted or rejected batches: notes only.

        Attributes:
            received_at (datetime.datetime | None | Unset):
            delivered_count (int | None | Unset):
            spend (float | None | str | Unset):
            contributor_count (int | None | Unset):
            artifacts (list[Artifact] | None | Unset):
            reported_metrics (BatchUpdateReportedMetricsType0 | None | Unset):
            notes (None | str | Unset):
            external_url (None | str | Unset):
    """

    received_at: datetime.datetime | None | Unset = UNSET
    delivered_count: int | None | Unset = UNSET
    spend: float | None | str | Unset = UNSET
    contributor_count: int | None | Unset = UNSET
    artifacts: list[Artifact] | None | Unset = UNSET
    reported_metrics: BatchUpdateReportedMetricsType0 | None | Unset = UNSET
    notes: None | str | Unset = UNSET
    external_url: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.batch_update_reported_metrics_type_0 import BatchUpdateReportedMetricsType0  # noqa: PLC0415

        received_at: None | str | Unset
        if isinstance(self.received_at, Unset):
            received_at = UNSET
        elif isinstance(self.received_at, datetime.datetime):
            received_at = self.received_at.isoformat()
        else:
            received_at = self.received_at

        delivered_count: int | None | Unset
        if isinstance(self.delivered_count, Unset):
            delivered_count = UNSET
        else:
            delivered_count = self.delivered_count

        spend: float | None | str | Unset
        if isinstance(self.spend, Unset):
            spend = UNSET
        else:
            spend = self.spend

        contributor_count: int | None | Unset
        if isinstance(self.contributor_count, Unset):
            contributor_count = UNSET
        else:
            contributor_count = self.contributor_count

        artifacts: list[dict[str, Any]] | None | Unset
        if isinstance(self.artifacts, Unset):
            artifacts = UNSET
        elif isinstance(self.artifacts, list):
            artifacts = []
            for artifacts_type_0_item_data in self.artifacts:
                artifacts_type_0_item = artifacts_type_0_item_data.to_dict()
                artifacts.append(artifacts_type_0_item)

        else:
            artifacts = self.artifacts

        reported_metrics: dict[str, Any] | None | Unset
        if isinstance(self.reported_metrics, Unset):
            reported_metrics = UNSET
        elif isinstance(self.reported_metrics, BatchUpdateReportedMetricsType0):
            reported_metrics = self.reported_metrics.to_dict()
        else:
            reported_metrics = self.reported_metrics

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        external_url: None | str | Unset
        if isinstance(self.external_url, Unset):
            external_url = UNSET
        else:
            external_url = self.external_url

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if received_at is not UNSET:
            field_dict["received_at"] = received_at
        if delivered_count is not UNSET:
            field_dict["delivered_count"] = delivered_count
        if spend is not UNSET:
            field_dict["spend"] = spend
        if contributor_count is not UNSET:
            field_dict["contributor_count"] = contributor_count
        if artifacts is not UNSET:
            field_dict["artifacts"] = artifacts
        if reported_metrics is not UNSET:
            field_dict["reported_metrics"] = reported_metrics
        if notes is not UNSET:
            field_dict["notes"] = notes
        if external_url is not UNSET:
            field_dict["external_url"] = external_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact import Artifact  # noqa: PLC0415
        from ..models.batch_update_reported_metrics_type_0 import BatchUpdateReportedMetricsType0  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_received_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                received_at_type_0 = datetime.datetime.fromisoformat(data)

                return received_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        received_at = _parse_received_at(d.pop("received_at", UNSET))

        def _parse_delivered_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        delivered_count = _parse_delivered_count(d.pop("delivered_count", UNSET))

        def _parse_spend(data: object) -> float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | str | Unset, data)

        spend = _parse_spend(d.pop("spend", UNSET))

        def _parse_contributor_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        contributor_count = _parse_contributor_count(d.pop("contributor_count", UNSET))

        def _parse_artifacts(data: object) -> list[Artifact] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                artifacts_type_0 = []
                _artifacts_type_0 = data
                for artifacts_type_0_item_data in _artifacts_type_0:
                    artifacts_type_0_item = Artifact.from_dict(artifacts_type_0_item_data)

                    artifacts_type_0.append(artifacts_type_0_item)

                return artifacts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Artifact] | None | Unset, data)

        artifacts = _parse_artifacts(d.pop("artifacts", UNSET))

        def _parse_reported_metrics(data: object) -> BatchUpdateReportedMetricsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                reported_metrics_type_0 = BatchUpdateReportedMetricsType0.from_dict(data)

                return reported_metrics_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BatchUpdateReportedMetricsType0 | None | Unset, data)

        reported_metrics = _parse_reported_metrics(d.pop("reported_metrics", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_external_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_url = _parse_external_url(d.pop("external_url", UNSET))

        batch_update = cls(
            received_at=received_at,
            delivered_count=delivered_count,
            spend=spend,
            contributor_count=contributor_count,
            artifacts=artifacts,
            reported_metrics=reported_metrics,
            notes=notes,
            external_url=external_url,
        )

        return batch_update
