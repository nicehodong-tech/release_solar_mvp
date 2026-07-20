"""Gyeokguk-specific ten-god action dictionary.

The same ten-god chain must be read differently by pattern. For example,
wealth controlling resource is a regulatory action inside a wealth pattern,
but it attacks the center when the pattern itself is a resource pattern. This
module records that distinction before any customer-facing wording is made.
"""

from __future__ import annotations

from .constants import (
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    TEN_GOD_GROUPS,
)
from .models import (
    BranchInteraction,
    ElementProfile,
    GyeokgukTenGodActionMatch,
    GyeokgukTenGodActionRule,
    MonthGovernanceProfile,
    PositionSignal,
    TenGodProfile,
)
from .patterns import REGULAR_PATTERN_BY_TEN_GOD, REGULAR_PATTERN_NEED_RULES


GYEOKGUK_TEN_GOD_ACTION_VERSION = "gyeokguk_ten_god_actions_v1"

MONTH_SUPPORT_STATES = {"supports_month_command", "usable_by_month_command"}
MONTH_MIXED_STATES = {"mixed_by_month_command"}
MONTH_PRESSURE_STATES = {"harms_month_command", "burdensome_by_month_command"}

FUNCTIONAL_ROLE_LABELS = {
    "pattern_center": "격국 중심",
    "supporting_god": "상신",
    "rescuing_god": "구신",
    "adverse_god": "기신",
    "conditional_god": "조건부 작용",
    "inactive": "미발동",
}

GYEOKGUK_ACTION_JUDGMENT_ORDER_LABELS = [
    ("month_command", "월령"),
    ("gyeokguk", "격국"),
    ("day_master_strength", "일간 강약"),
    ("climate", "조후"),
    ("protrusion", "투출"),
    ("rooting", "통근"),
    ("position", "위치"),
    ("hidden_stems", "지장간"),
    ("branch_interactions", "합충형파해"),
    ("flow_activation", "대운·세운 발동"),
]

GYEOKGUK_ACTION_JUDGMENT_ORDER = [
    key for key, _label in GYEOKGUK_ACTION_JUDGMENT_ORDER_LABELS
]


def gyeokguk_action_judgment_basis_codes(prefix: str) -> list[str]:
    """Expose the shared gyeokguk judgment order in rule basis codes."""

    return [
        *(f"{prefix}_judgment_step:{index}:{step}" for index, step in enumerate(GYEOKGUK_ACTION_JUDGMENT_ORDER, start=1)),
        f"{prefix}_luck_activation:daeun_seun",
    ]

TEN_GODS = [
    "bi_gyeon",
    "geob_jae",
    "sik_sin",
    "sang_gwan",
    "pyeon_jae",
    "jeong_jae",
    "pyeon_gwan",
    "jeong_gwan",
    "pyeon_in",
    "jeong_in",
]

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

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

PATTERN_CENTER_BY_PATTERN = {
    pattern: ten_god
    for ten_god, pattern in REGULAR_PATTERN_BY_TEN_GOD.items()
}

GROUP_GENERATES = {
    "resource": "peer",
    "peer": "output",
    "output": "wealth",
    "wealth": "officer",
    "officer": "resource",
}

GROUP_CONTROLS = {
    "peer": "wealth",
    "wealth": "resource",
    "resource": "output",
    "output": "officer",
    "officer": "peer",
}

MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS = {
    "siksang_saengjae",
    "jaesaenggwan",
    "gwanin_sangsaeng",
    "salin_sangsaeng",
    "siksin_jesal",
    "sanggwan_gyeongwan",
    "jaegeukin",
    "bigeop_jaengjae",
    "inseong_dosik",
    "jaesaengsal",
    "gwansal_honhap",
    "inbi_overload",
    "siksang_overload",
    "jaeda_sinyak_risk",
    "gwansal_overload",
}

CORE_SINGLE_CLASSICAL_TAGS_REQUIRING_CRITICAL_LENS = set(MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS)

CLASSICAL_ACTION_MECHANICS = {
    "gyeokguk_specific_adjustment": {
        "flow": "pattern_specific_adjustment",
        "disease": "actor_role_is_read_without_pattern_context",
        "medicine": "actor_role_is_judged_by_month_command_pattern_and_position",
        "events": ("judgment", "work", "money", "relationship"),
    },
    "siksang_saengjae": {
        "flow": "output_generates_wealth",
        "disease": "unpriced_output_or_output_without_ownership",
        "medicine": "repeatable_product_or_service_creates_income",
        "events": ("output", "income", "money", "asset"),
    },
    "jaesaenggwan": {
        "flow": "wealth_generates_officer",
        "disease": "money_becomes_responsibility_without_authority",
        "medicine": "resource_contract_and_compensation_formalize_role",
        "events": ("money", "responsibility", "work", "evaluation"),
    },
    "gwanin_sangsaeng": {
        "flow": "officer_generates_resource",
        "disease": "title_or_duty_without_documented_support",
        "medicine": "office_role_is_backed_by_document_license_and_reputation",
        "events": ("work", "document", "evaluation", "authority"),
    },
    "salin_sangsaeng": {
        "flow": "killing_generates_resource",
        "disease": "pressure_without_protection_or_method",
        "medicine": "pressure_is_absorbed_by_learning_document_and_skill",
        "events": ("responsibility", "document", "work", "reputation"),
    },
    "siksin_jesal": {
        "flow": "eating_god_controls_killing",
        "disease": "pressure_without_handled_method",
        "medicine": "practical_skill_controls_risk_and_heavy_responsibility",
        "events": ("output", "responsibility", "work", "authority"),
    },
    "sanggwan_gyeongwan": {
        "flow": "hurting_officer_controls_officer",
        "disease": "expression_or_reform_challenges_official_order",
        "medicine": "necessary_correction_when_official_order_is_excessive",
        "events": ("evaluation", "authority", "work", "relationship"),
    },
    "jaegeukin": {
        "flow": "wealth_controls_resource",
        "disease": "money_or_reality_damages_document_protection_or_learning",
        "medicine": "reality_requirement_checks_excessive_theory_or_dependence",
        "events": ("money", "document", "asset", "judgment"),
    },
    "bigeop_jaengjae": {
        "flow": "peer_controls_wealth",
        "disease": "people_compete_over_ownership_or_share",
        "medicine": "rules_contract_and_role_boundary_protect_wealth",
        "events": ("people", "money", "asset", "relationship"),
    },
    "inseong_dosik": {
        "flow": "resource_controls_output",
        "disease": "preparation_document_or_thought_blocks_output",
        "medicine": "right_document_and_method_refine_output_before_release",
        "events": ("document", "output", "judgment", "work"),
    },
    "jaesaengsal": {
        "flow": "wealth_generates_killing",
        "disease": "money_or_expansion_feeds_risk_pressure_or_liability",
        "medicine": "resource_and_method_absorb_expansion_pressure",
        "events": ("money", "responsibility", "work", "risk"),
    },
    "gwansal_honhap": {
        "flow": "officer_and_killing_mixed",
        "disease": "proper_role_and_excessive_pressure_are_confused",
        "medicine": "separate_official_duty_from_risk_pressure",
        "events": ("work", "responsibility", "evaluation", "authority"),
    },
    "inbi_overload": {
        "flow": "resource_generates_peer_overload",
        "disease": "support_and_self_assertion_delay_execution",
        "medicine": "clear_external_task_turns_preparation_into_action",
        "events": ("judgment", "document", "people", "work"),
    },
    "siksang_overload": {
        "flow": "output_same_group_overload",
        "disease": "too_many_words_outputs_or_attempts_without_standard",
        "medicine": "select_repeatable_output_and_attach_compensation_rule",
        "events": ("output", "evaluation", "work", "income"),
    },
    "jaeda_sinyak_risk": {
        "flow": "wealth_exceeds_day_master_capacity",
        "disease": "money_asset_or_contract_exceeds_capacity_to_hold",
        "medicine": "authority_document_and_support_define_safe_capacity",
        "events": ("money", "asset", "responsibility", "document"),
    },
    "gwansal_overload": {
        "flow": "officer_killing_exceeds_day_master_capacity",
        "disease": "role_pressure_and_evaluation_exceed_capacity",
        "medicine": "resource_method_and_clear_authority_absorb_pressure",
        "events": ("responsibility", "work", "evaluation", "health"),
    },
    "jaeseong_generates_gwanseong": {
        "flow": "wealth_generates_officer",
        "disease": "resource_or_money_turns_into_duty_before_capacity_is_set",
        "medicine": "contract_compensation_and_authority_align",
        "events": ("money", "work", "responsibility", "evaluation"),
    },
    "gwanseong_generates_inseong": {
        "flow": "officer_generates_resource",
        "disease": "duty_demands_protection_that_is_not_ready",
        "medicine": "duty_is_supported_by_license_document_and_learning",
        "events": ("work", "document", "evaluation", "authority"),
    },
    "siksang_controls_gwanseong": {
        "flow": "output_controls_officer",
        "disease": "expression_or_result_challenges_role_order",
        "medicine": "result_based_correction_refines_authority",
        "events": ("output", "authority", "evaluation", "work"),
    },
    "wealth_controls_resource": {
        "flow": "wealth_controls_resource",
        "disease": "reality_money_or_contract_damages_document_support",
        "medicine": "reality_requirement_checks_resource_excess",
        "events": ("money", "document", "asset", "judgment"),
    },
    "bigeop_controls_wealth": {
        "flow": "peer_controls_wealth",
        "disease": "people_interfere_with_wealth_boundary",
        "medicine": "ownership_share_and_contract_boundary_are_fixed",
        "events": ("people", "money", "asset", "relationship"),
    },
    "inseong_controls_output": {
        "flow": "resource_controls_output",
        "disease": "preparation_blocks_release",
        "medicine": "method_and_document_improve_output_quality",
        "events": ("document", "output", "judgment", "work"),
    },
    "gwanseong_controls_bigeop": {
        "flow": "officer_controls_peer",
        "disease": "rules_press_self_or_competitors",
        "medicine": "authority_and_rule_settle_peer_competition",
        "events": ("work", "responsibility", "people", "money"),
    },
    "bigeop_generates_siksang": {
        "flow": "peer_generates_output",
        "disease": "peer_force_scattered_into_unpriced_output",
        "medicine": "team_or_self_base_produces_repeatable_result",
        "events": ("people", "output", "work", "income"),
    },
    "inseong_generates_bigeop": {
        "flow": "resource_generates_peer",
        "disease": "support_feeds_self_assertion_without_execution",
        "medicine": "learning_and_document_build_self_base",
        "events": ("document", "judgment", "people", "work"),
    },
    "gwanseong_same_group": {
        "flow": "officer_same_group",
        "disease": "official_role_and_pressure_are_overloaded",
        "medicine": "role_authority_and_responsibility_are_separated",
        "events": ("work", "responsibility", "evaluation", "authority"),
    },
    "wealth_same_group": {
        "flow": "wealth_same_group",
        "disease": "money_contract_or_asset_becomes_too_large_to_hold",
        "medicine": "cashflow_ownership_and_contract_are_separated",
        "events": ("money", "asset", "income", "document"),
    },
    "siksang_same_group": {
        "flow": "output_same_group",
        "disease": "output_expression_or_attempts_are_overextended",
        "medicine": "standardize_output_and_attach_clear_market_route",
        "events": ("output", "evaluation", "work", "income"),
    },
    "inseong_same_group": {
        "flow": "resource_same_group",
        "disease": "document_learning_or_protection_is_overloaded",
        "medicine": "use_resource_as_basis_not_delay",
        "events": ("document", "judgment", "work", "relationship"),
    },
    "bigeop_same_group": {
        "flow": "peer_same_group",
        "disease": "self_or_peer_force_is_overloaded",
        "medicine": "role_boundary_and_share_rule_define_peer_force",
        "events": ("people", "money", "relationship", "work"),
    },
}


CLASSICAL_ACTION_MECHANIC_TEXTS = {
    "gyeokguk_specific_adjustment": {
        "principle": "같은 십신이라도 월령과 격국 중심에 따라 역할이 달라진다.",
        "disease": "격국을 보지 않고 십신 이름만 읽으면 성격과 파격을 구분하지 못한다.",
        "medicine": "월령, 격국 중심, 위치, 투출과 통근을 함께 보아 실제 작용을 판정한다.",
    },
    "siksang_saengjae": {
        "principle": "식상이 만든 결과물이 재성으로 이어지는 작용이다.",
        "disease": "결과물은 있으나 가격, 소유권, 회수 기준이 약하면 재물로 굳지 못한다.",
        "medicine": "반복 가능한 기술, 상품, 서비스에 보상 기준을 붙이면 수입 구조가 생긴다.",
    },
    "jaesaenggwan": {
        "principle": "재성이 관성을 생하여 돈과 자원이 직책, 책임, 신용으로 올라가는 작용이다.",
        "disease": "일간이 약하거나 관살이 과하면 돈이 권한이 아니라 부담과 책임으로 바뀐다.",
        "medicine": "계약, 보상, 권한 범위가 함께 잡힐 때 재물이 사회적 자리로 이어진다.",
    },
    "gwanin_sangsaeng": {
        "principle": "관성이 인성을 생하여 직책과 책임이 문서, 자격, 보호 기반으로 안정되는 작용이다.",
        "disease": "직책은 있으나 문서와 보호 장치가 약하면 명분 없는 책임만 커진다.",
        "medicine": "자격, 문서, 제도적 근거가 책임을 받쳐 주면 평판과 신뢰가 안정된다.",
    },
    "salin_sangsaeng": {
        "principle": "편관의 압박을 인성이 받아 자격, 학습, 보호 장치로 흡수하는 작용이다.",
        "disease": "인성이 약하면 위험과 압박을 감당할 장치가 부족해 소모가 커진다.",
        "medicine": "공부, 자격, 문서, 절차가 강한 책임을 다룰 수 있는 방식으로 바꾼다.",
    },
    "siksin_jesal": {
        "principle": "식신이 편관을 제어하여 압박과 위험을 실무 능력으로 다스리는 작용이다.",
        "disease": "식신이 약하면 해야 할 일과 압박은 큰데 처리 방식이 몸에 잡히지 않는다.",
        "medicine": "반복된 기술, 현장 처리력, 구체적 결과물이 편관의 살기를 제어한다.",
    },
    "sanggwan_gyeongwan": {
        "principle": "상관이 정관을 건드려 제도, 직책, 공식 평가와 충돌하는 작용이다.",
        "disease": "표현과 개혁성이 과하면 직책, 평판, 조직 질서와 마찰이 커진다.",
        "medicine": "잘못된 질서를 바로잡는 명확한 결과와 기준이 있을 때 개혁성으로 쓰인다.",
    },
    "jaegeukin": {
        "principle": "재성이 인성을 극하여 문서, 보호, 학습, 명분을 현실 요구로 누르는 작용이다.",
        "disease": "인성이 필요한 격에서는 문서, 자격, 보호 기반이 손상될 수 있다.",
        "medicine": "인성이 과할 때는 현실 요구가 생각과 명분을 실행으로 끌어내는 약이 된다.",
    },
    "bigeop_jaengjae": {
        "principle": "비겁이 재성을 극하여 소유권, 지분, 몫을 두고 사람이 끼는 작용이다.",
        "disease": "재성의 소유 기준이 약하면 동업, 가족, 가까운 사람과 재물 분쟁이 생긴다.",
        "medicine": "계약, 역할, 지분, 정산 기준이 명확하면 사람의 힘도 재물 확장에 쓰인다.",
    },
    "inseong_dosik": {
        "principle": "인성이 식상을 극하여 준비, 문서, 생각이 결과물의 발현을 늦추는 작용이다.",
        "disease": "생각과 명분이 많아져 말, 기술, 상품, 발표가 밖으로 나오지 못한다.",
        "medicine": "정확한 자료와 방법론이 결과물의 품질을 높이는 방향이면 도움이 된다.",
    },
    "jaesaengsal": {
        "principle": "재성이 편관을 생하여 돈, 확장, 자원이 강한 책임과 위험을 키우는 작용이다.",
        "disease": "확장한 돈이 보증, 압박, 책임, 위험 부담으로 돌아올 수 있다.",
        "medicine": "인성과 절차가 받쳐 주면 큰 자원을 감당할 수 있는 책임 구조가 된다.",
    },
    "gwansal_honhap": {
        "principle": "정관과 편관이 섞여 공식 책임과 강한 압박이 함께 들어오는 작용이다.",
        "disease": "직책, 평가, 위험 책임이 뒤섞이면 역할 기준이 흐려지고 소모가 커진다.",
        "medicine": "정식 책임과 예외적 압박을 분리하면 조직 안의 권한과 부담이 정리된다.",
    },
    "inbi_overload": {
        "principle": "인성과 비겁이 두터워져 보호, 생각, 자기 기준이 실행보다 앞서는 작용이다.",
        "disease": "준비와 자기 논리가 많아져 실제 결과와 시장 반응이 늦어진다.",
        "medicine": "외부 과제, 마감, 책임 기준이 들어오면 준비가 행동으로 바뀐다.",
    },
    "siksang_overload": {
        "principle": "식상이 과해 말, 표현, 결과물, 시도가 기준 없이 늘어나는 작용이다.",
        "disease": "표현은 많으나 한 방향으로 정리되지 않으면 평판과 보상으로 남기 어렵다.",
        "medicine": "반복 가능한 결과물을 고르고 평가 기준과 보상 구조를 붙여야 한다.",
    },
    "jaeda_sinyak_risk": {
        "principle": "재성이 일간의 감당력보다 커져 돈, 계약, 자산이 부담으로 바뀌는 작용이다.",
        "disease": "돈의 규모는 보이지만 소유, 관리, 책임을 버티는 힘이 부족해진다.",
        "medicine": "권한, 문서, 지원 기반을 정해 감당 가능한 재물 규모를 먼저 잡아야 한다.",
    },
    "gwansal_overload": {
        "principle": "관살이 과해 책임, 평가, 압박이 일간의 감당력을 넘어서는 작용이다.",
        "disease": "직책과 압박은 커지는데 권한과 보호 장치가 부족하면 소모가 심해진다.",
        "medicine": "인성의 보호, 명확한 권한, 처리 절차가 관살의 압박을 흡수한다.",
    },
    "jaeseong_generates_gwanseong": {
        "principle": "재성이 관성을 생해 자원과 계약이 공식 역할과 책임으로 이어진다.",
        "disease": "자원은 투입됐지만 권한과 보상 기준이 약하면 책임만 커진다.",
        "medicine": "돈, 계약, 권한, 직책이 함께 잡힐 때 사회적 성취로 연결된다.",
    },
    "gwanseong_generates_inseong": {
        "principle": "관성이 인성을 생해 책임이 문서, 자격, 보호 장치로 안정된다.",
        "disease": "책임을 받칠 자격과 문서가 약하면 평가 부담만 남는다.",
        "medicine": "공식 역할에 자격과 문서 근거가 붙으면 신뢰와 평판이 안정된다.",
    },
    "siksang_controls_gwanseong": {
        "principle": "식상이 관성을 제어하여 결과물과 표현으로 권한 질서를 조정한다.",
        "disease": "표현이 과하면 직책과 평가 체계를 정면으로 흔든다.",
        "medicine": "실제 성과가 있을 때 기존 질서를 수정하는 힘으로 작용한다.",
    },
    "wealth_controls_resource": {
        "principle": "재성이 인성을 제어하여 문서와 보호 기반을 현실 요구로 시험한다.",
        "disease": "문서, 자격, 보호 장치가 약하면 돈과 계약 문제에 밀릴 수 있다.",
        "medicine": "인성이 과할 때 현실 기준이 붙으면 공부와 명분이 실행으로 내려온다.",
    },
    "bigeop_controls_wealth": {
        "principle": "비겁이 재성을 제어하여 사람, 지분, 소유권이 재물에 개입한다.",
        "disease": "가까운 사람과 돈의 경계가 흐려지면 몫과 손익 문제가 커진다.",
        "medicine": "소유권과 정산 기준을 명확히 하면 협업도 재물 확장에 쓸 수 있다.",
    },
    "inseong_controls_output": {
        "principle": "인성이 식상을 제어하여 준비와 문서가 결과물의 발현을 조절한다.",
        "disease": "검토와 명분이 길어지면 발표와 상품화가 늦어진다.",
        "medicine": "자료와 방법이 결과물의 완성도를 높이는 수준에서 작동해야 한다.",
    },
    "gwanseong_controls_bigeop": {
        "principle": "관성이 비겁을 제어하여 자기 주장과 주변 사람의 몫 문제를 정리한다.",
        "disease": "관성이 과하면 사람을 규칙으로 누르고 관계가 경직된다.",
        "medicine": "책임, 권한, 규칙이 분명하면 경쟁과 지분 문제가 정돈된다.",
    },
    "bigeop_generates_siksang": {
        "principle": "비겁이 식상을 생하여 자기 기반과 동료의 힘이 결과물로 나온다.",
        "disease": "사람의 힘이 흩어지면 결과물은 많아도 보상 기준이 흐려진다.",
        "medicine": "역할 분담과 반복 가능한 산출물을 만들면 협업이 성과로 바뀐다.",
    },
    "inseong_generates_bigeop": {
        "principle": "인성이 비겁을 생하여 문서, 학습, 보호가 자기 기반을 두텁게 한다.",
        "disease": "보호와 자기 논리가 커지면 실행보다 입장 고수가 앞설 수 있다.",
        "medicine": "배움과 문서를 자립 기반으로 쓰면 독립성과 판단력이 안정된다.",
    },
    "gwanseong_same_group": {
        "principle": "관성이 겹쳐 공식 책임, 직책, 평가가 두터워지는 작용이다.",
        "disease": "정관과 편관이 뒤섞이면 역할과 압박의 기준이 혼잡해진다.",
        "medicine": "공식 책임과 위험 압박을 분리하면 권한과 평가가 정리된다.",
    },
    "wealth_same_group": {
        "principle": "재성이 겹쳐 수입, 자산, 거래, 소유 문제가 강해지는 작용이다.",
        "disease": "재성이 과하면 돈의 규모가 커져도 관리와 책임이 함께 무거워진다.",
        "medicine": "현금 흐름, 소유권, 계약 기준을 분리해야 재물이 오래 남는다.",
    },
    "siksang_same_group": {
        "principle": "식상이 겹쳐 말, 기술, 표현, 결과물이 강하게 드러나는 작용이다.",
        "disease": "결과물이 많아도 기준과 시장 경로가 없으면 성과가 흩어진다.",
        "medicine": "산출물을 정리하고 보상 기준을 붙이면 재주가 성취로 굳어진다.",
    },
    "inseong_same_group": {
        "principle": "인성이 겹쳐 문서, 자격, 학습, 보호 기반이 두터워지는 작용이다.",
        "disease": "인성이 과하면 생각과 명분이 실행을 대신한다.",
        "medicine": "문서와 학습을 지연의 이유가 아니라 실행의 근거로 써야 한다.",
    },
    "bigeop_same_group": {
        "principle": "비겁이 겹쳐 자기 기준, 동료, 경쟁, 지분 문제가 강해지는 작용이다.",
        "disease": "비겁이 과하면 사람 사이의 주도권과 몫 문제가 커진다.",
        "medicine": "역할, 지분, 책임 기준을 정하면 사람의 힘을 추진력으로 쓸 수 있다.",
    },
}


def classical_action_mechanic_codes(tags: list[str], *, prefix: str) -> list[str]:
    codes: list[str] = []
    for tag in tags:
        mechanic = CLASSICAL_ACTION_MECHANICS.get(tag)
        if not mechanic:
            continue
        codes.extend(
            [
                f"{prefix}_mechanic:{tag}:flow:{mechanic['flow']}",
                f"{prefix}_mechanic:{tag}:disease:{mechanic['disease']}",
                f"{prefix}_mechanic:{tag}:medicine:{mechanic['medicine']}",
            ]
        )
        codes.extend(f"{prefix}_mechanic:{tag}:event:{event}" for event in mechanic["events"])
    return list(dict.fromkeys(codes))

TEN_GOD_EXACT_NUANCE = {
    "bi_gyeon": "동등한 주체, 자기 기준, 독립성과 경쟁심",
    "geob_jae": "강한 경쟁, 분점, 동업·지분·주도권 문제",
    "sik_sin": "안정된 생산물, 기술, 반복 가능한 결과",
    "sang_gwan": "표현력, 반발성, 개혁성, 규칙을 넘어서는 재주",
    "pyeon_jae": "유동 자금, 외부 기회, 거래, 확장성",
    "jeong_jae": "고정 수입, 소유권, 생활 재정, 축적성",
    "pyeon_gwan": "압박, 위험, 경쟁, 위기 대응, 강한 책임",
    "jeong_gwan": "공식 직책, 질서, 제도권 평가, 명예",
    "pyeon_in": "비정형 학습, 편중된 보호, 고립된 몰입",
    "jeong_in": "정식 문서, 자격, 보호 기반, 학업과 명분",
}

TEN_GOD_EXACT_ACTION_PROFILE = {
    "bi_gyeon": {
        "excess": "자기 기준이 강해져 협의, 분배, 양보가 늦어진다.",
        "deficiency": "자기 몫을 지키는 힘이 약해져 주변 조건에 끌려가기 쉽다.",
        "protruded": "자기 입장과 독립성이 밖으로 드러난다.",
        "hidden": "겉으로 강하게 주장하지 않아도 내부 기준이 쉽게 꺾이지 않는다.",
        "rooted": "자기 기반이 오래 유지되어 흔들려도 다시 버틴다.",
        "unrooted": "겉으로는 강해 보여도 장기 지속력은 약해질 수 있다.",
        "domains": ["personality", "career", "relationship"],
    },
    "geob_jae": {
        "excess": "경쟁, 지분, 몫 문제가 커져 재물과 관계를 동시에 흔든다.",
        "deficiency": "강하게 치고 나가야 할 때 주도권을 놓치기 쉽다.",
        "protruded": "경쟁자, 동업자, 주변 사람과의 몫 문제가 밖으로 드러난다.",
        "hidden": "겉으로는 평온해도 실제 몫과 주도권 문제는 안쪽에 남는다.",
        "rooted": "경쟁 구도가 오래 이어지고 사람 문제가 쉽게 사라지지 않는다.",
        "unrooted": "순간적인 경쟁은 생기나 오래 지속되는 힘은 약하다.",
        "domains": ["money", "relationship", "career"],
    },
    "sik_sin": {
        "excess": "편안함과 반복성에 머물러 긴장감 있는 책임을 피할 수 있다.",
        "deficiency": "만든 결과물이 약해 재주가 돈과 평가로 이어지는 속도가 늦다.",
        "protruded": "기술, 결과물, 말, 서비스가 밖으로 드러난다.",
        "hidden": "실력은 안에 있으나 공개되거나 상품화되려면 자극이 필요하다.",
        "rooted": "반복 가능한 기술과 생산력이 안정적으로 유지된다.",
        "unrooted": "아이디어는 있어도 꾸준히 내놓는 힘이 약해질 수 있다.",
        "domains": ["career", "money", "personality"],
    },
    "sang_gwan": {
        "excess": "표현과 반발이 강해져 제도, 직책, 평가를 건드린다.",
        "deficiency": "자기 재주를 드러내는 힘이 약해 평가 기회를 놓치기 쉽다.",
        "protruded": "말, 기획, 개혁성, 반발성이 밖으로 뚜렷하게 나온다.",
        "hidden": "겉으로는 순해 보여도 기존 방식에 대한 불만과 개성이 남아 있다.",
        "rooted": "표현력과 돌파력이 지속되어 한 분야의 색깔이 된다.",
        "unrooted": "순간적인 표현은 강하지만 일관된 성과로 굳히기 어렵다.",
        "domains": ["career", "personality", "relationship"],
    },
    "pyeon_jae": {
        "excess": "확장 욕구가 커져 거래, 투자, 사람을 넓히는 과정에서 손실이 생긴다.",
        "deficiency": "외부 기회와 유동 자금을 잡는 감각이 약해진다.",
        "protruded": "거래, 외부 기회, 활동 자금이 밖으로 드러난다.",
        "hidden": "돈의 기회가 숨어 있어 운이나 사람을 만나야 현실화된다.",
        "rooted": "외부 재물과 거래 기반이 오래 유지된다.",
        "unrooted": "돈의 움직임은 생겨도 소유로 굳히는 힘은 약하다.",
        "domains": ["money", "career", "relationship"],
    },
    "jeong_jae": {
        "excess": "소유와 안정 기준이 강해져 변화 대응이 늦어진다.",
        "deficiency": "수입이 생겨도 소유권과 축적 구조가 약해진다.",
        "protruded": "고정 수입, 소유권, 생활 재정 문제가 밖으로 드러난다.",
        "hidden": "재물의 씨앗은 있으나 실제 소유로 굳히려면 절차가 필요하다.",
        "rooted": "생활 기반과 축적성이 안정적으로 유지된다.",
        "unrooted": "수입은 보여도 오래 남기는 기반은 약할 수 있다.",
        "domains": ["money", "marriage", "career"],
    },
    "pyeon_gwan": {
        "excess": "압박, 경쟁, 위험 부담이 커져 몸과 일의 긴장이 높아진다.",
        "deficiency": "강한 책임과 위기 상황을 돌파하는 힘이 약해진다.",
        "protruded": "압박, 경쟁, 책임, 위험 대응이 밖으로 드러난다.",
        "hidden": "겉으로는 안정되어 보여도 안쪽에는 긴장과 압박이 숨어 있다.",
        "rooted": "강한 책임과 경쟁 환경이 오래 지속된다.",
        "unrooted": "압박은 생기지만 실질 권한이나 지속성은 약할 수 있다.",
        "domains": ["career", "reputation", "personality"],
    },
    "jeong_gwan": {
        "excess": "규칙과 평판 부담이 커져 자유로운 선택이 어려워진다.",
        "deficiency": "공식 평가, 직책, 책임 기준이 약해져 사회적 자리 잡기가 늦다.",
        "protruded": "직책, 제도권 평가, 책임, 명예가 밖으로 드러난다.",
        "hidden": "공식 역할은 숨어 있어도 책임감과 평판 의식은 내부에 작용한다.",
        "rooted": "사회적 신뢰와 책임 구조가 오래 유지된다.",
        "unrooted": "직책은 보여도 실제 권한과 지속성이 약할 수 있다.",
        "domains": ["career", "reputation", "marriage"],
    },
    "pyeon_in": {
        "excess": "생각이 편중되고 몰입이 깊어져 현실 실행이 늦어진다.",
        "deficiency": "특수한 이해력과 비정형 문제를 붙드는 힘이 약해진다.",
        "protruded": "독특한 공부, 감각, 보호성, 편중된 관심이 밖으로 드러난다.",
        "hidden": "겉으로는 평범해 보여도 안쪽의 관심과 판단 방식은 독자적이다.",
        "rooted": "특수 지식과 몰입 성향이 오래 유지된다.",
        "unrooted": "관심은 생기지만 학습과 자격으로 굳히기 어렵다.",
        "domains": ["personality", "career", "relationship"],
    },
    "jeong_in": {
        "excess": "보호, 명분, 문서, 생각이 많아져 실행이 늦어진다.",
        "deficiency": "자격, 문서, 보호 기반이 약해 안정감과 명분이 부족해진다.",
        "protruded": "자격, 문서, 학습, 보호 기반이 밖으로 드러난다.",
        "hidden": "겉으로 드러나지 않아도 명분과 보호 욕구가 판단을 받친다.",
        "rooted": "문서, 자격, 학습 기반이 오래 유지된다.",
        "unrooted": "명분은 있어도 실제 보호력과 지속성은 약할 수 있다.",
        "domains": ["career", "personality", "marriage"],
    },
}

