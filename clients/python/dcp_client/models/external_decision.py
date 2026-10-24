from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.external_decision_status import ExternalDecisionStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.external_decision_attribute_counts_type_0 import ExternalDecisionAttributeCountsType0


T = TypeVar("T", bound="ExternalDecision")


@_attrs_define
class ExternalDecision:
    """For batches already accepted or rejected outside DCP (a vendor's QA, Labelbox, ...).

    Attributes:
        status (ExternalDecisionStatus):
        decided_by (str): The system or person that decided, e.g. `labelbox`, `surge`.
        accepted_count (int | None | Unset): Required when accepted.
        attribute_counts (ExternalDecisionAttributeCountsType0 | None | Unset):
        reason (None | str | Unset): Required when rejected.
        decided_at (datetime.datetime | None | Unset): When it was decided. Defaults to now.
    """

    status: ExternalDecisionStatus
    decided_by: str
    accepted_count: int | None | Unset = UNSET
    attribute_counts: ExternalDecisionAttributeCountsType0 | None | Unset = UNSET
    reason: None | str | Unset = UNSET
    decided_at: datetime.datetime | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.external_decision_attribute_counts_type_0 import ExternalDecisionAttributeCountsType0  # noqa: PLC0415

        status = self.status.value

        decided_by = self.decided_by

        accepted_count: int | None | Unset
        if isinstance(self.accepted_count, Unset):
            accepted_count = UNSET
        else:
            accepted_count = self.accepted_count

        attribute_counts: dict[str, Any] | None | Unset
        if isinstance(self.attribute_counts, Unset):
            attribute_counts = UNSET
        elif isinstance(self.attribute_counts, ExternalDecisionAttributeCountsType0):
            attribute_counts = self.attribute_counts.to_dict()
        else:
            attribute_counts = self.attribute_counts

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        decided_at: None | str | Unset
        if isinstance(self.decided_at, Unset):
            decided_at = UNSET
        elif isinstance(self.decided_at, datetime.datetime):
            decided_at = self.decided_at.isoformat()
        else:
            decided_at = self.decided_at

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "status": status,
                "decided_by": decided_by,
            }
        )
        if accepted_count is not UNSET:
            field_dict["accepted_count"] = accepted_count
        if attribute_counts is not UNSET:
            field_dict["attribute_counts"] = attribute_counts
        if reason is not UNSET:
            field_dict["reason"] = reason
        if decided_at is not UNSET:
            field_dict["decided_at"] = decided_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.external_decision_attribute_counts_type_0 import ExternalDecisionAttributeCountsType0  # noqa: PLC0415

        d = dict(src_dict)
        status = ExternalDecisionStatus(d.pop("status"))

        decided_by = d.pop("decided_by")

        def _parse_accepted_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        accepted_count = _parse_accepted_count(d.pop("accepted_count", UNSET))

        def _parse_attribute_counts(data: object) -> ExternalDecisionAttributeCountsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                attribute_counts_type_0 = ExternalDecisionAttributeCountsType0.from_dict(data)

                return attribute_counts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ExternalDecisionAttributeCountsType0 | None | Unset, data)

        attribute_counts = _parse_attribute_counts(d.pop("attribute_counts", UNSET))

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        def _parse_decided_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                decided_at_type_0 = datetime.datetime.fromisoformat(data)

                return decided_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        decided_at = _parse_decided_at(d.pop("decided_at", UNSET))

        external_decision = cls(
            status=status,
            decided_by=decided_by,
            accepted_count=accepted_count,
            attribute_counts=attribute_counts,
            reason=reason,
            decided_at=decided_at,
        )

        return external_decision
