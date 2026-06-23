"""Korean scene lexicon for future customer-report prose.

This module does not render customer prose by itself. It keeps the Korean
materials that will later translate abstract engine values into concrete life
scenes. The goal is to prevent code-shaped phrases such as "기준이 드러납니다"
from reaching the report without a domain-specific noun and verb.
"""

from __future__ import annotations

from dataclasses import dataclass


KOREAN_SCENE_LEXICON_VERSION = "korean_scene_lexicon_v1"


DomainKey = str


@dataclass(frozen=True)
class DomainSceneLexicon:
    """Concrete Korean materials for one report domain."""

    domain: DomainKey
    domain_label: str
    subject_nouns: tuple[str, ...]
    scene_nouns: tuple[str, ...]
    event_verbs: tuple[str, ...]
    timing_nouns: tuple[str, ...]
    caution_scene_nouns: tuple[str, ...]
    abstract_replacements: dict[str, tuple[str, ...]]
    state_verb_replacements: dict[str, tuple[str, ...]]


_MONEY = DomainSceneLexicon(
    domain="money",
    domain_label="재물",
    subject_nouns=(
        "수입",
        "보수",
        "정산금",
        "계약금",
        "저축액",
        "투자금",
        "고정비",
        "세금",
        "카드값",
        "대출 상환액",
    ),
    scene_nouns=(
        "지급일",
        "정산",
        "계약서",
        "보수 협의",
        "고정비",
        "저축액",
        "투자금",
        "세금",
        "거래처",
        "청구서",
        "매출",
        "대출 상환",
    ),
    event_verbs=(
        "입금됩니다",
        "정산됩니다",
        "보수로 돌아옵니다",
        "계약서에 남습니다",
        "지급일이 정해집니다",
        "고정비가 늘어납니다",
        "저축액이 쌓입니다",
        "투자금이 묶입니다",
        "세금이 붙습니다",
        "회수 일정이 늦어집니다",
    ),
    timing_nouns=(
        "입금일",
        "정산일",
        "계약 갱신일",
        "세금 납부 시기",
        "보너스 지급 시기",
        "투자 회수 시점",
    ),
    caution_scene_nouns=(
        "늦은 정산",
        "구두 약속",
        "늘어난 고정비",
        "세금 누락",
        "회수 일정 지연",
        "분리되지 않은 생활비",
        "충동 지출",
        "차입금 부담",
    ),
    abstract_replacements={
        "기준": ("지급일", "정산 방식", "계약서의 지급 조항", "고정비 한도"),
        "조건": ("보수 협의 내용", "거래처의 지급 약속", "세금 처리", "회수 일정"),
        "가능성": ("입금될 돈", "보수로 돌아올 일", "회수 가능한 투자금", "쌓일 저축액"),
        "판단": ("계약서 확인", "지출 결정", "투자금 회수 계산", "세금 계산"),
        "관리": ("통장 분리", "고정비 점검", "정산 일정 확인", "저축액 배분"),
        "조정": ("지출 축소", "정산 일정 변경", "투자금 비중 축소", "상환 일정 조절"),
        "안정": ("저축액 증가", "고정비 축소", "정산일 확정", "대출 상환 부담 감소"),
        "역할": ("돈을 벌어오는 자리", "정산을 맡는 자리", "거래를 마무리하는 자리", "입출금 내역을 확인하는 자리"),
        "방식": ("계약서로 남기는 일", "정산일을 먼저 정하는 일", "생활비를 분리하는 일", "회수 일정을 확인하는 일"),
        "구조": ("수입원", "지출 항목", "정산 절차", "저축과 투자 비중"),
    },
    state_verb_replacements={
        "드러납니다": ("보수 협의로 나옵니다", "정산 일정으로 확인됩니다", "지출 항목에서 확인됩니다"),
        "나타납니다": ("입금과 지출로 보입니다", "계약서와 정산서에 남습니다", "통장 잔액으로 확인됩니다"),
        "확인됩니다": ("정산일에서 확인됩니다", "계약 조항에서 확인됩니다", "고정비 내역에서 확인됩니다"),
        "정해집니다": ("지급일이 정해집니다", "정산 방식이 결정됩니다", "지출 한도가 정해집니다"),
        "이어집니다": ("입금으로 돌아옵니다", "저축액이 늘어납니다", "상환 부담이 줄어듭니다"),
        "반영됩니다": ("보수에 반영됩니다", "정산 금액에 반영됩니다", "계약 단가에 반영됩니다"),
        "구체화됩니다": ("지급일과 금액으로 정해집니다", "계약서 조항으로 남습니다", "저축 계획으로 정리됩니다"),
    },
)


