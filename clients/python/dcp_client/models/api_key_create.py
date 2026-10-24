from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.api_key_create_access import ApiKeyCreateAccess
from ..models.api_key_create_role import ApiKeyCreateRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyCreate")


@_attrs_define
class ApiKeyCreate:
    """
    Attributes:
        name (str):
        role (ApiKeyCreateRole): `admin`: everything, including keys and projects. `project`: only the project in
            `project_id`.
        access (ApiKeyCreateAccess | Unset): `read` can only look; `write` can change. Default:
            ApiKeyCreateAccess.WRITE.
        project_id (None | str | Unset): Required for `project` keys only.
    """

    name: str
    role: ApiKeyCreateRole
    access: ApiKeyCreateAccess | Unset = ApiKeyCreateAccess.WRITE
    project_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        role = self.role.value

        access: str | Unset = UNSET
        if not isinstance(self.access, Unset):
            access = self.access.value

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "role": role,
            }
        )
        if access is not UNSET:
            field_dict["access"] = access
        if project_id is not UNSET:
            field_dict["project_id"] = project_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        role = ApiKeyCreateRole(d.pop("role"))

        _access = d.pop("access", UNSET)
        access: ApiKeyCreateAccess | Unset
        if isinstance(_access, Unset):
            access = UNSET
        else:
            access = ApiKeyCreateAccess(_access)

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        api_key_create = cls(
            name=name,
            role=role,
            access=access,
            project_id=project_id,
        )

        return api_key_create
