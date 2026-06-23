"""Pillar and sexagenary-cycle calculation helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

from .astronomy import gregorian_to_jdn
from .constants import BRANCHES, SAJU_MONTH_BOUNDARIES, STEMS
from .models import Pillar


def sexagenary_pillar(index: int) -> Pillar:
    index = index % 60
    stem_index = index % 10
    branch_index = index % 12
    return Pillar(
        stem=STEMS[stem_index]["hanja"],
        branch=BRANCHES[branch_index]["hanja"],
        stem_key=STEMS[stem_index]["key"],
        branch_key=BRANCHES[branch_index]["key"],
        stem_index=stem_index,
        branch_index=branch_index,
        sexagenary_index=index,
    )


def year_pillar_for_gregorian_year(year: int) -> Pillar:
    return sexagenary_pillar((year - 4) % 60)


def day_pillar_for_date(year: int, month: int, day: int) -> Pillar:
    jdn = gregorian_to_jdn(year, month, day)
    return sexagenary_pillar((jdn + 49) % 60)


def month_pillar(year_stem_index: int, saju_month_index: int) -> Pillar:
    base_by_year_stem = {
        0: 2,
        5: 2,
        1: 4,
        6: 4,
        2: 6,
        7: 6,
        3: 8,
        8: 8,
        4: 0,
        9: 0,
    }
    stem_index = (base_by_year_stem[year_stem_index] + saju_month_index) % 10
    branch_index = SAJU_MONTH_BOUNDARIES[saju_month_index]["branch_index"]
    for idx in range(60):
        if idx % 10 == stem_index and idx % 12 == branch_index:
            return sexagenary_pillar(idx)
    raise RuntimeError("Month pillar cycle index not found.")


def hour_branch_index(true_solar_dt: datetime) -> int:
    adjusted_dt = true_solar_dt - timedelta(minutes=30)
    hour = adjusted_dt.hour
    if hour == 23:
        return 0
    return ((hour + 1) // 2) % 12


def hour_pillar(day_stem_index: int, branch_index: int) -> Pillar:
    stem_index = ((day_stem_index % 5) * 2 + branch_index) % 10
    for idx in range(60):
        if idx % 10 == stem_index and idx % 12 == branch_index:
            return sexagenary_pillar(idx)
    raise RuntimeError("Hour pillar cycle index not found.")
