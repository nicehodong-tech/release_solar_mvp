"""Natal chart structure assembly."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from saju_birth_engine.models import BirthChartResult

from .auxiliary import build_auxiliary_profile
from .career_fields import build_career_field_profile
from .constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_METADATA,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    POSITION_DOMAINS,
    STEM_METADATA,
)
from .combinations import build_combination_profile
from .cycle_regulation import build_cycle_regulation_profile
from .directional_interactions import build_directional_interaction_profile
from .element_combinations import build_element_combination_profile
from .elements import build_element_profile
from .features import build_life_feature_profile
from .interactions import find_natal_interactions
from .models import ChartStructure, PositionSignal
from .month_governance import build_month_governance_profile
from .month_hidden_phase import build_month_hidden_phase_profile
from .patterns import build_pattern_profile
from .source_reading_profiles import build_source_reading_profile
from .source_personality_profiles import build_source_personality_profile
from .stem_receptions import build_integrated_saju_profile, build_stem_reception_profile
from .ten_gods import build_ten_god_profile, hidden_ten_gods_for_branch, main_hidden_stem, ten_god_for
from .ten_god_interactions import build_ten_god_interaction_profile


POSITION_TEN_GOD_CONTEXTS: dict[str, dict[str, object]] = {
    "year": {
        "age_scope": "0-19",
        "life_stage": "early_environment",
        "primary_context": "origin_family_background",
        "stem_visibility_weight": 0.85,
        "branch_reality_weight": 1.05,
        "hidden_reality_weight": 0.85,
    },
    "month": {
        "age_scope": "20-39",
        "life_stage": "youth_social_entry",
        "primary_context": "career_social_role_family_duty",
        "stem_visibility_weight": 1.15,
        "branch_reality_weight": 1.45,
        "hidden_reality_weight": 1.25,
    },
    "day": {
        "age_scope": "40-58",
        "life_stage": "private_life_and_household",
        "primary_context": "self_spouse_home_private_choice",
        "stem_visibility_weight": 1.1,
        "branch_reality_weight": 1.3,
        "hidden_reality_weight": 1.1,
    },
    "hour": {
        "age_scope": "59+",
        "life_stage": "later_result_and_output",
        "primary_context": "children_output_future_late_life",
        "stem_visibility_weight": 0.9,
        "branch_reality_weight": 1.05,
        "hidden_reality_weight": 0.95,
    },
}


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult):
    pillars = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar
    return pillars


def _position_signals(chart: BirthChartResult) -> dict[str, PositionSignal]:
    pillars = _pillars(chart)
    visible_stems = {pillar.stem_key for pillar in pillars.values()}
    day_stem_key = chart.day_pillar.stem_key
    day_element = STEM_METADATA[day_stem_key]["element"]
    resource_element = next(element for element, child in ELEMENT_GENERATES.items() if child == day_element)
    officer_element = next(element for element, target in ELEMENT_CONTROLS.items() if target == day_element)

    signals: dict[str, PositionSignal] = {}
    for position, pillar in pillars.items():
        position_context = POSITION_TEN_GOD_CONTEXTS[position]
        hidden_stems = BRANCH_HIDDEN_STEMS[pillar.branch_key]
        hidden_stem_keys = [stem_key for stem_key, _ in hidden_stems]
        branch_main_stem = main_hidden_stem(pillar.branch_key)
        hidden_elements = [STEM_METADATA[stem_key]["element"] for stem_key in hidden_stem_keys]
        signals[position] = PositionSignal(
            position=position,
            pillar=pillar.label,
            stem_key=pillar.stem_key,
            branch_key=pillar.branch_key,
            stem_element=STEM_METADATA[pillar.stem_key]["element"],
            branch_element=BRANCH_METADATA[pillar.branch_key]["element"],
            stem_ten_god="self" if position == "day" else ten_god_for(day_stem_key, pillar.stem_key),
            branch_main_ten_god=ten_god_for(day_stem_key, branch_main_stem),
            hidden_ten_gods=hidden_ten_gods_for_branch(day_stem_key, pillar.branch_key),
            domains=POSITION_DOMAINS[position],
            protruded_hidden_stems=[stem_key for stem_key in hidden_stem_keys if stem_key in visible_stems],
            supports_day_master=day_element in hidden_elements or resource_element in hidden_elements,
            controls_day_master=officer_element in hidden_elements,
            age_scope=str(position_context["age_scope"]),
            life_stage=str(position_context["life_stage"]),
            primary_context=str(position_context["primary_context"]),
            stem_visibility_weight=float(position_context["stem_visibility_weight"]),
            branch_reality_weight=float(position_context["branch_reality_weight"]),
            hidden_reality_weight=float(position_context["hidden_reality_weight"]),
            position_basis_codes=[
                f"position_context_{position}",
                f"position_age_scope_{position_context['age_scope']}",
                "branch_reality_stronger_than_stem",
                f"position_primary_context_{position_context['primary_context']}",
            ],
        )
    return signals


def build_chart_structure(chart: BirthChartResult) -> ChartStructure:
    element_profile = build_element_profile(chart)
    ten_god_profile = build_ten_god_profile(chart)
    interactions = find_natal_interactions(chart)
    auxiliary = build_auxiliary_profile(chart)
    position_signals = _position_signals(chart)
    combination_profile = build_combination_profile(chart, position_signals)
    element_combination_profile = build_element_combination_profile(chart)
    directional_interaction_profile = build_directional_interaction_profile(chart)
    ten_god_interaction_profile = build_ten_god_interaction_profile(chart, position_signals)
    stem_reception_profile = build_stem_reception_profile(chart, interactions)
    integrated_saju_profile = build_integrated_saju_profile(stem_reception_profile)
    pattern_profile = build_pattern_profile(element_profile, ten_god_profile, position_signals)
    month_hidden_phase_profile = build_month_hidden_phase_profile(chart)
    month_governance_profile = build_month_governance_profile(
        day_master_stem=chart.day_pillar.stem_key,
        element_profile=element_profile,
        ten_god_profile=ten_god_profile,
        pattern_profile=pattern_profile,
        position_signals=position_signals,
        month_hidden_phase=month_hidden_phase_profile,
    )
    cycle_regulation_profile = build_cycle_regulation_profile(
        SimpleNamespace(
            day_master_element=element_profile.day_master_element,
            element_profile=element_profile,
            ten_god_profile=ten_god_profile,
            position_signals=position_signals,
            branch_interactions=interactions,
            pattern_profile=pattern_profile,
            month_governance_profile=month_governance_profile,
        )
    )
    life_feature_profile = build_life_feature_profile(
        element_profile,
        ten_god_profile,
        position_signals,
        interactions,
        auxiliary,
        pattern_profile,
        stem_reception_profile,
        integrated_saju_profile,
        cycle_regulation_profile,
        month_governance_profile,
    )
    source_personality_profile = build_source_personality_profile(
        day_stem_key=chart.day_pillar.stem_key,
        day_branch_key=chart.day_pillar.branch_key,
        month_branch_key=chart.month_pillar.branch_key,
    )
    source_reading_profile = build_source_reading_profile(
        day_stem_key=chart.day_pillar.stem_key,
        day_branch_key=chart.day_pillar.branch_key,
        month_branch_key=chart.month_pillar.branch_key,
    )
    career_field_profile = build_career_field_profile(
        day_master_stem=chart.day_pillar.stem_key,
        element_profile=element_profile,
        ten_god_profile=ten_god_profile,
        position_signals=position_signals,
        branch_interactions=interactions,
        life_feature_profile=life_feature_profile,
        element_combination_profile=element_combination_profile,
        ten_god_interaction_profile=ten_god_interaction_profile,
        stem_reception_profile=stem_reception_profile,
        integrated_saju_profile=integrated_saju_profile,
    )
    chart_types = pattern_profile.candidates

    tags: list[str] = [
        f"strength_{element_profile.day_master_strength}",
        f"temperature_{element_profile.temperature_balance}",
        f"moisture_{element_profile.moisture_balance}",
        f"circulation_{element_profile.circulation_level}",
    ]
    tags.extend(f"type_{item.name}" for item in chart_types[:3])
    if month_governance_profile.month_command_ten_god:
        tags.append(f"month_command_{month_governance_profile.month_command_ten_god}")
    if month_governance_profile.regular_pattern:
        tags.append(f"month_regular_pattern_{month_governance_profile.regular_pattern}")
    if month_hidden_phase_profile.active_stem:
        tags.append(f"month_hidden_phase_{month_hidden_phase_profile.active_phase}_{month_hidden_phase_profile.active_stem}")
    if month_hidden_phase_profile.active_ten_god:
        tags.append(f"month_hidden_phase_ten_god_{month_hidden_phase_profile.active_ten_god}")
    tags.extend(f"month_useful_{element}" for element in month_governance_profile.useful_elements[:3])
    tags.extend(f"month_caution_{element}" for element in month_governance_profile.caution_elements[:3])
    for interaction in interactions:
        if interaction.intensity in {"strong", "moderate"}:
            tags.append(f"branch_{interaction.relation_type}")
    for signal in combination_profile.heavenly_stem_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"combo_{signal.relation_type}")
    for signal in combination_profile.ten_god_chain_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"combo_{signal.relation_type}")
    for signal in element_combination_profile.heavenly_stem_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"element_combo_{signal.relation_type}")
    for signal in directional_interaction_profile.heavenly_stem_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"directional_{signal.direction_type}")
    for signal in ten_god_interaction_profile.visible_stem_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"ten_god_interaction_{signal.direction_key.replace('->', '_to_')}")
    for signal in stem_reception_profile.visible_stem_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"stem_reception_{signal.day_stem}_receives_{signal.target_stem}")
    for signal in integrated_saju_profile.visible_pair_signals[:4]:
        if signal.strength in {"high", "moderate"}:
            tags.append(f"integrated_saju_{signal.source_stem}_to_{signal.target_stem}")
    tags.extend(source_personality_profile.basis_codes)
    tags.extend(source_reading_profile.basis_codes[:12])

    warnings: list[str] = []
    if chart.boundary_sensitive:
        warnings.append(f"birth_chart_boundary_sensitive:{chart.boundary_type}")
    if chart.daeun_boundary_sensitive:
        warnings.append("daeun_boundary_sensitive")

    structure = ChartStructure(
        four_pillars={position: pillar.label for position, pillar in _pillars(chart).items()},
        day_master_stem=chart.day_pillar.stem_key,
        day_master_element=element_profile.day_master_element,
        day_master_yin_yang=STEM_METADATA[chart.day_pillar.stem_key]["yin_yang"],
        month_branch=chart.month_pillar.branch_key,
        season_label=element_profile.season_label,
        element_profile=element_profile,
        ten_god_profile=ten_god_profile,
        position_signals=position_signals,
        branch_interactions=interactions,
        auxiliary_profile=auxiliary,
        combination_profile=combination_profile,
        element_combination_profile=element_combination_profile,
        directional_interaction_profile=directional_interaction_profile,
        ten_god_interaction_profile=ten_god_interaction_profile,
        stem_reception_profile=stem_reception_profile,
        integrated_saju_profile=integrated_saju_profile,
        cycle_regulation_profile=cycle_regulation_profile,
        month_governance_profile=month_governance_profile,
        chart_types=chart_types,
        pattern_profile=pattern_profile,
        life_feature_profile=life_feature_profile,
        source_personality_profile=source_personality_profile,
        source_reading_profile=source_reading_profile,
        career_field_profile=career_field_profile,
        structure_tags=list(dict.fromkeys(tags)),
        warnings=warnings,
    )
    return replace(structure, cycle_regulation_profile=build_cycle_regulation_profile(structure))
