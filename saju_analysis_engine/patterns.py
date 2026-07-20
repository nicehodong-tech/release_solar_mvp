"""Pattern and useful-element candidate rules."""

from __future__ import annotations

from .constants import (
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    ELEMENTS,
)
from .models import ChartType, ElementProfile, PatternProfile, TenGodProfile, UsefulElementCandidate


REGULAR_PATTERN_BY_TEN_GOD = {
    "bi_gyeon": "jianlu_peer_pattern",
    "geob_jae": "yangren_peer_pattern",
    "sik_sin": "eating_god_pattern",
    "sang_gwan": "hurting_officer_pattern",
    "pyeon_jae": "indirect_wealth_pattern",
    "jeong_jae": "direct_wealth_pattern",
    "pyeon_gwan": "seven_killings_pattern",
    "jeong_gwan": "direct_officer_pattern",
    "pyeon_in": "indirect_resource_pattern",
    "jeong_in": "direct_resource_pattern",
}

TEN_GOD_GROUP_BY_MONTH_COMMAND = {
    "bi_gyeon": "peer",
    "geob_jae": "peer",
    "sik_sin": "output",
    "sang_gwan": "output",
    "pyeon_jae": "wealth",
    "jeong_jae": "wealth",
    "pyeon_gwan": "officer",
    "jeong_gwan": "officer",
    "pyeon_in": "resource",
    "jeong_in": "resource",
}

# Regular pattern rules add the month-command's own demand to the more general
# strength, climate, and illness-medicine candidates. A group can be useful and
# cautionary at the same time in different layers; downstream polarity keeps both
# signals instead of flattening the judgment.
REGULAR_PATTERN_NEED_RULES = {
    "bi_gyeon": {
        "support": (("officer", 78, "peer_pattern_needs_officer"), ("output", 68, "peer_pattern_uses_output")),
        "caution": (("peer", 76, "peer_pattern_excess_peer"), ("resource", 62, "peer_pattern_resource_overfeeds")),
    },
    "geob_jae": {
        "support": (("officer", 82, "yangren_needs_officer_control"), ("output", 70, "yangren_uses_output_release")),
        "caution": (("peer", 80, "yangren_excess_competition"), ("resource", 66, "yangren_resource_overfeeds")),
    },
    "sik_sin": {
        "support": (("wealth", 80, "eating_god_generates_wealth"), ("officer", 64, "eating_god_results_enter_responsibility")),
        "caution": (("resource", 78, "resource_can_damage_eating_god"),),
    },
    "sang_gwan": {
        "support": (("wealth", 78, "hurting_officer_generates_wealth"), ("resource", 74, "hurting_officer_needs_resource_refinement")),
        "caution": (("officer", 78, "hurting_officer_clashes_with_officer"),),
    },
    "pyeon_jae": {
        "support": (("officer", 76, "indirect_wealth_supports_officer"), ("output", 70, "output_sources_indirect_wealth")),
        "caution": (("peer", 78, "peer_competes_for_indirect_wealth"), ("resource", 62, "resource_slows_wealth_movement")),
    },
    "jeong_jae": {
        "support": (("officer", 78, "direct_wealth_supports_officer"), ("output", 70, "output_sources_direct_wealth")),
        "caution": (("peer", 78, "peer_competes_for_direct_wealth"), ("resource", 62, "resource_slows_wealth_accumulation")),
    },
    "pyeon_gwan": {
        "support": (("output", 82, "eating_god_controls_seven_killings"), ("resource", 78, "seven_killings_transforms_to_resource")),
        "caution": (("wealth", 78, "wealth_feeds_seven_killings"), ("officer", 66, "killing_pressure_excess")),
    },
    "jeong_gwan": {
        "support": (("resource", 82, "officer_resource_sequence"), ("wealth", 68, "wealth_supports_officer")),
        "caution": (("output", 80, "output_harms_officer_order"), ("peer", 60, "peer_disrupts_officer_order")),
    },
    "pyeon_in": {
        "support": (("wealth", 76, "wealth_regulates_indirect_resource"), ("output", 70, "resource_turns_into_output")),
        "caution": (("resource", 78, "indirect_resource_excess"), ("peer", 64, "resource_overprotects_day_master")),
    },
    "jeong_in": {
        "support": (("wealth", 74, "wealth_regulates_direct_resource"), ("output", 70, "resource_turns_into_visible_result")),
        "caution": (("resource", 76, "direct_resource_excess"), ("peer", 62, "resource_overprotects_day_master")),
    },
}


