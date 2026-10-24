from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchReject")


@_attrs_define
class BatchReject:
    """
    Attributes:
        reason (str):
        decided_by (str | Unset):  Default: ''.
    """

    reason: str
    decided_by: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        reason = self.reason

        decided_by = self.decided_by

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "reason": reason,
            }
        )
        if decided_by is not UNSET:
            field_dict["decided_by"] = decided_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reason = d.pop("reason")

        decided_by = d.pop("decided_by", UNSET)

        batch_reject = cls(
            reason=reason,
            decided_by=decided_by,
        )

        return batch_reject
