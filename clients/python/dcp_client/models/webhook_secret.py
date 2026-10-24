from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WebhookSecret")


@_attrs_define
class WebhookSecret:
    """
    Attributes:
        secret (str): Use this to verify the `webhook-signature` header.
        previous_secret_valid_until (datetime.datetime | None): After a rotation, messages are also signed with the
            previous secret until this time, so receivers can switch over without missing any.
    """

    secret: str
    previous_secret_valid_until: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        secret = self.secret

        previous_secret_valid_until: None | str
        if isinstance(self.previous_secret_valid_until, datetime.datetime):
            previous_secret_valid_until = self.previous_secret_valid_until.isoformat()
        else:
            previous_secret_valid_until = self.previous_secret_valid_until

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "secret": secret,
                "previous_secret_valid_until": previous_secret_valid_until,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        secret = d.pop("secret")

        def _parse_previous_secret_valid_until(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                previous_secret_valid_until_type_0 = datetime.datetime.fromisoformat(data)

                return previous_secret_valid_until_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        previous_secret_valid_until = _parse_previous_secret_valid_until(d.pop("previous_secret_valid_until"))

        webhook_secret = cls(
            secret=secret,
            previous_secret_valid_until=previous_secret_valid_until,
        )

        webhook_secret.additional_properties = d
        return webhook_secret

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
