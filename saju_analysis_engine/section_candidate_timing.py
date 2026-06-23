"""Timing adapter for premium candidate outline blocks.

Candidate section prose remains generic. This adapter reads event packets from
the analysis result and creates chart-specific timing additions for outline
blocks that explicitly require timing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import AnalysisResult, EventPacket
from .section_candidate_outline import PremiumCandidateOutline, build_premium_candidate_outline


CANDIDATE_TIMING_ADAPTER_VERSION = "candidate_timing_adapter_v1"


@dataclass(frozen=True)
class CandidateTimingAttachment:
    candidate_key: str
    timing_kind: str
    year_label: str
    korean_age_label: str
    sentences: list[str] = field(default_factory=list)
    evidence_packet_ids: list[str] = field(default_factory=list)
    evidence_terms: list[str] = field(default_factory=list)
    score: int = 0


def build_candidate_timing_attachments(
    analysis: AnalysisResult,
    outline: PremiumCandidateOutline | None = None,
    *,
    period_limit: int = 3,
) -> list[CandidateTimingAttachment]:
    outline = outline or build_premium_candidate_outline(analysis)
    attachments: list[CandidateTimingAttachment] = []
    for block in outline.blocks:
        if not block.timing_attachment_required:
            continue
        packets = _packets_for_candidate(block.candidate_key, analysis, period_limit)
        if not packets:
            continue
        attachments.append(_build_attachment(block.candidate_key, packets, analysis))
    return attachments


def candidate_timing_by_key(
    analysis: AnalysisResult,
    outline: PremiumCandidateOutline | None = None,
) -> dict[str, CandidateTimingAttachment]:
    return {
        attachment.candidate_key: attachment
        for attachment in build_candidate_timing_attachments(analysis, outline)
    }


def validate_candidate_timing_attachments(analysis: AnalysisResult) -> list[str]:
    outline = build_premium_candidate_outline(analysis)
    attachments = candidate_timing_by_key(analysis, outline)
    issues: list[str] = []
    required_keys = [
        block.candidate_key
        for block in outline.blocks
        if block.timing_attachment_required
    ]
    for key in required_keys:
        attachment = attachments.get(key)
        if attachment is None:
            issues.append(f"{key}: missing timing attachment")
            continue
        if not attachment.year_label:
            issues.append(f"{key}: missing year label")
        if not attachment.korean_age_label:
            issues.append(f"{key}: missing Korean age label")
        if len(attachment.sentences) < 2:
            issues.append(f"{key}: timing prose too thin")
        if any(_has_forbidden_timing_phrase(sentence) for sentence in attachment.sentences):
            issues.append(f"{key}: forbidden timing phrase")
        if not attachment.evidence_packet_ids:
            issues.append(f"{key}: missing evidence packets")
    return issues


def _packets_for_candidate(
    candidate_key: str,
    analysis: AnalysisResult,
    period_limit: int,
) -> list[EventPacket]:
    packets = [packet for packet in analysis.event_packets if _packet_year(packet) is not None]
    if candidate_key == "accumulated_work_gets_recognized_period":
        filtered = [packet for packet in packets if packet.domain in {"money", "career"}]
        return _top_unique_year_packets(
            filtered,
            key=lambda packet: (
                packet.opportunity_score * 1.15
                + packet.event_probability_score
                + packet.change_score * 0.35
                - packet.risk_score * 0.2
            ),
            limit=period_limit,
        )
    if candidate_key == "unresolved_promises_return_caution_period":
        filtered = [
            packet
            for packet in packets
            if packet.domain in {"money", "career", "love", "marriage"}
        ]
        return _top_unique_year_packets(
            filtered,
            key=lambda packet: (
                packet.risk_score * 1.2
                + packet.change_score
                + packet.event_probability_score * 0.65
            ),
            limit=period_limit,
        )
    if candidate_key == "direction_clarifies_after_break":
        return _top_unique_year_packets(
            packets,
            key=lambda packet: (
                packet.change_score * 1.2
                + packet.risk_score * 0.75
                + packet.event_probability_score * 0.45
            ),
            limit=period_limit,
        )
    if candidate_key == "later_life_settles_better_than_early":
        filtered = [packet for packet in packets if packet.domain in {"money", "career", "marriage"}]
        return _top_unique_year_packets(
            filtered,
            key=lambda packet: (
                packet.event_probability_score
                + packet.opportunity_score
                + packet.change_score * 0.25
                - packet.risk_score * 0.15
            ),
            limit=period_limit,
        )
    return _top_unique_year_packets(
        packets,
        key=lambda packet: packet.event_probability_score,
        limit=period_limit,
    )


def _build_attachment(
    candidate_key: str,
    packets: list[EventPacket],
    analysis: AnalysisResult,
) -> CandidateTimingAttachment:
    years = sorted(_packet_year(packet) for packet in packets if _packet_year(packet) is not None)
    typed_years = [year for year in years if year is not None]
    ages = _korean_ages(typed_years, analysis)
    year_label = _range_label(typed_years, suffix="년")
    age_label = _range_label(ages, suffix="세")
    evidence_terms = _evidence_terms(packets)
    timing_kind = _timing_kind(candidate_key)
    sentences = _timing_sentences(candidate_key, age_label, year_label, evidence_terms, packets)
    return CandidateTimingAttachment(
        candidate_key=candidate_key,
        timing_kind=timing_kind,
        year_label=year_label,
        korean_age_label=age_label,
        sentences=sentences,
        evidence_packet_ids=[packet.packet_id for packet in packets],
        evidence_terms=evidence_terms,
        score=max((_timing_packet_score(candidate_key, packet) for packet in packets), default=0),
    )


def _timing_sentences(
    candidate_key: str,
    age_label: str,
    year_label: str,
    evidence_terms: list[str],
    packets: list[EventPacket],
) -> list[str]:
    scene_sentences = _scene_sentences(candidate_key, packets, evidence_terms)
    if candidate_key == "accumulated_work_gets_recognized_period":
        return [
            f"한국 나이 {age_label} 전후에는 해온 일이 실제 수입으로 돌아오기 쉽습니다.",
            *scene_sentences,
            "새 일을 크게 벌이기보다 이미 끝낸 결과물을 다시 보여주는 편이 좋습니다.",
        ]
    if candidate_key == "unresolved_promises_return_caution_period":
        return [
            f"한국 나이 {age_label} 전후에는 말로 넘겼던 약속을 다시 확인해야 합니다.",
            *scene_sentences,
            "돈이 오가는 일은 기록으로 남겨야 손해를 줄입니다.",
            "책임이 애매한 부탁은 바로 맡지 않는 편이 좋습니다.",
        ]
    if candidate_key == "direction_clarifies_after_break":
        return [
            f"한국 나이 {age_label} 전후에는 하던 일의 방향을 다시 잡게 됩니다.",
            *scene_sentences,
            "한 번 멈춘 일은 그대로 밀기보다 무엇을 줄이고 무엇을 남길지 다시 정해야 합니다.",
        ]
    if candidate_key == "later_life_settles_better_than_early":
        return [
            f"한국 나이 {age_label} 전후에는 초년의 시행착오가 안정된 자리로 정리됩니다.",
            *scene_sentences,
            "무리하게 새 일을 벌이기보다 이미 쌓은 경험을 직업 기준으로 삼는 편이 좋습니다.",
            "돈 문제에서는 늘어난 수입을 오래 보관하는 방식이 중요해집니다.",
        ]
    return [
        f"한국 나이 {age_label} 전후에는 이 섹션의 일이 더 분명하게 드러납니다.",
        *scene_sentences,
    ]


def _scene_sentences(
    candidate_key: str,
    packets: list[EventPacket],
    evidence_terms: list[str],
) -> list[str]:
    scenes: list[str] = []
    for packet in packets:
        if packet.domain == "money":
            scenes.append(_money_scene(candidate_key, packet))
        elif packet.domain == "career":
            scenes.append(_career_scene(candidate_key, packet))
        elif packet.domain == "love":
            scenes.append("관계에서는 연락 방식이 다시 문제가 되기 쉽습니다.")
        elif packet.domain == "marriage":
            scenes.append("결혼 문제에서는 가족 의견이 크게 들어올 수 있습니다.")
    scenes = [scene for scene in dict.fromkeys(scenes) if scene]
    if scenes:
        return [f"해당 연도는 {_packet_years_label(packets)}입니다.", *scenes[:3]]
    if evidence_terms:
        return [f"해당 연도는 {_packet_years_label(packets)}입니다.", "해당 시기에는 지나간 일을 다시 정리해야 합니다."]
    return [f"해당 연도는 {_packet_years_label(packets)}입니다.", "이 시기에는 중요한 일을 서둘러 넘기지 않는 편이 좋습니다."]


def _packet_years_label(packets: list[EventPacket]) -> str:
    years = [year for packet in packets if (year := _packet_year(packet)) is not None]
    return _range_label(years, suffix="년") or "해당 연도"


def _money_scene(candidate_key: str, packet: EventPacket) -> str:
    if candidate_key == "unresolved_promises_return_caution_period":
        return "돈 문제에서는 정산 기준을 다시 확인해야 합니다."
    if candidate_key == "accumulated_work_gets_recognized_period":
        return "돈 문제에서는 기존 거래가 반복 수입으로 이어지기 쉽습니다."
    if candidate_key == "later_life_settles_better_than_early":
        return "돈 문제에서는 수입을 오래 보관하는 힘이 좋아집니다."
    if "지출" in packet.event_keywords or "정산 기준" in packet.event_keywords:
        return "돈 문제에서는 반복되는 지출을 줄여야 합니다."
    return "돈 문제에서는 계약 내용을 분명히 확인해야 합니다."


def _career_scene(candidate_key: str, packet: EventPacket) -> str:
    if candidate_key == "unresolved_promises_return_caution_period":
        return "직장에서는 맡은 일의 범위를 다시 확인해야 합니다."
    if candidate_key == "accumulated_work_gets_recognized_period":
        return "직장에서는 맡은 역할이 더 분명해집니다."
    if candidate_key == "direction_clarifies_after_break":
        return "직장에서는 역할 변경을 겪기 쉽습니다."
    if candidate_key == "later_life_settles_better_than_early":
        return "직장에서는 맡은 일이 안정되기 쉽습니다."
    return "직장에서는 평가 기준을 다시 확인해야 합니다."


def _top_unique_year_packets(
    packets: list[EventPacket],
    *,
    key,
    limit: int,
) -> list[EventPacket]:
    ordered = sorted(packets, key=key, reverse=True)
    selected: list[EventPacket] = []
    used_years: set[int] = set()
    for packet in ordered:
        year = _packet_year(packet)
        if year is None or year in used_years:
            continue
        selected.append(packet)
        used_years.add(year)
        if len(selected) >= limit:
            break
    return sorted(selected, key=lambda packet: _packet_year(packet) or 0)


def _packet_year(packet: EventPacket) -> int | None:
    label = str(packet.period_label)
    if label.isdigit():
        return int(label)
    return None


def _korean_ages(years: list[int], analysis: AnalysisResult) -> list[int]:
    birth_year = analysis.trace.get("birth_year")
    if not isinstance(birth_year, int) or isinstance(birth_year, bool):
        return []
    return [year - birth_year + 1 for year in years]


def _range_label(values: list[int], *, suffix: str) -> str:
    unique = sorted({value for value in values if isinstance(value, int)})
    if not unique:
        return ""
    if len(unique) == 1:
        return f"{unique[0]}{suffix}"
    if unique[-1] - unique[0] == len(unique) - 1:
        return f"{unique[0]}~{unique[-1]}{suffix}"
    return ", ".join(f"{value}{suffix}" for value in unique)


def _evidence_terms(packets: list[EventPacket]) -> list[str]:
    terms: list[str] = []
    for packet in packets:
        terms.extend(packet.event_keywords)
        terms.append(packet.sub_event_type)
        terms.append(packet.risk_topic)
    return [term for term in dict.fromkeys(str(term) for term in terms if str(term))][:8]


def _timing_kind(candidate_key: str) -> str:
    if candidate_key == "unresolved_promises_return_caution_period":
        return "caution_period"
    if candidate_key == "accumulated_work_gets_recognized_period":
        return "good_period"
    if candidate_key == "direction_clarifies_after_break":
        return "turning_point"
    if candidate_key == "later_life_settles_better_than_early":
        return "later_stability"
    return "general_period"


def _timing_packet_score(candidate_key: str, packet: EventPacket) -> int:
    if candidate_key == "unresolved_promises_return_caution_period":
        value = packet.risk_score * 0.55 + packet.change_score * 0.3 + packet.event_probability_score * 0.15
    elif candidate_key == "accumulated_work_gets_recognized_period":
        value = packet.opportunity_score * 0.55 + packet.event_probability_score * 0.3 + packet.change_score * 0.15
    elif candidate_key == "direction_clarifies_after_break":
        value = packet.change_score * 0.55 + packet.risk_score * 0.25 + packet.event_probability_score * 0.2
    else:
        value = packet.event_probability_score * 0.45 + packet.opportunity_score * 0.35 + packet.change_score * 0.2
    return max(0, min(100, int(round(value))))


def _has_forbidden_timing_phrase(sentence: str) -> bool:
    forbidden = (
        "흐름",
        "패턴",
        "에너지",
        "활성화",
        "조건에 따라",
        "좌우합니다",
        "기회가 열립니다",
        "성과가 남습니다",
    )
    return any(fragment in sentence for fragment in forbidden)