_CAREER = DomainSceneLexicon(
    domain="career",
    domain_label="직업",
    subject_nouns=(
        "직무",
        "업무량",
        "결정권",
        "성과 지표",
        "보고 체계",
        "책임 소재",
        "승진 심사",
        "프로젝트",
        "상급자 평가",
        "팀의 기대",
    ),
    scene_nouns=(
        "직무 범위",
        "결정권",
        "평가 방식",
        "성과 지표",
        "보고 체계",
        "책임 소재",
        "업무량",
        "프로젝트 일정",
        "회의 자리",
        "인사 평가",
        "승진 심사",
        "조직 개편",
    ),
    event_verbs=(
        "배정됩니다",
        "맡게 됩니다",
        "좋은 평가를 받습니다",
        "승인됩니다",
        "보고합니다",
        "조정합니다",
        "결정권을 받습니다",
        "책임이 커집니다",
        "일정이 당겨집니다",
        "업무 범위가 넓어집니다",
    ),
    timing_nouns=(
        "평가 시기",
        "프로젝트 마감일",
        "인사 이동 시기",
        "승진 심사",
        "계약 갱신 시기",
        "조직 개편 시기",
    ),
    caution_scene_nouns=(
        "권한 없는 책임",
        "불분명한 보고 체계",
        "잦은 기준 변경",
        "성과 지표 누락",
        "일정 압박",
        "책임 소재 혼선",
        "과도한 회의",
        "상급자 요구의 변동",
    ),
    abstract_replacements={
        "기준": ("성과 지표", "평가 방식", "보고 체계", "업무 마감일"),
        "조건": ("직무 범위", "결정권", "상급자의 요구", "인사 평가 방식"),
        "가능성": ("맡게 될 자리", "승진 심사에 오를 일", "평가받을 성과", "확대될 프로젝트"),
        "판단": ("업무 우선순위 결정", "보고 순서 결정", "일정 조정", "책임 소재 확인"),
        "관리": ("일정 관리", "문서 관리", "회의록 정리", "업무 배분"),
        "조정": ("일정 변경", "업무 범위 축소", "보고선 정리", "인력 배치 변경"),
        "안정": ("직무 범위 확정", "평가 방식 고정", "보고 체계 정착", "업무량 조절"),
        "역할": ("맡는 직무", "보고하는 자리", "결정하는 자리", "팀을 조율하는 자리"),
        "방식": ("문서로 정리하는 일", "순서대로 배분하는 일", "회의에서 결정하는 일", "보고선에 맞추는 일"),
        "구조": ("직무 체계", "보고 체계", "평가 체계", "프로젝트 운영 절차"),
    },
    state_verb_replacements={
        "드러납니다": ("평가 자리에서 보입니다", "업무 배분에서 보입니다", "보고 체계에서 확인됩니다"),
        "나타납니다": ("업무량으로 보입니다", "평가 결과로 확인됩니다", "조직의 요구로 커집니다"),
        "확인됩니다": ("직무 범위에서 확인됩니다", "평가 방식에서 확인됩니다", "보고선에서 확인됩니다"),
        "정해집니다": ("직무 범위가 정해집니다", "평가 방식이 결정됩니다", "보고 순서가 정리됩니다"),
        "이어집니다": ("좋은 평가를 받습니다", "책임이 확대됩니다", "다음 프로젝트를 맡습니다"),
        "반영됩니다": ("평가에 반영됩니다", "보직에 반영됩니다", "성과 지표에 반영됩니다"),
        "구체화됩니다": ("직무 범위로 정해집니다", "프로젝트 일정으로 정리됩니다", "평가 항목으로 정해집니다"),
    },
)


