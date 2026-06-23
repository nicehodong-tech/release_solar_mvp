"""Structured source-reading snippets for product surfaces.

The source files are long one-pillar and day-stem/month-branch readings. This
module does not expose those paragraphs directly. It extracts small domain
points, normalizes labels, and leaves the final customer copy to the product
renderer.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .source_personality_profiles import BRANCH_LABELS, STEM_LABELS
from .models import SourceReadingPoint, SourceReadingProfile


SOURCE_READING_PROFILE_VERSION = "source_reading_profile_v1"

DATA_DIR = Path(__file__).resolve().parent / "data" / "source_reading_profiles"
DAY_PILLAR_JSONL = DATA_DIR / "day_pillar_readings.jsonl"
MONTH_BRANCH_JSONL = DATA_DIR / "day_stem_month_branch_readings.jsonl"

SECTION_DOMAIN_RULES: tuple[tuple[str, str], ...] = (
    ("재물", "money"),
    ("직업", "career"),
    ("연애", "love_marriage"),
    ("결혼", "love_marriage"),
    ("대인관계", "social"),
    ("가족과 가까운 사람", "social"),
    ("상품용 압축문", "summary"),
)

POINT_LABEL_REPLACEMENTS = {
    "기본 돈 성향": "재물 성향",
    "기본 재물 성향": "재물 성향",
    "월령의 돈 성향": "월령 재물 성향",
    "일간의 돈 성향": "일간 재물 성향",
    "일지 본기의 돈 성향(비견)": "배우자궁 재물 성향",
    "일지 본기의 돈 성향(정인)": "배우자궁 재물 성향",
    "이 계절에 자주 생기는 돈 문제": "재물 변수",
    "돈이 새는 장면": "손실이 커지는 장면",
    "돈이 크게 새는 장면": "손실이 커지는 장면",
    "돈을 남기는 법": "재물 보전 기준",
    "잘 맞는 일": "잘 맞는 역할",
    "기본 직업 성향": "직업 성향",
    "월령상 강한 역할": "월령상 강한 역할",
    "일간이 잘하는 역할": "일간이 잘하는 역할",
    "일지 본기상 강한 역할": "일지 본기상 강한 역할",
    "잘못된 선택": "피해야 할 선택",
    "기본 연애 성향": "연애 성향",
    "월령이 더하는 관계 성향": "월령 관계 성향",
    "일간의 사랑 방식": "사랑 방식",
    "반복되기 쉬운 장면": "반복되는 관계 장면",
    "결혼 뒤 부딪히는 부분": "결혼 뒤 충돌 지점",
    "잘 맞는 상대": "잘 맞는 상대",
    "처음에는": "첫인상",
    "가까워지면": "가까워진 뒤",
    "사람을 끊는 기준": "관계 단절 기준",
    "평판이 무너지는 장면": "평판 주의점",
    "속마음": "내면 성향",
    "돈의 약점": "재물 주의점",
    "관계의 약점": "관계 주의점",
    "살려야 할 재능": "살려야 할 재능",
}

TEXT_REPLACEMENTS = {
    "돈이 새는": "재정 손실이 생기는",
    "돈이 크게 새는": "재정 손실이 커지는",
    "돈을 남기는": "재물을 보전하는",
    "돈을 붙인다": "자금을 투입합니다",
    "몫 문제가 생긴다": "몫과 권리 문제가 생깁니다",
    "오래 갑니다": "오래 유지됩니다",
    "맞습니다": "잘 맞습니다",
    "것입니다": "것이 필요합니다",
    "쉽습니다": "쉽습니다",
}

DOMAIN_LABEL_PRIORITY = {
    "money": (
        "재물 성향",
        "월령 재물 성향",
        "재물 변수",
        "손실이 커지는 장면",
        "재물 보전 기준",
        "재물 주의점",
    ),
    "career": (
        "직업 성향",
        "잘 맞는 역할",
        "월령상 강한 역할",
        "일간이 잘하는 역할",
        "조직에서는",
        "독립·사업에서는",
        "피해야 할 선택",
    ),
    "love_marriage": (
        "연애 성향",
        "사랑 방식",
        "월령 관계 성향",
        "반복되는 관계 장면",
        "결혼 뒤 충돌 지점",
        "잘 맞는 상대",
    ),
    "social": (
        "첫인상",
        "가까워진 뒤",
        "관계 단절 기준",
        "잘 맞는 사람",
        "평판 주의점",
        "가족 안에서 맡기 쉬운 역할",
        "가까운 사람과의 핵심 과제",
    ),
    "summary": (
        "첫인상",
        "내면 성향",
        "욕망",
        "자존심",
        "재물 주의점",
        "관계 주의점",
        "살려야 할 재능",
    ),
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


@lru_cache(maxsize=1)
def _day_readings() -> dict[str, dict[str, Any]]:
    return {str(row.get("pillar") or ""): row for row in _read_jsonl(DAY_PILLAR_JSONL)}


@lru_cache(maxsize=1)
def _month_readings() -> dict[str, dict[str, Any]]:
    return {
        f"{row.get('day_stem')}{row.get('month_branch')}": row
        for row in _read_jsonl(MONTH_BRANCH_JSONL)
    }


def _section_domain(heading: str) -> str:
    for marker, domain in SECTION_DOMAIN_RULES:
        if marker in heading:
            return domain
    return ""


def _sections(text: str) -> list[tuple[str, str, str]]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", text, flags=re.MULTILINE))
    sections: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        domain = _section_domain(heading)
        if domain:
            sections.append((domain, heading, text[start:end].strip()))
    return sections


def _clean_label(raw: str) -> str:
    label = str(raw or "").strip()
    label = label.replace(":", "").strip()
    return POINT_LABEL_REPLACEMENTS.get(label, label)


def _clean_text(raw: str) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    for source, target in TEXT_REPLACEMENTS.items():
        text = text.replace(source, target)
    sentence_replacements = (
        ("운영하려 들 수 있다", "운영하려는 태도가 강해질 수 있습니다"),
        ("하려 한다.", "하려는 성향이 있습니다."),
        ("하려 한다", "하려는 성향이 있습니다"),
        ("만들려 한다.", "만들려는 성향이 있습니다."),
        ("만들려 한다", "만들려는 성향이 있습니다"),
        ("키우려 한다.", "키우려는 성향이 있습니다."),
        ("키우려 한다", "키우려는 성향이 있습니다"),
        ("운영하려 들 수 있다.", "운영하려는 태도가 강해질 수 있습니다."),
        ("수 있다.", "수 있습니다."),
        ("수 있다", "수 있습니다"),
        ("좋다.", "좋습니다."),
        ("좋다", "좋습니다"),
        ("크다.", "큽니다."),
        ("크다", "큽니다"),
        ("세다.", "강합니다."),
        ("세다", "강합니다"),
        ("강하다.", "강합니다."),
        ("강하다", "강합니다"),
        ("약하다.", "약합니다."),
        ("약하다", "약합니다"),
        ("쉽다.", "쉽습니다."),
        ("쉽다", "쉽습니다"),
        ("생긴다.", "생깁니다."),
        ("생긴다", "생깁니다"),
        ("커진다.", "커집니다."),
        ("커진다", "커집니다"),
        ("어려워진다.", "어려워집니다."),
        ("어려워진다", "어려워집니다"),
        ("받아들인다.", "받아들입니다."),
        ("받아들인다", "받아들입니다"),
        ("붙인다.", "붙입니다."),
        ("붙인다", "붙입니다"),
        ("나간다.", "나갑니다."),
        ("나간다", "나갑니다"),
        ("오래 간다.", "오래 갑니다."),
        ("오래 간다", "오래 갑니다"),
        ("본다.", "봅니다."),
        ("본다", "봅니다"),
        ("한다.", "합니다."),
        ("한다", "합니다"),
        ("나타난다.", "나타납니다."),
        ("나타난다", "나타납니다"),
        ("드러난다.", "드러납니다."),
        ("드러난다", "드러납니다"),
        ("남는다.", "남습니다."),
        ("남는다", "남습니다"),
        ("늦다.", "늦습니다."),
        ("늦다", "늦습니다"),
    )
    for source, target in sentence_replacements:
        text = text.replace(source, target)
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _points_from_section(
    *,
    source_type: str,
    source_key: str,
    domain: str,
    body: str,
) -> list[SourceReadingPoint]:
    points: list[SourceReadingPoint] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        content = stripped[2:].strip()
        if ":" not in content:
            continue
        raw_label, raw_text = content.split(":", 1)
        label = _clean_label(raw_label)
        text = _clean_text(raw_text)
        if not label or not text:
            continue
        points.append(
            SourceReadingPoint(
                source_type=source_type,
                source_key=source_key,
                domain=domain,
                label=label,
                text=text,
                basis_codes=[f"source_reading:{source_type}:{source_key}:{domain}:{label}"],
            )
        )
    return points


def _points_for_row(source_type: str, source_key: str, row: dict[str, Any]) -> dict[str, list[SourceReadingPoint]]:
    text = str(row.get("text") or "")
    domain_points: dict[str, list[SourceReadingPoint]] = {}
    for domain, _heading, body in _sections(text):
        domain_points.setdefault(domain, []).extend(
            _points_from_section(
                source_type=source_type,
                source_key=source_key,
                domain=domain,
                body=body,
            )
        )
    return domain_points


def _sort_points(domain: str, points: list[SourceReadingPoint], limit: int) -> list[SourceReadingPoint]:
    priorities = DOMAIN_LABEL_PRIORITY.get(domain, ())
    priority_index = {label: index for index, label in enumerate(priorities)}
    if domain in {"money", "career"}:
        source_rank = {"day_stem_month_branch": 0, "day_pillar": 1}
    else:
        source_rank = {"day_pillar": 0, "day_stem_month_branch": 1}
    sorted_points = sorted(
        points,
        key=lambda point: (
            priority_index.get(point.label, 99),
            source_rank.get(point.source_type, 9),
            point.label,
        ),
    )
    deduped: list[SourceReadingPoint] = []
    seen: set[tuple[str, str]] = set()
    seen_labels: set[str] = set()
    for point in sorted_points:
        key = (point.label, point.text)
        if key in seen or point.label in seen_labels:
            continue
        seen.add(key)
        seen_labels.add(point.label)
        deduped.append(point)
        if len(deduped) >= limit:
            break
    return deduped


def build_source_reading_profile(
    *,
    day_stem_key: str,
    day_branch_key: str,
    month_branch_key: str,
    limit_per_domain: int = 6,
) -> SourceReadingProfile:
    day_stem = STEM_LABELS.get(day_stem_key, day_stem_key)
    day_branch = BRANCH_LABELS.get(day_branch_key, day_branch_key)
    month_branch = BRANCH_LABELS.get(month_branch_key, month_branch_key)

    day_pillar_key = f"{day_stem}{day_branch}"
    month_profile_key = f"{day_stem}{month_branch}"

    merged: dict[str, list[SourceReadingPoint]] = {}
    day_row = _day_readings().get(day_pillar_key)
    month_row = _month_readings().get(month_profile_key)
    for source_type, source_key, row in (
        ("day_pillar", day_pillar_key, day_row),
        ("day_stem_month_branch", month_profile_key, month_row),
    ):
        if not row:
            continue
        for domain, points in _points_for_row(source_type, source_key, row).items():
            merged.setdefault(domain, []).extend(points)

    domain_points = {
        domain: _sort_points(domain, points, limit_per_domain)
        for domain, points in merged.items()
        if domain != "summary"
    }
    summary_points = _sort_points("summary", merged.get("summary", []), limit_per_domain)
    basis_codes = list(
        dict.fromkeys(
            code
            for point in [*summary_points, *[item for points in domain_points.values() for item in points]]
            for code in point.basis_codes
        )
    )
    return SourceReadingProfile(
        domain_points=domain_points,
        summary_points=summary_points,
        basis_codes=basis_codes,
        rule_version=SOURCE_READING_PROFILE_VERSION,
    )


def source_reading_profile_payload(profile: SourceReadingProfile) -> dict[str, Any]:
    def point_payload(point: SourceReadingPoint) -> dict[str, Any]:
        return {
            "source_type": point.source_type,
            "source_key": point.source_key,
            "domain": point.domain,
            "label": point.label,
            "text": point.text,
            "basis_codes": list(point.basis_codes),
        }

    return {
        "rule_version": profile.rule_version,
        "domain_points": {
            domain: [point_payload(point) for point in points]
            for domain, points in profile.domain_points.items()
        },
        "summary_points": [point_payload(point) for point in profile.summary_points],
        "basis_codes": list(profile.basis_codes),
    }


def validate_source_reading_profiles() -> list[str]:
    errors: list[str] = []
    day_readings = _day_readings()
    month_readings = _month_readings()
    if len(day_readings) != 60:
        errors.append(f"day_readings: expected 60, got {len(day_readings)}")
    if len(month_readings) != 120:
        errors.append(f"month_readings: expected 120, got {len(month_readings)}")
    for key, row in list(day_readings.items())[:60]:
        points = _points_for_row("day_pillar", key, row)
        for domain in ("money", "career", "love_marriage"):
            if not points.get(domain):
                errors.append(f"day_readings:{key}: missing {domain}")
    for key, row in list(month_readings.items())[:120]:
        points = _points_for_row("day_stem_month_branch", key, row)
        for domain in ("money", "career", "love_marriage"):
            if not points.get(domain):
                errors.append(f"month_readings:{key}: missing {domain}")
    return errors
