from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.capability_row import CapabilityRow
    from ..models.source_kind_row import SourceKindRow


T = TypeVar("T", bound="Portfolio")


@_attrs_define
class Portfolio:
    """
    Attributes:
        project_id (None | str):
        since (datetime.datetime | None):
        until (datetime.datetime | None):
        generated_at (datetime.datetime):
        by_capability (list[CapabilityRow]):
        by_source_kind (list[SourceKindRow]):
    """

    project_id: None | str
    since: datetime.datetime | None
    until: datetime.datetime | None
    generated_at: datetime.datetime
    by_capability: list[CapabilityRow]
    by_source_kind: list[SourceKindRow]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id: None | str
        project_id = self.project_id

        since: None | str
        if isinstance(self.since, datetime.datetime):
            since = self.since.isoformat()
        else:
            since = self.since

        until: None | str
        if isinstance(self.until, datetime.datetime):
            until = self.until.isoformat()
        else:
            until = self.until

        generated_at = self.generated_at.isoformat()

        by_capability = []
        for by_capability_item_data in self.by_capability:
            by_capability_item = by_capability_item_data.to_dict()
            by_capability.append(by_capability_item)

        by_source_kind = []
        for by_source_kind_item_data in self.by_source_kind:
            by_source_kind_item = by_source_kind_item_data.to_dict()
            by_source_kind.append(by_source_kind_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_id": project_id,
                "since": since,
                "until": until,
                "generated_at": generated_at,
                "by_capability": by_capability,
                "by_source_kind": by_source_kind,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.capability_row import CapabilityRow  # noqa: PLC0415
        from ..models.source_kind_row import SourceKindRow  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        def _parse_since(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                since_type_0 = datetime.datetime.fromisoformat(data)

                return since_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        since = _parse_since(d.pop("since"))

        def _parse_until(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                until_type_0 = datetime.datetime.fromisoformat(data)

                return until_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        until = _parse_until(d.pop("until"))

        generated_at = datetime.datetime.fromisoformat(d.pop("generated_at"))

        by_capability = []
        _by_capability = d.pop("by_capability")
        for by_capability_item_data in _by_capability:
            by_capability_item = CapabilityRow.from_dict(by_capability_item_data)

            by_capability.append(by_capability_item)

        by_source_kind = []
        _by_source_kind = d.pop("by_source_kind")
        for by_source_kind_item_data in _by_source_kind:
            by_source_kind_item = SourceKindRow.from_dict(by_source_kind_item_data)

            by_source_kind.append(by_source_kind_item)

        portfolio = cls(
            project_id=project_id,
            since=since,
            until=until,
            generated_at=generated_at,
            by_capability=by_capability,
            by_source_kind=by_source_kind,
        )

        portfolio.additional_properties = d
        return portfolio

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
