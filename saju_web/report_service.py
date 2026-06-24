"""Stable adapter between the saju engines and the web UI.

The UI should call this module instead of importing the birth or analysis
engines directly. That keeps future engine, product, and writing patches from
leaking into page-level code.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from math import ceil
import re
from typing import Any

from saju_analysis_engine import (
    analyze_chart,
    build_product_output,
    build_timing_decision_payload_from_flows,
)
from saju_analysis_engine.branch_reality_profiles import (
    branch_domain_texture,
    branch_position_texture,
)
from saju_analysis_engine.premium_category_topics import (
    premium_category_contract,
    premium_content_plan_items,
    premium_topic_definition,
    premium_topic_items,
)
from saju_birth_engine import BirthInput, BirthChartResult, build_birth_chart
from saju_birth_engine.pillars import year_pillar_for_gregorian_year


SUPPORTED_TIERS: set[str] = {"free", "basic", "premium"}
SUPPORTED_GENDERS: set[str] = {"male", "female", "unknown"}
SUPPORTED_CALENDAR_TYPES: set[str] = {"solar"}
SUPPORTED_RELATIONSHIP_STATUSES: set[str] = {
    "single",
    "interested",
    "dating",
    "long_term",
    "preparing_marriage",
    "married",
    "unknown",
}

CUSTOMER_COPY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("돈이 들어오는 방식과 손에 남는 방식", "수익 발생 방식과 자산화 방식"),
    ("수입의 크기보다 손에 남는 돈", "수입 규모보다 자산화되는 금액"),
    ("들어오는 돈과 손에 남는 돈", "수입 규모와 자산화되는 금액"),
    ("돈이 들어오는 자리와 손에 남는 돈", "수익 발생 지점과 자산화되는 금액"),
    ("손에 남는 돈", "실질 수익"),
    ("손에 남는 금액", "실질 금액"),
    ("손에 남는 수입", "실질 수입"),
    ("손에 남는 몫", "실질 몫"),
    ("손에 남는 방식", "자산으로 남기는 방식"),
    ("기운이 살아나고", "활력이 붙고"),
    ("크게 잡힙니다", "뚜렷해집니다"),
    ("분명하게 잡히는", "분명하게 형성되는"),
    ("기준이 처음 잡히는", "기준이 처음 형성되는"),
    ("실제 행동으로 힘을 보태는", "실질적인 지원을 하는"),
    ("실제 행동으로 힘을 보태는 사람", "실질적인 지원을 하는 사람"),
    ("말로 넘기면", "구두 약속으로 처리하면"),
    ("오래 가져가지만", "오래 유지하지만"),
    ("중심을 잡고", "상황의 중심을 세우고"),
    ("결론이 강하게 나옵니다", "판정이 선명합니다"),
    ("판단이 강합니다", "판단이 뚜렷합니다"),
    ("공동 자금 기준 필요", "지분·명의 안정성"),
    ("정산 기준 필요", "수익 배분 안정성"),
    ("좋은 연도와 주의 연도가 뚜렷합니다", "좋은 연도와 주의 연도가 따로 드러납니다"),
    ("맡은 일의 결과가 보수와 계약 조건으로 확정됩니다", "일의 대가가 보수로 분명히 잡힙니다"),
    ("직업운은 성과가 평가와 보상으로 확정되는 힘이 강합니다", "직업운은 결과가 직함과 평판으로 굳어집니다"),
    ("공식 평가를 확보합니다", "공식 평가가 직책 상승으로 이어집니다"),
    ("말보다 실질적인 지원을 하는 사람", "실제 소개를 해주는 사람"),
    ("성패가 갈립니다", "성패가 정해집니다"),
    ("길흉이 다시 갈립니다", "길흉을 다시 판정합니다"),
    ("길흉은 이 기준 위에서 다시 갈립니다", "길흉은 이 기준 위에서 다시 판정합니다"),
    ("좋은 해와 주의할 해가 같은 영역에서 갈립니다", "상승 연도와 주의 연도가 같은 영역에서 드러납니다"),
    ("좋은 해와 주의할 해가 서로 다른 영역으로 갈립니다", "상승 연도와 주의 연도가 서로 다른 영역으로 드러납니다"),
    ("좋은 해와 주의할 해가 분명하게 갈립니다", "상승 연도와 주의 연도가 분명하게 드러납니다"),
    ("판정이 더 세밀하게 갈립니다", "판정이 더 세밀해집니다"),
    ("강점과 손실 지점이 뚜렷하게 갈립니다", "강점과 손실 지점이 뚜렷하게 나뉩니다"),
    ("함께 강하게 잡힙니다", "함께 뚜렷합니다"),
    ("강하게 잡힙니다", "뚜렷합니다"),
    ("결혼은 생활 기준이 맞을 때 안정됩니다.", "결혼은 감정보다 생활 기준에서 먼저 시험을 받습니다."),
    ("할 수 있습니다", "합니다"),
    ("될 수 있습니다", "됩니다"),
    ("생길 수 있습니다", "생깁니다"),
    ("커질 수 있습니다", "커집니다"),
    ("드러날 수 있습니다", "드러납니다"),
    ("이어질 수 있습니다", "이어집니다"),
    ("남을 수 있습니다", "남습니다"),
    ("부딪힐 수 있습니다", "부딪힙니다"),
    ("약해질 수 있습니다", "약해집니다"),
    ("바뀔 수 있습니다", "바뀝니다"),
    ("흔들릴 수 있습니다", "흔들립니다"),
    ("식을 수 있습니다", "식습니다"),
    ("거칠어질 수 있습니다", "거칠어집니다"),
    ("길어질 수 있습니다", "길어집니다"),
    ("늦어질 수 있습니다", "늦어집니다"),
    ("놓칠 수 있습니다", "놓칩니다"),
    ("돌아설 수 있습니다", "돌아섭니다"),
    ("돌아올 수 있습니다", "돌아옵니다"),
    ("흐려질 수 있습니다", "흐려집니다"),
    ("받아들일 수 있습니다", "받아들여집니다"),
    ("깎일 수 있습니다", "깎입니다"),
    ("살아납니다", "분명해집니다"),
    ("중요합니다", "핵심입니다"),
    ("봐야 합니다", "확인해야 합니다"),
        ("편이 좋습니다", "편이 낫습니다"),
)

PILLAR_DISPLAY_ORDER = (
    ("hour", "시"),
    ("day", "일"),
    ("month", "월"),
    ("year", "년"),
)
FIXED_SERVICE_CITY = "서울"
FIXED_SERVICE_CITY_LABEL = "서울 기준"
HOUR_RULE_LABEL = "자시 23:30~01:30 기준"
BRANCH_HOUR_REPRESENTATIVE_TIMES: dict[str, tuple[int, int]] = {
    "ja": (0, 30),
    "chuk": (2, 30),
    "in": (4, 30),
    "myo": (6, 30),
    "jin": (8, 30),
    "sa": (10, 30),
    "o": (12, 30),
    "mi": (14, 30),
    "sin": (16, 30),
    "yu": (18, 30),
    "sul": (20, 30),
    "hae": (22, 30),
}

STEM_HANJA_BY_KEY: dict[str, str] = {
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

TEN_GOD_LABEL_BY_KEY: dict[str, str] = {
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

BRANCH_HANJA_BY_KEY: dict[str, str] = {
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

ELEMENT_LABEL_BY_KEY: dict[str, str] = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

REGULAR_PATTERN_LABEL_BY_KEY: dict[str, str] = {
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
}

MONTH_HIDDEN_PHASE_LABEL_BY_KEY: dict[str, str] = {
    "yeogi": "여기(餘氣)",
    "junggi": "중기(中氣)",
    "jeonggi": "정기(正氣)",
}

DOMAIN_LABEL_BY_KEY: dict[str, str] = {
    "money": "재물",
    "career": "직업",
    "love": "연애·관계",
    "marriage": "결혼·가정",
    "personality": "성격",
    "social": "사회",
    "social_role": "사회",
    "honor": "명예",
    "parents": "부모·윗사람",
    "self": "자기 기준",
    "output": "결과물",
    "children": "자녀·후반",
    "late_life": "후반",
    "background": "초기 환경",
    "network": "대인관계",
    "family_origin": "가족 배경",
    "home": "가정",
    "future": "후반",
}

POSITION_KEY_BY_LABEL: dict[str, str] = {
    "연지": "year",
    "월지": "month",
    "일지": "day",
    "시지": "hour",
}

POSITION_REALITY_LABEL: dict[str, str] = {
    "year": "초년 배경과 바깥 관계",
    "month": "사회적 자리와 직업 환경",
    "day": "가까운 관계와 결혼 생활",
    "hour": "후반 성취와 장기 결과",
}

DOMAIN_BRANCH_TEXTURE_MAP: dict[str, str] = {
    "money": "money",
    "career": "career",
    "honor": "career",
    "social": "career",
    "love": "love",
    "marriage": "marriage",
}

BRANCH_READING_BY_LABEL: dict[str, str] = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}

PERSONALITY_STEM_PROFILE: dict[str, dict[str, str]] = {
    "甲": {
        "lead": "당신은 스스로 납득한 일에는 강하게 밀고 가는 사람입니다.",
        "core": "기본 성격: 큰 방향을 정하면 쉽게 꺾이지 않습니다.",
        "emotion": "감정 처리: 서운함을 바로 드러내기보다 마음속 기준으로 상대를 평가합니다.",
        "social": "사람 관계: 답답한 사람을 오래 기다리기보다 스스로 길을 만들려 합니다.",
        "strength": "강점: 시작을 두려워하지 않고, 책임질 일이 생기면 앞에 섭니다.",
        "weakness": "약점: 자기 판단이 선 뒤에는 타인의 속도를 답답하게 느낍니다.",
    },
    "乙": {
        "lead": "당신은 부드럽게 보이지만 속으로는 기준이 분명한 사람입니다.",
        "core": "기본 성격: 분위기를 읽고 사람 사이의 미묘한 변화를 빨리 알아챕니다.",
        "emotion": "감정 처리: 싫은 감정을 크게 터뜨리기보다 오래 기억합니다.",
        "social": "사람 관계: 겉으로는 맞춰주지만 속으로는 가까이 둘 사람을 분명히 가립니다.",
        "strength": "강점: 관계를 조율하고, 복잡한 상황에서도 빠져나갈 길을 찾습니다.",
        "weakness": "약점: 직접 부딪히기보다 돌려 말하다가 오해가 길어집니다.",
    },
    "丙": {
        "lead": "당신은 존재감이 드러날 때 판단과 표현이 더 분명해지는 사람입니다.",
        "core": "기본 성격: 마음에 든 일은 빠르게 반응하고, 답답한 분위기를 오래 견디지 못합니다.",
        "emotion": "감정 처리: 감정이 표정과 말투에 빨리 묻어납니다.",
        "social": "사람 관계: 인정받고 존중받는 자리에서 더 적극적으로 움직입니다.",
        "strength": "강점: 사람 앞에서 분위기를 살리고, 자기 의견을 분명히 전달합니다.",
        "weakness": "약점: 무시당한다고 느끼면 필요 이상으로 강하게 반응합니다.",
    },
    "丁": {
        "lead": "당신은 겉보다 속의 온도가 훨씬 깊은 사람입니다.",
        "core": "기본 성격: 조용히 관찰하다가 확신이 서면 집중력이 강해집니다.",
        "emotion": "감정 처리: 사소한 말과 태도에도 마음이 오래 움직입니다.",
        "social": "사람 관계: 넓은 관계보다 마음이 통하는 소수의 관계를 더 신뢰합니다.",
        "strength": "강점: 사람의 마음과 상황의 결을 섬세하게 읽습니다.",
        "weakness": "약점: 마음이 상해도 바로 말하지 않아 상대가 뒤늦게 알아차립니다.",
    },
    "戊": {
        "lead": "당신은 판단의 중심이 분명한 사람입니다.",
        "core": "기본 성격: 큰 틀과 책임을 먼저 생각하고, 한 번 맡은 일은 쉽게 놓지 않습니다.",
        "emotion": "감정 처리: 감정보다 현실적으로 감당 가능한 일인지 먼저 따집니다.",
        "social": "사람 관계: 한 번 믿은 관계는 오래 유지하지만, 선을 넘는 사람에게는 단호합니다.",
        "strength": "강점: 복잡한 상황에서도 일을 안정적으로 정리합니다.",
        "weakness": "약점: 변화가 빠른 상황에서는 자기 기준이 완고하게 드러납니다.",
    },
    "己": {
        "lead": "당신은 세세한 현실을 그냥 넘기지 않는 사람입니다.",
        "core": "기본 성격: 작은 조건, 생활의 불편, 사람의 태도 변화를 잘 살핍니다.",
        "emotion": "감정 처리: 불안이 생기면 먼저 상황을 정리하고 확인하려 합니다.",
        "social": "사람 관계: 가까운 사람에게는 챙김이 많지만, 반복되는 부담에는 예민해집니다.",
        "strength": "강점: 실무 감각과 생활 감각이 좋고, 빈틈을 빨리 찾아냅니다.",
        "weakness": "약점: 걱정이 많아지면 결정을 미루고 사소한 문제를 크게 봅니다.",
    },
    "庚": {
        "lead": "당신은 아닌 것을 오래 참지 않는 사람입니다.",
        "core": "기본 성격: 판단이 서면 단순하고 빠르게 정리하려 합니다.",
        "emotion": "감정 처리: 감정보다 사실과 책임을 먼저 따집니다.",
        "social": "사람 관계: 솔직함을 중시하고, 말이 돌려지는 관계를 피곤해합니다.",
        "strength": "강점: 문제를 정면으로 다루고, 불필요한 것을 정리하는 결단력이 있습니다.",
        "weakness": "약점: 말이 곧고 빠르게 나가 상대에게 차갑게 보입니다.",
    },
    "辛": {
        "lead": "당신은 기준이 섬세하고 자존감이 분명한 사람입니다.",
        "core": "기본 성격: 말, 태도, 결과물의 완성도를 그냥 넘기지 않습니다.",
        "emotion": "감정 처리: 불편함을 크게 드러내지 않아도 속으로는 정확히 판단합니다.",
        "social": "사람 관계: 무례함과 품위 없는 태도에 민감합니다.",
        "strength": "강점: 세부를 다듬어 일의 수준을 끌어올리는 눈이 있습니다.",
        "weakness": "약점: 스스로와 타인에게 요구하는 기준이 높아 쉽게 피로해집니다.",
    },
    "壬": {
        "lead": "당신은 한곳에 오래 묶이면 장점이 흐려지는 사람입니다.",
        "core": "기본 성격: 생각의 폭이 넓고, 상황을 여러 방향으로 동시에 봅니다.",
        "emotion": "감정 처리: 마음이 복잡해지면 거리를 두고 혼자 정리하려 합니다.",
        "social": "사람 관계: 자유를 존중해주는 사람에게 오래 마음을 둡니다.",
        "strength": "강점: 변화에 강하고, 큰 그림을 보며 새로운 기회를 찾습니다.",
        "weakness": "약점: 선택지가 많아질수록 결정을 미루고 한곳에 오래 머물기 어려워합니다.",
    },
    "癸": {
        "lead": "당신은 조용히 관찰하면서 속으로 깊게 계산하는 사람입니다.",
        "core": "기본 성격: 겉으로는 차분하지만 마음속에서는 여러 경우를 오래 따집니다.",
        "emotion": "감정 처리: 쉽게 믿지 않지만, 한 번 마음을 주면 오래 기억합니다.",
        "social": "사람 관계: 큰 소리보다 미묘한 태도와 말의 뉘앙스를 더 믿습니다.",
        "strength": "강점: 사람의 의도와 상황의 빈틈을 섬세하게 읽습니다.",
        "weakness": "약점: 생각이 깊어질수록 말이 늦어지고, 상대가 마음을 알기 어려워집니다.",
    },
}

PERSONALITY_MONTH_BRANCH_MODIFIER: dict[str, tuple[str, str]] = {
    "寅": ("외부 태도", "새 일을 시작하고 사람 앞에 나설수록 더 적극적으로 움직입니다."),
    "卯": ("외부 태도", "사람의 반응과 미묘한 거리감에 민감하게 반응합니다."),
    "辰": ("외부 태도", "현실 조건을 확인한 뒤 움직이려는 신중함이 강합니다."),
    "巳": ("외부 태도", "인정받는 자리와 표현할 기회가 생기면 속도가 빨라집니다."),
    "午": ("외부 태도", "자존심과 표현 욕구가 강해져 무시당하는 상황을 오래 견디기 어렵습니다."),
    "未": ("외부 태도", "가까운 사람과 생활 문제에 책임을 많이 느낍니다."),
    "申": ("외부 태도", "일을 평가하고 정리하는 기준이 분명해집니다."),
    "酉": ("외부 태도", "말과 행동의 품위, 결과물의 완성도에 민감합니다."),
    "戌": ("외부 태도", "한번 정한 약속과 책임을 오래 감당하는 성격이 강해집니다."),
    "亥": ("외부 태도", "혼자 생각을 정리하는 시간이 있어야 마음이 안정됩니다."),
    "子": ("외부 태도", "속으로 계산하고 관찰한 뒤 움직이는 신중함이 강합니다."),
    "丑": ("외부 태도", "당장 드러나는 감정보다 현실적인 안전과 지속성을 먼저 따집니다."),
}

PERSONALITY_TEN_GOD_TRAITS: dict[str, tuple[str, str]] = {
    "비견": ("반복 태도", "자기 기준이 강해 남의 말에 쉽게 끌려가지 않습니다."),
    "겁재": ("반복 태도", "경쟁이 붙으면 물러서기보다 직접 부딪히는 쪽입니다."),
    "식신": ("반복 태도", "편안한 방식으로 꾸준히 결과를 내는 데 강합니다."),
    "상관": ("반복 태도", "부당하다고 느끼면 말과 태도에서 바로 드러납니다."),
    "편재": ("반복 태도", "사람과 기회를 빠르게 읽고 실익을 계산합니다."),
    "정재": ("반복 태도", "약속, 금액, 책임처럼 분명한 기준을 편하게 느낍니다."),
    "편관": ("반복 태도", "압박이 생기면 긴장하지만 동시에 승부욕도 강해집니다."),
    "정관": ("반복 태도", "질서와 책임을 의식해 쉽게 선을 넘지 않습니다."),
    "편인": ("반복 태도", "남들이 그냥 넘기는 말과 분위기를 깊게 해석합니다."),
    "정인": ("반복 태도", "확실한 근거와 보호받는 기준이 있을 때 마음이 안정됩니다."),
}

PERSONALITY_STEM_ELEMENT: dict[str, str] = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

PERSONALITY_BRANCH_ELEMENT: dict[str, str] = {
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
    "子": "water",
    "丑": "earth",
}

PERSONALITY_VALUE_AXIS_COPY: dict[str, dict[str, str]] = {
    "조화": {
        "label": "관계 균형",
        "lead_mid": "사람 사이의 균형을 크게 의식하고",
        "lead_final": "사람 사이의 균형을 크게 의식하는",
        "summary": "서로 다른 입장을 맞추고 관계의 균형을 지키려는 마음이 큽니다.",
        "low": "사람을 맞추는 일보다 자신의 기준과 결과를 먼저 앞세웁니다.",
    },
    "흥미": {
        "label": "경험 확장",
        "lead_mid": "새로운 경험에서 활력이 붙고",
        "lead_final": "새로운 경험에서 활력이 붙는",
        "summary": "새로운 기회에서 실익을 빠르게 계산합니다.",
        "low": "즉흥적인 즐거움보다 책임, 안정, 실익을 먼저 따집니다.",
    },
    "독립": {
        "label": "자기 결정",
        "lead_mid": "스스로 결정할 때 장점이 분명해지고",
        "lead_final": "스스로 결정할 때 장점이 분명해지는",
        "summary": "스스로 선택할 수 있는 환경에서 장점이 분명하게 드러납니다.",
        "low": "혼자 밀고 가는 일보다 기준이 정해진 자리에서 안정됩니다.",
    },
    "배려": {
        "label": "책임 배려",
        "lead_mid": "가까운 사람의 사정을 쉽게 외면하지 못하고",
        "lead_final": "가까운 사람의 사정을 쉽게 외면하지 못하는",
        "summary": "가까운 사람의 사정과 필요를 쉽게 외면하지 못합니다.",
        "low": "정 때문에 끌려가기보다 손익과 책임을 먼저 가릅니다.",
    },
    "지위": {
        "label": "사회적 인정",
        "lead_mid": "인정받는 자리에서 태도가 달라지고",
        "lead_final": "인정받는 자리에서 태도가 달라지는",
        "summary": "인정, 영향력, 역할의 크기에 민감하게 반응합니다.",
        "low": "겉으로 보이는 명예보다 실제 안정과 생활의 효율을 더 봅니다.",
    },
    "안전": {
        "label": "안정 확보",
        "lead_mid": "위험을 줄일 방법을 먼저 가늠하고",
        "lead_final": "위험을 줄일 방법을 먼저 가늠하는",
        "summary": "위험을 줄이고 오래 유지되는 선택을 선호합니다.",
        "low": "안정만 붙드는 삶보다 변화와 성취 쪽으로 마음이 움직입니다.",
    },
    "성취": {
        "label": "목표 성취",
        "lead_mid": "목표와 결과가 분명할수록 집중하고",
        "lead_final": "목표와 결과가 분명할수록 집중하는",
        "summary": "목표와 결과가 분명할 때 집중력이 강해집니다.",
        "low": "성과 경쟁보다 관계의 안정이나 생활의 균형을 우선합니다.",
    },
    "질서": {
        "label": "절차 신뢰",
        "lead_mid": "약속과 기준이 분명해야 편안해지고",
        "lead_final": "약속과 기준이 분명해야 편안해지는",
        "summary": "약속과 절차가 분명할수록 마음이 안정됩니다.",
        "low": "정해진 절차보다 현장 판단과 개인의 재량을 더 믿습니다.",
    },
}

PERSONALITY_TEN_GOD_VALUE_WEIGHTS: dict[str, dict[str, int]] = {
    "비견": {"독립": 5, "성취": 2, "조화": 1},
    "겁재": {"독립": 4, "지위": 3, "성취": 2},
    "식신": {"흥미": 4, "안전": 3, "배려": 1},
    "상관": {"흥미": 4, "독립": 3, "성취": 2},
    "편재": {"흥미": 3, "지위": 3, "성취": 2, "독립": 1},
    "정재": {"안전": 4, "질서": 3, "성취": 1},
    "편관": {"성취": 4, "지위": 3, "질서": 2},
    "정관": {"질서": 4, "지위": 3, "안전": 2},
    "편인": {"독립": 3, "안전": 2, "흥미": 1},
    "정인": {"안전": 4, "조화": 2, "질서": 2, "배려": 1},
}

PERSONALITY_ELEMENT_VALUE_WEIGHTS: dict[str, dict[str, int]] = {
    "wood": {"독립": 3, "조화": 2, "성취": 1},
    "fire": {"흥미": 3, "지위": 2, "성취": 2},
    "earth": {"안전": 3, "배려": 2, "질서": 1},
    "metal": {"질서": 3, "성취": 2, "지위": 1},
    "water": {"조화": 2, "흥미": 2, "독립": 1},
}

PERSONALITY_DEFENSE_COPY: dict[str, str] = {
    "정면 대응형": "압박을 받으면 태도로 선을 분명히 긋습니다. 불공정한 상황은 오래 참고 넘기지 않습니다.",
    "거리 확보형": "압박을 받으면 먼저 거리를 두고 혼자 판단합니다. 마음이 복잡할수록 설명이 늦어집니다.",
    "기준 확인형": "압박을 받으면 책임 범위를 먼저 세웁니다. 감정보다 약속과 절차에 무게를 둡니다.",
}

PERSONALITY_EMOTION_COPY: dict[str, str] = {
    "확장형": "기회와 사람을 먼저 보며 움직입니다. 낯선 자리에서도 반응이 빠릅니다.",
    "긴장 관리형": "불안이 생기면 금전, 약속, 책임 범위를 좁혀 확인합니다. 애매한 일을 오래 두지 못합니다.",
    "버티기형": "부담이 커질수록 쉽게 물러서지 않고 끝까지 처리하려 합니다.",
    "철수형": "마음이 복잡하면 관계보다 혼자 정리할 시간을 택합니다.",
}


def _as_text(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def _clean_customer_copy_text(value: str) -> str:
    text = value
    for before, after in CUSTOMER_COPY_REPLACEMENTS:
        text = text.replace(before, after)
    return text


def _clean_customer_copy_value(value: Any) -> Any:
    if isinstance(value, str):
        return _clean_customer_copy_text(value)
    if isinstance(value, list):
        return [_clean_customer_copy_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clean_customer_copy_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _clean_customer_copy_value(item) for key, item in value.items()}
    return value


def _parse_birth_date(value: str) -> tuple[int, int, int]:
    compact = value.strip().replace(".", "").replace("/", "").replace("-", "")
    if len(compact) == 8 and compact.isdigit():
        return int(compact[:4]), int(compact[4:6]), int(compact[6:8])
    parts = value.split("-")
    if len(parts) != 3:
        raise ValueError("생년월일은 19990101 또는 YYYY-MM-DD 형식으로 입력해 주세요.")
    try:
        year, month, day = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("생년월일은 숫자로 입력해 주세요.") from exc
    return year, month, day


def _parse_birth_time(value: str) -> tuple[int, int]:
    branch_value = value.strip().lower()
    if branch_value in BRANCH_HOUR_REPRESENTATIVE_TIMES:
        return BRANCH_HOUR_REPRESENTATIVE_TIMES[branch_value]
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("태어난 시간은 시지 또는 HH:MM 형식으로 입력해 주세요.")
    try:
        hour, minute = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("태어난 시간은 숫자로 입력해 주세요.") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("태어난 시간은 00:00부터 23:59 사이로 입력해 주세요.")
    return hour, minute


def _parse_target_year(payload: dict[str, Any]) -> int:
    raw_year = payload.get("targetYear", date.today().year)
    try:
        target_year = int(raw_year)
    except (TypeError, ValueError) as exc:
        raise ValueError("분석 연도는 숫자로 입력해 주세요.") from exc
    if not 1900 <= target_year <= 2100:
        raise ValueError("분석 연도는 1900년부터 2100년 사이로 입력해 주세요.")
    return target_year


def _pillar_rows(chart: BirthChartResult) -> list[dict[str, Any]]:
    pillar_map = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
        "hour": chart.hour_pillar,
    }
    rows: list[dict[str, Any]] = []
    for key, label in PILLAR_DISPLAY_ORDER:
        pillar = pillar_map[key]
        rows.append(
            {
                "key": key,
                "label": label,
                "stem": pillar.stem,
                "branch": pillar.branch,
                "pillar": pillar.label,
                "tenGod": chart.ten_gods_by_stem.get(key, ""),
                "hiddenStems": list(chart.hidden_stems.get(key, [])),
                "hiddenTenGods": list(chart.ten_gods_by_branch_hidden.get(key, [])),
            }
        )
    return rows


def _daeun_start_display_age(start_age: float | None) -> int | None:
    if start_age is None:
        return None
    return max(1, ceil(start_age))


def _daeun_age_label(start_age: int, order: int) -> str:
    start = start_age + (order - 1) * 10
    end = start + 9
    return f"{start}~{end}세"


def _current_daeun_order(start_age: int | None, target_year: int, birth_year: int) -> int | None:
    if start_age is None:
        return None
    korean_age = target_year - birth_year + 1
    if korean_age < start_age:
        return 0
    return ((korean_age - start_age) // 10) + 1


def _daeun_rows(chart: BirthChartResult, target_year: int, birth_year: int) -> list[dict[str, Any]]:
    display_start = _daeun_start_display_age(chart.daeun_start_age)
    current_order = _current_daeun_order(display_start, target_year, birth_year)
    rows: list[dict[str, Any]] = []
    for entry in chart.daeun_sequence:
        rows.append(
            {
                "order": entry.order,
                "ageLabel": _daeun_age_label(display_start, entry.order) if display_start else "",
                "startAge": display_start + (entry.order - 1) * 10 if display_start else None,
                "endAge": display_start + entry.order * 10 - 1 if display_start else None,
                "stem": entry.pillar.stem,
                "branch": entry.pillar.branch,
                "pillar": entry.pillar.label,
                "isCurrent": entry.order == current_order,
            }
        )
    return rows


def _annual_rows(target_year: int, birth_year: int, count: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset in range(count):
        year = target_year + offset
        pillar = year_pillar_for_gregorian_year(year)
        rows.append(
            {
                "year": year,
                "ageLabel": f"{year - birth_year + 1}세",
                "stem": pillar.stem,
                "branch": pillar.branch,
                "stemKey": pillar.stem_key,
                "branchKey": pillar.branch_key,
                "pillar": pillar.label,
                "isCurrent": offset == 0,
            }
        )
    return rows


def _timing_target_years(birth_year: int, *, start_age: int = 20, end_age: int = 79) -> list[int]:
    start_year = max(1900, birth_year + start_age - 1)
    end_year = min(2100, birth_year + end_age - 1)
    return list(range(start_year, end_year + 1))


@lru_cache(maxsize=64)
def _analysis_context_cached(
    birth_date: str,
    birth_time: str,
    gender: str,
    calendar_type: str,
    relationship_status: str,
    target_year: int,
    leap_lunar_month: bool,
) -> tuple[BirthChartResult, int, list[int], Any]:
    payload = {
        "birthDate": birth_date,
        "birthTime": birth_time,
        "gender": gender,
        "calendarType": calendar_type,
        "targetYear": target_year,
        "leapLunarMonth": leap_lunar_month,
    }
    birth_input = _build_birth_input(payload)
    chart = build_birth_chart(birth_input)
    birth_year = int(str(chart.normalized_birth_datetime)[:4])
    product_target_years = _timing_target_years(birth_year)
    analysis = analyze_chart(
        chart,
        target_years=product_target_years,
        relationship_status=relationship_status,  # type: ignore[arg-type]
        include_sub_periods=False,
    )
    return chart, birth_year, product_target_years, analysis


def _timing_annual_rows(flow_signals: list[Any], birth_year: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, flow in enumerate(flow_signals):
        year = int(getattr(flow, "year", 0) or 0)
        if not year:
            continue
        pillar = year_pillar_for_gregorian_year(year)
        rows.append(
            {
                "year": year,
                "ageLabel": f"{year - birth_year + 1}세",
                "stem": pillar.stem,
                "branch": pillar.branch,
                "stemKey": pillar.stem_key,
                "branchKey": pillar.branch_key,
                "pillar": getattr(flow, "year_pillar", None) or pillar.label,
                "stemTenGod": getattr(flow, "year_stem_ten_god", ""),
                "branchTenGod": getattr(flow, "year_branch_main_ten_god", ""),
                "daeunPillar": getattr(flow, "daeun_pillar", "") or "",
                "daeunStemTenGod": getattr(flow, "daeun_stem_ten_god", "") or "",
                "daeunBranchTenGod": getattr(flow, "daeun_branch_main_ten_god", "") or "",
                "domainScores": dict(getattr(flow, "domain_scores", {}) or {}),
                "basisCodes": list(getattr(flow, "basis_codes", []) or [])[:8],
                "counterSignals": list(getattr(flow, "counter_signals", []) or [])[:8],
                "activationContext": dict(getattr(flow, "activation_context", {}) or {}),
                "branchInteractions": [
                    {
                        "relationType": str(getattr(item, "relation_type", "") or ""),
                        "positions": list(getattr(item, "positions", []) or []),
                        "basisCode": str(getattr(item, "basis_code", "") or ""),
                    }
                    for item in list(getattr(flow, "branch_interactions", []) or [])[:12]
                ],
                "isCurrent": index == 0,
            }
        )
    return rows


def _chart_summary(
    chart: BirthChartResult,
    target_year: int,
    birth_year: int,
    timing_flow_signals: list[Any] | None = None,
) -> dict[str, Any]:
    display_start_age = _daeun_start_display_age(chart.daeun_start_age)
    current_order = _current_daeun_order(display_start_age, target_year, birth_year)
    current_daeun = None
    if current_order:
        for row in _daeun_rows(chart, target_year, birth_year):
            if row["order"] == current_order:
                current_daeun = row
                break
    return {
        "fourPillars": dict(chart.four_pillars),
        "pillarRows": _pillar_rows(chart),
        "trueSolarDatetime": chart.true_solar_datetime,
        "normalizedBirthDatetime": chart.normalized_birth_datetime,
        "birthLocation": dict(chart.birth_location),
        "daeunDirection": chart.daeun_direction,
        "daeunStartAge": chart.daeun_start_age,
        "daeunStartAgeLabel": f"{display_start_age}세 시작" if display_start_age else "확인 필요",
        "currentDaeunOrder": current_order,
        "currentDaeun": current_daeun,
        "daeunRows": _daeun_rows(chart, target_year, birth_year),
        "annualRows": _annual_rows(target_year, birth_year),
        "timingAnnualRows": _timing_annual_rows(timing_flow_signals or [], birth_year),
        "basis": {
            "locationLabel": FIXED_SERVICE_CITY_LABEL,
            "hourRuleLabel": HOUR_RULE_LABEL,
            "koreanAge": target_year - birth_year + 1,
        },
        "boundarySensitive": chart.boundary_sensitive,
        "daeunBoundarySensitive": chart.daeun_boundary_sensitive,
        "warnings": list(chart.calculation_warnings),
    }


def _build_birth_input(payload: dict[str, Any]) -> BirthInput:
    birth_date = _as_text(payload, "birthDate")
    birth_time = _as_text(payload, "birthTime")
    country = "KR"
    gender = _as_text(payload, "gender", "unknown") or "unknown"
    calendar_type = _as_text(payload, "calendarType", "solar") or "solar"
    if gender not in SUPPORTED_GENDERS:
        raise ValueError("성별 값이 올바르지 않습니다.")
    if calendar_type not in SUPPORTED_CALENDAR_TYPES:
        raise ValueError("현재 출시본은 양력 입력만 지원합니다.")
    year, month, day = _parse_birth_date(birth_date)
    hour, minute = _parse_birth_time(birth_time)
    return BirthInput(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        calendar_type=calendar_type,  # type: ignore[arg-type]
        leap_lunar_month=bool(payload.get("leapLunarMonth", False)),
        country=country,
        city=FIXED_SERVICE_CITY,
        gender=gender,  # type: ignore[arg-type]
    )


def _stem_label(stem: Any) -> str:
    return STEM_HANJA_BY_KEY.get(str(stem), str(stem or ""))


def _branch_label(branch: Any) -> str:
    return BRANCH_HANJA_BY_KEY.get(str(branch), str(branch or ""))


def _ten_god_label(ten_god: Any) -> str:
    return TEN_GOD_LABEL_BY_KEY.get(str(ten_god), str(ten_god or ""))


def _element_label(element: Any) -> str:
    return ELEMENT_LABEL_BY_KEY.get(str(element), str(element or ""))


def _regular_pattern_label(pattern: Any) -> str:
    return REGULAR_PATTERN_LABEL_BY_KEY.get(str(pattern), str(pattern or ""))


def _month_anchor_context_from_analysis(analysis: Any) -> dict[str, Any]:
    structure = getattr(analysis, "chart_structure", None)
    if structure is None:
        return {}
    pattern = getattr(structure, "pattern_profile", None)
    month = getattr(structure, "month_governance_profile", None)
    day_stem = _stem_label(getattr(structure, "day_master_stem", ""))
    month_branch = _branch_label(getattr(structure, "month_branch", ""))
    month_command = str(
        getattr(month, "month_command_ten_god", "")
        or getattr(pattern, "month_command_ten_god", "")
        or ""
    )
    regular_pattern = str(
        getattr(month, "regular_pattern", "")
        or getattr(pattern, "regular_pattern", "")
        or ""
    )
    useful_elements = list(getattr(month, "useful_elements", []) or [])
    caution_elements = list(getattr(month, "caution_elements", []) or [])
    return {
        "day_stem": day_stem,
        "month_branch": month_branch,
        "month_command_ten_god": month_command,
        "month_command_label": _ten_god_label(month_command),
        "month_command_group": str(getattr(month, "month_command_group", "") or ""),
        "regular_pattern": regular_pattern,
        "regular_pattern_label": _regular_pattern_label(regular_pattern),
        "pattern_family": str(
            getattr(month, "pattern_family", "")
            or getattr(pattern, "pattern_family", "")
            or ""
        ),
        "month_element": str(getattr(month, "month_element", "") or ""),
        "month_element_label": _element_label(getattr(month, "month_element", "")),
        "useful_element_labels": [_element_label(element) for element in useful_elements[:3]],
        "caution_element_labels": [_element_label(element) for element in caution_elements[:3]],
    }


def _domain_labels(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    labels: list[str] = []
    for value in values:
        label = DOMAIN_LABEL_BY_KEY.get(str(value), str(value or ""))
        if label and label not in labels:
            labels.append(label)
    return labels[:4]


def _product_item_card_seed(item: dict[str, Any]) -> dict[str, Any]:
    domain = str(item.get("domain") or "")
    return {
        "domain": domain,
        "domain_label": str(item.get("domain_label") or item.get("title") or ""),
        "title": str(item.get("domain_label") or item.get("title") or ""),
    }


def _premium_section_seed(section: dict[str, Any]) -> dict[str, Any]:
    domain = str(section.get("domain") or "")
    seed = {
        "section_id": str(section.get("section_id") or ""),
        "packet_id": str(section.get("packet_id") or ""),
        "domain": domain,
        "domain_label": str(section.get("domain_label") or section.get("heading") or ""),
        "period_label": str(section.get("period_label") or ""),
        "heading": str(section.get("heading") or section.get("domain_label") or ""),
        "lead": str(section.get("lead") or ""),
        "paragraphs": list(section.get("paragraphs") or []),
        "key_points": list(section.get("key_points") or []),
        "timing_windows": list(section.get("timing_windows") or []),
        "relationship_status": str(section.get("relationship_status") or "unknown"),
        "relationship_status_label": str(section.get("relationship_status_label") or ""),
        "feature_axes": list(section.get("feature_axes") or []),
        "topic_items": list(section.get("topic_items") or []),
        "category_contract": dict(section.get("category_contract") or {}),
    }
    if isinstance(section.get("personality_profile"), dict):
        seed["personality_profile"] = dict(section.get("personality_profile") or {})
    return seed


def _factor_section(
    *,
    layer: str,
    source_label: str,
    heading: str,
    lead: str,
    domain_labels: list[str] | None = None,
    domain_bodies: dict[str, str] | None = None,
    domain_scores: dict[str, int] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "layer": layer,
        "source_label": source_label,
        "heading": heading,
        "lead": lead,
        "domain_labels": domain_labels or [],
    }
    if domain_bodies:
        payload["domain_bodies"] = dict(domain_bodies)
    if domain_scores:
        payload["domain_scores"] = dict(domain_scores)
    return payload


def _season_factor_section(life_feature_summary: dict[str, Any]) -> dict[str, Any] | None:
    season = life_feature_summary.get("season_context")
    if not isinstance(season, dict):
        return None
    month = str(season.get("month_branch_label") or season.get("month_branch") or "")
    month_display, _month_particle_base = _branch_display_with_reading(month)
    season_label = str(season.get("season_label") or "")
    useful = ", ".join(str(item) for item in season.get("useful_element_labels", []) if item)
    caution = ", ".join(str(item) for item in season.get("caution_element_labels", []) if item)
    strength = str(season.get("day_master_strength") or "")
    lead = f"월지 {month_display}의 {season_label} 작용을 기준으로 필요한 오행은 {useful or '대운·세운에서 보강되는 오행'}입니다."
    if caution:
        lead += f" 부담이 붙기 쉬운 오행은 {caution}입니다."
    else:
        lead += " 부담 작용은 특정 오행 하나보다 대운과 세운에서 치우치는 기운으로 판정합니다."
    parts = [lead]
    if strength:
        parts.append(f"일간 강약은 {strength}로 계산되었습니다")
    return _factor_section(
        layer="season_context",
        source_label="월령·조후",
        heading=f"월지 {month_display} {season_label} 기준".strip(),
        lead=" ".join(parts),
        domain_labels=["재물", "직업", "연애·관계", "결혼·가정"],
    )


def _hidden_stem_display(entry: dict[str, Any] | None) -> str:
    if not isinstance(entry, dict):
        return ""
    stem = _stem_label(entry.get("stem") or entry.get("active_stem"))
    ten_god = _ten_god_label(entry.get("ten_god") or entry.get("active_ten_god"))
    if stem and ten_god:
        return f"{stem}({ten_god})"
    return stem or ten_god


def _month_governance_domain_bodies(
    *,
    command_label: str,
    active_label: str,
    pattern_label: str,
) -> dict[str, str]:
    wealth_phrase = "재성" if command_label in {"정재", "편재"} or active_label in {"정재", "편재"} else command_label
    return {
        "money": (
            f"재물에서는 {command_label or wealth_phrase}의 보존성과 {active_label or wealth_phrase}의 체감 작용이 서로 다르게 나타납니다. "
            "고정 수입의 기반은 형성되지만, 실제 사건은 거래, 생활비, 가족 지출에서 먼저 드러납니다."
        ),
        "career": (
            "직업에서는 돈과 기준을 다루는 일이 강하게 부각됩니다. "
            "회계, 운영, 품질, 정산처럼 수치와 약속이 분명한 자리에서 평가가 남습니다."
        ),
        "honor": (
            "명예는 말보다 관리한 책임과 기록으로 남습니다. "
            "공식 평판은 맡은 자원을 안정적으로 처리했을 때 굳어집니다."
        ),
        "personality": (
            "성격에서는 손익과 책임 기준을 빨리 세우는 편입니다. "
            "감정이 앞서도 결국 계산 가능한 기준을 확인하려는 성향이 강합니다."
        ),
        "love": (
            "연애에서는 감정보다 신뢰와 생활 감각을 먼저 확인합니다. "
            "좋아하는 마음이 있어도 돈의 사용 방식과 약속의 태도를 가볍게 보지 않습니다."
        ),
        "marriage": (
            "결혼에서는 생활비, 주거, 가족 책임이 관계의 핵심 문제로 올라옵니다. "
            "애정이 깊어도 돈과 생활 기준이 어긋나면 피로가 빠르게 쌓입니다."
        ),
        "social": (
            "대인관계에서는 호의와 계산을 완전히 분리하기 어렵습니다. "
            "믿을 만한 사람이라도 돈과 역할이 얽히면 기준을 먼저 세우는 쪽이 맞습니다."
        ),
    }


def _month_governance_factor_section(life_feature_summary: dict[str, Any]) -> dict[str, Any] | None:
    month = life_feature_summary.get("month_governance_context")
    if not isinstance(month, dict):
        return None
    branch = str(month.get("month_branch_label") or _branch_label(month.get("month_branch")) or "").strip()
    command_label = str(month.get("month_command_label") or _ten_god_label(month.get("month_command_ten_god"))).strip()
    pattern_label = _regular_pattern_label(month.get("regular_pattern"))
    hidden_entries = [entry for entry in month.get("hidden_command_stems") or [] if isinstance(entry, dict)]
    command_display = _hidden_stem_display(hidden_entries[0]) if hidden_entries else ""
    phase = month.get("month_hidden_phase")
    active_phase_label = ""
    active_display = ""
    active_label = ""
    if isinstance(phase, dict):
        active_phase_label = MONTH_HIDDEN_PHASE_LABEL_BY_KEY.get(str(phase.get("active_phase") or ""), "")
        active_display = _hidden_stem_display(
            {
                "stem": phase.get("active_stem"),
                "ten_god": phase.get("active_ten_god"),
            }
        )
        active_label = _ten_god_label(phase.get("active_ten_god"))
    if not any((branch, command_label, pattern_label, command_display, active_display)):
        return None
    heading_core = f"{branch}월 {pattern_label or command_label}".strip()
    lead_parts: list[str] = []
    if branch and pattern_label:
        lead_parts.append(f"월지 {branch}는 {pattern_label}으로 잡힙니다.")
    elif branch and command_label:
        lead_parts.append(f"월지 {branch}는 {command_label} 월령으로 잡힙니다.")
    if command_display:
        lead_parts.append(f"월지 본기 {command_display}가 판단의 기준을 세웁니다.")
    if active_display:
        phase_text = f"{active_phase_label} " if active_phase_label else ""
        lead_parts.append(f"태어난 절기 안에서 실제로 먼저 작동하는 월률분야는 {phase_text}{active_display}입니다.")
    if command_label == "정재" and active_label == "편재":
        lead_parts.append("정재격의 보존성 위에 편재의 거래성과 현금 변동성이 먼저 체감됩니다.")
    elif command_label:
        lead_parts.append(f"{command_label}의 성질이 사주의 생활 판단과 사건 판정에 먼저 깔립니다.")
    return _factor_section(
        layer="month_governance",
        source_label="월령 심화",
        heading=f"{heading_core}의 월령 심화".strip(),
        lead=" ".join(lead_parts),
        domain_labels=["재물", "직업", "명예", "성격", "연애·관계", "결혼·가정", "대인관계"],
        domain_bodies=_month_governance_domain_bodies(
            command_label=command_label,
            active_label=active_label,
            pattern_label=pattern_label,
        ),
    )


def _branch_position_key(position_label: str, explicit_position: Any = "") -> str:
    position = str(explicit_position or "").strip()
    if position in {"year", "month", "day", "hour"}:
        return position
    return POSITION_KEY_BY_LABEL.get(str(position_label or "").strip(), "")


def _branch_position_reality(branch: str, position_label: str, explicit_position: Any = "") -> str:
    position_key = _branch_position_key(position_label, explicit_position)
    return branch_position_texture(branch, position_key) if position_key else ""


def _branch_domain_reality(branch: str, domain: str) -> str:
    mapped = DOMAIN_BRANCH_TEXTURE_MAP.get(str(domain or "").strip())
    return branch_domain_texture(branch, mapped) if mapped else ""


def _branch_display_with_reading(branch: str) -> tuple[str, str]:
    label = str(branch or "").strip()
    reading = BRANCH_READING_BY_LABEL.get(label, "")
    if reading:
        return f"{label}({reading})", reading
    return label, label


def _branch_reality_factor_sections(life_feature_summary: dict[str, Any]) -> list[dict[str, Any]]:
    branch_context = life_feature_summary.get("branch_reality_context")
    if not isinstance(branch_context, dict):
        return []
    sections: list[dict[str, Any]] = []
    for signal in branch_context.get("position_signals", [])[:3]:
        if not isinstance(signal, dict):
            continue
        position = str(signal.get("position_label") or "")
        position_key = _branch_position_key(position, signal.get("position"))
        branch = str(signal.get("branch_label") or "")
        branch_display, branch_particle_base = _branch_display_with_reading(branch)
        branch_key = str(signal.get("branch") or branch)
        element = str(signal.get("branch_element_label") or "")
        ten_god = _ten_god_label(signal.get("branch_main_ten_god"))
        hidden = ", ".join(_ten_god_label(item) for item in signal.get("hidden_ten_gods", []) if item)
        protruded_stems = [str(item) for item in signal.get("protruded_hidden_stems", []) if str(item or "")]
        protruded_labels = ", ".join(_stem_label(item) for item in protruded_stems if item)
        position_reality = _branch_position_reality(branch_key, position, position_key)
        reality_label = POSITION_REALITY_LABEL.get(position_key, "생활 속 현실 조건")
        opening = (
            f"{position} {branch_display}{_topic_particle(branch_particle_base)} {reality_label}에서 {element} {ten_god} 작용을 드러냅니다."
            if branch
            else f"{position}는 {reality_label}에서 {element} {ten_god} 작용을 드러냅니다."
        )
        if position_reality:
            opening = f"{opening} {position_reality}"
        lead_parts = [opening]
        if hidden:
            lead_parts.append(f"지장간 {hidden}{_topic_particle(hidden)} 시간이 지난 뒤 수입, 책임, 관계의 속사정으로 올라옵니다.")
            if protruded_labels:
                lead_parts.append(f"그중 {protruded_labels}{_subject_particle(protruded_labels)} 천간에 투출되어 숨은 작용이 밖으로 드러납니다.")
            else:
                lead_parts.append("투출이 약한 지장간은 시기와 사건을 만나야 밖으로 드러납니다.")
        if signal.get("supports_day_master"):
            lead_parts.append("이 지지는 일간의 뿌리가 되어 자기 기준과 버티는 힘을 보탭니다.")
        if signal.get("controls_day_master"):
            lead_parts.append("이 지지는 일간을 제어하는 관성 자리라 책임과 규칙을 실제 압력으로 만듭니다.")
        lead = " ".join(lead_parts)
        sections.append(
            _factor_section(
                layer="branch_reality",
                source_label="지지·지장간",
                heading=f"{position} {branch}의 현실 작용",
                lead=lead,
                domain_labels=_domain_labels(signal.get("domains")),
                domain_bodies=_branch_domain_bodies(
                    position,
                    branch_key,
                    branch,
                    element,
                    ten_god,
                    hidden,
                    protruded_stems=protruded_stems,
                    supports_day_master=bool(signal.get("supports_day_master")),
                    controls_day_master=bool(signal.get("controls_day_master")),
                ),
            )
        )
    for interaction in branch_context.get("interactions", [])[:2]:
        if not isinstance(interaction, dict):
            continue
        relation = str(interaction.get("relation_label") or interaction.get("relation_type") or "")
        branches = "".join(str(item) for item in interaction.get("branch_labels", []) if item)
        positions = "·".join(str(item) for item in interaction.get("position_labels", []) if item)
        lead = f"{positions}의 {branches} 관계는 {relation}입니다. 이 신호는 해당 궁성의 일이 움직이거나 부담이 드러나는 근거입니다."
        sections.append(
            _factor_section(
                layer="branch_reality",
                source_label="합충형파해",
                heading=f"{branches} {relation} 작용",
                lead=lead,
                domain_labels=_domain_labels(interaction.get("domain_links")),
            )
        )
    return sections


def _branch_domain_bodies(
    position: str,
    branch_key: str,
    branch: str,
    element: str,
    ten_god: str,
    hidden: str,
    *,
    protruded_stems: list[str] | None = None,
    supports_day_master: bool = False,
    controls_day_master: bool = False,
) -> dict[str, str]:
    branch_label = f"{position} {branch}".strip()
    protruded_labels = ", ".join(_stem_label(stem) for stem in (protruded_stems or []) if stem)

    def hidden_note(domain: str) -> str:
        if not hidden:
            return ""
        prefix = f" 지장간 {hidden}{_topic_particle(hidden)} "
        if protruded_labels:
            protruded_notes = {
                "money": "숨은 재물 작용을 실제 금액, 명의, 지분 문제로 빠르게 드러냅니다.",
                "career": "숨은 책임과 평가 기준을 직무와 직책 문제로 빠르게 드러냅니다.",
                "honor": "숨은 평판 요인을 공식 기록과 직함 문제로 빠르게 드러냅니다.",
                "love": "숨은 태도와 기대를 관계 안에서 빠르게 드러냅니다.",
                "marriage": "숨은 생활 기준과 책임 문제를 결혼 뒤 실제 역할로 빠르게 드러냅니다.",
                "social": "숨은 신뢰 기준과 거리감을 사람 사이에서 빠르게 드러냅니다.",
                "life": "숨은 선택 기준을 인생의 중요한 장면에서 빠르게 현실화합니다.",
                "personality": "숨은 반응 방식을 말과 선택으로 빠르게 드러냅니다.",
            }
            return f" 지장간 {hidden} 가운데 {protruded_labels}{_subject_particle(protruded_labels)} 천간에 투출되어 " + protruded_notes.get(
                domain,
                "숨은 작용을 실제 사건으로 빠르게 드러냅니다.",
            )
        notes = {
            "money": "겉으로 드러난 수입보다 뒤늦게 올라오는 지출과 몫 문제를 만듭니다.",
            "career": "처음 맡은 일보다 나중에 붙는 책임 문제로 나타납니다.",
            "honor": "초기의 평판보다 뒤늦게 확인되는 기록 문제로 작동합니다.",
            "love": "첫 호감보다 시간이 지난 뒤 드러나는 태도 문제로 올라옵니다.",
            "marriage": "결혼 뒤 생활비와 역할 문제에서 뒤늦게 드러납니다.",
            "social": "처음 인상보다 오래 지낸 뒤 신뢰 문제로 드러납니다.",
            "life": "나이가 들수록 생활 조건과 선택의 대가로 드러납니다.",
            "personality": "평소 모습보다 압박을 받는 순간의 반응으로 드러납니다.",
        }
        return prefix + notes.get(domain, "처음보다 시간이 지난 뒤 현실 문제로 올라옵니다.")

    position_key = _branch_position_key(position)
    position_domain = POSITION_REALITY_LABEL.get(position_key, "현실 조건")

    def root_note(domain: str) -> str:
        if supports_day_master:
            return " 이 지지는 일간의 뿌리가 되어 자기 기준과 지속력을 강하게 만듭니다."
        if controls_day_master:
            return " 이 지지는 일간을 제어하는 관성 자리라 책임, 규칙, 평가 압력을 실제 사건으로 만듭니다."
        return ""

    def texture(domain: str) -> str:
        sentence = _branch_domain_reality(branch_key or branch, domain)
        return f" {sentence}" if sentence else ""

    bodies = {
        "money": (
            f"{branch_label}의 {ten_god} 작용은 돈이 실제로 움직이는 자리를 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 수입이 자산으로 남는 방식을 정합니다.{texture('money')}{root_note('money')}{hidden_note('money')}"
        ),
        "career": (
            f"{branch_label}의 {ten_god} 작용은 직업에서 맡게 되는 역할과 책임의 성격을 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 일의 방식과 평가 기준이 여기서 정해집니다.{texture('career')}{root_note('career')}{hidden_note('career')}"
        ),
        "honor": (
            f"{branch_label}의 {ten_god} 작용은 사회적 평판이 생기는 자리를 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 명예는 말보다 실제 자리와 책임에서 드러납니다.{texture('honor')}{root_note('honor')}{hidden_note('honor')}"
        ),
        "love": (
            f"{branch_label}의 {ten_god} 작용은 가까운 관계에서 반복되는 태도를 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 호감보다 관계를 유지하는 태도가 먼저 드러납니다.{texture('love')}{root_note('love')}{hidden_note('love')}"
        ),
        "marriage": (
            f"{branch_label}의 {ten_god} 작용은 결혼 이후의 생활 기준을 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 결혼 생활의 안정감이 여기서 결정됩니다.{texture('marriage')}{root_note('marriage')}{hidden_note('marriage')}"
        ),
        "social": (
            f"{branch_label}의 {ten_god} 작용은 사람을 대할 때 반복되는 거리감과 신뢰 기준을 정합니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 오래 남는 관계의 성격이 분명해집니다.{texture('social')}{root_note('social')}{hidden_note('social')}"
        ),
        "life": (
            f"{branch_label}의 {ten_god} 작용은 인생에서 현실 조건이 형성되는 자리를 잡습니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 인생 구간별 체감이 달라집니다.{root_note('life')}{hidden_note('life')}"
        ),
        "personality": (
            f"{branch_label}의 {ten_god} 작용은 겉으로 보이는 성격보다 실제 선택 방식에 가깝습니다. "
            f"{element} 기운이 {position_domain}에 놓여 있어, 압박을 받을 때의 반응이 분명하게 드러납니다.{root_note('personality')}{hidden_note('personality')}"
        ),
    }
    return {domain: _polish_factor_basis_text(body) for domain, body in bodies.items()}


def _combination_factor_sections(life_feature_summary: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
    signals = life_feature_summary.get("top_combination_signals")
    if not isinstance(signals, list):
        return []
    sections: list[dict[str, Any]] = []
    for signal in signals[:limit]:
        if not isinstance(signal, dict):
            continue
        stems = "".join(_stem_label(stem) for stem in signal.get("stems", []) if stem)
        ten_gods = [_ten_god_label(item) for item in signal.get("ten_gods", []) if item]
        ten_god_text = "-".join(item for item in ten_gods if item)
        interpretation = str(signal.get("interpretation") or "").strip()
        if interpretation:
            lead = interpretation
        elif ten_god_text:
            lead = f"{stems} 배합과 {ten_god_text} 관계가 함께 작용합니다."
        else:
            lead = f"{stems} 배합이 주요 신호로 잡힙니다."
        sections.append(
            _factor_section(
                layer="integrated_saju",
                source_label="오행·십신 통합",
                heading=f"{stems} 통합 판단",
                lead=lead,
                domain_labels=_domain_labels(signal.get("domain_links")),
            )
        )
    return sections


SIMPLE_CYCLE_DOMAIN_BODIES: dict[str, dict[str, str]] = {
    "목생화": {
        "personality": "생각과 기획이 말, 표현, 설득으로 바로 이어지는 성향입니다.",
        "career": "기획과 아이디어가 발표, 교육, 홍보, 콘텐츠 업무로 살아납니다.",
        "money": "재물은 생각을 밖으로 드러내고 사람에게 전달할 때 움직입니다.",
        "social": "사람을 움직이는 힘은 조용한 배려보다 말과 표현에서 강하게 나옵니다.",
    },
    "화생토": {
        "personality": "표현과 책임을 현실 기준으로 굳히는 성향입니다. 감정이 올라와도 결국 결과와 책임을 따집니다.",
        "career": "노출, 평가, 책임이 조직 안의 신뢰와 기반으로 굳어집니다.",
        "money": "평판과 활동성이 자산, 기반, 고정 수입으로 굳어질 때 재물운이 강해집니다.",
        "honor": "평판은 순간적인 인기보다 맡은 일을 끝까지 남기는 방식으로 올라갑니다.",
    },
    "토생금": {
        "personality": "현실 기준을 세운 뒤 정확한 판단과 결과물로 정리하는 성향입니다.",
        "career": "관리, 기준, 품질, 심사, 시스템 업무에서 강점이 드러납니다.",
        "money": "자산과 기반이 계산, 문서, 기준을 거치며 돈으로 정리됩니다.",
        "honor": "명예는 실력보다 먼저 기준과 결과물을 통해 인정받습니다.",
    },
    "금생수": {
        "personality": "분석과 기준을 정보, 학습, 판단으로 확장하는 성향입니다.",
        "career": "데이터, 금융, 전략, 유통, 연구처럼 기준과 정보가 함께 필요한 일에서 강합니다.",
        "money": "재물은 계산, 문서, 정보 기준이 분명할 때 안정됩니다.",
        "social": "사람을 감정으로만 대하기보다 정보와 정황을 읽고 움직입니다.",
    },
    "수생목": {
        "personality": "정보와 배움이 기획, 성장, 확장 욕구로 이어지는 성향입니다.",
        "career": "학습, 기획, 교육, 확장형 업무에서 장기적으로 힘이 붙습니다.",
        "money": "재물은 공부와 정보가 실제 기회로 연결될 때 살아납니다.",
        "life": "인생의 방향은 배움과 이동을 통해 새롭게 열립니다.",
    },
}


ROLE_GROUP_LABELS: dict[str, str] = {
    "peer": "비겁",
    "output": "식상",
    "wealth": "재성",
    "officer": "관성",
    "resource": "인성",
}

PRINCIPLE_ROLE_EDGE_TITLES: dict[tuple[str, str, str], str] = {
    ("resource", "peer", "generates"): "인성생비겁",
    ("peer", "output", "generates"): "비겁생식상",
    ("output", "wealth", "generates"): "식상생재",
    ("wealth", "officer", "generates"): "재생관",
    ("officer", "resource", "generates"): "관인상생",
    ("peer", "wealth", "controls"): "비겁극재",
    ("wealth", "resource", "controls"): "재극인",
    ("resource", "output", "controls"): "인성극식상",
    ("output", "officer", "controls"): "식상제관",
    ("officer", "peer", "controls"): "관성제비겁",
}

PRINCIPLE_ROLE_EDGE_BODIES: dict[tuple[str, str, str], dict[str, str]] = {
    ("output", "wealth", "generates"): {
        "money": "기술, 말, 결과물이 수입으로 바뀌는 작용입니다. 원국에서는 식상의 현실성이 숨어 있으므로, 재능 자체보다 상품화와 가격 결정이 늦게 붙는 쪽으로 판정합니다.",
        "career": "직업에서는 결과물을 만들어내는 능력이 보상 기준으로 연결됩니다. 다만 결과물이 문서, 상품, 실적처럼 보이는 형태가 되어야 평가가 분명해집니다.",
        "personality": "성격에서는 생각을 오래 붙들기보다 실제 결과로 확인하려는 욕구가 있습니다. 준비만 길어지면 답답함이 커집니다.",
        "timing": "식상이 들어오는 연도에는 숨어 있던 생산 능력이 수입 문제로 드러납니다. 결과물, 계약 단가, 성과 보상이 함께 움직입니다.",
    },
    ("wealth", "officer", "generates"): {
        "money": "재성이 관성을 생하면 돈이 직책과 권한의 근거가 됩니다. 재물은 보수 체계와 공식 역할을 통해 커집니다.",
        "career": "직업에서는 보상 기준이 직함으로 이어집니다. 돈을 다루는 일이 곧 신뢰와 권한의 근거가 됩니다.",
        "honor": "명예는 말보다 직책과 책임에서 생깁니다. 사적인 이익을 공적인 기준으로 정리할수록 평판이 안정됩니다.",
        "love": "연애에서는 호감이 깊어질수록 책임과 약속 문제가 빨리 올라옵니다. 좋아하는 마음만으로 관계를 끌기보다 현실적인 태도와 책임감을 확인합니다.",
        "marriage": "결혼에서는 생활비와 명의 문제가 구체적인 약속으로 이어집니다. 감정보다 현실 책임을 먼저 확인하는 방식입니다.",
        "timing": "재성과 관성이 함께 움직이는 연도에는 보수 기준과 직책이 동시에 바뀝니다.",
    },
    ("wealth", "resource", "controls"): {
        "money": "재성이 인성을 극하면 현실의 돈 문제가 공부, 문서, 보호 장치를 밀어냅니다. 준비가 길어지기보다 수익화와 회수 판단이 앞당겨집니다.",
        "career": "직업에서는 자격과 명분보다 실제 성과 요구가 강해집니다. 이론으로 버티기보다 결과를 내야 하는 자리에서 판정이 뚜렷합니다.",
        "love": "관계에서는 오래 해석하기보다 실제 태도와 책임을 기준으로 결론을 냅니다. 말보다 현실 행동을 더 강하게 판단합니다.",
        "marriage": "결혼에서는 명분보다 생활 능력, 돈의 책임, 가족 문제를 먼저 따집니다. 현실 부담이 약속의 속도를 앞당기거나 늦춥니다.",
        "personality": "성격에서는 오래 검토한 뒤에도 결국 현실 이익을 기준으로 결정을 내립니다. 명분보다 실익이 선택을 앞당깁니다.",
        "timing": "문서, 학업, 준비가 길어진 뒤 돈과 성과의 압력이 들어오는 연도에 크게 드러납니다.",
    },
    ("peer", "wealth", "controls"): {
        "money": "비겁이 재성을 극하면 가까운 사람과 재물의 몫이 부딪힙니다. 가까운 사람과 자금이 섞이면 명의와 지분 문제가 민감해집니다.",
        "social": "대인관계에서는 친밀함이 곧 재물 안정으로 이어지지 않습니다. 가까운 사람일수록 몫과 책임을 분명히 해야 관계가 오래 갑니다.",
        "love": "연애에서는 애정과 소유감이 함께 강해집니다. 우선순위 문제가 갈등의 핵심이 됩니다.",
        "marriage": "결혼에서는 가족 돈, 생활비, 명의 문제가 민감하게 떠오릅니다. 부부 재정은 처음부터 분리와 합의가 필요합니다.",
        "timing": "비겁과 재성이 함께 움직이는 연도에는 공동 비용, 지분, 성과 배분 문제가 크게 드러납니다.",
    },
    ("officer", "peer", "controls"): {
        "money": "관성이 비겁을 제어하면 주변 사람의 재물 침범을 규칙과 권한으로 정리합니다. 계약, 직책, 책임선이 살아야 공동 자금 손실이 줄어듭니다.",
        "career": "직업에서는 규칙과 권한이 자기 주장과 경쟁을 정리합니다. 직책이 분명할수록 성과가 흩어지지 않습니다.",
        "social": "사람 문제는 정으로만 풀리지 않습니다. 역할과 책임이 분명해야 가까운 관계에서도 불필요한 소모가 줄어듭니다.",
        "honor": "공적인 기준이 사적인 이해관계를 누를 때 평판이 안정됩니다. 명예는 관계보다 규칙을 세울 때 지켜집니다.",
        "timing": "관성이 강하게 작동하는 연도에는 공동 재물과 책임 문제가 제도, 계약, 직책을 통해 정리됩니다.",
    },
    ("resource", "output", "controls"): {
        "money": "인성이 식상을 제어하면 생각, 문서, 자격이 결과물의 속도를 늦춥니다. 수익화는 가능하지만 준비와 검토가 길어지는 쪽입니다.",
        "career": "직업에서는 공부와 문서가 깊어지는 대신 결과물 제출이 늦어질 수 있습니다. 전문성은 강하지만 시장 반응은 속도가 필요합니다.",
        "personality": "성격에서는 쉽게 내놓지 않고, 근거가 충분해야 움직입니다. 신중함이 강점이지만 실행이 늦어지면 기회를 놓칩니다.",
        "timing": "인성과 식상이 함께 흔들리는 연도에는 준비와 결과물 사이의 지연이 크게 체감됩니다.",
    },
    ("output", "officer", "controls"): {
        "career": "식상이 관성을 제어하면 압박과 책임을 실무로 풀어냅니다. 어려운 일일수록 말보다 처리 능력이 평가를 만듭니다.",
        "money": "재물에서는 문제 해결 능력이 보상으로 이어집니다. 위험한 업무나 까다로운 고객을 처리할 때 수입 기회가 붙습니다.",
        "honor": "평판은 순종보다 실무 해결력에서 생깁니다. 다만 말과 태도가 거칠어지면 공식 평가가 깎입니다.",
        "timing": "책임과 실무가 동시에 강해지는 연도에는 문제 해결 능력이 직업과 재물의 성패를 정합니다.",
    },
    ("officer", "resource", "generates"): {
        "career": "관성이 인성을 생하면 책임이 자격, 문서, 신뢰로 축적됩니다. 직업운은 맡은 일을 기록과 권위로 남길 때 강합니다.",
        "honor": "명예는 직책과 문서 신뢰에서 만들어집니다. 즉흥적 인기보다 공식 책임과 검증된 이력이 오래 갑니다.",
        "marriage": "결혼에서는 책임을 피하지 않는 태도가 신뢰를 만듭니다. 생활의 약속이 구체적일수록 안정됩니다.",
        "personality": "압박을 받으면 감정으로 흩어지기보다 근거와 절차를 세우는 쪽으로 움직입니다.",
    },
    ("resource", "peer", "generates"): {
        "personality": "인성이 비겁을 생하면 배움, 문서, 보호 장치가 자기 기준을 뚜렷하게 만듭니다. 쉽게 흔들리지 않지만 자기 확신이 지나쳐질 수 있습니다.",
        "career": "직업에서는 자격과 근거가 자기 역할을 받칩니다. 단독 판단보다 근거를 갖춘 책임 수행에서 힘이 납니다.",
        "money": "재물에서는 보호 자원과 정보가 내 몫을 지키는 근거가 됩니다. 문서와 기록이 재산 방어에 중요합니다.",
    },
    ("peer", "output", "generates"): {
        "career": "비겁이 식상을 생하면 동료, 팀, 자기 추진력이 결과물을 만들어냅니다. 혼자보다 함께 움직일 때 산출이 커집니다.",
        "money": "재물에서는 주변 사람과 함께 만든 결과가 수입으로 이어질 수 있습니다. 다만 수익 배분 기준이 먼저 서야 합니다.",
        "social": "관계에서는 가까운 사람과 함께 움직이며 영향력이 생깁니다. 친분이 결과물로 이어질 때 관계가 강해집니다.",
    },
}


def _principle_edge_title(edge: dict[str, Any]) -> str:
    source = str(edge.get("source_group") or "")
    target = str(edge.get("target_group") or "")
    relation = str(edge.get("relation") or "")
    return (
        str(edge.get("classical_name") or "").strip()
        or PRINCIPLE_ROLE_EDGE_TITLES.get((source, target, relation), "")
        or f"{ROLE_GROUP_LABELS.get(source, source)}{'생' if relation == 'generates' else '극'}{ROLE_GROUP_LABELS.get(target, target)}"
    )


def _principle_scope_text(edge: dict[str, Any]) -> str:
    scope = str(edge.get("scope") or "")
    reality = str(edge.get("edge_reality_grade") or "")
    force_effect = str(edge.get("force_effect") or "")
    if scope.startswith("active") and reality in {"month_visible_edge", "rooted_edge"}:
        return "월령에서 기준이 잡히고 지지에 뿌리가 있어 실제 사건으로 이어지는 힘이 큽니다."
    if scope.startswith("active"):
        return "원국 안에서 드러난 작용이라 재물, 직업, 관계 판단에 직접 힘을 씁니다."
    if scope == "latent_reference":
        if "drains_source" in force_effect:
            return "원국에 작용은 있으나 힘이 약해, 대운·세운에서 보강될 때 사건성이 커집니다."
        return "겉으로 강하게 드러나지는 않아도 판단에서 제외할 수 없는 작용입니다."
    if scope == "trace_reference":
        return "현재 힘은 작지만, 대운·세운에서 같은 글자가 들어오면 표면으로 올라옵니다."
    return "월령, 지지, 지장간의 현실성을 거쳐 판정한 작용입니다."


def _principle_edge_lead(edge: dict[str, Any]) -> str:
    source = str(edge.get("source_group") or "")
    target = str(edge.get("target_group") or "")
    relation = str(edge.get("relation") or "")
    title = _principle_edge_title(edge)
    source_label = ROLE_GROUP_LABELS.get(source, source)
    target_label = ROLE_GROUP_LABELS.get(target, target)
    relation_label = "생" if relation == "generates" else "극"
    scope_text = _principle_scope_text(edge)
    known_leads = {
        "식상생재": "식상생재는 식상의 결과물이 재성으로 이어져 기술, 말, 생산물이 수입으로 전환되는 작용입니다.",
        "재생관": "재생관은 재성이 관성에 힘을 보태 직책, 책임, 공식 기준을 세우는 작용입니다.",
        "관인상생": "관인상생은 관성이 인성으로 이어져 책임이 문서, 자격, 신뢰로 굳어지는 작용입니다.",
        "인성생비겁": "인성생비겁은 인성이 비겁을 생해 지식, 보호, 문서가 자기 기준을 강화하는 작용입니다.",
        "비겁극재": "비겁극재는 비겁이 재성을 건드려 소유, 몫, 지분 문제를 일으키는 작용입니다.",
        "재극인": "재극인은 재성이 인성을 제어해 생각, 명분, 문서보다 현실성과 회수를 앞세우는 작용입니다.",
        "관성극비겁": "관성극비겁은 관성이 비겁을 제어해 경쟁과 자기주장을 규칙, 권한, 책임으로 정리하는 작용입니다.",
        "식상극관": "식상극관은 식상이 관성을 제어해 정해진 책임과 규칙에 문제를 제기하는 작용입니다.",
    }
    if title in known_leads:
        return f"{known_leads[title]} {scope_text}"
    if relation == "generates":
        base = f"{title}{_subject_particle(title)} {source_label}의 힘이 {target_label}으로 이어지는 작용입니다."
    else:
        base = f"{title}{_subject_particle(title)} {source_label}이 {target_label}을 제어해 현실 기준을 세우는 작용입니다."
    return f"{base} {scope_text}"


def _principle_edge_domain_scores(edge: dict[str, Any]) -> dict[str, int]:
    source = str(edge.get("source_group") or "")
    target = str(edge.get("target_group") or "")
    relation = str(edge.get("relation") or "")
    edge_key = (source, target, relation)
    scope = str(edge.get("scope") or "")
    reality = str(edge.get("edge_reality_grade") or "")
    base = 28
    if scope.startswith("active"):
        base += 28
    elif scope == "latent_reference":
        base += 12
    if reality in {"month_visible_edge", "rooted_edge"}:
        base += 22
    elif reality == "one_sided_edge":
        base += 8
    scores: dict[str, int] = {}
    for domain in edge.get("domain_links") or []:
        if str(domain) in DOMAIN_FACTOR_TERMS:
            scores[str(domain)] = base
    if "wealth" in {source, target}:
        scores["money"] = max(scores.get("money", 0), base + 34)
    if "officer" in {source, target} or edge_key in {("output", "officer", "controls"), ("officer", "resource", "generates")}:
        scores["career"] = max(scores.get("career", 0), base + 28)
        scores["honor"] = max(scores.get("honor", 0), base + 18)
    if "peer" in {source, target}:
        scores["social"] = max(scores.get("social", 0), base + 18)
    if edge_key in {("wealth", "officer", "generates"), ("peer", "wealth", "controls"), ("officer", "peer", "controls")}:
        scores["marriage"] = max(scores.get("marriage", 0), base + 18)
        scores["love"] = max(scores.get("love", 0), base + 12)
    if edge_key in {("resource", "output", "controls"), ("resource", "peer", "generates")}:
        scores["personality"] = max(scores.get("personality", 0), base + 26)
    if scope in {"latent_reference", "trace_reference"}:
        scores["timing"] = max(scores.get("timing", 0), base + 20)
    return {domain: min(score, 100) for domain, score in scores.items() if score > 0}


def _principle_role_domain_bodies(edge: dict[str, Any]) -> dict[str, str]:
    source = str(edge.get("source_group") or "")
    target = str(edge.get("target_group") or "")
    relation = str(edge.get("relation") or "")
    body_map = PRINCIPLE_ROLE_EDGE_BODIES.get((source, target, relation), {})
    if not body_map:
        return {}
    scope_text = _principle_scope_text(edge)
    domain_scores = _principle_edge_domain_scores(edge)
    return {
        domain: f"{body} {scope_text}"
        for domain, body in body_map.items()
        if domain_scores.get(domain, 0) > 0
    }


def _principle_edge_rank(edge: dict[str, Any]) -> tuple[int, int]:
    source = str(edge.get("source_group") or "")
    target = str(edge.get("target_group") or "")
    relation = str(edge.get("relation") or "")
    edge_key = (source, target, relation)
    priority_edges = {
        ("wealth", "officer", "generates"): 100,
        ("peer", "wealth", "controls"): 96,
        ("wealth", "resource", "controls"): 94,
        ("officer", "peer", "controls"): 92,
        ("output", "wealth", "generates"): 90,
        ("output", "officer", "controls"): 82,
        ("officer", "resource", "generates"): 80,
        ("resource", "output", "controls"): 78,
    }
    score = priority_edges.get(edge_key, 50)
    scope = str(edge.get("scope") or "")
    reality = str(edge.get("edge_reality_grade") or "")
    if scope.startswith("active"):
        score += 24
    elif scope == "latent_reference":
        score += 10
    if reality in {"month_visible_edge", "rooted_edge"}:
        score += 18
    if edge.get("touches_month_command"):
        score += 16
    try:
        score += int(edge.get("support_score") or 0) // 2
        score += int(edge.get("pressure_score") or 0) // 3
    except (TypeError, ValueError):
        pass
    return (-score, 0)


def _cycle_principle_matrix_factor_sections(
    life_feature_summary: dict[str, Any],
    limit: int = 8,
) -> list[dict[str, Any]]:
    profile = life_feature_summary.get("cycle_regulation_context")
    if not isinstance(profile, dict):
        return []
    matrix = profile.get("principle_matrix")
    if not isinstance(matrix, dict):
        return []
    raw_edges = [edge for edge in matrix.get("role_edges") or [] if isinstance(edge, dict)]
    if not raw_edges:
        return []
    sections: list[dict[str, Any]] = []
    seen: set[str] = set()
    for edge in sorted(raw_edges, key=_principle_edge_rank):
        title = _principle_edge_title(edge)
        if not title or title in seen:
            continue
        domain_scores = _principle_edge_domain_scores(edge)
        domain_bodies = _principle_role_domain_bodies(edge)
        if not domain_scores and not domain_bodies:
            continue
        seen.add(title)
        sections.append(
            _factor_section(
                layer="cycle_principle_matrix",
                source_label="생극·십신",
                heading=title,
                lead=_principle_edge_lead(edge),
                domain_labels=_domain_labels(list(domain_scores.keys())),
                domain_bodies=domain_bodies,
                domain_scores=domain_scores,
            )
        )
        if len(sections) >= limit:
            break
    return sections


def _cycle_domain_body(signal: dict[str, Any], domain: str, fallback: str) -> str:
    name = str(signal.get("classical_name") or "")
    sentence = str(signal.get("sentence") or "").strip()
    if name == "식상생재 후 재생관":
        return {
            "money": "만든 결과가 수입으로 바뀌고, 그 수입이 다시 계약과 책임 기준으로 올라갑니다. 재물운은 단순한 현금 유입보다 보수 기준과 역할 상승에서 강하게 움직입니다.",
            "career": "결과물이 수입 기준을 만들고, 그 기준이 직책과 책임으로 이어집니다. 직업운은 실적이 공식 평가로 남을 때 강합니다.",
            "honor": "결과물이 공식 기준으로 인정받습니다. 평판은 말보다 실적, 기록, 직책을 통해 올라갑니다.",
            "social": "사람 관계에서도 결과를 함께 만든 사람이 오래 남습니다. 말로 가까운 사람보다 일과 책임을 같이 통과한 인연이 강합니다.",
            "love": "관계에서도 말보다 실제 책임과 약속이 중요해집니다. 호감이 깊어지면 생활 기준과 역할 문제가 함께 올라옵니다.",
            "marriage": "결혼에서는 감정보다 생활 책임과 역할 기준이 먼저 굳어집니다. 약속이 구체화될수록 관계의 안정성이 분명해집니다.",
            "personality": "생각보다 결과물을 먼저 세우고, 결과가 생기면 책임 범위까지 따지는 성향으로 나타납니다.",
            "life": "인생의 중요한 성취는 재능 자체보다 결과물과 보수가 직책으로 이어질 때 남습니다.",
            "timing": "결과물, 보수, 직책이 함께 움직이는 해에 상승 작용이 강합니다. 직업 변화와 재물 변화가 같은 시기에 붙기 쉽습니다.",
        }.get(domain, sentence or fallback)
    if name == "재생관으로 비겁을 제어":
        return {
            "money": "재물이 관성을 세우면 가까운 사람과의 몫 문제를 계약과 책임 기준으로 묶습니다. 공동 자금은 정해진 기준이 있을 때 손실이 줄어듭니다.",
            "career": "현실 자원과 돈의 기준이 직책과 책임으로 올라갑니다. 책임 범위가 분명한 자리에서 경력 손실이 줄어듭니다.",
            "honor": "돈과 자원이 책임 있는 자리로 이어질 때 명예가 살아납니다. 사적인 이해관계를 공적인 기준으로 정리할수록 평판이 안정됩니다.",
            "social": "가까운 사람의 요구를 관계만으로 받아주지 않고 기준으로 정리합니다. 사람 문제는 정이 아니라 역할이 분명할 때 오래 갑니다.",
            "love": "관계에서는 정과 의리만으로 움직이지 않고 약속과 책임 기준을 세우게 됩니다.",
            "marriage": "결혼에서는 생활비, 명의, 가족 책임을 기준으로 정리할 때 안정이 생깁니다.",
            "personality": "주변 사람의 요구를 그대로 떠안기보다 책임 기준을 세워 정리하는 방식으로 나타납니다.",
            "life": "인생의 부담은 가까운 사람과 돈이 섞일 때 생기지만, 책임 기준이 서면 자리와 권한으로 바뀝니다.",
            "timing": "돈, 권한, 책임이 동시에 움직이는 해에는 주변 사람과의 몫 문제까지 함께 정리됩니다.",
        }.get(domain, sentence or fallback)
    if name == "재극인으로 도식을 완화":
        return {
            "money": "돈과 현실 조건이 긴 준비를 실제 회수 판단으로 돌립니다. 재물운은 준비보다 회수와 수익화가 빨라질 때 살아납니다.",
            "career": "현실 성과가 문서와 자격 중심의 지연을 밀어냅니다. 직업운은 이론을 실제 결과로 바꿀 때 강합니다.",
            "honor": "명분이나 자격만으로 머무르지 않고 실제 성과가 평판을 앞당깁니다. 이름은 준비 기간보다 결과가 나오는 순간에 붙습니다.",
            "social": "사람을 오래 관찰하기보다 실제 태도와 이해관계를 보고 판단합니다. 관계에서도 말보다 행동이 기준이 됩니다.",
            "love": "관계에서는 지나친 해석보다 실제 태도와 행동이 결론을 앞당깁니다.",
            "marriage": "결혼에서는 생각과 명분보다 주거, 돈, 가족 책임이 결정을 앞당깁니다.",
            "personality": "검토와 망설임이 길어질 때 현실 조건을 기준으로 결정을 내립니다.",
            "life": "준비와 고민이 길어질수록 현실 조건이 결정을 밀어냅니다. 삶의 방향은 생각보다 생계, 돈, 실제 성과에서 빠르게 정해집니다.",
            "timing": "문서, 학업, 준비가 길어진 뒤 현실 성과가 요구되는 해에 전환이 크게 나타납니다.",
        }.get(domain, sentence or fallback)
    if name == "관인상생":
        return {
            "money": "책임이 문서와 신뢰로 축적되면서 안정적인 보상으로 이어집니다.",
            "career": "압박과 책임이 자격, 문서, 공식 신뢰로 이어집니다. 직업운은 책임을 기록으로 남길 때 강합니다.",
            "honor": "공식 책임과 문서 신뢰가 명예를 만듭니다. 평판은 즉흥적 인기보다 직책, 기록, 자격에서 강하게 붙습니다.",
            "social": "사람을 대할 때 감정보다 신뢰와 절차를 중시합니다. 오래 가는 관계는 책임을 확인한 뒤 깊어집니다.",
            "love": "관계에서는 책임감과 보호하려는 태도가 신뢰를 만듭니다.",
            "marriage": "결혼에서는 책임을 피하지 않는 태도가 생활 안정으로 이어집니다.",
            "personality": "압박을 받으면 감정적으로 흩어지기보다 근거와 절차를 세우는 쪽으로 움직입니다.",
            "life": "인생의 안정은 책임을 피하지 않고 기록과 신뢰로 쌓아갈 때 강해집니다.",
            "timing": "직책, 문서, 자격, 공적 책임이 함께 들어오는 해에 상승 작용이 뚜렷합니다.",
        }.get(domain, sentence or fallback)
    if name == "비겁극재":
        return {
            "money": "돈과 소유를 두고 사람 사이의 몫 문제가 불거집니다. 공동 자금, 지분, 명의는 반드시 분리해야 합니다.",
            "career": "성과의 몫을 두고 동료나 협업자와 기준이 엇갈리기 쉽습니다. 권한과 보상 기준이 분명해야 합니다.",
            "honor": "공동 성과에서 누구의 공로인지가 흐려지면 평판이 흔들립니다. 이름이 남아야 할 일은 처음부터 역할을 분리해야 합니다.",
            "social": "친한 사람일수록 돈, 성과, 책임이 섞이기 쉽습니다. 관계를 오래 두려면 몫과 역할을 먼저 분명히 해야 합니다.",
            "love": "가까운 관계에서 소유욕과 자존심이 강하게 부딪힐 수 있습니다.",
            "marriage": "결혼에서는 가족 돈, 생활비, 명의 문제가 민감하게 떠오르기 쉽습니다.",
            "personality": "자기 몫을 쉽게 넘기지 않고, 손해를 보면 오래 기억하는 성향으로 나타납니다.",
            "life": "인생의 손실은 능력 부족보다 가까운 사람과 몫이 섞일 때 생깁니다. 사람을 얻되 재물 기준은 분리해야 합니다.",
            "timing": "공동 비용, 지분, 성과 배분이 걸린 해에는 관계보다 기준이 먼저입니다.",
        }.get(domain, sentence or fallback)
    if "통관" in name:
        return {
            "money": "재물 문제에서 바로 손실로 가지 않고, 조정과 회수의 길이 남습니다. 거래와 정산은 중간 기준을 세워야 합니다.",
            "career": "서로 맞지 않는 요구를 조정해 일의 순서를 잡습니다. 직업에서는 관리자, 조율자, 실무 연결자의 역할이 살아납니다.",
            "honor": "충돌이 생겨도 바로 평판 손상으로 끝나지 않습니다. 중간에서 기준을 세우고 정리하는 능력이 이름을 지켜냅니다.",
            "social": "관계가 부딪혀도 바로 끊기보다 중간 대화와 역할 조정으로 풉니다. 사람 사이의 균형을 잡는 쪽에 강합니다.",
            "love": "감정 충돌이 바로 끊어지기보다 중간 대화와 조율을 통해 풀립니다.",
            "marriage": "생활 기준이 부딪혀도 조정할 여지가 있습니다. 중간 규칙을 세우면 갈등이 오래 가지 않습니다.",
            "personality": "상반된 생각을 바로 밀어붙이지 않고 중간 기준을 찾아 조정합니다.",
            "life": "큰 전환기에도 한쪽으로 무너지기보다 중간 역할을 통해 길을 다시 잡습니다.",
            "timing": "서로 충돌하는 운이 들어와도 중간 작용이 살아나는 해에는 손실보다 조정과 전환이 크게 나타납니다.",
        }.get(domain, sentence or fallback)
    simple_body = SIMPLE_CYCLE_DOMAIN_BODIES.get(name, {}).get(domain)
    if simple_body:
        return simple_body
    return sentence or fallback


def _cycle_signal_text(signal: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "classical_name",
        "cycle_judgment_label",
        "sentence",
        "decision_reason",
        "source_group",
        "target_group",
        "bridge_group",
        "source_label",
        "target_label",
        "bridge_label",
        "relation",
    ):
        value = signal.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    parts.extend(str(item) for item in signal.get("groups") or [])
    parts.extend(str(item) for item in signal.get("group_labels") or [])
    return " ".join(parts)


def _cycle_signal_domain_score(signal: dict[str, Any], domain: str) -> int:
    text = _cycle_signal_text(signal)
    links = set(str(item) for item in signal.get("domain_links") or [])
    groups = set(str(item) for item in signal.get("groups") or [])
    relation = str(signal.get("relation") or "")
    score = int(signal.get("score") or 0) // 5
    if domain in links:
        score += 30
    domain_keywords: dict[str, tuple[str, ...]] = {
        "money": ("재성", "wealth", "식상생재", "비겁극재", "재극인", "재생관", "편재", "정재", "금액", "수입", "몫"),
        "career": ("관성", "officer", "resource", "output", "재생관", "관인상생", "식신제살", "통근", "투출", "직책", "책임", "평가"),
        "love": ("통관", "관계", "love", "marriage", "peer", "resource", "감정", "조율", "비겁극재"),
        "marriage": ("재생관", "관인상생", "통관", "marriage", "officer", "wealth", "생활", "책임", "기준"),
        "personality": ("통근", "투출", "비겁", "peer", "resource", "통관", "성향", "기준", "반응"),
        "honor": ("관성", "officer", "resource", "재생관", "관인상생", "통근", "투출", "직책", "평판", "책임"),
        "social": ("비겁", "peer", "통관", "비겁극재", "재생관", "관계", "몫", "역할", "조율"),
        "life": ("통근", "투출", "월령", "조후", "통관", "전환", "지속력", "현실화"),
        "timing": ("대운", "세운", "투출", "통근", "월령", "현실화", "전환"),
    }
    score += sum(11 for keyword in domain_keywords.get(domain, ()) if keyword in text)
    if domain == "money" and ("wealth" in groups or "재성" in text):
        score += 26
    if domain == "career" and ({"officer", "resource", "output"} & groups):
        score += 20
    if domain in {"love", "marriage", "social"} and ({"peer", "officer", "wealth", "resource"} & groups):
        score += 12
    if domain in {"honor", "career"} and relation in {"visible_root", "hidden_protrusion"}:
        score += 18
    if domain == "personality" and relation in {"visible_root", "hidden_protrusion", "element_bridge"}:
        score += 18
    if domain == "money" and relation in {"generates", "chain", "controls"}:
        score += 12
    if domain in {"love", "marriage"} and "식상생재 후 재생관" in text:
        score -= 10
    if domain == "love" and "재극인" in text:
        score -= 8
    return max(score, 0)


def _cycle_signal_domain_scores(signal: dict[str, Any]) -> dict[str, int]:
    return {
        domain: score
        for domain in ("money", "career", "love", "marriage", "personality", "honor", "social", "life", "timing")
        if (score := _cycle_signal_domain_score(signal, domain)) > 0
    }


def _cycle_regulation_factor_sections(life_feature_summary: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    profile = life_feature_summary.get("cycle_regulation_context")
    if not isinstance(profile, dict):
        return []
    raw_signals = [signal for signal in profile.get("signals") or [] if isinstance(signal, dict)]
    if not raw_signals:
        return []
    signal_by_id = {str(signal.get("signal_id") or ""): signal for signal in raw_signals}
    selected: list[dict[str, Any]] = []

    def append_signal(signal: dict[str, Any] | None) -> None:
        if not signal:
            return
        if any(id(signal) == id(item) for item in selected):
            return
        selected.append(signal)

    for signal_id in profile.get("top_signal_ids") or []:
        append_signal(signal_by_id.get(str(signal_id)))

    for domain in ("money", "career", "love", "marriage", "honor", "social", "personality", "life", "timing"):
        best_signal = max(
            raw_signals,
            key=lambda item: _cycle_signal_domain_score(item, domain),
            default=None,
        )
        if best_signal and _cycle_signal_domain_score(best_signal, domain) > 0:
            append_signal(best_signal)

    for signal in sorted(raw_signals, key=lambda item: int(item.get("score") or 0), reverse=True):
        append_signal(signal)
        if len(selected) >= limit * 2:
            break

    sections: list[dict[str, Any]] = []
    seen_headings: set[str] = set()
    for signal in selected:
        classical = str(signal.get("classical_name") or signal.get("cycle_judgment_label") or "").strip()
        if not classical:
            continue
        if classical in seen_headings:
            continue
        seen_headings.add(classical)
        sentence = str(signal.get("sentence") or "").strip()
        theory = str(signal.get("classical_theory") or "").strip()
        relation = str(signal.get("relation") or "")
        verdict = str(signal.get("month_command_verdict_label") or signal.get("cycle_judgment_label") or "").strip()
        reason = str(signal.get("decision_reason") or "").strip()
        if relation == "chain" and sentence:
            primary_lead = sentence
        elif theory:
            primary_lead = theory
        else:
            primary_lead = reason
        if "길흉은 다른 조건" in verdict:
            verdict = ""
        lead_parts = [part for part in (primary_lead, verdict, reason) if part]
        lead = " ".join(lead_parts[:2]) if lead_parts else f"{classical} 작용이 월령 기준 판정에 들어갑니다."
        domain_scores = _cycle_signal_domain_scores(signal)
        body_domains = {
            str(domain)
            for domain in signal.get("domain_links") or []
            if str(domain) in DOMAIN_FACTOR_TERMS
        }
        body_domains.update(domain for domain, score in domain_scores.items() if score >= 45)
        domain_links = _domain_labels(body_domains)
        domain_bodies = {
            domain: _cycle_domain_body(signal, domain, lead)
            for domain in body_domains
            if str(domain) in DOMAIN_FACTOR_TERMS
        }
        sections.append(
            _factor_section(
                layer="cycle_regulation",
                source_label="상생상극",
                heading=classical,
                lead=lead,
                domain_labels=domain_links,
                domain_bodies=domain_bodies,
                domain_scores=domain_scores,
            )
        )
        if len(sections) >= limit:
            break
    return sections


def _summary_heading(text: str, layer: str, source_label: str) -> str:
    if layer == "element_combination":
        match = re.search(r"([甲乙丙丁戊己庚辛壬癸]{2,3})\s*배합", text)
        if match:
            return f"{match.group(1)} 오행 배합"
    if layer == "stem_reception":
        match = re.search(r"([甲乙丙丁戊己庚辛壬癸])일간은\s*([甲乙丙丁戊己庚辛壬癸])[을를]\s*([가-힣]+?)(?:으로|로)", text)
        if match:
            return f"{match.group(1)}일간과 {match.group(2)} {match.group(3)}의 관계"
    if layer == "ten_god_interaction":
        match = re.search(r"사주에서\s*([가-힣]+)[이가]\s*([가-힣]+)[을를]\s*상대", text)
        if match:
            return f"{match.group(1)}-{match.group(2)} 십신 관계"
    first = text.split(".", 1)[0].strip()
    return first[:32] if first else source_label


def _summary_factor_sections(
    values: Any,
    *,
    layer: str,
    source_label: str,
    limit: int,
) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    sections: list[dict[str, Any]] = []
    for value in values[:limit]:
        text = str(value or "").strip()
        if not text:
            continue
        display_text = (
            text.replace("당신의 타고난 사주에서는 ", "")
            .replace("당신의 사주에서 ", "사주에서 ")
            .replace(" 해석값은 ", " 관계는 ")
        )
        display_text = _fix_factor_particle_text(display_text)
        sections.append(
            _factor_section(
                layer=layer,
                source_label=source_label,
                heading=_summary_heading(text, layer, source_label),
                lead=display_text,
                domain_labels=["재물", "직업", "연애·관계", "결혼·가정"] if layer != "stem_reception" else [],
            )
        )
    return sections


def _product_factor_sections(product_payload: dict[str, Any]) -> list[dict[str, Any]]:
    life_feature_summary = product_payload.get("life_feature_summary") or {}
    if not isinstance(life_feature_summary, dict):
        return []
    sections: list[dict[str, Any]] = []
    season_section = _season_factor_section(life_feature_summary)
    if season_section:
        sections.append(season_section)
    month_governance_section = _month_governance_factor_section(life_feature_summary)
    if month_governance_section:
        sections.append(month_governance_section)
    sections.extend(_branch_reality_factor_sections(life_feature_summary))
    sections.extend(_cycle_principle_matrix_factor_sections(life_feature_summary))
    sections.extend(_cycle_regulation_factor_sections(life_feature_summary))
    sections.extend(_combination_factor_sections(life_feature_summary))
    sections.extend(
        _summary_factor_sections(
            life_feature_summary.get("element_combination_summary"),
            layer="element_combination",
            source_label="오행 배합",
            limit=3,
        )
    )
    sections.extend(
        _summary_factor_sections(
            life_feature_summary.get("stem_reception_summary"),
            layer="stem_reception",
            source_label="일간 수용값",
            limit=3,
        )
    )
    sections.extend(
        _summary_factor_sections(
            life_feature_summary.get("ten_god_interaction_summary"),
            layer="ten_god_interaction",
            source_label="십신 배합",
            limit=3,
        )
    )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for section in sections:
        key = (str(section.get("layer") or ""), str(section.get("heading") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(section)
    return deduped


def _product_report_seed(product_payload: dict[str, Any]) -> dict[str, Any]:
    items = [dict(item) for item in product_payload.get("items", []) if isinstance(item, dict)]
    card_seeds = [_product_item_card_seed(item) for item in items]
    product_sections = [dict(section) for section in product_payload.get("sections", []) if isinstance(section, dict)]
    premium_section_seeds = [_premium_section_seed(section) for section in product_sections] or card_seeds
    life_feature_summary = product_payload.get("life_feature_summary")
    if not isinstance(life_feature_summary, dict):
        life_feature_summary = {}
    return {
        "schema_version": "premium_profile_report_v1",
        "source_schema_version": product_payload.get("schema_version", ""),
        "source_engine_manifest": product_payload.get("engine_manifest", {}),
        "product_tier": product_payload.get("product_tier", "free"),
        "target_years": list(product_payload.get("target_years") or []),
        "title": "AI 사주 : 이현",
        "overview": "",
        "mobile_cards": card_seeds,
        "web_sections": [],
        "premium_sections": premium_section_seeds,
        "reading_sections": [],
        "factor_sections": _product_factor_sections(product_payload),
        "premium_candidate_sections": list(product_payload.get("premium_candidate_sections") or []),
        "premium_detail_sections": list(product_payload.get("premium_detail_sections") or []),
        "premium_profile_contract": dict(product_payload.get("premium_profile_contract") or {}),
        "domain_decision_facets": dict(life_feature_summary.get("domain_decision_facets") or {}),
        "timing_decision_facets": dict(life_feature_summary.get("timing_decision_facets") or {}),
        "output_goal_coverage": dict(life_feature_summary.get("output_goal_coverage") or {}),
        "notices": [],
        "catalog_entries": [],
        "quality_flags": [],
    }


REPORT_TIMING_COVERAGE_SOURCE_ALIASES: dict[str, tuple[str, ...]] = {
    "대운 구간별 중심 과제": ("decade_profile",),
    "상승 연도": ("good_years",),
    "수입 강세 연도": ("income_peak",),
    "재물 강세 연도": ("money_peak",),
    "자산화 연도": ("asset_year",),
    "채권·미수금 회수 연도": ("receivables_recovery_year", "contract_caution"),
    "공동자금 주의 연도": ("shared_money_caution",),
    "계약·명의 주의 연도": ("contract_caution", "caution_years"),
    "부채·보증 주의 연도": ("debt_guarantee_caution", "shared_money_caution", "contract_caution"),
    "가족재산 주의 연도": ("family_asset_caution", "shared_money_caution", "family_caution"),
    "재물 주의 연도": ("contract_caution",),
    "직업 상승 연도": ("career_rise",),
    "권한 상승 연도": ("authority_year",),
    "보상 상승 연도": ("compensation_rise", "career_rise", "authority_year"),
    "직업 분야 전환 연도": ("career_domain_shift", "career_change"),
    "직업 전환 연도": ("career_change",),
    "소속 변화 연도": ("career_change", "good_years"),
    "직업 부담 연도": ("career_burden",),
    "직업 독립 연도": ("career_independence_year", "career_change", "good_years"),
    "연애 강세 연도": ("love_opening", "relationship_progress_year"),
    "새 인연 연도": ("love_opening", "relationship_progress_year", "good_years"),
    "관계 진전 연도": ("relationship_progress_year",),
    "재회·정리 연도": ("relationship_recovery_year",),
    "이별·정리 연도": ("separation_closure_year", "relationship_recovery_year", "love_caution"),
    "관계 주의 연도": ("love_caution",),
    "주변 개입 주의 연도": ("external_interference_caution", "love_caution"),
    "혼인 결정 연도": ("marriage_decision",),
    "결혼 적기": ("marriage_decision", "housing_preparation_year", "relationship_progress_year"),
    "주거·생활 준비 연도": ("housing_preparation_year",),
    "부부 재정 연도": ("couple_finance_year", "housing_preparation_year", "marriage_decision"),
    "가족·주거 변동 연도": ("family_caution",),
    "자녀·양육 책임 연도": ("child_rearing_year", "family_caution"),
    "결혼 주의 연도": ("family_caution", "love_caution", "caution_years"),
    "인생 전환 연도": ("good_years", "caution_years"),
    "주의 연도": ("caution_years",),
    "회복 연도": ("good_years",),
    "말년 안정 연도": ("decade_profile",),
}


def _timing_coverage_value(item: dict[str, Any]) -> str:
    parts: list[str] = []
    year = item.get("year")
    if year not in (None, ""):
        parts.append(str(year))
    age_label = str(item.get("age_label") or "").strip()
    age = item.get("age")
    if age_label:
        parts.append(age_label)
    elif age not in (None, ""):
        parts.append(f"{age}세")
    focus = str(item.get("focus") or item.get("event_label") or "").strip()
    if focus:
        parts.append(focus)
    return " · ".join(parts)


def _timing_collection_coverage(required: str, timing_decision: dict[str, Any], key: str) -> dict[str, Any]:
    collection = timing_decision.get(key)
    if not isinstance(collection, list) or not collection:
        return {}
    first = next((item for item in collection if isinstance(item, dict)), None)
    if not first:
        return {}
    if key == "decade_profile":
        row_candidates = [
            item for item in collection if isinstance(item, dict)
        ]
        row = row_candidates[-1] if required == "말년 안정 연도" else row_candidates[0]
        nested = row.get("good") if isinstance(row.get("good"), dict) else None
        if not nested and isinstance(row.get("caution"), dict):
            nested = row.get("caution")
        source_item = nested if isinstance(nested, dict) else row
        age_band = str(row.get("age_band") or "").strip()
        source_value = _timing_coverage_value(source_item)
        return {
            "required_conclusion": required,
            "status": "indirect",
            "source_type": "timing_year_list",
            "source_key": key,
            "source_label": age_band or "대운 구간",
            "count": len(collection),
            "year": source_item.get("year"),
            "age": source_item.get("age"),
            "focus": str(source_item.get("focus") or source_item.get("event_label") or ""),
            "score": source_item.get("score"),
            "value": f"{age_band} · {source_value}" if age_band and source_value else source_value or age_band,
        }
    return {
        "required_conclusion": required,
        "status": "indirect",
        "source_type": "timing_year_list",
        "source_key": key,
        "source_label": str(first.get("event_label") or first.get("focus") or key),
        "count": len(collection),
        "year": first.get("year"),
        "age": first.get("age"),
        "focus": str(first.get("focus") or first.get("event_label") or ""),
        "score": first.get("score"),
        "value": _timing_coverage_value(first),
    }


def _timing_event_coverage(required: str, timing_decision: dict[str, Any]) -> dict[str, Any]:
    event_years = timing_decision.get("event_years")
    if not isinstance(event_years, dict):
        return {}
    for key in REPORT_TIMING_COVERAGE_SOURCE_ALIASES.get(required, ()):
        event = event_years.get(key)
        if not isinstance(event, dict):
            continue
        return {
            "required_conclusion": required,
            "status": "covered",
            "source_type": "timing_event",
            "source_key": key,
            "source_label": str(event.get("event_label") or required),
            "year": event.get("year"),
            "age": event.get("age"),
            "focus": str(event.get("focus") or ""),
            "score": event.get("score"),
            "value": _timing_coverage_value(event),
        }
    return {}


def _timing_required_coverage(required: str, timing_decision: dict[str, Any]) -> dict[str, Any]:
    event = _timing_event_coverage(required, timing_decision)
    if event:
        return event
    for key in REPORT_TIMING_COVERAGE_SOURCE_ALIASES.get(required, ()):
        collection = _timing_collection_coverage(required, timing_decision, key)
        if collection:
            return collection
    return {
        "required_conclusion": required,
        "status": "missing",
        "source_type": "",
        "source_key": "",
        "source_label": "",
    }


def _refresh_output_goal_coverage_timing(
    coverage: dict[str, Any] | None,
    timing_decision: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(coverage, dict) or not isinstance(timing_decision, dict):
        return dict(coverage or {})
    refreshed = dict(coverage)
    timing_entries = [
        item
        for item in refreshed.get("timing", [])
        if isinstance(item, dict) and str(item.get("required_conclusion") or "").strip()
    ]
    refreshed_by_required = {
        str(item.get("required_conclusion")): _timing_required_coverage(
            str(item.get("required_conclusion")),
            timing_decision,
        )
        for item in timing_entries
    }
    refreshed["timing"] = list(refreshed_by_required.values())
    domains = refreshed.get("domains")
    if isinstance(domains, dict):
        next_domains: dict[str, list[dict[str, Any]]] = {}
        for domain, items in domains.items():
            next_items: list[dict[str, Any]] = []
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                required = str(item.get("required_conclusion") or "").strip()
                if required in refreshed_by_required:
                    next_items.append(dict(refreshed_by_required[required]))
                else:
                    timing_entry = _timing_required_coverage(required, timing_decision)
                    if str(timing_entry.get("status") or "") != "missing":
                        next_items.append(dict(timing_entry))
                    else:
                        next_items.append(dict(item))
            next_domains[str(domain)] = next_items
        refreshed["domains"] = next_domains
    all_entries: list[dict[str, Any]] = []
    refreshed_domains = refreshed.get("domains")
    if isinstance(refreshed_domains, dict):
        for items in refreshed_domains.values():
            all_entries.extend(item for item in items or [] if isinstance(item, dict))
    all_entries.extend(item for item in refreshed.get("timing", []) if isinstance(item, dict))
    missing_count = sum(1 for item in all_entries if str(item.get("status") or "") == "missing")
    refreshed["covered_count"] = len(all_entries) - missing_count
    refreshed["missing_count"] = missing_count
    refreshed["status"] = "complete" if missing_count == 0 else "partial"
    return refreshed


def _domain_key(value: dict[str, Any]) -> str:
    raw = f"{value.get('domain', '')} {value.get('domain_label', '')} {value.get('heading', '')} {value.get('title', '')}"
    if "money" in raw or "재물" in raw or "돈" in raw:
        return "money"
    if "career" in raw or "직업" in raw or "성취" in raw:
        return "career"
    if "love" in raw or "연애" in raw or "인연" in raw:
        return "love"
    if "marriage" in raw or "결혼" in raw or "가정" in raw:
        return "marriage"
    if "personality" in raw or "성향" in raw or "성격" in raw:
        return "personality"
    return str(value.get("domain") or "general")


def _compact_percentile(value: str) -> str:
    text = str(value or "").strip()
    compacted = text.replace(" 안팎", "")
    match = re.search(r"상위\s*(\d+)%", compacted)
    if match:
        rank = int(match.group(1))
        if rank <= 15:
            return "최상위권"
        if rank <= 20:
            return "상위권"
        if rank <= 35:
            return "중상위권"
        return "평균권"
    if compacted in {"최상위권", "상위권", "중상위권", "평균권", "주의 필요", "약세", "주의"}:
        return compacted
    if compacted == "보완 필요":
        return "주의 필요"
    if compacted == "평균권 하단":
        return "평균권"
    if compacted in {"보완 필요 구간", "주의 필요 구간", "평균 이하"}:
        return "주의 필요"
    if compacted == "낮음":
        return "약세"
    return compacted


def _axis_map(product_item: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not product_item:
        return {}
    axes = product_item.get("feature_axes", [])
    if not isinstance(axes, list):
        return {}
    return {str(axis.get("key")): dict(axis) for axis in axes if isinstance(axis, dict) and axis.get("key")}


def _feature_value(
    product_item: dict[str, Any] | None,
    key: str,
    *,
    fallback_score: int | None = None,
) -> str:
    axis = _axis_map(product_item).get(key)
    if axis:
        percentile = _compact_percentile(str(axis.get("percentile_label") or ""))
        if percentile:
            return percentile
        score = axis.get("score")
        if isinstance(score, int):
            return _score_value(score)
    if fallback_score is not None:
        return _score_value(fallback_score)
    return "확인 필요"


def _feature_score(
    product_item: dict[str, Any] | None,
    key: str,
    *,
    fallback_score: int | None = None,
) -> int | None:
    axis = _axis_map(product_item).get(key)
    if axis:
        score = axis.get("score")
        if isinstance(score, int):
            return score
    return fallback_score


def _feature_value_blended(
    product_item: dict[str, Any] | None,
    key: str,
    fallback_score: int | None,
    *,
    cap: str | None = None,
) -> str:
    score = _feature_score(product_item, key)
    if isinstance(score, int) and isinstance(fallback_score, int):
        blended_score = round((score + fallback_score) / 2)
        if fallback_score >= 82:
            blended_score = max(blended_score, fallback_score - 24)
        value = _score_value(blended_score)
    elif isinstance(score, int):
        value = _score_value(score)
    elif isinstance(fallback_score, int):
        value = _score_value(fallback_score)
    else:
        return _feature_value(product_item, key)
    if cap == "중상위권" and value in {"최상위권", "상위권"}:
        return "중상위권"
    return value


def _feature_value_strongest(
    product_item: dict[str, Any] | None,
    keys: tuple[str, ...],
    *,
    fallback_score: int | None = None,
    cap: str | None = None,
) -> str:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores and isinstance(fallback_score, int):
        scores.append(fallback_score)
    if not scores:
        return "확인 필요"
    value = _score_value(max(scores))
    if cap == "중상위권" and value in {"최상위권", "상위권"}:
        return "중상위권"
    return value


def _feature_value_average(
    product_item: dict[str, Any] | None,
    keys: tuple[str, ...],
    *,
    fallback_score: int | None = None,
    cap: str | None = None,
) -> str:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores and isinstance(fallback_score, int):
        scores.append(fallback_score)
    if not scores:
        return "확인 필요"
    value = _score_value(round(sum(scores) / len(scores)))
    if cap == "중상위권" and value in {"최상위권", "상위권"}:
        return "중상위권"
    return value


def _bounded_metric_score(score: int | float | None, *, cap: int | None = None) -> int | None:
    if not isinstance(score, (int, float)):
        return None
    value = max(0, min(100, round(float(score))))
    if isinstance(cap, int):
        value = min(value, cap)
    return value


def _feature_score_blended(
    product_item: dict[str, Any] | None,
    key: str,
    fallback_score: int | None,
    *,
    cap: int | None = None,
) -> int | None:
    score = _feature_score(product_item, key)
    if isinstance(score, int) and isinstance(fallback_score, int):
        blended_score = round((score + fallback_score) / 2)
        if fallback_score >= 82:
            blended_score = max(blended_score, fallback_score - 24)
        return _bounded_metric_score(blended_score, cap=cap)
    if isinstance(score, int):
        return _bounded_metric_score(score, cap=cap)
    if isinstance(fallback_score, int):
        return _bounded_metric_score(fallback_score, cap=cap)
    return None


def _feature_score_strongest(
    product_item: dict[str, Any] | None,
    keys: tuple[str, ...],
    *,
    fallback_score: int | None = None,
    cap: int | None = None,
) -> int | None:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores and isinstance(fallback_score, int):
        scores.append(fallback_score)
    if not scores:
        return None
    return _bounded_metric_score(max(scores), cap=cap)


def _feature_score_average(
    product_item: dict[str, Any] | None,
    keys: tuple[str, ...],
    *,
    fallback_score: int | None = None,
    cap: int | None = None,
) -> int | None:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores and isinstance(fallback_score, int):
        scores.append(fallback_score)
    if not scores:
        return None
    return _bounded_metric_score(sum(scores) / len(scores), cap=cap)


def _risk_control_score(score: int | None) -> int | None:
    if not isinstance(score, int):
        return None
    if score >= 75:
        return 40
    if score >= 62:
        return 45
    if score >= 48:
        return 58
    return 78


def _combined_stability_score(product_item: dict[str, Any] | None, *keys: str) -> int | None:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores:
        return None
    return _bounded_metric_score(min(scores))


def _contract_name_stability_score(product_item: dict[str, Any] | None) -> int | None:
    risk_score = _engine_score(product_item, "risk_score")
    if risk_score >= 62:
        return _risk_control_score(risk_score)
    return _combined_stability_score(product_item, "deal_selection", "loss_avoidance")


def _score_from_axis_value(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text or text == "확인 필요":
        return None
    if text in {"최상위권", "매우 좋음", "안정"}:
        return 88
    if text in {"상위권", "좋음"}:
        return 82
    if text in {"중상위권", "양호"}:
        return 74
    if text in {"평균권", "보통"}:
        return 56
    if text in {"주의 필요", "주의"}:
        return 38
    if text in {"약세", "위험", "낮음"}:
        return 28
    return None


def _feature_rank(
    product_item: dict[str, Any] | None,
    candidates: list[tuple[str, str]],
) -> tuple[str, str, int | None]:
    ranked: list[tuple[int, str, str]] = []
    for key, label in candidates:
        score = _feature_score(product_item, key)
        if isinstance(score, int):
            ranked.append((score, key, label))
    if not ranked:
        return candidates[0][1] if candidates else "핵심 항목", candidates[0][0] if candidates else "", None
    score, key, label = max(ranked, key=lambda item: item[0])
    return label, key, score


def _feature_rank_with_bias(
    product_item: dict[str, Any] | None,
    candidates: list[tuple[str, str, int]],
) -> tuple[str, str, int | None]:
    ranked: list[tuple[int, int, str, str, int]] = []
    for order, (key, label, bias) in enumerate(candidates):
        score = _feature_score(product_item, key)
        if isinstance(score, int):
            ranked.append((score + bias, -order, key, label, score))
    if not ranked:
        if not candidates:
            return "핵심 항목", "", None
        key, label, _bias = candidates[0]
        return label, key, None
    _weighted, _order, key, label, raw_score = max(ranked, key=lambda item: (item[0], item[1]))
    return label, key, raw_score


def _dominant_feature_value_with_bias(
    product_item: dict[str, Any] | None,
    candidates: list[tuple[str, str, int]],
    *,
    fallback_score: int | None = None,
) -> tuple[str, str]:
    label, key, score = _feature_rank_with_bias(product_item, candidates)
    return label, _feature_value(product_item, key, fallback_score=score or fallback_score)


def _dominant_feature_value(
    product_item: dict[str, Any] | None,
    candidates: list[tuple[str, str]],
    *,
    fallback_score: int | None = None,
) -> tuple[str, str]:
    label, key, score = _feature_rank(product_item, candidates)
    return label, _feature_value(product_item, key, fallback_score=score or fallback_score)


def _ranked_feature_verdict(label: str, score: int | None) -> str:
    if not isinstance(score, int):
        return f"{label} 확인 필요"
    if score >= 90:
        return f"{label} 최상위권"
    if score >= 80:
        return f"{label} 상위권"
    if score >= 70:
        return f"{label} 중상위권"
    if score >= 55:
        return f"{label} 평균권"
    if score >= 40:
        return f"{label} 주의 필요"
    return f"{label} 약세"


def _topic_particle(label: str) -> str:
    text = str(label or "").strip()
    if not text:
        return "은"
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "은" if (code - 0xAC00) % 28 else "는"
    return "은"


def _subject_particle(label: str) -> str:
    text = str(label or "").strip()
    if not text:
        return "이"
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "이" if (code - 0xAC00) % 28 else "가"
    return "이"


def _object_particle(label: str) -> str:
    text = str(label or "").strip()
    if not text:
        return "을"
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "을" if (code - 0xAC00) % 28 else "를"
    return "을"


def _fix_factor_particle_text(text: str) -> str:
    fixed = str(text or "")
    labels = sorted(set(TEN_GOD_LABEL_BY_KEY.values()), key=len, reverse=True)
    for label in labels:
        fixed = re.sub(rf"{re.escape(label)}[이가](?=\s)", f"{label}{_subject_particle(label)}", fixed)
        fixed = re.sub(rf"{re.escape(label)}[을를](?=\s)", f"{label}{_object_particle(label)}", fixed)
    return fixed


def _and_particle(label: str) -> str:
    text = str(label or "").strip()
    if not text:
        return "과"
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "과" if (code - 0xAC00) % 28 else "와"
    return "과"


def _feature_sentence(label: str, value: str) -> str:
    if value in {"보완 필요", "주의 필요"}:
        return f"{label} 주의 필요"
    if value in {"약세", "낮음"}:
        return f"{label} 약세"
    if value == "확인 필요":
        return f"{label} 확인 필요"
    return f"{label} {value}"


def _feature_clause(sentence: str) -> str:
    text = str(sentence or "").strip().rstrip(".")
    if text.endswith("입니다"):
        text = text[: -len("입니다")]
    for marker in ("은 ", "는 "):
        if marker in text:
            label, value = text.split(marker, 1)
            return f"{label}{_subject_particle(label)} {value}"
    return text


def _risk_rank(
    product_item: dict[str, Any] | None,
    candidates: list[tuple[str, str, bool]],
    *,
    fallback_risk: int = 0,
) -> tuple[str, int]:
    """Return the highest risk. bool means the feature is good when high."""
    ranked: list[tuple[int, str]] = []
    for key, label, inverse in candidates:
        score = _feature_score(product_item, key)
        if isinstance(score, int):
            severity = 100 - score if inverse else score
            ranked.append((severity, label))
    if not ranked:
        return candidates[0][1] if candidates else "관리 필요도", fallback_risk
    severity, label = max(ranked, key=lambda item: item[0])
    return label, severity


def _risk_text_caution(domain: str, product_item: dict[str, Any] | None) -> str:
    if not product_item:
        return ""
    risk_text = str(product_item.get("risk") or "")
    if not risk_text:
        return ""
    if domain == "money":
        if "나눌 몫" in risk_text or "몫" in risk_text:
            return "지분·명의 안정성"
        if "정산" in risk_text and "지출" in risk_text:
            return "지분·명의 안정성"
        if "정산" in risk_text:
            return "수익 배분 안정성"
        if "계약" in risk_text or "문서" in risk_text or "지급" in risk_text:
            return "계약·명의 안정성"
        if "지출" in risk_text:
            return "소비 통제력"
        if "손에 남는 돈" in risk_text:
            return "자산 보존력"
    if domain == "career":
        if "권한" in risk_text and "평가" in risk_text:
            return "책임·권한 균형"
        if "권한" in risk_text and "책임" in risk_text:
            return "책임·권한 균형"
        if "일정 압박" in risk_text or "일정" in risk_text:
            return "업무 지속력"
        if "책임" in risk_text:
            return "책임 과중"
    if domain == "love":
        if "거리감" in risk_text or "거리" in risk_text:
            return "표현 거리감"
        if "표현" in risk_text or "연락" in risk_text:
            return "표현과 연락 엇갈림"
        if "감정 반응" in risk_text:
            return "감정 반응 과열"
        if "오해" in risk_text:
            return "오해 장기화"
    if domain == "marriage":
        if "생활비" in risk_text and "주거" in risk_text:
            return "생활비·주거 기준 충돌"
        if "주거 조건" in risk_text or "주거" in risk_text:
            return "주거 조건 압박"
        if "압박" in risk_text:
            return "가족·주거 변수"
        if "현실 기준" in risk_text:
            return "생활 기준 충돌"
    return ""


def _score_value(score: int) -> str:
    if score >= 90:
        return "최상위권"
    if score >= 80:
        return "상위권"
    if score >= 70:
        return "중상위권"
    if score >= 55:
        return "평균권"
    if score >= 40:
        return "주의 필요"
    return "약세"


def _personality_feature_axes_from_profile(profile: dict[str, Any]) -> list[dict[str, Any]]:
    axes: list[dict[str, Any]] = []
    if not isinstance(profile, dict):
        return axes
    coordinate_scores = {
        str(item.get("label") or ""): int(item.get("score") or 0)
        for item in profile.get("coordinate_axes") or []
        if isinstance(item, dict) and isinstance(item.get("score"), int)
    }
    label_to_coordinate = {
        "판단 방식": "선택의 방향",
        "대인 태도": "관계의 거리",
        "감정 처리": "관계의 거리",
        "압박 대응": "압박 반응",
        "실행 방식": "실행 속도",
        "몰입 방향": "선택의 방향",
    }
    for index, card in enumerate(profile.get("cards") or []):
        if not isinstance(card, dict):
            continue
        label = str(card.get("label") or "").strip()
        if not label:
            continue
        score = coordinate_scores.get(label_to_coordinate.get(label, ""), 0)
        if not score:
            score = 74 if str(card.get("tone") or "") == "strong" else 62 if str(card.get("tone") or "") == "watch" else 68
        key = re.sub(r"[^0-9A-Za-z가-힣]+", "_", label).strip("_") or f"personality_{index + 1}"
        axes.append(
            {
                "key": f"personality_{key}",
                "category": "personality",
                "label": label,
                "score": score,
                "percentile_label": _score_value(score),
                "strength_label": str(card.get("value") or _score_value(score)),
                "confidence": "medium",
                "basis_codes": [f"personality_profile:{key}"],
                "counter_signals": [],
                "description": str(card.get("body") or "").strip(),
            }
        )
    if axes:
        return axes[:6]
    for index, item in enumerate(profile.get("axes") or []):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        score = item.get("score")
        if not label or not isinstance(score, int):
            continue
        key = re.sub(r"[^0-9A-Za-z가-힣]+", "_", label).strip("_") or f"personality_axis_{index + 1}"
        axes.append(
            {
                "key": f"personality_{key}",
                "category": "personality",
                "label": label,
                "score": score,
                "percentile_label": _score_value(score),
                "strength_label": str(item.get("value") or _score_value(score)),
                "confidence": "medium",
                "basis_codes": [f"personality_profile_axis:{key}"],
                "counter_signals": [],
                "description": str(item.get("body") or "").strip(),
            }
        )
    return axes[:6]


def _cap_top_rank(value: str, *, cap: str = "상위권") -> str:
    return cap if str(value or "") == "최상위권" else str(value or "")


def _risk_value(score: int) -> str:
    if score >= 62:
        return "주의"
    if score >= 48:
        return "보통"
    return "낮음"


def _risk_control_value(score: int) -> str:
    if score >= 62:
        return "낮음"
    if score >= 48:
        return "보통"
    return "안정"


def _caution_phrase(label: str, score: int) -> str:
    if score >= 62:
        if any(word in label for word in ("주의", "불균형", "과중", "과다", "충돌", "압박", "차이", "약화", "장기화", "문제")):
            return label
        return f"{label} 주의"
    return "뚜렷한 약점 적음"


def _inverse_risk_value(score: int | None) -> str:
    if score is None:
        return "확인 필요"
    if score >= 80:
        return "낮음"
    if score >= 60:
        return "보통"
    return "주의"


def _combined_inverse_risk_value(product_item: dict[str, Any] | None, *keys: str) -> str:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores:
        return "확인 필요"
    return _inverse_risk_value(min(scores))


def _stability_value(score: int | None) -> str:
    if score is None:
        return "확인 필요"
    if score >= 80:
        return "안정"
    if score >= 60:
        return "보통"
    return "낮음"


def _combined_stability_value(product_item: dict[str, Any] | None, *keys: str) -> str:
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in keys)
        if isinstance(score, int)
    ]
    if not scores:
        return "확인 필요"
    return _stability_value(min(scores))


def _contract_name_stability_value(product_item: dict[str, Any] | None) -> str:
    risk_score = _engine_score(product_item, "risk_score")
    if risk_score >= 62:
        return "낮음"
    return _combined_stability_value(product_item, "deal_selection", "loss_avoidance")


def _risk_sentence_value(score: int) -> str:
    value = _risk_value(score)
    return {
        "높음": "높습니다",
        "주의": "주의해야 합니다",
        "보통": "보통입니다",
        "낮음": "낮습니다",
    }.get(value, f"{value}입니다")


def _engine_score(product_item: dict[str, Any] | None, key: str, default: int = 0) -> int:
    if not product_item:
        return default
    value = product_item.get(key, default)
    return value if isinstance(value, int) else default


def _strength_from_score(score_label: str) -> str:
    if "매우 강함" in score_label:
        return "매우 강합니다"
    if "강함" in score_label:
        return "강합니다"
    if "주의" in score_label:
        return "주의가 큽니다"
    return "선명합니다"


def _grade_strength(value: str) -> int:
    text = str(value or "")
    if "최상위권" in text:
        return 5
    if "상위권" in text:
        return 4
    if "중상위권" in text:
        return 3
    if "평균권" in text or "보통" in text:
        return 2
    if "보완 필요" in text or "주의 필요" in text:
        return 1
    if "약세" in text or "낮음" in text:
        return 0
    return 2


def _money_summary(product_item: dict[str, Any] | None, caution: str) -> str:
    income = _feature_value(product_item, "income_expansion")
    asset = _feature_value(product_item, "asset_retention")
    skill = _feature_value(product_item, "business_expansion")
    income_strength = _grade_strength(income)
    asset_strength = _grade_strength(asset)
    skill_strength = _grade_strength(skill)
    if income_strength >= 4 and asset_strength >= 4:
        first = "재물운은 현금 유입과 자산화가 함께 강하게 나타납니다."
        second = "급여, 성과급, 계약금처럼 금액이 분명한 돈에서 유리합니다."
        fourth = "부동산, 지분, 장기 계약처럼 권리가 남는 재산으로 옮길 때 규모가 커집니다."
    elif income_strength >= 4:
        first = "수입 창출력은 강합니다."
        second = "성과가 금액으로 환산되는 자리에서 보수 단위가 올라갑니다."
        fourth = "재물 규모는 들어온 현금을 권리와 소유가 남는 재산으로 옮길 때 커집니다."
    elif asset_strength >= 4:
        first = "자산화 능력이 강합니다."
        second = "한 번 확보한 수입을 소비보다 소유권이 남는 방향으로 굳히는 사주입니다."
        fourth = "현금보다 등기, 지분, 장기 보유 자산에서 재물의 무게가 커집니다."
    elif income_strength >= 3:
        first = "수입을 만들어내는 기반은 평균보다 우세합니다."
        second = "일의 대가가 확인되는 자리에서 재물운이 분명하게 살아납니다."
        fourth = "반복 수입과 고정 거래를 확보할수록 재물의 폭이 넓어집니다."
    else:
        first = "재물은 한 번의 큰 수익보다 반복 수입에서 형성됩니다."
        second = "작은 수입이라도 고정적으로 들어오는 자리가 있어야 재물이 안정됩니다."
        fourth = "수입처를 무리하게 넓히기보다 오래 유지되는 돈의 자리를 먼저 만들어야 합니다."
    skill_sentence = "기술, 말, 결과물이 직접적인 수입 근거가 됩니다." if skill_strength >= 2 else fourth
    if "공동" in caution or "정산" in caution:
        third = "가까운 사람과 자금을 섞으면 명의와 지분이 상대 쪽으로 기울기 쉽습니다."
        fifth = "호의로 시작한 금전 관계가 권리 다툼으로 바뀌기 쉽습니다."
    elif "계약" in caution or "문서" in caution:
        third = "계약 조건이 흐리면 받을 돈이 늦어지거나 깎입니다."
        fifth = "지급일, 수수료, 환불 조건은 문서로 남겨야 합니다."
    else:
        third = _plain_caution_sentence(caution)
        fifth = ""
    return " ".join(part for part in (first, second, skill_sentence, third, fifth) if part)


def _career_summary(product_item: dict[str, Any] | None, caution: str) -> str:
    achievement = _feature_value(product_item, "career_achievement")
    recognition = _feature_value(product_item, "reputation_maintenance")
    expertise = _feature_value(product_item, "academic_expertise")
    if _grade_strength(achievement) >= 4 and _grade_strength(recognition) >= 4:
        first = "직업운은 성과가 공식 평가와 직함으로 남는 사주입니다."
        second = "남이 정리하지 못한 일을 기준과 절차로 정리할 때 존재감이 커집니다."
    elif _grade_strength(achievement) >= 3:
        first = "직업에서는 맡은 일을 결과물로 증명하는 능력이 강합니다."
        second = "담당 범위가 분명한 자리에서 성취가 자기 이름으로 남습니다."
    else:
        first = "직업운은 직함보다 실제 역할이 분명할 때 강해집니다."
        second = "역할이 흐린 자리보다 해야 할 일과 평가 기준이 정해진 자리가 낫습니다."
    expertise_sentence = "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다." if _grade_strength(expertise) >= 4 else "평가 기준이 뚜렷한 자리에서 이력이 제대로 남습니다."
    if "권한" in caution or "책임" in caution:
        third = "책임은 커지는데 결정권이 없는 자리는 피해야 합니다."
        fourth = "실무만 떠안고 성과의 이름을 가져가지 못하면 경력 손상이 남습니다."
    elif "조직" in caution:
        third = "기준이 자주 바뀌는 조직에서는 판단 부담과 심리적 소모가 남습니다."
        fourth = "조직을 고를 때는 직함보다 결재권과 평가 기준을 먼저 확인해야 합니다."
    else:
        third = _plain_caution_sentence(caution)
        fourth = ""
    return " ".join(part for part in (first, second, expertise_sentence, third, fourth) if part)


def _love_summary(product_item: dict[str, Any] | None, caution: str) -> str:
    stability = _feature_value(product_item, "relationship_stability")
    expression = _feature_value(product_item, "communication_expression")
    opening = _feature_value(product_item, "interpersonal_influence")
    if _grade_strength(stability) >= 4:
        first = "연애는 깊어질수록 오래 가는 사주입니다."
        second = "가벼운 설렘보다 책임 있는 태도를 보이는 상대에게 마음이 움직입니다."
    elif _grade_strength(expression) >= 4:
        first = "호감은 말과 태도에서 분명하게 드러납니다."
        second = "좋아하는 사람이 생기면 관계를 공식화하려는 의지가 강해집니다."
    elif _grade_strength(opening) >= 3:
        first = "인연은 열리지만 관계가 깊어지기까지 시간이 필요합니다."
        second = "처음 끌림보다 반복해서 확인되는 태도가 더 중요합니다."
    else:
        first = "연애는 만남의 수보다 상대를 가려 만나는 쪽에 가깝습니다."
        second = "쉽게 설레기보다 오래 볼 수 있는 사람인지 먼저 확인합니다."
    expression_sentence = "호감이 말과 행동으로 확인될 때 상대도 이 관계를 진지하게 받아들입니다." if _grade_strength(expression) >= 3 else "표현이 늦으면 상대는 확신을 갖기 어렵습니다."
    if "거리" in caution or "차이" in caution:
        third = "표현 속도의 차이는 곧 서운함으로 번집니다."
        fourth = "연락과 말이 늦어지면 상대가 먼저 지칠 수 있습니다."
    elif "오해" in caution:
        third = "말하지 않고 넘긴 감정은 나중에 오해로 돌아옵니다."
        fourth = "괜찮다고 넘긴 일이 반복되면 신뢰가 눈에 띄게 약해집니다."
    else:
        third = _plain_caution_sentence(caution)
        fourth = ""
    return " ".join(part for part in (first, second, expression_sentence, third, fourth) if part)


def _marriage_summary(product_item: dict[str, Any] | None, caution: str) -> str:
    stability = _feature_value(product_item, "marriage_stability")
    practical = _feature_value(product_item, "practical_planning")
    responsibility = _feature_value(product_item, "family_responsibility")
    if _grade_strength(stability) >= 4 and _grade_strength(practical) >= 4:
        first = "결혼운은 생활 기반을 갖춘 뒤 안정되는 사주입니다."
        second = "감정이 깊어진 뒤에도 주거, 재정, 역할 분담을 현실적으로 맞춰갑니다."
    elif _grade_strength(practical) >= 4:
        first = "결혼은 주거와 생활 기준이 정리될 때 현실성이 커집니다."
        second = "상대의 마음보다 생활을 함께 세울 수 있는지가 더 크게 작용합니다."
    elif _grade_strength(stability) >= 3:
        first = "결혼운은 열려 있지만 현실 조건의 영향이 큽니다."
        second = "감정이 깊어도 주거, 돈, 가족 책임을 확인한 뒤 결정하려 합니다."
    else:
        first = "생활 기준이 어긋나면 감정이 깊어도 결혼이 늦어집니다."
        second = "사랑만으로 밀어붙이기보다 현실 조건을 끝까지 확인하는 쪽입니다."
    responsibility_sentence = "가정을 지키려는 책임감도 분명합니다." if _grade_strength(responsibility) >= 3 else "가족 책임이 몰리면 부담도 빠르게 남습니다."
    if "주거" in caution or "가족" in caution:
        third = "생활 기준이 어긋나면 결혼 과정에서 부담이 크게 떠오릅니다."
        fourth = "양가 문제와 주거 조건은 결혼 전에 확실히 정리해야 합니다."
    elif "생활" in caution:
        third = "사랑이 깊어도 생활 방식이 어긋나면 결혼 생활이 늦게 안정됩니다."
        fourth = "생활비와 집안일 기준이 흐리면 감정이 있어도 피로가 쌓입니다."
    else:
        third = _plain_caution_sentence(caution)
        fourth = ""
    return " ".join(part for part in (first, second, responsibility_sentence, third, fourth) if part)


def _plain_caution_sentence(caution: str) -> str:
    text = str(caution or "").strip().rstrip(".")
    if _is_neutral_caution_label(text):
        return ""
    caution_sentences = {
        "지분·명의 안정성": "가까운 사람과 자금을 섞으면 명의와 지분이 상대 쪽으로 기울기 쉽습니다.",
        "수익 배분 안정성": "수익이 보이는 순간 배분 기준이 흔들리기 쉽습니다.",
        "계약·명의 안정성": "계약 조건과 명의가 흐리면 금전 권리가 상대 쪽으로 넘어가기 쉽습니다.",
        "계약·문서 안정성": "계약 조건과 명의가 흐리면 금전 권리가 상대 쪽으로 넘어가기 쉽습니다.",
        "소비 통제력": "수입이 늘어나는 시점에 관계 비용이 먼저 따라붙습니다.",
        "자산 보존력": "수입 규모에 비해 자산으로 굳어지는 몫이 약해질 수 있습니다.",
        "책임·권한 균형": "책임은 늘지만 결정권이 약한 자리는 경력에 흠이 남습니다.",
        "업무 지속력": "일정이 몰리는 자리에서는 실력보다 소모가 먼저 남습니다.",
        "책임 과중": "책임이 과하게 몰리면 성과보다 부담이 먼저 기록됩니다.",
    }
    if text in caution_sentences:
        return caution_sentences[text]
    return f"{text}."


def _is_neutral_caution_label(text: str) -> bool:
    normalized = str(text or "").strip().rstrip(".")
    if not normalized:
        return True
    neutral_labels = {
        "뚜렷한 위험 적음",
        "뚜렷한 약점 적음",
        "큰 주의 적음",
        "큰 주의 기준 적음",
        "주의점 확인",
        "확인 필요",
        "해당 없음",
    }
    if normalized in neutral_labels:
        return True
    return normalized.endswith("적음")


def _clean_caution_label(text: str, fallback: str = "") -> str:
    normalized = str(text or "").strip().rstrip(".")
    if _is_neutral_caution_label(normalized):
        return fallback
    return normalized


def _headline_for_card(card: dict[str, Any], product_item: dict[str, Any] | None = None) -> str:
    domain = _domain_key(card)
    if domain == "money":
        label, value = _dominant_feature_value(
            product_item,
            [
                ("asset_retention", "자산화 능력"),
                ("income_expansion", "수입 창출력"),
                ("money_potential", "재물 형성력"),
                ("business_expansion", "재주 수익화"),
            ],
            fallback_score=_engine_score(product_item, "event_probability_score"),
        )
        return _domain_feature_headline(domain, label, value)
    if domain == "career":
        label, value = _dominant_feature_value_with_bias(
            product_item,
            [
                ("career_achievement", "성취 축적력", 24),
                ("reputation_maintenance", "평가·명예 전환력", 18),
                ("responsibility_capacity", "책임 수행력", 14),
                ("organization_adaptability", "조직 적응력", 10),
                ("academic_expertise", "전문 자산화", 0),
            ],
            fallback_score=_engine_score(product_item, "event_probability_score"),
        )
        return _domain_feature_headline(domain, label, value)
    if domain == "love":
        label, value = _dominant_feature_value_with_bias(
            product_item,
            [
                ("relationship_stability", "관계 지속력", 28),
                ("interpersonal_influence", "인연 형성력", 6),
                ("communication_expression", "애정 표현성", 5),
                ("conflict_recovery", "갈등 회복력", -18),
            ],
            fallback_score=_engine_score(product_item, "event_probability_score"),
        )
        return _domain_feature_headline(domain, label, value)
    if domain == "marriage":
        label, value = _dominant_feature_value_with_bias(
            product_item,
            [
                ("marriage_stability", "혼인 성향", 16),
                ("practical_planning", "생활 안정", 7),
                ("family_responsibility", "가족 책임 경계력", 5),
                ("decision_consistency", "결정 지속성", 4),
            ],
            fallback_score=_engine_score(product_item, "event_probability_score"),
        )
        return _domain_feature_headline(domain, label, value)
    if domain == "personality":
        strength = _strength_from_score(str(card.get("score_label", "")))
        return f"기본 성격이 {strength}."
    strength = _strength_from_score(str(card.get("score_label", "")))
    return f"{card.get('domain_label') or '핵심 운'}이 {strength}."


def _domain_feature_headline(domain: str, label: str, value: str) -> str:
    strength = _grade_strength(value)
    if strength <= 1:
        return f"{label}에서 주의가 필요한 사주입니다."
    if domain == "money":
        if label == "자산화 능력":
            return "수입이 소유권 있는 자산으로 남는 재물운입니다."
        if label == "수입 창출력":
            return "성과를 실제 수입으로 바꾸는 재물운입니다."
        if label == "재물 형성력":
            return "수익 기회와 금전적 접점이 분명한 사주입니다."
        if label == "재주 수익화":
            return "기술과 결과물을 수입으로 바꾸는 사주입니다."
        return "재물이 만들어지는 경로가 분명한 사주입니다."
    if domain == "career":
        if label == "평가·명예 전환력":
            return "공식 평가가 따라오는 직업운입니다."
        if label == "전문 자산화":
            return "전문성이 경력의 단가와 협상력을 만드는 사주입니다."
        if label == "책임 수행력":
            return "책임 있는 역할에서 직함과 영향력이 함께 생깁니다."
        if label == "조직 적응력":
            return "조직 안에서 역할을 맡을수록 성취가 분명하게 남습니다."
        return "맡은 일을 결과와 평가로 남기는 직업운입니다."
    if domain == "love":
        if label == "관계 지속력":
            return "한 번 깊어진 관계가 오래 유지되는 연애운입니다."
        if label == "인연 형성력":
            return "새 인연과 호감 형성이 빠른 연애운입니다."
        if label == "애정 표현성":
            return "좋아하는 마음이 표현으로 바로 드러납니다."
        if label == "갈등 회복력":
            return "관계가 흔들려도 다시 맞추는 회복력이 있습니다."
        return "관계가 깊어질수록 안정성이 드러나는 연애운입니다."
    if domain == "marriage":
        if label == "혼인 성향":
            return "결혼은 감정이 생활로 옮겨진 뒤 안정되는 사주입니다."
        if label == "생활 안정":
            return "주거와 생활 기준이 맞는 관계에서 결혼운이 안정됩니다."
        if label in {"가족 변수", "가족 책임 경계력"}:
            return "양가와 원가족 문제에서 책임의 선을 분명히 세우는 결혼운입니다."
        if label == "결정 지속성":
            return "한 번 정한 결혼의 방향을 오래 유지합니다."
        return "결혼은 생활 기준이 잡힐수록 빠르게 안정되는 사주입니다."
    return _feature_sentence(label, value)


def _summary_for_card(card: dict[str, Any], product_item: dict[str, Any] | None = None) -> str:
    domain = _domain_key(card)
    if domain == "money":
        caution = _caution_for_card(card, product_item)
        return _money_summary(product_item, caution)
    if domain == "career":
        caution = _caution_for_card(card, product_item)
        return _career_summary(product_item, caution)
    if domain == "love":
        caution = _caution_for_card(card, product_item)
        return _love_summary(product_item, caution)
    if domain == "marriage":
        caution = _caution_for_card(card, product_item)
        return _marriage_summary(product_item, caution)
    if domain == "personality":
        return "당신은 자기 기준이 분명한 사람입니다. 마음이 움직여도 곧바로 드러내기보다 상황을 먼저 판단합니다. 책임이 애매한 관계에서는 자연스럽게 거리를 둡니다."
    return "핵심 결론이 분명합니다. 프리미엄에서는 세부 운세가 추가됩니다."


def _badges_for_card(card: dict[str, Any]) -> list[str]:
    domain = _domain_key(card)
    if domain == "money":
        return ["재물 형성력", "재물 규모 확장력", "수입 창출력", "자산화 능력", "공동자금 운영력", "계약·명의 안정성"]
    if domain == "career":
        return ["성취 축적력", "평가·명예 전환력", "조직 적응력", "권한 확보력", "전문 자산화"]
    if domain == "love":
        return ["끌림의 기준", "인연 형성력", "애정 표현성", "관계 지속력", "오해 조정력"]
    if domain == "marriage":
        return ["혼인 성향", "배우자상", "생활 안정", "부부 재정", "결혼 지속력"]
    if domain == "personality":
        return ["기본 성격", "내면 반응", "외부 태도", "반복 태도", "관심 분야"]
    return ["핵심 결론", "주의점", "상세 항목"]


def _axis_value(card: dict[str, Any], *, strong: str = "강함") -> str:
    text = str(card.get("score_label", ""))
    if "매우 강함" in text:
        return "최상위권"
    if "강함" in text:
        return strong
    if "주의" in text:
        return "주의"
    return "보통 이상"


def _risk_axis_value(card: dict[str, Any]) -> str:
    text = str(card.get("score_label", ""))
    if "강한 주의" in text or "주의 강함" in text:
        return "높음"
    if "주의" in text:
        return "보통"
    return "낮음"


def _raw_judgment_axes_for_card(
    card: dict[str, Any],
    product_item: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    domain = _domain_key(card)
    probability = _engine_score(product_item, "event_probability_score")
    opportunity = _engine_score(product_item, "opportunity_score")
    risk = _risk_value(_engine_score(product_item, "risk_score"))
    if domain == "money":
        return [
            {"key": "wealth_formation", "label": "재물 형성력", "value": _feature_value_blended(product_item, "money_potential", probability, cap="중상위권")},
            {"key": "wealth_scale", "label": "재물 규모 확장력", "value": _feature_value_strongest(product_item, ("money_potential", "business_expansion", "asset_retention"), fallback_score=probability, cap="중상위권")},
            {"key": "income_creation", "label": "수입 창출력", "value": _feature_value_strongest(product_item, ("income_expansion", "liquidity_stability", "reward_claim_strength"), fallback_score=opportunity, cap="중상위권")},
            {"key": "skill_income", "label": "재주 수익화", "value": _feature_value_average(product_item, ("business_expansion", "reward_claim_strength"), fallback_score=opportunity, cap="중상위권")},
            {"key": "performance_reward", "label": "성과 보상력", "value": _feature_value_blended(product_item, "reward_claim_strength", opportunity, cap="중상위권")},
            {"key": "asset_retention", "label": "자산화 능력", "value": _feature_value_strongest(product_item, ("asset_retention", "spending_control", "loss_avoidance"), fallback_score=probability)},
            {"key": "cashflow_stability", "label": "자금 운용 안정성", "value": _feature_value_strongest(product_item, ("liquidity_stability", "spending_control", "practical_planning"), fallback_score=probability)},
            {"key": "investment_trading_judgment", "label": "투자·거래 판단력", "value": _feature_value_strongest(product_item, ("investment_trading_sense", "deal_selection", "loss_avoidance"), fallback_score=opportunity)},
            {"key": "shared_asset_stability", "label": "공동자금 운영력", "value": _risk_control_value(_engine_score(product_item, "risk_score"))},
            {"key": "debt_guarantee_control", "label": "부채·보증 관리력", "value": _combined_stability_value(product_item, "loss_avoidance", "shared_asset_boundary")},
            {"key": "family_asset_boundary", "label": "가족재산 경계력", "value": _combined_stability_value(product_item, "shared_asset_boundary", "ownership_clarity")},
            {
                "key": "contract_stability",
                "label": "계약·명의 안정성",
                "value": _contract_name_stability_value(product_item),
            },
            {"key": "receivables_recovery", "label": "채권·미수금 회수력", "value": _feature_value_strongest(product_item, ("ownership_clarity", "deal_selection", "reward_claim_strength"), fallback_score=opportunity)},
            {"key": "business_expansion", "label": "사업 확장성", "value": _feature_value(product_item, "business_expansion")},
            {"key": "financial_defense", "label": "재정 방어력", "value": _combined_stability_value(product_item, "spending_control", "loss_avoidance")},
            {"key": "late_life_wealth_growth", "label": "후반 축재력", "value": _feature_value_strongest(product_item, ("late_life_money_growth", "asset_retention", "practical_planning"), fallback_score=probability)},
            {"key": "money_standard", "label": "금전 기준성", "value": _feature_value_strongest(product_item, ("money_attitude", "deal_selection", "decision_consistency"), fallback_score=probability)},
            {"key": "money_peak_year", "label": "재물 강세 연도", "value": _feature_value_strongest(product_item, ("money_potential", "income_expansion", "asset_retention", "business_expansion"), fallback_score=opportunity)},
            {"key": "money_caution_year", "label": "재물 주의 연도", "value": risk},
        ]
    if domain == "career":
        return [
            {"key": "career_fit", "label": "직업 적성", "value": _feature_value(product_item, "career_achievement", fallback_score=probability)},
            {"key": "career_field", "label": "직업 분야", "value": _feature_value(product_item, "organization_adaptability", fallback_score=probability)},
            {"key": "career_achievement", "label": "성취 축적력", "value": _feature_value(product_item, "career_achievement", fallback_score=probability)},
            {"key": "recognition", "label": "평가·명예 전환력", "value": _feature_value(product_item, "reputation_maintenance", fallback_score=opportunity)},
            {"key": "promotion_title_readiness", "label": "승진·직함 가능성", "value": _feature_value_strongest(product_item, ("promotion_visibility", "honor_recognition", "role_authority_alignment"), fallback_score=opportunity)},
            {"key": "social_ascent", "label": "사회적 도약성", "value": _feature_value_strongest(product_item, ("social_success_potential", "leadership_potential", "honor_recognition"), fallback_score=opportunity)},
            {"key": "authority_balance", "label": "권한 확보력", "value": _risk_control_value(_engine_score(product_item, "risk_score"))},
            {"key": "responsibility_authority_balance", "label": "책임·권한 균형", "value": _feature_value_strongest(product_item, ("role_authority_alignment", "responsibility_capacity", "boundary_management"), fallback_score=probability)},
            {"key": "compensation_negotiation", "label": "보상 협상력", "value": _feature_value_strongest(product_item, ("reward_claim_strength", "deal_selection", "role_authority_alignment"), fallback_score=opportunity)},
            {"key": "expertise", "label": "전문 자산화", "value": _feature_value(product_item, "academic_expertise")},
            {"key": "organization_fit", "label": "조직 적응력", "value": _feature_value(product_item, "organization_adaptability")},
            {"key": "affiliation_transition", "label": "소속 전환력", "value": _feature_value_strongest(product_item, ("change_adaptability", "self_direction", "organization_adaptability"), fallback_score=opportunity)},
            {"key": "independent_work", "label": "독립 가능성", "value": _feature_value(product_item, "business_expansion", fallback_score=opportunity)},
            {"key": "misfit_work", "label": "업무 조건 감별력", "value": risk},
            {"key": "career_transition_year", "label": "직업 전환 연도", "value": _feature_value(product_item, "change_adaptability", fallback_score=opportunity)},
        ]
    if domain == "love":
        return [
            {"key": "attraction_standard", "label": "끌림의 기준", "value": _feature_value(product_item, "interpersonal_influence", fallback_score=opportunity)},
            {"key": "partner_selection", "label": "상대 선택력", "value": _feature_value_strongest(product_item, ("attraction_selectivity", "spouse_match_quality", "decision_consistency"), fallback_score=probability)},
            {"key": "partner_trust_filter", "label": "상대 신뢰 감별력", "value": _feature_value_strongest(product_item, ("boundary_management", "misunderstanding_prevention", "decision_consistency"), fallback_score=probability)},
            {"key": "relationship_opening", "label": "인연 형성력", "value": _feature_value(product_item, "interpersonal_influence", fallback_score=opportunity)},
            {"key": "relationship_progress", "label": "관계 진전력", "value": _feature_value(product_item, "relationship_stability", fallback_score=probability)},
            {"key": "relationship_agency", "label": "관계 주도권", "value": _feature_value_strongest(product_item, ("self_direction", "boundary_management", "decision_consistency"), fallback_score=probability)},
            {"key": "relationship_tempo_control", "label": "관계 속도 조절력", "value": _feature_value_strongest(product_item, ("emotional_alignment", "boundary_management", "relationship_progression"), fallback_score=probability)},
            {"key": "expression", "label": "애정 표현성", "value": _feature_value(product_item, "communication_expression")},
            {"key": "affection_receptivity", "label": "정서 수용력", "value": _feature_value_strongest(product_item, ("affection_receptivity", "emotional_alignment", "conflict_recovery"), fallback_score=probability)},
            {
                "key": "stability",
                "label": "관계 지속력",
                "value": _feature_value_strongest(
                    product_item,
                    ("relationship_stability", "conflict_recovery", "misunderstanding_prevention", "emotional_alignment"),
                    fallback_score=probability,
                ),
            },
            {"key": "contact_distance_stability", "label": "연락·거리 안정성", "value": _feature_value_strongest(product_item, ("boundary_management", "relationship_stability", "communication_expression"), fallback_score=probability)},
            {"key": "misunderstanding", "label": "오해 조정력", "value": _feature_value(product_item, "boundary_management")},
            {"key": "conflict_source", "label": "갈등 관리력", "value": risk},
            {"key": "external_interference_control", "label": "주변 개입 관리력", "value": _feature_value_strongest(product_item, ("boundary_management", "misunderstanding_prevention", "conflict_recovery"), fallback_score=probability)},
            {"key": "reunion_chance", "label": "재회 가능성", "value": _feature_value(product_item, "conflict_recovery")},
            {"key": "marriage_bridge", "label": "결혼 연결력", "value": _feature_value(product_item, "marriage_stability", fallback_score=probability)},
        ]
    if domain == "marriage":
        return [
            {"key": "marriage_tendency", "label": "혼인 성향", "value": _feature_value(product_item, "marriage_stability", fallback_score=probability)},
            {"key": "spouse_type", "label": "배우자상", "value": _feature_value_strongest(product_item, ("spouse_match_quality", "spouse_support_benefit"), fallback_score=probability)},
            {"key": "marriage_timing", "label": "결혼 적기", "value": _feature_value(product_item, "change_adaptability", fallback_score=opportunity)},
            {"key": "marriage_realization", "label": "결혼 현실화력", "value": _feature_value_strongest(product_item, ("marriage_timing_readiness", "practical_planning", "decision_consistency"), fallback_score=probability)},
            {"key": "life_stability", "label": "생활 안정", "value": _feature_value(product_item, "practical_planning")},
            {"key": "household_management", "label": "가정 운영력", "value": _feature_value_strongest(product_item, ("household_stability", "household_finance_alignment", "family_responsibility"), fallback_score=probability)},
            {"key": "housing_life_design", "label": "주거·생활 설계력", "value": _feature_value_strongest(product_item, ("household_stability", "practical_planning", "asset_retention"), fallback_score=probability)},
            {"key": "couple_finance", "label": "부부 재정", "value": _feature_value(product_item, "asset_retention")},
            {"key": "living_cost_standard", "label": "생활비 기준성", "value": _feature_value_strongest(product_item, ("household_finance_alignment", "spending_control", "money_attitude"), fallback_score=probability)},
            {"key": "couple_conflict", "label": "부부 갈등 조정력", "value": risk},
            {"key": "couple_conflict_repair", "label": "부부 갈등 회복성", "value": _feature_value_strongest(product_item, ("conflict_recovery", "marriage_crisis_management", "communication_expression"), fallback_score=probability)},
            {"key": "family_boundary", "label": "가족 책임 경계력", "value": _risk_control_value(_engine_score(product_item, "risk_score"))},
            {"key": "inlaw_family_boundary", "label": "배우자 가족 경계", "value": _feature_value_strongest(product_item, ("inlaw_boundary_strength", "family_responsibility", "boundary_management"), fallback_score=probability)},
            {"key": "child_rearing_responsibility", "label": "자녀·양육 책임", "value": _feature_value_strongest(product_item, ("family_responsibility", "household_stability", "responsibility_capacity"), fallback_score=probability)},
            {"key": "spouse_fortune", "label": "배우자 복", "value": _feature_value(product_item, "relationship_stability", fallback_score=probability)},
            {"key": "marriage_crisis_tolerance", "label": "혼인 위기 대응력", "value": _feature_value_strongest(product_item, ("marriage_crisis_management", "conflict_recovery", "family_responsibility"), fallback_score=probability)},
            {"key": "marriage_continuity", "label": "결혼 지속력", "value": _feature_value(product_item, "decision_consistency")},
        ]
    primary = _axis_value(card)
    return [
        {"key": "core", "label": "핵심 결론", "value": primary},
        {"key": "risk", "label": "주의 필요도", "value": _risk_axis_value(card)},
    ]


def _judgment_axis_score(
    domain: str,
    key: str,
    product_item: dict[str, Any] | None,
    *,
    probability: int | None,
    opportunity: int | None,
    risk_score: int | None,
) -> int | None:
    if domain == "money":
        mapping = {
            "wealth_formation": lambda: _feature_score_blended(product_item, "money_potential", probability, cap=79),
            "wealth_scale": lambda: _feature_score_strongest(product_item, ("money_potential", "business_expansion", "asset_retention"), fallback_score=probability, cap=79),
            "income_creation": lambda: _feature_score_strongest(product_item, ("income_expansion", "liquidity_stability", "reward_claim_strength"), fallback_score=opportunity, cap=79),
            "skill_income": lambda: _feature_score_average(product_item, ("business_expansion", "reward_claim_strength"), fallback_score=opportunity, cap=79),
            "performance_reward": lambda: _feature_score_blended(product_item, "reward_claim_strength", opportunity, cap=79),
            "asset_retention": lambda: _feature_score_strongest(product_item, ("asset_retention", "spending_control", "loss_avoidance"), fallback_score=probability),
            "cashflow_stability": lambda: _feature_score_strongest(product_item, ("liquidity_stability", "spending_control", "practical_planning"), fallback_score=probability),
            "investment_trading_judgment": lambda: _feature_score_strongest(product_item, ("investment_trading_sense", "deal_selection", "loss_avoidance"), fallback_score=opportunity),
            "shared_asset_stability": lambda: _risk_control_score(risk_score),
            "debt_guarantee_control": lambda: _combined_stability_score(product_item, "loss_avoidance", "shared_asset_boundary"),
            "family_asset_boundary": lambda: _combined_stability_score(product_item, "shared_asset_boundary", "ownership_clarity"),
            "contract_stability": lambda: _contract_name_stability_score(product_item),
            "receivables_recovery": lambda: _feature_score_strongest(product_item, ("ownership_clarity", "deal_selection", "reward_claim_strength"), fallback_score=opportunity),
            "business_expansion": lambda: _feature_score(product_item, "business_expansion"),
            "financial_defense": lambda: _combined_stability_score(product_item, "spending_control", "loss_avoidance"),
            "late_life_wealth_growth": lambda: _feature_score_strongest(product_item, ("late_life_money_growth", "asset_retention", "practical_planning"), fallback_score=probability),
            "money_standard": lambda: _feature_score_strongest(product_item, ("money_attitude", "deal_selection", "decision_consistency"), fallback_score=probability),
            "money_peak_year": lambda: _feature_score_strongest(product_item, ("money_potential", "income_expansion", "asset_retention", "business_expansion"), fallback_score=opportunity),
            "money_caution_year": lambda: _risk_control_score(risk_score),
        }
    elif domain == "career":
        mapping = {
            "career_fit": lambda: _feature_score(product_item, "career_achievement", fallback_score=probability),
            "career_field": lambda: _feature_score(product_item, "organization_adaptability", fallback_score=probability),
            "career_achievement": lambda: _feature_score(product_item, "career_achievement", fallback_score=probability),
            "recognition": lambda: _feature_score(product_item, "reputation_maintenance", fallback_score=opportunity),
            "promotion_title_readiness": lambda: _feature_score_strongest(product_item, ("promotion_visibility", "honor_recognition", "role_authority_alignment"), fallback_score=opportunity),
            "social_ascent": lambda: _feature_score_strongest(product_item, ("social_success_potential", "leadership_potential", "honor_recognition"), fallback_score=opportunity),
            "authority_balance": lambda: _risk_control_score(risk_score),
            "responsibility_authority_balance": lambda: _feature_score_strongest(product_item, ("role_authority_alignment", "responsibility_capacity", "boundary_management"), fallback_score=probability),
            "compensation_negotiation": lambda: _feature_score_strongest(product_item, ("reward_claim_strength", "deal_selection", "role_authority_alignment"), fallback_score=opportunity),
            "expertise": lambda: _feature_score(product_item, "academic_expertise"),
            "organization_fit": lambda: _feature_score(product_item, "organization_adaptability"),
            "affiliation_transition": lambda: _feature_score_strongest(product_item, ("change_adaptability", "self_direction", "organization_adaptability"), fallback_score=opportunity),
            "independent_work": lambda: _feature_score(product_item, "business_expansion", fallback_score=opportunity),
            "misfit_work": lambda: _risk_control_score(risk_score),
            "career_transition_year": lambda: _feature_score(product_item, "change_adaptability", fallback_score=opportunity),
        }
    elif domain == "love":
        mapping = {
            "attraction_standard": lambda: _feature_score(product_item, "interpersonal_influence", fallback_score=opportunity),
            "partner_selection": lambda: _feature_score_strongest(product_item, ("attraction_selectivity", "spouse_match_quality", "decision_consistency"), fallback_score=probability),
            "partner_trust_filter": lambda: _feature_score_strongest(product_item, ("boundary_management", "misunderstanding_prevention", "decision_consistency"), fallback_score=probability),
            "relationship_opening": lambda: _feature_score(product_item, "interpersonal_influence", fallback_score=opportunity),
            "relationship_progress": lambda: _feature_score(product_item, "relationship_stability", fallback_score=probability),
            "relationship_agency": lambda: _feature_score_strongest(product_item, ("self_direction", "boundary_management", "decision_consistency"), fallback_score=probability),
            "relationship_tempo_control": lambda: _feature_score_strongest(product_item, ("emotional_alignment", "boundary_management", "relationship_progression"), fallback_score=probability),
            "expression": lambda: _feature_score(product_item, "communication_expression"),
            "affection_receptivity": lambda: _feature_score_strongest(product_item, ("affection_receptivity", "emotional_alignment", "conflict_recovery"), fallback_score=probability),
            "stability": lambda: _feature_score_strongest(product_item, ("relationship_stability", "conflict_recovery", "misunderstanding_prevention", "emotional_alignment"), fallback_score=probability),
            "contact_distance_stability": lambda: _feature_score_strongest(product_item, ("boundary_management", "relationship_stability", "communication_expression"), fallback_score=probability),
            "misunderstanding": lambda: _feature_score(product_item, "boundary_management"),
            "conflict_source": lambda: _risk_control_score(risk_score),
            "external_interference_control": lambda: _feature_score_strongest(product_item, ("boundary_management", "misunderstanding_prevention", "conflict_recovery"), fallback_score=probability),
            "reunion_chance": lambda: _feature_score(product_item, "conflict_recovery"),
            "marriage_bridge": lambda: _feature_score(product_item, "marriage_stability", fallback_score=probability),
        }
    elif domain == "marriage":
        mapping = {
            "marriage_tendency": lambda: _feature_score(product_item, "marriage_stability", fallback_score=probability),
            "spouse_type": lambda: _feature_score_strongest(product_item, ("spouse_match_quality", "spouse_support_benefit"), fallback_score=probability),
            "marriage_timing": lambda: _feature_score(product_item, "change_adaptability", fallback_score=opportunity),
            "marriage_realization": lambda: _feature_score_strongest(product_item, ("marriage_timing_readiness", "practical_planning", "decision_consistency"), fallback_score=probability),
            "life_stability": lambda: _feature_score(product_item, "practical_planning"),
            "household_management": lambda: _feature_score_strongest(product_item, ("household_stability", "household_finance_alignment", "family_responsibility"), fallback_score=probability),
            "housing_life_design": lambda: _feature_score_strongest(product_item, ("household_stability", "practical_planning", "asset_retention"), fallback_score=probability),
            "couple_finance": lambda: _feature_score(product_item, "asset_retention"),
            "living_cost_standard": lambda: _feature_score_strongest(product_item, ("household_finance_alignment", "spending_control", "money_attitude"), fallback_score=probability),
            "couple_conflict": lambda: _risk_control_score(risk_score),
            "couple_conflict_repair": lambda: _feature_score_strongest(product_item, ("conflict_recovery", "marriage_crisis_management", "communication_expression"), fallback_score=probability),
            "family_boundary": lambda: _risk_control_score(risk_score),
            "inlaw_family_boundary": lambda: _feature_score_strongest(product_item, ("inlaw_boundary_strength", "family_responsibility", "boundary_management"), fallback_score=probability),
            "child_rearing_responsibility": lambda: _feature_score_strongest(product_item, ("family_responsibility", "household_stability", "responsibility_capacity"), fallback_score=probability),
            "spouse_fortune": lambda: _feature_score(product_item, "relationship_stability", fallback_score=probability),
            "marriage_crisis_tolerance": lambda: _feature_score_strongest(product_item, ("marriage_crisis_management", "conflict_recovery", "family_responsibility"), fallback_score=probability),
            "marriage_continuity": lambda: _feature_score(product_item, "decision_consistency"),
        }
    else:
        mapping = {}
    scorer = mapping.get(key)
    if not scorer:
        return None
    return _bounded_metric_score(scorer())


def _judgment_axes_for_card(
    card: dict[str, Any],
    product_item: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    axes = [dict(axis) for axis in _raw_judgment_axes_for_card(card, product_item)]
    domain = _domain_key(card)
    probability = _engine_score(product_item, "event_probability_score")
    opportunity = _engine_score(product_item, "opportunity_score")
    risk_score = _engine_score(product_item, "risk_score")
    for axis in axes:
        key = str(axis.get("key") or "")
        score = _judgment_axis_score(
            domain,
            key,
            product_item,
            probability=probability,
            opportunity=opportunity,
            risk_score=risk_score,
        )
        if score is None:
            score = _score_from_axis_value(axis.get("value"))
        if isinstance(score, int):
            axis["score"] = score
    return axes


def _action_for_card(card: dict[str, Any], product_item: dict[str, Any] | None = None) -> str:
    domain = _domain_key(card)
    if domain == "money":
        return _headline_for_card(card, product_item)
    if domain == "career":
        return _headline_for_card(card, product_item)
    if domain == "love":
        return _headline_for_card(card, product_item)
    if domain == "marriage":
        return _headline_for_card(card, product_item)
    return "핵심 결론 우세"


def _caution_for_card(card: dict[str, Any], product_item: dict[str, Any] | None = None) -> str:
    domain = _domain_key(card)
    risk_score = _engine_score(product_item, "risk_score")
    text_caution = _risk_text_caution(domain, product_item)
    if risk_score >= 62 and text_caution:
        return text_caution
    if domain == "money":
        label, severity = _risk_rank(
            product_item,
            [
                ("spending_control", "소비 기준 약화", True),
                ("deal_selection", "계약·문서 안정성", True),
                ("loss_avoidance", "손실 관리", True),
                ("asset_retention", "축재력", True),
            ],
            fallback_risk=risk_score,
        )
        if risk_score >= 62 and risk_score >= severity:
            label, severity = "공동 자금 기준", risk_score
        return _caution_phrase(label, severity)
    if domain == "career":
        label, severity = _risk_rank(
            product_item,
            [
                ("responsibility_capacity", "책임 과중", True),
                ("organization_adaptability", "조직 적응 부담", True),
                ("career_achievement", "성과 정체", True),
            ],
            fallback_risk=risk_score,
        )
        if risk_score >= 62 and risk_score >= severity:
            label, severity = "책임 대비 권한 부족", risk_score
        return _caution_phrase(label, severity)
    if domain == "love":
        label, severity = _risk_rank(
            product_item,
            [
                ("boundary_management", "거리 조절", True),
                ("communication_expression", "표현 오해", True),
                ("conflict_recovery", "갈등 장기화", True),
            ],
            fallback_risk=risk_score,
        )
        if risk_score >= 62 and risk_score >= severity:
            label, severity = "감정 표현 차이", risk_score
        return _caution_phrase(label, severity)
    if domain == "marriage":
        label, severity = _risk_rank(
            product_item,
            [
                ("practical_planning", "생활 기준", True),
                ("family_responsibility", "가족 책임", True),
                ("decision_consistency", "결정 번복", True),
            ],
            fallback_risk=risk_score,
        )
        if risk_score >= 62 and risk_score >= severity:
            label, severity = "가족·주거 변수", risk_score
        return _caution_phrase(label, severity)
    return "판단 지연 주의"


def _engine_score_payload(product_item: dict[str, Any] | None) -> dict[str, Any]:
    if not product_item:
        return {}
    return {
        "opportunity_score": _engine_score(product_item, "opportunity_score"),
        "risk_score": _engine_score(product_item, "risk_score"),
        "change_score": _engine_score(product_item, "change_score"),
        "event_probability_score": _engine_score(product_item, "event_probability_score"),
        "score_labels": dict(product_item.get("score_labels") or {}),
    }


def _domain_strength_score(domain: str, product_item: dict[str, Any] | None) -> int:
    score_keys = {
        "money": ["money_potential", "income_expansion", "asset_retention", "business_expansion"],
        "career": ["career_achievement", "reputation_maintenance", "academic_expertise", "organization_adaptability"],
        "love": ["relationship_stability", "interpersonal_influence", "communication_expression", "conflict_recovery"],
        "marriage": ["marriage_stability", "practical_planning", "family_responsibility", "decision_consistency"],
    }.get(domain, [])
    scores = [
        score
        for score in (_feature_score(product_item, key) for key in score_keys)
        if isinstance(score, int)
    ]
    if not scores:
        return _engine_score(product_item, "event_probability_score")
    scores.sort(reverse=True)
    top_scores = scores[:3]
    return round(sum(top_scores) / len(top_scores))


def _score_label_for_card(
    card: dict[str, Any],
    product_item: dict[str, Any] | None,
    axes: list[dict[str, str]],
) -> str:
    domain_label = str(card.get("domain_label") or card.get("title") or "핵심").removesuffix("운")
    headline = _headline_for_card(card, product_item).rstrip(".")
    seen_labels: set[str] = set()
    axis_parts: list[str] = []
    for axis in axes:
        label = str(axis.get("label") or "").strip()
        value = str(axis.get("value") or "").strip()
        if not label or not value or label in seen_labels:
            continue
        if headline == f"{label} {value}" or headline.startswith(f"{label} "):
            seen_labels.add(label)
            continue
        seen_labels.add(label)
        axis_parts.append(f"{label} {value}")
    joined_axes = ". ".join(axis_parts[:2])
    if joined_axes:
        return f"{domain_label} 핵심: {headline}. {joined_axes}."
    return f"{domain_label} 핵심: {headline}."


def _normalize_mobile_card(
    card: dict[str, Any],
    product_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(card)
    domain = _domain_key(card)
    judgment_axes = _judgment_axes_for_card(card, product_item)
    normalized["title"] = str(card.get("domain_label") or card.get("title") or "핵심 결론")
    normalized["headline"] = _headline_for_card(card, product_item)
    normalized["summary"] = _summary_for_card(card, product_item)
    normalized["score_label"] = _score_label_for_card(card, product_item, judgment_axes)
    normalized["timing_label"] = "종합 분석"
    normalized["action_label"] = _action_for_card(card, product_item)
    normalized["caution_label"] = _caution_for_card(card, product_item)
    normalized["badges"] = _badges_for_card(card)
    normalized["judgment_axes"] = judgment_axes
    normalized["engine_scores"] = _engine_score_payload(product_item)
    normalized["strength_score"] = _domain_strength_score(domain, product_item)
    return normalized


FREE_PROFILE_AXIS_DEFINITIONS: dict[str, str] = {
    "타고난 재물의 그릇": "재물을 감당하고 키울 수 있는 선천적 기반입니다.",
    "수입 발생력": "직업 활동, 거래, 성과가 실제 금전 수입으로 이어지는 자리입니다.",
    "자산 확정력": "수입이 소비로 흩어지지 않고 현금과 소유권으로 남는 자리입니다.",
    "공동 자금 안정성": "가족, 지인, 동업자와 얽힌 자금에서 자기 몫과 명의를 지키는 기준입니다.",
    "계약·명의 안정성": "계약, 명의, 지분, 정산에서 금전 권리를 안정시키는 기준입니다.",
    "확장 가능성": "고정 수입을 넘어 사업, 투자, 외부 거래로 재물 단위가 커지는 자리입니다.",
    "재물이 들어오는 길": "일, 거래, 성과가 실제 수입으로 이어지는 자리입니다.",
    "재산으로 굳어지는 힘": "들어온 돈이 소비로 흩어지지 않고 자산으로 남는 구조입니다.",
    "재물에 얽히는 사람 문제": "가족, 지인, 동업자와 얽힌 돈에서 자기 몫과 명의를 지키는 기준입니다.",
    "돈을 지켜내는 기준": "계약, 명의, 정산, 보증에서 권리와 수령액을 지키는 기준입니다.",
    "재물 발생력": "금전 기회가 실제 수익으로 확정되는 재물 기반입니다.",
    "재물 형성력": "돈이 붙기 시작하는 자리와 금전 기회가 현실 수입으로 커지는 기반입니다.",
    "재물 규모 확장력": "일상의 수입을 넘어 거래 단위, 보유 자산, 사업 단위가 커집니다.",
    "수입 창출력": "일, 거래, 성과가 월급·매출·계약금처럼 실제 현금으로 회수됩니다.",
    "축재력": "들어온 수입을 소유권 있는 자산으로 남깁니다.",
    "자산화 능력": "들어온 돈을 현금, 소유권, 지분, 장기 자산으로 남깁니다.",
    "자금 운용 안정성": "수입 이후 생활비, 고정비, 예비 자금까지 안정적으로 배분합니다.",
    "투자·거래 판단력": "수익 가능성, 회수 조건, 상대 신뢰도, 명의 문제를 가려냅니다.",
    "지출 통제력": "반복 지출이 재산 형성을 방해하지 않게 관리합니다.",
    "공동 자금 운영력": "가까운 사람과 얽힌 돈에서 자기 몫과 명의를 지키는 힘이 분명해야 합니다.",
    "공동자금 운영력": "가까운 사람과 얽힌 돈에서 자기 몫과 명의를 지키는 힘이 분명해야 합니다.",
    "부채·보증 관리력": "대여, 보증, 채무 관계에서 책임 범위와 회수 가능성을 분명히 합니다.",
    "가족재산 경계력": "가족 재산과 자기 자산이 섞일 때 몫과 책임선을 지킵니다.",
    "계약·문서 안정성": "문서에서 권리와 수령액을 지켜냅니다.",
    "계약·명의 안정성": "계약서, 명의, 지분, 보증에서 자기 권리와 수령액을 보존합니다.",
    "채권·미수금 회수력": "받아야 할 돈과 지연된 보상을 자기 권리로 회수합니다.",
    "재주 수익화": "기술, 말, 기획, 콘텐츠를 단가와 보수로 바꿉니다.",
    "성과 보상력": "본인이 만든 성과를 보수, 직책, 공식 인정으로 회수합니다.",
    "사업 확장성": "고정 수입 밖의 거래와 사업 기회를 재물 규모로 키웁니다.",
    "재정 방어력": "손실, 보증, 명의 문제에서 자금을 지켜냅니다.",
    "후반 축재력": "나이가 들수록 수입 방식이 안정되고 자산 단위가 커집니다.",
    "금전 기준성": "돈 앞에서 체면보다 소유권, 보상 원칙, 지출 한계를 세웁니다.",
    "재물 주의 연도": "금전 판단과 계약에서 각별한 주의가 필요한 연도입니다.",
    "직업 성취력": "맡은 일이 결과와 이력으로 남아 직업적 위치를 높이는 자리입니다.",
    "직업적 성취의 그릇": "맡은 일을 성취와 이력으로 남기는 직업적 기반입니다.",
    "평가가 따라오는 자리": "성과가 조직과 시장에서 인정으로 돌아오는 자리입니다.",
    "조직 안에서 자리 잡는 힘": "조직의 기준 안에서 역할과 영향력을 확보하는 방식입니다.",
    "권한과 책임의 균형": "맡은 책임에 걸맞은 결정권과 보상을 확보하는 기준입니다.",
    "전문성으로 남는 힘": "시간이 지날수록 쉽게 대체되지 않는 직업 기반입니다.",
    "독립 가능성": "조직 밖에서도 자기 이름과 전문성으로 일할 수 있는 기반입니다.",
    "업무 평가력": "실력과 성과가 공적으로 인정되는 기준입니다.",
    "조직 적합도": "조직의 기준 안에서 성과를 안정적으로 확보하는 자리입니다.",
    "책임 수행력": "무거운 업무와 장기 과제를 끝까지 감당해 결과로 남기는 자리입니다.",
    "전문성": "쉽게 대체되지 않는 직업 기반이 됩니다.",
    "권한·책임 균형도": "맡은 책임에 걸맞은 결정권과 보상이 함께 붙는 자리입니다.",
    "직업 적성": "성과가 가장 잘 남는 일의 방식입니다.",
    "직업 분야": "맞는 산업과 역할의 성격입니다.",
    "성취 축적력": "맡은 일이 실적과 경력으로 남습니다.",
    "평가·명예 전환력": "성과가 평가, 직함, 평판으로 이어집니다.",
    "승진·직함 가능성": "실적이 내부 평가, 승진 후보, 공식 책임자로 올라갑니다.",
    "사회적 도약성": "직업 성취가 지위와 영향력 확대로 이어집니다.",
    "권한 확보력": "맡은 책임에 걸맞은 결정권과 보상을 확보합니다.",
    "책임·권한 균형": "책임, 결정권, 보고 체계, 보상 기준이 맞물립니다.",
    "보상 협상력": "성과를 연봉, 수수료, 지분, 성과급으로 확정합니다.",
    "전문 자산화": "자격과 경험이 직업 경쟁력으로 쌓입니다.",
    "조직 적응력": "조직 안에서 역할을 확보하고 오래 자리 잡습니다.",
    "소속 전환력": "부서, 회사, 직무가 바뀔 때 손실보다 새 기회를 만듭니다.",
    "업무 조건 감별력": "책임과 보상이 맞지 않는 자리를 미리 가려냅니다.",
    "직업 전환 연도": "이직, 승진, 독립, 역할 변화가 강해지는 연도입니다.",
    "인연 형성력": "새로운 만남과 호감이 관계의 계기로 발전하는 자리입니다.",
    "애정 표현성": "좋아하는 마음이 상대에게 전달되는 방식과 속도입니다.",
    "관계 지속력": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "결혼 현실성": "연애가 실제 약속과 생활 논의로 넘어가는 현실성입니다.",
    "인연이 들어오는 길": "새로운 만남과 호감이 관계의 계기로 이어지는 자리입니다.",
    "애정이 표현되는 방식": "좋아하는 마음이 말과 행동으로 드러나는 방식입니다.",
    "관계가 오래 가는 힘": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "관계 경계선": "가까워진 뒤에도 서로의 거리와 책임 범위를 지키는 기준입니다.",
    "결혼 연결성": "연애가 실제 약속과 생활 논의로 넘어가는 현실성입니다.",
    "상대 선택력": "호감만으로 움직이지 않고 오래 맞을 상대를 가려내는 기준입니다.",
    "결혼으로 이어지는 현실성": "연애가 실제 결혼 논의로 옮겨갈 수 있는 현실성입니다.",
    "함께 살아가는 기준": "생활비, 주거, 역할 분담을 함께 맞춰가는 기준입니다.",
    "애정 표현력": "좋아하는 마음을 상대가 알아들을 수 있게 드러내는 방식입니다.",
    "관계 안정성": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "끌림의 기준": "어떤 성향과 조건의 상대에게 마음이 움직이는지를 가르는 기준입니다.",
    "상대 선택력": "순간적인 끌림과 장기적인 안정성을 구분해 상대를 고릅니다.",
    "상대 신뢰 감별력": "호감이 생긴 뒤에도 상대의 말, 책임감, 생활 태도를 가려냅니다.",
    "관계 진전력": "호감이 실제 연애와 공식 관계로 넘어갑니다.",
    "관계 주도권": "상대의 속도에 끌려가지 않고 관계의 방향과 거리를 정합니다.",
    "관계 속도 조절력": "호감 이후 관계의 속도를 무리 없이 맞춥니다.",
    "정서 수용력": "상대의 불안, 서운함, 확인 욕구를 관계 안에서 받아냅니다.",
    "연락·거리 안정성": "연락 빈도, 개인 시간, 관계의 거리를 무리 없이 맞춥니다.",
    "오해 조정력": "상대가 서운함을 느끼기 쉬운 지점을 줄입니다.",
    "갈등 관리력": "관계를 흔드는 감정과 현실 문제를 관리합니다.",
    "주변 개입 관리력": "친구, 가족, 과거 인연의 말이 관계 안으로 들어올 때 흔들림을 줄입니다.",
    "재회 가능성": "지나간 관계가 다시 이어질 수 있는 접점입니다.",
    "결혼 연결력": "연애가 약속과 생활 논의로 넘어가는 현실성입니다.",
    "관계 조절력": "가까워지는 속도를 무리 없이 맞추는 자리입니다.",
    "갈등 회복력": "오해나 다툼이 생긴 뒤 관계를 다시 세우는 자리입니다.",
    "감정 조율력": "서로의 감정 차이를 줄이고 관계의 균형을 되찾는 자리입니다.",
    "결혼 안정성": "연애 감정이 실제 생활에서도 유지되는 안정성입니다.",
    "혼인 성향": "결혼을 감정의 결론으로 보는지, 생활과 책임의 결합으로 보는지에 대한 기준입니다.",
    "배우자상": "오래 맞는 상대의 성격, 생활 태도, 책임 감각을 정리한 기준입니다.",
    "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활을 버티게 하는 현실 기반입니다.",
    "부부 재정": "명의, 생활비, 공동 자산을 부부 사이에서 정리하는 기준입니다.",
    "결혼 현실화력": "결혼 의사가 주거, 절차, 가족 협의로 실제 굳어집니다.",
    "가정 운영력": "집안의 일정, 지출, 역할, 가족 책임을 안정적으로 운영합니다.",
    "주거·생활 설계력": "집, 생활비, 시간 사용, 역할 분담을 현실 조건으로 정리합니다.",
    "생활비 기준성": "반복 지출과 저축 기준을 감정 문제가 되기 전에 세웁니다.",
    "부부 갈등 조정력": "역할 불균형, 가족 개입, 돈 문제를 조정합니다.",
    "부부 갈등 회복성": "감정이 상한 뒤 생활 기준과 책임 범위를 다시 맞춥니다.",
    "가족 책임 경계력": "양가와 원가족 문제에서 맡을 책임과 끊어낼 책임을 구분합니다.",
    "배우자 가족 경계": "배우자 가족과 원가족 사이에서 책임, 돈, 간섭의 선을 세웁니다.",
    "자녀·양육 책임": "자녀, 양육, 돌봄 책임이 부부 생활 안에서 안정적으로 배분됩니다.",
    "가족 변수": "양가와 원가족 문제가 결혼 생활에 들어오는 지점입니다.",
    "배우자 복": "배우자로 인해 얻는 안정과 함께 따라오는 부담의 크기입니다.",
    "혼인 위기 대응력": "돈, 가족, 주거, 역할 문제가 겹칠 때 결혼 생활을 지킵니다.",
    "결혼 지속력": "결혼을 오래 유지하고 중간의 위기를 넘깁니다.",
    "결혼이 안정되는 힘": "결혼을 감정의 결론이 아니라 생활의 약속으로 지킵니다.",
    "생활 기반이 잡히는 방식": "주거, 생활비, 역할 기준이 결혼 생활의 기반으로 자리 잡는 방식입니다.",
    "가족 책임을 감당하는 힘": "양가와 원가족 문제에서 맡을 책임과 끊어낼 책임을 구분합니다.",
    "약속을 오래 지키는 힘": "결혼을 오래 유지하고 중간의 위기를 넘깁니다.",
    "배우자 관계 안정성": "배우자와의 감정, 역할, 책임이 오래 안정되는 자리입니다.",
    "가족 변수 관리력": "가족의 말, 돈, 책임이 부부 사이로 들어올 때 기준을 세웁니다.",
    "생활 안정성": "생활 기준이 결혼을 지탱하는 현실 기반입니다.",
    "가족 책임감": "배우자와 가족에게 요구되는 현실 책임을 감당하는 자리입니다.",
    "결정 지속성": "결혼과 가정의 방향을 정한 뒤 오래 유지하는 성향입니다.",
    "생활 기반 안정성": "생활 기준 앞에서도 결혼 생활이 흔들리지 않는 안정성입니다.",
    "대운 구간": "10년 단위로 중심 과제가 옮겨가는 생애 구간입니다.",
    "세운 사건": "각 연도에 두드러지는 사건 주제입니다.",
    "상승 연도": "성과와 기회가 뚜렷하게 드러나는 연도입니다.",
    "재물 강세 연도": "수입, 계약, 자산, 사업 기회가 강해지는 연도입니다.",
    "연애 강세 연도": "새 인연, 호감, 관계 진전이 강해지는 연도입니다.",
    "인생 전환 연도": "삶의 방향이 크게 바뀌는 선택이 올라오는 연도입니다.",
    "주의 연도": "금전, 직업, 관계에서 각별한 주의가 필요한 연도입니다.",
    "회복 연도": "손실과 정체를 정리하고 다시 기반을 잡는 연도입니다.",
    "말년 안정 연도": "후반부의 자산, 가족, 생활 기반이 안정되는 연도입니다.",
}


def _axis_rank_score(axis: dict[str, Any]) -> int:
    value = str(axis.get("value") or "")
    if "최상위" in value:
        return 96
    if "상위" in value:
        return 86
    if "중상위" in value:
        return 76
    if "안정" in value:
        return 72
    if "평균" in value:
        return 62
    if "보통" in value:
        return 56
    if "주의" in value:
        return 42
    if "약세" in value or "낮음" in value:
        return 34
    return 50


def _free_profile_axis(axis: dict[str, Any]) -> dict[str, Any]:
    label = str(axis.get("label") or "").strip()
    return {
        "key": str(axis.get("key") or ""),
        "label": label,
        "value": str(axis.get("value") or "확인").strip(),
        "definition": FREE_PROFILE_AXIS_DEFINITIONS.get(label, "이 영역에서 실제 결과를 가르는 세부 기준입니다."),
        "score": _axis_rank_score(axis),
    }


def _free_profile_strong_axis(axes: list[dict[str, Any]]) -> dict[str, Any]:
    if not axes:
        return _free_profile_axis({"label": "핵심 결론", "value": "확인"})
    return max((_free_profile_axis(axis) for axis in axes), key=lambda item: (int(item["score"]), str(item["label"])))


def _free_profile_watch_axis(axes: list[dict[str, Any]]) -> dict[str, Any]:
    if not axes:
        return _free_profile_axis({"label": "주의 기준", "value": "확인"})
    items = [_free_profile_axis(axis) for axis in axes]
    weakest_score = min((int(item["score"]) for item in items), default=50)
    shared_asset = next((item for item in items if item.get("label") == "공동자금 운영력"), None)
    if shared_asset and int(shared_asset["score"]) <= weakest_score + 8:
        return shared_asset
    return min(items, key=lambda item: (int(item["score"]), str(item["label"])))


def _has_korean_final_consonant(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    code = ord(text[-1])
    if not (0xAC00 <= code <= 0xD7A3):
        return False
    return (code - 0xAC00) % 28 != 0


def _with_particle(value: str, consonant_particle: str, vowel_particle: str) -> str:
    text = str(value or "").strip()
    particle = consonant_particle if _has_korean_final_consonant(text) else vowel_particle
    return f"{text}{particle}"


def _free_profile_section_summary(
    card: dict[str, Any],
    strong_axis: dict[str, Any],
    watch_axis: dict[str, Any],
) -> str:
    domain = _domain_key(card)
    headline = str(card.get("headline") or "").strip().rstrip(".")
    strong_label = str(strong_axis.get("label") or "강한 기준")
    watch_label = str(watch_axis.get("label") or "주의 기준")
    strong_subject = _with_particle(strong_label, "이", "가")
    watch_subject = _with_particle(watch_label, "은", "는")
    watch_score = int(watch_axis.get("score") or 0)
    if domain == "money":
        if watch_score < 50:
            return f"{headline}. {strong_subject} 재물운의 중심입니다. {watch_subject} 불리합니다. 가까운 사람과 돈을 함께 다루면 명의와 지분이 상대 쪽으로 기울기 쉽습니다."
        return f"{headline}. {strong_subject} 재물운의 중심입니다. {watch_subject} 수입을 자산으로 굳히는 힘을 더합니다."
    if domain == "career":
        if watch_score < 50:
            return f"{headline}. {strong_subject} 직업운의 중심입니다. {watch_subject} 불리합니다. 책임은 늘어나는데 결정권이 늦게 따라오는 자리를 조심해야 합니다."
        return f"{headline}. {strong_subject} 직업운의 중심입니다. {watch_subject} 직함과 평가를 안정적으로 받쳐줍니다."
    if domain == "love":
        if watch_score < 50:
            return f"{headline}. {strong_subject} 강한 편입니다. {watch_subject} 불리합니다. 마음이 있어도 표현이 늦으면 상대가 확신을 얻기 어렵습니다."
        return f"{headline}. {strong_subject} 강한 편입니다. {watch_subject} 깊어진 관계를 오래 유지하게 합니다."
    if domain == "marriage":
        if watch_score < 50:
            return f"{headline}. {strong_subject} 강한 편입니다. {watch_subject} 불리합니다. 결혼 뒤 주거와 가족 책임이 부담으로 커질 수 있습니다."
        return f"{headline}. {strong_subject} 강한 편입니다. {watch_subject} 결혼 생활을 안정적으로 지탱합니다."
    return str(card.get("summary") or headline or "핵심 결론을 확인합니다.")


def _free_profile_sections(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for card in cards:
        axes = [axis for axis in card.get("judgment_axes", []) if isinstance(axis, dict)]
        strong_axis = _free_profile_strong_axis(axes)
        watch_axis = _free_profile_watch_axis(axes)
        sections.append(
            {
                "domain": str(card.get("domain") or _domain_key(card)),
                "title": str(card.get("title") or card.get("domain_label") or "핵심 운세"),
                "headline": str(card.get("headline") or ""),
                "summary": _free_profile_section_summary(card, strong_axis, watch_axis),
                "grade": _score_value(int(card.get("strength_score") or 0)),
                "strong_axis": strong_axis,
                "watch_axis": watch_axis,
                "premium_hint": _free_profile_premium_hint(card),
            }
        )
    return sections


def _free_profile_premium_hint(card: dict[str, Any]) -> str:
    domain = _domain_key(card)
    if domain == "money":
        return "프리미엄에서는 수입이 자산으로 남는 방식과 계약·공동자금의 손익 지점까지 좁혀 보여드립니다."
    if domain == "career":
        return "프리미엄에서는 성취가 경력, 평가, 권한, 전문성으로 남는 과정을 더 구체적으로 보여드립니다."
    if domain == "love":
        return "프리미엄에서는 인연의 시작, 애정 표현, 관계 지속과 흔들리는 지점을 더 좁혀 보여드립니다."
    if domain == "marriage":
        return "프리미엄에서는 배우자상, 생활 안정, 부부 재정, 가족 책임까지 더 구체적으로 보여드립니다."
    return "프리미엄에서는 세부 기준이 더 선명하게 드러납니다."


def _free_profile_preview(cards: list[dict[str, Any]]) -> dict[str, Any]:
    sections = _free_profile_sections(cards)
    strongest = max(sections, key=lambda item: int(item.get("strong_axis", {}).get("score") or 0), default={})
    watch = min(sections, key=lambda item: int(item.get("watch_axis", {}).get("score") or 99), default={})
    return {
        "title": "무료 종합운",
        "headline": "재물, 직업, 연애, 결혼에서 먼저 볼 결론입니다.",
        "lead": "각 영역의 강한 지점과 반드시 조심할 지점을 먼저 정리했습니다.",
        "strongest": strongest,
        "watch": watch,
        "sections": sections,
    }


def _premium_checkpoints(section: dict[str, Any], product_item: dict[str, Any] | None = None) -> list[str]:
    domain = _domain_key(section)
    if domain == "money":
        return [
            f"재물 형성력: {_feature_value(product_item, 'money_potential')}",
            f"재물 규모 확장력: {_feature_value_strongest(product_item, ('money_potential', 'business_expansion', 'asset_retention'))}",
            f"수입 창출력: {_feature_value(product_item, 'income_expansion')}",
            f"자산화 능력: {_feature_value(product_item, 'asset_retention')}",
            f"지출 통제력: {_feature_value(product_item, 'spending_control')}",
            f"재주 수익화: {_feature_value(product_item, 'business_expansion')}",
            f"성과 보상력: {_feature_value(product_item, 'income_expansion')}",
            f"계약·명의 안정성: {_combined_stability_value(product_item, 'deal_selection', 'loss_avoidance')}",
            f"주의점: {_caution_for_card(section, product_item)}",
        ]
    if domain == "career":
        opportunity = _engine_score(product_item, "opportunity_score")
        probability = _engine_score(product_item, "event_probability_score")
        return [
            f"성취 축적력: {_feature_value(product_item, 'career_achievement')}",
            f"평가·명예 전환력: {_cap_top_rank(_feature_value(product_item, 'reputation_maintenance'))}",
            f"조직 적응력: {_feature_value(product_item, 'organization_adaptability')}",
            f"책임 수행력: {_feature_value(product_item, 'responsibility_capacity')}",
            f"전문 자산화: {_feature_value(product_item, 'academic_expertise')}",
            f"관리·운영 적성: {_feature_value(product_item, 'organization_adaptability', fallback_score=probability)}",
            f"대외 활동성: {_feature_value(product_item, 'career_achievement', fallback_score=opportunity)}",
            f"주의점: {_caution_for_card(section, product_item)}",
        ]
    if domain == "love":
        return [
            f"인연 형성력: {_feature_value(product_item, 'interpersonal_influence')}",
            f"애정 표현성: {_feature_value(product_item, 'communication_expression')}",
            f"관계 지속력: {_feature_value_strongest(product_item, ('relationship_stability', 'conflict_recovery', 'misunderstanding_prevention', 'emotional_alignment'))}",
            f"관계 조절력: {_feature_value(product_item, 'boundary_management')}",
            f"갈등 회복력: {_feature_value(product_item, 'conflict_recovery')}",
            f"주의점: {_caution_for_card(section, product_item)}",
        ]
    if domain == "marriage":
        return [
            f"혼인 성향: {_feature_value(product_item, 'marriage_stability')}",
            f"생활 안정: {_feature_value(product_item, 'practical_planning')}",
            f"가족 책임 경계력: {_feature_value(product_item, 'family_responsibility')}",
            f"결혼 지속력: {_feature_value(product_item, 'decision_consistency')}",
            f"갈등 회복력: {_feature_value(product_item, 'conflict_recovery')}",
            f"주의점: {_caution_for_card(section, product_item)}",
        ]
    return [
        "핵심 운세: 이 영역에서 강하게 작용하는 항목과 주의할 항목을 나눠 봅니다.",
        "세부 운세: 성향, 사건, 현실 조건을 구분해 판정합니다.",
    ]


def _detail_block(title: str, body: str, bullets: list[str] | None = None, *, tone: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "body": body,
        "bullets": bullets or [],
        "tone": tone,
    }


def _web_topic_evidence_text(text: Any) -> str:
    return str(text or "").replace("분석 기준:", "근거 항목:")


PREMIUM_DISPLAY_TITLE_ALIASES: dict[str, str] = {
    "재물 발생력": "재물 형성력",
    "타고난 재물의 그릇": "재물 형성력",
    "재물이 들어오는 길": "수입 창출력",
    "수익 전환력": "수입 창출력",
    "수입 발생력": "수입 창출력",
    "재산으로 굳어지는 힘": "자산화 능력",
    "축재력": "자산화 능력",
    "자산 축적력": "자산화 능력",
    "자산 확정력": "자산화 능력",
    "재물에 얽히는 사람 문제": "공동자금 운영력",
    "공동 자금 운영력": "공동자금 운영력",
    "공동 자금 관리력": "공동자금 운영력",
    "공동 자금 안정성": "공동자금 운영력",
    "돈을 지켜내는 기준": "계약·명의 안정성",
    "계약·문서 안정성": "계약·명의 안정성",
    "계약 안정성": "계약·명의 안정성",
    "직업적 성취의 그릇": "성취 축적력",
    "직업 성취력": "성취 축적력",
    "성과 구현력": "성취 축적력",
    "평가가 따라오는 자리": "평가·명예 전환력",
    "업무 평가력": "평가·명예 전환력",
    "평가 확보력": "평가·명예 전환력",
    "조직 안에서 자리 잡는 힘": "조직 적응력",
    "조직 적합도": "조직 적응력",
    "권한과 책임의 균형": "권한 확보력",
    "권한·책임 균형도": "권한 확보력",
    "권한 책임 균형도": "권한 확보력",
    "전문성으로 남는 힘": "전문 자산화",
    "전문성": "전문 자산화",
    "전문성 축적도": "전문 자산화",
    "인연이 들어오는 길": "인연 형성력",
    "호감 형성력": "인연 형성력",
    "애정이 표현되는 방식": "애정 표현성",
    "애정 표현력": "애정 표현성",
    "관계가 오래 가는 힘": "관계 지속력",
    "관계 안정성": "관계 지속력",
    "관계 지속력": "관계 지속력",
    "결혼으로 이어지는 현실성": "결혼 연결력",
    "결혼 현실화": "결혼 연결력",
    "결혼 현실성": "결혼 연결력",
    "함께 살아가는 기준": "생활 안정",
    "생활 기준": "생활 안정",
    "생활 조율력": "생활 안정",
    "생활 안정성": "생활 안정",
    "결혼이 안정되는 힘": "혼인 성향",
    "결혼 안정성": "혼인 성향",
    "생활 기반이 잡히는 방식": "생활 안정",
    "생활 기반 안정성": "생활 안정",
    "가족 책임감": "가족 책임 경계력",
    "가족 책임 수용력": "가족 책임 경계력",
    "결정 지속성": "결혼 지속력",
    "결정 지속력": "결혼 지속력",
    "초년·청년기": "초년에 형성되는 바탕",
    "초년 형성도": "초년에 형성되는 바탕",
    "중년기": "중년에 굳어지는 성취",
    "중년 성취도": "중년에 굳어지는 성취",
    "말년기": "말년에 남는 안정",
    "말년 안정도": "말년에 남는 안정",
    "대운 전환": "운이 바뀌는 전환기",
    "전환기 대응력": "운이 바뀌는 전환기",
    "사회적 인정": "공적 인정 기반",
    "사회적 인정도": "공적 인정 기반",
    "사회적 인정이 붙는 자리": "공적 인정 기반",
    "평가가 직함으로 이어지는 자리": "직책 상승력",
    "권한이 붙을수록 커지는 평판": "권한 기반 평판",
    "평판 유지력": "평판이 오래 남는 힘",
    "평판 지속력": "평판이 오래 남는 힘",
    "공식 책임": "공식 책임을 맡는 힘",
    "공식 역할 수용력": "공식 책임을 맡는 힘",
    "명예 관리": "명예를 지켜내는 기준",
    "명예 관리력": "명예를 지켜내는 기준",
    "사람을 얻는 방식": "사람을 얻는 힘",
    "인맥 형성력": "사람을 얻는 힘",
    "도움이 되는 사람": "도움으로 이어지는 인연",
    "조력자 인연": "도움으로 이어지는 인연",
    "부탁과 책임": "부탁과 책임의 경계",
    "책임 경계력": "부탁과 책임의 경계",
}


def _premium_display_title(value: Any) -> str:
    text = str(value or "").strip()
    return PREMIUM_DISPLAY_TITLE_ALIASES.get(text, text)


def _replace_premium_display_terms(text: Any) -> str:
    value = str(text or "")
    if not value:
        return value
    for source, target in sorted(PREMIUM_DISPLAY_TITLE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if source in value and target not in value:
            value = value.replace(source, target)
    return value


def _web_topic_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        updated = dict(item)
        if "title" in updated:
            updated["title"] = _premium_display_title(updated.get("title"))
        for key in ("body", "definition"):
            if key in updated:
                updated[key] = _replace_premium_display_terms(updated.get(key))
        if "evidence" in updated:
            updated["evidence"] = _replace_premium_display_terms(
                _web_topic_evidence_text(updated.get("evidence"))
            )
        normalized.append(updated)
    return normalized


def _premium_topic_items(
    domain: str,
    limit: int = 5,
    product_item: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if domain == "personality" and limit < 6:
        limit = 6
    feature_axes = list((product_item or {}).get("feature_axes") or [])
    items = premium_topic_items(domain, limit=limit, feature_axes=feature_axes)
    if domain == "money":
        return _web_topic_items(_align_money_topic_items(items, product_item))
    if domain == "career":
        return _web_topic_items(_align_career_topic_items(items, product_item))
    return _web_topic_items(items)


def _positive_control_score_from_risk(risk_score: int) -> int:
    if risk_score >= 75:
        return 40
    if risk_score >= 62:
        return 45
    if risk_score >= 48:
        return 58
    return 78


def _topic_tone_from_score(score: int) -> str:
    if score >= 80:
        return "strong"
    if score >= 68:
        return "good"
    if score < 50:
        return "watch"
    return "neutral"


def _align_money_topic_items(
    items: list[dict[str, Any]],
    product_item: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    risk_score = _engine_score(product_item, "risk_score")
    shared_score = _positive_control_score_from_risk(risk_score)
    shared_body = (
        "가까운 사람과 자금을 섞으면 명의와 지분이 상대 쪽으로 기울기 쉽습니다."
        if shared_score < 50
        else "명의가 분명하면 공동 자금도 안정적으로 굴러갑니다."
        if shared_score < 68
        else "가족 자금에서도 자기 몫을 안정적으로 지켜냅니다."
    )
    aligned: list[dict[str, Any]] = []
    for item in items:
        if str(item.get("title") or "") in {"공동자금 운영력", "공동 자금 운영력", "재물에 얽히는 사람 문제"}:
            updated = dict(item)
            updated["title"] = "공동자금 운영력"
            updated["score"] = shared_score
            updated["value"] = _score_value(shared_score)
            updated["tone"] = _topic_tone_from_score(shared_score)
            updated["body"] = shared_body
            updated["definition"] = "가까운 사람과 함께 다루는 돈에서 자기 몫과 명의를 지키는 기준입니다."
            updated["evidence"] = f"근거 항목: 공동자금 운영력, 재정 방어력 · 결과 등급: {_score_value(shared_score)}"
            aligned.append(updated)
        else:
            aligned.append(item)
    return aligned


def _align_career_topic_items(
    items: list[dict[str, Any]],
    product_item: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    risk_score = _engine_score(product_item, "risk_score")
    balance_score = _positive_control_score_from_risk(risk_score)
    balance_body = (
        "책임은 늘지만 결정권이 약한 자리는 경력에 흠이 남습니다."
        if balance_score < 50
        else "책임 범위와 결정권이 함께 정리될 때 직업 성취가 제대로 남습니다."
        if balance_score < 68
        else "책임과 결정권이 함께 주어지는 자리에서 실력이 공식 평가로 이어집니다."
    )
    aligned: list[dict[str, Any]] = []
    for item in items:
        if str(item.get("title") or "") in {"권한 확보력", "권한·책임 균형도", "권한과 책임의 균형"}:
            updated = dict(item)
            updated["title"] = "권한 확보력"
            updated["score"] = balance_score
            updated["value"] = _score_value(balance_score)
            updated["tone"] = _topic_tone_from_score(balance_score)
            updated["body"] = balance_body
            updated["definition"] = "맡은 책임만큼 결정권과 보상이 함께 따라오는 직업 안정입니다."
            updated["evidence"] = f"근거 항목: 권한 확보력, 직업 부담 조절력 · 결과 등급: {_score_value(balance_score)}"
            aligned.append(updated)
        else:
            aligned.append(item)
    return aligned


def _merged_feature_axes_from_sections(*sections: dict[str, Any] | None) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in sections:
        if not section:
            continue
        for axis in section.get("feature_axes") or []:
            if not isinstance(axis, dict):
                continue
            key = str(axis.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(axis)
    return merged


def _topic_items_from_sections(domain: str, *sections: dict[str, Any] | None, limit: int = 5) -> list[dict[str, Any]]:
    if domain == "personality" and limit < 6:
        limit = 6
    return _web_topic_items(
        premium_topic_items(
            domain,
            limit=limit,
            feature_axes=_merged_feature_axes_from_sections(*sections),
        )
    )


def _checkpoint_value(points: list[Any], label: str, fallback: str = "") -> str:
    marker = f"{label}:"
    for point in points:
        text = str(point or "").strip()
        if text.startswith(marker):
            return text[len(marker) :].strip()
    return fallback


def _career_risk_block(
    *,
    achievement: str,
    recognition: str,
    expertise: str,
    authority: str,
    authority_score: int,
    caution: str,
) -> tuple[str, str, list[str]]:
    strengths = {
        "성과": _section_value_strength(achievement),
        "평가": _section_value_strength(recognition),
        "전문성": _section_value_strength(expertise),
        "권한": max(_section_value_strength(authority), authority_score),
    }
    if min(strengths.values()) >= 80:
        return (
            "성과 소유권을 분명히 해야 하는 자리",
            "성과가 커질수록 내 이름과 권한을 기록해야 합니다.",
            ["직책, 담당 범위, 결과물의 소유권이 분명할수록 직업운이 강해집니다."],
        )
    weakest = min(strengths.items(), key=lambda item: (item[1], item[0]))[0]
    if weakest == "권한" or (("권한" in caution or "책임" in caution) and strengths["권한"] < 80):
        return (
            "권한 없이 책임지는 자리",
            "책임은 크게 오는데 결정권이 약한 자리에서는 실력보다 소모가 먼저 남습니다.",
            ["업무 범위, 결재권, 평가 기준이 분명해야 오래 갑니다.", "실무만 떠안는 자리는 성취가 자기 이름으로 남기 어렵습니다."],
        )
    if weakest == "평가":
        return (
            "평가가 늦어지는 자리",
            "성과가 있어도 기록과 추천 체계가 없으면 좋은 평가가 늦어집니다.",
            ["결과물, 담당 범위, 고객 반응을 남겨야 다음 자리가 만들어집니다."],
        )
    if weakest == "전문성":
        return (
            "전문성이 흩어지는 자리",
            "여러 일을 넓게 맡기만 하면 전문 분야가 늦게 확정됩니다.",
            ["한 분야의 자격을 남겨야 직업운이 강해집니다."],
        )
    return (
        "성과가 흩어지는 자리",
        "역할이 자주 바뀌면 해낸 일이 이력으로 남기 어렵습니다.",
        ["맡은 일의 결과와 평가 기준을 분명히 남겨야 합니다."],
    )


def _premium_detail_blocks_for_card(
    section: dict[str, Any],
    product_item: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    domain = _domain_key(section)
    caution = _caution_for_card(section, product_item)
    if domain == "money":
        income = _feature_value_strongest(
            product_item,
            ("income_expansion", "liquidity_stability", "reward_claim_strength"),
            fallback_score=_engine_score(product_item, "opportunity_score"),
            cap="중상위권",
        )
        asset = _feature_value(product_item, "asset_retention")
        spending = _feature_value(product_item, "spending_control")
        deal = _combined_stability_value(product_item, "deal_selection", "loss_avoidance")
        income_body = (
            "성과가 보수, 계약금, 매출처럼 금액으로 환산되는 선이 분명합니다."
            if _grade_strength(income) >= 3
            else "수입은 한 번의 큰돈보다 고정 거래와 반복 보상에서 안정됩니다."
        )
        if _grade_strength(asset) >= 4:
            asset_body = "재물은 현금 보유보다 명의가 남는 자산에서 크게 굳어집니다."
        elif _grade_strength(asset) >= 3:
            asset_body = "수입을 등기 자산으로 바꿀 때 재산의 기반이 만들어집니다."
        else:
            asset_body = "수입이 들어와도 소유권과 회수 가능한 권리로 굳히는 힘이 약합니다."
        if "공동" in caution or "정산" in caution:
            loss_body = "가까운 사람과 돈을 묶으면 처음의 호의가 나중에는 명의와 몫의 문제로 바뀝니다."
            loss_bullets = ["동업, 공동 투자, 가족 간 자금 이동은 지분율과 명의를 먼저 확정해야 합니다.", "작게 넘긴 돈이 나중에는 몫과 책임의 기준이 됩니다."]
        elif "계약" in caution or "문서" in caution:
            loss_body = "계약 조건이 흐리면 받을 돈과 권리의 귀속이 약해집니다."
            loss_bullets = ["지급일, 환불 조건, 수수료 기준이 손익을 정합니다.", "구두 약속은 정산 단계에서 서로 다르게 기억됩니다."]
        else:
            loss_body = _plain_caution_sentence(caution)
            loss_bullets = ["수입 계좌, 투자금, 생활비를 분리해야 재물의 계산이 흐려지지 않습니다."]
        return [
            _detail_block(
                "수익 발생 지점",
                income_body,
                ["직업 성과가 숫자로 확인되는 일에서 보수 기준이 올라갑니다.", "계약 기준이 분명해야 받을 금액도 분명해집니다."],
            ),
            _detail_block(
                "자산화 방식",
                asset_body,
                ["등기처럼 이름이 남는 자산에 강합니다.", "지출 기준이 느슨하면 수입이 늘어도 재산으로 남는 몫은 늦게 보입니다."],
            ),
            _detail_block("권리와 정산이 예민한 자리", loss_body, loss_bullets, tone="risk"),
        ]
    if domain == "career":
        achievement = _feature_value(product_item, "career_achievement")
        recognition = _feature_value(product_item, "reputation_maintenance")
        expertise = _feature_value(product_item, "academic_expertise")
        authority = _risk_control_value(_engine_score(product_item, "risk_score"))
        authority_score = _section_value_strength(authority)
        risk_title, risk_body, risk_bullets = _career_risk_block(
            achievement=achievement,
            recognition=recognition,
            expertise=expertise,
            authority=authority,
            authority_score=authority_score,
            caution=caution,
        )
        achievement_body = (
            "맡은 일의 범위와 결과물이 기록될수록 경력의 값이 올라갑니다."
            if _grade_strength(achievement) >= 3
            else "빠른 확장보다 담당 범위가 분명한 자리를 잡는 일이 먼저입니다."
        )
        recognition_body = (
            "평가는 말보다 기록, 추천, 직책으로 남을 때 강합니다."
            if _grade_strength(recognition) >= 3
            else "평가는 느리게 붙는 편이라 결과물과 이력 증빙을 분명히 남겨야 합니다."
        )
        return [
            _detail_block(
                "성과가 자기 이름으로 남는 자리",
                achievement_body,
                ["담당 범위가 결과물로 확인되는 자리에서 강합니다.", "일의 끝이 실적, 문서, 평판으로 남을수록 다음 직책이 가까워집니다."],
            ),
            _detail_block(
                "평가받는 방식",
                recognition_body,
                ["전문성이 드러나는 자리에서 직업적 신뢰가 생깁니다.", "추천, 심사, 공식 책임을 통해 평가가 분명해집니다."],
            ),
            _detail_block(risk_title, risk_body, risk_bullets, tone="risk"),
        ]
    if domain == "love":
        opening = _feature_value(product_item, "interpersonal_influence")
        expression = _feature_value(product_item, "communication_expression")
        stability = _feature_value(product_item, "relationship_stability")
        recovery = _feature_value(product_item, "conflict_recovery")
        if "거리" in caution or "표현" in caution:
            risk_body = "마음이 깊어도 표현이 늦으면 상대는 애정보다 불확실함을 먼저 느낍니다."
        else:
            risk_body = _plain_caution_sentence(caution)
        opening_body = (
            "인연은 갑작스러운 설렘보다 반복해서 마주치는 접점에서 깊어집니다."
            if _grade_strength(opening) >= 3
            else "인연은 많게 열리는 편이 아니라 오래 볼 사람을 가려 만나는 쪽입니다."
        )
        expression_body = (
            "호감이 생겨도 상대의 태도를 확인한 뒤 관계를 진전시킵니다."
            if _grade_strength(expression) >= 3
            else "마음이 있어도 표현이 늦으면 상대가 확신을 갖기 어렵습니다."
        )
        return [
            _detail_block("사랑을 시작하는 방식", opening_body, [f"인연 형성력: {opening}"]),
            _detail_block("애정 표현 방식", expression_body, [f"애정 표현성: {expression}"]),
            _detail_block("관계가 흔들리는 지점", risk_body, [f"관계 지속력: {stability}", f"재회 가능성: {recovery}"], tone="risk"),
        ]
    if domain == "marriage":
        stability = _feature_value(product_item, "marriage_stability")
        practical = _feature_value(product_item, "practical_planning")
        family = _feature_value(product_item, "family_responsibility")
        if "주거" in caution or "가족" in caution or "생활" in caution:
            risk_body = "결혼에서는 감정보다 생활 기준이 더 크게 떠오릅니다."
        else:
            risk_body = _plain_caution_sentence(caution)
        stability_body = (
            "결혼운은 감정이 생활 계획으로 넘어갈 때 강해집니다."
            if _grade_strength(stability) >= 3
            else "결혼은 감정보다 생활 기준이 정리된 뒤 안정됩니다."
        )
        practical_body = (
            "생활 기준이 분명해지면 결혼 이야기가 빠르게 구체화됩니다."
            if _grade_strength(practical) >= 3
            else "생활 기준이 흔들리면 결혼 결정이 늦어집니다."
        )
        return [
            _detail_block("결혼이 안정되는 방식", stability_body, [f"혼인 성향: {stability}"]),
            _detail_block("생활 기준", practical_body, [f"생활 안정: {practical}"]),
            _detail_block("충돌이 생기는 자리", risk_body, [f"가족 책임 경계력: {family}", "생활 기준은 결혼 전에 먼저 정리하는 편이 안전합니다."], tone="risk"),
        ]
    return []


def _axis_by_keys(axes: list[dict[str, str]], keys: tuple[str, ...], *, strongest: bool = True) -> dict[str, str] | None:
    matched = [axis for axis in axes if str(axis.get("key") or "") in keys or str(axis.get("label") or "") in keys]
    if not matched:
        return None
    ranked = sorted(matched, key=_axis_rank_score, reverse=strongest)
    return ranked[0]


def _axis_identity(axis: dict[str, str] | None) -> str:
    if not axis:
        return ""
    return str(axis.get("key") or axis.get("label") or axis.get("title") or "").strip()


def _axis_by_keys_excluding(
    axes: list[dict[str, str]],
    keys: tuple[str, ...],
    excluded: tuple[dict[str, str] | None, ...],
    *,
    strongest: bool = True,
) -> dict[str, str] | None:
    excluded_keys = {_axis_identity(axis) for axis in excluded if _axis_identity(axis)}
    matched = [
        axis
        for axis in axes
        if (str(axis.get("key") or "") in keys or str(axis.get("label") or "") in keys)
        and _axis_identity(axis) not in excluded_keys
    ]
    if not matched:
        return _axis_by_keys(axes, keys, strongest=strongest)
    return sorted(matched, key=_axis_rank_score, reverse=strongest)[0]


def _axis_label_value(axis: dict[str, str] | None, fallback: str = "") -> str:
    if not axis:
        return fallback
    label = str(axis.get("label") or "").strip()
    value = str(axis.get("value") or "").strip()
    if label and value:
        return f"{label} {value}"
    return label or value or fallback


def _axis_product_title(axis: dict[str, str] | None, fallback: str = "") -> str:
    if not axis:
        return fallback
    label = str(axis.get("label") or "").strip()
    return label or fallback


def _axis_product_body(
    domain: str,
    axis: dict[str, str] | None,
    *,
    role: str,
    fallback: str,
) -> str:
    if not axis:
        return fallback
    key = str(axis.get("key") or "").strip()
    value = str(axis.get("value") or "").strip()
    strong = _section_value_strength(value) >= 74
    watch = _section_value_strength(value) <= 45 or role == "watch"
    copy: dict[str, dict[str, tuple[str, str, str]]] = {
        "money": {
            "wealth_formation": (
                "돈이 생기는 자리가 분명합니다. 처음부터 큰 자산으로 시작하기보다 직업, 거래, 역할의 대가가 반복되면서 재물이 형성됩니다.",
                "재물은 한 번에 크게 튀기보다 반복 수입과 거래 경험을 통해 만들어집니다.",
                "재물 기회가 있어도 돈의 출처와 권리 형태가 불분명하면 실제 몫이 작아집니다.",
            ),
            "wealth_scale": (
                "일상의 수입을 넘어 거래 단위가 커질 수 있습니다. 단순 급여보다 계약, 지분, 장기 보유 자산에서 재물의 크기가 달라집니다.",
                "재물 규모는 안정된 수입 이후에 천천히 커집니다.",
                "금액을 키우는 과정에서는 상대, 명의, 회수 조건을 놓치면 규모보다 부담이 먼저 커집니다.",
            ),
            "income_creation": (
                "수입 창출력은 선명합니다. 맡은 일의 대가가 금액으로 잡히고, 성과가 보수로 돌아옵니다.",
                "수입은 직업적 역할과 거래 기준이 분명할 때 안정됩니다.",
                "일은 많아도 보상 기준이 늦게 정해지면 실제로 가져가는 몫이 줄어듭니다.",
            ),
            "skill_income": (
                "재주가 곧 수입원이 됩니다. 말, 기획, 기술, 상담, 콘텐츠처럼 직접 만들어낸 결과물이 돈으로 바뀝니다.",
                "재주는 상품이나 서비스 형태가 잡힐 때 수익으로 바뀝니다.",
                "재능이 있어도 판매 단위와 가격 기준이 없으면 수입 전환이 늦습니다.",
            ),
            "performance_reward": (
                "성과에 대한 보상 요구가 분명합니다. 해낸 일이 기록되고 상대가 인정하면 보수, 성과급, 계약금으로 이어집니다.",
                "성과 보상은 기준이 분명할 때 확보됩니다.",
                "성과를 내고도 기준을 정하지 않으면 공로는 남고 보상은 작아질 수 있습니다.",
            ),
            "asset_retention": (
                "수입이 현금으로 지나가지 않고 소유권 있는 자산으로 남기 쉽습니다. 등기, 지분, 장기 보유 자산처럼 권리로 확인되는 돈이 유리합니다.",
                "재산은 소유권이 남는 방식에서 만들어집니다.",
                "수입이 생겨도 소비와 임시 비용으로 흩어지면 자산의 흔적이 약해집니다.",
            ),
            "cashflow_stability": (
                "수입 이후의 운용도 안정적입니다. 생활비와 고정비를 감당한 뒤에도 남는 돈의 규모가 비교적 일정합니다.",
                "자금 운용은 무리한 확장보다 안정된 배분에서 유리합니다.",
                "수입 직후 지출이 커지면 재물의 체감이 약해집니다.",
            ),
            "investment_trading_judgment": (
                "투자와 거래를 읽는 감각이 좋습니다. 수익률보다 회수 가능성, 명의, 기간을 따질 때 판단이 정확해집니다.",
                "투자와 거래는 권리 구조가 분명할 때 맞습니다.",
                "상대의 말만 믿고 들어가는 투자는 손실로 굳기 쉽습니다.",
            ),
            "shared_asset_stability": (
                "공동자금에서도 자기 몫을 지킬 수 있습니다. 단, 명의와 지분을 처음부터 분리할 때 안정됩니다.",
                "공동자금은 명의와 지분이 먼저입니다.",
                "가까운 사람과 돈을 묶으면 자기 몫이 흐려집니다. 가족 지원, 공동 투자, 동업성 거래에서 배신감이나 손실이 생기기 쉽습니다.",
            ),
            "contract_stability": (
                "계약과 명의로 금전 권리를 지킬 수 있습니다. 지급일, 지분, 수령액이 문서에 남을수록 재물운이 안정됩니다.",
                "계약과 명의가 재물 안정의 기준입니다.",
                "서류와 명의가 약하면 받을 돈이 늦어지거나 몫이 줄어듭니다. 구두 약속, 지연 지급, 빌려준 돈은 손실로 굳기 쉽습니다.",
            ),
            "family_asset_boundary": (
                "가족 재산에서도 자기 몫을 지킬 기준이 있습니다. 도움과 상속, 공동 지출을 분리할수록 안정됩니다.",
                "가족 재산은 정과 권리를 분리해야 안정됩니다.",
                "가족 돈이 얽히면 자기 책임이 아닌 비용까지 떠안을 수 있습니다. 정으로 시작한 지원이 장기 부담으로 남기 쉽습니다.",
            ),
            "debt_guarantee_control": (
                "부채와 보증을 관리할 수 있습니다. 책임 범위를 수치로 제한하면 큰 손실은 피합니다.",
                "보증과 대여는 한도를 정할 때 안정됩니다.",
                "보증, 대여, 채무 인수는 손실이 커지기 쉬운 자리입니다. 부탁을 거절하지 못하면 돈보다 책임이 먼저 남습니다.",
            ),
            "financial_defense": (
                "재정 방어력이 분명합니다. 체면 지출과 불필요한 보증을 끊어내면 자금이 빠르게 안정됩니다.",
                "재정 방어는 돈을 더 버는 것만큼 중요합니다.",
                "손실이 시작되면 작은 비용이 반복 지출로 굳습니다. 초기에 끊지 않으면 재물의 회복이 늦어집니다.",
            ),
        },
        "career": {
            "career_fit": (
                "직업 적성은 뚜렷합니다. 단순 반복보다 기준을 세우고 결과를 남기는 일에서 능력이 드러납니다.",
                "역할이 분명한 일에서 적성이 분명해집니다.",
                "맞지 않는 자리에 오래 있으면 실력보다 피로가 먼저 쌓입니다.",
            ),
            "career_achievement": (
                "성과가 경력 자산으로 남습니다. 맡은 일을 끝까지 정리해 기록과 실적으로 남길수록 경력의 단가가 올라갑니다.",
                "성과는 기록으로 남을 때 강해집니다.",
                "성과가 자기 이름으로 남지 않으면 일은 했는데 경력의 값은 늦게 오릅니다.",
            ),
            "recognition": (
                "평가와 명예로 이어지는 자리입니다. 추천, 직책, 공식 평가가 붙을 때 직업운이 크게 올라갑니다.",
                "평가는 공식 기록에서 올라갑니다.",
                "평가 기준이 흐린 자리는 공로가 다른 사람에게 넘어가기 쉽습니다.",
            ),
            "promotion_title_readiness": (
                "직함이 붙는 운입니다. 책임이 커질수록 단순 실무자가 아니라 담당자, 관리자, 책임자로 이름이 남습니다.",
                "승진과 직함은 역할이 분명할 때 따라옵니다.",
                "직함 없이 책임만 커지는 자리는 경력보다 소모가 먼저 남습니다.",
            ),
            "social_ascent": (
                "사회적 도약성이 높습니다. 직업 성취가 평판, 제안, 더 큰 자리로 이어질 수 있습니다.",
                "직업 성취가 지위와 영향력으로 커집니다.",
                "겉으로 커 보이는 자리라도 실권이 없으면 도약보다 부담이 큽니다.",
            ),
            "authority_balance": (
                "권한을 확보할수록 직업운이 강해집니다. 결정권과 책임이 함께 주어지는 자리에서 성취가 오래 남습니다.",
                "권한이 붙을 때 경력이 안정됩니다.",
                "결정권 없는 책임은 피해야 합니다. 실무는 떠안고 평가와 성과의 이름을 가져가지 못하면 경력 손상이 생깁니다.",
            ),
            "responsibility_authority_balance": (
                "책임과 권한의 균형이 좋습니다. 맡은 범위, 보고 체계, 평가 기준이 분명할수록 실력이 크게 드러납니다.",
                "책임의 범위와 결정권을 같이 잡을 때 안정됩니다.",
                "책임이 커져도 권한이 없으면 직업 부담이 길게 남습니다.",
            ),
            "compensation_negotiation": (
                "보상 협상력이 강합니다. 성과를 연봉, 수수료, 성과급, 지분처럼 자기 몫으로 확정할 수 있습니다.",
                "성과는 보상 기준이 분명할 때 수입으로 이어집니다.",
                "성과를 냈는데 보상 기준을 미루면 가져갈 몫이 작아집니다.",
            ),
            "expertise": (
                "전문성이 경력의 핵심 자산입니다. 자격, 기술, 데이터, 경험이 쌓일수록 쉽게 대체되지 않는 사람이 됩니다.",
                "전문성은 시간을 들여 쌓일수록 시장에서 값이 올라갑니다.",
                "전문성이 기록되지 않으면 실력은 있어도 시장에서 낮게 평가될 수 있습니다.",
            ),
            "organization_fit": (
                "조직 안에서도 자리를 잡을 수 있습니다. 규칙과 체계가 있는 곳에서 역할이 분명하면 오래 갑니다.",
                "조직 적응은 역할이 명확할 때 좋습니다.",
                "규칙은 많은데 평가 기준이 흐린 조직에서는 답답함이 커집니다.",
            ),
            "affiliation_transition": (
                "소속이 바뀌어도 기회를 만들 수 있습니다. 부서 이동, 회사 변경, 직무 전환이 손실보다 확장으로 이어질 수 있습니다.",
                "소속 전환은 준비된 이력 위에서 유리합니다.",
                "준비 없이 옮기면 이름과 역할이 다시 약해집니다.",
            ),
            "independence_potential": (
                "독립 기반이 있습니다. 자기 이름, 전문성, 거래 기반이 생기면 조직 밖에서도 일할 수 있습니다.",
                "독립은 거래처와 전문성이 붙을 때 안정됩니다.",
                "이름과 고객 기반 없이 독립하면 수입보다 불안정성이 먼저 커집니다.",
            ),
            "misfit_work": (
                "맞지 않는 업무를 가려내야 합니다. 단순 보조, 결정권 없는 반복 업무, 공로가 흐려지는 자리는 오래 맞지 않습니다.",
                "업무 조건 감별이 중요합니다.",
                "맞지 않는 일을 오래 맡으면 실력보다 소모가 먼저 남습니다.",
            ),
        },
        "love": {
            "attraction_standard": (
                "끌림의 기준이 분명합니다. 말투보다 태도, 책임감, 생활 감각에서 마음이 움직입니다.",
                "호감은 태도와 생활 감각에서 깊어집니다.",
                "첫 호감만 믿고 들어가면 오래 갈 관계가 되기 어렵습니다.",
            ),
            "partner_selection": (
                "상대는 오래 볼 수 있는 사람인지 먼저 가립니다. 가벼운 설렘보다 태도와 책임감을 더 크게 봅니다.",
                "상대는 오래 볼 기준으로 고릅니다.",
                "순간적인 끌림에 밀리면 맞지 않는 사람을 오래 붙잡을 수 있습니다.",
            ),
            "partner_trust_filter": (
                "상대의 신뢰도를 잘 가려냅니다. 말보다 반복된 행동, 약속을 지키는 태도에서 마음이 열립니다.",
                "신뢰는 반복된 행동으로 확인합니다.",
                "상대의 말을 믿고 빨리 가까워지면 뒤늦게 실망이 커집니다.",
            ),
            "relationship_opening": (
                "인연은 반복되는 접점에서 열립니다. 직장, 소개, 사회활동처럼 계속 마주치는 자리에서 관계가 깊어집니다.",
                "인연은 반복된 만남 속에서 생깁니다.",
                "인연 자체가 적게 열리면 관계를 시작하는 속도가 늦습니다.",
            ),
            "relationship_progress": (
                "호감이 실제 관계로 넘어갈 수 있습니다. 마음이 확인되면 만남과 약속이 비교적 분명해집니다.",
                "관계 진전은 확인을 거쳐 움직입니다.",
                "확정을 미루면 상대가 먼저 지칠 수 있습니다.",
            ),
            "relationship_agency": (
                "관계를 시작하고 멈추는 기준이 분명합니다. 상대에게 끌려가기보다 관계의 속도와 거리를 스스로 정합니다.",
                "관계의 방향을 스스로 정하는 편입니다.",
                "주도권이 강하면 상대가 압박을 느낄 수 있습니다.",
            ),
            "relationship_tempo_control": (
                "관계 속도 조절이 좋습니다. 빨리 가까워지는 것보다 오래 갈 수 있는 속도를 찾습니다.",
                "만남과 연락의 속도를 조절합니다.",
                "속도가 너무 늦으면 상대가 확신을 잃습니다.",
            ),
            "expression": (
                "애정 표현이 분명하면 관계가 빨리 안정됩니다. 마음을 말과 행동으로 보여줄수록 상대가 안심합니다.",
                "표현 속도가 관계의 안정감을 가릅니다.",
                "마음보다 표현이 늦습니다. 좋아해도 상대가 확신을 받지 못하면 서운함이 먼저 쌓입니다.",
            ),
            "affection_receptivity": (
                "상대의 감정을 비교적 잘 받아냅니다. 서운함이 올라와도 관계를 바로 끊기보다 이해하려 합니다.",
                "정서적 수용력이 관계를 오래 붙잡습니다.",
                "상대의 감정을 지나치게 떠안으면 관계가 피곤해집니다.",
            ),
            "stability": (
                "깊어진 관계를 오래 유지합니다. 한 번 마음을 준 뒤에는 쉽게 돌아서지 않는 편입니다.",
                "관계는 오래 보지만 기준이 맞아야 합니다.",
                "서운함을 오래 넘기면 어느 순간 거리가 크게 벌어집니다.",
            ),
            "contact_distance_stability": (
                "연락과 거리 조절이 안정적입니다. 각자의 시간과 관계의 속도를 함께 맞추는 능력이 있습니다.",
                "연락과 거리는 무리 없이 맞출 때 안정됩니다.",
                "연락 간격이 길어지면 상대가 마음의 거리를 크게 느낍니다.",
            ),
            "misunderstanding": (
                "오해가 생겨도 다시 맞출 여지가 큽니다. 설명과 확인을 거치면 관계는 회복 쪽으로 돌아섭니다.",
                "오해는 말로 풀 때 줄어듭니다.",
                "말을 아끼면 작은 오해가 오래 남습니다.",
            ),
            "conflict_recovery": (
                "갈등 뒤에도 회복할 수 있습니다. 감정이 상해도 관계를 바로 버리기보다 다시 조정하는 힘이 있습니다.",
                "갈등 회복은 시간과 설명이 필요합니다.",
                "갈등이 반복되면 회복보다 피로가 먼저 커집니다.",
            ),
            "marriage_link": (
                "연애가 결혼 논의로 이어질 수 있습니다. 감정이 깊어지면 자연스럽게 생활과 약속을 생각합니다.",
                "연애는 현실 조건과 만날 때 결론이 분명해집니다.",
                "결혼 이야기를 미루면 관계가 애매하게 길어질 수 있습니다.",
            ),
        },
        "marriage": {
            "marriage_tendency": (
                "결혼은 안정과 책임을 중시합니다. 감정의 결론보다 생활을 함께 책임지는 약속으로 받아들입니다.",
                "결혼은 생활과 책임을 함께 볼 때 안정됩니다.",
                "감정만 앞세운 결혼은 뒤늦은 부담을 남깁니다.",
            ),
            "spouse_type": (
                "성실하고 기준 있는 배우자와 잘 맞습니다. 생활 태도와 책임감이 배우자 선택의 핵심입니다.",
                "배우자는 생활 기준이 맞아야 오래 갑니다.",
                "감정 기복이 큰 상대와는 결혼 뒤 생활 손상이 먼저 옵니다.",
            ),
            "marriage_realization": (
                "결혼이 현실로 이어질 가능성이 높습니다. 마음이 깊어지면 주거, 가족 협의, 절차가 빠르게 구체화됩니다.",
                "결혼 의사는 생활 준비와 함께 굳어집니다.",
                "현실 준비가 늦으면 결혼 의사도 같이 늦어집니다.",
            ),
            "life_stability": (
                "생활 안정성이 결혼운의 강점입니다. 집, 생활비, 역할 기준이 맞으면 결혼 생활이 오래 갑니다.",
                "주거와 생활비 기준이 결혼 안정의 핵심입니다.",
                "생활 기준이 어긋나면 애정이 있어도 피로가 커집니다.",
            ),
            "household_management": (
                "가정을 운영하는 감각이 있습니다. 일정, 지출, 역할 분담이 정리될수록 부부 생활이 안정됩니다.",
                "가정 운영은 기준이 있을 때 안정됩니다.",
                "가정 안의 책임이 한쪽으로 몰리면 갈등이 커집니다.",
            ),
            "housing_life_design": (
                "주거와 생활 설계가 강합니다. 결혼 이야기는 집, 생활비, 역할 분담이 잡힐 때 빠르게 진전됩니다.",
                "주거 계획이 분명할수록 결혼이 안정됩니다.",
                "집과 생활비 계획이 흐리면 결혼 결정이 늦어집니다.",
            ),
            "couple_finance": (
                "부부 재정은 기준을 세우면 안정됩니다. 공동 생활비와 개인 자산을 나눌수록 갈등이 줄어듭니다.",
                "공동 생활비와 개인 자산을 나누어야 합니다.",
                "부부 재정의 선이 흐리면 결혼 뒤 돈 문제가 반복됩니다.",
            ),
            "living_cost_standard": (
                "생활비 기준이 분명합니다. 반복 지출을 정리하면 결혼 생활의 안정감이 커집니다.",
                "생활비 기준은 결혼 안정의 바닥입니다.",
                "생활비 기준이 없으면 작은 지출이 반복 갈등으로 바뀝니다.",
            ),
            "couple_conflict": (
                "갈등을 조정할 수 있습니다. 감정보다 생활 기준과 책임 범위를 다시 맞추면 회복됩니다.",
                "부부 갈등은 기준을 다시 세울 때 풀립니다.",
                "부부 갈등이 반복되기 쉽습니다. 감정보다 역할, 돈, 가족 책임에서 부딪힙니다.",
            ),
            "family_boundary": (
                "가족 책임을 분리할 수 있으면 결혼이 안정됩니다. 양가와 원가족 문제에서 부부의 기준이 먼저입니다.",
                "가족 문제는 부부 기준을 먼저 세워야 합니다.",
                "원가족과 양가 문제가 부부 사이로 들어옵니다. 정으로 떠안은 책임이 결혼 생활의 피로로 바뀌기 쉽습니다.",
            ),
            "spouse_family_boundary": (
                "배우자 가족과의 선을 정하면 결혼 생활이 안정됩니다. 도움과 개입을 구분해야 합니다.",
                "배우자 가족과의 거리는 기준이 필요합니다.",
                "배우자 가족의 말이 부부 결정에 깊게 들어오면 갈등이 커집니다.",
            ),
            "marriage_durability": (
                "결혼 지속력은 좋습니다. 생활 기준을 세운 뒤에는 쉽게 흔들리지 않습니다.",
                "결혼은 기준이 맞으면 오래 갑니다.",
                "반복 갈등을 방치하면 결혼의 피로가 누적됩니다.",
            ),
        },
    }
    variants = copy.get(domain, {}).get(key)
    if not variants:
        return fallback
    if watch:
        return variants[2]
    if strong:
        return variants[0]
    return variants[1]


def _axis_product_item(
    domain: str,
    axis: dict[str, str] | None,
    *,
    role: str,
    label: str,
    fallback_title: str,
    fallback_body: str,
) -> dict[str, str]:
    value = str((axis or {}).get("value") or "").strip()
    if not value:
        value = "주의" if role == "watch" else "핵심"
    return {
        "role": role,
        "label": label,
        "title": _axis_product_title(axis, fallback_title),
        "value": value,
        "body": _axis_product_body(domain, axis, role=role, fallback=fallback_body),
    }


def _timing_keyword_summary(block: dict[str, Any] | None, fallback: str) -> str:
    text = str((block or {}).get("body") or "").strip()
    if not text:
        return fallback
    pairs = re.findall(r"(?:19|20)\d{2}년\(\d+세\)\s*([^/\.]+)", text)
    keywords: list[str] = []
    for pair in pairs:
        cleaned = re.sub(r"(입니다|입니다\.)$", "", pair).strip(" .")
        cleaned = re.sub(r"^(중심 분야는|핵심 사건은|대조 사건은)\s*", "", cleaned).strip()
        if cleaned and cleaned not in keywords:
            keywords.append(cleaned)
    if keywords:
        return " · ".join(keywords[:4])
    compact = re.sub(r"(결과가 선명하게 남는 해는|손실과 책임 소재를 분명히 해야 할 해는|지나온 연도)\s*", "", text)
    compact = re.sub(r"\s*중심 분야는.*$", "", compact).strip(" .")
    return compact[:70] if compact else fallback


def _candidate_event_value_series(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
    limit: int = 3,
) -> str:
    values = [
        _candidate_event_label(candidate, birth_year=birth_year)
        for candidate in candidates[:limit]
    ]
    values = [value for value in values if value]
    return " · ".join(values) if values else fallback


def _candidate_topic_series(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
    limit: int = 3,
) -> str:
    topics: list[str] = []
    for candidate in candidates:
        age = int(candidate.get("year") or 0) - birth_year + 1 if birth_year and candidate.get("year") else None
        title = _timing_event_title(candidate, age)
        phrase = _timing_event_keywords(candidate, age)
        for part in _unique_timing_parts(title, phrase):
            part = re.sub(r"\s+", " ", str(part or "").strip())
            if part and part not in topics:
                topics.append(part)
        if len(topics) >= limit:
            break
    return ", ".join(topics[:limit]) if topics else fallback


def _payload_event_display_topic(event: dict[str, Any]) -> str:
    title = re.sub(r"\s+", " ", str(event.get("title") or "").strip())
    if title in {"상승 연도", "주의 연도", "좋은 연도"}:
        title = ""
    if title.endswith(" 연도"):
        title = title[: -len(" 연도")].strip()
    elif title.endswith("연도") and len(title) > 2:
        title = title[: -len("연도")].strip()
    if title:
        return title
    for key in ("summary", "keywords", "focusLine"):
        candidate = re.sub(r"\s+", " ", str(event.get(key) or "").strip())
        if not candidate:
            continue
        for part in re.split(r"[·,/]+", candidate):
            part = re.sub(r"\s+", " ", part.strip())
            if part:
                return part
    keyword_items = event.get("keywordItems")
    if isinstance(keyword_items, list):
        for item in keyword_items:
            part = re.sub(r"\s+", " ", str(item or "").strip())
            if part:
                return part
    return ""


def _payload_event_value_series(
    events: list[dict[str, Any]],
    fallback: str,
    *,
    limit: int = 3,
) -> str:
    values: list[str] = []
    ordered = sorted(events, key=lambda item: int(item.get("year") or 9999))
    for event in ordered[:limit]:
        year = event.get("year")
        age = event.get("age")
        title = _payload_event_display_topic(event) or str(event.get("domainLabel") or "").strip()
        if not year:
            continue
        year_label = f"{year}년"
        if age:
            year_label += f"({age}세)"
        values.append(" ".join(part for part in (year_label, title) if part))
    return " · ".join(values) if values else fallback


def _payload_event_topic_series(
    events: list[dict[str, Any]],
    fallback: str,
    *,
    limit: int = 3,
) -> str:
    topics: list[str] = []
    ordered = sorted(events, key=lambda item: int(item.get("year") or 9999))
    for event in ordered:
        topic = _payload_event_display_topic(event)
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= limit:
            break
    return ", ".join(topics[:limit]) if topics else fallback


def _is_period_specific_story_text(text: str) -> bool:
    return bool(
        re.search(
            r"(?:19|20)\d{2}년|\d{4}-\d{2}-\d{2}|올해|당년|강한 시점|이 시기|해에는",
            str(text or ""),
        )
    )


def _premium_product_story_for_card(
    section: dict[str, Any],
    product_item: dict[str, Any] | None,
    axes: list[dict[str, str]],
    detail_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    domain = _domain_key(section)
    existing_headline = str(section.get("headline") or section.get("lead") or "").strip().rstrip(".")
    generated_headline = _headline_for_card(section, product_item).rstrip(".")
    can_use_existing = (
        existing_headline
        and not _is_period_specific_story_text(existing_headline)
        and len(existing_headline) <= 80
        and (domain == "personality" or product_item is None)
    )
    headline = existing_headline if can_use_existing else generated_headline
    summary = _summary_for_card(section, product_item)

    def axis(keys: tuple[str, ...], *, strongest: bool = True) -> dict[str, str] | None:
        return _axis_by_keys(axes, keys, strongest=strongest)

    def distinct_axis(
        keys: tuple[str, ...],
        *selected: dict[str, str] | None,
        strongest: bool = True,
    ) -> dict[str, str] | None:
        return _axis_by_keys_excluding(axes, keys, selected, strongest=strongest)

    def detail(tone: str) -> dict[str, Any] | None:
        for block in detail_blocks:
            if str(block.get("tone") or "") == tone:
                return block
        return None

    def detail_title(*keywords: str) -> dict[str, Any] | None:
        for block in detail_blocks:
            title = str(block.get("title") or "")
            if any(keyword and keyword in title for keyword in keywords):
                return block
        return None

    def block_title(block: dict[str, Any] | None, fallback: str) -> str:
        return str((block or {}).get("title") or fallback).strip() or fallback

    def block_body(block: dict[str, Any] | None, fallback: str) -> str:
        return str((block or {}).get("body") or fallback).strip() or fallback

    def year_summary_title(block: dict[str, Any] | None, fallback: str) -> str:
        text = block_body(block, "")
        years = re.findall(r"(?:19|20)\d{2}년\(\d+세\)", text)
        if years:
            return " / ".join(years[:3])
        return fallback

    strong_block = detail("strong") or (detail_blocks[0] if detail_blocks else None)
    watch_block = detail("risk") or detail("watch") or (detail_blocks[-1] if detail_blocks else None)

    if domain == "money":
        strong_axis = axis(("asset_retention", "income_creation", "wealth_scale", "skill_income", "performance_reward", "wealth_formation"))
        scene_axis = distinct_axis(("cashflow_stability", "investment_trading_judgment", "receivables_recovery", "business_expansion", "late_life_wealth_growth"), strong_axis)
        watch_axis = axis(("shared_asset_stability", "contract_stability", "family_asset_boundary", "debt_guarantee_control", "financial_defense"), strongest=False)
        contract_axis = distinct_axis(("contract_stability", "investment_trading_judgment", "receivables_recovery", "performance_reward"), strong_axis, scene_axis, watch_axis, strongest=True)
        return {
            "kicker": "재물 요약",
            "headline": headline,
            "lead": "이 재물운은 현금 유입보다 소유권과 회수 가능한 권리에서 값이 커집니다. 수입이 들어와도 명의, 지분, 계약 단위로 굳어질 때 재물의 격이 올라갑니다.",
            "items": [
                _axis_product_item(
                    domain,
                    strong_axis,
                    role="strong",
                    label="주요 재물 기반",
                    fallback_title="자산화 능력",
                    fallback_body="수입이 권리와 소유권으로 바뀔 때 재물운이 가장 선명합니다.",
                ),
                _axis_product_item(
                    domain,
                    scene_axis,
                    role="scene",
                    label="수익 확장 지점",
                    fallback_title="수입과 권리의 연결",
                    fallback_body="일의 대가가 금액으로만 끝나지 않고 계약 단위와 회수 가능한 권리로 이어질 때 재물 규모가 커집니다.",
                ),
                _axis_product_item(
                    domain,
                    watch_axis,
                    role="watch",
                    label="금전 손실 지점",
                    fallback_title=str(watch_block.get("title") if watch_block else "공동자금 운영력"),
                    fallback_body="가까운 사람과 돈을 묶을수록 처음의 호의가 나중에는 명의와 지분 문제로 돌아옵니다.",
                ),
                _axis_product_item(
                    domain,
                    contract_axis,
                    role="scene",
                    label="권리 확보 기준",
                    fallback_title="계약과 회수",
                    fallback_body="재물은 감으로 움직일 때보다 문서, 지급일, 회수 조건이 분명할 때 안정됩니다.",
                ),
            ],
        }

    if domain == "career":
        strong_axis = axis(("expertise", "career_achievement", "recognition", "promotion_title_readiness", "social_ascent"))
        scene_axis = distinct_axis(("responsibility_authority_balance", "compensation_negotiation", "organization_fit", "affiliation_transition"), strong_axis)
        watch_axis = axis(("authority_balance", "misfit_work", "responsibility_authority_balance"), strongest=False)
        reward_axis = distinct_axis(("compensation_negotiation", "recognition", "promotion_title_readiness", "career_achievement"), strong_axis, scene_axis, watch_axis, strongest=True)
        return {
            "kicker": "직업 요약",
            "headline": headline,
            "lead": "이 직업운은 성과가 누구의 이름으로 남는가에서 차이가 납니다. 해낸 일이 기록, 평가, 직함, 보상으로 연결될 때 경력의 값이 확실히 올라갑니다.",
            "items": [
                _axis_product_item(
                    domain,
                    strong_axis,
                    role="strong",
                    label="직업적 강점",
                    fallback_title="전문성과 공식 평가",
                    fallback_body="결과물이 문서, 직함, 공식 평가로 남는 자리에서 직업운이 가장 좋습니다.",
                ),
                _axis_product_item(
                    domain,
                    reward_axis,
                    role="scene",
                    label="평가와 보상",
                    fallback_title="성과의 보상 전환",
                    fallback_body="성과가 기록되고 상대가 인정하면 보수와 직함으로 이어집니다.",
                ),
                _axis_product_item(
                    domain,
                    watch_axis,
                    role="watch",
                    label="경력 손상 지점",
                    fallback_title=str(watch_block.get("title") if watch_block else "권한 확보력"),
                    fallback_body="책임만 크고 결정권이 약한 자리는 불리합니다. 실무는 떠안고 성과의 이름을 가져가지 못하면 경력보다 소모가 먼저 남습니다.",
                ),
                _axis_product_item(
                    domain,
                    scene_axis,
                    role="scene",
                    label="직업 선택 기준",
                    fallback_title="책임과 보상의 연결",
                    fallback_body="맡은 범위와 평가 기준이 분명할수록 경력은 다음 자리의 근거가 됩니다.",
                ),
            ],
        }

    if domain == "love":
        strong_axis = axis(("stability", "relationship_stability", "expression", "relationship_opening", "relationship_progress"))
        scene_axis = distinct_axis(("partner_selection", "partner_trust_filter", "relationship_pace_control", "emotional_acceptance"), strong_axis)
        watch_axis = axis(("friction", "expression", "contact_distance_stability", "misunderstanding_prevention", "surrounding_intervention_control"), strongest=False)
        progress_axis = distinct_axis(("relationship_progress", "relationship_opening", "marriage_link", "relationship_agency"), strong_axis, scene_axis, watch_axis, strongest=True)
        return {
            "kicker": "연애 요약",
            "headline": headline,
            "lead": "이 연애운은 빠른 설렘보다 신뢰가 확인된 관계에서 강합니다. 마음이 깊어지면 오래 가지만, 표현이 늦어지면 상대가 먼저 불안을 느낍니다.",
            "items": [
                _axis_product_item(
                    domain,
                    strong_axis,
                    role="strong",
                    label="사랑의 방식",
                    fallback_title="관계 지속력",
                    fallback_body="한 번 마음을 준 뒤에는 쉽게 돌아서지 않는 편입니다.",
                ),
                _axis_product_item(
                    domain,
                    scene_axis,
                    role="scene",
                    label="상대를 고르는 기준",
                    fallback_title="신뢰와 태도",
                    fallback_body="가벼운 말보다 실제 행동을 통해 상대를 판단합니다.",
                ),
                _axis_product_item(
                    domain,
                    watch_axis,
                    role="watch",
                    label="관계가 흔들리는 지점",
                    fallback_title=str(watch_block.get("title") if watch_block else "표현 거리감"),
                    fallback_body="좋아하는 마음이 있어도 말과 연락이 늦으면 상대는 확신을 잃습니다.",
                ),
                _axis_product_item(
                    domain,
                    progress_axis,
                    role="scene",
                    label="관계 진전성",
                    fallback_title="관계 진전력",
                    fallback_body="호감이 확인되면 실제 만남과 약속으로 이어집니다.",
                ),
            ],
        }

    if domain == "marriage":
        strong_axis = axis(("marriage_realization", "marriage_stability", "life_stability", "decision_consistency"))
        scene_axis = distinct_axis(("practical_planning", "housing_life_design", "household_operation", "living_cost_standard"), strong_axis)
        watch_axis = axis(("family_risk", "family_responsibility", "spouse_family_boundary", "couple_conflict_adjustment"), strongest=False)
        spouse_axis = distinct_axis(("spouse_type", "marriage_tendency", "couple_finance", "marriage_durability"), strong_axis, scene_axis, watch_axis, strongest=True)
        return {
            "kicker": "결혼 요약",
            "headline": headline,
            "lead": "이 결혼운은 감정의 깊이보다 생활이 맞아 들어갈 때 안정됩니다. 주거, 생활비, 가족 책임이 정리되면 결혼은 현실적으로 굳어집니다.",
            "items": [
                _axis_product_item(
                    domain,
                    strong_axis,
                    role="strong",
                    label="결혼이 안정되는 지점",
                    fallback_title="생활 기반 안정성",
                    fallback_body="약속을 실제 생활로 옮길 때 결혼운이 안정권에 들어옵니다.",
                ),
                _axis_product_item(
                    domain,
                    spouse_axis,
                    role="scene",
                    label="배우자와 맞는 기준",
                    fallback_title="배우자상",
                    fallback_body="오래 맞는 배우자는 감정만이 아니라 생활 태도와 책임감이 분명한 사람입니다.",
                ),
                _axis_product_item(
                    domain,
                    watch_axis,
                    role="watch",
                    label="부담이 커지는 지점",
                    fallback_title=str(watch_block.get("title") if watch_block else "가족 책임 경계력"),
                    fallback_body="양가와 원가족 문제가 부부 사이로 들어오면 결혼 생활의 피로가 커집니다.",
                ),
                _axis_product_item(
                    domain,
                    scene_axis,
                    role="scene",
                    label="장기 유지 조건",
                    fallback_title="주거와 생활 기준",
                    fallback_body="집, 생활비, 역할 분담이 정리될수록 결혼 이야기가 빨라집니다.",
                ),
            ],
        }

    if domain == "personality":
        strong_axis = axis(("personality_판단_방식", "personality_대인_태도", "personality_몰입_방향"))
        scene_axis = axis(("personality_감정_처리", "personality_압박_대응", "personality_실행_방식"))
        return {
            "kicker": "성격 요약",
            "headline": headline,
            "lead": "당신은 겉으로 쉽게 흔들리는 사람처럼 보이지 않습니다. 속으로는 손익, 책임, 상대의 태도를 오래 계산한 뒤 자기 기준을 세웁니다.",
            "items": [
                {
                    "role": "strong",
                    "label": "성격의 중심",
                    "title": _axis_label_value(strong_axis, "판단 기준"),
                    "value": "핵심",
                    "body": "중요한 선택 앞에서 남의 말보다 직접 확인한 근거를 우선합니다. 한 번 납득한 기준은 쉽게 바꾸지 않습니다.",
                },
                {
                    "role": "scene",
                    "label": "사람을 대하는 방식",
                    "title": _axis_label_value(scene_axis, "감정 처리"),
                    "value": "강점",
                    "body": "처음에는 거리를 두고 살피지만 신뢰한 사람은 오래 곁에 둡니다. 마음이 상하면 바로 터뜨리기보다 속으로 정리한 뒤 선을 긋습니다.",
                },
                {
                    "role": "watch",
                    "label": "압박을 받을 때",
                    "title": "기준 조율력",
                    "value": "주의",
                    "body": "부담이 커질수록 자기 입장이 굳어지고 타협의 폭이 좁아집니다. 이때는 감정 공방보다 책임 범위와 결론을 먼저 정하려 합니다.",
                },
            ],
        }

    if domain == "timing":
        good_block = detail_title("상승", "좋은")
        caution_block = detail_title("주의", "손실")
        past_block = detail_title("과거", "대조")
        timing_map = section.get("timing_map") if isinstance(section.get("timing_map"), dict) else {}
        good_events = [event for event in list(timing_map.get("goodHighlights") or []) if isinstance(event, dict)]
        caution_events = [event for event in list(timing_map.get("cautionHighlights") or []) if isinstance(event, dict)]
        past_events = [event for event in list(timing_map.get("pastCheck") or []) if isinstance(event, dict)]
        good_value = _payload_event_value_series(good_events, year_summary_title(good_block, "성과가 뚜렷한 해"))
        caution_value = _payload_event_value_series(caution_events, year_summary_title(caution_block, "책임과 손실을 가려야 하는 해"))
        past_value = _payload_event_value_series(past_events, year_summary_title(past_block, "이미 지나온 작용"))
        good_topics = _payload_event_topic_series(good_events, _timing_keyword_summary(good_block, "직업 성취, 재물 형성, 관계 안정"))
        caution_topics = _payload_event_topic_series(caution_events, _timing_keyword_summary(caution_block, "계약 손실, 책임 부담, 관계 충돌"))
        past_topics = _payload_event_topic_series(past_events, _timing_keyword_summary(past_block, "직업 전환, 자산 형성, 권한 불균형"))
        timing_headline = existing_headline or str(section.get("summary") or "").strip().rstrip(".") or "좋은 연도와 주의 연도가 뚜렷하게 갈리는 사주입니다"
        return {
            "kicker": "시기 요약",
            "headline": timing_headline,
            "lead": "20세부터 79세까지의 주요 연도를 압축했습니다. 상승 연도에는 성과와 자산이 남고, 주의 연도에는 계약, 권한, 가족 문제가 실제 부담으로 올라옵니다.",
            "items": [
                {
                    "role": "strong",
                    "label": "상승 연도",
                    "title": "상승 연도",
                    "value": good_value,
                    "body": f"{good_topics} 부문에서 실제 성과가 드러납니다.",
                },
                {
                    "role": "watch",
                    "label": "주의 연도",
                    "title": "주의 연도",
                    "value": caution_value,
                    "body": f"{caution_topics} 부문에서 손실과 책임 문제가 커집니다.",
                },
                {
                    "role": "scene",
                    "label": "지나온 주요 연도",
                    "title": "지나온 주요 연도",
                    "value": past_value,
                    "body": f"이미 지나온 해에는 {past_topics} 부문의 사건을 대조해볼 수 있습니다.",
                },
            ],
        }

    if domain == "life":
        youth_block = detail_title("초년", "청년")
        middle_block = detail_title("중년")
        later_block = detail_title("말년")
        return {
            "kicker": "인생 구간 요약",
            "headline": existing_headline or "인생의 무게가 중년 이후 더 뚜렷해지는 사주입니다",
            "lead": "초년에는 남의 기대보다 자기 기준이 먼저 만들어집니다. 중년에는 책임을 맡으면서 수입과 자산이 굳어지고, 말년에는 새 확장보다 보유 자산과 가족 관계를 안정시키는 일이 중요해집니다.",
            "items": [
                {
                    "role": "scene",
                    "label": "초년·청년",
                    "title": block_title(youth_block, "기준이 일찍 잡히는 시기"),
                    "value": "형성기",
                    "body": "초년에는 주변의 권유보다 직접 겪은 경험이 선택 기준이 됩니다. 첫 진로와 인간관계에서도 맞지 않는 것은 빨리 가려내는 편입니다.",
                },
                {
                    "role": "strong",
                    "label": "중년",
                    "title": block_title(middle_block, "성과가 재산으로 굳는 시기"),
                    "value": "성취기",
                    "body": "중년에는 맡는 책임이 커지고, 그 책임이 수입과 자산으로 남습니다. 직책, 거래처, 고정 수입처럼 손에 잡히는 결과가 늘어납니다.",
                },
                {
                    "role": "scene",
                    "label": "말년",
                    "title": block_title(later_block, "보유 자산을 지키는 시기"),
                    "value": "안정기",
                    "body": "말년에는 새 일을 크게 벌이기보다 이미 마련한 재산을 지키는 쪽이 유리합니다. 가족 관계와 주거 기반이 후반의 안정감을 결정합니다.",
                },
            ],
        }

    if domain == "honor":
        recognition_block = detail_title("인정", "평가")
        title_block = detail_title("직함", "직책")
        guard_block = detail_title("지키", "보호", "손상", "깎")
        return {
            "kicker": "명예 요약",
            "headline": "책임이 이름으로 남는 명예운입니다",
            "lead": "이 명예운은 가벼운 인기보다 공적 책임에서 강합니다. 직책, 공식 평가, 책임자 이력이 쌓일수록 사회적 신뢰가 붙고 이름값이 커집니다.",
            "items": [
                {
                    "role": "strong",
                    "label": "공식 인정",
                    "title": "직책 상승력",
                    "value": "강점",
                    "body": "조직이나 사회적 자리에서 책임 있는 일을 끝까지 처리할 때 이름이 남습니다. 결과를 책임진 기록이 직함과 평판으로 돌아옵니다.",
                },
                {
                    "role": "scene",
                    "label": "직책 운",
                    "title": "권한 기반 평판",
                    "value": "핵심",
                    "body": "권한이 없는 자리보다 결재권, 대표권, 책임 범위가 분명한 자리에서 명예가 커집니다.",
                },
                {
                    "role": "watch",
                    "label": "평판 손상 지점",
                    "title": "기록이 없을 때 생기는 손해",
                    "value": "주의",
                    "body": "구두 약속, 공동 비용, 책임 소재가 흐려지는 일은 평판 손상으로 번질 수 있습니다.",
                },
            ],
        }

    if domain == "social":
        trust_block = detail_title("신뢰", "형성")
        help_block = detail_title("조력", "도움", "소개")
        boundary_block = detail_title("부탁", "책임", "선")
        return {
            "kicker": "대인관계 요약",
            "headline": "좁지만 오래 남는 인맥에서 이득을 얻는 관계운입니다",
            "lead": "이 대인관계운은 사람을 많이 모으는 쪽보다 검증된 관계에서 강합니다. 결정적인 순간에는 말뿐인 호감보다 실제 소개, 정보, 실무 도움을 주는 사람이 남습니다.",
            "items": [
                {
                    "role": "strong",
                    "label": "신뢰 축적",
                    "title": "오래 남는 사람을 고르는 기준",
                    "value": "강점",
                    "body": "처음부터 쉽게 가까워지기보다 시간을 두고 사람을 확인합니다. 오래 본 사람일수록 이익과 책임을 함께 나눌 수 있습니다.",
                },
                {
                    "role": "scene",
                    "label": "실질 조력",
                    "title": "말보다 행동으로 돕는 인연",
                    "value": "핵심",
                    "body": "중요한 순간에는 감정적 위로보다 실제 소개와 실무 지원을 해주는 사람이 남습니다. 사람을 넓히기보다 쓸 수 있는 관계를 남기는 쪽이 유리합니다.",
                },
                {
                    "role": "watch",
                    "label": "관계 손상 지점",
                    "title": "부탁이 책임으로 바뀌는 관계",
                    "value": "주의",
                    "body": "가까운 사람의 부탁을 계속 받아주면 호의가 책임으로 굳어집니다. 돈, 보증, 소개 부탁은 처음부터 범위를 정해야 합니다.",
                },
            ],
        }

    return {
        "kicker": "핵심 요약",
        "headline": headline,
        "lead": summary,
        "items": [],
    }


def _attach_premium_product_stories(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for section in sections:
        next_section = dict(section)
        story = next_section.get("product_story")
        has_story = isinstance(story, dict) and any(
            str(story.get(key) or "").strip() for key in ("headline", "lead", "kicker")
        )
        if not has_story:
            axes = [dict(item) for item in list(next_section.get("judgment_axes") or []) if isinstance(item, dict)]
            detail_blocks = [
                dict(item) for item in list(next_section.get("detail_blocks") or []) if isinstance(item, dict)
            ]
            if axes or detail_blocks or _domain_key(next_section) in {"personality", "money", "career", "love", "marriage"}:
                next_section["product_story"] = _premium_product_story_for_card(
                    next_section,
                    None,
                    axes,
                    detail_blocks,
                )
        enriched.append(next_section)
    return enriched


def _normalize_premium_section(
    section: dict[str, Any],
    product_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(section)
    domain_label = str(section.get("domain_label") or "운세")
    detail_label = domain_label.removesuffix("운") if domain_label != "운세" else domain_label
    lead = _headline_for_card(section, product_item)
    summary = _summary_for_card(section, product_item)
    title = f"{detail_label} 세부 운세"
    normalized["title"] = title
    normalized["heading"] = title
    normalized["lead"] = lead
    normalized["headline"] = lead
    normalized["summary"] = summary
    normalized["narrative"] = summary
    normalized["narrative_paragraphs"] = [summary]
    normalized["section_id"] = f"premium-{_domain_key(section)}"
    normalized["packet_id"] = f"premium-{_domain_key(section)}"
    normalized["period_label"] = "종합"
    normalized["paragraphs"] = _premium_total_paragraphs(section, lead, summary)
    normalized["timing_windows"] = []
    normalized["checkpoints"] = _premium_checkpoints(section, product_item)
    judgment_axes = _judgment_axes_for_card(section, product_item)
    detail_blocks = _premium_detail_blocks_for_card(section, product_item)
    normalized["judgment_axes"] = judgment_axes
    normalized["detail_blocks"] = detail_blocks
    normalized["product_story"] = _premium_product_story_for_card(section, product_item, judgment_axes, detail_blocks)
    normalized["topic_items"] = _premium_topic_items(_domain_key(section), product_item=product_item)
    normalized["feature_axes"] = list((product_item or {}).get("feature_axes") or [])
    normalized["engine_scores"] = _engine_score_payload(product_item)
    normalized["strength_score"] = _domain_strength_score(_domain_key(section), product_item)
    normalized["action_label"] = _action_for_card(section, product_item)
    normalized["caution_label"] = _caution_for_card(section, product_item)
    normalized["timing_paragraphs"] = []
    return normalized


def _premium_total_paragraphs(section: dict[str, Any], lead: str, summary: str) -> list[str]:
    paragraphs: list[str] = []
    seen: set[str] = set()
    for candidate in (lead, summary):
        text = str(candidate or "").strip()
        if text and text not in seen:
            paragraphs.append(_polish_factor_basis_text(text))
            seen.add(text)
    if paragraphs:
        return paragraphs[:2]
    for paragraph in list(section.get("paragraphs") or []):
        text = str(paragraph or "").strip()
        if not text:
            continue
        if re.search(r"\d{4}-\d{2}-\d{2}", text):
            continue
        if "가장 뚜렷한 시기" in text or "해당 연도" in text:
            continue
        if "보조 근거 코드" in text or "basis" in text or "근거 코드" in text:
            continue
        if "이 해석은" in text and "근거로 정리" in text:
            continue
        if re.search(r"상위\s*\d+%|안팎", text):
            continue
        text = (
            text.replace("정산 방식과 지출 통제가 늦어지는 상황", "정산 기준이 늦게 잡히는 상황")
            .replace("정산 방식과 지출 기준이 늦어지는 상황", "정산 기준이 늦게 잡히는 상황")
            .replace("정산 방식과 지출 기준가 늦어지는 상황", "정산 기준이 늦게 잡히는 상황")
            .replace("사회적 평가를 통해 표면화됩니다", "사회적 평가로 드러납니다")
        )
        if text.startswith("재물은 막연한 기회보다 구체적인 역할"):
            text = (
                "재물은 막연한 기회보다 구체적인 역할, 프로젝트, 거래에서 움직입니다. "
                "성과가 평가를 받으면 수입으로 연결됩니다. "
                "이때는 수입이 커져도 정산 기준이 늦게 잡히는 상황을 조심해야 합니다. "
                "당신은 돈이 움직일 때 받을 몫과 나갈 돈을 먼저 가르는 사람입니다."
            )
        elif text.startswith("직업운은 맡겨진 책임"):
            text = (
                "직업운은 맡겨진 책임과 성과가 공식 평가로 이어질 때 강하게 드러납니다. "
                "이때는 역할이 커져도 권한과 평가 기준이 늦게 정해지는 상황을 조심해야 합니다. "
                "당신은 역할이 커질수록 권한과 평가 기준을 먼저 확인하는 사람입니다."
            )
        if text not in seen:
            paragraphs.append(_polish_factor_basis_text(text).replace("지출 통제", "지출 기준"))
            seen.add(text)
    if paragraphs:
        return paragraphs[:3]
    clean_summary = str(summary or "").strip()
    return [clean_summary] if clean_summary else []


def _premium_section(
    section_id: str,
    *,
    domain: str,
    domain_label: str,
    heading: str,
    lead: str,
    narrative: str,
    checkpoints: list[str],
    timing_paragraphs: list[str] | None = None,
    narrative_paragraphs: list[str] | None = None,
    detail_blocks: list[dict[str, Any]] | None = None,
    timing_events: list[dict[str, Any]] | None = None,
    summary_items: list[dict[str, str]] | None = None,
    topic_items: list[dict[str, Any]] | None = None,
    feature_axes: list[dict[str, Any]] | None = None,
    judgment_axes: list[dict[str, str]] | None = None,
    strength_score: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "section_id": section_id,
        "packet_id": section_id,
        "domain": domain,
        "domain_label": domain_label,
        "title": heading,
        "heading": heading,
        "lead": lead,
        "headline": lead,
        "summary": narrative,
        "narrative": narrative,
        "narrative_paragraphs": narrative_paragraphs or [narrative],
        "basis_paragraph": "",
        "basis_paragraphs": [],
        "basis_blocks": [],
        "checkpoints": checkpoints,
        "timing_paragraphs": timing_paragraphs or [],
        "topic_items": topic_items if topic_items is not None else _premium_topic_items(domain),
        "feature_axes": feature_axes or [],
    }
    if judgment_axes:
        payload["judgment_axes"] = judgment_axes
    if strength_score is not None:
        payload["strength_score"] = strength_score
    if detail_blocks:
        payload["detail_blocks"] = detail_blocks
    if timing_events:
        payload["timing_events"] = timing_events
    if summary_items:
        payload["summary_items"] = summary_items
    return payload


def _section_by_domain(sections: list[dict[str, Any]], domain: str) -> dict[str, Any] | None:
    for section in sections:
        if _domain_key(section) == domain:
            return section
    return None


def _section_strength(section: dict[str, Any] | None) -> int:
    if not section:
        return 0
    value = section.get("strength_score")
    if isinstance(value, int):
        return value
    scores = section.get("engine_scores") or {}
    value = scores.get("event_probability_score")
    return value if isinstance(value, int) else 0


def _ranked_domain_sections(sections: list[dict[str, Any]], limit: int = 2) -> list[dict[str, Any]]:
    ranked = [
        section
        for section in sections
        if _domain_key(section) in {"money", "career", "love", "marriage"}
    ]
    ranked.sort(key=_section_strength, reverse=True)
    return ranked[:limit]


def _domain_pair_label(sections: list[dict[str, Any]]) -> str:
    labels = [str(section.get("domain_label") or section.get("heading") or "운세") for section in sections]
    if not labels:
        return "핵심 운세"
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]}{_and_particle(labels[0])} {labels[1]}"


def _life_theme_from_sections(sections: list[dict[str, Any]]) -> tuple[str, str]:
    domains = {_domain_key(section) for section in sections}
    if {"money", "career"} <= domains:
        return (
            "직업 성취와 자산 형성",
            "직업에서 만든 성과가 재물 기반으로 남습니다",
        )
    if {"love", "marriage"} <= domains:
        return (
            "관계와 가정의 안정",
            "관계가 생활의 약속으로 이어집니다",
        )
    if "money" in domains:
        return ("자산 형성", "수입이 자산과 생활 기반으로 남습니다")
    if "career" in domains:
        return ("사회적 성취", "맡은 역할이 평가로 남습니다")
    if "love" in domains or "marriage" in domains:
        return ("관계 안정", "관계와 생활 기준이 삶의 중심에 놓입니다")
    pair = _domain_pair_label(sections)
    return (pair, f"{pair}이 삶의 중심 과제로 드러납니다")


def _pillar_row(chart_summary: dict[str, Any], key: str) -> dict[str, Any]:
    for row in chart_summary.get("pillarRows") or []:
        if row.get("key") == key:
            return row
    return {}


def _dominant_ten_god_label(chart_summary: dict[str, Any]) -> str:
    counts: dict[str, int] = {}
    for row in chart_summary.get("pillarRows") or []:
        ten_god = str(row.get("tenGod") or "").strip()
        if ten_god and ten_god != "일간":
            counts[ten_god] = counts.get(ten_god, 0) + 3
        for hidden in row.get("hiddenTenGods") or []:
            label = str(hidden or "").strip()
            if label and label != "일간":
                counts[label] = counts.get(label, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def _add_axis_scores(scores: dict[str, float], weights: dict[str, int], factor: float) -> None:
    for axis, weight in weights.items():
        scores[axis] = scores.get(axis, 0.0) + (weight * factor)


def _personality_ten_god_counts(chart_summary: dict[str, Any]) -> dict[str, float]:
    counts: dict[str, float] = {}
    position_weight = {"month": 4.0, "day": 3.0, "hour": 2.0, "year": 1.5}
    for row in chart_summary.get("pillarRows") or []:
        key = str(row.get("key") or "")
        weight = position_weight.get(key, 1.0)
        ten_god = str(row.get("tenGod") or "").strip()
        if ten_god and ten_god != "일간":
            counts[ten_god] = counts.get(ten_god, 0.0) + weight
        hidden_weight = weight * (0.55 if key == "month" else 0.35)
        for hidden in row.get("hiddenTenGods") or []:
            label = str(hidden or "").strip()
            if label and label != "일간":
                counts[label] = counts.get(label, 0.0) + hidden_weight
    return counts


def _personality_value_scores(chart_summary: dict[str, Any]) -> dict[str, float]:
    scores = {axis: 10.0 for axis in PERSONALITY_VALUE_AXIS_COPY}
    ten_counts = _personality_ten_god_counts(chart_summary)
    for ten_god, count in ten_counts.items():
        _add_axis_scores(scores, PERSONALITY_TEN_GOD_VALUE_WEIGHTS.get(ten_god, {}), count)

    position_weight = {"month": 3.5, "day": 2.5, "hour": 1.4, "year": 1.0}
    for row in chart_summary.get("pillarRows") or []:
        key = str(row.get("key") or "")
        weight = position_weight.get(key, 1.0)
        stem = str(row.get("stem") or "").strip()
        branch = str(row.get("branch") or "").strip()
        _add_axis_scores(scores, PERSONALITY_ELEMENT_VALUE_WEIGHTS.get(PERSONALITY_STEM_ELEMENT.get(stem, ""), {}), weight)
        _add_axis_scores(scores, PERSONALITY_ELEMENT_VALUE_WEIGHTS.get(PERSONALITY_BRANCH_ELEMENT.get(branch, ""), {}), weight * 1.15)
        if key == "month":
            _add_axis_scores(scores, PERSONALITY_ELEMENT_VALUE_WEIGHTS.get(PERSONALITY_BRANCH_ELEMENT.get(branch, ""), {}), 2.2)
    return scores


def _rank_personality_axes(scores: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def _personality_axis_text(axis: str, key: str, default: str = "") -> str:
    values = PERSONALITY_VALUE_AXIS_COPY.get(axis, {})
    return str(values.get(key) or default or axis)


def _personality_value_profile(chart_summary: dict[str, Any]) -> tuple[str, str, str, str, str]:
    ranked = _rank_personality_axes(_personality_value_scores(chart_summary))
    top = ranked[:3]
    low = ranked[-1][0] if ranked else "흥미"
    order = _personality_axis_text(top[0][0], "label", top[0][0]) if top else "안정 확보"
    first = top[0][0] if top else "안전"
    second = top[1][0] if len(top) > 1 else "질서"
    first_text = PERSONALITY_VALUE_AXIS_COPY[first]["summary"]
    second_text = PERSONALITY_VALUE_AXIS_COPY[second]["summary"]
    low_text = PERSONALITY_VALUE_AXIS_COPY[low]["low"]
    lead = (
        f"당신은 {_personality_axis_text(first, 'lead_mid')} "
        f"{_personality_axis_text(second, 'lead_final')} 성격입니다."
    )
    detail = f"{first_text} {second_text}"
    low_label = _personality_axis_text(low, "label", low)
    low_line = f"{_with_subject_particle(low_label)} 상대적으로 뒤로 밀립니다. {low_text}"
    return lead, order, detail, low_line, _personality_axis_text(first, "label", first)


PERSONALITY_DECISION_AXIS_COPY: dict[str, str] = {
    "조화": "결정을 내릴 때 사람 사이의 균형과 상대의 반응을 세밀하게 따집니다.",
    "흥미": "새로운 기회 앞에서는 실익을 먼저 계산합니다.",
    "독립": "스스로 납득하고 선택할 수 있어야 행동이 안정됩니다.",
    "배려": "가까운 사람의 사정과 책임을 쉽게 떼어놓지 못합니다.",
    "지위": "인정받을 수 있는 자리인지, 내 역할이 드러나는지를 중요하게 여깁니다.",
    "안전": "마지막에는 오래 유지될 수 있는 선택인지를 끝까지 따집니다.",
    "성취": "목표와 결과가 분명할수록 결정을 빠르게 좁힙니다.",
    "질서": "약속, 절차, 책임 범위가 분명해야 마음이 놓입니다.",
}


def _personality_decision_profile(chart_summary: dict[str, Any]) -> str:
    ranked = _rank_personality_axes(_personality_value_scores(chart_summary))[:3]
    parts = [
        PERSONALITY_DECISION_AXIS_COPY.get(axis)
        for axis, _score in ranked
        if PERSONALITY_DECISION_AXIS_COPY.get(axis)
    ]
    if parts:
        return " ".join(parts)
    return "스스로 납득할 수 있는 기준이 생겨야 판단과 행동이 안정됩니다."


def _personality_defense_profile(chart_summary: dict[str, Any]) -> tuple[str, str]:
    ten_counts = _personality_ten_god_counts(chart_summary)
    scores = {
        "정면 대응형": 8.0,
        "거리 확보형": 8.0,
        "기준 확인형": 8.0,
    }
    for name, value in ten_counts.items():
        if name in {"비견", "겁재", "상관", "편관"}:
            scores["정면 대응형"] += value * 2.0
        if name in {"편인", "정인"}:
            scores["거리 확보형"] += value * 2.0
        if name in {"정관", "정재", "정인"}:
            scores["기준 확인형"] += value * 1.8

    for row in chart_summary.get("pillarRows") or []:
        stem = str(row.get("stem") or "").strip()
        branch = str(row.get("branch") or "").strip()
        stem_element = PERSONALITY_STEM_ELEMENT.get(stem, "")
        branch_element = PERSONALITY_BRANCH_ELEMENT.get(branch, "")
        for element in (stem_element, branch_element):
            if element in {"fire", "metal"}:
                scores["정면 대응형"] += 1.0
            if element == "water":
                scores["거리 확보형"] += 1.2
            if element == "earth":
                scores["기준 확인형"] += 1.0
    label = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
    return label, PERSONALITY_DEFENSE_COPY[label]


def _personality_emotion_profile(chart_summary: dict[str, Any]) -> tuple[str, str]:
    ten_counts = _personality_ten_god_counts(chart_summary)
    day = _pillar_row(chart_summary, "day")
    day_branch = str(day.get("branch") or "").strip()
    day_branch_element = PERSONALITY_BRANCH_ELEMENT.get(day_branch, "")
    scores = {
        "확장형": 8.0,
        "긴장 관리형": 8.0,
        "버티기형": 8.0,
        "철수형": 8.0,
    }
    for name, value in ten_counts.items():
        if name in {"식신", "상관", "편재"}:
            scores["확장형"] += value * 1.8
        if name in {"정재", "정관"}:
            scores["긴장 관리형"] += value * 1.8
        if name in {"편관", "비견", "겁재"}:
            scores["버티기형"] += value * 1.7
        if name in {"편인", "정인"}:
            scores["철수형"] += value * 1.9
    if day_branch_element == "fire":
        scores["확장형"] += 3.0
    elif day_branch_element == "water":
        scores["철수형"] += 3.0
    elif day_branch_element == "earth":
        scores["긴장 관리형"] += 2.0
        scores["버티기형"] += 1.0
    elif day_branch_element == "metal":
        scores["긴장 관리형"] += 2.0
    elif day_branch_element == "wood":
        scores["확장형"] += 1.5
    label = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
    return label, PERSONALITY_EMOTION_COPY[label]


def _personality_action_pace_profile(chart_summary: dict[str, Any]) -> tuple[str, str]:
    ten_counts = _personality_ten_god_counts(chart_summary)
    scores = {
        "빠른 실행형": 8.0,
        "확인 후 실행형": 8.0,
        "지속 처리형": 8.0,
    }
    for name, value in ten_counts.items():
        if name in {"상관", "편재", "겁재", "편관"}:
            scores["빠른 실행형"] += value * 1.9
        if name in {"정재", "정관", "정인", "편인"}:
            scores["확인 후 실행형"] += value * 1.8
        if name in {"식신", "비견", "정재"}:
            scores["지속 처리형"] += value * 1.7
    for row in chart_summary.get("pillarRows") or []:
        key = str(row.get("key") or "")
        weight = 1.3 if key in {"month", "day"} else 0.8
        for element in (
            PERSONALITY_STEM_ELEMENT.get(str(row.get("stem") or ""), ""),
            PERSONALITY_BRANCH_ELEMENT.get(str(row.get("branch") or ""), ""),
        ):
            if element in {"fire", "wood"}:
                scores["빠른 실행형"] += weight
            if element in {"metal", "water"}:
                scores["확인 후 실행형"] += weight
            if element == "earth":
                scores["지속 처리형"] += weight
    label = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
    copy = {
        "빠른 실행형": "기회가 보이면 검토보다 실행이 앞섭니다. 다만 결정 기준이 흐리면 속도가 손실로 바뀔 수 있습니다.",
        "확인 후 실행형": "상황과 책임 범위가 잡힌 뒤 움직입니다. 늦어 보일 수 있지만 결정 뒤에는 쉽게 번복하지 않습니다.",
        "지속 처리형": "시작보다 유지에 강합니다. 빠른 반응보다 맡은 일을 끝까지 처리하는 지속성이 장점입니다.",
    }
    return label, copy[label]


def _personality_focus_profile(chart_summary: dict[str, Any]) -> tuple[str, str]:
    ranked = _rank_personality_axes(_personality_value_scores(chart_summary))
    primary = ranked[0][0] if ranked else "안전"
    if primary in {"성취", "지위"}:
        return (
            "성과 몰입형",
            "관심은 단순한 취미보다 결과와 평가가 남는 분야로 모입니다. 자기 이름이 걸린 일에서 집중력이 강해집니다.",
        )
    if primary in {"안전", "질서"}:
        return (
            "기준 몰입형",
            "불안정한 가능성보다 오래 유지되는 기준과 관리 가능한 분야에 마음이 오래 머뭅니다.",
        )
    if primary in {"조화", "배려"}:
        return (
            "관계 몰입형",
            "사람의 태도, 관계의 균형, 가까운 사람의 사정을 오래 살핍니다. 관계가 흔들리면 일의 집중도도 함께 흔들릴 수 있습니다.",
        )
    if primary == "독립":
        return (
            "자기 결정 몰입형",
            "스스로 정한 과제에 몰입할 때 가장 오래 갑니다. 지시만 받는 일보다 자기 판단이 들어가는 일에서 집중력이 살아납니다.",
        )
    return (
        "경험 탐색형",
        "새로운 경험이 들어올 때 관심이 분명해집니다. 같은 환경이 오래 반복되면 집중이 빠르게 식을 수 있습니다.",
    )


def _day_branch_emotion_line(branch: str) -> str:
    if branch in {"子", "亥"}:
        return "내면 반응: 마음이 복잡할수록 바로 말하지 않고 혼자 정리하려 합니다."
    if branch in {"寅", "卯"}:
        return "내면 반응: 사람의 말투와 관계의 변화를 민감하게 받아들입니다."
    if branch in {"巳", "午"}:
        return "내면 반응: 감정이 올라오면 표정과 말투가 먼저 달라집니다."
    if branch in {"申", "酉"}:
        return "내면 반응: 감정보다 사실관계와 상대의 태도를 먼저 판단합니다."
    if branch in {"辰", "戌", "丑", "未"}:
        return "내면 반응: 판단을 쉽게 넘기지는 않지만 한 번 마음이 닫히면 오래 갑니다."
    return "내면 반응: 마음을 쉽게 드러내기보다 상황을 확인한 뒤 반응합니다."


def _personality_domain_echo(top_sections: list[dict[str, Any]]) -> str:
    top = top_sections[0] if top_sections else {}
    domain = _domain_key(top)
    if domain == "money":
        return "현실 적용: 돈과 책임이 걸리면 사람보다 기준을 먼저 세웁니다."
    if domain == "career":
        return "현실 적용: 맡은 역할과 권한이 분명할 때 성격의 장점이 가장 잘 드러납니다."
    if domain == "love":
        return "현실 적용: 마음이 움직여도 상대의 태도와 반복되는 행동을 먼저 따집니다."
    if domain == "marriage":
        return "현실 적용: 가까운 관계일수록 생활 방식과 책임 분담을 무겁게 봅니다."
    return "현실 적용: 일을 대할 때 자신의 기준을 먼저 세운 뒤 움직입니다."


def _personality_operating_narrative(
    *,
    decision_detail: str,
    social_line: str,
    emotion_detail: str,
    defense_detail: str,
    pace_detail: str,
    focus_detail: str,
    strength_line: str,
    weakness_line: str,
) -> str:
    decision = str(decision_detail or "").strip()
    social = str(social_line or "").strip()
    emotion = str(emotion_detail or "").strip()
    defense = str(defense_detail or "").strip()
    pace = str(pace_detail or "").strip()
    focus = str(focus_detail or "").strip()
    strength = str(strength_line or "").strip()
    weakness = str(weakness_line or "").strip()

    parts = [
        _first_profile_sentence(decision),
        f"대인관계에서는 {social.rstrip('.') }." if social else "",
        _first_profile_sentence(defense),
        f"{strength.rstrip('.') }." if strength else "",
        f"다만 {weakness.rstrip('.') }." if weakness else "",
    ]
    return _join_profile_sentences(*(part for part in parts if part))


def _personality_priority_object(value: str) -> str:
    phrases = {
        "관계 균형": "상대의 반응과 관계의 균형을",
        "경험 확장": "새로운 기회와 실익을",
        "자기 결정": "스스로 납득할 수 있는지를",
        "책임 배려": "가까운 사람의 사정을",
        "사회적 인정": "인정받을 자리인지를",
        "안정 확보": "오래 유지될 선택인지",
        "목표 성취": "결과가 분명한지를",
        "절차 신뢰": "약속과 책임 범위가 맞는지를",
    }
    return phrases.get(value, _with_object_particle(value))


def _personality_priority_sentence(value_order: str) -> str:
    values = [item.strip() for item in str(value_order or "").split("·") if item.strip()]
    if values:
        return f"선택할 때는 {_personality_priority_object(values[0])} 가장 먼저 따집니다."
    return "선택 앞에서는 자기 기준을 세운 뒤 움직일 때 판단이 안정됩니다."


PERSONALITY_TYPE_PREFIX: dict[str, str] = {
    "조화": "관계 조율형",
    "흥미": "기회 포착형",
    "독립": "자기주도형",
    "배려": "책임 배려형",
    "지위": "인정 추구형",
    "안전": "안정 관리형",
    "성취": "성과 집중형",
    "질서": "원칙 관리형",
}

PERSONALITY_TYPE_SUFFIX: dict[str, str] = {
    "조화": "대인 조율형",
    "흥미": "확장 실행형",
    "독립": "자기 결정형",
    "배려": "책임 관리형",
    "지위": "사회 성취형",
    "안전": "현실 관리형",
    "성취": "성과 실행형",
    "질서": "원칙 관리형",
}

PERSONALITY_AXIS_SCENE_COPY: dict[str, str] = {
    "조화": "관계에서는 상대의 말투와 태도를 빠르게 읽습니다.",
    "흥미": "새로운 기회 앞에서는 실익을 먼저 계산합니다.",
    "독립": "스스로 선택할 수 있을 때 태도가 가장 선명합니다.",
    "배려": "가까운 사람의 사정을 소홀히 보지 않습니다.",
    "지위": "인정받는 자리에서 책임감과 승부욕이 살아납니다.",
    "안전": "오래 버틸 수 있는 선택인지 먼저 따집니다.",
    "성취": "결과가 분명할수록 집중력과 추진력이 살아납니다.",
    "질서": "약속과 책임 범위가 분명해야 마음이 놓입니다.",
}


def _personality_type_title(primary_axis: str, support_axis: str) -> str:
    if {primary_axis, support_axis} <= {"안전", "질서"}:
        return "안정·원칙 관리형"
    if {primary_axis, support_axis} <= {"성취", "지위"}:
        return "성과·인정 추구형"
    if {primary_axis, support_axis} <= {"조화", "배려"}:
        return "관계 책임형"
    prefix = PERSONALITY_TYPE_PREFIX.get(primary_axis, f"{_personality_axis_text(primary_axis, 'label', primary_axis)} 중심형")
    suffix = PERSONALITY_TYPE_SUFFIX.get(support_axis, "")
    if not suffix or support_axis == primary_axis:
        return prefix
    return f"{prefix} · {suffix}"


def _personality_type_subtitle(primary_axis: str, support_axis: str) -> str:
    primary = PERSONALITY_AXIS_SCENE_COPY.get(primary_axis) or PERSONALITY_VALUE_AXIS_COPY.get(primary_axis, {}).get("summary", "")
    support = PERSONALITY_AXIS_SCENE_COPY.get(support_axis) or PERSONALITY_VALUE_AXIS_COPY.get(support_axis, {}).get("summary", "")
    if primary and support and primary != support:
        return f"{primary} {support}"
    return primary or support or "자기 기준이 분명해질수록 선택과 행동이 안정됩니다."


def _first_profile_sentence(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    first = value.split(".", 1)[0].strip()
    return f"{first}." if first else value


def _personality_profile_summary(
    *,
    lead: str,
    primary_axis: str,
    support_axis: str,
    priority_sentence: str,
    emotion_detail: str,
    pressure_detail: str,
) -> str:
    first = str(lead or "").strip()
    primary = PERSONALITY_AXIS_SCENE_COPY.get(primary_axis, "")
    support = PERSONALITY_AXIS_SCENE_COPY.get(support_axis, "") if support_axis != primary_axis else ""
    pressure = _first_profile_sentence(pressure_detail)
    emotion = _first_profile_sentence(emotion_detail)
    closing = pressure or emotion or priority_sentence
    sentences = [first, primary, support, closing]
    return _join_profile_sentences(*(sentence for sentence in sentences if sentence))


def _personality_profile_summary_sentence(
    *,
    lead: str,
    decision_detail: str,
    emotion_detail: str,
) -> str:
    return _join_profile_sentences(lead, decision_detail, emotion_detail)


def _source_personality_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _source_personality_trait(profile: dict[str, Any], key: str) -> dict[str, Any]:
    value = profile.get(key)
    return value if isinstance(value, dict) else {}


def _source_personality_list(profile: dict[str, Any], key: str, limit: int = 3) -> list[str]:
    values = profile.get(key)
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _source_personality_phrase(values: list[str]) -> str:
    replacements = {
        "강직함": "원칙성",
        "책임감": "책임 의식",
        "완고함": "고집",
        "묵직함": "신중함",
        "통제감": "자기 통제력",
        "소유 기준": "내 몫에 대한 기준",
        "누적된 감정": "쌓인 감정",
        "고독감": "혼자 견디는 성향",
    }
    values = [replacements.get(str(value or "").strip(), str(value or "").strip()) for value in values if value]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]}{_and_particle(values[0])} {values[1]}"
    return f"{values[0]}, {values[1]}, {values[2]}"


def _compact_trait_phrase(value: str, limit: int = 2) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = [
        part.strip()
        for part in re.split(r"\s*[,·/]\s*", text)
        if part.strip()
    ]
    if not parts:
        return text
    return _source_personality_phrase(parts[:limit])


def _clean_personality_type_label(value: str) -> str:
    text = str(value or "").strip()
    for old, new in (
        (" 중심축", ""),
        ("중심축", ""),
        (" 기질", ""),
        ("기질", ""),
    ):
        text = text.replace(old, new)
    return text.strip(" ·")


def _personality_type_sentence(title: str) -> str:
    text = _clean_personality_type_label(title)
    if not text:
        return ""
    if "원칙" in text and "계산" in text:
        return "당신은 원칙을 쉽게 굽히지 않고, 속으로는 손익과 책임 범위를 꼼꼼히 계산합니다."
    parts = [
        part.strip()
        for part in re.split(r"\s*·\s*", text)
        if part.strip()
    ]
    clauses: list[str] = []
    for part in parts[:2]:
        if "원칙" in part:
            clauses.append("원칙을 쉽게 굽히지 않습니다")
        elif "계산" in part:
            clauses.append("속으로는 손익과 책임 범위를 꼼꼼히 계산합니다")
        elif "현실화" in part:
            clauses.append("생각을 실제 결과로 옮기려는 성향이 뚜렷합니다")
        elif "돌파" in part or "선도" in part:
            clauses.append("초반에 방향을 잡고 앞에서 밀어붙이는 성향이 강합니다")
        elif "완성" in part:
            clauses.append("일의 마무리와 완성도를 그냥 넘기지 않습니다")
        elif "야심" in part or "관리자" in part:
            clauses.append("성과와 책임을 자기 기준 안에서 관리하려 합니다")
        elif "신중" in part:
            clauses.append("확신이 서기 전까지 사람과 상황을 쉽게 단정하지 않습니다")
        elif "조율" in part:
            clauses.append("서로 다른 입장을 맞추는 감각이 발달해 있습니다")
        elif "감각" in part:
            clauses.append("분위기와 사람의 반응을 빠르게 읽습니다")
        elif "전략" in part:
            clauses.append("겉으로 드러난 말보다 다음 수를 먼저 계산합니다")
        elif "보호" in part:
            clauses.append("가까운 사람에게는 책임감이 강하게 작동합니다")
        elif "관찰" in part:
            clauses.append("사람과 상황을 먼저 관찰한 뒤 움직입니다")
        elif "확장" in part:
            clauses.append("새로운 기회와 실익을 빠르게 포착합니다")
        elif "신뢰" in part:
            clauses.append("사람을 넓게 믿기보다 오래 갈 사람을 가려냅니다")
        elif "균형" in part:
            clauses.append("관계의 균형과 명분을 중요하게 여깁니다")
        elif "책임" in part:
            clauses.append("맡은 책임을 쉽게 내려놓지 않습니다")
        elif "안정" in part:
            clauses.append("오래 유지될 수 있는 선택에 마음이 갑니다")
        elif "실행" in part:
            clauses.append("기회가 보이면 행동이 빠르게 나갑니다")
        elif "탐색" in part:
            clauses.append("새로운 경험이 들어올 때 관심이 살아납니다")
    if clauses:
        first, *rest = clauses
        return " ".join([f"당신은 {first}.", *(f"{clause}." for clause in rest)])
    if len(parts) >= 2:
        return f"당신은 {parts[0]}에 가까운 사람입니다. {parts[1]}의 성격도 선택과 관계에서 나타납니다."
    if text.endswith("성격"):
        return f"당신은 {text}입니다."
    if text.endswith("성향"):
        return f"당신은 {text}이 강합니다."
    return f"당신은 {text} 성격입니다." if text.endswith("형") else f"당신은 {text} 성향이 강합니다."


def _personality_profile_display_title(title: str, primary_axis: str, support_axis: str) -> str:
    text = _clean_personality_type_label(title)
    if not text:
        return _personality_type_title(primary_axis, support_axis)
    if "원칙" in text and "계산" in text:
        return "원칙이 강하고 손익 계산이 빠른 성격"
    if "원칙" in text:
        return "원칙이 강한 성격"
    if "계산" in text or "전략" in text:
        return "상황 판단이 빠른 성격"
    if "조율" in text:
        return "사람과 상황을 조율하는 성격"
    if "감각" in text or "심미" in text:
        return "감각과 기준이 섬세한 성격"
    if "책임" in text or "관리" in text:
        return "책임과 관리 의식이 강한 성격"
    if "개척" in text or "선도" in text:
        return "앞에서 방향을 여는 성격"
    parts = [part.strip().replace("형", "") for part in re.split(r"\s*·\s*", text) if part.strip()]
    if parts:
        return f"{parts[0]} 성향"
    return _personality_type_title(primary_axis, support_axis)


def _source_personality_lead(source_profile: dict[str, Any], fallback: str) -> str:
    day = _source_personality_trait(source_profile, "day_pillar_profile")
    month = _source_personality_trait(source_profile, "month_branch_profile")
    day_type = _clean_personality_type_label(str(day.get("compression_type") or ""))
    month_type = _clean_personality_type_label(str(month.get("compression_type") or ""))
    if day_type and month_type:
        return _personality_type_sentence(f"{day_type} · {month_type}")
    if day_type:
        return _personality_type_sentence(day_type)
    if month_type:
        return _personality_type_sentence(month_type)
    return fallback


def _source_personality_narrative(
    source_profile: dict[str, Any],
    fallback: str,
) -> str:
    day = _source_personality_trait(source_profile, "day_pillar_profile")
    month = _source_personality_trait(source_profile, "month_branch_profile")
    core = _source_personality_phrase(_source_personality_list(source_profile, "trait_keywords", 3))
    strengths = _source_personality_phrase(_source_personality_list(source_profile, "strength_keywords", 3))
    shadows = _source_personality_phrase(_source_personality_list(source_profile, "shadow_keywords", 2))
    day_outer = _source_personality_phrase(_source_personality_list(day, "outer_traits", 2))
    month_inner = _source_personality_phrase(_source_personality_list(month, "inner_traits", 2))
    sentences: list[str] = []
    if core:
        sentences.append(f"성격의 중심은 {core}입니다.")
    if day_outer:
        sentences.append(f"겉으로는 {_with_subject_particle(day_outer)} 먼저 느껴집니다.")
    if month_inner:
        sentences.append(f"속으로는 {_with_subject_particle(month_inner)} 오래 남습니다.")
    if strengths:
        sentences.append(f"일이 분명해지면 {_with_subject_particle(_compact_trait_phrase(strengths))} 강점으로 드러납니다.")
    if shadows:
        sentences.append(f"마음이 상하면 {_with_subject_particle(_compact_trait_phrase(shadows))} 오래 남습니다.")
    return _join_profile_sentences(*sentences) or fallback


def _source_personality_points(source_profile: dict[str, Any], fallback_points: list[str]) -> list[str]:
    if not source_profile:
        return fallback_points
    day = _source_personality_trait(source_profile, "day_pillar_profile")
    month = _source_personality_trait(source_profile, "month_branch_profile")
    core = _source_personality_phrase(_source_personality_list(source_profile, "trait_keywords", 3))
    strengths = _source_personality_phrase(_source_personality_list(source_profile, "strength_keywords", 3))
    shadows = _source_personality_phrase(_source_personality_list(source_profile, "shadow_keywords", 3))
    outer = _source_personality_phrase(_source_personality_list(day, "outer_traits", 2))
    inner = _source_personality_phrase(_source_personality_list(month, "inner_traits", 2))
    day_type = _clean_personality_type_label(str(day.get("compression_type") or ""))
    month_type = _clean_personality_type_label(str(month.get("compression_type") or ""))
    title = " · ".join(value for value in (day_type, month_type) if value)
    points = [
        f"성격 결론: {title}" if title else "",
        f"기본 성정: {core}" if core else "",
        f"겉으로 보이는 태도: {outer}" if outer else "",
        f"속기질: {inner}" if inner else "",
        f"강점: {strengths}" if strengths else "",
        f"주의할 성격: {shadows}" if shadows else "",
    ]
    points.extend(point for point in fallback_points if str(point or "").strip())
    deduped: list[str] = []
    seen_labels: set[str] = set()
    for point in points:
        text = str(point or "").strip()
        if not text:
            continue
        label = text.split(":", 1)[0].strip()
        if label in seen_labels and label in {"성격 결론", "강점", "주의할 성격"}:
            continue
        seen_labels.add(label)
        deduped.append(text)
    return deduped


def _personality_copy(
    top_sections: list[dict[str, Any]],
    chart_summary: dict[str, Any],
    source_profile: dict[str, Any] | None = None,
) -> tuple[str, str, list[str]]:
    day = _pillar_row(chart_summary, "day")
    month = _pillar_row(chart_summary, "month")
    day_stem = str(day.get("stem") or "")
    day_branch = str(day.get("branch") or "")
    month_branch = str(month.get("branch") or "")
    profile = PERSONALITY_STEM_PROFILE.get(day_stem) or PERSONALITY_STEM_PROFILE["戊"]
    month_label, month_line = PERSONALITY_MONTH_BRANCH_MODIFIER.get(
        month_branch,
        ("외부 태도", "밖에서는 자기 기준을 쉽게 드러내기보다 상황을 확인한 뒤 움직입니다."),
    )
    ten_god = _dominant_ten_god_label(chart_summary)
    ten_label, ten_line = PERSONALITY_TEN_GOD_TRAITS.get(
        ten_god,
        ("반복 태도", "스스로 납득할 수 있는 기준이 생겨야 행동이 안정됩니다."),
    )
    inner_line = _day_branch_emotion_line(day_branch)
    domain_echo = _personality_domain_echo(top_sections)
    value_lead, value_order, value_detail, value_low, primary_value_label = _personality_value_profile(chart_summary)
    decision_detail = _personality_decision_profile(chart_summary)
    defense_label, defense_detail = _personality_defense_profile(chart_summary)
    emotion_label, emotion_detail = _personality_emotion_profile(chart_summary)
    pace_label, pace_detail = _personality_action_pace_profile(chart_summary)
    focus_label, focus_detail = _personality_focus_profile(chart_summary)
    social_line = profile["social"].replace("사람 관계: ", "")
    core_line = profile["core"].replace("기본 성격: ", "")
    strength_line = profile["strength"].replace("강점: ", "")
    weakness_line = profile["weakness"].replace("약점: ", "")
    inner_text = inner_line.replace("내면 반응: ", "")
    lead = profile["lead"]
    priority_sentence = _personality_priority_sentence(value_order)
    narrative = _personality_operating_narrative(
        decision_detail=decision_detail,
        social_line=social_line,
        emotion_detail=emotion_detail,
        defense_detail=defense_detail,
        pace_detail=pace_detail,
        focus_detail=focus_detail,
        strength_line=strength_line,
        weakness_line=weakness_line,
    )
    points = [
        f"성격 결론: {lead}",
        f"선택 우선순위: {value_order}",
        f"판단 기준: {decision_detail}",
        f"대인 거리감: {social_line} {month_line}",
        f"감정 반응: {emotion_detail} {inner_text}",
        f"압박 대응: {defense_detail}",
        f"행동 속도: {pace_detail}",
        f"관심 몰입: {focus_detail}",
        f"보완 지점: {value_low}",
        f"성격 해석: {priority_sentence}",
        f"기본 기질: {core_line}",
        f"{month_label}: {month_line}",
        f"{ten_label}: {ten_line}",
        f"강점: {strength_line}",
        f"주의할 성격: {weakness_line}",
        domain_echo,
        f"대표 기준: {primary_value_label}",
        f"반응 유형: {emotion_label}",
        f"압박 유형: {defense_label}",
        f"실행 유형: {pace_label}",
        f"몰입 유형: {focus_label}",
    ]
    source = _source_personality_dict(source_profile)
    if source:
        lead = _source_personality_lead(source, lead)
        narrative = _source_personality_narrative(source, narrative)
        points = _source_personality_points(source, points)
    return lead, narrative, points


def _personality_profile_axis_score(score: float, low_score: float, high_score: float) -> int:
    if high_score <= low_score:
        return 68
    ratio = (score - low_score) / (high_score - low_score)
    return max(42, min(96, round(52 + ratio * 42)))


def _personality_coordinate_score(kind: str, *, primary_score: int, support_score: int, pace_type: str, pressure_type: str) -> int:
    if kind == "decision":
        return max(58, min(96, primary_score))
    if kind == "relationship":
        return max(54, min(92, round((primary_score + support_score) / 2)))
    if kind == "pressure":
        base = 78 if "기준" in pressure_type else 72
        if "긴장" in pressure_type:
            base = 68
        return max(50, min(92, base))
    if kind == "pace":
        if "빠른" in pace_type:
            return 84
        if "지속" in pace_type:
            return 74
        return 66
    return 68


def _personality_profile_payload(chart_summary: dict[str, Any], points: list[str]) -> dict[str, Any]:
    ranked = _rank_personality_axes(_personality_value_scores(chart_summary))
    if not ranked:
        return {}

    high_score = ranked[0][1]
    low_score = ranked[-1][1]
    primary_axis = ranked[0][0]
    support_axis = ranked[1][0] if len(ranked) > 1 else primary_axis
    lowest_axis = ranked[-1][0]
    axis_items = []
    for axis, score in ranked[:5]:
        normalized_score = _personality_profile_axis_score(score, low_score, high_score)
        axis_items.append(
            {
                "label": _personality_axis_text(axis, "label", axis),
                "value": _score_value(normalized_score),
                "score": normalized_score,
                "body": _personality_axis_text(axis, "summary", ""),
            }
        )

    decision = _checkpoint_value(points, "판단 기준")
    social = _checkpoint_value(points, "대인 거리감")
    emotion = _checkpoint_value(points, "감정 반응")
    pressure = _checkpoint_value(points, "압박 대응")
    pace = _checkpoint_value(points, "행동 속도")
    focus = _checkpoint_value(points, "관심 몰입")
    emotion_type = _checkpoint_value(points, "반응 유형", "감정 확인형")
    pressure_type = _checkpoint_value(points, "압박 유형", "기준 확인형")
    pace_type = _checkpoint_value(points, "실행 유형", "확인 후 실행형")
    focus_type = _checkpoint_value(points, "몰입 유형", "관심 몰입형")
    value_order = _checkpoint_value(points, "선택 우선순위") or _checkpoint_value(points, "삶의 기준", "")
    priority_sentence = _checkpoint_value(points, "성격 해석") or _personality_priority_sentence(value_order)
    external_attitude = _checkpoint_value(points, "외부 태도", "")
    source_title = _checkpoint_value(points, "성격 결론")
    source_core = _checkpoint_value(points, "기본 성정")
    source_outer = _checkpoint_value(points, "겉으로 보이는 태도")
    source_inner = _checkpoint_value(points, "속기질")
    basic_temperament = _checkpoint_value(points, "기본 기질", "")
    strength = _checkpoint_value(points, "강점", "")
    caution = _checkpoint_value(points, "주의할 성격", "")
    reality = _checkpoint_value(points, "현실 적용", "")
    primary_label = _personality_axis_text(primary_axis, "label", primary_axis)
    support_label = _personality_axis_text(support_axis, "label", support_axis)
    lowest_label = _personality_axis_text(lowest_axis, "label", lowest_axis)
    primary_score = axis_items[0]["score"] if axis_items else 68
    support_score = axis_items[1]["score"] if len(axis_items) > 1 else primary_score
    coordinate_axes = [
        {
            "label": "선택의 방향",
            "left": "상황 관찰",
            "right": primary_label,
            "value": f"{primary_label} 우위",
            "score": _personality_coordinate_score(
                "decision",
                primary_score=primary_score,
                support_score=support_score,
                pace_type=pace_type,
                pressure_type=pressure_type,
            ),
            "body": priority_sentence,
        },
        {
            "label": "관계의 거리",
            "left": "빠른 친화",
            "right": "신뢰 선별",
            "value": "신뢰 선별형",
            "score": _personality_coordinate_score(
                "relationship",
                primary_score=primary_score,
                support_score=support_score,
                pace_type=pace_type,
                pressure_type=pressure_type,
            ),
            "body": social,
        },
        {
            "label": "압박 반응",
            "left": "감정 반응",
            "right": pressure_type,
            "value": pressure_type,
            "score": _personality_coordinate_score(
                "pressure",
                primary_score=primary_score,
                support_score=support_score,
                pace_type=pace_type,
                pressure_type=pressure_type,
            ),
            "body": pressure,
        },
        {
            "label": "실행 속도",
            "left": "확인 후 실행",
            "right": "빠른 실행",
            "value": pace_type,
            "score": _personality_coordinate_score(
                "pace",
                primary_score=primary_score,
                support_score=support_score,
                pace_type=pace_type,
                pressure_type=pressure_type,
            ),
            "body": pace,
        },
    ]

    default_title = _personality_type_title(primary_axis, support_axis)
    default_subtitle = _personality_type_subtitle(primary_axis, support_axis)
    source_summary_parts = []
    if source_title:
        source_summary_parts.append(_personality_type_sentence(source_title))
    if source_core:
        source_summary_parts.append(f"기본 성정은 {source_core}입니다.")
    if strength:
        source_summary_parts.append(f"{_with_subject_particle(_compact_trait_phrase(strength))} 강점으로 드러납니다.")
    elif source_outer:
        source_summary_parts.append(f"겉으로는 {_with_subject_particle(source_outer)} 먼저 느껴집니다.")
    if caution:
        source_summary_parts.append(f"마음이 상하면 {_with_subject_particle(_compact_trait_phrase(caution))} 오래 남습니다.")
    elif source_inner:
        source_summary_parts.append(f"속으로는 {_with_subject_particle(source_inner)} 오래 남습니다.")
    source_summary = _join_profile_sentences(*source_summary_parts)
    default_summary = _personality_profile_summary(
            lead=_checkpoint_value(points, "성격 결론"),
            primary_axis=primary_axis,
            support_axis=support_axis,
            priority_sentence=priority_sentence,
            emotion_detail=emotion,
            pressure_detail=pressure,
    )

    return {
        "title": _personality_profile_display_title(source_title, primary_axis, support_axis) if source_title else default_title,
        "subtitle": f"{source_core} 성향이 중심입니다." if source_core else default_subtitle,
        "summary": source_summary or default_summary,
        "contrast": f"{_with_subject_particle(lowest_label)} 상대적으로 약합니다. 이 축을 놓치면 판단은 빠르지만 마무리가 거칠어질 수 있습니다.",
        "overview": [
            {
                "label": "선택 우선순위",
                "value": value_order or f"{primary_label} > {support_label}",
                "body": priority_sentence,
            },
            {
                "label": "대인 태도",
                "value": "관찰 후 접근",
                "body": external_attitude or social,
            },
            {
                "label": "감정 처리",
                "value": emotion_type,
                "body": emotion,
            },
            {
                "label": "현실 적용",
                "value": primary_label,
                "body": reality or strength or basic_temperament,
            },
        ],
        "coordinate_axes": coordinate_axes,
        "axes": axis_items,
        "cards": [
            {
                "label": "판단 방식",
                "value": primary_label,
                "body": priority_sentence,
                "tone": "strong",
            },
            {
                "label": "대인 태도",
                "value": "신뢰 선별형",
                "body": social,
                "tone": "neutral",
            },
            {
                "label": "감정 처리",
                "value": emotion_type,
                "body": emotion,
                "tone": "neutral",
            },
            {
                "label": "압박 대응",
                "value": pressure_type,
                "body": pressure,
                "tone": "watch",
            },
            {
                "label": "실행 방식",
                "value": pace_type,
                "body": pace,
                "tone": "neutral",
            },
            {
                "label": "몰입 방향",
                "value": focus_type,
                "body": focus,
                "tone": "strong",
            },
        ],
        "temperament": {
            "basic": basic_temperament,
            "strength": strength,
            "caution": caution,
        },
    }


def _source_reading_domain(section: dict[str, Any]) -> str:
    domain = _domain_key(section)
    section_id = str(section.get("section_id") or "")
    domain_label = str(section.get("domain_label") or section.get("heading") or "")
    if domain == "money":
        return "money"
    if domain == "career":
        return "career"
    if domain in {"love", "marriage"} or "연애" in domain_label or "결혼" in domain_label:
        return "love_marriage"
    if domain == "personality":
        return "summary"
    if "social" in section_id or "대인" in domain_label:
        return "social"
    return ""


def _source_reading_points(
    source_profile: dict[str, Any] | None,
    domain: str,
    limit: int = 4,
) -> list[dict[str, Any]]:
    if not isinstance(source_profile, dict) or not domain:
        return []
    if domain == "summary":
        raw_points = source_profile.get("summary_points")
    else:
        domain_points = source_profile.get("domain_points")
        raw_points = domain_points.get(domain) if isinstance(domain_points, dict) else []
    if not isinstance(raw_points, list):
        return []
    points: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for point in raw_points:
        if not isinstance(point, dict):
            continue
        label = str(point.get("label") or "").strip()
        text = str(point.get("text") or "").strip()
        if not label or not text:
            continue
        key = (label, text)
        if key in seen:
            continue
        seen.add(key)
        points.append(dict(point))
        if len(points) >= limit:
            break
    return points


def _source_reading_block_title(domain: str) -> str:
    return {
        "money": "재물 추가 내용",
        "career": "직업 추가 내용",
        "love_marriage": "관계 추가 내용",
        "social": "대인관계 추가 내용",
        "summary": "성격 추가 내용",
    }.get(domain, "추가 내용")


SOURCE_READING_COPY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("돈을 만든다.", "수입을 만들어내는 능력이 분명합니다."),
    ("안정적인 돈을 번다.", "안정적인 수입을 만들기 쉽습니다."),
    ("공부만 길어진다.", "학습과 준비가 길어질 수 있습니다."),
    ("돈이 오래 묶인다.", "자금 회수가 늦어질 수 있습니다."),
    ("겉만 커집니다.", "겉으로 보이는 규모만 불어날 수 있습니다."),
    ("높은 값을 받는다.", "높은 단가를 받기 쉽습니다."),
    ("돈이 " + "새기 쉽습니다.", "지출 부담이 붙기 쉽습니다."),
    ("돈이 많이 들어간다.", "지출 비중이 커질 수 있습니다."),
    (
        "신뢰와 생활 능력을 " + "중요" + "하게 보고 연애를 결혼과 현실 문제로 " + "연결" + "해 봅니다.",
        "신뢰와 생활 능력이 확인되어야 관계가 깊어집니다. 연애도 결혼과 현실 문제로 빠르게 이어지는 편입니다.",
    ),
    (
        "신뢰와 생활 능력을 " + "중요" + "하게 보고 연애를 결혼과 현실 문제로 " + "연결" + "해 봅니다",
        "신뢰와 생활 능력이 확인되어야 관계가 깊어집니다. 연애도 결혼과 현실 문제로 빠르게 이어지는 편입니다",
    ),
    ("연애를 결혼과 현실 문제로 " + "연결" + "해 봅니다.", "연애는 현실 조건과 만날 때 결론이 분명해집니다."),
    ("연애를 결혼과 현실 문제로 " + "연결" + "해 봅니다", "연애는 현실 조건과 만날 때 결론이 분명해집니다"),
)


def _polish_source_reading_text(text: str) -> str:
    value = str(text or "").strip()
    for before, after in SOURCE_READING_COPY_REPLACEMENTS:
        value = value.replace(before, after)
    return value


def _source_reading_point_sentence(point: dict[str, Any]) -> str:
    label = str(point.get("label") or "").strip()
    text = _polish_source_reading_text(str(point.get("text") or "").strip())
    if not label:
        return text
    return f"{label}: {text}"


def _attach_source_reading_points(
    section: dict[str, Any],
    source_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    domain = _source_reading_domain(section)
    if not domain or domain == "summary":
        return section
    points = _source_reading_points(source_profile, domain, limit=4)
    if not points:
        return section
    section_domain = _domain_key(section)
    if domain == "love_marriage":
        keyword_map = {
            "love": ("연애", "사랑", "애정", "인연", "호감", "관계"),
            "marriage": ("결혼", "혼인", "배우자", "부부", "생활", "가족", "주거"),
        }
        keywords = keyword_map.get(section_domain, ())
        if keywords:
            filtered_points = [
                point
                for point in points
                if any(
                    keyword in f"{point.get('label') or ''} {point.get('text') or ''}"
                    for keyword in keywords
                )
            ]
            if filtered_points:
                points = filtered_points[:4]
            elif section_domain == "marriage":
                return section
    enriched = dict(section)
    enriched["source_reading_points"] = points
    block_points = [_source_reading_point_sentence(point) for point in points]
    if domain == "love_marriage" and section_domain == "marriage":
        block_points = [
            point.replace("사랑 방식:", "결혼 생활:")
            .replace("연애 성향:", "혼인 성향:")
            .replace("애정 방식:", "배우자 관계:")
            .replace("사랑을 자기 방식대로 운영하려는 태도", "부부 생활을 자기 기준으로 끌고 가려는 태도")
            for point in block_points
        ]
    detail_blocks = [dict(block) for block in enriched.get("detail_blocks") or [] if isinstance(block, dict)]
    block_title = _source_reading_block_title(domain)
    if domain == "love_marriage":
        if section_domain == "love":
            block_title = "연애 추가 내용"
        elif section_domain == "marriage":
            block_title = "결혼 추가 내용"
    detail_blocks.append(
        _detail_block(
            block_title,
            block_points[0],
            block_points[1:],
        )
    )
    enriched["detail_blocks"] = detail_blocks
    checkpoints = [str(item) for item in enriched.get("checkpoints") or [] if str(item or "").strip()]
    for point in points[:2]:
        sentence = _source_reading_point_sentence(point)
        if sentence not in checkpoints:
            checkpoints.append(sentence)
    enriched["checkpoints"] = checkpoints
    return enriched


def _love_marriage_risk_block(
    *,
    love_expression: str,
    love_stability: str,
    marriage_stability: str,
    marriage_life: str,
    love_caution: str,
    marriage_caution: str,
) -> tuple[str, str, list[str]]:
    values = {
        "애정 표현": _section_value_strength(love_expression),
        "관계 안정": _section_value_strength(love_stability),
        "결혼 현실화": _section_value_strength(marriage_stability),
        "생활 기준": _section_value_strength(marriage_life),
    }
    weakest = min(values.items(), key=lambda item: (item[1], item[0]))[0]
    caution = love_caution or marriage_caution
    if weakest == "애정 표현":
        return (
            "마음이 늦게 전달되는 자리",
            "마음이 깊어도 표현이 늦으면 상대는 애정보다 불확실함을 먼저 느낍니다.",
            [caution or "좋아하는 마음이 표현으로 드러날 때 관계가 오래 갑니다."],
        )
    if weakest == "관계 안정":
        return (
            "관계가 흔들리는 자리",
            "감정이 깊어진 뒤에는 말투와 반복되는 태도가 관계를 흔듭니다.",
            [caution or "작은 서운함을 오래 묵히면 관계가 차갑게 굳습니다."],
        )
    if weakest == "생활 기준":
        return (
            "생활 기준을 맞춰야 하는 자리",
            "결혼 이야기가 현실로 가까워질수록 생활 기준이 선명하게 떠오릅니다.",
            [caution or "생활 기준이 흐리면 좋은 감정도 반복 갈등으로 바뀝니다."],
        )
    return (
        "약속이 분명해야 하는 자리",
        "연애가 깊어질수록 관계의 이름과 앞으로의 약속이 중요해집니다.",
        [caution or "애매한 관계가 길어지면 좋은 감정도 약해집니다."],
    )


def _checkpoint_by_priority(
    points: list[Any],
    labels: list[str],
    *,
    excluded: set[str] | None = None,
) -> str:
    excluded = excluded or set()
    string_points = [str(point) for point in points if point]
    for label in labels:
        for point in string_points:
            if point in excluded:
                continue
            if point.startswith(f"{label}:"):
                return point
    for point in string_points:
        if point not in excluded and "주의" not in point and "위험" not in point and "리스크" not in point:
            return point
    return ""


def _daeun_label(chart_summary: dict[str, Any]) -> str:
    current = chart_summary.get("currentDaeun") or {}
    age_label = current.get("ageLabel")
    if age_label:
        return f"{age_label} 구간"
    return "현재 대운"


def _next_daeun_label(chart_summary: dict[str, Any]) -> str:
    current_order = chart_summary.get("currentDaeunOrder")
    for row in chart_summary.get("daeunRows", []):
        if current_order and row.get("order") == current_order + 1:
            age_label = row.get("ageLabel")
            return f"{age_label} 구간" if age_label else "다음 구간"
    return "다음 구간"


def _early_life_age_label(chart_summary: dict[str, Any]) -> str:
    rows = list(chart_summary.get("daeunRows", []))
    if len(rows) >= 2:
        start_age = rows[0].get("startAge")
        end_age = rows[1].get("endAge")
        if start_age and end_age:
            return f"{start_age}~{end_age}세"
    if rows:
        return str(rows[0].get("ageLabel") or "초년")
    return "초년"


def _annual_age_labels(chart_summary: dict[str, Any], count: int = 3) -> str:
    labels = [row.get("ageLabel", "") for row in chart_summary.get("annualRows", [])[:count]]
    labels = [label for label in labels if label]
    return ", ".join(labels) if labels else "가까운 몇 해"


def _section_axis_map(section: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    if not section:
        return {}
    axes = section.get("judgment_axes") or []
    if not isinstance(axes, list):
        return {}
    mapped: dict[str, dict[str, str]] = {}
    for axis in axes:
        if not isinstance(axis, dict) or not axis.get("key"):
            continue
        mapped[str(axis["key"])] = {
            "label": str(axis.get("label") or ""),
            "value": str(axis.get("value") or ""),
        }
    return mapped


def _section_axis_value(section: dict[str, Any] | None, key: str, fallback: str = "확인 필요") -> str:
    axis = _section_axis_map(section).get(key)
    if axis and axis.get("value"):
        return axis["value"]
    return fallback


def _section_value_strength(value: str) -> int:
    text = str(value or "").strip()
    match = re.search(r"상위\s*(\d+)%", text)
    if match:
        return max(0, min(100, 105 - int(match.group(1))))
    if "최상위권" in text or "최상위" in text:
        return 95
    if "상위권" in text or "강세" in text or "강함" in text:
        return 85
    if "중상위권" in text or "양호" in text:
        return 74
    if "평균권" in text or text == "보통":
        return 58
    if "보완 필요" in text or "주의 필요" in text or "평균 이하" in text:
        return 45
    if "약세" in text or "낮음" in text:
        return 32
    if "주의" in text:
        return 28
    return 45


TIMING_DOMAIN_LABELS: dict[str, str] = {
    "money": "재물운",
    "career": "직업운",
    "love": "연애운",
    "marriage": "결혼운",
}

TIMING_GOOD_PHRASES: dict[str, str] = {
    "money": "자산 형성",
    "career": "직업 상승",
    "love": "인연 성립",
    "marriage": "혼인 성사",
}

TIMING_CAUTION_PHRASES: dict[str, str] = {
    "money": "금전 손실",
    "career": "권한 불균형",
    "love": "관계 단절",
    "marriage": "가족 개입",
}

TIMING_GOOD_TITLES: dict[str, str] = {
    "money": "재물 확장",
    "career": "직업 성취",
    "love": "인연 진전",
    "marriage": "결혼 결정",
}

TIMING_CAUTION_TITLES: dict[str, str] = {
    "money": "금전 분쟁",
    "career": "직업 부담",
    "love": "관계 이탈",
    "marriage": "가족·주거 문제",
}

TIMING_GOOD_FOCUS_LINES: dict[str, str] = {
    "money": "자산 형성",
    "career": "직업 상승",
    "love": "관계 확정",
    "marriage": "혼인 성사",
}

TIMING_CAUTION_FOCUS_LINES: dict[str, str] = {
    "money": "금전 손실",
    "career": "권한 불균형",
    "love": "관계 단절",
    "marriage": "가족 개입",
}

TIMING_GOOD_DECISION_LINES: dict[str, str] = {
    "money": "수입과 자산 규모가 확대되는 연도",
    "career": "직책과 평가가 분명해지는 연도",
    "love": "인연이 실제 관계로 이어지는 연도",
    "marriage": "결혼과 주거 결정이 분명해지는 연도",
}

TIMING_CAUTION_DECISION_LINES: dict[str, str] = {
    "money": "보증과 대여에서 손해가 드러나는 연도",
    "career": "책임과 결정권의 불균형이 드러나는 연도",
    "love": "관계 오해가 번지는 연도",
    "marriage": "가족과 주거 부담이 올라오는 연도",
}

TIMING_GOOD_PRODUCT_LINES: dict[str, str] = {
    "money": "수입이 현금성 자산, 소유권, 지분처럼 남는 재산으로 굳어집니다.",
    "career": "직업적 평가가 올라가고 맡는 역할의 격이 달라집니다.",
    "love": "애매하던 인연이 분명한 관계로 정리됩니다.",
    "marriage": "결혼 약속과 생활 기반이 현실 문제로 올라옵니다.",
}

TIMING_CAUTION_PRODUCT_LINES: dict[str, str] = {
    "money": "보증, 대여, 계약 취소가 실제 손실로 남기 쉽습니다.",
    "career": "책임과 권한의 불균형이 경력 부담으로 남기 쉽습니다.",
    "love": "표현과 연락의 차이가 관계 정리로 이어지기 쉽습니다.",
    "marriage": "가족 개입과 주거 비용이 결혼 결정을 흔들기 쉽습니다.",
}

TIMING_GOOD_CARD_CLAUSES: dict[str, str] = {
    "자산 형성": "자산이 형성됩니다",
    "자산 확보": "자산을 확보합니다",
    "거래 확장": "거래 단위가 달라집니다",
    "수입 강세": "수입이 강해집니다",
    "수입 확장": "수입원이 넓어집니다",
    "수익 회수": "수익 회수가 분명해집니다",
    "성과 보상": "성과에 대한 보상을 받습니다",
    "직업 상승": "직업적 위치가 올라갑니다",
    "직책·권한 상승": "직책과 권한이 함께 올라갑니다",
    "결정권 확보": "결정권을 확보합니다",
    "직책 확보": "직책과 권한을 확보합니다",
    "평가 상승": "평가가 올라갑니다",
    "인연 성립": "인연이 성립됩니다",
    "관계 확정": "관계가 확정됩니다",
    "관계 공식화": "관계가 공식화됩니다",
    "인연 진전": "인연이 실제 관계로 넘어갑니다",
    "혼인 성사": "혼인이 성사됩니다",
    "혼인 논의": "혼인 논의가 구체화됩니다",
    "혼담 확정": "혼담이 확정됩니다",
    "결혼 결정": "결혼 결정이 분명해집니다",
}

TIMING_CAUTION_CARD_CLAUSES: dict[str, str] = {
    "금전 손실": "금전 손실이 드러납니다",
    "보증·채무 손실": "보증과 채무 손실이 남습니다",
    "보증 손실": "보증 손실이 남습니다",
    "계약 손실": "계약 손실이 남습니다",
    "공동자금 손실": "공동자금 손실이 드러납니다",
    "문서 손상": "문서 문제가 손실로 이어집니다",
    "권한 불균형": "책임과 권한의 불균형이 드러납니다",
    "책임 전가": "책임 소재가 문제로 올라옵니다",
    "평판 손상": "평판 손상이 드러납니다",
    "평판 검증": "평판을 검증받습니다",
    "책임 과중": "책임이 과중해집니다",
    "관계 단절": "관계 단절이 드러납니다",
    "감정 오해": "감정 오해가 번집니다",
    "관계 소원": "관계가 멀어집니다",
    "가족 개입": "가족 문제가 결정을 흔듭니다",
    "가족 간섭": "가족 간섭이 결정을 흔듭니다",
    "가정 비용 부담": "가정 비용 부담이 올라옵니다",
    "주거 부담": "주거 부담이 올라옵니다",
    "혼인 지연": "혼인 결정이 늦어집니다",
    "결혼 준비 지연": "결혼 준비가 지연됩니다",
    "가족 책임 증가": "가족 책임이 늘어납니다",
}


TIMING_GOOD_VARIANTS: dict[str, dict[str, dict[str, str]]] = {
    "money": {
        "asset_acquisition": {
            "title": "자산 형성",
            "phrase": "자산 형성",
            "focusLine": "자산 형성",
            "decisionLine": "수입이 소유 자산으로 굳어지는 연도",
            "productLine": "수입이 현금성 자산, 소유권, 지분처럼 남는 재산으로 굳어집니다.",
        },
        "deal_expansion": {
            "title": "거래 확장",
            "phrase": "거래 확장",
            "focusLine": "거래 확장",
            "decisionLine": "거래 단위와 매출처가 달라지는 해",
            "productLine": "거래 단위가 달라지고 돈이 오가는 상대가 넓어집니다.",
        },
        "income_power": {
            "title": "수입 강세",
            "phrase": "수입 강세",
            "focusLine": "수입 강세",
            "decisionLine": "직접 수입이 선명하게 올라오는 연도",
            "productLine": "직접 수입이 올라오고 성과에 대한 금액이 분명해집니다.",
        },
    },
    "career": {
        "recognition": {
            "title": "평가 상승",
            "phrase": "평가 상승",
            "focusLine": "평가 상승",
            "decisionLine": "직업적 평가가 분명하게 올라오는 연도",
            "productLine": "평가가 직함, 보상, 공식 역할로 이어집니다.",
        },
        "role_transition": {
            "title": "직업 전환",
            "phrase": "직업 전환",
            "focusLine": "직업 전환",
            "decisionLine": "직업 방향이 바뀌거나 새 역할이 확정되는 연도",
            "productLine": "이직, 보직 변경, 새 역할처럼 직업 방향이 분명하게 바뀝니다.",
        },
        "authority_expansion": {
            "title": "직책·권한 상승",
            "phrase": "직책·권한 상승",
            "focusLine": "직책·권한 상승",
            "decisionLine": "직책과 결정권이 함께 올라가는 연도",
            "productLine": "직업적 평가가 올라가고 맡는 역할의 격이 달라집니다.",
        },
    },
    "love": {
        "new_connection": {
            "title": "인연 성립",
            "phrase": "인연 성립",
            "focusLine": "인연 성립",
            "decisionLine": "새로운 인연이 실제 만남으로 이어지는 연도",
            "productLine": "소개와 만남이 늘고, 호감이 실제 약속으로 이어집니다.",
        },
        "relationship_formalization": {
            "title": "관계 공식화",
            "phrase": "고백·공개 연애·관계 확정",
            "focusLine": "고백·공개·확정",
            "decisionLine": "애매한 관계가 분명한 관계로 넘어가는 해",
            "productLine": "애매하던 관계가 공개된 약속으로 정리됩니다.",
        },
        "strong_match": {
            "title": "강한 인연",
            "phrase": "강한 인연",
            "focusLine": "강한 인연",
            "decisionLine": "서로의 마음이 빠르게 확인되는 연도",
            "productLine": "호감이 빠르게 확인되고 관계의 속도가 붙습니다.",
        },
    },
    "marriage": {
        "marriage_decision": {
            "title": "혼인 성사",
            "phrase": "혼인 성사",
            "focusLine": "혼인 성사",
            "decisionLine": "결혼 약속과 일정이 잡히는 연도",
            "productLine": "결혼 약속, 일정, 양가 협의가 구체화됩니다.",
        },
        "housing_family_base": {
            "title": "생활 기반",
            "phrase": "주거 안정",
            "focusLine": "주거 안정",
            "decisionLine": "결혼 이후의 생활 기반이 안정되는 연도",
            "productLine": "주거 기준과 생활 기반이 안정권에 들어옵니다.",
        },
        "family_stability": {
            "title": "가정 안정",
            "phrase": "가정 안정",
            "focusLine": "가정 안정",
            "decisionLine": "가족과 생활 기반이 안정되는 연도",
            "productLine": "가족 합의와 주거 기준이 정리됩니다.",
        },
    },
}


TIMING_CAUTION_VARIANTS: dict[str, dict[str, dict[str, str]]] = {
    "money": {
        "financial_liability": {
            "title": "보증·채무 손실",
            "phrase": "보증·채무 손실",
            "focusLine": "보증·채무 손실",
            "decisionLine": "타인의 금전 책임이 내 손실로 넘어오는 연도",
            "productLine": "보증, 대여, 대신 책임지는 돈에서 손실이 생깁니다.",
        },
        "contract_loss": {
            "title": "계약 손실",
            "phrase": "계약 손실",
            "focusLine": "계약 손실",
            "decisionLine": "계약과 정산에서 손실이 드러나는 연도",
            "productLine": "계약 취소, 정산 지연, 문서 누락이 금전 손실로 이어집니다.",
        },
        "shared_money": {
            "title": "공동자금 손실",
            "phrase": "공동자금 손실",
            "focusLine": "공동자금 손실",
            "decisionLine": "가까운 사람과 나눈 돈에서 내 몫이 줄어드는 연도",
            "productLine": "가까운 사람과 나눈 돈에서 명의와 지분 문제가 올라옵니다.",
        },
    },
    "career": {
        "authority_gap": {
            "title": "권한 불균형",
            "phrase": "권한 불균형",
            "focusLine": "권한 불균형",
            "decisionLine": "책임은 늘고 결정권은 약해지는 연도",
            "productLine": "책임과 권한의 불균형이 경력 부담으로 남기 쉽습니다.",
        },
        "reputation_test": {
            "title": "평판 손상",
            "phrase": "평판 손상",
            "focusLine": "평판 손상",
            "decisionLine": "성과와 평판이 손상되기 쉬운 연도",
            "productLine": "성과보다 기록과 말이 문제로 남으면 평판이 깎입니다.",
        },
        "role_overload": {
            "title": "책임 과중",
            "phrase": "책임 과중",
            "focusLine": "책임 과중",
            "decisionLine": "감당해야 할 업무가 한꺼번에 몰리는 연도",
            "productLine": "맡는 일이 한꺼번에 몰립니다. 처리 범위를 넘기면 체력과 평판이 함께 흔들립니다.",
        },
    },
    "love": {
        "misreading": {
            "title": "감정 오해",
            "phrase": "감정 오해",
            "focusLine": "감정 오해",
            "decisionLine": "서로의 마음을 다르게 받아들이기 쉬운 연도",
            "productLine": "표현과 연락의 차이가 오해로 번져 관계가 멀어집니다.",
        },
        "separation": {
            "title": "관계 단절",
            "phrase": "관계 단절",
            "focusLine": "관계 단절",
            "decisionLine": "관계가 멀어지거나 정리되기 쉬운 연도",
            "productLine": "거리감이 생기고 관계 정리가 현실 문제가 됩니다.",
        },
        "contact_cooling": {
            "title": "관계 소원",
            "phrase": "관계 소원",
            "focusLine": "관계 소원",
            "decisionLine": "연락과 만남이 눈에 띄게 줄어드는 연도",
            "productLine": "연락과 만남이 줄며 마음도 식습니다.",
        },
    },
    "marriage": {
        "household_cost": {
            "title": "가정 비용 부담",
            "phrase": "가정 비용 부담",
            "focusLine": "가정 비용 부담",
            "decisionLine": "결혼과 가정 비용이 크게 들어오는 연도",
            "productLine": "주거비와 가족 비용이 결혼 생활의 부담으로 올라옵니다.",
        },
        "family_interference": {
            "title": "가족 개입",
            "phrase": "가족 개입",
            "focusLine": "가족 개입",
            "decisionLine": "가족 문제로 결혼 결정이 흔들리기 쉬운 연도",
            "productLine": "양가 의견이 강해져 결혼 결정의 주도권이 흔들립니다.",
        },
        "decision_delay": {
            "title": "혼인 지연",
            "phrase": "혼인 지연",
            "focusLine": "혼인 지연",
            "decisionLine": "결혼 약속과 일정이 늦어지기 쉬운 연도",
            "productLine": "결혼 약속과 일정이 늦어지고 관계의 피로가 남습니다.",
        },
        "family_burden": {
            "title": "가족 책임 증가",
            "phrase": "가족 책임 증가",
            "focusLine": "가족 책임 증가",
            "decisionLine": "가족과 주거 책임이 늘어나는 연도",
            "productLine": "가족 책임과 주거 비용이 한꺼번에 들어옵니다.",
        },
    },
}


def _number_value(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _section_strength_by_domain(sections: list[dict[str, Any]]) -> dict[str, int]:
    return {
        domain: _section_strength(_section_by_domain(sections, domain))
        for domain in TIMING_DOMAIN_LABELS
    }


def _annual_domain_scores(row: dict[str, Any], domain: str) -> dict[str, Any]:
    domain_scores = row.get("domainScores") or {}
    scores = domain_scores.get(domain) or {}
    return scores if isinstance(scores, dict) else {}


def _year_good_score(row: dict[str, Any], domain: str, base_strength: int) -> float:
    scores = _annual_domain_scores(row, domain)
    opportunity = _number_value(scores.get("opportunity"))
    probability = _number_value(scores.get("probability"))
    change = _number_value(scores.get("change"))
    risk = _number_value(scores.get("risk"))
    return opportunity * 0.42 + probability * 0.34 + change * 0.08 + base_strength * 0.18 - risk * 0.22


def _year_caution_score(row: dict[str, Any], domain: str, base_strength: int) -> float:
    scores = _annual_domain_scores(row, domain)
    opportunity = _number_value(scores.get("opportunity"))
    probability = _number_value(scores.get("probability"))
    change = _number_value(scores.get("change"))
    risk = _number_value(scores.get("risk"))
    return risk * 0.58 + change * 0.16 + max(0, base_strength - 68) * 0.08 - opportunity * 0.13 - probability * 0.06


def _timing_score_parts(row: dict[str, Any], domain: str) -> dict[str, float]:
    scores = _annual_domain_scores(row, domain)
    return {
        "opportunity": _number_value(scores.get("opportunity")),
        "probability": _number_value(scores.get("probability")),
        "change": _number_value(scores.get("change")),
        "risk": _number_value(scores.get("risk")),
    }


TIMING_RELATION_LABELS = {
    "six_combine": "지지 합",
    "three_harmony": "삼합",
    "three_harmony_half": "반합",
    "three_meeting": "방합",
    "clash": "충",
    "punishment": "형",
    "self_punishment": "자형",
    "harm": "해",
    "break": "파",
}


def _timing_activation_keywords(row: dict[str, Any], kind: str = "") -> list[str]:
    context = row.get("activationContext") if isinstance(row.get("activationContext"), dict) else {}
    keywords: list[str] = []
    if row.get("daeunPillar"):
        keywords.append("대운 배경")
    if int(context.get("useful_hit_count") or 0):
        keywords.append("필요 오행 발동")
    if int(context.get("caution_hit_count") or 0):
        keywords.append("부담 오행 발동")
    if int(context.get("phase_hit_count") or 0):
        keywords.append("월령 지장간 발동")
    relation_hits = context.get("relation_hits") if isinstance(context.get("relation_hits"), list) else []
    relation_labels = [
        TIMING_RELATION_LABELS.get(str(item.get("relation_type") or ""), "")
        for item in relation_hits
        if isinstance(item, dict)
    ]
    relation_labels = [label for label in relation_labels if label]
    if relation_labels:
        keywords.extend(list(dict.fromkeys(relation_labels))[:2])
    if kind == "good" and "부담 오행 발동" in keywords and "필요 오행 발동" in keywords:
        keywords.append("길흉 동시 발동")
    return list(dict.fromkeys(keywords))[:5]


def _timing_activation_label(row: dict[str, Any], kind: str = "") -> str:
    keywords = _timing_activation_keywords(row, kind)
    if not keywords:
        return ""
    if "길흉 동시 발동" in keywords:
        return "필요한 작용과 부담 작용이 함께 드러나는 연도"
    if "부담 오행 발동" in keywords and kind != "good":
        return "부담 작용이 현실 사건으로 올라오는 연도"
    if "필요 오행 발동" in keywords:
        return "원국에 필요한 작용이 살아나는 연도"
    if "월령 지장간 발동" in keywords:
        return "월령의 숨은 글자가 사건으로 드러나는 연도"
    if any(keyword in keywords for keyword in ("충", "형", "해", "파", "자형")):
        return "지지의 충돌이 사건을 움직이는 연도"
    if row.get("daeunPillar"):
        return "대운 배경 위에서 세운 사건이 드러나는 연도"
    return ""


def _timing_age_from_row(row: dict[str, Any]) -> int | None:
    age_label = str(row.get("ageLabel") or "")
    match = re.search(r"(\d+)세", age_label)
    return int(match.group(1)) if match else None


def _timing_variant_key(row: dict[str, Any], domain: str, kind: str) -> str:
    parts = _timing_score_parts(row, domain)
    opportunity = parts["opportunity"]
    probability = parts["probability"]
    change = parts["change"]
    risk = parts["risk"]
    age = _timing_age_from_row(row)

    if kind == "good":
        if domain == "money":
            if opportunity >= 86 and probability >= 80:
                return "asset_acquisition"
            if change >= 60 and change >= probability - 18:
                return "deal_expansion"
            return "income_power"
        if domain == "career":
            if change >= 58:
                return "role_transition"
            if opportunity >= 86:
                return "authority_expansion"
            return "recognition"
        if domain == "love":
            if change >= 50:
                return "relationship_formalization"
            if probability >= 76:
                return "strong_match"
            return "new_connection"
        if domain == "marriage":
            if age and age >= 50:
                return "family_stability"
            if change >= 50:
                return "marriage_decision"
            return "housing_family_base"

    if domain == "money":
        if risk >= 70 and change >= 55:
            return "contract_loss"
        if risk >= 66:
            return "financial_liability"
        return "shared_money"
    if domain == "career":
        if risk >= 74 and change >= 55:
            return "authority_gap"
        if risk >= 74:
            return "reputation_test"
        return "role_overload"
    if domain == "love":
        if risk >= 66 and change >= 45:
            return "separation"
        if risk >= 60:
            return "misreading"
        return "contact_cooling"
    if domain == "marriage":
        if age and age >= 50:
            return "family_burden"
        if risk >= 66 and change >= 45:
            return "household_cost"
        if risk >= 60:
            return "family_interference"
        return "decision_delay"
    return ""


def _timing_variant_data(domain: str, kind: str, variant: str) -> dict[str, str]:
    table = TIMING_GOOD_VARIANTS if kind == "good" else TIMING_CAUTION_VARIANTS
    return table.get(domain, {}).get(variant, {})


def _timing_source_path(row: dict[str, Any], domain: str, kind: str) -> str:
    keywords = _timing_activation_keywords(row, kind)
    compact_keywords = [
        keyword
        for keyword in keywords
        if keyword not in {"대운 배경", "길흉 동시 발동"}
    ][:2]
    daeun = str(row.get("daeunPillar") or "").strip()
    year_pillar = str(row.get("pillar") or "").strip()
    daeun_ten = "·".join(
        part
        for part in (
            _ten_god_label(row.get("daeunStemTenGod")),
            _ten_god_label(row.get("daeunBranchTenGod")),
        )
        if part
    )
    year_ten = "·".join(
        part
        for part in (
            _ten_god_label(row.get("stemTenGod")),
            _ten_god_label(row.get("branchTenGod")),
        )
        if part
    )
    domain_label = TIMING_DOMAIN_LABELS.get(domain, "운세")
    keyword_text = " · ".join(compact_keywords)
    if daeun and year_pillar and keyword_text:
        daeun_label = f"{daeun}대운"
        if daeun_ten:
            daeun_label = f"{daeun_label}({daeun_ten})"
        year_label = f"{year_pillar}세운"
        if year_ten:
            year_label = f"{year_label}({year_ten})"
        return f"{daeun_label} 위에 {year_label}이 붙어 {domain_label}의 {keyword_text}을 드러냅니다."
    if daeun and year_pillar:
        return f"{daeun}대운의 배경에서 {year_pillar}세운이 {domain_label} 사건을 표면화합니다."
    if keyword_text:
        return f"원국 안의 {keyword_text}이 {domain_label} 사건으로 드러납니다."
    return ""


def _year_candidate(
    row: dict[str, Any],
    domain: str,
    score: float,
    *,
    kind: str,
) -> dict[str, Any]:
    variant = _timing_variant_key(row, domain, kind)
    variant_data = _timing_variant_data(domain, kind, variant)
    return {
        "year": int(row.get("year") or 0),
        "domain": domain,
        "domainLabel": TIMING_DOMAIN_LABELS.get(domain, "운세"),
        "score": round(score, 2),
        "scoreParts": _timing_score_parts(row, domain),
        "variant": variant,
        "phrase": variant_data.get("phrase") or (TIMING_GOOD_PHRASES[domain] if kind == "good" else TIMING_CAUTION_PHRASES[domain]),
        "focusLine": variant_data.get("focusLine", ""),
        "decisionLine": variant_data.get("decisionLine", ""),
        "productLine": variant_data.get("productLine", ""),
        "kind": kind,
        "title": variant_data.get("title") or (TIMING_GOOD_TITLES[domain] if kind == "good" else TIMING_CAUTION_TITLES[domain]),
        "activationContext": row.get("activationContext") if isinstance(row.get("activationContext"), dict) else {},
        "activationLabel": _timing_activation_label(row, kind),
        "structureKeywords": _timing_activation_keywords(row, kind),
        "sourcePath": _timing_source_path(row, domain, kind),
        "daeunPillar": str(row.get("daeunPillar") or ""),
        "daeunStemTenGod": str(row.get("daeunStemTenGod") or ""),
        "daeunBranchTenGod": str(row.get("daeunBranchTenGod") or ""),
        "yearPillar": str(row.get("pillar") or ""),
        "yearStemTenGod": str(row.get("stemTenGod") or ""),
        "yearBranchTenGod": str(row.get("branchTenGod") or ""),
    }


def _select_year_candidates(
    rows: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    strengths = _section_strength_by_domain(sections)
    good_candidates: list[dict[str, Any]] = []
    caution_candidates: list[dict[str, Any]] = []
    for row in rows:
        if not row.get("year"):
            continue
        good_ranked: list[tuple[float, str]] = []
        caution_ranked: list[tuple[float, str]] = []
        for domain in TIMING_DOMAIN_LABELS:
            base_strength = strengths.get(domain, 0)
            good_ranked.append((_year_good_score(row, domain, base_strength), domain))
            caution_ranked.append((_year_caution_score(row, domain, base_strength), domain))
        good_score, good_domain = max(good_ranked, key=lambda item: item[0])
        caution_score, caution_domain = max(caution_ranked, key=lambda item: item[0])
        good_candidates.append(_year_candidate(row, good_domain, good_score, kind="good"))
        caution_candidates.append(_year_candidate(row, caution_domain, caution_score, kind="caution"))

    selected_good = _select_bucketed_years(good_candidates, limit=limit)
    selected_good_years = {int(candidate["year"]) for candidate in selected_good}
    selected_caution = _select_bucketed_years(
        caution_candidates,
        limit=limit,
        excluded_years=selected_good_years,
    )
    return selected_good, selected_caution


def _select_domain_year_candidates(
    rows: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> dict[str, dict[str, Any | None]]:
    strengths = _section_strength_by_domain(sections)
    output: dict[str, dict[str, Any | None]] = {}
    for domain, label in TIMING_DOMAIN_LABELS.items():
        good_candidates: list[dict[str, Any]] = []
        caution_candidates: list[dict[str, Any]] = []
        base_strength = strengths.get(domain, 0)
        for row in rows:
            if not row.get("year"):
                continue
            good_candidates.append(
                _year_candidate(
                    row,
                    domain,
                    _year_good_score(row, domain, base_strength),
                    kind="good",
                )
            )
            caution_candidates.append(
                _year_candidate(
                    row,
                    domain,
                    _year_caution_score(row, domain, base_strength),
                    kind="caution",
                )
            )
        good = max(
            good_candidates,
            key=lambda item: (float(item.get("score") or 0), -int(item.get("year") or 0)),
            default=None,
        )
        excluded_year = int(good.get("year") or 0) if good else 0
        caution_pool = [
            candidate
            for candidate in caution_candidates
            if int(candidate.get("year") or 0) != excluded_year
        ] or caution_candidates
        caution = max(
            caution_pool,
            key=lambda item: (float(item.get("score") or 0), -int(item.get("year") or 0)),
            default=None,
        )
        output[domain] = {
            "domain": domain,
            "domainLabel": label,
            "good": good,
            "caution": caution,
        }
    return output


def _select_bucketed_years(
    candidates: list[dict[str, Any]],
    *,
    limit: int,
    excluded_years: set[int] | None = None,
) -> list[dict[str, Any]]:
    excluded_years = excluded_years or set()
    usable = [candidate for candidate in candidates if int(candidate.get("year") or 0) not in excluded_years]
    if not usable:
        return []
    start_year = min(int(candidate["year"]) for candidate in usable)
    buckets: dict[int, list[dict[str, Any]]] = {}
    for candidate in usable:
        year = int(candidate["year"])
        bucket = max(0, (year - start_year) // 10)
        buckets.setdefault(bucket, []).append(candidate)

    selected: list[dict[str, Any]] = []
    for bucket in sorted(buckets):
        ranked = sorted(buckets[bucket], key=lambda item: (-item["score"], item["year"]))
        if ranked:
            selected.append(ranked[0])
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        selected_years = {int(candidate["year"]) for candidate in selected}
        for candidate in sorted(usable, key=lambda item: (-item["score"], item["year"])):
            year = int(candidate["year"])
            if year in selected_years:
                continue
            selected.append(candidate)
            selected_years.add(year)
            if len(selected) >= limit:
                break
    selected = _diversify_timing_topics(selected, usable, limit=limit)
    selected = _diversify_timing_domains(selected, usable, limit=limit)
    selected = _ensure_timing_money_event(selected, usable, limit=limit)
    selected.sort(key=lambda item: int(item["year"]))
    return selected


def _ensure_timing_money_event(
    selected: list[dict[str, Any]],
    usable: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    if not selected or any(candidate.get("domain") == "money" for candidate in selected):
        return selected
    money_candidates = [
        candidate
        for candidate in usable
        if candidate.get("domain") == "money" and candidate.get("kind") == "good"
    ]
    if not money_candidates:
        return selected
    money_candidate = max(
        money_candidates,
        key=lambda item: (
            item.get("variant") == "asset_acquisition",
            float(item.get("score") or 0),
            -int(item.get("year") or 0),
        ),
    )
    weakest_index = min(
        range(len(selected)),
        key=lambda index: (float(selected[index].get("score") or 0), -int(selected[index].get("year") or 0)),
    )
    weakest_score = float(selected[weakest_index].get("score") or 0)
    if float(money_candidate.get("score") or 0) < weakest_score - 18:
        return selected
    selected = list(selected[:limit])
    selected[weakest_index] = money_candidate
    return selected


def _timing_topic_key(candidate: dict[str, Any]) -> str:
    return f"{candidate.get('domain', '')}:{candidate.get('variant') or candidate.get('title') or ''}"


def _diversify_timing_domains(
    selected: list[dict[str, Any]],
    usable: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    if len(selected) < 2:
        return selected
    selected_domains = {str(item.get("domain") or "") for item in selected if item.get("domain")}
    available_domains = {str(item.get("domain") or "") for item in usable if item.get("domain")}
    desired_domain_count = min(limit, len(selected), len(available_domains))
    if len(selected_domains) >= desired_domain_count:
        return selected

    selected_years = {int(item.get("year") or 0) for item in selected}
    ranked = sorted(usable, key=lambda item: (-float(item.get("score") or 0), int(item.get("year") or 0)))
    while len(selected_domains) < desired_domain_count:
        repeated_domains = {
            domain
            for domain in selected_domains
            if sum(1 for item in selected if str(item.get("domain") or "") == domain) > 1
        }
        replacement_made = False
        for candidate in ranked:
            year = int(candidate.get("year") or 0)
            domain = str(candidate.get("domain") or "")
            if not year or year in selected_years or not domain or domain in selected_domains:
                continue
            replace_indexes = [
                index
                for index, item in enumerate(selected)
                if str(item.get("domain") or "") in repeated_domains
            ]
            if not replace_indexes:
                replace_indexes = list(range(len(selected)))
            weakest_index = min(
                replace_indexes,
                key=lambda index: (float(selected[index].get("score") or 0), -int(selected[index].get("year") or 0)),
            )
            weakest_score = float(selected[weakest_index].get("score") or 0)
            if float(candidate.get("score") or 0) < weakest_score - 18:
                continue
            removed = selected[weakest_index]
            selected_years.discard(int(removed.get("year") or 0))
            selected[weakest_index] = candidate
            selected_years.add(year)
            selected_domains = {str(item.get("domain") or "") for item in selected if item.get("domain")}
            replacement_made = True
            break
        if not replacement_made:
            break
    return selected


def _diversify_timing_topics(
    selected: list[dict[str, Any]],
    usable: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    if len(selected) < 2:
        return selected
    topic_keys = {_timing_topic_key(candidate) for candidate in selected}
    available_topic_count = len({_timing_topic_key(candidate) for candidate in usable})
    desired_topic_count = min(limit, len(selected), available_topic_count)
    if len(topic_keys) >= desired_topic_count:
        return selected

    selected_years = {int(candidate.get("year") or 0) for candidate in selected}
    selected_topics = {_timing_topic_key(candidate) for candidate in selected}
    ranked = sorted(usable, key=lambda item: (-float(item.get("score") or 0), int(item.get("year") or 0)))

    while len(selected_topics) < desired_topic_count:
        replacement_made = False
        duplicate_topics = {
            topic
            for topic in selected_topics
            if sum(1 for item in selected if _timing_topic_key(item) == topic) > 1
        }
        for candidate in ranked:
            year = int(candidate.get("year") or 0)
            topic = _timing_topic_key(candidate)
            if not year or year in selected_years or topic in selected_topics:
                continue
            duplicate_indexes = [
                index
                for index, item in enumerate(selected)
                if _timing_topic_key(item) in duplicate_topics
            ]
            if not duplicate_indexes:
                duplicate_indexes = list(range(len(selected)))
            weakest_index = min(
                duplicate_indexes,
                key=lambda index: (float(selected[index].get("score") or 0), -int(selected[index].get("year") or 0)),
            )
            weakest_score = float(selected[weakest_index].get("score") or 0)
            if float(candidate.get("score") or 0) < weakest_score - 14:
                continue
            removed = selected[weakest_index]
            selected_years.discard(int(removed.get("year") or 0))
            selected[weakest_index] = candidate
            selected_years.add(year)
            selected_topics = {_timing_topic_key(item) for item in selected}
            replacement_made = True
            break
        if not replacement_made:
            break
    return selected


def _age_from_timing_row(row: dict[str, Any], birth_year: int | None) -> int | None:
    age_label = str(row.get("ageLabel") or "")
    match = re.search(r"(\d+)세", age_label)
    if match:
        return int(match.group(1))
    year = int(row.get("year") or 0)
    if year and birth_year:
        return year - birth_year + 1
    return None


def _best_year_candidate_for_rows(
    rows: list[dict[str, Any]],
    strengths: dict[str, int],
    *,
    kind: str,
    excluded_years: set[int] | None = None,
) -> dict[str, Any] | None:
    excluded_years = excluded_years or set()
    ranked: list[dict[str, Any]] = []
    for row in rows:
        year = int(row.get("year") or 0)
        if not year or year in excluded_years:
            continue
        for domain in TIMING_DOMAIN_LABELS:
            base_strength = strengths.get(domain, 0)
            score = (
                _year_good_score(row, domain, base_strength)
                if kind == "good"
                else _year_caution_score(row, domain, base_strength)
            )
            ranked.append(_year_candidate(row, domain, score, kind=kind))
    if not ranked:
        return None
    return max(ranked, key=lambda item: (item["score"], -int(item["year"])))


def _timing_decade_groups(
    rows: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    birth_year: int,
    *,
    current_year: int | None = None,
) -> list[dict[str, Any]]:
    if not rows or not birth_year:
        return []
    strengths = _section_strength_by_domain(sections)
    groups: list[dict[str, Any]] = []
    for start_age in range(20, 80, 10):
        end_age = start_age + 9
        decade_rows = [
            row
            for row in rows
            if (age := _age_from_timing_row(row, birth_year)) is not None and start_age <= age <= end_age
        ]
        if not decade_rows:
            continue
        good = _best_year_candidate_for_rows(decade_rows, strengths, kind="good")
        caution = _best_year_candidate_for_rows(
            decade_rows,
            strengths,
            kind="caution",
            excluded_years={int(good["year"])} if good else set(),
        )
        first_year = min(int(row.get("year") or 0) for row in decade_rows if row.get("year"))
        last_year = max(int(row.get("year") or 0) for row in decade_rows if row.get("year"))
        groups.append(
            {
                "label": f"{start_age}대",
                "ageRange": f"{start_age}~{end_age}세",
                "yearRange": f"{first_year}~{last_year}년",
                "good": _timing_event_payload(good, birth_year, current_year=current_year) if good else None,
                "caution": _timing_event_payload(caution, birth_year, current_year=current_year) if caution else None,
            }
        )
    return groups


def _candidate_years(candidates: list[dict[str, Any]], fallback: str) -> str:
    years = [f"{candidate['year']}년" for candidate in candidates if candidate.get("year")]
    return " · ".join(years) if years else fallback


def _unique_timing_parts(*parts: Any) -> list[str]:
    values: list[str] = []
    for part in parts:
        text = str(part or "").strip().strip(".")
        if not text:
            continue
        if any(text == value or text in value or value in text for value in values):
            continue
        values.append(text)
    return values


def _candidate_title_phrase(candidate: dict[str, Any] | None, fallback: str = "") -> str:
    if not candidate:
        return fallback
    title = str(candidate.get("title") or candidate.get("domainLabel") or "운세").strip()
    phrase = str(candidate.get("phrase") or "").strip()
    parts = _unique_timing_parts(title, phrase)
    return " · ".join(parts) if parts else fallback


def _candidate_detail(candidate: dict[str, Any] | None, fallback: str) -> str:
    if not candidate:
        return fallback
    year = candidate.get("year")
    title_phrase = _candidate_title_phrase(candidate, fallback)
    return f"{year}년 {title_phrase}" if year else title_phrase


def _candidate_list(candidates: list[dict[str, Any]], fallback: str) -> str:
    details = [_candidate_detail(candidate, "") for candidate in candidates]
    details = [detail for detail in details if detail]
    return " / ".join(details) if details else fallback


def _current_year_from_timing_rows(rows: list[dict[str, Any]], chart_summary: dict[str, Any]) -> int:
    for row in chart_summary.get("annualRows") or []:
        if row.get("isCurrent") and row.get("year"):
            return int(row["year"])
    for row in rows:
        if row.get("isCurrent") and row.get("year"):
            return int(row["year"])
    return 2026


def _split_timing_candidates(
    candidates: list[dict[str, Any]],
    current_year: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    past = [candidate for candidate in candidates if int(candidate.get("year") or 0) < current_year]
    future = [candidate for candidate in candidates if int(candidate.get("year") or 0) >= current_year]
    return past, future


def _candidate_age_label(candidate: dict[str, Any], birth_year: int | None) -> str:
    year = int(candidate.get("year") or 0)
    if not year or not birth_year:
        return ""
    return f"{year - birth_year + 1}세"


def _candidate_short_list(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
) -> str:
    details = [
        (
            f"{candidate['year']}년"
            + (f"({_candidate_age_label(candidate, birth_year)})" if _candidate_age_label(candidate, birth_year) else "")
            + f" {_candidate_title_phrase(candidate, '운세')}"
        )
        for candidate in candidates
        if candidate.get("year")
    ]
    return " / ".join(details) if details else fallback


def _candidate_value_list(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
) -> str:
    details = [
        _candidate_event_label(candidate, birth_year=birth_year)
        for candidate in candidates
        if candidate.get("year")
    ]
    return " / ".join(details) if details else fallback


def _candidate_year_age_list(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
) -> str:
    details = [
        " · ".join(
            part
            for part in (
                f"{candidate['year']}년",
                _candidate_age_label(candidate, birth_year),
            )
            if part
        )
        for candidate in candidates
        if candidate.get("year")
    ]
    return " / ".join(details) if details else fallback


def _candidate_event_label(
    candidate: dict[str, Any] | None,
    *,
    birth_year: int | None = None,
) -> str:
    if not candidate or not candidate.get("year"):
        return ""
    year = f"{candidate['year']}년"
    age = _candidate_age_label(candidate, birth_year)
    title = str(candidate.get("title") or candidate.get("domainLabel") or "운세").strip()
    prefix = f"{year}({age})" if age else year
    return " ".join(part for part in (prefix, title) if part)


def _candidate_event_label_list(
    candidates: list[dict[str, Any]],
    fallback: str,
    *,
    birth_year: int | None = None,
    limit: int = 3,
) -> str:
    labels = [
        _candidate_event_label(candidate, birth_year=birth_year)
        for candidate in candidates[:limit]
    ]
    labels = [label for label in labels if label]
    return " / ".join(labels) if labels else fallback


def _candidate_phrase_list(candidates: list[dict[str, Any]], fallback: str) -> str:
    phrases: list[str] = []
    for candidate in candidates:
        phrase = str(candidate.get("phrase") or "").strip()
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return " · ".join(phrases[:3]) if phrases else fallback


def _candidate_phrase_sentence(candidates: list[dict[str, Any]], fallback: str) -> str:
    phrases: list[str] = []
    for candidate in candidates:
        phrase = str(candidate.get("phrase") or "").strip()
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return phrases[0] if phrases else fallback


def _candidate_keyword_list(candidates: list[dict[str, Any]], fallback: str) -> str:
    keywords: list[str] = []
    for candidate in candidates:
        phrase = str(candidate.get("phrase") or "").strip()
        for keyword in re.split(r"[·,/]+", phrase):
            keyword = keyword.strip()
            if keyword and keyword not in keywords:
                keywords.append(keyword)
    if keywords:
        return keywords[0]
    fallback_keywords = [keyword.strip() for keyword in re.split(r"[·,/]+", fallback) if keyword.strip()]
    return fallback_keywords[0] if fallback_keywords else fallback


def _candidate_average_score(candidates: list[dict[str, Any]]) -> int | None:
    scores = [_number_value(candidate.get("score"), -1) for candidate in candidates]
    scores = [score for score in scores if score >= 0]
    if not scores:
        return None
    return int(round(max(28, min(98, sum(scores) / len(scores)))))


def _candidate_domain_summary(candidates: list[dict[str, Any]], fallback: str) -> str:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for candidate in candidates:
        domain = str(candidate.get("domain") or "")
        if not domain:
            continue
        counts[domain] = counts.get(domain, 0) + 1
        labels[domain] = str(candidate.get("domainLabel") or TIMING_DOMAIN_LABELS.get(domain, domain))
    ranked = sorted(counts, key=lambda key: (-counts[key], key))
    return labels[ranked[0]] if ranked else fallback


def _timing_domain_rank_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    scores: dict[str, list[float]] = {}
    for candidate in candidates:
        domain = str(candidate.get("domain") or "")
        if not domain:
            continue
        counts[domain] = counts.get(domain, 0) + 1
        labels[domain] = str(candidate.get("domainLabel") or TIMING_DOMAIN_LABELS.get(domain, domain))
        scores.setdefault(domain, []).append(_number_value(candidate.get("score"), 0))
    ranked = sorted(
        counts,
        key=lambda key: (
            -counts[key],
            -sum(scores.get(key, [])) / max(1, len(scores.get(key, []))),
            labels.get(key, key),
        ),
    )
    return [
        {
            "domain": key,
            "label": labels.get(key, key),
            "count": counts[key],
            "averageScore": round(sum(scores.get(key, [])) / max(1, len(scores.get(key, []))), 1),
        }
        for key in ranked
    ]


def _timing_calendar_profile(
    good_years: list[dict[str, Any]],
    caution_years: list[dict[str, Any]],
    timing_decades: list[dict[str, Any]],
) -> dict[str, Any]:
    good_domains = _timing_domain_rank_items(good_years)
    caution_domains = _timing_domain_rank_items(caution_years)
    decisive_ages = [
        str(group.get("label") or "")
        for group in timing_decades
        if group.get("good") and group.get("caution")
    ]
    return {
        "range": "20세~79세",
        "goodFocus": (good_domains[0]["label"] if good_domains else "좋은 분야"),
        "cautionFocus": (caution_domains[0]["label"] if caution_domains else "주의 분야"),
        "decisiveAgeBands": " · ".join(decisive_ages[:4]) or "주요 연령대",
        "goodDomainItems": good_domains[:3],
        "cautionDomainItems": caution_domains[:3],
        "summary": (
            f"좋은 분야는 {_candidate_domain_summary(good_years, '좋은 분야')}입니다. "
            f"주의 분야는 {_candidate_domain_summary(caution_years, '주의 분야')}입니다. "
            f"확인 구간은 {' · '.join(decisive_ages[:4]) or '20대~70대'}입니다."
        ),
    }


def _timing_topic_item(
    title: str,
    value: str,
    body: str,
    *,
    candidates: list[dict[str, Any]],
    tone: str,
    evidence: str,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "title": title,
        "value": value,
        "body": body,
        "definition": body,
        "tone": tone,
        "evidence": evidence,
    }
    score = _candidate_average_score(candidates)
    if score is not None:
        item["score"] = score
    return item


def _timing_topic_items(
    good_years: list[dict[str, Any]],
    caution_years: list[dict[str, Any]],
    past_good: list[dict[str, Any]],
    past_caution: list[dict[str, Any]],
    *,
    birth_year: int,
) -> list[dict[str, Any]]:
    checked_range = "20세~79세 전체 구간"
    all_candidates = good_years + caution_years
    items = [
        _timing_topic_item(
            "상승 연도",
            _candidate_value_list(good_years, "뚜렷한 연도 없음", birth_year=birth_year),
            _candidate_keyword_list(good_years, "성과 · 계약"),
            candidates=good_years,
            tone="strong",
            evidence=f"{checked_range}에서 계약, 성과, 역할 확대가 가장 뚜렷한 해입니다.",
        ),
        _timing_topic_item(
            "주의 연도",
            _candidate_value_list(caution_years, "뚜렷한 연도 없음", birth_year=birth_year),
            _candidate_keyword_list(caution_years, "책임 · 계약"),
            candidates=caution_years,
            tone="watch",
            evidence=f"{checked_range}에서 책임, 손실, 평판 문제가 크게 드러나는 해입니다.",
        ),
        _timing_topic_item(
            "두드러지는 영역",
            _candidate_domain_summary(all_candidates, "뚜렷한 분야 없음"),
            _candidate_keyword_list(all_candidates, "성과 · 책임 · 계약"),
            candidates=all_candidates,
            tone="strong",
            evidence="실제 사건으로 자주 걸리는 영역입니다.",
        ),
    ]
    past_candidates = past_good + past_caution
    if past_candidates:
        items.append(
            _timing_topic_item(
                "지나온 연도",
                _candidate_value_list(past_candidates, "과거 대조 연도 없음", birth_year=birth_year),
                _candidate_keyword_list(past_candidates, "과거 대조"),
                candidates=past_candidates,
                tone="neutral",
                evidence="지나온 연도와 맞춰보면 이후의 상승 연도와 주의 연도가 더 분명해집니다.",
            )
        )
    return items


def _timing_detail_blocks(
    good_years: list[dict[str, Any]],
    caution_years: list[dict[str, Any]],
    past_good: list[dict[str, Any]],
    past_caution: list[dict[str, Any]],
    *,
    birth_year: int,
) -> list[dict[str, Any]]:
    def bullets(candidates: list[dict[str, Any]], fallback: str) -> list[str]:
        items = [
            " · ".join(
                part
                for part in (
                    f"{candidate.get('year')}년",
                    _candidate_age_label(candidate, birth_year),
                    _timing_event_summary(candidate, int(candidate.get("year") or 0) - birth_year + 1 if birth_year and candidate.get("year") else None),
                )
                if part
            )
            for candidate in candidates[:3]
            if candidate.get("year")
        ]
        return items or [fallback]

    good_values = _candidate_event_value_series(good_years, "뚜렷한 연도 없음", birth_year=birth_year)
    caution_values = _candidate_event_value_series(caution_years, "뚜렷한 연도 없음", birth_year=birth_year)
    good_topics = _candidate_topic_series(good_years, "성과, 계약", birth_year=birth_year)
    caution_topics = _candidate_topic_series(caution_years, "책임, 계약", birth_year=birth_year)
    good_body = (
        f"상승 연도에는 {good_topics} 부문에서 실제 성과가 드러납니다. 대표 연도는 {good_values}입니다."
        if good_years
        else "20세~79세 구간에서 특별히 강한 상승 연도는 선명하지 않습니다."
    )
    caution_body = (
        f"주의 연도에는 {caution_topics} 부문에서 손실과 책임 문제가 커집니다. 대표 연도는 {caution_values}입니다."
        if caution_years
        else "20세~79세 구간에서 특별히 강한 주의 연도는 선명하지 않습니다."
    )
    blocks = [
        _detail_block("상승 연도", good_body, bullets(good_years, "성과·계약·평가")),
        _detail_block("주의 연도", caution_body, bullets(caution_years, "손실·책임·관계 부담"), tone="risk"),
    ]
    past_candidates = past_good + past_caution
    if past_candidates:
        past_values = _candidate_event_value_series(past_candidates, "뚜렷한 연도 없음", birth_year=birth_year)
        past_topics = _candidate_topic_series(past_candidates, "주요 사건", birth_year=birth_year)
        past_body = (
            f"지나온 연도에서는 {past_topics} 부문의 사건을 대조해볼 수 있습니다. 해당 연도는 {past_values}입니다."
        )
        blocks.append(_detail_block("지나온 주요 연도", past_body, bullets(past_candidates, "주요 연도")))
    return blocks


def _timing_ranked_candidates(candidates: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda item: (-float(item.get("score") or 0), int(item.get("year") or 0)),
    )[:limit]


def _timing_chronological_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda item: int(item.get("year") or 0))


def _timing_decisive_age_labels(timing_decades: list[dict[str, Any]], *, limit: int = 4) -> str:
    labels = [
        str(group.get("label") or "")
        for group in timing_decades
        if group.get("good") and group.get("caution") and str(group.get("label") or "")
    ]
    return " · ".join(labels[:limit]) or "20대~70대"


def _timing_summary_cards(
    good_years: list[dict[str, Any]],
    caution_years: list[dict[str, Any]],
    timing_decades: list[dict[str, Any]],
    *,
    birth_year: int,
) -> list[dict[str, Any]]:
    return [
        {
            "label": "상승 연도",
            "title": _candidate_domain_summary(good_years, "상승 분야"),
            "value": _candidate_value_list(good_years, "뚜렷한 연도 없음", birth_year=birth_year),
            "keywords": _candidate_keyword_list(good_years, "성과 · 계약"),
            "tone": "good",
        },
        {
            "label": "주의 연도",
            "title": _candidate_domain_summary(caution_years, "주의 분야"),
            "value": _candidate_value_list(caution_years, "뚜렷한 연도 없음", birth_year=birth_year),
            "keywords": _candidate_keyword_list(caution_years, "책임 · 계약"),
            "tone": "risk",
        },
        {
            "label": "확인 구간",
            "title": _timing_decisive_age_labels(timing_decades),
            "value": "20세~79세",
            "keywords": "20대 · 30대 · 40대 · 50대 · 60대 · 70대",
            "tone": "neutral",
        },
    ]


def _timing_map_payload(
    good_years: list[dict[str, Any]],
    caution_years: list[dict[str, Any]],
    timing_decades: list[dict[str, Any]],
    past_good: list[dict[str, Any]],
    past_caution: list[dict[str, Any]],
    future_good: list[dict[str, Any]],
    future_caution: list[dict[str, Any]],
    domain_year_highlights: list[dict[str, Any]] | None = None,
    *,
    birth_year: int,
    current_year: int | None,
) -> dict[str, Any]:
    past_candidates = _timing_ranked_candidates(past_good + past_caution, limit=4)
    future_candidates = _timing_ranked_candidates(future_good + future_caution, limit=4)
    top_good = _timing_ranked_candidates(good_years, limit=1) or good_years[:1]
    top_caution = _timing_ranked_candidates(caution_years, limit=1) or caution_years[:1]
    good_anchor = _candidate_event_label_list(top_good, "확인 필요", birth_year=birth_year, limit=1)
    caution_anchor = _candidate_event_label_list(top_caution, "확인 필요", birth_year=birth_year, limit=1)
    good_domains = _candidate_domain_summary(good_years, "상승 분야")
    caution_domains = _candidate_domain_summary(caution_years, "주의 분야")
    return {
        "rangeLabel": "20세~79세",
        "headline": "상승 연도와 주의 연도",
        "boardLeadShort": "20세~79세 전체 기준입니다.",
        "boardLead": (
            f"상승 연도: {good_anchor}. "
            f"주의 연도: {caution_anchor}."
        ),
        "summaryCards": _timing_summary_cards(
            good_years,
            caution_years,
            timing_decades,
            birth_year=birth_year,
        ),
        "goodHighlights": _timing_event_payloads(
            _timing_ranked_candidates(good_years, limit=3),
            birth_year,
            current_year=current_year,
        ),
        "cautionHighlights": _timing_event_payloads(
            _timing_ranked_candidates(caution_years, limit=3),
            birth_year,
            current_year=current_year,
        ),
        "pastCheck": _timing_event_payloads(
            _timing_chronological_candidates(past_candidates),
            birth_year,
            current_year=current_year,
        ),
        "futureCheck": _timing_event_payloads(
            _timing_chronological_candidates(future_candidates),
            birth_year,
            current_year=current_year,
        ),
        "goodKeywords": _candidate_keyword_list(good_years, "계약 · 성과"),
        "cautionKeywords": _candidate_keyword_list(caution_years, "책임 · 손실"),
        "goodDomains": good_domains,
        "cautionDomains": caution_domains,
        "domainYearHighlights": list(domain_year_highlights or []),
    }


def _birth_year_from_timing_rows(rows: list[dict[str, Any]]) -> int | None:
    for row in rows:
        year = row.get("year")
        age_label = str(row.get("ageLabel") or "")
        match = re.search(r"(\d+)세", age_label)
        if year and match:
            return int(year) - int(match.group(1)) + 1
    return None


def _timing_event_title(candidate: dict[str, Any], age: int | None = None) -> str:
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    explicit = str(candidate.get("title") or "").strip()
    if explicit:
        return explicit
    if domain == "marriage" and age and age >= 50:
        return "가정 안정" if kind == "good" else "가족·주거 부담"
    if kind == "good":
        return TIMING_GOOD_TITLES.get(domain, TIMING_DOMAIN_LABELS.get(domain, "운세 강화"))
    return TIMING_CAUTION_TITLES.get(domain, TIMING_DOMAIN_LABELS.get(domain, "주의"))


def _timing_event_keywords(candidate: dict[str, Any], age: int | None = None) -> str:
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    explicit = str(candidate.get("phrase") or "").strip()
    if explicit:
        return explicit
    if domain == "marriage" and age and age >= 50:
        return "가족 합의·주거 안정" if kind == "good" else "가족 책임·주거 비용"
    return str(candidate.get("phrase") or "").strip()


def _timing_event_focus_line(candidate: dict[str, Any], age: int | None = None) -> str:
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    explicit = str(candidate.get("focusLine") or "").strip()
    if explicit:
        return explicit
    if domain == "marriage" and age and age >= 50:
        return "가족·주거·생활 안정" if kind == "good" else "가족·주거·비용"
    source = TIMING_GOOD_FOCUS_LINES if kind == "good" else TIMING_CAUTION_FOCUS_LINES
    return source.get(domain, "주요 사건")


def _timing_event_decision_line(candidate: dict[str, Any], age: int | None = None) -> str:
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    explicit = str(candidate.get("decisionLine") or "").strip()
    if explicit:
        return explicit
    if domain == "marriage" and age and age >= 50:
        return "가족과 생활 기반이 정리되는 해" if kind == "good" else "가족과 주거 책임이 올라오는 해"
    source = TIMING_GOOD_DECISION_LINES if kind == "good" else TIMING_CAUTION_DECISION_LINES
    return source.get(domain, "중요 사건이 드러나는 해")


def _timing_event_product_line(candidate: dict[str, Any], age: int | None = None) -> str:
    domain = str(candidate.get("domain") or "")
    kind = str(candidate.get("kind") or "")
    explicit = str(candidate.get("productLine") or "").strip()
    if explicit:
        return explicit
    if domain == "marriage" and age and age >= 50:
        return "가족 합의, 주거 안정, 생활 기반이 핵심입니다." if kind == "good" else "가족 책임, 주거 비용, 생활 부담을 조심해야 합니다."
    source = TIMING_GOOD_PRODUCT_LINES if kind == "good" else TIMING_CAUTION_PRODUCT_LINES
    return source.get(domain, "해당 연도의 생활 사건을 표시합니다.")


def _timing_event_summary(candidate: dict[str, Any], age: int | None = None) -> str:
    title = _timing_event_title(candidate, age)
    phrase = _timing_event_keywords(candidate, age)
    return " · ".join(_unique_timing_parts(title, phrase)) or title


def _timing_event_payload(
    candidate: dict[str, Any],
    birth_year: int,
    *,
    current_year: int | None = None,
) -> dict[str, Any]:
    year = int(candidate.get("year") or 0)
    age = year - birth_year + 1 if year and birth_year else None
    is_past = bool(current_year and year and year < current_year)
    return {
        "year": year,
        "age": age,
        "ageLabel": f"{age}세" if age else "",
        "isPast": is_past,
        "periodLabel": "지난 연도" if is_past else "다가올 연도",
        "domain": str(candidate.get("domain") or ""),
        "domainLabel": str(candidate.get("domainLabel") or ""),
        "kind": str(candidate.get("kind") or ""),
        "variant": str(candidate.get("variant") or ""),
        "eventKey": str(candidate.get("eventKey") or candidate.get("variant") or ""),
        "scoreParts": candidate.get("scoreParts") or {},
        "title": _timing_event_title(candidate, age),
        "keywords": _timing_event_keywords(candidate, age),
        "focusLine": _timing_event_focus_line(candidate, age),
        "decisionLine": _timing_event_decision_line(candidate, age),
        "productLine": _timing_event_product_line(candidate, age),
        "activationLabel": str(candidate.get("activationLabel") or ""),
        "sourcePath": str(candidate.get("sourcePath") or ""),
        "structureKeywords": [
            str(item)
            for item in list(candidate.get("structureKeywords") or [])
            if str(item)
        ][:5],
        "daeunPillar": str(candidate.get("daeunPillar") or ""),
        "daeunStemTenGod": str(candidate.get("daeunStemTenGod") or ""),
        "daeunBranchTenGod": str(candidate.get("daeunBranchTenGod") or ""),
        "yearPillar": str(candidate.get("yearPillar") or ""),
        "yearStemTenGod": str(candidate.get("yearStemTenGod") or ""),
        "yearBranchTenGod": str(candidate.get("yearBranchTenGod") or ""),
        "activationContext": candidate.get("activationContext") if isinstance(candidate.get("activationContext"), dict) else {},
        "kindLabel": "상승 연도" if str(candidate.get("kind") or "") == "good" else "주의 연도",
        "keywordItems": [
            item.strip()
            for item in re.split(r"[·,/]+", _timing_event_keywords(candidate, age))
            if item.strip()
        ][:4],
        "summary": _timing_event_summary(candidate, age),
        "score": candidate.get("score"),
    }


def _timing_event_payloads(
    candidates: list[dict[str, Any]],
    birth_year: int,
    *,
    current_year: int | None = None,
) -> list[dict[str, Any]]:
    return [
        _timing_event_payload(candidate, birth_year, current_year=current_year)
        for candidate in candidates
        if candidate.get("year")
    ]


TIMING_DECISION_EVENT_DISPLAY: dict[str, dict[str, str]] = {
    "receivables_recovery_year": {
        "title": "채권 회수",
        "phrase": "채권 회수·미수금 정리",
        "focusLine": "받아야 할 돈이 실제 회수되는 해",
        "decisionLine": "지연된 보상과 미수금이 정리되는 연도",
        "productLine": "성과 보상, 대여금, 지연 지급이 실제 입금과 정산으로 확정됩니다.",
    },
    "debt_guarantee_caution": {
        "title": "보증·채무",
        "phrase": "대여·보증·채무 책임",
        "focusLine": "남의 돈 문제가 자기 책임으로 넘어오기 쉬운 해",
        "decisionLine": "대여, 보증, 채무 인수에 신중해야 하는 연도",
        "productLine": "호의로 시작한 금전 관계가 책임 문제로 번질 수 있습니다.",
    },
    "family_asset_caution": {
        "title": "가족재산",
        "phrase": "가족재산·원가족 지출",
        "focusLine": "가족 돈과 자기 자산의 경계가 중요해지는 해",
        "decisionLine": "가족 자산, 상속성 돈, 원가족 지출을 구분해야 하는 연도",
        "productLine": "가족 문제로 움직이는 돈이 자기 자산의 기준을 흔들 수 있습니다.",
    },
    "compensation_rise": {
        "title": "보상 상승",
        "phrase": "연봉·성과급·지분 보상",
        "focusLine": "성과가 실제 보상으로 확정되기 쉬운 해",
        "decisionLine": "연봉, 성과급, 수수료, 지분 조건을 잡기 좋은 연도",
        "productLine": "해낸 일의 가치가 말뿐인 인정이 아니라 금전 보상으로 정리됩니다.",
    },
    "career_domain_shift": {
        "title": "전문 방향 전환",
        "phrase": "직업 분야·역할 전환",
        "focusLine": "맞는 산업과 역할이 새로 드러나는 해",
        "decisionLine": "직업 분야와 전문 방향이 바뀌는 연도",
        "productLine": "단순 이직보다 산업, 역할, 전문 방향의 선택이 중요해집니다.",
    },
    "career_independence_year": {
        "title": "직업 독립",
        "phrase": "독립·개인 기반",
        "focusLine": "자기 이름으로 일할 기반이 생기는 해",
        "decisionLine": "독립, 개인 고객, 별도 수입원을 세우기 좋은 연도",
        "productLine": "조직 안의 성과를 자기 이름과 고객 기반으로 옮길 수 있습니다.",
    },
    "separation_closure_year": {
        "title": "관계 정리",
        "phrase": "이별·정리",
        "focusLine": "애매한 관계를 끝내거나 다시 정리하는 해",
        "decisionLine": "오래 끌어온 관계의 결론이 분명해지는 연도",
        "productLine": "미뤄 둔 감정과 관계의 방향을 더는 애매하게 두기 어렵습니다.",
    },
    "external_interference_caution": {
        "title": "주변 개입",
        "phrase": "가족·지인·과거 인연",
        "focusLine": "주변 사람의 말이 관계에 끼어드는 해",
        "decisionLine": "제삼자의 말이 관계 판단을 흔드는 연도",
        "productLine": "친구, 가족, 과거 인연의 말이 관계 안으로 들어오며 결정이 흔들립니다.",
    },
    "couple_finance_year": {
        "title": "부부 재정",
        "phrase": "생활비·공동자산 기준",
        "focusLine": "부부 사이의 돈 기준이 현실 과제가 되는 해",
        "decisionLine": "생활비, 명의, 공동자산 기준을 정해야 하는 연도",
        "productLine": "관계의 확신이 생활비와 자산 기준으로 옮겨갑니다.",
    },
    "child_rearing_year": {
        "title": "양육 책임",
        "phrase": "자녀·돌봄·교육비",
        "focusLine": "자녀와 양육 책임이 커지는 해",
        "decisionLine": "돌봄과 교육비 문제가 생활 안으로 들어오는 연도",
        "productLine": "자녀, 돌봄, 교육비, 가족 지원 문제가 부부 생활의 실제 과제가 됩니다.",
    },
}


def _snake_or_camel(payload: dict[str, Any], snake: str, camel: str = "") -> Any:
    if snake in payload:
        return payload.get(snake)
    if camel:
        return payload.get(camel)
    parts = snake.split("_")
    camel_key = parts[0] + "".join(part.capitalize() for part in parts[1:])
    return payload.get(camel_key)


def _timing_decision_event_payloads(
    timing_decision: dict[str, Any],
    birth_year: int,
    *,
    current_year: int | None = None,
) -> list[dict[str, Any]]:
    event_years = timing_decision.get("event_years")
    if not isinstance(event_years, dict):
        return []
    payloads: list[dict[str, Any]] = []
    for event_key, event in event_years.items():
        if not isinstance(event, dict) or not event.get("year"):
            continue
        display = TIMING_DECISION_EVENT_DISPLAY.get(str(event_key), {})
        domain = str(event.get("domain") or "")
        kind = str(event.get("kind") or "")
        candidate = {
            "year": event.get("year"),
            "domain": domain,
            "domainLabel": str(event.get("domain_label") or TIMING_DOMAIN_LABELS.get(domain, domain)),
            "kind": kind,
            "variant": str(event_key),
            "eventKey": str(event_key),
            "score": event.get("score"),
            "scoreParts": _snake_or_camel(event, "score_parts", "scoreParts") or {},
            "title": display.get("title") or str(event.get("event_label") or event.get("focus") or ""),
            "phrase": display.get("phrase") or str(event.get("focus") or event.get("event_label") or ""),
            "focusLine": display.get("focusLine") or str(event.get("focus") or ""),
            "decisionLine": display.get("decisionLine") or str(event.get("event_label") or event.get("focus") or ""),
            "productLine": display.get("productLine") or "",
            "activationLabel": str(event.get("activation_label") or ""),
            "structureKeywords": [
                str(item)
                for item in list(event.get("structure_keywords") or [])
                if str(item)
            ][:5],
            "daeunPillar": str(event.get("daeun_pillar") or ""),
            "daeunStemTenGod": str(event.get("daeun_stem_ten_god") or ""),
            "daeunBranchTenGod": str(event.get("daeun_branch_main_ten_god") or ""),
            "yearPillar": str(event.get("year_pillar") or ""),
            "yearStemTenGod": str(event.get("year_stem_ten_god") or ""),
            "yearBranchTenGod": str(event.get("year_branch_main_ten_god") or ""),
            "activationContext": event.get("activation_context") if isinstance(event.get("activation_context"), dict) else {},
        }
        payloads.append(_timing_event_payload(candidate, birth_year, current_year=current_year))
    return sorted(
        payloads,
        key=lambda item: (
            0 if item.get("variant") in TIMING_DECISION_EVENT_DISPLAY else 1,
            -float(item.get("score") or 0),
            int(item.get("year") or 9999),
        ),
    )


def _merge_timing_event_payloads(
    base: list[dict[str, Any]],
    additions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for item in list(base or []) + list(additions or []):
        if not isinstance(item, dict):
            continue
        key = (
            item.get("variant") or item.get("eventKey") or "",
            item.get("year") or "",
            item.get("domain") or "",
            item.get("kind") or "",
            item.get("title") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _timing_domain_year_payloads(
    domain_year_candidates: dict[str, dict[str, Any | None]],
    birth_year: int,
    *,
    current_year: int | None = None,
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for domain in TIMING_DOMAIN_LABELS:
        item = domain_year_candidates.get(domain) or {}
        good = item.get("good")
        caution = item.get("caution")
        payloads.append(
            {
                "domain": domain,
                "domainLabel": str(item.get("domainLabel") or TIMING_DOMAIN_LABELS.get(domain, domain)),
                "good": _timing_event_payload(good, birth_year, current_year=current_year)
                if isinstance(good, dict)
                else None,
                "caution": _timing_event_payload(caution, birth_year, current_year=current_year)
                if isinstance(caution, dict)
                else None,
            }
        )
    return payloads


def _premium_timing_section(
    chart_summary: dict[str, Any],
    normalized_sections: list[dict[str, Any]],
    fallback_action: str,
    fallback_caution: str,
) -> dict[str, Any]:
    rows = list(chart_summary.get("timingAnnualRows") or chart_summary.get("annualRows") or [])
    birth_year = _birth_year_from_timing_rows(rows) or 0
    good_years, caution_years = _select_year_candidates(rows, normalized_sections)
    current_year = _current_year_from_timing_rows(rows, chart_summary)
    domain_years = _timing_domain_year_payloads(
        _select_domain_year_candidates(rows, normalized_sections),
        birth_year,
        current_year=current_year,
    )
    past_good, future_good = _split_timing_candidates(good_years, current_year)
    past_caution, future_caution = _split_timing_candidates(caution_years, current_year)
    good_label = _candidate_short_list(good_years, "뚜렷한 연도 없음", birth_year=birth_year)
    caution_label = _candidate_short_list(caution_years, "뚜렷한 연도 없음", birth_year=birth_year)
    past_good_label = _candidate_short_list(past_good, "해당 없음", birth_year=birth_year)
    past_caution_label = _candidate_short_list(past_caution, "해당 없음", birth_year=birth_year)
    good_year_age_label = _candidate_year_age_list(good_years, "뚜렷한 연도 없음", birth_year=birth_year)
    caution_year_age_label = _candidate_year_age_list(caution_years, "뚜렷한 연도 없음", birth_year=birth_year)
    good_phrase = _candidate_phrase_sentence(good_years, "성과와 계약")
    caution_phrase = _candidate_phrase_sentence(caution_years, "돈과 책임 문제")
    good_focus = _candidate_detail(good_years[0] if good_years else None, fallback_action)
    caution_focus = _candidate_detail(
        caution_years[0] if caution_years else None,
        fallback_caution,
    )
    good_domain_summary = _candidate_domain_summary(good_years, "성과와 기회")
    caution_domain_summary = _candidate_domain_summary(caution_years, "책임과 손실")
    top_good_years = _timing_ranked_candidates(good_years, limit=1) or good_years[:1]
    top_caution_years = _timing_ranked_candidates(caution_years, limit=1) or caution_years[:1]
    good_anchor = _candidate_event_label_list(top_good_years, "뚜렷한 연도 없음", birth_year=birth_year, limit=1)
    caution_anchor = _candidate_event_label_list(top_caution_years, "뚜렷한 연도 없음", birth_year=birth_year, limit=1)
    if good_domain_summary == caution_domain_summary:
        lead = f"20세~79세 전체에서 {good_domain_summary}의 상승 연도와 주의 연도가 모두 뚜렷합니다. 대표 상승은 {good_anchor}, 대표 주의는 {caution_anchor}입니다."
    else:
        lead = (
            f"20세~79세 전체에서 상승 연도는 {good_domain_summary}, 주의 연도는 {caution_domain_summary}에서 뚜렷합니다. "
            f"대표 상승은 {good_anchor}, 대표 주의는 {caution_anchor}입니다."
        )
    timing_events = _timing_event_payloads(
        good_years + caution_years,
        birth_year,
        current_year=current_year,
    )
    timing_decades = _timing_decade_groups(
        rows,
        normalized_sections,
        birth_year,
        current_year=current_year,
    )
    timing_profile = _timing_calendar_profile(good_years, caution_years, timing_decades)
    timing_map = _timing_map_payload(
        good_years,
        caution_years,
        timing_decades,
        past_good,
        past_caution,
        future_good,
        future_caution,
        domain_years,
        birth_year=birth_year,
        current_year=current_year,
    )
    good_keyword_text = _candidate_phrase_sentence(good_years, good_phrase)
    caution_keyword_text = _candidate_phrase_sentence(caution_years, caution_phrase)
    timing_narrative = (
        f"상승 연도 {_candidate_event_label_list(good_years, good_year_age_label, birth_year=birth_year)}. "
        f"주의 연도 {_candidate_event_label_list(caution_years, caution_year_age_label, birth_year=birth_year)}. "
        f"상승 쪽은 {good_keyword_text}, 주의 쪽은 {_with_subject_particle(caution_keyword_text)} 핵심입니다."
    )
    checkpoints = [
        f"상승 연도: {good_label}",
        f"주의 연도: {caution_label}",
        f"대표 사건: {good_focus}",
        f"주의 사건: {caution_focus}",
    ]
    if past_good:
        checkpoints.insert(2, f"과거 상승 연도: {past_good_label}")
    if past_caution:
        insert_at = 3 if past_good else 2
        checkpoints.insert(insert_at, f"과거 주의 연도: {past_caution_label}")
    summary_items = [
        {"label": "상승 연도", "value": good_label},
        {"label": "주의 연도", "value": caution_label},
    ]
    if past_good or past_caution:
        summary_items.append({"label": "과거 확인", "value": past_good_label if past_good else past_caution_label})

    section = _premium_section(
        "premium-good-timing",
        domain="timing",
        domain_label="인생 주요 연도",
        heading="인생 주요 연도",
        lead=lead,
        narrative=timing_narrative,
        checkpoints=checkpoints,
        timing_events=timing_events,
        detail_blocks=_timing_detail_blocks(
            good_years,
            caution_years,
            past_good,
            past_caution,
            birth_year=birth_year,
        ),
        summary_items=summary_items,
        topic_items=_timing_topic_items(
            good_years,
            caution_years,
            past_good,
            past_caution,
            birth_year=birth_year,
        ),
    )
    section["headline"] = f"상승 연도: {good_anchor}. 주의 연도: {caution_anchor}."
    section["judgment_axes"] = [
        {"key": "good_years", "label": "상승 연도", "value": good_label},
        {"key": "caution_years", "label": "주의 연도", "value": caution_label},
        {"key": "good_domains", "label": "상승 분야", "value": good_domain_summary},
        {"key": "caution_domains", "label": "주의 분야", "value": caution_domain_summary},
    ]
    section["timing_decades"] = timing_decades
    section["timing_profile"] = timing_profile
    section["timing_map"] = timing_map
    return section


def _best_section_axis(
    section: dict[str, Any] | None,
    candidates: list[tuple[str, str, int]],
) -> tuple[str, str]:
    axes = _section_axis_map(section)
    ranked: list[tuple[int, int, str, str]] = []
    for order, (key, label, bias) in enumerate(candidates):
        value = axes.get(key, {}).get("value", "")
        if not value:
            continue
        ranked.append((_section_value_strength(value) + bias, -order, label, value))
    if not ranked:
        if not candidates:
            return "핵심 항목", "확인 필요"
        return candidates[0][1], "확인 필요"
    _score, _order, label, value = max(ranked, key=lambda item: (item[0], item[1]))
    return label, value


def _feature_item_from_sections(*sections: dict[str, Any] | None) -> dict[str, Any]:
    return {"feature_axes": _merged_feature_axes_from_sections(*sections)}


def _average_feature_score(
    product_item: dict[str, Any] | None,
    keys: tuple[str, ...],
    *,
    fallback: int = 58,
) -> int:
    scores = [
        score
        for key in keys
        if isinstance((score := _feature_score(product_item, key)), int)
    ]
    if not scores:
        return fallback
    return max(0, min(100, round(sum(scores) / len(scores))))


def _topic_payload(
    domain: str,
    title: str,
    score: int,
    body: str,
    evidence_labels: tuple[str, ...],
) -> dict[str, Any]:
    evidence = ""
    labels = [label for label in evidence_labels if label]
    if labels:
        evidence = f"근거 항목: {', '.join(labels[:2])} · 결과 등급: {_score_value(score)}"
    payload: dict[str, Any] = {
        "title": title,
        "body": body,
        "definition": premium_topic_definition(domain, title) or body,
        "value": _score_value(score),
        "score": score,
        "tone": _topic_tone_from_score(score),
    }
    if evidence:
        payload["evidence"] = evidence
    return payload


def _scored_body(score: int, weak: str, normal: str, strong: str, peak: str) -> str:
    if score >= 90:
        return peak
    if score >= 76:
        return strong
    if score >= 58:
        return normal
    return weak


def _life_topic_items_from_sections(*sections: dict[str, Any] | None) -> list[dict[str, Any]]:
    item = _feature_item_from_sections(*sections)
    early_score = _average_feature_score(item, ("self_direction", "decision_consistency"))
    middle_score = _average_feature_score(
        item,
        ("career_achievement", "money_potential", "responsibility_capacity"),
    )
    late_score = _average_feature_score(
        item,
        ("asset_retention", "reputation_maintenance", "marriage_stability", "family_responsibility"),
    )
    transition_score = _average_feature_score(
        item,
        ("change_adaptability", "crisis_recovery", "responsibility_capacity"),
    )
    return [
        _topic_payload(
            "life",
            "초년에 형성되는 바탕",
            early_score,
            _scored_body(
                early_score,
                "초년에는 진로가 한 번에 고정되지 않습니다. 전공, 첫 일, 인간관계에서 시행착오가 생기지만 그 과정이 이후 선택 기준을 만듭니다.",
                "초년에는 경험을 거치며 기준이 잡힙니다. 급히 정한 선택보다 직접 확인한 길이 오래 갑니다.",
                "초년부터 선호와 거부감이 분명합니다. 전공이나 첫 진로에서도 남의 기대보다 자신의 판단이 앞섭니다.",
                "초년부터 주관이 강합니다. 맞지 않는 환경을 오래 참기보다 일찍 방향을 고쳐 자기 길을 만듭니다.",
            ),
            ("자기 주도성", "결정 지속성"),
        ),
        _topic_payload(
            "life",
            "중년에 굳어지는 성취",
            middle_score,
            _scored_body(
                middle_score,
                "중년에는 책임이 먼저 늘고 보상이 늦게 따라올 수 있습니다. 직함보다 권한과 보상 기준을 먼저 확인해야 합니다.",
                "중년에는 직업 책임과 생활 기반이 안정됩니다. 고정 수입, 거래처, 보유 자산처럼 현실에 남는 결과가 늘어납니다.",
                "중년에는 경력의 가치가 달라집니다. 맡은 책임이 보상과 직책으로 연결됩니다.",
                "중년 이후 성취가 가장 크게 올라옵니다. 직책과 수입, 자산 결정이 함께 움직입니다.",
            ),
            ("직업적 성취력", "재물 잠재력"),
        ),
        _topic_payload(
            "life",
            "말년에 남는 안정",
            late_score,
            _scored_body(
                late_score,
                "말년에는 가족 책임이 안정의 변수가 됩니다. 가까운 사람에게 재정 결정을 맡기면 손실이 남습니다.",
                "말년에는 새 일을 넓히기보다 보유 자산을 정돈하는 쪽으로 무게가 갑니다.",
                "말년에는 보유 자산이 생활 안정의 중심이 됩니다. 주거 기반도 비교적 견고하게 남습니다.",
                "말년에는 축적한 자산이 생활의 중심이 됩니다. 주거, 예금, 장기 수익처가 후반의 안정감을 만듭니다.",
            ),
            ("자산 유지력", "평판 유지력"),
        ),
        _topic_payload(
            "life",
            "운이 바뀌는 전환기",
            transition_score,
            _scored_body(
                transition_score,
                "인생 전환기에는 역할 변화에 늦게 적응할 수 있습니다. 결정을 미루면 제안과 기회가 먼저 줄어듭니다.",
                "인생 전환기에는 맡는 역할과 생활 과제가 달라집니다. 익숙한 방식만 고집하면 중요한 선택이 늦어집니다.",
                "인생 전환기마다 맡는 자리가 분명해집니다. 새 역할을 빠르게 확보할수록 다음 단계가 안정됩니다.",
                "인생 전환기마다 책임의 규모가 크게 달라집니다. 이때 잡은 역할이 이후 십 년의 방향을 정합니다.",
            ),
            ("변화 적응력", "책임 감당력"),
        ),
    ]


def _topic_lookup_by_title(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("title") or ""): item for item in items if isinstance(item, dict)}


def _strongest_topic(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {}
    return max(items, key=lambda item: int(item.get("score") or 0))


def _life_lead_from_topic(topic: dict[str, Any]) -> str:
    title = str(topic.get("title") or "")
    if title in {"초년·청년기", "초년에 형성되는 바탕"}:
        return "초년부터 자기 기준이 분명하게 형성되는 사주입니다."
    if title in {"중년기", "중년에 커지는 성취", "중년에 굳어지는 성취"}:
        return "중년 이후 직업 성취가 크게 살아나는 사주입니다."
    if title in {"말년기", "말년에 남는 안정"}:
        return "말년으로 갈수록 자산 기반이 안정적으로 남는 사주입니다."
    if title in {"대운 전환", "운이 바뀌는 전환기"}:
        return "큰 운이 바뀔 때 삶의 무대와 맡는 역할이 크게 달라지는 사주입니다."
    return "인생 구간마다 강해지는 과제가 분명한 사주입니다."


def _life_transition_bullet(timing_caution: str) -> str:
    caution = _clean_caution_label(timing_caution)
    replacements = {
        "지분·명의 안정성": "전환기에는 가까운 사람과 얽힌 명의 문제가 드러납니다. 금전 판단을 미루면 부담이 길어집니다.",
        "공동 자금 기준 필요": "전환기에는 가까운 사람과 얽힌 명의 문제가 드러납니다. 금전 판단을 미루면 부담이 길어집니다.",
        "책임·권한 균형": "전환기에는 책임 범위와 결정권을 먼저 확인해야 합니다. 맡는 일은 늘어나는데 권한이 약하면 직업 부담이 길어집니다.",
        "표현과 연락 엇갈림": "전환기에는 표현과 연락 방식이 관계를 크게 흔듭니다. 애매하게 넘긴 말은 나중에 서로 다르게 받아들일 수 있습니다.",
    }
    if caution in replacements:
        return replacements[caution]
    if caution.endswith("필요"):
        topic = caution[: -len("필요")].strip()
        if topic:
            return f"전환기에는 {_with_object_particle(topic)} 먼저 정리해야 합니다. 직업, 주거, 가족 책임이 겹치면 부담이 길어집니다."
    if caution:
        return f"전환기에는 {caution} 문제를 먼저 정리해야 합니다. 직업, 주거, 가족 책임이 겹치면 부담이 길어집니다."
    return "전환기에는 직업, 거처, 가족 책임이 함께 움직입니다. 맡는 역할과 생활 조건이 동시에 바뀌기 쉬우므로, 한 번의 선택이 이후 구간의 방향을 크게 정합니다."


def _dynamic_life_stage_section(
    normalized_sections: list[dict[str, Any]],
    chart_summary: dict[str, Any],
    *,
    top_pair: str,
    life_current: str,
    timing_caution: str,
) -> dict[str, Any]:
    daeun = _daeun_label(chart_summary)
    next_daeun = _next_daeun_label(chart_summary)
    early_life = _early_life_age_label(chart_summary)
    topic_items = _life_topic_items_from_sections(*normalized_sections)
    topics = _topic_lookup_by_title(topic_items)
    early = topics.get("초년에 형성되는 바탕", {}) or topics.get("초년·청년기", {})
    middle = topics.get("중년에 굳어지는 성취", {}) or topics.get("중년에 커지는 성취", {}) or topics.get("중년기", {})
    late = topics.get("말년에 남는 안정", {}) or topics.get("말년기", {})
    transition = topics.get("운이 바뀌는 전환기", {}) or topics.get("대운 전환", {})
    lead_topic = _strongest_topic([early, middle, late, transition])
    lead = _life_lead_from_topic(lead_topic)
    narrative = (
        f"{early.get('body', '')} {middle.get('body', '')} {late.get('body', '')} "
        f"현재 {daeun}에는 {life_current}. 다음 {next_daeun}에는 직업상 책임이 다시 배치됩니다."
    ).strip()
    return _premium_section(
        "premium-life-stages",
        domain="life",
        domain_label="초년·중년·말년",
        heading="초년·중년·말년",
        lead=lead,
        narrative=narrative,
        checkpoints=[
            f"초년·청년운: {early.get('body', '초년부터 자기 기준이 형성됩니다.')}",
            f"중년운: {middle.get('body', '중년에는 직업 성취와 생활 기반이 자리를 잡습니다.')}",
            f"말년운: {late.get('body', '말년에는 자산과 평판이 생활 기반으로 남습니다.')}",
            f"초년 결론: {early.get('body', '초년부터 자기 기준이 형성됩니다.')}",
            f"중년 결론: {middle.get('body', '중년에는 직업 성취와 생활 기반이 자리를 잡습니다.')}",
            f"말년 결론: {late.get('body', '말년에는 자산과 평판이 생활 기반으로 남습니다.')}",
            f"현재 구간: {daeun} {top_pair} 우세",
            f"다음 구간: {next_daeun} 역할 재배치",
            f"전환 주의: {timing_caution}",
        ],
        detail_blocks=[
            _detail_block(
                "초년·청년의 형성",
                str(early.get("body") or ""),
                [f"{early_life} 구간에는 전공 선택에서 남의 기준보다 자기 기준이 먼저 작동합니다."],
            ),
            _detail_block(
                "중년의 성취",
                str(middle.get("body") or ""),
                ["중년에는 성과가 직책과 보상으로 남습니다."],
                tone="strong" if int(middle.get("score") or 0) >= 76 else "",
            ),
            _detail_block(
                "말년의 안정",
                str(late.get("body") or ""),
                ["말년에는 주거와 보유 자산이 후반기 생활의 중심이 됩니다."],
                tone="strong" if int(late.get("score") or 0) >= 76 else "",
            ),
            _detail_block(
                "인생 전환기",
                str(transition.get("body") or ""),
                [_life_transition_bullet(timing_caution)],
                tone="risk" if int(transition.get("score") or 0) < 58 else "",
            ),
        ],
        topic_items=topic_items,
        feature_axes=_merged_feature_axes_from_sections(*normalized_sections),
    )


def _honor_topic_items(career: dict[str, Any] | None) -> list[dict[str, Any]]:
    item = _feature_item_from_sections(career)
    recognition_score = _average_feature_score(
        item,
        ("honor_recognition", "social_success_potential", "career_achievement"),
    )
    reputation_score = _average_feature_score(item, ("reputation_maintenance", "responsibility_capacity"))
    formal_score = _average_feature_score(
        item,
        ("responsibility_capacity", "organization_adaptability", "leadership_potential"),
    )
    management_score = _average_feature_score(item, ("reputation_maintenance", "loss_avoidance", "practical_planning"))
    return [
        _topic_payload(
            "honor",
            "공적 인정 기반",
            recognition_score,
            _scored_body(
                recognition_score,
                "공적 인정은 천천히 형성됩니다. 빠른 주목보다 끝까지 맡은 이력이 신뢰를 만듭니다.",
                "맡은 역할이 쌓일수록 공식 평가가 분명해집니다. 직함보다 책임 이력이 먼저 인정받습니다.",
                "공식 평가가 직책 상승으로 이어집니다. 조직 안에서 이름을 걸고 책임지는 역할을 맡기 쉽습니다.",
                "사회적으로 이름이 알려지는 자리까지 올라갑니다. 공식 책임이 붙고, 그 책임이 직함으로 남습니다.",
            ),
            ("명예운", "직업적 성취력"),
        ),
        _topic_payload(
            "honor",
            "평판이 오래 남는 힘",
            reputation_score,
            _scored_body(
                reputation_score,
                "평판은 얻는 것보다 지키는 일이 더 어렵습니다. 말과 약속이 흐려지면 손상이 빠릅니다.",
                "꾸준한 이력이 평판을 지킵니다. 한 번에 뜨는 이름보다 오래 쌓은 결과가 강합니다.",
                "한 번 쌓은 신뢰가 재의뢰로 돌아옵니다. 기록으로 남은 결과물이 평판을 지킵니다.",
                "평판이 오래 유지됩니다. 마무리가 좋은 일들이 다음 제안을 만듭니다.",
            ),
            ("평판 유지력", "책임 감당력"),
        ),
        _topic_payload(
            "honor",
            "공식 책임을 맡는 힘",
            formal_score,
            _scored_body(
                formal_score,
                "공식 책임이 권한 없이 주어지면 부담이 먼저 남습니다. 명예보다 책임 문제가 앞섭니다.",
                "역할이 분명한 자리에서는 책임을 감당합니다. 책임 범위가 정해져야 실력이 평가됩니다.",
                "책임자 역할을 맡을 때 이력이 남습니다. 남이 정리하지 못한 일을 마무리하면 평판이 직함으로 바뀝니다.",
                "책임자, 관리자, 대표 역할에서 두각을 드러냅니다. 결정권이 함께 있을수록 직함과 명예가 함께 붙습니다.",
            ),
            ("책임 감당력", "조직 적응력"),
        ),
        _topic_payload(
            "honor",
            "명예를 지켜내는 기준",
            management_score,
            _scored_body(
                management_score,
                "금전 책임이 흐려지면 평판이 먼저 손상됩니다. 특히 말로 정한 약속은 불리합니다.",
                "책임 범위를 분명히 하면 평판을 지킵니다. 기록, 일정, 정산 기준이 명예를 보호합니다.",
                "직함이 붙은 뒤에도 평판을 잃지 않습니다. 끝까지 책임진 이력이 다음 제안을 불러옵니다.",
                "직함이 높아질수록 신뢰도 더 단단해집니다. 큰 책임을 맡아도 평판을 끝까지 지켜냅니다.",
            ),
            ("평판 유지력", "손실 방어력"),
        ),
    ]


def _social_topic_items(
    love: dict[str, Any] | None,
    marriage: dict[str, Any] | None,
    money: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    item = _feature_item_from_sections(love, marriage, money)
    people_score = _average_feature_score(item, ("interpersonal_influence", "communication_expression"))
    support_score = _average_feature_score(
        item,
        ("interpersonal_influence", "reputation_maintenance", "academic_expertise"),
    )
    sustain_score = _average_feature_score(item, ("relationship_stability", "conflict_recovery"))
    boundary_score = _average_feature_score(
        item,
        ("boundary_management", "family_responsibility", "loss_avoidance"),
    )
    return [
        _topic_payload(
            "social",
            "사람을 얻는 힘",
            people_score,
            _scored_body(
                people_score,
                "사람을 넓히기보다 검증해서 만납니다. 얕은 인맥은 오래 남지 않습니다.",
                "필요한 사람을 오래 보고 관계로 남깁니다. 한 번 믿은 사람과는 관계가 길게 유지됩니다.",
                "필요한 사람을 알아보고 협업 관계로 묶습니다. 소개가 말에서 끝나지 않고 실제 제안으로 이어집니다.",
                "사람이 모이는 자리에서 필요한 사람을 빠르게 가려냅니다. 인맥이 소개, 거래, 지원으로 연결됩니다.",
            ),
            ("대인 영향력", "표현 전달력"),
        ),
        _topic_payload(
            "social",
            "도움으로 이어지는 인연",
            support_score,
            _scored_body(
                support_score,
                "결정적인 도움은 늦게 들어옵니다. 먼저 혼자 처리해야 하는 일이 많습니다.",
                "결정적인 도움은 말뿐인 응원이 아니라 실제 소개로 들어옵니다. 말뿐인 약속에는 기대를 크게 걸지 않는 편이 낫습니다.",
                "윗사람에게서 현실적인 도움이 들어옵니다. 소개가 실제 제안으로 이어집니다.",
                "윗사람과 전문가의 추천이 결정적인 자리를 만들어줍니다. 혼자 밀어붙이기보다 사람을 통해 기회가 열립니다.",
            ),
            ("대인 영향력", "평판 유지력"),
        ),
        _topic_payload(
            "social",
            "관계가 오래 남는 힘",
            sustain_score,
            _scored_body(
                sustain_score,
                "관계가 오래 남지 못하는 이유는 역할과 거리의 기준이 무너지기 때문입니다. 가까워질수록 맡길 일과 거절할 일이 분명해야 합니다.",
                "감정이 깊어진 뒤에도 관계를 오래 유지합니다. 갑자기 가까워지는 관계보다 오래 본 사람이 결정적인 도움을 줍니다.",
                "감정이 깊어진 뒤에도 관계를 오래 유지합니다. 오래 본 사람이 결국 소개, 보호, 실무 지원으로 돌아옵니다.",
                "오래 쌓은 신뢰가 실제 소개와 제안으로 돌아옵니다. 중요한 순간에는 말뿐인 응원보다 움직여줄 사람이 남습니다.",
            ),
            ("관계 안정성", "갈등 회복력"),
        ),
        _topic_payload(
            "social",
            "부탁과 책임의 경계",
            boundary_score,
            _scored_body(
                boundary_score,
                "가까운 사람의 부탁이 금전 부담으로 넘어옵니다. 거절이 늦으면 손해가 생깁니다.",
                "한 번 맡아준 부탁은 책임으로 되돌아옵니다. 호의가 당연한 책임처럼 굳어지는 관계는 끊어내야 합니다.",
                "가까운 관계에서도 책임의 선을 지킵니다. 도와주되 끌려가지는 않습니다.",
                "사람 사이의 부탁과 책임을 안정적으로 정리합니다. 가까운 사이에서도 주도권을 잃지 않습니다.",
            ),
            ("관계 경계 설정력", "가족 책임감"),
        ),
    ]


def _section_caution(section: dict[str, Any] | None, fallback: str = "주의점 확인") -> str:
    if not section:
        return fallback
    caution = str(section.get("caution_label") or "").strip()
    return _clean_caution_label(caution, fallback)


def _section_action(section: dict[str, Any] | None, fallback: str = "강점 확인") -> str:
    if not section:
        return fallback
    action = str(section.get("action_label") or "").strip()
    return action or fallback


def _top_section_action(top_sections: list[dict[str, Any]]) -> str:
    if not top_sections:
        return "강점 확인"
    return _section_action(top_sections[0])


def _top_section_caution(top_sections: list[dict[str, Any]]) -> str:
    for section in top_sections:
        caution = _section_caution(section, "")
        if caution:
            return caution
    return "무리한 확장 주의"


def _dynamic_honor_section(career: dict[str, Any] | None) -> dict[str, Any]:
    topic_items = _honor_topic_items(career)
    topics = _topic_lookup_by_title(topic_items)
    honor_topic = topics.get("공적 인정 기반", {}) or topics.get("사회적 인정이 붙는 자리", {}) or topics.get("사회적 인정도", {})
    reputation_topic = topics.get("평판이 오래 남는 힘", {}) or topics.get("평판 유지력", {})
    formal_topic = topics.get("공식 책임을 맡는 힘", {}) or topics.get("공식 책임", {})
    management_topic = topics.get("명예를 지켜내는 기준", {}) or topics.get("명예 관리", {})
    lead_label, lead_value = _best_section_axis(
        career,
        [
            ("recognition", "사회적 인정도", 8),
            ("career_achievement", "직업 성취력", 5),
            ("organization_fit", "조직 안에서 자리 잡는 힘", 4),
            ("responsibility_capacity", "책임 수행력", 3),
            ("expertise", "전문성", 1),
        ],
    )
    recognition = _section_axis_value(career, "recognition")
    achievement = _section_axis_value(career, "career_achievement")
    organization = _section_axis_value(career, "organization_fit")
    caution = _section_caution(career, "책임 대비 권한 부족")
    strongest = _strongest_topic(topic_items)
    strongest_title = str(strongest.get("title") or "")
    if strongest_title in {"공적 인정 기반", "사회적 인정도", "사회적 인정이 붙는 자리"}:
        main_sentence = "당신은 이름이 기록되는 책임 자리에서 명예가 올라가는 사주입니다."
    elif strongest_title in {"평판 유지력", "평판이 오래 남는 힘"}:
        main_sentence = "당신의 명예운은 오래 쌓은 신뢰가 다음 제안으로 돌아오는 쪽입니다."
    elif strongest_title in {"공식 책임", "공식 책임을 맡는 힘"}:
        main_sentence = "당신은 책임자 위치에 설 때 이름과 평판이 함께 올라갑니다."
    else:
        main_sentence = "당신의 명예운은 평판을 지키면서 책임의 크기를 키워가는 쪽입니다."
    support_sentence = str(strongest.get("body") or "").strip()
    if _grade_strength(lead_value) <= 2 and lead_label == "전문성":
        support_sentence = "빠른 주목보다 전문 분야와 책임 이력이 쌓일수록 명예가 강해집니다."
    management_score = int(management_topic.get("score") or 0)
    management_title = "명예를 지키는 방식" if management_score >= 58 else "평판을 깎는 자리"
    return _premium_section(
        "premium-honor",
        domain="honor",
        domain_label="명예운",
        heading="명예운",
        lead=main_sentence,
        narrative=f"{support_sentence} {management_topic.get('body', '책임 범위가 흐려지면 평판이 먼저 흔들립니다.')}",
        checkpoints=[
            f"공적 인정 기반: {recognition}",
            f"직업 성취력: {achievement}",
            f"공적 인정 기반: {_section_axis_value(career, 'recognition')}",
            f"전문성: {_section_axis_value(career, 'expertise')}",
            f"조직 안에서 자리 잡는 힘: {organization}",
            f"주의점: {caution}",
        ],
        detail_blocks=[
            _detail_block(
                "인정받는 방식",
                str(honor_topic.get("body") or support_sentence),
                ["공개 평가처럼 이름이 기록되는 자리에서 강합니다.", "전문성이 검증되는 자리일수록 책임도 함께 붙습니다."],
            ),
            _detail_block(
                "직함이 붙는 자리",
                str(formal_topic.get("body") or "책임자처럼 역할이 기록되는 자리에서 평판이 강해집니다."),
                ["권한이 붙은 책임 자리에서 명예가 붙습니다.", "권한 없이 책임만 맡는 자리는 평판보다 소모가 남습니다."],
                tone="strong" if int(formal_topic.get("score") or 0) >= 76 else "",
            ),
            _detail_block(
                "평판이 남는 방식",
                str(reputation_topic.get("body") or "꾸준한 이력이 평판을 지켜줍니다."),
                ["말로 한 약속보다 기록이 평판을 지킵니다."],
            ),
            _detail_block(
                management_title,
                str(management_topic.get("body") or "책임에 비해 권한이 좁은 자리는 인정과 부담이 함께 남습니다."),
                [f"{_with_particle(caution, '이', '가')} 드러나는 자리에서는 책임 소재가 흐려집니다. 이때는 인정받는 속도보다 평판 손상이 더 빠르게 남습니다."],
                tone="risk" if management_score < 58 else "",
            ),
        ],
        topic_items=topic_items,
        feature_axes=_merged_feature_axes_from_sections(career),
    )


def _dynamic_social_section(
    love: dict[str, Any] | None,
    marriage: dict[str, Any] | None,
    money: dict[str, Any] | None,
) -> dict[str, Any]:
    topic_items = _social_topic_items(love, marriage, money)
    topics = _topic_lookup_by_title(topic_items)
    people_topic = topics.get("사람을 얻는 힘", {}) or topics.get("사람을 얻는 방식", {})
    support_topic = topics.get("도움으로 이어지는 인연", {}) or topics.get("도움이 되는 사람", {})
    sustain_topic = topics.get("관계가 오래 남는 힘", {}) or topics.get("관계 지속력", {})
    boundary_topic = topics.get("부탁과 책임의 경계", {}) or topics.get("부탁과 책임", {})
    lead_label, lead_value = _best_section_axis(
        love,
        [
            ("relationship_opening", "인연 형성력", 6),
            ("stability", "관계 안정성", 7),
            ("expression", "표현력", 5),
            ("boundary", "관계 조절력", 4),
            ("recovery", "갈등 회복력", 1),
        ],
    )
    opening = _section_axis_value(love, "relationship_opening")
    stability = _section_axis_value(love, "stability")
    boundary = _section_axis_value(love, "boundary")
    shared_money = _section_axis_value(money, "shared_asset_risk", "")
    money_caution = _section_caution(money, "")
    love_caution = _section_caution(love, "표현 거리감")
    if shared_money in {"주의", "높음"} or "정산" in money_caution or "몫" in money_caution:
        caution = "금전·역할 혼선 주의"
    else:
        caution = love_caution
    family = _section_axis_value(marriage, "responsibility_share")
    strongest = _strongest_topic(topic_items)
    strongest_title = str(strongest.get("title") or "")
    if strongest_title in {"관계 지속력", "관계가 오래 남는 힘"}:
        main_sentence = "당신은 넓은 인맥보다 오래 남는 사람을 통해 운이 열리는 사주입니다."
    elif strongest_title in {"도움이 되는 사람", "도움으로 이어지는 인연"}:
        main_sentence = "당신의 대인관계운은 말뿐인 친분보다 실제 제안으로 들어오는 인연이 강합니다."
    elif strongest_title in {"사람을 얻는 방식", "사람을 얻는 힘"}:
        main_sentence = "당신은 필요한 사람을 알아보고 오래 곁에 남기는 힘이 있습니다."
    else:
        main_sentence = "당신의 대인관계는 부탁과 책임의 선을 분명히 할수록 오래 갑니다."
    support_sentence = str(strongest.get("body") or "").strip()
    if caution == "금전·역할 혼선 주의":
        final_sentence = "가까운 사이에 금전 관계가 들어오면 배신감이나 손해가 남습니다."
    else:
        final_sentence = "가까운 사이일수록 금전 부탁을 구두 약속으로 처리하면 부담이 남습니다."
    if _grade_strength(boundary) <= 1:
        support_sentence = "가까워질수록 부탁과 책임이 섞입니다."
        final_sentence = "처음부터 부탁의 범위와 거절 기준이 분명해야 합니다."
    boundary_topic_score = int(boundary_topic.get("score") or 0)
    boundary_title = "부탁과 책임의 선" if boundary_topic_score >= 58 else "부탁이 부담으로 바뀌는 지점"
    return _premium_section(
        "premium-social",
        domain="social",
        domain_label="대인관계운",
        heading="대인관계운",
        lead=main_sentence,
        narrative=f"{support_sentence} {final_sentence}",
        checkpoints=[
            f"인연 형성력: {opening}",
            f"관계가 오래 가는 힘: {stability}",
            f"관계 조절력: {boundary}",
            f"갈등 회복력: {_section_axis_value(love, 'recovery')}",
            f"애정 표현력: {_section_axis_value(love, 'expression')}",
            f"가까운 관계 책임: {family}",
            f"주의점: {caution}",
        ],
        detail_blocks=[
            _detail_block(
                "신뢰 형성 방식",
                str(people_topic.get("body") or support_sentence),
                ["넓은 모임보다 오래 본 사람, 반복해서 협업한 사람이 실질적인 조력이 됩니다.", "인맥은 규모보다 결정적인 순간에 실질적인 지원을 하는 사람이 값어치를 가집니다."],
            ),
            _detail_block(
                "실질 조력자",
                str(support_topic.get("body") or "오래 신뢰한 사람이 현실적인 도움을 줍니다."),
                ["조언보다 실제 소개를 해주는 사람이 귀합니다.", "오래 본 관계에서 결정적인 소개가 들어옵니다."],
            ),
            _detail_block(
                "관계가 오래 남는 지점",
                str(sustain_topic.get("body") or "검증된 관계는 오래 남습니다."),
                ["서로의 역할과 거리가 분명할수록 관계가 오래 갑니다."],
            ),
            _detail_block(
                boundary_title,
                str(boundary_topic.get("body") or final_sentence),
                ["부탁을 한 번 받아주면 다음에는 당연한 책임처럼 돌아올 수 있습니다."],
                tone="risk" if boundary_topic_score < 58 else "",
            ),
        ],
        topic_items=topic_items,
        feature_axes=_merged_feature_axes_from_sections(love, marriage, money),
    )


def _premium_detail_domains_for_section(section: dict[str, Any]) -> tuple[str, ...]:
    section_id = str(section.get("section_id") or "")
    domain = str(section.get("domain") or "")
    heading = str(section.get("heading") or "")
    label = f"{section_id} {domain} {heading} {section.get('domain_label') or ''}"
    if "love-marriage" in section_id:
        return ("love", "marriage")
    if domain in {"love", "marriage"}:
        return (domain,)
    if "연애" in label:
        return ("love",)
    if "결혼" in label:
        return ("marriage",)
    if "good-timing" in section_id or domain == "timing" or "좋은 시기" in label:
        return ("timing",)
    if "life-stages" in section_id or domain == "life" or "초년" in label:
        return ("life_period",)
    if "personality" in section_id or domain == "personality" or "성향" in label or "성격" in label:
        return ("personality",)
    if "honor" in section_id or domain == "honor" or "명예" in label:
        return ("honor",)
    if "social" in section_id or domain == "social" or "대인" in label:
        return ("social",)
    if domain in {"money", "career"}:
        return (domain,)
    return (domain,) if domain else ()


def _normalize_premium_detail(detail: dict[str, Any]) -> dict[str, Any]:
    def clean_detail_text(value: Any) -> str:
        return (
            str(value or "")
            .strip()
            .replace("좋은 연도의 사건화", "좋은 연도에 드러나는 일")
            .replace("주의 연도의 손실 사건", "주의 연도에 관리할 일")
            .replace("좋은 연도에는 계약, 승진, 자산 취득처럼 결과가 남습니다.", "좋은 연도에는 계약, 승진, 자산 확보가 두드러집니다.")
            .replace("주의 연도에는 돈, 계약, 관계 중 하나가 크게 흔들립니다.", "주의 연도에는 금전, 계약, 관계에서 관리할 일이 생깁니다.")
            .replace("결혼 논의 지연", "결혼 준비 지연")
            .replace("결혼 논의", "결혼 준비")
            .replace("손실 사건", "관리할 일")
            .replace("손실 지점", "주의점")
        )

    title = clean_detail_text(detail.get("title"))
    judgment = clean_detail_text(detail.get("judgment"))
    scenes = [
        clean_detail_text(scene)
        for scene in detail.get("event_scenes", [])
        if clean_detail_text(scene)
    ][:3]
    notes = [
        clean_detail_text(note)
        for note in detail.get("premium_notes", [])
        if clean_detail_text(note)
    ][:2]
    caution_targets = [
        clean_detail_text(target)
        for target in detail.get("caution_targets", [])
        if clean_detail_text(target)
    ][:3]
    level = _premium_detail_level(
        str(detail.get("level") or ""),
        title=title,
        judgment=judgment,
    )
    return {
        "entry_key": str(detail.get("entry_key") or ""),
        "domain": str(detail.get("domain") or ""),
        "title": title,
        "score": int(detail.get("score") or 0),
        "level": level,
        "judgment": judgment,
        "event_scenes": scenes,
        "premium_notes": notes,
        "caution_targets": caution_targets,
        "timing_keywords": [
            clean_detail_text(keyword)
            for keyword in detail.get("timing_keywords", [])
            if clean_detail_text(keyword)
        ][:3],
    }


def _premium_detail_level(source_level: str, *, title: str, judgment: str) -> str:
    level = str(source_level or "").strip().lower()
    if level in {"risk", "watch", "caution"}:
        return "watch"
    text = f"{title} {judgment}"
    watch_markers = (
        "손실",
        "손상",
        "불균형",
        "압박",
        "부담",
        "소모",
        "늦",
        "덜 남",
        "나뉘",
        "줄어",
        "줄어듭",
        "넘어갑",
        "넘어오",
        "흔들",
        "말이 달라",
        "부딪",
        "침범",
        "채무",
        "보증",
        "권리 주장",
        "명의 대여",
        "말로 정한 약속",
        "섞이는 재산",
        "공동 투자",
        "회수 과정",
        "손해",
        "손익이 흐려",
        "기준 없는 조직",
        "책임 전가",
        "공을 빼앗",
        "사생활",
        "감정 기복",
        "경력에 흠",
        "충돌",
        "갈등",
        "부부 사이",
        "가족의 돈",
        "가족 지원",
        "가족 책임",
        "명의 갈등",
        "부양 부담",
        "결정권을 놓고",
        "지나간 서운함",
        "평판 손상",
        "견제",
        "당신 몫으로 굳",
    )
    if any(marker in text for marker in watch_markers):
        return "watch"
    return level or "neutral"


def _section_topic_strength(section: dict[str, Any], *titles: str) -> int:
    wanted = {_compact_match_key(title) for title in titles if title}
    if not wanted:
        return 0
    best = 0
    for item in section.get("topic_items") or []:
        if not isinstance(item, dict):
            continue
        title = _compact_match_key(item.get("title"))
        if title in wanted:
            score = item.get("score")
            if isinstance(score, int):
                best = max(best, score)
            else:
                best = max(best, _section_value_strength(str(item.get("value") or "")))
    return best


def _premium_detail_conflicts_with_section(detail: dict[str, Any], section: dict[str, Any]) -> bool:
    title = str(detail.get("title") or "")
    domains = set(_premium_detail_domains_for_section(section))
    if domains == {"career"}:
        recognition_power = _section_topic_strength(section, "업무 평가력", "평가가 따라오는 자리")
        organization_power = _section_topic_strength(section, "조직 적합도", "조직 안에서 자리 잡는 힘")
        authority_power = _section_topic_strength(section, "권한·책임 균형도", "권한과 책임의 균형")
        all_strong = min(recognition_power or 100, organization_power or 100, authority_power or 100) >= 80
        if authority_power >= 80 and "책임과 결정권의 불균형" in title:
            return True
        if recognition_power >= 80 and "공을 빼앗기는 조직 자리" in title:
            return True
        if (organization_power >= 80 or all_strong) and "기준 없는 조직에서의 소모" in title:
            return True
    if domains == {"love", "marriage"} or domains == {"love"} or domains == {"marriage"}:
        marriage_power = _section_topic_strength(section, "결혼 연결력", "혼인 성향", "결혼 안정성", "결혼이 안정되는 힘")
        relationship_power = _section_topic_strength(section, "관계 안정성", "관계가 오래 가는 힘")
        expression_power = _section_topic_strength(section, "애정 표현력", "애정이 표현되는 방식")
        if marriage_power >= 74 and "결혼 판단이 늦어지는 자리" in title:
            return True
        if relationship_power >= 80 and "지나간 서운함이 돌아오는 시기" in title:
            return True
        if expression_power >= 80 and "표현" in title and "늦" in title:
            return True
    return False


def _attach_premium_detail_sections(
    section: dict[str, Any],
    premium_detail_sections: list[dict[str, Any]],
) -> dict[str, Any]:
    domains = set(_premium_detail_domains_for_section(section))
    if not domains:
        return section
    if domains == {"personality"}:
        return section
    if domains == {"timing"}:
        return section
    details = []
    for detail in premium_detail_sections:
        if not isinstance(detail, dict) or str(detail.get("domain") or "") not in domains:
            continue
        normalized = _normalize_premium_detail(detail)
        if _premium_detail_conflicts_with_section(normalized, section):
            continue
        details.append(normalized)
    detail_limit = 3
    if domains == {"money"} or domains == {"career"}:
        detail_limit = 4
    details = sorted(details, key=lambda item: (-int(item.get("score") or 0), str(item.get("title") or "")))[:detail_limit]
    if not details:
        return section
    enriched = dict(section)
    enriched["premium_details"] = details

    def detail_block_from_detail(detail: dict[str, Any]) -> dict[str, Any] | None:
        title = str(detail.get("title") or "").strip()
        judgment = str(detail.get("judgment") or "").strip()
        scenes = [
            str(scene).strip()
            for scene in detail.get("event_scenes", [])
            if str(scene or "").strip()
        ][:3]
        if not title or not judgment:
            return None
        return _detail_block(title, judgment, scenes, tone=str(detail.get("level") or ""))

    detail_blocks = [
        block
        for block in (detail_block_from_detail(detail) for detail in details)
        if isinstance(block, dict)
    ]
    existing_blocks = list(enriched.get("detail_blocks") or [])
    if domains & {"money", "career", "love", "marriage"}:
        ordered_blocks = detail_blocks + existing_blocks
    else:
        ordered_blocks = existing_blocks + detail_blocks

    deduped_blocks: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for block in ordered_blocks:
        title = str(block.get("title") or "").strip()
        key = _compact_match_key(title)
        if key and key in seen_titles:
            continue
        if key:
            seen_titles.add(key)
        deduped_blocks.append(block)
    if deduped_blocks:
        enriched["detail_blocks"] = deduped_blocks
    existing = list(enriched.get("checkpoints") or [])
    for detail in details[:2]:
        title = str(detail.get("title") or "")
        judgment = str(detail.get("judgment") or "")
        if title and judgment:
            existing.append(f"{title}: {judgment}")
    enriched["checkpoints"] = existing
    return enriched


def _premium_visual_profile(section: dict[str, Any]) -> dict[str, Any]:
    domain = _domain_key(section)
    config = premium_category_contract(domain)
    topics = [topic for topic in section.get("topic_items") or [] if isinstance(topic, dict)]
    if not config or not topics:
        return {}
    by_title = {str(topic.get("title") or ""): topic for topic in topics}
    display_labels = config.get("display_labels") or {}
    picked: list[dict[str, Any]] = []
    for title in config.get("visual_slots", ()):
        topic = by_title.get(str(title))
        if topic:
            picked.append(topic)
    for topic in topics:
        if len(picked) >= 3:
            break
        if topic not in picked:
            picked.append(topic)
    items: list[dict[str, Any]] = []
    for topic in picked[:3]:
        source_label = str(topic.get("title") or "").strip()
        label = str(display_labels.get(source_label, source_label)).strip()
        value = str(topic.get("value") or "").strip()
        body = str(topic.get("body") or topic.get("definition") or "").strip()
        if not label:
            continue
        item: dict[str, Any] = {
            "label": label,
            "source_title": source_label,
            "value": value or "확인",
            "caption": body,
            "tone": str(topic.get("tone") or "neutral"),
        }
        if topic.get("score") is not None:
            item["score"] = topic.get("score")
        items.append(item)
    if not items:
        return {}
    return {
        "label": str(config.get("visual_label") or config.get("section_label") or ""),
        "headline": str(config.get("visual_headline") or ""),
        "items": items,
    }


def _compact_match_key(value: Any) -> str:
    return re.sub(r"[\s·ㆍ\-\(\)]+", "", str(value or "").strip())


def _premium_topic_lookup(section: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for topic in section.get("topic_items") or []:
        if not isinstance(topic, dict):
            continue
        title = str(topic.get("title") or "").strip()
        if not title:
            continue
        lookup[title] = topic
        lookup[_compact_match_key(title)] = topic
    return lookup


def _find_premium_topic(
    lookup: dict[str, dict[str, Any]],
    topic_title: Any,
    label: Any,
) -> dict[str, Any]:
    candidates = [str(topic_title or "").strip(), str(label or "").strip()]
    for candidate in candidates:
        if candidate and candidate in lookup:
            return lookup[candidate]
        compact = _compact_match_key(candidate)
        if compact and compact in lookup:
            return lookup[compact]
    for candidate in candidates:
        compact = _compact_match_key(candidate)
        if not compact:
            continue
        for key, topic in lookup.items():
            if compact in _compact_match_key(key) or _compact_match_key(key) in compact:
                return topic
    return {}


def _premium_reading_unit_topic(
    section: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
    raw_unit: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    topic = _find_premium_topic(lookup, raw_unit.get("topic"), label)
    if topic:
        return topic
    domain = _domain_key(section)
    topic_title = str(raw_unit.get("topic") or "").strip()
    combined = f"{topic_title} {label}"
    if domain == "timing" and "사건 주제" in combined:
        return _find_premium_topic(lookup, "두드러지는 영역", "주요 분야")
    if domain == "timing" and "과거 대조" in combined:
        return _find_premium_topic(lookup, "지나온 연도", "과거 대조")
    return {}


def _premium_reading_units(section: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = _premium_topic_lookup(section)
    units: list[dict[str, Any]] = []
    for raw_unit in contract.get("reading_units") or []:
        if not isinstance(raw_unit, dict):
            continue
        label = str(raw_unit.get("label") or "").strip()
        focus = str(raw_unit.get("focus") or "").strip()
        topic = _premium_reading_unit_topic(section, lookup, raw_unit, label)
        if not label:
            continue
        result = str(topic.get("body") or topic.get("definition") or "").strip()
        unit: dict[str, Any] = {
            "label": label,
            "display_label": str(raw_unit.get("display_label") or label).strip(),
            "topic": str(raw_unit.get("topic") or label).strip(),
            "focus": focus,
            "result": result or focus,
            "value": str(topic.get("value") or "").strip(),
            "tone": str(topic.get("tone") or "neutral"),
        }
        if topic.get("score") is not None:
            unit["score"] = topic.get("score")
        units.append(unit)
    return units


def _premium_unit_strength(unit: dict[str, Any]) -> int:
    score = unit.get("score")
    if isinstance(score, int):
        return max(0, min(100, score))
    return _section_value_strength(str(unit.get("value") or ""))


def _premium_unit_has_profile_signal(unit: dict[str, Any]) -> bool:
    if isinstance(unit.get("score"), int):
        return True
    if str(unit.get("value") or "").strip():
        return True
    return any(str(unit.get(key) or "").strip() for key in ("result", "body", "text", "focus"))


def _premium_unit_is_watch(unit: dict[str, Any]) -> bool:
    strength = _premium_unit_strength(unit)
    tone = str(unit.get("tone") or "")
    value = str(unit.get("value") or "")
    has_metric_value = isinstance(unit.get("score"), int) or bool(value.strip())
    label_text = " ".join(str(unit.get(key) or "") for key in ("label", "display_label", "title"))
    joined = " ".join(
        str(unit.get(key) or "")
        for key in ("label", "display_label", "title", "result", "body", "text", "focus", "value")
    )
    if (
        has_metric_value
        and strength >= 58
        and tone not in {"watch", "risk"}
        and any(marker in label_text for marker in ("방어", "안정성", "통제력", "운영력", "확보력"))
        and not any(marker in label_text for marker in ("부적합", "주의", "위험", "리스크"))
    ):
        return False
    return (has_metric_value and strength < 58) or tone in {"watch", "risk"} or any(
        marker in f"{value} {joined}"
        for marker in (
            "주의",
            "약세",
            "낮음",
            "부적합",
            "갈등",
            "손상",
            "위험",
            "리스크",
            "피해야",
            "권한 없이",
            "결정권이 없는",
        )
    )


def _premium_profile_third_label(unit: dict[str, Any]) -> str:
    if _premium_unit_is_watch(unit):
        return "주의점"
    if _premium_unit_strength(unit) >= 76:
        return "추가 강점"
    return "추가 내용"


def _premium_profile_third_tone(unit: dict[str, Any]) -> str:
    if _premium_unit_is_watch(unit):
        return "watch"
    if _premium_unit_strength(unit) >= 76:
        return "strong"
    return str(unit.get("tone") or "neutral")


def _premium_profile_grade(unit: dict[str, Any]) -> str:
    value = str(unit.get("value") or "")
    if _premium_unit_is_watch(unit):
        return value if value in {"주의 필요", "약세", "낮음"} else "주의 필요"
    return value


def _premium_unit_label(unit: dict[str, Any], fallback: str = "핵심 기준") -> str:
    return _premium_sentence_axis_label(unit.get("display_label") or unit.get("label") or fallback)


def _premium_unit_text(unit: dict[str, Any], fallback: str = "") -> str:
    text = str(unit.get("result") or unit.get("focus") or "").strip()
    return text or fallback


PREMIUM_PROFILE_WATCH_TEXT_MARKERS = (
    "조심",
    "주의",
    "손해",
    "손실",
    "부담",
    "지칠",
    "어렵",
    "늦",
    "흔들",
    "기대",
    "거절",
    "불리",
    "기울",
    "피로",
    "잃",
    "덜 남",
    "나뉘",
    "줄어",
    "지연",
    "전가",
    "떠안",
    "회수 과정",
    "구두 약속",
)

PREMIUM_POSITIVE_UNIT_DEFAULTS: dict[str, str] = {
    "재물 형성력": "금전 기회가 반복적으로 생기고, 시간이 갈수록 다루는 돈의 단위가 올라갑니다.",
    "수입 창출력": "직업 성과와 거래 대가가 실제 수입으로 연결됩니다.",
    "재주 수익화": "기술, 말, 콘텐츠, 서비스가 가격을 갖고 수입으로 전환됩니다.",
    "성과 보상력": "해낸 일의 대가가 금액으로 분명하게 환산됩니다.",
    "자산화 능력": "현금보다 권리와 소유권이 남는 자산에서 재산의 기반이 만들어집니다.",
    "공동자금 운영력": "공동 자금에서도 자기 몫과 명의를 끝까지 확인해야 합니다.",
    "계약·명의 안정성": "수령액, 지급일, 권리 조건을 남겨야 금전 권리가 흔들리지 않습니다.",
    "채권·미수금 회수력": "받아야 할 돈은 지급일과 회수 조건이 분명할 때 안정됩니다.",
    "사업 확장성": "거래 단위가 커질수록 재물 규모도 함께 넓어집니다.",
    "재정 방어력": "계약, 명의, 지분 배분을 분명히 해 큰 손실을 줄입니다.",
    "재물 주의 연도": "금전 판단이 흔들리는 해에는 계약과 지급일을 먼저 확인해야 합니다.",
    "직업 적성": "기준을 세우고 결과를 남기는 자리에서 직업운이 살아납니다.",
    "직업 분야": "운영, 기획, 관리, 분석처럼 기준을 세우는 분야와 잘 맞습니다.",
    "성취 축적력": "맡은 일이 이력과 성과로 남는 편입니다.",
    "평가·명예 전환력": "성과가 공식 평가와 평판으로 이어집니다.",
    "권한 확보력": "책임과 결정권이 함께 주어질 때 경력이 선명하게 남습니다.",
    "전문 자산화": "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다.",
    "조직 적응력": "조직 안에서 기준과 역할이 분명할수록 자리가 안정됩니다.",
    "업무 조건 감별력": "책임은 큰데 결정권이 없는 자리를 가려내야 경력 손실을 줄입니다.",
    "인연이 들어오는 길": "생활권 안에서 만남의 계기가 생깁니다.",
    "끌림의 기준": "능력과 안정감이 보이는 상대에게 마음이 움직입니다.",
    "인연 형성력": "생활권 안에서 만남의 계기가 생깁니다.",
    "관계 진전력": "호감이 생기면 관계가 실제 약속으로 넘어가기 쉽습니다.",
    "애정 표현성": "좋아하는 마음이 말과 행동으로 분명하게 드러납니다.",
    "애정이 표현되는 방식": "좋아하는 마음이 말과 행동으로 분명하게 드러납니다.",
    "관계 지속력": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "관계가 오래 가는 힘": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "주변 개입 관리력": "주변의 말과 과거 인연이 관계 안으로 들어올 때 기준을 지킵니다.",
    "결혼 연결력": "연애가 깊어지면 결혼 이야기가 현실로 옮겨집니다.",
    "결혼으로 이어지는 현실성": "연애가 깊어지면 공식적인 약속으로 옮겨집니다.",
    "혼인 성향": "결혼은 감정만이 아니라 생활과 책임의 결합으로 굳어집니다.",
    "배우자상": "성실하고 생활 기준이 분명한 상대와 오래 맞습니다.",
    "생활 안정": "주거, 생활비, 역할 기준이 맞을 때 결혼 생활이 안정됩니다.",
    "자녀·양육 책임": "자녀와 양육 문제는 역할과 비용 기준이 분명할 때 안정됩니다.",
    "함께 살아가는 기준": "생활 기준을 현실적으로 맞춥니다.",
    "호감 형성력": "새로운 만남에서 상대의 관심을 끌어냅니다.",
    "결혼 현실화": "연애가 깊어지면 결혼 이야기가 현실로 옮겨집니다.",
    "생활 조율력": "생활 기준을 현실적으로 맞춥니다.",
    "책임 경계력": "부탁과 책임이 섞일 때 떠안을 일과 거절할 일을 가릅니다.",
    "조력자 인연": "말뿐인 친분보다 실질적인 지원을 하는 사람을 남깁니다.",
    "인맥 형성력": "넓은 친분보다 오래 남는 실속 있는 관계가 강합니다.",
    "공동재 관리력": "공동 자금에서도 명의를 지켜 재산 손실을 막습니다.",
    "공동 자금 관리력": "공동 자금에서도 명의를 지켜 재산 손실을 막습니다.",
    "계약 안정성": "수령액, 지급일, 권리 조건을 문서로 확정해 손실을 줄입니다.",
    "권한 책임 균형도": "책임과 결정권이 함께 주어질 때 성과가 본인 경력으로 귀속됩니다.",
}

PREMIUM_PROFILE_SECONDARY_UNIT_LABELS: dict[str, set[str]] = {
    "money": {
        "자금 운용 안정성",
        "부채·보증 관리력",
        "가족재산 경계력",
        "채권·미수금 회수력",
        "재물 주의 연도",
        "후반 축재력",
    },
    "career": {
        "소속 전환력",
        "직업 전환 연도",
    },
    "love": {
        "정서 수용력",
        "주변 개입 관리력",
        "재회 가능성",
    },
    "marriage": {
        "생활비 기준성",
        "가족 변수",
        "배우자 가족 경계",
        "자녀·양육 책임",
    },
}


def _premium_text_reads_as_watch(text: str) -> bool:
    cleaned = str(text or "")
    return any(marker in cleaned for marker in PREMIUM_PROFILE_WATCH_TEXT_MARKERS)


def _premium_positive_unit_text(domain: str, unit: dict[str, Any], fallback: str = "") -> str:
    text = _premium_unit_text(unit, fallback)
    if _premium_unit_is_watch(unit):
        return text
    if text and not _premium_text_reads_as_watch(text):
        return text
    first_sentence = text.split(".", 1)[0].strip() if text else ""
    if first_sentence and not _premium_text_reads_as_watch(first_sentence):
        return f"{first_sentence}."
    label = _premium_unit_label(unit)
    default = PREMIUM_POSITIVE_UNIT_DEFAULTS.get(label)
    if default:
        return default
    focus = str(unit.get("focus") or "").strip()
    if focus:
        return f"{_with_subject_particle(label)} {focus}에서 분명하게 드러납니다."
    return f"{_with_subject_particle(label)} 실제 결과로 드러납니다."


def _premium_profile_insight_labels(domain: str) -> tuple[str, str, str, str]:
    labels = {
        "personality": ("성격 결론", "판단 강점", "주의 반응", "현실 운용"),
        "money": ("재물 결론", "수익 발생 지점", "재물 관리 지점", "자산화 방식"),
        "career": ("직업 결론", "평가 확보 지점", "경력 손실 지점", "직업 선택 기준"),
        "love": ("관계 결론", "관계 진전 지점", "관계 불안 지점", "장기 유지 기준"),
        "marriage": ("결혼 결론", "생활 안정 지점", "결혼 부담 지점", "결정 유지 기준"),
        "life": ("인생 구간 결론", "강세 구간", "전환기 관리", "구간별 기준"),
        "honor": ("명예 결론", "공식 인정 지점", "평판 손상 지점", "명예 관리 기준"),
        "social": ("대인관계 결론", "신뢰 형성 방식", "관계 부담 지점", "관계 운용 기준"),
        "timing": ("연도 결론", "좋은 연도", "주의 연도", "과거 대조"),
    }
    return labels.get(domain, ("핵심 결론", "강점", "주의점", "적용 기준"))


def _premium_profile_strength_body(domain: str, axis: str, fallback: str) -> str:
    mapped = {
        "money": {
            "수익 전환력": "성과가 보수로 확정되는 재물운입니다.",
            "자산 축적력": "수입을 소유권 있는 자산으로 바꿀 때 재산의 기반이 만들어집니다.",
            "재물 형성력": "직업 성과와 거래에서 수입이 직접 형성됩니다.",
            "공동 자금 관리력": "공동 자금에서도 명의를 분명히 할 때 불리한 책임을 줄입니다.",
            "계약 안정성": "지급일이 분명할수록 수령액이 안정됩니다.",
        },
        "career": {
            "전문성 축적도": "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다.",
            "평가 확보력": "결과물이 공식 평가와 추천으로 이어집니다.",
            "성과 구현력": "맡은 일을 결과물로 끝까지 마무리합니다.",
            "조직 적응력": "조직 안에서 역할과 기준이 분명할 때 자기 자리가 생깁니다.",
            "권한 책임 균형도": "책임과 결정권이 함께 주어질 때 성취가 본인 이력으로 남습니다.",
        },
        "love": {
            "결혼 현실화": "관계가 깊어지면 결혼 이야기가 현실로 옮겨집니다.",
            "관계 지속력": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
            "호감 형성력": "만남의 시작과 호감 형성이 빠르게 일어납니다.",
            "애정 표현력": "호감이 생기면 표현이 분명해집니다.",
            "생활 조율력": "생활 기준이 맞는 관계에서 결혼 이야기가 빨리 구체화됩니다.",
        },
        "marriage": {
            "결혼 안정성": "주거 문제가 정해질수록 결혼이 안정됩니다.",
            "생활 안정성": "감정보다 생활 기반이 맞아야 결혼이 오래 갑니다.",
            "가족 책임 수용력": "결혼 뒤 가족 책임을 직접 맡는 일이 많아집니다.",
            "결정 지속력": "한 번 정한 약속을 오래 유지하는 편입니다.",
        },
    }
    return mapped.get(domain, {}).get(axis, fallback)


def _premium_profile_watch_body(domain: str, axis: str, fallback: str) -> str:
    mapped = {
        "money": {
            "공동 자금 관리력": "가까운 사람과 자금을 섞으면 명의와 지분이 상대 쪽으로 기울기 쉽습니다.",
            "계약 안정성": "문서 기준이 약하면 지급일과 수령액이 흔들립니다.",
            "자산 축적력": "수입이 늘어도 자산으로 전환하지 못하면 보유 금액이 약해집니다.",
        },
        "career": {
            "권한 책임 균형도": "책임은 늘지만 결정권이 약한 자리는 경력에 흠이 남습니다.",
            "조직 적응력": "기준 없는 조직에서는 성과보다 책임 전가가 먼저 남습니다.",
            "평가 확보력": "성과가 있어도 기록과 추천 체계가 없으면 평가가 늦어집니다.",
        },
        "love": {
            "애정 표현력": "마음이 깊어도 표현이 늦으면 상대는 확신을 갖기 어렵습니다.",
            "관계 지속력": "서운함을 오래 넘기면 관계가 한 번에 식을 수 있습니다.",
            "생활 조율력": "생활 기준이 어긋나면 감정이 깊어도 관계가 쉽게 지칩니다.",
        },
        "marriage": {
            "생활 안정성": "주거 조건이 어긋나면 결혼 생활이 흔들립니다.",
            "가족 책임 수용력": "가족 문제가 부부 사이로 들어오면 책임 부담도 함께 따라옵니다.",
            "결정 지속력": "결혼 결정을 자주 미루면 상대가 불안을 크게 느낍니다.",
        },
    }
    return mapped.get(domain, {}).get(axis, fallback)


def _premium_profile_application_body(domain: str, axis: str, fallback: str) -> str:
    mapped = {
        "money": {
            "자산 축적력": "재산은 소유권이 남는 형태로 만들어집니다.",
            "수익 전환력": "수익 규모가 달라지는 시점에는 보수를 먼저 확정해야 합니다.",
            "계약 안정성": "큰 금액일수록 구두 약속보다 문서와 지급 조건이 먼저입니다.",
            "공동 자금 관리력": "가까운 사람과의 금전 관계일수록 명의를 처음에 분명히 해야 합니다.",
        },
        "career": {
            "평가 확보력": "직함보다 결정권이 분명한 자리에서 경력이 강해집니다.",
            "전문성 축적도": "넓은 경험보다 한 분야의 자격이 경력을 키웁니다.",
            "권한 책임 균형도": "맡은 일의 범위와 결정권이 같이 주어져야 성과가 본인 이름으로 남습니다.",
        },
        "love": {
            "관계 지속력": "호감이 생긴 뒤에는 표현 속도가 관계의 안정성을 가릅니다.",
            "애정 표현력": "마음이 있어도 표현을 미루면 상대는 확신을 늦게 얻습니다.",
            "결혼 현실화": "관계가 깊어지면 주거 문제가 먼저 현실로 올라옵니다.",
        },
        "marriage": {
            "생활 안정성": "결혼은 주거 기준이 맞을 때 생활 안정성이 유지됩니다.",
            "결정 지속력": "결혼은 감정보다 결정 이후의 유지력이 더 크게 남습니다.",
            "가족 책임 수용력": "가족 책임이 늘어나는 시기에는 배우자와 역할을 미리 나눠야 합니다.",
        },
    }
    return mapped.get(domain, {}).get(axis, fallback)


def _premium_profile_insights(
    domain: str,
    profile_type: str,
    summary: str,
    strong: dict[str, Any],
    weak: dict[str, Any],
    support: dict[str, Any],
) -> list[dict[str, Any]]:
    conclusion_label, strength_label, watch_label, application_label = _premium_profile_insight_labels(domain)
    strong_axis = _premium_unit_label(strong)
    support_axis = _premium_unit_label(support)
    weak_axis = _premium_unit_label(weak)
    strong_text = _premium_positive_unit_text(domain, strong)
    support_text = _premium_positive_unit_text(domain, support)
    weak_is_watch = _premium_unit_is_watch(weak)
    weak_text = _premium_unit_text(weak) if weak_is_watch else _premium_positive_unit_text(domain, weak)
    strong_text = _premium_profile_strength_body(domain, strong_axis, strong_text)
    support_text = _premium_profile_strength_body(domain, support_axis, support_text)
    if not weak_is_watch:
        positive_third_labels = {
            "personality": "추가 성격 내용",
            "money": "추가 재물 내용",
            "career": "추가 직업 내용",
            "love": "추가 관계 내용",
            "marriage": "추가 결혼 내용",
            "life": "추가 생애 내용",
            "honor": "추가 명예 내용",
            "social": "추가 대인 내용",
            "timing": "추가 시기 내용",
        }
        watch_label = positive_third_labels.get(domain, "추가 내용")

    application_defaults = {
        "personality": "중요한 선택에서는 감정 반응보다 본인이 확인한 기준을 먼저 세울 때 안정됩니다.",
        "money": "수입과 거래가 커질수록 몫의 기준에서 손익이 정해집니다.",
        "career": "직함보다 역할, 권한, 평가 기준이 분명한 자리에서 경력이 가장 강해집니다.",
        "love": "호감이 생긴 뒤에는 표현 방식과 만나는 속도가 관계의 안정성을 가릅니다.",
        "marriage": "결혼은 주거 기준이 맞을 때 생활 안정성이 유지됩니다.",
        "life": "인생 구간이 바뀌는 때에는 익숙한 방식보다 새로 맡는 역할이 먼저 드러납니다.",
        "honor": "명예가 붙는 자리에서는 이름보다 책임 범위와 마무리 기준을 먼저 잡아야 합니다.",
        "social": "가까운 관계일수록 호의와 책임의 선을 분명히 해야 오래 갑니다.",
    }
    watch_defaults = {
        "personality": f"{weak_axis}{_topic_particle(weak_axis)} 중요한 선택 앞에서 판단이 흔들리거나 감정 소모가 남는 지점입니다.",
        "money": f"{weak_axis}{_topic_particle(weak_axis)} 수입이 늘어난 뒤 실제로 빠져나가는 금액과 손실 가능성을 가르는 기준입니다.",
        "career": f"{weak_axis}{_topic_particle(weak_axis)} 실력이 평가와 보상으로 바뀌는 과정에서 막히기 쉬운 지점입니다.",
        "love": f"{weak_axis}{_topic_particle(weak_axis)} 마음이 있어도 상대가 거리감을 먼저 느끼는 장면입니다.",
        "marriage": f"{weak_axis}{_topic_particle(weak_axis)} 감정이 깊어진 뒤 생활 문제가 부담으로 올라오는 지점입니다.",
        "life": f"{weak_axis}{_topic_particle(weak_axis)} 인생 구간이 바뀔 때 역할, 거처, 책임 범위를 다시 정하게 만드는 기준입니다.",
        "honor": f"{weak_axis}{_topic_particle(weak_axis)} 이름이 알려진 뒤 그 평판을 얼마나 오래 지키는지를 가르는 기준입니다.",
        "social": f"{weak_axis}{_topic_particle(weak_axis)} 가까운 사람의 부탁이 어디까지 책임으로 넘어오는지를 보여주는 기준입니다.",
    }
    watch_text = weak_text or watch_defaults.get(domain, "")
    watch_text = (
        _premium_profile_watch_body(domain, weak_axis, watch_text)
        if weak_is_watch
        else _premium_profile_strength_body(domain, weak_axis, watch_text)
    )
    application_body = _premium_profile_application_body(
        domain,
        support_axis,
        application_defaults.get(domain, support_text),
    )
    return [
        {
            "label": conclusion_label,
            "value": profile_type,
            "body": summary,
            "tone": "strong",
        },
        {
            "label": strength_label,
            "value": strong_axis,
            "body": strong_text,
            "tone": str(strong.get("tone") or "strong"),
        },
        {
            "label": watch_label,
            "value": weak_axis,
            "body": watch_text,
            "tone": "watch" if weak_is_watch else "neutral",
        },
        {
            "label": application_label,
            "value": support_axis,
            "body": application_body,
            "tone": "neutral",
        },
    ]


def _has_final_consonant(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    char = stripped[-1]
    code = ord(char)
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _with_subject_particle(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return value + ("이" if _has_final_consonant(value) else "가")


def _with_object_particle(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return value + ("을" if _has_final_consonant(value) else "를")


def _premium_sentence_axis_label(label: Any) -> str:
    value = str(label or "").strip()
    if not value:
        return "주요 항목"
    axis_labels = {
        "재물 발생": "타고난 재물의 그릇",
        "재물 발생력": "타고난 재물의 그릇",
        "재물 형성": "타고난 재물의 그릇",
        "재물 형성력": "타고난 재물의 그릇",
        "수입 전환": "수입 발생력",
        "수입 창출": "수입 발생력",
        "수입 창출력": "수입 발생력",
        "수익 전환": "수입 발생력",
        "수익 전환력": "수입 발생력",
        "축재": "자산 확정력",
        "축재력": "자산 확정력",
        "자산 축적": "자산 확정력",
        "자산 축적력": "자산 확정력",
        "공동 자금": "공동 자금 안정성",
        "공동 자금 운영력": "공동 자금 안정성",
        "공동재 관리": "공동 자금 안정성",
        "공동재 관리력": "공동 자금 안정성",
        "계약 안정": "계약·명의 안정성",
        "계약 안정성": "계약·명의 안정성",
        "계약·문서": "계약·명의 안정성",
        "계약·문서 안정성": "계약·명의 안정성",
        "성과": "직업적 성취의 그릇",
        "성과 증명": "직업적 성취의 그릇",
        "성과 구현": "직업적 성취의 그릇",
        "성과 구현력": "직업적 성취의 그릇",
        "직업 성취력": "직업적 성취의 그릇",
        "평가": "평가가 따라오는 자리",
        "평가 상승": "평가가 따라오는 자리",
        "업무 평가력": "평가가 따라오는 자리",
        "평가 확보": "평가가 따라오는 자리",
        "평가 확보력": "평가가 따라오는 자리",
        "조직 적합": "조직 안에서 자리 잡는 힘",
        "조직 적합도": "조직 안에서 자리 잡는 힘",
        "조직 적응": "조직 안에서 자리 잡는 힘",
        "조직 적응력": "조직 안에서 자리 잡는 힘",
        "권한과 책임": "권한과 책임의 균형",
        "권한·책임 균형도": "권한과 책임의 균형",
        "권한 책임 균형도": "권한과 책임의 균형",
        "전문성": "전문성으로 남는 힘",
        "전문성 축적도": "전문성으로 남는 힘",
        "인연 형성": "인연 형성력",
        "인연이 들어오는 길": "인연 형성력",
        "호감 형성": "인연 형성력",
        "호감 형성력": "인연 형성력",
        "애정 표현": "애정 표현성",
        "애정이 표현되는 방식": "애정 표현성",
        "애정 표현력": "애정 표현성",
        "관계 안정": "관계 지속력",
        "관계가 오래 가는 힘": "관계 지속력",
        "관계 안정성": "관계 지속력",
        "관계 지속": "관계 지속력",
        "결혼으로 이어지는 현실성": "결혼 현실성",
        "결혼 현실화": "결혼 연결력",
        "생활 기준": "생활 안정성",
        "함께 살아가는 기준": "생활 안정성",
        "생활 조율력": "생활 안정성",
        "결혼 안정": "혼인 성향",
        "결혼이 안정되는 힘": "혼인 성향",
        "결혼 안정성": "혼인 성향",
        "생활 안정": "생활 안정",
        "생활 기반이 잡히는 방식": "생활 안정",
        "생활 기반 안정성": "생활 안정",
        "가족 책임": "가족 변수",
        "가족 책임감": "가족 변수",
        "가족 책임 수용력": "가족 변수",
        "결정 지속": "결혼 지속력",
        "결정 지속력": "결혼 지속력",
        "초년 형성": "초년에 형성되는 바탕",
        "초년 기반": "초년에 형성되는 바탕",
        "초년 형성도": "초년에 형성되는 바탕",
        "중년 성취": "중년에 굳어지는 성취",
        "중년 성취도": "중년에 굳어지는 성취",
        "말년 안정": "말년에 남는 안정",
        "말년 안정도": "말년에 남는 안정",
        "대운 전환": "운이 바뀌는 전환기",
        "전환기": "운이 바뀌는 전환기",
        "전환기 대응력": "운이 바뀌는 전환기",
        "사회적 인정": "공적 인정 기반",
        "사회적 인정도": "공적 인정 기반",
        "사회적 인정이 붙는 자리": "공적 인정 기반",
        "평가가 직함으로 이어지는 자리": "직책 상승력",
        "권한이 붙을수록 커지는 평판": "권한 기반 평판",
        "평판 유지": "평판이 오래 남는 힘",
        "평판 유지력": "평판이 오래 남는 힘",
        "평판 지속력": "평판이 오래 남는 힘",
        "공식 역할": "공식 책임을 맡는 힘",
        "공식 역할 수용력": "공식 책임을 맡는 힘",
        "공식 책임 수행력": "공식 책임을 맡는 힘",
        "명예 관리": "명예를 지켜내는 기준",
        "평판 관리": "명예를 지켜내는 기준",
        "명예 관리력": "명예를 지켜내는 기준",
        "사람을 얻는 방식": "사람을 얻는 힘",
        "인맥 형성": "사람을 얻는 힘",
        "인맥 형성력": "사람을 얻는 힘",
        "도움이 되는 사람": "도움으로 이어지는 인연",
        "조력자 인연": "도움으로 이어지는 인연",
        "부탁과 책임": "부탁과 책임의 경계",
        "책임 경계력": "부탁과 책임의 경계",
        "판단 기준": "판단 기준",
        "대인 거리": "대인 조율감",
        "대인 거리감": "대인 조율감",
        "대인 조율감": "대인 조율감",
        "감정 반응": "감정 반응성",
        "감정 반응성": "감정 반응성",
        "압박 반응": "압박 대응력",
        "압박 대응": "압박 대응력",
        "압박 대응력": "압박 대응력",
        "행동 속도": "실행 속도",
        "실행 속도": "실행 속도",
        "관심 방향": "관심 방향성",
        "관심 몰입": "관심 몰입도",
        "관심 몰입도": "관심 몰입도",
    }
    return axis_labels.get(value, value)


def _premium_section_profile_type(domain: str, strong: dict[str, Any], weak: dict[str, Any]) -> str:
    strong_label = str(strong.get("label") or "")
    weak_label = str(weak.get("label") or "")
    weak_score = _premium_unit_strength(weak)
    type_maps = {
        "personality": {
            "판단 기준": "자기 기준이 강한 성향",
            "대인 거리": "관계의 거리를 조절하는 성향",
            "대인 거리감": "관계의 거리를 조절하는 성향",
            "감정 반응": "감정을 관찰한 뒤 움직이는 성향",
            "압박 반응": "압박 앞에서 버티는 성향",
            "압박 대응": "압박 앞에서 버티는 성향",
            "행동 속도": "생각보다 실행으로 판단하는 성향",
            "관심 방향": "한 분야에 깊게 몰입하는 성향",
            "관심 몰입": "한 분야에 깊게 몰입하는 성향",
        },
        "money": {
            "재물 발생": "재물이 형성되는 힘이 강한 사주",
            "재물 형성": "재물이 형성되는 힘이 강한 사주",
            "타고난 재물의 그릇": "큰 금액을 다루는 재물형 사주",
            "수입 전환": "성과가 수입으로 돌아오는 사주",
            "수입 창출": "성과가 수입으로 돌아오는 사주",
            "재물이 들어오는 길": "성과가 수입으로 돌아오는 사주",
            "수입 발생력": "성과가 수입으로 돌아오는 사주",
            "축재": "자산을 남기는 힘이 있는 사주",
            "자산 축적": "자산을 남기는 힘이 있는 사주",
            "재산으로 굳어지는 힘": "자산을 남기는 힘이 있는 사주",
            "자산 확정력": "자산을 남기는 힘이 있는 사주",
            "공동 자금": "공동 자금 관리가 중요한 사주",
            "재물에 얽히는 사람 문제": "공동 자금 관리가 중요한 사주",
            "공동 자금 안정성": "공동 자금 관리가 중요한 사주",
            "계약 안정": "계약 기준이 재물을 지키는 사주",
            "계약·문서": "계약 기준이 재물을 지키는 사주",
            "돈을 지켜내는 기준": "계약 기준이 재물을 지키는 사주",
            "계약·명의 안정성": "재정 방어력 중심형",
            "투자·거래 판단력": "거래 판단이 재물을 지키는 사주",
            "자금 운용 안정성": "재정 관리가 중요한 사주",
            "부채·보증 관리력": "채무와 보증에서 기준이 필요한 사주",
            "가족재산 경계력": "가족 재산의 경계가 중요한 사주",
            "확장 가능성": "사업성과 거래성이 붙는 사주",
        },
        "career": {
            "성과": "성과를 증명해 올라가는 사주",
            "성과 증명": "성과를 증명해 올라가는 사주",
            "평가": "평가와 평판이 따르는 사주",
            "평가 상승": "평가와 평판이 따르는 사주",
            "조직 적합": "조직 안에서 자기 자리가 생기는 사주",
            "조직 적응": "조직 안에서 자기 자리가 생기는 사주",
            "조직 안에서 자리 잡는 힘": "조직 안에서 자기 자리가 생기는 사주",
            "권한과 책임": "책임과 권한이 맞아야 이력이 남는 사주",
            "전문성": "전문성으로 경력이 남는 사주",
            "전문성으로 남는 힘": "전문성으로 경력이 남는 사주",
            "직업적 성취의 그릇": "직업 성취가 분명한 사주",
            "평가가 따라오는 자리": "평가와 평판이 따르는 사주",
        },
        "love": {
            "인연 형성": "인연이 빠르게 열리는 사주",
            "인연이 들어오는 길": "인연이 빠르게 열리는 사주",
            "애정 표현": "표현이 관계를 움직이는 사주",
            "애정이 표현되는 방식": "표현이 관계를 움직이는 사주",
            "관계 안정": "깊어진 인연이 오래 가는 사주",
            "관계가 오래 가는 힘": "깊어진 인연이 오래 가는 사주",
            "결혼 현실화": "연애가 공식 약속으로 옮겨지는 사주",
            "결혼으로 이어지는 현실성": "연애가 공식 약속으로 옮겨지는 사주",
            "생활 기준": "생활 기준이 관계를 굳히는 사주",
            "함께 살아가는 기준": "생활 기준이 관계를 굳히는 사주",
        },
        "marriage": {
            "결혼 안정": "결혼 생활이 안정되는 사주",
            "생활 안정": "생활 기반이 결혼을 지키는 사주",
            "가족 책임": "가족 책임을 안고 가는 사주",
            "결정 지속": "한 번 정한 약속을 오래 지키는 사주",
        },
        "life": {
            "초년 형성": "초년부터 자기 기준이 선명한 사주",
            "초년 기반": "초년부터 자기 기준이 선명한 사주",
            "초년에 형성되는 바탕": "초년부터 자기 기준이 선명한 사주",
            "중년 성취": "중년 이후 성취가 이력과 자산으로 남는 사주",
            "중년에 커지는 성취": "중년 이후 성취가 이력과 자산으로 남는 사주",
            "중년에 굳어지는 성취": "중년 이후 성취가 이력과 자산으로 남는 사주",
            "말년 안정": "말년으로 갈수록 안정이 남는 사주",
            "말년에 남는 안정": "말년으로 갈수록 안정이 남는 사주",
            "대운 전환": "운이 바뀔 때 삶의 무대가 달라지는 사주",
            "전환기": "운이 바뀔 때 삶의 무대가 달라지는 사주",
            "운이 바뀌는 전환기": "운이 바뀔 때 삶의 무대가 달라지는 사주",
        },
        "honor": {
            "사회적 인정": "책임 있는 자리에서 이름이 남는 사주",
            "공적 인정 기반": "책임 있는 자리에서 이름이 남는 사주",
            "사회적 인정이 붙는 자리": "책임 있는 자리에서 이름이 남는 사주",
            "직책 상승력": "평가가 직책으로 굳어지는 사주",
            "권한 기반 평판": "권한이 커질수록 이름값이 올라가는 사주",
            "평판 유지": "평판이 오래 남는 사주",
            "평판이 오래 남는 힘": "평판이 오래 남는 사주",
            "공식 책임을 맡는 힘": "책임 있는 자리에서 이름이 남는 사주",
            "공식 역할": "책임 있는 자리에서 이름이 남는 사주",
            "공식 역할 수용력": "책임 있는 자리에서 이름이 남는 사주",
            "공식 책임 수행력": "책임 있는 자리에서 이름이 남는 사주",
            "명예 관리": "명예를 관리해야 오래 가는 사주",
            "명예를 지켜내는 기준": "명예를 관리해야 오래 가는 사주",
            "평판 관리": "명예를 관리해야 오래 가는 사주",
        },
        "social": {
            "사람을 얻는 방식": "사람을 신중하게 고르는 사주",
            "인맥 형성": "사람을 신중하게 고르는 사주",
            "사람을 얻는 힘": "인맥이 실제 기회로 이어지는 사주",
            "도움이 되는 사람": "도움 받을 인연이 붙는 사주",
            "조력자 인연": "도움 받을 인연이 붙는 사주",
            "도움으로 이어지는 인연": "도움 받을 인연이 붙는 사주",
            "관계가 오래 남는 힘": "오래 쌓은 신뢰가 실제 제안으로 돌아오는 사주",
            "관계 지속": "오래 쌓은 신뢰가 실제 제안으로 돌아오는 사주",
            "관계 지속력": "오래 쌓은 신뢰가 실제 제안으로 돌아오는 사주",
            "부탁과 책임": "부탁과 책임의 선이 중요한 사주",
            "부탁과 책임의 경계": "부탁과 책임의 선이 중요한 사주",
        },
    }
    base = type_maps.get(domain, {}).get(strong_label) or f"{strong_label or '종합'} 중심형"
    caution_maps = {
        "money": {
            "공동 자금": "공동 자금에서 손실을 보기 쉬운 사주",
            "재물에 얽히는 사람 문제": "공동 자금에서 손실을 보기 쉬운 사주",
            "공동 자금 안정성": "공동 자금에서 손실을 보기 쉬운 사주",
            "계약 안정": "계약 문서에서 손해를 조심할 사주",
            "계약·문서": "계약 문서에서 손해를 조심할 사주",
            "돈을 지켜내는 기준": "계약 문서에서 손해를 조심할 사주",
            "계약·명의 안정성": "계약 문서에서 손해를 조심할 사주",
            "축재": "자산 보존을 따로 챙겨야 하는 사주",
            "자산 축적": "자산 보존을 따로 챙겨야 하는 사주",
            "재산으로 굳어지는 힘": "자산 보존을 따로 챙겨야 하는 사주",
            "자산 확정력": "자산 보존을 따로 챙겨야 하는 사주",
        },
        "career": {
            "권한과 책임": "권한 없는 책임을 조심할 사주",
            "조직 적합": "조직 소모를 조심할 사주",
            "조직 적응": "조직 소모를 조심할 사주",
            "평가": "평가 지연을 조심할 사주",
            "평가 상승": "평가 지연을 조심할 사주",
        },
        "love": {
            "애정 표현": "표현 지연을 조심할 사주",
            "관계 안정": "관계 냉각을 조심할 사주",
            "생활 기준": "생활 충돌을 조심할 사주",
        },
        "personality": {
            "판단 기준": "판단이 늦어질 때가 있는 성향",
            "대인 거리": "관계의 선을 분명히 해야 하는 성향",
            "대인 거리감": "관계의 선을 분명히 해야 하는 성향",
            "감정 반응": "감정 표현이 늦어질 때가 있는 성향",
            "압박 반응": "압박에 예민해질 때가 있는 성향",
            "압박 대응": "압박에 예민해질 때가 있는 성향",
            "행동 속도": "실행이 늦어질 때가 있는 성향",
            "관심 몰입": "관심이 흩어질 때가 있는 성향",
        },
        "social": {
            "관계 지속": "관계 단절을 조심할 사주",
            "부탁과 책임": "과한 부탁을 조심할 사주",
        },
    }
    caution = caution_maps.get(domain, {}).get(weak_label)
    if caution and weak_score < 58 and caution not in base:
        return f"{base} · {caution}"
    return base


def _premium_unit_result_sentence(unit: dict[str, Any]) -> str:
    text = str(unit.get("result") or unit.get("focus") or "").strip()
    if not text:
        label = _premium_sentence_axis_label(unit.get("label") or "")
        value = str(unit.get("value") or "").strip()
        return f"{label}{_subject_particle(label)} {value}입니다." if value else ""
    first = text.split(".", 1)[0].strip()
    if not first:
        return ""
    return first + "."


def _premium_unit_result_sentence_for_domain(domain: str, unit: dict[str, Any]) -> str:
    if not unit:
        return ""
    text = _premium_positive_unit_text(domain, unit)
    first = text.split(".", 1)[0].strip()
    if first:
        return first + "."
    return _premium_unit_result_sentence(unit)


def _join_profile_sentences(*parts: str) -> str:
    sentences: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = str(part or "").strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        sentences.append(text)
    return " ".join(sentences)


def _drop_repeated_keyword_sentences(base: str, extra: str, keywords: tuple[str, ...]) -> str:
    base_text = str(base or "")
    sentences = [sentence.strip() for sentence in str(extra or "").split(".") if sentence.strip()]
    kept: list[str] = []
    for sentence in sentences:
        if any(keyword and keyword in base_text and keyword in sentence for keyword in keywords):
            continue
        kept.append(sentence + ".")
    return " ".join(kept)


def _profile_sentence_repeats_type(profile_type: str, sentence: str) -> bool:
    type_text = str(profile_type or "")
    sentence_text = str(sentence or "")
    if not type_text or not sentence_text:
        return False
    for keyword in ("초년", "중년", "말년", "전환", "책임", "명예", "신뢰", "인맥", "결혼", "전문성"):
        if keyword in type_text and keyword in sentence_text:
            return True
    return False


def _premium_section_profile_summary(
    domain: str,
    strong: dict[str, Any],
    weak: dict[str, Any],
    support: dict[str, Any] | None = None,
) -> str:
    strong_label = str(strong.get("label") or "강한 기준")
    weak_label = str(weak.get("label") or "주의점")
    strong_axis = _premium_sentence_axis_label(strong_label)
    weak_axis = _premium_sentence_axis_label(weak_label)
    weak_score = _premium_unit_strength(weak)
    strong_sentence = _premium_unit_result_sentence_for_domain(domain, strong)
    support_sentence = _premium_unit_result_sentence_for_domain(domain, support or {})
    weak_sentence = _premium_unit_result_sentence(weak) if _premium_unit_is_watch(weak) else _premium_unit_result_sentence_for_domain(domain, weak)
    if domain == "money":
        opening = _premium_domain_lead_opening(domain, _premium_unit_label(strong))
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        ) or opening
    if domain == "career":
        opening = _premium_domain_lead_opening(domain, _premium_unit_label(strong))
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        ) or opening
    if domain in {"love", "marriage"}:
        opening = _premium_domain_lead_opening(domain, _premium_unit_label(strong))
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        ) or opening
    if domain == "personality":
        base = _join_profile_sentences(strong_sentence, support_sentence)
        if weak_score < 58:
            return _join_profile_sentences(base, weak_sentence or f"{weak_axis}{_topic_particle(weak_axis)} 선택이 늦어지거나 태도가 번복되는 지점입니다.")
        return base or f"성격은 {_with_object_particle(strong_axis)} 중심으로 드러납니다. {weak_axis}도 안정적이라 판단과 태도가 쉽게 번복되지 않습니다."
    if domain == "life":
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        )
    if domain == "honor":
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        )
    if domain == "social":
        return _premium_profile_compact_lead(
            domain,
            _premium_unit_label(strong),
            _premium_unit_label(support or {}),
            weak_label if _premium_unit_is_watch(weak) or weak_score < 58 else "",
        )
    return f"{_with_subject_particle(strong_axis)} 가장 선명합니다. {weak_axis}에서는 부담이 따로 드러납니다."


def _premium_timing_event_body(event: dict[str, Any], *, kind: str, fallback: str) -> str:
    """Return the visible consequence of a selected timing event."""

    product_line = str(event.get("productLine") or "").strip()
    if product_line:
        return product_line if product_line.endswith(".") else product_line + "."
    decision_line = str(event.get("decisionLine") or "").strip()
    if decision_line:
        return decision_line.replace("연도", "해") + "입니다."
    title = str(event.get("title") or fallback or "").strip()
    if not title:
        return "해당 연도의 사건성이 분명하게 드러납니다."
    if kind == "good":
        return f"{title}{_subject_particle(title)} 실제 성과로 남는 해입니다."
    return f"{title}{_subject_particle(title)} 손실이나 부담으로 남기 쉬운 해입니다."


def _timing_event_clause(keyword: str, *, kind: str) -> str:
    """Translate a timing keyword into a short customer-facing clause."""

    text = str(keyword or "").strip().rstrip(".")
    if not text:
        return ""
    if kind == "good":
        mapped = TIMING_GOOD_CARD_CLAUSES.get(text)
        return mapped or f"{_with_subject_particle(text)} 중심 사건으로 남습니다"
    mapped = TIMING_CAUTION_CARD_CLAUSES.get(text)
    return mapped or f"{_with_subject_particle(text)} 문제로 올라옵니다"


def _timing_event_connective_clause(clause: str) -> str:
    text = str(clause or "").strip().rstrip(".")
    replacements = (
        ("합니다", "하고"),
        ("받습니다", "받고"),
        ("들어옵니다", "들어오고"),
        ("달라집니다", "달라지고"),
        ("확장됩니다", "확장되고"),
        ("분명해집니다", "분명해지고"),
        ("올라갑니다", "올라가고"),
        ("넘어갑니다", "넘어가고"),
        ("구체화됩니다", "구체화되고"),
        ("확정됩니다", "확정되고"),
        ("남습니다", "남고"),
        ("두드러집니다", "두드러지고"),
    )
    for suffix, replacement in replacements:
        if text.endswith(suffix):
            return text[: -len(suffix)] + replacement
    return text


def _timing_topic_card_body(topic: str, good_keyword: str, caution_keyword: str) -> str:
    """Return the summary card sentence for the main timing field."""

    topic_text = str(topic or "").strip() or "주요 영역"
    good_clause = _timing_event_clause(good_keyword, kind="good")
    caution_clause = _timing_event_clause(caution_keyword, kind="watch")
    sentences = [f"연도별 사건은 {topic_text}에서 가장 선명합니다."]
    if good_clause and caution_clause:
        sentences.append(
            f"상승 연도에는 {_timing_event_connective_clause(good_clause)}, 주의 연도에는 {caution_clause}."
        )
    elif good_clause:
        sentences.append(f"상승 연도에는 {good_clause}.")
    elif caution_clause:
        sentences.append(f"주의 연도에는 {caution_clause}.")
    return " ".join(sentences)


def _premium_section_profile(section: dict[str, Any]) -> dict[str, Any]:
    contract = section.get("category_contract") if isinstance(section.get("category_contract"), dict) else {}
    units = [unit for unit in contract.get("reading_units") or [] if isinstance(unit, dict) and unit.get("label")]
    if not units:
        return {}
    domain = _domain_key(section)
    if domain == "timing":
        timing_map = section.get("timing_map") if isinstance(section.get("timing_map"), dict) else {}
        highlight_good = next((item for item in timing_map.get("goodHighlights") or [] if isinstance(item, dict)), {})
        highlight_caution = next((item for item in timing_map.get("cautionHighlights") or [] if isinstance(item, dict)), {})
        good = next((unit for unit in units if unit.get("label") == "좋은 연도"), units[0])
        caution = next((unit for unit in units if unit.get("label") == "주의 연도"), units[-1])
        topic = next((unit for unit in units if unit.get("label") == "사건 주제"), {})
        past = next((unit for unit in units if unit.get("label") == "과거 대조"), {})

        def primary_value(unit: dict[str, Any]) -> str:
            return str(unit.get("value") or "").split("/", 1)[0].strip()

        def event_value(event: dict[str, Any]) -> str:
            year = f"{event.get('year')}년" if event.get("year") else ""
            age = str(event.get("ageLabel") or "").strip()
            title = str(event.get("title") or "").strip()
            prefix = f"{year}({age})" if year and age else year
            return " ".join(part for part in (prefix, title) if part)

        def event_keywords(event: dict[str, Any]) -> str:
            items = [str(item).strip() for item in event.get("keywordItems") or [] if str(item).strip()]
            return items[0] if items else ""

        good_value = event_value(highlight_good) or primary_value(good)
        caution_value = event_value(highlight_caution) or primary_value(caution)
        past_value = primary_value(past)
        good_text = event_keywords(highlight_good) or str(good.get("result") or "성과").strip()
        caution_text = event_keywords(highlight_caution) or str(caution.get("result") or "책임 소재").strip()
        good_body = _premium_timing_event_body(highlight_good, kind="good", fallback=good_text)
        caution_body = _premium_timing_event_body(highlight_caution, kind="caution", fallback=caution_text)
        topic_value = str(topic.get("value") or "주요 사건").strip()
        timing_profile = section.get("timing_profile") if isinstance(section.get("timing_profile"), dict) else {}
        good_focus = str(timing_profile.get("goodFocus") or topic_value or "좋은 분야").strip()
        caution_focus = str(timing_profile.get("cautionFocus") or "주의 분야").strip()
        topic_value = good_focus or topic_value
        topic_text = _timing_topic_card_body(topic_value, good_text, caution_text)
        if good_focus == caution_focus:
            summary = (
                f"20세~79세 전체에서 {good_focus}의 상승 연도와 주의 연도가 모두 뚜렷합니다. "
                f"대표 상승은 {good_value}, 대표 주의는 {caution_value}입니다."
            )
        else:
            summary = (
                f"20세~79세 전체에서 상승 연도는 {good_focus}, 주의 연도는 {caution_focus}에서 뚜렷합니다. "
                f"대표 상승은 {good_value}, 대표 주의는 {caution_value}입니다."
            )
        return {
            "label": "핵심 유형",
            "type": "상승 연도와 주의 연도가 뚜렷한 사주",
            "summary": summary,
            "insights": [
                {
                    "label": "연도 결론",
                    "value": "상승 연도와 주의 연도가 뚜렷한 사주",
                    "body": summary,
                    "tone": "strong",
                },
                {
                    "label": "상승 연도",
                    "value": good_value or str(good.get("display_label") or "상승 연도"),
                    "body": good_body,
                    "tone": "strong",
                },
                {
                    "label": "주의 연도",
                    "value": caution_value or str(caution.get("display_label") or "주의 연도"),
                    "body": caution_body,
                    "tone": "watch",
                },
                {
                    "label": "활용 기준",
                    "value": topic_value,
                    "body": (
                        f"과거 대조 {past_value}."
                        if past_value
                        else topic_text
                    ),
                    "tone": "neutral",
                },
            ],
            "items": [
                {"label": "상승 연도", "value": good_value, "text": good_text, "body": good_body},
                {"label": "주의 연도", "value": caution_value, "text": caution_text, "body": caution_body, "tone": "watch"},
                {"label": "사건 주제", "value": topic_value, "text": topic_text},
            ],
        }
    profile_units = [unit for unit in units if _premium_unit_has_profile_signal(unit)] or units
    strong_units = [unit for unit in profile_units if not _premium_unit_is_watch(unit)] or profile_units
    secondary_labels = PREMIUM_PROFILE_SECONDARY_UNIT_LABELS.get(domain, set())
    primary_strong_units = [
        unit
        for unit in strong_units
        if _premium_unit_label(unit) not in secondary_labels
    ]
    if primary_strong_units:
        strong_units = primary_strong_units
    scored = sorted(
        strong_units,
        key=lambda unit: (
            -_premium_unit_strength(unit),
            _premium_label_priority(_premium_unit_label(unit)),
            str(unit.get("label") or ""),
        ),
    )
    weak_units = [unit for unit in profile_units if _premium_unit_is_watch(unit)] or profile_units
    weak_sorted = sorted(
        weak_units,
        key=lambda unit: (
            _premium_unit_strength(unit),
            _premium_label_priority(_premium_unit_label(unit)),
            str(unit.get("label") or ""),
        ),
    )
    strong = scored[0]
    weak = weak_sorted[0]
    support_candidates = [unit for unit in scored[1:] if unit is not strong and not _premium_unit_is_watch(unit)]
    support = support_candidates[0] if support_candidates else (scored[1] if len(scored) > 1 else strong)
    if domain == "money":
        money_watch = next(
            (
                unit
                for unit in units
                if any(
                    marker
                    in " ".join(
                        str(unit.get(key) or "")
                        for key in ("label", "display_label", "title", "result", "body", "text")
                    )
                    for marker in ("공동자금", "공동 자금", "명의와 지분", "자금을 섞으면")
                )
            ),
            None,
        )
        if isinstance(money_watch, dict):
            weak = money_watch
    profile_type = _premium_section_profile_type(domain, strong, weak)
    profile_summary = _premium_section_profile_summary(domain, strong, weak, support)
    strong_is_watch = _premium_unit_is_watch(strong)
    support_is_watch = _premium_unit_is_watch(support)
    weak_is_watch = _premium_unit_is_watch(weak)
    strong_label = (
        "핵심 기준"
        if strong_is_watch and domain == "money"
        else ("주의점" if strong_is_watch else ("대표 강점" if _premium_unit_strength(strong) >= 70 else "핵심 기준"))
    )
    return {
        "label": "핵심 유형",
        "type": profile_type,
        "summary": profile_summary,
        "insights": _premium_profile_insights(domain, profile_type, profile_summary, strong, weak, support),
        "items": [
            {
                "label": strong_label,
                "value": _premium_story_display_title(str(strong.get("display_label") or strong.get("label") or "")),
                "text": _premium_unit_text(strong) if strong_is_watch else _premium_positive_unit_text(domain, strong),
                "grade": _premium_profile_grade(strong),
                "tone": "watch" if strong_is_watch else str(strong.get("tone") or "strong"),
            },
            {
                "label": "주의점" if support_is_watch else ("함께 확인할 기준" if strong_is_watch else "함께 강한 기준"),
                "value": _premium_story_display_title(str(support.get("display_label") or support.get("label") or "")),
                "text": _premium_unit_text(support) if support_is_watch else _premium_positive_unit_text(domain, support),
                "grade": _premium_profile_grade(support),
                "tone": "watch" if support_is_watch else str(support.get("tone") or "neutral"),
            },
            {
                "label": _premium_profile_third_label(weak),
                "value": _premium_story_display_title(str(weak.get("display_label") or weak.get("label") or "")),
                "text": _premium_unit_text(weak) if weak_is_watch else _premium_positive_unit_text(domain, weak),
                "grade": _premium_profile_grade(weak),
                "tone": _premium_profile_third_tone(weak),
            },
        ],
    }


def _attach_premium_category_contract(section: dict[str, Any]) -> dict[str, Any]:
    source_contract = section.get("category_contract") if isinstance(section.get("category_contract"), dict) else {}
    base_contract = premium_category_contract(_domain_key(section))
    contract = dict(base_contract)
    if source_contract:
        contract.update(source_contract)
        for key in (
            "judgment_axes",
            "required_judgments",
            "evidence_layers",
            "content_plan",
            "content_plan_slots",
            "reading_order",
            "display_labels",
        ):
            if not contract.get(key) and base_contract.get(key):
                contract[key] = base_contract[key]
    if not contract:
        return section
    source_units = [unit for unit in contract.get("reading_units") or [] if isinstance(unit, dict)]
    reading_units = (
        source_units
        if source_units and all(str(unit.get("result") or "").strip() for unit in source_units)
        else _premium_reading_units(section, contract)
    )
    content_plan = [
        dict(item)
        for item in contract.get("content_plan") or []
        if isinstance(item, dict)
    ]
    if content_plan and not all(str(item.get("result") or "").strip() for item in content_plan):
        content_plan = premium_content_plan_items(
            _domain_key(section),
            content_plan=content_plan,
            topic_items=[
                item
                for item in (contract.get("topic_items") or section.get("topic_items") or [])
                if isinstance(item, dict)
            ],
        )
    display_labels = contract.get("display_labels") if isinstance(contract.get("display_labels"), dict) else {}
    synced_topic_items: list[dict[str, Any]] = []
    for item in section.get("topic_items") or []:
        if not isinstance(item, dict):
            continue
        next_item = dict(item)
        source_title = str(next_item.get("title") or "").strip()
        display_title = str(display_labels.get(source_title, source_title)).strip()
        if display_title and display_title != source_title:
            next_item["source_title"] = source_title
            next_item["title"] = display_title
        synced_topic_items.append(next_item)
    topic_keys = {
        _compact_match_key(item.get("title") or item.get("label") or "")
        for item in synced_topic_items
        if str(item.get("title") or item.get("label") or "").strip()
    }
    for unit in reading_units:
        if not isinstance(unit, dict):
            continue
        title = str(unit.get("display_label") or unit.get("label") or "").strip()
        if not title:
            continue
        key = _compact_match_key(title)
        if key and key in topic_keys:
            continue
        result = str(unit.get("result") or unit.get("focus") or "").strip()
        if not result and not str(unit.get("value") or "").strip():
            continue
        topic_keys.add(key)
        synced_topic_items.append(
            {
                "title": title,
                "body": result,
                "definition": str(unit.get("focus") or result),
                "value": str(unit.get("value") or "").strip(),
                "score": unit.get("score"),
                "tone": str(unit.get("tone") or "neutral"),
                "evidence": str(unit.get("evidence") or ""),
            }
        )
    exposed = {
        "schema_version": contract.get("schema_version") or "",
        "domain": contract.get("domain") or _domain_key(section),
        "section_label": contract.get("section_label") or "",
        "guide_label": contract.get("guide_label") or "",
        "guide_body": contract.get("guide_body") or "",
        "profile_role": contract.get("profile_role") or "",
        "reading_order": list(contract.get("reading_order") or []),
        "reading_units": reading_units,
        "judgment_axes": [
            dict(item)
            for item in contract.get("judgment_axes") or []
            if isinstance(item, dict)
        ],
        "required_judgments": [
            dict(item)
            for item in contract.get("required_judgments") or []
            if isinstance(item, dict)
        ],
        "evidence_layers": list(contract.get("evidence_layers") or []),
        "content_plan": content_plan,
        "content_plan_slots": [
            str(item.get("slot") or "").strip()
            for item in content_plan
            if isinstance(item, dict) and str(item.get("slot") or "").strip()
        ],
    }
    enriched = dict(section)
    if synced_topic_items:
        enriched["topic_items"] = synced_topic_items
    enriched["category_contract"] = exposed
    return enriched


def _attach_premium_section_profile(section: dict[str, Any]) -> dict[str, Any]:
    profile = _premium_section_profile(section)
    if not profile:
        return section
    enriched = dict(section)
    enriched["section_profile"] = profile
    headline = str(enriched.get("headline") or enriched.get("lead") or "").strip()
    support_lead = _premium_section_profile_lead(_domain_key(enriched), profile, headline=headline)
    if _domain_key(enriched) == "personality":
        personality_profile = enriched.get("personality_profile")
        if isinstance(personality_profile, dict):
            support_lead = _personality_profile_intro(personality_profile, fallback=support_lead)
            synced_profile = dict(enriched.get("section_profile") or {})
            synced_profile["type"] = str(personality_profile.get("title") or synced_profile.get("type") or "").strip()
            synced_profile["summary"] = str(personality_profile.get("summary") or synced_profile.get("summary") or "").strip()
            synced_profile["label"] = "성격 유형"
            synced_insights = [
                dict(item)
                for item in synced_profile.get("insights") or []
                if isinstance(item, dict)
            ]
            if synced_insights:
                synced_insights[0] = {
                    **synced_insights[0],
                    "label": "성격 결론",
                    "value": synced_profile["type"],
                    "body": synced_profile["summary"] or str(synced_insights[0].get("body") or "").strip(),
                }
                synced_profile["insights"] = synced_insights
            enriched["section_profile"] = synced_profile
    if support_lead:
        enriched["lead"] = support_lead
    return enriched


def _personality_profile_card_value(profile: dict[str, Any], label: str) -> str:
    for card in profile.get("cards") or []:
        if isinstance(card, dict) and str(card.get("label") or "") == label:
            return str(card.get("value") or "").strip()
    return ""


def _personality_profile_card_body(profile: dict[str, Any], label: str) -> str:
    for card in profile.get("cards") or []:
        if isinstance(card, dict) and str(card.get("label") or "") == label:
            return str(card.get("body") or "").strip()
    return ""


def _personality_intro_sentence(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    first = text.split(".", 1)[0].strip()
    for particle in ("을", "를"):
        marker = f"{particle} 가장 먼저 따집니다"
        if first.startswith("선택할 때는 ") and first.endswith(marker):
            focus = first.removeprefix("선택할 때는 ").removesuffix(marker).strip()
            if focus:
                if "기회" in focus and "실익" in focus:
                    return "선택 앞에서는 실익과 책임 범위를 빠르게 계산합니다."
                return f"선택 앞에서는 {focus}{particle} 가장 먼저 따집니다."
    return f"{first}." if first else ""


def _personality_intro_repeats(previous: str, sentence: str) -> bool:
    left = str(previous or "")
    right = str(sentence or "")
    if not left or not right:
        return False
    marker_groups = (
        ("손익", "실익", "계산"),
        ("책임", "범위", "약속"),
        ("원칙", "기준"),
        ("관계", "사람", "신뢰"),
    )
    for markers in marker_groups:
        if any(marker in left for marker in markers) and any(marker in right for marker in markers):
            return True
    return False


def _personality_profile_intro(profile: dict[str, Any], *, fallback: str = "") -> str:
    title = str(profile.get("title") or "").strip()
    decision = _personality_profile_card_value(profile, "판단 방식")
    decision_body = _personality_profile_card_body(profile, "판단 방식")
    social = _personality_profile_card_value(profile, "대인 태도")
    social_body = _personality_profile_card_body(profile, "대인 태도")
    pressure = _personality_profile_card_value(profile, "압박 대응")
    pressure_body = _personality_profile_card_body(profile, "압박 대응")
    parts: list[str] = []
    title_sentence = _personality_type_sentence(title)
    if title_sentence:
        parts.append(title_sentence)
    decision_sentence = _personality_intro_sentence(decision_body)
    if decision_sentence:
        if not _personality_intro_repeats(parts[0] if parts else "", decision_sentence):
            parts.append(decision_sentence)
    elif decision:
        parts.append(f"선택 앞에서는 {_with_object_particle(decision)} 먼저 봅니다.")
    social_sentence = _personality_intro_sentence(social_body)
    if social_sentence:
        if not _personality_intro_repeats(parts[0] if parts else "", social_sentence):
            parts.append(social_sentence)
    elif social:
        parts.append(f"사람을 대할 때는 {social} 성향이 강합니다.")
    pressure_sentence = _personality_intro_sentence(pressure_body)
    if pressure_sentence:
        parts.append(pressure_sentence)
    elif pressure:
        parts.append(f"압박을 받으면 {pressure}으로 반응합니다.")
    if parts:
        return _join_profile_sentences(*parts[:2])
    if title:
        return f"당신은 {title} 성격입니다." if title.endswith("형") else f"당신은 {title} 성향이 강합니다."
    return fallback


def _premium_profile_lead_label(value: str) -> str:
    cleaned = str(value or "").strip()
    replacements = {
        "재물 발생력": "재물 형성력",
        "타고난 재물의 그릇": "재물 형성력",
        "재물이 들어오는 길": "수입 창출력",
        "수익 전환력": "수입 창출력",
        "수입 발생력": "수입 창출력",
        "축재력": "자산화 능력",
        "자산 축적력": "자산화 능력",
        "재산으로 굳어지는 힘": "자산화 능력",
        "공동재 관리력": "공동자금 운영력",
        "공동 자금 관리력": "공동자금 운영력",
        "공동 자금 안정성": "공동자금 운영력",
        "재물에 얽히는 사람 문제": "공동자금 운영력",
        "계약·문서 안정성": "계약·명의 안정성",
        "계약 안정성": "계약·명의 안정성",
        "돈을 지켜내는 기준": "계약·명의 안정성",
        "전문성 축적도": "전문 자산화",
        "전문성으로 남는 힘": "전문 자산화",
        "전문성": "전문 자산화",
        "성과 구현력": "성취 축적력",
        "직업적 성취의 그릇": "성취 축적력",
        "직업 성취력": "성취 축적력",
        "권한과 책임의 균형": "권한 확보력",
        "권한 책임 균형도": "권한 확보력",
        "권한·책임 균형도": "권한 확보력",
        "평가가 따라오는 자리": "평가·명예 전환력",
        "평가 확보력": "평가·명예 전환력",
        "업무 평가력": "평가·명예 전환력",
        "조직 안에서 자리 잡는 힘": "조직 적응력",
        "조직 적합도": "조직 적응력",
        "결혼으로 이어지는 현실성": "결혼 연결력",
        "결혼 현실화": "결혼 연결력",
        "관계 안정성": "관계 지속력",
        "관계가 오래 가는 힘": "관계 지속력",
        "호감 형성력": "인연 형성력",
        "인연이 들어오는 길": "인연 형성력",
        "애정 표현력": "애정 표현성",
        "애정이 표현되는 방식": "애정 표현성",
        "초년 형성도": "초년에 형성되는 바탕",
        "중년 성취도": "중년에 굳어지는 성취",
        "말년 안정도": "말년에 남는 안정",
        "전환기 대응력": "운이 바뀌는 전환기",
        "공식 역할 수용력": "공식 책임을 맡는 힘",
        "공식 책임 수행력": "공식 책임을 맡는 힘",
        "명예 관리력": "명예를 지켜내는 기준",
        "사회적 인정도": "공적 인정 기반",
        "사회적 인정이 붙는 자리": "공적 인정 기반",
        "평가가 직함으로 이어지는 자리": "직책 상승력",
        "권한이 붙을수록 커지는 평판": "권한 기반 평판",
        "관계 조절력": "관계 조절",
        "조력자 인연": "도움으로 이어지는 인연",
        "책임 경계력": "부탁과 책임의 경계",
        "인맥 형성력": "사람을 얻는 힘",
    }
    return replacements.get(cleaned, cleaned)


def _premium_domain_lead_opening(domain: str, strong_value: str) -> str:
    axis = _premium_sentence_axis_label(strong_value)
    if domain == "money":
        openings = {
            "성과 수익화": "당신의 재물운은 해낸 일의 대가가 실제 보수로 확정될 때 강하게 살아납니다.",
            "수익 전환력": "당신의 재물운은 해낸 일의 대가가 실제 보수로 확정될 때 강하게 살아납니다.",
            "자산 축적": "당신의 재물운은 현금보다 소유권 있는 자산으로 옮길 때 격이 올라갑니다.",
            "자산 축적력": "당신의 재물운은 현금보다 소유권 있는 자산으로 옮길 때 격이 올라갑니다.",
            "수입 창출력": "당신은 일의 대가가 금액으로 분명히 돌아오는 재물운을 지녔습니다.",
            "자산화 능력": "당신은 들어온 수입을 재산으로 전환할 때 재물운이 커집니다.",
            "재물 형성력": "당신의 재물운은 큰 금액과 권리 관계를 다루는 자리에서 본격화됩니다.",
            "공동 자금 관리": "당신은 가까운 사람과 돈을 섞을 때 몫과 권리를 먼저 세워야 합니다.",
            "공동자금 운영력": "당신은 가까운 사람과 돈을 섞을 때 몫과 권리를 먼저 세워야 합니다.",
            "계약 안정": "당신의 재물운은 지급일, 권리 조건, 계약 기준이 분명할 때 지켜집니다.",
            "계약 안정성": "당신의 재물운은 지급일, 권리 조건, 계약 기준이 분명할 때 지켜집니다.",
            "계약·명의 안정성": "당신의 재물운은 계약과 명의가 분명할수록 손실이 줄어듭니다.",
            "계약·문서 안정성": "당신의 재물운은 계약과 명의가 분명할수록 손실이 줄어듭니다.",
        }
        return openings.get(axis, "당신의 재물운은 수입이 들어오는 자리와 재산으로 굳어지는 자리가 따로 움직입니다.")
    if domain == "career":
        openings = {
            "전문성": "당신의 직업운은 전문성이 경력의 단가를 만드는 사주입니다.",
            "전문성 축적도": "당신의 직업운은 전문성이 경력의 단가를 만드는 사주입니다.",
            "평가 확보": "당신의 직업운은 결과물이 공식 평가로 확정될 때 강해집니다.",
            "평가 확보력": "당신의 직업운은 결과물이 공식 평가로 확정될 때 강해집니다.",
            "성과 구현": "당신은 맡은 일을 결과물로 끝까지 마무리할 때 직업운이 살아납니다.",
            "성과 구현력": "당신은 맡은 일을 결과물로 끝까지 마무리할 때 직업운이 살아납니다.",
            "성취 축적력": "당신의 직업운은 맡은 역할이 성취와 이력으로 남는 쪽입니다.",
            "전문 자산화": "당신의 직업운은 전문성이 경력의 중심에 놓일 때 커집니다.",
            "평가·명예 전환력": "당신의 직업운은 성과가 누구의 이름으로 남는가에서 갈립니다.",
            "조직 적응력": "당신은 조직 안에서 역할과 기준이 분명할 때 자기 자리를 얻습니다.",
            "권한 확보력": "당신은 책임만 맡는 자리보다 결정권이 붙는 자리에서 성취가 남습니다.",
            "권한 책임 균형도": "당신은 책임만 맡는 자리보다 결정권이 붙는 자리에서 성취가 남습니다.",
        }
        return openings.get(axis, "당신의 직업운은 성과와 평가 기준이 분명한 자리에서 강합니다.")
    if domain == "love":
        openings = {
            "결혼 연결력": "당신의 연애운은 감정에 머무르지 않고 공식적인 약속으로 옮겨집니다.",
            "오래 가는 신뢰": "당신의 연애운은 빠른 설렘보다 신뢰가 확인된 관계에서 강합니다.",
            "관계 지속력": "당신의 연애운은 빠른 설렘보다 신뢰가 확인된 관계에서 강합니다.",
            "호감이 생기는 계기": "당신의 연애운은 새 만남과 호감 형성이 빠르게 올라오는 쪽입니다.",
            "호감 형성력": "당신의 연애운은 새 만남과 호감 형성이 빠르게 올라오는 쪽입니다.",
            "애정 표현": "당신은 마음이 생기면 말과 태도에서 애정이 분명해집니다.",
            "애정 표현성": "당신은 마음이 생기면 말과 태도에서 애정이 분명해집니다.",
            "생활 안정": "당신의 연애운은 생활 기준이 맞을 때 결혼 이야기로 빨리 넘어갑니다.",
        }
        return openings.get(axis, "당신의 연애운은 호감이 깊어져도 약속과 생활 문제를 그냥 넘기지 않는 쪽입니다.")
    if domain == "marriage":
        openings = {
            "혼인 성향": "당신의 결혼운은 감정보다 생활이 맞아 들어갈 때 안정됩니다.",
            "생활 안정": "당신의 결혼운은 주거와 생활 기반이 맞을 때 오래 갑니다.",
            "가족 책임 수용력": "당신은 결혼 뒤 가족 책임을 직접 맡는 성향이 강합니다.",
            "결혼 지속력": "당신의 결혼운은 한 번 정한 약속을 오래 유지하는 쪽입니다.",
        }
        return openings.get(axis, "당신의 결혼운은 생활 기준이 맞을 때 안정됩니다.")
    if domain == "life":
        openings = {
            "초년에 형성되는 바탕": "초년부터 자기 기준이 일찍 잡히는 사주입니다.",
            "초년 형성": "초년부터 자기 기준이 일찍 잡히는 사주입니다.",
            "중년에 굳어지는 성취": "중년 이후 직업 성취와 재물 기반이 본격적으로 남습니다.",
            "중년에 커지는 성취": "중년 이후 직업 성취와 재물 기반이 본격적으로 남습니다.",
            "말년에 남는 안정": "후반부로 갈수록 자산과 생활 안정이 분명해집니다.",
            "말년 안정": "후반부로 갈수록 자산과 생활 안정이 분명해집니다.",
            "운이 바뀌는 전환기": "대운이 바뀌는 시기에 삶의 무대가 크게 달라집니다.",
            "대운 전환": "대운이 바뀌는 시기에 삶의 무대가 크게 달라집니다.",
        }
        return openings.get(axis, "생애 구간마다 강하게 드러나는 영역이 다릅니다.")
    if domain == "honor":
        openings = {
            "공식 책임을 맡는 힘": "당신은 이름이 기록되는 책임 자리에서 명예가 올라가는 사주입니다.",
            "공식 역할 수용력": "당신은 이름이 기록되는 책임 자리에서 명예가 올라가는 사주입니다.",
            "평판이 오래 남는 힘": "당신의 명예운은 오래 쌓은 평판이 다음 제안으로 이어지는 쪽입니다.",
            "평판 유지력": "당신의 명예운은 오래 쌓은 평판이 다음 제안으로 이어지는 쪽입니다.",
            "공적 인정 기반": "당신은 공식 평가를 통해 직책과 역할을 얻는 사주입니다.",
            "사회적 인정이 붙는 자리": "당신은 공식 평가를 통해 직책과 역할을 얻는 사주입니다.",
            "사회적 인정도": "당신은 공식 평가를 통해 직함과 역할을 얻는 사주입니다.",
            "명예를 지켜내는 기준": "당신의 명예운은 얻은 이름을 오래 지키는 힘에서 갈립니다.",
        }
        return openings.get(axis, "당신은 책임 있는 자리에서 평가와 이름을 남기는 사주입니다.")
    if domain == "social":
        openings = {
            "관계가 오래 남는 힘": "당신은 넓은 인맥보다 오래 남는 사람을 통해 운이 열리는 사주입니다.",
            "관계 지속력": "당신은 넓은 인맥보다 오래 남는 사람을 통해 운이 열리는 사주입니다.",
            "도움으로 이어지는 인연": "당신의 대인관계운은 말뿐인 친분보다 실제 제안으로 들어오는 인연이 강합니다.",
            "조력자 인연": "당신의 대인관계운은 말뿐인 친분보다 실제 제안으로 들어오는 인연이 강합니다.",
            "사람을 얻는 힘": "당신은 필요한 사람을 알아보고 오래 곁에 남기는 힘이 있습니다.",
            "인맥 형성력": "당신은 필요한 사람을 알아보고 오래 곁에 남기는 힘이 있습니다.",
            "부탁과 책임의 경계": "당신의 대인관계는 부탁과 책임의 선을 분명히 할수록 오래 갑니다.",
            "책임 경계력": "당신의 대인관계는 부탁과 책임의 선을 분명히 할수록 오래 갑니다.",
        }
        return openings.get(axis, "당신의 대인관계는 오래 남는 신뢰에서 실속이 생기는 사주입니다.")
    return ""


def _premium_profile_compact_lead(
    domain: str,
    strong_value: str,
    support_value: str = "",
    watch_value: str = "",
) -> str:
    strong_axis = _premium_sentence_axis_label(strong_value)
    support_axis = _premium_sentence_axis_label(support_value) if str(support_value or "").strip() else ""
    watch_axis = _premium_sentence_axis_label(watch_value) if str(watch_value or "").strip() else ""
    opening = _premium_domain_lead_opening(domain, strong_axis)
    if not opening:
        opening = f"{_with_subject_particle(strong_axis)} 가장 선명합니다."
    if watch_axis:
        return _join_profile_sentences(opening, _premium_watch_lead_sentence(domain, watch_axis))
    if support_axis and support_axis != strong_axis:
        support_sentences = {
            "money": f"{support_axis}까지 받쳐 재물의 폭이 넓습니다.",
            "career": f"{support_axis}까지 받쳐 경력의 설득력이 커집니다.",
            "love": f"{support_axis}까지 갖춰 관계의 지속성이 강합니다.",
            "marriage": f"{support_axis}까지 갖춰 결혼 생활이 오래 갑니다.",
            "life": _premium_life_support_sentence(support_axis),
            "honor": _premium_honor_support_sentence(support_axis),
            "social": _premium_social_support_sentence(support_axis),
        }
        return _join_profile_sentences(opening, support_sentences.get(domain, f"{support_axis}{_topic_particle(support_axis)} 함께 작용합니다."))
    return opening


def _premium_watch_lead_sentence(domain: str, watch_axis: str) -> str:
    axis = _premium_sentence_axis_label(watch_axis)
    if domain == "money":
        if "공동" in axis or "자금" in axis:
            return "가까운 사람과 자금을 섞을 때 손실이 먼저 생깁니다."
        if "계약" in axis or "명의" in axis:
            return "계약과 명의가 흐리면 손실이 먼저 생깁니다."
        if "보증" in axis or "부채" in axis:
            return "보증과 채무 관계에서 손실 부담이 커집니다."
        return f"금전 손실은 {axis}에서 먼저 드러납니다."
    if domain == "career":
        if "권한" in axis:
            return "결정권 없는 책임에서 직업 부담이 먼저 나타납니다."
        if "평가" in axis or "명예" in axis:
            return "성과가 평가로 확정되지 않는 자리에서 손실이 생깁니다."
        if "조직" in axis:
            return "조직 기준이 불분명한 자리에서는 경력 소모가 커집니다."
        if "업무" in axis or "조건" in axis:
            return "업무 조건을 잘못 고르면 책임만 커지고 성과의 이름은 가져가기 어렵습니다."
        return f"직업 부담은 {axis}에서 가장 먼저 나타납니다."
    if domain == "love":
        if "갈등" in axis:
            return "관계가 흔들리는 지점은 갈등을 처리하는 방식입니다."
        if "표현" in axis:
            return "마음이 있어도 표현이 늦으면 상대가 먼저 멀어집니다."
        if "주변" in axis:
            return "주변의 말이 끼어들면 관계 판단이 흔들립니다."
        return f"연애에서 흔들리는 지점은 {axis}입니다."
    if domain == "marriage":
        if "부부 갈등" in axis:
            return "결혼 뒤에는 역할 분담이 갈등의 중심이 됩니다."
        if "가족" in axis:
            return "양가와 원가족 문제가 결혼 생활에 깊게 들어옵니다."
        if "재정" in axis or "생활비" in axis:
            return "부부 재정 기준이 늦게 잡히면 생활 갈등이 커집니다."
        return f"결혼에서 주의할 문제는 {axis}입니다."
    if domain == "life":
        if "전환" in axis or "대운" in axis:
            return "운이 바뀌는 시기에는 직업, 거처, 가족 책임이 한꺼번에 움직입니다."
        if "초년" in axis:
            return "초년에 굳어진 기준은 이후 선택에도 오래 영향을 남깁니다."
        if "중년" in axis:
            return "중년에는 책임과 보상의 균형이 다시 문제가 됩니다."
        if "말년" in axis:
            return "후반부에는 자산과 생활 기반을 지키는 일이 중요해집니다."
        return f"생애 구간에서는 {axis}{_topic_particle(axis)} 주의점입니다."
    if domain == "honor":
        if "명예" in axis or "평판" in axis:
            return "평판은 금전 책임과 말의 기록이 흐려질 때 손상됩니다."
        if "책임" in axis or "공식" in axis:
            return "권한 없는 책임은 명예보다 부담을 먼저 남깁니다."
        return f"명예운에서는 {axis}{_topic_particle(axis)} 주의점입니다."
    if domain == "social":
        if "사람" in axis or "인맥" in axis:
            return "사람을 급하게 넓히면 실속 없는 관계가 늘어납니다."
        if "도움" in axis or "조력" in axis:
            return "말뿐인 도움에 기대면 결정적인 순간에 혼자 남기 쉽습니다."
        if "책임" in axis or "부탁" in axis:
            return "가까운 사람의 부탁은 책임으로 되돌아오기 쉽습니다."
        return f"대인관계에서는 {axis}{_topic_particle(axis)} 주의점입니다."
    return f"{axis}{_topic_particle(axis)} 주의점입니다."


def _premium_life_support_sentence(axis: str) -> str:
    if "말년" in axis:
        return "말년에는 자산과 생활 기반이 안정의 중심이 됩니다."
    if "중년" in axis:
        return "중년에는 성취가 이력과 보상으로 남습니다."
    if "초년" in axis:
        return "초년에 잡힌 기준이 이후 선택의 바탕이 됩니다."
    if "전환" in axis or "대운" in axis:
        return "전환기마다 직업과 생활 기반이 다시 정리됩니다."
    return f"{axis}{_topic_particle(axis)} 생애 판단의 보조 기준입니다."


def _premium_honor_support_sentence(axis: str) -> str:
    if "평판" in axis:
        return "평판은 오래 유지되고 다음 제안으로 이어집니다."
    if "책임" in axis or "공식" in axis:
        return "공식 책임이 붙을수록 이름이 분명하게 남습니다."
    if "인정" in axis:
        return "사회적 인정이 직함과 역할로 굳어집니다."
    if "명예" in axis:
        return "평판을 지키는 기준이 분명할수록 명예가 오래 갑니다."
    return f"{axis}{_topic_particle(axis)} 명예운을 받쳐줍니다."


def _premium_social_support_sentence(axis: str) -> str:
    if "책임" in axis or "부탁" in axis:
        return "부탁과 책임의 선이 분명할수록 관계가 오래 갑니다."
    if "도움" in axis or "조력" in axis:
        return "실제 도움을 주는 인연이 결정적인 순간에 남습니다."
    if "사람" in axis or "인맥" in axis:
        return "필요한 사람을 가려내는 힘이 관계의 실속을 만듭니다."
    if "관계" in axis:
        return "검증된 관계가 오래 남아 실제 도움으로 이어집니다."
    return f"{axis}{_topic_particle(axis)} 대인관계의 보조 기준입니다."


def _premium_section_profile_lead(domain: str, profile: dict[str, Any], *, headline: str = "") -> str:
    items = [item for item in profile.get("items") or [] if isinstance(item, dict)]
    strong = next((item for item in items if str(item.get("label") or "") == "대표 강점"), items[0] if items else {})
    support = next(
        (
            item
            for item in items
            if str(item.get("label") or "") in {"함께 강한 기준", "함께 강한 축", "받쳐주는 기준", "함께 확인할 기준", "추가 강점", "보조 기준", "함께 보는 기준", "함께 보는 축"}
        ),
        items[1] if len(items) > 1 else {},
    )
    watch = next(
        (
            item
            for item in items
            if str(item.get("tone") or "") in {"watch", "risk"} or "주의" in str(item.get("label") or "")
        ),
        {},
    )
    strong_value = _premium_profile_lead_label(str(strong.get("value") or "").strip())
    watch_value = _premium_profile_lead_label(str(watch.get("value") or "").strip())
    support_value = _premium_profile_lead_label(str(support.get("value") or "").strip())
    strong_text = str(strong.get("text") or "").strip()
    support_text = str(support.get("text") or "").strip()
    watch_text = str(watch.get("text") or "").strip()
    if domain == "personality":
        profile_type = str(profile.get("type") or strong_value or "성격").strip()
        return f"{profile_type}입니다. 선택 기준이 선명합니다."
    if domain == "money":
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value)
    if domain == "career":
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value)
    if domain in {"love", "marriage"}:
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value) or "관계가 깊어지면 결혼 준비가 구체적인 의제가 됩니다."
    if domain == "timing":
        good = next(
            (
                item
                for item in items
                if str(item.get("label") or "") in {"상승 연도", "좋은 연도"}
            ),
            {},
        )
        caution = next((item for item in items if str(item.get("label") or "") == "주의 연도"), {})
        good_value = str(good.get("value") or "").strip()
        caution_value = str(caution.get("value") or "").strip()
        good_text = str(good.get("text") or "").strip()
        caution_text = str(caution.get("text") or "").strip()
        summary = str(profile.get("summary") or "").strip()
        if good_text and caution_text:
            good_anchor = good_value.split("/")[0].strip()
            caution_anchor = caution_value.split("/")[0].strip()
            anchor_sentence = (
                f"상승 연도: {good_anchor}. 주의 연도: {caution_anchor}."
                if good_anchor and caution_anchor
                else ""
            )
            return summary or anchor_sentence or "20세부터 79세까지 주요 연도를 정리합니다."
        return "20세부터 79세까지 주요 상승 연도와 주의 연도를 정리합니다."
    if domain == "life":
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value)
    if domain == "honor":
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value)
    if domain == "social":
        return _premium_profile_compact_lead(domain, strong_value, support_value, watch_value)
    if headline:
        return headline
    return ""


def _attach_premium_visual_profile(section: dict[str, Any]) -> dict[str, Any]:
    profile = _premium_visual_profile(section)
    if not profile:
        return section
    enriched = dict(section)
    enriched["visual_profile"] = profile
    return enriched


def _premium_story_text(value: Any) -> str:
    text = _clean_customer_copy_text(str(value or "").strip())
    replacements = (
        ("당신은 쉽게 흔들리지 않는 중심이 강한 사람입니다.", "당신은 판단의 중심이 분명한 사람입니다."),
        ("쉽게 흔들리지 않는 중심이 강한", "판단의 중심이 분명한"),
        ("쉽게 흔들리지는 않지만", "판단을 쉽게 넘기지는 않지만"),
        ("쉽게 흔들리지 않고", "쉽게 물러서지 않고"),
        ("쉽게 흔들리지 않습니다", "쉽게 무르지 않습니다"),
        ("생활 기반도 쉽게 흔들리지 않습니다", "생활 기반도 안정적으로 남습니다"),
        ("평판이 쉽게 흔들리지 않습니다", "평판이 오래 유지됩니다"),
        ("현금보다 자산으로 묶을 때", "현금보다 등기 자산으로 전환할 때"),
        ("중년에 자산을 크게 밀어 올리는 운이 옵니다.", "중년에는 자산 규모가 눈에 띄게 불어납니다."),
        ("결과가 잡힙니다", "결과가 분명해집니다"),
        ("결정이 잡힙니다", "결정이 분명해집니다"),
        ("결과가 강하게 나옵니다", "결과가 뚜렷합니다"),
        ("판단이 강합니다", "판단 기준이 분명합니다"),
    )
    for before, after in replacements:
        text = text.replace(before, after)
    return " ".join(text.split())


def _premium_story_sentence(value: Any, *, max_sentences: int = 1) -> str:
    text = _premium_story_text(value)
    if not text:
        return ""
    sentences: list[str] = []
    for raw in text.split("."):
        sentence = raw.strip()
        if not sentence:
            continue
        sentences.append(sentence + ".")
        if len(sentences) >= max_sentences:
            break
    return " ".join(sentences) if sentences else text


PREMIUM_STORY_CONTEXT_SENTENCES: dict[str, str] = {
    "판단 기준": "근거와 책임 범위가 흐린 제안에는 초반부터 거리를 둡니다.",
    "대인 조율감": "처음부터 가까워지기보다 상대의 태도와 약속을 확인한 뒤 거리를 정합니다.",
    "감정 반응성": "감정이 올라와도 바로 터뜨리기보다 사실관계를 먼저 따집니다.",
    "압박 대응력": "책임 소재가 흐린 일은 시간이 갈수록 본인에게 불리하게 남습니다.",
    "행동 속도": "기준이 서면 실행은 빠르지만, 기준이 흐리면 손해도 빨리 현실화됩니다.",
    "관심 몰입도": "흥미가 분명해진 분야에서는 자료, 경험, 사람을 빠르게 모읍니다.",
    "타고난 재물의 그릇": "금액이 커질수록 명의, 권리, 회수 기준이 재물의 크기를 결정합니다.",
    "재물이 들어오는 길": "단가와 지급 기준을 먼저 잡을 때 같은 일도 더 높은 보수로 계산됩니다.",
    "수입 발생력": "단가와 지급 기준을 먼저 잡을 때 같은 일도 더 높은 보수로 계산됩니다.",
    "해낸 일이 보수로 돌아옵니다": "단가와 지급 기준을 먼저 잡을 때 같은 일도 더 높은 보수로 계산됩니다.",
    "수익 전환력": "단가와 지급 기준을 먼저 잡을 때 같은 일도 더 높은 보수로 계산됩니다.",
    "자산 축적력": "현금보다 등기처럼 권리가 남는 자산에서 재산의 기반이 만들어집니다.",
    "자산 확정력": "현금보다 등기처럼 권리가 남는 자산에서 재산의 기반이 만들어집니다.",
    "공동 자금 관리력": "명의가 흐려지면 가까운 사람의 몫까지 떠안게 됩니다.",
    "공동 자금 안정성": "명의가 흐려지면 가까운 사람의 몫까지 떠안게 됩니다.",
    "공동재 관리력": "명의가 흐려지면 가까운 사람의 몫까지 떠안게 됩니다.",
    "계약 안정성": "지급일이 문서로 확정되면 손실이 줄어듭니다.",
    "계약·명의 안정성": "지급일과 명의가 문서로 확정되면 손실이 줄어듭니다.",
    "전문성 축적도": "그 분야에서 믿고 맡길 수 있는 사람으로 자리 잡습니다.",
    "운영을 장악하는 직업 성취": "운영 기준을 잡을 때 핵심 역할로 인정받습니다.",
    "재주 수익화": "기술, 콘텐츠, 서비스처럼 값을 매길 수 있는 산출물이 있을 때 수입이 붙습니다.",
    "독립 사업의 승부수": "고객층, 단가, 고정비 구조가 맞아야 회사 밖에서 자기 몫이 분명해집니다.",
    "권한 없이 책임지는 자리": "결정권이 빠진 책임은 성과보다 경력의 흠으로 남습니다.",
    "기준 없는 조직에서의 소모": "규정이 없는 곳에서는 실력보다 소모가 먼저 누적됩니다.",
    "결혼 현실화": "감정이 깊어지면 일정, 주거, 가족 협의가 곧바로 결혼 의제가 됩니다.",
    "관계가 공식화되는 연애": "말로만 이어지는 관계보다 공개된 약속이 있을 때 결혼 이야기가 현실로 옮겨집니다.",
    "애정 성향": "상대가 안정적인 사람인지 오래 확인한 뒤 관계를 진전시킵니다.",
    "마음보다 늦은 표현": "표현이 늦으면 상대는 확신을 갖기 어렵습니다.",
    "감정 기복이 큰 상대와의 손상": "감정 기복이 큰 상대와는 끌림보다 생활 손상이 먼저 드러납니다.",
    "초년의 기준": "초년의 선택은 이후 전공, 직장, 관계의 기준으로 오래 남습니다.",
    "중년의 자산 확장": "직업 책임과 자산 결정이 같은 시기에 맞물립니다.",
    "중년에 커지는 책임의 무게": "성과가 올라오는 시기에는 결정권을 가진 사람에게 경력의 몫이 돌아갑니다.",
    "중년에 굳어지는 책임의 무게": "성과가 올라오는 시기에는 결정권을 가진 사람에게 경력의 몫이 돌아갑니다.",
    "청년기의 직업 시행착오": "이 시기에는 직업 이름보다 실제 권한과 보상 기준이 손익을 정합니다.",
    "말년의 안정": "말년에는 자산 기반이 생활 안정의 격차를 만듭니다.",
    "공식 책임 수행력": "결정권이 주어질 때 실력이 공식 평가로 남습니다.",
    "공개 자리에서 받는 검증": "공식적인 자리에서는 성과와 책임 이력이 함께 남습니다.",
    "직책으로 올라가는 명예": "직책이 높아질수록 말보다 기록과 책임 이력이 중요해집니다.",
    "명예 관리력": "책임 소재가 정리될수록 평판이 오래 유지됩니다.",
    "금전 문제로 깎이는 평판": "금전 책임이 흐려지면 능력보다 신뢰 문제가 먼저 보입니다.",
    "관계 지속력": "가벼운 친분보다 오래 검증된 관계에서 소개와 보호가 들어옵니다.",
    "인맥 형성력": "넓게 아는 사람보다 실제로 움직여줄 사람이 남습니다.",
    "부탁이 책임으로 바뀌는 관계": "호의로 받아준 일이 시간이 지나면 당신의 몫으로 확정됩니다.",
    "책임 경계력": "도움이 책임으로 바뀌는 순간 관계의 주도권이 넘어갑니다.",
    "선을 넘는 관계의 정리": "상대의 요구가 반복되면 늦기 전에 관계의 범위를 정리합니다.",
    "질투하는 경쟁자": "성과가 보이는 자리에서는 축하보다 견제가 먼저 오는 사람을 가려야 합니다.",
}


def _premium_story_sentence_count(text: str) -> int:
    return sum(1 for part in str(text or "").split(".") if part.strip())


def _premium_story_context_sentence(title: str, body: str) -> str:
    cleaned_title = _premium_sentence_axis_label(_premium_story_text(title))
    body_text = _premium_story_text(body)
    if cleaned_title == "판단 기준":
        if "납득" in body_text:
            sentence = "근거가 흐린 제안에는 거리를 둡니다."
            return "" if sentence in body_text else sentence
        if "큰 선택" in body_text or "자기 기준" in body_text:
            sentence = "큰 선택일수록 손익과 책임의 경계를 먼저 가늠합니다."
            return "" if sentence in body_text else sentence
        if "근거" in body_text or "책임" in body_text:
            sentence = "근거가 약한 제안은 초반부터 거리를 둡니다."
            return "" if sentence in body_text else sentence
    if cleaned_title == "대인 조율감":
        if "선을 넘" in body_text:
            sentence = "정이 들어도 상대가 선을 넘으면 관계의 폭을 줄입니다."
            return "" if sentence in body_text else sentence
        if "솔직함" in body_text or "돌려" in body_text:
            sentence = "말의 책임이 분명한 관계에서 마음이 편합니다."
            return "" if sentence in body_text else sentence
        if "믿은 관계" in body_text:
            sentence = "사람을 넓게 늘리기보다 오래 볼 사람을 남깁니다."
            return "" if sentence in body_text else sentence
    sentence = PREMIUM_STORY_CONTEXT_SENTENCES.get(cleaned_title, "")
    if sentence and sentence not in str(body or ""):
        return sentence
    return ""


def _premium_story_detail_body(item: dict[str, Any]) -> str:
    for key in ("body", "judgment", "result", "focus", "text"):
        sentence = _premium_story_sentence(item.get(key))
        if sentence:
            return sentence
    for key in ("bullets", "event_scenes", "premium_notes", "caution_targets"):
        values = item.get(key)
        if isinstance(values, list):
            for value in values:
                sentence = _premium_story_sentence(value)
                if sentence:
                    return sentence
    return ""


def _premium_story_is_watch(item: dict[str, Any]) -> bool:
    tone = str(item.get("tone") or item.get("level") or "").strip().lower()
    if tone in {"watch", "risk", "caution"}:
        return True
    joined = " ".join(
        _premium_story_text(item.get(key))
        for key in ("label", "title", "value", "body", "judgment", "text", "level", "tone")
    )
    return any(
        marker in joined
        for marker in (
            "주의",
            "손해",
            "손실",
            "손상",
            "권리 주장",
            "권리를 주장",
            "몫",
            "부담",
            "소모",
            "책임 전가",
            "책임 문제",
            "책임으로 바뀌",
            "늦",
            "견제",
            "잃",
            "덜 남",
            "나뉩",
            "나뉘",
            "줄어",
            "지연",
            "전가",
            "떠안",
            "회수",
            "구두 약속",
            "보상은 다른",
            "빼앗",
            "부딪",
            "침범",
            "무너",
            "불균형",
            "불리",
            "기울",
            "압박",
            "시행착오",
            "어렵",
            "말이 달라",
        )
    )


def _premium_story_body_has_clear_caution(body: str) -> bool:
    text = _premium_story_text(body)
    return any(
        marker in text
        for marker in (
            "애매",
            "손해",
            "손실",
            "손상",
            "권리 주장",
            "권리를 주장",
            "부담",
            "소모",
            "늦",
            "견제",
            "빼앗",
            "부딪",
            "침범",
            "무너",
            "불균형",
            "외로워",
            "기복",
            "불안정",
            "무너",
            "버겁",
            "피로",
            "불리",
            "기울",
            "기준 없는",
            "규정이 없는",
            "어렵",
            "책임으로 바뀌",
            "잃",
            "덜 남",
            "나뉩",
            "나뉘",
            "줄어",
            "지연",
            "전가",
            "떠안",
            "회수",
            "구두 약속",
            "보상은 다른",
        )
    )


def _premium_story_caution_default(domain: str, title: str) -> str:
    defaults = {
        "personality": "책임이 애매한 자리에서는 감정 소모보다 불리한 책임 기록이 먼저 남습니다.",
        "money": "가까운 사람과 금전 관계를 맺으면 권리 주장과 손실이 함께 남습니다.",
        "career": "성과가 있어도 기록과 권한 체계가 없으면 공로가 다른 사람의 몫으로 넘어갑니다.",
        "love": "마음이 깊어도 표현이 늦으면 상대는 확신을 갖기 어렵습니다.",
        "marriage": "생활 기준이 정리되지 않으면 결혼 생활에서 반복 갈등이 남습니다.",
        "life": "전환기에는 익숙한 선택을 고집하다가 중요한 기회를 놓칠 수 있습니다.",
        "honor": "금전 책임이 불분명하면 평판까지 손상됩니다.",
        "social": "성과가 보이는 순간 가까운 사람도 경쟁자로 돌아설 수 있습니다.",
        "timing": "주의 연도에는 금전, 계약, 관계에서 관리할 일이 분명하게 생깁니다.",
    }
    if "돈" in title or "금전" in title:
        return defaults["money"]
    if domain == "social":
        if "부탁" in title or "책임" in title:
            return "호의로 받아준 일이 시간이 지나면 당신의 몫으로 확정됩니다."
        if "도움" in title or "조력" in title:
            return "결정적인 도움은 늦게 들어오고, 먼저 혼자 처리해야 하는 일이 많습니다."
        if "경쟁" in title or "견제" in title or "질투" in title:
            return defaults["social"]
    return defaults.get(domain, "애매한 책임과 말로 정한 약속은 손해로 남습니다.")


def _premium_story_display_title(title: str) -> str:
    replacements = {
        "타고난 재물의 그릇": "재물 형성력",
        "재물 발생력": "재물 형성력",
        "수입 발생력": "수입 창출력",
        "재물이 들어오는 길": "수입 창출력",
        "자산 확정력": "자산화 능력",
        "재산으로 굳어지는 힘": "자산화 능력",
        "공동 자금 안정성": "공동자금 운영력",
        "공동 자금 관리력": "공동자금 운영력",
        "확장 가능성": "사업 확장성",
        "재물에 얽히는 사람 문제": "공동자금 운영력",
        "돈을 지켜내는 기준": "계약·명의 안정성",
        "계약·문서 안정성": "계약·명의 안정성",
        "직업적 성취의 그릇": "성취 축적력",
        "평가가 따라오는 자리": "평가·명예 전환력",
        "조직 안에서 자리 잡는 힘": "조직 적응력",
        "권한과 책임의 균형": "권한 확보력",
        "전문성으로 남는 힘": "전문 자산화",
        "관계가 오래 가는 힘": "관계 지속력",
        "결혼 현실성": "결혼 연결력",
        "결혼으로 이어지는 현실성": "결혼 연결력",
        "생활 안정성": "생활 안정",
        "가족 변수 관리력": "가족 변수",
    }
    return replacements.get(title, title)


def _premium_story_watch_title(title: str) -> str:
    replacements = {
        "계약·문서 안정성": "계약·명의 주의",
        "계약·명의 안정성": "계약·명의 주의",
        "돈을 지켜내는 기준": "계약·명의 주의",
        "타고난 재물의 그릇": "재물 형성 주의",
        "재물 형성력": "재물 형성 주의",
        "재물이 들어오는 길": "수입 창출 주의",
        "수입 창출력": "수입 창출 주의",
        "재산으로 굳어지는 힘": "자산화 주의",
        "자산화 능력": "자산화 주의",
        "공식 책임을 맡는 힘": "권한 없는 공식 책임",
        "공적 인정 기반": "공적 인정이 늦게 따라오는 자리",
        "사회적 인정이 붙는 자리": "공적 인정이 늦게 따라오는 자리",
        "직책 상승력": "직책 상승이 늦어지는 자리",
        "권한 기반 평판": "권한이 평판 부담으로 바뀌는 자리",
        "직업적 성취의 그릇": "성과가 남지 않는 자리",
        "성취 축적력": "성과가 남지 않는 자리",
        "독립 사업의 승부수": "공로가 남지 않는 성과",
        "운영을 장악하는 직업 성취": "운영 책임이 과해지는 자리",
        "전문성으로 남는 힘": "전문성이 흩어지는 자리",
        "전문 자산화": "전문성이 흩어지는 자리",
        "도움으로 이어지는 인연": "늦게 들어오는 조력",
        "관계가 오래 남는 힘": "관계가 오래 남기 어려운 자리",
        "관계 지속력": "관계가 오래 남기 어려운 자리",
        "인연이 들어오는 길": "늦게 들어오는 인연",
        "인연 형성력": "늦게 들어오는 인연",
        "갈등 관리력": "감정 기복이 큰 상대와의 손상 관리",
        "결혼으로 이어지는 현실성": "결혼 결정이 늦어지는 자리",
        "결혼 연결력": "결혼 결정이 늦어지는 자리",
            "중년에 커지는 성취": "중년에 굳어지는 책임",
            "중년에 굳어지는 성취": "중년에 굳어지는 책임",
        "운이 바뀌는 전환기": "전환기의 선택 손실",
    }
    return replacements.get(title, title)


def _premium_story_card(
    label: str,
    title: Any,
    body: Any,
    *,
    tone: str = "neutral",
    source: str = "",
) -> dict[str, Any]:
    title_text = _premium_story_display_title(_premium_sentence_axis_label(_premium_story_text(title)))
    if str(tone).lower() in {"watch", "risk", "caution"} or "주의" in str(label or ""):
        title_text = _premium_story_watch_title(title_text)
    body_text = _premium_story_sentence(body, max_sentences=2)
    if _premium_story_sentence_count(body_text) < 2:
        context = _premium_story_context_sentence(title_text, body_text)
        if context:
            body_text = f"{body_text} {context}".strip()
    return {
        "label": label,
        "title": title_text,
        "body": body_text,
        "tone": tone,
        "source": source,
    }


def _premium_section_story_cards(section: dict[str, Any]) -> list[dict[str, Any]]:
    domain = _domain_key(section)
    profile = section.get("section_profile") if isinstance(section.get("section_profile"), dict) else {}
    if domain == "timing":
        return _premium_timing_story_cards(profile)
    profile_items = [item for item in profile.get("items") or [] if isinstance(item, dict)]
    details = [item for item in section.get("premium_details") or [] if isinstance(item, dict)]
    blocks = [item for item in section.get("detail_blocks") or [] if isinstance(item, dict)]

    strong = next((item for item in profile_items if item.get("label") in {"대표 강점", "핵심 기준", "주의점"}), None)
    support = next((item for item in profile_items if item.get("label") in {"함께 강한 기준", "함께 강한 축", "받쳐주는 기준", "함께 확인할 기준"}), None)
    weak = next((item for item in profile_items if "주의" in str(item.get("label") or "")), None)
    if weak is None:
        weak = next((item for item in profile_items if str(item.get("tone") or "") in {"watch", "risk"}), None)
    if weak is None and profile_items:
        weak = profile_items[-1]
    preferred_social_watch = None
    if domain == "social" and support:
        support_text = _premium_story_text(
            " ".join(str(support.get(key) or "") for key in ("value", "text", "body", "title"))
        )
        if "부탁" in support_text and "책임" in support_text:
            preferred_social_watch = support
    strong_title = _premium_story_text(
        (strong or {}).get("value") or (strong or {}).get("title") or (strong or {}).get("label") or ""
    )
    strong_body = _premium_story_text((strong or {}).get("text") or (strong or {}).get("body") or "")

    def is_repeated_scene(item: dict[str, Any]) -> bool:
        title = _premium_story_text(item.get("title") or item.get("value") or item.get("label") or "")
        return bool(strong_title and title and title == strong_title)

    def is_repeated_strong(item: dict[str, Any]) -> bool:
        title = _premium_story_text(item.get("title") or item.get("value") or item.get("label") or "")
        body = _premium_story_text(_premium_story_detail_body(item))
        return bool((strong_title and title and title == strong_title) or (strong_body and body and body == strong_body))

    scene_source = next(
        (item for item in details if not _premium_story_is_watch(item) and not is_repeated_scene(item)),
        None,
    )
    if scene_source is None:
        scene_source = next(
            (item for item in blocks if not _premium_story_is_watch(item) and not is_repeated_scene(item)),
            None,
        )
    if scene_source is None:
        scene_source = next((item for item in details if not _premium_story_is_watch(item)), None)
    if scene_source is None:
        scene_source = next((item for item in blocks if not _premium_story_is_watch(item)), None)
    if scene_source is None:
        scene_source = support or strong

    weak_body = _premium_story_detail_body(weak or {})
    watch_source = (
        weak
        if weak
        and _premium_story_is_watch(weak)
        and _premium_story_body_has_clear_caution(weak_body)
        else None
    )
    if watch_source is None:
        watch_source = next((item for item in details if _premium_story_is_watch(item) and not is_repeated_strong(item)), None)
    if watch_source is None:
        watch_source = next((item for item in blocks if _premium_story_is_watch(item) and not is_repeated_strong(item)), None)
    if watch_source is None:
        watch_source = weak
    if preferred_social_watch is not None:
        watch_source = preferred_social_watch

    strong_card = _premium_story_card(
        "핵심 기준"
        if domain == "money" and str((strong or {}).get("label") or "") == "핵심 기준"
        else (
            "주의점"
            if str((strong or {}).get("tone") or "").lower() in {"watch", "risk", "caution"} or str((strong or {}).get("label") or "") == "주의점"
            else ("핵심 기준" if str((strong or {}).get("label") or "") == "핵심 기준" else "대표 강점")
        ),
        (strong or {}).get("value") or (strong or {}).get("label") or profile.get("type"),
        (strong or {}).get("text") or (strong or {}).get("body") or profile.get("summary"),
        tone=str((strong or {}).get("tone") or "strong"),
        source="profile",
    )
    if domain == "social" and str(strong_card.get("label") or "") == "핵심 기준":
        strong_text = " ".join(
            _premium_story_text(str(strong_card.get(key) or ""))
            for key in ("title", "body")
        )
        if "부탁" in strong_text and "책임" in strong_text:
            strong_card = dict(strong_card)
            strong_card["label"] = "주의점"
            strong_card["tone"] = "watch"
    scene_card = _premium_story_card(
        "생활에서 보이는 장면",
        (scene_source or {}).get("title") or (scene_source or {}).get("value") or (scene_source or {}).get("label"),
        _premium_story_detail_body(scene_source or {}),
        tone=str((scene_source or {}).get("tone") or (scene_source or {}).get("level") or "neutral"),
        source="detail",
    )

    def watch_card_from(source: dict[str, Any] | None) -> dict[str, Any]:
        body = _premium_story_detail_body(source or {})
        source_title = (source or {}).get("title") or (source or {}).get("value") or (source or {}).get("label")
        title_text = str(source_title or "")
        if domain == "money" and any(marker in f"{title_text} {body}" for marker in ("공동자금", "명의와 지분", "자금을 섞으면")):
            source_title = "공동자금 운영력"
        return _premium_story_card(
            "주의할 자리",
            source_title,
            (
                body
                if _premium_story_body_has_clear_caution(body)
                else _premium_story_caution_default(
                    domain,
                    str((source or {}).get("title") or (source or {}).get("value") or (source or {}).get("label") or ""),
                )
            ),
            tone="watch",
            source="watch",
        )

    def visible_duplicate(card: dict[str, Any], others: list[dict[str, Any]]) -> bool:
        title = str(card.get("title") or "").strip()
        body = str(card.get("body") or "").strip()
        for other in others:
            other_title = str(other.get("title") or "").strip()
            other_body = str(other.get("body") or "").strip()
            if title and title == other_title:
                return True
            if body and body == other_body:
                return True
        return False

    watch_candidates: list[dict[str, Any]] = []
    for source in [watch_source, *details, *blocks, weak]:
        if isinstance(source, dict) and source and _premium_story_is_watch(source):
            watch_candidates.append(source)
    if domain == "money":
        watch_candidates.sort(
            key=lambda source: (
                0
                if any(
                    marker in " ".join(str(source.get(key) or "") for key in ("title", "value", "label", "body", "judgment"))
                    for marker in ("공동자금", "명의와 지분", "자금을 섞으면")
                )
                else 1,
            )
        )
    if domain == "social":
        watch_candidates.sort(
            key=lambda source: (
                0
                if (
                    "부탁" in " ".join(
                        str(source.get(key) or "")
                        for key in ("title", "value", "label", "body", "judgment")
                    )
                    and (
                        "책임" in " ".join(
                            str(source.get(key) or "")
                            for key in ("title", "value", "label", "body", "judgment")
                        )
                    )
                )
                else 1,
            )
        )
    watch_card = None
    for source in watch_candidates:
        candidate = watch_card_from(source)
        if not visible_duplicate(candidate, [strong_card, scene_card]):
            watch_card = candidate
            break
    if watch_card is None:
        watch_card = watch_card_from(watch_source or weak or {})

    candidates = [strong_card, scene_card, watch_card]
    if domain == "money":
        contract_sentence = "계약, 명의, 지분 배분을 분명히 해 큰 손실을 줄입니다."
        if not any(contract_sentence in str(card.get("body") or "") for card in candidates):
            target_index = 1 if str(scene_card.get("body") or "").strip() else 0
            updated = dict(candidates[target_index])
            updated["body"] = _join_distinct_summary_sentences(
                str(updated.get("body") or ""),
                contract_sentence,
                limit=2,
            )
            candidates[target_index] = updated

    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in candidates:
        title = str(card.get("title") or "").strip()
        body = str(card.get("body") or "").strip()
        if not title and not body:
            continue
        key = f"{title}|{body}"
        if key in seen:
            continue
        seen.add(key)
        cards.append(card)
    return cards


def _premium_timing_story_cards(profile: dict[str, Any]) -> list[dict[str, Any]]:
    items = [item for item in profile.get("items") or [] if isinstance(item, dict)]

    def by_label(label: str) -> dict[str, Any]:
        return next((item for item in items if str(item.get("label") or "") == label), {})

    def first_value(item: dict[str, Any]) -> str:
        return str(item.get("value") or "").split("/", 1)[0].strip()

    def keyword_text(item: dict[str, Any], fallback: str) -> str:
        text = str(item.get("text") or item.get("body") or item.get("result") or "").strip().rstrip(".")
        return text or fallback

    def body_text(item: dict[str, Any], fallback: str, *, kind: str) -> str:
        body = str(item.get("body") or "").strip()
        if body:
            return body if body.endswith(".") else body + "."
        text = keyword_text(item, fallback)
        if kind == "topic":
            value = str(item.get("value") or fallback or "").strip()
            return f"핵심 분야: {value}." if value else "핵심 분야를 표시합니다."
        if kind == "good":
            return f"{text}{_subject_particle(text)} 실제 성과로 남는 해입니다."
        if kind == "watch":
            return f"{text}{_subject_particle(text)} 손실이나 부담으로 남기 쉬운 해입니다."
        return f"핵심: {text}."

    good = by_label("상승 연도") or by_label("좋은 연도")
    caution = by_label("주의 연도")
    topic = by_label("사건 주제")
    good_text = keyword_text(good, "자산 확보")
    caution_text = keyword_text(caution, "책임 전가")
    topic_value = str(topic.get("value") or "주요 분야").strip()
    topic_title = f"{topic_value} 중심" if topic_value and topic_value != "주요 분야" else "주요 분야"
    topic_body = _timing_topic_card_body(topic_value, good_text, caution_text)
    if not topic_body:
        topic_body = body_text(topic, "재물운", kind="topic")
    candidates = [
        _premium_story_card(
            "상승 연도",
            first_value(good) or "상승 연도",
            body_text(good, good_text, kind="good"),
            tone="strong",
            source="timing",
        ),
        _premium_story_card(
            "주의 연도",
            first_value(caution) or "주의 연도",
            body_text(caution, caution_text, kind="watch"),
            tone="watch",
            source="timing",
        ),
        _premium_story_card(
            "주요 분야",
            topic_title,
            topic_body,
            tone="neutral",
            source="timing",
        ),
    ]
    return [
        card
        for card in candidates
        if str(card.get("title") or "").strip() and str(card.get("body") or "").strip()
    ]


def _attach_premium_section_story_cards(section: dict[str, Any]) -> dict[str, Any]:
    cards = _premium_section_story_cards(section)
    if not cards:
        return section
    enriched = dict(section)
    enriched["section_story_cards"] = cards
    return enriched


PREMIUM_REQUIRED_JUDGMENT_MATCH_LABELS: dict[str, dict[str, tuple[str, ...]]] = {
    "money": {
        "재물 형성력": ("재물 기반", "재물 형성력", "타고난 재물의 그릇", "재물 발생력"),
        "수입 창출력": ("현금화 능력", "수입 창출력", "수입 발생력", "수익 전환력"),
        "재주 수익화": ("재능 수익화", "재주 수익화", "수익화 능력"),
        "성과 보상력": ("성과 보상력", "성과 보상", "평가가 따라오는 자리"),
        "자금 운용 안정성": ("자금 운용 안정성", "현금 유동성", "현금 관리", "지출 통제력"),
        "자산화 능력": ("자산 전환력", "자산 확정력", "자산 축적력", "축재력"),
        "투자·거래 판단력": ("투자·거래 판단력", "투자 판단력", "거래 판단력", "투자·거래 감각"),
        "계약·명의 안정성": ("계약·명의 안전성", "계약·명의 안정성", "계약 안정성", "돈을 지켜내는 기준"),
        "채권·미수금 회수력": ("채권·미수금 회수력", "채권 회수력", "미수금 회수력", "몫과 권리"),
        "공동자금 운영력": ("공동자금 안정성", "공동 자금 안정성", "공동자금 운영력", "공동재 관리력"),
        "부채·보증 관리력": ("부채·보증 관리력", "보증 관리력", "채무 관리력", "공동자금 안정성"),
        "가족재산 경계력": ("가족재산 경계력", "가족 자산 경계", "가족 변수 대응력", "공동자금 안정성"),
        "사업 확장성": ("사업 확장성", "사업 확장력", "확장 가능성"),
        "재정 방어력": ("자산 전환력", "계약·명의 안전성", "공동자금 안정성", "손실 원인"),
        "후반 축재력": ("후반 축재력", "후반 재물운", "후반 자산화", "후반 재물 성장"),
        "금전 기준성": ("금전 기준성", "돈을 지켜내는 기준", "금전 기준", "소유권 기준"),
        "재물 주의 연도": ("계약 주의 연도", "재물 주의 연도", "주의 연도"),
        "재물 규모": ("타고난 재물의 그릇", "재물 발생력", "재물 형성력"),
        "수입 경로": ("수입 발생력", "수입 창출력", "수익 전환력", "재물이 들어오는 길"),
        "수익화 능력": ("수익 전환력", "수입 창출력", "재주 수익화", "전문성으로 남는 힘", "확장 가능성"),
        "자산화": ("자산 확정력", "자산 축적력", "축재력", "재산으로 굳어지는 힘"),
        "금전 운용": ("자산 확정력", "공동 자금 안정성", "계약·명의 안정성", "돈을 지켜내는 기준", "지출 통제력"),
        "몫과 권리": ("계약·명의 안정성", "계약 안정성", "돈을 지켜내는 기준"),
        "공동 자금": ("공동 자금 안정성", "공동 자금 관리력", "공동재 관리력", "재물에 얽히는 사람 문제"),
        "확장성": ("확장 가능성", "사업 확장력", "재주 수익화"),
        "손실 원인": ("공동 자금 안정성", "계약·명의 안정성", "지출 통제력", "자산 확정력"),
    },
    "career": {
        "직업 적성": ("직무 적합도", "직업 적합", "직업적 성취의 그릇"),
        "직업 분야": ("직무 적합도", "전문성 자산화", "독립 기반"),
        "성취 축적력": ("전문성 자산화", "성취 축적력", "성과 구현력"),
        "평가·명예 전환력": ("평가 상승력", "평가와 명예", "평가가 따라오는 자리"),
        "사회적 도약성": ("사회적 도약성", "사회적 성공 잠재력", "사회적 영향력", "사회적 성취"),
        "권한 확보력": ("권한 확보", "권한 확보력", "권한과 책임의 균형"),
        "책임·권한 균형": ("책임·권한 균형", "책임과 권한의 균형", "권한과 책임의 균형", "권한·책임 균형도"),
        "보상 협상력": ("보상 협상력", "성과 보상력", "권한 확보", "평가가 따라오는 자리"),
        "전문 자산화": ("전문성 자산화", "전문성으로 남는 힘", "전문성 축적도"),
        "조직 적응력": ("조직 지속력", "조직 적응력", "조직 안에서 자리 잡는 힘"),
        "소속 전환력": ("소속 전환력", "직업 전환 연도", "조직 적응력", "변화 대응력"),
        "독립 가능성": ("독립 기반", "독립 가능성", "사업 확장성"),
        "업무 조건 감별력": ("권한 확보", "조직 지속력", "직업 주의 연도"),
        "직업 전환 연도": ("직업 전환 연도", "직업 상승 연도", "독립 기반"),
        "일의 방식": ("직업적 성취의 그릇", "성과 구현력", "직업 성취력"),
        "성취 구조": ("직업적 성취의 그릇", "성과 구현력", "평가가 따라오는 자리", "전문성으로 남는 힘"),
        "평가 방식": ("평가가 따라오는 자리", "평가 확보력", "업무 평가력"),
        "권한과 보상": ("권한과 책임의 균형", "권한 책임 균형도", "권한·책임 균형도"),
        "전문 자산": ("전문성으로 남는 힘", "전문성 축적도", "전문성"),
        "조직과 독립": ("조직 안에서 자리 잡는 힘", "독립 가능성", "조직 적응력"),
        "피해야 할 자리": ("권한과 책임의 균형", "조직 안에서 자리 잡는 힘", "평가가 따라오는 자리"),
        "직업 상승 시기": ("평가가 따라오는 자리", "직업적 성취의 그릇", "독립 가능성", "좋은 연도"),
    },
    "love": {
        "인연 형성력": ("호감 형성력", "인연 형성력", "인연이 들어오는 길"),
        "끌림의 기준": ("애정 기준", "끌림의 기준", "호감 형성력"),
        "상대 선택력": ("상대 선택력", "끌림의 기준", "애정 기준", "배우자 적합도"),
        "관계 진전력": ("관계 진전력", "호감 형성력", "결혼 연결성"),
        "관계 주도권": ("관계 주도권", "관계 속도 조절력", "관계 거리", "관계 진전력"),
        "관계 속도 조절력": ("관계 속도 조절력", "관계 속도", "관계 진전력", "관계 진전"),
        "애정 표현성": ("표현 전달력", "애정 표현성", "애정 표현력"),
        "정서 수용력": ("정서 수용력", "오해 회복력", "관계 지속력", "관계 안정성"),
        "관계 지속력": ("관계 지속력", "관계 안정성", "오해 회복력"),
        "연락·거리 안정성": ("연락·거리 안정성", "관계 거리", "관계 지속력", "관계 안정성"),
        "오해 조정력": ("오해 회복력", "표현 전달력", "관계 지속력"),
        "갈등 관리력": ("오해 회복력", "관계 지속력", "표현 전달력"),
        "주변 개입 관리력": ("주변 개입 관리력", "주변 변수 관리력", "외부 개입 관리력", "관계 경계"),
        "재회 가능성": ("관계 지속력", "오해 회복력", "인연 형성력"),
        "결혼 연결력": ("결혼 연결성", "결혼 연결력", "결혼 현실성"),
        "인연 유입": ("인연 형성력", "호감 형성력", "인연이 들어오는 길"),
        "관계 진전": ("인연 형성력", "호감 형성력", "결혼 현실성", "관계가 오래 가는 힘"),
        "애정 표현": ("애정 표현성", "애정 표현력", "애정이 표현되는 방식"),
        "관계 지속": ("관계 지속력", "관계 안정성", "관계가 오래 가는 힘"),
        "이별 위험": ("관계 지속력", "생활 안정성", "가족 변수 관리력", "애정 표현성"),
        "미련과 재회": ("관계 지속력", "인연 형성력", "지나온 연도", "과거 대조"),
        "결혼 연결": ("결혼 현실성", "결혼 현실화", "결혼으로 이어지는 현실성"),
    },
    "marriage": {
        "혼인 성향": ("혼인 결정력", "혼인 성향", "결혼 현실성", "결혼 현실화"),
        "배우자상": ("배우자 적합도", "생활 기반", "결혼 안정성", "배우자 관계 안정성"),
        "결혼 적기": ("혼인 결정력", "결혼 적기", "결혼 현실성", "전환 연도"),
        "결혼 현실화력": ("결혼 현실화력", "결혼 현실성", "혼인 결정력", "결혼 현실화"),
        "생활 안정": ("생활 기반", "생활 안정성", "생활 기반이 잡히는 방식"),
        "가정 운영력": ("가정 운영력", "생활 기반", "생활 안정성", "가족 책임감"),
        "주거·생활 설계력": ("주거·생활 설계력", "생활 기반", "생활 안정성", "주거 계획"),
        "부부 재정": ("부부 재정 안정성", "공동자금 안정성", "계약·명의 안전성", "자산 확정력"),
        "생활비 기준성": ("생활비 기준성", "부부 재정 안정성", "생활 기반", "금전 기준성"),
        "부부 갈등 조정력": ("결혼 지속력", "가족 변수 대응력", "부부 재정 안정성", "주의 연도"),
        "부부 갈등 회복성": ("부부 갈등 회복성", "결혼 지속력", "갈등 관리력", "오해 회복력"),
        "가족 변수": ("가족 변수 대응력", "가족 변수 관리력", "가족 책임을 감당하는 힘"),
        "배우자 가족 경계": ("배우자 가족 경계", "가족 변수 대응력", "가족 변수 관리력", "관계 경계"),
        "자녀·양육 책임": ("자녀·양육 책임", "자녀 양육 책임", "양육 책임", "가족 책임감"),
        "배우자 복": ("배우자 적합도", "결혼 지속력", "생활 기반", "관계 지속력"),
        "결혼 지속력": ("결혼 지속력", "오해 회복력", "결정 지속력", "생활 기반"),
    },
}


PREMIUM_REQUIRED_JUDGMENT_SENTENCES: dict[str, dict[str, tuple[str, str, str]]] = {
    "money": {
        "재물 규모": (
            "재물 형성력은 선명합니다. 직업 성과와 거래 기회가 일정한 금액 단위로 이어집니다. 시간이 갈수록 다루는 돈의 크기도 올라갑니다.",
            "재물 형성은 안정권입니다. 고정 수입을 바탕으로 거래와 자산의 폭이 넓어집니다. 한 번의 큰돈보다 반복되는 수입에서 힘이 납니다.",
            "후반으로 갈수록 재물의 윤곽이 뚜렷해집니다. 초반에는 큰 금액보다 고정 수입과 현금 기반이 먼저입니다. 무리한 확장은 손실을 남깁니다.",
        ),
        "재물 규모 확장력": (
            "재물의 단위가 커질 가능성이 높습니다. 고정 수입을 넘어 거래 단위와 보유 자산의 폭이 함께 올라갑니다.",
            "재물 규모는 단계적으로 넓어집니다. 안정적인 수입 기반 위에서 큰 거래와 자산 형성이 붙습니다.",
            "재물 규모 확장은 신중해야 합니다. 큰 거래보다 고정 수입과 보유 자산을 먼저 굳혀야 손실이 줄어듭니다.",
        ),
        "수입 경로": (
            "수입 창출력은 강합니다. 직업 성과, 매출, 계약금처럼 계산 가능한 대가에서 돈이 들어옵니다.",
            "수입은 일의 대가가 분명할 때 안정됩니다. 역할과 보상 기준이 맞으면 돈이 꾸준히 들어옵니다.",
            "수입 기회는 있어도 보상 기준이 흔들리기 쉽습니다. 일한 양보다 받을 몫을 먼저 확정해야 합니다.",
        ),
        "성과 보상력": (
            "성과가 보상으로 환산되는 힘이 좋습니다. 연봉, 성과급, 수수료, 계약금처럼 자기 몫이 분명한 자리에서 강합니다.",
            "성과 보상은 계약 조건과 역할 범위가 맞을 때 커집니다. 해낸 일의 이름이 본인에게 남아야 받을 몫도 커집니다.",
            "성과에 비해 남는 보상이 작아지기 쉽습니다. 일은 본인이 해도 몫을 나누는 사람이 많아질 수 있습니다.",
        ),
        "수익화 능력": (
            "재주가 실제 수입으로 바뀝니다. 기술과 말, 콘텐츠가 시장에서 가격을 얻습니다.",
            "재주는 있으나 수익 구조가 늦게 잡힙니다. 결과물과 단가가 선명해야 수입으로 이어집니다.",
            "재능에 비해 수입 전환이 늦습니다. 결과물이 시장에서 단가를 얻기 전까지 보상은 제한됩니다.",
        ),
        "자산화": (
            "자산화가 강합니다. 현금보다 소유권, 지분, 장기 보유 자산으로 남길 때 재물운이 크게 살아납니다.",
            "재산은 권리가 남는 방식에서 만들어집니다. 부동산, 지분, 장기 예치처럼 소유권이 분명한 형태가 맞습니다.",
            "수입이 자산으로 굳기 전에 빠져나가기 쉽습니다. 소비보다 명의와 소유권을 먼저 남겨야 합니다.",
        ),
        "투자·거래 판단력": (
            "투자와 거래에서는 회수 가능성을 먼저 잡습니다. 명의, 기간, 상대 신뢰도가 맞을 때 금전 판단이 강해집니다.",
            "투자와 거래는 수익 가능성만으로 움직이면 불리합니다. 회수 시점과 권리 구조가 분명해야 손실이 줄어듭니다.",
            "급하게 들어온 투자 제안은 손실로 번지기 쉽습니다. 수익 설명보다 명의와 회수 조건을 먼저 확인해야 합니다.",
        ),
        "금전 운용": (
            "금전 운용은 비교적 단단합니다. 생활비와 투자금을 구분할수록 재정의 흔들림이 줄어듭니다.",
            "금전 운용은 배분 기준에서 갈립니다. 고정비, 투자금, 예비 자금을 먼저 분리해야 합니다.",
            "금전 기준이 불분명하면 지출이 빠르게 늘어납니다. 생활비와 투자금을 섞으면 손실이 커집니다.",
        ),
        "부채·보증 관리력": (
            "부채와 보증에서는 책임 범위를 분명히 잡아야 손실을 줄입니다. 빌려주는 돈보다 회수 조건이 먼저입니다.",
            "대여와 보증은 신중하게 다뤄야 합니다. 상대의 사정에 끌려가면 책임만 커질 수 있습니다.",
            "부채와 보증은 손실로 번지기 쉽습니다. 명의, 담보, 상환 시점을 확인하지 않으면 부담이 오래 남습니다.",
        ),
        "가족재산 경계력": (
            "가족 재산에서도 자기 몫과 책임선이 분명해야 합니다. 정리된 명의가 재물을 보호합니다.",
            "가족과 얽힌 돈은 감정으로 처리하면 불리합니다. 상속성 자산과 지원금은 처음 기준이 중요합니다.",
            "가족 재산 문제에서는 자기 몫이 흐려질 수 있습니다. 대신 떠안은 지출이 재물 손실로 이어지기 쉽습니다.",
        ),
        "금전 기준성": (
            "돈 앞에서 기준이 분명합니다. 정, 체면, 분위기보다 소유권과 보상 원칙을 먼저 잡아야 재산이 축적됩니다.",
            "금전 기준은 늦게 세우면 불리합니다. 친한 사이라도 지급일, 몫, 명의를 먼저 정해야 합니다.",
            "돈 문제를 좋게 넘기면 손실이 커집니다. 처음부터 자기 몫과 책임 범위를 나눠야 합니다.",
        ),
        "몫과 권리": (
            "계약과 명의로 금전 권리를 지킬 수 있습니다. 지급일, 지분, 수령액이 문서에 남을수록 재물이 안정됩니다.",
            "금전 관계에서는 지급일과 권리 조건을 먼저 남길수록 받을 몫이 안정됩니다.",
            "계약과 명의가 흐리면 받을 몫이 줄어듭니다. 구두 약속과 늦은 정산은 손실로 이어집니다.",
        ),
        "채권·미수금 회수력": (
            "받아야 할 돈은 회수 조건이 분명할 때 안정됩니다. 지급일과 증빙이 남아야 자기 몫이 지켜집니다.",
            "미수금과 대여금은 늦게 정리할수록 불리합니다. 금액보다 회수 시점이 먼저 확정되어야 합니다.",
            "받을 돈을 말로만 넘기면 손실이 됩니다. 지급일, 명의, 증빙을 남기지 않으면 회수가 늦어집니다.",
        ),
        "공동 자금": (
            "공동자금에서도 자기 몫을 지킬 수 있습니다. 명의와 지분을 먼저 잡으면 사람과 함께 다루는 돈도 안정됩니다.",
            "공동자금은 몫과 명의가 먼저입니다. 가까운 사람일수록 지분을 먼저 정하면 관계와 자금이 함께 안정됩니다.",
            "공동자금은 손실의 중심이 되기 쉽습니다. 호의로 시작한 돈이 명의, 지분, 보증 문제로 바뀔 수 있습니다.",
        ),
        "확장성": (
            "고정 수입 바깥의 거래와 사업성 기회로 재물이 커집니다. 단가와 권리 구조가 재물의 폭을 키웁니다.",
            "거래 단위와 회수 기준이 맞을 때 재물 규모가 커집니다.",
            "확장을 서두르면 이익보다 책임이 먼저 커집니다. 회수 가능한 구조부터 잡아야 합니다.",
        ),
        "손실 원인": (
            "손실은 돈을 못 벌어서가 아니라 권리 정리가 늦을 때 생깁니다. 명의, 보증, 정산을 늦게 잡으면 손해가 커집니다.",
            "손실은 작은 기준을 넘기면서 시작됩니다. 지급일과 몫을 늦게 정하면 나중에 말이 달라집니다.",
            "가장 큰 손실은 가까운 사람과의 금전 관계에서 옵니다. 호의로 시작한 돈이 책임으로 돌아오기 쉽습니다.",
        ),
        "후반 축재력": (
            "후반으로 갈수록 재물 단위가 커집니다. 수입보다 소유권과 장기 자산이 재물운의 핵심이 됩니다.",
            "후반 재물은 천천히 굳어지는 편입니다. 고정 수입과 자산 보유 구조가 맞을수록 안정됩니다.",
            "후반 자산화가 늦어질 수 있습니다. 큰 확장보다 이미 생긴 돈을 권리로 남기는 판단이 먼저입니다.",
        ),
    },
    "career": {
        "일의 방식": (
            "직업운은 단순 실행보다 책임 있는 운영에서 강합니다. 흩어진 일을 정리하고 결과를 확정하는 자리에서 평가가 올라갑니다.",
            "직업운은 맡은 일을 끝까지 결과로 남길 때 살아납니다. 역할의 범위가 분명해야 합니다.",
            "일의 범위가 불분명하면 성과가 자기 이름으로 남지 않습니다. 맡은 범위와 마감 지점이 선명해야 합니다.",
        ),
        "직업 분야": (
            "직업명보다 업무의 성격이 중요합니다. 운영, 기획, 관리처럼 결과와 책임이 남는 일이 잘 맞습니다.",
            "넓은 직업군보다 맡는 역할을 정확히 가려야 합니다. 조율, 관리, 분석이 들어간 일이 맞습니다.",
            "흥미만으로 고른 일은 오래가기 어렵습니다. 권한과 결과물이 남는 분야를 잡아야 합니다.",
        ),
        "성취 구조": (
            "성과는 한 번의 기회보다 누적된 결과물에서 커집니다. 기록과 실적이 쌓일수록 경력의 값이 올라갑니다.",
            "성취는 천천히 쌓이는 쪽입니다. 빠른 인정보다 결과물을 남기는 일이 강합니다.",
            "성과가 자기 이름으로 남지 않기 쉽습니다. 책임 범위와 결과물이 분명하지 않으면 경력의 값이 늦게 올라갑니다.",
        ),
        "평가 방식": (
            "평가는 말보다 기록과 결과물에서 올라옵니다. 공식 평가로 남는 일이 유리합니다.",
            "성과는 있지만 기록이 약하면 평가가 늦습니다. 결과물이 남아야 평판이 붙습니다.",
            "평가 기준이 흐린 자리에서는 공로가 남에게 넘어가기 쉽습니다. 기록과 권한 체계가 먼저입니다.",
        ),
        "승진·직함 가능성": (
            "승진과 직함이 붙는 자리까지 올라갈 수 있습니다. 성과가 공식 기록으로 남을수록 책임자 역할이 가까워집니다.",
            "승진 가능성은 있습니다. 다만 실적이 개인 노력으로만 끝나지 않고 조직의 공식 평가로 남아야 합니다.",
            "직함보다 실무 책임이 먼저 커질 수 있습니다. 권한 없는 책임은 경력의 손실로 남기 쉽습니다.",
        ),
        "사회적 도약성": (
            "직업 성취가 지위와 영향력으로 커집니다. 개인 실적이 조직 안팎의 자리로 이어질 수 있습니다.",
            "사회적 도약은 역할 확대에서 시작됩니다. 맡는 범위가 넓어질 때 이름이 따라옵니다.",
            "성과가 있어도 사회적 자리로 옮겨가는 속도는 늦을 수 있습니다. 평가 기준과 공식 권한을 먼저 확보해야 합니다.",
        ),
        "권한과 보상": (
            "책임에 맞는 결정권을 받아야 성취가 본인 이력으로 남습니다.",
            "책임은 커지지만 보상이 늦게 따라올 수 있습니다. 맡은 범위와 결정권을 분명히 해야 합니다.",
            "책임만 크고 결정권이 약한 자리는 손해입니다. 성과가 있어도 본인 이력으로 남지 않습니다.",
        ),
        "보상 협상력": (
            "성과가 보수로 확정되기 쉽습니다. 연봉, 성과급, 수수료처럼 자기 몫이 분명한 자리가 유리합니다.",
            "성과에 비해 보상 확정이 늦을 수 있습니다. 맡은 역할과 대가를 초기에 맞춰야 합니다.",
            "보상 기준이 불분명하면 성과가 남의 평가로만 끝납니다. 계약 조건이 먼저 서야 자기 몫이 남습니다.",
        ),
        "책임·권한 균형": (
            "책임과 권한이 함께 붙는 자리에서 직업운이 강해집니다. 결정권 없는 책임은 경력의 손실로 남기 쉽습니다.",
            "책임은 커지지만 권한이 늦게 따라올 수 있습니다. 보고 체계와 결정 범위를 먼저 확인해야 합니다.",
            "책임만 떠안는 자리는 피해야 합니다. 문제가 생겼을 때 이름만 남고 보상은 늦어질 수 있습니다.",
        ),
        "전문 자산": (
            "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다. 시간이 갈수록 대체하기 어려운 역할이 됩니다.",
            "전문성은 천천히 쌓이지만 한 번 자리 잡으면 협상력이 됩니다.",
            "전문 분야가 불분명하면 경력의 값이 늦게 올라갑니다. 넓은 경험보다 선명한 전문성이 먼저입니다.",
        ),
        "조직과 독립": (
            "조직 안에서는 역할이 분명해야 오래 갑니다. 조직 밖에서는 자기 이름으로 팔 수 있는 전문성이 승부처입니다.",
            "조직과 독립은 기준이 다릅니다. 조직에서는 역할이, 독립에서는 고객과 단가가 핵심입니다.",
            "조직 밖으로 나가는 일은 서둘러 잡기 어렵습니다. 고객층과 상품성이 먼저 준비되어야 합니다.",
        ),
        "소속 전환력": (
            "소속이 바뀌어도 맡을 역할을 빠르게 잡는 편입니다. 부서, 회사, 직무가 바뀔 때 새 기회를 만들 수 있습니다.",
            "소속 전환은 가능하지만 준비가 필요합니다. 직무 이름보다 맡을 권한과 보상 기준이 중요합니다.",
            "무리한 이직과 전환은 손실을 남깁니다. 새 자리의 권한과 평가 기준이 불분명하면 오래가기 어렵습니다.",
        ),
        "피해야 할 자리": (
            "피해야 할 자리는 책임만 크고 결정권이 약한 자리입니다. 성과가 있어도 자기 경력으로 남기 어렵습니다.",
            "평가 기준이 자주 바뀌는 자리는 소모가 큽니다. 무엇을 잘해야 인정받는지 보이지 않으면 오래 버티기 어렵습니다.",
            "일은 많고 권한은 약한 자리가 가장 불리합니다. 문제가 생겼을 때 책임만 남기 쉽습니다.",
        ),
        "직업 상승 시기": (
            "직업이 올라가는 시기에는 역할과 보상이 동시에 바뀝니다. 직함보다 단가 변화가 먼저 보입니다.",
            "상승 시기에는 맡는 일이 넓어집니다. 그때 결과물을 남기면 다음 자리로 넘어가기 쉽습니다.",
            "직업 전환기는 무리하게 넓히기보다 경력의 이름을 정리해야 합니다. 무엇으로 평가받을지가 먼저 정리되어야 합니다.",
        ),
    },
    "love": {
        "끌림의 기준": (
            "상대의 말보다 태도와 생활 감각에서 마음이 움직입니다. 말이 화려한 사람보다 약속이 일정하고 생활 태도가 안정된 사람에게 오래 끌립니다.",
            "호감은 쉽게 생겨도 깊어지는 데에는 시간이 걸립니다. 상대의 책임감을 확인하려 합니다.",
            "첫 호감만으로 관계가 오래가지는 않습니다. 말보다 행동이 맞아야 관계가 깊어집니다.",
        ),
        "상대 선택력": (
            "상대를 고를 때 순간의 호감보다 오래 맞을 생활 기준을 중시합니다. 처음 끌려도 책임감이 보이지 않으면 마음을 오래 열지 않습니다.",
            "끌림은 생겨도 쉽게 확정하지 않습니다. 상대의 태도와 생활 감각을 확인한 뒤 관계를 진전시킵니다.",
            "상대 선택이 흔들리면 관계가 피곤해집니다. 외적인 매력보다 책임감과 생활 기준을 먼저 확인해야 합니다.",
        ),
        "상대 신뢰 감별력": (
            "상대의 말보다 태도와 책임감을 빠르게 가려냅니다. 오래 갈 사람과 피해야 할 사람을 구분하는 눈이 좋습니다.",
            "호감이 생겨도 상대를 곧바로 믿지는 않습니다. 반복된 태도와 약속을 확인한 뒤 마음을 줍니다.",
            "호감이 앞서면 상대의 책임감을 늦게 확인할 수 있습니다. 말보다 반복된 행동을 기준으로 삼아야 합니다.",
        ),
        "인연 유입": (
            "인연은 갑작스러운 사건보다 생활권의 반복 접점에서 들어옵니다. 자주 마주치는 자리, 협업, 반복된 연락에서 관계가 실제 인연으로 굳습니다.",
            "만남은 넓은 소개보다 자주 마주치는 자리에서 생기기 쉽습니다.",
            "인연이 들어와도 관계로 굳는 속도는 느릴 수 있습니다. 상대를 오래 확인하는 편입니다.",
        ),
        "인연 형성력": (
            "인연은 갑작스러운 사건보다 생활권의 반복 접점에서 들어옵니다. 자주 마주치는 자리, 협업, 반복된 연락에서 관계가 실제 인연으로 굳습니다.",
            "만남은 넓은 소개보다 자주 마주치는 자리에서 생기기 쉽습니다.",
            "인연이 들어와도 관계로 굳는 속도는 느릴 수 있습니다. 상대를 오래 확인하는 편입니다.",
        ),
        "관계 진전": (
            "호감이 생기면 실제 연애로 넘어갑니다. 주변에서도 관계가 드러나기 쉽습니다.",
            "관계 진전은 빠르기보다 확인을 거쳐 움직입니다. 상대의 태도가 분명해질 때 관계가 깊어집니다.",
            "호감은 있어도 관계를 공식화하는 데 시간이 걸립니다. 망설임이 길어지면 상대가 먼저 지칠 수 있습니다.",
        ),
        "관계 진전력": (
            "호감이 생기면 실제 연애로 넘어갑니다. 주변에서도 관계가 드러나기 쉽습니다.",
            "관계 진전은 빠르기보다 확인을 거쳐 움직입니다. 상대의 태도가 분명해질 때 관계가 깊어집니다.",
            "호감은 있어도 관계를 공식화하는 데 시간이 걸립니다. 망설임이 길어지면 상대가 먼저 지칠 수 있습니다.",
        ),
        "관계 속도 조절력": (
            "마음이 움직여도 관계를 서두르지 않습니다. 만남과 약속의 속도가 맞을 때 오래 갑니다.",
            "관계 속도는 상대와 맞춰야 안정됩니다. 마음보다 약속이 앞서면 부담이 생깁니다.",
            "속도가 어긋나면 호감이 있어도 관계가 지칩니다. 연락과 만남의 간격을 분명히 해야 합니다.",
        ),
        "관계 주도권": (
            "관계의 방향을 상대에게만 맡기지 않습니다. 거리와 속도를 스스로 정할 때 안정됩니다.",
            "관계 주도권은 늦게 잡히는 편입니다. 상대의 요구에 맞추다 보면 피로가 생길 수 있습니다.",
            "상대에게 끌려가는 관계는 오래가기 어렵습니다. 만남의 속도와 약속의 기준을 분명히 해야 합니다.",
        ),
        "애정 표현": (
            "호감이 생기면 말과 행동이 비교적 분명해집니다.",
            "마음은 깊어도 표현 속도가 늦습니다. 상대가 확신을 얻는 데 시간이 걸립니다.",
            "마음이 있어도 표현이 늦으면 상대는 확신을 늦게 얻습니다.",
        ),
        "애정 표현성": (
            "호감이 생기면 말과 행동이 비교적 분명해집니다.",
            "마음은 깊어도 표현 속도가 늦습니다. 상대가 확신을 얻는 데 시간이 걸립니다.",
            "마음이 있어도 표현이 늦으면 상대는 확신을 늦게 얻습니다.",
        ),
        "관계 지속": (
            "한 번 깊어진 관계는 쉽게 끊지 않습니다. 검증된 상대에게 오래 머무르는 편입니다.",
            "관계는 길게 이어지는 편입니다. 다만 서운함을 오래 넘기면 한 번에 멀어질 수 있습니다.",
            "감정이 깊어도 생활 기준이 어긋나면 관계가 쉽게 지칩니다.",
        ),
        "관계 지속력": (
            "한 번 깊어진 관계는 쉽게 끊지 않습니다. 검증된 상대에게 오래 머무르는 편입니다.",
            "관계는 길게 이어지는 편입니다. 다만 서운함을 오래 넘기면 한 번에 멀어질 수 있습니다.",
            "감정이 깊어도 생활 기준이 어긋나면 관계가 쉽게 지칩니다.",
        ),
        "연락·거리 안정성": (
            "가까워진 뒤에도 개인 시간과 연락 간격을 지켜야 관계가 안정됩니다.",
            "연락과 거리의 기준이 맞으면 관계가 오래 갑니다. 지나친 확인은 서로를 지치게 합니다.",
            "연락 빈도와 사생활의 기준이 어긋나면 감정 소모가 커집니다.",
        ),
        "이별 위험": (
            "이별 위험은 감정이 식어서보다 기준이 어긋날 때 커집니다. 약속과 책임이 맞지 않으면 거리가 생깁니다.",
            "관계가 멀어지는 원인은 표현 부족보다 확인 지연에 있습니다. 상대가 기다리는 시간이 길어질 수 있습니다.",
            "끊어지는 관계는 갑자기 끝나지 않습니다. 연락과 약속이 느슨해지면서 이미 멀어져 있습니다.",
        ),
        "오해 조정력": (
            "상대가 서운함을 느끼는 지점이 반복될 수 있습니다. 표현과 연락의 속도가 맞지 않을 때 문제가 커집니다.",
            "오해는 큰 사건보다 작은 확인 지연에서 시작됩니다. 상대가 기다리는 시간이 길어질 수 있습니다.",
            "말하지 않고 넘긴 감정이 뒤늦게 올라옵니다. 연락과 약속의 기준을 분명히 해야 합니다.",
        ),
        "정서 수용력": (
            "상대의 불안과 서운함을 받아낼 수 있습니다. 감정이 커지기 전에 말을 맞추면 관계가 안정됩니다.",
            "상대의 감정을 이해해도 표현이 늦을 수 있습니다. 확인을 미루면 서운함이 쌓입니다.",
            "정서적인 요구가 많아지면 쉽게 지칠 수 있습니다. 무조건 맞춰주기보다 감정의 기준을 세워야 합니다.",
        ),
        "갈등 관리력": (
            "갈등은 사랑이 부족해서보다 생활 기준이 어긋날 때 커집니다.",
            "감정 표현보다 약속의 방식에서 갈등이 생기기 쉽습니다.",
            "연락, 시간, 책임의 기준이 어긋나면 관계가 빠르게 피곤해집니다.",
        ),
        "주변 개입 관리력": (
            "주변 사람의 말이 관계 안으로 들어와도 쉽게 흔들리지 않습니다. 두 사람의 기준을 먼저 세우는 편입니다.",
            "친구, 가족, 과거 인연의 말이 관계에 영향을 줄 수 있습니다. 관계 밖의 의견과 두 사람의 결정을 나누어야 합니다.",
            "주변 개입이 커지면 관계가 빠르게 흔들립니다. 제삼자의 말보다 두 사람의 약속이 먼저여야 합니다.",
        ),
        "미련과 재회": (
            "지나간 관계가 쉽게 사라지지는 않습니다. 마음이 정리된 뒤에도 다시 연락이 닿을 가능성이 있습니다.",
            "재회는 감정보다 상황이 다시 맞을 때 올라옵니다. 서로의 생활 조건이 달라지면 다시 생각할 수 있습니다.",
            "미련은 오래 남을 수 있지만 재회가 곧 안정은 아닙니다. 같은 문제가 반복되는지 먼저 확인해야 합니다.",
        ),
        "재회 가능성": (
            "지나간 관계가 쉽게 사라지지는 않습니다. 마음이 정리된 뒤에도 다시 연락이 닿을 가능성이 있습니다.",
            "재회는 감정보다 상황이 다시 맞을 때 올라옵니다. 서로의 생활 조건이 달라지면 다시 생각할 수 있습니다.",
            "미련은 오래 남을 수 있지만 재회가 곧 안정은 아닙니다. 같은 문제가 반복되는지 먼저 확인해야 합니다.",
        ),
        "결혼 연결": (
            "연애가 깊어지면 결혼 이야기가 구체화됩니다. 주거와 생활비 문제가 빠르게 따라붙습니다.",
            "결혼은 감정보다 생활 기준이 맞을 때 구체화됩니다.",
            "마음이 있어도 결혼 결정은 늦어질 수 있습니다. 주거와 가족 문제가 먼저 걸립니다.",
        ),
        "결혼 연결력": (
            "연애가 깊어지면 결혼 이야기가 구체화됩니다. 주거와 생활비 문제가 빠르게 따라붙습니다.",
            "결혼은 감정보다 생활 기준이 맞을 때 구체화됩니다.",
            "마음이 있어도 결혼 결정은 늦어질 수 있습니다. 주거와 가족 문제가 먼저 걸립니다.",
        ),
    },
    "marriage": {
        "혼인 성향": (
            "결혼은 감정보다 생활의 안정감을 더 중시합니다. 결혼을 결정할 때도 마음이 깊은지보다 함께 생활이 버틸 수 있는지를 먼저 따집니다.",
            "혼인은 서두르기보다 현실 조건을 맞춘 뒤 결정하는 쪽입니다.",
            "감정만으로 결혼을 결정하면 뒤늦은 부담이 커집니다.",
        ),
        "배우자상": (
            "성실하고 기준이 분명한 배우자와 오래 갑니다. 감정 기복이 적고 자기 몫을 조용히 해내는 사람이 결혼 상대로 맞습니다.",
            "말보다 약속을 지키는 상대에게 마음이 안정됩니다.",
            "감정 기복이 큰 상대와는 결혼 뒤 생활 손상이 먼저 드러납니다.",
        ),
        "결혼 적기": (
            "결혼 적기에는 약속이 빠르게 구체화됩니다. 주거와 생활 계획이 먼저 움직입니다.",
            "결혼은 감정이 깊어진 뒤 생활 기준이 정리될 때 성사됩니다. 준비가 늦으면 시기도 늦어집니다.",
            "결혼 결정은 서두르면 부담이 커집니다. 주거와 재정 기준이 잡힌 해를 기다리는 편이 낫습니다.",
        ),
        "결혼 현실화력": (
            "결혼 의사가 실제 절차로 이어지기 쉽습니다. 주거와 가족 협의가 잡히면 결정이 빠르게 굳어집니다.",
            "결혼 마음은 있어도 현실 준비가 늦어질 수 있습니다. 주거, 일정, 가족 협의가 따라와야 성사됩니다.",
            "감정만으로 결혼을 밀어붙이면 부담이 큽니다. 절차와 생활 기준이 어긋나면 결정이 늦어집니다.",
        ),
        "생활 안정": (
            "주거와 생활비가 정리될수록 결혼이 안정됩니다.",
            "결혼 생활은 감정보다 생활 기준이 정리될 때 오래 갑니다.",
            "생활 기준이 어긋나면 애정이 있어도 결혼 생활이 흔들립니다.",
        ),
        "주거·생활 설계력": (
            "집, 생활비, 시간 사용의 기준이 잡히면 결혼 생활이 안정됩니다.",
            "주거와 생활 설계는 결혼 안정의 핵심입니다. 역할 분담이 늦으면 갈등이 반복됩니다.",
            "감정은 있어도 생활 설계가 약하면 결혼 부담이 커집니다. 주거와 생활비 기준을 먼저 잡아야 합니다.",
        ),
        "가정 운영력": (
            "가정 안에서 일정과 책임을 정리합니다. 생활 기준이 잡히면 결혼 뒤 안정감이 커집니다.",
            "가정 운영은 감정보다 역할 배분에서 갈립니다. 집안일, 가족 책임, 지출 기준을 맞춰야 합니다.",
            "가정의 책임이 한쪽으로 몰리면 결혼 생활이 지칩니다. 역할과 비용의 기준을 처음부터 나눠야 합니다.",
        ),
        "부부 재정": (
            "부부 사이에서도 명의와 지출 기준이 분명해야 재산이 지켜집니다.",
            "공동 생활비와 개인 자산을 구분해야 결혼 뒤 돈 문제가 줄어듭니다.",
            "부부 재정이 섞이면 한쪽의 책임이 커집니다. 명의와 지출 기준이 핵심입니다.",
        ),
        "생활비 기준성": (
            "생활비 기준이 분명할수록 결혼 생활의 마찰이 줄어듭니다. 반복 지출과 저축선이 먼저 잡혀야 합니다.",
            "생활비는 감정 문제가 되기 쉽습니다. 고정비와 저축 기준을 늦게 정하면 서운함이 남습니다.",
            "생활비 기준이 흐리면 결혼 뒤 돈 문제가 반복됩니다. 가족 지원금과 개인 지출을 분리해야 합니다.",
        ),
        "부부 갈등 조정력": (
            "부부 갈등은 감정 싸움보다 역할 불균형에서 시작됩니다. 한쪽만 책임을 떠안으면 금방 지칩니다.",
            "갈등은 돈보다 기준에서 커집니다. 생활비와 가족 책임의 배분이 핵심입니다.",
            "결혼 뒤에는 가족 문제와 생활비가 갈등의 핵심이 됩니다. 처음 약속이 흐리면 오래 남습니다.",
        ),
        "부부 갈등 회복성": (
            "감정이 상한 뒤에도 생활 기준을 다시 맞출 수 있습니다. 사과보다 역할과 책임을 정리해야 회복됩니다.",
            "갈등 이후에도 회복 여지는 남습니다. 다만 같은 문제를 말로만 넘기면 다시 반복됩니다.",
            "부부 갈등은 회복이 늦어질 수 있습니다. 생활비, 가족 책임, 역할 분담을 다시 정해야 합니다.",
        ),
        "가족 변수": (
            "가족 문제를 감당하는 편입니다. 다만 부부 사이의 기준이 먼저 서야 합니다.",
            "가족 책임은 결혼 생활에 직접 들어오기 쉽습니다. 역할 분담이 분명해야 합니다.",
            "가족 문제가 부부 사이로 들어오면 결혼 생활의 부담이 커집니다.",
        ),
        "배우자 가족 경계": (
            "배우자 가족과 원가족 사이에서 책임선을 분명히 해야 합니다. 정으로 떠안은 부담은 부부 문제로 돌아올 수 있습니다.",
            "배우자 가족 문제는 초기에 기준을 세워야 안정됩니다. 돈과 돌봄의 범위가 늦게 정해지면 부담이 커집니다.",
            "가족 사이의 부탁을 모두 받아들이면 결혼 생활이 흔들립니다. 부부의 기준을 먼저 세워야 합니다.",
        ),
        "가족 책임 경계력": (
            "양가와 원가족 문제에서 맡을 책임과 끊어낼 책임을 분명히 가릅니다. 부부의 기준을 먼저 세울수록 결혼 생활이 안정됩니다.",
            "가족 책임은 결혼 생활 안으로 들어오기 쉽습니다. 어디까지 감당할지 정해야 부부 사이의 부담이 줄어듭니다.",
            "가족 문제를 정으로만 떠안으면 결혼 생활이 지칩니다. 돈과 돌봄의 책임선을 분명히 나누어야 합니다.",
        ),
        "자녀·양육 책임": (
            "자녀와 양육 문제는 결혼 생활의 중요한 축으로 들어옵니다. 역할과 비용 기준이 잡히면 가정이 안정됩니다.",
            "양육 책임은 한쪽으로 몰리면 부담이 커집니다. 교육비와 돌봄 시간을 현실적으로 나누어야 합니다.",
            "자녀 문제는 감정만으로 감당하기 어렵습니다. 비용, 시간, 가족 지원이 정리되지 않으면 부부 갈등으로 번집니다.",
        ),
        "배우자 복": (
            "배우자에게서 생활의 안정감을 얻습니다. 결혼 뒤 현실 기반이 단단해집니다.",
            "배우자 복은 상대의 성실함에서 드러납니다. 감정보다 생활을 지켜주는 사람이 맞습니다.",
            "배우자에게 기대는 부분이 커지면 부담도 커집니다. 도움과 책임의 균형을 잡아야 합니다.",
        ),
        "혼인 위기 대응력": (
            "돈, 가족, 주거 문제가 겹쳐도 결혼을 쉽게 놓지 않습니다. 감정 싸움보다 현실 기준을 다시 세우며 버팁니다.",
            "결혼 생활의 위기는 넘길 수 있습니다. 다만 같은 문제가 반복되면 생활비와 가족 책임을 다시 정해야 합니다.",
            "혼인 위기에는 감정만으로 버티기 어렵습니다. 돈, 가족, 주거 기준이 정리되지 않으면 갈등이 오래 남습니다.",
        ),
        "결혼 지속력": (
            "결혼은 한 번 정한 약속을 오래 지키는 쪽입니다.",
            "위기는 감정 싸움보다 생활 책임이 한쪽으로 기울 때 옵니다.",
            "약속을 미루는 시간이 길어지면 상대의 불안이 커집니다.",
        ),
    },
}

PREMIUM_REQUIRED_JUDGMENT_SENTENCE_ALIASES: dict[str, dict[str, str]] = {
    "money": {
        "재물 규모 확장력": "재물 규모 확장력",
        "재물 형성력": "재물 규모",
        "수입 창출력": "수입 경로",
        "재주 수익화": "수익화 능력",
        "성과 보상력": "성과 보상력",
        "자금 운용 안정성": "금전 운용",
        "자산화 능력": "자산화",
        "계약·명의 안정성": "몫과 권리",
        "채권·미수금 회수력": "채권·미수금 회수력",
        "공동자금 운영력": "공동 자금",
        "부채·보증 관리력": "부채·보증 관리력",
        "가족재산 경계력": "가족재산 경계력",
        "사업 확장성": "확장성",
        "재정 방어력": "손실 원인",
    },
    "career": {
        "직업 적성": "일의 방식",
        "성취 축적력": "성취 구조",
        "평가·명예 전환력": "평가 방식",
        "승진·직함 가능성": "승진·직함 가능성",
        "권한 확보력": "권한과 보상",
        "보상 협상력": "보상 협상력",
        "전문 자산화": "전문 자산",
        "조직 적응력": "조직과 독립",
        "소속 전환력": "소속 전환력",
        "독립 가능성": "조직과 독립",
        "업무 조건 감별력": "피해야 할 자리",
        "직업 전환 연도": "직업 상승 시기",
    },
    "love": {
        "인연 형성력": "인연 유입",
        "상대 선택력": "상대 선택력",
        "상대 신뢰 감별력": "상대 신뢰 감별력",
        "관계 주도권": "관계 주도권",
        "정서 수용력": "정서 수용력",
        "오해 조정력": "오해 조정력",
        "갈등 관리력": "갈등 관리력",
        "주변 개입 관리력": "주변 개입 관리력",
        "재회 가능성": "미련과 재회",
    },
    "marriage": {
        "결혼 현실화력": "결혼 현실화력",
        "가정 운영력": "가정 운영력",
        "생활비 기준성": "생활비 기준성",
        "부부 갈등 조정력": "부부 갈등 조정력",
        "가족 변수": "가족 변수",
        "가족 책임 경계력": "가족 책임 경계력",
        "자녀·양육 책임": "자녀·양육 책임",
        "혼인 위기 대응력": "혼인 위기 대응력",
        "결혼 지속력": "결혼 지속력",
    },
}


def _premium_required_sentence_templates(domain: str, title: str) -> tuple[str, str, str] | None:
    domain_templates = PREMIUM_REQUIRED_JUDGMENT_SENTENCES.get(domain, {})
    templates = domain_templates.get(title)
    if templates:
        return templates
    alias = PREMIUM_REQUIRED_JUDGMENT_SENTENCE_ALIASES.get(domain, {}).get(title, "")
    if alias:
        return domain_templates.get(alias)
    return None

PREMIUM_REQUIRED_WATCH_TITLES = {
    "손실 원인",
    "피해야 할 자리",
    "이별 위험",
    "오해 조정력",
    "갈등 관리력",
    "부부 갈등 조정력",
    "가족 변수",
    "재물 주의 연도",
    "관계 주의 연도",
    "가족·주거 변동 연도",
    "주의 연도",
}

PREMIUM_REQUIRED_PRESSURE_FACET_LABELS = {
    "공동자금 운영력",
    "계약·명의 안정성",
    "채권·미수금 회수력",
    "투자·거래 판단력",
    "재정 방어력",
    "금전 기준성",
    "책임·권한 균형",
    "업무 조건 감별력",
    "관계 속도 조절력",
    "연락·거리 안정성",
    "주변 개입 관리력",
    "주거·생활 설계력",
    "배우자 가족 경계",
    "자녀·양육 책임",
    "부부 갈등 회복성",
}

PREMIUM_REQUIRED_PRESERVE_TEMPLATE_TITLES = {
    "사업 확장성",
    "결혼 연결력",
}


def _premium_required_grade(score: int | None, *, tone: str = "") -> str:
    if tone in {"watch", "risk", "caution"}:
        return "주의"
    if not isinstance(score, int):
        return "확인"
    if score >= 86:
        return "매우 강함"
    if score >= 66:
        return "강함"
    if score >= 62:
        return "양호"
    if score >= 50:
        return "보완"
    return "주의"


def _premium_required_sentence_level(score: int | None, *, title: str) -> int:
    if title in {
        "손실 원인",
        "피해야 할 자리",
        "이별 위험",
        "오해 조정력",
        "갈등 관리력",
        "부부 갈등 조정력",
        "가족 변수",
        "주의 연도",
        "과거 대조",
    }:
        return 2
    if not isinstance(score, int):
        return 1
    if score >= 74:
        return 0
    if score >= 55:
        return 1
    return 2


def _premium_required_judgment_pool(section: dict[str, Any]) -> list[dict[str, Any]]:
    profile = section.get("visual_profile") if isinstance(section.get("visual_profile"), dict) else {}
    section_profile = section.get("section_profile") if isinstance(section.get("section_profile"), dict) else {}
    pool: list[dict[str, Any]] = []
    domain_facets = section.get("domain_decision_facets") if isinstance(section.get("domain_decision_facets"), dict) else {}
    timing_decision = section.get("timing_decision_facets") if isinstance(section.get("timing_decision_facets"), dict) else {}
    output_goal_coverage = section.get("output_goal_coverage") if isinstance(section.get("output_goal_coverage"), dict) else {}
    coverage_domains = output_goal_coverage.get("domains") if isinstance(output_goal_coverage.get("domains"), dict) else {}
    facet_domains = [_domain_key(section)]
    if facet_domains[0] == "love" and "결혼" in str(section.get("heading") or ""):
        facet_domains.append("marriage")
    for facet_domain in dict.fromkeys(facet_domains):
        for item in domain_facets.get(facet_domain) or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            score = item.get("score")
            pressure_level = str(item.get("pressure_level") or "none")
            has_pressure = bool(item.get("has_pressure")) or pressure_level in {"clear", "severe"}
            pressure_sensitive = label in PREMIUM_REQUIRED_PRESSURE_FACET_LABELS
            tone = (
                "watch"
                if has_pressure
                and (
                    pressure_level == "severe"
                    or pressure_sensitive
                    or (isinstance(score, int) and score < 52)
                )
                else "strong" if isinstance(score, int) and score >= 74 else "neutral"
            )
            pool.append(
                {
                    "source": "domain_decision_facet",
                    "key": str(item.get("key") or "").strip(),
                    "label": label,
                    "score": score,
                    "tone": tone,
                    "has_pressure": has_pressure,
                    "pressure_level": pressure_level,
                    "pressure_score": item.get("pressure_score"),
                    "pressure_reasons": list(item.get("pressure_reasons") or []),
                    "body": str(item.get("meaning") or "").strip(),
                    "layer_coverage": list(item.get("layer_coverage") or []),
                    "raw_layer_coverage": list(item.get("raw_layer_coverage") or []),
                    "cycle_sources": list(item.get("cycle_sources") or []),
                    "principle_edges": list(item.get("principle_edges") or []),
                }
            )
        for item in coverage_domains.get(facet_domain) or []:
            if not isinstance(item, dict):
                continue
            required = str(item.get("required_conclusion") or "").strip()
            if not required:
                continue
            score = item.get("score")
            value = str(item.get("value") or "").strip()
            focus = str(item.get("focus") or "").strip()
            source_label = str(item.get("source_label") or required).strip()
            body = " ".join(part for part in (source_label, value, focus) if part)
            score_value = int(score) if isinstance(score, (int, float)) else score
            pool.append(
                {
                    "source": "output_goal_coverage",
                    "key": str(item.get("source_key") or "").strip(),
                    "label": required,
                    "score": score_value,
                    "tone": (
                        "watch"
                        if required in PREMIUM_REQUIRED_WATCH_TITLES
                        or (isinstance(score_value, int) and score_value < 52)
                        else "neutral"
                    ),
                    "body": body,
                    "required_conclusion": required,
                    "source_label": source_label,
                    "value": value,
                    "year": item.get("year"),
                    "age": item.get("age"),
                    "age_label": item.get("age_label"),
                    "focus": focus,
                    "source_type": str(item.get("source_type") or "").strip(),
                    "coverage_status": str(item.get("status") or "").strip(),
                    "layer_coverage": list(item.get("layer_coverage") or []),
                }
            )
    decision_events = timing_decision.get("event_years") if isinstance(timing_decision.get("event_years"), dict) else {}
    for event_key, event in decision_events.items():
        if not isinstance(event, dict):
            continue
        event_label = str(event.get("event_label") or event.get("focus") or event_key).strip()
        focus = str(event.get("focus") or event_label).strip()
        score = event.get("score")
        score_value = int(score) if isinstance(score, (int, float)) else score
        kind = str(event.get("kind") or "")
        pool.append(
            {
                "source": "timing_decision_event",
                "source_type": "timing_event",
                "key": str(event_key or "").strip(),
                "label": event_label,
                "score": score_value,
                "tone": "watch" if kind == "caution" else "strong" if kind == "good" else "neutral",
                "body": " ".join(part for part in (event_label, focus) if part),
                "year": event.get("year"),
                "age": event.get("age"),
                "age_label": event.get("ageLabel") or event.get("age_label"),
                "focus": focus,
                "source_label": event_label,
            }
        )
    for source_name, items in (
        ("visual", profile.get("items") or []),
        ("topic", section.get("topic_items") or []),
        ("profile", section_profile.get("items") or []),
    ):
        for item in items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("title") or item.get("display_label") or item.get("value") or "").strip()
            if not label:
                continue
            pool.append(
                {
                    "source": source_name,
                    "label": label,
                    "score": item.get("score"),
                    "tone": str(item.get("tone") or ""),
                    "body": str(item.get("caption") or item.get("body") or item.get("text") or item.get("definition") or "").strip(),
                }
            )
    for detail in section.get("premium_details") or []:
        if not isinstance(detail, dict):
            continue
        label = str(detail.get("title") or "").strip()
        judgment = str(detail.get("judgment") or "").strip()
        if not label and not judgment:
            continue
        pool.append(
            {
                "source": "detail",
                "label": label,
                "score": detail.get("score"),
                "tone": str(detail.get("level") or ""),
                "body": judgment,
            }
        )
    return pool


def _premium_required_age_window(title: str) -> tuple[int, int] | None:
    if title in {"결혼 적기", "혼인 결정 연도", "주거·생활 준비 연도", "연애 강세 연도", "새 인연 연도", "관계 진전 연도"}:
        return (24, 45)
    if title in {"직업 상승 연도", "권한 상승 연도", "보상 상승 연도", "직업 전환 연도", "소속 변화 연도", "직업 독립 연도"}:
        return (23, 59)
    if title in {"수입 강세 연도", "재물 강세 연도", "자산화 연도", "채권·미수금 회수 연도"}:
        return (25, 65)
    return None


def _premium_required_best_timing_event(title: str, pool: list[dict[str, Any]]) -> dict[str, Any] | None:
    aliases = REPORT_TIMING_COVERAGE_SOURCE_ALIASES.get(title, ())
    if not aliases and "연도" not in title and title != "결혼 적기":
        return None
    alias_set = {str(alias) for alias in aliases}
    title_key = _compact_match_key(title)
    window = _premium_required_age_window(title)
    candidates: list[dict[str, Any]] = []
    for item in pool:
        if str(item.get("source_type") or "") != "timing_event":
            continue
        key = str(item.get("key") or "")
        label_key = _compact_match_key(f"{item.get('label') or ''} {item.get('body') or ''}")
        if alias_set and key not in alias_set and not any(_compact_match_key(alias) in label_key for alias in alias_set):
            continue
        if not alias_set and title_key and title_key not in label_key:
            continue
        candidates.append(item)
    if not candidates:
        return None

    def age_value(item: dict[str, Any]) -> int:
        age = item.get("age")
        if isinstance(age, (int, float)):
            return int(age)
        match = re.search(r"\d+", str(item.get("age_label") or ""))
        return int(match.group(0)) if match else 999

    def rank(item: dict[str, Any]) -> tuple[int, float, int]:
        age = age_value(item)
        in_window = 1 if window and window[0] <= age <= window[1] else 0
        if window is None:
            in_window = 1
        score = float(item.get("score") or 0)
        distance = 0
        if window and not in_window and age != 999:
            distance = min(abs(age - window[0]), abs(age - window[1]))
        return (in_window, score, -distance)

    selected = sorted(candidates, key=rank, reverse=True)[0]
    if window and age_value(selected) != 999 and not (window[0] <= age_value(selected) <= window[1]):
        return None
    return selected


def _premium_required_match_item(
    section: dict[str, Any],
    required: dict[str, Any],
    pool: list[dict[str, Any]],
) -> dict[str, Any] | None:
    domain = str(required.get("_judgment_domain") or _domain_key(section))
    title = str(required.get("title") or "").strip()
    timing_match = _premium_required_best_timing_event(title, pool)
    if timing_match:
        return timing_match
    age_window = _premium_required_age_window(title)
    preferred = PREMIUM_REQUIRED_JUDGMENT_MATCH_LABELS.get(domain, {}).get(title, ())
    preferred_keys = [_compact_match_key(label) for label in preferred if label]
    title_key = _compact_match_key(title)
    best: tuple[int, dict[str, Any] | None] = (0, None)
    for item in pool:
        label = str(item.get("label") or "")
        body = str(item.get("body") or "")
        item_tone = str(item.get("tone") or "")
        haystack = _compact_match_key(f"{label} {body}")
        score = 0
        if any(key and key in haystack for key in preferred_keys):
            score += 100
        if title_key and title_key in haystack:
            score += 45
        if str(item.get("required_conclusion") or "") == title:
            score += 140
        if str(item.get("source") or "") == "output_goal_coverage":
            score += 130
        if age_window and str(item.get("source_type") or "") == "timing_event":
            item_age = item.get("age")
            if isinstance(item_age, (int, float)):
                age_int = int(item_age)
            else:
                age_match = re.search(r"\d+", str(item.get("age_label") or ""))
                age_int = int(age_match.group(0)) if age_match else 0
            if age_int and not (age_window[0] <= age_int <= age_window[1]):
                continue
        if str(item.get("source") or "") == "domain_decision_facet":
            score += 70
        if title in PREMIUM_REQUIRED_WATCH_TITLES:
            if item_tone in {"watch", "risk", "caution"}:
                score += 90
            elif item_tone == "strong":
                score -= 35
        for word in str(required.get("premium_output") or "").replace("·", " ").replace(",", " ").split():
            if len(word) >= 2 and word in f"{label} {body}":
                score += 6
        item_score = item.get("score")
        if isinstance(item_score, int):
            score += min(20, max(0, item_score // 5))
        if score > best[0]:
            best = (score, item)
    return best[1]


def _premium_required_watch_match(pool: list[dict[str, Any]]) -> dict[str, Any] | None:
    watch_items = [
        item
        for item in pool
        if str(item.get("tone") or "") in {"watch", "risk", "caution"}
    ]
    if not watch_items:
        return None
    return sorted(
        watch_items,
        key=lambda item: (
            1 if str(item.get("label") or "") in PREMIUM_REQUIRED_PRESSURE_FACET_LABELS else 0,
            int(item.get("score") or 0) if isinstance(item.get("score"), int) else 0,
        ),
        reverse=True,
    )[0]


def _dedupe_repeated_phrase(text: str) -> str:
    compacted = " ".join(str(text or "").split())
    if not compacted:
        return ""
    tokens = compacted.split()
    if len(tokens) % 2 == 0:
        midpoint = len(tokens) // 2
        if tokens[:midpoint] == tokens[midpoint:]:
            return " ".join(tokens[:midpoint])
    return compacted


PREMIUM_REQUIRED_JUDGMENT_MEANINGS: dict[str, dict[str, str]] = {
    "money": {
        "재물 형성력": "수입이 지나가는 돈으로 끝나지 않고 자기 이름의 기반으로 남는 자리입니다.",
        "재물 규모 확장력": "돈의 단위가 커질 때 감당할 수 있는 거래 범위와 손실 범위가 함께 드러납니다.",
        "수입 창출력": "일의 결과가 실제 입금으로 돌아오고, 그 대가가 반복 수입으로 이어지는 자리입니다.",
        "재주 수익화": "기술, 말, 콘텐츠, 서비스가 취미나 재능에 머물지 않고 가격을 갖는 자리입니다.",
        "성과 보상력": "해낸 일이 타인의 이름으로 흩어지지 않고 자기 몫의 보상으로 돌아오는 자리입니다.",
        "자금 운용 안정성": "돈을 버는 순간보다 생활비, 투자금, 예비 자금의 선을 나눌 때 차이가 납니다.",
        "자산화 능력": "들어온 돈이 소비로 사라지지 않고 명의, 지분, 보유 자산으로 남는 자리입니다.",
        "투자·거래 판단력": "겉수익보다 회수 시점, 권리 구조, 상대의 책임 범위를 먼저 읽어야 하는 자리입니다.",
        "계약·명의 안정성": "받을 돈과 권리가 말이 아니라 계약서, 명의, 지분으로 고정되는 자리입니다.",
        "채권·미수금 회수력": "늦어진 돈과 받아야 할 보상이 흐지부지되지 않고 실제 회수로 이어지는 자리입니다.",
        "공동자금 운영력": "가까운 사람과 돈을 섞을 때 자기 몫과 책임 범위를 지킬 수 있는지가 드러납니다.",
        "부채·보증 관리력": "대여, 보증, 채무 인수에서 남의 책임이 자기 책임으로 넘어오는지를 가르는 자리입니다.",
        "가족재산 경계력": "가족 돈과 자기 재산이 섞일 때 권리와 부담의 선이 얼마나 분명한지가 드러납니다.",
        "사업 확장성": "고정 수입 바깥에서 거래처, 단가, 매출 단위가 커질 수 있는 자리입니다.",
        "재정 방어력": "손실이 생겨도 핵심 자산과 현금 기반을 지킬 수 있는지가 드러납니다.",
        "후반 축재력": "나이가 들수록 현금보다 보유 자산의 크기와 안정성이 중요해지는 자리입니다.",
        "금전 기준성": "정, 체면, 분위기보다 자기 몫과 권리를 먼저 세울 수 있는지가 드러납니다.",
        "재물 강세 연도": "수입, 자산, 계약 결과가 한 해의 사건으로 뚜렷하게 드러납니다.",
        "재물 주의 연도": "명의, 보증, 공동자금에서 자기 몫을 잃기 쉬운 해입니다.",
    },
    "career": {
        "직업 적성": "어떤 자리에서 실력이 가장 빨리 인정받고 경력이 값어치를 갖는지가 드러납니다.",
        "직업 분야": "직업명보다 실제 업무의 성격과 책임 구조가 맞는지가 중요해지는 자리입니다.",
        "성취 축적력": "한 번의 성과가 지나가는 칭찬으로 끝나지 않고 이력과 실적으로 남는 자리입니다.",
        "평가·명예 전환력": "실적이 평판, 추천, 직함으로 바뀌어 사회적 이름을 만드는 자리입니다.",
        "승진·직함 가능성": "책임자 역할과 공식 직함으로 올라설 가능성이 드러나는 자리입니다.",
        "사회적 도약성": "개인 성과가 더 큰 지위와 영향력으로 확대되는 자리입니다.",
        "권한 확보력": "맡은 일에 걸맞은 결정권을 가져와야 성과가 보호되는 자리입니다.",
        "책임·권한 균형": "책임과 결정권이 함께 주어질 때 직업운이 안정되는 자리입니다.",
        "보상 협상력": "성과를 연봉, 수수료, 성과급, 계약 조건으로 바꾸는 자리입니다.",
        "전문 자산화": "경험과 지식이 대체하기 어려운 전문성으로 굳어지는 자리입니다.",
        "조직 적응력": "조직 안에서 자기 역할과 위치를 안정적으로 확보할 수 있는지가 드러납니다.",
        "소속 전환력": "회사, 부서, 직무가 바뀌어도 새 역할을 다시 잡을 수 있는 자리입니다.",
        "독립 가능성": "자기 이름, 고객 기반, 별도 수입원으로 일할 가능성이 드러나는 자리입니다.",
        "업무 조건 감별력": "성과가 남는 자리와 소모만 큰 자리를 구분해야 하는 자리입니다.",
        "직업 전환 연도": "이직, 승진, 역할 변경이 한 해의 사건으로 크게 올라옵니다.",
    },
    "love": {
        "끌림의 기준": "처음 마음이 움직이는 지점과 오래 끌리는 상대의 성격이 구분됩니다.",
        "상대 선택력": "오래 갈 사람과 피해야 할 사람을 가려내는 눈이 드러납니다.",
        "상대 신뢰 감별력": "말보다 태도와 책임감을 보고 상대를 판단하는 자리입니다.",
        "인연 형성력": "새로운 만남이 스쳐 지나가지 않고 실제 인연으로 이어지는 자리입니다.",
        "관계 진전력": "호감이 만남, 약속, 공개된 관계로 넘어가는 힘이 드러납니다.",
        "관계 주도권": "관계의 속도와 거리를 스스로 정할 수 있는지가 중요해지는 자리입니다.",
        "관계 속도 조절력": "감정의 속도와 만남의 속도가 맞아야 오래 가는 자리입니다.",
        "애정 표현성": "좋아하는 마음을 상대가 확신할 만큼 보여줄 수 있는지가 드러납니다.",
        "정서 수용력": "상대의 불안과 서운함을 관계 안에서 감당할 수 있는지가 드러납니다.",
        "관계 지속력": "깊어진 관계를 쉽게 끊지 않고 오래 이어가는 성향이 강하게 드러납니다.",
        "연락·거리 안정성": "연락, 사생활, 만남의 간격이 안정될 때 관계가 오래 갑니다.",
        "오해 조정력": "말하지 않고 넘긴 감정을 늦기 전에 다시 맞출 수 있는지가 중요합니다.",
        "갈등 관리력": "자존심과 생활 기준이 부딪힐 때 관계를 깨뜨리지 않을 수 있는지가 드러납니다.",
        "주변 개입 관리력": "가족, 친구, 과거 인연의 말이 관계 안으로 들어올 때 선을 세워야 하는 자리입니다.",
        "재회 가능성": "끝난 인연이 다시 연락과 만남으로 이어질 여지가 드러납니다.",
        "결혼 연결력": "연애가 주거, 생활비, 가족 협의까지 이어질 현실성이 드러납니다.",
    },
    "marriage": {
        "혼인 성향": "결혼을 사랑의 결론에 그치지 않고 생활의 책임으로 받아들이는 자리입니다.",
        "배우자상": "오래 맞는 배우자의 성격, 생활 태도, 책임 감각이 드러납니다.",
        "결혼 적기": "혼인 논의가 약속과 절차로 굳어지기 쉬운 해입니다.",
        "결혼 현실화력": "결혼 의사가 집, 일정, 가족 협의로 이어질 수 있는지가 드러납니다.",
        "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활의 안정성을 결정하는 자리입니다.",
        "주거·생활 설계력": "집과 생활 구조를 현실적으로 짤 수 있는지가 드러납니다.",
        "가정 운영력": "가정 안의 일정, 비용, 책임을 정리해야 안정되는 자리입니다.",
        "부부 재정": "공동 생활비와 개인 자산의 선이 결혼 안정에 직접 연결됩니다.",
        "생활비 기준성": "고정비와 저축선이 부부 사이에서 분명해야 하는 자리입니다.",
        "부부 갈등 조정력": "역할 불균형과 돈 문제가 생길 때 다시 맞출 수 있는지가 드러납니다.",
        "부부 갈등 회복성": "상한 감정 뒤에도 생활 기준을 다시 세울 수 있는지가 중요합니다.",
        "가족 책임 경계력": "양가와 원가족 문제에서 책임선을 분명히 해야 하는 자리입니다.",
        "배우자 가족 경계": "배우자 가족 문제가 부부 생활 안으로 과하게 들어오지 않게 해야 합니다.",
        "자녀·양육 책임": "자녀, 돌봄, 교육비가 결혼 생활의 실제 과제로 들어오는 자리입니다.",
        "배우자 복": "배우자로 인한 안정과 함께 감당해야 할 책임의 크기도 같이 드러납니다.",
        "혼인 위기 대응력": "돈, 가족, 주거 문제가 겹칠 때 결혼을 다시 세울 수 있는지가 드러납니다.",
        "결혼 지속력": "한 번 정한 결혼의 약속을 오래 유지하려는 성향이 드러납니다.",
    },
    "timing": {
        "대운 구간": "10년 단위로 바뀌는 생활 조건과 사회적 자리를 구분하는 구간입니다.",
        "세운 사건": "대운의 배경 위에서 특정 연도에 실제 선택과 사건이 올라옵니다.",
        "상승 연도": "성과, 인연, 재물 중 한 가지가 선명한 결과로 남는 해입니다.",
        "수입 강세 연도": "현금 수입과 보상 기준이 한 해의 사건으로 강하게 드러납니다.",
        "재물 강세 연도": "수입과 자산 문제가 함께 커지고, 돈의 귀속이 분명해지는 해입니다.",
        "자산화 연도": "명의, 지분, 보유 자산을 잡기 쉬운 해입니다.",
        "채권·미수금 회수 연도": "받아야 할 돈과 지연된 보상을 정리하기 좋은 해입니다.",
        "공동자금 주의 연도": "공동 비용, 지분, 동업 자금에서 자기 몫이 흔들리기 쉬운 해입니다.",
        "계약·명의 주의 연도": "문서, 명의, 보증에서 손익이 크게 갈리는 해입니다.",
        "부채·보증 주의 연도": "빌려준 돈, 보증, 채무 책임이 자기 쪽으로 넘어오기 쉬운 해입니다.",
        "가족재산 주의 연도": "가족 자산과 자기 재산의 경계가 흔들리기 쉬운 해입니다.",
        "재물 주의 연도": "금전 판단에서 손실 가능성이 커지는 해입니다.",
        "직업 상승 연도": "평가, 직책, 제안이 강하게 올라오는 해입니다.",
        "권한 상승 연도": "맡는 범위와 결정권이 함께 커지는 해입니다.",
        "보상 상승 연도": "성과가 보수와 계약 조건으로 계산되는 해입니다.",
        "직업 분야 전환 연도": "산업, 직무, 전문 방향이 바뀌는 해입니다.",
        "직업 전환 연도": "이직, 승진, 독립 준비가 강하게 올라오는 해입니다.",
        "소속 변화 연도": "회사, 팀, 부서, 고용 형태가 바뀌기 쉬운 해입니다.",
        "직업 부담 연도": "책임 전가와 평가 손상이 커질 수 있는 해입니다.",
        "직업 독립 연도": "자기 이름의 일과 별도 수입원을 세우기 좋은 해입니다.",
        "연애 강세 연도": "호감이 실제 만남으로 옮겨가기 쉬운 해입니다.",
        "새 인연 연도": "새로운 만남과 소개가 강하게 들어오는 해입니다.",
        "관계 진전 연도": "만남이 약속과 공개된 관계로 넘어가는 해입니다.",
        "재회·정리 연도": "과거 인연이 다시 올라오거나 감정의 결론이 나는 해입니다.",
        "이별·정리 연도": "끌고 온 관계를 끝내거나 정리하기 쉬운 해입니다.",
        "관계 주의 연도": "오해, 단절, 자존심 충돌이 커지는 해입니다.",
        "주변 개입 주의 연도": "가족, 친구, 과거 인연의 말이 관계에 끼어드는 해입니다.",
        "혼인 결정 연도": "결혼 논의와 공식 약속이 현실로 굳어지는 해입니다.",
        "주거·생활 준비 연도": "집, 생활비, 역할 분담을 실제로 맞추는 해입니다.",
        "부부 재정 연도": "생활비와 공동 자산의 기준이 결혼 생활의 중심으로 올라오는 해입니다.",
        "가족·주거 변동 연도": "이사, 독립, 가족 책임이 현실 문제로 올라오는 해입니다.",
        "자녀·양육 책임 연도": "자녀, 돌봄, 교육비 책임이 커지는 해입니다.",
        "결혼 주의 연도": "주거, 생활비, 배우자 가족 문제가 부담으로 올라오는 해입니다.",
        "인생 전환 연도": "직업, 거주, 관계 방향을 크게 바꾸는 해입니다.",
        "주의 연도": "손실과 갈등이 커질 수 있어 큰 결정을 서두르지 말아야 하는 해입니다.",
        "회복 연도": "이전의 손실과 정체를 정리하고 다시 기반을 잡는 해입니다.",
        "말년 안정 연도": "후반부 생활 기반이 안정되는 해입니다.",
    },
}


PREMIUM_REQUIRED_JUDGMENT_SCENES: dict[str, dict[str, tuple[str, str]]] = {
    "money": {
        "재물 형성력": ("고정 수입과 반복 거래가 쌓일수록 재산의 바닥이 단단해집니다.", "수입이 생겨도 권리와 명의가 남지 않으면 재산으로 굳지 않습니다."),
        "재물 규모 확장력": ("거래 단위가 커지면서 보유 자산의 폭도 넓어집니다.", "큰 거래를 서두르면 이익보다 책임이 먼저 따라옵니다."),
        "수입 창출력": ("성과가 보수로 환산되고, 일의 대가가 비교적 분명하게 들어옵니다.", "일은 많아도 보상 기준이 흐리면 받을 몫이 줄어듭니다."),
        "재주 수익화": ("기술과 결과물이 상품으로 잡힐수록 단가가 올라갑니다.", "재능만 있고 가격표가 없으면 보상이 늦습니다."),
        "성과 보상력": ("한 일의 범위가 분명할수록 자기 몫을 요구할 명분이 생깁니다.", "성과를 냈는데도 공로가 흩어지면 보상이 약해집니다."),
        "자금 운용 안정성": ("생활비, 투자금, 예비 자금이 분리될수록 재정이 안정됩니다.", "생활비와 투자금이 섞이면 작은 손실도 크게 느껴집니다."),
        "자산화 능력": ("돈은 현금보다 소유권이 남는 형태에서 힘을 얻습니다.", "수입이 소비와 임시 비용으로 빠지면 자산의 흔적이 약해집니다."),
        "투자·거래 판단력": ("상대의 설명보다 회수 조건과 권리 구조를 먼저 확인해야 합니다.", "수익률만 보고 들어간 거래는 묶인 돈으로 남기 쉽습니다."),
        "계약·명의 안정성": ("지급일, 지분, 수령액이 문서에 남을수록 금전 권리가 안정됩니다.", "구두 약속과 흐린 명의는 받을 몫을 줄입니다."),
        "채권·미수금 회수력": ("증빙과 지급일이 남아 있으면 늦어진 돈도 회수할 수 있습니다.", "말로 넘긴 돈은 시간이 지날수록 회수가 어려워집니다."),
        "공동자금 운영력": ("처음부터 지분과 명의를 나누면 관계와 돈을 함께 지킬 수 있습니다.", "호의로 시작한 돈이 나중에는 몫과 책임 문제로 바뀝니다."),
        "부채·보증 관리력": ("책임 범위를 끊어내야 빌려준 돈과 보증이 손실로 번지지 않습니다.", "상대 사정에 끌려가면 이름만 빌려주고 책임은 본인에게 남습니다."),
        "가족재산 경계력": ("가족 자산에서도 자기 몫과 책임선을 분명히 해야 합니다.", "대신 떠안은 지출이 장기 손실로 남을 수 있습니다."),
        "사업 확장성": ("고객, 단가, 회수 구조가 갖춰지면 사업 단위가 커집니다.", "매출보다 책임이 먼저 커지는 확장은 피해야 합니다."),
        "재정 방어력": ("손실이 생겨도 핵심 자산을 지키는 구조가 중요합니다.", "예비 자금이 약하면 작은 변수도 큰 압박으로 커집니다."),
        "후반 축재력": ("후반으로 갈수록 현금보다 보유 자산의 질이 중요해집니다.", "늦은 확장은 수익보다 관리 부담을 먼저 만들 수 있습니다."),
        "금전 기준성": ("친한 사이라도 금액, 지급일, 명의를 분명히 남겨야 합니다.", "좋게 넘긴 돈은 나중에 가장 불편한 말이 됩니다."),
        "재물 강세 연도": ("해당 연도에는 돈이 들어오는 일보다 권리가 남는 일을 우선해야 합니다.", "강세 연도라도 명의가 흐리면 이익이 온전히 남지 않습니다."),
        "재물 주의 연도": ("큰 결정보다 계약서, 명의, 보증을 먼저 확인해야 합니다.", "가까운 사람의 부탁이 금전 손실로 이어질 수 있습니다."),
    },
    "career": {
        "직업 적성": ("업무의 기준과 결과물을 맡는 직무에서 강점이 분명합니다.", "단순 보조와 반복 처리만 많은 자리는 오래 맞지 않습니다."),
        "직업 분야": ("운영, 관리, 기획, 분석처럼 결과와 책임이 남는 분야에서 성과가 납니다.", "흥미만으로 고른 일은 경력의 이름이 약해집니다."),
        "성취 축적력": ("기록과 실적이 쌓일수록 경력의 단가가 올라갑니다.", "성과가 자기 이름으로 남지 않으면 경력의 값이 늦게 오릅니다."),
        "평가·명예 전환력": ("공식 평가와 추천이 따라올 때 직업운이 강해집니다.", "평가 기준이 흐린 자리는 공로가 다른 사람에게 넘어갑니다."),
        "승진·직함 가능성": ("성과가 직함과 책임자로 이어질 가능성이 있습니다.", "직함 없이 책임만 커지면 경력 부담이 먼저 남습니다."),
        "사회적 도약성": ("개인 성과가 더 큰 자리와 영향력으로 넓어질 수 있습니다.", "사회적 자리는 성과보다 기록과 신뢰가 먼저 요구됩니다."),
        "권한 확보력": ("결정권이 붙을수록 직업적 손실이 줄고 성취가 남습니다.", "권한 없는 책임은 경력의 흠으로 남기 쉽습니다."),
        "책임·권한 균형": ("책임과 권한이 함께 붙는 자리에서 오래 갑니다.", "문제가 생겼을 때 이름만 남는 자리는 피해야 합니다."),
        "보상 협상력": ("성과가 연봉, 성과급, 계약금으로 계산될 때 유리합니다.", "보상 기준을 늦게 맞추면 해낸 일보다 몫이 작아집니다."),
        "전문 자산화": ("한 분야의 전문성이 쌓이면 대체하기 어려운 역할이 됩니다.", "전문 분야가 흐리면 경험이 많아도 값이 늦게 오릅니다."),
        "조직 적응력": ("역할이 분명한 조직에서는 위치를 안정적으로 잡습니다.", "보고 체계가 흐린 조직에서는 책임만 늘 수 있습니다."),
        "소속 전환력": ("소속이 바뀌어도 맡을 역할을 빠르게 다시 잡습니다.", "새 자리의 권한과 평가 기준이 불분명하면 오래가기 어렵습니다."),
        "독립 가능성": ("고객층과 단가가 잡히면 자기 이름으로 일할 수 있습니다.", "상품과 거래처 없이 독립하면 수입이 흔들립니다."),
        "업무 조건 감별력": ("성과가 남는 자리와 소모만 큰 자리를 가려야 합니다.", "기준이 자주 바뀌는 자리는 노력에 비해 경력이 남지 않습니다."),
        "직업 전환 연도": ("해당 연도에는 역할, 소속, 보상 기준이 함께 움직입니다.", "전환을 서두르면 새 자리에서도 같은 문제가 반복됩니다."),
    },
    "love": {
        "끌림의 기준": ("말보다 생활 태도와 책임감에서 관계가 깊어집니다.", "첫 호감만으로는 오래 갈 관계가 되기 어렵습니다."),
        "상대 선택력": ("오래 맞을 사람을 고르는 기준이 비교적 분명합니다.", "외적인 끌림에 밀리면 상대의 책임감을 늦게 확인합니다."),
        "상대 신뢰 감별력": ("반복된 태도와 약속을 보고 마음을 줍니다.", "말이 좋은 사람에게 빠르게 마음을 주면 실망이 커집니다."),
        "인연 형성력": ("생활권과 반복 접점에서 인연이 들어오기 쉽습니다.", "넓은 만남이 많아도 깊어지는 관계는 따로 가려집니다."),
        "관계 진전력": ("호감이 생기면 실제 만남과 약속으로 넘어갑니다.", "확정을 미루면 상대가 먼저 지칠 수 있습니다."),
        "관계 주도권": ("관계의 거리와 속도를 본인이 정할 때 안정됩니다.", "상대의 요구에 끌려가면 피로가 빨리 쌓입니다."),
        "관계 속도 조절력": ("천천히 깊어지는 관계에서 오래 갑니다.", "마음보다 약속이 앞서면 부담이 커집니다."),
        "애정 표현성": ("마음을 상대가 알아들을 수 있게 보여주는 일이 중요합니다.", "마음이 있어도 표현이 늦으면 상대는 확신을 받지 못합니다."),
        "정서 수용력": ("상대의 불안과 서운함을 일정 부분 받아낼 수 있습니다.", "감정 요구가 많아지면 쉽게 지칠 수 있습니다."),
        "관계 지속력": ("한 번 깊어진 관계는 쉽게 끊지 않습니다.", "서운함을 오래 넘기면 한 번에 거리가 생깁니다."),
        "연락·거리 안정성": ("연락과 개인 시간을 함께 존중할 때 관계가 안정됩니다.", "연락 기준이 어긋나면 감정 소모가 커집니다."),
        "오해 조정력": ("작은 확인 지연에서 생긴 오해를 다시 맞출 수 있습니다.", "말하지 않고 넘긴 감정은 뒤늦게 크게 올라옵니다."),
        "갈등 관리력": ("생활 기준이 맞으면 갈등이 오래가지 않습니다.", "자존심이 부딪히면 관계가 빠르게 차가워질 수 있습니다."),
        "주변 개입 관리력": ("두 사람의 기준이 서면 주변 말에 쉽게 흔들리지 않습니다.", "제삼자의 말이 들어오면 관계의 판단이 흐려질 수 있습니다."),
        "재회 가능성": ("정리된 인연도 상황이 맞으면 다시 연락이 닿을 수 있습니다.", "같은 문제가 반복되면 재회가 안정으로 이어지지 않습니다."),
        "결혼 연결력": ("연애가 깊어지면 주거와 생활비 이야기로 넘어갑니다.", "마음은 있어도 현실 준비가 늦으면 결혼 결정이 밀립니다."),
    },
    "marriage": {
        "혼인 성향": ("결혼을 안정과 책임의 약속으로 받아들이는 편입니다.", "감정만 앞세운 결혼은 뒤늦은 부담을 남깁니다."),
        "배우자상": ("성실하고 생활 기준이 분명한 상대와 오래 맞습니다.", "감정 기복이 큰 상대와는 결혼 뒤 생활 손상이 먼저 옵니다."),
        "결혼 적기": ("약속이 실제 절차로 넘어가는 해에 결혼이 굳어집니다.", "주거와 가족 협의가 늦으면 결혼 시점도 늦어집니다."),
        "결혼 현실화력": ("마음이 집, 일정, 가족 협의로 옮겨갈 때 결혼이 성사됩니다.", "현실 준비 없이 밀어붙이면 결정이 부담으로 바뀝니다."),
        "생활 안정": ("주거와 생활비 기준이 잡히면 결혼 생활이 오래 갑니다.", "생활 기준이 어긋나면 애정이 있어도 피로가 커집니다."),
        "주거·생활 설계력": ("집과 생활 구조를 현실적으로 짤수록 안정됩니다.", "역할 분담이 늦으면 같은 갈등이 반복됩니다."),
        "가정 운영력": ("가정 안의 비용과 책임을 정리하는 힘이 있습니다.", "가정의 책임이 한쪽으로 몰리면 빠르게 지칩니다."),
        "부부 재정": ("공동 생활비와 개인 자산의 선을 나눌수록 안정됩니다.", "부부 돈이 흐리게 섞이면 한쪽 책임이 과해집니다."),
        "생활비 기준성": ("고정비와 저축선이 잡혀야 결혼 생활이 안정됩니다.", "생활비 기준이 흐리면 서운함이 돈 문제로 굳어집니다."),
        "부부 갈등 조정력": ("갈등은 역할을 다시 나눌 때 풀립니다.", "말로만 넘긴 갈등은 생활비와 가족 문제로 반복됩니다."),
        "부부 갈등 회복성": ("상한 감정 뒤에도 책임 기준을 다시 세우면 회복됩니다.", "사과만 있고 역할 변화가 없으면 같은 문제가 되풀이됩니다."),
        "가족 책임 경계력": ("양가와 원가족 문제에서 부부의 기준을 먼저 세워야 합니다.", "가족 문제를 정으로 떠안으면 결혼 생활이 흔들립니다."),
        "배우자 가족 경계": ("배우자 가족 문제도 책임 범위를 분명히 해야 안정됩니다.", "돌봄과 돈의 범위를 늦게 정하면 부담이 커집니다."),
        "자녀·양육 책임": ("자녀와 양육 문제는 결혼 생활의 큰 축으로 들어옵니다.", "비용과 돌봄 시간이 한쪽으로 몰리면 갈등이 커집니다."),
        "배우자 복": ("배우자에게서 생활의 안정감을 얻을 수 있습니다.", "상대에게 기대는 부분이 커지면 부담도 함께 커집니다."),
        "혼인 위기 대응력": ("돈, 가족, 주거 문제가 겹쳐도 다시 기준을 세울 수 있습니다.", "생활 기준이 정리되지 않으면 위기가 오래 갑니다."),
        "결혼 지속력": ("한 번 정한 약속을 오래 지키는 쪽입니다.", "약속을 미루는 시간이 길어지면 상대의 불안이 커집니다."),
    },
    "timing": {
        "대운 구간": ("10년 단위로 생활 조건이 바뀝니다.", "대운은 한 해의 사건보다 더 오래 지속되는 생활 조건입니다."),
        "세운 사건": ("특정 연도에 실제 사건의 성격이 올라옵니다.", "세운은 대운의 배경 위에서 선택, 계약, 관계, 이동으로 나타납니다."),
        "상승 연도": ("일, 돈, 관계 중 한 영역에서 결론이 선명한 해입니다.", "좋은 해라도 무엇이 남는 해인지가 분명해야 합니다."),
        "주의 연도": ("손실과 부담이 커지기 쉬운 해입니다.", "새 결정보다 기존 약속과 책임 범위를 먼저 정리해야 합니다."),
    },
}


PREMIUM_REQUIRED_JUDGMENT_MEANINGS["money"].update(
    {
        "재물 형성력": "수입이 현금으로 지나가지 않고 명의, 지분, 장기 보유 자산으로 남는 힘입니다.",
        "재물 규모 확장력": "돈의 단위가 커질 때 감당 가능한 거래 규모와 손실 한도가 함께 드러납니다.",
        "수입 창출력": "노동, 거래, 성과가 실제 입금으로 확인되는 수입 경로입니다.",
        "재주 수익화": "기술, 말, 콘텐츠, 서비스가 단순 재능에 머물지 않고 가격을 갖는 지점입니다.",
        "성과 보상력": "해낸 일이 타인의 이름으로 흩어지지 않고 자기 몫의 보수로 회수되는 힘입니다.",
        "자산화 능력": "벌어들인 돈을 소비가 아니라 소유권과 보유 자산으로 바꾸는 능력입니다.",
        "공동자금 운영력": "가까운 사람과 돈이 얽힐 때 자기 몫, 명의, 책임 범위를 지키는 힘입니다.",
        "계약·명의 안정성": "받을 돈과 권리를 계약서, 명의, 지분으로 고정시키는 능력입니다.",
        "투자·거래 판단력": "겉수익보다 회수 가능성, 상대의 책임, 권리 구조를 먼저 읽는 감각입니다.",
    }
)

PREMIUM_REQUIRED_JUDGMENT_MEANINGS["career"].update(
    {
        "직업 적성": "실력이 가장 빨리 인정받고 경력의 값이 올라가는 업무 성격입니다.",
        "직업 분야": "직업명보다 실제 업무 방식, 책임 구조, 결과물의 성격을 가르는 기준입니다.",
        "성취 축적력": "한 번의 성과가 칭찬으로 끝나지 않고 이력, 실적, 다음 자리의 근거로 남는 힘입니다.",
        "평가·명예 전환력": "실적이 평판, 추천, 직함, 공식 평가로 바뀌어 사회적 이름을 만드는 힘입니다.",
        "책임·권한 균형": "맡은 책임에 걸맞은 결정권이 붙을 때 경력 손상을 막고 성취를 남기는 기준입니다.",
        "권한 확보력": "일을 맡는 수준에 맞춰 결정권, 보고 체계, 보상 기준을 확보하는 힘입니다.",
    }
)

PREMIUM_REQUIRED_JUDGMENT_MEANINGS["love"].update(
    {
        "끌림의 기준": "처음 마음이 움직이는 지점과 오래 끌리는 상대의 조건을 구분하는 기준입니다.",
        "상대 선택력": "오래 갈 사람과 손상될 관계를 초기에 가려내는 눈입니다.",
        "상대 신뢰 감별력": "상대의 말보다 반복된 태도, 약속, 책임감을 읽는 감각입니다.",
        "인연 형성력": "스쳐 가는 호감이 실제 만남과 관계로 이어지는 힘입니다.",
        "관계 진전력": "호감이 만남, 약속, 공개된 관계로 넘어가는 속도와 확정성입니다.",
        "애정 표현성": "마음이 상대에게 오해 없이 전달되는 정도입니다.",
        "관계 지속력": "깊어진 관계를 쉽게 끊지 않고 오래 유지하려는 힘입니다.",
    }
)

PREMIUM_REQUIRED_JUDGMENT_MEANINGS["marriage"].update(
    {
        "혼인 성향": "결혼을 감정의 결론이 아니라 생활의 약속과 책임으로 받아들이는 방식입니다.",
        "배우자상": "오래 맞는 배우자의 성격, 생활 태도, 책임 감각을 보여주는 기준입니다.",
        "결혼 현실화력": "결혼 의사가 집, 일정, 가족 협의, 공식 절차로 넘어가는 힘입니다.",
        "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활을 오래 버티게 하는 기반입니다.",
        "부부 재정": "공동 생활비와 개인 자산의 선이 부부 사이의 안정에 미치는 힘입니다.",
        "가족 책임 경계력": "양가와 원가족 문제에서 부부의 책임선을 지켜내는 힘입니다.",
    }
)

PREMIUM_REQUIRED_JUDGMENT_SCENES["money"].update(
    {
        "재물 형성력": ("고정 수입과 반복 거래가 쌓이면 자기 이름의 재산 기반이 만들어집니다.", "수입이 생겨도 권리와 명의가 남지 않으면 재산으로 굳지 않습니다."),
        "성과 보상력": ("한 일의 범위가 분명할수록 자기 몫을 요구할 근거가 생깁니다.", "성과를 내고도 기준을 늦게 잡으면 보상은 작아집니다."),
        "계약·명의 안정성": ("지급일, 지분, 수령액이 문서에 남을수록 금전 권리가 보호됩니다.", "구두 약속과 흐린 명의는 받을 몫을 줄입니다."),
        "공동자금 운영력": ("지분과 명의를 나누면 관계와 돈을 함께 지킬 수 있습니다.", "호의로 시작한 돈이 나중에는 몫, 명의, 책임 문제로 바뀝니다."),
    }
)

PREMIUM_REQUIRED_JUDGMENT_SCENES["career"].update(
    {
        "성취 축적력": ("기록과 실적이 쌓일수록 경력의 단가가 올라갑니다.", "성과가 자기 이름으로 남지 않으면 경력의 값은 늦게 오릅니다."),
        "평가·명예 전환력": ("공식 평가와 추천이 붙을 때 직업운이 강해집니다.", "평가 기준이 흐린 자리는 공로가 다른 사람에게 넘어갑니다."),
        "책임·권한 균형": ("책임과 권한이 함께 붙는 자리에서 오래 갑니다.", "문제가 생겼을 때 이름만 남는 자리는 피해야 합니다."),
    }
)


PREMIUM_REQUIRED_PRODUCT_BODY_OVERRIDES: dict[str, dict[str, tuple[str, str, str]]] = {
    "money": {
        "재물 형성력": (
            "재물은 현금보다 권리로 굳어지는 쪽에서 커집니다. 고정 수입과 반복 거래가 쌓일수록 명의, 지분, 장기 보유 자산으로 옮겨갑니다. 후반으로 갈수록 재산의 윤곽이 선명해집니다.",
            "재물은 들어오는 순간보다 남는 형식이 더 중요합니다. 수입이 반복될 때 명의와 보유 자산을 남겨야 재산이 됩니다. 초반의 현금보다 후반의 소유 구조가 큽니다.",
            "수입은 생겨도 재산으로 굳는 속도가 늦습니다. 돈이 들어온 뒤 명의, 지분, 보유 자산으로 바꾸지 않으면 현금만 지나갑니다. 확장보다 소유권 확보가 먼저입니다.",
        ),
        "재물 규모 확장력": (
            "다루는 돈의 단위가 커질 사주입니다. 작은 수입을 반복하는 데서 끝나지 않고 거래 규모와 보유 자산의 폭이 넓어집니다. 큰돈은 준비된 구조 위에서 붙습니다.",
            "재물 규모는 단계적으로 넓어집니다. 고정 수입이 먼저 자리를 잡고, 이후 거래 단위와 자산 규모가 따라옵니다. 단번에 키우는 방식보다 순차적 확장이 맞습니다.",
            "돈의 단위를 키우는 과정에서 부담이 함께 커집니다. 큰 거래를 먼저 잡으면 회수와 책임이 무거워질 수 있습니다. 규모보다 감당 가능한 한도가 먼저입니다.",
        ),
        "수입 창출력": (
            "수입이 만들어지는 힘은 분명합니다. 일의 결과가 매출, 보수, 계약금처럼 계산 가능한 돈으로 돌아옵니다. 받을 금액이 정해진 자리에서 강합니다.",
            "수입 기회는 꾸준히 들어옵니다. 다만 수입이 크게 남으려면 역할과 보수 조건이 먼저 맞아야 합니다. 일한 만큼 받을 구조를 잡아야 합니다.",
            "수입 기회는 있어도 받을 몫이 줄어들 수 있습니다. 일은 많아지는데 보수 기준이 흐리면 남는 돈이 작습니다. 먼저 금액과 지급 조건을 확정해야 합니다.",
        ),
        "재주 수익화": (
            "재능이 가격을 갖기 쉬운 사주입니다. 기술, 말, 콘텐츠, 서비스가 반복 상품이 되면 수입이 붙습니다. 이름이 알려질수록 단가도 올라갑니다.",
            "재주는 있으나 수익 구조가 늦게 잡힙니다. 결과물이 분명해지고 반복 판매가 가능해질 때 돈이 붙습니다. 취미와 상품의 경계를 빨리 나눠야 합니다.",
            "재능에 비해 돈으로 바뀌는 속도가 느립니다. 잘하는 것만으로는 부족하고 가격, 고객, 판매 방식이 필요합니다. 결과물을 시장에 내놓는 과정이 핵심입니다.",
        ),
        "성과 보상력": (
            "성과가 자기 몫의 보상으로 돌아오는 힘이 좋습니다. 연봉, 성과급, 수수료, 계약금처럼 계산 가능한 보수에서 강합니다. 이름이 남는 성과일수록 돈도 커집니다.",
            "성과는 있으나 보상 구조를 확인해야 합니다. 해낸 일이 누구의 공으로 남는지에 따라 받을 몫이 달라집니다. 역할 범위를 문서와 평가에 남겨야 합니다.",
            "성과에 비해 보상이 작아질 수 있습니다. 일은 본인이 해도 공과 몫을 나누는 사람이 많아질 수 있습니다. 시작 전에 보상 기준을 잡아야 합니다.",
        ),
        "자금 운용 안정성": (
            "돈을 다루는 감각은 안정적입니다. 생활비, 투자금, 예비 자금을 구분할수록 재정이 단단해집니다. 큰돈보다 자금 배치에서 실력이 납니다.",
            "금전 운용은 기준을 세울수록 좋아집니다. 들어온 돈을 목적별로 나누면 재정 흔들림이 줄어듭니다. 즉흥 지출보다 분리 운용이 맞습니다.",
            "돈이 한 계좌 안에서 섞이면 빠르게 흐트러집니다. 생활비와 투자금이 섞이면 손실 판단이 늦어집니다. 자금의 용도를 먼저 나눠야 합니다.",
        ),
        "자산화 능력": (
            "번 돈을 자산으로 바꾸는 힘이 좋습니다. 현금보다 명의, 지분, 장기 보유 자산으로 남길 때 재물운이 커집니다. 후반 재산은 이 힘에서 만들어집니다.",
            "수입을 자산으로 굳히는 과정이 필요합니다. 돈이 들어오면 먼저 소유권이 남는 형태로 옮겨야 합니다. 소비보다 권리 확보가 우선입니다.",
            "수입이 자산으로 굳기 전에 빠져나가기 쉽습니다. 현금이 생겨도 명의와 소유권을 남기지 않으면 재산으로 보이지 않습니다. 저축보다 자산화 전략이 필요합니다.",
        ),
        "투자·거래 판단력": (
            "거래 판단은 수익률보다 회수 구조에서 강합니다. 상대의 책임, 계약 기간, 권리 구조를 읽을 때 손실을 줄입니다. 단기 이익보다 안전한 귀속이 맞습니다.",
            "투자와 거래는 조건을 따질수록 좋아집니다. 수익 설명보다 회수 시점과 권리 관계를 먼저 확인해야 합니다. 구조가 분명한 거래에서 유리합니다.",
            "급한 투자 제안은 손실로 번지기 쉽습니다. 높은 수익률보다 명의, 담보, 회수 조건을 먼저 확인해야 합니다. 말이 앞서는 거래는 피하는 편이 낫습니다.",
        ),
        "계약·명의 안정성": (
            "금전 권리는 문서와 명의로 지킬 수 있습니다. 지급일, 지분, 수령액이 남을수록 받을 몫이 안정됩니다. 말보다 기록이 재물을 보호합니다.",
            "계약과 명의는 늦게 잡으면 불리합니다. 친한 사이라도 금액, 지급일, 지분을 남겨야 합니다. 처음의 문서가 나중의 손익을 가릅니다.",
            "계약과 명의가 흐리면 받을 몫이 줄어듭니다. 구두 약속, 늦은 정산, 남의 명의는 손실로 이어질 수 있습니다. 금전 관계는 처음부터 문서가 필요합니다.",
        ),
        "채권·미수금 회수력": (
            "받아야 할 돈을 회수하는 힘이 있습니다. 지급일과 증빙이 남아 있으면 지연된 돈도 되찾을 수 있습니다. 자기 권리를 조용히 밀고 가는 편입니다.",
            "미수금은 늦게 정리할수록 불리합니다. 금액보다 회수 시점과 증빙을 먼저 확정해야 합니다. 받을 돈은 감정이 아니라 절차로 다뤄야 합니다.",
            "받을 돈을 말로 넘기면 회수가 늦어집니다. 상대 사정을 봐주다 보면 자기 몫이 뒤로 밀릴 수 있습니다. 지급일과 증빙을 반드시 남겨야 합니다.",
        ),
        "공동자금 운영력": (
            "공동 자금도 기준을 잡으면 다룰 수 있습니다. 명의와 지분이 분명하면 사람과 돈을 함께 가져갈 수 있습니다. 정을 지키려면 계산이 먼저 정리되어야 합니다.",
            "가까운 사람과 돈을 섞을 때는 몫을 먼저 나눠야 합니다. 시작은 호의여도 수익이 보이면 지분 문제가 올라옵니다. 관계보다 명의가 먼저입니다.",
            "공동 자금은 손실의 중심이 되기 쉽습니다. 가족, 지인, 동업자와 묶인 돈에서 배신감이나 손해가 생길 수 있습니다. 호의로 돈을 맡기면 불리합니다.",
        ),
        "부채·보증 관리력": (
            "대여와 보증은 책임 범위를 잡을 때 안정됩니다. 담보, 상환 시점, 명의가 확인되면 부담을 줄일 수 있습니다. 빌려주는 돈보다 회수 조건이 먼저입니다.",
            "부채와 보증은 신중해야 합니다. 상대의 사정에 끌려가면 책임이 커집니다. 도움을 주더라도 한도와 기한을 정해야 합니다.",
            "부채와 보증은 큰 손실로 번질 수 있습니다. 대신 서준 보증, 빌려준 돈, 공동 명의가 오래 부담으로 남을 수 있습니다. 명의가 들어가는 도움은 피해야 합니다.",
        ),
        "가족재산 경계력": (
            "가족 재산에서도 자기 몫을 지킬 수 있습니다. 명의와 책임선이 분명하면 지원과 손실을 구분합니다. 정리된 문서가 가족 간 부담을 줄입니다.",
            "가족과 얽힌 돈은 감정으로 처리하면 불리합니다. 상속성 자산, 지원금, 공동 지출은 처음 기준이 필요합니다. 자기 몫과 책임을 따로 세워야 합니다.",
            "가족 재산 문제에서 자기 몫이 흐려질 수 있습니다. 대신 떠안은 지출, 빌려준 돈, 명의 문제가 손실로 이어지기 쉽습니다. 가족일수록 돈의 선을 분명히 해야 합니다.",
        ),
        "사업 확장성": (
            "사업 확장성은 분명합니다. 거래처, 단가, 권리 구조가 맞으면 수입의 단위가 커집니다. 혼자 버는 돈보다 구조로 버는 돈이 커집니다.",
            "확장은 가능하지만 순서가 필요합니다. 매출보다 회수와 운영 체계를 먼저 잡아야 합니다. 거래 단위를 키우기 전에 손실 한도를 정해야 합니다.",
            "확장을 서두르면 이익보다 책임이 먼저 커집니다. 사람, 보증, 미수금이 얽히면 손익 계산이 흐려질 수 있습니다. 회수 가능한 구조부터 만들어야 합니다.",
        ),
        "재정 방어력": (
            "손실을 막는 힘이 있습니다. 계약, 명의, 지출 한도를 정하면 재정이 쉽게 무너지지 않습니다. 버는 힘보다 지키는 힘에서 안정이 생깁니다.",
            "재정 방어는 관리 여부에 따라 달라집니다. 작은 지출과 미뤄둔 정산을 넘기면 손실이 커집니다. 돈이 나가는 통로를 줄여야 합니다.",
            "손실이 생기면 한 번에 크게 빠질 수 있습니다. 보증, 공동 자금, 늦은 정산이 재정을 흔들 수 있습니다. 수익보다 위험한 돈부터 막아야 합니다.",
        ),
        "후반 축재력": (
            "후반 재물운이 강하게 올라옵니다. 젊을 때의 현금보다 중년 이후의 소유권과 장기 자산이 커집니다. 시간이 갈수록 재산의 형태가 분명해집니다.",
            "후반으로 갈수록 재물은 안정됩니다. 고정 수입과 자산 보유 구조가 맞으면 재산이 천천히 굳습니다. 빠른 성공보다 누적 재산이 맞습니다.",
            "후반 축재는 늦게 잡힐 수 있습니다. 초반의 돈을 소비로 흘려보내면 중년 이후 자산화가 지연됩니다. 지금부터 권리가 남는 자산을 만들어야 합니다.",
        ),
        "금전 기준성": (
            "돈 앞에서 기준을 세우는 힘이 있습니다. 정, 체면, 분위기보다 소유권과 보상 원칙을 잡을 때 재물이 남습니다. 기준이 선명할수록 손실이 줄어듭니다.",
            "금전 기준은 늦게 세우면 불리합니다. 친한 사이라도 지급일, 몫, 명의를 먼저 나눠야 합니다. 돈 문제는 초반에 정리할수록 좋습니다.",
            "돈 문제를 좋게 넘기면 손실이 커집니다. 처음에 불편한 말을 피하면 나중에 더 큰 금액으로 돌아옵니다. 자기 몫과 책임 범위를 분명히 해야 합니다.",
        ),
    },
    "career": {
        "직업 적성": (
            "직업운은 책임 있는 운영과 판단에서 강합니다. 흩어진 일을 정리하고 결과를 확정하는 자리에서 평가가 올라갑니다. 실행만 하는 자리보다 기준을 잡는 자리가 맞습니다.",
            "직업 적성은 실무와 관리의 중간에 있습니다. 직접 해내면서도 전체 순서와 책임을 정리해야 성과가 납니다. 역할이 흐린 자리는 오래 맞지 않습니다.",
            "단순 반복 업무에서는 직업운이 답답해집니다. 책임은 있는데 판단권이 없으면 소모가 커집니다. 맡은 범위와 결정권이 분명한 자리를 골라야 합니다.",
        ),
        "직업 분야": (
            "직업명보다 업무의 성격이 더 중요합니다. 운영, 기획, 관리, 분석처럼 결과와 책임이 남는 분야가 맞습니다. 사람과 자원을 정리하는 자리에서 강점이 드러납니다.",
            "직업 분야는 넓게 열려 있습니다. 다만 이름이 화려한 일보다 역할이 분명한 일이 맞습니다. 조율, 관리, 분석이 들어간 직무가 유리합니다.",
            "흥미만으로 고른 일은 오래가기 어렵습니다. 결과물과 권한이 남지 않으면 경력이 가볍게 흩어집니다. 직업 선택에서는 업무 구조를 먼저 봐야 합니다.",
        ),
        "성취 축적력": (
            "성과가 이력과 실적으로 남는 힘이 좋습니다. 한 번의 칭찬보다 기록, 포트폴리오, 공식 평가로 쌓일 때 경력의 값이 올라갑니다. 시간이 갈수록 경력이 단단해집니다.",
            "성취는 천천히 쌓이는 편입니다. 빠른 인정보다 결과물을 남기는 일이 강합니다. 기록되는 성과를 의식해야 경력이 커집니다.",
            "성과가 자기 이름으로 남지 않기 쉽습니다. 일을 해도 기록과 평가가 빠지면 경력의 값이 늦게 오릅니다. 결과물의 소유권을 남겨야 합니다.",
        ),
        "평가·명예 전환력": (
            "실적이 평판과 직함으로 바뀌기 쉽습니다. 공식 평가, 추천, 책임 있는 역할이 붙을 때 사회적 이름이 커집니다. 보이지 않는 노력보다 기록된 성과가 강합니다.",
            "평가는 결과물이 있을 때 올라갑니다. 말보다 보고서, 실적, 추천 같은 근거가 필요합니다. 평가 체계가 있는 조직에서 유리합니다.",
            "평가 기준이 흐린 자리는 불리합니다. 공로가 다른 사람에게 넘어가거나 책임만 남을 수 있습니다. 공식 기록이 없는 성과는 오래 남지 않습니다.",
        ),
        "승진·직함 가능성": (
            "승진과 직함은 기대할 만합니다. 책임 범위가 넓어지고 공식 역할이 붙을 때 직업운이 강해집니다. 직함은 실적을 따라오는 쪽입니다.",
            "승진은 가능하지만 순서가 필요합니다. 실적, 보고 체계, 상급자의 인정이 맞아야 합니다. 먼저 맡은 역할에서 이름을 남겨야 합니다.",
            "직함보다 책임이 먼저 올 수 있습니다. 이름은 없는데 일만 늘면 소모가 커집니다. 승진 제도와 권한을 확인해야 합니다.",
        ),
        "사회적 도약성": (
            "사회적 도약의 힘이 있습니다. 한 자리에서 실적을 쌓은 뒤 더 큰 역할로 이동하는 식입니다. 사람들에게 인정받는 이름이 만들어질 수 있습니다.",
            "사회적 도약은 누적 성과 위에서 생깁니다. 갑작스러운 변화보다 준비된 이동이 맞습니다. 평판과 실적을 동시에 관리해야 합니다.",
            "도약의 기회가 와도 기반이 약하면 부담이 커집니다. 큰 자리보다 감당 가능한 권한이 먼저입니다. 무리한 이동은 평판 손상으로 이어질 수 있습니다.",
        ),
        "권한 확보력": (
            "일을 맡을 때 권한도 함께 확보하는 힘이 있습니다. 결정권, 보고 체계, 보상 기준이 붙으면 실력이 크게 드러납니다. 책임 있는 자리에서 강합니다.",
            "권한은 요구해야 생깁니다. 일을 맡는 것만으로는 충분하지 않습니다. 결정 범위와 승인권을 함께 가져와야 합니다.",
            "권한 없이 책임만 맡으면 손상됩니다. 실무는 본인이 하고 결정은 다른 사람이 하는 자리에서 오래 버티기 어렵습니다. 처음부터 권한 범위를 확인해야 합니다.",
        ),
        "책임·권한 균형": (
            "책임과 권한이 맞을 때 크게 성장합니다. 맡은 일의 범위와 결정권이 함께 주어지면 성과가 오래 남습니다. 조직 안에서도 자기 자리를 만들 수 있습니다.",
            "책임은 자연스럽게 커집니다. 다만 권한이 같이 붙어야 경력이 됩니다. 책임 범위와 결정 범위를 따로 확인해야 합니다.",
            "책임은 큰데 결정권이 약한 자리는 피해야 합니다. 문제가 생기면 이름만 남고 보상은 작을 수 있습니다. 권한 없는 책임은 경력 손상으로 이어집니다.",
        ),
        "보상 협상력": (
            "성과를 보상으로 연결하는 협상력이 있습니다. 연봉, 성과급, 직급, 계약 조건을 말할 근거가 생깁니다. 숫자로 증명되는 성과일수록 유리합니다.",
            "보상은 성과를 정리할 때 올라갑니다. 해낸 일을 말로 설명하기보다 수치와 기록으로 제시해야 합니다. 협상은 준비된 자료에서 힘이 납니다.",
            "보상 협상이 늦으면 받을 몫이 줄어듭니다. 이미 일을 끝낸 뒤에는 조건을 바꾸기 어렵습니다. 시작 전에 기준을 잡아야 합니다.",
        ),
        "전문 자산화": (
            "전문성이 자산으로 남기 쉽습니다. 자격, 기술, 실적, 경험이 쌓여 다음 자리의 값이 됩니다. 오래 할수록 단가가 올라가는 분야가 맞습니다.",
            "전문성은 쌓이지만 드러내는 방식이 필요합니다. 기록, 자격, 포트폴리오가 붙어야 경력 자산이 됩니다. 해낸 일을 밖에서 볼 수 있게 만들어야 합니다.",
            "전문성이 흩어지면 경력으로 남지 않습니다. 여러 일을 해도 이름 붙일 기술이 없으면 약해집니다. 자신을 설명할 전문 축을 잡아야 합니다.",
        ),
        "조직 적응력": (
            "조직 안에서 자리를 잡는 힘이 있습니다. 규칙을 이해하고 필요한 사람을 설득하며 실적을 남기는 방식이 맞습니다. 오래 갈 조직에서는 영향력이 커집니다.",
            "조직 적응은 환경을 탑니다. 기준이 분명한 조직에서는 강하지만, 책임이 흐린 조직에서는 피로가 큽니다. 보고 체계가 있는 곳이 맞습니다.",
            "조직의 기준이 자주 바뀌면 소모가 커집니다. 책임 전가가 많은 곳에서는 실력이 묻힐 수 있습니다. 규칙과 평가가 흐린 조직은 피해야 합니다.",
        ),
        "소속 전환력": (
            "소속을 바꿔도 역할을 다시 만들 수 있습니다. 이직, 부서 이동, 직무 전환에서 적응력이 살아납니다. 이전 실적을 새 자리의 근거로 쓰는 편입니다.",
            "소속 전환은 준비가 있을 때 좋습니다. 이동 자체보다 옮긴 뒤 맡을 역할이 중요합니다. 이전 경력과 새 역할의 연결을 따져야 합니다.",
            "성급한 이동은 불리합니다. 소속만 바꾸고 역할이 불분명하면 경력 공백처럼 보일 수 있습니다. 전환 전 다음 자리의 권한을 확인해야 합니다.",
        ),
        "독립 가능성": (
            "독립 가능성은 있습니다. 자기 이름으로 거래처, 고객, 결과물을 가져갈 때 강해집니다. 조직에서 쌓은 전문성이 독립 기반이 됩니다.",
            "독립은 준비형입니다. 거래처, 수입원, 운영 체계가 있어야 안정됩니다. 기분으로 나가는 독립은 맞지 않습니다.",
            "독립을 서두르면 부담이 커집니다. 고객, 현금, 계약 구조가 없으면 책임만 늘어납니다. 먼저 고정 수입원을 만들어야 합니다.",
        ),
        "업무 조건 감별력": (
            "좋은 자리와 소모되는 자리를 구분하는 눈이 필요합니다. 권한, 평가, 보상, 보고 체계를 보면 답이 나옵니다. 조건을 잘 고르면 경력 손상이 줄어듭니다.",
            "업무 조건은 꼼꼼히 따져야 합니다. 직함보다 실제 권한과 평가 방식을 확인해야 합니다. 일의 범위가 분명한 자리가 유리합니다.",
            "조건을 대충 넘기면 손해가 큽니다. 책임은 넓고 보상은 작은 자리에 들어갈 수 있습니다. 입사와 계약 전 역할 범위를 확인해야 합니다.",
        ),
    },
    "love": {
        "끌림의 기준": (
            "마음은 가벼운 말보다 태도에서 움직입니다. 약속을 지키고 생활 감각이 안정된 사람에게 오래 끌립니다. 순간의 설렘보다 신뢰감이 강합니다.",
            "처음에는 호감이 생겨도 쉽게 확신하지 않습니다. 상대의 말과 행동이 반복해서 맞는지 확인합니다. 시간이 지나며 마음이 깊어지는 편입니다.",
            "말이 화려한 사람에게 흔들리면 손상이 생깁니다. 처음의 끌림보다 생활 태도를 봐야 합니다. 감정이 앞서면 상대 판단이 늦어질 수 있습니다.",
        ),
        "상대 선택력": (
            "오래 갈 사람을 고르는 눈이 좋습니다. 책임감, 생활 태도, 약속의 일관성을 빠르게 읽습니다. 가벼운 관계보다 신뢰가 남는 관계가 맞습니다.",
            "상대 선택은 신중한 편입니다. 마음이 있어도 쉽게 들어가지 않고 사람을 확인합니다. 이 신중함이 관계 손실을 줄입니다.",
            "상대의 말만 믿으면 손상될 수 있습니다. 처음의 호감이 좋아도 책임감이 없으면 오래 가지 않습니다. 선택 기준을 낮추면 관계 피로가 커집니다.",
        ),
        "상대 신뢰 감별력": (
            "상대의 진심을 비교적 잘 읽습니다. 반복된 태도, 약속, 돈과 시간의 사용에서 신뢰를 판단합니다. 말보다 행동을 더 정확히 봅니다.",
            "신뢰 판단은 시간이 걸립니다. 확신이 생기기 전까지 마음을 완전히 열지 않습니다. 관계가 늦게 깊어져도 안정성은 높아집니다.",
            "상대의 감정 표현에 끌려가면 판단이 흐려질 수 있습니다. 반복된 행동을 확인하지 않으면 실망이 큽니다. 신뢰는 말보다 생활에서 봐야 합니다.",
        ),
        "인연 형성력": (
            "인연은 생활권과 반복 접점에서 강하게 들어옵니다. 협업, 소개, 자주 마주치는 자리에서 관계가 실제 만남으로 굳습니다. 갑작스러운 인연보다 익숙해지는 인연이 좋습니다.",
            "인연은 꾸준히 들어오는 편입니다. 다만 스쳐 가는 호감을 실제 만남으로 옮기는 과정이 필요합니다. 반복된 연락과 약속이 관계를 만듭니다.",
            "인연이 있어도 관계로 굳기까지 시간이 걸립니다. 처음의 호감을 놓치거나 표현이 늦어질 수 있습니다. 만남을 미루면 인연이 흐려집니다.",
        ),
        "관계 진전력": (
            "관계가 시작되면 현실적인 약속으로 넘어가기 쉽습니다. 만남, 공개, 장기 계획이 붙을 때 애정운이 강해집니다. 가벼운 관계보다 정식 관계에 맞습니다.",
            "관계 진전은 속도보다 확신이 필요합니다. 상대의 태도와 책임감이 보이면 빠르게 깊어질 수 있습니다. 애매한 관계는 오래 두지 않는 편이 좋습니다.",
            "마음은 있어도 관계가 늦어질 수 있습니다. 표현이 늦고 확인이 많으면 상대가 거리감을 느낍니다. 진전이 필요할 때는 약속을 분명히 해야 합니다.",
        ),
        "관계 주도권": (
            "관계 안에서 주도권을 잡을 수 있습니다. 감정에 끌려가기보다 관계의 방향과 속도를 조정합니다. 상대가 불안정할수록 본인이 중심을 잡습니다.",
            "관계 주도권은 상황에 따라 달라집니다. 마음이 깊어지면 상대에게 맞추는 폭도 커집니다. 다만 기준을 잃으면 피로가 생깁니다.",
            "상대에게 끌려가면 관계가 불리해집니다. 연락, 만남, 돈, 시간의 기준이 상대 중심으로 흐를 수 있습니다. 초반부터 자기 속도를 지켜야 합니다.",
        ),
        "관계 속도 조절력": (
            "관계 속도를 조절하는 힘이 있습니다. 너무 빠른 관계보다 서로의 생활을 확인하며 깊어지는 방식이 맞습니다. 급하지 않은 만남에서 안정됩니다.",
            "속도 조절은 필요합니다. 마음이 있어도 바로 확정하기보다 생활 기준을 맞춰갑니다. 상대가 기다릴 수 있는 사람인지 봐야 합니다.",
            "속도가 어긋나면 관계가 흔들립니다. 상대는 빠른 확신을 원하고 본인은 확인이 필요할 수 있습니다. 늦은 표현이 오해로 남기 쉽습니다.",
        ),
        "애정 표현성": (
            "마음이 깊어지면 행동으로 표현하는 편입니다. 말보다 챙김, 시간, 책임감으로 애정을 보입니다. 상대가 이 방식을 이해하면 오래 갑니다.",
            "애정 표현은 절제된 편입니다. 좋아해도 과장된 말보다 안정된 태도를 보입니다. 상대에게는 확신을 주는 말도 필요합니다.",
            "표현이 늦으면 손상이 생깁니다. 마음은 있어도 상대가 확신을 얻지 못할 수 있습니다. 필요한 순간에는 분명히 말해야 합니다.",
        ),
        "정서 수용력": (
            "상대의 감정을 받아내는 힘이 있습니다. 쉽게 끊기보다 왜 그런지 확인하고 조정하려는 편입니다. 안정적인 상대와 만나면 관계가 깊어집니다.",
            "정서 수용은 가능하지만 한계가 분명합니다. 반복되는 불안과 감정 기복은 피로를 키웁니다. 상대의 감정을 다 떠안으면 안 됩니다.",
            "감정 기복이 큰 상대와 만나면 손상됩니다. 달래고 맞추는 시간이 길어지면 본인의 일상까지 흔들립니다. 불안정한 관계는 오래 끌지 않는 편이 좋습니다.",
        ),
        "관계 지속력": (
            "한 번 깊어진 관계는 오래 유지하려는 힘이 강합니다. 쉽게 끊기보다 책임감 있게 붙잡습니다. 안정된 상대와는 장기 관계로 이어집니다.",
            "관계는 오래 가는 편입니다. 다만 유지하는 동안 표현과 약속을 계속 확인해야 합니다. 묵묵함만으로는 부족할 때가 있습니다.",
            "관계를 끌고 가다가 지칠 수 있습니다. 이미 손상된 관계를 오래 붙잡으면 회복보다 소모가 커집니다. 끝낼 관계와 지킬 관계를 구분해야 합니다.",
        ),
        "연락·거리 안정성": (
            "연락과 거리의 균형을 잡을 수 있습니다. 지나치게 붙거나 멀어지지 않는 관계에서 안정됩니다. 서로의 생활을 존중하는 연애가 맞습니다.",
            "연락 방식은 조율이 필요합니다. 본인은 부담 없는 거리를 원해도 상대는 확신을 원할 수 있습니다. 초반에 연락 기준을 맞추는 편이 좋습니다.",
            "연락이 늦거나 거리감이 커지면 오해가 생깁니다. 상대는 무관심으로 받아들일 수 있습니다. 바쁠수록 짧은 확인이 필요합니다.",
        ),
        "오해 조정력": (
            "오해가 생겨도 다시 정리할 수 있습니다. 감정보다 사실과 약속을 확인하면 관계가 회복됩니다. 차분한 대화가 관계를 살립니다.",
            "오해 조정은 가능하지만 늦으면 커집니다. 서운함을 오래 두면 말이 딱딱해집니다. 작은 오해일 때 풀어야 합니다.",
            "오해를 방치하면 관계가 급격히 식습니다. 말하지 않은 서운함이 쌓이면 회복이 늦어집니다. 침묵보다 정리가 필요합니다.",
        ),
        "갈등 관리력": (
            "갈등이 생겨도 기준을 세우면 풀립니다. 감정 싸움보다 약속, 시간, 돈, 역할을 다시 나누는 방식이 맞습니다. 현실적인 정리가 관계를 지킵니다.",
            "갈등 관리는 상대에 따라 달라집니다. 대화가 되는 상대와는 회복이 빠릅니다. 감정으로 밀어붙이는 상대와는 피로가 커집니다.",
            "갈등이 반복되면 관계 손상이 큽니다. 같은 문제를 여러 번 넘기면 애정이 남아도 신뢰가 약해집니다. 반복되는 갈등은 초기에 끊어야 합니다.",
        ),
        "주변 개입 관리력": (
            "주변 말이 들어와도 관계의 중심을 지킬 수 있습니다. 가족, 친구, 과거 인연의 말보다 두 사람의 약속이 우선입니다. 경계를 세우면 관계가 안정됩니다.",
            "주변 개입은 조심해야 합니다. 가까운 사람의 조언이 관계 판단을 흔들 수 있습니다. 연애 문제는 둘 사이에서 먼저 정리해야 합니다.",
            "주변 개입이 강하면 관계가 흔들립니다. 가족, 친구, 과거 인연의 말이 오해를 키울 수 있습니다. 사적인 문제를 밖으로 넓히면 불리합니다.",
        ),
        "재회 가능성": (
            "끊어진 인연도 다시 올라올 수 있습니다. 감정만 남은 재회보다 생활 기준이 바뀐 재회가 오래 갑니다. 과거보다 달라진 조건이 있어야 합니다.",
            "재회 가능성은 있으나 선택이 필요합니다. 그리움만으로 돌아가면 같은 문제가 반복됩니다. 관계 방식이 바뀌었는지 봐야 합니다.",
            "재회는 손상을 반복할 수 있습니다. 과거의 문제가 그대로라면 다시 만나도 오래 안정되기 어렵습니다. 미련과 현실을 구분해야 합니다.",
        ),
        "결혼 연결력": (
            "연애가 결혼으로 이어질 힘이 있습니다. 감정이 생활 약속으로 넘어가면 관계가 굳어집니다. 오래 만나는 사람과 현실 논의가 붙기 쉽습니다.",
            "결혼 연결은 생활 조건이 맞을 때 강해집니다. 마음만으로는 부족하고 집, 돈, 가족 협의가 따라와야 합니다. 현실 준비가 관계를 굳힙니다.",
            "연애가 결혼으로 넘어가는 과정에서 지연이 생길 수 있습니다. 생활 조건이나 가족 문제가 걸리면 결정이 늦어집니다. 감정보다 현실 조율이 필요합니다.",
        ),
    },
    "marriage": {
        "혼인 성향": (
            "결혼을 생활의 약속으로 받아들이는 편입니다. 감정의 깊이보다 함께 버틸 수 있는 책임감이 더 크게 작용합니다. 안정된 상대와 오래 갑니다.",
            "결혼은 신중하게 결정합니다. 마음이 깊어도 생활 조건이 맞지 않으면 쉽게 확정하지 않습니다. 현실을 확인한 뒤 결혼으로 갑니다.",
            "감정만으로 결혼하면 부담이 커집니다. 생활비, 주거, 가족 책임을 확인하지 않으면 결혼 뒤 피로가 빠르게 올라옵니다. 현실 조건을 먼저 봐야 합니다.",
        ),
        "배우자상": (
            "성실하고 기준이 분명한 배우자와 오래 갑니다. 감정 기복이 적고 자기 몫을 조용히 해내는 사람이 맞습니다. 안정감 있는 사람이 복이 됩니다.",
            "배우자상은 생활형입니다. 화려한 사람보다 책임감이 있는 사람이 맞습니다. 같이 살 때 믿을 수 있는 사람이 중요합니다.",
            "감정 기복이 큰 배우자와는 충돌이 잦습니다. 말은 좋아도 생활 책임이 약하면 결혼 뒤 부담이 커집니다. 성실함을 먼저 봐야 합니다.",
        ),
        "결혼 현실화력": (
            "결혼 의사가 실제 절차로 이어지기 쉽습니다. 집, 일정, 가족 협의가 잡히면 결정이 빠르게 굳어집니다. 마음이 생활 계획으로 넘어갈 때 강합니다.",
            "결혼 현실화는 준비에 달려 있습니다. 감정은 있어도 주거와 돈의 기준이 잡혀야 확정됩니다. 현실 계획이 생기면 결혼이 가까워집니다.",
            "결혼 논의가 길어질 수 있습니다. 마음은 있어도 생활 조건이 정리되지 않으면 결정이 미뤄집니다. 준비 없는 약속은 부담이 됩니다.",
        ),
        "생활 안정": (
            "결혼 생활은 안정적으로 가져갈 수 있습니다. 주거, 생활비, 역할 기준이 잡히면 오래 버팁니다. 가정 안에서 책임을 다하려는 힘이 있습니다.",
            "생활 안정은 기준을 세울수록 좋아집니다. 애정이 있어도 돈과 시간의 사용을 맞춰야 합니다. 일상의 약속이 결혼을 지킵니다.",
            "생활 기준이 어긋나면 애정이 있어도 피로가 커집니다. 생활비, 집안일, 가족 책임이 한쪽으로 몰리면 불만이 쌓입니다. 초반 합의가 필요합니다.",
        ),
        "주거·생활 설계력": (
            "집과 생활 구조를 현실적으로 짜는 힘이 있습니다. 주거, 비용, 동선을 정리하면 결혼 생활이 안정됩니다. 큰 약속보다 생활 설계가 강합니다.",
            "주거와 생활 설계는 천천히 잡아야 합니다. 집 문제와 생활비를 따로 보면 갈등이 줄어듭니다. 일정과 비용을 분명히 해야 합니다.",
            "주거 문제가 늦게 정리되면 결혼 생활이 흔들립니다. 집, 대출, 생활비 기준이 흐리면 갈등이 커집니다. 낭만보다 설계가 먼저입니다.",
        ),
        "가정 운영력": (
            "가정을 운영하는 힘이 있습니다. 비용, 일정, 책임을 정리하며 생활을 안정시키는 편입니다. 결혼 뒤에도 실무형 책임감이 강합니다.",
            "가정 운영은 가능하지만 역할 분담이 필요합니다. 한쪽이 모든 일을 맡으면 금방 지칩니다. 책임을 나누면 안정됩니다.",
            "가정의 책임이 한쪽으로 몰리면 버티기 어렵습니다. 돈, 돌봄, 집안일이 쌓이면 애정도 피로해집니다. 역할 분담을 늦추면 안 됩니다.",
        ),
        "부부 재정": (
            "부부 재정은 안정적으로 만들 수 있습니다. 공동 생활비와 개인 자산의 선을 나누면 돈 문제가 크게 흔들리지 않습니다. 명의와 지출 기준이 중요합니다.",
            "부부 돈은 기준이 필요합니다. 같이 쓰는 돈과 각자 지킬 돈을 나눠야 합니다. 생활비 기준이 결혼 안정에 직접 작용합니다.",
            "부부 재정이 흐리게 섞이면 갈등이 커집니다. 한쪽이 더 부담하거나 명의가 불리해질 수 있습니다. 사랑과 돈의 장부는 따로 세워야 합니다.",
        ),
        "생활비 기준성": (
            "생활비 기준을 세우는 힘이 있습니다. 고정비, 저축, 가족 지원의 선을 나누면 결혼 생활이 단단해집니다. 돈의 질서가 곧 안정입니다.",
            "생활비는 합의가 필요합니다. 쓰는 방식이 다르면 작은 돈도 서운함으로 남습니다. 고정비와 각자 지출을 분명히 해야 합니다.",
            "생활비 기준이 흐리면 불만이 커집니다. 돈을 누가 더 쓰고 누가 더 부담하는지가 갈등이 됩니다. 초반부터 계산 방식을 정해야 합니다.",
        ),
        "부부 갈등 조정력": (
            "부부 갈등은 현실 기준을 다시 세울 때 풀립니다. 감정 싸움보다 역할과 비용을 재정리하는 방식이 맞습니다. 말보다 생활 변화가 회복을 만듭니다.",
            "갈등 조정은 가능하지만 늦으면 커집니다. 서운함이 쌓이기 전에 책임 범위를 다시 나눠야 합니다. 반복되는 문제는 구조를 바꿔야 합니다.",
            "갈등을 말로만 넘기면 오래 남습니다. 사과는 있어도 역할 변화가 없으면 같은 문제가 반복됩니다. 생활 기준을 바꾸지 않으면 회복이 늦습니다.",
        ),
        "부부 갈등 회복성": (
            "상한 감정 뒤에도 회복할 수 있는 힘이 있습니다. 책임을 다시 나누고 약속을 지키면 관계가 안정됩니다. 성숙한 대화가 결혼을 살립니다.",
            "회복은 가능하지만 시간이 필요합니다. 감정 표현보다 실제 변화가 있어야 합니다. 반복된 약속 위반은 신뢰를 늦게 회복시킵니다.",
            "갈등 회복이 늦어질 수 있습니다. 한 번 상한 마음을 오래 붙들 가능성이 있습니다. 말뿐인 화해보다 생활 변화가 필요합니다.",
        ),
        "가족 책임 경계력": (
            "양가와 원가족 문제에서 부부의 기준을 세울 수 있습니다. 지원과 책임을 분리하면 결혼 생활이 지켜집니다. 가족 문제도 선이 있어야 안정됩니다.",
            "가족 책임은 조심해서 나눠야 합니다. 부모, 형제, 친척의 문제가 부부 생활로 들어올 수 있습니다. 부부의 합의가 먼저입니다.",
            "가족 문제를 정으로 떠안으면 결혼 생활이 흔들립니다. 돈과 돌봄이 한쪽으로 몰리면 배우자의 불만이 커집니다. 원가족과 부부의 선을 분명히 해야 합니다.",
        ),
        "배우자 가족 경계": (
            "배우자 가족과도 적절한 거리를 만들 수 있습니다. 예의는 지키되 책임 범위를 분명히 하면 안정됩니다. 가까움보다 선명한 역할이 중요합니다.",
            "배우자 가족 문제는 조율이 필요합니다. 도움을 주더라도 부부가 먼저 합의해야 합니다. 돌봄과 비용의 한도를 정해야 합니다.",
            "배우자 가족 문제가 깊이 들어오면 부담이 큽니다. 돈, 돌봄, 거주 문제가 부부 갈등으로 번질 수 있습니다. 초반부터 경계를 세워야 합니다.",
        ),
        "자녀·양육 책임": (
            "자녀와 양육 문제에서도 책임감이 강합니다. 교육비, 돌봄, 생활 시간을 실제로 감당하려는 편입니다. 가족을 챙기는 힘이 있습니다.",
            "양육 책임은 현실 계획이 필요합니다. 비용과 시간을 누가 얼마나 맡을지 나눠야 합니다. 준비가 있으면 안정됩니다.",
            "양육과 돌봄 책임이 한쪽으로 몰리면 갈등이 커집니다. 교육비와 시간 부담이 결혼 생활을 압박할 수 있습니다. 역할 분담을 분명히 해야 합니다.",
        ),
        "배우자 복": (
            "배우자에게서 생활의 안정감을 얻을 수 있습니다. 성실한 상대를 만나면 결혼 뒤 기반이 단단해집니다. 서로의 책임감이 복으로 작용합니다.",
            "배우자 복은 상대의 생활 태도에 달려 있습니다. 좋은 감정보다 성실함과 책임감이 더 중요합니다. 안정형 배우자를 만나야 합니다.",
            "배우자에게 기대는 부분이 커지면 부담도 커집니다. 상대가 불안정하면 결혼 생활 전체가 흔들립니다. 배우자 선택이 매우 중요합니다.",
        ),
        "혼인 위기 대응력": (
            "위기가 와도 다시 정리할 수 있는 힘이 있습니다. 돈, 가족, 주거 문제가 겹쳐도 책임 기준을 새로 세우면 버팁니다. 위기 뒤에 관계가 더 현실적으로 바뀝니다.",
            "혼인 위기는 대화보다 구조 조정이 필요합니다. 생활비, 가족 책임, 주거 문제를 다시 나눠야 합니다. 감정만 풀어서는 부족합니다.",
            "위기가 길어지면 결혼 생활이 크게 손상됩니다. 돈과 가족 문제가 동시에 오면 회복이 늦습니다. 미루지 말고 기준을 다시 세워야 합니다.",
        ),
        "결혼 지속력": (
            "한 번 정한 약속을 오래 지키는 힘이 있습니다. 쉽게 흔들리지 않고 생활을 이어가려는 의지가 강합니다. 안정된 배우자와 만나면 결혼이 오래 갑니다.",
            "결혼 지속력은 있는 편입니다. 다만 표현과 생활 변화가 함께 있어야 합니다. 묵묵함만으로는 배우자가 외로울 수 있습니다.",
            "약속을 미루는 시간이 길어지면 상대의 불안이 커집니다. 결혼 뒤에도 생활 변화가 없으면 신뢰가 약해집니다. 지키겠다는 말보다 행동이 필요합니다.",
        ),
    },
}


def _premium_required_product_body_override(
    domain: str,
    title: str,
    score: int | None,
    *,
    tone: str = "",
) -> str:
    if "연도" in title or title in {"결혼 적기"}:
        return ""
    templates = PREMIUM_REQUIRED_PRODUCT_BODY_OVERRIDES.get(domain, {}).get(title)
    if not templates:
        return ""
    if tone in {"watch", "risk", "caution"}:
        level = 2
    elif not isinstance(score, int):
        level = 1
    elif score >= 74:
        level = 0
    elif score >= 55:
        level = 1
    else:
        level = 2
    return templates[min(level, len(templates) - 1)]


def _premium_required_judgment_meaning(domain: str, title: str) -> str:
    return PREMIUM_REQUIRED_JUDGMENT_MEANINGS.get(domain, {}).get(title, "")


def _premium_required_judgment_scene(domain: str, title: str, tone: str) -> str:
    scenes = PREMIUM_REQUIRED_JUDGMENT_SCENES.get(domain, {})
    pair = scenes.get(title)
    if not pair and domain == "timing":
        if "주의" in title or "부담" in title or "손실" in title:
            pair = scenes.get("주의 연도")
        else:
            pair = scenes.get("상승 연도")
    if not pair:
        return ""
    return pair[1] if tone in {"watch", "risk", "caution"} else pair[0]


def _premium_required_timing_event_parts(title: str, matched: dict[str, Any] | None) -> tuple[str, str, str]:
    if str((matched or {}).get("source_type") or "") != "timing_event":
        return ("", "", "")
    direct_year = (matched or {}).get("year")
    direct_focus = str((matched or {}).get("focus") or "").strip()
    if direct_year not in (None, ""):
        year = f"{int(direct_year)}년" if isinstance(direct_year, (int, float)) or str(direct_year).isdigit() else str(direct_year)
        age_value = (matched or {}).get("age")
        age_label = str((matched or {}).get("age_label") or "").strip()
        age = age_label or (f"{int(age_value)}세" if isinstance(age_value, (int, float)) or str(age_value).isdigit() else str(age_value or ""))
        topic = _dedupe_repeated_phrase(direct_focus or str((matched or {}).get("value") or "").strip())
        return (year, age, topic)
    raw = " ".join(str((matched or {}).get("body") or "").split()).strip()
    if not raw:
        return ("", "", "")
    if title and raw.startswith(title):
        raw = raw[len(title):].strip()
    parts = [part.strip(" .") for part in re.split(r"\s+·\s+", raw) if part.strip(" .")]
    year = parts[0] if parts else ""
    age = parts[1] if len(parts) >= 2 else ""
    topic = _dedupe_repeated_phrase(" ".join(parts[2:])) if len(parts) >= 3 else ""
    if re.fullmatch(r"\d{4}", year):
        year = f"{year}년"
    return (year, age, topic)


def _premium_required_timing_event_value(title: str, matched: dict[str, Any] | None) -> str:
    year, age, topic = _premium_required_timing_event_parts(title, matched)
    return " · ".join(part for part in (year, age, topic) if part)


def _premium_required_timing_event_body(title: str, matched: dict[str, Any] | None) -> str:
    year, age, topic = _premium_required_timing_event_parts(title, matched)
    if not year:
        return ""
    year_label = f"{year}({age})" if age else year
    topic_label = topic or title
    if title == "결혼 적기":
        return f"{year_label}은 결혼 논의가 현실 절차로 넘어가는 해입니다. 주거와 생활 조건이 결혼 결정의 전면에 놓입니다."
    if "수입" in title:
        return f"{year_label}은 현금 수입이 강해지는 해입니다. 받을 금액이 구체적으로 잡힙니다."
    if "재물" in title or "자산" in title:
        return f"{year_label}은 재물 사건이 뚜렷해지는 해입니다. 수입보다 명의와 자산 귀속이 중요해집니다."
    if "직업" in title or "권한" in title or "보상" in title:
        return f"{year_label}은 직업적 변화가 크게 드러나는 해입니다. 보상 기준도 함께 달라집니다."
    if "연애" in title or "인연" in title or "관계" in title or "재회" in title or "이별" in title:
        if "주의" in title or "이별" in title:
            return f"{year_label}은 관계의 부담이 커지는 해입니다. 주변 개입을 가볍게 넘기면 손상이 남습니다."
        return f"{year_label}은 인연과 관계 진전이 강해지는 해입니다. 호감이 실제 만남과 약속으로 넘어가기 쉽습니다."
    if "주의" in title or "부담" in title:
        return f"{year_label}은 {topic_label} 문제가 커지는 해입니다. 결정보다 책임 범위를 먼저 확인해야 합니다."
    if topic:
        return f"{year_label}은 {topic_label}{_subject_particle(topic_label)} 두드러지는 해입니다. 제안과 결정이 실제 결과로 이어지기 쉽습니다."
    return f"{year_label}은 해당 사건이 강하게 드러나는 해입니다."


def _premium_required_judgment_body(
    domain: str,
    title: str,
    score: int | None,
    matched: dict[str, Any] | None,
) -> str:
    override_body = _premium_required_product_body_override(
        domain,
        title,
        score,
        tone=str((matched or {}).get("tone") or ""),
    )
    if override_body:
        return override_body
    if str((matched or {}).get("source") or "") == "output_goal_coverage":
        timing_body = _premium_required_timing_event_body(title, matched)
        if timing_body:
            return timing_body
        matched_tone = str((matched or {}).get("tone") or "")
        if title == "사업 확장성" and (
            matched_tone in {"watch", "risk", "caution"} or (isinstance(score, int) and score < 55)
        ):
            return "거래 단위와 회수 기준이 맞을 때 재물 규모가 커집니다. 확장을 서두르면 이익보다 책임이 먼저 커집니다. 회수 가능한 구조부터 잡아야 합니다."
        templates = _premium_required_sentence_templates(domain, title)
        if templates:
            level = 2 if matched_tone in {"watch", "risk", "caution"} else _premium_required_sentence_level(score, title=title)
            return templates[min(level, len(templates) - 1)]
        matched_body = str((matched or {}).get("body") or "").strip()
        if matched_body:
            return _premium_story_sentence(matched_body, max_sentences=2)
    if str((matched or {}).get("source") or "") == "domain_decision_facet":
        label = str((matched or {}).get("label") or title).strip()
        meaning = str((matched or {}).get("body") or "").strip()
        matched_tone = str((matched or {}).get("tone") or "")
        templates = _premium_required_sentence_templates(domain, title)
        if title == "사업 확장성" and (matched_tone in {"watch", "risk", "caution"} or (isinstance(score, int) and score < 55)):
            return "거래 단위와 회수 기준이 맞을 때 재물 규모가 커집니다. 확장을 서두르면 이익보다 책임이 먼저 커집니다. 회수 가능한 구조부터 잡아야 합니다."
        if templates and title in PREMIUM_REQUIRED_PRESERVE_TEMPLATE_TITLES:
            level = 2 if matched_tone in {"watch", "risk", "caution"} else _premium_required_sentence_level(score, title=title)
            return templates[min(level, len(templates) - 1)]
        if templates:
            level = 2 if matched_tone in {"watch", "risk", "caution"} else _premium_required_sentence_level(score, title=title)
            return templates[min(level, len(templates) - 1)]
        if title in PREMIUM_REQUIRED_PRESERVE_TEMPLATE_TITLES:
            preserved = PREMIUM_POSITIVE_UNIT_DEFAULTS.get(title)
            if preserved:
                if title == "사업 확장성" and (matched_tone in {"watch", "risk", "caution"} or (isinstance(score, int) and score < 55)):
                    return f"{preserved} 확장을 서두르면 이익보다 책임이 먼저 커집니다. 회수 가능한 구조부터 잡아야 합니다."
                return preserved
        if title == "재물 주의 연도":
            return "재물 주의 연도에는 계약, 명의, 지분, 보증을 먼저 확인해야 합니다. 가까운 사람의 부탁이나 급한 투자 제안은 손실로 번지기 쉽습니다."
        if matched_tone in {"watch", "risk", "caution"}:
            if label == "공동자금 안정성":
                return "공동자금 안정성은 주의가 필요합니다. 가족, 지인, 동업자와 자금을 함께 다룰 때 몫과 명의가 불리하게 기울 수 있습니다."
            if label == "계약·명의 안전성":
                return "계약·명의 안전성은 주의가 필요합니다. 계약서, 명의, 지분, 보증에서 금전 권리를 잃지 않도록 처음부터 문서로 확정해야 합니다."
        if isinstance(score, int):
            if score >= 86:
                verdict = "상당히 강합니다"
            elif score >= 76:
                verdict = "강합니다"
            elif score >= 64:
                verdict = "분명합니다"
            elif score >= 52:
                verdict = "중간권입니다"
            elif score >= 40:
                verdict = "불안정합니다"
            else:
                verdict = "취약합니다"
            return f"{label}{_topic_particle(label)} {verdict}. {meaning}".strip()
        if meaning:
            return meaning
    templates = _premium_required_sentence_templates(domain, title)
    if templates:
        matched_tone = str((matched or {}).get("tone") or "")
        level = 2 if matched_tone in {"watch", "risk", "caution"} else _premium_required_sentence_level(score, title=title)
        return templates[min(level, len(templates) - 1)]
    matched_body = str((matched or {}).get("body") or "").strip()
    if matched_body:
        return _premium_story_sentence(matched_body, max_sentences=2)
    return f"{title}은 세부 확인이 필요한 기준입니다."


def _premium_timing_required_judgment_cards(section: dict[str, Any], required_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profile = section.get("section_profile") if isinstance(section.get("section_profile"), dict) else {}
    items = [item for item in profile.get("items") or [] if isinstance(item, dict)]
    timing_map = section.get("timing_map") if isinstance(section.get("timing_map"), dict) else {}
    timing_profile = section.get("timing_profile") if isinstance(section.get("timing_profile"), dict) else {}
    timing_events = [item for item in section.get("timing_events") or [] if isinstance(item, dict)]
    timing_decades = [item for item in section.get("timing_decades") or [] if isinstance(item, dict)]
    timing_decision = section.get("timing_decision_facets") if isinstance(section.get("timing_decision_facets"), dict) else {}
    decision_events = timing_decision.get("event_years") if isinstance(timing_decision.get("event_years"), dict) else {}

    def by_label(label: str) -> dict[str, Any]:
        return next((item for item in items if str(item.get("label") or "") == label), {})

    def event_label(event: dict[str, Any] | None) -> str:
        if not event:
            return ""
        year = str(event.get("year") or "").strip()
        age = str(event.get("ageLabel") or event.get("age_label") or "").strip()
        title = str(event.get("title") or event.get("summary") or event.get("keywords") or event.get("focus") or event.get("event_label") or "").strip()
        if not year:
            return title
        prefix = f"{year}년"
        if age:
            prefix = f"{prefix}({age})"
        return " ".join(part for part in (prefix, title) if part)

    def decision_event_label(*keys: str) -> str:
        for key in keys:
            event = decision_events.get(key) if isinstance(decision_events, dict) else None
            if isinstance(event, dict):
                label = event_label(event)
                if label:
                    return label
        return ""

    def first_event(events: list[dict[str, Any]], *, kind: str | None = None) -> dict[str, Any] | None:
        usable = [event for event in events if not kind or str(event.get("kind") or "") == kind]
        if not usable:
            return None
        return sorted(
            usable,
            key=lambda event: (-float(event.get("score") or 0), int(event.get("year") or 9999)),
        )[0]

    def highest_change_event() -> dict[str, Any] | None:
        if not timing_events:
            return None
        return sorted(
            timing_events,
            key=lambda event: (-_number_value((event.get("scoreParts") or {}).get("change")), -float(event.get("score") or 0)),
        )[0]

    def recovery_event() -> dict[str, Any] | None:
        caution_years = sorted(
            int(event.get("year") or 0)
            for event in timing_events
            if str(event.get("kind") or "") == "caution" and event.get("year")
        )
        good_events = sorted(
            (event for event in timing_events if str(event.get("kind") or "") == "good" and event.get("year")),
            key=lambda event: int(event.get("year") or 0),
        )
        for caution_year in caution_years:
            for event in good_events:
                if int(event.get("year") or 0) > caution_year:
                    return event
        return first_event(good_events)

    def later_stability_label() -> str:
        labels: list[str] = []
        for group in timing_decades:
            label = str(group.get("label") or "")
            if label not in {"60대", "70대"}:
                continue
            good = group.get("good") if isinstance(group.get("good"), dict) else None
            caution = group.get("caution") if isinstance(group.get("caution"), dict) else None
            event = good or caution
            rendered = event_label(event)
            labels.append(rendered or str(group.get("yearRange") or label))
        return " / ".join(label for label in labels if label) or "60대~70대"

    good = by_label("상승 연도") or by_label("좋은 연도")
    caution = by_label("주의 연도")
    topic = by_label("사건 주제")
    good_highlights = [item for item in timing_map.get("goodHighlights") or [] if isinstance(item, dict)]
    caution_highlights = [item for item in timing_map.get("cautionHighlights") or [] if isinstance(item, dict)]
    top_good_label = event_label(first_event(good_highlights) or first_event(timing_events, kind="good"))
    top_caution_label = event_label(first_event(caution_highlights) or first_event(timing_events, kind="caution"))
    good_value = top_good_label or str(good.get("value") or "").split("/", 1)[0].strip()
    caution_value = top_caution_label or str(caution.get("value") or "").split("/", 1)[0].strip()
    transition_value = event_label(highest_change_event()) or str(timing_profile.get("decisiveAgeBands") or "전환 구간").strip()
    recovery_value = event_label(recovery_event()) or good_value
    later_value = later_stability_label()
    past_value = event_label((timing_map.get("pastCheck") or [None])[0] if isinstance(timing_map.get("pastCheck"), list) else None)
    topic_value = str(topic.get("value") or timing_profile.get("goodFocus") or "주요 분야").strip()
    value_by_title = {
        "대운 구간": str(timing_decision.get("range") or timing_profile.get("decisiveAgeBands") or topic_value or "20세~79세").strip(),
        "세운 사건": f"{good_value} / {caution_value}".strip(" /"),
        "수입 강세 연도": decision_event_label("income_peak", "money_peak") or good_value,
        "재물 강세 연도": decision_event_label("money_peak", "asset_year") or good_value,
        "자산화 연도": decision_event_label("asset_year", "money_peak") or good_value,
        "채권·미수금 회수 연도": decision_event_label("receivables_recovery_year", "income_peak") or good_value,
        "공동자금 주의 연도": decision_event_label("shared_money_caution", "contract_caution") or caution_value,
        "계약·명의 주의 연도": decision_event_label("contract_caution", "shared_money_caution") or caution_value,
        "부채·보증 주의 연도": decision_event_label("debt_guarantee_caution", "shared_money_caution", "contract_caution") or caution_value,
        "가족재산 주의 연도": decision_event_label("family_asset_caution", "family_caution", "shared_money_caution") or caution_value,
        "재물 주의 연도": decision_event_label("contract_caution") or caution_value,
        "직업 상승 연도": decision_event_label("career_rise", "career_change") or good_value,
        "권한 상승 연도": decision_event_label("authority_year", "career_rise") or good_value,
        "보상 상승 연도": decision_event_label("compensation_rise", "career_rise", "authority_year") or good_value,
        "직업 분야 전환 연도": decision_event_label("career_domain_shift", "career_change") or transition_value,
        "직업 전환 연도": decision_event_label("career_change", "career_rise") or transition_value,
        "소속 변화 연도": decision_event_label("career_change", "career_domain_shift") or transition_value,
        "직업 부담 연도": decision_event_label("career_burden") or caution_value,
        "직업 독립 연도": decision_event_label("career_independence_year", "career_change", "career_domain_shift") or transition_value,
        "연애 강세 연도": decision_event_label("love_opening", "relationship_progress_year") or good_value,
        "새 인연 연도": decision_event_label("love_opening", "relationship_progress_year") or good_value,
        "관계 진전 연도": decision_event_label("relationship_progress_year", "love_opening") or good_value,
        "재회·정리 연도": decision_event_label("relationship_recovery_year", "love_caution") or transition_value,
        "이별·정리 연도": decision_event_label("separation_closure_year", "love_caution", "relationship_recovery_year") or caution_value,
        "관계 주의 연도": decision_event_label("love_caution") or caution_value,
        "주변 개입 주의 연도": decision_event_label("external_interference_caution", "love_caution") or caution_value,
        "혼인 결정 연도": decision_event_label("marriage_decision", "housing_preparation_year") or good_value,
        "주거·생활 준비 연도": decision_event_label("housing_preparation_year", "marriage_decision") or good_value,
        "부부 재정 연도": decision_event_label("couple_finance_year", "housing_preparation_year", "family_caution") or transition_value,
        "가족·주거 변동 연도": decision_event_label("family_caution", "marriage_decision") or transition_value,
        "자녀·양육 책임 연도": decision_event_label("child_rearing_year", "family_caution") or caution_value,
        "결혼 주의 연도": decision_event_label("family_caution", "child_rearing_year") or caution_value,
        "인생 전환 연도": transition_value,
        "말년 안정 연도": later_value,
        "대운 무대": str(timing_profile.get("decisiveAgeBands") or topic_value or "20세~79세").strip(),
        "세운 사건": f"{good_value} / {caution_value}".strip(" /"),
        "상승 연도": good_value,
        "주의 연도": caution_value,
        "전환 연도": transition_value,
        "회복 연도": recovery_value,
        "말년 안정": later_value,
        "과거 대조": past_value,
    }
    bodies = {
        "대운 구간": f"{value_by_title.get('대운 구간') or '20세~79세'} 구간에서 큰 변곡점이 갈립니다. 10년 단위로 직업, 재물, 관계의 강약이 달라집니다.",
        "대운 무대": f"10년 단위 운에서는 {topic_value}이 가장 선명합니다. 이 구간에서 생활 조건과 사회적 역할이 바뀝니다.",
        "세운 사건": f"{good_value or '상승 연도'} / {caution_value or '주의 연도'}. 상승 연도에는 성과가 잡히고, 주의 연도에는 책임과 손실이 드러납니다.",
        "상승 연도": f"{good_value or '상승 연도'}. 일, 돈, 관계 중 한 축에서 실제 성과가 잡히는 해입니다.",
        "수입 강세 연도": f"{value_by_title.get('수입 강세 연도') or '대표 연도 없음'}. 수입과 보상 조건이 선명해지는 해입니다.",
        "재물 강세 연도": f"{value_by_title.get('재물 강세 연도') or '재물 고점'}. 수입과 자산 사건이 함께 커지는 해입니다.",
        "자산화 연도": f"{value_by_title.get('자산화 연도') or '자산화 시기'}. 현금보다 명의, 지분, 장기 보유 자산이 중요해지는 해입니다.",
        "채권·미수금 회수 연도": f"{value_by_title.get('채권·미수금 회수 연도') or '대표 연도 없음'}. 받아야 할 돈과 지연된 보상을 회수하기 좋은 해입니다.",
        "공동자금 주의 연도": f"{value_by_title.get('공동자금 주의 연도') or '대표 연도 없음'}. 가족, 지인, 동업자와 묶인 돈에서 몫의 문제가 커지는 해입니다.",
        "계약·명의 주의 연도": f"{value_by_title.get('계약·명의 주의 연도') or '대표 연도 없음'}. 계약서, 명의, 지분이 곧 손익을 가르는 해입니다.",
        "부채·보증 주의 연도": f"{value_by_title.get('부채·보증 주의 연도') or '대표 연도 없음'}. 대여, 보증, 채무 인수에서 책임이 커지는 해입니다.",
        "가족재산 주의 연도": f"{value_by_title.get('가족재산 주의 연도') or '대표 연도 없음'}. 가족 자산과 자기 자산의 경계가 흔들리는 해입니다.",
        "재물 주의 연도": f"{value_by_title.get('재물 주의 연도') or '계약 주의 연도'}. 투자보다 계약, 명의, 보증을 먼저 봐야 하는 해입니다.",
        "직업 상승 연도": f"{value_by_title.get('직업 상승 연도') or '직업 상승 시기'}. 평가, 직책, 중요한 제안이 현실화되는 해입니다.",
        "권한 상승 연도": f"{value_by_title.get('권한 상승 연도') or '대표 연도 없음'}. 맡는 범위와 결정권이 함께 커지는 해입니다.",
        "보상 상승 연도": f"{value_by_title.get('보상 상승 연도') or '대표 연도 없음'}. 성과가 보상 기준으로 계산되는 해입니다.",
        "직업 분야 전환 연도": f"{value_by_title.get('직업 분야 전환 연도') or '대표 연도 없음'}. 산업, 전문 방향, 역할의 성격이 바뀌는 해입니다.",
        "직업 전환 연도": f"{value_by_title.get('직업 전환 연도') or '직업 전환기'}. 이직, 승진, 역할 변경, 독립 준비가 강한 해입니다.",
        "소속 변화 연도": f"{value_by_title.get('소속 변화 연도') or '대표 연도 없음'}. 회사, 부서, 팀, 고용 형태가 바뀌기 쉬운 해입니다.",
        "직업 부담 연도": f"{value_by_title.get('직업 부담 연도') or '대표 연도 없음'}. 책임 전가, 평가 손상, 과중한 업무를 조심해야 하는 해입니다.",
        "직업 독립 연도": f"{value_by_title.get('직업 독립 연도') or '대표 연도 없음'}. 자기 이름, 별도 거래처, 독립 수입원을 세우기 좋은 해입니다.",
        "연애 강세 연도": f"{value_by_title.get('연애 강세 연도') or '대표 연도 없음'}. 호감이 실제 만남으로 옮겨가기 쉬운 해입니다.",
        "새 인연 연도": f"{value_by_title.get('새 인연 연도') or '대표 연도 없음'}. 새로운 만남과 호감 형성이 뚜렷한 해입니다.",
        "관계 진전 연도": f"{value_by_title.get('관계 진전 연도') or '대표 연도 없음'}. 만남이 약속, 공개, 장기 관계로 굳어지는 해입니다.",
        "재회·정리 연도": f"{value_by_title.get('재회·정리 연도') or '대표 연도 없음'}. 과거 인연이 다시 올라오거나 감정의 결론이 나는 해입니다.",
        "이별·정리 연도": f"{value_by_title.get('이별·정리 연도') or '대표 연도 없음'}. 끌고 온 관계를 끝내거나 결론을 내기 쉬운 해입니다.",
        "관계 주의 연도": f"{value_by_title.get('관계 주의 연도') or '관계 주의 시기'}. 오해, 연락 단절, 자존심 충돌이 커지는 해입니다.",
        "주변 개입 주의 연도": f"{value_by_title.get('주변 개입 주의 연도') or '대표 연도 없음'}. 가족, 친구, 과거 인연의 말이 관계에 끼어드는 해입니다.",
        "혼인 결정 연도": f"{value_by_title.get('혼인 결정 연도') or '대표 연도 없음'}. 결혼 논의와 공식 약속이 현실로 굳어지는 해입니다.",
        "주거·생활 준비 연도": f"{value_by_title.get('주거·생활 준비 연도') or '대표 연도 없음'}. 집, 생활비, 역할 분담을 실제로 맞추는 해입니다.",
        "부부 재정 연도": f"{value_by_title.get('부부 재정 연도') or '대표 연도 없음'}. 생활비, 공동 자산, 각자 돈의 기준이 중요해지는 해입니다.",
        "가족·주거 변동 연도": f"{value_by_title.get('가족·주거 변동 연도') or '가족·주거 변동 시기'}. 이사, 독립, 가족 책임이 현실 문제로 올라오는 해입니다.",
        "자녀·양육 책임 연도": f"{value_by_title.get('자녀·양육 책임 연도') or '대표 연도 없음'}. 자녀, 돌봄, 교육비, 가족 지원 책임이 커지는 해입니다.",
        "결혼 주의 연도": f"{value_by_title.get('결혼 주의 연도') or '대표 연도 없음'}. 주거, 생활비, 배우자 가족 문제가 부담으로 올라오는 해입니다.",
        "인생 전환 연도": f"{transition_value or '전환 구간'}. 이직, 독립, 결혼, 이사처럼 삶의 방향을 바꾸는 선택이 강한 해입니다.",
        "주의 연도": f"{caution_value or '주의 연도'}. 금전, 직업, 관계 중 한 축에서 부담이 커지는 해입니다.",
        "회복 연도": f"{recovery_value or '상승 연도'}. 이전 손실과 정체를 정리하고 다시 올라서는 해입니다.",
        "말년 안정": f"{later_value}. 후반부에는 자산, 가족, 생활 기반이 안정의 중심으로 들어옵니다.",
        "말년 안정 연도": f"{later_value}. 후반부에는 자산, 가족, 생활 기반이 안정의 중심으로 들어옵니다.",
        "과거 대조": "과거의 큰 선택과 현재 운의 작용을 대조하면 정확도가 올라갑니다. 반복된 사건이 있는 해는 같은 영역을 다시 확인해야 합니다.",
    }
    cards: list[dict[str, Any]] = []
    for required in required_items:
        title = str(required.get("title") or "").strip()
        if not title:
            continue
        tone = "watch" if title in {"주의 연도", "재물 주의 연도", "관계 주의 연도"} else "strong" if title in {"상승 연도", "재물 강세 연도", "자산화 연도", "직업 상승 연도", "연애 강세 연도", "회복 연도", "말년 안정", "말년 안정 연도"} else "neutral"
        value = value_by_title.get(title) or "단독 연도 약함"
        cards.append(
            {
                "title": title,
                "grade": "주의" if tone == "watch" else "핵심",
                "value": value,
                "score": None,
                "tone": tone,
                "body": bodies.get(title, str(required.get("premium_output") or "")),
                "meaning": _premium_required_judgment_meaning("timing", title),
                "scene": _premium_required_judgment_scene("timing", title, tone),
                "basis": str(required.get("engine_basis") or ""),
            }
        )
    return cards


def _premium_required_judgment_cards(section: dict[str, Any]) -> list[dict[str, Any]]:
    contract = section.get("category_contract") if isinstance(section.get("category_contract"), dict) else {}
    required_items = [item for item in contract.get("required_judgments") or [] if isinstance(item, dict)]
    if not required_items:
        return []
    domain = _domain_key(section)
    if domain == "love" and "결혼" in str(section.get("heading") or ""):
        marriage_required = [
            {**item, "_judgment_domain": "marriage"}
            for item in premium_category_contract("marriage").get("required_judgments", [])
            if isinstance(item, dict)
        ]
        existing_titles = {str(item.get("title") or "") for item in required_items}
        required_items = [
            {**item, "_judgment_domain": "love"}
            for item in required_items
        ] + [
            item
            for item in marriage_required
            if str(item.get("title") or "") not in existing_titles
        ]
    if domain == "timing":
        return _premium_timing_required_judgment_cards(section, required_items)
    pool = _premium_required_judgment_pool(section)
    cards: list[dict[str, Any]] = []
    for required in required_items:
        title = str(required.get("title") or "").strip()
        if not title:
            continue
        judgment_domain = str(required.get("_judgment_domain") or domain)
        matched = _premium_required_match_item(section, required, pool)
        if title in PREMIUM_REQUIRED_WATCH_TITLES:
            watch_matched = _premium_required_watch_match(pool)
            if watch_matched:
                matched = watch_matched
        matched_score = (matched or {}).get("score")
        score = max(0, min(100, int(round(matched_score)))) if isinstance(matched_score, (int, float)) else None
        matched_tone = str((matched or {}).get("tone") or "")
        forced_watch = title in PREMIUM_REQUIRED_WATCH_TITLES
        tone = "watch" if forced_watch or matched_tone in {"watch", "risk"} or _premium_required_grade(score, tone=matched_tone) == "주의" else "strong" if isinstance(score, int) and score >= 70 else "neutral"
        grade = "주의" if forced_watch else _premium_required_grade(score, tone=tone)
        cards.append(
            {
                "title": title,
                "grade": grade,
                "value": _premium_required_timing_event_value(title, matched)
                or str((matched or {}).get("label") or "").strip(),
                "score": score,
                "tone": tone,
                "body": _premium_required_judgment_body(judgment_domain, title, score, matched),
                "meaning": _premium_required_judgment_meaning(judgment_domain, title),
                "scene": _premium_required_judgment_scene(judgment_domain, title, tone),
                "basis": str(required.get("engine_basis") or ""),
                "question": str(required.get("customer_question") or ""),
            }
        )
    return cards


def _attach_premium_required_judgment_cards(section: dict[str, Any]) -> dict[str, Any]:
    cards = _premium_required_judgment_cards(section)
    if not cards:
        return section
    enriched = dict(section)
    enriched["required_judgment_cards"] = cards
    return enriched


def _attach_timing_decision_events_to_section(
    section: dict[str, Any],
    timing_decision: dict[str, Any] | None,
    *,
    birth_year: int,
    current_year: int | None,
) -> dict[str, Any]:
    if str(section.get("domain") or "") != "timing" or not isinstance(timing_decision, dict):
        return section
    decision_events = _timing_decision_event_payloads(
        timing_decision,
        birth_year,
        current_year=current_year,
    )
    if not decision_events:
        return section
    enriched = dict(section)
    enriched["timing_events"] = _merge_timing_event_payloads(
        [item for item in enriched.get("timing_events") or [] if isinstance(item, dict)],
        decision_events,
    )
    timing_map = dict(enriched.get("timing_map") or {})
    good_additions = [event for event in decision_events if str(event.get("kind") or "") == "good"]
    caution_additions = [event for event in decision_events if str(event.get("kind") or "") == "caution"]
    timing_map["goodHighlights"] = _merge_timing_event_payloads(
        [item for item in timing_map.get("goodHighlights") or [] if isinstance(item, dict)],
        good_additions,
    )
    timing_map["cautionHighlights"] = _merge_timing_event_payloads(
        [item for item in timing_map.get("cautionHighlights") or [] if isinstance(item, dict)],
        caution_additions,
    )
    enriched["timing_map"] = timing_map
    return enriched


def _supplemental_premium_sections(
    normalized_sections: list[dict[str, Any]],
    chart_summary: dict[str, Any],
    premium_detail_sections: list[dict[str, Any]] | None = None,
    source_personality_profile: dict[str, Any] | None = None,
    source_reading_profile: dict[str, Any] | None = None,
    domain_decision_facets: dict[str, Any] | None = None,
    timing_decision_facets: dict[str, Any] | None = None,
    output_goal_coverage: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    money = _section_by_domain(normalized_sections, "money")
    career = _section_by_domain(normalized_sections, "career")
    love = _section_by_domain(normalized_sections, "love")
    marriage = _section_by_domain(normalized_sections, "marriage")
    top_sections = _ranked_domain_sections(normalized_sections, 2)
    top_pair = _domain_pair_label(top_sections)
    _life_theme, life_current = _life_theme_from_sections(top_sections)
    timing_action = _top_section_action(top_sections)
    timing_caution = _top_section_caution(top_sections)
    personality_lead, personality_narrative, personality_points = _personality_copy(
        top_sections,
        chart_summary,
        source_personality_profile,
    )
    personality_decision = _checkpoint_value(personality_points, "판단 기준", "판단 기준이 분명합니다.")
    personality_social = _checkpoint_value(personality_points, "대인 거리감", "사람을 대할 때 자신의 기준을 먼저 확인합니다.")
    personality_emotion = _checkpoint_value(personality_points, "감정 반응", "감정이 올라와도 상황을 확인한 뒤 표현합니다.")
    personality_pressure = _checkpoint_value(personality_points, "압박 대응") or _checkpoint_value(
        personality_points,
        "압박을 받을 때",
        "책임이 애매한 상황에서는 반응이 예민해집니다.",
    )
    personality_pace = _checkpoint_value(personality_points, "행동 속도", "판단 기준이 서면 바로 행동으로 옮깁니다.")
    personality_focus = _checkpoint_value(personality_points, "관심 몰입", "한 분야가 정해지면 오래 파고듭니다.")
    personality_profile_payload = _personality_profile_payload(chart_summary, personality_points)
    personality_section = _premium_section(
            "premium-personality",
            domain="personality",
            domain_label="성격",
            heading="성격",
            lead=personality_lead,
            narrative=personality_narrative,
            checkpoints=personality_points,
            detail_blocks=[
                _detail_block("판단 기준", personality_decision, [personality_lead]),
                _detail_block("대인 거리감", personality_social),
                _detail_block("감정 반응", personality_emotion),
                _detail_block("압박 대응", personality_pressure, tone="risk"),
                _detail_block("행동 속도", personality_pace),
                _detail_block("관심 몰입", personality_focus),
             ],
             topic_items=_topic_items_from_sections("personality", *normalized_sections),
             feature_axes=_personality_feature_axes_from_profile(personality_profile_payload),
     )
    personality_section["personality_profile"] = personality_profile_payload
    if source_personality_profile:
        personality_section["source_personality_profile"] = dict(source_personality_profile)
    sections = [
        personality_section,
        money
        or _premium_section(
            "premium-money",
            domain="money",
            domain_label="재물운",
            heading="재물 세부 운세",
            lead="재물 형성력이 강합니다.",
            narrative=_summary_for_card({"domain": "money"}),
            checkpoints=_premium_checkpoints({"domain": "money"}),
        ),
        career
        or _premium_section(
            "premium-career",
            domain="career",
            domain_label="직업운",
            heading="직업 세부 운세",
            lead="직업 성취력이 강합니다.",
            narrative=_summary_for_card({"domain": "career"}),
            checkpoints=_premium_checkpoints({"domain": "career"}),
        ),
        love
        or _premium_section(
            "premium-love",
            domain="love",
            domain_label="연애운",
            heading="연애 세부 운세",
            lead="연애는 상대를 고르는 기준과 관계를 오래 유지하는 힘이 핵심입니다.",
            narrative=_summary_for_card({"domain": "love"}),
            checkpoints=_premium_checkpoints({"domain": "love"}),
        ),
        marriage
        or _premium_section(
            "premium-marriage",
            domain="marriage",
            domain_label="결혼운",
            heading="결혼 세부 운세",
            lead="결혼은 배우자상, 생활 기준, 가족 책임, 부부 재정에서 결론이 드러납니다.",
            narrative=_summary_for_card({"domain": "marriage"}),
            checkpoints=_premium_checkpoints({"domain": "marriage"}),
        ),
        _premium_timing_section(chart_summary, normalized_sections, timing_action, timing_caution),
        _dynamic_life_stage_section(
            normalized_sections,
            chart_summary,
            top_pair=top_pair,
            life_current=life_current,
            timing_caution=timing_caution,
        ),
        _dynamic_honor_section(career),
        _dynamic_social_section(love, marriage, money),
    ]
    timing_rows = list(chart_summary.get("timingAnnualRows") or chart_summary.get("annualRows") or [])
    timing_birth_year = _birth_year_from_timing_rows(timing_rows) or 0
    timing_current_year = _current_year_from_timing_rows(timing_rows, chart_summary)
    def with_decision_payload(section: dict[str, Any]) -> dict[str, Any]:
        next_section = dict(section)
        if isinstance(domain_decision_facets, dict):
            next_section["domain_decision_facets"] = dict(domain_decision_facets)
        if isinstance(timing_decision_facets, dict):
            next_section["timing_decision_facets"] = dict(timing_decision_facets)
            next_section = _attach_timing_decision_events_to_section(
                next_section,
                timing_decision_facets,
                birth_year=timing_birth_year,
                current_year=timing_current_year,
            )
        if isinstance(output_goal_coverage, dict):
            next_section["output_goal_coverage"] = dict(output_goal_coverage)
        return next_section

    def prepare_visible_section(section: dict[str, Any]) -> dict[str, Any]:
        visible = _attach_premium_required_judgment_cards(
            _attach_premium_section_story_cards(
                _attach_premium_visual_profile(
                    _attach_premium_section_profile(
                        _attach_premium_category_contract(
                            _attach_premium_detail_sections(
                                _attach_source_reading_points(
                                    with_decision_payload(section),
                                    source_reading_profile,
                                ),
                                premium_detail_sections or [],
                            )
                        )
                    )
                )
            )
        )
        for internal_key in (
            "domain_decision_facets",
            "timing_decision_facets",
            "output_goal_coverage",
            "feature_axes",
        ):
            visible.pop(internal_key, None)
        return visible

    return [prepare_visible_section(section) for section in sections]


def _product_overview(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "종합운에서 먼저 볼 핵심 항목이 분명합니다."
    first = max(
        cards,
        key=lambda card: int(card.get("strength_score") or 0),
    )
    domain_label = str(first.get("title") or first.get("domain_label") or "핵심운")
    action = str(first.get("action_label") or "").rstrip(".")
    caution = str(first.get("caution_label") or "").rstrip(".")
    overview = f"가장 강한 운세는 {domain_label}입니다."
    if action:
        overview += f" {action}."
    if caution:
        overview += f" {_overview_caution_sentence(caution)}"
    return overview


def _overview_caution_sentence(caution: str) -> str:
    text = str(caution or "").strip().rstrip(".")
    if not text:
        return ""
    if text.endswith("변수"):
        return f"{text}가 큽니다."
    if any(marker in text for marker in ("주의", "불균형", "손실", "충돌", "압박", "과중", "과다", "차이", "약화", "장기화", "변수")):
        return f"{text}."
    return f"{text} 주의."


PREMIUM_SUMMARY_DOMAIN_FAMILY: dict[str, str] = {
    "money": "자산 형성",
    "career": "사회 평가",
    "honor": "사회 평가",
    "love": "관계 안정",
    "marriage": "관계 안정",
    "social": "관계 안정",
    "personality": "성격 중심",
    "life": "인생 구간",
}

PREMIUM_SUMMARY_FAMILY_DISPLAY_PRIORITY: dict[str, int] = {
    "자산 형성": 1,
    "사회 평가": 2,
    "관계 안정": 3,
    "성격 중심": 4,
    "인생 구간": 5,
}


def _premium_summary_display_priority(item: dict[str, Any] | None) -> int:
    if not item:
        return 99
    family = str(item.get("family") or "")
    if family in PREMIUM_SUMMARY_FAMILY_DISPLAY_PRIORITY:
        return PREMIUM_SUMMARY_FAMILY_DISPLAY_PRIORITY[family]
    return _premium_domain_priority(item.get("domain"))


def _premium_summary_strength_display_order(
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    strengths = [item for item in (primary, secondary) if item]
    if len(strengths) < 2:
        return strengths
    top_score = int(strengths[0].get("score") or 0)
    ordered = sorted(
        strengths,
        key=lambda item: (
            _premium_summary_display_priority(item),
            -int(item.get("score") or 0),
            _premium_label_priority(item.get("label")),
        ),
    )
    if ordered[0] is not strengths[0] and top_score - int(ordered[0].get("score") or 0) > 10:
        return strengths
    return ordered


def _premium_profile_summary(sections: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = _premium_summary_candidates(sections)
    strength_candidates = [
        item
        for item in candidates
        if item["domain"] not in {"personality", "life", "timing"}
    ]
    positive_strength_candidates = [
        item for item in strength_candidates if _premium_summary_strength_eligible(item)
    ] or strength_candidates
    primary = _pick_primary_summary_candidate(positive_strength_candidates)
    secondary = _pick_secondary_summary_candidate(positive_strength_candidates, primary)
    management = _pick_management_summary_candidate(strength_candidates)
    management = _premium_summary_management_with_money_anchor(
        strength_candidates,
        primary,
        secondary,
        management,
    )
    timing = _premium_summary_timing(sections)
    personality = _premium_summary_personality(sections)
    profile_type = _premium_profile_type(primary, secondary)
    headline = _premium_summary_headline(primary, secondary, management)
    summary = _premium_summary_body(primary, secondary, management)
    primary_copy = _premium_profile_panel_copy(
        str((primary or {}).get("domain") or ""),
        "primary",
        label="강점",
        title="강한 운세",
        caption="주요 강점",
    )
    management_copy = _premium_profile_panel_copy(
        str((management or {}).get("domain") or ""),
        "management",
        label="주의",
        title="주의점",
        caption="반드시 확인할 자리",
    )
    secondary_copy = _premium_profile_panel_copy(
        str((secondary or {}).get("domain") or ""),
        "secondary",
        label="강점",
        title="보조 강점",
        caption="두 번째 강점",
    )
    cards = [
        {
            "title": "성격 유형",
            "meta": "판단 기준과 감정 반응",
            "body": personality or "판단 기준이 분명합니다.",
            "detail": _premium_summary_personality_detail(sections),
        },
        {
            "title": primary_copy["title"],
            "meta": primary_copy["caption"],
            "body": _premium_summary_sentence(primary, role="primary") or "강한 운세가 분명합니다.",
            "detail": _premium_summary_card_detail(sections, primary, role="primary"),
        },
        {
            "title": management_copy["title"],
            "meta": management_copy["caption"],
            "body": _premium_summary_sentence(management, role="management") or "반드시 관리해야 할 지점이 있습니다.",
            "detail": _premium_summary_card_detail(sections, management, role="management"),
        },
        {
            "title": "인생 연도",
            "meta": "20세~79세 주요 연도",
            "body": _premium_timing_card_body(timing, "good"),
            "detail": _premium_timing_card_body(timing, "caution"),
        },
    ]
    if secondary and secondary is not primary:
        cards.insert(
            2,
            {
                "title": secondary_copy["title"],
                "meta": secondary_copy["caption"],
                "body": _premium_summary_sentence(secondary, role="secondary") or "보조 강점이 분명합니다.",
                "detail": _premium_summary_card_detail(sections, secondary, role="secondary"),
            },
        )
    profile_panels = _premium_profile_panels(
        sections,
        personality=personality,
        primary=primary,
        secondary=secondary,
        management=management,
        timing=timing,
    )
    return {
        "profile_type": profile_type,
        "headline": headline,
        "summary": summary,
        "primary": primary or {},
        "secondary": secondary or {},
        "management": management or {},
        "timing": timing,
        "profile_panels": profile_panels,
        "cards": cards,
    }


def _premium_summary_strength_eligible(item: dict[str, Any]) -> bool:
    label = str(item.get("label") or "")
    caption = str(item.get("caption") or "")
    tone = str(item.get("tone") or "")
    text = f"{label} {caption}"
    if tone in {"watch", "risk"}:
        return False
    blocked_markers = (
        "주의",
        "부적합",
        "갈등",
        "손실",
        "위기",
        "불균형",
        "부담",
        "약점",
    )
    return not any(marker in text for marker in blocked_markers)


def _premium_profile_panels(
    sections: list[dict[str, Any]],
    *,
    personality: str,
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    management: dict[str, Any] | None,
    timing: dict[str, str],
) -> list[dict[str, Any]]:
    """Build the premium profile summary as its own product contract."""

    personality_lead = _premium_profile_lead(personality, "판단 기준이 분명한 성격입니다.")
    personality_section = next(
        (
            section
            for section in sections
            if str(section.get("domain") or "") == "personality"
        ),
        {},
    )
    personality_profile = personality_section.get("section_profile")
    if not isinstance(personality_profile, dict):
        personality_profile = {}
    personality_payload = personality_section.get("personality_profile")
    if not isinstance(personality_payload, dict):
        personality_payload = {}
    if personality_payload:
        personality_lead = _personality_profile_intro(personality_payload, fallback=personality_lead)
    personality_value = str(
        personality_payload.get("title") or personality_profile.get("type") or "성격 요약"
    ).strip()
    personality_score = _personality_profile_score(personality_payload)
    panels: list[dict[str, Any]] = [
        {
            "panel_id": "premium_profile_personality",
            "role": "personality",
            "label": "성격",
            "title": "성격 유형",
            "caption": "성격과 판단 방식",
            "verdict": personality_lead,
            "detail": _premium_summary_personality_detail(sections),
            "domain": "personality",
            "domain_label": "성격",
            "metric_label": "성격 기준",
            "value": personality_value,
            "score": personality_score,
            "tone": "personality",
        },
        _premium_profile_candidate_panel(
            "primary",
            "강점",
            "강한 운세",
            "주요 강점",
            primary,
            sections,
        ),
        _premium_profile_candidate_panel(
            "secondary" if secondary else "primary",
            "강점",
            "보조 강점",
            "두 번째 강점",
            secondary or primary,
            sections,
        ),
        _premium_profile_candidate_panel(
            "management",
            "주의",
            "주의점",
            "반드시 확인할 자리",
            management,
            sections,
        ),
        {
            "panel_id": "premium_profile_timing",
            "role": "timing",
            "label": "연도",
            "title": "인생 연도",
            "caption": "20세~79세 주요 연도",
            "verdict": _premium_timing_card_body(timing, "good"),
            "detail": _premium_timing_card_body(timing, "caution"),
            "domain": "timing",
            "domain_label": "인생 주요 연도",
            "metric_label": "생애 구간",
            "value": "20세~79세",
            "score": None,
            "tone": "neutral",
        },
    ]
    return [panel for panel in panels if panel.get("title") and panel.get("verdict")]


def _premium_timing_card_body(timing: dict[str, str], kind: str) -> str:
    label = "상승 연도" if kind == "good" else "주의 연도"
    value = str(timing.get(kind) or "").strip()
    return f"{label}: {value}" if value else label


def _personality_profile_score(profile: dict[str, Any]) -> int | None:
    scores = [
        int(axis.get("score"))
        for axis in profile.get("axes") or []
        if isinstance(axis, dict) and isinstance(axis.get("score"), int)
    ]
    if not scores:
        return None
    usable = scores[:5]
    return max(0, min(100, round(sum(usable) / len(usable))))


def _premium_profile_lead(text: str, fallback: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return fallback
    first = cleaned.split(".", 1)[0].strip()
    if not first:
        return fallback
    return first + "."


def _premium_profile_panel_copy(
    domain: str,
    role: str,
    *,
    label: str,
    title: str,
    caption: str,
) -> dict[str, str]:
    if role == "management":
        copies = {
        "money": ("주의", "재물 주의점", "재물 관리 지점"),
            "career": ("주의", "직업 주의점", "경력 손실 지점"),
            "honor": ("주의", "명예 주의점", "평판 손상 지점"),
            "love": ("주의", "관계 주의점", "관계 불안 지점"),
            "marriage": ("주의", "결혼 주의점", "결혼 부담 지점"),
            "social": ("주의", "대인 주의점", "관계 부담 지점"),
            "life": ("주의", "생애 주의점", "전환기 부담 지점"),
        }
    else:
        copies = {
            "money": ("강점", "재물 강점", "자산 확대 지점"),
            "career": ("강점", "직업 강점", "평가 확보 지점"),
            "honor": ("강점", "명예 강점", "공식 인정 지점"),
            "love": ("강점", "관계 강점", "관계 지속 지점"),
            "marriage": ("강점", "결혼 강점", "생활 안정 지점"),
            "social": ("강점", "대인 강점", "신뢰 누적 지점"),
            "life": ("강점", "생애 강점", "생애 강세 구간"),
        }
    picked = copies.get(domain)
    if not picked:
        return {"label": label, "title": title, "caption": caption}
    picked_caption = picked[2]
    if role == "secondary" and domain in {"love", "marriage"}:
        picked_caption = f"{picked_caption} · 인생 연도"
    return {"label": picked[0], "title": picked[1], "caption": picked_caption}


def _premium_profile_candidate_panel(
    role: str,
    label: str,
    title: str,
    caption: str,
    item: dict[str, Any] | None,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    domain = str((item or {}).get("domain") or "")
    copy = _premium_profile_panel_copy(domain, role, label=label, title=title, caption=caption)
    score = item.get("score") if isinstance(item, dict) else None
    tone = "watch" if role == "management" else str((item or {}).get("tone") or "strong")
    if isinstance(score, int) and role == "management":
        tone = "watch" if score < 68 else "neutral"
    verdict = _premium_summary_sentence(item, role=role) if item else ""
    return {
        "panel_id": f"premium_profile_{role}",
        "role": role,
        "label": copy["label"],
        "title": copy["title"],
        "caption": copy["caption"],
        "verdict": verdict or ("반드시 관리해야 할 지점이 있습니다." if role == "management" else "강한 운세가 분명합니다."),
        "detail": _premium_summary_card_detail(sections, item, role=role),
        "domain": domain,
        "domain_label": str((item or {}).get("domain_label") or ""),
        "metric_label": str((item or {}).get("label") or ""),
        "value": str((item or {}).get("value") or (_score_value(score) if isinstance(score, int) else "")),
        "score": score if isinstance(score, int) else None,
        "tone": tone,
    }


def _premium_summary_candidates(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for section in sections:
        domain = str(section.get("domain") or "")
        if domain == "timing":
            continue
        domain_label = str(section.get("domain_label") or section.get("heading") or "")
        for item in _premium_summary_source_items(section):
            score = item.get("score")
            if not isinstance(score, int):
                continue
            label = _premium_sentence_axis_label(item.get("display_label") or item.get("label") or item.get("title") or "")
            value = str(item.get("value") or _score_value(score)).strip()
            caption = str(item.get("caption") or item.get("body") or item.get("definition") or "").strip()
            if not label:
                continue
            candidates.append(
                {
                    "domain": domain,
                    "domain_label": domain_label,
                    "family": PREMIUM_SUMMARY_DOMAIN_FAMILY.get(domain, domain_label),
                    "label": label,
                    "value": value,
                    "score": score,
                    "caption": caption,
                    "tone": str(item.get("tone") or _topic_tone_from_score(score)),
                }
            )
    return candidates


def _premium_summary_source_items(section: dict[str, Any]) -> list[dict[str, Any]]:
    profile = section.get("visual_profile") if isinstance(section.get("visual_profile"), dict) else {}
    visual_items = [
        {
            "label": item.get("label"),
            "value": item.get("value"),
            "caption": item.get("caption"),
            "score": item.get("score"),
            "tone": item.get("tone"),
        }
        for item in (profile or {}).get("items", [])
        if isinstance(item, dict)
    ]
    topic_items = [
        {
            "label": item.get("title"),
            "value": item.get("value"),
            "caption": item.get("body") or item.get("definition"),
            "score": item.get("score"),
            "tone": item.get("tone"),
        }
        for item in section.get("topic_items") or []
        if isinstance(item, dict)
    ]
    seen: set[tuple[str, int]] = set()
    merged: list[dict[str, Any]] = []
    for item in visual_items + topic_items:
        score = item.get("score")
        label = str(item.get("label") or "")
        if not isinstance(score, int) or not label:
            continue
        key = (label, score)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _pick_primary_summary_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    return sorted(candidates, key=_premium_strength_sort_key)[0]


def _pick_secondary_summary_candidate(
    candidates: list[dict[str, Any]],
    primary: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not candidates:
        return None
    primary_family = str((primary or {}).get("family") or "")
    primary_domain = str((primary or {}).get("domain") or "")
    pool = [
        item
        for item in candidates
        if item is not primary and item.get("domain") != primary_domain and item.get("family") != primary_family
    ]
    if not pool:
        pool = [item for item in candidates if item is not primary and item.get("domain") != primary_domain]
    if not pool:
        pool = [item for item in candidates if item is not primary]
    return sorted(pool, key=_premium_strength_sort_key)[0] if pool else None


def _pick_management_summary_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    watch = [
        item
        for item in candidates
        if int(item.get("score") or 0) <= 55 or str(item.get("tone") or "") in {"watch", "risk"}
    ]
    pool = watch or candidates
    return sorted(pool, key=lambda item: (int(item.get("score") or 0), _premium_domain_priority(item.get("domain"))))[0]


def _premium_summary_management_with_money_anchor(
    candidates: list[dict[str, Any]],
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    management: dict[str, Any] | None,
) -> dict[str, Any] | None:
    def money_loss_anchor(item: dict[str, Any]) -> bool:
        text = " ".join(
            str(item.get(key) or "")
            for key in ("label", "caption", "value")
        )
        return (
            "공동" in text
            or "명의와 지분" in text
            or "명의" in text and "지분" in text
        )

    money_candidates = [
        item
        for item in candidates
        if str(item.get("domain") or "") == "money"
    ]
    money_anchor_candidates = sorted(
        [item for item in money_candidates if money_loss_anchor(item)],
        key=lambda item: (
            int(item.get("score") or 0),
            _premium_label_priority(item.get("label")),
            str(item.get("label") or ""),
        ),
    )
    if money_anchor_candidates and int(money_anchor_candidates[0].get("score") or 0) <= 60:
        return money_anchor_candidates[0]

    selected_domains = {
        str((item or {}).get("domain") or "")
        for item in (primary, secondary, management)
        if item
    }
    if "money" in selected_domains:
        return management
    strength_domains = {
        str((item or {}).get("domain") or "")
        for item in (primary, secondary)
        if item
    }
    management_domain = str((management or {}).get("domain") or "")
    if management_domain and management_domain not in strength_domains:
        return management
    if not money_candidates:
        return management
    money_watch = sorted(
        money_candidates,
        key=lambda item: (
            int(item.get("score") or 0),
            _premium_label_priority(item.get("label")),
            str(item.get("label") or ""),
        ),
    )[0]
    if int(money_watch.get("score") or 0) <= 60:
        return money_watch
    return management


def _premium_strength_sort_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        -int(item.get("score") or 0),
        _premium_domain_priority(item.get("domain")),
        _premium_label_priority(item.get("label")),
        str(item.get("label") or ""),
    )


def _premium_domain_priority(domain: Any) -> int:
    order = {
        "money": 1,
        "career": 2,
        "honor": 3,
        "love": 4,
        "marriage": 5,
        "social": 6,
        "personality": 7,
        "life": 8,
    }
    return order.get(str(domain or ""), 99)


def _premium_label_priority(label: Any) -> int:
    order = {
        "관계 안정성": 1,
        "관계 지속력": 1,
        "결혼 안정성": 2,
        "사회적 인정도": 3,
        "업무 평가력": 4,
        "평가 확보력": 4,
        "직업 성취력": 5,
        "성과 구현력": 5,
        "타고난 재물의 그릇": 5,
        "축재력": 6,
        "자산 축적력": 6,
        "재산으로 굳어지는 힘": 6,
        "재물 발생력": 7,
        "재물 형성력": 7,
        "재물이 들어오는 길": 7,
        "수입 창출력": 7,
        "재주 수익화": 8,
        "결혼 현실화": 9,
        "결혼으로 이어지는 현실성": 9,
    }
    return order.get(str(label or ""), 99)


def _premium_profile_type(primary: dict[str, Any] | None, secondary: dict[str, Any] | None) -> str:
    families: list[str] = []
    for item in (primary, secondary):
        family = str((item or {}).get("family") or "").strip()
        if family and family not in families:
            families.append(family)
    if not families:
        return "종합 균형형"
    families = sorted(
        families,
        key=lambda family: PREMIUM_SUMMARY_FAMILY_DISPLAY_PRIORITY.get(family, 99),
    )
    return "·".join(families[:2]) + "형"


def _premium_summary_headline(
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    management: dict[str, Any] | None,
) -> str:
    if not primary:
        return "강한 운과 관리 지점이 분명합니다."
    pair_sentence = _premium_summary_domain_pair_sentence(primary, secondary, management).rstrip(".")
    parts = [pair_sentence] if pair_sentence else []
    parts.extend([
        _premium_summary_headline_clause(item, role="primary" if index == 0 else "secondary")
        for index, item in enumerate(_premium_summary_strength_display_order(primary, secondary))
    ])
    if management:
        parts.append(_premium_summary_headline_clause(management, role="management"))
    return ". ".join(parts) + "."


def _premium_summary_domain_pair_sentence(
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    management: dict[str, Any] | None = None,
) -> str:
    domains = {str((item or {}).get("domain") or "") for item in (primary, secondary, management)}
    if {"money", "career"}.issubset(domains):
        return "재물운과 직업운이 같은 자리에서 드러납니다."
    if domains & {"love", "marriage"} and "money" in domains:
        return "돈과 관계 문제가 같은 자리에서 움직입니다."
    if domains & {"love", "marriage"} and "career" in domains:
        return "직업 선택과 관계 선택이 서로 영향을 줍니다."
    return ""


def _premium_summary_body(
    primary: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
    management: dict[str, Any] | None,
) -> str:
    sentences: list[str] = []
    pair_sentence = _premium_summary_domain_pair_sentence(primary, secondary, management)
    if pair_sentence:
        sentences.append(pair_sentence)
    for index, item in enumerate(_premium_summary_strength_display_order(primary, secondary)):
        sentences.append(_premium_summary_sentence(item, role="primary" if index == 0 else "secondary") + ".")
    if management:
        sentences.append(_premium_summary_sentence(management, role="management") + ".")
    return " ".join(sentence for sentence in sentences if sentence)


def _premium_summary_headline_clause(item: dict[str, Any] | None, *, role: str) -> str:
    if not item:
        return ""
    domain = str(item.get("domain") or "")
    label = str(item.get("label") or "")
    is_management = role == "management"
    caption_verdict = _premium_summary_caption_verdict(item, role=role)
    if caption_verdict:
        return caption_verdict
    if domain in {"love", "marriage"}:
        if is_management:
            return "관계는 생활 문제에서 부담이 먼저 남습니다"
        if "관계 안정" in label or "결혼 안정" in label:
            return "관계는 깊은 신뢰로 오래 남습니다"
        if "결혼" in label:
            return "결혼 이야기가 현실로 옮겨집니다"
        return "관계는 짧은 호감보다 깊은 신뢰로 남습니다"
    if domain == "money":
        if is_management:
            caption = str(item.get("caption") or "")
            if "공동" in label or "사람" in label or "명의" in caption or "가까운 사람" in caption:
                return "다만 가까운 금전 관계에서는 명의와 지분이 상대 쪽으로 기울기 쉽습니다"
            if "지출" in label:
                return "다만 반복 지출이 자산 형성을 깎아냅니다"
            if "계약" in label or "문서" in label:
                return "다만 계약 문서가 허술하면 받을 몫이 줄어듭니다"
            return "다만 돈의 귀속이 불분명하면 실제 몫이 줄어듭니다"
        if "축재" in label:
            return "수입이 자산으로 남는 재물운입니다"
        if "수입" in label:
            return "성과가 보수와 계약금으로 확정됩니다"
        return "수입과 자산을 키우는 재물운입니다"
    if domain in {"career", "honor"}:
        if is_management:
            return "다만 결정권 없는 책임은 경력의 흠으로 남습니다"
        if "평가" in label or "인정" in label or "평판" in label:
            return "일의 결과가 이름과 평판으로 남습니다"
        if "전문" in label:
            return "전문성으로 평가받는 사주입니다"
        if "독립" in label:
            return "전문성이 경력의 단가와 협상력을 만듭니다"
        return "일에서 만든 결과가 이름과 평판으로 남습니다"
    if domain == "social":
        if is_management:
            return "다만 가까운 관계의 부탁이 책임으로 넘어옵니다"
        return "신뢰가 오래 남고 소개와 도움으로 이어집니다"
    return _premium_summary_sentence(item, role=role)


def _premium_summary_sentence(item: dict[str, Any] | None, *, role: str) -> str:
    if not item:
        return ""
    domain = str(item.get("domain") or "")
    label = str(item.get("label") or "")
    caption = str(item.get("caption") or "").strip().rstrip(".")
    is_management = role == "management"
    caption_verdict = _premium_summary_caption_verdict(item, role=role)
    if caption_verdict:
        return caption_verdict
    if domain in {"love", "marriage"}:
        if "관계 안정" in label or "관계 지속" in label or "결혼 안정" in label:
            return "결혼 이야기가 현실로 옮겨집니다" if not is_management else "관계가 안정되어도 생활 기준이 어긋나면 부담이 남습니다"
        if "결혼 현실" in label:
            return "연애가 공식적인 약속으로 옮겨집니다" if not is_management else "생활 기준이 덜 맞은 결혼은 이후 부담으로 남습니다"
        if "표현" in label:
            return "표현의 분명함이 관계의 진전 속도를 가릅니다"
        return "관계가 깊어지면 약속과 생활 기준이 곧 결혼 문제로 이어집니다" if not is_management else "감정이 깊어도 생활 기준이 어긋나면 관계의 부담이 남습니다"
    if domain == "money":
        caption = str(item.get("caption") or "")
        if is_management and ("사람" in label or "공동" in label or "명의" in caption or "가까운 사람" in caption):
            return "가까운 금전 관계에서는 명의와 지분이 상대 쪽으로 기울기 쉽습니다"
        if is_management and ("계약" in label or "문서" in label):
            return "계약 조건이 허술하면 받을 돈이 늦어지거나 줄어듭니다"
        if is_management and ("지출" in label):
            return "반복 지출이 늘어나면 자산으로 남을 돈이 줄어듭니다"
        if is_management:
            return "돈의 귀속이 불분명하면 실제로 남는 몫이 줄어듭니다"
        if "축재" in label:
            return "수입이 소비로 흩어지지 않고 소유 자산으로 남습니다" if not is_management else "수입이 자산으로 굳기 전에 관계 비용과 생활비가 먼저 늘어납니다"
        if "수입" in label:
            return "일의 성과가 보수와 계약금으로 확정됩니다" if not is_management else "수입 조건이 흐리면 받을 몫이 줄어듭니다"
        if "공동" in label:
            return "공동 자금은 명의와 몫이 분명할 때 재산으로 남습니다" if not is_management else "가까운 금전 관계에서는 명의와 지분이 상대 쪽으로 기울기 쉽습니다"
        if "계약" in label or "문서" in label:
            return "계약서가 곧 재물의 안전장치가 됩니다" if not is_management else "계약 조건을 소홀히 하면 수령액이 늦어지거나 줄어듭니다"
        return "일의 대가가 한 번의 수입으로 끝나지 않고 재산 기반으로 남습니다"
    if domain in {"career", "honor"}:
        if "평가" in label or "인정" in label:
            return "일에서 만든 결과가 공식 평가로 남습니다" if not is_management else "평가 기준이 흐린 자리에서는 성과가 제대로 남지 않습니다"
        if "전문" in label:
            return "전문 분야가 분명할수록 직함과 평판이 함께 따라옵니다"
        if "독립" in label:
            return "전문성이 경력의 단가와 협상력을 만듭니다"
        if "권한" in label or "책임" in label:
            return "책임과 권한이 맞물릴 때 직업적 성취가 본인 이력으로 남습니다" if not is_management else "결정권 없는 책임은 경력의 흠으로 남습니다"
        if "조직" in label:
            return "조직 안에서는 책임 있는 자리를 맡을수록 평가가 올라갑니다"
        return "일에서 만든 결과가 이름과 평판으로 남습니다"
    if domain == "social":
        if "관계 지속" in label:
            return "한 번 맺은 신뢰 관계가 오래 갑니다" if not is_management else "가까운 관계일수록 부탁이 책임으로 넘어옵니다"
        if "도움" in label:
            return "조력은 말보다 실질적인 지원을 하는 사람에게서 들어옵니다"
        return "사람을 무리하게 넓히기보다 필요한 사람과 오래 가는 쪽입니다"
    return caption or f"{item.get('domain_label') or '운세'}에서는 {label}이 가장 강합니다"


def _premium_candidate_display(item: dict[str, Any] | None) -> str:
    if not item:
        return ""
    label = str(item.get("label") or "")
    value = str(item.get("value") or "")
    domain_label = str(item.get("domain_label") or "")
    point = f"{label} {value}".strip()
    return f"{domain_label} · {point}" if domain_label else point


def _premium_summary_personality_detail(sections: list[dict[str, Any]]) -> str:
    personality = _section_by_domain(sections, "personality")
    if not personality:
        return ""
    checkpoints = list(personality.get("checkpoints") or [])
    emotion = _checkpoint_value(checkpoints, "감정 반응") or _checkpoint_value(checkpoints, "감정 처리")
    pace = _checkpoint_value(checkpoints, "행동 속도") or _checkpoint_value(checkpoints, "실행 방식")
    focus = _checkpoint_value(checkpoints, "관심 몰입") or _checkpoint_value(checkpoints, "몰입 방향")
    return _join_distinct_summary_sentences(
        _first_profile_sentence(_strip_profile_summary_prefix(emotion)),
        _first_profile_sentence(_strip_profile_summary_prefix(pace)),
        _first_profile_sentence(_strip_profile_summary_prefix(focus)),
        limit=3,
    )


def _premium_summary_positive_detail(item: dict[str, Any] | None) -> str:
    if not item:
        return ""
    domain = str(item.get("domain") or "")
    label = str(item.get("label") or "")
    if domain == "money":
        if "수입" in label:
            return "성과가 보수, 계약금, 단가로 확정됩니다."
        if "축재" in label or "자산" in label:
            return "수입이 소비로 흩어지지 않고 소유권이 남는 자산으로 전환됩니다."
        if "계약" in label or "문서" in label:
            return "금전 관계를 문서와 기준으로 정리할수록 손실 가능성이 줄어듭니다."
        if "공동" in label:
            return "공동 자금은 명의와 몫이 분명할 때 실제 재산으로 남습니다."
        return "수입이 한 번의 보수에 그치지 않고 자산 형성으로 이어집니다."
    if domain == "career":
        if "전문" not in label and "독립" not in label:
            return "책임과 권한이 맞물릴 때 직업적 성취가 본인 이력으로 남습니다."
        if "평가" in label or "인정" in label:
            return "맡은 일이 기록과 평판으로 남아 다음 직책의 근거가 됩니다."
        if "조직" in label or "자리" in label:
            return "공식 평가가 직책 상승과 사회적 인정으로 이어집니다."
        if "전문" in label:
            return "공식 평가가 직책 상승과 사회적 인정으로 이어집니다."
        if "독립" in label:
            return "전문성이 쌓일수록 경력의 단가와 협상력이 커집니다."
        return "책임과 권한이 맞물릴 때 직업적 성취가 본인 이력으로 남습니다."
    if domain in {"love", "marriage"}:
        if "결혼" in label or "생활" in label:
            return "관계가 감정에만 머물지 않고 생활 안정으로 이어집니다."
        return "감정이 깊어질수록 관계를 오래 유지하려는 태도가 강해집니다."
    if domain == "honor":
        return "공식적인 자리에서 이름과 역할이 분명해질수록 평판이 강해집니다."
    if domain == "social":
        return "한 번 얻은 신뢰가 오래 남아 다음 제안으로 돌아옵니다."
    return ""


def _premium_summary_card_detail(
    sections: list[dict[str, Any]],
    item: dict[str, Any] | None,
    *,
    role: str,
) -> str:
    if not item:
        return ""
    caption = str(item.get("caption") or "").strip().rstrip(".")
    domain = str(item.get("domain") or "")
    section = _section_by_domain(sections, domain)
    detail = _premium_summary_detail_from_section(section, item=item, role=role)
    if role != "management" and domain in {"money", "career", "honor", "social", "love", "marriage"}:
        story = _premium_summary_story_from_section(section, item=item, role=role)
        positive = _premium_summary_positive_detail(item)
        return _join_distinct_summary_sentences(caption, positive, story, detail, limit=3)
    if role == "management" and domain == "money":
        label = str(item.get("label") or "")
        caption_text = str(item.get("caption") or "")
        if any(marker in f"{label} {caption_text}" for marker in ("공동", "사람", "명의", "지분")):
            ownership_warning = "명의를 빌려주는 돈은 당신에게 불리하게 돌아오기 쉽고, 부동산을 마련할 때 명의와 자금 출처가 문제가 됩니다."
            return _join_distinct_summary_sentences(caption, ownership_warning, detail, limit=3)
    return _join_distinct_summary_sentences(caption, detail, limit=3)


def _premium_summary_detail_from_section(
    section: dict[str, Any] | None,
    *,
    item: dict[str, Any] | None,
    role: str,
) -> str:
    if not section:
        return ""
    details = [detail for detail in section.get("premium_details") or [] if isinstance(detail, dict)]
    if role == "management":
        details = _premium_summary_management_details(details, item)
        if not details:
            return _premium_summary_management_fallback(item)
    else:
        favorable_details = [
            detail
            for detail in details
            if str(detail.get("level") or "") not in {"risk", "watch"} and not _premium_story_is_watch(detail)
        ]
        details = favorable_details or details
    details = sorted(
        enumerate(details),
        key=lambda indexed: (-_premium_summary_detail_match_score(indexed[1], item), indexed[0]),
    )
    ordered_details = [detail for _index, detail in details]
    for detail in ordered_details:
        judgment = str(detail.get("judgment") or "").strip().rstrip(".")
        scenes = [
            str(scene).strip().rstrip(".")
            for scene in detail.get("event_scenes") or []
            if str(scene or "").strip()
        ]
        if judgment and scenes:
            return f"{judgment}. {scenes[0]}."
        if judgment:
            return f"{judgment}."
        if scenes:
            return f"{scenes[0]}."
    return ""


def _premium_summary_story_from_section(
    section: dict[str, Any] | None,
    *,
    item: dict[str, Any] | None,
    role: str,
) -> str:
    if not section or role == "management":
        return ""
    cards = [card for card in section.get("section_story_cards") or [] if isinstance(card, dict)]
    if not cards:
        return ""
    cards = [
        card
        for card in cards
        if str(card.get("tone") or "") not in {"watch", "risk"} and not _premium_story_is_watch(card)
    ] or cards
    ranked = sorted(
        enumerate(cards),
        key=lambda indexed: (-_premium_summary_story_match_score(indexed[1], item), indexed[0]),
    )
    for _index, card in ranked:
        body = _premium_story_sentence(card.get("body"), max_sentences=2).strip()
        if body:
            return body
    return ""


def _premium_summary_management_details(
    details: list[dict[str, Any]],
    item: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    label = str((item or {}).get("label") or "")
    domain = str((item or {}).get("domain") or "")
    if domain != "money":
        risk_details = [
            detail
            for detail in details
            if _premium_summary_detail_is_watch_like(detail)
        ]
        return risk_details or details
    allowed = [
        detail
        for detail in details
        if _premium_money_management_detail_matches(label, detail)
    ]
    watch_allowed = [
        detail
        for detail in allowed
        if _premium_summary_detail_is_watch_like(detail)
    ]
    return watch_allowed or allowed


def _premium_summary_detail_is_watch_like(detail: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(detail.get("title") or ""),
            str(detail.get("judgment") or ""),
            " ".join(str(scene) for scene in detail.get("event_scenes") or []),
            " ".join(str(target) for target in detail.get("caution_targets") or []),
        ]
    )
    return any(
        word in text
        for word in (
            "손실",
            "부담",
            "주의",
            "불균형",
            "흔들",
            "지연",
            "회수",
            "권리 주장",
            "책임",
        )
    )


def _premium_money_management_detail_matches(label: str, detail: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(detail.get("title") or ""),
            str(detail.get("judgment") or ""),
            " ".join(str(scene) for scene in detail.get("event_scenes") or []),
            " ".join(str(target) for target in detail.get("caution_targets") or []),
        ]
    )
    if "공동" in label or "공동재" in label or "사람" in label:
        return any(word in text for word in ("배우자", "가족", "공동 명의", "보증", "명의 대여", "권리 주장"))
    if "계약" in label or "문서" in label:
        return any(word in text for word in ("계약", "약속", "증빙", "잔금", "수수료", "환불", "회수"))
    if "수입" in label or "보상" in label:
        return any(word in text for word in ("보상", "성과급", "수익 배분", "저작권", "급여", "몫"))
    if "축재" in label or "자산" in label:
        return any(word in text for word in ("명의", "권리", "투자", "회수", "소유권", "단기", "지분"))
        if "지출" in label:
            return any(word in text for word in ("고정비", "비용", "대출", "지출", "확장", "체면"))
    return _premium_summary_detail_is_watch_like(detail)


def _premium_summary_caption_verdict(item: dict[str, Any] | None, *, role: str) -> str:
    if not item or role == "management":
        return ""
    caption = _premium_story_sentence(item.get("caption"), max_sentences=1).strip().rstrip(".")
    if not caption:
        return ""
    if _premium_text_reads_as_watch(caption) or _premium_story_body_has_clear_caution(caption):
        return ""
    if len(caption) > 48:
        return ""
    product_markers = (
        "보수",
        "수입",
        "자산",
        "재산",
        "매출",
        "계약금",
        "평가",
        "직책",
        "평판",
        "전문",
        "결혼",
        "생활",
        "인연",
        "관계",
        "신뢰",
        "공식",
        "권한",
        "성취",
        "유지",
        "남",
        "커집",
        "이어",
        "넘어",
        "확정",
        "전환",
    )
    if not any(marker in caption for marker in product_markers):
        return ""
    domain = str((item or {}).get("domain") or "")
    label = str((item or {}).get("label") or "")
    if domain == "career":
        if "전문" in label:
            return "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다"
        if "독립" in label:
            return "한 분야의 전문성이 경력의 단가와 협상력을 만듭니다"
        if "평가" in label or "인정" in label or "평판" in label:
            return "일에서 만든 결과가 이름과 평판으로 남습니다"
        if "조직" in label:
            return "조직 안에서 역할이 분명할 때 자기 자리가 생깁니다"
        if "권한" in label or "책임" in label:
            return "책임과 권한이 맞물릴 때 직업적 성취가 본인 이력으로 남습니다"
    if domain == "love":
        if "결혼" in label:
            return "관계가 깊어지면 결혼 이야기가 현실로 옮겨집니다"
        if "관계" in label:
            return "결혼 이야기가 현실로 옮겨집니다"
        if "표현" in label:
            return "좋아하는 마음이 말과 행동으로 분명히 전달됩니다"
    if domain == "money":
        if "자산" in label or "축재" in label or "재산" in label:
            return "수입이 소유권 있는 자산으로 남는 재물운입니다"
        if "수익" in label or "수입" in label or "재물이 들어오는 길" in label:
            return "성과가 실제 보수로 확정되는 재물운입니다"
    if (
        domain == "money"
        and any(marker in label for marker in ("수익", "수입", "재물이 들어오는 길", "성과 수익화"))
        and caption == "성과가 보수로 확정됩니다"
    ):
        return "성과가 실제 보수로 확정되는 재물운입니다"
    return caption


def _premium_summary_management_fallback(item: dict[str, Any] | None) -> str:
    domain = str((item or {}).get("domain") or "")
    label = str((item or {}).get("label") or "")
    if domain == "money":
        if "공동" in label or "공동재" in label or "사람" in label:
            return "처음의 호의가 나중에는 권리 주장으로 바뀝니다. 명의를 빌려주는 돈은 당신에게 불리하게 돌아오기 쉽습니다."
        if "계약" in label or "문서" in label:
            return "계약서에 빠진 조건은 결국 수령액을 줄입니다. 잔금, 수수료, 환불 조건은 반드시 기록으로 남겨야 합니다."
        if "수입" in label or "보상" in label:
            return "일한 양보다 보상 기준이 늦게 정해지면 당신 몫이 줄어듭니다. 성과급, 저작권, 수익 배분은 처음부터 따로 확인해야 합니다."
        if "축재" in label or "자산" in label:
            return "수입이 커져도 권리가 분명하지 않은 자산에는 재물이 오래 남지 않습니다. 명의와 회수 조건이 약하면 재산이 묶입니다."
        if "지출" in label:
            return "고정비와 체면 비용이 늘어나면 자산 형성이 늦어집니다. 한번 늘어난 비용은 쉽게 줄어들지 않습니다."
        return "수입이 생겨도 권리와 귀속이 분명하지 않으면 실질 몫이 줄어듭니다."
    if domain in {"career", "honor"}:
        return "책임은 늘지만 결정권이 작으면 성과가 온전히 남지 않습니다. 직함보다 권한과 평가 기준을 먼저 확인해야 합니다."
    if domain in {"love", "marriage", "social"}:
        return "가까운 관계일수록 부탁과 책임의 선이 흐려질 수 있습니다. 감정보다 약속의 범위를 먼저 분명히 해야 합니다."
    return ""


def _premium_summary_story_match_score(card: dict[str, Any], item: dict[str, Any] | None) -> int:
    label = str((item or {}).get("label") or "")
    caption = str((item or {}).get("caption") or "")
    haystack = " ".join(
        [
            str(card.get("label") or ""),
            str(card.get("title") or ""),
            str(card.get("body") or ""),
        ]
    )
    score = 0
    if label and label in haystack:
        score += 80
    compact_label = _compact_match_key(label)
    compact_haystack = _compact_match_key(haystack)
    if compact_label and compact_label in compact_haystack:
        score += 60
    if caption:
        first = caption.split(".", 1)[0].strip()
        if first and first in haystack:
            score += 30
    keyword_groups: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
        (("재물", "수입", "보수", "들어오는", "길"), ("수입", "보수", "성과급", "계약금", "매출", "대가")),
        (("축재", "자산", "재산"), ("자산", "재산", "부동산", "지분", "소유권", "예치")),
        (("재주", "수익", "기술"), ("기술", "콘텐츠", "서비스", "결과물", "매출", "강의")),
        (("공동", "자금", "명의"), ("공동", "명의", "지분", "권리", "가족", "배우자")),
        (("계약", "문서", "안정"), ("계약", "문서", "지급일", "수령액", "정산", "증빙")),
        (("전문", "평가", "직업", "성취"), ("전문", "평가", "직책", "평판", "경력", "성취")),
        (("권한", "책임"), ("권한", "책임", "결정권", "경력", "흠")),
        (("결혼", "관계", "애정"), ("결혼", "관계", "약속", "생활", "표현", "호감")),
    ]
    joined_label = f"{label} {caption}"
    for label_words, card_words in keyword_groups:
        if any(word in joined_label for word in label_words):
            score += sum(10 for word in card_words if word in haystack)
    return score


def _premium_summary_detail_match_score(detail: dict[str, Any], item: dict[str, Any] | None) -> int:
    label = str((item or {}).get("label") or "")
    caption = str((item or {}).get("caption") or "")
    domain = str((item or {}).get("domain") or "")
    haystack = " ".join(
        [
            str(detail.get("title") or ""),
            str(detail.get("judgment") or ""),
            " ".join(str(scene) for scene in detail.get("event_scenes") or []),
            " ".join(str(target) for target in detail.get("caution_targets") or []),
        ]
    )
    keyword_groups: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
        (("재물", "들어오는", "길"), ("수입", "보수", "성과", "성과급", "계약금", "매출", "대가")),
        (("공동", "자금", "몫", "사람"), ("공동", "가까운", "배우자", "가족", "명의", "몫", "권리", "섞")),
        (("계약", "문서", "안정"), ("계약", "문서", "정산", "지급", "수수료", "증빙")),
        (("축재", "자산"), ("자산", "부동산", "현금", "예금", "지분", "소유권")),
        (("수입", "창출", "재주", "수익"), ("수입", "수익", "기술", "결과물", "강의", "제작물")),
        (("평가", "인정", "명예", "평판"), ("평가", "인정", "평판", "직책", "공식", "이름")),
        (("관계", "결혼", "안정"), ("관계", "결혼", "공식화", "생활", "배우자", "약속")),
        (("조직", "권한", "책임"), ("조직", "권한", "책임", "결정권", "직무", "관리자")),
    ]
    score = 0
    label_basis = f"{label} {caption}"
    for label_words, detail_words in keyword_groups:
        if any(word in label_basis for word in label_words):
            score += sum(10 for word in detail_words if word in haystack)
    if domain and domain == str(detail.get("domain") or domain):
        score += 1
    return score


def _join_short_summary_parts(*parts: str) -> str:
    cleaned: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = str(part or "").strip()
        if not text:
            continue
        text = re.sub(r"\s+", " ", text).strip()
        if not text.endswith((".", "!", "?")):
            text += "."
        if text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return " ".join(cleaned[:2])


def _join_distinct_summary_sentences(*parts: str, limit: int = 3) -> str:
    cleaned: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = re.sub(r"\s+", " ", str(part or "").strip())
        if not text:
            continue
        fragments = [
            fragment.strip()
            for fragment in re.split(r"(?<=[.!?])\s+", text)
            if fragment.strip()
        ] or [text]
        for fragment in fragments:
            if not fragment.endswith((".", "!", "?")):
                fragment += "."
            key = re.sub(r"[\s.!?]+", "", fragment)
            if not key or key in seen:
                continue
            seen.add(key)
            cleaned.append(fragment)
            if len(cleaned) >= limit:
                return " ".join(cleaned)
    return " ".join(cleaned)


def _strip_profile_summary_prefix(value: str) -> str:
    text = str(value or "").strip()
    return re.sub(r"^[가-힣A-Za-z0-9·\s]+형\s*[-–]\s*", "", text).strip()


def _premium_summary_timing(sections: list[dict[str, Any]]) -> dict[str, str]:
    timing = next((section for section in sections if str(section.get("domain") or "") == "timing"), None)
    if not timing:
        return {}
    timing_map = timing.get("timing_map") if isinstance(timing.get("timing_map"), dict) else {}
    events = [event for event in timing.get("timing_events") or [] if isinstance(event, dict)]
    good_events = [
        event for event in timing_map.get("goodHighlights") or [] if isinstance(event, dict)
    ] or [event for event in events if event.get("kind") == "good"]
    caution_events = [
        event for event in timing_map.get("cautionHighlights") or [] if isinstance(event, dict)
    ] or [event for event in events if event.get("kind") == "caution"]
    good_source = sorted(good_events[:3], key=lambda event: int(event.get("year") or 0))
    caution_source = sorted(caution_events[:3], key=lambda event: int(event.get("year") or 0))
    good = [
        f"{event.get('year')}년 {_premium_summary_timing_title(event, 'good')}"
        for event in good_source
        if event.get("year")
    ]
    caution = [
        f"{event.get('year')}년 {_premium_summary_timing_title(event, 'caution')}"
        for event in caution_source
        if event.get("year")
    ]
    return {
        "good": " · ".join(good),
        "caution": " · ".join(caution),
    }


def _premium_summary_timing_title(event: dict[str, Any], kind: str) -> str:
    title = str(event.get("title") or event.get("domainLabel") or ("강한 운" if kind == "good" else "주의 운")).strip()
    replacements = {
        "책임·권한 불균형": "책임 전가",
        "권한 없는 책임": "책임 전가",
        "권한 확대": "결정권 확보",
        "자산 취득": "자산 확보",
        "업무 과부하": "책임 과중",
        "평판 손상": "평판 검증",
        "공동 자금 분쟁": "지분 손실",
        "보증·대여 손실": "보증 손실",
        "계약·정산 문제": "계약 손실",
    }
    return replacements.get(title, title)


def _premium_summary_personality(sections: list[dict[str, Any]]) -> str:
    personality = next((section for section in sections if str(section.get("domain") or "") == "personality"), None)
    if not personality:
        return ""
    payload = personality.get("personality_profile")
    if isinstance(payload, dict):
        intro = _personality_profile_intro(payload, fallback="")
        if intro:
            return intro
    checkpoints = list(personality.get("checkpoints") or [])
    conclusion = _checkpoint_value(checkpoints, "성격 결론")
    decision = _checkpoint_value(checkpoints, "판단 기준")
    if conclusion and decision:
        return _join_short_summary_parts(_personality_type_sentence(conclusion), decision)
    social = _checkpoint_value(checkpoints, "대인 거리감") or _checkpoint_value(checkpoints, "사람을 대하는 방식")
    if social:
        return _join_short_summary_parts(str(personality.get("lead") or ""), social)
    return str(personality.get("lead") or "")


def _premium_personality_basis_label(value: str) -> str:
    parts = [
        f"{part.strip()}형"
        for part in str(value or "").split(">")
        if part.strip()
    ]
    return " · ".join(parts[:3])



def _catalog_entry(
    entry_id: str,
    title: str,
    preview: str,
    *,
    tier: str,
    display_group: str = "default",
    kind: str = "domain",
    linked_index: int | None = None,
    premium_only: bool = False,
    view_target: str | None = None,
) -> dict[str, Any]:
    is_locked = premium_only and tier != "premium"
    return {
        "entry_id": entry_id,
        "title": title,
        "kind": kind,
        "display_group": display_group,
        "tiers": ["premium"] if premium_only else ["free", "premium"],
        "is_locked": is_locked,
        "unlock_tier": "premium" if is_locked else None,
        "preview": preview,
        "source_domains": [],
        "linked_item_indexes": [linked_index] if linked_index else [],
        "view_target": view_target,
        "content_blocks": [],
        "content_summary": preview,
    }


def _judgment_catalog_entries(tier: str) -> list[dict[str, Any]]:
    free_entries = [
        _catalog_entry(
            "judgment_total",
            "종합운",
            "사주 전체에서 가장 강하게 드러나는 결론을 먼저 보여드립니다.",
            tier=tier,
            kind="core",
            linked_index=1,
        ),
        _catalog_entry(
            "judgment_money",
            "재물운",
            "수입이 생기는 자리와 재산으로 남는 자리를 나누어 보여드립니다.",
            tier=tier,
            linked_index=1,
        ),
        _catalog_entry(
            "judgment_career",
            "직업운",
            "성취가 평가, 권한, 경력으로 남는 방식을 보여드립니다.",
            tier=tier,
            linked_index=2,
        ),
        _catalog_entry(
            "judgment_love",
            "연애운",
            "인연의 시작과 애정 표현, 관계 지속성을 보여드립니다.",
            tier=tier,
            linked_index=3,
        ),
        _catalog_entry(
            "judgment_marriage",
            "결혼운",
            "배우자상, 생활 안정, 부부 재정을 중심으로 보여드립니다.",
            tier=tier,
            linked_index=4,
        ),
    ]
    premium_entries = [
        _catalog_entry(
            "premium_personality",
            "성격",
            "판단 기준, 대인 태도, 감정 반응, 압박을 받을 때의 모습이 드러납니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_money_detail",
            "재물 세부 운세",
            "재물 형성력, 수입 창출력, 자산화 능력, 공동자금 운영력, 계약·명의 안정성이 각각 드러납니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_career_detail",
            "직업 세부 운세",
            "성취 축적력, 평가·명예 전환력, 조직 적응력, 권한 확보력, 전문 자산화가 각각 드러납니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_love_detail",
            "연애 세부 운세",
            "상대 선택, 인연 형성, 애정 표현, 관계 지속과 주변 개입 지점이 드러납니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_marriage_detail",
            "결혼 세부 운세",
            "혼인 성향, 배우자상, 생활 안정, 부부 재정, 가족 책임의 차이를 보여드립니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_good_timing",
            "인생 주요 연도",
            "20세부터 79세까지 좋은 연도와 주의 연도를 구분해 제시합니다.",
            tier=tier,
            display_group="premium",
            kind="timing",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_life_stages",
            "초년·중년·말년",
            "인생 구간별로 강해지는 영역과 보완할 영역을 구분합니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_honor",
            "명예운",
            "사회적 인정, 평판, 책임 있는 자리에서 명예운이 드러나는 방식을 제시합니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
        _catalog_entry(
            "premium_social",
            "대인관계운",
            "신뢰 형성 방식, 부담이 붙는 관계, 대인 영향력이 각각 드러납니다.",
            tier=tier,
            display_group="premium",
            kind="premium",
            premium_only=True,
            view_target="premium",
        ),
    ]
    if tier == "premium":
        return premium_entries
    return free_entries + premium_entries


def _pick_factor_preview_sections(sections: list[dict[str, Any]], limit: int = 23) -> list[dict[str, Any]]:
    layer_limits = {
        "season_context": 1,
        "month_governance": 1,
        "branch_reality": 3,
        "cycle_principle_matrix": 8,
        "cycle_regulation": 6,
        "integrated_saju": 2,
        "element_combination": 2,
        "stem_reception": 2,
        "ten_god_interaction": 2,
    }
    picked: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    for layer, layer_limit in layer_limits.items():
        layer_items = [section for section in sections if section.get("layer") == layer]
        for section in layer_items[:layer_limit]:
            picked.append(section)
            used_ids.add(id(section))
    if len(picked) < limit:
        for section in sections:
            if id(section) in used_ids:
                continue
            picked.append(section)
            if len(picked) >= limit:
                break
    return picked[:limit]


def _compact_factor_text(value: Any, *, sentence: bool = True) -> str:
    text = str(value or "").strip().replace("\n", " ")
    if not text:
        return ""
    first_sentence = text.split(".", 1)[0].strip()
    if not first_sentence:
        return text
    return f"{first_sentence}." if sentence else first_sentence


def _compact_factor_sentences(value: Any, *, limit: int = 3) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().replace("\n", " "))
    if not text:
        return ""
    sentences = [part.strip() for part in text.split(".") if part.strip()]
    if not sentences:
        return text
    return " ".join(f"{part}." for part in sentences[:limit])


TEN_GOD_FACTOR_MEANINGS: dict[str, str] = {
    "비견": "자기 기준, 독립성, 동료와의 관계",
    "겁재": "내 몫, 경쟁, 가까운 사람과의 분배 문제",
    "식신": "기술, 산출물, 꾸준히 만들어내는 결과",
    "상관": "표현, 비판, 개선, 말의 책임",
    "편재": "거래, 사업성, 외부 기회와 큰 자금",
    "정재": "고정 수입, 생활비, 현실 기준",
    "편관": "압박, 경쟁, 위험 처리와 강한 책임",
    "정관": "직업적 책임, 규칙, 평판과 관계의 질서",
    "편인": "전문성, 자격, 독자적인 해석",
    "정인": "학습, 문서, 보호, 안정적인 신뢰",
}


def _ten_god_factor_meaning(name: str) -> str:
    return TEN_GOD_FACTOR_MEANINGS.get(str(name or "").strip(), "성격과 사건의 작용 방식")


def _customer_factor_lead(section: dict[str, Any]) -> str:
    layer = str(section.get("layer") or "")
    source = str(section.get("source_label") or "")
    heading = str(section.get("heading") or "")
    lead = str(section.get("lead") or "")

    if layer == "season_context":
        specific = _compact_factor_text(lead)
        specific = specific.replace(
            "부담이 붙기 쉬운 오행은 확인 필요",
            "부담 작용은 대운과 세운에서 드러나는 쪽으로 잡힙니다",
        )
        if specific:
            return (
                f"{specific} "
                "월지는 사주의 기본 환경이므로, 이 기준에서 각 영역의 길흉을 다시 판정합니다."
            )
        return (
            "월지를 기준으로 계절 조건과 필요한 오행을 먼저 잡습니다. "
            "각 영역의 길흉은 이 기준 위에서 다시 판정합니다."
        )

    if source == "지지·지장간":
        lead_sentences = [part.strip() for part in str(lead or "").split(".") if part.strip()]
        sentence_limit = 4 if any("투출" in part for part in lead_sentences) else 2
        specific = ". ".join(lead_sentences[:sentence_limit])
        if specific:
            specific = f"{specific}."
            specific = _polish_factor_basis_text(specific)
        if specific:
            return specific
        position = heading.split(" ", 1)[0]
        position_text = {
            "월지": "사회적 조건과 직업 환경",
            "일지": "가까운 관계와 결혼 생활",
            "시지": "후반 결과와 장기 성취",
            "년지": "초년 배경과 바깥 관계",
        }.get(position, "생활 속 현실 조건")
        return (
            f"{heading}은 {position_text}에 대한 판단 근거입니다. "
            "지장간은 처음보다 시간이 지난 뒤 현실 문제로 올라오는 속사정입니다."
        )

    if source == "합충형파해":
        specific = _compact_factor_text(lead)
        if specific:
            return specific
        return (
            "지지의 합충형파해는 사건이 움직이는 방식을 보는 근거입니다. "
            "필요한 작용이 살아나는지, 부담 작용이 손실과 갈등으로 드러나는지 판정합니다."
        )

    if layer == "month_governance" or source == "월령 심화":
        specific = _compact_factor_sentences(lead, limit=4)
        if specific:
            return specific
        return (
            "월지 본기와 태어난 절기 안에서 실제로 작동하는 지장간을 분리해 판정합니다. "
            "격국의 이름보다 어떤 십신이 먼저 현실화되는지가 핵심입니다."
        )

    if layer == "stem_reception":
        match = re.search(r"([甲乙丙丁戊己庚辛壬癸])일간과\s*([甲乙丙丁戊己庚辛壬癸])\s*([가-힣]+)의 관계", heading)
        if match:
            day_stem, target_stem, ten_god = match.groups()
            meaning = _ten_god_factor_meaning(ten_god)
            return (
                f"{day_stem}일간이 {target_stem} 글자를 만나면 {meaning}{_object_particle(meaning)} 중심으로 반응합니다. "
                "겉으로 보이는 성향보다 실제 선택 기준에 가깝습니다."
            )
        return "일간이 다른 글자를 받아들이는 방식을 기준으로 성격과 실제 선택 방식을 구분합니다."

    if layer == "ten_god_interaction":
        match = re.search(r"([가-힣]+)-([가-힣]+)\s*십신 관계", heading)
        if match:
            left, right = match.groups()
            left_meaning = _ten_god_factor_meaning(left)
            right_meaning = _ten_god_factor_meaning(right)
            if left == right:
                return (
                    f"{left}{_subject_particle(left)} 반복되면 {left_meaning}{_subject_particle(left_meaning)} 강하게 부각됩니다. "
                    "돈, 직업, 관계 중 어느 영역에서 과해지거나 힘을 얻는지가 이 근거의 핵심입니다."
                )
            return (
                f"{left}{_and_particle(left)} {right}의 결합은 {left_meaning}에 {right_meaning}{_subject_particle(right_meaning)} 얽히는 신호입니다. "
                "돈, 직업, 관계 중 어느 영역에서 사건으로 드러나는지가 이 근거의 핵심입니다."
            )
        return "십신끼리의 결합은 행동 방식과 사건의 방향을 함께 정하는 근거입니다."

    if layer == "cycle_principle_matrix":
        return _compact_factor_sentences(lead, limit=3)

    if layer == "cycle_regulation":
        specific = _compact_factor_text(lead)
        specific = specific.replace("살아 있을 때", "받쳐 줄 때")
        specific = specific.replace("살아 있으면", "받쳐 주면")
        return specific

    if layer in {"integrated_saju", "element_combination"}:
        first = _compact_factor_text(lead)
        if first:
            return first
        return f"{heading}은 오행의 성질과 십신의 역할을 결합해 판단한 근거입니다."

    return _compact_factor_text(lead)


FACTOR_BASIS_COPY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        "겉으로 드러나지 않는 생활 조건을 설명합니다",
        "처음보다 시간이 지난 뒤 현실 문제로 올라옵니다",
    ),
    (
        "겉으로 바로 드러나지 않는 생활 조건을 설명합니다",
        "처음보다 시간이 지난 뒤 현실 문제로 올라옵니다",
    ),
    (
        "부담이 붙기 쉬운 오행은 확인 필요",
        "부담 작용은 대운과 세운에서 드러나는 쪽으로 잡힙니다",
    ),
    ("큰 자금를", "큰 자금을"),
    ("작용이 월령 기준 판정에 들어갑니다", "월령 기준 판정에 반영됩니다"),
)


def _polish_factor_basis_text(text: Any) -> str:
    cleaned = str(text or "").strip()
    for before, after in FACTOR_BASIS_COPY_REPLACEMENTS:
        cleaned = cleaned.replace(before, after)
    return _fix_factor_particle_text(cleaned)


def _customer_factor_domains(domain_labels: Any) -> list[str]:
    if not isinstance(domain_labels, list):
        return []
    allowed: list[str] = []
    label_map = {
        "사회": "직업",
        "자기 기준": "성격",
        "가정": "결혼·가정",
        "결과물": "직업",
        "후반": "인생 구간",
    }
    seen: set[str] = set()
    for label in domain_labels:
        text = str(label or "").strip()
        if not text:
            continue
        if any(blocked in text for blocked in ("부모", "자녀", "윗사람")):
            continue
        text = label_map.get(text, text)
        if text in seen:
            continue
        seen.add(text)
        allowed.append(text)
    return allowed[:4]


def _prepare_factor_sections_for_cards(sections: Any) -> list[dict[str, Any]]:
    if not isinstance(sections, list):
        return []
    normalized = [dict(section) for section in sections if isinstance(section, dict)]
    prepared: list[dict[str, Any]] = []
    for section in _pick_factor_preview_sections(normalized):
        prepared.append(
            {
                "layer": str(section.get("layer") or ""),
                "source_label": str(section.get("source_label") or "명리 요소"),
                "heading": _compact_factor_text(section.get("heading"), sentence=False),
                "lead": _customer_factor_lead(section),
                "domain_labels": _customer_factor_domains(section.get("domain_labels")),
                "domain_bodies": dict(section.get("domain_bodies") or {}),
                "domain_scores": dict(section.get("domain_scores") or {}),
            }
        )
    return prepared


DOMAIN_FACTOR_TERMS: dict[str, tuple[str, ...]] = {
    "personality": ("성격", "성향", "자기 기준", "판단", "일간"),
    "money": ("재물", "돈", "자산", "수입", "거래"),
    "career": ("직업", "사회", "성취", "책임", "평가"),
    "love": ("연애", "관계", "인연", "감정"),
    "marriage": ("결혼", "가정", "생활", "배우자"),
    "honor": ("명예", "평판", "공식", "사회"),
    "social": ("대인", "관계", "사람", "조력"),
    "life": ("인생", "구간", "초년", "중년", "말년"),
    "timing": ("연도", "시기", "대운", "세운", "전환"),
}


def _factor_domain_score(section: dict[str, Any], domain: str) -> int:
    layer = str(section.get("layer") or "")
    source = str(section.get("source_label") or "")
    heading = str(section.get("heading") or "")
    lead = str(section.get("lead") or "")
    labels = [str(label or "") for label in section.get("domain_labels") or []]
    terms = DOMAIN_FACTOR_TERMS.get(domain, ())
    text = " ".join([source, heading, lead, *labels])
    score = 0
    domain_scores = section.get("domain_scores")
    if isinstance(domain_scores, dict):
        try:
            score += int(domain_scores.get(domain) or 0)
        except (TypeError, ValueError):
            pass
    if any(term and term in text for term in terms):
        score += 70
    if domain == "money" and any(term in text for term in ("재성", "정재", "편재", "식상생재", "비겁", "몫", "소유")):
        score += 35
    if domain == "career" and any(term in text for term in ("관성", "정관", "편관", "식신제살", "관인상생", "재생관")):
        score += 35
    if domain in {"love", "marriage", "social"} and any(term in text for term in ("일지", "관계", "배우자", "합", "충", "형", "해", "파")):
        score += 30
    if domain == "personality" and layer in {"stem_reception", "element_combination", "ten_god_interaction"}:
        score += 35
    if layer == "cycle_principle_matrix":
        score += 68
    if layer == "season_context":
        score += 45
    if layer == "month_governance":
        score += 65
    if layer == "cycle_regulation":
        score += 55
    if source == "지지·지장간":
        if domain in {"career", "honor"} and heading.startswith("월지"):
            score += 45
        if domain in {"love", "marriage", "social"} and heading.startswith("일지"):
            score += 45
        if domain in {"money", "career", "life"} and heading.startswith("시지"):
            score += 35
    if source == "합충형파해":
        score += 25
    return score


def _basis_card_label(source: str, layer: str) -> str:
    if source == "월령·조후":
        return "월령 기준"
    if source == "월령 심화" or layer == "month_governance":
        return "월령 심화"
    if source == "지지·지장간":
        return "지지·지장간"
    if source == "합충형파해":
        return "사건 작용"
    if layer in {"integrated_saju", "ten_god_interaction"}:
        return "생극·십신"
    if layer == "cycle_principle_matrix":
        return "생극·십신"
    if layer == "cycle_regulation":
        return "상생상극"
    if layer == "element_combination":
        return "오행 배합"
    if layer == "stem_reception":
        return "일간 반응"
    return source or "판정 근거"


PREMIUM_BASIS_ORDER: dict[str, tuple[str, ...]] = {
    "personality": ("생극·십신", "상생상극", "오행 배합", "일간 반응", "월령 심화", "월령 기준", "지지·지장간", "월령 판정"),
    "money": ("월령 판정", "월령 심화", "생극·십신", "상생상극", "지지·지장간", "월령 기준", "오행 배합", "일간 반응", "사건 작용"),
    "career": ("월령 판정", "월령 심화", "지지·지장간", "생극·십신", "상생상극", "월령 기준", "오행 배합", "일간 반응"),
    "love": ("월령 판정", "월령 심화", "지지·지장간", "사건 작용", "생극·십신", "상생상극", "일간 반응", "월령 기준"),
    "marriage": ("월령 판정", "월령 심화", "지지·지장간", "사건 작용", "생극·십신", "상생상극", "일간 반응", "월령 기준"),
    "timing": ("연도 판정", "주의 판정", "판정 범위", "월령 심화", "생극·십신", "상생상극", "사건 작용", "월령 기준", "지지·지장간"),
    "life": ("지지·지장간", "월령 심화", "월령 기준", "생극·십신", "상생상극", "오행 배합", "일간 반응"),
    "honor": ("월령 판정", "월령 심화", "생극·십신", "상생상극", "지지·지장간", "월령 기준"),
    "social": ("월령 판정", "월령 심화", "지지·지장간", "사건 작용", "생극·십신", "상생상극", "일간 반응"),
}


def _source_reading_basis_limit(domain: str) -> int:
    return {
        "personality": 0,
        "timing": 0,
        "life": 0,
        "money": 1,
        "career": 1,
        "honor": 1,
        "love": 1,
        "marriage": 1,
        "social": 1,
    }.get(domain, 1)


def _premium_basis_limit(domain: str, default: int) -> int:
    return {
        "personality": 3,
        "money": 6,
        "career": 6,
        "love": 6,
        "marriage": 6,
        "timing": 3,
        "life": 3,
        "honor": 3,
        "social": 3,
    }.get(domain, default)


def _timing_basis_cards_for_section(section: dict[str, Any]) -> list[dict[str, Any]]:
    if _domain_key(section) != "timing":
        return []
    timing_map = section.get("timing_map") if isinstance(section.get("timing_map"), dict) else {}
    profile = section.get("timing_profile") if isinstance(section.get("timing_profile"), dict) else {}
    good_events = [
        event for event in timing_map.get("goodHighlights") or [] if isinstance(event, dict) and event.get("year")
    ]
    caution_events = [
        event for event in timing_map.get("cautionHighlights") or [] if isinstance(event, dict) and event.get("year")
    ]

    def event_label(event: dict[str, Any]) -> str:
        return " · ".join(
            part
            for part in (
                f"{event.get('year')}년" if event.get("year") else "",
                str(event.get("ageLabel") or ""),
                str(event.get("title") or event.get("domainLabel") or ""),
            )
            if part
        )

    def event_labels(events: list[dict[str, Any]]) -> str:
        labels = [event_label(event) for event in events[:3]]
        return " / ".join(label for label in labels if label)

    good_keywords = str(timing_map.get("goodKeywords") or "").strip()
    caution_keywords = str(timing_map.get("cautionKeywords") or "").strip()
    good_domains = str(timing_map.get("goodDomains") or profile.get("goodFocus") or "").strip()
    caution_domains = str(timing_map.get("cautionDomains") or profile.get("cautionFocus") or "").strip()
    cards: list[dict[str, Any]] = []
    if good_events:
        cards.append(
            {
                "label": "연도 판정",
                "title": "상승 연도",
                "body": (
                    f"상승 연도: {event_labels(good_events)}. "
                    f"핵심: {good_domains or '상승 분야'} · {good_keywords or '성과'}."
                ),
                "_score": 140,
                "_index": 0,
            }
        )
    if caution_events:
        cards.append(
            {
                "label": "주의 판정",
                "title": "주의 연도",
                "body": (
                    f"주의 연도: {event_labels(caution_events)}. "
                    f"핵심: {caution_domains or '주의 분야'} · {caution_keywords or '책임'}."
                ),
                "_score": 138,
                "_index": 1,
            }
        )
    range_label = str(timing_map.get("rangeLabel") or profile.get("range") or "20세~79세").strip()
    decisive = str(profile.get("decisiveAgeBands") or "").strip()
    cards.append(
        {
            "label": "판정 범위",
            "title": range_label,
            "body": (
                f"판정 범위: {range_label}. "
                f"집중 구간: {decisive or range_label}."
            ),
            "_score": 126,
            "_index": 2,
        }
    )
    return cards


SOURCE_READING_DOMAIN_TITLES: dict[str, dict[str, str]] = {
    "money": {
        "day_stem_month_branch": "월령으로 본 재물의 성격",
        "day_pillar": "일주로 본 재물의 쓰임",
    },
    "career": {
        "day_stem_month_branch": "월령으로 본 직업의 방향",
        "day_pillar": "일주로 본 직업 성향",
    },
    "love": {
        "day_stem_month_branch": "월령으로 본 애정의 방식",
        "day_pillar": "일주로 본 연애 성향",
    },
    "marriage": {
        "day_stem_month_branch": "월령으로 본 결혼의 조건",
        "day_pillar": "일주로 본 결혼 생활",
    },
    "honor": {
        "day_stem_month_branch": "월령으로 본 사회적 인정",
        "day_pillar": "일주로 본 평판의 성격",
    },
    "social": {
        "day_stem_month_branch": "월령으로 본 대인관계",
        "day_pillar": "일주로 본 관계 태도",
    },
}


def _source_reading_basis_label(source_type: str) -> str:
    source = str(source_type or "").strip()
    if source == "day_stem_month_branch":
        return "월령 판정"
    if source == "day_pillar":
        return "일주 판정"
    return "원국 판정"


def _source_reading_basis_title(point: dict[str, Any], domain: str) -> str:
    source_type = str(point.get("source_type") or "").strip()
    label = str(point.get("label") or "").strip()
    mapped = SOURCE_READING_DOMAIN_TITLES.get(domain, {}).get(source_type)
    if mapped:
        return mapped
    if "월령" in label:
        return f"월령으로 본 {label.replace('월령 ', '')}"
    if label:
        return label
    return "세부 판정"


def _source_reading_basis_intro(
    point: dict[str, Any],
    domain: str,
    month_anchor_context: dict[str, Any] | None = None,
) -> str:
    source_type = str(point.get("source_type") or "").strip()
    source_key = str(point.get("source_key") or "").strip()
    domain_label = {
        "money": "재물",
        "career": "직업",
        "love": "연애",
        "marriage": "결혼",
        "honor": "명예",
        "social": "대인관계",
        "life": "인생 구간",
        "personality": "성격",
    }.get(domain, "해당 영역")
    if source_type == "day_stem_month_branch" and len(source_key) >= 2:
        context = month_anchor_context if isinstance(month_anchor_context, dict) else {}
        day_stem = str(context.get("day_stem") or source_key[0]).strip()
        month_branch = str(context.get("month_branch") or source_key[1:]).strip()
        pattern_label = str(context.get("regular_pattern_label") or "").strip()
        command_label = str(context.get("month_command_label") or "").strip()
        if pattern_label:
            if command_label:
                return f"{day_stem}일간이 {month_branch}월에서 {pattern_label}으로 잡히는 명식입니다. {domain_label} 판단은 월지 본기 {command_label}와 {month_branch}월의 계절 작용에서 먼저 드러납니다."
            return f"{day_stem}일간이 {month_branch}월에서 {pattern_label}으로 잡히는 명식입니다. {domain_label} 판단은 {month_branch}월의 계절 작용에서 먼저 드러납니다."
        if command_label:
            return f"{day_stem}일간이 {month_branch}월 {command_label} 월령을 만난 기준에서 {domain_label}의 실제 작용을 판정합니다."
        return f"{day_stem}일간이 {month_branch}월령을 만난 기준에서 {domain_label}의 실제 작용을 판정합니다."
    if source_type == "day_pillar" and source_key:
        return f"{source_key}일주의 생활 성정이 {domain_label} 판단에 직접 반영됩니다."
    return ""


def _source_reading_phrase_as_sentence(text: str, label: str, domain: str) -> str:
    value = str(text or "").strip().rstrip(".")
    if not value:
        return ""
    sentence_markers = (
        "습니다",
        "입니다",
        "됩니다",
        "합니다",
        "입니다",
        "쉽습니다",
        "강합니다",
        "약합니다",
        "있습니다",
        "없습니다",
        "이어집니다",
        "현실화됩니다",
        "나타납니다",
        "드러납니다",
        "분명해집니다",
        "굳어집니다",
        "깊어집니다",
        "커집니다",
        "작아집니다",
        "올라갑니다",
        "내려갑니다",
        "돌아옵니다",
        "이어집니다",
        "갈립니다",
        "늦어집니다",
        "남습니다",
    )
    if any(value.endswith(marker) for marker in sentence_markers):
        return value + "."
    label_text = str(label or "").strip()
    if domain == "career" or any(token in label_text for token in ("역할", "직업", "일")):
        return f"잘 맞는 역할은 {value}입니다."
    if any(token in label_text for token in ("상대", "사람")):
        return f"잘 맞는 상대는 {value}입니다."
    if "선택" in label_text:
        return f"피해야 할 선택은 {value}입니다."
    if domain == "money":
        return f"재물은 {value}에서 손익의 결론이 갈립니다."
    if domain in {"love", "marriage"}:
        return f"관계는 {value}에서 실제 결론이 납니다."
    return value + "."


def _source_reading_basis_body(
    point: dict[str, Any],
    domain: str,
    month_anchor_context: dict[str, Any] | None = None,
) -> str:
    label = str(point.get("label") or "").strip()
    body = _polish_source_reading_text(str(point.get("text") or "").strip())
    body = _polish_factor_basis_text(body)
    body = _source_reading_phrase_as_sentence(body, label, domain)
    intro = _source_reading_basis_intro(point, domain, month_anchor_context)
    if intro and intro not in body:
        return f"{intro} {body}".strip()
    return body


def _source_reading_rank(point: dict[str, Any], domain: str, index: int) -> tuple[int, int]:
    source_type = str(point.get("source_type") or "").strip()
    label = str(point.get("label") or "").strip()
    score = 0
    if source_type == "day_stem_month_branch":
        score += 60
    elif source_type == "day_pillar":
        score += 35
    if "월령" in label:
        score += 25
    if domain == "money" and any(token in label for token in ("재물", "돈", "손실", "보전")):
        score += 18
    if domain == "career" and any(token in label for token in ("직업", "역할", "조직", "독립")):
        score += 18
    if domain in {"love", "marriage"} and any(token in label for token in ("연애", "사랑", "관계", "결혼")):
        score += 18
    if domain == "social" and any(token in label for token in ("관계", "평판", "첫인상")):
        score += 18
    return (-score, index)


def _source_reading_basis_cards(
    section: dict[str, Any],
    limit: int = 2,
    month_anchor_context: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    points = section.get("source_reading_points")
    if not isinstance(points, list):
        return cards
    domain = _domain_key(section)
    ranked_points = sorted(
        (
            (index, point)
            for index, point in enumerate(points)
            if isinstance(point, dict)
        ),
        key=lambda item: _source_reading_rank(item[1], domain, item[0]),
    )
    for _index, point in ranked_points:
        if not isinstance(point, dict):
            continue
        title = _source_reading_basis_title(point, domain)
        body = _source_reading_basis_body(point, domain, month_anchor_context)
        if not body:
            continue
        cards.append(
            {
                "label": _source_reading_basis_label(str(point.get("source_type") or "")),
                "title": title,
                "body": body,
            }
        )
        if len(cards) >= limit:
            break
    return cards


def _premium_basis_cards_for_section(
    section: dict[str, Any],
    factor_sections: list[dict[str, Any]],
    *,
    limit: int = 4,
    month_anchor_context: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    domain = _domain_key(section)
    target_limit = _premium_basis_limit(domain, limit)
    candidates: list[dict[str, Any]] = []
    candidates.extend(_timing_basis_cards_for_section(section))
    for index, card in enumerate(
        _source_reading_basis_cards(
            section,
            limit=_source_reading_basis_limit(domain),
            month_anchor_context=month_anchor_context,
        )
    ):
        candidates.append({**card, "_score": 120, "_index": index})

    ranked = sorted(
        (
            (_factor_domain_score(factor, domain), index, factor)
            for index, factor in enumerate(factor_sections)
            if isinstance(factor, dict)
        ),
        key=lambda item: (-item[0], item[1]),
    )
    for score, _index, factor in ranked:
        if score <= 0:
            continue
        title = str(factor.get("heading") or "").strip()
        domain_bodies = factor.get("domain_bodies")
        domain_body = (
            str(domain_bodies.get(domain) or "").strip()
            if isinstance(domain_bodies, dict)
            else ""
        )
        body = domain_body
        if not body:
            body = str(factor.get("lead") or "").strip()
        label = _basis_card_label(str(factor.get("source_label") or ""), str(factor.get("layer") or ""))
        if label == "상생상극" and domain in {"timing", "life", "honor", "social"} and not domain_body:
            continue
        if label == "상생상극" and any(marker in title for marker in ("통근", "투출")) and not domain_body:
            continue
        if not title or not body:
            continue
        candidates.append(
            {
                "label": label,
                "title": title,
                "body": _polish_factor_basis_text(body),
                "_score": score,
                "_index": _index + 100,
            }
        )

    order = PREMIUM_BASIS_ORDER.get(domain, ("월령 판정", "상생상극", "지지·지장간", "월령 기준"))

    def sort_key(card: dict[str, Any]) -> tuple[int, int, int]:
        label = str(card.get("label") or "")
        order_index = order.index(label) if label in order else len(order)
        return (order_index, -int(card.get("_score") or 0), int(card.get("_index") or 0))

    cards: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    label_counts: dict[str, int] = {}
    for card in sorted(candidates, key=sort_key):
        label = str(card.get("label") or "").strip()
        title = str(card.get("title") or "").strip()
        body = str(card.get("body") or "").strip()
        if not label or not title or not body:
            continue
        label_limit = 2 if label == "생극·십신" and domain in {"money", "career", "love", "marriage"} else 1
        if label_counts.get(label, 0) >= label_limit:
            continue
        key = (title, body)
        if key in seen:
            continue
        seen.add(key)
        label_counts[label] = label_counts.get(label, 0) + 1
        cards.append({"label": label, "title": title, "body": body})
        if len(cards) >= target_limit:
            break
    return cards[:target_limit]


def _attach_premium_basis_cards(
    sections: list[dict[str, Any]],
    factor_sections: list[dict[str, Any]],
    month_anchor_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for section in sections:
        next_section = dict(section)
        cards = _premium_basis_cards_for_section(
            next_section,
            factor_sections,
            month_anchor_context=month_anchor_context,
        )
        if cards:
            next_section["premium_basis_cards"] = cards
        enriched.append(next_section)
    return enriched


PUBLIC_TIMING_EVENT_KEYS = (
    "year",
    "age",
    "ageLabel",
    "isPast",
    "periodLabel",
    "domain",
    "domainLabel",
    "kind",
    "variant",
    "eventKey",
    "title",
    "keywords",
    "focusLine",
    "decisionLine",
    "productLine",
    "activationLabel",
    "sourcePath",
    "structureKeywords",
    "daeunPillar",
    "daeunStemTenGod",
    "daeunBranchTenGod",
    "yearPillar",
    "yearStemTenGod",
    "yearBranchTenGod",
    "kindLabel",
    "keywordItems",
    "summary",
    "score",
)


def _public_timing_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {}
    return {key: event.get(key) for key in PUBLIC_TIMING_EVENT_KEYS if key in event and event.get(key) not in (None, "", [], {})}


def _public_timing_event_list(events: Any) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        return []
    return [item for item in (_public_timing_event(event) for event in events) if item.get("year")]


def _public_timing_domain_years(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    public_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        next_item = {
            key: value
            for key, value in item.items()
            if key not in {"activationContext", "scoreParts", "basisCodes", "counterSignals", "branchInteractions"}
        }
        for nested_key in ("good", "caution"):
            if isinstance(next_item.get(nested_key), dict):
                next_item[nested_key] = _public_timing_event(next_item[nested_key])
        public_items.append(next_item)
    return public_items


def _public_timing_decades(groups: Any) -> list[dict[str, Any]]:
    if not isinstance(groups, list):
        return []
    public_groups: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        next_group = {
            key: value
            for key, value in group.items()
            if key not in {"activationContext", "scoreParts", "basisCodes", "counterSignals", "branchInteractions"}
        }
        for nested_key in ("good", "caution"):
            if isinstance(next_group.get(nested_key), dict):
                next_group[nested_key] = _public_timing_event(next_group[nested_key])
        public_groups.append(next_group)
    return public_groups


def _public_timing_map(timing_map: Any) -> dict[str, Any]:
    if not isinstance(timing_map, dict):
        return {}
    public_map = {
        key: value
        for key, value in timing_map.items()
        if key not in {"activationContext", "scoreParts", "basisCodes", "counterSignals", "branchInteractions"}
    }
    for key in ("goodHighlights", "cautionHighlights", "pastCheck", "futureCheck"):
        public_map[key] = _public_timing_event_list(public_map.get(key))
    public_map["domainYearHighlights"] = _public_timing_domain_years(public_map.get("domainYearHighlights"))
    return public_map


def _public_premium_section(section: dict[str, Any]) -> dict[str, Any]:
    next_section = dict(section)
    caution_label = _clean_caution_label(str(next_section.get("caution_label") or ""), "")
    if caution_label:
        next_section["caution_label"] = caution_label
    else:
        next_section.pop("caution_label", None)
    checkpoints = []
    for checkpoint in list(next_section.get("checkpoints") or []):
        text = str(checkpoint or "").strip()
        if not text:
            continue
        if text.startswith("주의점:"):
            caution_text = text.split(":", 1)[1].strip()
            if _is_neutral_caution_label(caution_text):
                continue
        checkpoints.append(text)
    if checkpoints:
        next_section["checkpoints"] = checkpoints
    if str(next_section.get("domain") or "") == "timing":
        next_section["timing_events"] = _public_timing_event_list(next_section.get("timing_events"))
        next_section["timing_map"] = _public_timing_map(next_section.get("timing_map"))
        next_section["timing_decades"] = _public_timing_decades(next_section.get("timing_decades"))
    return next_section


def _public_premium_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_public_premium_section(section) for section in sections]


def _prepare_judgment_card_payload(
    report: dict[str, Any],
    chart_summary: dict[str, Any],
    product_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prepared = dict(report)
    product_items = list((product_payload or {}).get("items", []))
    mobile_cards = [
        _normalize_mobile_card(dict(card), dict(product_items[index]) if index < len(product_items) else None)
        for index, card in enumerate(prepared.get("mobile_cards", []))
    ]
    normalized_premium_sections = [
        _normalize_premium_section(
            dict(section),
            dict(product_items[index]) if index < len(product_items) else None,
        )
        for index, section in enumerate(prepared.get("premium_sections", []))
    ]
    life_feature_summary = (product_payload or {}).get("life_feature_summary") or {}
    if not isinstance(life_feature_summary, dict):
        life_feature_summary = {}
    source_personality_profile = life_feature_summary.get("source_personality_profile")
    if not isinstance(source_personality_profile, dict):
        source_personality_profile = {}
    source_reading_profile = life_feature_summary.get("source_reading_profile")
    if not isinstance(source_reading_profile, dict):
        source_reading_profile = {}
    month_anchor_context = life_feature_summary.get("month_anchor_context")
    if not isinstance(month_anchor_context, dict):
        month_anchor_context = {}
    prepared_factor_sections = _prepare_factor_sections_for_cards(prepared.get("factor_sections"))
    premium_sections = (
        _supplemental_premium_sections(
            normalized_premium_sections,
            chart_summary,
            list((product_payload or {}).get("premium_detail_sections") or []),
            source_personality_profile,
            source_reading_profile,
            dict(prepared.get("domain_decision_facets") or {}),
            dict(prepared.get("timing_decision_facets") or {}),
            dict(prepared.get("output_goal_coverage") or {}),
        )
        if str(prepared.get("product_tier") or "free") == "premium"
        else []
    )
    if premium_sections:
        premium_sections = _attach_premium_basis_cards(
            premium_sections,
            prepared_factor_sections,
            month_anchor_context,
        )
        premium_sections = _attach_premium_product_stories(premium_sections)
    premium_profile_summary = _premium_profile_summary(premium_sections) if premium_sections else {}
    public_premium_sections = _public_premium_sections(premium_sections) if premium_sections else []
    is_premium = str(prepared.get("product_tier") or "free") == "premium"
    premium_profile_cards = list(premium_profile_summary.get("cards") or []) if is_premium else []
    premium_profile_panels = list(premium_profile_summary.get("profile_panels") or []) if is_premium else []
    prepared["title"] = "AI 사주 : 이현"
    prepared["overview"] = str(premium_profile_summary.get("headline") or "") or _product_overview(mobile_cards)
    prepared["premium_profile_summary"] = premium_profile_summary
    prepared["premium_profile_panels"] = premium_profile_panels
    prepared["premium_profile_cards"] = premium_profile_cards
    prepared["premium_profile_contract"] = dict((product_payload or {}).get("premium_profile_contract") or prepared.get("premium_profile_contract") or {})
    prepared["free_profile_preview"] = {} if is_premium else _free_profile_preview(mobile_cards)
    prepared["mobile_cards"] = [] if is_premium else mobile_cards
    prepared["premium_sections"] = public_premium_sections
    prepared["web_sections"] = []
    prepared["reading_sections"] = []
    prepared["factor_sections"] = prepared_factor_sections
    prepared["catalog_entries"] = _judgment_catalog_entries(str(prepared.get("product_tier") or "free"))
    for internal_key in (
        "domain_decision_facets",
        "timing_decision_facets",
        "output_goal_coverage",
        "premium_candidate_sections",
        "premium_detail_sections",
    ):
        prepared.pop(internal_key, None)
    return _clean_customer_copy_value(prepared)


def build_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a UI-ready fortune result payload from form input."""

    tier = _as_text(payload, "tier", "free") or "free"
    if tier not in SUPPORTED_TIERS:
        raise ValueError("상품 등급 값이 올바르지 않습니다.")
    relationship_status = _as_text(payload, "relationshipStatus", "unknown") or "unknown"
    if relationship_status not in SUPPORTED_RELATIONSHIP_STATUSES:
        raise ValueError("관계 상태 값이 올바르지 않습니다.")

    target_year = _parse_target_year(payload)
    birth_date = _as_text(payload, "birthDate")
    birth_time = _as_text(payload, "birthTime")
    gender = _as_text(payload, "gender", "unknown") or "unknown"
    calendar_type = _as_text(payload, "calendarType", _as_text(payload, "calendar", "solar")) or "solar"
    leap_lunar_month = bool(payload.get("leapLunarMonth", False))
    chart, birth_year, product_target_years, analysis = _analysis_context_cached(
        birth_date,
        birth_time,
        gender,
        calendar_type,
        relationship_status,
        target_year,
        leap_lunar_month,
    )
    product = build_product_output(
        analysis,
        tier=tier,  # type: ignore[arg-type]
        item_limit_override=72 if tier == "premium" else None,
        include_candidate_sections=False,
    )
    product_payload = product.to_dict()
    life_feature_summary = product_payload.setdefault("life_feature_summary", {})
    cycle_regulation_context = (
        life_feature_summary.get("cycle_regulation_context")
        if isinstance(life_feature_summary, dict)
        else None
    )
    if isinstance(life_feature_summary, dict) and (
        not isinstance(cycle_regulation_context, dict)
        or not isinstance(cycle_regulation_context.get("principle_matrix"), dict)
    ):
        life_feature_summary["cycle_regulation_context"] = dict(
            analysis.chart_structure.cycle_regulation_profile or {}
        )
    if isinstance(life_feature_summary, dict) and not isinstance(
        life_feature_summary.get("month_anchor_context"),
        dict,
    ):
        life_feature_summary["month_anchor_context"] = _month_anchor_context_from_analysis(analysis)
    timing_target_years = product_target_years
    timing_flow_signals = list(analysis.flow_signals)
    timing_event_packets = list(analysis.event_packets)
    if isinstance(life_feature_summary, dict):
        life_feature_summary["timing_decision_facets"] = build_timing_decision_payload_from_flows(
            timing_flow_signals,
            birth_year=birth_year,
            target_years=timing_target_years,
            event_packets=timing_event_packets,
        )
        life_feature_summary["output_goal_coverage"] = _refresh_output_goal_coverage_timing(
            life_feature_summary.get("output_goal_coverage"),
            life_feature_summary["timing_decision_facets"],
        )
    chart_payload = _chart_summary(chart, target_year, birth_year, timing_flow_signals)
    report_payload = _prepare_judgment_card_payload(
        _product_report_seed(product_payload),
        chart_payload,
        product_payload,
    )

    visible_chart_payload = dict(chart_payload)
    visible_chart_payload.pop("timingAnnualRows", None)

    return {
        "ok": True,
        "request": {
            "tier": tier,
            "targetYear": target_year,
            "relationshipStatus": relationship_status,
        },
        "chart": visible_chart_payload,
        "report": report_payload,
    }
