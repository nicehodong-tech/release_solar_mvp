"""Ten-god calculation helpers using stable internal keys."""

from __future__ import annotations

from collections import defaultdict

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .models import TenGodProfile


def ten_god_for(day_stem_key: str, target_stem_key: str) -> str:
    day = STEM_METADATA[day_stem_key]
    target = STEM_METADATA[target_stem_key]
    day_element = day["element"]
    target_element = target["element"]
    same_polarity = day["yin_yang"] == target["yin_yang"]

    if day_element == target_element:
        return "bi_gyeon" if same_polarity else "geob_jae"
    if ELEMENT_GENERATES[day_element] == target_element:
        return "sik_sin" if same_polarity else "sang_gwan"
    if ELEMENT_CONTROLS[day_element] == target_element:
        return "pyeon_jae" if same_polarity else "jeong_jae"
    if ELEMENT_CONTROLS[target_element] == day_element:
        return "pyeon_gwan" if same_polarity else "jeong_gwan"
    if ELEMENT_GENERATES[target_element] == day_element:
        return "pyeon_in" if same_polarity else "jeong_in"
    raise ValueError(f"Unresolvable ten-god relation: {day_stem_key} -> {target_stem_key}")


def main_hidden_stem(branch_key: str) -> str:
    return BRANCH_HIDDEN_STEMS[branch_key][0][0]


def hidden_ten_gods_for_branch(day_stem_key: str, branch_key: str) -> list[str]:
    return [ten_god_for(day_stem_key, stem_key) for stem_key, _ in BRANCH_HIDDEN_STEMS[branch_key]]


def _pillars(chart: BirthChartResult):
    return {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
        "hour": chart.hour_pillar,
    }


def build_ten_god_profile(chart: BirthChartResult) -> TenGodProfile:
    day_stem_key = chart.day_pillar.stem_key
    visible_counts: dict[str, float] = defaultdict(float)
    hidden_counts: dict[str, float] = defaultdict(float)

    for position, pillar in _pillars(chart).items():
        if position != "day":
            visible_counts[ten_god_for(day_stem_key, pillar.stem_key)] += POSITION_STEM_WEIGHTS[position]

        for hidden_stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]:
            ten_god = ten_god_for(day_stem_key, hidden_stem_key)
            hidden_counts[ten_god] += POSITION_BRANCH_WEIGHTS[position] * hidden_weight

    group_scores: dict[str, float] = defaultdict(float)
    for ten_god, score in visible_counts.items():
        group_scores[TEN_GOD_GROUPS[ten_god]] += score
    for ten_god, score in hidden_counts.items():
        group_scores[TEN_GOD_GROUPS[ten_god]] += score * 0.8

    all_counts = defaultdict(float)
    for key, value in visible_counts.items():
        all_counts[key] += value
    for key, value in hidden_counts.items():
        all_counts[key] += value * 0.7
    dominant_ten_gods = [
        key
        for key, _ in sorted(all_counts.items(), key=lambda item: item[1], reverse=True)[:4]
        if all_counts[key] >= 0.75
    ]

    important_pairs: list[str] = []
    if group_scores["output"] >= 1.2 and group_scores["wealth"] >= 1.2:
        important_pairs.append("output_to_wealth")
    if group_scores["officer"] >= 1.2 and group_scores["resource"] >= 1.0:
        important_pairs.append("officer_resource")
    if group_scores["peer"] >= 1.4 and group_scores["wealth"] >= 1.1:
        important_pairs.append("peer_wealth_competition")
    if visible_counts["sang_gwan"] + hidden_counts["sang_gwan"] >= 0.8 and group_scores["officer"] >= 1.0:
        important_pairs.append("hurting_officer_meets_officer")

    return TenGodProfile(
        visible_counts={key: round(value, 3) for key, value in sorted(visible_counts.items())},
        hidden_counts={key: round(value, 3) for key, value in sorted(hidden_counts.items())},
        group_scores={key: round(value, 3) for key, value in sorted(group_scores.items())},
        dominant_ten_gods=dominant_ten_gods,
        important_pairs=important_pairs,
    )
