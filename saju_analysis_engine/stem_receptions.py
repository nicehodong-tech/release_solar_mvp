"""Day-stem reception and integrated saju signal rules.

The calculation unit here is not "water direct wealth" or another broad
category. It is "a specific day stem receives a specific target stem, and that
target stem performs a specific ten-god role".
"""

from __future__ import annotations

from itertools import permutations
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    MONTH_SEASON_MODIFIERS,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
)
from .directional_interactions import _direction_type
from .models import (
    BranchInteraction,
    IntegratedSajuProfile,
    IntegratedSajuSignal,
    PositionSignal,
    StemReceptionProfile,
    StemReceptionSignal,
)
from .refined_interpretation_values import (
    REFINED_SPECIFIC_RECEPTION_OVERRIDES,
    REFINED_STEM_DOMAIN_SCENES,
    REFINED_STEM_PROFILES,
    REFINED_TEN_GOD_DOMAIN_LENSES,
    REFINED_TEN_GOD_RECEPTION_RULES,
)
from .ten_god_interactions import TEN_GOD_LABELS, ten_god_direction_rule
from .ten_gods import main_hidden_stem, ten_god_for


POSITION_ORDER = ("year", "month", "day", "hour")
STEM_ORDER = ("gap", "eul", "byeong", "jeong", "mu", "gi", "gyeong", "sin", "im", "gye")
SERVICE_DOMAINS = ("money", "career", "love", "marriage")
ALL_PROJECTION_DOMAINS = ("money", "career", "love", "marriage", "personality")

