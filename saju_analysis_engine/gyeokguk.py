"""Gyeokguk judgment layer.

This layer keeps the older broad pattern profile intact and adds a stricter
month-command profile. It treats the month branch as the gate of public
conditions, then separates main command, active hidden phase, protrusion, and
rooting before downstream product layers turn the result into customer copy.
"""

from __future__ import annotations

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .models import (
    BranchInteraction,
    Confidence,
    ElementProfile,
    GyeokgukCandidate,
    GyeokgukProfile,
    MonthGovernanceProfile,
    MonthHiddenPhaseProfile,
    PatternProfile,
    PositionSignal,
    TenGodProfile,
)
from .patterns import REGULAR_PATTERN_BY_TEN_GOD, REGULAR_PATTERN_NEED_RULES
from .gyeokguk_dual_ten_god_actions import build_gyeokguk_dual_ten_god_action_matches
from .gyeokguk_ten_god_actions import build_gyeokguk_ten_god_action_matches
from .ten_gods import ten_god_for


GYEOKGUK_PROFILE_VERSION = "gyeokguk_profile_v1"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _confidence(score: int) -> Confidence:
    if score >= 82:
        return "high"
    if score >= 70:
        return "medium_high"
    if score >= 55:
        return "medium"
    if score >= 42:
        return "low"
    return "restricted"


def _role_element(day_element: str, group: str) -> str:
    if group == "peer":
        return day_element
    if group == "resource":
        return ELEMENT_GENERATED_BY[day_element]
    if group == "output":
        return ELEMENT_GENERATES[day_element]
    if group == "wealth":
        return ELEMENT_CONTROLS[day_element]
    if group == "officer":
        return ELEMENT_CONTROLLED_BY[day_element]
    return ""


def _visible_positions(position_signals: dict[str, PositionSignal], stem_key: str) -> list[str]:
    return [
        signal.position
        for signal in position_signals.values()
        if signal.stem_key == stem_key
    ]


def _root_positions(position_signals: dict[str, PositionSignal], stem_key: str) -> list[str]:
    exact: list[str] = []
    element: list[str] = []
    stem_element = STEM_METADATA[stem_key]["element"]
    for signal in position_signals.values():
        hidden_stems = [item for item, _ in BRANCH_HIDDEN_STEMS.get(signal.branch_key, [])]
        if stem_key in hidden_stems:
            exact.append(signal.position)
            continue
        if any(STEM_METADATA[item]["element"] == stem_element for item in hidden_stems):
            element.append(f"{signal.position}:same_element")
    return _unique(exact + element)


def _candidate_role_rules(ten_god: str, day_element: str) -> tuple[list[str], list[str], list[str], list[str]]:
    rules = REGULAR_PATTERN_NEED_RULES.get(ten_god, {})
    support_roles = [str(item[0]) for item in rules.get("support", ())]
    burden_roles = [str(item[0]) for item in rules.get("caution", ())]
    favorable_elements = [_role_element(day_element, group) for group in support_roles]
    unfavorable_elements = [_role_element(day_element, group) for group in burden_roles]
    return (
        _unique(support_roles),
        _unique(burden_roles),
        _unique(favorable_elements),
        _unique(unfavorable_elements),
    )


def _month_authority(
    *,
    is_main: bool,
    is_active: bool,
    is_protruded: bool,
) -> str:
    if is_main and is_active and is_protruded:
        return "main_active_protruded_command"
    if is_main and is_protruded:
        return "main_protruded_command"
    if is_main and is_active:
        return "main_active_command"
    if is_main:
        return "main_month_command"
    if is_active and is_protruded:
        return "active_protruded_command"
    if is_active:
        return "active_hidden_command"
    if is_protruded:
        return "protruded_hidden_command"
    return "latent_month_hidden"


def _clarity_state(
    *,
    score: int,
    protruded: bool,
    rooted: bool,
    support_score: int,
    pressure_score: int,
    support_roles: list[str],
    burden_roles: list[str],
) -> str:
    # Role catalogs describe what can help or burden a pattern. They are not
    # evidence that both actions are present in this chart.
    del support_roles, burden_roles
    if pressure_score >= max(4, support_score + 4):
        return "clouded_by_month_pressure"
    if score >= 78 and protruded and rooted and support_score >= pressure_score:
        return "clear_and_rooted"
    if support_score > 0 and pressure_score > 0 and abs(support_score - pressure_score) <= 3:
        return "mixed_success_and_pressure"
    if protruded and rooted:
        return "formed_but_needs_refinement"
    if rooted and not protruded:
        return "rooted_but_hidden"
    if protruded and not rooted:
        return "visible_but_unrooted"
    return "latent_or_fragmented"


