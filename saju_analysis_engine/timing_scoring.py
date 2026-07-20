"""Shared scoring rules for selecting notable flow years.

The four annual domain axes have different semantics. Opportunity and risk
describe direction, while probability describes how strongly either direction
is likely to become an event. Keep this distinction here so engine payloads and
the web report cannot drift into different year rankings.
"""

from __future__ import annotations

from typing import Any, Mapping

from .relation_polarity import relation_effective_friction

CONNECTIVE_RELATIONS = {
    "six_combine",
    "three_harmony",
    "three_harmony_half",
    "three_meeting",
}


def _number(parts: Mapping[str, Any], key: str) -> float:
    try:
        return float(parts.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def timing_base_score(parts: Mapping[str, Any], kind: str) -> float:
    """Return the direction score before structural activation modifiers.

    Probability is event manifestation, not favorability. It therefore raises
    confidence in both a favorable and a cautionary selection. Opportunity is
    not subtracted from caution because mixed years can carry a real gain and a
    real loss mechanism at the same time.
    """

    opportunity = _number(parts, "opportunity")
    probability = _number(parts, "probability")
    change = _number(parts, "change")
    risk = _number(parts, "risk")
    if kind == "good":
        return round(
            opportunity * 0.43
            + probability * 0.36
            + change * 0.12
            - risk * 0.18,
            4,
        )
    if kind == "caution":
        return round(
            risk * 0.62
            + probability * 0.22
            + change * 0.16,
            4,
        )
    raise ValueError(f"Unsupported timing score kind: {kind}")


def _event_relation_hits(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    preferred = context.get("event_relation_hits")
    if isinstance(preferred, list):
        source = preferred
    else:
        source = []
        for key in ("relation_hits", "daeun_annual_relation_hits"):
            items = context.get(key)
            if isinstance(items, list):
                source.extend(items)

    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for item in source:
        if not isinstance(item, dict):
            continue
        relation_type = str(item.get("relation_type") or "")
        basis_code = str(item.get("basis_code") or "")
        positions = tuple(str(value) for value in list(item.get("positions") or []))
        key = (relation_type, basis_code, positions)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def timing_activation_modifier(context: Mapping[str, Any] | None, kind: str) -> float:
    """Score how strongly natal, daeun and annual signals activate together."""

    if not isinstance(context, Mapping):
        return 0.0
    compound = context.get("compound_direction")
    compound = compound if isinstance(compound, Mapping) else {}
    grade = str(compound.get("grade") or "")
    useful = int(context.get("useful_hit_count") or 0)
    caution = int(context.get("caution_hit_count") or 0)
    phase = int(context.get("phase_hit_count") or 0)
    relation_hits = _event_relation_hits(context)
    pressure_weight = 0.0
    for item in relation_hits:
        effective_friction = item.get("effective_friction")
        try:
            effective_friction = float(effective_friction)
        except (TypeError, ValueError):
            effective_friction = relation_effective_friction(
                str(item.get("relation_type") or ""),
                str(item.get("polarity") or "mixed"),
                str(item.get("intensity") or "moderate"),
            )
        # 2.6 preserves the former punishment ceiling while the shared
        # relation contract now retains a smaller, non-zero cost for a useful
        # clash, punishment, harm, or break.
        pressure_weight += max(0.0, effective_friction) * 2.6
    supportive_combine_count = sum(
        1
        for item in relation_hits
        if str(item.get("relation_type") or "") in CONNECTIVE_RELATIONS
        and str(item.get("polarity") or "mixed") == "supportive"
    )

    if kind == "good":
        score = {
            "daeun_supports_annual_support": 4.0,
            "daeun_burden_annual_support": 1.8,
            "daeun_annual_mixed": -1.0,
            "daeun_supports_annual_burden": -3.5,
            "daeun_burden_annual_burden": -6.0,
        }.get(grade, 0.0)
        score += min(4.0, useful * 1.2)
        score -= min(4.5, caution * 1.5)
        if phase and useful >= caution:
            score += min(3.5, phase * 1.5)
        elif phase and caution > useful:
            score -= min(3.5, phase * 1.2)
        if pressure_weight:
            score -= min(4.5, pressure_weight)
        if supportive_combine_count and useful > caution:
            score += min(2.5, supportive_combine_count * 1.0)
        return round(score, 2)

    if kind != "caution":
        raise ValueError(f"Unsupported timing modifier kind: {kind}")
    score = {
        "daeun_supports_annual_support": 0.0,
        "daeun_supports_annual_burden": 3.0,
        "daeun_burden_annual_support": 1.5,
        "daeun_burden_annual_burden": 5.0,
        "daeun_annual_mixed": 2.0,
    }.get(grade, 0.0)
    score += min(5.0, caution * 1.5)
    if phase and caution >= useful:
        score += min(4.0, phase * 1.4)
    if pressure_weight:
        score += min(5.0, pressure_weight)
    return round(score, 2)


def event_relation_hits(context: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Expose the normalized event relations for UI evidence labels."""

    if not isinstance(context, Mapping):
        return []
    return _event_relation_hits(context)
