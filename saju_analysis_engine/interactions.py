"""Branch relationship rules: combinations, clashes, penalties, harms, breaks."""

from __future__ import annotations

from itertools import combinations

from saju_birth_engine.models import BirthChartResult

from .constants import BRANCH_METADATA, ELEMENT_CONTROLS, ELEMENT_GENERATES, POSITION_DOMAINS
from .element_combinations import element_pair_rule
from .models import BranchInteraction, BranchPairCombination


def _pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


SIX_COMBINE = {
    _pair("ja", "chuk"): "earth",
    _pair("in", "hae"): "wood",
    _pair("myo", "sul"): "fire",
    _pair("jin", "yu"): "metal",
    _pair("sa", "sin"): "water",
    # 午未 is treated as earth-centered in the imported branch-relation
    # source material; some schools emphasize fire, but earth is safer as the
    # default engine value.
    _pair("o", "mi"): "earth",
}

CLASH = {
    _pair("ja", "o"): None,
    _pair("chuk", "mi"): None,
    _pair("in", "sin"): None,
    _pair("myo", "yu"): None,
    _pair("jin", "sul"): None,
    _pair("sa", "hae"): None,
}

HARM = {
    _pair("ja", "mi"): None,
    _pair("chuk", "o"): None,
    _pair("in", "sa"): None,
    _pair("myo", "jin"): None,
    _pair("sin", "hae"): None,
    _pair("yu", "sul"): None,
}

BREAK = {
    _pair("ja", "yu"): None,
    _pair("chuk", "jin"): None,
    _pair("in", "hae"): None,
    _pair("myo", "o"): None,
    _pair("sa", "sin"): None,
    _pair("mi", "sul"): None,
}

PUNISHMENT = {
    _pair("ja", "myo"): None,
    _pair("chuk", "sul"): None,
    _pair("chuk", "mi"): None,
    _pair("mi", "sul"): None,
    _pair("in", "sa"): None,
    _pair("sa", "sin"): None,
    _pair("in", "sin"): None,
}

SELF_PUNISHMENT_BRANCHES = {"jin", "o", "yu", "hae"}

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

THREE_HARMONY = [
    ({"sin", "ja", "jin"}, "water", "water_trine"),
    ({"hae", "myo", "mi"}, "wood", "wood_trine"),
    ({"in", "o", "sul"}, "fire", "fire_trine"),
    ({"sa", "yu", "chuk"}, "metal", "metal_trine"),
]

THREE_MEETING = [
    ({"in", "myo", "jin"}, "wood", "wood_seasonal_meeting"),
    ({"sa", "o", "mi"}, "fire", "fire_seasonal_meeting"),
    ({"sin", "yu", "sul"}, "metal", "metal_seasonal_meeting"),
    ({"hae", "ja", "chuk"}, "water", "water_seasonal_meeting"),
]


def _domains_for_positions(positions: list[str]) -> list[str]:
    domains: list[str] = []
    for position in positions:
        for domain in POSITION_DOMAINS.get(position, []):
            if domain not in domains:
                domains.append(domain)
    return domains


def _record(
    relation_type: str,
    branches: list[str],
    positions: list[str],
    effect_element: str | None,
    intensity: str,
    basis_code: str,
) -> BranchInteraction:
    return BranchInteraction(
        relation_type=relation_type,
        branches=branches,
        positions=positions,
        effect_element=effect_element,
        intensity=intensity,
        domain_links=_domains_for_positions(positions),
        basis_code=basis_code,
    )


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _natal_positions(chart: BirthChartResult) -> dict[str, str]:
    positions = {
        "year": chart.year_pillar.branch_key,
        "month": chart.month_pillar.branch_key,
        "day": chart.day_pillar.branch_key,
    }
    if not _birth_time_unknown(chart):
        positions["hour"] = chart.hour_pillar.branch_key
    return positions


def find_natal_interactions(chart: BirthChartResult) -> list[BranchInteraction]:
    return find_interactions(_natal_positions(chart))


def _element_direction(first: str, second: str) -> tuple[str, str, str, str]:
    if first == second:
        return "same", first, second, f"{ELEMENT_LABELS[first]} 동기"
    if ELEMENT_GENERATES[first] == second:
        return "generates", first, second, f"{ELEMENT_LABELS[first]}생{ELEMENT_LABELS[second]}"
    if ELEMENT_GENERATES[second] == first:
        return "generates", second, first, f"{ELEMENT_LABELS[second]}생{ELEMENT_LABELS[first]}"
    if ELEMENT_CONTROLS[first] == second:
        return "controls", first, second, f"{ELEMENT_LABELS[first]}극{ELEMENT_LABELS[second]}"
    return "controls", second, first, f"{ELEMENT_LABELS[second]}극{ELEMENT_LABELS[first]}"


