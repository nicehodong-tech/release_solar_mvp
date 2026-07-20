"""Gyeokguk-specific dual ten-god action dictionary.

This layer extends the single action dictionary from
``pattern + acting ten-god`` to ``pattern + first ten-god + second ten-god``.
The order is deliberate: the first ten-god is the already observed action, and
the second ten-god is the additional actor that redirects, reinforces, or
breaks that action.
"""

from __future__ import annotations

from .constants import TEN_GOD_GROUPS
from .models import (
    BranchInteraction,
    ElementProfile,
    GyeokgukDualTenGodActionMatch,
    GyeokgukDualTenGodActionRule,
    MonthGovernanceProfile,
    PositionSignal,
    TenGodProfile,
)
from .gyeokguk_ten_god_actions import (
    GYEOKGUK_ACTION_JUDGMENT_ORDER,
    GYEOKGUK_TEN_GOD_ACTIONS,
    MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS,
    PATTERN_CENTER_BY_PATTERN,
    PATTERN_LENS,
    ROLE_GRADE_VERDICT,
    TEN_GOD_EXACT_ACTION_PROFILE,
    TEN_GOD_EXACT_NUANCE,
    TEN_GODS,
    GROUP_CONTROLS,
    GROUP_GENERATES,
    CLASSICAL_ACTION_MECHANICS,
    CLASSICAL_ACTION_MECHANIC_TEXTS,
    classical_action_mechanic_codes,
    gyeokguk_action_judgment_basis_codes,
    gyeokguk_action_context_adjustment,
    gyeokguk_ten_god_action_rule,
)


GYEOKGUK_DUAL_TEN_GOD_ACTION_VERSION = "gyeokguk_dual_ten_god_actions_v1"

SUPPORTIVE_GRADES = {
    "core",
    "support",
    "strong_regulator",
    "regulator",
    "conditioned_support",
    "source",
}

MIXED_GRADES = {
    "mixed",
    "core_overload",
    "regulator_or_breaker",
    "breaker_or_medicine",
}

BURDEN_GRADES = {
    "burden",
    "breaker",
    "danger",
}

CHAIN_RESOLUTION_STATE = {
    "constructive_chain": "seonggyeok_chain",
    "supportive_chain": "seonggyeok_support_chain",
    "medicine_chain": "byeongyak_medicine_chain",
    "mediated_tension_chain": "mediated_condition_chain",
    "conditional_chain": "conditional_chain",
    "mixed_chain": "mixed_chain",
    "risk_chain": "pagyeok_chain",
    "compounded_burden_chain": "compounded_disease_chain",
    "disease_chain": "disease_chain",
}

CHAIN_RESOLUTION_LABELS = {
    "seonggyeok_chain": "성격 연쇄",
    "seonggyeok_support_chain": "성격 보조 연쇄",
    "byeongyak_medicine_chain": "병약 조절 연쇄",
    "mediated_condition_chain": "매개 조건 연쇄",
    "conditional_chain": "조건부 연쇄",
    "mixed_chain": "혼합 연쇄",
    "pagyeok_chain": "파격 연쇄",
    "compounded_disease_chain": "병증 중첩",
    "disease_chain": "병증 연쇄",
}

def _chain_resolution_state(chain_grade: str) -> str:
    return CHAIN_RESOLUTION_STATE.get(chain_grade, "mixed_chain")

FIT_PRESSURE_STATES = {"harms_month_command", "burdensome_by_month_command"}
FIT_SUPPORT_STATES = {"supports_month_command", "usable_by_month_command"}

DUAL_FUNCTIONAL_ROLE_LABELS = {
    "supporting_god": "상신",
    "rescuing_god": "구신",
    "adverse_god": "기신",
    "conditional_god": "조건부 작용",
    "inactive": "미발동",
}

MANDATORY_DUAL_CLASSICAL_ACTION_TAGS = set(MANDATORY_SINGLE_CLASSICAL_ACTION_TAGS)

CORE_DUAL_CLASSICAL_TAGS_REQUIRING_SPECIFIC_LENS = {
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

MANDATORY_PATTERN_CENTER_BRIDGE_KEYS = {
    "resource_generates_peer_generates_output",
    "peer_generates_output_generates_wealth",
    "output_generates_wealth_generates_officer",
    "wealth_generates_officer_generates_resource",
    "officer_generates_resource_generates_peer",
    "officer_controls_peer_controls_wealth",
    "peer_controls_wealth_controls_resource",
    "wealth_controls_resource_controls_output",
    "resource_controls_output_controls_officer",
    "output_controls_officer_controls_peer",
}

TEN_GOD_DOMAIN_WEIGHTS = {
    "bi_gyeon": {"personality": 4.2, "career": 2.4, "relationship": 2.2},
    "geob_jae": {"relationship": 4.0, "money": 3.7, "career": 2.0},
    "sik_sin": {"money": 3.8, "career": 3.5, "personality": 2.3},
    "sang_gwan": {"career": 3.6, "personality": 3.4, "relationship": 2.5, "reputation": 1.7},
    "pyeon_jae": {"money": 4.3, "relationship": 2.8, "career": 2.4},
    "jeong_jae": {"money": 4.4, "marriage": 3.1, "career": 2.2},
    "pyeon_gwan": {"career": 4.1, "personality": 3.1, "reputation": 2.8, "relationship": 1.5},
    "jeong_gwan": {"career": 4.0, "reputation": 3.8, "marriage": 3.0, "personality": 1.6},
    "pyeon_in": {"personality": 4.0, "career": 2.9, "relationship": 2.1},
    "jeong_in": {"career": 3.2, "personality": 2.8, "marriage": 2.7, "reputation": 1.4},
}

PATTERN_DOMAIN_BIAS = {
    "jianlu_peer_pattern": {"personality": 1.5, "career": 1.0, "money": 0.8},
    "yangren_peer_pattern": {"career": 1.4, "personality": 1.2, "relationship": 0.9},
    "eating_god_pattern": {"money": 1.4, "career": 1.2, "personality": 0.8},
    "hurting_officer_pattern": {"career": 1.4, "reputation": 1.2, "relationship": 0.8},
    "indirect_wealth_pattern": {"money": 1.6, "career": 0.9, "relationship": 0.8},
    "direct_wealth_pattern": {"money": 1.7, "marriage": 0.9, "career": 0.8},
    "seven_killings_pattern": {"career": 1.7, "reputation": 1.0, "personality": 0.9},
    "direct_officer_pattern": {"career": 1.7, "reputation": 1.3, "marriage": 0.9},
    "indirect_resource_pattern": {"personality": 1.4, "career": 1.1, "relationship": 0.7},
    "direct_resource_pattern": {"career": 1.3, "personality": 1.2, "marriage": 0.8},
}

PATTERN_PAIR_CATEGORY_LENS = {
    "wealth_controls_resource": {
        "direct_wealth_pattern": {
            "effect": "재격에서는 인성의 보류, 명분, 생각을 현실 소유와 정산 기준으로 눌러 재물 결정력을 살린다.",
            "risk": "제어가 과하면 문서, 보호자, 학업, 자격 문제가 재물 문제에 함께 걸린다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 외부 거래와 시장 요구가 편중된 생각을 깨워 돈의 회전과 거래 판단으로 끌어낸다.",
            "risk": "과하면 신뢰, 계약서, 보호 장치가 약해져 거래 손실이 커질 수 있다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 재성이 격의 중심인 인성을 직접 건드린다. 인성이 과할 때는 실행을 끌어내는 약이 되지만, 인성이 약하면 문서와 보호 기반을 손상한다.",
            "risk": "현실 요구가 지나치면 학업, 자격, 문서, 상사의 보호가 끊기는 쪽으로 나타난다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 재성이 특수한 몰입과 고립된 판단을 현실 요구로 끌어내 시장화의 계기를 만든다.",
            "risk": "편인의 집중이 약하면 현실 요구가 전문성을 깨뜨리고 산만한 거래 문제로 바뀐다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 재극인이 관인상생의 보호축을 건드린다. 재성이 관을 받치는 힘이 충분하면 직책의 현실 근거가 생기지만, 인성이 손상되면 명분과 문서가 약해진다.",
            "risk": "관의 신뢰를 받쳐야 할 문서와 자격이 흔들리면 평판과 책임 문제가 동시에 커진다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 재극인이 살인상생의 보호 장치를 건드린다. 살이 과할 때는 현실 판단이 필요하지만, 인성이 약하면 압박을 받아낼 장치가 줄어든다.",
            "risk": "재성이 살을 생하고 인성을 치면 압박, 손실, 문서 부담이 함께 커진다.",
        },
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 재성이 인성을 제어하면 강한 자기 기반을 명분과 보호 안에만 묶어두지 않고 현실 재정과 소유 판단으로 끌어낸다.",
            "risk": "재성이 약하면 인비가 두터워져 실행이 늦고, 재성이 과하면 자격·문서보다 돈 문제가 앞서 판단이 거칠어진다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 재성이 인성을 제어해 강한 기세를 현실 계산과 손익 판단으로 끌어낸다.",
            "risk": "제어가 거칠면 보호 장치 없이 돈과 승부가 앞서 충돌, 손실, 지분 문제가 커진다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 재성이 인성을 제어해 도식의 병을 낮춘다. 준비와 명분이 생산을 막을 때 현실 수입 요구가 결과물을 밖으로 끌어낸다.",
            "risk": "재성이 과하면 안정된 생산보다 돈의 요구가 앞서 식신의 꾸준함이 흔들린다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 재성이 인성을 제어해 문서와 명분으로 묶인 표현을 시장성과 거래 판단으로 돌린다.",
            "risk": "재성이 과하면 표현이 정제되기보다 돈과 확장 쪽으로 급해져 평판과 계약이 흔들릴 수 있다.",
        },
    },
    "wealth_generates_officer": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 재성이 관성을 생할 때 강한 자기 기반이 돈을 거쳐 직책과 공식 책임으로 정리된다.",
            "risk": "관성이 약하면 돈은 생겨도 사회적 자리로 묶이지 않고, 관성이 과하면 독립성이 책임 부담에 눌린다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 재성이 관살을 생해 강한 주도권을 권한, 경쟁, 책임의 자리로 밀어 올린다.",
            "risk": "식신이나 인성이 받치지 않으면 재생살로 기울어 돈이 권한보다 위험 부담을 키운다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 생산물이 재성으로 바뀐 뒤 관성으로 이어질 때 결과물이 직책과 평가의 근거가 된다.",
            "risk": "관성이 과하면 편안한 생산성이 절차와 책임에 묶이고, 재성이 약하면 결과물이 평가로 올라가지 못한다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 재성이 관성을 생해 표현과 기획의 시장성을 직책과 공식 평가로 연결한다.",
            "risk": "재성이 매개하지 못하면 상관이 관을 바로 쳐 상관견관의 병이 먼저 드러난다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 수입과 소유 기준이 직책, 신용, 책임으로 올라간다. 재물이 공적 책임으로 전환되는 구조다.",
            "risk": "일간이 약하거나 관이 과하면 돈이 권한이 아니라 부담과 책임으로 바뀐다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 외부 자원, 거래처, 투자 기회가 공적 신뢰와 사업 책임으로 확장된다.",
            "risk": "편재가 편관을 생하면 큰 거래가 위험 부담과 강한 압박으로 바뀔 수 있다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 재성이 격의 중심인 관을 생한다. 현실 기반이 직책과 평판을 안정시키는 방향이다.",
            "risk": "재가 탁하거나 과하면 관의 청정성이 흐려져 책임은 커지고 명예는 무거워진다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 재성이 살을 생한다. 충분히 제어되면 큰 책임과 권한이 되지만, 제어가 약하면 압박을 키운다.",
            "risk": "식신이나 인성이 받치지 않으면 재생살이 되어 돈, 책임, 위험이 함께 커진다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 재성이 관성을 생한 뒤 그 관성이 다시 인성으로 돌아오는지 본다. 현실 기반이 책임을 만들고, 그 책임이 문서와 자격을 받쳐야 격이 안정된다.",
            "risk": "재성이 인성을 먼저 손상하거나 관성이 인성으로 돌아오지 못하면 문서, 학업, 보호 기반이 흔들린다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 재성이 관살을 생해 특수한 몰입을 실제 책임과 전문 영역으로 몰아간다.",
            "risk": "관살이 과하면 편인의 전문성은 보호가 아니라 고립된 압박과 불안정한 책임으로 바뀐다.",
        },
    },
    "output_generates_wealth": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 강한 자기 기반이 식상으로 빠지고, 그 결과물이 재성으로 이어질 때 재물이 생긴다. 비겁의 힘을 밖으로 빼내는 통로가 핵심이다.",
            "risk": "식상이 약하면 강한 기운이 재성으로 가지 못하고 경쟁과 고집으로 남아 재물을 압박한다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 거친 주도권이 식상으로 배출되고 재성으로 이어질 때 추진력이 돈으로 바뀐다.",
            "risk": "상관으로 과하게 빠지면 속도와 확장은 크지만 회수, 정산, 평판이 흔들린다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 격의 중심인 생산물이 재물로 넘어간다. 반복 가능한 결과물이 수입의 근거가 된다.",
            "risk": "재성이 약하거나 비겁이 개입하면 만든 것은 있어도 소유와 정산이 흐려진다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 표현, 기획, 돌파성이 시장성과 돈으로 넘어간다. 재성이 받치면 재주가 수입화된다.",
            "risk": "상관이 과하면 돈보다 말과 충돌이 앞서 계약과 평판을 흔든다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 식상이 재성의 공급원이 된다. 기술과 결과물이 안정 수입을 만드는 방식이다.",
            "risk": "결과물이 약하면 재성은 있어도 수입의 지속성이 떨어진다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 식상이 외부 거래와 활동 자금을 만든다. 영업, 기획, 서비스가 돈의 입구가 된다.",
            "risk": "상관 쪽으로 과하면 확장은 빠르나 회수와 정산이 늦어진다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 식상이 재성을 생하면 직책에서 만든 성과가 보상과 생활 기반으로 내려온다.",
            "risk": "상관이 강하면 성과보다 조직 질서와의 마찰이 앞서 보상이 평판 문제로 바뀔 수 있다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 식상이 재성을 생하면 압박을 처리한 결과가 돈과 실적 보상으로 바뀐다.",
            "risk": "재성이 다시 살을 생하면 수입이 새로운 책임과 위험 부담을 키우는 순환이 생긴다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 식상이 재성을 생할 때 배운 것, 자격, 문서 기반이 결과물과 수입으로 현실화된다.",
            "risk": "인성이 과하면 결과물이 늦고, 재성이 과하면 문서와 학업 기반이 돈의 요구에 눌린다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 식상이 재성을 생할 때 특수 지식과 몰입이 상품, 서비스, 비정형 수익으로 나온다.",
            "risk": "식상이 약하면 전문성은 깊어도 시장에 내놓는 힘이 부족하고, 재성이 과하면 집중이 흩어진다.",
        },
    },
    "officer_generates_resource": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 관성이 인성을 생하면 강한 자기 기반이 직책을 거쳐 명분과 자격으로 안정된다.",
            "risk": "인성이 과하면 독립성에 명분이 붙어 고집이 두꺼워지고, 관성이 약하면 책임이 자격으로 이어지지 못한다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 관살이 인성을 생해 거친 기세를 자격, 문서, 명분의 보호 장치로 흡수한다.",
            "risk": "인성이 약하면 관살의 압박이 보호로 넘어가지 못하고, 인성이 과하면 양인의 기세에 명분만 더해져 충돌이 커진다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 관성이 인성을 생하면 생산물이 직책과 문서 절차를 거쳐 공식성을 얻는다.",
            "risk": "인성이 과하면 도식으로 돌아가 생산 속도를 막고, 관성이 과하면 결과물보다 책임이 앞선다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 관성이 인성을 생할 때 상관의 반발성과 표현이 문서, 자격, 품격으로 정리될 수 있다.",
            "risk": "관성이 먼저 강하면 상관견관의 긴장이 생기고, 인성이 약하면 표현을 정제하지 못해 평판 손상이 남는다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 관성이 인성을 생하면 재물에서 생긴 책임이 문서, 자격, 보호 장치로 안정된다.",
            "risk": "인성이 과하면 재물 실행이 절차와 명분에 묶이고, 관성이 과하면 돈이 책임과 문서 부담으로 굳어진다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 관성이 인성을 생해 외부 거래와 확장 자금을 신용, 문서, 자격의 장치로 묶는다.",
            "risk": "인성이 약하면 큰 거래를 보호할 문서와 명분이 부족하고, 관살이 과하면 확장이 압박으로 바뀐다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 관이 인성을 생해 직책이 문서, 자격, 명분으로 안정된다.",
            "risk": "인성이 과하면 책임을 실행하기보다 명분과 절차가 늘어난다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 살이 인성으로 화하여 압박이 자격, 공부, 보호 장치로 흡수된다.",
            "risk": "인성이 약하면 압박이 보호로 넘어가지 못하고 긴장과 소모로 남는다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 관성이 인성을 생해 격의 중심을 보강한다. 직책과 제도가 자격의 근거가 된다.",
            "risk": "관이 과하면 인성은 보호가 아니라 책임을 버티는 장치로 소모된다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 관살이 특수 전문성의 이유가 된다. 압박이 특정 공부와 기술 몰입을 만든다.",
            "risk": "편관과 편인이 과하면 고립된 압박과 불안정한 전문성으로 기울 수 있다.",
        },
    },
    "output_controls_officer": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 식상이 관성을 제어하면 강한 자기 기반이 조직과 책임을 성과로 조절한다.",
            "risk": "상관이 과하면 독립성과 표현이 제도권을 정면으로 쳐 직책과 평판을 흔든다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 식상이 관살을 제어해 거친 주도권과 압박을 실무, 기술, 결과물로 다스린다.",
            "risk": "식신이 약하면 압박을 처리하지 못하고, 상관이 과하면 권위 충돌과 사고성이 커진다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 식상으로 살을 제어하는지가 핵심이다. 식신은 압박을 실무와 기술로 다스리고, 상관은 강한 제도권 압박을 돌파력으로 꺾는다.",
            "risk": "식신이 약하면 책임만 커지고, 상관이 과하면 위험을 제어하기보다 권위와 정면으로 충돌한다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 식상이 관을 건드리는 방식이 정교해야 한다. 식신은 직책의 부담을 실제 성과로 풀 수 있지만, 상관은 상관견관으로 평판과 직책을 손상하기 쉽다.",
            "risk": "상관이 강하고 인성이나 재성이 받치지 못하면 말, 기획, 반발성이 공식 평가를 흔든다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 식신의 생산력이 관살의 압박을 감당하는 실무력으로 바뀐다. 만들어낸 결과물이 책임을 처리하는 근거가 된다.",
            "risk": "결과물이 약한 상태에서 관살만 강하면 해야 할 일과 책임이 생산력을 누른다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 표현과 돌파성이 관성을 건드린다. 재성으로 시장성을 얻거나 인성으로 품격을 얻으면 개혁성이 되지만, 그대로 관을 치면 상관견관의 병이 된다.",
            "risk": "제도권과의 충돌이 커지면 능력보다 말, 태도, 평판 문제가 먼저 드러난다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 식상이 관성을 제어하면 재물에서 생긴 책임을 실제 성과와 처리력으로 풀어낸다.",
            "risk": "상관이 과하면 재물과 직책 사이의 질서가 흔들려 계약, 평판, 책임 문제가 생긴다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 식상이 관성을 제어해 외부 거래에서 생긴 압박과 책임을 영업력, 기획력, 처리력으로 다룬다.",
            "risk": "상관이 과하면 거래 확장과 제도권 책임이 충돌해 회수, 계약, 평판이 흔들린다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 식상이 관성을 제어하면 자격과 문서 기반이 책임을 실제 결과물로 풀어내는 힘을 얻는다.",
            "risk": "상관이 과하면 문서와 명분의 보호를 넘어 제도권 질서를 건드려 인성의 안정성이 약해진다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 식상이 관살을 제어해 특수 지식과 몰입을 압박 상황의 해결력으로 바꾼다.",
            "risk": "식상이 약하면 편관의 압박이 전문성 안에 갇히고, 상관이 과하면 비정형 판단이 권위 충돌로 드러난다.",
        },
    },
    "peer_controls_wealth": {
        "eating_god_pattern": {
            "effect": "식신격에서는 비겁이 재성을 제어하면 생산물로 생긴 돈을 사람과 몫의 문제로 나누게 된다.",
            "risk": "비겁이 과하면 만든 결과보다 동업자, 가족, 동료의 지분 문제가 먼저 커진다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 비겁이 재성을 제어하면 표현과 기획으로 번 돈에 경쟁자와 지분 문제가 붙는다.",
            "risk": "겁재가 강하면 말과 확장이 빠른 만큼 정산, 공동 수익, 권리 다툼이 커진다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 비겁이 격의 중심인 재성을 직접 나눈다. 비견은 공동 소유와 분재로, 겁재는 지분 경쟁과 쟁재로 드러난다.",
            "risk": "친한 사람, 동업자, 가족 사이에서 소유권과 정산 기준이 흐려지면 재물의 안정성이 무너진다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 비겁이 외부 거래와 확장 자금을 건드린다. 사람을 통해 기회가 열리지만, 사람 때문에 회수와 몫 문제가 커질 수도 있다.",
            "risk": "겁재가 강하면 사업 자금, 투자금, 동업 지분에서 손실과 분쟁이 생기기 쉽다.",
        },
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 강한 자기 기반이 재성을 장악하려 한다. 재물이 생기면 내 몫을 지키려는 힘이 먼저 움직인다.",
            "risk": "관성의 기준이 약하면 재물보다 경쟁과 분배 문제가 앞서 재성이 탁해진다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 비겁의 기세가 재성을 강하게 친다. 관살이 제어하면 큰 추진력이 되지만, 제어가 약하면 겁재쟁재가 된다.",
            "risk": "강한 주도권이 돈 문제와 결합하면 동업, 지분, 손실 책임이 급격히 커진다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 비겁이 재성을 제어하면 직책과 평판을 받쳐야 할 현실 기반에 사람과 몫 문제가 끼어든다.",
            "risk": "관성이 정리하지 못하면 동료, 경쟁자, 가족의 돈 문제가 공식 책임과 평판까지 흔든다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 비겁이 재성을 제어하면 압박 속에서 돈과 사람의 주도권 문제가 함께 올라온다.",
            "risk": "겁재가 강하면 위험한 책임, 손실 부담, 동업 갈등이 한꺼번에 커질 수 있다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 비겁이 재성을 제어하면 문서와 자격을 현실 수입으로 바꾸는 과정에 자기 기준과 주변 몫이 개입한다.",
            "risk": "비겁이 과하면 재성이 인성을 조절하기 전에 사람 문제와 분배 문제가 먼저 커진다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 비겁이 재성을 제어하면 특수 전문성을 수익화하는 과정에 지분, 동료, 공동 작업 문제가 들어온다.",
            "risk": "겁재가 강하면 비정형 수익 구조에서 권리와 정산이 흐려질 수 있다.",
        },
    },
    "resource_controls_output": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 인성이 식상을 제어하면 강한 자기 기반이 결과물로 빠져나가는 속도를 늦춘다.",
            "risk": "인성이 과하면 강한 기운이 안에 머물러 실행보다 명분과 자기 확신이 앞선다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 인성이 식상을 제어해 거친 기세가 결과물로 배출되는 통로를 조절한다.",
            "risk": "제어가 과하면 실무와 결과물 대신 명분, 보호, 고집이 강해져 충돌을 풀지 못한다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 인성이 식신을 제어하면 도식 여부가 핵심이다. 적절한 인성은 품질과 자격을 주지만, 과하면 생산을 막는다.",
            "risk": "편인이 강하면 만들고 내놓아야 할 것이 생각, 준비, 보류 안에서 멈춘다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 인성이 상관을 정제한다. 인성이 알맞으면 상관패인이 되어 표현이 품격과 문서성을 얻는다.",
            "risk": "인성이 과하면 상관의 속도와 돌파력이 꺾이고, 약하면 상관의 반발성이 정리되지 않는다.",
        },
        "direct_resource_pattern": {
            "effect": "인수격에서는 인성이 이미 격의 중심이므로 식상을 누르는 힘이 더 강하게 작동한다. 문서와 명분은 좋지만 결과물은 늦어질 수 있다.",
            "risk": "재성이나 관성이 길을 열지 않으면 공부와 보호가 실행을 대신하는 병이 된다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 편중된 이해력과 몰입이 식상을 누른다. 특수 전문성은 깊어지지만 시장에 내놓는 속도는 늦어진다.",
            "risk": "식상이 약하면 편인의 고립과 도식이 강해져 재주가 상품으로 나오지 못한다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 인성이 식상을 제어하면 재물을 만드는 결과물의 속도와 형식이 문서, 자격, 명분에 묶인다.",
            "risk": "인성이 과하면 수입의 근거가 되는 생산이 늦어지고, 재물은 있어도 실제 공급력이 약해진다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 인성이 식상을 제어해 외부 거래를 만드는 표현과 활동성을 문서와 검토 쪽으로 늦춘다.",
            "risk": "제어가 과하면 확장 기회를 검토만 하다가 놓치고, 약하면 계약과 보호 장치 없이 움직인다.",
        },
        "direct_officer_pattern": {
            "effect": "정관격에서는 인성이 식상을 제어해 직책을 흔들 수 있는 말과 결과물을 문서, 절차, 품격으로 정리한다.",
            "risk": "인성이 과하면 책임을 성과로 풀기보다 절차와 명분이 늘어나고, 약하면 상관견관을 막지 못한다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서는 인성이 식상을 제어하면 압박을 처리할 실무 속도를 늦추는 대신 보호 장치와 문서 근거를 만든다.",
            "risk": "편인이 과하면 식신제살의 실무력이 막혀 압박을 실제 처리로 풀지 못한다.",
        },
    },
    "officer_controls_peer": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 관성이 강한 비겁을 정리한다. 자기 기준과 경쟁심이 제도권 책임으로 묶일 때 사회적 자리가 잡힌다.",
            "risk": "관성이 약하면 자기 주장만 남고, 관성이 과하면 독립성이 압박으로 눌린다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 관살이 양인의 기세를 제어하는 핵심 약이다. 거친 주도권이 권한과 책임으로 바뀐다.",
            "risk": "관살이 약하면 충돌이 남고, 편관이 과하면 위험한 책임과 압박으로 나타난다.",
        },
        "direct_wealth_pattern": {
            "effect": "정재격에서는 관성이 비겁을 제어해 재성의 소유권을 지킨다. 돈을 놓고 사람이 끼는 문제를 규칙과 책임으로 정리한다.",
            "risk": "관성이 약하면 친분과 몫 문제가 재물을 흔들고, 관성이 과하면 재물이 책임 부담으로 묶인다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서는 관성이 외부 거래의 사람 문제를 정리한다. 투자, 영업, 동업을 신용과 계약 기준으로 묶는 작용이다.",
            "risk": "관성이 약하면 확장한 만큼 회수와 지분 문제가 커진다.",
        },
    },
    "resource_generates_peer": {
        "direct_resource_pattern": {
            "effect": "인수격에서는 인성이 비겁을 생해 자기 기반을 두껍게 만든다. 공부와 보호가 자립의 근거가 된다.",
            "risk": "인비가 과하면 실행보다 자기 확신과 의존이 커져 외부 성과가 늦어진다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서는 특수한 이해력과 몰입이 자기 기준을 강화한다. 독자적 판단과 전문 분야가 생긴다.",
            "risk": "편인과 비겁이 함께 과하면 고립된 확신, 폐쇄성, 현실 판단 지연으로 기운다.",
        },
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 인성이 비겁을 더 강하게 만든다. 자립성은 두터워지지만 외부로 빼내는 식상과 질서가 필요하다.",
            "risk": "인비과중이면 강한 자기 기준만 남고 재물, 관계, 직업 성과가 늦어진다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 인성이 양인의 기세를 돕는다. 배경과 명분을 얻으면 추진력이 커진다.",
            "risk": "제어 없는 인비는 고집과 충돌을 키워 관살의 제어가 반드시 필요해진다.",
        },
    },
    "peer_generates_output": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서는 강한 자기 기반이 식상으로 빠져야 격이 산다. 자립성이 기술, 말, 결과물로 나가면 성과가 된다.",
            "risk": "식상이 약하면 강한 기운이 안에 머물러 경쟁과 고집으로 남는다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서는 거친 기세가 식상으로 빠지면 실행력과 돌파 성과가 된다.",
            "risk": "상관으로 과하게 빠지면 충돌과 반발성이 커지고, 식신이 약하면 지속 성과가 약하다.",
        },
        "eating_god_pattern": {
            "effect": "식신격에서는 비겁이 식신을 생해 생산 기반을 보강한다. 동료, 체력, 자기 기반이 결과물을 밀어준다.",
            "risk": "비겁이 과하면 생산보다 사람과 몫 문제가 먼저 커질 수 있다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서는 비겁이 상관을 생해 표현과 돌파성을 키운다. 자기 색깔이 강하게 드러난다.",
            "risk": "비겁과 상관이 함께 과하면 제도권 충돌과 평판 마찰이 강해진다.",
        },
    },
    "officer_same_group": {
        "direct_officer_pattern": {
            "effect": "정관격에서 관성이 겹치면 공식 책임, 직책, 평판 의식이 선명해진다.",
            "risk": "정관과 편관이 섞이면 관살혼잡이 되어 기준은 엄격한데 압박도 함께 커진다.",
        },
        "seven_killings_pattern": {
            "effect": "편관격에서 관살이 겹치면 강한 책임과 경쟁 환경이 두드러진다.",
            "risk": "식신이나 인성이 제어하지 못하면 관살과중으로 압박, 사고성, 책임 부담이 커진다.",
        },
    },
    "wealth_same_group": {
        "direct_wealth_pattern": {
            "effect": "정재격에서 재성이 겹치면 생활 재정과 소유 기준이 강해진다.",
            "risk": "일간이 약하면 재다신약으로 돈의 규모보다 관리 부담과 현실 요구가 커진다.",
        },
        "indirect_wealth_pattern": {
            "effect": "편재격에서 재성이 겹치면 거래, 확장, 외부 자금의 폭이 커진다.",
            "risk": "통제 없는 재성 과다는 과확장, 회수 지연, 사람을 통한 손실로 나타난다.",
        },
    },
    "output_same_group": {
        "eating_god_pattern": {
            "effect": "식신격에서 식상이 겹치면 생산력과 결과물의 폭이 커진다.",
            "risk": "식상과다이면 만들고 말하는 힘은 강하지만 책임, 기준, 수입화가 늦어질 수 있다.",
        },
        "hurting_officer_pattern": {
            "effect": "상관격에서 식상이 겹치면 표현력, 기획력, 돌파성이 매우 강해진다.",
            "risk": "식상과다이면 말과 행동이 앞서고, 인성이나 재성이 정제하지 못하면 관성을 쳐 평판과 직책을 흔든다.",
        },
    },
    "resource_same_group": {
        "direct_resource_pattern": {
            "effect": "인수격에서 인성이 겹치면 문서, 자격, 보호 기반이 두터워진다.",
            "risk": "인성 과다이면 생각과 명분은 많아지나 실행과 시장 반응이 늦어진다.",
        },
        "indirect_resource_pattern": {
            "effect": "편인격에서 인성이 겹치면 특수한 이해력과 몰입이 깊어진다.",
            "risk": "편인 과다는 고립, 도식, 비현실적 판단으로 흐르기 쉽다.",
        },
    },
    "peer_same_group": {
        "jianlu_peer_pattern": {
            "effect": "건록격에서 비겁이 겹치면 자립성, 체력, 자기 기준이 매우 강해진다.",
            "risk": "비겁 과중이면 분배, 경쟁, 고집 문제가 커져 재성과 관계를 압박한다.",
        },
        "yangren_peer_pattern": {
            "effect": "양인격에서 비겁이 겹치면 추진력과 주도권이 강하게 살아난다.",
            "risk": "관살이나 식상이 제어하지 못하면 충돌, 쟁재, 무리한 결정으로 나타난다.",
        },
    },
}

DUAL_CATEGORY_DEFAULT_LENS = {
    "wealth_controls_resource": {
        "effect": "재성이 인성을 제어한다. 현실 재정, 소유, 거래 요구가 문서, 명분, 학습, 보호성을 현실 판단으로 끌어낸다.",
        "risk": "제어가 과하면 문서와 보호 기반이 손상되고, 약하면 생각과 명분이 실행을 늦춘다.",
    },
    "wealth_generates_officer": {
        "effect": "재성이 관성을 생한다. 돈, 자원, 계약, 현실 기반이 직책, 신용, 책임으로 이어진다.",
        "risk": "재성이 탁하거나 관성이 과하면 재물은 권한이 아니라 부담, 압박, 책임 문제로 바뀐다.",
    },
    "output_generates_wealth": {
        "effect": "식상이 재성을 생한다. 기술, 말, 결과물, 서비스가 수입과 거래의 근거가 된다.",
        "risk": "결과물이 약하거나 재성이 흐리면 만든 것은 있어도 소유, 회수, 정산이 불안정하다.",
    },
    "officer_generates_resource": {
        "effect": "관성이 인성을 생한다. 직책, 책임, 압박, 평가가 문서, 자격, 명분, 보호 장치로 정리된다.",
        "risk": "인성이 약하면 책임이 보호로 넘어가지 못하고, 인성이 과하면 실행보다 명분과 절차가 늘어난다.",
    },
    "output_controls_officer": {
        "effect": "식상이 관성을 제어한다. 말, 기술, 결과물, 실무력이 직책과 압박을 다루는 방식이다.",
        "risk": "제어가 필요한 자리에서는 약이 되지만, 불필요하게 강하면 평판, 직책, 제도권 신뢰를 손상한다.",
    },
    "peer_controls_wealth": {
        "effect": "비겁이 재성을 제어한다. 자기 기준, 경쟁자, 동업자, 가까운 사람이 재물의 소유와 분배에 개입한다.",
        "risk": "재물이 보일수록 지분, 몫, 공동 비용, 정산 기준이 흔들릴 수 있다.",
    },
    "resource_controls_output": {
        "effect": "인성이 식상을 제어한다. 공부, 문서, 생각, 보호 논리가 결과물과 표현을 조절한다.",
        "risk": "적절하면 품질과 명분이 생기지만, 과하면 도식이 되어 결과물과 발표가 늦어진다.",
    },
    "officer_controls_peer": {
        "effect": "관성이 비겁을 제어한다. 규칙, 직책, 책임, 평가가 자기 주장과 경쟁심을 묶는다.",
        "risk": "관성이 약하면 사람 문제와 몫 문제가 남고, 과하면 독립성과 주도권이 압박을 받는다.",
    },
    "resource_generates_peer": {
        "effect": "인성이 비겁을 생한다. 공부, 문서, 보호, 명분이 자기 기반과 독립성을 두껍게 만든다.",
        "risk": "인비가 과하면 실행보다 자기 확신과 보호 논리가 앞서 현실 성과가 늦어진다.",
    },
    "peer_generates_output": {
        "effect": "비겁이 식상을 생한다. 자기 기반, 체력, 동료성, 경쟁심이 결과물과 표현을 밀어낸다.",
        "risk": "비겁이 과하면 성과보다 사람과 몫 문제가 먼저 커지고, 식상이 과하면 말과 행동이 앞설 수 있다.",
    },
    "officer_same_group": {
        "effect": "관성이 같은 계열에서 겹친다. 직책, 책임, 평가, 압박의 성격이 선명해진다.",
        "risk": "정관과 편관이 섞이면 관살혼잡이 되고, 한쪽이 과하면 관살과중으로 책임 부담이 커진다.",
    },
    "wealth_same_group": {
        "effect": "재성이 같은 계열에서 겹친다. 수입, 소유, 거래, 자산의 문제가 크게 드러난다.",
        "risk": "일간이 감당하지 못하면 재다신약으로 돈의 규모보다 관리 부담과 손실 위험이 커진다.",
    },
    "output_same_group": {
        "effect": "식상이 같은 계열에서 겹친다. 말, 재주, 기술, 결과물, 표현력이 강하게 드러난다.",
        "risk": "식상과다이면 생산과 표현은 많아도 책임, 기준, 수입화가 늦어질 수 있다.",
    },
    "resource_same_group": {
        "effect": "인성이 같은 계열에서 겹친다. 문서, 자격, 학습, 보호, 생각의 힘이 두터워진다.",
        "risk": "인성 과다이면 명분과 준비가 실행을 대신하고, 편중된 판단이 강해질 수 있다.",
    },
    "peer_same_group": {
        "effect": "비겁이 같은 계열에서 겹친다. 자립성, 경쟁심, 주도권, 자기 기준이 강해진다.",
        "risk": "비겁 과중이면 분배, 경쟁, 고집 문제가 커져 재성과 관계를 압박한다.",
    },
}

GROUP_LABELS = {
    "peer": "비겁",
    "output": "식상",
    "wealth": "재성",
    "officer": "관성",
    "resource": "인성",
}

TEN_GOD_LABEL = {
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

TEN_GOD_OPERATION_FACE = {
    "bi_gyeon": {
        "action": "자기 기준과 독립성",
        "result": "자립 기반",
        "risk": "고집과 경쟁",
        "timing": "자기 결정, 독립, 동등한 경쟁",
    },
    "geob_jae": {
        "action": "경쟁, 지분, 주도권",
        "result": "강한 추진력과 분점 구조",
        "risk": "분탈, 동업 갈등, 몫 다툼",
        "timing": "동업, 경쟁자, 지분 조정",
    },
    "sik_sin": {
        "action": "반복 생산과 안정된 결과물",
        "result": "기술, 상품, 꾸준한 성과",
        "risk": "안주와 속도 저하",
        "timing": "결과물 공개, 기술 수익화, 반복 판매",
    },
    "sang_gwan": {
        "action": "표현, 기획, 돌파성",
        "result": "개성 있는 성과와 시장 노출",
        "risk": "규칙 충돌과 평판 마찰",
        "timing": "발표, 기획 전환, 제도권 충돌",
    },
    "pyeon_jae": {
        "action": "외부 거래와 유동 자금",
        "result": "확장성, 영업, 투자 기회",
        "risk": "과확장과 회수 지연",
        "timing": "거래 확대, 외부 자금, 투자 제안",
    },
    "jeong_jae": {
        "action": "소유, 정산, 고정 수입",
        "result": "생활 재정과 축적 기반",
        "risk": "보수성과 실행 지연",
        "timing": "고정 수입, 정산, 자산 소유",
    },
    "pyeon_gwan": {
        "action": "압박, 경쟁, 위기 대응",
        "result": "강한 책임과 돌파 권한",
        "risk": "과중한 부담과 위험 노출",
        "timing": "압박 업무, 경쟁, 위기 대응",
    },
    "jeong_gwan": {
        "action": "질서, 직책, 공식 평가",
        "result": "명예, 신용, 제도권 자리",
        "risk": "경직성과 평판 부담",
        "timing": "직책, 평가, 공식 책임",
    },
    "pyeon_in": {
        "action": "특수 학습과 비정형 판단",
        "result": "직관, 몰입, 특수 전문성",
        "risk": "고립, 편중, 도식",
        "timing": "특수 공부, 고립된 준비, 기술 몰입",
    },
    "jeong_in": {
        "action": "문서, 자격, 보호 기반",
        "result": "정식 명분과 안정 장치",
        "risk": "보류, 의존, 실행 지연",
        "timing": "자격, 문서, 학업, 보호 장치",
    },
}

TEN_GOD_DOMAIN_FACE = {
    "bi_gyeon": {
        "money": "동등한 몫, 공동 소유, 자기 지분",
        "career": "독립 업무, 동료 경쟁, 자기 주도 역할",
        "relationship": "동등한 관계와 자기 입장",
        "marriage": "생활 주도권과 가족 재정의 분담",
        "personality": "자기 기준과 독립성",
    },
    "geob_jae": {
        "money": "지분 경쟁, 분점, 공동 자금의 손익",
        "career": "경쟁 구도, 주도권, 동업과 조직 내 힘겨루기",
        "relationship": "몫을 따지는 관계와 주도권 경쟁",
        "marriage": "배우자와 가족 사이의 재정·주도권 문제",
        "personality": "강한 추진력과 경쟁심",
    },
    "sik_sin": {
        "money": "반복 가능한 기술, 상품, 서비스의 수입화",
        "career": "실무 처리력, 결과물, 꾸준한 성과",
        "relationship": "편안한 표현과 안정된 호감",
        "marriage": "생활 속 배려와 반복되는 책임 수행",
        "personality": "안정성, 지속성, 손에 익은 방식",
    },
    "sang_gwan": {
        "money": "기획, 표현, 노출, 영업성의 수입화",
        "career": "개선안, 발표, 돌파력, 제도권과의 긴장",
        "relationship": "직설적인 표현과 감정의 속도",
        "marriage": "말의 강도, 생활 방식의 충돌, 개성의 주장",
        "personality": "비판성, 표현력, 규칙을 넘는 재주",
    },
    "pyeon_jae": {
        "money": "외부 거래, 유동 자금, 투자와 확장 수익",
        "career": "영업, 사업 기회, 거래처와 외부 자원",
        "relationship": "넓은 만남과 외부 인맥",
        "marriage": "활동 범위, 외부 인연, 생활비의 변동성",
        "personality": "기회 포착, 활동성, 현실 감각",
    },
    "jeong_jae": {
        "money": "고정 수입, 소유권, 정산, 축적 기준",
        "career": "보상 기준, 안정 수입, 계약상 대가",
        "relationship": "신뢰와 실질적 책임",
        "marriage": "생활비, 자산, 주거, 재정 합의",
        "personality": "현실성, 계산 기준, 안정 욕구",
    },
    "pyeon_gwan": {
        "money": "위험 부담이 붙은 돈, 책임 비용, 강한 거래 압박",
        "career": "강한 책임, 경쟁, 위기 대응, 권한 부담",
        "relationship": "긴장감, 통제, 압박으로 생기는 거리",
        "marriage": "생활 압박, 강한 책임, 불안정한 부담",
        "personality": "긴장감, 승부성, 위험 대응력",
    },
    "jeong_gwan": {
        "money": "직책과 연결된 보상, 공식 계약, 신용",
        "career": "직책, 공식 평가, 조직 질서, 책임 범위",
        "relationship": "약속, 신뢰, 책임 있는 태도",
        "marriage": "배우자 역할, 법적 책임, 장기 신뢰",
        "personality": "원칙, 품위, 평판 의식",
    },
    "pyeon_in": {
        "money": "특수 정보, 비정형 계약, 숨은 리스크",
        "career": "특수 지식, 비공식 자료, 몰입형 전문성",
        "relationship": "속내를 늦게 여는 태도와 독자적 판단",
        "marriage": "개인 영역, 고립감, 비정형 생활 방식",
        "personality": "직관, 몰입, 편중된 관심",
    },
    "jeong_in": {
        "money": "정식 문서, 자격, 보호 장치, 계약 근거",
        "career": "자격, 학력, 문서, 제도적 보호",
        "relationship": "보호 욕구, 신뢰의 근거, 안정감",
        "marriage": "가족의 보호, 절차, 문서와 명분",
        "personality": "신중함, 명분, 보호와 안정 욕구",
    },
}

CHAIN_DOMAIN_FACE = {
    "constructive_chain": "앞의 작용이 뒤의 작용으로 이어져 격국의 성립 조건을 넓힌다.",
    "supportive_chain": "두 작용이 같은 방향으로 격국을 보조한다.",
    "medicine_chain": "한쪽의 부담을 다른 쪽이 제어해 병을 약으로 바꾸는 조합이다.",
    "mediated_tension_chain": "두 작용이 모두 필요해도 서로 직접 극하므로 중간 기준이 있어야 성립한다.",
    "risk_chain": "두 작용이 결합하면서 격국의 약점이 사건으로 커질 수 있다.",
    "compounded_burden_chain": "부담 작용이 겹쳐 손실, 충돌, 책임 문제가 커지기 쉽다.",
    "conditional_chain": "과한 쪽을 조절하면 약이 되고, 약한 쪽을 치면 병이 된다.",
    "mixed_chain": "강약과 위치에 따라 성격과 파격이 갈린다.",
}

DUAL_RELATION_LABELS = {
    "first_generates_second": "앞 십신이 뒤 십신을 생한다",
    "second_generates_first": "뒤 십신이 앞 십신을 생한다",
    "first_controls_second": "앞 십신이 뒤 십신을 극한다",
    "second_controls_first": "뒤 십신이 앞 십신을 극한다",
    "same_group": "두 십신이 같은 계열로 겹친다",
}


ROLE_GRADE_INTERACTION_PHRASE = {
    "core": "격국의 중심을 직접 세우는 성격 작용이다.",
    "core_overload": "격국 중심을 강화하지만 과하면 병으로 바뀐다.",
    "support": "격국을 돕는 보조 작용이다.",
    "strong_regulator": "격국의 병을 강하게 제어하는 약이다.",
    "regulator": "격국의 과한 부분을 조절하는 약이다.",
    "regulator_or_breaker": "조건이 맞으면 약이고, 어긋나면 파격이다.",
    "breaker_or_medicine": "병을 치는 약이 될 수도 있고 격을 깨는 작용이 될 수도 있다.",
    "conditioned_support": "월령과 위치가 맞을 때 성과로 이어지는 조건부 보조 작용이다.",
    "source": "격국이 작동할 배경과 근거를 공급한다.",
    "mixed": "좋고 나쁨이 고정되지 않고 강약과 위치에서 결론이 갈린다.",
    "burden": "격국 성립에 부담을 얹는다.",
    "breaker": "격국의 중심을 직접 흔드는 파격 작용이다.",
    "danger": "격국의 약점을 사건화시키는 위험 작용이다.",
}

DOMAIN_EVENT_TARGETS = {
    "money": ("재물", "소유권", "정산"),
    "career": ("직업", "책임", "평가"),
    "relationship": ("사람", "관계"),
    "marriage": ("배우자", "가정"),
    "personality": ("성향", "판단 방식"),
    "reputation": ("명예", "평판"),
}

GROUP_EVENT_TARGETS = {
    "peer": ("사람", "몫", "지분"),
    "output": ("결과물", "기술", "표현"),
    "wealth": ("돈", "계약", "소유"),
    "officer": ("책임", "평가", "직책"),
    "resource": ("문서", "자격", "보호"),
}


DUAL_LUCK_DOMAIN_CONTEXT = {
    "money": {
        "daeun": "수입 구조, 소유권, 정산 기준, 자산화 방식이 길게 바뀐다",
        "seun": "계약, 정산, 회수, 지출, 공동 자금 문제가 실제 사건으로 올라온다",
    },
    "career": {
        "daeun": "직무 범위, 권한, 평가 방식, 책임 구조가 몇 해에 걸쳐 달라진다",
        "seun": "인사 평가, 직책 변화, 업무 배정, 권한 충돌이 구체 사건으로 드러난다",
    },
    "relationship": {
        "daeun": "사람을 고르는 기준과 관계를 유지하는 방식이 길게 바뀐다",
        "seun": "새 인연, 신뢰 확인, 거리 조절, 감정 충돌이 사건으로 잡힌다",
    },
    "marriage": {
        "daeun": "배우자상, 가족 책임, 주거와 생활 기준이 장기 과제가 된다",
        "seun": "혼인 결정, 가족 협의, 생활비, 주거 조건이 구체 문제로 드러난다",
    },
    "personality": {
        "daeun": "성격의 사용 방식, 관심 분야, 판단 기준이 서서히 달라진다",
        "seun": "중요한 선택 앞에서 성격의 장점과 약점이 뚜렷하게 드러난다",
    },
    "reputation": {
        "daeun": "평판, 직함, 신용, 사회적 역할의 무게가 길게 형성된다",
        "seun": "공식 평가, 공개적 인정, 평판 손상과 회복이 사건으로 나타난다",
    },
}


DUAL_LUCK_CATEGORY_CONTEXT = {
    "output_generates_wealth": {
        "daeun": "기술, 결과물, 말과 글, 서비스가 가격과 거래 구조로 옮겨 간다",
        "seun": "상품 공개, 판매, 보상 협의, 정산, 반복 거래가 핵심 사건이 된다",
        "order": "식상 운이 먼저 오면 만든 것이 시장으로 나가고, 재성 운이 먼저 오면 돈의 요구가 결과물을 재촉한다.",
    },
    "wealth_generates_officer": {
        "daeun": "돈, 계약, 자원, 보상 기준이 직책과 책임으로 이어진다",
        "seun": "보상 조정, 계약 책임, 직책 변화, 평판 평가가 함께 움직인다",
        "order": "재성 운이 먼저 오면 현실 이익이 책임으로 바뀌고, 관성 운이 먼저 오면 책임이 먼저 오고 보상은 뒤따른다.",
    },
    "officer_generates_resource": {
        "daeun": "직책과 책임이 자격, 문서, 보호 장치로 안정된다",
        "seun": "시험, 자격, 계약서, 증빙, 공식 절차가 사건의 열쇠가 된다",
        "order": "관성 운이 먼저 오면 책임이 자격을 요구하고, 인성 운이 먼저 오면 문서와 보호 장치가 직책을 받친다.",
    },
    "resource_generates_peer": {
        "daeun": "학습, 문서, 보호 기반이 자기 확신과 독립성으로 이어진다",
        "seun": "지원자, 가족, 자격, 소속 문제가 자기 결정 문제와 함께 올라온다",
        "order": "인성 운이 먼저 오면 배경이 마련되고, 비겁 운이 먼저 오면 자기주장과 독립 요구가 먼저 커진다.",
    },
    "peer_generates_output": {
        "daeun": "자기 기준과 경쟁심이 표현, 기술, 결과물로 빠져나간다",
        "seun": "발표, 제작, 실무 성과, 말과 글의 공개가 사건으로 드러난다",
        "order": "비겁 운이 먼저 오면 자기주장이 결과물을 만들고, 식상 운이 먼저 오면 표현이 앞서 자기 기준을 끌어낸다.",
    },
    "output_controls_officer": {
        "daeun": "표현과 결과물이 책임, 규칙, 직책 질서를 조정하거나 건드린다",
        "seun": "평가 충돌, 제도권 마찰, 문제 제기, 실무로 압박을 처리하는 일이 생긴다",
        "order": "식상 운이 먼저 오면 말과 결과물이 책임을 건드리고, 관성 운이 먼저 오면 압박이 먼저 생겨 처리 능력을 요구한다.",
    },
    "wealth_controls_resource": {
        "daeun": "돈과 현실 요구가 문서, 자격, 보호, 명분을 누르거나 현실화한다",
        "seun": "계약서, 학업, 자격, 보증, 보호자, 문서 손익이 사건으로 올라온다",
        "order": "재성 운이 먼저 오면 현실 결론이 문서를 압박하고, 인성 운이 먼저 오면 문서와 명분이 돈의 진행을 늦추거나 보호한다.",
    },
    "peer_controls_wealth": {
        "daeun": "사람, 지분, 동업, 경쟁이 소유권과 재물 경계를 흔든다",
        "seun": "공동 비용, 몫 다툼, 지분 조정, 가까운 사람과의 금전 문제가 드러난다",
        "order": "비겁 운이 먼저 오면 사람이 돈의 입구가 되고, 재성 운이 먼저 오면 돈이 보인 뒤 사람 사이의 몫 문제가 커진다.",
    },
    "officer_controls_peer": {
        "daeun": "규칙, 직책, 책임 기준이 자기주장과 경쟁 구도를 정리한다",
        "seun": "규정, 계약, 상급자 판단, 책임 범위가 사람 사이의 문제를 조정한다",
        "order": "관성 운이 먼저 오면 규칙이 사람을 정리하고, 비겁 운이 먼저 오면 경쟁과 자기주장이 규칙을 부른다.",
    },
    "resource_controls_output": {
        "daeun": "문서, 자격, 검토, 보호 장치가 표현과 생산 속도를 조절한다",
        "seun": "검토 지연, 승인, 자격 요건, 자료 보완, 결과물 수정이 사건으로 나타난다",
        "order": "인성 운이 먼저 오면 준비와 검토가 앞서고, 식상 운이 먼저 오면 결과물이 나오려 할 때 문서와 기준이 그것을 걸러낸다.",
    },
    "same_group": {
        "daeun": "같은 계열의 힘이 반복되어 장점과 병증이 함께 선명해진다",
        "seun": "같은 문제가 반복되거나, 같은 방식의 선택을 다시 요구받는다",
        "order": "어느 쪽이 먼저 오더라도 같은 계열의 성격이 강해지므로 과잉과 편중을 함께 본다.",
    },
}


def _dual_category_context(category: str, relation: str) -> dict[str, str]:
    if category in DUAL_LUCK_CATEGORY_CONTEXT:
        return DUAL_LUCK_CATEGORY_CONTEXT[category]
    if category.endswith("_same_group") or relation == "same_group":
        return DUAL_LUCK_CATEGORY_CONTEXT["same_group"]
    return {
        "daeun": "두 십신의 생극 관계가 생활 조건 안에서 길게 반복된다",
        "seun": "돈, 직업, 사람, 문서, 책임 중 하나가 실제 사건으로 올라온다",
        "order": "먼저 들어오는 십신이 사건의 입구가 되고, 뒤따르는 십신이 결론의 방향을 바꾼다.",
    }


def _dual_luck_activation(
    *,
    pattern: str,
    first_label: str,
    second_label: str,
    exact_pair_name: str,
    exact_pair_category: str,
    first_to_second_relation: str,
    chain_grade: str,
    domain_priority: list[str],
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    primary_domain = domain_priority[0] if domain_priority else "personality"
    domain_label = {
        "money": "재물",
        "career": "직업",
        "relationship": "관계",
        "marriage": "결혼과 가정",
        "personality": "성격과 경향",
        "reputation": "명예와 평판",
    }.get(primary_domain, primary_domain)
    domain_context = DUAL_LUCK_DOMAIN_CONTEXT.get(primary_domain, DUAL_LUCK_DOMAIN_CONTEXT["personality"])
    category_context = _dual_category_context(exact_pair_category, first_to_second_relation)
    chain_tail = DUAL_EVENT_CHAIN_TAILS.get(chain_grade, "월령, 강약, 위치에 따라 결론이 달라진다.")
    return (
        f"{pattern_label}에서 {exact_pair_name} 운이 들어오면 "
        f"{_and_form(first_label)} {second_label}의 선후가 {_object_form(pattern_center)} 거쳐 {domain_label} 결론을 바꾼다. "
        f"대운에서는 {category_context['daeun']}. {domain_context['daeun']}. "
        f"세운에서는 {category_context['seun']}. {domain_context['seun']}. "
        f"{category_context['order']} {chain_tail}"
    )


def _group_relation_to_pattern_phrase(pattern: str, acting_group: str) -> str:
    pattern_group = TEN_GOD_GROUPS[PATTERN_CENTER_BY_PATTERN[pattern]]
    if acting_group == pattern_group:
        return "격국의 중심 자체가 반복되는 작용"
    if GROUP_GENERATES.get(acting_group) == pattern_group:
        return "격국의 중심을 생하는 공급원이 두터워지는 작용"
    if GROUP_GENERATES.get(pattern_group) == acting_group:
        return "격국의 힘이 다음 역할로 빠져나가는 작용"
    if GROUP_CONTROLS.get(acting_group) == pattern_group:
        return "격국의 중심을 제어하는 힘이 커지는 작용"
    if GROUP_CONTROLS.get(pattern_group) == acting_group:
        return "격국의 중심이 제어하거나 다루어야 할 대상이 커지는 작용"
    return "격국의 중심을 우회적으로 흔드는 작용"


def _same_group_pattern_lens(pattern: str, category: str) -> dict[str, str]:
    group = category.removesuffix("_same_group")
    label = str(PATTERN_LENS[pattern]["label"])
    center = str(PATTERN_LENS[pattern]["center"])
    group_label = GROUP_LABELS[group]
    relation_phrase = _group_relation_to_pattern_phrase(pattern, group)
    faces = {
        "peer": ("자기 기준, 경쟁, 지분, 몫", "비겁 과중", "사람과 몫의 문제가 재물·관계·직업 판단에 끼어든다"),
        "output": ("기술, 표현, 결과물, 생산성", "식상과다", "말과 결과물은 많아지나 기준·책임·수입화가 늦어질 수 있다"),
        "wealth": ("수입, 소유, 거래, 자산", "재다신약", "돈의 규모보다 감당력, 회수, 관리 부담이 먼저 문제가 된다"),
        "officer": ("직책, 책임, 평가, 압박", "관살혼잡·관살과중", "책임과 평가가 선명해지지만 정관과 편관이 섞이면 기준이 탁해진다"),
        "resource": ("문서, 자격, 보호, 생각", "인성 과다", "명분과 준비가 두터워지나 실행과 결과가 늦어질 수 있다"),
    }
    domain, disease, risk_core = faces[group]
    effect = (
        f"{label}에서 {group_label}이 겹치면 {_object_form(center)} 기준으로 {domain}의 힘이 선명해진다. "
        f"이 겹침은 {relation_phrase}으로 판정한다. "
        f"월령에서 필요한 작용이면 성격을 보강하고, 불필요하면 {disease}의 병으로 기운다."
    )
    risk = (
        f"{label}에서 {group_label} 중첩이 과하면 {risk_core}. "
        f"투출하면 밖으로 사건화되고, 지장간에 있으면 대운·세운에서 자극될 때 현실 문제로 올라온다. "
        f"통근하면 오래 지속되고, 뿌리가 약하면 사건은 생겨도 안정적으로 붙들기 어렵다."
    )
    return {"effect": effect, "risk": risk}


def _resource_peer_pattern_lens(pattern: str) -> dict[str, str]:
    label = str(PATTERN_LENS[pattern]["label"])
    center = str(PATTERN_LENS[pattern]["center"])
    resource_relation = _group_relation_to_pattern_phrase(pattern, "resource")
    peer_relation = _group_relation_to_pattern_phrase(pattern, "peer")
    effect = (
        f"{label}에서 인성이 비겁을 생하면 문서, 명분, 학습, 보호가 자기 기준과 독립성을 두껍게 만든다. "
        f"인성은 이 격국에서 {resource_relation}이고, 비겁은 {peer_relation}이다. "
        f"따라서 이 조합은 {_object_form(center)} 안정시키는 배경이 될 수도 있고, 인비과중으로 실행을 늦추는 병이 될 수도 있다."
    )
    risk = (
        f"{label}에서 인비가 과하면 생각과 자기 확신이 강해져 외부 성과, 재물 회수, 관계 조율이 늦어진다. "
        f"인성이 투출하면 명분과 문서가 앞서고, 비겁이 통근하면 자기 기준과 경쟁심이 오래 간다. "
        f"대운·세운에서 인성이나 비겁이 반복되면 학업, 보호자, 독립, 동업, 고집 문제가 함께 드러난다."
    )
    return {"effect": effect, "risk": risk}


def _complete_overload_pattern_lenses() -> None:
    for category in (
        "officer_same_group",
        "wealth_same_group",
        "output_same_group",
        "resource_same_group",
        "peer_same_group",
    ):
        category_lenses = PATTERN_PAIR_CATEGORY_LENS.setdefault(category, {})
        for pattern in PATTERN_CENTER_BY_PATTERN:
            category_lenses.setdefault(pattern, _same_group_pattern_lens(pattern, category))

    inbi_lenses = PATTERN_PAIR_CATEGORY_LENS.setdefault("resource_generates_peer", {})
    for pattern in PATTERN_CENTER_BY_PATTERN:
        inbi_lenses.setdefault(pattern, _resource_peer_pattern_lens(pattern))

def _relation_between(first_group: str, second_group: str) -> str:
    if first_group == second_group:
        return "same_group"
    if GROUP_GENERATES.get(first_group) == second_group:
        return "first_generates_second"
    if GROUP_GENERATES.get(second_group) == first_group:
        return "second_generates_first"
    if GROUP_CONTROLS.get(first_group) == second_group:
        return "first_controls_second"
    if GROUP_CONTROLS.get(second_group) == first_group:
        return "second_controls_first"
    return "indirect_relation"


def _pattern_center_bridge_profile(pattern: str, first_ten_god: str, second_ten_god: str) -> dict[str, object]:
    pattern_center_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_group = TEN_GOD_GROUPS[pattern_center_ten_god]
    first_group = TEN_GOD_GROUPS[first_ten_god]
    second_group = TEN_GOD_GROUPS[second_ten_god]
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    pattern_center_label = TEN_GOD_LABEL[pattern_center_ten_god]
    center_label = GROUP_LABELS[pattern_group]

    def bridge_base(*, direction: str, mediated_category: str, mediated_name: str) -> dict[str, object]:
        return {
            "key": mediated_category,
            "mediated_category": mediated_category,
            "mediated_name": mediated_name,
            "direction": direction,
            "pattern": pattern,
            "pattern_label": pattern_label,
            "pattern_center": pattern_center,
            "pattern_center_ten_god": pattern_center_ten_god,
            "pattern_center_label": pattern_center_label,
            "pattern_center_group": pattern_group,
            "pattern_center_group_label": center_label,
            "first_ten_god": first_ten_god,
            "first_label": first_label,
            "first_group": first_group,
            "first_group_label": GROUP_LABELS[first_group],
            "second_ten_god": second_ten_god,
            "second_label": second_label,
            "second_group": second_group,
            "second_group_label": GROUP_LABELS[second_group],
        }

    if GROUP_GENERATES.get(first_group) == pattern_group and GROUP_GENERATES.get(pattern_group) == second_group:
        bridge_key = f"{first_group}_generates_{pattern_group}_generates_{second_group}"
        bridge_effect_tail = ""
        bridge_risk_tail = ""
        bridge_timing_tail = ""
        if pattern_group == "wealth" and second_group == "officer":
            bridge_effect_tail = (
                " 이 흐름이 끝까지 이어지면 관성이 비겁을 제어하여 사람, 몫, 정산 문제를 책임 기준으로 정리한다."
            )
            bridge_risk_tail = (
                " 관성이 약하면 재물은 생겨도 비겁의 침범을 정리하지 못해 공동 자금, 동업, 지분 문제가 남는다."
            )
            bridge_timing_tail = (
                " 관성 운이 분명하게 들어올 때 비겁 제어와 정산 기준이 함께 살아난다."
            )
        if pattern_group == "officer" and first_group == "wealth" and second_group == "resource":
            bridge_effect_tail = (
                " 이때 재관인 연쇄가 성립하면 재물이 직책의 현실 근거가 되고, 그 직책이 다시 문서와 명분을 살린다."
            )
            bridge_risk_tail = (
                " 재관인 연쇄가 끊기면 돈은 책임으로 묶이지만 문서, 자격, 보호 장치까지 이어지지 못한다."
            )
            bridge_timing_tail = (
                " 재성 운이 먼저 현실 기반을 만들고 관성 운이 그것을 받아 줄 때, 인성 운에서 문서와 명분이 정리된다."
            )
        return {
            **bridge_base(
                direction="first_to_second_via_pattern_center",
                mediated_category=bridge_key,
                mediated_name=f"{first_label}생{pattern_center_label}생{second_label}",
            ),
            "bridge_steps": [
                {"from": first_label, "relation": "생", "to": pattern_center_label},
                {"from": pattern_center_label, "relation": "생", "to": second_label},
            ],
            "effect": (
                f"{pattern_label}에서는 {_and_form(first_label)} {_object_form(second_label)} 직접 충돌로만 보지 않는다. "
                f"{_subject_form(first_label)} {_object_form(center_label)} 생하고, "
                f"{_subject_form(center_label)} 다시 {_object_form(second_label)} 생하면 "
                f"{_object_form(pattern_center)} 매개로 한 성격 연쇄가 성립한다."
                f"{bridge_effect_tail}"
            ),
            "risk": (
                f"{_subject_form(pattern_center)} 약하거나 탁하면 {first_label}의 작용이 {_euro_form(second_label)} 이어지지 못하고 "
                f"중간에서 끊긴다. 이때는 결과, 돈, 책임, 문서 중 어느 단계에서 막히는지 따로 판정해야 한다."
                f"{bridge_risk_tail}"
            ),
            "timing": (
                f"운에서는 {_subject_form(first_label)} 먼저 오면 시작점이 열리고, "
                f"{center_label} 운이 받쳐야 {_euro_form(second_label)} 결론이 넘어간다."
                f"{bridge_timing_tail}"
            ),
        }

    if GROUP_GENERATES.get(second_group) == pattern_group and GROUP_GENERATES.get(pattern_group) == first_group:
        bridge_key = f"{second_group}_generates_{pattern_group}_generates_{first_group}"
        return {
            **bridge_base(
                direction="second_to_first_via_pattern_center",
                mediated_category=bridge_key,
                mediated_name=f"{second_label}생{pattern_center_label}생{first_label}",
            ),
            "bridge_steps": [
                {"from": second_label, "relation": "생", "to": pattern_center_label},
                {"from": pattern_center_label, "relation": "생", "to": first_label},
            ],
            "effect": (
                f"{pattern_label}에서는 {_subject_form(second_label)} 먼저 {_object_form(center_label)} 생하고, "
                f"{_subject_form(center_label)} 다시 {_object_form(first_label)} 생하는 역순 매개가 가능하다. "
                f"따라서 두 십신은 따로 노는 것이 아니라 {_object_form(pattern_center)} 거쳐 앞 작용을 받친다."
            ),
            "risk": (
                f"{_subject_form(pattern_center)} 약하면 {_subject_form(second_label)} {_object_form(first_label)} 받치지 못하고 "
                f"각각의 사건으로 흩어진다. 투출과 통근이 약하면 이 매개는 운에서만 일시적으로 발동한다."
            ),
            "timing": (
                f"운에서는 {_subject_form(second_label)} 먼저 오면 배경 조건이 생기고, "
                f"{center_label} 운이 받칠 때 {first_label}의 현실 작용이 강해진다."
            ),
        }

    if GROUP_CONTROLS.get(first_group) == pattern_group and GROUP_CONTROLS.get(pattern_group) == second_group:
        bridge_key = f"{first_group}_controls_{pattern_group}_controls_{second_group}"
        dosik_release_effect_tail = ""
        dosik_release_risk_tail = ""
        dosik_release_timing_tail = ""
        if pattern_group == "resource" and first_group == "wealth" and second_group == "output":
            dosik_release_effect_tail = (
                " 재성이 과한 인성을 누르면 도식으로 묶였던 식상이 풀려 실행, 발표, 결과물의 길이 열린다."
            )
            dosik_release_risk_tail = (
                " 재성이 약하거나 인성이 이미 약하면 도식을 푸는 약이 아니라 문서와 보호 기반의 손상으로 기울 수 있다."
            )
            dosik_release_timing_tail = (
                " 재성 운이 현실 요구를 먼저 만들고 식상 운이 뒤따를 때 결과물이 밖으로 드러난다."
            )
        return {
            **bridge_base(
                direction="first_controls_second_via_pattern_center",
                mediated_category=bridge_key,
                mediated_name=f"{first_label}극{pattern_center_label}극{second_label}",
            ),
            "bridge_steps": [
                {"from": first_label, "relation": "극", "to": pattern_center_label},
                {"from": pattern_center_label, "relation": "극", "to": second_label},
            ],
            "effect": (
                f"{pattern_label}에서는 {first_label}의 제어가 바로 {_object_form(second_label)} 치는 것이 아니라 "
                f"{_object_form(pattern_center)} 거쳐 질서를 세울 수 있다. 이 경우 극은 손상이 아니라 단계적 제어로 본다."
                f"{dosik_release_effect_tail}"
            ),
            "risk": (
                f"{_subject_form(pattern_center)} 약하면 제어가 질서가 되지 못하고 직접 충돌로 변한다. "
                f"필요한 극인지 파격인지 월령과 통근으로 다시 판정해야 한다."
                f"{dosik_release_risk_tail}"
            ),
            "timing": (
                f"운에서는 {_subject_form(first_label)} 먼저 오면 제어 압력이 생기고, "
                f"{center_label} 운이 들어올 때 제어의 방향이 분명해진다."
                f"{dosik_release_timing_tail}"
            ),
        }

    if GROUP_CONTROLS.get(second_group) == pattern_group and GROUP_CONTROLS.get(pattern_group) == first_group:
        bridge_key = f"{second_group}_controls_{pattern_group}_controls_{first_group}"
        return {
            **bridge_base(
                direction="second_controls_first_via_pattern_center",
                mediated_category=bridge_key,
                mediated_name=f"{second_label}극{pattern_center_label}극{first_label}",
            ),
            "bridge_steps": [
                {"from": second_label, "relation": "극", "to": pattern_center_label},
                {"from": pattern_center_label, "relation": "극", "to": first_label},
            ],
            "effect": (
                f"{pattern_label}에서는 {second_label}의 제어가 {_object_form(pattern_center)} 거쳐 {_object_form(first_label)} 다스릴 수 있다. "
                f"이때 두 십신의 극은 직접 손상보다 격국 중심을 통한 조절로 판정한다."
            ),
            "risk": (
                f"{_subject_form(pattern_center)} 약하면 {second_label}의 제어가 조절이 되지 못하고 "
                f"{first_label}의 작용을 끊는 병으로 드러난다."
            ),
            "timing": (
                f"운에서는 {_subject_form(second_label)} 먼저 오면 제어가 시작되고, "
                f"{center_label} 운이 받쳐야 {_object_form(first_label)} 다스리는 결론으로 이어진다."
            ),
        }

    return {}


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


def _object_form(text: str) -> str:
    particle = "을" if _has_final_consonant(text) else "를"
    return f"{text}{particle}"


def _and_form(text: str) -> str:
    particle = "과" if _has_final_consonant(text) else "와"
    return f"{text}{particle}"


def _subject_form(text: str) -> str:
    particle = "이" if _has_final_consonant(text) else "가"
    return f"{text}{particle}"


def _topic_form(text: str) -> str:
    particle = "은" if _has_final_consonant(text) else "는"
    return f"{text}{particle}"


def _euro_form(text: str) -> str:
    final = _final_consonant_index(text)
    particle = "으로" if final and final != 8 else "로"
    return f"{text}{particle}"


_complete_overload_pattern_lenses()


def _ensure_sentence(text: str) -> str:
    value = text.strip()
    if not value:
        return ""
    return value if value.endswith((".", "다.", "요.", "음.")) else f"{value}."


def _with_dual_pattern_context(text: str, pattern: str, first_ten_god: str, second_ten_god: str) -> str:
    """Preserve the concrete pattern center when two ten-gods are combined."""

    value = str(text or "").strip()
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    additions: list[str] = []
    if pattern_label not in value or pattern_center not in value or first_label not in value or second_label not in value:
        additions.append(
            f"{pattern_label}의 기준은 {pattern_center}입니다. {_and_form(first_label)} {_topic_form(second_label)} 이 기준 안에서 성격·파격·병약을 다시 가른다."
        )
    if not additions:
        return value
    return f"{value} {' '.join(additions)}"


def _join_unique_sentences(*parts: str) -> str:
    sentences: list[str] = []
    seen: set[str] = set()
    for part in parts:
        value = str(part or "").strip()
        if not value:
            continue
        for raw in value.split(". "):
            sentence = raw.strip()
            if not sentence:
                continue
            if not sentence.endswith("."):
                sentence = f"{sentence}."
            key = sentence.rstrip(".").strip()
            if key in seen:
                continue
            seen.add(key)
            sentences.append(sentence)
    return " ".join(sentences)


def _category_parts(category: str) -> tuple[str, str, str]:
    if category.endswith("_same_group"):
        return category.removesuffix("_same_group"), "same_group", category.removesuffix("_same_group")
    first_group, operation, second_group = category.split("_", 2)
    return first_group, operation, second_group


def _grade_judgment(grade: str) -> str:
    if grade in SUPPORTIVE_GRADES:
        return "격을 돕는 작용"
    if grade in MIXED_GRADES:
        return "격을 살릴 수도 있고 흔들 수도 있는 작용"
    if grade in BURDEN_GRADES:
        return "그대로 커지면 병이 되는 작용"
    return "상황을 보아 판정해야 하는 작용"


def _grade_risk_phrase(grade: str) -> str:
    if grade in SUPPORTIVE_GRADES:
        return "강약과 위치가 맞으면 격의 성격이 또렷해진다"
    if grade in MIXED_GRADES:
        return "월령 적합성과 제어 여부에 따라 약과 부담이 갈린다"
    if grade in BURDEN_GRADES:
        return "파격과 병으로 먼저 드러난다"
    return "투출, 통근, 합충형파해를 함께 보아야 한다"


def _derived_pattern_pair_lens(pattern: str, category: str) -> dict[str, str]:
    first_group, operation, second_group = _category_parts(category)
    pattern_lens = PATTERN_LENS[pattern]
    label = pattern_lens["label"]
    center = pattern_lens["center"]
    first_grade, first_nature, first_effect = pattern_lens[first_group]
    second_grade, second_nature, second_effect = pattern_lens[second_group]
    first_label = GROUP_LABELS.get(first_group, first_group)
    second_label = GROUP_LABELS.get(second_group, second_group)
    first_effect_sentence = _ensure_sentence(first_effect)
    first_judgment = _grade_judgment(first_grade)
    second_judgment = _grade_judgment(second_grade)
    first_risk = _grade_risk_phrase(first_grade)
    second_risk = _grade_risk_phrase(second_grade)

    if operation == "same_group":
        effect = (
            f"{label}에서 {first_label}이 겹치면 {first_effect_sentence} "
            f"이 겹침은 {_object_form(center)} 기준으로 {first_judgment}으로 판정한다. "
            f"같은 계열이 반복되므로 투출하면 밖으로 선명하게 드러나고, 지장간에 머물면 특정 운에서 발동된다."
        )
        risk = (
            f"{label}에서 {first_label}이 과하면 {first_risk}. "
            f"통근하면 지속성이 강해지고, 뿌리가 약하면 사건은 생겨도 오래 버티지 못한다."
        )
        return {"effect": effect, "risk": risk}

    if operation == "generates":
        effect = (
            f"{label}에서 {first_label}이 {second_label}을 생하면 "
            f"{first_label} 작용에서 {second_label} 작용으로 힘이 넘어간다. "
            f"앞 작용은 이 격국에서 {first_nature}에 해당하고, 뒤 작용은 {second_nature}에 해당한다. "
            f"앞 작용은 {first_judgment}이고, 뒤 작용은 {second_judgment}이다. "
            f"따라서 이 결합은 {_object_form(center)} 살리는 방향인지, 중심에서 힘을 빼는 방향인지로 판정한다."
        )
        risk = (
            f"{label}에서 생이 성립하려면 앞 작용이 실제로 통근하거나 투출해 뒤 작용을 밀어야 한다. "
            f"앞 작용은 {first_risk}. 뒤 작용은 {second_risk}. "
            f"한쪽만 강하면 생이 아니라 부담의 이동으로 나타난다."
        )
        return {"effect": effect, "risk": risk}

    if operation == "controls":
        effect = (
            f"{label}에서 {first_label}이 {second_label}을 극하면 "
            f"{first_label} 작용이 {second_label} 작용을 제어한다. "
            f"앞 작용은 이 격국에서 {first_nature}에 해당하고, 제어받는 작용은 {second_nature}에 해당한다. "
            f"앞 작용은 {first_judgment}이고, 제어받는 작용은 {second_judgment}이다. "
            f"이 극은 무조건 손상이 아니라 {_object_form(center)} 세우기 위한 제어인지부터 판정한다."
        )
        risk = (
            f"{label}에서 극이 지나치면 제어가 손상으로 바뀐다. "
            f"앞 작용은 {first_risk}. 뒤 작용은 {second_risk}. "
            f"필요한 작용을 치면 파격이고, 병을 제어하면 약이 된다."
        )
        return {"effect": effect, "risk": risk}

    category_lens = DUAL_CATEGORY_DEFAULT_LENS.get(
        category,
        {
            "effect": "두 십신이 격국의 중심을 간접적으로 움직인다.",
            "risk": "강약, 위치, 월령 적합성이 맞지 않으면 두 작용이 따로 움직여 판단이 흐려진다.",
        },
    )
    return {
        "effect": f"{label}에서는 {_object_form(center)} 기준으로 판단한다. {category_lens['effect']}",
        "risk": f"{label}에서는 필요한 작용인지 먼저 보아야 한다. {category_lens['risk']}",
    }


def _pair_category(first_ten_god: str, second_ten_god: str, first_to_second_relation: str) -> str:
    first_group = TEN_GOD_GROUPS[first_ten_god]
    second_group = TEN_GOD_GROUPS[second_ten_god]
    if first_to_second_relation == "second_generates_first":
        first_group, second_group = second_group, first_group
    if first_to_second_relation == "second_controls_first":
        first_group, second_group = second_group, first_group
    if first_to_second_relation in {"first_generates_second", "second_generates_first"}:
        return f"{first_group}_generates_{second_group}"
    if first_to_second_relation in {"first_controls_second", "second_controls_first"}:
        return f"{first_group}_controls_{second_group}"
    if first_to_second_relation == "same_group":
        return f"{first_group}_same_group"
    return f"{first_group}_{second_group}_indirect"


def _default_pattern_pair_lens(pattern: str, category: str) -> dict[str, str]:
    category_lens = DUAL_CATEGORY_DEFAULT_LENS.get(
        category,
        {
            "effect": "두 십신이 격국의 중심을 간접적으로 움직인다.",
            "risk": "강약, 위치, 월령 적합성이 맞지 않으면 두 작용이 따로 움직여 판단이 흐려진다.",
        },
    )
    pattern_lens = PATTERN_LENS[pattern]
    return {
        "effect": (
            f"{pattern_lens['label']}에서는 {pattern_lens['center']}을 중심에 두고 이 결합을 판단한다. "
            f"{category_lens['effect']}"
        ),
        "risk": (
            f"{pattern_lens['label']}의 중심을 살리는지, 흔드는지에 따라 길흉이 달라진다. "
            f"{category_lens['risk']}"
        ),
    }


def _exact_pair_name(first_ten_god: str, second_ten_god: str, first_to_second_relation: str) -> str:
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    if first_to_second_relation == "first_generates_second":
        if first_ten_god in {"sik_sin", "sang_gwan"} and second_ten_god in {"pyeon_jae", "jeong_jae"}:
            return f"{first_label}생{second_label}"
        if first_ten_god in {"pyeon_jae", "jeong_jae"} and second_ten_god in {"pyeon_gwan", "jeong_gwan"}:
            return f"{first_label}생{second_label}"
        if first_ten_god == "pyeon_gwan" and second_ten_god in {"pyeon_in", "jeong_in"}:
            return "살인상생"
        if first_ten_god == "jeong_gwan" and second_ten_god in {"pyeon_in", "jeong_in"}:
            return "관인상생"
        return f"{first_label}생{second_label}"
    if first_to_second_relation == "first_controls_second":
        if first_ten_god == "sik_sin" and second_ten_god == "pyeon_gwan":
            return "식신제살"
        if first_ten_god == "sik_sin" and second_ten_god == "jeong_gwan":
            return "식신제관"
        if first_ten_god == "sang_gwan" and second_ten_god == "jeong_gwan":
            return "상관견관"
        if first_ten_god == "sang_gwan" and second_ten_god == "pyeon_gwan":
            return "상관제살"
        if first_ten_god in {"pyeon_jae", "jeong_jae"} and second_ten_god in {"pyeon_in", "jeong_in"}:
            return f"{first_label}극{second_label}"
        if first_ten_god == "pyeon_in" and second_ten_god == "sik_sin":
            return "편인도식"
        if first_ten_god == "jeong_in" and second_ten_god == "sik_sin":
            return "정인제식"
        return f"{first_label}극{second_label}"
    if first_to_second_relation == "second_generates_first":
        return f"{second_label}생{first_label}"
    if first_to_second_relation == "second_controls_first":
        if second_ten_god == "sik_sin" and first_ten_god == "pyeon_gwan":
            return "식신제살"
        if second_ten_god == "sik_sin" and first_ten_god == "jeong_gwan":
            return "식신제관"
        if second_ten_god == "sang_gwan" and first_ten_god == "jeong_gwan":
            return "상관견관"
        if second_ten_god == "sang_gwan" and first_ten_god == "pyeon_gwan":
            return "상관제살"
        if second_ten_god in {"pyeon_jae", "jeong_jae"} and first_ten_god in {"pyeon_in", "jeong_in"}:
            return f"{second_label}극{first_label}"
        if second_ten_god == "pyeon_in" and first_ten_god == "sik_sin":
            return "편인도식"
        if second_ten_god == "jeong_in" and first_ten_god == "sik_sin":
            return "정인제식"
        return f"{second_label}극{first_label}"
    if first_to_second_relation == "same_group":
        return f"{first_label}·{second_label} 병립"
    return f"{first_label}·{second_label} 간접 작용"


def _exact_pair_refinement(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    category: str,
    name: str,
) -> dict[str, str]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    key = "general_exact_pair"
    effect = (
        f"{pattern_label}에서는 {_and_form(first_label)} {second_label}의 차이를 따로 본다. "
        f"같은 십신군이라도 정편과 음양이 달라지면 {center}에 작용하는 방식이 달라진다."
    )
    risk = (
        f"{first_label}과 {second_label} 중 어느 쪽이 투출하고 통근했는지에 따라 "
        f"현실 사건의 주체와 부담 지점이 달라진다."
    )
    timing = (
        f"운에서는 {_subject_form(first_label)} 먼저 오면 첫 작용의 사건이 먼저 열리고, "
        f"{_subject_form(second_label)} 뒤따르면 결론이 두 번째 작용으로 이동한다."
    )

    if name == "식신제살":
        key = "siksin_jesal"
        pattern_exact_effects = {
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 살기가 격의 중심이다. "
                "식신은 그 살을 무너뜨리는 것이 아니라, 실무와 결과물로 낮추어 쓸 수 있게 만드는 약이다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 안정된 생산성이 격의 중심이다. "
                "편관이 들어오면 식신이 감당해야 할 어려운 책임이 생기고, 처리력이 충분하면 실력의 증거가 된다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                "식신제살은 재물을 직접 만드는 흐름보다, 위험한 책임을 처리해 돈과 신용을 지키는 장치로 작동한다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                "식신제살은 큰 거래 뒤에 붙는 압박과 위험 책임을 실무 능력으로 관리하는 작용이다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                "식신이 살을 제어해도 인성의 문서와 자격이 받쳐야 안정된 전문 책임으로 굳어진다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 이해와 몰입이 중심이다. "
                "식신제살은 비정형 전문성을 실제 처리력으로 꺼내 강한 압박을 다루게 한다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 정관의 질서가 중심이다. "
                "식신제살은 정관을 깨는 작용이 아니라, 편관성 압박이 섞일 때 실무로 책임을 낮추는 보조 장치다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 돌파성이 중심이다. "
                "식신제살은 상관식 충돌보다 안정된 결과물로 압박을 처리하게 만들어 과격함을 줄인다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                "식신제살은 비겁의 힘을 직접 충돌에 쓰지 않고 결과물과 처리력으로 빼내는 통로가 된다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 양인의 강한 기세가 중심이다. "
                "식신제살은 거친 결단을 실무 성과로 낮추어 사고성 압박을 다루게 한다."
            ),
        }
        pattern_exact_risks = {
            "seven_killings_pattern": "식신이 약하거나 인성이 막으면 살을 제어하지 못해 편관의 압박, 경쟁, 위험 책임이 그대로 남는다.",
            "eating_god_pattern": "편관이 식신보다 강하면 생산성은 시험을 받고, 처리 가능한 일보다 책임의 무게가 앞선다.",
            "direct_wealth_pattern": "재성이 약하면 처리한 책임이 돈과 신용으로 남지 않고, 편관이 강하면 손실 방어에 머문다.",
            "indirect_wealth_pattern": "식신이 약하면 큰 거래의 압박을 처리하지 못해 회수 지연, 클레임, 손실 책임이 커진다.",
            "direct_resource_pattern": "인성이 과하면 식신이 막혀 제살이 늦고, 인성이 약하면 처리력의 근거가 부족하다.",
            "indirect_resource_pattern": "편인이 고립되면 식신의 실제 처리력보다 불안한 판단과 준비만 길어진다.",
            "direct_officer_pattern": "정관의 질서가 약하면 식신이 책임을 감당하기보다 공식 평가를 가볍게 만드는 쪽으로 흐를 수 있다.",
            "hurting_officer_pattern": "상관성이 강하면 식신제살이 안정된 처리로 닫히지 않고 말과 충돌로 번질 수 있다.",
            "jianlu_peer_pattern": "비겁이 식신으로 빠지지 못하면 압박을 처리하지 못하고 자기 주장과 버티기로 남는다.",
            "yangren_peer_pattern": "양인의 기세가 과하면 식신의 완충보다 강한 충돌과 사고성 판단이 앞선다.",
        }
        effect = (
            f"{pattern_label}에서 식신제살은 식신이 편관의 살기를 실무, 기술, 반복 처리력으로 다스리는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '상관제살처럼 충돌로 꺾는 방식이 아니라, 해낸 결과로 압박을 낮춘다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "식신이 약하거나 뿌리가 없으면 편관의 압박을 감당하지 못해 책임과 위기만 남는다.")
        timing = "식신 운이 먼저 오면 처리 방식이 생기고, 편관 운이 뒤따르면 어려운 일을 맡아 성과로 증명한다."
    elif name == "식신제관":
        key = "siksin_jegwan"
        effect = (
            f"{pattern_label}에서 식신제관은 식신이 정관의 공식 책임을 실무와 결과물로 조절하는 작용이다. "
            f"정관을 부수는 것이 아니라, 맡은 일을 실제로 처리해 평가와 책임을 감당하는 방식이다."
        )
        risk = (
            "식신이 약하면 평가와 책임을 처리할 결과물이 부족하고, "
            "식신이 과하면 공식 기준을 가볍게 보아 신뢰가 약해질 수 있다."
        )
        timing = "식신 운이 먼저 오면 처리 방식과 성과물이 생기고, 정관 운이 뒤따르면 평가, 직책, 책임 문제가 분명해진다."
    elif name == "상관견관":
        key = "sanggwan_gyeongwan"
        pattern_exact_effects = {
            "direct_officer_pattern": (
                f"{pattern_label}에서는 정관의 질서, 직책, 공식 신뢰가 격의 중심이다. "
                "상관이 들어오면 능력과 표현이 있어도 그 중심을 직접 건드리므로 상관견관의 병으로 먼저 판정한다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 개혁성이 격의 중심이다. "
                "정관이 함께 오면 상관의 재주가 제도권 평가를 상대하게 되며, 인성이나 재성이 정제하면 개혁성이 된다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                "상관견관은 돈을 만드는 기획과 표현이 공식 책임을 건드려 계약, 승인, 평판 문제로 번지는지 본다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                "상관견관은 빠른 영업과 기획이 제도권 기준을 넘어서며 거래 신뢰를 흔드는지 판정한다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                "상관이 정관을 치더라도 인성이 정제하면 말과 기획을 문서, 자격, 품격 안에 넣을 수 있다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 비정형 전문성이 중심이다. "
                "상관견관은 특수한 판단이 공식 질서와 충돌하는 문제로 나타나므로 설명 가능성과 근거가 중요하다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 압박이 중심이다. "
                "상관이 정관을 치는 동시에 편관성 압박이 있으면 말과 충돌이 위험 책임으로 커질 수 있다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 안정 생산이 중심이다. "
                "상관견관은 안정된 결과물보다 말과 방향 전환이 공식 평가를 건드릴 때 병이 된다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                "상관견관은 독립적인 판단과 표현이 조직 질서와 부딪히는 방식으로 드러난다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 주도권이 중심이다. "
                "상관견관은 직설성과 승부성이 공식 평가를 건드려 충돌을 크게 만들 수 있다."
            ),
        }
        pattern_exact_risks = {
            "direct_officer_pattern": "인성이나 재성이 받치지 못하면 능력보다 말, 태도, 기획 방향이 먼저 문제 되어 직책과 평판을 손상한다.",
            "hurting_officer_pattern": "상관이 과하고 정제가 없으면 개혁성이 아니라 제도권 신뢰를 깨는 반발로 보인다.",
            "direct_wealth_pattern": "재성이 상관을 받아 주지 못하면 수익화보다 승인, 계약, 평판 리스크가 먼저 커진다.",
            "indirect_wealth_pattern": "거래 속도가 기준을 앞지르면 영업은 빠르지만 회수, 신뢰, 법적 책임이 흔들린다.",
            "direct_resource_pattern": "인성이 약하면 상관을 정제하지 못하고, 인성이 과하면 표현이 문서 안에 갇혀 수익화가 늦다.",
            "indirect_resource_pattern": "특수한 판단이 설명되지 않으면 비판과 고립으로 보이고 공식 평가에서 손해를 본다.",
            "seven_killings_pattern": "편관성 압박까지 강하면 상관견관이 단순 말실수가 아니라 위험 책임과 처벌성 문제로 커진다.",
            "eating_god_pattern": "상관이 식신보다 강하면 꾸준한 생산보다 방향 전환과 문제 제기가 앞선다.",
            "jianlu_peer_pattern": "관성이 약하면 독립성이 규칙을 무시하는 모습으로 보이고, 관성이 과하면 충돌이 커진다.",
            "yangren_peer_pattern": "양인의 기세와 상관이 함께 과하면 공식 질서와 정면 충돌하기 쉽다.",
        }
        effect = (
            f"{pattern_label}에서 상관견관은 상관이 정관의 공식성, 직책, 평판 질서를 치는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '개혁성과 표현력이 살아도 제도권 신뢰를 손상하는지부터 판단해야 한다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "인성이나 재성이 정제하지 못하면 말, 태도, 기획 방향 때문에 직책과 평판이 흔들린다.")
        timing = "상관 운이 먼저 오면 문제 제기와 반발이 앞서고, 정관 운이 뒤따르면 공식 평가와 책임 문제가 드러난다."
    elif name == "상관제살":
        key = "sanggwan_jesal"
        effect = (
            f"{pattern_label}에서 상관제살은 상관이 편관의 거친 압박을 돌파력으로 꺾는 작용이다. "
            f"식신제살보다 빠르고 강하지만, 정제되지 않으면 위험한 충돌이 된다."
        )
        risk = "상관이 과하면 압박을 해결하기보다 권위와 정면으로 부딪혀 사고성과 평판 부담이 커진다."
        timing = "상관 운이 먼저 오면 돌파와 반발이 생기고, 편관 운이 뒤따르면 강한 책임이나 경쟁으로 시험받는다."
    elif name == "관인상생":
        key = "gwanin_sangsaeng"
        resource_face = "정식 문서, 자격, 명분" if second_ten_god == "jeong_in" else "특수한 보호와 학습"
        pattern_exact_effects = {
            "direct_officer_pattern": (
                f"{pattern_label}에서는 정관이 격의 중심이다. "
                f"정관의 공식 책임이 {_euro_form(resource_face)} 이어질 때 직책과 평판이 안정된다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"정관이 인성을 생하면 직책과 제도가 자격, 문서, 보호 기반을 보강한다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 비정형 전문성과 몰입이 중심이다. "
                f"정관이 인성을 생하면 특수한 이해가 제도권 책임과 문서 근거를 얻는다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재물의 안정성이 중심이다. "
                f"정관이 인성을 생하면 재물에서 생긴 책임이 문서와 자격의 보호 장치로 정리된다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 중심이다. "
                f"정관이 인성을 생하면 외부 거래가 신용, 문서, 승인 절차 안으로 들어온다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 결과물이 중심이다. "
                f"정관이 인성을 생하면 생산물이 공식 책임과 문서 절차를 거쳐 신뢰를 얻는다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관이 관을 건드리기 쉽다. "
                f"정관이 인성을 생하면 표현과 문제 제기가 문서, 품격, 자격으로 정리된다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 자기 기반이 중심이다. "
                f"정관이 인성을 생하면 독립성이 직책과 명분을 통해 안정된다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세가 중심이다. "
                f"정관이 인성을 생하면 거친 추진력이 제도적 책임과 명분 안으로 들어온다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 압박과 정관의 공식 책임을 구분해야 한다. "
                f"정관이 인성을 생하면 살의 거친 압박보다 공식 책임과 문서 안정 쪽으로 정리된다."
            ),
        }
        pattern_exact_risks = {
            "direct_officer_pattern": "인성이 약하면 직책을 받칠 문서, 승인, 자격의 근거가 부족하다.",
            "direct_resource_pattern": "관이 과하면 인성은 보호가 아니라 책임을 버티는 장치로 소모된다.",
            "indirect_resource_pattern": "인성이 약하면 제도권 책임을 받아낼 문서 근거가 부족하고, 과하면 특수성이 절차 안에 갇힌다.",
            "direct_wealth_pattern": "인성이 과하면 재물 실행이 명분과 절차에 묶이고, 관이 과하면 돈이 책임 문서로 굳어진다.",
            "indirect_wealth_pattern": "문서와 승인 절차가 약하면 거래 확장이 신용 문제로 번질 수 있다.",
            "eating_god_pattern": "인성이 과하면 생산 속도가 늦어지고, 관성이 과하면 결과물보다 책임이 앞선다.",
            "hurting_officer_pattern": "인성이 약하면 상관의 표현을 정리하지 못해 평판과 공식 평가가 흔들린다.",
            "jianlu_peer_pattern": "관이 약하면 책임이 자격으로 이어지지 못하고, 인성이 과하면 독립성에 명분만 두꺼워진다.",
            "yangren_peer_pattern": "인성이 약하면 강한 기세가 보호로 넘어가지 못하고, 과하면 명분을 앞세운 충돌이 커진다.",
            "seven_killings_pattern": "정관과 편관이 섞이면 공식 책임과 위험 책임이 혼잡해질 수 있다.",
        }
        effect = (
            f"{pattern_label}에서 관인상생은 정관의 공식 책임이 인성의 문서, 자격, 명분으로 이어지는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '책임이 보호 장치와 신뢰로 정리될 때 격이 안정된다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "인성이 과하면 실행보다 명분과 절차가 늘고, 관성이 약하면 자격은 있어도 책임의 근거가 약하다.")
        timing = "정관 운이 먼저 오면 직책과 평가가 열리고, 인성 운이 뒤따르면 문서와 자격으로 안정된다."
    elif name == "살인상생":
        key = "salin_sangsaeng"
        resource_face = "정식 보호와 자격" if second_ten_god == "jeong_in" else "특수한 보호와 학습"
        pattern_exact_effects = {
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관이 격의 중심이다. "
                f"편관의 압박이 {_euro_form(resource_face)} 흡수되면 위험 책임이 자격, 공부, 보호 장치로 바뀐다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"편관이 인성을 생하면 압박과 경쟁이 공부, 자격, 보호 기반을 강화한다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 몰입이 중심이다. "
                f"편관이 인성을 생하면 위기와 압박이 특정 공부와 전문 기술의 이유가 된다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세가 중심이다. "
                f"편관이 인성을 생하면 거친 추진력과 압박이 문서와 보호 장치로 흡수된다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 자기 기반이 중심이다. "
                f"편관이 인성을 생하면 독립성이 강한 책임을 거쳐 자격과 명분으로 안정된다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재물의 안정성이 중심이다. "
                f"편관이 인성을 생하면 재물에서 생긴 강한 책임이 문서와 보호 장치로 정리된다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 외부 거래와 확장이 중심이다. "
                f"편관이 인성을 생하면 큰 거래의 압박이 신용, 문서, 전문성으로 수습된다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 생산성이 중심이다. "
                f"편관이 인성을 생하면 생산물에 붙은 강한 책임이 자격과 문서 절차로 정리된다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 돌파성이 중심이다. "
                f"편관이 인성을 생하면 권위와의 긴장이 자격, 문서, 전문성으로 흡수된다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 정관과 편관의 혼잡을 구분해야 한다. "
                f"편관이 인성을 생하면 거친 책임이 문서 보호로 수습되지만, 정관의 청정성을 흐릴 수도 있다."
            ),
        }
        pattern_exact_risks = {
            "seven_killings_pattern": "살이 인성으로 화하지 못하면 경쟁과 위기 책임이 그대로 남는다.",
            "direct_resource_pattern": "편관이 과하면 인성은 보호가 아니라 압박을 버티는 장치로 소모된다.",
            "indirect_resource_pattern": "편관과 편인이 함께 과하면 전문성보다 고립된 긴장과 불안정한 판단이 강해진다.",
            "yangren_peer_pattern": "인성이 약하면 강한 기세와 압박이 보호로 넘어가지 못해 충돌성이 커진다.",
            "jianlu_peer_pattern": "편관이 과하면 독립성이 위기 책임에 눌리고, 인성이 과하면 명분이 무거워진다.",
            "direct_wealth_pattern": "인성이 약하면 재물에서 생긴 강한 책임이 문서 손상과 부담으로 남는다.",
            "indirect_wealth_pattern": "문서와 전문성이 약하면 큰 거래가 압박, 회수 지연, 위험 책임으로 바뀐다.",
            "eating_god_pattern": "인성이 과하면 생산 속도가 막히고, 편관이 과하면 결과물보다 책임이 앞선다.",
            "hurting_officer_pattern": "인성이 약하면 상관의 돌파가 편관의 압박과 충돌해 평판 손상이 커진다.",
            "direct_officer_pattern": "편관이 강하면 공식 책임과 위험 책임이 섞여 관살혼잡으로 기울 수 있다.",
        }
        effect = (
            f"{pattern_label}에서 살인상생은 편관의 압박과 위험이 인성의 보호, 자격, 학습으로 흡수되는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '거친 책임을 공부와 제도적 장치로 받아내는 구조다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "인성이 약하면 편관의 압박이 보호로 넘어가지 못하고 긴장, 소모, 손실 부담으로 남는다.")
        timing = "편관 운이 먼저 오면 압박이 생기고, 인성 운이 뒤따르면 자격, 문서, 보호 장치로 수습된다."
    elif name == "편인도식":
        key = "pyeonin_dosik"
        pattern_exact_effects = {
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 생산성이 격의 중심이다. "
                f"편인이 식신을 누르면 결과물, 서비스, 반복 생산이 생각과 준비 안에서 막힌다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 변통성이 중심이다. "
                f"편인이 식신을 누르면 상관의 빠른 표현 뒤에 지속 생산의 기반이 약해진다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 중심이다. "
                f"편인이 식신을 누르면 재물을 만드는 공급력과 반복 결과물이 늦어져 수입의 근거가 약해진다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 중심이다. "
                f"편인이 식신을 누르면 특수한 판단은 깊어지지만 상품화와 외부 수익 전환이 늦어진다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"편인이 식신을 누르면 문서와 공부의 힘은 두터워지지만 결과물을 내놓는 속도는 분명히 늦어진다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 편인의 특수 몰입이 중심이다. "
                f"편인이 식신을 누르면 전문성은 깊어지지만 시장에 내놓을 결과물이 늦다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 중심이다. "
                f"편인이 식신을 누르면 직책의 책임을 성과로 풀기보다 문서, 승인, 내부 검토가 앞선다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 압박을 처리하는 힘이 중요하다. "
                f"편인이 식신을 누르면 식신제살의 실무력이 막혀 압박을 실제 처리로 풀기 어렵다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                f"편인이 식신을 누르면 자기 확신과 준비는 강해지지만 결과물로 빠져나가는 통로가 좁아진다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세가 중심이다. "
                f"편인이 식신을 누르면 거친 추진력이 실제 처리보다 고립된 판단과 명분으로 머물 수 있다."
            ),
        }
        pattern_exact_risks = {
            "eating_god_pattern": "식신이 약하면 생산 자체가 병목이 되고, 재성이 길을 열어도 수입화가 늦다.",
            "hurting_officer_pattern": "표현은 빠른데 반복 생산이 약하면 기획과 말이 실제 성과를 앞선다.",
            "direct_wealth_pattern": "재성은 있어도 공급력이 약하면 수입의 지속성과 소유 기준이 흔들린다.",
            "indirect_wealth_pattern": "거래 기회가 와도 상품화가 늦으면 회수와 확장이 불안정해진다.",
            "direct_resource_pattern": "인성이 과하면 공부와 문서가 결과물을 대신한다.",
            "indirect_resource_pattern": "편인의 고립이 강하면 전문성은 깊어도 대중화와 수익화가 늦다.",
            "direct_officer_pattern": "책임을 성과로 풀지 못하면 문서와 절차는 늘고 평가는 늦어진다.",
            "seven_killings_pattern": "식신제살이 막히면 압박을 실무로 처리하지 못해 책임과 긴장이 남는다.",
            "jianlu_peer_pattern": "식상이 약하면 강한 자기 기반이 밖으로 풀리지 못해 고집과 준비로 머문다.",
            "yangren_peer_pattern": "기세를 결과물로 빼내지 못하면 충돌을 풀 실무력이 약해진다.",
        }
        effect = (
            f"{pattern_label}에서 편인도식은 편인의 특수한 생각과 고립된 판단이 식신의 생산력을 막는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '깊은 이해는 생기지만 결과물을 내놓는 속도가 늦어진다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "식신이 약하면 준비와 생각이 성과를 대신하고, 재성이나 관성이 길을 열지 않으면 수입화가 늦다.")
        timing = "편인 운이 먼저 오면 준비와 몰입이 길어지고, 식신 운이 뒤따라야 실제 결과물이 나온다."
    elif name == "정인제식":
        key = "jeongin_jesik"
        pattern_exact_effects = {
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 안정 생산이 중심이다. "
                f"정인이 식신을 제어하면 결과물에 품질, 문서, 자격의 기준이 붙지만 속도는 늦어진다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 변통성이 중심이다. "
                f"정인이 식신을 제어하면 상관의 급한 표현을 정돈하되, 실제 반복 생산은 늦어질 수 있다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 중심이다. "
                f"정인이 식신을 제어하면 재물을 만드는 결과물이 문서와 기준을 얻지만 수입화의 속도는 느려진다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 중심이다. "
                f"정인이 식신을 제어하면 외부 수익을 만들 결과물에 검토와 문서 기준이 붙어 확장 속도를 조절한다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 정인의 문서와 보호가 중심이다. "
                f"정인이 식신을 제어하면 격의 안정성은 강해지지만 결과물과 수입화는 뒤로 밀린다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 이해가 중심이다. "
                f"정인이 식신을 제어하면 비정형 전문성이 공식 문서와 기준을 얻지만 상품화는 늦다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 중심이다. "
                f"정인이 식신을 제어하면 직책을 흔들 수 있는 결과물을 문서와 절차 안에서 정리한다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 압박을 처리하는 힘이 중요하다. "
                f"정인이 식신을 제어하면 위기 대응에 문서 근거는 생기지만 실무 처리 속도는 늦어진다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 자기 기반이 중심이다. "
                f"정인이 식신을 제어하면 강한 자기 기준이 결과물로 바로 나가기보다 문서와 명분을 거친다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세가 중심이다. "
                f"정인이 식신을 제어하면 거친 실행을 절차와 기준으로 낮추지만, 과하면 실무가 늦어진다."
            ),
        }
        pattern_exact_risks = {
            "eating_god_pattern": "정인이 과하면 품질 기준이 생산 속도를 누르고 결과물이 늦어진다.",
            "hurting_officer_pattern": "정제가 지나치면 표현의 속도와 시장 반응이 약해진다.",
            "direct_wealth_pattern": "결과물이 늦으면 재성은 있어도 수입의 공급 기반이 약해진다.",
            "indirect_wealth_pattern": "검토가 길어지면 확장 기회와 회수 시점이 늦어진다.",
            "direct_resource_pattern": "인성이 과하면 문서와 보호가 실행을 대신한다.",
            "indirect_resource_pattern": "공식 기준이 지나치면 특수 전문성이 시장에 늦게 나온다.",
            "direct_officer_pattern": "책임을 성과로 풀기보다 절차와 승인에 묶일 수 있다.",
            "seven_killings_pattern": "실무 속도가 늦으면 편관의 압박을 바로 처리하지 못한다.",
            "jianlu_peer_pattern": "식상이 약하면 자기 기반이 명분 안에 머물고 성과로 빠지지 못한다.",
            "yangren_peer_pattern": "절차가 과하면 양인의 기세를 결과물로 쓰기 전에 묶어 둔다.",
        }
        effect = (
            f"{pattern_label}에서 정인제식은 정인의 문서, 보호, 명분이 식신의 생산 속도를 조절하는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '품질과 안정성을 만들 수 있지만 과하면 결과물이 늦어진다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "정인이 과하면 자격과 절차가 앞서고, 식신의 반복 생산과 수입화가 뒤로 밀린다.")
        timing = "정인 운이 먼저 오면 문서와 기준이 잡히고, 식신 운이 뒤따르면 실제 결과물로 이어진다."
    elif category == "peer_generates_output":
        key = "peer_generates_output_exact"
        peer_face = "자기 기준과 독립성" if first_ten_god == "bi_gyeon" or second_ten_god == "bi_gyeon" else "경쟁심과 추진력"
        output_face = "반복 가능한 결과물" if first_ten_god == "sik_sin" or second_ten_god == "sik_sin" else "표현력과 돌파성"
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(peer_face)} {_euro_form(output_face)} 나가는 작용이다. "
            f"비겁의 힘이 안에서만 버티지 않고 식상으로 빠져나가야 {center}가 실제 결과를 얻는다."
        )
        risk = (
            "비겁이 과하면 결과물보다 지분과 주도권이 앞서고, "
            "식상이 약하면 움직임은 많아도 시장에 내놓을 성과가 부족하다."
        )
        timing = (
            f"{first_label} 운이 먼저 오면 첫 동력이 주도권을 만들고, "
            f"{second_label} 운이 뒤따르면 그 동력이 결과물이나 표현으로 드러난다."
        )
    elif category == "resource_generates_peer":
        key = "resource_generates_peer_exact"
        resource_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "resource")
        peer_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "peer")
        resource_face = "정식 문서와 보호" if resource_ten_god == "jeong_in" else "특수한 이해와 비정형 준비"
        peer_face = "자기 기반" if peer_ten_god == "bi_gyeon" else "경쟁력과 지분 의식"
        peer_risk_face = "자기 기준과 보수성" if peer_ten_god == "bi_gyeon" else "분점, 주도권, 지분 경쟁"
        pattern_exact_effects = {
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"{_subject_form(resource_face)} {_euro_form(peer_face)} 이어지면 문서와 보호가 자기 기반을 두껍게 만들며, 과하면 인비과중으로 닫힌다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 몰입이 격의 중심이다. "
                f"{_subject_form(resource_face)} {_euro_form(peer_face)} 이어지면 비정형 전문성이 독립성과 경쟁력으로 굳어진다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 비겁이 격의 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 강한 자기 기반에 명분과 보호가 붙어 독립성이 더 두꺼워진다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 양인의 강한 기세가 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 추진력에 명분이 붙지만, 과하면 승부성과 고집이 강해진다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 돈을 실행하기보다 명분과 자기 기준이 재물 판단에 개입한다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 외부 거래를 독립적으로 처리할 근거가 생기지만, 과하면 사람과 지분 문제가 커진다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 직책을 맡을 자기 기반은 강해지나, 관의 질서보다 자기 기준이 앞서는지 본다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 압박이 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 강한 책임을 버틸 체력이 생기지만, 과하면 압박에 맞서는 고집이 된다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 생산성이 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 결과물을 만들기 전 준비와 자기 기준이 두꺼워진다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현이 중심이다. "
                f"{_subject_form(resource_face)} 비겁을 생하면 자기 확신이 강해져 표현력은 분명해지지만, 정제되지 않으면 반발성이 커진다."
            ),
        }
        pattern_exact_risks = {
            "direct_resource_pattern": "재성이나 식상이 길을 열지 못하면 인비과중이 되어 문서, 명분, 자기 기준이 실행을 늦춘다.",
            "indirect_resource_pattern": "편인이 비겁을 과하게 생하면 전문성은 깊어도 고립, 독단, 비정형 판단이 강해진다.",
            "jianlu_peer_pattern": "관성이 정리하지 못하면 강한 독립성이 협력보다 자기 기준과 분재 문제로 나타난다.",
            "yangren_peer_pattern": "제어 장치가 약하면 명분이 붙은 승부욕이 되어 충돌과 지분 다툼이 커진다.",
            "direct_wealth_pattern": "재성이 약하면 돈보다 명분과 자기 기준이 앞서 재물 실행이 늦어진다.",
            "indirect_wealth_pattern": "관성이 약하면 외부 거래가 동업, 지분, 권리 배분 문제로 흔들린다.",
            "direct_officer_pattern": "관성이 약하면 자기 기준이 직책 질서를 앞서고, 인성이 과하면 절차와 명분만 늘어난다.",
            "seven_killings_pattern": "식신이나 인성이 균형을 잡지 못하면 압박을 버티는 힘이 고집과 충돌로 바뀐다.",
            "eating_god_pattern": "식상이 약하면 준비와 자기 기준이 결과물을 대신해 수입화가 늦어진다.",
            "hurting_officer_pattern": "인성이 상관을 정제하지 못하면 자기 확신이 말과 태도의 충돌로 드러난다.",
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(resource_face)} {_euro_form(peer_face)} 이어지는 작용이다. "
            f"{pattern_exact_effects.get(pattern, f'인성이 비겁을 생하면 공부, 자격, 보호가 자기 힘을 키워 {_object_form(center)} 떠받친다.')}"
        )
        risk = pattern_exact_risks.get(
            pattern,
            f"인성이 과하면 실행보다 준비와 명분이 길어지고, 비겁이 과하면 배운 힘이 협력보다 {peer_risk_face}으로 나타난다.",
        )
        timing = (
            f"{first_label} 운이 먼저 오면 첫 작용이 기반을 만들고, "
            f"{second_label} 운이 뒤따르면 그 기반이 자기 주장, 독립, 경쟁으로 현실화된다."
        )
    elif category == "officer_generates_resource":
        key = "officer_generates_resource_exact"
        officer_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "officer")
        resource_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "resource")
        officer_face = "공식 책임과 평가" if officer_ten_god == "jeong_gwan" else "압박과 위험 책임"
        resource_face = "정식 자격과 문서" if resource_ten_god == "jeong_in" else "특수한 보호와 학습"
        pattern_exact_effects = {
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 격의 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 직책과 평판이 문서, 승인, 자격으로 안정된다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 편관의 살기를 어떻게 받아내는지가 핵심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 넘어가면 강한 압박이 보호 장치와 전문성으로 흡수된다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 들어오면 직책과 제도가 자격, 문서, 보호 기반을 보강한다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 이해와 몰입이 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 들어오면 압박이 전문 영역과 비정형 학습의 이유가 된다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관이 관성을 건드리기 쉽다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 표현과 문제 제기가 문서, 품격, 자격으로 정리된다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 결과물이 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 생산물이 공식 책임과 문서 절차를 거쳐 신뢰를 얻는다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재물의 안정성이 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 돈에서 생긴 책임이 문서, 자격, 보호 장치로 굳어진다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 큰 거래가 신용, 문서, 자격의 보호를 얻는다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 자기 기반이 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 강한 독립성이 직책과 명분을 통해 안정된다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세가 중심이다. "
                f"{_subject_form(officer_face)} {_euro_form(resource_face)} 이어지면 거친 추진력이 자격, 문서, 제도적 보호로 흡수된다."
            ),
        }
        pattern_exact_risks = {
            "direct_officer_pattern": "인성이 과하면 책임의 실행보다 절차와 명분이 늘고, 인성이 약하면 직책을 받쳐 줄 근거가 부족하다.",
            "seven_killings_pattern": "인성이 약하면 살이 보호로 넘어가지 못하고 압박, 경쟁, 위기 책임으로 남는다.",
            "direct_resource_pattern": "관성이 과하면 인성은 보호가 아니라 책임을 버티는 장치로 소모된다.",
            "indirect_resource_pattern": "편관과 편인이 함께 과하면 압박이 전문성을 만들기보다 고립과 불안정한 판단을 키운다.",
            "hurting_officer_pattern": "인성이 약하면 상관의 표현을 정리하지 못해 말, 태도, 평판 문제가 남는다.",
            "eating_god_pattern": "인성이 과하면 생산 속도가 다시 늦어지고, 관성이 과하면 결과물보다 책임이 앞선다.",
            "direct_wealth_pattern": "인성이 과하면 재물 실행이 절차와 명분에 묶이고, 관성이 과하면 돈이 책임 문서로 굳어진다.",
            "indirect_wealth_pattern": "인성이 약하면 큰 거래를 보호할 문서와 명분이 부족하고, 관살이 과하면 확장이 압박으로 바뀐다.",
            "jianlu_peer_pattern": "관성이 약하면 책임이 자격으로 이어지지 못하고, 인성이 과하면 독립성에 명분만 두꺼워진다.",
            "yangren_peer_pattern": "인성이 약하면 압박이 보호로 넘어가지 못하고, 과하면 강한 기세에 명분만 붙어 충돌이 커진다.",
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(officer_face)} {_euro_form(resource_face)} 정리되는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '관성이 인성을 생하면 부담이 단순 압박으로 끝나지 않고 자격, 문서, 보호 장치로 넘어간다.')}"
        )
        risk = pattern_exact_risks.get(
            pattern,
            "인성이 약하면 책임을 받아낼 장치가 부족하고, 인성이 과하면 실제 수행보다 절차와 명분이 커진다.",
        )
        timing = (
            f"{first_label} 운이 먼저 오면 첫 작용이 책임의 성격을 열고, "
            f"{second_label} 운이 뒤따르면 그 책임이 문서, 자격, 보호 장치로 정리된다."
        )
    elif category == "resource_controls_output":
        key = "resource_controls_output_exact"
        resource_face = "정식 기준과 명분" if first_ten_god == "jeong_in" or second_ten_god == "jeong_in" else "특수한 판단과 몰입"
        output_face = "반복 생산" if first_ten_god == "sik_sin" or second_ten_god == "sik_sin" else "표현과 반발성"
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(resource_face)} {_object_form(output_face)} 제어하는 작용이다. "
            f"인성이 식상을 누르면 말과 결과물이 정제되지만, 과하면 {center}가 밖으로 드러나는 속도가 늦어진다."
        )
        risk = (
            "인성이 필요한 만큼만 작용하면 품질과 근거가 생기지만, "
            "인성이 지나치면 생각, 허가, 문서가 실행을 대신한다."
        )
        timing = (
            f"{first_label} 운이 먼저 오면 첫 작용의 제어가 먼저 생기고, "
            f"{second_label} 운이 뒤따르면 표현, 생산, 결과물의 성패가 드러난다."
        )
    elif category == "wealth_controls_resource":
        key = "wealth_controls_resource_exact"
        wealth_ten_god = first_ten_god if first_ten_god in {"jeong_jae", "pyeon_jae"} else second_ten_god
        resource_ten_god = first_ten_god if first_ten_god in {"jeong_in", "pyeon_in"} else second_ten_god
        wealth_face = "고정 소유와 정산 기준" if wealth_ten_god == "jeong_jae" else "외부 거래와 유동 자금"
        resource_face = "정식 문서, 자격, 보호 기반" if resource_ten_god == "jeong_in" else "특수 판단, 비정형 학습, 숨은 준비"
        pattern_exact_effects = {
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 {_subject_form(wealth_face)} 격의 중심이므로, "
                f"{_object_form(resource_face)} 현실 재물의 기준 아래로 끌어와 소유권, 증빙, 정산을 분명하게 만든다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 {_subject_form(wealth_face)} 격의 중심이므로, "
                f"{_object_form(resource_face)} 거래 판단과 회수 가능성의 기준 아래로 끌어와 기회를 돈으로 바꾸게 한다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 {_subject_form(resource_face)} 격의 중심이다. "
                f"재성이 이를 치면 인성이 과할 때는 현실 실행을 여는 약이 되고, 인성이 약할 때는 문서와 보호 기반을 직접 흔든다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 {_subject_form(resource_face)} 격의 중심이다. "
                f"재성이 이를 치면 특수한 몰입을 시장성으로 끌어내지만, 인성이 약하면 전문성과 준비 기반이 흩어진다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관인상생의 보호축이 관의 신뢰를 받친다. "
                f"재성이 {_object_form(resource_face)} 치면 직책의 현실 근거를 만들 수도 있지만, 지나치면 명분과 문서가 약해진다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 인성이 편관의 살기를 받아내는 보호 장치다. "
                f"재성이 {_object_form(resource_face)} 치면 현실 판단은 빨라지지만, 인성이 약하면 압박을 흡수할 장치가 줄어든다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 생산성이 중심이다. "
                f"재성이 {_object_form(resource_face)} 치면 도식의 병을 낮춰 결과물이 밖으로 나오지만, 과하면 돈의 요구가 생산의 안정성을 흔든다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 변통성이 중심이다. "
                f"재성이 {_object_form(resource_face)} 치면 명분에 묶인 표현을 시장성으로 돌리지만, 과하면 계약과 평판이 급해진다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 자기 기반과 독립성이 중심이다. "
                f"재성이 {_object_form(resource_face)} 치면 명분과 보호 안에 머문 힘을 현실 재정 판단으로 끌어낸다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 기세와 결단성이 중심이다. "
                f"재성이 {_object_form(resource_face)} 치면 기세를 손익 판단으로 낮추지만, 거칠면 보호 장치 없이 돈과 승부가 앞선다."
            ),
        }
        pattern_exact_risks = {
            "direct_wealth_pattern": "재성이 과하면 문서와 자격이 재물 문제에 종속되고, 재성이 약하면 인성이 재물 실행을 늦춘다.",
            "indirect_wealth_pattern": "재성이 과하면 보호 장치보다 거래가 앞서고, 재성이 약하면 기회가 판단과 준비 안에서 머문다.",
            "direct_resource_pattern": "인성이 필요한 사주에서 재성이 강하게 치면 학업, 자격, 문서, 보호자의 문제가 먼저 드러난다.",
            "indirect_resource_pattern": "편인의 전문성이 약할 때 재성이 강하면 비정형 판단이 거래 손실과 산만한 수입 문제로 바뀐다.",
            "direct_officer_pattern": "관을 받치는 인성이 손상되면 직책은 생겨도 명분, 문서, 승인, 상급자의 보호가 약해진다.",
            "seven_killings_pattern": "편관을 받아낼 인성이 약한데 재성이 강하면 돈, 책임, 위험, 문서 부담이 한꺼번에 커진다.",
            "eating_god_pattern": "재성이 도식을 풀어 주는 정도를 넘으면 꾸준한 생산보다 수익 요구가 앞서 식신이 흐려진다.",
            "hurting_officer_pattern": "재성이 상관을 시장성으로 돌리지 못하고 과하면 말, 계약, 평판, 회수 문제가 동시에 생긴다.",
            "jianlu_peer_pattern": "재성이 약하면 인비가 두터워 실행이 늦고, 재성이 과하면 자격과 문서보다 돈 문제가 앞선다.",
            "yangren_peer_pattern": "재성이 양인의 기세를 절제하지 못하면 손익 판단이 승부욕과 섞여 지분, 충돌, 손실로 번진다.",
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(wealth_face)} {_object_form(resource_face)} 누르는 작용이다. "
            f"{pattern_exact_effects.get(pattern, f'이 작용은 {center}을 기준으로 필요한 제어인지, 손상인지 다시 판정한다.')}"
        )
        risk = pattern_exact_risks.get(
            pattern,
            "재성이 필요한 인성을 치면 문서와 보호가 손상되고, 과다한 인성을 치면 실행을 열어 주는 약이 된다.",
        )
        timing = f"{first_label} 운이 먼저 오면 현실 요구가 강해지고, {second_label} 운이 뒤따르면 문서와 명분 문제가 함께 드러난다."
    elif category == "wealth_generates_officer":
        key = "wealth_generates_officer_exact"
        wealth_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "wealth")
        officer_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "officer")
        wealth_face = "소유권과 고정 수입" if wealth_ten_god == "jeong_jae" else "외부 자금과 거래 확장"
        officer_face = "공식 직책과 신용" if officer_ten_god == "jeong_gwan" else "강한 책임과 위험 부담"
        pattern_exact_effects = {
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                f"{_subject_form(wealth_face)} {_euro_form(officer_face)} 올라가면 재물이 신용, 직책, 공적 책임으로 전환된다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                f"{_subject_form(wealth_face)} {_euro_form(officer_face)} 올라가면 외부 자원이 사업 책임과 사회적 신뢰로 커진다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 격의 중심이다. "
                f"{_subject_form(wealth_face)} 관을 생하면 직책과 평판을 받치는 현실 기반이 생긴다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 재성이 살을 생하는지 먼저 본다. "
                f"{_subject_form(wealth_face)} {_euro_form(officer_face)} 올라가면 큰 책임과 권한이 되거나, 제어가 약하면 위험 부담이 커진다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                f"{_subject_form(wealth_face)} 관을 생하면 독립성이 돈을 거쳐 직책과 공식 책임으로 정리된다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 주도권이 중심이다. "
                f"{_subject_form(wealth_face)} 관살을 생하면 추진력이 권한과 책임으로 올라가지만 제어 장치가 반드시 필요하다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 생산물이 중심이다. "
                f"{_subject_form(wealth_face)} 관을 생하면 결과물이 보상에 그치지 않고 평가와 책임의 근거가 된다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 표현과 변통성이 중심이다. "
                f"{_subject_form(wealth_face)} 관을 생하면 상관의 시장성이 직책과 공식 평가로 연결된다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 중심이다. "
                + (
                    f"{_subject_form(wealth_face)} 정관을 생하면 현실 기반이 공식 직책을 만들고, 그 직책이 다시 문서와 자격을 받친다. 관인상생의 입구로 쓸 수 있다."
                    if officer_ten_god == "jeong_gwan"
                    else f"{_subject_form(wealth_face)} 편관을 생하면 먼저 재생살을 본다. 강한 책임과 압박이 생긴 뒤, 인성이 받아 주어야 살인상생으로 돌아선다."
                )
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 몰입이 중심이다. "
                + (
                    f"{_subject_form(wealth_face)} 정관을 생하면 비정형 지식이 제도권 책임과 공식 평가를 얻는다."
                    if officer_ten_god == "jeong_gwan"
                    else f"{_subject_form(wealth_face)} 편관을 생하면 특수한 몰입이 강한 압박과 위험 책임으로 시험받고, 인성이 받쳐야 전문성으로 굳어진다."
                )
            ),
        }
        pattern_exact_risks = {
            "direct_wealth_pattern": "관성이 과하면 재물이 권한이 아니라 책임 문서와 생활 부담으로 바뀐다.",
            "indirect_wealth_pattern": "편재가 편관을 생하면 큰 거래가 강한 압박과 위험 책임으로 바뀔 수 있다.",
            "direct_officer_pattern": "재가 탁하거나 과하면 관의 청정성이 흐려져 책임은 커지고 명예는 무거워진다.",
            "seven_killings_pattern": "식신이나 인성이 받치지 않으면 재생살이 되어 돈, 책임, 위험이 함께 커진다.",
            "jianlu_peer_pattern": "관성이 약하면 돈은 생겨도 사회적 책임으로 묶이지 않고, 관성이 과하면 독립성이 눌린다.",
            "yangren_peer_pattern": "식신이나 인성이 받치지 않으면 재생살로 기울어 돈이 권한보다 위험 부담을 키운다.",
            "eating_god_pattern": "관성이 과하면 편안한 생산성이 절차와 책임에 묶이고, 재성이 약하면 결과물이 평가로 올라가지 못한다.",
            "hurting_officer_pattern": "재성이 매개하지 못하면 상관이 관을 바로 쳐 상관견관의 병이 먼저 드러난다.",
            "direct_resource_pattern": (
                "재성이 인성을 먼저 손상하면 관인상생으로 이어지기 전에 문서와 보호 기반이 흔들린다."
                if officer_ten_god == "jeong_gwan"
                else "인성이 편관을 받아 주지 못하면 재생살이 되어 돈, 책임, 압박이 문서와 보호 기반을 누른다."
            ),
            "indirect_resource_pattern": (
                "정관이 과하면 편인의 전문성이 제도권 책임 안에 갇혀 속도가 늦어진다."
                if officer_ten_god == "jeong_gwan"
                else "편관이 과하면 편인의 전문성은 보호가 아니라 고립된 압박과 불안정한 책임으로 바뀐다."
            ),
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(wealth_face)} {_euro_form(officer_face)} 올라가는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '재성이 관성을 생하면 재물과 현실 기반이 직책, 평가, 책임으로 올라간다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "관성이 과하면 돈이 권한이 아니라 책임으로 바뀌고, 일간이 약하면 재물보다 부담이 먼저 커진다.")
        timing = f"{first_label} 운이 먼저 오면 돈과 계약이 열리고, {second_label} 운이 뒤따르면 직책, 평가, 책임으로 결론 난다."
    elif category == "output_generates_wealth":
        key = "output_generates_wealth_exact"
        output_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "output")
        wealth_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "wealth")
        output_face = "반복 가능한 기술과 상품" if output_ten_god == "sik_sin" else "표현, 기획, 노출, 돌파성"
        wealth_face = "고정 수입과 축적" if wealth_ten_god == "jeong_jae" else "외부 거래와 확장 수익"
        pattern_exact_effects = {
            "eating_god_pattern": (
                f"{pattern_label}에서는 식신의 생산성이 격의 중심이다. "
                f"{_subject_form(output_face)} {_euro_form(wealth_face)} 넘어가면 반복 가능한 결과물이 수입의 근거가 된다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 상관의 표현과 변통성이 격의 중심이다. "
                f"{_subject_form(output_face)} {_euro_form(wealth_face)} 넘어가면 기획, 노출, 설득이 시장성과 거래로 바뀐다."
            ),
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                f"{_subject_form(output_face)} 재성을 생하면 기술과 결과물이 안정 수입의 공급원이 된다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                f"{_subject_form(output_face)} 재성을 생하면 영업, 기획, 서비스가 외부 수익의 입구가 된다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                f"{_subject_form(output_face)} {_euro_form(wealth_face)} 넘어가면 비겁의 힘이 경쟁에 머물지 않고 재물로 빠져나간다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 거친 주도권이 중심이다. "
                f"{_subject_form(output_face)} {_euro_form(wealth_face)} 넘어가면 추진력이 결과물과 수익으로 전환된다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 격의 중심이다. "
                f"{_subject_form(output_face)} 재성을 생하면 직책 안에서 만든 성과가 보상과 생활 기반으로 내려온다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 압박을 처리하는 힘이 중요하다. "
                f"{_subject_form(output_face)} 재성을 생하면 어려운 일을 처리한 결과가 실적과 보상으로 바뀐다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"{_subject_form(output_face)} 재성을 생하면 배운 것과 문서 기반이 결과물과 수입으로 현실화된다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 이해와 몰입이 중심이다. "
                f"{_subject_form(output_face)} 재성을 생하면 특수 지식이 상품, 서비스, 비정형 수익으로 나온다."
            ),
        }
        pattern_exact_risks = {
            "eating_god_pattern": "재성이 약하거나 비겁이 개입하면 만든 것은 있어도 소유와 정산이 흐려진다.",
            "hurting_officer_pattern": "상관이 과하면 돈보다 말과 충돌이 앞서 계약과 평판을 흔든다.",
            "direct_wealth_pattern": "결과물이 약하면 재성은 있어도 수입의 지속성이 떨어진다.",
            "indirect_wealth_pattern": "상관 쪽으로 과하면 확장은 빠르지만 회수와 정산이 늦어진다.",
            "jianlu_peer_pattern": "식상이 약하면 강한 기운이 재성으로 가지 못하고 경쟁과 고집으로 남는다.",
            "yangren_peer_pattern": "상관으로 과하게 빠지면 속도와 확장은 크지만 회수, 정산, 평판이 흔들린다.",
            "direct_officer_pattern": "상관이 강하면 성과보다 조직 질서와의 마찰이 앞서 보상이 평판 문제로 바뀔 수 있다.",
            "seven_killings_pattern": "재성이 다시 살을 생하면 수입이 새로운 책임과 위험 부담을 키우는 순환이 생긴다.",
            "direct_resource_pattern": "인성이 과하면 결과물이 늦고, 재성이 과하면 문서와 학업 기반이 돈의 요구에 눌린다.",
            "indirect_resource_pattern": "식상이 약하면 전문성은 깊어도 시장에 내놓는 힘이 부족하고, 재성이 과하면 집중이 흩어진다.",
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(output_face)} {_euro_form(wealth_face)} 넘어가는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '식상이 재성을 생하면 결과물, 기술, 표현이 수입과 거래로 전환된다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "결과물이 약하면 수입의 근거가 약하고, 상관이 과하면 말과 기획이 앞서 회수와 정산이 늦어진다.")
        timing = f"{first_label} 운이 먼저 오면 결과물이 생기고, {second_label} 운이 뒤따르면 수입과 거래로 전환된다."
    elif category == "peer_controls_wealth":
        key = "peer_controls_wealth_exact"
        peer_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "peer")
        wealth_ten_god = next(tg for tg in (first_ten_god, second_ten_god) if TEN_GOD_GROUPS[tg] == "wealth")
        peer_face = "동등한 주체와 분재" if peer_ten_god == "bi_gyeon" else "경쟁자, 지분, 분탈"
        peer_behavior = "공동 소유, 동등한 몫, 자기 기준" if peer_ten_god == "bi_gyeon" else "주도권 경쟁, 지분 다툼, 분탈성"
        wealth_face = "고정 소유와 생활 재정" if wealth_ten_god == "jeong_jae" else "외부 자금과 거래 이익"
        pattern_exact_effects = {
            "direct_wealth_pattern": (
                f"{pattern_label}에서는 재성이 격의 중심이다. "
                f"{_subject_form(peer_face)} {_object_form(wealth_face)} 치면 소유권과 정산 기준에 {peer_behavior}이 개입한다."
            ),
            "indirect_wealth_pattern": (
                f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                f"{_subject_form(peer_face)} {_object_form(wealth_face)} 치면 사람을 통해 기회가 열리지만 회수, 지분, 공동 자금 문제가 함께 생긴다."
            ),
            "eating_god_pattern": (
                f"{pattern_label}에서는 생산물이 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 만든 결과물에서 생긴 수입을 사람과 몫의 문제로 나누게 된다."
            ),
            "hurting_officer_pattern": (
                f"{pattern_label}에서는 표현과 기획이 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 말과 확장으로 만든 수익에 경쟁자, 권리, 지분 문제가 붙는다."
            ),
            "jianlu_peer_pattern": (
                f"{pattern_label}에서는 비겁 자체가 격의 중심이다. "
                f"{_subject_form(peer_face)} {_object_form(wealth_face)} 치면 재물이 생길 때 내 몫과 공동 기준을 먼저 세우려 한다."
            ),
            "yangren_peer_pattern": (
                f"{pattern_label}에서는 강한 비겁의 기세가 중심이다. "
                f"{_subject_form(peer_face)} {_object_form(wealth_face)} 치면 돈 문제에 주도권과 승부성이 강하게 붙는다."
            ),
            "direct_officer_pattern": (
                f"{pattern_label}에서는 관성이 격의 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 직책과 평판을 받칠 현실 기반에 사람과 몫 문제가 끼어든다."
            ),
            "seven_killings_pattern": (
                f"{pattern_label}에서는 압박과 책임이 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 위험 책임 속에서 돈과 사람의 주도권 문제가 함께 올라온다."
            ),
            "direct_resource_pattern": (
                f"{pattern_label}에서는 인성이 격의 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 문서와 자격을 수입으로 바꾸는 과정에 자기 기준과 주변 몫이 들어온다."
            ),
            "indirect_resource_pattern": (
                f"{pattern_label}에서는 특수한 전문성이 중심이다. "
                f"{_subject_form(peer_face)} 재성을 치면 비정형 수익 구조에 동료, 공동 작업, 권리 배분이 끼어든다."
            ),
        }
        pattern_exact_risks = {
            "direct_wealth_pattern": "관성의 규칙이 약하면 가까운 사람과의 소유권, 정산, 생활 재정 문제가 재성을 흐린다.",
            "indirect_wealth_pattern": "겁재가 강하면 사업 자금, 투자금, 동업 지분에서 손실과 분쟁이 생기기 쉽다.",
            "eating_god_pattern": "비겁이 과하면 만든 결과보다 동업자, 가족, 동료의 지분 문제가 먼저 커진다.",
            "hurting_officer_pattern": "겁재가 강하면 말과 확장이 빠른 만큼 정산, 공동 수익, 권리 다툼이 커진다.",
            "jianlu_peer_pattern": "관성의 기준이 약하면 재물보다 경쟁과 분배 문제가 앞서 재성이 탁해진다.",
            "yangren_peer_pattern": "제어가 약하면 큰 추진력보다 겁재쟁재가 먼저 드러난다.",
            "direct_officer_pattern": "관성이 정리하지 못하면 동료, 경쟁자, 가족의 돈 문제가 공식 책임과 평판까지 흔든다.",
            "seven_killings_pattern": "겁재가 강하면 위험한 책임, 손실 부담, 동업 갈등이 한꺼번에 커질 수 있다.",
            "direct_resource_pattern": "비겁이 과하면 재성이 인성을 조절하기 전에 사람 문제와 분배 문제가 먼저 커진다.",
            "indirect_resource_pattern": "겁재가 강하면 비정형 수익 구조에서 권리와 정산이 흐려질 수 있다.",
        }
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(peer_face)} {_object_form(wealth_face)} 건드리는 작용이다. "
            f"{pattern_exact_effects.get(pattern, '비견은 나눔과 공동 기준으로, 겁재는 쟁재와 지분 다툼으로 더 강하게 드러난다.')}"
        )
        risk = pattern_exact_risks.get(pattern, "관성이 정리하지 못하면 가까운 사람, 동업자, 가족 사이에서 몫과 소유권 문제가 커진다.")
        timing = f"{first_label} 운이 먼저 오면 사람이 끼고, {second_label} 운이 뒤따르면 돈과 지분 문제가 현실화된다."
    elif category == "officer_controls_peer":
        key = "officer_controls_peer_exact"
        officer_face = "강한 압박과 통제" if first_ten_god == "pyeon_gwan" else "공식 기준과 책임"
        peer_face = "자기 기준" if second_ten_god == "bi_gyeon" else "경쟁과 지분"
        effect = (
            f"{pattern_label}에서 {_topic_form(name)} {_subject_form(officer_face)} {_object_form(peer_face)} 제어하는 작용이다. "
            f"관성이 살아 있으면 비겁의 경쟁성과 쟁재를 규칙, 직책, 책임 기준으로 묶는다."
        )
        risk = "관성이 약하면 제어가 되지 않고, 관성이 과하면 자립성과 추진력이 압박으로 눌린다."
        timing = f"{first_label} 운이 먼저 오면 규칙과 책임이 생기고, {second_label} 운이 뒤따르면 사람과 몫 문제가 정리되거나 충돌한다."
    elif category == "officer_same_group":
        if {first_ten_god, second_ten_god} == {"jeong_gwan", "pyeon_gwan"}:
            key = "gwansal_honhap"
            pattern_exact_effects = {
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 정관의 청정성과 제도권 신뢰가 격의 중심이다. "
                    "편관이 섞이면 공식 직책 위에 강한 압박과 위험 책임이 얹혀 관살혼잡으로 판정한다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박과 위기 책임이 격의 중심이다. "
                    "정관이 함께 오면 살의 거친 기세가 제도권 책임으로 정리될 수 있으나, 정리 장치가 약하면 책임 기준이 흔들린다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 격의 중심이다. "
                    "정관과 편관이 함께 작용하면 재물이 신용과 직책을 만들면서도 보증, 책임 문서, 법적 부담을 함께 부른다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 거래와 확장이 격의 중심이다. "
                    "관살이 섞이면 큰 거래가 공식 평가와 위험 부담을 동시에 만들므로 계약의 권한과 책임 범위가 핵심이 된다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 격의 중심이다. "
                    "관살혼잡은 인성이 받아야 할 책임의 성격을 복잡하게 만들며, 문서와 승인 체계가 강해야 약으로 쓴다."
                ),
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 특수한 이해와 몰입이 중심이다. "
                    "관살이 섞이면 비정형 전문성이 제도권 요구와 위험 업무를 동시에 상대하게 된다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 처리력이 중심이다. "
                    "정관과 편관이 섞일 때 식신이 살아 있으면 공식 책임과 돌발 압박을 실무로 풀어낸다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현과 변통성이 중심이다. "
                    "관살혼잡은 상관견관의 위험을 키우므로 재성이나 인성이 중간에서 말과 책임을 정리해야 한다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                    "관살이 섞이면 독립성과 경쟁성이 공식 규칙과 강한 압박을 함께 받는다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 강한 주도권이 중심이다. "
                    "관살혼잡은 양인의 기세를 제어하는 동시에 위험 책임을 크게 만들 수 있다."
                ),
            }
            pattern_exact_risks = {
                "direct_officer_pattern": "인성이나 식신이 약하면 정관의 명예보다 편관의 압박이 앞서 직책, 감사, 책임 문제가 한꺼번에 커진다.",
                "seven_killings_pattern": "살을 제어하지 못하면 정관의 질서가 약이 되지 못하고 관살혼잡으로 경쟁, 처벌성 책임, 심사 부담이 커진다.",
                "direct_wealth_pattern": "재성이 약하거나 탁하면 관성이 재물을 지켜 주지 못하고, 돈이 책임 문서와 보증 부담으로 바뀐다.",
                "indirect_wealth_pattern": "편재가 강하게 관살을 생하면 외부 거래가 권한보다 법적 책임과 손실 부담을 먼저 키운다.",
                "direct_resource_pattern": "인성이 약하면 관살을 받아내지 못해 문서, 자격, 승인, 상급자의 보호가 흔들린다.",
                "indirect_resource_pattern": "편인이 고립되면 관살의 압박을 전문성으로 처리하지 못하고 불안정한 책임으로 남긴다.",
                "eating_god_pattern": "식신이 약하면 관살혼잡을 처리할 실무 장치가 부족해 압박과 반복 업무가 소모로 바뀐다.",
                "hurting_officer_pattern": "상관이 과하면 정관과 충돌하고, 편관까지 건드려 평판과 책임 문제가 동시에 커진다.",
                "jianlu_peer_pattern": "관성이 정리되지 않으면 강한 자립성이 제도와 충돌하고, 관성이 과하면 독립성이 눌린다.",
                "yangren_peer_pattern": "양인의 기세가 관살과 부딪히면 권한보다 사고성 책임과 강한 충돌이 먼저 드러난다.",
            }
            effect = (
                f"{pattern_label}에서 정관과 편관이 함께 작용하면 관살혼잡 여부를 먼저 본다. "
                f"{pattern_exact_effects.get(pattern, '정관은 공식 책임과 평판을 세우고 편관은 강한 압박과 위험 책임을 불러오므로, 둘이 섞이면 책임의 성격이 복잡해진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "인성이나 식신이 정리하지 못하면 공식 평가, 직책, 압박, 위험 부담이 한꺼번에 커진다.")
            timing = "정관 운은 공식 평가로, 편관 운은 경쟁과 압박으로 나타나며 함께 오면 책임의 무게가 커진다."
        elif first_ten_god == second_ten_god == "jeong_gwan":
            key = "direct_officer_overload_exact"
            pattern_exact_effects = {
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 정관이 격의 중심이다. "
                    "정관이 거듭되면 직책, 규정, 공식 평가가 뚜렷해지지만 관성이 과중하면 청정한 관이 부담으로 바뀐다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관을 다스리는 일이 우선이다. "
                    "정관이 거듭 들어오면 강한 살을 제도권 책임으로 낮추는 장치가 되지만, 살의 기세가 더 강하면 형식만 늘어난다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 관을 받아 문서와 명분을 세워야 한다. "
                    "정관이 중첩되면 자격, 승인, 기관 평가가 두꺼워지고 인성이 약하면 절차 부담이 된다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이므로 관성 중첩은 재물이 신용과 공식 책임으로 올라가는지 본다. "
                    "관이 지나치면 재산보다 의무와 심사 부담이 앞선다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 강한 비겁을 관성이 정리해야 한다. "
                    "정관 중첩은 자기 기준을 사회적 규칙과 직책 안에 묶는 힘이 된다."
                ),
            }
            pattern_exact_risks = {
                "direct_officer_pattern": "인성이 받치지 못하면 직책은 겹치는데 보호 장치가 약해 관성 과중이 된다.",
                "seven_killings_pattern": "편관의 살기가 더 강하면 정관의 질서가 약해지고 절차와 압박이 따로 논다.",
                "direct_resource_pattern": "인성이 약하면 관을 받아내지 못해 문서, 승인, 상급자 문제로 소모된다.",
                "direct_wealth_pattern": "재성이 약하면 관을 생할 현실 기반이 부족해 명예보다 책임 비용이 커진다.",
                "jianlu_peer_pattern": "관성이 과하면 강한 자립성이 사회 규칙에 눌려 움직임이 굳어진다.",
            }
            effect = (
                f"{pattern_label}에서 정관이 중첩되면 관성의 과중을 보되, 편관처럼 거친 압박보다 공식 책임과 평판의 중첩으로 본다. "
                f"{pattern_exact_effects.get(pattern, '직책, 심사, 규정, 조직 내 평가가 반복되어 안정성은 생기지만 움직임이 경직될 수 있다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "인성이 받치지 못하면 책임은 많은데 보호 장치가 약하고, 식상이 과하면 공식 질서와의 충돌이 커진다.")
            timing = "정관 운이 거듭 강해지면 승진, 직책, 평가, 규정, 공적 책임 문제가 반복해서 올라온다."
        elif first_ten_god == second_ten_god == "pyeon_gwan":
            key = "seven_killings_overload_exact"
            pattern_exact_effects = {
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박이 격의 중심이다. "
                    "편관이 거듭되면 권한, 경쟁, 위험 업무가 강해지며 식신제살이나 살인상생이 성립해야 쓸 수 있다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 정관의 질서가 중심이다. "
                    "편관 중첩은 정관의 청정성을 흐릴 수 있으므로 공식 책임이 위기 업무와 섞이는지 판정한다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신이 살을 제어할 수 있는지가 핵심이다. "
                    "편관이 거듭되어도 식신이 살아 있으면 어려운 일을 처리하는 실무 권한이 된다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 관살을 받아 명분과 문서로 바꾸어야 한다. "
                    "편관 중첩은 인성이 충분할 때 강한 책임을 자격과 권위로 바꾼다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 거래와 확장이 중심이다. "
                    "편관 중첩은 큰 거래 뒤에 오는 위험 책임과 압박을 뜻하므로 회수와 법적 책임이 중요하다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 양인의 기세가 중심이다. "
                    "편관 중첩은 강한 기세를 제어하는 장치가 될 수 있지만, 제어가 거칠면 충돌과 사고성 책임이 커진다."
                ),
            }
            pattern_exact_risks = {
                "seven_killings_pattern": "식신이나 인성이 없으면 관살과중이 되어 압박, 처벌성 책임, 사고성 업무가 과중해진다.",
                "direct_officer_pattern": "정관의 명분이 약하면 편관의 압박이 청정한 관을 탁하게 만들어 관살혼잡으로 기운다.",
                "eating_god_pattern": "식신이 약하면 제살이 되지 못하고 해야 할 일과 위험만 늘어난다.",
                "direct_resource_pattern": "인성이 약하면 살을 받아내지 못해 문서와 보호 없이 강한 책임만 남는다.",
                "indirect_wealth_pattern": "재성이 살을 계속 생하면 거래 확장이 권한보다 손실 책임과 법적 부담을 키운다.",
                "yangren_peer_pattern": "양인과 편관이 거칠게 부딪히면 강한 통제, 충돌, 사고성 책임으로 나타난다.",
            }
            effect = (
                f"{pattern_label}에서 편관이 중첩되면 관살과중 중에서도 경쟁, 압박, 위기 대응의 성격이 강하다. "
                f"{pattern_exact_effects.get(pattern, '권한보다 위험 책임이 먼저 커지고, 빠른 결단과 강한 통제 상황에 놓이기 쉽다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "식신이나 인성이 약하면 압박을 처리하지 못해 소모, 충돌, 사고성 책임으로 번질 수 있다.")
            timing = "편관 운이 거듭 강해지면 경쟁, 감사, 위기 업무, 강한 책임, 법적 부담이 사건화된다."
    elif category == "wealth_same_group":
        key = "wealth_overload_exact"
        if first_ten_god == second_ten_god == "jeong_jae":
            pattern_exact_effects = {
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 격의 중심이다. "
                    "정재가 거듭되면 생활 재정, 고정 수입, 소유 기준이 선명해지고 일간이 감당하면 축재의 틀이 된다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 외부 재물의 회전이 중심이다. "
                    "정재 중첩은 넓은 거래를 생활 재정과 고정 자산으로 묶어 두려는 작용이다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 격의 중심이다. "
                    "정재 중첩은 문서와 명분을 생활 재정의 요구로 누르므로, 인성이 과할 때는 실행의 약이고 약할 때는 문서 손상이다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 격의 중심이다. "
                    "정재 중첩은 관을 생할 안정 재원과 신용을 만들지만, 과하면 직책에 따른 생활 책임이 커진다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 강한 비겁이 중심이다. "
                    "정재 중첩은 자기 기준이 생활 재정과 소유권을 붙잡는 구조이며, 관성이 약하면 분재가 된다."
                ),
            }
            pattern_exact_risks = {
                "direct_wealth_pattern": "일간이 약하면 재성이 중심이어도 재다신약으로 바뀌어 돈의 규모보다 관리 책임이 앞선다.",
                "indirect_wealth_pattern": "편재의 회전성이 약하면 정재는 자산화가 아니라 고정비와 묶인 돈으로 굳어진다.",
                "direct_resource_pattern": "인성이 약하면 재극인이 되어 학업, 자격, 문서 기반이 생활 재정 문제에 눌린다.",
                "direct_officer_pattern": "재성이 탁하면 관을 생하기보다 직책 비용, 부양 책임, 승인 부담을 키운다.",
                "jianlu_peer_pattern": "비겁이 강하면 정재가 안정 자산이 아니라 공동 명의, 가족 돈, 분배 문제로 흔들린다.",
            }
            effect = (
                f"{pattern_label}에서 정재가 중첩되면 재다신약 여부와 함께 소유, 저축, 고정 수입의 반복성을 본다. "
                f"{pattern_exact_effects.get(pattern, '돈의 폭보다 생활 기반, 자산 명의, 정산 기준이 선명해진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "일간이 감당하지 못하면 고정비, 생활 책임, 가족 재정, 자산 관리 부담이 먼저 커진다.")
            timing = "정재 운이 거듭 강해지면 월급, 생활비, 자산 취득, 고정 지출, 소유권 문제가 반복해서 올라온다."
        elif first_ten_god == second_ten_god == "pyeon_jae":
            pattern_exact_effects = {
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 편재의 거래성, 유동 자금, 사업 확장이 격의 중심이다. "
                    "편재가 거듭되면 외부 제안과 투자성이 커지며 회수 기준을 세울 때 재물 규모가 커진다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 정재의 소유 기준이 중심이다. "
                    "편재 중첩은 안정 재산 바깥의 거래와 확장을 열지만, 정재의 기준이 약하면 돈이 흩어진다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박을 다루어야 한다. "
                    "편재 중첩은 살을 생하는 자금과 거래가 되기 쉬워 재생살 여부를 먼저 본다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "편재 중첩은 직책을 받치는 외부 자원과 실적이 되지만, 과하면 평가보다 책임 거래가 앞선다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 시장성이 중심이다. "
                    "편재 중첩은 기획과 노출을 큰 거래로 키우지만, 회수 장치가 없으면 말과 거래가 먼저 커진다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 강한 주도권이 중심이다. "
                    "편재 중첩은 승부성 있는 자금 운용과 외부 확장을 만들지만 겁재가 붙으면 손실 폭도 커진다."
                ),
            }
            pattern_exact_risks = {
                "indirect_wealth_pattern": "일간이 약하거나 관성이 정리하지 못하면 편재는 사업 확장이 아니라 과확장, 투자 손실, 회수 지연으로 바뀐다.",
                "direct_wealth_pattern": "정재의 기준이 약하면 편재가 소유를 키우지 못하고 외부 거래와 지출로 빠져나간다.",
                "seven_killings_pattern": "편재가 편관을 계속 생하면 재생살로 기울어 돈, 책임, 위험이 함께 커진다.",
                "direct_officer_pattern": "편재가 탁하면 관을 생하기보다 실적 압박, 접대성 지출, 책임 거래를 키운다.",
                "hurting_officer_pattern": "상관이 과하면 편재 확장이 계약 회수보다 홍보와 말의 속도를 앞세운다.",
                "yangren_peer_pattern": "겁재가 강하면 외부 자금과 투자금이 주도권 다툼, 지분 분쟁, 손실로 번진다.",
            }
            effect = (
                f"{pattern_label}에서 편재가 중첩되면 재다신약 중에서도 외부 거래, 투자, 영업, 사업 확장의 폭을 본다. "
                f"{pattern_exact_effects.get(pattern, '돈의 길은 넓어지지만 회수와 통제 장치가 따르지 않으면 흔들림도 커진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "일간이 약하거나 관성이 정리하지 못하면 과확장, 투자 손실, 회수 지연, 거래처 부담이 먼저 드러난다.")
            timing = "편재 운이 거듭 강해지면 투자, 영업, 외부 제안, 사업 확장, 큰 거래의 성패가 사건화된다."
        else:
            pattern_exact_effects = {
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 정재의 소유 기준이 중심이다. "
                    "정재와 편재가 함께 있으면 안정 자산을 지키면서 외부 거래를 받아들일 수 있는지 판정한다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 편재의 확장이 중심이다. "
                    "정재가 함께 있으면 큰 거래를 생활 기반과 소유 기준으로 묶어 두는 힘이 생긴다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 격의 중심이다. "
                    "정편재 혼재는 인성을 현실 요구로 누르되, 정재는 생활 문제로, 편재는 외부 거래 문제로 다르게 작동한다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관을 제어해야 한다. "
                    "정편재 혼재가 관살을 생하면 안정 재정과 외부 자금이 함께 책임을 키우므로 재생살 여부를 판정한다."
                ),
            }
            pattern_exact_risks = {
                "direct_wealth_pattern": "정재의 기준보다 편재의 확장이 앞서면 소유는 약해지고 거래와 지출이 커진다.",
                "indirect_wealth_pattern": "편재의 회전보다 정재의 묶임이 강하면 확장성이 둔해지고 고정비가 커진다.",
                "direct_resource_pattern": "재극인이 과하면 정식 문서와 보호 기반이 생활비와 외부 거래 요구에 함께 눌린다.",
                "seven_killings_pattern": "편재 쪽이 강하게 관살을 생하면 책임과 위험 부담이 재물보다 먼저 커진다.",
            }
            effect = (
                f"{pattern_label}에서 정재와 편재가 함께 있으면 소유와 확장을 동시에 본다. "
                f"{pattern_exact_effects.get(pattern, '정재는 남기는 돈이고 편재는 벌려 들어오는 돈이므로, 축적 기준과 거래 확장 사이의 균형이 핵심이다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "정재가 약하면 번 돈이 남지 않고, 편재가 과하면 확장 속도가 관리 능력을 앞지른다.")
            timing = "정재 운은 자산과 정산으로, 편재 운은 투자와 거래로 드러나며 함께 오면 돈의 규모와 관리 문제가 동시에 커진다."
    elif category == "output_same_group":
        key = "output_overload_exact"
        if first_ten_god == second_ten_god == "sik_sin":
            pattern_exact_effects = {
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 안정 생산성이 격의 중심이다. "
                    "식신이 거듭되면 기술, 품질, 반복 가능한 결과물이 두꺼워지고 재성이 받으면 안정 수입의 근거가 된다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현과 돌파성이 격의 중심이다. "
                    "식신 중첩은 상관의 날카로움을 낮추고 결과물의 안정성을 더하지만, 확장 속도는 둔해질 수 있다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 격의 중심이다. "
                    "식신 중첩은 재물을 생하는 공급원이며, 꾸준한 기술과 상품이 생활 수입을 받친다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 거래와 확장이 중심이다. "
                    "식신 중첩은 큰 확장보다 반복 판매와 서비스 품질을 통해 외부 수익을 안정시킨다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 격의 중심이다. "
                    "식신 중첩은 직책의 책임을 실제 성과로 풀어 주지만, 과하면 공식 기준을 느슨하게 볼 수 있다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박을 다스려야 한다. "
                    "식신 중첩은 식신제살의 처리력을 키워 위험 업무와 강한 책임을 실무로 낮춘다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 격의 중심이다. "
                    "식신 중첩은 배운 것과 문서를 결과물로 꺼내는 힘이지만, 인성을 지나치게 설기하면 근거가 약해진다."
                ),
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 특수한 이해가 중심이다. "
                    "식신 중첩은 비정형 지식을 반복 가능한 서비스와 상품으로 바꾸는 통로가 된다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                    "식신 중첩은 비겁의 힘을 고집이 아니라 결과물로 빼내는 통로가 된다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 양인의 강한 기세가 중심이다. "
                    "식신 중첩은 거친 추진력을 반복 성과로 낮추어 충돌성을 줄인다."
                ),
            }
            pattern_exact_risks = {
                "eating_god_pattern": "재성이 받지 못하면 결과물은 쌓여도 수입으로 굳지 않고, 관성이 약하면 책임 있는 자리로 올라가지 못한다.",
                "hurting_officer_pattern": "식신이 상관을 지나치게 누르면 시장 반응과 돌파성이 약해져 재주는 있어도 확장이 늦다.",
                "direct_wealth_pattern": "식신이 약하면 재성은 있어도 수입의 공급원이 부족하고, 식신이 과하면 수익화보다 제작에 머문다.",
                "indirect_wealth_pattern": "반복 생산에 머물면 큰 거래와 외부 확장의 속도를 따라가지 못한다.",
                "direct_officer_pattern": "식신이 과하면 조직의 형식과 규정을 가볍게 보아 평가가 흔들릴 수 있다.",
                "seven_killings_pattern": "식신이 뿌리 없으면 제살이 되지 못하고, 과하면 긴장감이 풀려 강한 책임을 끝까지 밀지 못한다.",
                "direct_resource_pattern": "인성이 약하면 근거 없이 결과물만 앞서고, 인성이 과하면 식신이 막혀 결과물이 늦다.",
                "indirect_resource_pattern": "특수한 지식이 식신으로 정리되지 못하면 상품화보다 준비와 연구에 머문다.",
                "jianlu_peer_pattern": "식신이 약하면 강한 자기 기반이 결과물로 빠지지 못하고 경쟁과 고집으로 남는다.",
                "yangren_peer_pattern": "식신이 약하면 양인의 기세가 충돌로 남고, 과하면 결단력이 느슨해진다.",
            }
            effect = (
                f"{pattern_label}에서 식신이 중첩되면 식상과다 중에서도 반복 생산, 기술 축적, 안정된 결과물의 힘을 본다. "
                f"{pattern_exact_effects.get(pattern, '꾸준히 만드는 능력은 강하지만 변화와 결단이 늦어질 수 있다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "재성이 받지 못하면 결과물은 쌓여도 돈으로 바뀌는 속도가 늦고, 관성이 약하면 책임 있는 자리로 이어지기 어렵다.")
            timing = "식신 운이 거듭 강해지면 기술, 상품, 서비스, 반복 업무, 안정적 결과물이 사건화된다."
        elif first_ten_god == second_ten_god == "sang_gwan":
            pattern_exact_effects = {
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현, 기획, 개혁성이 격의 중심이다. "
                    "상관이 거듭되면 시장을 흔드는 힘은 커지지만, 재성이나 인성이 받지 않으면 상관견관의 병으로 기운다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 안정 생산성이 중심이다. "
                    "상관 중첩은 안정된 생산을 밖으로 밀어내는 힘이지만, 과하면 꾸준함보다 변동과 반발이 앞선다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "상관 중첩은 상품을 알리고 거래를 열어 재물을 만들 수 있으나, 정산과 신뢰 기준이 약하면 수입이 흔들린다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 외부 거래와 확장이 중심이다. "
                    "상관 중첩은 영업, 홍보, 기획, 설득의 폭을 키워 편재의 시장성을 강하게 만든다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 정관의 질서가 중심이다. "
                    "상관 중첩은 공식 직책과 평판을 직접 건드리므로 상관견관의 병을 가장 먼저 본다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박이 중심이다. "
                    "상관 중첩은 압박을 돌파할 수 있으나, 식신처럼 안정적으로 제어하지 못하면 충돌성이 커진다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 격의 중심이다. "
                    "상관 중첩은 인성이 쌓은 문서와 명분을 밖으로 꺼내지만, 과하면 보호와 자격을 흔든다."
                ),
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 특수한 이해가 중심이다. "
                    "상관 중첩은 비정형 전문성을 대중에게 드러내는 힘이지만, 설명이 거칠면 고립된 비판으로 보인다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 강한 자기 기반이 중심이다. "
                    "상관 중첩은 독립성을 말과 기획으로 드러내지만, 관성이 약하면 조직 질서와 부딪힌다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 양인의 주도권이 중심이다. "
                    "상관 중첩은 승부성과 직설성을 키워 빠르게 밀고 나가지만, 충돌과 평판 부담도 커진다."
                ),
            }
            pattern_exact_risks = {
                "hurting_officer_pattern": "재성이 받아 주지 못하면 상관은 수익화보다 말과 반발로 남고, 인성이 정제하지 못하면 평판이 흔들린다.",
                "eating_god_pattern": "상관이 식신을 앞지르면 결과물의 지속성보다 방향 전환과 문제 제기가 앞선다.",
                "direct_wealth_pattern": "재성이 약하면 표현은 커도 돈으로 남지 않고, 관성이 약하면 계약과 정산의 신뢰가 흔들린다.",
                "indirect_wealth_pattern": "확장 속도가 회수 기준을 앞지르면 큰 거래보다 홍보와 말이 먼저 커진다.",
                "direct_officer_pattern": "인성이나 재성이 중간에서 정리하지 못하면 직책, 평판, 공식 신뢰를 손상한다.",
                "seven_killings_pattern": "편관의 압박과 상관의 반발이 부딪히면 위험 책임과 충돌이 함께 커진다.",
                "direct_resource_pattern": "상관이 과하면 문서, 자격, 보호 기반을 흔들고 인성의 안정성을 깨뜨린다.",
                "indirect_resource_pattern": "특수한 판단이 설명되지 않으면 전문성이 아니라 비판과 고립으로 보인다.",
                "jianlu_peer_pattern": "관성이 약하면 독립적 표현이 규칙을 무시하는 태도로 보인다.",
                "yangren_peer_pattern": "상관과 양인이 함께 과하면 말, 결정, 행동이 빨라져 사고성 충돌이 커진다.",
            }
            effect = (
                f"{pattern_label}에서 상관이 중첩되면 식상과다 중에서도 표현, 기획, 비판, 돌파성이 강해진다. "
                f"{pattern_exact_effects.get(pattern, '변화와 노출은 빠르지만 공식 질서와 충돌할 가능성도 함께 커진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "인성이 정제하지 못하면 말과 태도가 앞서고, 관성이 약하거나 과하면 평판과 직책 문제가 흔들린다.")
            timing = "상관 운이 거듭 강해지면 발표, 기획 전환, 홍보, 문제 제기, 제도권 충돌이 사건화된다."
        else:
            pattern_exact_effects = {
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신이 중심이다. "
                    "상관이 함께 있으면 식신의 결과물이 밖으로 드러나지만, 상관이 앞서면 안정 생산이 흔들린다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현과 개혁성이 격의 중심이다. "
                    "식신이 함께 있으면 상관의 말과 기획에 실제 결과물이 붙어 시장성이 안정된다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "식신과 상관이 함께 재성을 생하면 생산, 홍보, 거래가 연결되어 돈의 입구가 넓어진다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "식신은 책임을 성과로 풀지만 상관은 관을 칠 수 있으므로 어느 쪽이 앞서는지 판정한다."
                ),
            }
            pattern_exact_risks = {
                "eating_god_pattern": "상관이 식신보다 강하면 결과물보다 말과 방향 전환이 앞선다.",
                "hurting_officer_pattern": "식신이 약하면 상관의 표현은 있어도 반복 가능한 결과물이 부족하다.",
                "direct_wealth_pattern": "재성이 약하면 생산과 홍보가 있어도 회수와 정산이 늦어진다.",
                "direct_officer_pattern": "상관이 강하면 식신의 성과보다 공식 질서와의 충돌이 먼저 드러난다.",
            }
            effect = (
                f"{pattern_label}에서 식신과 상관이 함께 있으면 안정 생산과 돌파 표현을 함께 본다. "
                f"{pattern_exact_effects.get(pattern, '식신은 꾸준히 만들고 상관은 밖으로 밀어내므로, 결과물의 품질과 시장 노출이 동시에 커진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "식신이 약하면 지속성이 부족하고, 상관이 과하면 말과 확장이 앞서 책임과 평판을 흔든다.")
            timing = "식신 운은 결과물과 반복 생산으로, 상관 운은 표현과 확장으로 드러난다."
    elif category == "resource_same_group":
        key = "resource_overload_exact"
        if first_ten_god == second_ten_god == "jeong_in":
            pattern_exact_effects = {
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 정인의 문서, 자격, 보호 기반이 격의 중심이다. "
                    "정인이 거듭되면 제도권 근거와 안정성은 강하지만, 재성이나 식상이 열지 않으면 인성 과다로 닫힌다."
                ),
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 편인의 특수 몰입이 중심이다. "
                    "정인 중첩은 비정형 전문성을 제도권 문서와 자격 안으로 정리하는 힘이 된다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 격의 중심이다. "
                    "정인 중첩은 재물이 상대해야 할 명분과 문서를 두껍게 만들며, 좋으면 계약 근거가 되고 과하면 재물 실행을 늦춘다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "정인 중첩은 관인상생의 문서 기반을 두껍게 하지만, 과하면 책임 실행보다 승인 절차가 앞선다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박을 받아내야 한다. "
                    "정인 중첩은 살인상생의 보호 장치가 되지만, 과하면 위험을 처리하기보다 명분으로 피하려 한다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 결과물이 중심이다. "
                    "정인 중첩은 품질과 기준을 세우지만 과하면 식신의 생산 속도를 누른다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현이 중심이다. "
                    "정인 중첩은 상관을 문서와 품격으로 정제하지만, 과하면 표현의 속도와 시장성이 약해진다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 비겁의 자기 기반이 중심이다. "
                    "정인 중첩은 독립성에 명분과 보호를 붙여 인비과중으로 기울 수 있다."
                ),
            }
            pattern_exact_risks = {
                "direct_resource_pattern": "재성이나 식상이 길을 열지 못하면 문서, 학력, 자격, 보호 기반이 실행을 대신한다.",
                "indirect_resource_pattern": "정인이 과하면 편인의 특수성이 제도권 형식에 갇혀 독창성이 약해진다.",
                "direct_wealth_pattern": "재성이 정인을 제어하지 못하면 명분과 검토가 돈의 실행과 회수를 늦춘다.",
                "direct_officer_pattern": "관성이 약하면 문서는 많아도 직책의 실제 책임으로 이어지지 못한다.",
                "seven_killings_pattern": "정인이 살을 받아내지 못하고 과하면 압박을 처리하기보다 회피와 명분으로 흐른다.",
                "eating_god_pattern": "정인이 과하면 도식으로 기울어 결과물이 늦고 수입화가 밀린다.",
                "hurting_officer_pattern": "정제가 지나치면 상관의 시장 반응과 돌파성이 약해진다.",
                "jianlu_peer_pattern": "인비가 과하면 독립성에 명분이 붙어 고집과 실행 지연이 커진다.",
            }
            effect = (
                f"{pattern_label}에서 정인이 중첩되면 인성 과다 중에서도 정식 문서, 학력, 자격, 보호 기반이 두꺼워진다. "
                f"{pattern_exact_effects.get(pattern, '안정성과 명분은 강하지만 실행 속도는 느려질 수 있다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "재성이 길을 열지 못하면 현실 수입으로 연결되지 않고, 식상이 약하면 공부와 문서가 결과물을 대신한다.")
            timing = "정인 운이 거듭 강해지면 학업, 자격, 문서, 보호자, 기관 지원 문제가 사건화된다."
        elif first_ten_god == second_ten_god == "pyeon_in":
            pattern_exact_effects = {
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 편인의 특수한 몰입과 비정형 판단이 격의 중심이다. "
                    "편인이 거듭되면 심층 연구와 독자적 해석은 강하지만, 재성이나 식상이 없으면 고립된 전문성으로 남는다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 정인의 제도권 근거가 중심이다. "
                    "편인 중첩은 정식 문서 바깥의 특수 판단을 키워 자격 체계를 흔들거나 보완한다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "편인 중첩은 돈의 실행 앞에 특수 정보와 의심을 늘리므로, 좋으면 리스크 검토이고 과하면 재물 지연이다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 외부 거래가 중심이다. "
                    "편인 중첩은 시장의 숨은 정보와 특수 기회를 읽게 하지만, 과하면 판단이 고립되어 회수가 늦다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 생산성이 중심이다. "
                    "편인 중첩은 편인도식으로 식신을 막기 쉬워, 특수한 생각이 결과물을 늦춘다."
                ),
                "hurting_officer_pattern": (
                    f"{pattern_label}에서는 상관의 표현이 중심이다. "
                    "편인 중첩은 표현에 독특한 관점을 주지만, 설명되지 않으면 비판과 고립으로 보인다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박이 중심이다. "
                    "편인 중첩은 살을 받아내는 비정형 보호가 되지만, 과하면 불안과 과잉 대비가 커진다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 자기 기반이 중심이다. "
                    "편인 중첩은 독립성에 특수한 판단을 붙여 고집과 비공식성을 강하게 만든다."
                ),
            }
            pattern_exact_risks = {
                "indirect_resource_pattern": "재성이나 식상이 없으면 특수 판단이 상품, 수입, 결과물로 나오지 못하고 고립된다.",
                "direct_resource_pattern": "정식 문서와 특수 판단이 충돌하면 제도권 신뢰와 설명 가능성이 약해진다.",
                "direct_wealth_pattern": "편인이 과하면 돈보다 의심, 검토, 숨은 정보가 앞서 실행이 늦어진다.",
                "indirect_wealth_pattern": "거래보다 비정형 판단이 앞서면 기회 포착은 빨라도 계약과 회수가 늦다.",
                "eating_god_pattern": "편인도식이 강하면 식신의 반복 생산과 안정 수입이 막힌다.",
                "hurting_officer_pattern": "편인이 상관을 정제하지 못하면 독특함보다 날 선 비판과 고립이 먼저 보인다.",
                "seven_killings_pattern": "편인이 살을 받아내지 못하면 압박을 전문성으로 바꾸지 못하고 불안정한 판단으로 남는다.",
                "jianlu_peer_pattern": "편인과 비겁이 과하면 독립성은 강하지만 협업과 현실 실행이 늦어진다.",
            }
            effect = (
                f"{pattern_label}에서 편인이 중첩되면 인성 과다 중에서도 특수 몰입, 비정형 정보, 고립된 판단이 강해진다. "
                f"{pattern_exact_effects.get(pattern, '전문성은 깊어질 수 있으나 보편적 설명과 실행 전환은 늦어질 수 있다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "재성이나 식상이 받치지 못하면 특수한 생각이 수입과 결과물로 바뀌지 못하고 고립된다.")
            timing = "편인 운이 거듭 강해지면 특수 공부, 비공식 자료, 심층 연구, 고립된 준비가 사건화된다."
        else:
            pattern_exact_effects = {
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 정인이 중심이다. "
                    "편인이 함께 있으면 정식 문서에 특수 전문성이 붙지만, 편인이 과하면 제도권 안정성이 흔들린다."
                ),
                "indirect_resource_pattern": (
                    f"{pattern_label}에서는 편인이 중심이다. "
                    "정인이 함께 있으면 비정형 전문성에 공식 자격과 문서 근거가 붙는다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "정편인이 함께 많으면 돈 앞에 문서, 명분, 특수 정보가 함께 개입해 실행 속도를 늦출 수 있다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "정편인이 함께 관을 받치면 직책의 근거는 두꺼워지지만 승인 절차와 판단 층위가 복잡해진다."
                ),
            }
            pattern_exact_risks = {
                "direct_resource_pattern": "편인이 과하면 정인의 안정성을 비정형 판단이 흔든다.",
                "indirect_resource_pattern": "정인이 과하면 편인의 특수성이 공식 형식에 갇힌다.",
                "direct_wealth_pattern": "재성이 약하면 인성 혼잡이 실행보다 검토와 명분을 키운다.",
                "direct_officer_pattern": "인성이 과하면 직책의 실행보다 문서, 승인, 절차가 앞선다.",
            }
            effect = (
                f"{pattern_label}에서 정인과 편인이 함께 있으면 공식 문서와 특수 몰입을 함께 본다. "
                f"{pattern_exact_effects.get(pattern, '정인은 제도권 근거를 만들고 편인은 비정형 전문성을 만들기 때문에, 안정성과 독특함이 동시에 생긴다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "정인이 과하면 절차가 늘고, 편인이 과하면 판단이 고립되어 실행과 수입화가 늦어진다.")
            timing = "정인 운은 자격과 문서로, 편인 운은 특수 공부와 숨은 정보로 드러난다."
    elif category == "peer_same_group":
        key = "peer_overload_exact"
        if first_ten_god == second_ten_god == "bi_gyeon":
            pattern_exact_effects = {
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 비견의 자립성과 자기 기준이 격의 중심이다. "
                    "비견이 거듭되면 독립성, 체력, 동등한 권리 의식이 강해지고 관성이 정리하면 사회적 책임으로 굳어진다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 양인의 강한 주도권이 중심이다. "
                    "비견 중첩은 겁재보다 덜 거칠지만 자기 기준을 두껍게 만들어 타협 속도를 늦춘다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "비견 중첩은 재물 앞에서 내 몫, 가족 몫, 공동 기준을 세우게 하며 관성이 약하면 분재로 기운다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 외부 거래와 확장이 중심이다. "
                    "비견 중첩은 동업자나 동등한 파트너를 끌어오지만, 권한과 지분 기준이 없으면 회수가 흐려진다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "비견 중첩은 직책 안에서 자기 기준을 세우는 힘이지만, 관성이 약하면 조직 질서보다 자기 입장이 앞선다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 압박이 중심이다. "
                    "비견 중첩은 강한 책임을 버틸 체력이 되지만, 제어되지 않으면 압박 앞에서 고집으로 맞선다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 생산성이 중심이다. "
                    "비견 중첩은 함께 만들 사람과 자기 체력을 늘리지만, 식상이 약하면 결과보다 몫이 앞선다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 중심이다. "
                    "비견 중첩은 문서와 보호에서 생긴 자기 기반을 두껍게 만들어 인비과중으로 기울 수 있다."
                ),
            }
            pattern_exact_risks = {
                "jianlu_peer_pattern": "관성이 약하면 독립성은 강하지만 공동 기준, 조직 질서, 재물 분배에서 고집이 커진다.",
                "yangren_peer_pattern": "비견이 겁재성을 자극하면 타협보다 자기 기준과 주도권이 앞선다.",
                "direct_wealth_pattern": "재성이 약하거나 관성이 정리하지 못하면 돈보다 자기 입장과 공동 명의 문제가 커진다.",
                "indirect_wealth_pattern": "파트너는 생겨도 계약과 지분 기준이 약하면 회수와 정산이 흐려진다.",
                "direct_officer_pattern": "관성이 약하면 공식 책임보다 자기 기준이 앞서 직책과 평판이 흔들린다.",
                "seven_killings_pattern": "편관을 받아낼 식신이나 인성이 약하면 고집으로 버티다 압박이 커진다.",
                "eating_god_pattern": "식상이 약하면 함께 움직이는 사람은 있어도 실제 결과물이 부족하다.",
                "direct_resource_pattern": "재성이나 식상이 길을 열지 못하면 인비과중으로 실행이 늦어진다.",
            }
            effect = (
                f"{pattern_label}에서 비견이 중첩되면 비겁 과중 중에서도 자기 기준, 독립성, 동등한 권리 의식이 강하다. "
                f"{pattern_exact_effects.get(pattern, '자립성은 분명하지만 공동의 기준을 맞추는 데 시간이 걸릴 수 있다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "관성이 정리하지 못하면 고집과 분재가 커지고, 재성이 약하면 돈보다 자기 입장이 앞선다.")
            timing = "비견 운이 거듭 강해지면 독립, 동등한 몫, 공동 명의, 자기 기준 문제가 사건화된다."
        elif first_ten_god == second_ten_god == "geob_jae":
            pattern_exact_effects = {
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 겁재의 강한 주도권과 승부성이 격의 중심이다. "
                    "겁재가 거듭되면 돌파력은 크지만 관살이나 식상이 제어하지 못하면 쟁재와 충돌이 병이 된다."
                ),
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 비견의 자립성이 중심이다. "
                    "겁재 중첩은 독립성을 경쟁과 지분 다툼으로 밀어 올리므로 관성의 규칙이 필요하다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "겁재 중첩은 재물을 직접 건드리는 힘이 강해 가까운 사람, 동업, 공동 자금에서 쟁재가 일어나기 쉽다."
                ),
                "indirect_wealth_pattern": (
                    f"{pattern_label}에서는 편재의 확장이 중심이다. "
                    "겁재 중첩은 사업 확장에 사람과 자금을 끌어오지만, 지분과 회수 기준이 약하면 손실 폭이 커진다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "겁재 중첩은 관성이 제어해야 할 경쟁성과 주도권이 커진 상태로, 규칙이 있으면 조직 장악력이 된다."
                ),
                "seven_killings_pattern": (
                    f"{pattern_label}에서는 편관의 강한 압박이 중심이다. "
                    "겁재 중첩은 압박에 맞서는 힘이지만, 살과 겁재가 거칠게 부딪히면 사고성 책임이 커진다."
                ),
                "eating_god_pattern": (
                    f"{pattern_label}에서는 식신의 생산성이 중심이다. "
                    "겁재 중첩은 함께 만들 추진력을 주지만, 식상이 약하면 결과보다 몫 다툼이 앞선다."
                ),
                "direct_resource_pattern": (
                    f"{pattern_label}에서는 인성이 중심이다. "
                    "겁재 중첩은 문서와 보호에서 생긴 힘이 경쟁성으로 번지는 모습이며, 과하면 인비과중과 분쟁이 함께 온다."
                ),
            }
            pattern_exact_risks = {
                "yangren_peer_pattern": "관살이나 식상이 제어하지 못하면 겁재쟁재, 동업 갈등, 손실, 무리한 결정으로 번진다.",
                "jianlu_peer_pattern": "정관의 규칙이 약하면 독립성이 주도권 경쟁과 지분 다툼으로 변한다.",
                "direct_wealth_pattern": "재성이 약하거나 관성이 정리하지 못하면 돈, 가족, 동업자, 가까운 사람 사이에서 손실과 분쟁이 커진다.",
                "indirect_wealth_pattern": "외부 자금과 투자금이 지분 분쟁, 회수 지연, 사업상 손실로 번질 수 있다.",
                "direct_officer_pattern": "관성이 약하면 겁재를 제어하지 못해 직책 안에서도 경쟁과 권한 충돌이 커진다.",
                "seven_killings_pattern": "편관과 겁재가 동시에 과하면 강한 압박, 충돌, 사고성 책임이 함께 커진다.",
                "eating_god_pattern": "식신이 약하면 함께 만드는 힘이 결과물보다 몫과 주도권 다툼으로 흐른다.",
                "direct_resource_pattern": "인성이 과하면 명분 있는 경쟁이 되고, 재성이 약하면 현실 수익보다 분쟁이 앞선다.",
            }
            effect = (
                f"{pattern_label}에서 겁재가 중첩되면 비겁 과중 중에서도 경쟁, 주도권, 지분 다툼이 강하다. "
                f"{pattern_exact_effects.get(pattern, '추진력은 거칠게 살아나지만 사람과 돈이 얽힐 때 손실 가능성도 커진다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "관성이 제어하지 못하면 동업 갈등, 몫 다툼, 공동 자금 손실, 가까운 사람과의 충돌이 커진다.")
            timing = "겁재 운이 거듭 강해지면 경쟁자, 동업, 지분, 공동 비용, 주도권 충돌이 사건화된다."
        else:
            pattern_exact_effects = {
                "jianlu_peer_pattern": (
                    f"{pattern_label}에서는 비견의 자립성이 중심이다. "
                    "겁재가 함께 있으면 자기 기준이 실제 경쟁과 주도권 문제로 번지므로 관성의 정리가 필요하다."
                ),
                "yangren_peer_pattern": (
                    f"{pattern_label}에서는 겁재성 주도권이 중심이다. "
                    "비견이 함께 있으면 단순 분탈보다 명분 있는 자기 기준이 붙어 더 오래 간다."
                ),
                "direct_wealth_pattern": (
                    f"{pattern_label}에서는 재성이 중심이다. "
                    "비견과 겁재가 함께 재성을 압박하면 공동 기준과 분탈성이 동시에 들어와 재물 안정성을 흔든다."
                ),
                "direct_officer_pattern": (
                    f"{pattern_label}에서는 관성이 중심이다. "
                    "비겁 혼재는 관성이 정리해야 할 자기 주장과 경쟁성이 함께 커진 상태다."
                ),
            }
            pattern_exact_risks = {
                "jianlu_peer_pattern": "관성이 약하면 자기 기준과 경쟁성이 함께 커져 협업과 재물 분배가 어렵다.",
                "yangren_peer_pattern": "식상이나 관살이 빼내지 못하면 명분 있는 경쟁과 주도권 다툼이 길어진다.",
                "direct_wealth_pattern": "비견은 공동 기준을, 겁재는 분탈성을 만들기 때문에 재성의 소유 기준이 흔들린다.",
                "direct_officer_pattern": "관성이 약하면 직책 안에서도 자기 주장과 경쟁이 함께 올라와 평가가 흔들린다.",
            }
            effect = (
                f"{pattern_label}에서 비견과 겁재가 함께 있으면 자기 기준과 경쟁성이 동시에 강해진다. "
                f"{pattern_exact_effects.get(pattern, '비견은 동등한 권리로, 겁재는 실제 주도권과 몫 다툼으로 나타난다.')}"
            )
            risk = pattern_exact_risks.get(pattern, "관성이나 식상이 빼내지 못하면 고집, 경쟁, 동업 갈등, 몫 다툼이 커진다.")
            timing = "비견 운은 독립과 동등한 권리로, 겁재 운은 경쟁자와 지분 문제로 드러난다."

    return {
        "key": key,
        "effect": effect,
        "risk": risk,
        "timing": timing,
    }


def _dual_classical_action_tags(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    category: str,
    name: str,
    bridge_key: str = "",
) -> list[str]:
    tags: list[str] = []
    pair = {first_ten_god, second_ten_god}
    pattern_center_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]

    def add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    category_tags = {
        "peer_generates_output": "bigeop_generates_siksang",
        "output_generates_wealth": "siksang_saengjae",
        "wealth_generates_officer": "jaeseong_generates_gwanseong",
        "officer_generates_resource": "gwanseong_generates_inseong",
        "resource_generates_peer": "inseong_generates_bigeop",
        "peer_controls_wealth": "bigeop_controls_wealth",
        "wealth_controls_resource": "wealth_controls_resource",
        "resource_controls_output": "inseong_controls_output",
        "output_controls_officer": "siksang_controls_gwanseong",
        "officer_controls_peer": "gwanseong_controls_bigeop",
        "peer_same_group": "bigeop_same_group",
        "output_same_group": "siksang_same_group",
        "wealth_same_group": "wealth_same_group",
        "officer_same_group": "gwanseong_same_group",
        "resource_same_group": "inseong_same_group",
    }
    if category in category_tags:
        add(category_tags[category])

    if category == "output_generates_wealth":
        add("siksang_saengjae")
    if category == "wealth_generates_officer":
        if "pyeon_gwan" in pair:
            add("jaesaengsal")
        else:
            add("jaesaenggwan")
    if category == "officer_generates_resource":
        if "pyeon_gwan" in pair:
            add("salin_sangsaeng")
        else:
            add("gwanin_sangsaeng")
    if name == "식신제살" or pair == {"sik_sin", "pyeon_gwan"}:
        add("siksin_jesal")
    if name == "상관견관" or pair == {"sang_gwan", "jeong_gwan"}:
        add("sanggwan_gyeongwan")
    if category == "wealth_controls_resource":
        add("jaegeukin")
    if category == "peer_controls_wealth":
        add("bigeop_jaengjae")
    if category == "resource_controls_output" or name in {"편인도식", "정인제식"}:
        add("inseong_dosik")
    if category == "officer_same_group":
        add("gwansal_overload")
        if {"jeong_gwan", "pyeon_gwan"}.issubset(pair):
            add("gwansal_honhap")
    if category in {"resource_same_group", "peer_same_group", "resource_generates_peer"}:
        add("inbi_overload")
    if category == "output_same_group":
        add("siksang_overload")
    if category == "wealth_same_group":
        add("jaeda_sinyak_risk")
    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"} and category == "wealth_same_group":
        add("jaeda_sinyak_risk")
    if pattern == "seven_killings_pattern" and category == "officer_same_group":
        add("gwansal_overload")

    bridge_component_tags = {
        "resource_generates_peer_generates_output": (
            "inseong_generates_bigeop",
            "bigeop_generates_siksang",
        ),
        "peer_generates_output_generates_wealth": (
            "bigeop_generates_siksang",
            "siksang_saengjae",
        ),
        "output_generates_wealth_generates_officer": (
            "siksang_saengjae",
            "jaesaenggwan",
            "gwanseong_controls_bigeop",
        ),
        "wealth_generates_officer_generates_resource": (
            "jaesaenggwan",
            "gwanin_sangsaeng",
        ),
        "officer_generates_resource_generates_peer": (
            "gwanin_sangsaeng",
            "inseong_generates_bigeop",
        ),
        "officer_controls_peer_controls_wealth": (
            "gwanseong_controls_bigeop",
            "bigeop_controls_wealth",
        ),
        "peer_controls_wealth_controls_resource": (
            "bigeop_controls_wealth",
            "wealth_controls_resource",
            "bigeop_jaengjae",
            "jaegeukin",
        ),
        "wealth_controls_resource_controls_output": (
            "wealth_controls_resource",
            "inseong_controls_output",
            "jaegeukin",
            "inseong_dosik",
        ),
        "resource_controls_output_controls_officer": (
            "inseong_controls_output",
            "siksang_controls_gwanseong",
            "inseong_dosik",
        ),
        "output_controls_officer_controls_peer": (
            "siksang_controls_gwanseong",
            "gwanseong_controls_bigeop",
        ),
    }
    for tag in bridge_component_tags.get(bridge_key, ()):
        if tag == "jaesaenggwan" and "pyeon_gwan" in {first_ten_god, second_ten_god, pattern_center_ten_god}:
            add("jaesaengsal")
            continue
        if tag == "gwanin_sangsaeng" and "pyeon_gwan" in {first_ten_god, second_ten_god, pattern_center_ten_god}:
            add("salin_sangsaeng")
            continue
        add(tag)

    if not tags:
        add("gyeokguk_dual_specific_adjustment")
    return tags


def _exact_pair_profile(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    first_to_second_relation: str,
    chain_grade: str,
) -> dict[str, str]:
    first = TEN_GOD_OPERATION_FACE[first_ten_god]
    second = TEN_GOD_OPERATION_FACE[second_ten_god]
    name = _exact_pair_name(first_ten_god, second_ten_god, first_to_second_relation)
    center = PATTERN_LENS[pattern]["center"]
    category = _pair_category(first_ten_god, second_ten_god, first_to_second_relation)
    exact_refinement = _exact_pair_refinement(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        category=category,
        name=name,
    )
    if first_to_second_relation == "first_generates_second":
        effect = (
            f"{first['action']}에서 {second['result']} 방향으로 이어진다. "
            f"{PATTERN_LENS[pattern]['label']}에서는 {center} 중심이 현실 결과로 넓어진다."
        )
        risk = f"{first['risk']} 문제가 커지면 {second['risk']}까지 함께 커져 성취가 부담으로 바뀐다."
    elif first_to_second_relation == "second_generates_first":
        effect = (
            f"{second['action']}에서 {_object_form(first['result'])} 받쳐 준다. "
            f"뒤의 십신이 앞의 십신에 근거를 공급하는 조합이다."
        )
        risk = f"{second['risk']} 문제가 강하면 {first['risk']}이 정리되지 않고 누적된다."
    elif first_to_second_relation == "first_controls_second":
        effect = (
            f"첫 작용은 {first['action']} 작용이고, 두 번째 작용인 {_object_form(second['action'])} 제어한다. "
            f"격국에서 필요한 제어라면 병을 약으로 바꾸고, 불필요하면 중심을 손상시킨다."
        )
        risk = f"제어가 지나치면 {second['result']} 쪽이 끊기고, 약하면 {second['risk']} 문제가 남는다."
    elif first_to_second_relation == "second_controls_first":
        effect = (
            f"두 번째 작용은 {second['action']} 작용이고, 앞선 작용인 {_object_form(first['action'])} 제어한다. "
            f"앞의 작용이 과할 때는 조절이 되고, 약할 때는 실행을 누른다."
        )
        risk = f"{second['risk']} 문제가 강하면 {first['result']} 쪽이 현실화되기 전에 막힌다."
    elif first_to_second_relation == "same_group":
        if first_ten_god == second_ten_god:
            effect = f"{first['action']} 작용이 같은 계열 안에서 거듭 나타난다. 장점은 선명해지고 편중도 강해진다."
            risk = f"과하면 {first['risk']} 문제가 반복해서 나타난다."
        else:
            effect = f"{first['action']} 작용과 {second['action']} 작용이 같은 계열에서 겹친다. 장점은 선명해지고 편중도 강해진다."
            risk = f"과하면 {first['risk']}, {_subject_form(second['risk'])} 함께 나타난다."
    else:
        effect = f"{first['action']}과 {second['action']}이 간접적으로 격국의 현실 방향을 바꾼다."
        risk = f"강약과 위치가 맞지 않으면 {first['risk']}과 {second['risk']}이 따로 논다."
    pattern_lens = PATTERN_PAIR_CATEGORY_LENS.get(category, {}).get(pattern)
    lens_type = "specific"
    if not pattern_lens:
        pattern_lens = _derived_pattern_pair_lens(pattern, category)
        lens_type = "derived_specific"
    if pattern_lens:
        effect = _join_unique_sentences(effect, pattern_lens["effect"])
        risk = _join_unique_sentences(risk, pattern_lens["risk"])
    effect = _join_unique_sentences(effect, exact_refinement["effect"])
    risk = _join_unique_sentences(risk, exact_refinement["risk"])
    if chain_grade in {"medicine_chain", "constructive_chain", "supportive_chain"}:
        effect = f"{name}: {effect}"
    else:
        effect = f"{name}: {effect}"
    timing = (
        f"운에서 {TEN_GOD_LABEL[first_ten_god]} 작용이 먼저 오면 {_subject_form(first['timing'])} 먼저 사건화되고, "
        f"{TEN_GOD_LABEL[second_ten_god]} 작용이 뒤따르면 {_euro_form(second['timing'])} 결론이 바뀐다."
    )
    timing = f"{timing} {exact_refinement['timing']}"
    return {
        "key": f"{first_ten_god}->{second_ten_god}",
        "category": category,
        "name": name,
        "effect": effect,
        "risk": risk,
        "timing": timing,
        "refinement_key": exact_refinement["key"],
        "lens_key": f"{lens_type}:{category}:{pattern}",
        "lens_type": lens_type,
    }


def _sequence_key(
    *,
    first_relation_to_pattern: str,
    second_relation_to_pattern: str,
    first_to_second_relation: str,
    first_grade: str,
    second_grade: str,
) -> str:
    if first_to_second_relation == "same_group":
        return "same_role_amplification"
    if first_to_second_relation == "first_generates_second":
        if second_grade in SUPPORTIVE_GRADES:
            return "first_action_flows_into_support"
        if second_grade in BURDEN_GRADES:
            return "first_action_feeds_pressure"
        return "first_action_flows_into_mixed_role"
    if first_to_second_relation == "second_generates_first":
        if first_grade in SUPPORTIVE_GRADES:
            return "second_action_sources_first_success"
        if first_grade in BURDEN_GRADES:
            return "second_action_sources_existing_burden"
        return "second_action_sources_mixed_first_role"
    if first_to_second_relation == "first_controls_second":
        if second_relation_to_pattern in {"actor_controls_pattern", "same_group"}:
            if first_grade in BURDEN_GRADES:
                return "first_action_damages_pattern_center"
            if first_grade in {"breaker_or_medicine", "regulator_or_breaker"}:
                return "first_action_conditionally_controls_pattern_center"
            return "first_action_restrains_pattern_pressure"
        return "first_action_restrains_secondary_role"
    if first_to_second_relation == "second_controls_first":
        if first_relation_to_pattern == "actor_controls_pattern":
            if first_grade in BURDEN_GRADES:
                return "second_action_controls_pattern_breaker"
            if first_grade in SUPPORTIVE_GRADES and second_grade in SUPPORTIVE_GRADES:
                return "second_action_restricts_existing_medicine"
            return "second_action_restricts_first_role"
        if first_grade in SUPPORTIVE_GRADES and second_grade in BURDEN_GRADES:
            return "second_action_damages_existing_support"
        return "second_action_restricts_first_role"
    return "indirect_dual_action"


def _chain_grade(sequence_key: str, first_grade: str, second_grade: str) -> str:
    if sequence_key in {"first_action_flows_into_support", "second_action_sources_first_success"}:
        return "constructive_chain"
    if sequence_key in {"first_action_restrains_pattern_pressure", "second_action_controls_pattern_breaker"}:
        return "medicine_chain"
    if sequence_key in {"first_action_feeds_pressure", "second_action_damages_existing_support"}:
        return "risk_chain"
    if sequence_key == "first_action_damages_pattern_center":
        return "risk_chain"
    if sequence_key == "first_action_conditionally_controls_pattern_center":
        return "conditional_chain"
    if sequence_key in {
        "first_action_restrains_secondary_role",
        "second_action_restricts_first_role",
        "second_action_restricts_existing_medicine",
    }:
        if first_grade in SUPPORTIVE_GRADES and second_grade in SUPPORTIVE_GRADES:
            return "mediated_tension_chain"
    if first_grade in BURDEN_GRADES and second_grade in BURDEN_GRADES:
        return "compounded_burden_chain"
    if first_grade in SUPPORTIVE_GRADES and second_grade in SUPPORTIVE_GRADES:
        return "supportive_chain"
    if first_grade in MIXED_GRADES or second_grade in MIXED_GRADES:
        return "conditional_chain"
    return "mixed_chain"


def _bridge_adjusted_chain_grade(
    chain_grade: str,
    pattern_center_bridge: dict[str, object],
    first_grade: str,
    second_grade: str,
) -> str:
    direction = pattern_center_bridge.get("direction", "")
    if direction in {"first_to_second_via_pattern_center", "second_to_first_via_pattern_center"}:
        if first_grade in BURDEN_GRADES or second_grade in BURDEN_GRADES:
            return "conditional_chain"
        if first_grade in MIXED_GRADES or second_grade in MIXED_GRADES:
            return "conditional_chain"
        return "constructive_chain"
    if direction in {"first_controls_second_via_pattern_center", "second_controls_first_via_pattern_center"}:
        if first_grade in BURDEN_GRADES or second_grade in BURDEN_GRADES:
            return "conditional_chain"
        return "medicine_chain"
    return chain_grade


def _exact_pair_adjusted_chain_grade(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    first_to_second_relation: str,
    chain_grade: str,
) -> str:
    pair = {first_ten_god, second_ten_god}
    has_wealth = bool(pair.intersection({"pyeon_jae", "jeong_jae"}))
    has_output = bool(pair.intersection({"sik_sin", "sang_gwan"}))
    has_killing = "pyeon_gwan" in pair
    is_generation_path = first_to_second_relation in {"first_generates_second", "second_generates_first"}
    if (
        has_output
        and has_killing
        and pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"}
        and chain_grade in {"constructive_chain", "supportive_chain"}
    ):
        return "conditional_chain"
    if not (has_wealth and has_killing and is_generation_path):
        return chain_grade
    if pattern in {"seven_killings_pattern", "direct_officer_pattern", "yangren_peer_pattern"}:
        return "risk_chain"
    if chain_grade not in {"constructive_chain", "supportive_chain"}:
        return chain_grade
    if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern", "eating_god_pattern", "hurting_officer_pattern"}:
        return "conditional_chain"
    return "risk_chain"


def _bridge_adjusted_chain_nature(chain_nature: str, pattern_center_bridge: dict[str, object]) -> str:
    direction = pattern_center_bridge.get("direction", "")
    if direction in {"first_to_second_via_pattern_center", "second_to_first_via_pattern_center"}:
        return "두 십신의 직접 생극보다 격국 중심을 거친 상생 연쇄를 우선한다."
    if direction in {"first_controls_second_via_pattern_center", "second_controls_first_via_pattern_center"}:
        return "두 십신의 직접 극보다 격국 중심을 거친 단계적 제어를 우선한다."
    return chain_nature


def _bridge_adjusted_pair_profile(
    exact_pair: dict[str, str],
    pattern_center_bridge: dict[str, object],
) -> dict[str, str]:
    if not pattern_center_bridge:
        return exact_pair
    adjusted = dict(exact_pair)
    adjusted["direct_name"] = exact_pair["name"]
    adjusted["direct_category"] = exact_pair["category"]
    if pattern_center_bridge.get("mediated_name"):
        adjusted["name"] = str(pattern_center_bridge["mediated_name"])
    adjusted["effect"] = (
        f"{pattern_center_bridge['effect']} "
        f"직접 생극으로 보면 {exact_pair['effect']}"
    )
    adjusted["risk"] = f"{pattern_center_bridge['risk']} {exact_pair['risk']}"
    adjusted["timing"] = f"{pattern_center_bridge['timing']} {exact_pair['timing']}"
    return adjusted


def _bridge_adjusted_resolution_logic(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    combination_resolution_logic: str,
    pattern_center_bridge: dict[str, object],
) -> str:
    if not pattern_center_bridge:
        return combination_resolution_logic
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    direction = pattern_center_bridge.get("direction", "")
    if direction in {"first_to_second_via_pattern_center", "second_to_first_via_pattern_center"}:
        return (
            f"{pattern_label}에서 {_and_form(first_label)} {_subject_form(second_label)} 직접 충돌하거나 따로 움직이는 조합으로 보지 않는다. "
            f"{_subject_form(pattern_center)} 중간에 서면 두 십신은 격국 중심을 거친 상생 연쇄로 판정된다. "
            f"{pattern_center_bridge['effect']} {combination_resolution_logic}"
        )
    if direction in {"first_controls_second_via_pattern_center", "second_controls_first_via_pattern_center"}:
        return (
            f"{pattern_label}에서 {_and_form(first_label)} {_subject_form(second_label)} 직접 손상으로만 보지 않는다. "
            f"{_subject_form(pattern_center)} 중간에서 힘의 방향을 잡으면 두 십신은 단계적 제어로 판정된다. "
            f"{pattern_center_bridge['effect']} {combination_resolution_logic}"
        )
    return combination_resolution_logic


def _chain_nature(sequence_key: str, chain_grade: str) -> str:
    if chain_grade == "constructive_chain":
        return "앞선 작용이 다음 십신으로 이어져 격국의 성립 조건을 넓힌다."
    if chain_grade == "medicine_chain":
        return "부담이 되는 작용을 다른 십신이 제어하여 병약의 약으로 쓰인다."
    if chain_grade == "risk_chain":
        return "앞선 작용이 부담 십신으로 흘러 격국의 약점을 키운다."
    if chain_grade == "compounded_burden_chain":
        return "두 십신이 함께 부담으로 작용하여 파격 가능성을 높인다."
    if chain_grade == "supportive_chain":
        return "두 십신이 함께 격국의 성립을 돕는 보조 조건이 된다."
    if chain_grade == "mediated_tension_chain":
        return "두 십신이 각각 격국에는 필요하지만 서로 직접 극하므로, 격국 중심이나 중간 작용이 매개되어야 성립한다."
    if chain_grade == "conditional_chain":
        return "좋고 나쁨이 고정되지 않고 강약, 위치, 투출 여부에 따라 갈린다."
    if sequence_key == "same_role_amplification":
        return "같은 계열의 작용이 반복되어 장점과 편중이 함께 커진다."
    return "두 십신이 간접적으로 격국의 방향을 바꾼다."


def _pattern_effect(pattern: str, first_ten_god: str, second_ten_god: str, chain_grade: str) -> str:
    label = PATTERN_LENS[pattern]["label"]
    center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    first_text = TEN_GOD_EXACT_NUANCE[first_ten_god]
    second_text = TEN_GOD_EXACT_NUANCE[second_ten_god]
    relation = _relation_between(TEN_GOD_GROUPS[first_ten_god], TEN_GOD_GROUPS[second_ten_god])
    if relation == "first_generates_second":
        relation_text = f"{_subject_form(first_label)} {_object_form(second_label)} 생하여 힘을 넘긴다"
    elif relation == "second_generates_first":
        relation_text = f"{_subject_form(second_label)} {_object_form(first_label)} 생하여 앞 작용의 근거가 된다"
    elif relation == "first_controls_second":
        relation_text = f"{_subject_form(first_label)} {_object_form(second_label)} 제어한다"
    elif relation == "second_controls_first":
        relation_text = f"{_subject_form(second_label)} {_object_form(first_label)} 제어한다"
    elif relation == "same_group":
        relation_text = f"{_and_form(first_label)} {_subject_form(second_label)} 같은 계열에서 중첩된다"
    else:
        relation_text = f"{_and_form(first_label)} {_subject_form(second_label)} 직접 생극이 아닌 간접 관계로 얽힌다"

    opening = (
        f"{label}에서는 {_object_form(center)} 기준으로 {_topic_form(first_label)} {first_text}, "
        f"{_topic_form(second_label)} {second_text}의 작용을 구분한다. {relation_text}."
    )
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        return (
            f"{opening} 월령과 격국이 이 방향을 필요로 하면 두 십신은 성격을 보강한다. "
            "운에서 먼저 드러나는 십신이 사건의 입구가 되고, 뒤따르는 십신이 결과의 성격을 정한다."
        )
    if chain_grade == "medicine_chain":
        return (
            f"{opening} 이 조합은 좋은 십신이 많아서가 아니라, 한쪽의 병을 다른 한쪽이 제어할 때 약으로 성립한다. "
            "투출과 통근이 약성을 받쳐야 실제로 격국을 살린다."
        )
    if chain_grade in {"risk_chain", "compounded_burden_chain"}:
        return (
            f"{opening} 월령에서 불필요하거나 힘의 균형이 어긋나면 두 십신은 성격을 돕지 않고 병증을 키운다. "
            f"이때 판단의 핵심은 {_subject_form(center)} 보존되는가, 파격 쪽으로 밀리는가다."
        )
    if chain_grade == "mediated_tension_chain":
        return (
            f"{opening} 두 십신은 각각 쓸 수 있어도 바로 맞물리지는 않는다. "
            "월지의 필요, 지지의 뿌리, 운의 순서가 중간에서 매개될 때 현실 작용이 안정된다."
        )
    return (
        f"{opening} 결론은 정해져 있지 않다. "
        "강약, 위치, 투출, 지장간의 뿌리, 합충형파해가 맞으면 쓸 수 있고 어긋나면 부담으로 바뀐다."
    )


def _pattern_combination_state(chain_grade: str, sequence_key: str) -> str:
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        return "성격 보조 조합"
    if chain_grade == "mediated_tension_chain":
        return "매개 필요 조합"
    if chain_grade == "medicine_chain":
        return "병약 조절 조합"
    if chain_grade in {"risk_chain", "compounded_burden_chain"}:
        return "파격 위험 조합"
    if sequence_key == "same_role_amplification":
        return "동류 편중 조합"
    return "조건부 혼합 조합"


def _dual_resolution_logic(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    first_to_second_relation: str,
    chain_grade: str,
    sequence_key: str,
    exact_pair_name: str,
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    state = _chain_resolution_state(chain_grade)
    state_label = CHAIN_RESOLUTION_LABELS[state]
    if first_to_second_relation == "first_generates_second":
        relation_text = f"{_subject_form(first_label)} {_object_form(second_label)} 생한다."
    elif first_to_second_relation == "second_generates_first":
        relation_text = f"{_subject_form(second_label)} {_object_form(first_label)} 생한다."
    elif first_to_second_relation == "first_controls_second":
        relation_text = f"{_subject_form(first_label)} {_object_form(second_label)} 제어한다."
    elif first_to_second_relation == "second_controls_first":
        relation_text = f"{_subject_form(second_label)} {_object_form(first_label)} 제어한다."
    elif first_to_second_relation == "same_group":
        relation_text = f"{_and_form(first_label)} {_subject_form(second_label)} 같은 계열로 중첩된다."
    else:
        relation_text = f"{_and_form(first_label)} {_subject_form(second_label)} 간접적으로 얽힌다."

    if state in {"seonggyeok_chain", "seonggyeok_support_chain"}:
        return (
            f"{pattern_label}에서 {_topic_form(exact_pair_name)} {state_label}에 해당한다. "
            f"{relation_text} 두 십신이 {_object_form(pattern_center)} 돕는 방향으로 이어지면 성격 조건이 두터워진다. "
            f"운에서는 먼저 오는 십신이 시작점을 만들고, 뒤따르는 십신이 결과의 영역을 정한다."
        )
    if state == "byeongyak_medicine_chain":
        return (
            f"{pattern_label}에서 {_topic_form(exact_pair_name)} {state_label}에 해당한다. "
            f"{relation_text} 한쪽이 만든 병을 다른 쪽이 제어하면 조합 전체가 약으로 쓰인다. "
            f"다만 약성이 성립하려면 월령의 필요성과 투출·통근의 실제 힘이 함께 맞아야 한다."
        )
    if state == "mediated_condition_chain":
        return (
            f"{pattern_label}에서 {_topic_form(exact_pair_name)} {state_label}에 해당한다. "
            f"{relation_text} 두 십신은 각각 쓸 수 있어도 서로 바로 맞물리지는 않는다. "
            f"격국 중심, 지지의 뿌리, 대운·세운의 순서가 매개될 때 현실 작용이 안정된다."
        )
    if state in {"pagyeok_chain", "compounded_disease_chain", "disease_chain"}:
        return (
            f"{pattern_label}에서 {_topic_form(exact_pair_name)} {state_label}에 해당한다. "
            f"{relation_text} 이 조합이 월령에서 불필요하거나 과하면 {_object_form(pattern_center)} 흔들고 파격 또는 병증을 만든다. "
            f"운에서 반복되면 돈, 직장, 문서, 관계 중 해당 영역의 사건성이 커진다."
        )
    return (
        f"{pattern_label}에서 {_topic_form(exact_pair_name)} {state_label}에 해당한다. "
        f"{relation_text} 강약, 위치, 투출, 통근, 합충형파해에 따라 성격·병약·파격 중 어디로 갈지 다시 가른다. "
        f"순서가 바뀌면 현실에서 먼저 드러나는 사건도 달라진다."
    )


def _primary_secondary(first_rule, second_rule, chain_grade: str, pattern: str) -> tuple[str, str]:
    first = first_rule.acting_ten_god
    second = second_rule.acting_ten_god
    relation = _relation_between(first_rule.acting_group, second_rule.acting_group)
    disease_grades = BURDEN_GRADES | {"core_overload", "regulator_or_breaker", "breaker_or_medicine"}
    pattern_center = PATTERN_CENTER_BY_PATTERN[pattern]

    if relation == "same_group":
        if first == pattern_center and second != pattern_center:
            return first, second
        if second == pattern_center and first != pattern_center:
            return second, first

    if chain_grade == "medicine_chain":
        if first_rule.role_grade in disease_grades and second_rule.role_grade not in disease_grades:
            return first, second
        if second_rule.role_grade in disease_grades and first_rule.role_grade not in disease_grades:
            return second, first
        return first, second
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        if relation == "second_generates_first":
            return second, first
        return first, second
    if chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"}:
        if first_rule.role_grade in disease_grades and second_rule.role_grade not in disease_grades:
            return first, second
        if second_rule.role_grade in disease_grades and first_rule.role_grade not in disease_grades:
            return second, first
        return first, second
    if first_rule.role_grade in SUPPORTIVE_GRADES and second_rule.role_grade not in SUPPORTIVE_GRADES:
        return first, second
    if second_rule.role_grade in SUPPORTIVE_GRADES and first_rule.role_grade not in SUPPORTIVE_GRADES:
        return second, first
    if first_rule.role_grade in disease_grades and second_rule.role_grade not in disease_grades:
        return first, second
    return first, second


def _actor_hierarchy_logic(
    *,
    pattern: str,
    first_rule,
    second_rule,
    primary_actor: str,
    secondary_actor: str,
    chain_grade: str,
    sequence_key: str,
    first_to_second_relation: str,
) -> str:
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    pattern_center_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_center_label = TEN_GOD_LABEL[pattern_center_ten_god]
    primary_label = TEN_GOD_LABEL[primary_actor]
    secondary_label = TEN_GOD_LABEL[secondary_actor]
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]

    if primary_actor == secondary_actor:
        return (
            f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
            f"{_subject_form(primary_label)} 반복되어 같은 작용이 겹친다. "
            f"이 경우 판단의 핵심은 장점의 선명함보다 과다 여부다. "
            f"{_object_form(pattern_center)} 기준으로 월령에서 필요하면 성격을 보강하고, 과하면 병증을 만든다."
        )
    if chain_grade == "medicine_chain":
        return (
            f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
            f"{_subject_form(primary_label)} 병약을 먼저 가르는 작용이고, {_subject_form(secondary_label)} 그 작용을 보조하거나 제어한다. "
            f"이 조합은 어느 십신이 좋은가보다 어느 십신이 병을 만들고 어느 십신이 약으로 쓰이는지가 핵심이다."
        )
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        return (
            f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
            f"{_subject_form(primary_label)} 먼저 힘을 내고, {_subject_form(secondary_label)} 결과를 받치거나 정리한다. "
            f"{_and_form(first_label)} {second_label}의 결합이 {_object_form(pattern_center)} 돕는 방향이면 성격 조건이 두터워진다. "
            f"운에서는 먼저 강해지는 십신이 사건의 입구가 되고, 뒤따르는 십신이 결과의 형태를 정한다."
        )
    if chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"}:
        if first_to_second_relation in {"first_controls_second", "second_controls_first"}:
            return (
                f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
                f"{_subject_form(primary_label)} 먼저 병증을 여는 작용이고, {_subject_form(secondary_label)} 그 작용에 의해 제어되거나 손상되는 축이다. "
                f"월령에서 불필요하거나 강약이 어긋나면 {_object_form(pattern_center)} 흔들며 파격 또는 병증으로 드러난다."
            )
        if first_to_second_relation == "same_group":
            return (
                f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
                f"{_subject_form(primary_label)} 먼저 부담을 만들고, {_subject_form(secondary_label)} 같은 계열에서 그 부담을 중첩시킨다. "
                f"월령에서 불필요하거나 강약이 어긋나면 {_object_form(pattern_center)} 흔들며 파격 또는 병증으로 드러난다."
            )
        return (
            f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
            f"{_subject_form(primary_label)} 먼저 부담을 만들고, {_subject_form(secondary_label)} 그 부담을 다음 작용으로 넘긴다. "
            f"월령에서 불필요하거나 강약이 어긋나면 {_object_form(pattern_center)} 흔들며 파격 또는 병증으로 드러난다."
        )
    if first_to_second_relation in {"first_generates_second", "second_generates_first"}:
        return (
            f"{pattern_label}에서는 {_subject_form(primary_label)} 방향을 잡고 {_subject_form(secondary_label)} 결과를 보강한다. "
            f"생의 흐름이 이어져도 {_object_form(pattern_center)} 기준으로 필요해야 성격이 된다. "
            f"불필요하면 좋은 상생처럼 보여도 부담이 다음 십신으로 넘어간다."
        )
    if first_to_second_relation in {"first_controls_second", "second_controls_first"}:
        return (
            f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
            f"{_subject_form(primary_label)} 먼저 제어를 걸고, {_subject_form(secondary_label)} 그 제어를 받는 작용이다. "
            f"극은 무조건 흉이 아니며, {_object_form(pattern_center)} 살리는 제어이면 약이 되고 불필요한 제어이면 손상이 된다."
        )
    return (
        f"{pattern_label}에서는 {_object_form(pattern_center_label)} 격국의 중심으로 둔다. "
        f"{_subject_form(primary_label)} 먼저 드러나는 작용이고, {_subject_form(secondary_label)} 그 뒤의 결과를 조정한다. "
        f"두 십신의 직접 생극보다 월령, 위치, 투출, 통근이 먼저 결론을 가른다. "
        f"순서가 바뀌면 돈, 직장, 문서, 관계 중 먼저 사건화되는 영역도 달라진다."
    )


def _disease_medicine_logic(
    pattern: str,
    first_rule,
    second_rule,
    first_to_second_relation: str,
    sequence_key: str,
    chain_grade: str,
    exact_pair_name: str,
) -> str:
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]
    first_face = TEN_GOD_OPERATION_FACE[first_rule.acting_ten_god]["action"]
    second_face = TEN_GOD_OPERATION_FACE[second_rule.acting_ten_god]["action"]
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_nuance = TEN_GOD_EXACT_NUANCE[first_rule.acting_ten_god]
    second_nuance = TEN_GOD_EXACT_NUANCE[second_rule.acting_ten_god]
    pair_name = exact_pair_name or f"{first_label}·{second_label}"
    context_tail = (
        f" {pattern_label} 기준에서는 {_subject_form(first_label)} {_euro_form(first_rule.pattern_effect_state)}, "
        f"{_subject_form(second_label)} {_euro_form(second_rule.pattern_effect_state)} 배치된다. "
        f"따라서 병약은 {_subject_form(first_nuance)} 먼저 {_object_form(pattern_center)} 살리는지, "
        f"{_subject_form(second_nuance)} 뒤에서 그 작용을 보강하거나 흐리는지로 나누어 판정한다."
    )
    if sequence_key == "first_action_damages_pattern_center":
        return (
            f"{_topic_form(pair_name)} {_subject_form(first_label)} {_object_form(second_label)} 직접 치는 조합이다. "
            f"{_subject_form(f'{first_label}의 {first_face}')} "
            f"{pattern_center}의 중심을 손상시키는 병으로 작동한다. "
            f"{_subject_form(second_label)} 투출하고 통근하면 일부 견딜 수 있지만, 약하면 직책, 명분, 평가의 손상이 먼저 드러난다."
            f"{context_tail}"
        )
    if sequence_key == "first_action_conditionally_controls_pattern_center":
        return (
            f"{_topic_form(pair_name)} {_subject_form(f'{first_label}의 {first_face}')} {_object_form(second_label)} 제어하는 조합이다. "
            f"{_subject_form(second_label)} 과할 때는 약이 되고, "
            f"{_subject_form(second_label)} 약할 때는 격국 중심을 손상시키는 병이 된다. "
            f"따라서 월령에서 {_subject_form(pattern_center)} 과한지 약한지를 먼저 보고, 투출과 통근으로 실제 강도를 다시 판정해야 한다."
            f"{context_tail}"
        )
    if chain_grade == "medicine_chain":
        if sequence_key == "first_action_restrains_pattern_pressure":
            disease_label, medicine_label = second_label, first_label
            disease_face, medicine_face = second_face, first_face
        elif first_rule.role_grade in BURDEN_GRADES:
            disease_label, medicine_label = first_label, second_label
            disease_face, medicine_face = first_face, second_face
        elif second_rule.role_grade in BURDEN_GRADES:
            disease_label, medicine_label = second_label, first_label
            disease_face, medicine_face = second_face, first_face
        else:
            disease_label, medicine_label = first_label, second_label
            disease_face, medicine_face = first_face, second_face
        return (
            f"{_topic_form(pair_name)} {_subject_form(f'{medicine_label}의 {medicine_face}')} "
            f"{disease_label}의 {disease_face}에서 생기는 부담을 제어하는 조합이다. "
            f"이 약이 투출하거나 통근하면 {_object_form(pattern_center)} 살리는 쪽으로 쓰이고, 약하면 부담 작용이 먼저 드러난다."
            f"{context_tail}"
        )
    if chain_grade in {"risk_chain", "compounded_burden_chain"}:
        return (
            f"{_topic_form(pair_name)} {_and_form(f'{first_label}의 {first_face}')} {_subject_form(f'{second_label}의 {second_face}')} "
            f"{_object_form(pattern_center)} 보강하기보다 부담을 키우는 쪽으로 결합한다. "
            "월령에서 필요하지 않거나 통근이 약하면 파격 쪽으로 기울 수 있다."
            f"{context_tail}"
        )
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        return (
            f"{_topic_form(pair_name)} {_and_form(f'{first_label}의 {first_face}')} {_subject_form(f'{second_label}의 {second_face}')} "
            f"{pattern_center}의 성립 조건을 보강한다. "
            "두 작용이 투출과 통근으로 받치면 현실 사건으로 쓰기 쉽다."
            f"{context_tail}"
        )
    if chain_grade == "mediated_tension_chain":
        if first_to_second_relation == "first_controls_second":
            controller_label, controlled_label = first_label, second_label
            controller_key, controlled_key = first_rule.acting_ten_god, second_rule.acting_ten_god
        elif first_to_second_relation == "second_controls_first":
            controller_label, controlled_label = second_label, first_label
            controller_key, controlled_key = second_rule.acting_ten_god, first_rule.acting_ten_god
        else:
            controller_label, controlled_label = first_label, second_label
            controller_key, controlled_key = first_rule.acting_ten_god, second_rule.acting_ten_god
        controller_face = TEN_GOD_OPERATION_FACE[controller_key]["action"]
        controlled_face = TEN_GOD_OPERATION_FACE[controlled_key]["action"]
        return (
            f"{_and_form(first_label)} {_subject_form(second_label)} 각각 격국 안에서 필요한 역할을 가질 수 있다. "
            f"다만 두 십신 사이에는 {_subject_form(controller_label)} {_object_form(controlled_label)} 제어하는 직접 극이 있으므로, "
            f"{_subject_form(pattern_center)} 매개되어야 성격으로 성립한다. "
            f"매개가 약하면 {_subject_form(f'{controller_label}의 {controller_face}')} "
            f"{_object_form(f'{controlled_label}의 {controlled_face}')} 눌러 성과보다 충돌이 먼저 드러난다."
            f"{context_tail}"
        )
    if sequence_key == "same_role_amplification":
        return (
            f"{_and_form(first_label)} {_subject_form(second_label)} 같은 계열이 겹친 조합이다. "
            f"장점은 선명해지지만 과하면 편중이 병이 된다."
            f"{context_tail}"
        )
    return f"{first_label}·{second_label} 조합의 성패는 월령, 강약, 위치, 투출 여부를 함께 보아 결정한다.{context_tail}"


def _sequence_activation(
    *,
    pattern: str,
    first_rule,
    second_rule,
    first_to_second_relation: str,
    chain_grade: str,
    pattern_center_bridge: dict[str, object],
) -> tuple[str, str]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]
    first_action = first_rule.action_nature
    second_action = second_rule.action_nature
    first_timing_face = TEN_GOD_OPERATION_FACE[first_rule.acting_ten_god]["timing"]
    second_timing_face = TEN_GOD_OPERATION_FACE[second_rule.acting_ten_god]["timing"]
    bridge_direction = pattern_center_bridge.get("direction", "")

    def contextualize(text: str) -> str:
        value = text.strip()
        if pattern_label not in value:
            value = f"{pattern_label}에서는 {_object_form(pattern_center)} 기준으로 {value}"
        if first_label not in value or second_label not in value:
            value = f"{value} 이 판단은 {_and_form(first_label)} {second_label}의 선후를 함께 본다."
        return value

    if bridge_direction == "first_to_second_via_pattern_center":
        return (
            contextualize(
                f"운에서 {_subject_form(first_label)} 먼저 오면 {first_action} 작용이 입구가 된다. "
                f"다만 {pattern_label}에서는 {_object_form(pattern_center)} 거쳐야 {_subject_form(second_label)} 결론으로 넘어간다."
            ),
            contextualize(
                f"운에서 {_subject_form(second_label)} 먼저 오면 {_subject_form(second_timing_face)} 먼저 드러난다. "
                f"이때 {_subject_form(first_label)} 뒤따라야 {_object_form(pattern_center)} 통해 원인과 결과가 이어진다."
            ),
        )
    if bridge_direction == "second_to_first_via_pattern_center":
        return (
            contextualize(
                f"운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(first_timing_face)} 먼저 요구된다. "
                f"{pattern_label}에서는 {_subject_form(second_label)} 뒤따라 {_object_form(pattern_center)} 받쳐야 지속된다."
            ),
            contextualize(
                f"운에서 {_subject_form(second_label)} 먼저 오면 배경 조건이 열린다. "
                f"{_subject_form(pattern_center)} 이를 받아 주면 {_subject_form(first_label)} 현실 작용으로 정리된다."
            ),
        )
    if bridge_direction == "first_controls_second_via_pattern_center":
        return (
            contextualize(
                f"운에서 {_subject_form(first_label)} 먼저 오면 제어 압력이 먼저 생긴다. "
                f"{pattern_label}에서는 이 극이 바로 손상이 되지 않으려면 {_subject_form(pattern_center)} 중간 질서가 되어야 한다."
            ),
            contextualize(
                f"운에서 {_subject_form(second_label)} 먼저 오면 제어받을 대상이 먼저 드러난다. "
                f"뒤이어 {_subject_form(first_label)} 들어오면 {_object_form(pattern_center)} 통해 정리되거나 직접 충돌로 갈린다."
            ),
        )
    if bridge_direction == "second_controls_first_via_pattern_center":
        return (
            contextualize(
                f"운에서 {_subject_form(first_label)} 먼저 오면 앞 작용이 먼저 커진다. "
                f"뒤이어 {_subject_form(second_label)} 들어오면 {_object_form(pattern_center)} 거쳐 조절될 때 약으로 쓰인다."
            ),
            contextualize(
                f"운에서 {_subject_form(second_label)} 먼저 오면 제어가 먼저 시작된다. "
                f"{pattern_label}에서는 {_subject_form(pattern_center)} 약하면 제어가 조절이 아니라 차단으로 드러난다."
            ),
        )

    if first_to_second_relation == "first_generates_second":
        first_then_second = (
            f"운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(first_timing_face)} 사건의 입구가 된다. "
            f"뒤이어 {_subject_form(second_label)} 오면 {second_timing_face} 쪽으로 결론이 이동한다."
        )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 {_subject_form(second_timing_face)} 먼저 드러난다. "
            f"뒤이어 {_subject_form(first_label)} 오지 않으면 근거가 약하고, 들어오면 원인과 결론이 연결된다."
        )
    elif first_to_second_relation == "second_generates_first":
        first_then_second = (
            f"운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(first_timing_face)} 먼저 드러나지만 받치는 배경이 약할 수 있다. "
            f"뒤이어 {_subject_form(second_label)} 오면 {_subject_form(second_timing_face)} 근거가 되어 지속성이 생긴다."
        )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 {_subject_form(second_timing_face)} 배경 조건으로 마련된다. "
            f"뒤이어 {_subject_form(first_label)} 오면 {first_timing_face}의 현실 사건으로 나타난다."
        )
    elif first_to_second_relation == "first_controls_second":
        if chain_grade == "medicine_chain":
            first_then_second = (
                f"운에서 {_subject_form(first_label)} 먼저 오면 제어와 처리 방식이 먼저 생긴다. "
                f"뒤이어 {_subject_form(second_label)} 오면 병을 약으로 쓰는지, 부담을 더 키우는지 갈린다."
            )
        else:
            first_then_second = (
                f"운에서 {_subject_form(first_label)} 먼저 오면 제어 압력이 먼저 생긴다. "
                f"뒤이어 {_subject_form(second_label)} 오면 {second_timing_face} 쪽이 눌리거나 손상될 수 있다."
            )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 제어받을 사건이 먼저 드러난다. "
            f"뒤이어 {_subject_form(first_label)} 오면 이를 정리할 수도 있고, 과하면 끊어낼 수도 있다."
        )
    elif first_to_second_relation == "second_controls_first":
        first_then_second = (
            f"운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(first_timing_face)} 먼저 커진다. "
            f"뒤이어 {_subject_form(second_label)} 오면 그 작용을 조절하거나 눌러 사건의 결론을 바꾼다."
        )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 제어가 먼저 시작된다. "
            f"뒤이어 {_subject_form(first_label)} 오면 이미 세워진 제한 안에서 움직이게 된다."
        )
    elif first_to_second_relation == "same_group":
        first_then_second = (
            f"운에서 {_subject_form(first_label)} 먼저 오면 같은 계열의 작용이 한 번 드러난다. "
            f"뒤이어 {_subject_form(second_label)} 오면 장점도 커지지만 편중도 함께 강해진다."
        )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 같은 계열의 다른 얼굴이 먼저 드러난다. "
            f"뒤이어 {_subject_form(first_label)} 오면 반복 작용이 되어 성격과 병이 더 선명해진다."
        )
    else:
        first_then_second = (
            f"운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(first_timing_face)} 사건의 입구가 된다. "
            f"뒤이어 {_subject_form(second_label)} 오면 {second_timing_face} 쪽으로 결과가 재조정된다."
        )
        second_then_first = (
            f"운에서 {_subject_form(second_label)} 먼저 오면 {_subject_form(second_timing_face)} 사건의 입구가 된다. "
            f"뒤이어 {_subject_form(first_label)} 오면 {first_timing_face} 쪽의 조건이 다시 바뀐다."
        )
    return contextualize(first_then_second), contextualize(second_then_first)


def _dual_timing_activation(
    pattern: str,
    first_rule,
    second_rule,
    chain_grade: str,
    exact_pair_category: str,
) -> str:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]
    first_timing = TEN_GOD_OPERATION_FACE[first_rule.acting_ten_god]["timing"]
    second_timing = TEN_GOD_OPERATION_FACE[second_rule.acting_ten_god]["timing"]
    relation = _relation_between(first_rule.acting_group, second_rule.acting_group)
    category_context = _dual_category_context(exact_pair_category, relation)
    order_tail = (
        f" {pattern_label}에서는 {_subject_form(first_label)} 먼저 오면 {first_timing} 관련 사건이 {_object_form(pattern_center)} 먼저 건드리고, "
        f"{_subject_form(second_label)} 뒤따르면 {second_timing} 쪽으로 결론이 이동한다. "
        f"반대로 {_subject_form(second_label)} 먼저 오면 사건의 입구가 달라져 {second_rule.pattern_effect_state} 쪽이 먼저 드러난다. "
        f"대운에서는 {category_context['daeun']}. 세운에서는 {category_context['seun']}. {category_context['order']}"
    )
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        return f"대운·세운에서 두 십신이 순차적으로 들어오면 격국의 성립 조건이 현실 사건으로 커진다.{order_tail}"
    if chain_grade == "medicine_chain":
        return f"대운·세운에서 약이 되는 십신이 들어오면 기존 부담이 정리되거나 쓰임으로 바뀐다.{order_tail}"
    if chain_grade == "mediated_tension_chain":
        return f"대운·세운에서 한쪽만 먼저 강해지면 두 십신의 충돌이 먼저 드러나고, 격국 중심을 매개하는 운이 이어질 때 성과로 정리된다.{order_tail}"
    if chain_grade in {"risk_chain", "compounded_burden_chain"}:
        return f"대운·세운에서 두 부담 십신이 함께 움직이면 손실, 충돌, 책임 문제가 커질 수 있다.{order_tail}"
    return f"대운·세운의 순서와 원국의 위치에 따라 기회와 부담이 갈린다.{order_tail}"


def _activation_order_profile(
    *,
    pattern: str,
    first_rule,
    second_rule,
    chain_grade: str,
    combination_resolution_state: str,
    first_then_second_activation: str,
    second_then_first_activation: str,
    domain_priority: list[str],
) -> dict[str, object]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_center_label = TEN_GOD_LABEL[pattern_center_ten_god]

    def domain_labels(domains: list[str]) -> list[str]:
        return [
            {
                "money": "재물",
                "career": "직업",
                "relationship": "관계",
                "marriage": "결혼",
                "personality": "성향",
                "reputation": "명예",
            }.get(domain, domain)
            for domain in domains
        ]

    def compact_domains(*domain_lists: list[str]) -> list[str]:
        merged: list[str] = []
        for domains in domain_lists:
            for domain in domains:
                if domain and domain not in merged:
                    merged.append(domain)
        return merged[:4]

    def event_targets(group: str, domains: list[str]) -> list[str]:
        targets: list[str] = []
        for domain in domains[:3]:
            targets.extend(DOMAIN_EVENT_TARGETS.get(domain, (domain,)))
        targets.extend(GROUP_EVENT_TARGETS.get(group, (group,)))
        return list(dict.fromkeys(targets))[:8]

    def direction(entry_rule, follow_rule, sequence_logic: str) -> dict[str, object]:
        entry_domains = compact_domains(list(entry_rule.domain_priority), domain_priority)
        result_domains = compact_domains(list(follow_rule.domain_priority), domain_priority, list(entry_rule.domain_priority))
        entry_label = TEN_GOD_LABEL[entry_rule.acting_ten_god]
        follow_label = TEN_GOD_LABEL[follow_rule.acting_ten_god]
        entry_face = TEN_GOD_OPERATION_FACE[entry_rule.acting_ten_god]
        follow_face = TEN_GOD_OPERATION_FACE[follow_rule.acting_ten_god]
        return {
            "entry_ten_god": entry_rule.acting_ten_god,
            "entry_ten_god_label": entry_label,
            "entry_group": entry_rule.acting_group,
            "entry_operation_face": entry_face["timing"],
            "entry_action_face": entry_face["action"],
            "entry_domains": entry_domains,
            "entry_domain_labels": domain_labels(entry_domains),
            "entry_event_targets": event_targets(entry_rule.acting_group, entry_domains),
            "follow_ten_god": follow_rule.acting_ten_god,
            "follow_ten_god_label": follow_label,
            "follow_group": follow_rule.acting_group,
            "follow_operation_face": follow_face["timing"],
            "follow_action_face": follow_face["action"],
            "result_domains": result_domains,
            "result_domain_labels": domain_labels(result_domains),
            "result_event_targets": event_targets(follow_rule.acting_group, result_domains),
            "sequence_logic": sequence_logic,
            "sequence_summary": (
                f"{entry_label} 운이 먼저 오면 {entry_face['timing']}이 사건의 입구가 되고, "
                f"{follow_label} 운이 뒤따르면 {follow_face['timing']} 쪽으로 결과가 정리된다."
            ),
        }

    return {
        "pattern": pattern,
        "pattern_label": pattern_label,
        "pattern_center_ten_god": pattern_center_ten_god,
        "pattern_center_label": pattern_center_label,
        "chain_grade": chain_grade,
        "combination_resolution_state": combination_resolution_state,
        "dominant_result_domains": list(domain_priority[:4]),
        "dominant_result_domain_labels": domain_labels(list(domain_priority[:4])),
        "first_then_second": direction(first_rule, second_rule, first_then_second_activation),
        "second_then_first": direction(second_rule, first_rule, second_then_first_activation),
    }


def _dual_domain_priority(pattern: str, first_rule, second_rule, chain_grade: str) -> list[str]:
    scores: dict[str, float] = {}
    for domain, weight in PATTERN_DOMAIN_BIAS.get(pattern, {}).items():
        scores[domain] = scores.get(domain, 0.0) + weight
    for index, domain in enumerate(first_rule.domain_priority):
        scores[domain] = scores.get(domain, 0.0) + max(0.5, 1.6 - index * 0.28)
    for index, domain in enumerate(second_rule.domain_priority):
        scores[domain] = scores.get(domain, 0.0) + max(0.4, 1.25 - index * 0.24)
    for domain, weight in TEN_GOD_DOMAIN_WEIGHTS[first_rule.acting_ten_god].items():
        scores[domain] = scores.get(domain, 0.0) + weight * 1.05
    for domain, weight in TEN_GOD_DOMAIN_WEIGHTS[second_rule.acting_ten_god].items():
        scores[domain] = scores.get(domain, 0.0) + weight * 0.92
    if chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"}:
        scores["relationship"] = scores.get("relationship", 0.0) + 1.2
    if chain_grade in {"medicine_chain", "constructive_chain", "supportive_chain"}:
        scores["career"] = scores.get("career", 0.0) + 0.8
        scores["money"] = scores.get("money", 0.0) + 0.5
    if first_rule.acting_group == "output" and second_rule.acting_group == "output":
        if pattern == "eating_god_pattern":
            scores["money"] = scores.get("money", 0.0) + 1.4
        elif pattern == "hurting_officer_pattern":
            scores["reputation"] = scores.get("reputation", 0.0) + 1.4
            scores["relationship"] = scores.get("relationship", 0.0) + 0.7
    return [
        domain
        for domain, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        if domain in {"money", "career", "relationship", "marriage", "personality", "reputation"}
    ][:5]


def _dual_domain_projections(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    chain_grade: str,
    sequence_key: str,
    exact_pair_name: str = "",
    direct_pair_name: str = "",
) -> dict[str, str]:
    label = PATTERN_LENS[pattern]["label"]
    center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    relation = _relation_between(TEN_GOD_GROUPS[first_ten_god], TEN_GOD_GROUPS[second_ten_god])
    direct_exact_name = direct_pair_name or _exact_pair_name(first_ten_god, second_ten_god, relation)
    exact_name = exact_pair_name or direct_exact_name
    pair_category = _pair_category(first_ten_god, second_ten_god, relation)
    chain_text = CHAIN_DOMAIN_FACE.get(chain_grade, "강약과 위치에 따라 성패가 갈린다.")

    def relation_sentence() -> str:
        exact_form = _euro_form(exact_name)
        if relation == "same_group":
            return f"{exact_form} 작용한다. {_and_form(first_label)} {_subject_form(second_label)} 같은 계열에서 겹친다."
        if pair_category == "output_generates_wealth":
            return f"{exact_form} 작용한다. 식상에서 나온 결과물이 재물과 거래로 넘어간다."
        if pair_category == "wealth_generates_officer":
            if "편관" in exact_name:
                return f"{exact_form} 작용한다. 재성이 편관을 생하면 돈과 욕심이 압박과 위험 부담을 키운다."
            return f"{exact_form} 작용한다. 재성이 정관을 생하면 돈과 현실 기반이 직책, 신용, 공식 책임으로 넘어간다."
        if pair_category == "officer_generates_resource":
            if exact_name == "살인상생":
                return f"{exact_form} 작용한다. 편관의 압박이 인성의 자격, 문서, 보호 장치로 전환된다."
            return f"{exact_form} 작용한다. 관성의 책임이 인성의 자격, 문서, 명분으로 안정된다."
        if pair_category == "resource_generates_peer":
            return f"{exact_form} 작용한다. 인성이 자기 기반과 비겁을 생해 버티는 힘을 키운다."
        if pair_category == "peer_generates_output":
            return f"{exact_form} 작용한다. 비겁의 자기 기반이 식상으로 빠져 결과물과 표현으로 나온다."
        if pair_category == "output_controls_officer":
            if exact_name != direct_exact_name:
                if direct_exact_name == "식신제관":
                    return (
                        f"{_euro_form(exact_name)} 작용한다. "
                        "직접 생극에서는 식신제관으로 작용한다. 식신이 정관을 부수는 것이 아니라 공식 책임을 실제 성과로 감당한다."
                    )
                if direct_exact_name == "식신제살":
                    return (
                        f"{_euro_form(exact_name)} 작용한다. "
                        "직접 생극에서는 식신제살로 작용한다. 식신이 편관의 압박을 실무와 결과물로 낮춘다."
                    )
                if direct_exact_name == "상관견관":
                    return (
                        f"{_euro_form(exact_name)} 작용한다. "
                        "직접 생극에서는 상관견관으로 작용한다. 상관의 표현과 반발이 정관의 직책, 평판 질서를 건드린다."
                    )
            if exact_name == "식신제살":
                return f"{exact_form} 작용한다. 식신이 편관의 압박을 실무와 결과물로 낮춘다."
            if exact_name == "식신제관":
                return f"{exact_form} 작용한다. 식신이 정관을 부수는 것이 아니라 공식 책임을 실제 성과로 감당한다."
            if exact_name == "상관견관":
                return f"{exact_form} 작용한다. 상관의 표현과 반발이 정관의 직책, 평판 질서를 건드린다."
            if exact_name == "상관제살":
                return f"{exact_form} 작용한다. 상관의 돌파성이 편관의 압박과 정면으로 맞선다."
        if pair_category == "wealth_controls_resource":
            if exact_name != direct_exact_name:
                return (
                    f"{_euro_form(exact_name)} 작용한다. "
                    f"직접 생극으로는 {direct_exact_name}이지만, 격국 중심을 거치며 다른 결론으로 재배열된다."
                )
            return f"{exact_form} 작용한다. 재성이 인성의 명분과 보호성을 현실의 소유, 성과 요구로 누른다."
        if pair_category == "peer_controls_wealth":
            return f"{exact_form} 작용한다. 비겁이 재성을 치면 돈에 사람, 지분, 몫 문제가 끼어든다."
        if pair_category == "officer_controls_peer":
            return f"{exact_form} 작용한다. 관성이 비겁의 경쟁과 분점성을 규칙, 책임, 직책으로 정리한다."
        if pair_category == "resource_controls_output":
            if exact_name in {"편인도식", "정인제식"}:
                return f"{exact_form} 작용한다. 인성이 식상의 생산과 표현을 문서, 명분, 보류성으로 제어한다."
            return f"{exact_form} 작용한다. 인성이 식상의 표현과 결과물을 절차와 근거로 조절한다."
        if relation == "first_generates_second":
            return f"{exact_form} 작용한다. {_subject_form(first_label)} {_object_form(second_label)} 생해 다음 작용으로 넘긴다."
        if relation == "second_generates_first":
            return f"{exact_form} 작용한다. {_subject_form(second_label)} {_object_form(first_label)} 생해 앞 작용을 받친다."
        if relation == "first_controls_second":
            return f"{exact_form} 작용한다. {_subject_form(first_label)} {_object_form(second_label)} 제어한다."
        if relation == "second_controls_first":
            return f"{exact_form} 작용한다. {_subject_form(second_label)} {_object_form(first_label)} 제어한다."
        return f"{exact_form} 작용한다. {_and_form(first_label)} {_subject_form(second_label)} 간접적으로 얽힌다."

    relation_text = relation_sentence()

    def face(ten_god: str, domain: str) -> str:
        return TEN_GOD_DOMAIN_FACE.get(ten_god, {}).get(domain, TEN_GOD_OPERATION_FACE[ten_god]["action"])

    def combined_face(first_face: str, second_face: str) -> str:
        if first_face == second_face:
            return f"{_subject_form(first_face)} 반복되어"
        return f"{_and_form(first_face)} {_subject_form(second_face)} 결합해"

    def sentence(domain: str, domain_label: str, conclusion: str) -> str:
        first_face = face(first_ten_god, domain)
        second_face = face(second_ten_god, domain)
        pattern_center = f"{label}의 {center}"
        if domain == "personality":
            return (
                f"{_topic_form(pattern_center)} 성격과 판단 경향에서 {_and_form(first_label)} {_subject_form(second_label)} 함께 작용하는 방식으로 드러난다. "
                f"{relation_text} {chain_text} {conclusion}"
            )
        return (
            f"{_topic_form(pattern_center)} {domain_label}에서 {combined_face(first_face, second_face)} 드러난다. "
            f"{relation_text} {chain_text} {conclusion}"
        )

    def personality_conclusion() -> str:
        if pair_category == "output_generates_wealth":
            if "식신" in exact_name:
                return (
                    "성향에서는 손에 익은 결과를 꾸준히 내놓고, 그것을 안정된 보상으로 바꾸려는 계산이 강하다. "
                    "결과물이 분명할수록 자신감이 안정되고, 결과 없이 돈부터 의식하면 마음이 급해진다."
                )
            if "상관" in exact_name:
                return (
                    "성향에서는 말, 기획, 개선 능력을 시장의 반응과 보상으로 확인하려는 경향이 강하다. "
                    "강하면 빠른 상품화 감각이 되고, 과하면 인정과 수익을 서둘러 관계나 평판을 건드린다."
                )
            return "성향에서는 만든 것을 실제 보상으로 바꾸려는 계산이 강해진다. 결과물이 없으면 마음이 급해지고, 결과가 분명하면 자신감이 안정된다."
        if pair_category == "wealth_generates_officer":
            if "편관" in exact_name:
                return (
                    "성향에서는 손익 판단이 승부성, 압박감, 위험 감수로 이어진다. "
                    "강하면 어려운 자리에서 결단이 빠르지만, 과하면 돈과 책임을 함께 끌어안고 긴장을 키운다."
                )
            return (
                "성향에서는 현실 감각이 책임 의식과 사회적 신용으로 이어진다. "
                "맡은 몫과 보상 기준이 분명할수록 태도가 안정되고, 과하면 돈 문제를 체면과 책임으로 떠안는다."
            )
        if pair_category == "officer_generates_resource":
            if exact_name == "살인상생":
                return (
                    "성향에서는 강한 압박을 그대로 받아치기보다 자격, 문서, 배움, 보호 장치로 흡수하려 한다. "
                    "위기 앞에서 신중해지고, 근거가 없으면 불안과 방어심이 먼저 커진다."
                )
            return (
                "성향에서는 책임을 근거와 명분으로 정리하려는 경향이 강하다. "
                "원칙과 절차가 분명할수록 품위가 살아나고, 과하면 행동보다 승인과 체면을 먼저 확인한다."
            )
        if pair_category == "resource_generates_peer":
            if "겁재" in exact_name:
                return (
                    "성향에서는 배운 것과 보호받은 기반이 경쟁심과 주도권으로 넘어가기 쉽다. "
                    "강하면 버티는 힘이 되지만, 과하면 자기 논리를 앞세워 관계의 긴장을 만든다."
                )
            return (
                "성향에서는 배운 것과 보호받은 기반을 자기 확신으로 바꾸려 한다. "
                "강하면 기준이 흔들리지 않고, 과하면 자기 입장이 단단해져 타협이 늦어진다."
            )
        if pair_category == "peer_generates_output":
            return "성향에서는 자기 기준을 말과 결과물로 밀어내려는 경향이 강하다. 혼자 품고 있기보다 밖으로 드러내야 기운이 풀린다."
        if pair_category == "output_controls_officer":
            if exact_name != direct_exact_name:
                if direct_exact_name == "식신제관":
                    return (
                        "성향에서는 직접 부딪치기보다 해낸 결과를 통해 책임과 평가를 받아내려 한다. "
                        "압박을 말이나 실무 처리로 낮추려는 경향도 함께 나타난다. "
                        "꾸준한 실무 성과가 있을수록 태도가 안정되고, 성과 없이 책임만 커지면 부담이 먼저 온다."
                    )
                if direct_exact_name == "식신제살":
                    return (
                        "성향에서는 위험과 압박을 감정으로 키우지 않고 처리 절차와 반복된 기술로 낮추려 한다. "
                        "격국 중심이 받쳐 주면 실무형 해결력이 되고, 약하면 책임을 피하려는 태도로 보일 수 있다."
                    )
                if direct_exact_name == "상관견관":
                    return (
                        "성향에서는 문제를 그냥 넘기지 않고 개선점과 손익을 동시에 보려 한다. "
                        "격국 중심이 받쳐 주면 시장 감각 있는 개혁성이 되고, 거칠면 말과 태도가 평가 질서를 건드린다."
                    )
            if exact_name == "상관견관":
                return (
                    "성향에서는 규칙을 그대로 받아들이기보다 문제점을 먼저 보는 경향이 강하다. "
                    "허점과 불합리가 보이면 그냥 넘기지 않는다. "
                    "결과가 있으면 개혁성이 되고, 말이 앞서면 직책과 평판을 직접 건드린다."
                )
            if exact_name == "식신제살":
                return (
                    "성향에서는 압박을 말이나 실무 처리로 낮추려는 경향이 강하다. "
                    "손에 익은 처리 방식이 있을수록 긴장 상황에서 안정되고, 준비가 약하면 부담이 오래 남는다."
                )
            if exact_name == "상관제살":
                return (
                    "성향에서는 강한 압박 앞에서 물러서기보다 돌파구를 만들려 한다. "
                    "재주가 날카로우면 위기를 뚫지만, 과하면 위험한 자리에서 말과 행동이 앞선다."
                )
            return "성향에서는 압박을 말이나 실무 처리로 낮추려는 경향이 강하다. 해본 방식이 있을수록 긴장 상황에서 안정된다."
        if pair_category == "wealth_controls_resource":
            if pattern == "direct_officer_pattern" and exact_name != direct_exact_name:
                return (
                    "성향에서는 현실 판단이 곧장 문서와 명분을 누르기보다, 책임 기준을 거쳐 안정된 태도로 정리된다. "
                    "돈, 직책, 자격을 따로 보지 않고 하나의 공식성 안에서 맞추려는 경향이 강하다."
                )
            if pattern == "seven_killings_pattern" and exact_name != direct_exact_name:
                return (
                    "성향에서는 현실 부담을 빠르게 읽지만, 그 부담을 혼자 떠안기보다 근거와 보호 장치를 먼저 찾는다. "
                    "압박이 커질수록 문서, 자격, 배후의 지원 여부에 예민해진다."
                )
            if pattern in {"direct_resource_pattern", "indirect_resource_pattern"}:
                return (
                    "성향에서는 생각보다 현실 결론을 먼저 요구하는 쪽으로 움직인다. "
                    "강하면 실행력이 되고, 약하면 마음의 안정과 문서 기반이 먼저 흔들린다."
                )
            if pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"}:
                return (
                    "성향에서는 손익, 소유권, 증빙을 분명히 하려는 기질이 강하다. "
                    "명분이 길어질수록 답답해하고, 계산이 서면 판단이 빨라진다."
                )
            return "성향에서는 생각보다 현실 결론을 먼저 요구하는 쪽으로 기운다. 명분이 길어지면 답답해지고, 근거가 분명하면 실행이 빨라진다."
        if pair_category == "peer_controls_wealth":
            if "겁재" in exact_name:
                return (
                    "성향에서는 내 몫을 지키려는 마음과 상대보다 밀리지 않으려는 경쟁심이 함께 움직인다. "
                    "가까운 사람일수록 정과 계산이 섞이고, 돈이 보이면 주도권 문제가 빨라진다."
                )
            return (
                "성향에서는 자기 몫과 생활 기준을 쉽게 양보하지 않으려 한다. "
                "강하면 소유 감각이 분명하지만, 과하면 작은 분배 문제도 오래 기억한다."
            )
        if pair_category == "officer_controls_peer":
            return "성향에서는 자기주장을 규칙과 책임으로 정리하려 한다. 권한이 분명하면 절제력이 되고, 억압이 강하면 위축으로 나타난다."
        if pair_category == "resource_controls_output":
            if exact_name == "편인도식":
                return (
                    "성향에서는 특수한 몰입과 의심이 결과물보다 먼저 선다. "
                    "깊이는 생기지만, 과하면 확신을 늦추고 내놓아야 할 결과를 계속 보류한다."
                )
            if exact_name == "정인제식":
                return (
                    "성향에서는 안정 확인과 절차가 표현보다 먼저 선다. "
                    "품질과 신뢰는 좋아지지만, 과하면 안전한 답을 찾느라 결과가 늦어진다."
                )
            return "성향에서는 생각과 검토가 표현보다 먼저 선다. 깊이는 생기지만, 과하면 내놓아야 할 결과가 늦어진다."
        if relation == "same_group":
            if pair_category == "wealth_same_group":
                return (
                    "성향에서는 안정적으로 지키려는 계산과 밖으로 넓히려는 욕구가 함께 움직인다. "
                    "강하면 재물 감각이 넓어지지만, 과하면 돈을 묶을지 굴릴지 판단이 흔들린다."
                )
            if pair_category == "officer_same_group":
                return (
                    "성향에서는 원칙을 지키려는 마음과 압박에 즉시 대응하려는 긴장이 함께 움직인다. "
                    "강하면 책임감이 분명하지만, 과하면 관살혼잡처럼 기준과 불안이 같이 커진다."
                )
            if pair_category == "output_same_group":
                return (
                    "성향에서는 꾸준히 만들려는 힘과 빠르게 표현하려는 힘이 함께 움직인다. "
                    "강하면 재주가 선명하지만, 과하면 말과 결과물이 서로 앞서가 산만해진다."
                )
            if pair_category == "resource_same_group":
                return (
                    "성향에서는 확인하고 보호받으려는 마음과 한쪽으로 깊게 몰입하는 기질이 함께 커진다. "
                    "강하면 이해가 깊지만, 과하면 생각이 많아 실행이 늦어진다."
                )
            if pair_category == "peer_same_group":
                return (
                    "성향에서는 자기 기준과 경쟁심이 동시에 강해진다. "
                    "강하면 독립성과 추진력이 되지만, 과하면 타협보다 주도권을 먼저 본다."
                )
            return "성향에서는 같은 기운이 반복되어 장점과 병이 동시에 선명해진다. 강점은 분명하지만 균형을 잃으면 한쪽으로 치우친다."
        if chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"}:
            return "성향에서는 반응이 빠르게 굳거나 부담을 크게 받아들이는 쪽으로 나타난다. 운에서 강해지면 선택이 급해질 수 있다."
        return "성향에서는 두 작용의 순서에 따라 관심, 판단, 행동 속도가 달라진다. 어느 쪽이 먼저 발동되는지가 실제 태도를 가른다."

    def life_domain_conclusion(domain: str) -> str:
        by_pair = {
            "output_generates_wealth": {
                "money": "재물에서는 결과물의 가격화, 반복 구매, 회수 기준이 핵심이다. 만든 것이 있어도 팔릴 구조가 없으면 돈으로 굳지 않는다.",
                "career": "직업에서는 실무 성과와 보상 기준이 붙을 때 강하다. 말이나 재주가 직무 성과로 인정되어야 한다.",
                "relationship": "관계에서는 표현과 실질적 도움을 통해 신뢰가 생긴다. 말보다 반복해서 보여주는 결과가 관계를 안정시킨다.",
                "marriage": "결혼에서는 생활 속 기여와 재정 기준이 함께 움직인다. 해주는 일과 돈의 기준이 분리되지 않으면 서운함이 생긴다.",
            },
            "wealth_generates_officer": {
                "money": "재물에서는 돈이 직책, 책임, 신용으로 이동한다. 보상 기준이 분명하면 상승이고, 권한 없이 책임만 커지면 부담이다.",
                "career": "직업에서는 자원과 성과가 공식 역할로 이어진다. 돈을 다루는 능력이 책임 있는 자리로 평가된다.",
                "relationship": "관계에서는 현실적 책임과 약속이 중요해진다. 호감보다 신뢰와 책임 이행이 관계의 무게를 만든다.",
                "marriage": "결혼에서는 생활비와 책임 범위가 배우자 신뢰로 이어진다. 돈의 기준이 흐리면 책임 문제가 커진다.",
            },
            "officer_generates_resource": {
                "money": "재물에서는 직책과 책임이 문서, 자격, 보호 장치로 안정된다. 근거 없는 돈보다 증빙 있는 돈이 강하다.",
                "career": "직업에서는 책임이 자격과 명분으로 받쳐질 때 오래 간다. 직함보다 문서와 제도적 근거가 중요하다.",
                "relationship": "관계에서는 믿을 만한 태도와 공식성이 신뢰의 근거가 된다. 말보다 절차와 책임 이행이 중요하다.",
                "marriage": "결혼에서는 법적 책임, 가족 절차, 문서 안정성이 생활 신뢰를 만든다.",
            },
            "wealth_controls_resource": {
                "money": (
                    "재물에서는 현실의 돈과 소유 문제가 문서, 명분, 보호성을 압박한다. 좋으면 실행이 빨라지고, 나쁘면 문서 손상이 생긴다."
                    if exact_name == direct_exact_name
                    else "재물에서는 돈이 직책과 자격의 통로를 거쳐 안정된다. 수입 자체보다 그 돈이 어떤 책임과 증빙 위에 놓이는지가 중요해진다."
                ),
                "career": (
                    "직업에서는 성과 요구가 공부와 자격 준비를 앞당긴다. 준비만 길어지면 현실 요구가 압박으로 들어온다."
                    if exact_name == direct_exact_name
                    else "직업에서는 재정 감각, 책임 범위, 문서 근거가 함께 맞을 때 공식 평가가 안정된다. 성과만 앞서면 책임은 커지고 보호 장치는 약해진다."
                ),
                "relationship": (
                    "관계에서는 마음보다 현실 조건이 먼저 보일 수 있다. 돈과 생활 문제가 신뢰의 기준을 바꾼다."
                    if exact_name == direct_exact_name
                    else "관계에서는 호의보다 책임의 근거를 먼저 확인하려는 경향이 강해진다. 서로 믿더라도 역할과 약속이 분명해야 마음이 놓인다."
                ),
                "marriage": (
                    "결혼에서는 자산, 주거, 가족 조건이 명분보다 앞서기 쉽다. 현실 조건이 맞지 않으면 안정이 늦어진다."
                    if exact_name == direct_exact_name
                    else "결혼에서는 생활비, 책임, 가족 절차가 한 흐름으로 묶인다. 감정보다 공식적인 합의와 문서 안정성이 생활 신뢰를 만든다."
                ),
            },
            "peer_controls_wealth": {
                "money": "재물에서는 사람, 지분, 공동 비용이 소유권을 흔든다. 가까운 사람일수록 돈의 경계가 중요하다.",
                "career": "직업에서는 동료 경쟁, 지분 다툼, 역할 분배가 성과를 흔들 수 있다. 규칙이 없으면 내 몫이 흐려진다.",
                "relationship": "관계에서는 정과 계산이 함께 움직인다. 서로 도와도 몫의 기준이 없으면 감정이 상한다.",
                "marriage": "결혼에서는 가족 재정과 배우자 주도권 문제가 커질 수 있다. 생활비와 소유권을 분명히 해야 한다.",
            },
            "output_controls_officer": {
                "money": "재물에서는 결과물이나 말이 책임과 평가를 건드린다. 성과가 분명하면 보상으로 가고, 말만 앞서면 손실이다.",
                "career": "직업에서는 실무 성과가 권한을 조정하거나 공식 질서와 충돌한다. 결과가 있으면 개혁이고, 없으면 반발로 보인다.",
                "relationship": "관계에서는 표현의 강도가 약속과 신뢰를 흔든다. 문제 제기가 필요해도 말의 방식이 중요하다.",
                "marriage": "결혼에서는 생활 방식의 자유와 배우자 역할 기준이 충돌할 수 있다. 표현이 강하면 사소한 문제가 크게 번진다.",
            },
            "resource_controls_output": {
                "money": "재물에서는 준비, 문서, 검토가 결과물의 수입화를 늦출 수 있다. 다만 기준이 맞으면 품질과 안정성을 높인다.",
                "career": "직업에서는 공부와 절차가 실무 속도를 제어한다. 깊이는 생기지만 결과물을 늦게 내놓기 쉽다.",
                "relationship": "관계에서는 생각과 해석이 표현보다 앞선다. 마음은 있어도 말이 늦어 오해가 생길 수 있다.",
                "marriage": "결혼에서는 안정 확인과 가족 절차가 생활 표현보다 먼저 온다. 신중함이 과하면 거리감이 생긴다.",
            },
            "officer_controls_peer": {
                "money": "재물에서는 규칙과 책임이 사람 사이의 몫 문제를 정리한다. 계약과 기준이 있으면 분쟁을 줄인다.",
                "career": "직업에서는 권한과 규칙이 경쟁 구도를 제어한다. 역할 범위가 분명할수록 성과가 안정된다.",
                "relationship": "관계에서는 책임 기준이 주도권 싸움을 낮춘다. 단, 기준이 지나치면 관계가 딱딱해진다.",
                "marriage": "결혼에서는 책임 분담과 생활 규칙이 가족 갈등을 정리한다. 일방적 통제는 부담이 된다.",
            },
        }
        if pair_category in by_pair and domain in by_pair[pair_category]:
            return by_pair[pair_category][domain]
        if relation == "same_group":
            return {
                "money": "재물에서는 같은 기운이 반복되어 강점과 병이 함께 커진다. 과하면 한쪽으로 몰려 손실이 생긴다.",
                "career": "직업에서는 같은 역할이 반복되어 전문성이 생기지만, 과하면 융통성이 줄어든다.",
                "relationship": "관계에서는 같은 반응이 반복되어 매력이 선명해지지만, 피로 지점도 분명해진다.",
                "marriage": "결혼에서는 같은 생활 태도가 반복되어 안정과 고집이 함께 드러난다.",
            }[domain]
        return {
            "money": "재물에서는 두 작용의 순서가 수입, 보존, 분배의 결론을 가른다.",
            "career": "직업에서는 어느 작용이 먼저 발동되는지가 역할, 권한, 평가의 방향을 가른다.",
            "relationship": "관계에서는 두 작용의 순서가 거리, 신뢰, 주도권을 다르게 만든다.",
            "marriage": "결혼에서는 생활 기준과 책임 범위가 어느 쪽에서 먼저 흔들리는지 본다.",
        }[domain]

    return {
        "money": sentence("money", "재물", life_domain_conclusion("money")),
        "career": sentence("career", "직업", life_domain_conclusion("career")),
        "relationship": sentence("relationship", "관계", life_domain_conclusion("relationship")),
        "marriage": sentence("marriage", "결혼과 가정", life_domain_conclusion("marriage")),
        "personality": sentence("personality", "성향", personality_conclusion()),
        "timing": (
            f"대운·세운에서 {_subject_form(first_label)} 먼저 오면 {_subject_form(TEN_GOD_OPERATION_FACE[first_ten_god]['timing'])} 먼저 드러난다. "
            f"{_subject_form(second_label)} 뒤따르면 {_euro_form(TEN_GOD_OPERATION_FACE[second_ten_god]['timing'])} 결론이 이동한다. "
            f"반대로 {_subject_form(second_label)} 먼저 오면 같은 조합이라도 시작점이 달라진다."
        ),
    }


DUAL_EVENT_CHAIN_TAILS = {
    "constructive_chain": "두 작용이 이어지면 기회가 결과로 굳어지는 방향이 강하다.",
    "supportive_chain": "중심 작용을 보조하는 힘이 붙어 현실 성과가 두터워진다.",
    "medicine_chain": "한쪽의 부담을 다른 쪽이 제어하면서 병약 조절이 성립한다.",
    "mediated_tension_chain": "두 작용 사이의 긴장은 격국 중심이 매개될 때 성과로 정리된다.",
    "conditional_chain": "순서와 위치가 맞을 때만 성과로 이어지고, 어긋나면 부담이 먼저 드러난다.",
    "mixed_chain": "기회와 부담이 함께 있으므로 월령과 투출·통근이 결론을 가른다.",
    "risk_chain": "손실, 충돌, 책임 문제가 먼저 커질 수 있으므로 중심 작용을 제어해야 한다.",
    "compounded_burden_chain": "부담이 겹쳐 하나의 생활 사건으로 커지기 쉽다.",
    "disease_chain": "격국 중심을 흔드는 병증으로 작동할 가능성을 먼저 본다.",
}


def _dual_event_manifestations(
    *,
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
    exact_pair_name: str,
    exact_pair_category: str,
    first_to_second_relation: str,
    chain_grade: str,
    domain_priority: list[str],
    first_then_second_activation: str,
    second_then_first_activation: str,
) -> dict[str, str]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    relation_label = {
        "first_generates_second": "상생",
        "second_generates_first": "역상생",
        "first_controls_second": "상극",
        "second_controls_first": "역상극",
        "same_group": "동류 중첩",
    }.get(first_to_second_relation, "간접 결합")
    tail = DUAL_EVENT_CHAIN_TAILS.get(chain_grade, "강약과 위치에 따라 사건의 방향이 달라진다.")
    center_topic = _topic_form(f"{pattern_label}의 {pattern_center}")
    def face(ten_god: str, domain: str) -> str:
        return TEN_GOD_DOMAIN_FACE.get(ten_god, {}).get(domain, TEN_GOD_OPERATION_FACE[ten_god]["action"])

    def sentence(domain: str, label: str) -> str:
        first_face = face(first_ten_god, domain)
        second_face = face(second_ten_god, domain)
        if first_face == second_face:
            event_face = f"{_subject_form(first_face)} 반복되어"
        else:
            event_face = f"{_and_form(first_face)} {_subject_form(second_face)} 결합해"
        return (
            f"운에서 {_subject_form(exact_pair_name)} 발동하면 {center_topic} {label} 영역에서 {event_face} 현실 사건을 만든다. "
            f"{_and_form(first_label)} {_subject_form(second_label)} {relation_label} 관계로 묶이며, {tail}"
        )

    return {
        "money": sentence("money", "재물"),
        "career": sentence("career", "직업"),
        "relationship": sentence("relationship", "관계"),
        "marriage": sentence("marriage", "결혼과 가정"),
        "personality": sentence("personality", "성향"),
        "luck_activation": _dual_luck_activation(
            pattern=pattern,
            first_label=first_label,
            second_label=second_label,
            exact_pair_name=exact_pair_name,
            exact_pair_category=exact_pair_category,
            first_to_second_relation=first_to_second_relation,
            chain_grade=chain_grade,
            domain_priority=domain_priority,
        ),
        "first_then_second": first_then_second_activation,
        "second_then_first": second_then_first_activation,
    }


def _interaction_role_phrase(rule) -> str:
    label = TEN_GOD_LABEL[rule.acting_ten_god]
    role = ROLE_GRADE_INTERACTION_PHRASE.get(
        rule.role_grade,
        "월령, 격국, 강약, 위치에 따라 작용 방향이 갈린다.",
    )
    return f"{label}: {role} {_euro_form(rule.pattern_effect_state)} 드러난다."


def _interaction_disease_controller(
    *,
    first_label: str,
    second_label: str,
    first_to_second_relation: str,
    chain_grade: str,
) -> str:
    if first_to_second_relation == "first_controls_second":
        if chain_grade in {"medicine_chain", "conditional_chain", "mediated_tension_chain"}:
            return f"{_subject_form(first_label)} {second_label}의 과잉을 제어하면 병이 약으로 바뀐다."
        return f"{_subject_form(first_label)} {_object_form(second_label)} 강하게 치면 필요한 작용까지 끊을 수 있다."
    if first_to_second_relation == "second_controls_first":
        if chain_grade in {"medicine_chain", "conditional_chain", "mediated_tension_chain"}:
            return f"{_subject_form(second_label)} {first_label}의 과잉을 제어하면 병이 약으로 바뀐다."
        return f"{_subject_form(second_label)} {_object_form(first_label)} 강하게 치면 앞 작용이 손상될 수 있다."
    if first_to_second_relation == "first_generates_second":
        return f"{_subject_form(first_label)} {_euro_form(second_label)} 힘을 넘기므로 앞 작용의 결과가 뒤 작용에서 결론을 얻는다."
    if first_to_second_relation == "second_generates_first":
        return f"{_subject_form(second_label)} {_object_form(first_label)} 받치므로 뒤 작용이 앞 작용의 근거가 된다."
    return "같은 계열의 힘이 겹치므로 성격은 선명해지지만 과하면 한쪽으로 몰린다."


def _interaction_event_targets(
    *,
    first_group: str,
    second_group: str,
    domain_priority: list[str],
) -> str:
    targets: list[str] = []
    for domain in domain_priority[:3]:
        targets.extend(DOMAIN_EVENT_TARGETS.get(domain, (domain,)))
    targets.extend(GROUP_EVENT_TARGETS.get(first_group, (first_group,)))
    targets.extend(GROUP_EVENT_TARGETS.get(second_group, (second_group,)))
    unique_targets = list(dict.fromkeys(str(target) for target in targets if str(target)))
    return ", ".join(unique_targets[:8])


def _dual_interaction_judgment(
    *,
    pattern: str,
    first_rule,
    second_rule,
    first_to_second_relation: str,
    chain_grade: str,
    combination_resolution_state: str,
    exact_pair_name: str,
    exact_pair_effect: str,
    exact_pair_risk: str,
    primary_actor: str,
    secondary_actor: str,
    domain_priority: list[str],
    first_then_second_activation: str,
    second_then_first_activation: str,
) -> dict[str, str]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]
    primary_label = TEN_GOD_LABEL.get(primary_actor, primary_actor)
    secondary_label = TEN_GOD_LABEL.get(secondary_actor, secondary_actor)
    relation_label = DUAL_RELATION_LABELS.get(first_to_second_relation, "두 십신이 간접적으로 결합한다")
    resolution_label = CHAIN_RESOLUTION_LABELS.get(combination_resolution_state, combination_resolution_state)
    event_targets = _interaction_event_targets(
        first_group=first_rule.acting_group,
        second_group=second_rule.acting_group,
        domain_priority=domain_priority,
    )
    return {
        "pattern_center": f"{pattern_label}은 {_object_form(pattern_center)} 중심으로 판단한다.",
        "pair_relation": f"{exact_pair_name}: {relation_label}.",
        "first_role": _interaction_role_phrase(first_rule),
        "second_role": _interaction_role_phrase(second_rule),
        "pattern_outcome": f"이 조합은 {resolution_label}로 판정한다. {exact_pair_effect}",
        "disease_or_medicine": _interaction_disease_controller(
            first_label=first_label,
            second_label=second_label,
            first_to_second_relation=first_to_second_relation,
            chain_grade=chain_grade,
        ),
        "risk_axis": exact_pair_risk,
        "primary_secondary": f"중심 작용은 {primary_label}, 보조 작용은 {_euro_form(secondary_label)} 잡는다.",
        "event_targets": f"현실에서는 {event_targets} 문제로 드러난다.",
        "sequence_first_then_second": first_then_second_activation,
        "sequence_second_then_first": second_then_first_activation,
    }


def _dual_visibility_interaction(
    *,
    pattern: str,
    first_rule,
    second_rule,
    exact_pair_name: str,
    first_to_second_relation: str,
) -> dict[str, str]:
    pattern_label = PATTERN_LENS[pattern]["label"]
    pattern_center = PATTERN_LENS[pattern]["center"]
    first_label = TEN_GOD_LABEL[first_rule.acting_ten_god]
    second_label = TEN_GOD_LABEL[second_rule.acting_ten_god]
    first_nuance = TEN_GOD_EXACT_NUANCE[first_rule.acting_ten_god]
    second_nuance = TEN_GOD_EXACT_NUANCE[second_rule.acting_ten_god]
    if first_to_second_relation == "first_generates_second":
        relation_phrase = "앞 작용이 뒤 작용으로 힘을 넘기는 조합"
    elif first_to_second_relation == "second_generates_first":
        relation_phrase = "뒤 작용이 앞 작용의 근거를 받치는 조합"
    elif first_to_second_relation == "first_controls_second":
        relation_phrase = "앞 작용이 뒤 작용을 제어하는 조합"
    elif first_to_second_relation == "second_controls_first":
        relation_phrase = "뒤 작용이 앞 작용을 제어하는 조합"
    elif first_to_second_relation == "same_group":
        relation_phrase = "같은 계열의 힘이 중첩되는 조합"
    else:
        relation_phrase = "두 작용이 간접적으로 얽히는 조합"
    center = f"{pattern_label}의 {pattern_center}"
    return {
        "protrusion": (
            f"{_subject_form(exact_pair_name)} 천간에 함께 드러나면 {_subject_form(relation_phrase)} 외부 선택, 평가, 계약에서 바로 보인다. "
            f"한쪽만 투출하면 투출한 십신이 사건의 입구가 되고, 숨은 십신은 결론을 늦게 만든다."
        ),
        "hidden_stem": (
            f"{_subject_form(exact_pair_name)} 지장간에 깔리면 겉으로는 약해 보여도 생활 조건 안에 씨앗이 남는다. "
            "대운·세운이 그 지지를 건드릴 때 돈, 직장, 관계, 문서 문제가 현실 사건으로 올라온다."
        ),
        "rooting": (
            f"{_and_form(first_label)} {_subject_form(second_label)} 통근하면 {center} 안에서 오래 버티는 작용이 된다. "
            "월지나 일지에 뿌리가 있으면 판단보다 생활 조건에서 먼저 드러난다."
        ),
        "unrooted": (
            f"{_subject_form(exact_pair_name)} 뿌리 없이 천간에만 있으면 말, 계획, 직책, 계약처럼 겉의 사건은 생기지만 지속력은 약하다. "
            "운에서 뿌리가 들어올 때 비로소 실제 결과가 붙는다."
        ),
        "position": (
            f"월주에 가까우면 {center}의 성립 조건으로 먼저 판단하고, 일지에 가까우면 배우자·생활 기반에서 체감된다. "
            "시주에 있으면 결과와 후반 성취로 늦게 드러난다."
        ),
        "branch_interaction": (
            "합은 조합을 묶어 사건을 모으고, 충은 숨은 작용을 움직인다. "
            "형·파·해는 좋은 조합도 압박과 손상을 거쳐 드러나게 하므로 월령과 격국의 필요성을 먼저 판정한다."
        ),
        "component_faces": (
            f"앞 십신은 {first_nuance}, 뒤 십신은 {second_nuance}의 얼굴을 가진다. "
            f"따라서 {_topic_form(exact_pair_name)} 두 성분을 나열하지 않고 어느 쪽이 드러나고 어느 쪽이 받치는지를 본다."
        ),
    }


def _conditions(first_rule, second_rule, first_to_second_relation: str, chain_grade: str) -> tuple[list[str], list[str]]:
    favorable = [
        "first_ten_god_present",
        "second_ten_god_present",
        *first_rule.favorable_conditions[:3],
        *second_rule.favorable_conditions[:3],
    ]
    unfavorable = [
        "first_or_second_ten_god_weak",
        *first_rule.unfavorable_conditions[:3],
        *second_rule.unfavorable_conditions[:3],
    ]
    if first_to_second_relation in {"first_generates_second", "second_generates_first"}:
        favorable.append("dual_action_has_generation_path")
    if first_to_second_relation in {"first_controls_second", "second_controls_first"}:
        unfavorable.append("dual_action_has_control_tension")
        if chain_grade == "medicine_chain":
            favorable.append("control_tension_can_work_as_medicine")
    if chain_grade in {"risk_chain", "compounded_burden_chain"}:
        unfavorable.append("dual_action_amplifies_pattern_pressure")
    if chain_grade in {"constructive_chain", "supportive_chain"}:
        favorable.append("dual_action_supports_pattern_success")
    return list(dict.fromkeys(favorable)), list(dict.fromkeys(unfavorable))


def _build_rule(pattern: str, first_ten_god: str, second_ten_god: str) -> GyeokgukDualTenGodActionRule:
    first_rule = gyeokguk_ten_god_action_rule(pattern, first_ten_god)
    second_rule = gyeokguk_ten_god_action_rule(pattern, second_ten_god)
    pattern_ten_god = PATTERN_CENTER_BY_PATTERN[pattern]
    pattern_group = TEN_GOD_GROUPS[pattern_ten_god]
    first_group = TEN_GOD_GROUPS[first_ten_god]
    second_group = TEN_GOD_GROUPS[second_ten_god]
    first_to_second_relation = _relation_between(first_group, second_group)
    sequence_key = _sequence_key(
        first_relation_to_pattern=first_rule.relation_to_pattern,
        second_relation_to_pattern=second_rule.relation_to_pattern,
        first_to_second_relation=first_to_second_relation,
        first_grade=first_rule.role_grade,
        second_grade=second_rule.role_grade,
    )
    pattern_center_bridge = _pattern_center_bridge_profile(pattern, first_ten_god, second_ten_god)
    chain_grade = _chain_grade(sequence_key, first_rule.role_grade, second_rule.role_grade)
    chain_grade = _bridge_adjusted_chain_grade(
        chain_grade,
        pattern_center_bridge,
        first_rule.role_grade,
        second_rule.role_grade,
    )
    chain_grade = _exact_pair_adjusted_chain_grade(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
    )
    chain_nature = _chain_nature(sequence_key, chain_grade)
    chain_nature = _bridge_adjusted_chain_nature(chain_nature, pattern_center_bridge)
    exact_pair = _exact_pair_profile(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
    )
    exact_pair = _bridge_adjusted_pair_profile(exact_pair, pattern_center_bridge)
    classical_tags = _dual_classical_action_tags(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        category=exact_pair["category"],
        name=exact_pair["name"],
        bridge_key=str(pattern_center_bridge.get("key", "")) if pattern_center_bridge else "",
    )
    first_single_classical_tags = [
        str(code).split(":", 1)[1]
        for code in first_rule.basis_codes
        if str(code).startswith("gyeokguk_single_classical_action:")
    ]
    second_single_classical_tags = [
        str(code).split(":", 1)[1]
        for code in second_rule.basis_codes
        if str(code).startswith("gyeokguk_single_classical_action:")
    ]
    pattern_effect = _pattern_effect(pattern, first_ten_god, second_ten_god, chain_grade)
    if pattern_center_bridge:
        pattern_effect = f"{pattern_effect} {pattern_center_bridge['effect']}"
    pattern_combination_state = _pattern_combination_state(chain_grade, sequence_key)
    combination_resolution_state = _chain_resolution_state(chain_grade)
    combination_resolution_logic = _dual_resolution_logic(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
        sequence_key=sequence_key,
        exact_pair_name=exact_pair["name"],
    )
    combination_resolution_logic = _bridge_adjusted_resolution_logic(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        combination_resolution_logic=combination_resolution_logic,
        pattern_center_bridge=pattern_center_bridge,
    )
    combination_resolution_logic = _with_dual_pattern_context(
        combination_resolution_logic, pattern, first_ten_god, second_ten_god
    )
    primary_actor, secondary_actor = _primary_secondary(first_rule, second_rule, chain_grade, pattern)
    actor_hierarchy_logic = _actor_hierarchy_logic(
        pattern=pattern,
        first_rule=first_rule,
        second_rule=second_rule,
        primary_actor=primary_actor,
        secondary_actor=secondary_actor,
        chain_grade=chain_grade,
        sequence_key=sequence_key,
        first_to_second_relation=first_to_second_relation,
    )
    actor_hierarchy_logic = _with_dual_pattern_context(actor_hierarchy_logic, pattern, first_ten_god, second_ten_god)
    disease_medicine_logic = _disease_medicine_logic(
        pattern,
        first_rule,
        second_rule,
        first_to_second_relation,
        sequence_key,
        chain_grade,
        exact_pair["name"],
    )
    if pattern_center_bridge:
        disease_medicine_logic = f"{disease_medicine_logic} {pattern_center_bridge['risk']}"
    disease_medicine_logic = _with_dual_pattern_context(disease_medicine_logic, pattern, first_ten_god, second_ten_god)
    first_then_second_activation, second_then_first_activation = _sequence_activation(
        pattern=pattern,
        first_rule=first_rule,
        second_rule=second_rule,
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
        pattern_center_bridge=pattern_center_bridge,
    )
    timing_activation = _dual_timing_activation(pattern, first_rule, second_rule, chain_grade, exact_pair["category"])
    if pattern_center_bridge:
        timing_activation = f"{timing_activation} {pattern_center_bridge['timing']}"
    timing_activation = _with_dual_pattern_context(timing_activation, pattern, first_ten_god, second_ten_god)
    domain_priority = _dual_domain_priority(pattern, first_rule, second_rule, chain_grade)
    activation_order_profile = _activation_order_profile(
        pattern=pattern,
        first_rule=first_rule,
        second_rule=second_rule,
        chain_grade=chain_grade,
        combination_resolution_state=combination_resolution_state,
        first_then_second_activation=first_then_second_activation,
        second_then_first_activation=second_then_first_activation,
        domain_priority=domain_priority,
    )
    interaction_judgment = _dual_interaction_judgment(
        pattern=pattern,
        first_rule=first_rule,
        second_rule=second_rule,
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
        combination_resolution_state=combination_resolution_state,
        exact_pair_name=exact_pair["name"],
        exact_pair_effect=exact_pair["effect"],
        exact_pair_risk=exact_pair["risk"],
        primary_actor=primary_actor,
        secondary_actor=secondary_actor,
        domain_priority=domain_priority,
        first_then_second_activation=first_then_second_activation,
        second_then_first_activation=second_then_first_activation,
    )
    visibility_interaction = _dual_visibility_interaction(
        pattern=pattern,
        first_rule=first_rule,
        second_rule=second_rule,
        exact_pair_name=exact_pair["name"],
        first_to_second_relation=first_to_second_relation,
    )
    event_manifestations = _dual_event_manifestations(
        pattern=pattern,
        first_ten_god=first_ten_god,
        second_ten_god=second_ten_god,
        exact_pair_name=exact_pair["name"],
        exact_pair_category=exact_pair["category"],
        first_to_second_relation=first_to_second_relation,
        chain_grade=chain_grade,
        domain_priority=domain_priority,
        first_then_second_activation=first_then_second_activation,
        second_then_first_activation=second_then_first_activation,
    )
    favorable, unfavorable = _conditions(first_rule, second_rule, first_to_second_relation, chain_grade)
    rule_key = f"{pattern}:{first_ten_god}+{second_ten_god}"
    pattern_label = str(PATTERN_LENS[pattern]["label"])
    pattern_center = str(PATTERN_LENS[pattern]["center"])
    first_label = TEN_GOD_LABEL[first_ten_god]
    second_label = TEN_GOD_LABEL[second_ten_god]
    success_logic = (
        f"{pattern_label}: {_topic_form(exact_pair['name'])} {_and_form(first_label)} {second_label}의 생극이 "
        f"{_object_form(pattern_center)} 어떻게 살리거나 제어하는지로 판단한다. "
        f"구성 작용으로는 {_and_form(first_rule.action_nature)} {_subject_form(second_rule.action_nature)} 포함되지만, 결론은 두 작용의 결합으로 본다. "
        f"{exact_pair['effect']} {actor_hierarchy_logic} {disease_medicine_logic}"
    )
    success_logic = _with_dual_pattern_context(success_logic, pattern, first_ten_god, second_ten_god)
    failure_logic = (
        f"{pattern_label}: {_topic_form(exact_pair['name'])} 월령에서 불필요하거나 강약·위치가 어긋나면 "
        f"{_subject_form(pattern_center)} 복합적으로 흐려진다. "
        f"{_and_form(first_label)} {second_label}의 결합은 어느 쪽이 먼저 강해지는지에 따라 병의 입구가 달라진다. "
        f"{exact_pair['risk']} {first_rule.excess_disease} {second_rule.excess_disease}"
    )
    failure_logic = _with_dual_pattern_context(failure_logic, pattern, first_ten_god, second_ten_god)
    bridge_basis_codes: list[str] = []
    if pattern_center_bridge:
        bridge_basis_codes = [
            f"gyeokguk_dual_pattern_center_bridge:{pattern_center_bridge['key']}",
            f"gyeokguk_dual_pattern_center_bridge_direction:{pattern_center_bridge['direction']}",
            f"gyeokguk_dual_pattern_center_bridge_pattern:{pattern}",
        ]
    pair_identity_basis_codes: list[str] = []
    if exact_pair.get("direct_name"):
        pair_identity_basis_codes.append(f"gyeokguk_dual_direct_pair_name:{exact_pair['direct_name']}")
    if exact_pair.get("direct_category"):
        pair_identity_basis_codes.append(f"gyeokguk_dual_direct_pair_category:{exact_pair['direct_category']}")
    if pattern_center_bridge and pattern_center_bridge.get("mediated_name"):
        pair_identity_basis_codes.append(f"gyeokguk_dual_mediated_pair_name:{exact_pair['name']}")
    if pattern_center_bridge and pattern_center_bridge.get("mediated_category"):
        pair_identity_basis_codes.append(
            f"gyeokguk_dual_mediated_pair_category:{pattern_center_bridge['mediated_category']}"
        )
    return GyeokgukDualTenGodActionRule(
        rule_key=rule_key,
        pattern=pattern,
        pattern_ten_god=pattern_ten_god,
        pattern_group=pattern_group,
        first_ten_god=first_ten_god,
        first_group=first_group,
        second_ten_god=second_ten_god,
        second_group=second_group,
        first_relation_to_pattern=first_rule.relation_to_pattern,
        second_relation_to_pattern=second_rule.relation_to_pattern,
        first_to_second_relation=first_to_second_relation,
        pattern_center_bridge=dict(pattern_center_bridge),
        sequence_key=sequence_key,
        chain_grade=chain_grade,
        chain_nature=chain_nature,
        pattern_effect=pattern_effect,
        combination_resolution_state=combination_resolution_state,
        combination_resolution_logic=combination_resolution_logic,
        exact_pair_key=exact_pair["key"],
        exact_pair_category=exact_pair["category"],
        exact_pair_name=exact_pair["name"],
        exact_pair_effect=exact_pair["effect"],
        exact_pair_risk=exact_pair["risk"],
        exact_pair_timing=exact_pair["timing"],
        pattern_combination_state=pattern_combination_state,
        primary_actor=primary_actor,
        secondary_actor=secondary_actor,
        actor_hierarchy_logic=actor_hierarchy_logic,
        disease_medicine_logic=disease_medicine_logic,
        first_then_second_activation=first_then_second_activation,
        second_then_first_activation=second_then_first_activation,
        timing_activation=timing_activation,
        activation_order_profile=activation_order_profile,
        event_manifestations=event_manifestations,
        interaction_judgment=interaction_judgment,
        visibility_interaction=visibility_interaction,
        classical_action_tags=list(classical_tags),
        first_single_classical_action_tags=list(first_single_classical_tags),
        second_single_classical_action_tags=list(second_single_classical_tags),
        domain_priority=domain_priority,
        success_logic=success_logic,
        failure_logic=failure_logic,
        domain_projections=_dual_domain_projections(
            pattern=pattern,
            first_ten_god=first_ten_god,
            second_ten_god=second_ten_god,
            chain_grade=chain_grade,
            sequence_key=sequence_key,
            exact_pair_name=exact_pair["name"],
            direct_pair_name=str(exact_pair.get("direct_name", "")),
        ),
        favorable_conditions=favorable,
        unfavorable_conditions=unfavorable,
        judgment_order=list(GYEOKGUK_ACTION_JUDGMENT_ORDER),
        basis_codes=[
            *gyeokguk_action_judgment_basis_codes("gyeokguk_dual"),
            f"gyeokguk_dual_pattern:{pattern}",
            f"gyeokguk_dual_first:{first_ten_god}",
            f"gyeokguk_dual_second:{second_ten_god}",
            f"gyeokguk_dual_first_exact_ten_god:{first_ten_god}",
            f"gyeokguk_dual_second_exact_ten_god:{second_ten_god}",
            *(
                f"gyeokguk_dual_first_exact_profile_domain:{domain}"
                for domain in TEN_GOD_EXACT_ACTION_PROFILE[first_ten_god]["domains"]
            ),
            *(
                f"gyeokguk_dual_second_exact_profile_domain:{domain}"
                for domain in TEN_GOD_EXACT_ACTION_PROFILE[second_ten_god]["domains"]
            ),
            f"gyeokguk_dual_relation:{first_to_second_relation}",
            f"gyeokguk_dual_sequence:{sequence_key}",
            f"gyeokguk_dual_chain_grade:{chain_grade}",
            f"gyeokguk_dual_combination_state:{pattern_combination_state}",
            f"gyeokguk_dual_resolution:{combination_resolution_state}",
            f"gyeokguk_dual_actor_hierarchy:{primary_actor}>{secondary_actor}",
            "gyeokguk_dual_activation_order_profile:daeun_seun_sequence",
            f"gyeokguk_dual_activation_order:first_then_second:{first_ten_god}>{second_ten_god}",
            f"gyeokguk_dual_activation_order:second_then_first:{second_ten_god}>{first_ten_god}",
            *(f"gyeokguk_dual_event_manifestation:{domain}" for domain in event_manifestations),
            *(f"gyeokguk_dual_visibility_interaction:{key}" for key in visibility_interaction),
            f"gyeokguk_dual_exact_pair:{exact_pair['key']}",
            f"gyeokguk_dual_exact_pair_name:{exact_pair['name']}",
            f"gyeokguk_dual_exact_pair_category:{exact_pair['category']}",
            f"gyeokguk_dual_exact_pair_refinement:{exact_pair['refinement_key']}",
            f"gyeokguk_dual_pair_lens:{exact_pair['lens_key']}",
            f"gyeokguk_dual_pair_lens_type:{exact_pair['lens_type']}",
            *pair_identity_basis_codes,
            *bridge_basis_codes,
            *(f"gyeokguk_dual_first_single_classical_action:{tag}" for tag in first_single_classical_tags),
            *(f"gyeokguk_dual_second_single_classical_action:{tag}" for tag in second_single_classical_tags),
            *(f"gyeokguk_dual_classical_action:{tag}" for tag in classical_tags),
            *classical_action_mechanic_codes(classical_tags, prefix="gyeokguk_dual"),
            *(f"gyeokguk_dual_domain:{domain}" for domain in domain_priority[:3]),
        ],
    )


def _build_dictionary() -> dict[str, dict[str, dict[str, GyeokgukDualTenGodActionRule]]]:
    return {
        pattern: {
            first_ten_god: {
                second_ten_god: _build_rule(pattern, first_ten_god, second_ten_god)
                for second_ten_god in TEN_GODS
            }
            for first_ten_god in TEN_GODS
        }
        for pattern in GYEOKGUK_TEN_GOD_ACTIONS
    }


GYEOKGUK_DUAL_TEN_GOD_ACTIONS = _build_dictionary()


def gyeokguk_dual_ten_god_action_rule(
    pattern: str,
    first_ten_god: str,
    second_ten_god: str,
) -> GyeokgukDualTenGodActionRule:
    return GYEOKGUK_DUAL_TEN_GOD_ACTIONS[pattern][first_ten_god][second_ten_god]


def _presence_values(ten_god_profile: TenGodProfile, ten_god: str) -> tuple[float, float, int]:
    visible = float(ten_god_profile.visible_counts.get(ten_god, 0.0) or 0.0)
    hidden = float(ten_god_profile.hidden_counts.get(ten_god, 0.0) or 0.0)
    score = max(0, min(100, round(visible * 32 + hidden * 22)))
    return visible, hidden, score


def _pair_presence_state(first_score: int, second_score: int) -> str:
    if first_score >= 40 and second_score >= 40:
        return "dual_action_clear"
    if first_score >= 25 and second_score >= 25:
        return "dual_action_present"
    if first_score > 0 and second_score > 0:
        return "dual_action_weak"
    return "dual_action_not_present"


def _month_fit_state(rule: GyeokgukDualTenGodActionRule, month_governance_profile: MonthGovernanceProfile) -> str:
    first_fit = month_governance_profile.role_fits.get(rule.first_group)
    second_fit = month_governance_profile.role_fits.get(rule.second_group)
    first_status = str(getattr(first_fit, "status", "") or "")
    second_status = str(getattr(second_fit, "status", "") or "")
    if first_status in FIT_PRESSURE_STATES and second_status in FIT_PRESSURE_STATES:
        return "both_pressure_by_month_command"
    if first_status in FIT_SUPPORT_STATES and second_status in FIT_SUPPORT_STATES:
        return "both_supported_by_month_command"
    if first_status in FIT_PRESSURE_STATES or second_status in FIT_PRESSURE_STATES:
        return "one_side_pressure_by_month_command"
    if first_status or second_status:
        return "mixed_or_neutral_by_month_command"
    return "not_evaluated_by_month_command"


def _match_verdict(rule: GyeokgukDualTenGodActionRule, presence_state: str, month_fit_state: str) -> str:
    if presence_state == "dual_action_not_present":
        return "not_activated"
    if rule.chain_grade in {"risk_chain", "compounded_burden_chain"}:
        return "risk_dual_action"
    if month_fit_state in {"both_pressure_by_month_command", "one_side_pressure_by_month_command"}:
        return "conditional_dual_action"
    if rule.chain_grade in {"constructive_chain", "supportive_chain", "medicine_chain"}:
        return "constructive_dual_action"
    if rule.chain_grade == "conditional_chain":
        return "conditional_dual_action"
    return ROLE_GRADE_VERDICT.get(rule.chain_grade, "observed_dual_action")


def _dual_functional_role(rule: GyeokgukDualTenGodActionRule, verdict: str) -> str:
    if verdict == "not_activated":
        return "inactive"
    if verdict == "risk_dual_action":
        return "adverse_god"
    if verdict == "constructive_dual_action":
        if rule.chain_grade == "medicine_chain":
            return "rescuing_god"
        return "supporting_god"
    return "conditional_god"


def _dual_activation_context(presence_state: str, month_fit_state: str, chain_grade: str) -> str:
    if presence_state == "dual_action_clear":
        base = "두 십신이 모두 분명해 원국 안에서 결합 작용을 읽을 수 있다."
    elif presence_state == "dual_action_present":
        base = "두 십신이 함께 존재하나 강약과 위치에 따라 작용 정도가 갈린다."
    elif presence_state == "dual_action_weak":
        base = "두 십신이 약하게 연결되어 운에서 자극될 때 사건성이 커진다."
    else:
        base = "원국에서는 이중 작용이 직접 활성화되지 않는다."
    if month_fit_state == "both_supported_by_month_command":
        return f"{base} 월령 기준에서도 두 작용을 쓸 수 있다."
    if month_fit_state == "both_pressure_by_month_command":
        return f"{base} 다만 월령 기준으로는 파격과 부담 가능성을 우선 점검한다."
    if month_fit_state == "one_side_pressure_by_month_command":
        return f"{base} 한쪽은 쓸 수 있으나 다른 한쪽은 부담으로 작용할 수 있다."
    if chain_grade == "medicine_chain":
        return f"{base} 병약 관계가 있으므로 제어하는 쪽의 힘을 중점적으로 본다."
    return base


def _combine_context(first_context: dict[str, object], second_context: dict[str, object]) -> dict[str, object]:
    score_delta = round((int(first_context["score_delta"]) + int(second_context["score_delta"])) / 2)
    position = {
        "first": dict(first_context["position"]),
        "second": dict(second_context["position"]),
    }
    branch = {
        "first": dict(first_context["branch_relation"]),
        "second": dict(second_context["branch_relation"]),
    }
    return {
        "score_delta": max(-20, min(24, score_delta)),
        "strength_label": " / ".join(
            item
            for item in [
                str(first_context["strength"].get("label", "")),
                str(second_context["strength"].get("label", "")),
            ]
            if item
        ),
        "climate_label": " / ".join(
            item
            for item in [
                str(first_context["climate"].get("label", "")),
                str(second_context["climate"].get("label", "")),
            ]
            if item
        ),
        "position": position,
        "branch_relation": branch,
        "basis_codes": [
            *list(first_context["basis_codes"]),
            *list(second_context["basis_codes"]),
        ],
        "counter_signals": [
            *list(first_context["counter_signals"]),
            *list(second_context["counter_signals"]),
        ],
    }


def _position_note(position: dict[str, object]) -> str:
    first = dict(position.get("first", {}) or {})
    second = dict(position.get("second", {}) or {})
    first_grade = str(first.get("grade", "") or "")
    second_grade = str(second.get("grade", "") or "")
    visible_count = len(list(first.get("visible_positions", []) or [])) + len(list(second.get("visible_positions", []) or []))
    branch_main_count = len(list(first.get("branch_main_positions", []) or [])) + len(list(second.get("branch_main_positions", []) or []))
    hidden_count = len(list(first.get("hidden_positions", []) or [])) + len(list(second.get("hidden_positions", []) or []))
    if "month_position_reality" in {first_grade, second_grade}:
        return "월지·월간 쪽에서 현실 작용이 강하다."
    if visible_count:
        return "천간에 드러나 외부 사건과 판단으로 바로 보인다."
    if branch_main_count:
        return "지지 본기에서 작용해 생활 조건과 현실 기반으로 나타난다."
    if hidden_count:
        return "지장간에 숨어 있어 특정 운에서 발동될 때 사건성이 커진다."
    return "위치상 작용은 약하거나 아직 뚜렷하지 않다."


def _protrusion_note(position: dict[str, object]) -> str:
    first = dict(position.get("first", {}) or {})
    second = dict(position.get("second", {}) or {})
    visible_positions = set(list(first.get("visible_positions", []) or [])) | set(
        list(second.get("visible_positions", []) or [])
    )
    if "month" in visible_positions:
        return "월간 투출이 있어 격국의 요구가 사회적 사건으로 바로 드러난다."
    if visible_positions:
        return "천간에 드러난 작용이 있어 외부 평가와 선택에서 먼저 보인다."
    return "천간 투출은 약하므로 지지와 지장간의 발동 조건을 더 본다."


def _rooting_note(position: dict[str, object]) -> str:
    first = dict(position.get("first", {}) or {})
    second = dict(position.get("second", {}) or {})
    branch_main_positions = set(list(first.get("branch_main_positions", []) or [])) | set(
        list(second.get("branch_main_positions", []) or [])
    )
    hidden_positions = set(list(first.get("hidden_positions", []) or [])) | set(
        list(second.get("hidden_positions", []) or [])
    )
    if "month" in branch_main_positions:
        return "월지 본기에 통근해 계절의 힘을 직접 받는다."
    if branch_main_positions:
        return "지지 본기에 닿아 현실에서 이어지는 힘이 있다."
    if hidden_positions:
        return "지장간에 뿌리가 있어 대운·세운에서 자극될 때 살아난다."
    return "통근은 약하므로 오래 유지되는 힘보다 발동 조건을 더 본다."


def _hidden_stem_note(position: dict[str, object]) -> str:
    first = dict(position.get("first", {}) or {})
    second = dict(position.get("second", {}) or {})
    hidden_count = len(list(first.get("hidden_positions", []) or [])) + len(list(second.get("hidden_positions", []) or []))
    branch_main_count = len(list(first.get("branch_main_positions", []) or [])) + len(list(second.get("branch_main_positions", []) or []))
    if hidden_count and branch_main_count:
        return "지지 본기와 지장간에 함께 깔려 현실 조건과 숨은 동기가 같이 움직인다."
    if hidden_count:
        return "지장간에 숨어 있어 겉으로 바로 보이지 않다가 운에서 자극될 때 드러난다."
    if branch_main_count:
        return "지지 본기에서 작용하므로 생활 조건과 현실 기반 쪽에서 먼저 드러난다."
    return "지장간 쪽 근거는 약하므로 투출·대운 발동 여부를 더 본다."


def _month_fit_label(month_fit_state: str) -> str:
    return {
        "both_supported_by_month_command": "두 작용 모두 월령상 사용 가능",
        "both_pressure_by_month_command": "두 작용 모두 월령상 부담 가능",
        "one_side_pressure_by_month_command": "한쪽은 쓰이고 한쪽은 부담",
        "mixed_or_neutral_by_month_command": "혼합 또는 중립",
        "not_evaluated_by_month_command": "월령 적합성 미평가",
    }.get(month_fit_state, month_fit_state)


def _context_state_label(state: str) -> str:
    return {
        "not_activated": "원국 직접 발동 약함",
        "month_pressure_confirms_risk": "월령상 위험 강화",
        "medicine_can_work": "병약 조절 가능",
        "structure_supports_expression": "성격 보조 강화",
        "risk_is_reinforced": "부담 작용 강화",
        "context_strengthens_pair": "보조 조건에 의한 작용 강화",
        "context_weakens_pair": "보조 조건에 의한 작용 약화",
        "conditional_by_context": "조건부 작용",
    }.get(state, state)


def _branch_note(branch_relation: dict[str, object]) -> str:
    first = dict(branch_relation.get("first", {}) or {})
    second = dict(branch_relation.get("second", {}) or {})
    grades = {str(first.get("grade", "") or ""), str(second.get("grade", "") or "")}
    if "branch_relation_pressures_actor" in grades:
        return "합충형파해에서는 압박 신호가 있어 좋은 작용도 사건성·마찰을 거쳐 드러난다."
    if "branch_relation_supports_actor" in grades:
        return "합이나 회합 계열의 보조가 있어 작용이 모이고 현실화되기 쉽다."
    if "branch_relation_mixed_actor" in grades:
        return "합충형파해가 섞여 있어 성립과 흔들림을 함께 본다."
    if "branch_relation_not_touching_actor" in grades:
        return "합충형파해가 이 조합을 직접 건드리지는 않는다."
    return "합충형파해 판단은 보조 신호로 둔다."


def _dual_context_judgment(
    *,
    rule: GyeokgukDualTenGodActionRule,
    presence_state: str,
    month_fit_state: str,
    combined_context: dict[str, object],
) -> dict[str, object]:
    score_delta = int(combined_context.get("score_delta", 0) or 0)
    if presence_state == "dual_action_not_present":
        state = "not_activated"
    elif month_fit_state in {"both_pressure_by_month_command", "one_side_pressure_by_month_command"} and rule.chain_grade in {
        "risk_chain",
        "compounded_burden_chain",
        "disease_chain",
    }:
        state = "month_pressure_confirms_risk"
    elif month_fit_state == "one_side_pressure_by_month_command":
        state = "conditional_by_context"
    elif month_fit_state == "both_pressure_by_month_command":
        state = "context_weakens_pair"
    elif rule.chain_grade == "medicine_chain":
        state = "medicine_can_work"
    elif rule.chain_grade in {"constructive_chain", "supportive_chain"} and score_delta >= 8:
        state = "structure_supports_expression"
    elif rule.chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"} and score_delta <= -4:
        state = "risk_is_reinforced"
    elif score_delta >= 8:
        state = "context_strengthens_pair"
    elif score_delta <= -8:
        state = "context_weakens_pair"
    else:
        state = "conditional_by_context"

    path = [
        f"월령: {_month_fit_label(month_fit_state)}",
        f"격국: {rule.pattern_combination_state}",
        f"일간 강약: {combined_context.get('strength_label', '')}",
        f"조후: {combined_context.get('climate_label', '')}",
        f"투출: {_protrusion_note(dict(combined_context.get('position', {}) or {}))}",
        f"통근: {_rooting_note(dict(combined_context.get('position', {}) or {}))}",
        f"위치: {_position_note(dict(combined_context.get('position', {}) or {}))}",
        f"지장간: {_hidden_stem_note(dict(combined_context.get('position', {}) or {}))}",
        f"합충형파해: {_branch_note(dict(combined_context.get('branch_relation', {}) or {}))}",
        f"대운·세운: {rule.timing_activation}",
    ]
    summary = (
        f"{_topic_form(rule.exact_pair_name)} {rule.pattern_combination_state}으로 읽는다. "
        f"월령 판단은 {_month_fit_label(month_fit_state)}이고, 강약·조후·위치 보정은 {score_delta:+d}이다. "
        f"최종 판정은 {_context_state_label(state)}이다."
    )
    return {
        "state": state,
        "summary": summary,
        "path": path,
        "basis_codes": [
            f"gyeokguk_dual_context_judgment:{state}",
            f"gyeokguk_dual_context_score_delta:{score_delta}",
        ],
    }


def build_gyeokguk_dual_ten_god_action_matches(
    *,
    pattern: str,
    ten_god_profile: TenGodProfile,
    month_governance_profile: MonthGovernanceProfile,
    element_profile: ElementProfile | None = None,
    position_signals: dict[str, PositionSignal] | None = None,
    branch_interactions: list[BranchInteraction] | None = None,
) -> list[GyeokgukDualTenGodActionMatch]:
    if pattern not in GYEOKGUK_DUAL_TEN_GOD_ACTIONS:
        return []
    matches: list[GyeokgukDualTenGodActionMatch] = []
    present_ten_gods: list[str] = []
    presence_scores: dict[str, int] = {}
    for ten_god in TEN_GODS:
        _, _, score = _presence_values(ten_god_profile, ten_god)
        if score > 0:
            present_ten_gods.append(ten_god)
            presence_scores[ten_god] = score
    for first_ten_god in present_ten_gods:
        for second_ten_god in present_ten_gods:
            if first_ten_god == second_ten_god:
                continue
            rule = gyeokguk_dual_ten_god_action_rule(pattern, first_ten_god, second_ten_god)
            first_fit = month_governance_profile.role_fits.get(rule.first_group)
            second_fit = month_governance_profile.role_fits.get(rule.second_group)
            first_month_fit_state = str(getattr(first_fit, "status", "") or "")
            second_month_fit_state = str(getattr(second_fit, "status", "") or "")
            first_single_rule = gyeokguk_ten_god_action_rule(pattern, first_ten_god)
            second_single_rule = gyeokguk_ten_god_action_rule(pattern, second_ten_god)
            first_score = presence_scores[first_ten_god]
            second_score = presence_scores[second_ten_god]
            first_context = gyeokguk_action_context_adjustment(
                ten_god=first_ten_god,
                acting_group=rule.first_group,
                element_profile=element_profile,
                position_signals=position_signals,
                branch_interactions=branch_interactions,
                month_fit_state=first_month_fit_state,
                role_grade=first_single_rule.role_grade,
            )
            second_context = gyeokguk_action_context_adjustment(
                ten_god=second_ten_god,
                acting_group=rule.second_group,
                element_profile=element_profile,
                position_signals=position_signals,
                branch_interactions=branch_interactions,
                month_fit_state=second_month_fit_state,
                role_grade=second_single_rule.role_grade,
            )
            combined_context = _combine_context(first_context, second_context)
            base_presence_score = min(100, round((first_score + second_score) / 2))
            presence_score = max(0, min(100, base_presence_score + int(combined_context["score_delta"])))
            presence_state = _pair_presence_state(first_score, second_score)
            month_state = _month_fit_state(rule, month_governance_profile)
            counter_signals: list[str] = []
            if presence_state == "dual_action_weak":
                counter_signals.append("gyeokguk_dual_weak_presence")
            if month_state in {"both_pressure_by_month_command", "one_side_pressure_by_month_command"}:
                counter_signals.append(month_state)
            counter_signals.extend(list(combined_context["counter_signals"]))
            context_judgment = _dual_context_judgment(
                rule=rule,
                presence_state=presence_state,
                month_fit_state=month_state,
                combined_context=combined_context,
            )
            verdict = _match_verdict(rule, presence_state, month_state)
            functional_role = _dual_functional_role(rule, verdict)
            matches.append(
                GyeokgukDualTenGodActionMatch(
                    rule_key=rule.rule_key,
                    pattern=rule.pattern,
                    pattern_ten_god=rule.pattern_ten_god,
                    pattern_group=rule.pattern_group,
                    first_ten_god=rule.first_ten_god,
                    first_group=rule.first_group,
                    second_ten_god=rule.second_ten_god,
                    second_group=rule.second_group,
                    first_relation_to_pattern=rule.first_relation_to_pattern,
                    second_relation_to_pattern=rule.second_relation_to_pattern,
                    first_to_second_relation=rule.first_to_second_relation,
                    pattern_center_bridge=dict(rule.pattern_center_bridge),
                    sequence_key=rule.sequence_key,
                    chain_grade=rule.chain_grade,
                    chain_nature=rule.chain_nature,
                    presence_state=presence_state,
                    presence_score=presence_score,
                    month_fit_state=month_state,
                    verdict=verdict,
                    functional_role=functional_role,
                    functional_role_label=DUAL_FUNCTIONAL_ROLE_LABELS[functional_role],
                    pattern_combination_state=rule.pattern_combination_state,
                    combination_resolution_state=rule.combination_resolution_state,
                    combination_resolution_logic=rule.combination_resolution_logic,
                    exact_pair_key=rule.exact_pair_key,
                    exact_pair_category=rule.exact_pair_category,
                    exact_pair_name=rule.exact_pair_name,
                    exact_pair_effect=rule.exact_pair_effect,
                    exact_pair_risk=rule.exact_pair_risk,
                    exact_pair_timing=rule.exact_pair_timing,
                    activation_context=_dual_activation_context(presence_state, month_state, rule.chain_grade),
                    context_judgment_state=str(context_judgment["state"]),
                    context_judgment_summary=str(context_judgment["summary"]),
                    context_judgment_path=list(context_judgment["path"]),
                    day_master_strength_context=str(combined_context["strength_label"]),
                    climate_context=str(combined_context["climate_label"]),
                    position_context=dict(combined_context["position"]),
                    branch_relation_context=dict(combined_context["branch_relation"]),
                    primary_actor=rule.primary_actor,
                    secondary_actor=rule.secondary_actor,
                    actor_hierarchy_logic=rule.actor_hierarchy_logic,
                    disease_medicine_logic=rule.disease_medicine_logic,
                    first_then_second_activation=rule.first_then_second_activation,
                    second_then_first_activation=rule.second_then_first_activation,
                    timing_activation=rule.timing_activation,
                    activation_order_profile=dict(rule.activation_order_profile),
                    event_manifestations=dict(rule.event_manifestations),
                    interaction_judgment=dict(rule.interaction_judgment),
                    visibility_interaction=dict(rule.visibility_interaction),
                    classical_action_tags=list(rule.classical_action_tags),
                    first_single_classical_action_tags=list(rule.first_single_classical_action_tags),
                    second_single_classical_action_tags=list(rule.second_single_classical_action_tags),
                    domain_priority=list(rule.domain_priority),
                    expert_summary=rule.success_logic,
                    domain_projections=dict(rule.domain_projections),
                    judgment_order=list(rule.judgment_order),
                    basis_codes=[
                        *rule.basis_codes,
                        f"gyeokguk_dual_presence:{presence_state}",
                        f"gyeokguk_dual_base_presence_score:{base_presence_score}",
                        f"gyeokguk_dual_presence_score:{presence_score}",
                        *list(combined_context["basis_codes"]),
                        *list(context_judgment["basis_codes"]),
                        f"gyeokguk_dual_functional_role:{functional_role}",
                    ],
                    counter_signals=list(dict.fromkeys(counter_signals)),
                )
            )
    matches.sort(
        key=lambda item: (
            item.presence_score,
            1 if item.verdict in {"constructive_dual_action", "conditional_dual_action"} else 0,
            item.chain_grade,
        ),
        reverse=True,
    )
    return matches


def validate_gyeokguk_dual_ten_god_action_dictionary() -> list[str]:
    issues: list[str] = []
    found_classical_tags: set[str] = set()
    found_pattern_center_bridge_keys: set[str] = set()
    mandatory_tag_pattern_signatures: dict[str, dict[str, set[tuple[object, ...]]]] = {}
    ordered_pair_pattern_signatures: dict[tuple[str, str], dict[str, tuple[object, ...]]] = {}
    disease_logic_seen: dict[str, str] = {}
    timing_logic_seen: dict[str, str] = {}
    for category, pattern_lenses in PATTERN_PAIR_CATEGORY_LENS.items():
        seen_effects: dict[str, str] = {}
        seen_risks: dict[str, str] = {}
        for pattern, lens in pattern_lenses.items():
            if pattern not in PATTERN_CENTER_BY_PATTERN:
                issues.append(f"{category}:{pattern}:unknown_pattern_lens")
            effect = str(lens.get("effect", "")).strip()
            risk = str(lens.get("risk", "")).strip()
            if not effect or not risk:
                issues.append(f"{category}:{pattern}:blank_pattern_pair_lens")
            if effect in seen_effects:
                issues.append(f"{category}:{pattern}:pattern_effect_collapsed_with:{seen_effects[effect]}")
            if risk in seen_risks:
                issues.append(f"{category}:{pattern}:pattern_risk_collapsed_with:{seen_risks[risk]}")
            seen_effects[effect] = pattern
            seen_risks[risk] = pattern
    if set(GYEOKGUK_DUAL_TEN_GOD_ACTIONS) != set(GYEOKGUK_TEN_GOD_ACTIONS):
        issues.append("pattern_set_mismatch")
    for pattern, first_map in GYEOKGUK_DUAL_TEN_GOD_ACTIONS.items():
        if set(first_map) != set(TEN_GODS):
            issues.append(f"{pattern}:first_ten_god_set_mismatch")
        for first_ten_god, second_map in first_map.items():
            if set(second_map) != set(TEN_GODS):
                issues.append(f"{pattern}:{first_ten_god}:second_ten_god_set_mismatch")
            for second_ten_god, rule in second_map.items():
                if not all(
                    [
                        rule.rule_key,
                        rule.pattern,
                        rule.pattern_ten_god,
                        rule.first_ten_god,
                        rule.second_ten_god,
                        rule.first_to_second_relation,
                        rule.sequence_key,
                        rule.chain_grade,
                        rule.chain_nature,
                        rule.pattern_effect,
                        rule.combination_resolution_state,
                        rule.combination_resolution_logic,
                        rule.exact_pair_key,
                        rule.exact_pair_category,
                        rule.exact_pair_name,
                        rule.exact_pair_effect,
                        rule.exact_pair_risk,
                        rule.exact_pair_timing,
                        rule.pattern_combination_state,
                        rule.primary_actor,
                        rule.secondary_actor,
                        rule.actor_hierarchy_logic,
                        rule.disease_medicine_logic,
                        rule.first_then_second_activation,
                        rule.second_then_first_activation,
                        rule.timing_activation,
                        rule.activation_order_profile,
                        rule.event_manifestations,
                        rule.interaction_judgment,
                        rule.visibility_interaction,
                        rule.classical_action_tags,
                        rule.first_single_classical_action_tags,
                        rule.second_single_classical_action_tags,
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
                for index, step in enumerate(GYEOKGUK_ACTION_JUDGMENT_ORDER, start=1):
                    if f"gyeokguk_dual_judgment_step:{index}:{step}" not in rule.basis_codes:
                        issues.append(f"{rule.rule_key}:missing_judgment_basis_step:{step}")
                if "gyeokguk_dual_luck_activation:daeun_seun" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_luck_activation_basis")
                if "gyeokguk_dual_activation_order_profile:daeun_seun_sequence" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_activation_order_profile_basis")
                if f"gyeokguk_dual_activation_order:first_then_second:{first_ten_god}>{second_ten_god}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_first_then_second_activation_order_basis")
                if f"gyeokguk_dual_activation_order:second_then_first:{second_ten_god}>{first_ten_god}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_second_then_first_activation_order_basis")
                order_profile = dict(rule.activation_order_profile or {})
                first_order = dict(order_profile.get("first_then_second", {}) or {})
                second_order = dict(order_profile.get("second_then_first", {}) or {})
                if not first_order or not second_order:
                    issues.append(f"{rule.rule_key}:missing_activation_order_profile")
                else:
                    if first_order.get("entry_ten_god") != first_ten_god:
                        issues.append(f"{rule.rule_key}:first_order_entry_ten_god_mismatch")
                    if first_order.get("follow_ten_god") != second_ten_god:
                        issues.append(f"{rule.rule_key}:first_order_follow_ten_god_mismatch")
                    if second_order.get("entry_ten_god") != second_ten_god:
                        issues.append(f"{rule.rule_key}:second_order_entry_ten_god_mismatch")
                    if second_order.get("follow_ten_god") != first_ten_god:
                        issues.append(f"{rule.rule_key}:second_order_follow_ten_god_mismatch")
                    for order_key, order in (
                        ("first_then_second", first_order),
                        ("second_then_first", second_order),
                    ):
                        if not order.get("entry_event_targets"):
                            issues.append(f"{rule.rule_key}:{order_key}:missing_entry_event_targets")
                        if not order.get("result_event_targets"):
                            issues.append(f"{rule.rule_key}:{order_key}:missing_result_event_targets")
                        if not order.get("entry_domains") or not order.get("result_domains"):
                            issues.append(f"{rule.rule_key}:{order_key}:missing_domains")
                        if not order.get("sequence_logic") or not order.get("sequence_summary"):
                            issues.append(f"{rule.rule_key}:{order_key}:missing_sequence_logic")
                if f"gyeokguk_dual_first_exact_ten_god:{first_ten_god}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_first_exact_ten_god_basis")
                if f"gyeokguk_dual_second_exact_ten_god:{second_ten_god}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_second_exact_ten_god_basis")
                first_exact_profile_domains = set(TEN_GOD_EXACT_ACTION_PROFILE[first_ten_god]["domains"])
                second_exact_profile_domains = set(TEN_GOD_EXACT_ACTION_PROFILE[second_ten_god]["domains"])
                first_exact_profile_domain_codes = {
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_first_exact_profile_domain:")
                }
                second_exact_profile_domain_codes = {
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_second_exact_profile_domain:")
                }
                if first_exact_profile_domains != first_exact_profile_domain_codes:
                    issues.append(f"{rule.rule_key}:first_exact_profile_domain_basis_mismatch")
                if second_exact_profile_domains != second_exact_profile_domain_codes:
                    issues.append(f"{rule.rule_key}:second_exact_profile_domain_basis_mismatch")
                for domain in (
                    "money",
                    "career",
                    "relationship",
                    "marriage",
                    "personality",
                    "luck_activation",
                    "first_then_second",
                    "second_then_first",
                ):
                    if domain not in rule.event_manifestations or not rule.event_manifestations[domain]:
                        issues.append(f"{rule.rule_key}:missing_event_manifestation:{domain}")
                    if f"gyeokguk_dual_event_manifestation:{domain}" not in rule.basis_codes:
                        issues.append(f"{rule.rule_key}:missing_event_manifestation_basis:{domain}")
                for key in (
                    "pattern_center",
                    "pair_relation",
                    "first_role",
                    "second_role",
                    "pattern_outcome",
                    "disease_or_medicine",
                    "risk_axis",
                    "primary_secondary",
                    "event_targets",
                    "sequence_first_then_second",
                    "sequence_second_then_first",
                ):
                    if key not in rule.interaction_judgment or not rule.interaction_judgment[key]:
                        issues.append(f"{rule.rule_key}:missing_interaction_judgment:{key}")
                for key in (
                    "protrusion",
                    "hidden_stem",
                    "rooting",
                    "unrooted",
                    "position",
                    "branch_interaction",
                    "component_faces",
                ):
                    if key not in rule.visibility_interaction or not rule.visibility_interaction[key]:
                        issues.append(f"{rule.rule_key}:missing_visibility_interaction:{key}")
                    if f"gyeokguk_dual_visibility_interaction:{key}" not in rule.basis_codes:
                        issues.append(f"{rule.rule_key}:missing_visibility_interaction_basis:{key}")
                if f"gyeokguk_dual_resolution:{rule.combination_resolution_state}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_dual_resolution_basis")
                if f"gyeokguk_dual_actor_hierarchy:{rule.primary_actor}>{rule.secondary_actor}" not in rule.basis_codes:
                    issues.append(f"{rule.rule_key}:missing_actor_hierarchy_basis")
                exact_pair_refinements = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_exact_pair_refinement:")
                ]
                if not exact_pair_refinements:
                    issues.append(f"{rule.rule_key}:missing_exact_pair_refinement")
                elif "general_exact_pair" in exact_pair_refinements:
                    issues.append(f"{rule.rule_key}:general_exact_pair_refinement_not_allowed")
                pattern_label = PATTERN_LENS[pattern]["label"]
                pattern_center = PATTERN_LENS[pattern]["center"]
                first_label = TEN_GOD_LABEL[first_ten_god]
                second_label = TEN_GOD_LABEL[second_ten_god]
                for logic_key, logic_text in {
                    "combination_resolution_logic": rule.combination_resolution_logic,
                    "actor_hierarchy_logic": rule.actor_hierarchy_logic,
                    "disease_medicine_logic": rule.disease_medicine_logic,
                    "timing_activation": rule.timing_activation,
                }.items():
                    if pattern_label not in logic_text:
                        issues.append(f"{rule.rule_key}:{logic_key}_missing_pattern_label")
                    if first_label not in logic_text:
                        issues.append(f"{rule.rule_key}:{logic_key}_missing_first_label")
                    if second_label not in logic_text:
                        issues.append(f"{rule.rule_key}:{logic_key}_missing_second_label")
                    if pattern_center not in logic_text:
                        issues.append(f"{rule.rule_key}:{logic_key}_missing_pattern_center")
                if rule.disease_medicine_logic in disease_logic_seen:
                    issues.append(f"{rule.rule_key}:disease_medicine_logic_collapsed_with:{disease_logic_seen[rule.disease_medicine_logic]}")
                disease_logic_seen[rule.disease_medicine_logic] = rule.rule_key
                if rule.timing_activation in timing_logic_seen:
                    issues.append(f"{rule.rule_key}:timing_activation_collapsed_with:{timing_logic_seen[rule.timing_activation]}")
                timing_logic_seen[rule.timing_activation] = rule.rule_key
                if (
                    rule.exact_pair_category == "wealth_generates_officer"
                    and "pyeon_gwan" in {first_ten_god, second_ten_god}
                    and rule.chain_grade in {"constructive_chain", "supportive_chain"}
                ):
                    issues.append(f"{rule.rule_key}:jaesaengsal_marked_plain_constructive")
                if (
                    rule.exact_pair_category == "wealth_generates_officer"
                    and "pyeon_gwan" in {first_ten_god, second_ten_god}
                    and pattern in {"seven_killings_pattern", "direct_officer_pattern", "yangren_peer_pattern"}
                    and rule.chain_grade != "risk_chain"
                ):
                    issues.append(f"{rule.rule_key}:jaesaengsal_should_be_risk_in_pressure_pattern")
                if (
                    pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"}
                    and "pyeon_gwan" in {first_ten_god, second_ten_god}
                    and any(
                        str(code) == "gyeokguk_dual_pattern_center_bridge:output_generates_wealth_generates_officer"
                        for code in rule.basis_codes
                    )
                    and rule.chain_grade in {"constructive_chain", "supportive_chain"}
                ):
                    issues.append(f"{rule.rule_key}:output_to_killing_via_wealth_marked_plain_constructive")
                if (
                    pattern == "direct_officer_pattern"
                    and rule.exact_pair_name == "상관견관"
                    and rule.chain_grade in {"constructive_chain", "supportive_chain", "medicine_chain"}
                ):
                    issues.append(f"{rule.rule_key}:sanggwan_gyeongwan_marked_too_soft")
                if (
                    pattern == "eating_god_pattern"
                    and rule.exact_pair_name in {"편인도식", "정인제식"}
                    and rule.chain_grade in {"constructive_chain", "supportive_chain", "medicine_chain"}
                ):
                    issues.append(f"{rule.rule_key}:dosik_marked_too_soft")
                if (
                    pattern in {"direct_wealth_pattern", "indirect_wealth_pattern"}
                    and rule.exact_pair_category == "peer_controls_wealth"
                    and rule.chain_grade in {"constructive_chain", "supportive_chain", "medicine_chain"}
                ):
                    issues.append(f"{rule.rule_key}:jaengjae_marked_too_soft")
                if (
                    pattern == "seven_killings_pattern"
                    and rule.exact_pair_name == "식신제살"
                    and first_ten_god == "sik_sin"
                    and second_ten_god == "pyeon_gwan"
                    and rule.chain_grade != "medicine_chain"
                ):
                    issues.append(f"{rule.rule_key}:siksin_jesal_not_medicine_chain")
                if (
                    pattern == "hurting_officer_pattern"
                    and rule.exact_pair_name in {"편인극상관", "정인극상관"}
                    and first_ten_god in {"pyeon_in", "jeong_in"}
                    and second_ten_god == "sang_gwan"
                    and rule.chain_grade != "medicine_chain"
                ):
                    issues.append(f"{rule.rule_key}:sanggwan_paein_not_medicine_chain")
                expected_relation = _relation_between(TEN_GOD_GROUPS[first_ten_god], TEN_GOD_GROUPS[second_ten_god])
                if rule.first_to_second_relation != expected_relation:
                    issues.append(f"{rule.rule_key}:first_to_second_relation_mismatch")
                first_rule = gyeokguk_ten_god_action_rule(pattern, first_ten_god)
                second_rule = gyeokguk_ten_god_action_rule(pattern, second_ten_god)
                if rule.first_relation_to_pattern != first_rule.relation_to_pattern:
                    issues.append(f"{rule.rule_key}:first_pattern_relation_mismatch")
                if rule.second_relation_to_pattern != second_rule.relation_to_pattern:
                    issues.append(f"{rule.rule_key}:second_pattern_relation_mismatch")
                first_single_tags = {
                    str(code).split(":", 1)[1]
                    for code in first_rule.basis_codes
                    if str(code).startswith("gyeokguk_single_classical_action:")
                }
                second_single_tags = {
                    str(code).split(":", 1)[1]
                    for code in second_rule.basis_codes
                    if str(code).startswith("gyeokguk_single_classical_action:")
                }
                dual_first_single_tags = {
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_first_single_classical_action:")
                }
                dual_second_single_tags = {
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_second_single_classical_action:")
                }
                if dual_first_single_tags != first_single_tags:
                    issues.append(f"{rule.rule_key}:first_single_classical_tags_not_preserved")
                if dual_second_single_tags != second_single_tags:
                    issues.append(f"{rule.rule_key}:second_single_classical_tags_not_preserved")
                if set(rule.first_single_classical_action_tags) != dual_first_single_tags:
                    issues.append(f"{rule.rule_key}:first_single_classical_tag_field_mismatch")
                if set(rule.second_single_classical_action_tags) != dual_second_single_tags:
                    issues.append(f"{rule.rule_key}:second_single_classical_tag_field_mismatch")
                ordered_pair_pattern_signatures.setdefault((first_ten_god, second_ten_god), {})[pattern] = (
                    rule.first_relation_to_pattern,
                    rule.second_relation_to_pattern,
                    rule.first_to_second_relation,
                    rule.chain_grade,
                    rule.combination_resolution_state,
                    rule.pattern_effect,
                    rule.exact_pair_category,
                    rule.exact_pair_effect,
                    rule.exact_pair_risk,
                    rule.disease_medicine_logic,
                    tuple(rule.domain_priority),
                    rule.first_then_second_activation,
                    rule.second_then_first_activation,
                )
                if first_ten_god != second_ten_god:
                    if rule.primary_actor == rule.secondary_actor:
                        issues.append(f"{rule.rule_key}:primary_secondary_actor_collapsed")
                    if rule.first_then_second_activation == rule.second_then_first_activation:
                        issues.append(f"{rule.rule_key}:activation_order_collapsed")
                for domain in ("money", "career", "relationship", "marriage", "personality", "timing"):
                    if domain not in rule.domain_projections or not rule.domain_projections[domain]:
                        issues.append(f"{rule.rule_key}:missing_domain_{domain}")
                if not set(rule.domain_priority).issubset({"money", "career", "relationship", "marriage", "personality", "reputation"}):
                    issues.append(f"{rule.rule_key}:invalid_domain_priority")
                exact_specificity_texts = {
                    "combination_resolution_logic": rule.combination_resolution_logic,
                    "actor_hierarchy_logic": rule.actor_hierarchy_logic,
                    "disease_medicine_logic": rule.disease_medicine_logic,
                    "timing_activation": rule.timing_activation,
                    "success_logic": rule.success_logic,
                    "failure_logic": rule.failure_logic,
                    "domain_projections": " ".join(rule.domain_projections.values()),
                    "event_manifestations": " ".join(rule.event_manifestations.values()),
                    "interaction_judgment": " ".join(rule.interaction_judgment.values()),
                    "visibility_interaction": " ".join(rule.visibility_interaction.values()),
                    "first_then_second_activation": rule.first_then_second_activation,
                    "second_then_first_activation": rule.second_then_first_activation,
                }
                for text_key, text_value in exact_specificity_texts.items():
                    if pattern_label not in text_value:
                        issues.append(f"{rule.rule_key}:{text_key}_missing_pattern_label")
                    if first_label not in text_value:
                        issues.append(f"{rule.rule_key}:{text_key}_missing_first_label")
                    if second_label not in text_value:
                        issues.append(f"{rule.rule_key}:{text_key}_missing_second_label")
                domain_visibility_text = (
                    exact_specificity_texts["domain_projections"]
                    + " "
                    + exact_specificity_texts["visibility_interaction"]
                )
                if TEN_GOD_EXACT_NUANCE[first_ten_god] not in domain_visibility_text:
                    issues.append(f"{rule.rule_key}:missing_first_exact_nuance_in_domain_or_visibility")
                if TEN_GOD_EXACT_NUANCE[second_ten_god] not in domain_visibility_text:
                    issues.append(f"{rule.rule_key}:missing_second_exact_nuance_in_domain_or_visibility")
                if not any(str(code).startswith("gyeokguk_dual_pair_lens:") for code in rule.basis_codes):
                    issues.append(f"{rule.rule_key}:missing_pair_lens")
                if not any(str(code).startswith("gyeokguk_dual_pair_lens_type:") for code in rule.basis_codes):
                    issues.append(f"{rule.rule_key}:missing_pair_lens_type")
                if any(str(code) == "gyeokguk_dual_pair_lens_type:default" for code in rule.basis_codes):
                    issues.append(f"{rule.rule_key}:default_pair_lens_not_allowed")
                if not any(str(code).startswith("gyeokguk_dual_exact_pair_refinement:") for code in rule.basis_codes):
                    issues.append(f"{rule.rule_key}:missing_exact_pair_refinement")
                lens_types = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_pair_lens_type:")
                ]
                classical_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_classical_action:")
                ]
                pattern_center_bridge_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_pattern_center_bridge:")
                ]
                found_pattern_center_bridge_keys.update(pattern_center_bridge_codes)
                direct_pair_name_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_direct_pair_name:")
                ]
                direct_pair_category_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_direct_pair_category:")
                ]
                mediated_pair_name_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_mediated_pair_name:")
                ]
                mediated_pair_category_codes = [
                    str(code).split(":", 1)[1]
                    for code in rule.basis_codes
                    if str(code).startswith("gyeokguk_dual_mediated_pair_category:")
                ]
                if pattern_center_bridge_codes:
                    bridge_profile = dict(rule.pattern_center_bridge or {})
                    if not bridge_profile:
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_missing_profile")
                    for required_key in (
                        "pattern_center_ten_god",
                        "pattern_center_label",
                        "pattern_center_group",
                        "mediated_name",
                        "direction",
                        "bridge_steps",
                        "effect",
                        "risk",
                        "timing",
                    ):
                        if required_key not in bridge_profile:
                            issues.append(f"{rule.rule_key}:pattern_center_bridge_profile_missing:{required_key}")
                    if bridge_profile and len(list(bridge_profile.get("bridge_steps", []) or [])) != 2:
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_steps_not_two")
                    if not direct_pair_name_codes:
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_missing_direct_pair_name")
                    if not direct_pair_category_codes:
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_missing_direct_pair_category")
                    if rule.exact_pair_name not in mediated_pair_name_codes:
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_missing_mediated_pair_name")
                    if not set(pattern_center_bridge_codes).issubset(set(mediated_pair_category_codes)):
                        issues.append(f"{rule.rule_key}:pattern_center_bridge_missing_mediated_pair_category")
                if not classical_codes:
                    issues.append(f"{rule.rule_key}:missing_classical_action_tag")
                if list(dict.fromkeys(classical_codes)) != list(rule.classical_action_tags):
                    issues.append(f"{rule.rule_key}:classical_action_tag_field_mismatch")
                if "gyeokguk_dual_specific_adjustment" in classical_codes:
                    issues.append(f"{rule.rule_key}:generic_classical_action_tag_not_allowed")
                if (
                    set(classical_codes).intersection(CORE_DUAL_CLASSICAL_TAGS_REQUIRING_SPECIFIC_LENS)
                    and "specific" not in lens_types
                    and not ("derived_specific" in lens_types and pattern_center_bridge_codes)
                ):
                    issues.append(f"{rule.rule_key}:core_classical_action_not_specific_lens")
                found_classical_tags.update(classical_codes)
                for tag in classical_codes:
                    if tag not in CLASSICAL_ACTION_MECHANICS:
                        issues.append(f"{rule.rule_key}:missing_classical_action_mechanic_profile:{tag}")
                        continue
                    mechanic_text = CLASSICAL_ACTION_MECHANIC_TEXTS.get(tag, {})
                    for text_axis in ("principle", "disease", "medicine"):
                        if not str(mechanic_text.get(text_axis, "")).strip():
                            issues.append(f"{rule.rule_key}:missing_dual_mechanic_text_{text_axis}:{tag}")
                    for mechanic_axis in ("flow", "disease", "medicine"):
                        if not any(
                            str(code).startswith(f"gyeokguk_dual_mechanic:{tag}:{mechanic_axis}:")
                            for code in rule.basis_codes
                        ):
                            issues.append(f"{rule.rule_key}:missing_dual_mechanic_{mechanic_axis}:{tag}")
                    if not any(
                        str(code).startswith(f"gyeokguk_dual_mechanic:{tag}:event:")
                        for code in rule.basis_codes
                    ):
                        issues.append(f"{rule.rule_key}:missing_dual_mechanic_event:{tag}")
                for tag in set(classical_codes).intersection(MANDATORY_DUAL_CLASSICAL_ACTION_TAGS):
                    signature = (
                        rule.first_ten_god,
                        rule.second_ten_god,
                        rule.first_relation_to_pattern,
                        rule.second_relation_to_pattern,
                        rule.first_to_second_relation,
                        rule.chain_grade,
                        rule.pattern_effect,
                        rule.exact_pair_category,
                        rule.exact_pair_effect,
                        rule.exact_pair_risk,
                        rule.disease_medicine_logic,
                        tuple(rule.domain_priority),
                    )
                    mandatory_tag_pattern_signatures.setdefault(tag, {}).setdefault(pattern, set()).add(signature)

    wealth_resource_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_in"]["jeong_gwan"]
    resource_wealth_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]["jeong_gwan"]
    if wealth_resource_officer.first_relation_to_pattern != "pattern_controls_actor":
        issues.append("direct_wealth_resource_officer_first_direction_invalid")
    if resource_wealth_officer.first_relation_to_pattern != "actor_controls_pattern":
        issues.append("direct_resource_wealth_officer_first_direction_invalid")
    if wealth_resource_officer.pattern_effect == resource_wealth_officer.pattern_effect:
        issues.append("dual_wealth_resource_resource_wealth_not_differentiated")

    wealth_wealth_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_jae"]["jeong_in"]
    resource_wealth_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]["jeong_in"]
    officer_wealth_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_jae"]["jeong_in"]
    if "소유권, 증빙, 정산" not in wealth_wealth_resource.exact_pair_effect:
        issues.append("dual_direct_wealth_pair_missing_wealth_resource_signature")
    if "격의 중심인 인성" not in resource_wealth_resource.exact_pair_effect:
        issues.append("dual_direct_resource_pair_missing_resource_center_signature")
    if "정재생정관생정인" not in officer_wealth_resource.exact_pair_name or "직책의 현실 근거" not in officer_wealth_resource.exact_pair_effect:
        issues.append("dual_direct_officer_pair_missing_wealth_officer_resource_chain")
    dual_wealth_resource_signatures = {
        (
            rule.exact_pair_name,
            rule.chain_grade,
            rule.pattern_effect,
            rule.exact_pair_effect,
            rule.exact_pair_risk,
            rule.disease_medicine_logic,
            rule.first_then_second_activation,
            rule.combination_resolution_state,
        )
        for rule in (wealth_wealth_resource, resource_wealth_resource, officer_wealth_resource)
    }
    if len(dual_wealth_resource_signatures) != 3:
        issues.append("dual_wealth_resource_by_pattern_center_collapsed")

    wealth_food_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["sik_sin"]["jeong_gwan"]
    wealth_hurting_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["sang_gwan"]["jeong_gwan"]
    wealth_food_killing = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["sik_sin"]["pyeon_gwan"]
    wealth_hurting_killing = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["sang_gwan"]["pyeon_gwan"]
    if "식신생정재생정관" not in wealth_food_officer.exact_pair_name or "식신제관" not in wealth_food_officer.exact_pair_effect:
        issues.append("dual_direct_wealth_food_officer_missing_output_wealth_officer_signature")
    if "반복 생산과 안정된 결과물" not in wealth_food_officer.exact_pair_effect or "평가와 책임을 처리할 결과물" not in wealth_food_officer.exact_pair_risk:
        issues.append("dual_direct_wealth_food_officer_missing_stable_output_responsibility_signature")
    if "상관생정재생정관" not in wealth_hurting_officer.exact_pair_name or "상관견관" not in wealth_hurting_officer.exact_pair_effect:
        issues.append("dual_direct_wealth_hurting_officer_missing_sanggwan_gyeongwan_signature")
    if "계약, 승인, 평판" not in wealth_hurting_officer.exact_pair_effect or "수익화보다 승인, 계약, 평판 리스크" not in wealth_hurting_officer.exact_pair_risk:
        issues.append("dual_direct_wealth_hurting_officer_missing_approval_reputation_signature")
    if "식신생정재생편관" not in wealth_food_killing.exact_pair_name or "식신제살" not in wealth_food_killing.exact_pair_effect:
        issues.append("dual_direct_wealth_food_killing_missing_siksin_jesal_signature")
    if "돈과 신용을 지키는 장치" not in wealth_food_killing.exact_pair_effect or "손실 방어에 머문다" not in wealth_food_killing.exact_pair_risk:
        issues.append("dual_direct_wealth_food_killing_missing_defensive_credit_signature")
    if "상관생정재생편관" not in wealth_hurting_killing.exact_pair_name or "상관제살" not in wealth_hurting_killing.exact_pair_effect:
        issues.append("dual_direct_wealth_hurting_killing_missing_sanggwan_jesal_signature")
    if "식신제살보다 빠르고 강하지만" not in wealth_hurting_killing.exact_pair_effect or "권위와 정면으로 부딪혀 사고성과 평판 부담" not in wealth_hurting_killing.exact_pair_risk:
        issues.append("dual_direct_wealth_hurting_killing_missing_collision_risk_signature")
    wealth_output_officer_signatures = {
        (
            rule.exact_pair_name,
            rule.chain_grade,
            rule.combination_resolution_state,
            rule.exact_pair_effect,
            rule.exact_pair_risk,
            rule.disease_medicine_logic,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (
            wealth_food_officer,
            wealth_hurting_officer,
            wealth_food_killing,
            wealth_hurting_killing,
        )
    }
    if len(wealth_output_officer_signatures) != 4:
        issues.append("dual_direct_wealth_output_officer_bridge_logic_collapsed")

    wealth_officer_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_gwan"]["jeong_in"]
    killing_wealth_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["seven_killings_pattern"]["jeong_jae"]["jeong_in"]
    if "재물에서 생긴 책임이 문서, 자격, 보호 장치로 안정" not in wealth_officer_resource.exact_pair_effect:
        issues.append("dual_direct_wealth_gwanin_missing_money_responsibility_document_signature")
    if "정재생정관생정인" not in officer_wealth_resource.exact_pair_name or "직책의 현실 근거" not in officer_wealth_resource.exact_pair_effect:
        issues.append("dual_direct_officer_jaegwanin_missing_official_real_base_signature")
    if "정재생편관생정인" not in killing_wealth_resource.exact_pair_name or killing_wealth_resource.chain_grade != "conditional_chain":
        issues.append("dual_seven_killings_jaegwanin_missing_conditional_salin_signature")
    if "재성이 살을 생하고 인성을 치면" not in killing_wealth_resource.exact_pair_risk:
        issues.append("dual_seven_killings_jaegwanin_missing_wealth_killing_resource_risk_signature")
    if "관인상생의 입구" not in resource_wealth_officer.exact_pair_effect or "재성이 인성을 먼저 손상하면" not in resource_wealth_officer.exact_pair_risk:
        issues.append("dual_direct_resource_jaegwanin_missing_resource_center_risk_signature")
    jaegwanin_signatures = {
        (
            rule.exact_pair_name,
            rule.exact_pair_category,
            rule.chain_grade,
            rule.combination_resolution_state,
            rule.exact_pair_effect,
            rule.exact_pair_risk,
            rule.disease_medicine_logic,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (wealth_officer_resource, officer_wealth_resource, killing_wealth_resource, resource_wealth_officer)
    }
    if len(jaegwanin_signatures) != 4:
        issues.append("dual_jaegwanin_pattern_logic_collapsed")

    resource_wealth_food = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]["sik_sin"]
    resource_wealth_hurting = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]["sang_gwan"]
    eating_wealth_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["eating_god_pattern"]["jeong_jae"]["pyeon_in"]
    eating_resource_wealth = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["eating_god_pattern"]["pyeon_in"]["jeong_jae"]
    if "도식으로 묶였던 식상이 풀려 실행, 발표, 결과물" not in resource_wealth_food.exact_pair_effect:
        issues.append("dual_direct_resource_wealth_food_missing_dosik_release_signature")
    if "상관생정재" not in resource_wealth_hurting.exact_pair_effect or "발표, 기획 전환" not in resource_wealth_hurting.timing_activation:
        issues.append("dual_direct_resource_wealth_hurting_missing_expression_release_signature")
    if "재성이 인성을 제어해 도식의 병을 낮춘다" not in eating_wealth_resource.exact_pair_effect:
        issues.append("dual_eating_wealth_resource_missing_dosik_medicine_signature")
    if "고정 소유와 정산 기준" not in eating_resource_wealth.exact_pair_effect or "외부 거래와 유동 자금" in eating_resource_wealth.exact_pair_effect:
        issues.append("dual_eating_resource_wealth_wrong_direct_wealth_face")
    if eating_wealth_resource.first_then_second_activation == eating_resource_wealth.first_then_second_activation:
        issues.append("dual_eating_dosik_medicine_order_activation_collapsed")
    dosik_release_signatures = {
        (
            rule.exact_pair_name,
            rule.chain_grade,
            rule.combination_resolution_state,
            rule.exact_pair_effect,
            rule.exact_pair_risk,
            rule.disease_medicine_logic,
            rule.first_then_second_activation,
            rule.second_then_first_activation,
            tuple(rule.domain_priority),
        )
        for rule in (resource_wealth_food, resource_wealth_hurting, eating_wealth_resource, eating_resource_wealth)
    }
    if len(dosik_release_signatures) != 4:
        issues.append("dual_jaegeukin_dosik_release_logic_collapsed")

    wealth_robbery_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["geob_jae"]["jeong_gwan"]
    wealth_robbery_killing = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["geob_jae"]["pyeon_gwan"]
    jianlu_wealth_officer = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["jianlu_peer_pattern"]["jeong_jae"]["jeong_gwan"]
    yangren_wealth_killing = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["yangren_peer_pattern"]["jeong_jae"]["pyeon_gwan"]
    if "재성의 소유권을 지킨다" not in wealth_robbery_officer.exact_pair_effect or "규칙과 책임으로 정리" not in wealth_robbery_officer.exact_pair_effect:
        issues.append("dual_direct_wealth_robbery_officer_missing_wealth_protection_signature")
    if "압박, 경쟁, 위기 대응" not in wealth_robbery_killing.exact_pair_effect or "위험 노출" not in wealth_robbery_killing.exact_pair_risk:
        issues.append("dual_direct_wealth_robbery_killing_missing_pressure_control_signature")
    if "강한 자기 기반이 돈을 거쳐 직책과 공식 책임" not in jianlu_wealth_officer.exact_pair_effect:
        issues.append("dual_jianlu_wealth_officer_missing_self_base_office_signature")
    if "제어 장치가 반드시 필요" not in yangren_wealth_killing.exact_pair_effect or yangren_wealth_killing.chain_grade != "risk_chain":
        issues.append("dual_yangren_wealth_killing_missing_required_control_signature")
    bigeop_control_signatures = {
        (
            rule.exact_pair_name,
            rule.exact_pair_category,
            rule.chain_grade,
            rule.combination_resolution_state,
            rule.exact_pair_effect,
            rule.exact_pair_risk,
            rule.disease_medicine_logic,
            rule.timing_activation,
            tuple(rule.domain_priority),
        )
        for rule in (wealth_robbery_officer, wealth_robbery_killing, jianlu_wealth_officer, yangren_wealth_killing)
    }
    if len(bigeop_control_signatures) != 4:
        issues.append("dual_bigeop_jaengjae_officer_control_logic_collapsed")

    killing_food_resource = GYEOKGUK_DUAL_TEN_GOD_ACTIONS["seven_killings_pattern"]["sik_sin"]["jeong_in"]
    if killing_food_resource.first_relation_to_pattern != "actor_controls_pattern":
        issues.append("seven_killings_food_resource_first_direction_invalid")
    if killing_food_resource.second_relation_to_pattern != "pattern_generates_actor":
        issues.append("seven_killings_food_resource_second_direction_invalid")

    def ensure_exact_variants_distinct(
        label: str,
        first_rule: GyeokgukDualTenGodActionRule,
        second_rule: GyeokgukDualTenGodActionRule,
    ) -> None:
        first_signature = (
            first_rule.exact_pair_name,
            first_rule.exact_pair_effect,
            first_rule.exact_pair_risk,
            first_rule.disease_medicine_logic,
            first_rule.timing_activation,
            tuple(first_rule.domain_priority),
        )
        second_signature = (
            second_rule.exact_pair_name,
            second_rule.exact_pair_effect,
            second_rule.exact_pair_risk,
            second_rule.disease_medicine_logic,
            second_rule.timing_activation,
            tuple(second_rule.domain_priority),
        )
        if first_signature == second_signature:
            issues.append(f"dual_exact_variant_collapsed:{label}")

    ensure_exact_variants_distinct(
        "direct_indirect_wealth_generates_officer",
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_wealth_pattern"]["jeong_jae"]["jeong_gwan"],
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["indirect_wealth_pattern"]["pyeon_jae"]["pyeon_gwan"],
    )
    ensure_exact_variants_distinct(
        "direct_officer_indirect_killing_generates_resource",
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_officer_pattern"]["jeong_gwan"]["jeong_in"],
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["seven_killings_pattern"]["pyeon_gwan"]["pyeon_in"],
    )
    ensure_exact_variants_distinct(
        "eating_hurting_output_generates_wealth",
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["eating_god_pattern"]["sik_sin"]["jeong_jae"],
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["hurting_officer_pattern"]["sang_gwan"]["pyeon_jae"],
    )
    ensure_exact_variants_distinct(
        "direct_indirect_resource_wealth_controls_resource",
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["direct_resource_pattern"]["jeong_jae"]["jeong_in"],
        GYEOKGUK_DUAL_TEN_GOD_ACTIONS["indirect_resource_pattern"]["pyeon_jae"]["pyeon_in"],
    )

    missing_classical_tags = MANDATORY_DUAL_CLASSICAL_ACTION_TAGS - found_classical_tags
    for tag in sorted(missing_classical_tags):
        issues.append(f"missing_mandatory_dual_classical_action:{tag}")
    missing_mechanic_tags = MANDATORY_DUAL_CLASSICAL_ACTION_TAGS - set(CLASSICAL_ACTION_MECHANICS)
    for tag in sorted(missing_mechanic_tags):
        issues.append(f"missing_mandatory_dual_classical_action_mechanic:{tag}")
    missing_mechanic_text_tags = set(CLASSICAL_ACTION_MECHANICS) - set(CLASSICAL_ACTION_MECHANIC_TEXTS)
    for tag in sorted(missing_mechanic_text_tags):
        issues.append(f"missing_dual_classical_action_mechanic_text:{tag}")
    expected_patterns = set(GYEOKGUK_DUAL_TEN_GOD_ACTIONS)
    for tag in sorted(MANDATORY_DUAL_CLASSICAL_ACTION_TAGS):
        covered_patterns = set(mandatory_tag_pattern_signatures.get(tag, {}))
        missing_patterns = expected_patterns - covered_patterns
        if missing_patterns:
            issues.append(
                f"mandatory_dual_classical_action_missing_patterns:{tag}:{','.join(sorted(missing_patterns))}"
            )
    missing_bridge_keys = MANDATORY_PATTERN_CENTER_BRIDGE_KEYS - found_pattern_center_bridge_keys
    for key in sorted(missing_bridge_keys):
        issues.append(f"missing_mandatory_pattern_center_bridge:{key}")
    for tag, pattern_signatures in mandatory_tag_pattern_signatures.items():
        if len(pattern_signatures) <= 1:
            continue
        unique_signatures = {
            signature
            for signatures in pattern_signatures.values()
            for signature in signatures
        }
        if len(unique_signatures) < len(pattern_signatures):
            issues.append(f"dual_mandatory_classical_action_pattern_signature_collapsed:{tag}")
    for tag in sorted(MANDATORY_DUAL_CLASSICAL_ACTION_TAGS):
        projection_signatures_by_pattern: dict[str, set[tuple[str, ...]]] = {}
        event_signatures_by_pattern: dict[str, set[tuple[str, ...]]] = {}
        for pattern, first_map in GYEOKGUK_DUAL_TEN_GOD_ACTIONS.items():
            for second_map in first_map.values():
                for rule in second_map.values():
                    if tag not in set(rule.classical_action_tags):
                        continue
                    projection_signatures_by_pattern.setdefault(pattern, set()).add(
                        tuple(
                            rule.domain_projections.get(domain, "")
                            for domain in ("money", "career", "relationship", "marriage", "personality", "timing")
                        )
                    )
                    event_signatures_by_pattern.setdefault(pattern, set()).add(
                        tuple(
                            rule.event_manifestations.get(domain, "")
                            for domain in (
                                "money",
                                "career",
                                "relationship",
                                "marriage",
                                "personality",
                                "luck_activation",
                                "first_then_second",
                                "second_then_first",
                            )
                        )
                    )
        if set(projection_signatures_by_pattern) != expected_patterns:
            issues.append(f"mandatory_dual_classical_action_projection_missing_patterns:{tag}")
            continue
        if set(event_signatures_by_pattern) != expected_patterns:
            issues.append(f"mandatory_dual_classical_action_event_missing_patterns:{tag}")
            continue
        projection_pattern_signatures = {
            pattern: tuple(sorted(signatures))
            for pattern, signatures in projection_signatures_by_pattern.items()
        }
        event_pattern_signatures = {
            pattern: tuple(sorted(signatures))
            for pattern, signatures in event_signatures_by_pattern.items()
        }
        if len(set(projection_pattern_signatures.values())) < len(expected_patterns):
            issues.append(f"dual_mandatory_classical_action_projection_collapsed_by_pattern:{tag}")
        if len(set(event_pattern_signatures.values())) < len(expected_patterns):
            issues.append(f"dual_mandatory_classical_action_event_collapsed_by_pattern:{tag}")
    for pair_key, pattern_signatures in ordered_pair_pattern_signatures.items():
        if set(pattern_signatures) != expected_patterns:
            missing = expected_patterns - set(pattern_signatures)
            issues.append(
                f"dual_ordered_pair_missing_pattern_signatures:{pair_key[0]}>{pair_key[1]}:{','.join(sorted(missing))}"
            )
            continue
        if len(set(pattern_signatures.values())) < len(expected_patterns):
            issues.append(f"dual_ordered_pair_pattern_signature_collapsed:{pair_key[0]}>{pair_key[1]}")
    return issues
