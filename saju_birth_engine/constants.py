"""Shared constants for sexagenary-cycle calculations."""

from __future__ import annotations

STEMS = [
    {"key": "gap", "hanja": "甲", "yin_yang": "yang", "element": "wood"},
    {"key": "eul", "hanja": "乙", "yin_yang": "yin", "element": "wood"},
    {"key": "byeong", "hanja": "丙", "yin_yang": "yang", "element": "fire"},
    {"key": "jeong", "hanja": "丁", "yin_yang": "yin", "element": "fire"},
    {"key": "mu", "hanja": "戊", "yin_yang": "yang", "element": "earth"},
    {"key": "gi", "hanja": "己", "yin_yang": "yin", "element": "earth"},
    {"key": "gyeong", "hanja": "庚", "yin_yang": "yang", "element": "metal"},
    {"key": "sin", "hanja": "辛", "yin_yang": "yin", "element": "metal"},
    {"key": "im", "hanja": "壬", "yin_yang": "yang", "element": "water"},
    {"key": "gye", "hanja": "癸", "yin_yang": "yin", "element": "water"},
]

BRANCHES = [
    {"key": "ja", "hanja": "子", "element": "water"},
    {"key": "chuk", "hanja": "丑", "element": "earth"},
    {"key": "in", "hanja": "寅", "element": "wood"},
    {"key": "myo", "hanja": "卯", "element": "wood"},
    {"key": "jin", "hanja": "辰", "element": "earth"},
    {"key": "sa", "hanja": "巳", "element": "fire"},
    {"key": "o", "hanja": "午", "element": "fire"},
    {"key": "mi", "hanja": "未", "element": "earth"},
    {"key": "sin", "hanja": "申", "element": "metal"},
    {"key": "yu", "hanja": "酉", "element": "metal"},
    {"key": "sul", "hanja": "戌", "element": "earth"},
    {"key": "hae", "hanja": "亥", "element": "water"},
]

HIDDEN_STEMS = {
    "子": ["壬", "癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["甲", "乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丙", "己", "丁"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["庚", "辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

TEN_GODS_BY_DAY_STEM = {
    "甲": {"甲": "比肩", "乙": "劫財", "丙": "食神", "丁": "傷官", "戊": "偏財", "己": "正財", "庚": "七殺", "辛": "正官", "壬": "偏印", "癸": "正印"},
    "乙": {"甲": "劫財", "乙": "比肩", "丙": "傷官", "丁": "食神", "戊": "正財", "己": "偏財", "庚": "正官", "辛": "七殺", "壬": "正印", "癸": "偏印"},
    "丙": {"甲": "偏印", "乙": "正印", "丙": "比肩", "丁": "劫財", "戊": "食神", "己": "傷官", "庚": "偏財", "辛": "正財", "壬": "七殺", "癸": "正官"},
    "丁": {"甲": "正印", "乙": "偏印", "丙": "劫財", "丁": "比肩", "戊": "傷官", "己": "食神", "庚": "正財", "辛": "偏財", "壬": "正官", "癸": "七殺"},
    "戊": {"甲": "七殺", "乙": "正官", "丙": "偏印", "丁": "正印", "戊": "比肩", "己": "劫財", "庚": "食神", "辛": "傷官", "壬": "偏財", "癸": "正財"},
    "己": {"甲": "正官", "乙": "七殺", "丙": "正印", "丁": "偏印", "戊": "劫財", "己": "比肩", "庚": "傷官", "辛": "食神", "壬": "正財", "癸": "偏財"},
    "庚": {"甲": "偏財", "乙": "正財", "丙": "七殺", "丁": "正官", "戊": "偏印", "己": "正印", "庚": "比肩", "辛": "劫財", "壬": "食神", "癸": "傷官"},
    "辛": {"甲": "正財", "乙": "偏財", "丙": "正官", "丁": "七殺", "戊": "正印", "己": "偏印", "庚": "劫財", "辛": "比肩", "壬": "傷官", "癸": "食神"},
    "壬": {"甲": "食神", "乙": "傷官", "丙": "偏財", "丁": "正財", "戊": "七殺", "己": "正官", "庚": "偏印", "辛": "正印", "壬": "比肩", "癸": "劫財"},
    "癸": {"甲": "傷官", "乙": "食神", "丙": "正財", "丁": "偏財", "戊": "正官", "己": "七殺", "庚": "正印", "辛": "偏印", "壬": "劫財", "癸": "比肩"},
}

# Month boundaries used by saju month pillars. The first month starts at
# Lichun, solar longitude 315 degrees, and has the Yin branch.
SAJU_MONTH_BOUNDARIES = [
    {"name": "lichun", "longitude": 315.0, "month_index": 0, "branch_index": 2},
    {"name": "jingzhe", "longitude": 345.0, "month_index": 1, "branch_index": 3},
    {"name": "qingming", "longitude": 15.0, "month_index": 2, "branch_index": 4},
    {"name": "lixia", "longitude": 45.0, "month_index": 3, "branch_index": 5},
    {"name": "mangzhong", "longitude": 75.0, "month_index": 4, "branch_index": 6},
    {"name": "xiaoshu", "longitude": 105.0, "month_index": 5, "branch_index": 7},
    {"name": "liqiu", "longitude": 135.0, "month_index": 6, "branch_index": 8},
    {"name": "bailu", "longitude": 165.0, "month_index": 7, "branch_index": 9},
    {"name": "hanlu", "longitude": 195.0, "month_index": 8, "branch_index": 10},
    {"name": "lidong", "longitude": 225.0, "month_index": 9, "branch_index": 11},
    {"name": "daxue", "longitude": 255.0, "month_index": 10, "branch_index": 0},
    {"name": "xiaohan", "longitude": 285.0, "month_index": 11, "branch_index": 1},
]