_LOVE = DomainSceneLexicon(
    domain="love",
    domain_label="연애",
    subject_nouns=(
        "연락",
        "말투",
        "만나는 빈도",
        "호감",
        "감정 표현",
        "약속",
        "대화 시간",
        "거리",
        "기대",
        "상대의 반응",
    ),
    scene_nouns=(
        "연락 간격",
        "말투",
        "만나는 빈도",
        "감정 표현",
        "약속 방식",
        "대화 시간",
        "답장 속도",
        "만남 장소",
        "서로의 거리",
        "기념일",
        "소개 자리",
        "갈등 뒤의 대화",
    ),
    event_verbs=(
        "연락이 잦아집니다",
        "만남이 늘어납니다",
        "호감이 커집니다",
        "마음을 표현합니다",
        "대화가 길어집니다",
        "약속이 정해집니다",
        "상대의 반응이 또렷해집니다",
        "거리감이 생깁니다",
        "오해가 풀립니다",
        "말투에서 차이가 납니다",
    ),
    timing_nouns=(
        "첫 연락 시기",
        "만남이 늘어나는 시기",
        "고백을 받는 시기",
        "관계가 가까워지는 시기",
        "갈등 뒤 대화하는 시기",
        "관계를 정하는 시기",
    ),
    caution_scene_nouns=(
        "늦은 답장",
        "애매한 약속",
        "말투 오해",
        "서로 다른 연락 간격",
        "표현의 지연",
        "주변 사람의 개입",
        "만남 빈도 차이",
        "갈등 뒤 침묵",
    ),
    abstract_replacements={
        "기준": ("연락 간격", "만나는 빈도", "약속 방식", "감정 표현의 속도"),
        "조건": ("상대의 연락 태도", "만남의 거리", "서로의 생활 시간", "약속을 지키는 태도"),
        "가능성": ("가까워질 사람", "이어질 만남", "표현될 마음", "확인될 호감"),
        "판단": ("답장 속도 확인", "만남 횟수 확인", "상대의 말투 확인", "약속을 지키는지 보는 일"),
        "관리": ("연락 간격 조절", "감정 표현 조절", "약속 시간 지키기", "오해를 바로 푸는 일"),
        "조정": ("연락 속도 맞추기", "만남 횟수 줄이기", "대화 시간을 다시 정하기", "기대치를 말로 맞추기"),
        "안정": ("연락 간격의 안정", "반복되는 만남", "편안한 말투", "갈등 뒤 다시 대화하는 힘"),
        "역할": ("먼저 연락하는 사람", "관계를 정리해 말하는 사람", "약속을 정하는 사람", "갈등을 푸는 사람"),
        "방식": ("자주 연락하는 일", "말로 확인하는 일", "약속을 먼저 정하는 일", "불편함을 바로 말하는 일"),
        "구조": ("연락의 간격", "만남의 빈도", "감정 표현의 속도", "서로의 생활 시간"),
    },
    state_verb_replacements={
        "드러납니다": ("말투에서 보입니다", "연락 간격에서 보입니다", "만남의 횟수로 확인됩니다"),
        "나타납니다": ("연락과 약속으로 보입니다", "상대의 반응으로 확인됩니다", "대화 시간에서 보입니다"),
        "확인됩니다": ("답장 속도에서 확인됩니다", "약속을 지키는 태도에서 확인됩니다", "만나는 빈도에서 확인됩니다"),
        "정해집니다": ("관계의 방향이 또렷해집니다", "만남의 속도가 정해집니다", "서로의 거리가 정해집니다"),
        "이어집니다": ("다음 만남이 잡힙니다", "고백으로 넘어갑니다", "관계를 확인하게 됩니다"),
        "반영됩니다": ("말투에 반영됩니다", "연락 태도에 반영됩니다", "만남의 빈도에 반영됩니다"),
        "구체화됩니다": ("약속 날짜가 정해집니다", "관계의 이름이 또렷해집니다", "반복되는 만남이 생깁니다"),
    },
)


