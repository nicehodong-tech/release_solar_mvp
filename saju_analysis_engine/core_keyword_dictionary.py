from __future__ import annotations

from collections import deque
from functools import lru_cache
from pathlib import Path
import re
from typing import Any


def _compact(value: Any) -> str:
    return re.sub(r"[\s·ㆍ\-\(\)\[\]{}:：/|,.;]+", "", str(value or "").strip())


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


@lru_cache(maxsize=1)
def _find_dictionary_dir() -> Path | None:
    here = Path(__file__).resolve()
    for base in (here.parent, *here.parents):
        if not base.exists():
            continue
        preferred = base / "명리 핵심어 파일 2"
        if preferred.is_dir() and (preferred / "00_파일목록_및_검증값.txt").is_file():
            return preferred
        for child in base.iterdir():
            if not child.is_dir():
                continue
            try:
                md_files = list(child.glob("*.md"))
                txt_files = list(child.glob("*.txt"))
            except OSError:
                continue
            if len(md_files) >= 10 and any(file.name.startswith("00_") for file in txt_files):
                return child
    return None


def _table_keyword(line: str) -> str:
    if not line.lstrip().startswith("|"):
        return ""
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 2:
        return ""
    if any(set(cell) <= {"-", ":"} for cell in cells):
        return ""
    header_text = "".join(cells)
    if any(token in header_text for token in ("분류", "핵심어", "지지", "천간", "십신", "오행")):
        return ""
    term = cells[-1].strip()
    if not term or len(term) > 24:
        return ""
    return term


@lru_cache(maxsize=1)
def load_core_keyword_dictionary() -> tuple[dict[str, Any], ...]:
    root = _find_dictionary_dir()
    if root is None:
        return ()

    entries: list[dict[str, Any]] = []
    for file in sorted(root.glob("*.md")):
        text = _read_text(file)
        heading_stack: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    depth = len(stripped) - len(stripped.lstrip("#"))
                    heading_stack = heading_stack[: max(0, depth - 1)]
                    heading_stack.append(heading)
                continue
            term = _table_keyword(stripped)
            if not term:
                continue
            context = " ".join([file.stem, *heading_stack])
            search = _compact(f"{file.stem} {context} {term}")
            entries.append(
                {
                    "term": term,
                    "context": context,
                    "search": search,
                    "term_key": _compact(term),
                    "search_chars": frozenset(search),
                    "file": file.name,
                }
            )
    return tuple(entries)


