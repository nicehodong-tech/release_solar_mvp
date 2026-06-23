"""Runtime manifest for patchable analysis and report outputs."""

from __future__ import annotations

from typing import Any


ENGINE_MANIFEST_SCHEMA_VERSION = "saju_service_manifest_v1"
ANALYSIS_ENGINE_VERSION = "analysis_engine_mvp_2026_06_08"
PRODUCT_CATALOG_VERSION = "product_catalog_v1"
CUSTOMER_LANGUAGE_POLICY_VERSION = "customer_language_policy_v1"
REPORT_RENDERER_VERSION = "customer_report_renderer_v1"
PATCH_CONTRACT_VERSION = "mvp_patch_contract_v1"


def build_engine_manifest(product_tier: str | None = None) -> dict[str, Any]:
    """Return the version manifest that must travel with product outputs."""

    manifest: dict[str, Any] = {
        "manifest_schema_version": ENGINE_MANIFEST_SCHEMA_VERSION,
        "analysis_engine_version": ANALYSIS_ENGINE_VERSION,
        "product_catalog_version": PRODUCT_CATALOG_VERSION,
        "customer_language_policy_version": CUSTOMER_LANGUAGE_POLICY_VERSION,
        "report_renderer_version": REPORT_RENDERER_VERSION,
        "patch_contract_version": PATCH_CONTRACT_VERSION,
    }
    if product_tier is not None:
        manifest["product_tier"] = product_tier
    return manifest
