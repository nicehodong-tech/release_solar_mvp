"""Evaluate the registered myeongri theory layers for one public metric.

The public metric base score already contains broad life-feature capacities.
This module supplies the missing expert adjudication layer: month authority,
seasonal capacity, climate, pattern viability, classical ten-god actions and
the reality of element/stem/branch chains.  Every distinct source signal is
retained in the audit ledger. Correlated signals are combined with diminishing
weights instead of being discarded, so repeated descriptions of one pair do
not become four full bonuses while their different theoretical meanings remain
available to the final judgment.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import math
import re
from threading import RLock
from typing import Any, Iterable

from .constants import ELEMENT_CONTROLS, ELEMENT_GENERATES, STEM_METADATA, TEN_GOD_GROUPS
from .metric_theory_registry import (
    METRIC_THEORY_LAYERS,
    METRIC_THEORY_REGISTRY_VERSION,
    METRIC_THEORY_REQUIREMENTS,
)
from .models import ChartStructure
from .relation_polarity import branch_relation_polarity


@dataclass(frozen=True)
class TheoryEvidence:
    layer_key: str
    family_id: str
    quality: float
    materiality: float
    source_key: str
    basis_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PreparedSignalFacts:
    """Chart-static facts reused by every public metric.

    The meaning assigned to a signal remains metric-specific.  Only expensive
    extraction and normalization that cannot change between metrics is cached.
    """

    groups: tuple[str, ...]
    ten_gods: tuple[str, ...]
    positions: tuple[str, ...]
    position_scopes: frozenset[str]
    source_group: str
    target_group: str
    direction_type: str
    chain_haystack: str
    domain_links: frozenset[str]
    counter_count: int
    branch_modifier: float
    strength: float
    priority_factor: float
    visibility: float
    source_key: str
    basis_codes: tuple[str, ...]


_PREPARED_SIGNAL_CACHE_LIMIT = 24
_PREPARED_SIGNAL_CACHE: OrderedDict[
    int,
    tuple[ChartStructure, dict[int, _PreparedSignalFacts]],
] = OrderedDict()
_PREPARED_SIGNAL_CACHE_LOCK = RLock()
_CONTRACT_VALUE_CACHE_LIMIT = 512
_CONTRACT_VALUE_CACHE: OrderedDict[
    int,
    tuple[Any, dict[str, float], dict[str, float]],
] = OrderedDict()
_CONTRACT_VALUE_CACHE_LOCK = RLock()


_DOMAIN_ALIASES: dict[str, frozenset[str]] = {
    "money": frozenset({"money"}),
    "career": frozenset({"career", "work"}),
    "personality": frozenset({"personality"}),
    "love": frozenset({"love", "relationship"}),
    "marriage": frozenset({"marriage", "relationship"}),
    "honor": frozenset({"reputation", "honor", "career"}),
    "social": frozenset({"relationship", "social", "network"}),
}

_STRENGTH_WEIGHTS = {
    "very_high": 1.0,
    "high": 0.92,
    "strong": 0.92,
    "moderate": 0.72,
    "medium": 0.72,
    "mild": 0.52,
    "low": 0.38,
    "weak": 0.34,
}

_FORMATION_QUALITY = {
    "properly_formed": 0.82,
    "partially_formed": 0.34,
    "latent_but_usable": 0.08,
    "weak_or_fragmented": -0.42,
    "broken": -0.82,
}

_CLARITY_QUALITY = {
    "clear_and_rooted": 0.72,
    "rooted_but_hidden": 0.18,
    "clouded_by_month_pressure": -0.38,
    "mixed": -0.08,
    "unclear": -0.34,
}

_SINGLE_VERDICT_QUALITY = {
    "constructive_action": 0.72,
    "feeds_pattern_source": 0.52,
    "center_reinforced": 0.24,
    "conditional_action": 0.0,
    "destructive_action": -0.78,
    "risk_activated": -0.88,
    "overload_action": -0.68,
}

_SINGLE_CONTEXT_QUALITY = {
    "constructive_by_context": 0.20,
    "medicine_or_regulator": 0.12,
    "conditional_by_context": 0.0,
    "context_strengthens_action": 0.06,
    "context_weakens_action": -0.18,
    "risk_by_context": -0.24,
}

_DUAL_VERDICT_QUALITY = {
    "constructive_dual_action": 0.72,
    "conditional_dual_action": 0.0,
    "risk_dual_action": -0.86,
    "not_activated": 0.0,
    "observed_dual_action": -0.02,
}

_DUAL_CONTEXT_QUALITY = {
    "structure_supports_expression": 0.18,
    "medicine_can_work": 0.20,
    "conditional_by_context": 0.0,
    "context_strengthens_pair": 0.04,
    "context_weakens_pair": -0.18,
    "month_pressure_confirms_risk": -0.26,
    "risk_is_reinforced": -0.20,
}

# The registry keeps these as separate interpretive layers.  For score
# accounting they are one source family whenever they describe the same stem
# or hidden-stem pair.
_PAIR_DERIVED_FAMILIES = frozenset(
    {"stem_pair", "directional_pair", "ten_god_chain", "integrated_pair"}
)

_LEGACY_SCORING_FAMILIES = frozenset(
    {
        "month_authority",
        "element_state",
        "ten_god_presence",
        "position",
        "kinship",
        "branch_pair",
        "spouse_evidence",
    }
)

_NON_SCORING_ROLES = frozenset(
    {
        "support_only",
        "dynamic_only",
        "selection_only",
        "calibration_only",
        "weighting",
    }
)

# The registry names the theory layer.  The hierarchy below states how that
# layer participates in a judgment.  Governance decides whether an action is
# useful in this chart; reality decides whether it can manifest; interaction
# describes what the elements and ten gods actually do to one another.
_GOVERNANCE_FAMILIES = frozenset(
    {
        "month_authority",
        "day_master_capacity",
        "climate_balance",
        "pattern_state",
        "useful_role",
        "pattern_exception",
    }
)
_REALITY_FAMILIES = frozenset(
    {
        "element_state",
        "visibility_reality",
        "ten_god_presence",
        "position",
        "kinship",
        "spouse_evidence",
        "yin_yang",
    }
)
_INTERACTION_FAMILIES = frozenset(
    {
        "disease_medicine",
        "element_chain",
        "stem_pair",
        "directional_pair",
        "ten_god_chain",
        "branch_pair",
        "pattern_action",
        "integrated_pair",
    }
)

_CORRELATION_CLUSTERS = {
    "month_authority": "month_governance",
    "climate_balance": "climate_governance",
    "element_state": "element_material",
    "visibility_reality": "visibility_material",
    "ten_god_presence": "ten_god_material",
    "position": "position_material",
    "kinship": "position_material",
    "stem_pair": "pair_synthesis",
    "directional_pair": "pair_synthesis",
    "ten_god_chain": "pair_synthesis",
    "integrated_pair": "pair_synthesis",
    "branch_pair": "branch_synthesis",
    "pattern_state": "pattern_governance",
    "pattern_action": "pattern_action",
}

_DOMAIN_LIMITED_CONTEXT_LAYERS: dict[str, frozenset[str]] = {
    "spouse_star_gender": frozenset({"love", "marriage"}),
    "kinship_projection": frozenset({"love", "marriage", "social"}),
    "yin_yang_balance": frozenset({"personality", "love", "social"}),
}

_ABSENCE_SENSITIVE_PRIMARY_LAYERS = frozenset(
    {
        "exact_ten_gods",
        "ten_god_interactions",
        "element_circulation",
        "visible_stems",
        "protrusion_rooting",
        "position_palaces",
        "pattern_single_actions",
        "pattern_dual_actions",
        "spouse_star_gender",
    }
)

# These layers describe the climate in which every metric has to operate.
# They must never become ten identical positive or negative votes merely
# because every metric contract references them.  Their evidence is retained
# and used as a carrying/fitness gate; the metric-specific ten-god, chain,
# palace and relation layers remain responsible for the actual verdict.
_UNIVERSAL_GATE_LAYERS = frozenset(
    {
        "month_environment",
        "month_hidden_phase",
        "seasonal_element_strength",
        "day_master_capacity",
        "element_distribution",
        "element_quality",
        "ten_god_groups",
        "special_pattern_exceptions",
    }
)

_DECISIVE_LAYER_ROLES = frozenset({"primary", "pressure"})
_CORROBORATING_LAYER_ROLES = frozenset({"confirming"})

_CHAIN_ALIASES: dict[str, tuple[str, ...]] = {
    "식상생재": ("식상생재", "식신생재", "상관생재", "siksang_saengjae"),
    "재생관": ("재생관", "정재생정관", "편재생정관", "jaesaenggwan", "jaeseong_generates_gwanseong"),
    "관인상생": ("관인상생", "정관생정인", "정관생편인", "gwanin_sangsaeng"),
    "살인상생": ("살인상생", "편관생정인", "편관생편인", "salin_sangsaeng"),
    "식신제살": ("식신제살", "상관제살", "siksin_jesal", "siksang_controls_gwanseong"),
    "상관견관": ("상관견관", "sanggwan_gyeongwan"),
    "재극인": ("재극인", "정재극인", "편재극인", "jaegeukin", "wealth_controls_resource"),
    "편인도식": ("편인도식", "inseong_dosik", "inseong_controls_output"),
    "인다식상": ("인다식상", "인성 과다", "인비 과중", "inbi_overload", "inseong_controls_output"),
    "비겁쟁재": ("비겁쟁재", "쟁재", "겁재극재", "비견극재", "bigeop_jaengjae", "bigeop_controls_wealth"),
    "비겁분재": ("비겁분재", "쟁재", "분점", "bigeop_jaengjae", "bigeop_controls_wealth"),
    "관성제비겁": ("관성제비겁", "정관극겁재", "정관극비견", "편관극겁재", "편관극비견", "gwanseong_controls_bigeop"),
    "관살혼잡": ("관살혼잡", "정관·편관 병립", "편관·정관 병립", "gwansal_honhap"),
}


def _clip(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _mean(values: Iterable[float], default: float = 0.0) -> float:
    items = list(values)
    return sum(items) / len(items) if items else default


def _strength_weight(value: Any) -> float:
    return _STRENGTH_WEIGHTS.get(str(value or "").lower(), 0.58)


def _ten_god_group(ten_god: str) -> str:
    if ten_god == "self":
        return "peer"
    return TEN_GOD_GROUPS.get(ten_god, "")


@lru_cache(maxsize=256)
def _role_element_map_cached(pairs: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return dict(pairs)


def _role_element_map(structure: ChartStructure) -> dict[str, str]:
    pairs = tuple(
        (str(group), str(fit.element))
        for group, fit in structure.month_governance_profile.role_fits.items()
        if str(getattr(fit, "element", ""))
    )
    return _role_element_map_cached(pairs)


def _element_group_map(structure: ChartStructure) -> dict[str, str]:
    return {element: group for group, element in _role_element_map(structure).items()}


def _ordered_role_values(items: Iterable[str], sign: float) -> dict[str, float]:
    """Preserve the contract's declared role priority instead of vote counting."""

    values: dict[str, float] = {}
    for index, item in enumerate(dict.fromkeys(str(value) for value in items if value)):
        weight = 1.0 / math.sqrt(index + 1.0)
        values[item] = values.get(item, 0.0) + sign * weight
    return values


@lru_cache(maxsize=512)
def _contract_group_values_cached(
    support_groups: tuple[str, ...],
    pressure_groups: tuple[str, ...],
) -> dict[str, float]:
    values = _ordered_role_values(support_groups, 1.0)
    for group, value in _ordered_role_values(
        pressure_groups,
        -1.0,
    ).items():
        values[group] = values.get(group, 0.0) + value
    return values


def _contract_group_values(contract: Any) -> dict[str, float]:
    return _contract_values(contract)[0]


@lru_cache(maxsize=512)
def _contract_ten_god_values_cached(
    support_ten_gods: tuple[str, ...],
    pressure_ten_gods: tuple[str, ...],
) -> dict[str, float]:
    values = _ordered_role_values(support_ten_gods, 1.0)
    for ten_god, value in _ordered_role_values(
        pressure_ten_gods,
        -1.0,
    ).items():
        values[ten_god] = values.get(ten_god, 0.0) + value
    return values


def _contract_ten_god_values(contract: Any) -> dict[str, float]:
    return _contract_values(contract)[1]


def _contract_values(contract: Any) -> tuple[dict[str, float], dict[str, float]]:
    """Reuse immutable registry-contract role maps across every evidence row."""

    contract_id = id(contract)
    with _CONTRACT_VALUE_CACHE_LOCK:
        cached = _CONTRACT_VALUE_CACHE.get(contract_id)
        if cached is not None and cached[0] is contract:
            _CONTRACT_VALUE_CACHE.move_to_end(contract_id)
            return cached[1], cached[2]
    group_values = _contract_group_values_cached(
        tuple(str(item) for item in (getattr(contract, "support_groups", ()) or ()) if item),
        tuple(str(item) for item in (getattr(contract, "pressure_groups", ()) or ()) if item),
    )
    ten_god_values = _contract_ten_god_values_cached(
        tuple(str(item) for item in (getattr(contract, "support_ten_gods", ()) or ()) if item),
        tuple(str(item) for item in (getattr(contract, "pressure_ten_gods", ()) or ()) if item),
    )
    with _CONTRACT_VALUE_CACHE_LOCK:
        _CONTRACT_VALUE_CACHE[contract_id] = (contract, group_values, ten_god_values)
        _CONTRACT_VALUE_CACHE.move_to_end(contract_id)
        while len(_CONTRACT_VALUE_CACHE) > _CONTRACT_VALUE_CACHE_LIMIT:
            _CONTRACT_VALUE_CACHE.popitem(last=False)
    return group_values, ten_god_values


