"""Five-element and ten-god cycle regulation.

This layer keeps the classical 생극 logic separate from prose rendering.  It
does not decide a whole fortune by itself; it tells downstream judgment whether
an active force is producing, regulating, damaging, or overfeeding another
force under the month-command standard.
"""

from __future__ import annotations

from typing import Any

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    ELEMENTS,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .relation_polarity import (
    COMBINE_RELATIONS,
    DISRUPTIVE_RELATIONS,
    branch_relation_polarity,
    relation_activated_elements,
)


CYCLE_REGULATION_VERSION = "cycle_regulation_v4_relation_two_axis"
PRINCIPLE_MATRIX_VERSION = "cycle_principle_matrix_v3_relation_two_axis"

ROLE_ORDER = ("resource", "peer", "output", "wealth", "officer")

ROLE_GENERATES = {
    "resource": "peer",
    "peer": "output",
    "output": "wealth",
    "wealth": "officer",
    "officer": "resource",
}

ROLE_CONTROLS = {
    "peer": "wealth",
    "wealth": "resource",
    "resource": "output",
    "output": "officer",
    "officer": "peer",
}

ROLE_LABELS = {
    "peer": "비겁",
    "output": "식상",
    "wealth": "재성",
    "officer": "관성",
    "resource": "인성",
}

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

ROLE_DOMAIN_LINKS = {
    "peer": ["money", "career", "love", "marriage", "personality"],
    "output": ["money", "career", "love", "personality"],
    "wealth": ["money", "career", "love", "marriage", "personality"],
    "officer": ["career", "money", "marriage", "love", "personality"],
    "resource": ["career", "money", "marriage", "love", "personality"],
}

BRANCH_REALITY_POSITION_WEIGHTS = {
    "month": 5.0,
    "day": 4.0,
    "hour": 3.0,
    "year": 2.5,
}

STEM_VISIBILITY_POSITION_WEIGHTS = {
    "month": 2.4,
    "day": 2.0,
    "hour": 1.5,
    "year": 1.3,
}

ROLE_EDGE_CLASSICAL_NAMES = {
    ("resource", "peer", "generates"): "인성생비겁",
    ("peer", "output", "generates"): "비겁생식상",
    ("output", "wealth", "generates"): "식상생재",
    ("wealth", "officer", "generates"): "재생관",
    ("officer", "resource", "generates"): "관인상생",
    ("peer", "wealth", "controls"): "비겁극재",
    ("wealth", "resource", "controls"): "재극인",
    ("resource", "output", "controls"): "인성극식상",
    ("output", "officer", "controls"): "식상극관",
    ("officer", "peer", "controls"): "관성극비겁",
}

ROLE_EDGE_THEORY = {
    "인성생비겁": "근거와 보호가 일간의 세력을 키웁니다.",
    "비겁생식상": "자기 힘이 실행과 결과물로 빠져나갑니다.",
    "식상생재": "기술, 말, 생산물이 재물로 이어집니다.",
    "재생관": "재물과 현실 조건이 책임, 계약, 지위로 올라갑니다.",
    "관인상생": "책임과 압박이 자격, 문서, 보호 장치로 이어집니다.",
    "비겁극재": "사람, 경쟁, 공동 몫이 재물을 건드립니다.",
    "재극인": "돈과 현실 조건이 인성의 보류, 보호, 문서성을 제어합니다.",
    "인성극식상": "인성의 생각과 보호가 식상의 실행과 결과물을 누릅니다.",
    "식상극관": "말, 기술, 결과물이 관성의 규칙과 압박을 건드립니다.",
    "관성극비겁": "관성이 비겁의 경쟁과 주도권을 책임 기준으로 묶습니다.",
}

JUDGMENT_LABELS = {
    "useful_generation": "필요한 기운을 생함",
    "burden_generation": "부담 기운을 생함",
    "strained_generation": "생하는 힘 자체가 불안정함",
    "functional_generation": "기능 연결",
    "medicinal_control": "부담 기운을 제어함",
    "damaging_control": "필요한 기운을 손상함",
    "burden_collision": "부담끼리 충돌함",
    "boundary_control": "경계를 세움",
    "wealth_competition": "재물을 두고 경쟁함",
    "shared_control_of_burdening_wealth": "부담 재물을 함께 감당함",
    "mediating_bridge": "상극을 통관으로 풀어냄",
    "unstable_bridge": "통관은 있으나 힘이 불안정함",
    "missing_bridge": "상극을 풀 중간 기운이 약함",
    "overloaded_bridge": "중간 기운이 부담까지 함께 받음",
    "reverse_control": "극하려는 힘이 약해 되밀림",
    "failed_control": "극이 제대로 성립하지 않음",
    "excessive_generation": "생이 지나쳐 부담을 키움",
    "draining_exhaustion": "생해 주는 쪽의 기운이 빠짐",
    "branch_combines_useful_element": "지지 합이 필요한 오행을 모음",
    "branch_combines_burden_element": "지지 합이 부담 오행을 모음",
    "branch_disrupts_useful_element": "충형해파가 필요한 오행을 흔듦",
    "branch_disrupts_burden_element": "충형해파가 부담 오행을 흔듦",
    "branch_mixed_cycle_activation": "지지 관계가 생극을 복합적으로 자극함",
    "stem_combine_transforms_useful_element": "천간합이 필요한 오행으로 화함",
    "stem_combine_transforms_burden_element": "천간합이 부담 오행으로 화함",
    "stem_combine_bound_not_transformed": "천간합은 있으나 합화가 약함",
    "stem_combine_ties_original_force": "천간합이 원래 작용을 묶음",
    "hidden_protrusion_supports_cycle": "지장간 투출이 필요한 생극을 현실화함",
    "hidden_protrusion_exposes_burden": "지장간 투출이 부담 작용을 드러냄",
    "visible_root_supports_cycle": "천간 통근이 필요한 생극을 지속시킴",
    "visible_root_anchors_burden": "천간 통근이 부담 작용을 고정함",
    "hidden_root_potential_cycle": "지장간과 통근이 잠재 생극을 보존함",
}

JUDGMENT_POLARITY = {
    "useful_generation": "support",
    "functional_generation": "support",
    "medicinal_control": "support",
    "boundary_control": "mixed",
    "shared_control_of_burdening_wealth": "mixed",
    "strained_generation": "mixed",
    "burden_generation": "pressure",
    "damaging_control": "pressure",
    "burden_collision": "pressure",
    "wealth_competition": "pressure",
    "mediating_bridge": "support",
    "unstable_bridge": "mixed",
    "missing_bridge": "pressure",
    "overloaded_bridge": "pressure",
    "reverse_control": "pressure",
    "failed_control": "mixed",
    "excessive_generation": "pressure",
    "draining_exhaustion": "pressure",
    "branch_combines_useful_element": "support",
    "branch_combines_burden_element": "pressure",
    "branch_disrupts_useful_element": "pressure",
    "branch_disrupts_burden_element": "mixed",
    "branch_mixed_cycle_activation": "mixed",
    "stem_combine_transforms_useful_element": "support",
    "stem_combine_transforms_burden_element": "pressure",
    "stem_combine_bound_not_transformed": "mixed",
    "stem_combine_ties_original_force": "mixed",
    "hidden_protrusion_supports_cycle": "support",
    "hidden_protrusion_exposes_burden": "pressure",
    "visible_root_supports_cycle": "support",
    "visible_root_anchors_burden": "pressure",
    "hidden_root_potential_cycle": "mixed",
}

MONTH_VERDICT_LABELS = {
    "generation_supports_needed_force": "생이 월령상 필요한 기운을 강화합니다.",
    "generation_overfeeds_burden": "생이 월령상 부담 기운을 키웁니다.",
    "generation_from_burdened_source": "생하는 쪽 자체가 월령상 부담을 안고 있습니다.",
    "generation_connects_function": "생이 기능을 이어 주지만 길흉은 강약과 위치에서 다시 갈립니다.",
    "control_regulates_illness": "극이 월령상 부담 기운을 제어합니다.",
    "control_damages_medicine": "극이 월령상 필요한 기운을 손상합니다.",
    "control_collides_burdens": "극이 부담 기운끼리 충돌하는 모양입니다.",
    "control_sets_boundary": "극이 경계를 세우지만 길흉은 강약과 위치에서 다시 갈립니다.",
    "control_competes_for_wealth": "비겁이 재성을 건드려 분배와 소유 문제가 생깁니다.",
    "control_shares_burdening_wealth": "부담 재성을 비겁이 함께 감당하지만 몫 문제도 생깁니다.",
    "bridge_mediates_conflict": "상극 사이에 통관 오행이 들어와 충돌을 완화합니다.",
    "bridge_unstable": "통관 오행은 있으나 월령상 힘이 불안정합니다.",
    "bridge_missing": "상극을 풀어 줄 통관 오행이 약합니다.",
    "bridge_overloaded": "통관 오행이 부담을 함께 받아 작용이 거칠어집니다.",
    "control_reversed": "극하려는 기운보다 받는 기운이 강해 반극이 일어납니다.",
    "control_failed": "극의 형식은 있으나 힘의 차이 때문에 제어가 약합니다.",
    "generation_excessive": "생하는 작용이 필요한 보강을 넘어 부담을 키웁니다.",
    "generation_drains_source": "생해 주는 쪽의 기운이 빠져 설기가 과해집니다.",
    "branch_combines_useful": "지지의 합이 월령상 필요한 오행을 모읍니다.",
    "branch_combines_burden": "지지의 합이 월령상 부담 오행을 키웁니다.",
    "branch_disrupts_useful": "충형해파가 필요한 오행의 뿌리와 작용을 흔듭니다.",
    "branch_disrupts_burden": "충형해파가 부담 오행을 흔들어 고착을 풉니다.",
    "branch_cycle_mixed": "지지 관계가 필요한 힘과 부담을 함께 자극합니다.",
    "stem_combine_transforms_useful": "천간합이 월령상 필요한 오행으로 화합니다.",
    "stem_combine_transforms_burden": "천간합이 월령상 부담 오행을 키웁니다.",
    "stem_combine_bound": "천간합은 있으나 월령이 합화 오행을 충분히 받아 주지 않습니다.",
    "stem_combine_ties_force": "천간합이 원래 글자의 생극 작용을 묶어 둡니다.",
    "hidden_protrusion_supports": "지장간의 글자가 투출되어 필요한 생극이 현실 작용으로 올라옵니다.",
    "hidden_protrusion_burdens": "지장간의 글자가 투출되어 부담 작용이 겉으로 드러납니다.",
    "visible_root_supports": "천간이 지지에 통근하여 필요한 생극의 지속력이 생깁니다.",
    "visible_root_burdens": "천간이 지지에 통근하여 부담 작용이 오래 유지됩니다.",
    "hidden_root_potential": "지장간과 뿌리에 생극 재료가 남아 잠재 작용을 보존합니다.",
}

ELEMENT_BRIDGE_THEORY = {
    ("wood", "fire", "earth"): "목극토의 충돌은 화가 살아 있을 때 목생화생토로 풀립니다.",
    ("fire", "earth", "metal"): "화극금의 충돌은 토가 살아 있을 때 화생토생금으로 풀립니다.",
    ("earth", "metal", "water"): "토극수의 충돌은 금이 살아 있을 때 토생금생수로 풀립니다.",
    ("metal", "water", "wood"): "금극목의 충돌은 수가 살아 있을 때 금생수생목으로 풀립니다.",
    ("water", "wood", "fire"): "수극화의 충돌은 목 기운이 중간에서 이어 줄 때 수생목생화로 정리됩니다.",
}

ELEMENT_REVERSE_CONTROL_THEORY = {
    ("wood", "earth"): "목극토라도 토가 지나치면 목이 꺾이는 토다목절로 봅니다.",
    ("fire", "metal"): "화극금이라도 금이 지나치면 불이 꺼지는 금다화식으로 봅니다.",
    ("earth", "water"): "토극수라도 수가 지나치면 흙이 떠내려가는 수다토류로 봅니다.",
    ("metal", "wood"): "금극목이라도 목이 지나치면 금이 이지러지는 목다금결로 봅니다.",
    ("water", "fire"): "수극화라도 화가 지나치면 물이 마르는 화다수갈로 봅니다.",
}

STEM_COMBINE_TRANSFORM_ELEMENTS = {
    frozenset(("gap", "gi")): ("earth", "갑기합토"),
    frozenset(("eul", "gyeong")): ("metal", "을경합금"),
    frozenset(("byeong", "sin")): ("water", "병신합수"),
    frozenset(("jeong", "im")): ("wood", "정임합목"),
    frozenset(("mu", "gye")): ("fire", "무계합화"),
}

STEM_LABELS = {
    "gap": "갑",
    "eul": "을",
    "byeong": "병",
    "jeong": "정",
    "mu": "무",
    "gi": "기",
    "gyeong": "경",
    "sin": "신",
    "im": "임",
    "gye": "계",
}

GENERATE_SENTENCES = {
    ("output", "wealth"): "식상이 재성을 생하면 만든 결과가 보상과 수입으로 넘어갑니다.",
    ("wealth", "officer"): "재성이 관성을 생하면 돈의 문제가 직책, 계약, 책임 기준으로 정리됩니다.",
    ("officer", "resource"): "관성이 인성을 생하면 맡은 책임이 문서, 자격, 보호 장치로 이어집니다.",
    ("resource", "peer"): "인성이 비겁을 생하면 판단의 근거가 일간과 자기 기반을 받칩니다.",
    ("peer", "output"): "비겁이 식상을 생하면 자기 힘이 결과물과 실행력으로 빠져나갑니다.",
}

CONTROL_REGULATION_SENTENCES = {
    ("officer", "peer"): "관성이 비겁을 제어하면 경쟁, 분배, 내 몫의 문제가 책임 기준 안으로 들어갑니다.",
    ("wealth", "resource"): "재성이 인성을 제어하면 생각과 검토가 길어지는 문제를 현실 기준으로 정리합니다.",
    ("resource", "output"): "인성이 식상을 제어하면 말과 결과물을 근거와 절차 안에서 다듬습니다.",
    ("output", "officer"): "식상이 관성을 제어하면 책임과 압박을 실제 처리 능력으로 풀어냅니다.",
    ("peer", "wealth"): "비겁이 재성을 제어하면 돈과 소유를 두고 사람 사이의 몫 문제가 커집니다.",
}

CONTROL_DAMAGE_SENTENCES = {
    ("officer", "peer"): "관성이 비겁을 지나치게 누르면 자기 결정권보다 책임과 평가가 먼저 커집니다.",
    ("wealth", "resource"): "재성이 인성을 손상하면 문서, 자격, 보호 장치보다 돈의 요구가 앞섭니다.",
    ("resource", "output"): "인성이 식상을 막으면 생각과 검토가 결과물보다 앞서 실행이 늦어집니다.",
    ("output", "officer"): "식상이 관성을 치면 말과 결과물이 규정, 평가, 책임 기준과 부딪힙니다.",
    ("peer", "wealth"): "비겁이 재성을 치면 수입이 생겨도 분배, 경쟁, 공동 비용 문제가 따라붙습니다.",
}

CHAIN_SENTENCES = {
    "wealth_generates_officer_controls_peer": "재성이 관성을 세우고 관성이 비겁을 제어하면 돈과 사람 사이의 몫 문제가 계약과 책임 기준으로 정리됩니다.",
    "wealth_generates_officer_controls_peer_with_cost": "재성이 관성을 세워 비겁을 묶는 힘은 있으나, 재성 자체가 부담이면 돈과 책임 문제가 함께 커집니다.",
    "wealth_controls_resource_releases_output": "재성이 인성을 제어하면 도식으로 묶였던 식상이 풀리고, 생각보다 결과물이 앞에 서기 시작합니다.",
    "output_controls_officer_reduces_pressure": "식상이 관성을 제어하면 어려운 책임을 말이 아니라 실무와 결과물로 처리합니다.",
    "officer_generates_resource_protects_body": "관성이 인성을 생하면 압박이 그대로 끝나지 않고 자격, 문서, 보호 장치로 이어집니다.",
    "output_generates_wealth_then_officer": "식상이 재성을 생하고 재성이 관성을 생하면 결과물이 돈이 되고, 그 돈이 다시 직책과 책임 기준으로 올라갑니다.",
    "resource_controls_output_dosik": "인성이 식상을 강하게 누르면 도식이 됩니다. 생각과 준비가 많아져 결과물이 늦어집니다.",
}

CHAIN_CLASSICAL_NAMES = {
    "wealth_generates_officer_controls_peer": "재생관으로 비겁을 제어",
    "wealth_controls_resource_releases_output": "재극인으로 도식을 완화",
    "output_controls_officer_reduces_pressure": "식상제살",
    "officer_generates_resource_protects_body": "관인상생",
    "output_generates_wealth_then_officer": "식상생재 후 재생관",
    "resource_controls_output_dosik": "도식",
}

CHAIN_STATUS_JUDGMENT = {
    "regulates_pressure": "medicinal_control",
    "regulates_with_cost": "boundary_control",
    "sets_boundary": "boundary_control",
    "feeds_useful_force": "useful_generation",
    "connects_function": "functional_generation",
    "mixed_chain": "strained_generation",
    "damages_useful_force": "damaging_control",
}

CHAIN_DECISION_TARGET_INDEX = {
    "wealth_generates_officer_controls_peer": -1,
    "wealth_controls_resource_releases_output": 1,
    "output_controls_officer_reduces_pressure": -1,
    "officer_generates_resource_protects_body": -1,
    "output_generates_wealth_then_officer": -1,
    "resource_controls_output_dosik": -1,
}

CHAIN_EDGE_RELATIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "wealth_generates_officer_controls_peer": (
        ("wealth", "officer", "generates"),
        ("officer", "peer", "controls"),
    ),
    "wealth_controls_resource_releases_output": (
        ("wealth", "resource", "controls"),
        ("resource", "output", "controls"),
    ),
    "output_controls_officer_reduces_pressure": (
        ("output", "officer", "controls"),
    ),
    "officer_generates_resource_protects_body": (
        ("officer", "resource", "generates"),
    ),
    "output_generates_wealth_then_officer": (
        ("output", "wealth", "generates"),
        ("wealth", "officer", "generates"),
    ),
    "resource_controls_output_dosik": (
        ("resource", "output", "controls"),
    ),
}

ROLE_EDGE_DOMAIN_AXES: dict[tuple[str, str, str], dict[str, str]] = {
    ("output", "wealth", "generates"): {
        "money": "기술과 결과물이 수입으로 전환되는 축",
        "career": "성과물이 평가와 보상으로 이어지는 축",
        "love": "표현과 호감이 현실 선택으로 이어지는 축",
        "marriage": "생활 표현이 돈과 책임 문제로 이어지는 축",
        "personality": "생각보다 결과물을 먼저 내놓는 성향",
    },
    ("wealth", "officer", "generates"): {
        "money": "돈과 계약이 책임 범위로 올라가는 축",
        "career": "자원과 실적이 직책과 권한으로 바뀌는 축",
        "love": "현실 조건이 관계의 약속을 압박하는 축",
        "marriage": "돈과 생활 조건이 결혼 결정으로 이어지는 축",
        "personality": "현실 부담을 책임으로 받아들이는 성향",
    },
    ("officer", "resource", "generates"): {
        "money": "책임을 문서와 보호 장치로 정리하는 축",
        "career": "직책과 압박이 자격과 신뢰로 이어지는 축",
        "love": "관계 부담을 안정감과 설명으로 바꾸는 축",
        "marriage": "배우자와 가족 책임을 제도와 약속으로 정리하는 축",
        "personality": "압박이 커질수록 근거와 절차를 찾는 성향",
    },
    ("resource", "peer", "generates"): {
        "money": "보호와 정보가 자기 몫의 근거를 키우는 축",
        "career": "자격과 문서가 자기 입지를 키우는 축",
        "love": "안정 욕구가 자기 기준을 강하게 만드는 축",
        "marriage": "가정의 보호 욕구가 생활 주도권으로 이어지는 축",
        "personality": "확신과 방어 논리가 강해지는 성향",
    },
    ("peer", "output", "generates"): {
        "money": "자기 힘이 실행과 상품으로 빠져나가는 축",
        "career": "주도권이 일 처리와 결과물로 바뀌는 축",
        "love": "자기 표현이 호감과 거리감에 영향을 주는 축",
        "marriage": "생활 주도권이 말과 행동 방식으로 드러나는 축",
        "personality": "내 힘을 직접 행동으로 바꾸려는 성향",
    },
    ("peer", "wealth", "controls"): {
        "money": "내 몫과 공동 몫이 부딪히는 축",
        "career": "경쟁자와 이해관계가 보상 기준을 건드리는 축",
        "love": "관계 안에서 소유감과 비교 의식이 생기는 축",
        "marriage": "생활비와 공동 자산의 몫이 예민해지는 축",
        "personality": "자기 몫을 쉽게 양보하지 않는 성향",
    },
    ("wealth", "resource", "controls"): {
        "money": "현실의 돈 문제가 문서와 명분을 누르는 축",
        "career": "성과 요구가 공부와 자격의 보류를 끊는 축",
        "love": "현실 조건이 감정의 명분을 검증하는 축",
        "marriage": "돈과 주거 조건이 보호 욕구를 현실로 끌어내리는 축",
        "personality": "생각보다 현실 결정을 우선하는 성향",
    },
    ("resource", "output", "controls"): {
        "money": "생각과 검토가 결과물의 출시를 늦추는 축",
        "career": "문서와 기준이 실행 속도를 제어하는 축",
        "love": "안전 확인이 표현을 늦추는 축",
        "marriage": "보호 논리가 생활 표현과 결정을 늦추는 축",
        "personality": "실행 전에 근거를 오래 확인하는 성향",
    },
    ("output", "officer", "controls"): {
        "money": "결과물과 말이 책임 기준을 건드리는 축",
        "career": "실무와 표현이 권한과 규정을 다루는 축",
        "love": "표현 방식이 약속과 책임을 흔드는 축",
        "marriage": "말과 행동이 배우자와의 책임 기준을 건드리는 축",
        "personality": "부당한 압박에는 말과 결과로 대응하는 성향",
    },
    ("officer", "peer", "controls"): {
        "money": "규칙과 계약이 경쟁과 몫 문제를 정리하는 축",
        "career": "권한과 책임이 자기 주장과 경쟁을 묶는 축",
        "love": "약속과 책임감이 관계의 주도권을 정리하는 축",
        "marriage": "가정의 규칙이 개인 주장과 역할을 정리하는 축",
        "personality": "책임 기준 앞에서 자기 힘을 조절하는 성향",
    },
}

