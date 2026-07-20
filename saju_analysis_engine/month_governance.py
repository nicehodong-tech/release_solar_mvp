"""Month-command governance layer.

The month branch is the chart's public environment, season, and pattern gate.
This module does not replace element balance or ten-god scoring. It decides
whether a signal is usable, burdensome, mixed, or only latent when judged from
the month branch and regular-pattern demand.
"""

from __future__ import annotations

from .constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_METADATA,
    ELEMENT_CONTROLLED_BY,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATES,
    ELEMENTS,
    STEM_METADATA,
    TEN_GOD_GROUPS,
)
from .models import (
    ElementProfile,
    MonthGovernanceDecision,
    MonthGovernanceElementFit,
    MonthHiddenPhaseProfile,
    MonthGovernanceProfile,
    MonthGovernanceRoleFit,
    PatternProfile,
    PositionSignal,
    TenGodProfile,
)
from .ten_gods import ten_god_for


MONTH_GOVERNANCE_VERSION = "month_governance_v1"

DOMAIN_FOCUS_GROUPS: dict[str, list[str]] = {
    "money": ["wealth", "output", "peer", "resource"],
    "career": ["officer", "resource", "output", "wealth"],
    "love": ["wealth", "officer", "output", "peer"],
    "marriage": ["officer", "wealth", "resource", "peer"],
    "personality": ["peer", "output", "wealth", "officer", "resource"],
    "honor": ["officer", "resource", "output", "wealth"],
    "social": ["peer", "officer", "resource", "output"],
    "life": ["resource", "officer", "wealth", "peer", "output"],
    "life_period": ["resource", "officer", "wealth", "peer", "output"],
    "timing": ["wealth", "officer", "output", "resource", "peer"],
}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _candidate_score(candidates: list[object], element: str) -> int:
    return max(
        (
            int(getattr(candidate, "score", 0) or 0)
            for candidate in candidates
            if str(getattr(candidate, "element", "")) == element
        ),
        default=0,
    )


def _candidate_roles(candidates: list[object], element: str) -> list[str]:
    return _unique(
        [
            str(getattr(candidate, "role", ""))
            for candidate in candidates
            if str(getattr(candidate, "element", "")) == element
        ]
    )


def _candidate_basis(candidates: list[object], element: str) -> list[str]:
    codes: list[str] = []
    for candidate in candidates:
        if str(getattr(candidate, "element", "")) != element:
            continue
        codes.extend(str(code) for code in list(getattr(candidate, "basis_codes", []) or []) if str(code))
    return _unique(codes)


def _score_step(score: int) -> int:
    if score >= 80:
        return 5
    if score >= 72:
        return 4
    if score >= 62:
        return 3
    if score >= 50:
        return 2
    if score > 0:
        return 1
    return 0


def _status(support_score: int, pressure_score: int) -> str:
    if support_score >= pressure_score + 3:
        return "supports_month_command"
    if pressure_score >= support_score + 3:
        return "harms_month_command"
    if support_score and pressure_score:
        return "mixed_by_month_command"
    if support_score:
        return "usable_by_month_command"
    if pressure_score:
        return "burdensome_by_month_command"
    return "neutral_to_month_command"


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


def _group_for_element(day_element: str, element: str) -> str:
    for group in ("peer", "resource", "output", "wealth", "officer"):
        if _role_element(day_element, group) == element:
            return group
    return ""


def _candidate_groups(candidates: list[object], day_element: str) -> list[str]:
    groups: list[str] = []
    for candidate in candidates:
        element = str(getattr(candidate, "element", ""))
        group = _group_for_element(day_element, element)
        if group:
            groups.append(group)
    return _unique(groups)


def _month_authority_for_element(
    element: str,
    *,
    month_branch: str,
    month_element: str,
    hidden_entries: list[dict[str, object]],
    protruded_hidden_stems: list[str],
) -> tuple[str, int, list[str]]:
    basis: list[str] = []
    if element == month_element:
        basis.append(f"month_branch_element_{element}")
        return "month_branch_body", 3, basis
    hidden_matches = [entry for entry in hidden_entries if entry.get("element") == element]
    if hidden_matches:
        basis.append(f"month_hidden_element_{element}")
        protruded = any(str(entry.get("stem")) in protruded_hidden_stems for entry in hidden_matches)
        if protruded:
            basis.append(f"month_hidden_protruded_{element}")
            return "month_hidden_protruded", 3, basis
        main_weight = max(float(entry.get("weight") or 0.0) for entry in hidden_matches)
        if main_weight >= 0.55:
            return "month_hidden_main", 2, basis
        return "month_hidden_secondary", 1, basis
    return f"season_{BRANCH_METADATA[month_branch]['season']}", 0, basis


