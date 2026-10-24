from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Sources")


@_attrs_define
class Sources:
    """Where the row's numbers come from.

    Attributes:
        dataset_version_ids (list[str]): Versions whose eval change is counted.
        eval_result_ids (list[str]): The eval results compared.
        batch_count (int): Batches behind the spend and usable units.
    """

    dataset_version_ids: list[str]
    eval_result_ids: list[str]
    batch_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_version_ids = self.dataset_version_ids

        eval_result_ids = self.eval_result_ids

        batch_count = self.batch_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_version_ids": dataset_version_ids,
                "eval_result_ids": eval_result_ids,
                "batch_count": batch_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_version_ids = cast(list[str], d.pop("dataset_version_ids"))

        eval_result_ids = cast(list[str], d.pop("eval_result_ids"))

        batch_count = d.pop("batch_count")

        sources = cls(
            dataset_version_ids=dataset_version_ids,
            eval_result_ids=eval_result_ids,
            batch_count=batch_count,
        )

        sources.additional_properties = d
        return sources

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
