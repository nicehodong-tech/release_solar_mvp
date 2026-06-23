"""Life-feature axis scoring for customer-facing interpretation."""

from __future__ import annotations

from .constants import ELEMENT_CONTROLLED_BY, ELEMENT_CONTROLS, ELEMENT_GENERATED_BY, ELEMENT_GENERATES
from .models import (
    AuxiliaryProfile,
    BranchInteraction,
    ElementProfile,
    IntegratedSajuProfile,
    LifeFeatureProfile,
    LifeFeatureScore,
    MonthGovernanceProfile,
    PatternProfile,
    PositionSignal,
    StemReceptionProfile,
    TenGodProfile,
)


def _clip(value: float) -> int:
    return max(0, min(100, round(value)))


def _group(profile: TenGodProfile, key: str) -> float:
    return float(profile.group_scores.get(key, 0.0))


def _ten_god(profile: TenGodProfile, key: str) -> float:
    return float(profile.visible_counts.get(key, 0.0)) + float(profile.hidden_counts.get(key, 0.0)) * 0.7


def _position_has(position_signals: dict[str, PositionSignal], position: str, domain: str) -> bool:
    return domain in position_signals[position].domains


def _interaction_count(interactions: list[BranchInteraction], relation_types: set[str], position: str | None = None) -> int:
    count = 0
    for item in interactions:
        if item.relation_type not in relation_types:
            continue
        if position is not None and position not in item.positions:
            continue
        count += 1
    return count


def _circulation_bonus(profile: ElementProfile) -> int:
    return {
        "smooth": 8,
        "usable": 5,
        "partial": 1,
        "blocked": -6,
    }.get(profile.circulation_level, 0)


def _strength_bonus(profile: ElementProfile) -> int:
    return round((profile.day_master_strength_score - 50) * 0.25)


def _element_quality(profile: ElementProfile, element: str) -> int:
    score = profile.scores[element]
    state_bonus = {
        "dominant": 6,
        "strong": 4,
        "balanced": 2,
        "weak": -2,
        "absent": -6,
    }.get(score.state, 0)
    exposure_bonus = {
        "clear": 3,
        "present": 2,
        "hidden": 0,
        "absent": -3,
    }.get(score.exposure, 0)
    role_fit_bonus = 0
    if element in profile.useful_elements:
        role_fit_bonus += 2
    if element in profile.caution_elements:
        role_fit_bonus -= 2
    return state_bonus + exposure_bonus + role_fit_bonus


def _element_basis(profile: ElementProfile, role: str, element: str) -> list[str]:
    score = profile.scores[element]
    basis: list[str] = []
    if score.exposure in {"clear", "present"}:
        basis.append(f"feature_element_{role}_visible")
    if score.state in {"balanced", "strong", "dominant"}:
        basis.append(f"feature_element_{role}_usable")
    if element in profile.useful_elements:
        basis.append(f"feature_element_{role}_useful")
    return basis


def _element_counters(profile: ElementProfile, role: str, element: str, *, dominant_load: bool = False) -> list[str]:
    score = profile.scores[element]
    counters: list[str] = []
    if score.state in {"weak", "absent"}:
        counters.append(f"feature_element_{role}_weak")
    if dominant_load and score.state == "dominant":
        counters.append(f"feature_element_{role}_dominant_load")
    if element in profile.caution_elements:
        counters.append(f"feature_element_{role}_caution")
    return counters


def _candidate_score_for_element(candidates: list[object], element: str) -> int:
    scores = [
        int(getattr(candidate, "score", 0) or 0)
        for candidate in candidates
        if str(getattr(candidate, "element", "")) == element
    ]
    return max(scores, default=0)


def _pattern_element_delta(pattern_profile: PatternProfile, element: str) -> int:
    support_score = _candidate_score_for_element(list(pattern_profile.useful_element_candidates), element)
    pressure_score = _candidate_score_for_element(list(pattern_profile.caution_element_candidates), element)
    support_delta = 3 if support_score >= 76 else 2 if support_score >= 62 else 1 if support_score else 0
    pressure_delta = 3 if pressure_score >= 76 else 2 if pressure_score >= 62 else 1 if pressure_score else 0
    return support_delta - pressure_delta


def _pattern_element_basis(pattern_profile: PatternProfile, role: str, element: str) -> list[str]:
    if _candidate_score_for_element(list(pattern_profile.useful_element_candidates), element):
        return [f"feature_pattern_useful_{role}"]
    return []


def _pattern_element_counters(pattern_profile: PatternProfile, role: str, element: str) -> list[str]:
    if _candidate_score_for_element(list(pattern_profile.caution_element_candidates), element):
        return [f"feature_pattern_caution_{role}"]
    return []


DOMAIN_AXIS_LINKS = {
    "money": (
        "money_potential",
        "income_expansion",
        "liquidity_stability",
        "reward_claim_strength",
        "asset_retention",
        "ownership_clarity",
        "shared_asset_boundary",
        "spending_control",
        "investment_trading_sense",
        "deal_selection",
        "loss_avoidance",
        "late_life_money_growth",
        "business_expansion",
        "money_attitude",
    ),
    "career": (
        "social_success_potential",
        "career_achievement",
        "work_domain_fit",
        "honor_recognition",
        "promotion_visibility",
        "responsibility_capacity",
        "role_authority_alignment",
        "organization_adaptability",
        "academic_expertise",
        "reputation_maintenance",
    ),
    "love": (
        "interpersonal_influence",
        "attraction_selectivity",
        "relationship_progression",
        "affection_expression",
        "affection_receptivity",
        "emotional_alignment",
        "relationship_stability",
        "communication_expression",
        "boundary_management",
        "misunderstanding_prevention",
        "conflict_recovery",
        "reunion_closure",
    ),
    "marriage": (
        "marriage_stability",
        "spouse_match_quality",
        "spouse_support_benefit",
        "marriage_timing_readiness",
        "household_stability",
        "household_finance_alignment",
        "relationship_stability",
        "family_responsibility",
        "inlaw_boundary_strength",
        "marriage_crisis_management",
        "practical_planning",
        "asset_retention",
        "conflict_recovery",
    ),
    "personality": (
        "self_direction",
        "decision_consistency",
        "change_adaptability",
        "practical_planning",
        "communication_expression",
        "boundary_management",
        "conflict_recovery",
        "crisis_recovery",
        "leadership_potential",
    ),
    "honor": (
        "honor_recognition",
        "promotion_visibility",
        "reputation_maintenance",
        "responsibility_capacity",
        "role_authority_alignment",
        "social_success_potential",
        "career_achievement",
        "organization_adaptability",
        "academic_expertise",
    ),
    "social": (
        "interpersonal_influence",
        "relationship_stability",
        "communication_expression",
        "boundary_management",
        "conflict_recovery",
        "leadership_potential",
        "reputation_maintenance",
        "shared_asset_boundary",
        "family_responsibility",
    ),
    "life": (
        "self_direction",
        "decision_consistency",
        "change_adaptability",
        "crisis_recovery",
        "practical_planning",
        "asset_retention",
        "late_life_money_growth",
        "household_stability",
        "family_responsibility",
        "career_achievement",
        "reputation_maintenance",
    ),
    "life_period": (
        "self_direction",
        "decision_consistency",
        "change_adaptability",
        "crisis_recovery",
        "practical_planning",
        "asset_retention",
        "late_life_money_growth",
        "household_stability",
        "family_responsibility",
        "career_achievement",
        "reputation_maintenance",
    ),
    "timing": (
        "change_adaptability",
        "crisis_recovery",
        "career_achievement",
        "money_potential",
        "income_expansion",
        "asset_retention",
        "relationship_stability",
        "marriage_stability",
        "responsibility_capacity",
        "loss_avoidance",
        "practical_planning",
    ),
}

TEN_GOD_AXIS_LINKS = {
    "bi_gyeon": ("self_direction", "leadership_potential", "relationship_stability", "money_attitude", "household_stability", "shared_asset_boundary"),
    "geob_jae": ("self_direction", "business_expansion", "spending_control", "asset_retention", "shared_asset_boundary", "ownership_clarity"),
    "sik_sin": ("income_expansion", "liquidity_stability", "career_achievement", "communication_expression", "practical_planning", "affection_expression", "relationship_progression", "reward_claim_strength"),
    "sang_gwan": ("communication_expression", "business_expansion", "organization_adaptability", "reputation_maintenance", "affection_expression", "misunderstanding_prevention"),
    "pyeon_jae": ("money_potential", "business_expansion", "investment_trading_sense", "interpersonal_influence", "attraction_selectivity", "spouse_match_quality", "liquidity_stability"),
    "jeong_jae": ("income_expansion", "asset_retention", "ownership_clarity", "spending_control", "practical_planning", "attraction_selectivity", "spouse_match_quality", "household_stability", "household_finance_alignment"),
    "pyeon_gwan": ("responsibility_capacity", "role_authority_alignment", "crisis_recovery", "career_achievement", "marriage_stability", "marriage_timing_readiness", "spouse_match_quality", "marriage_crisis_management"),
    "jeong_gwan": ("honor_recognition", "promotion_visibility", "organization_adaptability", "responsibility_capacity", "role_authority_alignment", "marriage_stability", "marriage_timing_readiness", "spouse_match_quality", "spouse_support_benefit"),
    "pyeon_in": ("academic_expertise", "decision_consistency", "change_adaptability", "crisis_recovery"),
    "jeong_in": ("academic_expertise", "practical_planning", "asset_retention", "conflict_recovery"),
}

RECEPTION_COUNTER_HEAVY_TEN_GODS = {"geob_jae", "sang_gwan", "pyeon_gwan", "pyeon_in"}

CYCLE_GROUP_AXIS_LINKS = {
    "peer": ("self_direction", "leadership_potential", "relationship_stability", "money_attitude", "asset_retention", "shared_asset_boundary"),
    "output": ("income_expansion", "liquidity_stability", "career_achievement", "communication_expression", "business_expansion", "affection_expression", "relationship_progression", "reward_claim_strength"),
    "wealth": ("money_potential", "income_expansion", "liquidity_stability", "asset_retention", "ownership_clarity", "deal_selection", "investment_trading_sense", "attraction_selectivity", "spouse_match_quality", "household_finance_alignment"),
    "officer": ("honor_recognition", "promotion_visibility", "organization_adaptability", "responsibility_capacity", "role_authority_alignment", "marriage_stability", "marriage_timing_readiness", "spouse_match_quality", "spouse_support_benefit"),
    "resource": ("academic_expertise", "decision_consistency", "practical_planning", "conflict_recovery", "household_stability", "misunderstanding_prevention", "emotional_alignment"),
}

