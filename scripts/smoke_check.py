from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def _read(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.status, response.read().decode("utf-8")


def _post_json(url: str, payload: dict[str, object]) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def main() -> None:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/")
    status, html = _read(base_url + "/")
    if status != 200 or "사주 이현" not in html:
        raise SystemExit(f"home check failed: status={status}")

    sample = {
        "birthDate": "19991212",
        "birthTime": "myo",
        "gender": "male",
        "calendarType": "solar",
        "relationshipStatus": "unknown",
        "targetYear": 2026,
        "tier": "premium",
    }
    status, text = _post_json(base_url + "/api/judgment", sample)
    payload = json.loads(text)
    if status != 200 or not payload.get("ok"):
        raise SystemExit(f"premium api check failed: status={status}")
    sections = payload.get("report", {}).get("analysis_sections", [])
    if len(sections) < 7:
        raise SystemExit(f"analysis section check failed: count={len(sections)}")

    detail_token = str(payload.get("detailToken") or "").strip()
    if not detail_token:
        raise SystemExit("detail token check failed")
    detail_url = base_url + "/api/judgment-detail?" + urllib.parse.urlencode({"token": detail_token})
    detail_status, detail_text = _read(detail_url)
    detail_payload = json.loads(detail_text)
    contextual = (
        detail_payload.get("report", {})
        .get("analysis_engine_contract", {})
        .get("gyeokguk_contextual", {})
    )
    source_profiles = contextual.get("source_evidence_profiles") or []
    verified_profiles = [
        profile
        for profile in source_profiles
        if isinstance(profile, dict) and profile.get("source_verified") is True
    ]
    if detail_status != 200 or len(source_profiles) < 25 or len(verified_profiles) != len(source_profiles):
        raise SystemExit(
            "contextual source evidence check failed: "
            f"status={detail_status}, profiles={len(source_profiles)}, verified={len(verified_profiles)}"
        )

    print(f"SMOKE_CHECK_OK contextual_source_profiles={len(source_profiles)}")


if __name__ == "__main__":
    main()
