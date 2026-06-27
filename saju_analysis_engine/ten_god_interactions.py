"""Directional ten-god interpretation rules.

This layer keeps the difference between "two ten-gods are present" and
"one ten-god sees another ten-god". The current implementation is the first
systematic rule table built from the supplied ten-god documents.
"""

from __future__ import annotations

from itertools import permutations
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import BRANCH_HIDDEN_STEMS, POSITION_BRANCH_WEIGHTS, POSITION_STEM_WEIGHTS, TEN_GOD_GROUPS
from .models import PositionSignal, TenGodInteractionProfile, TenGodInteractionSignal
from .ten_gods import main_hidden_stem, ten_god_for


POSITION_ORDER = ("year", "month", "day", "hour")
TEN_GOD_ORDER = (
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
)
SERVICE_DOMAINS = ("money", "career", "love", "marriage")

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

POSITION_LABELS = {
    "year": "연주",
    "month": "월주",
    "day": "일주",
    "hour": "시주",
}

TEN_GOD_SUBJECT_PARTICLE = {
    "bi_gyeon": "이",
    "geob_jae": "가",
    "sik_sin": "이",
    "sang_gwan": "이",
    "pyeon_jae": "가",
    "jeong_jae": "가",
    "pyeon_gwan": "이",
    "jeong_gwan": "이",
    "pyeon_in": "이",
    "jeong_in": "이",
}

TEN_GOD_OBJECT_PARTICLE = {
    "bi_gyeon": "을",
    "geob_jae": "를",
    "sik_sin": "을",
    "sang_gwan": "을",
    "pyeon_jae": "를",
    "jeong_jae": "를",
    "pyeon_gwan": "을",
    "jeong_gwan": "을",
    "pyeon_in": "을",
    "jeong_in": "을",
}


def _base(
    core: str,
    desire: str,
    talent: str,
    risk: str,
    domains: list[str],
) -> dict[str, Any]:
    return {
        "core": core,
        "desire": desire,
        "talent": talent,
        "risk": risk,
        "domain_links": domains,
    }


TEN_GOD_BASE_RULES: dict[str, dict[str, Any]] = {
    "bi_gyeon": _base(
        "나와 같은 사람을 확인하고, 내 사람과 함께 서려는 기준입니다.",
        "동등한 관계, 내 편, 공동체 안의 안정감을 원합니다.",
        "협업, 결속, 동료 의식, 공동 책임을 세웁니다.",
        "상대가 나와 다르다는 사실을 늦게 인정하면 배신감과 간섭이 커집니다.",
        ["career", "money", "love", "marriage"],
    ),
    "geob_jae": _base(
        "상대와 내가 다르다는 사실을 먼저 인식하고 이해관계를 조정하는 기준입니다.",
        "비교 우위, 실속, 경쟁 속 생존을 원합니다.",
        "대중 이해, 경쟁 적응, 사람 활용, 이해관계 조절에 강합니다.",
        "계약과 기준이 약하면 탈취, 도용, 무리한 양보로 기울 수 있습니다.",
        ["money", "career"],
    ),
    "sik_sin": _base(
        "자기 경험과 반복된 실행에서 만들어진 고유 능력입니다.",
        "내 손으로 해내고, 내 몫을 수행하며, 꾸준히 살아내기를 원합니다.",
        "실무, 생산, 생활력, 현장 경험, 장기 지속성을 만듭니다.",
        "근과 조력이 약하면 과로하거나 남에게 쓰이는 위치가 되기 쉽습니다.",
        ["money", "career", "marriage"],
    ),
    "sang_gwan": _base(
        "주변 상황을 읽고 쓸 만한 요소를 골라 활용하는 표현 능력입니다.",
        "빠른 성과, 효율, 자유로운 발언, 기존 질서의 검증을 원합니다.",
        "마케팅, 설득, 비판, 분석, 서비스, 상황 활용에 강합니다.",
        "자격과 제어가 약하면 말로 인한 손상, 도용, 권위 충돌이 커집니다.",
        ["money", "career", "love"],
    ),
    "pyeon_jae": _base(
        "외부 기회와 대외 관계에서 미래 가능성을 찾는 기준입니다.",
        "확장, 교류, 투자, 재미, 사람을 끌어들이는 일을 원합니다.",
        "영업, 대외 협상, 사업 확장, 기회 포착, 사교성을 만듭니다.",
        "범위를 크게 잡으면 책임과 위험도 같이 커집니다.",
        ["money", "career", "love"],
    ),
    "jeong_jae": _base(
        "내 것과 남의 것, 내 역할과 타인의 역할을 구분하는 관리 기준입니다.",
        "안정, 소유, 예측 가능한 생활, 책임 범위의 명확성을 원합니다.",
        "재무 관리, 실무 조정, 계약, 생활 기반 유지, 책임감을 세웁니다.",
        "범위를 좁게 정하면 확장과 변화 앞에서 소극적으로 굳어질 수 있습니다.",
        ["money", "career", "marriage"],
    ),
    "pyeon_gwan": _base(
        "외부에서 갑자기 주어지는 압박, 임무, 강제 상황을 뜻합니다.",
        "위기 해결, 결단, 도전, 수직적 책임 수행을 요구합니다.",
        "결단력, 위기 대응, 강한 추진력, 비상 상황 적응력을 만듭니다.",
        "일간의 힘과 조력이 약하면 압박을 버티느라 소모가 커집니다.",
        ["career", "marriage"],
    ),
    "jeong_gwan": _base(
        "사회가 인정하는 규칙과 직위를 중시합니다. 명분과 평판도 엄격하게 봅니다.",
        "질서, 신뢰, 공적 인정, 안정된 역할을 원합니다.",
        "조직 적응, 평판 관리, 원칙, 공적 책임, 직업 안정성을 세웁니다.",
        "지나치게 고정되면 자유로운 표현과 변화를 다루기 어렵습니다.",
        ["career", "marriage"],
    ),
    "pyeon_in": _base(
        "비공식적이고 직관적인 이해, 특수 분야의 몰입을 뜻합니다.",
        "나만의 해석, 심층 관심, 내면의 독립성을 원합니다.",
        "직관, 심리 이해, 특수 지식, 창작, 위기 속 융통성을 만듭니다.",
        "현실 검증이 약하면 고립, 자기모순, 실행 지연이 커집니다.",
        ["career", "love"],
    ),
    "jeong_in": _base(
        "외부에서 인정받은 지식, 자격, 보호, 정통성을 뜻합니다.",
        "갖춰짐, 품위, 공인된 자격, 안정된 보호를 원합니다.",
        "학습, 자격 취득, 문서화, 코칭, 제도 안의 설득력을 만듭니다.",
        "현실 적용이 약하면 유지에 머무르고 실행력이 낮아집니다.",
        ["career", "money", "marriage"],
    ),
}