def _formation_state(clarity_state: str, score: int) -> str:
    if clarity_state == "clear_and_rooted":
        return "properly_formed"
    if clarity_state in {"formed_but_needs_refinement", "mixed_success_and_pressure"}:
        return "formed_with_conditions"
    if clarity_state in {"rooted_but_hidden", "visible_but_unrooted"}:
        return "partially_formed"
    if score >= 55:
        return "latent_but_usable"
    return "weak_or_fragmented"


def _source_priority(source_tags: list[str]) -> str:
    if "main" in source_tags and "active" in source_tags and "protruded" in source_tags:
        return "main_active_protruded"
    if "main" in source_tags and "protruded" in source_tags:
        return "main_protruded"
    if "main" in source_tags:
        return "main_command"
    if "active" in source_tags and "protruded" in source_tags:
        return "active_protruded"
    if "active" in source_tags:
        return "active_command"
    if "protruded" in source_tags:
        return "protruded_hidden"
    return "hidden_secondary"


def _candidate_score(
    *,
    hidden_weight: float,
    source_tags: list[str],
    group_score: float,
    protruded: bool,
    rooted: bool,
    visible_positions: list[str],
    role_support_score: int,
    role_pressure_score: int,
    useful_group: bool,
    caution_group: bool,
) -> int:
    score = 34 + round(hidden_weight * 22)
    if "main" in source_tags:
        score += 16
    if "active" in source_tags:
        score += 10
    if protruded:
        score += 12
    if rooted:
        score += 7
    if "month" in visible_positions:
        score += 8
    elif visible_positions:
        score += 5
    score += min(14, round(group_score * 5))
    score += min(12, role_support_score * 2)
    if useful_group:
        score += 6
    if caution_group:
        score -= 5
    if role_pressure_score >= role_support_score + 4:
        score -= 8
    return max(24, min(98, score))


def _hidden_sources(
    *,
    month_branch: str,
    month_hidden_phase: MonthHiddenPhaseProfile | None,
    protruded_hidden_stems: list[str],
) -> dict[str, dict[str, object]]:
    sources: dict[str, dict[str, object]] = {}
    for index, (stem_key, weight) in enumerate(BRANCH_HIDDEN_STEMS.get(month_branch, [])):
        tags = ["main"] if index == 0 else ["hidden"]
        if stem_key in protruded_hidden_stems:
            tags.append("protruded")
        sources[stem_key] = {
            "stem": stem_key,
            "weight": float(weight),
            "phase": "",
            "tags": tags,
        }

    if month_hidden_phase and month_hidden_phase.active_stem:
        active = sources.setdefault(
            month_hidden_phase.active_stem,
            {
                "stem": month_hidden_phase.active_stem,
                "weight": 0.0,
                "phase": "",
                "tags": ["hidden"],
            },
        )
        active["phase"] = month_hidden_phase.active_phase
        active_tags = list(active.get("tags", []) or [])
        active_tags.append("active")
        if month_hidden_phase.active_stem in protruded_hidden_stems:
            active_tags.append("protruded")
        active["tags"] = _unique([str(item) for item in active_tags])
    return sources