BRANCH_RELATION_SCORE_MODIFIERS = {
    "six_combine": 0.10,
    "three_harmony": 0.10,
    "three_harmony_half": 0.10,
    "clash": 0.15,
    "punishment": 0.12,
    "self_punishment": 0.12,
    "break": 0.10,
    "harm": 0.10,
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

STEM_SUBJECT_PARTICLES = {
    "gap": "이",
    "eul": "이",
    "byeong": "이",
    "jeong": "이",
    "mu": "가",
    "gi": "가",
    "gyeong": "이",
    "sin": "이",
    "im": "이",
    "gye": "가",
}

STEM_OBJECT_PARTICLES = {
    "gap": "을",
    "eul": "을",
    "byeong": "을",
    "jeong": "을",
    "mu": "를",
    "gi": "를",
    "gyeong": "을",
    "sin": "을",
    "im": "을",
    "gye": "를",
}

STEM_WITH_PARTICLES = {
    "gap": "과",
    "eul": "과",
    "byeong": "과",
    "jeong": "과",
    "mu": "와",
    "gi": "와",
    "gyeong": "과",
    "sin": "과",
    "im": "과",
    "gye": "와",
}

TEN_GOD_AS_PARTICLES = {
    "bi_gyeon": "으로",
    "geob_jae": "로",
    "sik_sin": "으로",
    "sang_gwan": "으로",
    "pyeon_jae": "로",
    "jeong_jae": "로",
    "pyeon_gwan": "으로",
    "jeong_gwan": "으로",
    "pyeon_in": "으로",
    "jeong_in": "으로",
}

TEN_GOD_CAREER_FIT_CONTEXTS = {
    "bi_gyeon": "협업 기준과 책임 배분이 분명한 자리",
    "geob_jae": "경쟁 규칙과 보상 기준이 공개된 자리",
    "sik_sin": "실무 절차와 결과물이 눈에 보이는 자리",
    "sang_gwan": "개선 권한과 표현 범위가 허용되는 자리",
    "pyeon_jae": "외부 접점과 성과 보상이 연결된 자리",
    "jeong_jae": "계약 기준이 안정된 자리",
    "pyeon_gwan": "위기 대응 권한과 지휘 체계가 분명한 자리",
    "jeong_gwan": "직책, 규칙, 평가 기준이 분명한 자리",
    "pyeon_in": "탐색, 분석, 검증 시간이 허용되는 자리",
    "jeong_in": "문서, 학습, 보호 체계가 갖추어진 자리",
}

TEN_GOD_CAREER_MISFIT_CONTEXTS = {
    "bi_gyeon": "책임은 나누지 않으면서 비교만 강한 환경",
    "geob_jae": "규칙 없이 경쟁만 요구하는 환경",
    "sik_sin": "수고는 많지만 결과와 보상이 확인되지 않는 환경",
    "sang_gwan": "문제 제기를 금지하고 복종만 요구하는 환경",
    "pyeon_jae": "외부 접점 없이 내부 조정만 반복되는 환경",
    "jeong_jae": "계약과 보상 기준이 자주 바뀌는 환경",
    "pyeon_gwan": "권한 없이 부담만 무거운 환경",
    "jeong_gwan": "평가 기준은 엄격하지만 책임 범위가 흐린 환경",
    "pyeon_in": "근거 확인 없이 추측만 요구하는 환경",
    "jeong_in": "문서와 기준 없이 책임만 요구하는 환경",
}


def _stem_subject(stem: str) -> str:
    return f"{STEM_LABELS[stem]}{STEM_SUBJECT_PARTICLES[stem]}"


def _stem_object(stem: str) -> str:
    return f"{STEM_LABELS[stem]}{STEM_OBJECT_PARTICLES[stem]}"


def _stem_with(stem: str) -> str:
    return f"{STEM_LABELS[stem]}{STEM_WITH_PARTICLES[stem]}"


def _ten_god_as(ten_god: str) -> str:
    return f"{TEN_GOD_LABELS[ten_god]}{TEN_GOD_AS_PARTICLES[ten_god]}"


def _has_final_consonant(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    code = ord(stripped[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _subject_particle_text(text: str) -> str:
    return "이" if _has_final_consonant(text) else "가"


def _object_particle_text(text: str) -> str:
    return "을" if _has_final_consonant(text) else "를"


def _topic_particle_text(text: str) -> str:
    return "은" if _has_final_consonant(text) else "는"


def _keyword_pair_text(values: list[str]) -> str:
    keywords = [str(value) for value in values if str(value).strip()]
    if not keywords:
        return ""
    if len(keywords) == 1:
        return keywords[0]
    particle = "과" if _has_final_consonant(keywords[0]) else "와"
    return f"{keywords[0]}{particle} {keywords[1]}"


def _career_fit_context(ten_god: str) -> str:
    return TEN_GOD_CAREER_FIT_CONTEXTS[ten_god]


def _career_misfit_context(ten_god: str) -> str:
    return TEN_GOD_CAREER_MISFIT_CONTEXTS[ten_god]


def _stem_profile(
    mode: str,
    object_nature: str,
    keywords: list[str],
    fitting: list[str],
    misfitting: list[str],
) -> dict[str, Any]:
    return {
        "mode": mode,
        "object_nature": object_nature,
        "keywords": keywords,
        "fitting": fitting,
        "misfitting": misfitting,
    }


STEM_PROFILES: dict[str, dict[str, Any]] = {
    "gap": _stem_profile(
        "큰 방향을 세우고 먼저 기준을 만들려는 성향",
        "굵은 기준, 시작점, 성장의 큰 축",
        ["시작", "기준", "성장축"],
        ["명확한 목표", "상위 계획", "장기 책임"],
        ["세부 조율만 반복되는 자리", "결정권 없는 보조 역할"],
    ),
    "eul": _stem_profile(
        "관계와 상황을 세밀하게 엮으며 살아남는 성향",
        "관계 조율, 세부 책임, 유연한 연결",
        ["조율", "관계", "세부 책임"],
        ["협의", "상담", "섬세한 관리"],
        ["거친 명령 체계", "빠른 단절이 반복되는 환경"],
    ),
    "byeong": _stem_profile(
        "보이게 만들고 설명하며 시야를 넓히는 성향",
        "공개성, 시야, 설명력, 명분화",
        ["공개성", "시야", "설명"],
        ["발표", "교육", "브랜딩", "공개 평가"],
        ["불투명한 업무", "성과가 보이지 않는 자리"],
    ),
    "jeong": _stem_profile(
        "한 지점에 집중해 기술과 이해를 정교하게 다듬는 성향",
        "세밀한 기술, 검토, 집중력, 개선",
        ["기술", "검토", "집중"],
        ["연구", "개발", "품질 개선", "정밀 실무"],
        ["방향 없는 확장", "깊이 없는 반복 영업"],
    ),
    "mu": _stem_profile(
        "넓은 기반을 지키고 전체 조건을 받아내는 성향",
        "공간, 기반, 큰 책임, 보유 자원",
        ["기반", "공간", "책임"],
        ["관리 책임", "장기 보유", "조직 운영"],
        ["계속 흔들리는 역할", "권한 없는 과중 책임"],
    ),
    "gi": _stem_profile(
        "생활에 닿은 조건을 조정하고 실제 문제를 처리하는 성향",
        "생활 기반, 세부 관리, 적응, 돌봄",
        ["생활", "관리", "적응"],
        ["실무 조정", "고객 관리", "운영 관리"],
        ["추상적 구호만 있는 일", "현장 정보 없는 기획"],
    ),
    "gyeong": _stem_profile(
        "기준을 세우고 자르며 결과를 집행하려는 성향",
        "규칙, 집행, 결과물, 절단과 선별",
        ["집행", "규칙", "결과"],
        ["법무", "감사", "공정 관리", "집행 권한"],
        ["끝없는 타협", "기준 없는 정서 노동"],
    ),
    "sin": _stem_profile(
        "완성도와 품질을 세밀하게 가려내려는 성향",
        "품질, 선별, 정교한 결과, 가치 선별",
        ["품질", "선별", "완성도"],
        ["디자인", "심사", "검수", "브랜드 품질"],
        ["대충 처리해야 하는 자리", "완성 기준 없는 업무"],
    ),
    "im": _stem_profile(
        "큰 정보와 외부 변수를 넓게 다루는 성향",
        "시장 정보, 대외 자금, 이동성, 큰 거래",
        ["시장", "대외 정보", "큰 거래"],
        ["투자 검토", "해외·외부 거래", "대규모 네트워크"],
        ["좁은 반복 업무", "외부 접점이 막힌 자리"],
    ),
    "gye": _stem_profile(
        "세부 정보와 감각을 모아 조용히 가늠하는 성향",
        "현금성, 계약 세부, 감정 정보, 정밀한 기록",
        ["현금성", "계약", "기록"],
        ["회계", "계약 관리", "상담 기록", "데이터 정리"],
        ["큰소리로 밀어붙이는 일", "세부 확인 없이 진행하는 일"],
    ),
}


def _role_rule(
    core: str,
    felt: str,
    behavior: str,
    domain_links: list[str],
    fitting: dict[str, list[str]],
    misfitting: dict[str, list[str]],
    fatigue: dict[str, list[str]],
    domain_notes: dict[str, str],
) -> dict[str, Any]:
    return {
        "core": core,
        "felt": felt,
        "behavior": behavior,
        "domain_links": list(dict.fromkeys(domain_links + ["personality"])),
        "fitting": fitting,
        "misfitting": misfitting,
        "fatigue": fatigue,
        "domain_notes": domain_notes,
    }


def _conditions(
    money: list[str],
    career: list[str],
    love: list[str],
    marriage: list[str],
    personality: list[str],
) -> dict[str, list[str]]:
    return {
        "money": money,
        "career": career,
        "love": love,
        "marriage": marriage,
        "personality": personality,
    }


TEN_GOD_RECEPTION_RULES: dict[str, dict[str, Any]] = {
    "bi_gyeon": _role_rule(
        "같은 처지의 사람, 내 편, 공동 책임을 의식하게 하는 역할",
        "혼자 결정하기보다 함께 확인해야 마음이 놓입니다.",
        "나와 비슷한 사람과 비교하고 협의하며 움직입니다.",
        ["money", "career", "love", "marriage"],
        _conditions(["공동 관리", "가족·동료와의 장기 자산"], ["팀 단위 업무", "공동 책임"], ["친구 같은 관계"], ["생활을 함께 나누는 결혼"], ["동등성", "의리"]),
        _conditions(["지분이 불명확한 동업"], ["책임 소재가 모호한 팀"], ["상대가 늘 같아야 한다고 요구하는 관계"], ["역할 분담 없는 공동 생활"], ["차이를 인정하지 않는 태도"]),
        _conditions(["분배 갈등"], ["간섭과 책임 전가"], ["배신감"], ["가사·생활 부담의 불균형"], ["비교 피로"]),
        {
            "money": "돈이 개인 단독 성과보다 공동 책임과 분배 문제를 함께 동반합니다.",
            "career": "직업에서는 동료와 같은 선에 서는 구조가 중요합니다.",
            "love": "관계에서는 친구 같은 동질감이 안정 요인이 됩니다.",
            "marriage": "결혼에서는 생활을 함께 나누는 감각이 강합니다.",
            "personality": "성향은 내 사람을 중요하게 여기고 동등성을 민감하게 봅니다.",
        },
    ),
    "geob_jae": _role_rule(
        "서로 다른 이해관계, 경쟁자, 대중을 의식하게 하는 역할",
        "상대가 나와 다르다는 사실을 빨리 느낍니다.",
        "상대와 내 몫을 비교합니다. 손해가 보이면 바로 조정하려 합니다.",
        ["money", "career"],
        _conditions(["경쟁 시장", "성과 보상", "협상"], ["영업", "대중 상대", "이해관계 조정"], ["서로의 차이를 인정하는 관계"], ["경제 기준이 분명한 결혼"], ["현실 감각", "대중 이해"]),
        _conditions(["구두 약속만 있는 거래"], ["규칙 없는 경쟁 조직"], ["상대가 희생만 요구하는 관계"], ["돈과 역할을 말하지 않는 결혼"], ["일방적으로 양보하는 태도"]),
        _conditions(["탈취감", "불신", "급한 지출"], ["소모적 경쟁"], ["정서적 거리감"], ["금전 갈등"], ["경계심 과다"]),
        {
            "money": "돈은 경쟁과 협상 안에서 생기며, 계약과 확인 절차가 중요합니다.",
            "career": "직업에서는 사람의 욕구를 읽고 배치하는 능력이 커집니다.",
            "love": "관계에서는 서로 다른 욕구를 인정해야 안정됩니다.",
            "marriage": "결혼에서는 경제 기준과 역할 기준을 분명히 해야 합니다.",
            "personality": "성향은 비교 감각과 실속 감각이 빠릅니다.",
        },
    ),
    "sik_sin": _role_rule(
        "내가 직접 해온 일, 생활력, 반복 실행을 중요하게 여기는 역할",
        "내 손으로 처리해야 마음이 놓입니다.",
        "시간을 들여 능력을 쌓고 실제 행동으로 증명합니다.",
        ["money", "career", "marriage"],
        _conditions(["기술 수입", "장기 고객", "반복 가능한 소득"], ["실무", "제조", "현장 전문성", "꾸준한 작업"], ["챙겨주는 관계"], ["생활 책임이 분명한 결혼"], ["성실성", "몸으로 익힌 능력"]),
        _conditions(["몸만 쓰고 보상이 약한 일"], ["계속 부려지는 자리"], ["돌봄만 맡는 관계"], ["한쪽만 생활을 책임지는 결혼"], ["쉬지 못하는 태도"]),
        _conditions(["과로", "낮은 보상"], ["업무 누적"], ["돌봄 피로"], ["생활 소모"], ["탈진"]),
        {
            "money": "돈은 직접 수행한 능력과 반복된 노동에서 만들어집니다.",
            "career": "직업에서는 실무를 쌓아 신뢰를 얻는 방식이 강합니다.",
            "love": "관계에서는 말보다 챙김과 행동으로 마음을 보입니다.",
            "marriage": "결혼에서는 생활 책임과 꾸준함이 중심이 됩니다.",
            "personality": "성향은 자기 몫을 해내야 안정되는 쪽입니다.",
        },
    ),
    "sang_gwan": _role_rule(
        "주변을 분석하고 쓸 만한 방법을 고르는 표현 역할",
        "답답한 구조나 설명되지 않는 규칙을 그냥 넘기기 어렵습니다.",
        "관찰, 비판, 설득, 개선으로 상황을 바꾸려 합니다.",
        ["money", "career", "love"],
        _conditions(["마케팅", "판매 기획", "시장 조사"], ["기획", "홍보", "감사", "개선 업무"], ["말이 잘 통하는 관계"], ["대화 규칙을 정하는 결혼"], ["분석력", "표현력"]),
        _conditions(["말할 권한이 없는 자리"], ["일방적인 복종만 요구하는 조직"], ["감정만 앞세우는 관계"], ["비판을 금지하는 결혼"], ["비판 과다"]),
        _conditions(["구설", "저작권·출처 문제"], ["권위 충돌"], ["말로 인한 상처"], ["규칙 갈등"], ["피로한 예민함"]),
        {
            "money": "돈은 시장 요구를 읽고 설득하는 과정에서 생깁니다.",
            "career": "직업에서는 문제를 드러내고 개선안을 만드는 힘이 큽니다.",
            "love": "관계에서는 대화와 설명이 핵심이 됩니다.",
            "marriage": "결혼에서는 불만을 쌓지 말고 규칙을 조정해야 합니다.",
            "personality": "성향은 비판적이고 빠르게 방법을 찾습니다.",
        },
    ),
    "pyeon_jae": _role_rule(
        "외부 기회, 거래, 확장 가능성을 넓게 살피게 하는 역할",
        "바깥에서 생기는 기회와 사람의 반응을 빨리 봅니다.",
        "교류하고 설득하며 큰 가능성을 시험합니다.",
        ["money", "career", "love"],
        _conditions(["대외 거래", "영업", "투자 검토"], ["사업 개발", "제휴", "외부 프로젝트"], ["사교적 만남"], ["경제 확장성이 있는 결혼"], ["개방성", "기회 포착"]),
        _conditions(["세부 관리만 반복하는 일"], ["외부 접점 없는 자리"], ["깊이 없이 넓기만 한 관계"], ["책임보다 확장만 앞서는 결혼"], ["무리한 낙관"]),
        _conditions(["손실 확대", "책임 증가"], ["성과 압박"], ["관계의 얕음"], ["경제 부담"], ["불안정감"]),
        {
            "money": "돈은 외부 기회, 거래, 사람과의 교류에서 커집니다.",
            "career": "직업에서는 제휴와 확장 역할이 중요합니다.",
            "love": "관계에서는 매력과 접촉 범위가 넓어집니다.",
            "marriage": "결혼에서는 경제 목표와 대외 활동을 조정해야 합니다.",
            "personality": "성향은 기회의 크기를 먼저 보고 움직이는 편입니다.",
        },
    ),
    "jeong_jae": _role_rule(
        "내 것과 남의 것, 역할과 책임 범위를 나누는 관리 역할",
        "범위와 약속이 분명해야 안정됩니다.",
        "소유, 비용, 시간, 역할을 정리하며 움직입니다.",
        ["money", "career", "marriage"],
        _conditions(["계약 수입", "회계", "자산 관리"], ["관리", "운영", "총무", "실무 조정"], ["현실 기준이 분명한 관계"], ["생활비와 역할이 정리된 결혼"], ["책임감", "현실성"]),
        _conditions(["경계 없는 돈거래"], ["권한 없이 책임만 큰 자리"], ["기준 없이 맞춰야 하는 관계"], ["돈 이야기를 피하는 결혼"], ["자기 한계 고정"]),
        _conditions(["돈이 묶임", "작은 손실의 누적"], ["번아웃"], ["거리감"], ["생활 부담"], ["변화 회피"]),
        {
            "money": "돈은 계약, 정산, 관리, 예측 가능한 수입에서 안정성이 높습니다.",
            "career": "직업에서는 운영과 책임 범위가 분명할 때 실력을 안정적으로 인정받습니다.",
            "love": "관계에서는 감정보다 현실 조건을 확인하려 합니다.",
            "marriage": "결혼에서는 생활비와 역할 분담이 안정의 기준입니다.",
            "personality": "성향은 안정과 경계 설정을 중시합니다.",
        },
    ),
    "pyeon_gwan": _role_rule(
        "갑작스러운 임무, 압박, 위험, 강한 책임을 처리하게 하는 역할",
        "내 의지와 무관하게 처리해야 할 일이 생겼다고 느낍니다.",
        "결단하고 버티며 위기 속에서 역할을 수행합니다.",
        ["career", "marriage"],
        _conditions(["위기 대응 보상", "책임 수당"], ["위기 관리", "감사", "보안", "응급 대응"], ["강한 책임을 이해하는 관계"], ["어려운 일을 함께 버티는 결혼"], ["결단력", "긴장 속 집중"]),
        _conditions(["책임만 있고 보호 없는 자리"], ["무리한 상명하복"], ["압박이 사랑으로 착각되는 관계"], ["희생만 반복되는 결혼"], ["긴장 중독"]),
        _conditions(["과중 책임", "법적·조직 리스크"], ["소모와 불면"], ["통제 갈등"], ["가족 부담"], ["예민함"]),
        {
            "money": "돈은 위험과 책임을 감수한 대가로 붙기 쉽습니다.",
            "career": "직업에서는 위기 대응과 강한 책임 수행이 핵심입니다.",
            "love": "관계에서는 압박과 보호를 구분해야 합니다.",
            "marriage": "결혼에서는 한쪽에게 모든 부담이 몰리지 않게 해야 합니다.",
            "personality": "성향은 강한 상황에서 결단력이 커집니다.",
        },
    ),
    "jeong_gwan": _role_rule(
        "사회가 인정하는 규칙, 평판, 직위, 공적 책임을 의식하게 하는 역할",
        "정당한 기준 안에서 인정받아야 안정됩니다.",
        "규칙을 지키려 합니다. 맡은 역할을 끝까지 해내며 평판을 지킵니다.",
        ["career", "marriage"],
        _conditions(["직책 보상", "공식 급여", "장기 계약"], ["공직", "제도권 조직", "관리 책임"], ["예의와 약속이 있는 관계"], ["책임과 신뢰가 있는 결혼"], ["원칙", "신뢰"]),
        _conditions(["규칙을 무시하는 거래"], ["평판 관리가 어려운 조직"], ["약속이 가벼운 관계"], ["책임을 회피하는 결혼"], ["과도한 체면"]),
        _conditions(["평판 손상"], ["상급자 압박"], ["긴장감"], ["의무감 과다"], ["자유 부족"]),
        {
            "money": "돈은 공식 보상, 직책, 신뢰 기반 계약과 연결됩니다.",
            "career": "직업에서는 조직 신뢰와 직위가 중요합니다.",
            "love": "관계에서는 약속과 예의를 중시합니다.",
            "marriage": "결혼에서는 책임감과 사회적 신뢰가 안정 요인입니다.",
            "personality": "성향은 원칙과 평판을 중요하게 봅니다.",
        },
    ),
    "pyeon_in": _role_rule(
        "직관, 특수 이해, 비공식 지식, 내면의 해석을 중요하게 여기는 역할",
        "남들이 쉽게 보지 못한 의미를 혼자 먼저 느낍니다.",
        "직관적으로 파악하고 자기만의 해석을 만듭니다.",
        ["career", "love"],
        _conditions(["분석 자문", "특수 콘텐츠"], ["연구", "심리", "기획", "리스크 해석"], ["깊은 대화가 있는 관계"], ["내면을 존중하는 결혼"], ["직관", "통찰"]),
        _conditions(["검증하지 않은 판단에 기대는 투자"], ["공식 근거 없는 주장"], ["혼자 해석하고 단정하는 관계"], ["대화 없이 침묵하는 결혼"], ["고립"]),
        _conditions(["해석 착오"], ["신뢰 저하"], ["오해"], ["정서적 고립"], ["생각 과다"]),
        {
            "money": "돈에서는 가설과 정보 해석이 중요하지만 검증이 필요합니다.",
            "career": "직업에서는 특수 분야와 분석 자문에 강점이 있습니다.",
            "love": "관계에서는 직관이 빠르지만 확인 대화가 필요합니다.",
            "marriage": "결혼에서는 내면을 존중받아야 안정됩니다.",
            "personality": "성향은 깊이 생각하고 남다른 해석을 만듭니다.",
        },
    ),
    "jeong_in": _role_rule(
        "공인 지식, 자격, 보호, 정통성을 중요하게 여기는 역할",
        "근거와 자격이 있어야 확신이 생깁니다.",
        "배우고 문서화하며 공식 기준 안에서 설득합니다.",
        ["career", "money", "marriage"],
        _conditions(["문서 계약", "자격 기반 수입"], ["교육", "자격직", "행정", "문서화"], ["상대의 배경을 확인하는 관계"], ["가족과 제도적 보호가 있는 결혼"], ["학습", "품위"]),
        _conditions(["근거 없는 투자"], ["자격을 인정하지 않는 조직"], ["말뿐인 관계"], ["제도적 책임 없는 결혼"], ["현상 유지에 머무름"]),
        _conditions(["실행 지연"], ["형식 피로"], ["거리감"], ["가족 승인 문제"], ["소극성"]),
        {
            "money": "돈은 자격, 문서, 인증, 계약을 통해 안정됩니다.",
            "career": "직업에서는 학습과 공인된 전문성이 강점입니다.",
            "love": "관계에서는 상대의 신뢰도와 배경을 중요하게 봅니다.",
            "marriage": "결혼에서는 제도적 보호와 가족의 인정이 영향을 줍니다.",
            "personality": "성향은 근거를 갖추고 인정받으려 합니다.",
        },
    ),
}


SPECIFIC_RECEPTION_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("mu", "eul"): {
        "core": "戊가 乙을 보면 넓은 기반을 지키려는 성향이 관계적 책임과 세부 규칙을 받아들입니다.",
        "felt": "책임이 한 번 들어오면 쉽게 무시하지 못하고, 관계 안에서 요구되는 도리와 역할을 계속 의식합니다.",
        "behavior": "조직이나 관계 안에서 기준을 설명하고, 사람 사이의 역할을 정리하려는 행동으로 이어집니다.",
    },
    ("mu", "byeong"): {
        "core": "戊가 丙을 보면 넓은 기반 위에 시야, 설명력, 해석 능력을 받아들입니다.",
        "felt": "상황을 이해하고 밝혀야 마음이 놓이며, 특히 차갑거나 불투명한 조건에서 해석 근거를 찾습니다.",
        "behavior": "문서와 설명으로 맡은 책임을 납득 가능한 형태로 바꿉니다. 교육과 분석도 이 힘을 더합니다.",
    },
    ("mu", "gye"): {
        "core": "戊가 癸를 보면 큰 기반이 세부 현금, 계약, 감정 정보를 받아들입니다.",
        "felt": "돈과 약속이 작아 보여도 실제 생활을 움직이는 핵심 조건으로 체감합니다.",
        "behavior": "수치, 정산, 계약 조건을 확인하고 관리하면서 안정성을 만들려 합니다.",
    },
    ("gi", "im"): {
        "core": "己가 壬을 보면 생활 기반을 조정하는 성향이 큰 시장 정보와 대외 자금을 받아들입니다.",
        "felt": "외부 기회가 커 보일수록 그것을 실제로 감당할 수 있는지 먼저 확인합니다.",
        "behavior": "큰 거래와 외부 제안을 현실 조건에 맞게 줄이고 정리하는 방식으로 움직입니다.",
    },
    ("gi", "gap"): {
        "core": "己가 甲을 보면 생활 기반을 다루는 성향이 큰 기준과 상위 책임을 받아들입니다.",
        "felt": "분명한 명령이나 제도적 요구가 들어오면 부담을 느끼지만, 현실에 맞춰 처리하려 합니다.",
        "behavior": "주어진 기준을 현장과 사람의 상황에 맞게 세부 조정합니다.",
    },
}

STEM_PROFILES = REFINED_STEM_PROFILES
TEN_GOD_RECEPTION_RULES = REFINED_TEN_GOD_RECEPTION_RULES
SPECIFIC_RECEPTION_OVERRIDES = {
    **SPECIFIC_RECEPTION_OVERRIDES,
    **REFINED_SPECIFIC_RECEPTION_OVERRIDES,
}


def _copy_conditions(conditions: dict[str, list[str]]) -> dict[str, list[str]]:
    return {domain: list(values) for domain, values in conditions.items()}


PROJECTION_DOMAIN_LABELS = {
    "money": "재물",
    "career": "직업과 사회적 성취",
    "love": "연애와 대인관계",
    "marriage": "결혼과 가정",
    "personality": "성향",
}


def _domain_projection_text(day_stem: str, target_stem: str, ten_god: str, domain: str) -> str:
    day_label = STEM_LABELS[day_stem]
    domain_label = PROJECTION_DOMAIN_LABELS[domain]
    stem_scene = REFINED_STEM_DOMAIN_SCENES[target_stem][domain]
    role_lens = REFINED_TEN_GOD_DOMAIN_LENSES[ten_god][domain]
    return f"{day_label}일간이 {_stem_object(target_stem)} {_ten_god_as(ten_god)} 받을 때, {domain_label}에서는 {stem_scene} {role_lens}"


def _compose_reception_rule(day_stem: str, target_stem: str) -> dict[str, Any]:
    ten_god = ten_god_for(day_stem, target_stem)
    day = STEM_PROFILES[day_stem]
    target = STEM_PROFILES[target_stem]
    role = TEN_GOD_RECEPTION_RULES[ten_god]
    target_label = STEM_LABELS[target_stem]
    role_label = TEN_GOD_LABELS[ten_god]
    target_nature = str(target["object_nature"])
    target_keyword_pair = _keyword_pair_text(target["keywords"][:2])
    override = SPECIFIC_RECEPTION_OVERRIDES.get((day_stem, target_stem), {})
    core = override.get(
        "core",
        f"{_stem_subject(day_stem)} {_stem_object(target_stem)} 보면 {target_nature}{_subject_particle_text(target_nature)} "
        f"{role_label}의 역할을 합니다. {STEM_LABELS[day_stem]}일간은 "
        f"{_stem_subject(target_stem)} 맡은 {target_keyword_pair}{_object_particle_text(target_keyword_pair)} 중요하게 받아들입니다.",
    )
    felt = override.get(
        "felt",
        str(role["felt"]),
    )
    behavior = override.get(
        "behavior",
        f"{role['behavior']} 속으로는 {target_keyword_pair}{_object_particle_text(target_keyword_pair)} 정리하려는 태도가 강합니다.",
    )
    fitting = _copy_conditions(role["fitting"])
    misfitting = _copy_conditions(role["misfitting"])
    fatigue = _copy_conditions(role["fatigue"])
    for domain in ALL_PROJECTION_DOMAINS:
        fitting[domain] = list(dict.fromkeys(fitting[domain] + target["fitting"][:2]))
        misfitting[domain] = list(dict.fromkeys(misfitting[domain] + target["misfitting"][:2]))
    domain_projection = {
        domain: _domain_projection_text(day_stem, target_stem, ten_god, domain)
        for domain in ALL_PROJECTION_DOMAINS
    }
    return {
        "day_stem": day_stem,
        "target_stem": target_stem,
        "target_ten_god": ten_god,
        "trait_keywords": list(dict.fromkeys(target["keywords"] + [role_label, role["core"].split(",")[0]])),
        "core_interpretation": core,
        "felt_experience": felt,
        "behavior_tendency": behavior,
        "fitting_conditions": fitting,
        "misfitting_conditions": misfitting,
        "fatigue_or_loss": fatigue,
        "domain_projection": domain_projection,
        "domain_links": list(role["domain_links"]),
    }


STEM_RECEPTION_RULES: dict[tuple[str, str], dict[str, Any]] = {
    (day_stem, target_stem): _compose_reception_rule(day_stem, target_stem)
    for day_stem in STEM_ORDER
    for target_stem in STEM_ORDER
}


def stem_reception_rule(day_stem: str, target_stem: str) -> dict[str, Any]:
    return STEM_RECEPTION_RULES[(day_stem, target_stem)]


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult):
    pillars = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar
    return pillars


def _position_sort_key(position: str) -> int:
    base = position.split(":", 1)[0]
    return POSITION_ORDER.index(base) if base in POSITION_ORDER else 99


def _service_domains_for_position(position: str) -> list[str]:
    base = position.split(":", 1)[0]
    return {
        "year": ["career", "love"],
        "month": ["career", "money"],
        "day": ["love", "marriage"],
        "hour": ["career", "money", "marriage"],
    }.get(base, [])


def _strength_from_score(score: float) -> str:
    if score >= 1.55:
        return "high"
    if score >= 0.85:
        return "moderate"
    return "low"


def _branch_relation_modifiers(position: str, interactions: list[BranchInteraction]) -> list[str]:
    base = position.split(":", 1)[0]
    modifiers: list[str] = []
    for interaction in interactions:
        if base in interaction.positions:
            modifiers.append(interaction.relation_type)
    return list(dict.fromkeys(modifiers))


def _branch_relation_score_modifier(modifiers: list[str]) -> float:
    score = sum(BRANCH_RELATION_SCORE_MODIFIERS.get(modifier, 0.0) for modifier in modifiers)
    return min(0.35, score)


def _signal_counter_signals(
    *,
    ten_god: str,
    branch_modifiers: list[str],
    protruded: bool,
) -> list[str]:
    counters: list[str] = []
    if ten_god in {"geob_jae", "sang_gwan", "pyeon_gwan", "pyeon_in"}:
        counters.append(f"stem_reception_caution_{ten_god}")
    for modifier in branch_modifiers:
        if modifier in {"clash", "punishment", "self_punishment", "break", "harm"}:
            counters.append(f"stem_reception_branch_{modifier}")
    if protruded and ten_god in {"geob_jae", "sang_gwan", "pyeon_gwan"}:
        counters.append("stem_reception_protruded_counter_signal")
    return list(dict.fromkeys(counters))


def _entry_signal(
    *,
    chart: BirthChartResult,
    entry: dict[str, Any],
    interactions: list[BranchInteraction],
) -> StemReceptionSignal:
    day_stem = chart.day_pillar.stem_key
    target_stem = str(entry["stem"])
    target_element = STEM_METADATA[target_stem]["element"]
    ten_god = ten_god_for(day_stem, target_stem)
    rule = stem_reception_rule(day_stem, target_stem)
    position = str(entry["position"])
    source = str(entry["source"])
    seasonal_modifier = MONTH_SEASON_MODIFIERS[chart.month_pillar.branch_key][target_element]
    branch_modifiers = _branch_relation_modifiers(position, interactions)
    branch_relation_score_modifier = _branch_relation_score_modifier(branch_modifiers)
    protruded = bool(entry.get("protruded", False))
    raw_score = float(entry["weight"]) * seasonal_modifier
    if protruded:
        raw_score += 0.25
    raw_score += branch_relation_score_modifier
    strength = _strength_from_score(raw_score)
    position_domains = _service_domains_for_position(position)
    domain_links = [
        domain
        for domain in ALL_PROJECTION_DOMAINS
        if domain in set(rule["domain_links"] + position_domains)
    ]
    basis_codes = [
        f"stem_reception_{day_stem}_{target_stem}",
        f"stem_reception_ten_god_{ten_god}",
        f"stem_reception_position_{position.split(':', 1)[0]}",
        f"stem_reception_source_{source}",
    ]
    if protruded:
        basis_codes.append("stem_reception_hidden_stem_protruded")
    for modifier in branch_modifiers:
        basis_codes.append(f"stem_reception_branch_modifier_{modifier}")
    evidence = [
        f"day_stem:{day_stem}",
        f"target_stem:{target_stem}",
        f"target_ten_god:{ten_god}",
        f"position:{position}",
        f"source:{source}",
        f"seasonal_modifier:{seasonal_modifier:.2f}",
    ]
    if protruded:
        evidence.append("hidden_stem_protruded:true")
    evidence.extend(f"branch_relation:{modifier}" for modifier in branch_modifiers)
    if branch_relation_score_modifier:
        evidence.append(f"branch_relation_score_modifier:{branch_relation_score_modifier:.2f}")
    suffix = str(entry.get("suffix") or position.replace(":", "_"))
    return StemReceptionSignal(
        signal_id=f"stem_reception_{source}_{suffix}_{day_stem}_receives_{target_stem}",
        layer=str(entry["layer"]),
        day_stem=day_stem,
        target_stem=target_stem,
        target_element=target_element,
        target_ten_god=ten_god,
        position=position,
        branch=str(entry.get("branch", "")),
        source=source,
        strength=strength,
        priority_score=max(1, min(100, int(round(raw_score * 24)))),
        seasonal_modifier=round(seasonal_modifier, 3),
        protruded=protruded,
        branch_relation_modifiers=branch_modifiers,
        branch_relation_score_modifier=round(branch_relation_score_modifier, 3),
        domain_links=domain_links,
        basis_codes=basis_codes,
        counter_signals=_signal_counter_signals(ten_god=ten_god, branch_modifiers=branch_modifiers, protruded=protruded),
        trait_keywords=list(rule["trait_keywords"]),
        core_interpretation=str(rule["core_interpretation"]),
        felt_experience=str(rule["felt_experience"]),
        behavior_tendency=str(rule["behavior_tendency"]),
        fitting_conditions={domain: list(values) for domain, values in rule["fitting_conditions"].items()},
        misfitting_conditions={domain: list(values) for domain, values in rule["misfitting_conditions"].items()},
        fatigue_or_loss={domain: list(values) for domain, values in rule["fatigue_or_loss"].items()},
        domain_projection=dict(rule["domain_projection"]),
        evidence=evidence,
    )


def _visible_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    pillars = _pillars(chart)
    hidden_stems = {
        stem_key
        for pillar in pillars.values()
        for stem_key, _ in BRANCH_HIDDEN_STEMS[pillar.branch_key]
    }
    entries: list[dict[str, Any]] = []
    for position, pillar in pillars.items():
        if position == "day":
            continue
        entries.append(
            {
                "layer": "visible_stem",
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_STEM_WEIGHTS[position],
                "protruded": pillar.stem_key in hidden_stems,
                "suffix": position,
            }
        )
    return entries


def _hidden_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    visible_stems = {pillar.stem_key for pillar in _pillars(chart).values()}
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        for index, (stem_key, hidden_weight) in enumerate(BRANCH_HIDDEN_STEMS[pillar.branch_key]):
            entries.append(
                {
                    "layer": "hidden_stem",
                    "position": f"{position}:hidden:{index}",
                    "source": "hidden",
                    "stem": stem_key,
                    "branch": pillar.branch_key,
                    "weight": POSITION_BRANCH_WEIGHTS[position] * hidden_weight,
                    "protruded": stem_key in visible_stems,
                    "suffix": f"{position}_{index}",
                }
            )
    return entries


def _branch_main_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    visible_stems = {pillar.stem_key for pillar in _pillars(chart).values()}
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        stem_key = main_hidden_stem(pillar.branch_key)
        entries.append(
            {
                "layer": "branch_main",
                "position": f"{position}:branch_main",
                "source": "branch_main",
                "stem": stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_BRANCH_WEIGHTS[position],
                "protruded": stem_key in visible_stems,
                "suffix": position,
            }
        )
    return entries


def _signal_rank(signal: StemReceptionSignal) -> tuple[int, int, int, int]:
    layer_rank = {"visible_stem": 0, "branch_main": 1, "hidden_stem": 2}.get(signal.layer, 3)
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    position_rank = _position_sort_key(signal.position)
    return (layer_rank, strength_rank, position_rank, -signal.priority_score)


def _dedupe_reception_signals(signals: list[StemReceptionSignal], limit: int | None = None) -> list[StemReceptionSignal]:
    deduped: list[StemReceptionSignal] = []
    seen: set[tuple[str, str, str, str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        key = (signal.layer, signal.day_stem, signal.target_stem, signal.position)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _reception_summary(signals: list[StemReceptionSignal]) -> list[str]:
    selected = sorted(signals, key=_signal_rank)[:5]
    sentences: list[str] = []
    for signal in selected:
        fit = ", ".join(signal.fitting_conditions["career"][:2])
        misfit = ", ".join(signal.misfitting_conditions["career"][:2])
        fit_context = _career_fit_context(signal.target_ten_god)
        misfit_context = _career_misfit_context(signal.target_ten_god)
        sentences.append(
            f"당신의 사주에서 {STEM_LABELS[signal.day_stem]}일간은 {_stem_object(signal.target_stem)} {_ten_god_as(signal.target_ten_god)} 받아들입니다. {signal.core_interpretation} 직업적으로는 {fit}처럼 {fit_context}에서 강점이 분명하고, {misfit}처럼 {misfit_context}은 맞지 않습니다."
        )
    return sentences


def build_stem_reception_profile(
    chart: BirthChartResult,
    interactions: list[BranchInteraction],
) -> StemReceptionProfile:
    visible_stem_signals = [_entry_signal(chart=chart, entry=entry, interactions=interactions) for entry in _visible_entries(chart)]
    hidden_stem_signals = [_entry_signal(chart=chart, entry=entry, interactions=interactions) for entry in _hidden_entries(chart)]
    branch_main_signals = [_entry_signal(chart=chart, entry=entry, interactions=interactions) for entry in _branch_main_entries(chart)]
    all_signals = _dedupe_reception_signals(visible_stem_signals + branch_main_signals + hidden_stem_signals)
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_signal_rank)[:12]]
    return StemReceptionProfile(
        visible_stem_signals=visible_stem_signals,
        hidden_stem_signals=_dedupe_reception_signals(hidden_stem_signals, limit=36),
        branch_main_signals=branch_main_signals,
        top_signal_ids=top_signal_ids,
        summary_sentences=_reception_summary(all_signals),
    )


def iter_stem_reception_signals(profile: StemReceptionProfile) -> list[StemReceptionSignal]:
    return (
        list(profile.visible_stem_signals)
        + list(profile.branch_main_signals)
        + list(profile.hidden_stem_signals)
    )


def _entry_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    return (_position_sort_key(str(entry["position"])), str(entry["source"]), str(entry["stem"]))


def _pair_strength(source: StemReceptionSignal, target: StemReceptionSignal) -> str:
    if source.source == "visible" and target.source == "visible":
        return "high"
    if source.source == "visible" or target.source == "visible":
        return "moderate"
    total = source.priority_score + target.priority_score
    return "moderate" if total >= 55 else "low"


def _merge_condition_dicts(*items: dict[str, list[str]], limit: int = 5) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {domain: [] for domain in ALL_PROJECTION_DOMAINS}
    for item in items:
        for domain in ALL_PROJECTION_DOMAINS:
            merged[domain].extend(item.get(domain, []))
    return {domain: list(dict.fromkeys(values))[:limit] for domain, values in merged.items()}


def _integrated_domain_projection(
    source: StemReceptionSignal,
    target: StemReceptionSignal,
    ten_god_rule: dict[str, Any],
) -> dict[str, str]:
    source_label = STEM_LABELS[source.target_stem]
    target_label = STEM_LABELS[target.target_stem]
    source_role = TEN_GOD_LABELS[source.target_ten_god]
    target_role = TEN_GOD_LABELS[target.target_ten_god]
    projections: dict[str, str] = {}
    for domain in ALL_PROJECTION_DOMAINS:
        source_note = source.domain_projection[domain]
        target_note = target.domain_projection[domain]
        projections[domain] = f"{source_note} 또한 {target_note}"
    return projections


def _integrated_signal(
    *,
    layer: str,
    source: StemReceptionSignal,
    target: StemReceptionSignal,
    index: int,
) -> IntegratedSajuSignal:
    source_element = source.target_element
    target_element = target.target_element
    element_direction_key = f"{source_element}->{target_element}"
    ten_god_direction_key = f"{source.target_ten_god}->{target.target_ten_god}"
    ten_god_rule = ten_god_direction_rule(source.target_ten_god, target.target_ten_god)
    direction_type = _direction_type(source_element, target_element)
    role_keywords = list(ten_god_rule["trait_keywords"])
    strength = _pair_strength(source, target)
    priority_score = min(100, max(1, int(round((source.priority_score + target.priority_score) / 2))))
    if source.protruded or target.protruded:
        priority_score = min(100, priority_score + 6)
    branch_modifiers = list(dict.fromkeys(source.branch_relation_modifiers + target.branch_relation_modifiers))
    branch_relation_score_modifier = min(
        0.35,
        source.branch_relation_score_modifier + target.branch_relation_score_modifier,
    )
    if any(item in {"clash", "punishment", "self_punishment"} for item in branch_modifiers):
        priority_score = min(100, priority_score + 8)
    if branch_relation_score_modifier:
        priority_score = min(100, priority_score + int(round(branch_relation_score_modifier * 12)))
    domain_links = [
        domain
        for domain in ALL_PROJECTION_DOMAINS
        if domain in set(source.domain_links + target.domain_links + list(ten_god_rule["domain_links"]))
    ]
    integrated_basis_codes = [
        f"integrated_stem_pair_{source.target_stem}_{target.target_stem}",
        f"integrated_element_direction_{element_direction_key.replace('->', '_to_')}",
        f"integrated_ten_god_direction_{ten_god_direction_key.replace('->', '_to_')}",
        f"integrated_direction_type_{direction_type}",
    ]
    if branch_relation_score_modifier:
        integrated_basis_codes.append(f"integrated_branch_relation_score_{branch_relation_score_modifier:.2f}")
    basis_codes = list(dict.fromkeys(source.basis_codes + target.basis_codes + integrated_basis_codes))
    counter_signals = list(dict.fromkeys(source.counter_signals + target.counter_signals + list(ten_god_rule["counter_signals"])))
    if any(item in {"clash", "punishment", "break", "harm"} for item in branch_modifiers):
        counter_signals.append("integrated_branch_relation_caution")
    fitting = _merge_condition_dicts(source.fitting_conditions, target.fitting_conditions)
    misfitting = _merge_condition_dicts(source.misfitting_conditions, target.misfitting_conditions)
    fatigue = _merge_condition_dicts(source.fatigue_or_loss, target.fatigue_or_loss)
    source_label = STEM_LABELS[source.target_stem]
    target_label = STEM_LABELS[target.target_stem]
    source_role = TEN_GOD_LABELS[source.target_ten_god]
    target_role = TEN_GOD_LABELS[target.target_ten_god]
    core = (
        f"{_stem_subject(source.target_stem)} {_stem_object(target.target_stem)} 만나는 물상과 "
        f"{source_role}{_subject_particle_text(source_role)} {target_role}{_object_particle_text(target_role)} 대하는 역할이 한 장면에서 겹칩니다."
    )
    combined = (
        f"{source.core_interpretation} 여기에 {ten_god_rule['interpretation']} "
        f"이 관계는 장점이 살아나는 지점과 피로가 커지는 지점을 함께 구분해야 정확합니다."
    )
    evidence = list(
        dict.fromkeys(
            source.evidence
            + target.evidence
            + [
                f"element_direction:{element_direction_key}",
                f"ten_god_direction:{ten_god_direction_key}",
                f"direction_type:{direction_type}",
            ]
        )
    )
    if branch_relation_score_modifier:
        evidence.append(f"integrated_branch_relation_score_modifier:{branch_relation_score_modifier:.2f}")
    return IntegratedSajuSignal(
        signal_id=f"integrated_{layer}_{index}_{source.target_stem}_to_{target.target_stem}_{source.target_ten_god}_to_{target.target_ten_god}",
        layer=layer,
        source_position=source.position,
        target_position=target.position,
        source_stem=source.target_stem,
        target_stem=target.target_stem,
        source_element=source_element,
        target_element=target_element,
        source_ten_god=source.target_ten_god,
        target_ten_god=target.target_ten_god,
        element_direction_key=element_direction_key,
        ten_god_direction_key=ten_god_direction_key,
        source_reception_key=f"{source.day_stem}->{source.target_stem}",
        target_reception_key=f"{target.day_stem}->{target.target_stem}",
        strength=strength,
        priority_score=priority_score,
        branch_relation_score_modifier=round(branch_relation_score_modifier, 3),
        domain_links=domain_links,
        basis_codes=basis_codes,
        counter_signals=list(dict.fromkeys(counter_signals)),
        trait_keywords=list(dict.fromkeys(source.trait_keywords[:3] + target.trait_keywords[:3] + role_keywords)),
        core_interpretation=core,
        combined_interpretation=combined,
        fitting_conditions=fitting,
        misfitting_conditions=misfitting,
        fatigue_or_loss=fatigue,
        domain_projection=_integrated_domain_projection(source, target, ten_god_rule),
        evidence=evidence,
    )


def _integrated_rank(signal: IntegratedSajuSignal) -> tuple[int, int, int, int]:
    layer_rank = {"visible_pair": 0, "stem_branch_pair": 1, "hidden_pair": 2}.get(signal.layer, 3)
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    position_rank = min(_position_sort_key(signal.source_position), _position_sort_key(signal.target_position))
    return (layer_rank, strength_rank, position_rank, -signal.priority_score)


def _dedupe_integrated_signals(signals: list[IntegratedSajuSignal], limit: int | None = None) -> list[IntegratedSajuSignal]:
    deduped: list[IntegratedSajuSignal] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for signal in sorted(signals, key=_integrated_rank):
        key = (signal.layer, signal.source_stem, signal.target_stem, signal.source_position, signal.target_position)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _integrated_pair_signals(
    *,
    layer: str,
    signals: list[StemReceptionSignal],
    limit: int | None = None,
) -> list[IntegratedSajuSignal]:
    integrated: list[IntegratedSajuSignal] = []
    ordered = sorted(signals, key=lambda item: (_position_sort_key(item.position), item.source, item.target_stem))
    for index, (source, target) in enumerate(permutations(ordered, 2), start=1):
        if source.position == target.position:
            continue
        integrated.append(_integrated_signal(layer=layer, source=source, target=target, index=index))
    return _dedupe_integrated_signals(integrated, limit=limit)


def _stem_branch_pair_signals(profile: StemReceptionProfile) -> list[IntegratedSajuSignal]:
    visible_by_base: dict[str, StemReceptionSignal] = {}
    for signal in profile.visible_stem_signals:
        base = signal.position.split(":", 1)[0]
        visible_by_base[base] = signal
    integrated: list[IntegratedSajuSignal] = []
    index = 0
    for branch_signal in profile.branch_main_signals:
        base = branch_signal.position.split(":", 1)[0]
        visible = visible_by_base.get(base)
        if not visible:
            continue
        index += 1
        integrated.append(_integrated_signal(layer="stem_branch_pair", source=visible, target=branch_signal, index=index))
        index += 1
        integrated.append(_integrated_signal(layer="stem_branch_pair", source=branch_signal, target=visible, index=index))
    return _dedupe_integrated_signals(integrated)


def _integrated_summary(signals: list[IntegratedSajuSignal]) -> list[str]:
    selected = sorted(signals, key=_integrated_rank)[:5]
    sentences: list[str] = []
    for signal in selected:
        source_role = TEN_GOD_LABELS[signal.source_ten_god]
        fit = ", ".join(signal.fitting_conditions["career"][:2])
        misfit = ", ".join(signal.misfitting_conditions["career"][:2])
        source_fit_context = _career_fit_context(signal.source_ten_god)
        target_fit_context = _career_fit_context(signal.target_ten_god)
        source_misfit_context = _career_misfit_context(signal.source_ten_god)
        target_misfit_context = _career_misfit_context(signal.target_ten_god)
        sentences.append(
            f"당신의 사주에서 {_stem_with(signal.source_stem)} {_stem_subject(signal.target_stem)} 만날 때는 {source_role}에서 {_ten_god_as(signal.target_ten_god)} 이어지는 의미가 생깁니다. 직업적으로는 {fit}처럼 {source_fit_context}이면서 {target_fit_context}가 함께 갖추어질 때 맞고, {misfit}처럼 {source_misfit_context}이거나 {target_misfit_context}이면 부담이 커집니다."
        )
    return sentences


def build_integrated_saju_profile(stem_reception_profile: StemReceptionProfile) -> IntegratedSajuProfile:
    visible_pair_signals = _integrated_pair_signals(layer="visible_pair", signals=stem_reception_profile.visible_stem_signals)
    hidden_pair_signals = _integrated_pair_signals(layer="hidden_pair", signals=stem_reception_profile.hidden_stem_signals, limit=36)
    stem_branch_pair_signals = _stem_branch_pair_signals(stem_reception_profile)
    all_signals = _dedupe_integrated_signals(visible_pair_signals + stem_branch_pair_signals + hidden_pair_signals)
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_integrated_rank)[:12]]
    return IntegratedSajuProfile(
        visible_pair_signals=visible_pair_signals,
        hidden_pair_signals=hidden_pair_signals,
        stem_branch_pair_signals=stem_branch_pair_signals,
        top_signal_ids=top_signal_ids,
        summary_sentences=_integrated_summary(all_signals),
    )


def iter_integrated_saju_signals(profile: IntegratedSajuProfile) -> list[IntegratedSajuSignal]:
    return (
        list(profile.visible_pair_signals)
        + list(profile.stem_branch_pair_signals)
        + list(profile.hidden_pair_signals)
    )
