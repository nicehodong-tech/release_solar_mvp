"""Expert priority adjudication for deterministic saju analysis.

This layer does not rebuild the birth chart. It reads the already computed
month command, pattern, element, ten-god, position, relation, and flow signals,
then decides which classical judgment should lead the product output.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_METADATA,
    DOMAIN_ORDER,
    ELEMENTS,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .models import (
    ChartStructure,
    ClassicalConditionEntry,
    Confidence,
    Domain,
    EventPacket,
    ExpertDomainProjection,
    ExpertPriorityAdjudication,
    ExpertTrace,
    FlowSignal,
    PatternViabilityDecision,
    UsefulElementDecision,
)
from .patterns import REGULAR_PATTERN_BY_TEN_GOD, REGULAR_PATTERN_NEED_RULES
from .ten_gods import ten_god_for


EXPERT_ADJUDICATION_VERSION = "expert_priority_adjudication_v1"

EXPERT_PRIORITY_TYPES = (
    "climate_regulation",
    "capacity_balance",
    "illness_medicine",
    "pattern_support",
    "passage_or_mediation",
    "expression_or_output_channel",
    "wealth_activation",
    "authority_or_position",
    "resource_protection",
    "flow_activation",
)

PATTERN_VIABILITY_STATUSES = ("established", "conditional", "weak", "broken", "not_applicable")

EXPERT_ADJUSTMENT_LIMITS = {
    "opportunity": (0, 12),
    "risk": (-6, 18),
    "change": (0, 4),
    "probability": (-4, 10),
}

CLIMATE_NEEDS_BY_SEASON = {
    "winter": ["fire", "earth"],
    "late_winter": ["fire", "wood"],
    "spring": ["metal", "fire"],
    "late_spring": ["water", "metal"],
    "summer": ["water", "metal"],
    "late_summer": ["water", "wood"],
    "autumn": ["fire", "water"],
    "late_autumn": ["fire", "wood"],
}

GROUP_TO_ROLE_TYPE = {
    "output": "expression_or_output_channel",
    "wealth": "wealth_activation",
    "officer": "authority_or_position",
    "resource": "resource_protection",
}

ROLE_TYPE_DOMAIN_LINKS = {
    "climate_regulation": ["career", "money", "marriage"],
    "capacity_balance": ["career", "money", "love", "marriage"],
    "illness_medicine": ["career", "money", "marriage"],
    "pattern_support": ["money", "career", "marriage"],
    "passage_or_mediation": ["career", "love", "marriage"],
    "expression_or_output_channel": ["money", "career", "love"],
    "wealth_activation": ["money", "career", "marriage"],
    "authority_or_position": ["career", "money", "marriage"],
    "resource_protection": ["career", "marriage", "love"],
    "flow_activation": ["money", "career", "love", "marriage"],
}

DOMAIN_PRIORITY_BASE = {
    "money": 70,
    "career": 70,
    "love": 64,
    "marriage": 64,
}

DOMAIN_POSITION_LINKS = {
    "money": {"month", "hour"},
    "career": {"month", "year"},
    "love": {"day", "hour"},
    "marriage": {"day", "month"},
}

DOMAIN_GROUP_LINKS = {
    "money": {"wealth", "output", "peer", "officer"},
    "career": {"officer", "resource", "output", "wealth"},
    "love": {"wealth", "output", "peer", "resource"},
    "marriage": {"officer", "wealth", "resource", "peer"},
}

DOMAIN_REALIZATION_PATH = {
    "money": {
        "opportunity": "수입·소유·정산이 실제 재물 결과로 이어지는 경로",
        "risk": "몫·계약·지출이 재물 결과를 흔드는 경로",
        "activation": "재성, 식상, 관성의 작용이 실제 거래와 보상으로 이어질 때",
        "sustain": "소유권과 정산 기준이 명확할 때",
        "loss": "재성을 감당하는 기반보다 재물 요구가 앞설 때",
        "conflict": "비겁이 재성을 건드리거나 관성이 정리하지 못할 때",
    },
    "career": {
        "opportunity": "역할·권한·평가가 사회적 성취로 이어지는 경로",
        "risk": "책임과 권한의 균형이 무너져 직업 부담으로 바뀌는 경로",
        "activation": "관성, 인성, 식상의 작용이 직책과 실무로 이어질 때",
        "sustain": "맡은 역할과 결정권이 함께 주어질 때",
        "loss": "책임은 커지는데 처리 기반이 약할 때",
        "conflict": "상관견관, 관살혼잡, 비겁과 관성의 충돌이 커질 때",
    },
    "love": {
        "opportunity": "호감·표현·접촉이 실제 관계로 이어지는 경로",
        "risk": "감정 표현과 기대치가 어긋나 관계 부담으로 바뀌는 경로",
        "activation": "일지, 식상, 재관, 합충이 인연 자리를 움직일 때",
        "sustain": "감정 표현과 관계 책임이 같은 방향으로 갈 때",
        "loss": "표현은 생기지만 안정시키는 힘이 약할 때",
        "conflict": "일지 충형파해나 재관의 부담이 가까운 관계에 닿을 때",
    },
    "marriage": {
        "opportunity": "배우자 자리와 생활 책임이 장기 관계로 이어지는 경로",
        "risk": "생활 기준과 책임 분담이 결혼 안정성을 흔드는 경로",
        "activation": "일지, 관성, 재성, 인성이 배우자·가정 영역을 움직일 때",
        "sustain": "관계의 책임과 생활 기준이 함께 잡힐 때",
        "loss": "감정은 있으나 생활 조건과 책임이 엇갈릴 때",
        "conflict": "일지와 월지의 충형파해가 배우자 자리와 현실 조건을 흔들 때",
    },
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _confidence_from_score(score: int) -> Confidence:
    if score >= 82:
        return "high"
    if score >= 70:
        return "medium_high"
    if score >= 55:
        return "medium"
    if score >= 42:
        return "low"
    return "restricted"


def _clip(value: int) -> int:
    return max(0, min(100, value))


def _bounded_adjusted_score(raw_score: int, adjusted_score: int, metric: str) -> int:
    minimum, maximum = EXPERT_ADJUSTMENT_LIMITS[metric]
    delta = adjusted_score - raw_score
    if delta < minimum:
        return _clip(raw_score + minimum)
    if delta > maximum:
        delta = maximum
    if delta > 0:
        remaining_room = max(0, 100 - raw_score)
        delta = min(delta, max(1, round(remaining_room * 0.72)))
    return _clip(raw_score + delta)


def _group_element(day_element: str, group: str) -> str:
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
    return ""


def _groups_from_ten_gods(ten_gods: list[str]) -> list[str]:
    return _unique([TEN_GOD_GROUPS.get(item, "") for item in ten_gods])


def build_classical_condition_matrix() -> dict[str, ClassicalConditionEntry]:
    matrix: dict[str, ClassicalConditionEntry] = {}
    for day_stem in STEM_METADATA:
        for month_branch in BRANCH_METADATA:
            entry = classical_condition_entry(day_stem, month_branch)
            matrix[f"{day_stem}:{month_branch}"] = entry
    return matrix


def classical_condition_entry(day_stem: str, month_branch: str) -> ClassicalConditionEntry:
    if day_stem not in STEM_METADATA:
        raise ValueError(f"Unsupported day_stem: {day_stem}")
    if month_branch not in BRANCH_METADATA:
        raise ValueError(f"Unsupported month_branch: {month_branch}")

    day_element = STEM_METADATA[day_stem]["element"]
    month_element = BRANCH_METADATA[month_branch]["element"]
    season_label = BRANCH_METADATA[month_branch]["season"]
    month_command_stem = BRANCH_HIDDEN_STEMS[month_branch][0][0]
    month_command_ten_god = ten_god_for(day_stem, month_command_stem)
    month_command_group = TEN_GOD_GROUPS.get(month_command_ten_god, "")
    regular_pattern = REGULAR_PATTERN_BY_TEN_GOD.get(month_command_ten_god, "")
    rules = REGULAR_PATTERN_NEED_RULES.get(month_command_ten_god, {})
    pattern_support_groups = _unique([str(item[0]) for item in rules.get("support", ())])
    pattern_caution_groups = _unique([str(item[0]) for item in rules.get("caution", ())])
    climate_need_elements = list(CLIMATE_NEEDS_BY_SEASON.get(season_label, []))

    capacity_need_groups = ["peer", "resource"] if month_command_group in {"wealth", "officer", "output"} else []
    if month_element == day_element:
        capacity_need_groups = ["output", "wealth", "officer"]

    review_status = "review_ready"
    confidence_score = 70
    if season_label.startswith("late_"):
        review_status = "needs_review"
        confidence_score -= 8
    if not regular_pattern:
        review_status = "needs_review"
        confidence_score -= 6

    basis_codes = [
        f"classical_condition:{day_stem}:{month_branch}",
        f"month_command:{month_command_ten_god}",
        f"season:{season_label}",
    ]
    if climate_need_elements:
        basis_codes.append("climate_need_by_month_branch")
    if pattern_support_groups:
        basis_codes.append("regular_pattern_need_rules")

    priority_order = [
        "birth_confidence",
        "month_command",
        "season_climate",
        "day_master_capacity",
        "pattern_viability",
        "illness_medicine",
        "position_reality",
        "branch_relations",
        "flow_activation",
        "past_event_calibration",
    ]
    return ClassicalConditionEntry(
        day_stem=day_stem,
        month_branch=month_branch,
        day_element=day_element,
        month_element=month_element,
        season_label=season_label,
        month_command_stem=month_command_stem,
        month_command_ten_god=month_command_ten_god,
        month_command_group=month_command_group,
        regular_pattern=regular_pattern,
        climate_need_elements=climate_need_elements,
        capacity_need_groups=capacity_need_groups,
        pattern_support_groups=pattern_support_groups,
        pattern_caution_groups=pattern_caution_groups,
        priority_order=priority_order,
        review_status=review_status,
        confidence=_confidence_from_score(confidence_score),
        strong_conclusion_allowed=review_status != "needs_review",
        basis_codes=basis_codes,
        counter_signals=[] if review_status == "review_ready" else ["late_season_or_unsettled_pattern_requires_review"],
    )


def classify_pattern_viability(
    *,
    score: int,
    formation_state: str,
    clarity_state: str,
    rooted: bool,
    protruded: bool,
    support_count: int,
    burden_count: int,
) -> str:
    if score <= 0:
        return "not_applicable"
    if burden_count >= support_count + 2 and clarity_state in {"clouded_by_month_pressure", "mixed_success_and_pressure"}:
        return "broken"
    if score >= 78 and rooted and protruded and formation_state in {"properly_formed", "formed_with_conditions"}:
        return "established"
    conditional_states = {
        "properly_formed",
        "formed_with_conditions",
        "partially_formed",
        "latent_but_usable",
    }
    if score >= 62 and (rooted or protruded) and formation_state in conditional_states:
        return "conditional"
    if score >= 42:
        return "weak"
    return "broken"


def _observed_pattern_groups(
    structure: ChartStructure,
    groups: list[str],
    *,
    signal: str,
) -> list[str]:
    observed: list[str] = []
    governance = structure.month_governance_profile
    for group in groups:
        role_fit = governance.role_fits.get(group)
        if role_fit is None:
            continue
        element_fit = governance.element_fits.get(role_fit.element)
        reality_score = int(getattr(element_fit, "reality_score", 0) or 0)
        group_score = float(structure.ten_god_profile.group_scores.get(group, 0.0) or 0.0)
        if reality_score <= 0 and group_score <= 0:
            continue
        action_score = role_fit.support_score if signal == "support" else role_fit.pressure_score
        if action_score > 0:
            observed.append(group)
    return _unique(observed)


def build_pattern_viability_decisions(structure: ChartStructure) -> list[PatternViabilityDecision]:
    decisions: list[PatternViabilityDecision] = []
    profile = structure.gyeokguk_profile
    for candidate in profile.candidates:
        support_groups = _observed_pattern_groups(
            structure,
            list(candidate.support_roles),
            signal="support",
        )
        burden_groups = _observed_pattern_groups(
            structure,
            list(candidate.burden_roles),
            signal="pressure",
        )
        decisive: list[str] = []
        if candidate.rooted:
            decisive.append("rooted")
        if candidate.protruded:
            decisive.append("protruded")
        if candidate.month_authority:
            decisive.append(candidate.month_authority)
        decisive.extend(f"support_present:{group}" for group in support_groups)
        decisive.extend(f"burden_present:{group}" for group in burden_groups)
        status = classify_pattern_viability(
            score=candidate.score,
            formation_state=candidate.formation_state,
            clarity_state=candidate.clarity_state,
            rooted=candidate.rooted,
            protruded=candidate.protruded,
            support_count=len(support_groups),
            burden_count=len(burden_groups),
        )
        decisions.append(
            PatternViabilityDecision(
                pattern=candidate.pattern,
                pattern_ten_god=candidate.source_ten_god,
                pattern_group=candidate.source_group,
                status=status,
                score=candidate.score,
                confidence=candidate.confidence,
                support_groups=support_groups,
                burden_groups=burden_groups,
                decisive_factors=_unique(decisive),
                basis_codes=list(candidate.basis_codes),
                counter_signals=list(candidate.counter_signals),
            )
        )

    if not decisions:
        decisions.append(
            PatternViabilityDecision(
                pattern=profile.primary_pattern or "unknown",
                pattern_ten_god=profile.primary_ten_god,
                pattern_group=profile.primary_group,
                status="not_applicable",
                score=0,
                confidence="restricted",
                support_groups=[],
                burden_groups=[],
                decisive_factors=[],
                basis_codes=["pattern_viability:no_candidate"],
                counter_signals=["pattern_viability:not_applicable"],
            )
        )
    decisions.sort(key=lambda item: (PATTERN_VIABILITY_STATUSES.index(item.status), -item.score))
    return decisions


def _domain_links_for_role(role_type: str) -> list[str]:
    return list(ROLE_TYPE_DOMAIN_LINKS.get(role_type, DOMAIN_ORDER))


def _append_decision(
    decisions: list[UsefulElementDecision],
    *,
    element: str,
    role_type: str,
    role_group: str,
    priority: int,
    confidence: Confidence,
    action_state: str,
    basis_codes: list[str],
    counter_signals: list[str] | None = None,
) -> None:
    if not element or element not in ELEMENTS:
        return
    decisions.append(
        UsefulElementDecision(
            element=element,
            role_type=role_type,
            role_group=role_group,
            priority=priority,
            confidence=confidence,
            action_state=action_state,
            domain_links=_domain_links_for_role(role_type),
            basis_codes=basis_codes,
            counter_signals=counter_signals or [],
        )
    )


def build_useful_element_decisions(
    chart: BirthChartResult,
    structure: ChartStructure,
    flow_signals: list[FlowSignal],
    condition: ClassicalConditionEntry,
    pattern_decisions: list[PatternViabilityDecision],
) -> list[UsefulElementDecision]:
    del chart
    decisions: list[UsefulElementDecision] = []
    element_profile = structure.element_profile
    day_element = structure.day_master_element
    useful_elements = set(element_profile.useful_elements)
    climate_elements = _unique(list(element_profile.climate_needs))

    for element in climate_elements:
        score_state = element_profile.scores.get(element)
        state = score_state.state if score_state is not None else "absent"
        if state in {"absent", "weak"}:
            priority = 92
            action_state = "needed"
            confidence: Confidence = "medium_high"
        elif state == "balanced":
            priority = 86
            action_state = "needed"
            confidence = "medium_high"
        else:
            priority = 76
            action_state = "supportive"
            confidence = "medium"
        _append_decision(
            decisions,
            element=element,
            role_type="climate_regulation",
            role_group="climate",
            priority=priority,
            confidence=confidence,
            action_state=action_state,
            basis_codes=[
                f"measured_climate_need:{element}",
                f"temperature:{element_profile.temperature_balance}",
                f"moisture:{element_profile.moisture_balance}",
                f"season:{condition.season_label}",
            ],
        )

    strength = element_profile.day_master_strength
    if strength in {"weak", "very_weak"}:
        for group in ("resource", "peer"):
            _append_decision(
                decisions,
                element=_group_element(day_element, group),
                role_type="capacity_balance",
                role_group=group,
                priority=88 if strength == "very_weak" else 80,
                confidence="medium_high",
                action_state="capacity_support",
                basis_codes=[f"day_master_strength:{strength}", f"capacity_need:{group}"],
            )
    elif strength in {"strong", "very_strong"}:
        for group in ("output", "wealth", "officer"):
            _append_decision(
                decisions,
                element=_group_element(day_element, group),
                role_type=GROUP_TO_ROLE_TYPE.get(group, "capacity_balance"),
                role_group=group,
                priority=84 if strength == "very_strong" else 76,
                confidence="medium",
                action_state="excess_release",
                basis_codes=[f"day_master_strength:{strength}", f"release_need:{group}"],
            )

    for item in element_profile.illness_medicine:
        medicine_elements = [
            str(item.get("medicine_element") or item.get("element") or item.get("needed_element") or ""),
            *[str(value) for value in item.get("medicine", []) if value],
            *[str(value) for value in item.get("medicine_elements", []) if value],
        ]
        for element in _unique(medicine_elements):
            _append_decision(
                decisions,
                element=element,
                role_type="illness_medicine",
                role_group="medicine",
                priority=90,
                confidence="medium_high",
                action_state="medicine",
                basis_codes=["illness_medicine", f"medicine:{element}"],
                counter_signals=[str(item.get("illness") or item.get("target") or "")],
            )

    lead_pattern = pattern_decisions[0] if pattern_decisions else None
    if lead_pattern is not None and lead_pattern.status in {"established", "conditional", "weak"}:
        for group in lead_pattern.support_groups:
            _append_decision(
                decisions,
                element=_group_element(day_element, group),
                role_type=GROUP_TO_ROLE_TYPE.get(group, "pattern_support"),
                role_group=group,
                priority=86 if lead_pattern.status == "established" else 76,
                confidence=lead_pattern.confidence,
                action_state=f"pattern_{lead_pattern.status}",
                basis_codes=[f"pattern_support:{lead_pattern.pattern}", f"support_group:{group}"],
                counter_signals=list(lead_pattern.counter_signals),
            )

    if structure.cycle_regulation_profile.get("circulation_level") in {"blocked", "weak"} or element_profile.circulation_level in {"blocked", "weak"}:
        bridge = climate_elements[0] if climate_elements else (element_profile.useful_elements[0] if element_profile.useful_elements else "")
        _append_decision(
            decisions,
            element=bridge,
            role_type="passage_or_mediation",
            role_group="mediation",
            priority=74,
            confidence="medium",
            action_state="mediation_needed",
            basis_codes=["cycle_regulation:mediation_needed"],
        )

    activated_useful = _unique(
        [
            element
            for flow in flow_signals
            for element in flow.activated_elements
            if element in useful_elements or element in climate_elements
        ]
    )
    for element in activated_useful:
        _append_decision(
            decisions,
            element=element,
            role_type="flow_activation",
            role_group="flow",
            priority=72,
            confidence="medium",
            action_state="activated_by_flow",
            basis_codes=[f"flow_activates_useful_element:{element}"],
        )

    deduped: dict[tuple[str, str, str], UsefulElementDecision] = {}
    for decision in decisions:
        key = (decision.element, decision.role_type, decision.role_group)
        previous = deduped.get(key)
        if previous is None or decision.priority > previous.priority:
            deduped[key] = decision
    return sorted(deduped.values(), key=lambda item: item.priority, reverse=True)[:16]


def _relation_domain_score(structure: ChartStructure, domain: Domain) -> tuple[int, int, list[str], list[str]]:
    opportunity = 0
    risk = 0
    basis: list[str] = []
    counter: list[str] = []
    target_positions = DOMAIN_POSITION_LINKS[domain]
    for relation in structure.branch_interactions:
        positions = set(relation.positions)
        if not positions.intersection(target_positions):
            continue
        if relation.relation_type in {
            "six_combine",
            "three_harmony",
            "three_harmony_half",
            "three_meeting",
        }:
            opportunity += 3
            basis.append(f"expert_relation:{domain}:{relation.relation_type}")
        elif relation.relation_type in {"clash", "punishment", "harm", "break"}:
            risk += 4 if relation.intensity in {"strong", "high"} else 3
            counter.append(f"expert_relation:{domain}:{relation.relation_type}")
    return opportunity, risk, basis, counter


def _group_presence(structure: ChartStructure, group: str) -> float:
    return float(structure.ten_god_profile.group_scores.get(group, 0.0))


def _domain_projection(
    domain: Domain,
    structure: ChartStructure,
    flow_signals: list[FlowSignal],
    useful_decisions: list[UsefulElementDecision],
    pattern_decisions: list[PatternViabilityDecision],
    condition: ClassicalConditionEntry,
) -> ExpertDomainProjection:
    base = DOMAIN_REALIZATION_PATH[domain]
    useful_for_domain = [item for item in useful_decisions if domain in item.domain_links]
    realized_states = {"pattern_established", "pattern_conditional", "activated_by_flow"}
    realized_for_domain = [item for item in useful_for_domain if item.action_state in realized_states]
    required_for_domain = [item for item in useful_for_domain if item.action_state not in realized_states]
    lead_pattern = pattern_decisions[0] if pattern_decisions else None
    domain_groups = DOMAIN_GROUP_LINKS[domain]
    group_hit = [group for group in domain_groups if _group_presence(structure, group) >= 0.85]
    relation_opp, relation_risk, relation_basis, relation_counter = _relation_domain_score(structure, domain)
    priority_variation = 0

    opportunity_delta = min(5, len(realized_for_domain[:3]) * 2) + relation_opp
    risk_delta = relation_risk + min(3, len({item.role_type for item in required_for_domain}))
    change_delta = 1 if relation_opp or relation_risk else 0
    probability_delta = min(4, len(group_hit) + len(realized_for_domain[:2]))
    basis = list(relation_basis)
    counter = list(relation_counter)

    if group_hit:
        basis.extend(f"expert_domain_group:{domain}:{group}" for group in group_hit)
    if realized_for_domain:
        basis.extend(f"expert_useful_realized:{item.role_type}:{item.element}" for item in realized_for_domain[:4])
    if required_for_domain:
        counter.extend(f"expert_requirement:{item.role_type}:{item.element}" for item in required_for_domain[:4])
    if lead_pattern is not None:
        if lead_pattern.status in {"established", "conditional"}:
            opportunity_delta += 2
            probability_delta += 1
            basis.append(f"expert_pattern_viability:{lead_pattern.status}")
        elif lead_pattern.status in {"weak", "broken"}:
            risk_delta += 2
            counter.append(f"expert_pattern_viability:{lead_pattern.status}")

    if domain == "money":
        priority_variation += round(_group_presence(structure, "wealth") * 2)
        priority_variation += round(_group_presence(structure, "output"))
        priority_variation -= round(_group_presence(structure, "peer") * 0.8)
        if _group_presence(structure, "wealth") >= 1.0:
            opportunity_delta += 3
            basis.append("expert_money:wealth_present")
        if _group_presence(structure, "output") >= 0.8 and _group_presence(structure, "wealth") >= 0.8:
            opportunity_delta += 2
            basis.append("expert_money:output_to_wealth_present")
        if structure.element_profile.day_master_strength in {"weak", "very_weak"} and _group_presence(structure, "wealth") >= 1.0:
            risk_delta += 4
            counter.append("expert_money:weak_day_master_handles_wealth")
        if _group_presence(structure, "peer") >= 1.0 and _group_presence(structure, "wealth") >= 0.8:
            risk_delta += 4
            counter.append("expert_money:peer_competes_wealth")
        if _group_presence(structure, "officer") >= 0.8 and _group_presence(structure, "peer") >= 0.8:
            risk_delta = max(0, risk_delta - 2)
            basis.append("expert_money:officer_orders_peer")
    elif domain == "career":
        priority_variation += round(_group_presence(structure, "officer") * 2)
        priority_variation += round(_group_presence(structure, "resource"))
        priority_variation += round(_group_presence(structure, "output") * 0.5)
        if _group_presence(structure, "officer") >= 0.85:
            opportunity_delta += 3
            basis.append("expert_career:officer_present")
        if _group_presence(structure, "resource") >= 0.85 and _group_presence(structure, "officer") >= 0.7:
            opportunity_delta += 2
            basis.append("expert_career:officer_resource_sequence")
        if _group_presence(structure, "output") >= 1.1 and _group_presence(structure, "officer") >= 0.8:
            risk_delta += 3
            counter.append("expert_career:output_challenges_officer")
    elif domain == "love":
        priority_variation += round(_group_presence(structure, "output") * 2)
        priority_variation += round(_group_presence(structure, "wealth") * 0.8)
        priority_variation -= relation_risk
        if structure.position_signals.get("day"):
            basis.append("expert_love:day_branch_checked")
            probability_delta += 1
        if _group_presence(structure, "output") >= 0.9:
            opportunity_delta += 2
            basis.append("expert_love:expression_visible")
        if relation_risk:
            risk_delta += 1
            counter.append("expert_love:partner_palace_relation_pressure")
    elif domain == "marriage":
        priority_variation += round(_group_presence(structure, "officer") * 2)
        priority_variation += round(_group_presence(structure, "wealth") * 1.5)
        priority_variation += round(_group_presence(structure, "resource") * 0.8)
        priority_variation -= round(_group_presence(structure, "peer") * 0.8)
        priority_variation -= relation_risk
        day_signal = structure.position_signals.get("day")
        if day_signal is not None:
            if day_signal.branch_main_ten_god in {"jeong_gwan", "pyeon_gwan", "jeong_jae", "pyeon_jae"}:
                priority_variation += 3
                basis.append("expert_marriage:spouse_star_on_day_branch")
            if len(day_signal.hidden_ten_gods) >= 2:
                priority_variation += 1
                basis.append("expert_marriage:spouse_palace_hidden_roles")
        if structure.position_signals.get("day"):
            basis.append("expert_marriage:spouse_palace_checked")
            probability_delta += 1
        if _group_presence(structure, "officer") >= 0.8 or _group_presence(structure, "wealth") >= 0.8:
            opportunity_delta += 2
            basis.append("expert_marriage:spouse_star_present")
        if relation_risk:
            risk_delta += 2
            counter.append("expert_marriage:spouse_palace_relation_pressure")

    timing_target_elements = _unique(
        [
            item.element
            for item in useful_decisions
            if item.role_type != "flow_activation"
        ]
    )
    flow_useful_years = [
        str(flow.year)
        for flow in flow_signals
        if any(element in flow.activated_elements for element in timing_target_elements)
    ][:4]
    timing_condition = "대운·세운이 필요한 오행이나 격국 보조 신호를 건드릴 때"
    if flow_useful_years:
        timing_condition = f"{', '.join(flow_useful_years)}년처럼 필요한 오행이 운에서 드러날 때"
        basis.append("expert_flow:useful_element_years_detected")

    score_adjustments = {
        "opportunity": min(6, opportunity_delta),
        "risk": min(8, max(0, risk_delta)),
        "change": min(3, change_delta),
        "probability": min(5, probability_delta),
    }
    priority = (
        DOMAIN_PRIORITY_BASE[domain]
        + score_adjustments["opportunity"]
        + score_adjustments["probability"]
        - score_adjustments["risk"]
        + priority_variation
    )
    confidence_score = 62 + len(basis) * 2 - len(counter)
    if condition.review_status == "needs_review":
        confidence_score -= 5
        counter.append("expert_condition:needs_review")

    return ExpertDomainProjection(
        domain=domain,
        priority=max(35, min(96, priority)),
        confidence=_confidence_from_score(max(35, min(96, confidence_score))),
        opportunity_path=base["opportunity"],
        risk_path=base["risk"],
        activation_condition=base["activation"],
        sustaining_condition=base["sustain"],
        loss_condition=base["loss"],
        conflict_condition=base["conflict"],
        timing_condition=timing_condition,
        score_adjustments=score_adjustments,
        basis_codes=_unique(basis),
        counter_signals=_unique(counter),
    )


def _expert_summary(
    condition: ClassicalConditionEntry,
    useful: list[UsefulElementDecision],
    patterns: list[PatternViabilityDecision],
    projections: dict[str, ExpertDomainProjection],
) -> dict[str, Any]:
    lead_pattern = patterns[0] if patterns else None
    lead_useful = useful[:5]
    ordered_domains = sorted(projections.values(), key=lambda item: item.priority, reverse=True)
    return {
        "version": EXPERT_ADJUDICATION_VERSION,
        "month_anchor": {
            "day_stem": condition.day_stem,
            "month_branch": condition.month_branch,
            "month_command_ten_god": condition.month_command_ten_god,
            "month_command_group": condition.month_command_group,
            "regular_pattern": condition.regular_pattern,
            "review_status": condition.review_status,
        },
        "pattern_viability": asdict(lead_pattern) if lead_pattern is not None else {},
        "lead_useful_decisions": [asdict(item) for item in lead_useful],
        "domain_priority": [
            {"domain": item.domain, "priority": item.priority, "confidence": item.confidence}
            for item in ordered_domains
        ],
    }


def build_expert_priority_adjudication(
    chart: BirthChartResult,
    structure: ChartStructure,
    flow_signals: list[FlowSignal],
) -> ExpertPriorityAdjudication:
    condition = classical_condition_entry(structure.day_master_stem, structure.month_branch)
    patterns = build_pattern_viability_decisions(structure)
    useful = build_useful_element_decisions(chart, structure, flow_signals, condition, patterns)
    projections = {
        domain: _domain_projection(domain, structure, flow_signals, useful, patterns, condition)
        for domain in DOMAIN_ORDER
    }

    gate_results = {
        "gate0_birth_confidence": {
            "boundary_sensitive": bool(getattr(chart, "boundary_sensitive", False)),
            "known_birth_time": bool(getattr(chart, "birth_time_known", True)),
        },
        "gate1_month_climate": asdict(condition),
        "gate2_day_master_capacity": {
            "day_master_strength": structure.element_profile.day_master_strength,
            "day_master_strength_score": structure.element_profile.day_master_strength_score,
        },
        "gate3_pattern_viability": [asdict(item) for item in patterns],
        "gate4_illness_mediation": [
            asdict(item)
            for item in useful
            if item.role_type in {"illness_medicine", "passage_or_mediation", "climate_regulation"}
        ],
        "gate5_position_reality": {
            key: {
                "stem_ten_god": signal.stem_ten_god,
                "branch_main_ten_god": signal.branch_main_ten_god,
                "hidden_ten_gods": list(signal.hidden_ten_gods),
                "protruded_hidden_stems": list(signal.protruded_hidden_stems),
            }
            for key, signal in structure.position_signals.items()
        },
        "gate6_relations": [asdict(item) for item in structure.branch_interactions],
        "gate7_flow_activation": [
            {
                "year": flow.year,
                "activated_elements": list(flow.activated_elements),
                "basis_codes": list(flow.basis_codes),
                "counter_signals": list(flow.counter_signals),
            }
            for flow in flow_signals[:12]
        ],
        "gate8_past_event_calibration": "not_applied_in_expert_layer",
    }
    selected_primary_basis = _unique(
        condition.basis_codes
        + [code for pattern in patterns[:2] for code in pattern.basis_codes[:4]]
        + [code for item in useful[:5] for code in item.basis_codes[:3]]
    )
    promoted_signals = _unique(
        [f"{item.role_type}:{item.element}" for item in useful[:8]]
        + [f"{domain}:{projection.priority}" for domain, projection in projections.items()]
    )
    suppressed_signals = _unique(condition.counter_signals + [code for item in patterns for code in item.counter_signals[:3]])
    trace = ExpertTrace(
        priority_order=list(condition.priority_order),
        selected_primary_basis=selected_primary_basis,
        promoted_signals=promoted_signals,
        suppressed_signals=suppressed_signals,
        gate_results=gate_results,
        warnings=[] if condition.strong_conclusion_allowed else ["classical_condition_requires_review"],
    )
    summary = _expert_summary(condition, useful, patterns, projections)
    return ExpertPriorityAdjudication(
        version=EXPERT_ADJUDICATION_VERSION,
        classical_condition=condition,
        useful_element_decisions=useful,
        pattern_viability_decisions=patterns,
        domain_projections=projections,
        expert_trace=trace,
        summary=summary,
        basis_codes=selected_primary_basis,
        counter_signals=suppressed_signals,
    )


def _raw_flow_scores(flow_signals: list[FlowSignal]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (flow.period_label, domain): flow.domain_scores[domain]
        for flow in flow_signals
        for domain in DOMAIN_ORDER
    }


def apply_expert_projection_to_packets(
    packets: list[EventPacket],
    flow_signals: list[FlowSignal],
    adjudication: ExpertPriorityAdjudication,
) -> list[EventPacket]:
    raw_scores = _raw_flow_scores(flow_signals)
    updated_packets: list[EventPacket] = []
    for packet in packets:
        projection = adjudication.domain_projections.get(packet.domain)
        raw = raw_scores.get((packet.period_label, packet.domain), {})
        if projection is None or not raw:
            updated_packets.append(packet)
            continue
        adjustments = projection.score_adjustments
        opportunity = _bounded_adjusted_score(
            int(raw.get("opportunity", packet.opportunity_score)),
            packet.opportunity_score + adjustments.get("opportunity", 0),
            "opportunity",
        )
        risk = _bounded_adjusted_score(
            int(raw.get("risk", packet.risk_score)),
            packet.risk_score + adjustments.get("risk", 0),
            "risk",
        )
        change = _bounded_adjusted_score(
            int(raw.get("change", packet.change_score)),
            packet.change_score + adjustments.get("change", 0),
            "change",
        )
        probability = _bounded_adjusted_score(
            int(raw.get("probability", packet.event_probability_score)),
            packet.event_probability_score + adjustments.get("probability", 0),
            "probability",
        )
        summary = {
            "version": EXPERT_ADJUDICATION_VERSION,
            "domain": projection.domain,
            "priority": projection.priority,
            "confidence": projection.confidence,
            "opportunity_path": projection.opportunity_path,
            "risk_path": projection.risk_path,
            "activation_condition": projection.activation_condition,
            "sustaining_condition": projection.sustaining_condition,
            "loss_condition": projection.loss_condition,
            "conflict_condition": projection.conflict_condition,
            "timing_condition": projection.timing_condition,
            "score_adjustments": {
                "opportunity": opportunity - packet.opportunity_score,
                "risk": risk - packet.risk_score,
                "change": change - packet.change_score,
                "probability": probability - packet.event_probability_score,
            },
            "raw_flow_scores": {
                metric: int(raw.get(metric, getattr(packet, f"{metric}_score", 0)))
                for metric in ("opportunity", "risk", "change")
            }
            | {"probability": int(raw.get("probability", packet.event_probability_score))},
            "basis_codes": list(projection.basis_codes),
            "counter_signals": list(projection.counter_signals),
        }
        updated_packets.append(
            replace(
                packet,
                opportunity_score=opportunity,
                risk_score=risk,
                change_score=change,
                event_probability_score=probability,
                basis_codes=_unique(packet.basis_codes + projection.basis_codes + ["expert_projection_applied"]),
                counter_signals=_unique(packet.counter_signals + projection.counter_signals),
                expert_projection_summary=summary,
            )
        )
    return updated_packets


def expert_adjudication_payload(adjudication: ExpertPriorityAdjudication | None) -> dict[str, Any]:
    if adjudication is None:
        return {}
    return asdict(adjudication)
