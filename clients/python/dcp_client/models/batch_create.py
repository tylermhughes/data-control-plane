from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.artifact import Artifact
    from ..models.batch_create_reported_metrics import BatchCreateReportedMetrics
    from ..models.external_decision import ExternalDecision


T = TypeVar("T", bound="BatchCreate")


@_attrs_define
class BatchCreate:
    """
    Attributes:
        allocation_id (str): Must be active.
        received_at (datetime.datetime | None | Unset): Defaults to now.
        delivered_count (int | None | Unset): Items delivered. If left out (only allowed when files are listed), DCP
            fills it in from the files' record count after the checks.
        spend (float | None | str | Unset): What this delivery cost. If left out, DCP estimates it as the allocation's
            quoted rate × delivered_count (`spend_is_estimate: true`) until it's set.
        currency (None | str | Unset): Defaults to the allocation's currency.
        contributor_count (int | None | Unset): People who worked on it.
        artifacts (list[Artifact] | Unset): Delivered files. If any are listed, DCP checks them automatically.
        reported_metrics (BatchCreateReportedMetrics | Unset): Values DCP can't measure from the files, reported by the
            source, e.g. {"agreement": 0.91} or {"agreement[package_type=shrink_wrapped]": 0.84}. Used by acceptance rules;
            measured values win over reported ones.
        notes (str | Unset):  Default: ''.
        external_ref (None | str | Unset): The source's own id for this delivery. Unique per data source: sending the
            same one again updates that batch instead of creating a new one.
        external_url (None | str | Unset):
        decision (ExternalDecision | None | Unset): Include to import a batch already accepted or rejected elsewhere.
    """

    allocation_id: str
    received_at: datetime.datetime | None | Unset = UNSET
    delivered_count: int | None | Unset = UNSET
    spend: float | None | str | Unset = UNSET
    currency: None | str | Unset = UNSET
    contributor_count: int | None | Unset = UNSET
    artifacts: list[Artifact] | Unset = UNSET
    reported_metrics: BatchCreateReportedMetrics | Unset = UNSET
    notes: str | Unset = ""
    external_ref: None | str | Unset = UNSET
    external_url: None | str | Unset = UNSET
    decision: ExternalDecision | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.external_decision import ExternalDecision  # noqa: PLC0415

        allocation_id = self.allocation_id

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

        currency: None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        contributor_count: int | None | Unset
        if isinstance(self.contributor_count, Unset):
            contributor_count = UNSET
        else:
            contributor_count = self.contributor_count

        artifacts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.artifacts, Unset):
            artifacts = []
            for artifacts_item_data in self.artifacts:
                artifacts_item = artifacts_item_data.to_dict()
                artifacts.append(artifacts_item)

        reported_metrics: dict[str, Any] | Unset = UNSET
        if not isinstance(self.reported_metrics, Unset):
            reported_metrics = self.reported_metrics.to_dict()

        notes = self.notes

        external_ref: None | str | Unset
        if isinstance(self.external_ref, Unset):
            external_ref = UNSET
        else:
            external_ref = self.external_ref

        external_url: None | str | Unset
        if isinstance(self.external_url, Unset):
            external_url = UNSET
        else:
            external_url = self.external_url

        decision: dict[str, Any] | None | Unset
        if isinstance(self.decision, Unset):
            decision = UNSET
        elif isinstance(self.decision, ExternalDecision):
            decision = self.decision.to_dict()
        else:
            decision = self.decision

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "allocation_id": allocation_id,
            }
        )
        if received_at is not UNSET:
            field_dict["received_at"] = received_at
        if delivered_count is not UNSET:
            field_dict["delivered_count"] = delivered_count
        if spend is not UNSET:
            field_dict["spend"] = spend
        if currency is not UNSET:
            field_dict["currency"] = currency
        if contributor_count is not UNSET:
            field_dict["contributor_count"] = contributor_count
        if artifacts is not UNSET:
            field_dict["artifacts"] = artifacts
        if reported_metrics is not UNSET:
            field_dict["reported_metrics"] = reported_metrics
        if notes is not UNSET:
            field_dict["notes"] = notes
        if external_ref is not UNSET:
            field_dict["external_ref"] = external_ref
        if external_url is not UNSET:
            field_dict["external_url"] = external_url
        if decision is not UNSET:
            field_dict["decision"] = decision

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.artifact import Artifact  # noqa: PLC0415
        from ..models.batch_create_reported_metrics import BatchCreateReportedMetrics  # noqa: PLC0415
        from ..models.external_decision import ExternalDecision  # noqa: PLC0415

        d = dict(src_dict)
        allocation_id = d.pop("allocation_id")

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

        def _parse_currency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_contributor_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        contributor_count = _parse_contributor_count(d.pop("contributor_count", UNSET))

        _artifacts = d.pop("artifacts", UNSET)
        artifacts: list[Artifact] | Unset = UNSET
        if _artifacts is not UNSET:
            artifacts = []
            for artifacts_item_data in _artifacts:
                artifacts_item = Artifact.from_dict(artifacts_item_data)

                artifacts.append(artifacts_item)

        _reported_metrics = d.pop("reported_metrics", UNSET)
        reported_metrics: BatchCreateReportedMetrics | Unset
        if isinstance(_reported_metrics, Unset):
            reported_metrics = UNSET
        else:
            reported_metrics = BatchCreateReportedMetrics.from_dict(_reported_metrics)

        notes = d.pop("notes", UNSET)

        def _parse_external_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_ref = _parse_external_ref(d.pop("external_ref", UNSET))

        def _parse_external_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_url = _parse_external_url(d.pop("external_url", UNSET))

        def _parse_decision(data: object) -> ExternalDecision | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                decision_type_0 = ExternalDecision.from_dict(data)

                return decision_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ExternalDecision | None | Unset, data)

        decision = _parse_decision(d.pop("decision", UNSET))

        batch_create = cls(
            allocation_id=allocation_id,
            received_at=received_at,
            delivered_count=delivered_count,
            spend=spend,
            currency=currency,
            contributor_count=contributor_count,
            artifacts=artifacts,
            reported_metrics=reported_metrics,
            notes=notes,
            external_ref=external_ref,
            external_url=external_url,
            decision=decision,
        )

        return batch_create
