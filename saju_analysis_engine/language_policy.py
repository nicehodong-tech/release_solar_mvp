"""Customer-language policies used by report rendering.

This module keeps wording decisions that are likely to change during product
patches away from the rendering orchestration layer. Domain scoring should stay
in the analysis modules; this file only translates already-scored traits into
customer-facing language.
"""

from __future__ import annotations

from typing import Any

RELATIONSHIP_AXIS_CONTEXTS = {
    "대인 영향력": "호감이 생기고 관계가 시작되는 과정",
    "관계 안정성": "가까워진 관계를 오래 유지하는 과정",
    "표현 전달력": "생각과 감정을 전달하는 과정",
    "관계 경계 설정력": "가까운 사이에서도 각자의 책임 범위를 분명히 하는 과정",
    "갈등 회복력": "부딪힌 뒤 다시 대화와 행동을 정리하는 과정",
    "위기 회복력": "문제가 생긴 뒤 관계와 생활을 다시 안정시키는 과정",
    "결혼 안정성": "애정이 생활의 약속으로 이어지는 과정",
    "가족 책임감": "가까운 사람 앞에서 책임을 행동으로 지키는 과정",
    "결정 지속성": "한 번 정한 약속을 흔들리지 않게 이어 가는 과정",
    "현실 설계력": "생활 조건과 역할 분담을 현실적으로 정하는 과정",
    "자산 유지력": "공동 생활의 재정 기준을 안정시키는 과정",
    "돈을 대하는 태도": "돈과 생활비 문제를 대화로 정리하는 과정",
}

RELATIONSHIP_AXIS_BRIEF_CONTEXTS = {
    "대인 영향력": "호감 형성",
    "관계 안정성": "관계 유지",
    "표현 전달력": "감정 표현",
    "관계 경계 설정력": "거리 조절",
    "갈등 회복력": "갈등 회복",
    "위기 회복력": "위기 이후의 안정",
    "결혼 안정성": "생활 합의",
    "가족 책임감": "가족 책임",
    "결정 지속성": "약속 유지",
    "현실 설계력": "생활 설계",
    "자산 유지력": "공동 재정",
    "돈을 대하는 태도": "생활비 대화",
}

TIMING_PHASE_LABELS_BY_DOMAIN = {
    "money": {
        "contact": "새 제안이나 거래 접점이 늘어나는 상황",
        "proposal": "보상 기준과 정산 협의를 하게 되는 상황",
        "conflict": "돈의 기준을 두고 마찰이 커지는 상황",
        "contract": "계약과 약속을 다루는 상황",
        "income": "수입과 성과가 금액으로 정리되는 상황",
        "settlement": "돈의 정리와 결정이 함께 올라오는 상황",
        "rest": "지출 속도를 낮추고 재정을 정비하는 상황",
        "unknown": "금전 기준이 새로 확인되는 상황",
    },
    "career": {
        "contact": "새 역할이나 업무 접점이 늘어나는 상황",
        "proposal": "제안과 업무 협의를 하게 되는 상황",
        "conflict": "역할을 두고 마찰이 커지는 상황",
        "contract": "계약과 업무 약속을 다루는 상황",
        "income": "성과와 평가가 맡는 역할로 이어지는 상황",
        "settlement": "일의 기준과 방향이 다시 정리되는 상황",
        "rest": "업무 속도를 낮추고 기준을 정비하는 상황",
        "unknown": "업무 기준이 새로 확인되는 상황",
    },
    "love": {
        "contact": "만남과 연락 접점이 늘어나는 상황",
        "proposal": "관계의 방향을 두고 대화하게 되는 상황",
        "conflict": "감정을 두고 마찰이 커지는 상황",
        "contract": "약속과 관계 기준을 조율하는 상황",
        "income": "호감과 반응이 구체적으로 확인되는 상황",
        "settlement": "관계의 방향이 다시 정리되는 상황",
        "rest": "관계 속도를 낮추고 감정을 정비하는 상황",
        "unknown": "관계 반응이 새로 확인되는 상황",
    },
    "marriage": {
        "contact": "가족과 생활 조건의 접점이 늘어나는 상황",
        "proposal": "결혼 의사와 생활 협의를 하게 되는 상황",
        "conflict": "가족 책임을 두고 마찰이 커지는 상황",
        "contract": "약속과 생활 기준을 다루는 상황",
        "income": "생활 조건과 현실 계획이 논의되는 상황",
        "settlement": "결혼 조건과 역할이 다시 정리되는 상황",
        "rest": "결정 속도를 낮추고 생활 기준을 정비하는 상황",
        "unknown": "결혼 기준이 새로 확인되는 상황",
    },
}

