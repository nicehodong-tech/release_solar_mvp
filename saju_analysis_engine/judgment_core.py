"""Domain-level judgment synthesis.

This module is the bridge between raw saju materials and customer report prose.
It does not replace EventPacket scoring. It preserves why a domain conclusion
was made, with month command, branch reality, hidden stems, protrusion/rooting,
relations, element texture, ten-god roles, reception, and fortune activation
kept as separate judgment materials.
"""

from __future__ import annotations

import re
from typing import Any

from .branch_reality_profiles import branch_domain_texture, branch_position_texture
from .constants import BRANCH_HIDDEN_STEMS, ELEMENT_CONTROLS, ELEMENT_GENERATES, STEM_METADATA, TEN_GOD_GROUPS
from .cycle_regulation import build_cycle_regulation_profile
from .gyeokguk_ten_god_actions import TEN_GOD_EXACT_ACTION_PROFILE, TEN_GOD_EXACT_NUANCE
from .models import AnalysisResult, BranchInteraction, Domain, EventPacket, PositionSignal
from .relation_polarity import branch_relation_polarity
from .rendering import DOMAIN_LABELS
from .ten_gods import ten_god_for


JUDGMENT_CONTEXT_VERSION = "domain_judgment_context_v1"

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

STEM_LABELS = {
    "gap": "甲",
    "eul": "乙",
    "byeong": "丙",
    "jeong": "丁",
    "mu": "戊",
    "gi": "己",
    "gyeong": "庚",
    "sin": "辛",
    "im": "壬",
    "gye": "癸",
}

BRANCH_LABELS = {
    "ja": "子",
    "chuk": "丑",
    "in": "寅",
    "myo": "卯",
    "jin": "辰",
    "sa": "巳",
    "o": "午",
    "mi": "未",
    "sin": "申",
    "yu": "酉",
    "sul": "戌",
    "hae": "亥",
}

HANJA_HAS_JONGSEONG = {
    "甲": True,
    "乙": True,
    "丙": True,
    "丁": True,
    "戊": False,
    "己": False,
    "庚": True,
    "辛": True,
    "壬": True,
    "癸": False,
    "子": False,
    "丑": True,
    "寅": True,
    "卯": False,
    "辰": True,
    "巳": False,
    "午": False,
    "未": False,
    "申": True,
    "酉": False,
    "戌": True,
    "亥": False,
}

TEN_GOD_LABELS = {
    "self": "일간",
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

TEN_GOD_GROUP_LABELS = {
    "peer": "비겁",
    "output": "식상",
    "wealth": "재성",
    "officer": "관성",
    "resource": "인성",
}

PATTERN_LABELS = {
    "direct_wealth_pattern": "정재격",
    "indirect_wealth_pattern": "편재격",
    "direct_officer_pattern": "정관격",
    "seven_killings_pattern": "편관격",
    "eating_god_pattern": "식신격",
    "hurting_officer_pattern": "상관격",
    "direct_resource_pattern": "정인격",
    "indirect_resource_pattern": "편인격",
    "jianlu_peer_pattern": "건록격",
    "yangren_peer_pattern": "양인격",
    "output_to_wealth": "식상이 재성으로 이어지는 구조",
    "officer_resource": "관성이 인성으로 이어지는 구조",
    "resource_supported": "인성이 일간을 받치는 구조",
    "wealth_pressure": "재성이 일간을 압박하는 구조",
    "peer_wealth_competition": "비겁과 재성이 맞서는 구조",
    "cold_storage_needs_fire": "차가운 기운에 화기가 필요한 구조",
    "hot_dry_needs_water": "뜨겁고 건조한 기운에 수기가 필요한 구조",
    "dominant_day_master_special_watch": "일간 기운이 강하게 몰린 구조",
    "mixed_balanced_structure": "여러 기운이 함께 섞인 구조",
}

PATTERN_DOMAIN_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "support": "재물에서는 이 기운이 수입을 자산으로 남깁니다.",
        "pressure": "재물에서는 이 기운이 지출과 책임 비용을 키웁니다.",
    },
    "career": {
        "support": "직업에서는 맡은 역할이 인정받는 힘으로 바뀝니다.",
        "pressure": "직업에서는 이 기운이 책임을 키우고 결정권을 늦춥니다.",
    },
    "love": {
        "support": "연애에서는 이 기운이 마음 표현을 부드럽게 만듭니다.",
        "pressure": "연애에서는 이 기운이 감정 확인을 잦게 만듭니다. 거리감도 예민해집니다.",
    },
    "marriage": {
        "support": "결혼에서는 이 기운이 생활 방식과 약속을 안정시킵니다.",
        "pressure": "결혼에서는 이 기운이 돈 문제로 결정을 압박합니다. 주거 문제도 따로 다루게 됩니다.",
    },
}

PATTERN_CONCLUSION_SUPPORT: dict[Domain, str] = {
    "money": "받을 돈이 손에 남는 돈으로 바뀝니다.",
    "career": "맡은 일로 인정받고 다음 역할도 생깁니다.",
    "love": "마음이 연락으로 전해지고 만남이 늘어납니다.",
    "marriage": "애정이 생활 약속으로 굳어집니다.",
}

PATTERN_CONCLUSION_PRESSURE: dict[Domain, str] = {
    "money": "정산과 지출 부담이 커집니다.",
    "career": "책임과 결정권 문제가 커집니다.",
    "love": "거리감과 감정 확인이 예민해집니다.",
    "marriage": "생활비와 책임 분담 문제가 무거워집니다.",
}

PATTERN_MOBILE_SUPPORT: dict[Domain, str] = {
    "money": "손에 남는 돈이 커집니다.",
    "career": "직업적으로 인정받습니다.",
    "love": "관계가 가까워집니다.",
    "marriage": "생활 약속이 안정됩니다.",
}

PATTERN_MOBILE_PRESSURE: dict[Domain, str] = {
    "money": "지출 부담이 커집니다.",
    "career": "책임 부담이 커집니다.",
    "love": "감정 확인이 예민해집니다.",
    "marriage": "생활 부담이 커집니다.",
}

REALITY_RELATION_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "supportive": "정산 약속이 분명해지고 받을 돈도 정해집니다.",
        "burdensome": "정산과 지출 약속이 흔들립니다.",
        "mixed": "돈의 기회와 정산 부담이 함께 옵니다.",
        "neutral": "돈의 기준을 다시 세우게 됩니다.",
    },
    "career": {
        "supportive": "역할이 바뀌고 평가도 달라집니다.",
        "burdensome": "책임과 결정권 문제가 직업 현장에서 커집니다.",
        "mixed": "새 역할과 부담이 함께 커집니다.",
        "neutral": "맡을 일의 기준을 다시 세우게 됩니다.",
    },
    "love": {
        "supportive": "연락이 늘고 만남의 성격이 달라집니다.",
        "burdensome": "거리감과 감정 확인이 관계의 부담으로 나옵니다.",
        "mixed": "가까워지는 계기와 감정 부담이 함께 옵니다.",
        "neutral": "연락 방식과 거리감을 다시 맞추게 됩니다.",
    },
    "marriage": {
        "supportive": "약속이 굳어지고 생활 이야기가 정리됩니다.",
        "burdensome": "생활비와 가족 책임 문제가 무겁게 나옵니다.",
        "mixed": "결혼 이야기와 생활 부담이 함께 커집니다.",
        "neutral": "생활 기준과 책임 범위를 다시 정하게 됩니다.",
    },
}

HIDDEN_REALITY_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "peer": "돈의 몫과 지출 기준이 생활 문제로 나옵니다.",
        "output": "만든 결과가 수입으로 바뀝니다.",
        "wealth": "받을 돈과 남길 돈이 분명하게 나뉩니다.",
        "officer": "계약서와 비용 책임을 먼저 정합니다.",
        "resource": "문서와 보존 기준으로 돈을 지킵니다.",
    },
    "career": {
        "peer": "동료와의 경쟁 속에서 자기 역할이 또렷해집니다.",
        "output": "결과물이 직업적 평가의 근거가 됩니다.",
        "wealth": "성과가 보상과 거래로 이어집니다.",
        "officer": "직책과 책임 기준이 맡는 일을 정합니다.",
        "resource": "자격과 문서가 직업 기반이 됩니다.",
    },
    "love": {
        "peer": "관계 안에서 자기 입장과 거리감을 분명히 세웁니다.",
        "output": "말투와 표현 방식이 마음을 전합니다.",
        "wealth": "상대의 기대와 현실 감각을 의식하게 됩니다.",
        "officer": "약속과 책임의 무게가 관계 안에서 커집니다.",
        "resource": "안정감과 보호받고 싶은 마음이 커집니다.",
    },
    "marriage": {
        "peer": "생활 주도권과 몫 나눔 문제가 생활 안에서 커집니다.",
        "output": "일상의 표현과 돌봄이 결혼 생활의 기준이 됩니다.",
        "wealth": "생활비와 자산 문제가 결혼 이야기의 핵심이 됩니다.",
        "officer": "부부 사이의 책임과 약속이 정해집니다.",
        "resource": "집의 안정감과 가족 보호 의식이 커집니다.",
    },
}

REALITY_MOBILE_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "relation": "정산 약속이 다시 바뀝니다.",
        "hidden": "숨은 재물 기준이 밖으로 나옵니다.",
        "branch": "돈의 현실 자리가 또렷해집니다.",
        "month": "돈이 남는 기준을 세웁니다.",
    },
    "career": {
        "relation": "역할이 바뀌며 평가 기준도 달라집니다.",
        "hidden": "숨은 실력이 역할로 나옵니다.",
        "branch": "직업의 현실 자리가 또렷해집니다.",
        "month": "책임과 평가 기준을 세웁니다.",
    },
    "love": {
        "relation": "연락 방식이 달라집니다.",
        "hidden": "속마음의 기준이 표현으로 나옵니다.",
        "branch": "관계의 현실 자리가 또렷해집니다.",
        "month": "연락의 안정감을 기준으로 세웁니다.",
    },
    "marriage": {
        "relation": "생활 이야기가 약속으로 굳어집니다.",
        "hidden": "숨은 생활 기준이 약속으로 나옵니다.",
        "branch": "결혼의 현실 자리가 또렷해집니다.",
        "month": "생활비와 책임 기준을 세웁니다.",
    },
}

FORTUNE_GROUP_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "peer": "돈의 몫과 지출 기준이 먼저 달라집니다.",
        "output": "해낸 일이 받을 돈으로 바뀝니다.",
        "wealth": "거래와 수입 기회가 생깁니다.",
        "officer": "계약서와 비용 책임이 재물 판단의 중심이 됩니다.",
        "resource": "문서와 안전장치가 재물 판단의 기준이 됩니다.",
    },
    "career": {
        "peer": "역할 경쟁과 자기 기준이 직업 장면에서 커집니다.",
        "output": "결과물이 평가의 근거가 됩니다.",
        "wealth": "성과가 보상과 업무 기회를 만듭니다.",
        "officer": "책임과 직책 문제가 직업운의 중심이 됩니다.",
        "resource": "자격과 근거가 평가의 기반이 됩니다.",
    },
    "love": {
        "peer": "자기 입장과 거리감이 관계 안에서 예민해집니다.",
        "output": "말과 행동으로 마음을 전하게 됩니다.",
        "wealth": "호감과 만남의 기회가 생깁니다.",
        "officer": "약속과 예의가 관계의 안정감을 만듭니다.",
        "resource": "상대의 반응을 살피며 마음을 정합니다.",
    },
    "marriage": {
        "peer": "생활 주도권과 몫 나눔 문제가 커집니다.",
        "output": "생활 약속을 행동으로 옮기게 됩니다.",
        "wealth": "생활비와 자산 문제가 결혼 이야기의 핵심이 됩니다.",
        "officer": "부부 사이의 책임 기준이 정해집니다.",
        "resource": "문서와 가족 인정이 결혼을 안정시킵니다.",
    },
}

FORTUNE_MOBILE_RESULTS: dict[Domain, str] = {
    "money": "세운과 대운에서는 수입과 지출이 함께 커집니다.",
    "career": "세운과 대운에서는 역할과 평가가 함께 커집니다.",
    "love": "세운과 대운에서는 연락과 만남이 관계 판단의 중심이 됩니다.",
    "marriage": "세운과 대운에서는 생활비와 책임이 함께 커집니다.",
}

CYCLE_SIGNAL_DOMAIN_JUDGMENTS: dict[str, dict[Domain, dict[str, str]]] = {
    "output_generates_wealth_then_officer": {
        "money": {
            "dimension": "수입 창출력",
            "principle": "식상생재가 재생관으로 이어지는 흐름입니다.",
            "adjudication": "만든 결과물이 돈으로 바뀌고, 그 돈이 다시 보상과 책임 자리로 연결됩니다.",
            "caution": "결과물이 약하면 수입도 약해지고, 보상 기준도 분명해지기 어렵습니다.",
        },
        "career": {
            "dimension": "성과 보상력",
            "principle": "식상생재 뒤에 재생관이 붙는 흐름입니다.",
            "adjudication": "실무 성과가 보상으로 잡히고, 그 보상이 직업적 책임과 평가로 이어집니다.",
            "caution": "성과는 있는데 평가 체계가 약하면 책임만 늘고 실속이 줄어듭니다.",
        },
        "love": {
            "dimension": "표현의 현실화",
            "principle": "식상에서 재성으로 이어지는 표현과 선택의 흐름입니다.",
            "adjudication": "마음이 말과 행동으로 드러나고, 실제 만남과 선택으로 이어집니다.",
            "caution": "표현만 앞서고 책임 있는 태도가 약하면 관계가 가볍게 보일 수 있습니다.",
        },
        "marriage": {
            "dimension": "생활 구성력",
            "principle": "식상생재가 생활 책임으로 이어지는 흐름입니다.",
            "adjudication": "일상의 행동과 경제 판단이 결혼 생활의 안정성으로 이어집니다.",
            "caution": "생활비와 역할 기준이 늦게 잡히면 약속이 느슨해질 수 있습니다.",
        },
    },
    "wealth_generates_officer_controls_peer": {
        "money": {
            "dimension": "재물 보존력",
            "principle": "재생관으로 관성이 비겁을 제어하는 흐름입니다.",
            "adjudication": "돈의 기준이 계약과 책임으로 잡히면서 공동 비용과 몫 다툼이 정리됩니다.",
            "caution": "관성이 약하면 돈은 생겨도 가까운 사람과 나눌 몫에서 말이 나옵니다.",
        },
        "career": {
            "dimension": "책임 전환력",
            "principle": "재성이 관성을 생하고 관성이 비겁을 제어하는 흐름입니다.",
            "adjudication": "성과와 보상이 직책, 권한, 공식 책임으로 바뀝니다.",
            "caution": "권한이 약하면 책임만 커지고 조직 안의 경쟁이 쉽게 정리되지 않습니다.",
        },
        "love": {
            "dimension": "관계 기준",
            "principle": "재성이 관성으로 이어져 관계 안의 책임 기준을 세우는 흐름입니다.",
            "adjudication": "호감이 실제 약속과 예의로 정리되며 관계의 방향이 분명해집니다.",
            "caution": "기준이 지나치게 강하면 감정보다 의무감이 앞설 수 있습니다.",
        },
        "marriage": {
            "dimension": "책임 분담력",
            "principle": "재생관이 생활 책임과 몫 나눔을 정리하는 흐름입니다.",
            "adjudication": "생활비, 역할, 책임 범위가 정리될수록 결혼 안정성이 올라갑니다.",
            "caution": "돈과 책임을 문서나 약속으로 정하지 않으면 가족 문제로 번질 수 있습니다.",
        },
    },
    "wealth_controls_resource_releases_output": {
        "money": {
            "dimension": "현실 판단력",
            "principle": "재극인으로 인성의 과잉을 누르고 식상 출력을 풀어내는 흐름입니다.",
            "adjudication": "생각과 검토에 머무르던 돈 문제가 실제 선택과 수입 활동으로 내려옵니다.",
            "caution": "재성이 과하면 돈 문제 때문에 공부, 자격, 문서 판단이 흔들릴 수 있습니다.",
        },
        "career": {
            "dimension": "실행 전환력",
            "principle": "재극인이 준비 과잉을 누르고 결과물을 밖으로 내는 흐름입니다.",
            "adjudication": "검토와 준비에 머물던 일이 실행, 실무, 결과물로 전환됩니다.",
            "caution": "현실 압박이 너무 강하면 근거를 충분히 갖추기 전에 움직이게 됩니다.",
        },
        "love": {
            "dimension": "감정 결정력",
            "principle": "재성이 인성을 제어해 생각의 지연을 줄이는 흐름입니다.",
            "adjudication": "머리로 오래 재던 마음이 실제 만남과 선택으로 움직입니다.",
            "caution": "현실 조건을 너무 빨리 따지면 감정의 여지가 줄어듭니다.",
        },
        "marriage": {
            "dimension": "결정 현실화",
            "principle": "재극인이 생활 조건을 앞세워 결정을 현실화하는 흐름입니다.",
            "adjudication": "막연한 고민보다 주거, 비용, 가족 조건을 기준으로 결혼 판단이 빨라집니다.",
            "caution": "돈과 조건만 앞서면 정서적 합의가 뒤처질 수 있습니다.",
        },
    },
    "output_controls_officer_reduces_pressure": {
        "money": {
            "dimension": "압박 처리력",
            "principle": "식상이 관성을 제어해 부담을 실무로 풀어내는 흐름입니다.",
            "adjudication": "계약과 책임에서 생긴 부담을 기술, 말, 처리 능력으로 줄입니다.",
            "caution": "표현이 거칠면 책임 기준과 부딪혀 돈 문제가 더 복잡해질 수 있습니다.",
        },
        "career": {
            "dimension": "실무 돌파력",
            "principle": "식신제살과 상관제관 계열의 압박 조절 흐름입니다.",
            "adjudication": "압박이 큰 일을 실무 능력과 문제 해결력으로 처리합니다.",
            "caution": "조직의 규칙을 정면으로 치면 능력보다 마찰이 먼저 보입니다.",
        },
        "love": {
            "dimension": "표현 조절력",
            "principle": "식상이 관성의 긴장을 풀어 관계 압박을 낮추는 흐름입니다.",
            "adjudication": "딱딱한 약속과 긴장을 말과 행동으로 풀어 관계를 부드럽게 만듭니다.",
            "caution": "말이 지나치면 상대가 가볍게 느끼거나 예민하게 받아들일 수 있습니다.",
        },
        "marriage": {
            "dimension": "생활 문제 처리력",
            "principle": "식상이 책임 압박을 실제 처리 능력으로 바꾸는 흐름입니다.",
            "adjudication": "생활에서 생기는 문제를 말로 미루지 않고 실제 행동으로 처리합니다.",
            "caution": "표현이 앞서면 배우자와 책임 기준을 두고 다툴 수 있습니다.",
        },
    },
    "officer_generates_resource_protects_body": {
        "money": {
            "dimension": "문서 보호력",
            "principle": "관인상생으로 책임이 문서, 자격, 보호 장치로 이어지는 흐름입니다.",
            "adjudication": "계약과 책임이 문서 근거로 정리되어 재물 손실을 줄입니다.",
            "caution": "근거를 갖추는 과정이 길어지면 돈의 움직임은 늦어질 수 있습니다.",
        },
        "career": {
            "dimension": "공식 신뢰도",
            "principle": "관성이 인성을 생해 책임이 자격과 신뢰로 정리되는 흐름입니다.",
            "adjudication": "맡은 책임이 경력, 자격, 평판의 근거로 쌓입니다.",
            "caution": "책임이 과하면 준비와 검토가 길어져 실행 속도가 떨어질 수 있습니다.",
        },
        "love": {
            "dimension": "안정 확인",
            "principle": "관성이 인성으로 이어져 약속과 안정감을 확인하는 흐름입니다.",
            "adjudication": "관계에서 말보다 신뢰, 예의, 안정된 태도를 중요하게 봅니다.",
            "caution": "확인하려는 마음이 길어지면 표현이 늦어질 수 있습니다.",
        },
        "marriage": {
            "dimension": "가정 안정력",
            "principle": "관인상생이 생활 책임을 보호 장치와 가족 안정으로 바꾸는 흐름입니다.",
            "adjudication": "결혼 뒤의 책임이 문서, 가족 인정, 생활 안정으로 이어집니다.",
            "caution": "가족과 제도의 기준이 무거우면 결혼 결정이 늦어질 수 있습니다.",
        },
    },
    "resource_controls_output_dosik": {
        "money": {
            "dimension": "성과 지연도",
            "principle": "인성이 식상을 제어해 결과물과 수입 활동을 늦추는 흐름입니다.",
            "adjudication": "생각과 준비가 많아 결과물이 늦어지고, 수입 전환도 늦어집니다.",
            "caution": "검토가 길어질수록 받을 돈보다 놓치는 기회가 먼저 커집니다.",
        },
        "career": {
            "dimension": "실행 지연도",
            "principle": "인성이 식상을 누르는 도식의 흐름입니다.",
            "adjudication": "근거와 준비는 강하지만 결과물을 내는 속도가 늦어질 수 있습니다.",
            "caution": "완성도를 기다리다 평가받을 시기를 놓치기 쉽습니다.",
        },
        "love": {
            "dimension": "표현 지연도",
            "principle": "인성이 식상을 눌러 표현을 늦추는 흐름입니다.",
            "adjudication": "마음은 있어도 말과 행동으로 드러나는 속도가 늦습니다.",
            "caution": "상대는 신중함보다 거리감으로 받아들일 수 있습니다.",
        },
        "marriage": {
            "dimension": "결정 지연도",
            "principle": "인성이 식상을 제어해 생활 결정을 늦추는 흐름입니다.",
            "adjudication": "결혼을 신중하게 보지만, 실제 약속과 실행은 늦어질 수 있습니다.",
            "caution": "생각이 길어지면 상대와 가족은 결정을 미루는 것으로 봅니다.",
        },
    },
}

CYCLE_PRODUCT_FACET_DEFINITIONS: dict[str, dict[Domain, dict[str, str]]] = {
    "output_generates_wealth_then_officer": {
        "money": {
            "label": "성과 수익화",
            "meaning": "만든 결과물이 수입과 보상으로 넘어가는 힘",
            "assertion": "재물은 결과물과 직업 보상에서 생깁니다.",
        },
        "career": {
            "label": "성과 보상력",
            "meaning": "실무 성과가 평가와 보상으로 이어지는 작용",
            "assertion": "직업 성취는 결과물과 보상 체계에서 뚜렷해집니다.",
        },
        "love": {
            "label": "표현 현실화",
            "meaning": "마음이 말과 행동으로 드러나 실제 만남으로 이어지는 정도",
            "assertion": "연애에서는 표현이 실제 만남으로 이어집니다.",
        },
        "marriage": {
            "label": "생활 구성력",
            "meaning": "일상의 행동과 경제 판단이 결혼 생활로 이어지는 정도",
            "assertion": "결혼은 생활 행동과 경제 판단에서 구체화됩니다.",
        },
    },
    "wealth_generates_officer_controls_peer": {
        "money": {
            "label": "계약·분배 통제",
            "meaning": "돈의 몫을 계약과 책임 기준으로 정리하는 힘",
            "assertion": "공동 비용과 몫 문제는 계약 기준으로 정리됩니다.",
        },
        "career": {
            "label": "권한 정리력",
            "meaning": "성과와 보상이 직책과 공식 책임으로 바뀌는 힘",
            "assertion": "직업 성취는 권한과 책임이 함께 잡힐 때 강해집니다.",
        },
        "love": {
            "label": "약속 기준",
            "meaning": "호감이 예의와 약속으로 정리되는 힘",
            "assertion": "관계는 감정만이 아니라 약속의 태도에서 안정됩니다.",
        },
        "marriage": {
            "label": "책임 분담력",
            "meaning": "생활비와 역할을 서로의 책임으로 나누는 힘",
            "assertion": "결혼 안정성은 생활비와 역할 분담에서 드러납니다.",
        },
    },
    "wealth_controls_resource_releases_output": {
        "money": {
            "label": "현실 결정력",
            "meaning": "검토와 보류를 끝내고 돈의 결정을 내리는 힘",
            "assertion": "돈 문제는 오래 미루기보다 현실 결정을 통해 움직입니다.",
        },
        "career": {
            "label": "실행 전환력",
            "meaning": "준비에 머물던 일을 실행과 결과물로 바꾸는 힘",
            "assertion": "직업운은 준비보다 실행에서 평가가 납니다.",
        },
        "love": {
            "label": "감정 결정력",
            "meaning": "오래 재던 마음이 실제 선택으로 움직이는 힘",
            "assertion": "연애는 생각보다 실제 선택이 먼저 드러납니다.",
        },
        "marriage": {
            "label": "결정 현실화",
            "meaning": "주거, 비용, 가족 문제를 기준으로 결혼 결정을 내리는 힘",
            "assertion": "결혼 판단은 생활 조건을 통해 현실화됩니다.",
        },
    },
    "output_controls_officer_reduces_pressure": {
        "money": {
            "label": "책임 처리력",
            "meaning": "계약과 책임의 부담을 실무 능력으로 줄이는 힘",
            "assertion": "재물 부담은 말보다 처리 능력으로 줄어듭니다.",
        },
        "career": {
            "label": "실무 돌파력",
            "meaning": "압박이 큰 일을 처리 능력으로 풀어내는 힘",
            "assertion": "직업운은 어려운 일을 직접 처리할 때 강해집니다.",
        },
        "love": {
            "label": "긴장 완화력",
            "meaning": "딱딱한 약속과 긴장을 말과 행동으로 낮추는 힘",
            "assertion": "관계의 긴장은 표현과 태도로 풀립니다.",
        },
        "marriage": {
            "label": "생활 처리력",
            "meaning": "생활 문제를 말로 미루지 않고 행동으로 처리하는 힘",
            "assertion": "결혼 생활에서는 실제 처리 능력이 안정성을 만듭니다.",
        },
    },
    "officer_generates_resource_protects_body": {
        "money": {
            "label": "문서 보호력",
            "meaning": "계약과 책임을 문서 근거로 남겨 손실을 줄이는 힘",
            "assertion": "재물은 문서와 근거가 있을 때 지켜집니다.",
        },
        "career": {
            "label": "공식 신뢰도",
            "meaning": "맡은 책임이 경력과 자격의 근거로 쌓이는 힘",
            "assertion": "직업운은 공식 책임과 신뢰에서 강해집니다.",
        },
        "love": {
            "label": "관계 신뢰도",
            "meaning": "말보다 신뢰와 예의를 확인하는 힘",
            "assertion": "연애에서는 안정된 태도가 관계를 오래 끌고 갑니다.",
        },
        "marriage": {
            "label": "가정 안정력",
            "meaning": "생활 책임이 가족 인정과 보호 장치로 이어지는 작용",
            "assertion": "결혼운은 생활 책임이 안정 장치로 바뀔 때 강합니다.",
        },
    },
    "resource_controls_output_dosik": {
        "money": {
            "label": "수입 지연성",
            "meaning": "준비와 보류가 결과물과 수입 전환을 늦추는 작용",
            "assertion": "재물은 생각이 길어질수록 늦게 움직입니다.",
        },
        "career": {
            "label": "성과 지연성",
            "meaning": "근거와 준비가 강한 대신 결과물의 속도가 늦어지는 작용",
            "assertion": "직업 평가는 완성도보다 시점에서 밀릴 수 있습니다.",
        },
        "love": {
            "label": "표현 지연성",
            "meaning": "마음은 있어도 말과 행동이 늦어지는 작용",
            "assertion": "연애에서는 신중함이 거리감으로 보일 수 있습니다.",
        },
        "marriage": {
            "label": "결정 지연성",
            "meaning": "결혼 판단은 신중하지만 실제 약속이 늦어지는 작용",
            "assertion": "결혼 결정은 생각보다 실행이 늦어지기 쉽습니다.",
        },
    },
}

CYCLE_RELATION_FACET_DEFINITIONS: dict[str, dict[Domain, dict[str, str]]] = {
    "generates": {
        "money": {"label": "재물 연결성", "meaning": "한 기운이 다른 기운을 키워 돈의 경로를 만드는 작용"},
        "career": {"label": "역할 연결성", "meaning": "한 역할이 다음 책임과 평가로 이어지는 작용"},
        "love": {"label": "관계 연결성", "meaning": "마음이 접점과 약속으로 이어지는 작용"},
        "marriage": {"label": "생활 연결성", "meaning": "감정과 책임이 생활 약속으로 이어지는 작용"},
    },
    "controls": {
        "money": {"label": "재물 제어력", "meaning": "돈의 과함과 손실을 제어하는 작용"},
        "career": {"label": "책임 제어력", "meaning": "역할과 권한의 압박을 정리하는 작용"},
        "love": {"label": "관계 제어력", "meaning": "감정의 과함과 거리감을 조절하는 작용"},
        "marriage": {"label": "생활 제어력", "meaning": "생활 책임과 결정 부담을 조절하는 작용"},
    },
    "element_bridge": {
        "money": {"label": "통관 작용", "meaning": "충돌한 기운이 중간 오행을 거쳐 재물 판단으로 정리되는 작용"},
        "career": {"label": "통관 작용", "meaning": "충돌한 기운이 중간 오행을 거쳐 직업 판단으로 정리되는 작용"},
        "love": {"label": "통관 작용", "meaning": "충돌한 기운이 중간 오행을 거쳐 관계 판단으로 정리되는 작용"},
        "marriage": {"label": "통관 작용", "meaning": "충돌한 기운이 중간 오행을 거쳐 생활 판단으로 정리되는 작용"},
    },
    "element_exception": {
        "money": {"label": "반극 부담", "meaning": "제어하려던 기운이 되밀려 재물 부담으로 바뀌는 작용"},
        "career": {"label": "반극 부담", "meaning": "제어하려던 기운이 되밀려 직업 압박으로 바뀌는 작용"},
        "love": {"label": "반극 부담", "meaning": "조절하려던 감정이 되밀려 관계 부담으로 바뀌는 작용"},
        "marriage": {"label": "반극 부담", "meaning": "정리하려던 생활 문제가 되밀려 부담으로 바뀌는 작용"},
    },
    "branch_cycle": {
        "money": {"label": "지지 작용", "meaning": "지지의 합충형파해가 재물 사건을 현실화하는 작용"},
        "career": {"label": "지지 작용", "meaning": "지지의 합충형파해가 직업 사건을 현실화하는 작용"},
        "love": {"label": "지지 작용", "meaning": "지지의 합충형파해가 관계 사건을 현실화하는 작용"},
        "marriage": {"label": "지지 작용", "meaning": "지지의 합충형파해가 결혼과 생활 사건을 현실화하는 작용"},
    },
    "stem_combine": {
        "money": {"label": "천간합 작용", "meaning": "드러난 글자의 결합이 재물 판단의 방향을 바꾸는 작용"},
        "career": {"label": "천간합 작용", "meaning": "드러난 글자의 결합이 직업 판단의 방향을 바꾸는 작용"},
        "love": {"label": "천간합 작용", "meaning": "드러난 글자의 결합이 관계 판단의 방향을 바꾸는 작용"},
        "marriage": {"label": "천간합 작용", "meaning": "드러난 글자의 결합이 결혼 판단의 방향을 바꾸는 작용"},
    },
}

CYCLE_DOMAIN_SIGNAL_PRIORITY: dict[Domain, dict[str, int]] = {
    "money": {
        "output_generates_wealth_then_officer": 0,
        "wealth_generates_officer_controls_peer": 1,
        "wealth_controls_resource_releases_output": 2,
        "resource_controls_output_dosik": 3,
        "output_controls_officer_reduces_pressure": 4,
        "officer_generates_resource_protects_body": 5,
    },
    "career": {
        "output_controls_officer_reduces_pressure": 0,
        "output_generates_wealth_then_officer": 1,
        "officer_generates_resource_protects_body": 2,
        "wealth_generates_officer_controls_peer": 3,
        "wealth_controls_resource_releases_output": 4,
        "resource_controls_output_dosik": 5,
    },
    "love": {
        "output_generates_wealth_then_officer": 0,
        "officer_generates_resource_protects_body": 1,
        "wealth_generates_officer_controls_peer": 2,
        "wealth_controls_resource_releases_output": 3,
        "output_controls_officer_reduces_pressure": 4,
        "resource_controls_output_dosik": 5,
    },
    "marriage": {
        "wealth_generates_officer_controls_peer": 0,
        "officer_generates_resource_protects_body": 1,
        "output_generates_wealth_then_officer": 2,
        "wealth_controls_resource_releases_output": 3,
        "output_controls_officer_reduces_pressure": 4,
        "resource_controls_output_dosik": 5,
    },
}

MIXED_PATTERN_ROLE_SENTENCES: dict[Domain, str] = {
    "money": "격국상 {group}인 {element} 기운이 강해집니다. 재정 부담도 커집니다.",
    "career": "격국상 {group}인 {element} 기운이 강해집니다. 역할 경쟁도 커집니다.",
    "love": "격국상 {group}인 {element} 기운이 강해집니다. 거리감도 예민해집니다.",
    "marriage": "격국상 {group}인 {element} 기운이 강해집니다. 책임 분담도 무거워집니다.",
}

RELATION_POLARITY_DOMAIN_RESULTS: dict[Domain, dict[str, str]] = {
    "money": {
        "supportive": "받을 돈이 다시 정리됩니다. 손에 남는 돈도 커집니다.",
        "burdensome": "돈의 기준이 흔들립니다. 지출 부담도 커집니다.",
        "mixed": "돈의 기회가 생깁니다. 정산 부담도 따라붙습니다.",
    },
    "career": {
        "supportive": "맡을 역할이 정해집니다. 인정도 빨라집니다.",
        "burdensome": "역할 기준이 흔들립니다. 책임 부담도 커집니다.",
        "mixed": "새 역할을 맡게 됩니다. 책임 기준도 다시 다루게 됩니다.",
    },
    "love": {
        "supportive": "관계의 방향이 정리됩니다. 가까워지는 계기도 생깁니다.",
        "burdensome": "감정 반응이 커집니다. 거리감도 예민해집니다.",
        "mixed": "마음이 반응합니다. 기대 차이도 드러납니다.",
    },
    "marriage": {
        "supportive": "생활 기준이 다시 맞춰집니다. 약속도 안정됩니다.",
        "burdensome": "생활 기준이 부딪힙니다. 결정 부담도 커집니다.",
        "mixed": "결혼 이야기가 다시 시작됩니다. 현실 기준도 다시 다루게 됩니다.",
    },
}

RELATION_DOMAIN_EVENT_RESULTS: dict[str, dict[str, dict[Domain, str]]] = {
    "supportive": {
        "disruptive": {
            "money": "정산 질서가 다시 서고 받을 돈이 확정됩니다.",
            "career": "역할이 재배치되며 직업적 인정을 받습니다.",
            "love": "연락과 만남이 늘고 관계가 가까워집니다.",
            "marriage": "생활 이야기가 앞당겨지고 약속이 굳어집니다.",
        },
        "connecting": {
            "money": "정산 약속이 분명해지고 받을 돈이 확정됩니다.",
            "career": "흩어진 역할이 정리되고 인정을 받습니다.",
            "love": "연락의 계기가 생기고 관계가 가까워집니다.",
            "marriage": "생활 이야기가 모이고 약속이 안정됩니다.",
        },
        "neutral": {
            "money": "돈의 기준을 다시 세우게 됩니다.",
            "career": "맡을 역할이 다시 정리됩니다.",
            "love": "연락과 거리감이 다시 맞춰집니다.",
            "marriage": "생활 기준과 책임 범위가 다시 정리됩니다.",
        },
    },
    "burdensome": {
        "disruptive": {
            "money": "정산과 지출 문제가 커집니다.",
            "career": "책임과 결정권 문제가 커집니다.",
            "love": "감정 반응과 거리 문제가 커집니다.",
            "marriage": "생활비와 책임 분담 문제가 커집니다.",
        },
        "connecting": {
            "money": "돈의 접점은 생기지만 정산 부담이 커집니다.",
            "career": "역할은 정리되지만 책임 범위가 무거워집니다.",
            "love": "가까워지는 계기는 생기지만 감정 확인이 잦아집니다.",
            "marriage": "결혼 이야기는 모이지만 생활 부담이 커집니다.",
        },
        "neutral": {
            "money": "돈의 기준이 흔들리고 지출 부담이 커집니다.",
            "career": "역할 기준이 흔들리고 책임 부담이 커집니다.",
            "love": "거리감이 예민해지고 감정 확인이 잦아집니다.",
            "marriage": "생활 기준이 부딪히고 결정 부담이 커집니다.",
        },
    },
    "mixed": {
        "disruptive": {
            "money": "받을 돈은 생기지만 정산 부담도 커집니다.",
            "career": "새 역할은 생기지만 책임 기준도 다시 다루게 됩니다.",
            "love": "가까워지는 계기는 생기지만 기대 차이도 드러납니다.",
            "marriage": "결혼 이야기는 이어지지만 생활 부담도 같이 커집니다.",
        },
        "connecting": {
            "money": "돈의 기회가 모이고 정산 부담도 같이 커집니다.",
            "career": "역할이 정리되고 책임 범위도 같이 커집니다.",
            "love": "관계가 가까워지고 기대 차이도 같이 드러납니다.",
            "marriage": "약속이 구체화되고 현실 기준도 같이 무거워집니다.",
        },
        "neutral": {
            "money": "돈의 기회와 정산 부담이 같이 생깁니다.",
            "career": "새 역할과 책임 부담이 같이 생깁니다.",
            "love": "호감과 감정 부담이 같이 생깁니다.",
            "marriage": "결혼 이야기와 생활 부담이 같이 생깁니다.",
        },
    },
}