def _role_alignment_from_values(
    groups: Iterable[str],
    role_values: dict[str, float],
) -> tuple[float, int]:
    normalized = list(dict.fromkeys(group for group in groups if group))
    if not normalized:
        return 0.0, 0
    matched_values = [role_values[group] for group in normalized if group in role_values]
    if not matched_values:
        return 0.0, 0
    denominator = sum(abs(value) for value in matched_values) or 1.0
    return _clip(sum(matched_values) / denominator), len(matched_values)


def _role_alignment(groups: Iterable[str], contract: Any) -> tuple[float, int]:
    return _role_alignment_from_values(groups, _contract_group_values(contract))


def _signal_groups(signal: Any, structure: ChartStructure) -> list[str]:
    groups: list[str] = []
    for field in ("source_group", "target_group", "acting_group", "first_group", "second_group"):
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if value:
            groups.append(str(value))
    ten_gods: list[str] = []
    for field in ("ten_gods",):
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, [])
        ten_gods.extend(str(item) for item in (value or []))
    for field in ("source_ten_god", "target_ten_god", "acting_ten_god", "first_ten_god", "second_ten_god", "target_ten_god"):
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if value:
            ten_gods.append(str(value))
    groups.extend(_ten_god_group(item) for item in ten_gods)
    if not groups:
        element_to_group = _element_group_map(structure)
        elements: list[str] = []
        value = signal.get("elements") if isinstance(signal, dict) else getattr(signal, "elements", [])
        elements.extend(str(item) for item in (value or []))
        for field in ("source_element", "target_element", "bridge_element"):
            item = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
            if item:
                elements.append(str(item))
        groups.extend(element_to_group.get(item, "") for item in elements)
    return list(dict.fromkeys(group for group in groups if group))


def _signal_ten_gods(signal: Any) -> list[str]:
    ten_gods: list[str] = []
    value = signal.get("ten_gods") if isinstance(signal, dict) else getattr(signal, "ten_gods", [])
    ten_gods.extend(str(item) for item in (value or []))
    for field in (
        "source_ten_god",
        "target_ten_god",
        "acting_ten_god",
        "first_ten_god",
        "second_ten_god",
    ):
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if value:
            ten_gods.append(str(value))
    return list(dict.fromkeys(item for item in ten_gods if item))


def _signal_role_alignment(
    signal: Any,
    structure: ChartStructure,
    contract: Any,
) -> tuple[float, int]:
    """Judge both functional group and exact ten-god identity."""

    group_quality, group_hits = _role_alignment(_signal_groups(signal, structure), contract)
    ten_gods = _signal_ten_gods(signal)
    exact_values = _contract_ten_god_values(contract)
    matched_values = [exact_values[item] for item in ten_gods if item in exact_values]
    if not matched_values:
        return group_quality, group_hits
    denominator = sum(abs(value) for value in matched_values) or 1.0
    exact_quality = _clip(sum(matched_values) / denominator)
    exact_hits = len(matched_values)
    if group_hits:
        return _clip(exact_quality * 0.64 + group_quality * 0.36), exact_hits + group_hits
    return exact_quality, exact_hits


def _contract_role_value(group: str, contract: Any) -> float:
    return _clip(_contract_group_values(contract).get(group, 0.0))


def _signal_endpoint_groups(
    signal: Any,
    structure: ChartStructure,
) -> tuple[str, str, str]:
    get = (
        (lambda key, default="": signal.get(key, default))
        if isinstance(signal, dict)
        else (lambda key, default="": getattr(signal, key, default))
    )
    source_group = str(get("source_group") or "")
    target_group = str(get("target_group") or "")
    source_ten_god = str(get("source_ten_god") or "")
    target_ten_god = str(get("target_ten_god") or "")
    if not source_group and source_ten_god:
        source_group = _ten_god_group(source_ten_god)
    if not target_group and target_ten_god:
        target_group = _ten_god_group(target_ten_god)
    element_groups = _element_group_map(structure)
    source_element = str(get("source_element") or "")
    target_element = str(get("target_element") or "")
    if not source_group and source_element:
        source_group = element_groups.get(source_element, "")
    if not target_group and target_element:
        target_group = element_groups.get(target_element, "")

    direction_type = str(get("direction_type") or "")
    if not direction_type and source_element and target_element:
        if source_element == target_element:
            direction_type = "same_element"
        elif ELEMENT_GENERATES.get(source_element) == target_element:
            direction_type = "source_generates_target"
        elif ELEMENT_GENERATES.get(target_element) == source_element:
            direction_type = "target_generates_source"
        elif ELEMENT_CONTROLS.get(source_element) == target_element:
            direction_type = "source_controls_target"
        elif ELEMENT_CONTROLS.get(target_element) == source_element:
            direction_type = "target_controls_source"
    return source_group, target_group, direction_type


def _directed_role_alignment(
    signal: Any,
    structure: ChartStructure,
    contract: Any,
) -> tuple[float, int]:
    """Preserve who acts on whom in generation and control relations."""

    source_group, target_group, direction = _signal_endpoint_groups(signal, structure)
    if not source_group or not target_group or not direction:
        return 0.0, 0
    source_value = _contract_role_value(source_group, contract)
    target_value = _contract_role_value(target_group, contract)
    hits = int(source_value != 0.0) + int(target_value != 0.0)
    if not hits:
        return 0.0, 0

    if direction == "target_generates_source":
        source_value, target_value = target_value, source_value
        direction = "source_generates_target"
    elif direction == "target_controls_source":
        source_value, target_value = target_value, source_value
        direction = "source_controls_target"

    if direction == "source_generates_target":
        quality = source_value * 0.34 + target_value * 0.66
    elif direction == "source_controls_target":
        # A useful role controlling a burden is constructive; a burden
        # controlling a useful role is destructive. Controlling another
        # useful role carries a small cost rather than a false benefit.
        quality = source_value * 0.35 - target_value * 0.65
    else:
        quality = (source_value + target_value) / 2.0
    return _clip(quality), hits


def _signal_positions(signal: Any) -> list[str]:
    positions: list[str] = []
    value = signal.get("positions") if isinstance(signal, dict) else getattr(signal, "positions", [])
    positions.extend(str(item) for item in (value or []))
    for field in ("source_position", "target_position", "position"):
        item = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if item:
            positions.append(str(item))
    return list(dict.fromkeys(positions))


@lru_cache(maxsize=4096)
def _position_scopes_cached(positions: tuple[str, ...]) -> frozenset[str]:
    scopes: set[str] = set()
    for position in positions:
        value = str(position or "").lower()
        if not value:
            continue
        scopes.add(value)
        for pillar in ("year", "month", "day", "hour"):
            if value == pillar or value.startswith(f"{pillar}:") or value.startswith(f"{pillar}_") or value.startswith(f"{pillar}."):
                scopes.add(pillar)
    return frozenset(scopes)


def _position_scopes(positions: Iterable[str]) -> frozenset[str]:
    normalized = tuple(sorted(dict.fromkeys(str(position) for position in positions if position)))
    return _position_scopes_cached(normalized)


def _position_materiality(positions: Iterable[str], required_positions: Iterable[str]) -> float:
    actual = _position_scopes(positions)
    required = _position_scopes(required_positions)
    if not required:
        return 0.78
    if not actual:
        return 0.58
    overlap = len(actual.intersection(required))
    if overlap:
        return min(1.0, 0.78 + overlap * 0.11)
    return 0.46


@lru_cache(maxsize=16384)
def _normalize_text_cached(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", value).lower()


def _normalize_text(value: Any) -> str:
    return _normalize_text_cached(str(value or ""))


def _signal_chain_haystack(signal: Any) -> str:
    fields = (
        "action_nature",
        "exact_pair_name",
        "classical_name",
        "sequence_key",
        "action_key",
        "rule_key",
        "classical_action_tags",
        "first_single_classical_action_tags",
        "second_single_classical_action_tags",
    )
    parts: list[str] = []
    for field in fields:
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if isinstance(value, (list, tuple, set)):
            parts.extend(str(item) for item in value)
        elif value:
            parts.append(str(value))
    return _normalize_text(" ".join(parts))


def _chain_match_from_haystack(chains: Iterable[str], haystack: str) -> float:
    return _chain_match_from_haystack_cached(
        tuple(str(chain) for chain in chains),
        haystack,
    )


@lru_cache(maxsize=32768)
def _chain_match_from_haystack_cached(chains: tuple[str, ...], haystack: str) -> float:
    if not haystack:
        return 0.0
    best = 0.0
    for chain in chains:
        normalized_chain = _normalize_text(chain)
        if normalized_chain and normalized_chain in haystack:
            best = max(best, 1.0)
        for canonical, aliases in _CHAIN_ALIASES.items():
            if _normalize_text(canonical) not in normalized_chain:
                continue
            if any(_normalize_text(alias) in haystack for alias in aliases):
                best = max(best, 0.92)
    return best


def _chain_match_score(chains: Iterable[str], signal: Any) -> float:
    return _chain_match_from_haystack(chains, _signal_chain_haystack(signal))


def _basis_codes(signal: Any) -> tuple[str, ...]:
    value = signal.get("basis_codes") if isinstance(signal, dict) else getattr(signal, "basis_codes", [])
    return tuple(str(item) for item in (value or []) if str(item))[:8]


def _signal_source_key(signal: Any) -> str:
    for field in ("signal_id", "rule_key", "pair_id", "combination_key", "direction_key"):
        value = signal.get(field) if isinstance(signal, dict) else getattr(signal, field, "")
        if value:
            return str(value)
    positions = _signal_positions(signal)
    return ":".join(positions) or "observed"


def _prepared_signal_bucket(structure: ChartStructure) -> dict[int, _PreparedSignalFacts]:
    structure_id = id(structure)
    with _PREPARED_SIGNAL_CACHE_LOCK:
        cached = _PREPARED_SIGNAL_CACHE.get(structure_id)
        if cached is not None and cached[0] is structure:
            _PREPARED_SIGNAL_CACHE.move_to_end(structure_id)
            return cached[1]
        bucket: dict[int, _PreparedSignalFacts] = {}
        _PREPARED_SIGNAL_CACHE[structure_id] = (structure, bucket)
        _PREPARED_SIGNAL_CACHE.move_to_end(structure_id)
        while len(_PREPARED_SIGNAL_CACHE) > _PREPARED_SIGNAL_CACHE_LIMIT:
            _PREPARED_SIGNAL_CACHE.popitem(last=False)
        return bucket


def _prepared_signal_facts(signal: Any, structure: ChartStructure) -> _PreparedSignalFacts:
    bucket = _prepared_signal_bucket(structure)
    signal_id = id(signal)
    with _PREPARED_SIGNAL_CACHE_LOCK:
        cached = bucket.get(signal_id)
    if cached is not None:
        return cached

    source_group, target_group, direction_type = _signal_endpoint_groups(signal, structure)
    layer_name = str(
        signal.get("layer", "") if isinstance(signal, dict) else getattr(signal, "layer", "")
    )
    priority_score = float(
        (
            signal.get("priority_score", 0.0)
            if isinstance(signal, dict)
            else getattr(signal, "priority_score", 0.0)
        )
        or 0.0
    )
    domain_value = (
        signal.get("domain_links", [])
        if isinstance(signal, dict)
        else getattr(signal, "domain_links", [])
    )
    counter_value = (
        signal.get("counter_signals", [])
        if isinstance(signal, dict)
        else getattr(signal, "counter_signals", [])
    )
    branch_modifier = float(
        (
            signal.get("branch_relation_score_modifier", 0.0)
            if isinstance(signal, dict)
            else getattr(signal, "branch_relation_score_modifier", 0.0)
        )
        or 0.0
    )
    strength_value = (
        signal.get("strength", "")
        if isinstance(signal, dict)
        else getattr(signal, "strength", "")
    )
    positions = tuple(_signal_positions(signal))
    facts = _PreparedSignalFacts(
        groups=tuple(_signal_groups(signal, structure)),
        ten_gods=tuple(_signal_ten_gods(signal)),
        positions=positions,
        position_scopes=_position_scopes(positions),
        source_group=source_group,
        target_group=target_group,
        direction_type=direction_type,
        chain_haystack=_signal_chain_haystack(signal),
        domain_links=frozenset(str(item) for item in (domain_value or [])),
        counter_count=len(list(counter_value or [])),
        branch_modifier=branch_modifier,
        strength=_strength_weight(strength_value),
        priority_factor=(
            min(1.0, max(0.45, priority_score / 70.0))
            if priority_score
            else 0.72
        ),
        visibility=0.68 if "hidden" in layer_name else 0.82 if "branch" in layer_name else 1.0,
        source_key=_signal_source_key(signal),
        basis_codes=_basis_codes(signal),
    )
    with _PREPARED_SIGNAL_CACHE_LOCK:
        bucket[signal_id] = facts
    return facts


def _profile_signals(profile: Any, fields: Iterable[str]) -> list[Any]:
    signals: list[Any] = []
    for field in fields:
        signals.extend(list(getattr(profile, field, []) or []))
    return signals


def _profile_signal_evidence(
    *,
    layer_key: str,
    signals: Iterable[Any],
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
    layer_role: str,
    signal_audit: dict[str, dict[str, int]] | None = None,
) -> list[TheoryEvidence]:
    candidates: list[TheoryEvidence] = []
    aliases = _DOMAIN_ALIASES.get(requirement.domain, frozenset({requirement.domain}))
    required_positions = set(requirement.required_positions)
    required_position_scopes = _position_scopes(required_positions)
    group_values, exact_values = _contract_values(contract)
    audit = (
        signal_audit.setdefault(
            layer_key,
            {
                "observed": 0,
                "applied": 0,
                "rejected_no_metric_link": 0,
            },
        )
        if signal_audit is not None
        else None
    )
    for signal in signals:
        if audit is not None:
            audit["observed"] += 1
        facts = _prepared_signal_facts(signal, structure)
        role_quality, role_hits = _role_alignment_from_values(facts.groups, group_values)
        exact_matches = [exact_values[item] for item in facts.ten_gods if item in exact_values]
        if exact_matches:
            exact_denominator = sum(abs(value) for value in exact_matches) or 1.0
            exact_quality = _clip(sum(exact_matches) / exact_denominator)
            if role_hits:
                role_quality = _clip(exact_quality * 0.64 + role_quality * 0.36)
            else:
                role_quality = exact_quality
            role_hits += len(exact_matches)

        source_value = _clip(group_values.get(facts.source_group, 0.0))
        target_value = _clip(group_values.get(facts.target_group, 0.0))
        directed_hits = int(source_value != 0.0) + int(target_value != 0.0)
        directed_quality = 0.0
        direction = facts.direction_type
        if directed_hits and direction:
            if direction == "target_generates_source":
                source_value, target_value = target_value, source_value
                direction = "source_generates_target"
            elif direction == "target_controls_source":
                source_value, target_value = target_value, source_value
                direction = "source_controls_target"
            if direction == "source_generates_target":
                directed_quality = _clip(source_value * 0.34 + target_value * 0.66)
            elif direction == "source_controls_target":
                directed_quality = _clip(source_value * 0.35 - target_value * 0.65)
            else:
                directed_quality = _clip((source_value + target_value) / 2.0)
        if directed_hits:
            role_quality = _clip(directed_quality * 0.58 + role_quality * 0.42)
            role_hits += directed_hits
        chain_match = _chain_match_from_haystack(
            requirement.classical_chains,
            facts.chain_haystack,
        )
        positions = facts.positions
        if not required_position_scopes:
            position_fit = 0.78
        elif not facts.position_scopes:
            position_fit = 0.58
        else:
            overlap = len(facts.position_scopes.intersection(required_position_scopes))
            position_fit = min(1.0, 0.78 + overlap * 0.11) if overlap else 0.46
        domain_hit = bool(aliases.intersection(facts.domain_links))
        position_hit = bool(
            required_position_scopes.intersection(facts.position_scopes)
        ) if required_positions else False
        # A broad group hit alone is not a metric connection.  Most source
        # signals mention several life domains and most contracts contain
        # three support groups; accepting either fact alone admitted hundreds
        # of unrelated pairs into every metric.  A scored signal now needs an
        # exact role/chain match or a directed action located in the metric's
        # real palace.  Context evidence has the strictest admission rule.
        exact_hit = bool(exact_matches)
        directed_position_hit = bool(directed_hits and position_hit)
        broad_reality_hit = bool(role_hits and position_hit and domain_hit)
        exact_reality_hit = bool(exact_hit and (position_hit or domain_hit))
        if layer_role == "context":
            substantive_link = bool(
                chain_match > 0.0
                or (exact_hit and position_hit and domain_hit)
                or (directed_hits >= 2 and position_hit and domain_hit)
            )
        elif layer_role == "gate":
            substantive_link = bool(
                chain_match > 0.0
                or exact_reality_hit
                or directed_position_hit
                or broad_reality_hit
            )
        else:
            substantive_link = bool(
                chain_match > 0.0
                or exact_reality_hit
                or directed_position_hit
                or broad_reality_hit
            )
        if not substantive_link:
            if audit is not None:
                audit["rejected_no_metric_link"] += 1
            continue
        if audit is not None:
            audit["applied"] += 1
        domain_fit = 1.0 if domain_hit else 0.56

        counter_count = facts.counter_count
        branch_modifier = facts.branch_modifier
        quality = role_quality * 0.72
        if chain_match:
            quality += (0.22 if role_quality >= 0.0 else -0.12) * chain_match
        quality += max(-0.18, min(0.18, branch_modifier / 50.0))
        quality -= min(0.24, counter_count * 0.045)
        if role_hits == 0 and chain_match:
            quality += 0.08

        applicability = (
            1.0
            if role_hits
            else 0.90
            if chain_match
            else 0.74
            if domain_hit
            else 0.46
        )
        materiality = min(
            1.0,
            facts.strength * 0.46
            + facts.priority_factor * 0.18
            + position_fit * 0.20
            + domain_fit * 0.10
            + chain_match * 0.12,
        ) * facts.visibility * applicability
        candidates.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id=METRIC_THEORY_LAYERS[layer_key].anti_double_count_group,
                quality=_clip(quality),
                materiality=max(0.18, min(1.0, materiality)),
                source_key=facts.source_key,
                basis_codes=facts.basis_codes,
            )
        )
    return sorted(
        candidates,
        key=lambda item: item.materiality * (0.35 + abs(item.quality)),
        reverse=True,
    )


