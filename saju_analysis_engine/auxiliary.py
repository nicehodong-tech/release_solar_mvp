"""Auxiliary rules: twelve growth stages and selected shinsal markers."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

from saju_birth_engine.models import BirthChartResult
from saju_birth_engine.pillars import year_pillar_for_gregorian_year

from .constants import POSITION_DOMAINS
from .models import AuxiliaryMiscSignal, AuxiliaryProfile


TWELVE_GROWTH = {
    "gap": ["hae", "ja", "chuk", "in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul"],
    "eul": ["o", "sa", "jin", "myo", "in", "chuk", "ja", "hae", "sul", "yu", "sin", "mi"],
    "byeong": ["in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk"],
    "jeong": ["yu", "sin", "mi", "o", "sa", "jin", "myo", "in", "chuk", "ja", "hae", "sul"],
    "mu": ["in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk"],
    "gi": ["yu", "sin", "mi", "o", "sa", "jin", "myo", "in", "chuk", "ja", "hae", "sul"],
    "gyeong": ["sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk", "in", "myo", "jin"],
    "sin": ["ja", "hae", "sul", "yu", "sin", "mi", "o", "sa", "jin", "myo", "in", "chuk"],
    "im": ["sin", "yu", "sul", "hae", "ja", "chuk", "in", "myo", "jin", "sa", "o", "mi"],
    "gye": ["myo", "in", "chuk", "ja", "hae", "sul", "yu", "sin", "mi", "o", "sa", "jin"],
}

GROWTH_LABELS = [
    "changsheng",
    "muyu",
    "guandai",
    "linguan",
    "diwang",
    "shuai",
    "bing",
    "si",
    "mu",
    "jue",
    "tai",
    "yang",
]

TWELVE_SINSAL_ORDER = (
    "geopsal",
    "jaesal",
    "cheonsal",
    "jisal",
    "yeonsal",
    "wolsal",
    "mangsin_sal",
    "jangseong_sal",
    "banan_sal",
    "yeokma_sal",
    "yukhae_sal",
    "hwagae_sal",
)

TWELVE_SINSAL_LABELS = {
    "geopsal": "겁살",
    "jaesal": "재살",
    "cheonsal": "천살",
    "jisal": "지살",
    "yeonsal": "연살",
    "wolsal": "월살",
    "mangsin_sal": "망신살",
    "jangseong_sal": "장성살",
    "banan_sal": "반안살",
    "yeokma_sal": "역마살",
    "yukhae_sal": "육해살",
    "hwagae_sal": "화개살",
    "peach_blossom": "도화",
    "travel_horse": "역마",
    "huagai": "화개",
}

TWELVE_SINSAL_MEANINGS = {
    "geopsal": "기존 질서 밖에서 강한 자극이 들어오는 보조 신호",
    "jaesal": "규칙, 압박, 통제 문제가 구체화되는 보조 신호",
    "cheonsal": "개인이 바로 통제하기 어려운 외부 조건을 만나는 보조 신호",
    "jisal": "직접 움직이고 현장에 발을 딛는 보조 신호",
    "yeonsal": "시선, 매력, 관계 접점이 밖으로 드러나는 보조 신호",
    "wolsal": "속도가 줄고 보이지 않는 준비와 지연이 생기는 보조 신호",
    "mangsin_sal": "감춰둔 것이 밖으로 드러나 평가받는 보조 신호",
    "jangseong_sal": "주도권과 힘이 강해지는 보조 신호",
    "banan_sal": "움직인 뒤 자리와 지위를 얻어 안정하는 보조 신호",
    "yeokma_sal": "이동, 외부 활동, 영역 확장이 커지는 보조 신호",
    "yukhae_sal": "활동 뒤에 반복되는 작은 부담을 감당하는 보조 신호",
    "hwagae_sal": "경험을 거두어 지식, 예술, 전문성으로 정리하는 보조 신호",
    "peach_blossom": "시선, 매력, 관계 접점이 밖으로 드러나는 보조 신호",
    "travel_horse": "이동, 외부 활동, 영역 확장이 커지는 보조 신호",
    "huagai": "경험을 거두어 지식, 예술, 전문성으로 정리하는 보조 신호",
}

TWELVE_SINSAL_DOMAINS = {
    "geopsal": ["career", "money", "social"],
    "jaesal": ["career", "honor", "social"],
    "cheonsal": ["personality", "life"],
    "jisal": ["career", "social", "life"],
    "yeonsal": ["love", "social", "honor"],
    "wolsal": ["personality", "career"],
    "mangsin_sal": ["social", "honor"],
    "jangseong_sal": ["career", "honor", "personality"],
    "banan_sal": ["career", "honor"],
    "yeokma_sal": ["career", "life"],
    "yukhae_sal": ["life", "social"],
    "hwagae_sal": ["personality", "career"],
}

SINSAL_BRANCH_TABLE = {
    "fire_group": ("hae", "ja", "chuk", "in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul"),
    "water_group": ("sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk", "in", "myo", "jin"),
    "metal_group": ("in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk"),
    "wood_group": ("sin", "yu", "sul", "hae", "ja", "chuk", "in", "myo", "jin", "sa", "o", "mi"),
}

SINSAL_GROUPS = (
    ({"in", "o", "sul"}, "fire_group"),
    ({"sin", "ja", "jin"}, "water_group"),
    ({"sa", "yu", "chuk"}, "metal_group"),
    ({"hae", "myo", "mi"}, "wood_group"),
)

SINSAL_ALIASES = {
    "yeonsal": "peach_blossom",
    "yeokma_sal": "travel_horse",
    "hwagae_sal": "huagai",
}


LUGOD_BRANCH_BY_DAY_STEM = {
    "gap": "in",
    "eul": "myo",
    "byeong": "sa",
    "mu": "sa",
    "jeong": "o",
    "gi": "o",
    "gyeong": "sin",
    "sin": "yu",
    "im": "hae",
    "gye": "ja",
}

GEUMYEO_BRANCH_BY_DAY_STEM = {
    "gap": "jin",
    "eul": "sa",
    "byeong": "mi",
    "mu": "mi",
    "jeong": "sin",
    "gi": "sin",
    "gyeong": "sul",
    "sin": "hae",
    "im": "chuk",
    "gye": "in",
}

CHEONEUL_BRANCHES_BY_STEM = {
    "gap": {"chuk", "mi"},
    "mu": {"chuk", "mi"},
    "gyeong": {"chuk", "mi"},
    "eul": {"ja", "sin"},
    "gi": {"ja", "sin"},
    "byeong": {"hae", "yu"},
    "jeong": {"hae", "yu"},
    "sin": {"in", "o"},
    "im": {"myo", "sa"},
    "gye": {"myo", "sa"},
}

TAEGEUK_BRANCHES_BY_STEM = {
    "gap": {"ja", "o"},
    "eul": {"ja", "o"},
    "byeong": {"myo", "yu"},
    "jeong": {"myo", "yu"},
    "mu": {"jin", "sul", "chuk", "mi"},
    "gi": {"jin", "sul", "chuk", "mi"},
    "gyeong": {"in", "hae"},
    "sin": {"in", "hae"},
    "im": {"sa", "sin"},
    "gye": {"sa", "sin"},
}

MOONCHANG_MODERN_BRANCH_BY_DAY_STEM = {
    "gap": "sa",
    "eul": "o",
    "byeong": "sin",
    "mu": "sin",
    "jeong": "yu",
    "gi": "yu",
    "gyeong": "hae",
    "sin": "ja",
    "im": "in",
    "gye": "myo",
}

MOONCHANG_CLASSIC_BRANCH_BY_DAY_STEM = {
    "gap": "sa",
    "eul": "hae",
    "byeong": "sul",
    "jeong": "jin",
    "mu": "sin",
    "gi": "o",
    "gyeong": "in",
    "sin": "mi",
    "im": "myo",
    "gye": "chuk",
}

HAKDANG_BRANCHES_BY_DAY_STEM = {
    "gap": {"hae", "in"},
    "eul": {"hae", "in"},
    "byeong": {"in", "sa"},
    "jeong": {"in", "sa"},
    "mu": {"sin", "hae"},
    "gi": {"sin", "hae"},
    "gyeong": {"sa", "sin"},
    "sin": {"sa", "sin"},
    "im": {"sin", "hae"},
    "gye": {"sin", "hae"},
}

GUKIN_BRANCH_BY_DAY_STEM = {
    "gap": "sul",
    "eul": "hae",
    "byeong": "chuk",
    "mu": "chuk",
    "jeong": "in",
    "gi": "in",
    "gyeong": "jin",
    "sin": "sa",
    "im": "mi",
    "gye": "sin",
}

CHEONDEOK_TARGET_BY_MONTH_BRANCH = {
    "in": ("stem", "jeong"),
    "myo": ("branch", "sin"),
    "jin": ("stem", "im"),
    "sa": ("stem", "sin"),
    "o": ("branch", "hae"),
    "mi": ("stem", "gap"),
    "sin": ("stem", "gye"),
    "yu": ("branch", "in"),
    "sul": ("stem", "byeong"),
    "hae": ("stem", "eul"),
    "ja": ("branch", "sa"),
    "chuk": ("stem", "gyeong"),
}

WOLDEOK_STEM_BY_MONTH_GROUP = {
    "fire_group": "byeong",
    "wood_group": "gap",
    "water_group": "im",
    "metal_group": "gyeong",
}

YANGIN_STRICT_BRANCH_BY_DAY_STEM = {
    "gap": "myo",
    "byeong": "o",
    "mu": "o",
    "gyeong": "yu",
    "im": "ja",
}

YANGIN_EXPANDED_BRANCH_BY_DAY_STEM = {
    "eul": "in",
    "jeong": "sa",
    "gi": "sa",
    "sin": "sin",
    "gye": "hae",
}

HONGYEOM_BRANCH_BY_DAY_STEM = {
    "gap": "o",
    "eul": "o",
    "byeong": "in",
    "jeong": "mi",
    "mu": "ja",
    "gi": "jin",
    "gyeong": "sul",
    "sin": "yu",
    "im": "sa",
    "gye": "sin",
}

HONGLAN_CHEONHUI_BY_YEAR_BRANCH = {
    "ja": {"honglan": "myo", "cheonhui": "yu"},
    "chuk": {"honglan": "in", "cheonhui": "sin"},
    "in": {"honglan": "chuk", "cheonhui": "mi"},
    "myo": {"honglan": "ja", "cheonhui": "o"},
    "jin": {"honglan": "hae", "cheonhui": "sa"},
    "sa": {"honglan": "sul", "cheonhui": "jin"},
    "o": {"honglan": "yu", "cheonhui": "myo"},
    "mi": {"honglan": "sin", "cheonhui": "in"},
    "sin": {"honglan": "mi", "cheonhui": "chuk"},
    "yu": {"honglan": "o", "cheonhui": "ja"},
    "sul": {"honglan": "sa", "cheonhui": "hae"},
    "hae": {"honglan": "jin", "cheonhui": "sul"},
}

GWIMUN_PAIRS = {
    frozenset(("ja", "yu")),
    frozenset(("chuk", "o")),
    frozenset(("in", "mi")),
    frozenset(("myo", "sin")),
    frozenset(("jin", "hae")),
    frozenset(("sa", "sul")),
}

WONJIN_PAIRS = {
    frozenset(("ja", "mi")),
    frozenset(("chuk", "o")),
    frozenset(("in", "yu")),
    frozenset(("myo", "sin")),
    frozenset(("jin", "hae")),
    frozenset(("sa", "sul")),
}

GOJIN_GWASUK_BY_YEAR_GROUP = {
    frozenset(("hae", "ja", "chuk")): {"gojin": "in", "gwasuk": "sul"},
    frozenset(("in", "myo", "jin")): {"gojin": "sa", "gwasuk": "chuk"},
    frozenset(("sa", "o", "mi")): {"gojin": "sin", "gwasuk": "jin"},
    frozenset(("sin", "yu", "sul")): {"gojin": "hae", "gwasuk": "mi"},
}

SIPAK_DAEPAE_DAY_PILLARS = {
    "甲辰",
    "乙巳",
    "丙申",
    "丁亥",
    "戊戌",
    "己丑",
    "庚辰",
    "辛巳",
    "壬申",
    "癸亥",
}

EUMYANG_CHACHAK_DAY_PILLARS = {
    "丙子",
    "丁丑",
    "戊寅",
    "辛卯",
    "壬辰",
    "癸巳",
    "丙午",
    "丁未",
    "戊申",
    "辛酉",
    "壬戌",
    "癸亥",
}

GOEGANG_DAY_PILLARS = {"庚辰", "壬辰", "戊戌", "庚戌"}

BAEKHO_DAY_PILLARS = {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}

GORAN_DAY_PILLARS = {"乙巳", "丁巳", "辛亥", "戊申", "甲寅", "丙午", "戊午", "壬子"}

PALJEON_DAY_PILLARS = {"甲寅", "乙卯", "己未", "丁未", "庚申", "辛酉", "戊戌", "癸丑"}

GUCHU_DAY_PILLARS = {"壬子", "壬午", "戊子", "戊午", "己酉", "己卯", "乙卯", "辛酉", "辛卯"}

HYEONCHIM_STEMS = {"gap", "sin"}
HYEONCHIM_BRANCHES = {"myo", "o", "sin"}
CHEOLSHOE_BRANCHES = {"myo", "yu", "sul"}

GONGMANG_BRANCHES_BY_SUN = (
    ("gap_ja旬", {"sul", "hae"}),
    ("gap_sul旬", {"sin", "yu"}),
    ("gap_sin旬", {"o", "mi"}),
    ("gap_o旬", {"jin", "sa"}),
    ("gap_jin旬", {"in", "myo"}),
    ("gap_in旬", {"ja", "chuk"}),
)

MISC_SHINSAL_META = {
    "lugod": ("건록", "A", "고전 명리", "자립, 직업 기반, 자기 기술이 자리 잡는 보조 신호", "녹 하나로 재물과 직책을 확정하지 않습니다.", "career"),
    "geumyeo": ("금여", "A/B", "고전 명리", "생활 기반, 편의, 주거와 현실적 지원을 보는 보조 신호", "부귀와 고급 생활을 자동 단정하지 않습니다.", "money"),
    "cheoneul_day": ("천을귀인", "A", "고전 명리", "사람, 제도, 문서가 도움으로 작용할 여지를 보는 보조 신호", "누군가가 반드시 문제를 해결한다고 단정하지 않습니다.", "career"),
    "cheoneul_year": ("천을귀인", "A", "고전 명리", "대외 배경에서 조력과 중재가 붙을 여지를 보는 보조 신호", "연간 기준과 일간 기준을 합산하지 않습니다.", "career"),
    "cheondeok": ("천덕귀인", "A/B", "고전 명리", "계절의 거친 작용을 누그러뜨리는 보조 신호", "덕성이 원국 전체의 약점을 대신하지 않습니다.", "personality"),
    "woldeok": ("월덕귀인", "A", "고전 명리", "갈등 완화, 공적 신뢰, 원칙적 처리를 돕는 보조 신호", "월덕 하나로 사회적 성공을 확정하지 않습니다.", "career"),
    "taegeuk": ("태극귀인", "A/B", "고전 명리", "원리, 상징, 철학적 사고에 대한 관심을 보는 보조 신호", "영적 능력이나 종교 진로를 단정하지 않습니다.", "personality"),
    "moonchang_modern": ("문창귀인", "B", "현대 만세력", "내용을 정리하고 문서, 말, 시험, 기획으로 표현하는 보조 신호", "문창 하나로 학력과 합격을 단정하지 않습니다.", "career"),
    "moonchang_classic": ("문창귀인", "B", "오행정기 계열", "고전식 문창 표로 보는 문서와 학습의 보조 신호", "현대식 문창과 같은 필드로 합치지 않습니다.", "career"),
    "hakdang": ("학당·사관", "B", "오행정기 계열", "학습, 자격, 시험, 지식을 체계로 만드는 보조 신호", "인성, 식상, 월령과 함께 보아야 합니다.", "career"),
    "gukin": ("국인귀인", "B/C", "현대 실무", "기관, 직책, 자격, 공식 문서와 연결되는 보조 신호", "관성과 인성이 받쳐줄 때만 비중을 높입니다.", "career"),
    "honglan": ("홍란", "B/C", "연운·택일 계통", "혼인, 경사, 즐거운 만남을 보조하는 신호", "결혼 여부는 배우자궁과 운을 우선합니다.", "love"),
    "cheonhui": ("천희", "B/C", "연운·택일 계통", "관계의 기쁨과 축하할 일을 보조하는 신호", "경사를 확정하지 않습니다.", "love"),
    "yangin_strict": ("양인", "A/B", "자평법", "결단, 기술, 경쟁력, 위기 대응을 보조하는 강한 신호", "사고와 손상은 충형, 백호, 운의 반복이 함께 있어야만 올립니다.", "career"),
    "yangin_expanded": ("확장 양인", "C", "현대 만세력", "음간 확장표로 보는 강한 자기 방식의 보조 신호", "엄격 양인과 같은 공식으로 처리하지 않습니다.", "personality"),
    "gongmang": ("공망", "A", "고전 명리", "해당 자리의 내용이 늦거나 다른 형태로 채워지는 보조 신호", "가족, 배우자, 자녀의 부재를 단정하지 않습니다.", "personality"),
    "gojin": ("고진", "A/B", "고전 명리", "독립 생활, 혼자 집중하는 능력, 친밀 거리의 보조 신호", "독신과 이별을 단정하지 않습니다.", "love"),
    "gwasuk": ("과숙", "A/B", "고전 명리", "관계에 휩쓸리지 않는 태도와 독립성의 보조 신호", "배우자와 사별한다고 말하지 않습니다.", "love"),
    "cheonra": ("천라", "A/B", "고전 명리", "쉽게 빠져나오기 어려운 책임과 규정의 보조 신호", "감옥과 구속을 문자 그대로 말하지 않습니다.", "career"),
    "jimang": ("지망", "A/B", "고전 명리", "복잡한 규정, 가족과 조직의 얽힘을 보는 보조 신호", "구속과 형벌을 단정하지 않습니다.", "career"),
    "sipak_daepae": ("십악대패", "A/B", "고전 명리", "자기 기반과 보상의 연결이 늦어지는 보조 신호", "재산 손실 결론으로 바로 연결하지 않습니다.", "money"),
    "eumyang_chachak": ("음양차착", "A/B", "고전 명리", "가족 방식, 생활 기준, 관계 공식화에서 어긋남을 보는 보조 신호", "혼인 실패를 단정하지 않습니다.", "love"),
    "goegang": ("괴강", "A/B", "고전 명리", "권한, 결단, 위기에서 버티는 힘을 보조하는 신호", "성별에 따른 흉한 단정은 사용하지 않습니다.", "career"),
    "baekho": ("백호대살", "C", "한국 실무", "긴장도 높은 일, 위기 대응, 강한 책임을 보조하는 신호", "사고, 수술, 혈광을 자동 출력하지 않습니다.", "career"),
    "hongyeom": ("홍염살", "A/B", "고전 명리", "개인적인 끌림과 친밀한 관계 감각을 보는 보조 신호", "성적 낙인으로 사용하지 않습니다.", "love"),
    "goran": ("고란", "B", "고전 명리", "관계 안에서 자기 기준과 독립성이 강한 보조 신호", "결혼 불가를 단정하지 않습니다.", "love"),
    "paljeon": ("팔전", "B/D", "고전 잡설", "자기 기운이 한쪽으로 강하게 모이는 보조 신호", "옛 도덕 판단은 사용하지 않습니다.", "personality"),
    "guchu": ("구추", "B/D", "고전 잡설", "관계에서 자기 방식이 강해지는 보조 신호", "성적 문란이나 추한 결말을 말하지 않습니다.", "personality"),
    "gwimun": ("귀문관살", "C", "한국 실무", "분위기, 직관, 반복 사고, 상담과 연구 감각을 보는 보조 신호", "정신질환, 빙의, 범죄를 단정하지 않습니다.", "personality"),
    "wonjin": ("원진살", "C", "한국 실무", "가까운 관계에서 방식과 감정 기준이 어긋나는 보조 신호", "부부 불화와 이혼을 단정하지 않습니다.", "love"),
    "hyeonchim": ("현침살", "C", "한국 실무", "정밀함, 손기술, 날카로운 언어 감각을 보는 보조 신호", "의료나 사고 결론으로 바로 올리지 않습니다.", "career"),
    "cheolshoe": ("철쇄개금", "C", "한국 실무", "막힌 문제의 원인을 찾아내고 해결하는 보조 신호", "활인업을 확정하지 않습니다.", "career"),
    "cheonmun": ("천문성", "C", "한국 실무", "상징, 철학, 밤의 사유, 보이지 않는 원리에 대한 관심을 보는 보조 신호", "종교인이나 영적 능력을 단정하지 않습니다.", "personality"),
}


def _sinsal_targets(group_name: str) -> dict[str, str]:
    branches = SINSAL_BRANCH_TABLE.get(group_name, ())
    targets = {name: branch for name, branch in zip(TWELVE_SINSAL_ORDER, branches)}
    for source, alias in SINSAL_ALIASES.items():
        if source in targets:
            targets[alias] = targets[source]
    return targets


SAL_GROUPS = [
    (branches, group_name, _sinsal_targets(group_name))
    for branches, group_name in SINSAL_GROUPS
]


def growth_stage(day_stem_key: str, branch_key: str) -> str:
    branch_order = TWELVE_GROWTH[day_stem_key]
    return GROWTH_LABELS[branch_order.index(branch_key)]


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult) -> dict[str, str]:
    pillars = {
        "year": chart.year_pillar.branch_key,
        "month": chart.month_pillar.branch_key,
        "day": chart.day_pillar.branch_key,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar.branch_key
    return pillars


def _group_and_targets(reference_branch_key: str) -> tuple[str, dict[str, str]]:
    for branches, group_name, rules in SAL_GROUPS:
        if reference_branch_key in branches:
            return group_name, rules
    return "unknown_group", {}


def _sal_by_position(positions: dict[str, str], sal_targets: dict[str, str]) -> dict[str, list[str]]:
    sal_by_position: dict[str, list[str]] = {position: [] for position in positions}
    for position, branch_key in positions.items():
        for sal_name, target_branch in sal_targets.items():
            if branch_key == target_branch:
                sal_by_position[position].append(sal_name)
    return sal_by_position


def _stem_positions(chart: BirthChartResult) -> dict[str, str]:
    positions = {
        "year": chart.year_pillar.stem_key,
        "month": chart.month_pillar.stem_key,
        "day": chart.day_pillar.stem_key,
    }
    if not _birth_time_unknown(chart):
        positions["hour"] = chart.hour_pillar.stem_key
    return positions


def _pillar_labels(chart: BirthChartResult) -> dict[str, str]:
    labels = {
        "year": chart.year_pillar.label,
        "month": chart.month_pillar.label,
        "day": chart.day_pillar.label,
    }
    if not _birth_time_unknown(chart):
        labels["hour"] = chart.hour_pillar.label
    return labels


def _domains_for_positions(positions: list[str], primary_domain: str) -> list[str]:
    domains: list[str] = [primary_domain]
    for position in positions:
        domains.extend(POSITION_DOMAINS.get(position, ()))
    return list(dict.fromkeys(domains))


def _intensity_for_positions(positions: list[str], *, base: str = "support") -> str:
    if not positions:
        return "reference"
    if "month" in positions or "day" in positions:
        return "moderate"
    if len(positions) >= 2:
        return "moderate"
    if base == "strong_single":
        return "moderate"
    return "low"


def _make_misc_signal(
    key: str,
    formula_name: str,
    positions: list[str],
    pillar_labels: dict[str, str],
    *,
    intensity: str | None = None,
    extra_basis: list[str] | None = None,
) -> AuxiliaryMiscSignal:
    label, grade, lineage, meaning, caution, primary_domain = MISC_SHINSAL_META[key]
    clean_positions = list(dict.fromkeys(positions))
    allowed_use = "내부 참고" if "D" in grade else "보조 해설"
    return AuxiliaryMiscSignal(
        key=key,
        label=label,
        grade=grade,
        lineage=lineage,
        formula_name=formula_name,
        positions=clean_positions,
        pillar_labels=[pillar_labels[position] for position in clean_positions if position in pillar_labels],
        domains=_domains_for_positions(clean_positions, primary_domain),
        intensity=intensity or _intensity_for_positions(clean_positions),
        allowed_use=allowed_use,
        meaning=meaning,
        caution=caution,
        basis_codes=[f"misc_shinsal:{key}", f"formula:{formula_name}", *(extra_basis or [])],
    )


def _make_twelve_shinsal_signal(
    key: str,
    formula_name: str,
    positions: list[str],
    pillar_labels: dict[str, str],
    *,
    extra_basis: list[str],
) -> AuxiliaryMiscSignal:
    clean_positions = list(dict.fromkeys(positions))
    return AuxiliaryMiscSignal(
        key=key,
        label=TWELVE_SINSAL_LABELS[key],
        grade="B",
        lineage="12신살",
        formula_name=formula_name,
        positions=clean_positions,
        pillar_labels=[pillar_labels[position] for position in clean_positions if position in pillar_labels],
        domains=list(TWELVE_SINSAL_DOMAINS.get(key, [])),
        intensity=_intensity_for_positions(clean_positions),
        allowed_use="근거 전용",
        meaning=TWELVE_SINSAL_MEANINGS[key],
        caution="12신살은 월령·격국·십신의 본체 판단을 대신하지 않습니다.",
        basis_codes=[f"twelve_shinsal:{key}", f"formula:{formula_name}", *extra_basis],
    )


def _build_twelve_shinsal_signals(
    chart: BirthChartResult,
    day_sal_by_position: dict[str, list[str]],
    year_sal_by_position: dict[str, list[str]],
) -> list[AuxiliaryMiscSignal]:
    labels = _pillar_labels(chart)
    signals: list[AuxiliaryMiscSignal] = []
    for key in TWELVE_SINSAL_ORDER:
        day_positions = [position for position, values in day_sal_by_position.items() if key in values]
        if day_positions:
            signals.append(
                _make_twelve_shinsal_signal(
                    key,
                    "day_branch_group_twelve_shinsal",
                    day_positions,
                    labels,
                    extra_basis=[f"reference_branch:day:{chart.day_pillar.branch_key}"],
                )
            )
        year_positions = [position for position, values in year_sal_by_position.items() if key in values]
        if year_positions:
            signals.append(
                _make_twelve_shinsal_signal(
                    key,
                    "year_branch_group_twelve_shinsal",
                    year_positions,
                    labels,
                    extra_basis=[f"reference_branch:year:{chart.year_pillar.branch_key}"],
                )
            )
    return signals


def _positions_matching_branch(branch_positions: dict[str, str], targets: set[str]) -> list[str]:
    return [position for position, branch in branch_positions.items() if branch in targets]


def _positions_matching_stem(stem_positions: dict[str, str], targets: set[str]) -> list[str]:
    return [position for position, stem in stem_positions.items() if stem in targets]


def _append_branch_rule(
    signals: list[AuxiliaryMiscSignal],
    key: str,
    formula_name: str,
    target_branches: set[str],
    branch_positions: dict[str, str],
    pillar_labels: dict[str, str],
    *,
    extra_basis: list[str] | None = None,
) -> None:
    positions = _positions_matching_branch(branch_positions, target_branches)
    if positions:
        signals.append(_make_misc_signal(key, formula_name, positions, pillar_labels, extra_basis=extra_basis))


def _append_stem_or_branch_rule(
    signals: list[AuxiliaryMiscSignal],
    key: str,
    formula_name: str,
    target_kind: str,
    target_key: str,
    stem_positions: dict[str, str],
    branch_positions: dict[str, str],
    pillar_labels: dict[str, str],
) -> None:
    if target_kind == "stem":
        positions = _positions_matching_stem(stem_positions, {target_key})
    else:
        positions = _positions_matching_branch(branch_positions, {target_key})
    if positions:
        signals.append(_make_misc_signal(key, formula_name, positions, pillar_labels))


def _month_group(month_branch_key: str) -> str:
    for branches, group_name in (
        ({"in", "o", "sul"}, "fire_group"),
        ({"hae", "myo", "mi"}, "wood_group"),
        ({"sin", "ja", "jin"}, "water_group"),
        ({"sa", "yu", "chuk"}, "metal_group"),
    ):
        if month_branch_key in branches:
            return group_name
    return "unknown_group"


def _year_direction_group(year_branch_key: str) -> dict[str, str]:
    for branches, rule in GOJIN_GWASUK_BY_YEAR_GROUP.items():
        if year_branch_key in branches:
            return rule
    return {}


def _gongmang_targets(day_pillar_index: int) -> tuple[str, set[str]]:
    return GONGMANG_BRANCHES_BY_SUN[day_pillar_index // 10]


def _append_pair_signals(
    signals: list[AuxiliaryMiscSignal],
    key: str,
    formula_name: str,
    pair_rules: set[frozenset[str]],
    branch_positions: dict[str, str],
    pillar_labels: dict[str, str],
) -> None:
    matched_position_groups: list[list[str]] = []
    for left, right in combinations(branch_positions.items(), 2):
        left_position, left_branch = left
        right_position, right_branch = right
        if frozenset((left_branch, right_branch)) in pair_rules:
            matched_position_groups.append([left_position, right_position])
    if not matched_position_groups:
        return
    positions: list[str] = []
    has_adjacent = False
    adjacent_pairs = {("year", "month"), ("month", "day"), ("day", "hour")}
    for group in matched_position_groups:
        positions.extend(group)
        if tuple(group) in adjacent_pairs:
            has_adjacent = True
    intensity = "moderate" if has_adjacent or "day" in positions else "low"
    signals.append(
        _make_misc_signal(
            key,
            formula_name,
            positions,
            pillar_labels,
            intensity=intensity,
            extra_basis=[f"pair_count:{len(matched_position_groups)}"],
        )
    )


def _build_misc_shinsal_signals(chart: BirthChartResult) -> list[AuxiliaryMiscSignal]:
    branch_positions = _pillars(chart)
    stem_positions = _stem_positions(chart)
    pillar_labels = _pillar_labels(chart)
    day_stem = chart.day_pillar.stem_key
    year_stem = chart.year_pillar.stem_key
    year_branch = chart.year_pillar.branch_key
    month_branch = chart.month_pillar.branch_key
    day_pillar_label = chart.day_pillar.label
    signals: list[AuxiliaryMiscSignal] = []

    _append_branch_rule(signals, "lugod", "day_stem_lugod", {LUGOD_BRANCH_BY_DAY_STEM[day_stem]}, branch_positions, pillar_labels)
    _append_branch_rule(signals, "geumyeo", "day_stem_geumyeo", {GEUMYEO_BRANCH_BY_DAY_STEM[day_stem]}, branch_positions, pillar_labels)
    _append_branch_rule(
        signals,
        "cheoneul_day",
        "day_stem_cheoneul",
        CHEONEUL_BRANCHES_BY_STEM[day_stem],
        branch_positions,
        pillar_labels,
    )
    _append_branch_rule(
        signals,
        "cheoneul_year",
        "year_stem_cheoneul",
        CHEONEUL_BRANCHES_BY_STEM[year_stem],
        branch_positions,
        pillar_labels,
    )

    target_kind, target_key = CHEONDEOK_TARGET_BY_MONTH_BRANCH[month_branch]
    _append_stem_or_branch_rule(
        signals,
        "cheondeok",
        "month_branch_cheondeok",
        target_kind,
        target_key,
        stem_positions,
        branch_positions,
        pillar_labels,
    )
    woldeok_stem = WOLDEOK_STEM_BY_MONTH_GROUP.get(_month_group(month_branch))
    if woldeok_stem:
        _append_stem_or_branch_rule(
            signals,
            "woldeok",
            "month_group_woldeok",
            "stem",
            woldeok_stem,
            stem_positions,
            branch_positions,
            pillar_labels,
        )

    _append_branch_rule(signals, "taegeuk", "day_stem_taegeuk", TAEGEUK_BRANCHES_BY_STEM[day_stem], branch_positions, pillar_labels)
    _append_branch_rule(
        signals,
        "moonchang_modern",
        "day_stem_moonchang_modern",
        {MOONCHANG_MODERN_BRANCH_BY_DAY_STEM[day_stem]},
        branch_positions,
        pillar_labels,
    )
    _append_branch_rule(
        signals,
        "moonchang_classic",
        "day_stem_moonchang_classic_ohangjeonggi",
        {MOONCHANG_CLASSIC_BRANCH_BY_DAY_STEM[day_stem]},
        branch_positions,
        pillar_labels,
    )
    _append_branch_rule(signals, "hakdang", "day_stem_hakdang_sagwan", HAKDANG_BRANCHES_BY_DAY_STEM[day_stem], branch_positions, pillar_labels)
    _append_branch_rule(signals, "gukin", "day_stem_gukin", {GUKIN_BRANCH_BY_DAY_STEM[day_stem]}, branch_positions, pillar_labels)

    for key, target_branch in HONGLAN_CHEONHUI_BY_YEAR_BRANCH[year_branch].items():
        _append_branch_rule(signals, key, f"year_branch_{key}", {target_branch}, branch_positions, pillar_labels)

    if day_stem in YANGIN_STRICT_BRANCH_BY_DAY_STEM:
        _append_branch_rule(
            signals,
            "yangin_strict",
            "day_stem_yangin_strict",
            {YANGIN_STRICT_BRANCH_BY_DAY_STEM[day_stem]},
            branch_positions,
            pillar_labels,
        )
    if day_stem in YANGIN_EXPANDED_BRANCH_BY_DAY_STEM:
        _append_branch_rule(
            signals,
            "yangin_expanded",
            "day_stem_yangin_expanded_yin",
            {YANGIN_EXPANDED_BRANCH_BY_DAY_STEM[day_stem]},
            branch_positions,
            pillar_labels,
        )

    gongmang_formula, gongmang_branches = _gongmang_targets(chart.day_pillar.sexagenary_index)
    _append_branch_rule(
        signals,
        "gongmang",
        f"day_pillar_{gongmang_formula}",
        gongmang_branches,
        branch_positions,
        pillar_labels,
    )

    gojin_gwasuk = _year_direction_group(year_branch)
    for key, target_branch in gojin_gwasuk.items():
        _append_branch_rule(signals, key, f"year_branch_direction_{key}", {target_branch}, branch_positions, pillar_labels)

    _append_branch_rule(signals, "cheonra", "branch_fixed_cheonra", {"sul", "hae"}, branch_positions, pillar_labels)
    _append_branch_rule(signals, "jimang", "branch_fixed_jimang", {"jin", "sa"}, branch_positions, pillar_labels)

    for key, day_pillars in (
        ("sipak_daepae", SIPAK_DAEPAE_DAY_PILLARS),
        ("eumyang_chachak", EUMYANG_CHACHAK_DAY_PILLARS),
        ("goegang", GOEGANG_DAY_PILLARS),
        ("baekho", BAEKHO_DAY_PILLARS),
        ("goran", GORAN_DAY_PILLARS),
        ("paljeon", PALJEON_DAY_PILLARS),
        ("guchu", GUCHU_DAY_PILLARS),
    ):
        if day_pillar_label in day_pillars:
            signals.append(
                _make_misc_signal(
                    key,
                    f"day_pillar_{key}",
                    ["day"],
                    pillar_labels,
                    intensity="moderate",
                    extra_basis=[f"day_pillar:{day_pillar_label}"],
                )
            )

    _append_branch_rule(signals, "hongyeom", "day_stem_hongyeom", {HONGYEOM_BRANCH_BY_DAY_STEM[day_stem]}, branch_positions, pillar_labels)
    _append_pair_signals(signals, "gwimun", "branch_pair_gwimun_any_positions", GWIMUN_PAIRS, branch_positions, pillar_labels)
    _append_pair_signals(signals, "wonjin", "branch_pair_wonjin_korean", WONJIN_PAIRS, branch_positions, pillar_labels)

    hyeonchim_positions = _positions_matching_stem(stem_positions, HYEONCHIM_STEMS)
    hyeonchim_positions.extend(_positions_matching_branch(branch_positions, HYEONCHIM_BRANCHES))
    if hyeonchim_positions:
        signals.append(_make_misc_signal("hyeonchim", "stem_branch_shape_hyeonchim", hyeonchim_positions, pillar_labels))

    cheolshoe_positions = _positions_matching_branch(branch_positions, CHEOLSHOE_BRANCHES)
    if set(branch_positions[position] for position in cheolshoe_positions) == CHEOLSHOE_BRANCHES:
        signals.append(
            _make_misc_signal(
                "cheolshoe",
                "myo_yu_sul_full_cheolshoe",
                cheolshoe_positions,
                pillar_labels,
                intensity="moderate",
                extra_basis=["full_set:myo_yu_sul"],
            )
        )
    elif len({branch_positions[position] for position in cheolshoe_positions}) >= 2 and "day" in cheolshoe_positions:
        signals.append(
            _make_misc_signal(
                "cheolshoe",
                "myo_yu_sul_partial_day_included",
                cheolshoe_positions,
                pillar_labels,
                intensity="low",
                extra_basis=["partial_set_with_day"],
            )
        )

    _append_branch_rule(signals, "cheonmun", "branch_sul_hae_cheonmun", {"sul", "hae"}, branch_positions, pillar_labels)

    deduped: dict[tuple[str, str, tuple[str, ...]], AuxiliaryMiscSignal] = {}
    for signal in signals:
        deduped[(signal.key, signal.formula_name, tuple(signal.positions))] = signal
    return list(deduped.values())


def _annual_structure_positions(structure: Any) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    position_signals = getattr(structure, "position_signals", {}) or {}
    branch_positions: dict[str, str] = {}
    stem_positions: dict[str, str] = {}
    for position, signal in position_signals.items():
        branch_key = str(getattr(signal, "branch_key", "") or "")
        stem_key = str(getattr(signal, "stem_key", "") or "")
        if branch_key:
            branch_positions[str(position)] = branch_key
        if stem_key:
            stem_positions[str(position)] = stem_key
    pillar_labels = {
        str(position): str(label)
        for position, label in dict(getattr(structure, "four_pillars", {}) or {}).items()
        if str(label)
    }
    return branch_positions, stem_positions, pillar_labels


def _sexagenary_index_from_keys(stem_key: str, branch_key: str) -> int:
    stem_order = ("gap", "eul", "byeong", "jeong", "mu", "gi", "gyeong", "sin", "im", "gye")
    branch_order = ("ja", "chuk", "in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae")
    try:
        stem_index = stem_order.index(stem_key)
        branch_index = branch_order.index(branch_key)
    except ValueError:
        return 0
    for index in range(60):
        if index % 10 == stem_index and index % 12 == branch_index:
            return index
    return 0


def build_annual_shinsal_signals(
    structure: Any,
    target_years: Iterable[int],
) -> list[AuxiliaryMiscSignal]:
    """Calculate annual auxiliary activations without feeding metric scores.

    The returned signals are evidence-only observations. They intentionally do
    not enter any domain score, metric keyword selector, or annual total.
    """

    branch_positions, stem_positions, pillar_labels = _annual_structure_positions(structure)
    if not branch_positions or not stem_positions:
        return []
    day_signal = (getattr(structure, "position_signals", {}) or {}).get("day")
    year_signal = (getattr(structure, "position_signals", {}) or {}).get("year")
    month_signal = (getattr(structure, "position_signals", {}) or {}).get("month")
    day_stem = str(getattr(day_signal, "stem_key", "") or getattr(structure, "day_master_stem", "") or "")
    day_branch = str(getattr(day_signal, "branch_key", "") or "")
    year_stem = str(getattr(year_signal, "stem_key", "") or "")
    year_branch = str(getattr(year_signal, "branch_key", "") or "")
    month_branch = str(getattr(month_signal, "branch_key", "") or getattr(structure, "month_branch", "") or "")
    day_pillar_index = _sexagenary_index_from_keys(day_stem, day_branch)
    signals: list[AuxiliaryMiscSignal] = []

    def append_misc(
        key: str,
        formula_name: str,
        positions: list[str],
        labels: dict[str, str],
        year: int,
        *,
        extra_basis: list[str] | None = None,
        intensity: str = "moderate",
    ) -> None:
        signals.append(
            _make_misc_signal(
                key,
                formula_name,
                positions,
                labels,
                intensity=intensity,
                extra_basis=[
                    f"target_year:{year}",
                    "exposure_scope:comprehensive_basis_only",
                    *(extra_basis or []),
                ],
            )
        )

    for raw_year in target_years:
        year = int(raw_year)
        pillar = year_pillar_for_gregorian_year(year)
        annual_position = f"annual_{year}"
        labels = dict(pillar_labels)
        labels[annual_position] = f"{year}년 {pillar.label}"

        for reference_name, reference_branch in (("day", day_branch), ("year", year_branch)):
            _, targets = _group_and_targets(reference_branch)
            for key in TWELVE_SINSAL_ORDER:
                if targets.get(key) != pillar.branch_key:
                    continue
                signals.append(
                    _make_twelve_shinsal_signal(
                        key,
                        f"annual_{reference_name}_branch_group_twelve_shinsal",
                        [annual_position],
                        labels,
                        extra_basis=[
                            f"target_year:{year}",
                            f"reference_branch:{reference_name}:{reference_branch}",
                            "exposure_scope:comprehensive_basis_only",
                        ],
                    )
                )

        def branch_hit(key: str, formula_name: str, targets: set[str], *, extra_basis: list[str] | None = None) -> None:
            if pillar.branch_key in targets:
                append_misc(key, formula_name, [annual_position], labels, year, extra_basis=extra_basis)

        def stem_hit(key: str, formula_name: str, target: str) -> None:
            if pillar.stem_key == target:
                append_misc(key, formula_name, [annual_position], labels, year)

        if day_stem in LUGOD_BRANCH_BY_DAY_STEM:
            branch_hit("lugod", "annual_day_stem_lugod", {LUGOD_BRANCH_BY_DAY_STEM[day_stem]})
            branch_hit("geumyeo", "annual_day_stem_geumyeo", {GEUMYEO_BRANCH_BY_DAY_STEM[day_stem]})
            branch_hit("cheoneul_day", "annual_day_stem_cheoneul", CHEONEUL_BRANCHES_BY_STEM[day_stem])
            branch_hit("taegeuk", "annual_day_stem_taegeuk", TAEGEUK_BRANCHES_BY_STEM[day_stem])
            branch_hit("moonchang_modern", "annual_day_stem_moonchang_modern", {MOONCHANG_MODERN_BRANCH_BY_DAY_STEM[day_stem]})
            branch_hit("moonchang_classic", "annual_day_stem_moonchang_classic_ohangjeonggi", {MOONCHANG_CLASSIC_BRANCH_BY_DAY_STEM[day_stem]})
            branch_hit("hakdang", "annual_day_stem_hakdang_sagwan", HAKDANG_BRANCHES_BY_DAY_STEM[day_stem])
            branch_hit("gukin", "annual_day_stem_gukin", {GUKIN_BRANCH_BY_DAY_STEM[day_stem]})
            branch_hit("hongyeom", "annual_day_stem_hongyeom", {HONGYEOM_BRANCH_BY_DAY_STEM[day_stem]})
        if year_stem in CHEONEUL_BRANCHES_BY_STEM:
            branch_hit("cheoneul_year", "annual_year_stem_cheoneul", CHEONEUL_BRANCHES_BY_STEM[year_stem])

        if month_branch in CHEONDEOK_TARGET_BY_MONTH_BRANCH:
            target_kind, target_key = CHEONDEOK_TARGET_BY_MONTH_BRANCH[month_branch]
            if (target_kind == "stem" and pillar.stem_key == target_key) or (
                target_kind == "branch" and pillar.branch_key == target_key
            ):
                append_misc("cheondeok", "annual_month_branch_cheondeok", [annual_position], labels, year)
        woldeok_stem = WOLDEOK_STEM_BY_MONTH_GROUP.get(_month_group(month_branch))
        if woldeok_stem:
            stem_hit("woldeok", "annual_month_group_woldeok", woldeok_stem)

        for key, target_branch in HONGLAN_CHEONHUI_BY_YEAR_BRANCH.get(year_branch, {}).items():
            branch_hit(key, f"annual_year_branch_{key}", {target_branch})
        if day_stem in YANGIN_STRICT_BRANCH_BY_DAY_STEM:
            branch_hit("yangin_strict", "annual_day_stem_yangin_strict", {YANGIN_STRICT_BRANCH_BY_DAY_STEM[day_stem]})
        if day_stem in YANGIN_EXPANDED_BRANCH_BY_DAY_STEM:
            branch_hit("yangin_expanded", "annual_day_stem_yangin_expanded_yin", {YANGIN_EXPANDED_BRANCH_BY_DAY_STEM[day_stem]})

        gongmang_formula, gongmang_branches = _gongmang_targets(day_pillar_index)
        branch_hit("gongmang", f"annual_day_pillar_{gongmang_formula}", gongmang_branches)
        for key, target_branch in _year_direction_group(year_branch).items():
            branch_hit(key, f"annual_year_branch_direction_{key}", {target_branch})
        branch_hit("cheonra", "annual_branch_fixed_cheonra", {"sul", "hae"})
        branch_hit("jimang", "annual_branch_fixed_jimang", {"jin", "sa"})
        branch_hit("cheonmun", "annual_branch_sul_hae_cheonmun", {"sul", "hae"})

        for key, pair_rules in (("gwimun", GWIMUN_PAIRS), ("wonjin", WONJIN_PAIRS)):
            for natal_position, natal_branch in branch_positions.items():
                if frozenset((natal_branch, pillar.branch_key)) in pair_rules:
                    append_misc(
                        key,
                        f"annual_branch_pair_{key}",
                        [natal_position, annual_position],
                        labels,
                        year,
                        extra_basis=[f"natal_position:{natal_position}", f"branch_pair:{natal_branch}:{pillar.branch_key}"],
                    )

        if pillar.stem_key in HYEONCHIM_STEMS or pillar.branch_key in HYEONCHIM_BRANCHES:
            append_misc("hyeonchim", "annual_stem_branch_shape_hyeonchim", [annual_position], labels, year)

        combined_cheolshoe = set(branch_positions.values()) | {pillar.branch_key}
        if CHEOLSHOE_BRANCHES.issubset(combined_cheolshoe):
            matched_positions = [
                position for position, branch in branch_positions.items() if branch in CHEOLSHOE_BRANCHES
            ]
            matched_positions.append(annual_position)
            append_misc(
                "cheolshoe",
                "annual_myo_yu_sul_full_cheolshoe",
                list(dict.fromkeys(matched_positions)),
                labels,
                year,
                extra_basis=["full_set:myo_yu_sul", "promotion_candidate:safe_misc"],
            )

    deduped: dict[tuple[str, str, tuple[str, ...], tuple[str, ...]], AuxiliaryMiscSignal] = {}
    for signal in signals:
        deduped[
            (
                signal.key,
                signal.formula_name,
                tuple(signal.positions),
                tuple(signal.basis_codes),
            )
        ] = signal
    return list(deduped.values())


def build_auxiliary_profile(chart: BirthChartResult) -> AuxiliaryProfile:
    day_stem_key = chart.day_pillar.stem_key
    year_branch_key = chart.year_pillar.branch_key
    day_branch_key = chart.day_pillar.branch_key
    positions = _pillars(chart)
    twelve_growth_by_position = {
        position: growth_stage(day_stem_key, branch_key)
        for position, branch_key in positions.items()
    }

    day_group_name, day_sal_targets = _group_and_targets(day_branch_key)
    year_group_name, year_sal_targets = _group_and_targets(year_branch_key)
    day_sal_by_position = _sal_by_position(positions, day_sal_targets)
    year_sal_by_position = _sal_by_position(positions, year_sal_targets)

    return AuxiliaryProfile(
        twelve_growth_by_position=twelve_growth_by_position,
        sal_by_position=day_sal_by_position,
        day_branch_group=day_group_name,
        year_branch_group=year_group_name,
        day_sal_by_position=day_sal_by_position,
        year_sal_by_position=year_sal_by_position,
        twelve_shinsal_signals=_build_twelve_shinsal_signals(
            chart,
            day_sal_by_position,
            year_sal_by_position,
        ),
        misc_shinsal_signals=_build_misc_shinsal_signals(chart),
    )
