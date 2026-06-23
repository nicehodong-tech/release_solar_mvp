"""Domain event-packet generation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .combinations import signals_for_domain
from .constants import (
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    DOMAIN_ORDER,
    TEN_GOD_GROUPS,
)
from .cycle_regulation import build_cycle_regulation_profile
from .models import ChartStructure, Domain, EventPacket, FlowSignal, RelationshipStatus, SubPeriodSignal
from .month_governance import evaluate_month_governed_signal, governance_event_adjustment
from .relation_polarity import branch_relation_polarity, relation_activated_elements
from .refined_interpretation_values import (
    REFINED_EVENT_ACTION_BY_TYPE,
    REFINED_EVENT_KEYWORDS_BY_TYPE,
    REFINED_EVENT_RISK_BY_TYPE,
)
from .rendering import render_event_preview
from .templates import build_template_slots, select_common_template, select_domain_template, select_type_template


def _clip(value: float) -> int:
    return max(0, min(100, round(value)))


def _confidence(probability: int, basis_count: int, counter_count: int, boundary_sensitive: bool) -> str:
    adjusted = probability + min(10, basis_count * 2) - min(12, counter_count * 3)
    if boundary_sensitive:
        adjusted -= 7
    if adjusted >= 82:
        return "high"
    if adjusted >= 70:
        return "medium_high"
    if adjusted >= 55:
        return "medium"
    if adjusted >= 42:
        return "low"
    return "restricted"


def _expression_strength(probability: int, risk: int, confidence: str) -> str:
    if confidence in {"high", "medium_high"} and probability >= 76 and risk < 72:
        return "strong"
    if confidence in {"medium_high", "medium"} and probability >= 62:
        return "clear"
    if confidence == "restricted":
        return "restricted"
    return "soft"


def _conflict_status(risk: int, counter_count: int) -> str:
    if risk >= 75 or counter_count >= 3:
        return "strong"
    if risk >= 58 or counter_count >= 1:
        return "mild"
    return "none"


def _event_type(domain: str, opportunity: int, risk: int, change: int, feature_axes: list[dict[str, Any]] | None = None) -> str:
    feature_axes = feature_axes or []
    if domain == "money":
        deal_selection = _axis_score(feature_axes, "deal_selection")
        loss_avoidance = _axis_score(feature_axes, "loss_avoidance")
        late_growth = _axis_score(feature_axes, "late_life_money_growth")
        if opportunity >= 68 and risk >= 58:
            return "managed_income_expansion"
        if opportunity >= 68 or (late_growth >= 70 and opportunity >= 62):
            return "income_growth"
        if risk >= 62 or loss_avoidance < 45:
            return "cashflow_defense"
        if deal_selection >= 64 and opportunity >= 60 and risk >= 50:
            return "managed_income_expansion"
        if change >= 58:
            return "income_structure_change"
        return "money_flow_adjustment"
    if domain == "career":
        reputation = _axis_score(feature_axes, "reputation_maintenance")
        responsibility = _axis_score(feature_axes, "responsibility_capacity")
        if risk >= 68 and opportunity < 74:
            return "responsibility_pressure"
        if opportunity >= 70 and change >= 62:
            return "role_expansion_or_transition"
        if risk >= 72 or (responsibility < 45 and risk >= 58):
            return "responsibility_pressure"
        if opportunity >= 68 or (reputation >= 66 and opportunity >= 60):
            return "career_recognition"
        if change >= 66:
            return "work_environment_change"
        return "career_pace_adjustment"
    if domain == "love":
        relationship = _axis_score(feature_axes, "relationship_stability")
        boundary = _axis_score(feature_axes, "boundary_management")
        communication = _axis_score(feature_axes, "communication_expression")
        attraction = _axis_score(feature_axes, "attraction_selectivity")
        progression = _axis_score(feature_axes, "relationship_progression")
        affection = _axis_score(feature_axes, "affection_expression")
        recovery = _axis_score(feature_axes, "crisis_recovery")
        conflict_recovery = _axis_score(feature_axes, "conflict_recovery")
        interpersonal = _axis_score(feature_axes, "interpersonal_influence")
        if opportunity >= 70 and risk < 62 and progression >= 58:
            return "relationship_opening"
        if risk >= 68 or (conflict_recovery < 45 and risk >= 58):
            return "relationship_friction"
        if relationship < 45 or boundary < 45:
            return "relationship_boundary_check"
        if (communication >= 64 or affection >= 64) and opportunity >= 56:
            return "relationship_expression_alignment"
        if (recovery >= 64 or conflict_recovery >= 64) and risk >= 45:
            return "relationship_recovery_check"
        if (interpersonal >= 64 or progression >= 64) and opportunity >= 58:
            return "relationship_contact_increase"
        if attraction < 45 and opportunity >= 58:
            return "relationship_with_conditions"
        if risk >= 55 or (opportunity >= 60 and risk >= 50):
            return "relationship_with_conditions"
        return "relationship_temperature_shift"
    if domain == "marriage":
        marriage = _axis_score(feature_axes, "marriage_stability")
        relationship = _axis_score(feature_axes, "relationship_stability")
        boundary = _axis_score(feature_axes, "boundary_management")
        decision_consistency = _axis_score(feature_axes, "decision_consistency")
        practical_planning = _axis_score(feature_axes, "practical_planning")
        asset_retention = _axis_score(feature_axes, "asset_retention")
        family_responsibility = _axis_score(feature_axes, "family_responsibility")
        spouse_match = _axis_score(feature_axes, "spouse_match_quality")
        timing_readiness = _axis_score(feature_axes, "marriage_timing_readiness")
        household = _axis_score(feature_axes, "household_stability")
        conflict_recovery = _axis_score(feature_axes, "conflict_recovery")
        if opportunity >= 72 and risk < 62 and timing_readiness >= 58:
            return "marriage_stability_opening"
        if risk >= 68 or (conflict_recovery < 45 and risk >= 58):
            return "marriage_pressure"
        if relationship < 45 or boundary < 45 or family_responsibility < 45 or spouse_match < 45:
            return "marriage_condition_check"
        if (marriage >= 64 or spouse_match >= 64) and opportunity >= 58:
            return "marriage_commitment_readiness"
        if (practical_planning >= 64 or household >= 64) and risk < 58:
            return "marriage_practical_planning"
        if asset_retention < 45:
            return "marriage_asset_condition_check"
        if decision_consistency >= 64 and opportunity >= 55:
            return "marriage_decision_alignment"
        if risk >= 55 or (opportunity >= 60 and risk >= 50):
            return "marriage_condition_check"
        return "marriage_timing_adjustment"
    raise ValueError(f"Unsupported domain: {domain}")


EVENT_TEXT = {
    "money": {
        "form": "수입, 계약, 자산 배분, 자금 운용과 관련된 사건",
        "realization": "성과나 역할이 평가를 받은 뒤 금전 이동으로 이어지는 과정",
        "risk": "확장 속도가 계약 명확성, 지출 통제, 분배 균형을 앞질러 생기는 부담",
        "action": "확장 전에 계약 기준과 현금 여유분을 눈에 보이게 관리하는 것",
        "topic": "계약 명확성, 지출, 분배, 고정비",
        "scene": "재물은 막연한 기회보다 구체적인 역할, 프로젝트, 거래를 통해 움직입니다",
    },
    "career": {
        "form": "역할 변화, 책임, 평가, 프로젝트, 조직과 관련된 사건",
        "realization": "책임이나 성과가 드러난 뒤 사회적 평가가 따라오는 과정",
        "risk": "권한, 일정, 평판, 책임 압박이 과해져 생기는 부담",
        "action": "역할 경계와 평가 기준을 명확히 하는 것",
        "topic": "권한 충돌, 업무량, 평판, 실행 지연",
        "scene": "직업운은 맡겨진 책임, 드러나는 성과, 사회적 평가를 통해 표면화됩니다",
    },
    "love": {
        "form": "만남, 관계 진전, 감정 접촉, 관계 마찰과 관련된 사건",
        "realization": "접촉 빈도가 늘고 감정적 선택이 점차 뚜렷해지는 과정",
        "risk": "끌림과 생활 기준의 불일치가 함께 움직이며 속도를 불안정하게 만드는 부담",
        "action": "끌림과 생활 기준 점검을 분리해서 보는 것",
        "topic": "속도, 감정 기대, 애매함, 제삼자 변수",
        "scene": "연애운은 접촉, 호감, 생활 기준의 차이에서 움직임이 드러납니다",
    },
    "marriage": {
        "form": "결혼 시기, 배우자 조건, 가족 조건, 생활 안정과 관련된 사건",
        "realization": "관계 조건이 현실적인 논의로 넘어가 약속과 책임을 다루게 되는 과정",
        "risk": "가족, 돈, 주거, 역할 기대가 관계를 압박하며 생기는 부담",
        "action": "약속 전에 생활 조건과 역할 기대를 점검하는 것",
        "topic": "가족 조건, 주거, 돈, 역할 분담",
        "scene": "결혼운은 애정이 시기, 주거, 가족 문제로 옮겨질 때 실제 논의가 시작됩니다",
    },
}


EVENT_KEYWORDS_BY_TYPE = {
    "income_growth": ["성과의 금전 전환", "지급 조건", "거래 성사", "보상 실현"],
    "managed_income_expansion": ["관리형 수입 확대", "계약 범위", "정산 기준", "지출 한도"],
    "cashflow_defense": ["현금 방어", "고정비 축소", "손실 차단", "예비 자금"],
    "income_structure_change": ["수입 구조 전환", "새 수입원", "거래 방식", "역할 보상"],
    "money_flow_adjustment": ["재정 재배치", "소비 재정리", "기회 대비", "자금 확보"],
    "role_expansion_or_transition": ["역할 확대", "직무 전환", "권한 범위", "평가 기준"],
    "career_recognition": ["공식 인정", "성과 평가", "책임 부여", "보상 기준"],
    "responsibility_pressure": ["책임 압박", "일정 부담", "권한 부족", "상급자 요구"],
    "work_environment_change": ["업무 재배치", "조직 변동", "소속 변화", "역할 재설정"],
    "career_pace_adjustment": ["우선순위 재정리", "업무 속도 조절", "기준 정리", "무리한 확장 제한"],
    "relationship_opening": ["새 인연", "호감 형성", "만남의 계기", "관심 확인"],
    "relationship_with_conditions": ["관계 조건", "연락 방식", "기대치", "만남 속도"],
    "relationship_friction": ["감정 충돌", "기대 차이", "거리 조정", "책임 범위"],
    "relationship_boundary_check": ["거리감", "개인 영역", "책임 범위", "관계 부담"],
    "relationship_expression_alignment": ["표현 방식", "연락 빈도", "호감 전달", "오해 예방"],
    "relationship_recovery_check": ["오해 정리", "다시 대화", "반복 문제", "관계 회복"],
    "relationship_contact_increase": ["연락 증가", "만남 빈도", "호감 확인", "관계 방향"],
    "relationship_temperature_shift": ["감정 반응 변화", "연락 의지", "선택 기준", "관계 지속 여부"],
    "marriage_stability_opening": ["결혼 이야기", "생활 합의", "가족 조건", "책임 범위"],
    "marriage_condition_check": ["현실 조건", "주거 문제", "가족 조건", "역할 분담"],
    "marriage_pressure": ["결정 부담", "가족 변수", "경제 조건", "시점 압박"],
    "marriage_commitment_readiness": ["약속 준비", "결혼 의사", "생활 합의", "책임 확인"],
    "marriage_practical_planning": ["주거 계획", "재정 계획", "역할 분담", "일정 조율"],
    "marriage_asset_condition_check": ["자산 기준", "지출 기준", "부채 확인", "재정 합의"],
    "marriage_decision_alignment": ["결정 속도", "가족 협의", "약속 시점", "서로의 준비"],
    "marriage_timing_adjustment": ["시점 재검토", "생활 조건", "관계 안정", "준비 상태"],
}

EVENT_ACTION_BY_TYPE = {
    "income_growth": "해낸 일을 금액으로 확정하는 것",
    "managed_income_expansion": "계약 범위를 먼저 분명히 정하는 것",
    "cashflow_defense": "현금 여유를 먼저 지키는 것",
    "income_structure_change": "새 수입원이 기존 역할과 보상 기준을 어떻게 바꾸는지 계산하는 것",
    "money_flow_adjustment": "소비, 저축, 투자, 예비 자금의 순서를 다시 정하는 것",
    "role_expansion_or_transition": "결정권이 따르는 역할 변화",
    "career_recognition": "성과가 보상 기준과 다음 책임으로 정리되는 것",
    "responsibility_pressure": "책임이 커질수록 일정, 권한, 보고 기준을 좁혀 두는 것",
    "work_environment_change": "조직 변화 속에서 맡을 일과 맡지 않을 일을 분명히 나누는 것",
    "career_pace_adjustment": "무리한 확장보다 우선순위와 실행 속도를 다시 정하는 것",
    "relationship_opening": "호감이 생겨도 만남의 속도와 생활 기준을 함께 확인하는 것",
    "relationship_with_conditions": "감정보다 연락 방식, 생활 거리, 기대치를 먼저 정리하는 것",
    "relationship_friction": "기대치를 말로 정리하는 것",
    "relationship_boundary_check": "서로 편한 거리, 연락 빈도, 개인 영역을 분명히 합의하는 것",
    "relationship_expression_alignment": "호감의 크기보다 표현 방식과 연락 속도를 정리하는 것",
    "relationship_recovery_check": "오해를 풀되 같은 문제가 반복되지 않을 기준을 새로 세우는 것",
    "relationship_contact_increase": "접촉이 늘어날수록 관계의 방향과 기대치를 확인하는 것",
    "relationship_temperature_shift": "감정 반응이 달라질 때 결정을 서두르지 않고 확인 시간을 두는 것",
    "marriage_stability_opening": "약속을 정하기 전에 돈의 기준을 정리하는 것",
    "marriage_condition_check": "주거 조건을 감정만으로 보지 않고 따로 점검하는 것",
    "marriage_pressure": "결혼 결정을 서두르라는 압박을 받는 것",
    "marriage_commitment_readiness": "결혼 의사와 생활 합의를 같은 자리에서 확인하는 것",
    "marriage_practical_planning": "주거, 재정, 역할 분담을 숫자와 일정으로 정리하는 것",
    "marriage_asset_condition_check": "자산, 부채, 지출 기준을 약속 전에 투명하게 정리하는 것",
    "marriage_decision_alignment": "약속 시점, 가족 협의, 두 사람의 결정 속도를 함께 정리하는 것",
    "marriage_timing_adjustment": "관계 안정과 생활 조건이 정리될 때까지 시점을 조정하는 것",
}

EVENT_RISK_BY_TYPE = {
    "income_growth": "받을 금액과 나눌 몫을 흐리게 두어 손에 남는 돈이 줄어드는 상황",
    "managed_income_expansion": "수입은 커지지만 정산 방식과 지출 통제가 늦어지는 상황",
    "cashflow_defense": "예비 자금이 약한 상태에서 새 지출이 늘어 회복 시간이 길어지는 상황",
    "income_structure_change": "돈이 들어오는 방식이 바뀌며 기존 역할과 새 조건이 충돌하는 상황",
    "money_flow_adjustment": "소비 조절이 늦어 다음 기회에 쓸 자금이 묶이는 상황",
    "role_expansion_or_transition": "역할은 커지지만 권한과 평가 기준이 늦게 정해지는 상황",
    "career_recognition": "성과가 보이는 만큼 책임과 기대가 함께 커지는 상황",
    "responsibility_pressure": "권한보다 책임이 먼저 커지고 일정 압박이 누적되는 상황",
    "work_environment_change": "조직 변화 속에서 업무 경계가 불분명해지고 책임이 넓어지는 상황",
    "career_pace_adjustment": "기준 정리보다 실행 속도가 앞서 피로와 지연이 쌓이는 상황",
    "relationship_opening": "호감은 빨리 생기지만 생활 조건과 관계 속도가 맞지 않는 상황",
    "relationship_with_conditions": "기대는 커지지만 연락 방식과 생활 기준이 늦게 맞춰지는 상황",
    "relationship_friction": "감정 반응이 앞서 관계의 거리가 흔들리는 상황",
    "relationship_boundary_check": "서로의 거리감이 맞지 않아 오해와 피로가 반복되는 상황",
    "relationship_expression_alignment": "감정 표현의 속도와 연락 방식이 달라 불안이 생기는 상황",
    "relationship_recovery_check": "오해를 풀어도 같은 기대 차이가 다시 반복되는 상황",
    "relationship_contact_increase": "접촉은 늘지만 관계의 방향이 분명하지 않아 피로가 생기는 상황",
    "relationship_temperature_shift": "감정 반응이 달라져 선택이 늦어지는 상황",
    "marriage_stability_opening": "약속은 가까워져도 돈의 기준이 늦게 맞춰지는 상황",
    "marriage_condition_check": "주거 조건이 감정적 확신을 압박하는 상황",
    "marriage_pressure": "주변 압박과 현실 기준의 충돌이 결혼 결정을 서두르게 만드는 상황",
    "marriage_commitment_readiness": "의사는 분명해도 생활비와 주거 문제가 늦게 정리되는 상황",
    "marriage_practical_planning": "계획은 정해지지만 돈과 역할 분담이 한쪽으로 몰리는 상황",
    "marriage_asset_condition_check": "자산 기준이 불분명해 신뢰가 흔들리는 상황",
    "marriage_decision_alignment": "결정 속도와 가족 협의가 맞지 않아 약속이 지연되는 상황",
    "marriage_timing_adjustment": "시점을 조정하는 과정에서 관계 안정감이 약해지는 상황",
}

EVENT_KEYWORDS_BY_TYPE = {
    **EVENT_KEYWORDS_BY_TYPE,
    **REFINED_EVENT_KEYWORDS_BY_TYPE,
}
EVENT_ACTION_BY_TYPE = {
    **EVENT_ACTION_BY_TYPE,
    **REFINED_EVENT_ACTION_BY_TYPE,
}
EVENT_RISK_BY_TYPE = {
    **EVENT_RISK_BY_TYPE,
    **REFINED_EVENT_RISK_BY_TYPE,
}

FEATURE_AXES_BY_DOMAIN = {
    "money": [
        "money_potential",
        "income_expansion",
        "liquidity_stability",
        "reward_claim_strength",
        "asset_retention",
        "ownership_clarity",
        "shared_asset_boundary",
        "investment_trading_sense",
        "deal_selection",
        "loss_avoidance",
        "late_life_money_growth",
        "money_attitude",
        "practical_planning",
        "spending_control",
        "business_expansion",
    ],
    "career": [
        "social_success_potential",
        "career_achievement",
        "work_domain_fit",
        "responsibility_capacity",
        "role_authority_alignment",
        "reputation_maintenance",
        "self_direction",
        "decision_consistency",
        "honor_recognition",
        "promotion_visibility",
        "leadership_potential",
        "organization_adaptability",
        "academic_expertise",
        "change_adaptability",
    ],
    "love": [
        "interpersonal_influence",
        "attraction_selectivity",
        "relationship_progression",
        "affection_expression",
        "affection_receptivity",
        "emotional_alignment",
        "relationship_stability",
        "communication_expression",
        "boundary_management",
        "misunderstanding_prevention",
        "conflict_recovery",
        "reunion_closure",
        "crisis_recovery",
    ],
    "marriage": [
        "marriage_stability",
        "spouse_match_quality",
        "spouse_support_benefit",
        "marriage_timing_readiness",
        "household_stability",
        "household_finance_alignment",
        "relationship_stability",
        "conflict_recovery",
        "family_responsibility",
        "inlaw_boundary_strength",
        "marriage_crisis_management",
        "boundary_management",
        "decision_consistency",
        "practical_planning",
        "asset_retention",
        "money_attitude",
        "crisis_recovery",
    ],
}


def _feature_axes_for_domain(structure: ChartStructure, domain: str) -> list[dict[str, Any]]:
    axes = structure.life_feature_profile.axes
    payload: list[dict[str, Any]] = []
    for key in FEATURE_AXES_BY_DOMAIN[domain]:
        axis = axes.get(key)
        if axis is None:
            continue
        payload.append(
            {
                "key": axis.key,
                "category": axis.category,
                "label": axis.label,
                "score": axis.score,
                "percentile_label": axis.percentile_label,
                "strength_label": axis.strength_label,
                "confidence": axis.confidence,
                "basis_codes": list(axis.basis_codes),
                "counter_signals": list(axis.counter_signals),
                "customer_sentence": axis.customer_sentence,
            }
        )
    return payload


def _axis_score(feature_axes: list[dict[str, Any]], key: str, default: int = 50) -> int:
    for axis in feature_axes:
        if axis.get("key") == key:
            return int(axis.get("score") or default)
    return default


FEATURE_AXIS_ADJUSTMENT_LIMITS = {
    "opportunity": (0, 12),
    "risk": (-6, 18),
    "change": (0, 4),
    "probability": (-4, 10),
}

EVENT_PACKET_ADJUSTMENT_LIMITS = {
    "opportunity": (0, 12),
    "risk": (-6, 18),
    "change": (0, 4),
    "probability": (-4, 10),
}

CYCLE_REGULATION_ADJUSTMENT_LIMITS = {
    "opportunity": (-4, 10),
    "risk": (-8, 12),
    "change": (0, 6),
    "probability": (-6, 8),
}

DOMAIN_POSITION_PRIORITY: dict[str, tuple[str, ...]] = {
    "money": ("month", "hour", "day", "year"),
    "career": ("month", "year", "hour", "day"),
    "love": ("day", "hour", "month", "year"),
    "marriage": ("day", "month", "hour", "year"),
}

POSITION_RELEVANCE_WEIGHTS = (1.0, 0.72, 0.45, 0.28)

DOMAIN_TEN_GOD_GROUP_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "money": {
        "wealth": {"opportunity": 5, "probability": 2},
        "output": {"opportunity": 3, "change": 2, "probability": 1},
        "officer": {"opportunity": 1, "risk": -1, "probability": 1},
        "resource": {"risk": -2, "probability": 1},
        "peer": {"risk": 5, "change": 1, "probability": -1},
    },
    "career": {
        "officer": {"opportunity": 5, "change": 1, "probability": 2},
        "resource": {"opportunity": 3, "risk": -1, "probability": 1},
        "output": {"opportunity": 3, "change": 2, "probability": 1},
        "wealth": {"opportunity": 2, "probability": 1},
        "peer": {"risk": 2, "change": 2},
    },
    "love": {
        "wealth": {"opportunity": 3, "probability": 1},
        "officer": {"opportunity": 3, "probability": 1},
        "output": {"opportunity": 3, "change": 1},
        "resource": {"risk": -2, "probability": 1},
        "peer": {"risk": 3, "change": 2, "probability": -1},
    },
    "marriage": {
        "officer": {"opportunity": 4, "probability": 2},
        "wealth": {"opportunity": 3, "probability": 1},
        "resource": {"risk": -2, "probability": 1},
        "output": {"change": 1, "risk": 1},
        "peer": {"risk": 3, "change": 1, "probability": -1},
    },
}

PATTERN_GROUP_SUPPORT_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "money": {
        "wealth": {"opportunity": 5, "probability": 3},
        "output": {"opportunity": 4, "change": 1, "probability": 2},
        "officer": {"risk": -2, "probability": 1},
        "resource": {"risk": -2, "probability": 1},
        "peer": {"opportunity": 1, "risk": -1, "probability": 1},
    },
    "career": {
        "officer": {"opportunity": 5, "probability": 3},
        "resource": {"opportunity": 4, "risk": -1, "probability": 2},
        "output": {"opportunity": 3, "change": 2, "probability": 2},
        "wealth": {"opportunity": 2, "probability": 1},
        "peer": {"opportunity": 1, "risk": -1},
    },
    "love": {
        "wealth": {"opportunity": 3, "probability": 1},
        "officer": {"opportunity": 3, "probability": 1},
        "output": {"opportunity": 3, "change": 1},
        "resource": {"risk": -2, "probability": 1},
        "peer": {"risk": -1, "probability": 1},
    },
    "marriage": {
        "officer": {"opportunity": 4, "probability": 2},
        "wealth": {"opportunity": 3, "probability": 1},
        "resource": {"risk": -2, "probability": 1},
        "output": {"opportunity": 1, "change": 1},
        "peer": {"risk": -1, "probability": 1},
    },
}

PATTERN_GROUP_PRESSURE_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "money": {
        "wealth": {"risk": 4, "probability": -1},
        "output": {"risk": 2, "change": 1},
        "officer": {"risk": 2},
        "resource": {"risk": 2, "probability": -1},
        "peer": {"risk": 5, "probability": -2},
    },
    "career": {
        "officer": {"risk": 5, "probability": -1},
        "resource": {"risk": 2},
        "output": {"risk": 3, "change": 1},
        "wealth": {"risk": 2},
        "peer": {"risk": 3, "change": 1},
    },
    "love": {
        "wealth": {"risk": 2},
        "officer": {"risk": 3},
        "output": {"risk": 2, "change": 1},
        "resource": {"risk": 2},
        "peer": {"risk": 4, "probability": -1},
    },
    "marriage": {
        "officer": {"risk": 4, "probability": -1},
        "wealth": {"risk": 3},
        "resource": {"risk": 2},
        "output": {"risk": 2, "change": 1},
        "peer": {"risk": 4, "probability": -1},
    },
}

PATTERN_REASON_SUPPORT_EFFECTS: dict[str, dict[str, float]] = {
    "peer_pattern_needs_officer": {"risk": -2, "probability": 1},
    "peer_pattern_uses_output": {"opportunity": 2, "change": 1, "probability": 1},
    "yangren_needs_officer_control": {"risk": -3, "probability": 1},
    "yangren_uses_output_release": {"opportunity": 2, "change": 1, "risk": -1},
    "eating_god_generates_wealth": {"opportunity": 3, "probability": 1},
    "eating_god_results_enter_responsibility": {"opportunity": 2, "risk": -1, "probability": 1},
    "hurting_officer_generates_wealth": {"opportunity": 3, "change": 1},
    "hurting_officer_needs_resource_refinement": {"risk": -2, "probability": 1},
    "indirect_wealth_supports_officer": {"opportunity": 2, "risk": -1, "probability": 1},
    "output_sources_indirect_wealth": {"opportunity": 3, "change": 1},
    "direct_wealth_supports_officer": {"risk": -2, "probability": 2},
    "output_sources_direct_wealth": {"opportunity": 2, "probability": 1},
    "eating_god_controls_seven_killings": {"risk": -3, "opportunity": 1, "probability": 1},
    "seven_killings_transforms_to_resource": {"risk": -2, "probability": 2},
    "officer_resource_sequence": {"risk": -2, "probability": 2},
    "wealth_supports_officer": {"opportunity": 2, "probability": 1},
    "wealth_regulates_indirect_resource": {"risk": -2, "probability": 1},
    "resource_turns_into_output": {"opportunity": 2, "change": 1},
    "wealth_regulates_direct_resource": {"risk": -2, "probability": 1},
    "resource_turns_into_visible_result": {"opportunity": 2, "change": 1, "probability": 1},
}

PATTERN_REASON_PRESSURE_EFFECTS: dict[str, dict[str, float]] = {
    "peer_pattern_excess_peer": {"risk": 3, "probability": -1},
    "peer_pattern_resource_overfeeds": {"risk": 2, "probability": -2},
    "yangren_excess_competition": {"risk": 4, "change": 1, "probability": -1},
    "yangren_resource_overfeeds": {"risk": 3, "probability": -2},
    "resource_can_damage_eating_god": {"risk": 2, "probability": -2},
    "hurting_officer_clashes_with_officer": {"risk": 3, "change": 1, "probability": -1},
    "peer_competes_for_indirect_wealth": {"risk": 3, "change": 1, "probability": -1},
    "resource_slows_wealth_movement": {"risk": 2, "probability": -2},
    "peer_competes_for_direct_wealth": {"risk": 3, "probability": -1},
    "resource_slows_wealth_accumulation": {"risk": 2, "probability": -2},
    "wealth_feeds_seven_killings": {"risk": 3, "probability": -1},
    "killing_pressure_excess": {"risk": 3, "probability": -1},
    "output_harms_officer_order": {"risk": 3, "change": 1, "probability": -1},
    "peer_disrupts_officer_order": {"risk": 2, "change": 1, "probability": -1},
    "indirect_resource_excess": {"risk": 2, "probability": -2},
    "direct_resource_excess": {"risk": 2, "probability": -2},
    "resource_overprotects_day_master": {"risk": 2, "probability": -1},
}


def _bounded_feature_axis_adjustments(
    *,
    opportunity: int,
    risk: int,
    change: int,
    probability: int,
    basis_codes: list[str],
    counter_signals: list[str],
) -> dict[str, Any]:
    lower_opportunity, upper_opportunity = FEATURE_AXIS_ADJUSTMENT_LIMITS["opportunity"]
    lower_risk, upper_risk = FEATURE_AXIS_ADJUSTMENT_LIMITS["risk"]
    lower_change, upper_change = FEATURE_AXIS_ADJUSTMENT_LIMITS["change"]
    lower_probability, upper_probability = FEATURE_AXIS_ADJUSTMENT_LIMITS["probability"]
    return {
        "opportunity": max(lower_opportunity, min(upper_opportunity, opportunity)),
        "risk": max(lower_risk, min(upper_risk, risk)),
        "change": max(lower_change, min(upper_change, change)),
        "probability": max(lower_probability, min(upper_probability, probability)),
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _bounded_adjusted_score(
    raw_value: int,
    adjusted_value: int,
    metric: str,
    limits: dict[str, tuple[int, int]] | None = None,
) -> int:
    lower, upper = (limits or FEATURE_AXIS_ADJUSTMENT_LIMITS)[metric]
    adjustment = adjusted_value - raw_value
    if adjustment > 0:
        remaining_room = max(0, 100 - raw_value)
        dynamic_upper = min(upper, max(3, round(remaining_room * 0.72)))
        bounded_adjustment = min(dynamic_upper, adjustment)
    else:
        bounded_adjustment = max(lower, adjustment)
    return _clip(raw_value + bounded_adjustment)


def _scale_delta(value: float, weight: float) -> float:
    if value == 0:
        return 0
    scaled = value * weight
    if 0 < scaled < 1:
        return 1
    if -1 < scaled < 0:
        return -1
    return scaled


def _apply_group_effect(
    totals: dict[str, float],
    *,
    domain: str,
    group: str,
    weight: float,
    basis_code: str,
    counter_code: str,
) -> None:
    effect = DOMAIN_TEN_GOD_GROUP_EFFECTS.get(domain, {}).get(group)
    if not effect:
        return
    for metric in ("opportunity", "risk", "change", "probability"):
        totals[metric] += _scale_delta(float(effect.get(metric, 0)), weight)
    if effect.get("risk", 0) > 0 or effect.get("probability", 0) < 0:
        totals["counter_signals"].append(counter_code)
    else:
        totals["basis_codes"].append(basis_code)


def _ten_god_group_for_element(structure: ChartStructure, element: str) -> str:
    day_element = structure.day_master_element
    if element == day_element:
        return "peer"
    if element == ELEMENT_GENERATED_BY[day_element]:
        return "resource"
    if element == ELEMENT_GENERATES[day_element]:
        return "output"
    if element == ELEMENT_CONTROLS[day_element]:
        return "wealth"
    if element == ELEMENT_CONTROLLED_BY[day_element]:
        return "officer"
    return ""


def _pattern_confidence_weight(confidence: str) -> float:
    return {
        "high": 1.0,
        "medium_high": 0.82,
        "medium": 0.62,
        "low": 0.38,
        "restricted": 0.2,
    }.get(confidence, 0.5)


def _candidate_weight(score: int, *, active: bool) -> float:
    base = 1.0 if score >= 76 else 0.78 if score >= 62 else 0.52
    return base if active else base * 0.35


def _pattern_candidate_priority(candidate: object) -> tuple[int, int]:
    role = str(getattr(candidate, "role", ""))
    score = int(getattr(candidate, "score", 0) or 0)
    if role.startswith("regular_pattern_"):
        return (0, -score)
    if role in {"climate_medicine", "illness_medicine"}:
        return (1, -score)
    if "support" in role or "pressure" in role:
        return (2, -score)
    return (3, -score)


def _merge_pattern_candidate_for_element(candidates: list[object], element: str) -> object:
    element_candidates = [candidate for candidate in candidates if str(getattr(candidate, "element", "")) == element]
    if not element_candidates:
        raise ValueError(f"No candidates for element: {element}")
    role_source = sorted(element_candidates, key=_pattern_candidate_priority)[0]
    confidence_source = max(element_candidates, key=lambda candidate: int(getattr(candidate, "score", 0) or 0))
    basis_codes: list[str] = []
    for candidate in element_candidates:
        for code in list(getattr(candidate, "basis_codes", []) or []):
            text_code = str(code)
            if text_code and text_code not in basis_codes:
                basis_codes.append(text_code)
    return role_source.__class__(
        element=element,
        role=str(getattr(role_source, "role", "")),
        score=max(int(getattr(candidate, "score", 0) or 0) for candidate in element_candidates),
        confidence=getattr(confidence_source, "confidence", "medium"),
        basis_codes=basis_codes,
    )


def _prioritized_pattern_candidates(
    candidates: list[object],
    *,
    limit: int = 2,
    exclude_elements: set[str] | None = None,
) -> list[object]:
    blocked_elements = exclude_elements or set()
    available_candidates = [
        candidate
        for candidate in candidates
        if str(getattr(candidate, "element", "")) and str(getattr(candidate, "element", "")) not in blocked_elements
    ]
    element_order: dict[str, int] = {}
    for index, candidate in enumerate(available_candidates):
        element_order.setdefault(str(getattr(candidate, "element", "")), index)
    merged_candidates = [
        _merge_pattern_candidate_for_element(available_candidates, element)
        for element in element_order
    ]
    merged_candidates.sort(
        key=lambda candidate: (
            *_pattern_candidate_priority(candidate),
            element_order.get(str(getattr(candidate, "element", "")), 999),
        )
    )
    return merged_candidates[:limit]


def _apply_metric_effect(totals: dict[str, Any], effect: dict[str, float], weight: float) -> None:
    for metric in ("opportunity", "risk", "change", "probability"):
        totals[metric] += _scale_delta(float(effect.get(metric, 0)), weight)


def _apply_governance_event_adjustment(totals: dict[str, Any], adjustment: dict[str, object], weight: float = 1.0) -> None:
    for metric in ("opportunity", "risk", "change", "probability"):
        totals[metric] += _scale_delta(float(adjustment.get(metric, 0) or 0), weight)
    for code in list(adjustment.get("basis_codes", []) or []):
        text = str(code)
        if text:
            totals["basis_codes"].append(text)
    for code in list(adjustment.get("counter_signals", []) or []):
        text = str(code)
        if text:
            totals["counter_signals"].append(text)


def _candidate_reason_codes(candidate: object, effect_map: dict[str, dict[str, float]]) -> list[str]:
    reason_codes: list[str] = []
    for code in getattr(candidate, "basis_codes", []) or []:
        reason = str(code)
        if reason in effect_map:
            reason_codes.append(reason)
    return list(dict.fromkeys(reason_codes))


def _apply_pattern_reason_effect(
    totals: dict[str, Any],
    *,
    domain: str,
    candidate: object,
    effect_map: dict[str, dict[str, float]],
    weight: float,
    prefix: str,
    target_bucket: str,
) -> None:
    for reason in _candidate_reason_codes(candidate, effect_map):
        effect = effect_map[reason]
        _apply_metric_effect(totals, effect, weight)
        totals[target_bucket].append(f"{prefix}_{domain}_{reason}")


def _pattern_active_elements(flow: FlowSignal) -> set[str]:
    active = set(flow.activated_elements)
    for relation in flow.branch_interactions:
        active.update(relation_activated_elements(relation))
    return active


def _pattern_need_adjustments(structure: ChartStructure, flow: FlowSignal, domain: str) -> dict[str, Any]:
    """Make pattern needs and burdens affect the actual event packet, not only prose."""

    totals: dict[str, Any] = {
        "opportunity": 0.0,
        "risk": 0.0,
        "change": 0.0,
        "probability": 0.0,
        "basis_codes": [],
        "counter_signals": [],
    }
    pattern = structure.pattern_profile
    confidence_weight = _pattern_confidence_weight(pattern.pattern_confidence)
    active_elements = _pattern_active_elements(flow)

    month_group = TEN_GOD_GROUPS.get(pattern.month_command_ten_god, "")
    if month_group:
        effect = PATTERN_GROUP_SUPPORT_EFFECTS.get(domain, {}).get(month_group, {})
        _apply_metric_effect(totals, effect, confidence_weight * 0.28)
        totals["basis_codes"].append(f"pattern_month_command_{domain}_{month_group}")
        decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"pattern_month_command_{domain}_{month_group}",
            signal_type="month_command",
            ten_gods=[pattern.month_command_ten_god],
            positions=["month", "month:branch"],
            domain=domain,
        )
        _apply_governance_event_adjustment(totals, governance_event_adjustment(decision), confidence_weight)

    raw_useful_candidates = list(pattern.useful_element_candidates)
    raw_caution_candidates = list(pattern.caution_element_candidates)
    useful_candidates = _prioritized_pattern_candidates(raw_useful_candidates, limit=2)
    useful_elements = {str(candidate.element) for candidate in useful_candidates}
    caution_candidates = _prioritized_pattern_candidates(
        raw_caution_candidates,
        limit=2,
        exclude_elements=useful_elements,
    )
    overuse_candidates = _prioritized_pattern_candidates(
        [
            candidate
            for candidate in raw_caution_candidates
            if str(getattr(candidate, "element", "")) in useful_elements
        ],
        limit=2,
    )

    overuse_elements = {str(candidate.element) for candidate in overuse_candidates}
    for candidate in useful_candidates:
        element = str(candidate.element)
        group = _ten_god_group_for_element(structure, element)
        if not group:
            continue
        active = element in active_elements
        weight = _candidate_weight(int(candidate.score), active=active) * confidence_weight
        effect = PATTERN_GROUP_SUPPORT_EFFECTS.get(domain, {}).get(group, {})
        _apply_metric_effect(totals, effect, weight)
        totals["basis_codes"].append(f"pattern_useful_event_{domain}_{element}_{group}")
        _apply_pattern_reason_effect(
            totals,
            domain=domain,
            candidate=candidate,
            effect_map=PATTERN_REASON_SUPPORT_EFFECTS,
            weight=weight * 0.45,
            prefix="pattern_reason_support",
            target_bucket="basis_codes",
        )
        if active:
            totals["basis_codes"].append(f"pattern_useful_active_{domain}_{element}")
        if element in overuse_elements:
            totals["risk"] += _scale_delta(1.5, weight)
            totals["counter_signals"].append(f"pattern_useful_excess_watch_{domain}_{element}")
        decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"pattern_useful_{domain}_{element}_{group}",
            signal_type="pattern_useful_element",
            elements=[element],
            positions=["pattern_need", *(["flow_activation"] if active else [])],
            domain=domain,
        )
        _apply_governance_event_adjustment(totals, governance_event_adjustment(decision), confidence_weight * 0.85)

    for candidate in overuse_candidates:
        element = str(candidate.element)
        group = _ten_god_group_for_element(structure, element)
        active = element in active_elements
        weight = _candidate_weight(int(candidate.score), active=active) * confidence_weight
        if f"pattern_useful_excess_watch_{domain}_{element}" not in totals["counter_signals"]:
            totals["risk"] += _scale_delta(1.2, weight)
            totals["counter_signals"].append(f"pattern_useful_excess_watch_{domain}_{element}")
        _apply_pattern_reason_effect(
            totals,
            domain=domain,
            candidate=candidate,
            effect_map=PATTERN_REASON_PRESSURE_EFFECTS,
            weight=weight * 0.25,
            prefix="pattern_reason_overuse",
            target_bucket="counter_signals",
        )
        decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"pattern_overuse_{domain}_{element}_{group}",
            signal_type="pattern_overuse_element",
            elements=[element],
            positions=["pattern_need", *(["flow_activation"] if active else [])],
            domain=domain,
        )
        _apply_governance_event_adjustment(totals, governance_event_adjustment(decision), confidence_weight * 0.55)

    for candidate in caution_candidates:
        element = str(candidate.element)
        group = _ten_god_group_for_element(structure, element)
        if not group:
            continue
        active = element in active_elements
        weight = _candidate_weight(int(candidate.score), active=active) * confidence_weight
        effect = PATTERN_GROUP_PRESSURE_EFFECTS.get(domain, {}).get(group, {})
        _apply_metric_effect(totals, effect, weight)
        totals["counter_signals"].append(f"pattern_caution_event_{domain}_{element}_{group}")
        _apply_pattern_reason_effect(
            totals,
            domain=domain,
            candidate=candidate,
            effect_map=PATTERN_REASON_PRESSURE_EFFECTS,
            weight=weight * 0.45,
            prefix="pattern_reason_pressure",
            target_bucket="counter_signals",
        )
        if active:
            totals["counter_signals"].append(f"pattern_caution_active_{domain}_{element}")
        decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"pattern_caution_{domain}_{element}_{group}",
            signal_type="pattern_caution_element",
            elements=[element],
            positions=["pattern_need", *(["flow_activation"] if active else [])],
            domain=domain,
        )
        _apply_governance_event_adjustment(totals, governance_event_adjustment(decision), confidence_weight * 0.85)

    return _bounded_feature_axis_adjustments(
        opportunity=round(totals["opportunity"]),
        risk=round(totals["risk"]),
        change=round(totals["change"]),
        probability=round(totals["probability"]),
        basis_codes=totals["basis_codes"],
        counter_signals=totals["counter_signals"],
    )


def _natal_position_adjustments(structure: ChartStructure, domain: str) -> dict[str, Any]:
    """Translate natal palaces, hidden stems, and natal branch relations into event scoring."""

    totals: dict[str, Any] = {
        "opportunity": 0.0,
        "risk": 0.0,
        "change": 0.0,
        "probability": 0.0,
        "basis_codes": [],
        "counter_signals": [],
    }
    priority_positions = DOMAIN_POSITION_PRIORITY[domain]
    position_weights = dict(zip(priority_positions, POSITION_RELEVANCE_WEIGHTS, strict=True))

    for position in priority_positions:
        signal = structure.position_signals.get(position)
        if signal is None:
            continue
        weight = position_weights[position]
        if position == "month":
            totals["basis_codes"].append(f"natal_month_command_{domain}_{signal.branch_main_ten_god}")
            totals["probability"] += _scale_delta(2, weight)
        if domain in signal.domains:
            totals["basis_codes"].append(f"natal_palace_{domain}_{position}")
            totals["probability"] += _scale_delta(1, weight)
        position_decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"natal_position_{domain}_{position}",
            signal_type="natal_position",
            elements=[signal.branch_element, signal.stem_element],
            ten_gods=[signal.branch_main_ten_god, signal.stem_ten_god],
            positions=[position, f"{position}:branch", f"{position}:stem"],
            domain=domain,
        )
        _apply_governance_event_adjustment(
            totals,
            governance_event_adjustment(position_decision),
            weight * (1.05 if position == "month" else 0.62),
        )
        main_group = TEN_GOD_GROUPS.get(signal.branch_main_ten_god)
        if main_group:
            _apply_group_effect(
                totals,
                domain=domain,
                group=main_group,
                weight=weight,
                basis_code=f"natal_position_{domain}_{position}_{main_group}",
                counter_code=f"natal_position_counter_{domain}_{position}_{main_group}",
            )
        hidden_groups = {
            TEN_GOD_GROUPS[ten_god]
            for ten_god in signal.hidden_ten_gods
            if ten_god in TEN_GOD_GROUPS
        }
        for hidden_group in sorted(hidden_groups):
            hidden_weight = weight * (0.48 if signal.protruded_hidden_stems else 0.26)
            _apply_group_effect(
                totals,
                domain=domain,
                group=hidden_group,
                weight=hidden_weight,
                basis_code=f"natal_hidden_{domain}_{position}_{hidden_group}",
                counter_code=f"natal_hidden_counter_{domain}_{position}_{hidden_group}",
            )
        if signal.hidden_ten_gods:
            hidden_decision = evaluate_month_governed_signal(
                structure.month_governance_profile,
                signal_key=f"natal_hidden_{domain}_{position}",
                signal_type="natal_hidden_stems",
                ten_gods=list(signal.hidden_ten_gods),
                positions=[position, f"{position}:hidden", f"{position}:branch"],
                domain=domain,
            )
            _apply_governance_event_adjustment(
                totals,
                governance_event_adjustment(hidden_decision),
                weight * (0.78 if signal.protruded_hidden_stems else 0.42),
            )
        if signal.protruded_hidden_stems and position in priority_positions[:2]:
            totals["opportunity"] += _scale_delta(2, weight)
            totals["probability"] += _scale_delta(1, weight)
            totals["basis_codes"].append(f"natal_hidden_protrusion_{domain}_{position}")

    priority_set = set(priority_positions[:2])
    for relation in structure.branch_interactions:
        touched_priority = priority_set.intersection(relation.positions)
        if domain not in relation.domain_links and not touched_priority:
            continue
        weight = 1.0 if touched_priority else 0.58
        code = f"natal_branch_{relation.relation_type}_{domain}"
        polarity = branch_relation_polarity(structure.element_profile, relation, structure.pattern_profile)
        relation_decision = evaluate_month_governed_signal(
            structure.month_governance_profile,
            signal_key=f"natal_branch_relation_{domain}_{relation.relation_type}",
            signal_type="branch_relation",
            elements=list(relation_activated_elements(relation)),
            positions=[*relation.positions, "branch_relation"],
            domain=domain,
        )
        _apply_governance_event_adjustment(
            totals,
            governance_event_adjustment(relation_decision),
            weight * (1.0 if "month" in relation.positions else 0.56),
        )
        support_code = f"{code}_useful_relation"
        burden_code = f"{code}_burden_relation"
        overuse_code = f"{code}_overuse_relation"
        if relation.relation_type in {"six_combine", "three_harmony", "three_harmony_half"}:
            if polarity.polarity == "burdensome":
                totals["risk"] += _scale_delta(5, weight)
                totals["change"] += _scale_delta(2, weight)
                totals["counter_signals"].append(burden_code)
            else:
                totals["opportunity"] += _scale_delta(5, weight)
                totals["change"] += _scale_delta(2, weight)
                totals["probability"] += _scale_delta(2, weight)
                totals["basis_codes"].append(code)
                if polarity.polarity in {"supportive", "mixed"}:
                    totals["basis_codes"].append(support_code)
                    if polarity.polarity == "mixed":
                        totals["risk"] += _scale_delta(2, weight)
        elif relation.relation_type == "clash":
            totals["change"] += _scale_delta(6, weight)
            if polarity.polarity == "supportive":
                totals["opportunity"] += _scale_delta(5, weight)
                totals["probability"] += _scale_delta(2, weight)
                totals["basis_codes"].append(support_code)
            else:
                totals["risk"] += _scale_delta(5 if polarity.polarity == "mixed" else 7, weight)
                totals["probability"] += _scale_delta(1, weight)
                totals["counter_signals"].append(burden_code if polarity.polarity == "burdensome" else code)
                if polarity.polarity == "mixed":
                    totals["basis_codes"].append(support_code)
        elif relation.relation_type in {"punishment", "harm", "break", "self_punishment"}:
            totals["change"] += _scale_delta(3, weight)
            if polarity.polarity == "supportive":
                totals["opportunity"] += _scale_delta(3, weight)
                totals["basis_codes"].append(support_code)
                totals["risk"] += _scale_delta(1, weight)
                totals["counter_signals"].append(code)
            else:
                totals["risk"] += _scale_delta(3 if polarity.polarity == "mixed" else 5, weight)
                totals["counter_signals"].append(burden_code if polarity.polarity == "burdensome" else code)
                if polarity.polarity == "mixed":
                    totals["basis_codes"].append(support_code)

        if polarity.overuse_elements:
            totals["risk"] += _scale_delta(2, weight)
            totals["counter_signals"].append(overuse_code)

    return {
        "opportunity": totals["opportunity"],
        "risk": totals["risk"],
        "change": totals["change"],
        "probability": totals["probability"],
        "basis_codes": list(dict.fromkeys(totals["basis_codes"])),
        "counter_signals": list(dict.fromkeys(totals["counter_signals"])),
    }


def _feature_axis_adjustments(domain: str, feature_axes: list[dict[str, Any]]) -> dict[str, Any]:
    opportunity = 0
    risk = 0
    change = 0
    probability = 0
    basis_codes: list[str] = []
    counter_signals: list[str] = []

    if domain == "money":
        money_potential = _axis_score(feature_axes, "money_potential")
        income_expansion = _axis_score(feature_axes, "income_expansion")
        asset_retention = _axis_score(feature_axes, "asset_retention")
        spending_control = _axis_score(feature_axes, "spending_control")
        practical_planning = _axis_score(feature_axes, "practical_planning")
        investment_sense = _axis_score(feature_axes, "investment_trading_sense")
        money_attitude = _axis_score(feature_axes, "money_attitude")
        deal_selection = _axis_score(feature_axes, "deal_selection")
        loss_avoidance = _axis_score(feature_axes, "loss_avoidance")
        late_growth = _axis_score(feature_axes, "late_life_money_growth")
        if money_potential >= 70:
            opportunity += 4
            probability += 3
            basis_codes.append("feature_axis_money_potential_support")
        if income_expansion >= 68:
            opportunity += 5
            change += 2
            probability += 3
            basis_codes.append("feature_axis_income_expansion_support")
        if asset_retention < 45:
            risk += 6
            probability -= 2
            counter_signals.append("feature_axis_asset_retention_weak")
        if spending_control < 45:
            risk += 5
            counter_signals.append("feature_axis_spending_control_weak")
        if practical_planning >= 64:
            risk -= 2
            probability += 2
            basis_codes.append("feature_axis_practical_planning_support")
        if investment_sense >= 64:
            opportunity += 1
            change += 1
            probability += 1
            basis_codes.append("feature_axis_investment_trading_support")
        if deal_selection >= 64:
            risk -= 1
            basis_codes.append("feature_axis_deal_selection_support")
        if loss_avoidance >= 64:
            risk -= 2
            basis_codes.append("feature_axis_loss_avoidance_support")
        if late_growth >= 70:
            opportunity += 2
            probability += 1
            basis_codes.append("feature_axis_late_life_money_growth_support")
        if money_attitude < 45:
            risk += 2
            counter_signals.append("feature_axis_money_attitude_weak")
        if loss_avoidance < 45:
            risk += 4
            probability -= 2
            counter_signals.append("feature_axis_loss_avoidance_weak")
    elif domain == "career":
        social_success = _axis_score(feature_axes, "social_success_potential")
        career_achievement = _axis_score(feature_axes, "career_achievement")
        organization = _axis_score(feature_axes, "organization_adaptability")
        self_direction = _axis_score(feature_axes, "self_direction")
        decision_consistency = _axis_score(feature_axes, "decision_consistency")
        change_adaptability = _axis_score(feature_axes, "change_adaptability")
        reputation = _axis_score(feature_axes, "reputation_maintenance")
        responsibility = _axis_score(feature_axes, "responsibility_capacity")
        if social_success >= 70:
            opportunity += 5
            probability += 4
            basis_codes.append("feature_axis_social_success_support")
        if career_achievement >= 68:
            opportunity += 4
            probability += 3
            basis_codes.append("feature_axis_career_achievement_support")
        if organization < 45:
            risk += 6
            counter_signals.append("feature_axis_organization_adaptability_weak")
        if self_direction >= 64:
            opportunity += 2
            basis_codes.append("feature_axis_self_direction_support")
        if decision_consistency < 45:
            risk += 4
            counter_signals.append("feature_axis_decision_consistency_weak")
        if change_adaptability >= 64:
            change += 2
            probability += 2
            basis_codes.append("feature_axis_change_adaptability_support")
        if reputation >= 70:
            opportunity += 1
            basis_codes.append("feature_axis_reputation_maintenance_support")
        if responsibility >= 68:
            probability += 1
            basis_codes.append("feature_axis_responsibility_capacity_support")
        if reputation < 45:
            risk += 4
            counter_signals.append("feature_axis_reputation_maintenance_weak")
        if responsibility < 45:
            risk += 4
            counter_signals.append("feature_axis_responsibility_capacity_weak")
    elif domain == "love":
        interpersonal = _axis_score(feature_axes, "interpersonal_influence")
        relationship = _axis_score(feature_axes, "relationship_stability")
        communication = _axis_score(feature_axes, "communication_expression")
        boundary = _axis_score(feature_axes, "boundary_management")
        recovery = _axis_score(feature_axes, "crisis_recovery")
        conflict_recovery = _axis_score(feature_axes, "conflict_recovery")
        attraction = _axis_score(feature_axes, "attraction_selectivity")
        progression = _axis_score(feature_axes, "relationship_progression")
        affection = _axis_score(feature_axes, "affection_expression")
        if interpersonal >= 64:
            opportunity += 4
            probability += 3
            basis_codes.append("feature_axis_interpersonal_influence_support")
        if attraction >= 64:
            probability += 2
            basis_codes.append("feature_axis_attraction_selectivity_support")
        if progression >= 64:
            opportunity += 3
            change += 1
            probability += 2
            basis_codes.append("feature_axis_relationship_progression_support")
        if affection >= 64:
            opportunity += 2
            basis_codes.append("feature_axis_affection_expression_support")
        if communication >= 64:
            opportunity += 2
            basis_codes.append("feature_axis_communication_expression_support")
        if boundary >= 64:
            risk -= 2
            basis_codes.append("feature_axis_boundary_management_support")
        if recovery >= 64:
            risk -= 3
            basis_codes.append("feature_axis_crisis_recovery_support")
        if relationship < 45:
            risk += 8
            probability -= 2
            counter_signals.append("feature_axis_relationship_stability_weak")
        if attraction < 45:
            risk += 2
            counter_signals.append("feature_axis_attraction_selectivity_weak")
        if progression < 45:
            probability -= 2
            counter_signals.append("feature_axis_relationship_progression_weak")
        if affection < 45:
            risk += 2
            counter_signals.append("feature_axis_affection_expression_weak")
        if boundary < 45:
            risk += 5
            counter_signals.append("feature_axis_boundary_management_weak")
        if conflict_recovery >= 64:
            risk -= 1
            probability += 1
            basis_codes.append("feature_axis_conflict_recovery_support")
        if conflict_recovery < 45:
            risk += 3
            counter_signals.append("feature_axis_conflict_recovery_weak")
    elif domain == "marriage":
        marriage = _axis_score(feature_axes, "marriage_stability")
        relationship = _axis_score(feature_axes, "relationship_stability")
        boundary = _axis_score(feature_axes, "boundary_management")
        decision_consistency = _axis_score(feature_axes, "decision_consistency")
        practical_planning = _axis_score(feature_axes, "practical_planning")
        asset_retention = _axis_score(feature_axes, "asset_retention")
        family_responsibility = _axis_score(feature_axes, "family_responsibility")
        conflict_recovery = _axis_score(feature_axes, "conflict_recovery")
        spouse_match = _axis_score(feature_axes, "spouse_match_quality")
        timing_readiness = _axis_score(feature_axes, "marriage_timing_readiness")
        household = _axis_score(feature_axes, "household_stability")
        if marriage >= 64:
            opportunity += 5
            probability += 3
            basis_codes.append("feature_axis_marriage_stability_support")
        if spouse_match >= 64:
            opportunity += 2
            probability += 2
            basis_codes.append("feature_axis_spouse_match_quality_support")
        if timing_readiness >= 64:
            opportunity += 3
            change += 1
            probability += 2
            basis_codes.append("feature_axis_marriage_timing_readiness_support")
        if household >= 64:
            risk -= 2
            probability += 1
            basis_codes.append("feature_axis_household_stability_support")
        if boundary >= 64:
            risk -= 2
            basis_codes.append("feature_axis_boundary_management_support")
        if decision_consistency >= 64:
            probability += 2
            basis_codes.append("feature_axis_decision_consistency_support")
        if practical_planning >= 64:
            risk -= 2
            basis_codes.append("feature_axis_practical_planning_support")
        if relationship < 45:
            risk += 8
            probability -= 2
            counter_signals.append("feature_axis_relationship_stability_weak")
        if spouse_match < 45:
            risk += 4
            probability -= 2
            counter_signals.append("feature_axis_spouse_match_quality_weak")
        if timing_readiness < 45:
            probability -= 2
            counter_signals.append("feature_axis_marriage_timing_readiness_weak")
        if household < 45:
            risk += 3
            counter_signals.append("feature_axis_household_stability_weak")
        if boundary < 45:
            risk += 5
            counter_signals.append("feature_axis_boundary_management_weak")
        if asset_retention < 45:
            risk += 3
            counter_signals.append("feature_axis_asset_retention_weak")
        if family_responsibility >= 64:
            risk -= 1
            probability += 1
            basis_codes.append("feature_axis_family_responsibility_support")
        if conflict_recovery >= 64:
            risk -= 1
            basis_codes.append("feature_axis_conflict_recovery_support")
        if family_responsibility < 45:
            probability -= 1
            counter_signals.append("feature_axis_family_responsibility_weak")
        if conflict_recovery < 45:
            probability -= 1
            counter_signals.append("feature_axis_conflict_recovery_weak")

    return _bounded_feature_axis_adjustments(
        opportunity=opportunity,
        risk=risk,
        change=change,
        probability=probability,
        basis_codes=basis_codes,
        counter_signals=counter_signals,
    )


def _combination_adjustments(structure: ChartStructure, domain: str) -> dict[str, Any]:
    opportunity = 0
    risk = 0
    change = 0
    probability = 0
    basis_codes: list[str] = []
    counter_signals: list[str] = []

    for signal in signals_for_domain(structure.combination_profile, domain, limit=12):
        strength_bonus = {"high": 3, "moderate": 2, "low": 1}.get(signal.strength, 1)
        if signal.basis_codes:
            opportunity += strength_bonus
            probability += 1 if signal.strength in {"high", "moderate"} else 0
            basis_codes.extend(signal.basis_codes)
        if signal.counter_signals:
            risk += strength_bonus
            probability -= 1 if signal.strength == "high" else 0
            counter_signals.extend(signal.counter_signals)
        if signal.layer in {"heavenly_stem", "ten_god_chain"} and signal.strength == "high":
            change += 1

    return {
        "opportunity": opportunity,
        "risk": risk,
        "change": change,
        "probability": probability,
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _bounded_cycle_regulation_adjustments(
    *,
    opportunity: int,
    risk: int,
    change: int,
    probability: int,
    basis_codes: list[str],
    counter_signals: list[str],
) -> dict[str, Any]:
    bounded: dict[str, int] = {}
    for metric, value in {
        "opportunity": opportunity,
        "risk": risk,
        "change": change,
        "probability": probability,
    }.items():
        lower, upper = CYCLE_REGULATION_ADJUSTMENT_LIMITS[metric]
        bounded[metric] = max(lower, min(upper, value))
    return {
        **bounded,
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _flow_ten_god_groups(flow: FlowSignal) -> set[str]:
    groups: set[str] = set()
    for ten_god in (
        flow.year_stem_ten_god,
        flow.year_branch_main_ten_god,
        flow.daeun_stem_ten_god,
        flow.daeun_branch_main_ten_god,
    ):
        if ten_god:
            group = TEN_GOD_GROUPS.get(str(ten_god))
            if group:
                groups.add(group)
    return groups


def _cycle_signal_weight(
    domain: str,
    signal: dict[str, Any],
    flow: FlowSignal,
    activation: dict[str, Any] | None = None,
) -> float:
    score = int(signal.get("score") or 0)
    if score >= 90:
        weight = 1.0
    elif score >= 80:
        weight = 0.82
    elif score >= 70:
        weight = 0.62
    else:
        weight = 0.38

    activation = activation or _cycle_signal_flow_activation_context(domain, signal, flow)
    activation_grade = str(activation.get("grade") or "")
    if activation_grade == "flow_branch_relation_triggers_cycle":
        weight += 0.22
    elif activation_grade == "flow_annual_daeun_compounds_cycle":
        weight += 0.18
    elif activation_grade in {"flow_stem_branch_triggers_cycle", "flow_branch_triggers_cycle"}:
        weight += 0.14
    elif activation_grade in {"flow_hidden_triggers_cycle", "flow_stem_triggers_cycle", "flow_generic_triggers_cycle"}:
        weight += 0.08
    governance = dict(signal.get("governance_context") or {})
    if governance.get("touches_month_command"):
        weight += 0.08
    if governance.get("touches_useful") and signal.get("polarity") in {"support", "mixed"}:
        weight += 0.05
    if governance.get("touches_caution"):
        weight += 0.05
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    if pattern_cycle.get("support_rule_keys"):
        weight += 0.06
    if pattern_cycle.get("caution_rule_keys"):
        weight += 0.06
    condition = dict(signal.get("condition_context") or {})
    if condition.get("support_tags"):
        weight += 0.04
    if condition.get("pressure_tags"):
        weight += 0.04
    branch_reality = dict(signal.get("branch_reality_context") or {})
    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade in {"month_branch_visible", "month_hidden_protruded"}:
        weight += 0.09
    elif branch_grade in {"branch_dominant", "hidden_to_visible"}:
        weight += 0.07
    elif branch_grade == "branch_rooted":
        weight += 0.05
    elif branch_grade == "stem_visible_only":
        weight += 0.02
    return min(1.15, weight)


def _cycle_signal_selection_rank(domain: str, signal: dict[str, Any]) -> tuple[int, int, int, int, str]:
    """Rank cycle signals before applying the packet evidence limit.

    Hidden-stem protrusion and rooting should not disappear merely because many
    abstract chain signals were produced first.  The attached theory note treats
    월지 and 일지 as decisive reality anchors, so signals touching those
    positions receive an explicit selection lift.
    """

    relation = str(signal.get("relation") or "")
    positions = [str(item) for item in list(signal.get("positions") or []) if str(item)]
    root_positions = [str(item) for item in list(signal.get("root_positions") or []) if str(item)]
    all_positions = set(positions + root_positions)
    core_position_rank = 0
    if "month" in all_positions:
        core_position_rank += 3
    if "day" in all_positions:
        core_position_rank += 2

    domain_priority = DOMAIN_POSITION_PRIORITY.get(domain, ())
    domain_position_rank = 0
    for index, position in enumerate(domain_priority):
        if position in all_positions:
            domain_position_rank = max(domain_position_rank, len(domain_priority) - index)

    relation_rank = {
        "hidden_protrusion": 6,
        "visible_root": 6,
        "chain": 5,
        "generates": 4,
        "controls": 4,
        "element_exception": 4,
        "element_generates": 3,
        "element_controls": 3,
        "element_bridge": 3,
        "branch_cycle": 3,
        "stem_combine": 2,
    }.get(relation, 1)

    score_rank = int(signal.get("score") or 0) + int(signal.get("reality_score") or 0)
    return (
        core_position_rank,
        domain_position_rank,
        relation_rank,
        score_rank,
        str(signal.get("signal_id") or ""),
    )


def _cycle_signal_flow_hits(signal: dict[str, Any], flow: FlowSignal) -> dict[str, Any]:
    flow_elements = {str(element) for element in list(flow.activated_elements or []) if str(element)}
    flow_groups = _flow_ten_god_groups(flow)
    source_element = str(signal.get("source_element") or "")
    target_element = str(signal.get("target_element") or "")
    source_group = str(signal.get("source_group") or "")
    target_group = str(signal.get("target_group") or "")
    bridge_element = str(signal.get("bridge_element") or "")
    bridge_group = str(signal.get("bridge_group") or "")
    transform_element = str(signal.get("transform_element") or "")
    transform_group = str(signal.get("transform_group") or "")
    chain_elements = {str(element) for element in list(signal.get("elements") or []) if str(element)}
    chain_groups = {str(group) for group in list(signal.get("groups") or []) if str(group)}
    activated_elements = {str(element) for element in list(signal.get("activated_elements") or []) if str(element)}
    activated_groups = {str(group) for group in list(signal.get("activated_groups") or []) if str(group)}
    original_groups = {str(group) for group in list(signal.get("original_groups") or []) if str(group)}

    hit_points: list[str] = []
    if source_element in flow_elements or source_group in flow_groups:
        hit_points.append("source")
    if target_element in flow_elements or target_group in flow_groups:
        hit_points.append("target")
    if bridge_element in flow_elements or bridge_group in flow_groups:
        hit_points.append("bridge")
    if transform_element in flow_elements or transform_group in flow_groups:
        hit_points.append("combine")
    if (chain_elements & flow_elements) or (chain_groups & flow_groups):
        hit_points.append("chain")
    if (activated_elements & flow_elements) or (activated_groups & flow_groups):
        hit_points.append("branch")
    if not hit_points and (
        ({source_element, target_element, bridge_element, transform_element} | activated_elements) & flow_elements
        or ({source_group, target_group, bridge_group, transform_group} | activated_groups | original_groups) & flow_groups
    ):
        hit_points.append("edge")
    return {
        "hit_points": list(dict.fromkeys(hit_points)),
        "hit_elements": sorted(({source_element, target_element, bridge_element, transform_element} | chain_elements | activated_elements) & flow_elements),
        "hit_groups": sorted(({source_group, target_group, bridge_group, transform_group} | chain_groups | activated_groups | original_groups) & flow_groups),
    }


def _cycle_signal_element_group_map(signal: dict[str, Any]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    contexts: list[dict[str, Any]] = []
    for key in ("source_context", "target_context", "bridge_context"):
        context = signal.get(key)
        if isinstance(context, dict):
            contexts.append(context)
    contexts.extend(context for context in list(signal.get("group_contexts") or []) if isinstance(context, dict))
    for context in contexts:
        element = str(context.get("element") or "")
        group = str(context.get("group") or "")
        if element and group:
            mapping.setdefault(element, set()).add(group)
    return mapping


def _cycle_signal_flow_edge_contexts(
    signal: dict[str, Any],
    flow_groups: set[str],
    source_hit_groups: list[str],
    source_hit_elements: list[str],
    relation_hit_elements: list[str],
    relation_hits: list[str],
) -> list[dict[str, Any]]:
    month_cycle_fit = dict(signal.get("month_cycle_fit_context") or {})
    edge_contexts = [edge for edge in list(month_cycle_fit.get("edge_contexts") or []) if isinstance(edge, dict)]
    if not edge_contexts:
        return []

    element_groups = _cycle_signal_element_group_map(signal)
    groups_from_elements: set[str] = set()
    for element in [*source_hit_elements, *relation_hit_elements]:
        groups_from_elements.update(element_groups.get(str(element), set()))
    hit_groups = set(flow_groups) | set(source_hit_groups) | groups_from_elements
    results: list[dict[str, Any]] = []
    for edge in edge_contexts:
        source_group = str(edge.get("source_group") or "")
        target_group = str(edge.get("target_group") or "")
        relation = str(edge.get("relation") or "")
        source_hit = source_group in hit_groups
        target_hit = target_group in hit_groups
        has_relation = bool(relation_hits and (source_hit or target_hit))
        if source_hit and target_hit and has_relation:
            grade = "edge_flow_relation_triggers"
        elif source_hit and target_hit:
            grade = "edge_flow_both_roles"
        elif has_relation:
            grade = "edge_flow_relation_touches_role"
        elif source_hit or target_hit:
            grade = "edge_flow_single_role_touch"
        else:
            grade = "edge_flow_not_touched"
        results.append(
            {
                "source_group": source_group,
                "target_group": target_group,
                "relation": relation,
                "source_hit": source_hit,
                "target_hit": target_hit,
                "relation_hits": list(relation_hits) if has_relation else [],
                "hit_groups": sorted(hit_groups & {source_group, target_group}),
                "grade": grade,
                "active": grade in {"edge_flow_relation_triggers", "edge_flow_both_roles"},
                "soft_active": grade == "edge_flow_relation_touches_role",
                "month_fit_verdict": str(edge.get("verdict") or ""),
            }
        )
    return results


def _cycle_signal_flow_activation_context(domain: str, signal: dict[str, Any], flow: FlowSignal) -> dict[str, Any]:
    hits = _cycle_signal_flow_hits(signal, flow)
    signal_id = str(signal.get("signal_id") or "")
    relation = str(signal.get("relation") or "")
    signal_elements = {
        str(signal.get("source_element") or ""),
        str(signal.get("target_element") or ""),
        str(signal.get("bridge_element") or ""),
        str(signal.get("transform_element") or ""),
        *[str(element) for element in list(signal.get("elements") or [])],
        *[str(element) for element in list(signal.get("activated_elements") or [])],
    }
    signal_elements = {element for element in signal_elements if element}
    signal_groups = {
        str(signal.get("source_group") or ""),
        str(signal.get("target_group") or ""),
        str(signal.get("bridge_group") or ""),
        str(signal.get("transform_group") or ""),
        *[str(group) for group in list(signal.get("groups") or [])],
        *[str(group) for group in list(signal.get("activated_groups") or [])],
        *[str(group) for group in list(signal.get("original_groups") or [])],
    }
    signal_groups = {group for group in signal_groups if group}
    domain_score = dict((flow.domain_scores or {}).get(domain, {}) or {})
    flow_codes = [
        *[str(code) for code in list(flow.basis_codes or [])],
        *[str(code) for code in list(flow.counter_signals or [])],
        *[str(code) for code in list(domain_score.get("basis_codes") or [])],
        *[str(code) for code in list(domain_score.get("counter_signals") or [])],
    ]

    source_hits: list[str] = []
    direct_source_hits: list[str] = []
    source_hit_elements: list[str] = []
    strength = 0.0

    def code_hits(prefix: str, element: str) -> bool:
        return any(code.startswith(prefix) and f"_{element}" in code for code in flow_codes)

    for element in signal_elements:
        if code_hits("annual_stem_", element):
            source_hits.append("annual_stem")
            direct_source_hits.append("annual_stem")
            source_hit_elements.append(element)
            strength += 1.0
        if code_hits("annual_branch_main_", element) or code_hits("year_branch_", element):
            source_hits.append("annual_branch_main")
            direct_source_hits.append("annual_branch_main")
            source_hit_elements.append(element)
            strength += 1.15
        if code_hits("annual_branch_hidden_", element):
            source_hits.append("annual_branch_hidden")
            direct_source_hits.append("annual_branch_hidden")
            source_hit_elements.append(element)
            strength += 0.75
        if code_hits("daeun_stem_", element):
            source_hits.append("daeun_stem")
            direct_source_hits.append("daeun_stem")
            source_hit_elements.append(element)
            strength += 0.9
        if code_hits("daeun_branch_main_", element):
            source_hits.append("daeun_branch_main")
            direct_source_hits.append("daeun_branch_main")
            source_hit_elements.append(element)
            strength += 1.05
        if code_hits("daeun_branch_hidden_", element):
            source_hits.append("daeun_branch_hidden")
            direct_source_hits.append("daeun_branch_hidden")
            source_hit_elements.append(element)
            strength += 0.62

    flow_groups = _flow_ten_god_groups(flow)
    source_hit_groups: list[str] = []
    if signal_groups & flow_groups:
        group_hits = sorted(signal_groups & flow_groups)
        for group in group_hits:
            source_hits.append(f"flow_group_{group}")
            source_hit_groups.append(group)
            strength += 0.55

    relation_hits: list[str] = []
    relation_hit_elements: list[str] = []
    for interaction in list(flow.branch_interactions or []):
        activated = {str(element) for element in relation_activated_elements(interaction) if str(element)}
        relation_type = str(getattr(interaction, "relation_type", ""))
        matched = sorted(activated & signal_elements)
        if matched:
            relation_hits.append(relation_type)
            relation_hit_elements.extend(matched)
            strength += {
                "six_combine": 1.1,
                "three_harmony": 1.25,
                "three_harmony_half": 0.8,
                "clash": 1.25,
                "punishment": 1.1,
                "harm": 0.9,
                "break": 0.85,
                "self_punishment": 0.85,
            }.get(relation_type, 0.7)

    source_hits = list(dict.fromkeys(source_hits))
    direct_source_hits = list(dict.fromkeys(direct_source_hits))
    source_hit_elements = list(dict.fromkeys(source_hit_elements))
    source_hit_groups = list(dict.fromkeys(source_hit_groups))
    relation_hits = list(dict.fromkeys(relation_hits))
    relation_hit_elements = list(dict.fromkeys(relation_hit_elements))
    has_annual = any(hit.startswith("annual_") or hit.startswith("year_") for hit in source_hits)
    has_daeun = any(hit.startswith("daeun_") for hit in source_hits)
    has_stem = any("stem" in hit for hit in source_hits)
    has_branch = any("branch_main" in hit or "branch_hidden" in hit for hit in source_hits)
    has_hidden = any("branch_hidden" in hit for hit in source_hits)
    has_relation = bool(relation_hits)
    hit_points = set(str(point) for point in list(hits["hit_points"] or []))
    direct_role_points = hit_points & {"source", "target", "bridge", "combine"}
    hit_group_count = len(set(str(group) for group in list(hits["hit_groups"] or [])))
    hit_element_count = len(set(str(element) for element in list(hits["hit_elements"] or [])))
    direct_source_count = len(direct_source_hits)
    edge_flow_contexts = _cycle_signal_flow_edge_contexts(
        signal,
        flow_groups,
        source_hit_groups,
        source_hit_elements,
        relation_hit_elements,
        relation_hits,
    )
    active_edge_count = sum(1 for edge in edge_flow_contexts if edge.get("active"))
    soft_active_edge_count = sum(1 for edge in edge_flow_contexts if edge.get("soft_active"))

    if relation == "chain":
        strong_role_hit = active_edge_count >= 1 or hit_group_count >= 2 or (hit_element_count >= 2 and direct_source_count >= 1)
    elif relation in {"generates", "controls", "element_generates", "element_controls"}:
        strong_role_hit = {"source", "target"}.issubset(hit_points) or hit_group_count >= 2
    elif relation == "element_bridge":
        strong_role_hit = len(direct_role_points) >= 2 or hit_group_count >= 2
    elif relation == "element_exception":
        strong_role_hit = {"source", "target"}.issubset(hit_points) or hit_group_count >= 2
    elif relation in {"branch_cycle", "stem_combine", "hidden_protrusion", "visible_root"}:
        strong_role_hit = (
            len(direct_role_points) >= 2
            or hit_group_count >= 2
            or (relation in {"branch_cycle", "stem_combine"} and bool(hit_points & {"branch", "combine"}) and direct_source_count >= 2)
        )
    else:
        strong_role_hit = bool(direct_role_points) or (hit_group_count + hit_element_count >= 2 and direct_source_count >= 1)

    material_flow_touch = direct_source_count >= 1 or bool(relation_hits)
    relation_can_trigger = has_relation and strong_role_hit and material_flow_touch

    if not hits["hit_points"] and not source_hits and not relation_hits:
        grade = "flow_not_triggered"
    elif relation_can_trigger and has_branch:
        grade = "flow_branch_relation_triggers_cycle"
    elif strong_role_hit and has_annual and has_daeun and (has_stem or has_branch):
        grade = "flow_annual_daeun_compounds_cycle"
    elif strong_role_hit and has_branch and has_stem:
        grade = "flow_stem_branch_triggers_cycle"
    elif strong_role_hit and has_branch:
        grade = "flow_branch_triggers_cycle"
    elif strong_role_hit and has_hidden:
        grade = "flow_hidden_triggers_cycle"
    elif strong_role_hit and has_stem:
        grade = "flow_stem_triggers_cycle"
    elif strong_role_hit:
        grade = "flow_generic_triggers_cycle"
    else:
        grade = "flow_not_triggered"

    return {
        "signal_id": signal_id,
        "grade": grade,
        "hit_points": list(hits["hit_points"]),
        "hit_elements": list(hits["hit_elements"]),
        "hit_groups": list(hits["hit_groups"]),
        "source_hits": source_hits,
        "direct_source_hits": direct_source_hits,
        "source_hit_elements": source_hit_elements,
        "source_hit_groups": source_hit_groups,
        "relation_hits": relation_hits,
        "relation_hit_elements": relation_hit_elements,
        "edge_flow_contexts": edge_flow_contexts,
        "active_edge_count": active_edge_count,
        "soft_active_edge_count": soft_active_edge_count,
        "strong_role_hit": bool(strong_role_hit),
        "hit_group_count": hit_group_count,
        "hit_element_count": hit_element_count,
        "strength": round(strength, 2),
        "has_annual": has_annual,
        "has_daeun": has_daeun,
        "has_stem": has_stem,
        "has_branch": has_branch,
        "has_hidden": has_hidden,
        "has_relation": has_relation,
    }


def _cycle_signal_flow_codes(
    domain: str,
    signal: dict[str, Any],
    flow: FlowSignal,
    activation: dict[str, Any] | None = None,
    hits: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    hits = hits or _cycle_signal_flow_hits(signal, flow)
    activation = activation or _cycle_signal_flow_activation_context(domain, signal, flow)
    if not hits["hit_points"] and activation["grade"] == "flow_not_triggered":
        return {"basis_codes": [], "counter_signals": []}
    signal_id = str(signal.get("signal_id") or "")
    polarity = str(signal.get("polarity") or "")
    hit_label = "_".join(hits["hit_points"] or activation["source_hits"][:3] or ["flow"])
    code = f"cycle_flow_activation_{domain}_{signal_id}_{hit_label}"
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    if polarity in {"support", "mixed"}:
        basis_codes.append(code)
    if polarity in {"mixed", "pressure"}:
        counter_signals.append(f"{code}_cost")
    activation_grade = str(activation.get("grade") or "")
    if activation_grade and activation_grade != "flow_not_triggered":
        trigger_code = f"cycle_flow_trigger_{domain}_{signal_id}_{activation_grade}"
        if polarity in {"support", "mixed"}:
            basis_codes.append(trigger_code)
        if polarity in {"pressure", "mixed"}:
            counter_signals.append(f"{trigger_code}_cost")
        for source_hit in list(activation.get("source_hits") or [])[:4]:
            basis_codes.append(f"cycle_flow_source_{domain}_{signal_id}_{source_hit}")
        for relation_hit in list(activation.get("relation_hits") or [])[:3]:
            if polarity in {"support", "mixed"}:
                basis_codes.append(f"cycle_flow_relation_{domain}_{signal_id}_{relation_hit}")
            if polarity in {"pressure", "mixed"}:
                counter_signals.append(f"cycle_flow_relation_{domain}_{signal_id}_{relation_hit}_cost")
        for edge in list(activation.get("edge_flow_contexts") or [])[:4]:
            source = str(edge.get("source_group") or "")
            relation = str(edge.get("relation") or "")
            target = str(edge.get("target_group") or "")
            edge_grade = str(edge.get("grade") or "")
            if not (source and relation and target and edge_grade):
                continue
            edge_code = f"cycle_flow_edge_{domain}_{signal_id}_{source}_{relation}_{target}_{edge_grade}"
            fit = str(edge.get("month_fit_verdict") or "")
            fit_code = f"cycle_flow_edge_fit_{domain}_{signal_id}_{source}_{relation}_{target}_{fit}" if fit else ""
            if bool(edge.get("active")) and polarity in {"support", "mixed"}:
                basis_codes.append(edge_code)
            elif bool(edge.get("soft_active")):
                if polarity in {"support", "mixed"}:
                    basis_codes.append(edge_code)
                if polarity in {"pressure", "mixed"}:
                    counter_signals.append(f"{edge_code}_cost")
            elif edge_grade != "edge_flow_not_touched" and polarity in {"pressure", "mixed"}:
                counter_signals.append(f"{edge_code}_cost")
            if not fit_code:
                continue
            if fit in {"edge_needed", "edge_useful"} and edge.get("active") and polarity in {"support", "mixed"}:
                basis_codes.append(fit_code)
            elif fit in {"edge_useful_with_cost", "edge_pressure_with_use"} and (edge.get("active") or edge.get("soft_active")):
                if polarity in {"support", "mixed"}:
                    basis_codes.append(fit_code)
                counter_signals.append(f"{fit_code}_cost")
            elif fit in {"edge_burdens_month", "edge_pressure"} and (edge.get("active") or edge.get("soft_active")):
                counter_signals.append(f"{fit_code}_cost")
    governance = dict(signal.get("governance_context") or {})
    if governance.get("touches_month_command"):
        basis_codes.append(f"cycle_flow_governance_month_command_{domain}_{signal_id}")
    if governance.get("touches_useful"):
        basis_codes.append(f"cycle_flow_governance_useful_{domain}_{signal_id}")
    if governance.get("touches_caution"):
        counter_signals.append(f"cycle_flow_governance_caution_{domain}_{signal_id}")
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    if pattern_cycle.get("support_rule_keys"):
        basis_codes.append(f"cycle_flow_pattern_support_{domain}_{signal_id}")
    if pattern_cycle.get("caution_rule_keys"):
        counter_signals.append(f"cycle_flow_pattern_caution_{domain}_{signal_id}")
    condition = dict(signal.get("condition_context") or {})
    if condition.get("support_tags"):
        basis_codes.append(f"cycle_flow_condition_support_{domain}_{signal_id}")
    if condition.get("pressure_tags"):
        counter_signals.append(f"cycle_flow_condition_pressure_{domain}_{signal_id}")
    branch_reality = dict(signal.get("branch_reality_context") or {})
    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade:
        branch_code = f"cycle_flow_branch_reality_{domain}_{signal_id}_{branch_grade}"
        if polarity in {"support", "mixed"}:
            basis_codes.append(branch_code)
        if polarity in {"pressure", "mixed"}:
            counter_signals.append(f"{branch_code}_cost")
    for element in hits["hit_elements"][:3]:
        basis_codes.append(f"cycle_flow_element_{element}")
    for group in hits["hit_groups"][:3]:
        basis_codes.append(f"cycle_flow_group_{group}")
    return {
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "counter_signals": list(dict.fromkeys(counter_signals)),
    }


def _cycle_signal_basis_codes(signal: dict[str, Any]) -> list[str]:
    codes = [str(code) for code in list(signal.get("basis_codes") or []) if str(code)]
    priority_prefixes = (
        "cycle_classical_",
        "cycle_judgment_",
        "cycle_month_verdict_",
        "cycle_governance_month_command_",
        "cycle_governance_regular_pattern_",
        "cycle_governance_verdict_",
        "cycle_governance_tag_",
        "cycle_pattern_regular_",
        "cycle_pattern_verdict_",
        "cycle_pattern_rule_",
        "cycle_pattern_support_",
        "cycle_pattern_caution_",
        "cycle_condition_verdict_",
        "cycle_condition_strength_",
        "cycle_condition_climate_need_",
        "cycle_condition_support_",
        "cycle_condition_pressure_",
        "cycle_condition_branch_",
        "cycle_branch_reality_",
        "cycle_polarity_",
        "cycle_source_fit_",
        "cycle_target_fit_",
        "cycle_source_authority_",
        "cycle_target_authority_",
        "cycle_source_reality_",
        "cycle_target_reality_",
        "cycle_chain_",
        "cycle_element_bridge_",
        "cycle_bridge_fit_",
        "cycle_bridge_authority_",
    )
    priority = [code for code in codes if code.startswith(priority_prefixes)]
    pattern = [code for code in codes if code.startswith("cycle_pattern_")]
    condition = [code for code in codes if code.startswith("cycle_condition_")]
    branch_reality = [code for code in codes if code.startswith("cycle_branch_reality_")]
    context = [
        code
        for code in codes
        if code.startswith(("cycle_role_", "cycle_month_fit_", "element_cycle_", "element_cycle_month_fit_"))
    ]
    return list(dict.fromkeys([*priority[:10], *pattern[:6], *condition[:8], *branch_reality[:6], *context[:5]]))


def _cycle_signal_effect(domain: str, signal: dict[str, Any]) -> tuple[dict[str, float], bool]:
    signal_id = str(signal.get("signal_id") or "")
    status = str(signal.get("status") or "")
    source = str(signal.get("source_group") or "")
    target = str(signal.get("target_group") or "")
    groups = [str(group) for group in list(signal.get("groups") or [])]
    judgment = str(signal.get("cycle_judgment") or "")
    polarity = str(signal.get("polarity") or "")

    if signal_id == "wealth_generates_officer_controls_peer":
        if status == "regulates_with_cost":
            effects = {
                "money": {"opportunity": 1, "risk": -2, "change": 1, "probability": 1},
                "career": {"opportunity": 2, "risk": 1, "probability": 1},
                "love": {"risk": -1},
                "marriage": {"risk": -1, "probability": 1},
            }
            return effects.get(domain, {}), True
        effects = {
            "money": {"risk": -4, "probability": 2},
            "career": {"opportunity": 2, "probability": 1},
            "love": {"risk": -1},
            "marriage": {"risk": -2, "probability": 1},
        }
        return effects.get(domain, {}), False

    if signal_id == "wealth_controls_resource_releases_output":
        effects = {
            "money": {"opportunity": 2, "risk": -3, "change": 1, "probability": 2},
            "career": {"opportunity": 2, "change": 1, "probability": 1},
            "love": {"risk": -1, "probability": 1},
            "marriage": {"risk": -1, "probability": 1},
        }
        return effects.get(domain, {}), False

    if signal_id == "resource_controls_output_dosik":
        effects = {
            "money": {"opportunity": -2, "risk": 4, "probability": -2},
            "career": {"opportunity": -1, "risk": 3, "probability": -1},
            "love": {"risk": 2, "probability": -1},
            "marriage": {"risk": 2, "probability": -1},
        }
        return effects.get(domain, {}), True

    if signal_id == "output_generates_wealth_then_officer":
        effects = {
            "money": {"opportunity": 4, "change": 1, "probability": 2},
            "career": {"opportunity": 2, "change": 1, "probability": 1},
            "love": {"opportunity": 1},
            "marriage": {"probability": 1},
        }
        return effects.get(domain, {}), False

    if source == "peer" and target == "wealth" or status == "element_mixed_wealth_competition":
        effects = {
            "money": {"risk": 5, "change": 1, "probability": -2},
            "career": {"risk": 2, "change": 1},
            "love": {"risk": 2, "probability": -1},
            "marriage": {"risk": 2, "probability": -1},
        }
        return effects.get(domain, {}), True

    if source == "officer" and target == "peer":
        effects = {
            "money": {"risk": -3, "probability": 1},
            "career": {"opportunity": 2, "risk": -1, "probability": 1},
            "love": {"risk": -1},
            "marriage": {"risk": -2, "probability": 1},
        }
        return effects.get(domain, {}), False

    if source == "wealth" and target == "resource":
        if "damage" in status or status == "element_damages_useful_force":
            effects = {
                "money": {"opportunity": 1, "risk": 2},
                "career": {"risk": 2, "probability": -1},
                "love": {"risk": 1},
                "marriage": {"risk": 1},
            }
            return effects.get(domain, {}), True
        effects = {
            "money": {"risk": -2, "probability": 1},
            "career": {"opportunity": 1, "probability": 1},
            "love": {"risk": -1},
            "marriage": {"risk": -1},
        }
        return effects.get(domain, {}), False

    if source == "resource" and target == "output":
        if "damage" in status or "dosik" in signal_id:
            effects = {
                "money": {"opportunity": -1, "risk": 3, "probability": -2},
                "career": {"risk": 2, "probability": -1},
                "love": {"risk": 1},
                "marriage": {"risk": 1},
            }
            return effects.get(domain, {}), True
        effects = {
            "money": {"risk": -1},
            "career": {"opportunity": 1, "risk": -1},
            "love": {"risk": -1},
            "marriage": {"risk": -1},
        }
        return effects.get(domain, {}), False

    if source == "output" and target == "officer":
        if "regulates" in status or "sets_boundary" in status:
            effects = {
                "money": {"change": 1},
                "career": {"opportunity": 1, "risk": -3, "change": 1, "probability": 1},
                "love": {"risk": -1},
                "marriage": {"risk": -1},
            }
            return effects.get(domain, {}), False
        effects = {
            "money": {"risk": 1},
            "career": {"risk": 4, "change": 1, "probability": -2},
            "love": {"risk": 2},
            "marriage": {"risk": 2},
        }
        return effects.get(domain, {}), True

    if source == "output" and target == "wealth" or groups == ["output", "wealth"]:
        effects = {
            "money": {"opportunity": 3, "change": 1, "probability": 2},
            "career": {"opportunity": 1, "change": 1},
            "love": {"opportunity": 1},
            "marriage": {"opportunity": 1},
        }
        return effects.get(domain, {}), False

    if source == "wealth" and target == "officer":
        risk_delta = 1 if "mixed" in status or "burden" in status else 0
        effects = {
            "money": {"opportunity": 1, "risk": risk_delta, "probability": 1},
            "career": {"opportunity": 2, "risk": risk_delta, "probability": 1},
            "love": {"probability": 1},
            "marriage": {"opportunity": 1, "probability": 1},
        }
        return effects.get(domain, {}), risk_delta > 0

    if status in {
        "feeds_useful_force",
        "element_feeds_useful_force",
        "regulates_pressure",
        "element_regulates_pressure",
        "connects_function",
        "element_connects_function",
    }:
        return {"opportunity": 1, "risk": -1, "probability": 1}, False
    if status in {"damages_useful_force", "element_damages_useful_force", "conflict_or_overload", "element_conflict_or_overload"}:
        return {"risk": 2, "probability": -1}, True
    if status in {"mixed_control", "mixed_generation", "mixed_chain"}:
        return {"change": 1, "risk": 1}, True
    if judgment in {"useful_generation", "functional_generation", "medicinal_control"} or polarity == "support":
        return {"opportunity": 1, "risk": -1, "probability": 1}, False
    if judgment in {"burden_generation", "damaging_control", "burden_collision", "wealth_competition"} or polarity == "pressure":
        return {"risk": 2, "probability": -1}, True
    if judgment in {"boundary_control", "shared_control_of_burdening_wealth", "strained_generation"} or polarity == "mixed":
        return {"change": 1, "risk": 1}, True
    return {}, False


def _add_cycle_effect(effect: dict[str, float], metric: str, delta: float) -> None:
    if delta:
        effect[metric] = float(effect.get(metric, 0.0) or 0.0) + delta


def _contextual_cycle_signal_effect(
    domain: str,
    signal: dict[str, Any],
    base_effect: dict[str, float],
    has_cost: bool,
) -> tuple[dict[str, float], bool]:
    """Apply month-command, pattern, strength, climate, and branch reality to a cycle effect."""
    effect = dict(base_effect)
    polarity = str(signal.get("polarity") or "mixed")
    governance = dict(signal.get("governance_context") or {})
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    condition = dict(signal.get("condition_context") or {})
    branch_reality = dict(signal.get("branch_reality_context") or {})
    month_cycle_fit = dict(signal.get("month_cycle_fit_context") or {})

    month_fit_verdict = str(month_cycle_fit.get("verdict") or "")
    costly_edge_count = min(4, int(month_cycle_fit.get("costly_edge_count") or 0))
    burden_edge_count = min(4, int(month_cycle_fit.get("burden_edge_count") or 0))
    latent_edge_count = min(4, int(month_cycle_fit.get("latent_edge_count") or 0))
    if month_fit_verdict == "month_cycle_needed":
        _add_cycle_effect(effect, "opportunity", 0.65)
        _add_cycle_effect(effect, "probability", 0.45)
        if polarity == "support":
            _add_cycle_effect(effect, "risk", -0.25)
    elif month_fit_verdict == "month_cycle_needed_with_cost":
        _add_cycle_effect(effect, "opportunity", 0.45)
        _add_cycle_effect(effect, "probability", 0.25)
        _add_cycle_effect(effect, "risk", 0.35)
        has_cost = True
    elif month_fit_verdict == "month_cycle_pressure_with_use":
        _add_cycle_effect(effect, "opportunity", 0.2)
        _add_cycle_effect(effect, "risk", 0.75)
        _add_cycle_effect(effect, "change", 0.35)
        _add_cycle_effect(effect, "probability", -0.25)
        has_cost = True
    elif month_fit_verdict == "month_cycle_burdens_month":
        _add_cycle_effect(effect, "opportunity", -0.35)
        _add_cycle_effect(effect, "risk", 1.05)
        _add_cycle_effect(effect, "probability", -0.55)
        has_cost = True
    elif month_fit_verdict == "month_cycle_auxiliary_use":
        _add_cycle_effect(effect, "opportunity", 0.2)
        _add_cycle_effect(effect, "probability", 0.12)
    elif month_fit_verdict == "month_cycle_auxiliary_pressure":
        _add_cycle_effect(effect, "risk", 0.35)
        _add_cycle_effect(effect, "probability", -0.15)
        has_cost = True

    if costly_edge_count:
        _add_cycle_effect(effect, "risk", 0.18 * costly_edge_count)
        _add_cycle_effect(effect, "change", 0.08 * costly_edge_count)
        has_cost = True
    if burden_edge_count:
        _add_cycle_effect(effect, "opportunity", -0.05 * burden_edge_count)
        _add_cycle_effect(effect, "risk", 0.28 * burden_edge_count)
        _add_cycle_effect(effect, "probability", -0.12 * burden_edge_count)
        has_cost = True
    if latent_edge_count:
        _add_cycle_effect(effect, "probability", -0.1 * latent_edge_count)
        if polarity in {"support", "mixed"}:
            _add_cycle_effect(effect, "risk", 0.12 * latent_edge_count)
        has_cost = True

    if governance.get("touches_month_command"):
        _add_cycle_effect(effect, "change", 0.25)
    governance_verdict = str(governance.get("verdict") or "")
    if governance_verdict in {"governance_supports_cycle", "governance_support_with_caution", "governance_auxiliary_support"}:
        _add_cycle_effect(effect, "opportunity", 0.35)
        _add_cycle_effect(effect, "probability", 0.25)
        if governance_verdict == "governance_support_with_caution":
            _add_cycle_effect(effect, "risk", 0.35)
            has_cost = True
        elif polarity == "support":
            _add_cycle_effect(effect, "risk", -0.25)
    elif governance_verdict in {"governance_warns_cycle", "governance_pressure_with_use", "governance_auxiliary_pressure"}:
        _add_cycle_effect(effect, "risk", 0.65)
        _add_cycle_effect(effect, "probability", -0.25)
        has_cost = True
        if governance_verdict == "governance_pressure_with_use":
            _add_cycle_effect(effect, "opportunity", 0.2)

    support_strength = min(3.2, float(pattern_cycle.get("support_strength") or 0.0))
    caution_strength = min(3.2, float(pattern_cycle.get("caution_strength") or 0.0))
    support_factor = support_strength / 2.0
    caution_factor = caution_strength / 2.0
    if support_strength:
        if polarity == "pressure":
            _add_cycle_effect(effect, "risk", -0.35 * support_factor)
            _add_cycle_effect(effect, "probability", 0.2 * support_factor)
        else:
            _add_cycle_effect(effect, "opportunity", 0.55 * support_factor)
            _add_cycle_effect(effect, "probability", 0.35 * support_factor)
            if polarity == "support":
                _add_cycle_effect(effect, "risk", -0.25 * support_factor)
    if caution_strength:
        _add_cycle_effect(effect, "risk", 0.75 * caution_factor)
        _add_cycle_effect(effect, "probability", -0.35 * caution_factor)
        if polarity == "support":
            _add_cycle_effect(effect, "opportunity", -0.2 * caution_factor)
        has_cost = True

    condition_verdict = str(condition.get("verdict") or "")
    support_tag_count = min(3, len(list(condition.get("support_tags") or [])))
    pressure_tag_count = min(3, len(list(condition.get("pressure_tags") or [])))
    if condition_verdict == "condition_supports_cycle":
        if polarity == "pressure":
            _add_cycle_effect(effect, "risk", -0.55)
            _add_cycle_effect(effect, "probability", 0.25)
        else:
            _add_cycle_effect(effect, "opportunity", 0.7)
            _add_cycle_effect(effect, "probability", 0.45)
            _add_cycle_effect(effect, "risk", -0.3)
    elif condition_verdict == "condition_support_with_cost":
        _add_cycle_effect(effect, "opportunity", 0.5)
        _add_cycle_effect(effect, "risk", 0.35)
        _add_cycle_effect(effect, "change", 0.35)
        has_cost = True
    elif condition_verdict == "condition_mixed_cycle":
        _add_cycle_effect(effect, "opportunity", 0.25)
        _add_cycle_effect(effect, "risk", 0.65)
        _add_cycle_effect(effect, "change", 0.45)
        _add_cycle_effect(effect, "probability", -0.2)
        has_cost = True
    elif condition_verdict == "condition_pressure_with_use":
        _add_cycle_effect(effect, "opportunity", 0.2)
        _add_cycle_effect(effect, "risk", 0.95)
        _add_cycle_effect(effect, "probability", -0.55)
        has_cost = True
    elif condition_verdict == "condition_pressures_cycle":
        _add_cycle_effect(effect, "opportunity", -0.25)
        _add_cycle_effect(effect, "risk", 1.15)
        _add_cycle_effect(effect, "probability", -0.75)
        has_cost = True

    if support_tag_count and pressure_tag_count:
        _add_cycle_effect(effect, "change", 0.15 * min(support_tag_count, pressure_tag_count))
    elif support_tag_count and polarity in {"support", "mixed"}:
        _add_cycle_effect(effect, "probability", 0.1 * support_tag_count)
    if pressure_tag_count:
        _add_cycle_effect(effect, "risk", 0.12 * pressure_tag_count)
        if polarity in {"support", "mixed"}:
            has_cost = True

    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade in {"month_branch_visible", "month_hidden_protruded"}:
        if polarity == "support":
            _add_cycle_effect(effect, "opportunity", 0.45)
            _add_cycle_effect(effect, "probability", 0.45)
            _add_cycle_effect(effect, "change", 0.2)
        elif polarity == "pressure":
            _add_cycle_effect(effect, "risk", 0.85)
            _add_cycle_effect(effect, "probability", -0.25)
            has_cost = True
        else:
            _add_cycle_effect(effect, "change", 0.55)
            _add_cycle_effect(effect, "risk", 0.35)
            has_cost = True
    elif branch_grade in {"branch_dominant", "hidden_to_visible"}:
        if polarity == "support":
            _add_cycle_effect(effect, "opportunity", 0.35)
            _add_cycle_effect(effect, "probability", 0.3)
        elif polarity == "pressure":
            _add_cycle_effect(effect, "risk", 0.65)
            _add_cycle_effect(effect, "probability", -0.2)
            has_cost = True
        else:
            _add_cycle_effect(effect, "change", 0.4)
            _add_cycle_effect(effect, "risk", 0.25)
            has_cost = True
    elif branch_grade == "branch_rooted":
        if polarity == "support":
            _add_cycle_effect(effect, "probability", 0.2)
        elif polarity == "pressure":
            _add_cycle_effect(effect, "risk", 0.35)
            has_cost = True

    return effect, has_cost


def _flow_contextual_cycle_signal_effect(
    domain: str,
    signal: dict[str, Any],
    flow: FlowSignal,
    base_effect: dict[str, float],
    has_cost: bool,
    activation: dict[str, Any] | None = None,
) -> tuple[dict[str, float], bool]:
    effect = dict(base_effect)
    activation = activation or _cycle_signal_flow_activation_context(domain, signal, flow)
    grade = str(activation.get("grade") or "")
    if grade == "flow_not_triggered":
        return effect, has_cost

    polarity = str(signal.get("polarity") or "mixed")
    strength = min(2.4, max(0.4, float(activation.get("strength") or 0.0) / 2.0))
    relation_hits = set(str(item) for item in list(activation.get("relation_hits") or []))
    disruptive = bool(relation_hits & {"clash", "punishment", "harm", "break", "self_punishment"})
    combining = bool(relation_hits & {"six_combine", "three_harmony", "three_harmony_half"})
    edge_flow_contexts = [edge for edge in list(activation.get("edge_flow_contexts") or []) if isinstance(edge, dict)]

    if grade in {"flow_branch_relation_triggers_cycle", "flow_annual_daeun_compounds_cycle"}:
        multiplier = 1.0
    elif grade in {"flow_stem_branch_triggers_cycle", "flow_branch_triggers_cycle"}:
        multiplier = 0.78
    elif grade in {"flow_hidden_triggers_cycle", "flow_stem_triggers_cycle"}:
        multiplier = 0.55
    else:
        multiplier = 0.35

    if polarity == "support":
        _add_cycle_effect(effect, "opportunity", 0.5 * strength * multiplier)
        _add_cycle_effect(effect, "probability", 0.35 * strength * multiplier)
        if combining:
            _add_cycle_effect(effect, "change", 0.2 * strength * multiplier)
        if disruptive:
            _add_cycle_effect(effect, "risk", 0.25 * strength * multiplier)
            _add_cycle_effect(effect, "change", 0.25 * strength * multiplier)
            has_cost = True
    elif polarity == "pressure":
        _add_cycle_effect(effect, "risk", 0.65 * strength * multiplier)
        _add_cycle_effect(effect, "probability", -0.3 * strength * multiplier)
        if disruptive:
            _add_cycle_effect(effect, "risk", 0.35 * strength * multiplier)
            _add_cycle_effect(effect, "change", 0.35 * strength * multiplier)
        has_cost = True
    else:
        _add_cycle_effect(effect, "change", 0.55 * strength * multiplier)
        _add_cycle_effect(effect, "risk", 0.35 * strength * multiplier)
        if combining:
            _add_cycle_effect(effect, "opportunity", 0.2 * strength * multiplier)
        if disruptive:
            _add_cycle_effect(effect, "risk", 0.25 * strength * multiplier)
        has_cost = True

    for edge in edge_flow_contexts[:4]:
        if not (edge.get("active") or edge.get("soft_active")):
            continue
        edge_factor = 1.0 if edge.get("active") else 0.45
        fit = str(edge.get("month_fit_verdict") or "")
        if fit in {"edge_needed", "edge_useful"}:
            _add_cycle_effect(effect, "opportunity", 0.18 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "probability", 0.14 * edge_factor * strength * multiplier)
        elif fit == "edge_useful_with_cost":
            _add_cycle_effect(effect, "opportunity", 0.12 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "risk", 0.12 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "change", 0.08 * edge_factor * strength * multiplier)
            has_cost = True
        elif fit == "edge_pressure_with_use":
            _add_cycle_effect(effect, "opportunity", 0.08 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "risk", 0.24 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "probability", -0.08 * edge_factor * strength * multiplier)
            has_cost = True
        elif fit in {"edge_burdens_month", "edge_pressure"}:
            _add_cycle_effect(effect, "risk", 0.32 * edge_factor * strength * multiplier)
            _add_cycle_effect(effect, "probability", -0.16 * edge_factor * strength * multiplier)
            has_cost = True

    return effect, has_cost


def _cycle_regulation_adjustments(structure: ChartStructure, flow: FlowSignal, domain: str) -> dict[str, Any]:
    profile = structure.cycle_regulation_profile or build_cycle_regulation_profile(structure)
    totals: dict[str, Any] = {
        "opportunity": 0.0,
        "risk": 0.0,
        "change": 0.0,
        "probability": 0.0,
        "basis_codes": [],
        "counter_signals": [],
    }
    domain_signals = [
        signal
        for signal in list(profile.get("signals") or [])
        if domain in list(signal.get("domain_links") or [])
    ]
    chain_signals = [signal for signal in domain_signals if signal.get("relation") == "chain"]
    ten_god_edge_signals = [
        signal for signal in domain_signals if signal.get("relation") in {"generates", "controls"}
    ]
    element_edge_signals = [
        signal for signal in domain_signals if signal.get("relation") in {"element_generates", "element_controls"}
    ]
    bridge_signals = [signal for signal in domain_signals if signal.get("relation") == "element_bridge"]
    exception_signals = [signal for signal in domain_signals if signal.get("relation") == "element_exception"]
    branch_signals = [signal for signal in domain_signals if signal.get("relation") == "branch_cycle"]
    stem_combine_signals = [signal for signal in domain_signals if signal.get("relation") == "stem_combine"]
    rooting_signals = [
        signal for signal in domain_signals if signal.get("relation") in {"hidden_protrusion", "visible_root"}
    ]
    prioritized_rooting_signals = sorted(
        rooting_signals,
        key=lambda signal: _cycle_signal_selection_rank(domain, signal),
        reverse=True,
    )
    mandatory_reality_signals = sorted(
        [
            *branch_signals[:4],
            *stem_combine_signals[:3],
            *prioritized_rooting_signals[:4],
        ],
        key=lambda signal: _cycle_signal_selection_rank(domain, signal),
        reverse=True,
    )
    supportive_signals = [signal for signal in domain_signals if signal.get("polarity") == "support"]
    mixed_signals = [signal for signal in domain_signals if signal.get("polarity") == "mixed"]
    pressure_signals = [signal for signal in domain_signals if signal.get("polarity") == "pressure"]
    selected_signals = [
        *mandatory_reality_signals,
        *prioritized_rooting_signals[:8],
        *chain_signals[:5],
        *[signal for signal in chain_signals if signal.get("polarity") == "pressure"][:3],
        *ten_god_edge_signals[:6],
        *[signal for signal in ten_god_edge_signals if signal.get("polarity") == "pressure"][:3],
        *element_edge_signals[:6],
        *[signal for signal in element_edge_signals if signal.get("polarity") == "pressure"][:3],
        *exception_signals[:6],
        *[signal for signal in exception_signals if signal.get("polarity") == "pressure"][:4],
        *bridge_signals[:5],
        *branch_signals[:6],
        *[signal for signal in branch_signals if signal.get("polarity") == "pressure"][:4],
        *stem_combine_signals[:5],
        *[signal for signal in stem_combine_signals if signal.get("polarity") == "pressure"][:3],
        *[signal for signal in prioritized_rooting_signals if signal.get("polarity") == "pressure"][:4],
        *supportive_signals[:4],
        *mixed_signals[:4],
        *pressure_signals[:4],
        *domain_signals[:6],
    ]
    signals = list({str(signal.get("signal_id") or ""): signal for signal in selected_signals}.values())[:18]
    for signal in signals:
        effect, has_cost = _cycle_signal_effect(domain, signal)
        if not effect:
            continue
        activation = _cycle_signal_flow_activation_context(domain, signal, flow)
        effect, has_cost = _contextual_cycle_signal_effect(domain, signal, effect, has_cost)
        effect, has_cost = _flow_contextual_cycle_signal_effect(
            domain,
            signal,
            flow,
            effect,
            has_cost,
            activation=activation,
        )
        weight = _cycle_signal_weight(domain, signal, flow, activation=activation)
        for metric in ("opportunity", "risk", "change", "probability"):
            totals[metric] += _scale_delta(float(effect.get(metric, 0) or 0), weight)
        status = str(signal.get("status") or "")
        signal_id = str(signal.get("signal_id") or "")
        basis_code = f"cycle_regulation_{domain}_{signal_id}_{status}"
        if any(float(effect.get(metric, 0) or 0) > 0 for metric in ("opportunity", "probability")) or float(effect.get("risk", 0) or 0) < 0:
            totals["basis_codes"].append(basis_code)
        if has_cost or float(effect.get("risk", 0) or 0) > 0 or float(effect.get("probability", 0) or 0) < 0:
            totals["counter_signals"].append(f"{basis_code}_cost")
        flow_codes = _cycle_signal_flow_codes(
            domain,
            signal,
            flow,
            activation=activation,
            hits={
                "hit_points": list(activation.get("hit_points") or []),
                "hit_elements": list(activation.get("hit_elements") or []),
                "hit_groups": list(activation.get("hit_groups") or []),
            },
        )
        totals["basis_codes"].extend(flow_codes["basis_codes"])
        totals["counter_signals"].extend(flow_codes["counter_signals"])
        for code in _cycle_signal_basis_codes(signal):
            text = str(code)
            if text:
                totals["basis_codes"].append(text)

    return _bounded_cycle_regulation_adjustments(
        opportunity=round(totals["opportunity"]),
        risk=round(totals["risk"]),
        change=round(totals["change"]),
        probability=round(totals["probability"]),
        basis_codes=totals["basis_codes"],
        counter_signals=totals["counter_signals"],
    )


def _event_keywords(domain: str, sub_event_type: str, basis_codes: list[str], counter_signals: list[str]) -> list[str]:
    keywords = list(EVENT_KEYWORDS_BY_TYPE.get(sub_event_type, [domain]))
    combined_codes = basis_codes + counter_signals

    if any("spouse_star" in code for code in combined_codes):
        keywords.append("배우자성 활성")
    if any("travel_horse" in code for code in combined_codes):
        keywords.append("이동·변동")
    if any("peach_blossom" in code for code in combined_codes):
        keywords.append("노출·인기")
    if any("six_combine" in code or "combine" in code for code in combined_codes):
        keywords.append("연결·계약")
    if any("sang_gwan" in code for code in combined_codes):
        keywords.append("표현·평판")
    if any("clash" in code for code in combined_codes):
        keywords.append("변화·충돌")
    if any("break" in code or "harm" in code or "punishment" in code for code in combined_codes):
        keywords.append("조건 점검")

    return list(dict.fromkeys(keywords))[:6]


def _personality_filter(structure: ChartStructure) -> str:
    tags = set(structure.structure_tags)
    if "strength_weak" in tags or "strength_very_weak" in tags:
        return "큰 기회를 잡기 전에 지원 구조, 속도 조절, 역할 명확성이 먼저 필요하다"
    if "strength_strong" in tags or "strength_very_strong" in tags:
        return "성과, 책임, 눈에 보이는 결과를 적극적으로 쓸 때 반응이 좋다"
    if "temperature_cold" in tags:
        return "결과가 분명해지기 전에 온기, 속도, 노출, 활동성이 필요하다"
    return "기회와 위험을 구체적인 선택지로 분리할 때 가장 안정적으로 움직인다"


def _domain_personality_filter(structure: ChartStructure, domain: str) -> str:
    tags = set(structure.structure_tags)
    by_domain = {
        "money": {
            "weak": "당신은 돈이 움직일 때 받을 몫과 나갈 돈을 먼저 가르는 사람입니다",
            "strong": "당신은 성과가 금전 보상으로 바뀌는 순간을 빠르게 알아차리는 편입니다",
            "cold": "당신은 숫자로 확인되는 수입과 지출에 반응이 빠른 편입니다",
            "neutral": "당신은 돈 문제를 감각보다 기준으로 처리할 때 결과가 분명해집니다",
        },
        "career": {
            "weak": "당신은 역할이 커질수록 권한과 평가 기준을 먼저 확인하는 사람입니다",
            "strong": "당신은 책임이 커지는 자리에서 추진력이 살아나는 편입니다",
            "cold": "당신은 준비와 검토가 갖춰진 뒤에 직업적 성과가 분명해지는 편입니다",
            "neutral": "당신은 맡은 일의 범위가 분명할 때 실력이 가장 잘 드러납니다",
        },
        "love": {
            "weak": "당신은 호감이 생겨도 표현보다 관계의 안정감을 먼저 확인하는 편입니다",
            "strong": "당신은 마음이 움직이면 관계를 실제 만남으로 끌고 가는 힘이 있습니다",
            "cold": "당신은 상대의 태도를 오래 살핀 뒤 마음을 여는 편입니다",
            "neutral": "당신은 감정이 분명해도 관계의 속도가 맞아야 편안해집니다",
        },
        "marriage": {
            "weak": "당신은 감정보다 생활 기준이 맞아야 결혼 결정을 편하게 받아들이는 편입니다",
            "strong": "당신은 한번 결심하면 관계를 생활의 약속으로 밀고 가는 힘이 있습니다",
            "cold": "당신은 생활 조건이 확인되어야 결혼 결정을 안정적으로 내리는 편입니다",
            "neutral": "당신은 사랑의 확신이 생활의 기준으로 옮겨질 때 결혼운이 안정됩니다",
        },
    }
    profile = by_domain.get(domain, by_domain["career"])
    if "strength_weak" in tags or "strength_very_weak" in tags:
        return profile["weak"]
    if "strength_strong" in tags or "strength_very_strong" in tags:
        return profile["strong"]
    if "temperature_cold" in tags:
        return profile["cold"]
    return profile["neutral"]


def _focused_sub_periods(flow: FlowSignal, domain: str) -> list[SubPeriodSignal]:
    focused = [
        item
        for item in flow.sub_period_signals
        if domain in item.domain_focus and item.intensity_score >= 50
    ]
    if focused:
        focused.sort(key=lambda item: item.intensity_score, reverse=True)
        return focused[:5]

    fallback = [
        replace(item, intensity_score=max(50, item.intensity_score))
        for item in flow.sub_period_signals
        if domain in item.domain_focus
    ]
    fallback.sort(key=lambda item: (item.intensity_score, item.period_scope == "quarter"), reverse=True)
    return fallback[:3]


def _timing_markers(focused: list[SubPeriodSignal]) -> list[str]:
    markers: list[str] = []
    for item in focused:
        if item.start_datetime and item.end_datetime:
            markers.append(
                f"{item.period_label}|{item.start_datetime}~{item.end_datetime}|{item.monthly_phase}|{item.intensity_score}"
            )
        else:
            markers.append(f"{item.period_label}|{item.monthly_phase}|{item.intensity_score}")
    return markers


def _timing_windows(focused: list[SubPeriodSignal]) -> list[dict[str, Any]]:
    return [
        {
            "period_label": item.period_label,
            "period_scope": item.period_scope,
            "pillar": item.pillar,
            "start_datetime": item.start_datetime,
            "end_datetime": item.end_datetime,
            "monthly_phase": item.monthly_phase,
            "intensity_score": item.intensity_score,
            "domain_focus": list(item.domain_focus),
            "basis_codes": list(item.basis_codes),
            "counter_signals": list(item.counter_signals),
        }
        for item in focused
    ]


def build_event_packets(
    chart: BirthChartResult,
    structure: ChartStructure,
    flow_signals: list[FlowSignal],
    domains: list[Domain] | None = None,
    relationship_status: RelationshipStatus = "unknown",
) -> list[EventPacket]:
    selected_domains = domains or list(DOMAIN_ORDER)  # type: ignore[assignment]
    packets: list[EventPacket] = []

    for flow in flow_signals:
        for domain in selected_domains:
            data: dict[str, Any] = flow.domain_scores[domain]
            raw_opportunity = data["opportunity"]
            raw_risk = data["risk"]
            raw_change = data["change"]
            raw_probability = data["probability"]
            opportunity = raw_opportunity
            risk = raw_risk
            change = raw_change
            probability = raw_probability
            basis_codes = list(data["basis_codes"])
            counter_signals = list(data["counter_signals"])
            combination_adjustments = _combination_adjustments(structure, domain)
            opportunity = _clip(opportunity + combination_adjustments["opportunity"])
            risk = _clip(risk + combination_adjustments["risk"])
            change = _clip(change + combination_adjustments["change"])
            probability = _clip(probability + combination_adjustments["probability"])
            basis_codes = combination_adjustments["basis_codes"] + basis_codes
            counter_signals = combination_adjustments["counter_signals"] + counter_signals
            natal_adjustments = _natal_position_adjustments(structure, domain)
            opportunity = _clip(opportunity + natal_adjustments["opportunity"])
            risk = _clip(risk + natal_adjustments["risk"])
            change = _clip(change + natal_adjustments["change"])
            probability = _clip(probability + natal_adjustments["probability"])
            basis_codes = natal_adjustments["basis_codes"] + basis_codes
            counter_signals = natal_adjustments["counter_signals"] + counter_signals
            pattern_adjustments = _pattern_need_adjustments(structure, flow, domain)
            opportunity = _clip(opportunity + pattern_adjustments["opportunity"])
            risk = _clip(risk + pattern_adjustments["risk"])
            change = _clip(change + pattern_adjustments["change"])
            probability = _clip(probability + pattern_adjustments["probability"])
            basis_codes = pattern_adjustments["basis_codes"] + basis_codes
            counter_signals = pattern_adjustments["counter_signals"] + counter_signals
            cycle_adjustments = _cycle_regulation_adjustments(structure, flow, domain)
            opportunity = _clip(opportunity + cycle_adjustments["opportunity"])
            risk = _clip(risk + cycle_adjustments["risk"])
            change = _clip(change + cycle_adjustments["change"])
            probability = _clip(probability + cycle_adjustments["probability"])
            basis_codes = cycle_adjustments["basis_codes"] + basis_codes
            counter_signals = cycle_adjustments["counter_signals"] + counter_signals
            feature_axes = _feature_axes_for_domain(structure, domain)
            feature_adjustments = _feature_axis_adjustments(domain, feature_axes)
            opportunity = _clip(opportunity + feature_adjustments["opportunity"])
            risk = _clip(risk + feature_adjustments["risk"])
            change = _clip(change + feature_adjustments["change"])
            probability = _clip(probability + feature_adjustments["probability"])
            basis_codes.extend(feature_adjustments["basis_codes"])
            counter_signals.extend(feature_adjustments["counter_signals"])
            if chart.boundary_sensitive:
                counter_signals.append(f"boundary_sensitive_{chart.boundary_type}")
            opportunity = _bounded_adjusted_score(
                raw_opportunity,
                opportunity,
                "opportunity",
                EVENT_PACKET_ADJUSTMENT_LIMITS,
            )
            risk = _bounded_adjusted_score(raw_risk, risk, "risk", EVENT_PACKET_ADJUSTMENT_LIMITS)
            change = _bounded_adjusted_score(raw_change, change, "change", EVENT_PACKET_ADJUSTMENT_LIMITS)
            probability = _bounded_adjusted_score(
                raw_probability,
                probability,
                "probability",
                EVENT_PACKET_ADJUSTMENT_LIMITS,
            )

            confidence = _confidence(probability, len(basis_codes), len(counter_signals), chart.boundary_sensitive)
            expression_strength = _expression_strength(probability, risk, confidence)
            sub_event_type = _event_type(domain, opportunity, risk, change, feature_axes)
            conflict_status = _conflict_status(risk, len(counter_signals))
            domain_text = EVENT_TEXT[domain]
            main_action = EVENT_ACTION_BY_TYPE.get(sub_event_type, domain_text["action"])
            risk_path = EVENT_RISK_BY_TYPE.get(sub_event_type, domain_text["risk"])

            output_allowed_level = "basic" if probability >= 62 and confidence != "restricted" else "premium"
            if confidence == "restricted":
                output_allowed_level = "restricted"

            focused_timing = _focused_sub_periods(flow, domain)
            timing_markers = _timing_markers(focused_timing)
            timing_windows = _timing_windows(focused_timing)
            packet = EventPacket(
                packet_id=f"{flow.year}_{domain}_{sub_event_type}",
                domain=domain,
                sub_event_type=sub_event_type,
                period_label=flow.period_label,
                period_scope=flow.period_scope,
                opportunity_score=opportunity,
                risk_score=risk,
                change_score=change,
                event_probability_score=probability,
                confidence=confidence,
                expression_strength=expression_strength,
                event_form=domain_text["form"],
                realization_path=domain_text["realization"],
                risk_path=risk_path,
                timing_strength="annual" if flow.daeun_pillar is None else "daeun_and_annual",
                primary_scene_sentence=domain_text["scene"],
                main_action=main_action,
                risk_topic=domain_text["topic"],
                event_keywords=_event_keywords(domain, sub_event_type, basis_codes, counter_signals),
                personality_filter=_domain_personality_filter(structure, domain),
                domain_links=[item for item in DOMAIN_ORDER if item != domain and flow.domain_scores[item]["probability"] >= 62],
                basis_codes=list(dict.fromkeys(basis_codes + flow.basis_codes)),
                counter_signals=list(dict.fromkeys(counter_signals + flow.counter_signals)),
                conflict_status=conflict_status,
                output_allowed_level=output_allowed_level,
                timing_markers=timing_markers,
                timing_windows=timing_windows,
                relationship_status=relationship_status,
                feature_axes=feature_axes,
            )
            packet = EventPacket(
                **{
                    **packet.__dict__,
                    "common_template_id": select_common_template(packet),
                    "domain_template_id": select_domain_template(packet, relationship_status),
                    "type_template_id": select_type_template(structure),
                    "template_slots": build_template_slots(packet, structure, relationship_status),
                }
            )
            packets.append(replace(packet, rendered_preview=render_event_preview(packet)))

    return packets
