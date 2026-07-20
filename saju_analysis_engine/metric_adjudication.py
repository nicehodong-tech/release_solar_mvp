"""Metric-specific adjudication for customer-facing natal scores.

The base life-feature axes describe broad capacities.  Public product metrics
need one more pass because, for example, earning money and retaining an asset
do not use the same combination of roles, positions, and branch conditions.
This module keeps that pass declarative and auditable instead of adding a
single variance multiplier to every score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .constants import TEN_GOD_GROUPS
from .metric_theory_evidence import evaluate_metric_theory
from .models import ChartStructure, ExpertPriorityAdjudication
from .relation_polarity import branch_relation_polarity


@dataclass(frozen=True)
class NatalMetricContract:
    support_groups: tuple[str, ...]
    pressure_groups: tuple[str, ...] = ()
    support_ten_gods: tuple[str, ...] = ()
    pressure_ten_gods: tuple[str, ...] = ()
    focus_positions: tuple[str, ...] = ()
    relation_positions: tuple[str, ...] = ()
    spouse_star: bool = False
    hour_focus: bool = False


def _contract(
    support: str,
    *,
    pressure: str = "",
    support_ten_gods: str = "",
    pressure_ten_gods: str = "",
    positions: str = "",
    relations: str = "",
    spouse_star: bool = False,
    hour_focus: bool = False,
) -> NatalMetricContract:
    split = lambda value: tuple(item for item in value.split() if item)
    return NatalMetricContract(
        support_groups=split(support),
        pressure_groups=split(pressure),
        support_ten_gods=split(support_ten_gods),
        pressure_ten_gods=split(pressure_ten_gods),
        focus_positions=split(positions),
        relation_positions=split(relations),
        spouse_star=spouse_star,
        hour_focus=hour_focus,
    )


# Every metric exposed by PRODUCT_DOMAIN_METRIC_SPECS has its own contract.
# Similar-looking metrics may share ingredients, but their position and
# pressure emphasis differs.  This explicit registry is also the quality gate:
# a public metric without a contract must not silently inherit a generic score.
NATAL_METRIC_CONTRACTS: dict[str, NatalMetricContract] = {
    # Money
    "wealth_formation": _contract("output wealth", pressure="peer", support_ten_gods="sik_sin jeong_jae pyeon_jae", pressure_ten_gods="geob_jae", positions="month", relations="month"),
    "income_generation": _contract("output wealth", pressure="peer resource", support_ten_gods="sik_sin pyeon_jae sang_gwan", pressure_ten_gods="geob_jae pyeon_in", positions="month", relations="month"),
    "asset_consolidation": _contract(
        "wealth resource officer",
        pressure="peer output",
        support_ten_gods="jeong_jae jeong_in jeong_gwan",
        pressure_ten_gods="geob_jae sang_gwan",
        positions="day hour",
        relations="day",
        hour_focus=True,
    ),
    "cashflow_stability": _contract("wealth resource officer", pressure="peer", support_ten_gods="jeong_jae jeong_in jeong_gwan", pressure_ten_gods="geob_jae sang_gwan", positions="month day", relations="month day"),
    "contract_title_stability": _contract("resource officer wealth", pressure="peer output", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="geob_jae sang_gwan", positions="month day", relations="month day"),
    "shared_money_control": _contract("officer resource", pressure="peer", support_ten_gods="jeong_gwan jeong_in", pressure_ten_gods="geob_jae", positions="day month", relations="day month"),
    "financial_loss_defense": _contract("resource officer wealth", pressure="peer output", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="geob_jae pyeon_jae sang_gwan", positions="day hour", relations="day hour", hour_focus=True),
    "investment_trading_judgment": _contract("wealth resource output", pressure="peer", support_ten_gods="pyeon_jae jeong_in sik_sin", pressure_ten_gods="geob_jae", positions="month day", relations="month day"),
    "performance_reward": _contract("output wealth officer", pressure="peer", support_ten_gods="sik_sin jeong_jae jeong_gwan", pressure_ten_gods="geob_jae", positions="month", relations="month"),
    "late_life_wealth_growth": _contract(
        "wealth resource output",
        pressure="peer",
        support_ten_gods="jeong_jae jeong_in sik_sin",
        pressure_ten_gods="geob_jae",
        positions="hour day",
        relations="hour",
        hour_focus=True,
    ),

    # Career
    "achievement_accumulation": _contract("output officer resource", pressure="peer", support_ten_gods="sik_sin jeong_gwan jeong_in", pressure_ten_gods="geob_jae sang_gwan", positions="month hour", relations="month"),
    "organization_fit": _contract("officer resource", pressure="output peer", support_ten_gods="jeong_gwan jeong_in", pressure_ten_gods="sang_gwan geob_jae", positions="month", relations="month"),
    "promotion_title_readiness": _contract("officer resource wealth", pressure="output peer", support_ten_gods="jeong_gwan jeong_in jeong_jae", pressure_ten_gods="sang_gwan geob_jae", positions="month year", relations="month"),
    "professional_depth": _contract("resource output", pressure="wealth peer", support_ten_gods="jeong_in sik_sin pyeon_in", positions="month hour", relations="month"),
    "practical_execution": _contract("output officer", pressure="resource", support_ten_gods="sik_sin pyeon_gwan", pressure_ten_gods="pyeon_in", positions="month", relations="month"),
    "planning_judgment": _contract("resource wealth officer", pressure="output", support_ten_gods="jeong_in jeong_jae jeong_gwan", pressure_ten_gods="sang_gwan", positions="month", relations="month"),
    "authority_scope": _contract("officer peer resource", pressure="output", support_ten_gods="jeong_gwan pyeon_gwan bi_gyeon", pressure_ten_gods="sang_gwan", positions="month hour", relations="month hour", hour_focus=True),
    "evaluation_management": _contract("officer resource output", pressure="peer", support_ten_gods="jeong_gwan jeong_in sik_sin", pressure_ten_gods="geob_jae sang_gwan", positions="month year", relations="month"),
    "independent_work": _contract("output wealth peer", pressure="officer resource", support_ten_gods="sik_sin pyeon_jae bi_gyeon", positions="month hour", relations="month"),
    "career_continuity": _contract("resource officer output", pressure="peer", support_ten_gods="jeong_in jeong_gwan sik_sin", positions="month hour", relations="month"),

    # Personality
    "self_direction": _contract("peer officer output", pressure="resource", support_ten_gods="bi_gyeon pyeon_gwan sik_sin", positions="day", relations="day"),
    "emotional_alignment": _contract("resource officer", pressure="peer output", support_ten_gods="jeong_in jeong_gwan", pressure_ten_gods="geob_jae sang_gwan", positions="day month", relations="day month"),
    "action_pace": _contract("output peer wealth", pressure="resource", support_ten_gods="sik_sin bi_gyeon pyeon_jae", pressure_ten_gods="pyeon_in", positions="month day", relations="month day"),
    "decision_consistency": _contract("resource officer wealth", pressure="output", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="sang_gwan", positions="day month", relations="day month"),
    "focus_depth": _contract("resource officer output", pressure="wealth peer", support_ten_gods="pyeon_in jeong_in sik_sin", positions="day hour", relations="day hour", hour_focus=True),
    "boundary_management": _contract("officer resource peer", pressure="peer output", support_ten_gods="jeong_gwan jeong_in bi_gyeon", pressure_ten_gods="geob_jae sang_gwan", positions="day year", relations="day year"),
    "crisis_recovery": _contract("output resource officer", pressure="peer", support_ten_gods="sik_sin pyeon_gwan jeong_in", positions="day month", relations="day month"),
    "change_adaptability": _contract("output wealth peer", pressure="resource", support_ten_gods="sik_sin pyeon_jae bi_gyeon", pressure_ten_gods="pyeon_in", positions="month day", relations="month day"),
    "communication_expression": _contract("output peer", pressure="resource officer", support_ten_gods="sik_sin sang_gwan", pressure_ten_gods="pyeon_in", positions="day month year", relations="day month"),
    "responsibility_capacity": _contract("officer resource wealth", pressure="output peer", support_ten_gods="jeong_gwan pyeon_gwan jeong_in", pressure_ten_gods="sang_gwan geob_jae", positions="month day year", relations="month year"),
    "honor_recognition": _contract("output officer peer", pressure="resource", support_ten_gods="sik_sin sang_gwan jeong_gwan", pressure_ten_gods="pyeon_in", positions="year month", relations="year month"),
    "loss_avoidance": _contract("resource officer wealth", pressure="output peer", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="sang_gwan geob_jae", positions="day month hour", relations="day hour", hour_focus=True),

    # Love
    "opposite_sex_appeal": _contract("output wealth", pressure="resource", support_ten_gods="sik_sin sang_gwan pyeon_jae", positions="day month", relations="day month", spouse_star=True),
    "affection_expression": _contract("output wealth", pressure="resource officer", support_ten_gods="sik_sin sang_gwan", pressure_ten_gods="pyeon_in", positions="day month", relations="day month", spouse_star=True),
    "relationship_stability": _contract("resource officer", pressure="peer output", support_ten_gods="jeong_in jeong_gwan", pressure_ten_gods="geob_jae sang_gwan", positions="day hour", relations="day hour", spouse_star=True, hour_focus=True),
    "romantic_emotional_stability": _contract("resource officer", pressure="output peer", support_ten_gods="jeong_in jeong_gwan", pressure_ten_gods="sang_gwan geob_jae", positions="day month", relations="day month", spouse_star=True),
    "partner_selection": _contract("resource officer wealth", pressure="output peer", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="sang_gwan geob_jae", positions="day month year", relations="day year", spouse_star=True),
    "conflict_recovery": _contract("output resource officer", pressure="peer", support_ten_gods="sik_sin jeong_in jeong_gwan", positions="day month", relations="day month", spouse_star=True),
    "partner_dependency_control": _contract("peer resource officer", pressure="wealth output", support_ten_gods="bi_gyeon jeong_in jeong_gwan", pressure_ten_gods="pyeon_jae sang_gwan", positions="day year", relations="day year", spouse_star=True),
    "relationship_agency": _contract("peer output officer", pressure="resource", support_ten_gods="bi_gyeon sik_sin jeong_gwan", pressure_ten_gods="pyeon_in", positions="day month", relations="day month", spouse_star=True),
    "bond_continuity": _contract("resource officer wealth", pressure="peer output", support_ten_gods="jeong_in jeong_gwan jeong_jae", positions="day hour", relations="day hour", spouse_star=True, hour_focus=True),
    "breakup_resilience": _contract("resource officer peer", pressure="output wealth", support_ten_gods="jeong_in jeong_gwan bi_gyeon", pressure_ten_gods="sang_gwan pyeon_jae", positions="day month hour", relations="day month hour", spouse_star=True, hour_focus=True),

    # Marriage
    "marriage_overall_stability": _contract("resource officer wealth", pressure="peer output", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="geob_jae sang_gwan", positions="day hour", relations="day hour", spouse_star=True, hour_focus=True),
    "spouse_match": _contract("resource officer wealth", pressure="peer output", support_ten_gods="jeong_gwan jeong_jae", pressure_ten_gods="geob_jae sang_gwan", positions="day", relations="day", spouse_star=True),
    "household_coordination": _contract("resource output officer", pressure="peer", support_ten_gods="jeong_in sik_sin jeong_gwan", pressure_ten_gods="geob_jae", positions="day hour", relations="day hour", spouse_star=True, hour_focus=True),
    "family_responsibility": _contract("officer resource wealth", pressure="peer", support_ten_gods="jeong_gwan jeong_in jeong_jae", pressure_ten_gods="geob_jae", positions="day year", relations="day year", spouse_star=True),
    "marital_financial_agreement": _contract("wealth officer resource", pressure="peer", support_ten_gods="jeong_jae jeong_gwan jeong_in", pressure_ten_gods="geob_jae", positions="day month", relations="day month", spouse_star=True),
    "family_relationship_stability": _contract("resource officer", pressure="peer output", support_ten_gods="jeong_in jeong_gwan", positions="day year", relations="day year", spouse_star=True),
    "long_term_marriage": _contract(
        "resource officer wealth",
        pressure="peer output",
        support_ten_gods="jeong_in jeong_gwan jeong_jae",
        pressure_ten_gods="geob_jae sang_gwan",
        positions="hour day",
        relations="hour day",
        spouse_star=True,
        hour_focus=True,
    ),
    "spouse_conflict_control": _contract("resource output officer", pressure="peer", support_ten_gods="jeong_in sik_sin jeong_gwan", pressure_ten_gods="geob_jae", positions="day month year", relations="day month year", spouse_star=True),
    "marriage_decision": _contract("officer wealth resource", pressure="output peer", support_ten_gods="jeong_gwan jeong_jae jeong_in", pressure_ten_gods="sang_gwan geob_jae", positions="day month", relations="day month", spouse_star=True),
    "post_marriage_stability": _contract(
        "resource wealth officer",
        pressure="peer output",
        support_ten_gods="jeong_in jeong_jae jeong_gwan",
        pressure_ten_gods="geob_jae sang_gwan",
        positions="day hour",
        relations="day hour",
        spouse_star=True,
        hour_focus=True,
    ),

    # Honor
    "honor_social_recognition": _contract("output officer", pressure="resource peer", support_ten_gods="sik_sin sang_gwan jeong_gwan", pressure_ten_gods="pyeon_in geob_jae", positions="year month", relations="year"),
    "honor_reputation_formation": _contract("resource officer output", pressure="peer", support_ten_gods="jeong_in jeong_gwan sik_sin", pressure_ten_gods="geob_jae sang_gwan", positions="year month", relations="year month"),
    "honor_title_rise": _contract("officer wealth resource", pressure="output peer", support_ten_gods="jeong_gwan jeong_jae jeong_in", pressure_ten_gods="sang_gwan geob_jae", positions="month", relations="month"),
    "honor_public_trust": _contract("resource officer", pressure="output peer", support_ten_gods="jeong_in jeong_gwan", pressure_ten_gods="sang_gwan geob_jae", positions="year month", relations="year"),
    "honor_responsibility_acceptance": _contract("peer officer resource", pressure="output wealth", support_ten_gods="bi_gyeon pyeon_gwan jeong_gwan", pressure_ten_gods="sang_gwan pyeon_jae", positions="month day", relations="month day"),
    "honor_organizational_presence": _contract("output peer officer", pressure="resource", support_ten_gods="sik_sin bi_gyeon jeong_gwan", pressure_ten_gods="pyeon_in", positions="month day", relations="month day"),
    "honor_authority_establishment": _contract("officer peer resource", pressure="output", support_ten_gods="jeong_gwan pyeon_gwan bi_gyeon", pressure_ten_gods="sang_gwan", positions="month year", relations="month year"),
    "honor_legitimacy_management": _contract("resource officer wealth", pressure="output peer", support_ten_gods="jeong_in jeong_gwan jeong_jae", pressure_ten_gods="sang_gwan geob_jae", positions="year month", relations="year"),

    # Social
    "social_affinity": _contract("output peer", pressure="resource", support_ten_gods="sik_sin bi_gyeon", pressure_ten_gods="pyeon_in", positions="month day", relations="day month"),
    "social_trust_formation": _contract("resource officer", pressure="output peer", support_ten_gods="jeong_in jeong_gwan", pressure_ten_gods="sang_gwan geob_jae", positions="month day", relations="day month"),
    "social_relationship_continuity": _contract("resource officer peer", pressure="output", support_ten_gods="jeong_in jeong_gwan bi_gyeon", pressure_ten_gods="sang_gwan geob_jae", positions="day month", relations="day month"),
    "social_distance_control": _contract("officer resource peer", pressure="output", support_ten_gods="jeong_gwan jeong_in bi_gyeon", pressure_ten_gods="sang_gwan", positions="day", relations="day month"),
    "social_cooperation": _contract("output officer resource", pressure="peer", support_ten_gods="sik_sin jeong_gwan jeong_in", pressure_ten_gods="geob_jae", positions="month day", relations="day month"),
    "social_competition_control": _contract("officer resource peer", pressure="peer output", support_ten_gods="jeong_gwan jeong_in bi_gyeon", pressure_ten_gods="geob_jae sang_gwan", positions="month", relations="month day"),
    "social_speech_influence": _contract("output officer", pressure="resource peer", support_ten_gods="sik_sin sang_gwan jeong_gwan", pressure_ten_gods="pyeon_in geob_jae", positions="month day", relations="day"),
    "social_conflict_avoidance": _contract("resource officer output", pressure="peer", support_ten_gods="jeong_in jeong_gwan sik_sin", pressure_ten_gods="geob_jae", positions="day month", relations="day month"),
    "social_benefactor_support": _contract("resource officer output", pressure="peer", support_ten_gods="jeong_in jeong_gwan sik_sin", positions="month year", relations="month year"),
    "social_acquaintance_loss_defense": _contract("officer resource peer", pressure="peer wealth", support_ten_gods="jeong_gwan jeong_in bi_gyeon", pressure_ten_gods="geob_jae pyeon_jae", positions="year day", relations="year day"),
}


NATAL_METRIC_DOMAIN_BY_KEY: dict[str, str] = {
    key: domain
    for domain, keys in {
        "money": (
            "wealth_formation", "income_generation", "asset_consolidation",
            "cashflow_stability", "contract_title_stability", "shared_money_control",
            "financial_loss_defense", "investment_trading_judgment",
            "performance_reward", "late_life_wealth_growth",
        ),
        "career": (
            "achievement_accumulation", "organization_fit", "promotion_title_readiness",
            "professional_depth", "practical_execution", "planning_judgment",
            "authority_scope", "evaluation_management", "independent_work",
            "career_continuity",
        ),
        "love": (
            "opposite_sex_appeal", "affection_expression", "relationship_stability",
            "romantic_emotional_stability", "partner_selection", "conflict_recovery",
            "partner_dependency_control", "relationship_agency", "bond_continuity",
            "breakup_resilience",
        ),
        "marriage": (
            "marriage_overall_stability", "spouse_match", "household_coordination",
            "family_responsibility", "marital_financial_agreement",
            "family_relationship_stability", "long_term_marriage",
            "spouse_conflict_control", "marriage_decision", "post_marriage_stability",
        ),
    }.items()
    for key in keys
}


def _clip(value: float, low: float = 18.0, high: float = 92.0) -> float:
    return max(low, min(high, value))


def _ten_god_amount(structure: ChartStructure, ten_god: str) -> float:
    profile = structure.ten_god_profile
    return float(profile.visible_counts.get(ten_god, 0.0)) + float(profile.hidden_counts.get(ten_god, 0.0)) * 0.8


def _group_amount(structure: ChartStructure, group: str) -> float:
    return float(structure.ten_god_profile.group_scores.get(group, 0.0))


def _availability_score(amount: float) -> float:
    if amount <= 0.04:
        return 24.0
    if amount < 0.35:
        return 38.0 + amount * 20.0
    if amount < 0.9:
        return 49.0 + (amount - 0.35) * 30.0
    if amount < 1.8:
        return 65.5 + (amount - 0.9) * 15.0
    if amount < 2.8:
        return 79.0 - (amount - 1.8) * 7.0
    return max(42.0, 72.0 - (amount - 2.8) * 12.0)


def _role_fit_score(structure: ChartStructure, group: str) -> float:
    fit = structure.month_governance_profile.role_fits.get(group)
    if fit is None:
        return 50.0
    net = float(fit.support_score) - float(fit.pressure_score)
    fit_score = _clip(50.0 + net * 4.2)
    return fit_score * 0.58 + _availability_score(_group_amount(structure, group)) * 0.42


def _pressure_protection_score(structure: ChartStructure, group: str) -> float:
    fit = structure.month_governance_profile.role_fits.get(group)
    amount = _group_amount(structure, group)
    support = float(getattr(fit, "support_score", 0.0) or 0.0)
    pressure = float(getattr(fit, "pressure_score", 0.0) or 0.0)
    # The absence of a pressure role removes a liability; it does not prove a
    # strong defensive capacity. Keep that state neutral and let actual
    # regulation raise it only when there is something present to regulate.
    # This prevents an empty pressure group from becoming an automatic 76+
    # point bonus in every public metric that declares a caution role.
    active_pressure = min(1.4, max(0.0, amount))
    abundance_burden = max(0.0, amount - 0.18) * 12.5
    month_burden = max(0.0, pressure - support) * 4.2
    regulation = active_pressure * max(0.0, support - pressure) * 1.8
    return _clip(50.0 - abundance_burden - month_burden + regulation, 18.0, 64.0)


def _pressure_ten_god_score(structure: ChartStructure, ten_god: str) -> float:
    """Score freedom from one contract-declared pressure ten-god.

    No presence is neutral. A trace is retained without overreaction, while a
    rooted or repeated pressure role must remain visible as a real deduction.
    The surrounding role-fit layer can still judge whether the broader group
    is useful; this exact-ten-god layer only answers the declared caution.
    """

    amount = _ten_god_amount(structure, ten_god)
    burden = max(0.0, amount - 0.12) * 15.0
    return _clip(50.0 - burden, 18.0, 50.0)


def _priority_weights(length: int) -> list[float]:
    """Return descending weights for a contract's declared priority order.

    Contracts deliberately list the role that defines the metric first.  A
    plain mean made a primary role and an auxiliary role equally responsible
    for the result and pulled distinct metrics back toward the same midpoint.
    """

    if length <= 0:
        return []
    raw = [1.0 / (index + 1) for index in range(length)]
    total = sum(raw)
    return [value / total for value in raw]


def _priority_average(values: list[float]) -> float:
    if not values:
        return 50.0
    weights = _priority_weights(len(values))
    return sum(value * weight for value, weight in zip(values, weights, strict=True))


def _contract_role_score(structure: ChartStructure, contract: NatalMetricContract) -> float:
    support_score = _priority_average(
        [_role_fit_score(structure, group) for group in contract.support_groups]
    )
    if not contract.pressure_groups:
        return support_score
    protection_score = _priority_average(
        [_pressure_protection_score(structure, group) for group in contract.pressure_groups]
    )
    # The declared support role defines the capacity. Pressure protection is a
    # condition on whether that capacity is kept, not a second positive role.
    return support_score * 0.76 + protection_score * 0.24


def _specific_ten_god_score(structure: ChartStructure, contract: NatalMetricContract) -> float:
    support_scores = [
        _availability_score(_ten_god_amount(structure, ten_god))
        for ten_god in contract.support_ten_gods
    ]
    pressure_scores = [
        _pressure_ten_god_score(structure, ten_god)
        for ten_god in contract.pressure_ten_gods
    ]
    if support_scores and pressure_scores:
        return _priority_average(support_scores) * 0.76 + _priority_average(pressure_scores) * 0.24
    if support_scores:
        return _priority_average(support_scores)
    if pressure_scores:
        return _priority_average(pressure_scores)
    return 50.0


def _position_group_weights(structure: ChartStructure, position: str) -> dict[str, float]:
    signal = structure.position_signals.get(position)
    if signal is None:
        return {}
    roles = [
        (signal.stem_ten_god, float(signal.stem_visibility_weight)),
        (signal.branch_main_ten_god, float(signal.branch_reality_weight)),
    ]
    hidden_weight = float(signal.hidden_reality_weight) / max(1, len(signal.hidden_ten_gods))
    roles.extend((ten_god, hidden_weight) for ten_god in signal.hidden_ten_gods)
    groups: dict[str, float] = {}
    for ten_god, weight in roles:
        group = "peer" if ten_god == "self" else TEN_GOD_GROUPS.get(ten_god, "")
        if group:
            groups[group] = groups.get(group, 0.0) + weight
    return groups


def _position_score(structure: ChartStructure, contract: NatalMetricContract) -> float:
    if not contract.focus_positions:
        return 50.0
    position_scores: list[float] = []
    for position in contract.focus_positions:
        groups = _position_group_weights(structure, position)
        if not groups:
            # Unknown birth time must lower confidence, not invent an hour.
            position_scores.append(50.0)
            continue
        support_presence = [
            min(1.0, groups.get(group, 0.0) / 0.9)
            for group in contract.support_groups
        ]
        pressure_presence = [
            min(1.0, groups.get(group, 0.0) / 0.9)
            for group in contract.pressure_groups
        ]
        support_coverage = _priority_average(support_presence) if support_presence else 0.0
        pressure_coverage = _priority_average(pressure_presence) if pressure_presence else 0.0
        position_scores.append(_clip(28.0 + support_coverage * 66.0 - pressure_coverage * 24.0))
    return _priority_average(position_scores)


def _relation_score(structure: ChartStructure, contract: NatalMetricContract) -> float:
    positions = set(contract.relation_positions)
    if not positions:
        return 50.0
    relevant = [
        interaction
        for interaction in structure.branch_interactions
        if positions.intersection(interaction.positions)
    ]
    # No formal relation is neutral. It must not supply a small hidden bonus
    # before the ordinary branch-pair background is even considered.
    score = 50.0
    for interaction in relevant:
        polarity = branch_relation_polarity(
            structure.element_profile,
            interaction,
            structure.pattern_profile,
        )
        intensity = {"strong": 1.25, "moderate": 1.0, "mild": 0.65}.get(interaction.intensity, 0.8)
        if polarity.polarity == "supportive":
            score += 7.0 * intensity
        elif polarity.polarity == "burdensome":
            score -= 10.0 * intensity
        elif polarity.polarity == "mixed":
            score -= 2.5 * intensity
        else:
            score -= 0.8 * intensity
    formal_score = _clip(score)
    pair_score, pair_count = _ordinary_branch_pair_score(structure, contract)
    if pair_count <= 0:
        return formal_score
    # Ordinary branch pairs describe the background circulation between the
    # palaces selected by the contract. Formal combine/clash/punishment rules
    # remain primary and are excluded from this secondary calculation.
    pair_weight = 0.18 if relevant else 0.42
    return _clip(formal_score * (1.0 - pair_weight) + pair_score * pair_weight)


def _element_fit_net(structure: ChartStructure, element: str) -> float:
    fit = structure.month_governance_profile.element_fits.get(element)
    if fit is None:
        return 0.0
    return max(-6.0, min(6.0, float(fit.support_score) - float(fit.pressure_score)))


def _ordinary_branch_pair_score(
    structure: ChartStructure,
    contract: NatalMetricContract,
) -> tuple[float, int]:
    positions = set(contract.relation_positions)
    if not positions:
        return 50.0, 0
    pairs = [
        pair
        for pair in structure.branch_pair_combinations
        if not pair.formal_relation_types and positions.intersection(pair.positions)
    ]
    if not pairs:
        return 50.0, 0

    contributions: list[float] = []
    for pair in pairs:
        source_fit = _element_fit_net(structure, pair.source_element)
        target_fit = _element_fit_net(structure, pair.target_element)
        if pair.element_relation == "same":
            alignment = source_fit
        elif pair.element_relation == "generates":
            # In a generation path the receiving element determines whether
            # the circulation serves the month command; the source confirms
            # whether that support has a usable supply line.
            alignment = target_fit * 0.68 + source_fit * 0.32
        else:
            # Control is useful when a supported controller restrains an
            # element that the month command marks as a burden. It is costly
            # when it suppresses an element the chart actually needs.
            alignment = source_fit * 0.42 - target_fit * 0.68 - 0.35
        intensity = {"strong": 1.15, "moderate": 1.0, "mild": 0.68}.get(pair.intensity, 0.8)
        contributions.append(alignment * intensity)

    average_alignment = sum(contributions) / len(contributions)
    return _clip(50.0 + average_alignment * 2.2), len(contributions)


def _spouse_star_score(structure: ChartStructure) -> float:
    gender = str(getattr(structure, "gender", "unknown") or "unknown")
    spouse_group = "wealth" if gender == "male" else "officer" if gender == "female" else ""
    if not spouse_group:
        return 50.0
    role_score = _role_fit_score(structure, spouse_group)
    day_groups = _position_group_weights(structure, "day")
    day_presence = min(1.0, day_groups.get(spouse_group, 0.0) / 0.9)
    return _clip(role_score * 0.7 + (34.0 + day_presence * 52.0) * 0.3)


def _expert_metric_gate_score(
    metric_key: str,
    contract: NatalMetricContract,
    adjudication: ExpertPriorityAdjudication | None,
) -> tuple[float, int]:
    if adjudication is None:
        return 50.0, 0
    domain = NATAL_METRIC_DOMAIN_BY_KEY.get(metric_key, "")
    projection = adjudication.domain_projections.get(domain)
    if projection is None:
        return 50.0, 0

    matching_useful = [
        item
        for item in adjudication.useful_element_decisions
        if domain in item.domain_links and item.role_group in contract.support_groups
    ]
    lead_pattern = (
        adjudication.pattern_viability_decisions[0]
        if adjudication.pattern_viability_decisions
        else None
    )
    pattern_relevant = bool(
        lead_pattern is not None
        and lead_pattern.pattern_group in set(contract.support_groups + contract.pressure_groups)
    )
    if not matching_useful and not pattern_relevant:
        return 50.0, 0

    adjustments = projection.score_adjustments
    net = (
        float(adjustments.get("opportunity", 0)) * 1.15
        + float(adjustments.get("probability", 0)) * 0.75
        - float(adjustments.get("risk", 0)) * 1.25
    )
    evidence_count = len(matching_useful)
    if pattern_relevant and lead_pattern is not None:
        evidence_count += 1
        if lead_pattern.pattern_group in contract.support_groups:
            net += {
                "established": 2.0,
                "conditional": 0.8,
                "weak": -0.8,
                "broken": -1.8,
            }.get(lead_pattern.status, 0.0)
        elif lead_pattern.pattern_group in contract.pressure_groups:
            net += {
                "established": -1.2,
                "conditional": -0.5,
                "weak": 0.4,
                "broken": 0.8,
            }.get(lead_pattern.status, 0.0)
    confidence_factor = {"high": 1.0, "medium": 0.82, "low": 0.62}.get(
        str(projection.confidence),
        0.75,
    )
    return _clip(50.0 + net * 1.45 * confidence_factor), evidence_count


def _contract_grade(contract: NatalMetricContract | None) -> str:
    if contract is None:
        return "D"
    # A is reserved for a complete scoring contract. Spouse-star and hour
    # focus are useful modifiers, but they cannot replace an omitted month-led
    # role, palace, branch-relation, or exact ten-god premise.
    essential_layers = (
        bool(contract.support_groups or contract.pressure_groups),
        bool(contract.focus_positions),
        bool(contract.relation_positions),
        bool(contract.support_ten_gods or contract.pressure_ten_gods),
    )
    layer_count = sum(essential_layers)
    if all(essential_layers):
        return "A"
    if layer_count == 3:
        return "B+"
    if layer_count == 2:
        return "B"
    return "C"


def _contract_signature(contract: NatalMetricContract | None) -> tuple[tuple[str, ...], ...]:
    if contract is None:
        return ()
    return (
        contract.support_groups,
        contract.pressure_groups,
        contract.support_ten_gods,
        contract.pressure_ten_gods,
        contract.focus_positions,
        contract.relation_positions,
        ("spouse_star",) if contract.spouse_star else (),
        ("hour_focus",) if contract.hour_focus else (),
    )


def _centered_structural_adjustment(base_score: float, structural_score: float) -> float:
    """Reconcile a broad capacity with metric-specific structural evidence.

    ``base_score`` is the broad life-feature capacity, while
    ``structural_score`` is the metric-specific result of month-led role fit,
    palace position, branch relations and exact ten-god evidence.  Comparing
    the structural score only with a neutral 50 used to reward a 60-point
    structure even when the broad base was already 85.  That made weakly
    supported high capacities climb further and compressed several public
    metrics into the same upper band.

    Reconcile the two actual premises instead.  Positive structure may confirm
    a capacity, but it cannot manufacture one from a weak base.  A structural
    shortfall remains more visible because it identifies where a broad
    capacity does not survive the metric's month command, palace or relation
    conditions.  The bounds keep this layer from replacing the full engine
    judgment.
    """

    gap = structural_score - base_score
    if gap >= 0.0:
        if base_score < 45.0:
            factor = 0.20
        elif base_score < 55.0:
            factor = 0.28
        else:
            factor = 0.34
        return min(12.0, gap * factor)

    if base_score >= 75.0:
        factor = 0.44
    elif base_score >= 65.0:
        factor = 0.38
    else:
        factor = 0.34
    return max(-20.0, gap * factor)


def _apply_public_quality_evidence_gate(
    raw_score: float,
    *,
    theory_evaluation: dict[str, Any],
    lower_bound: float = 12.0,
    upper_bound: float = 96.0,
) -> dict[str, Any]:
    """Gate public grades by independent support and pressure evidence.

    This gate never creates a favorable or unfavorable result merely to widen
    a distribution. It only prevents an extreme grade that the independent
    theory families do not support, and prevents a material unresolved
    pressure from disappearing inside a high broad-capacity score.
    """

    support_count = int(
        theory_evaluation.get(
            "support_evidence_count",
            theory_evaluation.get("strong_support_count", 0),
        )
    )
    pressure_count = int(
        theory_evaluation.get(
            "pressure_evidence_count",
            theory_evaluation.get("strong_pressure_count", 0),
        )
    )
    counter_count = int(theory_evaluation.get("counter_count", 0))
    critical_pressure_count = int(
        theory_evaluation.get("critical_pressure_count", 0)
    )
    unresolved_critical_pressure_count = max(
        0,
        critical_pressure_count - counter_count,
    )
    gated_score = float(raw_score)
    gates: list[str] = []

    # Very good and danger are evidence grades, not merely numeric tails.
    if gated_score >= 80.0 and support_count < 3:
        # Keep the grade below "very good" without piling every unsupported
        # extreme on the same 79-point boundary. The retained value reflects
        # how many independent supports and counters were actually present.
        evidence_cap = 74.0 + min(5.0, support_count * 2.0 + counter_count)
        gated_score = min(gated_score, evidence_cap)
        gates.append("very_good_requires_three_support_families")
    if gated_score <= 29.0 and pressure_count < 3:
        evidence_floor = 34.0 - min(
            4.0,
            pressure_count * 2.0 + unresolved_critical_pressure_count,
        )
        gated_score = max(gated_score, evidence_floor)
        gates.append("danger_requires_three_pressure_families")

    # A good result needs at least two independent supports, or one support
    # plus a real counter-action that contains an identified pressure.
    if gated_score >= 65.0 and not (
        support_count >= 2 or (support_count >= 1 and counter_count >= 1)
    ):
        evidence_cap = 60.0 + min(4.0, support_count * 2.0 + counter_count)
        gated_score = min(gated_score, evidence_cap)
        gates.append("good_requires_independent_support")

    # A caution result also needs more than one weak source. This prevents a
    # single ambiguous signal from producing a long-lived negative verdict.
    if gated_score <= 44.0 and not (
        pressure_count >= 2 or unresolved_critical_pressure_count >= 1
    ):
        evidence_floor = 49.0 - min(
            4.0,
            pressure_count * 2.0 + unresolved_critical_pressure_count,
        )
        gated_score = max(gated_score, evidence_floor)
        gates.append("caution_requires_independent_pressure")

    # Critical pressure survives averaging unless an explicit counter-action
    # exists. Four independent pressures with almost no support are sufficient
    # to cap the public result in the caution band; they do not by themselves
    # manufacture a danger result.
    if unresolved_critical_pressure_count >= 1 and gated_score > 64.0:
        gated_score = 64.0
        gates.append("unresolved_critical_pressure_caps_good")
    if pressure_count >= 4 and support_count <= 1 and counter_count == 0 and gated_score > 44.0:
        gated_score = 44.0
        gates.append("convergent_pressure_caps_normal")

    # A result already below neutral should not hide a convergent, unresolved
    # pressure.  This is not a distribution adjustment: it is limited to the
    # lower-normal boundary and requires two independent pressure families, an
    # unresolved critical pressure and no counter-action.  Existing support is
    # still recorded, but it cannot be treated as if it resolved that pressure.
    if (
        44.0 < gated_score < 50.0
        and pressure_count >= 2
        and unresolved_critical_pressure_count >= 1
        and counter_count == 0
    ):
        gated_score = 44.0
        gates.append("unresolved_convergent_pressure_marks_caution_boundary")

    # Public grades are rendered from the rounded integer.  Apply the same
    # evidence contract to that integer boundary as well: a value such as
    # 64.6 must not round into the good band when the required independent
    # support is absent, and 44.4 must not round into caution without pressure.
    display_score = int(round(gated_score))
    if display_score >= 80 and support_count < 3:
        gated_score = min(gated_score, 79.0)
        if "very_good_requires_three_support_families" not in gates:
            gates.append("very_good_requires_three_support_families")
    display_score = int(round(gated_score))
    if display_score >= 65 and not (
        support_count >= 2 or (support_count >= 1 and counter_count >= 1)
    ):
        gated_score = min(gated_score, 64.0)
        if "good_requires_independent_support" not in gates:
            gates.append("good_requires_independent_support")
    display_score = int(round(gated_score))
    if display_score <= 29 and pressure_count < 3 and unresolved_critical_pressure_count < 1:
        gated_score = max(gated_score, 30.0)
        if "danger_requires_three_pressure_families" not in gates:
            gates.append("danger_requires_three_pressure_families")
    display_score = int(round(gated_score))
    if display_score <= 44 and not (
        pressure_count >= 2 or unresolved_critical_pressure_count >= 1
    ):
        gated_score = max(gated_score, 45.0)
        if "caution_requires_independent_pressure" not in gates:
            gates.append("caution_requires_independent_pressure")

    gated_score = _clip(gated_score, lower_bound, upper_bound)
    return {
        "quality_score": int(round(gated_score)),
        "raw_quality_score": round(float(raw_score), 2),
        "quality_gate_applied": bool(gates),
        "quality_gates": gates,
        "support_evidence_count": support_count,
        "pressure_evidence_count": pressure_count,
        "counter_evidence_count": counter_count,
        "critical_pressure_count": critical_pressure_count,
        "unresolved_critical_pressure_count": unresolved_critical_pressure_count,
    }


def adjudicate_natal_metric(
    *,
    metric_key: str,
    base_score: float,
    structure: ChartStructure | None,
    cycle_delta: float = 0.0,
    principle_delta: float = 0.0,
    gyeokguk_delta: float = 0.0,
    layer_delta: float = 0.0,
    expert_adjudication: ExpertPriorityAdjudication | None = None,
) -> dict[str, Any]:
    contract = NATAL_METRIC_CONTRACTS.get(metric_key)
    if structure is None or contract is None:
        return {
            "score": int(round(base_score)),
            "contract_grade": _contract_grade(contract),
            "contract_applied": False,
        }

    role_score = _contract_role_score(structure, contract)
    position_score = _position_score(structure, contract)
    relation_score = _relation_score(structure, contract)
    ten_god_score = _specific_ten_god_score(structure, contract)

    # A public metric must describe where and how the structure acts, not only
    # whether a favorable role group exists somewhere in the chart. Month-led
    # role fit remains the first premise; palace reality and branch circulation
    # receive enough weight to distinguish expression, relationship, household
    # and late-result metrics that would otherwise share the same ten-god pool.
    structural_parts: list[tuple[float, float]] = [
        (role_score, 0.28),
        (position_score, 0.30),
        (relation_score, 0.24),
        (ten_god_score, 0.18),
    ]
    spouse_score = None
    if contract.spouse_star:
        spouse_score = _spouse_star_score(structure)
        # The spouse star is a shared domain premise. Keeping it subordinate
        # prevents all love and marriage metrics from converging on the same
        # score while still retaining gender-specific spouse-star evidence.
        structural_parts = [(value, weight * 0.92) for value, weight in structural_parts]
        structural_parts.append((spouse_score, 0.08))
    structural_total = sum(value * weight for value, weight in structural_parts)
    structural_weight = sum(weight for _, weight in structural_parts) or 1.0
    structural_score = structural_total / structural_weight

    chain_score = _clip(
        50.0
        + cycle_delta * 2.7
        + principle_delta * 2.1
        + gyeokguk_delta * 1.8
        + layer_delta * 1.4
    )
    # Preserve the engine's broad capacity score and let the metric contract
    # adjudicate it around a neutral 50. Averaging absolute scores pulled high
    # and low capacities back toward the same midpoint. A centered adjustment
    # keeps the original engine contrast while allowing month command, exact
    # ten-god, position, branch relation and cycle evidence to move the result
    # only in the direction they actually support.
    pre_expert_structural_adjustment = _centered_structural_adjustment(
        base_score,
        structural_score,
    )
    expert_gate_score, expert_evidence_count = _expert_metric_gate_score(
        metric_key,
        contract,
        expert_adjudication,
    )
    structural_adjustment = pre_expert_structural_adjustment
    expert_reconciliation_adjustment = max(
        -2.5,
        min(2.5, (expert_gate_score - 50.0) * 0.18),
    ) if expert_evidence_count else 0.0
    # Position, exact ten-god and relation evidence are already constituent
    # parts of structural_score. Exposing separate diagnostics is useful, but
    # adding them once more would make the same evidence dominate the result.
    position_reality_adjustment = 0.0
    ten_god_specificity_adjustment = 0.0
    # Cycle, principle, gyeokguk and layer deltas already participate in the
    # upstream life-feature axes. Keep chain_score as an audit trace only.
    chain_adjustment = 0.0
    theory_evaluation = evaluate_metric_theory(
        metric_key=metric_key,
        structure=structure,
        contract=contract,
        base_score=base_score,
        legacy_scores={
            "role": role_score,
            "position": position_score,
            "relation": relation_score,
            "ten_god": ten_god_score,
            "spouse": spouse_score if spouse_score is not None else 50.0,
        },
    )
    theory_adjustment = float(theory_evaluation.get("adjustment", 0.0))
    high_dimensional_score = float(
        theory_evaluation.get(
            "high_dimensional_score",
            theory_evaluation.get("theory_score", 50.0),
        )
    )
    # The former pipeline kept the full theory stack inside a small additive
    # correction.  Hundreds of month, element, ten-god, stem and branch facts
    # could therefore move a public score by only a few points.  The direct
    # theory judgment is now the principal component.  Broad life capacity and
    # the compact legacy structural contract remain independent anchors, so a
    # noisy interaction family cannot replace the whole chart.
    score_blend = {
        "base_axis": 0.16,
        "legacy_structure": 0.12,
        "high_dimensional_theory": 0.72,
    }
    raw_score = _clip(
        base_score * score_blend["base_axis"]
        + structural_score * score_blend["legacy_structure"]
        + high_dimensional_score * score_blend["high_dimensional_theory"]
        + expert_reconciliation_adjustment,
        12.0,
        96.0,
    )
    quality_gate = _apply_public_quality_evidence_gate(
        raw_score,
        theory_evaluation=theory_evaluation,
    )
    score = int(quality_gate["quality_score"])
    ordinary_pair_score, ordinary_pair_count = _ordinary_branch_pair_score(structure, contract)
    quality_span = 46.0 if score >= 50 else 38.0
    signed_quality = max(-1.0, min(1.0, (float(score) - 50.0) / quality_span))
    return {
        "score": score,
        "quality_score": score,
        "raw_quality_score": quality_gate["raw_quality_score"],
        "effect_strength": theory_evaluation.get("evidence_strength", 0.0),
        "signed_quality": round(signed_quality, 3),
        "risk_intensity": 100 - score,
        "evidence_coverage": theory_evaluation.get("coverage_ratio", 0.0),
        "quality_gate_applied": quality_gate["quality_gate_applied"],
        "quality_gates": quality_gate["quality_gates"],
        "support_evidence_count": quality_gate["support_evidence_count"],
        "pressure_evidence_count": quality_gate["pressure_evidence_count"],
        "counter_evidence_count": quality_gate["counter_evidence_count"],
        "critical_pressure_count": quality_gate["critical_pressure_count"],
        "unresolved_critical_pressure_count": quality_gate[
            "unresolved_critical_pressure_count"
        ],
        "contract_grade": _contract_grade(contract),
        "contract_applied": True,
        "role_fit_score": round(role_score, 2),
        "position_score": round(position_score, 2),
        "relation_score": round(relation_score, 2),
        "ordinary_branch_pair_score": round(ordinary_pair_score, 2),
        "ordinary_branch_pair_count": ordinary_pair_count,
        "ten_god_specificity_score": round(ten_god_score, 2),
        "spouse_star_score": round(spouse_score, 2) if spouse_score is not None else None,
        "chain_score": round(chain_score, 2),
        "structural_adjustment": round(structural_adjustment, 2),
        "position_reality_adjustment": round(position_reality_adjustment, 2),
        "ten_god_specificity_adjustment": round(ten_god_specificity_adjustment, 2),
        "chain_adjustment": round(chain_adjustment, 2),
        "theory_registry_version": theory_evaluation.get("registry_version"),
        "theory_contract_applied": bool(theory_evaluation.get("applied")),
        "theory_semantic_axis": theory_evaluation.get("semantic_axis"),
        "theory_score": theory_evaluation.get("theory_score"),
        "high_dimensional_score": round(high_dimensional_score, 2),
        "high_dimensional_quality": dict(
            theory_evaluation.get("high_dimensional_quality", {})
        ),
        "score_blend": score_blend,
        "score_blend_method": "month_gated_functional_system_theory_v4_relation_two_axis",
        "theory_adjustment": round(theory_adjustment, 2),
        "theory_system_contrast_quality": theory_evaluation.get(
            "system_contrast_quality"
        ),
        "theory_raw_evidence_count": int(theory_evaluation.get("raw_evidence_count", 0)),
        "theory_retained_source_count": int(
            theory_evaluation.get("retained_source_count", 0)
        ),
        "theory_source_retention_ratio": theory_evaluation.get(
            "source_retention_ratio"
        ),
        "theory_observed_signal_count": int(
            theory_evaluation.get("observed_signal_count", 0)
        ),
        "theory_applicable_signal_count": int(
            theory_evaluation.get("applicable_signal_count", 0)
        ),
        "theory_rejected_signal_count": int(
            theory_evaluation.get("rejected_signal_count", 0)
        ),
        "theory_signal_application_ratio": theory_evaluation.get(
            "signal_application_ratio"
        ),
        "theory_signal_treatment_ledger": list(
            theory_evaluation.get("signal_treatment_ledger", [])
        ),
        "theory_independent_family_count": int(
            theory_evaluation.get("independent_family_count", 0)
        ),
        "theory_correlation_cluster_count": int(
            theory_evaluation.get("correlation_cluster_count", 0)
        ),
        "theory_novel_family_count": int(theory_evaluation.get("novel_family_count", 0)),
        "theory_minimum_independent_families": int(
            theory_evaluation.get("minimum_independent_families", 0)
        ),
        "theory_coverage_ratio": theory_evaluation.get("coverage_ratio"),
        "theory_strong_support_count": int(
            theory_evaluation.get("strong_support_count", 0)
        ),
        "theory_strong_pressure_count": int(
            theory_evaluation.get("strong_pressure_count", 0)
        ),
        "theory_counter_count": int(theory_evaluation.get("counter_count", 0)),
        "theory_critical_support_count": int(
            theory_evaluation.get("critical_support_count", 0)
        ),
        "theory_critical_pressure_count": int(
            theory_evaluation.get("critical_pressure_count", 0)
        ),
        "theory_activation_count": int(
            theory_evaluation.get("activation_count", 0)
        ),
        "theory_missing_primary_layers": list(
            theory_evaluation.get("missing_primary_layers", [])
        ),
        "theory_support_only_scored": list(
            theory_evaluation.get("support_only_scored", [])
        ),
        "theory_planned_scored": list(theory_evaluation.get("planned_scored", [])),
        "theory_evidence_summary": list(
            theory_evaluation.get("evidence_summary", [])
        ),
        "theory_evidence_ledger": list(
            theory_evaluation.get("evidence_ledger", [])
        ),
        "theory_source_evidence_summary": list(
            theory_evaluation.get("source_evidence_ledger", [])
        )[:12],
        "theory_hierarchy_ledger": list(
            theory_evaluation.get("hierarchy_ledger", [])
        ),
        "structural_score": round(structural_score, 2),
        "pre_expert_structural_adjustment": round(pre_expert_structural_adjustment, 2),
        "expert_gate_score": round(expert_gate_score, 2),
        "expert_evidence_count": expert_evidence_count,
        "expert_reconciliation_adjustment": round(expert_reconciliation_adjustment, 2),
        "base_axis_score": round(base_score, 2),
        "support_groups": list(contract.support_groups),
        "pressure_groups": list(contract.pressure_groups),
        "focus_positions": list(contract.focus_positions),
        "relation_positions": list(contract.relation_positions),
    }


def natal_metric_contract_audit(metric_keys: list[str]) -> dict[str, Any]:
    signature_counts: dict[tuple[tuple[str, ...], ...], int] = {}
    for key in metric_keys:
        signature = _contract_signature(NATAL_METRIC_CONTRACTS.get(key))
        if signature:
            signature_counts[signature] = signature_counts.get(signature, 0) + 1
    rows = []
    for key in metric_keys:
        contract = NATAL_METRIC_CONTRACTS.get(key)
        signature = _contract_signature(contract)
        quality_checks = {
            "explicit_contract": contract is not None,
            "role_groups_declared": bool(contract and (contract.support_groups or contract.pressure_groups)),
            "position_relevance_declared": bool(contract and contract.focus_positions),
            "branch_relation_scope_declared": bool(contract and contract.relation_positions),
            "exact_ten_god_distinction": bool(
                contract and (contract.support_ten_gods or contract.pressure_ten_gods)
            ),
            "independent_signature": bool(signature and signature_counts.get(signature, 0) == 1),
        }
        rows.append(
            {
                "key": key,
                "grade": _contract_grade(contract),
                "coverage_grade": _contract_grade(contract),
                "explicit": contract is not None,
                "support_groups": list(contract.support_groups) if contract else [],
                "focus_positions": list(contract.focus_positions) if contract else [],
                "relation_positions": list(contract.relation_positions) if contract else [],
                "quality_checks": quality_checks,
            }
        )
    grade_order = {"D": 0, "C": 1, "B": 2, "B+": 3, "A": 4}
    minimum_grade = min(
        (row["grade"] for row in rows),
        key=lambda grade: grade_order.get(grade, -1),
        default="D",
    )
    return {
        "metrics": rows,
        "minimum_grade": minimum_grade,
        "missing": [row["key"] for row in rows if not row["explicit"]],
        "duplicate_signatures": [
            row["key"]
            for row in rows
            if not row["quality_checks"]["independent_signature"]
        ],
        "below_b": [
            row["key"]
            for row in rows
            if grade_order.get(row["grade"], -1) < grade_order["B"]
        ],
    }
