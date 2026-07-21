"""Isolated report calculation entrypoints for process workers."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from .report_service import build_report_payload


def build_report_bytes(payload: dict[str, Any]) -> bytes:
    result = build_report_payload(payload, defer_detail=False)
    return json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def worker_identity(delay_seconds: float = 0.0) -> int:
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    return os.getpid()