_MARRIAGE = DomainSceneLexicon(
    domain="marriage",
    domain_label="결혼",
    subject_nouns=(
        "생활비",
        "주거 계획",
        "배우자의 책임",
        "가족과의 거리",
        "집안일",
        "돈 관리",
        "양가 협의",
        "결혼 시기",
        "부채",
        "공동 저축",
    ),
    scene_nouns=(
        "생활비",
        "주거 계획",
        "가족과의 거리",
        "역할 분담",
        "집안일",
        "돈 관리",
        "양가 협의",
        "혼수 비용",
        "부채 확인",
        "공동 저축",
        "자녀 계획",
        "거주지 선택",
    ),
    event_verbs=(
        "결혼 이야기가 나옵니다",
        "주거 계획이 정해집니다",
        "생활비를 정합니다",
        "가족과 협의합니다",
        "역할을 나눕니다",
        "부채를 확인합니다",
        "공동 저축을 시작합니다",
        "결혼 시기가 정해집니다",
        "집안일을 나눕니다",
        "양가의 요구가 커집니다",
    ),
    timing_nouns=(
        "결혼 이야기가 나오는 시기",
        "주거를 정하는 시기",
        "양가를 만나는 시기",
        "생활비를 정하는 시기",
        "식장과 날짜를 잡는 시기",
        "공동 저축을 시작하는 시기",
    ),
    caution_scene_nouns=(
        "생활비 부담",
        "주거 문제",
        "양가 요구",
        "부채 공개 지연",
        "집안일 불균형",
        "돈 관리 방식 차이",
        "거주지 선택 갈등",
        "결혼 시기 압박",
    ),
    abstract_replacements={
        "기준": ("생활비 부담", "집안일 분담", "가족과의 거리", "공동 저축 방식"),
        "조건": ("주거 계획", "양가의 요구", "부채 공개", "결혼 시기"),
        "가능성": ("결혼 이야기가 나올 일", "함께 살 집을 정할 일", "공동 저축을 시작할 일", "양가 협의가 시작될 일"),
        "판단": ("생활비를 나누는 일", "거주지를 정하는 일", "양가 요구를 듣는 일", "부채를 확인하는 일"),
        "관리": ("공동 통장 관리", "생활비 분담", "집안일 분담", "양가 일정 조율"),
        "조정": ("결혼 시기 조절", "거주지 재논의", "생활비 비율 조정", "가족 방문 횟수 조절"),
        "안정": ("생활비 분담의 정착", "주거 계획 확정", "가족과의 거리 조절", "집안일 분담의 지속"),
        "역할": ("생활비를 맡는 사람", "집안일을 나누는 사람", "양가와 대화하는 사람", "공동 재정을 챙기는 사람"),
        "방식": ("생활비를 나누는 일", "집안일을 정하는 일", "양가 일정을 맞추는 일", "공동 저축을 시작하는 일"),
        "구조": ("생활비 분담", "주거 계획", "가족 관계", "공동 재정"),
    },
    state_verb_replacements={
        "드러납니다": ("생활비 문제에서 보입니다", "주거 계획에서 보입니다", "가족과의 거리에서 확인됩니다"),
        "나타납니다": ("생활비와 집안일에서 커집니다", "양가 협의에서 다룹니다", "거주지 선택에서 갈립니다"),
        "확인됩니다": ("생활비 분담에서 확인됩니다", "부채 공개에서 확인됩니다", "가족과의 거리에서 확인됩니다"),
        "정해집니다": ("결혼 시기가 정해집니다", "생활비 분담이 정해집니다", "주거 계획이 정해집니다"),
        "이어집니다": ("결혼 이야기가 나옵니다", "주거 결정을 하게 됩니다", "공동 생활의 약속이 생깁니다"),
        "반영됩니다": ("생활비 분담에 반영됩니다", "주거 계획에 반영됩니다", "양가 협의에 반영됩니다"),
        "구체화됩니다": ("결혼 날짜가 정해집니다", "주거 계획으로 정리됩니다", "생활비 분담이 정해집니다"),
    },
)


DOMAIN_SCENE_LEXICONS: dict[DomainKey, DomainSceneLexicon] = {
    item.domain: item
    for item in (_MONEY, _CAREER, _LOVE, _MARRIAGE)
}

DOMAIN_ALIASES: dict[str, DomainKey] = {
    "relationship": "love",
    "romance": "love",
    "marital": "marriage",
}

FORBIDDEN_GENERIC_TOKENS = ("흐름", "리듬", "패턴", "판", "통로")


def normalize_domain(domain: str) -> DomainKey:
    """Return the canonical domain key used by the lexicon."""
    return DOMAIN_ALIASES.get(domain, domain)


