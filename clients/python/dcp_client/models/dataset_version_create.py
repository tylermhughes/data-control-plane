from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetVersionCreate")


@_attrs_define
class DatasetVersionCreate:
    """
    Attributes:
        batch_ids (list[str] | Unset): Accepted batches to add. Only accepted batches can go into a dataset.
        baseline_version_id (None | str | Unset): The version this one is compared against (any version for the same
            capability). Leave it out to use this dataset's previous version; send null for none.
        include_baseline_batches (bool | Unset): Start from the baseline's batches and add `batch_ids` to them. Default:
            True.
        notes (str | Unset):  Default: ''.
    """

    batch_ids: list[str] | Unset = UNSET
    baseline_version_id: None | str | Unset = UNSET
    include_baseline_batches: bool | Unset = True
    notes: str | Unset = ""

    def to_dict(self) -> dict[str, Any]:
        batch_ids: list[str] | Unset = UNSET
        if not isinstance(self.batch_ids, Unset):
            batch_ids = self.batch_ids

        baseline_version_id: None | str | Unset
        if isinstance(self.baseline_version_id, Unset):
            baseline_version_id = UNSET
        else:
            baseline_version_id = self.baseline_version_id

        include_baseline_batches = self.include_baseline_batches

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if batch_ids is not UNSET:
            field_dict["batch_ids"] = batch_ids
        if baseline_version_id is not UNSET:
            field_dict["baseline_version_id"] = baseline_version_id
        if include_baseline_batches is not UNSET:
            field_dict["include_baseline_batches"] = include_baseline_batches
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_ids = cast(list[str], d.pop("batch_ids", UNSET))

        def _parse_baseline_version_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        baseline_version_id = _parse_baseline_version_id(d.pop("baseline_version_id", UNSET))

        include_baseline_batches = d.pop("include_baseline_batches", UNSET)

        notes = d.pop("notes", UNSET)

        dataset_version_create = cls(
            batch_ids=batch_ids,
            baseline_version_id=baseline_version_id,
            include_baseline_batches=include_baseline_batches,
            notes=notes,
        )

        return dataset_version_create