RELATION_SUPPORT_CAUSE_SENTENCES: dict[str, str] = {
    "clash": "{relation_subject} 격국상 필요한 {element} 기운을 강하게 만듭니다.",
    "punishment": "{relation_subject} 반복되는 압박 속에서 격국상 필요한 {element} 기운을 강하게 만듭니다.",
    "self_punishment": "{relation_subject} 안에서 반복되던 문제를 건드려 격국상 필요한 {element} 기운을 강하게 만듭니다.",
    "break": "{relation_subject} 어긋난 약속 사이에서 격국상 필요한 {element} 기운을 강하게 만듭니다.",
    "harm": "{relation_subject} 말하기 어려운 불편 속에서 격국상 필요한 {element} 기운을 강하게 만듭니다.",
    "six_combine": "{relation_subject} 격국상 필요한 {element} 기운을 약속과 연결로 모읍니다.",
    "three_harmony": "{relation_subject} 격국상 필요한 {element} 기운을 한 방향으로 크게 모읍니다.",
    "three_harmony_half": "{relation_subject} 격국상 필요한 {element} 기운을 한 방향으로 모읍니다.",
    "three_meeting": "{relation_subject} 격국상 필요한 {element} 기운을 계절의 힘으로 크게 모읍니다.",
}

RELATION_PRESSURE_CAUSE_SENTENCES: dict[str, str] = {
    "clash": "{relation_subject} 격국상 부담이 되는 {element} 기운을 강하게 만듭니다.",
    "punishment": "{relation_subject} 격국상 부담이 되는 {element} 기운을 반복시킵니다.",
    "self_punishment": "{relation_subject} 격국상 부담이 되는 {element} 기운을 안에서 반복시킵니다.",
    "break": "{relation_subject} 격국상 부담이 되는 {element} 기운을 어긋난 약속으로 키웁니다.",
    "harm": "{relation_subject} 격국상 부담이 되는 {element} 기운을 말하기 어려운 불편으로 쌓습니다.",
    "six_combine": "{relation_subject} 격국상 부담이 되는 {element} 기운을 약속 문제로 키웁니다.",
    "three_harmony": "{relation_subject} 격국상 부담이 되는 {element} 기운을 한 방향으로 크게 모읍니다.",
    "three_harmony_half": "{relation_subject} 격국상 부담이 되는 {element} 기운을 한 방향으로 모읍니다.",
    "three_meeting": "{relation_subject} 격국상 부담이 되는 {element} 기운을 계절의 힘으로 크게 모읍니다.",
}

RELATION_SUPPORT_ROLE_TEXT: dict[Domain, dict[str, str]] = {
    "money": {
        "peer": "내 몫을 지키는 기준이 바로 섭니다.",
        "output": "해낸 일이 받을 돈의 근거가 됩니다.",
        "wealth": "돈의 기회가 거래로 이어집니다.",
        "officer": "계약 기준이 잡힙니다. 받을 돈도 정확해집니다.",
        "resource": "근거 자료가 돈을 지켜 줍니다.",
    },
    "career": {
        "peer": "비교와 경쟁 속에서 맡을 역할이 드러납니다.",
        "output": "결과물이 평가의 근거가 됩니다.",
        "wealth": "성과가 보상과 업무 기회를 만듭니다.",
        "officer": "직책과 책임 범위가 정해집니다.",
        "resource": "준비한 이력이 인정의 근거가 됩니다.",
    },
    "love": {
        "peer": "동등한 거리감이 관계를 편하게 만듭니다.",
        "output": "마음을 말과 행동으로 전하게 됩니다.",
        "wealth": "호감이 만남으로 옮겨집니다.",
        "officer": "약속이 관계를 안정시킵니다.",
        "resource": "상대의 태도에서 안정감을 얻습니다.",
    },
    "marriage": {
        "peer": "각자의 몫을 나누며 생활 기준을 맞춥니다.",
        "output": "생활 약속을 행동으로 옮깁니다.",
        "wealth": "주거와 돈 문제가 현실 결정으로 이어집니다.",
        "officer": "배우자와 나눌 책임 기준이 잡힙니다.",
        "resource": "가족의 동의와 문서 기준이 생활 약속을 단단하게 합니다.",
    },
}

RELATION_PRESSURE_ROLE_TEXT: dict[Domain, dict[str, str]] = {
    "money": {
        "peer": "돈의 몫을 두고 분배 부담이 커집니다.",
        "output": "결과가 앞서 계약 기준이 흔들립니다.",
        "wealth": "돈의 규모가 커져 책임 비용도 커집니다.",
        "officer": "계약 책임이 강해져 재정 부담이 커집니다.",
        "resource": "검토가 길어져 금전 결정이 늦어집니다.",
    },
    "career": {
        "peer": "역할 경쟁이 커지고 소모가 늘어납니다.",
        "output": "결과물이 앞서 평가 기준과 부딪칩니다.",
        "wealth": "성과 요구가 커져 업무 압박이 올라갑니다.",
        "officer": "책임 기준이 강해져 결정권 문제가 생깁니다.",
        "resource": "검토와 준비가 길어져 실행이 늦어집니다.",
    },
    "love": {
        "peer": "자존심이 앞서 거리감이 커집니다.",
        "output": "말이 앞서 감정이 상합니다.",
        "wealth": "현실 계산이 마음보다 앞섭니다.",
        "officer": "약속의 무게가 관계를 압박합니다.",
        "resource": "생각이 길어져 마음 표현이 늦어집니다.",
    },
    "marriage": {
        "peer": "생활 책임을 두고 부딪칩니다.",
        "output": "말이 앞서 생활 문제가 커집니다.",
        "wealth": "경제 문제가 결혼 결정을 압박합니다.",
        "officer": "책임 분담의 압박이 커집니다.",
        "resource": "가족 문제와 문서 문제가 길어집니다.",
    },
}

MONTH_TEN_GOD_DOMAIN_DIRECTIONS: dict[str, dict[Domain, str]] = {
    "bi_gyeon": {
        "money": "비견 월령은 돈을 혼자 움켜쥐기보다 내 몫을 지키려는 성향이 뚜렷합니다.",
        "career": "비견 월령은 같은 위치의 사람들과 경쟁하며 자기 역할을 세우는 직업운입니다.",
        "love": "비견 월령은 편안함과 동등성을 느낄 때 마음이 안정됩니다.",
        "marriage": "비견 월령은 결혼 뒤에도 각자의 결정권을 중요하게 보는 생활 태도입니다.",
    },
    "geob_jae": {
        "money": "겁재 월령은 재물에서 경쟁과 분배 문제를 먼저 키웁니다.",
        "career": "겁재 월령은 직업에서 협상과 성과 경쟁을 강하게 만듭니다.",
        "love": "겁재 월령은 호감이 생겨도 소유욕을 예민하게 만듭니다. 거리감도 따로 다루게 됩니다.",
        "marriage": "겁재 월령은 결혼에서 돈 이야기와 역할 분담을 빨리 정하게 만듭니다.",
    },
    "sik_sin": {
        "money": "식신 월령은 기술과 반복 성과가 수입으로 바뀌는 재물운을 만듭니다.",
        "career": "식신 월령은 꾸준히 만든 결과물로 직업적 신뢰를 얻습니다.",
        "love": "식신 월령은 말보다 일상적인 챙김으로 마음을 전합니다.",
        "marriage": "식신 월령은 결혼에서 돌봄과 생활 유지가 중요한 기준이 됩니다.",
    },
    "sang_gwan": {
        "money": "상관 월령은 표현력과 개선 능력을 수입으로 이어 줍니다.",
        "career": "상관 월령은 문제를 찾아 개선하는 능력으로 평가받습니다.",
        "love": "상관 월령은 감정을 숨기기보다 말로 확인하려 합니다.",
        "marriage": "상관 월령은 결혼에서 불만을 생활 규칙으로 바꾸어야 안정됩니다.",
    },
    "pyeon_jae": {
        "money": "편재 월령은 고정 수입보다 거래와 외부 기회에서 돈을 움직입니다.",
        "career": "편재 월령은 사업 개발과 대외 활동에서 직업 기회를 키웁니다.",
        "love": "편재 월령은 만남의 접점이 넓고 호감의 속도도 빠릅니다.",
        "marriage": "편재 월령은 결혼 뒤에도 외부 활동과 경제 목표를 크게 의식하게 만듭니다.",
    },
    "jeong_jae": {
        "money": "정재 월령은 생긴 돈을 안정적으로 남기려는 성향이 뚜렷합니다.",
        "career": "정재 월령은 맡은 일을 정확히 관리할 때 신뢰가 쌓이는 직업운입니다.",
        "love": "정재 월령은 안정된 태도와 약속 이행을 보고 마음을 엽니다.",
        "marriage": "정재 월령은 생활비 기준이 분명해지면서 결혼 안정도 빨라집니다.",
    },
    "pyeon_gwan": {
        "money": "편관 월령은 재물에서 위험 부담과 안전장치를 함께 보게 만듭니다.",
        "career": "편관 월령은 압박이 큰 자리에서 책임과 권한을 함께 다루게 만듭니다.",
        "love": "편관 월령은 강한 끌림과 긴장감을 함께 만듭니다.",
        "marriage": "편관 월령은 어려운 일을 견디는 힘을 줍니다. 통제 부담도 커집니다.",
    },
    "jeong_gwan": {
        "money": "정관 월령은 공식 보상과 안정된 계약에서 수입을 만듭니다.",
        "career": "정관 월령은 직위와 평판을 통해 사회적 인정을 받습니다.",
        "love": "정관 월령은 예의와 약속을 중시하는 관계 태도입니다.",
        "marriage": "정관 월령은 결혼을 공식적인 약속과 사회적 신뢰로 받아들입니다.",
    },
    "pyeon_in": {
        "money": "편인 월령은 특수한 정보와 해석 능력을 돈의 기회로 바꿉니다.",
        "career": "편인 월령은 남다른 분석과 기획에서 전문성을 만듭니다.",
        "love": "편인 월령은 혼자 생각하는 시간이 길어져 마음 표현이 늦어집니다.",
        "marriage": "편인 월령은 각자의 내면 시간을 존중해야 결혼이 안정됩니다.",
    },
    "jeong_in": {
        "money": "정인 월령은 문서와 자격을 통해 돈을 지키려는 성향이 뚜렷합니다.",
        "career": "정인 월령은 학습과 공인된 근거를 통해 전문성을 쌓습니다.",
        "love": "정인 월령은 신뢰의 근거가 쌓인 뒤 마음을 엽니다.",
        "marriage": "정인 월령은 제도적 보호와 가족의 인정을 중요하게 봅니다.",
    },
}

PRIMARY_PATTERN_DOMAIN_DIRECTIONS: dict[str, dict[Domain, str]] = {
    "output_to_wealth": {
        "money": "식상이 재성으로 이어지면 만든 결과가 돈으로 바뀝니다.",
        "career": "식상이 재성으로 이어지면 결과물을 통해 직업 기회가 커집니다.",
        "love": "식상이 재성으로 이어지면 표현이 관계의 진전으로 이어집니다.",
        "marriage": "식상이 재성으로 이어지면 생활을 꾸리는 능력이 결혼 안정으로 이어집니다.",
    },
    "officer_resource": {
        "money": "관성이 인성으로 이어지면 책임 있는 자리에서 수입이 생깁니다.",
        "career": "관성이 인성으로 이어지면 공식 책임이 자격과 평판으로 바뀝니다.",
        "love": "관성이 인성으로 이어지면 신뢰와 책임감이 호감의 기준이 됩니다.",
        "marriage": "관성이 인성으로 이어지면 약속과 보호가 결혼 안정의 기준이 됩니다.",
    },
    "resource_supported": {
        "money": "인성이 일간을 받치면 급한 수익보다 돈을 지키는 힘이 강해집니다.",
        "career": "인성이 일간을 받치면 준비와 근거가 직업적 신뢰가 됩니다.",
        "love": "인성이 일간을 받치면 확신이 생긴 뒤 마음을 엽니다.",
        "marriage": "인성이 일간을 받치면 안정감과 보호 욕구가 결혼 판단에 반영됩니다.",
    },
    "wealth_pressure": {
        "money": "재성이 일간을 압박하면 돈은 들어와도 관리 부담이 먼저 커집니다.",
        "career": "재성이 일간을 압박하면 성과 요구가 커집니다. 책임 비용도 커집니다.",
        "love": "재성이 일간을 압박하면 현실 기준이 감정보다 앞서기 쉽습니다.",
        "marriage": "재성이 일간을 압박하면 돈의 기준이 결혼 결정을 무겁게 만듭니다.",
    },
    "peer_wealth_competition": {
        "money": "비겁과 재성이 맞서면 돈을 버는 힘이 커집니다. 나가는 돈도 커집니다.",
        "career": "비겁과 재성이 맞서면 경쟁 속에서 성과를 증명해야 합니다.",
        "love": "비겁과 재성이 맞서면 호감보다 자존심 문제가 먼저 건드려집니다.",
        "marriage": "비겁과 재성이 맞서면 생활비와 각자의 몫을 분명히 나누게 됩니다.",
    },
    "cold_storage_needs_fire": {
        "money": "차가운 구조에서는 화기가 돈을 드러난 평가 뒤에 키웁니다.",
        "career": "차가운 구조에서는 화기가 표현과 인정을 중요하게 만듭니다.",
        "love": "차가운 구조에서는 화기가 마음을 말로 밝히게 합니다. 관계도 더 따뜻해집니다.",
        "marriage": "차가운 구조에서는 화기가 생활 안의 정서 표현을 살립니다.",
    },
    "hot_dry_needs_water": {
        "money": "뜨겁고 건조한 구조에서는 수기가 돈을 조절과 회수에서 남깁니다.",
        "career": "뜨겁고 건조한 구조에서는 수기가 판단의 여유를 만듭니다.",
        "love": "뜨겁고 건조한 구조에서는 수기가 감정의 속도를 낮춥니다. 관계도 안정됩니다.",
        "marriage": "뜨겁고 건조한 구조에서는 수기가 생활의 온도를 낮추는 합의를 만듭니다.",
    },
}

USEFUL_ELEMENT_ROLE_TEXT = {
    "climate_medicine": "계절의 치우침을 바로잡습니다",
    "support_day_master": "약한 일간을 받쳐 줍니다",
    "root_day_master": "일간의 뿌리를 보강합니다",
    "drain_strong_day_master": "강한 기운을 결과로 빼냅니다",
    "convert_output_to_value": "결과를 돈과 성과로 바꿉니다",
    "discipline_strong_day_master": "강한 기운에 질서와 책임을 세웁니다",
    "make_results_visible": "생각과 능력을 밖으로 드러냅니다",
    "connect_results_to_value": "결과를 보상과 가치로 연결합니다",
    "illness_medicine": "과한 기운의 부담을 덜어 줍니다",
    "regular_pattern_support_officer": {
        "money": "계약 기준을 분명하게 세웁니다",
        "career": "평가 기준을 분명하게 세웁니다",
        "love": "관계의 거리를 분명하게 세웁니다",
        "marriage": "생활 책임을 분명하게 나눕니다",
        "default": "선택의 기준을 분명하게 세웁니다",
    },
    "regular_pattern_support_output": {
        "money": "해낸 일을 보상으로 바꿉니다",
        "career": "능력을 결과물로 증명합니다",
        "love": "마음을 행동으로 전합니다",
        "marriage": "생활 약속을 행동으로 옮깁니다",
        "default": "생각을 눈에 보이는 행동으로 옮깁니다",
    },
    "regular_pattern_support_wealth": {
        "money": "수입 기회를 현실 이익으로 바꿉니다",
        "career": "성과를 실질적 보상으로 바꿉니다",
        "love": "호감을 만남으로 옮깁니다",
        "marriage": "생활 계획을 현실 결정으로 옮깁니다",
        "default": "현실적인 선택을 빠르게 잡아 줍니다",
    },
    "regular_pattern_support_resource": {
        "money": "돈을 쓰기 전 근거를 세웁니다",
        "career": "책임을 자격과 신뢰로 바꿉니다",
        "love": "상대의 태도에서 신뢰를 확인합니다",
        "marriage": "약속을 제도와 보호의 기준으로 바꿉니다",
        "default": "판단의 근거를 단단하게 만듭니다",
    },
}

CAUTION_ELEMENT_ROLE_TEXT = {
    "pressure_on_weak_day_master": "약한 일간에 부담을 줍니다",
    "resource_drain_or_money_pressure": "기운을 빼고 돈 문제를 무겁게 만듭니다",
    "excess_self_reinforcement": "자기 기준을 과하게 키웁니다",
    "overprotection_or_delay": "생각이 많아져 실행을 늦춥니다",
    "regular_pattern_pressure_peer": {
        "money": "분배 부담을 키웁니다",
        "career": "역할 경쟁을 키웁니다",
        "love": "자존심 문제를 키웁니다",
        "marriage": "생활 책임을 두고 부딪치게 합니다",
        "default": "내 몫과 상대의 몫을 두고 부딪치게 합니다",
    },
    "regular_pattern_pressure_resource": {
        "money": "금전 결정을 늦춥니다",
        "career": "실행 속도를 늦춥니다",
        "love": "마음 표현을 늦춥니다",
        "marriage": "결혼 결정을 늦춥니다",
        "default": "생각과 준비가 길어져 결정을 늦춥니다",
    },
    "regular_pattern_pressure_officer": {
        "money": "책임 비용을 키웁니다",
        "career": "평가 압박을 키웁니다",
        "love": "관계의 부담감을 키웁니다",
        "marriage": "책임 분담의 압박을 키웁니다",
        "default": "규칙과 책임의 압박을 키웁니다",
    },
    "regular_pattern_pressure_output": {
        "money": "계약 기준과 충돌하기 쉽습니다",
        "career": "평가 기준과 충돌하기 쉽습니다",
        "love": "말이 앞서 감정이 상하기 쉽습니다",
        "marriage": "말이 앞서 생활 문제가 커지기 쉽습니다",
        "default": "말과 결과물이 앞서 기준과 충돌하기 쉽습니다",
    },
    "regular_pattern_pressure_wealth": {
        "money": "돈의 규모만큼 책임 비용을 키웁니다",
        "career": "성과 요구를 키웁니다",
        "love": "현실 계산을 마음보다 앞세우기 쉽습니다",
        "marriage": "경제 문제로 결혼 결정을 압박합니다",
        "default": "현실 요구가 커지는 만큼 책임 압박을 높입니다",
    },
}

PATTERN_REASON_ROLE_TEXT: dict[str, dict[Domain, str]] = {
    "peer_pattern_needs_officer": {
        "money": "비견 월령에서는 계약 기준이 분명할수록 내 몫의 돈이 남습니다",
        "career": "비견 월령에서는 강한 자기 기준을 공식 책임으로 바꿔 직업운을 안정시킵니다",
        "love": "비견 월령에서는 자기 기준이 강하므로 관계의 약속과 거리가 분명해야 마음이 편합니다",
        "marriage": "비견 월령에서는 각자의 몫을 생활 책임으로 나눌 때 결혼 생활이 안정됩니다",
    },
    "peer_pattern_uses_output": {
        "money": "비견 월령에서는 경쟁 속에서 해낸 결과가 보상으로 잡힐 때 재물이 생깁니다",
        "career": "비견 월령에서는 자기 실력을 결과물로 보여 줄 때 인정받습니다",
        "love": "비견 월령에서는 마음을 말보다 행동으로 보여 줄 때 관계가 가까워집니다",
        "marriage": "비견 월령에서는 생활 속 약속을 행동으로 옮길 때 신뢰가 쌓입니다",
    },
    "peer_pattern_excess_peer": {
        "money": "비견 월령에서 비겁이 강해져 내 몫을 두고 분배 부담이 커집니다",
        "career": "비견 월령에서 비겁이 강해져 자기 기준과 역할 다툼이 커집니다",
        "love": "비견 월령에서 비겁이 강해져 마음보다 자존심이 먼저 앞섭니다",
        "marriage": "비견 월령에서 비겁이 강해져 각자의 몫을 두고 생활 충돌이 생깁니다",
    },
    "peer_pattern_resource_overfeeds": {
        "money": "비견 월령에서 인성이 강해져 판단이 길어지고 금전 결정이 늦어집니다",
        "career": "비견 월령에서 인성이 강해져 준비가 길어지고 맡은 일이 늦게 움직입니다",
        "love": "비견 월령에서 인성이 강해져 마음을 오래 확인하고 표현이 늦어집니다",
        "marriage": "비견 월령에서 인성이 강해져 안정 확인이 길어지고 생활 결정이 늦어집니다",
    },
    "yangren_needs_officer_control": {
        "money": "겁재 월령에서는 빠른 이해관계를 계약 내용으로 묶어야 돈이 흩어지지 않습니다",
        "career": "겁재 월령에서는 강한 경쟁심을 책임 범위 안에서 쓸 때 직업적 성취가 커집니다",
        "love": "겁재 월령에서는 감정의 주도권이 강하므로 관계의 기준이 분명해야 편합니다",
        "marriage": "겁재 월령에서는 생활 주도권을 책임 분담으로 나눌 때 결혼 부담이 줄어듭니다",
    },
    "yangren_uses_output_release": {
        "money": "겁재 월령에서는 경쟁 에너지가 결과물로 빠질 때 돈으로 바뀝니다",
        "career": "겁재 월령에서는 강한 추진력이 결과물로 남을 때 평가를 받습니다",
        "love": "겁재 월령에서는 감정을 행동으로 풀어낼 때 관계의 긴장이 줄어듭니다",
        "marriage": "겁재 월령에서는 생활 속 행동이 분명할 때 주도권 갈등이 줄어듭니다",
    },
    "yangren_excess_competition": {
        "money": "겁재 월령에서 비겁이 강해져 돈을 두고 경쟁과 손실이 커집니다",
        "career": "겁재 월령에서 비겁이 강해져 경쟁심이 앞서고 책임 충돌이 생깁니다",
        "love": "겁재 월령에서 비겁이 강해져 감정의 주도권을 놓고 긴장이 생깁니다",
        "marriage": "겁재 월령에서 비겁이 강해져 생활 주도권을 두고 충돌이 생깁니다",
    },
    "yangren_resource_overfeeds": {
        "money": "겁재 월령에서 인성이 강해져 판단이 길어지고 돈의 속도가 늦어집니다",
        "career": "겁재 월령에서 인성이 강해져 실행보다 준비가 길어집니다",
        "love": "겁재 월령에서 인성이 강해져 감정을 속으로 오래 붙잡습니다",
        "marriage": "겁재 월령에서 인성이 강해져 생활 결정을 오래 미룹니다",
    },
    "eating_god_generates_wealth": {
        "money": "식신 월령에서는 꾸준히 만든 결과가 거래와 수입으로 바뀝니다",
        "career": "식신 월령에서는 반복 가능한 실력이 보상과 업무 기회로 이어집니다",
        "love": "식신 월령에서는 편안한 표현이 호감을 만남으로 옮깁니다",
        "marriage": "식신 월령에서는 일상의 돌봄이 생활 계획과 재정 기준으로 이어집니다",
    },
    "eating_god_results_enter_responsibility": {
        "money": "식신 월령에서는 결과물이 계약 책임 안에 놓이면 돈이 안정됩니다",
        "career": "식신 월령에서는 산출물이 공식 책임으로 인정될 때 직업운이 커집니다",
        "love": "식신 월령에서는 표현이 약속으로 이어질 때 관계가 오래 갑니다",
        "marriage": "식신 월령에서는 생활 속 행동이 책임으로 인정될 때 결혼 생활이 안정됩니다",
    },
    "resource_can_damage_eating_god": {
        "money": "식신 월령에서 인성이 강해져 검토가 길어지고 수입 결정이 늦어집니다",
        "career": "식신 월령에서 인성이 강해져 준비가 길어지고 결과물이 늦게 나옵니다",
        "love": "식신 월령에서 인성이 강해져 생각이 많아지고 표현이 늦어집니다",
        "marriage": "식신 월령에서 인성이 강해져 생활 결정을 오래 미루게 됩니다",
    },
    "hurting_officer_generates_wealth": {
        "money": "상관 월령에서는 날카로운 표현과 개선 능력이 거래 이익으로 바뀝니다",
        "career": "상관 월령에서는 개선과 비판 능력이 성과 보상으로 이어집니다",
        "love": "상관 월령에서는 솔직한 표현이 호감으로 바뀌되 말의 온도가 중요합니다",
        "marriage": "상관 월령에서는 생활 개선 요구가 재정 계획으로 정리될 때 안정됩니다",
    },
    "hurting_officer_needs_resource_refinement": {
        "money": "상관 월령에서는 근거와 문서가 있어야 말한 이익이 돈으로 남습니다",
        "career": "상관 월령에서는 비판과 개선안을 근거로 정리할 때 평가가 좋아집니다",
        "love": "상관 월령에서는 솔직한 말에 배려와 신뢰가 붙어야 관계가 상하지 않습니다",
        "marriage": "상관 월령에서는 생활 불만을 근거와 합의로 정리할 때 결혼이 안정됩니다",
    },
    "hurting_officer_clashes_with_officer": {
        "money": "상관 월령에서 관성이 강하면 계약 기준과 표현 방식이 부딪힙니다",
        "career": "상관 월령에서 관성이 강하면 규정과 평가 기준에 맞서는 일이 생깁니다",
        "love": "상관 월령에서 관성이 강하면 말투와 약속 기준이 부딪힙니다",
        "marriage": "상관 월령에서 관성이 강하면 생활 규칙과 표현 방식이 충돌합니다",
    },
    "indirect_wealth_supports_officer": {
        "money": "편재 월령에서는 큰 거래가 책임 기준을 만나야 돈으로 남습니다",
        "career": "편재 월령에서는 확장 기회가 공식 책임으로 이어질 때 성취가 큽니다",
        "love": "편재 월령에서는 빠른 호감도 약속의 기준이 있어야 오래 갑니다",
        "marriage": "편재 월령에서는 생활 계획이 책임 기준으로 정리될 때 결정이 안정됩니다",
    },
    "output_sources_indirect_wealth": {
        "money": "편재 월령에서는 만들어 낸 결과가 거래 기회로 바뀔 때 재물이 커집니다",
        "career": "편재 월령에서는 결과물이 사업 기회와 보상으로 이어집니다",
        "love": "편재 월령에서는 표현이 만남의 기회를 넓힙니다",
        "marriage": "편재 월령에서는 생활을 꾸리는 행동이 현실 결정을 앞당깁니다",
    },
    "peer_competes_for_indirect_wealth": {
        "money": "편재 월령에서 비겁이 강하면 큰돈을 두고 경쟁과 분배 부담이 커집니다",
        "career": "편재 월령에서 비겁이 강하면 성과 경쟁과 역할 다툼이 커집니다",
        "love": "편재 월령에서 비겁이 강하면 호감보다 자존심과 비교심이 앞서기 쉽습니다",
        "marriage": "편재 월령에서 비겁이 강하면 생활비와 각자의 몫을 두고 부딪칩니다",
    },
    "resource_slows_wealth_movement": {
        "money": "편재 월령에서 인성이 강해져 거래 판단이 늦어지고 돈의 속도가 떨어집니다",
        "career": "편재 월령에서 인성이 강해져 기회 앞에서 검토가 길어집니다",
        "love": "편재 월령에서 인성이 강해져 빠른 호감도 마음속 검토로 늦어집니다",
        "marriage": "편재 월령에서 인성이 강해져 현실 결정이 길어지고 결혼 이야기가 늦어집니다",
    },
    "direct_wealth_supports_officer": {
        "money": "정재 월령에서는 받을 돈의 출처와 계약 내용을 분명하게 합니다",
        "career": "정재 월령에서는 맡은 일의 책임 범위가 분명할 때 공식 평가를 받습니다",
        "love": "정재 월령에서는 관계의 약속과 거리감을 분명하게 합니다",
        "marriage": "정재 월령에서는 생활비와 책임 분담을 분명하게 나눕니다",
    },
    "output_sources_direct_wealth": {
        "money": "정재 월령에서는 꾸준히 만든 결과가 안정 수입으로 바뀝니다",
        "career": "정재 월령에서는 반복 가능한 결과물이 보상 기준으로 잡힙니다",
        "love": "정재 월령에서는 안정적인 표현이 관계를 오래 가게 합니다",
        "marriage": "정재 월령에서는 일상의 행동이 생활 안정으로 남습니다",
    },
    "peer_competes_for_direct_wealth": {
        "money": "정재 월령에서 비겁이 강해지면 각자의 몫과 분배 부담이 커집니다",
        "career": "정재 월령에서 비겁이 강해지면 역할 경쟁이 평가 부담이 됩니다",
        "love": "정재 월령에서 비겁이 강해지면 관계의 주도권과 자존심이 예민해집니다",
        "marriage": "정재 월령에서 비겁이 강해지면 생활비와 책임 범위를 두고 부딪칩니다",
    },
    "resource_slows_wealth_accumulation": {
        "money": "정재 월령에서 인성이 강해져 안정만 보다가 돈이 쌓이는 속도가 늦어집니다",
        "career": "정재 월령에서 인성이 강해져 준비가 길어지고 평가 기회를 늦게 잡습니다",
        "love": "정재 월령에서 인성이 강해져 신뢰를 오래 확인하고 마음 표현이 늦어집니다",
        "marriage": "정재 월령에서 인성이 강해져 생활 결정을 오래 검토하게 됩니다",
    },
    "eating_god_controls_seven_killings": {
        "money": "편관 월령에서는 압박을 결과물로 제어할 때 돈의 부담이 줄어듭니다",
        "career": "편관 월령에서는 강한 압박을 성과물로 바꿀 때 평가가 올라갑니다",
        "love": "편관 월령에서는 긴장된 마음을 행동으로 풀어낼 때 관계가 부드러워집니다",
        "marriage": "편관 월령에서는 생활 압박을 행동 기준으로 나눌 때 안정됩니다",
    },
    "seven_killings_transforms_to_resource": {
        "money": "편관 월령에서는 압박을 근거와 안전장치로 바꿀 때 돈이 남습니다",
        "career": "편관 월령에서는 위기와 책임이 자격과 신뢰로 바뀔 때 성취가 큽니다",
        "love": "편관 월령에서는 강한 감정을 신뢰 확인으로 바꿀 때 관계가 안정됩니다",
        "marriage": "편관 월령에서는 책임 압박이 보호와 제도로 바뀔 때 결혼이 안정됩니다",
    },
    "wealth_feeds_seven_killings": {
        "money": "편관 월령에서 재성이 강하면 돈의 규모만큼 책임 비용이 커집니다",
        "career": "편관 월령에서 재성이 강하면 성과 요구가 곧 업무 압박이 됩니다",
        "love": "편관 월령에서 재성이 강하면 현실 계산이 감정의 부담을 키웁니다",
        "marriage": "편관 월령에서 재성이 강하면 돈 문제가 결혼 결정을 압박합니다",
    },
    "killing_pressure_excess": {
        "money": "편관 월령에서 관성이 강해져 계약 책임이 돈의 부담을 키웁니다",
        "career": "편관 월령에서 관성이 강해져 책임과 평가 압박이 크게 커집니다",
        "love": "편관 월령에서 관성이 강해져 관계의 부담감이 커집니다",
        "marriage": "편관 월령에서 관성이 강해져 책임 분담의 압박이 커집니다",
    },
    "officer_resource_sequence": {
        "money": "정관 월령에서는 책임 기준이 근거와 안전장치를 만나 돈을 지킵니다",
        "career": "정관 월령에서는 공식 책임이 자격과 신뢰로 이어져 평가가 안정됩니다",
        "love": "정관 월령에서는 약속과 신뢰가 함께 있어야 마음이 안정됩니다",
        "marriage": "정관 월령에서는 책임과 보호 기준이 함께 서야 결혼이 안정됩니다",
    },
    "wealth_supports_officer": {
        "money": "정관 월령에서는 돈의 기준이 책임을 받쳐 줄 때 재물 판단이 안정됩니다",
        "career": "정관 월령에서는 성과와 보상이 책임 있는 자리로 연결됩니다",
        "love": "정관 월령에서는 현실 기준이 약속을 받쳐 줄 때 관계가 오래 갑니다",
        "marriage": "정관 월령에서는 생활비 기준이 책임 분담을 받쳐 줄 때 안정됩니다",
    },
    "output_harms_officer_order": {
        "money": "정관 월령에서 식상이 강해져 말한 결과가 계약 기준과 부딪힙니다",
        "career": "정관 월령에서 식상이 강해져 표현과 결과물이 평가 질서와 충돌합니다",
        "love": "정관 월령에서 식상이 강해져 말이 약속의 무게를 흔듭니다",
        "marriage": "정관 월령에서 식상이 강해져 생활 불만이 책임 기준과 부딪힙니다",
    },
    "peer_disrupts_officer_order": {
        "money": "정관 월령에서 비겁이 강해져 내 몫을 앞세우고 계약 질서가 흔들립니다",
        "career": "정관 월령에서 비겁이 강해져 자기 기준이 공식 책임과 부딪힙니다",
        "love": "정관 월령에서 비겁이 강해져 자존심이 약속의 안정감을 흔듭니다",
        "marriage": "정관 월령에서 비겁이 강해져 각자의 몫이 생활 책임과 충돌합니다",
    },
    "wealth_regulates_indirect_resource": {
        "money": "편인 월령에서는 현실적인 돈의 기준이 생각을 정리합니다",
        "career": "편인 월령에서는 현실 성과가 비표준 지식을 쓸 자리로 바꿉니다",
        "love": "편인 월령에서는 현실적인 태도가 복잡한 마음을 안정시킵니다",
        "marriage": "편인 월령에서는 생활비 기준이 불안과 생각을 줄여 줍니다",
    },
    "resource_turns_into_output": {
        "money": "편인 월령에서는 머릿속 지식이 결과물로 나올 때 돈이 됩니다",
        "career": "편인 월령에서는 특수한 이해가 산출물로 바뀔 때 평가를 받습니다",
        "love": "편인 월령에서는 생각을 표현으로 바꿀 때 관계가 가까워집니다",
        "marriage": "편인 월령에서는 마음속 기준을 생활 행동으로 옮길 때 안정됩니다",
    },
    "indirect_resource_excess": {
        "money": "편인 월령에서 인성이 강해져 생각이 많아지고 금전 결정이 늦어집니다",
        "career": "편인 월령에서 인성이 강해져 해석은 깊어도 실행이 늦어집니다",
        "love": "편인 월령에서 인성이 강해져 마음을 오래 숨기게 됩니다",
        "marriage": "편인 월령에서 인성이 강해져 생활 결정을 오래 미루게 됩니다",
    },
    "wealth_regulates_direct_resource": {
        "money": "정인 월령에서는 현실적인 돈의 기준이 안정 욕구를 잡아 줍니다",
        "career": "정인 월령에서는 보상 기준이 학습과 자격을 현실 성과로 바꿉니다",
        "love": "정인 월령에서는 현실적인 태도가 신뢰 확인을 편하게 만듭니다",
        "marriage": "정인 월령에서는 생활비 기준이 보호 욕구를 안정시킵니다",
    },
    "resource_turns_into_visible_result": {
        "money": "정인 월령에서는 배운 것과 근거가 보이는 결과로 나올 때 돈이 됩니다",
        "career": "정인 월령에서는 자격과 준비가 결과물로 보일 때 평가를 받습니다",
        "love": "정인 월령에서는 신뢰가 표현으로 드러날 때 관계가 가까워집니다",
        "marriage": "정인 월령에서는 보호하려는 마음이 생활 행동으로 보여야 안정됩니다",
    },
    "direct_resource_excess": {
        "money": "정인 월령에서 인성이 강해져 안정만 보다가 금전 결정이 늦어집니다",
        "career": "정인 월령에서 인성이 강해져 준비가 길어지고 평가 시점을 놓치기 쉽습니다",
        "love": "정인 월령에서 인성이 강해져 확신을 오래 확인하고 표현이 늦어집니다",
        "marriage": "정인 월령에서 인성이 강해져 안정 확인이 길어지고 결혼 결정이 늦어집니다",
    },
    "resource_overprotects_day_master": {
        "money": "인성이 강해져 안전만 보다가 돈을 움직일 시점을 늦춥니다",
        "career": "인성이 강해져 준비와 보호가 길어지고 실행이 늦어집니다",
        "love": "인성이 강해져 마음을 보호하다가 표현이 늦어집니다",
        "marriage": "인성이 강해져 안정 확인이 길어지고 생활 결정이 늦어집니다",
    },
}

