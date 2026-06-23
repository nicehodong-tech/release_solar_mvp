"""Source personality profiles borrowed as structured analysis data.

This layer keeps external personality keywords out of the core calculation
rules. The analysis engine reads them only after the natal chart is fixed, then
exposes the matching day-pillar and day-stem/month-branch profile as supporting
material for personality-oriented product surfaces.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import SourcePersonalityProfile, SourcePersonalityTrait


SOURCE_PERSONALITY_PROFILE_VERSION = "source_personality_profile_v1"

DATA_DIR = Path(__file__).resolve().parent / "data" / "source_personality_profiles"
DAY_PILLAR_CSV = DATA_DIR / "day_pillar_personality_keywords.csv"
MONTH_BRANCH_CSV = DATA_DIR / "day_stem_month_branch_personality_keywords.csv"

STEM_LABELS = {
    "gap": "甲",
    "eul": "乙",
    "byeong": "丙",
    "jeong": "丁",
    "mu": "戊",
    "gi": "己",
    "gyeong": "庚",
    "sin": "辛",
    "im": "壬",
    "gye": "癸",
}

BRANCH_LABELS = {
    "ja": "子",
    "chuk": "丑",
    "in": "寅",
    "myo": "卯",
    "jin": "辰",
    "sa": "巳",
    "o": "午",
    "mi": "未",
    "sin": "申",
    "yu": "酉",
    "sul": "戌",
    "hae": "亥",
}


TRAIT_DISPLAY_REPLACEMENTS = {
    "버팀": "지속력",
    "손실 공포": "손실에 대한 경계심",
    "기억 집착": "오래 남는 기억",
    "생활 집착": "생활 안정에 대한 집요함",
    "분노 축적": "누적된 감정",
    "인정 갈망": "인정받고 싶은 마음",
    "인정 욕구": "인정받고 싶은 마음",
    "양보 거부": "쉽게 물러서지 않는 태도",
    "손절 지연": "관계 정리가 늦어지는 편",
    "사과 지연": "감정이 풀리기까지 걸리는 시간",
    "고립": "스스로 거리를 두는 태도",
    "이중성": "겉과 속이 달라지는 방어성",
    "독단": "혼자 결정하려는 태도",
    "독선": "자기 판단에 갇히는 경향",
    "통제욕": "통제감",
    "소유욕": "소유 기준",
    "질투": "비교에서 오는 예민함",
    "의심": "쉽게 믿지 않는 태도",
    "고집": "결정을 쉽게 바꾸지 않는 기질",
    "보수성": "검증된 방식을 선호하는 태도",
    "계산성": "손익을 먼저 따지는 기질",
    "냉정한 단절": "마음이 닫히면 단호해지는 태도",
    "뒤끝": "감정이 오래 남는 편",
    "관계 경직": "관계에서 유연성이 떨어지는 순간",
    "과소비": "지출 기준이 흐려지는 순간",
    "불안": "불안감",
    "고독": "고독감",
}


def _split_traits(raw: str) -> list[str]:
    value = str(raw or "").strip()
    if not value:
        return []
    parts = [part.strip() for part in value.replace(",", "·").split("·")]
    return [TRAIT_DISPLAY_REPLACEMENTS.get(part, part) for part in parts if part]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _trait_from_day_row(row: dict[str, str]) -> SourcePersonalityTrait:
    source_key = str(row.get("일주") or "").strip()
    return SourcePersonalityTrait(
        source_type="day_pillar",
        source_key=source_key,
        title=str(row.get("한글명") or source_key).strip(),
        compression_type=str(row.get("압축유형") or "").strip(),
        core_traits=_split_traits(row.get("핵심성정", "")),
        outer_traits=_split_traits(row.get("겉성격", "")),
        inner_traits=_split_traits(row.get("속기질", "")),
        strength_traits=_split_traits(row.get("강점기질", "")),
        shadow_traits=_split_traits(row.get("그림자기질", "")),
        basis_codes=[f"source_personality:day_pillar:{source_key}"] if source_key else [],
    )


def _trait_from_month_row(row: dict[str, str]) -> SourcePersonalityTrait:
    day_stem = str(row.get("일간") or "").strip()
    month_branch = str(row.get("월령") or "").strip()
    source_key = f"{day_stem}{month_branch}"
    return SourcePersonalityTrait(
        source_type="day_stem_month_branch",
        source_key=source_key,
        title=str(row.get("한글명") or source_key).strip(),
        compression_type=str(row.get("압축유형") or "").strip(),
        core_traits=_split_traits(row.get("핵심성정", "")),
        outer_traits=_split_traits(row.get("겉성격", "")),
        inner_traits=_split_traits(row.get("속기질", "")),
        strength_traits=_split_traits(row.get("강점기질", "")),
        shadow_traits=_split_traits(row.get("그림자기질", "")),
        main_ten_god=str(row.get("월령본기십신") or "").strip(),
        basis_codes=[f"source_personality:day_stem_month_branch:{source_key}"] if source_key else [],
    )


@lru_cache(maxsize=1)
def day_pillar_personality_profiles() -> dict[str, SourcePersonalityTrait]:
    profiles: dict[str, SourcePersonalityTrait] = {}
    for row in _read_csv(DAY_PILLAR_CSV):
        trait = _trait_from_day_row(row)
        if trait.source_key:
            profiles[trait.source_key] = trait
    return profiles


@lru_cache(maxsize=1)
def month_branch_personality_profiles() -> dict[str, SourcePersonalityTrait]:
    profiles: dict[str, SourcePersonalityTrait] = {}
    for row in _read_csv(MONTH_BRANCH_CSV):
        trait = _trait_from_month_row(row)
        if trait.source_key:
            profiles[trait.source_key] = trait
    return profiles


def _unique(values: list[str], limit: int | None = None) -> list[str]:
    unique_values = list(dict.fromkeys(value for value in values if value))
    if limit is None:
        return unique_values
    return unique_values[:limit]


def _trait_sentence(prefix: str, trait: SourcePersonalityTrait | None) -> str:
    if trait is None:
        return ""
    title = trait.compression_type or trait.title
    core = " · ".join(trait.core_traits[:3])
    strength = " · ".join(trait.strength_traits[:2])
    if core and strength:
        return f"{prefix} {title}입니다. {core} 성향이 중심에 있고, {strength}에서 장점이 드러납니다."
    if core:
        return f"{prefix} {title}입니다. {core} 성향이 중심에 있습니다."
    return f"{prefix} {title}입니다."


def build_source_personality_profile(
    *,
    day_stem_key: str,
    day_branch_key: str,
    month_branch_key: str,
) -> SourcePersonalityProfile:
    day_stem = STEM_LABELS.get(day_stem_key, day_stem_key)
    day_branch = BRANCH_LABELS.get(day_branch_key, day_branch_key)
    month_branch = BRANCH_LABELS.get(month_branch_key, month_branch_key)

    day_pillar_key = f"{day_stem}{day_branch}"
    month_profile_key = f"{day_stem}{month_branch}"

    day_profile = day_pillar_personality_profiles().get(day_pillar_key)
    month_profile = month_branch_personality_profiles().get(month_profile_key)
    profiles = [profile for profile in (day_profile, month_profile) if profile is not None]

    trait_keywords = _unique(
        [trait for profile in profiles for trait in profile.core_traits + profile.outer_traits],
        limit=10,
    )
    strength_keywords = _unique(
        [trait for profile in profiles for trait in profile.strength_traits],
        limit=8,
    )
    shadow_keywords = _unique(
        [trait for profile in profiles for trait in profile.inner_traits + profile.shadow_traits],
        limit=8,
    )
    summary_sentences = [
        sentence
        for sentence in (
            _trait_sentence("일주로 보면", day_profile),
            _trait_sentence("월령이 더하는 성격은", month_profile),
        )
        if sentence
    ]
    basis_codes = _unique([code for profile in profiles for code in profile.basis_codes])

    return SourcePersonalityProfile(
        day_pillar_profile=day_profile,
        month_branch_profile=month_profile,
        trait_keywords=trait_keywords,
        strength_keywords=strength_keywords,
        shadow_keywords=shadow_keywords,
        summary_sentences=summary_sentences,
        basis_codes=basis_codes,
        rule_version=SOURCE_PERSONALITY_PROFILE_VERSION,
    )


def source_personality_profile_payload(profile: SourcePersonalityProfile) -> dict[str, Any]:
    def trait_payload(trait: SourcePersonalityTrait | None) -> dict[str, Any] | None:
        if trait is None:
            return None
        return {
            "source_type": trait.source_type,
            "source_key": trait.source_key,
            "title": trait.title,
            "compression_type": trait.compression_type,
            "core_traits": list(trait.core_traits),
            "outer_traits": list(trait.outer_traits),
            "inner_traits": list(trait.inner_traits),
            "strength_traits": list(trait.strength_traits),
            "shadow_traits": list(trait.shadow_traits),
            "main_ten_god": trait.main_ten_god,
            "basis_codes": list(trait.basis_codes),
        }

    return {
        "rule_version": profile.rule_version,
        "day_pillar_profile": trait_payload(profile.day_pillar_profile),
        "month_branch_profile": trait_payload(profile.month_branch_profile),
        "trait_keywords": list(profile.trait_keywords),
        "strength_keywords": list(profile.strength_keywords),
        "shadow_keywords": list(profile.shadow_keywords),
        "summary_sentences": list(profile.summary_sentences),
        "basis_codes": list(profile.basis_codes),
    }


def validate_source_personality_profiles() -> list[str]:
    errors: list[str] = []
    day_profiles = day_pillar_personality_profiles()
    month_profiles = month_branch_personality_profiles()
    if len(day_profiles) != 60:
        errors.append(f"day_pillar_personality_profiles: expected 60, got {len(day_profiles)}")
    if len(month_profiles) != 120:
        errors.append(f"month_branch_personality_profiles: expected 120, got {len(month_profiles)}")
    for key, profile in {**day_profiles, **month_profiles}.items():
        if not profile.compression_type:
            errors.append(f"{key}: missing compression_type")
        if not profile.core_traits:
            errors.append(f"{key}: missing core_traits")
        if not profile.strength_traits:
            errors.append(f"{key}: missing strength_traits")
        if not profile.shadow_traits:
            errors.append(f"{key}: missing shadow_traits")
    return errors
