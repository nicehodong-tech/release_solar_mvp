"""Candidate section-bank assets collected before activation.

Candidate assets are prose resources that have not yet been wired into the
section selector. They are kept separate from the active bank so that prose can
be reviewed, revised, and scored before it affects customer reports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECTION_BANK_CANDIDATE_SCHEMA_VERSION = "section_bank_candidate_assets_v1"

_DATA_DIR = Path(__file__).with_name("data")
_DATA_PATH = _DATA_DIR / "section_bank_candidates_chatgpt_20260615.json"
_DATA_GLOB = "section_bank_candidates_*.json"

_BANNED_VISIBLE_FRAGMENTS = (
    "구조가 활성화",
    "내면의 에너지",
    "긍정적인 흐름",
    "재물의 경계가 흐려",
    "관계의 패턴",
    "조건에 따라",
    "좌우합니다",
    "좌우됩니다",
    "패턴을 인식",
)


@dataclass(frozen=True)
class CandidateSectionAsset:
    section_key: str
    source_key: str
    customer_title: str
    domain: str
    narrative_group: str
    selection_signal_hints: list[str]
    opening: list[str]
    main_body: list[str]
    compressed_summary: list[str]
    awkward_words_to_avoid: list[str]
    wording_notes: list[str]


@dataclass(frozen=True)
class SectionBankCandidateArtifact:
    schema_version: str
    source: str
    generation_notes: list[str]
    candidates: list[CandidateSectionAsset]


def load_section_bank_candidate_artifact(path: Path | None = None) -> SectionBankCandidateArtifact:
    if path is not None:
        return _load_single_artifact(path)

    artifacts = [_load_single_artifact(item) for item in candidate_artifact_paths()]
    candidates: list[CandidateSectionAsset] = []
    generation_notes: list[str] = []
    sources: list[str] = []
    schema_versions: set[str] = set()
    for artifact in artifacts:
        schema_versions.add(artifact.schema_version)
        sources.append(artifact.source)
        generation_notes.extend(artifact.generation_notes)
        candidates.extend(artifact.candidates)

    if not schema_versions:
        schema_version = SECTION_BANK_CANDIDATE_SCHEMA_VERSION
    elif len(schema_versions) == 1:
        schema_version = next(iter(schema_versions))
    else:
        schema_version = "+".join(sorted(schema_versions))
    return SectionBankCandidateArtifact(
        schema_version=schema_version,
        source="+".join(source for source in sources if source),
        generation_notes=generation_notes,
        candidates=candidates,
    )


def candidate_artifact_paths() -> list[Path]:
    paths = sorted(_DATA_DIR.glob(_DATA_GLOB))
    return paths or [_DATA_PATH]


def candidate_assets_by_key(path: Path | None = None) -> dict[str, CandidateSectionAsset]:
    artifact = load_section_bank_candidate_artifact(path)
    return {candidate.section_key: candidate for candidate in artifact.candidates}


def validate_section_bank_candidates(path: Path | None = None) -> list[str]:
    artifact = load_section_bank_candidate_artifact(path)
    issues: list[str] = []
    if artifact.schema_version != SECTION_BANK_CANDIDATE_SCHEMA_VERSION:
        issues.append(f"schema version mismatch: {artifact.schema_version}")

    seen_keys: set[str] = set()
    for candidate in artifact.candidates:
        if not candidate.section_key:
            issues.append("candidate missing section_key")
        if candidate.section_key in seen_keys:
            issues.append(f"duplicate candidate key: {candidate.section_key}")
        seen_keys.add(candidate.section_key)

        if candidate.domain not in {"money", "career", "love", "marriage", "personality", "life_timing"}:
            issues.append(f"{candidate.section_key}: unsupported domain {candidate.domain}")
        if not candidate.narrative_group:
            issues.append(f"{candidate.section_key}: missing narrative group")
        if len(candidate.selection_signal_hints) < 3:
            issues.append(f"{candidate.section_key}: selection hints too thin")
        if len(candidate.opening) < 2:
            issues.append(f"{candidate.section_key}: opening too thin")
        if len(candidate.main_body) < 8:
            issues.append(f"{candidate.section_key}: main body too thin")
        if len(candidate.compressed_summary) < 2:
            issues.append(f"{candidate.section_key}: compressed summary too thin")

        visible_text = " ".join(candidate.opening + candidate.main_body + candidate.compressed_summary)
        for fragment in _BANNED_VISIBLE_FRAGMENTS:
            if fragment in visible_text:
                issues.append(f"{candidate.section_key}: banned visible fragment: {fragment}")
        if "2026" in visible_text or "30세" in visible_text:
            issues.append(f"{candidate.section_key}: fixed timing leaked into candidate prose")

    return issues


def _candidate_from_payload(payload: dict[str, Any]) -> CandidateSectionAsset:
    return CandidateSectionAsset(
        section_key=str(payload.get("section_key", "")),
        source_key=str(payload.get("source_key", "")),
        customer_title=str(payload.get("customer_title", "")),
        domain=str(payload.get("domain", "")),
        narrative_group=str(payload.get("narrative_group", "")),
        selection_signal_hints=_string_list(payload.get("selection_signal_hints", [])),
        opening=_string_list(payload.get("opening", [])),
        main_body=_string_list(payload.get("main_body", [])),
        compressed_summary=_string_list(payload.get("compressed_summary", [])),
        awkward_words_to_avoid=_string_list(payload.get("awkward_words_to_avoid", [])),
        wording_notes=_string_list(payload.get("wording_notes", [])),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _load_single_artifact(path: Path) -> SectionBankCandidateArtifact:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return SectionBankCandidateArtifact(
        schema_version=str(payload.get("schema_version", "")),
        source=str(payload.get("source", "")),
        generation_notes=[str(item) for item in payload.get("generation_notes", [])],
        candidates=[
            _candidate_from_payload(item)
            for item in payload.get("candidates", [])
            if isinstance(item, dict)
        ],
    )
