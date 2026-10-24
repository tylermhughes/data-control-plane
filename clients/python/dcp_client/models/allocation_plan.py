from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.excluded import Excluded
    from ..models.suggestion import Suggestion


T = TypeVar("T", bound="AllocationPlan")


@_attrs_define
class AllocationPlan:
    """
    Attributes:
        request_id (str):
        unit (str):
        requested (int):
        already_allocated (int): Planned, active and complete allocations.
        remaining (int): Usable units still to plan for.
        due_date (datetime.date | None):
        suggestions (list[Suggestion]):
        excluded (list[Excluded]):
        shortfall (int): Usable units no source can deliver by the due date, as far as DCP can tell.
        coverage_gaps (list[str]): The request's current coverage gaps.
        method (str): How the split was made, in plain language.
        generated_at (datetime.datetime):
    """

    request_id: str
    unit: str
    requested: int
    already_allocated: int
    remaining: int
    due_date: datetime.date | None
    suggestions: list[Suggestion]
    excluded: list[Excluded]
    shortfall: int
    coverage_gaps: list[str]
    method: str
    generated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        request_id = self.request_id

        unit = self.unit

        requested = self.requested

        already_allocated = self.already_allocated

        remaining = self.remaining

        due_date: None | str
        if isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        suggestions = []
        for suggestions_item_data in self.suggestions:
            suggestions_item = suggestions_item_data.to_dict()
            suggestions.append(suggestions_item)

        excluded = []
        for excluded_item_data in self.excluded:
            excluded_item = excluded_item_data.to_dict()
            excluded.append(excluded_item)

        shortfall = self.shortfall

        coverage_gaps = self.coverage_gaps

        method = self.method

        generated_at = self.generated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "request_id": request_id,
                "unit": unit,
                "requested": requested,
                "already_allocated": already_allocated,
                "remaining": remaining,
                "due_date": due_date,
                "suggestions": suggestions,
                "excluded": excluded,
                "shortfall": shortfall,
                "coverage_gaps": coverage_gaps,
                "method": method,
                "generated_at": generated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.excluded import Excluded  # noqa: PLC0415
        from ..models.suggestion import Suggestion  # noqa: PLC0415

        d = dict(src_dict)
        request_id = d.pop("request_id")

        unit = d.pop("unit")

        requested = d.pop("requested")

        already_allocated = d.pop("already_allocated")

        remaining = d.pop("remaining")

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

        suggestions = []
        _suggestions = d.pop("suggestions")
        for suggestions_item_data in _suggestions:
            suggestions_item = Suggestion.from_dict(suggestions_item_data)

            suggestions.append(suggestions_item)

        excluded = []
        _excluded = d.pop("excluded")
        for excluded_item_data in _excluded:
            excluded_item = Excluded.from_dict(excluded_item_data)

            excluded.append(excluded_item)

        shortfall = d.pop("shortfall")

        coverage_gaps = cast(list[str], d.pop("coverage_gaps"))

        method = d.pop("method")

        generated_at = datetime.datetime.fromisoformat(d.pop("generated_at"))

        allocation_plan = cls(
            request_id=request_id,
            unit=unit,
            requested=requested,
            already_allocated=already_allocated,
            remaining=remaining,
            due_date=due_date,
            suggestions=suggestions,
            excluded=excluded,
            shortfall=shortfall,
            coverage_gaps=coverage_gaps,
            method=method,
            generated_at=generated_at,
        )

        allocation_plan.additional_properties = d
        return allocation_plan

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
