"""Small local web server for the saju fortune result product."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Semaphore, Thread
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .report_service import build_report_payload


WEB_ROOT = Path(__file__).resolve().parent / "static"
CANONICAL_HOST = "aisajuleehyeon.com"
WWW_HOST = "www.aisajuleehyeon.com"
API_CACHE_MAX_ENTRIES = 96
API_CACHE_VERSION = "judgment-v3"
_API_CACHE: "OrderedDict[str, bytes]" = OrderedDict()
_API_CACHE_LOCK = Lock()
API_JOB_MAX_ENTRIES = 64
_API_JOBS: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_API_JOBS_LOCK = Lock()
_API_JOB_SEMAPHORE = Semaphore(1)
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


def _cache_get(key: str) -> bytes | None:
    with _API_CACHE_LOCK:
        data = _API_CACHE.get(key)
        if data is None:
            return None
        _API_CACHE.move_to_end(key)
        return data


def _cache_set(key: str, data: bytes) -> None:
    with _API_CACHE_LOCK:
        _API_CACHE[key] = data
        _API_CACHE.move_to_end(key)
        while len(_API_CACHE) > API_CACHE_MAX_ENTRIES:
            _API_CACHE.popitem(last=False)


def _job_snapshot(job_id: str) -> dict[str, Any] | None:
    with _API_JOBS_LOCK:
        job = _API_JOBS.get(job_id)
        if job is None:
            return None
        _API_JOBS.move_to_end(job_id)
        return dict(job)


def _job_update(job_id: str, **updates: Any) -> None:
    with _API_JOBS_LOCK:
        job = _API_JOBS.setdefault(job_id, {})
        job.update(updates)
        job["updatedAt"] = time.time()
        _API_JOBS.move_to_end(job_id)
        while len(_API_JOBS) > API_JOB_MAX_ENTRIES:
            _API_JOBS.popitem(last=False)


def _run_judgment_job(job_id: str, cache_key: str, payload: dict[str, Any]) -> None:
    _job_update(
        job_id,
        status="running",
        message="명식을 계산하고 운의 강약을 정리하고 있습니다.",
        startedAt=time.time(),
    )
    try:
        with _API_JOB_SEMAPHORE:
            cached = _cache_get(cache_key)
            if cached is not None:
                _job_update(job_id, status="done", data=cached, cacheStatus="HIT")
                return
            result = build_report_payload(_payload_for_build(payload))
            data = _json_bytes(result)
            _cache_set(cache_key, data)
            _job_update(job_id, status="done", data=data, cacheStatus="MISS")
    except ValueError as exc:
        _job_update(job_id, status="error", errorMessage=str(exc))
    except Exception:
        _job_update(job_id, status="error", errorMessage="사주 분석 생성 중 오류가 발생했습니다.")


def _ensure_judgment_job(job_id: str, cache_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = _job_snapshot(job_id)
    if existing is not None:
        return existing
    _job_update(
        job_id,
        status="queued",
        message="분석 요청을 접수했습니다.",
        createdAt=time.time(),
    )
    worker = Thread(target=_run_judgment_job, args=(job_id, cache_key, _payload_for_build(payload)), daemon=True)
    worker.start()
    return _job_snapshot(job_id) or {"status": "queued", "message": "분석 요청을 접수했습니다."}


def _pending_response(job_id: str, job: dict[str, Any] | None) -> dict[str, Any]:
    status = str((job or {}).get("status") or "queued")
    message = str((job or {}).get("message") or "분석 결과를 준비하고 있습니다.")
    return {
        "ok": False,
        "pending": True,
        "jobId": job_id,
        "status": status,
        "message": message,
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
            cached = _cache_get(cache_key)
            if cached is not None:
                self._send_json_bytes(cached, 200, cache_status="HIT")
                return
            if payload.get("async"):
                job_id = _job_id_from_cache_key(cache_key)
                job = _ensure_judgment_job(job_id, cache_key, payload)
                if job.get("status") == "done" and job.get("data"):
                    self._send_json_bytes(job["data"], 200, cache_status=str(job.get("cacheStatus") or "JOB"))
                    return
                if job.get("status") == "error":
                    self._send_json({"ok": False, "error": {"message": job.get("errorMessage") or "분석 결과 생성에 실패했습니다."}}, 500)
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
            self._send_json(
                {"ok": False, "error": {"message": "사주 분석 생성 중 오류가 발생했습니다."}},
                500,
            )
            return
        self._send_json_bytes(data, 200, cache_status="MISS")

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
        if job.get("status") == "done" and job.get("data"):
            self._send_json_bytes(job["data"], 200, cache_status=str(job.get("cacheStatus") or "JOB"))
            return
        if job.get("status") == "error":
            self._send_json({"ok": False, "error": {"message": job.get("errorMessage") or "분석 결과 생성에 실패했습니다."}}, 500)
            return
        self._send_json(_pending_response(job_id, job), 202)

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
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if cache_status:
            self.send_header("X-Saju-Cache", cache_status)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local saju web MVP.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8765")), type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SajuWebHandler)
    print(f"Serving saju web MVP at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
