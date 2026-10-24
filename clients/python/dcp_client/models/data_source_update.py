from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.data_source_update_license_type_type_0 import DataSourceUpdateLicenseTypeType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="DataSourceUpdate")


@_attrs_define
class DataSourceUpdate:
    """Only the fields you send are changed. `kind` and project can't change.

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        default_unit (None | str | Unset):
        license_type (DataSourceUpdateLicenseTypeType0 | None | Unset):
        consent_scope (None | str | Unset):
        rights_expires_at (datetime.date | None | Unset):
        pii_handling (None | str | Unset):
        notes (None | str | Unset):
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    default_unit: None | str | Unset = UNSET
    license_type: DataSourceUpdateLicenseTypeType0 | None | Unset = UNSET
    consent_scope: None | str | Unset = UNSET
    rights_expires_at: datetime.date | None | Unset = UNSET
    pii_handling: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        default_unit: None | str | Unset
        if isinstance(self.default_unit, Unset):
            default_unit = UNSET
        else:
            default_unit = self.default_unit

        license_type: None | str | Unset
        if isinstance(self.license_type, Unset):
            license_type = UNSET
        elif isinstance(self.license_type, DataSourceUpdateLicenseTypeType0):
            license_type = self.license_type.value
        else:
            license_type = self.license_type

        consent_scope: None | str | Unset
        if isinstance(self.consent_scope, Unset):
            consent_scope = UNSET
        else:
            consent_scope = self.consent_scope

        rights_expires_at: None | str | Unset
        if isinstance(self.rights_expires_at, Unset):
            rights_expires_at = UNSET
        elif isinstance(self.rights_expires_at, datetime.date):
            rights_expires_at = self.rights_expires_at.isoformat()
        else:
            rights_expires_at = self.rights_expires_at

        pii_handling: None | str | Unset
        if isinstance(self.pii_handling, Unset):
            pii_handling = UNSET
        else:
            pii_handling = self.pii_handling

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if default_unit is not UNSET:
            field_dict["default_unit"] = default_unit
        if license_type is not UNSET:
            field_dict["license_type"] = license_type
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

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_default_unit(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        default_unit = _parse_default_unit(d.pop("default_unit", UNSET))

        def _parse_license_type(data: object) -> DataSourceUpdateLicenseTypeType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                license_type_type_0 = DataSourceUpdateLicenseTypeType0(data)

                return license_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DataSourceUpdateLicenseTypeType0 | None | Unset, data)

        license_type = _parse_license_type(d.pop("license_type", UNSET))

        def _parse_consent_scope(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        consent_scope = _parse_consent_scope(d.pop("consent_scope", UNSET))

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

        def _parse_pii_handling(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pii_handling = _parse_pii_handling(d.pop("pii_handling", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        data_source_update = cls(
            name=name,
            description=description,
            default_unit=default_unit,
            license_type=license_type,
            consent_scope=consent_scope,
            rights_expires_at=rights_expires_at,
            pii_handling=pii_handling,
            notes=notes,
        )

        return data_source_update