CYCLE_SIGNAL_AXIS_LINKS = {
    "wealth_generates_officer_controls_peer": (
        "deal_selection",
        "loss_avoidance",
        "ownership_clarity",
        "shared_asset_boundary",
        "responsibility_capacity",
        "reputation_maintenance",
        "boundary_management",
    ),
    "wealth_controls_resource_releases_output": (
        "decision_consistency",
        "practical_planning",
        "communication_expression",
        "income_expansion",
        "reward_claim_strength",
    ),
    "output_controls_officer_reduces_pressure": (
        "responsibility_capacity",
        "career_achievement",
        "crisis_recovery",
    ),
    "officer_generates_resource_protects_body": (
        "honor_recognition",
        "organization_adaptability",
        "academic_expertise",
        "crisis_recovery",
    ),
    "output_generates_wealth_then_officer": (
        "income_expansion",
        "money_potential",
        "career_achievement",
        "honor_recognition",
        "reward_claim_strength",
        "relationship_progression",
        "marriage_timing_readiness",
    ),
    "resource_controls_output_dosik": (
        "communication_expression",
        "career_achievement",
        "decision_consistency",
        "change_adaptability",
    ),
    "generates_output_to_wealth": ("income_expansion", "liquidity_stability", "money_potential", "business_expansion", "career_achievement", "relationship_progression", "reward_claim_strength"),
    "generates_wealth_to_officer": ("deal_selection", "ownership_clarity", "responsibility_capacity", "honor_recognition", "promotion_visibility", "marriage_timing_readiness", "role_authority_alignment"),
    "generates_officer_to_resource": ("organization_adaptability", "academic_expertise", "crisis_recovery", "household_stability", "spouse_support_benefit", "marriage_crisis_management"),
    "generates_resource_to_peer": ("decision_consistency", "self_direction", "conflict_recovery"),
    "generates_peer_to_output": ("communication_expression", "career_achievement", "self_direction"),
    "controls_peer_to_wealth": ("asset_retention", "spending_control", "deal_selection", "business_expansion", "shared_asset_boundary", "ownership_clarity"),
    "controls_wealth_to_resource": ("practical_planning", "academic_expertise", "decision_consistency", "investment_trading_sense", "misunderstanding_prevention"),
    "controls_resource_to_output": ("communication_expression", "career_achievement", "decision_consistency", "affection_expression", "misunderstanding_prevention"),
    "controls_output_to_officer": ("responsibility_capacity", "organization_adaptability", "reputation_maintenance", "role_authority_alignment"),
    "controls_officer_to_peer": ("self_direction", "responsibility_capacity", "leadership_potential", "shared_asset_boundary", "inlaw_boundary_strength"),
}


def _adjustment_bucket() -> dict[str, object]:
    return {"score": 0.0, "basis_codes": [], "counter_signals": []}


def _add_axis_adjustment(
    adjustments: dict[str, dict[str, object]],
    axis_key: str,
    *,
    score: float = 0.0,
    basis_codes: list[str] | None = None,
    counter_signals: list[str] | None = None,
) -> None:
    bucket = adjustments.setdefault(axis_key, _adjustment_bucket())
    bucket["score"] = float(bucket["score"]) + score
    if basis_codes:
        bucket_basis = bucket["basis_codes"]
        assert isinstance(bucket_basis, list)
        bucket_basis.extend(basis_codes)
    if counter_signals:
        bucket_counters = bucket["counter_signals"]
        assert isinstance(bucket_counters, list)
        bucket_counters.extend(counter_signals)


def _signal_strength_delta(strength: str, priority_score: int) -> float:
    base = {"high": 3.0, "moderate": 2.0, "low": 1.0}.get(strength, 1.0)
    if priority_score >= 70:
        return base + 1.0
    if priority_score >= 45:
        return base + 0.5
    return base


def _axis_keys_for_domain_and_ten_god(domain_links: list[str], ten_gods: list[str]) -> list[str]:
    keys: list[str] = []
    for domain in domain_links:
        keys.extend(DOMAIN_AXIS_LINKS.get(domain, ()))
    for ten_god in ten_gods:
        keys.extend(TEN_GOD_AXIS_LINKS.get(ten_god, ()))
    return list(dict.fromkeys(keys))


def _reception_axis_adjustments(
    stem_reception_profile: StemReceptionProfile | None,
    integrated_saju_profile: IntegratedSajuProfile | None,
    axis_keys: set[str],
) -> dict[str, dict[str, object]]:
    adjustments: dict[str, dict[str, object]] = {}
    if stem_reception_profile is not None:
        top_ids = set(stem_reception_profile.top_signal_ids)
        reception_signals = (
            list(stem_reception_profile.visible_stem_signals)
            + list(stem_reception_profile.branch_main_signals)
            + list(stem_reception_profile.hidden_stem_signals)
        )
        for signal in reception_signals:
            if signal.signal_id not in top_ids:
                continue
            score_delta = _signal_strength_delta(signal.strength, signal.priority_score) * 0.45
            counter_delta = 0.0
            if signal.counter_signals:
                counter_delta += 0.8
            if signal.branch_relation_score_modifier:
                counter_delta += min(1.2, signal.branch_relation_score_modifier * 2)
            axes = _axis_keys_for_domain_and_ten_god(signal.domain_links, [signal.target_ten_god])
            for axis_key in axes:
                if axis_key not in axis_keys:
                    continue
                basis_code = f"feature_stem_reception_{axis_key}_{signal.day_stem}_{signal.target_stem}_{signal.target_ten_god}"
                counter_codes: list[str] = []
                if signal.target_ten_god in RECEPTION_COUNTER_HEAVY_TEN_GODS and signal.counter_signals:
                    counter_codes.append(
                        f"feature_stem_reception_counter_{axis_key}_{signal.target_stem}_{signal.target_ten_god}"
                    )
                if signal.branch_relation_score_modifier and any(
                    item in {"clash", "punishment", "self_punishment", "break", "harm"}
                    for item in signal.branch_relation_modifiers
                ):
                    counter_codes.append(f"feature_stem_reception_branch_load_{axis_key}")
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=score_delta - counter_delta,
                    basis_codes=[basis_code],
                    counter_signals=counter_codes,
                )
    if integrated_saju_profile is not None:
        top_ids = set(integrated_saju_profile.top_signal_ids)
        integrated_signals = (
            list(integrated_saju_profile.visible_pair_signals)
            + list(integrated_saju_profile.stem_branch_pair_signals)
            + list(integrated_saju_profile.hidden_pair_signals)
        )
        for signal in integrated_signals:
            if signal.signal_id not in top_ids:
                continue
            score_delta = _signal_strength_delta(signal.strength, signal.priority_score) * 0.35
            counter_delta = 0.0
            if signal.counter_signals:
                counter_delta += 0.7
            if signal.branch_relation_score_modifier:
                counter_delta += min(1.0, signal.branch_relation_score_modifier * 1.7)
            axes = _axis_keys_for_domain_and_ten_god(
                signal.domain_links,
                [signal.source_ten_god, signal.target_ten_god],
            )
            for axis_key in axes:
                if axis_key not in axis_keys:
                    continue
                basis_code = (
                    f"feature_integrated_saju_{axis_key}_{signal.source_stem}_{signal.target_stem}_"
                    f"{signal.source_ten_god}_to_{signal.target_ten_god}"
                )
                counter_codes: list[str] = []
                if signal.counter_signals:
                    counter_codes.append(
                        f"feature_integrated_saju_counter_{axis_key}_{signal.source_ten_god}_to_{signal.target_ten_god}"
                    )
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=score_delta - counter_delta,
                    basis_codes=[basis_code],
                    counter_signals=counter_codes,
                )
    return adjustments


def _apply_reception_axis_adjustments(
    axes: list[LifeFeatureScore],
    stem_reception_profile: StemReceptionProfile | None,
    integrated_saju_profile: IntegratedSajuProfile | None,
) -> list[LifeFeatureScore]:
    axis_keys = {axis.key for axis in axes}
    adjustments = _reception_axis_adjustments(stem_reception_profile, integrated_saju_profile, axis_keys)
    adjusted: list[LifeFeatureScore] = []
    for axis in axes:
        adjustment = adjustments.get(axis.key)
        if not adjustment:
            adjusted.append(axis)
            continue
        basis_codes = adjustment["basis_codes"]
        counter_signals = adjustment["counter_signals"]
        assert isinstance(basis_codes, list)
        assert isinstance(counter_signals, list)
        adjusted.append(
            _axis(
                axis.key,
                axis.category,
                axis.label,
                axis.score + float(adjustment["score"]),
                list(axis.basis_codes) + [str(code) for code in basis_codes],
                list(axis.counter_signals) + [str(code) for code in counter_signals],
            )
        )
    return adjusted


def _cycle_axis_keys(signal: dict[str, object], axis_keys: set[str]) -> list[str]:
    signal_id = str(signal.get("signal_id") or "")
    keys: list[str] = list(CYCLE_SIGNAL_AXIS_LINKS.get(signal_id, ()))
    if str(signal.get("relation") or "") == "stem_combine" and "money" in {
        str(domain) for domain in list(signal.get("domain_links") or []) if str(domain)
    }:
        keys.append("money_potential")
    if str(signal.get("relation") or "") == "branch_cycle":
        for group in list(signal.get("activated_groups") or []):
            keys.extend(CYCLE_GROUP_AXIS_LINKS.get(str(group), ()))
    if str(signal.get("relation") or "") == "stem_combine":
        transform_group = str(signal.get("transform_group") or "")
        keys.extend(CYCLE_GROUP_AXIS_LINKS.get(transform_group, ()))
        for group in list(signal.get("original_groups") or []):
            keys.extend(CYCLE_GROUP_AXIS_LINKS.get(str(group), ()))
    for group_key in ("source_group", "target_group"):
        group = str(signal.get(group_key) or "")
        keys.extend(CYCLE_GROUP_AXIS_LINKS.get(group, ()))
    for group in list(signal.get("groups") or []):
        keys.extend(CYCLE_GROUP_AXIS_LINKS.get(str(group), ()))
    for group in list(signal.get("activated_groups") or []):
        keys.extend(CYCLE_GROUP_AXIS_LINKS.get(str(group), ()))
    for domain in list(signal.get("domain_links") or []):
        keys.extend(DOMAIN_AXIS_LINKS.get(str(domain), ()))
    return [key for key in dict.fromkeys(keys) if key in axis_keys]


def _cycle_axis_delta(signal: dict[str, object]) -> float:
    score = int(signal.get("score") or 0)
    reality = int(signal.get("reality_score") or 0)
    base = 1.1 + min(2.7, max(0.0, (score - 48) / 18)) + min(1.4, reality / 18)
    polarity = str(signal.get("polarity") or "mixed")
    judgment = str(signal.get("cycle_judgment") or "")
    governance = dict(signal.get("governance_context") or {})
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    condition = dict(signal.get("condition_context") or {})
    branch_reality = dict(signal.get("branch_reality_context") or {})
    bonus = 0.0
    cost = 0.0
    if governance.get("touches_month_command"):
        bonus += 0.15
    if governance.get("touches_useful"):
        bonus += 0.25
    if governance.get("touches_caution"):
        cost += 0.3
    support_strength = float(pattern_cycle.get("support_strength") or 0.0)
    caution_strength = float(pattern_cycle.get("caution_strength") or 0.0)
    if support_strength:
        bonus += min(0.85, 0.22 * support_strength)
    if caution_strength:
        cost += min(0.95, 0.25 * caution_strength)
    condition_verdict = str(condition.get("verdict") or "")
    if condition_verdict == "condition_supports_cycle":
        bonus += 0.45
    elif condition_verdict == "condition_support_with_cost":
        bonus += 0.3
        cost += 0.35
    elif condition_verdict == "condition_mixed_cycle":
        bonus += 0.2
        cost += 0.55
    elif condition_verdict == "condition_pressure_with_use":
        bonus += 0.15
        cost += 0.75
    elif condition_verdict == "condition_pressures_cycle":
        cost += 0.95
    if condition.get("pressure_tags"):
        cost += min(0.45, 0.15 * len(list(condition.get("pressure_tags") or [])))
    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade in {"month_branch_visible", "month_hidden_protruded"}:
        if polarity == "support":
            bonus += 0.55
        elif polarity == "pressure":
            cost += 0.65
        else:
            bonus += 0.25
            cost += 0.35
    elif branch_grade in {"branch_dominant", "hidden_to_visible"}:
        if polarity == "support":
            bonus += 0.4
        elif polarity == "pressure":
            cost += 0.5
        else:
            bonus += 0.2
            cost += 0.25
    elif branch_grade == "branch_rooted":
        if polarity == "support":
            bonus += 0.22
        elif polarity == "pressure":
            cost += 0.28
    if polarity == "support":
        return min(5.6, max(0.4, base + bonus - cost * 0.45))
    if polarity == "pressure":
        penalty = min(5.4, base + (0.8 if judgment in {"wealth_competition", "damaging_control"} else 0.0))
        return -min(5.9, max(0.6, penalty + cost - bonus * 0.35))
    return max(-2.2, min(2.4, base * 0.35 + bonus * 0.45 - cost * 0.5))