def _rule(
    keywords: list[str],
    interpretation: str,
    domains: list[str],
    counters: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "trait_keywords": keywords,
        "interpretation": interpretation,
        "domain_links": domains,
        "counter_signals": counters or [],
    }


TEN_GOD_DIRECTION_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("bi_gyeon", "bi_gyeon"): _rule(["동질 집단", "동료 의식", "간섭"], "비견이 비견을 보면 나와 같은 사람을 다시 확인합니다. 내 편을 소중히 여기지만, 서로의 몫과 경계가 흐려지면 간섭과 경쟁이 생깁니다.", ["career", "love"]),
    ("bi_gyeon", "geob_jae"): _rule(["내외 구분", "이해관계", "비교"], "비견이 겁재를 보면 내 사람 안에서도 서로 다른 이해관계가 있다는 사실을 배웁니다. 친밀함만으로 관계를 유지하기보다 역할과 몫을 정해야 안정됩니다.", ["money", "career"], ["ten_god_peer_boundary_caution"]),
    ("bi_gyeon", "sik_sin"): _rule(["협업", "생활력", "장기 활동"], "비견이 식신을 보면 동료, 친구, 가족과 함께 일을 도모합니다. 오래 해온 일이나 생활 기술이 공동 작업으로 발전하기 쉽습니다.", ["money", "career", "marriage"]),
    ("bi_gyeon", "sang_gwan"): _rule(["내부 토론", "아이디어", "집단 발언"], "비견이 상관을 보면 내 사람들끼리 의견을 내고 활동 방향을 정합니다. 내부 협의는 활발하지만 외부 검증이 약하면 수고가 늘어납니다.", ["career", "money"]),
    ("bi_gyeon", "pyeon_jae"): _rule(["동반 확장", "투자 동료", "지분"], "비견이 편재를 보면 미래 가능성을 혼자 보지 않고 동반자와 함께 키웁니다. 설득과 협업에는 좋지만 지분과 책임을 처음부터 정해야 합니다.", ["money", "career"]),
    ("bi_gyeon", "jeong_jae"): _rule(["공동 분배", "생활 기반", "공유"], "비견이 정재를 보면 내부 소유와 생활 기반을 나누어야 합니다. 가족, 동료, 배우자와 돈과 책임을 공유하는 양상이 강해집니다.", ["money", "marriage"], ["ten_god_shared_wealth_caution"]),
    ("bi_gyeon", "pyeon_gwan"): _rule(["위기 연대", "동료애", "강제 상황"], "비견이 편관을 보면 강한 압박이나 돌발 임무를 함께 버티는 동료가 생깁니다. 적과 아군의 구분이 분명해지고 관계의 결속도 강해집니다.", ["career", "marriage"]),
    ("bi_gyeon", "jeong_gwan"): _rule(["공정성", "소속 독립", "규칙 준수"], "비견이 정관을 보면 소속 질서 안에서 동료와 독립적인 역할을 수행합니다. 조직의 기준을 지키되 내부 운영은 자율적으로 정하려 합니다.", ["career", "marriage"]),
    ("bi_gyeon", "pyeon_in"): _rule(["소수 집단", "특수 관심", "동호회"], "비견이 편인을 보면 특수 분야나 비공식 지식을 함께 좋아하는 사람들이 모입니다. 소규모 집단이 깊은 관심사를 바탕으로 사회적 가치를 만들 수 있습니다.", ["career", "love"]),
    ("bi_gyeon", "jeong_in"): _rule(["정규 학습", "동문", "협회"], "비견이 정인을 보면 정규 학문, 자격, 전문 지식 안에서 같은 길을 가는 사람들과 연대합니다. 공부와 준비 과정에서 선후배, 동료, 협회성이 강해집니다.", ["career"]),
    ("geob_jae", "bi_gyeon"): _rule(["비교", "객관화", "내 사람 점검"], "겁재가 비견을 보면 나와 비슷한 사람을 비교 대상으로 삼습니다. 가까운 관계에서도 능력, 대우, 몫의 차이를 예민하게 확인합니다.", ["money", "career", "love"]),
    ("geob_jae", "geob_jae"): _rule(["경쟁 반복", "이해관계", "실속"], "겁재가 겁재를 보면 서로 다른 욕구와 경쟁 의식이 겹칩니다. 실속을 챙기는 감각은 강하지만 약속과 기준이 없으면 피로가 커집니다.", ["money", "career"], ["ten_god_peer_competition_caution"]),
    ("geob_jae", "sik_sin"): _rule(["설득 리더십", "자기 결론", "분업"], "겁재가 식신을 보면 서로 다른 사람들을 자기 결론 쪽으로 이끌려 합니다. 역할을 나누고 일을 진행하는 힘이 있지만 독단으로 보이지 않게 해야 합니다.", ["career", "money"]),
    ("geob_jae", "sang_gwan"): _rule(["사람 활용", "정보 수집", "시장 감각"], "겁재가 상관을 보면 사람, 정보, 기술을 관찰해 쓸 수 있는 요소로 바꿉니다. 영업과 응용력은 강하지만 출처와 권리를 분명히 해야 합니다.", ["money", "career"], ["ten_god_appropriation_caution"]),
    ("geob_jae", "pyeon_jae"): _rule(["과열 기회", "투자 경쟁", "불확실성"], "겁재가 편재를 보면 매력적인 기회에 여러 사람이 동시에 뛰어듭니다. 큰 수익의 가능성은 있지만 정보 검증과 손실 한계를 정해야 합니다.", ["money"], ["ten_god_overheated_market_caution"]),
    ("geob_jae", "jeong_jae"): _rule(["한정 자원", "양보와 쟁취", "자리 경쟁"], "겁재가 정재를 보면 한정된 돈, 자리, 소유를 두고 경쟁합니다. 근이 약하면 양보가 반복되고, 근이 강하면 취할 것과 포기할 것을 분명히 정합니다.", ["money", "career"], ["ten_god_wealth_competition_caution"]),
    ("geob_jae", "pyeon_gwan"): _rule(["피해 최소화", "압박 적응", "회피 기술"], "겁재가 편관을 보면 이미 주어진 압박 속에서 손해를 줄이는 방법을 찾습니다. 순응과 회피를 섞어 불리한 상황을 관리합니다.", ["career"], ["ten_god_pressure_caution"]),
    ("geob_jae", "jeong_gwan"): _rule(["사회화", "공동체 의무", "책임감"], "겁재가 정관을 보면 개인의 차이가 공동체 규칙 안으로 들어갑니다. '나'보다 '우리'를 우선하며 협응력과 책임감이 커집니다.", ["career", "marriage"]),
    ("geob_jae", "pyeon_in"): _rule(["비공식 통찰", "대중 호기심", "채널"], "겁재가 편인을 보면 특수한 직관과 비공식 지식을 대중에게 전달합니다. 흥미를 끄는 능력은 강하지만 과장과 현혹을 경계해야 합니다.", ["career", "love"], ["ten_god_unverified_claim_caution"]),
    ("geob_jae", "jeong_in"): _rule(["대중 친화 지식", "공인 실력", "강의"], "겁재가 정인을 보면 대중이 인정하는 지식과 자격을 갖추고 사람들에게 풀어냅니다. 전문 지식을 일반인이 이해할 수 있게 바꾸는 힘이 큽니다.", ["career", "money"]),
    ("sik_sin", "bi_gyeon"): _rule(["같이 일함", "분업", "생활 안정"], "식신이 비견을 보면 내가 해오던 일에 같이 일하는 사람이 생깁니다. 생산과 생활 부담을 나누지만 성과도 같이 나누게 됩니다.", ["money", "career", "marriage"]),
    ("sik_sin", "geob_jae"): _rule(["업무 분장", "몫나눔", "다른 목적"], "식신이 겁재를 보면 목적이 다른 사람과도 일을 나누어야 합니다. 역할, 보수, 책임을 문서로 정해야 손실이 줄어듭니다.", ["money", "career"], ["ten_god_distribution_caution"]),
    ("sik_sin", "sik_sin"): _rule(["반복 실행", "생활력", "과로"], "식신이 식신을 보면 꾸준함과 실행력이 반복됩니다. 성실함은 강하지만 몸을 계속 쓰는 구조라 휴식 관리가 될 때 몸의 부담이 줄어듭니다.", ["career", "money"], ["ten_god_overwork_caution"]),
    ("sik_sin", "sang_gwan"): _rule(["현장 개선", "실무 응용", "효율 보완"], "식신이 상관을 보면 오래 해온 일에 효율과 개선 의식이 더해집니다. 현장의 감각을 잃지 않으면서 방법을 바꾸는 힘이 생깁니다.", ["career", "money"]),
    ("sik_sin", "pyeon_jae"): _rule(["고유 능력 확장", "외부 기회", "사업화"], "식신이 편재를 보면 오래 준비한 능력을 바깥 기회와 연결합니다. 자기 기술, 취미, 현장 경험이 사업이나 부수입으로 커질 수 있습니다.", ["money", "career"]),
    ("sik_sin", "jeong_jae"): _rule(["안정 수입", "기술 소득", "꾸준한 관리"], "식신이 정재를 보면 한 분야에서 쌓은 능력으로 안정적인 수입을 만듭니다. 오래 쓰이는 기술, 자격, 실무 기반이 돈으로 연결됩니다.", ["money", "career"]),
    ("sik_sin", "pyeon_gwan"): _rule(["위험 차단", "매뉴얼", "구제"], "식신이 편관을 보면 갑작스러운 위험을 준비된 절차와 실력으로 막습니다. 위기 관리, 법적 대응, 구제 활동에서 명예가 생깁니다.", ["career", "marriage"]),
    ("sik_sin", "jeong_gwan"): _rule(["능력 증명", "공적 책임", "직무 신뢰"], "식신이 정관을 보면 꾸준한 실무 능력이 조직의 책임과 만납니다. 능력으로 직책을 얻고, 맡은 일을 성실히 증명합니다.", ["career"]),
    ("sik_sin", "pyeon_in"): _rule(["행동 검열", "소극성", "생각 과다"], "식신이 편인을 보면 행동을 하기 전에 스스로를 많이 검열합니다. 실행이 줄고 생각이 많아지면 성과가 늦어질 수 있습니다.", ["career", "money"], ["ten_god_indirect_resource_food_block"]),
    ("sik_sin", "jeong_in"): _rule(["자격 취득", "공식 절차", "능력 인정"], "식신이 정인을 보면 자기 행동에 자격과 명분을 붙이려 합니다. 허가, 수료, 자격증, 공식 등록을 통해 능력을 인정받습니다.", ["career", "money"]),
    ("sang_gwan", "bi_gyeon"): _rule(["내부 협의", "동료 발언", "초기 사업"], "상관이 비견을 보면 내부 동료와 의견을 모아 활동합니다. 가까운 사람끼리 시작하므로 시장 검증과 외부 기준을 보강해야 합니다.", ["career", "money"]),
    ("sang_gwan", "geob_jae"): _rule(["소비자 이해", "군중 관리", "도용 주의"], "상관이 겁재를 보면 소비자와 대중의 욕구를 읽는 감각이 커집니다. 영업과 시장 조사는 강하지만 제도적 자격이 약하면 도용 문제가 생길 수 있습니다.", ["money", "career"], ["ten_god_appropriation_caution"]),
    ("sang_gwan", "sik_sin"): _rule(["빠른 활용", "실행 보강", "현장 적용"], "상관이 식신을 보면 주변에서 얻은 방법을 실제 반복 작업으로 바꿉니다. 말과 아이디어가 현장 활동으로 내려옵니다.", ["career", "money"]),
    ("sang_gwan", "sang_gwan"): _rule(["비판 과다", "표현 과열", "분석"], "상관이 상관을 보면 비판과 표현이 강해집니다. 분석력은 좋지만 말의 강도와 대인 피로를 조절해야 합니다.", ["career", "love"], ["ten_god_expression_overheat_caution"]),
    ("sang_gwan", "pyeon_jae"): _rule(["마케팅", "외부 판매", "기회 활용"], "상관이 편재를 보면 시장의 요구를 읽고 빠르게 판매와 홍보로 옮깁니다. 대외 활동과 수익화가 빠르지만 무리한 확장에는 주의해야 합니다.", ["money", "career"]),
    ("sang_gwan", "jeong_jae"): _rule(["목표 수치", "커트라인", "현주소 파악"], "상관이 정재를 보면 목표 수치와 한계를 정하고 그에 맞춰 준비합니다. 시험, 매출, 비용, 안정화 기간처럼 수치가 분명한 일에 강합니다.", ["money", "career"]),
    ("sang_gwan", "pyeon_gwan"): _rule(["즉각 대응", "고발", "감시"], "상관이 편관을 보면 부당한 압박에 즉각 대응합니다. 감사, 고발, 토론, 사회운동의 힘이 있으나 권력과 결탁하면 책임 문제가 커집니다.", ["career", "marriage"], ["ten_god_hurting_officer_risk"]),
    ("sang_gwan", "jeong_gwan"): _rule(["질서 검증", "제도 비판", "자격 필요"], "상관이 정관을 보면 기존 규칙과 권위에 설명을 요구합니다. 자격과 근거가 있으면 감시자가 되고, 없으면 불평으로 비칠 수 있습니다.", ["career", "marriage"], ["ten_god_hurting_officer_risk"]),
    ("sang_gwan", "pyeon_in"): _rule(["자기반성", "직관 표현", "언행 정리"], "상관이 편인을 보면 외부를 향한 말이 내면의 통찰과 만납니다. 표현이 깊어지지만 현실 검증 없이 물질적 욕구만 붙으면 왜곡될 수 있습니다.", ["career", "love"]),
    ("sang_gwan", "jeong_in"): _rule(["공인 발언", "교육", "제도 안 표현"], "상관이 정인을 보면 자유로운 표현이 자격과 격식을 갖춥니다. 교사, 강사, 전문가 발언처럼 사회가 받아들일 수 있는 형태가 됩니다.", ["career"]),
    ("pyeon_jae", "bi_gyeon"): _rule(["동반자", "협상", "설득"], "편재가 비견을 보면 상대를 경쟁자보다 파트너로 받아들입니다. 의견을 나누고 함께 이익을 키우는 협상력이 강합니다.", ["money", "career", "love"]),
    ("pyeon_jae", "geob_jae"): _rule(["확인 절차", "서류", "손실 방지"], "편재가 겁재를 보면 매력적인 기회를 두고 이해관계가 복잡해집니다. 사람을 믿더라도 계약, 서류, 검증을 갖추는 편이 안전합니다.", ["money", "career"], ["ten_god_unseen_loss_caution"]),
    ("pyeon_jae", "sik_sin"): _rule(["자기 비전 실현", "장기 수입", "꾸준한 사업"], "편재가 식신을 보면 외부 기회를 자기만의 방식으로 실현합니다. 꾸준히 해온 분야가 수입 구조로 자리 잡기 쉽습니다.", ["money", "career"]),
    ("pyeon_jae", "sang_gwan"): _rule(["시장 기법", "로드맵", "홍보"], "편재가 상관을 보면 타인의 자료, 예측, 홍보 기법을 활용해 기회를 만듭니다. 변화가 빠른 시장에서 적응력이 강합니다.", ["money", "career"]),
    ("pyeon_jae", "pyeon_jae"): _rule(["기회 확대", "사교성", "리스크"], "편재가 편재를 보면 외부 기회와 대외 관계가 반복됩니다. 사람을 끌어들이는 힘은 크지만 범위가 커질수록 책임도 커집니다.", ["money", "career", "love"], ["ten_god_expansion_risk"]),
    ("pyeon_jae", "jeong_jae"): _rule(["확장과 관리", "수익 정리", "경계 설정"], "편재가 정재를 보면 바깥 기회를 내부 관리 기준으로 정리합니다. 벌 기회를 보면서도 소유, 비용, 책임 범위를 분명히 하려 합니다.", ["money", "career"]),
    ("pyeon_jae", "pyeon_gwan"): _rule(["권한", "대외 리더십", "큰 책임"], "편재가 편관을 보면 미래 비전이 강한 권한과 만납니다. 추진력과 설득력은 크지만 큰 위험에 사람을 이끌 수 있어 체력과 책임 관리가 중요합니다.", ["money", "career"], ["ten_god_high_risk_leadership"]),
    ("pyeon_jae", "jeong_gwan"): _rule(["공식 승인", "조직 프로젝트", "명분"], "편재가 정관을 보면 외부 가능성이 공식 권한을 얻습니다. 개인 아이디어가 조직의 사업이나 공적 프로젝트로 인정받기 쉽습니다.", ["money", "career"]),
    ("pyeon_jae", "pyeon_in"): _rule(["가설", "리스크 관리", "심리 포착"], "편재가 편인을 보면 시장 동향과 사람 심리를 직관적으로 읽습니다. 가설 설정, 데이터 해석, 리스크 관리, 콘텐츠 기획에 강합니다.", ["money", "career"]),
    ("pyeon_jae", "jeong_in"): _rule(["새 규칙", "데이터화", "예측"], "편재가 정인을 보면 외부 가능성을 규칙과 수치로 정리하려 합니다. 새로운 기준, 분석 모델, 예측 가능한 사업 체계를 만들 수 있습니다.", ["money", "career"]),
    ("jeong_jae", "bi_gyeon"): _rule(["공유", "공동 생활", "분배"], "정재가 비견을 보면 내부 자원과 생활 기반을 나누어야 합니다. 공평한 분배와 공동 책임이 중요한 주제가 됩니다.", ["money", "marriage"], ["ten_god_shared_wealth_caution"]),
    ("jeong_jae", "geob_jae"): _rule(["자리 경쟁", "탈취 위험", "치열함"], "정재가 겁재를 보면 내 돈, 자리, 역할을 두고 경쟁이 생깁니다. 실력과 배경이 비교되는 환경에서 자기 몫을 지켜야 합니다.", ["money", "career"], ["ten_god_wealth_competition_caution"]),
    ("jeong_jae", "sik_sin"): _rule(["소유 확충", "꾸준한 기술", "실속"], "정재가 식신을 보면 내가 가진 능력을 꾸준히 키워 소유를 늘립니다. 자격, 기술, 오래 해온 일이 현실 수입으로 쌓입니다.", ["money", "career"]),
    ("jeong_jae", "sang_gwan"): _rule(["환경 적응", "시장 방법", "효율"], "정재가 상관을 보면 처한 환경에서 가장 돈이 되는 방법을 찾습니다. 주변의 성공 사례를 보고 자기 상황에 맞게 적용합니다.", ["money", "career"]),
    ("jeong_jae", "pyeon_jae"): _rule(["관리 밖 기회", "확장 보완", "불안"], "정재가 편재를 보면 안정적으로 관리하던 범위 밖의 기회를 마주합니다. 수익 확장은 가능하지만 소유 경계와 책임을 새로 정해야 합니다.", ["money", "career"]),
    ("jeong_jae", "jeong_jae"): _rule(["관리 반복", "한계 설정", "안정"], "정재가 정재를 보면 소유와 책임의 범위를 반복해서 정리합니다. 안정성은 높지만 스스로 정한 한계 밖으로 나아가기 어렵습니다.", ["money", "marriage"]),
    ("jeong_jae", "pyeon_gwan"): _rule(["과중 책임", "위기 안정화", "번아웃"], "정재가 편관을 보면 자기 자원과 능력 안에서 예측 못한 책임을 감당합니다. 위기 안정화 능력은 뛰어나지만 과중한 책임, 과로와 부담이 큽니다.", ["career", "marriage"], ["ten_god_overburden_caution"]),
    ("jeong_jae", "jeong_gwan"): _rule(["헌신", "조직 안정", "공적 역할"], "정재가 정관을 보면 내 관리 능력으로 조직과 가정을 지키려 합니다. 충성심, 책임감, 안정적 직무 수행이 강해집니다.", ["career", "marriage", "money"]),
    ("jeong_jae", "pyeon_in"): _rule(["현실과 이상", "예술성", "자기모순"], "정재가 편인을 보면 현실 문제를 이상적, 철학적, 예술적으로 해석합니다. 감수성은 깊지만 현실과 이상 사이에서 우울과 갈등이 생길 수 있습니다.", ["career", "love"], ["ten_god_reality_ideal_caution"]),
    ("jeong_jae", "jeong_in"): _rule(["자격화", "문서", "계량화"], "정재가 정인을 보면 실제 활동과 소유를 공식적으로 인정받으려 합니다. 계약, 문서, 자격, 데이터 분석, 자산 운용에 강합니다.", ["money", "career", "marriage"]),
    ("pyeon_gwan", "bi_gyeon"): _rule(["동료애", "강제 임무", "연대"], "편관이 비견을 보면 강한 압박을 함께 견디는 사람이 생깁니다. 단체 대응, 팀 결속, 약자 연대의 성격이 강합니다.", ["career", "marriage"]),
    ("pyeon_gwan", "geob_jae"): _rule(["손해 축소", "긴장", "생존술"], "편관이 겁재를 보면 강제 상황에서 각자의 실속을 조절합니다. 피해를 줄이는 계산이 빠르지만 신뢰 관계는 긴장될 수 있습니다.", ["career"], ["ten_god_pressure_caution"]),
    ("pyeon_gwan", "sik_sin"): _rule(["사전 대비", "규정", "구제"], "편관이 식신을 보면 돌발 압박을 미리 대비한 절차로 다룹니다. 매뉴얼, 규정, 반복 훈련으로 위험을 낮춥니다.", ["career", "marriage"]),
    ("pyeon_gwan", "sang_gwan"): _rule(["즉시 반박", "감시", "개혁"], "편관이 상관을 보면 부당한 명령과 압박이 비판과 정면 대응을 부릅니다. 감사, 고발, 인권, 토론 분야에서 강점이 커집니다.", ["career", "marriage"], ["ten_god_hurting_officer_risk"]),
    ("pyeon_gwan", "pyeon_jae"): _rule(["비전 제시", "투자", "외부 조력"], "편관이 편재를 보면 압박이 큰 일을 외부 조력과 투자로 해결하려 합니다. 대외 관계가 활발하지만 책임의 폭도 커집니다.", ["money", "career"], ["ten_god_high_risk_leadership"]),
    ("pyeon_gwan", "jeong_jae"): _rule(["과중과로", "내부 자원", "질서화"], "편관이 정재를 보면 통제 밖 일을 자기 능력과 내부 자원으로 처리합니다. 무질서를 질서로 바꾸지만 소모가 큽니다.", ["career", "marriage"], ["ten_god_overburden_caution"]),
    ("pyeon_gwan", "pyeon_gwan"): _rule(["강한 압박", "결단 반복", "사건성"], "편관이 편관을 보면 돌발 임무와 강한 결단이 반복됩니다. 리더십은 선명하지만 긴장과 피로가 누적되기 쉽습니다.", ["career"], ["ten_god_pressure_caution"]),
    ("pyeon_gwan", "jeong_gwan"): _rule(["비상과 원칙", "권한 정비", "긴장"], "편관이 정관을 보면 변칙적 상황을 공식 기준으로 정리하려 합니다. 권한은 강해지지만 원칙과 현장 압박 사이의 긴장이 큽니다.", ["career", "marriage"]),
    ("pyeon_gwan", "pyeon_in"): _rule(["전략", "융통성", "위기 처리"], "편관이 편인을 보면 갑작스러운 임무를 유연한 전략으로 처리합니다. 복잡한 일을 빠르게 넘기는 능력이 좋지만 편법 의존은 경계해야 합니다.", ["career"], ["ten_god_shortcut_caution"]),
    ("pyeon_gwan", "jeong_in"): _rule(["체계화", "절차 수행", "느린 완성"], "편관이 정인을 보면 불편한 임무도 정식 절차와 형식으로 처리합니다. 속도는 느려도 완성도와 격식이 생깁니다.", ["career", "marriage"]),
    ("jeong_gwan", "bi_gyeon"): _rule(["허용된 독립", "역할 공간", "공정성"], "정관이 비견을 보면 규칙 안에서 개인의 활동 공간을 보장합니다. 소속되어 있으면서도 각자의 역할을 존중합니다.", ["career", "marriage"]),
    ("jeong_gwan", "geob_jae"): _rule(["사회화", "제어", "규범"], "정관이 겁재를 보면 서로 다른 욕구를 사회 기준 안으로 조정합니다. 규칙이 있어야 대중성과 실속이 안정됩니다.", ["career", "money"]),
    ("jeong_gwan", "sik_sin"): _rule(["직무 수행", "책임 실무", "신뢰"], "정관이 식신을 보면 조직의 책임이 실무 능력으로 수행됩니다. 성실한 일 처리와 신뢰가 직업 안정성을 높입니다.", ["career"]),
    ("jeong_gwan", "sang_gwan"): _rule(["설명 책임", "권위 검증", "갈등"], "정관이 상관을 보면 기존 규칙이 검증과 비판을 받습니다. 제도 개선이 가능하지만 말과 규정의 충돌이 커질 수 있습니다.", ["career", "marriage"], ["ten_god_hurting_officer_risk"]),
    ("jeong_gwan", "pyeon_jae"): _rule(["공식 권한", "명분 있는 확장", "조직 성장"], "정관이 편재를 보면 대외 기회가 공식 명분과 권한을 얻습니다. 조직의 성장 사업, 인허가, 대표 역할로 나타나기 쉽습니다.", ["money", "career"]),
    ("jeong_gwan", "jeong_jae"): _rule(["재생관", "조직 관리", "안정"], "정관이 정재를 보면 관리 능력이 직위와 평판을 지탱합니다. 안정된 조직, 공적 역할, 장기 직무에 적합합니다.", ["career", "money", "marriage"]),
    ("jeong_gwan", "pyeon_gwan"): _rule(["원칙과 비상", "권위 강화", "책임 확대"], "정관이 편관을 보면 정해진 질서가 비상 상황과 만납니다. 책임과 권한이 강해지고, 기준을 더 엄격히 세우게 됩니다.", ["career", "marriage"]),
    ("jeong_gwan", "jeong_gwan"): _rule(["평판", "브랜드", "보수성"], "정관이 정관을 보면 신뢰, 예절, 평판, 직위가 반복 강화됩니다. 안정성은 높지만 지나치게 보수적으로 굳을 수 있습니다.", ["career", "marriage"]),
    ("jeong_gwan", "pyeon_in"): _rule(["비표준 해석", "특수 기준", "내부 예외"], "정관이 편인을 보면 공식 기준 안에 비표준적 해석이 섞입니다. 특수한 판단력은 생기지만 주변에는 낯설게 보일 수 있습니다.", ["career", "love"]),
    ("jeong_gwan", "jeong_in"): _rule(["관인상생", "정통성", "지속성"], "정관이 정인을 보면 책임과 자격이 서로를 지탱합니다. 공직, 교육, 제도권 전문성처럼 오래 가는 직업 안정성이 강합니다.", ["career", "marriage"]),
    ("pyeon_in", "bi_gyeon"): _rule(["특수 공동체", "마니아", "소규모 연대"], "편인이 비견을 보면 특수한 관심사를 공유하는 사람들이 모입니다. 깊은 취미나 비정규 분야가 집단 활동으로 발전합니다.", ["career", "love"]),
    ("pyeon_in", "geob_jae"): _rule(["대중 호기심", "비공식 채널", "통찰 판매"], "편인이 겁재를 보면 특수한 통찰을 대중에게 전달하려 합니다. 흥미를 끄는 힘은 크지만 검증되지 않은 주장은 조심해야 합니다.", ["career", "money"], ["ten_god_unverified_claim_caution"]),
    ("pyeon_in", "sik_sin"): _rule(["도식", "행동 제어", "실행 지연"], "편인이 식신을 보면 생각과 검열이 행동을 누릅니다. 책임 있게 쓰면 세밀한 통제가 되지만, 약하면 실행력 저하와 의존 문제가 생깁니다.", ["career", "money"], ["ten_god_indirect_resource_food_block"]),
    ("pyeon_in", "sang_gwan"): _rule(["독창 표현", "자기반성", "언행 정리"], "편인이 상관을 보면 직관적 이해가 말과 표현으로 나옵니다. 깊은 메시지를 전할 수 있지만 현실 검증이 필요합니다.", ["career", "love"]),
    ("pyeon_in", "pyeon_jae"): _rule(["외부 자극", "후원", "감정 전환"], "편인이 편재를 보면 바깥 사람과 기회가 내면의 고립을 바꿉니다. 후원, 취미, 여행, 프로젝트가 생각을 움직입니다.", ["money", "love", "career"]),
    ("pyeon_in", "jeong_jae"): _rule(["현실 점검", "자기 검토", "내적 청결"], "편인이 정재를 보면 이상과 직관이 현실 앞에서 점검됩니다. 깊은 자기 검토가 생기고, 자신의 쓸모와 현실성을 묻게 됩니다.", ["career", "love"], ["ten_god_reality_ideal_caution"]),
    ("pyeon_in", "pyeon_gwan"): _rule(["위기 전략", "융통", "허점 활용"], "편인이 편관을 보면 급한 임무를 유연한 방법으로 해결합니다. 위기 대응은 뛰어나지만 사회적 허점을 과하게 이용하지 않아야 합니다.", ["career"], ["ten_god_shortcut_caution"]),
    ("pyeon_in", "jeong_gwan"): _rule(["특수 사고", "공식 기준", "낯선 적응"], "편인이 정관을 보면 비공식 사고가 제도적 기준과 만납니다. 독창성은 살아 있으나 공식 자리에서는 표현을 정돈해야 합니다.", ["career"]),
    ("pyeon_in", "pyeon_in"): _rule(["몰입", "고독", "내면 과다"], "편인이 편인을 보면 내면의 생각과 특수 관심이 깊어집니다. 직관은 강하지만 현실 접점이 약하면 고립되기 쉽습니다.", ["career", "love"], ["ten_god_isolation_caution"]),
    ("pyeon_in", "jeong_in"): _rule(["직관과 정통", "지식 보완", "충돌"], "편인이 정인을 보면 비공식 통찰과 정규 지식이 서로 보완하거나 충돌합니다. 둘을 구분해 쓰면 전문성이 깊어집니다.", ["career"]),
    ("jeong_in", "bi_gyeon"): _rule(["특정 집단", "지식 제공", "연대"], "정인이 비견을 보면 공인 지식과 자격이 특정 집단을 돕습니다. 동료나 내부 사람에게 기준과 이해를 제공하는 역할입니다.", ["career", "love"]),
    ("jeong_in", "geob_jae"): _rule(["대중 인기", "지식 배포", "영향력"], "정인이 겁재를 보면 갖춘 지식과 자격이 대중에게 알려집니다. 강의, 상담, 콘텐츠처럼 전문성을 쉽게 풀어내는 능력이 커집니다.", ["career", "money"]),
    ("jeong_in", "sik_sin"): _rule(["매뉴얼", "노하우", "절차화"], "정인이 식신을 보면 지식을 실행 절차로 바꿉니다. 정교한 기술, 매뉴얼, 훈련, 생활 규칙을 만드는 데 강합니다.", ["career", "money"]),
    ("jeong_in", "sang_gwan"): _rule(["자격 갖춘 비판", "교육", "공식 표현"], "정인이 상관을 보면 자유로운 비판과 표현이 자격을 갖춥니다. 전문가의 감시, 교육, 공인 발언으로 정리됩니다.", ["career"]),
    ("jeong_in", "pyeon_jae"): _rule(["지식 시장화", "새 도전", "콘텐츠"], "정인이 편재를 보면 오래 쌓은 지식이 시장과 만납니다. 강의, 출판, 방송, 온라인 콘텐츠처럼 지식을 새 수요에 맞춥니다.", ["money", "career"]),
    ("jeong_in", "jeong_jae"): _rule(["검증", "계약", "실무 조정"], "정인이 정재를 보면 이론과 자격이 현실 검증을 받습니다. 계약, 예산, 리스크 관리, 인사, 회계, 실무 조정에 강합니다.", ["money", "career", "marriage"]),
    ("jeong_in", "pyeon_gwan"): _rule(["임무 수행", "체계", "스트레스"], "정인이 편관을 보면 갑작스러운 임무를 형식과 체계로 처리합니다. 불편하고 느려도 결과의 완성도는 높습니다.", ["career", "marriage"]),
    ("jeong_in", "jeong_gwan"): _rule(["정통성", "직업 안정", "보호"], "정인이 정관을 보면 직위와 자격이 서로를 보호합니다. 안정된 조직, 공적 신뢰, 지속적인 경력에 유리합니다.", ["career", "marriage"]),
    ("jeong_in", "pyeon_in"): _rule(["정통과 직관", "해석 확장", "전문 깊이"], "정인이 편인을 보면 공식 지식과 직관적 이해가 만납니다. 학문적 틀 안에서 특수한 해석 능력이 깊어집니다.", ["career"]),
    ("jeong_in", "jeong_in"): _rule(["자격 반복", "보호", "현상 유지"], "정인이 정인을 보면 보호, 학습, 자격, 품위가 반복됩니다. 안정은 크지만 현실 행동과 확장이 약해질 수 있습니다.", ["career", "marriage"], ["ten_god_resource_stagnation_caution"]),
}