PATTERN_REASON_EVENT_TEXT: dict[str, dict[Domain, str]] = {
    "peer_pattern_needs_officer": {
        "money": "정산 방식이 분명해져 손에 남는 돈이 늘어납니다",
        "career": "맡은 책임이 평가 항목으로 올라갑니다",
        "love": "관계의 거리감이 정리되어 마음이 편해집니다",
        "marriage": "생활 책임이 나뉘어 갈등이 줄어듭니다",
    },
    "peer_pattern_uses_output": {
        "money": "성과가 보상으로 인정되어 수입이 생깁니다",
        "career": "결과물이 드러나 직업적 인정을 받습니다",
        "love": "행동으로 보인 마음이 호감을 만듭니다",
        "marriage": "작은 약속을 지키며 신뢰가 쌓입니다",
    },
    "peer_pattern_excess_peer": {
        "money": "수입이 생겨도 나눌 몫이 커집니다",
        "career": "역할 경계가 불분명해져 다툼이 생깁니다",
        "love": "자존심이 앞서 먼저 다가가기 어렵습니다",
        "marriage": "생활비 문제에서 양보가 늦어집니다",
    },
    "peer_pattern_resource_overfeeds": {
        "money": "확인할 일이 많아 금전 결정이 늦어집니다",
        "career": "준비 기간이 길어져 실행 시점이 늦어집니다",
        "love": "확신을 찾느라 표현이 늦어집니다",
        "marriage": "안정 확인이 길어져 결혼 이야기가 늦어집니다",
    },
    "yangren_needs_officer_control": {
        "money": "계약 기준이 서면서 급한 손실이 줄어듭니다",
        "career": "경쟁심이 책임 있는 자리에서 실적으로 바뀝니다",
        "love": "관계의 기준이 분명해져 감정 충돌이 줄어듭니다",
        "marriage": "책임 분담이 나뉘며 주도권 갈등이 줄어듭니다",
    },
    "yangren_uses_output_release": {
        "money": "추진력이 결과물로 남아 수입이 생깁니다",
        "career": "빠르게 밀어붙인 일로 실력을 인정받습니다",
        "love": "행동으로 표현한 마음이 긴장을 낮춥니다",
        "marriage": "생활 행동이 분명해져 갈등이 줄어듭니다",
    },
    "yangren_excess_competition": {
        "money": "경쟁이 커져 손실 부담이 생깁니다",
        "career": "앞서려는 마음이 책임 충돌을 만듭니다",
        "love": "주도권이 강해져 감정 다툼이 생깁니다",
        "marriage": "생활 주도권을 두고 충돌이 생깁니다",
    },
    "yangren_resource_overfeeds": {
        "money": "판단이 길어져 수입 기회를 늦게 잡습니다",
        "career": "준비가 길어져 실행 시점이 늦어집니다",
        "love": "감정을 오래 숨겨 관계의 속도가 늦어집니다",
        "marriage": "결정을 오래 미루며 생활 이야기가 늦어집니다",
    },
    "eating_god_generates_wealth": {
        "money": "꾸준한 결과물이 거래 수입으로 이어집니다",
        "career": "반복해서 쌓은 실력이 보상으로 이어집니다",
        "love": "편안한 표현이 호감을 만듭니다",
        "marriage": "일상의 배려가 생활 계획으로 이어집니다",
    },
    "eating_god_results_enter_responsibility": {
        "money": "결과물이 계약 안에 들어가 안정 수입으로 이어집니다",
        "career": "산출물이 책임 업무로 인정됩니다",
        "love": "표현이 약속으로 이어져 관계가 오래 갑니다",
        "marriage": "생활 행동이 책임으로 인정되어 안정됩니다",
    },
    "resource_can_damage_eating_god": {
        "money": "검토가 길어져 수입 결정이 늦어집니다",
        "career": "준비가 길어져 결과물이 늦게 나옵니다",
        "love": "생각이 많아져 표현이 늦어집니다",
        "marriage": "검토가 길어져 생활 결정이 늦어집니다",
    },
    "hurting_officer_generates_wealth": {
        "money": "개선안이 거래 이익으로 이어집니다",
        "career": "문제 제기가 성과 보상으로 이어집니다",
        "love": "솔직한 표현이 호감을 만듭니다",
        "marriage": "생활 개선 요구가 재정 계획으로 정리됩니다",
    },
    "hurting_officer_needs_resource_refinement": {
        "money": "문서 근거가 있어 말한 이익이 돈으로 남습니다",
        "career": "개선안에 근거가 붙어 인정받습니다",
        "love": "솔직한 말에 배려가 붙어 관계가 상하지 않습니다",
        "marriage": "생활 불만이 합의문으로 정리됩니다",
    },
    "hurting_officer_clashes_with_officer": {
        "money": "표현 방식이 계약 기준과 부딪힙니다",
        "career": "개선 요구가 평가 기준과 충돌합니다",
        "love": "말투가 약속 문제를 키웁니다",
        "marriage": "표현 방식이 생활 규칙과 충돌합니다",
    },
    "indirect_wealth_supports_officer": {
        "money": "큰 거래가 책임 기준 안에서 돈으로 남습니다",
        "career": "확장 기회가 책임 있는 자리로 이어집니다",
        "love": "빠른 호감이 약속으로 자리 잡습니다",
        "marriage": "생활 계획이 결정으로 이어집니다",
    },
    "output_sources_indirect_wealth": {
        "money": "만들어 낸 결과가 큰 거래로 이어집니다",
        "career": "결과물이 사업 기회로 이어집니다",
        "love": "표현이 새로운 만남으로 이어집니다",
        "marriage": "생활을 꾸리는 행동이 결정을 앞당깁니다",
    },
    "peer_competes_for_indirect_wealth": {
        "money": "큰돈 앞에서 나눌 몫이 커집니다",
        "career": "성과를 두고 역할 다툼이 커집니다",
        "love": "비교심이 호감을 가립니다",
        "marriage": "생활비를 두고 충돌이 생깁니다",
    },
    "resource_slows_wealth_movement": {
        "money": "검토가 길어져 거래 속도가 늦어집니다",
        "career": "기회 앞에서 결정이 늦어집니다",
        "love": "마음속 확인이 길어져 만남이 늦어집니다",
        "marriage": "현실 판단이 길어져 결혼 이야기가 늦어집니다",
    },
    "direct_wealth_supports_officer": {
        "money": "정산 방식이 분명해져 손에 남는 돈이 늘어납니다",
        "career": "책임 범위가 평가 항목으로 올라갑니다",
        "love": "거리감이 맞춰지며 관계가 안정됩니다",
        "marriage": "생활비 기준이 분명해져 가정이 안정됩니다",
    },
    "output_sources_direct_wealth": {
        "money": "꾸준한 결과물이 고정 수입으로 이어집니다",
        "career": "반복 가능한 결과물이 보상으로 인정됩니다",
        "love": "일관된 표현이 신뢰를 만듭니다",
        "marriage": "일상의 행동이 생활 안정으로 남습니다",
    },
    "peer_competes_for_direct_wealth": {
        "money": "수입이 생겨도 분배 부담이 커집니다",
        "career": "역할 경쟁이 평가 부담을 키웁니다",
        "love": "자존심이 예민해져 관계가 피로해집니다",
        "marriage": "생활비 문제로 충돌이 생깁니다",
    },
    "resource_slows_wealth_accumulation": {
        "money": "안정 확인이 길어져 돈이 늦게 쌓입니다",
        "career": "준비가 길어져 평가 기회를 늦게 잡습니다",
        "love": "신뢰 확인이 길어져 표현이 늦어집니다",
        "marriage": "생활 결정을 오래 검토하게 됩니다",
    },
    "eating_god_controls_seven_killings": {
        "money": "압박을 처리한 결과물이 돈의 부담을 줄입니다",
        "career": "압박 속에서 만든 성과가 평가를 올립니다",
        "love": "행동으로 풀어낸 긴장이 관계를 부드럽게 만듭니다",
        "marriage": "생활 압박을 나누며 안정이 생깁니다",
    },
    "seven_killings_transforms_to_resource": {
        "money": "안전장치가 생겨 돈의 부담이 줄어듭니다",
        "career": "위기 대응이 자격과 신뢰로 인정됩니다",
        "love": "신뢰 확인이 강한 감정을 안정시킵니다",
        "marriage": "보호 기준이 세워져 결혼이 안정됩니다",
    },
    "wealth_feeds_seven_killings": {
        "money": "돈의 규모가 커지며 책임 비용이 늘어납니다",
        "career": "성과 요구가 업무 압박을 키웁니다",
        "love": "현실 계산이 감정 부담을 키웁니다",
        "marriage": "돈 문제가 결혼 결정을 압박합니다",
    },
    "killing_pressure_excess": {
        "money": "계약 책임이 커져 돈의 부담이 늘어납니다",
        "career": "평가 압박이 강해져 피로가 커집니다",
        "love": "관계의 부담감이 커져 마음이 무거워집니다",
        "marriage": "책임 분담의 압박이 커집니다",
    },
    "officer_resource_sequence": {
        "money": "안전장치가 생겨 돈을 지킵니다",
        "career": "공식 책임이 자격과 신뢰로 인정됩니다",
        "love": "약속에 신뢰가 붙어 마음이 안정됩니다",
        "marriage": "보호 기준이 세워져 결혼 생활이 안정됩니다",
    },
    "wealth_supports_officer": {
        "money": "돈의 기준이 책임을 받쳐 재물 관리가 안정됩니다",
        "career": "성과와 보상이 책임 있는 자리로 이어집니다",
        "love": "현실 기준이 약속을 오래 가게 합니다",
        "marriage": "생활비 기준이 책임 분담을 안정시킵니다",
    },
    "output_harms_officer_order": {
        "money": "말한 결과가 계약 기준과 부딪힙니다",
        "career": "표현 방식이 평가 질서와 충돌합니다",
        "love": "말이 앞서 약속의 무게가 흔들립니다",
        "marriage": "생활 불만이 책임 기준과 부딪힙니다",
    },
    "peer_disrupts_officer_order": {
        "money": "내 몫을 앞세워 계약 질서가 흔들립니다",
        "career": "자기 기준이 공식 책임과 부딪힙니다",
        "love": "자존심이 약속의 안정감을 흔듭니다",
        "marriage": "각자의 몫이 생활 책임과 충돌합니다",
    },
    "wealth_regulates_indirect_resource": {
        "money": "현실적인 돈의 기준이 생각을 정리합니다",
        "career": "현실 성과가 특수한 지식을 쓸 자리를 만듭니다",
        "love": "현실적인 태도가 복잡한 마음을 안정시킵니다",
        "marriage": "생활비 기준이 불안을 줄입니다",
    },
    "resource_turns_into_output": {
        "money": "머릿속 지식이 결과물로 나와 돈이 됩니다",
        "career": "특수한 이해가 산출물로 바뀌어 평가를 받습니다",
        "love": "생각을 표현으로 바꾸며 관계가 가까워집니다",
        "marriage": "마음속 기준을 행동으로 옮기며 안정됩니다",
    },
    "indirect_resource_excess": {
        "money": "생각이 많아져 금전 결정이 늦어집니다",
        "career": "해석이 깊어도 실행이 늦어집니다",
        "love": "마음을 오래 숨겨 관계가 늦어집니다",
        "marriage": "생활 결정을 오래 미룹니다",
    },
    "wealth_regulates_direct_resource": {
        "money": "현실적인 돈의 기준이 안정 욕구를 잡아 줍니다",
        "career": "보상 기준이 자격을 성과로 바꿉니다",
        "love": "현실적인 태도가 신뢰 확인을 편하게 만듭니다",
        "marriage": "생활비 기준이 보호 욕구를 안정시킵니다",
    },
    "resource_turns_into_visible_result": {
        "money": "배운 것이 결과물로 보여 돈이 됩니다",
        "career": "자격과 준비가 결과물로 인정됩니다",
        "love": "신뢰가 표현으로 나와 관계가 가까워집니다",
        "marriage": "보호하려는 마음이 행동으로 보여 안정됩니다",
    },
    "direct_resource_excess": {
        "money": "안정 확인이 길어져 금전 결정이 늦어집니다",
        "career": "준비가 길어져 평가 시점을 놓칩니다",
        "love": "확신 확인이 길어져 표현이 늦어집니다",
        "marriage": "안정 확인이 길어져 결혼 결정이 늦어집니다",
    },
    "resource_overprotects_day_master": {
        "money": "안전을 먼저 보느라 돈을 늦게 움직입니다",
        "career": "보호와 준비가 길어져 실행이 늦어집니다",
        "love": "마음을 보호하려다 표현이 늦어집니다",
        "marriage": "안정 확인이 길어져 생활 결정이 늦어집니다",
    },
}

PATTERN_SUPPORT_REASON_CODES = {
    "peer_pattern_needs_officer",
    "peer_pattern_uses_output",
    "yangren_needs_officer_control",
    "yangren_uses_output_release",
    "eating_god_generates_wealth",
    "eating_god_results_enter_responsibility",
    "hurting_officer_generates_wealth",
    "hurting_officer_needs_resource_refinement",
    "indirect_wealth_supports_officer",
    "output_sources_indirect_wealth",
    "direct_wealth_supports_officer",
    "output_sources_direct_wealth",
    "eating_god_controls_seven_killings",
    "seven_killings_transforms_to_resource",
    "officer_resource_sequence",
    "wealth_supports_officer",
    "wealth_regulates_indirect_resource",
    "resource_turns_into_output",
    "wealth_regulates_direct_resource",
    "resource_turns_into_visible_result",
}

PATTERN_PRESSURE_REASON_CODES = {
    "peer_pattern_excess_peer",
    "peer_pattern_resource_overfeeds",
    "yangren_excess_competition",
    "yangren_resource_overfeeds",
    "resource_can_damage_eating_god",
    "hurting_officer_clashes_with_officer",
    "peer_competes_for_indirect_wealth",
    "resource_slows_wealth_movement",
    "peer_competes_for_direct_wealth",
    "resource_slows_wealth_accumulation",
    "wealth_feeds_seven_killings",
    "killing_pressure_excess",
    "output_harms_officer_order",
    "peer_disrupts_officer_order",
    "indirect_resource_excess",
    "direct_resource_excess",
    "resource_overprotects_day_master",
}

PATTERN_SUPPORT_OPENING: dict[Domain, str] = {
    "money": "격국상 필요한 {element} 기운이 강해집니다. 계약 내용과 정산 방식이 잡힙니다.",
    "career": "격국상 필요한 {element} 기운이 강해집니다. 맡을 역할과 평가 기준이 잡힙니다.",
    "love": "격국상 필요한 {element} 기운이 강해집니다. 연락과 약속의 방향이 잡힙니다.",
    "marriage": "격국상 필요한 {element} 기운이 강해집니다. 생활비와 책임 기준이 잡힙니다.",
}

PATTERN_RELATION_SUPPORT_OPENING: dict[Domain, str] = {
    "money": "{relation} 관계가 격국상 필요한 {element} 기운을 살립니다. 계약 내용과 정산 방식이 잡힙니다.",
    "career": "{relation} 관계가 격국상 필요한 {element} 기운을 살립니다. 맡을 역할과 평가 기준이 잡힙니다.",
    "love": "{relation} 관계가 격국상 필요한 {element} 기운을 살립니다. 연락과 약속의 방향이 잡힙니다.",
    "marriage": "{relation} 관계가 격국상 필요한 {element} 기운을 살립니다. 생활비와 책임 기준이 잡힙니다.",
}

PATTERN_PRESSURE_OPENING: dict[Domain, str] = {
    "money": "격국상 부담이 되는 {element} 기운은 재물운에서 정산 부담을 키웁니다.",
    "career": "격국상 부담이 되는 {element} 기운은 직업운에서 책임 압박을 키웁니다.",
    "love": "격국상 부담이 되는 {element} 기운은 연애운에서 감정 피로를 키웁니다.",
    "marriage": "격국상 부담이 되는 {element} 기운은 결혼운에서 생활 부담을 키웁니다.",
}

PATTERN_RELATION_PRESSURE_OPENING: dict[Domain, str] = {
    "money": "{relation} 관계가 격국상 부담이 되는 {element} 기운도 키웁니다.",
    "career": "{relation} 관계가 격국상 부담이 되는 {element} 기운도 키웁니다.",
    "love": "{relation} 관계가 격국상 부담이 되는 {element} 기운도 키웁니다.",
    "marriage": "{relation} 관계가 격국상 부담이 되는 {element} 기운도 키웁니다.",
}

POSITION_LABELS = {
    "year": "연주",
    "month": "월주",
    "day": "일주",
    "hour": "시주",
}

POSITION_BRANCH_LABELS = {
    "year": "연지",
    "month": "월지",
    "day": "일지",
    "hour": "시지",
}

SEASON_LABELS = {
    "spring": "봄",
    "summer": "여름",
    "autumn": "가을",
    "winter": "겨울",
    "late_spring": "늦봄",
    "late_summer": "환절기",
    "late_autumn": "늦가을",
    "late_winter": "늦겨울",
}

BRANCH_RELATION_LABELS = {
    "six_combine": "육합",
    "clash": "충",
    "punishment": "형",
    "harm": "해",
    "break": "파",
    "self_punishment": "자형",
    "three_harmony": "삼합",
    "three_harmony_half": "반합",
    "three_meeting": "방합",
}

CONNECTING_RELATION_TYPES = {"six_combine", "three_harmony", "three_harmony_half", "three_meeting"}
DISRUPTING_RELATION_TYPES = {"clash", "punishment", "harm", "break", "self_punishment"}

DOMAIN_POSITION_PRIORITY: dict[Domain, tuple[str, ...]] = {
    "money": ("month", "hour", "day", "year"),
    "career": ("month", "year", "hour", "day"),
    "love": ("day", "hour", "month", "year"),
    "marriage": ("day", "month", "hour", "year"),
}

DOMAIN_OUTPUT_TARGETS: dict[Domain, tuple[str, ...]] = {
    "money": ("수입이 생기는 방식", "손실이 생기는 지점", "자산으로 남는 힘", "계약과 거래 판단"),
    "career": ("맡게 되는 역할", "권한과 책임", "전문성 인정", "조직 안에서의 성취"),
    "love": ("호감이 생기는 방식", "감정 표현", "관계 주도권", "반복되는 피로 지점"),
    "marriage": ("생활 안정", "책임 분담", "감정적 충돌", "가정의 현실 문제"),
}

DOMAIN_MONTH_EFFECT = {
    "money": "재물에서는 큰 수입보다 손에 남는 돈이 더 중요합니다.",
    "career": "직업에서는 맡은 책임과 평가 기준을 먼저 의식합니다.",
    "love": "연애에서는 감정의 속도와 표현 방식이 관계의 체감을 바꿉니다.",
    "marriage": "결혼에서는 애정의 확신보다 생활 기준과 책임 문제가 더 크게 남습니다.",
}

DOMAIN_MONTH_BASE = {
    "money": "돈의 안정성과 장기 축적을 중요하게 여깁니다.",
    "career": "사회적 책임과 평가 기준을 민감하게 받아들입니다.",
    "love": "마음이 생겨도 관계의 속도와 표현 방식을 중요하게 여깁니다.",
    "marriage": "좋아하는 마음이 깊어져도 생활 기준을 함께 확인합니다.",
}

DOMAIN_MONTH_LEAD = {
    "money": "월령에서는 돈이 들어오는 방식과 손에 남는 방식이 함께 정해집니다.",
    "career": "월령에서는 책임을 맡는 방식과 평가를 받는 방식이 정해집니다.",
    "love": "월령에서는 마음이 열리는 속도와 표현 방식이 정해집니다.",
    "marriage": "월령에서는 애정의 확신보다 결혼 생활의 기준과 가족 책임이 먼저 올라옵니다.",
}

DOMAIN_ELEMENT_EFFECT = {
    "money": "재물에서는 돈이 들어오는 경로와 남기는 방식이 함께 보입니다. 수입이 생긴 뒤에도 보유 기준을 따로 세웁니다.",
    "career": "직업에서는 일을 처리하는 순서와 평가받는 방식이 함께 보입니다. 맡은 일이 결과로 남을 때 인정도 빨라집니다.",
    "love": "연애에서는 마음이 열리는 속도와 표현 방식이 함께 달라집니다. 호감이 생긴 뒤의 태도가 관계의 거리를 바꿉니다.",
    "marriage": "결혼에서는 생활 약속을 받아들이는 태도와 책임을 나누는 방식이 함께 보입니다. 애정이 생활의 약속으로 옮겨질 때 안정됩니다.",
}

ELEMENT_TRAIT_SENTENCES = {
    "관계망 확장": "사람을 만나며 기회가 넓어집니다.",
    "사회적 교류": "대화와 만남이 소개와 제안으로 이어집니다.",
    "조직적 결속": "팀 안에서 역할을 묶는 힘이 강합니다.",
    "친화주의": "사람과 부드럽게 맞추려는 태도가 강합니다.",
    "도움 받기": "필요한 순간 주변의 도움을 끌어옵니다.",
    "단계적 성장": "작은 역할이 커지며 다음 책임으로 이어집니다.",
    "활용": "배운 내용을 곧바로 일과 생활의 판단에 옮깁니다.",
    "경험 전환": "지나간 경험이 다음 선택의 재료가 됩니다.",
    "기준 조정": "서로 다른 기준을 맞추는 일이 많습니다.",
    "압박": "선택 앞에서 압박을 크게 느낍니다.",
    "선택": "결정해야 할 일이 자주 생깁니다.",
    "성향 반복": "같은 선택 방식이 반복됩니다.",
    "동질성": "비슷한 사람이나 비슷한 환경에 끌립니다.",
    "집중": "한 방향에 힘을 오래 쏟습니다.",
    "복합성": "상황을 단순하게 자르기 어렵습니다.",
    "상황 의존": "장소와 상대에 따라 반응이 달라집니다.",
    "해석 보류": "결론을 바로 내리기보다 더 살핍니다.",
}

ELEMENT_TRAIT_DOMAIN_SENTENCES: dict[str, dict[Domain, str]] = {
    "관계망 확장": {
        "money": "사람을 통한 기회가 수입으로 바뀝니다.",
        "career": "넓어진 관계가 직업 기회로 바뀝니다.",
        "love": "새로운 만남이 늘어나며 관계의 폭이 넓어집니다.",
        "marriage": "좋아하는 마음이 생활 기준을 말하는 단계로 넘어갑니다.",
    },
    "사회적 교류": {
        "money": "대외 접촉이 돈이 될 기회를 만듭니다.",
        "career": "대화 능력으로 직업 평가를 받습니다.",
        "love": "대화가 편해지면서 마음을 여는 속도도 빨라집니다.",
        "marriage": "대화가 생활비 기준을 확인하는 자리로 이어집니다.",
    },
    "단계적 성장": {
        "money": "작은 수입이 반복되며 남길 돈도 점차 커집니다.",
        "career": "작은 역할이 커지며 다음 책임을 맡게 됩니다.",
        "love": "가벼운 대화가 반복되며 마음을 여는 속도도 빨라집니다.",
        "marriage": "작은 약속이 쌓이며 생활 책임도 정해집니다.",
    },
    "활용": {
        "money": "배운 내용을 수입 기준과 지출 판단에 바로 적용합니다.",
        "career": "배운 내용을 곧바로 업무 방식과 결과물로 옮깁니다.",
        "love": "상대에게 배운 반응을 다음 대화와 표현에 바로 반영합니다.",
        "marriage": "함께 겪은 일을 생활 방식과 책임 분담에 바로 반영합니다.",
    },
}

DOMAIN_USEFUL_ELEMENT_EFFECT = {
    "money": "{elements} 기운은 받을 돈을 자산으로 바꾸는 힘을 키웁니다. 수입 이후의 지출 기준도 잡힙니다.",
    "career": "직업에서는 {elements} 기운이 책임 감당력과 인정운을 키웁니다.",
    "love": "연애에서는 {elements} 기운이 감정 표현을 부드럽게 만듭니다.",
    "marriage": "결혼에서는 {elements} 기운이 생활 기준과 책임 분담을 안정시킵니다.",
}

DOMAIN_CAUTION_ELEMENT_EFFECT = {
    "money": "{elements} 기운의 과잉은 돈을 벌 욕심을 키웁니다. 지출 판단도 어긋납니다.",
    "career": "{elements} 기운의 과잉은 맡는 일을 넓힙니다. 책임 부담도 커집니다.",
    "love": "{elements} 기운의 과잉은 감정 반응을 크게 만듭니다. 거리감도 예민해집니다.",
    "marriage": "{elements} 기운의 과잉은 생활 기준을 강하게 만듭니다. 가족 문제도 민감해집니다.",
}

DOMAIN_BRANCH_EFFECT = {
    "money": "재물에서는 정산 문제가 먼저 생깁니다. 지출 약속도 따로 다룹니다.",
    "career": "직업에서는 책임 범위가 업무 현장에서 커집니다. 소속 변화도 함께 생깁니다.",
    "love": "연애에서는 연락 방식이 먼저 달라집니다. 감정 반응도 관계의 분위기를 바꿉니다.",
    "marriage": "결혼에서는 생활 기준이 먼저 잡힙니다. 가족 문제도 생활에서 다루게 됩니다.",
}

DOMAIN_POSITION_EFFECT = {
    "money": "돈의 쓰임과 수입 안정성, 장기 축적을 먼저 따지게 만듭니다.",
    "career": "사회적 역할과 책임 범위, 평가 기준을 직접 의식하게 만듭니다.",
    "love": "가까운 관계에서 마음을 여는 속도와 거리감을 조절하게 만듭니다.",
    "marriage": "배우자와 생활을 맞추고 책임을 나누는 문제로 이어집니다.",
}

POSITION_REALITY_ROLES = {
    "year": "사회적 배경",
    "month": "직업과 사회 환경",
    "day": "배우자궁과 가까운 생활 자리",
    "hour": "후반기 선택과 실무",
}

DOMAIN_ELEMENT_BRANCH_TEXTURE: dict[Domain, dict[str, str]] = {
    "money": {
        "wood": "계약 기준과 책임 비용",
        "fire": "평판과 지출 명분",
        "earth": "보유 자산과 생활비",
        "metal": "정산과 회수 판단",
        "water": "수입과 지출 시점",
    },
    "career": {
        "wood": "직업 역할 확장과 책임",
        "fire": "업무 표현과 공식 평가",
        "earth": "업무 기반과 역할 범위",
        "metal": "업무 결정과 역할 정리",
        "water": "업무 정보와 보상 기준",
    },
    "love": {
        "wood": "관계의 시작과 약속",
        "fire": "표현과 호감",
        "earth": "거리감과 생활 안정",
        "metal": "정리와 선택",
        "water": "감정 반응과 연락",
    },
    "marriage": {
        "wood": "생활 책임과 성장 계획",
        "fire": "표현과 가족 평판",
        "earth": "생활 기반과 주거 문제",
        "metal": "결정과 역할 정리",
        "water": "돈 문제와 생활비 기준",
    },
}

POSITION_DOMAIN_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "month": "월지의 재물 기운은 직업 수입을 키웁니다. 고정 지출도 같은 자리에서 커집니다.",
        "hour": "시지의 재물 신호는 후반기 자산 기준을 만듭니다. 실무 보상도 함께 커집니다.",
        "day": "일지의 재물 기운은 생활비 문제로 이어집니다. 가까운 사람과 함께 쓰는 돈도 재물 판단에 포함됩니다.",
        "year": "연지의 재물 기운은 집안에서 익힌 돈 감각으로 남습니다. 밖에서 얻는 돈의 기준도 초기 환경에서 배웁니다.",
    },
    "career": {
        "month": "월지에 놓인 직업 기운은 실제 직장 환경에서 힘을 냅니다. 맡는 책임과 평가 방식도 구체적으로 정해집니다.",
        "year": "연지에 놓인 직업 기운은 대외 평판에 남습니다. 첫 소속의 영향도 오래 갑니다.",
        "hour": "시지에 놓인 직업 기운은 실무 책임으로 이어집니다. 후반기 전문성도 함께 강해집니다.",
        "day": "일지에 놓인 직업 기운은 가까운 관계에서 맡은 책임을 일의 태도에도 남깁니다.",
    },
    "love": {
        "day": "일지에 놓인 애정 기운은 마음을 주는 방식에서 가장 분명합니다. 가까워진 뒤의 거리감도 여기서 나옵니다.",
        "hour": "시지의 애정 기운은 늦게 생기는 기대에서 커집니다. 연락 방식도 그 영향을 받습니다.",
        "month": "월지의 애정 기운은 사회생활의 피로를 연애 태도에 남깁니다.",
        "year": "연지에 놓인 애정 기운은 초기에 익숙해진 인간관계와 마음을 여는 속도에 남습니다.",
    },
    "marriage": {
        "day": "일지에 놓인 결혼 기운은 배우자와의 생활 방식을 결정합니다. 감정 충돌도 가까운 생활 안에서 커집니다.",
        "month": "월지의 결혼 기운은 직업 문제를 결혼 이야기로 끌어옵니다. 돈 문제도 함께 커집니다.",
        "hour": "시지에 놓인 결혼 기운은 후반기 생활 계획으로 이어집니다. 장기 주거 문제도 이때 정해집니다.",
        "year": "연지에 놓인 결혼 기운은 가족 배경을 결혼 판단에 남깁니다. 주변 시선도 쉽게 무시되지 않습니다.",
    },
}

HIDDEN_POSITION_DOMAIN_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "month": "월지 지장간은 직업 안에서 생기는 숨은 수입 기준을 안에 품고 있습니다. 고정비도 함께 다룹니다.",
        "hour": "시지 지장간은 늦게 생기는 자산 욕심을 안에 품고 있습니다. 따로 모으는 돈도 강해집니다.",
        "day": "일지 지장간은 가까운 사람과 섞이는 돈 문제를 안에 품고 있습니다. 생활비 문제도 함께 커집니다.",
        "year": "연지 지장간은 집안에서 익힌 돈 감각을 안에 품고 있습니다. 외부 도움도 이 영향에서 나옵니다.",
    },
    "career": {
        "month": "월지 지장간은 직장 안에서 실제로 맡게 되는 책임을 안에 품고 있습니다. 평가를 의식하는 속마음도 여기서 읽힙니다.",
        "year": "연지 지장간은 평판을 의식하는 속마음을 품고 있습니다. 첫 소속의 영향도 함께 드러납니다.",
        "hour": "시지 지장간은 후반기 전문성을 안에 품고 있습니다. 실무 결과물도 함께 강해집니다.",
        "day": "일지 지장간은 가까운 관계에서 생긴 책임감을 안에 품고 있습니다. 그 책임감이 일의 태도로 옮겨갑니다.",
    },
    "love": {
        "day": "일지 지장간은 가까워진 뒤의 반응을 안쪽에 품고 있습니다.",
        "hour": "시지 지장간은 늦게 생기는 기대를 안에 품고 있습니다. 연락 습관도 이 영향에서 나옵니다.",
        "month": "월지 지장간은 사회생활에서 쌓인 긴장을 안에 품고 있습니다. 그 긴장이 연애 태도에도 남습니다.",
        "year": "연지 지장간은 초기 관계 경험을 안에 품고 있습니다. 마음을 여는 속도도 이 영향에서 읽힙니다.",
    },
    "marriage": {
        "day": "일지 지장간은 배우자에게 기대하는 생활 방식을 안에 품고 있습니다. 감정 충돌이 생기는 이유도 여기서 나옵니다.",
        "month": "월지 지장간은 직업 문제가 결혼 생활로 들어오는 단서를 안에 품고 있습니다. 돈 문제도 같이 커집니다.",
        "hour": "시지 지장간은 후반기 생활 계획을 안에 품고 있습니다. 장기 주거 문제도 이때 정해집니다.",
        "year": "연지 지장간은 집안 분위기와 주변 시선을 안에 품고 있습니다. 결혼 판단에도 그 영향이 남습니다.",
    },
}

HIDDEN_GROUP_DOMAIN_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "peer": "비겁은 돈을 나누는 문제를 만듭니다.",
        "output": "식상은 수입을 만들어 내는 기술입니다.",
        "wealth": "재성은 받을 돈과 보관할 돈을 구분하게 합니다.",
        "officer": "관성은 계약 기준과 책임 비용을 세웁니다.",
        "resource": "인성은 생긴 돈을 오래 지키는 힘이 됩니다.",
    },
    "career": {
        "peer": "비겁은 동료와 경쟁 속에서 역할을 세웁니다.",
        "output": "식상은 결과물과 실무 능력을 만듭니다.",
        "wealth": "재성은 성과를 보상과 거래로 연결합니다.",
        "officer": "관성은 직책, 책임, 공식 평가를 만듭니다.",
        "resource": "인성은 자격, 문서, 신뢰의 기반이 됩니다.",
    },
    "love": {
        "peer": "비겁은 관계 안의 주도권과 비교심을 키웁니다.",
        "output": "식상은 말투와 표현 방식으로 마음을 전합니다.",
        "wealth": "재성은 현실 감각과 상대의 기대를 의식하게 합니다.",
        "officer": "관성은 약속과 책임의 무게로 느껴집니다.",
        "resource": "인성은 안정감과 보호받고 싶은 마음을 키웁니다.",
    },
    "marriage": {
        "peer": "비겁은 생활 주도권과 몫 나눔 문제를 만듭니다.",
        "output": "식상은 말로 풀어야 할 불만을 만듭니다.",
        "wealth": "재성은 생활비와 자산 문제를 만듭니다.",
        "officer": "관성은 부부 사이의 책임과 약속을 세웁니다.",
        "resource": "인성은 가정을 지키려는 마음을 키웁니다.",
    },
}

HIDDEN_TEN_GOD_DOMAIN_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "bi_gyeon": "비견은 공동 비용과 내 몫의 기준을 세웁니다.",
        "geob_jae": "겁재는 나누어야 할 돈과 경쟁 지출을 만듭니다.",
        "sik_sin": "식신은 반복해서 만든 결과를 수입으로 바꿉니다.",
        "sang_gwan": "상관은 말, 기획, 표현의 결과를 보상 문제로 가져옵니다.",
        "pyeon_jae": "편재는 거래와 외부 수입의 기회를 크게 만듭니다.",
        "jeong_jae": "정재는 받을 돈과 생활비를 분명히 세웁니다.",
        "pyeon_gwan": "편관은 세금, 위약, 책임 비용을 먼저 따지게 만듭니다.",
        "jeong_gwan": "정관은 돈을 계약서와 문서로 분명하게 묶습니다.",
        "pyeon_in": "편인은 정보와 검토가 돈의 판단을 바꾸게 만듭니다.",
        "jeong_in": "정인은 문서와 보존 기준으로 생긴 돈을 지키게 만듭니다.",
    },
    "career": {
        "bi_gyeon": "비견은 독자적인 역할과 자기 기준을 직업 장면에 세웁니다.",
        "geob_jae": "겁재는 성과 경쟁을 직업 장면으로 가져옵니다.",
        "sik_sin": "식신은 반복 가능한 실무 능력과 결과물을 만듭니다.",
        "sang_gwan": "상관은 기획 능력을 평가 장면으로 가져옵니다.",
        "pyeon_jae": "편재는 외부 거래를 직업 기회로 만듭니다.",
        "jeong_jae": "정재는 성실한 관리와 숫자 감각을 업무 기준으로 만듭니다.",
        "pyeon_gwan": "편관은 압박이 큰 역할과 긴급한 책임을 맡게 합니다.",
        "jeong_gwan": "정관은 공식 책임을 분명히 세웁니다.",
        "pyeon_in": "편인은 분석 능력을 직업 강점으로 만듭니다.",
        "jeong_in": "정인은 자격을 직업 기반으로 만듭니다.",
    },
    "love": {
        "bi_gyeon": "비견은 관계 안에서 자기 입장과 거리감을 분명히 세웁니다.",
        "geob_jae": "겁재는 관계의 주도권과 비교심을 예민하게 만듭니다.",
        "sik_sin": "식신은 편안한 말투와 꾸준한 표현으로 마음을 전합니다.",
        "sang_gwan": "상관은 빠른 표현과 감정 반응을 관계 안에서 키웁니다.",
        "pyeon_jae": "편재는 끌림과 선택지를 넓혀 새로운 만남을 만듭니다.",
        "jeong_jae": "정재는 안정적인 태도와 생활 감각으로 마음을 확인합니다.",
        "pyeon_gwan": "편관은 긴장감 있는 끌림과 조급한 판단을 만들기 쉽습니다.",
        "jeong_gwan": "정관은 약속을 먼저 따지게 만듭니다.",
        "pyeon_in": "편인은 상대의 말과 반응을 깊이 해석하게 만듭니다.",
        "jeong_in": "정인은 안정감과 보호받고 싶은 마음을 크게 만듭니다.",
    },
    "marriage": {
        "bi_gyeon": "비견은 부부 사이의 생활 주도권을 세웁니다.",
        "geob_jae": "겁재는 생활비 분담과 가족 안의 몫 나눔을 예민하게 만듭니다.",
        "sik_sin": "식신은 일상의 표현과 돌봄이 결혼 생활에 들어오게 합니다.",
        "sang_gwan": "상관은 말투와 불만 표현이 결혼 생활의 쟁점이 되게 합니다.",
        "pyeon_jae": "편재는 외부 활동을 결혼 이야기로 가져옵니다.",
        "jeong_jae": "정재는 생활비 기준을 결혼 문제로 가져옵니다.",
        "pyeon_gwan": "편관은 가족 책임과 압박이 결혼 결정에 들어오게 만듭니다.",
        "jeong_gwan": "정관은 혼인 약속을 분명히 세웁니다.",
        "pyeon_in": "편인은 가족 문제를 깊이 따지고 결혼 결정을 늦추게 만듭니다.",
        "jeong_in": "정인은 집의 안정감을 결혼 기반으로 만듭니다.",
    },
}

