from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AllocationCreate")


@_attrs_define
class AllocationCreate:
    """
    Attributes:
        request_id (str):
        data_source_id (str): Must be in the same project as the request.
        quantity (int):
        quoted_unit_rate (float | str): Quoted price per unit.
        currency (str): ISO 4217 code.
        unit (None | str | Unset): Defaults to the data source's `default_unit`.
        due_date (datetime.date | None | Unset):
        notes (str | Unset):  Default: ''.
    """

    request_id: str
    data_source_id: str
    quantity: int
    quoted_unit_rate: float | str
    currency: str
    unit: None | str | Unset = UNSET
    due_date: datetime.date | None | Unset = UNSET
    notes: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        request_id = self.request_id

        data_source_id = self.data_source_id

        quantity = self.quantity

        quoted_unit_rate: float | str
        quoted_unit_rate = self.quoted_unit_rate

        currency = self.currency

        unit: None | str | Unset
        if isinstance(self.unit, Unset):
            unit = UNSET
        else:
            unit = self.unit

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        elif isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "request_id": request_id,
                "data_source_id": data_source_id,
                "quantity": quantity,
                "quoted_unit_rate": quoted_unit_rate,
                "currency": currency,
            }
        )
        if unit is not UNSET:
            field_dict["unit"] = unit
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        request_id = d.pop("request_id")

        data_source_id = d.pop("data_source_id")

        quantity = d.pop("quantity")

        def _parse_quoted_unit_rate(data: object) -> float | str:
            return cast(float | str, data)

        quoted_unit_rate = _parse_quoted_unit_rate(d.pop("quoted_unit_rate"))

        currency = d.pop("currency")

        def _parse_unit(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        unit = _parse_unit(d.pop("unit", UNSET))

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

        notes = d.pop("notes", UNSET)

        allocation_create = cls(
            request_id=request_id,
            data_source_id=data_source_id,
            quantity=quantity,
            quoted_unit_rate=quoted_unit_rate,
            currency=currency,
            unit=unit,
            due_date=due_date,
            notes=notes,
        )

        return allocation_create