def _cycle_signal_salience(signal: dict[str, object]) -> float:
    score = float(signal.get("score") or 0)
    reality = float(signal.get("reality_score") or 0)
    salience = score * 0.65 + reality * 1.35
    relation = str(signal.get("relation") or "")
    polarity = str(signal.get("polarity") or "mixed")
    governance = dict(signal.get("governance_context") or {})
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    condition = dict(signal.get("condition_context") or {})
    branch_reality = dict(signal.get("branch_reality_context") or {})

    if relation == "chain":
        salience += 14
    elif relation in {"hidden_protrusion", "visible_root", "branch_cycle"}:
        salience += 11
    elif relation in {"stem_combine", "element_exception"}:
        salience += 8
    elif relation == "element_bridge":
        salience += 6

    if polarity == "pressure":
        salience += 10
    elif polarity == "mixed":
        salience += 5

    if governance.get("touches_month_command"):
        salience += 9
    if governance.get("touches_useful"):
        salience += 6
    if governance.get("touches_caution"):
        salience += 8
    if pattern_cycle.get("support_rule_keys"):
        salience += min(14, 3 * len(list(pattern_cycle.get("support_rule_keys") or [])))
    if pattern_cycle.get("caution_rule_keys"):
        salience += min(16, 4 * len(list(pattern_cycle.get("caution_rule_keys") or [])))
    if condition.get("pressure_tags"):
        salience += min(12, 3 * len(list(condition.get("pressure_tags") or [])))
    if condition.get("support_tags"):
        salience += min(8, 2 * len(list(condition.get("support_tags") or [])))
    if str(branch_reality.get("grade") or "") in {
        "month_branch_visible",
        "month_hidden_protruded",
        "branch_dominant",
        "hidden_to_visible",
        "branch_rooted",
    }:
        salience += 8
    return salience


def _sorted_cycle_signals(signals: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        signals,
        key=lambda signal: (
            -_cycle_signal_salience(signal),
            str(signal.get("relation") or ""),
            str(signal.get("signal_id") or ""),
        ),
    )


def _select_cycle_axis_signals(
    raw_signals: list[dict[str, object]],
    axis_keys: set[str],
) -> list[dict[str, object]]:
    buckets: dict[str, list[dict[str, object]]] = {
        "chain": [],
        "ten_god_edge": [],
        "element_edge": [],
        "bridge": [],
        "exception": [],
        "branch": [],
        "stem_combine": [],
        "rooting": [],
        "domain_relevant": [],
    }
    for signal in raw_signals:
        if not _cycle_axis_keys(signal, axis_keys):
            continue
        relation = str(signal.get("relation") or "")
        if relation == "chain":
            buckets["chain"].append(signal)
        elif relation in {"generates", "controls"}:
            buckets["ten_god_edge"].append(signal)
        elif relation in {"element_generates", "element_controls"}:
            buckets["element_edge"].append(signal)
        elif relation == "element_bridge":
            buckets["bridge"].append(signal)
        elif relation == "element_exception":
            buckets["exception"].append(signal)
        elif relation == "branch_cycle":
            buckets["branch"].append(signal)
        elif relation == "stem_combine":
            buckets["stem_combine"].append(signal)
        elif relation in {"hidden_protrusion", "visible_root"}:
            buckets["rooting"].append(signal)
        if signal.get("domain_links"):
            buckets["domain_relevant"].append(signal)

    selected: list[dict[str, object]] = []
    quotas = {
        "chain": 10,
        "ten_god_edge": 12,
        "element_edge": 12,
        "bridge": 8,
        "exception": 10,
        "branch": 12,
        "stem_combine": 10,
        "rooting": 16,
        "domain_relevant": 14,
    }
    for name, quota in quotas.items():
        selected.extend(_sorted_cycle_signals(buckets[name])[:quota])
        selected.extend(
            _sorted_cycle_signals([signal for signal in buckets[name] if signal.get("polarity") == "pressure"])[:6]
        )

    selected.extend(_sorted_cycle_signals(raw_signals)[:16])
    deduped = list({str(signal.get("signal_id") or ""): signal for signal in selected if signal.get("signal_id")}.values())
    return _sorted_cycle_signals(deduped)[:64]


def _cycle_axis_context_codes(signal: dict[str, object]) -> tuple[list[str], list[str]]:
    signal_id = str(signal.get("signal_id") or "")
    governance = dict(signal.get("governance_context") or {})
    pattern_cycle = dict(signal.get("pattern_cycle_context") or {})
    condition = dict(signal.get("condition_context") or {})
    branch_reality = dict(signal.get("branch_reality_context") or {})
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    if governance.get("touches_month_command"):
        basis_codes.append(f"feature_cycle_governance_month_command_{signal_id}")
    if governance.get("touches_useful"):
        basis_codes.append(f"feature_cycle_governance_useful_{signal_id}")
    if governance.get("touches_caution"):
        counter_signals.append(f"feature_cycle_governance_caution_{signal_id}")
    if pattern_cycle.get("support_rule_keys"):
        strength = min(9, int(round(float(pattern_cycle.get("support_strength") or 0))))
        grade = str(pattern_cycle.get("reality_grade") or "unknown")
        basis_codes.append(f"feature_cycle_pattern_support_{signal_id}_{grade}_{strength}")
    if pattern_cycle.get("caution_rule_keys"):
        strength = min(9, int(round(float(pattern_cycle.get("caution_strength") or 0))))
        grade = str(pattern_cycle.get("reality_grade") or "unknown")
        counter_signals.append(f"feature_cycle_pattern_caution_{signal_id}_{grade}_{strength}")
    condition_verdict = str(condition.get("verdict") or "")
    if condition.get("support_tags"):
        basis_codes.append(f"feature_cycle_condition_support_{signal_id}_{condition_verdict}")
    if condition.get("pressure_tags"):
        counter_signals.append(f"feature_cycle_condition_counter_{signal_id}_{condition_verdict}")
    branch_grade = str(branch_reality.get("grade") or "")
    if branch_grade:
        branch_ratio = min(9, int(round(float(branch_reality.get("branch_ratio") or 0.0) * 10)))
        code = f"feature_cycle_branch_reality_{signal_id}_{branch_grade}_{branch_ratio}"
        polarity = str(signal.get("polarity") or "mixed")
        if polarity in {"support", "mixed"}:
            basis_codes.append(code)
        if polarity in {"pressure", "mixed"}:
            counter_signals.append(f"{code}_cost")
    return list(dict.fromkeys(basis_codes)), list(dict.fromkeys(counter_signals))


def _cycle_axis_primary_context_codes(
    signal: dict[str, object],
    basis_codes: list[str],
    counter_signals: list[str],
) -> tuple[list[str], list[str]]:
    """Keep only the decisive context codes for a feature axis.

    Cycle regulation can carry month command, useful/caution, pattern, condition,
    and branch-reality context at once. Those details matter, but sending all of
    them into every product axis makes the final judgment look unfocused.
    """

    polarity = str(signal.get("polarity") or "mixed")
    if polarity == "pressure":
        return basis_codes[:1], counter_signals[:2]
    if polarity == "mixed":
        return basis_codes[:2], counter_signals[:1]
    return basis_codes[:2], counter_signals[:1]


def _cycle_regulation_axis_adjustments(
    cycle_regulation_profile: dict[str, object] | None,
    axis_keys: set[str],
) -> dict[str, dict[str, object]]:
    adjustments: dict[str, dict[str, object]] = {}
    if not cycle_regulation_profile:
        return adjustments
    raw_signals = [signal for signal in list(cycle_regulation_profile.get("signals") or []) if isinstance(signal, dict)]
    signals = _select_cycle_axis_signals(raw_signals, axis_keys)
    axis_signal_candidates: dict[str, list[dict[str, object]]] = {}
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        signal_id = str(signal.get("signal_id") or "")
        if not signal_id:
            continue
        delta = _cycle_axis_delta(signal)
        axis_candidates = _cycle_axis_keys(signal, axis_keys)
        if not axis_candidates:
            continue
        basis_code = f"feature_cycle_regulation_{signal_id}_{signal.get('cycle_judgment', '')}"
        counter_code = f"feature_cycle_regulation_counter_{signal_id}_{signal.get('cycle_judgment', '')}"
        context_basis_codes, context_counter_signals = _cycle_axis_context_codes(signal)
        polarity = str(signal.get("polarity") or "mixed")
        candidate_limit = (
            8
            if str(signal.get("relation") or "") in {"branch_cycle", "stem_combine", "hidden_protrusion", "visible_root"}
            else 4
        )
        direct_axis_keys = set(CYCLE_SIGNAL_AXIS_LINKS.get(signal_id, ()))
        for axis_index, axis_key in enumerate(axis_candidates[:candidate_limit]):
            priority = _cycle_signal_salience(signal) - axis_index * 7
            if axis_key in direct_axis_keys:
                priority += 18
            if str(signal.get("relation") or "") == "chain":
                priority += 10
            if polarity == "pressure":
                priority += 6
            axis_signal_candidates.setdefault(axis_key, []).append(
                {
                    "priority": priority,
                    "delta": delta,
                    "polarity": polarity,
                    "basis_code": basis_code,
                    "counter_code": counter_code,
                    "context_basis_codes": context_basis_codes,
                    "context_counter_signals": context_counter_signals,
                }
            )

    for axis_key, candidates in axis_signal_candidates.items():
        ranked = sorted(candidates, key=lambda item: -float(item["priority"]))
        pressure = [item for item in ranked if item["polarity"] == "pressure"][:3]
        support = [item for item in ranked if item["polarity"] == "support"][:3]
        mixed = [item for item in ranked if item["polarity"] == "mixed"][:2]
        selected: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for item in [*ranked[:6], *pressure, *support, *mixed]:
            code_key = str(item.get("basis_code") or item.get("counter_code") or item.get("priority"))
            if code_key in seen_ids:
                continue
            selected.append(item)
            seen_ids.add(code_key)
            if len(selected) >= 9:
                break
        for order, item in enumerate(selected):
            polarity = str(item["polarity"])
            weight = 1.0 if order < 4 else 0.65 if order < 8 else 0.4
            delta = float(item["delta"]) * weight
            basis_code = str(item["basis_code"])
            counter_code = str(item["counter_code"])
            context_basis_codes = [str(code) for code in list(item["context_basis_codes"] or [])]
            context_counter_signals = [str(code) for code in list(item["context_counter_signals"] or [])]
            context_basis_codes, context_counter_signals = _cycle_axis_primary_context_codes(
                {"polarity": polarity},
                context_basis_codes,
                context_counter_signals,
            )
            if polarity == "pressure":
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=delta,
                    basis_codes=context_basis_codes,
                    counter_signals=[counter_code, *context_counter_signals],
                )
            elif polarity == "mixed":
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=delta,
                    basis_codes=[basis_code, *context_basis_codes],
                    counter_signals=[counter_code, *context_counter_signals],
                )
            else:
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=delta,
                    basis_codes=[basis_code, *context_basis_codes],
                    counter_signals=context_counter_signals,
                )
    return adjustments