PATTERN_ACTION_CONTEXT = {
    "jianlu_peer_pattern": {
        "success": "강한 자기 기반을 성과와 질서로 빼낼 때 격이 선다.",
        "disease": "자기 기운이 과하면 경쟁, 고집, 분배 문제가 병이 된다.",
        "timing": "운에서 식상이나 관성이 들어오면 강한 기운이 성과와 책임으로 정리된다.",
    },
    "yangren_peer_pattern": {
        "success": "거친 주도권을 권한, 책임, 결과물로 묶을 때 격이 선다.",
        "disease": "양인의 기세가 제어되지 않으면 충돌과 쟁재가 병이 된다.",
        "timing": "운에서 관살이나 식상이 들어오면 기세가 제도나 성과로 발동된다.",
    },
    "eating_god_pattern": {
        "success": "생산물과 기술이 끊기지 않고 재물과 평가로 이어질 때 격이 선다.",
        "disease": "인성이 식신을 막거나 결과물이 약하면 생산이 병목이 된다.",
        "timing": "운에서 재성이나 관성이 들어오면 만든 것이 돈과 책임으로 넘어간다.",
    },
    "hurting_officer_pattern": {
        "success": "표현과 돌파력이 재물, 기획, 문서성으로 정제될 때 격이 선다.",
        "disease": "상관이 관을 직접 치면 평판, 직책, 제도와 충돌한다.",
        "timing": "운에서 재성이나 인성이 들어오면 표현이 시장성 또는 품격으로 정리된다.",
    },
    "indirect_wealth_pattern": {
        "success": "외부 자원과 거래 기회를 제도, 신용, 실행력으로 묶을 때 격이 선다.",
        "disease": "비겁이 끼거나 재성이 과하면 지분, 손실, 과확장이 병이 된다.",
        "timing": "운에서 식상이나 관성이 들어오면 거래가 수입과 책임으로 확장된다.",
    },
    "direct_wealth_pattern": {
        "success": "소유, 정산, 생활 재정을 안정된 기준과 책임으로 굳힐 때 격이 선다.",
        "disease": "비겁이 재성을 나누거나 인성이 실행을 늦추면 재물의 병이 생긴다.",
        "timing": "운에서 식상·관성이 들어오면 수입이 소유와 직책으로 연결된다.",
    },
    "seven_killings_pattern": {
        "success": "압박과 위험을 식신이나 인성으로 제어해 권한과 전문성으로 바꿀 때 격이 선다.",
        "disease": "재성이 살을 생하거나 관살이 혼잡하면 압박과 손실이 병이 된다.",
        "timing": "운에서 식신이나 인성이 들어오면 압박이 실무력과 자격으로 전환된다.",
    },
    "direct_officer_pattern": {
        "success": "직책과 질서가 재성의 현실 기반과 인성의 명분을 얻을 때 격이 선다.",
        "disease": "상관이 관을 치거나 비겁이 질서를 흔들면 평판의 병이 생긴다.",
        "timing": "운에서 재성이나 인성이 들어오면 직책과 평판이 안정된다.",
    },
    "indirect_resource_pattern": {
        "success": "특수한 이해력과 보호성이 결과물이나 현실성으로 연결될 때 격이 선다.",
        "disease": "편인이 과하면 고립, 지연, 도식이 병이 된다.",
        "timing": "운에서 재성이나 식상이 들어오면 생각이 현실 요구와 결과물로 움직인다.",
    },
    "direct_resource_pattern": {
        "success": "자격, 문서, 보호 기반이 직책과 실행으로 이어질 때 격이 선다.",
        "disease": "정인이 과하면 보류, 의존, 실행 지연이 병이 된다.",
        "timing": "운에서 관성이나 재성이 들어오면 명분이 직책 또는 현실 판단으로 움직인다.",
    },
}

ROLE_GRADE_EFFECT_STATE = {
    "core": "격국 중심",
    "core_overload": "중심 과다",
    "support": "성격 보조",
    "strong_regulator": "강한 조절",
    "regulator": "병약 조절",
    "regulator_or_breaker": "조절·파격 경계",
    "breaker_or_medicine": "파격·약성 경계",
    "conditioned_support": "조건부 성격",
    "source": "근원 보조",
    "mixed": "혼합 작용",
    "burden": "부담 작용",
    "breaker": "파격 위험",
    "danger": "강한 파격 위험",
}

ROLE_GRADE_RESOLUTION_STATE = {
    "core": "seonggyeok_center",
    "core_overload": "disease_overload",
    "support": "seonggyeok_support",
    "strong_regulator": "byeongyak_medicine",
    "regulator": "byeongyak_medicine",
    "regulator_or_breaker": "medicine_or_pagyeok",
    "breaker_or_medicine": "pagyeok_or_medicine",
    "conditioned_support": "conditional_seonggyeok",
    "source": "seonggyeok_source",
    "mixed": "conditional_mixed",
    "burden": "disease_burden",
    "breaker": "pagyeok_risk",
    "danger": "strong_pagyeok_risk",
}

RESOLUTION_STATE_LABELS = {
    "seonggyeok_center": "성격 중심",
    "seonggyeok_support": "성격 보조",
    "seonggyeok_source": "성격 근원",
    "conditional_seonggyeok": "조건부 성격",
    "byeongyak_medicine": "병약 조절",
    "medicine_or_pagyeok": "약성·파격 경계",
    "pagyeok_or_medicine": "파격·약성 경계",
    "conditional_mixed": "혼합 조건",
    "disease_overload": "과중 병",
    "disease_burden": "부담 병",
    "pagyeok_risk": "파격 위험",
    "strong_pagyeok_risk": "강한 파격 위험",
}


def _single_resolution_state(role_grade: str) -> str:
    return ROLE_GRADE_RESOLUTION_STATE.get(role_grade, "conditional_mixed")


def _single_resolution_logic(
    *,
    pattern: str,
    acting_ten_god: str,
    role_grade: str,
    relation: str,
    center_effect: str,
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    state = _single_resolution_state(role_grade)
    state_label = RESOLUTION_STATE_LABELS[state]
    relation_text = RELATION_EXPERT_TEXT.get(relation, "격국 중심과 간접적으로 얽힌다.")
    if state in {"seonggyeok_center", "seonggyeok_support", "seonggyeok_source", "conditional_seonggyeok"}:
        return (
            f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
            f"{center_effect} 월령에서 필요한 작용이면 {_object_form(pattern_center)} 실제로 세우고, "
            f"약하거나 숨어 있으면 대운·세운에서 자극될 때 성격 조건으로 올라온다. {relation_text}"
        )
    if state == "byeongyak_medicine":
        return (
            f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
            f"격국의 병을 그대로 키우는 것이 아니라 {_object_form(pattern_center)} 조절하는 약성으로 쓴다. "
            f"투출과 통근이 맞으면 약으로 쓰이고, 약하면 조절력이 약해진다. {relation_text}"
        )
    if state in {"medicine_or_pagyeok", "pagyeok_or_medicine"}:
        return (
            f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
            f"월령과 강약이 맞으면 병을 제어하지만, 과하거나 위치가 나쁘면 파격으로 바뀐다. "
            f"같은 십신이라도 투출, 통근, 합충형파해에 따라 결론이 갈린다. {relation_text}"
        )
    if state in {"disease_overload", "disease_burden"}:
        return (
            f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
            f"필요한 힘이라도 과하면 {_object_form(pattern_center)} 두텁게 하기보다 한쪽으로 몰아 병을 만든다. "
            f"대운·세운에서 반복되면 부담이 사건으로 드러난다. {relation_text}"
        )
    if state in {"pagyeok_risk", "strong_pagyeok_risk"}:
        return (
            f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
            f"격국 중심과 충돌하면 {_object_form(pattern_center)} 흔들고, 월령에서 불필요하면 파격 판단을 우선한다. "
            f"다만 강약과 위치가 조절되면 일부는 현실 대응력으로 전환될 수 있다. {relation_text}"
        )
    return (
        f"{pattern_label}에서 {_topic_form(ten_god_label)} {state_label}에 해당한다. "
        f"월령, 강약, 조후, 위치를 모두 보아 성격인지 병인지 다시 가른다. {relation_text}"
    )


def _single_role_in_pattern_logic(
    *,
    pattern: str,
    acting_ten_god: str,
    role_grade: str,
    relation: str,
    action_nature: str,
    center_effect: str,
) -> str:
    specialized = _single_specialized_role_in_pattern_logic(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        role_grade=role_grade,
        relation=relation,
        action_nature=action_nature,
        center_effect=center_effect,
    )
    if specialized:
        return specialized

    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    relation_text = RELATION_EXPERT_TEXT.get(relation, "격국 중심과 간접적으로 얽힌다.")
    state = _single_resolution_state(role_grade)
    state_label = RESOLUTION_STATE_LABELS[state]
    state_phrase = _euro_form(state_label)

    if state in {"seonggyeok_center", "seonggyeok_support", "seonggyeok_source", "conditional_seonggyeok"}:
        return (
            f"{pattern_label}에서 {ten_god_label}의 역할은 {_object_form(pattern_center)} 실제로 세우거나 보강하는 것이다. "
            f"이 십신은 {exact}의 성격으로 작동하고, {action_nature}의 방식으로 격국에 참여한다. "
            f"월령에서 필요하고 투출·통근이 받치면 {state_phrase} 쓰인다. {relation_text} {center_effect}"
        )
    if state == "byeongyak_medicine":
        return (
            f"{pattern_label}에서 {ten_god_label}의 역할은 격국의 병을 제어하는 것이다. "
            f"이 십신은 {exact}의 성격으로 작동하고, {action_nature}의 방식으로 부담을 약으로 돌린다. "
            f"월령에서 필요하고 실제 힘이 있으면 조절력이 생기지만, 약하면 병을 다스리지 못한다. {relation_text} {center_effect}"
        )
    if state in {"medicine_or_pagyeok", "pagyeok_or_medicine", "conditional_mixed"}:
        return (
            f"{pattern_label}에서 {ten_god_label}의 역할은 조건부 작용이다. "
            f"이 십신은 {exact}의 성격으로 작동하므로, 강약과 위치가 맞으면 {state_phrase} 쓰이고 맞지 않으면 반대 작용으로 기운다. "
            f"투출하면 밖으로 드러나고, 지장간에 있으면 운에서 자극될 때 현실 사건으로 올라온다. {relation_text} {center_effect}"
        )
    if state in {"disease_overload", "disease_burden"}:
        return (
            f"{pattern_label}에서 {ten_god_label}의 역할은 필요한 힘을 과하게 몰아 병으로 만드는 쪽에 가깝다. "
            f"이 십신은 {exact}의 성격으로 드러나며, {action_nature}이 과하면 {_object_form(pattern_center)} 두텁게 하기보다 한쪽으로 치우치게 한다. "
            f"통근하면 오래 지속되고, 대운·세운에서 반복되면 부담이 사건으로 커진다. {relation_text}"
        )
    return (
        f"{pattern_label}에서 {ten_god_label}의 역할은 격국 중심을 흔들 수 있는 작용이다. "
        f"이 십신은 {exact}의 성격으로 작동하고, {action_nature}의 방식으로 {_object_form(pattern_center)} 건드린다. "
        f"월령에서 불필요하거나 과하면 파격 판단을 우선하고, 위치와 강약이 조절되면 일부는 현실 대응력으로 전환된다. {relation_text}"
    )


def _single_specialized_role_in_pattern_logic(
    *,
    pattern: str,
    acting_ten_god: str,
    role_grade: str,
    relation: str,
    action_nature: str,
    center_effect: str,
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    pattern_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_group = TEN_GOD_GROUPS[pattern_ten_god]
    acting_group = TEN_GOD_GROUPS[acting_ten_god]
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    relation_text = RELATION_EXPERT_TEXT.get(relation, "격국 중심과 간접적으로 얽힌다.")
    state = _single_resolution_state(role_grade)
    state_label = RESOLUTION_STATE_LABELS[state]
    state_phrase = _euro_form(state_label)
    actor_subject = _subject_particle(ten_god_label)
    center_sentence = _sentence(center_effect)

    def finish(main: str, effect: str) -> str:
        return (
            f"{main} "
            f"{effect} "
            f"월령에서 필요한 힘인지, 투출·통근으로 실제 힘을 얻었는지에 따라 {state_phrase} 판정한다. "
            f"{relation_text} {center_sentence}"
        )

    if action_nature in {"재극정인", "재극편인"} and pattern_group == "wealth" and acting_group == "resource":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 재물의 문서 근거, 자격, 보호 장치를 재성의 질서 안에 묶는 것이다.",
            f"이때 재극인은 공부와 명분을 없애는 작용이 아니라, 돈과 소유가 실제로 성립하도록 근거를 정리하는 작용이다. {actor_subject} {exact}의 방식으로 재물의 안전장치를 만든다.",
        )

    if action_nature in {"정재극인", "편재극인"} and pattern_group == "resource" and acting_group == "wealth":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 격의 중심인 {pattern_center}을 현실의 돈, 계약, 생활 요구로 압박하는 것이다.",
            f"이 재극인은 인성을 깨뜨리기만 하는 작용이 아니다. 인성이 과하면 현실 감각을 세우는 약이 되고, 인성이 약하면 문서, 학업, 보호 기반을 손상시키는 병이 된다. {actor_subject} {exact}의 방식으로 작동한다.",
        )

    if action_nature in {"식신생재", "상관생재"} and pattern_group == "wealth" and acting_group == "output":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 재물이 생길 수 있는 결과물과 시장 입구를 만드는 것이다.",
            f"{action_nature}는 돈을 직접 늘리는 말이 아니라, 기술, 상품, 말, 기획, 서비스가 재물의 근거로 바뀌는 작용이다. {actor_subject} {exact}의 방식으로 재성을 생한다.",
        )

    if action_nature in {"식신생재", "상관생재"} and pattern_group == "output" and acting_group == "wealth":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 격의 중심인 생산과 표현을 돈, 거래, 보상으로 받아 주는 것이다.",
            f"이때 재성은 욕심의 문제가 아니라 결과물이 실제 수입으로 확정되는 통로다. {actor_subject} {exact}의 방식으로 결과물의 값을 정한다.",
        )

    if action_nature in {"재생관", "재생살"} and pattern_group == "wealth" and acting_group == "officer":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 재물이 직책, 책임, 법적 부담으로 넘어가는 지점을 만드는 것이다.",
            f"{action_nature}은 돈이 권한을 얻는 길이기도 하지만, 일간이 약하거나 관살이 과하면 재물이 책임과 압박으로 묶이는 작용이다. {actor_subject} {exact}의 방식으로 재성의 결과를 공적 책임으로 바꾼다.",
        )

    if action_nature in {"정재생관", "편재생관"} and pattern_group == "officer" and acting_group == "wealth":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 공식 직책과 사회적 신뢰를 현실 기반으로 받치는 것이다.",
            f"재성은 관성을 생하지만, 격국상 필요한 재성일 때는 보수, 계약, 자원, 생활 기반이 직책을 안정시킨다. 과하면 책임을 돈으로 떠안는 문제가 된다. {actor_subject} {exact}의 방식으로 작동한다.",
        )

    if action_nature == "관인상생" and pattern_group == "officer" and acting_group == "resource":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 직책과 평가를 문서, 자격, 명분으로 안정시키는 것이다.",
            f"관인상생은 관성이 강해지는 말이 아니라, 공식 책임이 보호 장치와 신뢰의 근거를 얻는 작용이다. {actor_subject} {exact}의 방식으로 관성의 지속성을 만든다.",
        )

    if action_nature == "살인상생" and pattern_group == "officer" and acting_group == "resource":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 강한 압박과 위험을 배움, 문서, 보호 기반으로 흡수하는 것이다.",
            f"살인상생은 편관의 날카로움을 없애는 것이 아니라, 그 압박을 감당할 방법과 자격으로 바꾸는 작용이다. {actor_subject} {exact}의 방식으로 살의 부담을 받아낸다.",
        )

    if action_nature in {"관인상생", "살인상생"} and pattern_group == "resource" and acting_group == "officer":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 인성의 문서와 자격이 실제 직책, 평가, 책임으로 이어지는 길을 여는 것이다.",
            f"이 작용은 배움이 명분으로만 머무르지 않고 제도권의 역할을 얻는 과정이다. {actor_subject} {exact}의 방식으로 인성의 사회적 쓰임을 만든다.",
        )

    if action_nature == "식신제살" and pattern_group == "officer" and acting_group == "output":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 편관의 압박을 실무, 기술, 결과물로 낮추는 것이다.",
            f"식신제살은 강한 책임을 피하는 작용이 아니다. 손에 익은 처리력과 반복 가능한 결과물로 위험을 다루는 작용이다. {actor_subject} {exact}의 방식으로 살을 제어한다.",
        )

    if (
        (action_nature == "식신제살" and pattern_group == "output" and acting_group == "officer")
        or (pattern == "eating_god_pattern" and acting_ten_god == "pyeon_gwan")
    ):
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 식신의 생산성을 시험하는 압박과 책임을 제공하는 것이다.",
            f"편관이 적당하면 결과물에 긴장감과 사회적 쓰임이 붙지만, 과하면 생산보다 부담이 먼저 커진다. {actor_subject} {exact}의 방식으로 식신의 현실 강도를 시험한다.",
        )

    if action_nature == "상관견관" and pattern_group == "officer" and acting_group == "output":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 직책과 공식 신뢰를 직접 건드리는 것이다.",
            f"상관견관은 단순한 말실수가 아니라, 표현, 개혁성, 불복성이 관성의 질서와 충돌하는 작용이다. {actor_subject} {exact}의 방식으로 평판과 조직 질서를 흔든다.",
        )

    if action_nature == "상관견관" and pattern_group == "output" and acting_group == "officer":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 상관의 표현력에 공식 질서와 평가 기준을 붙이는 것이다.",
            f"정관이 적당하면 재주가 제도권의 신뢰를 얻지만, 정관이 과하거나 상관이 거칠면 표현과 규칙이 정면으로 충돌한다. {actor_subject} {exact}의 방식으로 상관의 사회적 한계를 정한다.",
        )

    if action_nature in {"편인도식", "정인제식"} and pattern_group == "output" and acting_group == "resource":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 생산과 표현을 문서, 생각, 자격의 힘으로 제어하는 것이다.",
            f"{action_nature}은 결과물을 망치는 말로만 읽으면 부족하다. 필요한 인성은 결과물의 품질을 높이지만, 과하면 내놓아야 할 것을 계속 늦춘다. {actor_subject} {exact}의 방식으로 식상을 누른다.",
        )

    if action_nature in {"쟁재", "재물 장악"} and pattern_group == "wealth" and acting_group == "peer":
        return finish(
            f"{pattern_label}에서 {ten_god_label}의 역할은 재물의 소유권과 몫에 사람의 힘을 끌어들이는 것이다.",
            f"비겁쟁재는 사람을 만나는 문제만이 아니다. 돈이 보이는 순간 지분, 공동 비용, 가족 재정, 동업 손익에서 누가 가져갈지가 예민해지는 작용이다. {actor_subject} {exact}의 방식으로 재성을 건드린다.",
        )

    return ""

PATTERN_LENS = {
    "jianlu_peer_pattern": {
        "label": "건록격",
        "center": "자기 기반과 독립성",
        "peer": ("core_overload", "중심 강화", "자기 기반이 강해지나 경쟁과 고집도 함께 커진다."),
        "output": ("support", "설기성 성과", "강한 자기 기운을 결과물과 표현으로 풀어낸다."),
        "wealth": ("mixed", "재물 장악", "돈과 소유를 직접 잡으려 하나 경쟁이 개입되기 쉽다."),
        "officer": ("regulator", "관성 제어", "강한 자기 주장을 직책과 규칙으로 정리한다."),
        "resource": ("burden", "인성 과다", "보호와 명분이 자기 기운을 더 키워 고집이 두꺼워진다."),
    },
    "yangren_peer_pattern": {
        "label": "양인격",
        "center": "강한 주도권과 경쟁성",
        "peer": ("breaker", "겁재 과중", "주도권이 지나쳐 충돌과 분점 문제가 커진다."),
        "output": ("support", "기세 배출", "강한 기운을 실무와 성과로 빼내야 살아난다."),
        "wealth": ("danger", "쟁재", "돈이 보이면 사람과 지분 문제가 날카로워진다."),
        "officer": ("strong_regulator", "살관 제어", "강한 기운을 권한과 책임으로 묶을 때 격이 선다."),
        "resource": ("burden", "인성 조장", "보호와 명분이 강한 기운을 더 부추길 수 있다."),
    },
    "eating_god_pattern": {
        "label": "식신격",
        "center": "안정된 생산과 결과물",
        "peer": ("source", "생산 기반", "자기 기반이 식신을 받쳐 기술과 결과가 꾸준해진다."),
        "output": ("core", "중심 강화", "생산과 재주가 중심으로 드러난다."),
        "wealth": ("support", "식신생재", "만든 결과가 재물과 거래로 이어진다."),
        "officer": ("conditioned_support", "성과의 책임화", "결과물이 직책과 책임으로 넘어가면 사회적 평가가 생긴다."),
        "resource": ("breaker", "도식", "인성이 식신을 누르면 결과물이 늦고 생각이 생산을 막는다."),
    },
    "hurting_officer_pattern": {
        "label": "상관격",
        "center": "표현과 돌파력",
        "peer": ("source", "표현 기반", "자기 기반이 표현력을 키우지만 과하면 말과 행동이 거칠어진다."),
        "output": ("core_overload", "중심 강화", "재주와 표현이 강해져 성과도 크고 반발도 커진다."),
        "wealth": ("support", "상관생재", "표현과 기획이 돈과 시장성으로 연결된다."),
        "officer": ("breaker", "상관견관", "규칙과 직책을 건드려 평가·조직 문제를 만들 수 있다."),
        "resource": ("regulator", "상관패인", "인성이 표현을 정제하면 재주가 품격과 문서성을 얻는다."),
    },
    "indirect_wealth_pattern": {
        "label": "편재격",
        "center": "외부 자원과 거래 확장",
        "peer": ("breaker", "쟁재", "사람과 지분이 끼어 외부 재물이 흩어질 수 있다."),
        "output": ("support", "식상생재", "활동력과 결과물이 거래 기회를 키운다."),
        "wealth": ("core", "중심 강화", "움직이는 돈과 외부 기회가 강해진다."),
        "officer": ("support", "재생관", "돈과 자원이 직책, 신용, 공식 책임으로 이어진다."),
        "resource": ("regulator", "재극인", "명분과 보호성을 현실 이익으로 제어한다."),
    },
    "direct_wealth_pattern": {
        "label": "정재격",
        "center": "고정 재물과 소유 질서",
        "peer": ("breaker", "쟁재", "가까운 사람과 몫·소유권 문제가 생기기 쉽다."),
        "output": ("support", "식상생재", "기술과 결과물이 안정 수입으로 바뀐다."),
        "wealth": ("core", "중심 강화", "소유, 정산, 생활 재정의 중심이 강해진다."),
        "officer": ("support", "재생관", "재물이 직책과 공적 신뢰로 이어진다."),
        "resource": ("regulator", "재극인", "생각과 명분을 누르고 현실적 소유를 확정한다."),
    },
    "seven_killings_pattern": {
        "label": "편관격",
        "center": "압박과 위기 대응",
        "peer": ("burden", "겁살 충돌", "자기 주장과 압박이 맞붙어 충돌성이 커진다."),
        "output": ("regulator", "식신제살", "실무와 기술로 강한 압박을 제어한다."),
        "wealth": ("danger", "재생살", "돈과 욕심이 압박과 위험을 키울 수 있다."),
        "officer": ("core_overload", "관살 중첩", "책임과 압박이 겹쳐 강한 자리와 소모가 함께 온다."),
        "resource": ("support", "살인상생", "압박이 자격, 문서, 학습, 보호 기반으로 전환된다."),
    },
    "direct_officer_pattern": {
        "label": "정관격",
        "center": "질서와 공식 평가",
        "peer": ("burden", "관성 흔들림", "자기 주장이나 주변 경쟁이 질서를 흐릴 수 있다."),
        "output": ("breaker", "상관견관", "표현과 반발이 직책과 평판을 건드린다."),
        "wealth": ("support", "재생관", "현실 기반과 재물이 직책과 신용을 받친다."),
        "officer": ("core", "중심 강화", "직책, 명예, 제도권 평가가 선명해진다."),
        "resource": ("support", "관인상생", "직책이 문서, 자격, 명분과 연결되어 안정된다."),
    },
    "indirect_resource_pattern": {
        "label": "편인격",
        "center": "비정형 지식과 특수한 보호성",
        "peer": ("burden", "인비 과중", "생각과 자기 기준이 강해져 현실 접점이 좁아질 수 있다."),
        "output": ("mixed", "편인과 식상", "아이디어가 결과로 나오면 강점이 되나 도식이면 결과가 늦다."),
        "wealth": ("regulator_or_breaker", "재극인", "현실 요구가 편중된 생각을 깨우지만 격의 중심도 흔든다."),
        "officer": ("source", "살인상생", "압박과 책임이 공부와 자격의 이유가 된다."),
        "resource": ("core_overload", "중심 강화", "지식과 보호성이 깊어지나 과하면 고립된다."),
    },
    "direct_resource_pattern": {
        "label": "정인격",
        "center": "정식 자격과 보호 기반",
        "peer": ("burden", "인비 과중", "보호와 자기 기준이 강해져 현실 대응이 늦어진다."),
        "output": ("mixed", "인성의 결과화", "배운 것이 결과물로 나오면 좋으나 인성이 과하면 생산이 막힌다."),
        "wealth": ("breaker_or_medicine", "재극인", "재물이 문서·보호 기반을 흔들며, 인성 과다에는 약이 된다."),
        "officer": ("support", "관인상생", "직책과 제도가 자격과 명분을 살린다."),
        "resource": ("core_overload", "중심 강화", "문서, 학업, 보호 기반이 강해지나 과하면 의존이 된다."),
    },
}

RELATION_EXPERT_TEXT = {
    "same_group": "같은 계열이 겹친 작용이다. 중심이 선명해지지만 과하면 편중된다.",
    "actor_generates_pattern": "작용 십신이 격국의 중심을 생한다. 중심을 살리는 보조 조건으로 본다.",
    "pattern_generates_actor": "격국의 중심이 작용 십신으로 힘을 넘긴다. 중심의 결과가 다음 역할로 이어진다.",
    "actor_controls_pattern": "작용 십신이 격국의 중심을 극한다. 격의 중심을 다듬는 약이 되거나 깨뜨리는 압박이 된다.",
    "pattern_controls_actor": "격국의 중심이 작용 십신을 극한다. 중심이 주변 역할을 제어하여 현실성을 확보한다.",
}

ROLE_GRADE_VERDICT = {
    "core": "center_reinforced",
    "core_overload": "center_reinforced_with_excess",
    "support": "supports_pattern_success",
    "strong_regulator": "strongly_regulates_pattern",
    "regulator": "regulates_pattern",
    "regulator_or_breaker": "regulates_or_breaks_by_balance",
    "breaker_or_medicine": "breaks_center_or_treats_excess",
    "conditioned_support": "supports_when_ordered",
    "source": "feeds_pattern_source",
    "mixed": "mixed_by_strength_and_position",
    "burden": "burdens_pattern",
    "breaker": "breaks_pattern_order",
    "danger": "amplifies_pattern_risk",
}


