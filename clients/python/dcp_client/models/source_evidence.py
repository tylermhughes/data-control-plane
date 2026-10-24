from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.source_evidence_value_mix import SourceEvidenceValueMix


T = TypeVar("T", bound="SourceEvidence")


@_attrs_define
class SourceEvidence:
    """What a source's recent deliveries show (last 90 days).

    Attributes:
        batches_decided (int): Accepted or rejected batches.
        delivered (int):
        accepted (int):
        accept_rate (float | None): accepted ÷ delivered.
        cost_per_usable_unit (None | str):
        usable_per_day (float | None): Throughput.
        open_commitments (int): Units still owed on its active allocations (quantity − accepted).
        last_quoted_rate (None | str):
        currency (None | str):
        value_mix (SourceEvidenceValueMix): Share of each attribute value in its accepted deliveries.
    """

    batches_decided: int
    delivered: int
    accepted: int
    accept_rate: float | None
    cost_per_usable_unit: None | str
    usable_per_day: float | None
    open_commitments: int
    last_quoted_rate: None | str
    currency: None | str
    value_mix: SourceEvidenceValueMix
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batches_decided = self.batches_decided

        delivered = self.delivered

        accepted = self.accepted

        accept_rate: float | None
        accept_rate = self.accept_rate

        cost_per_usable_unit: None | str
        cost_per_usable_unit = self.cost_per_usable_unit

        usable_per_day: float | None
        usable_per_day = self.usable_per_day

        open_commitments = self.open_commitments

        last_quoted_rate: None | str
        last_quoted_rate = self.last_quoted_rate

        currency: None | str
        currency = self.currency

        value_mix = self.value_mix.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "batches_decided": batches_decided,
                "delivered": delivered,
                "accepted": accepted,
                "accept_rate": accept_rate,
                "cost_per_usable_unit": cost_per_usable_unit,
                "usable_per_day": usable_per_day,
                "open_commitments": open_commitments,
                "last_quoted_rate": last_quoted_rate,
                "currency": currency,
                "value_mix": value_mix,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.source_evidence_value_mix import SourceEvidenceValueMix  # noqa: PLC0415

        d = dict(src_dict)
        batches_decided = d.pop("batches_decided")

        delivered = d.pop("delivered")

        accepted = d.pop("accepted")

        def _parse_accept_rate(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        accept_rate = _parse_accept_rate(d.pop("accept_rate"))

        def _parse_cost_per_usable_unit(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        cost_per_usable_unit = _parse_cost_per_usable_unit(d.pop("cost_per_usable_unit"))

        def _parse_usable_per_day(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        usable_per_day = _parse_usable_per_day(d.pop("usable_per_day"))

        open_commitments = d.pop("open_commitments")

        def _parse_last_quoted_rate(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_quoted_rate = _parse_last_quoted_rate(d.pop("last_quoted_rate"))

        def _parse_currency(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        currency = _parse_currency(d.pop("currency"))

        value_mix = SourceEvidenceValueMix.from_dict(d.pop("value_mix"))

        source_evidence = cls(
            batches_decided=batches_decided,
            delivered=delivered,
            accepted=accepted,
            accept_rate=accept_rate,
            cost_per_usable_unit=cost_per_usable_unit,
            usable_per_day=usable_per_day,
            open_commitments=open_commitments,
            last_quoted_rate=last_quoted_rate,
            currency=currency,
            value_mix=value_mix,
        )

        source_evidence.additional_properties = d
        return source_evidence

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
