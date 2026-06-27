"""Pure element and stem-combination profile separate from ten-god translation."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
)
from .models import ElementCombinationProfile, ElementCombinationSignal


POSITION_ORDER = ("year", "month", "day", "hour")
STEM_ORDER = ("gap", "eul", "byeong", "jeong", "mu", "gi", "gyeong", "sin", "im", "gye")
SERVICE_DOMAINS = ("money", "career", "love", "marriage")

STEM_HANJA = {
    "gap": "甲",
    "eul": "乙",
    "byeong": "丙",
    "jeong": "丁",
    "mu": "戊",
    "gi": "己",
    "gyeong": "庚",
    "sin": "辛",
    "im": "壬",
    "gye": "癸",
}

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")

SPECIFIC_STEM_PAIR_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("eul", "byeong"): {
        "relation_type": "eul_byeong_social_expansion",
        "source_rule": "오행의 특성과 오행의 배합 정리: 을목과 병화의 배합",
        "domain_links": ["career", "love", "marriage"],
        "trait_keywords": [
            "관계망 확장",
            "사회적 교류",
            "조직적 결속",
            "친화주의",
            "도움 받기",
        ],
        "interpretation": (
            "乙丙 배합은 을목의 관계망 기반 성장성이 병화의 소통, 교류, 인도하는 힘을 만난 것입니다. "
            "개인의 실력만으로 밀고 나가기보다 사람을 만나고 설득하며, 팀이나 조직의 성장 안에서 "
            "자신의 역량을 인정받으려는 성향으로 봅니다. 이 배합은 자발적 사회 확장, 도움 받기, "
            "관계 속 포트폴리오 형성의 의미가 강합니다."
        ),
    },
}

SPECIFIC_ELEMENT_SET_RULES: dict[tuple[str, ...], dict[str, Any]] = {
    ("wood", "fire"): {
        "relation_type": "wood_fire_expression_growth",
        "source_rule": "오행 물상 배합 기본값: 목화",
        "domain_links": ["career", "love"],
        "trait_keywords": ["기획 표현", "교육·콘텐츠", "관계 확장", "말의 설득력"],
        "interpretation": (
            "木火 배합은 생각, 성장성, 기획력이 표현과 노출로 이어지는 구성입니다. "
            "직업에서는 교육, 발표, 홍보, 콘텐츠, 기획처럼 보이게 만드는 일에 강하고, "
            "관계에서는 먼저 분위기를 만들고 호감을 드러내는 방식으로 나타납니다."
        ),
    },
    ("fire", "earth"): {
        "relation_type": "fire_earth_reputation_foundation",
        "source_rule": "오행 물상 배합 기본값: 화토",
        "domain_links": ["career", "money", "marriage"],
        "trait_keywords": ["평판의 축적", "브랜드 기반", "신뢰 형성", "생활 안정"],
        "interpretation": (
            "火土 배합은 드러난 평가와 명성이 신뢰, 기반, 생활 안정으로 굳어지는 구성입니다. "
            "직업에서는 평판과 실적을 조직 안의 자리로 만들고, 재물에서는 보이는 성과를 "
            "소유와 축적으로 바꾸려는 힘으로 작용합니다."
        ),
    },
    ("earth", "metal"): {
        "relation_type": "earth_metal_system_asset",
        "source_rule": "오행 물상 배합 기본값: 토금",
        "domain_links": ["money", "career"],
        "trait_keywords": ["관리 체계", "품질 기준", "회계·심사", "자산 정리"],
        "interpretation": (
            "土金 배합은 기반, 자산, 조직을 기준과 성과물로 정리하는 구성입니다. "
            "재물에서는 회계, 세무, 심사, 계약 관리처럼 숫자와 권리를 분명히 하는 힘으로 나타나고, "
            "직업에서는 운영, 품질, 시스템, 규정 관리에 강점이 붙습니다."
        ),
    },
    ("metal", "water"): {
        "relation_type": "metal_water_analysis_distribution",
        "source_rule": "오행 물상 배합 기본값: 금수",
        "domain_links": ["career", "money"],
        "trait_keywords": ["분석 유통", "자료 해석", "금융·데이터", "판단의 정밀도"],
        "interpretation": (
            "金水 배합은 기준, 기술, 문서, 분석력이 정보와 유통으로 이어지는 구성입니다. "
            "직업에서는 데이터, 금융, 전략, 리서치, 기술 문서에 강하고, 재물에서는 계산과 정보가 "
            "수입 판단의 근거가 됩니다."
        ),
    },
    ("water", "wood"): {
        "relation_type": "water_wood_learning_planning",
        "source_rule": "오행 물상 배합 기본값: 수목",
        "domain_links": ["career", "love", "personality"],
        "trait_keywords": ["학습 성장", "기회 포착", "관계 적응", "기획 확장"],
        "interpretation": (
            "水木 배합은 정보, 학습, 이동성이 성장과 기획으로 이어지는 구성입니다. "
            "직업에서는 배움이 빠르고 새 방향을 잡는 감각이 좋으며, 관계에서는 상대의 분위기를 읽고 "
            "자연스럽게 맞춰 가는 힘으로 나타납니다."
        ),
    },
    ("wood", "earth"): {
        "relation_type": "wood_earth_foundation_pressure",
        "source_rule": "오행 물상 배합 기본값: 목토",
        "domain_links": ["money", "career", "marriage"],
        "trait_keywords": ["기반 개척", "현실 압박", "자산 충돌", "생활 책임"],
        "interpretation": (
            "木土 배합은 성장하려는 힘이 기존 기반, 자산, 생활 조건을 밀고 들어가는 구성입니다. "
            "좋게 작용하면 굳은 환경을 바꾸고 새 일을 시작하지만, 무리하면 돈, 부동산, 가족 책임에서 "
            "압박이 먼저 커집니다."
        ),
    },
    ("fire", "metal"): {
        "relation_type": "fire_metal_refinement_pressure",
        "source_rule": "오행 물상 배합 기본값: 화금",
        "domain_links": ["career", "love"],
        "trait_keywords": ["평가 압박", "기술 제련", "공개 검증", "말과 기준의 충돌"],
        "interpretation": (
            "火金 배합은 드러내는 힘과 기준, 기술, 규정이 맞부딪히는 구성입니다. "
            "직업에서는 실력과 결과가 공개적으로 평가받고, 관계에서는 말투와 기준이 분명해져 "
            "호감과 긴장이 함께 생깁니다."
        ),
    },
    ("earth", "water"): {
        "relation_type": "earth_water_cashflow_containment",
        "source_rule": "오행 물상 배합 기본값: 토수",
        "domain_links": ["money", "marriage"],
        "trait_keywords": ["현금 보존", "자금 통제", "생활비 관리", "감정 절제"],
        "interpretation": (
            "土水 배합은 돈, 정보, 감정의 움직임을 현실의 기준으로 막고 관리하는 구성입니다. "
            "재물에서는 현금 보존, 지출 통제, 채무 관리에 강하게 작용하고, 결혼에서는 생활비와 "
            "가계 기준을 분명히 해야 안정됩니다."
        ),
    },
    ("metal", "wood"): {
        "relation_type": "metal_wood_pruning_order",
        "source_rule": "오행 물상 배합 기본값: 금목",
        "domain_links": ["career", "love", "personality"],
        "trait_keywords": ["기준 정리", "성장 조율", "편집·검수", "관계의 선"],
        "interpretation": (
            "金木 배합은 자라나는 힘을 기준, 규칙, 판단력으로 다듬는 구성입니다. "
            "직업에서는 기획을 검수하고 품질을 높이는 힘으로 쓰이며, 관계에서는 호감이 있어도 "
            "선을 분명히 보는 태도로 나타납니다."
        ),
    },
    ("water", "fire"): {
        "relation_type": "water_fire_visibility_control",
        "source_rule": "오행 물상 배합 기본값: 수화",
        "domain_links": ["career", "love", "personality"],
        "trait_keywords": ["명예 조절", "감정 절제", "전략적 노출", "판단과 표현의 긴장"],
        "interpretation": (
            "水火 배합은 정보, 생각, 감정의 깊이와 표현, 명예, 노출이 맞서는 구성입니다. "
            "좋게 쓰이면 과열된 선택을 식히고 전략적으로 드러내지만, 불안정하면 생각은 많은데 "
            "표현 시점이 흔들립니다."
        ),
    },
    ("wood", "fire", "earth"): {
        "relation_type": "wood_fire_earth_result_foundation",
        "source_rule": "오행 물상 배합 기본값: 목화토",
        "domain_links": ["career", "money", "marriage"],
        "trait_keywords": ["기획의 성과화", "브랜드 기반", "생활 정착", "결과의 축적"],
        "interpretation": (
            "木火土 배합은 기획과 성장성이 표현을 거쳐 기반과 소유로 굳어지는 구성입니다. "
            "직업에서는 아이디어를 보이는 결과로 만들고, 재물에서는 결과물이 신뢰와 자산으로 "
            "남는지가 판단의 중심입니다."
        ),
    },
    ("fire", "earth", "metal"): {
        "relation_type": "fire_earth_metal_reputation_system",
        "source_rule": "오행 물상 배합 기본값: 화토금",
        "domain_links": ["career", "money"],
        "trait_keywords": ["평판의 제도화", "품질 체계", "성과 검증", "공식 기준"],
        "interpretation": (
            "火土金 배합은 노출된 평가가 기반을 만들고 다시 기준과 성과물로 정리되는 구성입니다. "
            "직업에서는 평판, 직함, 품질 기준이 함께 움직이고, 재물에서는 성과가 문서와 권리로 "
            "확정되는지를 봅니다."
        ),
    },
    ("earth", "metal", "water"): {
        "relation_type": "earth_metal_water_asset_information",
        "source_rule": "오행 물상 배합 기본값: 토금수",
        "domain_links": ["money", "career"],
        "trait_keywords": ["자산 정보화", "금융 판단", "자료 기반 수익", "회수 관리"],
        "interpretation": (
            "土金水 배합은 자산과 조직 기반이 기준, 문서, 분석을 거쳐 정보와 현금 흐름으로 이어지는 구성입니다. "
            "재물에서는 금융, 회수, 정산, 현금 관리가 중요하고, 직업에서는 데이터와 제도 안에서 "
            "성과를 만드는 힘이 강합니다."
        ),
    },
    ("metal", "water", "wood"): {
        "relation_type": "metal_water_wood_research_planning",
        "source_rule": "오행 물상 배합 기본값: 금수목",
        "domain_links": ["career", "personality"],
        "trait_keywords": ["분석 후 기획", "전략 수립", "자료 기반 성장", "학습 설계"],
        "interpretation": (
            "金水木 배합은 기준과 분석이 정보 수집을 거쳐 새 기획과 성장 방향으로 이어지는 구성입니다. "
            "직업에서는 리서치, 전략, 기술 기획에 강하고, 성향에서는 바로 움직이기보다 근거를 모은 뒤 "
            "방향을 잡는 편입니다."
        ),
    },
    ("water", "wood", "fire"): {
        "relation_type": "water_wood_fire_learning_expression",
        "source_rule": "오행 물상 배합 기본값: 수목화",
        "domain_links": ["career", "love", "personality"],
        "trait_keywords": ["배움의 표현", "성장 노출", "교육·상담", "관계 친화"],
        "interpretation": (
            "水木火 배합은 학습과 정보가 성장성을 만들고 다시 표현과 명예로 드러나는 구성입니다. "
            "직업에서는 교육, 상담, 콘텐츠, 발표에 강하고, 관계에서는 상대를 이해한 뒤 자연스럽게 "
            "호감을 표현하는 방식으로 나타납니다."
        ),
    },
}

GENERIC_RELATION_RULES = {
    "element_generation": {
        "domain_links": ["money", "career"],
        "trait_keywords": ["단계적 성장", "활용", "경험 전환"],
        "interpretation": "서로 생하는 오행이 이어져 배움, 경험, 표현, 결과가 다음 단계로 넘어가기 쉽습니다.",
    },
    "element_control": {
        "domain_links": ["career", "marriage"],
        "trait_keywords": ["기준 조정", "압박", "선택"],
        "interpretation": "서로 극하는 오행이 함께 있어 기준을 세우고 조정해야 하는 요구가 커집니다.",
    },
    "same_element_density": {
        "domain_links": ["career", "money"],
        "trait_keywords": ["성향 반복", "동질성", "집중"],
        "interpretation": "같은 오행이 겹쳐 해당 오행의 성향이 반복되고 한 방향으로 집중됩니다.",
    },
    "element_mixed": {
        "domain_links": ["career"],
        "trait_keywords": ["복합성", "상황 의존", "해석 보류"],
        "interpretation": "오행이 직접 생극으로만 정리되지 않아 다른 글자와 위치 조건을 함께 보아야 합니다.",
    },
}


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult):
    pillars = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar
    return pillars


def _canonical_stems(stems: list[str]) -> list[str]:
    return sorted(stems, key=lambda stem: STEM_ORDER.index(stem))


def _canonical_elements(elements: list[str]) -> tuple[str, ...]:
    unique_elements = list(dict.fromkeys(element for element in elements if element))
    return tuple(sorted(unique_elements, key=lambda element: ELEMENT_ORDER.index(element)))


def _combination_key(stems: list[str]) -> str:
    return "-".join(_canonical_stems(stems))


def _hanja_key(stems: list[str]) -> str:
    return "".join(STEM_HANJA[stem] for stem in _canonical_stems(stems))


def _position_sort_key(position: str) -> int:
    base = position.split(":", 1)[0]
    return POSITION_ORDER.index(base) if base in POSITION_ORDER else 99


def _relation_type_for_stems(stems: list[str]) -> str:
    canonical = tuple(_canonical_stems(stems))
    if len(canonical) == 2 and canonical in SPECIFIC_STEM_PAIR_RULES:
        return str(SPECIFIC_STEM_PAIR_RULES[canonical]["relation_type"])
    elements = [STEM_METADATA[stem]["element"] for stem in canonical]
    element_key = _canonical_elements(elements)
    if element_key in SPECIFIC_ELEMENT_SET_RULES:
        return str(SPECIFIC_ELEMENT_SET_RULES[element_key]["relation_type"])
    if len(set(elements)) == 1:
        return "same_element_density"
    if len(canonical) == 2:
        first, second = elements
        if ELEMENT_GENERATES[first] == second or ELEMENT_GENERATES[second] == first:
            return "element_generation"
        if ELEMENT_CONTROLS[first] == second or ELEMENT_CONTROLS[second] == first:
            return "element_control"
    for first, second in combinations(elements, 2):
        if ELEMENT_GENERATES[first] == second or ELEMENT_GENERATES[second] == first:
            return "element_generation"
        if ELEMENT_CONTROLS[first] == second or ELEMENT_CONTROLS[second] == first:
            return "element_control"
    return "element_mixed"


def _rule_payload(stems: list[str], relation_type: str) -> dict[str, Any]:
    canonical = tuple(_canonical_stems(stems))
    if len(canonical) == 2 and canonical in SPECIFIC_STEM_PAIR_RULES:
        return SPECIFIC_STEM_PAIR_RULES[canonical]
    elements = [STEM_METADATA[stem]["element"] for stem in canonical]
    element_key = _canonical_elements(elements)
    if element_key in SPECIFIC_ELEMENT_SET_RULES:
        return SPECIFIC_ELEMENT_SET_RULES[element_key]
    rule = GENERIC_RELATION_RULES[relation_type]
    return {
        "source_rule": "generic_element_relation",
        "domain_links": rule["domain_links"],
        "trait_keywords": rule["trait_keywords"],
        "interpretation": f"{_hanja_key(stems)} 배합은 {rule['interpretation']}",
    }


def _strength_from_entries(entries: list[dict[str, Any]]) -> str:
    if all(entry["source"] == "visible" for entry in entries):
        return "high"
    if any(entry["source"] == "visible" for entry in entries):
        return "moderate"
    weight = sum(float(entry.get("weight", 0.0)) for entry in entries)
    return "moderate" if weight >= 1.1 else "low"


def _entry_positions(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(list(dict.fromkeys(entry["position"] for entry in entries)), key=_position_sort_key)


def _domain_links(payload_domains: list[str], positions: list[str]) -> list[str]:
    position_domains = {
        "year": ["career", "love"],
        "month": ["career", "money"],
        "day": ["love", "marriage"],
        "hour": ["career", "money", "marriage"],
    }
    domains = list(payload_domains)
    for position in positions:
        base = position.split(":", 1)[0]
        domains.extend(position_domains.get(base, []))
    return [domain for domain in SERVICE_DOMAINS if domain in set(domains)]


def _element_key_for_stems(stems: list[str]) -> tuple[str, ...]:
    return _canonical_elements([STEM_METADATA[stem]["element"] for stem in _canonical_stems(stems)])


def _element_key_label(element_key: tuple[str, ...]) -> str:
    return "".join(ELEMENT_LABELS.get(element, element) for element in element_key)


def _month_variant_note(chart: BirthChartResult, stems: list[str], relation_type: str) -> str:
    if relation_type == "eul_byeong_social_expansion":
        if chart.month_pillar.branch_key in {"hae", "ja", "chuk", "in", "myo"}:
            return "겨울·봄에 태어난 당신에게 이 乙丙 배합은 배움, 관계 형성, 사회적 성장으로 이어집니다."
        return "여름·가을에 태어난 당신에게 이 乙丙 배합은 성장 욕구만으로 끝나지 않고, 표현력과 현실 조건이 갖춰질 때 더 좋은 성과로 이어집니다."
    element_key = _element_key_for_stems(stems)
    if element_key in SPECIFIC_ELEMENT_SET_RULES:
        label = _element_key_label(element_key)
        return f"월지 기준에서는 {label} 배합이 겉으로 드러난 힘인지, 지지와 지장간에 깔린 현실 조건인지가 해석의 핵심입니다."
    return ""


def _day_master_variant_note(chart: BirthChartResult, stems: list[str], relation_type: str) -> str:
    day_stem = chart.day_pillar.stem_key
    if relation_type == "eul_byeong_social_expansion":
        return (
            f"{STEM_HANJA[day_stem]}일간인 당신에게 이 배합은 사람을 만나며 배우고 넓어지는 성향이 뚜렷합니다. "
            "관계 안에서 자신의 능력을 인정받으려는 마음도 분명합니다."
        )
    element_key = _element_key_for_stems(stems)
    if element_key in SPECIFIC_ELEMENT_SET_RULES:
        day_element = STEM_METADATA[day_stem]["element"]
        label = _element_key_label(element_key)
        if day_element in element_key:
            return f"{STEM_HANJA[day_stem]}일간인 당신에게 {label} 배합은 성격과 선택 방식에 직접 나타납니다."
        return f"{STEM_HANJA[day_stem]}일간인 당신에게 {label} 배합은 사람, 일, 돈의 환경 조건으로 먼저 나타납니다."
    return ""


def _signal(
    chart: BirthChartResult,
    *,
    layer: str,
    entries: list[dict[str, Any]],
    signal_suffix: str,
    strength: str | None = None,
) -> ElementCombinationSignal:
    stems = [entry["stem"] for entry in entries]
    relation_type = _relation_type_for_stems(stems)
    payload = _rule_payload(stems, relation_type)
    key = _combination_key(stems)
    branches = [entry["branch"] for entry in entries if entry.get("branch")]
    positions = _entry_positions(entries)
    basis_codes = [
        f"element_combo_{layer}_{relation_type}",
        f"element_combo_{layer}_{key.replace('-', '_')}",
    ]
    return ElementCombinationSignal(
        signal_id=f"element_{layer}_{signal_suffix}_{key.replace('-', '_')}",
        layer=layer,
        combination_key=key,
        positions=positions,
        stems=_canonical_stems(stems),
        branches=list(dict.fromkeys(branches)),
        elements=[STEM_METADATA[stem]["element"] for stem in _canonical_stems(stems)],
        relation_type=relation_type,
        source_rule=str(payload["source_rule"]),
        strength=strength or _strength_from_entries(entries),
        domain_links=_domain_links(list(payload["domain_links"]), positions),
        basis_codes=basis_codes,
        counter_signals=[],
        trait_keywords=list(payload["trait_keywords"]),
        interpretation=str(payload["interpretation"]),
        monthly_variant_note=_month_variant_note(chart, stems, relation_type),
        day_master_variant_note=_day_master_variant_note(chart, stems, relation_type),
    )


def _visible_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        entries.append(
            {
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_STEM_WEIGHTS[position],
            }
        )
    return entries


def _hidden_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        for index, (stem_key, hidden_weight) in enumerate(BRANCH_HIDDEN_STEMS[pillar.branch_key]):
            entries.append(
                {
                    "position": f"{position}:hidden:{index}",
                    "source": "hidden",
                    "stem": stem_key,
                    "branch": pillar.branch_key,
                    "weight": POSITION_BRANCH_WEIGHTS[position] * hidden_weight,
                }
            )
    return entries


def _heavenly_stem_signals(chart: BirthChartResult, entries: list[dict[str, Any]]) -> list[ElementCombinationSignal]:
    signals: list[ElementCombinationSignal] = []
    for size in (2, 3):
        for index, selected in enumerate(combinations(entries, size), start=1):
            signals.append(
                _signal(
                    chart,
                    layer="heavenly_stem",
                    entries=list(selected),
                    signal_suffix=f"{size}_{index}",
                    strength="high",
                )
            )
    return _dedupe_signals(signals)


def _hidden_stem_signals(chart: BirthChartResult, entries: list[dict[str, Any]]) -> list[ElementCombinationSignal]:
    signals: list[ElementCombinationSignal] = []
    for index, selected in enumerate(combinations(entries, 2), start=1):
        signals.append(
            _signal(
                chart,
                layer="hidden_stem",
                entries=list(selected),
                signal_suffix=f"2_{index}",
            )
        )
    return _dedupe_signals(signals, limit=24)


def _stem_branch_signals(chart: BirthChartResult) -> list[ElementCombinationSignal]:
    signals: list[ElementCombinationSignal] = []
    for position, pillar in _pillars(chart).items():
        hidden_stem_key = BRANCH_HIDDEN_STEMS[pillar.branch_key][0][0]
        entries = [
            {
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_STEM_WEIGHTS[position],
            },
            {
                "position": f"{position}:branch_main",
                "source": "hidden",
                "stem": hidden_stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_BRANCH_WEIGHTS[position],
            },
        ]
        signals.append(
            _signal(
                chart,
                layer="stem_branch",
                entries=entries,
                signal_suffix=position,
                strength="high" if pillar.stem_key == hidden_stem_key else "moderate",
            )
        )
    return _dedupe_signals(signals)


def _signal_rank(signal: ElementCombinationSignal) -> tuple[int, int, int]:
    source_rank = 0 if signal.source_rule != "generic_element_relation" else 1
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    domain_rank = -len(signal.domain_links)
    return (source_rank, strength_rank, domain_rank)


def _dedupe_signals(
    signals: list[ElementCombinationSignal],
    limit: int | None = None,
) -> list[ElementCombinationSignal]:
    deduped: list[ElementCombinationSignal] = []
    seen: set[tuple[str, str, tuple[str, ...], str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        key = (signal.layer, signal.relation_type, tuple(signal.positions), signal.combination_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def iter_element_combination_signals(profile: ElementCombinationProfile) -> list[ElementCombinationSignal]:
    return (
        list(profile.heavenly_stem_signals)
        + list(profile.hidden_stem_signals)
        + list(profile.stem_branch_signals)
    )


def _domain_notes(signals: list[ElementCombinationSignal]) -> dict[str, list[str]]:
    notes: dict[str, list[str]] = {domain: [] for domain in SERVICE_DOMAINS}
    seen_relation_by_domain: dict[str, set[str]] = {domain: set() for domain in SERVICE_DOMAINS}
    for signal in sorted(signals, key=_signal_rank):
        for domain in signal.domain_links:
            if signal.relation_type in seen_relation_by_domain[domain]:
                continue
            if len(notes[domain]) < 5 and signal.interpretation not in notes[domain]:
                notes[domain].append(signal.interpretation)
                seen_relation_by_domain[domain].add(signal.relation_type)
    return notes


def _summary_sentences(signals: list[ElementCombinationSignal]) -> list[str]:
    selected: list[ElementCombinationSignal] = []
    seen_relations: set[str] = set()
    for signal in sorted(signals, key=_signal_rank):
        if signal.relation_type in seen_relations:
            continue
        selected.append(signal)
        seen_relations.add(signal.relation_type)
        if len(selected) >= 4:
            break
    sentences: list[str] = []
    for signal in selected:
        keywords = ", ".join(signal.trait_keywords[:3])
        sentences.append(f"당신의 사주에서 {signal.interpretation} 여기서 두드러지는 특성은 {keywords}입니다.")
    return sentences


def build_element_combination_profile(chart: BirthChartResult) -> ElementCombinationProfile:
    visible_entries = _visible_entries(chart)
    hidden_entries = _hidden_entries(chart)
    heavenly_stem_signals = _heavenly_stem_signals(chart, visible_entries)
    hidden_stem_signals = _hidden_stem_signals(chart, hidden_entries)
    stem_branch_signals = _stem_branch_signals(chart)
    all_signals = _dedupe_signals(heavenly_stem_signals + hidden_stem_signals + stem_branch_signals)
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_signal_rank)[:10]]
    return ElementCombinationProfile(
        heavenly_stem_signals=heavenly_stem_signals,
        hidden_stem_signals=hidden_stem_signals,
        stem_branch_signals=stem_branch_signals,
        top_signal_ids=top_signal_ids,
        domain_notes=_domain_notes(all_signals),
        summary_sentences=_summary_sentences(all_signals),
    )