def _relation_to_pattern(pattern_group: str, acting_group: str) -> str:
    if pattern_group == acting_group:
        return "same_group"
    if GROUP_GENERATES.get(acting_group) == pattern_group:
        return "actor_generates_pattern"
    if GROUP_GENERATES.get(pattern_group) == acting_group:
        return "pattern_generates_actor"
    if GROUP_CONTROLS.get(acting_group) == pattern_group:
        return "actor_controls_pattern"
    if GROUP_CONTROLS.get(pattern_group) == acting_group:
        return "pattern_controls_actor"
    return "indirect_relation"


def _conditions(pattern: str, acting_group: str, relation: str, role_grade: str) -> tuple[list[str], list[str]]:
    rules = REGULAR_PATTERN_NEED_RULES.get(PATTERN_CENTER_BY_PATTERN[pattern], {})
    support_groups = {str(item[0]) for item in rules.get("support", ())}
    caution_groups = {str(item[0]) for item in rules.get("caution", ())}
    favorable = [
        "acting_ten_god_protruded",
        "acting_ten_god_rooted",
        "month_command_not_damaged",
    ]
    unfavorable = [
        "acting_ten_god_unrooted",
        "month_command_mixed_or_damaged",
    ]
    if acting_group in support_groups:
        favorable.append(f"pattern_support_group:{acting_group}")
    if acting_group in caution_groups:
        unfavorable.append(f"pattern_caution_group:{acting_group}")
    if relation == "actor_controls_pattern":
        unfavorable.append("actor_controls_pattern_center")
        if role_grade in {"regulator_or_breaker", "breaker_or_medicine"}:
            favorable.append("center_excess_needs_control")
    if relation == "pattern_controls_actor":
        favorable.append("pattern_center_can_regulate_actor")
        unfavorable.append("control_too_strong_can_damage_actor_domain")
    return list(dict.fromkeys(favorable)), list(dict.fromkeys(unfavorable))


