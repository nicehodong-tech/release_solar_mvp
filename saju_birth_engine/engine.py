"""Public birth chart calculation engine."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from .astronomy import solar_longitude_crossing_utc, true_solar_datetime
from .constants import HIDDEN_STEMS, SAJU_MONTH_BOUNDARIES, TEN_GODS_BY_DAY_STEM
from .locations import resolve_location
from .lunar import korean_lunar_to_solar
from .models import BirthChartResult, BirthInput, DaeunEntry
from .pillars import day_pillar_for_date, hour_branch_index, hour_pillar, month_pillar, sexagenary_pillar, year_pillar_for_gregorian_year


def _normalize_birth_date(birth_input: BirthInput) -> tuple[date, list[str], dict[str, Any]]:
    warnings: list[str] = []
    trace: dict[str, Any] = {"calendar_type": birth_input.calendar_type}

    if birth_input.calendar_type == "solar":
        solar_date = date(birth_input.year, birth_input.month, birth_input.day)
        return solar_date, warnings, trace

    if birth_input.calendar_type == "lunar":
        solar_date = korean_lunar_to_solar(
            birth_input.year,
            birth_input.month,
            birth_input.day,
            birth_input.leap_lunar_month,
        )
        trace["lunar_input"] = {
            "year": birth_input.year,
            "month": birth_input.month,
            "day": birth_input.day,
            "is_leap_month": birth_input.leap_lunar_month,
        }
        trace["converted_solar_date"] = solar_date.isoformat()
        return solar_date, warnings, trace

    raise ValueError(f"Unsupported calendar_type: {birth_input.calendar_type}")


def _solar_month_boundaries(year: int) -> list[dict[str, Any]]:
    boundaries: list[dict[str, Any]] = []
    for y in [year - 1, year, year + 1]:
        for item in SAJU_MONTH_BOUNDARIES:
            boundaries.append(
                {
                    **item,
                    "year": y,
                    "time_utc": solar_longitude_crossing_utc(y, item["longitude"]),
                }
            )
    boundaries.sort(key=lambda item: item["time_utc"])
    return boundaries


def _effective_year_for_pillar(local_year: int, birth_utc: datetime) -> tuple[int, datetime]:
    lichun = solar_longitude_crossing_utc(local_year, 315.0)
    if birth_utc >= lichun:
        return local_year, lichun
    return local_year - 1, solar_longitude_crossing_utc(local_year - 1, 315.0)


def _effective_month_boundary(local_year: int, birth_utc: datetime) -> dict[str, Any]:
    candidates = [item for item in _solar_month_boundaries(local_year) if item["time_utc"] <= birth_utc]
    if not candidates:
        raise RuntimeError("No previous solar month boundary found.")
    return candidates[-1]


def _nearest_solar_boundary_minutes(local_year: int, birth_utc: datetime) -> tuple[str | None, float | None]:
    boundaries = _solar_month_boundaries(local_year)
    nearest = min(boundaries, key=lambda item: abs((birth_utc - item["time_utc"]).total_seconds()))
    distance = abs((birth_utc - nearest["time_utc"]).total_seconds()) / 60.0
    return nearest["name"], distance


def _nearest_hour_boundary_minutes(true_dt: datetime) -> float:
    boundary_hours = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    candidates: list[datetime] = []
    for day_delta in [-1, 0, 1]:
        base = (true_dt + timedelta(days=day_delta)).replace(minute=0, second=0, microsecond=0)
        for hour in boundary_hours:
            candidates.append(base.replace(hour=hour, minute=30))
    return min(abs((true_dt - item).total_seconds()) for item in candidates) / 60.0


def _boundary_status(
    local_year: int,
    birth_utc: datetime,
    true_dt: datetime,
    threshold_minutes: float = 15.0,
) -> tuple[bool, str | None, float | None, dict[str, Any]]:
    month_boundary_name, month_distance = _nearest_solar_boundary_minutes(local_year, birth_utc)
    midnight = true_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_distance = min(
        abs((true_dt - midnight).total_seconds()) / 60.0,
        abs((true_dt - (midnight + timedelta(days=1))).total_seconds()) / 60.0,
        abs((true_dt - (midnight - timedelta(days=1))).total_seconds()) / 60.0,
    )
    hour_distance = _nearest_hour_boundary_minutes(true_dt)

    distances = {
        "month": month_distance,
        "day": day_distance,
        "hour": hour_distance,
    }
    boundary_type = min(distances, key=lambda key: distances[key] if distances[key] is not None else 999999)
    boundary_distance = distances[boundary_type]
    trace = {
        "nearest_month_boundary_name": month_boundary_name,
        "nearest_month_boundary_minutes": month_distance,
        "nearest_day_boundary_minutes": day_distance,
        "nearest_hour_boundary_minutes": hour_distance,
    }

    if month_distance is not None and month_distance <= threshold_minutes:
        if month_boundary_name == "lichun":
            return True, "year_month", round(month_distance, 3), trace
        return True, "month", round(month_distance, 3), trace
    if day_distance <= threshold_minutes:
        return True, "day", round(day_distance, 3), trace
    if hour_distance <= threshold_minutes:
        return True, "hour", round(hour_distance, 3), trace

    return False, None, round(boundary_distance, 3) if boundary_distance is not None else None, trace


def _ten_gods(day_stem: str, pillars: dict[str, Any]) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]]]:
    mapping = TEN_GODS_BY_DAY_STEM[day_stem]
    by_stem = {name: mapping[pillar.stem] for name, pillar in pillars.items()}
    hidden = {name: HIDDEN_STEMS[pillar.branch] for name, pillar in pillars.items()}
    by_hidden = {name: [mapping[stem] for stem in stems] for name, stems in hidden.items()}
    return by_stem, by_hidden, hidden


def _daeun_direction(gender: str, year_stem_index: int) -> str:
    if gender not in {"male", "female"}:
        return "unknown"
    yang_year = year_stem_index % 2 == 0
    if gender == "male":
        return "forward" if yang_year else "backward"
    return "backward" if yang_year else "forward"


def _daeun_start(
    direction: str,
    local_year: int,
    birth_utc: datetime,
) -> tuple[float | None, str | None, datetime | None, dict[str, Any]]:
    if direction == "unknown":
        return None, None, None, {"daeun_reason": "gender_unknown"}

    boundaries = _solar_month_boundaries(local_year)
    if direction == "forward":
        target = next(item for item in boundaries if item["time_utc"] > birth_utc)
        delta = target["time_utc"] - birth_utc
    else:
        previous = [item for item in boundaries if item["time_utc"] <= birth_utc]
        target = previous[-1]
        delta = birth_utc - target["time_utc"]

    days = delta.total_seconds() / 86400.0
    start_age_years = days / 3.0
    start_date = birth_utc + timedelta(days=start_age_years * 365.2425)
    trace = {
        "daeun_reference_boundary": target["name"],
        "daeun_reference_boundary_utc": target["time_utc"].isoformat(),
        "daeun_delta_days": days,
    }
    return round(start_age_years, 3), start_date.date().isoformat(), target["time_utc"], trace


def _daeun_sequence(direction: str, month_pillar_value: Any, start_age: float | None, count: int = 10) -> list[DaeunEntry]:
    if direction == "unknown" or start_age is None:
        return []

    entries: list[DaeunEntry] = []
    step = 1 if direction == "forward" else -1
    for order in range(1, count + 1):
        pillar = sexagenary_pillar(month_pillar_value.sexagenary_index + step * order)
        start = round(start_age + (order - 1) * 10.0, 3)
        end = round(start_age + order * 10.0, 3)
        entries.append(DaeunEntry(order=order, pillar=pillar, start_age_years=start, end_age_years=end))
    return entries


def build_birth_chart(birth_input: BirthInput) -> BirthChartResult:
    warnings: list[str] = []
    solar_date, date_warnings, trace = _normalize_birth_date(birth_input)
    warnings.extend(date_warnings)

    local_standard_dt = datetime(solar_date.year, solar_date.month, solar_date.day, birth_input.hour, birth_input.minute)
    location, dst_applied, location_warnings = resolve_location(birth_input, local_standard_dt)
    warnings.extend(location_warnings)

    birth_utc = (local_standard_dt - timedelta(minutes=location.timezone_offset_minutes)).replace(tzinfo=timezone.utc)
    true_dt, longitude_correction, eot = true_solar_datetime(
        local_standard_dt,
        location.longitude,
        location.timezone_offset_minutes,
    )

    effective_year, lichun_utc = _effective_year_for_pillar(local_standard_dt.year, birth_utc)
    year_pillar = year_pillar_for_gregorian_year(effective_year)
    month_boundary = _effective_month_boundary(local_standard_dt.year, birth_utc)
    month_pillar_value = month_pillar(year_pillar.stem_index, month_boundary["month_index"])

    day_pillar = day_pillar_for_date(true_dt.year, true_dt.month, true_dt.day)
    hour_branch = hour_branch_index(true_dt)
    hour_pillar_value = hour_pillar(day_pillar.stem_index, hour_branch)

    pillars = {
        "year": year_pillar,
        "month": month_pillar_value,
        "day": day_pillar,
        "hour": hour_pillar_value,
    }
    ten_gods_by_stem, ten_gods_by_hidden, hidden = _ten_gods(day_pillar.stem, pillars)

    direction = _daeun_direction(birth_input.gender, year_pillar.stem_index)
    daeun_start_age, daeun_start_date, daeun_ref_utc, daeun_trace = _daeun_start(direction, local_standard_dt.year, birth_utc)
    daeun_sequence = _daeun_sequence(direction, month_pillar_value, daeun_start_age)

    boundary_sensitive, boundary_type, boundary_distance, boundary_trace = _boundary_status(
        local_standard_dt.year,
        birth_utc,
        true_dt,
    )
    daeun_boundary_sensitive = bool(daeun_start_age is not None and daeun_start_age <= 1.0)

    trace.update(
        {
            "location": {
                "country": location.country,
                "city": location.city,
                "latitude": location.latitude,
                "longitude": location.longitude,
            },
            "birth_utc": birth_utc.isoformat(),
            "true_solar_datetime": true_dt.isoformat(),
            "effective_year_for_pillar": effective_year,
            "lichun_utc": lichun_utc.isoformat(),
            "month_boundary": {
                "name": month_boundary["name"],
                "year": month_boundary["year"],
                "longitude": month_boundary["longitude"],
                "time_utc": month_boundary["time_utc"].isoformat(),
            },
            "longitude_correction_minutes": longitude_correction,
            "equation_of_time_minutes": eot,
            "daeun": daeun_trace,
            "boundary": boundary_trace,
        }
    )

    if direction == "unknown":
        warnings.append("Gender is unknown; daeun direction and sequence were not calculated.")

    return BirthChartResult(
        normalized_birth_datetime=local_standard_dt.isoformat(timespec="minutes"),
        birth_datetime_utc=birth_utc.isoformat(),
        birth_location={
            "country": location.country,
            "city": location.city,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        timezone_offset_minutes=location.timezone_offset_minutes,
        dst_applied=dst_applied,
        longitude_correction_minutes=round(longitude_correction, 3),
        equation_of_time_minutes=round(eot, 3),
        true_solar_datetime=true_dt.isoformat(timespec="minutes"),
        year_pillar=year_pillar,
        month_pillar=month_pillar_value,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar_value,
        hidden_stems=hidden,
        ten_gods_by_stem=ten_gods_by_stem,
        ten_gods_by_branch_hidden=ten_gods_by_hidden,
        daeun_direction=direction,
        daeun_start_age=daeun_start_age,
        daeun_start_date=daeun_start_date,
        daeun_sequence=daeun_sequence,
        boundary_sensitive=boundary_sensitive,
        boundary_type=boundary_type,
        boundary_distance_minutes=boundary_distance,
        daeun_boundary_sensitive=daeun_boundary_sensitive,
        calculation_warnings=warnings,
        calculation_trace=trace,
    )
