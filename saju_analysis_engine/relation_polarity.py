"""Polarity rules for branch combinations and conflicts.

Branch relations are not automatically good or bad. A combine, clash,
punishment, harm, or break is judged by the element it activates and by whether
that element is useful or burdensome for the natal structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import BRANCH_HIDDEN_STEMS, BRANCH_METADATA, STEM_METADATA
from .models import BranchInteraction, ElementProfile, PatternProfile


COMBINE_RELATIONS = {"six_combine", "three_harmony", "three_harmony_half", "three_meeting"}
DISRUPTIVE_RELATIONS = {"clash", "punishment", "harm", "break", "self_punishment"}


@dataclass(frozen=True)
class RelationPolarity:
    polarity: str
    support_elements: tuple[str, ...]
    pressure_elements: tuple[str, ...]
    overuse_elements: tuple[str, ...]
    activated_elements: tuple[str, ...]
    useful_score: int
    pressure_score: int


def _unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in values if item))


def relation_activated_elements(interaction: BranchInteraction) -> tuple[str, ...]:
    elements: list[str] = []
    if interaction.effect_element:
        elements.append(interaction.effect_element)
    for branch in interaction.branches:
        branch_element = BRANCH_METADATA.get(branch, {}).get("element")
        if branch_element:
            elements.append(branch_element)
        for stem_key, weight in BRANCH_HIDDEN_STEMS.get(branch, []):
            if weight < 0.25:
                continue
            element = STEM_METADATA.get(stem_key, {}).get("element")
            if element:
                elements.append(element)
    return _unique(elements)


def _is_dominant_pressure(profile: ElementProfile, element: str) -> bool:
    score = profile.scores.get(element)
    return bool(score and score.state == "dominant")


def _candidate_weight(score: int) -> int:
    if score >= 76:
        return 2
    if score >= 62:
        return 1
    return 0


def _candidate_priority(candidate: object) -> tuple[int, int]:
    role = str(getattr(candidate, "role", ""))
    score = int(getattr(candidate, "score", 0) or 0)
    if role.startswith("regular_pattern_"):
        return (0, -score)
    if role in {"climate_medicine", "illness_medicine"}:
        return (1, -score)
    if "support" in role or "pressure" in role:
        return (2, -score)
    return (3, -score)


def _selected_candidate_weights(
    candidates: list[object],
    *,
    limit: int = 2,
    exclude_elements: set[str] | None = None,
) -> dict[str, int]:
    blocked_elements = exclude_elements or set()
    available = [
        candidate
        for candidate in candidates
        if str(getattr(candidate, "element", "")) and str(getattr(candidate, "element", "")) not in blocked_elements
    ]
    element_order: dict[str, int] = {}
    element_candidates: dict[str, list[object]] = {}
    for index, candidate in enumerate(available):
        element = str(getattr(candidate, "element", ""))
        element_order.setdefault(element, index)
        element_candidates.setdefault(element, []).append(candidate)

    ranked: list[tuple[tuple[int, int, int], str, int]] = []
    for element, grouped in element_candidates.items():
        role_source = sorted(grouped, key=_candidate_priority)[0]
        score = max(int(getattr(candidate, "score", 0) or 0) for candidate in grouped)
        weight = _candidate_weight(score)
        if weight:
            ranked.append(
                (
                    (
                        *_candidate_priority(role_source),
                        element_order.get(element, 999),
                    ),
                    element,
                    weight,
                )
            )
    ranked.sort(key=lambda item: item[0])
    return {element: weight for _, element, weight in ranked[:limit]}


def _pattern_support_weights(pattern_profile: PatternProfile | None) -> tuple[dict[str, int], dict[str, int]]:
    if pattern_profile is None:
        return {}, {}
    support = _selected_candidate_weights(list(pattern_profile.useful_element_candidates), limit=2)
    pressure = _selected_candidate_weights(
        list(pattern_profile.caution_element_candidates),
        limit=2,
    )
    return support, pressure


def branch_relation_polarity(
    profile: ElementProfile,
    interaction: BranchInteraction,
    pattern_profile: PatternProfile | None = None,
) -> RelationPolarity:
    activated = relation_activated_elements(interaction)
    pattern_support, pattern_pressure = _pattern_support_weights(pattern_profile)
    touches_month = "month" in interaction.positions
    support: list[str] = []
    pressure: list[str] = []
    overuse: list[str] = []
    useful_score = 0
    pressure_score = 0

    for element in activated:
        element_supports = False
        element_pressures = False
        if element in profile.useful_elements:
            useful_score += 2
            support.append(element)
            element_supports = True
        if element in profile.climate_needs:
            useful_score += 1
            support.append(element)
            element_supports = True
        if element in pattern_support:
            useful_score += pattern_support[element]
            support.append(element)
            element_supports = True
            if touches_month:
                useful_score += 1
        if touches_month and element in profile.useful_elements:
            useful_score += 1
        if (
            not element_supports
            and element in profile.caution_elements
            and element not in profile.useful_elements
            and element not in pattern_support
        ):
            pressure_score += 2
            pressure.append(element)
            element_pressures = True
        if element in pattern_pressure:
            if element_supports:
                pressure_score += max(1, pattern_pressure[element] - 1)
                overuse.append(element)
                element_pressures = True
                if touches_month:
                    pressure_score += 1
            else:
                pressure_score += pattern_pressure[element]
                pressure.append(element)
                element_pressures = True
                if touches_month:
                    pressure_score += 1
        elif not element_supports and _is_dominant_pressure(profile, element) and element not in profile.useful_elements:
            pressure_score += 1
            pressure.append(element)
            element_pressures = True
        if touches_month and element_pressures and element in profile.caution_elements:
            pressure_score += 1

    if useful_score > pressure_score:
        polarity = "supportive"
    elif pressure_score > useful_score:
        polarity = "burdensome"
    elif useful_score and pressure_score:
        polarity = "mixed"
    else:
        polarity = "neutral"

    return RelationPolarity(
        polarity=polarity,
        support_elements=_unique(support),
        pressure_elements=_unique(pressure),
        overuse_elements=_unique(overuse),
        activated_elements=activated,
        useful_score=useful_score,
        pressure_score=pressure_score,
    )