TIMING_SCOPE_SENTENCES_BY_DOMAIN = {
    "money": {
        "quarter": "몇 달에 걸쳐 수입 기준과 지출 판단이 반복됩니다. 한 번 들어오는 돈보다 이후의 쓰임을 더 크게 봅니다.",
        "month": "한 달 단위로 금전 결정이 빨라집니다. 계약 기준도 또렷해집니다.",
    },
    "career": {
        "quarter": "몇 달에 걸쳐 역할 문제가 반복됩니다. 한 번의 업무 변화보다 이후의 책임 범위를 더 크게 봅니다.",
        "month": "한 달 단위로 일의 조건이 결정됩니다. 평가 일정이 먼저 움직입니다.",
    },
    "love": {
        "quarter": "몇 달에 걸쳐 만남의 방식이 반복됩니다. 한 번의 연락보다 이후의 태도가 관계를 정합니다.",
        "month": "한 달 단위로 관계 반응이 빨라집니다. 연락 방식이 먼저 달라집니다.",
    },
    "marriage": {
        "quarter": "몇 달에 걸쳐 생활 조건이 반복됩니다. 한 번의 약속보다 이후의 책임 분담을 더 크게 봅니다.",
        "month": "한 달 단위로 결혼 기준을 논의합니다. 가족 협의가 먼저 움직입니다.",
    },
}

TIMING_INTENSITY_SENTENCES_BY_DOMAIN = {
    "money": {
        "very": "계약과 지출 결정이 바로 움직이는 힘이 매우 강합니다.",
        "clear": "계약과 지출 판단이 곧 결정으로 옮겨집니다.",
        "moderate": "금전 판단이 평소보다 또렷해집니다.",
        "low": "작은 기준 변화가 돈의 판단에 영향을 줍니다.",
    },
    "career": {
        "very": "업무 배분이나 평가 조정으로 이어질 힘이 매우 강합니다.",
        "clear": "업무 배분이나 평가 조정으로 이어질 힘이 큰 편입니다.",
        "moderate": "일의 조건을 평소보다 더 구체적으로 따집니다.",
        "low": "일정과 책임 범위의 작은 변화가 직업 판단에 영향을 줍니다.",
    },
    "love": {
        "very": "연락, 만남, 감정 표현의 변화가 매우 뚜렷합니다.",
        "clear": "연락, 만남, 감정 표현의 변화가 뚜렷합니다.",
    "moderate": "관계 반응이 평소보다 조금 더 세심하게 확인됩니다.",
        "low": "작은 말투와 연락 간격이 관계 판단에 영향을 줍니다.",
    },
    "marriage": {
        "very": "가족 협의, 주거, 역할 분담 논의로 이어질 힘이 매우 강합니다.",
        "clear": "가족 협의, 주거, 역할 분담 논의로 이어질 힘이 큰 편입니다.",
    "moderate": "생활 기준과 책임 범위가 평소보다 자세히 확인됩니다.",
        "low": "생활 기준과 책임 범위의 작은 차이가 결혼 판단에 영향을 줍니다.",
    },
}

TIMING_INTENSITY_FALLBACK_SENTENCES = {
    "very": "구체적인 선택과 결정으로 이어질 힘이 매우 강합니다.",
    "clear": "구체적인 선택과 결정으로 이어질 힘이 큰 편입니다.",
    "moderate": "살펴볼 문제가 평소보다 또렷합니다.",
    "low": "작은 변화라도 선택 기준을 확인하는 데 의미가 있습니다.",
}


def money_career_axis_display(label: str, percentile_label: str) -> str:
    """Render a money/career axis with percentile wording and soft buffering."""
    if percentile_label.startswith("상위"):
        return f"{label}은 {percentile_label}입니다"
    if percentile_label == "평균권":
        return f"{label}은 평균권입니다"
    if percentile_label == "평균권 하단":
        return f"{label}은 신중하게 다뤄야 하는 편입니다. 관리 기준을 세우면 보완됩니다"
    return f"{label}은 아직 크게 강한 영역은 아닙니다"


def money_career_axis_brief_display(label: str, percentile_label: str) -> str:
    """Render a short mobile-safe money/career axis phrase."""
    if percentile_label.startswith("상위"):
        return f"{label}은 {percentile_label}입니다"
    if percentile_label == "평균권":
        return f"{label}은 평균권"
    return f"{label}은 관리 기준으로 보완됩니다"


