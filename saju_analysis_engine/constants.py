"""Internal rule constants for the saju analysis engine.

The analysis layer uses stable romanized keys. Customer-facing Korean wording
is intentionally kept out of this first rule engine layer.
"""

from __future__ import annotations


ELEMENTS = ["wood", "fire", "earth", "metal", "water"]

ELEMENT_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

ELEMENT_CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}

ELEMENT_GENERATED_BY = {child: parent for parent, child in ELEMENT_GENERATES.items()}
ELEMENT_CONTROLLED_BY = {target: controller for controller, target in ELEMENT_CONTROLS.items()}

STEM_METADATA = {
    "gap": {"element": "wood", "yin_yang": "yang"},
    "eul": {"element": "wood", "yin_yang": "yin"},
    "byeong": {"element": "fire", "yin_yang": "yang"},
    "jeong": {"element": "fire", "yin_yang": "yin"},
    "mu": {"element": "earth", "yin_yang": "yang"},
    "gi": {"element": "earth", "yin_yang": "yin"},
    "gyeong": {"element": "metal", "yin_yang": "yang"},
    "sin": {"element": "metal", "yin_yang": "yin"},
    "im": {"element": "water", "yin_yang": "yang"},
    "gye": {"element": "water", "yin_yang": "yin"},
}

BRANCH_METADATA = {
    "ja": {"element": "water", "season": "winter"},
    "chuk": {"element": "earth", "season": "late_winter"},
    "in": {"element": "wood", "season": "spring"},
    "myo": {"element": "wood", "season": "spring"},
    "jin": {"element": "earth", "season": "late_spring"},
    "sa": {"element": "fire", "season": "summer"},
    "o": {"element": "fire", "season": "summer"},
    "mi": {"element": "earth", "season": "late_summer"},
    "sin": {"element": "metal", "season": "autumn"},
    "yu": {"element": "metal", "season": "autumn"},
    "sul": {"element": "earth", "season": "late_autumn"},
    "hae": {"element": "water", "season": "winter"},
}

BRANCH_HIDDEN_STEMS = {
    # Keep the main qi first because month-command and branch-main rules use
    # index zero. Residual and middle qi follow with lower weights.
    "ja": [("gye", 0.8), ("im", 0.2)],
    "chuk": [("gi", 0.6), ("gye", 0.25), ("sin", 0.15)],
    "in": [("gap", 0.6), ("byeong", 0.25), ("mu", 0.15)],
    "myo": [("eul", 0.8), ("gap", 0.2)],
    "jin": [("mu", 0.6), ("eul", 0.25), ("gye", 0.15)],
    "sa": [("byeong", 0.6), ("mu", 0.25), ("gyeong", 0.15)],
    "o": [("jeong", 0.6), ("gi", 0.25), ("byeong", 0.15)],
    "mi": [("gi", 0.6), ("jeong", 0.25), ("eul", 0.15)],
    "sin": [("gyeong", 0.6), ("im", 0.25), ("mu", 0.15)],
    "yu": [("sin", 0.8), ("gyeong", 0.2)],
    "sul": [("mu", 0.6), ("sin", 0.25), ("jeong", 0.15)],
    "hae": [("im", 0.6), ("gap", 0.25), ("mu", 0.15)],
}

POSITION_STEM_WEIGHTS = {
    "year": 0.85,
    "month": 1.15,
    "day": 1.2,
    "hour": 0.9,
}

POSITION_BRANCH_WEIGHTS = {
    "year": 0.8,
    "month": 1.35,
    "day": 1.05,
    "hour": 0.9,
}

MONTH_SEASON_MODIFIERS = {
    "in": {"wood": 1.7, "fire": 1.2, "earth": 0.85, "metal": 0.65, "water": 0.9},
    "myo": {"wood": 1.75, "fire": 1.2, "earth": 0.8, "metal": 0.6, "water": 0.9},
    "jin": {"wood": 1.0, "fire": 0.85, "earth": 1.25, "metal": 0.75, "water": 0.95},
    "sa": {"wood": 0.9, "fire": 1.7, "earth": 1.2, "metal": 0.75, "water": 0.55},
    "o": {"wood": 0.85, "fire": 1.75, "earth": 1.25, "metal": 0.7, "water": 0.5},
    "mi": {"wood": 0.8, "fire": 1.1, "earth": 1.35, "metal": 0.75, "water": 0.55},
    "sin": {"wood": 0.6, "fire": 0.75, "earth": 1.0, "metal": 1.7, "water": 1.15},
    "yu": {"wood": 0.55, "fire": 0.7, "earth": 1.0, "metal": 1.75, "water": 1.1},
    "sul": {"wood": 0.55, "fire": 0.8, "earth": 1.35, "metal": 1.1, "water": 0.65},
    "hae": {"wood": 1.15, "fire": 0.55, "earth": 0.75, "metal": 0.9, "water": 1.7},
    "ja": {"wood": 1.1, "fire": 0.5, "earth": 0.75, "metal": 0.9, "water": 1.75},
    "chuk": {"wood": 0.65, "fire": 0.55, "earth": 1.35, "metal": 0.85, "water": 1.1},
}

TEN_GOD_GROUPS = {
    "bi_gyeon": "peer",
    "geob_jae": "peer",
    "sik_sin": "output",
    "sang_gwan": "output",
    "pyeon_jae": "wealth",
    "jeong_jae": "wealth",
    "pyeon_gwan": "officer",
    "jeong_gwan": "officer",
    "pyeon_in": "resource",
    "jeong_in": "resource",
}

POSITION_DOMAINS = {
    "year": ["background", "network", "family_origin"],
    "month": ["career", "social_role", "parents"],
    "day": ["self", "love", "marriage", "home"],
    "hour": ["output", "future", "children", "late_life"],
    "year_flow": ["annual_event"],
    "quarter_flow": ["seasonal_event"],
    "month_flow": ["monthly_event"],
    "daeun": ["decade_environment"],
}

DOMAIN_ORDER = ["money", "career", "love", "marriage"]
