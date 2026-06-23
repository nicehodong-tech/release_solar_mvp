"""Output contract checks for template-ready analysis packets."""

from __future__ import annotations

from datetime import datetime

from .models import AnalysisResult, EventPacket, ProductOutput, ProductOutputItem, ProductOutputSection


REQUIRED_FEATURE_AXIS_KEYS = frozenset(
    {
        "key",
        "category",
        "label",
        "score",
        "percentile_label",
        "strength_label",
        "confidence",
        "basis_codes",
        "counter_signals",
        "customer_sentence",
    }
)

FEATURE_AXIS_CATEGORIES = frozenset({"money", "social", "personality"})
FEATURE_AXIS_CONFIDENCE = frozenset({"high", "medium_high", "medium", "low", "restricted"})

REQUIRED_TEMPLATE_SLOT_KEYS = frozenset(
    {
        "domain",
        "period_label",
        "confidence",
        "domain_opportunity_score",
        "domain_risk_score",
        "change_score",
        "event_candidates",
        "event_keywords",
        "main_action",
        "risk_topic",
        "primary_scene_sentence",
        "past_check_status",
        "relationship_status",
        "primary_chart_type",
        "regular_pattern",
        "type_confidence",
        "active_chart_type",
        "active_type_role",
        "active_type_confidence",
        "timing_markers",
        "timing_windows",
        "monthly_phase",
        "feature_axes",
    }
)

NON_EMPTY_TEMPLATE_SLOT_KEYS = frozenset(
    {
        "domain",
        "period_label",
        "confidence",
        "event_candidates",
        "event_keywords",
        "main_action",
        "risk_topic",
        "primary_scene_sentence",
        "past_check_status",
        "relationship_status",
        "primary_chart_type",
        "active_chart_type",
        "active_type_role",
        "active_type_confidence",
        "monthly_phase",
    }
)


def _empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    return False


def _validate_window_order(prefix: str, label: str, index: int, window: dict[str, object]) -> list[str]:
    start = window.get("start_datetime")
    end = window.get("end_datetime")
    if not start or not end:
        return []
    try:
        start_dt = datetime.fromisoformat(str(start))
        end_dt = datetime.fromisoformat(str(end))
    except ValueError:
        return [f"{prefix}: {label}[{index}] invalid datetime"]
    if start_dt >= end_dt:
        return [f"{prefix}: {label}[{index}] end_datetime must be after start_datetime"]
    return []


def _validate_feature_axes(prefix: str, label: str, feature_axes: object, require_personality_axis: bool = True) -> list[str]:
    errors: list[str] = []
    if not isinstance(feature_axes, list):
        return [f"{prefix}: {label} must be a list"]
    if not feature_axes:
        return [f"{prefix}: {label} must not be empty"]

    has_personality_axis = False
    for index, axis in enumerate(feature_axes):
        if not isinstance(axis, dict):
            errors.append(f"{prefix}: {label}[{index}] must be a dict")
            continue
        missing = sorted(REQUIRED_FEATURE_AXIS_KEYS.difference(axis))
        if missing:
            errors.append(f"{prefix}: {label}[{index}] missing {', '.join(missing)}")
        category = axis.get("category")
        if category not in FEATURE_AXIS_CATEGORIES:
            errors.append(f"{prefix}: {label}[{index}] invalid category")
        if category == "personality":
            has_personality_axis = True
        confidence = axis.get("confidence")
        if confidence not in FEATURE_AXIS_CONFIDENCE:
            errors.append(f"{prefix}: {label}[{index}] invalid confidence")
        score = axis.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            errors.append(f"{prefix}: {label}[{index}] score out of range")
        if not isinstance(axis.get("basis_codes"), list) or not axis.get("basis_codes"):
            errors.append(f"{prefix}: {label}[{index}] missing basis_codes")
        if not isinstance(axis.get("counter_signals"), list):
            errors.append(f"{prefix}: {label}[{index}] counter_signals must be a list")
        sentence = axis.get("customer_sentence")
        if not isinstance(sentence, str) or not sentence.startswith("당신"):
            errors.append(f"{prefix}: {label}[{index}] customer_sentence must address customer")
    if require_personality_axis and not has_personality_axis:
        errors.append(f"{prefix}: {label} missing personality axis")
    return errors


