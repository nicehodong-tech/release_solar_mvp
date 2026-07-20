"""Astronomical helpers for true solar time and solar terms."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache


def normalize_angle(degrees: float) -> float:
    return degrees % 360.0


def gregorian_to_jdn(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def julian_day(dt_utc: datetime) -> float:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_utc = dt_utc.astimezone(timezone.utc)

    year = dt_utc.year
    month = dt_utc.month
    day_fraction = (
        dt_utc.day
        + (dt_utc.hour / 24)
        + (dt_utc.minute / 1440)
        + (dt_utc.second / 86400)
        + (dt_utc.microsecond / 86400_000_000)
    )
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day_fraction
        + b
        - 1524.5
    )


def apparent_solar_longitude(dt_utc: datetime) -> float:
    jd = julian_day(dt_utc)
    t = (jd - 2451545.0) / 36525.0
    l0 = normalize_angle(280.46646 + 36000.76983 * t + 0.0003032 * t * t)
    m = normalize_angle(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    m_rad = math.radians(m)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )
    true_longitude = l0 + c
    omega = math.radians(125.04 - 1934.136 * t)
    return normalize_angle(true_longitude - 0.00569 - 0.00478 * math.sin(omega))


def equation_of_time_minutes(local_date: datetime) -> float:
    day_of_year = local_date.timetuple().tm_yday
    b = 2 * math.pi * (day_of_year - 81) / 364.0
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_datetime(
    local_standard_dt: datetime,
    longitude: float,
    timezone_offset_minutes: int,
) -> tuple[datetime, float, float]:
    standard_meridian = timezone_offset_minutes / 60.0 * 15.0
    longitude_correction = 4.0 * (longitude - standard_meridian)
    eot = equation_of_time_minutes(local_standard_dt)
    adjusted = local_standard_dt + timedelta(minutes=longitude_correction + eot)
    return adjusted, longitude_correction, eot


def _unwrap_to_previous(raw_longitude: float, previous_unwrapped: float) -> float:
    candidate = raw_longitude
    while candidate < previous_unwrapped - 180.0:
        candidate += 360.0
    while candidate > previous_unwrapped + 180.0:
        candidate -= 360.0
    return candidate


@lru_cache(maxsize=96)
def _solar_longitude_samples(year: int) -> tuple[tuple[datetime, float], ...]:
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 10, tzinfo=timezone.utc)
    step = timedelta(hours=6)
    samples: list[tuple[datetime, float]] = []
    current_time = start
    previous_unwrapped = apparent_solar_longitude(start)
    samples.append((start, previous_unwrapped))
    current_time += step
    while current_time <= end:
        current_raw = apparent_solar_longitude(current_time)
        current_unwrapped = _unwrap_to_previous(current_raw, previous_unwrapped)
        samples.append((current_time, current_unwrapped))
        previous_unwrapped = current_unwrapped
        current_time += step
    return tuple(samples)


@lru_cache(maxsize=4096)
def solar_longitude_crossing_utc(year: int, target_longitude: float) -> datetime:
    samples = _solar_longitude_samples(year)
    prev_time, prev_unwrapped = samples[0]
    target = target_longitude
    while target < prev_unwrapped:
        target += 360.0

    for current_time, current_unwrapped in samples[1:]:
        if prev_unwrapped <= target <= current_unwrapped:
            lo = prev_time
            hi = current_time
            lo_long = prev_unwrapped
            for _ in range(50):
                mid = lo + (hi - lo) / 2
                mid_long = _unwrap_to_previous(apparent_solar_longitude(mid), lo_long)
                if mid_long < target:
                    lo = mid
                    lo_long = mid_long
                else:
                    hi = mid
            return hi.replace(microsecond=0)
        prev_time = current_time
        prev_unwrapped = current_unwrapped

    raise RuntimeError(f"Solar longitude {target_longitude} crossing not found for {year}.")