def ten_god_base_rule(ten_god: str) -> dict[str, Any]:
    return TEN_GOD_BASE_RULES[ten_god]


def ten_god_direction_rule(source_ten_god: str, target_ten_god: str) -> dict[str, Any]:
    return TEN_GOD_DIRECTION_RULES[(source_ten_god, target_ten_god)]


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


def _domains_for_positions(source_position: str, target_position: str) -> list[str]:
    position_domains = {
        "year": ["career", "love"],
        "month": ["career", "money"],
        "day": ["love", "marriage"],
        "hour": ["career", "money", "marriage"],
    }
    domains: list[str] = []
    for position in (source_position, target_position):
        base = position.split(":", 1)[0]
        domains.extend(position_domains.get(base, []))
    return domains


def _group_domains(source_ten_god: str, target_ten_god: str) -> list[str]:
    domains: list[str] = []
    for ten_god in (source_ten_god, target_ten_god):
        domains.extend(TEN_GOD_BASE_RULES[ten_god]["domain_links"])
        group = TEN_GOD_GROUPS[ten_god]
        if group == "wealth":
            domains.append("money")
        if group == "officer":
            domains.extend(["career", "marriage"])
        if group == "output":
            domains.extend(["career", "money"])
        if group == "resource":
            domains.append("career")
        if group == "peer":
            domains.extend(["money", "career"])
    return domains


