"""Stem, hidden-stem, stem-branch, and ten-god combination signals."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .models import CombinationProfile, CombinationSignal, PositionSignal
from .ten_gods import main_hidden_stem, ten_god_for


POSITION_ORDER = ("year", "month", "day", "hour")
STEM_ORDER = ("gap", "eul", "byeong", "jeong", "mu", "gi", "gyeong", "sin", "im", "gye")
SERVICE_DOMAINS = ("money", "career", "love", "marriage")

STEM_HANJA = {
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

TEN_GOD_LABELS = {
    "self": "일간",
    "bi_gyeon": "비견",
    "geob_jae": "겁재",
    "sik_sin": "식신",
    "sang_gwan": "상관",
    "pyeon_jae": "편재",
    "jeong_jae": "정재",
    "pyeon_gwan": "편관",
    "jeong_gwan": "정관",
    "pyeon_in": "편인",
    "jeong_in": "정인",
}

RELATION_DOMAINS = {
    "element_generation": ["money", "career"],
    "element_control": ["career", "marriage"],
    "same_element_density": ["money", "career"],
    "visible_stem_root": ["career", "marriage"],
    "hidden_stem_protrusion": ["career", "money"],
    "output_wealth_chain": ["money", "career"],
    "wealth_officer_chain": ["money", "career"],
    "officer_resource_chain": ["career", "marriage"],
    "resource_self_chain": ["career"],
    "officer_resource_self_chain": ["career", "marriage"],
    "peer_output_wealth_chain": ["money", "career"],
    "output_wealth_officer_chain": ["money", "career"],
    "resource_peer_support": ["career", "money"],
    "officer_self_pressure": ["career", "marriage"],
    "officer_peer_pressure": ["career", "marriage", "money"],
    "peer_wealth_competition": ["money"],
    "hurting_officer_meets_officer": ["career", "marriage"],
    "resource_output_friction": ["career", "money"],
    "indirect_resource_food_block": ["career", "money"],
    "peer_density": ["money", "career"],
}

COUNTER_RELATIONS = {
    "officer_self_pressure",
    "officer_peer_pressure",
    "peer_wealth_competition",
    "hurting_officer_meets_officer",
    "resource_output_friction",
    "indirect_resource_food_block",
    "peer_density",
}

RELATION_INTERPRETATIONS = {
    "element_generation": "서로 생하는 오행이 연결되어 능력, 학습, 실무 결과가 다음 단계로 이어집니다.",
    "element_control": "서로 극하는 오행이 함께 있어 기준, 압박, 조정의 요구가 분명합니다.",
    "same_element_density": "같은 오행이 겹쳐 자기 기준과 반복성이 강해집니다.",
    "visible_stem_root": "천간의 글자가 지지 안에서 뿌리를 얻어 겉으로 보이는 성향이 생활 기반까지 이어집니다.",
    "hidden_stem_protrusion": "지지 안의 성분이 천간으로 투출되어 속에 있던 욕구나 역할이 실제 행동으로 확인됩니다.",
    "output_wealth_chain": "표현, 기술, 생산성이 수입과 거래 조건으로 이어지는 식상생재 성격이 확인됩니다.",
    "wealth_officer_chain": "재성의 현실 감각이 관성의 직위, 평가, 책임으로 이어져 사회적 성취와 연결됩니다.",
    "officer_resource_chain": "규칙, 평가, 책임이 학습, 자격, 명분과 결합하여 직업 안정성을 높입니다.",
    "resource_self_chain": "지식, 보호, 자격이 일간을 받쳐 판단의 지속성과 회복력을 보강합니다.",
    "officer_resource_self_chain": "책임과 평가가 학습, 자격, 자기 관리로 흡수되는 관인상생 계열의 작용이 있습니다.",
    "peer_output_wealth_chain": "동료, 실행력, 생산성이 수익 조건으로 이어질 수 있어 일의 규모를 키우는 데 유리합니다.",
    "output_wealth_officer_chain": "생산성과 수익이 사회적 책임 또는 직위로 이어질 수 있습니다.",
    "resource_peer_support": "지식과 보호가 자기 주장이나 동료 관계를 키웁니다. 자기 기준도 쉽게 굳어집니다.",
    "officer_self_pressure": "책임, 규칙, 평가가 당신을 직접 압박하므로 직업 책임감과 긴장감이 함께 커집니다.",
    "officer_peer_pressure": "규칙과 경쟁심이 함께 있어 조직, 동료, 금전 판단에서 긴장과 비교가 생기기 쉽습니다.",
    "peer_wealth_competition": "비겁과 재성이 맞물려 돈을 벌 기회와 나눠야 할 부담이 함께 생깁니다.",
    "hurting_officer_meets_officer": "상관과 관성이 함께 작용해 표현력은 강하지만 평가, 규칙, 권위와 마찰이 생길 수 있습니다.",
    "resource_output_friction": "인성과 식상이 함께 있어 생각과 실행 사이의 검열이 커질 수 있습니다.",
    "indirect_resource_food_block": "편인이 식신을 누르는 성격이 있어 능력은 있어도 행동이 늦어지거나 자기 검열이 강해질 수 있습니다.",
    "peer_density": "비견과 겁재 성분이 겹쳐 자기 주도성은 강하지만 경쟁, 분산, 독립 판단이 커집니다.",
}


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult):
    pillars = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar
    return pillars


def _canonical_stems(stems: list[str]) -> list[str]:
    return sorted(stems, key=lambda stem: STEM_ORDER.index(stem))


def _combination_key(stems: list[str]) -> str:
    return "-".join(_canonical_stems(stems))


def _hanja_key(stems: list[str]) -> str:
    return "".join(STEM_HANJA[stem] for stem in _canonical_stems(stems))


def _group_for(ten_god: str) -> str:
    if ten_god == "self":
        return "self"
    return TEN_GOD_GROUPS[ten_god]


def _groups_for(ten_gods: list[str]) -> set[str]:
    return {_group_for(ten_god) for ten_god in ten_gods}


def _position_sort_key(position: str) -> int:
    base = position.split(":", 1)[0]
    return POSITION_ORDER.index(base) if base in POSITION_ORDER else 99


def _relation_from_elements(stems: list[str], ten_gods: list[str]) -> str:
    if len(stems) == 2:
        first, second = _canonical_stems(stems)
        first_element = STEM_METADATA[first]["element"]
        second_element = STEM_METADATA[second]["element"]
        groups = _groups_for(ten_gods)
        ten_god_set = set(ten_gods)
        if groups == {"self", "peer"} or groups == {"peer"}:
            return "peer_density"
        if "peer" in groups and "wealth" in groups:
            return "peer_wealth_competition"
        if "officer" in groups and "peer" in groups:
            return "officer_peer_pressure"
        if "officer" in groups and "self" in groups:
            return "officer_self_pressure"
        if "officer" in groups and "resource" in groups:
            return "officer_resource_chain"
        if "resource" in groups and ("self" in groups or "peer" in groups):
            return "resource_self_chain" if "self" in groups else "resource_peer_support"
        if "output" in groups and "wealth" in groups:
            return "output_wealth_chain"
        if "wealth" in groups and "officer" in groups:
            return "wealth_officer_chain"
        if "output" in groups and "officer" in groups:
            return "hurting_officer_meets_officer" if "sang_gwan" in ten_god_set else "element_control"
        if "resource" in groups and "output" in groups:
            if "pyeon_in" in ten_god_set and "sik_sin" in ten_god_set:
                return "indirect_resource_food_block"
            return "resource_output_friction"
        if first_element == second_element:
            return "same_element_density"
        if ELEMENT_GENERATES[first_element] == second_element or ELEMENT_GENERATES[second_element] == first_element:
            return "element_generation"
        if ELEMENT_CONTROLS[first_element] == second_element or ELEMENT_CONTROLS[second_element] == first_element:
            return "element_control"
        return "neutral"

    groups = _groups_for(ten_gods)
    ten_god_set = set(ten_gods)
    if {"officer", "resource", "self"}.issubset(groups):
        return "officer_resource_self_chain"
    if {"peer", "output", "wealth"}.issubset(groups):
        return "peer_output_wealth_chain"
    if {"output", "wealth", "officer"}.issubset(groups):
        return "output_wealth_officer_chain"
    if "peer" in groups and "wealth" in groups and "officer" in groups:
        return "officer_peer_pressure"
    if "peer" in groups and "wealth" in groups:
        return "peer_wealth_competition"
    if "output" in groups and "officer" in groups:
        return "hurting_officer_meets_officer" if "sang_gwan" in ten_god_set else "element_control"
    return "neutral"


def _domains_for_relation(relation_type: str, positions: list[str]) -> list[str]:
    domains = list(RELATION_DOMAINS.get(relation_type, []))
    position_domains = {
        "year": ["career", "love"],
        "month": ["career", "money"],
        "day": ["love", "marriage"],
        "hour": ["career", "money", "marriage"],
    }
    for position in positions:
        base = position.split(":", 1)[0]
        domains.extend(position_domains.get(base, []))
    return [domain for domain in SERVICE_DOMAINS if domain in set(domains)]


def _strength_from_entries(entries: list[dict[str, Any]]) -> str:
    if all(entry["source"] == "visible" for entry in entries):
        return "high"
    if any(entry["source"] == "visible" for entry in entries):
        return "moderate"
    weight = sum(float(entry.get("weight", 0.0)) for entry in entries)
    return "moderate" if weight >= 1.1 else "low"


def _signal(
    *,
    layer: str,
    relation_type: str,
    entries: list[dict[str, Any]],
    signal_suffix: str,
    strength: str | None = None,
) -> CombinationSignal:
    stems = [entry["stem"] for entry in entries]
    ten_gods = [entry["ten_god"] for entry in entries]
    positions = [entry["position"] for entry in entries]
    branches = [entry["branch"] for entry in entries if entry.get("branch")]
    elements = [STEM_METADATA[stem]["element"] for stem in stems]
    key = _combination_key(stems)
    basis_codes = [
        f"combo_{layer}_{relation_type}",
        f"combo_{layer}_{key.replace('-', '_')}",
    ]
    counter_signals = [f"combo_counter_{relation_type}"] if relation_type in COUNTER_RELATIONS else []
    labels = ", ".join(TEN_GOD_LABELS.get(item, item) for item in ten_gods)
    interpretation = RELATION_INTERPRETATIONS.get(relation_type, "타고난 글자 배합에서 성향과 생활 방식이 함께 읽힙니다.")
    return CombinationSignal(
        signal_id=f"{layer}_{signal_suffix}_{key.replace('-', '_')}",
        layer=layer,
        relation_type=relation_type,
        combination_key=key,
        positions=sorted(list(dict.fromkeys(positions)), key=_position_sort_key),
        stems=_canonical_stems(stems),
        branches=list(dict.fromkeys(branches)),
        elements=[STEM_METADATA[stem]["element"] for stem in _canonical_stems(stems)],
        ten_gods=list(dict.fromkeys(ten_gods)),
        strength=strength or _strength_from_entries(entries),
        domain_links=_domains_for_relation(relation_type, positions),
        basis_codes=basis_codes,
        counter_signals=counter_signals,
        interpretation=f"{_hanja_key(stems)} 배합은 {labels}의 연결로 보며, {interpretation}",
    )


def _visible_entries(chart: BirthChartResult, position_signals: dict[str, PositionSignal]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        signal = position_signals[position]
        entries.append(
            {
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "ten_god": signal.stem_ten_god,
                "weight": POSITION_STEM_WEIGHTS[position],
            }
        )
    return entries


def _hidden_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        for index, (stem_key, hidden_weight) in enumerate(BRANCH_HIDDEN_STEMS[pillar.branch_key]):
            entries.append(
                {
                    "position": f"{position}:hidden:{index}",
                    "source": "hidden",
                    "stem": stem_key,
                    "branch": pillar.branch_key,
                    "ten_god": "self" if position == "day" and stem_key == chart.day_pillar.stem_key else ten_god_for(chart.day_pillar.stem_key, stem_key),
                    "weight": POSITION_BRANCH_WEIGHTS[position] * hidden_weight,
                }
            )
    return entries


def _visible_stem_signals(visible_entries: list[dict[str, Any]]) -> list[CombinationSignal]:
    signals: list[CombinationSignal] = []
    for size in (2, 3):
        for index, entries in enumerate(combinations(visible_entries, size), start=1):
            entry_list = list(entries)
            relation_type = _relation_from_elements(
                [entry["stem"] for entry in entry_list],
                [entry["ten_god"] for entry in entry_list],
            )
            if relation_type == "neutral":
                continue
            signals.append(
                _signal(
                    layer="heavenly_stem",
                    relation_type=relation_type,
                    entries=entry_list,
                    signal_suffix=f"{size}_{index}",
                    strength="high",
                )
            )
    return signals


def _hidden_stem_signals(
    visible_entries: list[dict[str, Any]],
    hidden_entries: list[dict[str, Any]],
) -> list[CombinationSignal]:
    signals: list[CombinationSignal] = []
    visible_by_stem: dict[str, list[dict[str, Any]]] = {}
    for entry in visible_entries:
        visible_by_stem.setdefault(entry["stem"], []).append(entry)

    for index, hidden in enumerate(hidden_entries, start=1):
        for visible in visible_by_stem.get(hidden["stem"], []):
            relation_entries = [hidden, visible]
            signals.append(
                _signal(
                    layer="hidden_stem",
                    relation_type="hidden_stem_protrusion",
                    entries=relation_entries,
                    signal_suffix=f"protrusion_{index}",
                    strength="moderate",
                )
            )

    pair_index = 0
    for first, second in combinations(hidden_entries, 2):
        relation_entries = [first, second]
        relation_type = _relation_from_elements(
            [entry["stem"] for entry in relation_entries],
            [entry["ten_god"] for entry in relation_entries],
        )
        if relation_type == "neutral":
            continue
        pair_index += 1
        signals.append(
            _signal(
                layer="hidden_stem",
                relation_type=relation_type,
                entries=relation_entries,
                signal_suffix=f"pair_{pair_index}",
            )
        )
    return _dedupe_signals(signals, limit=28)


def _stem_branch_signals(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> list[CombinationSignal]:
    signals: list[CombinationSignal] = []
    for position, pillar in _pillars(chart).items():
        signal = position_signals[position]
        main_stem = main_hidden_stem(pillar.branch_key)
        visible_entry = {
            "position": f"{position}:stem",
            "source": "visible",
            "stem": pillar.stem_key,
            "branch": pillar.branch_key,
            "ten_god": signal.stem_ten_god,
            "weight": POSITION_STEM_WEIGHTS[position],
        }
        branch_entry = {
            "position": f"{position}:branch_main",
            "source": "hidden",
            "stem": main_stem,
            "branch": pillar.branch_key,
            "ten_god": signal.branch_main_ten_god,
            "weight": POSITION_BRANCH_WEIGHTS[position],
        }
        hidden_stems = {stem_key for stem_key, _ in BRANCH_HIDDEN_STEMS[pillar.branch_key]}
        if pillar.stem_key in hidden_stems:
            relation_type = "visible_stem_root"
        else:
            relation_type = _relation_from_elements(
                [visible_entry["stem"], branch_entry["stem"]],
                [visible_entry["ten_god"], branch_entry["ten_god"]],
            )
        if relation_type == "neutral":
            continue
        signals.append(
            _signal(
                layer="stem_branch",
                relation_type=relation_type,
                entries=[visible_entry, branch_entry],
                signal_suffix=position,
                strength="high" if relation_type == "visible_stem_root" else "moderate",
            )
        )
    return signals


def _ten_god_chain_signals(
    visible_entries: list[dict[str, Any]],
    hidden_entries: list[dict[str, Any]],
) -> list[CombinationSignal]:
    candidate_entries = visible_entries + hidden_entries
    signals: list[CombinationSignal] = []
    relation_seen: set[tuple[str, str]] = set()
    chain_index = 0

    for size in (2, 3):
        for entries in combinations(candidate_entries, size):
            entry_list = list(entries)
            if len({entry["position"] for entry in entry_list}) != len(entry_list):
                continue
            relation_type = _relation_from_elements(
                [entry["stem"] for entry in entry_list],
                [entry["ten_god"] for entry in entry_list],
            )
            if relation_type == "neutral":
                continue
            if relation_type in {"element_generation", "element_control", "same_element_density"}:
                continue
            key = (relation_type, _combination_key([entry["stem"] for entry in entry_list]))
            if key in relation_seen:
                continue
            relation_seen.add(key)
            chain_index += 1
            signals.append(
                _signal(
                    layer="ten_god_chain",
                    relation_type=relation_type,
                    entries=entry_list,
                    signal_suffix=f"{size}_{chain_index}",
                )
            )

    return _dedupe_signals(signals, limit=24)


def _signal_rank(signal: CombinationSignal) -> tuple[int, int, int]:
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    counter_rank = 1 if signal.counter_signals else 0
    domain_rank = -len(signal.domain_links)
    return (strength_rank, counter_rank, domain_rank)


def _dedupe_signals(signals: list[CombinationSignal], limit: int | None = None) -> list[CombinationSignal]:
    deduped: list[CombinationSignal] = []
    seen: set[tuple[str, str, tuple[str, ...], str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        key = (signal.layer, signal.relation_type, tuple(signal.positions), signal.combination_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def iter_combination_signals(profile: CombinationProfile) -> list[CombinationSignal]:
    return (
        list(profile.heavenly_stem_signals)
        + list(profile.hidden_stem_signals)
        + list(profile.stem_branch_signals)
        + list(profile.ten_god_chain_signals)
    )


def signals_for_domain(profile: CombinationProfile, domain: str, limit: int = 8) -> list[CombinationSignal]:
    signals = [
        signal
        for signal in iter_combination_signals(profile)
        if domain in signal.domain_links
    ]
    return sorted(signals, key=_signal_rank)[:limit]


def _domain_notes(signals: list[CombinationSignal]) -> dict[str, list[str]]:
    notes: dict[str, list[str]] = {domain: [] for domain in SERVICE_DOMAINS}
    for signal in sorted(signals, key=_signal_rank):
        for domain in signal.domain_links:
            if len(notes[domain]) < 5 and signal.interpretation not in notes[domain]:
                notes[domain].append(signal.interpretation)
    return notes


def _summary_sentences(signals: list[CombinationSignal]) -> list[str]:
    selected = sorted(signals, key=_signal_rank)[:4]
    sentences: list[str] = []
    for signal in selected:
        domains = ", ".join(signal.domain_links) if signal.domain_links else "기본 성향"
        sentences.append(f"당신의 타고난 사주에서는 {signal.interpretation} 이 판단은 {domains} 해석에 직접 반영됩니다.")
    return sentences


def build_combination_profile(
    chart: BirthChartResult,
    position_signals: dict[str, PositionSignal],
) -> CombinationProfile:
    visible_entries = _visible_entries(chart, position_signals)
    hidden_entries = _hidden_entries(chart)
    heavenly_stem_signals = _visible_stem_signals(visible_entries)
    hidden_stem_signals = _hidden_stem_signals(visible_entries, hidden_entries)
    stem_branch_signals = _stem_branch_signals(chart, position_signals)
    ten_god_chain_signals = _ten_god_chain_signals(visible_entries, hidden_entries)
    all_signals = _dedupe_signals(
        heavenly_stem_signals + hidden_stem_signals + stem_branch_signals + ten_god_chain_signals
    )
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_signal_rank)[:10]]
    return CombinationProfile(
        heavenly_stem_signals=heavenly_stem_signals,
        hidden_stem_signals=hidden_stem_signals,
        stem_branch_signals=stem_branch_signals,
        ten_god_chain_signals=ten_god_chain_signals,
        top_signal_ids=top_signal_ids,
        domain_notes=_domain_notes(all_signals),
        summary_sentences=_summary_sentences(all_signals),
    )
