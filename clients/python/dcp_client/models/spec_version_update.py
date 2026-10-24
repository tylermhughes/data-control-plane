from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acceptance_rule import AcceptanceRule
    from ..models.attribute import Attribute
    from ..models.spec_version_update_coverage_targets_type_0 import SpecVersionUpdateCoverageTargetsType0
    from ..models.spec_version_update_record_schema_type_0 import SpecVersionUpdateRecordSchemaType0


T = TypeVar("T", bound="SpecVersionUpdate")


@_attrs_define
class SpecVersionUpdate:
    """For drafts only. Fields you send replace the draft's; the rest are kept.

    Attributes:
        guidelines (None | str | Unset):
        attributes (list[Attribute] | None | Unset):
        coverage_targets (None | SpecVersionUpdateCoverageTargetsType0 | Unset):
        coverage_tolerance (float | None | Unset):
        acceptance_rules (list[AcceptanceRule] | None | Unset):
        record_schema (None | SpecVersionUpdateRecordSchemaType0 | Unset):
        change_note (None | str | Unset):
    """

    guidelines: None | str | Unset = UNSET
    attributes: list[Attribute] | None | Unset = UNSET
    coverage_targets: None | SpecVersionUpdateCoverageTargetsType0 | Unset = UNSET
    coverage_tolerance: float | None | Unset = UNSET
    acceptance_rules: list[AcceptanceRule] | None | Unset = UNSET
    record_schema: None | SpecVersionUpdateRecordSchemaType0 | Unset = UNSET
    change_note: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.spec_version_update_coverage_targets_type_0 import SpecVersionUpdateCoverageTargetsType0  # noqa: PLC0415
        from ..models.spec_version_update_record_schema_type_0 import SpecVersionUpdateRecordSchemaType0  # noqa: PLC0415

        guidelines: None | str | Unset
        if isinstance(self.guidelines, Unset):
            guidelines = UNSET
        else:
            guidelines = self.guidelines

        attributes: list[dict[str, Any]] | None | Unset
        if isinstance(self.attributes, Unset):
            attributes = UNSET
        elif isinstance(self.attributes, list):
            attributes = []
            for attributes_type_0_item_data in self.attributes:
                attributes_type_0_item = attributes_type_0_item_data.to_dict()
                attributes.append(attributes_type_0_item)

        else:
            attributes = self.attributes

        coverage_targets: dict[str, Any] | None | Unset
        if isinstance(self.coverage_targets, Unset):
            coverage_targets = UNSET
        elif isinstance(self.coverage_targets, SpecVersionUpdateCoverageTargetsType0):
            coverage_targets = self.coverage_targets.to_dict()
        else:
            coverage_targets = self.coverage_targets

        coverage_tolerance: float | None | Unset
        if isinstance(self.coverage_tolerance, Unset):
            coverage_tolerance = UNSET
        else:
            coverage_tolerance = self.coverage_tolerance

        acceptance_rules: list[dict[str, Any]] | None | Unset
        if isinstance(self.acceptance_rules, Unset):
            acceptance_rules = UNSET
        elif isinstance(self.acceptance_rules, list):
            acceptance_rules = []
            for acceptance_rules_type_0_item_data in self.acceptance_rules:
                acceptance_rules_type_0_item = acceptance_rules_type_0_item_data.to_dict()
                acceptance_rules.append(acceptance_rules_type_0_item)

        else:
            acceptance_rules = self.acceptance_rules

        record_schema: dict[str, Any] | None | Unset
        if isinstance(self.record_schema, Unset):
            record_schema = UNSET
        elif isinstance(self.record_schema, SpecVersionUpdateRecordSchemaType0):
            record_schema = self.record_schema.to_dict()
        else:
            record_schema = self.record_schema

        change_note: None | str | Unset
        if isinstance(self.change_note, Unset):
            change_note = UNSET
        else:
            change_note = self.change_note

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if guidelines is not UNSET:
            field_dict["guidelines"] = guidelines
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if coverage_targets is not UNSET:
            field_dict["coverage_targets"] = coverage_targets
        if coverage_tolerance is not UNSET:
            field_dict["coverage_tolerance"] = coverage_tolerance
        if acceptance_rules is not UNSET:
            field_dict["acceptance_rules"] = acceptance_rules
        if record_schema is not UNSET:
            field_dict["record_schema"] = record_schema
        if change_note is not UNSET:
            field_dict["change_note"] = change_note

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acceptance_rule import AcceptanceRule  # noqa: PLC0415
        from ..models.attribute import Attribute  # noqa: PLC0415
        from ..models.spec_version_update_coverage_targets_type_0 import SpecVersionUpdateCoverageTargetsType0  # noqa: PLC0415
        from ..models.spec_version_update_record_schema_type_0 import SpecVersionUpdateRecordSchemaType0  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_guidelines(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        guidelines = _parse_guidelines(d.pop("guidelines", UNSET))

        def _parse_attributes(data: object) -> list[Attribute] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                attributes_type_0 = []
                _attributes_type_0 = data
                for attributes_type_0_item_data in _attributes_type_0:
                    attributes_type_0_item = Attribute.from_dict(attributes_type_0_item_data)

                    attributes_type_0.append(attributes_type_0_item)

                return attributes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Attribute] | None | Unset, data)

        attributes = _parse_attributes(d.pop("attributes", UNSET))

        def _parse_coverage_targets(data: object) -> None | SpecVersionUpdateCoverageTargetsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                coverage_targets_type_0 = SpecVersionUpdateCoverageTargetsType0.from_dict(data)

                return coverage_targets_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SpecVersionUpdateCoverageTargetsType0 | Unset, data)

        coverage_targets = _parse_coverage_targets(d.pop("coverage_targets", UNSET))

        def _parse_coverage_tolerance(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        coverage_tolerance = _parse_coverage_tolerance(d.pop("coverage_tolerance", UNSET))

        def _parse_acceptance_rules(data: object) -> list[AcceptanceRule] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                acceptance_rules_type_0 = []
                _acceptance_rules_type_0 = data
                for acceptance_rules_type_0_item_data in _acceptance_rules_type_0:
                    acceptance_rules_type_0_item = AcceptanceRule.from_dict(acceptance_rules_type_0_item_data)

                    acceptance_rules_type_0.append(acceptance_rules_type_0_item)

                return acceptance_rules_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[AcceptanceRule] | None | Unset, data)

        acceptance_rules = _parse_acceptance_rules(d.pop("acceptance_rules", UNSET))

        def _parse_record_schema(data: object) -> None | SpecVersionUpdateRecordSchemaType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                record_schema_type_0 = SpecVersionUpdateRecordSchemaType0.from_dict(data)

                return record_schema_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SpecVersionUpdateRecordSchemaType0 | Unset, data)

        record_schema = _parse_record_schema(d.pop("record_schema", UNSET))

        def _parse_change_note(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        change_note = _parse_change_note(d.pop("change_note", UNSET))

        spec_version_update = cls(
            guidelines=guidelines,
            attributes=attributes,
            coverage_targets=coverage_targets,
            coverage_tolerance=coverage_tolerance,
            acceptance_rules=acceptance_rules,
            record_schema=record_schema,
            change_note=change_note,
        )

        return spec_version_update