CHAIN_DECISION_NOTES = {
    "wealth_generates_officer_controls_peer": "중간의 관성이 비겁을 제어하는 힘으로 쓰이는지가 핵심입니다.",
    "wealth_controls_resource_releases_output": "재성이 인성의 도식 작용을 제어한 뒤 식상이 풀리는지가 핵심입니다.",
    "output_controls_officer_reduces_pressure": "식상이 관성의 압박을 실무와 결과물로 처리하는지를 봅니다.",
    "officer_generates_resource_protects_body": "관성이 인성으로 이어져 책임이 자격과 보호로 정리되는지를 봅니다.",
    "output_generates_wealth_then_officer": "식상의 결과물이 재성으로 이어지고 다시 관성으로 올라가는지를 봅니다.",
    "resource_controls_output_dosik": "인성이 식상을 눌러 결과물이 늦어지는지를 봅니다.",
}


REGULAR_PATTERN_CYCLE_RULES: dict[str, list[dict[str, Any]]] = {
    "jianlu_peer_pattern": [
        {
            "key": "jianlu_uses_officer_to_bind_peer",
            "role": "support",
            "edges": (("officer", "peer", "controls"),),
            "signal_ids": ("wealth_generates_officer_controls_peer",),
            "reason": "비견·건록 계열은 비겁의 힘을 관성으로 묶을 때 사회적 책임과 자리로 정리됩니다.",
        },
        {
            "key": "jianlu_uses_output_to_release_peer",
            "role": "support",
            "edges": (("peer", "output", "generates"),),
            "reason": "강한 자기 힘은 식상으로 빠져 결과물과 실행력으로 쓰여야 합니다.",
        },
        {
            "key": "jianlu_warns_resource_feeding_peer",
            "role": "caution",
            "edges": (("resource", "peer", "generates"),),
            "reason": "인성이 비겁을 더 키우면 자기 기준과 경쟁심이 과해질 수 있습니다.",
        },
        {
            "key": "jianlu_warns_peer_competing_wealth",
            "role": "caution",
            "edges": (("peer", "wealth", "controls"),),
            "reason": "비겁이 재성을 치면 몫, 분배, 돈의 소유권이 예민해집니다.",
        },
    ],
    "yangren_peer_pattern": [
        {
            "key": "yangren_needs_officer_control",
            "role": "support",
            "edges": (("officer", "peer", "controls"),),
            "signal_ids": ("wealth_generates_officer_controls_peer",),
            "reason": "양인 계열은 관성이 칼날 같은 비겁을 제어할 때 힘이 사회적 책임으로 정리됩니다.",
        },
        {
            "key": "yangren_uses_output_release",
            "role": "support",
            "edges": (("peer", "output", "generates"),),
            "reason": "강한 기운은 식상으로 풀려 실무와 결과물로 빠질 때 쓰임이 생깁니다.",
        },
        {
            "key": "yangren_warns_resource_overfeeding_blade",
            "role": "caution",
            "edges": (("resource", "peer", "generates"),),
            "reason": "인성이 비겁을 더 생하면 양인의 힘이 고집과 충돌로 굳기 쉽습니다.",
        },
        {
            "key": "yangren_warns_peer_taking_wealth",
            "role": "caution",
            "edges": (("peer", "wealth", "controls"),),
            "reason": "비겁이 재성을 치면 재물보다 경쟁과 분배 문제가 먼저 커집니다.",
        },
    ],
    "eating_god_pattern": [
        {
            "key": "eating_god_uses_output_to_wealth",
            "role": "support",
            "edges": (("output", "wealth", "generates"),),
            "signal_ids": ("output_generates_wealth_then_officer",),
            "reason": "식신격은 결과물과 기술이 재성으로 이어질 때 수입의 길이 분명해집니다.",
        },
        {
            "key": "eating_god_controls_seven_killings",
            "role": "support",
            "edges": (("output", "officer", "controls"),),
            "signal_ids": ("output_controls_officer_reduces_pressure",),
            "reason": "식신은 편관의 압박을 처리 능력과 실무력으로 다스릴 때 격이 살아납니다.",
        },
        {
            "key": "eating_god_warns_resource_damaging_output",
            "role": "caution",
            "edges": (("resource", "output", "controls"),),
            "signal_ids": ("resource_controls_output_dosik",),
            "reason": "인성이 식신을 누르면 도식이 되어 결과물이 늦고 실행이 막힙니다.",
        },
    ],
    "hurting_officer_pattern": [
        {
            "key": "hurting_officer_uses_output_to_wealth",
            "role": "support",
            "edges": (("output", "wealth", "generates"),),
            "signal_ids": ("output_generates_wealth_then_officer",),
            "reason": "상관격은 말, 기획, 개선 능력이 재성으로 이어질 때 현실 성과가 생깁니다.",
        },
        {
            "key": "hurting_officer_uses_resource_refinement",
            "role": "support",
            "edges": (("resource", "output", "controls"),),
            "reason": "상관격의 식상은 인성의 근거와 자격을 얻을 때 표현이 권위와 신뢰를 갖습니다.",
        },
        {
            "key": "hurting_officer_warns_output_attacking_officer",
            "role": "caution",
            "edges": (("output", "officer", "controls"),),
            "reason": "상관이 관성을 치면 규정, 평가, 권위와 직접 부딪혀 직업적 마찰이 커집니다.",
        },
    ],
    "indirect_wealth_pattern": [
        {
            "key": "indirect_wealth_uses_output_to_wealth",
            "role": "support",
            "edges": (("output", "wealth", "generates"),),
            "signal_ids": ("output_generates_wealth_then_officer",),
            "reason": "편재격은 활동과 생산물이 재성으로 이어질 때 외부 수익과 거래가 살아납니다.",
        },
        {
            "key": "indirect_wealth_uses_wealth_to_officer",
            "role": "support",
            "edges": (("wealth", "officer", "generates"),),
            "signal_ids": ("wealth_generates_officer_controls_peer",),
            "reason": "편재가 관성을 생하면 외부 기회가 책임 있는 자리와 사업적 권한으로 올라갑니다.",
        },
        {
            "key": "indirect_wealth_warns_peer_competition",
            "role": "caution",
            "edges": (("peer", "wealth", "controls"),),
            "reason": "편재격에서 비겁이 재성을 치면 큰돈, 거래, 수익 배분을 두고 경쟁이 커집니다.",
        },
    ],
    "direct_wealth_pattern": [
        {
            "key": "direct_wealth_uses_output_to_wealth",
            "role": "support",
            "edges": (("output", "wealth", "generates"),),
            "signal_ids": ("output_generates_wealth_then_officer",),
            "reason": "정재격은 꾸준한 결과가 안정 수입으로 이어질 때 재물의 근거가 분명해집니다.",
        },
        {
            "key": "direct_wealth_uses_wealth_to_officer",
            "role": "support",
            "edges": (("wealth", "officer", "generates"),),
            "signal_ids": ("wealth_generates_officer_controls_peer",),
            "reason": "정재가 관성을 생하면 수입, 계약, 책임 기준이 함께 잡힙니다.",
        },
        {
            "key": "direct_wealth_uses_wealth_to_control_resource",
            "role": "support",
            "edges": (("wealth", "resource", "controls"),),
            "signal_ids": ("wealth_controls_resource_releases_output",),
            "reason": "정재격에서 재극인은 생각과 보류를 현실 기준으로 정리해 돈의 결정력을 살립니다.",
        },
        {
            "key": "direct_wealth_warns_peer_competition",
            "role": "caution",
            "edges": (("peer", "wealth", "controls"),),
            "reason": "정재격에서 비겁이 재성을 치면 안정 수입과 생활 기반의 몫 문제가 예민해집니다.",
        },
    ],
    "seven_killings_pattern": [
        {
            "key": "seven_killings_uses_output_control",
            "role": "support",
            "edges": (("output", "officer", "controls"),),
            "signal_ids": ("output_controls_officer_reduces_pressure",),
            "reason": "편관격은 식신이 살을 제어할 때 압박이 실무 능력과 문제 해결력으로 바뀝니다.",
        },
        {
            "key": "seven_killings_uses_officer_to_resource",
            "role": "support",
            "edges": (("officer", "resource", "generates"),),
            "signal_ids": ("officer_generates_resource_protects_body",),
            "reason": "편관이 인성으로 이어지면 살의 압박이 자격, 문서, 보호 장치로 전환됩니다.",
        },
        {
            "key": "seven_killings_warns_wealth_feeding_killing",
            "role": "caution",
            "edges": (("wealth", "officer", "generates"),),
            "reason": "편관격에서 재성이 관살을 더 생하면 돈, 성과, 계약이 곧 책임 압박으로 커집니다.",
        },
    ],
    "direct_officer_pattern": [
        {
            "key": "direct_officer_uses_officer_to_resource",
            "role": "support",
            "edges": (("officer", "resource", "generates"),),
            "signal_ids": ("officer_generates_resource_protects_body",),
            "reason": "정관격은 관성이 인성으로 이어질 때 책임이 자격과 제도적 안정으로 정리됩니다.",
        },
        {
            "key": "direct_officer_uses_wealth_to_officer",
            "role": "support",
            "edges": (("wealth", "officer", "generates"),),
            "reason": "재성이 관성을 생하면 공적 책임과 평가가 현실 기반을 얻습니다.",
        },
        {
            "key": "direct_officer_warns_output_attacking_officer",
            "role": "caution",
            "edges": (("output", "officer", "controls"),),
            "reason": "정관격에서 식상이 관성을 치면 규정, 직책, 평가 체계와 충돌하기 쉽습니다.",
        },
        {
            "key": "direct_officer_warns_peer_disrupting_order",
            "role": "support",
            "edges": (("officer", "peer", "controls"),),
            "reason": "정관격에서 관성이 비겁을 제어하면 자기 기준이 공적 책임과 질서 안으로 들어옵니다.",
        },
    ],
    "indirect_resource_pattern": [
        {
            "key": "indirect_resource_uses_wealth_control",
            "role": "support",
            "edges": (("wealth", "resource", "controls"),),
            "signal_ids": ("wealth_controls_resource_releases_output",),
            "reason": "편인격은 재성이 편인의 과한 보류와 의심을 제어할 때 현실 판단이 살아납니다.",
        },
        {
            "key": "indirect_resource_uses_output_result",
            "role": "support",
            "edges": (("resource", "output", "controls"),),
            "reason": "편인격은 인성의 생각이 식상 결과물로 정리될 때 전문성이 밖으로 나옵니다.",
        },
        {
            "key": "indirect_resource_warns_resource_excess",
            "role": "caution",
            "edges": (("resource", "peer", "generates"),),
            "reason": "편인이 일간을 지나치게 생하면 검토와 자기 확신이 늘어 실행이 늦어집니다.",
        },
        {
            "key": "indirect_resource_warns_dosik",
            "role": "caution",
            "signal_ids": ("resource_controls_output_dosik",),
            "reason": "편인이 식신을 직접 누르면 도식이 되어 결과물과 수입화가 늦어집니다.",
        },
    ],
    "direct_resource_pattern": [
        {
            "key": "direct_resource_uses_wealth_control",
            "role": "support",
            "edges": (("wealth", "resource", "controls"),),
            "signal_ids": ("wealth_controls_resource_releases_output",),
            "reason": "정인격은 재성이 보호와 보류를 현실 기준으로 조절할 때 안정이 결과로 이어집니다.",
        },
        {
            "key": "direct_resource_uses_output_result",
            "role": "support",
            "edges": (("resource", "output", "controls"),),
            "reason": "정인격은 인성의 근거가 결과물과 문서화로 이어질 때 실용성이 생깁니다.",
        },
        {
            "key": "direct_resource_warns_resource_excess",
            "role": "caution",
            "edges": (("resource", "peer", "generates"),),
            "reason": "정인이 과하면 보호와 안정 욕구가 강해져 실행과 결정이 늦어집니다.",
        },
        {
            "key": "direct_resource_warns_dosik",
            "role": "caution",
            "signal_ids": ("resource_controls_output_dosik",),
            "reason": "정인이 식상을 지나치게 누르면 준비와 명분이 앞서 결과물이 늦어집니다.",
        },
    ],
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


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


def _group_for_element(day_element: str, element: str) -> str:
    for group in ROLE_ORDER:
        if _role_element(day_element, group) == element:
            return group
    return ""


def _role_positions(position_signals: dict[str, Any], group: str) -> list[str]:
    positions: list[str] = []
    for position, signal in position_signals.items():
        stem_group = TEN_GOD_GROUPS.get(str(getattr(signal, "stem_ten_god", "")))
        if stem_group == group:
            positions.append(f"{position}_stem")
        for ten_god in list(getattr(signal, "hidden_ten_gods", []) or []):
            if TEN_GOD_GROUPS.get(str(ten_god)) == group:
                positions.append(f"{position}_hidden")
                break
        branch_group = TEN_GOD_GROUPS.get(str(getattr(signal, "branch_main_ten_god", "")))
        if branch_group == group:
            positions.append(f"{position}_branch_main")
    return _unique(positions)


def _element_positions(position_signals: dict[str, Any], element: str) -> list[str]:
    positions: list[str] = []
    for position, signal in position_signals.items():
        if str(getattr(signal, "stem_element", "")) == element:
            positions.append(f"{position}_stem")
        if str(getattr(signal, "branch_element", "")) == element:
            positions.append(f"{position}_branch_body")
        branch_key = str(getattr(signal, "branch_key", ""))
        for stem_key, _weight in BRANCH_HIDDEN_STEMS.get(branch_key, []):
            if STEM_METADATA[stem_key]["element"] == element:
                positions.append(f"{position}_hidden")
                break
    return _unique(positions)


def _fit(profile: Any, group: str) -> Any | None:
    return getattr(profile, "role_fits", {}).get(group)


def _fit_scores(profile: Any, group: str) -> tuple[int, int]:
    fit = _fit(profile, group)
    if fit is None:
        return 0, 0
    return int(getattr(fit, "support_score", 0) or 0), int(getattr(fit, "pressure_score", 0) or 0)


def _element_fit_scores(profile: Any, element: str) -> tuple[int, int]:
    fit = getattr(profile, "element_fits", {}).get(element)
    if fit is None:
        return 0, 0
    return int(getattr(fit, "support_score", 0) or 0), int(getattr(fit, "pressure_score", 0) or 0)


def _presence_level(score: float) -> str:
    if score >= 1.6:
        return "strong"
    if score >= 0.85:
        return "clear"
    if score >= 0.25:
        return "latent"
    return "weak"


def _net_fit(support_score: int, pressure_score: int) -> int:
    return int(support_score) - int(pressure_score)


def _position_reality_score(positions: list[str]) -> int:
    joined = " ".join(positions)
    score = 0
    if "month" in joined:
        score += 4
    if "day" in joined:
        score += 2
    if "hour" in joined:
        score += 1
    if "year" in joined:
        score += 1
    if "stem" in joined:
        score += 2
    if "branch" in joined:
        score += 2
    if "hidden" in joined:
        score += 1
    return score


def _visible_position_count(positions: list[str]) -> int:
    return sum(
        1
        for position in positions
        if ("stem" in position or "branch" in position) and "hidden" not in position
    )


def _root_position_count(positions: list[str]) -> int:
    return sum(1 for position in positions if "branch" in position or "hidden" in position)


def _cycle_force_index(context: dict[str, Any]) -> float:
    """Estimate whether a force can actually act, not merely exist.

    The score intentionally separates monthly fit, visible expression, and
    rooted reality.  This follows the rule that a visible 글자 can be weak
    without root, while a hidden/rooted 글자 can become decisive through
    month command or 운 activation.
    """

    presence = float(context.get("presence_score") or 0.0)
    reality = int(context.get("reality_score") or 0)
    net_fit = int(context.get("net_fit") or 0)
    visible_count = int(context.get("visible_count") or 0)
    root_count = int(context.get("root_count") or 0)
    month_bonus = 3 if any("month" in str(position) for position in list(context.get("positions") or [])) else 0
    return presence * 18 + reality + net_fit + visible_count * 1.2 + root_count * 1.8 + month_bonus


def _force_grade(value: float) -> str:
    if value >= 34:
        return "decisive"
    if value >= 24:
        return "active"
    if value >= 15:
        return "present"
    return "latent"


def _force_anchor_grade(context: dict[str, Any]) -> str:
    positions = {str(position) for position in list(context.get("positions") or []) if str(position)}
    visible_count = int(context.get("visible_count") or 0)
    root_count = int(context.get("root_count") or 0)
    if any("month" in position for position in positions) and root_count:
        return "month_rooted"
    if any("month" in position for position in positions):
        return "month_visible"
    if visible_count and root_count:
        return "rooted_visible"
    if root_count:
        return "rooted_hidden"
    if visible_count:
        return "visible_only"
    return "latent_only"


def _force_balance_context(
    *,
    relation: str,
    source_context: dict[str, Any],
    target_context: dict[str, Any],
) -> dict[str, Any]:
    source_force = _cycle_force_index(source_context)
    target_force = _cycle_force_index(target_context)
    gap = target_force - source_force
    if gap >= 8:
        balance = "target_overwhelms_source"
    elif gap >= 4:
        balance = "target_leans_stronger"
    elif gap <= -8:
        balance = "source_overwhelms_target"
    elif gap <= -4:
        balance = "source_leans_stronger"
    else:
        balance = "balanced"

    if relation == "generates":
        if balance == "target_overwhelms_source":
            effect = "generation_drains_source"
        elif balance == "source_overwhelms_target":
            effect = "generation_overfeeds_target"
        elif balance == "source_leans_stronger":
            effect = "generation_can_push"
        elif balance == "target_leans_stronger":
            effect = "generation_requires_source_support"
        else:
            effect = "generation_balanced"
    elif relation == "controls":
        if balance == "target_overwhelms_source":
            effect = "control_resisted"
        elif balance == "source_overwhelms_target":
            effect = "control_effective"
        elif balance == "source_leans_stronger":
            effect = "control_sets_boundary"
        elif balance == "target_leans_stronger":
            effect = "control_insufficient"
        else:
            effect = "control_balanced"
    else:
        effect = "force_chain_reference"

    return {
        "relation": relation,
        "source_force_index": round(source_force, 2),
        "target_force_index": round(target_force, 2),
        "force_gap": round(gap, 2),
        "source_force_grade": _force_grade(source_force),
        "target_force_grade": _force_grade(target_force),
        "source_anchor_grade": _force_anchor_grade(source_context),
        "target_anchor_grade": _force_anchor_grade(target_context),
        "balance": balance,
        "effect": effect,
        "source_visible_count": int(source_context.get("visible_count") or 0),
        "target_visible_count": int(target_context.get("visible_count") or 0),
        "source_root_count": int(source_context.get("root_count") or 0),
        "target_root_count": int(target_context.get("root_count") or 0),
    }


def _force_balance_basis_codes(force_balance: dict[str, Any]) -> list[str]:
    gap = abs(float(force_balance.get("force_gap") or 0.0))
    if gap >= 12:
        gap_grade = "wide"
    elif gap >= 6:
        gap_grade = "clear"
    else:
        gap_grade = "narrow"
    return _unique(
        [
            f"cycle_force_source_{force_balance.get('source_force_grade')}",
            f"cycle_force_target_{force_balance.get('target_force_grade')}",
            f"cycle_force_source_anchor_{force_balance.get('source_anchor_grade')}",
            f"cycle_force_target_anchor_{force_balance.get('target_anchor_grade')}",
            f"cycle_force_balance_{force_balance.get('balance')}",
            f"cycle_force_effect_{force_balance.get('effect')}",
            f"cycle_force_gap_{gap_grade}",
        ]
    )


def _single_force_context(context: dict[str, Any]) -> dict[str, Any]:
    force = _cycle_force_index(context)
    return {
        "force_index": round(force, 2),
        "force_grade": _force_grade(force),
        "anchor_grade": _force_anchor_grade(context),
        "visible_count": int(context.get("visible_count") or 0),
        "root_count": int(context.get("root_count") or 0),
        "reality_score": int(context.get("reality_score") or 0),
        "net_fit": int(context.get("net_fit") or 0),
    }


def _single_force_basis_codes(prefix: str, force_context: dict[str, Any]) -> list[str]:
    return _unique(
        [
            f"{prefix}_force_{force_context.get('force_grade')}",
            f"{prefix}_anchor_{force_context.get('anchor_grade')}",
            f"{prefix}_reality_{min(9, int(force_context.get('reality_score') or 0))}",
        ]
    )


def _role_context(chart_structure: Any, group: str) -> dict[str, Any]:
    element = _role_element(chart_structure.day_master_element, group)
    support_score, pressure_score = _fit_scores(chart_structure.month_governance_profile, group)
    element_fit = getattr(chart_structure.month_governance_profile, "element_fits", {}).get(element)
    positions = _role_positions(chart_structure.position_signals, group)
    group_score = float(chart_structure.ten_god_profile.group_scores.get(group, 0.0) or 0.0)
    reality_score = int(getattr(element_fit, "reality_score", 0) or 0) + _position_reality_score(positions)
    visible_count = _visible_position_count(positions)
    root_count = _root_position_count(positions)
    return {
        "group": group,
        "group_label": ROLE_LABELS[group],
        "element": element,
        "element_label": ELEMENT_LABELS.get(element, element),
        "support_score": support_score,
        "pressure_score": pressure_score,
        "net_fit": _net_fit(support_score, pressure_score),
        "fit_status": str(getattr(_fit(chart_structure.month_governance_profile, group), "status", "")),
        "month_authority": str(getattr(element_fit, "month_authority", "")),
        "reality_score": reality_score,
        "positions": positions,
        "presence_score": group_score,
        "presence": _presence_level(group_score),
        "visible_count": visible_count,
        "root_count": root_count,
    }


def _element_context(chart_structure: Any, element: str) -> dict[str, Any]:
    support_score, pressure_score = _element_fit_scores(chart_structure.month_governance_profile, element)
    element_fit = getattr(chart_structure.month_governance_profile, "element_fits", {}).get(element)
    score = chart_structure.element_profile.scores[element]
    positions = _element_positions(chart_structure.position_signals, element)
    reality_score = int(getattr(element_fit, "reality_score", 0) or 0) + _position_reality_score(positions)
    group = _group_for_element(chart_structure.day_master_element, element)
    return {
        "element": element,
        "element_label": ELEMENT_LABELS.get(element, element),
        "group": group,
        "group_label": ROLE_LABELS.get(group, ""),
        "support_score": support_score,
        "pressure_score": pressure_score,
        "net_fit": _net_fit(support_score, pressure_score),
        "fit_status": str(getattr(element_fit, "status", "")),
        "month_authority": str(getattr(element_fit, "month_authority", "")),
        "reality_score": reality_score,
        "positions": positions,
        "presence_score": float(getattr(score, "ratio", 0.0) or 0.0),
        "presence": _presence_level(float(getattr(score, "ratio", 0.0) or 0.0) * 5),
        "visible_count": int(getattr(score, "visible_count", 0) or 0),
        "root_count": int(getattr(score, "root_count", 0) or 0),
        "state": str(getattr(score, "state", "")),
    }


def _relation_judgment(*, relation: str, source_context: dict[str, Any], target_context: dict[str, Any]) -> str:
    source_net = int(source_context["net_fit"])
    target_net = int(target_context["net_fit"])
    source_group = str(source_context.get("group") or "")
    target_group = str(target_context.get("group") or "")
    target_reality = int(target_context.get("reality_score") or 0)
    source_force = _cycle_force_index(source_context)
    target_force = _cycle_force_index(target_context)
    source_presence = str(source_context.get("presence") or "")
    target_presence = str(target_context.get("presence") or "")

    if relation == "generates":
        if target_net <= -3 and target_force >= source_force + 4 and target_presence in {"clear", "strong"}:
            return "excessive_generation"
        if source_net <= -2 and target_force >= source_force + 4:
            return "draining_exhaustion"
        if source_presence == "weak" and target_presence in {"clear", "strong"}:
            return "draining_exhaustion"
        if target_net >= 3 and source_net >= -1:
            return "useful_generation"
        if target_net <= -3 and target_reality >= 3:
            return "burden_generation"
        if source_net <= -3:
            return "strained_generation"
        return "functional_generation"

    if source_group == "peer" and target_group == "wealth":
        if target_net <= -3 and source_net >= 0:
            return "shared_control_of_burdening_wealth"
        return "wealth_competition"
    if target_net <= -3 and source_net >= -1:
        if target_force - source_force >= 10 and source_presence == "weak":
            return "failed_control"
        return "medicinal_control"
    if target_force - source_force >= 7 and target_presence in {"clear", "strong"}:
        return "reverse_control"
    if target_force - source_force >= 4 or source_presence == "weak":
        return "failed_control"
    if target_net >= 3 and source_net <= 0:
        return "damaging_control"
    if source_net <= -3 and target_net <= -1:
        return "burden_collision"
    return "boundary_control"


def _month_command_verdict(relation: str, judgment: str) -> str:
    if relation == "generates":
        return {
            "useful_generation": "generation_supports_needed_force",
            "burden_generation": "generation_overfeeds_burden",
            "strained_generation": "generation_from_burdened_source",
            "functional_generation": "generation_connects_function",
            "excessive_generation": "generation_excessive",
            "draining_exhaustion": "generation_drains_source",
        }.get(judgment, "generation_connects_function")
    if relation == "bridge":
        return {
            "mediating_bridge": "bridge_mediates_conflict",
            "unstable_bridge": "bridge_unstable",
            "missing_bridge": "bridge_missing",
            "overloaded_bridge": "bridge_overloaded",
        }.get(judgment, "bridge_unstable")
    if relation == "exception":
        return {
            "reverse_control": "control_reversed",
            "failed_control": "control_failed",
            "excessive_generation": "generation_excessive",
            "draining_exhaustion": "generation_drains_source",
        }.get(judgment, "control_failed")
    if relation == "branch":
        return {
            "branch_combines_useful_element": "branch_combines_useful",
            "branch_combines_burden_element": "branch_combines_burden",
            "branch_disrupts_useful_element": "branch_disrupts_useful",
            "branch_disrupts_burden_element": "branch_disrupts_burden",
            "branch_mixed_cycle_activation": "branch_cycle_mixed",
        }.get(judgment, "branch_cycle_mixed")
    if relation == "stem_combine":
        return {
            "stem_combine_transforms_useful_element": "stem_combine_transforms_useful",
            "stem_combine_transforms_burden_element": "stem_combine_transforms_burden",
            "stem_combine_bound_not_transformed": "stem_combine_bound",
            "stem_combine_ties_original_force": "stem_combine_ties_force",
        }.get(judgment, "stem_combine_bound")
    if relation == "rooting":
        return {
            "hidden_protrusion_supports_cycle": "hidden_protrusion_supports",
            "hidden_protrusion_exposes_burden": "hidden_protrusion_burdens",
            "visible_root_supports_cycle": "visible_root_supports",
            "visible_root_anchors_burden": "visible_root_burdens",
            "hidden_root_potential_cycle": "hidden_root_potential",
        }.get(judgment, "hidden_root_potential")
    if relation == "chain":
        return {
            "useful_generation": "generation_supports_needed_force",
            "functional_generation": "generation_connects_function",
            "medicinal_control": "control_regulates_illness",
            "boundary_control": "control_sets_boundary",
            "damaging_control": "control_damages_medicine",
            "strained_generation": "generation_from_burdened_source",
        }.get(judgment, "control_sets_boundary")
    return {
        "medicinal_control": "control_regulates_illness",
        "damaging_control": "control_damages_medicine",
        "burden_collision": "control_collides_burdens",
        "boundary_control": "control_sets_boundary",
        "wealth_competition": "control_competes_for_wealth",
        "shared_control_of_burdening_wealth": "control_shares_burdening_wealth",
        "reverse_control": "control_reversed",
        "failed_control": "control_failed",
    }.get(judgment, "control_sets_boundary")


def _decision_reason(
    *,
    relation: str,
    source_context: dict[str, Any],
    target_context: dict[str, Any],
    judgment: str,
) -> str:
    source = f"{source_context.get('group_label')}({source_context.get('element_label')})"
    target = f"{target_context.get('group_label')}({target_context.get('element_label')})"
    source_net = int(source_context.get("net_fit") or 0)
    target_net = int(target_context.get("net_fit") or 0)
    verdict = MONTH_VERDICT_LABELS[_month_command_verdict(relation, judgment)]
    return (
        f"{source}에서 {target}으로 작용합니다. "
        f"월령 기준 순작용 차이는 출발점 {source_net}, 도착점 {target_net}입니다. "
        f"{verdict}"
    )


def _status_from_judgment(relation: str, judgment: str) -> str:
    if relation == "generates":
        return {
            "useful_generation": "feeds_useful_force",
            "burden_generation": "feeds_burden",
            "strained_generation": "mixed_generation",
            "functional_generation": "connects_function",
            "excessive_generation": "overfeeds_target",
            "draining_exhaustion": "drains_source",
        }.get(judgment, "connects_function")
    return {
        "medicinal_control": "regulates_pressure",
        "boundary_control": "sets_boundary",
        "shared_control_of_burdening_wealth": "mixed_control",
        "wealth_competition": "damages_useful_force",
        "damaging_control": "damages_useful_force",
        "burden_collision": "conflict_or_overload",
        "reverse_control": "reverse_control",
        "failed_control": "failed_control",
    }.get(judgment, "mixed_control")


def _relation_basis_codes(
    *,
    layer: str,
    relation: str,
    source_key: str,
    target_key: str,
    source_context: dict[str, Any],
    target_context: dict[str, Any],
    judgment: str,
    classical_name: str,
) -> list[str]:
    return _unique(
        [
            f"cycle_{layer}_{relation}_{source_key}_to_{target_key}",
            f"cycle_classical_{classical_name}" if classical_name else "",
            f"cycle_judgment_{judgment}",
            f"cycle_month_verdict_{_month_command_verdict(relation, judgment)}",
            f"cycle_polarity_{JUDGMENT_POLARITY.get(judgment, 'mixed')}",
            f"cycle_source_fit_{source_context.get('fit_status')}",
            f"cycle_target_fit_{target_context.get('fit_status')}",
            f"cycle_source_authority_{source_context.get('month_authority')}",
            f"cycle_target_authority_{target_context.get('month_authority')}",
            f"cycle_source_reality_{min(9, int(source_context.get('reality_score') or 0))}",
            f"cycle_target_reality_{min(9, int(target_context.get('reality_score') or 0))}",
        ]
    )


def _governance_role_tags(profile: Any, context: dict[str, Any]) -> list[str]:
    element = str(context.get("element") or "")
    group = str(context.get("group") or "")
    authority = str(context.get("month_authority") or "")
    tags: list[str] = []
    if element and element == str(getattr(profile, "month_element", "")):
        tags.append("month_branch_body")
    if group and group == str(getattr(profile, "month_command_group", "")):
        tags.append("month_command_group")
    if element and element in list(getattr(profile, "useful_elements", []) or []):
        tags.append("pattern_useful_element")
    if element and element in list(getattr(profile, "caution_elements", []) or []):
        tags.append("pattern_caution_element")
    if group and group in list(getattr(profile, "useful_groups", []) or []):
        tags.append("pattern_useful_group")
    if group and group in list(getattr(profile, "caution_groups", []) or []):
        tags.append("pattern_caution_group")
    if authority in {"month_hidden_protruded", "month_hidden_main", "month_hidden_secondary"}:
        tags.append(authority)
    return _unique(tags)


def _signal_governance_contexts(signal: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for key in ("source_context", "target_context", "bridge_context"):
        context = signal.get(key)
        if isinstance(context, dict):
            contexts.append(context)
    for context in list(signal.get("group_contexts") or []):
        if isinstance(context, dict):
            contexts.append(context)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for context in contexts:
        marker = (
            str(context.get("group") or ""),
            str(context.get("element") or ""),
            " ".join(str(position) for position in list(context.get("positions") or [])),
        )
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(context)
    return deduped


def _governance_verdict(profile: Any, contexts: list[dict[str, Any]]) -> str:
    support_total = sum(int(context.get("support_score") or 0) for context in contexts)
    pressure_total = sum(int(context.get("pressure_score") or 0) for context in contexts)
    tags = [tag for context in contexts for tag in _governance_role_tags(profile, context)]
    touches_month_command = any(tag in {"month_branch_body", "month_command_group", "month_hidden_protruded"} for tag in tags)
    touches_useful = any(tag in {"pattern_useful_element", "pattern_useful_group"} for tag in tags)
    touches_caution = any(tag in {"pattern_caution_element", "pattern_caution_group"} for tag in tags)

    if touches_useful and not touches_caution and support_total >= pressure_total:
        return "governance_supports_cycle"
    if touches_caution and not touches_useful and pressure_total >= support_total:
        return "governance_warns_cycle"
    if touches_useful and touches_caution:
        if support_total >= pressure_total + 3:
            return "governance_support_with_caution"
        if pressure_total >= support_total + 3:
            return "governance_pressure_with_use"
        return "governance_mixed_cycle"
    if touches_month_command:
        return "governance_month_command_active"
    if support_total > pressure_total:
        return "governance_auxiliary_support"
    if pressure_total > support_total:
        return "governance_auxiliary_pressure"
    return "governance_neutral_cycle"


def _signal_governance_context(chart_structure: Any, signal: dict[str, Any]) -> dict[str, Any]:
    profile = chart_structure.month_governance_profile
    contexts = _signal_governance_contexts(signal)
    context_summaries: list[dict[str, Any]] = []
    for context in contexts:
        context_summaries.append(
            {
                "group": str(context.get("group") or ""),
                "group_label": str(context.get("group_label") or ""),
                "element": str(context.get("element") or ""),
                "element_label": str(context.get("element_label") or ""),
                "fit_status": str(context.get("fit_status") or ""),
                "month_authority": str(context.get("month_authority") or ""),
                "support_score": int(context.get("support_score") or 0),
                "pressure_score": int(context.get("pressure_score") or 0),
                "reality_score": int(context.get("reality_score") or 0),
                "governance_tags": _governance_role_tags(profile, context),
            }
        )

    tags = _unique([tag for summary in context_summaries for tag in summary["governance_tags"]])
    support_total = sum(int(summary["support_score"]) for summary in context_summaries)
    pressure_total = sum(int(summary["pressure_score"]) for summary in context_summaries)
    reality_total = min(99, sum(int(summary["reality_score"]) for summary in context_summaries))
    verdict = _governance_verdict(profile, contexts)
    return {
        "month_branch": str(getattr(profile, "month_branch", "")),
        "month_element": str(getattr(profile, "month_element", "")),
        "month_command_ten_god": str(getattr(profile, "month_command_ten_god", "")),
        "month_command_group": str(getattr(profile, "month_command_group", "")),
        "regular_pattern": str(getattr(profile, "regular_pattern", "")),
        "pattern_family": str(getattr(profile, "pattern_family", "")),
        "useful_elements": list(getattr(profile, "useful_elements", []) or []),
        "caution_elements": list(getattr(profile, "caution_elements", []) or []),
        "useful_groups": list(getattr(profile, "useful_groups", []) or []),
        "caution_groups": list(getattr(profile, "caution_groups", []) or []),
        "context_summaries": context_summaries,
        "support_total": support_total,
        "pressure_total": pressure_total,
        "net_total": support_total - pressure_total,
        "reality_total": reality_total,
        "governance_tags": tags,
        "verdict": verdict,
        "touches_month_command": any(tag in {"month_branch_body", "month_command_group", "month_hidden_protruded"} for tag in tags),
        "touches_useful": any(tag in {"pattern_useful_element", "pattern_useful_group"} for tag in tags),
        "touches_caution": any(tag in {"pattern_caution_element", "pattern_caution_group"} for tag in tags),
    }


def _governance_basis_codes(governance: dict[str, Any]) -> list[str]:
    codes = [
        f"cycle_governance_month_command_{governance.get('month_command_ten_god')}",
        f"cycle_governance_month_group_{governance.get('month_command_group')}",
        f"cycle_governance_month_branch_{governance.get('month_branch')}",
        f"cycle_governance_regular_pattern_{governance.get('regular_pattern')}",
        f"cycle_governance_pattern_family_{governance.get('pattern_family')}",
        f"cycle_governance_verdict_{governance.get('verdict')}",
        f"cycle_governance_net_{max(-9, min(9, int(governance.get('net_total') or 0)))}",
        f"cycle_governance_reality_{min(9, int(governance.get('reality_total') or 0))}",
    ]
    codes.extend(f"cycle_governance_tag_{tag}" for tag in list(governance.get("governance_tags") or [])[:8])
    codes.extend(f"cycle_governance_useful_{element}" for element in list(governance.get("useful_elements") or [])[:4])
    codes.extend(f"cycle_governance_caution_{element}" for element in list(governance.get("caution_elements") or [])[:4])
    return _unique([str(code) for code in codes if str(code) and not str(code).endswith("_")])


def _cycle_relation_kind(signal: dict[str, Any]) -> str:
    relation = str(signal.get("relation") or "")
    if relation in {"generates", "element_generates"}:
        return "generates"
    if relation in {"controls", "element_controls"}:
        return "controls"
    return relation


def _pattern_rule_matches(signal: dict[str, Any], rule: dict[str, Any]) -> bool:
    signal_id = str(signal.get("signal_id") or "")
    if signal_id and signal_id in set(rule.get("signal_ids") or ()):
        return True

    relation_kind = _cycle_relation_kind(signal)
    source_group = str(signal.get("source_group") or "")
    target_group = str(signal.get("target_group") or "")
    edge = (source_group, target_group, relation_kind)
    if edge in set(rule.get("edges") or ()):
        return True

    groups = tuple(str(group) for group in list(signal.get("groups") or []))
    if groups and groups in set(rule.get("group_sequences") or ()):
        return True
    return False


def _pattern_rule_weight(signal: dict[str, Any], rule: dict[str, Any]) -> float:
    weight = 0.0
    signal_id = str(signal.get("signal_id") or "")
    if signal_id and signal_id in set(rule.get("signal_ids") or ()):
        weight += 2.0

    relation_kind = _cycle_relation_kind(signal)
    source_group = str(signal.get("source_group") or "")
    target_group = str(signal.get("target_group") or "")
    if (source_group, target_group, relation_kind) in set(rule.get("edges") or ()):
        weight += 1.4

    groups = tuple(str(group) for group in list(signal.get("groups") or []))
    if groups and groups in set(rule.get("group_sequences") or ()):
        weight += 1.2

    return weight or 1.0


def _pattern_cycle_reality_context(profile: Any, signal: dict[str, Any]) -> dict[str, Any]:
    contexts = _signal_governance_contexts(signal)
    positions = _unique(
        [
            str(position)
            for context in contexts
            for position in list(context.get("positions") or [])
            if str(position)
        ]
    )
    tags = _unique([tag for context in contexts for tag in _governance_role_tags(profile, context)])
    reality_total = min(99, sum(int(context.get("reality_score") or 0) for context in contexts))
    max_reality = max([int(context.get("reality_score") or 0) for context in contexts] or [0])
    has_month = any("month" in position for position in positions) or any(
        tag in {"month_branch_body", "month_command_group", "month_hidden_protruded"} for tag in tags
    )
    has_stem = any("stem" in position for position in positions)
    has_branch = any("branch" in position for position in positions)
    has_hidden = any("hidden" in position for position in positions)

    if has_month and has_stem:
        grade = "month_visible"
    elif has_month and (has_branch or has_hidden):
        grade = "month_rooted"
    elif has_stem and (has_branch or has_hidden):
        grade = "rooted_visible"
    elif has_stem:
        grade = "visible"
    elif has_branch or has_hidden:
        grade = "rooted_or_hidden"
    else:
        grade = "weak"

    return {
        "positions": positions,
        "governance_tags": tags,
        "reality_total": reality_total,
        "max_reality": max_reality,
        "reality_grade": grade,
        "touches_month": has_month,
        "has_visible_stem": has_stem,
        "has_branch_body": has_branch,
        "has_hidden_root": has_hidden,
    }


def _pattern_cycle_context(chart_structure: Any, signal: dict[str, Any]) -> dict[str, Any]:
    regular_pattern = str(getattr(chart_structure.pattern_profile, "regular_pattern", "") or "")
    month_command = str(getattr(chart_structure.pattern_profile, "month_command_ten_god", "") or "")
    profile = chart_structure.month_governance_profile
    rules = REGULAR_PATTERN_CYCLE_RULES.get(regular_pattern, [])
    matched = [rule for rule in rules if _pattern_rule_matches(signal, rule)]
    support_rules = [rule for rule in matched if rule.get("role") == "support"]
    caution_rules = [rule for rule in matched if rule.get("role") == "caution"]
    reality = _pattern_cycle_reality_context(profile, signal)
    reality_bonus = 0.0
    if reality["touches_month"]:
        reality_bonus += 1.0
    if reality["reality_grade"] in {"month_visible", "month_rooted"}:
        reality_bonus += 0.8
    elif reality["reality_grade"] == "rooted_visible":
        reality_bonus += 0.5
    elif reality["reality_grade"] == "visible":
        reality_bonus += 0.3
    if int(reality["max_reality"]) >= 8:
        reality_bonus += 0.5
    elif int(reality["max_reality"]) >= 5:
        reality_bonus += 0.25
    support_strength = sum(_pattern_rule_weight(signal, rule) for rule in support_rules)
    caution_strength = sum(_pattern_rule_weight(signal, rule) for rule in caution_rules)
    if support_strength:
        support_strength += reality_bonus
    if caution_strength:
        caution_strength += reality_bonus

    if support_rules and caution_rules:
        verdict = "pattern_cycle_support_and_caution"
    elif support_rules:
        verdict = "pattern_cycle_support"
    elif caution_rules:
        verdict = "pattern_cycle_caution"
    elif regular_pattern:
        verdict = "pattern_cycle_not_primary"
    else:
        verdict = "pattern_cycle_no_regular_pattern"

    return {
        "regular_pattern": regular_pattern,
        "month_command_ten_god": month_command,
        "matched_rule_keys": [str(rule.get("key") or "") for rule in matched],
        "support_rule_keys": [str(rule.get("key") or "") for rule in support_rules],
        "caution_rule_keys": [str(rule.get("key") or "") for rule in caution_rules],
        "verdict": verdict,
        "support_strength": round(support_strength, 2),
        "caution_strength": round(caution_strength, 2),
        "reality_grade": str(reality["reality_grade"]),
        "reality_total": int(reality["reality_total"]),
        "max_reality": int(reality["max_reality"]),
        "touches_month": bool(reality["touches_month"]),
        "has_visible_stem": bool(reality["has_visible_stem"]),
        "has_branch_body": bool(reality["has_branch_body"]),
        "has_hidden_root": bool(reality["has_hidden_root"]),
        "reality_positions": list(reality["positions"]),
        "support_reasons": [str(rule.get("reason") or "") for rule in support_rules],
        "caution_reasons": [str(rule.get("reason") or "") for rule in caution_rules],
    }


def _pattern_cycle_basis_codes(pattern_cycle: dict[str, Any]) -> list[str]:
    regular_pattern = str(pattern_cycle.get("regular_pattern") or "")
    if not regular_pattern:
        return []
    codes = [
        f"cycle_pattern_regular_{regular_pattern}",
        f"cycle_pattern_month_command_{pattern_cycle.get('month_command_ten_god')}",
        f"cycle_pattern_verdict_{pattern_cycle.get('verdict')}",
        f"cycle_pattern_reality_{pattern_cycle.get('reality_grade')}",
        f"cycle_pattern_support_strength_{min(9, int(round(float(pattern_cycle.get('support_strength') or 0))))}",
        f"cycle_pattern_caution_strength_{min(9, int(round(float(pattern_cycle.get('caution_strength') or 0))))}",
    ]
    codes.extend(f"cycle_pattern_rule_{key}" for key in list(pattern_cycle.get("matched_rule_keys") or []))
    codes.extend(f"cycle_pattern_support_{key}" for key in list(pattern_cycle.get("support_rule_keys") or []))
    codes.extend(f"cycle_pattern_caution_{key}" for key in list(pattern_cycle.get("caution_rule_keys") or []))
    return _unique([str(code) for code in codes if str(code) and not str(code).endswith("_")])


def _signal_elements(signal: dict[str, Any]) -> set[str]:
    elements = {
        str(signal.get("source_element") or ""),
        str(signal.get("target_element") or ""),
        str(signal.get("bridge_element") or ""),
        str(signal.get("transform_element") or ""),
    }
    elements.update(str(element) for element in list(signal.get("elements") or []) if str(element))
    elements.update(str(element) for element in list(signal.get("activated_elements") or []) if str(element))
    for context in _signal_governance_contexts(signal):
        element = str(context.get("element") or "")
        if element:
            elements.add(element)
    return {element for element in elements if element}


def _signal_groups(signal: dict[str, Any]) -> set[str]:
    groups = {
        str(signal.get("source_group") or ""),
        str(signal.get("target_group") or ""),
        str(signal.get("bridge_group") or ""),
        str(signal.get("transform_group") or ""),
    }
    groups.update(str(group) for group in list(signal.get("groups") or []) if str(group))
    groups.update(str(group) for group in list(signal.get("activated_groups") or []) if str(group))
    groups.update(str(group) for group in list(signal.get("original_groups") or []) if str(group))
    for context in _signal_governance_contexts(signal):
        group = str(context.get("group") or "")
        if group:
            groups.add(group)
    return {group for group in groups if group}


def _branch_reality_context(chart_structure: Any, signal: dict[str, Any]) -> dict[str, Any]:
    elements = _signal_elements(signal)
    groups = _signal_groups(signal)
    details: list[dict[str, Any]] = []
    branch_score = 0.0
    hidden_score = 0.0
    protruded_hidden_score = 0.0
    stem_score = 0.0
    month_branch_score = 0.0
    day_branch_score = 0.0

    for position, position_signal in chart_structure.position_signals.items():
        position_key = str(position)
        position_weight = BRANCH_REALITY_POSITION_WEIGHTS.get(position_key, 1.0)
        stem_weight = STEM_VISIBILITY_POSITION_WEIGHTS.get(position_key, 1.0)
        branch_key = str(getattr(position_signal, "branch_key", ""))
        position_score = 0.0
        matched_layers: list[str] = []
        matched_elements: list[str] = []
        matched_groups: list[str] = []

        stem_element = str(getattr(position_signal, "stem_element", ""))
        stem_group = _group_for_element(chart_structure.day_master_element, stem_element)
        if stem_element in elements or stem_group in groups:
            layer_score = stem_weight
            stem_score += layer_score
            position_score += layer_score
            matched_layers.append("visible_stem")
            if stem_element:
                matched_elements.append(stem_element)
            if stem_group:
                matched_groups.append(stem_group)

        branch_element = str(getattr(position_signal, "branch_element", ""))
        branch_group = _group_for_element(chart_structure.day_master_element, branch_element)
        if branch_element in elements or branch_group in groups:
            layer_score = position_weight * 0.9
            branch_score += layer_score
            position_score += layer_score
            matched_layers.append("branch_body")
            if branch_element:
                matched_elements.append(branch_element)
            if branch_group:
                matched_groups.append(branch_group)

        for stem_key, hidden_weight in BRANCH_HIDDEN_STEMS.get(branch_key, []):
            hidden_element = STEM_METADATA[stem_key]["element"]
            hidden_group = _group_for_element(chart_structure.day_master_element, hidden_element)
            if hidden_element not in elements and hidden_group not in groups:
                continue
            hidden_weight_value = float(hidden_weight or 0.0)
            is_protruded = stem_key in list(getattr(position_signal, "protruded_hidden_stems", []) or [])
            layer_score = position_weight * (0.35 + hidden_weight_value)
            if is_protruded:
                layer_score += position_weight * 0.35
                protruded_hidden_score += layer_score
            hidden_score += layer_score
            position_score += layer_score
            matched_layers.append("hidden_stem_protruded" if is_protruded else "hidden_stem")
            matched_elements.append(hidden_element)
            matched_groups.append(hidden_group)

        if position_score <= 0:
            continue
        if position_key == "month":
            month_branch_score += position_score
        if position_key == "day":
            day_branch_score += position_score
        details.append(
            {
                "position": position_key,
                "branch": branch_key,
                "score": round(position_score, 2),
                "layers": _unique(matched_layers),
                "elements": _unique(matched_elements),
                "groups": _unique(matched_groups),
                "domains": list(getattr(position_signal, "domains", []) or []),
            }
        )

    branch_total = branch_score + hidden_score
    total = branch_total + stem_score
    branch_ratio = round(branch_total / total, 3) if total else 0.0
    top_positions = [
        str(detail["position"])
        for detail in sorted(details, key=lambda item: float(item.get("score") or 0.0), reverse=True)[:4]
    ]

    if month_branch_score >= 8 and stem_score >= 2:
        grade = "month_branch_visible"
    elif month_branch_score >= 6 and protruded_hidden_score > 0:
        grade = "month_hidden_protruded"
    elif branch_total >= 11 and branch_ratio >= 0.62:
        grade = "branch_dominant"
    elif hidden_score >= 5 and stem_score >= 2:
        grade = "hidden_to_visible"
    elif branch_total >= 5:
        grade = "branch_rooted"
    elif stem_score >= 3:
        grade = "stem_visible_only"
    else:
        grade = "weak_reality"

    return {
        "grade": grade,
        "branch_score": round(branch_score, 2),
        "hidden_score": round(hidden_score, 2),
        "protruded_hidden_score": round(protruded_hidden_score, 2),
        "stem_score": round(stem_score, 2),
        "month_branch_score": round(month_branch_score, 2),
        "day_branch_score": round(day_branch_score, 2),
        "branch_ratio": branch_ratio,
        "top_positions": top_positions,
        "details": details,
    }


def _branch_reality_basis_codes(branch_reality: dict[str, Any]) -> list[str]:
    codes = [
        f"cycle_branch_reality_grade_{branch_reality.get('grade')}",
        f"cycle_branch_reality_ratio_{min(9, int(round(float(branch_reality.get('branch_ratio') or 0.0) * 10)))}",
        f"cycle_branch_reality_branch_{min(9, int(round(float(branch_reality.get('branch_score') or 0.0))))}",
        f"cycle_branch_reality_hidden_{min(9, int(round(float(branch_reality.get('hidden_score') or 0.0))))}",
        f"cycle_branch_reality_stem_{min(9, int(round(float(branch_reality.get('stem_score') or 0.0))))}",
    ]
    codes.extend(f"cycle_branch_reality_position_{position}" for position in list(branch_reality.get("top_positions") or [])[:4])
    return _unique([str(code) for code in codes if str(code) and not str(code).endswith("_")])


def _strength_condition_tags(chart_structure: Any, signal: dict[str, Any]) -> tuple[list[str], list[str]]:
    strength = str(chart_structure.element_profile.day_master_strength)
    groups = _signal_groups(signal)
    signal_id = str(signal.get("signal_id") or "")
    support: list[str] = []
    pressure: list[str] = []

    if strength in {"weak", "very_weak"}:
        if groups & {"resource", "peer"}:
            support.append("weak_day_master_needs_root_or_resource")
        if groups & {"wealth", "officer"}:
            pressure.append("weak_day_master_wealth_officer_cost")
        if {"output", "wealth"}.issubset(groups) or signal_id == "output_generates_wealth_then_officer":
            pressure.append("weak_day_master_output_to_wealth_cost")
    elif strength in {"strong", "very_strong"}:
        if groups & {"output", "wealth", "officer"}:
            support.append("strong_day_master_uses_output_wealth_officer")
        if groups & {"resource", "peer"}:
            pressure.append("strong_day_master_peer_resource_overfeeds")
    else:
        if groups & {"output", "wealth", "officer"}:
            support.append("balanced_day_master_uses_functional_cycle")
    return support, pressure


def _climate_condition_tags(chart_structure: Any, signal: dict[str, Any]) -> tuple[list[str], list[str]]:
    climate_needs = set(str(element) for element in list(chart_structure.element_profile.climate_needs or []) if str(element))
    if not climate_needs:
        return [], []

    elements = _signal_elements(signal)
    relation_kind = _cycle_relation_kind(signal)
    target_element = str(signal.get("target_element") or "")
    bridge_element = str(signal.get("bridge_element") or "")
    transform_element = str(signal.get("transform_element") or "")
    support: list[str] = []
    pressure: list[str] = []

    touched = sorted(elements & climate_needs)
    if touched:
        support.extend(f"climate_medicine_present_{element}" for element in touched)
    if relation_kind == "generates" and target_element in climate_needs:
        support.append(f"climate_medicine_generated_{target_element}")
    if relation_kind == "controls" and target_element in climate_needs:
        pressure.append(f"climate_medicine_controlled_{target_element}")
    if bridge_element in climate_needs:
        support.append(f"climate_medicine_bridge_{bridge_element}")
    if transform_element in climate_needs:
        support.append(f"climate_medicine_transformed_{transform_element}")
    if str(signal.get("cycle_judgment") or "") in {"damaging_control", "draining_exhaustion"} and climate_needs & elements:
        pressure.append("climate_medicine_under_stress")
    return support, pressure


def _branch_condition_tags(chart_structure: Any, signal: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    elements = _signal_elements(signal)
    support: list[str] = []
    pressure: list[str] = []
    details: list[dict[str, Any]] = []
    if not elements:
        return support, pressure, details

    for interaction in list(getattr(chart_structure, "branch_interactions", []) or []):
        activated = set(relation_activated_elements(interaction))
        matched = sorted(activated & elements)
        if not matched:
            continue
        polarity = branch_relation_polarity(
            chart_structure.element_profile,
            interaction,
            getattr(chart_structure, "pattern_profile", None),
        )
        relation_type = str(getattr(interaction, "relation_type", ""))
        if relation_type in COMBINE_RELATIONS:
            if polarity.polarity == "supportive":
                support.append(f"branch_combine_supports_{'_'.join(matched)}")
            elif polarity.polarity == "burdensome":
                pressure.append(f"branch_combine_burdens_{'_'.join(matched)}")
            elif polarity.polarity == "mixed":
                support.append(f"branch_combine_mixed_{'_'.join(matched)}")
                pressure.append(f"branch_combine_mixed_{'_'.join(matched)}")
        elif relation_type in DISRUPTIVE_RELATIONS:
            if polarity.polarity == "supportive":
                support.append(f"branch_disruption_releases_burden_{'_'.join(matched)}")
                pressure.append(f"branch_disruption_structural_friction_{'_'.join(matched)}")
            elif polarity.polarity == "burdensome":
                pressure.append(f"branch_disruption_damages_useful_{'_'.join(matched)}")
            elif polarity.polarity == "mixed":
                support.append(f"branch_disruption_mixed_{'_'.join(matched)}")
                pressure.append(f"branch_disruption_mixed_{'_'.join(matched)}")
        details.append(
            {
                "relation_type": relation_type,
                "positions": list(getattr(interaction, "positions", []) or []),
                "matched_elements": matched,
                "polarity": polarity.polarity,
                "intrinsic_friction": polarity.intrinsic_friction,
                "effective_friction": polarity.effective_friction,
                "intensity": str(getattr(interaction, "intensity", "")),
                "basis_code": str(getattr(interaction, "basis_code", "")),
            }
        )
    return _unique(support), _unique(pressure), details


def _condition_verdict(support_tags: list[str], pressure_tags: list[str]) -> str:
    if support_tags and pressure_tags:
        if len(support_tags) >= len(pressure_tags) + 2:
            return "condition_support_with_cost"
        if len(pressure_tags) >= len(support_tags) + 2:
            return "condition_pressure_with_use"
        return "condition_mixed_cycle"
    if support_tags:
        return "condition_supports_cycle"
    if pressure_tags:
        return "condition_pressures_cycle"
    return "condition_neutral_cycle"


def _condition_context(chart_structure: Any, signal: dict[str, Any]) -> dict[str, Any]:
    strength_support, strength_pressure = _strength_condition_tags(chart_structure, signal)
    climate_support, climate_pressure = _climate_condition_tags(chart_structure, signal)
    branch_support, branch_pressure, branch_details = _branch_condition_tags(chart_structure, signal)
    support_tags = _unique([*strength_support, *climate_support, *branch_support])
    pressure_tags = _unique([*strength_pressure, *climate_pressure, *branch_pressure])
    return {
        "day_master_strength": str(chart_structure.element_profile.day_master_strength),
        "day_master_strength_score": int(chart_structure.element_profile.day_master_strength_score),
        "temperature_balance": str(chart_structure.element_profile.temperature_balance),
        "moisture_balance": str(chart_structure.element_profile.moisture_balance),
        "climate_needs": list(chart_structure.element_profile.climate_needs or []),
        "signal_elements": sorted(_signal_elements(signal)),
        "signal_groups": sorted(_signal_groups(signal)),
        "support_tags": support_tags,
        "pressure_tags": pressure_tags,
        "branch_details": branch_details,
        "verdict": _condition_verdict(support_tags, pressure_tags),
        "net_condition": len(support_tags) - len(pressure_tags),
    }


def _condition_basis_codes(condition: dict[str, Any]) -> list[str]:
    codes = [
        f"cycle_condition_strength_{condition.get('day_master_strength')}",
        f"cycle_condition_temperature_{condition.get('temperature_balance')}",
        f"cycle_condition_moisture_{condition.get('moisture_balance')}",
        f"cycle_condition_verdict_{condition.get('verdict')}",
        f"cycle_condition_net_{max(-9, min(9, int(condition.get('net_condition') or 0)))}",
    ]
    codes.extend(f"cycle_condition_climate_need_{element}" for element in list(condition.get("climate_needs") or []))
    codes.extend(f"cycle_condition_support_{tag}" for tag in list(condition.get("support_tags") or [])[:8])
    codes.extend(f"cycle_condition_pressure_{tag}" for tag in list(condition.get("pressure_tags") or [])[:8])
    for detail in list(condition.get("branch_details") or [])[:5]:
        relation_type = str(detail.get("relation_type") or "")
        matched = "_".join(str(element) for element in list(detail.get("matched_elements") or []))
        polarity = str(detail.get("polarity") or "")
        if relation_type and matched:
            codes.append(f"cycle_condition_branch_{relation_type}_{matched}_{polarity}")
    return _unique([str(code) for code in codes if str(code) and not str(code).endswith("_")])


def _context_for_group(contexts: list[dict[str, Any]], group: str) -> dict[str, Any]:
    for context in contexts:
        if str(context.get("group") or "") == group:
            return context
    return {}


def _cycle_focus_groups(signal: dict[str, Any]) -> tuple[str, str]:
    groups = [str(group) for group in list(signal.get("groups") or []) if str(group)]
    signal_id = str(signal.get("signal_id") or "")
    source_group = str(signal.get("source_group") or "")
    target_group = str(signal.get("target_group") or "")
    if groups:
        source_group = source_group or groups[0]
        target_index = CHAIN_DECISION_TARGET_INDEX.get(signal_id, -1)
        try:
            target_group = target_group or groups[target_index]
        except IndexError:
            target_group = target_group or groups[-1]
    return source_group, target_group


def _cycle_relation_family(signal: dict[str, Any]) -> str:
    relation = str(signal.get("relation") or "")
    if relation == "chain":
        return "chain"
    if relation in {"generates", "element_generates"}:
        return "generates"
    if relation in {"controls", "element_controls"}:
        return "controls"
    if relation == "element_bridge":
        return "bridge"
    if relation == "element_exception":
        return "exception"
    return relation


def _cycle_edge_relations(signal: dict[str, Any]) -> list[tuple[str, str, str]]:
    signal_id = str(signal.get("signal_id") or "")
    mapped = CHAIN_EDGE_RELATIONS.get(signal_id)
    if mapped:
        return list(mapped)

    relation_family = _cycle_relation_family(signal)
    source_group, target_group = _cycle_focus_groups(signal)
    if source_group and target_group and relation_family in {"generates", "controls"}:
        return [(source_group, target_group, relation_family)]
    return []


def _pattern_edge_roles(chart_structure: Any, signal: dict[str, Any], edge: tuple[str, str, str]) -> tuple[list[str], list[str]]:
    regular_pattern = str(getattr(chart_structure.pattern_profile, "regular_pattern", "") or "")
    rules = REGULAR_PATTERN_CYCLE_RULES.get(regular_pattern, [])
    signal_id = str(signal.get("signal_id") or "")
    support: list[str] = []
    caution: list[str] = []
    for rule in rules:
        rule_edges = set(rule.get("edges") or ())
        edge_match = edge in rule_edges
        signal_match = bool(signal_id and signal_id in set(rule.get("signal_ids") or ()) and not rule_edges)
        if not edge_match and not signal_match:
            continue
        role = str(rule.get("role") or "")
        reason = str(rule.get("reason") or "")
        if role == "support":
            support.append(reason)
        elif role == "caution":
            caution.append(reason)
    return _unique(support), _unique(caution)


def _positions_touch_month(positions: list[str]) -> bool:
    return any("month" in str(position) for position in positions)


def _positions_have_visible_axis(positions: list[str]) -> bool:
    return any(("stem" in str(position) or "branch" in str(position)) and "hidden" not in str(position) for position in positions)


def _edge_reality_context(source_context: dict[str, Any], target_context: dict[str, Any]) -> dict[str, Any]:
    source_positions = [str(position) for position in list(source_context.get("positions") or [])]
    target_positions = [str(position) for position in list(target_context.get("positions") or [])]
    source_reality = int(source_context.get("reality_score") or 0)
    target_reality = int(target_context.get("reality_score") or 0)
    source_touches_month = _positions_touch_month(source_positions)
    target_touches_month = _positions_touch_month(target_positions)
    source_visible = _positions_have_visible_axis(source_positions)
    target_visible = _positions_have_visible_axis(target_positions)
    edge_reality_score = min(99, source_reality + target_reality)

    if (
        (source_touches_month or target_touches_month)
        and source_reality >= 7
        and target_reality >= 7
        and (source_visible or target_visible)
    ):
        grade = "month_visible_edge"
    elif source_reality >= 7 and target_reality >= 7:
        grade = "rooted_edge"
    elif (source_reality >= 7 and target_reality >= 4) or (target_reality >= 7 and source_reality >= 4):
        grade = "one_sided_edge"
    elif source_reality >= 4 and target_reality >= 4:
        grade = "subtle_edge"
    else:
        grade = "latent_edge"

    return {
        "source_reality": source_reality,
        "target_reality": target_reality,
        "source_positions": source_positions,
        "target_positions": target_positions,
        "source_touches_month": source_touches_month,
        "target_touches_month": target_touches_month,
        "source_visible": source_visible,
        "target_visible": target_visible,
        "edge_reality_score": edge_reality_score,
        "edge_reality_grade": grade,
    }


def _edge_fit_context(
    chart_structure: Any,
    signal: dict[str, Any],
    contexts: list[dict[str, Any]],
    edge: tuple[str, str, str],
) -> dict[str, Any]:
    source_group, target_group, relation = edge
    source_context = _context_for_group(contexts, source_group)
    target_context = _context_for_group(contexts, target_group)
    source_support = int(source_context.get("support_score") or 0)
    source_pressure = int(source_context.get("pressure_score") or 0)
    target_support = int(target_context.get("support_score") or 0)
    target_pressure = int(target_context.get("pressure_score") or 0)
    source_net = source_support - source_pressure
    target_net = target_support - target_pressure
    reality = _edge_reality_context(source_context, target_context)
    profile = chart_structure.month_governance_profile
    month_group = str(getattr(profile, "month_command_group", "") or "")
    useful_groups = set(str(group) for group in list(getattr(profile, "useful_groups", []) or []))
    caution_groups = set(str(group) for group in list(getattr(profile, "caution_groups", []) or []))

    support = 0
    pressure = 0
    reasons: list[str] = []
    caution_reasons: list[str] = []

    if source_net > 0:
        support += min(2, max(1, source_net // 3))
    elif source_net < 0:
        pressure += min(2, max(1, abs(source_net) // 3))
    if target_net > 0:
        support += min(3, max(1, target_net // 2))
    elif target_net < 0:
        pressure += min(3, max(1, abs(target_net) // 2))

    if source_group == month_group or target_group == month_group:
        if (source_group == month_group and source_net >= 0) or (target_group == month_group and target_net >= 0):
            support += 3
            reasons.append("월령 본기와 직접 닿는 간선입니다.")
        else:
            pressure += 3
            caution_reasons.append("월령 본기와 닿지만 부담 점수가 더 큽니다.")

    if source_group in useful_groups:
        support += 1
    if target_group in useful_groups:
        support += 2
    if source_group in caution_groups and source_pressure > source_support:
        pressure += 1
    if target_group in caution_groups and target_pressure > target_support:
        pressure += 2

    edge_reality_grade = str(reality["edge_reality_grade"])
    if edge_reality_grade == "month_visible_edge":
        support += 2
    elif edge_reality_grade == "rooted_edge":
        support += 1
    elif edge_reality_grade == "one_sided_edge":
        pressure += 1
    elif edge_reality_grade == "latent_edge":
        pressure += 2

    if relation == "generates":
        if target_net >= 3 and source_net >= -1:
            support += 4
            reasons.append("생을 받는 쪽이 월령 기준에서 필요한 역할입니다.")
        elif target_net <= -3:
            pressure += 4
            caution_reasons.append("생을 받는 쪽이 월령 기준에서 부담으로 커질 수 있습니다.")
        if source_net <= -3:
            pressure += 2
            caution_reasons.append("생하는 쪽의 설기 비용이 큽니다.")
    elif relation == "controls":
        if target_net <= -3 and source_net >= -1:
            support += 5
            reasons.append("부담 기운을 제어하는 간선입니다.")
        elif target_net >= 3 and source_net <= 0:
            pressure += 5
            caution_reasons.append("필요한 기운을 손상할 수 있는 간선입니다.")
        else:
            support += 1
            pressure += 1

    pattern_support, pattern_caution = _pattern_edge_roles(chart_structure, signal, edge)
    if pattern_support:
        support += 5
        reasons.extend(pattern_support)
    if pattern_caution:
        pressure += 5
        caution_reasons.extend(pattern_caution)

    net = support - pressure
    if support >= pressure + 6 and support >= 8:
        verdict = "edge_needed"
    elif support >= pressure + 2 and support >= 5:
        verdict = "edge_useful_with_cost" if pressure >= 4 else "edge_useful"
    elif pressure >= support + 6 and pressure >= 8:
        verdict = "edge_burdens_month"
    elif pressure >= support + 2 and pressure >= 5:
        verdict = "edge_pressure_with_use" if support >= 4 else "edge_pressure"
    else:
        verdict = "edge_mixed"

    if verdict == "edge_needed" and edge_reality_grade in {"latent_edge", "one_sided_edge"}:
        verdict = "edge_useful_with_cost"
        caution_reasons.append("cycle edge is useful but its source and target are not equally established")

    return {
        "source_group": source_group,
        "target_group": target_group,
        "relation": relation,
        "source_net": source_net,
        "target_net": target_net,
        **reality,
        "support_score": support,
        "pressure_score": pressure,
        "net_score": net,
        "verdict": verdict,
        "touches_month_command": source_group == month_group or target_group == month_group,
        "uses_pattern_support": bool(pattern_support),
        "uses_pattern_caution": bool(pattern_caution),
        "reasons": _unique(reasons)[:3],
        "caution_reasons": _unique(caution_reasons)[:3],
    }


def _month_cycle_fit_context(
    chart_structure: Any,
    signal: dict[str, Any],
    governance: dict[str, Any],
    pattern_cycle: dict[str, Any],
    condition: dict[str, Any],
    branch_reality: dict[str, Any],
) -> dict[str, Any]:
    profile = chart_structure.month_governance_profile
    contexts = _signal_governance_contexts(signal)
    source_group, target_group = _cycle_focus_groups(signal)
    source_context = _context_for_group(contexts, source_group)
    target_context = _context_for_group(contexts, target_group)
    relation_family = _cycle_relation_family(signal)
    edge_contexts = [
        _edge_fit_context(chart_structure, signal, contexts, edge)
        for edge in _cycle_edge_relations(signal)
    ]

    source_support = int(source_context.get("support_score") or 0)
    source_pressure = int(source_context.get("pressure_score") or 0)
    target_support = int(target_context.get("support_score") or 0)
    target_pressure = int(target_context.get("pressure_score") or 0)
    source_net = source_support - source_pressure
    target_net = target_support - target_pressure
    month_group = str(getattr(profile, "month_command_group", "") or "")
    useful_groups = set(str(group) for group in list(getattr(profile, "useful_groups", []) or []))
    caution_groups = set(str(group) for group in list(getattr(profile, "caution_groups", []) or []))

    support = 0
    pressure = 0
    reasons: list[str] = []
    caution_reasons: list[str] = []

    governance_net = int(governance.get("net_total") or 0)
    if governance_net > 0:
        support += min(3, max(1, governance_net // 3))
    elif governance_net < 0:
        pressure += min(3, max(1, abs(governance_net) // 3))

    if relation_family == "chain" and edge_contexts:
        edge_support_total = sum(int(edge.get("support_score") or 0) for edge in edge_contexts)
        edge_pressure_total = sum(int(edge.get("pressure_score") or 0) for edge in edge_contexts)
        support += min(18, edge_support_total)
        pressure += min(18, edge_pressure_total)
        for edge in edge_contexts:
            reasons.extend(str(reason) for reason in list(edge.get("reasons") or []) if str(reason))
            caution_reasons.extend(str(reason) for reason in list(edge.get("caution_reasons") or []) if str(reason))
    else:
        if source_net > 0:
            support += min(3, max(1, source_net // 2))
        elif source_net < 0:
            pressure += min(3, max(1, abs(source_net) // 2))
        if target_net > 0:
            support += min(4, max(1, target_net // 2))
        elif target_net < 0:
            pressure += min(4, max(1, abs(target_net) // 2))

    pattern_support = float(pattern_cycle.get("support_strength") or 0.0)
    pattern_caution = float(pattern_cycle.get("caution_strength") or 0.0)
    if pattern_support and not (relation_family == "chain" and edge_contexts):
        support += int(round(pattern_support * 1.8))
        reasons.extend(str(reason) for reason in list(pattern_cycle.get("support_reasons") or []) if str(reason))
    if pattern_caution and not (relation_family == "chain" and edge_contexts):
        pressure += int(round(pattern_caution * 1.8))
        caution_reasons.extend(str(reason) for reason in list(pattern_cycle.get("caution_reasons") or []) if str(reason))

    if source_group == month_group or target_group == month_group:
        if (source_group == month_group and source_net >= 0) or (target_group == month_group and target_net >= 0):
            support += 3
            reasons.append("월령 본기와 직접 닿아 실제 작용력이 있습니다.")
        else:
            pressure += 3
            caution_reasons.append("월령 본기를 건드리지만 부담 쪽 점수가 더 큽니다.")

    if source_group in useful_groups:
        support += 2
    if target_group in useful_groups:
        support += 3
    if source_group in caution_groups and source_pressure > source_support:
        pressure += 2
    if target_group in caution_groups and target_pressure > target_support:
        pressure += 3

    if relation_family == "generates":
        if target_net >= 3 and source_net >= -1:
            support += 4
            reasons.append("생을 받는 쪽이 월령 기준에서 필요한 역할입니다.")
        elif target_net <= -3:
            pressure += 4
            caution_reasons.append("생을 받는 쪽이 월령 기준에서 부담으로 커질 수 있습니다.")
        if source_net <= -3:
            pressure += 2
            caution_reasons.append("생하는 쪽이 약하거나 부담이면 설기 비용이 붙습니다.")
    elif relation_family == "controls":
        if target_net <= -3 and source_net >= -1:
            support += 5
            reasons.append("극을 받는 쪽이 부담 기운이라 제어 작용으로 쓸 수 있습니다.")
        elif target_net >= 3 and source_net <= 0:
            pressure += 5
            caution_reasons.append("필요한 기운을 극하는 형태라 손상으로 나타날 수 있습니다.")
        else:
            support += 1
            pressure += 1
    elif relation_family == "chain":
        if pattern_support and not pattern_caution:
            support += 4
        if pattern_caution:
            pressure += 4
        if str(signal.get("cycle_judgment") or "") in {"medicinal_control", "useful_generation", "functional_generation"}:
            support += 2
        if str(signal.get("cycle_judgment") or "") in {"damaging_control", "burden_generation", "wealth_competition"}:
            pressure += 2
    elif relation_family == "bridge":
        if str(signal.get("cycle_judgment") or "") == "mediating_bridge":
            support += 3
            reasons.append("상극을 통관하는 중간 기운이 확인됩니다.")
        else:
            pressure += 2
    elif relation_family == "exception":
        pressure += 3
        caution_reasons.append("일반 생극이 뒤집히는 예외 작용이 붙습니다.")

    condition_verdict = str(condition.get("verdict") or "")
    if condition_verdict in {"condition_supports_cycle", "condition_support_with_cost"}:
        support += 2
    if condition_verdict in {"condition_pressures_cycle", "condition_pressure_with_use", "condition_mixed_cycle"}:
        pressure += 2

    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade in {"month_branch_visible", "month_hidden_protruded"}:
        support += 2
        pressure += 1
    elif branch_grade in {"branch_dominant", "hidden_to_visible"}:
        support += 1

    net = support - pressure
    primary_anchor = bool(pattern_support or pattern_caution or source_group == month_group or target_group == month_group)
    if not primary_anchor and support >= pressure + 4:
        verdict = "month_cycle_auxiliary_use"
    elif not primary_anchor and pressure >= support + 4:
        verdict = "month_cycle_auxiliary_pressure"
    elif support >= pressure + 7 and support >= 9:
        verdict = "month_cycle_needed"
    elif support >= pressure + 2 and support >= 6:
        verdict = "month_cycle_needed_with_cost" if pressure >= 5 else "month_cycle_needed"
    elif pressure >= support + 7 and pressure >= 9:
        verdict = "month_cycle_burdens_month"
    elif pressure >= support + 2 and pressure >= 6:
        verdict = "month_cycle_pressure_with_use" if support >= 5 else "month_cycle_burdens_month"
    else:
        verdict = "month_cycle_mixed"

    edge_verdicts = {str(edge.get("verdict") or "") for edge in edge_contexts}
    costly_edge_count = sum(
        1
        for edge in edge_contexts
        if str(edge.get("verdict") or "") in {"edge_useful_with_cost", "edge_pressure_with_use", "edge_burdens_month", "edge_mixed"}
    )
    burden_edge_count = sum(
        1
        for edge in edge_contexts
        if str(edge.get("verdict") or "") in {"edge_pressure_with_use", "edge_burdens_month"}
    )
    latent_edge_count = sum(
        1
        for edge in edge_contexts
        if str(edge.get("edge_reality_grade") or "") in {"one_sided_edge", "latent_edge"}
    )
    if relation_family == "chain" and verdict == "month_cycle_needed" and (costly_edge_count or latent_edge_count):
        verdict = "month_cycle_needed_with_cost"

    return {
        "relation_family": relation_family,
        "source_group": source_group,
        "target_group": target_group,
        "month_command_group": month_group,
        "source_net": source_net,
        "target_net": target_net,
        "source_support": source_support,
        "source_pressure": source_pressure,
        "target_support": target_support,
        "target_pressure": target_pressure,
        "support_score": support,
        "pressure_score": pressure,
        "net_score": net,
        "verdict": verdict,
        "touches_month_command": bool(source_group == month_group or target_group == month_group or governance.get("touches_month_command")),
        "primary_anchor": primary_anchor,
        "uses_pattern_support": bool(pattern_support),
        "uses_pattern_caution": bool(pattern_caution),
        "edge_verdicts": sorted(edge_verdicts),
        "costly_edge_count": costly_edge_count,
        "burden_edge_count": burden_edge_count,
        "latent_edge_count": latent_edge_count,
        "edge_contexts": edge_contexts,
        "reasons": _unique(reasons)[:4],
        "caution_reasons": _unique(caution_reasons)[:4],
    }


def _month_cycle_fit_basis_codes(month_cycle_fit: dict[str, Any]) -> list[str]:
    codes = [
        f"cycle_month_fit_verdict_{month_cycle_fit.get('verdict')}",
        f"cycle_month_fit_relation_{month_cycle_fit.get('relation_family')}",
        f"cycle_month_fit_source_{month_cycle_fit.get('source_group')}",
        f"cycle_month_fit_target_{month_cycle_fit.get('target_group')}",
        f"cycle_month_fit_month_group_{month_cycle_fit.get('month_command_group')}",
        f"cycle_month_fit_net_{max(-9, min(9, int(month_cycle_fit.get('net_score') or 0)))}",
    ]
    if month_cycle_fit.get("touches_month_command"):
        codes.append("cycle_month_fit_touches_month_command")
    if month_cycle_fit.get("uses_pattern_support"):
        codes.append("cycle_month_fit_uses_pattern_support")
    if month_cycle_fit.get("uses_pattern_caution"):
        codes.append("cycle_month_fit_uses_pattern_caution")
    costly_edge_count = int(month_cycle_fit.get("costly_edge_count") or 0)
    burden_edge_count = int(month_cycle_fit.get("burden_edge_count") or 0)
    latent_edge_count = int(month_cycle_fit.get("latent_edge_count") or 0)
    if costly_edge_count:
        codes.append(f"cycle_month_fit_costly_edges_{min(9, costly_edge_count)}")
    if burden_edge_count:
        codes.append(f"cycle_month_fit_burden_edges_{min(9, burden_edge_count)}")
    if latent_edge_count:
        codes.append(f"cycle_month_fit_latent_edges_{min(9, latent_edge_count)}")
    for edge in list(month_cycle_fit.get("edge_contexts") or [])[:4]:
        source = str(edge.get("source_group") or "")
        target = str(edge.get("target_group") or "")
        relation = str(edge.get("relation") or "")
        verdict = str(edge.get("verdict") or "")
        if source and target and relation and verdict:
            codes.append(f"cycle_month_fit_edge_{source}_{relation}_{target}_{verdict}")
        reality_grade = str(edge.get("edge_reality_grade") or "")
        if source and target and relation and reality_grade:
            codes.append(f"cycle_month_fit_edge_reality_{source}_{relation}_{target}_{reality_grade}")
    return _unique([str(code) for code in codes if str(code) and not str(code).endswith("_")])


def _attach_governance_context(chart_structure: Any, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for signal in signals:
        governance = _signal_governance_context(chart_structure, signal)
        pattern_cycle = _pattern_cycle_context(chart_structure, signal)
        condition = _condition_context(chart_structure, signal)
        branch_reality = _branch_reality_context(chart_structure, signal)
        month_cycle_fit = _month_cycle_fit_context(
            chart_structure,
            signal,
            governance,
            pattern_cycle,
            condition,
            branch_reality,
        )
        basis_codes = _unique(
            list(signal.get("basis_codes") or [])
            + _governance_basis_codes(governance)
            + _pattern_cycle_basis_codes(pattern_cycle)
            + _condition_basis_codes(condition)
            + _branch_reality_basis_codes(branch_reality)
            + _month_cycle_fit_basis_codes(month_cycle_fit)
        )
        score = int(signal.get("score") or 0)
        if governance["touches_month_command"]:
            score += 3
        if governance["touches_useful"] and signal.get("polarity") == "support":
            score += 2
        if governance["touches_caution"] and signal.get("polarity") == "pressure":
            score += 2
        support_strength = int(round(float(pattern_cycle.get("support_strength") or 0)))
        caution_strength = int(round(float(pattern_cycle.get("caution_strength") or 0)))
        if pattern_cycle["support_rule_keys"] and signal.get("polarity") in {"support", "mixed"}:
            score += max(2, min(6, support_strength))
        if pattern_cycle["caution_rule_keys"] and signal.get("polarity") in {"pressure", "mixed"}:
            score += max(2, min(6, caution_strength))
        if condition["verdict"] in {"condition_supports_cycle", "condition_support_with_cost"} and signal.get("polarity") in {"support", "mixed"}:
            score += 2
        if condition["verdict"] in {"condition_pressures_cycle", "condition_pressure_with_use"} and signal.get("polarity") in {"pressure", "mixed"}:
            score += 2
        if branch_reality["grade"] in {"month_branch_visible", "month_hidden_protruded"}:
            score += 4
        elif branch_reality["grade"] in {"branch_dominant", "hidden_to_visible"}:
            score += 3
        elif branch_reality["grade"] == "branch_rooted":
            score += 2
        elif branch_reality["grade"] == "stem_visible_only":
            score += 1
        month_fit_verdict = str(month_cycle_fit.get("verdict") or "")
        if month_fit_verdict == "month_cycle_needed":
            score += 4
        elif month_fit_verdict == "month_cycle_needed_with_cost":
            score += 3
        elif month_fit_verdict == "month_cycle_pressure_with_use":
            score += 2
        elif month_fit_verdict == "month_cycle_burdens_month":
            score += 2
        effect_strength = max(35, min(98, score))
        enriched_signal = {
            **signal,
            # ``score`` is retained as a compatibility alias.  It measures how
            # strongly the relation materializes, not whether it is auspicious.
            "score": effect_strength,
            "effect_strength": effect_strength,
            "governance_context": governance,
            "pattern_cycle_context": pattern_cycle,
            "condition_context": condition,
            "branch_reality_context": branch_reality,
            "month_cycle_fit_context": month_cycle_fit,
            "basis_codes": basis_codes,
        }
        enriched.append(enriched_signal)
    return enriched


def _signal_score(source_score: float, target_score: float, source_fit: tuple[int, int], target_fit: tuple[int, int]) -> int:
    support = source_fit[0] + target_fit[0]
    pressure = source_fit[1] + target_fit[1]
    reality = min(18, round((source_score + target_score) * 5))
    return max(35, min(98, 48 + reality + support + pressure))


def _domains_for(*groups: str) -> list[str]:
    domains: list[str] = []
    for group in groups:
        domains.extend(ROLE_DOMAIN_LINKS.get(group, []))
    return _unique(domains)


def _basis_for(chart_structure: Any, *groups: str) -> list[str]:
    basis: list[str] = []
    month_profile = chart_structure.month_governance_profile
    for group in groups:
        element = _role_element(chart_structure.day_master_element, group)
        basis.append(f"cycle_role_{group}_{element}")
        fit = _fit(month_profile, group)
        if fit is not None:
            basis.append(f"cycle_month_fit_{group}_{getattr(fit, 'status', '')}")
            basis.extend(str(code) for code in list(getattr(fit, "basis_codes", []) or [])[:3])
            basis.extend(str(code) for code in list(getattr(fit, "counter_signals", []) or [])[:2])
        basis.extend(f"cycle_position_{group}_{position}" for position in _role_positions(chart_structure.position_signals, group)[:3])
    return _unique(basis)


def _element_basis_for(chart_structure: Any, *elements: str) -> list[str]:
    basis: list[str] = []
    profile = chart_structure.month_governance_profile
    for element in elements:
        fit = getattr(profile, "element_fits", {}).get(element)
        basis.append(f"element_cycle_{element}")
        if fit is not None:
            basis.append(f"element_cycle_month_fit_{element}_{getattr(fit, 'status', '')}")
            basis.extend(str(code) for code in list(getattr(fit, "basis_codes", []) or [])[:3])
            basis.extend(str(code) for code in list(getattr(fit, "counter_signals", []) or [])[:2])
    return _unique(basis)


def _edge_signal(
    chart_structure: Any,
    *,
    relation: str,
    source: str,
    target: str,
    sentence: str,
    status: str,
) -> dict[str, Any]:
    group_scores = chart_structure.ten_god_profile.group_scores
    source_score = float(group_scores.get(source, 0.0) or 0.0)
    target_score = float(group_scores.get(target, 0.0) or 0.0)
    source_fit = _fit_scores(chart_structure.month_governance_profile, source)
    target_fit = _fit_scores(chart_structure.month_governance_profile, target)
    source_element = _role_element(chart_structure.day_master_element, source)
    target_element = _role_element(chart_structure.day_master_element, target)
    source_context = _role_context(chart_structure, source)
    target_context = _role_context(chart_structure, target)
    classical_name = ROLE_EDGE_CLASSICAL_NAMES.get((source, target, relation), "")
    judgment = _relation_judgment(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    force_balance = _force_balance_context(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    status = _status_from_judgment(relation, judgment)
    basis_codes = (
        _basis_for(chart_structure, source, target)
        + _relation_basis_codes(
            layer="ten_god",
            relation=relation,
            source_key=source,
            target_key=target,
            source_context=source_context,
            target_context=target_context,
            judgment=judgment,
            classical_name=classical_name,
        )
        + _force_balance_basis_codes(force_balance)
    )
    return {
        "signal_id": f"{relation}_{source}_to_{target}",
        "layer": "cycle_regulation",
        "relation": relation,
        "status": status,
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict(relation, judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict(relation, judgment), ""),
        "decision_reason": _decision_reason(
            relation=relation,
            source_context=source_context,
            target_context=target_context,
            judgment=judgment,
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": ROLE_EDGE_THEORY.get(classical_name, ""),
        "source_group": source,
        "target_group": target,
        "source_element": source_element,
        "target_element": target_element,
        "source_label": ROLE_LABELS[source],
        "target_label": ROLE_LABELS[target],
        "source_element_label": ELEMENT_LABELS.get(source_element, source_element),
        "target_element_label": ELEMENT_LABELS.get(target_element, target_element),
        "source_presence": _presence_level(source_score),
        "target_presence": _presence_level(target_score),
        "score": _signal_score(source_score, target_score, source_fit, target_fit),
        "domain_links": _domains_for(source, target),
        "sentence": sentence,
        "source_context": source_context,
        "target_context": target_context,
        "force_balance_context": force_balance,
        "reality_score": min(99, int(source_context["reality_score"]) + int(target_context["reality_score"])),
        "basis_codes": _unique(basis_codes),
    }


def _element_signal_score(source_score: float, target_score: float, source_fit: tuple[int, int], target_fit: tuple[int, int]) -> int:
    support = source_fit[0] + target_fit[0]
    pressure = source_fit[1] + target_fit[1]
    reality = min(16, round((source_score + target_score) * 18))
    return max(32, min(96, 42 + reality + support + pressure))


def _element_relation_status(chart_structure: Any, source: str, target: str, relation: str) -> str:
    source_group = _group_for_element(chart_structure.day_master_element, source)
    target_group = _group_for_element(chart_structure.day_master_element, target)
    if relation == "controls" and source_group == "peer" and target_group == "wealth":
        return "element_mixed_wealth_competition"
    source_support, source_pressure = _element_fit_scores(chart_structure.month_governance_profile, source)
    target_support, target_pressure = _element_fit_scores(chart_structure.month_governance_profile, target)
    if relation == "generates":
        if target_support > target_pressure and source_pressure <= source_support:
            return "element_feeds_useful_force"
        if target_pressure > target_support:
            return "element_feeds_burden"
        return "element_connects"
    if target_pressure > target_support and source_support >= source_pressure:
        return "element_regulates_pressure"
    if source_pressure > source_support and target_support > target_pressure:
        return "element_damages_useful_force"
    if source_pressure > source_support and target_pressure >= target_support:
        return "element_conflict_or_overload"
    return "element_sets_boundary"


def _element_relation_sentence(chart_structure: Any, source: str, target: str, relation: str, status: str) -> str:
    source_label = ELEMENT_LABELS.get(source, source)
    target_label = ELEMENT_LABELS.get(target, target)
    source_group = _group_for_element(chart_structure.day_master_element, source)
    target_group = _group_for_element(chart_structure.day_master_element, target)
    source_role = ROLE_LABELS.get(source_group, "")
    target_role = ROLE_LABELS.get(target_group, "")
    source_text = f"{source_label} {source_role}".strip()
    target_text = f"{target_label} {target_role}".strip()
    if relation == "generates":
        if status == "element_feeds_burden":
            return f"{source_text}이 {target_text}을 생하지만, 받는 기운이 부담이면 그 부담도 함께 커집니다."
        return f"{source_text}이 {target_text}을 생해 다음 작용으로 힘을 넘깁니다."
    if status == "element_regulates_pressure":
        return f"{source_text}이 {target_text}을 극해 과해진 기운을 제어합니다."
    if status == "element_mixed_wealth_competition":
        return f"{source_text}이 {target_text}을 극하면 재물에서는 경쟁, 분배, 공동 비용 문제가 함께 따라옵니다."
    if status == "element_damages_useful_force":
        return f"{source_text}이 {target_text}을 극하면 필요한 기운이 손상됩니다."
    if status == "element_conflict_or_overload":
        return f"{source_text}과 {target_text}의 극은 부담끼리 부딪히는 형태입니다."
    return f"{source_text}이 {target_text}을 극해 경계를 세웁니다."


def _element_edge_signal(chart_structure: Any, *, relation: str, source: str, target: str) -> dict[str, Any]:
    score_map = chart_structure.element_profile.scores
    source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
    target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
    source_fit = _element_fit_scores(chart_structure.month_governance_profile, source)
    target_fit = _element_fit_scores(chart_structure.month_governance_profile, target)
    source_group = _group_for_element(chart_structure.day_master_element, source)
    target_group = _group_for_element(chart_structure.day_master_element, target)
    source_context = _element_context(chart_structure, source)
    target_context = _element_context(chart_structure, target)
    judgment = _relation_judgment(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    force_balance = _force_balance_context(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    status = _element_relation_status(chart_structure, source, target, relation)
    if status != "element_mixed_wealth_competition":
        status = f"element_{_status_from_judgment(relation, judgment)}"
    classical_name = f"{ELEMENT_LABELS.get(source, source)}{'생' if relation == 'generates' else '극'}{ELEMENT_LABELS.get(target, target)}"
    basis_codes = (
        _element_basis_for(chart_structure, source, target)
        + _relation_basis_codes(
            layer="element",
            relation=relation,
            source_key=source,
            target_key=target,
            source_context=source_context,
            target_context=target_context,
            judgment=judgment,
            classical_name=classical_name,
        )
        + _force_balance_basis_codes(force_balance)
    )
    return {
        "signal_id": f"element_{relation}_{source}_to_{target}",
        "layer": "cycle_regulation",
        "relation": f"element_{relation}",
        "status": status,
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict(relation, judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict(relation, judgment), ""),
        "decision_reason": _decision_reason(
            relation=relation,
            source_context=source_context,
            target_context=target_context,
            judgment=judgment,
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": "오행 자체의 생극을 먼저 판정하고, 그 오행이 일간에게 맡는 십신 역할로 다시 번역했습니다.",
        "source_group": source_group,
        "target_group": target_group,
        "source_element": source,
        "target_element": target,
        "source_label": ROLE_LABELS.get(source_group, ""),
        "target_label": ROLE_LABELS.get(target_group, ""),
        "source_element_label": ELEMENT_LABELS.get(source, source),
        "target_element_label": ELEMENT_LABELS.get(target, target),
        "source_presence": _presence_level(source_score * 5),
        "target_presence": _presence_level(target_score * 5),
        "score": _element_signal_score(source_score, target_score, source_fit, target_fit),
        "domain_links": _domains_for(source_group, target_group),
        "sentence": _element_relation_sentence(chart_structure, source, target, relation, status),
        "source_context": source_context,
        "target_context": target_context,
        "force_balance_context": force_balance,
        "reality_score": min(99, int(source_context["reality_score"]) + int(target_context["reality_score"])),
        "basis_codes": _unique(basis_codes),
    }


def _bridge_judgment(
    *,
    source_context: dict[str, Any],
    bridge_context: dict[str, Any],
    target_context: dict[str, Any],
    control_judgment: str,
) -> str:
    bridge_net = int(bridge_context.get("net_fit") or 0)
    bridge_reality = int(bridge_context.get("reality_score") or 0)
    bridge_presence = str(bridge_context.get("presence") or "")
    target_net = int(target_context.get("net_fit") or 0)
    source_net = int(source_context.get("net_fit") or 0)

    if bridge_net >= 2 and bridge_reality >= 3 and bridge_presence in {"clear", "strong"}:
        return "mediating_bridge"
    if bridge_net <= -3 or bridge_presence == "weak":
        return "missing_bridge"
    if control_judgment in {"burden_collision", "damaging_control", "wealth_competition"} and target_net <= -1:
        return "overloaded_bridge"
    if source_net <= -3:
        return "unstable_bridge"
    return "unstable_bridge"


def _element_bridge_score(
    source_context: dict[str, Any],
    bridge_context: dict[str, Any],
    target_context: dict[str, Any],
) -> int:
    presence = (
        float(source_context.get("presence_score") or 0.0)
        + float(bridge_context.get("presence_score") or 0.0)
        + float(target_context.get("presence_score") or 0.0)
    )
    fit_pressure = (
        int(source_context.get("pressure_score") or 0)
        + int(bridge_context.get("pressure_score") or 0)
        + int(target_context.get("pressure_score") or 0)
    )
    fit_support = (
        int(source_context.get("support_score") or 0)
        + int(bridge_context.get("support_score") or 0)
        + int(target_context.get("support_score") or 0)
    )
    reality = min(
        16,
        int(source_context.get("reality_score") or 0)
        + int(bridge_context.get("reality_score") or 0)
        + int(target_context.get("reality_score") or 0),
    )
    return max(36, min(98, 42 + round(presence * 5) + reality + fit_support + fit_pressure))


def _element_bridge_sentence(source: str, bridge: str, target: str, judgment: str) -> str:
    source_label = ELEMENT_LABELS.get(source, source)
    bridge_label = ELEMENT_LABELS.get(bridge, bridge)
    target_label = ELEMENT_LABELS.get(target, target)
    if judgment == "mediating_bridge":
        return f"{source_label}이 {target_label}을 극하는 관계는 {bridge_label}을 거치며 풀립니다."
    if judgment == "missing_bridge":
        return f"{source_label}과 {target_label}의 상극을 풀어 줄 {bridge_label} 기운이 약합니다."
    if judgment == "overloaded_bridge":
        return f"{bridge_label}이 중간에 서지만 부담까지 함께 받아 상극이 매끄럽게 풀리지는 않습니다."
    return f"{source_label}과 {target_label} 사이에 {bridge_label} 통관이 있으나 작용은 안정과 부담이 함께 나타납니다."


def _element_bridge_signal(chart_structure: Any, *, source: str, bridge: str, target: str) -> dict[str, Any]:
    source_context = _element_context(chart_structure, source)
    bridge_context = _element_context(chart_structure, bridge)
    target_context = _element_context(chart_structure, target)
    control_judgment = _relation_judgment(
        relation="controls",
        source_context=source_context,
        target_context=target_context,
    )
    judgment = _bridge_judgment(
        source_context=source_context,
        bridge_context=bridge_context,
        target_context=target_context,
        control_judgment=control_judgment,
    )
    source_group = str(source_context.get("group") or "")
    bridge_group = str(bridge_context.get("group") or "")
    target_group = str(target_context.get("group") or "")
    classical_name = (
        f"{ELEMENT_LABELS.get(source, source)}극{ELEMENT_LABELS.get(target, target)} 통관"
    )
    basis_codes = (
        _element_basis_for(chart_structure, source, bridge, target)
        + [
            f"cycle_element_bridge_{source}_via_{bridge}_to_{target}",
            f"cycle_classical_{classical_name}",
            f"cycle_judgment_{judgment}",
            f"cycle_month_verdict_{_month_command_verdict('bridge', judgment)}",
            f"cycle_polarity_{JUDGMENT_POLARITY.get(judgment, 'mixed')}",
            f"cycle_bridge_fit_{bridge_context.get('fit_status')}",
            f"cycle_bridge_authority_{bridge_context.get('month_authority')}",
        ]
    )
    return {
        "signal_id": f"element_bridge_{source}_via_{bridge}_to_{target}",
        "layer": "cycle_regulation",
        "relation": "element_bridge",
        "status": f"element_bridge_{judgment}",
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict("bridge", judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("bridge", judgment), ""),
        "decision_reason": (
            f"{ELEMENT_LABELS.get(source, source)}극{ELEMENT_LABELS.get(target, target)} 관계를 "
            f"{ELEMENT_LABELS.get(bridge, bridge)} 통관으로 다시 보았습니다. "
            f"{MONTH_VERDICT_LABELS.get(_month_command_verdict('bridge', judgment), '')}"
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": ELEMENT_BRIDGE_THEORY.get((source, bridge, target), ""),
        "source_element": source,
        "bridge_element": bridge,
        "target_element": target,
        "source_group": source_group,
        "bridge_group": bridge_group,
        "target_group": target_group,
        "source_element_label": ELEMENT_LABELS.get(source, source),
        "bridge_element_label": ELEMENT_LABELS.get(bridge, bridge),
        "target_element_label": ELEMENT_LABELS.get(target, target),
        "source_label": ROLE_LABELS.get(source_group, ""),
        "bridge_label": ROLE_LABELS.get(bridge_group, ""),
        "target_label": ROLE_LABELS.get(target_group, ""),
        "source_context": source_context,
        "bridge_context": bridge_context,
        "target_context": target_context,
        "group_contexts": [source_context, bridge_context, target_context],
        "score": _element_bridge_score(source_context, bridge_context, target_context),
        "domain_links": _domains_for(source_group, bridge_group, target_group),
        "sentence": _element_bridge_sentence(source, bridge, target, judgment),
        "reality_score": min(
            99,
            int(source_context.get("reality_score") or 0)
            + int(bridge_context.get("reality_score") or 0)
            + int(target_context.get("reality_score") or 0),
        ),
        "basis_codes": _unique(basis_codes),
    }


def _element_force_index(context: dict[str, Any]) -> float:
    presence = float(context.get("presence_score") or 0.0)
    reality = int(context.get("reality_score") or 0)
    net_fit = int(context.get("net_fit") or 0)
    root_count = int(context.get("root_count") or 0)
    visible_count = int(context.get("visible_count") or 0)
    return presence * 22 + reality + net_fit + root_count * 1.5 + visible_count


def _element_exception_kind(
    *,
    relation: str,
    source_context: dict[str, Any],
    target_context: dict[str, Any],
) -> str:
    source_force = _element_force_index(source_context)
    target_force = _element_force_index(target_context)
    source_net = int(source_context.get("net_fit") or 0)
    target_net = int(target_context.get("net_fit") or 0)
    source_presence = str(source_context.get("presence") or "")
    target_presence = str(target_context.get("presence") or "")

    if relation == "controls":
        if target_force - source_force >= 7 and target_presence in {"clear", "strong"}:
            return "reverse_control"
        if target_force - source_force >= 4 or source_presence == "weak":
            return "failed_control"
        return ""

    if relation == "generates":
        if target_net <= -3 and target_presence in {"clear", "strong"}:
            return "excessive_generation"
        if source_net <= -2 and target_force - source_force >= 4:
            return "draining_exhaustion"
        if source_presence == "weak" and target_presence in {"clear", "strong"}:
            return "draining_exhaustion"
        return ""
    return ""


def _element_exception_classical_name(source: str, target: str, kind: str) -> str:
    source_label = ELEMENT_LABELS.get(source, source)
    target_label = ELEMENT_LABELS.get(target, target)
    if kind == "reverse_control":
        return f"{source_label}극{target_label} 반극"
    if kind == "failed_control":
        return f"{source_label}극{target_label} 극력 부족"
    if kind == "excessive_generation":
        return f"{source_label}생{target_label} 과생"
    if kind == "draining_exhaustion":
        return f"{source_label}생{target_label} 설기 과다"
    return f"{source_label}-{target_label} 생극 예외"


def _element_exception_sentence(source: str, target: str, kind: str) -> str:
    source_label = ELEMENT_LABELS.get(source, source)
    target_label = ELEMENT_LABELS.get(target, target)
    if kind == "reverse_control":
        return f"{source_label}이 {target_label}을 극하려 하나 {target_label}의 힘이 더 강해 반극으로 나타납니다."
    if kind == "failed_control":
        return f"{source_label}이 {target_label}을 극하는 형식은 있으나 제어력은 충분하지 않습니다."
    if kind == "excessive_generation":
        return f"{source_label}이 {target_label}을 생하지만 보강을 넘어 부담을 키웁니다."
    if kind == "draining_exhaustion":
        return f"{source_label}이 {target_label}을 생하면서 자신의 기운이 지나치게 빠집니다."
    return f"{source_label}과 {target_label}의 생극은 힘의 차이에서 결론이 갈립니다."


def _element_exception_signal(chart_structure: Any, *, relation: str, source: str, target: str) -> dict[str, Any] | None:
    source_context = _element_context(chart_structure, source)
    target_context = _element_context(chart_structure, target)
    kind = _element_exception_kind(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    if not kind:
        return None
    source_group = str(source_context.get("group") or "")
    target_group = str(target_context.get("group") or "")
    force_balance = _force_balance_context(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    classical_name = _element_exception_classical_name(source, target, kind)
    theory = ""
    if kind in {"reverse_control", "failed_control"}:
        theory = ELEMENT_REVERSE_CONTROL_THEORY.get((source, target), "")
    elif kind == "excessive_generation":
        theory = "생이 필요한 보강을 넘어 부담 기운을 키우면 과생으로 판단합니다."
    elif kind == "draining_exhaustion":
        theory = "생하는 쪽이 약한데 계속 내보내면 설기 과다로 판단합니다."
    score = max(
        38,
        min(
            98,
            44
            + round(abs(_element_force_index(target_context) - _element_force_index(source_context)))
            + int(source_context.get("reality_score") or 0)
            + int(target_context.get("reality_score") or 0),
        ),
    )
    basis_codes = (
        _element_basis_for(chart_structure, source, target)
        + [
            f"cycle_element_exception_{relation}_{source}_to_{target}_{kind}",
            f"cycle_classical_{classical_name}",
            f"cycle_judgment_{kind}",
            f"cycle_month_verdict_{_month_command_verdict('exception', kind)}",
            f"cycle_polarity_{JUDGMENT_POLARITY.get(kind, 'mixed')}",
            f"cycle_source_force_{min(20, round(_element_force_index(source_context)))}",
            f"cycle_target_force_{min(20, round(_element_force_index(target_context)))}",
        ]
        + _force_balance_basis_codes(force_balance)
    )
    return {
        "signal_id": f"element_exception_{relation}_{source}_to_{target}_{kind}",
        "layer": "cycle_regulation",
        "relation": "element_exception",
        "status": f"element_exception_{kind}",
        "cycle_judgment": kind,
        "cycle_judgment_label": JUDGMENT_LABELS.get(kind, kind),
        "month_command_verdict": _month_command_verdict("exception", kind),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("exception", kind), ""),
        "decision_reason": (
            f"{ELEMENT_LABELS.get(source, source)}와 {ELEMENT_LABELS.get(target, target)}의 "
            f"{'상극' if relation == 'controls' else '상생'}을 힘의 차이로 다시 판단했습니다. "
            f"{MONTH_VERDICT_LABELS.get(_month_command_verdict('exception', kind), '')}"
        ),
        "polarity": JUDGMENT_POLARITY.get(kind, "mixed"),
        "classical_name": classical_name,
        "classical_theory": theory,
        "source_element": source,
        "target_element": target,
        "source_group": source_group,
        "target_group": target_group,
        "source_element_label": ELEMENT_LABELS.get(source, source),
        "target_element_label": ELEMENT_LABELS.get(target, target),
        "source_label": ROLE_LABELS.get(source_group, ""),
        "target_label": ROLE_LABELS.get(target_group, ""),
        "source_context": source_context,
        "target_context": target_context,
        "force_balance_context": force_balance,
        "score": score,
        "domain_links": _domains_for(source_group, target_group),
        "sentence": _element_exception_sentence(source, target, kind),
        "reality_score": min(
            99,
            int(source_context.get("reality_score") or 0) + int(target_context.get("reality_score") or 0),
        ),
        "basis_codes": _unique(basis_codes),
    }


def _branch_cycle_judgment(relation_type: str, polarity: str) -> str:
    if relation_type in COMBINE_RELATIONS:
        if polarity == "supportive":
            return "branch_combines_useful_element"
        if polarity == "burdensome":
            return "branch_combines_burden_element"
        return "branch_mixed_cycle_activation"
    if relation_type in DISRUPTIVE_RELATIONS:
        if polarity == "supportive":
            return "branch_disrupts_burden_element"
        if polarity == "burdensome":
            return "branch_disrupts_useful_element"
        return "branch_mixed_cycle_activation"
    return "branch_mixed_cycle_activation"


def _branch_cycle_sentence(relation_type: str, elements: list[str], judgment: str) -> str:
    element_text = ", ".join(ELEMENT_LABELS.get(element, element) for element in elements) or "오행"
    if judgment == "branch_combines_useful_element":
        return f"지지의 합이 {element_text} 기운을 모아 필요한 생극을 살립니다."
    if judgment == "branch_combines_burden_element":
        return f"지지의 합이 {element_text} 기운을 모으지만 월령상 부담도 함께 커집니다."
    if judgment == "branch_disrupts_useful_element":
        return f"지지의 {relation_type} 작용이 {element_text} 기운을 흔들어 필요한 생극을 약하게 만듭니다."
    if judgment == "branch_disrupts_burden_element":
        return f"지지의 {relation_type} 작용이 {element_text} 부담을 흔들어 고착된 힘을 풉니다."
    return f"지지의 {relation_type} 작용이 {element_text} 기운을 복합적으로 자극합니다."


def _branch_cycle_signal(chart_structure: Any, interaction: Any) -> dict[str, Any] | None:
    polarity = branch_relation_polarity(
        chart_structure.element_profile,
        interaction,
        getattr(chart_structure, "pattern_profile", None),
    )
    activated = [str(element) for element in list(polarity.activated_elements or []) if str(element)]
    if not activated:
        return None
    judgment = _branch_cycle_judgment(str(interaction.relation_type), polarity.polarity)
    primary_element = (
        list(polarity.support_elements or polarity.pressure_elements or polarity.overuse_elements or activated)[0]
    )
    primary_context = _element_context(chart_structure, primary_element)
    activated_groups = _unique([_group_for_element(chart_structure.day_master_element, element) for element in activated])
    domain_links = _unique(
        list(getattr(interaction, "domain_links", []) or [])
        + [domain for group in activated_groups for domain in ROLE_DOMAIN_LINKS.get(group, [])]
    )
    intensity_bonus = {"strong": 8, "moderate": 5, "mild": 3}.get(str(getattr(interaction, "intensity", "")), 2)
    score = max(
        36,
        min(
            98,
            44
            + intensity_bonus
            + int(getattr(polarity, "useful_score", 0) or 0) * 3
            + int(getattr(polarity, "pressure_score", 0) or 0) * 3
            + int(primary_context.get("reality_score") or 0),
        ),
    )
    relation_type = str(getattr(interaction, "relation_type", "branch_relation"))
    branches = [str(branch) for branch in list(getattr(interaction, "branches", []) or [])]
    positions = [str(position) for position in list(getattr(interaction, "positions", []) or [])]
    signal_id = f"branch_cycle_{relation_type}_{'_'.join(branches)}_{'_'.join(positions)}"
    classical_name = f"지지 {relation_type} 생극 작용"
    basis_codes = [
        str(getattr(interaction, "basis_code", "")),
        f"cycle_branch_relation_{relation_type}",
        f"cycle_branch_positions_{'_'.join(positions)}",
        f"cycle_branch_elements_{'_'.join(activated)}",
        f"cycle_classical_{classical_name}",
        f"cycle_judgment_{judgment}",
        f"cycle_month_verdict_{_month_command_verdict('branch', judgment)}",
        f"cycle_polarity_{JUDGMENT_POLARITY.get(judgment, 'mixed')}",
        f"cycle_branch_polarity_{polarity.polarity}",
    ]
    basis_codes.extend(f"cycle_branch_support_element_{element}" for element in polarity.support_elements)
    basis_codes.extend(f"cycle_branch_pressure_element_{element}" for element in polarity.pressure_elements)
    basis_codes.extend(f"cycle_branch_overuse_element_{element}" for element in polarity.overuse_elements)
    counter_signals = []
    if relation_type in DISRUPTIVE_RELATIONS and polarity.effective_friction > 0.0:
        counter_signals.append(f"cycle_branch_structural_friction_{relation_type}")
        basis_codes.append(f"cycle_branch_intrinsic_friction_{polarity.intrinsic_friction:.4f}")
        basis_codes.append(f"cycle_branch_effective_friction_{polarity.effective_friction:.4f}")
    return {
        "signal_id": signal_id,
        "layer": "cycle_regulation",
        "relation": "branch_cycle",
        "status": f"branch_cycle_{judgment}",
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict("branch", judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("branch", judgment), ""),
        "decision_reason": (
            f"지지 {relation_type}이 {', '.join(ELEMENT_LABELS.get(element, element) for element in activated)}을 "
            f"활성화합니다. {MONTH_VERDICT_LABELS.get(_month_command_verdict('branch', judgment), '')}"
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": "지지의 합충형해파는 오행을 모으거나 흔들어 원국 생극의 현실 작용을 바꿉니다.",
        "relation_type": relation_type,
        "branches": branches,
        "positions": positions,
        "activated_elements": activated,
        "activated_groups": list(activated_groups),
        "source_element": primary_element,
        "source_group": str(primary_context.get("group") or ""),
        "source_context": primary_context,
        "score": score,
        "domain_links": domain_links,
        "sentence": _branch_cycle_sentence(relation_type, activated, judgment),
        "reality_score": min(99, int(primary_context.get("reality_score") or 0) + intensity_bonus),
        "counter_signals": counter_signals,
        "basis_codes": _unique(basis_codes),
    }


def _visible_stem_entries(chart_structure: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, signal in chart_structure.position_signals.items():
        stem = str(getattr(signal, "stem_key", ""))
        if not stem:
            continue
        element = STEM_METADATA[stem]["element"]
        entries.append(
            {
                "position": position,
                "stem": stem,
                "element": element,
                "group": _group_for_element(chart_structure.day_master_element, element),
            }
        )
    return entries


def _stem_combine_judgment(chart_structure: Any, transform_element: str, positions: list[str]) -> str:
    context = _element_context(chart_structure, transform_element)
    net_fit = int(context.get("net_fit") or 0)
    reality = int(context.get("reality_score") or 0) + _position_reality_score([f"{position}_stem" for position in positions])
    presence = str(context.get("presence") or "")

    if net_fit >= 2 and reality >= 4:
        return "stem_combine_transforms_useful_element"
    if net_fit <= -3 and presence in {"clear", "strong"}:
        return "stem_combine_transforms_burden_element"
    if reality < 3 or presence == "weak":
        return "stem_combine_bound_not_transformed"
    return "stem_combine_ties_original_force"


def _stem_combine_sentence(stems: list[str], transform_element: str, judgment: str) -> str:
    stem_text = "".join(STEM_LABELS.get(stem, stem) for stem in stems)
    element_label = ELEMENT_LABELS.get(transform_element, transform_element)
    if judgment == "stem_combine_transforms_useful_element":
        return f"{stem_text}합은 {element_label} 기운으로 화하여 필요한 생극을 보탭니다."
    if judgment == "stem_combine_transforms_burden_element":
        return f"{stem_text}합은 {element_label} 기운을 키우지만 월령상 부담도 함께 커집니다."
    if judgment == "stem_combine_bound_not_transformed":
        return f"{stem_text}합은 있으나 {element_label}으로 완전히 화하기에는 힘이 약합니다."
    return f"{stem_text}합은 두 천간의 원래 생극 작용을 묶어 두는 힘으로 나타납니다."


def _stem_combine_signal(
    chart_structure: Any,
    first: dict[str, Any],
    second: dict[str, Any],
    transform_element: str,
    combine_name: str,
) -> dict[str, Any]:
    stems = [str(first["stem"]), str(second["stem"])]
    positions = [str(first["position"]), str(second["position"])]
    transformed_context = _element_context(chart_structure, transform_element)
    original_contexts = [_element_context(chart_structure, str(first["element"])), _element_context(chart_structure, str(second["element"]))]
    judgment = _stem_combine_judgment(chart_structure, transform_element, positions)
    transformed_group = str(transformed_context.get("group") or "")
    original_groups = _unique([str(first.get("group") or ""), str(second.get("group") or "")])
    signal_id = f"stem_combine_{'_'.join(stems)}_{'_'.join(positions)}"
    reality_score = min(
        99,
        int(transformed_context.get("reality_score") or 0)
        + _position_reality_score([f"{position}_stem" for position in positions]),
    )
    score = max(
        38,
        min(
            98,
            46
            + reality_score
            + int(transformed_context.get("support_score") or 0)
            + int(transformed_context.get("pressure_score") or 0),
        ),
    )
    basis_codes = [
        f"cycle_stem_combine_{combine_name}",
        f"cycle_stem_combine_positions_{'_'.join(positions)}",
        f"cycle_stem_combine_transform_{transform_element}",
        f"cycle_classical_{combine_name}",
        f"cycle_judgment_{judgment}",
        f"cycle_month_verdict_{_month_command_verdict('stem_combine', judgment)}",
        f"cycle_polarity_{JUDGMENT_POLARITY.get(judgment, 'mixed')}",
        f"cycle_transform_fit_{transformed_context.get('fit_status')}",
        f"cycle_transform_authority_{transformed_context.get('month_authority')}",
    ]
    for group in original_groups:
        if group:
            basis_codes.append(f"cycle_stem_combine_original_group_{group}")
    return {
        "signal_id": signal_id,
        "layer": "cycle_regulation",
        "relation": "stem_combine",
        "status": f"stem_combine_{judgment}",
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict("stem_combine", judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("stem_combine", judgment), ""),
        "decision_reason": (
            f"{combine_name}은 {ELEMENT_LABELS.get(transform_element, transform_element)} 기운으로 화하는지를 "
            f"월령 기준에서 판단했습니다. "
            f"{MONTH_VERDICT_LABELS.get(_month_command_verdict('stem_combine', judgment), '')}"
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": combine_name,
        "classical_theory": "천간합은 월령과 뿌리가 받쳐 줄 때 합화 오행으로 작용하고, 그렇지 않으면 두 글자의 원래 생극을 묶는 힘으로 봅니다.",
        "stems": stems,
        "positions": positions,
        "transform_element": transform_element,
        "transform_group": transformed_group,
        "source_element": transform_element,
        "source_group": transformed_group,
        "original_groups": list(original_groups),
        "source_context": transformed_context,
        "group_contexts": [transformed_context, *original_contexts],
        "score": score,
        "domain_links": _unique(
            [
                domain
                for group in [transformed_group, *original_groups]
                for domain in ROLE_DOMAIN_LINKS.get(group, [])
            ]
        ),
        "sentence": _stem_combine_sentence(stems, transform_element, judgment),
        "reality_score": reality_score,
        "basis_codes": _unique(basis_codes),
    }


def _build_stem_combine_signals(chart_structure: Any) -> list[dict[str, Any]]:
    entries = _visible_stem_entries(chart_structure)
    signals: list[dict[str, Any]] = []
    for index, first in enumerate(entries):
        for second in entries[index + 1 :]:
            key = frozenset((str(first["stem"]), str(second["stem"])))
            if key not in STEM_COMBINE_TRANSFORM_ELEMENTS:
                continue
            transform_element, combine_name = STEM_COMBINE_TRANSFORM_ELEMENTS[key]
            signals.append(_stem_combine_signal(chart_structure, first, second, transform_element, combine_name))
    return signals


def _rooting_judgment(context: dict[str, Any], *, mode: str) -> str:
    net_fit = int(context.get("net_fit") or 0)
    reality = int(context.get("reality_score") or 0)
    if mode == "protrusion":
        if net_fit >= 2:
            return "hidden_protrusion_supports_cycle"
        if net_fit <= -2:
            return "hidden_protrusion_exposes_burden"
        return "hidden_root_potential_cycle"
    if net_fit >= 2 and reality >= 4:
        return "visible_root_supports_cycle"
    if net_fit <= -2 and reality >= 4:
        return "visible_root_anchors_burden"
    return "hidden_root_potential_cycle"


def _rooting_sentence(stem: str, element: str, judgment: str) -> str:
    stem_label = STEM_LABELS.get(stem, stem)
    element_label = ELEMENT_LABELS.get(element, element)
    if judgment == "hidden_protrusion_supports_cycle":
        return f"지장간 {stem_label}이 투출되어 {element_label} 생극이 현실 작용으로 드러납니다."
    if judgment == "hidden_protrusion_exposes_burden":
        return f"지장간 {stem_label}이 투출되며 {element_label} 부담도 겉으로 드러납니다."
    if judgment == "visible_root_supports_cycle":
        return f"천간 {stem_label}이 지지에 통근하여 {element_label} 생극의 지속력이 생깁니다."
    if judgment == "visible_root_anchors_burden":
        return f"천간 {stem_label}이 지지에 통근하여 {element_label} 부담이 오래 유지됩니다."
    return f"{stem_label}의 뿌리는 {element_label} 생극의 잠재 작용을 보존합니다."


def _rooting_signal(
    chart_structure: Any,
    *,
    mode: str,
    stem: str,
    element: str,
    group: str,
    positions: list[str],
    root_positions: list[str],
    hidden_position: str | None = None,
) -> dict[str, Any]:
    context = _element_context(chart_structure, element)
    judgment = _rooting_judgment(context, mode=mode)
    force_context = _single_force_context(context)
    relation = "hidden_protrusion" if mode == "protrusion" else "visible_root"
    signal_id = f"{relation}_{stem}_{'_'.join(positions)}"
    if root_positions:
        signal_id = f"{signal_id}_root_{'_'.join(root_positions)}"
    classical_name = f"지장간 {STEM_LABELS.get(stem, stem)} 투출" if mode == "protrusion" else f"{STEM_LABELS.get(stem, stem)} 통근"
    reality_score = min(
        99,
        int(context.get("reality_score") or 0)
        + _position_reality_score([f"{position}_stem" for position in positions])
        + _position_reality_score([f"{position}_hidden" for position in root_positions]),
    )
    score = max(
        38,
        min(
            98,
            44
            + reality_score
            + int(context.get("support_score") or 0)
            + int(context.get("pressure_score") or 0),
        ),
    )
    basis_codes = [
        f"cycle_{relation}_{stem}",
        f"cycle_{relation}_element_{element}",
        f"cycle_{relation}_group_{group}",
        f"cycle_{relation}_positions_{'_'.join(positions)}",
        f"cycle_classical_{classical_name}",
        f"cycle_judgment_{judgment}",
        f"cycle_month_verdict_{_month_command_verdict('rooting', judgment)}",
        f"cycle_polarity_{JUDGMENT_POLARITY.get(judgment, 'mixed')}",
        f"cycle_rooting_fit_{context.get('fit_status')}",
        f"cycle_rooting_authority_{context.get('month_authority')}",
    ]
    if hidden_position:
        basis_codes.append(f"cycle_hidden_position_{hidden_position}")
    basis_codes.extend(f"cycle_root_position_{position}" for position in root_positions)
    basis_codes.extend(_single_force_basis_codes(f"cycle_{relation}", force_context))
    return {
        "signal_id": signal_id,
        "layer": "cycle_regulation",
        "relation": relation,
        "status": f"{relation}_{judgment}",
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict("rooting", judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("rooting", judgment), ""),
        "decision_reason": (
            f"{classical_name}은 {ELEMENT_LABELS.get(element, element)} 기운의 현실성을 높입니다. "
            f"{MONTH_VERDICT_LABELS.get(_month_command_verdict('rooting', judgment), '')}"
        ),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": "투출은 지장간의 숨은 생극이 표면화되는 과정이고, 통근은 천간의 생극이 지지에서 지속력을 얻는 근거입니다.",
        "stem": stem,
        "positions": positions,
        "root_positions": root_positions,
        "source_element": element,
        "source_group": group,
        "source_context": context,
        "force_context": force_context,
        "score": score,
        "domain_links": _unique(
            [
                *[domain for position in positions + root_positions for domain in list(getattr(chart_structure.position_signals.get(position, object()), "domains", []) or [])],
                *ROLE_DOMAIN_LINKS.get(group, []),
            ]
        ),
        "sentence": _rooting_sentence(stem, element, judgment),
        "reality_score": reality_score,
        "basis_codes": _unique(basis_codes),
    }


def _build_hidden_protrusion_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for position, position_signal in chart_structure.position_signals.items():
        branch_key = str(getattr(position_signal, "branch_key", ""))
        for stem, hidden_weight in BRANCH_HIDDEN_STEMS.get(branch_key, []):
            if stem not in list(getattr(position_signal, "protruded_hidden_stems", []) or []):
                continue
            element = STEM_METADATA[stem]["element"]
            group = _group_for_element(chart_structure.day_master_element, element)
            visible_positions = [
                visible_position
                for visible_position, visible_signal in chart_structure.position_signals.items()
                if str(getattr(visible_signal, "stem_key", "")) == stem
            ]
            signals.append(
                _rooting_signal(
                    chart_structure,
                    mode="protrusion",
                    stem=stem,
                    element=element,
                    group=group,
                    positions=visible_positions or [position],
                    root_positions=[position],
                    hidden_position=position,
                )
            )
    return signals


def _build_visible_root_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for position, position_signal in chart_structure.position_signals.items():
        stem = str(getattr(position_signal, "stem_key", ""))
        if not stem:
            continue
        element = STEM_METADATA[stem]["element"]
        group = _group_for_element(chart_structure.day_master_element, element)
        root_positions: list[str] = []
        for root_position, root_signal in chart_structure.position_signals.items():
            branch_key = str(getattr(root_signal, "branch_key", ""))
            hidden_stems = {hidden_stem for hidden_stem, _weight in BRANCH_HIDDEN_STEMS.get(branch_key, [])}
            if stem in hidden_stems:
                root_positions.append(root_position)
        if not root_positions:
            continue
        signals.append(
            _rooting_signal(
                chart_structure,
                mode="root",
                stem=stem,
                element=element,
                group=group,
                positions=[position],
                root_positions=_unique(root_positions),
            )
        )
    return signals


def _control_status(chart_structure: Any, source: str, target: str) -> str:
    judgment = _relation_judgment(
        relation="controls",
        source_context=_role_context(chart_structure, source),
        target_context=_role_context(chart_structure, target),
    )
    return _status_from_judgment("controls", judgment)


def _generation_status(chart_structure: Any, source: str, target: str) -> str:
    judgment = _relation_judgment(
        relation="generates",
        source_context=_role_context(chart_structure, source),
        target_context=_role_context(chart_structure, target),
    )
    return _status_from_judgment("generates", judgment)


def _build_edge_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    group_scores = chart_structure.ten_god_profile.group_scores
    for source, target in ROLE_GENERATES.items():
        if float(group_scores.get(source, 0.0) or 0.0) < 0.18 and float(group_scores.get(target, 0.0) or 0.0) < 0.18:
            continue
        signals.append(
            _edge_signal(
                chart_structure,
                relation="generates",
                source=source,
                target=target,
                status=_generation_status(chart_structure, source, target),
                sentence=GENERATE_SENTENCES[(source, target)],
            )
        )
    for source, target in ROLE_CONTROLS.items():
        if float(group_scores.get(source, 0.0) or 0.0) < 0.18 and float(group_scores.get(target, 0.0) or 0.0) < 0.18:
            continue
        status = _control_status(chart_structure, source, target)
        sentence_source = CONTROL_REGULATION_SENTENCES if status in {"regulates_pressure", "sets_boundary"} else CONTROL_DAMAGE_SENTENCES
        signals.append(
            _edge_signal(
                chart_structure,
                relation="controls",
                source=source,
                target=target,
                status=status,
                sentence=sentence_source[(source, target)],
            )
        )
    return signals


def _domain_summary(signals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for domain in ("money", "career", "love", "marriage", "personality"):
        domain_signals = [signal for signal in signals if domain in list(signal.get("domain_links") or [])]
        summary[domain] = {
            "support_count": sum(1 for signal in domain_signals if signal.get("polarity") == "support"),
            "mixed_count": sum(1 for signal in domain_signals if signal.get("polarity") == "mixed"),
            "pressure_count": sum(1 for signal in domain_signals if signal.get("polarity") == "pressure"),
            "top_signal_ids": [str(signal.get("signal_id") or "") for signal in domain_signals[:5]],
            "support_signal_ids": [str(signal.get("signal_id") or "") for signal in domain_signals if signal.get("polarity") == "support"][:5],
            "caution_signal_ids": [str(signal.get("signal_id") or "") for signal in domain_signals if signal.get("polarity") in {"mixed", "pressure"}][:5],
            "top_classical_names": _unique([str(signal.get("classical_name") or "") for signal in domain_signals[:5]]),
        }
    return summary


def _personality_summary(signals: list[dict[str, Any]]) -> dict[str, Any]:
    personality_signals = [
        signal
        for signal in signals
        if "personality" in list(signal.get("domain_links") or [])
    ]
    support = [signal for signal in personality_signals if signal.get("polarity") == "support"]
    pressure = [signal for signal in personality_signals if signal.get("polarity") == "pressure"]
    mixed = [signal for signal in personality_signals if signal.get("polarity") == "mixed"]
    return {
        "support_count": len(support),
        "mixed_count": len(mixed),
        "pressure_count": len(pressure),
        "top_signal_ids": [str(signal.get("signal_id") or "") for signal in personality_signals[:6]],
        "behavior_support_codes": _unique(
            [
                f"cycle_personality_support_{signal.get('signal_id')}"
                for signal in support[:6]
            ]
        ),
        "behavior_pressure_codes": _unique(
            [
                f"cycle_personality_pressure_{signal.get('signal_id')}"
                for signal in pressure[:6]
            ]
        ),
        "classical_names": _unique([str(signal.get("classical_name") or "") for signal in personality_signals[:8]]),
        "judgments": _unique([str(signal.get("cycle_judgment") or "") for signal in personality_signals[:8]]),
    }


def _principle_coverage(signals: list[dict[str, Any]]) -> dict[str, Any]:
    ten_god_edges = [signal for signal in signals if signal.get("relation") in {"generates", "controls"}]
    element_edges = [signal for signal in signals if signal.get("relation") in {"element_generates", "element_controls"}]
    element_bridges = [signal for signal in signals if signal.get("relation") == "element_bridge"]
    element_exceptions = [signal for signal in signals if signal.get("relation") == "element_exception"]
    branch_cycles = [signal for signal in signals if signal.get("relation") == "branch_cycle"]
    stem_combines = [signal for signal in signals if signal.get("relation") == "stem_combine"]
    hidden_protrusions = [signal for signal in signals if signal.get("relation") == "hidden_protrusion"]
    visible_roots = [signal for signal in signals if signal.get("relation") == "visible_root"]
    chains = [signal for signal in signals if signal.get("relation") == "chain"]
    governance_verdicts = [
        str(dict(signal.get("governance_context") or {}).get("verdict") or "")
        for signal in signals
        if dict(signal.get("governance_context") or {}).get("verdict")
    ]
    pattern_cycle_verdicts = [
        str(dict(signal.get("pattern_cycle_context") or {}).get("verdict") or "")
        for signal in signals
        if dict(signal.get("pattern_cycle_context") or {}).get("matched_rule_keys")
    ]
    pattern_reality_grades = [
        str(dict(signal.get("pattern_cycle_context") or {}).get("reality_grade") or "")
        for signal in signals
        if dict(signal.get("pattern_cycle_context") or {}).get("matched_rule_keys")
    ]
    condition_verdicts = [
        str(dict(signal.get("condition_context") or {}).get("verdict") or "")
        for signal in signals
        if dict(signal.get("condition_context") or {}).get("verdict")
    ]
    branch_reality_grades = [
        str(dict(signal.get("branch_reality_context") or {}).get("grade") or "")
        for signal in signals
        if dict(signal.get("branch_reality_context") or {}).get("grade")
    ]
    return {
        "ten_god_edge_count": len(ten_god_edges),
        "element_edge_count": len(element_edges),
        "element_bridge_count": len(element_bridges),
        "element_exception_count": len(element_exceptions),
        "branch_cycle_count": len(branch_cycles),
        "stem_combine_count": len(stem_combines),
        "hidden_protrusion_count": len(hidden_protrusions),
        "visible_root_count": len(visible_roots),
        "chain_count": len(chains),
        "governance_context_count": len(governance_verdicts),
        "governance_verdicts": _unique(governance_verdicts),
        "pattern_cycle_match_count": len(pattern_cycle_verdicts),
        "pattern_cycle_verdicts": _unique(pattern_cycle_verdicts),
        "pattern_cycle_reality_grades": _unique(pattern_reality_grades),
        "condition_context_count": len(condition_verdicts),
        "condition_verdicts": _unique(condition_verdicts),
        "branch_reality_context_count": len(branch_reality_grades),
        "branch_reality_grades": _unique(branch_reality_grades),
        "classical_names": _unique([str(signal.get("classical_name") or "") for signal in signals]),
        "supportive_signal_ids": [str(signal.get("signal_id") or "") for signal in signals if signal.get("polarity") == "support"],
        "pressure_signal_ids": [str(signal.get("signal_id") or "") for signal in signals if signal.get("polarity") == "pressure"],
    }


def _build_element_edge_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    score_map = chart_structure.element_profile.scores
    for source in ELEMENTS:
        target = ELEMENT_GENERATES[source]
        source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
        target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
        if source_score >= 0.035 or target_score >= 0.035:
            signals.append(_element_edge_signal(chart_structure, relation="generates", source=source, target=target))
    for source in ELEMENTS:
        target = ELEMENT_CONTROLS[source]
        source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
        target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
        if source_score >= 0.035 or target_score >= 0.035:
            signals.append(_element_edge_signal(chart_structure, relation="controls", source=source, target=target))
    return signals


def _build_element_bridge_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    score_map = chart_structure.element_profile.scores
    for source in ELEMENTS:
        target = ELEMENT_CONTROLS[source]
        bridge = ELEMENT_GENERATES[source]
        source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
        bridge_score = float(getattr(score_map[bridge], "ratio", 0.0) or 0.0)
        target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
        if max(source_score, bridge_score, target_score) >= 0.035:
            signals.append(_element_bridge_signal(chart_structure, source=source, bridge=bridge, target=target))
    return signals


def _build_element_exception_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    score_map = chart_structure.element_profile.scores
    for source in ELEMENTS:
        target = ELEMENT_GENERATES[source]
        source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
        target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
        if source_score >= 0.035 or target_score >= 0.035:
            signal = _element_exception_signal(chart_structure, relation="generates", source=source, target=target)
            if signal is not None:
                signals.append(signal)
    for source in ELEMENTS:
        target = ELEMENT_CONTROLS[source]
        source_score = float(getattr(score_map[source], "ratio", 0.0) or 0.0)
        target_score = float(getattr(score_map[target], "ratio", 0.0) or 0.0)
        if source_score >= 0.035 or target_score >= 0.035:
            signal = _element_exception_signal(chart_structure, relation="controls", source=source, target=target)
            if signal is not None:
                signals.append(signal)
    return signals


def _build_branch_cycle_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for interaction in list(getattr(chart_structure, "branch_interactions", []) or []):
        signal = _branch_cycle_signal(chart_structure, interaction)
        if signal is not None:
            signals.append(signal)
    return signals


def _has_role(chart_structure: Any, group: str, minimum: float = 0.18) -> bool:
    return float(chart_structure.ten_god_profile.group_scores.get(group, 0.0) or 0.0) >= minimum


def _pressure_greater(chart_structure: Any, group: str) -> bool:
    support, pressure = _fit_scores(chart_structure.month_governance_profile, group)
    return pressure > support


def _support_not_weaker(chart_structure: Any, group: str) -> bool:
    support, pressure = _fit_scores(chart_structure.month_governance_profile, group)
    return support >= pressure


def _chain_signal(chart_structure: Any, signal_id: str, groups: list[str], status: str, sentence: str) -> dict[str, Any]:
    group_scores = chart_structure.ten_god_profile.group_scores
    source_score = sum(float(group_scores.get(group, 0.0) or 0.0) for group in groups)
    support = sum(_fit_scores(chart_structure.month_governance_profile, group)[0] for group in groups)
    pressure = sum(_fit_scores(chart_structure.month_governance_profile, group)[1] for group in groups)
    group_contexts = [_role_context(chart_structure, group) for group in groups]
    judgment = CHAIN_STATUS_JUDGMENT.get(status, "strained_generation")
    classical_name = CHAIN_CLASSICAL_NAMES.get(signal_id, signal_id)
    target_index = CHAIN_DECISION_TARGET_INDEX.get(signal_id, -1)
    source_context = group_contexts[0]
    target_context = group_contexts[target_index]
    force_balance = _force_balance_context(
        relation="chain",
        source_context=source_context,
        target_context=target_context,
    )
    basis_codes = (
        _basis_for(chart_structure, *groups)
        + [f"cycle_chain_{signal_id}"]
        + _relation_basis_codes(
            layer="chain",
            relation="chain",
            source_key=groups[0],
            target_key=groups[target_index],
            source_context=source_context,
            target_context=target_context,
            judgment=judgment,
            classical_name=classical_name,
        )
        + _force_balance_basis_codes(force_balance)
    )
    return {
        "signal_id": signal_id,
        "layer": "cycle_regulation",
        "relation": "chain",
        "status": status,
        "cycle_judgment": judgment,
        "cycle_judgment_label": JUDGMENT_LABELS.get(judgment, judgment),
        "month_command_verdict": _month_command_verdict("chain", judgment),
        "month_command_verdict_label": MONTH_VERDICT_LABELS.get(_month_command_verdict("chain", judgment), ""),
        "decision_reason": (
            _decision_reason(
                relation="chain",
                source_context=source_context,
                target_context=target_context,
                judgment=judgment,
            )
            + " "
            + CHAIN_DECISION_NOTES.get(signal_id, "")
        ).strip(),
        "polarity": JUDGMENT_POLARITY.get(judgment, "mixed"),
        "classical_name": classical_name,
        "classical_theory": "둘 이상의 생극이 이어져 한쪽 기운을 키우거나 제어하는 연쇄입니다.",
        "groups": groups,
        "group_labels": [ROLE_LABELS[group] for group in groups],
        "elements": [_role_element(chart_structure.day_master_element, group) for group in groups],
        "score": max(42, min(98, 45 + round(source_score * 4) + support + pressure)),
        "domain_links": _domains_for(*groups),
        "sentence": sentence,
        "group_contexts": group_contexts,
        "force_balance_context": force_balance,
        "reality_score": min(99, sum(int(context["reality_score"]) for context in group_contexts)),
        "basis_codes": _unique(basis_codes),
    }


def _build_chain_signals(chart_structure: Any) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if _has_role(chart_structure, "wealth") and _has_role(chart_structure, "officer") and _has_role(chart_structure, "peer"):
        wealth_support, wealth_pressure = _fit_scores(chart_structure.month_governance_profile, "wealth")
        if _support_not_weaker(chart_structure, "officer") and wealth_pressure <= wealth_support:
            status = "regulates_pressure"
            sentence = CHAIN_SENTENCES["wealth_generates_officer_controls_peer"]
        elif _support_not_weaker(chart_structure, "officer"):
            status = "regulates_with_cost"
            sentence = CHAIN_SENTENCES["wealth_generates_officer_controls_peer_with_cost"]
        else:
            status = "mixed_chain"
            sentence = CHAIN_SENTENCES["wealth_generates_officer_controls_peer"]
        signals.append(
            _chain_signal(
                chart_structure,
                "wealth_generates_officer_controls_peer",
                ["wealth", "officer", "peer"],
                status,
                sentence,
            )
        )
    if _has_role(chart_structure, "wealth") and _has_role(chart_structure, "resource"):
        if _pressure_greater(chart_structure, "resource") or _has_role(chart_structure, "output"):
            signals.append(
                _chain_signal(
                    chart_structure,
                    "wealth_controls_resource_releases_output",
                    ["wealth", "resource", "output"],
                    "regulates_pressure" if _pressure_greater(chart_structure, "resource") else "sets_boundary",
                    CHAIN_SENTENCES["wealth_controls_resource_releases_output"],
                )
            )
    if _has_role(chart_structure, "output") and _has_role(chart_structure, "officer"):
        if _pressure_greater(chart_structure, "officer") or _support_not_weaker(chart_structure, "output"):
            signals.append(
                _chain_signal(
                    chart_structure,
                    "output_controls_officer_reduces_pressure",
                    ["output", "officer"],
                    "regulates_pressure" if _pressure_greater(chart_structure, "officer") else "sets_boundary",
                    CHAIN_SENTENCES["output_controls_officer_reduces_pressure"],
                )
            )
    if _has_role(chart_structure, "officer") and _has_role(chart_structure, "resource"):
        signals.append(
            _chain_signal(
                chart_structure,
                "officer_generates_resource_protects_body",
                ["officer", "resource"],
                "feeds_useful_force" if _support_not_weaker(chart_structure, "resource") else "mixed_chain",
                CHAIN_SENTENCES["officer_generates_resource_protects_body"],
            )
        )
    if _has_role(chart_structure, "output") and _has_role(chart_structure, "wealth") and _has_role(chart_structure, "officer"):
        signals.append(
            _chain_signal(
                chart_structure,
                "output_generates_wealth_then_officer",
                ["output", "wealth", "officer"],
                "connects_function",
                CHAIN_SENTENCES["output_generates_wealth_then_officer"],
            )
        )
    if _has_role(chart_structure, "resource") and _has_role(chart_structure, "output"):
        if _pressure_greater(chart_structure, "resource"):
            signals.append(
                _chain_signal(
                    chart_structure,
                    "resource_controls_output_dosik",
                    ["resource", "output"],
                    "damages_useful_force",
                    CHAIN_SENTENCES["resource_controls_output_dosik"],
                )
            )
    return signals


def _matrix_presence_grade(presence_score: float, reality_score: int) -> str:
    if presence_score >= 1.6 or reality_score >= 12:
        return "strong"
    if presence_score >= 0.85 or reality_score >= 8:
        return "clear"
    if presence_score >= 0.25 or reality_score >= 4:
        return "weak"
    if presence_score > 0 or reality_score > 0:
        return "trace"
    return "absent"


def _matrix_scope(
    *,
    source_grade: str,
    target_grade: str,
    relation_verdict: str,
    reality_grade: str,
) -> str:
    if source_grade == "absent" and target_grade == "absent":
        return "not_present"
    if reality_grade in {"latent_edge", "one_sided_edge"} or "latent" in relation_verdict:
        return "latent_reference"
    if relation_verdict in {"edge_needed", "edge_useful"}:
        return "active_support"
    if relation_verdict in {"edge_useful_with_cost", "edge_pressure_with_use", "edge_mixed"}:
        return "active_mixed"
    if relation_verdict in {
        "edge_burdens_month",
        "edge_pressure",
        "overfeeds_target",
        "drains_source",
        "reverse_control",
        "failed_control",
        "damages_useful_force",
        "conflict_or_overload",
        "feeds_burden",
    }:
        return "active_pressure"
    if source_grade == "trace" or target_grade == "trace":
        return "trace_reference"
    return "reference"


def _matrix_domain_projection(source: str, target: str, relation: str, verdict: str, scope: str) -> dict[str, str]:
    projection = dict(ROLE_EDGE_DOMAIN_AXES.get((source, target, relation), {}))
    if not projection:
        return {}
    if scope in {"latent_reference", "trace_reference"}:
        suffix = " 이 축은 약하게 남아 보조 판단에 둡니다."
    elif verdict in {"edge_burdens_month", "edge_pressure"}:
        suffix = " 이 축은 부담으로 나타납니다."
    elif verdict in {"edge_pressure_with_use", "edge_useful_with_cost", "edge_mixed"}:
        suffix = " 이 축은 장점과 부담이 함께 나타납니다."
    elif verdict in {"edge_needed", "edge_useful"}:
        suffix = " 이 축은 강점으로 나타납니다."
    elif verdict in {"overfeeds_target", "drains_source", "reverse_control", "failed_control", "damages_useful_force", "conflict_or_overload", "feeds_burden"}:
        suffix = " 이 축은 부담으로 나타납니다."
    else:
        suffix = " 이 축은 보조 판단으로 남습니다."
    return {domain: f"{text}.{suffix}" for domain, text in projection.items()}


def _role_edge_matrix_item(chart_structure: Any, *, source: str, target: str, relation: str) -> dict[str, Any]:
    contexts = [_role_context(chart_structure, group) for group in ROLE_ORDER]
    pseudo_signal = {
        "signal_id": f"matrix_{relation}_{source}_to_{target}",
        "relation": relation,
        "source_group": source,
        "target_group": target,
        "groups": [source, target],
    }
    edge = _edge_fit_context(chart_structure, pseudo_signal, contexts, (source, target, relation))
    source_context = _context_for_group(contexts, source)
    target_context = _context_for_group(contexts, target)
    force_balance = _force_balance_context(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    source_presence_score = float(source_context.get("presence_score") or 0.0)
    target_presence_score = float(target_context.get("presence_score") or 0.0)
    source_reality = int(source_context.get("reality_score") or 0)
    target_reality = int(target_context.get("reality_score") or 0)
    source_grade = _matrix_presence_grade(source_presence_score, source_reality)
    target_grade = _matrix_presence_grade(target_presence_score, target_reality)
    verdict = str(edge.get("verdict") or "")
    reality_grade = str(edge.get("edge_reality_grade") or "")
    classical_name = ROLE_EDGE_CLASSICAL_NAMES.get((source, target, relation), f"{source}_{relation}_{target}")
    scope = _matrix_scope(
        source_grade=source_grade,
        target_grade=target_grade,
        relation_verdict=verdict,
        reality_grade=reality_grade,
    )

    return {
        "edge_key": f"{source}_{relation}_{target}",
        "classical_name": classical_name,
        "relation": relation,
        "source_group": source,
        "target_group": target,
        "source_label": ROLE_LABELS.get(source, source),
        "target_label": ROLE_LABELS.get(target, target),
        "source_element": _role_element(chart_structure.day_master_element, source),
        "target_element": _role_element(chart_structure.day_master_element, target),
        "source_presence_score": round(source_presence_score, 3),
        "target_presence_score": round(target_presence_score, 3),
        "source_presence_grade": source_grade,
        "target_presence_grade": target_grade,
        "source_reality_score": source_reality,
        "target_reality_score": target_reality,
        "edge_reality_grade": reality_grade,
        "force_balance_context": force_balance,
        "source_force_index": force_balance["source_force_index"],
        "target_force_index": force_balance["target_force_index"],
        "force_balance": force_balance["balance"],
        "force_effect": force_balance["effect"],
        "month_fit_verdict": verdict,
        "support_score": int(edge.get("support_score") or 0),
        "pressure_score": int(edge.get("pressure_score") or 0),
        "net_score": int(edge.get("net_score") or 0),
        "scope": scope,
        "touches_month_command": bool(edge.get("touches_month_command")),
        "uses_pattern_support": bool(edge.get("uses_pattern_support")),
        "uses_pattern_caution": bool(edge.get("uses_pattern_caution")),
        "domain_links": _domains_for(source, target),
        "domain_projection": _matrix_domain_projection(source, target, relation, verdict, scope),
        "reasons": list(edge.get("reasons") or []),
        "caution_reasons": list(edge.get("caution_reasons") or []),
        "basis_codes": _unique(
            [
                f"principle_matrix_role_edge_{source}_{relation}_{target}",
                f"principle_matrix_role_scope_{_matrix_scope(source_grade=source_grade, target_grade=target_grade, relation_verdict=verdict, reality_grade=reality_grade)}",
                f"principle_matrix_role_month_fit_{verdict}",
                f"principle_matrix_role_reality_{reality_grade}",
                *_force_balance_basis_codes(force_balance),
            ]
        ),
    }


def _element_edge_matrix_item(chart_structure: Any, *, source: str, target: str, relation: str) -> dict[str, Any]:
    source_context = _element_context(chart_structure, source)
    target_context = _element_context(chart_structure, target)
    force_balance = _force_balance_context(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    judgment = _relation_judgment(
        relation=relation,
        source_context=source_context,
        target_context=target_context,
    )
    source_presence_score = float(source_context.get("presence_score") or 0.0)
    target_presence_score = float(target_context.get("presence_score") or 0.0)
    source_reality = int(source_context.get("reality_score") or 0)
    target_reality = int(target_context.get("reality_score") or 0)
    source_grade = _matrix_presence_grade(source_presence_score * 5, source_reality)
    target_grade = _matrix_presence_grade(target_presence_score * 5, target_reality)
    reality = _edge_reality_context(source_context, target_context)
    source_group = _group_for_element(chart_structure.day_master_element, source)
    target_group = _group_for_element(chart_structure.day_master_element, target)
    verdict = _status_from_judgment(relation, judgment)
    relation_label = "생" if relation == "generates" else "극"
    classical_name = f"{ELEMENT_LABELS.get(source, source)}{relation_label}{ELEMENT_LABELS.get(target, target)}"

    return {
        "edge_key": f"{source}_{relation}_{target}",
        "classical_name": classical_name,
        "relation": relation,
        "source_element": source,
        "target_element": target,
        "source_label": ELEMENT_LABELS.get(source, source),
        "target_label": ELEMENT_LABELS.get(target, target),
        "source_group": source_group,
        "target_group": target_group,
        "source_presence_score": round(source_presence_score, 3),
        "target_presence_score": round(target_presence_score, 3),
        "source_presence_grade": source_grade,
        "target_presence_grade": target_grade,
        "source_reality_score": source_reality,
        "target_reality_score": target_reality,
        "edge_reality_grade": str(reality.get("edge_reality_grade") or ""),
        "force_balance_context": force_balance,
        "source_force_index": force_balance["source_force_index"],
        "target_force_index": force_balance["target_force_index"],
        "force_balance": force_balance["balance"],
        "force_effect": force_balance["effect"],
        "cycle_judgment": judgment,
        "month_command_verdict": _month_command_verdict(relation, judgment),
        "support_score": int(source_context.get("support_score") or 0) + int(target_context.get("support_score") or 0),
        "pressure_score": int(source_context.get("pressure_score") or 0) + int(target_context.get("pressure_score") or 0),
        "net_score": int(source_context.get("net_fit") or 0) + int(target_context.get("net_fit") or 0),
        "scope": _matrix_scope(
            source_grade=source_grade,
            target_grade=target_grade,
            relation_verdict=verdict,
            reality_grade=str(reality.get("edge_reality_grade") or ""),
        ),
        "domain_links": _domains_for(source_group, target_group),
        "basis_codes": _unique(
            [
                f"principle_matrix_element_edge_{source}_{relation}_{target}",
                f"principle_matrix_element_scope_{_matrix_scope(source_grade=source_grade, target_grade=target_grade, relation_verdict=verdict, reality_grade=str(reality.get('edge_reality_grade') or ''))}",
                f"principle_matrix_element_judgment_{judgment}",
                *_force_balance_basis_codes(force_balance),
            ]
        ),
    }


def _branch_relation_matrix_items(chart_structure: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for interaction in list(getattr(chart_structure, "branch_interactions", []) or []):
        polarity = branch_relation_polarity(
            chart_structure.element_profile,
            interaction,
            getattr(chart_structure, "pattern_profile", None),
        )
        activated_elements = relation_activated_elements(interaction)
        activated_groups = _unique(
            [
                _group_for_element(chart_structure.day_master_element, element)
                for element in activated_elements
            ]
        )
        items.append(
            {
                "relation_type": str(getattr(interaction, "relation_type", "") or ""),
                "branches": list(getattr(interaction, "branches", []) or []),
                "positions": list(getattr(interaction, "positions", []) or []),
                "intensity": str(getattr(interaction, "intensity", "") or ""),
                "activated_elements": activated_elements,
                "activated_groups": activated_groups,
                "polarity": str(getattr(polarity, "polarity", "") or ""),
                "useful_score": int(getattr(polarity, "useful_score", 0) or 0),
                "pressure_score": int(getattr(polarity, "pressure_score", 0) or 0),
                "intrinsic_friction": float(getattr(polarity, "intrinsic_friction", 0.0) or 0.0),
                "effective_friction": float(getattr(polarity, "effective_friction", 0.0) or 0.0),
                "domain_links": _unique(
                    list(getattr(interaction, "domain_links", []) or [])
                    + [domain for group in activated_groups for domain in ROLE_DOMAIN_LINKS.get(group, [])]
                ),
                "basis_codes": _unique(
                    [
                        f"principle_matrix_branch_relation_{getattr(interaction, 'relation_type', '')}",
                        *(
                            [
                                f"principle_matrix_branch_structural_friction_{getattr(interaction, 'relation_type', '')}"
                            ]
                            if float(getattr(polarity, "effective_friction", 0.0) or 0.0) > 0.0
                            else []
                        ),
                        *[f"principle_matrix_branch_element_{element}" for element in activated_elements],
                    ]
                ),
            }
        )
    return items


def _source_reality_summary(chart_structure: Any) -> dict[str, Any]:
    role_sources: dict[str, dict[str, Any]] = {
        group: {
            "visible_stem_positions": [],
            "branch_main_positions": [],
            "hidden_positions": [],
            "protruded_hidden_positions": [],
        }
        for group in ROLE_ORDER
    }
    visible_stems = {signal.stem_key for signal in chart_structure.position_signals.values()}
    for position, signal in chart_structure.position_signals.items():
        stem_group = TEN_GOD_GROUPS.get(signal.stem_ten_god, "")
        if stem_group in role_sources:
            role_sources[stem_group]["visible_stem_positions"].append(position)
        branch_group = TEN_GOD_GROUPS.get(signal.branch_main_ten_god, "")
        if branch_group in role_sources:
            role_sources[branch_group]["branch_main_positions"].append(position)
        for stem_key, _weight in BRANCH_HIDDEN_STEMS.get(signal.branch_key, []):
            hidden_group = _group_for_element(
                chart_structure.day_master_element,
                STEM_METADATA[stem_key]["element"],
            )
            if hidden_group in role_sources:
                role_sources[hidden_group]["hidden_positions"].append(position)
                if stem_key in visible_stems:
                    role_sources[hidden_group]["protruded_hidden_positions"].append(position)
    return {
        group: {
            key: _unique([str(position) for position in positions])
            for key, positions in values.items()
        }
        for group, values in role_sources.items()
    }


def _build_principle_matrix(chart_structure: Any, signals: list[dict[str, Any]]) -> dict[str, Any]:
    role_edges = [
        _role_edge_matrix_item(chart_structure, source=source, target=target, relation="generates")
        for source, target in ROLE_GENERATES.items()
    ] + [
        _role_edge_matrix_item(chart_structure, source=source, target=target, relation="controls")
        for source, target in ROLE_CONTROLS.items()
    ]
    element_edges = [
        _element_edge_matrix_item(chart_structure, source=source, target=ELEMENT_GENERATES[source], relation="generates")
        for source in ELEMENTS
    ] + [
        _element_edge_matrix_item(chart_structure, source=source, target=ELEMENT_CONTROLS[source], relation="controls")
        for source in ELEMENTS
    ]
    active_role_edges = [item for item in role_edges if str(item.get("scope") or "").startswith("active")]
    latent_role_edges = [item for item in role_edges if str(item.get("scope") or "") in {"latent_reference", "trace_reference"}]
    pressure_role_edges = [item for item in role_edges if item.get("scope") == "active_pressure"]
    matrix_basis_codes = [
        code
        for item in role_edges + element_edges
        for code in list(item.get("basis_codes") or [])
    ]
    month_hidden_phase = getattr(chart_structure.month_governance_profile, "month_hidden_phase", None)
    month_hidden_phase_anchor: dict[str, Any] | None = None
    if month_hidden_phase is not None:
        month_hidden_phase_anchor = {
            "rule_version": str(getattr(month_hidden_phase, "rule_version", "") or ""),
            "day_index_from_boundary": getattr(month_hidden_phase, "day_index_from_boundary", 0.0),
            "active_phase": str(getattr(month_hidden_phase, "active_phase", "") or ""),
            "active_stem": str(getattr(month_hidden_phase, "active_stem", "") or ""),
            "active_element": str(getattr(month_hidden_phase, "active_element", "") or ""),
            "active_ten_god": str(getattr(month_hidden_phase, "active_ten_god", "") or ""),
            "active_ten_god_group": str(getattr(month_hidden_phase, "active_ten_god_group", "") or ""),
            "basis_codes": list(getattr(month_hidden_phase, "basis_codes", []) or []),
        }
        matrix_basis_codes.extend(month_hidden_phase_anchor["basis_codes"])

    return {
        "version": PRINCIPLE_MATRIX_VERSION,
        "month_anchor": {
            "month_branch": str(getattr(chart_structure, "month_branch", "") or ""),
            "month_element": str(getattr(chart_structure.month_governance_profile, "month_element", "") or ""),
            "month_command_ten_god": str(getattr(chart_structure.month_governance_profile, "month_command_ten_god", "") or ""),
            "month_command_group": str(getattr(chart_structure.month_governance_profile, "month_command_group", "") or ""),
            "regular_pattern": str(getattr(chart_structure.month_governance_profile, "regular_pattern", "") or ""),
            "useful_groups": list(getattr(chart_structure.month_governance_profile, "useful_groups", []) or []),
            "caution_groups": list(getattr(chart_structure.month_governance_profile, "caution_groups", []) or []),
            "useful_elements": list(getattr(chart_structure.month_governance_profile, "useful_elements", []) or []),
            "caution_elements": list(getattr(chart_structure.month_governance_profile, "caution_elements", []) or []),
            "month_hidden_phase": month_hidden_phase_anchor,
        },
        "role_edges": role_edges,
        "element_edges": element_edges,
        "branch_relations": _branch_relation_matrix_items(chart_structure),
        "source_reality": _source_reality_summary(chart_structure),
        "signal_links": {
            "active_signal_ids": [str(signal.get("signal_id") or "") for signal in signals[:12]],
            "chain_signal_ids": [str(signal.get("signal_id") or "") for signal in signals if signal.get("relation") == "chain"],
            "branch_signal_ids": [str(signal.get("signal_id") or "") for signal in signals if signal.get("relation") == "branch_cycle"],
            "hidden_signal_ids": [
                str(signal.get("signal_id") or "")
                for signal in signals
                if signal.get("relation") in {"hidden_protrusion", "visible_root"}
            ],
        },
        "coverage": {
            "role_edge_count": len(role_edges),
            "element_edge_count": len(element_edges),
            "branch_relation_count": len(getattr(chart_structure, "branch_interactions", []) or []),
            "active_role_edge_count": len(active_role_edges),
            "latent_role_edge_count": len(latent_role_edges),
            "pressure_role_edge_count": len(pressure_role_edges),
            "month_touched_role_edge_count": sum(1 for item in role_edges if item.get("touches_month_command")),
            "basis_code_count": len(_unique(matrix_basis_codes)),
        },
        "basis_codes": _unique(matrix_basis_codes),
    }


def build_cycle_regulation_profile(chart_structure: Any) -> dict[str, Any]:
    """Return rule-level 생극 circulation signals for a chart structure."""

    signals = _attach_governance_context(chart_structure, [
        *_build_chain_signals(chart_structure),
        *_build_edge_signals(chart_structure),
        *_build_element_edge_signals(chart_structure),
        *_build_element_bridge_signals(chart_structure),
        *_build_element_exception_signals(chart_structure),
        *_build_branch_cycle_signals(chart_structure),
        *_build_stem_combine_signals(chart_structure),
        *_build_hidden_protrusion_signals(chart_structure),
        *_build_visible_root_signals(chart_structure),
    ])
    signals.sort(
        key=lambda signal: (
            0
            if signal.get("polarity") == "support"
            else 1
            if signal.get("polarity") == "mixed"
            else 2,
            -int(signal.get("reality_score", 0)),
            -int(signal.get("effect_strength", signal.get("score", 0))),
            str(signal.get("signal_id", "")),
        )
    )
    return {
        "version": CYCLE_REGULATION_VERSION,
        "score_contract": {
            "effect_strength_field": "effect_strength",
            "legacy_strength_alias": "score",
            "effect_strength_semantics": "magnitude_not_quality",
            "quality_direction_field": "polarity",
            "public_quality_rule": "derive_by_metric_context",
        },
        "signals": signals,
        "top_signal_ids": [str(signal["signal_id"]) for signal in signals[:8]],
        "domain_summary": _domain_summary(signals),
        "personality_summary": _personality_summary(signals),
        "principle_coverage": _principle_coverage(signals),
        "principle_matrix": _build_principle_matrix(chart_structure, signals),
    }
