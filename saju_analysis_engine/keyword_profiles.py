"""Keyword profile lookup for branch relations and auxiliary stars."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data" / "keyword_profiles"
BRANCH_RELATION_PROFILE_PATH = DATA_DIR / "branch_relation_keyword_profiles.jsonl"
SHINSAL_PROFILE_PATH = DATA_DIR / "shinsal_keyword_profiles.jsonl"

BRANCH_HANJA = {
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

BRANCH_LABELS = {
    "ja": "자",
    "chuk": "축",
    "in": "인",
    "myo": "묘",
    "jin": "진",
    "sa": "사",
    "o": "오",
    "mi": "미",
    "sin": "신",
    "yu": "유",
    "sul": "술",
    "hae": "해",
}

BRANCH_ORDER = {
    "ja": 1,
    "chuk": 2,
    "in": 3,
    "myo": 4,
    "jin": 5,
    "sa": 6,
    "o": 7,
    "mi": 8,
    "sin": 9,
    "yu": 10,
    "sul": 11,
    "hae": 12,
}

THREE_HARMONY_HANJA = {
    frozenset(("sin", "ja", "jin")): "申子辰 三合水局",
    frozenset(("hae", "myo", "mi")): "亥卯未 三合木局",
    frozenset(("in", "o", "sul")): "寅午戌 三合火局",
    frozenset(("sa", "yu", "chuk")): "巳酉丑 三合金局",
}

THREE_MEETING_HANJA = {
    frozenset(("in", "myo", "jin")): "寅卯辰 方合木",
    frozenset(("sa", "o", "mi")): "巳午未 方合火",
    frozenset(("sin", "yu", "sul")): "申酉戌 方合金",
    frozenset(("hae", "ja", "chuk")): "亥子丑 方合水",
}

HALF_HARMONY_HANJA = {
    frozenset(("sin", "ja")): "申子 半合水",
    frozenset(("ja", "jin")): "子辰 半合水",
    frozenset(("sin", "jin")): "申辰 拱水",
    frozenset(("hae", "myo")): "亥卯 半合木",
    frozenset(("myo", "mi")): "卯未 半合木",
    frozenset(("hae", "mi")): "亥未 拱木",
    frozenset(("in", "o")): "寅午 半合火",
    frozenset(("o", "sul")): "午戌 半合火",
    frozenset(("in", "sul")): "寅戌 拱火",
    frozenset(("sa", "yu")): "巳酉 半合金",
    frozenset(("yu", "chuk")): "酉丑 半合金",
    frozenset(("sa", "chuk")): "巳丑 拱金",
}

PAIR_SUFFIX_BY_RELATION = {
    "six_combine": "合",
    "clash": "冲",
    "punishment": "刑",
    "self_punishment": "自刑",
    "harm": "害",
    "break": "破",
}

RELATION_PRIORITY = {
    "three_harmony": 96,
    "three_meeting": 94,
    "clash": 91,
    "punishment": 88,
    "self_punishment": 86,
    "six_combine": 84,
    "three_harmony_half": 80,
    "harm": 76,
    "break": 74,
}

SHINSAL_PRIORITY_BY_CATEGORY = {
    "12신살": 80,
    "핵심 신살": 76,
    "실무 신살": 70,
}

# The engine keeps formula-specific keys, while the customer source dictionary
# owns the canonical public names.  This registry is the only bridge between
# them; aliases never create a second customer card.
SHINSAL_SOURCE_NAME_BY_ENGINE_KEY = {
    "geopsal": "겁살",
    "jaesal": "재살",
    "cheonsal": "천살",
    "jisal": "지살",
    "yeonsal": "연살",
    "wolsal": "월살",
    "mangsin_sal": "망신살",
    "jangseong_sal": "장성살",
    "banan_sal": "반안살",
    "yeokma_sal": "역마살",
    "yukhae_sal": "육해살",
    "hwagae_sal": "화개살",
    "geumyeo": "금여",
    "cheoneul_day": "천을귀인",
    "cheoneul_year": "천을귀인",
    "cheondeok": "천덕귀인",
    "woldeok": "월덕귀인",
    "taegeuk": "태극귀인",
    "moonchang_modern": "문창귀인",
    "moonchang_classic": "문창귀인",
    "hakdang": "학당귀인",
    "gukin": "국인귀인",
    "honglan": "홍란성",
    "cheonhui": "천희성",
    "yangin_strict": "양인살",
    "yangin_expanded": "양인살",
    "gongmang": "공망",
    "gojin": "고진살",
    "gwasuk": "과숙살",
    "cheonra": "천라지망",
    "jimang": "천라지망",
    "sipak_daepae": "십악대패",
    "eumyang_chachak": "음양차착",
    "goegang": "괴강살",
    "baekho": "백호대살",
    "hongyeom": "홍염살",
    "goran": "고란살",
    "paljeon": "팔전살",
    "guchu": "구추방해",
    "gwimun": "귀문관살",
    "wonjin": "원진살",
    "hyeonchim": "현침살",
    "cheolshoe": "철쇄개금",
    "cheonmun": "천문성",
}

SAFE_MISC_PRODUCT_CANDIDATES = {"shinsal_038"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


@lru_cache(maxsize=1)
def _branch_relation_profiles() -> list[dict[str, Any]]:
    return _read_jsonl(BRANCH_RELATION_PROFILE_PATH)


@lru_cache(maxsize=1)
def _shinsal_profiles() -> list[dict[str, Any]]:
    return _read_jsonl(SHINSAL_PROFILE_PATH)


@lru_cache(maxsize=1)
def _branch_relation_profile_by_hanja() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for item in _branch_relation_profiles():
        hanja = str(item.get("hanja") or "").strip()
        if hanja:
            profiles[hanja] = item
    return profiles


@lru_cache(maxsize=1)
def _shinsal_profiles_by_name() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for item in _shinsal_profiles():
        names = [item.get("name"), item.get("hanja"), *(item.get("aliases") or [])]
        for name in names:
            key = str(name or "").strip()
            if key and key not in profiles:
                profiles[key] = item
    return profiles


def _ordered_pair(branches: list[str]) -> list[str]:
    return sorted([branch for branch in branches if branch in BRANCH_HANJA], key=lambda item: BRANCH_ORDER[item])


def _hanja_pair(branches: list[str]) -> str:
    return "".join(BRANCH_HANJA[branch] for branch in branches if branch in BRANCH_HANJA)


def _pair_candidates(branches: list[str], suffix: str) -> list[str]:
    ordered = _ordered_pair(branches)
    if len(ordered) < 2:
        return []
    forward = _hanja_pair(ordered[:2]) + suffix
    backward = _hanja_pair(list(reversed(ordered[:2]))) + suffix
    candidates = [forward]
    if backward != forward:
        candidates.append(backward)
    return candidates


def _relation_hanja_candidates(interaction: Any) -> list[str]:
    relation_type = str(getattr(interaction, "relation_type", "") or "")
    branches = [str(branch) for branch in list(getattr(interaction, "branches", []) or [])]
    branch_set = frozenset(branches)
    if relation_type == "three_harmony":
        return [THREE_HARMONY_HANJA[branch_set]] if branch_set in THREE_HARMONY_HANJA else []
    if relation_type == "three_meeting":
        return [THREE_MEETING_HANJA[branch_set]] if branch_set in THREE_MEETING_HANJA else []
    if relation_type == "three_harmony_half":
        return [HALF_HARMONY_HANJA[branch_set]] if branch_set in HALF_HARMONY_HANJA else []
    if relation_type == "self_punishment":
        ordered = _ordered_pair(branches)
        if not ordered:
            return []
        return [BRANCH_HANJA[ordered[0]] + BRANCH_HANJA[ordered[0]] + "自刑"]
    suffix = PAIR_SUFFIX_BY_RELATION.get(relation_type)
    if suffix:
        return _pair_candidates(branches, suffix)
    return []


def _keyword_groups_from_rows(rows: Any) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    group_map: dict[str, list[str]] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, list) or len(row) < 2:
                continue
            tag = str(row[0] or "").strip()
            word = str(row[1] or "").strip()
            if not tag or not word:
                continue
            group_map.setdefault(tag, [])
            if word not in group_map[tag]:
                group_map[tag].append(word)
    for tag, words in group_map.items():
        groups.append({"tag": tag, "words": words})
    return groups


def _keyword_groups_from_keyword_items(items: Any) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    group_map: dict[str, list[str]] = {}
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            tag = str(item.get("tag") or "").strip()
            word = str(item.get("word") or "").strip()
            if not tag or not word:
                continue
            group_map.setdefault(tag, [])
            if word not in group_map[tag]:
                group_map[tag].append(word)
    for tag, words in group_map.items():
        groups.append({"tag": tag, "words": words})
    return groups


def _flatten_groups(groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    keywords: list[dict[str, str]] = []
    for group in groups:
        tag = str(group.get("tag") or "").strip()
        for word in group.get("words") or []:
            text = str(word or "").strip()
            if tag and text:
                keywords.append({"tag": tag, "word": text})
    return keywords


def branch_relation_keyword_profile(interaction: Any) -> dict[str, Any] | None:
    profiles = _branch_relation_profile_by_hanja()
    matched: dict[str, Any] | None = None
    matched_hanja = ""
    for hanja in _relation_hanja_candidates(interaction):
        if hanja in profiles:
            matched = profiles[hanja]
            matched_hanja = hanja
            break
    if not matched:
        return None
    groups = _keyword_groups_from_rows(matched.get("rows"))
    branches = [str(branch) for branch in list(getattr(interaction, "branches", []) or [])]
    return {
        "kind": "branch_relation",
        "type": matched.get("type"),
        "name": matched.get("name"),
        "hanja": matched.get("hanja") or matched_hanja,
        "relation_type": getattr(interaction, "relation_type", ""),
        "branches": branches,
        "branch_labels": [BRANCH_LABELS.get(branch, branch) for branch in branches],
        "positions": list(getattr(interaction, "positions", []) or []),
        "effect_element": getattr(interaction, "effect_element", ""),
        "intensity": getattr(interaction, "intensity", ""),
        "priority": RELATION_PRIORITY.get(str(getattr(interaction, "relation_type", "") or ""), 60),
        "groups": groups,
        "keywords": _flatten_groups(groups),
    }


def branch_relation_keyword_profiles(interactions: Any, limit: int = 10) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for interaction in list(interactions or []):
        profile = branch_relation_keyword_profile(interaction)
        if not profile:
            continue
        key = str(profile.get("hanja") or profile.get("name") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        profiles.append(profile)
    profiles.sort(key=lambda item: (int(item.get("priority") or 0), len(item.get("keywords") or [])), reverse=True)
    return profiles[:limit]


def _signal_value(signal: Any, key: str, default: Any = None) -> Any:
    if isinstance(signal, dict):
        return signal.get(key, default)
    return getattr(signal, key, default)


def _signal_list(signal: Any, key: str) -> list[Any]:
    value = _signal_value(signal, key, [])
    return list(value or []) if isinstance(value, (list, tuple, set)) else []


def _activation_years_from_basis_codes(basis_codes: list[Any]) -> list[int]:
    years: list[int] = []
    for raw in basis_codes:
        text = str(raw or "")
        if not text.startswith("target_year:"):
            continue
        try:
            year = int(text.split(":", 1)[1])
        except (TypeError, ValueError):
            continue
        if year not in years:
            years.append(year)
    return sorted(years)


def shinsal_keyword_profile(signal: Any, *, product_only: bool = True) -> dict[str, Any] | None:
    profiles = _shinsal_profiles_by_name()
    engine_key = str(_signal_value(signal, "key", "") or "").strip()
    canonical_name = SHINSAL_SOURCE_NAME_BY_ENGINE_KEY.get(engine_key, "")
    candidates = [
        canonical_name,
        str(_signal_value(signal, "label", "") or "").strip(),
        engine_key,
        str(_signal_value(signal, "formula_name", "") or "").strip(),
    ]
    matched: dict[str, Any] | None = None
    for candidate in candidates:
        if candidate in profiles:
            matched = profiles[candidate]
            break
    if not matched:
        return None
    usage = str(matched.get("usage") or "").strip()
    basis_codes = [str(value) for value in _signal_list(signal, "basis_codes") if str(value)]
    is_safe_candidate = bool(
        str(matched.get("id") or "") in SAFE_MISC_PRODUCT_CANDIDATES
        and "full_set:myo_yu_sul" in basis_codes
        and "partial_set_with_day" not in basis_codes
    )
    if product_only and usage != "상품용" and not is_safe_candidate:
        return None
    groups = _keyword_groups_from_keyword_items(matched.get("keywords"))
    category = str(matched.get("category") or "").strip()
    formula_name = str(_signal_value(signal, "formula_name", "") or "").strip()
    positions = [str(value) for value in _signal_list(signal, "positions") if str(value)]
    pillar_labels = [str(value) for value in _signal_list(signal, "pillar_labels") if str(value)]
    activation_years = _activation_years_from_basis_codes(basis_codes)
    return {
        "kind": "shinsal",
        "source_id": matched.get("id"),
        "category": category,
        "usage": "상품후보" if is_safe_candidate and usage != "상품용" else usage,
        "source_usage": usage,
        "promotion_status": "safe_candidate" if is_safe_candidate else "approved_product_source",
        "exposure_scope": "comprehensive_basis_only",
        "name": matched.get("name"),
        "hanja": matched.get("hanja"),
        "aliases": list(matched.get("aliases") or []),
        "one_line": str(matched.get("one_line") or ""),
        "positions": positions,
        "pillar_labels": pillar_labels,
        "domains": [str(value) for value in _signal_list(signal, "domains") if str(value)],
        "intensity": _signal_value(signal, "intensity", ""),
        "formula_names": [formula_name] if formula_name else [],
        "basis_codes": basis_codes,
        "activation_years": activation_years,
        "occurrences": [
            {
                "engine_key": engine_key,
                "formula_name": formula_name,
                "positions": positions,
                "pillar_labels": pillar_labels,
                "basis_codes": basis_codes,
                "activation_years": activation_years,
            }
        ],
        "priority": SHINSAL_PRIORITY_BY_CATEGORY.get(category, 50),
        "groups": groups,
        "keywords": _flatten_groups(groups),
    }


def shinsal_keyword_profiles(signals: Any, limit: int = 8, *, product_only: bool = True) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for signal in list(signals or []):
        profile = shinsal_keyword_profile(signal, product_only=product_only)
        if not profile:
            continue
        key = str(profile.get("source_id") or profile.get("hanja") or profile.get("name") or "")
        if key not in merged:
            merged[key] = profile
            continue
        target = merged[key]
        for field in (
            "aliases",
            "positions",
            "pillar_labels",
            "domains",
            "formula_names",
            "basis_codes",
            "activation_years",
        ):
            target[field] = list(dict.fromkeys([*(target.get(field) or []), *(profile.get(field) or [])]))
        occurrence_keys = {
            (
                str(item.get("engine_key") or ""),
                str(item.get("formula_name") or ""),
                tuple(item.get("positions") or []),
                tuple(item.get("activation_years") or []),
            )
            for item in target.get("occurrences") or []
            if isinstance(item, dict)
        }
        for occurrence in profile.get("occurrences") or []:
            if not isinstance(occurrence, dict):
                continue
            occurrence_key = (
                str(occurrence.get("engine_key") or ""),
                str(occurrence.get("formula_name") or ""),
                tuple(occurrence.get("positions") or []),
                tuple(occurrence.get("activation_years") or []),
            )
            if occurrence_key not in occurrence_keys:
                target.setdefault("occurrences", []).append(occurrence)
                occurrence_keys.add(occurrence_key)
        if profile.get("usage") == "상품용":
            target["usage"] = "상품용"
            target["promotion_status"] = "approved_product_source"
    profiles = list(merged.values())
    for profile in profiles:
        profile["activation_years"] = sorted(
            int(value) for value in profile.get("activation_years") or [] if isinstance(value, int)
        )
    profiles.sort(key=lambda item: (int(item.get("priority") or 0), len(item.get("keywords") or [])), reverse=True)
    return profiles[:limit]


def annotate_shinsal_structure_alignment(
    profiles: Any,
    contextual_profile: Any,
) -> list[dict[str, Any]]:
    """Record structural correspondence without changing any score or keyword."""

    contextual = contextual_profile if isinstance(contextual_profile, dict) else {}
    domain_map = contextual.get("domain_action_map") if isinstance(contextual.get("domain_action_map"), dict) else {}
    actions = [item for item in contextual.get("contextual_actions") or [] if isinstance(item, dict)]
    annotated: list[dict[str, Any]] = []
    for raw_profile in list(profiles or []):
        if not isinstance(raw_profile, dict):
            continue
        profile = dict(raw_profile)
        domains = [str(value) for value in profile.get("domains") or [] if str(value)]
        positions = [str(value) for value in profile.get("positions") or [] if str(value)]
        formulas = [str(value) for value in profile.get("formula_names") or [] if str(value)]
        month_order_match = "month" in positions or any("month" in formula for formula in formulas)
        matched_domains: list[str] = []
        supported_domains: list[str] = []
        burden_domains: list[str] = []
        for domain in domains:
            domain_state = domain_map.get(domain)
            if not isinstance(domain_state, dict):
                continue
            matched_domains.append(domain)
            net = float(domain_state.get("net") or 0.0)
            state = str(domain_state.get("state") or "")
            if net > 0 or state in {"support", "favorable", "strong"}:
                supported_domains.append(domain)
            elif net < 0 or state in {"burden", "pressure", "caution"}:
                burden_domains.append(domain)
        action_matches = []
        for action in actions:
            priorities = [str(value) for value in action.get("domain_priority") or [] if str(value)]
            overlap = [domain for domain in domains if domain in priorities]
            if not overlap:
                continue
            action_matches.append(
                {
                    "action_id": str(action.get("action_id") or action.get("action_key") or ""),
                    "verdict": str(action.get("verdict") or ""),
                    "presence_score": int(action.get("presence_score") or 0),
                    "domains": overlap,
                }
            )
        if month_order_match and action_matches:
            alignment_key = "month_order_and_structure"
            alignment_label = "월령·구조 일치"
        elif matched_domains or action_matches:
            alignment_key = "structural_correspondence"
            alignment_label = "구조 연동"
        else:
            alignment_key = "auxiliary_only"
            alignment_label = "보조 근거"
        profile["structure_alignment"] = {
            "key": alignment_key,
            "label": alignment_label,
            "month_order_match": month_order_match,
            "matched_domains": matched_domains,
            "supported_domains": supported_domains,
            "burden_domains": burden_domains,
            "ten_god_action_matches": action_matches,
            "score_influence": False,
        }
        annotated.append(profile)
    return annotated