def domain_scene_lexicon(domain: str) -> DomainSceneLexicon:
    """Return concrete Korean materials for a domain."""
    normalized = normalize_domain(domain)
    if normalized not in DOMAIN_SCENE_LEXICONS:
        raise KeyError(f"unsupported domain for Korean scene lexicon: {domain}")
    return DOMAIN_SCENE_LEXICONS[normalized]


def concrete_terms_for(domain: str, abstract_key: str) -> tuple[str, ...]:
    """Return concrete nouns that can replace an abstract source marker."""
    lexicon = domain_scene_lexicon(domain)
    return lexicon.abstract_replacements.get(abstract_key, ())


def event_verbs_for(domain: str) -> tuple[str, ...]:
    """Return event verbs that fit a domain's customer scene."""
    return domain_scene_lexicon(domain).event_verbs


def state_verb_rewrite_targets(domain: str, marker: str) -> tuple[str, ...]:
    """Return domain-specific replacements for a state-reporting verb."""
    lexicon = domain_scene_lexicon(domain)
    return lexicon.state_verb_replacements.get(marker, ())


def lexicon_coverage_for_markers(markers: tuple[str, ...]) -> dict[str, dict[str, bool]]:
    """Report whether each domain has concrete material for each marker."""
    coverage: dict[str, dict[str, bool]] = {}
    for domain, lexicon in DOMAIN_SCENE_LEXICONS.items():
        coverage[domain] = {
            marker: bool(
                lexicon.abstract_replacements.get(marker)
                or lexicon.state_verb_replacements.get(marker)
            )
            for marker in markers
        }
    return coverage


def validate_korean_scene_lexicon() -> list[str]:
    """Return static lexicon errors without touching rendered reports."""
    errors: list[str] = []
    required_domains = {"money", "career", "love", "marriage"}
    if set(DOMAIN_SCENE_LEXICONS) != required_domains:
        errors.append("korean_scene_lexicon: domain set mismatch")

    required_abstract_keys = {
        "기준",
        "조건",
        "가능성",
        "판단",
        "관리",
        "조정",
        "안정",
        "역할",
        "방식",
        "구조",
    }
    required_state_verbs = {
        "드러납니다",
        "나타납니다",
        "확인됩니다",
        "정해집니다",
        "이어집니다",
        "반영됩니다",
        "구체화됩니다",
    }

    for domain, lexicon in DOMAIN_SCENE_LEXICONS.items():
        if len(lexicon.subject_nouns) < 8:
            errors.append(f"korean_scene_lexicon:{domain}: subject nouns too sparse")
        if len(lexicon.scene_nouns) < 10:
            errors.append(f"korean_scene_lexicon:{domain}: scene nouns too sparse")
        if len(lexicon.event_verbs) < 8:
            errors.append(f"korean_scene_lexicon:{domain}: event verbs too sparse")
        if len(lexicon.timing_nouns) < 5:
            errors.append(f"korean_scene_lexicon:{domain}: timing nouns too sparse")
        if len(lexicon.caution_scene_nouns) < 6:
            errors.append(f"korean_scene_lexicon:{domain}: caution nouns too sparse")

        missing_abstract = required_abstract_keys - set(lexicon.abstract_replacements)
        if missing_abstract:
            errors.append(f"korean_scene_lexicon:{domain}: missing abstract keys {sorted(missing_abstract)}")
        missing_state_verbs = required_state_verbs - set(lexicon.state_verb_replacements)
        if missing_state_verbs:
            errors.append(f"korean_scene_lexicon:{domain}: missing state verbs {sorted(missing_state_verbs)}")

        material_values: list[str] = []
        material_values.extend(lexicon.subject_nouns)
        material_values.extend(lexicon.scene_nouns)
        material_values.extend(lexicon.event_verbs)
        material_values.extend(lexicon.timing_nouns)
        material_values.extend(lexicon.caution_scene_nouns)
        for values in lexicon.abstract_replacements.values():
            material_values.extend(values)
        for values in lexicon.state_verb_replacements.values():
            material_values.extend(values)

        for value in material_values:
            if any(token in value for token in FORBIDDEN_GENERIC_TOKENS):
                errors.append(f"korean_scene_lexicon:{domain}: forbidden generic token in {value}")
            if not value.strip():
                errors.append(f"korean_scene_lexicon:{domain}: blank material")

    return errors
