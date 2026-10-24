from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.data_source_create_kind import DataSourceCreateKind
from ..models.data_source_create_license_type import DataSourceCreateLicenseType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DataSourceCreate")


@_attrs_define
class DataSourceCreate:
    """
    Attributes:
        name (str): Unique within the project.
        kind (DataSourceCreateKind):
        license_type (DataSourceCreateLicenseType): Details go in `notes`.
        project_id (None | str | Unset): Project to create this in. Optional for project keys (defaults to their
            project); required for admin keys.
        description (str | Unset):  Default: ''.
        default_unit (None | str | Unset): Defaults to `tasks` for RL environments and `items` for everything else.
        consent_scope (str | Unset): What contributors agreed to. Default: ''.
        rights_expires_at (datetime.date | None | Unset): When the right to use it ends.
        pii_handling (str | Unset):  Default: ''.
        notes (str | Unset):  Default: ''.
    """

    name: str
    kind: DataSourceCreateKind
    license_type: DataSourceCreateLicenseType
    project_id: None | str | Unset = UNSET
    description: str | Unset = ""
    default_unit: None | str | Unset = UNSET
    consent_scope: str | Unset = ""
    rights_expires_at: datetime.date | None | Unset = UNSET
    pii_handling: str | Unset = ""
    notes: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        kind = self.kind.value

        license_type = self.license_type.value

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        description = self.description

        default_unit: None | str | Unset
        if isinstance(self.default_unit, Unset):
            default_unit = UNSET
        else:
            default_unit = self.default_unit

        consent_scope = self.consent_scope

        rights_expires_at: None | str | Unset
        if isinstance(self.rights_expires_at, Unset):
            rights_expires_at = UNSET
        elif isinstance(self.rights_expires_at, datetime.date):
            rights_expires_at = self.rights_expires_at.isoformat()
        else:
            rights_expires_at = self.rights_expires_at

        pii_handling = self.pii_handling

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "kind": kind,
                "license_type": license_type,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if description is not UNSET:
            field_dict["description"] = description
        if default_unit is not UNSET:
            field_dict["default_unit"] = default_unit
        if consent_scope is not UNSET:
            field_dict["consent_scope"] = consent_scope
        if rights_expires_at is not UNSET:
            field_dict["rights_expires_at"] = rights_expires_at
        if pii_handling is not UNSET:
            field_dict["pii_handling"] = pii_handling
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        kind = DataSourceCreateKind(d.pop("kind"))

        license_type = DataSourceCreateLicenseType(d.pop("license_type"))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        description = d.pop("description", UNSET)

        def _parse_default_unit(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        default_unit = _parse_default_unit(d.pop("default_unit", UNSET))

        consent_scope = d.pop("consent_scope", UNSET)

        def _parse_rights_expires_at(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                rights_expires_at_type_0 = datetime.date.fromisoformat(data)

                return rights_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        rights_expires_at = _parse_rights_expires_at(d.pop("rights_expires_at", UNSET))

        pii_handling = d.pop("pii_handling", UNSET)

        notes = d.pop("notes", UNSET)

        data_source_create = cls(
            name=name,
            kind=kind,
            license_type=license_type,
            project_id=project_id,
            description=description,
            default_unit=default_unit,
            consent_scope=consent_scope,
            rights_expires_at=rights_expires_at,
            pii_handling=pii_handling,
            notes=notes,
        )

        return data_source_create
