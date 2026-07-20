"""Contextual synthesis for gyeokguk, month command, elements and climate.

This layer does not reinterpret the chart from scratch. It gathers the
gyeokguk action dictionaries, month-governance anchor, principle matrix, and
element/climate profile into one auditable payload.
"""

from __future__ import annotations

from typing import Any

from .constants import (
    DOMAIN_ORDER,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    STEM_METADATA,
)
from .element_combinations import GENERIC_RELATION_RULES, SPECIFIC_ELEMENT_SET_RULES, same_element_density_rule
from .stem_receptions import STEM_LABELS, STEM_ORDER, stem_reception_rule
from .ten_gods import ten_god_for


GYEOKGUK_CONTEXTUAL_VERSION = "gyeokguk_contextual_v1"

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")

ROLE_LABELS = {
    "peer": "비겁",
    "output": "식상",
    "wealth": "재성",
    "officer": "관성",
    "resource": "인성",
}

TEN_GOD_LABELS = {
    "bi_gyeon": "비견",
    "geob_jae": "겁재",
    "sik_sin": "식신",
    "sang_gwan": "상관",
    "pyeon_jae": "편재",
    "jeong_jae": "정재",
    "pyeon_gwan": "편관",
    "jeong_gwan": "정관",
    "pyeon_in": "편인",
    "jeong_in": "정인",
}

DOMAIN_LABELS = {
    "money": "재물",
    "career": "직업",
    "love": "연애",
    "relationship": "관계",
    "marriage": "결혼",
    "personality": "성향",
    "reputation": "명예",
    "luck_activation": "대운·세운",
}

PATTERN_LABELS = {
    "jianlu_peer_pattern": "건록격",
    "yangren_peer_pattern": "양인격",
    "friend_pattern": "건록격",
    "rob_wealth_pattern": "양인격",
    "eating_god_pattern": "식신격",
    "hurting_officer_pattern": "상관격",
    "indirect_wealth_pattern": "편재격",
    "direct_wealth_pattern": "정재격",
    "seven_killings_pattern": "편관격",
    "direct_officer_pattern": "정관격",
    "indirect_resource_pattern": "편인격",
    "direct_resource_pattern": "정인격",
}

MATERIALITY_RELATION_LABELS = {
    "eul_byeong_social_expansion": "을병 관계 확장",
    "wood_fire_expression_growth": "목화 표현 성장",
    "fire_earth_reputation_foundation": "화토 평판 축적",
    "earth_metal_system_asset": "토금 체계 자산화",
    "metal_water_analysis_distribution": "금수 분석 유통",
    "water_wood_learning_planning": "수목 학습 기획",
    "wood_earth_foundation_pressure": "목토 기반 압박",
    "fire_metal_refinement_pressure": "화금 검증 압박",
    "earth_water_cashflow_containment": "토수 현금 통제",
    "metal_wood_pruning_order": "금목 기준 정리",
    "water_fire_visibility_control": "수화 노출 조절",
    "wood_fire_earth_result_foundation": "목화토 결과 기반화",
    "fire_earth_metal_reputation_system": "화토금 평판 제도화",
    "earth_metal_water_asset_information": "토금수 자산 정보화",
    "metal_water_wood_research_planning": "금수목 분석 기획",
    "water_wood_fire_learning_expression": "수목화 학습 표현",
    "element_generation": "상생 배합",
    "element_control": "상극 조절",
    "same_element_density": "동일 오행 집중",
    "element_mixed": "복합 오행 배합",
}

SEASON_LABELS = {
    "spring": "봄",
    "summer": "여름",
    "autumn": "가을",
    "winter": "겨울",
    "late_winter": "늦겨울",
    "late_spring": "늦봄",
    "late_summer": "환절기",
    "late_autumn": "늦가을",
}

ELEMENT_STATUS_LABELS = {
    "useful": "필요한 오행",
    "caution": "과해지면 부담이 되는 오행",
    "dominant": "월령에서 강하게 드러난 오행",
    "weak": "발동 조건이 필요한 오행",
    "ordinary": "보조적으로 작용하는 오행",
}

ELEMENT_RELATION_LABELS = {
    "same": "월령과 같은 오행",
    "month_generates_pattern": "월령이 격국 작용을 생하는 관계",
    "pattern_generates_month": "격국 작용이 월령으로 설기되는 관계",
    "month_controls_pattern": "월령이 격국 작용을 제어하는 관계",
    "pattern_controls_month": "격국 작용이 월령을 제어하는 관계",
    "indirect": "직접 생극보다 배합으로 드러나는 관계",
}

TEMPERATURE_BALANCE_LABELS = {
    "cold": "한랭",
    "hot": "과열",
    "balanced": "온도 균형",
}

MOISTURE_BALANCE_LABELS = {
    "dry": "건조",
    "wet": "습중",
    "balanced": "건습 균형",
}

CLIMATE_ELEMENT_MEANINGS = {
    "wood": "성장성과 생동감",
    "fire": "온기와 표현력",
    "earth": "균형과 생활 기반",
    "metal": "정리와 기준",
    "water": "수분과 조절력",
}

CLIMATE_ELEMENT_DOMAINS = {
    "wood": ("career", "personality", "love"),
    "fire": ("reputation", "love", "career"),
    "earth": ("money", "marriage", "career"),
    "metal": ("career", "reputation", "money"),
    "water": ("career", "money", "personality"),
}

DOMAIN_TILT_BY_GROUP = {
    "peer": ("relationship", "money", "personality"),
    "output": ("career", "money", "love", "personality"),
    "wealth": ("money", "career", "marriage", "relationship"),
    "officer": ("career", "reputation", "marriage", "personality"),
    "resource": ("personality", "career", "relationship", "reputation"),
}

RECEPTION_DOMAIN_PRIORITY = {
    "peer": ("relationship", "money", "personality"),
    "output": ("career", "money", "love", "personality"),
    "wealth": ("money", "marriage", "career", "relationship"),
    "officer": ("career", "reputation", "marriage", "personality"),
    "resource": ("personality", "career", "reputation", "relationship"),
}

STEM_POSITION_LABELS = {
    "year": "연간",
    "month": "월간",
    "day": "일간",
    "hour": "시간",
}

BRANCH_POSITION_LABELS = {
    "year": "연지",
    "month": "월지",
    "day": "일지",
    "hour": "시지",
}

POSITION_GRADE_LABELS = {
    "month_position_reality": "월령 작동",
    "visible_stem_action": "천간 투출",
    "branch_main_reality": "지지 통근",
    "hidden_stem_latent": "지장간 잠복",
    "position_weak": "위치 약함",
    "position_not_evaluated": "위치 미평가",
}

BRANCH_RELATION_LABELS = {
    "six_combine": "육합",
    "three_harmony": "삼합",
    "half_harmony": "반합",
    "seasonal_combine": "방합",
    "clash": "충",
    "punishment": "형",
    "harm": "해",
    "break": "파",
}

BRANCH_RELATION_GRADE_LABELS = {
    "branch_relation_supports_actor": "지지 관계가 작용을 받침",
    "branch_relation_pressures_actor": "지지 관계가 작용을 압박",
    "branch_relation_supports_needed_actor": "필요 작용을 지지에서 받침",
    "branch_relation_pressures_needed_actor": "필요 작용이 지지에서 압박을 받음",
    "branch_relation_mixed_actor": "지지 관계가 혼재",
    "branch_relation_not_touching_actor": "지지 관계 접점 약함",
}

ACTION_SOURCE_LABELS = {
    "single": "격국별 단일 십신 작용",
    "dual": "격국별 이중 십신 조합",
}

ACTION_STATE_LABELS = {
    "support": "성격 보조",
    "burden": "부담 작용",
    "mixed": "혼합 작용",
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


def _limit(values: list[Any], limit: int) -> list[Any]:
    return list(values[: max(0, limit)])


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _nested_contexts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    children = [item for item in (value.get("first"), value.get("second")) if isinstance(item, dict)]
    if children:
        return children
    return [value]


def _position_summary(position_context: Any) -> dict[str, Any]:
    contexts = _nested_contexts(position_context)
    visible: list[str] = []
    branch_main: list[str] = []
    hidden: list[str] = []
    grades: list[str] = []
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    score_delta = 0
    for context in contexts:
        visible.extend(str(item) for item in _as_list(context.get("visible_positions")))
        branch_main.extend(str(item) for item in _as_list(context.get("branch_main_positions")))
        hidden.extend(str(item) for item in _as_list(context.get("hidden_positions")))
        grade = str(context.get("grade") or "")
        if grade:
            grades.append(grade)
        basis_codes.extend(str(item) for item in _as_list(context.get("basis_codes")))
        counter_signals.extend(str(item) for item in _as_list(context.get("counter_signals")))
        score_delta += int(context.get("score_delta") or 0)
    return {
        "visible_positions": _unique(visible),
        "visible_position_labels": _unique([STEM_POSITION_LABELS.get(item, item) for item in visible]),
        "root_positions": _unique(branch_main),
        "root_position_labels": _unique([BRANCH_POSITION_LABELS.get(item, item) for item in branch_main]),
        "hidden_positions": _unique(hidden),
        "hidden_position_labels": _unique([f"{BRANCH_POSITION_LABELS.get(item, item)} 지장간" for item in hidden]),
        "grades": _unique(grades),
        "grade_labels": _unique([POSITION_GRADE_LABELS.get(item, item) for item in grades]),
        "score_delta": score_delta,
        "basis_codes": _unique(basis_codes)[:8],
        "counter_signals": _unique(counter_signals)[:6],
    }


def _branch_relation_summary(branch_context: Any) -> dict[str, Any]:
    contexts = _nested_contexts(branch_context)
    relation_types: list[str] = []
    relation_position_labels: list[str] = []
    effect_elements: list[str] = []
    grades: list[str] = []
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    score_delta = 0
    for context in contexts:
        grade = str(context.get("grade") or "")
        if grade:
            grades.append(grade)
        basis_codes.extend(str(item) for item in _as_list(context.get("basis_codes")))
        counter_signals.extend(str(item) for item in _as_list(context.get("counter_signals")))
        score_delta += int(context.get("score_delta") or 0)
        for relation in _as_list(context.get("relations")):
            if not isinstance(relation, dict):
                continue
            relation_type = str(relation.get("relation_type") or "")
            if relation_type:
                relation_types.append(relation_type)
            positions = [BRANCH_POSITION_LABELS.get(str(item), str(item)) for item in _as_list(relation.get("positions"))]
            if positions:
                relation_position_labels.append("·".join(positions))
            effect = str(relation.get("effect_element") or "")
            if effect:
                effect_elements.append(effect)
    return {
        "relation_types": _unique(relation_types),
        "relation_type_labels": _unique([BRANCH_RELATION_LABELS.get(item, item) for item in relation_types]),
        "relation_position_labels": _unique(relation_position_labels)[:6],
        "effect_elements": _unique(effect_elements),
        "effect_element_labels": _unique([ELEMENT_LABELS.get(item, item) for item in effect_elements]),
        "grades": _unique(grades),
        "grade_labels": _unique([BRANCH_RELATION_GRADE_LABELS.get(item, item) for item in grades]),
        "score_delta": score_delta,
        "basis_codes": _unique(basis_codes)[:8],
        "counter_signals": _unique(counter_signals)[:6],
    }


def _role_element(day_master_element: str, group: str) -> str:
    if group == "peer":
        return day_master_element
    if group == "output":
        return ELEMENT_GENERATES.get(day_master_element, "")
    if group == "wealth":
        return ELEMENT_CONTROLS.get(day_master_element, "")
    if group == "officer":
        return ELEMENT_CONTROLLED_BY.get(day_master_element, "")
    if group == "resource":
        return ELEMENT_GENERATED_BY.get(day_master_element, "")
    return ""


def _grade_weight(grade: str) -> int:
    return {
        "dominant": 38,
        "strong": 30,
        "present": 22,
        "weak": 12,
        "trace": 6,
        "absent": 0,
    }.get(str(grade or ""), 0)


def _scope_weight(scope: str) -> int:
    return {
        "active_support": 32,
        "active_mixed": 24,
        "active_pressure": 28,
        "latent_reference": 12,
        "trace_reference": 6,
        "reference": 3,
    }.get(str(scope or ""), 0)


def _edge_salience(edge: dict[str, Any]) -> int:
    support = int(edge.get("support_score") or 0)
    pressure = int(edge.get("pressure_score") or 0)
    net = abs(int(edge.get("net_score") or 0))
    reality = int(edge.get("source_reality_score") or 0) + int(edge.get("target_reality_score") or 0)
    month_bonus = 12 if edge.get("touches_month_command") else 0
    return _scope_weight(str(edge.get("scope") or "")) + support + pressure + net + reality // 2 + month_bonus


def _edge_state(edge: dict[str, Any]) -> str:
    support = int(edge.get("support_score") or 0)
    pressure = int(edge.get("pressure_score") or 0)
    net = int(edge.get("net_score") or 0)
    scope = str(edge.get("scope") or "")
    if scope == "active_pressure" or pressure >= support + 8 or net <= -8:
        return "burden"
    if scope == "active_support" or support >= pressure + 8 or net >= 8:
        return "support"
    return "mixed"


def _compact_role_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_key": edge.get("edge_key"),
        "classical_name": edge.get("classical_name"),
        "relation": edge.get("relation"),
        "source_group": edge.get("source_group"),
        "source_label": edge.get("source_label"),
        "target_group": edge.get("target_group"),
        "target_label": edge.get("target_label"),
        "source_element": edge.get("source_element"),
        "source_element_label": ELEMENT_LABELS.get(str(edge.get("source_element") or ""), ""),
        "target_element": edge.get("target_element"),
        "target_element_label": ELEMENT_LABELS.get(str(edge.get("target_element") or ""), ""),
        "scope": edge.get("scope"),
        "state": _edge_state(edge),
        "month_fit_verdict": edge.get("month_fit_verdict"),
        "force_balance": edge.get("force_balance"),
        "force_effect": edge.get("force_effect"),
        "support_score": int(edge.get("support_score") or 0),
        "pressure_score": int(edge.get("pressure_score") or 0),
        "net_score": int(edge.get("net_score") or 0),
        "domain_links": _unique([str(item) for item in _as_list(edge.get("domain_links"))]),
        "basis_codes": _unique([str(item) for item in _as_list(edge.get("basis_codes"))])[:8],
    }


