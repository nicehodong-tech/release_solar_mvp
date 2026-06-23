"""Quality review helpers for staged section-bank candidates.

The review is intentionally separate from activation. A candidate can be useful
for selector experiments even when its prose still needs editorial work.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .section_bank_candidates import CandidateSectionAsset, candidate_assets_by_key


CANDIDATE_SECTION_QUALITY_VERSION = "candidate_section_quality_v1"

_REVIEW_VISIBLE_BANNED_FRAGMENTS = (
    "구조가 활성화",
    "내면의 에너지",
    "긍정적인 흐름",
    "재물의 경계",
    "관계의 패턴",
    "조건에 따라",
    "좌우합니다",
    "좌우됩니다",
    "패턴을 인식",
    "성과가 남습니다",
    "기회가 열립니다",
    "자리가 열립니다",
)
_TIMING_FRAGMENTS = ("2026", "2027", "2028", "30세", "한국 나이")
_OVERPACKED_MARKERS = ("역할, 권한", "결정권, 결과물", "연락 방식, 감정 표현")


@dataclass(frozen=True)
class CandidateQualityReview:
    candidate_key: str
    domain: str
    score: int
    status: str
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    sentence_count: int = 0
    visible_character_count: int = 0


def review_candidate_quality(candidate: CandidateSectionAsset) -> CandidateQualityReview:
    visible_units = candidate.opening + candidate.main_body + candidate.compressed_summary
    visible_text = " ".join(visible_units)
    issues: list[str] = []
    strengths: list[str] = []

    if len(candidate.opening) < 3:
        issues.append("opening_too_short")
    else:
        strengths.append("opening_has_room_for_reader_entry")

    if len(candidate.main_body) < 8:
        issues.append("main_body_too_short")
    elif len(candidate.main_body) >= 10:
        strengths.append("main_body_has_report_weight")

    if len(candidate.compressed_summary) < 3:
        issues.append("summary_too_short")
    else:
        strengths.append("summary_is_ready_for_card")

    if any(fragment in visible_text for fragment in _REVIEW_VISIBLE_BANNED_FRAGMENTS):
        issues.append("banned_visible_fragment")
    if any(fragment in visible_text for fragment in _TIMING_FRAGMENTS):
        issues.append("fixed_timing_in_candidate_body")
    if any(fragment in visible_text for fragment in _OVERPACKED_MARKERS):
        issues.append("overpacked_sentence_marker")

    if _has_life_words(visible_text):
        strengths.append("life_scene_words_present")
    else:
        issues.append("life_scene_words_thin")

    if _has_customer_address(candidate):
        strengths.append("customer_address_present")
    else:
        issues.append("customer_address_missing")

    if len(candidate.selection_signal_hints) >= 5:
        strengths.append("selection_hints_are_useful")
    else:
        issues.append("selection_hints_too_thin")

    score = _quality_score(candidate, visible_text, issues, strengths)
    status = _quality_status(score, issues)
    return CandidateQualityReview(
        candidate_key=candidate.section_key,
        domain=candidate.domain,
        score=score,
        status=status,
        issues=issues,
        strengths=strengths,
        sentence_count=len(visible_units),
        visible_character_count=len(visible_text),
    )


def review_all_candidate_quality() -> list[CandidateQualityReview]:
    return [
        review_candidate_quality(candidate)
        for candidate in candidate_assets_by_key().values()
    ]


def candidate_quality_by_key() -> dict[str, CandidateQualityReview]:
    return {
        review.candidate_key: review
        for review in review_all_candidate_quality()
    }


def candidate_quality_summary() -> dict[str, object]:
    reviews = review_all_candidate_quality()
    status_counts: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    for review in reviews:
        status_counts[review.status] = status_counts.get(review.status, 0) + 1
        for issue in review.issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    return {
        "version": CANDIDATE_SECTION_QUALITY_VERSION,
        "candidate_count": len(reviews),
        "status_counts": status_counts,
        "issue_counts": issue_counts,
        "minimum_score": min((review.score for review in reviews), default=0),
        "average_score": round(
            sum(review.score for review in reviews) / len(reviews),
            2,
        )
        if reviews
        else 0,
    }


def validate_candidate_quality_floor(minimum_score: int = 62) -> list[str]:
    issues: list[str] = []
    for review in review_all_candidate_quality():
        if review.score < minimum_score:
            issues.append(
                f"{review.candidate_key}: quality score {review.score} below {minimum_score}"
            )
        if review.status == "blocked":
            issues.append(f"{review.candidate_key}: blocked by {review.issues}")
    return issues


def _quality_score(
    candidate: CandidateSectionAsset,
    visible_text: str,
    issues: list[str],
    strengths: list[str],
) -> int:
    score = 58
    score += min(len(strengths) * 4, 24)
    score += min(max(len(candidate.main_body) - 8, 0), 5)
    if 450 <= len(visible_text) <= 1600:
        score += 5
    if len(visible_text) < 360:
        score -= 10
    if len(visible_text) > 2200:
        score -= 8
    if len(candidate.opening) >= 4:
        score += 2
    if len(candidate.wording_notes) >= 5:
        score += 2
    score -= len(issues) * 8
    if "banned_visible_fragment" in issues:
        score -= 20
    if "fixed_timing_in_candidate_body" in issues:
        score -= 16
    return max(0, min(100, score))


def _quality_status(score: int, issues: list[str]) -> str:
    if "banned_visible_fragment" in issues or "fixed_timing_in_candidate_body" in issues:
        return "blocked"
    if score >= 82:
        return "ready_for_staging"
    if score >= 68:
        return "needs_editorial_review"
    return "needs_rewrite"


def _has_life_words(text: str) -> bool:
    life_words = (
        "돈",
        "직장",
        "가족",
        "배우자",
        "고객",
        "계약",
        "정산",
        "일정",
        "생활비",
        "책임",
        "관계",
        "수입",
        "자료",
        "설명",
        "결정",
        "기준",
    )
    return any(word in text for word in life_words)


def _has_customer_address(candidate: CandidateSectionAsset) -> bool:
    visible_text = " ".join(candidate.opening + candidate.main_body + candidate.compressed_summary)
    return "당신" in visible_text or "이 사주" in visible_text