def _apply_cycle_regulation_axis_adjustments(
    axes: list[LifeFeatureScore],
    cycle_regulation_profile: dict[str, object] | None,
) -> list[LifeFeatureScore]:
    axis_keys = {axis.key for axis in axes}
    adjustments = _cycle_regulation_axis_adjustments(cycle_regulation_profile, axis_keys)
    adjusted: list[LifeFeatureScore] = []
    for axis in axes:
        adjustment = adjustments.get(axis.key)
        if not adjustment:
            adjusted.append(axis)
            continue
        basis_codes = adjustment["basis_codes"]
        counter_signals = adjustment["counter_signals"]
        assert isinstance(basis_codes, list)
        assert isinstance(counter_signals, list)
        adjusted.append(
            _axis(
                axis.key,
                axis.category,
                axis.label,
                axis.score + float(adjustment["score"]),
                list(axis.basis_codes) + [str(code) for code in basis_codes],
                list(axis.counter_signals) + [str(code) for code in counter_signals],
            )
        )
    return adjusted


def _month_governance_delta(status: str, support_score: int, pressure_score: int) -> float:
    status_delta = {
        "supports_month_command": 2.1,
        "usable_by_month_command": 1.25,
        "mixed_by_month_command": 0.25,
        "neutral_to_month_command": 0.0,
        "burdensome_by_month_command": -1.25,
        "harms_month_command": -2.2,
    }.get(status, 0.0)
    score_delta = max(-2.4, min(2.4, (support_score - pressure_score) * 0.28))
    return status_delta + score_delta


def _month_governance_axis_adjustments(
    month_governance_profile: MonthGovernanceProfile | None,
    axis_keys: set[str],
) -> dict[str, dict[str, object]]:
    adjustments: dict[str, dict[str, object]] = {}
    if month_governance_profile is None:
        return adjustments
    for group, fit in month_governance_profile.role_fits.items():
        role_axes = [key for key in CYCLE_GROUP_AXIS_LINKS.get(group, ()) if key in axis_keys]
        if not role_axes:
            continue
        delta = _month_governance_delta(fit.status, fit.support_score, fit.pressure_score)
        basis_codes = [
            f"feature_month_governance_role_{group}_{fit.status}",
            f"feature_month_governance_role_element_{group}_{fit.element}",
            *fit.basis_codes,
        ]
        counter_codes = [
            f"feature_month_governance_role_counter_{group}_{fit.status}",
            *fit.counter_signals,
        ]
        for axis_key in role_axes:
            if delta >= 0:
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=delta,
                    basis_codes=basis_codes,
                    counter_signals=counter_codes if fit.pressure_score > fit.support_score else [],
                )
            else:
                _add_axis_adjustment(
                    adjustments,
                    axis_key,
                    score=delta,
                    basis_codes=basis_codes if fit.support_score else [],
                    counter_signals=counter_codes,
                )

    for domain, focus_groups in month_governance_profile.domain_focus_groups.items():
        domain_axes = [key for key in DOMAIN_AXIS_LINKS.get(domain, ()) if key in axis_keys]
        if not domain_axes:
            continue
        focus_delta = 0.0
        basis_codes: list[str] = []
        counter_codes: list[str] = []
        for group in focus_groups:
            fit = month_governance_profile.role_fits.get(group)
            if fit is None:
                continue
            group_delta = _month_governance_delta(fit.status, fit.support_score, fit.pressure_score) * 0.18
            focus_delta += group_delta
            if group_delta >= 0:
                basis_codes.append(f"feature_month_governance_domain_{domain}_{group}_{fit.status}")
            else:
                counter_codes.append(f"feature_month_governance_domain_counter_{domain}_{group}_{fit.status}")
        if not focus_delta and not basis_codes and not counter_codes:
            continue
        for axis_key in domain_axes[:8]:
            _add_axis_adjustment(
                adjustments,
                axis_key,
                score=max(-1.8, min(1.8, focus_delta)),
                basis_codes=basis_codes,
                counter_signals=counter_codes,
            )
    return adjustments


def _apply_month_governance_axis_adjustments(
    axes: list[LifeFeatureScore],
    month_governance_profile: MonthGovernanceProfile | None,
) -> list[LifeFeatureScore]:
    axis_keys = {axis.key for axis in axes}
    adjustments = _month_governance_axis_adjustments(month_governance_profile, axis_keys)
    adjusted: list[LifeFeatureScore] = []
    for axis in axes:
        adjustment = adjustments.get(axis.key)
        if not adjustment:
            adjusted.append(axis)
            continue
        basis_codes = adjustment["basis_codes"]
        counter_signals = adjustment["counter_signals"]
        assert isinstance(basis_codes, list)
        assert isinstance(counter_signals, list)
        adjusted.append(
            _axis(
                axis.key,
                axis.category,
                axis.label,
                axis.score + float(adjustment["score"]),
                list(axis.basis_codes) + [str(code) for code in basis_codes],
                list(axis.counter_signals) + [str(code) for code in counter_signals],
            )
        )
    return adjusted


def _percentile_label(score: int) -> str:
    if score >= 88:
        return "상위 10% 안팎"
    if score >= 80:
        return "상위 15% 안팎"
    if score >= 72:
        return "상위 25% 안팎"
    if score >= 64:
        return "상위 35% 안팎"
    if score >= 56:
        return "상위 45% 안팎"
    if score >= 48:
        return "평균권"
    if score >= 40:
        return "평균권 하단"
    return "주의 필요 구간"


def _strength_label(score: int) -> str:
    if score >= 78:
        return "강하게 발달한 편"
    if score >= 64:
        return "평균보다 우세한 편"
    if score >= 52:
        return "보통 이상"
    if score >= 42:
        return "관리가 필요한 편"
    return "약하게 작동하는 편"


def _confidence(score: int, basis_count: int, counter_count: int) -> str:
    adjusted = score + min(8, basis_count * 2) - min(10, counter_count * 3)
    if adjusted >= 78 and basis_count >= 2:
        return "high"
    if adjusted >= 66:
        return "medium_high"
    if adjusted >= 52:
        return "medium"
    if adjusted >= 40:
        return "low"
    return "restricted"


def _category_phrase(category: str) -> str:
    return {
        "money": "돈을 벌고 지키는 방식",
        "social": "사회적 역할과 평가를 얻는 방식",
        "personality": "성향과 행동을 조절하는 방식",
    }[category]


def _axis_phrase(label: str, category: str) -> str:
    return {
        "재물 잠재력": "돈이 되는 기회를 고르고 재물 규모를 키우는 방식",
        "수입 확대력": "수입원과 보상 기준을 늘리는 방식",
        "자산 유지력": "벌어들인 돈을 자산으로 남기는 방식",
        "지출 통제력": "지출 기준과 생활비를 관리하는 방식",
        "투자와 거래 감각": "투자, 거래, 제안의 조건을 읽는 방식",
        "돈을 대하는 태도": "돈을 쓰고 모으며 위험을 바라보는 방식",
        "좋은 제안을 고르는 힘": "계약, 제안, 수익 조건을 비교하는 방식",
        "손실 방어력": "손실 가능성과 지출 위험을 미리 줄이는 방식",
        "후반 재물 성장성": "시간이 지날수록 돈과 자산을 쌓아 가는 방식",
        "사회적 성공 잠재력": "사회에서 역할과 성과를 인정받는 방식",
        "명예운": "공식 평가를 안정적으로 얻는 방식",
        "직업적 성취력": "직업에서 성과와 책임을 쌓는 방식",
        "리더십 잠재력": "사람과 일을 이끌며 책임을 맡는 방식",
        "대인 영향력": "대인 관계에서 설득과 존재감을 만드는 방식",
        "연애 선별력": "끌리는 사람을 고르고 관계의 기준을 세우는 방식",
        "관계 진전력": "호감이 실제 만남과 관계로 이어지는 방식",
        "애정 표현성": "마음을 말과 행동으로 전하는 방식",
        "사업 확장력": "사업, 거래, 외부 제안을 넓히는 방식",
        "학문·전문성 성취력": "학문, 자격, 전문성을 깊게 쌓는 방식",
        "조직 적응력": "조직 안에서 역할과 규칙에 맞추는 방식",
        "평판 유지력": "사회적 평판과 신뢰를 오래 지키는 방식",
        "책임 감당력": "일과 사람 앞에서 책임 범위를 안정적으로 다루는 방식",
        "자기 주도성": "스스로 방향을 정하고 일을 밀고 가는 방식",
        "결정 지속성": "선택을 유지하고 결정을 번복하지 않는 방식",
        "표현 전달력": "생각과 감정을 상대에게 전달하는 방식",
        "관계 경계 설정력": "거리감과 책임 범위를 정하는 방식",
        "현실 설계력": "돈과 일의 조건을 현실적으로 정리하는 방식",
        "변화 적응력": "새 조건에 맞추어 행동을 조정하는 방식",
        "관계 안정성": "관계의 온도와 거리를 안정시키는 방식",
        "결혼 안정성": "생활 조건과 책임 범위를 맞추는 방식",
        "배우자상": "오래 맞는 배우자 조건을 알아보는 방식",
        "혼인 성향": "결혼 논의를 약속과 일정으로 옮기는 방식",
        "가정 안정력": "생활비와 가족 책임을 안정시키는 방식",
        "가족 책임감": "가족과 가까운 사람 앞에서 책임을 행동으로 지는 방식",
        "갈등 회복력": "관계 갈등 뒤 감정과 행동을 다시 정리하는 방식",
        "위기 회복력": "문제가 생긴 뒤 다시 정리하는 방식",
    }.get(label, _category_phrase(category))


