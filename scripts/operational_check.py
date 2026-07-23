from __future__ import annotations

import argparse
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


SAMPLES = (
    {"birthDate": "19991212", "birthTime": "myo", "gender": "male"},
    {"birthDate": "19960403", "birthTime": "sin", "gender": "female"},
    {"birthDate": "19880517", "birthTime": "unknown", "gender": "female"},
    {"birthDate": "19730221", "birthTime": "ja", "gender": "male"},
)


def _request(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 30,
    accept_gzip: bool = False,
) -> tuple[int, dict[str, str], bytes]:
    data = None
    headers = {"Accept": "application/json"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
        method = "POST"
    if accept_gzip:
        headers["Accept-Encoding"] = "gzip"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read()
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        if response_headers.get("content-encoding") == "gzip":
            raw = gzip.decompress(raw)
        return int(response.status), response_headers, raw


def _json_request(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 30,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    status, headers, raw = _request(url, payload=payload, timeout=timeout, accept_gzip=True)
    parsed = json.loads(raw.decode("utf-8") or "{}")
    if not isinstance(parsed, dict):
        raise RuntimeError(f"JSON object expected: {url}")
    return status, headers, parsed


def _full_payload(sample: dict[str, str]) -> dict[str, Any]:
    return {
        **sample,
        "calendarType": "solar",
        "relationshipStatus": "unknown",
        "targetYear": "2026",
        "tier": "public_mvp",
        "async": True,
    }


def _analyze(base_url: str, sample: dict[str, str], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    status, headers, payload = _json_request(
        base_url + "/api/judgment",
        payload=_full_payload(sample),
        timeout=30,
    )
    job_id = str(payload.get("jobId") or "")
    deadline = time.monotonic() + timeout
    while status == 202 and payload.get("pending") and job_id:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"analysis timeout: {sample['birthDate']}")
        retry_ms = max(500, min(3000, int(payload.get("retryAfterMs") or 1000)))
        time.sleep(retry_ms / 1000)
        status, headers, payload = _json_request(
            base_url + "/api/judgment-status?" + urllib.parse.urlencode({"jobId": job_id}),
            timeout=30,
        )
    if status != 200 or not payload.get("ok"):
        raise RuntimeError(f"analysis failed: date={sample['birthDate']} status={status} payload={payload}")

    token = str(payload.get("detailToken") or "").strip()
    if not token:
        raise RuntimeError(f"detail token missing: {sample['birthDate']}")
    detail_status, _detail_headers, detail = _json_request(
        base_url + "/api/judgment-detail?" + urllib.parse.urlencode({"token": token}),
        timeout=60,
    )
    if detail_status != 200 or not detail.get("ok"):
        raise RuntimeError(f"detail failed: date={sample['birthDate']} status={detail_status}")
    report = detail.get("report") or {}
    sections = report.get("analysis_sections") or []
    factors = report.get("factor_sections") or []
    if len(sections) < 10 or not factors:
        raise RuntimeError(
            f"detail content incomplete: date={sample['birthDate']} sections={len(sections)} factors={len(factors)}"
        )
    pillars = ((detail.get("chart") or {}).get("fourPillars") or {})
    if sample["birthTime"] == "unknown" and "hour" in pillars:
        raise RuntimeError("unknown birth time unexpectedly contains an hour pillar")
    if sample["birthTime"] != "unknown" and "hour" not in pillars:
        raise RuntimeError("known birth time is missing the hour pillar")
    return {
        "date": sample["birthDate"],
        "seconds": round(time.perf_counter() - started, 2),
        "sections": len(sections),
        "factors": len(factors),
        "cache": headers.get("x-saju-cache", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the deployed web service operating contract.")
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8765")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--health-path", default="/healthz")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    health_url = base_url + "/" + args.health_path.lstrip("/")

    health_status, _headers, health = _json_request(health_url)
    if health_status != 200 or not health.get("ok"):
        raise SystemExit(f"health check failed: status={health_status} payload={health}")

    static_status, static_headers, static_data = _request(
        base_url + "/app-v2.js?v=operational-check",
        accept_gzip=True,
    )
    if static_status != 200 or len(static_data) < 1000 or "etag" not in static_headers:
        raise SystemExit("static asset check failed")

    samples = SAMPLES[: max(1, min(len(SAMPLES), args.concurrency))]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(samples)) as executor:
        futures = {executor.submit(_analyze, base_url, sample, args.timeout): sample for sample in samples}
        for future in as_completed(futures):
            results.append(future.result())

    final_status, _headers, final_health = _json_request(health_url)
    if final_status != 200 or not final_health.get("ok"):
        raise SystemExit("final health check failed")
    print(
        json.dumps(
            {
                "ok": True,
                "health": final_health,
                "analyses": sorted(results, key=lambda item: item["date"]),
                "staticGzip": static_headers.get("content-encoding") == "gzip",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
