from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_delivery_status import WebhookDeliveryStatus

if TYPE_CHECKING:
    from ..models.delivery_attempt import DeliveryAttempt
    from ..models.webhook_delivery_payload import WebhookDeliveryPayload


T = TypeVar("T", bound="WebhookDelivery")


@_attrs_define
class WebhookDelivery:
    """
    Attributes:
        id (str):
        endpoint_id (str):
        project_id (None | str):
        event_id (str): Also sent as the `webhook-id` header.
        event_type (str):
        status (WebhookDeliveryStatus):
        attempt_count (int):
        next_attempt_at (datetime.datetime | None): When it will be tried next.
        delivered_at (datetime.datetime | None):
        attempts (list[DeliveryAttempt]):
        redelivery_of (None | str): The delivery this one re-sends, if any.
        payload (WebhookDeliveryPayload): The exact JSON body sent.
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    endpoint_id: str
    project_id: None | str
    event_id: str
    event_type: str
    status: WebhookDeliveryStatus
    attempt_count: int
    next_attempt_at: datetime.datetime | None
    delivered_at: datetime.datetime | None
    attempts: list[DeliveryAttempt]
    redelivery_of: None | str
    payload: WebhookDeliveryPayload
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        endpoint_id = self.endpoint_id

        project_id: None | str
        project_id = self.project_id

        event_id = self.event_id

        event_type = self.event_type

        status = self.status.value

        attempt_count = self.attempt_count

        next_attempt_at: None | str
        if isinstance(self.next_attempt_at, datetime.datetime):
            next_attempt_at = self.next_attempt_at.isoformat()
        else:
            next_attempt_at = self.next_attempt_at

        delivered_at: None | str
        if isinstance(self.delivered_at, datetime.datetime):
            delivered_at = self.delivered_at.isoformat()
        else:
            delivered_at = self.delivered_at

        attempts = []
        for attempts_item_data in self.attempts:
            attempts_item = attempts_item_data.to_dict()
            attempts.append(attempts_item)

        redelivery_of: None | str
        redelivery_of = self.redelivery_of

        payload = self.payload.to_dict()

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "endpoint_id": endpoint_id,
                "project_id": project_id,
                "event_id": event_id,
                "event_type": event_type,
                "status": status,
                "attempt_count": attempt_count,
                "next_attempt_at": next_attempt_at,
                "delivered_at": delivered_at,
                "attempts": attempts,
                "redelivery_of": redelivery_of,
                "payload": payload,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delivery_attempt import DeliveryAttempt  # noqa: PLC0415
        from ..models.webhook_delivery_payload import WebhookDeliveryPayload  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        endpoint_id = d.pop("endpoint_id")

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        event_id = d.pop("event_id")

        event_type = d.pop("event_type")

        status = WebhookDeliveryStatus(d.pop("status"))

        attempt_count = d.pop("attempt_count")

        def _parse_next_attempt_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_attempt_at_type_0 = datetime.datetime.fromisoformat(data)

                return next_attempt_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        next_attempt_at = _parse_next_attempt_at(d.pop("next_attempt_at"))

        def _parse_delivered_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                delivered_at_type_0 = datetime.datetime.fromisoformat(data)

                return delivered_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        delivered_at = _parse_delivered_at(d.pop("delivered_at"))

        attempts = []
        _attempts = d.pop("attempts")
        for attempts_item_data in _attempts:
            attempts_item = DeliveryAttempt.from_dict(attempts_item_data)

            attempts.append(attempts_item)

        def _parse_redelivery_of(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        redelivery_of = _parse_redelivery_of(d.pop("redelivery_of"))

        payload = WebhookDeliveryPayload.from_dict(d.pop("payload"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        webhook_delivery = cls(
            id=id,
            endpoint_id=endpoint_id,
            project_id=project_id,
            event_id=event_id,
            event_type=event_type,
            status=status,
            attempt_count=attempt_count,
            next_attempt_at=next_attempt_at,
            delivered_at=delivered_at,
            attempts=attempts,
            redelivery_of=redelivery_of,
            payload=payload,
            created_at=created_at,
            updated_at=updated_at,
        )

        webhook_delivery.additional_properties = d
        return webhook_delivery

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
