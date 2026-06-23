"""Data models for the saju analysis engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Domain = Literal["money", "career", "love", "marriage"]
Confidence = Literal["high", "medium_high", "medium", "low", "restricted"]
ProductTier = Literal["free", "basic", "premium"]
RelationshipStatus = Literal["single", "interested", "dating", "long_term", "preparing_marriage", "married", "unknown"]


@dataclass(frozen=True)
class ElementScore:
    element: str
    raw_score: float
    seasonal_score: float
    ratio: float
    visible_count: int
    root_count: int
    exposure: str
    state: str


@dataclass(frozen=True)
class ElementProfile:
    day_master_element: str
    month_branch: str
    season_label: str
    scores: dict[str, ElementScore]
    day_master_strength_score: int
    day_master_strength: str
    useful_elements: list[str]
    caution_elements: list[str]
    temperature_balance: str
    moisture_balance: str
    climate_needs: list[str]
    circulation_level: str
    circulation_notes: list[str]
    illness_medicine: list[dict[str, Any]]


@dataclass(frozen=True)
class TenGodProfile:
    visible_counts: dict[str, float]
    hidden_counts: dict[str, float]
    group_scores: dict[str, float]
    dominant_ten_gods: list[str]
    important_pairs: list[str]


@dataclass(frozen=True)
class BranchInteraction:
    relation_type: str
    branches: list[str]
    positions: list[str]
    effect_element: str | None
    intensity: str
    domain_links: list[str]
    basis_code: str


@dataclass(frozen=True)
class AuxiliaryMiscSignal:
    key: str
    label: str
    grade: str
    lineage: str
    formula_name: str
    positions: list[str]
    pillar_labels: list[str]
    domains: list[str]
    intensity: str
    allowed_use: str
    meaning: str
    caution: str
    basis_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuxiliaryProfile:
    twelve_growth_by_position: dict[str, str]
    sal_by_position: dict[str, list[str]]
    day_branch_group: str
    year_branch_group: str = "unknown_group"
    day_sal_by_position: dict[str, list[str]] = field(default_factory=dict)
    year_sal_by_position: dict[str, list[str]] = field(default_factory=dict)
    misc_shinsal_signals: list[AuxiliaryMiscSignal] = field(default_factory=list)


@dataclass(frozen=True)
class ChartType:
    name: str
    role: str
    score: int
    confidence: Confidence
    basis_codes: list[str]


@dataclass(frozen=True)
class UsefulElementCandidate:
    element: str
    role: str
    score: int
    confidence: Confidence
    basis_codes: list[str]


@dataclass(frozen=True)
class PatternProfile:
    primary_pattern: str
    pattern_confidence: Confidence
    candidates: list[ChartType]
    useful_element_candidates: list[UsefulElementCandidate]
    caution_element_candidates: list[UsefulElementCandidate]
    decision_notes: list[str]
    month_command_ten_god: str = ""
    regular_pattern: str = ""
    pattern_family: str = ""
    special_pattern_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LifeFeatureScore:
    key: str
    category: str
    label: str
    score: int
    percentile_label: str
    strength_label: str
    confidence: Confidence
    basis_codes: list[str]
    counter_signals: list[str]
    customer_sentence: str


@dataclass(frozen=True)
class LifeFeatureProfile:
    axes: dict[str, LifeFeatureScore]
    top_axis_keys: list[str]
    caution_axis_keys: list[str]
    summary_sentences: list[str]


@dataclass(frozen=True)
class SourcePersonalityTrait:
    source_type: str
    source_key: str
    title: str
    compression_type: str
    core_traits: list[str]
    outer_traits: list[str]
    inner_traits: list[str]
    strength_traits: list[str]
    shadow_traits: list[str]
    main_ten_god: str = ""
    basis_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourcePersonalityProfile:
    day_pillar_profile: SourcePersonalityTrait | None
    month_branch_profile: SourcePersonalityTrait | None
    trait_keywords: list[str]
    strength_keywords: list[str]
    shadow_keywords: list[str]
    summary_sentences: list[str]
    basis_codes: list[str]
    rule_version: str = "source_personality_profile_v1"


@dataclass(frozen=True)
class SourceReadingPoint:
    source_type: str
    source_key: str
    domain: str
    label: str
    text: str
    basis_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceReadingProfile:
    domain_points: dict[str, list[SourceReadingPoint]]
    summary_points: list[SourceReadingPoint]
    basis_codes: list[str]
    rule_version: str = "source_reading_profile_v1"


@dataclass(frozen=True)
class CareerWorkStyleScore:
    key: str
    label: str
    score: int
    strength_label: str
    confidence: Confidence
    role_sentence: str
    basis_codes: list[str]
    counter_signals: list[str]
    customer_sentence: str


@dataclass(frozen=True)
class CareerSubRoleScore:
    key: str
    label: str
    parent_field_key: str
    score: int
    strength_label: str
    confidence: Confidence
    work_style_links: list[str]
    role_sentence: str
    basis_codes: list[str]
    counter_signals: list[str]


@dataclass(frozen=True)
class CareerFieldScore:
    key: str
    label: str
    category: str
    score: int
    strength_label: str
    confidence: Confidence
    suitable_fields: list[str]
    unsuitable_conditions: list[str]
    primary_unsuitable_condition: str
    day_master_fit_mode: str
    seasonal_fit_note: str
    fit_context_sentence: str
    fit_context_basis_codes: list[str]
    role_style: str
    income_link: str
    sub_roles: list[CareerSubRoleScore]
    top_sub_role_keys: list[str]
    display_priority: str
    basis_codes: list[str]
    counter_signals: list[str]
    customer_sentence: str


@dataclass(frozen=True)
class CareerFieldProfile:
    fields: dict[str, CareerFieldScore]
    work_styles: dict[str, CareerWorkStyleScore]
    top_field_keys: list[str]
    primary_field_keys: list[str]
    reference_field_keys: list[str]
    caution_field_keys: list[str]
    top_work_style_keys: list[str]
    summary_sentences: list[str]
    interpretation_principle: str
    rule_version: str = "career_field_projection_v1"


@dataclass(frozen=True)
class CombinationSignal:
    signal_id: str
    layer: str
    relation_type: str
    combination_key: str
    positions: list[str]
    stems: list[str]
    branches: list[str]
    elements: list[str]
    ten_gods: list[str]
    strength: str
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    interpretation: str


@dataclass(frozen=True)
class CombinationProfile:
    heavenly_stem_signals: list[CombinationSignal]
    hidden_stem_signals: list[CombinationSignal]
    stem_branch_signals: list[CombinationSignal]
    ten_god_chain_signals: list[CombinationSignal]
    top_signal_ids: list[str]
    domain_notes: dict[str, list[str]]
    summary_sentences: list[str]


@dataclass(frozen=True)
class ElementCombinationSignal:
    signal_id: str
    layer: str
    combination_key: str
    positions: list[str]
    stems: list[str]
    branches: list[str]
    elements: list[str]
    relation_type: str
    source_rule: str
    strength: str
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    trait_keywords: list[str]
    interpretation: str
    monthly_variant_note: str = ""
    day_master_variant_note: str = ""


@dataclass(frozen=True)
class ElementCombinationProfile:
    heavenly_stem_signals: list[ElementCombinationSignal]
    hidden_stem_signals: list[ElementCombinationSignal]
    stem_branch_signals: list[ElementCombinationSignal]
    top_signal_ids: list[str]
    domain_notes: dict[str, list[str]]
    summary_sentences: list[str]
    rule_version: str = "element_combination_v1"


@dataclass(frozen=True)
class DirectionalInteractionSignal:
    signal_id: str
    layer: str
    direction_key: str
    element_direction_key: str
    direction_type: str
    source_position: str
    target_position: str
    source_stem: str
    target_stem: str
    source_branch: str
    target_branch: str
    source_element: str
    target_element: str
    source_rule: str
    strength: str
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    trait_keywords: list[str]
    interpretation: str
    element_interpretation: str


@dataclass(frozen=True)
class DirectionalInteractionProfile:
    heavenly_stem_signals: list[DirectionalInteractionSignal]
    hidden_stem_signals: list[DirectionalInteractionSignal]
    stem_branch_signals: list[DirectionalInteractionSignal]
    top_signal_ids: list[str]
    summary_sentences: list[str]
    rule_version: str = "directional_interaction_v1"


@dataclass(frozen=True)
class TenGodInteractionSignal:
    signal_id: str
    layer: str
    direction_key: str
    source_position: str
    target_position: str
    source_stem: str
    target_stem: str
    source_branch: str
    target_branch: str
    source_ten_god: str
    target_ten_god: str
    source_rule: str
    strength: str
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    trait_keywords: list[str]
    interpretation: str
    source_core: str
    target_core: str
    position_context: str
    month_context_note: str


@dataclass(frozen=True)
class TenGodInteractionProfile:
    visible_stem_signals: list[TenGodInteractionSignal]
    hidden_stem_signals: list[TenGodInteractionSignal]
    stem_branch_signals: list[TenGodInteractionSignal]
    top_signal_ids: list[str]
    summary_sentences: list[str]
    rule_version: str = "ten_god_interaction_v1"


@dataclass(frozen=True)
class StemReceptionSignal:
    signal_id: str
    layer: str
    day_stem: str
    target_stem: str
    target_element: str
    target_ten_god: str
    position: str
    branch: str
    source: str
    strength: str
    priority_score: int
    seasonal_modifier: float
    protruded: bool
    branch_relation_modifiers: list[str]
    branch_relation_score_modifier: float
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    trait_keywords: list[str]
    core_interpretation: str
    felt_experience: str
    behavior_tendency: str
    fitting_conditions: dict[str, list[str]]
    misfitting_conditions: dict[str, list[str]]
    fatigue_or_loss: dict[str, list[str]]
    domain_projection: dict[str, str]
    evidence: list[str]


@dataclass(frozen=True)
class StemReceptionProfile:
    visible_stem_signals: list[StemReceptionSignal]
    hidden_stem_signals: list[StemReceptionSignal]
    branch_main_signals: list[StemReceptionSignal]
    top_signal_ids: list[str]
    summary_sentences: list[str]
    rule_version: str = "stem_reception_v1"


@dataclass(frozen=True)
class IntegratedSajuSignal:
    signal_id: str
    layer: str
    source_position: str
    target_position: str
    source_stem: str
    target_stem: str
    source_element: str
    target_element: str
    source_ten_god: str
    target_ten_god: str
    element_direction_key: str
    ten_god_direction_key: str
    source_reception_key: str
    target_reception_key: str
    strength: str
    priority_score: int
    branch_relation_score_modifier: float
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    trait_keywords: list[str]
    core_interpretation: str
    combined_interpretation: str
    fitting_conditions: dict[str, list[str]]
    misfitting_conditions: dict[str, list[str]]
    fatigue_or_loss: dict[str, list[str]]
    domain_projection: dict[str, str]
    evidence: list[str]


@dataclass(frozen=True)
class IntegratedSajuProfile:
    visible_pair_signals: list[IntegratedSajuSignal]
    hidden_pair_signals: list[IntegratedSajuSignal]
    stem_branch_pair_signals: list[IntegratedSajuSignal]
    top_signal_ids: list[str]
    summary_sentences: list[str]
    rule_version: str = "integrated_saju_signal_v1"


@dataclass(frozen=True)
class MonthGovernanceElementFit:
    element: str
    status: str
    support_score: int
    pressure_score: int
    reality_score: int
    month_authority: str
    roles: list[str]
    basis_codes: list[str]
    counter_signals: list[str]


@dataclass(frozen=True)
class MonthGovernanceRoleFit:
    group: str
    element: str
    status: str
    support_score: int
    pressure_score: int
    basis_codes: list[str]
    counter_signals: list[str]


@dataclass(frozen=True)
class MonthGovernanceDecision:
    signal_key: str
    signal_type: str
    domain: str
    positions: list[str]
    elements: list[str]
    ten_gods: list[str]
    groups: list[str]
    fit_status: str
    support_score: int
    pressure_score: int
    reality_status: str
    domain_fit: str
    basis_codes: list[str]
    counter_signals: list[str]


@dataclass(frozen=True)
class MonthHiddenPhaseEntry:
    phase: str
    stem: str
    element: str
    ten_god: str
    ten_god_group: str
    days: int
    start_day: int
    end_day: int
    active: bool
    repeated_stem: bool = False


@dataclass(frozen=True)
class MonthHiddenPhaseProfile:
    month_branch: str
    day_index_from_boundary: float
    active_phase: str
    active_stem: str
    active_element: str
    active_ten_god: str
    active_ten_god_group: str
    entries: list[MonthHiddenPhaseEntry]
    basis_codes: list[str]
    rule_version: str = "month_hidden_phase_v1"


@dataclass(frozen=True)
class MonthGovernanceProfile:
    month_branch: str
    month_element: str
    month_command_ten_god: str
    month_command_group: str
    regular_pattern: str
    pattern_family: str
    command_hidden_stems: list[dict[str, Any]]
    protruded_hidden_stems: list[str]
    useful_elements: list[str]
    caution_elements: list[str]
    useful_groups: list[str]
    caution_groups: list[str]
    element_fits: dict[str, MonthGovernanceElementFit]
    role_fits: dict[str, MonthGovernanceRoleFit]
    domain_focus_groups: dict[str, list[str]]
    decision_notes: list[str]
    month_hidden_phase: MonthHiddenPhaseProfile | None = None
    rule_version: str = "month_governance_v1"


@dataclass(frozen=True)
class PositionSignal:
    position: str
    pillar: str
    stem_key: str
    branch_key: str
    stem_element: str
    branch_element: str
    stem_ten_god: str
    branch_main_ten_god: str
    hidden_ten_gods: list[str]
    domains: list[str]
    protruded_hidden_stems: list[str]
    supports_day_master: bool
    controls_day_master: bool
    age_scope: str = ""
    life_stage: str = ""
    primary_context: str = ""
    stem_visibility_weight: float = 1.0
    branch_reality_weight: float = 1.0
    hidden_reality_weight: float = 1.0
    position_basis_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChartStructure:
    four_pillars: dict[str, str]
    day_master_stem: str
    day_master_element: str
    day_master_yin_yang: str
    month_branch: str
    season_label: str
    element_profile: ElementProfile
    ten_god_profile: TenGodProfile
    position_signals: dict[str, PositionSignal]
    branch_interactions: list[BranchInteraction]
    auxiliary_profile: AuxiliaryProfile
    combination_profile: CombinationProfile
    element_combination_profile: ElementCombinationProfile
    directional_interaction_profile: DirectionalInteractionProfile
    ten_god_interaction_profile: TenGodInteractionProfile
    stem_reception_profile: StemReceptionProfile
    integrated_saju_profile: IntegratedSajuProfile
    cycle_regulation_profile: dict[str, Any]
    month_governance_profile: MonthGovernanceProfile
    chart_types: list[ChartType]
    pattern_profile: PatternProfile
    life_feature_profile: LifeFeatureProfile
    source_personality_profile: SourcePersonalityProfile
    source_reading_profile: SourceReadingProfile
    career_field_profile: CareerFieldProfile
    structure_tags: list[str]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubPeriodSignal:
    period_label: str
    period_scope: str
    pillar: str
    stem_ten_god: str
    branch_main_ten_god: str
    domain_focus: list[str]
    intensity_score: int
    basis_codes: list[str]
    counter_signals: list[str]
    start_datetime: str | None = None
    end_datetime: str | None = None
    monthly_phase: str = "unknown"


@dataclass(frozen=True)
class FlowSignal:
    period_label: str
    period_scope: str
    year: int
    year_pillar: str
    year_stem_ten_god: str
    year_branch_main_ten_god: str
    daeun_pillar: str | None
    daeun_stem_ten_god: str | None
    daeun_branch_main_ten_god: str | None
    branch_interactions: list[BranchInteraction]
    activated_elements: list[str]
    domain_scores: dict[str, dict[str, Any]]
    sub_period_signals: list[SubPeriodSignal]
    basis_codes: list[str]
    counter_signals: list[str]
    activation_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PastEventAnswer:
    event_key: str
    answer: str
    year: int | None = None
    domain: Domain | None = None


@dataclass(frozen=True)
class CalibrationProfile:
    status: str
    matched_count: int
    partial_count: int
    unmatched_count: int
    skipped_count: int
    domain_adjustments: dict[str, int]
    confidence_adjustment: int
    basis_codes: list[str]


@dataclass(frozen=True)
class EventPacket:
    packet_id: str
    domain: Domain
    sub_event_type: str
    period_label: str
    period_scope: str
    opportunity_score: int
    risk_score: int
    change_score: int
    event_probability_score: int
    confidence: Confidence
    expression_strength: str
    event_form: str
    realization_path: str
    risk_path: str
    timing_strength: str
    primary_scene_sentence: str
    main_action: str
    risk_topic: str
    event_keywords: list[str]
    personality_filter: str
    domain_links: list[str]
    basis_codes: list[str]
    counter_signals: list[str]
    conflict_status: str
    output_allowed_level: str
    past_check_status: str = "not_checked"
    timing_markers: list[str] = field(default_factory=list)
    timing_windows: list[dict[str, Any]] = field(default_factory=list)
    rendered_preview: str | None = None
    common_template_id: str = ""
    domain_template_id: str = ""
    type_template_id: str = ""
    template_slots: dict[str, Any] = field(default_factory=dict)
    relationship_status: RelationshipStatus = "unknown"
    feature_axes: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class RiskFilterResult:
    original_text: str
    filtered_text: str
    flags: list[str]
    output_allowed: bool


@dataclass(frozen=True)
class ProductOutputItem:
    packet_id: str
    product_tier: ProductTier
    domain: Domain
    domain_label: str
    period_label: str
    title: str
    summary: str
    detail: str
    timing: list[str]
    timing_windows: list[dict[str, Any]]
    action: str
    risk: str
    basis_codes: list[str]
    filter_flags: list[str]
    event_keywords: list[str] = field(default_factory=list)
    opportunity_score: int = 0
    risk_score: int = 0
    change_score: int = 0
    event_probability_score: int = 0
    confidence: Confidence = "restricted"
    expression_strength: str = ""
    score_labels: dict[str, str] = field(default_factory=dict)
    basis_summary: list[str] = field(default_factory=list)
    counter_summary: list[str] = field(default_factory=list)
    common_template_id: str = ""
    domain_template_id: str = ""
    type_template_id: str = ""
    template_slots: dict[str, Any] = field(default_factory=dict)
    past_check_status: str = "not_checked"
    relationship_status: RelationshipStatus = "unknown"
    relationship_status_label: str = ""
    relationship_context: str = ""
    feature_axes: list[dict[str, Any]] = field(default_factory=list)
    judgment_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductOutputSection:
    section_id: str
    packet_id: str
    product_tier: ProductTier
    detail_level: str
    domain: Domain
    domain_label: str
    period_label: str
    heading: str
    lead: str
    paragraphs: list[str]
    key_points: list[str]
    timing_windows: list[dict[str, Any]]
    template_ids: dict[str, str]
    relationship_status: RelationshipStatus = "unknown"
    relationship_status_label: str = ""
    feature_axes: list[dict[str, Any]] = field(default_factory=list)
    topic_items: list[dict[str, Any]] = field(default_factory=list)
    category_contract: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SectionSelectionJudgment:
    key: str
    label: str
    value: str
    score: int
    basis_codes: list[str] = field(default_factory=list)
    counter_signals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SelectedReportSection:
    section_key: str
    title: str
    domain: str
    narrative_group: str
    score: int
    priority: int
    paragraphs: list[str]
    compressed_summary: str
    trigger_codes: list[str] = field(default_factory=list)
    judgment_keys: list[str] = field(default_factory=list)
    suppressed_by: str = ""
    source_key: str = ""
    age_timing_sentences: list[str] = field(default_factory=list)
    annual_sentences: dict[int, list[str]] = field(default_factory=dict)
    wording_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateReportSection:
    section_key: str
    title: str
    domain: str
    slot_label: str
    score: int
    quality_score: int
    opening: list[str]
    body: list[str]
    summary: list[str]
    timing_sentences: list[str] = field(default_factory=list)
    timing_year_label: str = ""
    timing_age_label: str = ""
    evidence: list[str] = field(default_factory=list)
    source_key: str = "section_bank_candidate"
    quality_status: str = ""


@dataclass(frozen=True)
class PremiumDetailMatch:
    entry_key: str
    domain: str
    title: str
    narrative_group: str
    score: int
    level: str
    priority: int
    judgment: str
    event_scenes: list[str] = field(default_factory=list)
    premium_notes: list[str] = field(default_factory=list)
    caution_targets: list[str] = field(default_factory=list)
    timing_keywords: list[str] = field(default_factory=list)
    matched_codes: list[str] = field(default_factory=list)
    matched_event_terms: list[str] = field(default_factory=list)
    matched_feature_axes: list[str] = field(default_factory=list)
    engine_signal_hints: list[str] = field(default_factory=list)
    dictionary_version: str = ""
    selection_version: str = ""


@dataclass(frozen=True)
class ProductOutput:
    product_tier: ProductTier
    items: list[ProductOutputItem]
    omitted_packet_ids: list[str]
    sections: list[ProductOutputSection] = field(default_factory=list)
    target_years: list[int] = field(default_factory=list)
    schema_version: str = "analysis_product_v1"
    engine_manifest: dict[str, Any] = field(default_factory=dict)
    calibration_status: str = "not_checked"
    calibration_label: str = ""
    calibration_basis_codes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    warning_labels: list[str] = field(default_factory=list)
    domain_coverage: dict[str, str] = field(default_factory=dict)
    domain_coverage_labels: dict[str, str] = field(default_factory=dict)
    life_feature_summary: dict[str, Any] = field(default_factory=dict)
    catalog_entries: list[dict[str, Any]] = field(default_factory=list)
    section_selection_judgments: list[SectionSelectionJudgment] = field(default_factory=list)
    selected_report_sections: list[SelectedReportSection] = field(default_factory=list)
    premium_candidate_sections: list[CandidateReportSection] = field(default_factory=list)
    premium_detail_sections: list[PremiumDetailMatch] = field(default_factory=list)
    premium_profile_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisResult:
    chart_structure: ChartStructure
    flow_signals: list[FlowSignal]
    event_packets: list[EventPacket]
    calibration_profile: CalibrationProfile
    warnings: list[str]
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