def relationship_axis_display(axis: dict[str, Any], label: str) -> str:
    """Render love/marriage axis language as relationship scenes, not ranks."""
    score = int(axis.get("score") or 50)
    context = RELATIONSHIP_AXIS_CONTEXTS.get(label, "관계의 실제 장면")
    moderate = {
        "대인 영향력": "대인 영향력은 호감이 생기는 자리에서 자연스럽게 강해집니다.",
        "관계 안정성": "관계 안정성은 가까워진 관계를 오래 유지하는 성향입니다.",
        "표현 전달력": "표현 전달력은 마음을 전하는 과정에서 서서히 커집니다.",
        "관계 경계 설정력": "관계 경계 설정력은 가까운 사이에서 거리를 맞추는 성향입니다.",
        "갈등 회복력": "갈등 회복력은 다시 대화하는 과정에서 커집니다.",
        "결혼 안정성": "결혼 안정성은 애정이 생활의 약속으로 옮겨질 때 강해집니다.",
        "가족 책임감": "가족 책임감은 가까운 사람을 챙기는 태도입니다.",
    }
    low = {
        "대인 영향력": "대인 영향력은 처음 관계가 시작될 때 조심스럽게 커집니다.",
        "관계 안정성": "관계 안정성은 가까워진 뒤 유지 과정에서 피로가 생기기 쉽습니다.",
        "표현 전달력": "표현 전달력은 마음이 있어도 늦어지기 쉽습니다.",
        "관계 경계 설정력": "관계 경계 설정력은 가까운 사이에서 거리를 맞추는 일이 어려워지기 쉽습니다.",
        "갈등 회복력": "갈등 회복력은 불편함이 생긴 뒤 늦게 커집니다.",
        "결혼 안정성": "결혼 안정성은 생활의 약속을 늦게 정할수록 결정이 무거워집니다.",
        "가족 책임감": "가족 책임감은 책임이 한쪽으로 몰릴 때 부담이 커집니다.",
    }
    if score >= 64:
        return f"{label}은 {context}에서 분명한 장점입니다."
    if score >= 46:
        return moderate.get(label, f"{label}은 {context}에서 자연스럽게 강해집니다.")
    return low.get(label, f"{label}은 {context}에서 피로가 생기기 쉽습니다.")


def relationship_axis_brief_display(label: str, score: int | None = None) -> str:
    """Render a compact relationship-axis phrase for mobile cards."""
    context = RELATIONSHIP_AXIS_BRIEF_CONTEXTS.get(label, "관계의 실제 장면")
    moderate = {
        "대인 영향력": "대인 영향력은 호감이 생기는 자리에서 강해집니다",
        "관계 안정성": "관계 안정성은 가까운 관계를 오래 유지하는 성향입니다",
        "표현 전달력": "표현 전달력은 마음을 전하는 과정에서 커집니다",
        "관계 경계 설정력": "관계 경계 설정력은 거리를 맞추는 성향입니다",
        "갈등 회복력": "갈등 회복력은 다시 대화하는 과정에서 커집니다",
        "결혼 안정성": "결혼 안정성은 생활 약속을 오래 지키는 성향입니다",
        "가족 책임감": "가족 책임감은 가까운 사람을 챙기는 태도입니다",
    }
    if score is None:
        return f"{label}은 {context}에서 따로 살펴볼 항목"
    if score >= 64:
        return f"{label}은 {context}에서 강점이 됩니다"
    if score >= 46:
        return moderate.get(label, f"{label}은 {context}에서 자연스럽게 강해집니다")
    return f"{label}은 {context}에서 피로가 생깁니다"