PROTRUDED_TEN_GOD_DOMAIN_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "bi_gyeon": "밖으로 드러난 비견은 공동 비용에서 내 몫을 분명히 세우게 합니다.",
        "geob_jae": "밖으로 드러난 겁재는 분배와 경쟁 지출을 먼저 예민하게 만듭니다.",
        "sik_sin": "밖으로 드러난 식신은 반복해서 만든 결과를 돈으로 바꿉니다.",
        "sang_gwan": "밖으로 드러난 상관은 말과 기획의 대가를 금액으로 따지게 합니다.",
        "pyeon_jae": "밖으로 드러난 편재는 거래와 외부 수입의 기회를 분명하게 드러냅니다.",
        "jeong_jae": "밖으로 드러난 정재는 받을 돈과 지급일을 분명하게 만듭니다.",
        "pyeon_gwan": "밖으로 드러난 편관은 책임 비용과 급한 지출을 먼저 보게 만듭니다.",
        "jeong_gwan": "밖으로 드러난 정관은 계약서와 정산 기준을 먼저 세웁니다.",
        "pyeon_in": "밖으로 드러난 편인은 정보 확인과 계산이 돈의 판단을 바꾸게 합니다.",
        "jeong_in": "밖으로 드러난 정인은 문서와 보존 기준으로 돈을 지키게 합니다.",
    },
    "career": {
        "bi_gyeon": "밖으로 드러난 비견은 독자적인 판단과 역할 주도권을 분명히 세웁니다.",
        "geob_jae": "밖으로 드러난 겁재는 경쟁과 성과 분배 문제를 업무 현장으로 가져옵니다.",
        "sik_sin": "밖으로 드러난 식신은 반복 가능한 결과물로 인정을 받게 합니다.",
        "sang_gwan": "밖으로 드러난 상관은 기획 능력을 평가 장면으로 가져옵니다.",
        "pyeon_jae": "밖으로 드러난 편재는 외부 기회를 업무 성과로 만듭니다.",
        "jeong_jae": "밖으로 드러난 정재는 관리 능력과 숫자 감각을 업무 기준으로 만듭니다.",
        "pyeon_gwan": "밖으로 드러난 편관은 압박이 큰 책임과 긴급한 역할을 맡게 합니다.",
        "jeong_gwan": "밖으로 드러난 정관은 공식 책임과 직책 문제를 분명히 세웁니다.",
        "pyeon_in": "밖으로 드러난 편인은 분석력과 특수 지식을 직업 강점으로 만듭니다.",
        "jeong_in": "밖으로 드러난 정인은 자격, 문서, 교육 이력을 직업 기반으로 만듭니다.",
    },
    "love": {
        "bi_gyeon": "밖으로 드러난 비견은 관계의 속도와 거리를 분명히 세웁니다.",
        "geob_jae": "밖으로 드러난 겁재는 관계의 주도권과 비교심을 예민하게 만듭니다.",
        "sik_sin": "밖으로 드러난 식신은 꾸준한 표현과 다정한 태도를 관계에서 살립니다.",
        "sang_gwan": "밖으로 드러난 상관은 말투와 감정 반응을 빠르게 키웁니다.",
        "pyeon_jae": "밖으로 드러난 편재는 새로운 만남과 끌림을 밖에서 만들게 합니다.",
        "jeong_jae": "밖으로 드러난 정재는 안정적인 태도와 생활 감각으로 관계를 봅니다.",
        "pyeon_gwan": "밖으로 드러난 편관은 긴장감 있는 끌림과 압박을 관계에 만듭니다.",
        "jeong_gwan": "밖으로 드러난 정관은 약속과 신뢰를 관계의 기준으로 세웁니다.",
        "pyeon_in": "밖으로 드러난 편인은 상대의 말과 반응을 깊이 따지게 만듭니다.",
        "jeong_in": "밖으로 드러난 정인은 안정감과 보호받고 싶은 마음을 크게 키웁니다.",
    },
    "marriage": {
        "bi_gyeon": "밖으로 드러난 비견은 부부 사이의 몫과 생활 주도권을 분명히 세웁니다.",
        "geob_jae": "밖으로 드러난 겁재는 생활비 분담과 가족 안의 몫 문제를 예민하게 만듭니다.",
        "sik_sin": "밖으로 드러난 식신은 일상의 돌봄과 표현을 결혼 생활에서 살립니다.",
        "sang_gwan": "밖으로 드러난 상관은 말투와 불만 표현을 결혼 쟁점으로 만듭니다.",
        "pyeon_jae": "밖으로 드러난 편재는 돈과 외부 활동 문제를 결혼 이야기로 가져옵니다.",
        "jeong_jae": "밖으로 드러난 정재는 생활비 기준을 결혼 문제로 세웁니다.",
        "pyeon_gwan": "밖으로 드러난 편관은 가족 책임과 결정 압박을 결혼 문제로 가져옵니다.",
        "jeong_gwan": "밖으로 드러난 정관은 혼인 약속과 책임 분담을 분명히 세웁니다.",
        "pyeon_in": "밖으로 드러난 편인은 가족 문제와 준비 상태를 깊이 따지게 만듭니다.",
        "jeong_in": "밖으로 드러난 정인은 집의 안정감을 결혼 기반으로 만듭니다.",
    },
}

STEM_RECEPTION_EVENT_BY_DOMAIN: dict[Domain, dict[str, str]] = {
    "money": {
        "bi_gyeon": "공동 비용과 내 몫의 기준을 나누는 일",
        "geob_jae": "분배와 경쟁 지출을 다시 계산하는 일",
        "sik_sin": "반복해서 만든 결과를 금액으로 인정받는 일",
        "sang_gwan": "말과 기획의 대가를 보상 기준으로 따지는 일",
        "pyeon_jae": "외부 거래와 큰 수입 기회를 움직이는 일",
        "jeong_jae": "받을 돈, 지급일, 보관할 돈을 나누는 일",
        "pyeon_gwan": "책임 비용과 급한 지출을 먼저 확인하는 일",
        "jeong_gwan": "계약서와 정산 기준을 바로 세우는 일",
        "pyeon_in": "정보 확인과 계산으로 돈의 판단을 바꾸는 일",
        "jeong_in": "문서와 보존 기준으로 생긴 돈을 지키는 일",
    },
    "career": {
        "bi_gyeon": "독자적인 판단과 역할 주도권을 세우는 일",
        "geob_jae": "경쟁과 성과 분배 문제를 업무 현장에서 다루는 일",
        "sik_sin": "반복 가능한 결과물로 실력을 인정받는 일",
        "sang_gwan": "말, 기획, 표현 능력을 평가 장면에 드러내는 일",
        "pyeon_jae": "거래, 제안, 외부 기회를 업무 성과로 바꾸는 일",
        "jeong_jae": "관리 능력과 숫자 감각을 업무 기준으로 세우는 일",
        "pyeon_gwan": "압박이 큰 책임과 긴급한 역할을 맡는 일",
        "jeong_gwan": "공식 책임과 직책 문제를 분명하게 하는 일",
        "pyeon_in": "분석과 특수 지식을 직업 강점으로 보이는 일",
        "jeong_in": "자격, 문서, 교육 이력을 직업 기반으로 삼는 일",
    },
    "love": {
        "bi_gyeon": "관계의 속도와 거리를 분명히 하는 일",
        "geob_jae": "관계의 주도권과 비교심을 예민하게 다루는 일",
        "sik_sin": "꾸준한 표현과 다정한 태도를 보이는 일",
        "sang_gwan": "말투와 감정 반응을 빠르게 드러내는 일",
        "pyeon_jae": "새로운 만남과 끌림을 밖에서 만드는 일",
        "jeong_jae": "안정적인 태도와 생활 감각으로 관계를 보는 일",
        "pyeon_gwan": "긴장감 있는 끌림과 압박을 관계에서 다루는 일",
        "jeong_gwan": "약속과 신뢰를 관계의 기준으로 세우는 일",
        "pyeon_in": "상대의 말과 반응을 깊이 따지는 일",
        "jeong_in": "안정감과 보호받고 싶은 마음을 크게 드러내는 일",
    },
    "marriage": {
        "bi_gyeon": "부부 사이의 몫과 생활 주도권을 분명히 하는 일",
        "geob_jae": "생활비 분담과 가족 안의 몫 문제를 다루는 일",
        "sik_sin": "일상의 돌봄과 표현을 결혼 생활에서 분명히 하는 일",
        "sang_gwan": "말투와 불만 표현을 결혼 쟁점으로 다루는 일",
        "pyeon_jae": "돈과 외부 활동 문제가 결혼 이야기로 들어오는 일",
        "jeong_jae": "생활비와 자산 기준을 결혼 문제로 분명히 하는 일",
        "pyeon_gwan": "가족 책임과 결정 압박을 결혼 문제로 드러내는 일",
        "jeong_gwan": "혼인 약속과 책임 분담을 분명하게 하는 일",
        "pyeon_in": "가족 문제와 준비 상태를 깊이 따지는 일",
        "jeong_in": "집, 문서, 보호 욕구를 결혼 안정의 기반으로 삼는 일",
    },
}

STEM_RECEPTION_DOMAIN_ANCHORS: dict[Domain, str] = {
    "money": "돈을 판단하는 태도에도 이 글자의 성질이 들어갑니다.",
    "career": "업무에서 맡는 역할에도 이 글자의 성질이 들어갑니다.",
    "love": "호감이 생기는 방식에도 이 글자의 성질이 들어갑니다.",
    "marriage": "배우자와 생활을 맞추는 방식에도 이 글자의 성질이 들어갑니다.",
}

HIDDEN_ELEMENT_BALANCE_SENTENCES: dict[Domain, dict[str, str]] = {
    "money": {
        "supportive": "월령에서 {element} 기운은 재물운을 돕습니다. {role_subject} 돈을 남기는 힘을 키웁니다.",
        "pressure": "월령에서 {element} 기운은 재물 부담을 키웁니다. {role_subject} 수입보다 지출과 책임을 먼저 키웁니다.",
        "mixed": "월령에서 {element} 기운은 재물운을 돕지만 지출 부담도 남깁니다. {role_subject} 돈의 기준을 세웁니다. 지출 한도도 따로 세웁니다.",
        "neutral": "월령에서 {element} 기운은 보조적인 힘입니다. {role_subject} 돈의 판단을 세밀하게 바꿉니다.",
    },
    "career": {
        "supportive": "월령에서 {element} 기운은 직업운을 돕습니다. {role_subject} 맡은 역할로 인정받게 합니다.",
        "pressure": "월령에서 {element} 기운은 직업 부담을 키웁니다. {role_subject} 책임을 키웁니다. 결정권 문제도 먼저 생깁니다.",
        "mixed": "월령에서 {element} 기운은 직업운을 돕지만 평가 부담도 남깁니다. {role_subject} 능력을 쓰게 합니다. 평가 기준도 까다로워집니다.",
        "neutral": "월령에서 {element} 기운은 보조적인 힘입니다. {role_subject} 맡은 역할의 성격을 세밀하게 바꿉니다.",
    },
    "love": {
        "supportive": "월령에서 {element} 기운은 애정 표현을 부드럽게 만듭니다. {role_subject} 표현 방식을 안정시킵니다.",
        "pressure": "월령에서 {element} 기운은 관계 부담을 키웁니다. {role_subject} 호감보다 거리감과 확인 욕구를 먼저 키웁니다.",
        "mixed": "월령에서 {element} 기운은 애정 표현을 움직이지만 거리감도 남깁니다. {role_subject} 마음을 쉽게 내주지 않게 합니다. 관계의 속도는 느려집니다.",
        "neutral": "월령에서 {element} 기운은 보조적인 힘입니다. {role_subject} 마음을 주고받는 방식을 세밀하게 바꿉니다.",
    },
    "marriage": {
        "supportive": "월령에서 {element} 기운은 결혼 생활의 안정을 돕습니다. {role_subject} 생활 기준과 책임 분담을 안정시킵니다.",
        "pressure": "월령에서 {element} 기운은 결혼 부담을 키웁니다. {role_subject} 돈의 기준을 먼저 키웁니다. 가족 책임도 따로 커집니다.",
        "mixed": "월령에서 {element} 기운은 결혼 이야기를 이어 가게 하지만 생활 책임도 무겁게 만듭니다. {role_subject} 약속을 현실로 옮깁니다. 생활 기준도 따로 세웁니다.",
        "neutral": "월령에서 {element} 기운은 보조적인 힘입니다. {role_subject} 생활 방식의 차이를 세밀하게 만듭니다.",
    },
}

BRANCH_RELATION_ACTIONS = {
    "six_combine": "연결이 생깁니다. 약속도 구체적으로 오갑니다.",
    "clash": "이동과 변경이 생깁니다. 서로 부딪히는 문제도 드러납니다.",
    "punishment": "같은 부담이 반복됩니다. 예민한 반응도 커집니다.",
    "harm": "겉으로 말하기 어려운 불편을 쌓습니다.",
    "break": "약속과 기준이 흔들립니다.",
    "self_punishment": "같은 문제를 마음속에서 여러 번 되짚게 합니다.",
    "three_harmony": "한 오행의 힘을 크게 모읍니다.",
    "three_harmony_half": "한 방향으로 기운을 모읍니다.",
}

DOMAIN_BRANCH_RELATION_ACTIONS: dict[Domain, dict[str, str]] = {
    "money": {
        "break": "정산 약속과 지출 기준이 어긋납니다.",
        "harm": "말하기 어려운 손익 부담이 쌓입니다.",
    },
    "career": {
        "break": "일정과 역할 약속이 어긋납니다.",
        "harm": "겉으로 말하기 어려운 업무 부담이 쌓입니다.",
    },
    "love": {
        "break": "연락 약속과 기대가 어긋납니다.",
        "harm": "말로 꺼내기 어려운 불편이 쌓입니다.",
    },
    "marriage": {
        "break": "생활 약속과 가족 기준이 어긋납니다.",
        "harm": "말하기 어려운 생활 부담이 쌓입니다.",
    },
}

DOMAIN_HIDDEN_STEM_EFFECT = {
    "money": "이 숨은 재료는 받을 돈과 빠져나갈 돈을 가르는 장면에서 힘을 냅니다.",
    "career": "이 숨은 재료는 책임을 맡거나 평가를 받을 때 실력으로 확인됩니다.",
    "love": "이 숨은 재료는 가까운 관계에서 감정 반응과 거리감으로 확인됩니다.",
    "marriage": "이 숨은 재료는 생활비 문제에서 먼저 확인됩니다. 가족 책임도 결혼 생활에서 먼저 드러납니다.",
}

DOMAIN_TEN_GOD_EFFECT = {
    "money": "식상은 수입을 만들고, 관성은 계약 기준을 세웁니다. 인성은 보존력을 키웁니다. 재성은 돈이 생기는 자리를 정합니다. 분배 기준도 따로 따집니다.",
    "career": "관성은 책임을 맡게 하고, 식상은 결과물을 만듭니다. 인성은 전문성과 신뢰를 키웁니다. 이 조합은 업무에서 맡는 역할과 평가 기준을 분명하게 만듭니다.",
    "love": "식상은 표현을 만들고, 비겁은 주도성을 키웁니다. 인성은 안정 욕구를 강하게 합니다. 이 조합에서는 연락 방식과 감정 표현이 관계 안에서 맞춰지는 과정이 뚜렷합니다.",
    "marriage": "재성은 생활 감각을 만듭니다. 관성은 책임을 세웁니다. 인성은 가정을 지키려는 힘을 키웁니다.",
}

DOMAIN_STRENGTH_EFFECT = {
    "money": {
        "strong": "돈을 크게 움직일 배짱이 있습니다. 분배 기준도 강하게 따집니다. 지출 기준도 따로 세워야 합니다.",
        "balanced": "수입과 지출을 함께 다루는 감각이 비교적 안정적입니다.",
        "weak": "큰돈을 급히 키우기보다 감당 가능한 계약과 관리 기준을 먼저 세우는 쪽입니다.",
        "very_weak": "큰돈보다 안정적인 수입 기준과 보존력이 더 중요한 재물 구조입니다.",
    },
    "career": {
        "strong": "직업에서는 큰 책임과 경쟁을 직접 감당하려는 힘이 강합니다.",
        "balanced": "직업에서는 책임과 권한을 비교적 균형 있게 받아들이는 편입니다.",
        "weak": "직업에서는 권한보다 책임이 커지는 자리를 오래 버티기 어렵습니다.",
        "very_weak": "직업에서는 보호 장치와 명확한 기준이 있어야 맡은 일을 끝까지 감당합니다.",
    },
    "love": {
        "strong": "관계에서는 주도권을 직접 잡으려는 성향이 뚜렷합니다.",
        "balanced": "관계에서는 다가가는 힘과 받아들이는 힘이 비교적 고릅니다.",
        "weak": "관계에서는 상대의 반응을 크게 의식하고 마음을 늦게 여는 편입니다.",
        "very_weak": "관계에서는 안정감이 확인될 때 깊은 감정 표현이 나옵니다.",
    },
    "marriage": {
        "strong": "결혼에서는 자신의 생활 기준을 분명히 세우려는 힘이 강합니다.",
        "balanced": "결혼에서는 책임과 생활 기준을 비교적 현실적으로 맞추는 편입니다.",
        "weak": "결혼에서는 상대의 요구와 가족 문제에 쉽게 지치기 쉽습니다.",
        "very_weak": "결혼에서는 생활 기준이 분명해야 관계가 오래 안정됩니다.",
    },
}

EVENT_CONCLUSIONS = {
    "income_growth": "해낸 일이 받을 돈으로 인정되는 해입니다.",
    "managed_income_expansion": "수입 규모가 커지는 해입니다.",
    "cashflow_defense": "새 수입보다 현금 보존과 지출 정리가 중요한 해입니다.",
    "income_structure_change": "돈을 버는 방식 자체가 달라지는 해입니다.",
    "money_flow_adjustment": "돈의 쓰임과 보관 방식을 다시 잡는 해입니다.",
    "role_expansion_or_transition": "맡는 역할이 커지는 해입니다.",
    "career_recognition": "해낸 일이 공식 평가와 다음 역할로 이어지는 해입니다.",
    "responsibility_pressure": "책임이 무거워지는 해입니다.",
    "work_environment_change": "소속과 업무 배치가 바뀌는 해입니다.",
    "career_pace_adjustment": "업무의 순서와 책임 범위를 다시 잡는 해입니다.",
    "relationship_opening": "새 인연이 생기는 시기입니다.",
    "relationship_with_conditions": "호감은 생기지만 거리가 쉽게 좁혀지지는 않는 시기입니다.",
    "relationship_friction": "감정 충돌이 커지기 쉬운 시기입니다.",
    "relationship_boundary_check": "연락 방식과 개인 영역을 다시 확인하는 시기입니다.",
    "relationship_expression_alignment": "감정 표현이 관계의 핵심이 되는 시기입니다.",
    "relationship_recovery_check": "오해를 풀고 관계를 다시 맞추는 시기입니다.",
    "relationship_contact_increase": "접촉과 만남의 빈도가 늘어나는 시기입니다.",
    "relationship_temperature_shift": "마음의 온도와 선택 기준이 달라지는 시기입니다.",
    "marriage_stability_opening": "결혼 이야기가 생활 약속으로 이어지는 시기입니다.",
    "marriage_condition_check": "주거 문제가 결혼 이야기에서 중요해지는 시기입니다.",
    "marriage_pressure": "결혼 결정을 서두르라는 압박이 강하게 드러나는 시기입니다.",
    "marriage_commitment_readiness": "결혼 약속을 구체적으로 준비하는 시기입니다.",
    "marriage_practical_planning": "주거와 재정 계획이 결혼의 중심이 되는 시기입니다.",
    "marriage_asset_condition_check": "돈의 기준과 지출 문제가 결혼 이야기의 핵심이 되는 시기입니다.",
    "marriage_decision_alignment": "결정 시점을 맞추는 시기입니다.",
    "marriage_timing_adjustment": "결혼 시기를 다시 점검하는 시기입니다.",
}


def _compact(text: str) -> str:
    return " ".join(str(text).split())


def _stem_label(stem: str) -> str:
    return STEM_LABELS.get(stem, stem)


def _branch_label(branch: str) -> str:
    return BRANCH_LABELS.get(branch, branch)


def _ten_god_label(ten_god: str) -> str:
    return TEN_GOD_LABELS.get(ten_god, ten_god)


def _element_label(element: str) -> str:
    return ELEMENT_LABELS.get(element, element)


def _domain_label(domain: Domain) -> str:
    return DOMAIN_LABELS.get(domain, domain)


def _join(items: list[str]) -> str:
    cleaned = [item for item in items if item]
    if len(cleaned) <= 1:
        return "".join(cleaned)
    return ", ".join(cleaned[:-1]) + ", " + cleaned[-1]


def _and_particle_text(text: str) -> str:
    return "과" if _has_jongseong(text) else "와"


def _and_join(items: list[str]) -> str:
    cleaned = [item for item in items if item]
    if len(cleaned) <= 1:
        return "".join(cleaned)
    result = cleaned[0]
    for item in cleaned[1:]:
        result += f"{_and_particle_text(result)} {item}"
    return result


def _unique_and_join(items: list[str]) -> str:
    return _and_join(list(dict.fromkeys(item for item in items if item)))


def _has_jongseong(text: str) -> bool:
    for char in reversed(str(text).strip()):
        if char in HANJA_HAS_JONGSEONG:
            return HANJA_HAS_JONGSEONG[char]
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28 != 0
    return False


def _subject_particle_text(text: str) -> str:
    return "이" if _has_jongseong(text) else "가"


def _topic_particle_text(text: str) -> str:
    return "은" if _has_jongseong(text) else "는"


def _object_particle_text(text: str) -> str:
    return "을" if _has_jongseong(text) else "를"


def _adverbial_particle_text(text: str) -> str:
    return "으로" if _has_jongseong(text) else "로"


def _adverbial_phrase_text(text: str) -> str:
    return f"{text}{_adverbial_particle_text(text)}"


def _period_subject_text(period_label: str) -> str:
    label = _compact(period_label)
    if re.fullmatch(r"\d{4}", label):
        return f"{label}년"
    return label


def _material_sentence(text: str) -> str:
    """Keep internal material prose usable as customer-facing evidence."""

    cleaned = _compact(text)
    replacements = (
        ("강하게 드러냅니다", "중심이 됩니다"),
        ("먼저 드러납니다", "먼저 보입니다"),
        ("바로 드러냅니다", "바로 보입니다"),
        ("문제로 드러납니다", "문제로 나타납니다"),
        ("능력으로 드러납니다", "실력을 인정받습니다"),
        ("성향으로 드러납니다", "성향으로 읽힙니다"),
        ("드러나는 재료입니다", "판단 근거입니다"),
        ("드러나는 방식", "보이는 방식"),
        ("드러냅니다", "뚜렷해집니다"),
        ("드러납니다", "나타납니다"),
        ("먼저 잡혀야 합니다", "먼저 자리를 잡아야 합니다"),
        ("먼저 잡아야 합니다", "먼저 세워야 합니다"),
        ("기준이 늦게 정해지면", "기준이 늦게 잡히면"),
        ("기준이 정해지면", "기준이 잡히면"),
        ("기준이 정해지고", "기준이 잡히고"),
        ("기준이 정해지며", "기준이 잡히며"),
        ("기준을 먼저 적는 것", "기준을 먼저 문서로 남기는 것"),
        ("모호한 조건", "모호한 상황"),
        ("조건에서는", "상황에서는"),
        ("조건에서", "상황에서"),
    )
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    return _compact(cleaned)


def _complete_sentence(text: str) -> str:
    cleaned = _material_sentence(text)
    if not cleaned:
        return ""
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."


def _top_element_labels(analysis: AnalysisResult, limit: int = 2) -> list[str]:
    scores = sorted(
        analysis.chart_structure.element_profile.scores.values(),
        key=lambda score: score.ratio,
        reverse=True,
    )
    return [_element_label(score.element) for score in scores[:limit]]


def _hidden_stem_entries(analysis: AnalysisResult, signal: PositionSignal) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for stem_key, weight in BRANCH_HIDDEN_STEMS.get(signal.branch_key, []):
        ten_god = ten_god_for(analysis.chart_structure.day_master_stem, stem_key)
        element = STEM_METADATA[stem_key]["element"]
        entries.append(
            {
                "stem": stem_key,
                "stem_label": _stem_label(stem_key),
                "element": element,
                "element_label": _element_label(element),
                "ten_god": ten_god,
                "ten_god_label": _ten_god_label(ten_god),
                "weight": weight,
                "protruded": stem_key in signal.protruded_hidden_stems,
            }
        )
    return entries


def _hidden_role_scene(domain: Domain, ten_god: str, *, protruded: bool) -> str:
    scene_map = PROTRUDED_TEN_GOD_DOMAIN_SCENES if protruded else HIDDEN_TEN_GOD_DOMAIN_SCENES
    return scene_map.get(domain, {}).get(ten_god, "")


def _hidden_element_balance_status(analysis: AnalysisResult, element: str) -> str:
    profile = analysis.chart_structure.element_profile
    score = profile.scores.get(element)
    pattern_status = _pattern_element_status(analysis, element)
    helpful = (
        element in profile.useful_elements
        or element in profile.climate_needs
        or pattern_status in {"supportive", "mixed"}
    )
    burdensome = (
        element in profile.caution_elements
        or bool(score and score.state == "dominant")
        or pattern_status in {"pressure", "mixed"}
    )
    if helpful and burdensome:
        return "mixed"
    if burdensome:
        return "pressure"
    if helpful:
        return "supportive"
    return "neutral"


def _pattern_element_status(analysis: AnalysisResult, element: str) -> str:
    pattern_profile = analysis.chart_structure.pattern_profile
    useful = {str(candidate.element) for candidate in pattern_profile.useful_element_candidates}
    caution = {str(candidate.element) for candidate in pattern_profile.caution_element_candidates}
    if element in useful and element in caution:
        return "mixed"
    if element in useful:
        return "supportive"
    if element in caution:
        return "pressure"
    return ""


def _hidden_element_balance_sentence(analysis: AnalysisResult, domain: Domain, entry: dict[str, Any]) -> str:
    element = str(entry.get("element") or "")
    role = str(entry.get("ten_god_label") or "")
    if not element or not role:
        return ""
    status = _hidden_element_balance_status(analysis, element)
    template = HIDDEN_ELEMENT_BALANCE_SENTENCES[domain].get(status, HIDDEN_ELEMENT_BALANCE_SENTENCES[domain]["neutral"])
    return _compact(
        template.format(
            element=_element_label(element),
            role=role,
            role_subject=f"{role}{_subject_particle_text(role)}",
        )
    )


def _hidden_pattern_role_sentence(analysis: AnalysisResult, domain: Domain, entry: dict[str, Any]) -> str:
    element = str(entry.get("element") or "")
    if not element:
        return ""
    status = _pattern_element_status(analysis, element)
    if not status:
        return ""
    group = _element_ten_god_group_key(analysis, element)
    group_label = TEN_GOD_GROUP_LABELS.get(group, "")
    element_label = _element_label(element)
    if not group_label:
        return ""
    support_text = RELATION_SUPPORT_ROLE_TEXT.get(domain, {}).get(group, "")
    pressure_text = RELATION_PRESSURE_ROLE_TEXT.get(domain, {}).get(group, "")
    if status == "supportive" and support_text:
        return f"지장간 속 {element_label} 기운에서는 필요한 {group_label}의 성질이 살아납니다. {support_text}"
    if status == "pressure" and pressure_text:
        return f"지장간 속 {element_label} 기운에서는 부담이 되는 {group_label}의 성질이 강해집니다. {pressure_text}"
    if status == "mixed":
        mixed_sentence = MIXED_PATTERN_ROLE_SENTENCES[domain].format(
            element=element_label,
            group=group_label,
        )
        hidden_mixed_sentence = mixed_sentence.replace(
            f"격국상 {element_label} 기운은",
            f"지장간 속 {element_label} 기운은 격국상",
            1,
        )
        parts = [
            hidden_mixed_sentence,
        ]
        if support_text:
            parts.append(support_text)
        if pressure_text:
            parts.append(pressure_text)
        return _compact(" ".join(parts))
    return ""


def _clean_reception_sentence(text: str) -> str:
    replacements = (
        (
            "책임이 들어오면 쉽게 넘기지 못하고, 사람 사이에서 지켜야 할 도리와 역할을 의식합니다.",
            "맡은 원칙을 쉽게 넘기지 못합니다.",
        ),
        (
            "돈과 약속이 작아 보여도 실제 생활에 직접 영향을 주는 기준으로 느낍니다.",
            "작은 돈과 약속도 생활에 닿은 기준으로 봅니다.",
        ),
        (
            "돈과 약속이 작아 보여도 실제 생활에 직접 영향을 주는 조건으로 느낍니다.",
            "작은 돈과 약속도 생활에 닿은 기준으로 봅니다.",
        ),
        (
            "돈과 약속이 작아 보여도 실제 생활을 움직이는 핵심 조건으로 체감합니다.",
            "작은 돈과 약속도 생활에 닿은 기준으로 봅니다.",
        ),
        (
            "돈과 약속이 작아 보여도 실제 생활을 움직이는 핵심 기준으로 체감합니다.",
            "작은 돈과 약속도 생활에 닿은 기준으로 봅니다.",
        ),
        (
            "혼자 결정하기보다 생각이 비슷한 사람에게 마음이 놓입니다.",
            "생각이 비슷한 사람에게 마음이 놓입니다.",
        ),
        (
            "내 손으로 해낼 수 있고, 결과가 눈에 보여야 편안합니다.",
            "결과가 눈에 보여야 마음이 놓입니다.",
        ),
        ("조건", "기준"),
        ("체감은", "생활에서는"),
        ("쪽으로 이어집니다", "문제로 나타납니다"),
        ("실제 체감은", "생활에서는"),
    )
    cleaned = str(text or "")
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    return _compact(cleaned)


def _first_sentence(text: str) -> str:
    sentences = [part.strip() for part in str(text or "").split(".") if part.strip()]
    if not sentences:
        return ""
    return _compact(f"{sentences[0]}.")


def _matching_hidden_reception_signal(analysis: AnalysisResult, position: str, stem_key: str):
    prefix = f"{position}:hidden"
    for signal in analysis.chart_structure.stem_reception_profile.hidden_stem_signals:
        if signal.target_stem == stem_key and str(signal.position).startswith(prefix):
            return signal
    return None


def _stem_reception_event_sentence(domain: Domain, reception_signal: Any, *, protruded: bool) -> str:
    day = _stem_label(str(reception_signal.day_stem))
    target = _stem_label(str(reception_signal.target_stem))
    role = _ten_god_label(str(reception_signal.target_ten_god))
    target_phrase = f"{target} {role}"
    felt_sentence = _first_sentence(_clean_reception_sentence(str(reception_signal.felt_experience)))
    domain_tail = {
        "money": "돈을 다룰 때 이 태도가 앞섭니다.",
        "career": "일을 맡을 때 이 태도가 앞섭니다.",
        "love": "관계에서는 이 반응이 앞섭니다.",
        "marriage": "결혼을 생각할 때 이 태도가 앞섭니다.",
    }.get(domain, "생활에서도 이 태도가 앞섭니다.")
    source = "지장간에서 천간에 투출된" if protruded else "지장간의"
    return _compact(
        f"{source} {target_phrase}의 영향으로 {day}일간인 당신은 {felt_sentence} "
        f"{domain_tail}"
    )