def _build_candidate(
    *,
    source: dict[str, object],
    day_master_stem: str,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    month_governance_profile: MonthGovernanceProfile,
) -> GyeokgukCandidate:
    stem_key = str(source["stem"])
    hidden_weight = float(source.get("weight") or 0.0)
    source_tags = [str(item) for item in list(source.get("tags", []) or [])]
    source_element = STEM_METADATA[stem_key]["element"]
    ten_god = ten_god_for(day_master_stem, stem_key)
    source_group = TEN_GOD_GROUPS.get(ten_god, "")
    pattern = REGULAR_PATTERN_BY_TEN_GOD.get(ten_god, f"{ten_god}_month_command")
    protrusion_positions = _visible_positions(position_signals, stem_key)
    root_positions = _root_positions(position_signals, stem_key)
    protruded = bool(protrusion_positions)
    rooted = bool(root_positions)
    support_roles, burden_roles, favorable_elements, unfavorable_elements = _candidate_role_rules(
        ten_god,
        element_profile.day_master_element,
    )
    role_fit = month_governance_profile.role_fits.get(source_group)
    role_support_score = int(getattr(role_fit, "support_score", 0) or 0)
    role_pressure_score = int(getattr(role_fit, "pressure_score", 0) or 0)
    group_score = float(ten_god_profile.group_scores.get(source_group, 0.0) or 0.0)
    score = _candidate_score(
        hidden_weight=hidden_weight,
        source_tags=source_tags,
        group_score=group_score,
        protruded=protruded,
        rooted=rooted,
        visible_positions=protrusion_positions,
        role_support_score=role_support_score,
        role_pressure_score=role_pressure_score,
        useful_group=source_group in month_governance_profile.useful_groups,
        caution_group=source_group in month_governance_profile.caution_groups,
    )
    is_main = "main" in source_tags
    is_active = "active" in source_tags
    month_authority = _month_authority(
        is_main=is_main,
        is_active=is_active,
        is_protruded=protruded,
    )
    clarity_state = _clarity_state(
        score=score,
        protruded=protruded,
        rooted=rooted,
        support_score=role_support_score,
        pressure_score=role_pressure_score,
        support_roles=support_roles,
        burden_roles=burden_roles,
    )
    formation_state = _formation_state(clarity_state, score)

    basis_codes = [
        f"gyeokguk_month_branch_{month_governance_profile.month_branch}",
        f"gyeokguk_source_stem_{stem_key}",
        f"gyeokguk_source_ten_god_{ten_god}",
        f"gyeokguk_source_group_{source_group}",
        f"gyeokguk_month_authority_{month_authority}",
    ]
    if is_main:
        basis_codes.append("gyeokguk_main_hidden_stem")
    if is_active:
        basis_codes.append(f"gyeokguk_active_hidden_phase_{source.get('phase', '')}")
    if protruded:
        basis_codes.append("gyeokguk_hidden_stem_protruded")
    if rooted:
        basis_codes.append("gyeokguk_source_stem_rooted")
    if source_group in month_governance_profile.useful_groups:
        basis_codes.append(f"gyeokguk_group_useful_by_month_{source_group}")

    counter_signals: list[str] = []
    if not protruded:
        counter_signals.append("gyeokguk_not_protruded")
    if not rooted:
        counter_signals.append("gyeokguk_not_rooted")
    if source_group in month_governance_profile.caution_groups:
        counter_signals.append(f"gyeokguk_group_caution_by_month_{source_group}")
    if role_fit:
        counter_signals.extend(list(role_fit.counter_signals))

    return GyeokgukCandidate(
        pattern=pattern,
        source_ten_god=ten_god,
        source_group=source_group,
        source_stem=stem_key,
        source_element=source_element,
        source_weight=hidden_weight,
        source_priority=_source_priority(source_tags),
        source_phase=str(source.get("phase", "") or ""),
        protruded=protruded,
        protrusion_positions=protrusion_positions,
        rooted=rooted,
        root_positions=root_positions,
        month_authority=month_authority,
        clarity_state=clarity_state,
        formation_state=formation_state,
        support_roles=support_roles,
        burden_roles=burden_roles,
        favorable_elements=favorable_elements,
        unfavorable_elements=unfavorable_elements,
        score=score,
        confidence=_confidence(score),
        basis_codes=_unique(basis_codes),
        counter_signals=_unique(counter_signals),
    )


def _success_conditions(candidate: GyeokgukCandidate) -> list[str]:
    conditions = [
        f"pattern_source:{candidate.source_priority}",
        f"month_authority:{candidate.month_authority}",
    ]
    if candidate.protruded:
        conditions.append("hidden_command_visible_in_heavenly_stem")
    if candidate.rooted:
        conditions.append("source_stem_has_branch_root")
    conditions.extend(f"support_role:{group}" for group in candidate.support_roles[:3])
    conditions.extend(f"favorable_element:{element}" for element in candidate.favorable_elements[:3])
    return _unique(conditions)


def _failure_conditions(candidate: GyeokgukCandidate) -> list[str]:
    conditions: list[str] = []
    if not candidate.protruded:
        conditions.append("hidden_command_not_protruded")
    if not candidate.rooted:
        conditions.append("source_stem_without_root")
    conditions.extend(f"burden_role:{group}" for group in candidate.burden_roles[:3])
    conditions.extend(f"unfavorable_element:{element}" for element in candidate.unfavorable_elements[:3])
    conditions.extend(candidate.counter_signals[:5])
    return _unique(conditions)