def relationship_axis_customer_sentence(axis: dict[str, Any], label: str) -> str:
    """Explain love/marriage axes through concrete relational behavior."""
    score = int(axis.get("score") or 50)
    context = RELATIONSHIP_AXIS_CONTEXTS.get(label, "관계의 실제 장면")
    strong_sentences = {
        "대인 영향력": "당신은 처음 만난 사람에게 호감을 남기는 편입니다. 관계가 시작될 때 신뢰를 먼저 얻습니다.",
        "관계 안정성": "당신은 가까워진 관계를 비교적 안정적으로 이어 갑니다. 연락 방식이 편해질수록 감정 전달도 자연스러워집니다. 책임 조율이 분명하면 관계가 오래 안정됩니다.",
        "표현 전달력": "당신은 마음을 표현으로 옮기는 능력이 있습니다. 상대는 당신의 진심을 비교적 분명하게 느낍니다.",
        "갈등 회복력": "당신은 부딪힌 뒤 다시 대화하는 편입니다. 관계가 틀어져도 회복의 실마리를 찾습니다.",
        "결혼 안정성": "당신은 애정을 생활의 약속으로 옮기는 성향이 있습니다. 결혼 뒤에도 관계를 유지하려는 책임감이 강합니다.",
        "가족 책임감": "당신은 가까운 사람을 책임지려는 마음이 강합니다. 가족 문제 앞에서 쉽게 물러서지 않습니다.",
        "현실 설계력": "당신은 생활의 기준을 세우는 능력이 있습니다. 결혼 문제를 감정만으로 결정하지 않습니다.",
        "자산 유지력": "당신은 공동 재정을 지키는 감각이 있습니다. 결혼 생활에서 돈의 기준을 쉽게 흐리지 않습니다.",
    }
    moderate_sentences = {
        "대인 영향력": "처음에는 호감이 생기지만, 가까워질수록 관계의 속도에 기복이 생깁니다. 처음의 호감이 오래가려면 서로 원하는 속도를 말해야 합니다.",
        "관계 안정성": "가까워진 뒤에 감정의 기복이 생깁니다. 오래 만날수록 표현 방식을 더 크게 봅니다.",
        "표현 전달력": "마음을 전하는 방식은 상황에 따라 달라집니다. 마음이 있어도 말이 늦어지면 오해가 생깁니다.",
        "갈등 회복력": "갈등을 풀어 가는 힘은 대화의 시점에 따라 달라집니다. 늦게 풀수록 불편함이 오래 남습니다.",
        "결혼 안정성": "결혼 문제에서는 생활 기준에 따라 기복이 생깁니다. 애정이 깊어도 생활비와 책임 분담이 늦게 정리되면 부담이 커집니다.",
        "가족 책임감": "가족 문제는 상황에 따라 무겁게 다가옵니다. 챙기려는 마음이 커질수록 부담도 함께 커집니다.",
        "현실 설계력": "생활을 정리하는 힘은 대화의 순서에 따라 달라집니다. 생활 기준을 늦게 꺼내면 결정이 흔들립니다.",
        "자산 유지력": "공동 재정은 지출 기준에서 기복이 생깁니다. 공동 재정의 기준이 흐리면 불안이 커집니다.",
    }
    low_sentences = {
        "대인 영향력": "당신은 관계가 시작될 때 조심스러워집니다. 상대의 반응을 확인하기 전에는 마음을 쉽게 열지 않습니다.",
        "관계 안정성": "당신은 가까운 관계에서 피로를 쉽게 느낍니다. 마음이 깊어도 생활 기준이 어긋나면 불편함이 반복됩니다.",
        "표현 전달력": "당신은 마음을 표현하는 데 시간이 걸립니다. 상대는 그 침묵을 거리감으로 느끼기 쉽습니다.",
        "갈등 회복력": "당신은 갈등 뒤에 말을 아끼는 편입니다. 불편함을 오래 두면 관계 회복이 늦어집니다.",
        "결혼 안정성": "당신은 결혼 문제에서 생활 조건을 늦게 정하면 부담을 크게 느낍니다. 애정만으로는 결정을 끝내기 어렵습니다.",
        "가족 책임감": "당신은 가족 책임 앞에서 부담을 크게 느낍니다. 책임이 한쪽으로 몰리면 마음이 빨리 지칩니다.",
        "현실 설계력": "당신은 생활 기준을 정하는 과정에서 고민이 길어집니다. 결정을 미루면 관계의 피로가 커집니다.",
        "자산 유지력": "당신은 공동 재정에서 불안을 느끼기 쉽습니다. 돈의 기준이 늦게 정해지면 신뢰가 흔들립니다.",
    }
    if score >= 64:
        return strong_sentences.get(label, f"당신은 {context}에서 안정적입니다. 가까운 관계에서도 태도가 쉽게 흔들리지 않습니다.")
    if score >= 46:
        return moderate_sentences.get(label, f"당신의 {label}은 {context}에서 기복이 생깁니다. 관계가 가까워질수록 확인 대화가 늘어납니다.")
    return low_sentences.get(label, f"당신의 {label}은 {context}에서 부담이 됩니다. 가까운 관계일수록 피로가 쌓입니다.")