def validate_event_packet_contract(packet: EventPacket) -> list[str]:
    """Return human-readable contract errors for one event packet."""

    errors: list[str] = []
    prefix = packet.packet_id or "<missing_packet_id>"

    for field_name in ("packet_id", "domain", "period_label", "common_template_id", "domain_template_id", "type_template_id"):
        if _empty(getattr(packet, field_name)):
            errors.append(f"{prefix}: missing {field_name}")

    missing_slots = sorted(REQUIRED_TEMPLATE_SLOT_KEYS.difference(packet.template_slots))
    if missing_slots:
        errors.append(f"{prefix}: missing template slots {', '.join(missing_slots)}")

    for key in sorted(NON_EMPTY_TEMPLATE_SLOT_KEYS.intersection(packet.template_slots)):
        if _empty(packet.template_slots[key]):
            errors.append(f"{prefix}: empty template slot {key}")

    if packet.template_slots.get("domain") != packet.domain:
        errors.append(f"{prefix}: domain slot mismatch")
    if packet.template_slots.get("period_label") != packet.period_label:
        errors.append(f"{prefix}: period_label slot mismatch")
    if packet.template_slots.get("relationship_status") != packet.relationship_status:
        errors.append(f"{prefix}: relationship_status slot mismatch")
    if packet.template_slots.get("event_keywords") != packet.event_keywords:
        errors.append(f"{prefix}: event_keywords slot mismatch")
    if packet.template_slots.get("feature_axes") != packet.feature_axes:
        errors.append(f"{prefix}: feature_axes slot mismatch")

    if packet.domain in {"love", "marriage"} and not packet.domain_template_id.startswith(f"T-{packet.domain.upper()}"):
        errors.append(f"{prefix}: relationship domain template mismatch")

    timing_markers = packet.template_slots.get("timing_markers")
    if not isinstance(timing_markers, list):
        errors.append(f"{prefix}: timing_markers slot must be a list")
    timing_windows = packet.template_slots.get("timing_windows")
    if not isinstance(timing_windows, list):
        errors.append(f"{prefix}: timing_windows slot must be a list")
    for index, window in enumerate(timing_windows or []):
        if not isinstance(window, dict):
            errors.append(f"{prefix}: timing_windows[{index}] must be a dict")
            continue
        for key in ("period_label", "period_scope", "monthly_phase", "intensity_score"):
            if key not in window:
                errors.append(f"{prefix}: timing_windows[{index}] missing {key}")
        errors.extend(_validate_window_order(prefix, "timing_windows", index, window))
    feature_axes = packet.template_slots.get("feature_axes")
    errors.extend(_validate_feature_axes(prefix, "feature_axes", feature_axes))

    return errors


def validate_analysis_contract(analysis: AnalysisResult) -> list[str]:
    """Return all template contract errors for an analysis result."""

    errors: list[str] = []
    if not analysis.event_packets:
        return ["analysis: no event packets"]
    for packet in analysis.event_packets:
        errors.extend(validate_event_packet_contract(packet))
    return errors


