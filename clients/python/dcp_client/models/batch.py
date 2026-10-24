from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.batch_decision_source_type_0 import BatchDecisionSourceType0
from ..models.batch_status import BatchStatus

if TYPE_CHECKING:
    from ..models.artifact import Artifact
    from ..models.batch_attribute_counts import BatchAttributeCounts
    from ..models.batch_reported_metrics import BatchReportedMetrics
    from ..models.quality_summary import QualitySummary


T = TypeVar("T", bound="Batch")


@_attrs_define
class Batch:
    """
    Attributes:
        id (str):
        project_id (str):
        request_id (str):
        allocation_id (str):
        data_source_id (str):
        spec_version_id (str): The spec version this delivery was made under.
        received_at (datetime.datetime):
        status (BatchStatus):
        delivered_count (int):
        accepted_count (int | None): Null until decided.
        rejected_count (int | None): delivered − accepted.
        contributor_count (int | None):
        spend (str):
        currency (str):
        attribute_counts (BatchAttributeCounts): As reported (see `quality` for counts from the files).
        artifacts (list[Artifact]):
        reported_metrics (BatchReportedMetrics):
        delivered_count_from_files (bool): True while DCP fills delivered_count in from the files' record count.
        spend_is_estimate (bool): True while spend is an estimate (quoted rate × delivered_count).
        quality (None | QualitySummary): The latest automated check run.
        override_reason (None | str): Why a failed batch was accepted anyway.
        notes (str):
        decision_source (BatchDecisionSourceType0 | None): `dcp` if decided here, `external` if imported already
            decided.
        decided_by (None | str):
        decided_by_key_id (None | str):
        decided_at (datetime.datetime | None):
        rejection_reason (None | str):
        external_ref (None | str):
        external_url (None | str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    request_id: str
    allocation_id: str
    data_source_id: str
    spec_version_id: str
    received_at: datetime.datetime
    status: BatchStatus
    delivered_count: int
    accepted_count: int | None
    rejected_count: int | None
    contributor_count: int | None
    spend: str
    currency: str
    attribute_counts: BatchAttributeCounts
    artifacts: list[Artifact]
    reported_metrics: BatchReportedMetrics
    delivered_count_from_files: bool
    spend_is_estimate: bool
    quality: None | QualitySummary
    override_reason: None | str
    notes: str
    decision_source: BatchDecisionSourceType0 | None
    decided_by: None | str
    decided_by_key_id: None | str
    decided_at: datetime.datetime | None
    rejection_reason: None | str
    external_ref: None | str
    external_url: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.quality_summary import QualitySummary  # noqa: PLC0415

        id = self.id

        project_id = self.project_id

        request_id = self.request_id

        allocation_id = self.allocation_id

        data_source_id = self.data_source_id

        spec_version_id = self.spec_version_id

        received_at = self.received_at.isoformat()

        status = self.status.value

        delivered_count = self.delivered_count

        accepted_count: int | None
        accepted_count = self.accepted_count

        rejected_count: int | None
        rejected_count = self.rejected_count

        contributor_count: int | None
        contributor_count = self.contributor_count

        spend = self.spend

        currency = self.currency

        attribute_counts = self.attribute_counts.to_dict()

        artifacts = []
        for artifacts_item_data in self.artifacts:
            artifacts_item = artifacts_item_data.to_dict()
            artifacts.append(artifacts_item)

        reported_metrics = self.reported_metrics.to_dict()

        delivered_count_from_files = self.delivered_count_from_files

        spend_is_estimate = self.spend_is_estimate

        quality: dict[str, Any] | None
        if isinstance(self.quality, QualitySummary):
            quality = self.quality.to_dict()
        else:
            quality = self.quality

        override_reason: None | str
        override_reason = self.override_reason

        notes = self.notes

        decision_source: None | str
        if isinstance(self.decision_source, BatchDecisionSourceType0):
            decision_source = self.decision_source.value
        else:
            decision_source = self.decision_source

        decided_by: None | str
        decided_by = self.decided_by

        decided_by_key_id: None | str
        decided_by_key_id = self.decided_by_key_id

        decided_at: None | str
        if isinstance(self.decided_at, datetime.datetime):
            decided_at = self.decided_at.isoformat()
        else:
            decided_at = self.decided_at

        rejection_reason: None | str
        rejection_reason = self.rejection_reason

        external_ref: None | str
        external_ref = self.external_ref

        external_url: None | str
        external_url = self.external_url

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "request_id": request_id,
                "allocation_id": allocation_id,
                "data_source_id": data_source_id,
                "spec_version_id": spec_version_id,
                "received_at": received_at,
                "status": status,
                "delivered_count": delivered_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "contributor_count": contributor_count,
                "spend": spend,
                "currency": currency,
                "attribute_counts": attribute_counts,
                "artifacts": artifacts,
                "reported_metrics": reported_metrics,
                "delivered_count_from_files": delivered_count_from_files,
                "spend_is_estimate": spend_is_estimate,
                "quality": quality,
                "override_reason": override_reason,
                "notes": notes,
                "decision_source": decision_source,
                "decided_by": decided_by,
                "decided_by_key_id": decided_by_key_id,
                "decided_at": decided_at,
                "rejection_reason": rejection_reason,
                "external_ref": external_ref,
                "external_url": external_url,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact import Artifact  # noqa: PLC0415
        from ..models.batch_attribute_counts import BatchAttributeCounts  # noqa: PLC0415
        from ..models.batch_reported_metrics import BatchReportedMetrics  # noqa: PLC0415
        from ..models.quality_summary import QualitySummary  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        request_id = d.pop("request_id")

        allocation_id = d.pop("allocation_id")

        data_source_id = d.pop("data_source_id")

        spec_version_id = d.pop("spec_version_id")

        received_at = datetime.datetime.fromisoformat(d.pop("received_at"))

        status = BatchStatus(d.pop("status"))

        delivered_count = d.pop("delivered_count")

        def _parse_accepted_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        accepted_count = _parse_accepted_count(d.pop("accepted_count"))

        def _parse_rejected_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        rejected_count = _parse_rejected_count(d.pop("rejected_count"))

        def _parse_contributor_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        contributor_count = _parse_contributor_count(d.pop("contributor_count"))

        spend = d.pop("spend")

        currency = d.pop("currency")

        attribute_counts = BatchAttributeCounts.from_dict(d.pop("attribute_counts"))

        artifacts = []
        _artifacts = d.pop("artifacts")
        for artifacts_item_data in _artifacts:
            artifacts_item = Artifact.from_dict(artifacts_item_data)

            artifacts.append(artifacts_item)

        reported_metrics = BatchReportedMetrics.from_dict(d.pop("reported_metrics"))

        delivered_count_from_files = d.pop("delivered_count_from_files")

        spend_is_estimate = d.pop("spend_is_estimate")

        def _parse_quality(data: object) -> None | QualitySummary:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                quality_type_0 = QualitySummary.from_dict(data)

                return quality_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | QualitySummary, data)

        quality = _parse_quality(d.pop("quality"))

        def _parse_override_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        override_reason = _parse_override_reason(d.pop("override_reason"))

        notes = d.pop("notes")

        def _parse_decision_source(data: object) -> BatchDecisionSourceType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                decision_source_type_0 = BatchDecisionSourceType0(data)

                return decision_source_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BatchDecisionSourceType0 | None, data)

        decision_source = _parse_decision_source(d.pop("decision_source"))

        def _parse_decided_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        decided_by = _parse_decided_by(d.pop("decided_by"))

        def _parse_decided_by_key_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        decided_by_key_id = _parse_decided_by_key_id(d.pop("decided_by_key_id"))

        def _parse_decided_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                decided_at_type_0 = datetime.datetime.fromisoformat(data)

                return decided_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        decided_at = _parse_decided_at(d.pop("decided_at"))

        def _parse_rejection_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        rejection_reason = _parse_rejection_reason(d.pop("rejection_reason"))

        def _parse_external_ref(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        external_ref = _parse_external_ref(d.pop("external_ref"))

        def _parse_external_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        external_url = _parse_external_url(d.pop("external_url"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        batch = cls(
            id=id,
            project_id=project_id,
            request_id=request_id,
            allocation_id=allocation_id,
            data_source_id=data_source_id,
            spec_version_id=spec_version_id,
            received_at=received_at,
            status=status,
            delivered_count=delivered_count,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            contributor_count=contributor_count,
            spend=spend,
            currency=currency,
            attribute_counts=attribute_counts,
            artifacts=artifacts,
            reported_metrics=reported_metrics,
            delivered_count_from_files=delivered_count_from_files,
            spend_is_estimate=spend_is_estimate,
            quality=quality,
            override_reason=override_reason,
            notes=notes,
            decision_source=decision_source,
            decided_by=decided_by,
            decided_by_key_id=decided_by_key_id,
            decided_at=decided_at,
            rejection_reason=rejection_reason,
            external_ref=external_ref,
            external_url=external_url,
            created_at=created_at,
            updated_at=updated_at,
        )

        batch.additional_properties = d
        return batch

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