def _confidence(score: int) -> str:
    if score >= 82:
        return "high"
    if score >= 70:
        return "medium_high"
    if score >= 55:
        return "medium"
    if score >= 42:
        return "low"
    return "restricted"


def build_chart_type_candidates(
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, object] | None = None,
) -> list[ChartType]:
    group_scores = ten_god_profile.group_scores
    types: list[ChartType] = []
    month_signal = position_signals.get("month") if position_signals else None
    month_command_ten_god = getattr(month_signal, "branch_main_ten_god", "")
    protruded_hidden_stems = getattr(month_signal, "protruded_hidden_stems", [])

    if month_command_ten_god in REGULAR_PATTERN_BY_TEN_GOD:
        group = {
            "bi_gyeon": "peer",
            "geob_jae": "peer",
            "sik_sin": "output",
            "sang_gwan": "output",
            "pyeon_jae": "wealth",
            "jeong_jae": "wealth",
            "pyeon_gwan": "officer",
            "jeong_gwan": "officer",
            "pyeon_in": "resource",
            "jeong_in": "resource",
        }[month_command_ten_god]
        score = 58 + round(group_scores.get(group, 0.0) * 8)
        basis_codes = [f"month_command_{month_command_ten_god}", f"{group}_group_score"]
        if protruded_hidden_stems:
            score += 10
            basis_codes.append("month_hidden_stem_protruded")
        if month_command_ten_god in ten_god_profile.dominant_ten_gods:
            score += 7
            basis_codes.append("month_command_is_dominant_ten_god")
        types.append(
            ChartType(
                REGULAR_PATTERN_BY_TEN_GOD[month_command_ten_god],
                "regular_pattern_candidate",
                min(96, score),
                _confidence(min(96, score)),
                basis_codes,
            )
        )

    output_score = group_scores.get("output", 0.0)
    wealth_score = group_scores.get("wealth", 0.0)
    officer_score = group_scores.get("officer", 0.0)
    resource_score = group_scores.get("resource", 0.0)
    peer_score = group_scores.get("peer", 0.0)
    strength = element_profile.day_master_strength

    if output_score >= 1.2 and wealth_score >= 1.1:
        score = min(95, round(55 + output_score * 9 + wealth_score * 9))
        types.append(ChartType("output_to_wealth", "primary_candidate", score, _confidence(score), ["output_group", "wealth_group"]))
    if officer_score >= 1.2 and resource_score >= 1.0:
        score = min(92, round(55 + officer_score * 10 + resource_score * 8))
        types.append(ChartType("officer_resource", "primary_candidate", score, _confidence(score), ["officer_group", "resource_group"]))
    if resource_score >= 1.25 and strength in {"weak", "very_weak", "balanced"}:
        score = min(90, round(58 + resource_score * 12))
        types.append(ChartType("resource_supported", "secondary_candidate", score, _confidence(score), ["resource_group", f"strength_{strength}"]))
    if wealth_score >= 1.25 and strength in {"weak", "very_weak"}:
        score = min(90, round(60 + wealth_score * 10))
        types.append(ChartType("wealth_pressure", "risk_candidate", score, _confidence(score), ["wealth_group", f"strength_{strength}"]))
    if peer_score >= 1.4 and wealth_score >= 1.0:
        score = min(88, round(55 + peer_score * 9 + wealth_score * 6))
        types.append(ChartType("peer_wealth_competition", "risk_candidate", score, _confidence(score), ["peer_group", "wealth_group"]))
    if element_profile.temperature_balance == "cold":
        score = 72 if "fire" in element_profile.climate_needs else 65
        types.append(ChartType("cold_storage_needs_fire", "condition_candidate", score, _confidence(score), ["cold_temperature_bias"]))
    if element_profile.temperature_balance == "hot":
        score = 72 if "water" in element_profile.climate_needs else 65
        types.append(ChartType("hot_dry_needs_water", "condition_candidate", score, _confidence(score), ["hot_temperature_bias"]))

    dominant = [element for element, score in element_profile.scores.items() if score.state == "dominant"]
    absent = [element for element, score in element_profile.scores.items() if score.state == "absent"]
    if len(dominant) == 1 and len(absent) >= 2:
        score = 68 + len(absent) * 3
        types.append(
            ChartType(
                f"skewed_{dominant[0]}_structure",
                "special_pattern_watch",
                min(82, score),
                _confidence(min(82, score)),
                [f"dominant_{dominant[0]}", "multiple_absent_elements"],
            )
        )

    if element_profile.day_master_strength == "very_weak":
        strongest_group = max(group_scores.items(), key=lambda item: item[1], default=("none", 0.0))
        if strongest_group[1] >= 2.2 and group_scores.get("peer", 0.0) + group_scores.get("resource", 0.0) <= 1.3:
            score = min(86, round(60 + strongest_group[1] * 8))
            types.append(
                ChartType(
                    f"follow_{strongest_group[0]}_watch",
                    "special_pattern_watch",
                    score,
                    _confidence(score),
                    ["very_weak_day_master", f"dominant_{strongest_group[0]}_group", "weak_support_base"],
                )
            )

    if element_profile.day_master_strength == "very_strong":
        if group_scores.get("peer", 0.0) + group_scores.get("resource", 0.0) >= 3.2:
            score = min(84, round(58 + (group_scores.get("peer", 0.0) + group_scores.get("resource", 0.0)) * 6))
            types.append(
                ChartType(
                    "dominant_day_master_special_watch",
                    "special_pattern_watch",
                    score,
                    _confidence(score),
                    ["very_strong_day_master", "peer_resource_excess"],
                )
            )

    types.sort(key=lambda item: item.score, reverse=True)
    return types[:6]