def _has_final_consonant(text: str) -> bool:
    if not text:
        return False
    code = ord(text[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _final_consonant_index(text: str) -> int:
    if not text:
        return 0
    code = ord(text[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28
    return 0


def _subject_form(text: str) -> str:
    return f"{text}{'은' if _has_final_consonant(text) else '는'}"


def _topic_form(text: str) -> str:
    return f"{text}{'은' if _has_final_consonant(text) else '는'}"


def _subject_particle(text: str) -> str:
    return f"{text}{'이' if _has_final_consonant(text) else '가'}"


def _object_form(text: str) -> str:
    return f"{text}{'을' if _has_final_consonant(text) else '를'}"


def _euro_form(text: str) -> str:
    final = _final_consonant_index(text)
    particle = "으로" if final and final != 8 else "로"
    return f"{text}{particle}"


PATTERN_PERSONALITY_FRAMES = {
    "jianlu_peer_pattern": "강한 자기 기준과 독립성을 먼저 세우는 성향",
    "yangren_peer_pattern": "강한 추진력과 승부성을 앞세우는 성향",
    "eating_god_pattern": "꾸준한 생산성과 손에 익은 방식을 중시하는 성향",
    "hurting_officer_pattern": "표현력, 개선 욕구, 기존 방식에 대한 비판성이 강한 성향",
    "indirect_wealth_pattern": "기회 포착, 외부 활동, 거래 감각이 빠른 성향",
    "direct_wealth_pattern": "생활 기준, 소유 감각, 안정성을 먼저 확인하는 성향",
    "seven_killings_pattern": "긴장, 책임, 위기 대응을 민감하게 받아들이는 성향",
    "direct_officer_pattern": "원칙, 평판, 공식 기준을 의식하는 성향",
    "indirect_resource_pattern": "직관, 몰입, 특수한 관심으로 파고드는 성향",
    "direct_resource_pattern": "명분, 문서, 보호와 안정감을 중시하는 성향",
}

PATTERN_LIFE_DOMAIN_FRAMES = {
    "jianlu_peer_pattern": {
        "money": "자기 몫, 독립 수입, 공동 재산의 분리 기준이 먼저 중요하다",
        "career": "독립성, 자기 권한, 동료와의 역할 경계가 직업 판단의 중심이다",
        "relationship": "동등성, 주도권, 서로의 영역을 침범하지 않는 거리가 중요하다",
        "marriage": "생활 주도권과 가족 재정의 분담 기준이 안정성을 좌우한다",
    },
    "yangren_peer_pattern": {
        "money": "큰 움직임과 강한 주도권이 돈을 만들지만, 분배와 지분 문제가 함께 따라온다",
        "career": "강한 역할, 위기 대응, 경쟁 구도에서 자기 존재감이 드러난다",
        "relationship": "호감보다 기세와 주도권이 먼저 보이기 쉬워 관계의 힘 조절이 중요하다",
        "marriage": "생활 안에서 강한 주장과 책임 범위를 어떻게 나누는지가 핵심이다",
    },
    "eating_god_pattern": {
        "money": "반복 가능한 기술과 결과물이 수입의 근거가 된다",
        "career": "손에 익은 실무, 꾸준한 결과물, 안정된 처리력이 직업의 중심이다",
        "relationship": "편안한 표현과 지속적인 배려가 관계를 안정시킨다",
        "marriage": "일상 속 반복되는 책임과 생활의 편안함이 결혼 안정성을 만든다",
    },
    "hurting_officer_pattern": {
        "money": "표현, 기획, 개선 능력이 시장성과 보상으로 이어지는지가 중요하다",
        "career": "기존 질서를 고치는 능력과 공식 평가 사이의 긴장이 직업의 중심이다",
        "relationship": "말의 속도와 표현 강도가 호감과 마찰을 동시에 만든다",
        "marriage": "생활 방식의 자유와 상대가 요구하는 기준 사이의 조율이 중요하다",
    },
    "indirect_wealth_pattern": {
        "money": "외부 거래, 유동 자금, 확장 기회가 재물 판단의 중심이다",
        "career": "사업성, 영업력, 거래처와 외부 자원을 다루는 능력이 중요하다",
        "relationship": "넓은 만남과 외부 인맥이 관계의 기회와 부담을 동시에 만든다",
        "marriage": "활동 범위와 생활 안정 사이의 균형이 결혼 안정성에 영향을 준다",
    },
    "direct_wealth_pattern": {
        "money": "고정 수입, 소유권, 정산, 축적 기준이 재물 판단의 중심이다",
        "career": "보상 기준, 계약상 대가, 안정적인 역할이 직업 판단의 중심이다",
        "relationship": "호의보다 신뢰와 실질적 책임이 관계의 기준이 된다",
        "marriage": "생활비, 주거, 자산 합의가 결혼 안정성의 핵심이다",
    },
    "seven_killings_pattern": {
        "money": "위험 부담, 책임 비용, 압박 속에서 돈이 어떻게 관리되는지가 중요하다",
        "career": "강한 책임, 경쟁, 위기 대응 능력이 직업 판단의 중심이다",
        "relationship": "긴장과 통제감이 관계의 거리와 신뢰를 흔들 수 있다",
        "marriage": "생활 압박과 책임 부담을 어떻게 나누는지가 결혼 안정성을 가른다",
    },
    "direct_officer_pattern": {
        "money": "직책, 신용, 공식 계약과 연결된 보상이 재물 판단의 중심이다",
        "career": "직책, 공식 평가, 조직 질서, 책임 범위가 직업 판단의 중심이다",
        "relationship": "약속, 신뢰, 책임 있는 태도가 관계의 기준이 된다",
        "marriage": "배우자 역할, 법적 책임, 장기 신뢰가 결혼 안정성을 만든다",
    },
    "indirect_resource_pattern": {
        "money": "특수 정보, 비정형 계약, 숨은 위험을 읽는 능력이 재물 판단에 들어온다",
        "career": "특수 지식, 몰입형 전문성, 비공식 자료를 다루는 능력이 중요하다",
        "relationship": "속내를 늦게 열고 독자적으로 판단하는 태도가 관계의 속도를 늦춘다",
        "marriage": "개인 영역과 비정형 생활 방식이 결혼의 체감 안정성에 영향을 준다",
    },
    "direct_resource_pattern": {
        "money": "정식 문서, 자격, 보호 장치가 돈의 근거와 안정성을 좌우한다",
        "career": "자격, 학력, 문서, 제도적 보호가 직업 판단의 중심이다",
        "relationship": "신뢰의 근거와 안정감을 확인한 뒤 마음을 여는 쪽이다",
        "marriage": "가족의 보호, 절차, 문서와 명분이 결혼 안정성에 깊게 들어온다",
    },
}

TEN_GOD_PERSONALITY_FACES = {
    "bi_gyeon": "자기 입장을 쉽게 놓지 않고 독립성을 지키려는 성향",
    "geob_jae": "경쟁과 주도권에 민감하고 몫의 경계를 예민하게 보는 성향",
    "sik_sin": "편안한 방식으로 오래 반복하며 안정된 결과를 만들려는 성향",
    "sang_gwan": "말과 표현이 빠르고 기존 기준을 고쳐 쓰려는 성향",
    "pyeon_jae": "기회를 넓게 보고 사람과 돈의 움직임을 빠르게 읽는 성향",
    "jeong_jae": "손익, 소유권, 생활 안정성을 차분히 계산하는 성향",
    "pyeon_gwan": "압박과 위험에 예민하고 승부를 피하지 않는 성향",
    "jeong_gwan": "원칙, 체면, 평판을 의식하며 책임을 정돈하려는 성향",
    "pyeon_in": "관심이 한쪽으로 깊고 독자적 판단을 쉽게 버리지 않는 성향",
    "jeong_in": "명분, 안전, 보호 장치를 확인한 뒤 움직이려는 성향",
}

RELATION_PERSONALITY_EFFECTS = {
    "same_group": "격국의 본래 성향이 반복되므로 장점은 선명해지지만, 과하면 같은 병도 커진다.",
    "actor_generates_pattern": "격국 중심을 생해 판단과 행동이 비교적 자연스럽게 중심 목표로 모인다.",
    "pattern_generates_actor": "격국의 힘이 다음 행동으로 빠져나가므로 생각보다 표현, 실행, 책임으로 빨리 이동한다.",
    "actor_controls_pattern": "격국 중심을 제어하기 때문에 균형이 맞으면 약이 되고, 강하면 본래 중심을 흔든다.",
    "pattern_controls_actor": "격국 중심이 이 성향을 다루는 구조라, 현실 기준이 과한 생각이나 충동을 눌러 정리한다.",
    "indirect_relation": "직접 생극은 약하지만 위치와 운에서 발동되면 성격의 방향을 우회적으로 바꾼다.",
}

ROLE_GRADE_PERSONALITY_EFFECTS = {
    "core": "성격의 중심축으로 강하게 드러난다.",
    "core_overload": "본래 장점이 과해지면 집착이나 한쪽 치우침으로 보인다.",
    "support": "본래 성향을 안정적으로 보조한다.",
    "strong_regulator": "과한 기운을 제어하는 절제력으로 작용한다.",
    "regulator": "성향의 균형을 잡아 주는 조절력으로 작용한다.",
    "regulator_or_breaker": "균형이 맞으면 절제력이고, 어긋나면 성격의 긴장으로 드러난다.",
    "breaker_or_medicine": "상황에 따라 약이 되기도 하고, 본래 성향을 깨뜨리기도 한다.",
    "conditioned_support": "조건이 맞을 때 성향의 장점으로 살아난다.",
    "source": "겉으로 드러난 행동보다 안쪽의 근거와 배경으로 작용한다.",
    "mixed": "좋고 나쁨이 고정되지 않고 강약과 위치에 따라 성향의 결이 갈린다.",
    "burden": "성격상 부담과 피로를 만드는 쪽으로 작용하기 쉽다.",
    "breaker": "본래 격국의 성향을 흔드는 파격 요소로 작용한다.",
    "danger": "강하게 오면 성격의 압박, 충돌, 과한 반응으로 드러난다.",
}

RELATION_LIFE_DOMAIN_EFFECTS = {
    "same_group": "격국의 중심이 반복되어 장점은 두터워지지만, 과하면 같은 문제가 커진다.",
    "actor_generates_pattern": "작용 십신이 격국 중심을 생하므로 현실 결과가 중심 영역으로 모인다.",
    "pattern_generates_actor": "격국 중심의 힘이 다음 역할로 이동해 사건의 방향이 빠르게 바뀐다.",
    "actor_controls_pattern": "작용 십신이 격국 중심을 제어하므로 균형이 맞으면 조절이고, 강하면 손상이다.",
    "pattern_controls_actor": "격국 중심이 작용 십신을 다루므로 과한 요소를 현실 기준으로 정리한다.",
    "indirect_relation": "직접 생극은 약해도 위치와 운에서 발동되면 해당 영역의 사건으로 올라온다.",
}

ROLE_GRADE_LIFE_DOMAIN_EFFECTS = {
    "core": "월령에서 힘을 얻으면 그 영역의 핵심 장점으로 바로 드러난다.",
    "core_overload": "강하면 장점이 선명하지만 과하면 같은 영역의 부담도 커진다.",
    "support": "필요한 위치에서 받쳐 주면 안정적인 성과로 이어진다.",
    "strong_regulator": "과한 기운을 강하게 눌러 사건을 정리하는 역할을 한다.",
    "regulator": "영역 안의 지나침을 조절해 손실과 충돌을 줄인다.",
    "regulator_or_breaker": "균형이 맞으면 조절이고, 어긋나면 해당 영역을 흔든다.",
    "breaker_or_medicine": "병을 치는 약이 될 수도 있고, 중심을 손상시키는 파격이 될 수도 있다.",
    "conditioned_support": "조건이 맞을 때 성과로 나타나며, 약하면 가능성만 남는다.",
    "source": "겉으로 드러나기보다 배경과 근거로 작용한다.",
    "mixed": "강약과 위치에 따라 기회와 부담이 함께 나타난다.",
    "burden": "운에서 반복되면 해당 영역의 피로와 지연으로 나타난다.",
    "breaker": "강하게 작동하면 해당 영역의 기존 질서를 깨뜨린다.",
    "danger": "강하게 오면 손실, 압박, 충돌을 먼저 점검해야 한다.",
}


def _single_personality_projection(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    relation: str,
    role_grade: str,
) -> str:
    lens = PATTERN_LENS[pattern]
    pattern_label = str(lens["label"])
    pattern_center = str(lens["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    pattern_frame = PATTERN_PERSONALITY_FRAMES[pattern]
    actor_face = TEN_GOD_PERSONALITY_FACES[acting_ten_god]
    relation_effect = RELATION_PERSONALITY_EFFECTS.get(relation, RELATION_PERSONALITY_EFFECTS["indirect_relation"])
    role_effect = ROLE_GRADE_PERSONALITY_EFFECTS.get(role_grade, "월령과 위치에 따라 성향의 결론이 달라진다.")
    action_conclusion = _single_personality_action_conclusion(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        action_nature=action_nature,
        relation_effect=relation_effect,
        role_effect=role_effect,
    )
    return (
        f"{_topic_form(f'{pattern_label}의 {pattern_center}')} 성격과 경향에서 {pattern_frame}이다. "
        f"{_subject_particle(ten_god_label)} 작용하면 {_subject_particle(actor_face)} 더해진다. "
        f"구체적으로는 {_subject_particle(exact)} 판단의 기준으로 올라오며, 무엇을 먼저 확인하고 어디에서 멈추는지가 달라진다. "
        f"{action_conclusion}"
    )


def _single_personality_action_conclusion(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    relation_effect: str,
    role_effect: str,
) -> str:
    pattern_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_group = TEN_GOD_GROUPS[pattern_ten_god]
    acting_group = TEN_GOD_GROUPS[acting_ten_god]
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    ten_god_subject = _subject_particle(ten_god_label)
    action_topic = _topic_form(action_nature)

    if action_nature in {"재극정인", "재극편인"} and pattern_group == "wealth" and acting_group == "resource":
        return (
            f"{action_topic} 성격에서 돈의 근거와 안전장치를 확인하려는 태도로 드러난다. "
            f"{ten_god_subject} 적절하면 신중함과 증빙 감각이 살아나고, 과하면 명분과 걱정이 재물 결정을 늦춘다."
        )
    if action_nature in {"정재극인", "편재극인"} and pattern_group == "resource" and acting_group == "wealth":
        return (
            f"{action_topic} 성격에서 보호받고 확인하려는 마음을 현실 요구가 밀어붙이는 형태로 드러난다. "
            f"{ten_god_subject} 적절하면 실행력이 생기지만, 과하면 안정감과 문서 기반을 먼저 흔든다."
        )
    if action_nature in {"식신생재", "상관생재"}:
        return (
            f"{action_topic} 성격에서 만든 것을 그냥 두지 않고 대가와 결과로 바꾸려는 경향이다. "
            f"강하면 실용성과 판매 감각이 살아나고, 약하면 재주는 있어도 돈으로 확정하는 힘이 늦다."
        )
    if action_nature in {"재생관", "정재생관", "편재생관"}:
        return (
            f"{action_topic} 성격에서 손익 판단을 책임 의식과 공식 기준으로 연결한다. "
            f"강하면 신용과 직책을 의식해 행동이 단정해지고, 과하면 돈과 책임을 지나치게 함께 떠안는다."
        )
    if action_nature == "재생살":
        return (
            "재생살은 성격에서 현실 욕구와 손익 판단이 압박, 경쟁, 위험 부담을 키우는 형태로 나타난다. "
            "판단은 빠르지만 긴장도 함께 커지므로, 근거 없는 확장과 무리한 책임을 먼저 경계해야 한다."
        )
    if action_nature == "관인상생":
        return (
            "관인상생은 성격에서 책임을 명분, 절차, 자격으로 정리하려는 태도다. "
            "강하면 품위와 신뢰가 생기고, 과하면 행동보다 절차와 체면을 먼저 챙긴다."
        )
    if action_nature == "살인상생":
        return (
            "살인상생은 성격에서 압박을 피하지 않고 배움, 문서, 보호 장치로 흡수하려는 태도다. "
            "강하면 위기 대응력이 되지만, 인성이 약하면 불안과 방어심이 먼저 커진다."
        )
    if action_nature == "식신제살":
        return (
            "식신제살은 성격에서 압박을 말로 키우지 않고 손에 익은 처리력으로 낮추려는 경향이다. "
            "강하면 침착한 실무 감각이 되고, 약하면 책임은 큰데 처리 방식이 몸에 붙지 않아 긴장이 남는다."
        )
    if action_nature == "상관견관":
        return (
            "상관견관은 성격에서 규칙을 그대로 받아들이기보다 허점과 불합리를 먼저 보는 경향이다. "
            "결과가 있으면 개선 능력이 되고, 말이 앞서면 직책과 평판을 직접 건드린다."
        )
    if action_nature in {"편인도식", "정인제식", "도식"}:
        return (
            f"{action_topic} 성격에서 생각과 검토가 표현보다 먼저 서는 형태다. "
            "깊이는 생기지만, 과하면 내놓아야 할 결과를 계속 미루고 스스로 확신을 늦춘다."
        )
    if action_nature in {"쟁재", "재물 장악"}:
        return (
            f"{action_topic} 성격에서 내 몫과 타인의 몫을 예민하게 구분하려는 경향이다. "
            "강하면 주도권과 생존력이 되지만, 과하면 가까운 사람과 돈의 경계가 거칠어진다."
        )
    return f"{_topic_form(action_nature)} {relation_effect} {role_effect}"


def _single_life_domain_projection(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    relation: str,
    role_grade: str,
    domain: str,
    domain_label: str,
    actor_face: str,
) -> str:
    lens = PATTERN_LENS[pattern]
    pattern_label = str(lens["label"])
    pattern_center = str(lens["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    pattern_frame = PATTERN_LIFE_DOMAIN_FRAMES[pattern][domain]
    relation_effect = RELATION_LIFE_DOMAIN_EFFECTS.get(relation, RELATION_LIFE_DOMAIN_EFFECTS["indirect_relation"])
    role_effect = ROLE_GRADE_LIFE_DOMAIN_EFFECTS.get(role_grade, "월령과 위치에 따라 사건의 결론이 달라진다.")
    return (
        f"{_topic_form(f'{pattern_label}의 {pattern_center}')} {domain_label}에서 {pattern_frame}. "
        f"{_subject_particle(ten_god_label)} 작용하면 {_subject_particle(actor_face)} 핵심 표면으로 드러난다. "
        f"{exact}의 차이가 사건의 방식과 강도를 가르고, {_topic_form(action_nature)} {relation_effect} {role_effect}"
    )


def _domain_projections(
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
    *,
    relation: str,
    role_grade: str,
) -> dict[str, str]:
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact_actor = f"{ten_god_label}의 {exact}"
    lens = PATTERN_LENS[pattern]
    center = lens["center"]
    group_faces = {
        "peer": {
            "money": "몫, 공동 비용, 지분, 가까운 사람과의 소유권",
            "career": "독립성, 동료 경쟁, 자기 주도권",
            "relationship": "동등한 관계, 주도권, 경쟁심",
            "marriage": "생활 주도권, 가족 재정의 분담, 배우자와의 힘의 균형",
            "personality": "자기 기준, 독립성, 양보와 고집의 경계",
        },
        "output": {
            "money": "기술, 결과물, 서비스, 표현물의 수입화",
            "career": "실무 성과, 기획력, 발표, 결과물로 받는 평가",
            "relationship": "감정 표현, 말의 방식, 호감이 전달되는 속도",
            "marriage": "일상 표현, 생활 속 배려, 함께 만들어내는 결과",
            "personality": "표현 방식, 실행 속도, 결과물을 밖으로 내놓는 태도",
        },
        "wealth": {
            "money": "수입, 소유권, 거래, 회수, 축적과 지출 기준",
            "career": "보상, 계약, 영업 성과, 현실 자원",
            "relationship": "돈과 사람이 얽히는 방식, 호의와 계산의 경계",
            "marriage": "생활비, 자산, 주거, 부부 사이의 재정 합의",
            "personality": "현실 감각, 소유 의식, 손익을 판단하는 기준",
        },
        "officer": {
            "money": "책임이 붙은 돈, 계약상 의무, 직책과 연결된 보상",
            "career": "직책, 권한, 공식 평가, 조직 안의 책임",
            "relationship": "약속, 책임감, 상대에게 요구하는 기준",
            "marriage": "배우자 역할, 법적·생활적 책임, 장기적 신뢰",
            "personality": "원칙, 평판 의식, 책임을 받아들이는 태도",
        },
        "resource": {
            "money": "문서, 자격, 보호 장치, 명분이 재물에 끼어드는 방식",
            "career": "자격, 학습, 문서, 전문성, 보호받는 기반",
            "relationship": "보호 욕구, 신뢰의 근거, 마음을 여는 속도",
            "marriage": "가족의 보호, 문서와 절차, 안정감을 확인하는 방식",
            "personality": "생각의 깊이, 보류 습관, 명분과 안전을 찾는 태도",
        },
    }
    faces = group_faces.get(acting_group, group_faces["peer"])
    pattern_label = lens["label"]
    pattern_center = f"{pattern_label}의 {center}"
    return {
        "money": (
            f"{_topic_form(pattern_center)} 재물에서 {_euro_form(faces['money'])} 드러난다. "
            f"{_subject_particle(exact_actor)} {_object_form(action_nature)} 거치면 수입, 보존, 분배의 결론이 달라진다. "
            + _single_life_domain_projection(
                pattern=pattern,
                acting_ten_god=acting_ten_god,
                action_nature=action_nature,
                relation=relation,
                role_grade=role_grade,
                domain="money",
                domain_label="재물",
                actor_face=faces["money"],
            )
        ),
        "career": (
            f"{_topic_form(pattern_center)} 직업에서 {_euro_form(faces['career'])} 드러난다. "
            f"{_subject_particle(ten_god_label)} {_euro_form(action_nature)} 작용하면 역할, 권한, 성과 방식이 이 작용으로 구체화된다. "
            + _single_life_domain_projection(
                pattern=pattern,
                acting_ten_god=acting_ten_god,
                action_nature=action_nature,
                relation=relation,
                role_grade=role_grade,
                domain="career",
                domain_label="직업",
                actor_face=faces["career"],
            )
        ),
        "relationship": (
            f"{_topic_form(pattern_center)} 관계에서 {_euro_form(faces['relationship'])} 드러난다. "
            f"{_subject_particle(exact_actor)} 가까운 사람과의 거리, 신뢰, 부담의 방향을 만든다. "
            + _single_life_domain_projection(
                pattern=pattern,
                acting_ten_god=acting_ten_god,
                action_nature=action_nature,
                relation=relation,
                role_grade=role_grade,
                domain="relationship",
                domain_label="관계",
                actor_face=faces["relationship"],
            )
        ),
        "marriage": (
            f"{_topic_form(pattern_center)} 결혼과 가정에서 {_euro_form(faces['marriage'])} 드러난다. "
            f"{_subject_particle(ten_god_label)} {_euro_form(action_nature)} 작용하면 생활 기준과 책임의 안정성을 바꾼다. "
            + _single_life_domain_projection(
                pattern=pattern,
                acting_ten_god=acting_ten_god,
                action_nature=action_nature,
                relation=relation,
                role_grade=role_grade,
                domain="marriage",
                domain_label="결혼과 가정",
                actor_face=faces["marriage"],
            )
        ),
        "personality": _single_personality_projection(
            pattern=pattern,
            acting_ten_god=acting_ten_god,
            action_nature=action_nature,
            relation=relation,
            role_grade=role_grade,
        ),
    }


def _domain_priority(pattern: str, acting_ten_god: str, action_nature: str) -> list[str]:
    priorities = list(TEN_GOD_EXACT_ACTION_PROFILE[acting_ten_god]["domains"])
    if "재" in action_nature and "money" not in priorities:
        priorities.insert(0, "money")
    if "관" in action_nature and "career" not in priorities:
        priorities.insert(0, "career")
    if "인" in action_nature and "personality" not in priorities:
        priorities.append("personality")
    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and "money" not in priorities:
        priorities.insert(0, "money")
    if pattern in {"direct_officer_pattern", "seven_killings_pattern"} and "career" not in priorities:
        priorities.insert(0, "career")
    return list(dict.fromkeys(priorities))


SINGLE_EVENT_DOMAIN_FACES = {
    "peer": {
        "money": "지분, 몫, 공동 비용, 가까운 사람과의 금전 경계",
        "career": "독립성, 동료 경쟁, 역할 주도권",
        "relationship": "주도권, 거리 조절, 동등성의 문제",
        "marriage": "생활 주도권, 가족 재정의 분담, 배우자와의 힘의 균형",
        "personality": "자기 기준, 독립성, 양보와 고집의 경계",
    },
    "output": {
        "money": "기술, 결과물, 말과 글, 서비스의 수입화",
        "career": "실무 성과, 기획력, 발표, 결과물에 대한 평가",
        "relationship": "감정 표현, 말투, 호감이 전달되는 속도",
        "marriage": "일상 표현, 생활 속 배려, 함께 만드는 결과",
        "personality": "표현 방식, 실행 속도, 결과물을 내놓는 태도",
    },
    "wealth": {
        "money": "수입, 소유권, 거래, 회수, 축적과 지출 기준",
        "career": "보상, 계약, 영업 성과, 현실 자원",
        "relationship": "호의와 계산의 경계, 돈과 사람이 얽히는 방식",
        "marriage": "생활비, 자산, 주거, 부부 사이의 재정 합의",
        "personality": "현실 감각, 소유 의식, 손익을 판단하는 기준",
    },
    "officer": {
        "money": "책임이 붙은 돈, 계약상 의무, 직책과 연결된 보상",
        "career": "직책, 권한, 공식 평가, 조직 안의 책임",
        "relationship": "약속, 책임감, 상대에게 요구하는 기준",
        "marriage": "배우자 역할, 법적·생활적 책임, 장기적 신뢰",
        "personality": "원칙, 평판 의식, 책임을 받아들이는 태도",
    },
    "resource": {
        "money": "문서, 자격, 보호 장치, 명분이 재물에 개입하는 방식",
        "career": "자격, 학습, 문서, 전문성, 보호받는 기반",
        "relationship": "보호 욕구, 신뢰의 근거, 마음을 여는 속도",
        "marriage": "가족의 보호, 문서와 절차, 안정감을 확인하는 방식",
        "personality": "생각의 깊이, 보류 습관, 명분과 안전을 찾는 태도",
    },
}


SINGLE_EVENT_ROLE_TAILS = {
    "core": "격의 중심을 강화하므로 성과가 분명해지지만, 과하면 한쪽으로 몰린다.",
    "core_overload": "중심이 과하게 강해지는 작용이라 장점과 병증이 함께 커진다.",
    "support": "격을 돕는 작용이므로 월령에서 필요하고 뿌리가 있으면 현실 성과로 쓰인다.",
    "strong_regulator": "격국의 거친 힘을 강하게 제어하므로 권한과 책임의 질서를 세운다.",
    "regulator": "격국의 병을 조절하는 작용이라 과한 부분을 현실 기준으로 눌러 준다.",
    "regulator_or_breaker": "균형이 맞으면 약이 되지만, 강약이 어긋나면 격의 중심을 건드린다.",
    "breaker_or_medicine": "병을 치는 약이 될 수도 있고, 중심을 손상시키는 파격이 될 수도 있다.",
    "conditioned_support": "조건이 맞을 때만 성과로 이어지며, 약하면 책임만 먼저 보인다.",
    "source": "격의 근거를 공급하므로 숨어 있어도 운에서 살아나면 배경이 된다.",
    "mixed": "쓸 수 있는 면과 부담이 함께 있으므로 월령과 위치가 결론을 가른다.",
    "burden": "격의 중심에 부담을 얹는 작용이라 운에서 반복되면 피로와 지연으로 보인다.",
    "breaker": "격의 질서를 깨뜨리기 쉬우므로 운에서 강해지면 충돌이나 손상으로 나타난다.",
    "danger": "위험을 키우는 작용이라 운에서 강하게 오면 손실, 압박, 갈등을 먼저 점검한다.",
}


SINGLE_LUCK_DOMAIN_CONTEXT = {
    "money": {
        "daeun": "수입 구조, 소유권, 회수 기준, 지출 습관이 몇 해에 걸쳐 바뀐다",
        "seun": "계약, 정산, 큰 지출, 회수 문제처럼 손에 잡히는 돈 사건으로 드러난다",
    },
    "career": {
        "daeun": "직무 범위, 평가 방식, 책임의 크기, 조직 안의 위치가 길게 조정된다",
        "seun": "인사 평가, 직책 변화, 업무 배정, 상사와의 책임 문제로 나타난다",
    },
    "relationship": {
        "daeun": "사람을 대하는 태도, 만남의 폭, 거리 조절 방식이 오래 바뀐다",
        "seun": "새 인연, 기존 관계의 충돌, 연락 방식, 신뢰 확인으로 사건화된다",
    },
    "marriage": {
        "daeun": "주거, 가족 책임, 배우자와의 생활 기준이 장기 과제로 올라온다",
        "seun": "혼인 결정, 가족 협의, 생활비, 주거 조건 같은 구체 문제로 드러난다",
    },
    "personality": {
        "daeun": "판단 습관, 관심 분야, 선택 기준이 서서히 달라진다",
        "seun": "중요한 결정을 앞두고 성격의 장점과 약점이 뚜렷하게 드러난다",
    },
    "reputation": {
        "daeun": "평판, 신용, 사회적 역할의 무게가 길게 형성된다",
        "seun": "평가, 공개적 인정, 평판 손상이나 회복 같은 사건으로 드러난다",
    },
}


SINGLE_LUCK_GROUP_CONTEXT = {
    "peer": "사람, 지분, 동업, 경쟁이 운의 입구가 된다.",
    "output": "기술, 말, 글, 결과물, 서비스가 운의 입구가 된다.",
    "wealth": "돈, 계약, 소유권, 거래 조건이 운의 입구가 된다.",
    "officer": "책임, 평가, 직책, 규칙이 운의 입구가 된다.",
    "resource": "문서, 자격, 학업, 보호 장치가 운의 입구가 된다.",
}


SINGLE_LUCK_ROLE_CONTEXT = {
    "core": "격의 중심이 운에서 살아나므로 장점도 분명하지만 과하면 한쪽으로 몰린다.",
    "core_overload": "중심이 지나치게 강해지는 운에서는 성과와 병증이 함께 커진다.",
    "support": "월령이 필요로 하는 보조 작용이면 성과가 안정적으로 붙는다.",
    "strong_regulator": "과한 힘을 강하게 제어하는 운이므로 권한과 책임의 질서가 선명해진다.",
    "regulator": "부담을 조절하는 운이면 손실보다 정리가 먼저 일어난다.",
    "regulator_or_breaker": "강약이 맞으면 약이고, 맞지 않으면 격의 중심을 직접 건드린다.",
    "breaker_or_medicine": "운에서 약으로 쓰이면 막힌 부분이 풀리고, 병으로 쓰이면 중심이 손상된다.",
    "conditioned_support": "필요한 위치와 뿌리가 있을 때 성과로 이어지고, 약하면 책임만 먼저 보인다.",
    "source": "숨어 있던 근거가 운에서 살아나면 배경과 보호 장치가 마련된다.",
    "mixed": "기회와 부담이 함께 움직이므로 월령, 위치, 투출 여부가 결론을 가른다.",
    "burden": "부담이 반복되는 운에서는 피로, 지연, 책임 문제가 먼저 올라온다.",
    "breaker": "격의 질서를 흔드는 운에서는 충돌, 손상, 방향 전환을 먼저 살핀다.",
    "danger": "손실, 압박, 갈등이 커질 수 있는 운이므로 발동 지점을 좁혀 보아야 한다.",
}


def _single_luck_activation(
    *,
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
    role_grade: str,
    domain_priority: list[str],
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    primary_domain = domain_priority[0] if domain_priority else "personality"
    domain_label = {
        "money": "재물",
        "career": "직업",
        "relationship": "관계",
        "marriage": "결혼과 가정",
        "personality": "성격과 경향",
        "reputation": "명예와 평판",
    }.get(primary_domain, primary_domain)
    domain_context = SINGLE_LUCK_DOMAIN_CONTEXT.get(primary_domain, SINGLE_LUCK_DOMAIN_CONTEXT["personality"])
    group_context = SINGLE_LUCK_GROUP_CONTEXT.get(acting_group, "해당 십신의 현실 작용이 운의 입구가 된다.")
    role_context = SINGLE_LUCK_ROLE_CONTEXT.get(role_grade, "강약과 위치에 따라 운의 결론이 달라진다.")
    return (
        f"{pattern_label}에서 {ten_god_label} 운이 들어오면 {_subject_form(action_nature)} "
        f"{_object_form(pattern_center)} 통해 {domain_label} 문제로 발동한다. "
        f"대운에서는 {domain_context['daeun']}. "
        f"세운에서는 {domain_context['seun']}. "
        f"{group_context} {role_context}"
    )


def _single_event_manifestations(
    *,
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
    role_grade: str,
    domain_priority: list[str],
) -> dict[str, str]:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    face = SINGLE_EVENT_DOMAIN_FACES.get(acting_group, SINGLE_EVENT_DOMAIN_FACES["peer"])
    role_tail = SINGLE_EVENT_ROLE_TAILS.get(role_grade, "강약과 위치에 따라 사건의 방향이 달라진다.")
    center_topic = _topic_form(f"{pattern_label}의 {pattern_center}")
    def sentence(domain: str, label: str) -> str:
        return (
            f"운에서 {_subject_particle(action_nature)} 발동하면 {center_topic} {label} 영역에서 {_euro_form(face[domain])} 현실화된다. "
            f"{_subject_particle(ten_god_label)} 투출하면 외부 사건으로 빠르게 드러나고, 지장간에 있으면 특정 운에서 조건이 열릴 때 올라온다. "
            f"{role_tail}"
        )

    return {
        "money": sentence("money", "재물"),
        "career": sentence("career", "직업"),
        "relationship": sentence("relationship", "관계"),
        "marriage": sentence("marriage", "결혼과 가정"),
        "personality": sentence("personality", "성향"),
        "luck_activation": _single_luck_activation(
            pattern=pattern,
            acting_ten_god=acting_ten_god,
            acting_group=acting_group,
            action_nature=action_nature,
            role_grade=role_grade,
            domain_priority=domain_priority,
        ),
    }


def _same_group_action_nature(pattern_ten_god: str, acting_ten_god: str) -> str:
    if pattern_ten_god == acting_ten_god:
        return f"{TEN_GOD_LABELS[acting_ten_god]} 중첩"
    group = TEN_GOD_GROUPS[pattern_ten_god]
    if group == "wealth":
        return "정편재 혼재"
    if group == "officer":
        return "관살혼잡"
    if group == "output":
        return "식상혼잡"
    if group == "resource":
        return "인성혼잡"
    if group == "peer":
        return "비겁혼잡"
    return "중심 강화"


def _exact_action_nature(pattern_ten_god: str, action_nature: str, acting_ten_god: str) -> str:
    if action_nature == "중심 강화":
        return _same_group_action_nature(pattern_ten_god, acting_ten_god)
    if action_nature == "관살 중첩":
        if pattern_ten_god == acting_ten_god == "pyeon_gwan":
            return "편관 중첩"
        if TEN_GOD_GROUPS[pattern_ten_god] == "officer" and TEN_GOD_GROUPS[acting_ten_god] == "officer":
            return "관살혼잡"
    if action_nature == "식상생재":
        if acting_ten_god == "sik_sin":
            return "식신생재"
        if acting_ten_god == "sang_gwan":
            return "상관생재"
    if action_nature == "상관견관":
        if acting_ten_god == "sik_sin":
            return "식신제관"
        if acting_ten_god == "sang_gwan":
            return "상관견관"
    if action_nature == "재극인":
        if acting_ten_god == "pyeon_jae":
            return "편재극인"
        if acting_ten_god == "jeong_jae":
            return "정재극인"
        if acting_ten_god == "pyeon_in":
            return "재극편인"
        if acting_ten_god == "jeong_in":
            return "재극정인"
    if action_nature == "재생관":
        if acting_ten_god == "pyeon_gwan":
            return "재생살"
        if acting_ten_god == "jeong_gwan":
            return "재생관"
        if acting_ten_god == "pyeon_jae":
            return "편재생관"
        if acting_ten_god == "jeong_jae":
            return "정재생관"
    if action_nature == "도식":
        if acting_ten_god == "pyeon_in":
            return "편인도식"
        if acting_ten_god == "jeong_in":
            return "정인제식"
    if action_nature == "관인상생":
        if acting_ten_god == "pyeon_gwan":
            return "살인상생"
        if acting_ten_god == "jeong_gwan":
            return "관인상생"
    return action_nature


def _critical_single_action_lens(
    *,
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
) -> dict[str, object]:
    """Return pattern-specific disease/medicine text for named classical actions."""

    lens: dict[str, object] = {
        "excess": "",
        "deficiency": "",
        "timing": "",
        "success_append": "",
        "failure_append": "",
        "basis_codes": [],
    }

    def set_lens(
        *,
        key: str,
        excess: str,
        deficiency: str,
        timing: str,
        success_append: str = "",
        failure_append: str = "",
    ) -> dict[str, object]:
        return {
            "excess": excess,
            "deficiency": deficiency,
            "timing": timing,
            "success_append": success_append,
            "failure_append": failure_append,
            "basis_codes": [f"gyeokguk_single_critical_action:{key}"],
        }

    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "peer":
        if acting_ten_god == "geob_jae":
            if pattern == "direct_wealth_pattern":
                return set_lens(
                    key="direct_wealth_bigeop_jaengjae",
                    excess="정재격에서 겁재가 강하면 겁재쟁재가 생활 재정과 소유권을 직접 건드린다. 돈이 보일 때 가까운 사람, 가족 비용, 공동 지출에서 내 몫이 흐려지기 쉽다.",
                    deficiency="겁재가 너무 약하면 정재의 소유 기준은 있어도 실제 분배 국면에서 자기 몫을 지키는 힘이 부족하다.",
                    timing="운에서 겁재가 강하게 오면 생활비, 공동 자금, 공동 지출, 지분, 가족 재정, 가까운 사람과의 정산 문제가 사건화된다.",
                    failure_append="정재격의 겁재는 안정 재정과 소유권을 흔드는 작용이다.",
                )
            if pattern == "indirect_wealth_pattern":
                return set_lens(
                    key="indirect_wealth_bigeop_jaengjae",
                    excess="편재격에서 겁재가 강하면 겁재쟁재가 외부 거래와 유동 자금에서 나타난다. 동업, 투자, 영업권, 거래처 배분처럼 큰돈의 흐름을 두고 경쟁이 생긴다.",
                    deficiency="겁재가 너무 약하면 편재의 외부 기회가 있어도 협상력과 주도권이 약해져 이익 배분에서 밀릴 수 있다.",
                    timing="운에서 겁재가 강하게 오면 동업, 투자금, 거래처, 사업 지분, 외부 자금의 몫 문제가 먼저 드러난다.",
                    failure_append="편재격의 겁재는 유동 자금과 외부 기회의 배분권을 건드리는 작용이다.",
                )
            return set_lens(
                key="bigeop_jaengjae",
                excess="재격에서 겁재가 강하면 겁재쟁재가 된다. 돈이 없어서가 아니라, 돈이 보일 때 지분, 몫, 공동 비용, 동업 손익이 예민해진다.",
                deficiency="비겁이 너무 약하면 자기 몫을 주장하지 못해 수입과 소유권을 남에게 넘기기 쉽다.",
                timing="운에서 겁재가 강하게 오면 동업, 지분, 공동 자금, 가까운 사람과의 정산 문제가 먼저 사건화된다.",
                failure_append="재격의 겁재는 단순한 경쟁심이 아니라 재성의 소유권을 직접 건드리는 작용이다.",
            )
        if pattern == "direct_wealth_pattern":
            return set_lens(
                key="direct_wealth_bigeop_bunjae",
                excess="정재격에서 비견이 강하면 안정적으로 모아야 할 돈이 가족, 동료, 생활 공동체 안에서 나뉜다. 소유 기준은 있으나 단독 관리가 약해진다.",
                deficiency="비견이 약하면 정재를 지키는 자기 기준이 약해져 생활 재정이 주변 사정에 끌려간다.",
                timing="운에서 비견이 오면 공동 명의, 가족 비용, 생활비 분담, 동등한 몫을 요구하는 일이 드러난다.",
            )
        if pattern == "indirect_wealth_pattern":
            return set_lens(
                key="indirect_wealth_bigeop_bunjae",
                excess="편재격에서 비견이 강하면 외부 거래와 사업 기회가 동등한 권리 주장 속에서 나뉜다. 이익은 생겨도 독점력과 회수력이 약해질 수 있다.",
                deficiency="비견이 약하면 편재의 기회를 잡아도 협상 기준과 자기 지분을 세우는 힘이 부족하다.",
                timing="운에서 비견이 오면 거래처, 영업권, 공동 사업, 외부 수익의 배분 문제가 드러난다.",
            )
        return set_lens(
            key="bigeop_bunjae",
            excess="재격에서 비견이 강하면 재물을 함께 나누는 분재가 된다. 공동 소유, 가족 재정, 동등한 권리 주장으로 재물의 단독성이 약해진다.",
            deficiency="비견이 약하면 재물을 지키는 자기 기준이 약해져 주변 사정에 끌려간다.",
            timing="운에서 비견이 오면 공동 명의, 가족 비용, 동등한 몫을 요구하는 문제가 드러난다.",
        )

    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "output":
        if acting_ten_god == "sik_sin":
            if pattern == "direct_wealth_pattern":
                return set_lens(
                    key="direct_wealth_siksin_saengjae",
                    excess="정재격에서 식신이 과하면 생산은 안정되지만 수입이 생활 재정 안에서 천천히 굳어진다. 돈은 안정적이나 회전과 확장 속도가 둔해질 수 있다.",
                    deficiency="식신이 약하면 정재를 받칠 반복 가능한 기술, 상품, 서비스가 부족해 고정 수입의 근거가 약해진다.",
                    timing="운에서 식신이 살아나면 기술, 상품, 서비스가 월급, 정산, 고정 거래 같은 안정 수입으로 올라온다.",
                    success_append="정재격의 식신생재는 결과물이 안정 수입과 소유 기반으로 굳는 작용이다.",
                )
            if pattern == "indirect_wealth_pattern":
                return set_lens(
                    key="indirect_wealth_siksin_saengjae",
                    excess="편재격에서 식신이 과하면 꾸준한 결과물이 외부 거래로 이어지지만, 속도가 느리면 시장 기회를 놓칠 수 있다.",
                    deficiency="식신이 약하면 편재를 열어 줄 상품, 기술, 반복 서비스가 부족해 외부 기회가 말뿐으로 남는다.",
                    timing="운에서 식신이 살아나면 기술, 상품, 서비스가 영업, 거래처, 사업 수익의 근거로 올라온다.",
                    success_append="편재격의 식신생재는 결과물이 외부 거래와 사업 기회로 바뀌는 작용이다.",
                )
            return set_lens(
                key="siksin_saengjae",
                excess="재격에서 식신이 과하면 생산은 안정되지만 속도가 늦어져 재물의 회전이 둔해진다.",
                deficiency="식신이 약하면 재성을 생하는 결과물이 부족해 돈의 근거가 약해진다.",
                timing="운에서 식신이 살아나면 반복 가능한 기술, 상품, 서비스가 수입의 근거로 올라온다.",
                success_append="정재·편재가 결과물을 받아 주면 재물은 말이 아니라 실제 상품과 서비스에서 생긴다.",
            )
        if pattern == "direct_wealth_pattern":
            return set_lens(
                key="direct_wealth_sanggwan_saengjae",
                excess="정재격에서 상관이 과하면 기획과 표현이 안정 재정의 기준을 흔든다. 수입은 만들 수 있으나 말, 홍보, 확장 욕구가 정산과 신용을 앞서기 쉽다.",
                deficiency="상관이 약하면 정재를 시장에 드러내고 고정 수입을 넓히는 표현력과 기획력이 부족하다.",
                timing="운에서 상관이 오면 홍보, 기획, 발표, 영업 방식이 안정 수입의 입구를 바꾼다.",
                success_append="정재격의 상관생재는 표현과 기획이 안정 재정으로 정리될 때 힘이 난다.",
            )
        if pattern == "indirect_wealth_pattern":
            return set_lens(
                key="indirect_wealth_sanggwan_saengjae",
                excess="편재격에서 상관이 과하면 말, 기획, 홍보가 외부 돈을 빠르게 끌어오지만 회수와 계약이 뒤따르지 않으면 손실 폭도 커진다.",
                deficiency="상관이 약하면 편재의 거래 기회를 넓힐 홍보력, 설득력, 시장 노출이 부족하다.",
                timing="운에서 상관이 오면 광고, 영업, 콘텐츠, 제휴, 사업 확장이 재물의 입구를 바꾼다.",
                success_append="편재격의 상관생재는 재주가 시장성과 큰 거래로 전환되는 작용이다.",
            )
        return set_lens(
            key="sanggwan_saengjae",
            excess="재격에서 상관이 과하면 재물보다 말, 기획, 과감한 확장이 앞서 계약과 평판을 흔든다.",
            deficiency="상관이 약하면 시장에 드러내는 힘이 부족해 재물 기회가 작아진다.",
            timing="운에서 상관이 오면 홍보, 기획, 영업, 표현 방식이 재물의 입구를 바꾼다.",
            success_append="상관생재가 성립하면 재주는 시장성으로 바뀐다.",
        )

    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "officer":
        if acting_ten_god == "pyeon_gwan":
            if pattern == "direct_wealth_pattern":
                return set_lens(
                    key="direct_wealth_jaesaengsal",
                    excess="정재격에서 편관이 과하면 안정 재정이 위험 책임으로 묶인다. 돈 자체보다 보증, 규정, 법적 책임, 강한 압박이 재물의 운용을 무겁게 만든다.",
                    deficiency="편관이 약하면 정재를 지킬 긴장감과 위기 대응 장치가 부족해 관리가 느슨해진다.",
                    timing="운에서 편관이 오면 생활 재정, 소유, 계약이 책임, 압박, 법적 부담으로 이어질 수 있다.",
                )
            if pattern == "indirect_wealth_pattern":
                return set_lens(
                    key="indirect_wealth_jaesaengsal",
                    excess="편재격에서 편관이 과하면 재생살이 강하게 드러난다. 투자, 거래, 사업 확장이 경쟁, 손실 위험, 강한 책임으로 번질 수 있다.",
                    deficiency="편관이 약하면 큰 거래와 외부 자금을 감당할 압박 대응력과 통제 장치가 부족하다.",
                    timing="운에서 편관이 오면 투자, 사업, 외부 거래가 경쟁, 법적 부담, 강한 책임 문제로 이어질 수 있다.",
                )
            return set_lens(
                key="jaesaengsal_in_wealth_pattern",
                excess="재격에서 편관이 과하면 재생살이 되어 돈이 권한보다 위험 부담과 압박으로 바뀐다.",
                deficiency="편관이 약하면 큰 거래를 감당할 긴장감과 책임 장치가 부족해진다.",
                timing="운에서 편관이 오면 재물 문제가 책임, 경쟁, 법적 부담, 강한 압박으로 이어질 수 있다.",
            )
        if pattern == "direct_wealth_pattern":
            return set_lens(
                key="direct_wealth_jaesaenggwan",
                excess="정재격에서 정관이 과하면 안정 재정이 직책과 책임으로 묶인다. 신용은 생기지만 돈을 자유롭게 움직이는 폭은 좁아진다.",
                deficiency="정관이 약하면 정재의 소유와 수입이 신용, 직책, 제도권 평가로 이어지는 힘이 부족하다.",
                timing="운에서 정관이 오면 고정 수입, 소유, 신용이 직책, 평가, 공식 책임으로 연결된다.",
            )
        if pattern == "indirect_wealth_pattern":
            return set_lens(
                key="indirect_wealth_jaesaenggwan",
                excess="편재격에서 정관이 과하면 외부 거래와 사업 수익이 제도권 책임으로 정리된다. 과하면 확장성보다 규정과 책임이 먼저 커진다.",
                deficiency="정관이 약하면 편재의 거래와 확장이 신용, 공식 계약, 직책으로 굳어지는 힘이 부족하다.",
                timing="운에서 정관이 오면 거래처, 사업 수익, 외부 자금이 계약, 평가, 공식 책임으로 연결된다.",
            )
        return set_lens(
            key="jaesaenggwan_in_wealth_pattern",
            excess="재격에서 정관이 과하면 재물이 직책과 책임으로 묶여 자유로운 운용이 어려워진다.",
            deficiency="정관이 약하면 돈이 생겨도 신용, 직책, 제도권 평가로 이어지는 힘이 부족하다.",
            timing="운에서 정관이 오면 수입과 소유가 직책, 평가, 공식 책임으로 연결된다.",
        )

    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "resource":
        if acting_ten_god == "jeong_in":
            if pattern == "direct_wealth_pattern":
                return set_lens(
                    key="direct_wealth_pattern_jeongin",
                    excess="정재격에서 정인이 과하면 명분, 문서, 보호 논리가 안정 재정의 실행을 늦춘다. 좋게 작용하면 재물의 근거와 문서 안정성, 소유권과 계약의 근거가 단단해진다.",
                    deficiency="정인이 약하면 정재의 문서 근거, 자격, 보호 장치가 약해져 소유와 정산이 불안정해진다.",
                    timing="운에서 정인이 오면 계약서, 자격, 문서, 증빙, 보호자 문제가 생활 재정과 소유 판단에 직접 개입한다.",
                )
            if pattern == "indirect_wealth_pattern":
                return set_lens(
                    key="indirect_wealth_pattern_jeongin",
                    excess="편재격에서 정인이 과하면 외부 거래와 투자 판단이 문서, 명분, 보호 논리에 묶인다. 좋게 작용하면 큰 거래의 법적 근거와 신뢰 장치가 생긴다.",
                    deficiency="정인이 약하면 편재의 거래와 확장을 받쳐 줄 문서, 증빙, 공식 보호 장치가 부족하다.",
                    timing="운에서 정인이 오면 투자 계약, 외부 제안, 거래 문서, 보증 자료가 재물 판단에 개입한다.",
                )
            return set_lens(
                key="wealth_pattern_jeongin",
                excess="재격에서 정인이 과하면 명분, 문서, 보호 논리가 재물 실행을 늦춘다. 좋게 작용하면 재물의 근거와 문서 안정성을 만든다.",
                deficiency="정인이 약하면 재물의 문서 근거, 자격, 보호 장치가 약해져 소유가 불안정해진다.",
                timing="운에서 정인이 오면 계약서, 자격, 문서, 보호자 문제가 재물 판단에 직접 개입한다.",
            )
        if pattern == "direct_wealth_pattern":
            return set_lens(
                key="direct_wealth_pattern_pyeonin",
                excess="정재격에서 편인이 과하면 고립된 판단과 비정형 정보가 생활 재정의 실행을 늦춘다. 숨은 리스크를 읽는 장점도 있으나 관리가 지나치게 복잡해질 수 있다.",
                deficiency="편인이 약하면 정재를 지키는 데 필요한 특수 정보, 비공식 자료, 숨은 위험을 읽는 힘이 부족하다.",
                timing="운에서 편인이 오면 숨은 계약 조건, 특수 문서, 비공식 정보가 생활 재정과 소유 문제로 올라온다.",
            )
        if pattern == "indirect_wealth_pattern":
            return set_lens(
                key="indirect_wealth_pattern_pyeonin",
                excess="편재격에서 편인이 과하면 외부 돈의 흐름을 지나치게 비정형적으로 읽어 거래 판단이 굴절될 수 있다. 특수 정보는 강하지만 확정과 회수가 늦어진다.",
                deficiency="편인이 약하면 편재의 외부 기회 속에 숨어 있는 정보, 특수 계약, 비공식 리스크를 읽는 힘이 부족하다.",
                timing="운에서 편인이 오면 비공식 제안, 특수 투자, 숨은 계약 조건, 비정형 수입 구조가 재물 문제로 올라온다.",
            )
        return set_lens(
            key="wealth_pattern_pyeonin",
            excess="재격에서 편인이 과하면 비정형 판단과 고립된 생각이 돈의 실행을 늦추고 거래 판단을 비틀 수 있다.",
            deficiency="편인이 약하면 특수 정보, 비공식 자료, 숨은 리스크를 읽는 힘이 부족하다.",
            timing="운에서 편인이 오면 숨은 정보, 특수 계약, 비정형 수입 구조가 재물 문제로 올라온다.",
        )

    if pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "wealth":
        if acting_ten_god == "jeong_jae":
            if pattern == "direct_resource_pattern":
                return set_lens(
                    key="direct_resource_pattern_jeongjae_controls_resource",
                    excess="정인격에서 정재가 과하면 재극인이 되어 문서, 학업, 보호 기반이 생활 재정 요구에 눌린다. 좋게 작용하면 공부와 자격이 현실 수입으로 정리된다.",
                    deficiency="정재가 약하면 정인의 공부와 명분이 실제 생활 기반과 고정 수입으로 연결되는 힘이 부족하다.",
                    timing="운에서 정재가 오면 학업, 자격, 문서가 돈과 생활 현실, 생활비, 고정 수입, 정산 문제 앞에서 다시 정리된다.",
                    failure_append="정인격의 정재극인은 정식 문서와 보호 기반을 현실 생활 재정이 시험하는 작용이다.",
                )
            if pattern == "indirect_resource_pattern":
                return set_lens(
                    key="indirect_resource_pattern_jeongjae_controls_resource",
                    excess="편인격에서 정재가 과하면 특수 지식과 몰입이 생활 재정과 소유 기준에 눌린다. 좋게 작용하면 비정형 전문성이 실질 수입으로 정리된다.",
                    deficiency="정재가 약하면 편인의 특수 지식이 고정 수입과 생활 기반으로 굳어지는 힘이 부족하다.",
                    timing="운에서 정재가 오면 특수 공부, 비공식 자료, 몰입형 전문성이 생활 재정과 정산 문제로 검증된다.",
                    failure_append="편인격의 정재극인은 특수한 인성 기반을 현실 소득 기준으로 끌어내리는 작용이다.",
                )
            return set_lens(
                key="resource_pattern_jeongjae_controls_resource",
                excess="인성격에서 정재가 과하면 재극인이 되어 문서, 학업, 보호 기반을 현실 재정 요구가 직접 압박한다.",
                deficiency="정재가 약하면 공부와 명분은 있어도 현실 수입과 생활 기반으로 연결되는 힘이 부족하다.",
                timing="운에서 정재가 오면 학업, 자격, 문서가 돈과 생활 현실 앞에서 다시 정리된다.",
                failure_append="인성격의 재극인은 재격의 현실성 강화와 다르다. 격의 중심인 인성을 건드리므로 문서 손상과 실행 촉진을 함께 본다.",
            )
        if pattern == "direct_resource_pattern":
            return set_lens(
                key="direct_resource_pattern_pyeonjae_controls_resource",
                excess="정인격에서 편재가 과하면 정식 공부와 문서 기반이 외부 거래, 투자, 시장 요구에 흔들린다. 좋게 작용하면 자격이 더 넓은 수익 기회로 열린다.",
                deficiency="편재가 약하면 정인의 자격과 명분을 외부 기회, 거래, 사업성으로 넓히는 힘이 부족하다.",
                timing="운에서 편재가 오면 자격, 학업, 문서 기반이 외부 제안, 투자, 거래 기회와 부딪힌다.",
            )
        if pattern == "indirect_resource_pattern":
            return set_lens(
                key="indirect_resource_pattern_pyeonjae_controls_resource",
                excess="편인격에서 편재가 과하면 특수 정보와 몰입이 시장성, 투자, 비정형 거래로 흔들린다. 좋게 작용하면 숨은 지식이 외부 수익으로 빠르게 열린다.",
                deficiency="편재가 약하면 편인의 특수 전문성을 외부 거래, 투자, 큰 수익 기회로 돌리는 힘이 부족하다.",
                timing="운에서 편재가 오면 특수 지식, 비공식 정보, 몰입형 기술이 투자, 거래, 외부 제안과 부딪힌다.",
            )
        return set_lens(
            key="resource_pattern_pyeonjae_controls_resource",
            excess="인성격에서 편재가 과하면 외부 거래와 시장 요구가 인성의 보호와 집중을 흔든다.",
            deficiency="편재가 약하면 전문성과 지식을 외부 기회, 거래, 수익으로 돌리는 힘이 부족하다.",
            timing="운에서 편재가 오면 공부나 자격이 시장, 거래, 투자, 외부 제안과 부딪힌다.",
        )

    if pattern == "eating_god_pattern" and acting_group == "resource":
        if acting_ten_god == "pyeon_in":
            return set_lens(
                key="pyeonin_dosik",
                excess="식신격에서 편인이 과하면 편인도식이다. 만들고 내놓아야 할 결과물이 생각, 준비, 불안정한 몰입 속에서 막힌다.",
                deficiency="편인이 너무 약하면 결과물의 품질을 검토하고 특수성을 붙드는 힘이 부족하다.",
                timing="운에서 편인이 오면 생산과 발표가 늦어지고, 공부·준비·문서 검토가 먼저 사건화된다.",
            )
        return set_lens(
            key="jeongin_controls_siksin",
            excess="식신격에서 정인이 과하면 결과물보다 자격, 문서, 명분이 앞서 생산 속도가 늦어진다.",
            deficiency="정인이 약하면 꾸준한 결과물에 정식 근거와 보호 장치가 부족하다.",
            timing="운에서 정인이 오면 기술과 상품을 문서, 자격, 공식 절차로 정리하는 일이 생긴다.",
        )

    if pattern == "hurting_officer_pattern" and acting_group == "resource":
        return set_lens(
            key="sanggwan_paein",
            excess="상관격에서 인성이 과하면 표현 속도는 늦어지지만, 알맞으면 상관패인이 되어 재주가 품격, 문서성, 전문성으로 정제된다.",
            deficiency="인성이 약하면 상관의 말과 기획이 정제되지 않아 평판 마찰이 커진다.",
            timing="운에서 인성이 오면 말, 기획, 표현물이 문서, 자격, 공식성으로 정리된다.",
        )

    if pattern == "direct_officer_pattern" and acting_group == "output":
        if acting_ten_god == "sang_gwan":
            return set_lens(
                key="sanggwan_gyeongwan",
                excess="정관격에서 상관이 과하면 상관견관이다. 능력이 있어도 말, 태도, 기획 방식이 직책과 평판을 직접 흔든다.",
                deficiency="상관이 너무 약하면 공식 책임을 실제 성과로 풀어내는 표현력과 개선력이 부족하다.",
                timing="운에서 상관이 오면 조직, 상사, 제도, 평가와 부딪히는 말과 행동이 사건화된다.",
            )
        return set_lens(
            key="siksin_controls_direct_officer",
            excess="정관격에서 식신이 과하면 직책의 긴장감이 풀려 책임 수행의 속도가 느려질 수 있다.",
            deficiency="식신이 약하면 공식 책임을 실제 성과로 증명하는 힘이 부족하다.",
            timing="운에서 식신이 오면 직책의 부담을 실무 결과물로 풀어내는 일이 생긴다.",
        )

    if pattern == "seven_killings_pattern" and acting_group == "output":
        if acting_ten_god == "sik_sin":
            return set_lens(
                key="siksin_jesal",
                excess="편관격에서 식신은 식신제살의 약이다. 다만 식신이 과하면 긴장감이 풀려 강한 책임을 끝까지 밀어붙이는 힘이 약해질 수 있다.",
                deficiency="식신이 약하면 결과물과 실무력이 부족해 편관의 압박을 실무와 기술로 제어하지 못하고 책임과 위험이 그대로 남는다.",
                timing="운에서 식신이 오면 압박 업무, 경쟁, 위기 상황을 기술과 처리력으로 제어하는 사건이 생긴다.",
                success_append="편관격에서 식신은 단순한 재주가 아니라 살을 다스리는 핵심 약이다.",
            )
        return set_lens(
            key="sanggwan_controls_seven_killings",
            excess="편관격에서 상관이 과하면 압박을 제어하기보다 권위와 정면 충돌할 수 있다.",
            deficiency="상관이 약하면 위기 상황을 돌파하는 표현력과 판단 전환이 부족하다.",
            timing="운에서 상관이 오면 경쟁 환경에서 반발, 돌파, 제도권 충돌이 드러난다.",
        )

    if pattern == "seven_killings_pattern" and acting_group == "wealth":
        return set_lens(
            key="jaesaengsal",
            excess="편관격에서 재성이 과하면 재생살이다. 돈, 욕심, 거래가 편관의 압박과 위험을 더 키운다.",
            deficiency="재성이 약하면 큰 책임을 현실 자원으로 받치는 힘이 부족하다.",
            timing="운에서 재성이 오면 돈, 계약, 투자, 거래가 압박과 책임 문제로 이어질 수 있다.",
        )

    if pattern in {"direct_officer_pattern", "seven_killings_pattern"} and acting_group == "officer":
        if pattern == "direct_officer_pattern" and acting_ten_god == "pyeon_gwan":
            return set_lens(
                key="officer_pattern_gwansal_mixed",
                excess="정관격에 편관이 섞이면 관살혼잡이다. 공식 질서에 강한 압박과 위험성이 섞여 평판과 책임이 탁해질 수 있다.",
                deficiency="편관이 약하면 돌발 상황과 경쟁 압박을 감당하는 힘은 부족하다.",
                timing="운에서 편관이 오면 직책 안에 강한 압박, 경쟁, 책임 문제가 끼어든다.",
            )
        if pattern == "seven_killings_pattern":
            return set_lens(
                key="seven_killings_overload",
                excess="편관격에서 관살이 과하면 관살과중이다. 권한보다 압박, 책임, 위험 노출이 먼저 커진다.",
                deficiency="관살이 약하면 큰 책임과 경쟁을 돌파하는 기세가 부족하다.",
                timing="운에서 관살이 오면 강한 책임, 경쟁, 평가, 압박이 동시에 올라온다.",
            )

    if pattern in {"direct_resource_pattern", "indirect_resource_pattern", "jianlu_peer_pattern", "yangren_peer_pattern"} and (
        (pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "peer")
        or (pattern in {"jianlu_peer_pattern", "yangren_peer_pattern"} and acting_group == "resource")
    ):
        if pattern == "direct_resource_pattern":
                return set_lens(
                    key="direct_resource_inbi_overload",
                    excess="정인격에서 비겁이 강하면 인비과중이다. 정식 학습, 자격, 보호 기반이 자기 기준과 결합해 보수성이 두꺼워진다. 실행보다 검토와 안정 확인이 길어진다.",
                    deficiency="비겁이 약하면 정인의 보호와 자격은 있어도 스스로 버티고 주장하는 기반이 부족하다.",
                    timing="운에서 비겁이 오면 학업, 자격, 조직 보호를 바탕으로 독립성, 자기 주장, 동료 관계가 함께 드러난다.",
                )
        if pattern == "indirect_resource_pattern":
            return set_lens(
                key="indirect_resource_inbi_overload",
                excess="편인격에서 비겁이 강하면 특수 지식과 자기 기준이 결합해 고립성과 편중이 커진다. 깊이는 생기지만 현실 협업과 외부 성과가 늦어질 수 있다.",
                deficiency="비겁이 약하면 편인의 특수 몰입을 지탱할 자기 기반과 독립성이 부족하다.",
                timing="운에서 비겁이 오면 특수 공부, 개인 연구, 비공식 기술이 독립성, 동료 갈등, 자기 주장과 함께 드러난다.",
            )
        if pattern == "jianlu_peer_pattern":
            return set_lens(
                key="jianlu_inbi_overload",
                excess="건록격에서 인성이 강하면 자기 기반이 공부와 보호 논리로 더 두꺼워진다. 안정성은 생기지만 실행과 외부 성취가 늦어질 수 있다.",
                deficiency="인성이 약하면 건록의 자기 기반을 받쳐 줄 지식, 문서, 보호 장치가 부족하다.",
                timing="운에서 인성이 오면 독립성, 직업 기반, 자격, 공부, 보호자 문제가 함께 드러난다.",
            )
        if pattern == "yangren_peer_pattern":
            return set_lens(
                key="yangren_inbi_overload",
                excess="양인격에서 인성이 강하면 강한 주도권에 보호 논리와 확신이 더해져 고집과 충돌성이 커진다. 제어가 없으면 밀어붙이는 힘이 과해진다.",
                deficiency="인성이 약하면 양인의 강한 기세를 정리할 지식, 명분, 보호 장치가 부족하다.",
                timing="운에서 인성이 오면 강한 자기 주장, 독립 문제, 보호자, 자격, 명분 싸움이 함께 드러난다.",
            )
        return set_lens(
            key="inbi_overload",
            excess="인성과 비겁이 함께 강해지면 인비과중이다. 생각, 보호, 자기 기준이 두꺼워져 현실 실행과 외부 성과가 늦어진다.",
            deficiency="인비가 약하면 자기 기반과 보호 장치가 부족해 외부 압박에 쉽게 흔들린다.",
            timing="운에서 인성이나 비겁이 오면 학업, 보호자, 자기 고집, 독립 문제가 함께 드러난다.",
        )

    if pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "output":
        if acting_ten_god == "sik_sin":
            if pattern == "eating_god_pattern":
                return set_lens(
                    key="eating_god_siksin_overload",
                    excess="식신격에서 식신이 과하면 안정된 생산이 반복과 안주로 기울 수 있다. 결과물은 꾸준하지만 변화, 책임, 수입화의 속도는 늦어진다.",
                    deficiency="식신이 약하면 식신격의 중심인 꾸준한 결과물과 안정 생산력이 부족하다.",
                    timing="운에서 식신이 오면 기술, 상품, 서비스, 반복 판매가 격의 중심 사건으로 드러난다.",
                )
            if pattern == "hurting_officer_pattern":
                return set_lens(
                    key="hurting_officer_siksin_overload",
                    excess="상관격에서 식신이 과하면 날카로운 표현과 기획이 안정 생산 쪽으로 눌린다. 재주는 부드러워지지만 돌파성과 개혁성은 둔해질 수 있다.",
                    deficiency="식신이 약하면 상관의 표현을 실제 결과물로 안정시키는 생산력이 부족하다.",
                    timing="운에서 식신이 오면 말, 기획, 홍보가 상품, 서비스, 반복 가능한 결과물로 정리된다.",
                )
            return set_lens(
                key="siksin_overload",
                excess="식신이 과하면 식상과다 중에서도 안주와 반복성이 강해진다. 결과물은 나오지만 책임, 기준, 수입화가 늦어질 수 있다.",
                deficiency="식신이 약하면 꾸준한 결과물과 안정된 생산력이 부족하다.",
                timing="운에서 식신이 오면 기술, 상품, 서비스, 반복 판매가 크게 드러난다.",
            )
        if pattern == "eating_god_pattern":
            return set_lens(
                key="eating_god_sanggwan_overload",
                excess="식신격에서 상관이 과하면 안정 생산의 격에 말, 기획, 반발성이 섞인다. 결과물은 넓어지지만 꾸준함과 신뢰가 흔들릴 수 있다.",
                deficiency="상관이 약하면 식신의 결과물을 시장에 알리고 확장하는 표현력과 기획력이 부족하다.",
                timing="운에서 상관이 오면 기술과 상품이 홍보, 발표, 기획 전환, 외부 노출로 넓어진다.",
            )
        if pattern == "hurting_officer_pattern":
            return set_lens(
                key="hurting_officer_sanggwan_overload",
                excess="상관격에서 상관이 과하면 식상과다 중에서도 말, 기획, 반발성이 강해진다. 재주는 크지만 책임, 기준, 평판과 충돌하기 쉽다.",
                deficiency="상관이 약하면 상관격의 중심인 표현력, 기획력, 판을 바꾸는 힘이 부족하다.",
                timing="운에서 상관이 오면 말, 발표, 홍보, 기획 전환, 제도권 충돌이 격의 중심 사건으로 드러난다.",
            )
        return set_lens(
            key="sanggwan_overload",
            excess="상관이 과하면 식상과다 중에서도 말, 기획, 반발성이 강해진다. 재주는 크지만 책임, 기준, 평판과 충돌하기 쉽다.",
            deficiency="상관이 약하면 자기 재주를 시장에 드러내고 판을 바꾸는 힘이 부족하다.",
            timing="운에서 상관이 오면 말, 발표, 홍보, 기획 전환, 제도권 충돌이 크게 드러난다.",
        )

    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "wealth":
        if acting_ten_god == "jeong_jae":
            if pattern == "direct_wealth_pattern":
                return set_lens(
                    key="direct_wealth_jeongjae_overload",
                    excess="정재격에서 정재가 과하면 재다신약 여부를 반드시 본다. 생활 재정과 소유 기준은 강해지지만 일간이 감당하지 못하면 관리 부담과 책임이 커진다.",
                    deficiency="정재가 약하면 정재격의 중심인 고정 수입, 소유권, 생활 재정의 실체가 약하다.",
                    timing="운에서 정재가 오면 고정 수입, 자산 소유, 정산, 생활 재정이 격의 중심 사건으로 커진다.",
                )
            if pattern == "indirect_wealth_pattern":
                return set_lens(
                    key="indirect_wealth_jeongjae_overload",
                    excess="편재격에서 정재가 과하면 외부 거래의 유동성이 생활 재정과 소유 기준에 묶인다. 안정성은 생기지만 확장 속도는 둔해질 수 있다.",
                    deficiency="정재가 약하면 편재의 외부 기회를 고정 수입과 소유 자산으로 굳히는 힘이 부족하다.",
                    timing="운에서 정재가 오면 외부 수익이 고정 수입, 정산, 소유권, 생활 재정으로 정리된다.",
                )
            return set_lens(
                key="jeongjae_overload",
                excess="정재가 과하면 재다신약 여부를 반드시 본다. 생활 재정과 소유 기준은 강해지지만 일간이 감당하지 못하면 관리 부담이 커진다.",
                deficiency="정재가 약하면 고정 수입, 소유권, 생활 재정의 실체가 약하다.",
                timing="운에서 정재가 오면 고정 수입, 자산 소유, 정산, 생활 재정이 직접 커진다.",
            )
        if pattern == "direct_wealth_pattern":
            return set_lens(
                key="direct_wealth_pyeonjae_overload",
                excess="정재격에서 편재가 과하면 안정 재정 위에 외부 거래와 확장 욕구가 붙는다. 소유 기준이 흔들리면 회수 지연과 지출 확대가 커진다.",
                deficiency="편재가 약하면 정재의 안정성은 있어도 외부 기회, 거래처, 투자 자금으로 넓히는 힘이 부족하다.",
                timing="운에서 편재가 오면 고정 수입과 생활 재정 위에 외부 거래, 투자 제안, 사업 확장이 붙는다.",
            )
        if pattern == "indirect_wealth_pattern":
            return set_lens(
                key="indirect_wealth_pyeonjae_overload",
                excess="편재격에서 편재가 과하면 재다신약 여부를 반드시 본다. 거래와 확장은 커지지만 일간이 감당하지 못하면 회수 지연, 투자 손실, 과확장이 커진다.",
                deficiency="편재가 약하면 편재격의 중심인 외부 기회, 거래처, 투자 자금, 확장성을 잡는 힘이 부족하다.",
                timing="운에서 편재가 오면 외부 거래, 투자 제안, 유동 자금, 사업 확장이 격의 중심 사건으로 커진다.",
            )
        return set_lens(
            key="pyeonjae_overload",
            excess="편재가 과하면 재다신약 여부를 반드시 본다. 거래와 확장은 커지지만 일간이 감당하지 못하면 회수 지연과 손실 위험이 커진다.",
            deficiency="편재가 약하면 외부 기회, 거래처, 투자 자금, 확장성을 잡는 힘이 부족하다.",
                timing="운에서 편재가 오면 외부 거래, 투자 제안, 유동 자금, 사업 확장이 직접 커진다.",
        )

    if pattern == "direct_officer_pattern" and acting_group == "wealth":
        if acting_ten_god == "jeong_jae":
            return set_lens(
                key="direct_officer_jeongjae_saenggwan",
                excess="정관격에서 정재가 과하면 재생관이 지나쳐 재물과 생활 책임이 직책 부담으로 굳어진다.",
                deficiency="정재가 약하면 직책과 명예를 받쳐 줄 현실 재정, 신용, 생활 기반이 부족하다.",
                timing="운에서 정재가 오면 직책, 평가, 신용 문제가 고정 수입, 정산, 생활 기반과 함께 움직인다.",
                success_append="정관격의 정재는 직책을 현실 기반으로 받치는 재생관의 근거다.",
            )
        return set_lens(
            key="direct_officer_pyeonjae_saenggwan",
            excess="정관격에서 편재가 과하면 외부 거래와 큰돈이 관을 생해 책임 범위가 넓어진다. 과하면 평판보다 부담이 커진다.",
            deficiency="편재가 약하면 직책은 있어도 외부 자원, 거래처, 사업적 확장으로 이어지는 힘이 부족하다.",
            timing="운에서 편재가 오면 직책과 평판이 거래, 외부 자금, 사업 제안과 연결된다.",
        )

    if pattern == "direct_officer_pattern" and acting_group == "resource":
        if acting_ten_god == "jeong_in":
            return set_lens(
                key="direct_officer_jeongin_gwanin",
                excess="정관격에서 정인이 과하면 관인상생이 지나쳐 직책보다 문서, 절차, 명분이 무거워진다.",
                deficiency="정인이 약하면 직책을 안정시킬 자격, 문서, 보호 기반이 부족하다.",
                timing="운에서 정인이 오면 승진, 평가, 직책 문제가 자격, 문서, 학업, 공식 절차와 함께 움직인다.",
                success_append="정관격의 정인은 관인상생의 정식 명분이다.",
            )
        return set_lens(
            key="direct_officer_pyeonin_gwanin",
            excess="정관격에서 편인이 과하면 직책이 특수한 지식과 비정형 판단으로 기울어 공식성이 탁해질 수 있다.",
            deficiency="편인이 약하면 직책 뒤에 숨은 전문성, 특수 자료, 비정형 문제 대응력이 부족하다.",
            timing="운에서 편인이 오면 직책과 평가가 특수 공부, 내부 문서, 비공식 정보와 연결된다.",
        )

    if pattern == "direct_officer_pattern" and acting_ten_god == "jeong_gwan":
        return set_lens(
            key="direct_officer_center",
            excess="정관격에서 정관이 과하면 공식 책임과 평판 의식이 지나쳐 선택이 경직된다.",
            deficiency="정관이 약하면 직책, 규칙, 사회적 신뢰의 중심이 약해져 자리가 흔들린다.",
            timing="운에서 정관이 오면 직책, 평가, 공식 책임, 명예 문제가 정면으로 올라온다.",
        )

    if pattern == "seven_killings_pattern" and acting_group == "resource":
        if acting_ten_god == "jeong_in":
            return set_lens(
                key="seven_killings_jeongin_salin",
                excess="편관격에서 정인이 과하면 살인상생이 문서와 보호에 머물러 압박을 실제 권한으로 바꾸는 속도가 늦어진다.",
                deficiency="정인이 약하면 편관의 압박을 받아낼 자격, 문서, 보호 장치가 부족하다.",
                timing="운에서 정인이 오면 강한 책임과 압박이 자격, 문서, 시험, 보호 장치로 전환된다.",
                success_append="편관격의 정인은 살을 보호 장치로 흡수하는 살인상생의 안정축이다.",
            )
        return set_lens(
            key="seven_killings_pyeonin_salin",
            excess="편관격에서 편인이 과하면 압박이 특수 몰입과 고립된 판단으로 흡수되어 불안정한 전문성이 강해진다.",
            deficiency="편인이 약하면 위기 상황을 특수 지식과 직관으로 처리하는 힘이 부족하다.",
            timing="운에서 편인이 오면 위기, 경쟁, 강한 책임이 특수 공부와 비정형 기술로 연결된다.",
        )

    if pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "officer":
        if pattern == "direct_resource_pattern" and acting_ten_god == "jeong_gwan":
            return set_lens(
                key="resource_pattern_jeonggwan_gwanin",
                excess="인수격에서 정관이 과하면 관인상생이 지나쳐 공부와 자격이 책임과 절차 부담으로 무거워진다.",
                deficiency="정관이 약하면 자격과 문서가 사회적 직책, 평가, 공식 신뢰로 이어지는 힘이 부족하다.",
                timing="운에서 정관이 오면 자격, 문서, 학업 기반이 직책과 평가로 연결된다.",
                success_append="인수격의 정관은 인성을 사회적 명분으로 세우는 관인상생의 축이다.",
            )
        if acting_ten_god == "pyeon_gwan":
            return set_lens(
                key="resource_pattern_pyeongwan_salin",
                excess="인성격에서 편관이 과하면 살인상생이 아니라 책임과 압박이 인성 기반을 소모하는 쪽으로 흐를 수 있다.",
                deficiency="편관이 약하면 자격과 전문성을 강한 책임, 경쟁, 권한으로 끌어올리는 힘이 부족하다.",
                timing="운에서 편관이 오면 공부, 자격, 문서 기반이 경쟁, 압박, 강한 책임과 연결된다.",
            )
        return set_lens(
            key="resource_pattern_jeonggwan_supports_resource",
            excess="편인격에서 정관이 과하면 비정형 전문성이 제도와 절차 안에 묶여 답답해질 수 있다.",
            deficiency="정관이 약하면 특수 지식이 공식 평가와 신뢰로 인정받는 힘이 부족하다.",
            timing="운에서 정관이 오면 특수 지식과 몰입이 직책, 평가, 제도권 신뢰로 연결된다.",
        )

    if pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "wealth":
        if pattern == "eating_god_pattern" and acting_ten_god == "jeong_jae":
            return set_lens(
                key="eating_god_jeongjae_siksin_saengjae",
                excess="식신격에서 정재가 과하면 결과물이 생활 재정에 묶여 안정은 생기지만 확장 속도는 느려진다.",
                deficiency="정재가 약하면 꾸준한 결과물이 고정 수입과 소유로 굳어지는 힘이 부족하다.",
                timing="운에서 정재가 오면 기술, 상품, 서비스가 고정 수입과 정산 구조로 연결된다.",
                success_append="식신격의 정재는 식신생재가 안정 수입으로 굳는 자리다.",
            )
        if pattern == "eating_god_pattern":
            return set_lens(
                key="eating_god_pyeonjae_siksin_saengjae",
                excess="식신격에서 편재가 과하면 결과물은 돈이 되지만 외부 거래와 확장이 빨라져 회수 관리가 중요해진다.",
                deficiency="편재가 약하면 꾸준한 결과물을 외부 거래, 판매, 사업 기회로 넓히는 힘이 부족하다.",
                timing="운에서 편재가 오면 기술과 상품이 외부 거래, 영업, 투자 기회로 연결된다.",
            )
        if acting_ten_god == "jeong_jae":
            return set_lens(
                key="hurting_officer_jeongjae_sanggwan_saengjae",
                excess="상관격에서 정재가 과하면 표현과 기획이 돈으로 바뀌되 안정 재정의 기준에 묶여 돌파성이 둔해진다.",
                deficiency="정재가 약하면 재주와 기획이 고정 수입과 소유로 굳어지는 힘이 부족하다.",
                timing="운에서 정재가 오면 말, 기획, 홍보가 정산, 고정 수입, 생활 재정으로 연결된다.",
            )
        return set_lens(
            key="hurting_officer_pyeonjae_sanggwan_saengjae",
            excess="상관격에서 편재가 과하면 상관생재의 시장성은 커지지만 말과 확장이 앞서 회수와 계약이 흔들릴 수 있다.",
            deficiency="편재가 약하면 표현과 기획이 외부 거래와 큰 수입으로 넓어지는 힘이 부족하다.",
            timing="운에서 편재가 오면 말, 콘텐츠, 영업, 기획이 외부 거래와 사업 확장으로 연결된다.",
            success_append="상관격의 편재는 재주가 시장성으로 전환되는 대표 작용이다.",
        )

    if pattern in {"jianlu_peer_pattern", "yangren_peer_pattern"}:
        pattern_is_yangren = pattern == "yangren_peer_pattern"
        if acting_group == "peer":
            if acting_ten_god == "geob_jae":
                return set_lens(
                    key=f"{pattern}_geobjae_center",
                    excess=("양인격에서 겁재가 과하면 양인의 기세가 분탈과 충돌로 드러난다." if pattern_is_yangren else "건록격에서 겁재가 과하면 자립성보다 경쟁, 지분, 몫 다툼이 먼저 강해진다."),
                    deficiency=("겁재가 약하면 강하게 밀고 나가야 할 때 주도권을 놓친다." if pattern_is_yangren else "겁재가 약하면 동등한 경쟁에서 밀리고 자기 몫을 강하게 확보하기 어렵다."),
                    timing=("운에서 겁재가 오면 경쟁자, 동업 지분, 강한 주도권 충돌이 사건화된다." if pattern_is_yangren else "운에서 겁재가 오면 독립, 경쟁, 지분 조정, 주변 사람과의 몫 문제가 드러난다."),
                )
            return set_lens(
                key=f"{pattern}_bigyeon_center",
                excess=("양인격에서 비견이 과하면 강한 자기 기준이 충돌성을 키운다." if pattern_is_yangren else "건록격에서 비견이 과하면 자기 기반은 강해지나 고집과 독자성이 지나쳐 협의가 늦어진다."),
                deficiency=("비견이 약하면 양인의 기세를 오래 유지할 자기 기반이 부족하다." if pattern_is_yangren else "비견이 약하면 자립 기반과 자기 결정을 오래 버티는 힘이 약하다."),
                timing=("운에서 비견이 오면 독립, 자기 결정, 경쟁 환경이 강하게 드러난다." if pattern_is_yangren else "운에서 비견이 오면 독립, 자기 기반, 동등한 경쟁 문제가 드러난다."),
            )
        if acting_group == "output":
            if acting_ten_god == "sang_gwan":
                return set_lens(
                    key=f"{pattern}_sanggwan_release",
                    excess=("양인격에서 상관이 과하면 기세가 말, 반발, 제도권 충돌로 빠져나간다." if pattern_is_yangren else "건록격에서 상관이 과하면 강한 자기 기운이 표현과 반발로 빠져나가 평판 마찰을 만들 수 있다."),
                    deficiency=("상관이 약하면 강한 기세를 돌파성과 기획으로 배출하지 못한다." if pattern_is_yangren else "상관이 약하면 강한 자기 기반을 밖으로 드러내는 표현력과 기획력이 부족하다."),
                    timing=("운에서 상관이 오면 반발, 기획 전환, 제도권 충돌이 강하게 나타난다." if pattern_is_yangren else "운에서 상관이 오면 말, 발표, 기획, 자기 표현이 강해진다."),
                )
            return set_lens(
                key=f"{pattern}_siksin_release",
                excess=("양인격에서 식신이 과하면 기세가 누그러져 강한 결단력이 느슨해질 수 있다." if pattern_is_yangren else "건록격에서 식신이 과하면 안정된 생산은 생기지만 독립적 추진의 속도는 늦어진다."),
                deficiency=("식신이 약하면 양인의 강한 기세를 실무와 결과물로 빼내지 못한다." if pattern_is_yangren else "식신이 약하면 강한 자기 기반을 안정된 결과물로 전환하지 못한다."),
                timing=("운에서 식신이 오면 강한 경쟁성이 실무 처리와 결과물로 배출된다." if pattern_is_yangren else "운에서 식신이 오면 기술, 결과물, 반복 가능한 성과가 드러난다."),
            )
        if acting_group == "wealth":
            if acting_ten_god == "pyeon_jae":
                return set_lens(
                    key=f"{pattern}_pyeonjae_wealth_control",
                    excess=("양인격에서 편재가 과하면 강한 주도권이 외부 돈과 부딪혀 과확장과 쟁재가 된다." if pattern_is_yangren else "건록격에서 편재가 과하면 독립성이 외부 거래와 확장 욕구를 직접 장악하려 한다."),
                    deficiency=("편재가 약하면 강한 주도권을 외부 거래와 사업 기회로 넓히는 힘이 부족하다." if pattern_is_yangren else "편재가 약하면 자립 기반은 있어도 외부 돈과 거래를 잡는 감각이 부족하다."),
                    timing=("운에서 편재가 오면 사업 제안, 투자, 외부 거래, 지분 경쟁이 강하게 드러난다." if pattern_is_yangren else "운에서 편재가 오면 외부 거래, 투자, 활동 자금 문제가 드러난다."),
                )
            return set_lens(
                key=f"{pattern}_jeongjae_wealth_control",
                excess=("양인격에서 정재가 과하면 소유권과 생활 재정을 두고 주도권 충돌이 생긴다." if pattern_is_yangren else "건록격에서 정재가 과하면 자기 기준으로 돈과 소유를 붙들어 변화 대응이 늦어진다."),
                deficiency=("정재가 약하면 강한 기세를 안정 재정과 소유로 굳히지 못한다." if pattern_is_yangren else "정재가 약하면 자립성은 있어도 고정 수입과 생활 재정의 기반이 약하다."),
                timing=("운에서 정재가 오면 소유권, 고정 수입, 생활 재정, 지분 문제가 현실화된다." if pattern_is_yangren else "운에서 정재가 오면 고정 수입, 자산 소유, 정산 문제가 드러난다."),
            )
        if acting_group == "officer":
            if acting_ten_god == "pyeon_gwan":
                return set_lens(
                    key=f"{pattern}_pyeongwan_regulates_peer",
                    excess=("양인격에서 편관이 과하면 제어가 아니라 강한 압박과 위험 부담으로 나타난다." if pattern_is_yangren else "건록격에서 편관이 과하면 독립성을 지나치게 압박해 긴장과 책임 부담이 커진다."),
                    deficiency=("편관이 약하면 양인의 기세를 제어할 강한 책임과 권한이 부족하다." if pattern_is_yangren else "편관이 약하면 강한 자기 기준을 사회적 책임으로 묶는 힘이 부족하다."),
                    timing=("운에서 편관이 오면 경쟁, 압박, 강한 책임, 권한 문제가 드러난다." if pattern_is_yangren else "운에서 편관이 오면 독립성과 책임 사이의 긴장이 커진다."),
                )
            return set_lens(
                key=f"{pattern}_jeonggwan_regulates_peer",
                excess=("양인격에서 정관이 과하면 강한 기세가 규칙과 평판 부담에 눌릴 수 있다." if pattern_is_yangren else "건록격에서 정관이 과하면 독립성이 제도와 평판 부담에 묶인다."),
                deficiency=("정관이 약하면 양인의 기세를 공식 책임과 질서로 묶지 못한다." if pattern_is_yangren else "정관이 약하면 자립 기반은 강해도 사회적 자리와 평가 기준이 약하다."),
                timing=("운에서 정관이 오면 주도권이 직책, 평가, 공식 책임으로 정리된다." if pattern_is_yangren else "운에서 정관이 오면 독립성이 직책, 평가, 제도권 책임과 연결된다."),
            )

    if pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "peer":
        if acting_ten_god == "geob_jae":
            return set_lens(
                key=f"{pattern}_geobjae_feeds_output",
                excess=("상관격에서 겁재가 과하면 표현 기반이 경쟁심과 결합해 말과 행동이 거칠어진다." if pattern == "hurting_officer_pattern" else "식신격에서 겁재가 과하면 생산 기반보다 사람과 몫 문제가 먼저 커질 수 있다."),
                deficiency=("겁재가 약하면 표현과 결과물을 밀어붙일 경쟁력과 추진력이 부족하다." if pattern == "hurting_officer_pattern" else "겁재가 약하면 결과물을 밀어주는 동료성, 추진력, 경쟁력이 부족하다."),
                timing=("운에서 겁재가 오면 표현, 기획, 경쟁자, 동업 문제가 함께 드러난다." if pattern == "hurting_officer_pattern" else "운에서 겁재가 오면 생산 과정에 동료, 경쟁자, 몫 문제가 끼어든다."),
            )
        return set_lens(
            key=f"{pattern}_bigyeon_feeds_output",
            excess=("상관격에서 비견이 과하면 자기 색깔이 강해져 표현이 독단적으로 흐를 수 있다." if pattern == "hurting_officer_pattern" else "식신격에서 비견이 과하면 생산 기반은 두터워지나 자기 방식에 머물러 변화가 늦다."),
            deficiency=("비견이 약하면 자기 색깔을 지키며 표현을 이어가는 힘이 부족하다." if pattern == "hurting_officer_pattern" else "비견이 약하면 꾸준한 생산을 받쳐 줄 자기 기반이 부족하다."),
            timing=("운에서 비견이 오면 자기 표현, 독립 작업, 동등한 경쟁이 드러난다." if pattern == "hurting_officer_pattern" else "운에서 비견이 오면 자기 기술, 독립 생산, 반복 작업 기반이 드러난다."),
        )

    if pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "officer":
        if pattern == "eating_god_pattern" and acting_ten_god == "pyeon_gwan":
            return set_lens(
                key="eating_god_pyeongwan_jesal_target",
                excess="식신격에서 편관이 과하면 식신제살의 대상이 커진다. 결과물로 감당할 책임보다 압박이 앞설 수 있다.",
                deficiency="편관이 약하면 결과물이 직업적 긴장과 사회적 책임으로 올라가는 계기가 부족하다.",
                timing="운에서 편관이 오면 생산물과 기술이 압박 업무, 경쟁, 강한 책임과 연결된다.",
            )
        if pattern == "eating_god_pattern":
            return set_lens(
                key="eating_god_jeonggwan_responsibility",
                excess="식신격에서 정관이 과하면 결과물이 직책과 절차에 묶여 편안한 생산성이 줄어든다.",
                deficiency="정관이 약하면 결과물이 공식 평가, 직책, 책임으로 인정받는 힘이 부족하다.",
                timing="운에서 정관이 오면 만든 결과물이 평가, 직책, 공식 책임으로 이어진다.",
            )
        if acting_ten_god == "jeong_gwan":
            return set_lens(
                key="hurting_officer_jeonggwan_gyeongwan",
                excess="상관격에서 정관이 강하게 들어오면 상관견관의 긴장이 뚜렷해진다. 표현과 제도권 평가가 정면으로 부딪힌다.",
                deficiency="정관이 약하면 상관의 재주를 공식 평가와 직책으로 묶는 힘이 부족하다.",
                timing="운에서 정관이 오면 표현, 말, 기획이 조직 평가와 직책 문제를 건드린다.",
            )
        return set_lens(
            key="hurting_officer_pyeongwan_conflict",
            excess="상관격에서 편관이 강하면 반발성과 압박이 맞붙어 경쟁, 위험, 권위 충돌이 커진다.",
            deficiency="편관이 약하면 상관의 돌파성이 강한 책임과 긴장감으로 이어지는 힘이 부족하다.",
            timing="운에서 편관이 오면 말과 기획이 압박 업무, 경쟁, 강한 책임과 부딪힌다.",
        )

    if pattern in {"direct_officer_pattern", "seven_killings_pattern"} and acting_group == "peer":
        if pattern == "direct_officer_pattern":
            if acting_ten_god == "geob_jae":
                return set_lens(
                    key="direct_officer_geobjae_shakes_order",
                    excess="정관격에서 겁재가 과하면 공식 질서에 경쟁자, 동료, 지분 문제가 끼어 평판이 흔들린다.",
                    deficiency="겁재가 약하면 직책 안에서 경쟁을 돌파하고 주도권을 확보하는 힘이 부족하다.",
                    timing="운에서 겁재가 오면 조직 안 경쟁, 동료 갈등, 책임과 몫 문제가 드러난다.",
                )
            return set_lens(
                key="direct_officer_bigyeon_shakes_order",
                excess="정관격에서 비견이 과하면 자기 주장과 공식 질서가 맞부딪혀 유연성이 떨어진다.",
                deficiency="비견이 약하면 직책 안에서 자기 기준을 지키는 힘이 부족하다.",
                timing="운에서 비견이 오면 직책과 자기 입장 사이의 조율 문제가 드러난다.",
            )
        if acting_ten_god == "geob_jae":
            return set_lens(
                key="seven_killings_geobjae_pressure",
                excess="편관격에서 겁재가 과하면 압박과 경쟁심이 맞붙어 충돌과 위험 부담이 커진다.",
                deficiency="겁재가 약하면 강한 경쟁 상황에서 밀어붙이는 힘이 부족하다.",
                timing="운에서 겁재가 오면 경쟁자, 동업자, 위기 상황 속 주도권 문제가 드러난다.",
            )
        return set_lens(
            key="seven_killings_bigyeon_pressure",
            excess="편관격에서 비견이 과하면 자기 주장과 압박이 맞붙어 긴장이 오래 간다.",
            deficiency="비견이 약하면 편관의 압박 속에서 자기 기준을 지키기 어렵다.",
            timing="운에서 비견이 오면 압박 상황에서 독립 판단과 자기 방어가 중요해진다.",
        )

    if pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "output":
        if pattern == "direct_resource_pattern":
            if acting_ten_god == "sik_sin":
                return set_lens(
                    key="direct_resource_siksin_result",
                    excess="인수격에서 식신이 과하면 배운 것을 결과물로 내놓되 문서와 명분의 안정성이 느슨해질 수 있다.",
                    deficiency="식신이 약하면 자격과 공부가 실제 결과물로 나오지 못한다.",
                    timing="운에서 식신이 오면 학업, 자격, 문서 기반이 기술, 상품, 결과물로 드러난다.",
                )
            return set_lens(
                key="direct_resource_sanggwan_result",
                excess="인수격에서 상관이 과하면 문서와 명분을 넘어 표현과 반발성이 강해져 자격 기반을 흔들 수 있다.",
                deficiency="상관이 약하면 배운 것을 시장에 드러내고 개선하는 힘이 부족하다.",
                timing="운에서 상관이 오면 자격과 공부가 말, 발표, 기획, 제도권 충돌로 드러난다.",
            )
        if acting_ten_god == "sik_sin":
            return set_lens(
                key="indirect_resource_siksin_result",
                excess="편인격에서 식신이 과하면 특수 지식과 몰입이 결과물로 나오지만 깊은 연구의 지속성이 약해질 수 있다.",
                deficiency="식신이 약하면 특수 지식이 상품, 기술, 결과물로 나오지 못한다.",
                timing="운에서 식신이 오면 특수 지식과 몰입이 기술, 서비스, 결과물로 현실화된다.",
            )
        return set_lens(
            key="indirect_resource_sanggwan_result",
            excess="편인격에서 상관이 과하면 독특한 판단이 말과 기획으로 강하게 드러나지만 산만해질 수 있다.",
            deficiency="상관이 약하면 특수한 이해를 밖으로 꺼내 설득하고 시장화하는 힘이 부족하다.",
            timing="운에서 상관이 오면 특수 지식이 발표, 콘텐츠, 기획, 비정형 성과로 드러난다.",
        )

    if pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "resource":
        if acting_ten_god == "jeong_in":
            return set_lens(
                key=f"{pattern}_jeongin_center",
                excess=("정인격에서 정인이 과하면 인성 과다로 명분, 보호, 학습이 실행을 대신한다." if pattern == "direct_resource_pattern" else "편인격에서 정인이 과하면 특수한 판단이 정식 문서와 보호 논리에 묶여 속도가 늦어진다."),
                deficiency=("정인이 약하면 정식 자격, 문서, 보호 기반이 부족하다." if pattern == "direct_resource_pattern" else "정인이 약하면 편인의 특수성을 정식 명분과 문서로 안정시키는 힘이 부족하다."),
                timing=("운에서 정인이 오면 학업, 문서, 자격, 보호 장치가 강하게 드러난다." if pattern == "direct_resource_pattern" else "운에서 정인이 오면 특수 지식이 정식 자격, 문서, 보호 체계와 연결된다."),
            )
        return set_lens(
            key=f"{pattern}_pyeonin_center",
            excess=("정인격에서 편인이 과하면 정식 학습 안에 비정형 몰입이 섞여 판단이 편중될 수 있다." if pattern == "direct_resource_pattern" else "편인격에서 편인이 과하면 편인 과다로 고립, 도식, 비현실적 판단이 강해진다."),
            deficiency=("편인이 약하면 정식 문서 너머의 특수 문제와 비정형 자료를 읽는 힘이 부족하다." if pattern == "direct_resource_pattern" else "편인이 약하면 특수 전문성과 깊은 몰입이 부족하다."),
            timing=("운에서 편인이 오면 특수 공부, 비공식 자료, 고립된 준비가 드러난다." if pattern == "direct_resource_pattern" else "운에서 편인이 오면 특수 지식, 고립된 몰입, 비정형 판단이 강하게 드러난다."),
        )

    return lens


def _single_classical_action_tags(
    *,
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
    critical_key: str,
) -> list[str]:
    tags: list[str] = []
    pattern_group = TEN_GOD_GROUPS[PATTERN_CENTER_BY_PATTERN[pattern]]

    def add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    if acting_group == pattern_group:
        same_group_tags = {
            "peer": "bigeop_same_group",
            "output": "siksang_same_group",
            "wealth": "wealth_same_group",
            "officer": "gwanseong_same_group",
            "resource": "inseong_same_group",
        }
        add(same_group_tags[acting_group])

    if pattern_group == "peer" and acting_group == "output":
        add("bigeop_generates_siksang")
    if pattern_group == "peer" and acting_group == "wealth":
        add("bigeop_controls_wealth")
        add("bigeop_jaengjae")
    if pattern_group == "peer" and acting_group == "officer":
        add("gwanseong_controls_bigeop")
    if pattern_group == "peer" and acting_group == "resource":
        add("inseong_generates_bigeop")

    if pattern_group == "output" and acting_group == "peer":
        add("bigeop_generates_siksang")
    if pattern_group == "output" and acting_group == "officer":
        add("siksang_controls_gwanseong")

    if pattern_group == "wealth" and acting_group == "peer":
        add("bigeop_controls_wealth")
    if pattern_group == "wealth" and acting_group == "officer":
        add("jaeseong_generates_gwanseong")
    if pattern_group == "wealth" and acting_group == "resource":
        add("wealth_controls_resource")

    if pattern_group == "officer" and acting_group == "peer":
        add("gwanseong_controls_bigeop")
    if pattern_group == "officer" and acting_group == "output":
        add("siksang_controls_gwanseong")
    if pattern_group == "officer" and acting_group == "resource":
        add("gwanseong_generates_inseong")

    if pattern_group == "resource" and acting_group == "peer":
        add("inseong_generates_bigeop")
    if pattern_group == "resource" and acting_group == "output":
        add("inseong_controls_output")
        add("inseong_dosik")
    if pattern_group == "resource" and acting_group == "wealth":
        add("wealth_controls_resource")

    if action_nature in {"식신생재", "상관생재"} or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "output"
    ) or (
        pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "wealth"
    ):
        add("siksang_saengjae")
    if action_nature in {"재생관", "정재생관", "편재생관"} or (
        pattern == "direct_officer_pattern" and acting_group == "wealth"
    ) or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_ten_god == "jeong_gwan"
    ):
        add("jaesaenggwan")
    if action_nature in {"재생살"} or (
        pattern == "seven_killings_pattern" and acting_group == "wealth"
    ) or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_ten_god == "pyeon_gwan"
    ):
        add("jaesaengsal")
    if action_nature == "관인상생" or (
        pattern == "direct_officer_pattern" and acting_group == "resource"
    ) or (
        pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_ten_god == "jeong_gwan"
    ):
        add("gwanin_sangsaeng")
    if action_nature == "살인상생" or (
        pattern == "seven_killings_pattern" and acting_group == "resource"
    ) or (
        pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_ten_god == "pyeon_gwan"
    ):
        add("salin_sangsaeng")
    if "siksin_jesal" in critical_key or "jesal" in critical_key or (
        pattern == "seven_killings_pattern" and acting_ten_god == "sik_sin"
    ):
        add("siksin_jesal")
    if "sanggwan_gyeongwan" in critical_key or (
        pattern == "direct_officer_pattern" and acting_ten_god == "sang_gwan"
    ) or (
        pattern == "hurting_officer_pattern" and acting_ten_god == "jeong_gwan"
    ):
        add("sanggwan_gyeongwan")
    if "재극" in action_nature or "controls_resource" in critical_key or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "resource"
    ) or (
        pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "wealth"
    ):
        add("jaegeukin")
    if action_nature == "쟁재" or "jaengjae" in critical_key or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "peer"
    ):
        add("bigeop_jaengjae")
    if action_nature in {"편인도식", "정인제식", "도식"} or "dosik" in critical_key or (
        pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "resource"
    ):
        add("inseong_dosik")
    if "gwansal_mixed" in critical_key or (
        pattern == "direct_officer_pattern" and acting_ten_god == "pyeon_gwan"
    ) or (
        pattern == "seven_killings_pattern" and acting_ten_god == "jeong_gwan"
    ):
        add("gwansal_honhap")
    if "inbi_overload" in critical_key or (
        pattern in {"direct_resource_pattern", "indirect_resource_pattern"} and acting_group == "peer"
    ) or (
        pattern in {"jianlu_peer_pattern", "yangren_peer_pattern"} and acting_group == "resource"
    ):
        add("inbi_overload")
    if "siksin_overload" in critical_key or "sanggwan_overload" in critical_key or (
        pattern in {"eating_god_pattern", "hurting_officer_pattern"} and acting_group == "output"
    ):
        add("siksang_overload")
    if "jae_overload" in critical_key or (
        pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and acting_group == "wealth"
    ):
        add("jaeda_sinyak_risk")
    if "seven_killings_overload" in critical_key or (
        pattern == "seven_killings_pattern" and acting_group == "officer"
    ):
        add("gwansal_overload")

    if not tags:
        add("gyeokguk_specific_adjustment")
    return tags


def _activation_context(presence_state: str, month_fit_state: str) -> str:
    if presence_state == "visible_and_rooted":
        base = "투출과 통근이 함께 있어 현실 작용이 분명하다."
    elif presence_state == "visible":
        base = "천간에 드러나 밖으로 보이는 작용이다."
    elif presence_state == "rooted_or_hidden":
        base = "지지와 지장간에 깔려 생활 조건에서 작용한다."
    elif presence_state == "weakly_present":
        base = "약하게 존재하므로 운에서 자극될 때 해석 비중이 커진다."
    else:
        base = "원국에서 직접 활성화되지 않는다."
    if month_fit_state in {"supports_month_command", "usable_by_month_command"}:
        return f"{base} 월령 기준에서도 쓸 수 있는 작용이다."
    if month_fit_state in {"harms_month_command", "burdensome_by_month_command"}:
        return f"{base} 다만 월령 기준에서는 부담 또는 파격 가능성을 함께 본다."
    if month_fit_state == "mixed_by_month_command":
        return f"{base} 월령 기준에서는 성패가 강약과 위치에 따라 갈린다."
    return base


def _role_element(day_element: str, group: str) -> str:
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


def _day_master_strength_context(element_profile: ElementProfile | None, acting_group: str) -> dict[str, object]:
    if element_profile is None:
        return {"label": "일간 강약 미평가", "score_delta": 0, "basis_codes": [], "counter_signals": []}
    strength = str(element_profile.day_master_strength)
    weak = {"weak", "very_weak"}
    strong = {"strong", "very_strong"}
    if strength in weak:
        if acting_group in {"peer", "resource"}:
            return {
                "label": "약한 일간을 보강하는 작용",
                "score_delta": 7,
                "basis_codes": [f"gyeokguk_action_strength_{strength}_actor_supports_day_master"],
                "counter_signals": [],
            }
        return {
            "label": "약한 일간에는 부담을 키울 수 있는 작용",
            "score_delta": -7,
            "basis_codes": [],
            "counter_signals": [f"gyeokguk_action_strength_{strength}_actor_burdens_day_master"],
        }
    if strength in strong:
        if acting_group in {"output", "wealth", "officer"}:
            return {
                "label": "강한 일간을 배출·제어하는 작용",
                "score_delta": 7,
                "basis_codes": [f"gyeokguk_action_strength_{strength}_actor_regulates_day_master"],
                "counter_signals": [],
            }
        return {
            "label": "강한 일간을 더 키워 편중시킬 수 있는 작용",
            "score_delta": -5,
            "basis_codes": [],
            "counter_signals": [f"gyeokguk_action_strength_{strength}_actor_overfeeds_day_master"],
        }
    return {
        "label": "일간 강약은 중립에 가까워 월령과 위치 판단을 우선한다.",
        "score_delta": 0,
        "basis_codes": [f"gyeokguk_action_strength_{strength}_balanced_context"],
        "counter_signals": [],
    }


def _climate_context(element_profile: ElementProfile | None, acting_group: str) -> dict[str, object]:
    if element_profile is None:
        return {"label": "조후 미평가", "score_delta": 0, "basis_codes": [], "counter_signals": []}
    acting_element = _role_element(element_profile.day_master_element, acting_group)
    if not acting_element:
        return {"label": "조후 작용 미확정", "score_delta": 0, "basis_codes": [], "counter_signals": []}
    acting_element_label = ELEMENT_LABELS.get(acting_element, acting_element)
    if acting_element in element_profile.climate_needs:
        return {
            "label": f"조후상 필요한 {acting_element_label} 기운을 보충하는 작용",
            "score_delta": 8,
            "basis_codes": [f"gyeokguk_action_climate_need_{acting_element}"],
            "counter_signals": [],
        }
    if acting_element in element_profile.useful_elements:
        return {
            "label": f"구조상 쓸 수 있는 {acting_element_label} 기운으로 작용",
            "score_delta": 4,
            "basis_codes": [f"gyeokguk_action_useful_element_{acting_element}"],
            "counter_signals": [],
        }
    if acting_element in element_profile.caution_elements:
        return {
            "label": f"구조상 부담이 될 수 있는 {acting_element_label} 기운으로 작용",
            "score_delta": -5,
            "basis_codes": [],
            "counter_signals": [f"gyeokguk_action_caution_element_{acting_element}"],
        }
    return {
        "label": f"{acting_element_label} 기운은 조후상 결정적 보정 없이 작용",
        "score_delta": 0,
        "basis_codes": [f"gyeokguk_action_neutral_element_{acting_element}"],
        "counter_signals": [],
    }


def _positions_for_ten_god(
    position_signals: dict[str, PositionSignal] | None,
    ten_god: str,
) -> dict[str, object]:
    if not position_signals:
        return {
            "visible_positions": [],
            "branch_main_positions": [],
            "hidden_positions": [],
            "grade": "position_not_evaluated",
            "score_delta": 0,
            "basis_codes": [],
            "counter_signals": [],
        }
    visible: list[str] = []
    branch_main: list[str] = []
    hidden: list[str] = []
    for position, signal in position_signals.items():
        if signal.stem_ten_god == ten_god:
            visible.append(position)
        if signal.branch_main_ten_god == ten_god:
            branch_main.append(position)
        if ten_god in list(signal.hidden_ten_gods or []):
            hidden.append(position)

    score_delta = 0
    if "month" in visible:
        score_delta += 10
    elif visible:
        score_delta += 5
    if "month" in branch_main:
        score_delta += 9
    elif "day" in branch_main:
        score_delta += 7
    elif branch_main:
        score_delta += 4
    if "month" in hidden:
        score_delta += 5
    elif "day" in hidden:
        score_delta += 4
    elif hidden:
        score_delta += 2

    if "month" in visible or "month" in branch_main:
        grade = "month_position_reality"
    elif "day" in branch_main or "day" in hidden:
        grade = "day_branch_life_reality"
    elif visible:
        grade = "visible_stem_action"
    elif branch_main or hidden:
        grade = "branch_hidden_action"
    else:
        grade = "position_weak"

    basis_codes = [
        *(f"gyeokguk_action_visible_position_{position}" for position in visible),
        *(f"gyeokguk_action_branch_main_position_{position}" for position in branch_main),
        *(f"gyeokguk_action_hidden_position_{position}" for position in hidden[:4]),
        f"gyeokguk_action_position_grade_{grade}",
    ]
    counter_signals = [] if visible or branch_main or hidden else ["gyeokguk_action_position_not_found"]
    return {
        "visible_positions": visible,
        "branch_main_positions": branch_main,
        "hidden_positions": hidden,
        "grade": grade,
        "score_delta": min(18, score_delta),
        "basis_codes": basis_codes,
        "counter_signals": counter_signals,
    }


POSITIVE_BRANCH_RELATIONS = {"six_combine", "three_harmony", "three_harmony_half", "three_meeting"}
PRESSURE_BRANCH_RELATIONS = {"clash", "punishment", "self_punishment", "break", "harm"}


def _actor_alignment_for_branch(month_fit_state: str, role_grade: str) -> str:
    if month_fit_state in {"harms_month_command", "burdensome_by_month_command"}:
        return "burdensome"
    if role_grade in {"breaker", "danger", "burden", "core_overload"}:
        return "burdensome"
    if month_fit_state in {"supports_month_command", "usable_by_month_command"}:
        return "needed"
    if role_grade in {
        "support",
        "strong_regulator",
        "regulator",
        "breaker_or_medicine",
        "regulator_or_breaker",
        "source",
        "conditioned_support",
    }:
        return "needed"
    return "mixed"


def _branch_relation_context(
    *,
    branch_interactions: list[BranchInteraction] | None,
    position_context: dict[str, object],
    acting_element: str,
    month_fit_state: str = "",
    role_grade: str = "",
) -> dict[str, object]:
    if not branch_interactions:
        return {
            "relations": [],
            "grade": "branch_relation_not_evaluated",
            "score_delta": 0,
            "basis_codes": [],
            "counter_signals": [],
        }
    positions = set(position_context.get("visible_positions", []) or [])
    positions.update(position_context.get("branch_main_positions", []) or [])
    positions.update(position_context.get("hidden_positions", []) or [])
    details: list[dict[str, object]] = []
    score_delta = 0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    actor_alignment = _actor_alignment_for_branch(month_fit_state, role_grade)
    for interaction in branch_interactions:
        relation_type = str(interaction.relation_type)
        touched_by_position = bool(positions & set(interaction.positions))
        touched_by_element = bool(acting_element and interaction.effect_element == acting_element)
        if not touched_by_position and not touched_by_element:
            continue
        detail = {
            "relation_type": relation_type,
            "positions": list(interaction.positions),
            "branches": list(interaction.branches),
            "effect_element": interaction.effect_element,
        }
        details.append(detail)
        if relation_type in POSITIVE_BRANCH_RELATIONS:
            if actor_alignment == "burdensome":
                score_delta -= 4
                counter_signals.append(f"gyeokguk_action_branch_supports_burdensome_actor_{relation_type}")
            else:
                score_delta += 4
                basis_codes.append(f"gyeokguk_action_branch_supports_needed_actor_{relation_type}")
        elif relation_type in PRESSURE_BRANCH_RELATIONS:
            if actor_alignment == "burdensome":
                score_delta += 3
                basis_codes.append(f"gyeokguk_action_branch_pressure_releases_burdensome_actor_{relation_type}")
                counter_signals.append(f"gyeokguk_action_branch_pressure_eventful_{relation_type}")
            elif actor_alignment == "mixed":
                score_delta -= 2
                counter_signals.append(f"gyeokguk_action_branch_pressure_forces_mixed_actor_{relation_type}")
            else:
                score_delta -= 6
                counter_signals.append(f"gyeokguk_action_branch_pressure_damages_needed_actor_{relation_type}")
        else:
            basis_codes.append(f"gyeokguk_action_branch_relation_{relation_type}")
    if not details:
        return {
            "relations": [],
            "grade": "branch_relation_not_touching_actor",
            "score_delta": 0,
            "basis_codes": [],
            "counter_signals": [],
        }
    if score_delta > 0 and any("pressure_releases_burdensome_actor" in code for code in basis_codes):
        grade = "branch_relation_releases_burdensome_actor"
    elif score_delta > 0:
        grade = "branch_relation_supports_needed_actor"
    elif score_delta < 0 and any("supports_burdensome_actor" in code for code in counter_signals):
        grade = "branch_relation_amplifies_burdensome_actor"
    elif score_delta < 0:
        grade = "branch_relation_pressures_needed_actor"
    else:
        grade = "branch_relation_mixed_actor"
    return {
        "relations": details[:5],
        "grade": grade,
        "score_delta": max(-12, min(10, score_delta)),
        "basis_codes": basis_codes,
        "counter_signals": counter_signals,
        "actor_alignment": actor_alignment,
    }


def gyeokguk_action_context_adjustment(
    *,
    ten_god: str,
    acting_group: str,
    element_profile: ElementProfile | None,
    position_signals: dict[str, PositionSignal] | None,
    branch_interactions: list[BranchInteraction] | None = None,
    month_fit_state: str = "",
    role_grade: str = "",
) -> dict[str, object]:
    acting_element = _role_element(element_profile.day_master_element, acting_group) if element_profile else ""
    strength = _day_master_strength_context(element_profile, acting_group)
    climate = _climate_context(element_profile, acting_group)
    position = _positions_for_ten_god(position_signals, ten_god)
    branch = _branch_relation_context(
        branch_interactions=branch_interactions,
        position_context=position,
        acting_element=acting_element,
        month_fit_state=month_fit_state,
        role_grade=role_grade,
    )
    score_delta = int(strength["score_delta"]) + int(climate["score_delta"]) + int(position["score_delta"]) + int(branch["score_delta"])
    return {
        "acting_element": acting_element,
        "score_delta": max(-24, min(28, score_delta)),
        "strength": strength,
        "climate": climate,
        "position": position,
        "branch_relation": branch,
        "basis_codes": [
            *list(strength.get("basis_codes", []) or []),
            *list(climate.get("basis_codes", []) or []),
            *list(position.get("basis_codes", []) or []),
            *list(branch.get("basis_codes", []) or []),
        ],
        "counter_signals": [
            *list(strength.get("counter_signals", []) or []),
            *list(climate.get("counter_signals", []) or []),
            *list(position.get("counter_signals", []) or []),
            *list(branch.get("counter_signals", []) or []),
        ],
    }


def _rule_basis_codes(
    *,
    pattern: str,
    pattern_ten_god: str,
    acting_ten_god: str,
    relation: str,
    role_grade: str,
    pattern_effect_state: str,
    domain_priority: list[str],
) -> list[str]:
    return [
        *gyeokguk_action_judgment_basis_codes("gyeokguk_action"),
        f"gyeokguk_action_pattern:{pattern}",
        f"gyeokguk_action_pattern_ten_god:{pattern_ten_god}",
        f"gyeokguk_action_actor:{acting_ten_god}",
        f"gyeokguk_action_exact_ten_god:{acting_ten_god}",
        f"gyeokguk_action_relation:{relation}",
        f"gyeokguk_action_role_grade:{role_grade}",
        f"gyeokguk_action_effect_state:{pattern_effect_state}",
        *(f"gyeokguk_action_exact_profile_domain:{domain}" for domain in TEN_GOD_EXACT_ACTION_PROFILE[acting_ten_god]["domains"]),
        *(f"gyeokguk_action_domain:{domain}" for domain in domain_priority[:3]),
    ]


def _sentence(text: str) -> str:
    value = text.strip()
    if not value:
        return ""
    return value if value.endswith((".", "다.", "요.", "음.")) else f"{value}."


def _with_single_pattern_context(text: str, pattern: str, acting_ten_god: str) -> str:
    """Keep the month-command pattern center visible in core rule logic."""

    value = text.strip()
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    additions: list[str] = []
    if pattern_label not in value or pattern_center not in value or ten_god_label not in value:
        additions.append(
            f"{pattern_label}의 판단 기준은 {pattern_center}입니다. {_topic_form(ten_god_label)} 이 기준 안에서 성격·파격·병약을 다시 가른다."
        )
    if not additions:
        return value
    return f"{value} {' '.join(additions)}"


def _display_action_label(action_nature: str) -> str:
    canonical_prefixes = [
        ("재극", "재극인"),
        ("정재생관", "재생관"),
        ("편재생관", "재생관"),
        ("식신생재", "식상생재"),
        ("상관생재", "식상생재"),
        ("정인제식", "인성도식"),
        ("편인도식", "인성도식"),
    ]
    for prefix, canonical in canonical_prefixes:
        if action_nature.startswith(prefix) and canonical not in action_nature:
            return f"{canonical}·{action_nature}"
    return action_nature


def _subject_phrase(text: str) -> str:
    stripped = text.rstrip()
    probe = stripped
    while probe and probe[-1] in ")]}）』」":
        probe = probe[:-1].rstrip()
    particle = "이" if _has_final_consonant(probe) else "가"
    return f"{stripped}{particle}"


def _actor_subject_phrase(ten_god_label: str, action_nature: str) -> str:
    action_label = _display_action_label(action_nature)
    particle = "이" if _has_final_consonant(ten_god_label) else "가"
    return f"{ten_god_label}({action_label}){particle}"


def _single_visibility_effects(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    center_effect: str,
) -> dict[str, str]:
    exact_profile = TEN_GOD_EXACT_ACTION_PROFILE[acting_ten_god]
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    actor_label = _actor_subject_phrase(ten_god_label, action_nature)
    center_sentence = _sentence(center_effect)
    return {
        "protruded": (
            f"{pattern_label}에서 {actor_label} 천간에 투출하면 "
            f"{pattern_center}에 대한 작용이 밖으로 드러난다. "
            f"{center_sentence} {exact_profile['protruded']}"
        ),
        "hidden": (
            f"{pattern_label}에서 {actor_label} 지장간에 숨어 있으면 "
            f"{_object_form(pattern_center)} 직접 장악하기보다 생활 조건과 사건의 배경에서 움직인다. "
            f"{exact_profile['hidden']}"
        ),
        "rooted": (
            f"{pattern_label}에서 {actor_label} 통근하면 "
            f"{pattern_center}에 작용하는 힘이 실제 조건으로 버틴다. "
            f"{exact_profile['rooted']}"
        ),
        "unrooted": (
            f"{pattern_label}에서 {actor_label} 뿌리 없이 떠 있으면 "
            f"{pattern_center}에 대한 판단은 들어오지만 지속성과 현실 장악력은 낮아진다. "
            f"{exact_profile['unrooted']}"
        ),
    }


def _single_success_logic(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    role_grade: str,
    center_effect: str,
    pattern_success: str,
    critical_append: str,
) -> str:
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    intro = (
        f"{PATTERN_LENS[pattern]['label']}: {action_nature} 작용. "
        f"작용 십신은 {ten_god_label}입니다. 핵심 성격은 {TEN_GOD_EXACT_NUANCE[acting_ten_god]}이다. "
    )
    center_sentence = _sentence(center_effect)
    critical_sentence = f" {critical_append.strip()}" if critical_append.strip() else ""
    if role_grade in {
        "breaker",
        "danger",
        "burden",
        "core_overload",
        "regulator_or_breaker",
        "breaker_or_medicine",
    }:
        return (
            f"{intro}이 격국에서는 {center_sentence} "
            f"이 작용은 그대로 키우기보다 제어와 분별이 필요하다. "
            f"정리되면 {pattern_success}{critical_sentence}"
        )
    return (
        f"{intro}이 격국에서는 {center_sentence} "
        f"이 작용이 제자리를 잡으면 {pattern_success}{critical_sentence}"
    )


def _single_failure_logic(
    *,
    pattern: str,
    acting_ten_god: str,
    action_nature: str,
    role_grade: str,
    center_effect: str,
    pattern_disease: str,
    relation: str,
    exact_profile: dict[str, object],
    critical_lens: dict[str, object],
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    exact = TEN_GOD_EXACT_NUANCE[acting_ten_god]
    center_sentence = _sentence(center_effect)
    excess = _sentence(str(critical_lens.get("excess") or exact_profile["excess"]))
    deficiency = _sentence(str(critical_lens.get("deficiency") or exact_profile["deficiency"]))
    relation_text = RELATION_EXPERT_TEXT.get(relation, "간접 작용")
    critical_sentence = f" {str(critical_lens.get('failure_append', '')).strip()}" if str(critical_lens.get("failure_append", "")).strip() else ""
    if role_grade in {
        "breaker",
        "danger",
        "burden",
        "core_overload",
        "regulator_or_breaker",
        "breaker_or_medicine",
    }:
        role_sentence = "이 작용은 처음부터 격국을 돕는 힘으로만 보지 않는다. 과하거나 약하면 본래 역할이 흔들린다."
    else:
        role_sentence = "이 작용도 강약과 위치가 어긋나면 본래 역할이 흔들린다."
    return (
        f"{pattern_label}: {action_nature} 작용의 실패 조건. "
        f"작용 십신은 {ten_god_label}입니다. 핵심 성격은 {exact}이다. "
        f"이 격국에서는 {center_sentence} {role_sentence} "
        f"과하면 {excess} 약하면 {deficiency} "
        f"{pattern_disease} {relation_text}{critical_sentence}"
    )


def _single_timing_activation(
    *,
    pattern: str,
    acting_ten_god: str,
    acting_group: str,
    action_nature: str,
    role_grade: str,
    domain_priority: list[str],
    timing_text: str,
) -> str:
    pattern_label = PATTERN_LENS[pattern]["label"]
    ten_god_label = TEN_GOD_LABELS[acting_ten_god]
    actor_label = _actor_subject_phrase(ten_god_label, action_nature)
    body = _sentence(timing_text)
    primary_domain = domain_priority[0] if domain_priority else "personality"
    domain_context = SINGLE_LUCK_DOMAIN_CONTEXT.get(primary_domain, SINGLE_LUCK_DOMAIN_CONTEXT["personality"])
    group_context = SINGLE_LUCK_GROUP_CONTEXT.get(acting_group, "")
    role_context = SINGLE_LUCK_ROLE_CONTEXT.get(role_grade, "")
    activation_tail = (
        f" 대운에서는 {domain_context['daeun']}. "
        f"세운에서는 {domain_context['seun']}."
    )
    if group_context:
        activation_tail = f"{activation_tail} {group_context}"
    if role_context:
        activation_tail = f"{activation_tail} {role_context}"
    if pattern_label in body and ten_god_label in body:
        return f"{body}{activation_tail}"
    return f"{pattern_label}에서 {actor_label} 대운·세운에서 발동하면 {body}{activation_tail}"


def _build_rule(pattern: str, acting_ten_god: str) -> GyeokgukTenGodActionRule:
    pattern_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_group = TEN_GOD_GROUPS[pattern_ten_god]
    acting_group = TEN_GOD_GROUPS[acting_ten_god]
    relation = _relation_to_pattern(pattern_group, acting_group)
    role_grade, action_nature, center_effect = PATTERN_LENS[pattern][acting_group]
    action_nature = _exact_action_nature(pattern_ten_god, action_nature, acting_ten_god)
    favorable, unfavorable = _conditions(pattern, acting_group, relation, role_grade)
    exact_profile = TEN_GOD_EXACT_ACTION_PROFILE[acting_ten_god]
    critical_lens = _critical_single_action_lens(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        acting_group=acting_group,
        action_nature=action_nature,
    )
    critical_codes = list(critical_lens.get("basis_codes", []) or [])
    critical_key = ""
    for code in critical_codes:
        if str(code).startswith("gyeokguk_single_critical_action:"):
            critical_key = str(code).split(":", 1)[1]
            break
    classical_tags = _single_classical_action_tags(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        acting_group=acting_group,
        action_nature=action_nature,
        critical_key=critical_key,
    )
    pattern_context = PATTERN_ACTION_CONTEXT[pattern]
    pattern_effect_state = ROLE_GRADE_EFFECT_STATE[role_grade]
    pattern_resolution_state = _single_resolution_state(role_grade)
    role_in_pattern_logic = _single_role_in_pattern_logic(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        role_grade=role_grade,
        relation=relation,
        action_nature=action_nature,
        center_effect=center_effect,
    )
    role_in_pattern_logic = _with_single_pattern_context(role_in_pattern_logic, pattern, acting_ten_god)
    pattern_resolution_logic = _single_resolution_logic(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        role_grade=role_grade,
        relation=relation,
        center_effect=center_effect,
    )
    pattern_resolution_logic = _with_single_pattern_context(pattern_resolution_logic, pattern, acting_ten_god)
    domain_priority = _domain_priority(pattern, acting_ten_god, action_nature)
    event_manifestations = _single_event_manifestations(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        acting_group=acting_group,
        action_nature=action_nature,
        role_grade=role_grade,
        domain_priority=domain_priority,
    )
    rule_key = f"{pattern}:{acting_ten_god}"
    visibility_effects = _single_visibility_effects(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        action_nature=action_nature,
        center_effect=center_effect,
    )
    success_logic = _single_success_logic(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        action_nature=action_nature,
        role_grade=role_grade,
        center_effect=center_effect,
        pattern_success=pattern_context["success"],
        critical_append=str(critical_lens.get("success_append", "")),
    )
    success_logic = _with_single_pattern_context(success_logic, pattern, acting_ten_god)
    failure_logic = _single_failure_logic(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        action_nature=action_nature,
        role_grade=role_grade,
        center_effect=center_effect,
        pattern_disease=pattern_context["disease"],
        relation=relation,
        exact_profile=exact_profile,
        critical_lens=critical_lens,
    )
    failure_logic = _with_single_pattern_context(failure_logic, pattern, acting_ten_god)
    timing_activation = _single_timing_activation(
        pattern=pattern,
        acting_ten_god=acting_ten_god,
        acting_group=acting_group,
        action_nature=action_nature,
        role_grade=role_grade,
        domain_priority=domain_priority,
        timing_text=str(critical_lens.get("timing") or pattern_context["timing"]),
    )
    timing_activation = _with_single_pattern_context(timing_activation, pattern, acting_ten_god)
    return GyeokgukTenGodActionRule(
        rule_key=rule_key,
        pattern=pattern,
        pattern_ten_god=pattern_ten_god,
        pattern_group=pattern_group,
        acting_ten_god=acting_ten_god,
        acting_group=acting_group,
        relation_to_pattern=relation,
        action_key=f"{pattern}_{acting_ten_god}_{action_nature}",
        role_grade=role_grade,
        action_nature=action_nature,
        center_effect=center_effect,
        role_in_pattern_logic=role_in_pattern_logic,
        pattern_effect_state=pattern_effect_state,
        pattern_resolution_state=pattern_resolution_state,
        pattern_resolution_logic=pattern_resolution_logic,
        excess_disease=str(critical_lens.get("excess") or exact_profile["excess"]),
        deficiency_gap=str(critical_lens.get("deficiency") or exact_profile["deficiency"]),
        protrusion_effect=visibility_effects["protruded"],
        hidden_effect=visibility_effects["hidden"],
        rooting_effect=visibility_effects["rooted"],
        unrooted_effect=visibility_effects["unrooted"],
        timing_activation=timing_activation,
        event_manifestations=event_manifestations,
        classical_action_tags=list(classical_tags),
        domain_priority=domain_priority,
        success_logic=success_logic,
        failure_logic=failure_logic,
        domain_projections=_domain_projections(
            pattern,
            acting_ten_god,
            acting_group,
            action_nature,
            relation=relation,
            role_grade=role_grade,
        ),
        favorable_conditions=favorable,
        unfavorable_conditions=unfavorable,
        judgment_order=list(GYEOKGUK_ACTION_JUDGMENT_ORDER),
        basis_codes=_rule_basis_codes(
            pattern=pattern,
            pattern_ten_god=pattern_ten_god,
            acting_ten_god=acting_ten_god,
            relation=relation,
            role_grade=role_grade,
            pattern_effect_state=pattern_effect_state,
            domain_priority=domain_priority,
        )
        + [f"gyeokguk_single_actor_role:{acting_ten_god}:{role_grade}"]
        + [f"gyeokguk_single_event_manifestation:{domain}" for domain in event_manifestations]
        + [f"gyeokguk_single_resolution:{pattern_resolution_state}"]
        + critical_codes
        + [f"gyeokguk_single_classical_action:{tag}" for tag in classical_tags]
        + classical_action_mechanic_codes(classical_tags, prefix="gyeokguk_single"),
    )


def _build_dictionary() -> dict[str, dict[str, GyeokgukTenGodActionRule]]:
    return {
        pattern: {
            ten_god: _build_rule(pattern, ten_god)
            for ten_god in TEN_GODS
        }
        for pattern in PATTERN_CENTER_BY_PATTERN
    }


GYEOKGUK_TEN_GOD_ACTIONS = _build_dictionary()


def gyeokguk_ten_god_action_rule(pattern: str, acting_ten_god: str) -> GyeokgukTenGodActionRule:
    return GYEOKGUK_TEN_GOD_ACTIONS[pattern][acting_ten_god]


def _presence_state(visible: float, hidden: float) -> str:
    if visible >= 0.75 and hidden >= 0.5:
        return "visible_and_rooted"
    if visible >= 0.75:
        return "visible"
    if hidden >= 0.5:
        return "rooted_or_hidden"
    if visible or hidden:
        return "weakly_present"
    return "not_present"


def _presence_score(visible: float, hidden: float) -> int:
    return max(0, min(100, round(visible * 32 + hidden * 22)))


def _verdict(rule: GyeokgukTenGodActionRule, presence_state: str, month_fit_state: str) -> str:
    if presence_state == "not_present":
        return "not_activated"
    if month_fit_state in MONTH_PRESSURE_STATES:
        if rule.role_grade in {"breaker", "danger"}:
            return "risk_activated"
        if rule.role_grade in {"core", "core_overload", "burden"}:
            return "overload_action"
        return "conditional_action"
    if rule.role_grade in {"breaker", "danger"}:
        return "destructive_action"
    if rule.role_grade in {"burden", "core_overload"}:
        return "overload_action"
    if month_fit_state in MONTH_SUPPORT_STATES:
        if rule.role_grade == "core":
            return "center_reinforced"
        if rule.role_grade == "source":
            return "feeds_pattern_source"
        if rule.role_grade in {"support", "strong_regulator", "regulator"}:
            return "constructive_action"
    if month_fit_state in MONTH_MIXED_STATES:
        if rule.role_grade == "core":
            return "center_reinforced"
        return "conditional_action"
    if rule.role_grade in {"regulator_or_breaker", "breaker_or_medicine", "mixed", "conditioned_support"}:
        return "conditional_action"
    return ROLE_GRADE_VERDICT.get(rule.role_grade, "observed_action")


def _functional_role(rule: GyeokgukTenGodActionRule, verdict: str) -> str:
    if verdict == "not_activated":
        return "inactive"
    if verdict in {"risk_activated", "destructive_action", "overload_action"}:
        return "adverse_god"
    if rule.role_grade == "core":
        return "pattern_center"
    if verdict == "constructive_action":
        if rule.role_grade in {"strong_regulator", "regulator"}:
            return "rescuing_god"
        return "supporting_god"
    if verdict == "feeds_pattern_source":
        return "supporting_god"
    return "conditional_god"


def _single_month_fit_label(month_fit_state: str) -> str:
    return {
        "supports_month_command": "월령 기준에서 필요성이 확인되는 작용",
        "usable_by_month_command": "월령상 사용할 수 있는 작용",
        "mixed_by_month_command": "월령상 성패가 갈리는 조건부 작용",
        "harms_month_command": "월령 기준에서 격을 흔드는 작용",
        "burdensome_by_month_command": "월령 기준에서 부담이 커지는 작용",
    }.get(month_fit_state, "월령 판단은 보조 조건으로 남는 작용")


def _single_context_state_label(state: str) -> str:
    return {
        "constructive_by_context": "성격 보조 강화",
        "medicine_or_regulator": "병약 조절 가능",
        "risk_by_context": "파격 위험 강화",
        "context_strengthens_action": "보조 조건이 작용 강화",
        "conditional_by_context": "조건부 작용",
        "context_weakens_action": "보조 조건이 작용 약화",
        "not_activated": "원국 직접 발동 약함",
    }.get(state, "조건부 작용")


def _single_protrusion_note(position: dict[str, object]) -> str:
    visible = list(position.get("visible_positions", []) or [])
    if "month" in visible:
        return "월간에 드러나 격국 판단과 사회적 사건에 직접 들어온다."
    if visible:
        return "천간에 드러나 외부 평가와 사건으로 보이기 쉽다."
    return "천간 투출은 약하고 지지·지장간의 현실 작용을 우선 본다."


def _single_position_note(position: dict[str, object]) -> str:
    visible = list(position.get("visible_positions", []) or [])
    branch_main = list(position.get("branch_main_positions", []) or [])
    hidden = list(position.get("hidden_positions", []) or [])
    grade = str(position.get("grade", "") or "")
    if "month" in visible or "month" in branch_main:
        return "월주와 월지에 닿아 격국 판단의 중심부에서 작용한다."
    if "day" in branch_main or "day" in hidden:
        return "일지에서 확인되어 생활 감각과 실제 선택에 가깝게 작용한다."
    if visible:
        return "천간에 떠 있어 외부에서 먼저 보이는 작용이다."
    if branch_main or hidden:
        return "지지와 지장간에 깔려 현실 조건 안에서 늦게 드러난다."
    if grade == "position_not_evaluated":
        return "위치 신호는 아직 별도 평가되지 않았다."
    return "위치상 작용은 약하게 확인된다."


def _single_rooting_note(position: dict[str, object]) -> str:
    branch_main = list(position.get("branch_main_positions", []) or [])
    hidden = list(position.get("hidden_positions", []) or [])
    if "month" in branch_main:
        return "월지 본기에 닿아 계절의 힘을 직접 받는다."
    if branch_main:
        return "지지 본기에 닿아 현실에서 버티는 힘이 있다."
    if hidden:
        return "지장간에 숨어 있어 운에서 자극될 때 뿌리처럼 작동한다."
    return "통근은 약하므로 오래 버티는 힘보다 발동 조건을 더 본다."


def _single_hidden_note(position: dict[str, object]) -> str:
    hidden = list(position.get("hidden_positions", []) or [])
    branch_main = list(position.get("branch_main_positions", []) or [])
    if "month" in hidden or "month" in branch_main:
        return "월지와 지장간에 닿아 겉보다 현실 조건에서 더 중요하게 작용한다."
    if "day" in hidden or "day" in branch_main:
        return "일지와 지장간에 닿아 관계, 생활, 반복 선택에서 드러난다."
    if hidden:
        return "지장간에 숨어 있어 대운·세운에서 열릴 때 사건성이 커진다."
    return "지장간 작용은 약하므로 천간과 월령 판단을 우선한다."


def _single_branch_note(branch_relation: dict[str, object]) -> str:
    grade = str(branch_relation.get("grade", "") or "")
    relations = list(branch_relation.get("relations", []) or [])
    if not relations:
        return "합충형파해가 해당 작용을 직접 건드리는 신호는 약하다."
    if grade == "branch_relation_supports_needed_actor":
        return "합·회합 계열이 필요한 작용을 모아 성립과 현실화를 돕는다."
    if grade == "branch_relation_amplifies_burdensome_actor":
        return "합·회합 계열이 부담 작용까지 묶어 병증을 키울 수 있다."
    if grade == "branch_relation_releases_burdensome_actor":
        return "충·형·파·해가 부담 작용을 흔들어 묶인 병을 풀어내는 쪽으로도 작용한다."
    if grade == "branch_relation_pressures_needed_actor":
        return "충·형·파·해가 필요한 작용을 흔들어 사건성, 갈등, 손상을 키운다."
    return "합충형파해가 섞여 있어 도움과 변동을 함께 본다."


def _single_context_judgment(
    *,
    rule: GyeokgukTenGodActionRule,
    presence_state: str,
    month_fit_state: str,
    context: dict[str, object],
) -> dict[str, object]:
    score_delta = int(context.get("score_delta", 0) or 0)
    verdict = _verdict(rule, presence_state, month_fit_state)
    if presence_state == "not_present":
        state = "not_activated"
    elif verdict == "constructive_action" and score_delta >= 6:
        state = "constructive_by_context"
    elif verdict in {"risk_activated", "destructive_action", "overload_action"} and month_fit_state in MONTH_PRESSURE_STATES:
        state = "risk_by_context"
    elif (
        rule.role_grade in {"regulator", "strong_regulator", "breaker_or_medicine", "regulator_or_breaker"}
        and month_fit_state not in MONTH_PRESSURE_STATES
        and score_delta >= 0
    ):
        state = "medicine_or_regulator"
    elif score_delta >= 8:
        state = "context_strengthens_action"
    elif score_delta <= -8:
        state = "context_weakens_action"
    else:
        state = "conditional_by_context"

    position = dict(context.get("position", {}) or {})
    branch = dict(context.get("branch_relation", {}) or {})
    month_label = _single_month_fit_label(month_fit_state)
    state_label = _single_context_state_label(state)
    ten_god_label = TEN_GOD_LABELS.get(rule.acting_ten_god, rule.acting_ten_god)
    pattern_label = str(PATTERN_LENS[rule.pattern]["label"])
    score_text = f"+{score_delta}" if score_delta >= 0 else str(score_delta)
    path = [
        f"월령: {month_label}",
        f"격국: {pattern_label} / {rule.pattern_effect_state}",
        f"일간 강약: {context['strength'].get('label', '')}",
        f"조후: {context['climate'].get('label', '')}",
        f"투출: {_single_protrusion_note(position)}",
        f"통근: {_single_rooting_note(position)}",
        f"위치: {_single_position_note(position)}",
        f"지장간: {_single_hidden_note(position)}",
        f"합충형파해: {_single_branch_note(branch)}",
        f"대운·세운: {rule.timing_activation}",
    ]
    summary = (
        f"{_subject_form(ten_god_label)} {rule.action_nature} 작용으로 읽는다. "
        f"월령 판단은 {month_label}이고, 강약·조후·위치 보정은 {score_text}이다. "
        f"최종 판정은 {state_label}이다."
    )
    return {
        "state": state,
        "summary": summary,
        "path": path,
        "basis_codes": [
            f"gyeokguk_single_context_judgment:{state}",
            f"gyeokguk_single_context_score_delta:{score_delta}",
        ],
    }


def build_gyeokguk_ten_god_action_matches(
    *,
    pattern: str,
    ten_god_profile: TenGodProfile,
    month_governance_profile: MonthGovernanceProfile,
    element_profile: ElementProfile | None = None,
    position_signals: dict[str, PositionSignal] | None = None,
    branch_interactions: list[BranchInteraction] | None = None,
) -> list[GyeokgukTenGodActionMatch]:
    if pattern not in GYEOKGUK_TEN_GOD_ACTIONS:
        return []
    matches: list[GyeokgukTenGodActionMatch] = []
    for ten_god in TEN_GODS:
        visible = float(ten_god_profile.visible_counts.get(ten_god, 0.0) or 0.0)
        hidden = float(ten_god_profile.hidden_counts.get(ten_god, 0.0) or 0.0)
        state = _presence_state(visible, hidden)
        if state == "not_present":
            continue
        rule = gyeokguk_ten_god_action_rule(pattern, ten_god)
        fit = month_governance_profile.role_fits.get(rule.acting_group)
        month_fit_state = str(getattr(fit, "status", "") or "")
        context = gyeokguk_action_context_adjustment(
            ten_god=ten_god,
            acting_group=rule.acting_group,
            element_profile=element_profile,
            position_signals=position_signals,
            branch_interactions=branch_interactions,
            month_fit_state=month_fit_state,
            role_grade=rule.role_grade,
        )
        context_judgment = _single_context_judgment(
            rule=rule,
            presence_state=state,
            month_fit_state=month_fit_state,
            context=context,
        )
        base_score = _presence_score(visible, hidden)
        score = max(0, min(100, base_score + int(context["score_delta"])))
        verdict = _verdict(rule, state, month_fit_state)
        functional_role = _functional_role(rule, verdict)
        basis_codes = [
            *rule.basis_codes,
            f"gyeokguk_action_presence:{state}",
            f"gyeokguk_action_base_presence_score:{base_score}",
            f"gyeokguk_action_presence_score:{score}",
            *list(context["basis_codes"]),
            *list(context_judgment["basis_codes"]),
            f"gyeokguk_functional_role:{functional_role}",
        ]
        counter_signals: list[str] = []
        if state == "weakly_present":
            counter_signals.append("gyeokguk_action_weak_presence")
        if fit:
            counter_signals.extend(list(fit.counter_signals))
        counter_signals.extend(list(context["counter_signals"]))
        matches.append(
            GyeokgukTenGodActionMatch(
                rule_key=rule.rule_key,
                pattern=rule.pattern,
                acting_ten_god=rule.acting_ten_god,
                acting_group=rule.acting_group,
                relation_to_pattern=rule.relation_to_pattern,
                action_key=rule.action_key,
                action_nature=rule.action_nature,
                role_grade=rule.role_grade,
                center_effect=rule.center_effect,
                role_in_pattern_logic=rule.role_in_pattern_logic,
                presence_state=state,
                presence_score=score,
                month_fit_state=month_fit_state,
                verdict=verdict,
                functional_role=functional_role,
                functional_role_label=FUNCTIONAL_ROLE_LABELS[functional_role],
                pattern_effect_state=rule.pattern_effect_state,
                pattern_resolution_state=rule.pattern_resolution_state,
                pattern_resolution_logic=rule.pattern_resolution_logic,
                activation_context=_activation_context(state, month_fit_state),
                context_judgment_state=str(context_judgment["state"]),
                context_judgment_summary=str(context_judgment["summary"]),
                context_judgment_path=list(context_judgment["path"]),
                day_master_strength_context=str(context["strength"].get("label", "")),
                climate_context=str(context["climate"].get("label", "")),
                position_context=dict(context["position"]),
                branch_relation_context=dict(context["branch_relation"]),
                excess_disease=rule.excess_disease,
                deficiency_gap=rule.deficiency_gap,
                protrusion_effect=rule.protrusion_effect,
                hidden_effect=rule.hidden_effect,
                rooting_effect=rule.rooting_effect,
                unrooted_effect=rule.unrooted_effect,
                timing_activation=rule.timing_activation,
                event_manifestations=dict(rule.event_manifestations),
                classical_action_tags=list(rule.classical_action_tags),
                domain_priority=list(rule.domain_priority),
                expert_summary=rule.success_logic,
                domain_projections=dict(rule.domain_projections),
                judgment_order=list(rule.judgment_order),
                basis_codes=list(dict.fromkeys(basis_codes)),
                counter_signals=list(dict.fromkeys(counter_signals)),
            )
        )
    matches.sort(
        key=lambda item: (
            item.presence_score,
            1 if item.verdict in {"constructive_action", "conditional_action"} else 0,
        ),
        reverse=True,
    )
    return matches


def validate_gyeokguk_ten_god_action_dictionary() -> list[str]:
    issues: list[str] = []
    found_classical_tags: set[str] = set()
    core_tag_pattern_signatures: dict[str, dict[str, set[tuple[object, ...]]]] = {}
    ten_god_pattern_signatures: dict[str, dict[str, tuple[object, ...]]] = {}
    expected_patterns = set(PATTERN_CENTER_BY_PATTERN)
    exact_pair_checks = [
        ("bi_gyeon", "geob_jae"),
        ("sik_sin", "sang_gwan"),
        ("pyeon_jae", "jeong_jae"),
        ("pyeon_gwan", "jeong_gwan"),
        ("pyeon_in", "jeong_in"),
    ]
    if set(GYEOKGUK_TEN_GOD_ACTIONS) != expected_patterns:
        issues.append("pattern_set_mismatch")
    for pattern, rules in GYEOKGUK_TEN_GOD_ACTIONS.items():
        if set(rules) != set(TEN_GODS):
            issues.append(f"{pattern}:ten_god_set_mismatch")
        pattern_ten_god = PATTERN_CENTER_BY_PATTERN.get(pattern, "")
        pattern_group = TEN_GOD_GROUPS.get(pattern_ten_god, "")
        support_groups = {str(item[0]) for item in REGULAR_PATTERN_NEED_RULES.get(pattern_ten_god, {}).get("support", ())}
        caution_groups = {str(item[0]) for item in REGULAR_PATTERN_NEED_RULES.get(pattern_ten_god, {}).get("caution", ())}
        for ten_god, rule in rules.items():
            if not all(
                [
                    rule.rule_key,
                    rule.pattern,
                    rule.pattern_ten_god,
                    rule.acting_ten_god,
                    rule.relation_to_pattern,
                    rule.action_key,
                    rule.role_grade,
                    rule.center_effect,
                    rule.role_in_pattern_logic,
                    rule.pattern_effect_state,
                    rule.pattern_resolution_state,
                    rule.pattern_resolution_logic,
                    rule.excess_disease,
                    rule.deficiency_gap,
                    rule.protrusion_effect,
                    rule.hidden_effect,
                    rule.rooting_effect,
                    rule.unrooted_effect,
                    rule.timing_activation,
                    rule.event_manifestations,
                    rule.classical_action_tags,
                    rule.domain_priority,
                    rule.success_logic,
                    rule.failure_logic,
                    rule.domain_projections,
                    rule.judgment_order,
                ]
            ):
                issues.append(f"{rule.rule_key}:blank_required_field")
            if rule.judgment_order != GYEOKGUK_ACTION_JUDGMENT_ORDER:
                issues.append(f"{rule.rule_key}:judgment_order_mismatch")
            if f"gyeokguk_action_exact_ten_god:{ten_god}" not in rule.basis_codes:
                issues.append(f"{rule.rule_key}:missing_exact_ten_god_basis")
            exact_profile_domains = set(TEN_GOD_EXACT_ACTION_PROFILE[ten_god]["domains"])
            exact_profile_domain_codes = {
                str(code).split(":", 1)[1]
                for code in rule.basis_codes
                if str(code).startswith("gyeokguk_action_exact_profile_domain:")
            }
            if exact_profile_domains != exact_profile_domain_codes:
                issues.append(f"{rule.rule_key}:exact_profile_domain_basis_mismatch")
            if f"gyeokguk_single_resolution:{rule.pattern_resolution_state}" not in rule.basis_codes:
                issues.append(f"{rule.rule_key}:missing_single_resolution_basis")
            if f"gyeokguk_single_actor_role:{rule.acting_ten_god}:{rule.role_grade}" not in rule.basis_codes:
                issues.append(f"{rule.rule_key}:missing_single_actor_role_basis")
            for index, step in enumerate(GYEOKGUK_ACTION_JUDGMENT_ORDER, start=1):
                if f"gyeokguk_action_judgment_step:{index}:{step}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_judgment_basis_step:{step}")
            if "gyeokguk_action_luck_activation:daeun_seun" not in rule.basis_codes:
                issues.append(f"{rule.rule_key}:missing_luck_activation_basis")
            for domain in ("money", "career", "relationship", "marriage", "personality", "luck_activation"):
                if domain not in rule.event_manifestations or not rule.event_manifestations[domain]:
                    issues.append(f"{rule.rule_key}:missing_event_manifestation:{domain}")
                if f"gyeokguk_single_event_manifestation:{domain}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_event_manifestation_basis:{domain}")
            expected_relation = _relation_to_pattern(pattern_group, TEN_GOD_GROUPS[ten_god])
            if rule.relation_to_pattern != expected_relation:
                issues.append(f"{rule.rule_key}:relation_mismatch")
            if rule.acting_group in support_groups and rule.role_grade in {"breaker", "danger"}:
                issues.append(f"{rule.rule_key}:support_group_marked_destructive")
            if rule.acting_group in caution_groups and rule.role_grade == "support":
                issues.append(f"{rule.rule_key}:caution_group_marked_plain_support")
            ten_god_pattern_signatures.setdefault(ten_god, {})[pattern] = (
                rule.relation_to_pattern,
                rule.role_grade,
                rule.pattern_resolution_state,
                rule.center_effect,
                rule.excess_disease,
                rule.deficiency_gap,
                tuple(rule.domain_priority),
            )
            pattern_label = PATTERN_LENS[pattern]["label"]
            pattern_center = PATTERN_LENS[pattern]["center"]
            ten_god_label = TEN_GOD_LABELS[ten_god]
            exact_nuance = TEN_GOD_EXACT_NUANCE[ten_god]
            for logic_key, logic_text in {
                "role_in_pattern_logic": rule.role_in_pattern_logic,
                "pattern_resolution_logic": rule.pattern_resolution_logic,
                "success_logic": rule.success_logic,
                "failure_logic": rule.failure_logic,
                "timing_activation": rule.timing_activation,
                "domain_projections": " ".join(rule.domain_projections.values()),
                "event_manifestations": " ".join(rule.event_manifestations.values()),
            }.items():
                if pattern_label not in logic_text:
                    issues.append(f"{rule.rule_key}:{logic_key}_missing_pattern_label")
                if ten_god_label not in logic_text:
                    issues.append(f"{rule.rule_key}:{logic_key}_missing_ten_god_label")
                if logic_key in {
                    "role_in_pattern_logic",
                    "pattern_resolution_logic",
                    "success_logic",
                    "failure_logic",
                    "timing_activation",
                } and pattern_center not in logic_text:
                    issues.append(f"{rule.rule_key}:{logic_key}_missing_pattern_center")
            if exact_nuance not in " ".join(rule.domain_projections.values()):
                issues.append(f"{rule.rule_key}:domain_projection_missing_exact_ten_god_nuance")
            for logic_key, logic_text in {
                "success_logic": rule.success_logic,
                "failure_logic": rule.failure_logic,
            }.items():
                if exact_nuance not in logic_text:
                    issues.append(f"{rule.rule_key}:{logic_key}_missing_exact_ten_god_nuance")
            display_action = _display_action_label(rule.action_nature)
            if pattern_label not in rule.protrusion_effect or display_action not in rule.protrusion_effect:
                issues.append(f"{rule.rule_key}:visibility_not_pattern_specific")
            visibility_checks = {
                "protrusion": ("천간", rule.protrusion_effect),
                "hidden": ("지장간", rule.hidden_effect),
                "rooting": ("통근", rule.rooting_effect),
                "unrooted": ("뿌리", rule.unrooted_effect),
            }
            for visibility_key, (needle, text) in visibility_checks.items():
                if needle not in text:
                    issues.append(f"{rule.rule_key}:missing_{visibility_key}_visibility_context")
            exact_visibility_checks = {
                "protrusion": ("protruded", rule.protrusion_effect),
                "hidden": ("hidden", rule.hidden_effect),
                "rooting": ("rooted", rule.rooting_effect),
                "unrooted": ("unrooted", rule.unrooted_effect),
            }
            for visibility_key, (profile_key, text) in exact_visibility_checks.items():
                if str(TEN_GOD_EXACT_ACTION_PROFILE[ten_god][profile_key]) not in text:
                    issues.append(f"{rule.rule_key}:missing_exact_{visibility_key}_profile")
            for domain in ("money", "career", "relationship", "marriage", "personality"):
                if domain not in rule.domain_projections or not rule.domain_projections[domain]:
                    issues.append(f"{rule.rule_key}:missing_domain_{domain}")
            if not set(rule.domain_priority).issubset({"money", "career", "relationship", "marriage", "personality", "reputation"}):
                issues.append(f"{rule.rule_key}:invalid_domain_priority")
            classical_codes = [
                str(code).split(":", 1)[1]
                for code in rule.basis_codes
                if str(code).startswith("gyeokguk_single_classical_action:")
            ]
            if not classical_codes:
                issues.append(f"{rule.rule_key}:missing_classical_action_tag")
            if list(dict.fromkeys(classical_codes)) != list(rule.classical_action_tags):
                issues.append(f"{rule.rule_key}:classical_action_tag_field_mismatch")
            found_classical_tags.update(classical_codes)
            for tag in classical_codes:
                if tag not in CLASSICAL_ACTION_MECHANICS:
                    issues.append(f"{rule.rule_key}:missing_classical_action_mechanic_profile:{tag}")
                    continue
                mechanic_text = CLASSICAL_ACTION_MECHANIC_TEXTS.get(tag, {})
                for text_axis in ("principle", "disease", "medicine"):
                    if not str(mechanic_text.get(text_axis, "")).strip():
                        issues.append(f"{rule.rule_key}:missing_classical_action_mechanic_text_{text_axis}:{tag}")
                for mechanic_axis in ("flow", "disease", "medicine"):
                    if not any(
                        str(code).startswith(f"gyeokguk_single_mechanic:{tag}:{mechanic_axis}:")
                        for code in rule.basis_codes
                    ):
                        issues.append(f"{rule.rule_key}:missing_single_mechanic_{mechanic_axis}:{tag}")
                if not any(
                    str(code).startswith(f"gyeokguk_single_mechanic:{tag}:event:")
                    for code in rule.basis_codes
                ):
                    issues.append(f"{rule.rule_key}:missing_single_mechanic_event:{tag}")
            for tag in set(classical_codes).intersection(CORE_SINGLE_CLASSICAL_TAGS_REQUIRING_CRITICAL_LENS):
                signature = (
                    rule.acting_ten_god,
                    rule.action_nature,
                    rule.role_grade,
                    rule.relation_to_pattern,
                    rule.center_effect,
                    rule.excess_disease,
                    rule.deficiency_gap,
                    rule.timing_activation,
                    tuple(rule.domain_priority),
                )
                core_tag_pattern_signatures.setdefault(tag, {}).setdefault(pattern, set()).add(signature)
            critical_codes = [
                str(code).split(":", 1)[1]
                for code in rule.basis_codes
                if str(code).startswith("gyeokguk_single_critical_action:")
            ]
            if (
                set(classical_codes).intersection(CORE_SINGLE_CLASSICAL_TAGS_REQUIRING_CRITICAL_LENS)
                and not critical_codes
            ):
                issues.append(f"{rule.rule_key}:core_classical_action_not_critical_lens")
        for first_ten_god, second_ten_god in exact_pair_checks:
            first_rule = rules.get(first_ten_god)
            second_rule = rules.get(second_ten_god)
            if first_rule is None or second_rule is None:
                continue
            first_signature = (
                first_rule.excess_disease,
                first_rule.deficiency_gap,
                first_rule.protrusion_effect,
                first_rule.hidden_effect,
                first_rule.rooting_effect,
                first_rule.unrooted_effect,
                first_rule.timing_activation,
                tuple(first_rule.domain_priority),
            )
            second_signature = (
                second_rule.excess_disease,
                second_rule.deficiency_gap,
                second_rule.protrusion_effect,
                second_rule.hidden_effect,
                second_rule.rooting_effect,
                second_rule.unrooted_effect,
                second_rule.timing_activation,
                tuple(second_rule.domain_priority),
            )
            if first_signature == second_signature:
                issues.append(f"{pattern}:{first_ten_god}_{second_ten_god}:exact_ten_gods_collapsed")
            first_projection_signature = tuple(
                first_rule.domain_projections.get(domain, "")
                for domain in ("money", "career", "relationship", "marriage", "personality")
            )
            second_projection_signature = tuple(
                second_rule.domain_projections.get(domain, "")
                for domain in ("money", "career", "relationship", "marriage", "personality")
            )
            if first_projection_signature == second_projection_signature:
                issues.append(f"{pattern}:{first_ten_god}_{second_ten_god}:exact_ten_god_domain_projection_collapsed")
            first_event_signature = tuple(
                first_rule.event_manifestations.get(domain, "")
                for domain in ("money", "career", "relationship", "marriage", "personality", "luck_activation")
            )
            second_event_signature = tuple(
                second_rule.event_manifestations.get(domain, "")
                for domain in ("money", "career", "relationship", "marriage", "personality", "luck_activation")
            )
            if first_event_signature == second_event_signature:
                issues.append(f"{pattern}:{first_ten_god}_{second_ten_god}:exact_ten_god_event_manifestation_collapsed")
            if TEN_GOD_EXACT_NUANCE[first_ten_god] not in " ".join(first_rule.domain_projections.values()):
                issues.append(f"{first_rule.rule_key}:missing_exact_nuance_in_domain_projection")
            if TEN_GOD_EXACT_NUANCE[second_ten_god] not in " ".join(second_rule.domain_projections.values()):
                issues.append(f"{second_rule.rule_key}:missing_exact_nuance_in_domain_projection")
            if first_rule.success_logic == second_rule.success_logic:
                issues.append(f"{pattern}:{first_ten_god}_{second_ten_god}:exact_ten_god_success_logic_collapsed")
            if first_rule.failure_logic == second_rule.failure_logic:
                issues.append(f"{pattern}:{first_ten_god}_{second_ten_god}:exact_ten_god_failure_logic_collapsed")

    wealth_resource = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_in"]
    if wealth_resource.relation_to_pattern != "pattern_controls_actor" or "재극" not in wealth_resource.action_nature:
        issues.append("direct_wealth_resource_direction_invalid")
    resource_wealth = GYEOKGUK_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]
    if resource_wealth.relation_to_pattern != "actor_controls_pattern" or "재극" not in resource_wealth.action_nature:
        issues.append("direct_resource_wealth_direction_invalid")
    if wealth_resource.center_effect == resource_wealth.center_effect:
        issues.append("wealth_resource_and_resource_wealth_not_differentiated")
    officer_wealth = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_jae"]
    if officer_wealth.relation_to_pattern != "actor_generates_pattern" or "생관" not in officer_wealth.action_nature:
        issues.append("direct_officer_wealth_direction_invalid")
    if "재물의 문서 근거" not in wealth_resource.role_in_pattern_logic or "문서 안정성" not in wealth_resource.excess_disease:
        issues.append("direct_wealth_resource_missing_pattern_specific_resource_logic")
    if "현실의 돈, 계약, 생활 요구" not in resource_wealth.role_in_pattern_logic or "문서, 학업, 보호 기반" not in resource_wealth.excess_disease:
        issues.append("direct_resource_wealth_missing_pattern_specific_wealth_logic")
    if "공식 직책과 사회적 신뢰" not in officer_wealth.role_in_pattern_logic or "직책 부담" not in officer_wealth.excess_disease:
        issues.append("direct_officer_wealth_missing_pattern_specific_wealth_logic")
    single_wealth_resource_signatures = {
        (
            rule.action_nature,
            rule.relation_to_pattern,
            rule.pattern_resolution_state,
            rule.role_grade,
            rule.center_effect,
            rule.role_in_pattern_logic,
            rule.excess_disease,
        )
        for rule in (wealth_resource, resource_wealth, officer_wealth)
    }
    if len(single_wealth_resource_signatures) != 3:
        issues.append("single_wealth_resource_officer_logic_collapsed")
    eating_stable_wealth = GYEOKGUK_TEN_GOD_ACTIONS["eating_god_pattern"]["jeong_jae"]
    hurting_stable_wealth = GYEOKGUK_TEN_GOD_ACTIONS["hurting_officer_pattern"]["jeong_jae"]
    direct_wealth_hurting = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["sang_gwan"]
    indirect_wealth_hurting = GYEOKGUK_TEN_GOD_ACTIONS["indirect_wealth_pattern"]["sang_gwan"]
    if "결과물이 생활 재정" not in eating_stable_wealth.excess_disease:
        issues.append("single_eating_god_wealth_missing_stable_output_income_signature")
    if "돌파성이 둔해진다" not in hurting_stable_wealth.excess_disease:
        issues.append("single_hurting_officer_wealth_missing_breakthrough_income_signature")
    if "정산과 신용" not in direct_wealth_hurting.excess_disease:
        issues.append("single_direct_wealth_output_missing_settlement_credit_signature")
    if "외부 돈" not in indirect_wealth_hurting.excess_disease:
        issues.append("single_indirect_wealth_output_missing_external_money_signature")
    siksang_saengjae_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (eating_stable_wealth, hurting_stable_wealth, direct_wealth_hurting, indirect_wealth_hurting)
    }
    if len(siksang_saengjae_signatures) != 4:
        issues.append("single_siksang_saengjae_pattern_logic_collapsed")
    direct_wealth_robbery = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["geob_jae"]
    indirect_wealth_robbery = GYEOKGUK_TEN_GOD_ACTIONS["indirect_wealth_pattern"]["geob_jae"]
    yangren_stable_wealth = GYEOKGUK_TEN_GOD_ACTIONS["yangren_peer_pattern"]["jeong_jae"]
    jianlu_stable_wealth = GYEOKGUK_TEN_GOD_ACTIONS["jianlu_peer_pattern"]["jeong_jae"]
    if "생활 재정과 소유권" not in direct_wealth_robbery.excess_disease:
        issues.append("single_direct_wealth_bigeop_missing_household_ownership_signature")
    if "외부 거래와 유동 자금" not in indirect_wealth_robbery.excess_disease:
        issues.append("single_indirect_wealth_bigeop_missing_external_capital_signature")
    if "주도권 충돌" not in yangren_stable_wealth.excess_disease:
        issues.append("single_yangren_wealth_missing_control_conflict_signature")
    if "자기 기준으로 돈과 소유" not in jianlu_stable_wealth.excess_disease:
        issues.append("single_jianlu_wealth_missing_self_standard_wealth_signature")
    bigeop_jaengjae_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_wealth_robbery, indirect_wealth_robbery, yangren_stable_wealth, jianlu_stable_wealth)
    }
    if len(bigeop_jaengjae_signatures) != 4:
        issues.append("single_bigeop_jaengjae_pattern_logic_collapsed")
    direct_wealth_officer = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_gwan"]
    direct_wealth_killing = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["pyeon_gwan"]
    direct_officer_wealth = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_jae"]
    seven_killings_wealth = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["jeong_jae"]
    if "직책과 책임" not in direct_wealth_officer.excess_disease or "고정 수입, 소유, 신용" not in direct_wealth_officer.timing_activation:
        issues.append("single_direct_wealth_officer_missing_credit_responsibility_signature")
    if "위험 책임" not in direct_wealth_killing.excess_disease or "보증, 규정, 법적 책임" not in direct_wealth_killing.excess_disease:
        issues.append("single_direct_wealth_killing_missing_risk_liability_signature")
    if "보수, 계약, 자원, 생활 기반이 직책을 안정" not in direct_officer_wealth.role_in_pattern_logic:
        issues.append("single_direct_officer_wealth_missing_official_base_signature")
    if "돈, 욕심, 거래" not in seven_killings_wealth.excess_disease or seven_killings_wealth.role_grade != "danger":
        issues.append("single_seven_killings_wealth_missing_jaesaengsal_danger_signature")
    jaesaenggwan_salingwan_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_wealth_officer, direct_wealth_killing, direct_officer_wealth, seven_killings_wealth)
    }
    if len(jaesaenggwan_salingwan_signatures) != 4:
        issues.append("single_jaesaenggwan_jaesaengsal_pattern_logic_collapsed")
    direct_officer_resource = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_in"]
    seven_killings_resource = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["jeong_in"]
    direct_resource_officer = GYEOKGUK_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_gwan"]
    indirect_resource_killing = GYEOKGUK_TEN_GOD_ACTIONS["indirect_resource_pattern"]["pyeon_gwan"]
    if "직책보다 문서, 절차, 명분" not in direct_officer_resource.excess_disease:
        issues.append("single_direct_officer_resource_missing_procedure_reputation_signature")
    if "강한 압박과 위험" not in seven_killings_resource.role_in_pattern_logic or "자격, 문서, 시험" not in seven_killings_resource.timing_activation:
        issues.append("single_seven_killings_resource_missing_salin_signature")
    if "인성의 문서와 자격이 실제 직책" not in direct_resource_officer.role_in_pattern_logic:
        issues.append("single_direct_resource_officer_missing_resource_to_office_signature")
    if "책임과 압박이 인성 기반을 소모" not in indirect_resource_killing.excess_disease:
        issues.append("single_indirect_resource_killing_missing_pressure_resource_signature")
    gwanin_salin_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_officer_resource, seven_killings_resource, direct_resource_officer, indirect_resource_killing)
    }
    if len(gwanin_salin_signatures) != 4:
        issues.append("single_gwanin_salin_pattern_logic_collapsed")
    officer_output = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["sang_gwan"]
    killing_output = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["sik_sin"]
    food_killing = GYEOKGUK_TEN_GOD_ACTIONS["eating_god_pattern"]["pyeon_gwan"]
    hurting_officer = GYEOKGUK_TEN_GOD_ACTIONS["hurting_officer_pattern"]["jeong_gwan"]
    if "편관의 압박을 실무" not in killing_output.role_in_pattern_logic or "식신제살의 약" not in killing_output.excess_disease:
        issues.append("single_seven_killings_food_missing_siksin_jesal_signature")
    if "식신의 생산성을 시험" not in food_killing.role_in_pattern_logic or food_killing.pattern_resolution_state != "conditional_seonggyeok":
        issues.append("single_eating_god_killing_missing_responsibility_test_signature")
    if "직책과 공식 신뢰를 직접 건드리는" not in officer_output.role_in_pattern_logic or "상관견관" not in officer_output.excess_disease:
        issues.append("single_direct_officer_output_missing_sanggwan_gyeongwan_signature")
    if "공식 질서와 평가 기준" not in hurting_officer.role_in_pattern_logic or "상관견관의 긴장" not in hurting_officer.excess_disease:
        issues.append("single_hurting_officer_officer_missing_official_tension_signature")
    output_officer_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (killing_output, food_killing, officer_output, hurting_officer)
    }
    if len(output_officer_signatures) != 4:
        issues.append("single_siksin_jesal_sanggwan_gyeongwan_pattern_logic_collapsed")
    eating_indirect_resource = GYEOKGUK_TEN_GOD_ACTIONS["eating_god_pattern"]["pyeon_in"]
    eating_direct_resource = GYEOKGUK_TEN_GOD_ACTIONS["eating_god_pattern"]["jeong_in"]
    hurting_direct_resource = GYEOKGUK_TEN_GOD_ACTIONS["hurting_officer_pattern"]["jeong_in"]
    direct_resource_food = GYEOKGUK_TEN_GOD_ACTIONS["direct_resource_pattern"]["sik_sin"]
    indirect_resource_food = GYEOKGUK_TEN_GOD_ACTIONS["indirect_resource_pattern"]["sik_sin"]
    if "편인도식" not in eating_indirect_resource.excess_disease or eating_indirect_resource.role_grade != "breaker":
        issues.append("single_eating_god_indirect_resource_missing_dosik_breaker_signature")
    if "생산 속도" not in eating_direct_resource.excess_disease or eating_direct_resource.pattern_resolution_state != "pagyeok_risk":
        issues.append("single_eating_god_direct_resource_missing_production_delay_signature")
    if "상관패인" not in hurting_direct_resource.excess_disease or hurting_direct_resource.pattern_resolution_state != "byeongyak_medicine":
        issues.append("single_hurting_officer_resource_missing_sanggwan_paein_signature")
    if "학업, 자격, 문서 기반" not in direct_resource_food.timing_activation or "결과물" not in direct_resource_food.excess_disease:
        issues.append("single_direct_resource_food_missing_resource_output_signature")
    if "특수 지식과 몰입" not in indirect_resource_food.excess_disease or "기술, 서비스, 결과물" not in indirect_resource_food.timing_activation:
        issues.append("single_indirect_resource_food_missing_specialized_output_signature")
    dosik_resource_output_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (
            eating_indirect_resource,
            eating_direct_resource,
            hurting_direct_resource,
            direct_resource_food,
            indirect_resource_food,
        )
    }
    if len(dosik_resource_output_signatures) != 5:
        issues.append("single_dosik_resource_output_pattern_logic_collapsed")

    direct_resource_peer = GYEOKGUK_TEN_GOD_ACTIONS["direct_resource_pattern"]["bi_gyeon"]
    indirect_resource_robbery = GYEOKGUK_TEN_GOD_ACTIONS["indirect_resource_pattern"]["geob_jae"]
    jianlu_resource = GYEOKGUK_TEN_GOD_ACTIONS["jianlu_peer_pattern"]["jeong_in"]
    yangren_indirect_resource = GYEOKGUK_TEN_GOD_ACTIONS["yangren_peer_pattern"]["pyeon_in"]
    if "인비과중" not in direct_resource_peer.excess_disease or "정식 학습, 자격, 보호 기반" not in direct_resource_peer.excess_disease:
        issues.append("single_direct_resource_peer_missing_inbi_overload_signature")
    if "특수 지식과 자기 기준" not in indirect_resource_robbery.excess_disease:
        issues.append("single_indirect_resource_robbery_missing_specialized_inbi_signature")
    if "자기 기반이 공부와 보호 논리" not in jianlu_resource.excess_disease:
        issues.append("single_jianlu_resource_missing_self_base_resource_signature")
    if "강한 주도권에 보호 논리" not in yangren_indirect_resource.excess_disease:
        issues.append("single_yangren_resource_missing_assertive_resource_signature")
    inbi_overload_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_resource_peer, indirect_resource_robbery, jianlu_resource, yangren_indirect_resource)
    }
    if len(inbi_overload_signatures) != 4:
        issues.append("single_inbi_overload_pattern_logic_collapsed")

    direct_officer_killing = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["pyeon_gwan"]
    killing_officer = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["jeong_gwan"]
    killing_killing = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["pyeon_gwan"]
    if "관살혼잡" not in direct_officer_killing.excess_disease or "공식 질서에 강한 압박" not in direct_officer_killing.excess_disease:
        issues.append("single_direct_officer_killing_missing_mixed_officer_signature")
    if "관살과중" not in killing_officer.excess_disease or "권한보다 압박" not in killing_officer.excess_disease:
        issues.append("single_killing_officer_missing_overload_signature")
    if "편관 중첩" not in killing_killing.timing_activation or killing_killing.role_grade != "core_overload":
        issues.append("single_killing_killing_missing_repeated_killing_signature")
    gwansal_overload_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_officer_killing, killing_officer, killing_killing)
    }
    if len(gwansal_overload_signatures) != 3:
        issues.append("single_gwansal_mixed_overload_pattern_logic_collapsed")

    direct_wealth_self = GYEOKGUK_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_jae"]
    indirect_wealth_self = GYEOKGUK_TEN_GOD_ACTIONS["indirect_wealth_pattern"]["pyeon_jae"]
    eating_food = GYEOKGUK_TEN_GOD_ACTIONS["eating_god_pattern"]["sik_sin"]
    hurting_hurting = GYEOKGUK_TEN_GOD_ACTIONS["hurting_officer_pattern"]["sang_gwan"]
    if "재다신약" not in direct_wealth_self.excess_disease or "생활 재정과 소유 기준" not in direct_wealth_self.excess_disease:
        issues.append("single_direct_wealth_self_missing_jaeda_household_signature")
    if "재다신약" not in indirect_wealth_self.excess_disease or "거래와 확장" not in indirect_wealth_self.excess_disease:
        issues.append("single_indirect_wealth_self_missing_jaeda_expansion_signature")
    if "안정된 생산이 반복과 안주" not in eating_food.excess_disease:
        issues.append("single_eating_god_self_missing_repetition_overload_signature")
    if "식상과다" not in hurting_hurting.excess_disease or "말, 기획, 반발성" not in hurting_hurting.excess_disease:
        issues.append("single_hurting_officer_self_missing_expression_overload_signature")
    wealth_output_overload_signatures = {
        (
            rule.action_nature,
            rule.role_grade,
            rule.pattern_resolution_state,
            rule.relation_to_pattern,
            rule.role_in_pattern_logic,
            rule.excess_disease,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (direct_wealth_self, indirect_wealth_self, eating_food, hurting_hurting)
    }
    if len(wealth_output_overload_signatures) != 4:
        issues.append("single_jaeda_siksang_overload_pattern_logic_collapsed")
    if officer_output.excess_disease == killing_output.excess_disease:
        issues.append("sanggwan_gyeongwan_and_siksin_jesal_collapsed")
    officer_resource = GYEOKGUK_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_in"]
    killing_resource = GYEOKGUK_TEN_GOD_ACTIONS["seven_killings_pattern"]["jeong_in"]
    resource_officer = GYEOKGUK_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_gwan"]
    if len({officer_resource.excess_disease, killing_resource.excess_disease, resource_officer.excess_disease}) != 3:
        issues.append("gwanin_salin_resource_gwanin_collapsed")
    missing_classical_tags = MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS - found_classical_tags
    for tag in sorted(missing_classical_tags):
        issues.append(f"missing_mandatory_single_classical_action:{tag}")
    missing_mechanic_tags = MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS - set(CLASSICAL_ACTION_MECHANICS)
    for tag in sorted(missing_mechanic_tags):
        issues.append(f"missing_mandatory_single_classical_action_mechanic:{tag}")
    missing_mechanic_text_tags = set(CLASSICAL_ACTION_MECHANICS) - set(CLASSICAL_ACTION_MECHANIC_TEXTS)
    for tag in sorted(missing_mechanic_text_tags):
        issues.append(f"missing_classical_action_mechanic_text:{tag}")
    for tag, pattern_signatures in core_tag_pattern_signatures.items():
        if len(pattern_signatures) <= 1:
            continue
        unique_signatures = {
            signature
            for signatures in pattern_signatures.values()
            for signature in signatures
        }
        if len(unique_signatures) < len(pattern_signatures):
            issues.append(f"single_core_classical_action_pattern_signature_collapsed:{tag}")
    for ten_god, pattern_signatures in ten_god_pattern_signatures.items():
        if set(pattern_signatures) != expected_patterns:
            missing = expected_patterns - set(pattern_signatures)
            issues.append(f"single_ten_god_missing_pattern_signatures:{ten_god}:{','.join(sorted(missing))}")
            continue
        if len(set(pattern_signatures.values())) < len(expected_patterns):
            issues.append(f"single_ten_god_pattern_signature_collapsed:{ten_god}")
    return issues
