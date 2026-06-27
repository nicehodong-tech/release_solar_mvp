"""Element balance, season, climate, and day-master strength rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_METADATA,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    ELEMENTS,
    MONTH_SEASON_MODIFIERS,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
)
from .models import ElementProfile, ElementScore


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


def _clip(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def _state_from_ratio(ratio: float) -> str:
    if ratio >= 0.32:
        return "dominant"
    if ratio >= 0.23:
        return "strong"
    if ratio >= 0.13:
        return "balanced"
    if ratio > 0.035:
        return "weak"
    return "absent"


def _exposure(visible_count: int, root_count: int) -> str:
    if visible_count >= 2:
        return "clear"
    if visible_count == 1:
        return "present"
    if root_count >= 1:
        return "hidden"
    return "absent"


def _strength_label(score: int) -> str:
    if score >= 75:
        return "very_strong"
    if score >= 62:
        return "strong"
    if score >= 45:
        return "balanced"
    if score >= 32:
        return "weak"
    return "very_weak"


def _temperature_balance(month_branch: str, seasonal_scores: dict[str, float]) -> tuple[str, list[str]]:
    month_bonus = {
        "sa": 2.1,
        "o": 2.4,
        "mi": 1.0,
        "in": 0.25,
        "myo": 0.2,
        "jin": -0.1,
        "sin": -0.2,
        "yu": -0.3,
        "sul": 0.25,
        "hae": -2.0,
        "ja": -2.35,
        "chuk": -1.35,
    }[month_branch]
    value = seasonal_scores["fire"] - seasonal_scores["water"] + month_bonus
    if value >= 1.6:
        return "hot", ["water", "metal"]
    if value <= -1.6:
        return "cold", ["fire", "wood"]
    return "balanced", []


def _moisture_balance(month_branch: str, seasonal_scores: dict[str, float]) -> tuple[str, list[str]]:
    wet_branch_bonus = {"hae": 1.5, "ja": 1.7, "chuk": 1.0, "jin": 0.6}.get(month_branch, 0.0)
    dry_branch_bonus = {"sa": 1.0, "o": 1.3, "mi": 1.2, "sul": 1.0, "yu": 0.4}.get(month_branch, 0.0)
    value = seasonal_scores["water"] + wet_branch_bonus - seasonal_scores["fire"] - dry_branch_bonus
    if value >= 1.5:
        return "wet", ["fire", "earth"]
    if value <= -1.5:
        return "dry", ["water", "metal"]
    return "balanced", []


def build_element_profile(chart: BirthChartResult) -> ElementProfile:
    pillars = _pillars(chart)
    day_element = STEM_METADATA[chart.day_pillar.stem_key]["element"]
    month_branch = chart.month_pillar.branch_key

    raw_scores: dict[str, float] = {element: 0.0 for element in ELEMENTS}
    visible_counts: dict[str, int] = {element: 0 for element in ELEMENTS}
    root_counts: dict[str, int] = {element: 0 for element in ELEMENTS}

    for position, pillar in pillars.items():
        stem_element = STEM_METADATA[pillar.stem_key]["element"]
        raw_scores[stem_element] += POSITION_STEM_WEIGHTS[position]
        visible_counts[stem_element] += 1

        for hidden_stem_key, hidden_weight in BRANCH_HIDDEN_STEMS[pillar.branch_key]:
            hidden_element = STEM_METADATA[hidden_stem_key]["element"]
            raw_scores[hidden_element] += POSITION_BRANCH_WEIGHTS[position] * hidden_weight
            if hidden_weight >= 0.15:
                root_counts[hidden_element] += 1

    modifiers = MONTH_SEASON_MODIFIERS[month_branch]
    seasonal_scores = {
        element: raw_scores[element] * modifiers[element]
        for element in ELEMENTS
    }
    total = sum(seasonal_scores.values()) or 1.0

    scores = {
        element: ElementScore(
            element=element,
            raw_score=round(raw_scores[element], 3),
            seasonal_score=round(seasonal_scores[element], 3),
            ratio=round(seasonal_scores[element] / total, 3),
            visible_count=visible_counts[element],
            root_count=root_counts[element],
            exposure=_exposure(visible_counts[element], root_counts[element]),
            state=_state_from_ratio(seasonal_scores[element] / total),
        )
        for element in ELEMENTS
    }

    resource_element = ELEMENT_GENERATED_BY[day_element]
    output_element = ELEMENT_GENERATES[day_element]
    wealth_element = ELEMENT_CONTROLS[day_element]
    officer_element = ELEMENT_CONTROLLED_BY[day_element]

    supportive = seasonal_scores[day_element] + seasonal_scores[resource_element] * 0.75
    consuming = (
        seasonal_scores[output_element] * 0.55
        + seasonal_scores[wealth_element] * 0.72
        + seasonal_scores[officer_element] * 0.85
    )
    strength_score = _clip(50 + 45 * ((supportive - consuming) / total))
    strength_label = _strength_label(strength_score)

    if strength_label in {"weak", "very_weak"}:
        useful_elements = [resource_element, day_element]
        caution_elements = [officer_element, wealth_element]
    elif strength_label in {"strong", "very_strong"}:
        useful_elements = [output_element, wealth_element, officer_element]
        caution_elements = [day_element, resource_element]
    else:
        useful_elements = [output_element, wealth_element]
        caution_elements = []

    temperature_balance, temperature_needs = _temperature_balance(month_branch, seasonal_scores)
    moisture_balance, moisture_needs = _moisture_balance(month_branch, seasonal_scores)
    climate_needs = list(dict.fromkeys(temperature_needs + moisture_needs))

    present_elements = [element for element in ELEMENTS if scores[element].state != "absent"]
    dominant_elements = [element for element in ELEMENTS if scores[element].state == "dominant"]
    if len(present_elements) >= 5 and not dominant_elements:
        circulation_level = "smooth"
    elif len(present_elements) >= 4:
        circulation_level = "usable"
    elif len(present_elements) >= 3:
        circulation_level = "partial"
    else:
        circulation_level = "blocked"

    circulation_notes: list[str] = []
    if scores[output_element].state in {"balanced", "strong", "dominant"} and scores[wealth_element].state != "absent":
        circulation_notes.append("output_to_wealth_available")
    if scores[resource_element].state in {"balanced", "strong", "dominant"}:
        circulation_notes.append("resource_support_available")
    if scores[officer_element].state == "dominant" and strength_label in {"weak", "very_weak"}:
        circulation_notes.append("officer_pressure_on_weak_day_master")

    illness_medicine: list[dict[str, Any]] = []
    for element, score in scores.items():
        if score.state == "dominant":
            medicine = [ELEMENT_CONTROLS[element], ELEMENT_GENERATES[element]]
            illness_medicine.append(
                {"illness": f"{element}_excess", "medicine": medicine, "basis": "element_dominance"}
            )
        if score.state == "absent":
            illness_medicine.append(
                {"illness": f"{element}_absence", "medicine": [element], "basis": "element_absence"}
            )
    if temperature_balance != "balanced":
        illness_medicine.append(
            {
                "illness": f"{temperature_balance}_temperature_bias",
                "medicine": temperature_needs,
                "basis": "johu_temperature",
            }
        )
    if moisture_balance != "balanced":
        illness_medicine.append(
            {
                "illness": f"{moisture_balance}_moisture_bias",
                "medicine": moisture_needs,
                "basis": "johu_moisture",
            }
        )

    return ElementProfile(
        day_master_element=day_element,
        month_branch=month_branch,
        season_label=BRANCH_METADATA[month_branch]["season"],
        scores=scores,
        day_master_strength_score=strength_score,
        day_master_strength=strength_label,
        useful_elements=useful_elements,
        caution_elements=caution_elements,
        temperature_balance=temperature_balance,
        moisture_balance=moisture_balance,
        climate_needs=climate_needs,
        circulation_level=circulation_level,
        circulation_notes=circulation_notes,
        illness_medicine=illness_medicine,
    )
