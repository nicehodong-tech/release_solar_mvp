"""Context-aware Korean prose checks for customer fortune reports.

This module does not ban words globally. It checks whether a sentence fits the
section role, domain, and nearby report context. Repetition is acceptable when
it sounds natural; awkward substitutions and vague explanatory register are not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


CONTEXTUAL_KOREAN_POLICY_VERSION = "contextual_korean_policy_v3"

CONCLUSION_ROLES = {"summary", "closing", "conclusion", "score", "final"}
OPENING_ROLES = {"opening", "lead", "overview", "intro"}
BASIS_ROLES = {"basis", "evidence", "factor", "material", "source"}

DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "money": ("재물", "돈", "수입", "지급", "지급일", "정산", "계약", "약속", "지출", "대출", "자산", "현금", "보수", "금액", "비용", "몫"),
    "career": ("일", "직업", "업무", "직무", "역할", "평가", "책임", "권한", "조직", "성과", "보고", "인정", "신뢰", "약속", "기준", "평판", "소속"),
    "love": ("연애", "관계", "연락", "말투", "만남", "감정", "호감", "대화", "거리", "기대", "마음", "약속"),
    "marriage": ("결혼", "배우자", "생활비", "주거", "가족", "가정", "약속", "살림", "책임", "책임 분담", "사랑", "생활", "마음"),
}

GENERIC_EVENT_TERMS = ("생활 사건", "생활 조건", "구체적인 일", "현실 문제", "사건성")
ABSTRACT_AXIS_TERMS = ("능력", "잠재력", "안정성", "성취력", "영향력", "가능성", "감각")
ABSTRACT_PREDICATES = ("정합니다", "결정합니다", "결론이 납니다", "방향을 정합니다")
WEAK_FORTUNE_REGISTER_PHRASES = {
    "결론이 흘러갑니다": "결론은 '정해집니다', '분명해집니다', '강해집니다'처럼 직접 말합니다.",
    "운이 흘러갑니다": "운세 결론은 '강합니다', '생깁니다', '분명합니다'처럼 실제 양상으로 말합니다.",
    "강하게 열릴 수 있습니다": "상태 설명보다 '강합니다', '크게 생깁니다', '분명합니다'처럼 바로 말합니다.",
    "크게 열릴 수 있습니다": "금전과 성취는 '큽니다', '수입이 늘어납니다', '좋은 평가를 받습니다'처럼 고객이 체감하는 말로 씁니다.",
    "먼저 열립니다": "'먼저 열립니다'는 분석어처럼 들립니다. '먼저 보입니다', '먼저 정해집니다'처럼 실제 장면으로 구체화합니다.",
    "결과를 바꿉니다": "운세 문장에서는 결과를 바꾼다는 설명보다 실제로 나타나는 일을 말합니다.",
    "결과를 바꾸는지": "상품 안내에서는 선택의 효과보다 프리미엄에서 더 보는 사건과 시기를 말합니다.",
    "조건이 맞": "조건부 표현은 운세 결론을 약하게 만듭니다. 실제 양상과 결과를 직접 말합니다.",
    "경우에 따라": "경우의 수를 앞세우면 상담의 확신이 약해집니다. 먼저 결론을 말합니다.",
}

PARTICLE_COLLISION_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"어떤 일이 [^.!?。！？]{0,24} 일이"),
        "어떤 일이 ... 일이",
        "같은 문장 안에서 '일이'가 반복되어 사건 설명과 주어가 겹칩니다.",
    ),
    (
        re.compile(r"맡는 자리가 [^.!?。！？]{0,24} 일이"),
        "맡는 자리가 ... 일이",
        "직업 사건을 설명하는 과정에서 주어가 길어지고 조사가 어색해집니다.",
    ),
    (
        re.compile(r"(?:재물|직업|연애|관계|결혼|성향|건강)에서는 [^.!?。！？]{1,48}에서는"),
        "에서는 ... 에서는",
        "같은 문장 안에서 주제 표지가 두 번 붙어 조립 문장처럼 읽힙니다.",
    ),
    (
        re.compile(r"[가-힣]+의 안정됩니다|[가-힣]+의 [가-힣]{1,12}됩니다"),
        "의 ... 됩니다",
        "명사구와 서술어가 바로 붙어 조사와 서술이 깨집니다.",
    ),
)


@dataclass(frozen=True)
class ContextualKoreanIssue:
    issue_type: str
    severity: int
    marker: str
    reason: str
    suggestion: str
    text: str


def _compact(text: object) -> str:
    return " ".join(str(text or "").replace("\n", " ").split())


def _sentence_domain_hits(text: str) -> dict[str, int]:
    return {
        domain: sum(1 for term in terms if term in text)
        for domain, terms in DOMAIN_TERMS.items()
    }


def _concrete_term_count(text: str) -> int:
    terms = {term for terms in DOMAIN_TERMS.values() for term in terms}
    return sum(1 for term in terms if term in text)


def _has_three_item_list(text: str) -> bool:
    if text.count(",") >= 2:
        return True
    return bool(re.search(r"[가-힣A-Za-z0-9]+·[가-힣A-Za-z0-9]+·[가-힣A-Za-z0-9]+", text))


def contextual_korean_issues(
    text: object,
    *,
    domain: str = "",
    role: str = "",
    section_path: str = "",
) -> list[ContextualKoreanIssue]:
    """Return context-sensitive Korean naturalness issues."""

    sentence = _compact(text)
    if not sentence:
        return []

    normalized_role = str(role or "").strip().lower()
    normalized_domain = str(domain or "").strip().lower()
    issues: list[ContextualKoreanIssue] = []

    if "에서 결론이 납니다" in sentence and normalized_role not in CONCLUSION_ROLES:
        issues.append(
            ContextualKoreanIssue(
                "context_misplaced_conclusion",
                9,
                "에서 결론이 납니다",
                "결론형 문장이 근거·도입·본문 설명 자리에 놓이면 상담 문장보다 조립 문장처럼 보입니다.",
                "도입과 근거에서는 '중요해집니다', '분명해집니다', '안정됩니다'처럼 해당 장면의 작용을 말합니다.",
                sentence,
            )
        )

    if re.search(r"[가-힣]+운에서( 가장)? 먼저 결론이 납니다", sentence):
        issues.append(
            ContextualKoreanIssue(
                "awkward_domain_conclusion_particle",
                8,
                "운에서 결론이 납니다",
                "운세 영역을 장소처럼 처리한 한국어 결합이 어색합니다.",
                "'재물운이 먼저 강해집니다' 또는 '재물운의 결론이 먼저 보입니다'처럼 주어와 서술어를 맞춥니다.",
                sentence,
            )
        )

    if _has_three_item_list(sentence):
        hits = _sentence_domain_hits(sentence)
        active_domains = [name for name, count in hits.items() if count]
        if len(active_domains) >= 2 or sum(hits.values()) >= 3:
            issues.append(
                ContextualKoreanIssue(
                    "multi_core_context_mix",
                    8,
                    "three_or_more_items",
                    "한 문장 안에 서로 다른 생활 영역이나 판단 항목이 함께 들어가 중심이 흐려집니다.",
                    "한 문장에는 한 사건만 둡니다. 나머지는 다음 문장으로 분리합니다.",
                    sentence,
                )
            )

    if any(term in sentence for term in GENERIC_EVENT_TERMS) and _concrete_term_count(sentence) <= 1:
        issues.append(
            ContextualKoreanIssue(
                "generic_event_without_scene",
                7,
                "generic_event",
                "구체적인 생활 묘사 없이 '생활 조건' 같은 표현만 남아 해당 장면이 흐려집니다.",
                "재물은 지급일·정산·지출 한도, 직업은 역할·평가·결정권, 관계는 연락·말투·만남으로 내려 씁니다.",
                sentence,
            )
        )

    for phrase, suggestion in WEAK_FORTUNE_REGISTER_PHRASES.items():
        if phrase in sentence:
            issues.append(
                ContextualKoreanIssue(
                    "weak_fortune_register",
                    8,
                    phrase,
                    "운세 상담 문장으로는 결론이 약하거나 설명문처럼 흘러갑니다.",
                    suggestion,
                    sentence,
                )
            )

    for pattern, marker, reason in PARTICLE_COLLISION_PATTERNS:
        if pattern.search(sentence):
            issues.append(
                ContextualKoreanIssue(
                    "particle_collision_after_rewrite",
                    9,
                    marker,
                    reason,
                    "사건명은 '업무 범위 정리', '해낸 일의 금전 보상'처럼 조사 결합이 안정적인 명사구로 정리합니다.",
                    sentence,
                )
            )

    if any(term in sentence for term in ABSTRACT_AXIS_TERMS) and any(
        predicate in sentence for predicate in ABSTRACT_PREDICATES
    ):
        if normalized_role in OPENING_ROLES or normalized_role in BASIS_ROLES or not normalized_role:
            issues.append(
                ContextualKoreanIssue(
                    "abstract_axis_as_event_subject",
                    7,
                    "abstract_axis_predicate",
                    "능력·잠재력 같은 항목명이 실제 사건의 주어처럼 쓰여 자연스러운 상담 문장으로 읽히지 않습니다.",
                    "항목명은 한 번만 밝히고 다음 문장에서는 사용자의 행동이나 사건을 주어로 둡니다.",
                    sentence,
                )
            )

    if normalized_domain and normalized_domain in DOMAIN_TERMS:
        hits = _sentence_domain_hits(sentence)
        other_hits = sum(count for name, count in hits.items() if name != normalized_domain)
        if hits.get(normalized_domain, 0) == 0 and other_hits >= 2:
            issues.append(
                ContextualKoreanIssue(
                    "domain_context_drift",
                    8,
                    normalized_domain,
                    "현재 섹션의 운세 영역과 다른 생활 묘사가 문장의 중심을 차지합니다.",
                    "다른 영역은 별도 문장으로 넘기거나 현재 영역과 연결되는 이유를 먼저 밝힙니다.",
                    sentence,
                )
            )

    if section_path and normalized_role in OPENING_ROLES and sentence.count("과") + sentence.count("와") >= 3:
        issues.append(
            ContextualKoreanIssue(
                "overloaded_opening",
                6,
                "long_opening",
                "서두 문장에 여러 판단을 한 번에 제시하면 섹션의 주제 의식이 흐려집니다.",
                "서두에는 성향 하나와 올해·선천 결론 하나만 둡니다. 세부 내용은 다음 문단으로 보냅니다.",
                sentence,
            )
        )

    return issues


def contextual_korean_summary(rows: list[tuple[str, str, str, str]]) -> dict[str, object]:
    counts: dict[str, int] = {}
    total = 0
    for text, domain, role, section_path in rows:
        for issue in contextual_korean_issues(text, domain=domain, role=role, section_path=section_path):
            total += 1
            counts[issue.issue_type] = counts.get(issue.issue_type, 0) + 1
    return {
        "policy_version": CONTEXTUAL_KOREAN_POLICY_VERSION,
        "issue_count": total,
        "issue_counts": counts,
    }
