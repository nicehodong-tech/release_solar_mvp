"""Data models for the birth chart engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


CalendarType = Literal["solar", "lunar"]
Gender = Literal["male", "female", "unknown"]


@dataclass(frozen=True)
class BirthInput:
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    calendar_type: CalendarType = "solar"
    leap_lunar_month: bool = False
    country: str = "KR"
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone_offset_minutes: int | None = None
    gender: Gender = "unknown"


@dataclass(frozen=True)
class Location:
    country: str
    city: str
    latitude: float
    longitude: float
    timezone_offset_minutes: int


@dataclass(frozen=True)
class Pillar:
    stem: str
    branch: str
    stem_key: str
    branch_key: str
    stem_index: int
    branch_index: int
    sexagenary_index: int

    @property
    def label(self) -> str:
        return f"{self.stem}{self.branch}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["label"] = self.label
        return data


@dataclass(frozen=True)
class DaeunEntry:
    order: int
    pillar: Pillar
    start_age_years: float
    end_age_years: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "pillar": self.pillar.to_dict(),
            "start_age_years": self.start_age_years,
            "end_age_years": self.end_age_years,
        }


@dataclass(frozen=True)
class BirthChartResult:
    normalized_birth_datetime: str
    birth_datetime_utc: str
    birth_location: dict[str, Any]
    timezone_offset_minutes: int
    dst_applied: bool
    longitude_correction_minutes: float
    equation_of_time_minutes: float
    true_solar_datetime: str
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    hidden_stems: dict[str, list[str]]
    ten_gods_by_stem: dict[str, str]
    ten_gods_by_branch_hidden: dict[str, list[str]]
    daeun_direction: str
    daeun_start_age: float | None
    daeun_start_date: str | None
    daeun_sequence: list[DaeunEntry]
    boundary_sensitive: bool
    boundary_type: str | None
    boundary_distance_minutes: float | None
    daeun_boundary_sensitive: bool
    calculation_warnings: list[str] = field(default_factory=list)
    calculation_trace: dict[str, Any] = field(default_factory=dict)

    @property
    def four_pillars(self) -> dict[str, str]:
        return {
            "year": self.year_pillar.label,
            "month": self.month_pillar.label,
            "day": self.day_pillar.label,
            "hour": self.hour_pillar.label,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_birth_datetime": self.normalized_birth_datetime,
            "birth_datetime_utc": self.birth_datetime_utc,
            "birth_location": self.birth_location,
            "timezone_offset_minutes": self.timezone_offset_minutes,
            "dst_applied": self.dst_applied,
            "longitude_correction_minutes": self.longitude_correction_minutes,
            "equation_of_time_minutes": self.equation_of_time_minutes,
            "true_solar_datetime": self.true_solar_datetime,
            "year_pillar": self.year_pillar.to_dict(),
            "month_pillar": self.month_pillar.to_dict(),
            "day_pillar": self.day_pillar.to_dict(),
            "hour_pillar": self.hour_pillar.to_dict(),
            "four_pillars": self.four_pillars,
            "hidden_stems": self.hidden_stems,
            "ten_gods_by_stem": self.ten_gods_by_stem,
            "ten_gods_by_branch_hidden": self.ten_gods_by_branch_hidden,
            "daeun_direction": self.daeun_direction,
            "daeun_start_age": self.daeun_start_age,
            "daeun_start_date": self.daeun_start_date,
            "daeun_sequence": [entry.to_dict() for entry in self.daeun_sequence],
            "boundary_sensitive": self.boundary_sensitive,
            "boundary_type": self.boundary_type,
            "boundary_distance_minutes": self.boundary_distance_minutes,
            "daeun_boundary_sensitive": self.daeun_boundary_sensitive,
            "calculation_warnings": self.calculation_warnings,
            "calculation_trace": self.calculation_trace,
        }
