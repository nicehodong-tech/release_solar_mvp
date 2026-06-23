"""Location and civil-time helpers."""

from __future__ import annotations

from datetime import datetime

from .models import BirthInput, Location


KOREA_LOCATIONS = {
    "춘천": (37.8813, 127.7298),
    "chuncheon": (37.8813, 127.7298),
    "서울": (37.5665, 126.9780),
    "seoul": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "busan": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "daegu": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "incheon": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "gwangju": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "daejeon": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "ulsan": (35.5384, 129.3114),
    "세종": (36.4800, 127.2890),
    "sejong": (36.4800, 127.2890),
    "제주": (33.4996, 126.5312),
    "jeju": (33.4996, 126.5312),
    "수원": (37.2636, 127.0286),
    "suwon": (37.2636, 127.0286),
    "청주": (36.6424, 127.4890),
    "cheongju": (36.6424, 127.4890),
    "전주": (35.8242, 127.1480),
    "jeonju": (35.8242, 127.1480),
    "창원": (35.2279, 128.6811),
    "changwon": (35.2279, 128.6811),
    "강릉": (37.7519, 128.8761),
    "gangneung": (37.7519, 128.8761),
    "원주": (37.3422, 127.9202),
    "wonju": (37.3422, 127.9202),
}


def normalize_country(country: str) -> str:
    value = country.strip().lower()
    if value in {"kr", "kor", "korea", "south korea", "republic of korea", "대한민국", "한국"}:
        return "KR"
    return country.strip().upper()


def korea_timezone_offset_minutes(local_dt: datetime) -> tuple[int, bool, list[str]]:
    warnings: list[str] = []
    offset = 540
    dst = False

    if datetime(1954, 3, 21) <= local_dt < datetime(1961, 8, 10):
        offset = 510
        warnings.append("Korea UTC+08:30 historical standard time applied.")

    # South Korea used daylight saving time for the Seoul Olympic period.
    if datetime(1987, 5, 10, 2, 0) <= local_dt < datetime(1987, 10, 11, 3, 0):
        offset += 60
        dst = True
    if datetime(1988, 5, 8, 2, 0) <= local_dt < datetime(1988, 10, 9, 3, 0):
        offset += 60
        dst = True

    if local_dt.year < 1954:
        warnings.append("Pre-1954 Korean time-zone history is not fully modeled.")

    return offset, dst, warnings


def resolve_location(birth_input: BirthInput, local_dt: datetime) -> tuple[Location, bool, list[str]]:
    warnings: list[str] = []
    country = normalize_country(birth_input.country)

    if birth_input.timezone_offset_minutes is not None:
        offset = birth_input.timezone_offset_minutes
        dst = False
    elif country == "KR":
        offset, dst, warnings = korea_timezone_offset_minutes(local_dt)
    else:
        raise ValueError("timezone_offset_minutes is required for non-KR locations.")

    if birth_input.latitude is not None and birth_input.longitude is not None:
        city = birth_input.city or "custom"
        return Location(country, city, birth_input.latitude, birth_input.longitude, offset), dst, warnings

    if country == "KR" and birth_input.city:
        key = birth_input.city.strip().lower()
        if key in KOREA_LOCATIONS:
            lat, lon = KOREA_LOCATIONS[key]
            return Location(country, birth_input.city, lat, lon, offset), dst, warnings

    raise ValueError("A known Korean city or explicit latitude/longitude is required.")
