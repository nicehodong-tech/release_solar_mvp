"""Month hidden-stem phase layer.

This layer keeps the existing branch-hidden-stem weights intact and adds a
separate 월률분야 calculation for the month branch. Its job is narrow:
identify which hidden stem is currently holding the month command by elapsed
days from the solar-term boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .constants import STEM_METADATA, TEN_GOD_GROUPS
from .models import MonthHiddenPhaseEntry, MonthHiddenPhaseProfile
from .ten_gods import ten_god_for


MONTH_HIDDEN_PHASE_VERSION = "month_hidden_phase_v1"

MONTH_HIDDEN_PHASE_TABLE: dict[str, list[tuple[str, str, int]]] = {
    "in": [("yeogi", "mu", 7), ("junggi", "byeong", 7), ("jeonggi", "gap", 16)],
    "myo": [("yeogi", "gap", 10), ("junggi", "eul", 10), ("jeonggi", "eul", 10)],
    "jin": [("yeogi", "eul", 9), ("junggi", "gye", 3), ("jeonggi", "mu", 18)],
    "sa": [("yeogi", "mu", 7), ("junggi", "gyeong", 7), ("jeonggi", "byeong", 16)],
    "o": [("yeogi", "byeong", 10), ("junggi", "gi", 9), ("jeonggi", "jeong", 11)],
    "mi": [("yeogi", "jeong", 9), ("junggi", "eul", 3), ("jeonggi", "gi", 18)],
    "sin": [("yeogi", "mu", 7), ("junggi", "im", 7), ("jeonggi", "gyeong", 16)],
    "yu": [("yeogi", "gyeong", 10), ("junggi", "sin", 10), ("jeonggi", "sin", 10)],
    "sul": [("yeogi", "sin", 9), ("junggi", "jeong", 3), ("jeonggi", "mu", 18)],
    "hae": [("yeogi", "mu", 7), ("junggi", "gap", 7), ("jeonggi", "im", 16)],
    "ja": [("yeogi", "im", 10), ("junggi", "gye", 10), ("jeonggi", "gye", 10)],
    "chuk": [("yeogi", "gye", 9), ("junggi", "sin", 3), ("jeonggi", "gi", 18)],
}


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _boundary_datetime(chart: Any) -> datetime | None:
    trace = getattr(chart, "calculation_trace", None)
    if not isinstance(trace, dict):
        return None
    boundary = trace.get("month_boundary")
    if not isinstance(boundary, dict):
        return None
    return _parse_datetime(boundary.get("time_utc"))


def _birth_datetime(chart: Any) -> datetime | None:
    trace = getattr(chart, "calculation_trace", None)
    if isinstance(trace, dict):
        birth_utc = _parse_datetime(trace.get("birth_utc"))
        if birth_utc is not None:
            return birth_utc
        true_solar = _parse_datetime(trace.get("true_solar_datetime"))
        if true_solar is not None:
            return true_solar
    return None


def _elapsed_days_from_boundary(chart: Any) -> float | None:
    boundary_dt = _boundary_datetime(chart)
    birth_dt = _birth_datetime(chart)
    if boundary_dt is None or birth_dt is None:
        return None
    return (birth_dt - boundary_dt).total_seconds() / 86400.0


def _clamped_day_index(value: float | None, total_days: int) -> float:
    if value is None:
        return 0.0
    if value < 0:
        return 0.0
    upper = max(0.0, float(total_days) - 0.001)
    if value > upper:
        return upper
    return value


def build_month_hidden_phase_profile(chart: Any) -> MonthHiddenPhaseProfile:
    """Build the 월률분야 profile for the chart's month branch."""

    month_branch = str(getattr(getattr(chart, "month_pillar", None), "branch_key", "") or "")
    day_stem = str(getattr(getattr(chart, "day_pillar", None), "stem_key", "") or "")
    rows = MONTH_HIDDEN_PHASE_TABLE.get(month_branch, [])
    total_days = sum(days for _phase, _stem, days in rows) or 30
    elapsed_days = _elapsed_days_from_boundary(chart)
    day_index = _clamped_day_index(elapsed_days, total_days)

    entries: list[MonthHiddenPhaseEntry] = []
    active_entry: MonthHiddenPhaseEntry | None = None
    cursor = 0
    seen_phase_stems: set[str] = set()
    basis_codes = [f"month_hidden_phase_branch_{month_branch}"] if month_branch else ["month_hidden_phase_branch_missing"]
    if elapsed_days is None:
        basis_codes.append("month_hidden_phase_boundary_missing")

    for phase, stem, days in rows:
        start_day = cursor
        end_day = cursor + int(days)
        is_active = start_day <= day_index < end_day
        ten_god = ten_god_for(day_stem, stem) if day_stem and stem in STEM_METADATA else ""
        entry = MonthHiddenPhaseEntry(
            phase=phase,
            stem=stem,
            element=STEM_METADATA.get(stem, {}).get("element", ""),
            ten_god=ten_god,
            ten_god_group=TEN_GOD_GROUPS.get(ten_god, ""),
            days=int(days),
            start_day=start_day,
            end_day=end_day,
            active=is_active,
            repeated_stem=stem in seen_phase_stems,
        )
        seen_phase_stems.add(stem)
        entries.append(entry)
        if is_active:
            active_entry = entry
        cursor = end_day

    if active_entry is None and entries:
        active_entry = entries[-1]

    active_phase = active_entry.phase if active_entry else ""
    active_stem = active_entry.stem if active_entry else ""
    active_element = active_entry.element if active_entry else ""
    active_ten_god = active_entry.ten_god if active_entry else ""
    active_ten_god_group = active_entry.ten_god_group if active_entry else ""
    if active_phase:
        basis_codes.append(f"month_hidden_phase_active_{active_phase}_{active_stem}")
    if active_element:
        basis_codes.append(f"month_hidden_phase_active_element_{active_element}")
    if active_ten_god:
        basis_codes.append(f"month_hidden_phase_active_ten_god_{active_ten_god}")

    return MonthHiddenPhaseProfile(
        month_branch=month_branch,
        day_index_from_boundary=round(day_index, 3),
        active_phase=active_phase,
        active_stem=active_stem,
        active_element=active_element,
        active_ten_god=active_ten_god,
        active_ten_god_group=active_ten_god_group,
        entries=entries,
        basis_codes=basis_codes,
        rule_version=MONTH_HIDDEN_PHASE_VERSION,
    )
