from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="SpecVersionApprove")


@_attrs_define
class SpecVersionApprove:
    """
    Attributes:
        approved_by (str): Name of the person approving this version.
    """

    approved_by: str

    def to_dict(self) -> dict[str, Any]:
        approved_by = self.approved_by

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "approved_by": approved_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        approved_by = d.pop("approved_by")

        spec_version_approve = cls(
            approved_by=approved_by,
        )

        return spec_version_approve
