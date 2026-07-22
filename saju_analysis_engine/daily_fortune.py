"""Deterministic daily-flow signals for the customer report.

The daily layer keeps natal capacity, annual environment, solar-month context,
and the current day trigger separate.  It does not generate customer prose or
apply any browser-only grade adjustment.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from saju_birth_engine.models import BirthChartResult, Pillar
from saju_birth_engine.pillars import day_pillar_for_date, month_pillar, year_pillar_for_gregorian_year

from .constants import BRANCH_HIDDEN_STEMS, STEM_METADATA, TEN_GOD_GROUPS
from .flows import (
    _apply_flow_governance_score,
    _apply_interaction_score,
    _apply_ten_god_score,
    _finalize_domain_scores,
    _flow_anchor_hits_for_pillar,
    _infer_gender,
    _initial_domain_scores,
    _pillar_ten_gods,
    _saju_month_periods,
)
from .interactions import flow_interactions
from .models import ChartStructure
from .relation_polarity import branch_relation_polarity
from .ten_gods import main_hidden_stem, ten_god_for


DAILY_FORTUNE_SIGNAL_VERSION = "daily_fortune_signal_v1"


def _clip(value: float) -> int:
    return max(0, min(100, round(value)))


def _solar_month_pillar_for_date(
    target_date: date,
    *,
    timezone_offset_minutes: int,
) -> tuple[int, int, Pillar]:
    """Return the effective saju year, month index, and solar-month pillar."""

    target_dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0)
    for saju_year in (target_date.year - 1, target_date.year):
        periods = _saju_month_periods(saju_year, timezone_offset_minutes)
        for month_index, period in enumerate(periods):
            start = datetime.fromisoformat(str(period["start"]))
            end = datetime.fromisoformat(str(period["end"]))
            if start <= target_dt < end:
                year_pillar = year_pillar_for_gregorian_year(saju_year)
                return saju_year, month_index, month_pillar(year_pillar.stem_index, month_index)

    # The solar-term table spans adjacent years, so this is only a defensive
    # fallback for an astronomy calculation failure near a boundary.
    saju_year = target_date.year
    year_pillar = year_pillar_for_gregorian_year(saju_year)
    month_index = (target_date.month - 2) % 12
    return saju_year, month_index, month_pillar(year_pillar.stem_index, month_index)


def _phase_domain_scores(
    chart: BirthChartResult,
    structure: ChartStructure,
    pillar: Pillar,
    *,
    source: str,
    ten_god_weight: float,
    governance_weight: float,
) -> tuple[dict[str, dict[str, Any]], list[Any], dict[str, Any]]:
    day_stem_key = chart.day_pillar.stem_key
    gender = _infer_gender(chart)
    stem_ten_god, branch_ten_god = _pillar_ten_gods(day_stem_key, pillar)
    scores = _initial_domain_scores()

    _apply_ten_god_score(scores, stem_ten_god, ten_god_weight, f"{source}_stem", gender)
    _apply_ten_god_score(scores, branch_ten_god, ten_god_weight, f"{source}_branch", gender)
    for hidden_stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]:
        if hidden_stem_key == main_hidden_stem(pillar.branch_key):
            continue
        _apply_ten_god_score(
            scores,
            ten_god_for(day_stem_key, hidden_stem_key),
            ten_god_weight * hidden_weight * 0.28,
            f"{source}_hidden_{hidden_stem_key}",
            gender,
        )

    active_elements = [
        str(STEM_METADATA[pillar.stem_key]["element"]),
        str(STEM_METADATA[main_hidden_stem(pillar.branch_key)]["element"]),
    ]
    _apply_flow_governance_score(
        scores,
        structure,
        source=source,
        elements=active_elements,
        ten_gods=[stem_ten_god, branch_ten_god],
        positions=[source, f"{source}:stem", f"{source}:branch"],
        weight=governance_weight,
    )

    interactions = flow_interactions(chart, source, pillar.branch_key)
    for interaction in interactions:
        _apply_interaction_score(scores, structure, interaction, f"{source}_{interaction.basis_code}")

    anchor = _flow_anchor_hits_for_pillar(
        structure,
        source=source,
        day_stem_key=day_stem_key,
        pillar=pillar,
    )
    return _finalize_domain_scores(scores), interactions, {
        "pillar": pillar.label,
        "stem_ten_god": stem_ten_god,
        "branch_ten_god": branch_ten_god,
        "stem_group": TEN_GOD_GROUPS[stem_ten_god],
        "branch_group": TEN_GOD_GROUPS[branch_ten_god],
        "anchor": anchor,
    }


def _relation_payload(
    structure: ChartStructure,
    interactions: list[Any],
    *,
    source: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for interaction in interactions:
        polarity = branch_relation_polarity(
            structure.element_profile,
            interaction,
            structure.pattern_profile,
        )
        rows.append(
            {
                "source": source,
                "relation_type": str(interaction.relation_type),
                "positions": list(interaction.positions),
                "branches": list(interaction.branches),
                "polarity": str(polarity.polarity or "mixed"),
                "effective_friction": round(float(polarity.effective_friction or 0.0), 3),
                "basis_code": str(interaction.basis_code or ""),
            }
        )
    return rows


_CONTEXT_GROUP_WEIGHTS: dict[str, dict[str, float]] = {
    "mood": {"resource": 4.5, "output": 4.0, "peer": 1.5, "wealth": 1.0, "officer": -2.0},
    "social": {"output": 5.0, "peer": 4.0, "officer": 2.5, "wealth": 2.0, "resource": 0.5},
    "family": {"resource": 4.5, "wealth": 3.0, "officer": 2.0, "output": 1.0, "peer": -1.5},
}


_CONTEXT_POSITIONS: dict[str, set[str]] = {
    "mood": {"day", "hour"},
    "social": {"year", "month"},
    "family": {"year", "day", "hour"},
}


def _context_quality_score(
    key: str,
    day_meta: dict[str, Any],
    month_meta: dict[str, Any],
    relations: list[dict[str, Any]],
) -> int:
    score = 52.0
    group_weights = _CONTEXT_GROUP_WEIGHTS[key]
    score += group_weights.get(str(day_meta["stem_group"]), 0.0)
    score += group_weights.get(str(day_meta["branch_group"]), 0.0)
    score += group_weights.get(str(month_meta["stem_group"]), 0.0) * 0.30
    score += group_weights.get(str(month_meta["branch_group"]), 0.0) * 0.30

    day_anchor = dict(day_meta.get("anchor") or {})
    month_anchor = dict(month_meta.get("anchor") or {})
    score += min(10.0, len(day_anchor.get("useful_element_hits") or []) * 4.0)
    score -= min(12.0, len(day_anchor.get("caution_element_hits") or []) * 5.0)
    score += min(4.0, len(month_anchor.get("useful_element_hits") or []) * 1.5)
    score -= min(5.0, len(month_anchor.get("caution_element_hits") or []) * 2.0)

    focus_positions = _CONTEXT_POSITIONS[key]
    for relation in relations:
        if not focus_positions.intersection(set(relation.get("positions") or [])):
            continue
        phase_weight = 1.0 if relation.get("source") == "day_flow" else 0.35
        polarity = str(relation.get("polarity") or "mixed")
        relation_type = str(relation.get("relation_type") or "")
        if polarity == "supportive":
            score += 4.5 * phase_weight
        elif polarity == "burdensome":
            score -= 6.0 * phase_weight
        else:
            score -= 1.0 * phase_weight
        if relation_type in {"clash", "punishment", "harm", "break", "self_punishment"}:
            score -= 3.0 * phase_weight * max(0.45, float(relation.get("effective_friction") or 0.0))
    return _clip(score)


def build_daily_fortune_signal(
    chart: BirthChartResult,
    structure: ChartStructure,
    target_date: date,
    *,
    timezone_offset_minutes: int = 540,
) -> dict[str, Any]:
    """Calculate chart-specific daily signals without customer presentation logic."""

    day_pillar = day_pillar_for_date(target_date.year, target_date.month, target_date.day)
    saju_year, month_index, solar_month_pillar = _solar_month_pillar_for_date(
        target_date,
        timezone_offset_minutes=timezone_offset_minutes,
    )
    effective_year_pillar = year_pillar_for_gregorian_year(saju_year)

    day_scores, day_interactions, day_meta = _phase_domain_scores(
        chart,
        structure,
        day_pillar,
        source="day_flow",
        ten_god_weight=0.70,
        governance_weight=0.58,
    )
    month_scores, month_interactions, month_meta = _phase_domain_scores(
        chart,
        structure,
        solar_month_pillar,
        source="month_flow",
        ten_god_weight=0.46,
        governance_weight=0.38,
    )

    domain_components: dict[str, dict[str, Any]] = {}
    for domain in day_scores:
        day_component = day_scores[domain]
        month_component = month_scores[domain]
        domain_components[domain] = {
            component: _clip(
                float(day_component[component]) * 0.74
                + float(month_component[component]) * 0.26
            )
            for component in ("opportunity", "risk", "change", "probability")
        }
        domain_components[domain]["basis_codes"] = list(
            dict.fromkeys(
                [
                    *list(day_component.get("basis_codes") or []),
                    *list(month_component.get("basis_codes") or []),
                ]
            )
        )
        domain_components[domain]["counter_signals"] = list(
            dict.fromkeys(
                [
                    *list(day_component.get("counter_signals") or []),
                    *list(month_component.get("counter_signals") or []),
                ]
            )
        )

    relations = [
        *_relation_payload(structure, day_interactions, source="day_flow"),
        *_relation_payload(structure, month_interactions, source="month_flow"),
    ]
    return {
        "version": DAILY_FORTUNE_SIGNAL_VERSION,
        "date": target_date.isoformat(),
        "effective_saju_year": saju_year,
        "month_index": month_index,
        "year_pillar": effective_year_pillar.label,
        "month_pillar": solar_month_pillar.label,
        "day_pillar": day_pillar.label,
        "day_stem_ten_god": day_meta["stem_ten_god"],
        "day_branch_ten_god": day_meta["branch_ten_god"],
        "domain_components": domain_components,
        "context_quality": {
            key: _context_quality_score(key, day_meta, month_meta, relations)
            for key in ("mood", "social", "family")
        },
        "anchor_hits": {
            "day": day_meta["anchor"],
            "month": month_meta["anchor"],
        },
        "relations": relations,
    }
