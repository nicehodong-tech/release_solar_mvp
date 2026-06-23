"""Template selection bridge for first and second sentence templates."""

from __future__ import annotations

from .models import ChartStructure, EventPacket, RelationshipStatus


DOMAIN_TEMPLATE_BY_EVENT = {
    "income_growth": "T-MONEY-HIGH",
    "managed_income_expansion": "T-MONEY-HIGH",
    "cashflow_defense": "T-MONEY-RISK",
    "income_structure_change": "T-MONEY-EARN-WITH-CAREER",
    "money_flow_adjustment": "T-MONEY-LOW",
    "role_expansion_or_transition": "T-CAREER-ROLE-UP",
    "career_recognition": "T-CAREER-ROLE-UP",
    "responsibility_pressure": "T-CAREER-CONFLICT",
    "work_environment_change": "T-CAREER-CHANGE",
    "career_pace_adjustment": "T-CAREER-STAGNANT",
    "relationship_opening": "T-LOVE-NEW",
    "relationship_with_conditions": "T-LOVE-REPAIR",
    "relationship_friction": "T-LOVE-RISK",
    "relationship_boundary_check": "T-LOVE-REPAIR",
    "relationship_expression_alignment": "T-LOVE-ATTRACTIVE",
    "relationship_recovery_check": "T-LOVE-REPAIR",
    "relationship_contact_increase": "T-LOVE-NEW",
    "relationship_temperature_shift": "T-LOVE-LOW",
    "marriage_stability_opening": "T-MARRIAGE-HIGH",
    "marriage_condition_check": "T-MARRIAGE-MID",
    "marriage_pressure": "T-MARRIAGE-RISK",
    "marriage_commitment_readiness": "T-MARRIAGE-HIGH",
    "marriage_practical_planning": "T-MARRIAGE-MID",
    "marriage_asset_condition_check": "T-MARRIAGE-MID",
    "marriage_decision_alignment": "T-MARRIAGE-MID",
    "marriage_timing_adjustment": "T-MARRIAGE-MID",
}

TYPE_TEMPLATE_BY_PATTERN = {
    "output_to_wealth": "T-TYPE-SIKSANG-SAENGJAE",
    "officer_resource": "T-TYPE-GWANIN-SANGSAENG",
    "resource_supported": "T-TYPE-STRONG-INSEONG",
    "wealth_pressure": "T-TYPE-JAEDA-SINYAK",
    "peer_wealth_competition": "T-TYPE-BIGYEOP-JAE",
    "cold_storage_needs_fire": "T-TYPE-COLD-DAMP",
    "hot_dry_needs_water": "T-TYPE-HOT-DRY",
    "direct_wealth_pattern": "T-TYPE-JAE-GWAN-IN",
    "indirect_wealth_pattern": "T-TYPE-JAE-GWAN-IN",
    "direct_officer_pattern": "T-TYPE-GWANIN-SANGSAENG",
    "seven_killings_pattern": "T-TYPE-GWANSAL-MIXED",
    "eating_god_pattern": "T-TYPE-SIKSANG-SAENGJAE",
    "hurting_officer_pattern": "T-TYPE-STRONG-SIKSANG",
    "direct_resource_pattern": "T-TYPE-STRONG-INSEONG",
    "indirect_resource_pattern": "T-TYPE-STRONG-INSEONG",
    "jianlu_peer_pattern": "T-TYPE-BIGYEOP-JAE",
    "yangren_peer_pattern": "T-TYPE-BIGYEOP-JAE",
}


def select_common_template(packet: EventPacket) -> str:
    opportunity = packet.opportunity_score
    risk = packet.risk_score
    if opportunity >= 75 and risk >= 70:
        return "T-COMMON-OPEN-WITH-RISK"
    if opportunity >= 80 and risk < 70:
        return "T-COMMON-OPEN-HIGH"
    if 60 <= opportunity <= 79 and risk < 70:
        return "T-COMMON-OPEN-MID"
    if 60 <= opportunity <= 74 and risk >= 70:
        return "T-COMMON-CAUTIOUS-CHANGE"
    if opportunity < 60 and risk >= 65:
        return "T-COMMON-DEFENSE"
    if 40 <= opportunity <= 59 and risk < 65:
        return "T-COMMON-PREPARE"
    return "T-COMMON-QUIET"


def select_domain_template(packet: EventPacket, relationship_status: RelationshipStatus = "unknown") -> str:
    if packet.domain == "love":
        if relationship_status in {"single", "interested"} and packet.opportunity_score >= 60:
            return "T-LOVE-NEW"
        if relationship_status in {"dating", "long_term", "preparing_marriage", "married"}:
            if packet.risk_score >= 70:
                return "T-LOVE-RISK"
            if packet.risk_score >= 55:
                return "T-LOVE-REPAIR"
            return "T-LOVE-ATTRACTIVE"
    if packet.domain == "marriage":
        if relationship_status == "single":
            return "T-MARRIAGE-SINGLE"
        if relationship_status == "interested":
            return "T-MARRIAGE-INTERESTED"
        if relationship_status in {"dating", "long_term"}:
            return "T-MARRIAGE-DATING"
        if relationship_status == "preparing_marriage":
            return "T-MARRIAGE-PREPARING"
        if relationship_status == "married":
            return "T-MARRIAGE-MARRIED"
    return DOMAIN_TEMPLATE_BY_EVENT.get(packet.sub_event_type, f"T-{packet.domain.upper()}-GENERIC")


def select_type_template(structure: ChartStructure) -> str:
    profile = structure.pattern_profile
    pattern_name = profile.primary_pattern
    if pattern_name in TYPE_TEMPLATE_BY_PATTERN:
        return TYPE_TEMPLATE_BY_PATTERN[pattern_name]
    if profile.regular_pattern in TYPE_TEMPLATE_BY_PATTERN:
        return TYPE_TEMPLATE_BY_PATTERN[profile.regular_pattern]
    if profile.pattern_family == "special_watch":
        return "T-TYPE-SPECIAL-PATTERN-CANDIDATE"
    if profile.pattern_family == "mixed":
        return "T-TYPE-MIXED"
    return "T-TYPE-MIXED"


def build_template_slots(packet: EventPacket, structure: ChartStructure, relationship_status: RelationshipStatus = "unknown") -> dict[str, object]:
    return {
        "domain": packet.domain,
        "period_label": packet.period_label,
        "confidence": packet.confidence,
        "domain_opportunity_score": packet.opportunity_score,
        "domain_risk_score": packet.risk_score,
        "change_score": packet.change_score,
        "event_candidates": packet.event_form,
        "event_keywords": packet.event_keywords,
        "main_action": packet.main_action,
        "risk_topic": packet.risk_topic,
        "primary_scene_sentence": packet.primary_scene_sentence,
        "past_check_status": packet.past_check_status,
        "relationship_status": relationship_status,
        "primary_chart_type": structure.pattern_profile.primary_pattern,
        "regular_pattern": structure.pattern_profile.regular_pattern,
        "type_confidence": structure.pattern_profile.pattern_confidence,
        "active_chart_type": structure.pattern_profile.primary_pattern,
        "active_type_role": structure.pattern_profile.pattern_family,
        "active_type_confidence": structure.pattern_profile.pattern_confidence,
        "timing_markers": packet.timing_markers,
        "timing_windows": packet.timing_windows,
        "monthly_phase": packet.timing_windows[0]["monthly_phase"] if packet.timing_windows else "unknown",
        "feature_axes": packet.feature_axes,
    }
