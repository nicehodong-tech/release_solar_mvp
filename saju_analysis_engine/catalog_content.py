"""Customer-facing content blocks for product catalog entries.

The catalog is the promise shown in menus. These blocks make each menu entry
open into a distinct customer-facing unit without recalculating the chart.
"""

from __future__ import annotations

from typing import Any

from .branch_reality_profiles import branch_domain_texture, branch_position_texture
from .catalog_dedicated_profiles import DEDICATED_CATALOG_BLOCK_PROFILES
from .models import Domain, ProductOutputItem
from .rendering import DOMAIN_LABELS


ContentBlock = dict[str, object]

MIN_VISIBLE_CONTENT_BLOCKS = 4
CURRENT_FORTUNE_YEAR = 2026
CURRENT_FORTUNE_YEAR_PILLAR = "병오"

ANNUAL_ENTRY_IDS = {
    "annual_overview",
    "annual_money",
    "annual_career",
    "annual_love",
    "annual_best",
    "annual_caution",
    "annual_good_timing",
    "annual_caution_timing",
}

YEAR_EXPLICIT_ENTRY_IDS = ANNUAL_ENTRY_IDS | {
    "timing_detail",
    "monthly_key_timing",
    "favorable_timing",
    "caution_timing",
}

DEDICATED_BLOCK_ROLE_ORDER = ("orientation", "life_scene", "strength", "score", "caution", "action")
DEDICATED_BLOCK_HEADINGS = {
    "orientation": "이 영역을 대하는 태도",
    "life_scene": "생활에서 보이는 모습",
    "strength": "강점",
    "score": "판단 기준",
    "caution": "주의할 점",
    "action": "좋게 쓰는 법",
}


DOMAIN_ORDER: tuple[Domain, ...] = ("money", "career", "love", "marriage")

DOMAIN_NOUNS: dict[Domain, str] = {
    "money": "재물",
    "career": "직업",
    "love": "연애",
    "marriage": "결혼",
}

DOMAIN_GOOD_TIMING_SENTENCES: dict[Domain, str] = {
    "money": "재물운에서 받을 돈이 좋아집니다.",
    "career": "직업운에서 인정받을 일이 생깁니다.",
    "love": "연애운에서 좋은 만남이 생깁니다.",
    "marriage": "결혼운에서 약속이 가까워집니다.",
}

DOMAIN_CAUTION_TIMING_SENTENCES: dict[Domain, str] = {
    "money": "재물운에서 신중하게 다룰 돈 문제가 생깁니다.",
    "career": "직업운에서 책임과 권한 문제를 신중하게 봐야 합니다.",
    "love": "연애운에서 마음이 급해지기 쉬운 시기입니다.",
    "marriage": "결혼운에서 생활 문제를 서두르지 말아야 합니다.",
}

DOMAIN_SCENES: dict[Domain, str] = {
    "money": "수입 구조",
    "career": "맡는 역할",
    "love": "감정 표현",
    "marriage": "생활 합의",
}

DOMAIN_BRANCH_POSITION_PRIORITY: dict[Domain, tuple[str, ...]] = {
    "money": ("month", "hour", "day", "year"),
    "career": ("month", "year", "hour", "day"),
    "love": ("day", "hour", "month", "year"),
    "marriage": ("day", "month", "hour", "year"),
}

DOMAIN_REALITY_CATALOG_SCENES: dict[Domain, dict[str, str]] = {
    "money": {
        "month": "직업 수입",
        "day": "가까운 사람 사이의 돈",
        "hour": "후반 자산 기준",
        "year": "초기 재물 습관",
    },
    "career": {
        "month": "직장 환경",
        "day": "일상 업무 방식",
        "hour": "후반 성과",
        "year": "대외 평판",
    },
    "love": {
        "month": "사회적 만남",
        "day": "마음을 주는 방식",
        "hour": "늦게 생기는 기대",
        "year": "첫인상",
    },
    "marriage": {
        "month": "직업 문제가 결혼 이야기로 이어지는 방식",
        "day": "배우자와의 생활 방식",
        "hour": "가정의 후반 계획",
        "year": "가족 배경과 책임 의식",
    },
}

DOMAIN_REALITY_CATALOG_RESULTS: dict[Domain, str] = {
    "money": "재물운은 들어온 돈을 얼마나 남기느냐에서 강해집니다. 지출 한도가 정해지며 돈이 남습니다. 남길 돈을 따로 떼어 두는 습관이 자산을 오래 지킵니다.",
    "career": "직업운은 맡는 일의 범위에서 강해집니다. 무엇으로 평가받는지가 보일 때 인정도 빨라집니다. 결정권이 주어지는 자리에서 직업운이 강해집니다.",
    "love": "연애운은 꾸준한 연락에서 안정됩니다. 말투가 안정될수록 마음도 안정됩니다. 만남의 간격이 편안할 때 관계가 오래 갑니다.",
    "marriage": "결혼운은 생활비 이야기가 정리될 때 안정됩니다. 주거 문제가 풀릴수록 결혼 이야기도 앞으로 나갑니다.",
}

DOMAIN_REALITY_CATALOG_OPENINGS: dict[Domain, dict[str, str]] = {
    "money": {
        "month": "당신의 재물운은 {label} 때문에 직업 수입의 변화가 빠릅니다.",
        "day": "당신의 재물운은 {label} 때문에 가까운 사람과 돈 문제를 맞추게 됩니다.",
        "hour": "당신의 재물운은 {label} 때문에 후반 자산 계획이 구체적으로 잡힙니다.",
        "year": "당신의 재물운은 {label} 때문에 초년에 익힌 돈 습관이 오래 남습니다.",
    },
    "career": {
        "month": "당신의 직업운은 {label} 때문에 직장 환경의 변화에 민감합니다.",
        "day": "당신의 직업운은 {label} 때문에 일상 업무 방식에서 강점과 피로가 함께 보입니다.",
        "hour": "당신의 직업운은 {label} 때문에 후반으로 갈수록 성과가 결과물로 남습니다.",
        "year": "당신의 직업운은 {label} 때문에 대외 평판이 오래 남습니다.",
    },
    "love": {
        "month": "당신의 연애운은 {label} 때문에 사회적 만남에서 호감이 생깁니다.",
        "day": "당신의 연애운은 {label} 때문에 마음을 주는 방식이 신중합니다.",
        "hour": "당신의 연애운은 {label} 때문에 시간이 지나며 기대를 더 분명히 말하게 됩니다.",
        "year": "당신의 연애운은 {label} 때문에 첫인상과 말투가 오래 남습니다.",
    },
    "marriage": {
        "month": "당신의 결혼운은 {label} 때문에 직업 문제와 생활 문제가 함께 커집니다.",
        "day": "당신의 결혼운은 {label} 때문에 배우자와 생활 방식을 중요하게 확인합니다.",
        "hour": "당신의 결혼운은 {label} 때문에 가정의 후반 계획을 오래 따집니다.",
        "year": "당신의 결혼운은 {label} 때문에 가족 배경과 책임 의식이 오래 남습니다.",
    },
}

