from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ConnectorObject")


@_attrs_define
class ConnectorObject:
    """
    Attributes:
        key (str):
        size_bytes (int):
        etag (str):
        last_modified (datetime.datetime):
        batch_id (None | str):
        error (None | str): Why this file didn't become a batch, if it didn't.
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    key: str
    size_bytes: int
    etag: str
    last_modified: datetime.datetime
    batch_id: None | str
    error: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        size_bytes = self.size_bytes

        etag = self.etag

        last_modified = self.last_modified.isoformat()

        batch_id: None | str
        batch_id = self.batch_id

        error: None | str
        error = self.error

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
                "size_bytes": size_bytes,
                "etag": etag,
                "last_modified": last_modified,
                "batch_id": batch_id,
                "error": error,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        size_bytes = d.pop("size_bytes")

        etag = d.pop("etag")

        last_modified = datetime.datetime.fromisoformat(d.pop("last_modified"))

        def _parse_batch_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        batch_id = _parse_batch_id(d.pop("batch_id"))

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        connector_object = cls(
            key=key,
            size_bytes=size_bytes,
            etag=etag,
            last_modified=last_modified,
            batch_id=batch_id,
            error=error,
            created_at=created_at,
            updated_at=updated_at,
        )

        connector_object.additional_properties = d
        return connector_object

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
