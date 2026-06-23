"""Deterministic preview rendering for event packets.

This is not the final product sentence layer. It only proves that the structured
packet has enough material to become customer-facing Korean prose later.
"""

from __future__ import annotations

from .models import EventPacket
from .refined_interpretation_values import REFINED_EVENT_DISPLAY_BY_TYPE


DOMAIN_LABELS = {
    "money": "재물",
    "career": "직업",
    "love": "연애",
    "marriage": "결혼",
}

EVENT_LABELS = {
    event_type: payload["label"]
    for event_type, payload in REFINED_EVENT_DISPLAY_BY_TYPE.items()
}

CONFIDENCE_LABELS = {
    "high": "강하게 볼 수 있습니다",
    "medium_high": "가능성이 높은 편입니다",
    "medium": "가능성이 비교적 분명합니다",
    "low": "보조 신호로 봅니다",
    "restricted": "단정하기보다 관리 신호로 봅니다",
}

RISK_LABELS = {
    "none": "특별한 반대 신호는 크지 않습니다",
    "mild": "다만 반대 신호가 일부 섞여 있습니다",
    "strong": "다만 반대 신호가 강하므로 관리가 필요합니다",
}

PHASE_LABELS = {
    "contact": "접촉이 늘어나는 국면",
    "proposal": "제안과 협의가 들어오는 국면",
    "conflict": "조정과 마찰이 함께 강해지는 국면",
    "contract": "계약과 약속을 다루는 국면",
    "income": "수입과 성과가 움직이는 국면",
    "settlement": "정리와 결정이 필요한 국면",
    "rest": "속도를 낮추고 정비하는 국면",
    "unknown": "상황을 관찰해야 하는 국면",
}


def _format_date(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    return value[:10]


def _timing_summary(packet: EventPacket) -> str:
    if not packet.timing_windows:
        return packet.period_label
    parts: list[str] = []
    for window in packet.timing_windows[:3]:
        start = _format_date(window.get("start_datetime"))
        end = _format_date(window.get("end_datetime"))
        phase = PHASE_LABELS.get(str(window.get("monthly_phase")), "상황을 관찰해야 하는 국면")
        if start and end:
            parts.append(f"{start}~{end} {phase}")
        else:
            parts.append(phase)
    return ", ".join(parts)


def render_event_preview(packet: EventPacket) -> str:
    domain = DOMAIN_LABELS[packet.domain]
    event = EVENT_LABELS.get(packet.sub_event_type, packet.sub_event_type)
    confidence = {
        "high": "강하게 나타납니다",
        "medium_high": "뚜렷하게 나타납니다",
        "medium": "가능성이 보입니다",
        "low": "보조 신호로 봅니다",
        "restricted": "판정을 보류해야 하는 신호입니다",
    }[packet.confidence]
    risk = {
        "none": "크게 꺾는 변수는 약합니다",
        "mild": "중간에 조율할 문제가 있습니다",
        "strong": "그 과정에서 비용과 부담도 커집니다",
    }[packet.conflict_status]
    timing = _timing_summary(packet)

    return (
        f"{packet.period_label}년 {domain}운은 {event}입니다. "
        f"{packet.primary_scene_sentence}. "
        f"강한 시점은 {timing}입니다. "
        f"{risk}. 핵심은 {packet.main_action}입니다."
    )
