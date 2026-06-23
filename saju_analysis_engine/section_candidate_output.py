"""Product-output assembly for staged premium candidate sections.

This layer does not reinterpret the birth chart. It receives the candidate
outline chosen by the selection layer, attaches chart-specific timing prose
from the timing adapter, and returns stable product-output blocks.
"""

from __future__ import annotations

from .models import AnalysisResult, CandidateReportSection
from .section_candidate_outline import PremiumCandidateOutline, build_premium_candidate_outline
from .section_candidate_timing import CandidateTimingAttachment, candidate_timing_by_key


CANDIDATE_REPORT_SECTION_VERSION = "candidate_report_section_v1"


def build_candidate_report_sections(
    analysis: AnalysisResult,
    outline: PremiumCandidateOutline | None = None,
    *,
    selection_limit: int = 14,
    outline_limit: int = 10,
) -> list[CandidateReportSection]:
    """Return premium candidate sections ready to be carried by ProductOutput."""

    outline = outline or build_premium_candidate_outline(
        analysis,
        selection_limit=selection_limit,
        outline_limit=outline_limit,
    )
    timing_by_key = candidate_timing_by_key(analysis, outline)
    sections: list[CandidateReportSection] = []
    for block in outline.blocks:
        timing = timing_by_key.get(block.candidate_key)
        sections.append(
            CandidateReportSection(
                section_key=block.candidate_key,
                title=block.title,
                domain=block.domain,
                slot_label=block.slot_label,
                score=block.score,
                quality_score=block.quality_score,
                quality_status=block.quality_status,
                opening=list(block.opening),
                body=list(block.body),
                summary=list(block.summary),
                timing_sentences=list(timing.sentences) if timing else [],
                timing_year_label=timing.year_label if timing else "",
                timing_age_label=timing.korean_age_label if timing else "",
                evidence=list(block.evidence),
            )
        )
    return sections


def validate_candidate_report_sections(
    analysis: AnalysisResult,
    outline: PremiumCandidateOutline | None = None,
) -> list[str]:
    """Validate the product-output candidate section bridge."""

    outline = outline or build_premium_candidate_outline(analysis)
    required_timing_keys = {
        block.candidate_key
        for block in outline.blocks
        if block.timing_attachment_required
    }
    sections = build_candidate_report_sections(analysis, outline)
    issues: list[str] = []
    if not sections:
        issues.append("candidate report sections missing")

    seen: set[str] = set()
    for section in sections:
        if section.section_key in seen:
            issues.append(f"{section.section_key}: duplicate candidate report section")
        seen.add(section.section_key)
        if not section.title:
            issues.append(f"{section.section_key}: missing title")
        if not section.opening or not section.body or not section.summary:
            issues.append(f"{section.section_key}: incomplete body split")
        if section.section_key in required_timing_keys:
            if not section.timing_sentences:
                issues.append(f"{section.section_key}: missing timing sentences")
            if not section.timing_year_label or not section.timing_age_label:
                issues.append(f"{section.section_key}: missing timing labels")
        if _has_forbidden_candidate_report_phrase(section):
            issues.append(f"{section.section_key}: forbidden customer phrase")
    return issues


def _has_forbidden_candidate_report_phrase(section: CandidateReportSection) -> bool:
    text = " ".join(section.opening + section.body + section.summary + section.timing_sentences)
    forbidden = (
        "구조가 활성화",
        "긍정적인 흐름",
        "내면의 에너지",
        "관계의 패턴",
        "조건에 따라",
        "좌우합니다",
    )
    return any(fragment in text for fragment in forbidden)
