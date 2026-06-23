# Saju Analysis Engine

This package is the rule-based analysis layer placed after the verified
birth-chart engine.

Scope of this layer:

- Accept one finalized `BirthChartResult`.
- Preserve the birth-chart engine as an upstream dependency.
- Build natal structure signals: five elements, season, johu, day-master
  strength, illness-medicine, ten-god distribution, branch interactions,
  twelve growth stages, and selected shinsal markers.
- Preserve combination profiles for visible heavenly stems, hidden stems,
  stem-branch relations, and ten-god chains so element/ten-god pairings such as
  officer-resource-self, output-wealth, peer-wealth, and stem-root relations are
  not lost in aggregate scores.
- Preserve pure element-combination profiles before ten-god translation. This
  keeps source meanings such as Eul-Byeong social expansion, relationship-based
  growth, and organizational cohesion separate from day-master ten-god readings.
- Preserve directional element/stem base values such as Eul seeing Byeong and
  Byeong seeing Eul as separate signals before later ten-god and seasonal
  corrections are applied.
- Build pattern and useful-element candidates without treating them as final
  deterministic labels.
- Build flow signals for daeun, annual years, quarters, and solar months.
- Convert domain scores into event packets for money, career, love, and
  marriage.
- Preserve differentiated life-feature axes such as money potential, asset
  retention, social success potential, career achievement, self-direction,
  practical planning, relationship stability, and crisis recovery.
- Accept optional past-event check answers and adjust confidence/domain
  priority without changing the birth chart.
- Accept relationship status and route love/marriage wording without changing
  the chart judgment.
- Produce deterministic Korean preview sentences, product output items, and
  report sections that preserve the same packet IDs and template IDs.
- Render customer-facing mobile cards, web detail sections, and premium report
  sections from ProductOutput without recalculating chart judgment.
- Keep mobile cards and web detail sections aligned as the same judgment shown
  at different screen densities, not as separate interpretations.
- Use public report packet IDs in CustomerReport so internal event-code packet
  IDs are not exposed to customer-facing payloads.
- Export customer reports as Markdown for sample review or report-file
  generation.
- Preserve template slots, event keywords, timing windows, judgment scores,
  basis summaries, counter-signal summaries, and relationship status through
  the product-output layer.
- Preserve calibration labels, warning labels, domain coverage labels, and
  output warnings so UI layers do not have to reinterpret internal codes.
- Preserve product-output schema version and target years at the output root so
  API clients can validate the response contract without reading nested traces.
- Preserve runtime manifest metadata through ProductOutput and CustomerReport so
  analysis, product catalog, customer-language, and renderer patch versions can
  be audited later.
- Export `PRODUCT_OUTPUT_SCHEMA_VERSION` from the package root for API-layer
  version checks.
- Export product catalog definitions and `catalog_payload_for_tier()` so API and
  UI layers can build fortune menus without recalculating chart judgment.
- Preserve `catalog_entries` through ProductOutput and CustomerReport, including
  preview text, locked-state hints, visible-detail links, and availability
  status for free/basic/premium product menus.
- Validate chronological timing windows across monthly and quarterly flow
  signals.
- Validate event-packet and product-output contracts so mobile cards and web
  detail views receive the same structured judgment data.

Out of scope for this layer:

- Birth-chart calculation changes.
- Product-page or UI logic.
- Medical, legal, or high-risk deterministic claims.

The output is intentionally a structured judgment packet and product-output
contract rather than a finished fortune essay. Later template and UI layers
should consume this output without recalculating the chart judgment.

See `analysis_engine_output_schema.md` in the workspace root for the current
`ProductOutput` API contract.

See `customer_report_rendering_schema.md` for the customer-facing report
contract built on top of `ProductOutput`.

See `ui_content_block_layout_contract.md` for the mobile/web content block
layout contract used by future UI work.

See `product_catalog_contract.md` and `product_catalog_mvp_snapshot.md` for the
free/basic/premium fortune menu contract, locked-entry behavior, and catalog
availability summary.

See `patch_manifest_contract.md` for the ProductOutput-to-CustomerReport runtime
manifest contract used by future patch audits.

See `customer_report_commercial_writing_standard.md` for the fixed commercial
writing standard used by customer-facing report prose.

See `future_work_quality_standard.md` for the ongoing work standard covering
engine precision, data confidence, customer prose, and three review passes per
major work block.

