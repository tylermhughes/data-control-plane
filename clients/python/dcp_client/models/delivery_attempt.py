from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DeliveryAttempt")


@_attrs_define
class DeliveryAttempt:
    """
    Attributes:
        at (datetime.datetime):
        status_code (int | None): Null if no response (timeout, refused).
        error (None | str):
        duration_ms (int):
        response_body (str): The first 1,000 characters of the response.
    """

    at: datetime.datetime
    status_code: int | None
    error: None | str
    duration_ms: int
    response_body: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        at = self.at.isoformat()

        status_code: int | None
        status_code = self.status_code

        error: None | str
        error = self.error

        duration_ms = self.duration_ms

        response_body = self.response_body

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "at": at,
                "status_code": status_code,
                "error": error,
                "duration_ms": duration_ms,
                "response_body": response_body,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        at = datetime.datetime.fromisoformat(d.pop("at"))

        def _parse_status_code(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        status_code = _parse_status_code(d.pop("status_code"))

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        duration_ms = d.pop("duration_ms")

        response_body = d.pop("response_body")

        delivery_attempt = cls(
            at=at,
            status_code=status_code,
            error=error,
            duration_ms=duration_ms,
            response_body=response_body,
        )

        delivery_attempt.additional_properties = d
        return delivery_attempt

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