def _compact_element_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_key": edge.get("edge_key"),
        "classical_name": edge.get("classical_name"),
        "relation": edge.get("relation"),
        "source_element": edge.get("source_element"),
        "source_label": edge.get("source_label"),
        "target_element": edge.get("target_element"),
        "target_label": edge.get("target_label"),
        "source_group": edge.get("source_group"),
        "source_group_label": ROLE_LABELS.get(str(edge.get("source_group") or ""), ""),
        "target_group": edge.get("target_group"),
        "target_group_label": ROLE_LABELS.get(str(edge.get("target_group") or ""), ""),
        "scope": edge.get("scope"),
        "state": _edge_state(edge),
        "cycle_judgment": edge.get("cycle_judgment"),
        "month_command_verdict": edge.get("month_command_verdict"),
        "force_balance": edge.get("force_balance"),
        "force_effect": edge.get("force_effect"),
        "support_score": int(edge.get("support_score") or 0),
        "pressure_score": int(edge.get("pressure_score") or 0),
        "net_score": int(edge.get("net_score") or 0),
        "domain_links": _unique([str(item) for item in _as_list(edge.get("domain_links"))]),
        "basis_codes": _unique([str(item) for item in _as_list(edge.get("basis_codes"))])[:8],
    }


def _match_salience(match: Any, source: str) -> int:
    score = int(getattr(match, "presence_score", 0) or 0)
    verdict = str(getattr(match, "verdict", "") or "")
    month_fit = str(getattr(match, "month_fit_state", "") or "")
    context_state = str(getattr(match, "context_judgment_state", "") or "")
    score += 16 if source == "dual" else 8
    if "support" in verdict or "useful" in verdict:
        score += 12
    if "burden" in verdict or "pressure" in verdict:
        score += 8
    if "month" in month_fit:
        score += 6
    if context_state:
        score += 5
    return score


def _context_score_delta_from_basis(match: Any, source: str) -> int:
    prefix = "gyeokguk_dual_context_score_delta:" if source == "dual" else "gyeokguk_single_context_score_delta:"
    for code in _as_list(getattr(match, "basis_codes", [])):
        value = str(code or "")
        if not value.startswith(prefix):
            continue
        try:
            return int(value.split(":", 1)[1])
        except ValueError:
            return 0
    return 0


def _operation_state(
    *,
    presence_score: int,
    context_score_delta: int,
    position_score_delta: int,
    branch_score_delta: int,
    contextual_state: str,
) -> str:
    if presence_score >= 78 and context_score_delta >= 8 and contextual_state == "support":
        return "dominant_supported"
    if presence_score >= 66 and position_score_delta >= 10 and contextual_state == "support":
        return "visible_supported"
    if branch_score_delta <= -6 and context_score_delta < 0:
        return "eventful_pressure"
    if context_score_delta <= -8:
        return "weakened_by_context"
    if presence_score <= 42:
        return "latent_or_weak"
    if contextual_state == "mixed":
        return "mixed_operation"
    return "ordinary_operation"


def _operation_profile(
    *,
    match: Any,
    source: str,
    salience_score: int,
    contextual_state: str,
    position_summary: dict[str, Any],
    branch_relation_summary: dict[str, Any],
) -> dict[str, Any]:
    presence_score = int(getattr(match, "presence_score", 0) or 0)
    context_score_delta = _context_score_delta_from_basis(match, source)
    position_score_delta = int(position_summary.get("score_delta") or 0)
    branch_score_delta = int(branch_relation_summary.get("score_delta") or 0)
    reality_score_delta = position_score_delta + branch_score_delta
    return {
        "salience_score": salience_score,
        "presence_score": presence_score,
        "context_score_delta": context_score_delta,
        "reality_score_delta": reality_score_delta,
        "position_score_delta": position_score_delta,
        "branch_score_delta": branch_score_delta,
        "operation_state": _operation_state(
            presence_score=presence_score,
            context_score_delta=context_score_delta,
            position_score_delta=position_score_delta,
            branch_score_delta=branch_score_delta,
            contextual_state=contextual_state,
        ),
        "month_fit_state": str(getattr(match, "month_fit_state", "") or ""),
        "context_judgment_state": str(getattr(match, "context_judgment_state", "") or ""),
        "verdict": str(getattr(match, "verdict", "") or ""),
        "source": source,
    }


def _role_edges_for_groups(role_edges: list[dict[str, Any]], groups: set[str], limit: int = 5) -> list[dict[str, Any]]:
    matched = [
        edge
        for edge in role_edges
        if str(edge.get("source_group") or "") in groups or str(edge.get("target_group") or "") in groups
    ]
    return [_compact_role_edge(edge) for edge in sorted(matched, key=_edge_salience, reverse=True)[:limit]]


def _element_edges_for_groups(element_edges: list[dict[str, Any]], day_master_element: str, groups: set[str], limit: int = 5) -> list[dict[str, Any]]:
    elements = {_role_element(day_master_element, group) for group in groups}
    elements.discard("")
    matched = [
        edge
        for edge in element_edges
        if str(edge.get("source_element") or "") in elements or str(edge.get("target_element") or "") in elements
    ]
    return [_compact_element_edge(edge) for edge in sorted(matched, key=_edge_salience, reverse=True)[:limit]]


def _action_payload(
    match: Any,
    *,
    source: str,
    salience_score: int,
    role_edges: list[dict[str, Any]],
    element_edges: list[dict[str, Any]],
    day_master_element: str,
) -> dict[str, Any]:
    if source == "dual":
        groups = {
            str(getattr(match, "pattern_group", "") or ""),
            str(getattr(match, "first_group", "") or ""),
            str(getattr(match, "second_group", "") or ""),
        }
        groups.discard("")
        actors = [
            str(getattr(match, "first_ten_god", "") or ""),
            str(getattr(match, "second_ten_god", "") or ""),
        ]
        action_name = str(getattr(match, "exact_pair_name", "") or getattr(match, "sequence_key", "") or "")
        relation_summary = {
            "first_relation_to_pattern": getattr(match, "first_relation_to_pattern", ""),
            "second_relation_to_pattern": getattr(match, "second_relation_to_pattern", ""),
            "first_to_second_relation": getattr(match, "first_to_second_relation", ""),
        }
        resolution = str(getattr(match, "combination_resolution_state", "") or "")
    else:
        groups = {
            str(getattr(match, "pattern_group", "") or ""),
            str(getattr(match, "acting_group", "") or ""),
        }
        groups.discard("")
        actors = [str(getattr(match, "acting_ten_god", "") or "")]
        action_name = str(getattr(match, "action_nature", "") or getattr(match, "action_key", "") or "")
        relation_summary = {"relation_to_pattern": getattr(match, "relation_to_pattern", "")}
        resolution = str(getattr(match, "pattern_resolution_state", "") or "")

    relevant_role_edges = _role_edges_for_groups(role_edges, groups)
    relevant_element_edges = _element_edges_for_groups(element_edges, day_master_element, groups)
    edge_states = [str(edge.get("state") or "") for edge in [*relevant_role_edges, *relevant_element_edges]]
    if edge_states.count("support") > edge_states.count("burden"):
        contextual_state = "support"
    elif edge_states.count("burden") > edge_states.count("support"):
        contextual_state = "burden"
    else:
        contextual_state = "mixed"

    basis_codes = [
        *[str(code) for code in _as_list(getattr(match, "basis_codes", []))],
        *[str(code) for edge in relevant_role_edges for code in _as_list(edge.get("basis_codes"))],
        *[str(code) for edge in relevant_element_edges for code in _as_list(edge.get("basis_codes"))],
    ]
    classical_tags = _unique([str(tag) for tag in _as_list(getattr(match, "classical_action_tags", []))])
    position_summary = _position_summary(getattr(match, "position_context", {}))
    branch_relation_summary = _branch_relation_summary(getattr(match, "branch_relation_context", {}))
    context_score_delta = _context_score_delta_from_basis(match, source)
    operation_profile = _operation_profile(
        match=match,
        source=source,
        salience_score=salience_score,
        contextual_state=contextual_state,
        position_summary=position_summary,
        branch_relation_summary=branch_relation_summary,
    )

    return {
        "source": source,
        "rule_key": getattr(match, "rule_key", ""),
        "pattern": getattr(match, "pattern", ""),
        "pattern_label": PATTERN_LABELS.get(str(getattr(match, "pattern", "") or ""), str(getattr(match, "pattern", "") or "")),
        "action_name": action_name,
        "actors": [
            {"key": actor, "label": TEN_GOD_LABELS.get(actor, actor)}
            for actor in actors
            if actor
        ],
        "groups": sorted(groups),
        "group_labels": [ROLE_LABELS.get(group, group) for group in sorted(groups)],
        "relation_summary": relation_summary,
        "salience_score": salience_score,
        "presence_score": int(getattr(match, "presence_score", 0) or 0),
        "context_score_delta": context_score_delta,
        "operation_profile": operation_profile,
        "month_fit_state": getattr(match, "month_fit_state", ""),
        "verdict": getattr(match, "verdict", ""),
        "resolution_state": resolution,
        "contextual_state": contextual_state,
        "context_judgment_state": getattr(match, "context_judgment_state", ""),
        "day_master_strength_context": getattr(match, "day_master_strength_context", ""),
        "climate_context": getattr(match, "climate_context", ""),
        "position_summary": position_summary,
        "branch_relation_summary": branch_relation_summary,
        "domain_priority": _unique([str(item) for item in _as_list(getattr(match, "domain_priority", []))]),
        "domain_projection": dict(getattr(match, "domain_projections", {}) or {}),
        "single_classical_tags": classical_tags if source == "single" else [],
        "dual_classical_tags": classical_tags if source == "dual" else [],
        "role_edges": relevant_role_edges,
        "element_edges": relevant_element_edges,
        "basis_codes": _unique(basis_codes)[:18],
        "counter_signals": _unique([str(code) for code in _as_list(getattr(match, "counter_signals", []))])[:8],
    }


