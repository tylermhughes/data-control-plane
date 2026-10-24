from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.request_priority import RequestPriority
from ..models.request_status import RequestStatus

if TYPE_CHECKING:
    from ..models.allocated_total import AllocatedTotal


T = TypeVar("T", bound="Request")


@_attrs_define
class Request:
    """
    Attributes:
        id (str):
        project_id (str):
        capability_id (str):
        title (str):
        requested_by (str):
        priority (RequestPriority):
        rationale (str):
        target_metric (str):
        quantity (int):
        unit (str):
        due_date (datetime.date | None):
        spec_version_id (None | str):
        spec_id (None | str): The spec that `spec_version_id` belongs to.
        spec_version (int | None): The version number of `spec_version_id`.
        status (RequestStatus):
        allocated (list[AllocatedTotal]): Allocated so far, per unit and currency (cancelled allocations excluded). May
            exceed `quantity`, e.g. to cover expected rejects.
        opened_at (datetime.datetime | None):
        closed_at (datetime.datetime | None):
        cancelled_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    project_id: str
    capability_id: str
    title: str
    requested_by: str
    priority: RequestPriority
    rationale: str
    target_metric: str
    quantity: int
    unit: str
    due_date: datetime.date | None
    spec_version_id: None | str
    spec_id: None | str
    spec_version: int | None
    status: RequestStatus
    allocated: list[AllocatedTotal]
    opened_at: datetime.datetime | None
    closed_at: datetime.datetime | None
    cancelled_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        capability_id = self.capability_id

        title = self.title

        requested_by = self.requested_by

        priority = self.priority.value

        rationale = self.rationale

        target_metric = self.target_metric

        quantity = self.quantity

        unit = self.unit

        due_date: None | str
        if isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        spec_version_id: None | str
        spec_version_id = self.spec_version_id

        spec_id: None | str
        spec_id = self.spec_id

        spec_version: int | None
        spec_version = self.spec_version

        status = self.status.value

        allocated = []
        for allocated_item_data in self.allocated:
            allocated_item = allocated_item_data.to_dict()
            allocated.append(allocated_item)

        opened_at: None | str
        if isinstance(self.opened_at, datetime.datetime):
            opened_at = self.opened_at.isoformat()
        else:
            opened_at = self.opened_at

        closed_at: None | str
        if isinstance(self.closed_at, datetime.datetime):
            closed_at = self.closed_at.isoformat()
        else:
            closed_at = self.closed_at

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
                "capability_id": capability_id,
                "title": title,
                "requested_by": requested_by,
                "priority": priority,
                "rationale": rationale,
                "target_metric": target_metric,
                "quantity": quantity,
                "unit": unit,
                "due_date": due_date,
                "spec_version_id": spec_version_id,
                "spec_id": spec_id,
                "spec_version": spec_version,
                "status": status,
                "allocated": allocated,
                "opened_at": opened_at,
                "closed_at": closed_at,
                "cancelled_at": cancelled_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.allocated_total import AllocatedTotal  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        capability_id = d.pop("capability_id")

        title = d.pop("title")

        requested_by = d.pop("requested_by")

        priority = RequestPriority(d.pop("priority"))

        rationale = d.pop("rationale")

        target_metric = d.pop("target_metric")

        quantity = d.pop("quantity")

        unit = d.pop("unit")

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

        def _parse_spec_version_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        spec_version_id = _parse_spec_version_id(d.pop("spec_version_id"))

        def _parse_spec_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        spec_id = _parse_spec_id(d.pop("spec_id"))

        def _parse_spec_version(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        spec_version = _parse_spec_version(d.pop("spec_version"))

        status = RequestStatus(d.pop("status"))

        allocated = []
        _allocated = d.pop("allocated")
        for allocated_item_data in _allocated:
            allocated_item = AllocatedTotal.from_dict(allocated_item_data)

            allocated.append(allocated_item)

        def _parse_opened_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                opened_at_type_0 = datetime.datetime.fromisoformat(data)

                return opened_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        opened_at = _parse_opened_at(d.pop("opened_at"))

        def _parse_closed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                closed_at_type_0 = datetime.datetime.fromisoformat(data)

                return closed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        closed_at = _parse_closed_at(d.pop("closed_at"))

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

        request = cls(
            id=id,
            project_id=project_id,
            capability_id=capability_id,
            title=title,
            requested_by=requested_by,
            priority=priority,
            rationale=rationale,
            target_metric=target_metric,
            quantity=quantity,
            unit=unit,
            due_date=due_date,
            spec_version_id=spec_version_id,
            spec_id=spec_id,
            spec_version=spec_version,
            status=status,
            allocated=allocated,
            opened_at=opened_at,
            closed_at=closed_at,
            cancelled_at=cancelled_at,
            created_at=created_at,
            updated_at=updated_at,
        )

        request.additional_properties = d
        return request

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
