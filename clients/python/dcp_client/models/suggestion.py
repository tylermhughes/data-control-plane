from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.suggestion_role import SuggestionRole

if TYPE_CHECKING:
    from ..models.source_evidence import SourceEvidence
    from ..models.suggestion_allocation import SuggestionAllocation


T = TypeVar("T", bound="Suggestion")


@_attrs_define
class Suggestion:
    """
    Attributes:
        data_source_id (str):
        name (str):
        kind (str):
        role (SuggestionRole): `proven`: has a track record; `pilot`: untested, small trial share.
        share (float): Share of the remaining usable units.
        expected_usable (int):
        order_quantity (int): What to allocate, including extra for expected rejects.
        expected_cost (None | str):
        currency (None | str):
        capacity_by_due_date (int | None): Usable units it can likely deliver by the due date (null: no due date).
        evidence (SourceEvidence): What a source's recent deliveries show (last 90 days).
        notes (list[str]):
        allocation (SuggestionAllocation): Ready to send to POST /v1/allocations as-is (adjust anything first).
    """

    data_source_id: str
    name: str
    kind: str
    role: SuggestionRole
    share: float
    expected_usable: int
    order_quantity: int
    expected_cost: None | str
    currency: None | str
    capacity_by_due_date: int | None
    evidence: SourceEvidence
    notes: list[str]
    allocation: SuggestionAllocation
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data_source_id = self.data_source_id

        name = self.name

        kind = self.kind

        role = self.role.value

        share = self.share

        expected_usable = self.expected_usable

        order_quantity = self.order_quantity

        expected_cost: None | str
        expected_cost = self.expected_cost

        currency: None | str
        currency = self.currency

        capacity_by_due_date: int | None
        capacity_by_due_date = self.capacity_by_due_date

        evidence = self.evidence.to_dict()

        notes = self.notes

        allocation = self.allocation.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data_source_id": data_source_id,
                "name": name,
                "kind": kind,
                "role": role,
                "share": share,
                "expected_usable": expected_usable,
                "order_quantity": order_quantity,
                "expected_cost": expected_cost,
                "currency": currency,
                "capacity_by_due_date": capacity_by_due_date,
                "evidence": evidence,
                "notes": notes,
                "allocation": allocation,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.source_evidence import SourceEvidence  # noqa: PLC0415
        from ..models.suggestion_allocation import SuggestionAllocation  # noqa: PLC0415

        d = dict(src_dict)
        data_source_id = d.pop("data_source_id")

        name = d.pop("name")

        kind = d.pop("kind")

        role = SuggestionRole(d.pop("role"))

        share = d.pop("share")

        expected_usable = d.pop("expected_usable")

        order_quantity = d.pop("order_quantity")

        def _parse_expected_cost(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        expected_cost = _parse_expected_cost(d.pop("expected_cost"))

        def _parse_currency(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        currency = _parse_currency(d.pop("currency"))

        def _parse_capacity_by_due_date(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        capacity_by_due_date = _parse_capacity_by_due_date(d.pop("capacity_by_due_date"))

        evidence = SourceEvidence.from_dict(d.pop("evidence"))

        notes = cast(list[str], d.pop("notes"))

        allocation = SuggestionAllocation.from_dict(d.pop("allocation"))

        suggestion = cls(
            data_source_id=data_source_id,
            name=name,
            kind=kind,
            role=role,
            share=share,
            expected_usable=expected_usable,
            order_quantity=order_quantity,
            expected_cost=expected_cost,
            currency=currency,
            capacity_by_due_date=capacity_by_due_date,
            evidence=evidence,
            notes=notes,
            allocation=allocation,
        )

        suggestion.additional_properties = d
        return suggestion

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
