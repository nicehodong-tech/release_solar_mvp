"""Lunar-to-solar conversion adapters."""

from __future__ import annotations

import subprocess
from datetime import date


class LunarConversionError(RuntimeError):
    pass


def korean_lunar_to_solar(year: int, month: int, day: int, is_leap_month: bool = False) -> date:
    """Convert a Korean lunar date to Gregorian date using Windows/.NET.

    The current project runs on Windows and does not have a pure-Python lunar
    library installed. This adapter keeps lunar conversion isolated so the core
    engine remains deterministic and testable.
    """

    leap_literal = "$true" if is_leap_month else "$false"
    script = f"""
$ErrorActionPreference = 'Stop'
$cal = [System.Globalization.KoreanLunisolarCalendar]::new()
$year = {int(year)}
$month = {int(month)}
$day = {int(day)}
$isLeap = {leap_literal}
$leapMonth = $cal.GetLeapMonth($year)
$calendarMonth = $month
if ($leapMonth -gt 0) {{
  if ($isLeap) {{
    if ($leapMonth -ne ($month + 1)) {{
      throw "Requested month is not the leap lunar month for this year."
    }}
    $calendarMonth = $leapMonth
  }} elseif ($month -ge $leapMonth) {{
    $calendarMonth = $month + 1
  }}
}} elseif ($isLeap) {{
  throw "This lunar year has no leap month."
}}
$dt = $cal.ToDateTime($year, $calendarMonth, $day, 0, 0, 0, 0)
$dt.ToString('yyyy-MM-dd')
"""
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - platform guard
        raise LunarConversionError(f"PowerShell lunar conversion failed: {exc}") from exc

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise LunarConversionError(message)

    text = completed.stdout.strip().splitlines()[-1].strip()
    try:
        y, m, d = [int(part) for part in text.split("-")]
        return date(y, m, d)
    except Exception as exc:
        raise LunarConversionError(f"Unexpected lunar conversion output: {text}") from exc