def build_gyeokguk_profile(
    *,
    day_master_stem: str,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    pattern_profile: PatternProfile,
    month_governance_profile: MonthGovernanceProfile,
    branch_interactions: list[BranchInteraction] | None = None,
    month_hidden_phase: MonthHiddenPhaseProfile | None = None,
) -> GyeokgukProfile:
    month_branch = element_profile.month_branch
    protruded_hidden_stems = list(month_governance_profile.protruded_hidden_stems)
    sources = _hidden_sources(
        month_branch=month_branch,
        month_hidden_phase=month_hidden_phase,
        protruded_hidden_stems=protruded_hidden_stems,
    )
    candidates = [
        _build_candidate(
            source=source,
            day_master_stem=day_master_stem,
            element_profile=element_profile,
            ten_god_profile=ten_god_profile,
            position_signals=position_signals,
            month_governance_profile=month_governance_profile,
        )
        for source in sources.values()
    ]
    candidates.sort(
        key=lambda item: (
            item.score,
            item.protruded,
            item.rooted,
            item.source_weight,
        ),
        reverse=True,
    )
    primary = candidates[0] if candidates else None
    if primary is None:
        return GyeokgukProfile(
            primary_pattern="",
            primary_ten_god="",
            primary_group="",
            family="",
            formation_state="undetermined",
            clarity_state="undetermined",
            candidates=[],
            month_branch=month_branch,
            month_command_stem="",
            month_command_ten_god=pattern_profile.month_command_ten_god,
            active_hidden_stem=getattr(month_hidden_phase, "active_stem", "") if month_hidden_phase else "",
            active_hidden_ten_god=getattr(month_hidden_phase, "active_ten_god", "") if month_hidden_phase else "",
            protruded_month_stems=protruded_hidden_stems,
            favorable_elements=[],
            unfavorable_elements=[],
            success_conditions=[],
            failure_conditions=[],
            ten_god_action_matches=[],
            dual_ten_god_action_matches=[],
            basis_codes=[f"gyeokguk_month_branch_{month_branch}", "gyeokguk_no_candidate"],
            decision_notes=["gyeokguk:no_month_hidden_candidate"],
            rule_version=GYEOKGUK_PROFILE_VERSION,
        )

    month_command_stem = BRANCH_HIDDEN_STEMS.get(month_branch, [("", 0.0)])[0][0]
    notes = [
        f"month_branch:{month_branch}",
        f"month_command_stem:{month_command_stem}",
        f"month_command_ten_god:{pattern_profile.month_command_ten_god}",
        f"primary_pattern:{primary.pattern}",
        f"formation:{primary.formation_state}",
        f"clarity:{primary.clarity_state}",
    ]
    active_stem = getattr(month_hidden_phase, "active_stem", "") if month_hidden_phase else ""
    active_ten_god = getattr(month_hidden_phase, "active_ten_god", "") if month_hidden_phase else ""
    if active_stem:
        notes.append(f"active_hidden_stem:{active_stem}")
    if protruded_hidden_stems:
        notes.append("month_hidden_stem_protruded")
    ten_god_action_matches = build_gyeokguk_ten_god_action_matches(
        pattern=primary.pattern,
        ten_god_profile=ten_god_profile,
        month_governance_profile=month_governance_profile,
        element_profile=element_profile,
        position_signals=position_signals,
        branch_interactions=branch_interactions,
    )
    dual_ten_god_action_matches = build_gyeokguk_dual_ten_god_action_matches(
        pattern=primary.pattern,
        ten_god_profile=ten_god_profile,
        month_governance_profile=month_governance_profile,
        element_profile=element_profile,
        position_signals=position_signals,
        branch_interactions=branch_interactions,
    )

    return GyeokgukProfile(
        primary_pattern=primary.pattern,
        primary_ten_god=primary.source_ten_god,
        primary_group=primary.source_group,
        family=primary.source_group,
        formation_state=primary.formation_state,
        clarity_state=primary.clarity_state,
        candidates=candidates,
        month_branch=month_branch,
        month_command_stem=month_command_stem,
        month_command_ten_god=pattern_profile.month_command_ten_god,
        active_hidden_stem=active_stem,
        active_hidden_ten_god=active_ten_god,
        protruded_month_stems=protruded_hidden_stems,
        favorable_elements=primary.favorable_elements,
        unfavorable_elements=primary.unfavorable_elements,
        success_conditions=_success_conditions(primary),
        failure_conditions=_failure_conditions(primary),
        ten_god_action_matches=ten_god_action_matches,
        dual_ten_god_action_matches=dual_ten_god_action_matches,
        basis_codes=_unique(
            [
                f"gyeokguk_month_branch_{month_branch}",
                f"gyeokguk_month_command_stem_{month_command_stem}",
                f"gyeokguk_primary_{primary.pattern}",
                *primary.basis_codes,
            ]
        ),
        decision_notes=_unique(notes),
        rule_version=GYEOKGUK_PROFILE_VERSION,
    )
