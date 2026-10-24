from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.event_data import EventData


T = TypeVar("T", bound="Event")


@_attrs_define
class Event:
    """
    Attributes:
        id (str):
        type_ (str):
        subject_id (str): The thing that changed.
        project_id (None | str):
        actor_key_id (None | str): The API key that made the change.
        data (EventData): The thing as it was right after the change.
        created_at (datetime.datetime):
    """

    id: str
    type_: str
    subject_id: str
    project_id: None | str
    actor_key_id: None | str
    data: EventData
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_

        subject_id = self.subject_id

        project_id: None | str
        project_id = self.project_id

        actor_key_id: None | str
        actor_key_id = self.actor_key_id

        data = self.data.to_dict()

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "subject_id": subject_id,
                "project_id": project_id,
                "actor_key_id": actor_key_id,
                "data": data,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_data import EventData  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        type_ = d.pop("type")

        subject_id = d.pop("subject_id")

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("project_id"))

        def _parse_actor_key_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        actor_key_id = _parse_actor_key_id(d.pop("actor_key_id"))

        data = EventData.from_dict(d.pop("data"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        event = cls(
            id=id,
            type_=type_,
            subject_id=subject_id,
            project_id=project_id,
            actor_key_id=actor_key_id,
            data=data,
            created_at=created_at,
        )

        event.additional_properties = d
        return event

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
