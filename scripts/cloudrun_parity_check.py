from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from operational_check import SAMPLES, _full_payload, _json_request


_PARITY_EXCLUDED_KEYS = frozenset({"detail_token", "daily_fortune"})


def _normalize_comparable(value: Any) -> Any:
    """Remove only ephemeral or intentionally additive release fields.

    The remaining chart and report payload must still match byte-for-byte after
    canonical JSON encoding, so existing engine judgments cannot drift during
    an additive product release.
    """

    if isinstance(value, dict):
        return {
            key: _normalize_comparable(item)
            for key, item in value.items()
            if key not in _PARITY_EXCLUDED_KEYS
        }
    if isinstance(value, list):
        return [_normalize_comparable(item) for item in value]
    return value


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _first_difference(left: Any, right: Any, path: str = "$") -> str | None:
    if type(left) is not type(right):
        return f"{path}: type {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        left_keys = set(left)
        right_keys = set(right)
        if left_keys != right_keys:
            missing = sorted(left_keys - right_keys)[:5]
            added = sorted(right_keys - left_keys)[:5]
            return f"{path}: missing={missing} added={added}"
        for key in sorted(left):
            difference = _first_difference(left[key], right[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            difference = _first_difference(left_item, right_item, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if left != right:
        left_text = repr(left)
        right_text = repr(right)
        return f"{path}: {left_text[:160]} != {right_text[:160]}"
    return None


def _fetch_result(base_url: str, sample: dict[str, str], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    status, _headers, payload = _json_request(
        base_url.rstrip("/") + "/api/judgment",
        payload=_full_payload(sample),
        timeout=30,
    )
    job_id = str(payload.get("jobId") or "")
    deadline = time.monotonic() + timeout
    while status == 202 and payload.get("pending") and job_id:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"analysis timeout: {base_url} {sample['birthDate']}")
        retry_ms = max(500, min(3000, int(payload.get("retryAfterMs") or 1000)))
        time.sleep(retry_ms / 1000)
        status, _headers, payload = _json_request(
            base_url.rstrip("/")
            + "/api/judgment-status?"
            + urllib.parse.urlencode({"jobId": job_id}),
            timeout=30,
        )
    if status != 200 or not payload.get("ok"):
        raise RuntimeError(
            f"analysis failed: url={base_url} date={sample['birthDate']} status={status}"
        )

    token = str(payload.get("detailToken") or "").strip()
    if not token:
        raise RuntimeError(f"detail token missing: {base_url} {sample['birthDate']}")
    detail_status, _headers, detail = _json_request(
        base_url.rstrip("/")
        + "/api/judgment-detail?"
        + urllib.parse.urlencode({"token": token}),
        timeout=90,
    )
    if detail_status != 200 or not detail.get("ok"):
        raise RuntimeError(
            f"detail failed: url={base_url} date={sample['birthDate']} status={detail_status}"
        )
    comparable = _normalize_comparable({
        "chart": detail.get("chart") or {},
        "report": detail.get("report") or {},
    })
    return {
        "seconds": round(time.perf_counter() - started, 2),
        "fingerprint": _fingerprint(comparable),
        "comparable": comparable,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare deterministic saju results between production and Cloud Run staging."
    )
    parser.add_argument("production_url")
    parser.add_argument("staging_url")
    parser.add_argument("--sample-count", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()

    sample_count = max(1, min(len(SAMPLES), args.sample_count))
    results: list[dict[str, Any]] = []
    for sample in SAMPLES[:sample_count]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            production_future = executor.submit(
                _fetch_result, args.production_url, sample, args.timeout
            )
            staging_future = executor.submit(
                _fetch_result, args.staging_url, sample, args.timeout
            )
            production = production_future.result()
            staging = staging_future.result()

        matched = production["fingerprint"] == staging["fingerprint"]
        difference = None
        if not matched:
            difference = _first_difference(
                production["comparable"], staging["comparable"]
            )
        results.append(
            {
                "birthDate": sample["birthDate"],
                "matched": matched,
                "productionSeconds": production["seconds"],
                "stagingSeconds": staging["seconds"],
                "productionHash": production["fingerprint"],
                "stagingHash": staging["fingerprint"],
                "firstDifference": difference,
            }
        )

    output = {"ok": all(item["matched"] for item in results), "samples": results}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not output["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
