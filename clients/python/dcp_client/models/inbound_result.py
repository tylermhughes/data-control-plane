from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InboundResult")


@_attrs_define
class InboundResult:
    """
    Attributes:
        message_id (str):
        status (Literal['processed']):
        batch_id (str):
        batch_status (str):
        duplicate (bool): True if this message was already processed earlier.
    """

    message_id: str
    status: Literal["processed"]
    batch_id: str
    batch_status: str
    duplicate: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message_id = self.message_id

        status = self.status

        batch_id = self.batch_id

        batch_status = self.batch_status

        duplicate = self.duplicate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message_id": message_id,
                "status": status,
                "batch_id": batch_id,
                "batch_status": batch_status,
                "duplicate": duplicate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message_id = d.pop("message_id")

        status = cast(Literal["processed"], d.pop("status"))
        if status != "processed":
            raise ValueError(f"status must match const 'processed', got '{status}'")

        batch_id = d.pop("batch_id")

        batch_status = d.pop("batch_status")

        duplicate = d.pop("duplicate")

        inbound_result = cls(
            message_id=message_id,
            status=status,
            batch_id=batch_id,
            batch_status=batch_status,
            duplicate=duplicate,
        )

        inbound_result.additional_properties = d
        return inbound_result

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
