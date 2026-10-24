from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_created_access import ApiKeyCreatedAccess
from ..models.api_key_created_role import ApiKeyCreatedRole

T = TypeVar("T", bound="ApiKeyCreated")


@_attrs_define
class ApiKeyCreated:
    """
    Attributes:
        id (str):
        name (str):
        key_prefix (str): First characters of the key, to tell keys apart.
        role (ApiKeyCreatedRole):
        access (ApiKeyCreatedAccess):
        project_id (None | str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        last_used_at (datetime.datetime | None): Approximate: updated at most once a minute.
        revoked_at (datetime.datetime | None):
        secret (str): The full API key. Shown only once: store it now, it cannot be retrieved later.
    """

    id: str
    name: str
    key_prefix: str
    role: ApiKeyCreatedRole
    access: ApiKeyCreatedAccess
    project_id: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_used_at: datetime.datetime | None
    revoked_at: datetime.datetime | None
    secret: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        key_prefix = self.key_prefix

        role = self.role.value

        access = self.access.value

        project_id: None | str
        project_id = self.project_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        revoked_at: None | str
        if isinstance(self.revoked_at, datetime.datetime):
            revoked_at = self.revoked_at.isoformat()
        else:
            revoked_at = self.revoked_at

        secret = self.secret

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "key_prefix": key_prefix,
                "role": role,
                "access": access,
                "project_id": project_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "last_used_at": last_used_at,
                "revoked_at": revoked_at,
                "secret": secret,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        key_prefix = d.pop("key_prefix")

        role = ApiKeyCreatedRole(d.pop("role"))

        access = ApiKeyCreatedAccess(d.pop("access"))

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_last_used_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

        def _parse_revoked_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                revoked_at_type_0 = datetime.datetime.fromisoformat(data)

                return revoked_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        revoked_at = _parse_revoked_at(d.pop("revoked_at"))

        secret = d.pop("secret")

        api_key_created = cls(
            id=id,
            name=name,
            key_prefix=key_prefix,
            role=role,
            access=access,
            project_id=project_id,
            created_at=created_at,
            updated_at=updated_at,
            last_used_at=last_used_at,
            revoked_at=revoked_at,
            secret=secret,
        )

        api_key_created.additional_properties = d
        return api_key_created

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
