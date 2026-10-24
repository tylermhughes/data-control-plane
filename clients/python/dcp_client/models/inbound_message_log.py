from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.inbound_message_log_status import InboundMessageLogStatus

T = TypeVar("T", bound="InboundMessageLog")


@_attrs_define
class InboundMessageLog:
    """
    Attributes:
        id (str):
        endpoint_id (str):
        message_id (None | str): The sender's `webhook-id` header.
        message_type (None | str):
        status (InboundMessageLogStatus):
        http_status (int):
        error (None | str):
        batch_id (None | str):
        received_at (datetime.datetime):
    """

    id: str
    endpoint_id: str
    message_id: None | str
    message_type: None | str
    status: InboundMessageLogStatus
    http_status: int
    error: None | str
    batch_id: None | str
    received_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        endpoint_id = self.endpoint_id

        message_id: None | str
        message_id = self.message_id

        message_type: None | str
        message_type = self.message_type

        status = self.status.value

        http_status = self.http_status

        error: None | str
        error = self.error

        batch_id: None | str
        batch_id = self.batch_id

        received_at = self.received_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "endpoint_id": endpoint_id,
                "message_id": message_id,
                "message_type": message_type,
                "status": status,
                "http_status": http_status,
                "error": error,
                "batch_id": batch_id,
                "received_at": received_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        endpoint_id = d.pop("endpoint_id")

        def _parse_message_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        message_id = _parse_message_id(d.pop("message_id"))

        def _parse_message_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        message_type = _parse_message_type(d.pop("message_type"))

        status = InboundMessageLogStatus(d.pop("status"))

        http_status = d.pop("http_status")

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        def _parse_batch_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        batch_id = _parse_batch_id(d.pop("batch_id"))

        received_at = datetime.datetime.fromisoformat(d.pop("received_at"))

        inbound_message_log = cls(
            id=id,
            endpoint_id=endpoint_id,
            message_id=message_id,
            message_type=message_type,
            status=status,
            http_status=http_status,
            error=error,
            batch_id=batch_id,
            received_at=received_at,
        )

        inbound_message_log.additional_properties = d
        return inbound_message_log

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