def _domain_links(
    source_ten_god: str,
    target_ten_god: str,
    source_position: str,
    target_position: str,
) -> list[str]:
    rule = ten_god_direction_rule(source_ten_god, target_ten_god)
    domains = (
        list(rule["domain_links"])
        + _group_domains(source_ten_god, target_ten_god)
        + _domains_for_positions(source_position, target_position)
    )
    domain_set = set(domains)
    return [domain for domain in SERVICE_DOMAINS if domain in domain_set]


def _strength_from_entries(source_entry: dict[str, Any], target_entry: dict[str, Any]) -> str:
    if source_entry["source"] == "visible" and target_entry["source"] == "visible":
        return "high"
    if source_entry["source"] == "visible" or target_entry["source"] == "visible":
        return "moderate"
    weight = float(source_entry.get("weight", 0.0)) + float(target_entry.get("weight", 0.0))
    return "moderate" if weight >= 1.1 else "low"


def _entry_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    return (_position_sort_key(str(entry["position"])), str(entry["source"]), str(entry["stem"]))


def _position_base(position: str) -> str:
    return position.split(":", 1)[0]


def _position_context(source_position: str, target_position: str) -> str:
    source_base = _position_base(source_position)
    target_base = _position_base(target_position)
    source_label = POSITION_LABELS.get(source_base, source_base)
    target_label = POSITION_LABELS.get(target_base, target_base)
    if ":hidden" in source_position or ":hidden" in target_position:
        return f"{source_label}와 {target_label}의 지장간에서 숨어 있던 십신 작용입니다."
    if "branch_main" in source_position or "branch_main" in target_position:
        return f"{source_label}와 {target_label}의 천간·지지 본기가 맞물린 작용입니다."
    return f"{source_label}와 {target_label}의 천간에 드러난 십신 작용입니다."


