from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.spec_content import SpecContent


T = TypeVar("T", bound="SpecCreate")


@_attrs_define
class SpecCreate:
    """
    Attributes:
        name (str): Unique within the project.
        project_id (None | str | Unset): Project to create this in. Optional for project keys (defaults to their
            project); required for admin keys.
        description (str | Unset):  Default: ''.
        first_version (SpecContent | Unset): The content of a spec version. Cross-checked: targets and rules must use
            real attributes.
    """

    name: str
    project_id: None | str | Unset = UNSET
    description: str | Unset = ""
    first_version: SpecContent | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        description = self.description

        first_version: dict[str, Any] | Unset = UNSET
        if not isinstance(self.first_version, Unset):
            first_version = self.first_version.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if description is not UNSET:
            field_dict["description"] = description
        if first_version is not UNSET:
            field_dict["first_version"] = first_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.spec_content import SpecContent  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        description = d.pop("description", UNSET)

        _first_version = d.pop("first_version", UNSET)
        first_version: SpecContent | Unset
        if isinstance(_first_version, Unset):
            first_version = UNSET
        else:
            first_version = SpecContent.from_dict(_first_version)

        spec_create = cls(
            name=name,
            project_id=project_id,
            description=description,
            first_version=first_version,
        )

        return spec_create
