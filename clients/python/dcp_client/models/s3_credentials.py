from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="S3Credentials")


@_attrs_define
class S3Credentials:
    """
    Attributes:
        access_key_id (str):
        secret_access_key (str):
        session_token (None | str | Unset):
    """

    access_key_id: str
    secret_access_key: str
    session_token: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        access_key_id = self.access_key_id

        secret_access_key = self.secret_access_key

        session_token: None | str | Unset
        if isinstance(self.session_token, Unset):
            session_token = UNSET
        else:
            session_token = self.session_token

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "access_key_id": access_key_id,
                "secret_access_key": secret_access_key,
            }
        )
        if session_token is not UNSET:
            field_dict["session_token"] = session_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_key_id = d.pop("access_key_id")

        secret_access_key = d.pop("secret_access_key")

        def _parse_session_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_token = _parse_session_token(d.pop("session_token", UNSET))

        s3_credentials = cls(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        )

        return s3_credentials