def _month_context_note(source_position: str, target_position: str) -> str:
    touches_month = _position_base(source_position) == "month" or _position_base(target_position) == "month"
    if not touches_month:
        return "월지 기준에서는 보조 신호로 보되, 대운·세운에서 같은 십신이 살아날 때 현실화가 강해집니다."
    if "branch" in source_position or "branch" in target_position or ":hidden" in source_position or ":hidden" in target_position:
        return "월지와 지장간에 걸린 작용이라 현실 조건, 직업 환경, 돈의 기준에 직접 닿습니다."
    return "월간에 드러난 작용이라 사회적 태도와 직업적 선택에서 먼저 보입니다."


def _subject_label(ten_god: str) -> str:
    return f"{TEN_GOD_LABELS[ten_god]}{TEN_GOD_SUBJECT_PARTICLE[ten_god]}"


def _object_label(ten_god: str) -> str:
    return f"{TEN_GOD_LABELS[ten_god]}{TEN_GOD_OBJECT_PARTICLE[ten_god]}"


def _signal(
    *,
    layer: str,
    source_entry: dict[str, Any],
    target_entry: dict[str, Any],
    signal_suffix: str,
) -> TenGodInteractionSignal:
    source_ten_god = str(source_entry["ten_god"])
    target_ten_god = str(target_entry["ten_god"])
    source_position = str(source_entry["position"])
    target_position = str(target_entry["position"])
    source_stem = str(source_entry["stem"])
    target_stem = str(target_entry["stem"])
    rule = ten_god_direction_rule(source_ten_god, target_ten_god)
    source_base = ten_god_base_rule(source_ten_god)
    target_base = ten_god_base_rule(target_ten_god)
    direction_key = f"{source_ten_god}->{target_ten_god}"
    basis_codes = [
        f"ten_god_interaction_{layer}_{source_ten_god}_{target_ten_god}",
        f"ten_god_source_{source_ten_god}",
        f"ten_god_target_{target_ten_god}",
    ]
    return TenGodInteractionSignal(
        signal_id=f"ten_god_interaction_{layer}_{signal_suffix}_{source_ten_god}_to_{target_ten_god}",
        layer=layer,
        direction_key=direction_key,
        source_position=source_position,
        target_position=target_position,
        source_stem=source_stem,
        target_stem=target_stem,
        source_branch=str(source_entry.get("branch", "")),
        target_branch=str(target_entry.get("branch", "")),
        source_ten_god=source_ten_god,
        target_ten_god=target_ten_god,
        source_rule="ten_god_interaction_v1",
        strength=_strength_from_entries(source_entry, target_entry),
        domain_links=_domain_links(source_ten_god, target_ten_god, source_position, target_position),
        basis_codes=basis_codes,
        counter_signals=list(rule["counter_signals"]),
        trait_keywords=list(rule["trait_keywords"]),
        interpretation=str(rule["interpretation"]),
        source_core=str(source_base["core"]),
        target_core=str(target_base["core"]),
        position_context=_position_context(source_position, target_position),
        month_context_note=_month_context_note(source_position, target_position),
    )


