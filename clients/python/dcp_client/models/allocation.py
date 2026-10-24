from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.allocation_status import AllocationStatus

T = TypeVar("T", bound="Allocation")


@_attrs_define
class Allocation:
    """
    Attributes:
        id (str):
        project_id (str):
        request_id (str):
        data_source_id (str):
        spec_version_id (str): The spec version this allocation was quoted against. Never changes.
        quantity (int):
        unit (str):
        quoted_unit_rate (str):
        currency (str):
        quoted_cost (str): quantity × quoted_unit_rate.
        batch_count (int): Deliveries received so far.
        delivered_count (int):
        accepted_count (int): From accepted batches.
        spend (str): Sum of batch spend.
        progress (float): accepted_count ÷ quantity. Can exceed 1.
        due_date (datetime.date | None):
        notes (str):
        status (AllocationStatus):
        activated_at (datetime.datetime | None):
        completed_at (datetime.datetime | None):
        cancelled_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    request_id: str
    data_source_id: str
    spec_version_id: str
    quantity: int
    unit: str
    quoted_unit_rate: str
    currency: str
    quoted_cost: str
    batch_count: int
    delivered_count: int
    accepted_count: int
    spend: str
    progress: float
    due_date: datetime.date | None
    notes: str
    status: AllocationStatus
    activated_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    cancelled_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        request_id = self.request_id

        data_source_id = self.data_source_id

        spec_version_id = self.spec_version_id

        quantity = self.quantity

        unit = self.unit

        quoted_unit_rate = self.quoted_unit_rate

        currency = self.currency

        quoted_cost = self.quoted_cost

        batch_count = self.batch_count

        delivered_count = self.delivered_count

        accepted_count = self.accepted_count

        spend = self.spend

        progress = self.progress

        due_date: None | str
        if isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        notes = self.notes

        status = self.status.value

        activated_at: None | str
        if isinstance(self.activated_at, datetime.datetime):
            activated_at = self.activated_at.isoformat()
        else:
            activated_at = self.activated_at

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        cancelled_at: None | str
        if isinstance(self.cancelled_at, datetime.datetime):
            cancelled_at = self.cancelled_at.isoformat()
        else:
            cancelled_at = self.cancelled_at

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "request_id": request_id,
                "data_source_id": data_source_id,
                "spec_version_id": spec_version_id,
                "quantity": quantity,
                "unit": unit,
                "quoted_unit_rate": quoted_unit_rate,
                "currency": currency,
                "quoted_cost": quoted_cost,
                "batch_count": batch_count,
                "delivered_count": delivered_count,
                "accepted_count": accepted_count,
                "spend": spend,
                "progress": progress,
                "due_date": due_date,
                "notes": notes,
                "status": status,
                "activated_at": activated_at,
                "completed_at": completed_at,
                "cancelled_at": cancelled_at,
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

        request_id = d.pop("request_id")

        data_source_id = d.pop("data_source_id")

        spec_version_id = d.pop("spec_version_id")

        quantity = d.pop("quantity")

        unit = d.pop("unit")

        quoted_unit_rate = d.pop("quoted_unit_rate")

        currency = d.pop("currency")

        quoted_cost = d.pop("quoted_cost")

        batch_count = d.pop("batch_count")

        delivered_count = d.pop("delivered_count")

        accepted_count = d.pop("accepted_count")

        spend = d.pop("spend")

        progress = d.pop("progress")

        def _parse_due_date(data: object) -> datetime.date | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_type_0 = datetime.date.fromisoformat(data)

                return due_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None, data)

        due_date = _parse_due_date(d.pop("due_date"))

        notes = d.pop("notes")

        status = AllocationStatus(d.pop("status"))

        def _parse_activated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                activated_at_type_0 = datetime.datetime.fromisoformat(data)

                return activated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        activated_at = _parse_activated_at(d.pop("activated_at"))

        def _parse_completed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = datetime.datetime.fromisoformat(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        completed_at = _parse_completed_at(d.pop("completed_at"))

        def _parse_cancelled_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                cancelled_at_type_0 = datetime.datetime.fromisoformat(data)

                return cancelled_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        cancelled_at = _parse_cancelled_at(d.pop("cancelled_at"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        allocation = cls(
            id=id,
            project_id=project_id,
            request_id=request_id,
            data_source_id=data_source_id,
            spec_version_id=spec_version_id,
            quantity=quantity,
            unit=unit,
            quoted_unit_rate=quoted_unit_rate,
            currency=currency,
            quoted_cost=quoted_cost,
            batch_count=batch_count,
            delivered_count=delivered_count,
            accepted_count=accepted_count,
            spend=spend,
            progress=progress,
            due_date=due_date,
            notes=notes,
            status=status,
            activated_at=activated_at,
            completed_at=completed_at,
            cancelled_at=cancelled_at,
            created_at=created_at,
            updated_at=updated_at,
        )

        allocation.additional_properties = d
        return allocation

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
