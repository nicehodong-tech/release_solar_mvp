from __future__ import annotations

import sys
import unittest
from pathlib import Path


RELEASE_ROOT = Path(__file__).resolve().parents[1]
if str(RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(RELEASE_ROOT))

from saju_analysis_engine import analyze_chart  # noqa: E402
from saju_analysis_engine.constants import BRANCH_HIDDEN_STEMS  # noqa: E402
from saju_analysis_engine.features import _preserve_cycle_axis_evidence  # noqa: E402
from saju_birth_engine import BirthInput, build_birth_chart  # noqa: E402
from saju_birth_engine.constants import HIDDEN_STEMS  # noqa: E402
from saju_web.app import _operational_snapshot  # noqa: E402
from saju_web.report_service import (  # noqa: E402
    DISPLAY_HIDDEN_STEMS_BY_BRANCH_KEY,
    STEM_HANJA_BY_KEY,
    build_report_payload,
)


SAMPLE_INPUT = {
    "birthDate": "19991212",
    "birthTime": "myo",
    "gender": "male",
    "calendarType": "solar",
    "relationshipStatus": "unknown",
    "targetYear": 2026,
    "tier": "public_mvp",
}


class EngineEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        chart = build_birth_chart(
            BirthInput(1999, 12, 12, 7, 10, city="chuncheon", gender="male")
        )
        cls.analysis = analyze_chart(chart, target_years=[2028])

    def test_cycle_versions_match_current_relation_contract(self) -> None:
        profile = self.analysis.chart_structure.cycle_regulation_profile
        self.assertEqual(profile["version"], "cycle_regulation_v4_relation_two_axis")
        self.assertEqual(
            profile["principle_matrix"]["version"],
            "cycle_principle_matrix_v3_relation_two_axis",
        )

    def test_branch_relation_evidence_reaches_metric_axis(self) -> None:
        axis = self.analysis.chart_structure.life_feature_profile.axes["money_potential"]
        evidence_codes = [*axis.basis_codes, *axis.counter_signals]
        self.assertTrue(any("branch_cycle_" in code for code in evidence_codes))

    def test_evidence_only_preservation_does_not_change_score(self) -> None:
        adjustments = {
            "money_potential": {
                "score": 4.25,
                "basis_codes": ["existing_support"],
                "counter_signals": [],
            }
        }
        branch_candidate = {
            "priority": 20,
            "polarity": "support",
            "relation": "branch_cycle",
            "basis_code": "feature_cycle_regulation_branch_cycle_example",
            "counter_code": "feature_cycle_regulation_counter_branch_cycle_example",
        }
        _preserve_cycle_axis_evidence(
            adjustments,
            "money_potential",
            [branch_candidate],
            [],
        )
        self.assertEqual(adjustments["money_potential"]["score"], 4.25)
        self.assertIn(
            "feature_cycle_regulation_branch_cycle_example",
            adjustments["money_potential"]["basis_codes"],
        )

    def test_hidden_stem_source_display_and_calculation_sets_match(self) -> None:
        branch_hanja = {
            "ja": "子", "chuk": "丑", "in": "寅", "myo": "卯",
            "jin": "辰", "sa": "巳", "o": "午", "mi": "未",
            "sin": "申", "yu": "酉", "sul": "戌", "hae": "亥",
        }
        expected_main = {
            "ja": "gye", "chuk": "gi", "in": "gap", "myo": "eul",
            "jin": "mu", "sa": "byeong", "o": "jeong", "mi": "gi",
            "sin": "gyeong", "yu": "sin", "sul": "mu", "hae": "im",
        }
        for branch_key, hanja in branch_hanja.items():
            with self.subTest(branch=branch_key):
                calculation = BRANCH_HIDDEN_STEMS[branch_key]
                calculation_keys = {stem for stem, _weight in calculation}
                display_keys = set(DISPLAY_HIDDEN_STEMS_BY_BRANCH_KEY[branch_key])
                source_keys = {
                    key
                    for key, stem_hanja in STEM_HANJA_BY_KEY.items()
                    if stem_hanja in HIDDEN_STEMS[hanja]
                }
                self.assertEqual(calculation_keys, display_keys)
                self.assertEqual(calculation_keys, source_keys)
                self.assertEqual(calculation[0][0], expected_main[branch_key])
                self.assertAlmostEqual(sum(weight for _stem, weight in calculation), 1.0)

    def test_unknown_birth_time_excludes_hour_from_natal_analysis(self) -> None:
        charts = []
        for hour in (6, 12, 18):
            chart = build_birth_chart(
                BirthInput(1996, 4, 3, hour, 0, city="seoul", gender="female")
            )
            chart.calculation_trace["birth_time_unknown"] = True
            charts.append(analyze_chart(chart, target_years=[2026, 2027]))

        structures = [analysis.chart_structure for analysis in charts]
        for structure in structures:
            self.assertNotIn("hour", structure.four_pillars)
        self.assertTrue(all(
            structure.element_profile.scores == structures[0].element_profile.scores
            for structure in structures[1:]
        ))
        self.assertTrue(all(
            structure.ten_god_profile.visible_counts == structures[0].ten_god_profile.visible_counts
            and structure.ten_god_profile.hidden_counts == structures[0].ten_god_profile.hidden_counts
            for structure in structures[1:]
        ))


class WebProductContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = build_report_payload(dict(SAMPLE_INPUT), defer_detail=False)
        cls.report = cls.payload["report"]

    def test_health_contract_is_available(self) -> None:
        health = _operational_snapshot()
        self.assertTrue(health["ok"])
        self.assertEqual(health["version"], "judgment-v22-hidden-stem-complete")
        self.assertEqual(health["runtime"]["service"], "local")
        self.assertEqual(health["runtime"]["revision"], "local")
        self.assertIn("analysisWorkers", health)
        self.assertIn("jobs", health)
        self.assertIn("cache", health)

    def test_current_product_navigation_contract(self) -> None:
        sections = self.report.get("analysis_sections") or []
        domains = [str(section.get("domain") or "") for section in sections]
        self.assertEqual(
            [domain for domain in domains if domain in {
                "personality", "money", "career", "love", "marriage", "honor", "social"
            }],
            ["personality", "money", "career", "love", "marriage", "honor", "social"],
        )
        for domain in ("timing", "year_2026", "year_2027"):
            self.assertIn(domain, domains)
        self.assertEqual(self.report.get("premium_sections"), [])
        self.assertEqual(self.report.get("free_profile_preview"), {})
        self.assertTrue(self.report.get("factor_sections"))
        self.assertTrue(self.report.get("analysis_engine_contract", {}).get("gyeokguk_contextual"))

    def test_sample_time_bucket_matches_the_0710_hour_pillar(self) -> None:
        exact = build_birth_chart(
            BirthInput(1999, 12, 12, 7, 10, city="seoul", gender="male")
        )
        self.assertEqual(self.payload["chart"]["fourPillars"]["hour"], exact.hour_pillar.label)
        self.assertEqual(exact.hour_pillar.label, "乙卯")

    def test_metric_scores_are_quality_oriented_and_bounded(self) -> None:
        sections = self.report.get("analysis_sections") or []
        seen_labels: dict[str, set[str]] = {}
        for section in sections:
            if not isinstance(section, dict):
                continue
            domain = str(section.get("domain") or "")
            if domain == "timing":
                continue
            metrics = []
            if domain.startswith("year_"):
                for group in section.get("metric_groups") or []:
                    metrics.extend(group.get("items") or [])
            else:
                metrics = list(section.get("feature_axes") or [])
            labels = seen_labels.setdefault(domain, set())
            for metric in metrics:
                with self.subTest(domain=domain, label=metric.get("label")):
                    score = metric.get("score")
                    self.assertIsInstance(score, int)
                    self.assertGreaterEqual(score, 0)
                    self.assertLessEqual(score, 100)
                    self.assertEqual(metric.get("score_direction"), "higher_is_better")
                    self.assertEqual(metric.get("quality_score", score), score)
                    label = str(metric.get("label") or "")
                    self.assertNotIn(label, labels)
                    labels.add(label)
                    if metric.get("polarity") == "risk":
                        self.assertEqual(metric.get("risk_intensity_score"), 100 - score)

    def test_contextual_basis_is_fully_source_verified(self) -> None:
        contextual = (
            self.report.get("analysis_engine_contract", {})
            .get("gyeokguk_contextual", {})
        )
        profiles = contextual.get("source_evidence_profiles") or []
        self.assertGreaterEqual(len(profiles), 25)
        for profile in profiles:
            with self.subTest(title=profile.get("title")):
                self.assertTrue(profile.get("source_verified"))
                self.assertTrue(str(profile.get("source_file") or "").endswith(".md"))
                self.assertTrue(profile.get("source_section"))
                self.assertTrue(
                    profile.get("description_parts")
                    or profile.get("keyword_groups")
                    or profile.get("keywords")
                )

    def test_timing_keeps_eight_decades_and_the_verified_2021_caution(self) -> None:
        timing = next(
            section
            for section in self.report.get("analysis_sections") or []
            if section.get("domain") == "timing"
        )
        decades = timing.get("timing_decades") or []
        self.assertEqual(len(decades), 8)
        for decade in decades:
            with self.subTest(label=decade.get("label")):
                self.assertIn(len(decade.get("good") or []), {1, 2})
                self.assertIn(len(decade.get("caution") or []), {1, 2})
        caution_2021 = [
            event
            for decade in decades
            for event in decade.get("caution") or []
            if event.get("year") == 2021
        ]
        self.assertTrue(caution_2021)
        self.assertTrue(all(event.get("domain") == "career" for event in caution_2021))

    def test_unknown_birth_time_payload_has_no_hour_pillar_or_hour_evidence(self) -> None:
        unknown_payload = build_report_payload(
            {
                **SAMPLE_INPUT,
                "birthDate": "19960403",
                "birthTime": "unknown",
                "gender": "female",
            },
            defer_detail=False,
        )
        self.assertFalse(unknown_payload["request"]["birthTimeKnown"])
        self.assertNotIn("hour", unknown_payload["chart"]["fourPillars"])
        self.assertNotIn(
            "hour",
            {row.get("key") for row in unknown_payload["chart"].get("pillarRows") or []},
        )
        self.assertFalse(any(
            "시주" in str(section) or "hour" in str(section).lower()
            for section in unknown_payload["report"].get("factor_sections") or []
        ))

    def test_annual_sections_keep_eight_complete_groups(self) -> None:
        sections = {
            section["domain"]: section
            for section in self.report.get("analysis_sections") or []
            if isinstance(section, dict) and section.get("domain") in {"year_2026", "year_2027"}
        }
        self.assertEqual(set(sections), {"year_2026", "year_2027"})
        expected_keys = {
            "overall", "career", "money", "social", "love", "marriage", "honor", "condition"
        }
        for domain, section in sections.items():
            with self.subTest(domain=domain):
                groups = section.get("metric_groups") or []
                self.assertEqual({group.get("key") for group in groups}, expected_keys)
                self.assertTrue(all(group.get("items") for group in groups))
                self.assertTrue(all(group.get("total_indicator_labels") for group in groups))
                self.assertEqual(len(section.get("representative_metrics") or []), 8)

    def test_static_assets_use_current_contract(self) -> None:
        index_html = (RELEASE_ROOT / "saju_web" / "static" / "index.html").read_text(encoding="utf-8")
        app_js = (RELEASE_ROOT / "saju_web" / "static" / "app-v2.js").read_text(encoding="utf-8")
        self.assertIn("production-release-v55", index_html)
        self.assertIn("annualGroupAggregateItems", app_js)
        self.assertIn("total_indicator_labels", app_js)
        self.assertIn("rawMetricJudgmentStateType", app_js)
        self.assertIn("metricDisplayStateType", app_js)
        self.assertNotIn('data-submit-tier="free"', index_html)

    def test_web_interstitial_uses_the_configured_ad_unit_safely(self) -> None:
        index_html = (RELEASE_ROOT / "saju_web" / "static" / "index.html").read_text(encoding="utf-8")
        gam_js = (RELEASE_ROOT / "saju_web" / "static" / "gam-interstitial.js").read_text(encoding="utf-8")
        self.assertIn(
            'name="google-ad-manager-interstitial-unit" content="/23363471499/leehyeon_web_interstitial"',
            index_html,
        )
        self.assertIn("/gam-interstitial.js?v=gam-web-interstitial-v3", index_html)
        self.assertIn("securepubads.g.doubleclick.net/tag/js/gpt.js", gam_js)
        self.assertIn("OutOfPageFormat.INTERSTITIAL", gam_js)
        self.assertIn("LEEHYEON_ARM_GAM_AFTER_COUPANG", gam_js)
        self.assertIn('reason = "waiting_for_coupang_departure"', gam_js)
        self.assertIn("backward: false", gam_js)
        self.assertIn("continueReading: false", gam_js)
        self.assertIn("unhideWindow: true", gam_js)
        self.assertIn("navBar: false", gam_js)
        self.assertIn("inactivity: false", gam_js)
        self.assertIn("endOfArticle: false", gam_js)

    def test_web_interstitial_only_uses_natural_internal_transitions(self) -> None:
        index_html = (RELEASE_ROOT / "saju_web" / "static" / "index.html").read_text(encoding="utf-8")
        app_js = (RELEASE_ROOT / "saju_web" / "static" / "app-v2.js").read_text(encoding="utf-8")
        self.assertIn('<a class="report-entry-card', app_js)
        self.assertIn('<a class="domain-direct-card', app_js)
        self.assertIn('data-google-interstitial="false">쿠팡 방문하고 결과 보기', app_js)
        self.assertIn('typeof window.LEEHYEON_ARM_GAM_AFTER_COUPANG === "function"', app_js)
        self.assertIn("window.LEEHYEON_ARM_GAM_AFTER_COUPANG();", app_js)
        self.assertGreaterEqual(index_html.count('data-google-interstitial="false"'), 2)

    def test_cloud_run_staging_contract_is_isolated_and_preserves_engine_data(self) -> None:
        dockerfile = (RELEASE_ROOT / "Dockerfile").read_text(encoding="utf-8")
        dockerignore = (RELEASE_ROOT / ".dockerignore").read_text(encoding="utf-8")
        gcloudignore = (RELEASE_ROOT / ".gcloudignore").read_text(encoding="utf-8")
        deploy_script = (
            RELEASE_ROOT / "deploy" / "cloudrun" / "deploy-staging.ps1"
        ).read_text(encoding="utf-8")
        parity_script = (
            RELEASE_ROOT / "scripts" / "cloudrun_parity_check.py"
        ).read_text(encoding="utf-8")

        self.assertIn("FROM python:3.12-slim", dockerfile)
        self.assertIn("COPY --chown=saju:saju saju_analysis_engine", dockerfile)
        self.assertIn('USER saju', dockerfile)
        self.assertIn('"--host", "0.0.0.0"', dockerfile)
        self.assertNotIn("**/*.md", dockerignore)
        self.assertNotIn("*.jsonl", dockerignore)
        self.assertNotIn("**/*.md", gcloudignore)
        self.assertNotIn("*.jsonl", gcloudignore)
        self.assertIn('--min-instances 1', deploy_script)
        self.assertIn('--max-instances 1', deploy_script)
        self.assertIn('--no-cpu-throttling', deploy_script)
        self.assertIn('aisaju-leehyeon-staging', deploy_script)
        self.assertNotIn('aisajuleehyeon.com', deploy_script)
        self.assertIn('"chart": detail.get("chart")', parity_script)
        self.assertIn('"report": detail.get("report")', parity_script)

    def test_cloud_run_cutover_is_preverified_and_reversible(self) -> None:
        deploy_root = RELEASE_ROOT / "deploy" / "cloudrun"
        preflight = (deploy_root / "preflight.ps1").read_text(encoding="utf-8")
        certificate = (deploy_root / "prepare-certificate.ps1").read_text(encoding="utf-8")
        promotion = (deploy_root / "promote-production.ps1").read_text(encoding="utf-8")
        edge = (deploy_root / "prepare-edge.ps1").read_text(encoding="utf-8")
        verify_edge = (deploy_root / "verify-edge.ps1").read_text(encoding="utf-8")
        verify_cutover = (deploy_root / "verify-cutover.ps1").read_text(encoding="utf-8")
        rollback = (deploy_root / "verify-rollback.ps1").read_text(encoding="utf-8")
        runbook = (RELEASE_ROOT / "CLOUD_RUN_CUTOVER_2026-07-23.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("unittest discover -s tests -v", preflight)
        self.assertIn("billing projects describe", preflight)
        self.assertIn("mqquvbd6c9bd03f8.sel3.cloudtype.app", preflight)
        self.assertIn("dns-authorizations create", certificate)
        self.assertIn("Certificate state", certificate)
        self.assertIn("verify-staging.ps1", promotion)
        self.assertIn("spec.template.spec.containers[0].image", promotion)
        self.assertIn("--max-instances 1", promotion)
        self.assertIn("serverless", edge)
        self.assertIn("EXTERNAL_MANAGED", edge)
        self.assertIn("managed.state", edge)
        self.assertIn("--resolve", verify_edge)
        self.assertIn("cloudrun_parity_check.py", verify_edge)
        self.assertIn("Resolve-DnsName", verify_cutover)
        self.assertIn("cloudrun_parity_check.py", verify_cutover)
        self.assertIn("CloudtypeTarget", rollback)
        self.assertIn("jobs.running", runbook)
        self.assertIn("jobs.queued", runbook)
        self.assertIn("TTL 600", runbook)
        for source in (certificate, promotion, edge, verify_edge):
            self.assertNotIn("Remove-DnsServerResourceRecord", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