def build_natal_branch_pairs(
    chart: BirthChartResult,
    interactions: list[BranchInteraction] | None = None,
) -> list[BranchPairCombination]:
    position_to_branch = _natal_positions(chart)
    formal_interactions = interactions if interactions is not None else find_interactions(position_to_branch)
    pairs: list[BranchPairCombination] = []
    for (position_a, branch_a), (position_b, branch_b) in combinations(position_to_branch.items(), 2):
        positions = [position_a, position_b]
        branches = [branch_a, branch_b]
        first_element = str(BRANCH_METADATA[branch_a]["element"])
        second_element = str(BRANCH_METADATA[branch_b]["element"])
        element_relation, source_element, target_element, relation_label = _element_direction(
            first_element,
            second_element,
        )
        rule = element_pair_rule(first_element, second_element)
        related_formal = [
            item
            for item in formal_interactions
            if len(item.positions) == 2
            and set(item.positions) == set(positions)
            and sorted(item.branches) == sorted(branches)
        ]
        formal_types = list(dict.fromkeys(item.relation_type for item in related_formal))
        formal_strengths = {item.intensity for item in related_formal}
        if "strong" in formal_strengths:
            intensity = "strong"
        elif "moderate" in formal_strengths or {"month", "day"}.intersection(positions):
            intensity = "moderate"
        else:
            intensity = "mild"
        domains = _domains_for_positions(positions)
        for domain in list(rule.get("domain_links") or []):
            if domain not in domains:
                domains.append(domain)
        basis_codes = [
            f"branch_pair_{position_a}_{position_b}_{branch_a}_{branch_b}",
            f"branch_pair_element_{source_element}_{element_relation}_{target_element}",
        ]
        basis_codes.extend(item.basis_code for item in related_formal)
        pairs.append(
            BranchPairCombination(
                pair_id=f"branch_pair_{position_a}_{position_b}",
                branches=branches,
                positions=positions,
                elements=[first_element, second_element],
                element_relation=element_relation,
                relation_label=relation_label,
                source_element=source_element,
                target_element=target_element,
                formal_relation_types=formal_types,
                intensity=intensity,
                domain_links=domains,
                basis_codes=list(dict.fromkeys(basis_codes)),
                trait_keywords=list(rule.get("trait_keywords") or []),
                interpretation=str(rule.get("interpretation") or ""),
            )
        )
    return pairs


def find_interactions(position_to_branch: dict[str, str]) -> list[BranchInteraction]:
    interactions: list[BranchInteraction] = []
    items = list(position_to_branch.items())

    for (pos_a, branch_a), (pos_b, branch_b) in combinations(items, 2):
        branches = [branch_a, branch_b]
        positions = [pos_a, pos_b]
        key = _pair(branch_a, branch_b)

        if key in SIX_COMBINE:
            interactions.append(_record("six_combine", branches, positions, SIX_COMBINE[key], "moderate", "branch_six_combine"))
        if key in CLASH:
            interactions.append(_record("clash", branches, positions, None, "strong", "branch_clash"))
        if key in PUNISHMENT:
            interactions.append(_record("punishment", branches, positions, None, "moderate", "branch_punishment"))
        if key in HARM:
            interactions.append(_record("harm", branches, positions, None, "mild", "branch_harm"))
        if key in BREAK:
            interactions.append(_record("break", branches, positions, None, "mild", "branch_break"))
        if branch_a == branch_b and branch_a in SELF_PUNISHMENT_BRANCHES:
            interactions.append(_record("self_punishment", branches, positions, None, "moderate", "branch_self_punishment"))

    branch_set = set(position_to_branch.values())
    for branches, element, code in THREE_HARMONY:
        if branches.issubset(branch_set):
            positions = [position for position, branch in position_to_branch.items() if branch in branches]
            interactions.append(_record("three_harmony", sorted(branches), positions, element, "strong", code))
        elif len(branches.intersection(branch_set)) == 2:
            positions = [position for position, branch in position_to_branch.items() if branch in branches]
            interactions.append(_record("three_harmony_half", sorted(branches.intersection(branch_set)), positions, element, "mild", f"{code}_half"))

    for branches, element, code in THREE_MEETING:
        if branches.issubset(branch_set):
            positions = [position for position, branch in position_to_branch.items() if branch in branches]
            interactions.append(_record("three_meeting", sorted(branches), positions, element, "strong", code))

    return interactions


def flow_interactions(chart: BirthChartResult, flow_position: str, branch_key: str) -> list[BranchInteraction]:
    positions = _natal_positions(chart)
    positions[flow_position] = branch_key
    return [
        item
        for item in find_interactions(positions)
        if flow_position in item.positions
    ]
