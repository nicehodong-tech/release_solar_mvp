"""Audited contracts for every public annual metric.

Annual scores are not synonyms for the four broad flow components.  Each
metric declares how it reads opportunity, realization, change, risk control,
the natal capacities that can retain the event, and the ten-god groups that
activate or burden it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnnualMetricContract:
    component_weights: tuple[float, float, float, float]
    change_mode: str
    natal_labels: tuple[str, ...]
    support_groups: tuple[str, ...]
    pressure_groups: tuple[str, ...]


def _annual(
    weights: tuple[float, float, float, float],
    change_mode: str,
    natal: str,
    support: str,
    pressure: str,
) -> AnnualMetricContract:
    if change_mode not in {"activation", "guard", "neutral"}:
        raise ValueError(f"unsupported annual change mode: {change_mode}")
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError(f"annual component weights must sum to 1.0: {weights}")
    split = lambda value: tuple(item.strip() for item in value.split("|") if item.strip())
    return AnnualMetricContract(weights, change_mode, split(natal), split(support), split(pressure))


ANNUAL_METRIC_CONTRACTS: dict[str, AnnualMetricContract] = {
    # Overall flow
    "연간 상승도": _annual((0.32, 0.36, 0.12, 0.20), "activation", "직업 성취도|재물 형성력|사회적 인정", "output|wealth|officer", "peer"),
    "기회 유입": _annual((0.52, 0.23, 0.18, 0.07), "activation", "변화 수용성|친화성|수입 창출력", "output|wealth|peer", "resource"),
    "성과 실현도": _annual((0.24, 0.49, 0.08, 0.19), "activation", "직업 성취도|보상 회수력|실무 처리력", "output|wealth|officer", "peer"),
    "변화 강도": _annual((0.10, 0.18, 0.43, 0.29), "guard", "변화 수용성|문제 해결력|위험 감지", "resource|officer", "peer|output"),
    "안정 유지력": _annual((0.13, 0.27, 0.08, 0.52), "guard", "직업 지속성|현금 운용력|관계 유지성", "resource|officer", "peer|output"),
    "회복 탄력성": _annual((0.13, 0.37, 0.09, 0.41), "guard", "문제 해결력|갈등 회복력|손실 회피력", "resource|output|officer", "peer"),
    "외부 지원 정도": _annual((0.39, 0.29, 0.08, 0.24), "activation", "지인 덕|신뢰 형성|조직 적응성", "resource|officer|output", "peer"),
    "주의 필요도": _annual((0.08, 0.15, 0.31, 0.46), "guard", "위험 감지|손실 회피력|문제 해결력", "resource|officer", "peer|output"),
    "체감 만족도": _annual((0.28, 0.38, 0.10, 0.24), "neutral", "감정 조절|자기 기준|관계 유지성", "resource|output", "officer|peer"),
    "연말 잔존 성과": _annual((0.16, 0.41, 0.05, 0.38), "guard", "자산화 성향|전문성 축적|직업 지속성", "resource|wealth|officer", "peer|output"),

    # Career and work
    "직업 성과 상승도": _annual((0.25, 0.48, 0.10, 0.17), "activation", "직업 성취도|실무 처리력", "output|officer", "peer"),
    "평가 상승도": _annual((0.24, 0.45, 0.09, 0.22), "activation", "평가 관리력|사회적 인정", "officer|resource|output", "peer"),
    "승진·직책 상승도": _annual((0.20, 0.47, 0.11, 0.22), "activation", "직책 상승성|권한 확보력", "officer|resource|wealth", "output|peer"),
    "역할 확장": _annual((0.37, 0.31, 0.25, 0.07), "activation", "책임 감각|실무 처리력|직업 성취도", "officer|output", "resource"),
    "권한 확대": _annual((0.22, 0.43, 0.15, 0.20), "activation", "권한 확보력|직책 상승성|자기 기준", "officer|resource|wealth", "peer|output"),
    "전문성 강화": _annual((0.19, 0.45, 0.08, 0.28), "activation", "전문성 축적|몰입 성향|신중성", "resource|output", "wealth|peer"),
    "이직 기회": _annual((0.48, 0.22, 0.24, 0.06), "activation", "변화 수용성|직업 성취도|자기 기준", "output|wealth|peer", "resource|officer"),
    "직업 변동": _annual((0.10, 0.17, 0.48, 0.25), "guard", "직업 지속성|변화 수용성|문제 해결력", "resource|officer", "peer|output"),
    "독립 업무 기회": _annual((0.46, 0.25, 0.23, 0.06), "activation", "독립 업무성|자기 기준|수입 창출력", "output|wealth|peer", "officer|resource"),
    "조직 지원": _annual((0.36, 0.34, 0.07, 0.23), "activation", "조직 적응성|신뢰 형성|지인 덕", "resource|officer", "output|peer"),
    "경쟁 노출": _annual((0.08, 0.13, 0.34, 0.45), "guard", "경쟁 대응력|자기 기준|평가 관리력", "officer|resource", "peer|output"),
    "업무 갈등": _annual((0.07, 0.15, 0.29, 0.49), "guard", "갈등 회피력|감정 조절|문제 해결력", "resource|officer|output", "peer"),
    "업무 부담": _annual((0.06, 0.17, 0.25, 0.52), "guard", "책임 감각|문제 해결력|직업 지속성", "resource|officer", "output|peer"),
    "문서·계약 주의 정도": _annual((0.07, 0.21, 0.20, 0.52), "guard", "계약 안정성|신중성|위험 감지", "resource|officer|wealth", "output|peer"),
    "직업 지속 안정성": _annual((0.12, 0.32, 0.05, 0.51), "guard", "직업 지속성|조직 적응성|전문성 축적", "resource|officer", "output|peer"),
    "성과 보상도": _annual((0.18, 0.51, 0.08, 0.23), "activation", "보상 회수력|평가 관리력|수입 창출력", "output|wealth|officer", "peer"),

    # Money
    "수입 상승도": _annual((0.28, 0.47, 0.10, 0.15), "activation", "수입 창출력|재물 형성력", "output|wealth", "peer|resource"),
    "추가 수입 기회": _annual((0.50, 0.25, 0.18, 0.07), "activation", "수입 창출력|투자 판단력|독립 업무성", "output|wealth", "peer"),
    "현금흐름 안정성": _annual((0.14, 0.32, 0.05, 0.49), "guard", "현금 운용력|손실 회피력|자산화 성향", "wealth|resource|officer", "peer|output"),
    "목돈 형성": _annual((0.17, 0.48, 0.06, 0.29), "guard", "자산화 성향|후반 축재성|보상 회수력", "wealth|resource|officer", "peer"),
    "자산 증가": _annual((0.21, 0.45, 0.06, 0.28), "guard", "재물 형성력|자산화 성향|후반 축재성", "wealth|resource|output", "peer"),
    "지출 압박": _annual((0.05, 0.12, 0.24, 0.59), "guard", "현금 운용력|손실 회피력|공동재 관리", "resource|officer", "peer|output"),
    "예상 밖 지출": _annual((0.04, 0.11, 0.31, 0.54), "guard", "손실 회피력|현금 운용력|위험 감지", "resource|officer", "peer|output"),
    "소비 통제력": _annual((0.09, 0.28, 0.04, 0.59), "guard", "현금 운용력|손실 회피력|신중성", "resource|officer|wealth", "output|peer"),
    "투자 기회": _annual((0.48, 0.25, 0.21, 0.06), "activation", "투자 판단력|재물 형성력|수입 창출력", "wealth|output", "peer|resource"),
    "투자 판단 안정성": _annual((0.13, 0.35, 0.05, 0.47), "guard", "투자 판단력|위험 감지|신중성", "resource|wealth|officer", "output|peer"),
    "계약 성사": _annual((0.34, 0.43, 0.13, 0.10), "activation", "계약 안정성|보상 회수력|수입 창출력", "wealth|officer|resource", "peer"),
    "계약 안정성": _annual((0.10, 0.33, 0.04, 0.53), "guard", "계약 안정성|손실 회피력|신중성", "resource|officer|wealth", "output|peer"),
    "손실 노출": _annual((0.04, 0.10, 0.23, 0.63), "guard", "손실 회피력|투자 판단력|위험 감지", "resource|officer", "peer|output"),
    "공동 재정 안정성": _annual((0.10, 0.30, 0.04, 0.56), "guard", "공동재 관리|재정 합의성|현금 운용력", "officer|resource|wealth", "peer|output"),

    # Social relationships
    "신규 인연 유입": _annual((0.52, 0.21, 0.20, 0.07), "activation", "친화성|말의 영향력|변화 수용성", "output|peer", "resource"),
    "관계 확장": _annual((0.47, 0.23, 0.24, 0.06), "activation", "친화성|협력성|말의 영향력", "output|peer", "resource|officer"),
    "신뢰 상승도": _annual((0.20, 0.44, 0.07, 0.29), "guard", "신뢰 형성|관계 유지성|책임 감각", "resource|officer", "output|peer"),
    "협력 성사": _annual((0.31, 0.45, 0.14, 0.10), "activation", "협력성|신뢰 형성|지인 덕", "output|officer|resource", "peer"),
    "귀인 지원": _annual((0.42, 0.31, 0.06, 0.21), "activation", "지인 덕|사회적 인정|신뢰 형성", "resource|officer", "peer"),
    "지인 도움": _annual((0.38, 0.35, 0.05, 0.22), "activation", "지인 덕|관계 유지성|친화성", "resource|output|officer", "peer"),
    "관계 유지 안정성": _annual((0.12, 0.35, 0.04, 0.49), "guard", "관계 유지성|거리 조절|갈등 회피력", "resource|officer", "output|peer"),
    "관계 회복": _annual((0.16, 0.42, 0.12, 0.30), "guard", "갈등 회복력|관계 유지성|감정 조절", "resource|output|officer", "peer"),
    "갈등 노출": _annual((0.05, 0.13, 0.31, 0.51), "guard", "갈등 회피력|거리 조절|감정 조절", "resource|officer", "peer|output"),
    "구설·오해 노출": _annual((0.04, 0.14, 0.28, 0.54), "guard", "말의 영향력|평판 형성|신뢰 형성", "resource|officer", "output|peer"),
    "관계 피로도": _annual((0.05, 0.15, 0.22, 0.58), "guard", "거리 조절|감정 조절|관계 유지성", "resource|officer", "peer|output"),
    "관계 정리": _annual((0.08, 0.17, 0.40, 0.35), "guard", "거리 조절|관계 유지성|자기 기준", "resource|officer|peer", "output"),
    "지인 손실 위험성": _annual((0.03, 0.11, 0.20, 0.66), "guard", "지인 손실 방어력|공동재 관리|위험 감지", "resource|officer", "peer|output"),
    "소개·연결운": _annual((0.49, 0.27, 0.18, 0.06), "activation", "지인 덕|친화성|협력성", "output|resource|peer", "officer"),

    # Love
    "연애 활성도": _annual((0.47, 0.24, 0.23, 0.06), "activation", "이성 대상 호감도|애정 표현|관계 주도성", "spouse|output", "resource"),
    "호감 유입도": _annual((0.52, 0.24, 0.18, 0.06), "activation", "이성 대상 호감도|표현 방식|친화성", "spouse|output", "resource"),
    "감정 교류 정도": _annual((0.32, 0.39, 0.20, 0.09), "activation", "애정 표현|감정 안정성|표현 방식", "output|spouse", "resource|peer"),
    "관계 진전도": _annual((0.34, 0.42, 0.17, 0.07), "activation", "관계 주도성|인연 지속성|선택 신중성", "spouse|output|officer", "peer"),
    "연애 안정성": _annual((0.12, 0.36, 0.04, 0.48), "guard", "관계 지속성|감정 안정성|이별 리스크 관리력", "resource|spouse|officer", "peer|output"),
    "갈등 회복성": _annual((0.14, 0.43, 0.08, 0.35), "guard", "갈등 회복력|감정 안정성|표현 방식", "resource|output|officer", "peer"),
    "관계 주도권 변화": _annual((0.07, 0.15, 0.42, 0.36), "guard", "관계 주도성|관계 자립성|자기 기준", "peer|officer|resource", "spouse|output"),
    "이별 위험성": _annual((0.03, 0.09, 0.25, 0.63), "guard", "이별 리스크 관리력|관계 지속성|갈등 회복력", "resource|officer", "peer|output"),
    "새로운 연애 기회": _annual((0.55, 0.21, 0.19, 0.05), "activation", "이성 대상 호감도|친화성|관계 주도성", "spouse|output|peer", "resource"),
    "소개 인연": _annual((0.49, 0.28, 0.17, 0.06), "activation", "지인 덕|이성 대상 호감도|선택 신중성", "spouse|resource|output", "peer"),
    "관계 시작 가능성": _annual((0.39, 0.43, 0.13, 0.05), "activation", "관계 주도성|애정 표현|이성 대상 호감도", "spouse|output", "resource"),
    "선택 적합도": _annual((0.14, 0.39, 0.05, 0.42), "guard", "선택 신중성|위험 감지|감정 안정성", "resource|officer|spouse", "output|peer"),
    "애정 심화 정도": _annual((0.25, 0.48, 0.10, 0.17), "activation", "인연 지속성|애정 표현|관계 지속성", "spouse|resource|output", "peer"),
    "미래 합의": _annual((0.19, 0.48, 0.08, 0.25), "guard", "결혼 시기성|결혼 안정성|재정 합의성", "spouse|officer|wealth", "peer|output"),
    "거리 발생": _annual((0.04, 0.12, 0.38, 0.46), "guard", "관계 지속성|거리 조절|이별 리스크 관리력", "resource|officer", "peer|output"),
    "외부 변수 영향": _annual((0.05, 0.13, 0.34, 0.48), "guard", "관계 지속성|갈등 회복력|거리 조절", "resource|officer", "peer|output"),

    # Marriage and household
    "결혼 인연 유입": _annual((0.47, 0.30, 0.17, 0.06), "activation", "배우자 인연|결혼 시기성|선택 신중성", "spouse|resource|officer", "peer"),
    "결혼 구체화": _annual((0.25, 0.48, 0.09, 0.18), "activation", "결혼 시기성|결혼 안정성|생활 조율성", "spouse|officer|wealth", "peer|output"),
    "결혼 결정": _annual((0.18, 0.50, 0.08, 0.24), "guard", "결혼 시기성|자기 기준|신중성", "spouse|officer|resource", "output|peer"),
    "가족 합의": _annual((0.15, 0.44, 0.06, 0.35), "guard", "가족 관계성|생활 조율성|가정 책임감", "resource|officer|wealth", "peer|output"),
    "결혼 준비 안정성": _annual((0.12, 0.38, 0.04, 0.46), "guard", "결혼 안정성|재정 합의성|생활 조율성", "resource|wealth|officer", "peer|output"),
    "결혼 지연 요인": _annual((0.04, 0.11, 0.27, 0.58), "guard", "결혼 시기성|문제 해결력|재정 합의성", "resource|officer|spouse", "peer|output"),
    "부부 관계 안정도": _annual((0.10, 0.37, 0.04, 0.49), "guard", "결혼 안정성|장기 유지성|배우자 갈등 조정력", "resource|officer|spouse", "peer|output"),
    "생활 조율": _annual((0.11, 0.40, 0.04, 0.45), "guard", "생활 조율성|가정 책임감|감정 조절", "resource|wealth|officer", "peer|output"),
    "재정 합의": _annual((0.09, 0.36, 0.03, 0.52), "guard", "재정 합의성|공동재 관리|현금 운용력", "wealth|resource|officer", "peer|output"),
    "가정 책임 분담": _annual((0.13, 0.42, 0.05, 0.40), "guard", "가정 책임감|생활 조율성|책임 감각", "resource|officer|wealth", "peer"),
    "배우자 지원": _annual((0.36, 0.37, 0.05, 0.22), "activation", "배우자 인연|결혼 후 안정도|신뢰 형성", "spouse|resource|officer", "peer"),
    "배우자 갈등": _annual((0.03, 0.10, 0.29, 0.58), "guard", "배우자 갈등 조정력|결혼 안정성|갈등 회복력", "resource|officer", "peer|output"),
    "가족 개입": _annual((0.04, 0.12, 0.26, 0.58), "guard", "가족 관계성|거리 조절|가정 책임감", "resource|officer", "peer|output"),
    "가정 환경 안정": _annual((0.10, 0.35, 0.04, 0.51), "guard", "결혼 후 안정도|생활 조율성|재정 합의성", "resource|wealth|officer", "peer|output"),

    # Honor and reputation
    "사회적 인정 상승도": _annual((0.23, 0.46, 0.10, 0.21), "activation", "사회적 인정|평판 형성|직업 성취도", "officer|output|resource", "peer"),
    "평판 상승도": _annual((0.19, 0.48, 0.07, 0.26), "guard", "평판 형성|공적 신뢰도|평가 관리력", "officer|resource|output", "peer"),
    "공적 신뢰 상승도": _annual((0.16, 0.47, 0.05, 0.32), "guard", "공적 신뢰도|책임 수용도|명분 관리", "officer|resource", "output|peer"),
    "직함 상승도": _annual((0.20, 0.48, 0.11, 0.21), "activation", "직함 상승성|권위 확보력|직책 상승성", "officer|resource|wealth", "output|peer"),
    "대외 노출도": _annual((0.42, 0.28, 0.24, 0.06), "activation", "조직 내 존재감|말의 영향력|사회적 인정", "output|officer|peer", "resource"),
    "영향력 확대": _annual((0.35, 0.36, 0.21, 0.08), "activation", "조직 내 존재감|권위 확보력|말의 영향력", "officer|output|peer", "resource"),
    "책임 증가": _annual((0.06, 0.16, 0.30, 0.48), "guard", "책임 수용도|권한 확보력|문제 해결력", "officer|resource", "output|peer"),
    "명분 확보": _annual((0.17, 0.46, 0.06, 0.31), "guard", "명분 관리|공적 신뢰도|평판 형성", "officer|resource", "output|peer"),
    "구설 위험도": _annual((0.03, 0.10, 0.26, 0.61), "guard", "평판 형성|말의 영향력|갈등 회피력", "resource|officer", "output|peer"),
    "평판 회복도": _annual((0.14, 0.45, 0.09, 0.32), "guard", "평판 형성|공적 신뢰도|문제 해결력", "resource|officer|output", "peer"),

    # Daily condition
    "생활 활력": _annual((0.34, 0.31, 0.24, 0.11), "activation", "실행 속도|문제 해결력|감정 조절", "output|peer", "resource|officer"),
    "스트레스 부담": _annual((0.04, 0.12, 0.25, 0.59), "guard", "감정 조절|거리 조절|문제 해결력", "resource|officer", "peer|output"),
    "피로 누적도": _annual((0.03, 0.11, 0.20, 0.66), "guard", "감정 조절|신중성|문제 해결력", "resource|officer", "output|peer"),
    "생활 안정성": _annual((0.10, 0.36, 0.04, 0.50), "guard", "감정 조절|책임 감각|신중성", "resource|officer", "output|peer"),
    "회복 관리": _annual((0.12, 0.43, 0.07, 0.38), "guard", "문제 해결력|감정 조절|위험 감지", "resource|output|officer", "peer"),
    "과로 노출 위험": _annual((0.03, 0.10, 0.24, 0.63), "guard", "책임 감각|문제 해결력|감정 조절", "resource|officer", "output|peer"),
    "부주의 사고 위험": _annual((0.02, 0.09, 0.27, 0.62), "guard", "위험 감지|신중성|감정 조절", "resource|officer", "output|peer"),
    "이동 피로도": _annual((0.04, 0.12, 0.39, 0.45), "guard", "변화 수용성|문제 해결력|감정 조절", "resource|officer", "output|peer"),
    "생활환경 변화 가능성": _annual((0.07, 0.14, 0.46, 0.33), "guard", "변화 수용성|자기 기준|문제 해결력", "resource|officer|peer", "output"),
    "자기관리 지속도": _annual((0.09, 0.40, 0.03, 0.48), "guard", "신중성|책임 감각|몰입 성향", "resource|officer", "output|peer"),
}


GRADE_ORDER = {"D": 0, "C": 1, "B": 2, "B+": 3, "A": 4}


def annual_contract_grade(contract: AnnualMetricContract | None) -> str:
    if contract is None:
        return "D"
    layers = 1  # annual domain flow
    layers += bool(contract.natal_labels)
    layers += bool(contract.support_groups)
    layers += bool(contract.pressure_groups)
    layers += contract.change_mode in {"activation", "guard", "neutral"}
    if layers >= 5:
        return "A"
    if layers == 4:
        return "B+"
    if layers == 3:
        return "B"
    return "C"


def _annual_contract_signature(contract: AnnualMetricContract | None) -> tuple[Any, ...]:
    if contract is None:
        return ()
    return (
        tuple(round(value, 4) for value in contract.component_weights),
        contract.change_mode,
        contract.natal_labels,
        contract.support_groups,
        contract.pressure_groups,
    )


def _annual_contract_quality_issues(contract: AnnualMetricContract | None) -> list[str]:
    if contract is None:
        return ["missing_contract"]
    issues: list[str] = []
    if abs(sum(contract.component_weights) - 1.0) > 0.001:
        issues.append("component_weight_sum")
    if max(contract.component_weights) - min(contract.component_weights) < 0.08:
        issues.append("component_weights_not_discriminating")
    if len(contract.natal_labels) < 2:
        issues.append("insufficient_natal_capacity_links")
    if not contract.support_groups:
        issues.append("missing_support_groups")
    if not contract.pressure_groups:
        issues.append("missing_pressure_groups")
    if set(contract.support_groups).intersection(contract.pressure_groups):
        issues.append("support_pressure_overlap")
    return issues


def annual_metric_contract_audit(labels: list[str]) -> dict[str, Any]:
    signature_labels: dict[tuple[Any, ...], list[str]] = {}
    for label in labels:
        signature = _annual_contract_signature(ANNUAL_METRIC_CONTRACTS.get(label))
        if signature:
            signature_labels.setdefault(signature, []).append(label)
    rows = []
    for label in labels:
        contract = ANNUAL_METRIC_CONTRACTS.get(label)
        signature = _annual_contract_signature(contract)
        rows.append({
            "label": label,
            "grade": annual_contract_grade(contract),
            "explicit": contract is not None,
            "unique_signature": len(signature_labels.get(signature, [])) == 1,
            "quality_issues": _annual_contract_quality_issues(contract),
        })
    return {
        "metrics": rows,
        "missing": [row["label"] for row in rows if not row["explicit"]],
        "below_b": [row["label"] for row in rows if GRADE_ORDER[row["grade"]] < GRADE_ORDER["B"]],
        "duplicate_contracts": [
            group for group in signature_labels.values() if len(group) > 1
        ],
        "quality_issues": {
            row["label"]: row["quality_issues"]
            for row in rows
            if row["quality_issues"]
        },
    }
