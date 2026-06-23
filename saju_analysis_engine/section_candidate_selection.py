"""Staged selector for candidate section-bank assets.

This module connects candidate prose assets to existing analysis output without
activating them in customer reports. It is the bridge layer between the current
engine and a larger section bank.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .domains import FEATURE_AXES_BY_DOMAIN
from .models import AnalysisResult, EventPacket
from .section_bank_candidates import CandidateSectionAsset, candidate_assets_by_key
from .section_selection import build_section_selection


CANDIDATE_SECTION_SELECTION_VERSION = "candidate_section_selection_v1"

_SUPPORTED_DOMAINS = {"money", "career", "love", "marriage", "personality", "life_timing"}
_SUPPORTED_JUDGMENT_KEYS = {
    "day_master",
    "month_command",
    "day_master_strength",
    "wealth_presence",
    "peer_wealth_contact",
    "output_to_wealth",
    "money_retention_pressure",
    "practical_output_under_pressure",
    "authority_responsibility_gap",
}
_SUPPORTED_FEATURE_AXIS_KEYS = set().union(*FEATURE_AXES_BY_DOMAIN.values())
_DOMAIN_SELECTION_LIMITS = {
    "personality": 2,
    "life_timing": 2,
    "money": 3,
    "career": 4,
    "love": 2,
    "marriage": 2,
}


@dataclass(frozen=True)
class CandidateSelectionRule:
    candidate_key: str
    domain: str
    narrative_group: str
    priority: int
    judgment_keys: tuple[str, ...] = ()
    code_needles: tuple[str, ...] = ()
    event_needles: tuple[str, ...] = ()
    feature_axis_needles: tuple[str, ...] = ()
    base_score: int = 16
    opportunity_weight: float = 0.08
    risk_weight: float = 0.08


@dataclass(frozen=True)
class CandidateSectionMatch:
    candidate_key: str
    customer_title: str
    domain: str
    narrative_group: str
    score: int
    priority: int
    matched_judgment_keys: list[str] = field(default_factory=list)
    matched_codes: list[str] = field(default_factory=list)
    matched_event_terms: list[str] = field(default_factory=list)
    selection_signal_hints: list[str] = field(default_factory=list)
    suppressed_by: str = ""


@dataclass(frozen=True)
class CandidateSectionSelectionResult:
    version: str
    matches: list[CandidateSectionMatch]
    suppressed_matches: list[CandidateSectionMatch]


def candidate_selection_rules() -> tuple[CandidateSelectionRule, ...]:
    return _CANDIDATE_SELECTION_RULES


def build_candidate_section_selection(
    analysis: AnalysisResult,
    *,
    limit: int = 12,
    threshold: int = 48,
) -> CandidateSectionSelectionResult:
    assets = candidate_assets_by_key()
    judgment_map = {
        judgment.key: judgment
        for judgment in build_section_selection(analysis).judgments
    }
    code_space_by_domain = _analysis_code_space_by_domain(analysis)
    event_terms_by_domain = _analysis_event_terms_by_domain(analysis)
    feature_axes_by_domain = _analysis_feature_axes_by_domain(analysis)

    candidates: list[CandidateSectionMatch] = []
    for rule in _CANDIDATE_SELECTION_RULES:
        asset = assets.get(rule.candidate_key)
        if asset is None:
            continue
        score, matched_judgments, matched_codes, matched_events = _score_rule(
            rule,
            analysis,
            judgment_map,
            code_space_by_domain.get(rule.domain, []),
            event_terms_by_domain.get(rule.domain, []),
            feature_axes_by_domain.get(rule.domain, []),
        )
        if score < threshold:
            continue
        candidates.append(
            CandidateSectionMatch(
                candidate_key=asset.section_key,
                customer_title=asset.customer_title,
                domain=asset.domain,
                narrative_group=asset.narrative_group,
                score=score,
                priority=rule.priority,
                matched_judgment_keys=matched_judgments,
                matched_codes=matched_codes,
                matched_event_terms=matched_events,
                selection_signal_hints=list(asset.selection_signal_hints),
            )
        )

    matches, suppressed = _dedupe_candidate_matches(candidates, limit)
    return CandidateSectionSelectionResult(
        version=CANDIDATE_SECTION_SELECTION_VERSION,
        matches=matches,
        suppressed_matches=suppressed,
    )


def validate_candidate_selection_rules() -> list[str]:
    issues: list[str] = []
    assets = candidate_assets_by_key()
    seen: set[str] = set()

    for rule in _CANDIDATE_SELECTION_RULES:
        if rule.candidate_key in seen:
            issues.append(f"duplicate candidate selection rule: {rule.candidate_key}")
        seen.add(rule.candidate_key)

        asset = assets.get(rule.candidate_key)
        if asset is None:
            issues.append(f"{rule.candidate_key}: missing candidate asset")
            continue
        if rule.domain not in _SUPPORTED_DOMAINS:
            issues.append(f"{rule.candidate_key}: unsupported domain {rule.domain}")
        if rule.domain != asset.domain:
            issues.append(f"{rule.candidate_key}: rule domain does not match asset")
        if rule.narrative_group != asset.narrative_group:
            issues.append(f"{rule.candidate_key}: rule narrative group does not match asset")
        unsupported_judgments = [
            key for key in rule.judgment_keys if key not in _SUPPORTED_JUDGMENT_KEYS
        ]
        if unsupported_judgments:
            issues.append(
                f"{rule.candidate_key}: unsupported judgment keys {unsupported_judgments}"
            )
        if not (rule.judgment_keys or rule.code_needles or rule.event_needles or rule.feature_axis_needles):
            issues.append(f"{rule.candidate_key}: rule has no selection signals")
        unsupported_axis_needles = [
            needle
            for needle in rule.feature_axis_needles
            if not any(needle.lower() in axis_key.lower() for axis_key in _SUPPORTED_FEATURE_AXIS_KEYS)
        ]
        if unsupported_axis_needles:
            issues.append(
                f"{rule.candidate_key}: feature-axis needles do not match engine axes "
                f"{unsupported_axis_needles}"
            )

    missing_rules = sorted(set(assets) - seen)
    if missing_rules:
        issues.append(f"candidate assets without selection rules: {missing_rules}")
    return issues


def _score_rule(
    rule: CandidateSelectionRule,
    analysis: AnalysisResult,
    judgment_map: dict[str, object],
    code_space: list[str],
    event_terms: list[str],
    feature_axes: list[str],
) -> tuple[int, list[str], list[str], list[str]]:
    matched_judgments = [
        key
        for key in rule.judgment_keys
        if key in judgment_map
    ]
    judgment_score = max(
        (
            int(getattr(judgment_map[key], "score", 0))
            for key in matched_judgments
        ),
        default=0,
    )
    matched_codes = _matching_items(code_space, rule.code_needles, limit=8)
    matched_events = _matching_items(event_terms, rule.event_needles, limit=8)
    matched_axes = _matching_items(feature_axes, rule.feature_axis_needles, limit=6)
    domain_score = _domain_packet_score(analysis, rule)
    score = _clip(
        rule.base_score
        + judgment_score * 0.26
        + domain_score
        + min(len(matched_codes) * 3, 18)
        + min(len(matched_events) * 4, 20)
        + min(len(matched_axes) * 3, 12)
    )
    return score, matched_judgments, matched_codes + matched_axes, matched_events


def _domain_packet_score(analysis: AnalysisResult, rule: CandidateSelectionRule) -> float:
    if rule.domain == "personality":
        return 0.0
    packets = [packet for packet in analysis.event_packets if packet.domain == rule.domain]
    if not packets and rule.domain in {"personality", "life_timing"}:
        packets = list(analysis.event_packets)
    if not packets:
        return 0.0
    return max(
        packet.event_probability_score * 0.10
        + packet.opportunity_score * rule.opportunity_weight
        + packet.risk_score * rule.risk_weight
        for packet in packets
    )


def _analysis_code_space_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    all_codes: list[str] = []
    for packet in analysis.event_packets:
        codes = by_domain.setdefault(str(packet.domain), [])
        codes.extend(packet.basis_codes)
        codes.extend(packet.counter_signals)
        codes.append(packet.sub_event_type)
        codes.append(packet.risk_topic)
        codes.append(packet.main_action)
        all_codes.extend(codes)
    for flow in analysis.flow_signals:
        all_codes.extend(flow.basis_codes)
        all_codes.extend(flow.counter_signals)
    output = {domain: _unique_strings(codes) for domain, codes in by_domain.items()}
    output["personality"] = _unique_strings(all_codes)
    output["life_timing"] = _unique_strings(all_codes)
    return output


def _analysis_event_terms_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    all_terms: list[str] = []
    for packet in analysis.event_packets:
        terms = by_domain.setdefault(str(packet.domain), [])
        terms.extend(packet.event_keywords)
        terms.append(packet.sub_event_type)
        terms.append(packet.event_form)
        terms.append(packet.realization_path)
        terms.append(packet.risk_path)
        terms.append(packet.primary_scene_sentence)
        all_terms.extend(terms)
    output = {domain: _unique_strings(terms) for domain, terms in by_domain.items()}
    output["personality"] = _unique_strings(all_terms)
    output["life_timing"] = _unique_strings(all_terms)
    return output


def _analysis_feature_axes_by_domain(analysis: AnalysisResult) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    all_axes: list[str] = []
    for packet in analysis.event_packets:
        axes = by_domain.setdefault(str(packet.domain), [])
        for axis in packet.feature_axes:
            value = axis.get("key")
            if isinstance(value, str):
                axes.append(value)
                all_axes.append(value)
    output = {domain: _unique_strings(axes) for domain, axes in by_domain.items()}
    output["personality"] = _unique_strings(all_axes)
    output["life_timing"] = _unique_strings(all_axes)
    return output


def _matching_items(haystack: list[str], needles: tuple[str, ...], *, limit: int) -> list[str]:
    matched: list[str] = []
    for item in haystack:
        lowered = item.lower()
        if any(needle.lower() in lowered for needle in needles):
            matched.append(item)
        if len(matched) >= limit:
            break
    return matched


def _dedupe_candidate_matches(
    candidates: list[CandidateSectionMatch],
    limit: int,
) -> tuple[list[CandidateSectionMatch], list[CandidateSectionMatch]]:
    ordered = sorted(candidates, key=lambda item: (-item.score, item.priority, item.candidate_key))
    selected: list[CandidateSectionMatch] = []
    suppressed: list[CandidateSectionMatch] = []
    used_groups: dict[str, str] = {}
    used_domains: dict[str, int] = {}
    for candidate in ordered:
        if candidate.narrative_group in used_groups:
            suppressed.append(
                CandidateSectionMatch(
                    candidate_key=candidate.candidate_key,
                    customer_title=candidate.customer_title,
                    domain=candidate.domain,
                    narrative_group=candidate.narrative_group,
                    score=candidate.score,
                    priority=candidate.priority,
                    matched_judgment_keys=list(candidate.matched_judgment_keys),
                    matched_codes=list(candidate.matched_codes),
                    matched_event_terms=list(candidate.matched_event_terms),
                    selection_signal_hints=list(candidate.selection_signal_hints),
                    suppressed_by=used_groups[candidate.narrative_group],
                )
            )
            continue
        domain_limit = _DOMAIN_SELECTION_LIMITS.get(candidate.domain)
        if domain_limit is not None and used_domains.get(candidate.domain, 0) >= domain_limit:
            suppressed.append(
                CandidateSectionMatch(
                    candidate_key=candidate.candidate_key,
                    customer_title=candidate.customer_title,
                    domain=candidate.domain,
                    narrative_group=candidate.narrative_group,
                    score=candidate.score,
                    priority=candidate.priority,
                    matched_judgment_keys=list(candidate.matched_judgment_keys),
                    matched_codes=list(candidate.matched_codes),
                    matched_event_terms=list(candidate.matched_event_terms),
                    selection_signal_hints=list(candidate.selection_signal_hints),
                    suppressed_by=f"domain_limit:{candidate.domain}",
                )
            )
            continue
        if len(selected) >= limit:
            suppressed.append(
                CandidateSectionMatch(
                    candidate_key=candidate.candidate_key,
                    customer_title=candidate.customer_title,
                    domain=candidate.domain,
                    narrative_group=candidate.narrative_group,
                    score=candidate.score,
                    priority=candidate.priority,
                    matched_judgment_keys=list(candidate.matched_judgment_keys),
                    matched_codes=list(candidate.matched_codes),
                    matched_event_terms=list(candidate.matched_event_terms),
                    selection_signal_hints=list(candidate.selection_signal_hints),
                    suppressed_by="limit",
                )
            )
            continue
        used_groups[candidate.narrative_group] = candidate.candidate_key
        used_domains[candidate.domain] = used_domains.get(candidate.domain, 0) + 1
        selected.append(candidate)
    return selected, suppressed


def _unique_strings(values: list[str]) -> list[str]:
    return [value for value in dict.fromkeys(str(value) for value in values if str(value))]


def _clip(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(value))))


_CANDIDATE_SELECTION_RULES = (
    CandidateSelectionRule(
        candidate_key="delayed_start_deep_consideration",
        domain="personality",
        narrative_group="personality_decision_speed",
        priority=5,
        judgment_keys=("day_master_strength", "month_command"),
        code_needles=("resource", "in_seong", "counter", "support", "day_master"),
        event_needles=("기준", "책임", "판단", "결정", "준비"),
        feature_axis_needles=("decision_consistency", "practical_planning", "self_direction"),
        risk_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="calm_outside_strong_inner_standard",
        domain="personality",
        narrative_group="personality_inner_standard",
        priority=6,
        judgment_keys=("day_master", "month_command", "day_master_strength"),
        code_needles=("officer", "resource", "counter", "self", "branch"),
        event_needles=("책임", "기준", "감정 충돌", "평가 기준", "관계 안정"),
        feature_axis_needles=("responsibility", "boundary", "relationship"),
        risk_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="taking_responsibility_for_others",
        domain="personality",
        narrative_group="personality_responsibility_burden",
        priority=7,
        judgment_keys=("authority_responsibility_gap", "practical_output_under_pressure"),
        code_needles=("responsibility", "officer", "family", "counter", "peer"),
        event_needles=("책임", "역할 확대", "가족 변수", "책임 확인", "권한 범위"),
        feature_axis_needles=("responsibility_capacity", "family_responsibility"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="agreeable_outside_clear_inner_boundary",
        domain="personality",
        narrative_group="personality_social_boundary",
        priority=8,
        judgment_keys=("peer_wealth_contact", "day_master_strength"),
        code_needles=("peer", "counter", "relationship", "branch", "harm"),
        event_needles=("거리 조정", "기대 차이", "감정 충돌", "책임 범위"),
        feature_axis_needles=("relationship", "boundary", "social"),
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="income_grows_with_living_costs",
        domain="money",
        narrative_group="money_retention",
        priority=10,
        judgment_keys=("wealth_presence", "money_retention_pressure"),
        code_needles=("cashflow", "spending", "asset_retention", "living_cost"),
        event_needles=("생활비", "지출", "지출 한도", "관리형 수입"),
        feature_axis_needles=("asset_retention", "spending_control"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="talent_without_pricing",
        domain="money",
        narrative_group="money_creation",
        priority=20,
        judgment_keys=("output_to_wealth", "wealth_presence"),
        code_needles=("sik_sin", "sang_gwan", "income_growth", "result"),
        event_needles=("성과의 금전 전환", "보상", "거래 성사", "결과물"),
        feature_axis_needles=("deal_selection", "income_expansion", "business_expansion"),
    ),
    CandidateSelectionRule(
        candidate_key="family_money_request_difficulty",
        domain="money",
        narrative_group="money_family",
        priority=30,
        judgment_keys=("peer_wealth_contact", "money_retention_pressure"),
        code_needles=("family", "peer", "geob_jae", "spending", "counter"),
        event_needles=("가족", "생활비", "지출", "책임"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="verbal_promise_money_loss",
        domain="money",
        narrative_group="money_contract",
        priority=40,
        judgment_keys=("wealth_presence", "peer_wealth_contact"),
        code_needles=("contract", "settlement", "risk", "counter", "peer_wealth"),
        event_needles=("계약", "정산", "지급 조건", "거래"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="delayed_reward_after_performance",
        domain="career",
        narrative_group="career_compensation",
        priority=50,
        judgment_keys=("output_to_wealth", "authority_responsibility_gap"),
        code_needles=("recognition", "reward", "responsibility", "income_growth"),
        event_needles=("평가 기준", "보상", "성과", "권한 범위"),
    ),
    CandidateSelectionRule(
        candidate_key="middle_responsibility_between_boss_and_customer",
        domain="career",
        narrative_group="career_authority",
        priority=60,
        judgment_keys=("authority_responsibility_gap", "practical_output_under_pressure"),
        code_needles=("responsibility_pressure", "authority", "officer", "operation"),
        event_needles=("권한 범위", "평가 기준", "고객", "책임"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="work_done_name_not_left",
        domain="career",
        narrative_group="career_recognition",
        priority=70,
        judgment_keys=("authority_responsibility_gap", "practical_output_under_pressure"),
        code_needles=("recognition", "evaluation", "responsibility", "authority_gap"),
        event_needles=("평가 기준", "역할 확대", "책임", "성과"),
    ),
    CandidateSelectionRule(
        candidate_key="fast_alone_slow_in_team",
        domain="career",
        narrative_group="career_work_style",
        priority=80,
        judgment_keys=("practical_output_under_pressure",),
        code_needles=("operation", "team", "responsibility", "peer"),
        event_needles=("업무 재배치", "역할 확대", "일정", "협업"),
    ),
    CandidateSelectionRule(
        candidate_key="opportunities_through_people",
        domain="career",
        narrative_group="career_social_expansion",
        priority=90,
        judgment_keys=("peer_wealth_contact", "wealth_presence"),
        code_needles=("contract", "peer", "income_growth", "connection"),
        event_needles=("연결·계약", "거래 성사", "역할 확대", "평판"),
        opportunity_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="deep_love_late_expression",
        domain="love",
        narrative_group="love_expression",
        priority=100,
        code_needles=("love", "relationship", "counter", "officer"),
        event_needles=("감정 충돌", "기대 차이", "거리 조정", "연락"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="marriage_living_cost_role_sensitivity",
        domain="marriage",
        narrative_group="marriage_life_basis",
        priority=110,
        judgment_keys=("money_retention_pressure", "authority_responsibility_gap"),
        code_needles=("marriage", "responsibility", "wealth", "spending"),
        event_needles=("생활 합의", "책임 확인", "경제 조건", "가족 변수"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="delayed_refusal_from_guilt",
        domain="love",
        narrative_group="relationship_boundary",
        priority=120,
        code_needles=("counter", "peer", "family", "relationship"),
        event_needles=("거리 조정", "책임 범위", "기대 차이", "감정 충돌"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="delayed_settlement_talk",
        domain="money",
        narrative_group="money_settlement_delay",
        priority=130,
        judgment_keys=("wealth_presence", "money_retention_pressure"),
        code_needles=("contract", "settlement", "cashflow", "income_growth"),
        event_needles=("정산 기준", "지급 조건", "계약 범위", "거래"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="lending_and_guarantee_caution",
        domain="money",
        narrative_group="money_debt_guarantee",
        priority=140,
        judgment_keys=("peer_wealth_contact", "money_retention_pressure"),
        code_needles=("peer", "family", "counter", "risk", "spending"),
        event_needles=("지출 한도", "책임", "경제 조건", "가족 변수"),
        risk_weight=0.14,
    ),
    CandidateSelectionRule(
        candidate_key="upfront_business_learning_costs",
        domain="money",
        narrative_group="money_upfront_costs",
        priority=150,
        judgment_keys=("output_to_wealth", "money_retention_pressure"),
        code_needles=("output", "income_growth", "spending", "asset_retention"),
        event_needles=("성과의 금전 전환", "지출 한도", "관리형 수입", "계약 범위"),
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="family_asset_standard_gap",
        domain="money",
        narrative_group="money_family_asset_standard",
        priority=160,
        judgment_keys=("peer_wealth_contact", "wealth_presence"),
        code_needles=("family", "wealth", "asset", "spending", "counter"),
        event_needles=("가족 변수", "경제 조건", "생활 합의", "지출 한도"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="documents_and_proof_protect_work",
        domain="career",
        narrative_group="career_documents_proof",
        priority=170,
        judgment_keys=("authority_responsibility_gap", "practical_output_under_pressure"),
        code_needles=("contract", "authority", "operation", "responsibility"),
        event_needles=("평가 기준", "권한 범위", "계약 범위", "역할 확대"),
    ),
    CandidateSelectionRule(
        candidate_key="planning_analysis_recognition",
        domain="career",
        narrative_group="career_planning_analysis",
        priority=171,
        judgment_keys=("output_to_wealth", "practical_output_under_pressure"),
        code_needles=("output", "resource", "operation", "recognition", "result"),
        event_needles=("평가 기준", "역할 확대", "성과", "자료", "전문성"),
        feature_axis_needles=("practical_planning", "academic_expertise", "career_achievement"),
        opportunity_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="teaching_counseling_explanation_strength",
        domain="career",
        narrative_group="career_teaching_counseling",
        priority=172,
        judgment_keys=("output_to_wealth", "practical_output_under_pressure"),
        code_needles=("output", "resource", "recognition", "service", "support"),
        event_needles=("평가 기준", "성과", "역할 확대", "고객", "책임"),
        feature_axis_needles=("communication_expression", "academic_expertise", "interpersonal_influence"),
        opportunity_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="operations_schedule_coordination_role",
        domain="career",
        narrative_group="career_operations_coordination",
        priority=173,
        judgment_keys=("practical_output_under_pressure", "authority_responsibility_gap"),
        code_needles=("operation", "responsibility", "project", "schedule", "authority"),
        event_needles=("역할 확대", "업무 재배치", "권한 범위", "평가 기준", "일정"),
        feature_axis_needles=("organization_adaptability", "practical_planning", "responsibility_capacity"),
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="independent_work_pricing_customer_boundary",
        domain="career",
        narrative_group="career_independent_pricing_boundary",
        priority=174,
        judgment_keys=("output_to_wealth", "wealth_presence"),
        code_needles=("income_growth", "contract", "output", "customer", "settlement"),
        event_needles=("거래 성사", "계약 범위", "지급 조건", "성과의 금전 전환", "고객"),
        feature_axis_needles=("deal_selection", "business_expansion", "boundary_management"),
        opportunity_weight=0.1,
        risk_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="real_authority_over_promotion",
        domain="career",
        narrative_group="career_real_authority",
        priority=180,
        judgment_keys=("authority_responsibility_gap",),
        code_needles=("authority", "officer", "responsibility_pressure"),
        event_needles=("권한 범위", "역할 확대", "책임", "평가 기준"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="customer_complaint_frontline_role",
        domain="career",
        narrative_group="career_customer_response",
        priority=190,
        judgment_keys=("practical_output_under_pressure", "authority_responsibility_gap"),
        code_needles=("operation", "responsibility", "counter", "risk"),
        event_needles=("고객", "민원", "책임", "문제"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="expertise_with_late_self_promotion",
        domain="career",
        narrative_group="career_expertise_visibility",
        priority=200,
        judgment_keys=("output_to_wealth", "practical_output_under_pressure"),
        code_needles=("output", "recognition", "result", "career_recognition"),
        event_needles=("성과", "평가 기준", "역할 확대", "전문성"),
        opportunity_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="tone_misread_in_love",
        domain="love",
        narrative_group="love_expression_tone",
        priority=210,
        code_needles=("love", "relationship", "counter", "officer"),
        event_needles=("감정 충돌", "기대 차이", "거리 조정", "대화"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="personal_time_needed_in_love",
        domain="love",
        narrative_group="love_distance_and_personal_time",
        priority=220,
        code_needles=("love", "relationship", "counter", "peer"),
        event_needles=("거리 조정", "기대 차이", "관계 안정 점검", "감정 충돌"),
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="family_involvement_in_marriage",
        domain="marriage",
        narrative_group="marriage_family_involvement",
        priority=230,
        judgment_keys=("peer_wealth_contact", "authority_responsibility_gap"),
        code_needles=("marriage", "family", "responsibility", "wealth"),
        event_needles=("가족 변수", "결정 부담", "생활 합의", "책임 확인"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="housing_and_living_costs_marriage",
        domain="marriage",
        narrative_group="marriage_housing_living_costs",
        priority=240,
        judgment_keys=("wealth_presence", "money_retention_pressure"),
        code_needles=("marriage", "wealth", "spending", "asset_retention"),
        event_needles=("경제 조건", "생활 합의", "지출 한도", "가족 변수"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="care_turns_into_love_pressure",
        domain="love",
        narrative_group="love_care_pressure",
        priority=250,
        judgment_keys=("authority_responsibility_gap",),
        code_needles=("love", "relationship", "responsibility", "support", "resource"),
        event_needles=("연락", "감정", "거리", "기대", "책임"),
        feature_axis_needles=("relationship", "boundary", "responsibility"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="slow_reply_misread_love",
        domain="love",
        narrative_group="love_reply_delay",
        priority=251,
        code_needles=("love", "relationship", "resource", "counter", "expression"),
        event_needles=("연락", "표현", "오해", "거리", "감정"),
        feature_axis_needles=("communication", "relationship", "decision"),
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="fast_attraction_slow_reality_love",
        domain="love",
        narrative_group="love_attraction_reality_gap",
        priority=252,
        judgment_keys=("wealth_presence", "authority_responsibility_gap"),
        code_needles=("love", "relationship", "wealth", "change", "counter"),
        event_needles=("만남", "연락", "생활", "거리", "감정"),
        feature_axis_needles=("relationship_progression", "change_adaptability", "decision_consistency"),
        opportunity_weight=0.09,
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="spouse_money_standard_difference",
        domain="marriage",
        narrative_group="marriage_money_standard_gap",
        priority=260,
        judgment_keys=("wealth_presence", "money_retention_pressure"),
        code_needles=("marriage", "wealth", "asset", "spending", "family"),
        event_needles=("경제 조건", "생활 합의", "지출", "주거", "가족"),
        feature_axis_needles=("asset_retention", "boundary_management", "loss_avoidance"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="home_family_role_burden_marriage",
        domain="marriage",
        narrative_group="marriage_home_role_burden",
        priority=261,
        judgment_keys=("authority_responsibility_gap", "peer_wealth_contact"),
        code_needles=("marriage", "family", "responsibility", "support", "officer"),
        event_needles=("가족", "책임", "생활 합의", "결정 부담", "역할"),
        feature_axis_needles=("responsibility_capacity", "boundary_management", "self_direction"),
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="marriage_delayed_by_practical_preparation",
        domain="marriage",
        narrative_group="marriage_practical_delay",
        priority=262,
        judgment_keys=("day_master_strength", "wealth_presence", "authority_responsibility_gap"),
        code_needles=("marriage", "wealth", "resource", "support", "responsibility"),
        event_needles=("경제 조건", "주거", "생활 합의", "결정 부담", "책임"),
        feature_axis_needles=("decision_consistency", "asset_retention", "career_achievement"),
        opportunity_weight=0.08,
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="cautious_big_decision_personality",
        domain="personality",
        narrative_group="personality_big_decision_caution",
        priority=270,
        judgment_keys=("day_master_strength", "month_command"),
        code_needles=("resource", "support", "officer", "counter", "risk"),
        event_needles=("판단", "결정", "책임", "기준", "준비"),
        feature_axis_needles=("decision_consistency", "loss_avoidance", "self_direction"),
        base_score=16,
        risk_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="public_private_split_personality",
        domain="personality",
        narrative_group="personality_public_private_split",
        priority=271,
        judgment_keys=("day_master", "month_command", "authority_responsibility_gap"),
        code_needles=("officer", "peer", "relationship", "branch", "counter"),
        event_needles=("관계", "책임", "감정", "가족", "기준"),
        feature_axis_needles=("relationship", "boundary", "responsibility"),
        base_score=16,
        risk_weight=0.1,
    ),
    CandidateSelectionRule(
        candidate_key="skill_money_irregular_income",
        domain="money",
        narrative_group="money_skill_irregular_income",
        priority=280,
        judgment_keys=("output_to_wealth", "wealth_presence"),
        code_needles=("output", "income_growth", "contract", "service", "result"),
        event_needles=("성과의 금전 전환", "거래 성사", "수입", "계약", "고객"),
        feature_axis_needles=("business_expansion", "career_achievement", "asset_retention"),
        opportunity_weight=0.11,
        risk_weight=0.08,
    ),
    CandidateSelectionRule(
        candidate_key="shared_business_profit_split",
        domain="money",
        narrative_group="money_shared_profit_split",
        priority=281,
        judgment_keys=("peer_wealth_contact", "wealth_presence", "money_retention_pressure"),
        code_needles=("peer", "wealth", "settlement", "contract", "counter"),
        event_needles=("정산 기준", "계약 범위", "공동", "거래", "지출"),
        feature_axis_needles=("boundary_management", "asset_retention", "loss_avoidance"),
        opportunity_weight=0.09,
        risk_weight=0.13,
    ),
    CandidateSelectionRule(
        candidate_key="executor_weak_self_claim_career",
        domain="career",
        narrative_group="career_execution_self_claim",
        priority=282,
        judgment_keys=("output_to_wealth", "practical_output_under_pressure"),
        code_needles=("output", "recognition", "result", "responsibility", "career"),
        event_needles=("성과", "평가 기준", "역할", "책임", "보상"),
        feature_axis_needles=("career_achievement", "reputation_maintenance", "practical_planning"),
        opportunity_weight=0.1,
        risk_weight=0.09,
    ),
    CandidateSelectionRule(
        candidate_key="organization_rule_personal_judgment_career",
        domain="career",
        narrative_group="career_rule_judgment_conflict",
        priority=283,
        judgment_keys=("authority_responsibility_gap", "practical_output_under_pressure"),
        code_needles=("officer", "authority", "responsibility", "operation", "counter"),
        event_needles=("권한 범위", "책임", "평가 기준", "업무", "조직"),
        feature_axis_needles=("organization_adaptability", "crisis_recovery", "decision_consistency"),
        opportunity_weight=0.08,
        risk_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="later_life_settles_better_than_early",
        domain="life_timing",
        narrative_group="life_timing_later_stability",
        priority=300,
        judgment_keys=("day_master_strength", "wealth_presence", "output_to_wealth"),
        code_needles=("daeun", "useful", "support", "resource", "output"),
        event_needles=("역할 확대", "성과의 금전 전환", "평가 기준", "관리형 수입 확대"),
        feature_axis_needles=("asset_retention", "career_achievement", "practical_planning"),
        opportunity_weight=0.09,
    ),
    CandidateSelectionRule(
        candidate_key="direction_clarifies_after_break",
        domain="life_timing",
        narrative_group="life_timing_after_break_direction",
        priority=310,
        judgment_keys=("day_master_strength", "authority_responsibility_gap"),
        code_needles=("clash", "break", "harm", "counter", "change"),
        event_needles=("직무 전환", "근무 환경 변화", "거리 조정", "결정 부담", "변화"),
        feature_axis_needles=("change_adaptability", "decision_consistency", "crisis_recovery"),
        risk_weight=0.11,
    ),
    CandidateSelectionRule(
        candidate_key="accumulated_work_gets_recognized_period",
        domain="life_timing",
        narrative_group="life_timing_accumulated_work_recognition",
        priority=320,
        judgment_keys=("output_to_wealth", "practical_output_under_pressure", "wealth_presence"),
        code_needles=("income_growth", "recognition", "output", "contract", "useful"),
        event_needles=("성과의 금전 전환", "거래 성사", "평가 기준", "역할 확대", "고정"),
        feature_axis_needles=("career_achievement", "business_expansion", "income_expansion"),
        opportunity_weight=0.12,
    ),
    CandidateSelectionRule(
        candidate_key="unresolved_promises_return_caution_period",
        domain="life_timing",
        narrative_group="life_timing_unresolved_promise_caution",
        priority=330,
        judgment_keys=("money_retention_pressure", "authority_responsibility_gap", "peer_wealth_contact"),
        code_needles=("counter", "risk", "contract", "settlement", "clash"),
        event_needles=("정산 기준", "계약 범위", "책임 범위", "감정 충돌", "결정 부담"),
        feature_axis_needles=("loss_avoidance", "asset_retention", "boundary_management"),
        risk_weight=0.13,
    ),
)