def validate_product_output_item_contract(item: ProductOutputItem) -> list[str]:
    """Return contract errors for a product output item."""

    errors: list[str] = []
    prefix = item.packet_id or "<missing_product_packet_id>"

    for field_name in (
        "packet_id",
        "domain",
        "domain_label",
        "period_label",
        "title",
        "summary",
        "detail",
        "action",
        "risk",
        "common_template_id",
        "domain_template_id",
        "type_template_id",
        "expression_strength",
    ):
        if _empty(getattr(item, field_name)):
            errors.append(f"{prefix}: missing product {field_name}")

    if item.event_probability_score <= 0:
        errors.append(f"{prefix}: missing product event_probability_score")
    if not item.basis_summary:
        errors.append(f"{prefix}: missing product basis_summary")
    if not item.event_keywords:
        errors.append(f"{prefix}: missing product event_keywords")
    if set(item.score_labels) != {"opportunity", "risk", "change", "probability", "confidence"}:
        errors.append(f"{prefix}: product score_labels mismatch")
    if not isinstance(item.timing_windows, list):
        errors.append(f"{prefix}: product timing_windows must be a list")
    for index, window in enumerate(item.timing_windows):
        if not isinstance(window, dict):
            errors.append(f"{prefix}: product timing_windows[{index}] must be a dict")
            continue
        errors.extend(_validate_window_order(prefix, "product timing_windows", index, window))
    errors.extend(_validate_feature_axes(prefix, "product feature_axes", item.feature_axes))

    missing_slots = sorted(REQUIRED_TEMPLATE_SLOT_KEYS.difference(item.template_slots))
    if missing_slots:
        errors.append(f"{prefix}: product missing template slots {', '.join(missing_slots)}")

    if item.template_slots.get("relationship_status") != item.relationship_status:
        errors.append(f"{prefix}: product relationship_status slot mismatch")
    if item.template_slots.get("past_check_status") != item.past_check_status:
        errors.append(f"{prefix}: product past_check_status slot mismatch")
    if item.template_slots.get("feature_axes") != item.feature_axes:
        errors.append(f"{prefix}: product feature_axes slot mismatch")
    if item.domain in {"love", "marriage"} and item.relationship_status != "unknown" and not item.relationship_context:
        errors.append(f"{prefix}: missing product relationship_context")
    if item.relationship_status != "unknown" and not item.relationship_status_label:
        errors.append(f"{prefix}: missing product relationship_status_label")
    if item.template_slots.get("domain") != item.domain:
        errors.append(f"{prefix}: product domain slot mismatch")
    if item.template_slots.get("period_label") != item.period_label:
        errors.append(f"{prefix}: product period_label slot mismatch")
    context = item.judgment_context
    if not isinstance(context, dict) or context.get("version") != "domain_judgment_context_v1":
        errors.append(f"{prefix}: missing product judgment_context")
    else:
        if context.get("domain") != item.domain:
            errors.append(f"{prefix}: product judgment_context domain mismatch")
        if not isinstance(context.get("core_conclusion"), str) or not context.get("core_conclusion"):
            errors.append(f"{prefix}: product judgment_context missing core_conclusion")
        material_layers = context.get("material_layers")
        if not isinstance(material_layers, list) or len(material_layers) < 5:
            errors.append(f"{prefix}: product judgment_context material_layers too sparse")
        coverage = context.get("material_coverage")
        required_coverage = {
            "month_command",
            "branch_foundation",
            "hidden_stem_storage",
            "element_distribution",
            "ten_god_distribution",
            "fortune_activation",
        }
        if not isinstance(coverage, dict) or any(not coverage.get(key) for key in required_coverage):
            errors.append(f"{prefix}: product judgment_context material coverage incomplete")

    return errors


def validate_product_output_section_contract(section: ProductOutputSection, item_by_id: dict[str, ProductOutputItem]) -> list[str]:
    """Return contract errors for a product report section."""

    errors: list[str] = []
    prefix = section.section_id or "<missing_section_id>"

    for field_name in ("section_id", "packet_id", "detail_level", "domain", "domain_label", "period_label", "heading", "lead"):
        if _empty(getattr(section, field_name)):
            errors.append(f"{prefix}: missing section {field_name}")

    if not section.paragraphs:
        errors.append(f"{prefix}: missing section paragraphs")
    if not section.key_points:
        errors.append(f"{prefix}: missing section key_points")

    item = item_by_id.get(section.packet_id)
    if item is None:
        errors.append(f"{prefix}: section packet_id has no matching item")
        return errors

    if section.product_tier != item.product_tier:
        errors.append(f"{prefix}: section tier mismatch")
    expected_detail_level = {"free": "brief", "basic": "standard", "premium": "expanded"}[section.product_tier]
    if section.detail_level != expected_detail_level:
        errors.append(f"{prefix}: section detail_level mismatch")
    if section.domain != item.domain:
        errors.append(f"{prefix}: section domain mismatch")
    if section.domain_label != item.domain_label:
        errors.append(f"{prefix}: section domain_label mismatch")
    if section.period_label != item.period_label:
        errors.append(f"{prefix}: section period_label mismatch")
    if section.relationship_status != item.relationship_status:
        errors.append(f"{prefix}: section relationship_status mismatch")
    if section.relationship_status_label != item.relationship_status_label:
        errors.append(f"{prefix}: section relationship_status_label mismatch")
    if section.template_ids.get("common") != item.common_template_id:
        errors.append(f"{prefix}: section common template mismatch")
    if section.template_ids.get("domain") != item.domain_template_id:
        errors.append(f"{prefix}: section domain template mismatch")
    if section.template_ids.get("type") != item.type_template_id:
        errors.append(f"{prefix}: section type template mismatch")
    if section.feature_axes != item.feature_axes:
        errors.append(f"{prefix}: section feature_axes mismatch")

    return errors


