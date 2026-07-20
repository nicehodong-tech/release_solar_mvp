"""Human-reviewable tongbyeon phrase bank for customer-facing screens.

This module is intentionally deterministic. It does not create new prose from
scratch; it chooses short, pre-reviewed fortune-service phrases from the bank
below and applies conservative surface replacements for internal labels.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class TongbyeonPhrase:
    key: str
    title: str
    line: str
    keywords: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()


SURFACE_TITLE_REPLACEMENTS: dict[str, str] = {
    "종합 기준": "나의 본질",
    "격국 변주": "인생의 굴곡",
    "중심 작용": "인생의 큰 줄기",
    "주요 영역": "운세 조언",
    "영역별 적용": "운세 조언",
    "종합 해석 기준": "나의 본질",
    "상승 연도": "좋은 시기",
    "좋은 연도": "좋은 시기",
    "주의 연도": "조심할 시기",
    "연도 범위": "인생의 굴곡",
    "격국 중심 작용": "인생의 큰 줄기",
}

SURFACE_TEXT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("상승 연도와 주의 연도", "좋은 시기와 조심할 시기"),
    ("상승 연도", "좋은 시기"),
    ("좋은 연도", "좋은 시기"),
    ("주의 연도", "조심할 시기"),
    ("격국 변주", "인생의 굴곡"),
    ("중심 작용", "중심 흐름"),
    ("종합 기준", "나의 본질"),
    ("영역별 적용", "운세 조언"),
    ("격국·월령·오행 통합", "타고난 바탕과 운의 굴곡"),
    ("십신 생극", "운의 작용"),
    ("격국의 방향과 월령의 작용", "타고난 흐름"),
    ("월령의 압박과 생극의 부담", "운에서 걸리는 부담"),
    ("생극 관계", "운의 작용"),
    ("형충의 압박", "변동과 마찰"),
    ("대운과 세운", "큰 운과 해마다 들어오는 운"),
    ("원국", "사주"),
    ("작용은 있으나", "기운은 있으나"),
    ("발동 조건", "드러나는 시점"),
    ("실제 영역 판단", "생활 속 판단"),
)

UNSAFE_SURFACE_PATTERNS: tuple[str, ...] = (
    "사망",
    "죽",
    "이혼하게",
    "파혼하게",
    "반드시 헤어",
    "중병",
    "불치",
    "임신한다",
    "아들을",
    "딸을",
)

INTERNAL_SURFACE_PATTERNS: tuple[str, ...] = (
    "격국 변주",
    "중심 작용",
    "종합 기준",
    "십신 생극",
    "생극 관계",
    "형충의 압박",
    "발동 조건",
)

TIMING_GOOD_PHRASES: tuple[TongbyeonPhrase, ...] = (
    TongbyeonPhrase(
        "foundation_opening",
        "새 기틀이 잡히는 시기",
        "미뤄졌던 일이 정리되고, 앞으로 이어질 기반이 새로 잡힙니다.",
        ("기회", "전환", "시작", "확장", "준비"),
        ("life", "career", "money"),
    ),
    TongbyeonPhrase(
        "visible_result",
        "결실이 보이는 시기",
        "그동안 쌓아온 일이 밖으로 드러나고, 평가와 보상이 따라옵니다.",
        ("성과", "평가", "보상", "결과", "성취"),
        ("career", "honor", "money"),
    ),
    TongbyeonPhrase(
        "wealth_settlement",
        "재물이 자리를 잡는 시기",
        "수입이 일시적인 흐름에 그치지 않고, 자산과 소유로 남기 쉽습니다.",
        ("재물", "자산", "수입", "계약", "명의", "소유"),
        ("money",),
    ),
    TongbyeonPhrase(
        "standing_growth",
        "입지가 넓어지는 시기",
        "맡은 역할이 커지고, 이름과 신용이 함께 올라갑니다.",
        ("직업", "역할", "권한", "승진", "명예", "평판"),
        ("career", "honor"),
    ),
    TongbyeonPhrase(
        "support_person",
        "조력자가 따르는 시기",
        "혼자 밀어붙이던 일에 도움의 손길이 붙고, 귀인이 힘을 보탭니다.",
        ("귀인", "조력", "인연", "협력", "관계"),
        ("relationship", "career", "life"),
    ),
    TongbyeonPhrase(
        "social_support_relation",
        "귀인 인연이 붙는 시기",
        "일과 생활에서 도움을 주는 사람이 들어오고, 소개와 협력이 길을 넓힙니다.",
        ("귀인", "조력", "소개", "협력", "사회", "대인"),
        ("relationship", "social", "career", "life"),
    ),
    TongbyeonPhrase(
        "family_stability_phase",
        "가정 안정이 잡히는 시기",
        "배우자, 가족, 주거 기준이 정리되며 생활 기반이 안정됩니다.",
        ("배우자", "가정", "가족", "주거", "생활", "안정"),
        ("family", "marriage"),
    ),
    TongbyeonPhrase(
        "relationship_warmth",
        "인연이 깊어지는 시기",
        "가볍게 지나가던 만남이 진지한 인연으로 굳어질 수 있습니다.",
        ("연애", "인연", "배우자", "결혼", "관계"),
        ("love", "marriage", "relationship"),
    ),
)

TIMING_CAUTION_PHRASES: tuple[TongbyeonPhrase, ...] = (
    TongbyeonPhrase(
        "document_money_check",
        "문서와 금전 관계를 살필 시기",
        "문서, 계약, 명의, 보증, 정산에서 자기 몫을 분명히 해야 합니다.",
        ("문서", "계약", "명의", "보증", "정산", "지분"),
        ("money", "career"),
    ),
    TongbyeonPhrase(
        "loss_gossip_guard",
        "손재와 구설을 조심할 시기",
        "작은 말과 가벼운 약속이 손실이나 평판 문제로 번질 수 있습니다.",
        ("손실", "구설", "관계", "말", "평판", "오해"),
        ("relationship", "honor", "money"),
    ),
    TongbyeonPhrase(
        "overreach_guard",
        "과욕을 경계할 시기",
        "분수보다 큰 결정을 서두르면 얻은 것보다 잃는 것이 커집니다.",
        ("투자", "확장", "사업", "무리", "과욕", "위험"),
        ("money", "career", "business"),
    ),
    TongbyeonPhrase(
        "authority_pressure",
        "책임이 무거워지는 시기",
        "맡은 일은 커지지만 권한과 보상이 늦게 따라올 수 있습니다.",
        ("책임", "직업", "권한", "상사", "평가", "부담"),
        ("career", "honor"),
    ),
    TongbyeonPhrase(
        "family_boundary",
        "가족과 재산의 경계를 살필 시기",
        "가족 일과 내 재산이 섞이면 책임의 범위가 커질 수 있습니다.",
        ("가족", "재산", "상속", "주거", "생활비", "배우자"),
        ("family", "marriage", "money"),
    ),
    TongbyeonPhrase(
        "family_responsibility_guard",
        "배우자·가정 책임을 살필 시기",
        "배우자, 가족, 주거, 생활비 문제가 현실 부담으로 커질 수 있습니다.",
        ("배우자", "가정", "가족", "주거", "생활비", "책임"),
        ("family", "marriage"),
    ),
    TongbyeonPhrase(
        "relationship_reputation_guard",
        "관계 구설을 조심할 시기",
        "가까운 관계나 사회적 인연에서 말과 체면 문제가 커지기 쉽습니다.",
        ("대인", "귀인", "사회", "관계", "구설", "체면", "말"),
        ("relationship", "social", "honor"),
    ),
    TongbyeonPhrase(
        "marriage_decision_guard",
        "결혼 결정을 살필 시기",
        "감정이 있어도 가족, 주거, 생활비 문제가 결정의 부담으로 올라올 수 있습니다.",
        ("결혼", "혼인", "배우자", "가족", "주거", "생활비", "부담"),
        ("marriage", "family"),
    ),
    TongbyeonPhrase(
        "relationship_fracture",
        "연애 오해를 조심할 시기",
        "연락과 표현이 어긋나면 가까운 관계에서 서운함이 커질 수 있습니다.",
        ("연애", "관계", "배우자", "말", "감정", "체면"),
        ("love", "marriage", "relationship"),
    ),
)

SUMMARY_PHRASES: tuple[TongbyeonPhrase, ...] = (
    TongbyeonPhrase(
        "life_foundation",
        "기틀을 세워 결실을 보는 사주",
        "초반에는 방향을 잡는 데 시간이 걸리지만, 중후반으로 갈수록 자기 기반이 뚜렷해집니다.",
        ("기반", "결실", "중년", "말년"),
    ),
    TongbyeonPhrase(
        "public_credit",
        "신용과 입지로 운을 여는 사주",
        "말보다 책임 있는 행동이 운을 키우며, 명예와 재물도 신용 위에서 따라옵니다.",
        ("신용", "입지", "명예", "책임"),
    ),
    TongbyeonPhrase(
        "skill_to_wealth",
        "재주가 재물로 이어지는 사주",
        "가진 재주를 꾸준히 밖으로 내놓을수록 수입과 평판이 함께 커집니다.",
        ("재주", "재물", "성과", "평판"),
    ),
    TongbyeonPhrase(
        "boundary_life",
        "몫과 경계를 분명히 해야 복이 머무는 사주",
        "사람을 잘 만나도 돈과 책임의 기준이 흐려지면 손재와 구설이 따르기 쉽습니다.",
        ("돈", "책임", "사람", "손재", "구설"),
    ),
)


def tongbyeon_surface_title(value: Any) -> str:
    text = str(value or "").strip()
    return SURFACE_TITLE_REPLACEMENTS.get(text, text)


def tongbyeon_surface_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return ""
    for source, target in SURFACE_TEXT_REPLACEMENTS:
        text = text.replace(source, target)
    return text


def _haystack(candidate: dict[str, Any] | None) -> str:
    if not isinstance(candidate, dict):
        return ""
    values: list[str] = []
    for key in (
        "title",
        "focus",
        "focusLine",
        "domainLabel",
        "domain_label",
        "decisionLine",
        "productLine",
        "summary",
        "body",
    ):
        value = candidate.get(key)
        if isinstance(value, str):
            values.append(value)
    return " ".join(values)


def timing_candidate_age(candidate: dict[str, Any] | None) -> int | None:
    if not isinstance(candidate, dict):
        return None
    raw_age = candidate.get("age")
    if isinstance(raw_age, int):
        return raw_age
    if isinstance(raw_age, str) and raw_age.strip().isdigit():
        return int(raw_age.strip())
    for key in ("ageLabel", "age_label"):
        value = str(candidate.get(key) or "")
        match = re.search(r"(\d+)세", value)
        if match:
            return int(match.group(1))
    return None


def timing_lifecycle_category(candidate: dict[str, Any] | None, *, kind: str = "good") -> str:
    if not isinstance(candidate, dict):
        return ""
    age = timing_candidate_age(candidate)
    domain = str(candidate.get("domain") or "").strip()
    haystack = _haystack(candidate)
    compact = haystack.replace(" ", "")

    if domain == "money" or any(token in compact for token in ("재물", "자산", "수입", "계약", "명의", "금전")):
        return "재물"
    if domain == "career" or any(token in compact for token in ("직업", "직책", "권한", "평가", "승진", "업무")):
        return "직업"
    if domain == "honor" or any(token in compact for token in ("명예", "평판", "신용")):
        return "명예"
    if domain == "love":
        if age is not None and age >= 45:
            return "대인·귀인" if kind == "good" else "대인관계"
        return "연애·인연"
    if domain == "marriage":
        if age is not None and age >= 45:
            return "배우자·가정"
        return "혼인·배우자"

    marriage_signal = domain == "marriage" or any(
        token in compact for token in ("결혼", "혼인", "배우자", "가정", "가족", "주거", "생활비")
    )
    love_signal = domain in {"love", "relationship"} or any(
        token in compact for token in ("연애", "인연", "만남", "호감", "관계")
    )

    if marriage_signal:
        if age is not None and age >= 45:
            return "배우자·가정"
        return "혼인·배우자"
    if love_signal:
        if age is not None and age >= 45:
            return "대인·귀인" if kind == "good" else "대인관계"
        return "연애·인연"
    return ""


def _phrase_by_key(phrases: tuple[TongbyeonPhrase, ...], key: str) -> TongbyeonPhrase | None:
    return next((phrase for phrase in phrases if phrase.key == key), None)


def _score_phrase(phrase: TongbyeonPhrase, haystack: str) -> int:
    score = 0
    compact = haystack.replace(" ", "")
    for keyword in phrase.keywords:
        if keyword and keyword.replace(" ", "") in compact:
            score += 3
    for domain in phrase.domains:
        if domain and domain in compact:
            score += 1
    return score


def select_tongbyeon_timing_phrase(candidate: dict[str, Any] | None, *, kind: str) -> TongbyeonPhrase:
    phrases = TIMING_GOOD_PHRASES if kind == "good" else TIMING_CAUTION_PHRASES
    category = timing_lifecycle_category(candidate, kind=kind)
    preferred_key = ""
    if kind == "good":
        if category == "대인·귀인":
            preferred_key = "social_support_relation"
        elif category == "연애·인연":
            preferred_key = "relationship_warmth"
        elif category == "배우자·가정":
            preferred_key = "family_stability_phase"
    else:
        if category == "대인관계":
            preferred_key = "relationship_reputation_guard"
        elif category == "연애·인연":
            preferred_key = "relationship_fracture"
        elif category == "혼인·배우자":
            preferred_key = "marriage_decision_guard"
        elif category == "배우자·가정":
            preferred_key = "family_responsibility_guard"
    if preferred_key:
        preferred = _phrase_by_key(phrases, preferred_key)
        if preferred:
            return preferred
    haystack = _haystack(candidate)
    ranked = sorted(phrases, key=lambda phrase: (-_score_phrase(phrase, haystack), phrase.key))
    return ranked[0]


def compose_tongbyeon_timing_sentence(candidate: dict[str, Any] | None, *, kind: str) -> str:
    phrase = select_tongbyeon_timing_phrase(candidate, kind=kind)
    return phrase.line


def select_tongbyeon_summary_phrase(values: list[Any] | tuple[Any, ...]) -> TongbyeonPhrase:
    haystack = " ".join(str(value or "") for value in values)
    ranked = sorted(SUMMARY_PHRASES, key=lambda phrase: (-_score_phrase(phrase, haystack), phrase.key))
    return ranked[0]


def tongbyeon_warning_counts(text: str) -> dict[str, int]:
    return {
        "unsafe_prediction_count": sum(1 for pattern in UNSAFE_SURFACE_PATTERNS if pattern in text),
        "internal_surface_leak_count": sum(1 for pattern in INTERNAL_SURFACE_PATTERNS if pattern in text),
    }
