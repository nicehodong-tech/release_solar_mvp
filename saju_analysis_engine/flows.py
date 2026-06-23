"""Daeun and annual-flow reaction scoring."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from saju_birth_engine.models import BirthChartResult, DaeunEntry, Pillar
from saju_birth_engine.astronomy import solar_longitude_crossing_utc
from saju_birth_engine.constants import SAJU_MONTH_BOUNDARIES
from saju_birth_engine.pillars import month_pillar, year_pillar_for_gregorian_year

from .auxiliary import SAL_GROUPS
from .constants import (
    BRANCH_HIDDEN_STEMS,
    DOMAIN_ORDER,
    ELEMENTS,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .interactions import find_interactions, flow_interactions
from .models import ChartStructure, FlowSignal, SubPeriodSignal
from .month_governance import evaluate_month_governed_signal, governance_event_adjustment
from .relation_polarity import branch_relation_polarity
from .ten_gods import main_hidden_stem, ten_god_for


CONNECTIVE_BRANCH_RELATIONS = {"six_combine", "three_harmony", "three_harmony_half", "three_meeting"}


def _clip(value: float) -> int:
    return max(0, min(100, round(value)))


def _clip_opportunity(value: float) -> int:
    clipped = _clip(value)
    if clipped <= 94:
        return clipped
    return _clip(94 + round((clipped - 94) * 0.35))


def _active_daeun(chart: BirthChartResult, target_year: int) -> DaeunEntry | None:
    birth_year = datetime.fromisoformat(chart.normalized_birth_datetime).year
    age = target_year - birth_year
    for entry in chart.daeun_sequence:
        if entry.start_age_years <= age < entry.end_age_years:
            return entry
    return None


def _infer_gender(chart: BirthChartResult) -> str | None:
    if chart.daeun_direction not in {"forward", "backward"}:
        return None
    yang_year = chart.year_pillar.stem_index % 2 == 0
    if yang_year:
        return "male" if chart.daeun_direction == "forward" else "female"
    return "male" if chart.daeun_direction == "backward" else "female"


def _day_group_sal_targets(day_branch_key: str) -> dict[str, str]:
    for branches, _, targets in SAL_GROUPS:
        if day_branch_key in branches:
            return targets
    return {}


def _apply_ten_god_score(domain_scores: dict[str, dict[str, Any]], ten_god: str, weight: float, basis_prefix: str, gender: str | None) -> None:
    group = TEN_GOD_GROUPS[ten_god]
    for domain in DOMAIN_ORDER:
        domain_scores[domain].setdefault("basis_codes", [])
        domain_scores[domain].setdefault("counter_signals", [])

    if group == "wealth":
        domain_scores["money"]["opportunity"] += 18 * weight
        domain_scores["money"]["change"] += 7 * weight
        domain_scores["money"]["basis_codes"].append(f"{basis_prefix}_{ten_god}")
        if gender == "male":
            domain_scores["love"]["opportunity"] += 13 * weight
            domain_scores["marriage"]["opportunity"] += 16 * weight if ten_god == "jeong_jae" else 10 * weight
            domain_scores["love"]["basis_codes"].append(f"{basis_prefix}_male_spouse_star")
            domain_scores["marriage"]["basis_codes"].append(f"{basis_prefix}_male_spouse_star")
    elif group == "output":
        domain_scores["money"]["opportunity"] += 8 * weight
        domain_scores["career"]["opportunity"] += 8 * weight
        domain_scores["career"]["change"] += 9 * weight
        domain_scores["money"]["basis_codes"].append(f"{basis_prefix}_{ten_god}")
        domain_scores["career"]["basis_codes"].append(f"{basis_prefix}_{ten_god}")
        if ten_god == "sang_gwan":
            domain_scores["career"]["risk"] += 7 * weight
            domain_scores["career"]["counter_signals"].append(f"{basis_prefix}_sang_gwan_pressure")
    elif group == "officer":
        domain_scores["career"]["opportunity"] += 18 * weight
        domain_scores["career"]["change"] += 7 * weight
        domain_scores["career"]["basis_codes"].append(f"{basis_prefix}_{ten_god}")
        if gender == "female":
            domain_scores["love"]["opportunity"] += 13 * weight
            domain_scores["marriage"]["opportunity"] += 16 * weight if ten_god == "jeong_gwan" else 10 * weight
            domain_scores["love"]["basis_codes"].append(f"{basis_prefix}_female_spouse_star")
            domain_scores["marriage"]["basis_codes"].append(f"{basis_prefix}_female_spouse_star")
    elif group == "resource":
        domain_scores["career"]["opportunity"] += 9 * weight
        domain_scores["career"]["risk"] -= 3 * weight
        domain_scores["career"]["basis_codes"].append(f"{basis_prefix}_{ten_god}")
        domain_scores["marriage"]["risk"] -= 2 * weight
    elif group == "peer":
        domain_scores["money"]["risk"] += 10 * weight
        domain_scores["money"]["counter_signals"].append(f"{basis_prefix}_{ten_god}_competition")
        domain_scores["career"]["change"] += 5 * weight


def _pattern_elements(structure: ChartStructure) -> tuple[set[str], set[str]]:
    useful = {
        str(getattr(candidate, "element", ""))
        for candidate in structure.pattern_profile.useful_element_candidates
        if str(getattr(candidate, "element", ""))
    }
    caution = {
        str(getattr(candidate, "element", ""))
        for candidate in structure.pattern_profile.caution_element_candidates
        if str(getattr(candidate, "element", ""))
    }
    return useful, caution


def _append_element_context_codes(
    basis_codes: list[str],
    counter_signals: list[str],
    structure: ChartStructure,
    source: str,
    element: str,
) -> None:
    pattern_useful, pattern_caution = _pattern_elements(structure)
    if element in structure.element_profile.useful_elements:
        basis_codes.append(f"{source}_useful_element_{element}")
    if element in structure.element_profile.caution_elements:
        counter_signals.append(f"{source}_caution_element_{element}")
    if element in pattern_useful:
        basis_codes.append(f"{source}_pattern_useful_element_{element}")
    if element in pattern_caution and element not in pattern_useful:
        counter_signals.append(f"{source}_pattern_caution_element_{element}")
    decision = evaluate_month_governed_signal(
        structure.month_governance_profile,
        signal_key=f"flow_element_context_{source}_{element}",
        signal_type="flow_element_context",
        elements=[element],
        positions=[source, "flow"],
    )
    basis_codes.extend(decision.basis_codes)
    counter_signals.extend(decision.counter_signals)


def _pillar_anchor_terms(day_stem_key: str, pillar: Pillar) -> dict[str, set[str]]:
    hidden_stems = [stem_key for stem_key, _weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]]
    hidden_ten_gods = [ten_god_for(day_stem_key, stem_key) for stem_key in hidden_stems]
    return {
        "stems": {pillar.stem_key, *hidden_stems},
        "elements": {
            STEM_METADATA[pillar.stem_key]["element"],
            *[STEM_METADATA[stem_key]["element"] for stem_key in hidden_stems],
        },
        "ten_gods": {
            ten_god_for(day_stem_key, pillar.stem_key),
            ten_god_for(day_stem_key, main_hidden_stem(pillar.branch_key)),
            *hidden_ten_gods,
        },
    }


def _flow_anchor_hits_for_pillar(
    structure: ChartStructure,
    *,
    source: str,
    day_stem_key: str,
    pillar: Pillar,
) -> dict[str, Any]:
    terms = _pillar_anchor_terms(day_stem_key, pillar)
    month_profile = structure.month_governance_profile
    phase = getattr(month_profile, "month_hidden_phase", None)
    useful_elements = set(month_profile.useful_elements or [])
    caution_elements = set(month_profile.caution_elements or [])
    hits: list[str] = []
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    natal_terms = _natal_stem_branch_terms(structure)
    flow_hidden_stems = [stem_key for stem_key, _weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]]
    rooted_natal_visible_stems = sorted(natal_terms["visible_stems"].intersection(flow_hidden_stems))
    protruded_natal_hidden_stems = sorted(natal_terms["hidden_stems"].intersection({pillar.stem_key}))
    repeated_natal_visible_stems = sorted(natal_terms["visible_stems"].intersection({pillar.stem_key}))
    repeated_natal_branches = sorted(natal_terms["branches"].intersection({pillar.branch_key}))

    def add_stem_activation(kind: str, stem_key: str) -> None:
        element = STEM_METADATA[stem_key]["element"]
        ten_god = ten_god_for(day_stem_key, stem_key)
        hits.append(kind)
        basis_codes.append(f"{source}_{kind}_{stem_key}_{ten_god}")
        if element in useful_elements:
            basis_codes.append(f"{source}_{kind}_supports_month_{element}")
        if element in caution_elements and element not in useful_elements:
            counter_signals.append(f"{source}_{kind}_pressures_month_{element}")

    if month_profile.month_element in terms["elements"]:
        hits.append("month_element")
        basis_codes.append(f"{source}_touches_month_element_{month_profile.month_element}")
    if month_profile.month_command_ten_god in terms["ten_gods"]:
        hits.append("month_command_ten_god")
        basis_codes.append(f"{source}_touches_month_command_{month_profile.month_command_ten_god}")
    if phase is not None and getattr(phase, "active_stem", ""):
        active_stem = str(phase.active_stem)
        active_element = str(phase.active_element)
        active_ten_god = str(phase.active_ten_god)
        if active_stem in terms["stems"]:
            hits.append("month_hidden_phase_stem")
            basis_codes.append(f"{source}_touches_month_hidden_phase_stem_{active_stem}")
        if active_element in terms["elements"]:
            hits.append("month_hidden_phase_element")
            basis_codes.append(f"{source}_touches_month_hidden_phase_element_{active_element}")
        if active_ten_god in terms["ten_gods"]:
            hits.append("month_hidden_phase_ten_god")
            basis_codes.append(f"{source}_touches_month_hidden_phase_ten_god_{active_ten_god}")

        phase_fit = month_profile.element_fits.get(active_element)
        if phase_fit is not None and any(hit.startswith("month_hidden_phase") for hit in hits):
            if phase_fit.pressure_score > phase_fit.support_score:
                counter_signals.append(f"{source}_activates_pressure_month_hidden_phase_{active_element}")
            elif phase_fit.support_score:
                basis_codes.append(f"{source}_activates_support_month_hidden_phase_{active_element}")

    useful_hits = sorted(terms["elements"] & useful_elements)
    caution_hits = sorted((terms["elements"] & caution_elements) - set(useful_hits))
    basis_codes.extend(f"{source}_touches_month_useful_element_{element}" for element in useful_hits)
    counter_signals.extend(f"{source}_touches_month_caution_element_{element}" for element in caution_hits)
    for stem_key in rooted_natal_visible_stems:
        add_stem_activation("roots_natal_visible_stem", stem_key)
    for stem_key in protruded_natal_hidden_stems:
        add_stem_activation("protrudes_natal_hidden_stem", stem_key)
    for stem_key in repeated_natal_visible_stems:
        add_stem_activation("repeats_natal_visible_stem", stem_key)
    if repeated_natal_branches:
        hits.append("repeats_natal_branch")
        basis_codes.extend(f"{source}_repeats_natal_branch_{branch}" for branch in repeated_natal_branches)

    return {
        "source": source,
        "pillar": pillar.label,
        "branch": pillar.branch_key,
        "stem": pillar.stem_key,
        "hits": list(dict.fromkeys(hits)),
        "useful_element_hits": useful_hits,
        "caution_element_hits": caution_hits,
        "rooted_natal_visible_stems": rooted_natal_visible_stems,
        "protruded_natal_hidden_stems": protruded_natal_hidden_stems,
        "repeated_natal_visible_stems": repeated_natal_visible_stems,
        "repeated_natal_branches": repeated_natal_branches,
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _flow_source_context(
    *,
    source: str,
    day_stem_key: str,
    pillar: Pillar,
) -> dict[str, Any]:
    main_stem = main_hidden_stem(pillar.branch_key)
    hidden_stems = [stem_key for stem_key, _weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]]
    return {
        "source": source,
        "pillar": pillar.label,
        "stem": pillar.stem_key,
        "branch": pillar.branch_key,
        "stem_element": STEM_METADATA[pillar.stem_key]["element"],
        "branch_main_element": STEM_METADATA[main_stem]["element"],
        "hidden_elements": list(
            dict.fromkeys(STEM_METADATA[stem_key]["element"] for stem_key in hidden_stems)
        ),
        "stem_ten_god": ten_god_for(day_stem_key, pillar.stem_key),
        "branch_main_ten_god": ten_god_for(day_stem_key, main_stem),
        "hidden_ten_gods": list(dict.fromkeys(ten_god_for(day_stem_key, stem_key) for stem_key in hidden_stems)),
        "stem_role": "visible_role" if source == "annual" else "long_term_visible_role",
        "branch_role": "annual_reality_base" if source == "annual" else "decade_environment_base",
        "stem_operation": "겉으로 드러나는 선택과 명분" if source == "annual" else "오래 지속되는 역할 변화",
        "branch_operation": "그해 실제 생활 조건과 사건 무대" if source == "annual" else "십 년 단위의 생활 기반과 환경",
        "hidden_operation": "겉으로 약해도 사건의 재료로 남는 지장간",
    }


def _natal_stem_branch_terms(structure: ChartStructure) -> dict[str, set[str]]:
    visible_stems: set[str] = set()
    hidden_stems: set[str] = set()
    branches: set[str] = set()
    for signal in structure.position_signals.values():
        visible_stems.add(signal.stem_key)
        branches.add(signal.branch_key)
        hidden_stems.update(stem_key for stem_key, _weight in BRANCH_HIDDEN_STEMS[signal.branch_key])
    return {
        "visible_stems": visible_stems,
        "hidden_stems": hidden_stems,
        "branches": branches,
    }


def _flow_anchor_direction(anchor: dict[str, Any]) -> dict[str, Any]:
    useful_count = len(list(anchor.get("useful_element_hits") or []))
    caution_count = len(list(anchor.get("caution_element_hits") or []))
    support_codes = [
        str(code)
        for code in list(anchor.get("basis_codes") or [])
        if "support" in str(code) or "useful" in str(code)
    ]
    pressure_codes = [
        str(code)
        for code in list(anchor.get("counter_signals") or [])
        if "pressure" in str(code) or "caution" in str(code) or "burdens" in str(code)
    ]
    support_score = useful_count * 2 + min(2, len(support_codes))
    pressure_score = caution_count * 2 + min(2, len(pressure_codes))
    if support_score > pressure_score:
        status = "supportive"
    elif pressure_score > support_score:
        status = "burdensome"
    elif support_score and pressure_score:
        status = "mixed"
    else:
        status = "neutral"
    return {
        "source": str(anchor.get("source") or ""),
        "status": status,
        "support_score": support_score,
        "pressure_score": pressure_score,
        "useful_element_hits": list(anchor.get("useful_element_hits") or []),
        "caution_element_hits": list(anchor.get("caution_element_hits") or []),
        "hits": list(anchor.get("hits") or []),
    }


def _flow_compound_direction(
    annual_direction: dict[str, Any],
    daeun_direction: dict[str, Any] | None,
) -> dict[str, Any]:
    annual_status = str(annual_direction.get("status") or "neutral")
    daeun_status = str((daeun_direction or {}).get("status") or "none")
    if daeun_direction is None:
        grade = f"annual_{annual_status}"
    elif annual_status == "supportive" and daeun_status == "supportive":
        grade = "daeun_supports_annual_support"
    elif annual_status == "burdensome" and daeun_status == "supportive":
        grade = "daeun_supports_annual_burden"
    elif annual_status == "supportive" and daeun_status == "burdensome":
        grade = "daeun_burden_annual_support"
    elif annual_status == "burdensome" and daeun_status == "burdensome":
        grade = "daeun_burden_annual_burden"
    elif "mixed" in {annual_status, daeun_status}:
        grade = "daeun_annual_mixed"
    else:
        grade = "daeun_annual_neutral"
    return {
        "grade": grade,
        "annual_status": annual_status,
        "daeun_status": daeun_status,
        "annual_support_score": int(annual_direction.get("support_score") or 0),
        "annual_pressure_score": int(annual_direction.get("pressure_score") or 0),
        "daeun_support_score": int((daeun_direction or {}).get("support_score") or 0),
        "daeun_pressure_score": int((daeun_direction or {}).get("pressure_score") or 0),
    }


def _flow_compound_score_adjustment(compound: dict[str, Any]) -> dict[str, float]:
    grade = str(compound.get("grade") or "")
    if grade == "daeun_supports_annual_support":
        return {"opportunity": 3.2, "risk": 0.0, "change": 1.2, "probability": 2.2}
    if grade == "daeun_supports_annual_burden":
        return {"opportunity": 0.8, "risk": 3.0, "change": 2.0, "probability": -0.4}
    if grade == "daeun_burden_annual_support":
        return {"opportunity": 1.8, "risk": 1.8, "change": 1.4, "probability": 0.4}
    if grade == "daeun_burden_annual_burden":
        return {"opportunity": -0.6, "risk": 4.2, "change": 2.2, "probability": -1.2}
    if grade == "daeun_annual_mixed":
        return {"opportunity": 1.0, "risk": 1.8, "change": 1.6, "probability": 0.0}
    if grade == "annual_supportive":
        return {"opportunity": 1.4, "risk": 0.0, "change": 0.6, "probability": 0.8}
    if grade == "annual_burdensome":
        return {"opportunity": 0.0, "risk": 1.8, "change": 0.8, "probability": -0.4}
    return {"opportunity": 0.0, "risk": 0.0, "change": 0.0, "probability": 0.0}


def _flow_cross_interactions(year_pillar: Pillar, daeun_pillar: Pillar | None) -> list[Any]:
    if daeun_pillar is None:
        return []
    return [
        item
        for item in find_interactions(
            {
                "daeun": daeun_pillar.branch_key,
                "year_flow": year_pillar.branch_key,
            }
        )
        if {"daeun", "year_flow"}.issubset(set(item.positions))
    ]


def _flow_activation_context(
    structure: ChartStructure,
    *,
    day_stem_key: str,
    year_pillar: Pillar,
    daeun_pillar: Pillar | None,
    interactions: list[Any],
) -> dict[str, Any]:
    month_profile = structure.month_governance_profile
    phase = getattr(month_profile, "month_hidden_phase", None)
    anchor_hits = [
        _flow_anchor_hits_for_pillar(
            structure,
            source="annual",
            day_stem_key=day_stem_key,
            pillar=year_pillar,
        )
    ]
    source_contexts = {
        "annual": _flow_source_context(
            source="annual",
            day_stem_key=day_stem_key,
            pillar=year_pillar,
        )
    }
    if daeun_pillar is not None:
        anchor_hits.append(
            _flow_anchor_hits_for_pillar(
                structure,
                source="daeun",
                day_stem_key=day_stem_key,
                pillar=daeun_pillar,
            )
        )
        source_contexts["daeun"] = _flow_source_context(
            source="daeun",
            day_stem_key=day_stem_key,
            pillar=daeun_pillar,
        )

    relation_hits = []
    daeun_annual_relation_hits = []
    for interaction in interactions:
        positions = list(getattr(interaction, "positions", []) or [])
        relation_payload = {
            "relation_type": str(getattr(interaction, "relation_type", "") or ""),
            "basis_code": str(getattr(interaction, "basis_code", "") or ""),
            "positions": positions,
        }
        if "month" in positions:
            relation_hits.append(relation_payload)
        if {"daeun", "year_flow"}.issubset(set(positions)):
            daeun_annual_relation_hits.append(relation_payload)

    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for item in anchor_hits:
        basis_codes.extend(list(item.get("basis_codes") or []))
        counter_signals.extend(list(item.get("counter_signals") or []))
    basis_codes.extend(f"flow_relation_touches_month_{item['basis_code']}" for item in relation_hits if item.get("basis_code"))
    basis_codes.extend(
        f"flow_daeun_annual_relation_{item['basis_code']}"
        for item in daeun_annual_relation_hits
        if item.get("basis_code")
    )

    useful_hit_count = sum(len(list(item.get("useful_element_hits") or [])) for item in anchor_hits)
    caution_hit_count = sum(len(list(item.get("caution_element_hits") or [])) for item in anchor_hits)
    phase_hit_count = sum(
        1
        for item in anchor_hits
        for hit in list(item.get("hits") or [])
        if str(hit).startswith("month_hidden_phase")
    )
    directions = {
        str(item.get("source") or ""): _flow_anchor_direction(item)
        for item in anchor_hits
        if str(item.get("source") or "")
    }
    compound_direction = _flow_compound_direction(
        directions.get("annual", {"status": "neutral"}),
        directions.get("daeun"),
    )
    basis_codes.append(f"flow_compound_{compound_direction['grade']}")
    if str(compound_direction.get("annual_status")) == "supportive":
        basis_codes.append("flow_annual_supportive_event")
    elif str(compound_direction.get("annual_status")) == "burdensome":
        counter_signals.append("flow_annual_burdensome_event")
    if str(compound_direction.get("daeun_status")) == "supportive":
        basis_codes.append("flow_daeun_supportive_environment")
    elif str(compound_direction.get("daeun_status")) == "burdensome":
        counter_signals.append("flow_daeun_burdensome_environment")

    return {
        "version": "flow_activation_context_v2",
        "hierarchy": {
            "natal_role": "base_structure",
            "daeun_role": "long_term_environment",
            "annual_role": "year_event_trigger",
        },
        "month_anchor": {
            "month_branch": month_profile.month_branch,
            "month_element": month_profile.month_element,
            "month_command_ten_god": month_profile.month_command_ten_god,
            "month_command_group": month_profile.month_command_group,
            "active_month_hidden_phase": {
                "phase": str(getattr(phase, "active_phase", "") or ""),
                "stem": str(getattr(phase, "active_stem", "") or ""),
                "element": str(getattr(phase, "active_element", "") or ""),
                "ten_god": str(getattr(phase, "active_ten_god", "") or ""),
                "ten_god_group": str(getattr(phase, "active_ten_god_group", "") or ""),
            }
            if phase is not None
            else None,
        },
        "source_contexts": source_contexts,
        "anchor_hits": anchor_hits,
        "relation_hits": relation_hits,
        "daeun_annual_relation_hits": daeun_annual_relation_hits,
        "source_directions": directions,
        "compound_direction": compound_direction,
        "useful_hit_count": useful_hit_count,
        "caution_hit_count": caution_hit_count,
        "phase_hit_count": phase_hit_count,
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _apply_flow_governance_score(
    domain_scores: dict[str, dict[str, Any]],
    structure: ChartStructure,
    *,
    source: str,
    elements: list[str] | None = None,
    ten_gods: list[str] | None = None,
    positions: list[str] | None = None,
    weight: float = 1.0,
) -> None:
    month_governance_profile = getattr(structure, "month_governance_profile", None)
    if month_governance_profile is None:
        return
    for domain in DOMAIN_ORDER:
        decision = evaluate_month_governed_signal(
            month_governance_profile,
            signal_key=f"flow_governance_{source}_{domain}",
            signal_type="flow_activation",
            elements=elements or [],
            ten_gods=ten_gods or [],
            positions=positions or [source, "flow"],
            domain=domain,
        )
        adjustment = governance_event_adjustment(decision)
        for metric in ("opportunity", "risk", "change", "probability"):
            if metric in domain_scores[domain]:
                domain_scores[domain][metric] += float(adjustment.get(metric, 0) or 0) * weight
        domain_scores[domain]["basis_codes"].extend(list(adjustment.get("basis_codes", []) or []))
        domain_scores[domain]["counter_signals"].extend(list(adjustment.get("counter_signals", []) or []))


def _apply_interaction_score(domain_scores: dict[str, dict[str, Any]], structure: ChartStructure, interaction: Any, basis_code: str) -> None:
    relation_type = interaction.relation_type
    positions = interaction.positions
    touches_day = "day" in positions
    touches_month = "month" in positions
    polarity = branch_relation_polarity(structure.element_profile, interaction, structure.pattern_profile)
    supportive = polarity.polarity == "supportive"
    burdensome = polarity.polarity == "burdensome"
    mixed = polarity.polarity == "mixed"
    _apply_flow_governance_score(
        domain_scores,
        structure,
        source=basis_code,
        elements=list(polarity.activated_elements),
        positions=[*interaction.positions, "flow_relation"],
        weight=1.0 if "month" in interaction.positions else 0.58,
    )
    support_code = f"{basis_code}_useful_relation"
    burden_code = f"{basis_code}_burden_relation"
    overuse_code = f"{basis_code}_overuse_relation"

    def apply_overuse(weight: float = 1.0) -> None:
        if not polarity.overuse_elements:
            return
        if touches_day:
            domain_scores["love"]["risk"] += 2 * weight
            domain_scores["marriage"]["risk"] += 2 * weight
            domain_scores["love"]["counter_signals"].append(overuse_code)
            domain_scores["marriage"]["counter_signals"].append(overuse_code)
        if touches_month:
            domain_scores["career"]["risk"] += 2 * weight
            domain_scores["money"]["risk"] += 1 * weight
            domain_scores["career"]["counter_signals"].append(overuse_code)
            domain_scores["money"]["counter_signals"].append(overuse_code)
        for domain in interaction.domain_links:
            if domain in domain_scores:
                domain_scores[domain]["risk"] += 1 * weight
                domain_scores[domain]["counter_signals"].append(overuse_code)

    if relation_type in CONNECTIVE_BRANCH_RELATIONS:
        connect_weight = 0.62 if relation_type == "three_harmony_half" else 1.0
        if burdensome:
            if touches_day:
                domain_scores["love"]["risk"] += 7 * connect_weight
                domain_scores["marriage"]["risk"] += 7 * connect_weight
                domain_scores["love"]["counter_signals"].append(burden_code)
                domain_scores["marriage"]["counter_signals"].append(burden_code)
            if touches_month:
                domain_scores["career"]["risk"] += 6 * connect_weight
                domain_scores["career"]["counter_signals"].append(burden_code)
            domain_scores["money"]["risk"] += 4 * connect_weight
            return
        if touches_day:
            domain_scores["love"]["opportunity"] += 10 * connect_weight
            domain_scores["marriage"]["opportunity"] += 10 * connect_weight
            domain_scores["love"]["basis_codes"].append(basis_code)
            domain_scores["marriage"]["basis_codes"].append(basis_code)
        if touches_month:
            domain_scores["career"]["opportunity"] += 8 * connect_weight
            domain_scores["career"]["basis_codes"].append(basis_code)
        if supportive or mixed:
            for domain in DOMAIN_ORDER:
                domain_scores[domain]["basis_codes"].append(support_code)
        if supportive or mixed:
            apply_overuse(connect_weight)
        if mixed:
            if touches_day:
                domain_scores["love"]["risk"] += 5 * connect_weight
                domain_scores["marriage"]["risk"] += 5 * connect_weight
                domain_scores["love"]["counter_signals"].append(burden_code)
                domain_scores["marriage"]["counter_signals"].append(burden_code)
            if touches_month:
                domain_scores["career"]["risk"] += 4 * connect_weight
                domain_scores["career"]["counter_signals"].append(burden_code)
            domain_scores["money"]["risk"] += 3 * connect_weight
    elif relation_type == "clash":
        if supportive:
            if touches_day:
                domain_scores["love"]["opportunity"] += 9
                domain_scores["marriage"]["opportunity"] += 8
                domain_scores["love"]["change"] += 18
                domain_scores["marriage"]["change"] += 18
                domain_scores["love"]["basis_codes"].append(support_code)
                domain_scores["marriage"]["basis_codes"].append(support_code)
            if touches_month:
                domain_scores["career"]["opportunity"] += 7
                domain_scores["career"]["change"] += 18
                domain_scores["career"]["basis_codes"].append(support_code)
            domain_scores["money"]["change"] += 6
            apply_overuse()
            return
        if touches_day:
            risk_add = 13 if mixed else 18
            domain_scores["love"]["risk"] += risk_add
            domain_scores["marriage"]["risk"] += risk_add + 2
            domain_scores["love"]["change"] += 18
            domain_scores["marriage"]["change"] += 18
            domain_scores["love"]["counter_signals"].append(burden_code if burdensome else basis_code)
            domain_scores["marriage"]["counter_signals"].append(burden_code if burdensome else basis_code)
            if mixed:
                domain_scores["love"]["basis_codes"].append(support_code)
                domain_scores["marriage"]["basis_codes"].append(support_code)
        if touches_month:
            domain_scores["career"]["risk"] += 9 if mixed else 12
            domain_scores["career"]["change"] += 18
            domain_scores["career"]["counter_signals"].append(burden_code if burdensome else basis_code)
            if mixed:
                domain_scores["career"]["basis_codes"].append(support_code)
        domain_scores["money"]["change"] += 6
    elif relation_type in {"punishment", "harm", "break", "self_punishment"}:
        risk_add = 12 if relation_type == "punishment" else 8
        if supportive:
            if touches_day:
                domain_scores["love"]["opportunity"] += 5
                domain_scores["marriage"]["opportunity"] += 5
                domain_scores["love"]["basis_codes"].append(support_code)
                domain_scores["marriage"]["basis_codes"].append(support_code)
            if touches_month:
                domain_scores["career"]["opportunity"] += 5
                domain_scores["career"]["basis_codes"].append(support_code)
            for domain in DOMAIN_ORDER:
                domain_scores[domain]["change"] += 2
            apply_overuse()
            return
        adjusted_risk = max(4, risk_add - 3) if mixed else risk_add
        if touches_day:
            domain_scores["love"]["risk"] += adjusted_risk
            domain_scores["marriage"]["risk"] += adjusted_risk
            domain_scores["love"]["counter_signals"].append(burden_code if burdensome else basis_code)
            domain_scores["marriage"]["counter_signals"].append(burden_code if burdensome else basis_code)
            if mixed:
                domain_scores["love"]["basis_codes"].append(support_code)
                domain_scores["marriage"]["basis_codes"].append(support_code)
        if touches_month:
            domain_scores["career"]["risk"] += adjusted_risk
            domain_scores["career"]["counter_signals"].append(burden_code if burdensome else basis_code)
            if mixed:
                domain_scores["career"]["basis_codes"].append(support_code)


def _domains_for_ten_god(ten_god: str, gender: str | None) -> list[str]:
    group = TEN_GOD_GROUPS[ten_god]
    if group == "wealth":
        domains = ["money"]
        if gender == "male":
            domains.extend(["love", "marriage"])
        return domains
    if group == "officer":
        domains = ["career"]
        if gender == "female":
            domains.extend(["love", "marriage"])
        return domains
    if group == "output":
        return ["career", "money"]
    if group == "resource":
        return ["career"]
    if group == "peer":
        return ["money", "career"]
    return []


def _initial_domain_scores() -> dict[str, dict[str, Any]]:
    return {
        domain: {
            "opportunity": 42.0,
            "risk": 34.0,
            "change": 36.0,
            "probability": 0.0,
            "basis_codes": [],
            "counter_signals": [],
        }
        for domain in DOMAIN_ORDER
    }


def _finalize_domain_scores(domain_scores: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    finalized: dict[str, dict[str, Any]] = {}
    for domain, data in domain_scores.items():
        opportunity = _clip_opportunity(data["opportunity"])
        risk = _clip(data["risk"])
        change = _clip(data["change"])
        probability = _clip(opportunity * 0.58 + change * 0.27 - max(0, risk - 62) * 0.2 + 13 + float(data.get("probability", 0.0) or 0.0))
        finalized[domain] = {
            "opportunity": opportunity,
            "risk": risk,
            "change": change,
            "probability": probability,
            "basis_codes": list(dict.fromkeys(data["basis_codes"])),
            "counter_signals": list(dict.fromkeys(data["counter_signals"])),
        }
    return finalized


def _pillar_ten_gods(day_stem_key: str, pillar: Pillar) -> tuple[str, str]:
    stem_ten_god = ten_god_for(day_stem_key, pillar.stem_key)
    branch_main_ten_god = ten_god_for(day_stem_key, main_hidden_stem(pillar.branch_key))
    return stem_ten_god, branch_main_ten_god


MONTH_PERIOD_LABELS = [
    "early_spring_yin_month",
    "mid_spring_myo_month",
    "late_spring_jin_month",
    "early_summer_sa_month",
    "mid_summer_o_month",
    "late_summer_mi_month",
    "early_autumn_sin_month",
    "mid_autumn_yu_month",
    "late_autumn_sul_month",
    "early_winter_hae_month",
    "mid_winter_ja_month",
    "late_winter_chuk_month",
]

QUARTERS = [
    ("spring_quarter", [0, 1, 2]),
    ("summer_quarter", [3, 4, 5]),
    ("autumn_quarter", [6, 7, 8]),
    ("winter_quarter", [9, 10, 11]),
]


def _saju_month_periods(target_year: int, timezone_offset_minutes: int) -> list[dict[str, str]]:
    starts = [
        {
            "name": item["name"],
            "month_index": item["month_index"],
            "start_utc": solar_longitude_crossing_utc(
                target_year + 1 if item["month_index"] == 11 else target_year,
                item["longitude"],
            ),
        }
        for item in SAJU_MONTH_BOUNDARIES
    ]
    starts.sort(key=lambda item: item["month_index"])
    next_lichun = solar_longitude_crossing_utc(target_year + 1, 315.0)
    periods: list[dict[str, str]] = []

    for index, item in enumerate(starts):
        end_utc = starts[index + 1]["start_utc"] if index < len(starts) - 1 else next_lichun
        start_local = item["start_utc"] + timedelta(minutes=timezone_offset_minutes)
        end_local = end_utc + timedelta(minutes=timezone_offset_minutes)
        periods.append(
            {
                "name": item["name"],
                "start": start_local.replace(tzinfo=None).isoformat(timespec="minutes"),
                "end": end_local.replace(tzinfo=None).isoformat(timespec="minutes"),
            }
        )
    return periods


def _sub_period_signals(
    chart: BirthChartResult,
    structure: ChartStructure,
    year_pillar: Pillar,
    target_year: int,
    gender: str | None,
) -> list[SubPeriodSignal]:
    day_stem_key = chart.day_pillar.stem_key
    month_signals: list[SubPeriodSignal] = []
    month_periods = _saju_month_periods(target_year, chart.timezone_offset_minutes)

    for month_index, label in enumerate(MONTH_PERIOD_LABELS):
        pillar = month_pillar(year_pillar.stem_index, month_index)
        period = month_periods[month_index]
        stem_tg, branch_tg = _pillar_ten_gods(day_stem_key, pillar)
        focus = list(dict.fromkeys(_domains_for_ten_god(stem_tg, gender) + _domains_for_ten_god(branch_tg, gender)))
        interactions = flow_interactions(chart, "month_flow", pillar.branch_key)
        basis_codes = [f"month_pillar_{pillar.stem_key}_{pillar.branch_key}", f"month_stem_{stem_tg}", f"month_branch_{branch_tg}"]
        counter_signals: list[str] = []

        monthly_element_sources = [
            ("month_stem", STEM_METADATA[pillar.stem_key]["element"]),
            ("month_branch_main", STEM_METADATA[main_hidden_stem(pillar.branch_key)]["element"]),
            *[
                (f"month_branch_hidden_{stem_key}", STEM_METADATA[stem_key]["element"])
                for stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]
                if stem_key != main_hidden_stem(pillar.branch_key) and hidden_weight >= 0.18
            ],
        ]
        for source, element in monthly_element_sources:
            _append_element_context_codes(basis_codes, counter_signals, structure, source, element)

        for interaction in interactions:
            code = f"month_{interaction.basis_code}"
            polarity = branch_relation_polarity(structure.element_profile, interaction, structure.pattern_profile)
            if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity != "burdensome":
                basis_codes.append(code)
            if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "mixed":
                counter_signals.append(f"{code}_mixed_relation")
            if interaction.relation_type in {"clash", "punishment", "harm", "break", "self_punishment"} and polarity.polarity != "supportive":
                counter_signals.append(code)
            if polarity.polarity in {"supportive", "mixed"}:
                basis_codes.append(f"{code}_useful_relation")

        monthly_phase = _monthly_phase(stem_tg, branch_tg, focus, counter_signals)
        intensity = 34 + len(focus) * 6 + len(basis_codes) * 3 + len(interactions) * 3 - len(counter_signals) * 4
        month_signals.append(
            SubPeriodSignal(
                period_label=f"{target_year}:{period['name']}_{label}",
                period_scope="month",
                pillar=pillar.label,
                stem_ten_god=stem_tg,
                branch_main_ten_god=branch_tg,
                domain_focus=focus,
                intensity_score=_clip(intensity),
                basis_codes=list(dict.fromkeys(basis_codes)),
                counter_signals=list(dict.fromkeys(counter_signals)),
                start_datetime=period["start"],
                end_datetime=period["end"],
                monthly_phase=monthly_phase,
            )
        )

    quarter_signals: list[SubPeriodSignal] = []
    for quarter_label, month_indexes in QUARTERS:
        selected = [month_signals[index] for index in month_indexes]
        domain_focus = list(dict.fromkeys(domain for item in selected for domain in item.domain_focus))
        basis_codes = list(dict.fromkeys(code for item in selected for code in item.basis_codes))
        counter_signals = list(dict.fromkeys(code for item in selected for code in item.counter_signals))
        intensity = round(sum(item.intensity_score for item in selected) / len(selected))
        strongest = max(selected, key=lambda item: item.intensity_score)
        quarter_signals.append(
            SubPeriodSignal(
                period_label=f"{target_year}:{quarter_label}",
                period_scope="quarter",
                pillar=strongest.pillar,
                stem_ten_god=strongest.stem_ten_god,
                branch_main_ten_god=strongest.branch_main_ten_god,
                domain_focus=domain_focus,
                intensity_score=_clip(intensity),
                basis_codes=basis_codes[:12],
                counter_signals=counter_signals[:8],
                start_datetime=selected[0].start_datetime,
                end_datetime=selected[-1].end_datetime,
                monthly_phase=_quarter_phase(selected),
            )
        )

    return quarter_signals + month_signals


def _monthly_phase(stem_tg: str, branch_tg: str, focus: list[str], counter_signals: list[str]) -> str:
    ten_gods = {stem_tg, branch_tg}
    if counter_signals:
        return "conflict"
    if "money" in focus and ten_gods.intersection({"pyeon_jae", "jeong_jae"}):
        return "income"
    if "career" in focus and ten_gods.intersection({"pyeon_gwan", "jeong_gwan"}):
        return "proposal"
    if ten_gods.intersection({"pyeon_in", "jeong_in"}):
        return "contract"
    if "love" in focus or "marriage" in focus:
        return "contact"
    if ten_gods.intersection({"sik_sin", "sang_gwan"}):
        return "settlement"
    return "rest"


def _quarter_phase(selected: list[SubPeriodSignal]) -> str:
    priority = ["conflict", "income", "proposal", "contract", "contact", "settlement", "rest"]
    phases = [item.monthly_phase for item in selected]
    for phase in priority:
        if phase in phases:
            return phase
    return "unknown"


def build_flow_signals(
    chart: BirthChartResult,
    structure: ChartStructure,
    target_years: list[int],
    *,
    include_sub_periods: bool = True,
) -> list[FlowSignal]:
    signals: list[FlowSignal] = []
    day_stem_key = chart.day_pillar.stem_key
    sal_targets = _day_group_sal_targets(chart.day_pillar.branch_key)
    gender = _infer_gender(chart)

    for target_year in target_years:
        year_pillar = year_pillar_for_gregorian_year(target_year)
        active_daeun = _active_daeun(chart, target_year)
        year_stem_tg, year_branch_tg = _pillar_ten_gods(day_stem_key, year_pillar)

        domain_scores = _initial_domain_scores()
        basis_codes = [f"annual_pillar_{year_pillar.stem_key}_{year_pillar.branch_key}"]
        counter_signals: list[str] = []

        _apply_ten_god_score(domain_scores, year_stem_tg, 0.92, "year_stem", gender)
        _apply_ten_god_score(domain_scores, year_branch_tg, 0.92, "year_branch", gender)
        for hidden_stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[year_pillar.branch_key]:
            if hidden_stem_key == main_hidden_stem(year_pillar.branch_key):
                continue
            _apply_ten_god_score(
                domain_scores,
                ten_god_for(day_stem_key, hidden_stem_key),
                0.22 * hidden_weight,
                f"year_branch_hidden_{hidden_stem_key}",
                gender,
            )
        _apply_flow_governance_score(
            domain_scores,
            structure,
            source="year_pillar",
            elements=[
                STEM_METADATA[year_pillar.stem_key]["element"],
                STEM_METADATA[main_hidden_stem(year_pillar.branch_key)]["element"],
            ],
            ten_gods=[year_stem_tg, year_branch_tg],
            positions=["year_flow", "year_flow:stem", "year_flow:branch"],
            weight=0.72,
        )

        interactions = flow_interactions(chart, "year_flow", year_pillar.branch_key)
        for interaction in interactions:
            _apply_interaction_score(domain_scores, structure, interaction, interaction.basis_code)
            basis_codes.append(f"year_{interaction.basis_code}")
            polarity = branch_relation_polarity(structure.element_profile, interaction, structure.pattern_profile)
            if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "burdensome":
                counter_signals.append(f"year_{interaction.basis_code}")
            if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "mixed":
                counter_signals.append(f"year_{interaction.basis_code}_mixed_relation")
            if interaction.relation_type in {"clash", "punishment", "harm", "break", "self_punishment"} and polarity.polarity != "supportive":
                counter_signals.append(f"year_{interaction.basis_code}")
            if polarity.polarity in {"supportive", "mixed"}:
                basis_codes.append(f"year_{interaction.basis_code}_useful_relation")

        if sal_targets.get("peach_blossom") == year_pillar.branch_key:
            domain_scores["love"]["opportunity"] += 12
            domain_scores["love"]["change"] += 8
            domain_scores["love"]["basis_codes"].append("annual_peach_blossom")
            domain_scores["marriage"]["basis_codes"].append("annual_peach_blossom")
        if sal_targets.get("travel_horse") == year_pillar.branch_key:
            domain_scores["career"]["change"] += 10
            domain_scores["money"]["change"] += 6
            domain_scores["career"]["basis_codes"].append("annual_travel_horse")

        daeun_pillar_label = None
        daeun_pillar = None
        daeun_stem_tg = None
        daeun_branch_tg = None
        if active_daeun is not None:
            daeun_pillar = active_daeun.pillar
            daeun_pillar_label = daeun_pillar.label
            daeun_stem_tg, daeun_branch_tg = _pillar_ten_gods(day_stem_key, daeun_pillar)
            _apply_ten_god_score(domain_scores, daeun_stem_tg, 0.72, "daeun_stem", gender)
            _apply_ten_god_score(domain_scores, daeun_branch_tg, 1.04, "daeun_branch", gender)
            for hidden_stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[daeun_pillar.branch_key]:
                if hidden_stem_key == main_hidden_stem(daeun_pillar.branch_key):
                    continue
                _apply_ten_god_score(
                    domain_scores,
                    ten_god_for(day_stem_key, hidden_stem_key),
                    0.3 * hidden_weight,
                    f"daeun_branch_hidden_{hidden_stem_key}",
                    gender,
                )
            _apply_flow_governance_score(
                domain_scores,
                structure,
                source="daeun_pillar",
                elements=[
                    STEM_METADATA[daeun_pillar.stem_key]["element"],
                    STEM_METADATA[main_hidden_stem(daeun_pillar.branch_key)]["element"],
                ],
                ten_gods=[daeun_stem_tg, daeun_branch_tg],
                positions=["daeun", "daeun:stem", "daeun:branch"],
                weight=0.88,
            )
            daeun_interactions = flow_interactions(chart, "daeun", daeun_pillar.branch_key)
            for interaction in daeun_interactions:
                interactions.append(interaction)
                _apply_interaction_score(domain_scores, structure, interaction, interaction.basis_code)
                basis_codes.append(f"daeun_{interaction.basis_code}")
                polarity = branch_relation_polarity(structure.element_profile, interaction, structure.pattern_profile)
                if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "burdensome":
                    counter_signals.append(f"daeun_{interaction.basis_code}")
                if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "mixed":
                    counter_signals.append(f"daeun_{interaction.basis_code}_mixed_relation")
                if interaction.relation_type in {"clash", "punishment", "harm", "break", "self_punishment"} and polarity.polarity != "supportive":
                    counter_signals.append(f"daeun_{interaction.basis_code}")
                if polarity.polarity in {"supportive", "mixed"}:
                    basis_codes.append(f"daeun_{interaction.basis_code}_useful_relation")

            cross_interactions = _flow_cross_interactions(year_pillar, daeun_pillar)
            for interaction in cross_interactions:
                interactions.append(interaction)
                cross_basis_code = f"daeun_annual_{interaction.basis_code}"
                _apply_interaction_score(domain_scores, structure, interaction, cross_basis_code)
                basis_codes.append(cross_basis_code)
                polarity = branch_relation_polarity(structure.element_profile, interaction, structure.pattern_profile)
                if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "burdensome":
                    counter_signals.append(cross_basis_code)
                if interaction.relation_type in CONNECTIVE_BRANCH_RELATIONS and polarity.polarity == "mixed":
                    counter_signals.append(f"{cross_basis_code}_mixed_relation")
                if interaction.relation_type in {"clash", "punishment", "harm", "break", "self_punishment"} and polarity.polarity != "supportive":
                    counter_signals.append(cross_basis_code)
                if polarity.polarity in {"supportive", "mixed"}:
                    basis_codes.append(f"{cross_basis_code}_useful_relation")

        flow_element_sources = [
            ("annual_stem", STEM_METADATA[year_pillar.stem_key]["element"], 1.0),
            ("annual_branch_main", STEM_METADATA[main_hidden_stem(year_pillar.branch_key)]["element"], 0.85),
            *[
                (f"annual_branch_hidden_{stem_key}", STEM_METADATA[stem_key]["element"], 0.38 * weight)
                for stem_key, weight in BRANCH_HIDDEN_STEMS[year_pillar.branch_key]
                if stem_key != main_hidden_stem(year_pillar.branch_key)
            ],
        ]
        if daeun_pillar is not None:
            flow_element_sources.extend(
                [
                    ("daeun_stem", STEM_METADATA[daeun_pillar.stem_key]["element"], 0.82),
                    ("daeun_branch_main", STEM_METADATA[main_hidden_stem(daeun_pillar.branch_key)]["element"], 0.7),
                    *[
                        (f"daeun_branch_hidden_{stem_key}", STEM_METADATA[stem_key]["element"], 0.3 * weight)
                        for stem_key, weight in BRANCH_HIDDEN_STEMS[daeun_pillar.branch_key]
                        if stem_key != main_hidden_stem(daeun_pillar.branch_key)
                    ],
                ]
            )

        pattern_useful_elements, pattern_caution_elements = _pattern_elements(structure)
        for source, element, weight in flow_element_sources:
            _apply_flow_governance_score(
                domain_scores,
                structure,
                source=source,
                elements=[element],
                positions=[source, "flow"],
                weight=weight * 0.5,
            )
            if source.startswith("daeun"):
                for domain in DOMAIN_ORDER:
                    domain_scores[domain]["basis_codes"].append(f"{source}_element_{element}")
            if element in structure.element_profile.useful_elements:
                for domain in DOMAIN_ORDER:
                    domain_scores[domain]["opportunity"] += 3 * weight
                    domain_scores[domain]["basis_codes"].append(f"useful_element_{element}")
                    domain_scores[domain]["basis_codes"].append(f"{source}_useful_element_{element}")
            if element in structure.element_profile.caution_elements:
                for domain in DOMAIN_ORDER:
                    domain_scores[domain]["risk"] += 3 * weight
                    domain_scores[domain]["counter_signals"].append(f"caution_element_{element}")
                    domain_scores[domain]["counter_signals"].append(f"{source}_caution_element_{element}")
            if element in pattern_useful_elements:
                basis_codes.append(f"{source}_pattern_useful_element_{element}")
                for domain in DOMAIN_ORDER:
                    domain_scores[domain]["basis_codes"].append(f"{source}_pattern_useful_element_{element}")
            if element in pattern_caution_elements and element not in pattern_useful_elements:
                counter_signals.append(f"{source}_pattern_caution_element_{element}")
                for domain in DOMAIN_ORDER:
                    domain_scores[domain]["counter_signals"].append(f"{source}_pattern_caution_element_{element}")

        if "hurting_officer_meets_officer" in structure.ten_god_profile.important_pairs:
            domain_scores["career"]["risk"] += 8
            domain_scores["career"]["counter_signals"].append("natal_hurting_officer_meets_officer")
        if "peer_wealth_competition" in structure.ten_god_profile.important_pairs:
            domain_scores["money"]["risk"] += 8
            domain_scores["money"]["counter_signals"].append("natal_peer_wealth_competition")

        activation_context = _flow_activation_context(
            structure,
            day_stem_key=day_stem_key,
            year_pillar=year_pillar,
            daeun_pillar=daeun_pillar,
            interactions=interactions,
        )
        basis_codes.extend(list(activation_context.get("basis_codes") or []))
        counter_signals.extend(list(activation_context.get("counter_signals") or []))
        useful_hit_count = int(activation_context.get("useful_hit_count") or 0)
        caution_hit_count = int(activation_context.get("caution_hit_count") or 0)
        phase_hit_count = int(activation_context.get("phase_hit_count") or 0)
        rooting_hit_count = sum(
            len(list(item.get("rooted_natal_visible_stems") or []))
            for item in list(activation_context.get("anchor_hits") or [])
            if isinstance(item, dict)
        )
        protrusion_hit_count = sum(
            len(list(item.get("protruded_natal_hidden_stems") or []))
            for item in list(activation_context.get("anchor_hits") or [])
            if isinstance(item, dict)
        )
        repeated_branch_count = sum(
            len(list(item.get("repeated_natal_branches") or []))
            for item in list(activation_context.get("anchor_hits") or [])
            if isinstance(item, dict)
        )
        for domain in DOMAIN_ORDER:
            domain_scores[domain]["basis_codes"].extend(list(activation_context.get("basis_codes") or []))
            domain_scores[domain]["counter_signals"].extend(list(activation_context.get("counter_signals") or []))
            compound_adjustment = _flow_compound_score_adjustment(dict(activation_context.get("compound_direction") or {}))
            for metric, adjustment in compound_adjustment.items():
                if metric in domain_scores[domain]:
                    domain_scores[domain][metric] += adjustment
            if useful_hit_count:
                domain_scores[domain]["opportunity"] += min(5, useful_hit_count * 1.4)
            if caution_hit_count:
                domain_scores[domain]["risk"] += min(5, caution_hit_count * 1.4)
            if phase_hit_count:
                domain_scores[domain]["change"] += min(3, phase_hit_count)
            if rooting_hit_count:
                domain_scores[domain]["probability"] += min(3.2, rooting_hit_count * 0.9)
                domain_scores[domain]["change"] += min(2.4, rooting_hit_count * 0.6)
            if protrusion_hit_count:
                domain_scores[domain]["opportunity"] += min(3.4, protrusion_hit_count * 0.85)
                domain_scores[domain]["change"] += min(2.8, protrusion_hit_count * 0.7)
            if repeated_branch_count:
                domain_scores[domain]["change"] += min(2.2, repeated_branch_count * 0.7)

        finalized = _finalize_domain_scores(domain_scores)
        sub_period_signals = (
            _sub_period_signals(chart, structure, year_pillar, target_year, gender)
            if include_sub_periods
            else []
        )
        activated_elements = list(
            dict.fromkeys(
                [element for _, element, _ in flow_element_sources]
            )
        )

        signals.append(
            FlowSignal(
                period_label=str(target_year),
                period_scope="year",
                year=target_year,
                year_pillar=year_pillar.label,
                year_stem_ten_god=year_stem_tg,
                year_branch_main_ten_god=year_branch_tg,
                daeun_pillar=daeun_pillar_label,
                daeun_stem_ten_god=daeun_stem_tg,
                daeun_branch_main_ten_god=daeun_branch_tg,
                branch_interactions=interactions,
                activated_elements=[element for element in ELEMENTS if element in activated_elements],
                domain_scores=finalized,
                sub_period_signals=sub_period_signals,
                basis_codes=list(dict.fromkeys(basis_codes)),
                counter_signals=list(dict.fromkeys(counter_signals)),
                activation_context=activation_context,
            )
        )

    return signals