def _contextual_actions(gyeokguk_profile: Any, matrix: dict[str, Any], day_master_element: str) -> list[dict[str, Any]]:
    role_edges = [edge for edge in _as_list(matrix.get("role_edges")) if isinstance(edge, dict)]
    element_edges = [edge for edge in _as_list(matrix.get("element_edges")) if isinstance(edge, dict)]
    candidates: list[tuple[int, str, Any]] = []
    for match in _as_list(getattr(gyeokguk_profile, "dual_ten_god_action_matches", [])):
        candidates.append((_match_salience(match, "dual"), "dual", match))
    for match in _as_list(getattr(gyeokguk_profile, "ten_god_action_matches", [])):
        candidates.append((_match_salience(match, "single"), "single", match))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [
        _action_payload(
            match,
            source=source,
            salience_score=score,
            role_edges=role_edges,
            element_edges=element_edges,
            day_master_element=day_master_element,
        )
        for score, source, match in candidates[:8]
    ]


def _element_context(element_profile: Any, matrix: dict[str, Any]) -> dict[str, Any]:
    element_edges = [edge for edge in _as_list(matrix.get("element_edges")) if isinstance(edge, dict)]
    useful = [str(item) for item in _as_list(getattr(element_profile, "useful_elements", []))]
    caution = [str(item) for item in _as_list(getattr(element_profile, "caution_elements", []))]
    top_scores: list[dict[str, Any]] = []
    scores = getattr(element_profile, "scores", {}) or {}
    if isinstance(scores, dict):
        for key, score in scores.items():
            top_scores.append(
                {
                    "element": key,
                    "label": ELEMENT_LABELS.get(str(key), str(key)),
                    "ratio": round(float(getattr(score, "ratio", 0.0) or 0.0), 3),
                    "seasonal_score": round(float(getattr(score, "seasonal_score", 0.0) or 0.0), 3),
                    "state": getattr(score, "state", ""),
                    "exposure": getattr(score, "exposure", ""),
                }
            )
    top_scores.sort(key=lambda item: float(item["seasonal_score"]), reverse=True)

    def related_edges(elements: list[str]) -> list[dict[str, Any]]:
        selected = [
            edge
            for edge in element_edges
            if str(edge.get("source_element") or "") in elements or str(edge.get("target_element") or "") in elements
        ]
        return [_compact_element_edge(edge) for edge in sorted(selected, key=_edge_salience, reverse=True)[:6]]

    return {
        "day_master_element": getattr(element_profile, "day_master_element", ""),
        "day_master_element_label": ELEMENT_LABELS.get(str(getattr(element_profile, "day_master_element", "") or ""), ""),
        "day_master_strength": getattr(element_profile, "day_master_strength", ""),
        "day_master_strength_score": getattr(element_profile, "day_master_strength_score", 0),
        "dominant_elements": top_scores[:3],
        "weak_elements": sorted(top_scores, key=lambda item: float(item["seasonal_score"]))[:3],
        "useful_elements": useful,
        "useful_element_labels": [ELEMENT_LABELS.get(item, item) for item in useful],
        "caution_elements": caution,
        "caution_element_labels": [ELEMENT_LABELS.get(item, item) for item in caution],
        "useful_element_edges": related_edges(useful),
        "caution_element_edges": related_edges(caution),
        "temperature_balance": getattr(element_profile, "temperature_balance", ""),
        "moisture_balance": getattr(element_profile, "moisture_balance", ""),
        "climate_needs": _unique([str(item) for item in _as_list(getattr(element_profile, "climate_needs", []))]),
        "circulation_level": getattr(element_profile, "circulation_level", ""),
    }


