from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.request_update_priority_type_0 import RequestUpdatePriorityType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestUpdate")


@_attrs_define
class RequestUpdate:
    """Draft and open requests only. Fields you send are changed; the rest are kept.

    Attributes:
        title (None | str | Unset):
        requested_by (None | str | Unset):
        priority (None | RequestUpdatePriorityType0 | Unset):
        rationale (None | str | Unset):
        target_metric (None | str | Unset):
        quantity (int | None | Unset):
        unit (None | str | Unset):
        due_date (datetime.date | None | Unset):
        spec_version_id (None | str | Unset):
    """

    title: None | str | Unset = UNSET
    requested_by: None | str | Unset = UNSET
    priority: None | RequestUpdatePriorityType0 | Unset = UNSET
    rationale: None | str | Unset = UNSET
    target_metric: None | str | Unset = UNSET
    quantity: int | None | Unset = UNSET
    unit: None | str | Unset = UNSET
    due_date: datetime.date | None | Unset = UNSET
    spec_version_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        requested_by: None | str | Unset
        if isinstance(self.requested_by, Unset):
            requested_by = UNSET
        else:
            requested_by = self.requested_by

        priority: None | str | Unset
        if isinstance(self.priority, Unset):
            priority = UNSET
        elif isinstance(self.priority, RequestUpdatePriorityType0):
            priority = self.priority.value
        else:
            priority = self.priority

        rationale: None | str | Unset
        if isinstance(self.rationale, Unset):
            rationale = UNSET
        else:
            rationale = self.rationale

        target_metric: None | str | Unset
        if isinstance(self.target_metric, Unset):
            target_metric = UNSET
        else:
            target_metric = self.target_metric

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

        field_dict.update({})
        if title is not UNSET:
            field_dict["title"] = title
        if requested_by is not UNSET:
            field_dict["requested_by"] = requested_by
        if priority is not UNSET:
            field_dict["priority"] = priority
        if rationale is not UNSET:
            field_dict["rationale"] = rationale
        if target_metric is not UNSET:
            field_dict["target_metric"] = target_metric
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
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

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_requested_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        requested_by = _parse_requested_by(d.pop("requested_by", UNSET))

        def _parse_priority(data: object) -> None | RequestUpdatePriorityType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                priority_type_0 = RequestUpdatePriorityType0(data)

                return priority_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RequestUpdatePriorityType0 | Unset, data)

        priority = _parse_priority(d.pop("priority", UNSET))

        def _parse_rationale(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        rationale = _parse_rationale(d.pop("rationale", UNSET))

        def _parse_target_metric(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_metric = _parse_target_metric(d.pop("target_metric", UNSET))

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

        request_update = cls(
            title=title,
            requested_by=requested_by,
            priority=priority,
            rationale=rationale,
            target_metric=target_metric,
            quantity=quantity,
            unit=unit,
            due_date=due_date,
            spec_version_id=spec_version_id,
        )

        return request_update