def validate_product_output_contract(output: ProductOutput) -> list[str]:
    """Return all contract errors for a rendered product output."""

    errors: list[str] = []
    if not output.items:
        return ["product_output: no items"]
    for item in output.items:
        errors.extend(validate_product_output_item_contract(item))
    if len(output.sections) != len(output.items):
        errors.append("product_output: section count mismatch")
    item_by_id = {item.packet_id: item for item in output.items}
    for section in output.sections:
        errors.extend(validate_product_output_section_contract(section, item_by_id))
    if not output.schema_version:
        errors.append("product_output: missing schema_version")
    if not output.engine_manifest:
        errors.append("product_output: missing engine_manifest")
    else:
        required_manifest_keys = {
            "manifest_schema_version",
            "analysis_engine_version",
            "product_catalog_version",
            "customer_language_policy_version",
            "report_renderer_version",
            "patch_contract_version",
            "product_tier",
        }
        if not required_manifest_keys.issubset(output.engine_manifest):
            errors.append("product_output: engine_manifest missing required fields")
        if output.engine_manifest.get("product_tier") != output.product_tier:
            errors.append("product_output: engine_manifest tier mismatch")
    if not output.target_years:
        errors.append("product_output: missing target_years")
    if any(not isinstance(year, int) or isinstance(year, bool) for year in output.target_years):
        errors.append("product_output: target_years must contain integer years")
    if not output.calibration_status:
        errors.append("product_output: missing calibration_status")
    if not output.calibration_label:
        errors.append("product_output: missing calibration_label")
    if output.warnings and not output.warning_labels:
        errors.append("product_output: missing warning_labels")
    expected_domains = {"money", "career", "love", "marriage"}
    if set(output.domain_coverage) != expected_domains:
        errors.append("product_output: domain_coverage mismatch")
    if set(output.domain_coverage_labels) != expected_domains:
        errors.append("product_output: domain_coverage_labels mismatch")
    invalid_statuses = set(output.domain_coverage.values()).difference(
        {"included", "omitted_by_tier", "restricted", "not_generated"}
    )
    if invalid_statuses:
        errors.append("product_output: invalid domain_coverage status")
    if not output.life_feature_summary:
        errors.append("product_output: missing life_feature_summary")
    else:
        for key in ("top_axes", "caution_axes", "summary_sentences"):
            if key not in output.life_feature_summary:
                errors.append(f"product_output: life_feature_summary missing {key}")
        for key in ("top_axes", "caution_axes"):
            axes = output.life_feature_summary.get(key, [])
            if not isinstance(axes, list) or not axes:
                errors.append(f"product_output: life_feature_summary {key} must be a non-empty list")
                continue
            errors.extend(
                _validate_feature_axes(
                    "product_output",
                    f"life_feature_summary {key}",
                    axes,
                    require_personality_axis=False,
                )
            )
        summary_sentences = output.life_feature_summary.get("summary_sentences", [])
        if not isinstance(summary_sentences, list) or not summary_sentences:
            errors.append("product_output: life_feature_summary summary_sentences must be a non-empty list")
        elif any(not isinstance(sentence, str) or not sentence.startswith("당신") for sentence in summary_sentences):
            errors.append("product_output: life_feature_summary summary_sentences must address customer")
    if output.product_tier == "premium":
        if not output.premium_candidate_sections:
            errors.append("product_output: missing premium candidate sections")
        for section in output.premium_candidate_sections:
            prefix = f"product_output candidate section {section.section_key}"
            if not section.title:
                errors.append(f"{prefix}: missing title")
            if not section.opening or not section.body or not section.summary:
                errors.append(f"{prefix}: incomplete prose split")
            if section.domain == "life_timing":
                if not section.timing_sentences:
                    errors.append(f"{prefix}: missing timing sentences")
                if not section.timing_year_label or not section.timing_age_label:
                    errors.append(f"{prefix}: missing timing labels")
        if not output.premium_detail_sections:
            errors.append("product_output: missing premium detail sections")
        for detail in output.premium_detail_sections:
            prefix = f"product_output premium detail {detail.entry_key}"
            if not detail.title or not detail.judgment:
                errors.append(f"{prefix}: missing title or judgment")
            if not detail.event_scenes:
                errors.append(f"{prefix}: missing event scenes")
            if detail.score < 44:
                errors.append(f"{prefix}: score below selection threshold")
    elif output.premium_candidate_sections:
        errors.append("product_output: non-premium output must not include premium candidate sections")
    elif output.premium_detail_sections:
        errors.append("product_output: non-premium output must not include premium detail sections")
    if not output.catalog_entries:
        errors.append("product_output: missing catalog_entries")
    for entry in output.catalog_entries:
        if not isinstance(entry, dict):
            errors.append("product_output: catalog entry must be a dict")
            continue
        required_keys = {
            "entry_id",
            "title",
            "kind",
            "source_domains",
            "tiers",
            "section_titles",
            "is_locked",
            "preview",
            "display_group",
            "content_mode",
            "surface_hint",
            "linked_item_indexes",
            "availability_status",
            "content_summary",
            "content_blocks",
        }
        if not required_keys.issubset(entry):
            errors.append("product_output: catalog entry missing required fields")
        if not entry.get("entry_id") or not entry.get("title"):
            errors.append("product_output: catalog entry missing id or title")
        if not isinstance(entry.get("source_domains"), list) or not entry.get("source_domains"):
            errors.append("product_output: catalog entry missing source domains")
        if not isinstance(entry.get("section_titles"), list) or not entry.get("section_titles"):
            errors.append("product_output: catalog entry missing section titles")
        for field_name in ("preview", "display_group", "content_mode", "surface_hint"):
            if not str(entry.get(field_name) or "").strip():
                errors.append(f"product_output: catalog entry missing {field_name}")
        if not isinstance(entry.get("linked_item_indexes"), list):
            errors.append("product_output: catalog entry missing linked_item_indexes")
        if entry.get("availability_status") not in {"locked", "has_visible_detail", "menu_only"}:
            errors.append("product_output: catalog entry invalid availability_status")
        if not str(entry.get("content_summary") or "").strip():
            errors.append("product_output: catalog entry missing content_summary")
        content_blocks = entry.get("content_blocks")
        if not isinstance(content_blocks, list) or not content_blocks:
            errors.append("product_output: catalog entry missing content_blocks")
        else:
            for block in content_blocks:
                if not isinstance(block, dict):
                    errors.append("product_output: catalog content block must be a dict")
                    continue
                for field_name in ("block_id", "role", "heading", "body", "source_domains"):
                    if field_name not in block:
                        errors.append(f"product_output: catalog content block missing {field_name}")
                for field_name in ("block_id", "role", "heading", "body"):
                    if not str(block.get(field_name) or "").strip():
                        errors.append(f"product_output: catalog content block empty {field_name}")
                if not isinstance(block.get("source_domains"), list):
                    errors.append("product_output: catalog content block source_domains must be a list")
    return errors
