"""Small local web server for the saju fortune result product."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Semaphore
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .report_service import build_report_payload


WEB_ROOT = Path(__file__).resolve().parent / "static"
LOGGER = logging.getLogger("saju_web")
CANONICAL_HOST = "aisajuleehyeon.com"
WWW_HOST = "www.aisajuleehyeon.com"
API_CACHE_MAX_ENTRIES = 96
API_CACHE_MAX_BYTES = 48 * 1024 * 1024
API_CACHE_COMPRESSION_LEVEL = 1
API_CACHE_VERSION = "judgment-v20-trait-layer"
_API_CACHE: "OrderedDict[str, bytes]" = OrderedDict()
_API_CACHE_LOCK = Lock()
_API_CACHE_BYTES = 0
API_DETAIL_KEY_MAX_ENTRIES = 96
_API_DETAIL_KEYS: "OrderedDict[str, str]" = OrderedDict()
_API_DETAIL_KEYS_LOCK = Lock()
API_JOB_MAX_ENTRIES = 64
API_JOB_STALE_SECONDS = 180
_API_JOBS: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_API_JOBS_LOCK = Lock()
_API_JOB_SEMAPHORE = Semaphore(1)
_API_JOB_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="saju-analysis")
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _payload_cache_key(payload: dict[str, Any]) -> str:
    """Build a stable key for repeated report requests."""
    normalized = {
        "version": API_CACHE_VERSION,
        "birthDate": str(payload.get("birthDate") or payload.get("birth_date") or ""),
        "birthTime": str(payload.get("birthTime") or payload.get("birth_time") or ""),
        "calendar": str(payload.get("calendar") or payload.get("calendarType") or ""),
        "gender": str(payload.get("gender") or ""),
        "relationshipStatus": str(payload.get("relationshipStatus") or ""),
        "targetYear": str(payload.get("targetYear") or ""),
        "tier": str(payload.get("tier") or ""),
    }
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_for_build(payload: dict[str, Any]) -> dict[str, Any]:
    build_payload = dict(payload)
    build_payload.pop("async", None)
    return build_payload


def _job_id_from_cache_key(cache_key: str) -> str:
    return hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:32]


def _detail_token_from_cache_key(cache_key: str) -> str:
    return _job_id_from_cache_key(cache_key)


def _detail_key_set(token: str, cache_key: str) -> None:
    if not token or not cache_key:
        return
    with _API_DETAIL_KEYS_LOCK:
        _API_DETAIL_KEYS[token] = cache_key
        _API_DETAIL_KEYS.move_to_end(token)
        while len(_API_DETAIL_KEYS) > API_DETAIL_KEY_MAX_ENTRIES:
            _API_DETAIL_KEYS.popitem(last=False)


def _detail_key_get(token: str) -> str | None:
    if not token:
        return None
    with _API_DETAIL_KEYS_LOCK:
        cache_key = _API_DETAIL_KEYS.get(token)
        if cache_key is None:
            return None
        _API_DETAIL_KEYS.move_to_end(token)
        return cache_key


def _cache_get(key: str) -> bytes | None:
    with _API_CACHE_LOCK:
        compressed = _API_CACHE.get(key)
        if compressed is None:
            return None
        _API_CACHE.move_to_end(key)
    try:
        return gzip.decompress(compressed)
    except (OSError, EOFError):
        global _API_CACHE_BYTES
        with _API_CACHE_LOCK:
            removed = _API_CACHE.pop(key, None)
            if removed is not None:
                _API_CACHE_BYTES = max(0, _API_CACHE_BYTES - len(removed))
        key_digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        LOGGER.warning("discarded corrupt judgment cache entry key=%s", key_digest)
        return None


def _cache_contains(key: str) -> bool:
    with _API_CACHE_LOCK:
        return key in _API_CACHE


def _cache_set(key: str, data: bytes) -> None:
    global _API_CACHE_BYTES
    compressed = gzip.compress(data, compresslevel=API_CACHE_COMPRESSION_LEVEL)
    with _API_CACHE_LOCK:
        previous = _API_CACHE.pop(key, None)
        if previous is not None:
            _API_CACHE_BYTES -= len(previous)
        _API_CACHE[key] = compressed
        _API_CACHE_BYTES += len(compressed)
        _API_CACHE.move_to_end(key)
        while len(_API_CACHE) > API_CACHE_MAX_ENTRIES or _API_CACHE_BYTES > API_CACHE_MAX_BYTES:
            _, removed = _API_CACHE.popitem(last=False)
            _API_CACHE_BYTES = max(0, _API_CACHE_BYTES - len(removed))


def _strip_initial_section(section: dict[str, Any]) -> dict[str, Any]:
    next_section = _compact_section_for_transport(section)
    domain = str(next_section.get("domain") or "")
    if domain == "timing":
        next_section.pop("timing_map", None)
        next_section.pop("timing_decision_facets", None)
    if domain in {"year_2026", "year_2027"}:
        next_section.pop("metric_groups", None)
        next_section.pop("detail_blocks", None)
        next_section.pop("topic_items", None)
    return next_section


_INTERNAL_METRIC_FIELDS = {
    "score_components",
    "judgment_components",
    "gyeokguk_action_sources",
}


def _compact_metric_for_transport(metric: Any) -> Any:
    if not isinstance(metric, dict):
        return metric
    return {
        key: value
        for key, value in metric.items()
        if key not in _INTERNAL_METRIC_FIELDS
    }


def _compact_metric_list_for_transport(items: Any) -> list[Any]:
    return [
        _compact_metric_for_transport(item)
        for item in list(items or [])
    ]


def _compact_section_for_transport(section: dict[str, Any]) -> dict[str, Any]:
    """Remove calculation-only metric diagnostics from the browser payload."""
    next_section = dict(section)
    domain = str(next_section.get("domain") or "")
    for field in ("representative_metrics", "feature_axes"):
        if isinstance(next_section.get(field), list):
            next_section[field] = _compact_metric_list_for_transport(next_section[field])

    # The browser renders annual details from metric_groups. feature_axes is an
    # exact second copy of those items and adds no visible information.
    if domain in {"year_2026", "year_2027"}:
        next_section.pop("feature_axes", None)
        compact_groups: list[Any] = []
        for group in list(next_section.get("metric_groups") or []):
            if not isinstance(group, dict):
                compact_groups.append(group)
                continue
            next_group = dict(group)
            next_group["items"] = _compact_metric_list_for_transport(next_group.get("items"))
            compact_groups.append(next_group)
        next_section["metric_groups"] = compact_groups

    # judgment_axes is the internal scoring mirror of the public feature axes.
    # No current screen reads it; retaining it triples the same metric payload.
    next_section.pop("judgment_axes", None)
    return next_section


def _initial_payload_from_full(full_payload: dict[str, Any], detail_token: str) -> dict[str, Any]:
    """Return the fast first-screen payload while preserving the full cache entry."""
    initial = dict(full_payload)
    report = dict(initial.get("report") or {})
    sections = report.get("analysis_sections")
    if isinstance(sections, list):
        report["analysis_sections"] = [
            _strip_initial_section(section)
            for section in sections
            if isinstance(section, dict) and str(section.get("domain") or "") not in {"timing", "year_2026", "year_2027"}
        ]
    screen_contract = report.get("analysis_screen_contract")
    if isinstance(screen_contract, dict):
        report["analysis_screen_contract"] = {
            key: screen_contract.get(key)
            for key in ("summary", "detail_menu", "loading")
            if key in screen_contract
        }
    report["analysis_detail_units"] = {}
    report["analysis_engine_contract"] = {}
    report["factor_sections"] = []
    report["detail_deferred"] = True
    report["detail_token"] = detail_token
    initial["report"] = report
    initial["detailToken"] = detail_token
    initial["detailDeferred"] = True
    return initial


def _initial_payload_bytes_from_full_bytes(full_data: bytes, detail_token: str) -> bytes:
    try:
        full_payload = json.loads(full_data.decode("utf-8") or "{}")
    except Exception:
        return full_data
    if not isinstance(full_payload, dict):
        return full_data
    return _json_bytes(_initial_payload_from_full(full_payload, detail_token))


def _detail_payload_from_full(full_payload: dict[str, Any], detail_token: str) -> dict[str, Any]:
    report = dict((full_payload or {}).get("report") or {})
    detail_report = {
        "analysis_sections": [
            _compact_section_for_transport(section)
            for section in list(report.get("analysis_sections") or [])
            if isinstance(section, dict)
        ],
        "analysis_detail_units": report.get("analysis_detail_units") or {},
        "analysis_engine_contract": report.get("analysis_engine_contract") or {},
        "analysis_screen_contract": report.get("analysis_screen_contract") or {},
        "factor_sections": report.get("factor_sections") or [],
        "analysis_profile_summary": report.get("analysis_profile_summary") or {},
        "analysis_profile_panels": report.get("analysis_profile_panels") or [],
        "analysis_profile_cards": report.get("analysis_profile_cards") or [],
        "detail_deferred": False,
        "detail_token": detail_token,
    }
    return {
        "ok": True,
        "detailToken": detail_token,
        "detailDeferred": False,
        "chart": (full_payload or {}).get("chart") or {},
        "report": detail_report,
    }


def _detail_payload_bytes_from_full_bytes(full_data: bytes, detail_token: str) -> bytes:
    full_payload = json.loads(full_data.decode("utf-8") or "{}")
    if not isinstance(full_payload, dict):
        raise ValueError("상세 결과 형식이 올바르지 않습니다.")
    return _json_bytes(_detail_payload_from_full(full_payload, detail_token))


def _job_snapshot(job_id: str) -> dict[str, Any] | None:
    with _API_JOBS_LOCK:
        job = _API_JOBS.get(job_id)
        if job is None:
            return None
        _API_JOBS.move_to_end(job_id)
        return dict(job)


def _job_update_if_current(job_id: str, run_id: str, **updates: Any) -> bool:
    with _API_JOBS_LOCK:
        job = _API_JOBS.get(job_id)
        if job is None or str(job.get("runId") or "") != run_id:
            return False
        job.update(updates)
        job["updatedAt"] = time.time()
        _API_JOBS.move_to_end(job_id)
        return True


def _reserve_judgment_job(job_id: str, cache_key: str) -> tuple[dict[str, Any], bool]:
    now = time.time()
    cache_available = _cache_contains(cache_key)
    with _API_JOBS_LOCK:
        existing = _API_JOBS.get(job_id)
        if existing is not None:
            status = str(existing.get("status") or "")
            updated_at = float(existing.get("updatedAt") or existing.get("createdAt") or 0)
            is_fresh = (now - updated_at) < API_JOB_STALE_SECONDS
            if (status in {"queued", "running", "initial"} and is_fresh) or (
                status == "done" and cache_available
            ):
                _API_JOBS.move_to_end(job_id)
                return dict(existing), False

        run_id = f"{time.time_ns():x}"
        job = {
            "status": "queued",
            "message": "분석 요청을 접수했습니다.",
            "createdAt": now,
            "updatedAt": now,
            "runId": run_id,
        }
        _API_JOBS[job_id] = job
        _API_JOBS.move_to_end(job_id)
        while len(_API_JOBS) > API_JOB_MAX_ENTRIES:
            removable_id = next(
                (
                    candidate_id
                    for candidate_id, candidate in _API_JOBS.items()
                    if candidate_id != job_id and str(candidate.get("status") or "") in {"done", "error"}
                ),
                next(candidate_id for candidate_id in _API_JOBS if candidate_id != job_id),
            )
            _API_JOBS.pop(removable_id, None)
        return dict(job), True


def _run_judgment_job(job_id: str, cache_key: str, payload: dict[str, Any], run_id: str) -> None:
    try:
        with _API_JOB_SEMAPHORE:
            if not _job_update_if_current(
                job_id,
                run_id,
                status="running",
                message="명식을 계산하고 운의 강약을 정리하고 있습니다.",
                startedAt=time.time(),
            ):
                return
            cached = _cache_get(cache_key)
            if cached is not None:
                _job_update_if_current(
                    job_id,
                    run_id,
                    status="done",
                    cacheStatus="HIT",
                    finishedAt=time.time(),
                )
                return
            full_result = build_report_payload(_payload_for_build(payload), defer_detail=False)
            full_data = _json_bytes(full_result)
            _cache_set(cache_key, full_data)
            _job_update_if_current(
                job_id,
                run_id,
                status="done",
                cacheStatus="MISS",
                finishedAt=time.time(),
            )
    except ValueError as exc:
        _job_update_if_current(job_id, run_id, status="error", errorMessage=str(exc), finishedAt=time.time())
    except Exception:
        LOGGER.exception("judgment job failed job_id=%s", job_id)
        _job_update_if_current(
            job_id,
            run_id,
            status="error",
            errorMessage="사주 분석 생성 중 오류가 발생했습니다.",
            finishedAt=time.time(),
        )


def _ensure_judgment_job(job_id: str, cache_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    job, should_start = _reserve_judgment_job(job_id, cache_key)
    if should_start:
        _API_JOB_EXECUTOR.submit(
            _run_judgment_job,
            job_id,
            cache_key,
            _payload_for_build(payload),
            str(job.get("runId") or ""),
        )
    return _job_snapshot(job_id) or job


def _pending_response(job_id: str, job: dict[str, Any] | None) -> dict[str, Any]:
    status = str((job or {}).get("status") or "queued")
    message = str((job or {}).get("message") or "분석 결과를 준비하고 있습니다.")
    return {
        "ok": False,
        "pending": True,
        "jobId": job_id,
        "status": status,
        "message": message,
        "retryAfterMs": 900,
    }


class SajuWebHandler(BaseHTTPRequestHandler):
    server_version = "SajuWebMVP/0.1"

    def do_GET(self) -> None:
        if self._redirect_to_canonical_host():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/judgment-status":
            self._handle_judgment_status(parsed.query)
            return
        if parsed.path == "/api/judgment-detail":
            self._handle_judgment_detail(parsed.query)
            return
        if parsed.path.startswith("/api/"):
            self._send_json({"ok": False, "error": {"message": "지원하지 않는 요청입니다."}}, 404)
            return
        self._serve_static()

    def do_HEAD(self) -> None:
        if self._redirect_to_canonical_host():
            return
        self._serve_static(include_body=False)

    def do_POST(self) -> None:
        if self._redirect_to_canonical_host():
            return
        parsed = urlparse(self.path)
        if parsed.path != "/api/judgment":
            self._send_json({"ok": False, "error": {"message": "지원하지 않는 요청입니다."}}, 404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("요청 형식이 올바르지 않습니다.")
            cache_key = _payload_cache_key(payload)
            detail_token = _detail_token_from_cache_key(cache_key)
            _detail_key_set(detail_token, cache_key)
            cached = _cache_get(cache_key)
            if cached is not None:
                self._send_json_bytes(
                    _initial_payload_bytes_from_full_bytes(cached, detail_token),
                    200,
                    cache_status="HIT-SLIM",
                )
                return
            if payload.get("async"):
                job_id = detail_token
                job = _ensure_judgment_job(job_id, cache_key, payload)
                if job.get("status") == "done":
                    completed_data = _cache_get(cache_key)
                    if completed_data is None:
                        job = _ensure_judgment_job(job_id, cache_key, payload)
                    else:
                        self._send_json_bytes(
                            _initial_payload_bytes_from_full_bytes(completed_data, detail_token),
                            200,
                            cache_status=f"{str(job.get('cacheStatus') or 'JOB')}-SLIM",
                        )
                        return
                if job.get("status") == "initial":
                    initial_data = _cache_get(cache_key)
                    if initial_data is not None:
                        self._send_json_bytes(
                            _initial_payload_bytes_from_full_bytes(initial_data, detail_token),
                            200,
                            cache_status="INITIAL-SLIM",
                        )
                        return
                if job.get("status") == "error":
                    # A failure created after this request began is returned once.
                    # The next POST replaces the terminal job and retries cleanly.
                    self._send_json(
                        {
                            "ok": False,
                            "error": {
                                "message": job.get("errorMessage") or "분석 결과 생성에 실패했습니다."
                            },
                        },
                        500,
                    )
                    return
                self._send_json(_pending_response(job_id, job), 202)
                return
            result = build_report_payload(_payload_for_build(payload))
            data = _json_bytes(result)
            _cache_set(cache_key, data)
        except ValueError as exc:
            self._send_json({"ok": False, "error": {"message": str(exc)}}, 400)
            return
        except Exception:
            LOGGER.exception("synchronous judgment request failed")
            self._send_json(
                {"ok": False, "error": {"message": "사주 분석 생성 중 오류가 발생했습니다."}},
                500,
            )
            return
        self._send_json_bytes(
            _initial_payload_bytes_from_full_bytes(data, detail_token),
            200,
            cache_status="MISS-SLIM",
        )

    def _handle_judgment_status(self, query: str) -> None:
        params = parse_qs(query)
        job_id = (params.get("jobId") or [""])[0].strip()
        if not job_id:
            self._send_json({"ok": False, "error": {"message": "작업 번호가 없습니다."}}, 400)
            return
        job = _job_snapshot(job_id)
        if job is None:
            self._send_json({"ok": False, "error": {"message": "분석 작업을 찾을 수 없습니다."}}, 404)
            return
        if job.get("status") in {"initial", "done"}:
            cache_key = _detail_key_get(job_id)
            completed_data = _cache_get(cache_key) if cache_key else None
            if completed_data is not None:
                detail_token = _detail_token_from_cache_key(cache_key) if cache_key else job_id
                self._send_json_bytes(
                    _initial_payload_bytes_from_full_bytes(completed_data, detail_token),
                    200,
                    cache_status=f"{str(job.get('cacheStatus') or 'JOB')}-SLIM",
                )
                return
            self._send_json(
                {
                    "ok": False,
                    "retryable": True,
                    "error": {"message": "분석 서버가 갱신되었습니다. 결과를 다시 연결합니다."},
                },
                409,
            )
            return
        if job.get("status") == "error":
            self._send_json({"ok": False, "error": {"message": job.get("errorMessage") or "분석 결과 생성에 실패했습니다."}}, 500)
            return
        self._send_json(_pending_response(job_id, job), 202)

    def _handle_judgment_detail(self, query: str) -> None:
        params = parse_qs(query)
        token = (params.get("token") or params.get("detailToken") or [""])[0].strip()
        if not token:
            self._send_json({"ok": False, "error": {"message": "상세 결과 번호가 없습니다."}}, 400)
            return
        cache_key = _detail_key_get(token)
        full_data = _cache_get(cache_key) if cache_key else None
        if full_data is None:
            job = _job_snapshot(token)
            if job and job.get("status") in {"queued", "running", "initial"}:
                self._send_json(_pending_response(token, job), 202)
                return
        if full_data is None:
            self._send_json(
                {
                    "ok": False,
                    "retryable": True,
                    "error": {"message": "상세 결과 연결이 끊어졌습니다. 분석을 자동으로 복구합니다."},
                },
                409,
            )
            return
        try:
            detail_data = _detail_payload_bytes_from_full_bytes(full_data, token)
        except Exception:
            LOGGER.exception("judgment detail serialization failed token=%s", token)
            self._send_json({"ok": False, "error": {"message": "상세 결과를 정리하지 못했습니다."}}, 500)
            return
        self._send_json_bytes(detail_data, 200, cache_status="DETAIL")

    def _serve_static(self, *, include_body: bool = True) -> None:
        raw_path = self.path.split("?", 1)[0]
        relative = unquote(raw_path).lstrip("/") or "index.html"
        if relative.endswith("/"):
            relative += "index.html"
        target = (WEB_ROOT / relative).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())) or not target.is_file():
            self._send_json({"ok": False, "error": {"message": "파일을 찾을 수 없습니다."}}, 404)
            return
        content_type = MIME_TYPES.get(target.suffix.lower(), "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if include_body:
            self.wfile.write(data)

    def _redirect_to_canonical_host(self) -> bool:
        host = (self.headers.get("Host") or "").split(":", 1)[0].strip().lower()
        if host != WWW_HOST:
            return False
        scheme = (self.headers.get("X-Forwarded-Proto") or "https").split(",", 1)[0].strip() or "https"
        location = f"{scheme}://{CANONICAL_HOST}{self.path}"
        self.send_response(308)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()
        return True

    def _send_json(self, payload: dict[str, Any], status: int) -> None:
        data = _json_bytes(payload)
        self._send_json_bytes(data, status)

    def _send_json_bytes(self, data: bytes, status: int, cache_status: str | None = None) -> None:
        accepts_gzip = "gzip" in (self.headers.get("Accept-Encoding") or "").lower()
        response_data = gzip.compress(data, compresslevel=5) if accepts_gzip and len(data) > 1024 else data
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Vary", "Accept-Encoding")
        if response_data is not data:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(response_data)))
        if cache_status:
            self.send_header("X-Saju-Cache", cache_status)
        self.end_headers()
        self.wfile.write(response_data)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local saju web MVP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SajuWebHandler)
    print(f"Serving saju web MVP at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
