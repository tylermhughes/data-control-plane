from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acceptance_rule import AcceptanceRule
    from ..models.attribute import Attribute
    from ..models.spec_content_coverage_targets import SpecContentCoverageTargets
    from ..models.spec_content_record_schema_type_0 import SpecContentRecordSchemaType0


T = TypeVar("T", bound="SpecContent")


@_attrs_define
class SpecContent:
    """The content of a spec version. Cross-checked: targets and rules must use real attributes.

    Attributes:
        guidelines (str | Unset): Instructions, plain text or Markdown. Default: ''.
        attributes (list[Attribute] | Unset):
        coverage_targets (SpecContentCoverageTargets | Unset): Target share of items per attribute value, as fractions
            (0.35 = 35%). Each attribute's shares must add up to 1 or less.
        coverage_tolerance (float | Unset): How far below its target share a value may fall before it is flagged (0.05 =
            5 points: target 35%, actual 29% is flagged; 33% is not). Default: 0.05.
        acceptance_rules (list[AcceptanceRule] | Unset):
        record_schema (None | SpecContentRecordSchemaType0 | Unset): Optional JSON Schema for each record. Checked
            against files from M6.
        change_note (str | Unset): What changed in this version. Default: ''.
    """

    guidelines: str | Unset = ""
    attributes: list[Attribute] | Unset = UNSET
    coverage_targets: SpecContentCoverageTargets | Unset = UNSET
    coverage_tolerance: float | Unset = 0.05
    acceptance_rules: list[AcceptanceRule] | Unset = UNSET
    record_schema: None | SpecContentRecordSchemaType0 | Unset = UNSET
    change_note: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        from ..models.spec_content_record_schema_type_0 import SpecContentRecordSchemaType0  # noqa: PLC0415

        guidelines = self.guidelines

        attributes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        coverage_targets: dict[str, Any] | Unset = UNSET
        if not isinstance(self.coverage_targets, Unset):
            coverage_targets = self.coverage_targets.to_dict()

        coverage_tolerance = self.coverage_tolerance

        acceptance_rules: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.acceptance_rules, Unset):
            acceptance_rules = []
            for acceptance_rules_item_data in self.acceptance_rules:
                acceptance_rules_item = acceptance_rules_item_data.to_dict()
                acceptance_rules.append(acceptance_rules_item)

        record_schema: dict[str, Any] | None | Unset
        if isinstance(self.record_schema, Unset):
            record_schema = UNSET
        elif isinstance(self.record_schema, SpecContentRecordSchemaType0):
            record_schema = self.record_schema.to_dict()
        else:
            record_schema = self.record_schema

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
        from ..models.spec_content_coverage_targets import SpecContentCoverageTargets  # noqa: PLC0415
        from ..models.spec_content_record_schema_type_0 import SpecContentRecordSchemaType0  # noqa: PLC0415

        d = dict(src_dict)
        guidelines = d.pop("guidelines", UNSET)

        _attributes = d.pop("attributes", UNSET)
        attributes: list[Attribute] | Unset = UNSET
        if _attributes is not UNSET:
            attributes = []
            for attributes_item_data in _attributes:
                attributes_item = Attribute.from_dict(attributes_item_data)

                attributes.append(attributes_item)

        _coverage_targets = d.pop("coverage_targets", UNSET)
        coverage_targets: SpecContentCoverageTargets | Unset
        if isinstance(_coverage_targets, Unset):
            coverage_targets = UNSET
        else:
            coverage_targets = SpecContentCoverageTargets.from_dict(_coverage_targets)

        coverage_tolerance = d.pop("coverage_tolerance", UNSET)

        _acceptance_rules = d.pop("acceptance_rules", UNSET)
        acceptance_rules: list[AcceptanceRule] | Unset = UNSET
        if _acceptance_rules is not UNSET:
            acceptance_rules = []
            for acceptance_rules_item_data in _acceptance_rules:
                acceptance_rules_item = AcceptanceRule.from_dict(acceptance_rules_item_data)

                acceptance_rules.append(acceptance_rules_item)

        def _parse_record_schema(data: object) -> None | SpecContentRecordSchemaType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                record_schema_type_0 = SpecContentRecordSchemaType0.from_dict(data)

                return record_schema_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SpecContentRecordSchemaType0 | Unset, data)

        record_schema = _parse_record_schema(d.pop("record_schema", UNSET))

        change_note = d.pop("change_note", UNSET)

        spec_content = cls(
            guidelines=guidelines,
            attributes=attributes,
            coverage_targets=coverage_targets,
            coverage_tolerance=coverage_tolerance,
            acceptance_rules=acceptance_rules,
            record_schema=record_schema,
            change_note=change_note,
        )

        return spec_content
