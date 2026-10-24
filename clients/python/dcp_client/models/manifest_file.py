from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ManifestFile")


@_attrs_define
class ManifestFile:
    """
    Attributes:
        batch_id (str):
        data_source_id (str):
        source_kind (str):
        spec_version_id (str):
        uri (str):
        format_ (str):
        sha256 (None | str):
        size_bytes (int | None):
        record_count (int | None):
    """

    batch_id: str
    data_source_id: str
    source_kind: str
    spec_version_id: str
    uri: str
    format_: str
    sha256: None | str
    size_bytes: int | None
    record_count: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        data_source_id = self.data_source_id

        source_kind = self.source_kind

        spec_version_id = self.spec_version_id

        uri = self.uri

        format_ = self.format_

        sha256: None | str
        sha256 = self.sha256

        size_bytes: int | None
        size_bytes = self.size_bytes

        record_count: int | None
        record_count = self.record_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "batch_id": batch_id,
                "data_source_id": data_source_id,
                "source_kind": source_kind,
                "spec_version_id": spec_version_id,
                "uri": uri,
                "format": format_,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "record_count": record_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id")

        data_source_id = d.pop("data_source_id")

        source_kind = d.pop("source_kind")

        spec_version_id = d.pop("spec_version_id")

        uri = d.pop("uri")

        format_ = d.pop("format")

        def _parse_sha256(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        sha256 = _parse_sha256(d.pop("sha256"))

        def _parse_size_bytes(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes"))

        def _parse_record_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        record_count = _parse_record_count(d.pop("record_count"))

        manifest_file = cls(
            batch_id=batch_id,
            data_source_id=data_source_id,
            source_kind=source_kind,
            spec_version_id=spec_version_id,
            uri=uri,
            format_=format_,
            sha256=sha256,
            size_bytes=size_bytes,
            record_count=record_count,
        )

        manifest_file.additional_properties = d
        return manifest_file

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