def timing_phase_label(monthly_phase: str, domain: str) -> str:
    """Translate a shared monthly phase into a domain-specific life scene."""
    domain_labels = TIMING_PHASE_LABELS_BY_DOMAIN.get(domain, {})
    return domain_labels.get(monthly_phase, domain_labels.get("unknown", "상황이 새로 확인되는 시기"))


def timing_window_sentence(start: str, end: str, scope: str, phase: str, intensity: int, domain: str = "") -> str:
    """Render premium timing windows in a warmer, customer-readable register."""
    phase_scene = phase.replace("국면", "상황")
    scope_sentence = _timing_scope_sentence(scope, domain)
    intensity_sentence = _timing_intensity_sentence(intensity, domain)
    opening_sentence = _timing_opening_sentence(start, end, scope, phase_scene, intensity, domain)
    return f"{opening_sentence} {scope_sentence} {intensity_sentence}"


def _timing_intensity_sentence(intensity: int, domain: str) -> str:
    level = _timing_intensity_level(intensity)
    return TIMING_INTENSITY_SENTENCES_BY_DOMAIN.get(domain, TIMING_INTENSITY_FALLBACK_SENTENCES).get(
        level,
        TIMING_INTENSITY_FALLBACK_SENTENCES[level],
    )


def _timing_intensity_level(intensity: int) -> str:
    if intensity >= 78:
        return "very"
    if intensity >= 68:
        return "clear"
    if intensity >= 58:
        return "moderate"
    return "low"


def _timing_opening_sentence(
    start: str,
    end: str,
    scope: str,
    phase_scene: str,
    intensity: int,
    domain: str,
) -> str:
    prefix = f"{start}부터 {end}까지는" if start and end else "이 시기에는"
    focus = _timing_focus_phrase(intensity)
    tail = _timing_domain_tail(scope, domain)
    return f"{prefix} {phase_scene}{_subject_particle(phase_scene)} {focus}. {tail}"


def _subject_particle(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "이"
    last = text[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "이" if (code - 0xAC00) % 28 else "가"
    return "이"


def _timing_focus_phrase(intensity: int) -> str:
    if intensity >= 78:
        return "가장 뚜렷합니다"
    if intensity >= 68:
        return "분명합니다"
    if intensity >= 58:
        return "눈에 띕니다"
    return "조금씩 보입니다"


def _timing_visibility_phrase(intensity: int) -> str:
    if intensity >= 78:
        return "매우 강하게"
    if intensity >= 68:
        return "분명하게"
    if intensity >= 58:
        return "뚜렷하게"
    return "조금씩"


def _timing_domain_tail(scope: str, domain: str) -> str:
    domain_tails = {
        "money": {
            "quarter": "돈의 기준을 다시 점검하게 됩니다.",
            "month": "계약과 정산을 다시 살피게 됩니다. 지출 결정도 빨라집니다.",
        },
        "career": {
            "quarter": "업무 범위와 평가 기준을 다시 정리하게 됩니다.",
            "month": "평가 일정, 업무 배분, 책임 조정이 뒤따릅니다.",
        },
        "love": {
            "quarter": "연락 방식과 만남의 태도를 다시 살피게 됩니다.",
            "month": "만남, 연락, 감정 표현에서 먼저 보입니다.",
        },
        "marriage": {
            "quarter": "생활 조건과 가족 협의를 다시 정리하게 됩니다.",
            "month": "가족 협의가 시작됩니다. 주거와 재정 계획도 함께 움직입니다. 역할 분담도 다시 말하게 됩니다.",
        },
    }
    if domain in domain_tails and scope in domain_tails[domain]:
        return domain_tails[domain][scope]
    if scope == "quarter":
        return "같은 주제가 이어지며 선택 기준을 다시 세우게 됩니다."
    if scope == "month":
        return "구체적인 약속과 결정이 뒤따릅니다."
    return "해당 시기의 선택 기준을 다시 세우게 됩니다."


def _timing_scope_sentence(scope: str, domain: str) -> str:
    domain_sentences = TIMING_SCOPE_SENTENCES_BY_DOMAIN.get(domain, {})
    if scope in domain_sentences:
        return domain_sentences[scope]
    return {
        "quarter": "몇 달에 걸쳐 같은 주제가 반복될 수 있으므로, 한 번의 사건보다 이어지는 변화까지 함께 보아야 합니다.",
        "month": "한 달 단위로 사건이 실제 결정으로 이어지기 쉬우므로, 약속·계약·만남·역할 조정처럼 날짜가 남는 일을 함께 보아야 합니다.",
    }.get(scope, "전체 시기 안에서 특별히 주의를 기울일 필요가 있는 기간입니다.")
