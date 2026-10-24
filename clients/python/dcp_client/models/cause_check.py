from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cause_check_cause import CauseCheckCause
from ..models.cause_check_status import CauseCheckStatus

T = TypeVar("T", bound="CauseCheck")


@_attrs_define
class CauseCheck:
    """
    Attributes:
        cause (CauseCheckCause):
        status (CauseCheckStatus):
        summary (str):
    """

    cause: CauseCheckCause
    status: CauseCheckStatus
    summary: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cause = self.cause.value

        status = self.status.value

        summary = self.summary

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cause": cause,
                "status": status,
                "summary": summary,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cause = CauseCheckCause(d.pop("cause"))

        status = CauseCheckStatus(d.pop("status"))

        summary = d.pop("summary")

        cause_check = cls(
            cause=cause,
            status=status,
            summary=summary,
        )

        cause_check.additional_properties = d
        return cause_check

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