See `analysis_regression_case_matrix.md` for the current 72-case regression
coverage matrix.

See `customer_report_quality_baseline.md` in the workspace root for the current
customer-report surface quality baseline.

See `customer_report_actual_phrase_snapshot.md` for representative actual
customer-facing Korean phrases generated by the current report renderer.

Run `python scripts/validate_analysis_output.py` from the workspace root for a
JSON summary of the 72-case analysis/product-output contract check, including
schema-version coverage, target-year preservation, and timing-window order.

Run `python scripts/audit_target_year_input_contract.py` for target-year input
contract checks. This verifies empty, duplicate, unsorted, boolean, and
non-integer year rejection, plus single-year, consecutive multi-year, and
non-consecutive multi-year report-title rendering.

Run `python scripts/generate_customer_report_samples.py` for representative
customer-facing Markdown report samples.

Run `python scripts/audit_regression_case_balance.py` for regression-case
distribution checks. This verifies city, decade, gender, boundary-sensitive,
near-midnight, seasonal-boundary, and historical-time-zone coverage.

Run `python scripts/audit_customer_report_quality.py` for customer-report
surface density, length, domain-distribution, and tier-exposure checks.

Run `python scripts/audit_life_feature_axes.py` for differentiated life-feature
axis score distribution checks over the 72 regression cases.

Run `python scripts/audit_combination_profile_contract.py` for combination-layer
contract checks. This verifies heavenly-stem, hidden-stem, stem-branch, and
ten-god-chain profiles over the 72 regression cases, including the canonical
1999-12-12 Chuncheon case and product-output preservation.

Run `python scripts/audit_element_combination_profile_contract.py` for pure
element-combination contract checks. This verifies source-rule preservation,
including the Eul-Byeong element-combination meaning from the local learning
material.

Run `python scripts/audit_directional_interaction_base_contract.py` for
directional base-value checks. This verifies the 25 element-direction rules, 100
stem-direction rules, and canonical preservation of Eul->Byeong and
Byeong->Eul as distinct readings.

Run `python scripts/audit_commercial_axis_contract.py` for commercial
life-feature axis checks. This verifies the 30-axis money/social/personality
contract, the canonical 1999-12-12 Chuncheon 07:10 four pillars, and product
exposure of the nine newly added commercial axes.

Run `python scripts/audit_domain_axis_coverage.py` for domain-specific
feature-axis coverage checks. This verifies that money, career, love, and
marriage judgments keep their expected money/social/personality axis bundles.

Run `python scripts/audit_product_catalog_contract.py` for product catalog
contract checks. This verifies the 18-entry catalog, free-tier 16 visible menu
entries, locked-entry behavior, preview wording, visible-detail links, and
ProductOutput-to-CustomerReport preservation.

Run `python scripts/audit_patch_manifest_contract.py` for patch manifest
contract checks. This verifies ProductOutput.engine_manifest,
CustomerReport.source_engine_manifest, product-tier alignment, and JSON
serialization preservation.

Run `python scripts/audit_operational_metadata_shielding.py` for operational
metadata shielding checks. This verifies that manifest fields stay present in
API payloads but do not leak into customer-facing Markdown or catalog preview
text.

Run `python scripts/run_patch_readiness_smoke.py` after small product, catalog,
or wording patches. This executes the product catalog, patch manifest,
operational metadata shielding, output preservation, and customer prose register
checks without replacing the full precision suite.

Run `python scripts/audit_feature_axis_score_influence.py` for feature-axis
score influence checks. This verifies that life-feature axes affect event
opportunity, risk, change, and probability scores within bounded ranges instead
of remaining as customer-sentence decoration.

Run `python scripts/audit_past_event_sensitivity.py` for past-event calibration
sensitivity checks. This verifies that no-input, matched, partial, unmatched,
skipped, double-matched, mixed, and conflicting answers adjust probabilities and
confidence without changing the natal chart or life-feature profile.

Run `python scripts/audit_past_event_prompt_contract.py` for customer-facing
past-event prompt checks. This verifies that four light-weight options map to
matched, partial, unmatched, and skipped engine answers without asking the
customer to score event intensity. It also verifies zero-prompt and invalid
prompt-count boundary handling for users who skip optional event checks.

