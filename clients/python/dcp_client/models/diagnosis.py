from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.diagnosis_recommendation import DiagnosisRecommendation
from ..models.diagnosis_trend import DiagnosisTrend

if TYPE_CHECKING:
    from ..models.cause_check import CauseCheck
    from ..models.coverage import Coverage
    from ..models.scored_version import ScoredVersion
    from ..models.suggested_spec_change import SuggestedSpecChange


T = TypeVar("T", bound="Diagnosis")


@_attrs_define
class Diagnosis:
    """
    Attributes:
        capability_id (str):
        eval_metric (str):
        flattening_threshold (float):
        versions (list[ScoredVersion]): Scored dataset versions, oldest first.
        trend (DiagnosisTrend):
        latest_vs_earlier (float | None): Latest points per 10K ÷ average of earlier versions.
        checks (list[CauseCheck]):
        recommendation (DiagnosisRecommendation):
        summary (str): The recommendation and why, in plain language.
        coverage (Coverage | None): The data-mix check behind it, if run.
        suggested_spec_change (None | SuggestedSpecChange):
        generated_at (datetime.datetime):
    """

    capability_id: str
    eval_metric: str
    flattening_threshold: float
    versions: list[ScoredVersion]
    trend: DiagnosisTrend
    latest_vs_earlier: float | None
    checks: list[CauseCheck]
    recommendation: DiagnosisRecommendation
    summary: str
    coverage: Coverage | None
    suggested_spec_change: None | SuggestedSpecChange
    generated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.coverage import Coverage  # noqa: PLC0415
        from ..models.suggested_spec_change import SuggestedSpecChange  # noqa: PLC0415

        capability_id = self.capability_id

        eval_metric = self.eval_metric

        flattening_threshold = self.flattening_threshold

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        trend = self.trend.value

        latest_vs_earlier: float | None
        latest_vs_earlier = self.latest_vs_earlier

        checks = []
        for checks_item_data in self.checks:
            checks_item = checks_item_data.to_dict()
            checks.append(checks_item)

        recommendation = self.recommendation.value

        summary = self.summary

        coverage: dict[str, Any] | None
        if isinstance(self.coverage, Coverage):
            coverage = self.coverage.to_dict()
        else:
            coverage = self.coverage

        suggested_spec_change: dict[str, Any] | None
        if isinstance(self.suggested_spec_change, SuggestedSpecChange):
            suggested_spec_change = self.suggested_spec_change.to_dict()
        else:
            suggested_spec_change = self.suggested_spec_change

        generated_at = self.generated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "capability_id": capability_id,
                "eval_metric": eval_metric,
                "flattening_threshold": flattening_threshold,
                "versions": versions,
                "trend": trend,
                "latest_vs_earlier": latest_vs_earlier,
                "checks": checks,
                "recommendation": recommendation,
                "summary": summary,
                "coverage": coverage,
                "suggested_spec_change": suggested_spec_change,
                "generated_at": generated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cause_check import CauseCheck  # noqa: PLC0415
        from ..models.coverage import Coverage  # noqa: PLC0415
        from ..models.scored_version import ScoredVersion  # noqa: PLC0415
        from ..models.suggested_spec_change import SuggestedSpecChange  # noqa: PLC0415

        d = dict(src_dict)
        capability_id = d.pop("capability_id")

        eval_metric = d.pop("eval_metric")

        flattening_threshold = d.pop("flattening_threshold")

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = ScoredVersion.from_dict(versions_item_data)

            versions.append(versions_item)

        trend = DiagnosisTrend(d.pop("trend"))

        def _parse_latest_vs_earlier(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        latest_vs_earlier = _parse_latest_vs_earlier(d.pop("latest_vs_earlier"))

        checks = []
        _checks = d.pop("checks")
        for checks_item_data in _checks:
            checks_item = CauseCheck.from_dict(checks_item_data)

            checks.append(checks_item)

        recommendation = DiagnosisRecommendation(d.pop("recommendation"))

        summary = d.pop("summary")

        def _parse_coverage(data: object) -> Coverage | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                coverage_type_0 = Coverage.from_dict(data)

                return coverage_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(Coverage | None, data)

        coverage = _parse_coverage(d.pop("coverage"))

        def _parse_suggested_spec_change(data: object) -> None | SuggestedSpecChange:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                suggested_spec_change_type_0 = SuggestedSpecChange.from_dict(data)

                return suggested_spec_change_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SuggestedSpecChange, data)

        suggested_spec_change = _parse_suggested_spec_change(d.pop("suggested_spec_change"))

        generated_at = datetime.datetime.fromisoformat(d.pop("generated_at"))

        diagnosis = cls(
            capability_id=capability_id,
            eval_metric=eval_metric,
            flattening_threshold=flattening_threshold,
            versions=versions,
            trend=trend,
            latest_vs_earlier=latest_vs_earlier,
            checks=checks,
            recommendation=recommendation,
            summary=summary,
            coverage=coverage,
            suggested_spec_change=suggested_spec_change,
            generated_at=generated_at,
        )

        diagnosis.additional_properties = d
        return diagnosis

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