def _domain_synthesis(actions: list[dict[str, Any]], matrix: dict[str, Any]) -> dict[str, Any]:
    domain_totals: dict[str, dict[str, Any]] = {}

    def bucket(domain: str) -> dict[str, Any]:
        label = DOMAIN_LABELS.get(domain, domain)
        return domain_totals.setdefault(
            domain,
            {"domain": domain, "label": label, "support": 0, "burden": 0, "mixed": 0, "source_count": 0, "source_keys": []},
        )

    for action in actions:
        state = str(action.get("contextual_state") or "mixed")
        edge_weight = sum(_scope_weight(str(edge.get("scope") or "")) for edge in _as_list(action.get("role_edges"))) // 8
        element_weight = sum(_scope_weight(str(edge.get("scope") or "")) for edge in _as_list(action.get("element_edges"))) // 12
        base_amount = max(2, int(action.get("presence_score") or 0) // 13 + edge_weight + element_weight)
        for domain_index, domain in enumerate([str(item) for item in _as_list(action.get("domain_priority")) if str(item)]):
            weight = (1.0, 0.72, 0.5, 0.32, 0.22, 0.16)[min(domain_index, 5)]
            amount = max(1, int(round(base_amount * weight)))
            data = bucket(domain)
            data["source_count"] += 1
            data["source_keys"].append(str(action.get("rule_key") or ""))
            if state == "support":
                data["support"] += amount
            elif state == "burden":
                data["burden"] += amount
            else:
                data["mixed"] += amount

    # Only month-command-touched edges are allowed to add a small secondary
    # domain signal. This prevents the ten generic 생극 edges from flattening
    # every chart into the same money/career/marriage profile.
    month_edges = [
        edge
        for edge in _as_list(matrix.get("role_edges"))
        if isinstance(edge, dict)
        and edge.get("touches_month_command")
        and str(edge.get("scope") or "").startswith("active")
    ][:4]
    for edge in sorted(month_edges, key=_edge_salience, reverse=True):
        domains = [
            str(domain)
            for domain in list((edge.get("domain_projection") or {}).keys())
            if str(domain) in {str(item.get("domain")) for item in domain_totals.values()}
        ][:3]
        state = _edge_state(edge)
        amount = max(1, _edge_salience(edge) // 22)
        for domain in domains:
            data = bucket(domain)
            data["source_count"] += 1
            data["source_keys"].append(str(edge.get("edge_key") or ""))
            if state == "support":
                data["support"] += amount
            elif state == "burden":
                data["burden"] += amount
            else:
                data["mixed"] += amount

    ordered = []
    preferred_order = [*DOMAIN_ORDER, "relationship", "reputation", "personality", "luck_activation"]
    for domain in preferred_order:
        data = domain_totals.get(domain)
        if not data:
            continue
        net = int(data["support"]) - int(data["burden"])
        total = int(data["support"]) + int(data["burden"]) + int(data["mixed"])
        ordered.append(
            {
                **data,
                "net": net,
                "total": total,
                "source_keys": _unique([str(key) for key in _as_list(data.get("source_keys"))])[:10],
                "state": "support" if net >= 8 else "burden" if net <= -8 else "mixed",
            }
        )
    ordered.sort(key=lambda item: (abs(int(item["net"])) + int(item["total"])), reverse=True)
    return {
        "top_domains": ordered[:6],
        "by_domain": {str(item["domain"]): item for item in ordered},
    }


def _basis_suffixes(action: dict[str, Any], prefix: str, limit: int = 8) -> list[str]:
    suffixes: list[str] = []
    for code in _as_list(action.get("basis_codes")):
        text = str(code)
        if text.startswith(prefix):
            suffixes.append(text.split(":", 1)[1])
    return _unique(suffixes)[:limit]


def _action_label(action: dict[str, Any]) -> str:
    action_name = str(action.get("action_name") or "")
    if action_name:
        return action_name
    actors = [
        str(actor.get("label") or actor.get("key") or "")
        for actor in _as_list(action.get("actors"))
        if isinstance(actor, dict)
    ]
    return "·".join([item for item in actors if item]) or str(action.get("rule_key") or "")


def _action_unit(action: dict[str, Any], *, domain: str = "") -> dict[str, Any]:
    state = str(action.get("contextual_state") or "mixed")
    source = str(action.get("source") or "")
    position = action.get("position_summary") if isinstance(action.get("position_summary"), dict) else {}
    branch = action.get("branch_relation_summary") if isinstance(action.get("branch_relation_summary"), dict) else {}
    projection = action.get("domain_projection") if isinstance(action.get("domain_projection"), dict) else {}
    domain_statement = str(projection.get(domain) or "") if domain else ""
    return {
        "source": source,
        "source_label": ACTION_SOURCE_LABELS.get(source, source),
        "rule_key": str(action.get("rule_key") or ""),
        "pattern": str(action.get("pattern") or ""),
        "pattern_label": str(action.get("pattern_label") or action.get("pattern") or ""),
        "action_name": _action_label(action),
        "actors": _as_list(action.get("actors"))[:3],
        "state": state,
        "state_label": ACTION_STATE_LABELS.get(state, state),
        "presence_score": int(action.get("presence_score") or 0),
        "verdict": str(action.get("verdict") or ""),
        "resolution_state": str(action.get("resolution_state") or ""),
        "domain_priority": _unique([str(item) for item in _as_list(action.get("domain_priority"))])[:6],
        "domain_statement": domain_statement,
        "visible_position_labels": _unique([str(item) for item in _as_list(position.get("visible_position_labels"))])[:4],
        "root_position_labels": _unique([str(item) for item in _as_list(position.get("root_position_labels"))])[:4],
        "hidden_position_labels": _unique([str(item) for item in _as_list(position.get("hidden_position_labels"))])[:4],
        "branch_relation_labels": _unique([str(item) for item in _as_list(branch.get("relation_type_labels"))])[:4],
        "single_classical_tags": _unique(
            [
                *[str(item) for item in _as_list(action.get("single_classical_tags"))],
                *_basis_suffixes(action, "gyeokguk_single_classical_action:", limit=5),
            ]
        )[:5],
        "dual_classical_tags": _unique(
            [
                *[str(item) for item in _as_list(action.get("dual_classical_tags"))],
                *_basis_suffixes(action, "gyeokguk_dual_classical_action:", limit=5),
            ]
        )[:5],
        "basis_codes": _unique([str(code) for code in _as_list(action.get("basis_codes"))])[:10],
        "counter_signals": _unique([str(code) for code in _as_list(action.get("counter_signals"))])[:6],
    }


def _action_rank_for_domain(action: dict[str, Any], domain: str = "") -> int:
    score = int(action.get("presence_score") or 0)
    source = str(action.get("source") or "")
    state = str(action.get("contextual_state") or "")
    domains = [str(item) for item in _as_list(action.get("domain_priority"))]
    projection = action.get("domain_projection") if isinstance(action.get("domain_projection"), dict) else {}
    if source == "dual":
        score += 18
    if domain and domains:
        if domains[0] == domain:
            score += 16
        elif domain in domains[:3]:
            score += 9
        elif domain in domains:
            score += 4
    if domain and domain in projection:
        score += 7
    if state in {"support", "burden"}:
        score += 5
    return score


def _action_distribution(actions: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, int] = {}
    by_state: dict[str, int] = {}
    classical_tags: dict[str, int] = {}
    for action in actions:
        source = str(action.get("source") or "")
        state = str(action.get("contextual_state") or "mixed")
        by_source[source] = by_source.get(source, 0) + 1
        by_state[state] = by_state.get(state, 0) + 1
        for tag in [
            *[str(item) for item in _as_list(action.get("single_classical_tags"))],
            *[str(item) for item in _as_list(action.get("dual_classical_tags"))],
            *_basis_suffixes(action, "gyeokguk_single_classical_action:", limit=10),
            *_basis_suffixes(action, "gyeokguk_dual_classical_action:", limit=10),
        ]:
            classical_tags[tag] = classical_tags.get(tag, 0) + 1

    lead_actions = sorted(actions, key=_action_rank_for_domain, reverse=True)
    return {
        "action_count": len(actions),
        "by_source": {
            source: {
                "count": count,
                "label": ACTION_SOURCE_LABELS.get(source, source),
            }
            for source, count in sorted(by_source.items())
        },
        "by_state": {
            state: {
                "count": count,
                "label": ACTION_STATE_LABELS.get(state, state),
            }
            for state, count in sorted(by_state.items())
        },
        "classical_tags": [
            {"tag": tag, "count": count}
            for tag, count in sorted(classical_tags.items(), key=lambda item: item[1], reverse=True)[:10]
        ],
        "lead_actions": [_action_unit(action) for action in lead_actions[:5]],
        "support_actions": [
            _action_unit(action)
            for action in lead_actions
            if str(action.get("contextual_state") or "") == "support"
        ][:4],
        "burden_actions": [
            _action_unit(action)
            for action in lead_actions
            if str(action.get("contextual_state") or "") == "burden"
        ][:4],
    }


def _domain_action_map(actions: list[dict[str, Any]], domain_synthesis: dict[str, Any]) -> dict[str, Any]:
    by_domain = domain_synthesis.get("by_domain") if isinstance(domain_synthesis.get("by_domain"), dict) else {}
    domain_order = [str(item.get("domain") or "") for item in _as_list(domain_synthesis.get("top_domains")) if isinstance(item, dict)]
    for action in actions:
        for domain in _as_list(action.get("domain_priority")):
            domain_text = str(domain)
            if domain_text and domain_text not in domain_order:
                domain_order.append(domain_text)
        projection = action.get("domain_projection") if isinstance(action.get("domain_projection"), dict) else {}
        for domain in projection:
            domain_text = str(domain)
            if domain_text and domain_text not in domain_order:
                domain_order.append(domain_text)

    result: dict[str, Any] = {}
    for domain in domain_order[:8]:
        related = [
            action
            for action in actions
            if domain in [str(item) for item in _as_list(action.get("domain_priority"))]
            or (
                isinstance(action.get("domain_projection"), dict)
                and domain in action.get("domain_projection", {})
            )
        ]
        related.sort(key=lambda item: _action_rank_for_domain(item, domain), reverse=True)
        summary = by_domain.get(domain) if isinstance(by_domain.get(domain), dict) else {}
        if not related and not summary:
            continue
        lead_units = [_action_unit(action, domain=domain) for action in related[:4]]
        result[domain] = {
            "domain": domain,
            "label": DOMAIN_LABELS.get(domain, domain),
            "state": str(summary.get("state") or "mixed"),
            "net": int(summary.get("net") or 0),
            "total": int(summary.get("total") or 0),
            "support": int(summary.get("support") or 0),
            "burden": int(summary.get("burden") or 0),
            "mixed": int(summary.get("mixed") or 0),
            "source_count": len(related),
            "lead_actions": lead_units,
            "action_labels": [unit["action_name"] for unit in lead_units if unit.get("action_name")],
            "basis_codes": _unique(
                [code for unit in lead_units for code in _as_list(unit.get("basis_codes"))]
            )[:14],
        }
    return result


def _engine_readiness(
    *,
    coverage: dict[str, Any],
    actions: list[dict[str, Any]],
    action_distribution: dict[str, Any],
    domain_action_map: dict[str, Any],
    pattern_variation: dict[str, Any],
) -> dict[str, Any]:
    score = 0
    checks: list[dict[str, Any]] = []

    def add(key: str, passed: bool, points: int, label: str) -> None:
        nonlocal score
        if passed:
            score += points
        checks.append({"key": key, "passed": passed, "points": points if passed else 0, "label": label})

    by_source = action_distribution.get("by_source") if isinstance(action_distribution.get("by_source"), dict) else {}
    add("month_anchor", bool(coverage.get("month_anchor")), 14, "월지·월령 기준이 확보되었습니다.")
    add("single_actions", int((by_source.get("single") or {}).get("count") or 0) >= 1, 10, "격국별 단일 십신 작용이 연결되었습니다.")
    add("dual_actions", int((by_source.get("dual") or {}).get("count") or 0) >= 1, 14, "격국별 이중 십신 조합이 연결되었습니다.")
    add("reality_profile", bool((pattern_variation.get("reality_profile") or {}).get("state")), 12, "투출·통근·지장간·지지 관계가 현실성 판단에 반영되었습니다.")
    add("elemental_judgment", bool((pattern_variation.get("elemental_judgment") or {}).get("components")), 12, "오행·월령·조후 보정이 격국 판단에 반영되었습니다.")
    add("day_stem_reception", bool((pattern_variation.get("day_stem_reception") or {}).get("reception_key")), 8, "일간별 천간 수용값이 연결되었습니다.")
    add("elemental_materiality", bool((pattern_variation.get("elemental_materiality") or {}).get("materiality_key")), 8, "오행 배합 물상값이 연결되었습니다.")
    add("domain_action_map", len(domain_action_map) >= 3, 12, "분야별로 어떤 격국 작용이 들어갔는지 분리되었습니다.")
    add("branch_relations", int(coverage.get("branch_relations") or 0) >= 1, 5, "합충형파해 자료가 보조 판단에 포함되었습니다.")
    add("climate", bool(coverage.get("climate")), 5, "조후 판단이 포함되었습니다.")

    level = "complete" if score >= 86 else "usable" if score >= 72 else "needs_review"
    gaps = [item["key"] for item in checks if not item["passed"]]
    return {
        "score": score,
        "level": level,
        "checks": checks,
        "gaps": gaps,
        "summary": (
            "격국론 1차 산출 계약으로 사용할 수 있습니다."
            if level == "complete"
            else "사용은 가능하지만 보강해야 할 판단축이 남아 있습니다."
            if level == "usable"
            else "격국론 산출 계약을 더 보강해야 합니다."
        ),
    }


def _element_score_entry(element_context: dict[str, Any], element: str) -> dict[str, Any]:
    for item in [
        *_as_list(element_context.get("dominant_elements")),
        *_as_list(element_context.get("weak_elements")),
    ]:
        if isinstance(item, dict) and str(item.get("element") or "") == element:
            return item
    return {}


def _pattern_element_status(element_context: dict[str, Any], pattern_element: str) -> str:
    if not pattern_element:
        return "ordinary"
    useful = {str(item) for item in _as_list(element_context.get("useful_elements"))}
    caution = {str(item) for item in _as_list(element_context.get("caution_elements"))}
    score = _element_score_entry(element_context, pattern_element)
    state = str(score.get("state") or "")
    if pattern_element in useful:
        return "useful"
    if pattern_element in caution:
        return "caution"
    if state in {"dominant", "strong"}:
        return "dominant"
    if state in {"weak", "absent"}:
        return "weak"
    return "ordinary"


def _month_pattern_element_relation(month_element: str, pattern_element: str) -> str:
    if not month_element or not pattern_element:
        return "indirect"
    if month_element == pattern_element:
        return "same"
    if ELEMENT_GENERATES.get(month_element) == pattern_element:
        return "month_generates_pattern"
    if ELEMENT_GENERATES.get(pattern_element) == month_element:
        return "pattern_generates_month"
    if ELEMENT_CONTROLS.get(month_element) == pattern_element:
        return "month_controls_pattern"
    if ELEMENT_CONTROLS.get(pattern_element) == month_element:
        return "pattern_controls_month"
    return "indirect"


def _variation_state(pattern_status: str, actions: list[dict[str, Any]]) -> str:
    support = sum(1 for action in actions if action.get("contextual_state") == "support")
    burden = sum(1 for action in actions if action.get("contextual_state") == "burden")
    if pattern_status in {"useful", "dominant"} and support >= burden:
        return "support"
    if pattern_status == "caution" or burden > support + 1:
        return "burden"
    if pattern_status == "weak":
        return "latent"
    return "mixed"


def _bounded(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _pattern_status_delta(pattern_status: str) -> int:
    return {
        "useful": 8,
        "dominant": 5,
        "ordinary": 0,
        "weak": -5,
        "caution": -8,
    }.get(str(pattern_status or ""), 0)


def _month_relation_delta(relation: str) -> int:
    return {
        "same": 6,
        "month_generates_pattern": 8,
        "pattern_generates_month": -4,
        "month_controls_pattern": -8,
        "pattern_controls_month": -3,
        "indirect": 0,
    }.get(str(relation or ""), 0)


def _pattern_element_exposure_delta(score: dict[str, Any]) -> int:
    state = str(score.get("state") or "")
    exposure = str(score.get("exposure") or "")
    delta = {
        "dominant": 4,
        "strong": 3,
        "balanced": 1,
        "weak": -3,
        "absent": -6,
    }.get(state, 0)
    delta += {
        "clear": 3,
        "present": 2,
        "hidden": -1,
        "absent": -3,
    }.get(exposure, 0)
    return delta


def _day_master_capacity_delta(primary_group: str, day_master_strength: str) -> int:
    """Adjust whether the day master can carry the pattern role.

    Wealth and officer roles press the day master more directly. Peer/resource
    roles can become excessive when the day master is already strong. This is a
    compact bridge between strength theory and pattern judgment.
    """

    strength = str(day_master_strength or "")
    group = str(primary_group or "")
    if group in {"wealth", "officer"}:
        return {
            "very_strong": 4,
            "strong": 3,
            "balanced": 1,
            "weak": -5,
            "very_weak": -8,
        }.get(strength, 0)
    if group == "output":
        return {
            "very_strong": 3,
            "strong": 2,
            "balanced": 1,
            "weak": -2,
            "very_weak": -4,
        }.get(strength, 0)
    if group in {"peer", "resource"}:
        return {
            "very_strong": -6,
            "strong": -3,
            "balanced": 1,
            "weak": 4,
            "very_weak": 5,
        }.get(strength, 0)
    return 0


def _action_balance_delta(actions: list[dict[str, Any]]) -> int:
    support = sum(1 for action in actions if action.get("contextual_state") == "support")
    burden = sum(1 for action in actions if action.get("contextual_state") == "burden")
    mixed = sum(1 for action in actions if action.get("contextual_state") == "mixed")
    return _bounded((support - burden) * 2 + min(mixed, 2), -6, 6)


def _action_reality_profile(actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize whether the pattern action is visible, rooted, latent or pressured."""

    visible_positions: list[str] = []
    root_positions: list[str] = []
    hidden_positions: list[str] = []
    position_grades: list[str] = []
    branch_relation_types: list[str] = []
    branch_relation_grades: list[str] = []
    position_delta = 0
    branch_delta = 0
    counter_signals: list[str] = []
    basis_codes: list[str] = []

    for action in actions:
        position = action.get("position_summary") if isinstance(action, dict) else {}
        branch = action.get("branch_relation_summary") if isinstance(action, dict) else {}
        if isinstance(position, dict):
            visible_positions.extend(str(item) for item in _as_list(position.get("visible_positions")))
            root_positions.extend(str(item) for item in _as_list(position.get("root_positions")))
            hidden_positions.extend(str(item) for item in _as_list(position.get("hidden_positions")))
            position_grades.extend(str(item) for item in _as_list(position.get("grades")))
            position_delta += int(position.get("score_delta") or 0)
            counter_signals.extend(str(item) for item in _as_list(position.get("counter_signals")))
            basis_codes.extend(str(item) for item in _as_list(position.get("basis_codes")))
        if isinstance(branch, dict):
            branch_relation_types.extend(str(item) for item in _as_list(branch.get("relation_types")))
            branch_relation_grades.extend(str(item) for item in _as_list(branch.get("grades")))
            branch_delta += int(branch.get("score_delta") or 0)
            counter_signals.extend(str(item) for item in _as_list(branch.get("counter_signals")))
            basis_codes.extend(str(item) for item in _as_list(branch.get("basis_codes")))

    visible = _unique(visible_positions)
    rooted = _unique(root_positions)
    hidden = _unique(hidden_positions)
    counters = _unique(counter_signals)
    action_count = max(1, len(actions))
    visible_bonus = min(3, len(visible))
    root_bonus = min(2, len(rooted))
    hidden_bonus = 1 if hidden else 0
    pressure_penalty = min(5, len(counters))
    score_delta = _bounded(
        round(position_delta / max(8, action_count * 7))
        + visible_bonus
        + root_bonus
        + hidden_bonus
        + _bounded(round(branch_delta / max(8, action_count * 6)), -4, 4)
        - pressure_penalty,
        -8,
        8,
    )

    if score_delta >= 4:
        state = "support"
    elif score_delta <= -3:
        state = "burden"
    elif hidden and not visible and not rooted:
        state = "latent"
    else:
        state = "mixed"

    return {
        "state": state,
        "score_delta": score_delta,
        "position_delta": position_delta,
        "branch_delta": branch_delta,
        "visible_positions": visible,
        "visible_position_labels": [STEM_POSITION_LABELS.get(item, item) for item in visible],
        "root_positions": rooted,
        "root_position_labels": [BRANCH_POSITION_LABELS.get(item, item) for item in rooted],
        "hidden_positions": hidden,
        "hidden_position_labels": [f"{BRANCH_POSITION_LABELS.get(item, item)} 지장간" for item in hidden],
        "position_grade_labels": _unique([POSITION_GRADE_LABELS.get(item, item) for item in position_grades])[:6],
        "branch_relation_types": _unique(branch_relation_types),
        "branch_relation_labels": _unique([BRANCH_RELATION_LABELS.get(item, item) for item in branch_relation_types])[:6],
        "branch_grade_labels": _unique([BRANCH_RELATION_GRADE_LABELS.get(item, item) for item in branch_relation_grades])[:6],
        "counter_signals": counters[:8],
        "basis_codes": _unique(basis_codes)[:12],
    }


def _climate_need_delta(pattern_element: str, element_context: dict[str, Any]) -> int:
    climate_needs = {str(item) for item in _as_list(element_context.get("climate_needs"))}
    useful = {str(item) for item in _as_list(element_context.get("useful_elements"))}
    caution = {str(item) for item in _as_list(element_context.get("caution_elements"))}
    if pattern_element and pattern_element in climate_needs:
        return 7
    if pattern_element and pattern_element in useful:
        return 4
    if pattern_element and pattern_element in caution:
        return -5
    return 0


def _climate_temperature_delta(pattern_element: str, temperature_balance: str) -> int:
    element = str(pattern_element or "")
    temperature = str(temperature_balance or "")
    if temperature == "cold":
        return {
            "fire": 4,
            "earth": 1,
            "water": -3,
        }.get(element, 0)
    if temperature == "hot":
        return {
            "water": 4,
            "metal": 1,
            "fire": -3,
            "earth": -1,
        }.get(element, 0)
    return 0


def _climate_moisture_delta(pattern_element: str, moisture_balance: str) -> int:
    element = str(pattern_element or "")
    moisture = str(moisture_balance or "")
    if moisture == "dry":
        return {
            "water": 4,
            "metal": 2,
            "fire": -2,
            "earth": -2,
        }.get(element, 0)
    if moisture == "wet":
        return {
            "fire": 3,
            "earth": 2,
            "water": -3,
            "wood": -1,
        }.get(element, 0)
    return 0


def _climate_state_from_delta(score_delta: int, has_climate_signal: bool) -> str:
    if score_delta >= 3:
        return "support"
    if score_delta <= -3:
        return "burden"
    if score_delta < 0:
        return "unstable"
    return "mixed" if has_climate_signal else "neutral"


def _climate_adjustment_profile(
    *,
    primary_group: str,
    pattern_element: str,
    element_context: dict[str, Any],
) -> dict[str, Any]:
    element = str(pattern_element or "")
    element_label = ELEMENT_LABELS.get(element, element)
    temperature = str(element_context.get("temperature_balance") or "")
    moisture = str(element_context.get("moisture_balance") or "")
    climate_needs = _unique([str(item) for item in _as_list(element_context.get("climate_needs")) if str(item)])
    useful = {str(item) for item in _as_list(element_context.get("useful_elements"))}
    caution = {str(item) for item in _as_list(element_context.get("caution_elements"))}
    components: list[dict[str, Any]] = []

    need_delta = _climate_need_delta(element, element_context)
    components.append({"key": "climate_need_match", "label": "조후 필요 오행", "score_delta": need_delta})
    temp_delta = _climate_temperature_delta(element, temperature)
    components.append({"key": "temperature_balance", "label": "온도 조절", "score_delta": temp_delta})
    moisture_delta = _climate_moisture_delta(element, moisture)
    components.append({"key": "moisture_balance", "label": "건습 조절", "score_delta": moisture_delta})

    if element and element in useful and need_delta <= 0:
        components.append({"key": "useful_element_support", "label": "필요 오행 보조", "score_delta": 3})
    if element and element in caution and need_delta >= 0:
        components.append({"key": "caution_element_pressure", "label": "주의 오행 압력", "score_delta": -4})

    raw_delta = sum(int(item["score_delta"]) for item in components)
    score_delta = _bounded(round(raw_delta / 2), -6, 6)
    has_climate_signal = any(
        [
            temperature and temperature != "balanced",
            moisture and moisture != "balanced",
            climate_needs,
            element in useful,
            element in caution,
        ]
    )
    state = _climate_state_from_delta(score_delta, has_climate_signal)
    needed = element in set(climate_needs)
    meaning = CLIMATE_ELEMENT_MEANINGS.get(element, "격국의 작용")
    temperature_label = TEMPERATURE_BALANCE_LABELS.get(temperature, temperature)
    moisture_label = MOISTURE_BALANCE_LABELS.get(moisture, moisture)

    if needed:
        interpretation = f"{element_label} 기운은 조후상 필요한 재료입니다. {meaning}이 사주의 치우침을 잡는 쪽으로 작용합니다."
    elif element in caution:
        interpretation = f"{element_label} 기운은 조후상 과해지면 부담이 됩니다. {meaning}이 지나치면 격국의 장점도 소모로 바뀔 수 있습니다."
    elif score_delta > 0:
        interpretation = f"{element_label} 기운은 조후의 치우침을 일부 보완합니다. {meaning}이 안정될 때 격국의 활용도가 올라갑니다."
    elif score_delta < 0:
        interpretation = f"{element_label} 기운은 조후의 치우침을 키울 수 있습니다. {meaning}을 쓰더라도 속도와 소모를 함께 관리해야 합니다."
    else:
        interpretation = f"{element_label} 기운은 조후상 결정적 약재나 병으로 고정되지 않습니다. 다른 오행과 위치 조건을 함께 보아야 합니다."

    domains = _unique(
        [
            *CLIMATE_ELEMENT_DOMAINS.get(element, ()),
            *RECEPTION_DOMAIN_PRIORITY.get(str(primary_group or ""), ()),
        ]
    )
    domain_modifiers: list[dict[str, Any]] = []
    for index, domain in enumerate(domains):
        if domain not in DOMAIN_LABELS:
            continue
        weight = (1.0, 0.75, 0.55, 0.35, 0.25)[min(index, 4)]
        domain_delta = _bounded(round(score_delta * weight), -4, 4)
        if domain_delta == 0 and state in {"support", "burden"}:
            domain_delta = 1 if state == "support" else -1
        domain_modifiers.append(
            {
                "domain": domain,
                "label": DOMAIN_LABELS.get(domain, domain),
                "score_delta": domain_delta,
                "state": _reception_state_from_delta(domain_delta),
                "reason": f"{element_label} 조후 작용이 {DOMAIN_LABELS.get(domain, domain)} 영역의 지속성과 소모를 가릅니다.",
            }
        )
        if len(domain_modifiers) >= 6:
            break

    return {
        "climate_key": "|".join(
            [
                element,
                temperature,
                moisture,
                "-".join(climate_needs),
                state,
            ]
        ),
        "pattern_element": element,
        "pattern_element_label": element_label,
        "temperature_balance": temperature,
        "temperature_balance_label": temperature_label,
        "moisture_balance": moisture,
        "moisture_balance_label": moisture_label,
        "climate_needs": climate_needs,
        "climate_need_labels": [ELEMENT_LABELS.get(item, item) for item in climate_needs],
        "state": state,
        "score_delta": score_delta,
        "raw_delta": raw_delta,
        "components": components,
        "interpretation": interpretation,
        "domain_modifiers": domain_modifiers,
        "basis_codes": [
            f"pattern_variation_climate:{item['key']}:{item['score_delta']}"
            for item in components
        ],
    }


def _elemental_judgment(
    *,
    primary_group: str,
    day_master_strength: str,
    pattern_status: str,
    relation: str,
    pattern_element: str,
    score: dict[str, Any],
    actions: list[dict[str, Any]],
    element_context: dict[str, Any],
    reality_profile: dict[str, Any],
) -> dict[str, Any]:
    components = [
        {
            "key": "pattern_element_status",
            "label": "격국 오행 상태",
            "score_delta": _pattern_status_delta(pattern_status),
        },
        {
            "key": "month_pattern_relation",
            "label": "월령과 격국 오행 관계",
            "score_delta": _month_relation_delta(relation),
        },
        {
            "key": "pattern_element_exposure",
            "label": "오행 노출과 뿌리",
            "score_delta": _pattern_element_exposure_delta(score),
        },
        {
            "key": "day_master_capacity",
            "label": "일간 감당력",
            "score_delta": _day_master_capacity_delta(primary_group, day_master_strength),
        },
        {
            "key": "climate_need",
            "label": "조후 필요성",
            "score_delta": _climate_need_delta(pattern_element, element_context),
        },
        {
            "key": "action_balance",
            "label": "격국 작용의 성격",
            "score_delta": _action_balance_delta(actions),
        },
        {
            "key": "position_branch_reality",
            "label": "투출·통근·지장간 현실성",
            "score_delta": int(reality_profile.get("score_delta") or 0),
        },
    ]
    raw_delta = sum(int(item["score_delta"]) for item in components)
    score_delta = _bounded(round(raw_delta / 3), -10, 10)
    if score_delta >= 4:
        state = "support"
    elif score_delta <= -4:
        state = "burden"
    elif score_delta <= -1:
        state = "unstable"
    elif pattern_status == "caution":
        state = "unstable"
    else:
        state = "mixed"
    return {
        "state": state,
        "score_delta": score_delta,
        "raw_delta": raw_delta,
        "components": components,
        "basis_codes": [
            f"pattern_variation_elemental:{item['key']}:{item['score_delta']}"
            for item in components
        ],
    }


def _pattern_target_stem(
    *,
    day_master_stem: str,
    pattern_element: str,
    primary_ten_god: str,
    month_command_stem: str = "",
) -> str:
    day_stem = str(day_master_stem or "")
    target_element = str(pattern_element or "")
    ten_god = str(primary_ten_god or "")
    command_stem = str(month_command_stem or "")
    if day_stem not in STEM_METADATA or not target_element:
        return ""
    if command_stem in STEM_METADATA:
        try:
            if (
                STEM_METADATA[command_stem]["element"] == target_element
                and (not ten_god or ten_god_for(day_stem, command_stem) == ten_god)
            ):
                return command_stem
        except KeyError:
            pass
    candidates: list[str] = []
    for stem in STEM_ORDER:
        if STEM_METADATA.get(stem, {}).get("element") != target_element:
            continue
        try:
            if not ten_god or ten_god_for(day_stem, stem) == ten_god:
                candidates.append(stem)
        except KeyError:
            continue
    return candidates[0] if candidates else ""


def _reception_state_from_delta(delta: int) -> str:
    if delta >= 3:
        return "support"
    if delta <= -3:
        return "burden"
    if delta < 0:
        return "unstable"
    return "mixed"


def _reception_domain_base_delta(*, primary_group: str, domain: str, rule: dict[str, Any]) -> int:
    group = str(primary_group or "")
    target_domain = str(domain or "")
    domain_links = {str(item) for item in _as_list(rule.get("domain_links"))}
    preferred = set(RECEPTION_DOMAIN_PRIORITY.get(group, ()))
    if target_domain in preferred and target_domain in domain_links:
        return 2
    if target_domain in preferred:
        return 1
    if target_domain in domain_links:
        return 1
    return 0


def _reception_state_factor(elemental_state: str) -> int:
    state = str(elemental_state or "")
    if state == "support":
        return 1
    if state == "burden":
        return -2
    if state == "unstable":
        return -1
    return 0


def _day_stem_reception_profile(
    *,
    anchor: dict[str, Any],
    pattern_element: str,
    elemental_judgment: dict[str, Any],
) -> dict[str, Any]:
    day_master_stem = str(anchor.get("day_master_stem") or "")
    primary_ten_god = str(anchor.get("primary_ten_god") or "")
    primary_group = str(anchor.get("primary_group") or "")
    target_stem = _pattern_target_stem(
        day_master_stem=day_master_stem,
        pattern_element=pattern_element,
        primary_ten_god=primary_ten_god,
        month_command_stem=str(anchor.get("month_command_stem") or ""),
    )
    if not day_master_stem or not target_stem:
        return {}
    rule = stem_reception_rule(day_master_stem, target_stem)
    ten_god = str(rule.get("target_ten_god") or primary_ten_god)
    day_label = STEM_LABELS.get(day_master_stem, day_master_stem)
    target_label = STEM_LABELS.get(target_stem, target_stem)
    ten_god_label = TEN_GOD_LABELS.get(ten_god, ten_god)
    state_factor = _reception_state_factor(str(elemental_judgment.get("state") or ""))
    preferred_domains = RECEPTION_DOMAIN_PRIORITY.get(primary_group, ())
    ordered_domains = _unique([*preferred_domains, *[str(item) for item in _as_list(rule.get("domain_links"))]])
    domain_modifiers = []
    for domain in ordered_domains:
        if domain not in DOMAIN_LABELS:
            continue
        base_delta = _reception_domain_base_delta(primary_group=primary_group, domain=domain, rule=rule)
        if not base_delta and domain not in preferred_domains:
            continue
        score_delta = _bounded(base_delta + state_factor, -4, 4)
        domain_modifiers.append(
            {
                "domain": domain,
                "label": DOMAIN_LABELS.get(domain, domain),
                "score_delta": score_delta,
                "state": _reception_state_from_delta(score_delta),
                "reason": (
                    f"{day_label}일간이 {target_label}을 {ten_god_label} 작용으로 받아들이는 방식이 "
                    f"{DOMAIN_LABELS.get(domain, domain)} 판단에 적용됩니다."
                ),
            }
        )
        if len(domain_modifiers) >= 5:
            break
    return {
        "reception_key": f"{day_master_stem}->{target_stem}",
        "day_master_stem": day_master_stem,
        "day_master_stem_label": day_label,
        "target_stem": target_stem,
        "target_stem_label": target_label,
        "target_element": STEM_METADATA[target_stem]["element"],
        "target_ten_god": ten_god,
        "target_ten_god_label": ten_god_label,
        "trait_keywords": _as_list(rule.get("trait_keywords"))[:6],
        "core_interpretation": str(rule.get("core_interpretation") or ""),
        "felt_experience": str(rule.get("felt_experience") or ""),
        "behavior_tendency": str(rule.get("behavior_tendency") or ""),
        "domain_modifiers": domain_modifiers,
        "basis_codes": [
            f"pattern_variation_reception:{day_master_stem}:{target_stem}",
            f"pattern_variation_reception_ten_god:{ten_god}",
            f"pattern_variation_reception_group:{primary_group}",
        ],
    }


def _element_pair_key(*elements: str) -> tuple[str, ...]:
    values = [str(element or "") for element in elements if str(element or "") in ELEMENT_ORDER]
    return tuple(sorted(dict.fromkeys(values), key=lambda item: ELEMENT_ORDER.index(item)))


def _direct_element_relation(source_element: str, target_element: str) -> str:
    source = str(source_element or "")
    target = str(target_element or "")
    if not source or not target:
        return "indirect"
    if source == target:
        return "same"
    if ELEMENT_GENERATES.get(source) == target:
        return "source_generates_target"
    if ELEMENT_GENERATES.get(target) == source:
        return "target_generates_source"
    if ELEMENT_CONTROLS.get(source) == target:
        return "source_controls_target"
    if ELEMENT_CONTROLS.get(target) == source:
        return "target_controls_source"
    return "indirect"


def _element_relation_type(source_element: str, target_element: str, relation: str = "") -> str:
    pair_key = _element_pair_key(source_element, target_element)
    if len(pair_key) == 1:
        return "same_element_density"
    if pair_key in SPECIFIC_ELEMENT_SET_RULES:
        return str(SPECIFIC_ELEMENT_SET_RULES[pair_key].get("relation_type") or "")
    direct_relation = _direct_element_relation(source_element, target_element)
    if direct_relation in {"source_generates_target", "target_generates_source"}:
        return "element_generation"
    if direct_relation in {"source_controls_target", "target_controls_source"}:
        return "element_control"
    if relation in {"month_generates_pattern", "pattern_generates_month"}:
        return "element_generation"
    if relation in {"month_controls_pattern", "pattern_controls_month"}:
        return "element_control"
    return "element_mixed"


def _element_rule_payload(source_element: str, target_element: str, relation_type: str) -> dict[str, Any]:
    pair_key = _element_pair_key(source_element, target_element)
    if pair_key in SPECIFIC_ELEMENT_SET_RULES:
        return dict(SPECIFIC_ELEMENT_SET_RULES[pair_key])
    if relation_type == "same_element_density" and len(pair_key) == 1:
        return same_element_density_rule(pair_key[0])
    rule = GENERIC_RELATION_RULES.get(relation_type) or GENERIC_RELATION_RULES["element_mixed"]
    return {
        "relation_type": relation_type,
        "source_rule": "generic_element_relation",
        "domain_links": list(rule.get("domain_links") or []),
        "trait_keywords": list(rule.get("trait_keywords") or []),
        "interpretation": str(rule.get("interpretation") or ""),
    }


def _element_relation_base_delta(relation: str) -> int:
    return {
        "same": 2,
        "month_generates_pattern": 4,
        "pattern_generates_month": -2,
        "month_controls_pattern": -4,
        "pattern_controls_month": 1,
        "indirect": 0,
    }.get(str(relation or ""), 0)


def _element_status_base_delta(pattern_status: str) -> int:
    return {
        "useful": 3,
        "dominant": 2,
        "ordinary": 0,
        "weak": -2,
        "caution": -3,
    }.get(str(pattern_status or ""), 0)


def _day_pattern_relation_delta(direct_relation: str, primary_group: str) -> int:
    relation = str(direct_relation or "")
    group = str(primary_group or "")
    if relation == "same":
        return 1
    if relation == "source_generates_target":
        return 2
    if relation == "target_generates_source":
        return 1
    if relation == "source_controls_target":
        return 2 if group in {"wealth", "resource"} else 1
    if relation == "target_controls_source":
        return -3 if group in {"officer", "wealth"} else -1
    return 0


def _element_materiality_profile(
    *,
    primary_group: str,
    day_master_element: str,
    month_element: str,
    pattern_element: str,
    relation: str,
    pattern_status: str,
) -> dict[str, Any]:
    direct_relation = _direct_element_relation(day_master_element, pattern_element)
    relation_type = _element_relation_type(day_master_element, pattern_element, relation)
    payload = _element_rule_payload(day_master_element, pattern_element, relation_type)
    pair_key = _element_pair_key(day_master_element, pattern_element)
    pair_label = "".join(ELEMENT_LABELS.get(item, item) for item in pair_key)
    raw_delta = (
        _element_relation_base_delta(relation)
        + _element_status_base_delta(pattern_status)
        + _day_pattern_relation_delta(direct_relation, primary_group)
    )
    score_delta = _bounded(round(raw_delta / 2), -5, 5)
    if score_delta >= 3:
        state = "support"
    elif score_delta <= -3:
        state = "burden"
    elif score_delta < 0:
        state = "unstable"
    else:
        state = "mixed"
    payload_domains = [str(item) for item in _as_list(payload.get("domain_links"))]
    preferred = list(RECEPTION_DOMAIN_PRIORITY.get(str(primary_group or ""), ()))
    domains = _unique([*payload_domains, *preferred])
    domain_modifiers: list[dict[str, Any]] = []
    for domain in domains:
        if domain not in DOMAIN_LABELS:
            continue
        base = 2 if domain in payload_domains else 1
        if domain in preferred:
            base += 1
        domain_delta = _bounded(base + score_delta // 2, -4, 4)
        domain_modifiers.append(
            {
                "domain": domain,
                "label": DOMAIN_LABELS.get(domain, domain),
                "score_delta": domain_delta,
                "state": _reception_state_from_delta(domain_delta),
                "reason": f"{pair_label} 배합이 {DOMAIN_LABELS.get(domain, domain)} 영역의 작용 방식을 구체화합니다.",
            }
        )
        if len(domain_modifiers) >= 6:
            break
    return {
        "materiality_key": "|".join([relation_type, *pair_key, str(relation or ""), str(pattern_status or "")]),
        "relation_type": relation_type,
        "relation_type_label": MATERIALITY_RELATION_LABELS.get(relation_type, relation_type),
        "source_rule": str(payload.get("source_rule") or ""),
        "day_master_element": day_master_element,
        "day_master_element_label": ELEMENT_LABELS.get(day_master_element, day_master_element),
        "month_element": month_element,
        "month_element_label": ELEMENT_LABELS.get(month_element, month_element),
        "pattern_element": pattern_element,
        "pattern_element_label": ELEMENT_LABELS.get(pattern_element, pattern_element),
        "element_pair": list(pair_key),
        "element_pair_label": pair_label,
        "day_pattern_relation": direct_relation,
        "relation": relation,
        "relation_label": ELEMENT_RELATION_LABELS.get(relation, relation),
        "state": state,
        "score_delta": score_delta,
        "raw_delta": raw_delta,
        "domain_links": payload_domains,
        "trait_keywords": _as_list(payload.get("trait_keywords"))[:6],
        "interpretation": str(payload.get("interpretation") or ""),
        "domain_modifiers": domain_modifiers,
        "basis_codes": [
            f"pattern_variation_materiality:{relation_type}",
            f"pattern_variation_materiality_pair:{'-'.join(pair_key)}",
            f"pattern_variation_materiality_day_relation:{direct_relation}",
            f"pattern_variation_materiality_relation:{relation}",
            f"pattern_variation_materiality_status:{pattern_status}",
            f"pattern_variation_materiality_score_delta:{score_delta}",
        ],
    }


def _variation_domain_tilt(
    *,
    primary_group: str,
    domain_synthesis: dict[str, Any],
    variation_state: str,
    elemental_judgment: dict[str, Any],
    day_stem_reception: dict[str, Any],
    elemental_materiality: dict[str, Any],
    climate_adjustment: dict[str, Any],
    reality_profile: dict[str, Any],
    pattern_status: str = "",
) -> list[dict[str, Any]]:
    top_domains = [item for item in _as_list(domain_synthesis.get("top_domains")) if isinstance(item, dict)]
    preferred = list(DOMAIN_TILT_BY_GROUP.get(primary_group, ()))
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    base_delta = int(elemental_judgment.get("score_delta") or 0)
    reception_label = str(day_stem_reception.get("target_ten_god_label") or "")
    materiality_label = str(elemental_materiality.get("element_pair_label") or "")
    climate_label = str(climate_adjustment.get("pattern_element_label") or "")
    materiality_domains = [
        str(item.get("domain") or "")
        for item in _as_list(elemental_materiality.get("domain_modifiers") if isinstance(elemental_materiality, dict) else [])
        if isinstance(item, dict)
    ]
    climate_domains = [
        str(item.get("domain") or "")
        for item in _as_list(climate_adjustment.get("domain_modifiers") if isinstance(climate_adjustment, dict) else [])
        if isinstance(item, dict)
    ]
    for domain in [*preferred, *materiality_domains, *climate_domains, *[str(item.get("domain") or "") for item in top_domains]]:
        if not domain or domain in seen:
            continue
        seen.add(domain)
        source = next((item for item in top_domains if str(item.get("domain") or "") == domain), {})
        state = str(source.get("state") or variation_state or "mixed")
        net = int(source.get("net") or 0)
        net_delta = _bounded(round(net / 8), -4, 4)
        primary_factor = 1.0 if domain in preferred else 0.45
        reception_modifier = next(
            (
                item
                for item in _as_list(day_stem_reception.get("domain_modifiers") if isinstance(day_stem_reception, dict) else [])
                if isinstance(item, dict) and str(item.get("domain") or "") == domain
            ),
            {},
        )
        reception_delta = int(reception_modifier.get("score_delta") or 0) if isinstance(reception_modifier, dict) else 0
        materiality_modifier = next(
            (
                item
                for item in _as_list(elemental_materiality.get("domain_modifiers") if isinstance(elemental_materiality, dict) else [])
                if isinstance(item, dict) and str(item.get("domain") or "") == domain
            ),
            {},
        )
        materiality_delta = int(materiality_modifier.get("score_delta") or 0) if isinstance(materiality_modifier, dict) else 0
        climate_modifier = next(
            (
                item
                for item in _as_list(climate_adjustment.get("domain_modifiers") if isinstance(climate_adjustment, dict) else [])
                if isinstance(item, dict) and str(item.get("domain") or "") == domain
            ),
            {},
        )
        climate_delta = int(climate_modifier.get("score_delta") or 0) if isinstance(climate_modifier, dict) else 0
        reality_delta = _bounded(round(int(reality_profile.get("score_delta") or 0) * primary_factor / 3), -3, 3)
        elemental_delta = round(base_delta * primary_factor * 0.65)
        score_delta = _bounded(
            elemental_delta + net_delta + reception_delta + materiality_delta + climate_delta + reality_delta,
            -8,
            8,
        )
        if str(reality_profile.get("state") or "") == "mixed" and score_delta > 7:
            score_delta = 7

        burden_gate = (
            str(pattern_status or "") == "caution"
            or str(variation_state or "") == "burden"
            or str(elemental_judgment.get("state") or "") in {"burden", "unstable"}
            or str(elemental_materiality.get("state") or "") == "burden"
            or str(climate_adjustment.get("state") or "") == "burden"
            or str(reality_profile.get("state") or "") == "burden"
        )
        if burden_gate:
            burden_caps_by_group = {
                "peer": {
                    "relationship": 2,
                    "money": -3,
                    "personality": 3,
                },
                "output": {
                    "career": 3,
                    "money": 2,
                    "love": 2,
                    "personality": 2,
                },
                "wealth": {
                    "money": 3,
                    "career": 2,
                    "marriage": 2,
                    "relationship": -1,
                },
                "officer": {
                    "career": 3,
                    "reputation": 2,
                    "marriage": 2,
                    "personality": 1,
                    "relationship": 1,
                },
                "resource": {
                    "personality": 4,
                    "career": 2,
                    "reputation": 2,
                    "relationship": 1,
                    "money": -2,
                    "love": 0,
                    "marriage": 0,
                },
            }
            group_caps = burden_caps_by_group.get(str(primary_group or ""), {})
            cap = group_caps.get(domain)
            if cap is None and domain not in preferred:
                cap = 1
            if cap is not None:
                score_delta = min(score_delta, cap)

        if score_delta >= 3:
            state = "support"
        elif score_delta <= -3:
            state = "burden"
        elif burden_gate:
            state = "burden" if score_delta <= -2 else "mixed"
        reasons = [
            "격국의 중심 작용이 이 영역으로 먼저 향합니다."
            if domain in preferred
            else "원국의 생극 자료에서 이 영역의 비중이 확인됩니다."
        ]
        if reception_delta:
            if reception_label:
                reasons.append(f"{reception_label} 수용 방식이 이 영역의 반응을 바꿉니다.")
            else:
                reasons.append("일간 수용값이 이 영역의 반응을 바꿉니다.")
        if materiality_delta:
            if materiality_label:
                reasons.append(f"{materiality_label} 물상이 이 영역의 성격을 구체화합니다.")
            else:
                reasons.append("오행 배합의 물상이 이 영역의 성격을 구체화합니다.")
        if climate_delta:
            if climate_label:
                reasons.append(f"{climate_label} 조후 작용이 이 영역의 지속성을 바꿉니다.")
            else:
                reasons.append("조후 작용이 이 영역의 지속성을 바꿉니다.")
        if reality_delta:
            reasons.append("투출·통근·지장간과 지지 관계가 현실에서 드러나는 정도를 가릅니다.")
        ordered.append(
            {
                "domain": domain,
                "label": DOMAIN_LABELS.get(domain, domain),
                "state": state,
                "net": net,
                "total": int(source.get("total") or 0),
                "score_delta": score_delta,
                "reception_delta": reception_delta,
                "materiality_delta": materiality_delta,
                "climate_delta": climate_delta,
                "reality_delta": reality_delta,
                "reason": " ".join(reasons),
            }
        )
        if len(ordered) >= 5:
            break
    return ordered


def _variation_summary(
    *,
    pattern_label: str,
    season_label: str,
    pattern_element_label: str,
    pattern_status: str,
    relation: str,
    variation_state: str,
) -> str:
    season = SEASON_LABELS.get(season_label, season_label)
    status_phrases = {
        "useful": f"{pattern_element_label} 기운이 격국의 활용도를 높입니다.",
        "caution": f"{pattern_element_label} 기운이 강해질수록 손실·압박 요인도 함께 커집니다.",
        "dominant": f"{pattern_element_label} 기운이 외부 활동에서 뚜렷하게 드러납니다.",
        "weak": f"{pattern_element_label} 기운은 잠재되어 있어 대운·세운의 발동 조건을 함께 봅니다.",
        "ordinary": f"{pattern_element_label} 기운은 보조 축으로 작용합니다.",
    }
    relation_phrases = {
        "same": "월령과 같은 오행이라 실제 사건으로 드러나는 속도가 빠릅니다.",
        "month_generates_pattern": "월령이 이 작용을 생하므로 순기능이 비교적 쉽게 살아납니다.",
        "pattern_generates_month": "격국의 기운이 월령 쪽으로 설기되므로 결과를 붙잡는 장치가 필요합니다.",
        "month_controls_pattern": "월령이 이 작용을 제어하므로 성과와 압박이 동시에 나타납니다.",
        "pattern_controls_month": "격국의 기운이 월령을 제어하므로 현실 조건을 다루는 능력이 중요합니다.",
        "indirect": "직접 생극보다 주변 배합을 통해 작용이 드러납니다.",
    }
    if variation_state == "support":
        judgment = "격국의 순기능이 비교적 선명하게 드러납니다."
    elif variation_state == "burden":
        judgment = "성과보다 손실·압박 요인을 먼저 분리해서 보아야 합니다."
    elif variation_state == "latent":
        judgment = "격국의 작용은 있으나 대운·세운에서 발동 조건을 따로 확인해야 합니다."
    else:
        judgment = "순기능과 압박이 함께 나타나므로 영역별 분리가 필요합니다."
    return " ".join(
        part
        for part in (
            f"{pattern_label}은 {season} 월령에서 판단합니다.",
            status_phrases.get(pattern_status, f"{pattern_element_label} 기운의 작용을 확인합니다."),
            relation_phrases.get(relation, ""),
            judgment,
        )
        if part
    )


def _pattern_variation(
    *,
    anchor: dict[str, Any],
    element_context: dict[str, Any],
    actions: list[dict[str, Any]],
    domain_synthesis: dict[str, Any],
) -> dict[str, Any]:
    primary_pattern = str(anchor.get("primary_pattern") or "")
    primary_pattern_label = str(anchor.get("primary_pattern_label") or primary_pattern)
    primary_ten_god = str(anchor.get("primary_ten_god") or "")
    primary_group = str(anchor.get("primary_group") or "")
    primary_group_label = str(anchor.get("primary_group_label") or primary_group)
    season_label = str(anchor.get("season_label") or "")
    month_element = str(anchor.get("month_element") or "")
    day_master_stem = str(anchor.get("day_master_stem") or "")
    day_master_element = str(element_context.get("day_master_element") or "")
    pattern_element = _role_element(day_master_element, primary_group)
    pattern_status = _pattern_element_status(element_context, pattern_element)
    relation = _month_pattern_element_relation(month_element, pattern_element)
    state = _variation_state(pattern_status, actions)
    score = _element_score_entry(element_context, pattern_element)
    reality_profile = _action_reality_profile(actions)
    elemental_judgment = _elemental_judgment(
        primary_group=primary_group,
        day_master_strength=str(element_context.get("day_master_strength") or ""),
        pattern_status=pattern_status,
        relation=relation,
        pattern_element=pattern_element,
        score=score,
        actions=actions,
        element_context=element_context,
        reality_profile=reality_profile,
    )
    if elemental_judgment["state"] in {"support", "burden"}:
        state = str(elemental_judgment["state"])
    elemental_materiality = _element_materiality_profile(
        primary_group=primary_group,
        day_master_element=day_master_element,
        month_element=month_element,
        pattern_element=pattern_element,
        relation=relation,
        pattern_status=pattern_status,
    )
    day_stem_reception = _day_stem_reception_profile(
        anchor=anchor,
        pattern_element=pattern_element,
        elemental_judgment=elemental_judgment,
    )
    climate_adjustment = _climate_adjustment_profile(
        primary_group=primary_group,
        pattern_element=pattern_element,
        element_context=element_context,
    )
    useful = [str(item) for item in _as_list(element_context.get("useful_elements"))]
    caution = [str(item) for item in _as_list(element_context.get("caution_elements"))]
    support_actions = [action for action in actions if action.get("contextual_state") == "support"]
    burden_actions = [action for action in actions if action.get("contextual_state") == "burden"]
    branch_pressure = [
        action
        for action in actions
        if (action.get("branch_relation_summary") or {}).get("counter_signals")
    ]

    pattern_element_label = ELEMENT_LABELS.get(pattern_element, pattern_element)
    month_element_label = ELEMENT_LABELS.get(month_element, month_element)
    basis_codes = [
        f"pattern_variation:pattern:{primary_pattern}",
        f"pattern_variation:group:{primary_group}",
        f"pattern_variation:day_stem:{day_master_stem}",
        f"pattern_variation:day_element:{day_master_element}",
        f"pattern_variation:pattern_element:{pattern_element}",
        f"pattern_variation:month_element:{month_element}",
        f"pattern_variation:season:{season_label}",
        f"pattern_variation:element_status:{pattern_status}",
        f"pattern_variation:month_relation:{relation}",
        f"pattern_variation:state:{state}",
        f"pattern_variation:elemental_state:{elemental_judgment['state']}",
        f"pattern_variation:elemental_score_delta:{elemental_judgment['score_delta']}",
        f"pattern_variation:climate_state:{climate_adjustment['state']}",
        f"pattern_variation:climate_score_delta:{climate_adjustment['score_delta']}",
        f"pattern_variation:reality_state:{reality_profile['state']}",
        f"pattern_variation:reality_score_delta:{reality_profile['score_delta']}",
        *[str(code) for code in _as_list(elemental_judgment.get("basis_codes"))],
        *[str(code) for code in _as_list(elemental_materiality.get("basis_codes"))],
        *[str(code) for code in _as_list(climate_adjustment.get("basis_codes"))],
        *[str(code) for code in _as_list(reality_profile.get("basis_codes"))],
        *[str(code) for code in _as_list(day_stem_reception.get("basis_codes") if day_stem_reception else [])],
    ]
    return {
        "variation_key": "|".join(
            [
                primary_pattern,
                primary_ten_god,
                day_master_stem,
                primary_group,
                day_master_element,
                pattern_element,
                month_element,
                season_label,
                pattern_status,
                relation,
                str(elemental_materiality.get("relation_type") or ""),
                str(climate_adjustment.get("state") or ""),
                state,
            ]
        ),
        "primary_pattern": primary_pattern,
        "primary_pattern_label": primary_pattern_label,
        "primary_ten_god": primary_ten_god,
        "primary_ten_god_label": TEN_GOD_LABELS.get(primary_ten_god, primary_ten_god),
        "primary_group": primary_group,
        "primary_group_label": primary_group_label,
        "season_label": season_label,
        "season_display": SEASON_LABELS.get(season_label, season_label),
        "day_master_stem": day_master_stem,
        "day_master_stem_label": STEM_LABELS.get(day_master_stem, day_master_stem),
        "day_master_element": day_master_element,
        "day_master_element_label": ELEMENT_LABELS.get(day_master_element, day_master_element),
        "month_element": month_element,
        "month_element_label": month_element_label,
        "pattern_element": pattern_element,
        "pattern_element_label": pattern_element_label,
        "pattern_element_status": pattern_status,
        "pattern_element_status_label": ELEMENT_STATUS_LABELS.get(pattern_status, pattern_status),
        "month_pattern_relation": relation,
        "month_pattern_relation_label": ELEMENT_RELATION_LABELS.get(relation, relation),
        "variation_state": state,
        "elemental_judgment": elemental_judgment,
        "elemental_materiality": elemental_materiality,
        "climate_adjustment": climate_adjustment,
        "day_stem_reception": day_stem_reception,
        "reality_profile": reality_profile,
        "pattern_element_score": {
            "ratio": score.get("ratio"),
            "seasonal_score": score.get("seasonal_score"),
            "state": score.get("state"),
            "exposure": score.get("exposure"),
        },
        "climate_profile": {
            "temperature_balance": element_context.get("temperature_balance"),
            "moisture_balance": element_context.get("moisture_balance"),
            "climate_needs": _unique([str(item) for item in _as_list(element_context.get("climate_needs"))]),
            "useful_elements": useful,
            "useful_element_labels": [ELEMENT_LABELS.get(item, item) for item in useful],
            "caution_elements": caution,
            "caution_element_labels": [ELEMENT_LABELS.get(item, item) for item in caution],
        },
        "favorable_modifiers": [
            *(
                [f"{pattern_element_label}이 조후상 필요한 오행으로 분류됩니다."]
                if pattern_element and pattern_element in useful
                else []
            ),
            *[
                f"{str(action.get('action_name') or action.get('rule_key'))} 작용이 격의 성립을 돕습니다."
                for action in support_actions[:3]
                if action.get("action_name") or action.get("rule_key")
            ],
        ][:5],
        "caution_modifiers": [
            *(
                [f"{pattern_element_label}이 과해지면 격의 부담 조건으로 바뀝니다."]
                if pattern_element and pattern_element in caution
                else []
            ),
            *[
                f"{str(action.get('action_name') or action.get('rule_key'))} 작용은 부담 조건을 함께 봅니다."
                for action in burden_actions[:3]
                if action.get("action_name") or action.get("rule_key")
            ],
            *(
                ["지지의 합충형파해가 필요한 작용을 흔드는 자료가 있습니다."]
                if branch_pressure
                else []
            ),
        ][:5],
        "domain_tilt": _variation_domain_tilt(
            primary_group=primary_group,
            domain_synthesis=domain_synthesis,
            variation_state=state,
            elemental_judgment=elemental_judgment,
            day_stem_reception=day_stem_reception,
            elemental_materiality=elemental_materiality,
            climate_adjustment=climate_adjustment,
            reality_profile=reality_profile,
            pattern_status=pattern_status,
        ),
        "judgment_summary": _variation_summary(
            pattern_label=primary_pattern_label,
            season_label=season_label,
            pattern_element_label=pattern_element_label,
            pattern_status=pattern_status,
            relation=relation,
            variation_state=state,
        ),
        "basis_codes": basis_codes,
    }


def _coverage(matrix: dict[str, Any], actions: list[dict[str, Any]], element_context: dict[str, Any]) -> dict[str, Any]:
    role_edges = [edge for edge in _as_list(matrix.get("role_edges")) if isinstance(edge, dict)]
    element_edges = [edge for edge in _as_list(matrix.get("element_edges")) if isinstance(edge, dict)]
    branch_relations = [edge for edge in _as_list(matrix.get("branch_relations")) if isinstance(edge, dict)]
    return {
        "month_anchor": bool((matrix.get("month_anchor") or {}).get("month_branch")),
        "gyeokguk_actions": len(actions),
        "role_edges": len(role_edges),
        "element_edges": len(element_edges),
        "branch_relations": len(branch_relations),
        "useful_element_edges": len(_as_list(element_context.get("useful_element_edges"))),
        "caution_element_edges": len(_as_list(element_context.get("caution_element_edges"))),
        "climate": bool(element_context.get("temperature_balance") or element_context.get("moisture_balance")),
    }


def build_gyeokguk_contextual_profile(chart_structure: Any) -> dict[str, Any]:
    """Build a combined profile from existing engine layers."""

    gyeokguk_profile = getattr(chart_structure, "gyeokguk_profile", None)
    element_profile = getattr(chart_structure, "element_profile", None)
    month_profile = getattr(chart_structure, "month_governance_profile", None)
    cycle_profile = getattr(chart_structure, "cycle_regulation_profile", {}) or {}
    matrix = cycle_profile.get("principle_matrix") if isinstance(cycle_profile, dict) else {}
    if not isinstance(matrix, dict):
        matrix = {}

    day_master_element = str(getattr(element_profile, "day_master_element", "") or "")
    actions = _contextual_actions(gyeokguk_profile, matrix, day_master_element) if gyeokguk_profile is not None else []
    element_context = _element_context(element_profile, matrix) if element_profile is not None else {}
    domain_synthesis = _domain_synthesis(actions, matrix)
    month_anchor = dict(matrix.get("month_anchor") or {})

    primary_pattern = str(getattr(gyeokguk_profile, "primary_pattern", "") or "")
    primary_ten_god = str(getattr(gyeokguk_profile, "primary_ten_god", "") or "")
    anchor = {
        "primary_pattern": primary_pattern,
        "primary_pattern_label": PATTERN_LABELS.get(primary_pattern, primary_pattern),
        "primary_ten_god": primary_ten_god,
        "primary_ten_god_label": TEN_GOD_LABELS.get(primary_ten_god, primary_ten_god),
        "primary_group": str(getattr(gyeokguk_profile, "primary_group", "") or ""),
        "primary_group_label": ROLE_LABELS.get(str(getattr(gyeokguk_profile, "primary_group", "") or ""), ""),
        "formation_state": str(getattr(gyeokguk_profile, "formation_state", "") or ""),
        "clarity_state": str(getattr(gyeokguk_profile, "clarity_state", "") or ""),
        "day_master_stem": str(getattr(chart_structure, "day_master_stem", "") or ""),
        "month_branch": str(getattr(chart_structure, "month_branch", "") or ""),
        "month_element": str(getattr(month_profile, "month_element", "") or month_anchor.get("month_element") or ""),
        "month_command_stem": str(getattr(month_profile, "month_command_stem", "") or month_anchor.get("month_command_stem") or ""),
        "month_command_ten_god": str(getattr(month_profile, "month_command_ten_god", "") or month_anchor.get("month_command_ten_god") or ""),
        "month_command_group": str(getattr(month_profile, "month_command_group", "") or month_anchor.get("month_command_group") or ""),
        "regular_pattern": str(getattr(month_profile, "regular_pattern", "") or month_anchor.get("regular_pattern") or ""),
        "season_label": str(getattr(chart_structure, "season_label", "") or ""),
    }
    pattern_variation = _pattern_variation(
        anchor=anchor,
        element_context=element_context,
        actions=actions,
        domain_synthesis=domain_synthesis,
    )
    coverage = _coverage(matrix, actions, element_context)
    action_distribution = _action_distribution(actions)
    domain_action_map = _domain_action_map(actions, domain_synthesis)
    engine_readiness = _engine_readiness(
        coverage=coverage,
        actions=actions,
        action_distribution=action_distribution,
        domain_action_map=domain_action_map,
        pattern_variation=pattern_variation,
    )
    basis_codes = [
        f"gyeokguk_contextual:pattern:{primary_pattern}",
        f"gyeokguk_contextual:ten_god:{primary_ten_god}",
        f"gyeokguk_contextual:day_element:{day_master_element}",
        f"gyeokguk_contextual:month_branch:{getattr(chart_structure, 'month_branch', '')}",
        f"gyeokguk_contextual:season:{getattr(chart_structure, 'season_label', '')}",
        *[str(code) for code in _as_list(matrix.get("basis_codes"))[:20]],
        *[str(code) for action in actions[:4] for code in _as_list(action.get("basis_codes"))[:4]],
    ]

    return {
        "version": GYEOKGUK_CONTEXTUAL_VERSION,
        "context_key": "|".join(
            [
                primary_pattern,
                primary_ten_god,
                day_master_element,
                str(getattr(chart_structure, "month_branch", "") or ""),
                str(getattr(chart_structure, "season_label", "") or ""),
                str(getattr(element_profile, "temperature_balance", "") or ""),
                str(getattr(element_profile, "moisture_balance", "") or ""),
            ]
        ),
        "anchor": anchor,
        "month_anchor": month_anchor,
        "element_context": element_context,
        "pattern_variation": pattern_variation,
        "contextual_actions": actions,
        "domain_synthesis": domain_synthesis,
        "source_reality": matrix.get("source_reality") if isinstance(matrix.get("source_reality"), dict) else {},
        "signal_links": matrix.get("signal_links") if isinstance(matrix.get("signal_links"), dict) else {},
        "action_distribution": action_distribution,
        "domain_action_map": domain_action_map,
        "engine_readiness": engine_readiness,
        "coverage": coverage,
        "basis_codes": _unique(basis_codes)[:40],
    }