def _has_final_consonant(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    code = ord(stripped[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _object_particle(text: str) -> str:
    return "을" if _has_final_consonant(text) else "를"


def _customer_sentence(label: str, category: str, score: int) -> str:
    phrase = _axis_phrase(label, category)
    phrase_object = f"{phrase}{_object_particle(phrase)}"
    if label == "자산 유지력":
        if score >= 70:
            return "당신의 자산 유지력은 강한 편입니다. 수입이 생긴 뒤에도 돈을 오래 붙잡아 자산으로 키웁니다."
        if score >= 52:
            return "당신의 자산 유지력은 평균권보다 안정적입니다. 수입이 생기면 남길 돈을 먼저 떼어 둘 때 자산이 쌓입니다."
        if score >= 46:
            return "당신의 자산 유지력은 평균권에 가깝습니다. 지출 순서를 먼저 정해야 벌어들인 돈이 자산으로 남습니다."
        return "당신의 자산 유지력은 초반에는 흔들리기 쉽습니다. 들어온 돈을 바로 쓰지 않고 남길 금액부터 정해야 합니다."
    if label == "사회적 성공 잠재력":
        if score >= 80:
            return "당신의 사회적 성공 잠재력은 매우 강합니다. 공식 책임과 성과가 사회적 평판으로 커집니다."
        if score >= 70:
            return "당신의 사회적 성공 잠재력은 강한 편입니다. 맡은 역할이 분명할수록 사회적 평가가 좋아집니다."
        if score >= 56:
            return "당신의 사회적 성공 잠재력은 좋은 편입니다. 사회에서 맡을 역할을 분명히 할수록 평가가 안정됩니다."
        if score >= 46:
            return "당신의 사회적 성공 잠재력은 평균권에 가깝습니다. 역할과 책임을 분명히 해야 사회적 평가가 흔들리지 않습니다."
        return "당신의 사회적 성공 잠재력은 초반에는 크게 드러나지 않습니다. 맡을 역할을 좁고 분명하게 잡아야 평가가 안정됩니다."
    if label == "연애 선별력":
        if score >= 70:
            return "당신의 연애 선별력은 강합니다. 호감이 생겨도 오래 맞을 사람인지 먼저 가립니다."
        if score >= 56:
            return "당신의 연애 선별력은 좋은 편입니다. 상대의 태도와 생활 기준을 보고 마음을 정합니다."
        if score >= 46:
            return "당신의 연애 선별력은 평균권입니다. 끌림이 커질수록 상대의 말과 행동을 따로 확인해야 합니다."
        return "당신의 연애 선별력은 초반에 흔들리기 쉽습니다. 감정이 앞서면 맞지 않는 사람에게도 오래 끌릴 수 있습니다."
    if label == "관계 진전력":
        if score >= 70:
            return "당신의 관계 진전력은 강합니다. 호감이 생기면 만남과 연락이 빠르게 현실화됩니다."
        if score >= 56:
            return "당신의 관계 진전력은 좋은 편입니다. 접점이 생기면 관계가 자연스럽게 가까워집니다."
        if score >= 46:
            return "당신의 관계 진전력은 평균권입니다. 만남이 생겨도 다음 약속으로 옮기는 힘을 따로 써야 합니다."
        return "당신의 관계 진전력은 초반에 약합니다. 마음은 있어도 관계가 실제 만남으로 늦게 옮겨질 수 있습니다."
    if label == "애정 표현성":
        if score >= 70:
            return "당신의 애정 표현성은 강합니다. 마음이 생기면 말과 행동에서 호감이 분명히 드러납니다."
        if score >= 56:
            return "당신의 애정 표현성은 좋은 편입니다. 상대가 당신의 호감을 비교적 빨리 알아차립니다."
        if score >= 46:
            return "당신의 애정 표현성은 평균권입니다. 마음이 있어도 표현 방식이 일정하지 않으면 상대가 헷갈릴 수 있습니다."
        return "당신의 애정 표현성은 늦게 드러납니다. 좋아하는 마음이 있어도 상대에게 확신을 주기까지 시간이 걸립니다."
    if label == "배우자상":
        if score >= 70:
            return "당신의 배우자상은 분명합니다. 오래 맞을 사람을 고르는 기준이 비교적 뚜렷합니다."
        if score >= 56:
            return "당신의 배우자상은 좋은 편입니다. 성격보다 생활 태도가 맞는 사람과 안정됩니다."
        if score >= 46:
            return "당신의 배우자상은 아직 흔들림이 있습니다. 좋아하는 마음과 생활 기준을 따로 확인해야 합니다."
        return "당신의 배우자상은 초반에 흔들리기 쉽습니다. 감정이 깊어도 생활 조건이 맞지 않으면 부담이 오래 갑니다."
    if label == "혼인 성향":
        if score >= 70:
            return "당신의 혼인 성향은 분명합니다. 결혼 이야기가 나오면 약속과 일정으로 옮기는 힘이 있습니다."
        if score >= 56:
            return "당신의 혼인 성향은 좋은 편입니다. 생활 조건이 정리되면 결혼 결정도 비교적 분명해집니다."
        if score >= 46:
            return "당신의 혼인 성향은 신중합니다. 마음이 있어도 시기와 책임 범위를 다시 확인하게 됩니다."
        return "당신의 혼인 성향은 늦어지기 쉽습니다. 좋아하는 마음이 있어도 결혼 약속으로 옮기는 데 시간이 걸립니다."
    if label == "가정 안정력":
        if score >= 70:
            return "당신의 가정 안정력은 강합니다. 생활비와 가족 책임을 현실적으로 정리하는 힘이 있습니다."
        if score >= 56:
            return "당신의 가정 안정력은 좋은 편입니다. 주거와 생활비 기준이 서면 결혼 생활도 안정됩니다."
        if score >= 46:
            return "당신의 가정 안정력은 평균권입니다. 가족 책임과 지출 기준을 늦게 정하면 부담이 커집니다."
        return "당신의 가정 안정력은 초반에 흔들리기 쉽습니다. 생활비와 가족 문제를 미루면 결혼 뒤 피로가 커집니다."
    if category == "money":
        if score >= 70:
            return f"당신의 {label}은 강한 편입니다. {phrase}에서 수입이 크게 늘어납니다."
        if score >= 56:
            return f"당신의 {label}은 좋은 편입니다. {phrase_object} 분명히 정하면 수입이 안정됩니다."
        if score >= 46:
            return f"당신의 {label}은 평균권에 가깝습니다. {phrase_object} 미리 정하면 손에 남는 돈이 안정됩니다."
        return f"당신의 {label}은 초반에는 크게 드러나지 않습니다. {phrase_object} 작고 분명하게 세워야 돈이 남습니다."
    if category == "social":
        if score >= 70:
            return f"당신의 {label}은 강한 편입니다. {phrase}에서 인정을 받습니다."
        if score >= 56:
            return f"당신의 {label}은 좋은 편입니다. {phrase_object} 분명히 정하면 평가가 안정됩니다."
        if score >= 46:
            return f"당신의 {label}은 평균권에 가깝습니다. {phrase_object} 미리 정하면 역할이 안정됩니다."
        return f"당신의 {label}은 초반에는 크게 드러나지 않습니다. {phrase_object} 작고 분명하게 세워야 평가가 흔들리지 않습니다."
    if score >= 70:
        return f"당신의 {label}은 강한 편입니다. {phrase}에서 판단이 단단합니다."
    if score >= 56:
        return f"당신의 {label}은 좋은 편입니다. {phrase_object} 분명히 정하면 행동이 안정됩니다."
    if score >= 46:
        return f"당신의 {label}은 평균권에 가깝습니다. {phrase_object} 미리 정하면 선택이 흔들리지 않습니다."
    return f"당신의 {label}은 초반에는 흔들리기 쉽습니다. {phrase_object} 작고 분명하게 세워야 선택이 안정됩니다."


def _axis(
    key: str,
    category: str,
    label: str,
    score: float,
    basis_codes: list[str],
    counter_signals: list[str],
) -> LifeFeatureScore:
    clipped = _clip(score)
    basis = list(dict.fromkeys(basis_codes))
    counter = list(dict.fromkeys(counter_signals))
    return LifeFeatureScore(
        key=key,
        category=category,
        label=label,
        score=clipped,
        percentile_label=_percentile_label(clipped),
        strength_label=_strength_label(clipped),
        confidence=_confidence(clipped, len(basis), len(counter)),  # type: ignore[arg-type]
        basis_codes=basis,
        counter_signals=counter,
        customer_sentence=_customer_sentence(label, category, clipped),
    )


def _sal_present(auxiliary: AuxiliaryProfile, sal_key: str) -> bool:
    return any(sal_key in values for values in auxiliary.sal_by_position.values())


def build_life_feature_profile(
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    branch_interactions: list[BranchInteraction],
    auxiliary_profile: AuxiliaryProfile,
    pattern_profile: PatternProfile,
    stem_reception_profile: StemReceptionProfile | None = None,
    integrated_saju_profile: IntegratedSajuProfile | None = None,
    cycle_regulation_profile: dict[str, object] | None = None,
    month_governance_profile: MonthGovernanceProfile | None = None,
) -> LifeFeatureProfile:
    """Build differentiated life-feature axes from natal structure."""

    wealth = _group(ten_god_profile, "wealth")
    output = _group(ten_god_profile, "output")
    officer = _group(ten_god_profile, "officer")
    resource = _group(ten_god_profile, "resource")
    peer = _group(ten_god_profile, "peer")
    sang_gwan = _ten_god(ten_god_profile, "sang_gwan")
    jeong_gwan = _ten_god(ten_god_profile, "jeong_gwan")
    pyeon_gwan = _ten_god(ten_god_profile, "pyeon_gwan")

    circulation = _circulation_bonus(element_profile)
    strength = _strength_bonus(element_profile)
    day_conflict = _interaction_count(branch_interactions, {"clash", "punishment", "harm", "break", "self_punishment"}, "day")
    month_conflict = _interaction_count(branch_interactions, {"clash", "punishment", "harm", "break", "self_punishment"}, "month")
    combines = _interaction_count(branch_interactions, {"six_combine", "three_harmony", "three_harmony_half", "three_meeting"})
    peach = 5 if _sal_present(auxiliary_profile, "peach_blossom") else 0
    travel = 4 if _sal_present(auxiliary_profile, "travel_horse") else 0
    pattern_bonus = 5 if pattern_profile.pattern_confidence in {"high", "medium_high"} else 0
    day_element = element_profile.day_master_element
    role_elements = {
        "peer": day_element,
        "resource": ELEMENT_GENERATED_BY[day_element],
        "output": ELEMENT_GENERATES[day_element],
        "wealth": ELEMENT_CONTROLS[day_element],
        "officer": ELEMENT_CONTROLLED_BY[day_element],
    }
    element_quality = {
        role: _element_quality(element_profile, element) + _pattern_element_delta(pattern_profile, element)
        for role, element in role_elements.items()
    }
    element_basis = {
        role: _element_basis(element_profile, role, element) + _pattern_element_basis(pattern_profile, role, element)
        for role, element in role_elements.items()
    }
    element_counters = {
        role: _element_counters(
            element_profile,
            role,
            element,
            dominant_load=role in {"peer", "output", "wealth", "officer"},
        )
        + _pattern_element_counters(pattern_profile, role, element)
        for role, element in role_elements.items()
    }

    axes = [
        _axis(
            "money_potential",
            "money",
            "재물 잠재력",
            43
            + wealth * 9
            + output * 4
            + element_quality["wealth"] * 0.7
            + element_quality["output"] * 0.3
            + circulation
            + pattern_bonus
            - peer * 2,
            (
                ["feature_wealth_group", "feature_output_support"]
                + element_basis["wealth"]
                + element_basis["output"]
            )
            if wealth or output
            else ["feature_money_baseline"] + element_basis["wealth"],
            (
                ["feature_peer_wealth_competition"]
                if "peer_wealth_competition" in ten_god_profile.important_pairs
                else []
            )
            + element_counters["wealth"]
            + element_counters["peer"],
        ),
        _axis(
            "income_expansion",
            "money",
            "수입 확대력",
            42
            + wealth * 7
            + output * 8
            + element_quality["wealth"] * 0.4
            + element_quality["output"] * 0.6
            + travel
            + circulation
            - month_conflict * 3,
            (
                ["feature_output_to_wealth"]
                if "output_to_wealth" in ten_god_profile.important_pairs
                else ["feature_income_material"]
            )
            + element_basis["wealth"]
            + element_basis["output"],
            (["feature_month_conflict"] if month_conflict else [])
            + element_counters["wealth"]
            + element_counters["output"],
        ),
        _axis(
            "liquidity_stability",
            "money",
            "현금 유동성",
            43
            + wealth * 6
            + output * 6
            + officer * 2
            + element_quality["wealth"] * 0.45
            + element_quality["output"] * 0.45
            + element_quality["officer"] * 0.2
            + circulation
            - peer * 2.5
            - month_conflict * 2,
            (
                ["feature_output_to_cash", "feature_wealth_cash_channel"]
                if wealth or output
                else ["feature_cash_baseline"]
            )
            + element_basis["wealth"]
            + element_basis["output"]
            + element_basis["officer"],
            (["feature_peer_cash_division"] if peer >= 1.2 else [])
            + (["feature_month_conflict_cash_noise"] if month_conflict else [])
            + element_counters["wealth"]
            + element_counters["output"],
        ),
        _axis(
            "reward_claim_strength",
            "money",
            "보상 확정력",
            42
            + output * 5
            + wealth * 5
            + officer * 5
            + element_quality["output"] * 0.35
            + element_quality["wealth"] * 0.35
            + element_quality["officer"] * 0.35
            + pattern_bonus * 0.4
            - peer * 2.2
            - sang_gwan * 1.2,
            ["feature_output_result", "feature_wealth_reward", "feature_officer_formal_standard"]
            + element_basis["output"]
            + element_basis["wealth"]
            + element_basis["officer"],
            (["feature_peer_reward_division"] if peer >= 1.2 else [])
            + (["feature_expression_reward_noise"] if sang_gwan >= 0.8 else [])
            + element_counters["output"]
            + element_counters["wealth"]
            + element_counters["officer"],
        ),
        _axis(
            "asset_retention",
            "money",
            "자산 유지력",
            48
            + resource * 7
            + officer * 4
            + element_quality["resource"] * 0.6
            + element_quality["officer"] * 0.3
            + max(0, strength)
            - peer * 6
            - wealth * 1.5,
            ["feature_resource_retention", "feature_officer_order"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_peer_distribution"] if peer >= 1.2 else [])
            + element_counters["resource"]
            + element_counters["peer"],
        ),
        _axis(
            "ownership_clarity",
            "money",
            "소유권 확정력",
            45
            + wealth * 4.5
            + officer * 6
            + resource * 4
            + element_quality["wealth"] * 0.35
            + element_quality["officer"] * 0.5
            + element_quality["resource"] * 0.35
            + max(0, strength) * 0.35
            - peer * 4.5
            - day_conflict * 3,
            ["feature_wealth_property_right", "feature_officer_title_standard", "feature_resource_document_basis"]
            + element_basis["wealth"]
            + element_basis["officer"]
            + element_basis["resource"],
            (["feature_peer_title_blur"] if peer >= 1.2 else [])
            + (["feature_day_conflict_title_noise"] if day_conflict else [])
            + element_counters["wealth"]
            + element_counters["officer"]
            + element_counters["resource"],
        ),
        _axis(
            "shared_asset_boundary",
            "money",
            "공동자금 경계력",
            45
            + officer * 5
            + resource * 4
            + wealth * 2.5
            + element_quality["officer"] * 0.45
            + element_quality["resource"] * 0.35
            + element_quality["wealth"] * 0.25
            + max(0, strength) * 0.25
            - peer * 5
            - day_conflict * 3
            - month_conflict * 1.5,
            ["feature_officer_shared_money_rule", "feature_resource_shared_money_record", "feature_wealth_shared_asset"]
            + element_basis["officer"]
            + element_basis["resource"]
            + element_basis["wealth"],
            (["feature_peer_shared_money_pressure"] if peer >= 1.2 else [])
            + (["feature_day_conflict_shared_money_noise"] if day_conflict else [])
            + (["feature_month_conflict_shared_money_noise"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["resource"]
            + element_counters["wealth"],
        ),
        _axis(
            "spending_control",
            "money",
            "지출 통제력",
            48
            + officer * 6
            + resource * 4
            + element_quality["officer"] * 0.5
            + element_quality["resource"] * 0.4
            - output * 3
            - peer * 4
            + max(0, strength),
            ["feature_officer_control", "feature_resource_planning"]
            + element_basis["officer"]
            + element_basis["resource"],
            (
                ["feature_output_spending", "feature_peer_spending"]
                if output + peer >= 2.2
                else []
            )
            + element_counters["output"]
            + element_counters["peer"],
        ),
        _axis(
            "investment_trading_sense",
            "money",
            "투자와 거래 감각",
            42
            + wealth * 6
            + output * 6
            + resource * 2
            + element_quality["wealth"] * 0.5
            + element_quality["output"] * 0.5
            + element_quality["resource"] * 0.2
            + travel
            + circulation
            - month_conflict * 2,
            ["feature_wealth_trade", "feature_output_market", "feature_resource_review"]
            + element_basis["wealth"]
            + element_basis["output"]
            + element_basis["resource"],
            (["feature_month_conflict_trade_noise"] if month_conflict else [])
            + element_counters["wealth"]
            + element_counters["output"],
        ),
        _axis(
            "money_attitude",
            "money",
            "돈을 대하는 태도",
            47
            + resource * 5
            + officer * 4
            + wealth * 3
            + element_quality["resource"] * 0.4
            + element_quality["officer"] * 0.3
            + element_quality["wealth"] * 0.3
            + max(0, strength) * 0.4
            - peer * 2
            - output,
            ["feature_resource_money_attitude", "feature_officer_money_standard", "feature_wealth_value_sense"]
            + element_basis["resource"]
            + element_basis["officer"]
            + element_basis["wealth"],
            (["feature_peer_money_pressure"] if peer >= 1.2 else [])
            + element_counters["peer"]
            + element_counters["output"],
        ),
        _axis(
            "deal_selection",
            "money",
            "좋은 제안을 고르는 힘",
            46
            + officer * 5
            + resource * 5
            + wealth * 3
            + element_quality["officer"] * 0.4
            + element_quality["resource"] * 0.4
            + element_quality["wealth"] * 0.3
            + max(0, strength) * 0.4
            - sang_gwan * 2
            - day_conflict * 3,
            ["feature_contract_review", "feature_resource_review", "feature_officer_standard"]
            + element_basis["officer"]
            + element_basis["resource"]
            + element_basis["wealth"],
            (["feature_expression_overrides_contract_review"] if sang_gwan >= 0.8 else [])
            + (["feature_day_conflict_selection_pressure"] if day_conflict else [])
            + element_counters["officer"]
            + element_counters["resource"],
        ),
        _axis(
            "loss_avoidance",
            "money",
            "손실 방어력",
            48
            + resource * 6
            + officer * 5
            + element_quality["resource"] * 0.5
            + element_quality["officer"] * 0.5
            + max(0, strength) * 0.5
            - peer * 3
            - output * 2
            - day_conflict * 2,
            ["feature_resource_loss_review", "feature_officer_risk_control"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_peer_loss_pressure"] if peer >= 1.2 else [])
            + (["feature_output_risk_speed"] if output >= 1.6 else [])
            + (["feature_day_conflict_loss_noise"] if day_conflict else [])
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "late_life_money_growth",
            "money",
            "후반 재물 성장성",
            43
            + wealth * 6
            + resource * 4
            + output * 3
            + element_quality["wealth"] * 0.4
            + element_quality["resource"] * 0.4
            + element_quality["output"] * 0.2
            + circulation
            + pattern_bonus
            + max(0, strength) * 0.5
            - month_conflict * 1.5,
            ["feature_wealth_growth", "feature_resource_accumulation", "feature_output_to_wealth"]
            + element_basis["wealth"]
            + element_basis["resource"]
            + element_basis["output"],
            (["feature_month_conflict_growth_delay"] if month_conflict else [])
            + element_counters["wealth"]
            + element_counters["resource"],
        ),
        _axis(
            "social_success_potential",
            "social",
            "사회적 성공 잠재력",
            44
            + officer * 8
            + output * 5
            + resource * 4
            + element_quality["officer"] * 0.5
            + element_quality["output"] * 0.3
            + element_quality["resource"] * 0.2
            + circulation
            + pattern_bonus
            - month_conflict * 2,
            ["feature_officer_status", "feature_output_visibility", "feature_resource_support"]
            + element_basis["officer"]
            + element_basis["output"]
            + element_basis["resource"],
            (["feature_month_conflict"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["output"],
        ),
        _axis(
            "honor_recognition",
            "social",
            "명예운",
            43
            + officer * 9
            + resource * 5
            + jeong_gwan * 4
            + element_quality["officer"] * 0.6
            + element_quality["resource"] * 0.4
            + peach
            - sang_gwan * 2,
            ["feature_officer_recognition", "feature_resource_reputation"]
            + element_basis["officer"]
            + element_basis["resource"],
            (
                ["feature_hurting_officer_pressure"]
                if "hurting_officer_meets_officer" in ten_god_profile.important_pairs
                else []
            )
            + element_counters["officer"],
        ),
        _axis(
            "promotion_visibility",
            "social",
            "발탁 가능성",
            42
            + officer * 7
            + output * 4
            + resource * 4
            + jeong_gwan * 3
            + element_quality["officer"] * 0.55
            + element_quality["output"] * 0.25
            + element_quality["resource"] * 0.3
            + peach * 0.5
            + pattern_bonus * 0.5
            - sang_gwan * 2.2
            - month_conflict * 2.5,
            ["feature_officer_promotion", "feature_output_public_result", "feature_resource_recommendation"]
            + element_basis["officer"]
            + element_basis["output"]
            + element_basis["resource"],
            (
                ["feature_hurting_officer_promotion_noise"]
                if "hurting_officer_meets_officer" in ten_god_profile.important_pairs or sang_gwan >= 0.8
                else []
            )
            + (["feature_month_conflict_promotion_noise"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["output"],
        ),
        _axis(
            "career_achievement",
            "social",
            "직업적 성취력",
            45
            + officer * 8
            + output * 5
            + resource * 3
            + element_quality["officer"] * 0.5
            + element_quality["output"] * 0.3
            + (5 if _position_has(position_signals, "month", "career") else 0)
            - month_conflict * 3,
            ["feature_month_palace_career", "feature_officer_work"]
            + element_basis["officer"]
            + element_basis["output"],
            (["feature_month_conflict"] if month_conflict else [])
            + element_counters["officer"],
        ),
        _axis(
            "work_domain_fit",
            "social",
            "직업 분야 적합도",
            43
            + officer * 5
            + output * 4
            + resource * 4
            + wealth * 2.5
            + element_quality["officer"] * 0.35
            + element_quality["output"] * 0.3
            + element_quality["resource"] * 0.3
            + element_quality["wealth"] * 0.2
            + (4 if _position_has(position_signals, "month", "career") else 0)
            + circulation * 0.5
            - month_conflict * 2,
            ["feature_month_palace_career", "feature_role_element_fit", "feature_work_domain_material"]
            + element_basis["officer"]
            + element_basis["output"]
            + element_basis["resource"]
            + element_basis["wealth"],
            (["feature_month_conflict_work_domain_noise"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["output"]
            + element_counters["resource"],
        ),
        _axis(
            "leadership_potential",
            "social",
            "리더십 잠재력",
            42
            + peer * 5
            + officer * 6
            + pyeon_gwan * 5
            + element_quality["peer"] * 0.4
            + element_quality["officer"] * 0.5
            + strength
            + circulation,
            ["feature_peer_drive", "feature_officer_responsibility"]
            + element_basis["peer"]
            + element_basis["officer"],
            ["feature_weak_day_master_leadership_load"] if element_profile.day_master_strength in {"weak", "very_weak"} else [],
        ),
        _axis(
            "interpersonal_influence",
            "social",
            "대인 영향력",
            43
            + output * 7
            + element_quality["output"] * 0.5
            + peach
            + combines * 4
            + peer * 2
            - day_conflict * 3,
            ["feature_output_expression", "feature_connection_signal"] + element_basis["output"],
            (["feature_day_conflict"] if day_conflict else []) + element_counters["output"],
        ),
        _axis(
            "attraction_selectivity",
            "personality",
            "연애 선별력",
            44
            + wealth * 5
            + officer * 4
            + resource * 3
            + element_quality["wealth"] * 0.45
            + element_quality["officer"] * 0.35
            + element_quality["resource"] * 0.25
            + peach
            + max(0, strength) * 0.25
            - day_conflict * 4
            - peer * 1.5,
            ["feature_love_selectivity", "feature_wealth_attraction", "feature_officer_partner_standard"]
            + element_basis["wealth"]
            + element_basis["officer"]
            + element_basis["resource"],
            (["feature_day_conflict_love_selection_noise"] if day_conflict else [])
            + (["feature_peer_rivalry_love_selection"] if peer >= 1.2 else [])
            + element_counters["wealth"]
            + element_counters["officer"],
        ),
        _axis(
            "affection_receptivity",
            "personality",
            "애정 수용성",
            44
            + resource * 4
            + wealth * 4
            + officer * 3
            + combines * 3
            + element_quality["resource"] * 0.35
            + element_quality["wealth"] * 0.35
            + element_quality["officer"] * 0.25
            + peach * 0.6
            - day_conflict * 3.5
            - peer * 1.5,
            ["feature_resource_affection_trust", "feature_wealth_affection_reality", "feature_officer_affection_commitment"]
            + element_basis["resource"]
            + element_basis["wealth"]
            + element_basis["officer"],
            (["feature_day_conflict_affection_receptivity_noise"] if day_conflict else [])
            + (["feature_peer_affection_competition"] if peer >= 1.2 else [])
            + element_counters["resource"]
            + element_counters["wealth"]
            + element_counters["officer"],
        ),
        _axis(
            "relationship_progression",
            "social",
            "관계 진전력",
            42
            + output * 5
            + wealth * 3
            + officer * 3
            + combines * 5
            + peach
            + element_quality["output"] * 0.45
            + element_quality["wealth"] * 0.25
            + element_quality["officer"] * 0.25
            - resource * 1.2
            - day_conflict * 3,
            ["feature_contact_progression", "feature_connection_signal", "feature_output_expression"]
            + element_basis["output"]
            + element_basis["wealth"]
            + element_basis["officer"],
            (["feature_day_conflict_progression_load"] if day_conflict else [])
            + (["feature_resource_hesitation"] if resource >= 1.6 else [])
            + element_counters["output"],
        ),
        _axis(
            "emotional_alignment",
            "personality",
            "감정 조율력",
            45
            + resource * 4
            + officer * 4
            + output * 2.5
            + combines * 3
            + element_quality["resource"] * 0.35
            + element_quality["officer"] * 0.35
            + element_quality["output"] * 0.2
            - day_conflict * 5
            - sang_gwan * 1.5,
            ["feature_resource_emotional_review", "feature_officer_emotional_standard", "feature_output_emotional_expression"]
            + element_basis["resource"]
            + element_basis["officer"]
            + element_basis["output"],
            (["feature_day_conflict_emotional_noise"] if day_conflict else [])
            + (["feature_expression_emotional_friction"] if sang_gwan >= 0.8 else [])
            + element_counters["resource"]
            + element_counters["officer"]
            + element_counters["output"],
        ),
        _axis(
            "affection_expression",
            "personality",
            "애정 표현성",
            43
            + output * 7
            + peer * 2
            + combines * 2
            + peach
            + element_quality["output"] * 0.6
            + element_quality["peer"] * 0.2
            - resource * 2
            - day_conflict * 2,
            ["feature_affection_expression", "feature_output_expression", "feature_visibility_contact"]
            + element_basis["output"]
            + element_basis["peer"],
            (["feature_resource_expression_delay"] if resource >= 1.5 else [])
            + (["feature_day_conflict_expression_noise"] if day_conflict else [])
            + element_counters["output"],
        ),
        _axis(
            "misunderstanding_prevention",
            "personality",
            "오해 차단력",
            46
            + resource * 5
            + officer * 3.5
            + output * 2
            + element_quality["resource"] * 0.45
            + element_quality["officer"] * 0.3
            + element_quality["output"] * 0.2
            + combines * 2
            - sang_gwan * 2.5
            - day_conflict * 4.5
            - peer,
            ["feature_resource_message_check", "feature_officer_contact_standard", "feature_output_expression_filter"]
            + element_basis["resource"]
            + element_basis["officer"]
            + element_basis["output"],
            (["feature_expression_misunderstanding_noise"] if sang_gwan >= 0.8 else [])
            + (["feature_day_conflict_misunderstanding_noise"] if day_conflict else [])
            + (["feature_peer_misunderstanding_pressure"] if peer >= 1.2 else [])
            + element_counters["resource"]
            + element_counters["output"],
        ),
        _axis(
            "reunion_closure",
            "personality",
            "관계 정리력",
            44
            + resource * 4
            + officer * 3.5
            + combines * 3
            + element_quality["resource"] * 0.4
            + element_quality["officer"] * 0.35
            + max(0, strength) * 0.25
            - day_conflict * 3
            - peer * 1.5,
            ["feature_resource_relationship_memory", "feature_officer_relationship_closure", "feature_connection_signal"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_day_conflict_reunion_noise"] if day_conflict else [])
            + (["feature_peer_reunion_interference"] if peer >= 1.2 else [])
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "business_expansion",
            "money",
            "사업 확장력",
            41
            + wealth * 7
            + output * 6
            + peer * 3
            + element_quality["wealth"] * 0.5
            + element_quality["output"] * 0.5
            + travel
            + circulation
            - resource * 1.5,
            ["feature_wealth_trade", "feature_output_market", "feature_peer_drive"]
            + element_basis["wealth"]
            + element_basis["output"],
            (["feature_retention_check"] if peer >= 1.2 else [])
            + element_counters["wealth"]
            + element_counters["output"],
        ),
        _axis(
            "academic_expertise",
            "social",
            "학문·전문성 성취력",
            44
            + resource * 9
            + officer * 4
            + element_quality["resource"] * 0.7
            + element_quality["officer"] * 0.2
            + circulation
            + (3 if "resource_support_available" in element_profile.circulation_notes else 0),
            ["feature_resource_learning", "feature_officer_certification"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_resource_low"] if resource < 0.8 else []) + element_counters["resource"],
        ),
        _axis(
            "organization_adaptability",
            "social",
            "조직 적응력",
            48
            + officer * 7
            + resource * 4
            + element_quality["officer"] * 0.6
            + element_quality["resource"] * 0.3
            - sang_gwan * 5
            - month_conflict * 4,
            ["feature_officer_order", "feature_resource_acceptance"]
            + element_basis["officer"]
            + element_basis["resource"],
            (["feature_sang_gwan_friction"] if sang_gwan >= 0.8 else [])
            + element_counters["officer"]
            + element_counters["output"],
        ),
        _axis(
            "reputation_maintenance",
            "social",
            "평판 유지력",
            45
            + officer * 8
            + resource * 5
            + jeong_gwan * 3
            + element_quality["officer"] * 0.5
            + element_quality["resource"] * 0.4
            + peach
            - sang_gwan * 3
            - month_conflict * 2
            - day_conflict,
            ["feature_officer_reputation", "feature_resource_credibility", "feature_jeong_gwan_public_order"]
            + element_basis["officer"]
            + element_basis["resource"],
            (
                ["feature_hurting_officer_reputation_pressure"]
                if "hurting_officer_meets_officer" in ten_god_profile.important_pairs
                else []
            )
            + (["feature_month_conflict_reputation_noise"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["output"],
        ),
        _axis(
            "responsibility_capacity",
            "social",
            "책임 감당력",
            44
            + officer * 7
            + pyeon_gwan * 4
            + resource * 3
            + element_quality["officer"] * 0.5
            + element_quality["resource"] * 0.3
            + strength
            + circulation
            - day_conflict * 2,
            ["feature_officer_responsibility", "feature_pyeon_gwan_pressure_handling", "feature_resource_support"]
            + element_basis["officer"]
            + element_basis["resource"],
            (
                ["feature_weak_day_master_responsibility_load"]
                if element_profile.day_master_strength in {"weak", "very_weak"}
                else []
            )
            + (["feature_day_conflict_responsibility_noise"] if day_conflict else [])
            + element_counters["officer"],
        ),
        _axis(
            "role_authority_alignment",
            "social",
            "권한 일치도",
            43
            + officer * 6
            + resource * 4
            + wealth * 3
            + element_quality["officer"] * 0.5
            + element_quality["resource"] * 0.35
            + element_quality["wealth"] * 0.25
            + max(0, strength) * 0.3
            + pattern_bonus * 0.3
            - peer * 2.5
            - day_conflict * 2
            - month_conflict * 2,
            ["feature_officer_authority", "feature_resource_reporting_basis", "feature_wealth_compensation_standard"]
            + element_basis["officer"]
            + element_basis["resource"]
            + element_basis["wealth"],
            (["feature_peer_authority_interference"] if peer >= 1.2 else [])
            + (["feature_day_conflict_authority_noise"] if day_conflict else [])
            + (["feature_month_conflict_authority_noise"] if month_conflict else [])
            + element_counters["officer"]
            + element_counters["resource"],
        ),
        _axis(
            "self_direction",
            "personality",
            "자기 주도성",
            45
            + peer * 6
            + output * 3
            + pyeon_gwan * 3
            + element_quality["peer"] * 0.5
            + strength
            + pattern_bonus
            - month_conflict * 2,
            ["feature_peer_self_direction", "feature_day_master_drive"] + element_basis["peer"],
            ["feature_weak_day_master_self_direction_load"]
            if element_profile.day_master_strength in {"weak", "very_weak"}
            else [],
        ),
        _axis(
            "decision_consistency",
            "personality",
            "결정 지속성",
            48
            + resource * 5
            + officer * 5
            + element_quality["resource"] * 0.4
            + element_quality["officer"] * 0.4
            + max(0, strength)
            - sang_gwan * 3
            - day_conflict * 4,
            ["feature_resource_review", "feature_officer_consistency"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_expression_overrides_consistency"] if sang_gwan >= 0.8 else [])
            + element_counters["output"],
        ),
        _axis(
            "communication_expression",
            "personality",
            "표현 전달력",
            43
            + output * 8
            + element_quality["output"] * 0.6
            + peach
            + combines * 2
            + peer * 2
            - resource * 1.5,
            ["feature_output_expression", "feature_visibility_contact"] + element_basis["output"],
            (["feature_expression_needs_filter"] if output >= 1.6 else []) + element_counters["output"],
        ),
        _axis(
            "boundary_management",
            "personality",
            "관계 경계 설정력",
            47
            + officer * 5
            + resource * 4
            + element_quality["officer"] * 0.4
            + element_quality["resource"] * 0.4
            + max(0, strength)
            - day_conflict * 6
            - peer * 2,
            ["feature_officer_boundary", "feature_resource_self_protection"]
            + element_basis["officer"]
            + element_basis["resource"],
            (["feature_day_conflict_boundary_pressure"] if day_conflict else [])
            + element_counters["peer"],
        ),
        _axis(
            "practical_planning",
            "personality",
            "현실 설계력",
            46
            + resource * 5
            + wealth * 4
            + officer * 5
            + element_quality["resource"] * 0.4
            + element_quality["wealth"] * 0.3
            + element_quality["officer"] * 0.3
            + circulation
            - output * 1.5,
            ["feature_resource_planning", "feature_wealth_reality_check", "feature_officer_order"]
            + element_basis["resource"]
            + element_basis["wealth"]
            + element_basis["officer"],
            (["feature_plan_execution_gap"] if output >= 1.6 and resource < 1.0 else [])
            + element_counters["resource"],
        ),
        _axis(
            "change_adaptability",
            "personality",
            "변화 적응력",
            45
            + output * 3
            + element_quality["output"] * 0.3
            + combines * 4
            + travel
            + circulation
            - month_conflict * 3,
            ["feature_connection_signal", "feature_change_mobility"] + element_basis["output"],
            (["feature_month_conflict_adaptation_load"] if month_conflict else [])
            + element_counters["output"],
        ),
        _axis(
            "relationship_stability",
            "personality",
            "관계 안정성",
            49
            + resource * 3
            + element_quality["resource"] * 0.3
            + combines * 5
            + max(0, strength)
            - day_conflict * 8
            - peer * 2,
            ["feature_day_palace_relationship", "feature_connection_signal"] + element_basis["resource"],
            (["feature_day_conflict"] if day_conflict else []) + element_counters["peer"],
        ),
        _axis(
            "marriage_stability",
            "personality",
            "결혼 안정성",
            48
            + officer * 3
            + resource * 3
            + element_quality["officer"] * 0.3
            + element_quality["resource"] * 0.2
            + combines * 4
            - day_conflict * 9
            + (4 if _position_has(position_signals, "day", "marriage") else 0),
            ["feature_day_palace_marriage", "feature_responsibility_support"]
            + element_basis["officer"]
            + element_basis["resource"],
            (["feature_day_conflict"] if day_conflict else [])
            + element_counters["officer"]
            + element_counters["peer"],
        ),
        _axis(
            "spouse_match_quality",
            "personality",
            "배우자상",
            45
            + officer * 5
            + wealth * 4
            + resource * 2
            + combines * 3
            + element_quality["officer"] * 0.45
            + element_quality["wealth"] * 0.35
            + element_quality["resource"] * 0.2
            + (5 if _position_has(position_signals, "day", "marriage") else 0)
            - day_conflict * 7
            - peer * 1.5,
            ["feature_spouse_match", "feature_day_palace_marriage", "feature_officer_partner_standard"]
            + element_basis["officer"]
            + element_basis["wealth"]
            + element_basis["resource"],
            (["feature_day_conflict_spouse_mismatch"] if day_conflict else [])
            + (["feature_peer_spouse_competition"] if peer >= 1.2 else [])
            + element_counters["officer"]
            + element_counters["wealth"],
        ),
        _axis(
            "spouse_support_benefit",
            "personality",
            "배우자 조력운",
            43
            + officer * 5
            + wealth * 4
            + resource * 3
            + combines * 3
            + element_quality["officer"] * 0.4
            + element_quality["wealth"] * 0.3
            + element_quality["resource"] * 0.3
            + (4 if _position_has(position_signals, "day", "marriage") else 0)
            - day_conflict * 5
            - peer * 2,
            ["feature_spouse_support", "feature_officer_partner_reliability", "feature_wealth_household_resource"]
            + element_basis["officer"]
            + element_basis["wealth"]
            + element_basis["resource"],
            (["feature_day_conflict_spouse_support_noise"] if day_conflict else [])
            + (["feature_peer_spouse_support_interference"] if peer >= 1.2 else [])
            + element_counters["officer"]
            + element_counters["wealth"]
            + element_counters["resource"],
        ),
        _axis(
            "marriage_timing_readiness",
            "personality",
            "혼인 성향",
            44
            + officer * 5
            + wealth * 4
            + resource * 3
            + combines * 4
            + element_quality["officer"] * 0.4
            + element_quality["wealth"] * 0.3
            + element_quality["resource"] * 0.3
            + max(0, strength) * 0.25
            - sang_gwan * 1.5
            - day_conflict * 5,
            ["feature_marriage_timing", "feature_officer_commitment", "feature_wealth_household_reality"]
            + element_basis["officer"]
            + element_basis["wealth"]
            + element_basis["resource"],
            (["feature_hurting_officer_commitment_delay"] if sang_gwan >= 0.8 else [])
            + (["feature_day_conflict_marriage_timing_load"] if day_conflict else [])
            + element_counters["officer"]
            + element_counters["wealth"],
        ),
        _axis(
            "household_stability",
            "personality",
            "가정 안정력",
            46
            + resource * 5
            + wealth * 4
            + officer * 3
            + element_quality["resource"] * 0.45
            + element_quality["wealth"] * 0.35
            + element_quality["officer"] * 0.25
            + (4 if _position_has(position_signals, "day", "marriage") else 0)
            + max(0, strength) * 0.25
            - day_conflict * 5
            - peer * 2,
            ["feature_household_stability", "feature_resource_care", "feature_wealth_household_reality"]
            + element_basis["resource"]
            + element_basis["wealth"]
            + element_basis["officer"],
            (["feature_day_conflict_household_pressure"] if day_conflict else [])
            + (["feature_peer_household_burden"] if peer >= 1.2 else [])
            + element_counters["resource"]
            + element_counters["wealth"],
        ),
        _axis(
            "household_finance_alignment",
            "personality",
            "부부 재정 합의력",
            45
            + wealth * 4
            + resource * 4
            + officer * 4
            + element_quality["wealth"] * 0.35
            + element_quality["resource"] * 0.35
            + element_quality["officer"] * 0.3
            + (3 if _position_has(position_signals, "day", "marriage") else 0)
            - peer * 3.5
            - day_conflict * 4,
            ["feature_wealth_couple_finance", "feature_resource_couple_record", "feature_officer_couple_rule"]
            + element_basis["wealth"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_peer_couple_finance_pressure"] if peer >= 1.2 else [])
            + (["feature_day_conflict_couple_finance_noise"] if day_conflict else [])
            + element_counters["wealth"]
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "family_responsibility",
            "personality",
            "가족 책임감",
            47
            + resource * 5
            + officer * 4
            + wealth * 2
            + combines * 2
            + element_quality["resource"] * 0.4
            + element_quality["officer"] * 0.3
            + element_quality["wealth"] * 0.2
            + (4 if _position_has(position_signals, "day", "marriage") else 0)
            - day_conflict * 4
            - peer,
            ["feature_family_responsibility", "feature_resource_care", "feature_officer_household_order"]
            + element_basis["resource"]
            + element_basis["officer"]
            + element_basis["wealth"],
            (["feature_day_conflict_family_pressure"] if day_conflict else [])
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "inlaw_boundary_strength",
            "personality",
            "배우자 가족 경계력",
            45
            + officer * 4
            + resource * 4
            + wealth * 2
            + element_quality["officer"] * 0.35
            + element_quality["resource"] * 0.35
            + element_quality["wealth"] * 0.2
            + max(0, strength) * 0.25
            - day_conflict * 4
            - peer * 2.5,
            ["feature_officer_inlaw_boundary", "feature_resource_family_record", "feature_wealth_family_responsibility"]
            + element_basis["officer"]
            + element_basis["resource"]
            + element_basis["wealth"],
            (["feature_day_conflict_inlaw_boundary_noise"] if day_conflict else [])
            + (["feature_peer_inlaw_boundary_pressure"] if peer >= 1.2 else [])
            + element_counters["officer"]
            + element_counters["resource"],
        ),
        _axis(
            "conflict_recovery",
            "personality",
            "갈등 회복력",
            46
            + resource * 5
            + officer * 3
            + combines * 4
            + element_quality["resource"] * 0.5
            + element_quality["officer"] * 0.3
            + max(0, strength)
            + circulation
            - day_conflict * 5,
            ["feature_relationship_repair", "feature_resource_recovery", "feature_officer_boundary"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_day_conflict_repair_load"] if day_conflict else [])
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "marriage_crisis_management",
            "personality",
            "혼인 위기 관리력",
            44
            + resource * 5
            + officer * 4
            + combines * 3
            + element_quality["resource"] * 0.45
            + element_quality["officer"] * 0.35
            + max(0, strength) * 0.3
            + circulation * 0.5
            - day_conflict * 5
            - month_conflict * 1.5,
            ["feature_resource_marriage_recovery", "feature_officer_marriage_rule", "feature_connection_signal"]
            + element_basis["resource"]
            + element_basis["officer"],
            (["feature_day_conflict_marriage_crisis_noise"] if day_conflict else [])
            + (["feature_month_conflict_marriage_crisis_noise"] if month_conflict else [])
            + element_counters["resource"]
            + element_counters["officer"],
        ),
        _axis(
            "crisis_recovery",
            "personality",
            "위기 회복력",
            47
            + resource * 5
            + element_quality["resource"] * 0.6
            + max(0, strength)
            + circulation
            + len(element_profile.useful_elements) * 2
            - day_conflict * 2,
            ["feature_resource_recovery", "feature_useful_element_support"] + element_basis["resource"],
            (["feature_climate_bias"] if element_profile.climate_needs else [])
            + element_counters["resource"],
        ),
    ]

    axes = _apply_reception_axis_adjustments(axes, stem_reception_profile, integrated_saju_profile)
    axes = _apply_month_governance_axis_adjustments(axes, month_governance_profile)
    axes = _apply_cycle_regulation_axis_adjustments(axes, cycle_regulation_profile)

    axis_map = {axis.key: axis for axis in axes}
    top_axis_keys = [axis.key for axis in sorted(axes, key=lambda item: item.score, reverse=True)[:5]]
    caution_axis_keys = [
        axis.key
        for axis in sorted(axes, key=lambda item: (item.score, -len(item.counter_signals)))
        if axis.score < 52 or axis.counter_signals
    ][:5]
    summary_sentences = [axis_map[key].customer_sentence for key in top_axis_keys[:3]]
    return LifeFeatureProfile(
        axes=axis_map,
        top_axis_keys=top_axis_keys,
        caution_axis_keys=caution_axis_keys,
        summary_sentences=summary_sentences,
    )
