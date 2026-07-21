from __future__ import annotations

import sys
import unittest
from pathlib import Path


RELEASE_ROOT = Path(__file__).resolve().parents[1]
if str(RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(RELEASE_ROOT))

from saju_analysis_engine import analyze_chart  # noqa: E402
from saju_analysis_engine.features import _preserve_cycle_axis_evidence  # noqa: E402
from saju_birth_engine import BirthInput, build_birth_chart  # noqa: E402
from saju_web.app import _operational_snapshot  # noqa: E402
from saju_web.report_service import build_report_payload  # noqa: E402


SAMPLE_INPUT = {
    "birthDate": "19991212",
    "birthTime": "jin",
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


class WebProductContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = build_report_payload(dict(SAMPLE_INPUT), defer_detail=False)
        cls.report = cls.payload["report"]

    def test_health_contract_is_available(self) -> None:
        health = _operational_snapshot()
        self.assertTrue(health["ok"])
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
        self.assertIn("production-release-v54", index_html)
        self.assertIn("annualGroupAggregateItems", app_js)
        self.assertIn("total_indicator_labels", app_js)
        self.assertIn("rawMetricJudgmentStateType", app_js)
        self.assertIn("metricDisplayStateType", app_js)
        self.assertNotIn('data-submit-tier="free"', index_html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