@lru_cache(maxsize=4096)
def _core_keywords_for_query_cached(query_terms: tuple[str, ...], limit: int) -> tuple[str, ...]:
    if not query_terms or limit <= 0:
        return ()

    character_bits = _core_keyword_character_bits()
    query_items = tuple(
        (
            query,
            frozenset(query),
            _character_mask(query, character_bits),
            _core_keyword_term_keys_in_query(query),
            min(len(frozenset(query)), min(3, max(1, len(query) // 3))),
        )
        for query in query_terms
        if query
    )
    # Product queries usually contain dozens of source terms. Building a Python
    # hit-count dictionary for every character was slower than checking the
    # 3,320 precomputed integer masks directly. Integer bit_count performs the
    # same overlap gate in C and preserves the original ranking exactly.
    bit_groups = _core_keyword_search_bit_groups()
    ranked: list[tuple[int, int, str]] = []
    if len(query_items) == 1:
        query, _, query_mask, matched_term_keys, required_overlap = query_items[0]
        for term, group_mask, variants in bit_groups:
            if (query_mask & group_mask).bit_count() < required_overlap:
                continue
            for search, term_key, search_mask, order in variants:
                if query == term_key:
                    score = 10
                elif query in search:
                    score = 6
                elif term_key and term_key in matched_term_keys:
                    score = 5
                else:
                    overlap = (query_mask & search_mask).bit_count()
                    score = min(3, overlap) if overlap >= required_overlap else 0
                if score <= 0:
                    continue
                ranked.append((score, -order, term))
                break
        ranked.sort(reverse=True)
        return tuple(term for _, _, term in ranked[:limit])

    for term, group_mask, variants in bit_groups:
        if not any(
            (query_mask & group_mask).bit_count() >= required_overlap
            for _, _, query_mask, _, required_overlap in query_items
        ):
            continue
        for search, term_key, search_mask, order in variants:
            score = 0
            for query, _, query_mask, matched_term_keys, _ in query_items:
                if query == term_key:
                    score += 10
                elif query in search:
                    score += 6
                elif term_key and term_key in matched_term_keys:
                    score += 5
                else:
                    overlap = (query_mask & search_mask).bit_count()
                    if overlap >= min(3, max(1, len(query) // 3)):
                        score += min(3, overlap)
            if score <= 0:
                continue
            ranked.append((score, -order, term))
            break

    ranked.sort(reverse=True)
    return tuple(term for _, _, term in ranked[:limit])


@lru_cache(maxsize=1)
def _core_keyword_search_groups(
) -> tuple[tuple[str, tuple[tuple[str, str, frozenset[str], int], ...]], ...]:
    grouped: dict[str, list[tuple[str, str, frozenset[str], int]]] = {}
    for order, entry in enumerate(load_core_keyword_dictionary()):
        term = str(entry.get("term") or "").strip()
        if not term:
            continue
        search = str(entry.get("search") or "")
        term_key = str(entry.get("term_key") or _compact(term))
        search_chars = entry.get("search_chars")
        if not isinstance(search_chars, frozenset):
            search_chars = frozenset(search)
        grouped.setdefault(term, []).append((search, term_key, search_chars, order))
    return tuple((term, tuple(variants)) for term, variants in grouped.items())


@lru_cache(maxsize=1)
def _core_keyword_character_bits() -> dict[str, int]:
    characters: set[str] = set()
    for _, variants in _core_keyword_search_groups():
        for search, term_key, search_chars, _ in variants:
            characters.update(search_chars or frozenset(search))
            characters.update(term_key)
    return {character: index for index, character in enumerate(sorted(characters))}


def _character_mask(characters: Any, character_bits: dict[str, int]) -> int:
    mask = 0
    for character in characters:
        bit = character_bits.get(character)
        if bit is not None:
            mask |= 1 << bit
    return mask


@lru_cache(maxsize=1)
def _core_keyword_search_bit_groups(
) -> tuple[tuple[str, int, tuple[tuple[str, str, int, int], ...]], ...]:
    character_bits = _core_keyword_character_bits()
    bit_groups: list[tuple[str, int, tuple[tuple[str, str, int, int], ...]]] = []
    for term, variants in _core_keyword_search_groups():
        group_mask = 0
        bit_variants: list[tuple[str, str, int, int]] = []
        for search, term_key, search_chars, order in variants:
            search_mask = _character_mask(search_chars or frozenset(search), character_bits)
            group_mask |= search_mask
            group_mask |= _character_mask(term_key, character_bits)
            bit_variants.append((search, term_key, search_mask, order))
        bit_groups.append((term, group_mask, tuple(bit_variants)))
    return tuple(bit_groups)


@lru_cache(maxsize=1)
def _core_keyword_term_automaton(
) -> tuple[tuple[dict[str, int], ...], tuple[int, ...], tuple[frozenset[str], ...]]:
    transitions: list[dict[str, int]] = [{}]
    failures: list[int] = [0]
    outputs: list[set[str]] = [set()]

    term_keys = {
        term_key
        for _, variants in _core_keyword_search_groups()
        for _, term_key, _, _ in variants
        if term_key
    }
    for term_key in term_keys:
        state = 0
        for character in term_key:
            next_state = transitions[state].get(character)
            if next_state is None:
                next_state = len(transitions)
                transitions[state][character] = next_state
                transitions.append({})
                failures.append(0)
                outputs.append(set())
            state = next_state
        outputs[state].add(term_key)

    queue: deque[int] = deque()
    for state in transitions[0].values():
        queue.append(state)
    while queue:
        state = queue.popleft()
        for character, next_state in transitions[state].items():
            queue.append(next_state)
            fallback = failures[state]
            while fallback and character not in transitions[fallback]:
                fallback = failures[fallback]
            failures[next_state] = transitions[fallback].get(character, 0)
            outputs[next_state].update(outputs[failures[next_state]])

    return (
        tuple(transitions),
        tuple(failures),
        tuple(frozenset(values) for values in outputs),
    )


@lru_cache(maxsize=4096)
def _core_keyword_term_keys_in_query(query: str) -> frozenset[str]:
    if not query:
        return frozenset()
    transitions, failures, outputs = _core_keyword_term_automaton()
    state = 0
    matched: set[str] = set()
    for character in query:
        while state and character not in transitions[state]:
            state = failures[state]
        state = transitions[state].get(character, 0)
        if outputs[state]:
            matched.update(outputs[state])
    return frozenset(matched)


@lru_cache(maxsize=1)
def _core_keyword_group_character_index() -> dict[str, tuple[int, ...]]:
    index: dict[str, list[int]] = {}
    for group_index, (_, variants) in enumerate(_core_keyword_search_groups()):
        group_characters: set[str] = set()
        for search, term_key, search_chars, _ in variants:
            group_characters.update(search_chars or frozenset(search))
            group_characters.update(term_key)
        for character in group_characters:
            index.setdefault(character, []).append(group_index)
    return {character: tuple(group_indexes) for character, group_indexes in index.items()}


def core_keywords_for_query(*parts: Any, limit: int = 7) -> list[str]:
    query_terms = tuple(compacted for part in parts if (compacted := _compact(part)))
    return list(_core_keywords_for_query_cached(query_terms, int(limit or 0)))


def _section_heading_pattern(section_label: Any) -> re.Pattern[str] | None:
    label = str(section_label or "").strip()
    if not label:
        return None
    return re.compile(
        rf"(?<![가-힣A-Za-z0-9]){re.escape(label)}(?:\([^)]+\))?(?![가-힣A-Za-z0-9])"
    )


@lru_cache(maxsize=512)
def _core_keywords_for_exact_section_cached(
    section_label: str,
    file_name_contains: str,
    limit: int,
) -> tuple[str, ...]:
    pattern = _section_heading_pattern(section_label)
    if pattern is None or limit <= 0:
        return ()
    file_key = _compact(file_name_contains)
    preferred_entries: list[dict[str, Any]] = []
    fallback_entries: list[dict[str, Any]] = []
    for entry in load_core_keyword_dictionary():
        file_name = str(entry.get("file") or "")
        if file_key and file_key not in _compact(file_name):
            continue
        context = str(entry.get("context") or "")
        if not pattern.search(context):
            continue
        if "12개핵심어" in _compact(context):
            preferred_entries.append(entry)
        else:
            fallback_entries.append(entry)

    # 사전의 표나 관계 목록이 본문보다 먼저 나오는 경우가 있다. 고객 화면의
    # 원문 핵심어는 반드시 명시된 '12개 핵심어' 절을 우선하고, 해당 절이 없는
    # 사전만 기존 문맥 검색으로 보완한다.
    source_entries = preferred_entries or fallback_entries
    keywords: list[str] = []
    for entry in source_entries:
        term = str(entry.get("term") or "").strip()
        if term and term not in keywords:
            keywords.append(term)
        if len(keywords) >= limit:
            break
    return tuple(keywords)


def core_keywords_for_exact_section(
    section_label: Any,
    *,
    file_name_contains: str = "",
    limit: int = 12,
) -> list[str]:
    return list(
        _core_keywords_for_exact_section_cached(
            str(section_label or "").strip(),
            str(file_name_contains or "").strip(),
            int(limit or 0),
        )
    )


@lru_cache(maxsize=512)
def _core_section_heading_cached(
    section_label: str,
    file_name_contains: str,
) -> str:
    root = _find_dictionary_dir()
    pattern = _section_heading_pattern(section_label)
    if root is None or pattern is None:
        return ""
    file_key = _compact(file_name_contains)
    for file in sorted(root.glob("*.md")):
        if file_key and file_key not in _compact(file.name):
            continue
        for line in _read_text(file).splitlines():
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            heading = stripped.lstrip("#").strip()
            if pattern.search(heading):
                return heading
    return ""


def core_section_heading(
    section_label: Any,
    *,
    file_name_contains: str = "",
) -> str:
    """Return the exact heading used by the source dictionary section."""
    return _core_section_heading_cached(
        str(section_label or "").strip(),
        str(file_name_contains or "").strip(),
    )


@lru_cache(maxsize=512)
def _core_section_field_cached(
    section_label: str,
    file_name_contains: str,
    field_label: str,
) -> str:
    root = _find_dictionary_dir()
    pattern = _section_heading_pattern(section_label)
    if root is None or pattern is None:
        return ""
    file_key = _compact(file_name_contains)
    field = str(field_label or "").strip()
    if not field:
        return ""
    for file in sorted(root.glob("*.md")):
        if file_key and file_key not in _compact(file.name):
            continue
        lines = _read_text(file).splitlines()
        in_section = False
        section_depth = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                depth = len(stripped) - len(stripped.lstrip("#"))
                heading = stripped.lstrip("#").strip()
                if in_section and depth <= section_depth:
                    break
                if pattern.search(heading):
                    in_section = True
                    section_depth = depth
                continue
            if not in_section:
                continue
            match = re.match(rf"\*\*{re.escape(field)}:\*\*\s*(.+)", stripped)
            if match:
                return match.group(1).strip()
    return ""


def core_section_field(
    section_label: Any,
    field_label: str,
    *,
    file_name_contains: str = "",
) -> str:
    return _core_section_field_cached(
        str(section_label or "").strip(),
        str(file_name_contains or "").strip(),
        str(field_label or "").strip(),
    )


def _source_heading_matches(heading: str, section_label: str) -> bool:
    candidate = re.sub(r"^\d+\s*[.)]\s*", "", str(heading or "").strip())
    label = str(section_label or "").strip()
    if not candidate or not label:
        return False
    return (
        candidate == label
        or candidate.startswith(f"{label} ")
        or candidate.startswith(f"{label}(")
    )


@lru_cache(maxsize=1024)
def _core_source_section_profile_cached(
    section_label: str,
    file_name_contains: str,
) -> tuple[
    str,
    str,
    tuple[tuple[str, str], ...],
    tuple[tuple[str, tuple[str, ...]], ...],
    tuple[str, ...],
]:
    root = _find_dictionary_dir()
    if root is None:
        return "", "", (), (), ()
    file_key = _compact(file_name_contains)
    for file in sorted(root.glob("*.md")):
        if file_key and file_key not in _compact(file.name):
            continue
        lines = _read_text(file).splitlines()
        section_start = -1
        section_depth = 0
        source_heading = ""
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            depth = len(stripped) - len(stripped.lstrip("#"))
            heading = stripped.lstrip("#").strip()
            if _source_heading_matches(heading, section_label):
                section_start = index + 1
                section_depth = depth
                source_heading = heading
                break
        if section_start < 0:
            continue

        fields: list[tuple[str, str]] = []
        grouped_words: dict[str, list[str]] = {}
        group_order: list[str] = []
        keywords: list[str] = []
        in_keyword_table = False
        for line in lines[section_start:]:
            stripped = line.strip()
            if stripped.startswith("#"):
                depth = len(stripped) - len(stripped.lstrip("#"))
                heading = stripped.lstrip("#").strip()
                if depth <= section_depth:
                    break
                in_keyword_table = "12개 핵심어" in heading
                continue

            field_match = re.match(r"\*\*([^*：:]+)[：:]*\*\*\s*[：:]?\s*(.+)", stripped)
            if field_match:
                field_label = field_match.group(1).strip()
                field_value = field_match.group(2).strip().rstrip()
                if field_label and field_value:
                    fields.append((field_label, field_value))

            list_field_match = re.match(r"-\s*([^：:]+)[：:]\s*(.+)", stripped)
            if list_field_match:
                field_label = list_field_match.group(1).strip()
                field_value = list_field_match.group(2).strip().rstrip()
                if field_label and field_value:
                    fields.append((field_label, field_value))

            if not stripped.startswith("|"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 2:
                continue
            if cells[0] in {"분류", "구분"} and cells[-1] == "핵심어":
                in_keyword_table = True
                continue
            if any(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if not in_keyword_table:
                continue
            tag = cells[0]
            word = cells[-1]
            if tag in {"분류", "구분"} or word == "핵심어" or not tag or not word:
                continue
            if tag not in grouped_words:
                grouped_words[tag] = []
                group_order.append(tag)
            if word not in grouped_words[tag]:
                grouped_words[tag].append(word)
            if word not in keywords:
                keywords.append(word)

        groups = tuple((tag, tuple(grouped_words[tag])) for tag in group_order)
        return file.name, source_heading, tuple(fields), groups, tuple(keywords)
    return "", "", (), (), ()


def core_source_section_profile(
    section_label: Any,
    *,
    file_name_contains: str,
    description_fields: tuple[str, ...] = ("한 줄 핵심", "작용 구조", "배합 구조"),
    keyword_limit: int = 12,
) -> dict[str, Any]:
    """Return an exact, source-verifiable section from 명리 핵심어 파일 2."""
    file_name, source_heading, field_pairs, group_pairs, keywords = (
        _core_source_section_profile_cached(
            str(section_label or "").strip(),
            str(file_name_contains or "").strip(),
        )
    )
    if not file_name or not source_heading:
        return {}
    fields = dict(field_pairs)
    description_parts = [
        fields[field]
        for field in description_fields
        if fields.get(field)
    ]
    limited_keywords = list(keywords[: max(0, int(keyword_limit or 0))])
    allowed = set(limited_keywords)
    groups = [
        {"tag": tag, "words": [word for word in words if word in allowed]}
        for tag, words in group_pairs
        if any(word in allowed for word in words)
    ]
    return {
        "source_verified": True,
        "source_file": file_name,
        "source_section": source_heading,
        "title": source_heading,
        "fields": fields,
        "description_parts": description_parts,
        "description": " ".join(description_parts),
        "groups": groups,
        "keywords": limited_keywords,
    }
