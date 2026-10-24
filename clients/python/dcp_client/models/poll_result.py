from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PollResult")


@_attrs_define
class PollResult:
    """
    Attributes:
        connector_id (str):
        files_listed (int):
        new_batches (list[str]):
        updated_files (list[str]): Files that changed since last seen.
        errors (list[str]):
    """

    connector_id: str
    files_listed: int
    new_batches: list[str]
    updated_files: list[str]
    errors: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        connector_id = self.connector_id

        files_listed = self.files_listed

        new_batches = self.new_batches

        updated_files = self.updated_files

        errors = self.errors

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connector_id": connector_id,
                "files_listed": files_listed,
                "new_batches": new_batches,
                "updated_files": updated_files,
                "errors": errors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        connector_id = d.pop("connector_id")

        files_listed = d.pop("files_listed")

        new_batches = cast(list[str], d.pop("new_batches"))

        updated_files = cast(list[str], d.pop("updated_files"))

        errors = cast(list[str], d.pop("errors"))

        poll_result = cls(
            connector_id=connector_id,
            files_listed=files_listed,
            new_batches=new_batches,
            updated_files=updated_files,
            errors=errors,
        )

        poll_result.additional_properties = d
        return poll_result

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