def _build_hidden_entries(day_stem: str, month_branch: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for stem_key, weight in BRANCH_HIDDEN_STEMS.get(month_branch, []):
        ten_god = ten_god_for(day_stem, stem_key)
        entries.append(
            {
                "stem": stem_key,
                "element": STEM_METADATA[stem_key]["element"],
                "ten_god": ten_god,
                "group": TEN_GOD_GROUPS.get(ten_god, ""),
                "weight": weight,
            }
        )
    return entries


def build_month_governance_profile(
    *,
    day_master_stem: str,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    pattern_profile: PatternProfile,
    position_signals: dict[str, PositionSignal],
    month_hidden_phase: MonthHiddenPhaseProfile | None = None,
) -> MonthGovernanceProfile:
    month_signal = position_signals.get("month")
    month_branch = element_profile.month_branch
    month_element = month_signal.branch_element if month_signal else BRANCH_METADATA[month_branch]["element"]
    month_command_ten_god = pattern_profile.month_command_ten_god
    month_command_group = TEN_GOD_GROUPS.get(month_command_ten_god, "")
    hidden_entries = _build_hidden_entries(day_master_stem, month_branch)
    protruded_hidden_stems = list(month_signal.protruded_hidden_stems if month_signal else [])

    useful_candidates = list(pattern_profile.useful_element_candidates)
    caution_candidates = list(pattern_profile.caution_element_candidates)
    useful_elements = _unique([str(candidate.element) for candidate in useful_candidates if str(candidate.element)])
    caution_elements = _unique([str(candidate.element) for candidate in caution_candidates if str(candidate.element)])
    useful_groups = _candidate_groups(useful_candidates, element_profile.day_master_element)
    caution_groups = _candidate_groups(caution_candidates, element_profile.day_master_element)

    element_fits: dict[str, MonthGovernanceElementFit] = {}
    for element in ELEMENTS:
        support_score = 0
        pressure_score = 0
        basis_codes: list[str] = []
        counter_signals: list[str] = []
        roles: list[str] = []

        support_candidate_score = _candidate_score(useful_candidates, element)
        pressure_candidate_score = _candidate_score(caution_candidates, element)
        support_score += _score_step(support_candidate_score)
        pressure_score += _score_step(pressure_candidate_score)
        roles.extend(_candidate_roles(useful_candidates, element))
        roles.extend(_candidate_roles(caution_candidates, element))
        basis_codes.extend(_candidate_basis(useful_candidates, element))
        counter_signals.extend(_candidate_basis(caution_candidates, element))

        score = element_profile.scores[element]
        if element in element_profile.useful_elements:
            support_score += 2
            basis_codes.append(f"month_governance_element_useful_{element}")
        if element in element_profile.climate_needs:
            support_score += 2
            basis_codes.append(f"month_governance_johu_need_{element}")
        if element in element_profile.caution_elements and element not in useful_elements:
            pressure_score += 2
            counter_signals.append(f"month_governance_element_caution_{element}")
        if score.state == "dominant" and element not in useful_elements and element not in element_profile.climate_needs:
            pressure_score += 1
            counter_signals.append(f"month_governance_element_dominant_load_{element}")

        month_authority, authority_score, authority_basis = _month_authority_for_element(
            element,
            month_branch=month_branch,
            month_element=month_element,
            hidden_entries=hidden_entries,
            protruded_hidden_stems=protruded_hidden_stems,
        )
        basis_codes.extend(authority_basis)
        reality_score = authority_score
        if score.exposure in {"clear", "present"}:
            reality_score += 2
            basis_codes.append(f"month_governance_visible_{element}")
        elif score.exposure == "hidden":
            reality_score += 1
            basis_codes.append(f"month_governance_rooted_{element}")
        if month_hidden_phase and month_hidden_phase.active_element == element:
            reality_score += 2
            basis_codes.append(f"month_hidden_phase_active_element_{element}")
            if month_hidden_phase.active_stem in protruded_hidden_stems:
                reality_score += 1
                basis_codes.append(f"month_hidden_phase_active_stem_protruded_{month_hidden_phase.active_stem}")
        if element == month_element and pressure_score and not support_score:
            pressure_score += 1
            counter_signals.append(f"month_body_pressures_pattern_{element}")

        element_fits[element] = MonthGovernanceElementFit(
            element=element,
            status=_status(support_score, pressure_score),
            support_score=support_score,
            pressure_score=pressure_score,
            reality_score=reality_score,
            month_authority=month_authority,
            roles=_unique(roles),
            basis_codes=_unique(basis_codes),
            counter_signals=_unique(counter_signals),
        )

    role_fits: dict[str, MonthGovernanceRoleFit] = {}
    for group in ("peer", "resource", "output", "wealth", "officer"):
        element = _role_element(element_profile.day_master_element, group)
        fit = element_fits[element]
        role_fits[group] = MonthGovernanceRoleFit(
            group=group,
            element=element,
            status=fit.status,
            support_score=fit.support_score,
            pressure_score=fit.pressure_score,
            basis_codes=[*fit.basis_codes, f"month_governance_role_{group}_{element}"],
            counter_signals=list(fit.counter_signals),
        )

    notes = [
        f"month_branch:{month_branch}",
        f"month_command:{month_command_ten_god}",
        f"month_command_group:{month_command_group}",
    ]
    if pattern_profile.regular_pattern:
        notes.append(f"regular_pattern:{pattern_profile.regular_pattern}")
    if protruded_hidden_stems:
        notes.append("month_hidden_stem_protruded")
    if month_hidden_phase and month_hidden_phase.active_stem:
        notes.append(f"month_hidden_phase:{month_hidden_phase.active_phase}:{month_hidden_phase.active_stem}")
        if month_hidden_phase.active_ten_god:
            notes.append(f"month_hidden_phase_ten_god:{month_hidden_phase.active_ten_god}")
    if ten_god_profile.dominant_ten_gods:
        notes.extend(f"dominant_ten_god:{item}" for item in ten_god_profile.dominant_ten_gods[:3])

    return MonthGovernanceProfile(
        month_branch=month_branch,
        month_element=month_element,
        month_command_ten_god=month_command_ten_god,
        month_command_group=month_command_group,
        regular_pattern=pattern_profile.regular_pattern,
        pattern_family=pattern_profile.pattern_family,
        command_hidden_stems=hidden_entries,
        protruded_hidden_stems=protruded_hidden_stems,
        useful_elements=useful_elements,
        caution_elements=caution_elements,
        useful_groups=useful_groups,
        caution_groups=caution_groups,
        element_fits=element_fits,
        role_fits=role_fits,
        domain_focus_groups=DOMAIN_FOCUS_GROUPS,
        decision_notes=_unique(notes),
        month_hidden_phase=month_hidden_phase,
    )


def _position_reality_bonus(positions: list[str]) -> int:
    joined = " ".join(positions)
    score = 0
    if "month" in positions or "month" in joined:
        score += 3
    if "day" in positions or "day" in joined:
        score += 2
    if any(token in joined for token in ("stem", "visible", "flow", "daeun", "year_flow")):
        score += 2
    if any(token in joined for token in ("hidden", "branch", "root")):
        score += 1
    return score


def _reality_status(profile: MonthGovernanceProfile, elements: list[str], ten_gods: list[str], positions: list[str]) -> str:
    if profile.month_element in elements or profile.month_command_ten_god in ten_gods:
        if any("month" in item for item in positions):
            return "month_command_direct"
    relevant_protruded = any(
        STEM_METADATA.get(stem, {}).get("element") in elements
        for stem in profile.protruded_hidden_stems
    )
    if relevant_protruded:
        if any(profile.element_fits[element].month_authority == "month_hidden_protruded" for element in elements if element in profile.element_fits):
            return "protruded_month_hidden_stem"
    max_reality = max((profile.element_fits[element].reality_score for element in elements if element in profile.element_fits), default=0)
    max_reality += _position_reality_bonus(positions)
    if max_reality >= 6:
        return "visible_and_rooted"
    if max_reality >= 4:
        return "rooted_or_activated"
    if max_reality >= 2:
        return "latent_but_present"
    return "weakly_observed"


def _domain_fit(domain: str, groups: list[str], fit_status: str) -> str:
    focus = set(DOMAIN_FOCUS_GROUPS.get(domain, []))
    matched = bool(focus.intersection(groups))
    if matched and fit_status in {"supports_month_command", "usable_by_month_command"}:
        return "direct_domain_support"
    if matched and fit_status == "mixed_by_month_command":
        return "domain_support_with_burden"
    if matched and fit_status in {"harms_month_command", "burdensome_by_month_command"}:
        return "direct_domain_pressure"
    if matched:
        return "domain_relevant"
    return "domain_secondary"


def evaluate_month_governed_signal(
    profile: MonthGovernanceProfile,
    *,
    signal_key: str,
    signal_type: str,
    elements: list[str] | tuple[str, ...] = (),
    ten_gods: list[str] | tuple[str, ...] = (),
    positions: list[str] | tuple[str, ...] = (),
    domain: str = "",
) -> MonthGovernanceDecision:
    clean_elements = _unique([element for element in elements if element in profile.element_fits])
    clean_ten_gods = _unique([ten_god for ten_god in ten_gods if ten_god in TEN_GOD_GROUPS])
    groups = _unique([TEN_GOD_GROUPS[ten_god] for ten_god in clean_ten_gods])
    for element in clean_elements:
        group = next((group for group, fit in profile.role_fits.items() if fit.element == element), "")
        if group:
            groups.append(group)
    groups = _unique(groups)

    support_score = 0
    pressure_score = 0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for element in clean_elements:
        fit = profile.element_fits[element]
        support_score += fit.support_score
        pressure_score += fit.pressure_score
        basis_codes.extend(fit.basis_codes)
        counter_signals.extend(fit.counter_signals)
    for group in groups:
        fit = profile.role_fits.get(group)
        if not fit:
            continue
        # A role fit is derived from its corresponding element fit.  When both
        # are supplied they are one piece of evidence and must be counted once.
        if fit.element not in clean_elements:
            support_score += max(0, fit.support_score - 1)
            pressure_score += max(0, fit.pressure_score - 1)
        basis_codes.extend(fit.basis_codes)
        counter_signals.extend(fit.counter_signals)

    if any("month" in position for position in positions):
        support_score += 1 if support_score >= pressure_score else 0
        pressure_score += 1 if pressure_score > support_score else 0
        basis_codes.append("month_governance_touches_month_branch")
    if any("flow" in position or "daeun" in position for position in positions):
        basis_codes.append("month_governance_flow_activation")

    fit_status = _status(support_score, pressure_score)
    status_code = f"month_governance_{fit_status}"
    if fit_status in {"harms_month_command", "burdensome_by_month_command"}:
        counter_signals.append(status_code)
    else:
        basis_codes.append(status_code)
    return MonthGovernanceDecision(
        signal_key=signal_key,
        signal_type=signal_type,
        domain=domain,
        positions=list(positions),
        elements=clean_elements,
        ten_gods=clean_ten_gods,
        groups=groups,
        fit_status=fit_status,
        support_score=support_score,
        pressure_score=pressure_score,
        reality_status=_reality_status(profile, clean_elements, clean_ten_gods, list(positions)),
        domain_fit=_domain_fit(domain, groups, fit_status) if domain else "",
        basis_codes=_unique(basis_codes),
        counter_signals=_unique(counter_signals),
    )


def governance_event_adjustment(decision: MonthGovernanceDecision) -> dict[str, object]:
    support = decision.support_score
    pressure = decision.pressure_score
    domain_direct = decision.domain_fit in {"direct_domain_support", "domain_support_with_burden", "direct_domain_pressure"}
    reality_bonus = {
        "month_command_direct": 1,
        "protruded_month_hidden_stem": 1,
        "visible_and_rooted": 1,
    }.get(decision.reality_status, 0)

    opportunity = 0
    risk = 0
    probability = 0
    change = 0
    if decision.fit_status in {"supports_month_command", "usable_by_month_command"}:
        opportunity += min(5, max(1, support // 3)) + reality_bonus
        probability += 2 if domain_direct else 1
    elif decision.fit_status == "mixed_by_month_command":
        opportunity += min(3, max(1, support // 5))
        risk += min(3, max(1, pressure // 5))
        change += 1
        probability += 1 if domain_direct else 0
    elif decision.fit_status in {"harms_month_command", "burdensome_by_month_command"}:
        risk += min(5, max(1, pressure // 3)) + reality_bonus
        probability += 1 if domain_direct else 0

    return {
        "opportunity": opportunity,
        "risk": risk,
        "change": change,
        "probability": probability,
        "basis_codes": list(decision.basis_codes),
        "counter_signals": list(decision.counter_signals),
    }