def _role_fit_evidence(layer_key: str, structure: ChartStructure, contract: Any, score: float) -> list[TheoryEvidence]:
    return [
        TheoryEvidence(
            layer_key=layer_key,
            family_id=METRIC_THEORY_LAYERS[layer_key].anti_double_count_group,
            quality=_clip((score - 50.0) / 38.0),
            materiality=0.92,
            source_key="metric_role_fit",
        )
    ]


def _month_role_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
) -> list[TheoryEvidence]:
    """Keep every contract role inside the month-command judgment.

    The former implementation reduced all support and pressure roles to one
    already-averaged legacy score.  That concealed whether, for example,
    wealth was usable while output was weak, or whether officer pressure was
    present but regulated.  Each role is now retained and later reconciled at
    family level.
    """

    evidence: list[TheoryEvidence] = []
    ordered_roles = list(dict.fromkeys((*contract.support_groups, *contract.pressure_groups)))
    support_roles = set(contract.support_groups)
    pressure_roles = set(contract.pressure_groups)
    for index, group in enumerate(ordered_roles):
        fit = structure.month_governance_profile.role_fits.get(group)
        if fit is None:
            continue
        support_score = float(getattr(fit, "support_score", 0.0) or 0.0)
        pressure_score = float(getattr(fit, "pressure_score", 0.0) or 0.0)
        amount = float(structure.ten_god_profile.group_scores.get(group, 0.0) or 0.0)
        presence = min(1.0, amount / 1.45)
        net_fit = _clip((support_score - pressure_score) / 6.0)
        if group in support_roles:
            quality = net_fit * 0.68 + (presence - 0.30) * 0.52
        elif group in pressure_roles:
            active_burden = presence * max(0.30, 0.72 + max(0.0, -net_fit) * 0.28)
            regulation = max(0.0, net_fit) * presence * 0.34
            quality = regulation - active_burden
        else:
            quality = net_fit * 0.42
        priority = 1.0 / (1.0 + index * 0.20)
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="month_authority",
                quality=_clip(quality),
                materiality=max(0.42, min(1.0, 0.56 + presence * 0.28 + priority * 0.12)),
                source_key=f"month_role:{group}:{getattr(fit, 'status', '')}",
                basis_codes=tuple(str(item) for item in (getattr(fit, "basis_codes", []) or [])[:8]),
            )
        )
    return evidence


def _month_hidden_evidence(layer_key: str, structure: ChartStructure, contract: Any) -> list[TheoryEvidence]:
    phase = structure.month_governance_profile.month_hidden_phase
    if phase is None:
        return []
    quality, hits = _role_alignment([phase.active_ten_god_group], contract)
    if not hits:
        quality = 0.0
    return [
        TheoryEvidence(
            layer_key=layer_key,
            family_id="month_authority",
            quality=quality * 0.72,
            materiality=0.86,
            source_key=f"{phase.active_phase}:{phase.active_stem}",
            basis_codes=tuple(phase.basis_codes[:8]),
        )
    ]


def _day_master_capacity_evidence(layer_key: str, structure: ChartStructure, contract: Any) -> list[TheoryEvidence]:
    score = float(structure.element_profile.day_master_strength_score)
    load_coefficients = {"wealth": 1.0, "officer": 0.95, "output": 0.68, "peer": -0.62, "resource": -0.72}
    groups = list(getattr(contract, "support_groups", ()) or ())
    weights = [1.0 / (index + 1) for index in range(len(groups))]
    coefficient = (
        sum(load_coefficients.get(group, 0.0) * weight for group, weight in zip(groups, weights, strict=True))
        / max(0.01, sum(weights))
        if groups
        else 0.0
    )
    quality = ((score - 50.0) / 42.0) * coefficient
    return [
        TheoryEvidence(
            layer_key=layer_key,
            family_id="day_master_capacity",
            quality=_clip(quality),
            materiality=0.72,
            source_key=f"day_master:{int(score)}",
        )
    ]


def _element_availability(structure: ChartStructure, element: str) -> float:
    item = structure.element_profile.scores.get(element)
    if item is None:
        return 0.0
    ratio_score = min(1.0, max(0.0, float(item.ratio) / 0.22))
    root_score = min(1.0, float(item.root_count) / 2.0)
    visible_score = min(1.0, float(item.visible_count) / 2.0)
    return ratio_score * 0.48 + root_score * 0.30 + visible_score * 0.22


def _element_state_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    *,
    mode: str,
) -> list[TheoryEvidence]:
    """Evaluate seasonal power, distribution and reality as distinct facts."""

    role_elements = _role_element_map(structure)
    support_roles = set(contract.support_groups)
    pressure_roles = set(contract.pressure_groups)
    ordered_roles = list(dict.fromkeys((*contract.support_groups, *contract.pressure_groups)))
    total_raw = sum(float(item.raw_score) for item in structure.element_profile.scores.values()) or 1.0
    evidence: list[TheoryEvidence] = []
    seen: set[tuple[str, str]] = set()
    for index, group in enumerate(ordered_roles):
        element = role_elements.get(group)
        item = structure.element_profile.scores.get(str(element)) if element else None
        if item is None or (group, str(element)) in seen:
            continue
        seen.add((group, str(element)))
        ratio = max(0.0, float(item.ratio))
        raw_share = max(0.0, float(item.raw_score) / total_raw)
        seasonal_modifier = (
            float(item.seasonal_score) / float(item.raw_score)
            if float(item.raw_score) > 0.001
            else 0.0
        )
        visible = min(1.0, float(item.visible_count) / 2.0)
        rooted = min(1.0, float(item.root_count) / 2.0)
        reality = visible * 0.42 + rooted * 0.46 + (0.12 if item.exposure != "absent" else 0.0)

        if mode == "seasonal":
            seasonal_presence = min(1.15, ratio / 0.24)
            season_fit = _clip((seasonal_modifier - 1.0) / 0.85)
            support_quality = (seasonal_presence - 0.34) * 0.78 + season_fit * 0.28
            pressure_quality = -max(0.0, seasonal_presence - 0.12) * (0.62 + max(0.0, season_fit) * 0.18)
            materiality = 0.48 + min(0.40, ratio * 1.30) + min(0.10, raw_share * 0.35)
        elif mode == "distribution":
            presence = min(1.20, raw_share / 0.22)
            support_quality = (presence - 0.30) * 0.82
            pressure_quality = -max(0.0, presence - 0.10) * 0.76
            materiality = 0.44 + min(0.48, raw_share * 1.55)
        else:
            support_quality = (reality - 0.30) * 1.08
            pressure_quality = -max(0.0, reality - 0.08) * 0.82
            materiality = 0.44 + reality * 0.50

        if group in support_roles:
            quality = support_quality
        elif group in pressure_roles:
            quality = pressure_quality
        else:
            quality = 0.0
        priority = 1.0 / (1.0 + index * 0.18)
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="element_state",
                quality=_clip(quality),
                materiality=max(0.30, min(1.0, materiality * (0.88 + priority * 0.12))),
                source_key=f"{mode}:{group}:{element}:{item.state}:{item.exposure}",
            )
        )
    return evidence


def _climate_need_elements(kind: str, state: str) -> tuple[str, ...]:
    if kind == "temperature":
        return {"cold": ("fire", "wood"), "hot": ("water", "metal")}.get(state, ())
    return {"wet": ("fire", "earth"), "dry": ("water", "wood")}.get(state, ())


def _climate_evidence(layer_key: str, structure: ChartStructure, *, kind: str) -> list[TheoryEvidence]:
    state = (
        structure.element_profile.temperature_balance
        if kind == "temperature"
        else structure.element_profile.moisture_balance
    )
    if state == "balanced":
        return [TheoryEvidence(layer_key, "climate_balance", 0.24, 0.46, f"{kind}:balanced")]
    needs = _climate_need_elements(kind, state)
    if not needs:
        return []
    availability = _mean(_element_availability(structure, element) for element in needs)
    quality = (availability - 0.52) * 1.65
    return [
        TheoryEvidence(
            layer_key,
            "climate_balance",
            _clip(quality),
            0.82,
            f"{kind}:{state}:{','.join(needs)}",
        )
    ]


def _illness_medicine_evidence(layer_key: str, structure: ChartStructure) -> list[TheoryEvidence]:
    candidates: list[TheoryEvidence] = []
    for item in structure.element_profile.illness_medicine:
        medicine = [str(element) for element in item.get("medicine", [])]
        availability = _mean((_element_availability(structure, element) for element in medicine), 0.0)
        candidates.append(
            TheoryEvidence(
                layer_key,
                "disease_medicine",
                _clip((availability - 0.5) * 1.55),
                0.74,
                str(item.get("illness") or "illness"),
                tuple(str(item.get("basis") or "").split())[:8],
            )
        )
    return sorted(
        candidates,
        key=lambda item: abs(item.quality) * item.materiality,
        reverse=True,
    )


