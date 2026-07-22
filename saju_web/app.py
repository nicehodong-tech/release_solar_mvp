"""Small local web server for the saju fortune result product."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import multiprocessing
import os
import secrets
import signal
import statistics
import time
from collections import OrderedDict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Semaphore, Thread
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .worker import build_report_bytes, worker_identity


WEB_ROOT = Path(__file__).resolve().parent / "static"
LOGGER = logging.getLogger("saju_web")
CANONICAL_HOST = "aisajuleehyeon.com"
WWW_HOST = "www.aisajuleehyeon.com"
SERVER_STARTED_AT = time.time()
# Spawned calculation workers must share one hash seed. Several legacy engine
# selectors use set membership internally, so a random process seed can change
# tie ordering even when the chart is identical.
os.environ.setdefault("PYTHONHASHSEED", "0")


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


API_ANALYSIS_WORKERS = _env_int("SAJU_ANALYSIS_WORKERS", 2, minimum=1, maximum=2)
API_CACHE_MAX_ENTRIES = 64
API_CACHE_MAX_BYTES = 48 * 1024 * 1024
API_CACHE_COMPRESSION_LEVEL = 1
API_CACHE_VERSION = "judgment-v23-daily-fortune"
_API_CACHE: "OrderedDict[str, bytes]" = OrderedDict()
_API_CACHE_LOCK = Lock()
_API_CACHE_BYTES = 0
API_DETAIL_KEY_MAX_ENTRIES = 256
_API_DETAIL_KEYS: "OrderedDict[str, str]" = OrderedDict()
_API_DETAIL_KEYS_LOCK = Lock()
API_JOB_MAX_ENTRIES = 192
API_JOB_MAX_PENDING = _env_int("SAJU_JOB_MAX_PENDING", 12, minimum=4, maximum=24)
API_JOB_STALE_SECONDS = _env_int("SAJU_JOB_STALE_SECONDS", 600, minimum=180, maximum=1800)
API_JOB_ESTIMATED_SECONDS = _env_int("SAJU_JOB_ESTIMATED_SECONDS", 15, minimum=5, maximum=60)
API_JOB_HARD_TIMEOUT_SECONDS = _env_int("SAJU_JOB_HARD_TIMEOUT_SECONDS", 120, minimum=60, maximum=600)
_API_JOBS: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_API_JOBS_LOCK = Lock()
_API_JOB_SEMAPHORE = Semaphore(API_ANALYSIS_WORKERS)
_API_JOB_EXECUTOR = ThreadPoolExecutor(
    max_workers=API_ANALYSIS_WORKERS,
    thread_name_prefix="saju-coordinator",
)
_API_BUILD_EXECUTOR_LOCK = Lock()
_API_BUILD_EXECUTOR: ProcessPoolExecutor | None = None
_API_BUILD_FALLBACK_LOCK = Lock()
_API_JOB_DURATION_SAMPLES: "deque[float]" = deque(maxlen=32)
_API_JOB_DURATION_LOCK = Lock()
MAX_REQUEST_BODY_BYTES = 64 * 1024
STATIC_GZIP_SUFFIXES = {".css", ".html", ".js", ".json", ".svg", ".txt", ".xml"}
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


def _new_build_executor() -> ProcessPoolExecutor:
    return ProcessPoolExecutor(
        max_workers=API_ANALYSIS_WORKERS,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=32,
    )


def _build_executor() -> ProcessPoolExecutor:
    global _API_BUILD_EXECUTOR
    with _API_BUILD_EXECUTOR_LOCK:
        if _API_BUILD_EXECUTOR is None:
            _API_BUILD_EXECUTOR = _new_build_executor()
        return _API_BUILD_EXECUTOR


def _replace_broken_build_executor(broken: ProcessPoolExecutor) -> None:
    global _API_BUILD_EXECUTOR
    with _API_BUILD_EXECUTOR_LOCK:
        if _API_BUILD_EXECUTOR is not broken:
            return
        broken.shutdown(wait=False, cancel_futures=True)
        _API_BUILD_EXECUTOR = _new_build_executor()


def _compute_report_bytes(payload: dict[str, Any]) -> bytes:
    for attempt in range(2):
        executor = _build_executor()
        try:
            return executor.submit(build_report_bytes, payload).result()
        except BrokenProcessPool:
            LOGGER.exception("analysis worker pool stopped unexpectedly attempt=%s", attempt + 1)
            _replace_broken_build_executor(executor)
    LOGGER.error("analysis worker pool recovery failed; using serialized in-process fallback")
    with _API_BUILD_FALLBACK_LOCK:
        return build_report_bytes(payload)


def _warm_analysis_workers() -> set[int]:
    executor = _build_executor()
    # Keep the probes overlapping so every configured process is started.
    futures = [
        executor.submit(worker_identity, 0.15)
        for _ in range(API_ANALYSIS_WORKERS * 2)
    ]
    return {int(future.result(timeout=45)) for future in futures}


def _shutdown_executors() -> None:
    global _API_BUILD_EXECUTOR
    _API_JOB_EXECUTOR.shutdown(wait=False, cancel_futures=True)
    with _API_BUILD_EXECUTOR_LOCK:
        executor = _API_BUILD_EXECUTOR
        _API_BUILD_EXECUTOR = None
    if executor is not None:
        executor.shutdown(wait=False, cancel_futures=True)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _payload_cache_key(payload: dict[str, Any]) -> str:
    """Build a stable key for repeated report requests."""
    normalized = {
        "version": API_CACHE_VERSION,
        "dailyDate": datetime.now(timezone(timedelta(hours=9))).date().isoformat(),
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


def _job_cache_key(job_id: str, job: dict[str, Any] | None = None) -> str:
    return str(_detail_key_get(job_id) or (job or {}).get("cacheKey") or "")


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


def _record_job_duration(seconds: float) -> None:
    if seconds <= 0:
        return
    with _API_JOB_DURATION_LOCK:
        _API_JOB_DURATION_SAMPLES.append(float(seconds))


def _estimated_job_duration() -> float:
    with _API_JOB_DURATION_LOCK:
        samples = tuple(_API_JOB_DURATION_SAMPLES)
    if not samples:
        return float(API_JOB_ESTIMATED_SECONDS)
    return max(5.0, min(90.0, float(statistics.median(samples))))


def _active_jobs_locked(now: float) -> list[tuple[str, dict[str, Any]]]:
    active = [
        (candidate_id, candidate)
        for candidate_id, candidate in _API_JOBS.items()
        if str(candidate.get("status") or "") in {"queued", "running", "initial"}
        and (now - float(candidate.get("updatedAt") or candidate.get("createdAt") or 0))
        < API_JOB_STALE_SECONDS
    ]
    return sorted(active, key=lambda item: float(item[1].get("createdAt") or 0))


def _job_runtime_fields_locked(job_id: str, job: dict[str, Any], now: float) -> dict[str, Any]:
    active = _active_jobs_locked(now)
    status = str(job.get("status") or "")
    jobs_ahead = 0
    if status == "queued":
        for candidate_id, _candidate in active:
            if candidate_id == job_id:
                break
            jobs_ahead += 1
    batches_ahead = (jobs_ahead + API_ANALYSIS_WORKERS - 1) // API_ANALYSIS_WORKERS
    return {
        "activeJobs": len(active),
        "jobsAhead": jobs_ahead,
        "queuePosition": jobs_ahead + 1 if status == "queued" else 0,
        "workerCount": API_ANALYSIS_WORKERS,
        "estimatedWaitSeconds": int(round(batches_ahead * _estimated_job_duration())),
    }


def _operational_snapshot() -> dict[str, Any]:
    now = time.time()
    with _API_JOBS_LOCK:
        active = _active_jobs_locked(now)
        running = sum(1 for _, job in active if str(job.get("status") or "") == "running")
        queued = sum(1 for _, job in active if str(job.get("status") or "") == "queued")
        running_ages = [
            max(0.0, now - float(job.get("startedAt") or job.get("updatedAt") or now))
            for _, job in active
            if str(job.get("status") or "") == "running"
        ]
        oldest_running_seconds = max(running_ages, default=0.0)
    with _API_CACHE_LOCK:
        cache_entries = len(_API_CACHE)
        cache_bytes = _API_CACHE_BYTES
    healthy = oldest_running_seconds < API_JOB_HARD_TIMEOUT_SECONDS
    return {
        "ok": healthy,
        "status": "healthy" if healthy else "degraded",
        "version": API_CACHE_VERSION,
        "runtime": {
            "service": os.environ.get("K_SERVICE") or "local",
            "revision": (
                os.environ.get("K_REVISION")
                or os.environ.get("SAJU_RELEASE_REVISION")
                or "local"
            ),
            "configuration": os.environ.get("K_CONFIGURATION") or "local",
        },
        "uptimeSeconds": int(max(0, now - SERVER_STARTED_AT)),
        "analysisWorkers": API_ANALYSIS_WORKERS,
        "jobs": {
            "running": running,
            "queued": queued,
            "capacity": API_JOB_MAX_PENDING,
            "oldestRunningSeconds": int(round(oldest_running_seconds)),
            "hardTimeoutSeconds": API_JOB_HARD_TIMEOUT_SECONDS,
        },
        "cache": {"entries": cache_entries, "compressedBytes": cache_bytes},
    }


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
        snapshot = dict(job)
        snapshot.update(_job_runtime_fields_locked(job_id, job, time.time()))
        return snapshot


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
                snapshot = dict(existing)
                snapshot.update(_job_runtime_fields_locked(job_id, existing, now))
                return snapshot, False

        active_jobs = _active_jobs_locked(now)
        if len(active_jobs) >= API_JOB_MAX_PENDING:
            estimated_wait = (
                (len(active_jobs) + API_ANALYSIS_WORKERS - 1) // API_ANALYSIS_WORKERS
            ) * _estimated_job_duration()
            return {
                "status": "busy",
                "message": "현재 분석 요청이 많습니다. 접수 순서를 확보하는 중입니다.",
                "retryAfterMs": 5000,
                "activeJobs": len(active_jobs),
                "workerCount": API_ANALYSIS_WORKERS,
                "estimatedWaitSeconds": int(round(estimated_wait)),
            }, False

        run_id = secrets.token_hex(12)
        job = {
            "status": "queued",
            "message": "분석 요청을 접수했습니다.",
            "cacheKey": cache_key,
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
        snapshot = dict(job)
        snapshot.update(_job_runtime_fields_locked(job_id, job, now))
        return snapshot, True


def _run_judgment_job(job_id: str, cache_key: str, payload: dict[str, Any], run_id: str) -> None:
    started = time.perf_counter()
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
            LOGGER.info("analysis_started job=%s", job_id[:12])
            cached = _cache_get(cache_key)
            if cached is not None:
                duration = time.perf_counter() - started
                _job_update_if_current(
                    job_id,
                    run_id,
                    status="done",
                    cacheStatus="HIT",
                    durationMs=int(round(duration * 1000)),
                    finishedAt=time.time(),
                )
                LOGGER.info("analysis_cache_hit job=%s duration_ms=%s", job_id[:12], int(round(duration * 1000)))
                return
            full_data = _compute_report_bytes(_payload_for_build(payload))
            _cache_set(cache_key, full_data)
            duration = time.perf_counter() - started
            _record_job_duration(duration)
            _job_update_if_current(
                job_id,
                run_id,
                status="done",
                cacheStatus="MISS",
                durationMs=int(round(duration * 1000)),
                finishedAt=time.time(),
            )
            LOGGER.info(
                "analysis_completed job=%s duration_ms=%s bytes=%s",
                job_id[:12],
                int(round(duration * 1000)),
                len(full_data),
            )
    except ValueError as exc:
        duration = time.perf_counter() - started
        _job_update_if_current(
            job_id,
            run_id,
            status="error",
            errorMessage=str(exc),
            durationMs=int(round(duration * 1000)),
            finishedAt=time.time(),
        )
        LOGGER.warning("analysis_rejected job=%s duration_ms=%s", job_id[:12], int(round(duration * 1000)))
    except Exception:
        duration = time.perf_counter() - started
        LOGGER.exception("judgment job failed job_id=%s", job_id)
        _job_update_if_current(
            job_id,
            run_id,
            status="error",
            errorMessage="사주 분석 생성 중 오류가 발생했습니다.",
            durationMs=int(round(duration * 1000)),
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
    jobs_ahead = int((job or {}).get("jobsAhead") or 0)
    estimated_wait = int((job or {}).get("estimatedWaitSeconds") or 0)
    if status == "queued" and jobs_ahead > 0:
        message = f"앞선 분석 {jobs_ahead}건을 순서대로 처리하고 있습니다."
    elif status == "queued":
        message = "분석을 시작할 준비를 마쳤습니다."
    elif status == "running":
        message = "명식을 계산하고 운의 강약을 정리하고 있습니다."
    return {
        "ok": False,
        "pending": True,
        "jobId": job_id,
        "status": status,
        "message": message,
        "retryAfterMs": 1100 if status == "running" else 1400,
        "jobsAhead": jobs_ahead,
        "queuePosition": int((job or {}).get("queuePosition") or 0),
        "activeJobs": int((job or {}).get("activeJobs") or 0),
        "workerCount": int((job or {}).get("workerCount") or API_ANALYSIS_WORKERS),
        "estimatedWaitSeconds": estimated_wait,
    }


@lru_cache(maxsize=64)
def _static_payload(path_text: str, modified_ns: int, size: int) -> tuple[bytes, bytes | None, str]:
    path = Path(path_text)
    data = path.read_bytes()
    compressed = gzip.compress(data, compresslevel=5) if path.suffix.lower() in STATIC_GZIP_SUFFIXES and len(data) > 1024 else None
    etag_seed = f"{path.name}:{modified_ns}:{size}".encode("utf-8")
    etag = '"' + hashlib.sha256(etag_seed).hexdigest()[:20] + '"'
    return data, compressed, etag


class SajuHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 128


class SajuWebHandler(BaseHTTPRequestHandler):
    server_version = "SajuWebMVP/0.1"

    def do_GET(self) -> None:
        if self._redirect_to_canonical_host():
            return
        parsed = urlparse(self.path)
        if parsed.path in {"/health", "/healthz"}:
            snapshot = _operational_snapshot()
            self._send_json(snapshot, 200 if snapshot.get("ok") else 503)
            return
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
        if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
            self._send_json(
                {"ok": False, "error": {"message": "요청 데이터의 크기가 허용 범위를 벗어났습니다."}},
                413,
            )
            return
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
                if job.get("status") == "busy":
                    self._send_json(
                        {
                            "ok": False,
                            "busy": True,
                            "retryable": True,
                            "message": job.get("message"),
                            "retryAfterMs": job.get("retryAfterMs") or 2500,
                            "error": {"message": job.get("message")},
                        },
                        429,
                        headers={"Retry-After": "5"},
                    )
                    return
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
            data = _compute_report_bytes(_payload_for_build(payload))
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
            cache_key = _job_cache_key(job_id, job)
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
        job = _job_snapshot(token)
        cache_key = _job_cache_key(token, job)
        full_data = _cache_get(cache_key) if cache_key else None
        if full_data is None:
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
        try:
            target.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self._send_json({"ok": False, "error": {"message": "파일을 찾을 수 없습니다."}}, 404)
            return
        if not target.is_file():
            self._send_json({"ok": False, "error": {"message": "파일을 찾을 수 없습니다."}}, 404)
            return
        content_type = MIME_TYPES.get(target.suffix.lower(), "application/octet-stream")
        stat = target.stat()
        data, compressed, etag = _static_payload(str(target), stat.st_mtime_ns, stat.st_size)
        cache_control = (
            "no-cache"
            if target.suffix.lower() == ".html"
            else "public, max-age=604800, stale-while-revalidate=86400"
        )
        if (self.headers.get("If-None-Match") or "").strip() == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache_control)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        accepts_gzip = "gzip" in (self.headers.get("Accept-Encoding") or "").lower()
        response_data = compressed if accepts_gzip and compressed is not None else data
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache_control)
        self.send_header("ETag", etag)
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("X-Content-Type-Options", "nosniff")
        if response_data is compressed:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(response_data)))
        self.end_headers()
        if include_body:
            self.wfile.write(response_data)

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

    def _send_json(
        self,
        payload: dict[str, Any],
        status: int,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        data = _json_bytes(payload)
        self._send_json_bytes(data, status, headers=headers)

    def _send_json_bytes(
        self,
        data: bytes,
        status: int,
        cache_status: str | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        accepts_gzip = "gzip" in (self.headers.get("Accept-Encoding") or "").lower()
        response_data = gzip.compress(data, compresslevel=5) if accepts_gzip and len(data) > 1024 else data
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("X-Content-Type-Options", "nosniff")
        if response_data is not data:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(response_data)))
        if cache_status:
            self.send_header("X-Saju-Cache", cache_status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response_data)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local saju web MVP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8765")), type=int)
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, os.environ.get("SAJU_LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        worker_pids = _warm_analysis_workers()
        LOGGER.info(
            "analysis_workers_ready workers=%s processes=%s max_pending=%s",
            API_ANALYSIS_WORKERS,
            len(worker_pids),
            API_JOB_MAX_PENDING,
        )
    except Exception:
        LOGGER.exception("analysis worker warmup failed; requests will use the recovery path")

    server = SajuHTTPServer((args.host, args.port), SajuWebHandler)

    def request_shutdown(signum: int, _frame: object) -> None:
        LOGGER.info("shutdown_requested signal=%s", signum)
        Thread(target=server.shutdown, name="saju-shutdown", daemon=True).start()

    for signal_name in ("SIGTERM", "SIGINT"):
        shutdown_signal = getattr(signal, signal_name, None)
        if shutdown_signal is not None:
            signal.signal(shutdown_signal, request_shutdown)

    LOGGER.info(
        "server_ready url=http://%s:%s workers=%s cache_mb=%s",
        args.host,
        args.port,
        API_ANALYSIS_WORKERS,
        API_CACHE_MAX_BYTES // (1024 * 1024),
    )
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        _shutdown_executors()
        LOGGER.info("server_stopped")


if __name__ == "__main__":
    main()