def _candidate(element: str, role: str, score: int, basis_codes: list[str]) -> UsefulElementCandidate:
    return UsefulElementCandidate(
        element=element,
        role=role,
        score=max(0, min(100, score)),
        confidence=_confidence(score),
        basis_codes=basis_codes,
    )


def _element_for_ten_god_group(day_element: str, group: str) -> str:
    if group == "peer":
        return day_element
    if group == "resource":
        return ELEMENT_GENERATED_BY[day_element]
    if group == "output":
        return ELEMENT_GENERATES[day_element]
    if group == "wealth":
        return ELEMENT_CONTROLS[day_element]
    if group == "officer":
        return ELEMENT_CONTROLLED_BY[day_element]
    raise ValueError(f"Unknown ten-god group: {group}")


def _regular_pattern_candidates(
    element_profile: ElementProfile,
    month_command_ten_god: str,
) -> tuple[list[UsefulElementCandidate], list[UsefulElementCandidate]]:
    rules = REGULAR_PATTERN_NEED_RULES.get(month_command_ten_god)
    if not rules:
        return [], []
    pattern_name = REGULAR_PATTERN_BY_TEN_GOD.get(month_command_ten_god, "regular_pattern")
    useful: list[UsefulElementCandidate] = []
    caution: list[UsefulElementCandidate] = []
    for group, score, reason in rules["support"]:
        element = _element_for_ten_god_group(element_profile.day_master_element, group)
        useful.append(
            _candidate(
                element,
                f"regular_pattern_support_{group}",
                score,
                [f"month_command_{month_command_ten_god}", f"regular_pattern_{pattern_name}", reason],
            )
        )
    for group, score, reason in rules["caution"]:
        element = _element_for_ten_god_group(element_profile.day_master_element, group)
        caution.append(
            _candidate(
                element,
                f"regular_pattern_pressure_{group}",
                score,
                [f"month_command_{month_command_ten_god}", f"regular_pattern_{pattern_name}", reason],
            )
        )
    return useful, caution


