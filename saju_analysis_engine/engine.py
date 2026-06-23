"""Public entry point for rule-based saju analysis."""

from __future__ import annotations

from collections.abc import Sequence
from saju_birth_engine.models import BirthChartResult

from .calibration import apply_calibration_to_packets, build_calibration_profile
from .constants import DOMAIN_ORDER
from .domains import build_event_packets
from .flows import build_flow_signals
from .models import AnalysisResult, Domain, PastEventAnswer, RelationshipStatus
from .structure import build_chart_structure


VALID_RELATIONSHIP_STATUSES = {
    "single",
    "interested",
    "dating",
    "long_term",
    "preparing_marriage",
    "married",
    "unknown",
}


def _birth_year_from_chart(chart: BirthChartResult) -> int | None:
    try:
        return int(str(chart.normalized_birth_datetime)[:4])
    except (TypeError, ValueError):
        return None


def _default_target_years(chart: BirthChartResult) -> list[int]:
    """Use the adult-life span as the default for comprehensive products."""

    birth_year = _birth_year_from_chart(chart)
    if birth_year is None:
        return []
    return list(range(birth_year + 20, birth_year + 80))


def analyze_chart(
    chart: BirthChartResult,
    *,
    target_years: Sequence[int] | None = None,
    domains: list[Domain] | None = None,
    past_event_answers: list[PastEventAnswer] | None = None,
    relationship_status: RelationshipStatus = "unknown",
    include_sub_periods: bool = True,
) -> AnalysisResult:
    """Analyze a finalized birth chart without changing the chart itself."""

    normalized_target_years = list(target_years) if target_years is not None else None
    if relationship_status not in VALID_RELATIONSHIP_STATUSES:
        raise ValueError(f"Unsupported relationship_status: {relationship_status}")
    if normalized_target_years is not None:
        if not normalized_target_years:
            raise ValueError("target_years must not be empty")
        if any(not isinstance(year, int) or isinstance(year, bool) for year in normalized_target_years):
            raise ValueError("target_years must contain integer years")
        if len(set(normalized_target_years)) != len(normalized_target_years):
            raise ValueError("target_years must not contain duplicate years")
        if normalized_target_years != sorted(normalized_target_years):
            raise ValueError("target_years must be sorted in increasing order")

    structure = build_chart_structure(chart)
    years = normalized_target_years or _default_target_years(chart)
    if not years:
        raise ValueError("birth year is required when target_years is omitted")
    selected_domains = domains or list(DOMAIN_ORDER)  # type: ignore[assignment]
    unsupported_domains = sorted(set(selected_domains).difference(DOMAIN_ORDER))
    if unsupported_domains:
        raise ValueError(f"Unsupported domains: {', '.join(unsupported_domains)}")
    if past_event_answers:
        unsupported_event_domains = sorted(
            {
                answer.domain
                for answer in past_event_answers
                if answer.domain is not None and answer.domain not in DOMAIN_ORDER
            }
        )
        if unsupported_event_domains:
            raise ValueError(f"Unsupported past_event domain: {', '.join(unsupported_event_domains)}")
    flow_signals = build_flow_signals(chart, structure, years, include_sub_periods=include_sub_periods)
    packets = build_event_packets(chart, structure, flow_signals, selected_domains, relationship_status)
    calibration_profile = build_calibration_profile(past_event_answers)
    packets = apply_calibration_to_packets(packets, calibration_profile)

    warnings = list(chart.calculation_warnings) + list(structure.warnings)
    if chart.boundary_sensitive:
        warnings.append("Analysis confidence is lowered around the recorded chart boundary.")

    return AnalysisResult(
        chart_structure=structure,
        flow_signals=flow_signals,
        event_packets=packets,
        calibration_profile=calibration_profile,
        warnings=list(dict.fromkeys(warnings)),
        trace={
            "target_years": years,
            "birth_year": _birth_year_from_chart(chart),
            "domains": selected_domains,
            "calibration_status": calibration_profile.status,
            "relationship_status": relationship_status,
            "birth_engine_boundary_sensitive": chart.boundary_sensitive,
            "daeun_boundary_sensitive": chart.daeun_boundary_sensitive,
        },
    )
