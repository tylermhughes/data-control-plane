from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AllocationUpdate")


@_attrs_define
class AllocationUpdate:
    """Planned allocations: any field. Active: only quantity, due date and notes.
    Complete or cancelled: nothing.

        Attributes:
            quantity (int | None | Unset):
            unit (None | str | Unset):
            quoted_unit_rate (float | None | str | Unset):
            currency (None | str | Unset):
            due_date (datetime.date | None | Unset):
            notes (None | str | Unset):
    """

    quantity: int | None | Unset = UNSET
    unit: None | str | Unset = UNSET
    quoted_unit_rate: float | None | str | Unset = UNSET
    currency: None | str | Unset = UNSET
    due_date: datetime.date | None | Unset = UNSET
    notes: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity: int | None | Unset
        if isinstance(self.quantity, Unset):
            quantity = UNSET
        else:
            quantity = self.quantity

        unit: None | str | Unset
        if isinstance(self.unit, Unset):
            unit = UNSET
        else:
            unit = self.unit

        quoted_unit_rate: float | None | str | Unset
        if isinstance(self.quoted_unit_rate, Unset):
            quoted_unit_rate = UNSET
        else:
            quoted_unit_rate = self.quoted_unit_rate

        currency: None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        elif isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if unit is not UNSET:
            field_dict["unit"] = unit
        if quoted_unit_rate is not UNSET:
            field_dict["quoted_unit_rate"] = quoted_unit_rate
        if currency is not UNSET:
            field_dict["currency"] = currency
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_quantity(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        quantity = _parse_quantity(d.pop("quantity", UNSET))

        def _parse_unit(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        unit = _parse_unit(d.pop("unit", UNSET))

        def _parse_quoted_unit_rate(data: object) -> float | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | str | Unset, data)

        quoted_unit_rate = _parse_quoted_unit_rate(d.pop("quoted_unit_rate", UNSET))

        def _parse_currency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_due_date(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_type_0 = datetime.date.fromisoformat(data)

                return due_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        due_date = _parse_due_date(d.pop("due_date", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        allocation_update = cls(
            quantity=quantity,
            unit=unit,
            quoted_unit_rate=quoted_unit_rate,
            currency=currency,
            due_date=due_date,
            notes=notes,
        )

        return allocation_update
