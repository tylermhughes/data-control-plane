from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.data_source_kind import DataSourceKind
from ..models.data_source_license_type import DataSourceLicenseType

T = TypeVar("T", bound="DataSource")


@_attrs_define
class DataSource:
    """
    Attributes:
        id (str):
        project_id (str):
        name (str):
        description (str):
        kind (DataSourceKind):
        default_unit (str): What one unit of data is, e.g. images, tasks, reviews, records, flags.
        license_type (DataSourceLicenseType):
        consent_scope (str):
        rights_expires_at (datetime.date | None):
        pii_handling (str):
        notes (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    name: str
    description: str
    kind: DataSourceKind
    default_unit: str
    license_type: DataSourceLicenseType
    consent_scope: str
    rights_expires_at: datetime.date | None
    pii_handling: str
    notes: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        name = self.name

        description = self.description

        kind = self.kind.value

        default_unit = self.default_unit

        license_type = self.license_type.value

        consent_scope = self.consent_scope

        rights_expires_at: None | str
        if isinstance(self.rights_expires_at, datetime.date):
            rights_expires_at = self.rights_expires_at.isoformat()
        else:
            rights_expires_at = self.rights_expires_at

        pii_handling = self.pii_handling

        notes = self.notes

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "name": name,
                "description": description,
                "kind": kind,
                "default_unit": default_unit,
                "license_type": license_type,
                "consent_scope": consent_scope,
                "rights_expires_at": rights_expires_at,
                "pii_handling": pii_handling,
                "notes": notes,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        name = d.pop("name")

        description = d.pop("description")

        kind = DataSourceKind(d.pop("kind"))

        default_unit = d.pop("default_unit")

        license_type = DataSourceLicenseType(d.pop("license_type"))

        consent_scope = d.pop("consent_scope")

        def _parse_rights_expires_at(data: object) -> datetime.date | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                rights_expires_at_type_0 = datetime.date.fromisoformat(data)

                return rights_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None, data)

        rights_expires_at = _parse_rights_expires_at(d.pop("rights_expires_at"))

        pii_handling = d.pop("pii_handling")

        notes = d.pop("notes")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        data_source = cls(
            id=id,
            project_id=project_id,
            name=name,
            description=description,
            kind=kind,
            default_unit=default_unit,
            license_type=license_type,
            consent_scope=consent_scope,
            rights_expires_at=rights_expires_at,
            pii_handling=pii_handling,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )

        data_source.additional_properties = d
        return data_source

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