Run `python scripts/audit_timing_window_precision.py` for timing-window precision
checks. This verifies solar-term monthly/quarterly windows, domain-focused
timing windows, intensity sorting, and product-output timing preservation.

Run `python scripts/audit_multi_year_output_consistency.py` for multi-year
output consistency checks. This verifies that 2028~2030 analysis output,
product output, customer-report titles, visible period labels, and timing
windows stay inside the requested year range across basic and premium tiers.

Run `python scripts/audit_event_type_diversity.py` for event-type and
customer-sentence diversity checks. This verifies that the 72 regression cases
do not collapse into a single event type, template type, headline, or keyword
surface per domain.

Run `python scripts/audit_relationship_status_rendering.py` for relationship
status rendering checks. This verifies that love and marriage outputs preserve
single, interested, dating, long-term, preparing-marriage, married, and unknown
status labels across mobile cards, web sections, and premium checkpoints.

Run `python scripts/audit_relationship_axis_language.py` for relationship axis
language checks. This verifies that love and marriage feature-axis wording stays
scene-based instead of percentile-based, avoids awkward fragments, and preserves
concrete relationship terms across mobile, web, and premium surfaces.

Run `python scripts/audit_mobile_web_content_consistency.py` for mobile/web
content consistency checks. This verifies that paired mobile cards and web
sections preserve the same public packet ID, headline, action, caution,
representative timing, badges, and representative feature-axis label so later UI
layouts can rearrange blocks without changing conclusions.

Run `python scripts/audit_ui_content_block_contract.py` for UI content-block
readiness checks. This verifies that report headers, notices, mobile cards, web
detail sections, and premium sections expose nonempty layout-ready blocks with
stable roles.

The customer language helpers in `saju_analysis_engine/language_policy.py` also
have direct unit coverage in `tests/test_language_policy.py`. Update those tests
when changing percentile wording, relationship-scene wording, timing phase
labels, timing-window prose, or mobile axis phrases.

Run `python scripts/audit_score_label_and_tier_boundaries.py` for score-label
and product-tier boundary checks. This verifies that visible score labels match
numeric scores, visible items do not carry risk-language filter flags, and
free/basic/premium item counts stay inside their product limits.

Run `python scripts/audit_output_preservation.py` for analysis-to-product and
product-to-customer preservation checks. This verifies that packet scores,
timing windows, feature axes, template slots, relationship status, public report
IDs, and internal-ID shielding remain intact across the output layers.

Run `python scripts/audit_customer_prose_register.py` for customer prose register
checks. This verifies direct address, non-distant subject wording, premium
narrative sentence density, domain-specific life-scene terms, web paragraph
roles, and banned cliche/internal phrases.

Run `python scripts/audit_timing_prose_variety.py` for premium timing prose
variety checks. This verifies that timing paragraphs keep domain-specific life
terms, avoid fixed mechanical openers, and preserve enough opening variation
across money, career, love, and marriage.

Run `python scripts/audit_feature_sentence_quality.py` for life-feature sentence
quality checks. This verifies that money, social, and personality feature-axis
sentences contain concrete life terms, keep enough sentence variation, and are
preserved across mobile, web, and premium customer surfaces.

Run `python scripts/run_precision_audit_suite.py` for the full precision gate.
This executes the unit tests, analysis-output contract, regression-case balance
audit, customer-report quality audit, life-feature axis audit, combination
profile audit, element-combination audit, directional base-value audit,
domain-axis coverage audit, commercial-axis contract audit,
target-year input contract audit, past-event sensitivity audit,
past-event prompt contract audit, feature-axis score influence audit,
timing-window precision audit,
multi-year output consistency audit,
event-type diversity audit,
relationship-status rendering audit, relationship-axis language audit,
mobile/web content consistency audit, UI content-block contract audit,
extension/patch architecture audit, patch-manifest audit, operational-metadata
shielding audit,
score-label/tier-boundary audit,
output-preservation audit, customer prose register audit, feature sentence
quality audit, timing prose variety audit, birth engine reference verification,
and an internal Python AST syntax check. The default output
artifact is `precision_audit_suite_latest.json` in the workspace root.

For future feature additions or patch work, read
`extension_patch_architecture.md` first. It fixes the expected modification path
from birth calculation through analysis axes, domain events, product output,
customer language policy, audits, samples, and documentation.