def _visible_entries(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        if position == "day":
            continue
        signal = position_signals[position]
        entries.append(
            {
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "ten_god": signal.stem_ten_god,
                "weight": POSITION_STEM_WEIGHTS[position],
            }
        )
    return entries


def _hidden_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    day_stem_key = chart.day_pillar.stem_key
    for position, pillar in _pillars(chart).items():
        for index, (stem_key, hidden_weight) in enumerate(BRANCH_HIDDEN_STEMS[pillar.branch_key]):
            entries.append(
                {
                    "position": f"{position}:hidden:{index}",
                    "source": "hidden",
                    "stem": stem_key,
                    "branch": pillar.branch_key,
                    "ten_god": ten_god_for(day_stem_key, stem_key),
                    "weight": POSITION_BRANCH_WEIGHTS[position] * hidden_weight,
                }
            )
    return entries


def _stem_branch_entries(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for position, pillar in _pillars(chart).items():
        if position == "day":
            continue
        signal = position_signals[position]
        hidden_stem_key = main_hidden_stem(pillar.branch_key)
        stem_entry = {
            "position": f"{position}:stem",
            "source": "visible",
            "stem": pillar.stem_key,
            "branch": pillar.branch_key,
            "ten_god": signal.stem_ten_god,
            "weight": POSITION_STEM_WEIGHTS[position],
        }
        branch_entry = {
            "position": f"{position}:branch_main",
            "source": "hidden",
            "stem": hidden_stem_key,
            "branch": pillar.branch_key,
            "ten_god": signal.branch_main_ten_god,
            "weight": POSITION_BRANCH_WEIGHTS[position],
        }
        pairs.append((stem_entry, branch_entry))
        pairs.append((branch_entry, stem_entry))
    return pairs


def _directional_pair_signals(
    *,
    layer: str,
    entries: list[dict[str, Any]],
    limit: int | None = None,
) -> list[TenGodInteractionSignal]:
    signals: list[TenGodInteractionSignal] = []
    ordered_entries = sorted(entries, key=_entry_sort_key)
    for index, (source_entry, target_entry) in enumerate(permutations(ordered_entries, 2), start=1):
        if source_entry["ten_god"] not in TEN_GOD_ORDER or target_entry["ten_god"] not in TEN_GOD_ORDER:
            continue
        signals.append(
            _signal(
                layer=layer,
                source_entry=source_entry,
                target_entry=target_entry,
                signal_suffix=f"2_{index}",
            )
        )
    return _dedupe_signals(signals, limit=limit)


def _stem_branch_signals(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> list[TenGodInteractionSignal]:
    signals: list[TenGodInteractionSignal] = []
    for index, (source_entry, target_entry) in enumerate(_stem_branch_entries(chart, position_signals), start=1):
        if source_entry["ten_god"] not in TEN_GOD_ORDER or target_entry["ten_god"] not in TEN_GOD_ORDER:
            continue
        signals.append(
            _signal(
                layer="stem_branch",
                source_entry=source_entry,
                target_entry=target_entry,
                signal_suffix=f"2_{index}",
            )
        )
    return _dedupe_signals(signals)


def _signal_rank(signal: TenGodInteractionSignal) -> tuple[int, int, int, int, int]:
    layer_rank = {"visible_stem": 0, "stem_branch": 1, "hidden_stem": 2}.get(signal.layer, 3)
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    counter_rank = 0 if signal.counter_signals else 1
    position_rank = min(_position_sort_key(signal.source_position), _position_sort_key(signal.target_position))
    domain_rank = -len(signal.domain_links)
    return (layer_rank, strength_rank, counter_rank, position_rank, domain_rank)


def _dedupe_signals(
    signals: list[TenGodInteractionSignal],
    limit: int | None = None,
) -> list[TenGodInteractionSignal]:
    deduped: list[TenGodInteractionSignal] = []
    seen: set[tuple[str, str, str, str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        key = (signal.layer, signal.direction_key, signal.source_position, signal.target_position)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _summary_sentences(signals: list[TenGodInteractionSignal]) -> list[str]:
    selected: list[TenGodInteractionSignal] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        pair_key = tuple(sorted((signal.source_ten_god, signal.target_ten_god))) + (signal.layer,)
        if pair_key in seen_pairs:
            continue
        selected.append(signal)
        seen_pairs.add(pair_key)
        if len(selected) >= 5:
            break
    sentences: list[str] = []
    for signal in selected:
        source_label = _subject_label(signal.source_ten_god)
        target_label = _object_label(signal.target_ten_god)
        keywords = ", ".join(signal.trait_keywords[:3])
        sentences.append(
            f"당신의 사주에서는 {source_label} {target_label} 상대합니다. 핵심은 {keywords}입니다. {signal.interpretation} {signal.month_context_note}"
        )
    return sentences


def iter_ten_god_interaction_signals(profile: TenGodInteractionProfile) -> list[TenGodInteractionSignal]:
    return (
        list(profile.visible_stem_signals)
        + list(profile.stem_branch_signals)
        + list(profile.hidden_stem_signals)
    )


def build_ten_god_interaction_profile(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> TenGodInteractionProfile:
    visible_entries = _visible_entries(chart, position_signals)
    hidden_entries = _hidden_entries(chart)
    visible_stem_signals = _directional_pair_signals(layer="visible_stem", entries=visible_entries)
    stem_branch_signals = _stem_branch_signals(chart, position_signals)
    hidden_stem_signals = _directional_pair_signals(layer="hidden_stem", entries=hidden_entries, limit=36)
    all_signals = _dedupe_signals(visible_stem_signals + stem_branch_signals + hidden_stem_signals)
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_signal_rank)[:12]]
    return TenGodInteractionProfile(
        visible_stem_signals=visible_stem_signals,
        hidden_stem_signals=hidden_stem_signals,
        stem_branch_signals=stem_branch_signals,
        top_signal_ids=top_signal_ids,
        summary_sentences=_summary_sentences(all_signals),
    )
