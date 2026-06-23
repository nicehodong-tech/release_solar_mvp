from __future__ import annotations

import json
import sys
import urllib.error
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
    if status != 200 or "AI 사주 : 이현" not in html:
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
    sections = payload.get("report", {}).get("premium_sections", [])
    if len(sections) < 8:
        raise SystemExit(f"premium section check failed: count={len(sections)}")

    status, text = _post_json(base_url + "/api/judgment", {**sample, "calendarType": "lunar"})
    if status != 400 or "양력 입력만 지원" not in text:
        raise SystemExit(f"solar-only guard failed: status={status}")

    print("SMOKE_CHECK_OK")


if __name__ == "__main__":
    main()
