"""Quality gate for externally borrowed source-reading material.

The imported files are useful as structured saju material, but their prose is
not trusted as customer-ready copy. This gate checks whether source-derived
snippets still carry raw endings, AI-style abstractions, or low-grade guidebook
phrasing before they reach product surfaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


SOURCE_IMPORT_QUALITY_VERSION = "source_import_quality_v1"


@dataclass(frozen=True)
class SourceImportQualityIssue:
    code: str
    marker: str
    severity: int
    reason: str
    location: str = ""


RAW_ENDING_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"하려\s*한다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"하려\s*든다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"수\s*있다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"좋다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"크다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"세다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"강하다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"약하다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"쉽다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"본다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"한다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"생긴다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"커진다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"어려워진다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"받아들인다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"붙인다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"나간다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"나타난다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"드러난다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"남는다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"오래\s*간다(?:[.!?]|$)", "raw_declarative_ending"),
    (r"늦다(?:[.!?]|$)", "raw_declarative_ending"),
)

RAW_SOURCE_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("반드시", "deterministic_source_phrase"),
    ("돈이 새", "raw_money_metaphor"),
    ("돈을 남기는 법", "raw_guidebook_label"),
    ("것입니다", "raw_stiff_ending"),
    ("쉽게 말하면", "low_age_explanation"),
    ("좋은 흐름", "ai_abstract_flow"),
    ("삶의 흐름", "ai_abstract_flow"),
    ("내면의 에너지", "ai_abstract_energy"),
    ("에너지가", "ai_abstract_energy"),
    ("패턴을 인식", "ai_pattern_phrase"),
    ("균형이 중요", "ai_balance_phrase"),
    ("가능성이 있습니다", "weak_possibility_phrase"),
)

AWKWARD_SOURCE_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("묵직함와", "broken_particle"),
    ("마음와", "broken_particle"),
    ("거리감이가", "broken_particle"),
    ("성향은 성향", "repeated_abstract_subject"),
    ("문제로 커집니다", "awkward_problem_growth"),
    ("방식이 드러납니다", "abstract_subject_predicate"),
    ("조건이 드러납니다", "abstract_subject_predicate"),
    ("가능성이 드러납니다", "abstract_subject_predicate"),
    ("역할이 드러납니다", "abstract_subject_predicate"),
)


def source_import_quality_issues_for_text(text: str, *, location: str = "") -> list[SourceImportQualityIssue]:
    body = str(text or "").strip()
    if not body:
        return []
    issues: list[SourceImportQualityIssue] = []
    for pattern, code in RAW_ENDING_PATTERNS:
        match = re.search(pattern, body)
        if match:
            issues.append(
                SourceImportQualityIssue(
                    code=code,
                    marker=match.group(0),
                    severity=3,
                    reason="외부 원문 종결체가 고객용 문장으로 정제되지 않았습니다.",
                    location=location,
                )
            )
    for marker, code in RAW_SOURCE_FRAGMENTS:
        if marker in body:
            issues.append(
                SourceImportQualityIssue(
                    code=code,
                    marker=marker,
                    severity=3,
                    reason="외부 자료의 원문체 또는 AI식 완충 표현이 남아 있습니다.",
                    location=location,
                )
            )
    for marker, code in AWKWARD_SOURCE_FRAGMENTS:
        if marker in body:
            issues.append(
                SourceImportQualityIssue(
                    code=code,
                    marker=marker,
                    severity=4,
                    reason="한국어 결합이 어색해 상품 문장 신뢰도를 떨어뜨립니다.",
                    location=location,
                )
            )
    return issues


def _iter_strings(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield from _iter_strings(item, next_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            next_path = f"{path}[{index}]"
            yield from _iter_strings(item, next_path)


def source_import_quality_issues(payload: Any) -> list[SourceImportQualityIssue]:
    issues: list[SourceImportQualityIssue] = []
    for location, text in _iter_strings(payload):
        issues.extend(source_import_quality_issues_for_text(text, location=location))
    return issues


def source_import_quality_summary(payload: Any) -> dict[str, Any]:
    issues = source_import_quality_issues(payload)
    return {
        "version": SOURCE_IMPORT_QUALITY_VERSION,
        "issue_count": len(issues),
        "max_severity": max((issue.severity for issue in issues), default=0),
        "issues": [
            {
                "code": issue.code,
                "marker": issue.marker,
                "severity": issue.severity,
                "reason": issue.reason,
                "location": issue.location,
            }
            for issue in issues
        ],
    }