def _month_command_material(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    structure = analysis.chart_structure
    element_profile = structure.element_profile
    month_signal = structure.position_signals.get("month")
    month_branch = _branch_label(element_profile.month_branch)
    season = SEASON_LABELS.get(element_profile.season_label, element_profile.season_label)
    month_element = _element_label(month_signal.branch_element) if month_signal else ""
    ten_god = _ten_god_label(month_signal.branch_main_ten_god) if month_signal else ""
    sentence_parts = [
        DOMAIN_MONTH_LEAD[domain],
    ]
    if month_element and ten_god:
        sentence_parts.append(f"{season} {month_branch}월·{month_element} {ten_god} 성향이 뚜렷해서, {DOMAIN_MONTH_BASE[domain]}")
    else:
        sentence_parts.append(f"{season} {month_branch}월의 기운이 먼저 나타납니다.")
    return {
        "layer": "month_command",
        "label": "월령",
        "priority": "primary",
        "sentence": _material_sentence(" ".join(sentence_parts)),
        "basis_codes": [f"month_branch_{element_profile.month_branch}", f"month_command_{month_signal.branch_main_ten_god}" if month_signal else ""],
    }


def _month_governance_material(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    profile = analysis.chart_structure.month_governance_profile
    support_fits = sorted(
        profile.element_fits.values(),
        key=lambda item: (item.support_score - item.pressure_score, item.reality_score),
        reverse=True,
    )
    pressure_fits = sorted(
        profile.element_fits.values(),
        key=lambda item: (item.pressure_score - item.support_score, item.reality_score),
        reverse=True,
    )
    support = [fit for fit in support_fits if fit.support_score > fit.pressure_score][:2]
    pressure = [fit for fit in pressure_fits if fit.pressure_score > fit.support_score][:2]
    support_labels = [_element_label(fit.element) for fit in support]
    pressure_labels = [_element_label(fit.element) for fit in pressure]
    command = _ten_god_label(profile.month_command_ten_god) if profile.month_command_ten_god else ""
    month_branch = _branch_label(profile.month_branch)
    sentence_parts = [
        f"월지 {month_branch}을 기준으로 먼저 사주의 사회적 기준과 격국의 방향을 잡습니다."
    ]
    if command:
        sentence_parts.append(f"월령의 중심 십신은 {command}로 잡히며, 이 기준에 맞는 오행과 부담이 되는 오행을 나누어 보았습니다.")
    if support_labels:
        sentence_parts.append(f"이 명식에서 살려야 할 쪽은 {_join(support_labels)} 기운입니다.")
    if pressure_labels:
        sentence_parts.append(f"반대로 과해지면 판단을 흐리는 쪽은 {_join(pressure_labels)} 기운입니다.")
    return {
        "layer": "month_governance",
        "label": "월령 통제",
        "priority": "primary",
        "sentence": _material_sentence(" ".join(sentence_parts)),
        "month_branch": profile.month_branch,
        "month_command_ten_god": profile.month_command_ten_god,
        "regular_pattern": profile.regular_pattern,
        "support_elements": [fit.element for fit in support],
        "pressure_elements": [fit.element for fit in pressure],
        "basis_codes": list(profile.decision_notes)
        + [code for fit in support for code in fit.basis_codes[:3]]
        + [code for fit in pressure for code in fit.counter_signals[:3]],
    }


def _element_material(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    element_profile = analysis.chart_structure.element_profile
    top_labels = _top_element_labels(analysis, 3)
    useful = [_element_label(item) for item in element_profile.useful_elements[:2]]
    caution = [_element_label(item) for item in element_profile.caution_elements[:2]]
    sentences = []
    if top_labels:
        sentences.append(f"월령 보정 뒤에는 {_join(top_labels)} 기운이 뚜렷합니다.")
    if useful:
        sentences.append(DOMAIN_USEFUL_ELEMENT_EFFECT[domain].format(elements=_join(useful)))
    if caution:
        sentences.append(DOMAIN_CAUTION_ELEMENT_EFFECT[domain].format(elements=_join(caution)))
    sentences.append(DOMAIN_ELEMENT_EFFECT[domain])
    return {
        "layer": "element_distribution",
        "label": "오행 배합",
        "priority": "support",
        "sentence": _material_sentence(" ".join(sentences)),
        "basis_codes": [f"element_top_{label}" for label in top_labels],
    }


def _cycle_regulation_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    profile = analysis.chart_structure.cycle_regulation_profile or build_cycle_regulation_profile(analysis.chart_structure)
    domain_signals = [
        signal
        for signal in list(profile.get("signals") or [])
        if domain in list(signal.get("domain_links") or [])
    ]
    if not domain_signals:
        domain_signals = list(profile.get("signals") or [])[:1]
    signal_priority = {
        "wealth_generates_officer_controls_peer": 0,
        "wealth_controls_resource_releases_output": 1,
        "output_controls_officer_reduces_pressure": 2,
        "officer_generates_resource_protects_body": 3,
        "output_generates_wealth_then_officer": 4,
        "resource_controls_output_dosik": 5,
    }
    relation_priority = {
        "chain": 0,
        "generates": 1,
        "controls": 1,
        "element_bridge": 2,
        "branch_cycle": 2,
        "stem_combine": 2,
        "hidden_protrusion": 2,
        "visible_root": 2,
        "element_generates": 3,
        "element_controls": 3,
    }
    domain_signals = sorted(
        domain_signals,
        key=lambda signal: (
            signal_priority.get(str(signal.get("signal_id") or ""), 20),
            relation_priority.get(str(signal.get("relation") or ""), 9),
            0 if signal.get("polarity") == "support" else 1 if signal.get("polarity") == "mixed" else 2,
            -int(signal.get("reality_score", 0) or 0),
            -int(signal.get("score", 0) or 0),
        ),
    )
    chain_signals = [signal for signal in domain_signals if signal.get("relation") == "chain"]
    ten_god_signals = [signal for signal in domain_signals if signal.get("relation") in {"generates", "controls"}]
    bridge_signals = [signal for signal in domain_signals if signal.get("relation") == "element_bridge"]
    exception_signals = [signal for signal in domain_signals if signal.get("relation") == "element_exception"]
    branch_signals = [signal for signal in domain_signals if signal.get("relation") == "branch_cycle"]
    stem_combine_signals = [signal for signal in domain_signals if signal.get("relation") == "stem_combine"]
    rooting_signals = [
        signal for signal in domain_signals if signal.get("relation") in {"hidden_protrusion", "visible_root"}
    ]
    element_signals = [
        signal for signal in domain_signals if signal.get("relation") in {"element_generates", "element_controls"}
    ]
    selected_signals = list(
        {
            str(signal.get("signal_id") or ""): signal
            for signal in [
                *chain_signals[:6],
                *ten_god_signals[:2],
                *exception_signals[:2],
                *bridge_signals[:1],
                *branch_signals[:2],
                *stem_combine_signals[:2],
                *rooting_signals[:3],
                *[signal for signal in rooting_signals if signal.get("polarity") == "pressure"][:2],
                *element_signals[:2],
                *domain_signals[:3],
            ]
        }.values()
    )

    materials: list[dict[str, Any]] = []
    for signal in selected_signals[:16]:
        status = str(signal.get("status") or "")
        score = int(signal.get("score") or 0)
        priority = (
            "primary"
            if status in {"regulates_pressure", "regulates_with_cost", "feeds_useful_force", "connects_function"} and score >= 70
            else "support"
        )
        materials.append(
            {
                "layer": "cycle_regulation",
                "label": "상생상극 조절",
                "priority": priority,
                "signal_id": str(signal.get("signal_id") or ""),
                "relation": str(signal.get("relation") or ""),
                "status": status,
                "cycle_judgment": str(signal.get("cycle_judgment") or ""),
                "cycle_judgment_label": str(signal.get("cycle_judgment_label") or ""),
                "month_command_verdict": str(signal.get("month_command_verdict") or ""),
                "month_command_verdict_label": str(signal.get("month_command_verdict_label") or ""),
                "decision_reason": str(signal.get("decision_reason") or ""),
                "polarity": str(signal.get("polarity") or ""),
                "classical_name": str(signal.get("classical_name") or ""),
                "classical_theory": str(signal.get("classical_theory") or ""),
                "score": score,
                "source_group": str(signal.get("source_group") or ""),
                "target_group": str(signal.get("target_group") or ""),
                "groups": list(signal.get("groups") or []),
                "domain_links": list(signal.get("domain_links") or []),
                "sentence": _material_sentence(str(signal.get("sentence") or "")),
                "source_context": dict(signal.get("source_context") or {}),
                "target_context": dict(signal.get("target_context") or {}),
                "group_contexts": list(signal.get("group_contexts") or []),
                "governance_context": dict(signal.get("governance_context") or {}),
                "pattern_cycle_context": dict(signal.get("pattern_cycle_context") or {}),
                "condition_context": dict(signal.get("condition_context") or {}),
                "branch_reality_context": dict(signal.get("branch_reality_context") or {}),
                "month_cycle_fit_context": dict(signal.get("month_cycle_fit_context") or {}),
                "basis_codes": list(signal.get("basis_codes") or []),
            }
        )
    return materials


def _cycle_matrix_scope_rank(scope: str) -> int:
    return {
        "active_support": 0,
        "active_mixed": 1,
        "active_pressure": 2,
        "latent_reference": 3,
        "trace_reference": 4,
        "reference": 5,
        "not_present": 9,
    }.get(scope, 8)


def _cycle_principle_matrix_context(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    profile = analysis.chart_structure.cycle_regulation_profile or build_cycle_regulation_profile(analysis.chart_structure)
    matrix = dict(profile.get("principle_matrix") or {})
    role_edges = [
        edge
        for edge in list(matrix.get("role_edges") or [])
        if isinstance(edge, dict) and domain in list(edge.get("domain_links") or [])
    ]
    element_edges = [
        edge
        for edge in list(matrix.get("element_edges") or [])
        if isinstance(edge, dict) and domain in list(edge.get("domain_links") or [])
    ]
    branch_relations = [
        item
        for item in list(matrix.get("branch_relations") or [])
        if isinstance(item, dict) and domain in list(item.get("domain_links") or [])
    ]

    role_edges.sort(
        key=lambda edge: (
            _cycle_matrix_scope_rank(str(edge.get("scope") or "")),
            0 if edge.get("touches_month_command") else 1,
            -abs(int(edge.get("net_score") or 0)),
            str(edge.get("edge_key") or ""),
        )
    )
    element_edges.sort(
        key=lambda edge: (
            _cycle_matrix_scope_rank(str(edge.get("scope") or "")),
            -abs(int(edge.get("net_score") or 0)),
            str(edge.get("edge_key") or ""),
        )
    )
    branch_relations.sort(
        key=lambda item: (
            0 if "month" in list(item.get("positions") or []) else 1,
            -int(item.get("useful_score") or 0) - int(item.get("pressure_score") or 0),
            str(item.get("relation_type") or ""),
        )
    )

    primary_role_edges = role_edges[:5]
    latent_role_edges = [
        edge
        for edge in role_edges
        if str(edge.get("scope") or "") in {"latent_reference", "trace_reference"}
    ][:5]
    active_role_edges = [
        edge
        for edge in role_edges
        if str(edge.get("scope") or "").startswith("active")
    ][:5]

    return {
        "version": str(matrix.get("version") or ""),
        "domain": domain,
        "month_anchor": dict(matrix.get("month_anchor") or {}),
        "coverage": dict(matrix.get("coverage") or {}),
        "primary_role_edges": primary_role_edges,
        "active_role_edges": active_role_edges,
        "latent_role_edges": latent_role_edges,
        "primary_element_edges": element_edges[:5],
        "branch_relations": branch_relations[:5],
        "source_reality": dict(matrix.get("source_reality") or {}),
        "primary_classical_names": list(
            dict.fromkeys(
                str(edge.get("classical_name") or "")
                for edge in primary_role_edges + element_edges[:3]
                if str(edge.get("classical_name") or "")
            )
        ),
        "domain_projections": [
            str(dict(edge.get("domain_projection") or {}).get(domain) or "")
            for edge in primary_role_edges
            if dict(edge.get("domain_projection") or {}).get(domain)
        ],
    }


def _cycle_signal_domain_judgment(signal_id: str, domain: Domain, material: dict[str, Any]) -> dict[str, str]:
    configured = CYCLE_SIGNAL_DOMAIN_JUDGMENTS.get(signal_id, {}).get(domain)
    if configured:
        return dict(configured)

    relation = str(material.get("relation") or "")
    source = TEN_GOD_GROUP_LABELS.get(str(material.get("source_group") or ""), str(material.get("source_group") or ""))
    target = TEN_GOD_GROUP_LABELS.get(str(material.get("target_group") or ""), str(material.get("target_group") or ""))
    classical = str(material.get("classical_name") or "")
    if relation == "generates":
        principle = f"{source}이 {target}을 생하는 흐름입니다."
        adjudication = f"{source}의 작용이 {target}의 역할을 키웁니다."
    elif relation == "controls":
        principle = f"{source}이 {target}을 극하는 흐름입니다."
        adjudication = f"{source}의 작용이 {target}의 과함을 누르거나, 필요하면 부담으로 작용합니다."
    elif relation == "branch_cycle":
        principle = "지지의 합충형파해가 오행을 움직이는 흐름입니다."
        adjudication = str(material.get("sentence") or "지지 관계가 원국의 생극 작용을 현실 사건으로 끌어냅니다.")
    elif relation == "stem_combine":
        principle = "천간합이 드러난 기운을 묶거나 다른 오행으로 돌리는 흐름입니다."
        adjudication = str(material.get("sentence") or "천간의 결합이 원래 생극 작용의 방향을 바꿉니다.")
    elif relation == "element_bridge":
        principle = "상극을 중간 오행이 이어 주는 통관 흐름입니다."
        adjudication = "충돌하던 기운이 다른 오행을 거치며 실제 선택지로 정리됩니다."
    elif relation == "element_exception":
        principle = "과생, 반극, 설기 과다처럼 일반 생극이 뒤집히는 흐름입니다."
        adjudication = "겉으로는 도움이 되는 기운도 실제로는 소모나 부담으로 바뀔 수 있습니다."
    elif classical:
        principle = f"{classical}에 해당하는 생극 흐름입니다."
        adjudication = str(material.get("sentence") or "생극 관계가 이 영역의 판단을 조정합니다.")
    else:
        principle = "상생상극의 연결로 판단하는 흐름입니다."
        adjudication = str(material.get("sentence") or "생극 관계가 이 영역의 판단을 조정합니다.")

    domain_dimension = {
        "money": "재물 조절력",
        "career": "직업 조절력",
        "love": "관계 조절력",
        "marriage": "생활 조절력",
    }.get(domain, "생극 조절력")
    return {
        "dimension": domain_dimension,
        "principle": _material_sentence(principle),
        "adjudication": _material_sentence(adjudication),
        "caution": _material_sentence(str(material.get("decision_reason") or "")),
    }


def _cycle_flow_codes_for_packet(packet: EventPacket, signal_id: str) -> dict[str, Any]:
    return _cycle_flow_contexts_for_packet(packet, [signal_id]).get(
        signal_id,
        _empty_cycle_flow_context(),
    )


def _empty_cycle_flow_context() -> dict[str, Any]:
    return {
        "flow_triggered": False,
        "trigger_grades": [],
        "source_hits": [],
        "relation_hits": [],
        "branch_grades": [],
        "edge_contexts": [],
        "basis_codes": [],
        "counter_signals": [],
    }


def _cycle_flow_contexts_for_packet(
    packet: EventPacket,
    signal_ids: list[str],
) -> dict[str, dict[str, Any]]:
    """Index every cycle-flow code once for all cycle signals on a packet."""

    ordered_signal_ids = sorted(
        dict.fromkeys(str(signal_id) for signal_id in signal_ids if signal_id),
        key=len,
        reverse=True,
    )
    contexts = {signal_id: _empty_cycle_flow_context() for signal_id in ordered_signal_ids}
    seen_values = {
        signal_id: {
            "trigger": set(),
            "source": set(),
            "relation": set(),
            "branch": set(),
            "edge": set(),
        }
        for signal_id in ordered_signal_ids
    }
    domain = packet.domain
    kind_prefixes = (
        ("trigger", f"cycle_flow_trigger_{domain}_"),
        ("source", f"cycle_flow_source_{domain}_"),
        ("relation", f"cycle_flow_relation_{domain}_"),
        ("branch", f"cycle_flow_branch_reality_{domain}_"),
        ("edge", f"cycle_flow_edge_{domain}_"),
    )
    basis = [str(code) for code in list(packet.basis_codes or [])]
    counters = [str(code) for code in list(packet.counter_signals or [])]
    for source_name, raw_code in [
        *[("basis_codes", code) for code in basis],
        *[("counter_signals", code) for code in counters],
    ]:
        code = raw_code[:-5] if raw_code.endswith("_cost") else raw_code
        kind = ""
        remainder = ""
        for candidate_kind, prefix in kind_prefixes:
            if code.startswith(prefix):
                kind = candidate_kind
                remainder = code[len(prefix):]
                break
        if not kind:
            continue
        signal_id = next(
            (
                candidate
                for candidate in ordered_signal_ids
                if remainder.startswith(f"{candidate}_")
            ),
            "",
        )
        if not signal_id:
            continue
        suffix = remainder[len(signal_id) + 1:]
        if not suffix:
            continue
        context = contexts[signal_id]
        if raw_code not in context[source_name]:
            context[source_name].append(raw_code)
        seen = seen_values[signal_id]
        if kind == "edge":
            parts = suffix.split("_")
            if len(parts) < 4:
                continue
            source_group, edge_relation, target_group = parts[0], parts[1], parts[2]
            grade = "_".join(parts[3:])
            marker = (source_group, edge_relation, target_group, grade)
            if marker in seen["edge"]:
                continue
            seen["edge"].add(marker)
            context["edge_contexts"].append(
                {
                    "source_group": source_group,
                    "relation": edge_relation,
                    "target_group": target_group,
                    "grade": grade,
                    "active": grade in {"edge_flow_relation_triggers", "edge_flow_both_roles"},
                    "soft_active": grade == "edge_flow_relation_touches_role",
                }
            )
            continue
        target_key = {
            "trigger": "trigger_grades",
            "source": "source_hits",
            "relation": "relation_hits",
            "branch": "branch_grades",
        }[kind]
        if suffix not in seen[kind]:
            seen[kind].add(suffix)
            context[target_key].append(suffix)

    for context in contexts.values():
        context["flow_triggered"] = bool(
            context["trigger_grades"]
            or context["source_hits"]
            or context["relation_hits"]
            or any(edge.get("active") for edge in context["edge_contexts"])
        )
    # Preserve the former audit contract exactly. These ledgers intentionally
    # include every cycle-flow code that names the signal, not only the four
    # score-bearing prefix families indexed above.
    for signal_id, context in contexts.items():
        context["basis_codes"] = [
            code
            for code in basis
            if signal_id in code and code.startswith("cycle_flow_")
        ]
        context["counter_signals"] = [
            code
            for code in counters
            if signal_id in code and code.startswith("cycle_flow_")
        ]
    return contexts


def _cycle_reality_grade_score(grade: str) -> int:
    return {
        "month_branch_visible": 16,
        "month_visible": 15,
        "month_hidden_protruded": 14,
        "month_rooted": 13,
        "branch_dominant": 12,
        "hidden_to_visible": 10,
        "rooted_visible": 10,
        "branch_rooted": 8,
        "visible": 7,
        "stem_visible_only": 5,
        "rooted_or_hidden": 5,
        "weak_reality": 0,
        "weak": 0,
    }.get(grade, 0)


def _cycle_adjudication_score(material: dict[str, Any], flow_context: dict[str, Any]) -> int:
    base_score = int(material.get("score") or 0)
    score = int(round(base_score * 0.68))
    pattern = dict(material.get("pattern_cycle_context") or {})
    branch = dict(material.get("branch_reality_context") or {})
    condition = dict(material.get("condition_context") or {})
    governance = dict(material.get("governance_context") or {})
    month_cycle_fit = dict(material.get("month_cycle_fit_context") or {})

    score += min(9, int(round(float(pattern.get("support_strength") or 0) * 1.6)))
    score += min(5, int(round(float(pattern.get("caution_strength") or 0) * 0.8)))
    score += int(round(_cycle_reality_grade_score(str(pattern.get("reality_grade") or "")) * 0.45))
    score += int(round(_cycle_reality_grade_score(str(branch.get("grade") or "")) * 0.55))
    month_fit_verdict = str(month_cycle_fit.get("verdict") or "")
    if month_fit_verdict == "month_cycle_needed":
        score += 7
    elif month_fit_verdict == "month_cycle_needed_with_cost":
        score += 4
    elif month_fit_verdict == "month_cycle_pressure_with_use":
        score += 2
    elif month_fit_verdict == "month_cycle_burdens_month":
        score -= 5
    elif month_fit_verdict == "month_cycle_auxiliary_use":
        score += 1
    elif month_fit_verdict == "month_cycle_auxiliary_pressure":
        score -= 2
    if governance.get("touches_month_command"):
        score += 5
    if governance.get("touches_useful"):
        score += 3
    if flow_context.get("flow_triggered"):
        score += 4
    active_edge_count = sum(1 for edge in list(flow_context.get("edge_contexts") or []) if edge.get("active"))
    soft_edge_count = sum(1 for edge in list(flow_context.get("edge_contexts") or []) if edge.get("soft_active"))
    score += min(4, active_edge_count * 2 + soft_edge_count)
    if flow_context.get("relation_hits"):
        score += 2
    if condition.get("pressure_tags"):
        score -= min(10, len(condition.get("pressure_tags") or []) * 2)
    return max(0, min(99, score))


def _cycle_adjudication_direction(material: dict[str, Any]) -> str:
    polarity = str(material.get("polarity") or "")
    pattern = dict(material.get("pattern_cycle_context") or {})
    condition = dict(material.get("condition_context") or {})
    if polarity == "support":
        if pattern.get("caution_rule_keys") or condition.get("pressure_tags"):
            return "support_with_cost"
        return "support"
    if polarity == "pressure":
        return "pressure"
    return "mixed"


def _cycle_product_facet_tone(item: dict[str, Any]) -> str:
    direction = str(item.get("direction") or "")
    month_fit = str(item.get("month_cycle_fit_verdict") or "")
    if direction == "pressure" or month_fit in {"month_cycle_burdens_month", "month_cycle_auxiliary_pressure"}:
        return "caution"
    if direction == "support_with_cost" or month_fit in {"month_cycle_needed_with_cost", "month_cycle_pressure_with_use"}:
        return "mixed"
    if direction == "support":
        return "strength"
    return "mixed"


def _cycle_product_facet_definition(domain: Domain, item: dict[str, Any]) -> dict[str, str]:
    signal_id = str(item.get("signal_id") or "")
    configured = CYCLE_PRODUCT_FACET_DEFINITIONS.get(signal_id, {}).get(domain)
    if configured:
        return dict(configured)
    relation = str(item.get("relation") or "")
    fallback = CYCLE_RELATION_FACET_DEFINITIONS.get(relation, {}).get(domain)
    if fallback:
        return dict(fallback)
    dimension = str(item.get("dimension") or "")
    if dimension:
        return {
            "label": dimension,
            "meaning": f"{dimension}을 조정하는 생극 작용",
            "assertion": f"{dimension}이 이 영역의 판정을 조정합니다.",
        }
    return {
        "label": "생극 조절력",
        "meaning": "상생상극이 영역 판단을 조정하는 작용",
        "assertion": "상생상극의 작용이 이 영역의 판정을 조정합니다.",
    }


def _cycle_product_facets(domain: Domain, selected_items: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    facets: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for item in selected_items:
        definition = _cycle_product_facet_definition(domain, item)
        label = _compact(str(definition.get("label") or ""))
        if not label or label in seen_labels:
            continue
        seen_labels.add(label)
        classical_name = str(item.get("classical_name") or "")
        principle = str(item.get("principle") or "")
        basis_parts = [part for part in (classical_name, principle) if part]
        facets.append(
            {
                "key": str(item.get("signal_id") or item.get("relation") or label),
                "label": label,
                "meaning": _material_sentence(str(definition.get("meaning") or "")),
                "assertion": _material_sentence(str(definition.get("assertion") or "")),
                "tone": _cycle_product_facet_tone(item),
                "score": int(item.get("score") or 0),
                "selection_score": int(item.get("selection_score") or 0),
                "source_signal_id": str(item.get("signal_id") or ""),
                "relation": str(item.get("relation") or ""),
                "classical_name": classical_name,
                "month_cycle_fit_verdict": str(item.get("month_cycle_fit_verdict") or ""),
                "branch_reality_grade": str(item.get("branch_reality_grade") or ""),
                "basis": " / ".join(dict.fromkeys(basis_parts)),
            }
        )
        if len(facets) >= limit:
            break
    return facets


def _merge_flow_and_month_edges(
    flow_context: dict[str, Any],
    month_cycle_fit_context: dict[str, Any],
) -> list[dict[str, Any]]:
    month_edges = [
        edge
        for edge in list(month_cycle_fit_context.get("edge_contexts") or [])
        if isinstance(edge, dict)
    ]
    month_by_key = {
        (
            str(edge.get("source_group") or ""),
            str(edge.get("relation") or ""),
            str(edge.get("target_group") or ""),
        ): edge
        for edge in month_edges
    }
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in list(flow_context.get("edge_contexts") or []):
        if not isinstance(edge, dict):
            continue
        key = (
            str(edge.get("source_group") or ""),
            str(edge.get("relation") or ""),
            str(edge.get("target_group") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        month_edge = month_by_key.get(key, {})
        merged.append(
            {
                **dict(edge),
                "month_fit_verdict": str(month_edge.get("verdict") or ""),
                "month_fit_net": int(month_edge.get("net_score") or 0),
                "month_fit_reasons": list(month_edge.get("reasons") or []),
                "month_fit_caution_reasons": list(month_edge.get("caution_reasons") or []),
            }
        )
    return merged


def _flow_edge_fit_score(flow_edges: list[dict[str, Any]]) -> int:
    score = 0
    for edge in flow_edges[:4]:
        active_factor = 2 if edge.get("active") else 1 if edge.get("soft_active") else 0
        if not active_factor:
            continue
        fit = str(edge.get("month_fit_verdict") or "")
        if fit in {"edge_needed", "edge_useful"}:
            score += 2 * active_factor
        elif fit == "edge_useful_with_cost":
            score += active_factor
        elif fit == "edge_pressure_with_use":
            score -= active_factor
        elif fit in {"edge_burdens_month", "edge_pressure"}:
            score -= 2 * active_factor
    return max(-6, min(6, score))


def _month_cycle_fit_selection_bonus(verdict: str) -> int:
    return {
        "month_cycle_needed": 6,
        "month_cycle_needed_with_cost": 1,
        "month_cycle_auxiliary_use": -2,
        "month_cycle_mixed": -3,
        "month_cycle_pressure_with_use": -5,
        "month_cycle_auxiliary_pressure": -6,
        "month_cycle_burdens_month": -8,
    }.get(verdict, 0)


def _build_cycle_adjudication_context(
    domain: Domain,
    materials: list[dict[str, Any]],
    packet: EventPacket,
) -> dict[str, Any]:
    cycle_materials = [
        material
        for material in materials
        if material.get("layer") == "cycle_regulation" and str(material.get("signal_id") or "")
    ]
    items: list[dict[str, Any]] = []
    flow_contexts = _cycle_flow_contexts_for_packet(
        packet,
        [str(material.get("signal_id") or "") for material in cycle_materials],
    )
    for material in cycle_materials:
        signal_id = str(material.get("signal_id") or "")
        judgment = _cycle_signal_domain_judgment(signal_id, domain, material)
        configured_judgment = signal_id in CYCLE_SIGNAL_DOMAIN_JUDGMENTS and domain in CYCLE_SIGNAL_DOMAIN_JUDGMENTS[signal_id]
        flow_context = flow_contexts.get(signal_id, _empty_cycle_flow_context())
        pattern_context = dict(material.get("pattern_cycle_context") or {})
        branch_context = dict(material.get("branch_reality_context") or {})
        condition_context = dict(material.get("condition_context") or {})
        governance_context = dict(material.get("governance_context") or {})
        month_cycle_fit_context = dict(material.get("month_cycle_fit_context") or {})
        flow_edges = _merge_flow_and_month_edges(flow_context, month_cycle_fit_context)
        direction = _cycle_adjudication_direction(material)
        score = max(0, min(99, _cycle_adjudication_score(material, flow_context) + _flow_edge_fit_score(flow_edges)))
        priority_rank = CYCLE_DOMAIN_SIGNAL_PRIORITY.get(domain, {}).get(signal_id, 50)
        month_fit_verdict = str(month_cycle_fit_context.get("verdict") or "")
        selection_score = (
            score
            + max(0, 12 - priority_rank * 3)
            + _month_cycle_fit_selection_bonus(month_fit_verdict)
        )
        items.append(
            {
                "signal_id": signal_id,
                "relation": str(material.get("relation") or ""),
                "configured_judgment": configured_judgment,
                "priority_rank": priority_rank,
                "selection_score": selection_score,
                "dimension": judgment["dimension"],
                "principle": judgment["principle"],
                "adjudication": judgment["adjudication"],
                "caution": judgment["caution"],
                "direction": direction,
                "polarity": str(material.get("polarity") or ""),
                "status": str(material.get("status") or ""),
                "cycle_judgment": str(material.get("cycle_judgment") or ""),
                "month_command_verdict": str(material.get("month_command_verdict") or ""),
                "score": score,
                "base_score": int(material.get("score") or 0),
                "source_group": str(material.get("source_group") or ""),
                "target_group": str(material.get("target_group") or ""),
                "groups": list(material.get("groups") or []),
                "classical_name": str(material.get("classical_name") or ""),
                "pattern_verdict": str(pattern_context.get("verdict") or ""),
                "pattern_support_strength": float(pattern_context.get("support_strength") or 0.0),
                "pattern_caution_strength": float(pattern_context.get("caution_strength") or 0.0),
                "pattern_reality_grade": str(pattern_context.get("reality_grade") or ""),
                "month_cycle_fit_verdict": month_fit_verdict,
                "month_cycle_fit_net": int(month_cycle_fit_context.get("net_score") or 0),
                "month_cycle_fit_source": str(month_cycle_fit_context.get("source_group") or ""),
                "month_cycle_fit_target": str(month_cycle_fit_context.get("target_group") or ""),
                "month_cycle_fit_primary_anchor": bool(month_cycle_fit_context.get("primary_anchor")),
                "month_cycle_fit_costly_edge_count": int(month_cycle_fit_context.get("costly_edge_count") or 0),
                "month_cycle_fit_burden_edge_count": int(month_cycle_fit_context.get("burden_edge_count") or 0),
                "month_cycle_fit_latent_edge_count": int(month_cycle_fit_context.get("latent_edge_count") or 0),
                "month_cycle_fit_edge_verdicts": list(month_cycle_fit_context.get("edge_verdicts") or []),
                "month_cycle_fit_edges": list(month_cycle_fit_context.get("edge_contexts") or []),
                "month_cycle_fit_reasons": list(month_cycle_fit_context.get("reasons") or []),
                "month_cycle_fit_caution_reasons": list(month_cycle_fit_context.get("caution_reasons") or []),
                "branch_reality_grade": str(branch_context.get("grade") or ""),
                "branch_reality_ratio": float(branch_context.get("branch_ratio") or 0.0),
                "branch_reality_positions": list(branch_context.get("top_positions") or []),
                "flow_triggered": bool(flow_context.get("flow_triggered")),
                "flow_trigger_grades": list(flow_context.get("trigger_grades") or []),
                "flow_source_hits": list(flow_context.get("source_hits") or []),
                "flow_relation_hits": list(flow_context.get("relation_hits") or []),
                "flow_edge_contexts": flow_edges,
                "support_tags": list(condition_context.get("support_tags") or []),
                "pressure_tags": list(condition_context.get("pressure_tags") or []),
                "touches_month_command": bool(governance_context.get("touches_month_command")),
                "touches_useful": bool(governance_context.get("touches_useful")),
                "touches_caution": bool(governance_context.get("touches_caution")),
                "basis_codes": list(dict.fromkeys(list(material.get("basis_codes") or []) + list(flow_context.get("basis_codes") or []))),
                "counter_signals": list(flow_context.get("counter_signals") or []),
            }
        )

    items.sort(
        key=lambda item: (
            0 if item["configured_judgment"] else 1,
            -int(item["selection_score"]),
            int(item["priority_rank"]),
            {"chain": 0, "generates": 1, "controls": 1, "element_bridge": 2, "element_exception": 3, "branch_cycle": 4}.get(
                next((str(material.get("relation") or "") for material in cycle_materials if material.get("signal_id") == item["signal_id"]), ""),
                5,
            ),
            0 if item["direction"] in {"support", "support_with_cost"} else 1 if item["direction"] == "mixed" else 2,
            -int(item["score"]),
            str(item["signal_id"]),
        )
    )
    selected = items[:5]
    support_count = sum(1 for item in items if item["direction"] in {"support", "support_with_cost"})
    pressure_count = sum(1 for item in items if item["direction"] == "pressure")
    mixed_count = sum(1 for item in items if item["direction"] == "mixed")
    if support_count > pressure_count + mixed_count:
        dominant = "support"
    elif pressure_count > support_count:
        dominant = "pressure"
    else:
        dominant = "mixed"
    product_facets = _cycle_product_facets(domain, selected)
    return {
        "version": "cycle_adjudication_v1",
        "domain": domain,
        "dominant_direction": dominant,
        "support_count": support_count,
        "pressure_count": pressure_count,
        "mixed_count": mixed_count,
        "flow_triggered_count": sum(1 for item in items if item["flow_triggered"]),
        "primary_dimensions": list(dict.fromkeys(str(item["dimension"]) for item in selected if item.get("dimension"))),
        "primary_cycle": selected[0] if selected else {},
        "primary_product_facet": product_facets[0] if product_facets else {},
        "product_facets": product_facets,
        "items": selected,
    }


def _element_ten_god_group_label(analysis: AnalysisResult, element: str) -> str:
    group = _element_ten_god_group_key(analysis, element)
    return TEN_GOD_GROUP_LABELS.get(group, "")


def _element_ten_god_group_key(analysis: AnalysisResult, element: str) -> str:
    day = analysis.chart_structure.day_master_element
    if element == day:
        return "peer"
    if ELEMENT_GENERATES[day] == element:
        return "output"
    if ELEMENT_CONTROLS[day] == element:
        return "wealth"
    if ELEMENT_CONTROLS[element] == day:
        return "officer"
    if ELEMENT_GENERATES[element] == day:
        return "resource"
    return ""


def _candidate_pattern_reason_role(candidate: Any, domain: Domain) -> str:
    for code in reversed(list(getattr(candidate, "basis_codes", []) or [])):
        role_text = PATTERN_REASON_ROLE_TEXT.get(str(code))
        if role_text:
            return str(role_text.get(domain) or "")
    return ""


def _candidate_intro_sentences(candidates: list[Any], *, need_type: str) -> list[str]:
    if not candidates:
        return []
    labels = [_element_label(str(item.element)) for item in candidates]
    if need_type == "useful":
        sentences = [f"격국상 필요한 기운은 {labels[0]}입니다."]
        sentences.extend(f"{label} 기운도 보조 기운입니다." for label in labels[1:])
        return sentences
    sentences = [f"격국상 부담이 되는 기운은 {labels[0]}입니다."]
    sentences.extend(f"{label} 기운도 부담을 만듭니다." for label in labels[1:])
    return sentences


def _candidate_element_role_sentences(
    analysis: AnalysisResult,
    candidates: list[Any],
    role_texts: dict[str, Any],
    domain: Domain,
) -> list[str]:
    sentences: list[str] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        element = str(candidate.element)
        role_key = str(candidate.role)
        key = (element, role_key)
        if key in seen:
            continue
        seen.add(key)
        element_label = _element_label(element)
        group_label = _element_ten_god_group_label(analysis, element)
        role_value = role_texts.get(role_key, "사주의 균형을 조정합니다")
        if isinstance(role_value, dict):
            role = str(role_value.get(domain) or role_value.get("default") or "사주의 균형을 조정합니다")
        else:
            role = str(role_value)
        role = _candidate_pattern_reason_role(candidate, domain) or role
        if group_label:
            sentences.append(f"{group_label}인 {element_label} 기운이 이 판단의 중심입니다.")
        if "월령에서는" in role or "월령에서" in role or role.startswith("인성이 과하면"):
            sentences.append(_complete_sentence(role))
        else:
            sentences.append(f"{element_label} 기운은 {role}.")
    return sentences


def _candidate_role_priority(candidate: Any) -> tuple[int, int]:
    role = str(getattr(candidate, "role", ""))
    score = int(getattr(candidate, "score", 0) or 0)
    if role.startswith("regular_pattern_"):
        return (0, -score)
    if role in {"climate_medicine", "illness_medicine"}:
        return (1, -score)
    if "support" in role or "pressure" in role:
        return (2, -score)
    return (3, -score)


def _merge_candidates_for_element(candidates: list[Any], element: str) -> Any:
    element_candidates = [candidate for candidate in candidates if str(getattr(candidate, "element", "")) == element]
    if not element_candidates:
        raise ValueError(f"No candidates for element: {element}")
    role_source = sorted(element_candidates, key=_candidate_role_priority)[0]
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


def _select_pattern_candidates(
    candidates: list[Any],
    *,
    limit: int,
    exclude_elements: set[str] | None = None,
) -> list[Any]:
    if limit <= 0:
        return []

    blocked_elements = exclude_elements or set()
    available_candidates = [
        candidate
        for candidate in candidates
        if str(getattr(candidate, "element", "")) and str(getattr(candidate, "element", "")) not in blocked_elements
    ]
    element_order: dict[str, int] = {}
    for index, candidate in enumerate(available_candidates):
        element = str(getattr(candidate, "element", ""))
        element_order.setdefault(element, index)

    merged_candidates = [
        _merge_candidates_for_element(available_candidates, element)
        for element in element_order
    ]
    merged_candidates.sort(
        key=lambda candidate: (
            *_candidate_role_priority(candidate),
            element_order.get(str(getattr(candidate, "element", "")), 999),
        )
    )
    return merged_candidates[:limit]


def _pattern_subject_sentence(pattern_label: str) -> str:
    label = _compact(pattern_label)
    if label.endswith("이 필요한 구조") or label.endswith("가 필요한 구조"):
        core = label[: -len(" 필요한 구조")]
        return f"당신의 사주는 {core} 필요합니다."
    if label.endswith("기운이 함께 섞인 구조"):
        return "당신의 사주는 여러 기운이 함께 섞여 있습니다."
    if label.endswith("강하게 몰린 구조"):
        core = label[: -len(" 구조")]
        return f"당신의 사주는 {core} 상태입니다."
    if label.endswith(" 구조"):
        core = label[:-3]
        return f"당신의 사주에서는 {core} 힘이 강합니다."
    return f"당신의 사주는 {label} 힘이 강합니다."


def _pattern_direction_sentences(profile: Any, domain: Domain, pattern_label: str, regular_label: str) -> list[str]:
    sentences: list[str] = []
    month_direction = MONTH_TEN_GOD_DOMAIN_DIRECTIONS.get(profile.month_command_ten_god, {}).get(domain, "")
    if month_direction:
        sentences.append(month_direction)
    elif regular_label and regular_label != pattern_label:
        sentences.append(f"월령에서는 {regular_label} 성향도 함께 강해집니다.")

    primary_direction = PRIMARY_PATTERN_DOMAIN_DIRECTIONS.get(profile.primary_pattern, {}).get(domain, "")
    if primary_direction:
        sentences.append(primary_direction)
    elif regular_label and regular_label != pattern_label and not month_direction:
        sentences.append(f"{regular_label}의 성질도 이 영역의 판단에 반영됩니다.")
    return sentences


def _flow_pattern_activation_sentences(
    analysis: AnalysisResult,
    domain: Domain,
    packet: EventPacket | None,
    useful: list[Any],
    caution: list[Any],
) -> list[str]:
    if packet is None:
        return []
    flow = _matching_flow(analysis, packet)
    if flow is None:
        return []
    useful_elements = {str(item.element) for item in useful}
    caution_elements = {str(item.element) for item in caution}
    sentences: list[str] = []

    useful_active = [element for element in flow.activated_elements if element in useful_elements]
    caution_active = [
        element
        for element in flow.activated_elements
        if element in caution_elements and element not in useful_elements
    ]
    if useful_active:
        label = _element_label(useful_active[0])
        sentences.append(f"이 시기에는 필요한 {label} 기운이 {_domain_label(domain)}에서 먼저 힘을 냅니다.")
        sentences.append(PATTERN_DOMAIN_RESULTS[domain]["support"].replace("이 기운", f"{label} 기운"))
    if caution_active:
        label = _element_label(caution_active[0])
        sentences.append(f"이 시기에는 부담이 되는 {label} 기운이 {_domain_label(domain)}에서 먼저 무거워집니다.")
        sentences.append(PATTERN_DOMAIN_RESULTS[domain]["pressure"].replace("이 기운", f"{label} 기운"))

    for relation in flow.branch_interactions:
        polarity = branch_relation_polarity(
            analysis.chart_structure.element_profile,
            relation,
            analysis.chart_structure.pattern_profile,
        )
        branches = "".join(_branch_label(branch) for branch in relation.branches)
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        relation_subject = f"{branches} {relation_label}" if branches else relation_label
        support_elements = [element for element in polarity.support_elements if element in useful_elements]
        pressure_elements = [element for element in polarity.pressure_elements if element in caution_elements]
        if support_elements:
            label = _element_label(support_elements[0])
            sentences.append(f"{relation_subject} 관계가 격국상 필요한 {label} 기운을 {_domain_label(domain)} 쪽으로 끌어냅니다.")
            break
        if pressure_elements:
            label = _element_label(pressure_elements[0])
            sentences.append(f"{relation_subject} 관계에서 격국상 부담이 되는 {label} 기운도 힘을 받습니다.")
            break

    if flow.activated_elements and not useful_active and not caution_active:
        label = _element_label(flow.activated_elements[0])
        sentences.append(f"운에서 들어오는 {label} 기운은 올해 사건의 바탕에 깔립니다.")
    return sentences[:4]


def _pattern_candidate_reason_codes(candidates: list[Any], allowed_codes: set[str]) -> list[str]:
    reason_codes: list[str] = []
    for candidate in candidates:
        for code in getattr(candidate, "basis_codes", []) or []:
            text_code = str(code)
            if text_code in allowed_codes and text_code not in reason_codes:
                reason_codes.append(text_code)
    return reason_codes


def _pattern_candidate_reason_entries(candidates: list[Any], allowed_codes: set[str], domain: Domain) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for candidate in candidates:
        element = str(getattr(candidate, "element", ""))
        role = str(getattr(candidate, "role", ""))
        for code in getattr(candidate, "basis_codes", []) or []:
            text_code = str(code)
            if text_code not in allowed_codes:
                continue
            sentence = _complete_sentence(PATTERN_REASON_ROLE_TEXT.get(text_code, {}).get(domain, ""))
            event_sentence = _complete_sentence(PATTERN_REASON_EVENT_TEXT.get(text_code, {}).get(domain, ""))
            if not sentence and not event_sentence:
                continue
            entries.append(
                {
                    "element": element,
                    "role": role,
                    "reason_code": text_code,
                    "sentence": sentence,
                    "event_sentence": event_sentence,
                }
            )
    return entries


def _pattern_need_material(analysis: AnalysisResult, domain: Domain, packet: EventPacket | None = None) -> dict[str, Any]:
    profile = analysis.chart_structure.pattern_profile
    primary_name = profile.primary_pattern or profile.regular_pattern or "mixed_balanced_structure"
    pattern_label = PATTERN_LABELS.get(primary_name, primary_name)
    regular_label = PATTERN_LABELS.get(profile.regular_pattern, "") if profile.regular_pattern else ""
    useful_candidates = list(profile.useful_element_candidates)
    caution_candidates = list(profile.caution_element_candidates)
    useful = _select_pattern_candidates(useful_candidates, limit=2)
    useful_elements = {str(item.element) for item in useful}
    caution = _select_pattern_candidates(caution_candidates, limit=2, exclude_elements=useful_elements)
    overuse = _select_pattern_candidates(
        [
            candidate
            for candidate in caution_candidates
            if str(getattr(candidate, "element", "")) in useful_elements
        ],
        limit=1,
    )
    sentences = [
        _pattern_subject_sentence(pattern_label),
    ]
    sentences.extend(_pattern_direction_sentences(profile, domain, pattern_label, regular_label))
    if useful:
        sentences.extend(_candidate_intro_sentences(useful[:2], need_type="useful"))
        sentences.extend(_candidate_element_role_sentences(analysis, useful[:2], USEFUL_ELEMENT_ROLE_TEXT, domain))
        main_useful_label = _element_label(str(useful[0].element))
        sentences.append(PATTERN_DOMAIN_RESULTS[domain]["support"].replace("이 기운", f"{main_useful_label} 기운"))
    if caution:
        sentences.extend(_candidate_intro_sentences(caution[:2], need_type="caution"))
        sentences.extend(_candidate_element_role_sentences(analysis, caution[:2], CAUTION_ELEMENT_ROLE_TEXT, domain))
        caution_label = _element_label(str(caution[0].element))
        sentences.append(PATTERN_DOMAIN_RESULTS[domain]["pressure"].replace("이 기운", f"{caution_label} 기운"))
    sentences.extend(_flow_pattern_activation_sentences(analysis, domain, packet, useful, caution))

    basis_codes = [f"pattern_{primary_name}"]
    if profile.regular_pattern:
        basis_codes.append(f"regular_pattern_{profile.regular_pattern}")
    basis_codes.extend(f"pattern_useful_{item.element}_{item.role}" for item in useful)
    basis_codes.extend(f"pattern_caution_{item.element}_{item.role}" for item in caution)
    basis_codes.extend(f"pattern_useful_excess_{item.element}_{item.role}" for item in overuse)
    support_reason_codes = _pattern_candidate_reason_codes(useful, PATTERN_SUPPORT_REASON_CODES)
    pressure_reason_codes = _pattern_candidate_reason_codes(caution, PATTERN_PRESSURE_REASON_CODES)
    support_reason_entries = _pattern_candidate_reason_entries(useful, PATTERN_SUPPORT_REASON_CODES, domain)
    pressure_reason_entries = _pattern_candidate_reason_entries(caution, PATTERN_PRESSURE_REASON_CODES, domain)
    overuse_reason_entries = _pattern_candidate_reason_entries(overuse, PATTERN_PRESSURE_REASON_CODES, domain)
    for entry in support_reason_entries[:1]:
        event_sentence = _compact(str(entry.get("event_sentence") or ""))
        if event_sentence:
            sentences.append(_complete_sentence(event_sentence))
    for entry in pressure_reason_entries[:1]:
        event_sentence = _compact(str(entry.get("event_sentence") or ""))
        if event_sentence:
            sentences.append(_complete_sentence(event_sentence))
    for item in [*useful, *caution, *overuse]:
        for code in getattr(item, "basis_codes", []) or []:
            if code not in basis_codes:
                basis_codes.append(str(code))
    return {
        "layer": "pattern_need",
        "label": "격국과 필요한 기운",
        "priority": "primary",
        "pattern_name": primary_name,
        "regular_pattern": profile.regular_pattern,
        "useful_elements": [str(item.element) for item in useful],
        "caution_elements": [str(item.element) for item in caution],
        "overuse_elements": [str(item.element) for item in overuse],
        "support_reason_codes": support_reason_codes,
        "pressure_reason_codes": pressure_reason_codes,
        "support_reason_entries": support_reason_entries,
        "pressure_reason_entries": pressure_reason_entries,
        "overuse_reason_entries": overuse_reason_entries,
        "support_reason_sentence": support_reason_entries[0]["sentence"] if support_reason_entries else "",
        "pressure_reason_sentence": pressure_reason_entries[0]["sentence"] if pressure_reason_entries else "",
        "support_event_sentence": support_reason_entries[0]["event_sentence"] if support_reason_entries else "",
        "pressure_event_sentence": pressure_reason_entries[0]["event_sentence"] if pressure_reason_entries else "",
        "sentence": _material_sentence(" ".join(sentences)),
        "basis_codes": basis_codes,
    }


def _strength_material(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    strength = analysis.chart_structure.element_profile.day_master_strength
    text = DOMAIN_STRENGTH_EFFECT[domain].get(strength, DOMAIN_STRENGTH_EFFECT[domain]["balanced"])
    return {
        "layer": "day_master_strength",
        "label": "일간 강약",
        "priority": "support",
        "sentence": text,
        "basis_codes": [f"day_master_strength_{strength}"],
    }


def _position_sentence(domain: Domain, signal: PositionSignal) -> str:
    position = POSITION_BRANCH_LABELS.get(signal.position, signal.position)
    role = POSITION_REALITY_ROLES.get(signal.position, "현실")
    domain_position_roles = {
        "money": {
            "month": "직업 수입과 사회 환경",
            "day": "생활비와 가까운 사람의 돈 문제",
            "hour": "후반기 자산과 실무 보상",
            "year": "초기 환경과 집안의 돈 감각",
        },
        "career": {
            "month": "직업과 사회 환경",
            "day": "가까운 관계에서 맡는 책임",
            "hour": "후반기 전문성과 결과물",
            "year": "사회적 배경과 대외 평판",
        },
        "love": {
            "month": "사회생활과 관계 태도",
            "day": "가까운 관계와 일상",
            "hour": "후반기 인연과 관계 기대",
            "year": "초기 관계 경험",
        },
        "marriage": {
            "month": "직업 환경과 생활 책임",
            "day": "배우자궁과 가까운 생활",
            "hour": "후반기 생활 계획",
            "year": "가족 배경과 주변 시선",
        },
    }
    role = domain_position_roles.get(domain, {}).get(signal.position, role)
    if signal.position == "day":
        if domain == "marriage":
            role = "배우자궁과 가까운 생활"
        elif domain == "love":
            role = "가까운 관계와 일상"
    branch = _branch_label(signal.branch_key)
    branch_topic = _topic_particle_text(branch)
    element = _element_label(signal.branch_element)
    texture = DOMAIN_ELEMENT_BRANCH_TEXTURE.get(domain, {}).get(signal.branch_element, "생활 감각")
    ten_god = _ten_god_label(signal.branch_main_ten_god)
    scene = POSITION_DOMAIN_SCENES.get(domain, {}).get(signal.position, DOMAIN_POSITION_EFFECT[domain])
    position_texture = branch_position_texture(signal.branch_key, signal.position)
    domain_texture = branch_domain_texture(signal.branch_key, domain)
    detail_parts = [
        f"{position} {branch}에서는 {role}{_subject_particle_text(role)} 먼저 바뀝니다.",
    ]
    if position_texture:
        detail_parts.append(position_texture)
    if domain_texture:
        detail_parts.append(domain_texture)
    if domain == "money":
        detail_parts.append(f"재물운에서는 {texture}{_object_particle_text(texture)} 먼저 따집니다.")
        detail_parts.append("수입과 자산 기준이 구체적으로 세워집니다.")
        detail_parts.append("생활비 문제도 함께 봅니다.")
    elif domain == "career":
        detail_parts.append(f"직업운에서는 {texture}{_object_particle_text(texture)} 먼저 확인합니다.")
        detail_parts.append("업무 역할과 평가 방식이 구체적으로 정해집니다.")
    elif domain == "love":
        detail_parts.append(f"연애운에서는 {texture}{_subject_particle_text(texture)} 먼저 보입니다.")
        detail_parts.append("마음의 거리와 연락 간격이 구체적으로 달라집니다.")
    elif domain == "marriage":
        detail_parts.append(f"결혼운에서는 {texture}{_object_particle_text(texture)} 먼저 따집니다.")
        detail_parts.append("배우자와의 생활 방식이 구체적으로 정해집니다.")
        detail_parts.append("생활비와 주거 문제도 함께 봅니다.")
    else:
        detail_parts.append(f"실제 생활에서는 {texture}{_subject_particle_text(texture)} 먼저 바뀝니다.")
    detail_parts.append(f"본기인 {ten_god}{_topic_particle_text(ten_god)} 이 지지의 중심 기운입니다.")
    detail_parts.append(scene)
    return _material_sentence(
        " ".join(part for part in detail_parts if part)
    )


def _branch_relation_action(domain: Domain, relation_type: str) -> str:
    return DOMAIN_BRANCH_RELATION_ACTIONS.get(domain, {}).get(
        relation_type,
        BRANCH_RELATION_ACTIONS.get(relation_type, "지지의 힘이 생활 문제를 직접 흔듭니다."),
    )


def _branch_foundation_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    for position in DOMAIN_POSITION_PRIORITY[domain][:2]:
        signal = analysis.chart_structure.position_signals.get(position)
        if signal is None:
            continue
        materials.append(
            {
                "layer": "earthly_branch_foundation",
                "label": POSITION_BRANCH_LABELS.get(position, position),
                "position": position,
                "branch": signal.branch_key,
                "branch_label": _branch_label(signal.branch_key),
                "branch_element": signal.branch_element,
                "branch_element_label": _element_label(signal.branch_element),
                "branch_main_ten_god": signal.branch_main_ten_god,
                "branch_main_ten_god_label": _ten_god_label(signal.branch_main_ten_god),
                "priority": "primary" if position in {"month", "day"} else "support",
                "sentence": _position_sentence(domain, signal),
                "basis_codes": [f"position_{position}_{signal.branch_key}_{signal.branch_main_ten_god}"],
            }
        )
    return materials


def _hidden_stem_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    for position in DOMAIN_POSITION_PRIORITY[domain][:3]:
        signal = analysis.chart_structure.position_signals.get(position)
        if signal is None or not signal.hidden_ten_gods:
            continue
        hidden_entries = _hidden_stem_entries(analysis, signal)[:3]
        if not hidden_entries:
            continue
        protruded_entries = [entry for entry in hidden_entries if entry["protruded"]]
        leading_entry = protruded_entries[0] if protruded_entries else hidden_entries[0]
        hidden_roles = [str(entry["ten_god_label"]) for entry in hidden_entries]
        hidden_phrase = _join(hidden_roles)
        hidden_particle = _subject_particle_text(hidden_phrase)
        group_effects: list[str] = []
        for role in [str(entry["ten_god"]) for entry in hidden_entries]:
            group = TEN_GOD_GROUPS.get(role, "")
            effect = HIDDEN_GROUP_DOMAIN_SCENES.get(domain, {}).get(group, "")
            if effect and effect not in group_effects:
                group_effects.append(effect)
        hidden_effect = " ".join(group_effects[:2]) or DOMAIN_HIDDEN_STEM_EFFECT[domain]
        hidden_role_sentence = _hidden_role_scene(domain, str(leading_entry["ten_god"]), protruded=False) or hidden_effect
        protruded_role_sentence = ""
        reception_source_entry = protruded_entries[0] if protruded_entries else leading_entry
        reception_signal = _matching_hidden_reception_signal(analysis, position, str(reception_source_entry["stem"]))
        stem_reception_sentence = ""
        if reception_signal is not None:
            stem_reception_sentence = _stem_reception_event_sentence(
                domain,
                reception_signal,
                protruded=bool(protruded_entries),
            )
        hidden_element_balance_status = _hidden_element_balance_status(analysis, str(reception_source_entry["element"]))
        hidden_element_balance_sentence = _hidden_element_balance_sentence(analysis, domain, reception_source_entry)
        hidden_pattern_status = _pattern_element_status(analysis, str(reception_source_entry["element"]))
        hidden_pattern_role_sentence = _hidden_pattern_role_sentence(analysis, domain, reception_source_entry)
        branch = _branch_label(signal.branch_key)
        hidden_position_scene = HIDDEN_POSITION_DOMAIN_SCENES.get(domain, {}).get(position, "")
        if protruded_entries:
            stems = [str(entry["stem_label"]) for entry in protruded_entries]
            stem_phrase = _join(stems)
            stem_particle = _subject_particle_text(stem_phrase)
            protruded_role_sentence = (
                _hidden_role_scene(domain, str(protruded_entries[0]["ten_god"]), protruded=True)
                or "투출된 지장간은 속에 있던 기준을 말과 선택으로 분명하게 가져옵니다."
            )
            if "지장간" not in protruded_role_sentence:
                protruded_role_sentence = protruded_role_sentence.replace("밖으로 드러난 ", "투출된 ", 1)
            if protruded_role_sentence:
                protruded_role_sentence = _compact(
                    f"{protruded_role_sentence} {HIDDEN_REALITY_RESULTS.get(domain, {}).get(TEN_GOD_GROUPS.get(str(protruded_entries[0]['ten_god']), ''), '')}"
                )
            sentence = (
                f"{POSITION_BRANCH_LABELS.get(position, position)} {branch}의 지장간에는 {hidden_phrase}{hidden_particle} 자리합니다. "
                f"{hidden_position_scene} "
                f"{hidden_role_sentence} "
                f"그중 {stem_phrase}{stem_particle} 천간에도 자리합니다. {protruded_role_sentence}"
                f"{(' ' + stem_reception_sentence) if stem_reception_sentence else ''}"
                f"{(' ' + hidden_element_balance_sentence) if hidden_element_balance_sentence else ''}"
                f"{(' ' + hidden_pattern_role_sentence) if hidden_pattern_role_sentence else ''}"
            )
            priority = "primary"
        else:
            sentence = (
                f"{POSITION_BRANCH_LABELS.get(position, position)} {branch}의 지장간에는 {hidden_phrase}{hidden_particle} 자리합니다. "
                f"{hidden_position_scene} "
                f"{hidden_role_sentence}"
                f"{(' ' + stem_reception_sentence) if stem_reception_sentence else ''}"
                f"{(' ' + hidden_element_balance_sentence) if hidden_element_balance_sentence else ''}"
                f"{(' ' + hidden_pattern_role_sentence) if hidden_pattern_role_sentence else ''}"
            )
            priority = "support"
        materials.append(
            {
                "layer": "hidden_stem_storage",
                "label": f"{POSITION_BRANCH_LABELS.get(position, position)} 지장간",
                "position": position,
                "branch": signal.branch_key,
                "hidden_stems": [str(entry["stem"]) for entry in hidden_entries],
                "hidden_elements": [str(entry["element"]) for entry in hidden_entries],
                "hidden_ten_gods": [str(entry["ten_god"]) for entry in hidden_entries],
                "protruded_hidden_stems": [str(entry["stem"]) for entry in protruded_entries],
                "protruded_hidden_stem_labels": [str(entry["stem_label"]) for entry in protruded_entries],
                "protruded_hidden_elements": [str(entry["element"]) for entry in protruded_entries],
                "protruded_ten_gods": [str(entry["ten_god"]) for entry in protruded_entries],
                "dominant_hidden_ten_god": str(leading_entry["ten_god"]),
                "dominant_hidden_ten_god_label": str(leading_entry["ten_god_label"]),
                "dominant_hidden_group": TEN_GOD_GROUPS.get(str(leading_entry["ten_god"]), ""),
                "selected_hidden_element": str(reception_source_entry["element"]),
                "selected_hidden_element_balance": hidden_element_balance_status,
                "selected_hidden_pattern_status": hidden_pattern_status,
                "hidden_role_sentence": _material_sentence(hidden_role_sentence),
                "protruded_role_sentence": _material_sentence(protruded_role_sentence),
                "stem_reception_signal_id": str(getattr(reception_signal, "signal_id", "")) if reception_signal else "",
                "stem_reception_target_stem": str(getattr(reception_signal, "target_stem", "")) if reception_signal else "",
                "stem_reception_target_ten_god": str(getattr(reception_signal, "target_ten_god", "")) if reception_signal else "",
                "stem_reception_strength": str(getattr(reception_signal, "strength", "")) if reception_signal else "",
                "stem_reception_sentence": _material_sentence(stem_reception_sentence),
                "hidden_element_balance_sentence": _material_sentence(hidden_element_balance_sentence),
                "hidden_pattern_role_sentence": _material_sentence(hidden_pattern_role_sentence),
                "priority": priority,
                "sentence": _material_sentence(sentence),
                "basis_codes": list(
                    dict.fromkeys(
                        [f"hidden_{position}_{entry['ten_god']}" for entry in hidden_entries]
                        + [f"hidden_protruded_{position}_{entry['ten_god']}" for entry in protruded_entries]
                        + [f"hidden_balance_{position}_{hidden_element_balance_status}_{reception_source_entry['element']}"]
                        + (
                            [f"hidden_pattern_{position}_{hidden_pattern_status}_{reception_source_entry['element']}"]
                            if hidden_pattern_status
                            else []
                        )
                    )
                ),
            }
        )
    return materials[:2]


def _relation_relevant(domain: Domain, relation: BranchInteraction) -> bool:
    if domain in relation.domain_links:
        return True
    priority_positions = set(DOMAIN_POSITION_PRIORITY[domain][:2])
    return bool(priority_positions.intersection(relation.positions))


def _relation_element_role_sentence(
    analysis: AnalysisResult,
    domain: Domain,
    element: str,
    *,
    pressure: bool,
) -> str:
    group = _element_ten_god_group_key(analysis, element)
    if not group:
        return ""
    element_label = _element_label(element)
    group_label = TEN_GOD_GROUP_LABELS.get(group, "")
    if pressure:
        role_text = RELATION_PRESSURE_ROLE_TEXT.get(domain, {}).get(group, "")
    else:
        role_text = RELATION_SUPPORT_ROLE_TEXT.get(domain, {}).get(group, "")
    if not role_text:
        return ""
    return f"{group_label}인 {element_label} 기운이 이 변화를 이끕니다. {role_text}"


def _relation_motion_type(relation_type: str) -> str:
    if relation_type in DISRUPTING_RELATION_TYPES:
        return "disruptive"
    if relation_type in CONNECTING_RELATION_TYPES:
        return "connecting"
    return "neutral"


def _relation_domain_event_result(domain: Domain, polarity: str, relation_type: str) -> str:
    motion_type = _relation_motion_type(relation_type)
    return (
        RELATION_DOMAIN_EVENT_RESULTS.get(polarity, {})
        .get(motion_type, {})
        .get(domain)
        or RELATION_DOMAIN_EVENT_RESULTS.get(polarity, {})
        .get("neutral", {})
        .get(domain, "")
    )


def _relation_cause_sentence(relation_type: str, polarity: str, relation_label: str, element_label: str) -> str:
    if polarity == "supportive":
        template = RELATION_SUPPORT_CAUSE_SENTENCES.get(relation_type)
    elif polarity == "burdensome":
        template = RELATION_PRESSURE_CAUSE_SENTENCES.get(relation_type)
    else:
        template = ""
    relation_subject = f"{relation_label}{_topic_particle_text(relation_label)}"
    if template:
        return template.format(relation_subject=relation_subject, relation=relation_label, element=element_label)
    if polarity == "supportive":
        return f"{relation_subject} 격국상 필요한 {element_label} 기운을 받쳐 줍니다."
    if polarity == "burdensome":
        return f"{relation_subject} 격국상 부담이 되는 {element_label} 기운을 키웁니다."
    return ""


def _relation_polarity_sentence(analysis: AnalysisResult, relation: BranchInteraction, domain: Domain) -> str:
    polarity = branch_relation_polarity(
        analysis.chart_structure.element_profile,
        relation,
        analysis.chart_structure.pattern_profile,
    )
    support_labels = [_element_label(element) for element in polarity.support_elements]
    pressure_labels = [_element_label(element) for element in polarity.pressure_elements]
    def one_label(labels: list[str], index: int) -> str:
        if len(labels) <= index:
            return ""
        return labels[index].split(",")[0].strip()

    if polarity.polarity == "supportive" and support_labels:
        first = one_label(support_labels, 0)
        support_element = polarity.support_elements[0]
        role_sentence = _relation_element_role_sentence(analysis, domain, support_element, pressure=False)
        extra = (
            f" {_relation_element_role_sentence(analysis, domain, polarity.support_elements[1], pressure=False)}"
            if len(polarity.support_elements) > 1
            else ""
        )
        result = RELATION_POLARITY_DOMAIN_RESULTS[domain]["supportive"]
        event_result = _relation_domain_event_result(domain, "supportive", relation.relation_type)
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        cause = _relation_cause_sentence(relation.relation_type, "supportive", relation_label, first)
        return f"{cause} {event_result} {role_sentence} {result}{extra}"
    if polarity.polarity == "burdensome" and pressure_labels:
        first = one_label(pressure_labels, 0)
        pressure_element = polarity.pressure_elements[0]
        role_sentence = _relation_element_role_sentence(analysis, domain, pressure_element, pressure=True)
        extra = (
            f" {_relation_element_role_sentence(analysis, domain, polarity.pressure_elements[1], pressure=True)}"
            if len(polarity.pressure_elements) > 1
            else ""
        )
        result = RELATION_POLARITY_DOMAIN_RESULTS[domain]["burdensome"]
        event_result = _relation_domain_event_result(domain, "burdensome", relation.relation_type)
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        cause = _relation_cause_sentence(relation.relation_type, "burdensome", relation_label, first)
        return f"{cause} {event_result} {role_sentence} {result}{extra}"
    if polarity.polarity == "mixed":
        result = _relation_domain_event_result(domain, "mixed", relation.relation_type) or RELATION_POLARITY_DOMAIN_RESULTS[domain]["mixed"]
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        relation_topic = f"{relation_label}{_topic_particle_text(relation_label)}"
        first_support = one_label(support_labels, 0)
        first_pressure = one_label(pressure_labels, 0)
        support_role = (
            _relation_element_role_sentence(analysis, domain, polarity.support_elements[0], pressure=False)
            if polarity.support_elements
            else ""
        )
        pressure_role = (
            _relation_element_role_sentence(analysis, domain, polarity.pressure_elements[0], pressure=True)
            if polarity.pressure_elements
            else ""
        )
        if first_support and first_pressure:
            return (
                f"{relation_topic} 격국상 필요한 {first_support} 기운을 움직입니다. "
                f"격국상 부담이 되는 {first_pressure} 기운은 따로 부담으로 남습니다. "
                f"{support_role} {pressure_role} {result}"
            )
        labels = _join(support_labels or pressure_labels)
        if labels:
            return f"{relation_topic} 월령과 격국에서 {labels} 기운을 함께 움직입니다. {result}"
        return RELATION_POLARITY_DOMAIN_RESULTS[domain]["mixed"]
    relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
    relation_topic = f"{relation_label}{_topic_particle_text(relation_label)}"
    return f"{relation_topic} 큰 길흉보다 같은 문제를 반복하게 만듭니다."


def _position_branch_phrase(positions: list[str], branches: list[str]) -> str:
    pairs = [
        f"{position_label} {_branch_label(branch)}"
        for position_label, branch in zip(positions, branches)
        if position_label and branch
    ]
    if pairs:
        return _and_join(pairs)
    return _and_join(positions)


def _branch_relation_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    for relation in analysis.chart_structure.branch_interactions:
        if not _relation_relevant(domain, relation):
            continue
        branches = "".join(_branch_label(branch) for branch in relation.branches)
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        positions = [_branch_label_name for _branch_label_name in (POSITION_BRANCH_LABELS.get(pos, pos) for pos in relation.positions)]
        action = _branch_relation_action(domain, relation.relation_type)
        effect = _element_label(relation.effect_element) if relation.effect_element else ""
        effect_sentence = f" {effect} 기운이 더해집니다." if effect else ""
        polarity_sentence = _relation_polarity_sentence(analysis, relation, domain)
        polarity = branch_relation_polarity(
            analysis.chart_structure.element_profile,
            relation,
            analysis.chart_structure.pattern_profile,
        )
        position_phrase = _and_join(positions)
        position_branch_phrase = _position_branch_phrase(positions, list(relation.branches))
        sentence = (
            f"지지에서는 {position_branch_phrase}{_subject_particle_text(position_branch_phrase)} "
            f"{relation_label}{_object_particle_text(relation_label)} 이룹니다. "
            f"{action}{effect_sentence} {polarity_sentence} {DOMAIN_BRANCH_EFFECT[domain]}"
        )
        materials.append(
            {
                "layer": "branch_relations",
                "label": f"{branches} {relation_label}",
                "relation_type": relation.relation_type,
                "branches": list(relation.branches),
                "positions": list(relation.positions),
                "relation_polarity": polarity.polarity,
                "relation_support_elements": list(polarity.support_elements),
                "relation_pressure_elements": list(polarity.pressure_elements),
                "relation_overuse_elements": list(polarity.overuse_elements),
                "relation_useful_score": polarity.useful_score,
                "relation_pressure_score": polarity.pressure_score,
                "priority": "primary" if set(relation.positions).intersection({"month", "day"}) else "support",
                "sentence": _material_sentence(sentence),
                "basis_codes": [relation.basis_code],
            }
        )
    return materials[:2]


def _flow_branch_relation_materials(analysis: AnalysisResult, packet: EventPacket, domain: Domain) -> list[dict[str, Any]]:
    flow = _matching_flow(analysis, packet)
    if flow is None:
        return []

    materials: list[dict[str, Any]] = []
    flow_position_labels = {
        "year_flow": "세운",
        "daeun": "대운",
    }
    for relation in flow.branch_interactions:
        if not _relation_relevant(domain, relation):
            continue
        branches = "".join(_branch_label(branch) for branch in relation.branches)
        relation_label = BRANCH_RELATION_LABELS.get(relation.relation_type, relation.relation_type)
        positions = [
            flow_position_labels.get(position, POSITION_BRANCH_LABELS.get(position, position))
            for position in relation.positions
        ]
        action = _branch_relation_action(domain, relation.relation_type)
        effect = _element_label(relation.effect_element) if relation.effect_element else ""
        effect_sentence = f" {effect} 기운이 더해집니다." if effect else ""
        polarity_sentence = _relation_polarity_sentence(analysis, relation, domain)
        polarity = branch_relation_polarity(
            analysis.chart_structure.element_profile,
            relation,
            analysis.chart_structure.pattern_profile,
        )
        relation_subject = f"{branches} {relation_label}"
        position_phrase = _and_join(positions)
        position_branch_phrase = _position_branch_phrase(positions, list(relation.branches))
        sentence = (
            f"{_period_subject_text(packet.period_label)}에는 {position_branch_phrase}{_subject_particle_text(position_branch_phrase)} "
            f"{relation_label}{_object_particle_text(relation_label)} 이룹니다. "
            f"{action}{effect_sentence} {polarity_sentence} {DOMAIN_BRANCH_EFFECT[domain]}"
        )
        materials.append(
            {
                "layer": "flow_branch_relations",
                "label": relation_subject,
                "relation_type": relation.relation_type,
                "branches": list(relation.branches),
                "positions": list(relation.positions),
                "relation_polarity": polarity.polarity,
                "relation_support_elements": list(polarity.support_elements),
                "relation_pressure_elements": list(polarity.pressure_elements),
                "relation_overuse_elements": list(polarity.overuse_elements),
                "relation_useful_score": polarity.useful_score,
                "relation_pressure_score": polarity.pressure_score,
                "priority": "timing",
                "sentence": _material_sentence(sentence),
                "basis_codes": [relation.basis_code],
            }
        )
    return materials[:2]


def _ten_god_material(analysis: AnalysisResult, domain: Domain) -> dict[str, Any]:
    group_scores = analysis.chart_structure.ten_god_profile.group_scores
    ranked = sorted(group_scores.items(), key=lambda item: item[1], reverse=True)
    top_groups = [group for group, score in ranked if score > 0][:3]
    labels = [TEN_GOD_GROUP_LABELS.get(group, group) for group in top_groups]
    if labels:
        leading = f"십신 구성에서는 {_join(labels)}의 비중이 강합니다."
    else:
        leading = "십신 구성에서는 특정 역할 하나가 결론을 독점하지 않습니다."
    return {
        "layer": "ten_god_distribution",
        "label": "십신 분포",
        "priority": "primary",
        "sentence": _material_sentence(f"{leading} {DOMAIN_TEN_GOD_EFFECT[domain]}"),
        "basis_codes": [f"ten_god_group_{group}" for group in top_groups],
    }


def _signal_domain_match(domain: Domain, signal: Any) -> bool:
    links = getattr(signal, "domain_links", [])
    return domain in links


def _element_trait_sentence(domain: Domain, trait: str) -> str:
    domain_sentence = ELEMENT_TRAIT_DOMAIN_SENTENCES.get(trait, {}).get(domain)
    if domain_sentence:
        return domain_sentence
    return ELEMENT_TRAIT_SENTENCES.get(trait, f"이 배합에서는 {trait} 성향이 먼저 강해집니다.")


def _element_combo_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    profile = analysis.chart_structure.element_combination_profile
    signals = list(profile.heavenly_stem_signals) + list(profile.hidden_stem_signals) + list(profile.stem_branch_signals)
    materials: list[dict[str, Any]] = []
    for signal in signals:
        if not _signal_domain_match(domain, signal):
            continue
        stems = [_stem_label(stem) for stem in signal.stems]
        elements = [_element_label(element) for element in signal.elements]
        traits = [str(item) for item in getattr(signal, "trait_keywords", [])[:2]]
        label = "".join(stems) if stems else _join(elements)
        trait_sentences: list[str] = []
        if traits:
            trait_sentences.append(_element_trait_sentence(domain, traits[0]))
            if len(traits) >= 2:
                trait_sentences.append(_element_trait_sentence(domain, traits[1]))
        trait_text = f" {' '.join(trait_sentences)}" if trait_sentences else ""
        sentence = (
            f"{label} 오행 배합은 {_join(elements)} 기운이 만난 구성입니다. "
            f"{DOMAIN_ELEMENT_EFFECT[domain]}{trait_text}"
        )
        materials.append(
            {
                "layer": "element_pair_relations",
                "label": f"{label} 오행 배합",
                "priority": "support",
                "sentence": _material_sentence(sentence),
                "basis_codes": list(signal.basis_codes),
            }
        )
    return materials[:2]


def _integrated_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    profile = analysis.chart_structure.integrated_saju_profile
    signals = list(profile.visible_pair_signals) + list(profile.hidden_pair_signals) + list(profile.stem_branch_pair_signals)
    materials: list[dict[str, Any]] = []
    for signal in signals:
        if not _signal_domain_match(domain, signal):
            continue
        source = _stem_label(signal.source_stem)
        target = _stem_label(signal.target_stem)
        source_role = _ten_god_label(signal.source_ten_god)
        target_role = _ten_god_label(signal.target_ten_god)
        projection = str(signal.domain_projection.get(domain, "")).strip()
        if not projection:
            projection = f"{_domain_label(domain)}에서는 {source_role}와 {target_role}의 연결이 생활 속 선택으로 이어집니다."
        target_role_path = f"{target_role}{_adverbial_particle_text(target_role)}"
        sentence = (
            f"{source}{target} 결합에서는 오행의 성질과 십신의 역할이 한 장면에 놓입니다. "
            f"{source_role}에서 {target_role_path} 이어지는 작용이 있으며, {projection}"
        )
        materials.append(
            {
                "layer": "integrated_pair_action",
                "label": f"{source}{target} 오행·십신 결합",
                "priority": "primary",
                "sentence": _material_sentence(sentence),
                "basis_codes": list(signal.basis_codes),
            }
        )
    return materials[:2]


def _first_reception_condition(condition_map: dict[str, list[str]], domain: Domain) -> str:
    for value in condition_map.get(domain, []):
        phrase = _compact(str(value))
        if phrase:
            return phrase.replace("조건", "상황")
    return ""


def _day_stem_reception_event_sentence(signal: Any, domain: Domain) -> str:
    event = STEM_RECEPTION_EVENT_BY_DOMAIN.get(domain, {}).get(signal.target_ten_god, "")
    if not event:
        return ""
    return f"{_domain_label(domain)}에서는 {event}로 옮겨집니다."


def _stem_reception_source_sentence(signal: Any) -> str:
    base_position = str(signal.position).split(":", 1)[0]
    if signal.layer == "visible_stem":
        position = POSITION_LABELS.get(base_position, base_position)
        return f"{position} 천간에 있어 밖으로 바로 확인됩니다."
    branch_position = POSITION_BRANCH_LABELS.get(base_position, base_position)
    if signal.layer == "branch_main":
        return f"{branch_position} 본기에 있어 생활 장면에서 꾸준히 힘을 냅니다."
    if signal.protruded:
        return f"{branch_position} 지장간에 있고 천간에도 드러나 사건성이 분명합니다."
    return f"{branch_position} 지장간에 있어 생활 속에서 늦게 확인됩니다."


def _stem_reception_season_sentence(signal: Any) -> str:
    modifier = float(getattr(signal, "seasonal_modifier", 1.0))
    target = _stem_label(signal.target_stem)
    if modifier >= 1.15:
        return f"월령에서 {target}의 힘이 강해 이 글자가 빠르게 힘을 냅니다."
    if modifier <= 0.85:
        return f"월령에서 {target}의 힘이 약해 이 글자는 시간이 지나야 힘을 냅니다."
    return ""


def _relation_polarity_from_modifiers(modifiers: list[str]) -> str:
    supportive = {"six_combine", "three_harmony", "three_harmony_half"}
    burdensome = {"clash", "punishment", "self_punishment", "break", "harm"}
    has_support = any(modifier in supportive for modifier in modifiers)
    has_burden = any(modifier in burdensome for modifier in modifiers)
    if has_support and not has_burden:
        return "supportive"
    if has_burden and not has_support:
        return "burdensome"
    if has_support or has_burden:
        return "mixed"
    return "neutral"


def _stem_reception_relation_sentence(signal: Any, domain: Domain) -> str:
    modifiers = list(getattr(signal, "branch_relation_modifiers", []) or [])
    if not modifiers:
        return ""
    labels = [BRANCH_RELATION_LABELS.get(modifier, modifier) for modifier in modifiers[:2]]
    relation_text = _join(labels)
    relation_subject = f"{relation_text}{_subject_particle_text(relation_text)}"
    polarity = _relation_polarity_from_modifiers(modifiers)
    domain_result = RELATION_POLARITY_DOMAIN_RESULTS.get(domain, {}).get(polarity, "")
    if domain_result:
        return f"지지에서는 {relation_subject} 함께 걸립니다. {domain_result}"
    return f"지지에서는 {relation_subject} 동시에 보입니다."


def _stem_reception_condition_sentences(signal: Any, domain: Domain) -> list[str]:
    domain_name = _domain_label(domain)
    fitting = _first_reception_condition(signal.fitting_conditions, domain)
    misfitting = _first_reception_condition(signal.misfitting_conditions, domain)
    fatigue = _first_reception_condition(signal.fatigue_or_loss, domain)
    sentences: list[str] = []
    if fitting:
        sentences.append(f"{domain_name}에서 잘 맞는 장면은 {fitting}입니다.")
    if misfitting:
        sentences.append(f"{domain_name}에서 맞지 않는 장면은 {misfitting}입니다.")
    if fatigue:
        sentences.append(f"{domain_name}에서 소모가 커지는 지점은 {fatigue}입니다.")
    return sentences


def _stem_reception_materials(analysis: AnalysisResult, domain: Domain) -> list[dict[str, Any]]:
    profile = analysis.chart_structure.stem_reception_profile
    signals = list(profile.visible_stem_signals) + list(profile.branch_main_signals) + list(profile.hidden_stem_signals)
    materials: list[dict[str, Any]] = []
    for signal in signals:
        if not _signal_domain_match(domain, signal):
            continue
        day = _stem_label(signal.day_stem)
        target = _stem_label(signal.target_stem)
        role = _ten_god_label(signal.target_ten_god)
        projection = str(signal.domain_projection.get(domain, "")).strip()
        if not projection:
            projection = f"{_domain_label(domain)}에서는 이 재료가 판단 방식과 선택 태도로 이어집니다."
        target_object = f"{target}{_object_particle_text(target)}"
        event_sentence = _day_stem_reception_event_sentence(signal, domain)
        source_sentence = _stem_reception_source_sentence(signal)
        seasonal_sentence = _stem_reception_season_sentence(signal)
        relation_sentence = _stem_reception_relation_sentence(signal, domain)
        condition_sentences = _stem_reception_condition_sentences(signal, domain)
        sentence_parts = [
            f"{day}일간은 {target_object} {role}의 영역으로 받아들입니다.",
            str(signal.felt_experience),
            projection,
            STEM_RECEPTION_DOMAIN_ANCHORS.get(domain, ""),
            event_sentence,
            source_sentence,
            seasonal_sentence,
            relation_sentence,
            *condition_sentences,
        ]
        sentence = " ".join(part for part in sentence_parts if part)
        materials.append(
            {
                "layer": "day_stem_reception",
                "label": f"{day}일간의 {target} 수용",
                "priority": "primary" if signal.layer == "visible_stem" else "support",
                "sentence": _material_sentence(sentence),
                "basis_codes": list(signal.basis_codes),
                "stem_reception_event": STEM_RECEPTION_EVENT_BY_DOMAIN.get(domain, {}).get(signal.target_ten_god, ""),
                "fitting_scene": _first_reception_condition(signal.fitting_conditions, domain),
                "misfitting_scene": _first_reception_condition(signal.misfitting_conditions, domain),
                "fatigue_scene": _first_reception_condition(signal.fatigue_or_loss, domain),
                "seasonal_modifier": signal.seasonal_modifier,
                "branch_relation_modifiers": list(signal.branch_relation_modifiers),
                "protruded": signal.protruded,
            }
        )
    return materials[:2]


def _matching_flow(analysis: AnalysisResult, packet: EventPacket):
    for flow in analysis.flow_signals:
        if flow.period_label == packet.period_label:
            return flow
        if str(flow.year) == str(packet.period_label).replace("년", ""):
            return flow
    return None


def _flow_element_status(analysis: AnalysisResult, element: str) -> str:
    profile = analysis.chart_structure.element_profile
    score = profile.scores.get(element)
    pattern_status = _pattern_element_status(analysis, element)
    helpful = (
        element in profile.useful_elements
        or element in profile.climate_needs
        or pattern_status in {"supportive", "mixed"}
    )
    burdensome = (
        element in profile.caution_elements
        or bool(score and score.state == "dominant")
        or pattern_status in {"pressure", "mixed"}
    )
    if helpful and burdensome:
        return "mixed"
    if helpful:
        return "supportive"
    if burdensome:
        return "pressure"
    return "neutral"


def _flow_pattern_role_sentence(domain: Domain, status: str, support_text: str, pressure_text: str) -> str:
    domain_label = {
        "money": "재물운",
        "career": "직업운",
        "love": "연애운",
        "marriage": "결혼운",
    }.get(domain, _domain_label(domain))
    if status == "supportive" and support_text:
        return f"이 시기 {domain_label}에서는 {support_text}"
    if status == "pressure" and pressure_text:
        return f"이 시기 {domain_label}에서는 {pressure_text}"
    if status == "mixed":
        parts = [f"이 시기 {domain_label}에서는"]
        if support_text:
            parts.append(support_text)
        if pressure_text:
            parts.append(pressure_text)
        return _compact(" ".join(parts))
    return ""


def _flow_element_activation_sentence(analysis: AnalysisResult, domain: Domain, flow: Any) -> tuple[str, str, str]:
    for element in getattr(flow, "activated_elements", []):
        status = _flow_element_status(analysis, str(element))
        if status == "neutral":
            continue
        group = _element_ten_god_group_key(analysis, str(element))
        if not group:
            continue
        support_text = RELATION_SUPPORT_ROLE_TEXT.get(domain, {}).get(group, "")
        pressure_text = RELATION_PRESSURE_ROLE_TEXT.get(domain, {}).get(group, "")
        sentence = _flow_pattern_role_sentence(domain, status, support_text, pressure_text)
        if sentence:
            return sentence, status, str(element)
    return "", "", ""


def _fortune_keyword_sentences(domain: Domain, keywords: list[str]) -> str:
    cleaned = [keyword for keyword in keywords if keyword]
    if not cleaned:
        return f"해당 사건이 {_domain_label(domain)} 문제로 이어집니다."

    def event_label(keyword: str) -> str:
        subject = keyword.strip()
        if subject.endswith(" 일"):
            subject = f"{subject[:-2]} 장면"
        elif subject.endswith("일"):
            subject = f"{subject[:-1]} 장면"
        return subject

    def event_subject(keyword: str) -> str:
        subject = event_label(keyword)
        return f"{subject}{_subject_particle_text(subject)}"

    first = cleaned[0]
    first_subject = event_subject(first)
    sentences = [f"{first_subject} 올해 {_domain_label(domain)}운에서 먼저 커집니다."]
    if len(cleaned) >= 2:
        second_label = event_label(cleaned[1])
        domain_second_templates = {
            "money": f"{second_label}도 함께 바뀝니다.",
            "career": f"{second_label}도 함께 생깁니다.",
            "love": f"{second_label}도 함께 말하게 됩니다.",
            "marriage": f"{second_label}도 함께 정리하게 됩니다.",
        }
        sentences.append(domain_second_templates.get(domain, f"{second_label}도 함께 바뀝니다."))
    return _compact(" ".join(sentences))


def _fortune_year_role_sentence(domain: Domain, period_year_label: str, year_pillar: str, role_phrase: str) -> str:
    subject = f"{period_year_label} 세운 {year_pillar}"
    role_subject = f"{role_phrase} 기운" if role_phrase else "세운의 기운"
    templates = {
        "money": "{subject}에는 {role_subject}이 수입 기준을 바꿉니다. 지출 기준도 다시 조정됩니다.",
        "career": "{subject}에는 {role_subject}이 역할을 바꿉니다. 평가 방식도 달라집니다.",
        "love": "{subject}에는 {role_subject}이 연락 방식을 바꿉니다. 감정 표현도 달라집니다.",
        "marriage": "{subject}에는 {role_subject}이 생활비 기준을 바꿉니다. 책임 분담도 다시 조정됩니다.",
    }
    return templates.get(domain, "{subject}에는 {role_subject}이 생활의 선택을 바꿉니다.").format(
        subject=subject,
        role_subject=role_subject,
    )


def _fortune_material(analysis: AnalysisResult, packet: EventPacket) -> dict[str, Any]:
    flow = _matching_flow(analysis, packet)
    keywords = [str(item) for item in packet.event_keywords[:2]]
    keyword_sentence = _fortune_keyword_sentences(packet.domain, keywords)
    flow_pattern_sentence = ""
    flow_pattern_status = ""
    flow_pattern_element = ""
    if flow is None:
        sentence = f"{packet.period_label}에는 {keyword_sentence}"
        basis_codes = list(packet.basis_codes[:3])
    else:
        stem_role = _ten_god_label(flow.year_stem_ten_god)
        branch_role = _ten_god_label(flow.year_branch_main_ten_god)
        year_role_phrase = _unique_and_join([stem_role, branch_role])
        flow_pattern_sentence, flow_pattern_status, flow_pattern_element = _flow_element_activation_sentence(
            analysis,
            packet.domain,
            flow,
        )
        sentence = f"{_fortune_year_role_sentence(packet.domain, _flow_period_year_label(packet), flow.year_pillar, year_role_phrase)} {keyword_sentence}"
        if flow_pattern_sentence:
            sentence += f" {flow_pattern_sentence}"
        if flow.daeun_pillar:
            daeun_roles = [
                _ten_god_label(role)
                for role in (flow.daeun_stem_ten_god, flow.daeun_branch_main_ten_god)
                if role
            ]
            daeun_phrase = _unique_and_join(daeun_roles)
            daeun_subject = f"대운 {flow.daeun_pillar}"
            daeun_topic = f"{daeun_subject}{_topic_particle_text(daeun_subject)}"
            if daeun_phrase:
                sentence += f" {daeun_topic} {daeun_phrase}의 장기 배경을 만듭니다."
            else:
                sentence += f" {daeun_subject}의 장기 배경도 함께 봅니다."
        basis_codes = list(flow.basis_codes[:3]) + list(packet.basis_codes[:3])
        if flow_pattern_status and flow_pattern_element:
            group = _element_ten_god_group_key(analysis, flow_pattern_element)
            basis_codes.append(f"fortune_flow_pattern_{packet.domain}_{flow_pattern_status}_{flow_pattern_element}_{group}")
    return {
        "layer": "fortune_activation",
        "label": "세운·대운 자극",
        "priority": "timing",
        "sentence": _material_sentence(sentence),
        "basis_codes": list(dict.fromkeys(basis_codes)),
        "flow_pattern_status": flow_pattern_status,
        "flow_pattern_element": flow_pattern_element,
        "flow_pattern_role_sentence": _material_sentence(flow_pattern_sentence),
    }


def _ten_god_group_result(domain: Domain, ten_god: str | None) -> str:
    if not ten_god:
        return ""
    group = TEN_GOD_GROUPS.get(ten_god, "")
    if not group:
        return ""
    return FORTUNE_GROUP_RESULTS.get(domain, {}).get(group, "")


def _flow_period_year_label(packet: EventPacket) -> str:
    period = str(packet.period_label)
    return period if period.endswith("년") else f"{period}년"


def _fortune_conclusion_sentences(analysis: AnalysisResult, packet: EventPacket) -> dict[str, str]:
    flow = _matching_flow(analysis, packet)
    if flow is None:
        return {"outcome": "", "mobile": "", "daeun": ""}

    domain = packet.domain
    year_stem_role = _ten_god_label(flow.year_stem_ten_god)
    year_branch_role = _ten_god_label(flow.year_branch_main_ten_god)
    year_role_phrase = _unique_and_join([year_stem_role, year_branch_role])
    stem_result = _ten_god_group_result(domain, flow.year_stem_ten_god)
    branch_result = _ten_god_group_result(domain, flow.year_branch_main_ten_god)
    outcome_parts = [
        _fortune_year_role_sentence(domain, _flow_period_year_label(packet), flow.year_pillar, year_role_phrase)
    ]
    if stem_result:
        outcome_parts.append(stem_result)
    if branch_result and branch_result != stem_result:
        outcome_parts.append(branch_result)

    flow_pattern_sentence, flow_pattern_status, _ = _flow_element_activation_sentence(analysis, domain, flow)
    if flow_pattern_sentence and flow_pattern_status in {"supportive", "mixed"}:
        outcome_parts.append(flow_pattern_sentence)

    daeun_sentence = ""
    if flow.daeun_pillar:
        daeun_roles = [
            _ten_god_label(role)
            for role in (flow.daeun_stem_ten_god, flow.daeun_branch_main_ten_god)
            if role
        ]
        daeun_phrase = _unique_and_join(daeun_roles)
        daeun_subject = f"대운 {flow.daeun_pillar}"
        daeun_topic = f"{daeun_subject}{_topic_particle_text(daeun_subject)}"
        daeun_stem_result = _ten_god_group_result(domain, flow.daeun_stem_ten_god)
        daeun_branch_result = _ten_god_group_result(domain, flow.daeun_branch_main_ten_god)
        daeun_parts = [
            f"{daeun_topic} {daeun_phrase}의 장기 배경을 만듭니다." if daeun_phrase else f"{daeun_subject}도 장기 배경으로 봅니다."
        ]
        if daeun_stem_result:
            daeun_parts.append(daeun_stem_result)
        if daeun_branch_result and daeun_branch_result != daeun_stem_result:
            daeun_parts.append(daeun_branch_result)
        daeun_sentence = _material_sentence(" ".join(daeun_parts))

    mobile = FORTUNE_MOBILE_RESULTS[domain]
    if flow.daeun_pillar:
        mobile_subject = f"{_flow_period_year_label(packet)} 세운과 대운 {flow.daeun_pillar}"
        mobile_targets = {
            "money": "수입 기준이 커집니다. 지출 기준도 다시 조정됩니다.",
            "career": "역할이 커집니다. 평가 방식도 달라집니다.",
            "love": "연락과 만남이 관계 판단의 중심이 됩니다.",
            "marriage": "생활비 기준이 커집니다. 책임 분담도 다시 조정됩니다.",
        }
        mobile = f"{mobile_subject}에서는 {mobile_targets[domain]}"

    return {
        "outcome": _material_sentence(" ".join(outcome_parts)),
        "mobile": _material_sentence(mobile),
        "daeun": daeun_sentence,
    }


def _core_conclusion(packet: EventPacket) -> str:
    conclusion = EVENT_CONCLUSIONS.get(packet.sub_event_type)
    if conclusion:
        return f"당신의 {packet.period_label} {packet.domain_label if hasattr(packet, 'domain_label') else _domain_label(packet.domain) + '운'}은 {conclusion}"
    return f"당신의 {packet.period_label} {_domain_label(packet.domain)}운은 {packet.primary_scene_sentence}"


def _score_judgment(packet: EventPacket) -> str:
    if packet.event_probability_score >= 78 and packet.risk_score < 60:
        return "기회가 강하고 반대 신호가 크지 않아 결론이 분명합니다."
    if packet.event_probability_score >= 70 and packet.risk_score >= 60:
        return "사건성이 강하고 부담도 커서 결과와 관리 문제가 동시에 커집니다."
    if packet.risk_score >= 70:
        return "부담 신호가 강하므로 조심할 장면을 선명하게 보아야 합니다."
    if packet.event_probability_score >= 60:
        return "생활에서 충분히 느낄 만큼 커집니다."
    return "큰 사건으로 단정하기보다 생활 속 보조 신호로 읽습니다."


def _first_material(materials: list[dict[str, Any]], layer: str) -> dict[str, Any] | None:
    return next((material for material in materials if material.get("layer") == layer), None)


def _material_relation_label(material: dict[str, Any] | None) -> str:
    if not material:
        return ""
    label = _compact(str(material.get("label") or ""))
    return label or "지지 관계"


def _first_pattern_element(material: dict[str, Any] | None, key: str) -> str:
    if not material:
        return ""
    values = list(material.get(key) or [])
    return str(values[0]) if values else ""


def _pattern_reason_sentence(
    material: dict[str, Any] | None,
    key: str,
    domain: Domain,
    *,
    preferred_element: str = "",
) -> str:
    if not material:
        return ""
    entries_key = "support_reason_entries" if key == "support_reason_codes" else "pressure_reason_entries"
    entries = [entry for entry in list(material.get(entries_key) or []) if isinstance(entry, dict)]
    if preferred_element:
        for entry in entries:
            if str(entry.get("element") or "") == preferred_element:
                return _complete_sentence(str(entry.get("sentence") or ""))
        return ""
    if entries:
        return _complete_sentence(str(entries[0].get("sentence") or ""))
    direct_key = "support_reason_sentence" if key == "support_reason_codes" else "pressure_reason_sentence"
    direct_sentence = _compact(str(material.get(direct_key) or ""))
    if direct_sentence:
        return _complete_sentence(direct_sentence)
    for code in list(material.get(key) or []):
        text = PATTERN_REASON_ROLE_TEXT.get(str(code), {}).get(domain, "")
        if text:
            return _complete_sentence(text)
    return ""


def _pattern_event_sentence(
    material: dict[str, Any] | None,
    key: str,
    domain: Domain,
    *,
    preferred_element: str = "",
) -> str:
    if not material:
        return ""
    entries_key = "support_reason_entries" if key == "support_reason_codes" else "pressure_reason_entries"
    entries = [entry for entry in list(material.get(entries_key) or []) if isinstance(entry, dict)]
    if preferred_element:
        for entry in entries:
            if str(entry.get("element") or "") == preferred_element:
                return _complete_sentence(str(entry.get("event_sentence") or ""))
        return ""
    if entries:
        return _complete_sentence(str(entries[0].get("event_sentence") or ""))
    direct_key = "support_event_sentence" if key == "support_reason_codes" else "pressure_event_sentence"
    direct_sentence = _compact(str(material.get(direct_key) or ""))
    if direct_sentence:
        return _complete_sentence(direct_sentence)
    for code in list(material.get(key) or []):
        text = PATTERN_REASON_EVENT_TEXT.get(str(code), {}).get(domain, "")
        if text:
            return _complete_sentence(text)
    return ""


def _reason_entry_elements(material: dict[str, Any] | None, entries_key: str) -> set[str]:
    if not material:
        return set()
    return {
        str(entry.get("element") or "")
        for entry in list(material.get(entries_key) or [])
        if isinstance(entry, dict) and str(entry.get("element") or "")
    }


def _relation_pattern_element_for_reason(
    *,
    relation_material: dict[str, Any] | None,
    pattern_material: dict[str, Any] | None,
    relation_key: str,
    fallback: str,
    entries_key: str,
    allowed_elements: set[str] | None = None,
) -> str:
    if not relation_material:
        return fallback
    values = [str(value) for value in list(relation_material.get(relation_key) or []) if str(value)]
    if allowed_elements:
        values = [value for value in values if value in allowed_elements]
    if not values:
        return fallback
    reason_elements = _reason_entry_elements(pattern_material, entries_key)
    if fallback and fallback in values and fallback in reason_elements:
        return fallback
    for value in values:
        if value in reason_elements:
            return value
    if fallback and fallback in values:
        return fallback
    return values[0]


def _pattern_relation_materials(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flow_materials = [material for material in materials if material.get("layer") == "flow_branch_relations"]
    if flow_materials:
        return flow_materials
    return [material for material in materials if material.get("layer") == "branch_relations"]


def _relation_pattern_match_score(
    *,
    relation_material: dict[str, Any],
    pattern_material: dict[str, Any],
    relation_key: str,
    fallback: str,
    entries_key: str,
    polarity_targets: set[str],
    score_key: str,
    allowed_elements: set[str],
) -> int:
    values = {str(value) for value in list(relation_material.get(relation_key) or []) if str(value)}
    values = values.intersection(allowed_elements)
    if not values:
        return -1

    reason_elements = _reason_entry_elements(pattern_material, entries_key)
    polarity = str(relation_material.get("relation_polarity") or "")
    score = int(relation_material.get(score_key) or 0)
    if reason_elements.intersection(values):
        score += 80
    if fallback and fallback in values:
        score += 30
    if fallback and fallback in values and fallback in reason_elements:
        score += 40
    if polarity in polarity_targets:
        score += 20
    if polarity == "mixed":
        score += 5
    return score


def _select_relation_material_for_pattern(
    *,
    materials: list[dict[str, Any]],
    pattern_material: dict[str, Any],
    relation_key: str,
    fallback: str,
    entries_key: str,
    polarity_targets: set[str],
    score_key: str,
    allowed_elements: set[str],
) -> dict[str, Any] | None:
    candidates = _pattern_relation_materials(materials)
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, material in enumerate(candidates):
        score = _relation_pattern_match_score(
            relation_material=material,
            pattern_material=pattern_material,
            relation_key=relation_key,
            fallback=fallback,
            entries_key=entries_key,
            polarity_targets=polarity_targets,
            score_key=score_key,
            allowed_elements=allowed_elements,
        )
        if score >= 0:
            ranked.append((score, index, material))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2]


def _pattern_conclusion_sentences(
    domain: Domain,
    materials: list[dict[str, Any]],
) -> dict[str, str]:
    pattern_material = _first_material(materials, "pattern_need")
    if not pattern_material:
        return {"outcome": "", "pressure": "", "mobile": ""}

    useful_element = _first_pattern_element(pattern_material, "useful_elements")
    caution_element = _first_pattern_element(pattern_material, "caution_elements")
    useful_elements = {str(value) for value in list(pattern_material.get("useful_elements") or []) if str(value)}
    caution_elements = {str(value) for value in list(pattern_material.get("caution_elements") or []) if str(value)}

    support_relation_material = _select_relation_material_for_pattern(
        materials=materials,
        pattern_material=pattern_material,
        relation_key="relation_support_elements",
        fallback=useful_element,
        entries_key="support_reason_entries",
        polarity_targets={"supportive", "mixed"},
        score_key="relation_useful_score",
        allowed_elements=useful_elements,
    )
    pressure_relation_material = _select_relation_material_for_pattern(
        materials=materials,
        pattern_material=pattern_material,
        relation_key="relation_pressure_elements",
        fallback=caution_element,
        entries_key="pressure_reason_entries",
        polarity_targets={"burdensome", "mixed"},
        score_key="relation_pressure_score",
        allowed_elements=caution_elements,
    )
    support_element = _relation_pattern_element_for_reason(
        relation_material=support_relation_material,
        pattern_material=pattern_material,
        relation_key="relation_support_elements",
        fallback=useful_element,
        entries_key="support_reason_entries",
        allowed_elements=useful_elements,
    )
    pressure_element = _relation_pattern_element_for_reason(
        relation_material=pressure_relation_material,
        pattern_material=pattern_material,
        relation_key="relation_pressure_elements",
        fallback=caution_element,
        entries_key="pressure_reason_entries",
        allowed_elements=caution_elements,
    )
    support_reason = _pattern_reason_sentence(
        pattern_material,
        "support_reason_codes",
        domain,
        preferred_element=support_element,
    )
    support_event = _pattern_event_sentence(
        pattern_material,
        "support_reason_codes",
        domain,
        preferred_element=support_element,
    )
    direct_support_event = _complete_sentence(str(pattern_material.get("support_event_sentence") or ""))
    pressure_reason = _pattern_reason_sentence(
        pattern_material,
        "pressure_reason_codes",
        domain,
        preferred_element=pressure_element,
    )
    pressure_event = _pattern_event_sentence(
        pattern_material,
        "pressure_reason_codes",
        domain,
        preferred_element=pressure_element,
    )
    direct_pressure_event = _complete_sentence(str(pattern_material.get("pressure_event_sentence") or ""))

    outcome = ""
    if support_element:
        support_label = _element_label(support_element)
        if support_relation_material:
            relation_label = _material_relation_label(support_relation_material)
            opening = PATTERN_RELATION_SUPPORT_OPENING[domain].format(
                relation=relation_label,
                element=support_label,
            )
        else:
            opening = PATTERN_SUPPORT_OPENING[domain].format(element=support_label)
        outcome_parts = [opening]
        if support_reason and support_reason not in opening:
            outcome_parts.append(support_reason)
        if support_event and support_event not in " ".join(outcome_parts):
            outcome_parts.append(support_event)
        if direct_support_event and direct_support_event not in " ".join(outcome_parts):
            outcome_parts.append(direct_support_event)
        outcome_parts.append(PATTERN_CONCLUSION_SUPPORT[domain])
        outcome = " ".join(outcome_parts)

    pressure = ""
    if pressure_element:
        pressure_label = _element_label(pressure_element)
        if pressure_relation_material:
            relation_label = _material_relation_label(pressure_relation_material)
            opening = PATTERN_RELATION_PRESSURE_OPENING[domain].format(
                relation=relation_label,
                element=pressure_label,
            )
        else:
            opening = PATTERN_PRESSURE_OPENING[domain].format(element=pressure_label)
        pressure_parts = [opening]
        if pressure_reason and pressure_reason not in opening:
            pressure_parts.append(pressure_reason)
        if pressure_event and pressure_event not in " ".join(pressure_parts):
            pressure_parts.append(pressure_event)
        if direct_pressure_event and direct_pressure_event not in " ".join(pressure_parts):
            pressure_parts.append(direct_pressure_event)
        if not pressure_reason:
            pressure_parts.append(PATTERN_CONCLUSION_PRESSURE[domain])
        pressure = " ".join(pressure_parts)

    mobile = ""
    if support_element:
        support_label = _element_label(support_element)
        mobile = f"{support_label} 기운이 힘을 얻으면서 {PATTERN_MOBILE_SUPPORT[domain]}"
    elif pressure_element:
        pressure_label = _element_label(pressure_element)
        mobile = f"{pressure_label} 기운이 과해지면서 {PATTERN_MOBILE_PRESSURE[domain]}"

    return {
        "outcome": _material_sentence(outcome),
        "pressure": _material_sentence(pressure),
        "mobile": _material_sentence(mobile),
    }


def _month_reality_conclusion(domain: Domain, material: dict[str, Any] | None) -> str:
    if not material:
        return ""
    return _material_sentence(f"월령은 {_domain_label(domain)}운의 기본 바탕입니다. {DOMAIN_MONTH_EFFECT[domain]}")


def _branch_reality_conclusion(domain: Domain, material: dict[str, Any] | None) -> str:
    if not material:
        return ""
    position = str(material.get("position") or "")
    position_label = str(material.get("label") or POSITION_BRANCH_LABELS.get(position, "지지"))
    branch_label = str(material.get("branch_label") or "")
    branch_key = str(material.get("branch") or branch_label)
    branch_phrase = _compact(f"{position_label} {branch_label}")
    if not branch_phrase:
        branch_phrase = position_label
    domain_texture = branch_domain_texture(branch_key, domain)
    scene = POSITION_DOMAIN_SCENES.get(domain, {}).get(position, "")
    if not scene:
        scene = f"{_domain_label(domain)}운은 생활의 실제 문제로 확인됩니다."
    body_parts = [f"{branch_phrase}{_subject_particle_text(branch_phrase)} {_domain_label(domain)}운을 현실에서 체감하게 만듭니다."]
    if domain_texture:
        body_parts.append(domain_texture)
    body_parts.append(scene)
    return _material_sentence(
        " ".join(part for part in body_parts if part)
    )


def _hidden_reality_conclusion(domain: Domain, material: dict[str, Any] | None) -> str:
    if not material:
        return ""
    label = _compact(str(material.get("label") or "지장간"))
    group = str(material.get("dominant_hidden_group") or "")
    role_label = str(material.get("dominant_hidden_ten_god_label") or "숨은 기운")
    result = HIDDEN_REALITY_RESULTS.get(domain, {}).get(group) or DOMAIN_HIDDEN_STEM_EFFECT[domain]
    protruded_labels = [str(item) for item in material.get("protruded_hidden_stem_labels", []) if str(item)]
    if protruded_labels:
        stem_phrase = _join(protruded_labels[:2])
        return _material_sentence(
            f"{label}에서 {stem_phrase}{_subject_particle_text(stem_phrase)} 천간으로 투출됩니다. {result}"
        )
    return _material_sentence(f"{label} 속 {role_label}{_subject_particle_text(role_label)} 현실 판단의 기준이 됩니다. {result}")


def _relation_reality_conclusion(domain: Domain, material: dict[str, Any] | None) -> str:
    if not material:
        return ""
    label = _material_relation_label(material)
    polarity = str(material.get("relation_polarity") or "neutral")
    result = REALITY_RELATION_RESULTS.get(domain, {}).get(polarity) or REALITY_RELATION_RESULTS[domain]["neutral"]
    opening_by_domain = {
        "money": f"{_adverbial_phrase_text(label)} 받을 돈 문제가 커집니다. 지출도 커집니다.",
        "career": f"{_adverbial_phrase_text(label)} 역할 이동이 생깁니다. 평가는 달라집니다.",
        "love": f"{_adverbial_phrase_text(label)} 연락 방식이 달라집니다. 만남의 간격도 달라집니다.",
        "marriage": f"{_adverbial_phrase_text(label)} 생활 약속이 무거워집니다. 책임 문제도 커집니다.",
    }
    return _material_sentence(
        f"{opening_by_domain[domain]} {result}"
    )


def _reality_conclusion_sentences(domain: Domain, materials: list[dict[str, Any]]) -> dict[str, str]:
    month_material = _first_material(materials, "month_command")
    branch_material = _first_material(materials, "earthly_branch_foundation")
    hidden_material = _first_material(materials, "hidden_stem_storage")
    relation_material = _first_material(materials, "flow_branch_relations") or _first_material(materials, "branch_relations")

    month = _month_reality_conclusion(domain, month_material)
    branch = _branch_reality_conclusion(domain, branch_material)
    hidden = _hidden_reality_conclusion(domain, hidden_material)
    relation = _relation_reality_conclusion(domain, relation_material)

    if relation:
        front = relation
        mobile_source = _material_relation_label(relation_material)
        mobile = f"{_adverbial_phrase_text(mobile_source)} {REALITY_MOBILE_RESULTS[domain]['relation']}"
    elif hidden:
        front = hidden
        mobile = f"지장간이 {REALITY_MOBILE_RESULTS[domain]['hidden']}"
    elif branch:
        front = branch
        branch_label = str(branch_material.get("branch_label") or "") if branch_material else ""
        position_label = str(branch_material.get("label") or "지지") if branch_material else "지지"
        branch_phrase = _compact(f"{position_label} {branch_label}")
        mobile = f"{branch_phrase}{_subject_particle_text(branch_phrase)} {REALITY_MOBILE_RESULTS[domain]['branch']}"
    else:
        front = month
        mobile = f"월령이 {REALITY_MOBILE_RESULTS[domain]['month']}" if month else ""

    return {
        "month": month,
        "branch": branch,
        "hidden": hidden,
        "relation": relation,
        "front": _material_sentence(front),
        "mobile": _material_sentence(mobile),
    }


def _material_coverage(materials: list[dict[str, Any]]) -> dict[str, bool]:
    layers = {str(material.get("layer")) for material in materials}
    return {
        "month_command": "month_command" in layers,
        "month_governance": "month_governance" in layers,
        "branch_foundation": "earthly_branch_foundation" in layers,
        "hidden_stem_storage": "hidden_stem_storage" in layers,
        "branch_relations": "branch_relations" in layers,
        "flow_branch_relations": "flow_branch_relations" in layers,
        "pattern_need": "pattern_need" in layers,
        "cycle_regulation": "cycle_regulation" in layers,
        "element_distribution": "element_distribution" in layers,
        "ten_god_distribution": "ten_god_distribution" in layers,
        "integrated_pair_action": "integrated_pair_action" in layers,
        "stem_reception": "day_stem_reception" in layers,
        "gyeokguk_core_action": "gyeokguk_core_action" in layers,
        "gyeokguk_flow_action": "gyeokguk_flow_action" in layers,
        "fortune_activation": "fortune_activation" in layers,
    }


def _dedupe_materials(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for material in materials:
        key = (str(material.get("layer")), str(material.get("sentence")))
        if key in seen:
            continue
        seen.add(key)
        material["basis_codes"] = [code for code in list(dict.fromkeys(material.get("basis_codes", []))) if code]
        deduped.append(material)
    return deduped


def _gyeokguk_action_context_rank(match: Any, *, source: str) -> int:
    context_rank = {
        "constructive_by_context": 34,
        "medicine_or_regulator": 34,
        "risk_by_context": 34,
        "structure_supports_expression": 34,
        "medicine_can_work": 34,
        "month_pressure_confirms_risk": 34,
        "risk_is_reinforced": 34,
        "context_strengthens_action": 28,
        "context_strengthens_pair": 28,
        "conditional_by_context": 15,
        "context_weakens_action": 6,
        "context_weakens_pair": 6,
        "not_activated": 0,
    }.get(str(getattr(match, "context_judgment_state", "")), 0)
    if source == "dual":
        grade_rank = {
            "medicine_chain": 28,
            "constructive_chain": 28,
            "supportive_chain": 22,
            "mediated_tension_chain": 22,
            "success_chain": 22,
            "support_chain": 22,
            "risk_chain": 22,
            "compounded_burden_chain": 22,
            "conditional_chain": 14,
            "mixed_chain": 8,
            "disease_chain": 4,
        }.get(str(getattr(match, "chain_grade", "")), 0)
    else:
        grade_rank = {
            "core": 28,
            "core_overload": 28,
            "strong_regulator": 28,
            "danger": 28,
            "breaker": 28,
            "breaker_or_medicine": 22,
            "regulator_or_breaker": 22,
            "support": 22,
            "regulator": 22,
            "burden": 14,
            "conditioned_support": 14,
            "mixed": 8,
            "source": 8,
        }.get(str(getattr(match, "role_grade", "")), 0)
    return int(getattr(match, "presence_score", 0) or 0) + context_rank + grade_rank


def _gyeokguk_match_identity(source: str, match: Any) -> tuple[str, str, str]:
    if source == "dual":
        return (
            "dual",
            str(getattr(match, "exact_pair_category", "") or getattr(match, "exact_pair_key", "")),
            str(getattr(match, "rule_key", "")),
        )
    return (
        "single",
        str(getattr(match, "action_key", "")),
        str(getattr(match, "rule_key", "")),
    )


def _gyeokguk_exact_profile_domain_basis(match: Any) -> dict[str, list[str]]:
    payload: dict[str, list[str]] = {
        "single": [],
        "first": [],
        "second": [],
        "all": [],
    }
    prefixes = {
        "single": "gyeokguk_action_exact_profile_domain:",
        "first": "gyeokguk_dual_first_exact_profile_domain:",
        "second": "gyeokguk_dual_second_exact_profile_domain:",
    }
    for code in list(getattr(match, "basis_codes", []) or []):
        text = str(code)
        for key, prefix in prefixes.items():
            if text.startswith(prefix):
                domain = text.split(":", 1)[1]
                payload[key].append(domain)
                payload["all"].append(domain)
    return {
        key: list(dict.fromkeys(values))
        for key, values in payload.items()
        if values
    }


def _gyeokguk_match_has_pattern_center_bridge(match: Any) -> bool:
    return any(
        str(code).startswith("gyeokguk_dual_pattern_center_bridge:")
        for code in list(getattr(match, "basis_codes", []) or [])
    )


def _gyeokguk_pattern_center_relevance_score(profile: Any, source: str, match: Any) -> int:
    pattern_ten_god = str(getattr(profile, "primary_ten_god", "") or "")
    pattern_group = str(getattr(profile, "primary_group", "") or "")
    if source == "dual":
        direct = (
            str(getattr(match, "first_ten_god", "") or "") == pattern_ten_god
            or str(getattr(match, "second_ten_god", "") or "") == pattern_ten_god
        )
        same_group = (
            str(getattr(match, "first_group", "") or "") == pattern_group
            or str(getattr(match, "second_group", "") or "") == pattern_group
        )
        if direct:
            return 46
        if same_group:
            return 32
        if _gyeokguk_match_has_pattern_center_bridge(match):
            return 28
        return -10

    acting_ten_god = str(getattr(match, "acting_ten_god", "") or "")
    acting_group = str(getattr(match, "acting_group", "") or "")
    if acting_ten_god == pattern_ten_god:
        return 42
    if acting_group == pattern_group:
        return 30
    if str(getattr(match, "relation_to_pattern", "") or ""):
        return 8
    return -8


def _gyeokguk_center_axis_score(match: Any) -> dict[str, Any]:
    """Score how fully a match is grounded in the required judgment axes."""

    def has_text(value: Any) -> bool:
        if isinstance(value, dict):
            return any(has_text(item) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(has_text(item) for item in value)
        return bool(str(value or "").strip())

    visibility_interaction = dict(getattr(match, "visibility_interaction", {}) or {})
    position_context = dict(getattr(match, "position_context", {}) or {})
    branch_context = dict(getattr(match, "branch_relation_context", {}) or {})
    axis_scores = {
        "month_command": 12 if has_text(getattr(match, "month_fit_state", "")) else 0,
        "day_master_strength": 8 if has_text(getattr(match, "day_master_strength_context", "")) else 0,
        "climate": 8 if has_text(getattr(match, "climate_context", "")) else 0,
        "protrusion": 5 if has_text(getattr(match, "protrusion_effect", "") or visibility_interaction.get("protrusion", "")) else 0,
        "rooting": 5 if has_text(getattr(match, "rooting_effect", "") or visibility_interaction.get("rooting", "")) else 0,
        "hidden_stems": 5 if has_text(getattr(match, "hidden_effect", "") or visibility_interaction.get("hidden_stem", "")) else 0,
        "unrooted": 3 if has_text(getattr(match, "unrooted_effect", "") or visibility_interaction.get("unrooted", "")) else 0,
        "position": 5 if has_text(position_context or visibility_interaction.get("position", "")) else 0,
        "branch_interactions": 5 if has_text(branch_context or visibility_interaction.get("branch_interaction", "")) else 0,
        "flow_activation": 4 if has_text(getattr(match, "timing_activation", "")) else 0,
    }
    return {
        "score": sum(axis_scores.values()),
        "axes": axis_scores,
    }


def _gyeokguk_exact_ten_god_specificity_score(source: str, match: Any) -> dict[str, Any]:
    """Score whether the selected action carries exact ten-god meaning, not only a generic group."""

    if source == "dual":
        ten_gods = [
            str(getattr(match, "first_ten_god", "") or ""),
            str(getattr(match, "second_ten_god", "") or ""),
        ]
    else:
        ten_gods = [str(getattr(match, "acting_ten_god", "") or "")]

    domains: list[str] = []
    exact_faces = 0
    for ten_god in ten_gods:
        profile = dict(TEN_GOD_EXACT_ACTION_PROFILE.get(ten_god, {}) or {})
        if TEN_GOD_EXACT_NUANCE.get(ten_god):
            exact_faces += 1
        domains.extend(str(domain) for domain in list(profile.get("domains", []) or []) if domain)

    score = min(18, exact_faces * 4 + len(set(domains)) * 2)
    if source == "dual" and str(getattr(match, "exact_pair_category", "") or ""):
        score += 6
    if source == "dual" and str(getattr(match, "exact_pair_effect", "") or "") and str(getattr(match, "exact_pair_risk", "") or ""):
        score += 4

    return {
        "score": min(28, score),
        "ten_gods": ten_gods,
        "domains": sorted(set(domains)),
        "has_exact_pair": source == "dual" and bool(str(getattr(match, "exact_pair_category", "") or "")),
    }


def _gyeokguk_center_selection_components(profile: Any, source: str, match: Any) -> dict[str, Any]:
    context_rank = _gyeokguk_action_context_rank(match, source=source)
    pattern_center = _gyeokguk_pattern_center_relevance_score(profile, source, match)
    axis_score = _gyeokguk_center_axis_score(match)
    exact_score = _gyeokguk_exact_ten_god_specificity_score(source, match)
    total = context_rank + pattern_center + int(axis_score["score"]) + int(exact_score["score"])
    return {
        "context_rank": context_rank,
        "pattern_center_relevance": pattern_center,
        "required_axis_score": int(axis_score["score"]),
        "required_axis_breakdown": dict(axis_score["axes"]),
        "exact_ten_god_score": int(exact_score["score"]),
        "exact_ten_god_basis": exact_score,
        "total": total,
    }


def _gyeokguk_global_center_action_index(analysis: AnalysisResult, limit: int = 3) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Select the natal center actions once, then let each domain reuse them."""

    profile = analysis.chart_structure.gyeokguk_profile
    support_tags = {
        "siksang_saengjae",
        "jaesaenggwan",
        "gwanin_sangsaeng",
        "salin_sangsaeng",
        "siksin_jesal",
        "jaeseong_generates_gwanseong",
        "gwanseong_generates_inseong",
        "siksang_controls_gwanseong",
        "gwanseong_controls_bigeop",
        "bigeop_generates_siksang",
        "inseong_generates_bigeop",
    }
    caution_tags = {
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
        "bigeop_controls_wealth",
        "wealth_controls_resource",
        "inseong_controls_output",
    }

    def candidate_tags(source: str, match: Any) -> set[str]:
        tags = {str(tag) for tag in list(getattr(match, "classical_action_tags", []) or [])}
        if source == "dual":
            tags.update(str(tag) for tag in list(getattr(match, "first_single_classical_action_tags", []) or []))
            tags.update(str(tag) for tag in list(getattr(match, "second_single_classical_action_tags", []) or []))
        return tags

    def candidate_direct_center(source: str, match: Any) -> bool:
        pattern_ten_god = str(getattr(profile, "primary_ten_god", "") or "")
        pattern_group = str(getattr(profile, "primary_group", "") or "")
        if source == "dual":
            return (
                str(getattr(match, "first_ten_god", "") or "") == pattern_ten_god
                or str(getattr(match, "second_ten_god", "") or "") == pattern_ten_god
                or str(getattr(match, "first_group", "") or "") == pattern_group
                or str(getattr(match, "second_group", "") or "") == pattern_group
            )
        return (
            str(getattr(match, "acting_ten_god", "") or "") == pattern_ten_god
            or str(getattr(match, "acting_group", "") or "") == pattern_group
        )

    candidates: list[dict[str, Any]] = []
    for match in list(getattr(profile, "dual_ten_god_action_matches", []) or []):
        components = _gyeokguk_center_selection_components(profile, "dual", match)
        score = int(components["total"])
        tags = candidate_tags("dual", match)
        candidates.append(
            {
                "score": score,
                "selection_components": components,
                "source_order": 0,
                "presence_score": int(getattr(match, "presence_score", 0) or 0),
                "source": "dual",
                "rule_key": str(getattr(match, "rule_key", "")),
                "match": match,
                "tags": tags,
                "direct_center": candidate_direct_center("dual", match),
                "center_bridge": _gyeokguk_match_has_pattern_center_bridge(match),
                "support": bool(tags & support_tags),
                "caution": bool(tags & caution_tags),
            }
        )
    for match in list(getattr(profile, "ten_god_action_matches", []) or []):
        components = _gyeokguk_center_selection_components(profile, "single", match)
        score = int(components["total"])
        tags = candidate_tags("single", match)
        candidates.append(
            {
                "score": score,
                "selection_components": components,
                "source_order": 1,
                "presence_score": int(getattr(match, "presence_score", 0) or 0),
                "source": "single",
                "rule_key": str(getattr(match, "rule_key", "")),
                "match": match,
                "tags": tags,
                "direct_center": candidate_direct_center("single", match),
                "center_bridge": False,
                "support": bool(tags & support_tags),
                "caution": bool(tags & caution_tags),
            }
        )

    selected: dict[tuple[str, str, str], dict[str, int]] = {}
    seen_categories: set[tuple[str, str]] = set()

    def sorted_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            items,
            key=lambda item: (
                -int(item["score"]),
                int(item["source_order"]),
                -int(item["presence_score"]),
                str(item["rule_key"]),
            ),
        )

    def add_candidate(candidate: dict[str, Any] | None) -> None:
        if candidate is None or len(selected) >= limit:
            return
        source = str(candidate["source"])
        match = candidate["match"]
        identity = _gyeokguk_match_identity(source, match)
        category = (identity[0], identity[1])
        if category in seen_categories:
            return
        seen_categories.add(category)
        selected[identity] = {
            "rank": len(selected) + 1,
            "score": int(candidate["score"]),
            "presence_score": int(candidate["presence_score"]),
            "source_order": int(candidate["source_order"]),
            "selection_components": dict(candidate.get("selection_components", {}) or {}),
        }

    def best_candidate(predicate) -> dict[str, Any] | None:
        matches = [candidate for candidate in candidates if predicate(candidate)]
        return sorted_candidates(matches)[0] if matches else None

    add_candidate(best_candidate(lambda item: item["source"] == "dual" and item["direct_center"] and item["support"]))
    add_candidate(best_candidate(lambda item: item["source"] == "dual" and item["center_bridge"] and item["caution"]))
    add_candidate(best_candidate(lambda item: item["source"] == "single" and item["direct_center"]))

    for candidate in sorted_candidates(candidates):
        if len(selected) >= limit:
            break
        add_candidate(candidate)
    return selected


def _gyeokguk_domain_aliases(domain: Domain) -> tuple[str, ...]:
    return {
        "money": ("money",),
        "career": ("career", "reputation"),
        "love": ("love", "relationship", "people", "partner"),
        "marriage": ("marriage", "partner", "family", "relationship"),
    }.get(domain, (domain,))


def _gyeokguk_action_matches_domain(match: Any, domain: Domain) -> bool:
    aliases = _gyeokguk_domain_aliases(domain)
    if any(alias in list(getattr(match, "domain_priority", []) or []) for alias in aliases):
        return True
    projections = getattr(match, "domain_projections", {}) or {}
    return isinstance(projections, dict) and any(alias in projections for alias in aliases)


def _gyeokguk_projection_for_domain(match: Any, domain: Domain) -> str:
    aliases = _gyeokguk_domain_aliases(domain)
    projections = getattr(match, "domain_projections", {}) or {}
    if not isinstance(projections, dict):
        return ""
    for alias in aliases:
        text = str(projections.get(alias, "") or "").strip()
        if text:
            return text
    return ""


def _gyeokguk_domain_relevance_score(match: Any, domain: Domain) -> int:
    aliases = _gyeokguk_domain_aliases(domain)
    priority = [str(item) for item in list(getattr(match, "domain_priority", []) or [])]
    projections = getattr(match, "domain_projections", {}) or {}
    score = 0
    for alias in aliases:
        if alias in priority:
            # The first material in each domain must be the center action that
            # actually explains that domain, not merely the globally strongest
            # action repeated across every section.
            score = max(score, 130 - min(priority.index(alias), 5) * 16)
        if isinstance(projections, dict) and str(projections.get(alias, "") or "").strip():
            score = max(score, 20)
    return score


def _gyeokguk_single_operation_axes(match: Any) -> dict[str, Any]:
    """Preserve the single-ten-god action as judgment material, not prose only."""

    acting = str(getattr(match, "acting_ten_god", "") or "")
    return {
        "operation_type": "single_ten_god",
        "acting_ten_god": acting,
        "acting_ten_god_label": _ten_god_label(acting),
        "acting_group": getattr(match, "acting_group", ""),
        "relation_to_pattern": getattr(match, "relation_to_pattern", ""),
        "action_key": getattr(match, "action_key", ""),
        "action_nature": getattr(match, "action_nature", ""),
        "role_grade": getattr(match, "role_grade", ""),
        "center_effect": getattr(match, "center_effect", ""),
        "role_in_pattern_logic": getattr(match, "role_in_pattern_logic", ""),
        "pattern_effect_state": getattr(match, "pattern_effect_state", ""),
        "pattern_resolution_state": getattr(match, "pattern_resolution_state", ""),
        "pattern_resolution_logic": getattr(match, "pattern_resolution_logic", ""),
        "activation_context": getattr(match, "activation_context", ""),
    }


def _gyeokguk_dual_operation_axes(match: Any) -> dict[str, Any]:
    """Preserve the ordered two-ten-god chain and its disease/medicine logic."""

    first = str(getattr(match, "first_ten_god", "") or "")
    second = str(getattr(match, "second_ten_god", "") or "")
    pattern_ten_god = str(getattr(match, "pattern_ten_god", "") or "")
    return {
        "operation_type": "dual_ten_god_chain",
        "pattern_ten_god": pattern_ten_god,
        "pattern_ten_god_label": _ten_god_label(pattern_ten_god),
        "first_ten_god": first,
        "first_ten_god_label": _ten_god_label(first),
        "first_group": getattr(match, "first_group", ""),
        "first_relation_to_pattern": getattr(match, "first_relation_to_pattern", ""),
        "second_ten_god": second,
        "second_ten_god_label": _ten_god_label(second),
        "second_group": getattr(match, "second_group", ""),
        "second_relation_to_pattern": getattr(match, "second_relation_to_pattern", ""),
        "first_to_second_relation": getattr(match, "first_to_second_relation", ""),
        "sequence_key": getattr(match, "sequence_key", ""),
        "chain_grade": getattr(match, "chain_grade", ""),
        "chain_nature": getattr(match, "chain_nature", ""),
        "pattern_combination_state": getattr(match, "pattern_combination_state", ""),
        "combination_resolution_state": getattr(match, "combination_resolution_state", ""),
        "combination_resolution_logic": getattr(match, "combination_resolution_logic", ""),
        "primary_actor": getattr(match, "primary_actor", ""),
        "secondary_actor": getattr(match, "secondary_actor", ""),
        "actor_hierarchy_logic": getattr(match, "actor_hierarchy_logic", ""),
        "disease_medicine_logic": getattr(match, "disease_medicine_logic", ""),
        "first_then_second_activation": getattr(match, "first_then_second_activation", ""),
        "second_then_first_activation": getattr(match, "second_then_first_activation", ""),
    }


def _gyeokguk_reality_axes(match: Any) -> dict[str, Any]:
    """Keep where the action is visible, rooted, hidden, and eventized."""

    return {
        "presence_state": getattr(match, "presence_state", ""),
        "presence_score": getattr(match, "presence_score", 0),
        "month_fit_state": getattr(match, "month_fit_state", ""),
        "verdict": getattr(match, "verdict", ""),
        "day_master_strength_context": getattr(match, "day_master_strength_context", ""),
        "climate_context": getattr(match, "climate_context", ""),
        "position_context": dict(getattr(match, "position_context", {}) or {}),
        "branch_relation_context": dict(getattr(match, "branch_relation_context", {}) or {}),
        "protrusion_effect": getattr(match, "protrusion_effect", ""),
        "rooting_effect": getattr(match, "rooting_effect", ""),
        "hidden_effect": getattr(match, "hidden_effect", ""),
        "unrooted_effect": getattr(match, "unrooted_effect", ""),
        "event_manifestations": dict(getattr(match, "event_manifestations", {}) or {}),
        "timing_activation": getattr(match, "timing_activation", ""),
    }


def _gyeokguk_eventization_basis(match: Any, context_axes: dict[str, Any], reality_axes: dict[str, Any]) -> dict[str, Any]:
    """Preserve the route from gyeokguk theory to event-level judgment."""

    visibility_interaction = dict(getattr(match, "visibility_interaction", {}) or {})
    position_context = reality_axes["position_context"] or visibility_interaction.get("position", "")
    branch_relation_context = reality_axes["branch_relation_context"] or visibility_interaction.get("branch_interaction", "")
    return {
        "month_fit_state": getattr(match, "month_fit_state", ""),
        "day_master_strength": getattr(match, "day_master_strength_context", ""),
        "climate": getattr(match, "climate_context", ""),
        "presence_state": getattr(match, "presence_state", ""),
        "presence_score": getattr(match, "presence_score", 0),
        "visibility_path": {
            "protrusion": reality_axes["protrusion_effect"] or visibility_interaction.get("protrusion", ""),
            "rooting": reality_axes["rooting_effect"] or visibility_interaction.get("rooting", ""),
            "hidden_stems": reality_axes["hidden_effect"] or visibility_interaction.get("hidden_stem", ""),
            "unrooted": reality_axes["unrooted_effect"] or visibility_interaction.get("unrooted", ""),
            "position": position_context,
            "branch_interactions": branch_relation_context,
        },
        "luck_activation": reality_axes["timing_activation"],
        "judgment_order": context_axes["judgment_order"],
        "judgment_path": context_axes["context_judgment_path"],
    }


def _gyeokguk_exact_ten_god_faces(match: Any) -> dict[str, Any]:
    """Extract exact ten-god action faces from rule basis codes."""

    def profile_payload(ten_god: str) -> dict[str, Any]:
        profile = dict(TEN_GOD_EXACT_ACTION_PROFILE.get(ten_god, {}) or {})
        return {
            "ten_god": ten_god,
            "label": _ten_god_label(ten_god),
            "nuance": TEN_GOD_EXACT_NUANCE.get(ten_god, ""),
            "excess": profile.get("excess", ""),
            "deficiency": profile.get("deficiency", ""),
            "protruded": profile.get("protruded", ""),
            "hidden": profile.get("hidden", ""),
            "rooted": profile.get("rooted", ""),
            "unrooted": profile.get("unrooted", ""),
            "domains": list(profile.get("domains", []) or []),
        }

    codes = [str(code) for code in list(getattr(match, "basis_codes", []) or [])]
    single = [
        code.split(":", 1)[1]
        for code in codes
        if code.startswith("gyeokguk_action_exact_profile_domain:")
    ]
    first = [
        code.split(":", 1)[1]
        for code in codes
        if code.startswith("gyeokguk_dual_first_exact_profile_domain:")
    ]
    second = [
        code.split(":", 1)[1]
        for code in codes
        if code.startswith("gyeokguk_dual_second_exact_profile_domain:")
    ]
    return {
        "single_profile": profile_payload(str(getattr(match, "acting_ten_god", "") or "")),
        "first_profile": profile_payload(str(getattr(match, "first_ten_god", "") or "")),
        "second_profile": profile_payload(str(getattr(match, "second_ten_god", "") or "")),
        "single_domains": list(dict.fromkeys(single)),
        "first_domains": list(dict.fromkeys(first)),
        "second_domains": list(dict.fromkeys(second)),
        "all_domains": list(dict.fromkeys([*single, *first, *second])),
    }


def _gyeokguk_context_axes(match: Any) -> dict[str, Any]:
    return {
        "context_judgment_state": getattr(match, "context_judgment_state", ""),
        "context_judgment_summary": getattr(match, "context_judgment_summary", ""),
        "context_judgment_path": list(getattr(match, "context_judgment_path", []) or []),
        "domain_priority": list(getattr(match, "domain_priority", []) or []),
        "expert_summary": getattr(match, "expert_summary", ""),
        "judgment_order": list(getattr(match, "judgment_order", []) or []),
        "basis_codes": list(getattr(match, "basis_codes", []) or []),
        "counter_signals": list(getattr(match, "counter_signals", []) or []),
    }


def _gyeokguk_single_action_material(
    analysis: AnalysisResult,
    match: Any,
    domain: Domain,
    center_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = analysis.chart_structure.gyeokguk_profile
    center_meta = dict(center_meta or {})
    pattern_label = PATTERN_LABELS.get(profile.primary_pattern, profile.primary_pattern)
    role_label = _ten_god_label(str(getattr(match, "acting_ten_god", "")))
    domain_name = _domain_label(domain)
    projection = _gyeokguk_projection_for_domain(match, domain)
    summary = str(getattr(match, "context_judgment_summary", "") or getattr(match, "expert_summary", "") or "").strip()
    excess = str(getattr(match, "excess_disease", "") or "").strip()
    deficiency = str(getattr(match, "deficiency_gap", "") or "").strip()
    protrusion = str(getattr(match, "protrusion_effect", "") or "").strip()
    rooting = str(getattr(match, "rooting_effect", "") or "").strip()
    hidden = str(getattr(match, "hidden_effect", "") or "").strip()
    effect_parts = [part for part in (projection, summary, excess, deficiency) if part]
    operation_axes = _gyeokguk_single_operation_axes(match)
    reality_axes = _gyeokguk_reality_axes(match)
    context_axes = _gyeokguk_context_axes(match)
    exact_ten_god_faces = _gyeokguk_exact_ten_god_faces(match)
    pattern_identity = {
        "pattern": profile.primary_pattern,
        "pattern_label": pattern_label,
        "pattern_center_ten_god": profile.primary_ten_god,
        "pattern_center_ten_god_label": _ten_god_label(profile.primary_ten_god),
        "month_command_ten_god": profile.month_command_ten_god,
        "month_command_ten_god_label": _ten_god_label(profile.month_command_ten_god),
        "pattern_family": profile.family,
        "formation_state": profile.formation_state,
        "clarity_state": profile.clarity_state,
    }
    action_identity = {
        **pattern_identity,
        "acting_ten_god": getattr(match, "acting_ten_god", ""),
        "acting_ten_god_label": role_label,
        "relation_to_pattern": getattr(match, "relation_to_pattern", ""),
        "action_key": getattr(match, "action_key", ""),
        "action_nature": getattr(match, "action_nature", ""),
        "center_effect": getattr(match, "center_effect", ""),
        "exact_ten_god_domains": exact_ten_god_faces["single_domains"],
    }
    sentence = _material_sentence(
        " ".join(
            [
                f"격국은 {pattern_label}을 중심으로 잡히며, {role_label} 작용이 {domain_name} 판단에 직접 걸립니다.",
                *effect_parts[:3],
            ]
        )
    )
    return {
        "layer": "gyeokguk_core_action",
        "label": f"{pattern_label} {role_label}",
        "priority": "primary",
        "source": "single",
        "center_selected": bool(center_meta),
        "center_rank": int(center_meta.get("rank", 0) or 0),
        "center_selection_score": int(center_meta.get("score", 0) or 0),
        "center_selection_components": dict(center_meta.get("selection_components", {}) or {}),
        "pattern": profile.primary_pattern,
        "action_identity": action_identity,
        "exact_profile_domain_basis": _gyeokguk_exact_profile_domain_basis(match),
        "exact_ten_god_faces": exact_ten_god_faces,
        "acting_ten_god": getattr(match, "acting_ten_god", ""),
        "acting_ten_god_label": role_label,
        "action_key": getattr(match, "action_key", ""),
        "action_nature": getattr(match, "action_nature", ""),
        "role_grade": getattr(match, "role_grade", ""),
        "presence_score": getattr(match, "presence_score", 0),
        "month_fit_state": getattr(match, "month_fit_state", ""),
        "context_judgment_state": getattr(match, "context_judgment_state", ""),
        "context_judgment_summary": summary,
        "context_judgment_path": list(getattr(match, "context_judgment_path", []) or []),
        "domain_projection": projection,
        "excess_disease": excess,
        "deficiency_gap": deficiency,
        "protrusion_effect": protrusion,
        "hidden_effect": hidden,
        "rooting_effect": rooting,
        "unrooted_effect": getattr(match, "unrooted_effect", ""),
        "timing_activation": getattr(match, "timing_activation", ""),
        "operation_axes": operation_axes,
        "reality_axes": reality_axes,
        "context_axes": context_axes,
        "event_manifestations": reality_axes["event_manifestations"],
        "visibility_axes": {
            "protrusion": protrusion,
            "rooting": rooting,
            "hidden": hidden,
            "unrooted": getattr(match, "unrooted_effect", ""),
            "position": reality_axes["position_context"],
            "branch_relation": reality_axes["branch_relation_context"],
        },
        "eventization_basis": _gyeokguk_eventization_basis(match, context_axes, reality_axes),
        "judgment_order": list(getattr(match, "judgment_order", []) or []),
        "sentence": sentence,
        "basis_codes": list(getattr(match, "basis_codes", []) or []),
        "mechanic_codes": [
            str(code)
            for code in list(getattr(match, "basis_codes", []) or [])
            if str(code).startswith("gyeokguk_single_mechanic:")
        ],
        "counter_signals": list(getattr(match, "counter_signals", []) or []),
    }


def _gyeokguk_dual_action_material(
    analysis: AnalysisResult,
    match: Any,
    domain: Domain,
    center_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = analysis.chart_structure.gyeokguk_profile
    center_meta = dict(center_meta or {})
    pattern_label = PATTERN_LABELS.get(profile.primary_pattern, profile.primary_pattern)
    first_label = _ten_god_label(str(getattr(match, "first_ten_god", "")))
    second_label = _ten_god_label(str(getattr(match, "second_ten_god", "")))
    pair_name = str(getattr(match, "exact_pair_name", "") or f"{first_label}-{second_label}")
    domain_name = _domain_label(domain)
    projection = _gyeokguk_projection_for_domain(match, domain)
    summary = str(getattr(match, "context_judgment_summary", "") or getattr(match, "expert_summary", "") or "").strip()
    effect = str(getattr(match, "exact_pair_effect", "") or "").strip()
    risk = str(getattr(match, "exact_pair_risk", "") or "").strip()
    disease_logic = str(getattr(match, "disease_medicine_logic", "") or "").strip()
    operation_axes = _gyeokguk_dual_operation_axes(match)
    reality_axes = _gyeokguk_reality_axes(match)
    context_axes = _gyeokguk_context_axes(match)
    exact_ten_god_faces = _gyeokguk_exact_ten_god_faces(match)
    pattern_identity = {
        "pattern": profile.primary_pattern,
        "pattern_label": pattern_label,
        "pattern_center_ten_god": profile.primary_ten_god,
        "pattern_center_ten_god_label": _ten_god_label(profile.primary_ten_god),
        "month_command_ten_god": profile.month_command_ten_god,
        "month_command_ten_god_label": _ten_god_label(profile.month_command_ten_god),
        "pattern_family": profile.family,
        "formation_state": profile.formation_state,
        "clarity_state": profile.clarity_state,
    }
    action_identity = {
        **pattern_identity,
        "first_ten_god": getattr(match, "first_ten_god", ""),
        "first_ten_god_label": first_label,
        "second_ten_god": getattr(match, "second_ten_god", ""),
        "second_ten_god_label": second_label,
        "pattern_ten_god": getattr(match, "pattern_ten_god", ""),
        "pattern_ten_god_label": _ten_god_label(str(getattr(match, "pattern_ten_god", ""))),
        "pattern_group": getattr(match, "pattern_group", ""),
        "first_relation_to_pattern": getattr(match, "first_relation_to_pattern", ""),
        "second_relation_to_pattern": getattr(match, "second_relation_to_pattern", ""),
        "first_to_second_relation": getattr(match, "first_to_second_relation", ""),
        "sequence_key": getattr(match, "sequence_key", ""),
        "chain_nature": getattr(match, "chain_nature", ""),
        "exact_pair_key": getattr(match, "exact_pair_key", ""),
        "exact_pair_category": getattr(match, "exact_pair_category", ""),
        "exact_pair_name": pair_name,
        "exact_pair_effect": effect,
        "exact_pair_risk": risk,
        "exact_pair_timing": getattr(match, "exact_pair_timing", ""),
        "first_then_second_activation": getattr(match, "first_then_second_activation", ""),
        "second_then_first_activation": getattr(match, "second_then_first_activation", ""),
        "first_exact_ten_god_domains": exact_ten_god_faces["first_domains"],
        "second_exact_ten_god_domains": exact_ten_god_faces["second_domains"],
    }
    sentence = _material_sentence(
        " ".join(
            [
                f"격국은 {pattern_label}을 중심으로 잡히며, {pair_name} 작용이 {domain_name} 판단의 핵심 연결부입니다.",
                *[part for part in (projection, summary, effect, risk) if part][:3],
            ]
        )
    )
    return {
        "layer": "gyeokguk_core_action",
        "label": f"{pattern_label} {pair_name}",
        "priority": "primary",
        "source": "dual",
        "center_selected": bool(center_meta),
        "center_rank": int(center_meta.get("rank", 0) or 0),
        "center_selection_score": int(center_meta.get("score", 0) or 0),
        "center_selection_components": dict(center_meta.get("selection_components", {}) or {}),
        "pattern": profile.primary_pattern,
        "action_identity": action_identity,
        "exact_profile_domain_basis": _gyeokguk_exact_profile_domain_basis(match),
        "exact_ten_god_faces": exact_ten_god_faces,
        "first_ten_god": getattr(match, "first_ten_god", ""),
        "first_ten_god_label": first_label,
        "second_ten_god": getattr(match, "second_ten_god", ""),
        "second_ten_god_label": second_label,
        "first_to_second_relation": getattr(match, "first_to_second_relation", ""),
        "sequence_key": getattr(match, "sequence_key", ""),
        "chain_grade": getattr(match, "chain_grade", ""),
        "exact_pair_key": getattr(match, "exact_pair_key", ""),
        "exact_pair_category": getattr(match, "exact_pair_category", ""),
        "exact_pair_name": pair_name,
        "exact_pair_effect": effect,
        "exact_pair_risk": risk,
        "exact_pair_timing": getattr(match, "exact_pair_timing", ""),
        "pattern_combination_state": getattr(match, "pattern_combination_state", ""),
        "primary_actor": getattr(match, "primary_actor", ""),
        "secondary_actor": getattr(match, "secondary_actor", ""),
        "disease_medicine_logic": disease_logic,
        "first_then_second_activation": getattr(match, "first_then_second_activation", ""),
        "second_then_first_activation": getattr(match, "second_then_first_activation", ""),
        "presence_score": getattr(match, "presence_score", 0),
        "month_fit_state": getattr(match, "month_fit_state", ""),
        "context_judgment_state": getattr(match, "context_judgment_state", ""),
        "context_judgment_summary": summary,
        "context_judgment_path": list(getattr(match, "context_judgment_path", []) or []),
        "domain_projection": projection,
        "timing_activation": getattr(match, "timing_activation", ""),
        "operation_axes": operation_axes,
        "reality_axes": reality_axes,
        "context_axes": context_axes,
        "event_manifestations": reality_axes["event_manifestations"],
        "interaction_judgment": dict(getattr(match, "interaction_judgment", {}) or {}),
        "visibility_interaction": dict(getattr(match, "visibility_interaction", {}) or {}),
        "visibility_axes": {
            "interaction": dict(getattr(match, "interaction_judgment", {}) or {}),
            "visibility": dict(getattr(match, "visibility_interaction", {}) or {}),
            "position": reality_axes["position_context"],
            "branch_relation": reality_axes["branch_relation_context"],
        },
        "eventization_basis": {
            **_gyeokguk_eventization_basis(match, context_axes, reality_axes),
            "judgment_path": context_axes["context_judgment_path"],
            "activation_order": {
                "first_then_second": getattr(match, "first_then_second_activation", ""),
                "second_then_first": getattr(match, "second_then_first_activation", ""),
            },
        },
        "judgment_order": list(getattr(match, "judgment_order", []) or []),
        "sentence": sentence,
        "basis_codes": list(getattr(match, "basis_codes", []) or []),
        "mechanic_codes": [
            str(code)
            for code in list(getattr(match, "basis_codes", []) or [])
            if str(code).startswith("gyeokguk_dual_mechanic:")
        ],
        "counter_signals": list(getattr(match, "counter_signals", []) or []),
    }


def _gyeokguk_core_action_materials(analysis: AnalysisResult, domain: Domain, limit: int = 3) -> list[dict[str, Any]]:
    profile = analysis.chart_structure.gyeokguk_profile
    center_index = _gyeokguk_global_center_action_index(analysis)
    candidates: list[tuple[int, str, Any, dict[str, int]]] = []
    for match in list(getattr(profile, "dual_ten_god_action_matches", []) or []):
        if _gyeokguk_action_matches_domain(match, domain):
            center_meta = center_index.get(_gyeokguk_match_identity("dual", match), {})
            center_bonus = 110 - int(center_meta.get("rank", 0) or 0) * 18 if center_meta else 0
            candidates.append((
                _gyeokguk_action_context_rank(match, source="dual")
                + _gyeokguk_domain_relevance_score(match, domain)
                + center_bonus,
                "dual",
                match,
                center_meta,
            ))
    for match in list(getattr(profile, "ten_god_action_matches", []) or []):
        if _gyeokguk_action_matches_domain(match, domain):
            center_meta = center_index.get(_gyeokguk_match_identity("single", match), {})
            center_bonus = 110 - int(center_meta.get("rank", 0) or 0) * 18 if center_meta else 0
            candidates.append((
                _gyeokguk_action_context_rank(match, source="single")
                + _gyeokguk_domain_relevance_score(match, domain)
                + center_bonus,
                "single",
                match,
                center_meta,
            ))
    if not candidates:
        for match in list(getattr(profile, "dual_ten_god_action_matches", []) or []):
            center_meta = center_index.get(_gyeokguk_match_identity("dual", match), {})
            if center_meta:
                candidates.append((int(center_meta.get("score", 0) or 0), "dual", match, center_meta))
        for match in list(getattr(profile, "ten_god_action_matches", []) or []):
            center_meta = center_index.get(_gyeokguk_match_identity("single", match), {})
            if center_meta:
                candidates.append((int(center_meta.get("score", 0) or 0), "single", match, center_meta))
    candidates.sort(key=lambda item: (-item[0], 0 if item[1] == "dual" else 1))

    materials: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    deferred_center_candidates: list[tuple[int, str, Any, dict[str, int]]] = []
    selected_center_count = 0

    def append_material(source: str, match: Any, center_meta: dict[str, int]) -> None:
        if source == "dual":
            materials.append(_gyeokguk_dual_action_material(analysis, match, domain, center_meta))
        else:
            materials.append(_gyeokguk_single_action_material(analysis, match, domain, center_meta))

    for score, source, match, center_meta in candidates:
        key = (
            source,
            str(getattr(match, "exact_pair_category", "") or getattr(match, "action_key", "")),
        )
        if key in seen:
            continue
        if center_meta and selected_center_count >= 1:
            deferred_center_candidates.append((score, source, match, center_meta))
            continue
        seen.add(key)
        append_material(source, match, center_meta)
        if center_meta:
            selected_center_count += 1
        if len(materials) >= limit:
            break
    for _, source, match, center_meta in deferred_center_candidates:
        if len(materials) >= limit:
            break
        key = (
            source,
            str(getattr(match, "exact_pair_category", "") or getattr(match, "action_key", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        append_material(source, match, center_meta)
    return materials


def _gyeokguk_flow_action_material(
    analysis: AnalysisResult,
    match: Any,
    domain: Domain,
    source: str,
    center_meta: dict[str, Any] | None,
    target_years: list[int],
) -> dict[str, Any]:
    if source == "dual":
        material = _gyeokguk_dual_action_material(analysis, match, domain, center_meta)
    else:
        material = _gyeokguk_single_action_material(analysis, match, domain, center_meta)

    label = str(material.get("label") or "")
    domain_name = _domain_label(domain)
    timing_activation = str(getattr(match, "timing_activation", "") or "").strip()
    event_manifestations = dict(getattr(match, "event_manifestations", {}) or {})
    flow_basis = {
        "target_years": list(target_years),
        "timing_activation": timing_activation,
        "luck_activation_event": str(event_manifestations.get("luck_activation", "") or "").strip(),
        "domain_projection": _gyeokguk_projection_for_domain(match, domain),
        "judgment_order": list(getattr(match, "judgment_order", []) or []),
        "event_manifestations": event_manifestations,
    }
    if source == "dual":
        flow_basis.update(
            {
                "exact_pair_timing": str(getattr(match, "exact_pair_timing", "") or "").strip(),
                "first_then_second_activation": str(getattr(match, "first_then_second_activation", "") or "").strip(),
                "second_then_first_activation": str(getattr(match, "second_then_first_activation", "") or "").strip(),
            }
        )

    basis_codes = list(material.get("basis_codes", []) or [])
    basis_codes.extend(
        [
            "gyeokguk_flow_action",
            f"gyeokguk_flow_action_source:{source}",
            f"gyeokguk_flow_action_domain:{domain}",
        ]
    )
    basis_codes.extend(f"gyeokguk_flow_action_target_year:{year}" for year in target_years)

    sentence = _material_sentence(
        f"대운·세운에서 {label} 작용이 현실화되는 시기에는 {domain_name} 판단에서 {timing_activation}"
    )
    material.update(
        {
            "layer": "gyeokguk_flow_action",
            "priority": "timing",
            "flow_selected": True,
            "target_years": list(target_years),
            "flow_activation_basis": flow_basis,
            "sentence": sentence,
            "basis_codes": list(dict.fromkeys(code for code in basis_codes if code)),
        }
    )
    return material


def _gyeokguk_flow_action_materials(analysis: AnalysisResult, domain: Domain, limit: int = 2) -> list[dict[str, Any]]:
    target_years = [
        int(year)
        for year in list(analysis.trace.get("target_years", []) or [])
        if isinstance(year, int)
    ]
    if not target_years:
        return []

    profile = analysis.chart_structure.gyeokguk_profile
    center_index = _gyeokguk_global_center_action_index(analysis)
    candidates: list[tuple[int, str, Any, dict[str, Any]]] = []

    def flow_score(match: Any, source: str, center_meta: dict[str, Any]) -> int:
        event_manifestations = dict(getattr(match, "event_manifestations", {}) or {})
        timing_activation = str(getattr(match, "timing_activation", "") or "").strip()
        timing_score = 24 if timing_activation else 0
        luck_event_score = 18 if str(event_manifestations.get("luck_activation", "") or "").strip() else 0
        center_bonus = 95 - int(center_meta.get("rank", 0) or 0) * 18 if center_meta else 0
        return (
            _gyeokguk_action_context_rank(match, source=source)
            + _gyeokguk_domain_relevance_score(match, domain)
            + timing_score
            + luck_event_score
            + center_bonus
        )

    for match in list(getattr(profile, "dual_ten_god_action_matches", []) or []):
        if not _gyeokguk_action_matches_domain(match, domain):
            continue
        center_meta = center_index.get(_gyeokguk_match_identity("dual", match), {})
        candidates.append((flow_score(match, "dual", center_meta), "dual", match, center_meta))
    for match in list(getattr(profile, "ten_god_action_matches", []) or []):
        if not _gyeokguk_action_matches_domain(match, domain):
            continue
        center_meta = center_index.get(_gyeokguk_match_identity("single", match), {})
        candidates.append((flow_score(match, "single", center_meta), "single", match, center_meta))

    if not candidates:
        return []

    candidates.sort(key=lambda item: (-item[0], 0 if item[1] == "dual" else 1))
    materials: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for _, source, match, center_meta in candidates:
        key = (
            source,
            str(getattr(match, "exact_pair_category", "") or getattr(match, "action_key", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        materials.append(_gyeokguk_flow_action_material(analysis, match, domain, source, center_meta, target_years))
        if len(materials) >= limit:
            break
    return materials


def _domain_judgment_shared_materials(
    analysis: AnalysisResult,
    domain: Domain,
) -> dict[str, Any]:
    """Build the chart-level judgment layers that every packet in a domain shares."""

    before_pattern = [
        _month_command_material(analysis, domain),
        _month_governance_material(analysis, domain),
    ]
    after_pattern: list[dict[str, Any]] = []
    after_pattern.extend(_cycle_regulation_materials(analysis, domain))
    after_pattern.append(_element_material(analysis, domain))
    after_pattern.append(_strength_material(analysis, domain))
    after_pattern.extend(_branch_foundation_materials(analysis, domain))
    after_pattern.extend(_hidden_stem_materials(analysis, domain))
    after_pattern.append(_ten_god_material(analysis, domain))
    after_pattern.extend(_gyeokguk_core_action_materials(analysis, domain))
    after_pattern.extend(_gyeokguk_flow_action_materials(analysis, domain))
    after_pattern.extend(_branch_relation_materials(analysis, domain))

    after_flow: list[dict[str, Any]] = []
    after_flow.extend(_element_combo_materials(analysis, domain))
    after_flow.extend(_stem_reception_materials(analysis, domain))
    after_flow.extend(_integrated_materials(analysis, domain))
    return {
        "before_pattern": before_pattern,
        "after_pattern": after_pattern,
        "after_flow": after_flow,
        "cycle_principle_matrix": _cycle_principle_matrix_context(analysis, domain),
    }


def build_domain_judgment_context(
    analysis: AnalysisResult,
    packet: EventPacket,
    *,
    shared_materials_by_domain: dict[Domain, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a report-ready judgment context for one ProductOutputItem."""

    domain = packet.domain
    shared = None
    if shared_materials_by_domain is not None:
        shared = shared_materials_by_domain.get(domain)
        if shared is None:
            shared = _domain_judgment_shared_materials(analysis, domain)
            shared_materials_by_domain[domain] = shared
    if shared is None:
        shared = _domain_judgment_shared_materials(analysis, domain)

    materials: list[dict[str, Any]] = [
        dict(material)
        for material in list(shared.get("before_pattern") or [])
    ]
    materials.append(_pattern_need_material(analysis, domain, packet))
    materials.extend(
        dict(material)
        for material in list(shared.get("after_pattern") or [])
    )
    materials.extend(_flow_branch_relation_materials(analysis, packet, domain))
    materials.extend(
        dict(material)
        for material in list(shared.get("after_flow") or [])
    )
    materials.append(_fortune_material(analysis, packet))
    materials = _dedupe_materials(materials)

    primary_sentences = [m["sentence"] for m in materials if m.get("priority") == "primary"][:5]
    support_sentences = [m["sentence"] for m in materials if m.get("priority") == "support"][:4]
    timing_sentences = [m["sentence"] for m in materials if m.get("priority") == "timing"][:2]
    conclusion = _core_conclusion(packet)
    pattern_conclusions = _pattern_conclusion_sentences(domain, materials)
    reality_conclusions = _reality_conclusion_sentences(domain, materials)
    fortune_conclusions = _fortune_conclusion_sentences(analysis, packet)
    cycle_adjudication = _build_cycle_adjudication_context(domain, materials, packet)
    cycle_principle_matrix = dict(shared.get("cycle_principle_matrix") or {})

    return {
        "version": JUDGMENT_CONTEXT_VERSION,
        "domain": domain,
        "domain_label": _domain_label(domain),
        "period_label": packet.period_label,
        "sub_event_type": packet.sub_event_type,
        "output_targets": list(DOMAIN_OUTPUT_TARGETS[domain]),
        "core_conclusion": conclusion,
        "score_judgment": _score_judgment(packet),
        "material_layers": materials,
        "material_coverage": _material_coverage(materials),
        "cycle_adjudication": cycle_adjudication,
        "cycle_principle_matrix": cycle_principle_matrix,
        "primary_sentences": primary_sentences,
        "support_sentences": support_sentences,
        "timing_sentences": timing_sentences,
        "report_sentences": {
            "opening": conclusion,
            "pattern_outcome": pattern_conclusions["outcome"],
            "pattern_pressure": pattern_conclusions["pressure"],
            "pattern_mobile": pattern_conclusions["mobile"],
            "reality_front": reality_conclusions["front"],
            "reality_mobile": reality_conclusions["mobile"],
            "month_outcome": reality_conclusions["month"],
            "branch_outcome": reality_conclusions["branch"],
            "hidden_outcome": reality_conclusions["hidden"],
            "relation_outcome": reality_conclusions["relation"],
            "fortune_outcome": fortune_conclusions["outcome"],
            "fortune_mobile": fortune_conclusions["mobile"],
            "fortune_daeun": fortune_conclusions["daeun"],
            "native_basis": primary_sentences[0] if primary_sentences else "",
            "reality_basis": primary_sentences[1] if len(primary_sentences) > 1 else "",
            "cycle_basis": next((m["sentence"] for m in materials if m.get("layer") == "cycle_regulation"), ""),
            "cycle_adjudication": str(cycle_adjudication.get("primary_cycle", {}).get("adjudication") or ""),
            "element_basis": next((m["sentence"] for m in materials if m.get("layer") == "element_distribution"), ""),
            "ten_god_basis": next((m["sentence"] for m in materials if m.get("layer") == "ten_god_distribution"), ""),
            "gyeokguk_action_basis": next((m["sentence"] for m in materials if m.get("layer") == "gyeokguk_core_action"), ""),
            "gyeokguk_flow_basis": next((m["sentence"] for m in materials if m.get("layer") == "gyeokguk_flow_action"), ""),
            "branch_basis": next((m["sentence"] for m in materials if m.get("layer") == "branch_relations"), ""),
            "flow_branch_basis": next((m["sentence"] for m in materials if m.get("layer") == "flow_branch_relations"), ""),
            "fortune_basis": next((m["sentence"] for m in materials if m.get("layer") == "fortune_activation"), ""),
        },
    }
