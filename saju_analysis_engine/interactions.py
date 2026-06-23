"""Branch relationship rules: combinations, clashes, penalties, harms, breaks."""

from __future__ import annotations

from itertools import combinations

from saju_birth_engine.models import BirthChartResult

from .constants import POSITION_DOMAINS
from .models import BranchInteraction


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


def _natal_positions(chart: BirthChartResult) -> dict[str, str]:
    return {
        "year": chart.year_pillar.branch_key,
        "month": chart.month_pillar.branch_key,
        "day": chart.day_pillar.branch_key,
        "hour": chart.hour_pillar.branch_key,
    }


def find_natal_interactions(chart: BirthChartResult) -> list[BranchInteraction]:
    return find_interactions(_natal_positions(chart))


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
