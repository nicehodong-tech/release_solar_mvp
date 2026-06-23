"""Premium outline assembly for staged candidate sections.

This module turns scored candidate matches into a product-shaped outline while
keeping candidate prose and chart-specific timing additions separate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import AnalysisResult
from .section_bank_candidates import candidate_assets_by_key
from .section_candidate_quality import CandidateQualityReview, candidate_quality_by_key
from .section_candidate_selection import CandidateSectionMatch, build_candidate_section_selection


PREMIUM_CANDIDATE_OUTLINE_VERSION = "premium_candidate_outline_v1"

_DOMAIN_SLOT_LABELS = {
    "personality": "나의 성향",
    "money": "재물운",
    "career": "직업운",
    "love": "연애운",
    "marriage": "결혼운",
    "life_timing": "인생 시기",
}
_DOMAIN_SLOT_ORDER = {
    "personality": 10,
    "money": 20,
    "career": 30,
    "love": 40,
    "marriage": 50,
    "life_timing": 60,
}
_TIMING_REQUIRED_DOMAINS = {"life_timing"}


@dataclass(frozen=True)
class PremiumCandidateOutlineBlock:
    slot_key: str
    slot_label: str
    candidate_key: str
    title: str
    domain: str
    score: int
    quality_status: str
    quality_score: int
    opening: list[str] = field(default_factory=list)
    body: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    timing_attachment_required: bool = False
    timing_attachment_note: str = ""
    evidence: list[str] = field(default_factory=list)
    editorial_issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PremiumCandidateOutline:
    version: str
    blocks: list[PremiumCandidateOutlineBlock]
    suppressed_candidate_keys: list[str] = field(default_factory=list)


def build_premium_candidate_outline(
    analysis: AnalysisResult,
    *,
    selection_limit: int = 14,
    outline_limit: int = 12,
) -> PremiumCandidateOutline:
    selection = build_candidate_section_selection(analysis, limit=selection_limit)
    assets = candidate_assets_by_key()
    quality = candidate_quality_by_key()
    blocks: list[PremiumCandidateOutlineBlock] = []

    for match in selection.matches:
        asset = assets.get(match.candidate_key)
        review = quality.get(match.candidate_key)
        if asset is None or review is None:
            continue
        blocks.append(_outline_block(match, review))

    blocks = _balanced_outline_blocks(blocks, outline_limit)
    selected_keys = {block.candidate_key for block in blocks}
    suppressed_keys = [
        match.candidate_key
        for match in selection.matches + selection.suppressed_matches
        if match.candidate_key not in selected_keys
    ]
    return PremiumCandidateOutline(
        version=PREMIUM_CANDIDATE_OUTLINE_VERSION,
        blocks=blocks,
        suppressed_candidate_keys=list(dict.fromkeys(suppressed_keys)),
    )


def validate_premium_candidate_outline(analysis: AnalysisResult) -> list[str]:
    outline = build_premium_candidate_outline(analysis)
    issues: list[str] = []
    if outline.version != PREMIUM_CANDIDATE_OUTLINE_VERSION:
        issues.append(f"outline version mismatch: {outline.version}")
    if not outline.blocks:
        issues.append("outline has no blocks")

    seen_keys: set[str] = set()
    for block in outline.blocks:
        if block.candidate_key in seen_keys:
            issues.append(f"duplicate outline block: {block.candidate_key}")
        seen_keys.add(block.candidate_key)
        if block.quality_status == "blocked":
            issues.append(f"{block.candidate_key}: blocked quality candidate selected")
        if not block.opening or not block.body or not block.summary:
            issues.append(f"{block.candidate_key}: incomplete prose split")
        if block.domain == "life_timing" and not block.timing_attachment_required:
            issues.append(f"{block.candidate_key}: life timing block missing timing attachment flag")
        if block.domain != "life_timing" and block.timing_attachment_required:
            issues.append(f"{block.candidate_key}: non timing block unexpectedly requires timing")
    return issues


def _outline_block(
    match: CandidateSectionMatch,
    review: CandidateQualityReview,
) -> PremiumCandidateOutlineBlock:
    asset = candidate_assets_by_key()[match.candidate_key]
    timing_required = asset.domain in _TIMING_REQUIRED_DOMAINS
    return PremiumCandidateOutlineBlock(
        slot_key=asset.domain,
        slot_label=_DOMAIN_SLOT_LABELS.get(asset.domain, asset.domain),
        candidate_key=asset.section_key,
        title=asset.customer_title,
        domain=asset.domain,
        score=match.score,
        quality_status=review.status,
        quality_score=review.score,
        opening=list(asset.opening),
        body=list(asset.main_body),
        summary=list(asset.compressed_summary),
        timing_attachment_required=timing_required,
        timing_attachment_note=(
            "대운·세운 선택층에서 나이대와 연도 문장을 별도로 붙여야 합니다."
            if timing_required
            else ""
        ),
        evidence=list(dict.fromkeys(match.matched_judgment_keys + match.matched_event_terms)),
        editorial_issues=list(review.issues),
    )


def _balanced_outline_blocks(
    blocks: list[PremiumCandidateOutlineBlock],
    outline_limit: int,
) -> list[PremiumCandidateOutlineBlock]:
    ordered = sorted(
        blocks,
        key=lambda block: (
            _DOMAIN_SLOT_ORDER.get(block.domain, 999),
            -block.score,
            block.candidate_key,
        ),
    )
    by_domain: dict[str, list[PremiumCandidateOutlineBlock]] = {}
    for block in ordered:
        by_domain.setdefault(block.domain, []).append(block)

    selected: list[PremiumCandidateOutlineBlock] = []
    selected_keys: set[str] = set()
    for domain in sorted(by_domain, key=lambda item: _DOMAIN_SLOT_ORDER.get(item, 999)):
        if len(selected) >= outline_limit:
            break
        block = sorted(by_domain[domain], key=lambda item: (-item.score, item.candidate_key))[0]
        selected.append(block)
        selected_keys.add(block.candidate_key)

    for block in ordered:
        if len(selected) >= outline_limit:
            break
        if block.candidate_key in selected_keys:
            continue
        selected.append(block)
        selected_keys.add(block.candidate_key)

    return sorted(
        selected,
        key=lambda block: (
            _DOMAIN_SLOT_ORDER.get(block.domain, 999),
            -block.score,
            block.candidate_key,
        ),
    )