def build_useful_element_candidates(
    element_profile: ElementProfile,
    month_command_ten_god: str = "",
) -> tuple[list[UsefulElementCandidate], list[UsefulElementCandidate]]:
    day_element = element_profile.day_master_element
    resource_element = ELEMENT_GENERATED_BY[day_element]
    output_element = ELEMENT_GENERATES[day_element]
    wealth_element = ELEMENT_CONTROLS[day_element]
    officer_element = ELEMENT_CONTROLLED_BY[day_element]

    useful: list[UsefulElementCandidate] = []
    caution: list[UsefulElementCandidate] = []

    for element in element_profile.climate_needs:
        useful.append(_candidate(element, "climate_medicine", 78, [f"johu_needs_{element}"]))

    pattern_useful, pattern_caution = _regular_pattern_candidates(element_profile, month_command_ten_god)
    useful.extend(pattern_useful)
    caution.extend(pattern_caution)

    strength = element_profile.day_master_strength
    if strength in {"weak", "very_weak"}:
        useful.append(_candidate(resource_element, "support_day_master", 74, ["weak_day_master", "resource_support"]))
        useful.append(_candidate(day_element, "root_day_master", 66, ["weak_day_master", "same_element_root"]))
        caution.append(_candidate(officer_element, "pressure_on_weak_day_master", 72, ["officer_controls_weak_day_master"]))
        caution.append(_candidate(wealth_element, "resource_drain_or_money_pressure", 65, ["wealth_drains_weak_day_master"]))
    elif strength in {"strong", "very_strong"}:
        useful.append(_candidate(output_element, "drain_strong_day_master", 74, ["strong_day_master", "output_use"]))
        useful.append(_candidate(wealth_element, "convert_output_to_value", 70, ["strong_day_master", "wealth_use"]))
        useful.append(_candidate(officer_element, "discipline_strong_day_master", 62, ["strong_day_master", "officer_use"]))
        caution.append(_candidate(day_element, "excess_self_reinforcement", 70, ["strong_day_master", "peer_excess"]))
        caution.append(_candidate(resource_element, "overprotection_or_delay", 62, ["strong_day_master", "resource_excess"]))
    else:
        useful.append(_candidate(output_element, "make_results_visible", 66, ["balanced_day_master", "output_use"]))
        useful.append(_candidate(wealth_element, "connect_results_to_value", 64, ["balanced_day_master", "wealth_use"]))

    for item in element_profile.illness_medicine:
        for medicine in item.get("medicine", []):
            score = 68 if item.get("basis") == "element_dominance" else 62
            useful.append(_candidate(medicine, "illness_medicine", score, [item["basis"], item["illness"]]))

    useful.sort(key=lambda item: item.score, reverse=True)
    caution.sort(key=lambda item: item.score, reverse=True)

    dedup_useful = []
    seen_useful = set()
    for item in useful:
        key = (item.element, item.role)
        if key not in seen_useful and item.element in ELEMENTS:
            seen_useful.add(key)
            dedup_useful.append(item)

    dedup_caution = []
    seen_caution = set()
    for item in caution:
        key = (item.element, item.role)
        if key not in seen_caution and item.element in ELEMENTS:
            seen_caution.add(key)
            dedup_caution.append(item)

    return dedup_useful[:6], dedup_caution[:4]


def build_pattern_profile(
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, object] | None = None,
) -> PatternProfile:
    candidates = build_chart_type_candidates(element_profile, ten_god_profile, position_signals)
    month_signal = position_signals.get("month") if position_signals else None
    month_command_ten_god = getattr(month_signal, "branch_main_ten_god", "")
    useful, caution = build_useful_element_candidates(element_profile, month_command_ten_god)
    regular_pattern = REGULAR_PATTERN_BY_TEN_GOD.get(month_command_ten_god, "")

    regular_candidate = next(
        (item for item in candidates if item.role == "regular_pattern_candidate"),
        None,
    )
    functional_candidate = next(
        (item for item in candidates if item.role != "special_pattern_watch"),
        None,
    )
    lead_candidate = regular_candidate or functional_candidate
    if lead_candidate is not None:
        primary = lead_candidate.name
        confidence = lead_candidate.confidence
    else:
        primary = "mixed_balanced_structure"
        confidence = "medium"

    if regular_candidate is not None:
        pattern_family = "regular"
    elif functional_candidate is not None:
        pattern_family = "functional"
    else:
        pattern_family = "mixed"

    special_pattern_flags = [
        item.name for item in candidates if item.role == "special_pattern_watch"
    ]

    notes: list[str] = []
    if month_command_ten_god:
        notes.append(f"month_command:{month_command_ten_god}")
    if regular_pattern:
        notes.append(f"regular_pattern_candidate:{regular_pattern}")
    if element_profile.temperature_balance != "balanced":
        notes.append(f"johu_priority:{element_profile.temperature_balance}")
    if element_profile.moisture_balance != "balanced":
        notes.append(f"moisture_priority:{element_profile.moisture_balance}")
    if ten_god_profile.important_pairs:
        notes.extend(f"pair:{item}" for item in ten_god_profile.important_pairs)
    if special_pattern_flags:
        notes.append("special_pattern_watch_requires_separate_confirmation")
    if lead_candidate is None:
        notes.append("no_single_pattern_dominates")

    return PatternProfile(
        primary_pattern=primary,
        pattern_confidence=confidence,
        candidates=candidates,
        useful_element_candidates=useful,
        caution_element_candidates=caution,
        decision_notes=notes,
        month_command_ten_god=month_command_ten_god,
        regular_pattern=regular_pattern,
        pattern_family=pattern_family,
        special_pattern_flags=special_pattern_flags,
    )