def _cycle_evidence(layer_key: str, structure: ChartStructure, contract: Any, requirement: Any) -> list[TheoryEvidence]:
    profile = structure.cycle_regulation_profile or {}
    candidates: list[TheoryEvidence] = []
    aliases = _DOMAIN_ALIASES.get(requirement.domain, frozenset({requirement.domain}))
    for signal in list(profile.get("signals") or []):
        role_quality, role_hits = _signal_role_alignment(signal, structure, contract)
        directed_quality, directed_hits = _directed_role_alignment(signal, structure, contract)
        if directed_hits:
            role_quality = _clip(directed_quality * 0.58 + role_quality * 0.42)
            role_hits += directed_hits
        chain_match = _chain_match_score(requirement.classical_chains, signal)
        domain_links = set(str(item) for item in signal.get("domain_links", []) or [])
        if role_hits == 0 and chain_match <= 0.0:
            continue
        if domain_links and not aliases.intersection(domain_links) and chain_match <= 0.0:
            continue
        polarity = str(signal.get("polarity") or "mixed")
        effect_strength = float(signal.get("effect_strength", signal.get("score", 50.0)) or 50.0)
        if polarity == "support":
            quality = 0.35 + max(0.0, effect_strength - 50.0) / 75.0
        elif polarity == "pressure":
            quality = -(0.42 + max(0.0, effect_strength - 50.0) / 70.0)
        else:
            quality = 0.0
        if role_hits:
            if polarity == "support":
                if role_quality < -0.2:
                    quality *= -0.62
                elif role_quality > 0.2:
                    quality += 0.15 * role_quality
                else:
                    quality *= 0.72
            elif polarity == "pressure":
                if role_quality > 0.2:
                    quality *= 0.78
                elif role_quality < -0.2:
                    quality -= 0.10 * abs(role_quality)
            else:
                quality = 0.26 * role_quality
        if quality > 0:
            quality += 0.12 * chain_match
        elif quality < 0:
            quality -= 0.06 * chain_match
        reality = min(1.0, max(0.2, float(signal.get("reality_score") or 8.0) / 20.0))
        materiality = min(1.0, 0.42 + reality * 0.34 + chain_match * 0.18 + min(0.12, role_hits * 0.05))
        candidates.append(
            TheoryEvidence(
                layer_key,
                "element_chain",
                _clip(quality),
                materiality,
                str(signal.get("signal_id") or "cycle"),
                tuple(str(item) for item in (signal.get("basis_codes") or [])[:8]),
            )
        )
    return sorted(
        candidates,
        key=lambda item: item.materiality * (0.35 + abs(item.quality)),
        reverse=True,
    )


def _visibility_evidence(layer_key: str, structure: ChartStructure, contract: Any, *, hidden: bool) -> list[TheoryEvidence]:
    profile = structure.ten_god_profile
    counts = profile.hidden_counts if hidden else profile.visible_counts
    support = sum(float(counts.get(item, 0.0)) for item in contract.support_ten_gods)
    pressure = sum(float(counts.get(item, 0.0)) for item in contract.pressure_ten_gods)
    if not contract.support_ten_gods:
        support = sum(
            float(value)
            for ten_god, value in counts.items()
            if _ten_god_group(str(ten_god)) in set(contract.support_groups)
        )
    if not contract.pressure_ten_gods:
        pressure = sum(
            float(value)
            for ten_god, value in counts.items()
            if _ten_god_group(str(ten_god)) in set(contract.pressure_groups)
        )
    if support <= 0.0 and pressure <= 0.0:
        return [TheoryEvidence(layer_key, "visibility_reality", -0.52, 0.48 if hidden else 0.62, "required_role_absent")]
    support_reality = min(1.0, support / (1.1 if hidden else 0.8))
    pressure_reality = min(1.0, pressure / (1.0 if hidden else 0.75))
    quality = support_reality * 0.82 - pressure_reality * 0.68 - 0.12
    return [
        TheoryEvidence(
            layer_key,
            "visibility_reality",
            _clip(quality),
            0.68 if hidden else 0.90,
            "hidden_roles" if hidden else "visible_roles",
        )
    ]


def _ten_god_presence_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    *,
    exact: bool,
) -> list[TheoryEvidence]:
    """Retain each exact ten god or functional group as its own premise."""

    profile = structure.ten_god_profile
    support_items = contract.support_ten_gods if exact else contract.support_groups
    pressure_items = contract.pressure_ten_gods if exact else contract.pressure_groups
    ordered = list(dict.fromkeys((*support_items, *pressure_items)))
    role_values = (
        _contract_ten_god_values(contract)
        if exact
        else _contract_group_values(contract)
    )
    evidence: list[TheoryEvidence] = []
    for index, key in enumerate(ordered):
        if exact:
            visible = float(profile.visible_counts.get(key, 0.0) or 0.0)
            hidden = float(profile.hidden_counts.get(key, 0.0) or 0.0)
            amount = visible + hidden * 0.78
        else:
            visible = 0.0
            hidden = 0.0
            amount = float(profile.group_scores.get(key, 0.0) or 0.0)
        scale = 1.35 if exact else 1.75
        presence = min(1.45, amount / scale)
        role_value = _clip(role_values.get(key, 0.0))
        if role_value > 0.0:
            if presence <= 0.03:
                functional_quality = -0.58
            elif presence < 0.32:
                functional_quality = -0.42 + presence * 1.55
            elif presence <= 1.0:
                functional_quality = 0.08 + (presence - 0.32) * 1.08
            else:
                # More is not indefinitely better. Excess keeps some usable
                # capacity but begins to create rigidity, leakage or overload;
                # the exact consequence is resolved by month and capacity gates.
                functional_quality = 0.81 - (presence - 1.0) * 0.74
            quality = functional_quality * abs(role_value)
        elif role_value < 0.0:
            # A pressure role is neutral when absent and increasingly costly
            # as it gains material presence. Its regulation is judged by the
            # interaction and pattern-action layers, not assumed here.
            quality = -max(0.0, presence - 0.05) * 0.86 * abs(role_value)
        else:
            quality = 0.0
        reality = min(1.0, visible / 0.9) * 0.58 + min(1.0, hidden / 1.2) * 0.32 if exact else min(1.0, amount / 1.8) * 0.72
        absence_materiality = 0.54 if role_value > 0.0 and amount <= 0.04 else 0.0
        materiality = max(absence_materiality, 0.38 + reality * 0.54)
        materiality *= (0.88 + abs(role_value) * 0.12) * (
            0.90 + (1.0 / (1.0 + index * 0.20)) * 0.10
        )
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="ten_god_presence",
                quality=_clip(quality),
                materiality=max(0.28, min(1.0, materiality)),
                source_key=f"{'ten_god' if exact else 'group'}:{key}:{amount:.3f}",
            )
        )
    return evidence


def _position_group_weights(structure: ChartStructure, position: str) -> dict[str, float]:
    signal = structure.position_signals.get(position)
    if signal is None:
        return {}
    roles = [
        (signal.stem_ten_god, float(signal.stem_visibility_weight)),
        (signal.branch_main_ten_god, float(signal.branch_reality_weight)),
    ]
    hidden_weight = float(signal.hidden_reality_weight) / max(1, len(signal.hidden_ten_gods))
    roles.extend((ten_god, hidden_weight) for ten_god in signal.hidden_ten_gods)
    groups: dict[str, float] = {}
    for ten_god, weight in roles:
        group = _ten_god_group(str(ten_god))
        if group:
            groups[group] = groups.get(group, 0.0) + float(weight)
    return groups


def _position_ten_god_weights(structure: ChartStructure, position: str) -> dict[str, float]:
    signal = structure.position_signals.get(position)
    if signal is None:
        return {}
    roles = [
        (signal.stem_ten_god, float(signal.stem_visibility_weight)),
        (signal.branch_main_ten_god, float(signal.branch_reality_weight)),
    ]
    hidden_weight = float(signal.hidden_reality_weight) / max(1, len(signal.hidden_ten_gods))
    roles.extend((ten_god, hidden_weight) for ten_god in signal.hidden_ten_gods)
    values: dict[str, float] = {}
    for ten_god, weight in roles:
        key = str(ten_god or "")
        if key:
            values[key] = values.get(key, 0.0) + float(weight)
    return values


def _weighted_position_presence(
    available: dict[str, float],
    role_values: dict[str, float],
    *,
    positive: bool,
) -> float:
    weighted = 0.0
    denominator = 0.0
    for key, role_value in role_values.items():
        if positive and role_value <= 0.0:
            continue
        if not positive and role_value >= 0.0:
            continue
        weight = abs(role_value)
        weighted += min(1.0, float(available.get(key, 0.0)) / 0.9) * weight
        denominator += weight
    return weighted / denominator if denominator else 0.0


def _position_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
) -> list[TheoryEvidence]:
    positions = list(requirement.required_positions or contract.focus_positions)
    evidence: list[TheoryEvidence] = []
    for index, position in enumerate(dict.fromkeys(positions)):
        signal = structure.position_signals.get(position)
        if signal is None:
            if position == "hour" and getattr(contract, "hour_focus", False):
                evidence.append(
                    TheoryEvidence(layer_key, "position", 0.0, 0.24, "hour:unknown")
                )
            continue
        groups = _position_group_weights(structure, position)
        exact_ten_gods = _position_ten_god_weights(structure, position)
        group_values = _contract_group_values(contract)
        ten_god_values = _contract_ten_god_values(contract)
        group_support = _weighted_position_presence(groups, group_values, positive=True)
        group_pressure = _weighted_position_presence(groups, group_values, positive=False)
        exact_support = _weighted_position_presence(
            exact_ten_gods,
            ten_god_values,
            positive=True,
        )
        exact_pressure = _weighted_position_presence(
            exact_ten_gods,
            ten_god_values,
            positive=False,
        )
        has_exact_support = any(value > 0.0 for value in ten_god_values.values())
        has_exact_pressure = any(value < 0.0 for value in ten_god_values.values())
        support_presence = (
            exact_support * 0.68 + group_support * 0.32
            if has_exact_support
            else group_support
        )
        pressure_presence = (
            exact_pressure * 0.68 + group_pressure * 0.32
            if has_exact_pressure
            else group_pressure
        )
        quality = support_presence * 0.84 - pressure_presence * 0.72
        if support_presence <= 0.02 and contract.support_groups:
            quality -= 0.24
        layer_factor = 0.78 if layer_key == "life_stage_positions" else 1.0
        materiality = min(
            1.0,
            (
                0.46
                + float(signal.stem_visibility_weight) * 0.12
                + float(signal.branch_reality_weight) * 0.16
                + float(signal.hidden_reality_weight) * 0.10
            )
            * layer_factor,
        )
        source_context = (
            f"{signal.life_stage}:{signal.age_scope}"
            if layer_key == "life_stage_positions"
            else signal.primary_context
        )
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="position",
                quality=_clip(quality),
                materiality=max(0.30, materiality * (0.92 + 0.08 / (index + 1))),
                source_key=f"position:{position}:{source_context}",
                basis_codes=tuple(signal.position_basis_codes[:8]),
            )
        )
    return evidence


def _element_fit_quality(structure: ChartStructure, element: str) -> float:
    fit = structure.month_governance_profile.element_fits.get(element)
    if fit is None:
        return 0.0
    return _clip(
        (float(fit.support_score) - float(fit.pressure_score)) / 6.0
    )


def _branch_pair_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
) -> list[TheoryEvidence]:
    required = set(requirement.required_positions or contract.relation_positions)
    aliases = _DOMAIN_ALIASES.get(requirement.domain, frozenset({requirement.domain}))
    element_groups = _element_group_map(structure)
    evidence: list[TheoryEvidence] = []
    for pair in structure.branch_pair_combinations:
        if required and not required.intersection(pair.positions):
            continue
        if pair.domain_links and not aliases.intersection(set(pair.domain_links)):
            position_fit = _position_materiality(pair.positions, required)
            if position_fit < 0.75:
                continue
        groups = [element_groups.get(element, "") for element in pair.elements]
        role_quality, role_hits = _role_alignment(groups, contract)
        source_fit = _element_fit_quality(structure, pair.source_element)
        target_fit = _element_fit_quality(structure, pair.target_element)
        if pair.element_relation == "same":
            path_quality = (source_fit + target_fit) / 2.0
        elif pair.element_relation == "generates":
            path_quality = source_fit * 0.34 + target_fit * 0.66
        else:
            path_quality = source_fit * 0.42 - target_fit * 0.66
        if role_hits:
            quality = role_quality * 0.58 + path_quality * 0.42
        else:
            quality = path_quality * 0.52
        intensity = _strength_weight(pair.intensity)
        materiality = min(
            1.0,
            0.36
            + intensity * 0.28
            + _position_materiality(pair.positions, required) * 0.22
            + (0.10 if pair.formal_relation_types else 0.0),
        )
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="branch_pair",
                quality=_clip(quality),
                materiality=max(0.24, materiality),
                source_key=f"pair:{pair.pair_id}:{pair.element_relation}",
                basis_codes=tuple(pair.basis_codes[:8]),
            )
        )
    return evidence


def _formal_branch_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
) -> list[TheoryEvidence]:
    required = set(requirement.required_positions or contract.relation_positions)
    element_groups = _element_group_map(structure)
    evidence: list[TheoryEvidence] = []
    for interaction in structure.branch_interactions:
        if required and not required.intersection(interaction.positions):
            continue
        if layer_key == "branch_transformation" and not interaction.effect_element:
            continue
        polarity = branch_relation_polarity(
            structure.element_profile,
            interaction,
            structure.pattern_profile,
        )
        groups = [element_groups.get(element, "") for element in polarity.activated_elements]
        role_quality, role_hits = _role_alignment(groups, contract)
        polarity_quality = _clip((polarity.useful_score - polarity.pressure_score) / 5.0)
        quality = (
            polarity_quality * 0.48 + role_quality * 0.52
            if role_hits
            else polarity_quality * 0.72
        )
        intensity = _strength_weight(interaction.intensity)
        materiality = min(
            1.0,
            0.42
            + intensity * 0.28
            + _position_materiality(interaction.positions, required) * 0.22,
        )
        # A formal branch relation is one fact with two readings: which
        # element it activates and how much structural friction its form
        # creates.  Emitting those readings as two full evidence rows made one
        # clash/punishment count twice and pulled unrelated metrics toward the
        # same middle-low band.  Keep the direction as the main judgment and
        # fold a bounded friction cost into that same fact instead.
        friction_penalty = min(
            0.18,
            float(polarity.effective_friction or 0.0) * 0.18,
        )
        quality = _clip(quality - friction_penalty)
        relation_basis_codes = [interaction.basis_code]
        if polarity.effective_friction > 0.0:
            relation_basis_codes.extend(
                [
                    f"relation_direction_{polarity.polarity}",
                    f"relation_structural_friction_{interaction.relation_type}",
                    f"relation_intrinsic_friction_{polarity.intrinsic_friction:.4f}",
                    f"relation_effective_friction_{polarity.effective_friction:.4f}",
                ]
            )
        evidence.append(
            TheoryEvidence(
                layer_key=layer_key,
                family_id="branch_pair",
                quality=_clip(quality),
                materiality=max(0.30, materiality),
                source_key=f"formal:{interaction.relation_type}:{'-'.join(interaction.branches)}:{'-'.join(interaction.positions)}",
                basis_codes=tuple(relation_basis_codes),
            )
        )
    return evidence


