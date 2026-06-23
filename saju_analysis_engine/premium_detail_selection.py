"""Selection layer for premium detailed judgment dictionary.

The dictionary owns the customer-facing judgment assets. This selector reads
already-built analysis output and decides which entries fit the current chart.
It does not recalculate the chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import AnalysisResult, EventPacket, PremiumDetailMatch
from .premium_detail_dictionary import (
    PREMIUM_DETAIL_DICTIONARY,
    PREMIUM_DETAIL_DICTIONARY_VERSION,
    PremiumDetailEntry,
    premium_detail_entry,
)


PREMIUM_DETAIL_SELECTION_VERSION = "premium_detail_selection_v1"


@dataclass(frozen=True)
class PremiumDetailRule:
    entry_key: str
    domain: str
    narrative_group: str
    priority: int
    source_domains: tuple[str, ...] = ()
    code_needles: tuple[str, ...] = ()
    event_needles: tuple[str, ...] = ()
    feature_axis_needles: tuple[str, ...] = ()
    base_score: int = 18
    opportunity_weight: float = 0.05
    risk_weight: float = 0.05
    change_weight: float = 0.03
    probability_weight: float = 0.04


@dataclass(frozen=True)
class PremiumDetailSelectionResult:
    version: str
    matches: list[PremiumDetailMatch]
    suppressed_matches: list[PremiumDetailMatch]


def premium_detail_rules() -> tuple[PremiumDetailRule, ...]:
    return _PREMIUM_DETAIL_RULES


def build_premium_detail_selection(
    analysis: AnalysisResult,
    *,
    threshold: int = 44,
    total_limit: int = 32,
) -> PremiumDetailSelectionResult:
    """Select premium dictionary entries for a chart."""

    code_space_by_domain = _code_space_by_domain(analysis)
    event_terms_by_domain = _event_terms_by_domain(analysis)
    feature_axes_by_domain = _feature_axes_by_domain(analysis)
    axis_scores_by_domain = _axis_scores_by_domain(analysis)
    packet_scores_by_domain = _packet_scores_by_domain(analysis)

    candidates: list[PremiumDetailMatch] = []
    for rule in _PREMIUM_DETAIL_RULES:
        entry = premium_detail_entry(rule.entry_key)
        if entry is None:
            continue
        domains = _source_domains(rule)
        code_space = _merged(code_space_by_domain, domains)
        event_terms = _merged(event_terms_by_domain, domains)
        feature_axes = _merged(feature_axes_by_domain, domains)
        axis_scores = _merged_axis_scores(axis_scores_by_domain, domains)
        score = _score_rule(
            rule,
            packet_scores_by_domain,
            domains,
            code_space,
            event_terms,
            feature_axes,
            axis_scores,
        )
        if score < threshold:
            continue
        matched_codes = _matched_needles(rule.code_needles, code_space)
        matched_events = _matched_needles(rule.event_needles, event_terms)
        matched_axes = _matched_needles(rule.feature_axis_needles, feature_axes)
        candidates.append(
            _match_from_entry(
                entry,
                rule=rule,
                score=score,
                matched_codes=matched_codes,
                matched_event_terms=matched_events,
                matched_feature_axes=matched_axes,
            )
        )

    selected, suppressed = _select_by_domain_and_group(candidates, total_limit)
    return PremiumDetailSelectionResult(
        version=PREMIUM_DETAIL_SELECTION_VERSION,
        matches=selected,
        suppressed_matches=suppressed,
    )


def validate_premium_detail_selection_static_contract() -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for rule in _PREMIUM_DETAIL_RULES:
        if rule.entry_key in seen:
            issues.append(f"duplicate premium detail rule: {rule.entry_key}")
        seen.add(rule.entry_key)
        entry = PREMIUM_DETAIL_DICTIONARY.get(rule.entry_key)
        if entry is None:
            issues.append(f"missing dictionary entry for rule: {rule.entry_key}")
            continue
        if entry.domain != rule.domain:
            issues.append(f"{rule.entry_key}: rule domain does not match dictionary domain")
        if not (rule.code_needles or rule.event_needles or rule.feature_axis_needles):
            issues.append(f"{rule.entry_key}: rule has no selection needles")
    missing_rules = sorted(set(PREMIUM_DETAIL_DICTIONARY) - seen)
    for key in missing_rules:
        issues.append(f"dictionary entry has no selection rule: {key}")
    return issues


def _source_domains(rule: PremiumDetailRule) -> tuple[str, ...]:
    if rule.source_domains:
        return rule.source_domains
    if rule.domain == "personality":
        return ("money", "career", "love", "marriage")
    if rule.domain == "honor":
        return ("career", "money")
    if rule.domain == "social":
        return ("love", "marriage", "career", "money")
    if rule.domain in {"life_period", "timing"}:
        return ("money", "career", "love", "marriage")
    return (rule.domain,)


def _match_from_entry(
    entry: PremiumDetailEntry,
    *,
    rule: PremiumDetailRule,
    score: int,
    matched_codes: list[str],
    matched_event_terms: list[str],
    matched_feature_axes: list[str],
) -> PremiumDetailMatch:
    level = _level_for_score(score)
    judgment = {
        "strong": entry.strong_judgment,
        "moderate": entry.moderate_judgment,
        "weak": entry.weak_judgment,
    }[level]
    return PremiumDetailMatch(
        entry_key=entry.key,
        domain=entry.domain,
        title=entry.title,
        narrative_group=rule.narrative_group,
        score=score,
        level=level,
        priority=rule.priority,
        judgment=judgment,
        event_scenes=list(entry.event_scenes),
        premium_notes=list(entry.premium_notes),
        caution_targets=list(entry.caution_targets),
        timing_keywords=list(entry.timing_keywords),
        matched_codes=matched_codes[:10],
        matched_event_terms=matched_event_terms[:8],
        matched_feature_axes=matched_feature_axes[:8],
        engine_signal_hints=list(entry.engine_signal_hints),
        dictionary_version=PREMIUM_DETAIL_DICTIONARY_VERSION,
        selection_version=PREMIUM_DETAIL_SELECTION_VERSION,
    )


def _level_for_score(score: int) -> str:
    if score >= 74:
        return "strong"
    if score >= 56:
        return "moderate"
    return "weak"


def _score_rule(
    rule: PremiumDetailRule,
    packet_scores_by_domain: dict[str, dict[str, int]],
    domains: tuple[str, ...],
    code_space: list[str],
    event_terms: list[str],
    feature_axes: list[str],
    axis_scores: list[dict[str, Any]],
) -> int:
    matched_codes = _matched_needles(rule.code_needles, code_space)
    matched_events = _matched_needles(rule.event_needles, event_terms)
    matched_axes = _matched_needles(rule.feature_axis_needles, feature_axes)
    packet_score = _best_packet_score(packet_scores_by_domain, domains)
    axis_score = _axis_score_for_needles(rule.feature_axis_needles, axis_scores)
    axis_adjustment = _axis_adjustment(rule.entry_key, axis_score)
    score = (
        rule.base_score
        + min(len(matched_codes), 3) * 5
        + min(len(matched_events), 3) * 6
        + min(len(matched_axes), 2) * 7
        + axis_adjustment
        + int(packet_score["opportunity"] * rule.opportunity_weight)
        + int(packet_score["risk"] * rule.risk_weight)
        + int(packet_score["change"] * rule.change_weight)
        + int(packet_score["probability"] * rule.probability_weight)
    )
    return max(0, min(100, score))


def _axis_adjustment(entry_key: str, axis_score: int | None) -> int:
    if axis_score is None:
        return 0
    risk_like_fragments = (
        "loss",
        "risk",
        "shortfall",
        "unstable",
        "conflict",
        "damage",
        "burden",
        "intrusion",
        "volatility",
        "authority_gap",
        "credit_taken",
        "unwritten",
        "guarantee",
        "old_hurt",
        "speech",
        "caution",
    )
    if any(fragment in entry_key for fragment in risk_like_fragments):
        return max(-8, min(12, int((68 - axis_score) * 0.28)))
    return max(-8, min(12, int((axis_score - 58) * 0.24)))


def _axis_score_for_needles(
    needles: tuple[str, ...],
    axis_scores: list[dict[str, Any]],
) -> int | None:
    scores: list[int] = []
    for needle in needles:
        lower_needle = needle.lower()
        matched: list[int] = []
        for axis in axis_scores:
            text = " ".join(
                str(axis.get(key) or "")
                for key in ("key", "category", "label", "strength_label", "percentile_label")
            ).lower()
            if lower_needle in text:
                value = axis.get("score")
                if isinstance(value, int) and not isinstance(value, bool):
                    matched.append(value)
        if matched:
            scores.append(max(matched))
    if not scores:
        return None
    return int(sum(scores) / len(scores))


def _best_packet_score(
    packet_scores_by_domain: dict[str, dict[str, int]],
    domains: tuple[str, ...],
) -> dict[str, int]:
    best = {"opportunity": 0, "risk": 0, "change": 0, "probability": 0}
    for domain in domains:
        scores = packet_scores_by_domain.get(domain, {})
        for key in best:
            best[key] = max(best[key], int(scores.get(key, 0)))
    return best


def _select_by_domain_and_group(
    candidates: list[PremiumDetailMatch],
    total_limit: int,
) -> tuple[list[PremiumDetailMatch], list[PremiumDetailMatch]]:
    domain_limits = {
        "money": 4,
        "career": 4,
        "love": 3,
        "marriage": 3,
        "honor": 3,
        "social": 3,
        "personality": 3,
        "life_period": 3,
        "timing": 2,
    }
    ordered = sorted(candidates, key=lambda item: (-item.score, item.priority, item.entry_key))
    selected: list[PremiumDetailMatch] = []
    suppressed: list[PremiumDetailMatch] = []
    used_groups: set[tuple[str, str]] = set()
    domain_counts: dict[str, int] = {}
    for candidate in ordered:
        group_key = (candidate.domain, candidate.narrative_group)
        if group_key in used_groups:
            suppressed.append(candidate)
            continue
        if domain_counts.get(candidate.domain, 0) >= domain_limits.get(candidate.domain, 2):
            suppressed.append(candidate)
            continue
        if len(selected) >= total_limit:
            suppressed.append(candidate)
            continue
        selected.append(candidate)
        used_groups.add(group_key)
        domain_counts[candidate.domain] = domain_counts.get(candidate.domain, 0) + 1
    return selected, suppressed


def _code_space_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    global_terms = _structure_terms(analysis)
    for packet in analysis.event_packets:
        terms = _packet_terms(packet) + global_terms
        by_domain.setdefault(packet.domain, []).extend(terms)
    for domain in list(by_domain):
        by_domain[domain] = _dedupe_texts(by_domain[domain])
    return by_domain


def _event_terms_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    for packet in analysis.event_packets:
        terms = [
            packet.sub_event_type,
            packet.event_form,
            packet.realization_path,
            packet.risk_path,
            packet.primary_scene_sentence,
            packet.main_action,
            packet.risk_topic,
            packet.personality_filter,
            *packet.event_keywords,
            *packet.timing_markers,
        ]
        by_domain.setdefault(packet.domain, []).extend(str(term) for term in terms if term)
    for domain in list(by_domain):
        by_domain[domain] = _dedupe_texts(by_domain[domain])
    return by_domain


def _feature_axes_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    for packet in analysis.event_packets:
        terms: list[str] = []
        for axis in packet.feature_axes:
            if not isinstance(axis, dict):
                continue
            terms.extend(
                str(axis.get(key) or "")
                for key in ("key", "category", "label", "strength_label", "percentile_label")
            )
            terms.extend(str(code) for code in axis.get("basis_codes", []) if code)
            terms.extend(str(code) for code in axis.get("counter_signals", []) if code)
        by_domain.setdefault(packet.domain, []).extend(term for term in terms if term)
    for domain in list(by_domain):
        by_domain[domain] = _dedupe_texts(by_domain[domain])
    return by_domain


def _axis_scores_by_domain(analysis: AnalysisResult) -> dict[str, list[dict[str, Any]]]:
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for packet in analysis.event_packets:
        axes: list[dict[str, Any]] = []
        for axis in packet.feature_axes:
            if not isinstance(axis, dict):
                continue
            value = axis.get("score")
            if not isinstance(value, int) or isinstance(value, bool):
                continue
            axes.append(
                {
                    "key": str(axis.get("key") or ""),
                    "category": str(axis.get("category") or ""),
                    "label": str(axis.get("label") or ""),
                    "strength_label": str(axis.get("strength_label") or ""),
                    "percentile_label": str(axis.get("percentile_label") or ""),
                    "score": value,
                }
            )
        by_domain.setdefault(packet.domain, []).extend(axes)
    return by_domain


def _packet_scores_by_domain(analysis: AnalysisResult) -> dict[str, dict[str, int]]:
    scores: dict[str, dict[str, int]] = {}
    for packet in analysis.event_packets:
        current = scores.setdefault(
            packet.domain,
            {"opportunity": 0, "risk": 0, "change": 0, "probability": 0},
        )
        current["opportunity"] = max(current["opportunity"], int(packet.opportunity_score))
        current["risk"] = max(current["risk"], int(packet.risk_score))
        current["change"] = max(current["change"], int(packet.change_score))
        current["probability"] = max(current["probability"], int(packet.event_probability_score))
    return scores


def _packet_terms(packet: EventPacket) -> list[str]:
    terms = [
        packet.packet_id,
        packet.domain,
        packet.sub_event_type,
        packet.period_label,
        packet.period_scope,
        packet.event_form,
        packet.realization_path,
        packet.risk_path,
        packet.timing_strength,
        packet.primary_scene_sentence,
        packet.main_action,
        packet.risk_topic,
        packet.personality_filter,
        packet.conflict_status,
        packet.output_allowed_level,
        packet.common_template_id,
        packet.domain_template_id,
        packet.type_template_id,
        packet.relationship_status,
        *packet.domain_links,
        *packet.basis_codes,
        *packet.counter_signals,
        *packet.event_keywords,
        *packet.timing_markers,
    ]
    for window in packet.timing_windows:
        if isinstance(window, dict):
            terms.extend(str(value) for value in window.values() if value)
    return [str(term) for term in terms if term]


def _structure_terms(analysis: AnalysisResult) -> list[str]:
    structure = analysis.chart_structure
    terms: list[str] = [
        structure.day_master_stem,
        structure.day_master_element,
        structure.month_branch,
        structure.season_label,
        *structure.structure_tags,
    ]
    month = structure.month_governance_profile
    terms.extend(
        [
            month.month_branch,
            month.month_element,
            month.month_command_ten_god,
            month.month_command_group,
            month.regular_pattern,
            month.pattern_family,
            *month.useful_elements,
            *month.caution_elements,
            *month.useful_groups,
            *month.caution_groups,
            *month.protruded_hidden_stems,
        ]
    )
    for signal in structure.position_signals.values():
        terms.extend(
            [
                signal.position,
                signal.pillar,
                signal.stem_key,
                signal.branch_key,
                signal.stem_element,
                signal.branch_element,
                signal.stem_ten_god,
                signal.branch_main_ten_god,
                *signal.hidden_ten_gods,
                *signal.domains,
                *signal.protruded_hidden_stems,
            ]
        )
    for relation in structure.branch_interactions:
        terms.extend(
            [
                relation.relation_type,
                *relation.branches,
                *relation.positions,
                *relation.domain_links,
                relation.effect_element or "",
                relation.intensity,
                relation.basis_code,
            ]
        )
    return [str(term) for term in terms if term]


def _merged(source: dict[str, list[str]], domains: tuple[str, ...]) -> list[str]:
    terms: list[str] = []
    for domain in domains:
        terms.extend(source.get(domain, []))
    return _dedupe_texts(terms)


def _merged_axis_scores(
    source: dict[str, list[dict[str, Any]]],
    domains: tuple[str, ...],
) -> list[dict[str, Any]]:
    axes: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for domain in domains:
        for axis in source.get(domain, []):
            key = (
                str(axis.get("key") or ""),
                str(axis.get("label") or ""),
                int(axis.get("score") or 0),
            )
            if key in seen:
                continue
            seen.add(key)
            axes.append(axis)
    return axes


def _matched_needles(needles: tuple[str, ...], values: list[str]) -> list[str]:
    matches: list[str] = []
    lower_values = [value.lower() for value in values]
    for needle in needles:
        lower_needle = needle.lower()
        if any(lower_needle in value for value in lower_values):
            matches.append(needle)
    return matches


def _dedupe_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


_PREMIUM_DETAIL_RULES: tuple[PremiumDetailRule, ...] = (
    PremiumDetailRule("money_close_person_loss", "money", "money_people_loss", 10, code_needles=("peer", "geob_jae", "shared_control", "controls_peer_to_wealth", "settlement", "wealth"), event_needles=("공동", "정산", "지출", "가족", "계약"), feature_axis_needles=("asset_retention", "boundary_management", "family_responsibility"), risk_weight=0.12),
    PremiumDetailRule("money_unwritten_agreement_loss", "money", "money_contract_loss", 20, code_needles=("contract", "officer", "resource", "harm", "break", "wealth"), event_needles=("계약", "정산", "잔금", "기준", "책임"), feature_axis_needles=("deal_selection", "loss_avoidance", "decision_consistency"), risk_weight=0.12),
    PremiumDetailRule("money_reward_shortfall", "money", "money_reward_gap", 30, code_needles=("output", "wealth", "officer", "recognition", "income_expansion"), event_needles=("성과", "보상", "평가", "역할", "수입"), feature_axis_needles=("income_expansion", "career_achievement", "reputation_maintenance"), opportunity_weight=0.09, risk_weight=0.08),
    PremiumDetailRule("money_skill_income_conversion", "money", "money_skill_income", 40, code_needles=("output_generates_wealth", "output_to_wealth", "eating_god", "hurting_officer", "income_material"), event_needles=("성과", "거래", "고객", "수입", "계약"), feature_axis_needles=("income_expansion", "business_expansion", "career_achievement"), opportunity_weight=0.12),
    PremiumDetailRule("money_asset_retention", "money", "money_asset_retention", 50, code_needles=("asset_retention", "wealth", "resource", "root", "branch"), event_needles=("자산", "고정", "관리형 수입", "주거", "명의"), feature_axis_needles=("asset_retention", "spending_control", "practical_planning"), opportunity_weight=0.08),
    PremiumDetailRule("money_investment_volatility", "money", "money_investment_risk", 60, code_needles=("indirect_wealth", "pyeon_jae", "clash", "punishment", "break", "risk"), event_needles=("투자", "손실", "변화", "계약", "회수"), feature_axis_needles=("loss_avoidance", "investment_trading_sense", "deal_selection"), risk_weight=0.15, change_weight=0.08),
    PremiumDetailRule("money_business_expansion_pressure", "money", "money_expansion_pressure", 70, code_needles=("business_expansion", "wealth_generates_officer", "strained_generation", "officer", "fixed"), event_needles=("확장", "대출", "고정", "비용", "역할"), feature_axis_needles=("business_expansion", "income_expansion", "responsibility_capacity"), opportunity_weight=0.08, risk_weight=0.1),
    PremiumDetailRule("money_spouse_family_asset", "money", "money_family_asset", 80, source_domains=("money", "marriage"), code_needles=("marriage", "family", "wealth", "asset", "day"), event_needles=("가족", "경제 조건", "주거", "명의", "지출"), feature_axis_needles=("family_responsibility", "asset_retention", "marriage_stability"), risk_weight=0.11),
    PremiumDetailRule("money_debt_guarantee", "money", "money_debt_guarantee", 90, code_needles=("peer", "wealth", "officer", "risk", "counter", "clash"), event_needles=("대출", "책임", "지출", "계약", "가족"), feature_axis_needles=("loss_avoidance", "deal_selection", "family_responsibility"), risk_weight=0.15),
    PremiumDetailRule("career_authority_gap", "career", "career_authority_gap", 100, code_needles=("authority", "responsibility", "officer", "counter", "role_expansion"), event_needles=("권한", "책임", "평가", "역할", "상사"), feature_axis_needles=("responsibility_capacity", "organization_adaptability", "decision_consistency"), risk_weight=0.12),
    PremiumDetailRule("career_credit_taken", "career", "career_credit_taken", 110, code_needles=("output", "recognition", "peer", "officer", "result"), event_needles=("성과", "평가", "역할", "보상", "책임"), feature_axis_needles=("career_achievement", "reputation_maintenance", "income_expansion"), opportunity_weight=0.08, risk_weight=0.1),
    PremiumDetailRule("career_specialist_recognition", "career", "career_specialist", 120, code_needles=("resource", "officer", "expertise", "credential", "recognition"), event_needles=("전문", "평가", "자격", "역할", "공식"), feature_axis_needles=("academic_expertise", "career_achievement", "reputation_maintenance"), opportunity_weight=0.11),
    PremiumDetailRule("career_unstable_organization", "career", "career_unstable_org", 130, code_needles=("counter", "break", "harm", "authority", "responsibility"), event_needles=("근무 환경", "변화", "책임", "기준", "업무"), feature_axis_needles=("organization_adaptability", "crisis_recovery", "decision_consistency"), risk_weight=0.14, change_weight=0.08),
    PremiumDetailRule("career_independent_business", "career", "career_independent", 140, source_domains=("career", "money"), code_needles=("output", "wealth", "business_expansion", "indirect_wealth", "peer"), event_needles=("사업", "고객", "계약", "수입", "확장"), feature_axis_needles=("business_expansion", "income_expansion", "career_achievement"), opportunity_weight=0.11, risk_weight=0.08),
    PremiumDetailRule("career_operational_control", "career", "career_operation", 150, code_needles=("operation", "officer", "resource", "earth", "metal", "responsibility"), event_needles=("운영", "업무", "역할", "기준", "평가"), feature_axis_needles=("organization_adaptability", "responsibility_capacity", "practical_planning"), opportunity_weight=0.09),
    PremiumDetailRule("career_public_system_fit", "career", "career_system_fit", 160, code_needles=("officer_resource", "resource", "officer", "regular_pattern", "credential"), event_needles=("공식", "평가", "자격", "책임", "기관"), feature_axis_needles=("academic_expertise", "organization_adaptability", "reputation_maintenance"), opportunity_weight=0.09),
    PremiumDetailRule("career_sales_network_profit", "career", "career_network_sales", 170, source_domains=("career", "money"), code_needles=("output", "wealth", "network", "market_response", "relationship"), event_needles=("거래", "고객", "제휴", "소개", "수입"), feature_axis_needles=("interpersonal_influence", "business_expansion", "income_expansion"), opportunity_weight=0.11),
    PremiumDetailRule("love_slow_expression", "love", "love_expression_delay", 200, code_needles=("resource", "officer", "expression", "relationship", "counter"), event_needles=("연락", "표현", "오해", "거리", "감정"), feature_axis_needles=("communication_expression", "relationship_stability", "boundary_management"), risk_weight=0.11),
    PremiumDetailRule("love_unstable_partner", "love", "love_unstable_partner", 210, code_needles=("clash", "punishment", "harm", "relationship", "counter"), event_needles=("감정 충돌", "거리 조정", "기대 차이", "연락", "관계"), feature_axis_needles=("relationship_stability", "conflict_recovery", "boundary_management"), risk_weight=0.14, change_weight=0.08),
    PremiumDetailRule("love_official_relationship", "love", "love_official", 220, source_domains=("love", "marriage"), code_needles=("officer", "combine", "marriage", "relationship", "stable"), event_needles=("만남", "약속", "관계", "가족", "결정"), feature_axis_needles=("relationship_stability", "decision_consistency", "marriage_stability"), opportunity_weight=0.1),
    PremiumDetailRule("love_old_hurt_return", "love", "love_old_hurt", 230, code_needles=("harm", "break", "punishment", "relationship", "resource"), event_needles=("서운", "오해", "감정", "회복", "거리"), feature_axis_needles=("conflict_recovery", "communication_expression", "relationship_stability"), risk_weight=0.13),
    PremiumDetailRule("marriage_family_money_conflict", "marriage", "marriage_family_money", 300, source_domains=("marriage", "money"), code_needles=("family", "wealth", "resource", "marriage", "day"), event_needles=("가족", "경제 조건", "주거", "책임", "지출"), feature_axis_needles=("family_responsibility", "asset_retention", "practical_planning"), risk_weight=0.13),
    PremiumDetailRule("marriage_stable_partner", "marriage", "marriage_stable_partner", 310, code_needles=("officer", "wealth", "combine", "stable", "resource"), event_needles=("생활 합의", "결혼", "가족", "경제 조건", "결정"), feature_axis_needles=("marriage_stability", "spouse_match_quality", "decision_consistency"), opportunity_weight=0.1),
    PremiumDetailRule("marriage_commitment_delay", "marriage", "marriage_delay", 315, code_needles=("marriage", "relationship", "resource", "combine", "clash"), event_needles=("결혼", "주거", "가족", "결정", "약속"), feature_axis_needles=("marriage_stability", "decision_consistency", "practical_planning"), risk_weight=0.1, change_weight=0.07),
    PremiumDetailRule("marriage_privacy_intrusion", "marriage", "marriage_boundary", 320, code_needles=("peer", "resource", "officer", "clash", "relationship_boundary"), event_needles=("가족", "책임", "거리", "생활", "갈등"), feature_axis_needles=("boundary_management", "family_responsibility", "conflict_recovery"), risk_weight=0.13),
    PremiumDetailRule("marriage_spouse_power_conflict", "marriage", "marriage_power", 325, code_needles=("officer", "peer", "day", "clash", "responsibility"), event_needles=("결정", "생활", "주거", "가족", "갈등"), feature_axis_needles=("decision_consistency", "family_responsibility", "conflict_recovery"), risk_weight=0.13, change_weight=0.06),
    PremiumDetailRule("honor_reputation_by_role", "honor", "honor_role", 400, code_needles=("officer", "recognition", "role", "responsibility", "wealth_generates_officer"), event_needles=("평가", "역할", "책임", "공식", "승진"), feature_axis_needles=("reputation_maintenance", "career_achievement", "responsibility_capacity"), opportunity_weight=0.1),
    PremiumDetailRule("honor_reputation_loss_by_money", "honor", "honor_money_loss", 410, source_domains=("money", "career"), code_needles=("wealth", "officer", "risk", "contract", "peer"), event_needles=("정산", "계약", "책임", "평가", "손실"), feature_axis_needles=("loss_avoidance", "reputation_maintenance", "deal_selection"), risk_weight=0.14),
    PremiumDetailRule("honor_exam_credential", "honor", "honor_credential", 420, source_domains=("career",), code_needles=("resource", "officer", "credential", "academic", "recognition"), event_needles=("자격", "평가", "공식", "전문", "역할"), feature_axis_needles=("academic_expertise", "reputation_maintenance", "career_achievement"), opportunity_weight=0.1),
    PremiumDetailRule("honor_speech_damage", "honor", "honor_speech_damage", 430, source_domains=("career", "love"), code_needles=("hurting_officer", "output", "officer", "counter", "speech"), event_needles=("말", "감정", "평가", "갈등", "오해"), feature_axis_needles=("communication_expression", "reputation_maintenance", "conflict_recovery"), risk_weight=0.14),
    PremiumDetailRule("honor_public_scrutiny", "honor", "honor_public_scrutiny", 440, source_domains=("career", "money"), code_needles=("output", "officer", "recognition", "responsibility", "result"), event_needles=("평가", "공식", "성과", "책임", "심사"), feature_axis_needles=("career_achievement", "reputation_maintenance", "responsibility_capacity"), opportunity_weight=0.09, risk_weight=0.08),
    PremiumDetailRule("social_favor_to_burden", "social", "social_favor_burden", 500, code_needles=("peer", "resource", "responsibility", "support", "wealth"), event_needles=("부탁", "책임", "가족", "지출", "관계"), feature_axis_needles=("interpersonal_influence", "family_responsibility", "responsibility_capacity"), risk_weight=0.12),
    PremiumDetailRule("social_competitive_jealousy", "social", "social_competition", 510, code_needles=("peer", "output", "wealth", "competition", "recognition"), event_needles=("성과", "평가", "관계", "갈등", "역할"), feature_axis_needles=("leadership_potential", "reputation_maintenance", "interpersonal_influence"), risk_weight=0.11),
    PremiumDetailRule("social_senior_helper", "social", "social_helper", 520, source_domains=("career", "money"), code_needles=("resource", "officer", "support", "useful", "combine"), event_needles=("도움", "평가", "공식", "자격", "역할"), feature_axis_needles=("academic_expertise", "organization_adaptability", "career_achievement"), opportunity_weight=0.1),
    PremiumDetailRule("social_boundary_cutoff", "social", "social_boundary", 530, code_needles=("peer", "officer", "resource", "harm", "relationship_boundary"), event_needles=("부탁", "거리", "갈등", "가족", "책임"), feature_axis_needles=("boundary_management", "conflict_recovery", "relationship_stability"), risk_weight=0.12, change_weight=0.06),
    PremiumDetailRule("social_public_trust", "social", "social_public_trust", 540, source_domains=("career", "love", "marriage"), code_needles=("officer", "resource", "trust", "regular_pattern", "responsibility"), event_needles=("공식", "평가", "약속", "관계", "역할"), feature_axis_needles=("reputation_maintenance", "relationship_stability", "responsibility_capacity"), opportunity_weight=0.1, probability_weight=0.06),
    PremiumDetailRule("personality_controlled_drive", "personality", "personality_drive", 600, code_needles=("peer", "officer", "resource", "strong_day_master", "control"), event_needles=("판단", "결정", "책임", "기준", "역할"), feature_axis_needles=("self_direction", "decision_consistency", "leadership_potential"), opportunity_weight=0.07),
    PremiumDetailRule("personality_many_interests", "personality", "personality_interests", 610, code_needles=("resource", "output", "water", "wood", "draining"), event_needles=("기획", "변화", "준비", "역할", "성과"), feature_axis_needles=("academic_expertise", "communication_expression", "business_expansion"), change_weight=0.08),
    PremiumDetailRule("personality_loss_and_status", "personality", "personality_status", 620, code_needles=("wealth", "officer", "reputation", "responsibility", "resource"), event_needles=("평가", "돈", "책임", "기준", "관계"), feature_axis_needles=("money_potential", "reputation_maintenance", "loss_avoidance"), risk_weight=0.08),
    PremiumDetailRule("life_youth_family_distance", "life_period", "life_youth_family", 700, code_needles=("year", "month", "resource", "family", "harm"), event_needles=("가족", "책임", "거리", "감정", "기준"), feature_axis_needles=("family_responsibility", "boundary_management", "relationship_stability"), risk_weight=0.08),
    PremiumDetailRule("life_middle_age_asset_push", "life_period", "life_middle_asset", 710, source_domains=("money", "career"), code_needles=("daeun", "wealth", "asset", "output", "officer"), event_needles=("자산", "수입", "역할", "평가", "계약"), feature_axis_needles=("asset_retention", "income_expansion", "career_achievement"), opportunity_weight=0.11),
    PremiumDetailRule("life_late_stability", "life_period", "life_late_stability", 720, source_domains=("money", "marriage"), code_needles=("hour", "resource", "wealth", "support", "stable"), event_needles=("자산", "생활", "가족", "안정", "주거"), feature_axis_needles=("asset_retention", "marriage_stability", "practical_planning"), opportunity_weight=0.08),
    PremiumDetailRule("life_early_career_trial", "life_period", "life_early_career", 730, source_domains=("career",), code_needles=("career", "change", "clash", "break", "officer"), event_needles=("직무 전환", "근무 환경", "변화", "역할", "책임"), feature_axis_needles=("change_adaptability", "career_achievement", "decision_consistency"), change_weight=0.1),
    PremiumDetailRule("life_middle_role_burden", "life_period", "life_middle_role", 740, source_domains=("career", "marriage", "money"), code_needles=("daeun", "officer", "responsibility", "wealth_generates_officer", "family"), event_needles=("책임", "역할", "가족", "자산", "평가"), feature_axis_needles=("responsibility_capacity", "family_responsibility", "career_achievement"), opportunity_weight=0.08, risk_weight=0.1),
    PremiumDetailRule("life_late_family_asset", "life_period", "life_late_family_asset", 750, source_domains=("money", "marriage"), code_needles=("hour", "family", "asset", "wealth", "resource"), event_needles=("자산", "가족", "명의", "주거", "지출"), feature_axis_needles=("asset_retention", "family_responsibility", "practical_planning"), opportunity_weight=0.07, risk_weight=0.09),
    PremiumDetailRule("timing_good_year_peak", "timing", "timing_good_peak", 800, code_needles=("useful", "support", "combine", "wealth", "officer"), event_needles=("계약", "승진", "자산", "평가", "수입"), feature_axis_needles=("income_expansion", "career_achievement", "marriage_stability"), opportunity_weight=0.12, probability_weight=0.08),
    PremiumDetailRule("timing_caution_year_loss", "timing", "timing_caution_loss", 810, code_needles=("counter", "risk", "clash", "punishment", "break", "harm"), event_needles=("손실", "갈등", "책임", "정산", "계약"), feature_axis_needles=("loss_avoidance", "deal_selection", "conflict_recovery"), risk_weight=0.14, change_weight=0.08),
    PremiumDetailRule("timing_daeun_transition_reset", "timing", "timing_daeun_transition", 820, code_needles=("daeun", "change", "clash", "useful", "counter"), event_needles=("변화", "역할", "관계", "자산", "직무 전환"), feature_axis_needles=("career_achievement", "income_expansion", "conflict_recovery"), opportunity_weight=0.07, risk_weight=0.07, change_weight=0.12),
    PremiumDetailRule("timing_relationship_formalization", "timing", "timing_relationship_formal", 830, source_domains=("love", "marriage"), code_needles=("marriage", "combine", "officer", "wealth", "stable"), event_needles=("만남", "약속", "가족", "결혼", "주거"), feature_axis_needles=("marriage_stability", "relationship_stability", "decision_consistency"), opportunity_weight=0.1, probability_weight=0.06),
)
