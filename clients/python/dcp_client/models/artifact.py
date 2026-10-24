from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.artifact_format import ArtifactFormat
from ..types import UNSET, Unset

T = TypeVar("T", bound="Artifact")


@_attrs_define
class Artifact:
    """A pointer to delivered data. DCP stores the pointer, not the data.

    Attributes:
        uri (str): Where the file is, e.g. s3://bucket/path/part-1.jsonl
        format_ (ArtifactFormat):
        sha256 (None | str | Unset):
        size_bytes (int | None | Unset):
        record_count (int | None | Unset):
    """

    uri: str
    format_: ArtifactFormat
    sha256: None | str | Unset = UNSET
    size_bytes: int | None | Unset = UNSET
    record_count: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        uri = self.uri

        format_ = self.format_.value

        sha256: None | str | Unset
        if isinstance(self.sha256, Unset):
            sha256 = UNSET
        else:
            sha256 = self.sha256

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes

        record_count: int | None | Unset
        if isinstance(self.record_count, Unset):
            record_count = UNSET
        else:
            record_count = self.record_count

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "uri": uri,
                "format": format_,
            }
        )
        if sha256 is not UNSET:
            field_dict["sha256"] = sha256
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes
        if record_count is not UNSET:
            field_dict["record_count"] = record_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        uri = d.pop("uri")

        format_ = ArtifactFormat(d.pop("format"))

        def _parse_sha256(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sha256 = _parse_sha256(d.pop("sha256", UNSET))

        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes", UNSET))

        def _parse_record_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        record_count = _parse_record_count(d.pop("record_count", UNSET))

        artifact = cls(
            uri=uri,
            format_=format_,
            sha256=sha256,
            size_bytes=size_bytes,
            record_count=record_count,
        )

        return artifact