STEM_HANJA: dict[str, str] = {
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

TEN_GOD_LABELS: dict[str, str] = {
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

FACTOR_BRIDGE_SIGNAL_KEYS = (
    "top_element_combination_signals",
    "top_stem_reception_signals",
    "top_ten_god_interaction_signals",
    "top_integrated_saju_signals",
)

FACTOR_BRIDGE_CLOSINGS: dict[Domain, str] = {
    "money": "당신의 재물운은 돈이 들어온 뒤 그 돈을 지켜내는 과정에서 강해집니다. 계약 내용이 분명해지며 손에 남는 돈이 커집니다. 정산 방식도 정리되며 재물의 안정감이 커집니다.",
    "career": "당신의 직업운은 직함보다 실제로 맡는 역할에서 강해집니다. 무엇으로 평가받는지가 보이는 자리에서는 인정도 안정적으로 받습니다. 책임 범위가 분명한 자리는 직업운이 오래 갑니다.",
    "love": "당신의 연애운은 호감이 생긴 뒤 연락에서 안정됩니다. 거리감이 어긋나면 감정이 있어도 피로가 커집니다. 표현이 자연스러워지면 관계가 오래 갑니다.",
    "marriage": "당신의 결혼운은 애정만으로 끝나지 않습니다. 생활비를 나누는 방식에서 안정감이 생깁니다. 주거 문제는 결혼 생활에 직접 닿아 있습니다.",
}

AXIS_CONTEXTS: dict[str, str] = {
    "재물 잠재력": "돈이 되는 기회를 고르고 재물 규모를 키우는 일",
    "수입 확대력": "보수가 커지는 기준을 세우는 일",
    "자산 유지력": "벌어들인 돈을 자산으로 남기는 일",
    "투자와 거래 감각": "투자, 거래, 계약의 기준을 읽는 일",
    "사업 확장력": "외부 거래와 사업 규모를 넓히는 일",
    "사회적 성공 잠재력": "맡은 역할로 사회적 인정을 받는 일",
    "직업적 성취력": "맡은 일로 실력을 인정받는 일",
    "책임 감당력": "책임 범위가 넓은 일을 끝까지 정리하는 일",
    "평판 유지력": "사회적 신뢰와 평판을 오래 지키는 일",
    "명예운": "공식 평가를 받는 일",
    "리더십 잠재력": "사람과 책임을 나누어 이끄는 일",
    "대인 영향력": "상대에게 신뢰를 주는 힘",
    "학문·전문성 성취력": "전문성이 자격과 결과물로 남는 일",
    "관계 안정성": "가까워진 관계를 안정적으로 유지하는 일",
    "표현 전달력": "생각과 감정을 상대가 이해할 수 있게 전하는 일",
    "결혼 안정성": "생활 기준과 책임을 정리하여 결혼을 유지하는 일",
    "갈등 회복력": "오해와 충돌 뒤에 관계를 다시 정리하는 일",
    "가족 책임감": "가족과 가까운 사람 앞에서 책임을 행동으로 보이는 일",
    "현실 설계력": "돈과 일의 기준을 먼저 정리하는 일",
    "변화 적응력": "상황이 바뀐 뒤 행동 기준을 다시 잡는 일",
}

AXIS_CUSTOMER_SUBJECTS: dict[str, str] = {
    "재물 잠재력": "재물을 키우는 감각",
    "수입 확대력": "수입을 키우는 감각",
    "자산 유지력": "돈을 남기는 기준",
    "투자와 거래 감각": "계약과 회수 기준을 읽는 감각",
    "사업 확장력": "확장 뒤의 비용과 책임을 계산하는 감각",
    "사회적 성공 잠재력": "사회적 인정운",
    "직업적 성취력": "직업 성취력",
    "책임 감당력": "큰 책임을 끝까지 처리하는 기질",
    "평판 유지력": "평판 유지력",
    "명예운": "명예운",
    "리더십 잠재력": "사람과 책임을 나누어 이끄는 태도",
    "대인 영향력": "상대에게 신뢰를 주는 태도",
    "학문·전문성 성취력": "전문성 성취력",
    "관계 안정성": "가까운 관계를 오래 유지하는 태도",
    "표현 전달력": "생각과 감정을 알아듣게 전하는 태도",
    "결혼 안정성": "생활 기준을 맞추는 태도",
    "갈등 회복력": "충돌 뒤 다시 대화하는 태도",
    "가족 책임감": "가족과 가까운 사람 앞에서 책임을 피하지 않는 태도",
    "현실 설계력": "돈과 일의 기준을 먼저 세우는 성향",
    "변화 적응력": "상황 변화에 맞춰 행동을 바꾸는 성향",
}


def _axis_customer_subject(axis_label: str, default: str = "현실 판단") -> str:
    return AXIS_CUSTOMER_SUBJECTS.get(axis_label, AXIS_CONTEXTS.get(axis_label, axis_label or default))


def _axis_customer_event(axis_label: str, default: str = "현실 판단") -> str:
    return AXIS_CONTEXTS.get(axis_label, AXIS_CUSTOMER_SUBJECTS.get(axis_label, axis_label or default))


def _axis_customer_label(axis_label: str, default: str = "중요한 장점") -> str:
    return _axis_customer_subject(axis_label, default=default)


def _axis_customer_prose_text(text: str) -> str:
    output = str(text)
    for old, new in AXIS_CUSTOMER_SUBJECTS.items():
        output = output.replace(old, new)
    corrections = (
        ("상대에게 신뢰를 주는 태도을 잘 쓸 때", "상대에게 신뢰를 주는 태도가 분명할 때"),
        ("충돌 뒤 다시 대화하는 태도을 잘 쓸 때", "충돌 뒤 다시 대화하는 태도가 분명할 때"),
        ("상대에게 신뢰를 주는 태도을 제대로 쓸 때", "상대에게 신뢰를 주는 태도가 분명할 때"),
        ("충돌 뒤 다시 대화하는 태도을 제대로 쓸 때", "충돌 뒤 다시 대화하는 태도가 분명할 때"),
        ("태도을 잘 쓸 때", "태도가 분명할 때"),
        ("상대에게 신뢰를 주는 태도을 크게 쓰는 사람입니다", "상대에게 신뢰를 주는 태도가 뚜렷한 사람입니다"),
        ("충돌 뒤 다시 대화하는 태도을 크게 쓰는 사람입니다", "충돌 뒤 다시 대화하는 태도가 뚜렷한 사람입니다"),
        ("상대에게 신뢰를 주는 태도을 중심에 둘 때", "상대에게 신뢰를 주는 태도가 중심에 설 때"),
        ("충돌 뒤 다시 대화하는 태도을 중심에 둘 때", "충돌 뒤 다시 대화하는 태도가 중심에 설 때"),
        ("태도을", "태도를"),
        ("태도은", "태도는"),
        ("태도이", "태도가"),
        ("태도과", "태도와"),
        ("사회적으로 인정받는 기질이 강합니다", "사회적으로 인정받을 자리가 분명합니다"),
        ("사회적으로 인정받는 기질이 강해질수록", "사회적으로 인정받을 자리가 분명해질수록"),
        ("공식 평가에서 인정받는 기질이 강해질수록", "공식 평가가 따르는 자리에서"),
        ("공식 평가에서 인정받는 기질이 강합니다", "공식 평가가 따르는 자리에 강합니다"),
        ("성향을 먼저 살피는 사람", "성향이 강한 사람"),
        ("성향이 강해질 때 판단이 단단해집니다", "성향이 분명해질수록 판단도 단단해집니다"),
        ("성향은 결정이 늦어질 때 부담으로 바뀌기 쉬운 영역입니다", "성향은 결정을 오래 미룰 때 부담으로 바뀝니다"),
    )
    for old, new in corrections:
        output = output.replace(old, new)
    return output


def _domain_timing_subject(domain: Domain, axis_label: str) -> str:
    domain_subjects: dict[Domain, str] = {
        "money": "받을 돈과 남길 돈",
        "career": "맡은 역할과 평가",
        "love": "연락과 마음의 거리",
        "marriage": "생활비와 약속",
    }
    return domain_subjects.get(domain, _axis_customer_event(axis_label))

ENTRY_CUSTOMER_FOCUS_SENTENCES: dict[str, str] = {
    "native_money": (
        "당신은 들어오는 돈을 자산으로 바꾸는 능력이 좋습니다. "
        "수입이 생기면 보유할 돈을 따로 구분합니다. "
        "다시 쓸 돈도 따로 나뉩니다. "
        "미리 막아야 할 지출이 정리되며 손에 남는 돈도 커집니다."
    ),
    "money_attitude": (
        "당신은 돈을 즉흥적으로 쓰기보다 목적과 한도를 분명히 세우는 사람입니다. "
        "돈을 쓸 때도 이유가 분명합니다. "
        "저축과 투자는 목적이 분명해진 뒤에 움직입니다."
    ),
    "native_wealth_level": (
        "한 번의 큰 수입보다 반복해서 남기는 습관에서 차이가 납니다. "
        "당신은 받을 돈, 쓸 돈, 남길 돈을 나누며 재물 수준을 끌어올립니다."
    ),
    "income_expansion_method": (
        "수입을 키우는 해에는 해낸 일이 얼마의 보상으로 인정되는지가 확정됩니다. "
        "당신은 더 많은 일을 맡는 것보다 역할과 결과물이 금액으로 인정될 때 수입이 커집니다."
    ),
    "wealth_retention_conditions": (
        "당신은 수입이 생기면 생활비와 보유금을 바로 나누는 편입니다. "
        "이 습관이 후반 자산을 키웁니다."
    ),
    "money_leak_conditions": (
        "이 부분은 큰 실패보다 느슨한 약속에서 시작됩니다. "
        "지급일을 대충 넘기면 받을 돈이 늦어집니다. "
        "나눌 몫과 남길 돈이 흐려지면 손에 남는 금액이 줄어듭니다."
    ),
    "wealth_potential": (
        "당신은 돈이 될 만한 일을 빨리 알아봅니다. "
        "규모를 키우기 전에는 돈을 회수하는 절차를 따집니다. "
        "이 절차가 재물운을 키웁니다."
    ),
    "income_expansion_power": (
        "같은 일을 하더라도 더 높은 단가와 보상으로 인정받는 자리가 있습니다. "
        "당신은 해낸 일을 말로만 남기지 않을 때 수입이 커집니다. "
        "받을 금액도 따로 정해집니다. "
        "지급일도 분명히 봅니다."
    ),
    "asset_retention_power": (
        "당신은 들어온 돈을 쉽게 흩어 놓지 않습니다. "
        "지출 한도와 보유할 돈을 미리 나눕니다. "
        "이 습관이 들어온 돈을 오래 지킵니다."
    ),
    "investment_trade_sense": (
        "투자와 거래에서는 수익률보다 회수 절차와 손실 한도를 더 크게 봅니다. "
        "당신은 계약 구조와 상대의 책임 범위를 보고 거래에서 재물운을 안정적으로 지킵니다."
    ),
    "business_expansion_power": (
        "사업 확장은 매출만 커지는 일이 아닙니다. "
        "거래처와 비용이 같이 늘어납니다. 인력과 책임 범위도 커집니다. 관리 가능한 크기의 확장이 이익으로 남습니다."
    ),
    "business_expansion": (
        "사업·확장 잠재력은 돈과 일이 함께 커지는 장면에서 강해집니다. "
        "당신은 새 기회를 잡더라도 비용과 역할을 먼저 맞추며 확장을 수익으로 바꿉니다."
    ),
    "money_caution_years": (
        "그해의 재물운은 버는 힘보다 지키는 힘으로 읽습니다. "
        "금액이 커 보이는 제안일수록 확인할 문서가 늘어납니다."
    ),
    "annual_money": (
        "올해는 받을 돈과 남길 돈이 따로 갈라집니다. "
        "지급일과 지출 한도가 분명해지면서 올해 들어오는 돈이 생활 속에서 더 오래 남습니다."
    ),
    "long_term_years": (
        "재물 규모가 커지는 때에는 일에서 받은 인정이 돈으로 환산됩니다. "
        "들어온 돈은 소비보다 보유 자산 쪽으로 묶입니다."
    ),
    "ten_year_luck": (
        "대운은 한두 사건보다 삶의 역할과 선택 방향이 길게 바뀌는 구간입니다. "
        "직업에서 맡는 역할이 달라집니다. "
        "그 변화가 수입 구조도 바꿉니다. 가까운 관계에서 맡는 몫도 달라집니다."
    ),
    "near_years_luck": (
        "가까운 연도 운세에서는 돈 문제가 강해지는 해가 따로 나옵니다. "
        "일의 문제도 해마다 다른 모양으로 커집니다. "
        "관계 문제는 그다음 선택으로 넘어갑니다. "
        "해마다 강한 영역이 달라지므로 좋은 해와 신중한 해가 따로 갈라집니다."
    ),
    "monthly_key_timing": (
        "월별 운세는 한 해 안에서 사건이 강해지는 달을 짚는 부분입니다. "
        "좋은 달에는 일이 앞당겨집니다. 부담이 큰 달에는 계약과 관계 문제가 더 차분하게 처리됩니다."
    ),
    "native_career": (
        "당신은 맡은 일로 밖에서 인정받을 때 직업운이 크게 강해지는 사람입니다. "
        "책임이 커질수록 주변에서 당신의 실력을 더 분명히 봅니다. "
        "결정권이 함께 주어지는 자리에서는 맡은 일로 실력을 인정받습니다."
    ),
    "career_precision": (
        "직업운의 핵심은 책임의 크기보다 그 일로 어떤 인정을 받는지입니다. "
        "맡는 범위가 정리되면 업무 판단이 빨라집니다. "
        "대가가 늦게 정해지면 피로가 쌓입니다."
    ),
    "annual_career": (
        "맡은 일이 눈에 띄게 바뀝니다. "
        "새 역할이 주어집니다. "
        "업무 범위를 초기에 잡아야 부담이 커지지 않습니다."
    ),
    "career_fit_fields": (
        "잘 맞는 분야에서는 일의 순서를 잡는 능력이 잘 보입니다. "
        "협업을 정리하고 일정이 움직이게 만드는 역할에서 강점이 큽니다. "
        "현재 직업명과 달라도 업무 안의 역할이 맞으면 직업운이 강해집니다."
    ),
    "career_mismatch_conditions": (
        "맞지 않는 업무 장면에서는 노력보다 소모가 커집니다. "
        "권한 없이 책임만 커지는 자리는 피합니다. "
        "기준이 자주 바뀌는 자리도 우선순위를 낮춥니다."
    ),
    "organization_success_method": (
        "조직 안에서는 상사의 기대와 협업 기준을 빨리 읽습니다. "
        "맡은 일이 문서와 결과물로 남을수록 인정도 빨라집니다. "
        "권한이 분명한 자리에서는 책임이 부담으로만 남지 않습니다."
    ),
    "expertise_recognition_method": (
        "전문성은 아는 양보다 보이는 형태에서 인정됩니다. "
        "보고서, 자격, 발표, 교육 자료처럼 남는 결과물이 평가의 근거가 됩니다. "
        "말보다 증거가 더 빨리 인정받습니다."
    ),
    "social_success_potential": (
        "사회적 성공은 맡는 자리와 책임이 함께 커질 때 강해집니다. "
        "맡은 역할이 밖에서 보이면 다음 역할도 맡게 됩니다. "
        "평판은 해낸 일이 반복해서 확인될 때 단단해집니다."
    ),
    "leadership_potential": (
        "리더십은 목소리보다 역할 배분에서 신뢰를 얻습니다. "
        "사람마다 맡을 일을 분명히 정할 때 팀이 안정됩니다. "
        "결정권이 따라오는 자리에서 리더십을 인정받습니다."
    ),
    "academic_expertise_achievement": (
        "학문과 전문성은 지식이 쌓이는 데서 끝나지 않습니다. "
        "자격, 연구, 분석, 교육 자료처럼 확인 가능한 형태로 남을 때 인정이 커집니다. "
        "전문성은 결과물로 보일 때 평가가 빨라집니다."
    ),
}

ENTRY_CAUTION_SENTENCES: dict[str, str] = {
    "native_money": (
        "돈이 들어오는 순간만 보고 지출 계획을 늦추면 손에 남는 돈이 줄어듭니다. "
        "수입이 확정될 때 보유할 돈과 빠져나갈 돈이 바로 구분됩니다."
    ),
    "money_attitude": (
        "돈을 쓸 명분이 약한데도 지출을 먼저 결정하면 남는 금액이 줄어듭니다. "
        "특히 기분에 따른 소비와 목적이 불분명한 투자는 한도가 먼저 정해집니다."
    ),
    "native_wealth_level": (
        "선천 재물운이 있어도 자산으로 남기는 절차가 약하면 손에 남는 돈이 늦게 늘어납니다. "
        "수입이 커지는 시기에는 생활비가 먼저 분리됩니다. 예비 자금도 따로 남게 됩니다."
    ),
    "income_expansion_method": (
        "수입이 커지는 자리에서는 일을 더 맡는 만큼 단가도 함께 올라갑니다. "
        "지급일이 분명해질 때 손에 남는 수입이 커집니다. 역할만 늘고 대가가 그대로라면 수입운이 피로로 바뀝니다."
    ),
    "wealth_retention_conditions": (
        "남길 돈을 늦게 떼어 두면 지출이 먼저 자리를 차지합니다. "
        "받은 뒤에 남기려 하기보다, 받기 전부터 남길 금액이 정해집니다."
    ),
    "money_leak_conditions": (
        "손실이 생기는 지점에서는 작은 예외가 곧 실제 부담이 됩니다. "
        "지급일이 느슨해져 받을 돈이 늦어집니다. "
        "나눌 몫과 남길 돈이 흐려져 손에 남는 돈이 줄어듭니다."
    ),
    "wealth_potential": (
        "기회를 크게 보더라도 회수 절차가 약하면 재물을 키울 기회가 손실로 바뀝니다. "
        "돈이 될 만한 일에서는 들어오는 금액과 빠져나갈 비용을 따로 계산하게 됩니다."
    ),
    "income_expansion_power": (
        "보상이 함께 올라가야 수입이 제대로 커집니다. "
        "일을 많이 해내고도 금액이 정해지지 않으면 수입은 기대보다 작아집니다. "
        "지급일이 늦게 정해져도 손에 남는 수입이 줄어듭니다."
    ),
    "asset_retention_power": (
        "생활비와 투자 규모가 함께 커지는 시기에는 자산이 늦게 쌓입니다. "
        "수입이 늘어나는 시기에도 고정비와 예비 자금이 먼저 지켜집니다."
    ),
    "investment_trade_sense": (
        "투자와 거래에서는 수익이 좋아 보여도 빠져나올 길이 없으면 부담이 커집니다. "
        "계약 구조를 꼼꼼히 봅니다. 손실 한도를 정한 뒤에 재물운이 안정됩니다. 회수 절차도 따로 따집니다."
    ),
    "business_expansion_power": (
        "확장을 서두르면 매출보다 비용과 책임이 먼저 커집니다. "
        "거래처, 인력, 고정비가 관리 가능한 범위 안에 들어와야 이익으로 남습니다."
    ),
    "money_caution_years": (
        "이 시기에는 금액이 커 보이는 제안일수록 확인이 늦어집니다. "
        "계약서를 확인하지 않으면 손에 남는 돈이 줄어듭니다. "
        "세금과 지급일도 이 시기에는 따로 보아야 합니다."
    ),
    "annual_money": (
        "올해는 받을 돈이 보여도 정산 방식이 늦어지면 손에 남는 돈이 줄어듭니다. "
        "지급일과 지출 한도가 먼저 정해지며 돈이 들어온 뒤에도 흔들리지 않습니다."
    ),
    "native_career": (
        "일은 많아지는데 결정권이 늦게 주어지면 부담만 커집니다. "
        "무엇으로 평가받는지가 흐리면 해낸 일이 좋은 인정으로 돌아오지 않습니다."
    ),
    "career_precision": (
        "맡는 범위와 대가가 어긋나면 일을 해내고도 피로가 커집니다. "
        "권한이 늦게 정해지면 결정의 부담만 먼저 생깁니다."
    ),
    "annual_career": (
        "올해는 새 역할이 들어오는 만큼 맡을 일과 맡지 않을 일을 다시 나눕니다. "
        "맡을 일과 맡지 않을 일을 늦게 나누면 부담이 빠르게 늘어납니다."
    ),
    "career_fit_fields": (
        "잘 맞는 분야라도 책임 범위가 모호하면 적성이 충분히 쓰이지 않습니다. "
        "기준이 자주 바뀌는 자리에서는 강점보다 피로가 커집니다."
    ),
    "career_mismatch_conditions": (
        "맞지 않는 업무 장면에서는 노력보다 소모가 커집니다. "
        "권한 없이 책임만 커지는 자리는 피합니다. "
        "기준이 자주 바뀌는 자리도 우선순위를 낮춥니다."
    ),
    "organization_success_method": (
        "조직 안에서 기대가 계속 바뀌면 실력을 인정받기 어렵습니다. "
        "보고 기준이 흐리면 해낸 일도 개인의 부담으로 남습니다."
    ),
    "expertise_recognition_method": (
        "전문성이 있어도 결과물로 남기지 않으면 인정이 늦어집니다. "
        "자료와 증거가 약하면 설명만 길어지고 평가가 흐려집니다."
    ),
    "social_success_potential": (
        "사회적 역할이 커지는 시기에는 기대도 함께 커집니다. "
        "약속한 범위를 흐리게 두면 인정이 부담으로 바뀝니다."
    ),
    "reputation_success": (
        "명예·성공운이 강한 사람에게는 평판 관리도 더 신중해집니다. "
        "해낸 일이 커지는 자리에서는 책임 범위를 먼저 나눕니다. 공식 평가가 잡히면 인정을 받습니다."
    ),
    "honor_reputation": (
        "명예운은 빠른 인정만으로 끝나지 않습니다. "
        "해낸 일을 문서, 결과물, 공식 평가로 남기지 않으면 평판이 기대만큼 오래 유지되지 않습니다."
    ),
    "leadership_potential": (
        "사람의 역할을 나누지 못하면 리더십이 개인 부담으로 바뀝니다. "
        "책임만 맡고 결정권을 받지 못하면 팀 안에서 소모가 커집니다."
    ),
    "academic_expertise_achievement": (
        "지식이 많아도 확인 가능한 결과물이 없으면 인정이 늦어집니다. "
        "자격, 문서, 발표 자료가 약하면 전문성이 충분히 보이지 않습니다."
    ),
    "long_term_years": (
        "큰돈이 들어오는 해에는 결정도 함께 커집니다. "
        "투자와 세금이 따로 갈라집니다. 생활비와 다음 사업비도 구분됩니다. 이 구분이 늦어지면 큰 수입이 지나간 뒤 남는 금액이 작아집니다."
    ),
}

ENTRY_AXIS_LABELS: dict[str, tuple[str, ...]] = {
    "native_money": ("재물 잠재력", "자산 유지력", "수입 확대력"),
    "native_wealth_level": ("재물 잠재력", "자산 유지력"),
    "money_attitude": ("현실 설계력", "재물 잠재력"),
    "wealth_potential": ("재물 잠재력",),
    "income_expansion_power": ("수입 확대력",),
    "income_expansion_method": ("수입 확대력", "현실 설계력"),
    "asset_retention_power": ("자산 유지력",),
    "wealth_retention_conditions": ("자산 유지력", "현실 설계력"),
    "investment_trade_sense": ("투자와 거래 감각",),
    "business_expansion_power": ("사업 확장력", "수입 확대력"),
    "business_expansion": ("사업 확장력", "수입 확대력", "사회적 성공 잠재력"),
    "independence_business_potential": ("사업 확장력", "리더십 잠재력", "재물 잠재력", "현실 설계력"),
    "leadership_potential": ("리더십 잠재력", "책임 감당력", "대인 영향력"),
    "academic_expertise_achievement": ("학문·전문성 성취력", "직업적 성취력", "명예운"),
    "money_leak_conditions": ("수입 확대력", "투자와 거래 감각", "자산 유지력"),
    "native_career": ("사회적 성공 잠재력", "직업적 성취력", "책임 감당력"),
    "career_precision": ("직업적 성취력", "사회적 성공 잠재력"),
    "social_success_potential": ("사회적 성공 잠재력",),
    "reputation_success": ("명예운", "평판 유지력", "사회적 성공 잠재력"),
    "honor_reputation": ("명예운", "평판 유지력"),
    "leadership_potential": ("리더십 잠재력", "책임 감당력"),
    "social_influence": ("대인 영향력", "평판 유지력"),
    "academic_expertise_achievement": ("학문·전문성 성취력", "직업적 성취력"),
    "native_love": ("대인 영향력", "관계 안정성", "표현 전달력"),
    "love_precision": ("대인 영향력", "관계 안정성", "표현 전달력"),
    "native_marriage": ("결혼 안정성", "관계 안정성", "가족 책임감"),
    "marriage_precision": ("결혼 안정성", "가족 책임감", "관계 안정성"),
    "marriage_stability_conditions": ("결혼 안정성", "가족 책임감"),
    "spouse_conflict_points": ("갈등 회복력", "표현 전달력", "관계 안정성"),
    "children_family_luck": ("가족 책임감", "결혼 안정성"),
    "relationship_social": ("대인 영향력", "관계 안정성", "갈등 회복력"),
    "personality_overview": ("현실 설계력", "변화 적응력", "표현 전달력"),
    "life_strength_balance": ("사회적 성공 잠재력", "재물 잠재력", "결혼 안정성"),
}

MONEY_ENTRIES = {
    "native_money",
    "money_attitude",
    "native_wealth_level",
    "income_expansion_method",
    "wealth_retention_conditions",
    "money_leak_conditions",
    "wealth_potential",
    "income_expansion_power",
    "asset_retention_power",
    "investment_trade_sense",
    "business_expansion_power",
    "money_caution_years",
    "annual_money",
}

MONEY_DETAIL_ENTRIES = {
    "native_money",
    "money_attitude",
    "native_wealth_level",
    "income_expansion_method",
    "wealth_retention_conditions",
    "money_leak_conditions",
    "wealth_potential",
    "income_expansion_power",
    "asset_retention_power",
    "investment_trade_sense",
    "business_expansion_power",
    "money_caution_years",
    "annual_money",
}

CAREER_ENTRIES = {
    "native_career",
    "career_precision",
    "career_fit_fields",
    "career_mismatch_conditions",
    "organization_success_method",
    "expertise_recognition_method",
    "independence_business_potential",
    "social_success_potential",
    "honor_reputation",
    "leadership_potential",
    "business_expansion",
    "business_expansion_power",
    "academic_expertise_achievement",
    "annual_career",
    "reputation_success",
}

RELATIONSHIP_ENTRIES = {
    "native_love",
    "native_marriage",
    "relationship_social",
    "love_precision",
    "marriage_precision",
    "spouse_conflict_points",
    "marriage_stability_conditions",
    "children_family_luck",
    "annual_love",
}

NATAL_BASIS_ENTRY_IDS = {
    "native_money",
    "native_career",
    "native_love",
    "native_marriage",
}

LOVE_ENTRY_IDS = {"native_love", "love_precision", "relationship_social", "annual_love", "social_influence"}
MARRIAGE_ENTRY_IDS = {
    "native_marriage",
    "marriage_precision",
    "spouse_conflict_points",
    "marriage_stability_conditions",
    "children_family_luck",
}

TIMING_ENTRIES = {
    "annual_good_timing",
    "annual_caution_timing",
    "timing_detail",
    "long_term_years",
    "ten_year_luck",
    "near_years_luck",
    "monthly_key_timing",
    "favorable_timing",
    "caution_timing",
}

FACTOR_BRIDGE_ENTRY_IDS = {
    "money_attitude",
    "native_wealth_level",
    "income_expansion_method",
    "wealth_retention_conditions",
    "money_leak_conditions",
    "wealth_potential",
    "income_expansion_power",
    "asset_retention_power",
    "investment_trade_sense",
    "money_caution_years",
    "long_term_years",
    "career_precision",
    "career_fit_fields",
    "career_mismatch_conditions",
    "organization_success_method",
    "expertise_recognition_method",
    "independence_business_potential",
    "social_success_potential",
    "honor_reputation",
    "leadership_potential",
    "business_expansion",
    "academic_expertise_achievement",
    "relationship_social",
    "love_precision",
    "marriage_precision",
    "spouse_conflict_points",
    "marriage_stability_conditions",
    "children_family_luck",
    "health_life_management",
    "final_money_work_relationship_advice",
    "premium_core_five",
}


def attach_catalog_content_blocks(
    catalog_entries: list[dict[str, object]],
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
    product_tier: str = "basic",
) -> list[dict[str, object]]:
    """Return catalog entries enriched with stable customer content blocks."""

    enriched: list[dict[str, object]] = []
    for entry in catalog_entries:
        payload = dict(entry)
        entry_items = _items_for_catalog_entry(str(payload.get("entry_id") or ""), items)
        blocks = _content_blocks_for_entry(payload, entry_items, life_feature_summary, target_years)
        blocks = _add_dedicated_catalog_blocks(payload, blocks, entry_items, life_feature_summary, target_years)
        blocks = _add_factor_bridge_catalog_blocks(payload, blocks, life_feature_summary, product_tier)
        blocks = _expand_catalog_content_blocks(payload, blocks, entry_items, life_feature_summary, target_years)
        blocks = _enrich_catalog_content_block_bodies(payload, blocks, entry_items, life_feature_summary, target_years)
        payload["content_blocks"] = blocks
        payload["content_summary"] = _content_summary(blocks, str(payload.get("preview") or ""))
        enriched.append(payload)
    return enriched


def _items_for_catalog_entry(entry_id: str, items: list[ProductOutputItem]) -> list[ProductOutputItem]:
    if entry_id not in ANNUAL_ENTRY_IDS:
        return items
    current_items = [item for item in items if str(item.period_label) == str(CURRENT_FORTUNE_YEAR)]
    return current_items


def _content_summary(blocks: list[ContentBlock], fallback: str) -> str:
    bodies = [_compact(str(block.get("body") or "")) for block in blocks]
    readable = [body for body in bodies if body]
    dedicated = [
        _compact(str(block.get("body") or ""))
        for block in blocks
        if "-dedicated-" in str(block.get("block_id") or "") and str(block.get("body") or "").strip()
    ]
    if readable:
        if dedicated and dedicated[0] != readable[0]:
            return _compact(" ".join([readable[0], dedicated[0]]))
        return _compact(" ".join(readable[:2]))
    return _compact(fallback)


def _add_dedicated_catalog_blocks(
    entry: dict[str, object],
    blocks: list[ContentBlock],
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    if bool(entry.get("is_locked")):
        return blocks

    entry_id = str(entry.get("entry_id") or "")
    profile = DEDICATED_CATALOG_BLOCK_PROFILES.get(entry_id)
    if not profile:
        return blocks

    title = str(entry.get("title") or "운세")
    expanded = list(blocks)
    roles = {str(block.get("role") or "") for block in expanded}
    domains = _entry_domains(entry, expanded)
    item = _best_item_for_entry(domains, items)
    axes = _entry_axes(entry_id, domains, item, life_feature_summary)
    context = _dedicated_block_context(entry_id, title, domains, axes, item, target_years)

    for role in DEDICATED_BLOCK_ROLE_ORDER:
        if role in roles:
            continue
        template = profile.get(role)
        if not template:
            continue
        body = _dedicated_body_text(template.format(**context))
        body = _dedicated_complete_risk_sentence(role, body, context)
        followup = _dedicated_followup_sentence(role, title, domains, context, entry_id)
        if followup and followup not in body and _catalog_body_sentence_count(body) < 2:
            body = _dedicated_body_text(f"{_sentence_end(body)} {followup}")
        if not body:
            continue
        expanded.append(
            _block(
                f"{entry_id}-dedicated-{role}",
                role,
                DEDICATED_BLOCK_HEADINGS.get(role, "세부 해석"),
                body,
                domains or ((item.domain,) if item else ()),
            )
        )
        roles.add(role)
    return expanded


def _add_factor_bridge_catalog_blocks(
    entry: dict[str, object],
    blocks: list[ContentBlock],
    life_feature_summary: dict[str, Any],
    product_tier: str,
) -> list[ContentBlock]:
    if product_tier != "premium" or bool(entry.get("is_locked")):
        return blocks

    entry_id = str(entry.get("entry_id") or "catalog")
    if entry_id not in FACTOR_BRIDGE_ENTRY_IDS:
        return blocks
    domains = _entry_domains(entry, blocks)
    if not domains:
        return blocks
    domains = _factor_bridge_ordered_domains(entry_id, domains)
    signals = _factor_bridge_signals(life_feature_summary, domains, limit=2)
    if not signals:
        return blocks

    title = str(entry.get("title") or "운세")
    body = _factor_bridge_sentence(title, domains, signals)
    if not body:
        return blocks
    return list(blocks) + [
        _block(
            f"{entry_id}-factor-bridge",
            "factor_bridge",
            "사주에서 보이는 세부 단서",
            body,
            domains,
        )
    ]


def _factor_bridge_signals(
    life_feature_summary: dict[str, Any],
    domains: tuple[Domain, ...],
    limit: int,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key in FACTOR_BRIDGE_SIGNAL_KEYS:
        raw_signals = life_feature_summary.get(key)
        if not isinstance(raw_signals, list):
            continue
        selected_for_layer = False
        for signal in raw_signals:
            if not isinstance(signal, dict) or not _factor_signal_matches_domains(signal, domains):
                continue
            title = _factor_signal_title(key, signal)
            core = _factor_signal_core_sentence(key, signal, domains)
            if not title or not core:
                continue
            dedupe_key = f"{key}:{title}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            results.append((title, core))
            selected_for_layer = True
            if len(results) >= limit:
                return results
            break
        if selected_for_layer and len(results) >= limit:
            return results
    return results


def _factor_signal_matches_domains(signal: dict[str, Any], domains: tuple[Domain, ...]) -> bool:
    links = {str(domain) for domain in signal.get("domain_links", [])}
    return bool(links.intersection(domains))


def _factor_bridge_ordered_domains(entry_id: str, domains: tuple[Domain, ...]) -> tuple[Domain, ...]:
    if entry_id in MONEY_ENTRIES or entry_id == "long_term_years":
        primary: Domain = "money"
    elif entry_id in CAREER_ENTRIES:
        primary = "career"
    elif entry_id in MARRIAGE_ENTRY_IDS:
        primary = "marriage"
    elif entry_id in LOVE_ENTRY_IDS or entry_id in RELATIONSHIP_ENTRIES:
        primary = "love"
    else:
        primary = domains[0]
    ordered = [primary] + [domain for domain in domains if domain != primary]
    return tuple(_unique(ordered))


def _factor_signal_title(key: str, signal: dict[str, Any]) -> str:
    if key == "top_element_combination_signals":
        stems = [str(stem) for stem in signal.get("stems", []) if str(stem).strip()]
        title = "".join(_stem_label(stem) for stem in stems)
        return f"{title} 오행 배합" if title else ""
    if key == "top_stem_reception_signals":
        day_stem = _stem_label(str(signal.get("day_stem") or ""))
        target_stem = _stem_label(str(signal.get("target_stem") or ""))
        ten_god = _ten_god_label(str(signal.get("target_ten_god") or ""))
        if not day_stem or not target_stem or not ten_god:
            return ""
        return f"{day_stem}일간-{target_stem} {ten_god} 관계"
    if key == "top_ten_god_interaction_signals":
        source = _ten_god_label(str(signal.get("source_ten_god") or ""))
        target = _ten_god_label(str(signal.get("target_ten_god") or ""))
        if not source or not target:
            return ""
        return f"{source}-{target} 십신 관계"
    if key == "top_integrated_saju_signals":
        source = _stem_label(str(signal.get("source_stem") or ""))
        target = _stem_label(str(signal.get("target_stem") or ""))
        title = f"{source}{target}" if source and target else ""
        return f"{title} 오행·십신 통합" if title else ""
    return ""


def _factor_signal_core_sentence(
    key: str,
    signal: dict[str, Any],
    domains: tuple[Domain, ...],
) -> str:
    domain = domains[0]
    if key in {"top_stem_reception_signals", "top_integrated_saju_signals"}:
        projection = signal.get("domain_projection")
        if isinstance(projection, dict):
            projected = _first_sentence(projection.get(domain))
            if projected:
                return projected
    if key == "top_element_combination_signals":
        return _first_sentence(signal.get("interpretation")) or _first_sentence(signal.get("day_master_variant_note"))
    if key == "top_ten_god_interaction_signals":
        return _first_sentence(signal.get("interpretation"))
    if key == "top_stem_reception_signals":
        return _first_sentence(signal.get("core_interpretation")) or _first_sentence(signal.get("felt_experience"))
    if key == "top_integrated_saju_signals":
        return _first_sentence(signal.get("combined_interpretation")) or _first_sentence(signal.get("core_interpretation"))
    return ""


def _factor_bridge_sentence(title: str, domains: tuple[Domain, ...], signals: list[tuple[str, str]]) -> str:
    domain = domains[0]
    factor_titles = _join_korean([signal_title for signal_title, _ in signals])
    tail = _factor_bridge_lead_sentence(title, domain, factor_titles)
    return _compact(tail or _factor_bridge_title_sentence(title, domain))


def _factor_bridge_domain_phrase(domain: Domain) -> str:
    return {
        "money": "돈 문제의 핵심 단서로",
        "career": "직업 문제의 핵심 단서로",
        "love": "연애 문제의 핵심 단서로",
        "marriage": "결혼 문제의 핵심 단서로",
    }[domain]


def _factor_bridge_lead_sentence(title: str, domain: Domain, factor_titles: str) -> str:
    if "건강운" in title or "생활 관리" in title:
        return "무리가 쌓이는 생활 장면이 분명합니다. 회복 순서도 따로 잡힙니다."
    if "최종 조언" in title:
        return "먼저 잡을 선택과 신중하게 미룰 선택이 분명합니다."
    if "핵심 결론" in title:
        return "먼저 살릴 장점과 줄여야 할 부담이 분명합니다."
    if domain == "money":
        if "태도" in title:
            return "돈을 쓰기 전 목적과 한도를 먼저 정합니다."
        if "선천" in title or "수준" in title:
            return "평생 들어오는 돈보다 손에 남는 돈을 더 크게 봅니다."
        if "수입" in title:
            return "해낸 일이 금액으로 인정되며 수입이 커집니다."
        if "남는" in title or "유지" in title or "자산" in title:
            return "수입이 들어온 뒤 고정비와 저축 순서가 바로 나뉩니다."
        if "새" in title or "조심" in title:
            return "정산이 늦거나 지출 한도가 흐리면 손실이 바로 커집니다."
        if "투자" in title or "거래" in title:
            return "계약서와 회수 시점이 분명해야 돈을 지킵니다."
        if "큰돈" in title or "연도" in title:
            return "수입 규모가 커질 때에는 계약과 세금 문제도 함께 커집니다."
        return "들어오는 돈과 손에 남는 돈의 차이가 크게 납니다."
    if domain == "career":
        if "직업 분야" in title:
            return "당신에게 맞는 일은 직함보다 실제로 맡는 역할에서 분명합니다."
        if "맞지" in title:
            return "능력이 있어도 소모가 먼저 쌓이는 업무 장면이 있습니다."
        if "조직" in title:
            return "조직 안에서는 결과가 기록으로 남을 때 인정이 빨라집니다."
        if "전문성" in title or "학문" in title:
            return "지식과 경험이 문서나 결과물로 남을 때 인정이 커집니다."
        if "독립" in title or "사업" in title:
            return "독립해서 일하면 계약과 비용을 직접 관리할 때 매출이 커집니다."
        if "명예" in title or "평판" in title:
            return "해낸 일이 밖에서 확인될 때 평판이 올라갑니다."
        return "결정권이 분명한 자리에서 능력을 제대로 인정받습니다."
    if domain == "love":
        if "대인" in title:
            return "호의가 있어도 거리감이 맞아야 관계가 편안합니다."
        return "호감이 생긴 뒤에는 연락과 표현이 관계의 속도를 바꿉니다."
    if domain == "marriage":
        if "부딪" in title:
            return "애정보다 생활 방식에서 충돌이 먼저 생깁니다."
        if "안정" in title:
            return "애정이 생활의 약속으로 옮겨질 때 결혼 생활이 안정됩니다."
        if "자식" in title or "가정" in title:
            return "가족을 챙기는 마음이 커질수록 결혼 뒤의 역할 분담도 중요해집니다."
        return "결혼운은 애정만으로 안정되지 않습니다. 생활 방식이 맞춰지면서 결혼 생활이 오래 갑니다."
    return "선택한 방향은 생활 속 선택에서 바로 확인됩니다."


def _factor_bridge_title_sentence(title: str, domain: Domain) -> str:
    if "건강운" in title or "생활 관리" in title:
        return "이 조합은 과로, 일정 부담, 관계 피로가 생활 관리에서 어디에 쌓이는지 드러냅니다."
    if "최종 조언" in title:
        return "이 조합은 선택의 우선순위를 정합니다."
    if "핵심 결론" in title:
        return "이 조합에서는 살릴 강점과 줄일 부담이 나뉩니다."
    if domain == "money":
        if "태도" in title:
            return "돈을 쓰기 전 목적을 먼저 따지는 성향입니다. 한도와 회수 절차도 같이 정합니다."
        if "선천" in title or "수준" in title:
            return "큰돈이 한 번 들어오는 것보다 들어온 돈이 오래 남는 쪽에 무게가 실립니다."
        if "수입" in title:
            return "맡은 역할이 커지고 받을 몫이 함께 올라갈 때 수입도 커집니다."
        if "남는" in title or "유지" in title or "자산" in title:
            return "수입 이후의 순서를 중시합니다. 고정비를 줄이면 자산이 남습니다. 저축할 금액이 분명할수록 보유 금액도 커집니다."
        if "새" in title or "조심" in title:
            return "느슨한 계약과 늦은 정산에서 손실이 생기기 쉽습니다. 생활비와 운영비도 따로 관리해야 합니다."
        if "투자" in title or "거래" in title:
            return "수익률보다 계약 구조와 회수 절차를 꼼꼼히 봅니다. 손실 한도도 크게 잡습니다."
        if "큰돈" in title or "연도" in title:
            return "수입 규모가 커질 때에는 계약과 세금 문제도 함께 커집니다. 지급일과 보유할 금액도 결론을 바꿉니다."
        return "이 조합은 돈이 들어오는 자리와 손에 남는 돈 사이의 차이를 설명합니다."
    if domain == "career":
        if "직업 분야" in title:
            return "직함보다 실제 역할에서 강점이 분명합니다. 일정 관리에서 실력이 잘 보입니다. 사람을 조율하는 자리에서도 능력을 인정받습니다."
        if "맞지" in title:
            return "능력이 있어도 결정권이 없고 책임만 커지는 자리에서는 소모가 커집니다."
        if "조직" in title:
            return "조직 안에서는 협업 방식이 분명할 때 실력을 인정받습니다. 결과물이 보이면 평가가 빨라집니다. 책임 범위가 분명한 자리에서도 강합니다."
        if "전문성" in title or "학문" in title:
            return "지식이나 경험을 문서, 자격, 분석 자료처럼 보이는 형태로 만들 때 인정이 커집니다."
        if "독립" in title or "사업" in title:
            return "독립해서 일하더라도 계약, 비용, 일정, 책임 범위를 직접 관리할 때 수익과 평가가 커집니다."
        if "명예" in title or "평판" in title:
            return "말보다 결과물과 책임 이행이 평판을 만듭니다."
        return "맡는 역할이 직업적 평가를 만듭니다. 무엇으로 평가받는지도 일의 결론을 바꿉니다."
    if domain == "love":
        if "대인" in title:
            return "이 조합은 호의를 주고받는 자리에서도 기대치와 거리감이 먼저 갈린다는 뜻입니다."
        return "이 조합은 호감이 생긴 뒤 연락이 핵심 장면으로 올라온다는 뜻입니다. 표현 방식도 달라집니다."
    if domain == "marriage":
        if "부딪" in title:
            return "이 조합은 애정의 부족보다 돈 문제에서 충돌이 생긴다는 뜻입니다. 주거 문제도 따로 다룹니다."
        if "안정" in title:
            return "이 조합은 애정이 생활의 약속으로 옮겨질 때 결혼 생활이 안정된다는 뜻입니다."
        if "자식" in title or "가정" in title:
            return "이 조합은 가까운 사람을 챙기는 마음과 책임 분담이 함께 올라온다는 뜻입니다."
        return "이 조합은 애정과 생활 방식이 함께 결혼운의 안정성을 만든다는 뜻입니다."
    return "이 조합은 해당 영역에서 어떤 선택이 현실의 일로 이어지는지를 설명합니다."


def _first_sentence(text: object) -> str:
    body = _factor_bridge_clean(str(text or ""))
    if not body:
        return ""
    sentences = [part.strip() for part in body.replace("?", ".").replace("!", ".").split(".") if part.strip()]
    if not sentences:
        return ""
    return _sentence_end(sentences[0])


def _factor_bridge_clean(text: str) -> str:
    body = _dedicated_body_text(text)
    replacements = (
        ("자신의 역량을 드러내려는", "자신의 활동 범위를 넓히려는"),
        ("실제 체감은", "체감상"),
        ("의 과제로 들어옵니다", "의 문제로 이어집니다"),
        ("戊의 판단은 己이", "戊의 성향은 己가"),
        ("己의 판단은 戊이", "己의 성향은 戊가"),
        ("丙의 판단은 癸이", "丙의 성향은 癸가"),
        ("丙의 판단은 丁이", "丙의 성향은 丁이"),
        ("丙의 판단은 戊이", "丙의 성향은 戊가"),
    )
    for old, new in replacements:
        body = body.replace(old, new)
    return _compact(body)


def _stem_label(stem: str) -> str:
    return STEM_HANJA.get(stem, stem)


def _ten_god_label(ten_god: str) -> str:
    return TEN_GOD_LABELS.get(ten_god, ten_god)


def _dedicated_complete_risk_sentence(role: str, body: str, context: dict[str, str]) -> str:
    risk = _compact(context.get("risk") or "")
    if role != "caution" or not body or not risk:
        return body
    if _compact(body) != risk:
        return body
    return f"가장 주의할 부분은 {risk}입니다."


def _dedicated_body_text(text: object) -> str:
    body = _compact(str(text or ""))
    replacements = (
        ("이 항목은 ", ""),
        ("더 무겁게 봅니다", "더 강하게 반영됩니다"),
        ("더 무겁게 보아 판단합니다", "더 강하게 반영됩니다"),
        ("결과로 남을 힘이 큰 것", "돈과 평가로 돌아올 일이 큰 것"),
        ("돈이 들어오는 힘", "돈이 들어오는 자리"),
        ("힘과 보존하는 힘", "능력과 보존 능력"),
        ("힘을 정하지 않으면", "장점을 정하지 않으면"),
        ("힘이 강해지는 정도", "강해지는 정도"),
        ("힘을 더", "능력을 더"),
        ("힘입니다", "능력입니다"),
        ("이 장점이 잘 쓰이면", "이 장점을 제대로 쓰면"),
        ("이 장점을 잘 쓰면", "이 장점을 제대로 쓰면"),
        ("잘 쓰이면", "제대로 쓰이면"),
        ("잘 쓸 때", "제대로 쓸 때"),
        ("상대에게 신뢰를 주는 태도을 제대로 쓸 때", "상대에게 신뢰를 주는 태도가 분명할 때"),
        ("충돌 뒤 다시 대화하는 태도을 제대로 쓸 때", "충돌 뒤 다시 대화하는 태도가 분명할 때"),
        ("상대에게 신뢰를 주는 태도을 크게 쓰는 사람입니다", "상대에게 신뢰를 주는 태도가 뚜렷한 사람입니다"),
        ("충돌 뒤 다시 대화하는 태도을 크게 쓰는 사람입니다", "충돌 뒤 다시 대화하는 태도가 뚜렷한 사람입니다"),
        ("상대에게 신뢰를 주는 태도을 중심에 둘 때", "상대에게 신뢰를 주는 태도가 중심에 설 때"),
        ("충돌 뒤 다시 대화하는 태도을 중심에 둘 때", "충돌 뒤 다시 대화하는 태도가 중심에 설 때"),
        ("태도을", "태도를"),
        ("태도은", "태도는"),
        ("태도이", "태도가"),
        ("태도과", "태도와"),
        ("당신의 사주에서는 사회적으로 인정받는 기질이 강합니다.", "당신의 사주에는 사회적으로 인정받을 자리가 분명합니다."),
        ("당신의 직업운에서는 사회적으로 인정받는 기질이 강합니다. 이 장점이 강해질수록 해낸 일로 인정받고 보상도 커집니다.", "당신의 직업운은 사회적으로 인정받는 자리에서 강합니다. 해낸 일로 인정받고 보상도 커집니다."),
        ("당신은 공식 평가에서 인정받는 기질이 강해질수록 해낸 일로 주변의 인정을 받습니다.", "당신은 공식 평가가 따르는 자리에서 해낸 일로 주변의 인정을 받습니다."),
        ("사회적으로 인정받는 기질은 상위", "사회적 인정운은 상위"),
        ("공식 평가에서 인정받는 기질은 상위", "공식 평가와 명예운은 상위"),
        ("돈과 일의 기준을 먼저 세우는 성향이 강해질 때", "돈과 일의 기준이 분명해질 때"),
        ("돈과 일의 기준을 먼저 세우는 성향이 강합니다", "돈과 일의 기준을 먼저 세우는 성향이 뚜렷합니다"),
        ("상황 변화에 맞춰 행동을 바꾸는 성향이 강해질 때", "상황 변화에 대한 판단이 빨라질 때"),
        ("상황 변화에 맞춰 행동을 바꾸는 성향이 강합니다", "상황 변화에 맞춰 행동을 바꾸는 성향이 뚜렷합니다"),
        ("성향이 강해질 때", "성향이 분명해질 때"),
        ("성향이 강해지면", "성향이 분명해지면"),
        ("이 장점이 강해질수록", "이 장점이 분명할수록"),
        ("이 장점이 강해지면", "이 장점이 분명해지면"),
        ("살아날수록", "살아날수록"),
        ("살아나면", "살아나면"),
        ("살아날 때", "살아날 때"),
        ("실제 자산", "자산"),
        ("실제 관계", "구체적인 관계"),
        ("실제 성취", "직업적 인정"),
        ("성공운의 핵심입니다", "성공운에서 가장 먼저 힘을 씁니다"),
        ("직업 성취의 중심입니다", "직업운을 강하게 만드는 장점입니다"),
        ("사회적 자리를 키우는 핵심입니다", "사회적 위치를 키우는 기준입니다"),
        ("재물 수준을 올리는 핵심입니다", "재물 수준을 올리는 기준입니다"),
        ("중요한 단서가 됩니다", "장기 선택의 기준이 됩니다"),
        ("나누어 보는 편이 좋습니다", "나누어 정하는 편이 좋습니다"),
        ("나누어 봅니다", "구분해 확인합니다"),
        ("함께 봅니다", "함께 확인합니다"),
        ("살핍니다", "확인합니다"),
        ("재물운의 장점", "재물운에서 유리한 자리"),
        ("선천적인 재물운의 장점", "선천적인 재물운에서 유리한 자리"),
        ("뒷받침합니다", "받쳐 줍니다"),
        ("를 가르는 핵심입니다", "에서 가장 비중이 큽니다"),
        ("가 핵심입니다", "가 가장 중요합니다"),
        ("이 핵심입니다", "이 가장 중요합니다"),
        ("은 핵심입니다", "은 가장 중요합니다"),
        ("가장 중요합니다", "가장 비중이 큽니다"),
        ("중요합니다", "중요합니다"),
        ("할 수 있습니다", "합니다"),
        ("될 수 있습니다", "됩니다"),
        ("줄 수 있습니다", "줄입니다"),
        ("커질 수 있습니다", "커집니다"),
        ("약해질 수 있습니다", "약해집니다"),
        ("작아질 수 있습니다", "작아집니다"),
        ("늦어질 수 있습니다", "늦어집니다"),
        ("흔들릴 수 있습니다", "흔들립니다"),
        ("권한를", "권한을"),
        ("지급 조건", "돈을 받는 기준"),
        ("해야 합니다..", "해야 합니다."),
        ("습니다..", "습니다."),
    )
    for old, new in replacements:
        body = body.replace(old, new)
    targeted = (
        ("속도 조절이 필요합니다", "속도를 낮출수록 부담이 줄어듭니다"),
        ("현실 검증이 필요합니다", "현실 검증을 거쳐야 손해를 줄입니다"),
        ("확인 대화가 필요합니다", "확인 대화가 있어야 관계가 안정됩니다"),
        ("휴식 관리가 필요합니다", "휴식 관리가 될 때 성과가 오래 갑니다"),
        ("관리 기준도 필요합니다", "관리 기준도 함께 서야 이익이 남습니다"),
        ("확인점입니다", "결론이 나는 지점입니다"),
        ("먼저 실행하는 편이 좋습니다", "먼저 실행할 때 기회를 잡습니다"),
        ("나누어 정하는 편이 좋습니다", "나뉘어 정리될 때 일이 안정됩니다"),
        ("기록으로 남기는 편이 좋습니다", "기록으로 남을 때 인정이 이어집니다"),
        ("관리하는 편이 좋습니다", "관리될 때 안정이 오래 갑니다"),
        ("낮추는 편이 좋습니다", "낮아질 때 소모가 줄어듭니다"),
        ("맡는 편이 좋습니다", "맡을수록 강점을 인정받습니다"),
        ("두는 편이 좋습니다", "둘 때 일이 안정됩니다"),
        ("정하는 편이 좋습니다", "정해질수록 일이 안정됩니다"),
        ("보는 편이 좋습니다", "확인할수록 결론이 분명합니다"),
        ("줄이는 편이 좋습니다", "줄어들 때 안정이 생깁니다"),
        ("챙기는 편이 좋습니다", "챙겨질 때 일이 안정됩니다"),
        ("만드는 편이 좋습니다", "만들어질 때 인정받습니다"),
        ("보수적으로 살피는 편이 좋습니다", "보수적으로 살펴야 손실이 줄어듭니다"),
    )
    for old, new in targeted:
        body = body.replace(old, new)
    return _compact(body)


def _dedicated_followup_sentence(
    role: str,
    title: str,
    domains: tuple[Domain, ...],
    context: dict[str, str],
    entry_id: str = "",
) -> str:
    domain_noun = context.get("domain_noun") or _dedicated_domain_noun(domains)
    axis_label = context.get("axis_label") or _dedicated_default_axis_label(domains)
    axis_text = _axis_customer_label(axis_label)
    event = context.get("event") or "중요한 선택 기준"
    action = context.get("action") or "선택의 기준을 먼저 정리하는 일"

    if role == "life_scene":
        return _entry_customer_focus_sentence(title, domains, entry_id)
    if role == "strength":
        return ""
    if role == "score":
        return _dedicated_score_followup_sentence(axis_label, domain_noun, domains)
    if role == "caution":
        return ""
    if role == "action":
        return ""
    if role == "summary":
        return _entry_customer_focus_sentence(title, domains, entry_id)
    if role == "condition":
        return f"{axis_text}이 생활 방식과 함께 움직이며 {domain_noun}운의 안정성이 더 좋아집니다."
    if role in {"timing", "timing_caution"}:
        return f"이 시기에는 {action}이 먼저 실행됩니다. 부담이 커지는 장면은 초기에 줄어듭니다."
    if role == "basis":
        return f"이 근거가 강할수록 {domain_noun}운은 생활에서 바로 보이는 일로 커집니다."
    if role == "advice":
        return f"{axis_text}을 중심에 두면 {domain_noun}운에서 잡을 선택과 미룰 선택이 갈립니다."
    return ""


def _dedicated_score_followup_sentence(axis_label: str, domain_noun: str, domains: tuple[Domain, ...]) -> str:
    axis_text = _axis_customer_label(axis_label)
    if "money" in domains and "career" in domains:
        return f"{axis_text}이 강하게 쓰일수록 일의 성과가 받을 몫으로 이어집니다. 그 대가가 직업 선택의 방향을 정합니다."
    if "love" in domains and "marriage" in domains:
        return f"{axis_text}이 강하게 쓰일수록 감정 표현이 맞춰집니다. 생활 방식도 가까운 관계의 안정감을 키웁니다."
    domain = domains[0] if domains else "money"
    followups = {
        "money": f"{axis_text}은 돈이 들어온 뒤 손에 남는 금액과 연결됩니다. 그래서 {domain_noun}운은 수입보다 정산 방식과 보유할 금액을 더 크게 봅니다.",
        "career": f"{axis_text}에서는 맡는 역할이 평가와 보상으로 이어지는 지점을 봅니다. 그래서 {domain_noun}운은 직업명보다 책임 범위와 인정 방식을 더 크게 봅니다.",
        "love": f"{axis_text}에서는 호감이 생긴 뒤 연락과 표현을 오래 맞춰 갑니다. 그래서 {domain_noun}운은 만남의 수보다 연락과 표현의 안정성이 더 중요합니다.",
        "marriage": f"{axis_text}에서는 애정을 생활의 약속으로 옮기려 합니다. 그래서 {domain_noun}운은 결혼 여부보다 생활 방식에서 더 분명합니다.",
    }
    return followups.get(domain, f"{axis_text}이 강하게 쓰일수록 {domain_noun}운이 생활에서 바로 강해집니다.")


def _dedicated_action_followup_sentence(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "이 부분이 정리되면 일의 성과가 받을 몫으로 이어지고, 커진 책임도 감당 가능한 범위 안에서 처리됩니다."
    if "love" in domains and "marriage" in domains:
        return "이 부분이 정리되면 좋아하는 마음이 생활의 약속으로 굳어지고, 가까워진 관계도 오래 안정됩니다."
    domain = domains[0] if domains else "money"
    followups = {
        "money": "이 부분이 정리되면 받을 돈이 분리됩니다. 남길 돈도 따로 정해지면서 자산으로 쌓입니다.",
        "career": "이 부분이 정리되면 맡은 일의 결과가 평가받는 근거가 됩니다. 책임도 더 분명하게 정리됩니다.",
        "love": "이 부분이 정리되면 호감이 생긴 뒤에도 연락과 만남이 편안하게 이어집니다.",
        "marriage": "이 부분이 정리되면 애정이 생활의 약속으로 옮겨지고, 결혼 생활의 부담이 줄어듭니다.",
    }
    return followups.get(domain, "이 부분이 정리되면 좋은 시기와 조심할 시기가 나뉩니다.")


def _dedicated_caution_followup_sentence(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "책임과 대가가 같은 자리에서 정리되며 성과가 부담으로 바뀌지 않습니다."
    if "love" in domains and "marriage" in domains:
        return "마음의 확인이 분명해지며 가까운 관계가 오래 안정됩니다. 생활 방식도 따로 정리됩니다."
    domain = domains[0] if domains else "money"
    followups = {
        "money": "계약 내용이 늦어지지 않을 때 들어온 돈이 손에 남습니다. 정산 방식도 따로 세우게 됩니다.",
        "career": "책임 범위가 분명하면 인정이 부담으로 바뀌지 않습니다. 결정권도 분명해야 합니다.",
        "love": "기대치가 초기에 정리될수록 같은 오해가 반복되지 않습니다. 표현 방식도 관계의 결론을 바꿉니다.",
        "marriage": "생활비 이야기가 늦어지지 않을 때 약속이 안정됩니다. 주거 문제도 따로 정리됩니다.",
    }
    return followups.get(domain, "주의할 부분이 늦어지지 않을 때 손해와 갈등이 줄어듭니다.")


def _entry_customer_focus_sentence(title: str, domains: tuple[Domain, ...], entry_id: str = "") -> str:
    specific = ENTRY_CUSTOMER_FOCUS_SENTENCES.get(entry_id)
    if specific:
        return specific
    if "money" in domains and "career" in domains:
        return _stable_title_variant(
            f"{entry_id}:{title}",
            (
                "역할이 커지는 시기에는 받을 몫도 커집니다. 맡는 범위가 분명해지며 일의 성과가 돈으로 이어집니다.",
                "일의 범위가 넓어지며 돈 이야기도 함께 커집니다. 권한이 있는 자리에서는 해낸 일을 바탕으로 다음 역할도 맡게 됩니다. 대가가 분명해지며 수입도 흔들리지 않습니다.",
                "해낸 일의 대가가 분명한 자리에서 수입이 커집니다. 지급일이 정해지면 받을 돈도 흔들리지 않습니다.",
                "해낸 일이 기록으로 남는 자리에서 재물운도 강해집니다. 무엇으로 평가받는지가 보이면 받을 돈의 크기도 더 또렷해집니다.",
                "업무의 결과가 숫자로 확인되는 자리에서 수입도 함께 늘어납니다. 성과가 바로 보상으로 이어지는 자리에서 재물운이 강합니다.",
                "맡은 역할이 받을 돈과 바로 연결됩니다. 책임 범위가 분명할수록 보상도 안정됩니다.",
                "일의 성과가 정산 방식으로 이어지는 구조입니다. 평가가 분명하면 수입의 흐트러짐도 줄어듭니다.",
                "권한을 맡는 만큼 받을 몫도 올라갑니다. 다만 대가가 늦게 정해지면 부담이 커집니다.",
            ),
        )
    if "love" in domains and "marriage" in domains:
        return _stable_title_variant(
            f"{entry_id}:{title}",
            (
                "관계가 깊어지며 생활 문제가 함께 커집니다. 마음이 깊어도 돈 문제를 늦게 다루면 서운함이 쌓입니다.",
                "관계가 결혼 문제로 이어지면 생활비 이야기를 먼저 꺼내게 됩니다. 역할 분담을 늦게 꺼내면 부담이 커집니다.",
                "좋아하는 마음만으로 관계와 결혼이 끝나지 않습니다. 연락 방식이 먼저 흔들립니다. 가족과의 거리도 관계의 안정성을 바꿉니다.",
                "마음이 깊어질수록 생활의 약속도 무거워집니다. 돈과 주거 이야기를 늦게 꺼내면 부담이 커집니다.",
                "연애가 결혼으로 가까워지면 말투보다 생활 방식이 크게 보입니다. 역할 분담이 늦어지면 서운함도 오래 갑니다.",
                "관계가 깊어질수록 가족 문제와 생활비 문제도 함께 커집니다. 애정이 있어도 이 부분을 늦게 다루면 마음이 무거워집니다.",
            ),
        )
    domain = domains[0] if domains else "money"
    variants = {
        "money": (
            "재물운은 들어온 돈이 얼마나 남는지에서 판단합니다. 받을 금액이 분명해지며 수입이 자산으로 이어집니다. 지출 한도도 돈을 오래 남깁니다.",
            "돈 문제에서는 기회를 고르는 눈이 먼저 드러납니다. 계약 내용이 분명해지며 수입이 흩어지지 않습니다. 정산 방식도 손에 남는 돈을 키웁니다.",
            "재물운은 수입이 생기는 자리에서 강합니다. 돈이 빠져나가는 자리도 따로 정리되며 자산이 안정됩니다.",
        ),
        "career": (
            "넓은 책임을 맡을수록 직업운이 강해집니다. 맡은 일이 밖에서 보이면 인정도 빠릅니다.",
            "결정할 수 있는 일이 있을 때 판단력이 좋아집니다. 지시만 많은 자리에서는 능력이 늦게 평가됩니다.",
            "자료, 일정, 사람의 역할을 정리하는 자리에서 강점이 큽니다. 결과물이 남으면 평판도 좋아집니다.",
            "공식 평가가 있는 일에서 유리합니다. 확인되는 성과가 있을 때 더 큰 역할도 맡게 됩니다.",
            "협업이 복잡할수록 정리 능력으로 인정받습니다. 여러 사람의 일을 맞추는 자리에서 실력이 보입니다.",
            "대가가 늦게 정해지면 일의 피로가 커집니다. 맡은 범위는 처음부터 정해야 합니다.",
            "직함이 커도 결정권이 없으면 오래 맞지 않습니다. 직접 판단할 수 있는 자리가 직업운을 키웁니다.",
            "기록이 남는 업무에서 강합니다. 말로 설명하는 일보다 결과물을 확인받는 일이 더 유리합니다.",
            "일정과 절차를 잡는 자리에서 집중력이 높아집니다. 책임의 범위가 보이면 일의 속도도 빨라집니다.",
            "인정받는 자리일수록 맡을 일도 늘어납니다. 그만큼 업무의 경계는 초기에 정해야 합니다.",
        ),
        "love": (
            "연애운은 첫 끌림보다 연락을 이어 가는 방식에서 안정됩니다. 표현이 편안해질수록 관계가 오래 갑니다.",
            "연애운은 마음이 생긴 뒤 관계를 이어 가는 방식에서 깊어집니다. 연락 간격이 자연스러워지며 호감도 깊어집니다.",
            "관계에서는 좋아하는 마음을 어떻게 전하는지가 결론을 정합니다. 기대치를 말로 꺼내면 오해가 줄어듭니다.",
            "좋아하는 마음이 있어도 표현이 늦으면 상대는 확신을 갖기 어렵습니다. 만남의 속도가 편안해야 관계가 오래 갑니다.",
            "감정이 커질수록 말투와 약속이 관계를 흔듭니다. 작은 어긋남을 오래 두면 관계의 피로가 됩니다.",
        ),
        "marriage": (
            "사랑이 깊어도 생활의 속도가 어긋나면 부담이 커집니다. 생활비 이야기가 정리되면 마음이 한결 편해집니다. 주거 문제가 정리되면 결혼 생활도 안정됩니다.",
            "결혼운에서는 약속의 말보다 생활 방식이 더 중요해집니다. 돈 이야기가 정리되며 안정이 이어지고, 가족과의 거리도 편안함을 정합니다.",
            "결혼 문제에서는 마음의 확신만큼 생활 방식을 크게 봅니다. 두 사람이 같은 생활 감각을 갖춰 갈수록 갈등이 줄고 안정성이 커집니다.",
            "결혼 생활은 생활비와 주거 문제가 잡힐 때 안정됩니다. 서로의 역할이 분명해지면 생활의 부담도 줄어듭니다.",
            "배우자와의 안정은 생활의 세부 약속에서 만들어집니다. 돈 이야기를 늦게 꺼내면 작은 불만이 오래 남습니다.",
            "가족과 주거 문제를 현실적으로 다룰수록 결혼운이 안정됩니다. 애정만 앞세우면 생활의 부담이 커집니다.",
        ),
    }
    return _stable_title_variant(
        f"{entry_id}:{title}",
        variants.get(domain, (f"{title}에서는 타고난 장점과 생활 기준이 함께 움직이면서 결과가 좋아집니다.",)),
    )


def _sentence_end(text: str) -> str:
    body = _compact(text)
    if not body:
        return body
    if body.endswith((".", "!", "?", "다.", "요.")):
        return body
    return f"{body}."


def _stable_title_variant(title: str, options: tuple[str, ...]) -> str:
    if not options:
        return ""
    index = sum((offset + 1) * ord(char) for offset, char in enumerate(title)) % len(options)
    return options[index]


def _strength_customer_sentence(axis_label: str, event: str, domains: tuple[Domain, ...]) -> str:
    axis_text = _axis_customer_label(axis_label)
    if "money" in domains and "career" in domains:
        return (
            f"{axis_text}은 {event}{_subject_particle(event)} 보상과 인정으로 연결될 때 강해집니다. "
            "역할이 정해지며 해낸 일이 수입을 키웁니다. 지급 방식도 정해집니다."
        )
    if "love" in domains and "marriage" in domains:
        return (
            f"{axis_text}은 {event}{_object_particle(event)} 마음의 확인에서 생활의 약속으로 옮기는 데 중요합니다. "
            "감정 표현이 맞을 때 가까운 관계가 오래 안정됩니다. 생활 방식도 약속의 무게를 정합니다."
        )
    domain = domains[0] if domains else "money"
    if domain == "money":
        if axis_label == "재물 잠재력":
            return f"{axis_text}은 {event}{_subject_particle(event)} 돈이 되는지 가려내는 장점입니다. 기회가 들어와도 회수 절차와 손에 남는 금액을 함께 계산합니다."
        if axis_label == "수입 확대력":
            return f"{axis_text}은 {event}{_object_particle(event)} 더 높은 보상으로 바꾸는 장점입니다. 해낸 일이 금액으로 인정되며 수입이 커집니다. 지급일도 정해집니다."
        if axis_label == "자산 유지력":
            return f"{axis_text}은 {event}{_object_particle(event)} 오래 남기는 장점입니다. 들어온 돈에서 생활비가 먼저 구분됩니다. 예비 자금도 따로 남습니다."
        if axis_label == "투자와 거래 감각":
            return f"{axis_text}은 {event}{_object_particle(event)} 계약 구조와 회수 절차까지 따져 보는 장점입니다. 빠져나올 길이 보일 때 손실이 줄어듭니다."
        if axis_label == "현실 설계력":
            return f"{axis_text}은 {event}{_object_particle(event)} 돈의 절차로 옮기는 장점입니다. 지출 한도를 세울 때 재물운이 안정됩니다. 정산 방식도 정해집니다."
    return {
        "money": f"{axis_text}은 {event}{_object_particle(event)} 수입과 자산으로 바꾸는 데 직접 도움이 됩니다.",
        "career": f"{axis_text}은 {event}{_object_particle(event)} 인정과 다음 역할로 바꾸는 장점입니다.",
        "love": f"{axis_text}은 {event} 뒤에도 대화를 이어 가고 관계를 정리하는 장점입니다.",
        "marriage": f"{axis_text}은 {event}{_object_particle(event)} 생활의 약속과 책임 분담으로 정리하는 장점입니다.",
    }.get(domain, f"{axis_text}은 선택을 좋은 일로 옮기는 데 도움이 됩니다.")


def _dedicated_block_context(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    axes: list[dict[str, Any]],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> dict[str, str]:
    axis = axes[0] if axes else None
    axis_label = str(axis.get("label") or "") if axis else _dedicated_default_axis_label(domains)
    axis_text = _axis_customer_label(axis_label, default=axis_label)
    return {
        "title": title,
        "period": _entry_period(entry_id, target_years, item),
        "year_period": _entry_period(entry_id, target_years, item),
        "age_period": _age_period(target_years, item),
        "domain_noun": _dedicated_domain_noun(domains),
        "domain_scene": _dedicated_domain_scene(domains),
        "axis": _axis_short_clause(axis, default=axis_label),
        "axis_label": axis_text,
        "axis_label_raw": axis_label,
        "event": _dedicated_event_phrase(item, domains),
        "action": _action_subject(str(item.action)) if item and item.action else _action_subject(_dedicated_action_phrase(domains)),
        "risk": str(item.risk) if item and item.risk else _domain_caution_sentence(domains),
    }


def _dedicated_default_axis_label(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "수입 구조와 직업적 성취력"
    if "love" in domains and "marriage" in domains:
        return "관계 안정성과 결혼 안정성"
    domain = domains[0] if domains else "money"
    return {
        "money": "재물 잠재력",
        "career": "직업적 성취력",
        "love": "관계 안정성",
        "marriage": "결혼 안정성",
    }.get(domain, "현실 판단력")


def _dedicated_domain_noun(domains: tuple[Domain, ...]) -> str:
    nouns = [DOMAIN_NOUNS[domain] for domain in domains if domain in DOMAIN_NOUNS]
    return "·".join(nouns) if nouns else "운세"


def _dedicated_domain_scene(domains: tuple[Domain, ...]) -> str:
    scenes = [DOMAIN_SCENES[domain] for domain in domains if domain in DOMAIN_SCENES]
    return " / ".join(scenes) if scenes else "실제 생활의 선택 방향"


def _dedicated_event_phrase(item: ProductOutputItem | None, domains: tuple[Domain, ...]) -> str:
    if item:
        return _keyword_text(item)
    if domains:
        return _dedicated_domain_scene(domains)
    return "중요한 선택 방향"


def _dedicated_action_phrase(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "받을 몫과 책임 범위를 함께 정리하는 것"
    if "love" in domains and "marriage" in domains:
        return "감정 표현과 생활 방식을 함께 정리하는 것"
    domain = domains[0] if domains else "money"
    return {
        "money": "받을 돈과 남길 돈을 먼저 나누는 것",
        "career": "역할과 평가받는 근거를 먼저 정리하는 것",
        "love": "연락 방식과 기대치를 말로 정리하는 것",
        "marriage": "돈 이야기를 먼저 정리하는 것",
    }.get(domain, "선택의 방향을 먼저 정리하는 것")


def _content_blocks_for_entry(
    entry: dict[str, object],
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    entry_id = str(entry.get("entry_id") or "")
    title = str(entry.get("title") or "운세")
    domains = tuple(str(domain) for domain in entry.get("source_domains", []) if str(domain) in DOMAIN_NOUNS)
    typed_domains = tuple(domain for domain in domains if domain in DOMAIN_NOUNS)
    is_locked = bool(entry.get("is_locked"))
    if is_locked:
        return [_locked_block(title, entry_id)]

    if entry_id == "life_overview":
        return _life_overview_blocks(items, life_feature_summary, target_years)
    if entry_id == "personality_overview":
        return _personality_blocks(items, life_feature_summary)
    if entry_id == "annual_overview":
        return _annual_overview_blocks(items, target_years)
    if entry_id in {"annual_best", "annual_caution", "success_advice", "final_money_work_relationship_advice", "premium_core_five"}:
        return _advice_blocks(entry_id, title, items, life_feature_summary, target_years)
    if entry_id in TIMING_ENTRIES:
        return _timing_blocks(entry_id, title, items, target_years)
    if entry_id in {"career_fit_fields", "career_mismatch_conditions", "organization_success_method", "expertise_recognition_method"}:
        return _career_field_blocks(entry_id, title, life_feature_summary)
    if entry_id in {"business_expansion", "independence_business_potential", "leadership_potential", "academic_expertise_achievement"}:
        return _career_special_blocks(entry_id, title, items, life_feature_summary, target_years)
    if entry_id in {"ten_year_luck", "near_years_luck"}:
        return _timing_blocks(entry_id, title, items, target_years)
    if entry_id in {"health_life_management"}:
        return _health_life_blocks(items, life_feature_summary)
    if entry_id in MONEY_ENTRIES:
        return _money_catalog_blocks(entry_id, title, items, life_feature_summary, target_years)
    if entry_id in CAREER_ENTRIES:
        return _domain_catalog_blocks(entry_id, title, "career", items, life_feature_summary, target_years)
    if entry_id in RELATIONSHIP_ENTRIES:
        domain: Domain = "marriage" if entry_id in MARRIAGE_ENTRY_IDS else "love"
        return _relationship_catalog_blocks(entry_id, title, domain, items, life_feature_summary, target_years)
    if entry_id == "life_strength_balance":
        return _life_strength_blocks(items, life_feature_summary)

    domain = typed_domains[0] if typed_domains else "money"
    return _domain_catalog_blocks(entry_id, title, domain, items, life_feature_summary, target_years)


def _block(block_id: str, role: str, heading: str, body: str, source_domains: tuple[Domain, ...] = ()) -> ContentBlock:
    return {
        "block_id": block_id,
        "role": role,
        "heading": _compact(heading),
        "body": _dedicated_body_text(body),
        "source_domains": list(source_domains),
    }


def _expand_catalog_content_blocks(
    entry: dict[str, object],
    blocks: list[ContentBlock],
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    if bool(entry.get("is_locked")):
        return blocks

    entry_id = str(entry.get("entry_id") or "catalog")
    title = str(entry.get("title") or "운세")
    domains = _entry_domains(entry, blocks)
    item = _best_item_for_entry(domains, items)
    axes = _entry_axes(entry_id, domains, item, life_feature_summary)
    caution_axis = _entry_caution_axis(entry_id, item, life_feature_summary)
    expanded = list(blocks)
    roles = {str(block.get("role") or "") for block in expanded}

    if "orientation" not in roles:
        expanded.append(
            _block(
                f"{entry_id}-expanded-orientation",
                "orientation",
                "이 영역을 대하는 태도",
                _entry_orientation_sentence(entry_id, title, domains, item, axes),
                domains or ((item.domain,) if item else ()),
            )
        )

    if "life_scene" not in roles:
        expanded.append(
            _block(
                f"{entry_id}-expanded-life",
                "life_scene",
                "생활에서 보이는 모습",
                _entry_life_scene_sentence(entry_id, title, domains, item, target_years),
                domains,
            )
        )

    if "strength" not in roles:
        expanded.append(
            _block(
                f"{entry_id}-expanded-strength",
                "strength",
                "강점",
                _entry_strength_sentence(entry_id, title, domains, axes, item, target_years),
                domains,
            )
        )

    if "score" not in roles and item:
        expanded.append(
            _block(
                f"{entry_id}-expanded-score",
                "score",
                "판단 기준",
                _entry_score_sentence(entry_id, item, target_years),
                (item.domain,),
            )
        )

    if "caution" not in roles:
        expanded.append(
            _block(
                f"{entry_id}-expanded-caution",
                "caution",
                "주의할 점",
                _entry_caution_sentence(entry_id, domains, caution_axis, item),
                domains or ((item.domain,) if item else ()),
            )
        )

    if "action" not in roles:
        expanded.append(
            _block(
                f"{entry_id}-expanded-action",
                "action",
                "좋게 쓰는 법",
                _entry_action_sentence(entry_id, title, domains, item, target_years),
                domains or ((item.domain,) if item else ()),
            )
        )

    if len(expanded) < MIN_VISIBLE_CONTENT_BLOCKS:
        expanded.append(
            _block(
                f"{entry_id}-expanded-basis",
                "basis",
                "판단 근거",
                "타고난 세부 특성, 해당 시기의 사건 신호, 강점과 부담이 함께 놓이는 지점을 대조해 해석합니다.",
                domains,
            )
        )
    return expanded


def _catalog_body_sentence_count(text: str) -> int:
    return sum(1 for part in text.replace("?", ".").replace("!", ".").split(".") if part.strip())


def _enrich_catalog_content_block_bodies(
    entry: dict[str, object],
    blocks: list[ContentBlock],
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    if bool(entry.get("is_locked")):
        return blocks

    entry_id = str(entry.get("entry_id") or "")
    title = str(entry.get("title") or "운세")
    domains = _entry_domains(entry, blocks)
    item = _best_item_for_entry(domains, items)
    axes = _entry_axes(entry_id, domains, item, life_feature_summary)
    context = _dedicated_block_context(entry_id, title, domains, axes, item, target_years)

    enriched: list[ContentBlock] = []
    for block in blocks:
        body = _dedicated_body_text(block.get("body"))
        role = str(block.get("role") or "")
        if body and _catalog_body_sentence_count(body) < 2:
            followup = _dedicated_followup_sentence(role, title, domains, context, entry_id)
            if followup and followup not in body:
                body = _dedicated_body_text(f"{body} {followup}")
        updated = dict(block)
        updated["body"] = body
        enriched.append(updated)
    return enriched


def _entry_domains(entry: dict[str, object], blocks: list[ContentBlock]) -> tuple[Domain, ...]:
    block_domains: list[str] = []
    for block in blocks:
        block_domains.extend(str(domain) for domain in block.get("source_domains", []) if str(domain) in DOMAIN_NOUNS)
    if block_domains:
        return tuple(domain for domain in _unique(block_domains) if domain in DOMAIN_NOUNS)
    raw_domains = [str(domain) for domain in entry.get("source_domains", []) if str(domain) in DOMAIN_NOUNS]
    return tuple(domain for domain in _unique(raw_domains) if domain in DOMAIN_NOUNS)


def _best_item_for_entry(domains: tuple[Domain, ...], items: list[ProductOutputItem]) -> ProductOutputItem | None:
    if not items:
        return None
    if domains:
        primary_items = [item for item in items if item.domain == domains[0]]
        if primary_items:
            return max(primary_items, key=_item_rank)
        domain_items = [item for item in items if item.domain in domains]
        if domain_items:
            return max(domain_items, key=_item_rank)
    return max(items, key=_item_rank)


def _entry_axes(
    entry_id: str,
    domains: tuple[Domain, ...],
    item: ProductOutputItem | None,
    life_feature_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()), limit=3)
    if axes:
        return axes
    if item and item.feature_axes:
        return [axis for axis in item.feature_axes if isinstance(axis, dict)][:3]
    if domains:
        domain_axes = [
            axis
            for axis in _top_axes(life_feature_summary, limit=8)
            if _axis_matches_domains(axis, domains)
        ]
        if domain_axes:
            return domain_axes[:3]
    return _top_axes(life_feature_summary, limit=3)


def _entry_caution_axis(
    entry_id: str,
    item: ProductOutputItem | None,
    life_feature_summary: dict[str, Any],
) -> dict[str, Any] | None:
    labeled = _caution_axis(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()))
    if labeled:
        return labeled
    if item:
        for axis in item.feature_axes:
            if not isinstance(axis, dict):
                continue
            percentile = str(axis.get("percentile_label") or "")
            strength = str(axis.get("strength_label") or "")
            sentence = str(axis.get("customer_sentence") or "")
            if "하단" in percentile or "관리" in strength or "보완" in sentence:
                return axis
    cautions = _caution_axes(life_feature_summary, limit=1)
    return cautions[0] if cautions else None


def _axis_matches_domains(axis: dict[str, Any], domains: tuple[Domain, ...]) -> bool:
    category = str(axis.get("category") or "")
    if "money" in domains and category == "money":
        return True
    if "career" in domains and category in {"career", "social"}:
        return True
    if "love" in domains and category in {"relationship", "love", "social"}:
        return True
    if "marriage" in domains and category in {"relationship", "marriage", "family"}:
        return True
    return False


def _entry_life_scene_sentence(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    base = _domain_life_sentence(domains)
    if item:
        keywords = _keyword_text(item)
        if entry_id in ANNUAL_ENTRY_IDS:
            return (
                f"{base} {title}에서는 {keywords}{_subject_particle(keywords)} 올해 사건의 단서가 됩니다. "
                f"{_period([CURRENT_FORTUNE_YEAR])}에는 이 문제가 돈, 평가, 관계 중 어디에서 먼저 커지는지 확인됩니다."
            )
        age_period = _age_period(target_years, item)
        return (
            f"{base} {title}에서는 {keywords}{_subject_particle(keywords)} 생활에서 반복되는 주제가 됩니다. "
            f"{age_period}에는 이 성향이 생활 속 선택과 사건에서 더 뚜렷해집니다."
        )
    return f"{base} {title}은 강점과 부담이 함께 읽힐 때 결론이 더 정확해집니다."


def _entry_orientation_sentence(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    item: ProductOutputItem | None,
    axes: list[dict[str, Any]],
) -> str:
    axis_label = str(axes[0].get("label") or "") if axes else ""
    domain = domains[0] if domains else (item.domain if item else "money")
    domain_hint = f"{entry_id} {title}"
    if any(keyword in domain_hint for keyword in ("재물", "돈", "수입", "자산", "큰돈")):
        domain = "money"
    elif any(keyword in domain_hint for keyword in ("직업", "일", "성공", "명예", "평판", "전문성", "리더십")):
        domain = "career"
    elif any(keyword in domain_hint for keyword in ("연애", "애정", "대인", "관계")):
        domain = "love"
    elif any(keyword in domain_hint for keyword in ("결혼", "배우자", "가정", "자식")):
        domain = "marriage"
    if entry_id == "life_overview":
        return (
            "당신은 맡은 역할을 중심으로 삶의 방향을 잡는 책임형 인물입니다. "
            "겉으로는 밝고 유연해 보입니다. 속으로는 자신의 위치를 오래 생각합니다. 사람들 사이에서의 평가도 깊이 의식합니다."
        )
    if entry_id == "personality_overview":
        return (
            "당신은 서두르기보다 오래 남을 결정을 고르는 사람입니다. "
            "마음속 기준이 강해지면 혼자 판단하는 시간이 길어집니다. 결론을 혼자 오래 생각하는 경향도 강해집니다."
        )
    if entry_id in {"annual_overview", "annual_best", "annual_caution", "annual_good_timing", "annual_caution_timing"}:
        noun = DOMAIN_NOUNS.get(domain, "운세")
        axis_event = _axis_customer_event(axis_label, default=f"{noun}의 핵심")
        axis_particle = _subject_particle(axis_event)
        axis_phrases = {
            "annual_overview": f"올해는 {axis_event}{axis_particle} 먼저 생깁니다. ",
            "annual_best": f"올해는 {axis_event}{axis_particle} 한 해의 가장 좋은 기회입니다. ",
            "annual_caution": f"{axis_event}{axis_particle} 흔들리면 부담이 커집니다. ",
            "annual_good_timing": f"이 시기에는 {axis_event}{axis_particle} 중요한 계기가 됩니다. ",
            "annual_caution_timing": f"이 시기에는 {noun} 결정을 서두르면 부담이 커집니다. ",
        }
        axis_phrase = axis_phrases.get(entry_id, f"{axis_event}{axis_particle} 올해 선택의 핵심입니다. ") if axis_label else ""
        annual_variants: dict[Domain, tuple[str, ...]] = {
            "money": (
                f"올해 재물에서는 돈 문제를 더 미룰 수 없습니다. {axis_phrase}미뤄 둔 정산도 더는 뒤로 밀리지 않습니다.",
                f"올해 재물에서는 결정할 돈 문제가 빨리 생깁니다. {axis_phrase}초반에 받을 금액과 지출 한도가 나뉩니다.",
                f"올해는 재물의 결론이 빨리 나는 해입니다. {axis_phrase}망설이던 계약과 지출 문제도 앞에 놓입니다.",
                f"올해 재물에서는 초반 선택이 손에 남는 돈을 정합니다. {axis_phrase}뒤로 미룬 정산은 더 큰 부담으로 남습니다.",
                f"올해는 재물에서 미뤄 둔 문제가 다시 앞에 놓입니다. {axis_phrase}초반에 받을 돈과 남길 돈이 나뉩니다.",
            ),
            "career": (
                f"올해 직업에서는 중요한 일을 더 미루기 어렵습니다. {axis_phrase}미뤄 둔 업무 문제도 더는 뒤로 밀리지 않습니다.",
                f"올해 직업에서는 결정할 일이 빨리 생깁니다. {axis_phrase}초반 선택이 이후 평가와 보상을 바꿉니다.",
                f"올해는 직업의 결론이 빨리 나는 해입니다. {axis_phrase}망설이던 역할 문제가 앞에 놓이고 선택도 빨라집니다.",
                f"올해 직업에서는 초반에 맡는 일이 한 해의 평가를 정합니다. {axis_phrase}미룬 일은 결국 더 큰 책임이 됩니다.",
                f"올해 직업에서는 미뤄 둔 업무 문제가 다시 앞에 놓입니다. {axis_phrase}초반에 맡을 일과 책임 범위를 분명히 나눕니다.",
            ),
            "love": (
                f"올해 연애에서는 마음의 문제를 더 미루기 어렵습니다. {axis_phrase}미뤄 둔 감정도 더는 숨기기 어렵습니다.",
                f"올해 연애에서는 결정할 일이 빨리 생깁니다. {axis_phrase}초반 말투와 연락 방식이 이후 관계의 거리를 바꿉니다.",
                f"올해 연애에서는 미뤄 둔 마음을 더는 숨기기 어렵습니다. {axis_phrase}망설이던 감정도 더는 뒤로 밀리지 않습니다.",
                f"올해 연애에서는 초반 선택이 관계의 온도를 정합니다. {axis_phrase}뒤로 미룬 감정은 더 큰 오해로 남습니다.",
                f"올해는 연애에서 미뤄 둔 문제가 다시 앞에 놓입니다. {axis_phrase}초반에 연락 방식과 거리감을 맞추게 됩니다.",
            ),
            "marriage": (
                f"올해 결혼에서는 생활 문제를 더 미루기 어렵습니다. {axis_phrase}미뤄 둔 약속도 더는 뒤로 밀리지 않습니다.",
                f"올해 결혼에서는 결정할 일이 빨리 생깁니다. {axis_phrase}초반에 생활비와 책임 기준이 나뉩니다.",
                f"올해 결혼에서는 생활의 결정이 빨라집니다. {axis_phrase}미뤄 둔 생활 문제도 더는 뒤로 밀리지 않습니다.",
                f"올해 결혼에서는 초반 선택이 생활의 안정감을 정합니다. {axis_phrase}뒤로 미룬 책임은 더 큰 부담으로 남습니다.",
                f"올해는 결혼에서 미뤄 둔 문제가 다시 앞에 놓입니다. {axis_phrase}초반에 생활비와 주거 문제를 구체적으로 말하게 됩니다.",
            ),
        }
        return _stable_title_variant(
            f"{entry_id}:{title}:{axis_label}",
            annual_variants.get(domain, annual_variants["money"]),
        )
    if entry_id in {"timing_detail", "long_term_years", "ten_year_luck", "near_years_luck", "monthly_key_timing", "favorable_timing", "caution_timing"}:
        subject = _domain_timing_subject(domain, axis_label)
        return _stable_title_variant(
            f"{entry_id}:{title}:{axis_label}",
            (
                f"당신은 시기 변화가 오면 {subject}{_object_particle(subject)} 중심으로 선택을 다시 세웁니다. 맡을 일의 범위도 함께 달라집니다.",
                f"중요한 때에는 {subject}{_subject_particle(subject)} 먼저 앞에 놓입니다. 일의 우선순위가 바뀌고 돈의 사용처도 달라집니다.",
                f"시기 변화 앞에서 당신은 머뭇거리기보다 현실적인 선택을 다시 세웁니다. 이때 {subject}{_object_particle(subject)} 분명하게 정합니다.",
            ),
        )
    if domain == "money":
        if entry_id == "money_attitude":
            return (
                "당신은 돈이 들어오는 순간보다 그 돈이 얼마나 오래 남는지를 더 예민하게 봅니다. "
                "돈이 주는 자유를 의식합니다. 어느 순간부터는 남길 금액을 먼저 정하게 됩니다."
            )
        if entry_id in {"money_leak_conditions", "money_caution_years"}:
            return (
                "당신은 돈을 번 뒤에도 손에 남는 금액을 오래 확인합니다. "
                "작은 약속이 반복되면 손에 남는 돈이 빠르게 줄어듭니다. 정산이 늦어져도 돈이 남는 느낌이 약해집니다."
            )
        if entry_id in {"investment_trade_sense", "business_expansion_power"}:
            return (
                "당신은 기회 안에서 이익 지점을 빠르게 찾는 거래 감각형입니다. "
                "재물의 크기가 커지면 계약 내용이 더 치밀해집니다. 회수 문제도 늦게 넘기지 않습니다."
            )
        if entry_id in {"income_expansion_method", "income_expansion_power", "annual_money"}:
            return _stable_title_variant(
                f"{entry_id}:{title}:{axis_label}",
                (
                    "당신은 해낸 일이 돈으로 인정될 때 재물운이 강해지는 사람입니다. 맡은 일이 금액으로 인정될수록 수입도 커집니다.",
                    "수입은 막연한 기대보다 해낸 일의 대가로 생깁니다. 보상 금액이 정해질 때 재물운도 강해집니다.",
                    "돈은 성과가 정산되는 자리에서 생깁니다. 지급일이 정해지며 늘어난 돈이 손에 남습니다.",
                    "당신은 일의 결과가 보상으로 바뀔 때 재물운을 크게 느낍니다. 정산이 빠를수록 돈도 오래 남습니다.",
                ),
            )
        if entry_id in {"wealth_retention_conditions", "asset_retention_power"}:
            return (
                "당신은 들어온 돈을 오래 보존하려는 자산 관리형입니다. "
                "지출 뒤에 남는 금액이 실제 재물 수준을 정합니다."
            )
        if entry_id in {"native_money", "native_wealth_level", "wealth_potential"}:
            return _stable_title_variant(
                title,
                (
                    "당신은 돈이 들어온 뒤의 관리까지 오래 보는 사람입니다. 나이가 들수록 한 번 들어온 돈을 쉽게 흘려보내지 않습니다.",
                    "당신의 재물운은 수입의 크기보다 남기는 방식에서 강해집니다. 나이가 들수록 들어온 돈을 자산으로 남기는 힘이 강해집니다.",
                    "당신은 돈을 선택권으로 받아들이는 편입니다. 들어온 돈을 오래 남길수록 재물운도 더 강해집니다.",
                ),
            )
        return (
            "당신은 돈을 생활의 안정감과 연결해서 받아들이는 사람입니다. "
            "수입이 들어온 뒤 그 돈을 어떻게 지켜내는지가 재물운의 결론으로 남습니다."
        )
    if domain == "career":
        if entry_id == "career_mismatch_conditions":
            return (
                "당신은 능력이 부족해서 힘든 사람이 아닙니다. "
                "책임은 커지는데 결정권이 약한 자리에서 소모가 빨라집니다. "
                "무엇으로 평가받는지 보이지 않는 업무도 피로를 남깁니다."
            )
        if entry_id in {"career_fit_fields", "career_mismatch_conditions"}:
            return (
                "당신은 자기 판단을 써야 하는 자리에서 강해지는 실행 주도형입니다. "
                "사람을 설득하는 자리에서 일의 성취가 커집니다. "
                "복잡한 일을 정리하는 자리에서도 능력이 잘 쓰입니다."
            )
        if entry_id in {"honor_reputation", "reputation_success", "social_success_potential"}:
            return _stable_title_variant(
                title,
                (
                    "당신은 인정과 평판을 가볍게 넘기지 않는 사람입니다. 맡은 일이 밖에서 확인될수록 더 큰 책임도 감당하게 됩니다.",
                    "사회적 자리에서는 신뢰를 가볍게 보지 않습니다. 직책이 주어지면 맡은 범위를 넓게 보고 책임 있게 처리하려 합니다.",
                    "당신은 해낸 일이 이름과 평판으로 돌아올 때 더 강해집니다. 신뢰를 잃지 않으려는 태도도 분명합니다.",
                ),
            )
        if entry_id in {"native_career", "career_precision"}:
            return _stable_title_variant(
                title,
                (
                    "당신은 맡은 일을 성과와 인정으로 연결하려는 사람입니다. 이름뿐인 자리보다 결정권이 있는 자리에서 능력을 인정받습니다.",
                    "직업에서는 무엇을 맡느냐보다 어디까지 결정할 수 있느냐가 중요합니다. 평가 기준이 보이면 움직임도 빨라집니다.",
                    "당신의 직업운은 책임이 분명한 자리에서 강합니다. 결과가 외부에 보이는 업무에서 인정을 빨리 받습니다.",
                ),
            )
        if entry_id == "organization_success_method":
            return (
                "당신은 조직 안에서 기준과 절차를 읽는 능력이 강한 사람입니다. "
                "상사의 기대가 분명한 자리에서 맡은 일을 안정적으로 끝냅니다. "
                "문서와 결과물이 남는 업무에서 신뢰를 얻습니다."
            )
        if entry_id == "expertise_recognition_method":
            return (
                "당신은 아는 것을 결과물로 바꾸는 전문 실무형입니다. "
                "지식이 문서, 자격, 발표, 교육 자료로 남을 때 인정이 빨라집니다. "
                "말보다 증거가 당신의 직업운을 강하게 합니다."
            )
        if entry_id in {"leadership_potential", "responsibility_capacity"}:
            return (
                "당신은 혼자 성과를 내는 데서 끝나는 사람이 아닙니다. "
                "사람의 역할을 나누고 책임의 순서를 세울 때 리더십이 강해집니다. "
                "권한이 따라오는 자리에서 인정이 쌓입니다."
            )
        if entry_id in {"independence_business_potential", "business_expansion", "business_expansion_power"}:
            return (
                "당신은 독립적인 선택에 끌리는 확장형입니다. "
                "자유로운 일일수록 계약과 일정이 분명할 때 이익이 남습니다. 비용 기준을 먼저 세울 때 사업운이 안정됩니다."
            )
        return (
            _stable_title_variant(
                f"{entry_id}:{title}:{axis_label}",
                (
                    "당신은 일에서 자신의 능력이 제대로 쓰이기를 바랍니다. 맡은 일로 인정받을 때 집중력도 오래 갑니다.",
                    "직업에서는 책임 있는 자리를 피하지 않습니다. 해낸 일이 평가로 남을수록 다음 역할도 맡게 됩니다.",
                    "당신은 바쁘기만 한 자리보다 실력이 보이는 자리를 원합니다. 맡은 일로 인정받을 때 집중력도 오래 갑니다.",
                    "일에서는 결과가 보이는 업무가 맞습니다. 책임이 주어질수록 실력도 더 정확히 인정받습니다.",
                ),
            )
        )
    if domain == "love":
        return _stable_title_variant(
            title,
            (
                "당신은 감정을 가볍게 쓰지 않는 신중 애정형입니다. 처음에는 편하게 어울려도 마음을 깊이 주기까지 시간이 걸립니다. 말투와 약속이 안정될 때 더 가까워집니다.",
                "당신은 호감이 생겨도 관계의 속도를 살피는 사람입니다. 상대가 꾸준히 다가올 때 마음을 엽니다. 급한 표현보다 안정적인 태도에 더 크게 반응합니다.",
                "당신은 마음이 움직여도 바로 드러내기보다 상대의 태도를 오래 봅니다. 연락이 일정해질 때 안심합니다. 말투가 편안할 때 감정도 깊어집니다.",
            ),
        )
    if domain == "marriage":
        if entry_id in {"spouse_conflict_points", "marriage_stability_conditions"}:
            return (
                "당신은 결혼을 현실의 약속으로 받아들이는 생활 검토형입니다. 좋아하는 마음이 깊어져도 생활 방식이 맞는지를 오래 봅니다. "
                "배우자를 아끼면서도 자신의 기준을 쉽게 내려놓지 않아, 가까운 관계일수록 대화의 시점을 먼저 잡게 됩니다."
            )
        return _stable_title_variant(
            title,
            (
                "당신은 결혼을 생활의 약속으로 받아들이는 현실 안정형입니다. 사랑이 깊어져도 생활비의 기준을 오래 봅니다. 가족 책임도 결혼 판단에서 중요하게 봅니다.",
                "당신에게 결혼은 마음의 확신과 생활의 안정이 함께 가는 문제입니다. 좋아하는 마음이 커질수록 주거와 가족 문제도 진지하게 따집니다.",
                "당신은 결혼을 가볍게 결정하지 않습니다. 서로를 좋아해도 생활 방식이 어긋나면 마음이 쉽게 불편해집니다. 돈의 기준이 정리될 때 약속도 안정됩니다.",
            ),
        )
    if axis_label:
        axis_text = _axis_customer_label(axis_label)
        return (
            f"당신은 {axis_text}이 삶의 선택에서 자주 앞에 놓이는 사람입니다. "
            "이 성향은 생각에 머무르지 않고 돈, 일, 관계를 대하는 태도로 반복됩니다."
        )
    return (
        f"당신은 {title}을 단순한 길흉보다 자신의 선택과 생활 태도에서 먼저 받아들이는 편입니다. "
        "이 태도는 현실의 일, 돈, 관계에서 반복됩니다."
    )


def _entry_strength_sentence(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    axes: list[dict[str, Any]],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    sentences: list[str] = []
    if axes:
        customer_sentence = _axis_customer_prose_text(_field_text(axes[0], "customer_sentence", ""))
        sentences.append(customer_sentence or _axis_phrase(axes[0]))
        if len(axes) > 1:
            labels = _join_korean([_axis_customer_label(str(axis.get("label") or "")) for axis in axes[1:3]])
            if labels:
                sentences.append(f"함께 보이는 장점은 {labels}입니다. 이 장점이 맞물리며 {DOMAIN_SCENES.get(domains[0], '생활 방식')}이 더 안정됩니다.")
    elif item:
        keywords = _keyword_text(item)
        sentences.append(f"{title}에서는 {keywords}{_subject_particle(keywords)} 강점으로 쓰입니다.")
    else:
        sentences.append(f"{title}에서는 타고난 장점과 현재 시기의 자극이 함께 맞물립니다.")
    if item and item.event_keywords:
        keywords = _keyword_text(item)
        if entry_id in ANNUAL_ENTRY_IDS:
            sentences.append(f"올해 사건에서는 {keywords}{_object_particle(keywords)} 먼저 정할 때 강점이 더 잘 쓰입니다.")
        else:
            age_period = _age_period(target_years, item)
            sentences.append(f"{age_period}에는 {keywords}{_object_particle(keywords)} 먼저 정할 때 강점이 생활에서 더 잘 쓰입니다.")
    return " ".join(sentences)


def _entry_score_sentence(entry_id: str, item: ProductOutputItem, target_years: list[int]) -> str:
    probability = _score_level_text(str(item.score_labels.get("probability") or "보통"))
    opportunity = _score_level_text(str(item.score_labels.get("opportunity") or "보통"))
    change = _score_level_text(str(item.score_labels.get("change") or "보통"))
    risk = _score_level_text(str(item.score_labels.get("risk") or "관리 필요"))
    if entry_id not in ANNUAL_ENTRY_IDS:
        age_period = _age_period(target_years, item)
        return (
            f"{age_period}에는 이 주제가 생활에서 {probability}하게 커집니다. 기회의 강도는 {opportunity}입니다. 변화 폭은 {change}입니다. "
            f"위험 신호는 {risk}{_direction_particle(risk)} 보이며 선택의 속도와 범위가 줄어듭니다."
        )
    return (
        f"올해 사건은 {probability}하게 이어집니다. 기회의 강도는 {opportunity}입니다. 변화 폭은 {change}입니다. "
        f"위험 신호는 {risk}{_direction_particle(risk)} 보이며 선택의 속도와 범위가 줄어듭니다."
    )


def _entry_caution_sentence(
    entry_id: str,
    domains: tuple[Domain, ...],
    caution_axis: dict[str, Any] | None,
    item: ProductOutputItem | None,
) -> str:
    sentences: list[str] = []
    if item:
        sentences.append(f"주의할 장면은 {item.risk}입니다.")
    if caution_axis:
        sentences.append(_entry_axis_caution_sentence(entry_id, caution_axis))
    if not sentences:
        sentences.append(_domain_caution_sentence(domains))
    return " ".join(sentences)


def _action_subject(action: str) -> str:
    compacted = _compact(action)
    replacements = {
        "맡는 자리가 커지는 일": "업무 범위가 넓어지는 일",
        "해낸 일이 돈으로 인정되는 일": "해낸 일의 금전 보상",
        "약속을 정하기 전에 돈의 기준을 정리하는 것": "돈 문제 정리",
        "결혼 결정을 서두르라는 압박을 받는 것": "결혼 결정 압박",
        "기대치를 말로 정리하는 일": "기대치 정리",
        "서로 편한 거리, 연락 빈도, 개인 영역을 분명히 합의하는 것": "관계의 거리 조정",
        "감정보다 연락 방식, 생활 거리, 기대치를 먼저 정리하는 것": "연락 방식 정리",
        "호감의 크기보다 표현 방식과 연락 속도를 정리하는 것": "표현 방식 정리",
        "호감이 생겨도 만남의 속도와 생활 기준을 함께 확인하는 것": "만남의 속도 확인",
        "결혼 의사와 생활 합의를 같은 자리에서 확인하는 것": "결혼 의사와 생활 방식",
        "결혼 의사와 생활 합의를 같은 자리에서 확인하는 일": "결혼 의사와 생활 방식",
        "결혼 의사와 생활 기준 합의를 같은 자리에서 확인하는 것": "결혼 의사와 생활 방식",
        "결혼 의사와 생활 기준 합의를 같은 자리에서 확인하는 일": "결혼 의사와 생활 방식",
        "정산을 다시 맞추는 것": "정산 재조정",
        "업무 기준을 다시 세우는 것": "업무 기준 재정비",
        "소비 기준을 다시 세우는 것": "소비 기준 재정비",
        "성과를 금액과 지급 시점으로 명확히 정리하는 것": "해낸 일의 금액 확정",
        "성과를 금액과 지급 시점으로 명확히 정리하는 일": "해낸 일의 금액 확정",
    }
    if compacted in replacements:
        return replacements[compacted]
    if "새 역할을 받기 전에 권한" in compacted or "새 역할에서 결정권" in compacted:
        return "결정권이 따르는 역할 변화"
    if "만남의 속도와 생활 기준을 함께 확인" in compacted:
            return "만남의 속도와 생활 방식"
    if "결정 시점과 책임 범위를 차분히 확인" in compacted:
        return "결정 시점과 책임 범위"
    if compacted.endswith("권한"):
        return f"{compacted} 범위"
    if compacted.endswith("하는 것") or compacted.endswith("는 것"):
        return compacted[:-1] + "일"
    return compacted


def _period_action_sentence(period: str, action: str) -> str:
    subject = _action_subject(action)
    return f"{period}에는 {subject}{_subject_particle(subject)} 중요한 선택으로 넘어갑니다."


def _entry_action_sentence(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    specific = _catalog_action_sentence(entry_id, title, domains, item, target_years)
    if specific:
        return specific
    if item:
        return (
            f"{_period_action_sentence(_entry_period(entry_id, target_years, item), item.action)} "
            f"이 기준을 지킬수록 {_domain_result_sentence(domains or (item.domain,))}"
        )
    return f"좋은 자리와 조심할 자리가 나뉩니다. {_domain_result_sentence(domains)}"


def _catalog_action_sentence(
    entry_id: str,
    title: str,
    domains: tuple[Domain, ...],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    period = _entry_period(entry_id, target_years, item)
    risk = item.risk if item else "기준이 흐려지는 상황"
    domain = domains[0] if domains else (item.domain if item else "money")
    action_subject = _action_subject(item.action) if item else "중요한 문제를 구체적으로 정리하는 일"

    money_actions = {
        "native_money": f"{period}에는 들어온 돈을 어디에 남길지 먼저 정합니다. 수입의 쓰임이 정리되며 재물운이 안정됩니다. 지출 한도를 따로 둘수록 돈이 남습니다.",
        "money_attitude": f"{period}에는 돈을 쓰기 전에 목적을 분명히 세웁니다. 지출 한도가 정해지며 들어온 돈이 오래 남습니다.",
        "native_wealth_level": f"{period}에는 큰 수입보다 남길 순서를 더 크게 봅니다. 고정비가 분리되며 재물운은 자산으로 쌓입니다. 예비 자금은 따로 남습니다.",
        "income_expansion_method": f"{period}에는 보수와 지급일이 문서로 확정됩니다. 해낸 일의 금액도 정해집니다. 받을 돈이 함께 늘어납니다.",
        "wealth_retention_conditions": f"{period}에는 수입이 생긴 뒤 고정비와 저축 순서가 바로 나뉩니다. 남길 돈을 따로 떼어 둘수록 지출이 재물운을 흔들지 않습니다.",
        "money_leak_conditions": f"{period}에는 느슨한 약속을 그대로 두지 않습니다. 지급일이 정해지며 손실도 작아집니다. 나눌 돈과 남길 돈도 따로 계산됩니다.",
        "wealth_potential": f"{period}에는 기회를 잡기 전에 계약 문제가 생깁니다. 회수 절차가 정해지며 재물운이 커집니다. 남는 금액도 따로 계산됩니다.",
        "income_expansion_power": f"{period}에는 역할이 커지며 받을 금액도 올라갑니다. 지급 시점이 정해지며 수입이 늘어납니다. 금액도 따로 정해집니다.",
        "asset_retention_power": f"{period}에는 생긴 돈을 오래 보유할 순서가 세워집니다. 지출 한도가 정해지며 수입이 자산으로 남습니다. 예비 자금은 따로 남습니다.",
        "investment_trade_sense": f"{period}에는 수익률보다 손실 한도를 더 크게 봅니다. 빠져나올 길이 분명한 거래가 재물운을 지킵니다.",
        "business_expansion_power": f"{period}에는 매출을 늘리기 전에 비용 문제가 생깁니다. 책임 범위가 정해지며 이익이 남습니다.",
        "money_caution_years": f"{period}에는 계약서부터 확인합니다. 세금 문제도 별도로 챙깁니다. {risk}이 줄어들며 재물 손실도 작아집니다.",
        "annual_money": f"{period}에는 해낸 일이 금액으로 확정되며 올해 재물운이 강해집니다. 받을 금액을 꼼꼼히 따집니다. 나갈 돈도 따로 가릅니다. 올해 돈은 손에 남는 금액으로 판단합니다.",
    }
    career_actions = {
        "native_career": f"{period}에는 맡는 역할이 분명해집니다. 무엇으로 평가받는지가 보이면서 직업에서 인정받는 일이 생깁니다.",
        "career_precision": f"{period}에는 맡는 역할이 직업운의 중심이 됩니다. 결정권도 분명해집니다. 인정받을 자리가 생깁니다.",
        "career_fit_fields": f"{period}에는 현재 직업명이 다르더라도 강점이 쓰이는 역할이 늘어납니다. 일정 관리가 보이는 일을 맡으며 인정도 빨라집니다. 기준 정리도 당신의 강점으로 쓰입니다.",
        "career_mismatch_conditions": f"{period}에는 책임은 큰데 결정권이 없는 자리가 부담이 됩니다. 무엇으로 평가받는지가 어긋난 자리에서는 부담이 커집니다.",
        "organization_success_method": f"{period}에는 조직 안에서 맡은 일이 기록으로 남습니다. 결과물이 확인되며 인정도 빨라집니다.",
        "expertise_recognition_method": f"{period}에는 전문성이 말보다 결과물에서 평가받습니다. 자격이 쌓이며 직업적 신뢰가 커집니다. 보고서도 당신의 평가를 올립니다.",
        "independence_business_potential": f"{period}에는 독립적인 선택을 하더라도 계약이 문서로 남습니다. 일정은 숫자로 정해집니다. 관리 기준이 서면서 자유로운 일이 이익으로 남습니다.",
        "social_success_potential": f"{period}에는 성과를 외부에서 인정받습니다. 다음 역할도 맡게 됩니다. 대가를 늦게 정하면 부담이 커집니다.",
        "honor_reputation": f"{period}에는 말과 결과물이 어긋나지 않게 관리됩니다. 약속한 기준을 끝까지 지키며 신뢰를 얻습니다.",
        "leadership_potential": f"{period}에는 맡길 일과 직접 책임질 일이 나뉩니다. 역할 배분이 정해지며 리더십이 부담이 아니라 성과로 인정됩니다.",
        "business_expansion": f"{period}에는 거래를 늘리기 전에 비용 문제가 생깁니다. 역할 기준이 정해지며 확장이 안정됩니다.",
        "academic_expertise_achievement": f"{period}에는 지식과 경험이 문서로 남습니다. 자격은 밖에서 인정받는 힘이 됩니다. 교육 성과도 전문성을 키웁니다.",
        "annual_career": f"{period}에는 {action_subject}{_subject_particle(action_subject)} 직업운에서 인정을 부릅니다. 해낸 일이 평가받습니다. 권한이 확정됩니다. 받을 대가도 보입니다. 이 해에는 다음 역할도 맡게 됩니다.",
        "reputation_success": f"{period}에는 해낸 일이 평판으로 이어지도록 결과물과 책임 범위가 정리됩니다. 인정받는 자리에서 더 큰 역할도 맡게 됩니다.",
    }
    relationship_actions = {
        "native_love": f"{period}에는 감정을 표현하는 방식이 관계를 바꿉니다. 표현 방식이 어긋나 관계가 늦게 안정됩니다.",
        "relationship_social": f"{period}에는 가까워지는 속도를 다시 맞추게 됩니다. 호감이 생기며 기대치를 말로 꺼내게 됩니다.",
        "love_precision": f"{period}에는 연락 방식이 끌림보다 더 중요하게 느껴집니다. 마음의 방향도 정해집니다. 서로의 기대가 말로 정리되며 관계가 안정됩니다.",
        "annual_love": f"{period}에는 기대치를 말로 정리하게 됩니다. 같은 오해가 줄어듭니다. 올해 애정운은 연락 방식에서 차이가 납니다.",
    }
    marriage_actions = {
        "native_marriage": f"{period}에는 애정만큼 생활 방식을 크게 봅니다. 돈 문제를 분명히 말하게 되면서 결혼운이 안정됩니다. 주거 문제도 따로 다룹니다.",
        "marriage_precision": f"{period}에는 결혼 의사를 분명히 말하게 됩니다. 마음이 깊어질수록 생활 방식도 말로 꺼내게 됩니다.",
        "spouse_conflict_points": f"{period}에는 배우자와 부딪히기 쉬운 지점을 말로 꺼내게 됩니다. 돈 이야기가 맞지 않으면 부담이 커집니다. 가족 책임도 따로 남습니다.",
        "marriage_stability_conditions": f"{period}에는 생활비 이야기가 결혼 생활의 중심이 됩니다. 주거 계획이 정리되며 결혼 생활도 안정됩니다.",
        "children_family_luck": f"{period}에는 가족 안에서 맡을 몫이 갈라집니다. 챙기는 마음이 커지며 생활 책임도 함께 늘어납니다.",
        "health_life_management": f"{period}에는 일정이 줄어듭니다. 책임이 커지는 시기에는 생활 관리가 운세의 안정성을 지킵니다.",
        "annual_marriage": f"{period}에는 {action_subject}{_subject_particle(action_subject)} 먼저 분명해집니다. 결혼 의사를 확인하며 생활 약속도 안정됩니다.",
    }

    if entry_id in money_actions:
        return money_actions[entry_id]
    if entry_id in career_actions:
        return career_actions[entry_id]
    if entry_id in relationship_actions:
        return relationship_actions[entry_id]
    if entry_id in marriage_actions:
        return marriage_actions[entry_id]
    if domain == "money":
        return f"{period}에는 {action_subject}이 돈의 방향을 정합니다. 수입의 쓰임이 정해지며 손에 남는 돈이 커집니다."
    if domain == "career":
        return f"{period}에는 {action_subject}이 직업운의 핵심이 됩니다. 맡을 역할이 정해지며 인정받는 일이 생깁니다."
    if domain == "love":
        return f"{period}에는 {action_subject}이 관계의 방향을 정합니다. 기대치가 정리되면서 관계가 편안해집니다."
    if domain == "marriage":
        return f"{period}에는 {action_subject}이 생활의 방향을 정합니다. 애정과 현실 문제가 함께 정리되면서 결혼운이 안정됩니다."
    return ""


def _domain_life_sentence(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "돈과 일은 맡는 역할에서 달라집니다. 받을 몫이 정해질수록 수입과 평가가 함께 좋아집니다."
    if "love" in domains and "marriage" in domains:
        return "관계와 결혼은 연락 방식에서 달라집니다. 생활 방식이 맞춰질 때 오래 갑니다."
    domain = domains[0] if domains else "money"
    return {
        "money": "생활에서는 받을 돈의 순서가 중요합니다. 빠져나갈 돈도 따로 계산됩니다.",
        "career": "일에서는 책임 범위가 직업운의 중심에 놓입니다. 무엇으로 평가받는지도 결과를 바꿉니다.",
        "love": "관계에서는 연락 방식에서 편안함이 생깁니다. 표현 속도도 마음의 거리를 바꿉니다.",
        "marriage": "결혼에서는 애정의 깊이와 별개로 돈 문제가 안정되어야 합니다. 가족과의 거리도 결혼 생활에 오래 남습니다.",
    }.get(domain, "생활에서는 강점이 커지는 장면과 부담이 커지는 장면이 다릅니다.")


def _domain_caution_sentence(domains: tuple[Domain, ...]) -> str:
    domain = domains[0] if domains else "money"
    return {
        "money": "돈이 들어오는 장면만 보고 정산 순서를 늦추면 남는 금액이 줄어듭니다. 계약 내용도 초기에 잡아야 합니다.",
        "career": "성과만 앞세우고 책임 범위와 평가받는 근거를 늦게 정하면 부담이 커집니다.",
        "love": "마음이 있어도 연락 방식과 기대치를 말하지 않으면 오해가 쌓입니다.",
        "marriage": "애정이 깊어도 돈 이야기를 미루면 생활의 부담이 커집니다. 주거 문제도 늦게 다루면 부담이 커집니다.",
    }.get(domain, "핵심 문제를 늦게 다루면 장점이 제때 쓰이지 못합니다.")


def _domain_result_sentence(domains: tuple[Domain, ...]) -> str:
    if "money" in domains and "career" in domains:
        return "수입 구조와 직업적 평가가 같은 방향으로 정리됩니다."
    if "love" in domains and "marriage" in domains:
        return "감정의 안정과 생활 방식을 함께 정리하게 됩니다."
    domain = domains[0] if domains else "money"
    return {
        "money": "수입, 계약, 지출 선택이 돈으로 남습니다.",
        "career": "역할과 평가가 뚜렷해집니다.",
        "love": "호감과 만남이 안정된 관계로 이어집니다.",
        "marriage": "애정과 생활 방식이 같은 방향으로 정리됩니다.",
    }.get(domain, "무엇을 먼저 선택할지 분명해집니다.")


def _score_level_text(label: str) -> str:
    return {
        "매우 강함": "매우 강한 편",
        "강함": "강한 편",
        "보통 이상": "보통 이상",
        "약함": "약한 편",
        "매우 약함": "매우 약한 편",
        "강한 주의": "강한 주의가 필요한 수준",
        "주의": "주의가 필요한 수준",
        "관리 가능": "관리 가능한 수준",
        "낮음": "낮은 편",
        "관리 필요": "관리해야 하는 수준",
    }.get(label, label)


def _locked_block(title: str, entry_id: str) -> ContentBlock:
    money_ids = {
        "money_attitude",
        "native_wealth_level",
        "income_expansion_method",
        "wealth_retention_conditions",
        "money_leak_conditions",
        "investment_trade_sense",
        "wealth_potential",
        "income_expansion_power",
        "asset_retention_power",
        "business_expansion_power",
        "money_caution_years",
    }
    career_ids = {
        "career_precision",
        "career_fit_fields",
        "career_mismatch_conditions",
        "organization_success_method",
        "expertise_recognition_method",
        "independence_business_potential",
        "social_success_potential",
        "honor_reputation",
        "leadership_potential",
        "social_influence",
        "business_expansion",
        "academic_expertise_achievement",
    }
    relationship_ids = {
        "love_precision",
        "marriage_precision",
        "spouse_conflict_points",
        "marriage_stability_conditions",
        "children_family_luck",
        "health_life_management",
    }
    timing_ids = {
        "long_term_years",
        "ten_year_luck",
        "near_years_luck",
        "monthly_key_timing",
        "favorable_timing",
        "caution_timing",
    }
    if entry_id in money_ids:
        body = (
            "프리미엄에서는 재물 규모가 확대되는 나이와 실질 금액을 더 깊게 풀이합니다. "
            "계약, 지출, 정산에서 손재가 생기기 쉬운 지점까지 따로 짚습니다."
        )
    elif entry_id in career_ids:
        body = (
            "프리미엄에서는 직업 성취와 사회적 평가를 더 깊게 풀이합니다. "
            "잘 맞는 역할, 인정받는 자리, 부담으로 남기 쉬운 업무 환경까지 따로 짚습니다."
        )
    elif entry_id in relationship_ids:
        body = (
            "프리미엄에서는 마음이 움직이는 방식과 애정 표현을 더 깊게 풀이합니다. "
            "부딪히기 쉬운 부분과 오래 안정되는 생활 문제까지 따로 짚습니다."
        )
    elif entry_id in timing_ids:
        body = (
            "프리미엄에서는 대운과 세운에서 강해지는 시기를 더 깊게 풀이합니다. "
            "돈이 강해지는 해를 먼저 짚습니다. 관계에서 조심할 시기도 함께 짚습니다."
        )
    else:
        body = (
            "프리미엄에서는 이 주제를 더 긴 상담 문단으로 풀어냅니다. "
            "타고난 성향, 현실의 일, 신중하게 다룰 시기를 함께 정리합니다."
        )
    return _block(f"{entry_id}-premium", "premium_teaser", f"{title} 프리미엄 안내", body)


def _life_overview_blocks(
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    strongest = _strongest_items(items, limit=2)
    axes = _top_axes(life_feature_summary, limit=2)
    axis_phrase = _axis_pair_phrase(axes)
    domain_phrase = _join_korean(_unique([f"{DOMAIN_NOUNS[item.domain]}운" for item in strongest])) or "주요 운세"
    period = _age_period(target_years, strongest[0] if strongest else None)
    blocks = [
        _block(
            "lifeOverview-core",
            "summary",
            "나의 사주 총운",
            f"당신은 {axis_phrase}{_subject_particle(axis_phrase)} 두드러지는 사람입니다. {period}에는 {domain_phrase}이 뚜렷하게 살아납니다.",
            tuple(item.domain for item in strongest),
        )
    ]
    natal_reality = _natal_reality_catalog_sentence(life_feature_summary)
    if natal_reality:
        blocks.append(
            _block(
                "lifeOverview-natal-reality",
                "natal_basis",
                "타고난 사주의 핵심 단서",
                natal_reality,
                tuple(item.domain for item in strongest),
            )
        )
    if strongest:
        item = strongest[0]
        keywords = _keyword_text(item)
        blocks.append(
            _block(
                "lifeOverview-focus",
                "focus",
                "대표 강점",
                f"{period}에는 {DOMAIN_NOUNS[item.domain]}운이 가장 뚜렷합니다. {keywords}{_subject_particle(keywords)} 먼저 생깁니다.",
                (item.domain,),
            )
        )
    return blocks


def _personality_blocks(items: list[ProductOutputItem], life_feature_summary: dict[str, Any]) -> list[ContentBlock]:
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS["personality_overview"], limit=3)
    caution = _caution_axis(life_feature_summary, ("변화 적응력", "표현 전달력"))
    source_profile = life_feature_summary.get("source_personality_profile")
    blocks = _source_personality_blocks(source_profile) if isinstance(source_profile, dict) else []
    if not blocks:
        blocks = [
            _block(
                "personality-core",
                "summary",
                "타고난 성향",
                _personality_summary_sentence(axes, caution),
            )
        ]
    if axes:
        blocks.append(
            _block(
                "personality-detail",
                "basis",
                "성향의 세부 기준",
                _axis_collection_sentence(axes, "성향에서는"),
            )
        )
    if caution:
        blocks.append(
            _block(
                "personality-caution",
                "caution",
                "성향에서 조심할 부분",
                _axis_caution_sentence(caution),
            )
        )
    return blocks


def _source_personality_blocks(source_profile: dict[str, Any]) -> list[ContentBlock]:
    day_profile = source_profile.get("day_pillar_profile")
    month_profile = source_profile.get("month_branch_profile")
    if not isinstance(day_profile, dict) and not isinstance(month_profile, dict):
        return []

    blocks: list[ContentBlock] = []
    day_type = _source_trait_text(day_profile, "compression_type")
    month_type = _source_trait_text(month_profile, "compression_type")
    day_traits = _source_trait_list(day_profile, "core_traits", limit=3)
    month_traits = _source_trait_list(month_profile, "core_traits", limit=3)
    strengths = _source_profile_keywords(source_profile, "strength_keywords", limit=3)
    shadows = _source_profile_keywords(source_profile, "shadow_keywords", limit=3)

    if day_type or month_type:
        type_phrase = " · ".join(value for value in (day_type, month_type) if value)
        core_phrase = _natural_keyword_phrase(day_traits or month_traits)
        body = f"당신의 성격은 {type_phrase}의 성향이 강합니다."
        if core_phrase:
            body += f" 기본 바탕에는 {core_phrase}{_subject_particle(core_phrase)} 놓입니다."
        blocks.append(_block("personality-source-core", "summary", "성격의 기본형", body))

    if month_profile and isinstance(month_profile, dict):
        month_title = _source_trait_text(month_profile, "title")
        month_core = _natural_keyword_phrase(month_traits)
        month_inner = _natural_keyword_phrase(_source_trait_list(month_profile, "inner_traits", limit=2))
        body_parts = []
        if month_title and month_core:
            body_parts.append(f"{month_title}의 영향으로 {month_core}{_subject_particle(month_core)} 사회적 태도에 더해집니다.")
        if month_inner:
            body_parts.append(f"겉으로는 차분해 보여도 안쪽에서는 {month_inner}{_subject_particle(month_inner)} 쉽게 사라지지 않습니다.")
        if body_parts:
            blocks.append(_block("personality-source-month", "basis", "월령이 더하는 성격", " ".join(body_parts)))

    if strengths:
        strength_phrase = _natural_keyword_phrase(strengths)
        blocks.append(
            _block(
                "personality-source-strength",
                "strength",
                "성격에서 잘 쓰는 힘",
                f"{strength_phrase}{_subject_particle(strength_phrase)} 장점으로 드러납니다. 한 가지 일에 기준이 생기면 집중력과 지속성이 분명해집니다.",
            )
        )

    if shadows:
        shadow_phrase = _natural_keyword_phrase(shadows)
        blocks.append(
            _block(
                "personality-source-caution",
                "caution",
                "성격에서 조심할 부분",
                f"{shadow_phrase}{_subject_particle(shadow_phrase)} 강해질 때 판단이 좁아질 수 있습니다. 이때는 바로 결론을 내리기보다 손해와 책임 범위를 먼저 확인하는 편이 좋습니다.",
            )
        )
    return blocks


def _source_trait_text(profile: Any, key: str) -> str:
    if not isinstance(profile, dict):
        return ""
    return _compact(str(profile.get(key) or ""))


def _source_trait_list(profile: Any, key: str, limit: int) -> list[str]:
    if not isinstance(profile, dict):
        return []
    values = profile.get(key)
    if not isinstance(values, list):
        return []
    return [_compact(str(value)) for value in values if _compact(str(value))][:limit]


def _source_profile_keywords(source_profile: dict[str, Any], key: str, limit: int) -> list[str]:
    values = source_profile.get(key)
    if not isinstance(values, list):
        return []
    return [_compact(str(value)) for value in values if _compact(str(value))][:limit]


def _natural_keyword_phrase(keywords: list[str]) -> str:
    filtered = [keyword for keyword in keywords if keyword]
    if not filtered:
        return ""
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 2:
        return f"{filtered[0]}{_and_particle(filtered[0])} {filtered[1]}"
    return f"{filtered[0]}, {filtered[1]}, {filtered[2]}"


def _and_particle(text: str) -> str:
    return "과" if _has_final_consonant(text) else "와"


def _personality_summary_sentence(axes: list[dict[str, Any]], caution: dict[str, Any] | None) -> str:
    main = axes[0] if axes else None
    main_label = _field_text(main, "label", "") if main else ""
    main_clause = _axis_short_clause(main, default="현실 판단과 책임 기준")
    if main_label == "현실 설계력":
        main_subject = "돈과 일의 기준을 먼저 정리하는 사람"
    elif main_label == "변화 적응력":
        main_subject = "상황이 바뀌면 행동 기준을 다시 세우는 적응형"
    elif main_clause.endswith("힘"):
        main_subject = f"{main_clause}이 강한 사람"
    else:
        main_subject = f"{main_clause}{_object_particle(main_clause)} 중요하게 보는 사람"
    if caution:
        caution_raw_label = _field_text(caution, "label", "표현 방식")
        if caution_raw_label == "변화 적응력":
            return f"당신은 {main_subject}입니다. 다만 상황이 바뀐 뒤 결정을 오래 미루면 피로가 쌓입니다."
        caution_label = _axis_customer_label(caution_raw_label)
        caution_subject = caution_label.replace("하는 힘", "하는 일") if caution_label.endswith("힘") else caution_label
        return f"당신은 {main_subject}입니다. 다만 {caution_subject}{_topic_particle(caution_subject)} 늦어지면 피로가 쌓입니다."
    return f"당신은 {main_subject}입니다. 생각을 현실적인 기준으로 정리할 때 장점이 행동으로 옮겨집니다."


def _annual_overview_blocks(items: list[ProductOutputItem], target_years: list[int]) -> list[ContentBlock]:
    strongest = _strongest_items(items, limit=2)
    period = _period([CURRENT_FORTUNE_YEAR])
    if not strongest:
        return [_block("annualOverview-core", "summary", "올해 총운", f"{period}에는 전체 운세가 큰 변화보다 정리에 가깝습니다. 특히 달라지는 영역이 따로 생기고, 그 이후 현실 선택이 나뉩니다.")]
    main = strongest[0]
    second = strongest[1] if len(strongest) > 1 else None
    keywords = _keyword_text(main)
    action_subject = _action_subject(main.action)
    domain_core = {
        "money": "올해 돈 문제는 받을 금액과 남길 금액이 갈립니다.",
        "career": "올해 일은 맡을 범위가 넓어지고 평가받는 자리도 달라집니다.",
        "love": "올해 연애는 연락의 안정감이 중심입니다.",
        "marriage": "올해 결혼은 생활비와 주거 문제가 앞으로 나옵니다.",
    }.get(main.domain, f"올해는 {DOMAIN_NOUNS[main.domain]}운의 기준이 잡힙니다.")
    second_core = {
        "money": "재물 문제도 달라집니다. 받을 돈도 보입니다.",
        "career": "직업 문제도 함께 달라집니다. 맡을 역할도 정해집니다.",
        "love": "연애 문제도 함께 달라집니다. 관계의 거리도 달라집니다.",
        "marriage": "결혼 문제도 함께 달라집니다. 생활 문제도 정리됩니다.",
    }
    body = (
        f"{period}에는 {DOMAIN_NOUNS[main.domain]}운이 가장 뚜렷합니다. "
        f"{keywords}{_subject_particle(keywords)} 선택의 기준이 됩니다. "
        f"{domain_core} "
        f"올해 {DOMAIN_NOUNS[main.domain]}운의 출발점은 {action_subject}입니다."
    )
    if second and second.domain != main.domain:
        body += " " + second_core.get(
            second.domain,
            f"{DOMAIN_NOUNS[second.domain]} 문제도 함께 달라집니다. 현실 기준도 정해집니다.",
        )
    return [_block("annualOverview-core", "summary", "올해 총운", body, tuple(item.domain for item in strongest))]


def _advice_blocks(
    entry_id: str,
    title: str,
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    strongest = _strongest_items(items, limit=1)
    caution = _highest_risk_item(items)
    axes = _top_axes(life_feature_summary, limit=2)
    base = strongest[0] if strongest else None
    if entry_id == "premium_core_five":
        statements = _premium_core_statements(items, life_feature_summary, target_years)
        return [
            _block(
                "premiumCoreFive-summary",
                "summary",
                title,
                " ".join(statements[:3]),
                tuple(item.domain for item in items[:4]),
            )
        ]
    if entry_id == "annual_best" and base:
        keywords = _keyword_text(base)
        action_subject = _action_subject(base.action)
        return [
            _block(
                "annualBest-core",
                "summary",
                title,
                _annual_best_market_sentence(base, keywords, action_subject),
                (base.domain,),
            )
        ]
    if entry_id == "annual_caution" and caution:
        return [
            _block(
                "annualCaution-core",
                "caution",
                title,
                f"{_period([CURRENT_FORTUNE_YEAR])}에 가장 신중하게 다룰 운은 {DOMAIN_NOUNS[caution.domain]}운입니다. {caution.risk}이 반복되면 결정이 늦어집니다. 기준을 다시 세우는 일도 생깁니다. 올해는 초반 부담을 줄이며 결정 여유가 생깁니다.",
                (caution.domain,),
            )
        ]
    if entry_id == "success_advice":
        return _success_advice_blocks(title, strongest, caution, axes)
    if entry_id == "final_money_work_relationship_advice":
        return _final_advice_blocks(title, items, caution, axes)
    if caution:
        return [
            _block(
                "annualCaution-core",
                "caution",
                title,
                f"가장 신중하게 다룰 영역은 {DOMAIN_NOUNS[caution.domain]}입니다. {caution.risk}이 반복되면 기회가 커져도 부담이 남습니다.",
                (caution.domain,),
            )
        ]
    return [_block(f"{entry_id}-core", "advice", title, "좋은 시기는 기준이 먼저 잡힐 때 강하게 쓰입니다.")]


def _success_advice_blocks(
    title: str,
    strongest: list[ProductOutputItem],
    caution: ProductOutputItem | None,
    axes: list[dict[str, Any]],
) -> list[ContentBlock]:
    base = strongest[0] if strongest else None
    axis_label = str(axes[0].get("label") or "가장 강한 장점") if axes else "가장 강한 장점"
    second_axis = str(axes[1].get("label") or "") if len(axes) > 1 else ""
    axis_event = _axis_customer_event(axis_label, default="가장 강한 장점")
    body = f"당신의 성공운은 {axis_event}{_subject_particle(axis_event)} 먼저 강해질 때 크게 좋아집니다."
    if second_axis:
        second_event = _axis_customer_event(second_axis, default=second_axis)
        body += f" 함께 살릴 장점은 {second_event}입니다."
    if base:
        body += f" 특히 {DOMAIN_NOUNS[base.domain]}에서는 {base.action}이 성과를 남기는 기준입니다."
    if caution:
        body += f" 다만 {caution.risk}은 초기에 관리될 때 부담이 작아집니다."
    return [_block("successAdvice-core", "advice", title, body, tuple(item.domain for item in strongest))]


def _annual_best_market_sentence(base: ProductOutputItem, keywords: str, action_subject: str) -> str:
    period = _period([CURRENT_FORTUNE_YEAR])
    particle = _subject_particle(keywords)
    action_particle = _subject_particle(action_subject)
    if base.domain == "money":
        return (
            f"{period}에 가장 잘 풀리는 운은 재물운입니다. "
            f"{keywords}{particle} 돈이 생기는 계기가 됩니다. "
            f"{action_subject}{action_particle} 손에 남는 금액을 키웁니다."
        )
    if base.domain == "career":
        action_sentence = (
            f"{action_subject}{_object_particle(action_subject)} 확보하며 인정받을 자리가 생깁니다."
            if "권한" in action_subject or "결정권" in action_subject
            else f"{action_subject}{_object_particle(action_subject)} 맡으며 인정받을 자리가 생깁니다."
        )
        return (
            f"{period}에 가장 잘 풀리는 운은 직업운입니다. "
            f"{keywords}{particle} 인정받는 계기가 됩니다. "
            f"자리 변화도 함께 생깁니다. "
            f"{action_sentence}"
        )
    if base.domain == "love":
        return (
            f"{period}에 가장 잘 풀리는 운은 연애운입니다. "
            f"{keywords}{particle} 인연과 연락으로 이어집니다. "
            f"{action_subject}{action_particle} 관계가 가까워지는 계기가 됩니다."
        )
    if base.domain == "marriage":
        return (
            f"{period}에 가장 잘 풀리는 운은 결혼운입니다. "
            f"{keywords}{particle} 결혼 이야기와 생활 약속으로 이어집니다. "
            f"{action_subject}{action_particle} 약속을 구체화합니다."
        )
    return (
        f"{period}에 가장 잘 풀리는 운은 {DOMAIN_NOUNS[base.domain]}운입니다. "
        f"{keywords}{particle} 올해 중요한 일이 됩니다. "
        f"{action_subject}{action_particle} 중요한 일을 앞당깁니다."
    )


def _final_advice_blocks(
    title: str,
    items: list[ProductOutputItem],
    caution: ProductOutputItem | None,
    axes: list[dict[str, Any]],
) -> list[ContentBlock]:
    strongest = _strongest_items(items, limit=2)
    primary_axis = _axis_customer_label(str(axes[0].get("label") or "현실 판단력")) if axes else "현실 판단력"
    domain_phrase = _join_korean(_unique([f"{DOMAIN_NOUNS[item.domain]}운" for item in strongest])) or "주요 운세"
    body = (
        f"최종 조언의 중심은 {primary_axis}입니다. "
        f"{domain_phrase}은 한 가지 선택 안에서 갈립니다. "
        "돈은 받을 금액보다 남길 금액이 먼저 정리됩니다. "
        "직업에서는 결정권이 잡힐 때 평가가 붙습니다. "
        "가까운 관계는 같은 시기에 피로가 커집니다."
    )
    if strongest:
        body += f" 이번 선택에서 가장 먼저 다룰 일은 {_action_subject(strongest[0].action)}입니다."
    if len(strongest) > 1:
        body += f" 그다음에는 {DOMAIN_NOUNS[strongest[1].domain]}운도 함께 정리됩니다. {_action_subject(strongest[1].action)}도 같은 시기에 다루게 됩니다."
    if caution:
        body += f" {caution.risk}을 늦게 다루면 좋은 시기에도 부담이 남습니다."
    return [_block("finalAdvice-core", "advice", title, body, tuple(item.domain for item in strongest))]


def _money_catalog_blocks(
    entry_id: str,
    title: str,
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    item = _best_item_for_domain(items, "money")
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()), limit=3)
    blocks: list[ContentBlock] = [
        _block(
            f"{entry_id}-money-summary",
            "summary",
            title,
            _money_lead_sentence(entry_id, title, axes, item, target_years),
            ("money",),
        )
    ]
    reality = _domain_reality_catalog_sentence("money", life_feature_summary) if entry_id in NATAL_BASIS_ENTRY_IDS else ""
    if reality:
        blocks.append(
            _block(
                f"{entry_id}-money-reality",
                "natal_basis",
                "원국에서 확인되는 돈의 단서",
                reality,
                ("money",),
            )
        )
    if axes:
        blocks.append(
            _block(
                f"{entry_id}-money-basis",
                "basis",
                "재물운이 돈으로 남는 기준",
                _axis_collection_sentence(axes, "당신의 재물운은"),
                ("money",),
            )
        )
    if item and entry_id in {"annual_money", "money_caution_years"}:
        blocks.append(
            _block(
                f"{entry_id}-money-event",
                "timing" if entry_id == "annual_money" else "timing_caution",
                "올해 돈에서 눈여겨볼 일",
                _event_sentence(item) if entry_id == "annual_money" else f"{_timing_point(item)}에는 재물 문제를 신중하게 다뤄야 합니다. 주의할 부분은 {item.risk}입니다.",
                ("money",),
            )
        )
    elif item:
        blocks.append(
            _block(
                f"{entry_id}-money-action",
                "action",
                "돈을 다룰 때의 기준",
                _catalog_action_sentence(entry_id, title, ("money",), item, target_years),
                ("money",),
            )
        )
    caution_axis = _caution_axis(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()))
    if caution_axis:
        blocks.append(_block(f"{entry_id}-money-caution", "caution", "주의할 점", _entry_axis_caution_sentence(entry_id, caution_axis), ("money",)))
    return blocks


def _money_lead_sentence(
    entry_id: str,
    title: str,
    axes: list[dict[str, Any]],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    axis = axes[0] if axes else None
    axis_clause = _axis_short_clause(axis, default="돈을 남기는 순서를 세우는 능력")
    if entry_id == "native_money":
        return f"당신은 돈을 어디에 남길지 분명할수록 재물 수준이 올라갑니다. 돈이 들어온 뒤 자산으로 남기는 능력이 강합니다."
    if entry_id == "money_attitude":
        return f"당신은 돈을 쓰기 전에 목적과 한도를 따지는 사람입니다. 충동보다 오래 남길 금액을 먼저 계산합니다. 그래서 소비도 비교적 차분해지고, 저축과 투자 선택도 쉽게 흔들리지 않습니다."
    if entry_id == "native_wealth_level":
        return f"당신의 선천 재물 수준은 벌어들인 돈이 얼마나 오래 남는지에서 높아집니다. {axis_clause}{_subject_particle(axis_clause)} 분명해지며 재물운도 강해집니다."
    if entry_id == "income_expansion_method":
        return f"수입은 해낸 일이 얼마로 인정되는지에서 커집니다. 지급일이 정해지며 손에 남는 돈도 올라갑니다. {axis_clause}{_subject_particle(axis_clause)} 분명할수록 수입도 커집니다."
    if entry_id == "wealth_retention_conditions":
        return f"돈이 남는 힘은 벌어들인 뒤의 순서에서 생깁니다. 당신은 고정비와 저축을 먼저 나눕니다. 재투자와 예비 자금까지 따로 나뉘며 수입이 자산으로 남습니다."
    if entry_id == "money_leak_conditions":
        return f"주의가 필요한 지점은 약속이 느슨한 거래에서 시작됩니다. 정산이 늦어질 때도 부담이 커집니다. 돈이 들어오기 전부터 받을 시점과 금액을 확인합니다."
    if entry_id == "wealth_potential":
        return f"당신은 돈이 될 만한 일을 비교적 빨리 알아봅니다. 그 일이 수입으로 바뀌는 과정도 함께 계산합니다. {axis_clause}을 제대로 쓸수록 재물 규모가 커집니다."
    if entry_id == "income_expansion_power":
        return f"당신은 해낸 일이 금액으로 인정될 때 수입이 커집니다. 보상 기준이 구체적일수록 받을 금액도 올라갑니다. 지급일이 정해지며 늘어난 수입이 손에 남습니다."
    if entry_id == "asset_retention_power":
        return f"당신은 한 번 들어온 돈을 쉽게 흘려보내지 않습니다. 지출 한도를 먼저 잡습니다. 저축 방식도 따로 정하고, 오래 가져갈 자산도 구분해 둡니다."
    if entry_id == "investment_trade_sense":
        return f"투자와 거래에서는 빠져나올 길이 중요합니다. 당신은 계약 구조를 먼저 읽습니다. 손실 한도가 보일 때 돈을 더 안정적으로 지킵니다."
    if entry_id == "business_expansion_power":
        return f"사업 확장은 거래처와 매출이 늘어나는 만큼 비용도 커집니다. 인력과 책임 범위도 함께 늘어납니다. 당신은 규모를 키우기 전에 감당할 범위를 정하며 이익을 남깁니다."
    if entry_id == "money_caution_years":
        if item:
            return f"재물 문제로 신중해야 할 때는 {_age_period(target_years, item)}입니다. 이 시기에는 계약을 보수적으로 봅니다. 정산과 지출도 보수적으로 다룹니다."
        return "재물 문제로 신중하게 다룰 시기에는 계약, 정산, 지출 순서가 흔들립니다."
    if entry_id == "annual_money" and item:
        keywords = _keyword_text(item)
        return f"{_period([CURRENT_FORTUNE_YEAR])} 재물운은 {keywords}{_subject_particle(keywords)} 받을 돈의 크기를 정합니다. 해낸 일이 금액으로 확정되며 손에 남는 돈도 커집니다."
    return f"{title}에서는 {axis_clause}{_subject_particle(axis_clause)} 뚜렷합니다. 돈이 생긴 뒤 무엇이 남는지가 결론입니다."


def _domain_catalog_blocks(
    entry_id: str,
    title: str,
    domain: Domain,
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    item = _best_item_for_domain(items, domain)
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()), limit=3)
    blocks: list[ContentBlock] = []
    if axes:
        blocks.append(_block(f"{entry_id}-axis", "summary", title, _domain_axis_lead_sentence(title, domain, axes), (domain,)))
        blocks.append(_block(f"{entry_id}-basis", "basis", "세부 해석", _axis_collection_sentence(axes, f"{title}에서는"), (domain,)))
    elif item:
        blocks.append(_block(f"{entry_id}-event", "summary", title, _event_sentence(item), (domain,)))
    else:
        blocks.append(_block(f"{entry_id}-summary", "summary", title, f"{title}은 타고난 특성과 {DOMAIN_SCENES[domain]}이 맞물리며 실제 운세가 정해집니다.", (domain,)))

    reality = _domain_reality_catalog_sentence(domain, life_feature_summary) if entry_id in NATAL_BASIS_ENTRY_IDS else ""
    if reality:
        blocks.append(
            _block(
                f"{entry_id}-reality",
                "natal_basis",
                "원국에서 확인되는 현실 단서",
                reality,
                (domain,),
            )
        )

    if item:
        blocks.append(
            _block(
                f"{entry_id}-action",
                "action",
                "도움 되는 기준",
                _catalog_action_sentence(entry_id, title, (domain,), item, target_years),
                (domain,),
            )
        )
    caution_axis = _caution_axis(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()))
    if caution_axis:
        blocks.append(_block(f"{entry_id}-caution", "caution", "주의할 점", _entry_axis_caution_sentence(entry_id, caution_axis), (domain,)))
    return blocks


def _domain_axis_lead_sentence(title: str, domain: Domain, axes: list[dict[str, Any]]) -> str:
    axis = axes[0] if axes else None
    axis_clause = _axis_short_clause(axis, default=f"{title}의 핵심 기준")
    career_tail = _stable_title_variant(
        title,
        (
            "맡은 일이 문서나 결과로 확인될 때 인정이 빨라집니다. 결정권이 있는 자리에서 직업 만족도도 높습니다. 책임 범위가 분명한 자리에서는 다음 역할도 맡게 됩니다.",
            "역할이 커질수록 책임도 커집니다. 결과가 보이는 자리에서 신뢰를 얻습니다. 책임 범위가 분명할수록 실력도 오래 인정됩니다.",
            "이름만 큰 직함보다 실제 권한과 결과가 있는 업무가 맞습니다. 결과가 보이면 평가도 빨라집니다. 책임이 분명한 자리에서는 다음 역할도 맡게 됩니다.",
        ),
    )
    love_tail = _stable_title_variant(
        title,
        (
            "표현 방식이 마음의 거리를 바꿉니다. 연락의 간격이 맞을수록 마음도 안정됩니다.",
            "호감은 말투와 연락에서 먼저 생깁니다. 기대가 편안하게 전달될 때 관계가 오래 갑니다.",
            "감정의 크기보다 전달 방식이 앞섭니다. 거리감이 맞을 때 관계가 자연스럽게 깊어집니다.",
        ),
    )
    marriage_tail = _stable_title_variant(
        title,
        (
            "애정은 생활 안에서 확인됩니다. 돈의 기준과 주거 문제가 맞물릴 때 결혼 생활이 안정됩니다.",
            "결혼은 말보다 생활에서 확인됩니다. 책임의 나눔이 선명해질 때 약속도 오래 갑니다.",
            "좋아하는 마음은 결혼의 출발입니다. 생활비와 가족 책임이 정리될 때 결혼운이 안정됩니다.",
        ),
    )
    if domain == "career":
        return _axis_lead_sentence(title, axis_clause, career_tail)
    if domain == "love":
        return _axis_lead_sentence(title, axis_clause, love_tail)
    if domain == "marriage":
        return _axis_lead_sentence(title, axis_clause, marriage_tail)
    return f"당신은 {axis_clause}{_subject_particle(axis_clause)} 뚜렷합니다."


def _axis_lead_sentence(title: str, axis_clause: str, tail: str) -> str:
    title_head = title.replace("·", " ").split("과")[0].split()[0].strip()
    if title_head and axis_clause.startswith(title_head):
        return f"{axis_clause}{_subject_particle(axis_clause)} 뚜렷합니다. {tail}"
    return f"{title}에서는 {axis_clause}{_subject_particle(axis_clause)} 뚜렷합니다. {tail}"


def _relationship_catalog_blocks(
    entry_id: str,
    title: str,
    domain: Domain,
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    item = _best_item_for_domain(items, domain)
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()), limit=3)
    blocks: list[ContentBlock] = [
        _block(
            f"{entry_id}-relationship-summary",
            "summary",
            title,
            _relationship_lead_sentence(entry_id, title, domain, axes, item, target_years),
            (domain,),
        )
    ]
    reality = _domain_reality_catalog_sentence(domain, life_feature_summary) if entry_id in NATAL_BASIS_ENTRY_IDS else ""
    if reality:
        blocks.append(
            _block(
                f"{entry_id}-relationship-reality",
                "natal_basis",
                "원국에서 확인되는 관계 단서",
                reality,
                (domain,),
            )
        )
    if domain == "love":
        blocks.append(
            _block(
                f"{entry_id}-emotion",
                "emotion",
                "감정 양상",
                _love_emotion_sentence(entry_id, axes, item),
                ("love",),
            )
        )
        blocks.append(
            _block(
                f"{entry_id}-condition",
                "condition",
                "관계가 이어지는 기준",
                _love_condition_sentence(entry_id, axes, item),
                ("love",),
            )
        )
    else:
        blocks.append(
            _block(
                f"{entry_id}-emotion",
                "emotion",
                "감정 양상",
                _marriage_emotion_sentence(entry_id, axes, item),
                ("marriage",),
            )
        )
        blocks.append(
            _block(
                f"{entry_id}-life-condition",
                "condition",
                "생활 기준",
                _marriage_condition_sentence(entry_id, axes, item),
                ("marriage",),
            )
        )
    if item:
        blocks.append(
            _block(
                f"{entry_id}-action",
                "action",
                "도움 되는 기준",
                _catalog_action_sentence(entry_id, title, (domain,), item, target_years),
                (domain,),
            )
        )
    return blocks


def _relationship_lead_sentence(
    entry_id: str,
    title: str,
    domain: Domain,
    axes: list[dict[str, Any]],
    item: ProductOutputItem | None,
    target_years: list[int],
) -> str:
    axis_clause = _axis_short_clause(axes[0] if axes else None, default="관계의 기준을 정하는 능력")
    if domain == "love":
        if entry_id == "annual_love" and item:
            keywords = _keyword_text(item)
            return f"{_period([CURRENT_FORTUNE_YEAR])} 연애운에서는 {keywords}{_subject_particle(keywords)} 먼저 생깁니다. 말투가 거칠어지면 관계가 빨리 흔들립니다. 편안한 거리가 정해지며 마음도 오래 갑니다."
        if entry_id == "relationship_social":
            return "당신은 사람과 가까워질 때 호감보다 속도를 더 민감하게 느낍니다. 편안한 간격이 정해지며 관계도 오래갑니다."
        return "당신은 마음을 천천히 여는 신중 애정형입니다. 상대의 태도가 꾸준해야 마음도 깊어집니다."
    if entry_id == "spouse_conflict_points":
        return "당신은 배우자와 서로 깊이 좋아하더라도 감정 표현이 어긋나면 부딪힙니다. 돈을 쓰는 방식이 달라도 충돌이 커집니다. 가족 책임은 따로 말해야 합니다."
    if entry_id == "marriage_stability_conditions":
        return "결혼 생활에서는 생활비와 주거 문제가 일찍 정리됩니다. 생활의 불안도 줄어듭니다."
    if entry_id == "children_family_luck":
        return "자식·가정운에서는 가족 안의 책임 분담을 먼저 다루게 됩니다. 가까운 사람을 챙기는 마음이 커질수록 생활 부담도 커집니다."
    return f"당신의 결혼운에서는 {axis_clause}{_subject_particle(axis_clause)} 결혼 생활의 중심이 됩니다. 마음이 깊어도 사는 방식이 어긋나면 불편함이 오래 남습니다. 책임을 나누는 방식도 결혼 뒤에 계속 중요해집니다."


def _love_emotion_sentence(entry_id: str, axes: list[dict[str, Any]], item: ProductOutputItem | None) -> str:
    if item:
        keywords = _keyword_text(item)
        entry_templates = {
            "relationship_social": (
                f"사람이 가까워질수록 당신은 {keywords}{_object_particle(keywords)} 더 민감하게 느낍니다.",
                "호감보다 관계의 간격을 먼저 살피게 됩니다. 상대의 기대가 빠르게 들어오면 마음이 쉽게 지칩니다.",
            ),
            "love_precision": (
                f"연애가 구체적인 관계로 옮겨질수록 {keywords}{_subject_particle(keywords)} 더 크게 느껴집니다.",
                "감정이 커질수록 표현의 속도를 맞추려 합니다. 연락이 들쭉날쭉하면 마음도 쉽게 지칩니다.",
            ),
            "native_love": (
                f"좋아하는 마음이 깊어질수록 {keywords}{_subject_particle(keywords)} 더 크게 느껴집니다.",
                "표현이 늦어지면 상대의 확신도 늦어집니다. 기대가 엇갈리면 연락부터 불편해집니다.",
            ),
            "annual_love": (
                f"{_period([CURRENT_FORTUNE_YEAR])}에는 {keywords}{_subject_particle(keywords)} 먼저 생깁니다.",
                "좋아하는 마음은 분명해도 거리감이 어긋나면 관계가 늦게 안정됩니다. 만남의 속도가 편안해지며 감정도 오래 갑니다.",
            ),
        }
        lead, tail = entry_templates.get(
            entry_id,
            (
                f"관계가 가까워질수록 {keywords}{_subject_particle(keywords)} 더 크게 느껴집니다.",
                "감정이 커질수록 표현의 속도를 맞추려 합니다. 연락이 들쭉날쭉하면 마음도 쉽게 지칩니다.",
            ),
        )
        return f"{lead} {tail}"
    axis_clause = _axis_short_clause(axes[0] if axes else None, default="표현 방식")
    return f"관계가 가까워질수록 {axis_clause}{_subject_particle(axis_clause)} 마음의 거리를 바꿉니다. 전달 방식이 편안해지면서 마음도 오래 갑니다."


def _love_condition_sentence(entry_id: str, axes: list[dict[str, Any]], item: ProductOutputItem | None) -> str:
    if item:
        action_subject = _action_subject(item.action)
        entry_templates = {
            "relationship_social": (
                f"대인관계에서는 {action_subject}{_subject_particle(action_subject)} 관계의 피로를 줄입니다.",
                "서로의 간격이 정해지며 관계도 오래 갑니다.",
            ),
            "love_precision": (
                f"연애에서는 {action_subject}{_subject_particle(action_subject)} 만남의 분위기를 다르게 합니다.",
                "연락 방식을 말로 맞추게 되며 같은 오해가 줄어듭니다. 기대하는 바도 초기에 말하게 됩니다.",
            ),
            "native_love": (
                f"관계가 시작될 때는 {action_subject}{_subject_particle(action_subject)} 마음을 안정시킵니다.",
                "표현 방식이 부드러워지며 호감이 오래 갑니다. 관계의 부담도 줄어듭니다.",
            ),
            "annual_love": (
                f"{_period([CURRENT_FORTUNE_YEAR])}에는 기대치를 먼저 말로 꺼내게 됩니다.",
                "만남의 간격이 편안해지며 관계가 안정됩니다. 서로 원하는 속도도 함께 맞춰집니다.",
            ),
        }
        lead, tail = entry_templates.get(
            entry_id,
            (
                f"관계가 이어질 때는 {action_subject}{_subject_particle(action_subject)} 만남의 분위기를 다르게 합니다.",
                "연락 방식을 말로 맞추게 되며 같은 오해가 줄어듭니다. 기대하는 바도 초기에 말하게 됩니다.",
            ),
        )
        return f"{lead} {tail}"
    return f"관계가 이어지는 과정에서는 {_axis_short_clause(axes[-1] if axes else None, default='거리 조절')}이 현실적인 부담이 됩니다."


def _marriage_emotion_sentence(entry_id: str, axes: list[dict[str, Any]], item: ProductOutputItem | None) -> str:
    if item:
        keywords = _keyword_text(item)
        keyword_phrase = "결혼 준비" if keywords == "약속 준비" else keywords
        entry_templates = {
            "marriage_precision": (
                f"결혼 이야기가 구체적인 준비로 넘어갑니다. 이때는 {keyword_phrase}{_object_particle(keyword_phrase)} 더 진지하게 다룹니다.",
                "말이 거칠어지면 회복이 늦습니다.",
            ),
            "spouse_conflict_points": (
                f"배우자와 가까워질수록 {keyword_phrase}{_object_particle(keyword_phrase)} 더 자주 마주하게 됩니다.",
                "서로 좋아해도 말투의 차이 때문에 충돌이 생깁니다. 기대 차이를 늦게 말하면 다툼이 길어집니다.",
            ),
            "marriage_stability_conditions": (
                f"결혼 생활을 안정시키려 할수록 {keyword_phrase}{_object_particle(keyword_phrase)} 먼저 정리하게 됩니다.",
                "안정을 바라는 마음이 커지는 만큼 서로 원하는 생활의 모습도 분명히 말합니다.",
            ),
            "children_family_luck": (
                f"가정 안에서는 {keyword_phrase}{_subject_particle(keyword_phrase)} 구체화될수록 맡아야 할 몫도 늘어납니다.",
                "책임이 한쪽으로 몰리면 서운함이 커집니다.",
            ),
            "native_marriage": (
                f"결혼을 생각할수록 {keyword_phrase}{_subject_particle(keyword_phrase)} 마음의 부담이 됩니다.",
                "가족 문제가 나오면 마음이 곧바로 현실을 봅니다.",
            ),
        }
        lead, tail = entry_templates.get(
            entry_id,
            (
                f"결혼 이야기가 구체적인 준비로 넘어갑니다. 이때는 {keyword_phrase}{_object_particle(keyword_phrase)} 더 진지하게 다룹니다.",
                "결혼이 가까워질수록 안정을 바라는 마음이 커집니다. 원하는 생활의 모습이 다르면 감정도 쉽게 예민해집니다.",
            ),
        )
        return f"{lead} {tail}"
    return "결혼 이야기가 구체적인 준비로 옮겨질수록 표현 방식이 결혼 생활에 깊게 남습니다. 기대가 다를 때는 이야기가 길어집니다."


def _marriage_condition_sentence(entry_id: str, axes: list[dict[str, Any]], item: ProductOutputItem | None) -> str:
    if item:
        action_subject = _action_subject(item.action)
        entry_tails = {
            "marriage_precision": "생활비는 초기에 이야기하게 됩니다. 주거 문제는 결혼 생활에 직접 영향을 줍니다.",
            "spouse_conflict_points": "돈을 쓰는 방식이 다르면 충돌이 커집니다.",
            "marriage_stability_conditions": "주거 계획이 분명해질 때 결혼 부담이 줄어듭니다. 생활비 이야기는 늦게 넘기지 않습니다.",
            "children_family_luck": "역할 분담이 보이면 생활의 긴장이 줄어듭니다. 가족 책임은 따로 남습니다.",
            "native_marriage": "생활비는 초기에 이야기하게 됩니다. 주거 문제가 정리되면 결혼 생활의 긴장도 줄어듭니다.",
        }
        tail = entry_tails.get(
            entry_id,
            "생활비는 초기에 이야기하게 됩니다. 주거 문제는 결혼 생활의 편안함에 직접 영향을 줍니다. 가족과의 거리도 따로 정리됩니다.",
        )
        if "결혼 의사" in action_subject and ("생활 기준" in action_subject or "생활 방식" in action_subject):
            entry_leads = {
                "marriage_precision": "생활에서는 결혼 의사와 생활 방식을 같은 자리에서 맞춥니다.",
                "spouse_conflict_points": "부딪힐 때는 결혼 의사보다 생활 방식의 차이가 먼저 커집니다.",
                "marriage_stability_conditions": "결혼 생활은 생활비와 주거 문제가 정리될수록 안정됩니다.",
                "children_family_luck": "가정 안에서는 역할 분담과 생활 방식을 함께 맞춥니다.",
                "native_marriage": "결혼을 생각할 때는 마음과 생활 방식을 함께 맞춥니다.",
            }
            return f"{entry_leads.get(entry_id, '생활에서는 결혼 의사와 생활 방식을 같은 자리에서 맞춥니다.')} {tail}"
        if "압박" in action_subject or "부담" in action_subject:
            return f"생활에서는 {action_subject}{_object_particle(action_subject)} 먼저 꺼내게 됩니다. {tail}"
        if action_subject in {"돈의 기준 정리", "돈 문제 정리"}:
            return f"생활에서는 생활비와 주거 문제를 먼저 맞춥니다. {tail}"
        return f"생활에서는 {action_subject}{_object_particle(action_subject)} 먼저 맞춥니다. {tail}"
    return f"생활에서는 {_axis_short_clause(axes[0] if axes else None, default='책임 분담')}이 결혼 안정의 핵심입니다. 결혼은 감정과 실제 생활이 함께 맞아 갈 때 안정됩니다."


def _career_field_blocks(entry_id: str, title: str, life_feature_summary: dict[str, Any]) -> list[ContentBlock]:
    primary = _first_dict(life_feature_summary.get("primary_career_fields"))
    caution = _first_dict(life_feature_summary.get("caution_career_fields"))
    style = _first_dict(life_feature_summary.get("top_career_work_styles"))
    if entry_id == "career_mismatch_conditions" and caution:
        condition = _field_text(caution, "primary_unsuitable_condition", "권한과 책임이 맞지 않는 자리")
        return [
            _block(
                "careerMismatch-core",
                "caution",
                title,
                f"{_field_text(caution, 'label', '해당 분야')}은 우선순위를 낮추는 편이 좋습니다. {condition}에서는 능력을 써도 실력으로 인정받기 어렵고, 소모가 커집니다.",
                ("career",),
            )
        ]
    if entry_id == "organization_success_method" and style:
        body = f"당신은 {_field_text(style, 'label', '조직형')} 업무에서 강점을 잘 씁니다. {_field_text(style, 'role_sentence', '맡은 몫과 책임이 보이는 자리에서 안정적으로 성취하는 성향입니다.')}"
        if primary:
            body += f" 특히 {_field_text(primary, 'label', '잘 맞는 분야')}처럼 맡은 역할과 평가 방식이 분명한 업무에서 실력을 인정받습니다."
        return [
            _block(
                "organizationSuccess-core",
                "summary",
                title,
                body,
                ("career",),
            )
        ]
    if primary:
        sub_role = _first_dict(primary.get("sub_roles"))
        field_label = _field_text(primary, "label", "현재 강점이 잘 쓰이는 분야")
        role_style = _field_text(primary, "role_style", "업무의 순서와 책임을 정리하는 역할에서 실력을 인정받습니다.")
        condition = _field_text(primary, "primary_unsuitable_condition", "책임은 크고 결정권이 약한 자리")
        if entry_id == "expertise_recognition_method":
            body = f"전문성은 {field_label} 분야에서 가장 잘 평가받습니다. {role_style}"
            if sub_role:
                body += f" 특히 {_field_text(sub_role, 'label', '세부 직무')}처럼 {_field_text(sub_role, 'role_sentence', '맡은 일이 또렷한 업무')}을 맡을 때 실력으로 인정받습니다."
            return [
                _block("careerExpertise-core", "summary", title, body, ("career",)),
                _block(
                    "careerExpertise-caution",
                    "caution",
                    "전문성이 약해지는 조건",
                    f"{condition}에서는 실력이 있어도 인정으로 이어지기 어렵습니다.",
                    ("career",),
                ),
            ]
        summary_body = f"당신에게 가장 잘 맞는 분야는 {field_label}입니다. {role_style}"
        blocks = [
            _block(
                "careerField-core",
                "summary",
                title,
                summary_body,
                ("career",),
            )
        ]
        if sub_role:
            blocks.append(
                _block(
                    "careerField-role",
                    "role",
                    "강점이 쓰이는 세부 역할",
                    f"세부적으로는 {_field_text(sub_role, 'label', '해당 직무')}처럼 {_field_text(sub_role, 'role_sentence', '맡은 일이 또렷한 업무')}을 맡을 때 실력을 인정받습니다.",
                    ("career",),
                )
            )
        if primary.get("income_link"):
            blocks.append(
                _block(
                    "careerField-income",
                    "money_link",
                    "수입과 연결되는 방식",
                    str(primary.get("income_link")),
                    ("career", "money"),
                )
            )
        if primary.get("primary_unsuitable_condition"):
            blocks.append(
                _block(
                    "careerField-caution",
                    "caution",
                    "맞지 않는 업무 조건",
                    f"{condition}에서는 좋은 적성도 충분히 쓰이기 어렵습니다.",
                    ("career",),
                )
            )
        return blocks
    return [_block("careerField-fallback", "summary", title, "직업 분야는 현재 직함보다 업무 안에서 맡는 역할과 책임의 크기로 더 분명하게 갈립니다.", ("career",))]


def _career_special_blocks(
    entry_id: str,
    title: str,
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[ContentBlock]:
    axes = _axes_by_labels(life_feature_summary, ENTRY_AXIS_LABELS.get(entry_id, ()), limit=3)
    primary = _first_dict(life_feature_summary.get("primary_career_fields"))
    caution = _first_dict(life_feature_summary.get("caution_career_fields"))
    item = _best_item_for_domain(items, "career") or _best_item_for_domain(items, "money")
    domains: tuple[Domain, ...] = ("career", "money") if entry_id in {"business_expansion", "independence_business_potential"} else ("career",)
    summary = _career_special_summary(entry_id, axes, primary)
    blocks = [_block(f"{entry_id}-special-summary", "summary", title, summary, domains)]
    if axes:
        blocks.append(
            _block(
                f"{entry_id}-special-basis",
                "basis",
                "선택의 중심",
                _axis_collection_sentence(axes, f"{title}에서는"),
                domains,
            )
        )
    if item:
        blocks.append(
            _block(
                f"{entry_id}-special-action",
                "action",
                "도움 되는 기준",
                _career_special_action(entry_id, item, target_years),
                domains,
            )
        )
    if caution:
        condition = _field_text(caution, "primary_unsuitable_condition", "권한과 책임이 맞지 않는 자리")
        blocks.append(
            _block(
                f"{entry_id}-special-caution",
                "caution",
                "맞지 않는 자리",
                f"{condition}에서는 능력을 써도 인정이 늦어집니다.",
                ("career",),
            )
        )
    return blocks


def _career_special_summary(entry_id: str, axes: list[dict[str, Any]], primary: dict[str, Any] | None) -> str:
    axis_focus = _career_axis_focus(axes, "역할과 책임을 정리하는 힘")
    field_label = _field_text(primary, "label", "현재 강점이 잘 쓰이는 분야")
    if entry_id == "business_expansion":
        return (
            "사업이 커지면 매출과 거래처가 함께 늘어납니다. 비용 문제도 같이 커집니다. 권한 배분도 따로 정해야 합니다. 비용과 권한을 함께 계산할수록 커진 규모가 이익으로 남습니다. "
            f"현재 직업명이 다르더라도 {field_label}처럼 일정을 조정하는 역할에서 사업 감각이 강해집니다."
        )
    if entry_id == "independence_business_potential":
        return (
            f"독립해서 일할 때는 결정 뒤의 비용과 책임을 감당하는 능력이 중요합니다. "
            "비용과 일정이 현실적으로 세워질수록 독립 업무에서 성과를 냅니다. "
            "프리랜스나 작은 사업 운영에서도 같은 강점이 쓰입니다."
        )
    if entry_id == "leadership_potential":
        return (
            f"당신의 리더십은 역할과 책임을 나누고 일의 방향을 설명하는 방식에서 좋습니다. "
            f"{axis_focus}이 강해질 때 여러 사람의 일을 한 방향으로 정리하는 능력이 커집니다."
        )
    if entry_id == "academic_expertise_achievement":
        return (
            "전문성은 지식이 자격, 분석, 교육 자료, 문서 성과로 남을 때 강해집니다. "
            "해낸 일이 결과로 남을 때 전문성도 인정받습니다."
        )
    return f"직업적으로는 {axis_focus}{_subject_particle(axis_focus)} 성과의 방향을 결정합니다."


def _career_axis_focus(axes: list[dict[str, Any]], default: str) -> str:
    labels = [_axis_customer_label(str(axis.get("label") or "")) for axis in axes if axis.get("label")]
    if not labels:
        return default
    return _join_korean(labels[:2])


def _career_special_action(entry_id: str, item: ProductOutputItem, target_years: list[int]) -> str:
    period = _entry_period(entry_id, target_years, item)
    if entry_id == "business_expansion":
        return f"{period}에는 거래를 늘리기 전에 비용 문제가 커집니다. 역할이 따로 정해질 때 확장이 이익으로 남습니다."
    if entry_id == "independence_business_potential":
        return f"{period}에는 독립적인 선택을 하더라도 계약이 문서로 남습니다. 일정도 숫자로 정해집니다. 관리 기준이 서면서 자유로운 일이 이익으로 남습니다."
    if entry_id == "leadership_potential":
        return f"{period}에는 사람을 이끌 때 맡길 일과 직접 책임질 일이 나뉩니다. 역할 배분이 분명해질 때 리더십이 부담이 아니라 성과로 인정됩니다."
    if entry_id == "academic_expertise_achievement":
        return f"{period}에는 지식과 경험이 결과물, 자격, 문서, 교육 성과로 남습니다. 쌓아 둔 전문성이 밖에 남는 형태가 중요합니다."
    return _period_action_sentence(period, item.action)


def _timing_blocks(
    entry_id: str,
    title: str,
    items: list[ProductOutputItem],
    target_years: list[int],
) -> list[ContentBlock]:
    if entry_id in {"annual_caution_timing", "caution_timing", "money_caution_years"}:
        item = _highest_risk_item(items)
        if item:
            point = _timing_point(item)
            return [
                _block(
                    f"{entry_id}-caution",
                    "timing_caution",
                    title,
                    f"{point}에는 {DOMAIN_CAUTION_TIMING_SENTENCES[item.domain]} {item.risk}{_subject_particle(item.risk)} 가장 주의할 부분입니다.",
                    (item.domain,),
                )
            ]
    item = _strongest_items(items, limit=1)[0] if items else None
    if item:
        point = _timing_point(item)
        if entry_id == "long_term_years":
            body = f"당신의 장기 운세에서는 {_age_period(target_years, item)}에 {DOMAIN_NOUNS[item.domain]}운이 중심에 놓입니다. 좋은 시기와 신중해야 할 시기를 나누면 큰 선택의 순서가 정리됩니다."
        elif entry_id == "ten_year_luck":
            body = f"대운에서는 긴 기간에 걸친 역할 변화가 중요합니다. 현재는 {DOMAIN_NOUNS[item.domain]} 문제가 장기간 중요한 기준이 됩니다."
        elif entry_id == "near_years_luck":
            keywords = _keyword_text(item)
            body = f"가까운 시기에서는 {_age_period(target_years, item)}에 {DOMAIN_NOUNS[item.domain]}운이 강합니다. {keywords}{_subject_particle(keywords)} 실제 일정으로 잡힙니다."
        else:
            action_subject = _action_subject(item.action)
            if item.domain == "career":
                if "권한" in action_subject or "결정권" in action_subject:
                    action_sentence = "새 역할에서 결정권을 쥐게 됩니다."
                else:
                    action_sentence = f"{action_subject}{_object_particle(action_subject)} 실제 업무로 맡게 됩니다."
                body = f"{point}에는 직업운에서 인정받을 일이 생깁니다. {action_sentence}"
            elif item.domain == "money":
                body = f"{point}에는 재물운에서 받을 돈이 좋아집니다. {action_subject}{_subject_particle(action_subject)} 수입으로 이어집니다."
            else:
                body = f"{point}에는 {DOMAIN_GOOD_TIMING_SENTENCES[item.domain]} {action_subject}{_subject_particle(action_subject)} 먼저 생깁니다."
        return [_block(f"{entry_id}-timing", "timing", title, body, (item.domain,))]
    return [_block(f"{entry_id}-timing", "timing", title, f"{_entry_period(entry_id, target_years, item)} 전체에서 좋은 시기와 신중한 시기를 구분합니다.")]


def _health_life_blocks(items: list[ProductOutputItem], life_feature_summary: dict[str, Any]) -> list[ContentBlock]:
    axis = _caution_axis(life_feature_summary, ("변화 적응력", "표현 전달력", "가족 책임감"))
    body = "건강운에서는 과로가 먼저 쌓입니다. 생활 관리에서는 수면과 회복 순서를 별도로 잡습니다. 감정 소모도 몸의 피로를 키웁니다."
    if axis:
        body += f" 특히 {axis.get('label')}은 생활 관리에서 별도로 다룹니다."
    return [_block("healthLife-core", "advice", "건강운과 생활 관리", body, tuple(item.domain for item in items[:2]))]


def _life_strength_blocks(items: list[ProductOutputItem], life_feature_summary: dict[str, Any]) -> list[ContentBlock]:
    top_axes = _top_axes(life_feature_summary, limit=3)
    cautions = _caution_axes(life_feature_summary, limit=2)
    blocks = [
        _block(
            "lifeStrength-core",
            "summary",
            "강한 영역",
            _axis_collection_sentence(top_axes, "강한 영역은"),
        )
    ]
    if cautions:
        blocks.append(_block("lifeStrength-caution", "caution", "먼저 관리할 영역", _axis_collection_sentence(cautions, "먼저 관리할 영역은")))
    return blocks


def _premium_core_statements(
    items: list[ProductOutputItem],
    life_feature_summary: dict[str, Any],
    target_years: list[int],
) -> list[str]:
    strongest = _strongest_items(items, limit=2)
    axes = _top_axes(life_feature_summary, limit=2)
    statements: list[str] = []
    if axes:
        first_axis = _axis_customer_label(str(axes[0].get("label") or "가장 강한 장점"))
        statements.append(f"첫째, {first_axis}이 당신의 가장 강한 장점입니다. 중요한 선택에서는 이 장점이 기준이 됩니다.")
    if len(axes) > 1:
        second_axis = _axis_customer_label(str(axes[1].get("label") or "보조 강점"))
        statements.append(f"둘째, {second_axis}은 당신의 선택을 받쳐 주는 보조 강점입니다. 이 장점이 살아나면 주변의 신뢰를 얻습니다. 생활도 안정됩니다.")
    if strongest:
        statements.append(f"셋째, {_age_period(target_years, strongest[0])}에는 {DOMAIN_NOUNS[strongest[0].domain]}이 가장 뚜렷합니다. 이 영역의 일이 먼저 생깁니다.")
    if len(strongest) > 1:
        statements.append(f"넷째, {DOMAIN_NOUNS[strongest[1].domain]}은 두 번째로 중요한 영역입니다. 첫 번째 영역만 보고 결정하면 다른 중요한 사건을 놓칩니다.")
    caution = _highest_risk_item(items)
    if caution:
        statements.append(f"다섯째, {caution.risk}은 신중하게 다루어야 합니다. 이 장면을 초기에 정리하면 좋은 운을 끝까지 살릴 수 있습니다.")
    return statements


def _event_sentence(item: ProductOutputItem) -> str:
    keywords = _keyword_text(item)
    action_subject = _action_subject(item.action)
    period = _period([int(item.period_label)]) if str(item.period_label).isdigit() else f"{item.period_label}년"
    return " ".join(
        (
            _domain_event_opening(item.domain, period, keywords),
            _domain_action_result(item.domain, action_subject),
        )
    )


def _domain_event_opening(domain: Domain, period: str, keywords: str) -> str:
    particle = _subject_particle(keywords)
    if domain == "money":
        return f"{period} 재물운에서는 {keywords}{particle} 첫 재물 사건입니다."
    if domain == "career":
        return f"{period} 직업운은 {keywords}{particle} 출발점입니다. 평가 방식도 달라집니다."
    if domain == "love":
        return f"{period} 연애운에서는 {keywords}{particle} 연락과 만남에서 먼저 보입니다."
    if domain == "marriage":
        return f"{period} 결혼운에서는 {keywords}{particle} 약속과 생활의 중심이 됩니다."
    return f"{period} {DOMAIN_NOUNS.get(domain, '운세')}에서는 {keywords}{particle} 생활에서 먼저 다룰 일이 됩니다."


def _domain_action_result(domain: Domain, action_subject: str) -> str:
    particle = _subject_particle(action_subject)
    if domain == "money":
        return f"{action_subject}{particle} 받을 돈을 분명하게 합니다."
    if domain == "career":
        if "권한" in action_subject or "결정권" in action_subject:
            return "새 역할에서 결정권을 확보하며 직업적 인정을 받습니다. 다음 역할도 맡게 됩니다."
        return f"{action_subject}{_object_particle(action_subject)} 맡아 실력을 인정받습니다. 맡는 일이 더 커집니다."
    if domain == "love":
        return f"{action_subject}{particle} 연락과 만남을 이어 줍니다."
    if domain == "marriage":
        return f"{action_subject}{particle} 결혼 이야기를 생활의 약속으로 옮깁니다."
    return f"{action_subject}{particle} 중요한 결론을 앞당깁니다."


def _axis_collection_sentence(axes: list[dict[str, Any]], lead: str) -> str:
    if not axes:
        return f"{lead} 아직 여러 기준이 함께 정리되는 단계입니다."
    phrases = [_axis_phrase(axis) for axis in axes]
    if "에서는" in lead:
        return " ".join(phrases)
    if lead.endswith("은"):
        return f"{lead[:-1]}을 보면, " + " ".join(phrases)
    if lead.endswith("는"):
        return f"{lead} " + " ".join(phrases)
    return f"{lead} " + " ".join(phrases)


def _axis_phrase(axis: dict[str, Any]) -> str:
    label = str(axis.get("label") or "세부 특성")
    label_text = _axis_customer_label(label, default=label)
    percentile = str(axis.get("percentile_label") or "평균권")
    context = AXIS_CONTEXTS.get(label, f"{label}이 필요한 장면")
    if "하단" in percentile:
        return f"{label_text}은 기준이 먼저 서야 안정되는 영역입니다. {context}에서는 실행 순서와 한계가 분명해질 때 부담이 줄어듭니다."
    if "상위" in percentile:
        high_sentences = {
            "재물 잠재력": "돈이 되는 기회를 고르는 감각이 좋습니다. 수입과 자산의 크기도 커집니다.",
            "수입 확대력": "보수가 커지는 기준을 잘 세웁니다. 받을 보수도 커지기 쉽습니다.",
            "자산 유지력": "벌어들인 돈을 자산으로 남기는 힘이 좋습니다. 손에 남는 돈도 오래 갑니다.",
            "투자와 거래 감각": "투자와 거래의 기준을 잘 읽습니다. 거래 판단도 안정됩니다.",
            "사업 확장력": "외부 거래와 사업 규모를 넓히는 힘이 좋습니다. 남는 이익도 함께 커집니다.",
            "사회적 성공 잠재력": "맡은 역할로 사회적 인정을 받기 쉽습니다. 더 큰 역할도 맡게 됩니다.",
            "직업적 성취력": "맡은 일로 실력을 인정받기 쉽습니다. 평가도 빨라집니다.",
            "책임 감당력": "책임 범위가 넓은 일도 끝까지 정리합니다. 부담보다 성취가 앞섭니다.",
            "평판 유지력": "사회적 신뢰와 평판을 오래 지킵니다. 한 번 얻은 신뢰가 쉽게 흔들리지 않습니다.",
            "명예운": "공식 평가를 받는 자리에서 평판이 강해집니다. 책임 있는 역할도 함께 붙습니다.",
            "리더십 잠재력": "사람과 책임을 나누어 이끄는 힘이 좋습니다. 이끄는 자리에서 신뢰를 얻습니다.",
            "학문·전문성 성취력": "전문성이 자격과 결과물로 남습니다. 준비한 지식이 평가로 이어집니다.",
            "관계 안정성": "가까워진 관계를 안정적으로 유지합니다. 관계가 쉽게 흔들리지 않습니다.",
            "현실 설계력": "돈과 일의 기준을 현실적으로 세웁니다. 중요한 선택 앞에서도 판단이 쉽게 흔들리지 않습니다.",
            "표현 전달력": "생각과 감정을 상대가 알아듣게 전합니다. 상대가 당신의 뜻을 더 정확하게 이해합니다.",
        }
        return f"{label_text}은 {percentile} 수준으로 좋습니다. {high_sentences.get(label, f'{context}에서 강점이 분명하게 살아납니다.')}"
    return f"{label_text}은 {percentile} 수준입니다. {context}에서는 선택의 기준이 먼저 세워질 때 안정됩니다."


def _axis_caution_sentence(axis: dict[str, Any]) -> str:
    label = str(axis.get("label") or "세부 특성")
    label_text = _axis_customer_label(label, default=label)
    context = AXIS_CONTEXTS.get(label, "중요한 선택 장면")
    if label == "변화 적응력":
        return "상황이 바뀌면 판단할 일이 많아집니다. 결정을 오래 미루면 부담이 커집니다. 할 일과 멈출 일을 먼저 나눌 때 안정됩니다."
    return f"{label_text}은 결정이 늦어질 때 부담으로 바뀌기 쉬운 영역입니다. {context}에서는 할 일과 멈출 일이 먼저 갈라집니다."


def _entry_axis_caution_sentence(entry_id: str, axis: dict[str, Any]) -> str:
    specific = ENTRY_CAUTION_SENTENCES.get(entry_id)
    if specific:
        return specific
    return _axis_caution_sentence(axis)


def _axis_pair_phrase(axes: list[dict[str, Any]]) -> str:
    labels = [_axis_customer_label(str(axis.get("label") or "")) for axis in axes if axis.get("label")]
    if not labels:
        return "현실 판단과 책임감"
    if len(labels) == 1:
        return labels[0]
    particle = "과" if _has_final_consonant(labels[0]) else "와"
    return f"{labels[0]}{particle} {labels[1]}"


def _join_korean(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        particle = "과" if _has_final_consonant(cleaned[0]) else "와"
        return f"{cleaned[0]}{particle} {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", {cleaned[-1]}"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _keyword_text(item: ProductOutputItem) -> str:
    return _clean_keyword(item.event_keywords[0]) if item.event_keywords else DOMAIN_NOUNS[item.domain]


def _clean_keyword(keyword: object) -> str:
    text = _compact(str(keyword))
    replacements = {
        "재대화": "다시 대화",
        "금전 전환": "금전 보상",
        "성과의 금전 전환": "해낸 일의 금전 보상",
        "성과의 금전 보상": "해낸 일의 금전 보상",
        "역할 확대": "업무 범위가 넓어지는 일",
        "직무 전환": "직무 변화",
        "호감 형성": "호감 형성",
        "생활 합의": "생활 방식",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _subject_particle(text: str) -> str:
    return "이" if _has_final_consonant(text) else "가"


def _topic_particle(text: str) -> str:
    return "은" if _has_final_consonant(text) else "는"


def _object_particle(text: str) -> str:
    return "을" if _has_final_consonant(text) else "를"


def _direction_particle(text: str) -> str:
    final = _final_consonant_index(text)
    if final == 0 or final == 8:
        return "로"
    return "으로"


def _has_final_consonant(text: str) -> bool:
    return _final_consonant_index(text) != 0


def _final_consonant_index(text: str) -> int:
    for char in reversed(text.strip()):
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28
        if char.isalnum():
            return 0
    return 0


def _best_item_for_domain(items: list[ProductOutputItem], domain: Domain) -> ProductOutputItem | None:
    domain_items = [item for item in items if item.domain == domain]
    if not domain_items:
        return None
    return max(domain_items, key=_item_rank)


def _strongest_items(items: list[ProductOutputItem], limit: int) -> list[ProductOutputItem]:
    return sorted(items, key=_item_rank, reverse=True)[:limit]


def _highest_risk_item(items: list[ProductOutputItem]) -> ProductOutputItem | None:
    if not items:
        return None
    return max(items, key=lambda item: (item.risk_score, item.event_probability_score))


def _item_rank(item: ProductOutputItem) -> int:
    return item.event_probability_score * 2 + item.opportunity_score + item.change_score - item.risk_score // 2


def _timing_point(item: ProductOutputItem) -> str:
    if not item.timing_windows:
        return f"{item.period_label}년"
    first = item.timing_windows[0]
    start = str(first.get("start_datetime") or "")[:10]
    end = str(first.get("end_datetime") or "")[:10]
    if start and end:
        return f"{start}부터 {end}까지"
    return f"{item.period_label}년"


def _period(target_years: list[int]) -> str:
    years = sorted(set(target_years))
    if not years:
        return "이번 시기"
    if len(years) == 1:
        if years[0] == CURRENT_FORTUNE_YEAR:
            return f"{CURRENT_FORTUNE_YEAR}년 {CURRENT_FORTUNE_YEAR_PILLAR}년"
        return f"{years[0]}년"
    if years == list(range(years[0], years[-1] + 1)):
        return f"{years[0]}~{years[-1]}년"
    return ", ".join(f"{year}년" for year in years)


def _birth_year_from_item(item: ProductOutputItem | None) -> int | None:
    if not item:
        return None
    birth_year = item.template_slots.get("birth_year")
    return birth_year if isinstance(birth_year, int) else None


def _korean_age(year: int, birth_year: int) -> int:
    return year - birth_year + 1


def _age_period(target_years: list[int], item: ProductOutputItem | None) -> str:
    birth_year = _birth_year_from_item(item)
    years = sorted(set(target_years))
    if not birth_year or not years:
        return "인생 전반"
    ages = [_korean_age(year, birth_year) for year in years]
    if len(ages) == 1:
        return f"한국 나이 {ages[0]}세 전후"
    if ages == list(range(ages[0], ages[-1] + 1)):
        return f"한국 나이 {ages[0]}~{ages[-1]}세"
    return "한국 나이 " + ", ".join(f"{age}세" for age in ages)


def _entry_period(entry_id: str, target_years: list[int], item: ProductOutputItem | None) -> str:
    if entry_id in ANNUAL_ENTRY_IDS:
        return _period([CURRENT_FORTUNE_YEAR])
    if entry_id in YEAR_EXPLICIT_ENTRY_IDS:
        return _period(target_years)
    return _age_period(target_years, item)


def _natal_reality_catalog_sentence(life_feature_summary: dict[str, Any]) -> str:
    season_sentence = _season_catalog_sentence(life_feature_summary)
    month_signal = _position_signal(life_feature_summary, "month")
    day_signal = _position_signal(life_feature_summary, "day")
    sentences = [season_sentence] if season_sentence else []
    if month_signal:
        label = _position_branch_label(month_signal)
        if label:
            branch_key = str(month_signal.get("branch") or month_signal.get("branch_label") or "")
            texture = branch_position_texture(branch_key, "month")
            body = f"{label}에서는 직업 수입과 사회적 평가가 먼저 바뀝니다. 받을 돈과 지출 한도도 함께 정리됩니다."
            if texture:
                body += f" {texture}"
            body += " 이 영향으로 돈 문제와 일의 기준에 민감해집니다."
            sentences.append(body)
    if day_signal:
        label = _position_branch_label(day_signal)
        if label:
            branch_key = str(day_signal.get("branch") or day_signal.get("branch_label") or "")
            texture = branch_position_texture(branch_key, "day")
            body = f"{label}에서는 가까운 관계에서 마음을 쓰는 방식이 잘 보입니다."
            if texture:
                body += f" {texture}"
            body += " 그래서 연애와 결혼도 감정만으로 정리되지 않습니다."
            sentences.append(body)
    hidden_sentence = _hidden_protrusion_catalog_sentence(month_signal or day_signal)
    if hidden_sentence:
        sentences.append(hidden_sentence)
    return _compact(" ".join(sentence for sentence in sentences if sentence))


def _domain_reality_catalog_sentence(domain: Domain, life_feature_summary: dict[str, Any]) -> str:
    signal = _domain_position_signal(domain, life_feature_summary)
    sentences: list[str] = []
    if signal:
        label = _position_branch_label(signal)
        position = str(signal.get("position") or "")
        branch_key = str(signal.get("branch") or signal.get("branch_label") or "")
        scene = DOMAIN_REALITY_CATALOG_SCENES.get(domain, {}).get(position, DOMAIN_SCENES[domain])
        if label:
            opening = DOMAIN_REALITY_CATALOG_OPENINGS.get(domain, {}).get(position)
            if opening:
                sentences.append(opening.format(label=label, scene=scene))
            else:
                sentences.append(f"{label}를 통해 {DOMAIN_NOUNS[domain]}운의 {scene} 문제가 먼저 보입니다.")
        texture = branch_domain_texture(branch_key, domain)
        if texture:
            sentences.append(texture)
        hidden_sentence = _hidden_protrusion_catalog_sentence(signal, domain)
        if hidden_sentence:
            sentences.append(hidden_sentence)
    result = DOMAIN_REALITY_CATALOG_RESULTS.get(domain, "")
    if result:
        sentences.append(result)
    return _compact(" ".join(sentence for sentence in sentences if sentence))


def _season_catalog_sentence(life_feature_summary: dict[str, Any], domain: Domain | None = None) -> str:
    season = life_feature_summary.get("season_context")
    if not isinstance(season, dict):
        return ""
    month_branch = _compact(str(season.get("month_branch_label") or ""))
    season_label = _compact(str(season.get("season_label") or ""))
    month_element = _compact(str(season.get("month_element_label") or ""))
    useful_labels = season.get("useful_element_labels")
    useful_text = ""
    if isinstance(useful_labels, list):
        useful_text = _join_korean([str(label) for label in useful_labels[:2] if str(label)])
    if not month_branch and not season_label:
        return ""
    base = f"당신의 사주는 {season_label} {month_branch}월의 기운을 바탕으로 합니다.".replace("  ", " ").strip()
    if domain:
        scene = {
            "money": "돈을 남기는 기준",
            "career": "일을 맡고 평가받는 기준",
            "love": "마음을 열고 거리를 맞추는 방식",
            "marriage": "생활비와 책임을 나누는 방식",
        }[domain]
        if month_element:
            base += f" {month_element} 기운이 {scene}에 먼저 닿습니다."
        else:
            base += f" 이 월령이 {scene}에 먼저 닿습니다."
        texture = branch_domain_texture(month_branch, domain)
        if texture:
            base += f" {texture}"
    elif month_element:
        base += f" {month_element} 기운이 강해 생활 전반의 판단과 반응이 예민해집니다."
    if useful_text:
        base += f" 삶이 안정될 때는 {useful_text} 기운이 함께 받쳐 줍니다."
    return _compact(base)


def _domain_position_signal(domain: Domain, life_feature_summary: dict[str, Any]) -> dict[str, Any] | None:
    branch_context = life_feature_summary.get("branch_reality_context")
    if not isinstance(branch_context, dict):
        return None
    signals = branch_context.get("position_signals")
    if not isinstance(signals, list):
        return None
    typed = [signal for signal in signals if isinstance(signal, dict)]
    priorities = DOMAIN_BRANCH_POSITION_PRIORITY.get(domain, ())
    for position in priorities:
        for signal in typed:
            domains = signal.get("domains")
            if signal.get("position") == position and (not isinstance(domains, list) or domain in domains):
                return signal
    for position in priorities:
        match = next((signal for signal in typed if signal.get("position") == position), None)
        if match:
            return match
    return typed[0] if typed else None


def _position_signal(life_feature_summary: dict[str, Any], position: str) -> dict[str, Any] | None:
    branch_context = life_feature_summary.get("branch_reality_context")
    if not isinstance(branch_context, dict):
        return None
    signals = branch_context.get("position_signals")
    if not isinstance(signals, list):
        return None
    return next(
        (signal for signal in signals if isinstance(signal, dict) and signal.get("position") == position),
        None,
    )


def _position_branch_label(signal: dict[str, Any]) -> str:
    position_label = _compact(str(signal.get("position_label") or ""))
    branch_label = _compact(str(signal.get("branch_label") or ""))
    if position_label and branch_label:
        return f"{position_label} {branch_label}"
    return position_label or branch_label


PROTRUDED_HIDDEN_CATALOG_SENTENCES: dict[Domain, str] = {
    "money": "{stem_text} 성향 때문에 돈 문제를 말로 빨리 정리합니다. 받을 금액과 지출 한도도 빨리 가릅니다.",
    "career": "{stem_text} 성향 때문에 업무 범위를 말과 행동으로 바로 정합니다. 맡을 범위도 오래 미루지 않습니다.",
    "love": "{stem_text} 성향은 속마음이 말투와 태도에 묻어납니다. 마음을 숨겨도 결정 앞에서는 태도가 먼저 나옵니다.",
    "marriage": "{stem_text} 성향은 생활 방식을 말로 꺼내게 합니다. 결혼을 생각할수록 돈과 책임 문제를 미루기 어렵습니다.",
}


def _hidden_protrusion_catalog_sentence(signal: dict[str, Any] | None, domain: Domain | None = None) -> str:
    if not signal:
        return ""
    stems = signal.get("protruded_hidden_stems")
    if not isinstance(stems, list) or not stems:
        return ""
    labels = [_stem_label(str(stem)) for stem in stems[:2] if str(stem)]
    if not labels:
        return ""
    stem_text = _join_korean(labels)
    if domain in PROTRUDED_HIDDEN_CATALOG_SENTENCES:
        return PROTRUDED_HIDDEN_CATALOG_SENTENCES[domain].format(stem_text=stem_text)
    return (
        f"{stem_text} 성향이 말과 행동으로 빨리 나옵니다. "
        "속으로 두던 판단도 중요한 순간에는 바로 선택으로 옮깁니다."
    )


def _stem_label(stem: str) -> str:
    return STEM_HANJA.get(stem, stem)


def _top_axes(life_feature_summary: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    return [axis for axis in life_feature_summary.get("top_axes", []) if isinstance(axis, dict)][:limit]


def _caution_axes(life_feature_summary: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    return [axis for axis in life_feature_summary.get("caution_axes", []) if isinstance(axis, dict)][:limit]


def _axes_by_labels(
    life_feature_summary: dict[str, Any],
    labels: tuple[str, ...],
    limit: int,
) -> list[dict[str, Any]]:
    if not labels:
        return []
    axes = [
        axis
        for axis in list(life_feature_summary.get("top_axes", []))
        if isinstance(axis, dict) and axis.get("label") in labels
    ]
    ordered: list[dict[str, Any]] = []
    for label in labels:
        match = next((axis for axis in axes if axis.get("label") == label), None)
        if match and match not in ordered:
            ordered.append(match)
        if len(ordered) >= limit:
            break
    return ordered


def _caution_axis(life_feature_summary: dict[str, Any], labels: tuple[str, ...]) -> dict[str, Any] | None:
    caution_axes = _caution_axes(life_feature_summary, 10)
    if labels:
        for label in labels:
            match = next((axis for axis in caution_axes if axis.get("label") == label), None)
            if match:
                return match
        return None
    return caution_axes[0] if caution_axes else None


def _axis_short_clause(axis: dict[str, Any] | None, default: str) -> str:
    if not axis:
        return _axis_customer_label(default, default=default)
    label = str(axis.get("label") or default)
    percentile = str(axis.get("percentile_label") or "")
    label_text = _axis_customer_label(label, default=label)
    if "상위" in percentile:
        return label_text
    if "하단" in percentile:
        return f"{label_text}의 기준"
    if percentile:
        return label_text
    return label_text


def _field_text(field: dict[str, Any] | None, key: str, fallback: str) -> str:
    if not field:
        return fallback
    value = field.get(key)
    text = _compact(str(value or ""))
    if key == "label" and text.count("·") >= 2:
        parts = [part.strip() for part in text.split("·") if part.strip()]
        if len(parts) >= 2:
            particle = "과" if _has_final_consonant(parts[0]) else "와"
            text = f"{parts[0]}{particle} {parts[-1]}"
    return text if text else fallback


def _first_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return None


def _compact(text: str) -> str:
    return " ".join(str(text).replace("\n", " ").split())
