from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.check_name import CheckName
from ..models.check_outcome import CheckOutcome

if TYPE_CHECKING:
    from ..models.check_details import CheckDetails


T = TypeVar("T", bound="Check")


@_attrs_define
class Check:
    """
    Attributes:
        name (CheckName):
        outcome (CheckOutcome):
        summary (str):
        details (CheckDetails): Examples, per-file results, rule results, ...
    """

    name: CheckName
    outcome: CheckOutcome
    summary: str
    details: CheckDetails
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name.value

        outcome = self.outcome.value

        summary = self.summary

        details = self.details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "outcome": outcome,
                "summary": summary,
                "details": details,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.check_details import CheckDetails  # noqa: PLC0415

        d = dict(src_dict)
        name = CheckName(d.pop("name"))

        outcome = CheckOutcome(d.pop("outcome"))

        summary = d.pop("summary")

        details = CheckDetails.from_dict(d.pop("details"))

        check = cls(
            name=name,
            outcome=outcome,
            summary=summary,
            details=details,
        )

        check.additional_properties = d
        return check

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
