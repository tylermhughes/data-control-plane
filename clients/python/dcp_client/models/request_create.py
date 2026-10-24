from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.request_create_priority import RequestCreatePriority
from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestCreate")


@_attrs_define
class RequestCreate:
    """
    Attributes:
        capability_id (str): The capability this data should improve.
        title (str):
        quantity (int):
        requested_by (str | Unset): Who asked for the data. Default: ''.
        priority (RequestCreatePriority | Unset):  Default: RequestCreatePriority.P2.
        rationale (str | Unset): Why the data is needed. Default: ''.
        target_metric (str | Unset): The eval metric or slice to move, if narrower. Default: ''.
        unit (str | Unset):  Default: 'items'.
        due_date (datetime.date | None | Unset):
        spec_version_id (None | str | Unset): The spec version to use (an `spv_` id). Can be added later. Must be
            approved before the request is opened.
    """

    capability_id: str
    title: str
    quantity: int
    requested_by: str | Unset = ""
    priority: RequestCreatePriority | Unset = RequestCreatePriority.P2
    rationale: str | Unset = ""
    target_metric: str | Unset = ""
    unit: str | Unset = "items"
    due_date: datetime.date | None | Unset = UNSET
    spec_version_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        capability_id = self.capability_id

        title = self.title

        quantity = self.quantity

        requested_by = self.requested_by

        priority: str | Unset = UNSET
        if not isinstance(self.priority, Unset):
            priority = self.priority.value

        rationale = self.rationale

        target_metric = self.target_metric

        unit = self.unit

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        elif isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        spec_version_id: None | str | Unset
        if isinstance(self.spec_version_id, Unset):
            spec_version_id = UNSET
        else:
            spec_version_id = self.spec_version_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "capability_id": capability_id,
                "title": title,
                "quantity": quantity,
            }
        )
        if requested_by is not UNSET:
            field_dict["requested_by"] = requested_by
        if priority is not UNSET:
            field_dict["priority"] = priority
        if rationale is not UNSET:
            field_dict["rationale"] = rationale
        if target_metric is not UNSET:
            field_dict["target_metric"] = target_metric
        if unit is not UNSET:
            field_dict["unit"] = unit
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if spec_version_id is not UNSET:
            field_dict["spec_version_id"] = spec_version_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        capability_id = d.pop("capability_id")

        title = d.pop("title")

        quantity = d.pop("quantity")

        requested_by = d.pop("requested_by", UNSET)

        _priority = d.pop("priority", UNSET)
        priority: RequestCreatePriority | Unset
        if isinstance(_priority, Unset):
            priority = UNSET
        else:
            priority = RequestCreatePriority(_priority)

        rationale = d.pop("rationale", UNSET)

        target_metric = d.pop("target_metric", UNSET)

        unit = d.pop("unit", UNSET)

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

        def _parse_spec_version_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        spec_version_id = _parse_spec_version_id(d.pop("spec_version_id", UNSET))

        request_create = cls(
            capability_id=capability_id,
            title=title,
            quantity=quantity,
            requested_by=requested_by,
            priority=priority,
            rationale=rationale,
            target_metric=target_metric,
            unit=unit,
            due_date=due_date,
            spec_version_id=spec_version_id,
        )

        return request_create