def _yin_yang_evidence(layer_key: str, structure: ChartStructure) -> list[TheoryEvidence]:
    values = [
        STEM_METADATA.get(signal.stem_key, {}).get("yin_yang")
        for signal in structure.position_signals.values()
    ]
    yang = sum(value == "yang" for value in values)
    yin = sum(value == "yin" for value in values)
    total = yang + yin
    if not total:
        return []
    # Yin and yang describe expression mode, not a universal good/bad axis.
    # Preserve the fact for interaction audits without manufacturing quality.
    return [
        TheoryEvidence(
            layer_key,
            "yin_yang",
            0.0,
            0.48 + min(0.22, abs(yang - yin) / total * 0.22),
            f"yin:{yin}:yang:{yang}:day_master:{structure.day_master_yin_yang}",
        )
    ]


def _rooting_evidence(layer_key: str, structure: ChartStructure, contract: Any) -> list[TheoryEvidence]:
    support_groups = set(contract.support_groups)
    pressure_groups = set(contract.pressure_groups)
    candidates = [
        candidate
        for candidate in structure.gyeokguk_profile.candidates
        if candidate.source_group in support_groups | pressure_groups
    ]
    evidence: list[TheoryEvidence] = []
    represented_support = {candidate.source_group for candidate in candidates if candidate.source_group in support_groups}
    for group in support_groups - represented_support:
        evidence.append(
            TheoryEvidence(layer_key, "visibility_reality", -0.48, 0.52, f"unrooted_absence:{group}")
        )
    for candidate in candidates:
        reality = (0.52 if candidate.rooted else -0.32) + (0.26 if candidate.protruded else -0.06)
        if candidate.source_group in pressure_groups:
            reality = -max(0.0, reality + 0.18)
        evidence.append(
            TheoryEvidence(
                layer_key,
                "visibility_reality",
                _clip(reality),
                min(1.0, 0.50 + float(candidate.score) / 220.0),
                f"{candidate.pattern}:{candidate.source_group}:{candidate.source_stem}",
                tuple(candidate.basis_codes[:8]),
            )
        )
    return evidence


def _pattern_state_evidence(layer_key: str, structure: ChartStructure, contract: Any, *, clarity: bool) -> list[TheoryEvidence]:
    profile = structure.gyeokguk_profile
    quality = (
        _CLARITY_QUALITY.get(profile.clarity_state, -0.08)
        if clarity
        else _FORMATION_QUALITY.get(profile.formation_state, -0.08)
    )
    if profile.primary_group in set(contract.pressure_groups):
        quality *= -0.78
    elif profile.primary_group not in set(contract.support_groups):
        quality *= 0.48
    candidate_score = max((candidate.score for candidate in profile.candidates), default=50)
    return [
        TheoryEvidence(
            layer_key,
            "pattern_state",
            _clip(quality),
            min(1.0, 0.56 + float(candidate_score) / 220.0),
            f"{profile.primary_pattern}:{profile.primary_group}",
            tuple(profile.basis_codes[:8]),
        )
    ]


def _single_action_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
    *,
    layer_role: str,
    signal_audit: dict[str, dict[str, int]] | None = None,
) -> list[TheoryEvidence]:
    candidates: list[TheoryEvidence] = []
    aliases = _DOMAIN_ALIASES.get(requirement.domain, frozenset({requirement.domain}))
    audit = (
        signal_audit.setdefault(
            layer_key,
            {"observed": 0, "applied": 0, "rejected_no_metric_link": 0},
        )
        if signal_audit is not None
        else None
    )
    for match in structure.gyeokguk_profile.ten_god_action_matches:
        if audit is not None:
            audit["observed"] += 1
        domain_fit = bool(aliases.intersection(set(match.domain_priority)))
        chain_match = _chain_match_score(requirement.classical_chains, match)
        role_quality, role_hits = _signal_role_alignment(match, structure, contract)
        position_context = match.position_context or {}
        positions = list(position_context.get("visible_positions") or []) + list(position_context.get("hidden_positions") or [])
        position_hit = bool(
            _position_scopes(requirement.required_positions).intersection(
                _position_scopes(positions)
            )
        )
        substantive_link = bool(
            chain_match
            or (domain_fit and role_hits and (position_hit or layer_role != "context"))
        )
        if not substantive_link:
            if audit is not None:
                audit["rejected_no_metric_link"] += 1
            continue
        if audit is not None:
            audit["applied"] += 1
        quality = _SINGLE_VERDICT_QUALITY.get(match.verdict, 0.0)
        quality += _SINGLE_CONTEXT_QUALITY.get(match.context_judgment_state, 0.0)
        if quality > 0.0:
            if role_quality < -0.2 and match.role_grade not in {"regulator", "breaker_or_medicine", "regulator_or_breaker"}:
                quality *= -0.58
            elif role_quality > 0.2:
                quality += 0.12
            quality += 0.12 * chain_match
        elif quality < 0.0:
            if role_quality > 0.2:
                quality *= 0.78
            elif role_quality < -0.2:
                quality -= 0.08
            quality -= 0.06 * chain_match
        materiality = min(
            1.0,
            0.34
            + float(match.presence_score) / 145.0
            + _position_materiality(positions, requirement.required_positions) * 0.20
            + chain_match * 0.14,
        )
        candidates.append(
            TheoryEvidence(
                layer_key,
                "pattern_action",
                _clip(quality),
                materiality,
                match.rule_key,
                tuple(match.basis_codes[:8]),
            )
        )
    return sorted(
        candidates,
        key=lambda item: item.materiality * (0.35 + abs(item.quality)),
        reverse=True,
    )


def _dual_action_evidence(
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
    *,
    layer_role: str,
    signal_audit: dict[str, dict[str, int]] | None = None,
) -> list[TheoryEvidence]:
    candidates: list[TheoryEvidence] = []
    aliases = _DOMAIN_ALIASES.get(requirement.domain, frozenset({requirement.domain}))
    audit = (
        signal_audit.setdefault(
            layer_key,
            {"observed": 0, "applied": 0, "rejected_no_metric_link": 0},
        )
        if signal_audit is not None
        else None
    )
    for match in structure.gyeokguk_profile.dual_ten_god_action_matches:
        if audit is not None:
            audit["observed"] += 1
        if match.verdict == "not_activated" or float(match.presence_score) <= 0.0:
            if audit is not None:
                audit["rejected_no_metric_link"] += 1
            continue
        domain_fit = bool(aliases.intersection(set(match.domain_priority)))
        chain_match = _chain_match_score(requirement.classical_chains, match)
        role_quality, role_hits = _signal_role_alignment(match, structure, contract)
        position_context = match.position_context or {}
        positions = list(position_context.get("first_visible_positions") or []) + list(position_context.get("second_visible_positions") or [])
        position_hit = bool(
            _position_scopes(requirement.required_positions).intersection(
                _position_scopes(positions)
            )
        )
        substantive_link = bool(
            chain_match
            or (domain_fit and role_hits and (position_hit or layer_role != "context"))
        )
        if not substantive_link:
            if audit is not None:
                audit["rejected_no_metric_link"] += 1
            continue
        if audit is not None:
            audit["applied"] += 1
        quality = _DUAL_VERDICT_QUALITY.get(match.verdict, 0.0)
        quality += _DUAL_CONTEXT_QUALITY.get(match.context_judgment_state, 0.0)
        if quality > 0.0:
            if role_quality < -0.2 and match.chain_grade != "medicine_chain":
                quality *= -0.52
            elif role_quality > 0.2:
                quality += 0.10
            quality += 0.14 * chain_match
        elif quality < 0.0:
            if role_quality > 0.2:
                quality *= 0.78
            elif role_quality < -0.2:
                quality -= 0.08
            quality -= 0.08 * chain_match
        materiality = min(
            1.0,
            0.36
            + float(match.presence_score) / 150.0
            + _position_materiality(positions, requirement.required_positions) * 0.18
            + chain_match * 0.16,
        )
        candidates.append(
            TheoryEvidence(
                layer_key,
                "pattern_action",
                _clip(quality),
                materiality,
                match.rule_key,
                tuple(match.basis_codes[:8]),
            )
        )
    return sorted(
        candidates,
        key=lambda item: item.materiality * (0.35 + abs(item.quality)),
        reverse=True,
    )


def _useful_role_evidence(layer_key: str, structure: ChartStructure, contract: Any) -> list[TheoryEvidence]:
    useful = set(structure.month_governance_profile.useful_groups)
    caution = set(structure.month_governance_profile.caution_groups)
    support = set(contract.support_groups)
    pressure = set(contract.pressure_groups)
    support_hits = len(support.intersection(useful))
    support_cautions = len(support.intersection(caution))
    pressure_cautions = len(pressure.intersection(caution))
    pressure_useful = len(pressure.intersection(useful))
    denominator = max(1, len(support) + len(pressure))
    quality = (support_hits + pressure_cautions * 0.35 - support_cautions * 0.8 - pressure_useful * 0.35) / denominator
    return [TheoryEvidence(layer_key, "useful_role", _clip(quality), 0.76, "month_useful_roles")]


def _birth_time_evidence(layer_key: str, structure: ChartStructure, contract: Any) -> list[TheoryEvidence]:
    hour_known = "hour" in structure.position_signals and bool(structure.position_signals.get("hour"))
    if hour_known:
        return [TheoryEvidence(layer_key, "confidence", 0.12, 0.55, "hour_known")]
    if getattr(contract, "hour_focus", False):
        return [TheoryEvidence(layer_key, "confidence", 0.0, 0.25, "hour_unknown")]
    return []


