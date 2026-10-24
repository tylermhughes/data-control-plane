from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.unit_total import UnitTotal


T = TypeVar("T", bound="DatasetVersion")


@_attrs_define
class DatasetVersion:
    """
    Attributes:
        id (str):
        project_id (str):
        dataset_id (str):
        capability_id (str):
        version (int):
        baseline_version_id (None | str):
        batch_ids (list[str]):
        totals (list[UnitTotal]): All batches in this version.
        new_vs_baseline (list[UnitTotal]): Only batches the baseline didn't have: the spend that bought this version's
            eval change.
        notes (str):
        created_at (datetime.datetime):
    """

    id: str
    project_id: str
    dataset_id: str
    capability_id: str
    version: int
    baseline_version_id: None | str
    batch_ids: list[str]
    totals: list[UnitTotal]
    new_vs_baseline: list[UnitTotal]
    notes: str
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        dataset_id = self.dataset_id

        capability_id = self.capability_id

        version = self.version

        baseline_version_id: None | str
        baseline_version_id = self.baseline_version_id

        batch_ids = self.batch_ids

        totals = []
        for totals_item_data in self.totals:
            totals_item = totals_item_data.to_dict()
            totals.append(totals_item)

        new_vs_baseline = []
        for new_vs_baseline_item_data in self.new_vs_baseline:
            new_vs_baseline_item = new_vs_baseline_item_data.to_dict()
            new_vs_baseline.append(new_vs_baseline_item)

        notes = self.notes

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "project_id": project_id,
                "dataset_id": dataset_id,
                "capability_id": capability_id,
                "version": version,
                "baseline_version_id": baseline_version_id,
                "batch_ids": batch_ids,
                "totals": totals,
                "new_vs_baseline": new_vs_baseline,
                "notes": notes,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.unit_total import UnitTotal  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("project_id")

        dataset_id = d.pop("dataset_id")

        capability_id = d.pop("capability_id")

        version = d.pop("version")

        def _parse_baseline_version_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        baseline_version_id = _parse_baseline_version_id(d.pop("baseline_version_id"))

        batch_ids = cast(list[str], d.pop("batch_ids"))

        totals = []
        _totals = d.pop("totals")
        for totals_item_data in _totals:
            totals_item = UnitTotal.from_dict(totals_item_data)

            totals.append(totals_item)

        new_vs_baseline = []
        _new_vs_baseline = d.pop("new_vs_baseline")
        for new_vs_baseline_item_data in _new_vs_baseline:
            new_vs_baseline_item = UnitTotal.from_dict(new_vs_baseline_item_data)

            new_vs_baseline.append(new_vs_baseline_item)

        notes = d.pop("notes")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        dataset_version = cls(
            id=id,
            project_id=project_id,
            dataset_id=dataset_id,
            capability_id=capability_id,
            version=version,
            baseline_version_id=baseline_version_id,
            batch_ids=batch_ids,
            totals=totals,
            new_vs_baseline=new_vs_baseline,
            notes=notes,
            created_at=created_at,
        )

        dataset_version.additional_properties = d
        return dataset_version

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
