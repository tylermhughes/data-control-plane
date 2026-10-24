from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.acceptance_rule_operator import AcceptanceRuleOperator
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acceptance_rule_applies_to_type_0 import AcceptanceRuleAppliesToType0


T = TypeVar("T", bound="AcceptanceRule")


@_attrs_define
class AcceptanceRule:
    """A pass/fail rule for batches, e.g. agreement >= 0.85. Checked automatically from M6.

    Attributes:
        metric (str): Lowercase letters, digits and underscores, starting with a letter.
        operator (AcceptanceRuleOperator):
        threshold (float):
        applies_to (AcceptanceRuleAppliesToType0 | None | Unset): Limit the rule to items with these attribute values.
        description (str | Unset):  Default: ''.
    """

    metric: str
    operator: AcceptanceRuleOperator
    threshold: float
    applies_to: AcceptanceRuleAppliesToType0 | None | Unset = UNSET
    description: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        from ..models.acceptance_rule_applies_to_type_0 import AcceptanceRuleAppliesToType0  # noqa: PLC0415

        metric = self.metric

        operator = self.operator.value

        threshold = self.threshold

        applies_to: dict[str, Any] | None | Unset
        if isinstance(self.applies_to, Unset):
            applies_to = UNSET
        elif isinstance(self.applies_to, AcceptanceRuleAppliesToType0):
            applies_to = self.applies_to.to_dict()
        else:
            applies_to = self.applies_to

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "metric": metric,
                "operator": operator,
                "threshold": threshold,
            }
        )
        if applies_to is not UNSET:
            field_dict["applies_to"] = applies_to
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acceptance_rule_applies_to_type_0 import AcceptanceRuleAppliesToType0  # noqa: PLC0415

        d = dict(src_dict)
        metric = d.pop("metric")

        operator = AcceptanceRuleOperator(d.pop("operator"))

        threshold = d.pop("threshold")

        def _parse_applies_to(data: object) -> AcceptanceRuleAppliesToType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                applies_to_type_0 = AcceptanceRuleAppliesToType0.from_dict(data)

                return applies_to_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AcceptanceRuleAppliesToType0 | None | Unset, data)

        applies_to = _parse_applies_to(d.pop("applies_to", UNSET))

        description = d.pop("description", UNSET)

        acceptance_rule = cls(
            metric=metric,
            operator=operator,
            threshold=threshold,
            applies_to=applies_to,
            description=description,
        )

        return acceptance_rule