def _layer_evidence(
    *,
    layer_key: str,
    structure: ChartStructure,
    contract: Any,
    requirement: Any,
    legacy_scores: dict[str, float],
    layer_role: str,
    signal_audit: dict[str, dict[str, int]] | None = None,
) -> list[TheoryEvidence]:
    if layer_key == "month_environment":
        return _month_role_evidence(layer_key, structure, contract)
    if layer_key == "month_hidden_phase":
        return _month_hidden_evidence(layer_key, structure, contract)
    if layer_key == "seasonal_element_strength":
        return _element_state_evidence(layer_key, structure, contract, mode="seasonal")
    if layer_key == "element_distribution":
        return _element_state_evidence(layer_key, structure, contract, mode="distribution")
    if layer_key == "element_quality":
        return _element_state_evidence(layer_key, structure, contract, mode="quality")
    if layer_key == "day_master_capacity":
        return _day_master_capacity_evidence(layer_key, structure, contract)
    if layer_key == "climate_temperature":
        return _climate_evidence(layer_key, structure, kind="temperature")
    if layer_key == "climate_moisture":
        return _climate_evidence(layer_key, structure, kind="moisture")
    if layer_key == "illness_medicine":
        return _illness_medicine_evidence(layer_key, structure)
    if layer_key == "element_circulation":
        return _cycle_evidence(layer_key, structure, contract, requirement)
    if layer_key == "element_combinations":
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.element_combination_profile,
                ("heavenly_stem_signals", "hidden_stem_signals", "stem_branch_signals", "month_hidden_visible_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "yin_yang_balance":
        return _yin_yang_evidence(layer_key, structure)
    if layer_key == "visible_stems":
        return _visibility_evidence(layer_key, structure, contract, hidden=False)
    if layer_key == "hidden_stems":
        return _visibility_evidence(layer_key, structure, contract, hidden=True)
    if layer_key == "protrusion_rooting":
        return _rooting_evidence(layer_key, structure, contract)
    if layer_key in {"stem_combinations", "stem_transformation"}:
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.combination_profile,
                ("heavenly_stem_signals", "hidden_stem_signals", "stem_branch_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "stem_reception":
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.stem_reception_profile,
                ("visible_stem_signals", "hidden_stem_signals", "branch_main_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "directional_interactions":
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.directional_interaction_profile,
                ("heavenly_stem_signals", "hidden_stem_signals", "stem_branch_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "branch_pairs":
        return _branch_pair_evidence(layer_key, structure, contract, requirement)
    if layer_key in {"formal_branch_relations", "branch_transformation"}:
        return _formal_branch_evidence(layer_key, structure, contract, requirement)
    if layer_key in {"position_palaces", "life_stage_positions", "kinship_projection"}:
        return _position_evidence(layer_key, structure, contract, requirement)
    if layer_key == "exact_ten_gods":
        return _ten_god_presence_evidence(layer_key, structure, contract, exact=True)
    if layer_key == "ten_god_groups":
        return _ten_god_presence_evidence(layer_key, structure, contract, exact=False)
    if layer_key == "ten_god_interactions":
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.ten_god_interaction_profile,
                ("visible_stem_signals", "hidden_stem_signals", "stem_branch_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "pattern_formation":
        return _pattern_state_evidence(layer_key, structure, contract, clarity=False)
    if layer_key == "pattern_clarity":
        return _pattern_state_evidence(layer_key, structure, contract, clarity=True)
    if layer_key == "pattern_single_actions":
        return _single_action_evidence(
            layer_key,
            structure,
            contract,
            requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "pattern_dual_actions":
        return _dual_action_evidence(
            layer_key,
            structure,
            contract,
            requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "useful_element_roles":
        return _useful_role_evidence(layer_key, structure, contract)
    if layer_key == "special_pattern_exceptions":
        flags = list(structure.pattern_profile.special_pattern_flags or [])
        return [TheoryEvidence(layer_key, "pattern_exception", -0.48, 0.66, ",".join(flags))] if flags else []
    if layer_key == "integrated_saju_signals":
        return _profile_signal_evidence(
            layer_key=layer_key,
            signals=_profile_signals(
                structure.integrated_saju_profile,
                ("visible_pair_signals", "hidden_pair_signals", "stem_branch_pair_signals"),
            ),
            structure=structure,
            contract=contract,
            requirement=requirement,
            layer_role=layer_role,
            signal_audit=signal_audit,
        )
    if layer_key == "spouse_star_gender":
        return _role_fit_evidence(layer_key, structure, contract, legacy_scores.get("spouse", 50.0))
    if layer_key == "birth_time_confidence":
        return _birth_time_evidence(layer_key, structure, contract)
    # Support-only, timing-only, selection-only and evidence-accounting layers
    # remain registered and audited but do not manufacture a natal score.
    return []


def _requirement_layer_roles(requirement: Any) -> dict[str, str]:
    """Return declared roles plus every applicable active theory layer.

    A metric requirement names the layers that are decisive for that metric.
    The chart, however, can contain a relevant counter-action in a layer that
    is not one of those headline premises.  Omitting that layer is information
    loss.  Such layers therefore enter as low-weight context after domain and
    scoring-role gates; they can corroborate or restrain a conclusion but
    cannot outrank a declared primary premise.
    """

    roles: dict[str, str] = {}
    for layer_key in requirement.pressure_layers:
        roles[layer_key] = "pressure"
    for layer_key in requirement.confirming_layers:
        roles[layer_key] = "confirming"
    for layer_key in requirement.primary_layers:
        roles[layer_key] = "primary"
    for layer_key in _UNIVERSAL_GATE_LAYERS:
        if layer_key in roles:
            roles[layer_key] = "gate"
    for layer_key, layer in METRIC_THEORY_LAYERS.items():
        if layer_key in roles:
            continue
        if layer.status not in {"active", "partial"}:
            continue
        if layer.scoring_role in _NON_SCORING_ROLES or layer.scoring_role == "confidence_gate":
            continue
        allowed_domains = _DOMAIN_LIMITED_CONTEXT_LAYERS.get(layer_key)
        if allowed_domains and requirement.domain not in allowed_domains:
            continue
        roles[layer_key] = "context"
    return roles


def _scoring_family(evidence: TheoryEvidence) -> str:
    group = METRIC_THEORY_LAYERS[evidence.layer_key].anti_double_count_group
    return group or evidence.family_id


def _correlation_cluster(family: str) -> str:
    if family in _PAIR_DERIVED_FAMILIES:
        return "pair_synthesis"
    return _CORRELATION_CLUSTERS.get(family, family)


def _hierarchy_for_family(family: str) -> str:
    if family in _GOVERNANCE_FAMILIES:
        return "governance"
    if family in _REALITY_FAMILIES:
        return "reality"
    if family in _INTERACTION_FAMILIES:
        return "interaction"
    return "context"


def _evidence_weight(evidence: TheoryEvidence, role: str) -> float:
    layer = METRIC_THEORY_LAYERS[evidence.layer_key]
    role_weight = {
        "primary": 1.0,
        "confirming": 0.68,
        "pressure": 1.0 if evidence.quality < 0 else 0.46,
        "gate": 0.72,
        "context": 0.38,
    }.get(role, 0.38)
    priority_weight = {1: 1.0, 2: 0.86, 3: 0.70, 4: 0.54}.get(layer.priority, 0.7)
    status_weight = 0.72 if layer.status == "partial" else 1.0
    return evidence.materiality * role_weight * priority_weight * status_weight


def _exact_evidence_key(item: TheoryEvidence) -> tuple[str, str, str, tuple[str, ...]]:
    return (item.layer_key, item.family_id, item.source_key, item.basis_codes)


def _deduplicate_exact_sources(
    evidence: Iterable[TheoryEvidence],
    layer_roles: dict[str, str],
) -> list[TheoryEvidence]:
    """Remove only literal duplicate rows, never distinct theoretical facts."""

    selected: dict[tuple[str, str, str, tuple[str, ...]], TheoryEvidence] = {}
    for item in evidence:
        key = _exact_evidence_key(item)
        current = selected.get(key)
        if current is None:
            selected[key] = item
            continue
        current_weight = _evidence_weight(current, layer_roles.get(current.layer_key, "confirming"))
        item_weight = _evidence_weight(item, layer_roles.get(item.layer_key, "confirming"))
        current_rank = current_weight * (0.45 + abs(current.quality))
        item_rank = item_weight * (0.45 + abs(item.quality))
        if item_rank > current_rank:
            selected[key] = item
    return sorted(
        selected.values(),
        key=lambda item: _evidence_weight(
            item,
            layer_roles.get(item.layer_key, "context"),
        )
        * (0.45 + abs(item.quality)),
        reverse=True,
    )


def _diminishing_aggregate(
    items: list[TheoryEvidence],
    layer_roles: dict[str, str],
) -> dict[str, Any]:
    """Aggregate correlated evidence without deleting any source signal."""

    ranked = sorted(
        items,
        key=lambda item: _evidence_weight(
            item,
            layer_roles.get(item.layer_key, "context"),
        )
        * (0.40 + abs(item.quality)),
        reverse=True,
    )
    numerator = 0.0
    denominator = 0.0
    support_mass = 0.0
    pressure_mass = 0.0
    support_count = 0
    pressure_count = 0
    for index, item in enumerate(ranked):
        role = layer_roles.get(item.layer_key, "context")
        weight = _evidence_weight(item, layer_roles.get(item.layer_key, "confirming"))
        if weight <= 0.0:
            continue
        # The first premise remains fully visible. Additional correlated
        # premises confirm it with a square-root decay instead of disappearing
        # or stacking as full independent bonuses.
        decay = 1.0 / math.sqrt(index + 1.0)
        effective_weight = weight * decay
        numerator += item.quality * effective_weight
        denominator += effective_weight
        if item.quality > 0.10:
            support_mass += item.quality * effective_weight
            support_count += 1
        elif item.quality < -0.10:
            pressure_mass += abs(item.quality) * effective_weight
            pressure_count += 1
    quality = numerator / denominator if denominator else 0.0

    def role_view(allowed_roles: frozenset[str]) -> tuple[float, float, int]:
        role_numerator = 0.0
        role_denominator = 0.0
        role_count = 0
        for index, item in enumerate(
            candidate
            for candidate in ranked
            if layer_roles.get(candidate.layer_key, "context") in allowed_roles
        ):
            role = layer_roles.get(item.layer_key, "context")
            weight = _evidence_weight(item, role)
            if weight <= 0.0:
                continue
            effective_weight = weight / math.sqrt(index + 1.0)
            role_numerator += item.quality * effective_weight
            role_denominator += effective_weight
            role_count += 1
        return (
            _clip(role_numerator / role_denominator if role_denominator else 0.0),
            min(1.0, role_denominator / 1.75),
            role_count,
        )

    decisive_quality, decisive_materiality, decisive_count = role_view(
        _DECISIVE_LAYER_ROLES
    )
    confirming_quality, confirming_materiality, confirming_count = role_view(
        _CORROBORATING_LAYER_ROLES
    )
    gate_quality, gate_materiality, gate_count = role_view(frozenset({"gate"}))
    context_quality, context_materiality, context_count = role_view(
        frozenset({"context"})
    )
    return {
        "quality": _clip(quality),
        "materiality": min(1.0, denominator / 1.75),
        "effective_weight": denominator,
        "source_count": len(ranked),
        "support_source_count": support_count,
        "pressure_source_count": pressure_count,
        "support_mass": support_mass,
        "pressure_mass": pressure_mass,
        "dominant_source": ranked[0].source_key if ranked else "",
        "layers": sorted({item.layer_key for item in ranked}),
        "decisive_quality": decisive_quality,
        "decisive_materiality": decisive_materiality,
        "decisive_source_count": decisive_count,
        "confirming_quality": confirming_quality,
        "confirming_materiality": confirming_materiality,
        "confirming_source_count": confirming_count,
        "gate_quality": gate_quality,
        "gate_materiality": gate_materiality,
        "gate_source_count": gate_count,
        "context_quality": context_quality,
        "context_materiality": context_materiality,
        "context_source_count": context_count,
    }


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "quality": 0.0,
            "materiality": 0.0,
            "effective_weight": 0.0,
            "source_count": 0,
            "family_count": 0,
            "support_source_count": 0,
            "pressure_source_count": 0,
            "support_mass": 0.0,
            "pressure_mass": 0.0,
        }
    ranked = sorted(
        rows,
        key=lambda row: float(row.get("effective_weight", 0.0))
        * (0.40 + abs(float(row.get("quality", 0.0)))),
        reverse=True,
    )
    numerator = 0.0
    denominator = 0.0
    for index, row in enumerate(ranked):
        weight = max(0.05, float(row.get("materiality", 0.0)))
        decay = 1.0 / math.sqrt(index + 1.0)
        numerator += float(row.get("quality", 0.0)) * weight * decay
        denominator += weight * decay
    return {
        "quality": _clip(numerator / denominator if denominator else 0.0),
        "materiality": min(1.0, denominator / 1.8),
        "effective_weight": denominator,
        "source_count": sum(int(row.get("source_count", 0)) for row in ranked),
        "family_count": sum(int(row.get("family_count", 1)) for row in ranked),
        "support_source_count": sum(int(row.get("support_source_count", 0)) for row in ranked),
        "pressure_source_count": sum(int(row.get("pressure_source_count", 0)) for row in ranked),
        "support_mass": sum(float(row.get("support_mass", 0.0)) for row in ranked),
        "pressure_mass": sum(float(row.get("pressure_mass", 0.0)) for row in ranked),
    }


def _build_theory_aggregates(
    evidence: list[TheoryEvidence],
    layer_roles: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_family: dict[str, list[TheoryEvidence]] = defaultdict(list)
    for item in evidence:
        by_family[_scoring_family(item)].append(item)

    family_rows: list[dict[str, Any]] = []
    for family, items in by_family.items():
        row = _diminishing_aggregate(items, layer_roles)
        row.update(
            {
                "family": family,
                "cluster": _correlation_cluster(family),
                "hierarchy": _hierarchy_for_family(family),
                "family_count": 1,
            }
        )
        family_rows.append(row)

    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in family_rows:
        by_cluster[str(row["cluster"])].append(row)
    cluster_rows: list[dict[str, Any]] = []
    for cluster, rows in by_cluster.items():
        aggregate = _aggregate_rows(rows)
        hierarchies = {str(row["hierarchy"]) for row in rows}
        aggregate.update(
            {
                "cluster": cluster,
                "hierarchy": next(iter(hierarchies)) if len(hierarchies) == 1 else "interaction",
                "families": sorted(str(row["family"]) for row in rows),
            }
        )
        cluster_rows.append(aggregate)

    by_hierarchy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cluster_rows:
        by_hierarchy[str(row["hierarchy"])].append(row)
    hierarchy_rows: list[dict[str, Any]] = []
    for hierarchy in ("governance", "reality", "interaction", "context"):
        rows = by_hierarchy.get(hierarchy, [])
        aggregate = _aggregate_rows(rows)
        aggregate.update(
            {
                "hierarchy": hierarchy,
                "clusters": sorted(str(row["cluster"]) for row in rows),
            }
        )
        hierarchy_rows.append(aggregate)
    return family_rows, cluster_rows, hierarchy_rows


def _high_dimensional_quality(
    family_rows: list[dict[str, Any]],
    hierarchy_rows: list[dict[str, Any]],
) -> dict[str, float]:
    """Reconcile the chart as a functional system, not a flat vote.

    Authority decides whether a role is useful, capacity whether the day
    master and climate can carry it, material potential whether the required
    roles exist, manifestation whether they reach a real palace, process how
    they generate/control one another, and stability whether branch reality
    preserves or disrupts the result.  Positive action must pass those gates;
    unresolved pressure does not receive the same benefit of the doubt.
    """

    by_key = {str(row["hierarchy"]): row for row in hierarchy_rows}
    by_family = {str(row["family"]): row for row in family_rows}

    def aggregate_view(
        families: tuple[str, ...],
        *,
        view: str,
        fallback_to_whole: bool = False,
    ) -> tuple[float, float, int]:
        parts: list[tuple[float, float, int]] = []
        for family in families:
            row = by_family.get(family)
            if not row:
                continue
            count = int(row.get(f"{view}_source_count", 0))
            quality = float(row.get(f"{view}_quality", 0.0))
            materiality = float(row.get(f"{view}_materiality", 0.0))
            if count <= 0 and fallback_to_whole:
                count = int(row.get("source_count", 0))
                quality = float(row.get("quality", 0.0))
                materiality = float(row.get("materiality", 0.0))
            if count > 0 and materiality > 0.0:
                parts.append((quality, materiality, count))
        if not parts:
            return 0.0, 0.0, 0
        denominator = sum(materiality for _, materiality, _ in parts) or 1.0
        return (
            _clip(sum(quality * materiality for quality, materiality, _ in parts) / denominator),
            min(1.0, denominator / max(1.0, len(parts) * 0.72)),
            sum(count for _, _, count in parts),
        )

    def metric_view(*families: str) -> tuple[float, float, int]:
        decisive = aggregate_view(tuple(families), view="decisive")
        confirming = aggregate_view(tuple(families), view="confirming")
        parts: list[tuple[float, float, int, float]] = []
        if decisive[2]:
            parts.append((*decisive, 1.0))
        if confirming[2]:
            parts.append((*confirming, 0.62))
        if not parts:
            return 0.0, 0.0, 0
        denominator = sum(materiality * weight for _, materiality, _, weight in parts) or 1.0
        return (
            _clip(
                sum(quality * materiality * weight for quality, materiality, _, weight in parts)
                / denominator
            ),
            min(1.0, denominator),
            sum(count for _, _, count, _ in parts),
        )

    def gate_view(*families: str) -> tuple[float, float, int]:
        return aggregate_view(tuple(families), view="gate")

    def context_view(*families: str) -> tuple[float, float, int]:
        return aggregate_view(tuple(families), view="context")

    def role_system_view(view: str) -> tuple[float, float, int, float, float, float]:
        """Combine one theoretical role without flattening its polarity.

        A high-dimensional judgment is not a vote among every extracted fact.
        First, correlated families are reconciled inside one source cluster.
        Then independent clusters are combined while support and pressure stay
        in separate lanes.  This prevents a decisive weak premise from being
        hidden by numerous mild descriptions of an unrelated strength, while
        preserving every source in the audit ledger.
        """

        hierarchy_weight = {
            "governance": 1.08,
            "reality": 1.16,
            "interaction": 1.12,
            "context": 0.54,
        }
        by_cluster: dict[str, list[tuple[float, float, int, float]]] = defaultdict(list)
        for row in family_rows:
            count = int(row.get(f"{view}_source_count", 0))
            materiality = float(row.get(f"{view}_materiality", 0.0))
            if count <= 0 or materiality <= 0.0:
                continue
            quality = float(row.get(f"{view}_quality", 0.0))
            weight = hierarchy_weight.get(str(row.get("hierarchy") or "context"), 0.54)
            by_cluster[str(row.get("cluster") or row.get("family") or "unknown")].append(
                (quality, materiality, count, weight)
            )

        cluster_views: list[tuple[float, float, int]] = []
        for rows in by_cluster.values():
            ranked = sorted(
                rows,
                key=lambda item: item[1] * item[3] * (0.45 + abs(item[0])),
                reverse=True,
            )
            numerator = 0.0
            denominator = 0.0
            source_count = 0
            for index, (quality, materiality, count, weight) in enumerate(ranked):
                effective = materiality * weight / math.sqrt(index + 1.0)
                numerator += quality * effective
                denominator += effective
                source_count += count
            if denominator:
                cluster_views.append(
                    (
                        _clip(numerator / denominator),
                        min(1.0, denominator / 1.10),
                        source_count,
                    )
                )

        if not cluster_views:
            return 0.0, 0.0, 0, 0.0, 0.0, 0.0

        positive_mass = sum(max(0.0, quality) * materiality for quality, materiality, _ in cluster_views)
        pressure_mass = sum(max(0.0, -quality) * materiality for quality, materiality, _ in cluster_views)
        total_mass = positive_mass + pressure_mass
        signed_balance = (
            (positive_mass - pressure_mass) / (0.42 + total_mass)
            if total_mass
            else 0.0
        )
        weighted_denominator = sum(materiality for _, materiality, _ in cluster_views) or 1.0
        weighted_quality = sum(
            quality * materiality for quality, materiality, _ in cluster_views
        ) / weighted_denominator
        # The lane balance preserves convergent direction; the weighted mean
        # preserves mixed structures. Neither source count nor repeated wording
        # can manufacture a high score by itself.
        system_quality = _clip(signed_balance * 0.64 + weighted_quality * 0.36)
        conflict_ratio = (
            min(positive_mass, pressure_mass) / max(positive_mass, pressure_mass)
            if max(positive_mass, pressure_mass) > 0.001
            else 0.0
        )
        return (
            system_quality,
            min(1.0, weighted_denominator / 3.2),
            sum(count for _, _, count in cluster_views),
            positive_mass,
            pressure_mass,
            conflict_ratio,
        )

    governance = float(by_key.get("governance", {}).get("quality", 0.0))
    reality = float(by_key.get("reality", {}).get("quality", 0.0))
    interaction = float(by_key.get("interaction", {}).get("quality", 0.0))
    context = float(by_key.get("context", {}).get("quality", 0.0))

    month_quality, month_materiality, _ = gate_view("month_authority")
    pattern_metric = metric_view("pattern_state", "useful_role", "pattern_exception")
    pattern_gate = gate_view("pattern_state", "useful_role", "pattern_exception")
    pattern_quality = pattern_metric[0] if pattern_metric[2] else pattern_gate[0]
    capacity_quality, capacity_materiality, _ = gate_view("day_master_capacity")
    climate_gate_row = gate_view("climate_balance", "disease_medicine")
    climate_context_row = context_view("climate_balance", "disease_medicine")
    climate_quality = (
        climate_gate_row[0] if climate_gate_row[2] else climate_context_row[0]
    )
    climate_materiality = max(climate_gate_row[1], climate_context_row[1])
    useful_role_metric = metric_view("useful_role")
    useful_role_gate = gate_view("useful_role")
    useful_role_context = context_view("useful_role")
    useful_role_quality = float(
        useful_role_metric[0]
        if useful_role_metric[2]
        else useful_role_gate[0]
        if useful_role_gate[2]
        else useful_role_context[0]
    )

    authority_metric = metric_view(
        "month_authority", "pattern_state", "useful_role", "pattern_exception"
    )
    carrying_metric = metric_view(
        "day_master_capacity", "climate_balance", "disease_medicine"
    )
    material_metric = metric_view("element_state", "ten_god_presence")
    manifestation_metric = metric_view(
        "visibility_reality", "position", "kinship", "spouse_evidence"
    )
    process_metric = metric_view(
        "element_chain",
        "stem_pair",
        "directional_pair",
        "ten_god_chain",
        "pattern_action",
        "integrated_pair",
    )
    stability_metric = metric_view("branch_pair", "pattern_state")

    authority_quality = authority_metric[0]
    carrying_quality = carrying_metric[0]
    material_quality = material_metric[0]
    manifestation_quality = manifestation_metric[0]
    process_quality = process_metric[0]
    stability_quality = stability_metric[0]

    metric_dimensions = (
        (authority_metric, 0.92),
        (carrying_metric, 0.88),
        (material_metric, 1.00),
        (manifestation_metric, 1.06),
        (process_metric, 1.08),
        (stability_metric, 0.90),
    )
    active_dimensions = [
        (row, weight) for row, weight in metric_dimensions if row[2] > 0
    ]
    dimension_denominator = sum(
        row[1] * weight for row, weight in active_dimensions
    ) or 1.0
    broad_dimension_quality = _clip(
        sum(row[0] * row[1] * weight for row, weight in active_dimensions)
        / dimension_denominator
        if active_dimensions
        else 0.0
    )
    broad_dimension_materiality = min(1.0, dimension_denominator / 3.2)
    active_dimension_count = float(len(active_dimensions))

    decisive_system = role_system_view("decisive")
    confirming_system = role_system_view("confirming")
    gate_system = role_system_view("gate")
    if decisive_system[2] > 0:
        metric_core_quality = _clip(
            decisive_system[0] * 0.72
            + broad_dimension_quality * 0.20
            + confirming_system[0] * 0.08
        )
        metric_core_materiality = min(
            1.0,
            decisive_system[1] * 0.76
            + broad_dimension_materiality * 0.18
            + confirming_system[1] * 0.06,
        )
    else:
        metric_core_quality = broad_dimension_quality
        metric_core_materiality = broad_dimension_materiality

    regime_parts = [
        (month_quality, month_materiality, 1.00),
        (capacity_quality, capacity_materiality, 0.82),
        (climate_quality, climate_materiality, 0.64),
    ]
    if pattern_gate[2]:
        regime_parts.append((pattern_gate[0], pattern_gate[1], 0.86))
    regime_denominator = sum(materiality * weight for _, materiality, weight in regime_parts) or 1.0
    regime_quality = _clip(
        sum(quality * materiality * weight for quality, materiality, weight in regime_parts)
        / regime_denominator
    )

    pressure_balance_numerator = 0.0
    pressure_balance_denominator = 0.0
    for row in family_rows:
        support_mass = float(row.get("support_mass", 0.0))
        pressure_mass = float(row.get("pressure_mass", 0.0))
        total_mass = support_mass + pressure_mass
        if total_mass <= 0.001:
            continue
        weight = max(0.10, float(row.get("materiality", 0.0)))
        pressure_balance_numerator += (
            (support_mass - pressure_mass) / total_mass
        ) * weight
        pressure_balance_denominator += weight
    evidence_balance_quality = _clip(
        pressure_balance_numerator / pressure_balance_denominator
        if pressure_balance_denominator
        else 0.0
    )

    governance_gate = max(0.0, min(1.0, (governance + 1.0) / 2.0))
    month_gate = max(0.0, min(1.0, (month_quality + 1.0) / 2.0))
    pattern_gate = max(0.0, min(1.0, (pattern_quality + 1.0) / 2.0))
    capacity_gate = max(0.0, min(1.0, (capacity_quality + 1.0) / 2.0))
    climate_gate = max(0.0, min(1.0, (climate_quality + 1.0) / 2.0))
    reality_gate = max(0.0, min(1.0, (reality + 1.0) / 2.0))
    authority_gate = max(0.0, min(1.0, (regime_quality + 1.0) / 2.0))
    carrying_gate = max(0.0, min(1.0, (capacity_quality + 1.0) / 2.0))
    material_gate = max(0.0, min(1.0, (material_quality + 1.0) / 2.0))
    manifestation_gate = max(
        0.0,
        min(1.0, (manifestation_quality + 1.0) / 2.0),
    )
    usability_gate = max(
        0.12,
        min(
            1.0,
            0.18
            + authority_gate * 0.30
            + carrying_gate * 0.20
            + material_gate * 0.14
            + manifestation_gate * 0.18,
        ),
    )
    if metric_core_quality >= 0.0:
        gated_metric_core = metric_core_quality * usability_gate
    else:
        pressure_factor = (
            0.86
            + (1.0 - authority_gate) * 0.12
            + (1.0 - carrying_gate) * 0.12
            + (1.0 - manifestation_gate) * 0.10
            + max(0.0, -stability_quality) * 0.10
        )
        gated_metric_core = max(-1.0, metric_core_quality * pressure_factor)

    if process_quality >= 0.0:
        gated_interaction = process_quality * usability_gate
    else:
        gated_interaction = max(
            -1.0,
            process_quality
            * (0.88 + (1.0 - usability_gate) * 0.28),
        )

    synergy = max(
        0.0,
        min(
            regime_quality,
            metric_core_quality,
            material_quality,
            manifestation_quality,
            max(0.0, gated_interaction),
        ),
    ) * 0.10
    bottleneck_penalty = (
        min(max(0.0, material_quality), max(0.0, -manifestation_quality)) * 0.14
        + min(max(0.0, metric_core_quality), max(0.0, -regime_quality)) * 0.12
        + min(max(0.0, process_quality), max(0.0, -stability_quality)) * 0.08
    )
    # A favorable capacity cannot be sold as fully usable when a required
    # material, palace manifestation, or governing condition is distinctly
    # weak. This is a system bottleneck, not an extra negative signal.
    essential_bottleneck = max(
        0.0,
        -min(
            0.0,
            material_quality,
            manifestation_quality,
            regime_quality,
        ),
    )
    bottleneck_penalty += essential_bottleneck * max(
        0.04,
        min(0.18, 0.08 + max(0.0, metric_core_quality) * 0.10),
    )

    context_rows = [
        row
        for row in family_rows
        if int(row.get("context_source_count", 0)) > 0
    ]
    context_weight = sum(
        float(row.get("context_materiality", 0.0)) for row in context_rows
    ) or 1.0
    context_corroboration = _clip(
        sum(
            float(row.get("context_quality", 0.0))
            * float(row.get("context_materiality", 0.0))
            for row in context_rows
        )
        / context_weight
        if context_rows
        else 0.0
    )
    context_alignment = (
        min(abs(context_corroboration), 0.28)
        * (1.0 if context_corroboration * gated_metric_core >= 0.0 else -0.65)
    )

    net_quality = _clip(
        gated_metric_core * 0.80
        + gated_interaction * 0.04
        + confirming_system[0] * confirming_system[1] * 0.05
        + stability_quality * 0.02
        + evidence_balance_quality * 0.03
        + context_alignment * 0.02
        + regime_quality * 0.04
        + synergy
        - bottleneck_penalty
    )
    return {
        "governance_quality": governance,
        "reality_quality": reality,
        "interaction_quality": interaction,
        "gated_interaction_quality": gated_interaction,
        "context_quality": context,
        "month_quality": month_quality,
        "pattern_quality": pattern_quality,
        "capacity_quality": capacity_quality,
        "climate_quality": climate_quality,
        "useful_role_quality": useful_role_quality,
        "regime_quality": regime_quality,
        "metric_core_quality": metric_core_quality,
        "metric_core_materiality": metric_core_materiality,
        "broad_dimension_quality": broad_dimension_quality,
        "broad_dimension_materiality": broad_dimension_materiality,
        "decisive_system_quality": decisive_system[0],
        "decisive_system_materiality": decisive_system[1],
        "decisive_system_source_count": float(decisive_system[2]),
        "decisive_support_mass": decisive_system[3],
        "decisive_pressure_mass": decisive_system[4],
        "decisive_conflict_ratio": decisive_system[5],
        "confirming_system_quality": confirming_system[0],
        "confirming_system_materiality": confirming_system[1],
        "gate_system_quality": gate_system[0],
        "gate_system_materiality": gate_system[1],
        "active_dimension_count": active_dimension_count,
        "gated_metric_core_quality": gated_metric_core,
        "usability_gate": usability_gate,
        "context_corroboration_quality": context_corroboration,
        "context_alignment_quality": context_alignment,
        "authority_quality": authority_quality,
        "carrying_quality": carrying_quality,
        "material_quality": material_quality,
        "manifestation_quality": manifestation_quality,
        "process_quality": process_quality,
        "stability_quality": stability_quality,
        "evidence_balance_quality": evidence_balance_quality,
        "synergy_quality": synergy,
        "bottleneck_penalty": bottleneck_penalty,
        "essential_bottleneck": essential_bottleneck,
        "governance_gate": governance_gate,
        "month_gate": month_gate,
        "pattern_gate": pattern_gate,
        "capacity_gate": capacity_gate,
        "climate_gate": climate_gate,
        "reality_gate": reality_gate,
        "authority_gate": authority_gate,
        "carrying_gate": carrying_gate,
        "material_gate": material_gate,
        "manifestation_gate": manifestation_gate,
        "net_quality": net_quality,
    }


def _reconcile_adjustment_with_whole_theory(
    adjustment: float,
    theory_score: float,
) -> float:
    """Keep a novel signal from contradicting the whole theory judgment.

    Legacy role, position and relation evidence cannot be added again, but it
    still defines whether a new independent signal confirms the whole chart.
    A near-neutral whole-theory score therefore permits only a small
    refinement; a material adjustment requires the complete evidence stack to
    point in the same direction.
    """

    distance = theory_score - 50.0
    if abs(distance) < 0.05:
        distance = 0.0
    if adjustment > 0.0:
        if distance <= 0.0:
            return min(adjustment, 1.0)
        return min(adjustment, 1.5 + distance * 0.45)
    if adjustment < 0.0:
        if distance >= 0.0:
            return max(adjustment, -1.5)
        return max(adjustment, -(2.0 + abs(distance) * 0.55))
    return 0.0


def evaluate_metric_theory(
    *,
    metric_key: str,
    structure: ChartStructure,
    contract: Any,
    base_score: float,
    legacy_scores: dict[str, float],
) -> dict[str, Any]:
    """Return a source-preserving, gate-aware judgment for one natal metric."""

    requirement = METRIC_THEORY_REQUIREMENTS.get(metric_key)
    if requirement is None:
        return {
            "registry_version": METRIC_THEORY_REGISTRY_VERSION,
            "applied": False,
            "adjustment": 0.0,
        }

    layer_roles = _requirement_layer_roles(requirement)
    raw_evidence: list[TheoryEvidence] = []
    evidence_layers: set[str] = set()
    scored_support_only: list[str] = []
    scored_planned: list[str] = []
    signal_audit: dict[str, dict[str, int]] = {}
    for layer_key, role in layer_roles.items():
        layer = METRIC_THEORY_LAYERS[layer_key]
        items = _layer_evidence(
            layer_key=layer_key,
            structure=structure,
            contract=contract,
            requirement=requirement,
            legacy_scores=legacy_scores,
            layer_role=role,
            signal_audit=signal_audit,
        )
        layer_audit = signal_audit.setdefault(
            layer_key,
            {"observed": 0, "applied": 0, "rejected_no_metric_link": 0},
        )
        if layer_audit["observed"] == 0 and items:
            layer_audit["observed"] = len(items)
            layer_audit["applied"] = len(items)
        if items:
            evidence_layers.add(layer_key)
        if layer.status == "support_only" and items:
            scored_support_only.append(layer_key)
            continue
        if layer.status == "planned" and items:
            scored_planned.append(layer_key)
            continue
        if layer.scoring_role in _NON_SCORING_ROLES:
            continue
        raw_evidence.extend(items)

    unique_evidence = _deduplicate_exact_sources(raw_evidence, layer_roles)
    family_rows, cluster_rows, hierarchy_rows = _build_theory_aggregates(
        unique_evidence,
        layer_roles,
    )
    high_dimensional = _high_dimensional_quality(family_rows, hierarchy_rows)
    all_family_count = len(family_rows)
    cluster_count = len(cluster_rows)
    novel_family_count = sum(
        str(row.get("family")) not in _LEGACY_SCORING_FAMILIES
        for row in family_rows
    )
    coverage_factor = min(
        1.0,
        all_family_count / max(1, requirement.minimum_independent_families),
    )
    # The functional system produces a signed quality in -1..1. A flat linear
    # mapping left clear but moderate convergence visually trapped around 50.
    # This monotonic contrast curve does not rank or normalize people against
    # one another; it only maps the same evidence scale to a readable product
    # scale while preserving zero and order exactly.
    system_contrast_quality = math.tanh(
        float(high_dimensional["net_quality"]) * 2.30
    )
    calibrated_quality = system_contrast_quality * (
        0.76 + coverage_factor * 0.24
    )
    theory_score = 50.0 + calibrated_quality * 46.0

    missing_primary_layers = [
        layer_key
        for layer_key in requirement.primary_layers
        if layer_key in _ABSENCE_SENSITIVE_PRIMARY_LAYERS and layer_key not in evidence_layers
    ]
    missing_deduction = min(4.5, len(missing_primary_layers) * 1.15)
    theory_score -= missing_deduction

    source_ledger: list[dict[str, Any]] = []
    for item in unique_evidence:
        family = _scoring_family(item)
        role = layer_roles.get(item.layer_key, "context")
        if item.quality <= -0.35 and item.materiality >= 0.45:
            evidence_kind = "pressure"
        elif role == "pressure" and item.quality >= 0.25 and item.materiality >= 0.45:
            evidence_kind = "counter"
        elif item.quality >= 0.35 and item.materiality >= 0.45:
            evidence_kind = "support"
        elif item.quality < -0.10:
            evidence_kind = "partial_pressure"
        elif item.quality > 0.10:
            evidence_kind = "partial_support"
        else:
            evidence_kind = "context"
        source_ledger.append(
            {
                "family": family,
                "cluster": _correlation_cluster(family),
                "hierarchy": _hierarchy_for_family(family),
                "layer": item.layer_key,
                "role": role,
                "kind": evidence_kind,
                "quality": round(item.quality, 3),
                "materiality": round(item.materiality, 3),
                "effective_weight": round(_evidence_weight(item, role), 3),
                "critical": bool(
                    item.materiality >= 0.75
                    and abs(item.quality) >= 0.65
                    and role in {"primary", "pressure"}
                ),
                "activated": bool(item.materiality >= 0.45 and abs(item.quality) >= 0.18),
                "source": item.source_key,
                "basis_codes": list(item.basis_codes),
            }
        )
    source_ledger.sort(
        key=lambda item: float(item["effective_weight"])
        * (0.45 + abs(float(item["quality"]))),
        reverse=True,
    )

    sources_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in source_ledger:
        sources_by_family[str(item["family"])].append(item)
    evidence_ledger: list[dict[str, Any]] = []
    for row in family_rows:
        family = str(row["family"])
        sources = sources_by_family.get(family, [])
        quality = float(row.get("quality", 0.0))
        materiality = float(row.get("materiality", 0.0))
        has_counter = any(item["kind"] == "counter" for item in sources)
        if quality <= -0.32 and materiality >= 0.38:
            kind = "pressure"
        elif has_counter and quality >= 0.12:
            kind = "counter"
        elif quality >= 0.32 and materiality >= 0.38:
            kind = "support"
        elif quality < -0.10:
            kind = "partial_pressure"
        elif quality > 0.10:
            kind = "partial_support"
        else:
            kind = "context"
        dominant = sources[0] if sources else {}
        evidence_ledger.append(
            {
                "family": family,
                "cluster": row["cluster"],
                "hierarchy": row["hierarchy"],
                "layer": dominant.get("layer", ""),
                "role": dominant.get("role", "context"),
                "kind": kind,
                "quality": round(quality, 3),
                "materiality": round(materiality, 3),
                "critical": bool(
                    materiality >= 0.70
                    and abs(quality) >= 0.58
                    and str(dominant.get("role", "")) in {"primary", "pressure"}
                ),
                "activated": bool(materiality >= 0.38 and abs(quality) >= 0.16),
                "source": row.get("dominant_source", ""),
                "source_count": int(row.get("source_count", 0)),
                "support_source_count": int(row.get("support_source_count", 0)),
                "pressure_source_count": int(row.get("pressure_source_count", 0)),
            }
        )
    evidence_ledger.sort(
        key=lambda item: float(item["materiality"])
        * (0.45 + abs(float(item["quality"]))),
        reverse=True,
    )

    strong_support_count = sum(
        item["kind"] == "support" for item in evidence_ledger
    )
    strong_pressure_count = sum(
        item["kind"] == "pressure" for item in evidence_ledger
    )
    counter_count = sum(item["kind"] == "counter" for item in evidence_ledger)
    critical_support_count = sum(
        item["kind"] == "support" and item["critical"] for item in evidence_ledger
    )
    critical_pressure_count = sum(
        item["kind"] == "pressure" and item["critical"] for item in evidence_ledger
    )
    activation_count = sum(bool(item["activated"]) for item in source_ledger)

    # Extreme grades need convergence from independent theoretical families.
    # This is an epistemic gate, not a distribution normalizer.
    if theory_score > 80.0 and strong_support_count < 3:
        theory_score = min(theory_score, 79.0)
    if theory_score < 30.0 and strong_pressure_count < 3:
        theory_score = max(theory_score, 30.0)

    raw_adjustment = (theory_score - float(base_score)) * 0.34
    adjustment = _reconcile_adjustment_with_whole_theory(
        max(-14.0, min(10.0, raw_adjustment)),
        theory_score,
    )

    hour_known = "hour" in structure.position_signals and bool(structure.position_signals.get("hour"))
    if getattr(contract, "hour_focus", False) and not hour_known:
        adjustment = min(adjustment, 0.0)

    evidence_summary = [
        {
            key: value
            for key, value in item.items()
            if key in {"family", "layer", "role", "quality", "materiality", "source"}
        }
        for item in evidence_ledger[:6]
    ]
    support_evidence_count = strong_support_count
    pressure_evidence_count = strong_pressure_count
    evidence_strength = (
        sum(abs(float(item["quality"])) * float(item["materiality"]) for item in source_ledger)
        / len(source_ledger)
        * 100.0
        if source_ledger
        else 0.0
    )

    family_ledger = [
        {
            key: (
                round(value, 3)
                if isinstance(value, float)
                else value
            )
            for key, value in row.items()
        }
        for row in family_rows
    ]
    family_ledger.sort(
        key=lambda item: float(item.get("materiality", 0.0))
        * (0.45 + abs(float(item.get("quality", 0.0)))),
        reverse=True,
    )
    cluster_ledger = [
        {
            key: round(value, 3) if isinstance(value, float) else value
            for key, value in row.items()
        }
        for row in cluster_rows
    ]
    hierarchy_ledger = [
        {
            key: round(value, 3) if isinstance(value, float) else value
            for key, value in row.items()
        }
        for row in hierarchy_rows
    ]
    observed_signal_count = sum(
        int(item.get("observed", 0)) for item in signal_audit.values()
    )
    applicable_signal_count = sum(
        int(item.get("applied", 0)) for item in signal_audit.values()
    )
    rejected_signal_count = sum(
        int(item.get("rejected_no_metric_link", 0))
        for item in signal_audit.values()
    )
    signal_treatment_ledger = [
        {
            "layer": layer_key,
            "role": layer_roles.get(layer_key, "context"),
            "observed": int(item.get("observed", 0)),
            "applied": int(item.get("applied", 0)),
            "rejected_no_metric_link": int(item.get("rejected_no_metric_link", 0)),
        }
        for layer_key, item in signal_audit.items()
        if int(item.get("observed", 0)) > 0
    ]
    signal_treatment_ledger.sort(
        key=lambda item: (int(item["applied"]), int(item["observed"])),
        reverse=True,
    )

    return {
        "registry_version": METRIC_THEORY_REGISTRY_VERSION,
        "applied": True,
        "semantic_axis": requirement.semantic_axis,
        "theory_score": round(max(12.0, min(96.0, theory_score)), 2),
        "high_dimensional_score": round(max(12.0, min(96.0, theory_score)), 2),
        "high_dimensional_quality": {
            key: round(value, 3) for key, value in high_dimensional.items()
        },
        "system_contrast_quality": round(system_contrast_quality, 3),
        "adjustment": round(max(-14.0, min(10.0, adjustment)), 2),
        "raw_evidence_count": len(raw_evidence),
        "retained_source_count": len(unique_evidence),
        "source_retention_ratio": round(
            len(unique_evidence) / len(raw_evidence) if raw_evidence else 1.0,
            3,
        ),
        "observed_signal_count": observed_signal_count,
        "applicable_signal_count": applicable_signal_count,
        "rejected_signal_count": rejected_signal_count,
        "signal_application_ratio": round(
            applicable_signal_count / observed_signal_count
            if observed_signal_count
            else 1.0,
            3,
        ),
        "independent_family_count": all_family_count,
        "correlation_cluster_count": cluster_count,
        "novel_family_count": novel_family_count,
        "minimum_independent_families": requirement.minimum_independent_families,
        "coverage_ratio": round(coverage_factor, 3),
        "strong_support_count": strong_support_count,
        "strong_pressure_count": strong_pressure_count,
        "support_evidence_count": support_evidence_count,
        "pressure_evidence_count": pressure_evidence_count,
        "counter_count": counter_count,
        "critical_support_count": critical_support_count,
        "critical_pressure_count": critical_pressure_count,
        "activation_count": activation_count,
        "evidence_strength": round(evidence_strength, 2),
        "missing_primary_layers": missing_primary_layers,
        "support_only_scored": sorted(set(scored_support_only)),
        "planned_scored": sorted(set(scored_planned)),
        "evidence_summary": evidence_summary,
        "evidence_ledger": evidence_ledger,
        "source_evidence_ledger": source_ledger,
        "family_ledger": family_ledger,
        "cluster_ledger": cluster_ledger,
        "hierarchy_ledger": hierarchy_ledger,
        "signal_treatment_ledger": signal_treatment_ledger,
    }
