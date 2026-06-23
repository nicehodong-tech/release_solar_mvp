"""Small local web server for the saju fortune result product."""

from __future__ import annotations

import argparse
import json
import os
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import unquote

from .report_service import build_report_payload


WEB_ROOT = Path(__file__).resolve().parent / "static"
API_CACHE_MAX_ENTRIES = 96
API_CACHE_VERSION = "judgment-v2"
_API_CACHE: "OrderedDict[str, bytes]" = OrderedDict()
_API_CACHE_LOCK = Lock()
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


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


class SajuWebHandler(BaseHTTPRequestHandler):
    server_version = "SajuWebMVP/0.1"

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._send_json({"ok": False, "error": {"message": "지원하지 않는 요청입니다."}}, 404)
            return
        self._serve_static()

    def do_POST(self) -> None:
        if self.path != "/api/judgment":
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
            result = build_report_payload(payload)
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

    def _serve_static(self) -> None:
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
        self.wfile.write(data)

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
