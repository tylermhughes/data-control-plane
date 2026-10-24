from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_accept_attribute_counts_type_0 import BatchAcceptAttributeCountsType0


T = TypeVar("T", bound="BatchAccept")


@_attrs_define
class BatchAccept:
    """
    Attributes:
        accepted_count (int): Items kept. Can be less than delivered.
        attribute_counts (BatchAcceptAttributeCountsType0 | None | Unset): Accepted items per attribute value, e.g.
            {"package_type": {"shrink_wrapped": 3300}}. Optional.
        decided_by (str | Unset): Who decided. Default: ''.
        override_reason (None | str | Unset): Required to accept a batch whose checks failed: why it's accepted anyway.
    """

    accepted_count: int
    attribute_counts: BatchAcceptAttributeCountsType0 | None | Unset = UNSET
    decided_by: str | Unset = ""
    override_reason: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.batch_accept_attribute_counts_type_0 import BatchAcceptAttributeCountsType0  # noqa: PLC0415

        accepted_count = self.accepted_count

        attribute_counts: dict[str, Any] | None | Unset
        if isinstance(self.attribute_counts, Unset):
            attribute_counts = UNSET
        elif isinstance(self.attribute_counts, BatchAcceptAttributeCountsType0):
            attribute_counts = self.attribute_counts.to_dict()
        else:
            attribute_counts = self.attribute_counts

        decided_by = self.decided_by

        override_reason: None | str | Unset
        if isinstance(self.override_reason, Unset):
            override_reason = UNSET
        else:
            override_reason = self.override_reason

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "accepted_count": accepted_count,
            }
        )
        if attribute_counts is not UNSET:
            field_dict["attribute_counts"] = attribute_counts
        if decided_by is not UNSET:
            field_dict["decided_by"] = decided_by
        if override_reason is not UNSET:
            field_dict["override_reason"] = override_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_accept_attribute_counts_type_0 import BatchAcceptAttributeCountsType0  # noqa: PLC0415

        d = dict(src_dict)
        accepted_count = d.pop("accepted_count")

        def _parse_attribute_counts(data: object) -> BatchAcceptAttributeCountsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                attribute_counts_type_0 = BatchAcceptAttributeCountsType0.from_dict(data)

                return attribute_counts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BatchAcceptAttributeCountsType0 | None | Unset, data)

        attribute_counts = _parse_attribute_counts(d.pop("attribute_counts", UNSET))

        decided_by = d.pop("decided_by", UNSET)

        def _parse_override_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        override_reason = _parse_override_reason(d.pop("override_reason", UNSET))

        batch_accept = cls(
            accepted_count=accepted_count,
            attribute_counts=attribute_counts,
            decided_by=decided_by,
            override_reason=override_reason,
        )

        return batch_accept
