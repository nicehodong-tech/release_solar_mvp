"""Report-section selection layer.

This layer reads already-built analysis signals and chooses customer-facing
section assets. It does not recalculate the natal chart, and it does not own
the prose bank. The prose bank can grow independently from this selector and
from report rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .catalog_content import CURRENT_FORTUNE_YEAR
from .models import AnalysisResult, EventPacket, SectionSelectionJudgment, SelectedReportSection
from .section_bank import ReportSectionAsset, section_asset_for


SECTION_SELECTION_VERSION = "section_selection_v1"


@dataclass(frozen=True)
class _SectionPrototype:
    section_key: str
    priority: int
    scorer: Callable[["_SelectionContext"], tuple[int, list[str], list[str]]]


@dataclass(frozen=True)
class SectionSelectionResult:
    judgments: list[SectionSelectionJudgment]
    selected_sections: list[SelectedReportSection]
    suppressed_sections: list[SelectedReportSection]


class _SelectionContext:
    def __init__(self, analysis: AnalysisResult) -> None:
        self.analysis = analysis
        self.structure = analysis.chart_structure
        self.packets = list(analysis.event_packets)
        self.codes = _all_codes(self.packets)

    def group(self, key: str) -> float:
        return float(self.structure.ten_god_profile.group_scores.get(key, 0.0))

    def best_packet(self, domain: str) -> EventPacket | None:
        packets = [packet for packet in self.packets if packet.domain == domain]
        if not packets:
            return None
        return max(
            packets,
            key=lambda packet: (
                packet.event_probability_score,
                packet.opportunity_score,
                packet.change_score,
                -packet.risk_score,
            ),
        )

    def packets_for_domain(self, domain: str) -> list[EventPacket]:
        return [packet for packet in self.packets if packet.domain == domain]

    def feature_axis_score(self, axis_key: str) -> int:
        scores: list[int] = []
        for packet in self.packets:
            for axis in packet.feature_axes:
                if axis.get("key") == axis_key:
                    value = axis.get("score")
                    if isinstance(value, int) and not isinstance(value, bool):
                        scores.append(value)
        return max(scores, default=0)

    def has_code(self, *needles: str) -> bool:
        return any(any(needle in code for needle in needles) for code in self.codes)

    def branch_relation_count(self, *relation_types: str) -> int:
        wanted = set(relation_types)
        natal_count = sum(
            1
            for relation in self.structure.branch_interactions
            if relation.relation_type in wanted
        )
        flow_count = sum(
            1
            for flow in self.analysis.flow_signals
            for relation in flow.branch_interactions
            if relation.relation_type in wanted
        )
        return natal_count + flow_count


def build_section_selection(analysis: AnalysisResult, *, limit: int = 5) -> SectionSelectionResult:
    """Choose customer report sections from already-built analysis signals."""

    context = _SelectionContext(analysis)
    judgments = _build_judgments(context)
    candidates: list[SelectedReportSection] = []

    for prototype in _SECTION_PROTOTYPES:
        asset = section_asset_for(prototype.section_key)
        if asset is None:
            continue

        score, trigger_codes, judgment_keys = prototype.scorer(context)
        if score < 52:
            continue

        age_timing_sentences = _build_age_timing_sentences(asset, context)
        annual_sentences = _build_annual_sentences(asset, context)
        candidates.append(
            SelectedReportSection(
                section_key=prototype.section_key,
                title=asset.title,
                domain=asset.domain,
                narrative_group=asset.narrative_group,
                score=score,
                priority=prototype.priority,
                paragraphs=list(asset.opening) + list(asset.main_body),
                compressed_summary=" ".join(asset.compressed_summary),
                trigger_codes=list(dict.fromkeys(trigger_codes)),
                judgment_keys=list(dict.fromkeys(judgment_keys)),
                source_key=asset.source_key,
                age_timing_sentences=age_timing_sentences,
                annual_sentences=annual_sentences,
                wording_notes=list(asset.wording_notes),
            )
        )

    selected, suppressed = _dedupe_by_narrative(candidates, limit)
    return SectionSelectionResult(
        judgments=judgments,
        selected_sections=selected,
        suppressed_sections=suppressed,
    )


def _all_codes(packets: list[EventPacket]) -> list[str]:
    codes: list[str] = []
    for packet in packets:
        codes.extend(packet.basis_codes)
        codes.extend(packet.counter_signals)
        codes.extend(packet.event_keywords)
        codes.append(packet.sub_event_type)
        codes.append(packet.risk_topic)
        codes.append(packet.main_action)
    return [code for code in dict.fromkeys(str(code) for code in codes) if code]


def _build_age_timing_sentences(asset: ReportSectionAsset, context: _SelectionContext) -> list[str]:
    periods = _top_periods_for_asset(asset, context, limit=3)
    if not periods:
        return []

    ages = _age_label([age for _, age, _ in periods if age is not None])
    years = _year_label([year for year, _, _ in periods])
    if not ages:
        ages = f"{years} 무렵"

    if asset.section_key == "created_output_becomes_money":
        return [
            f"한국 나이 {ages} 전후에는 직접 만든 결과물이 수입으로 바뀌는 일이 강해집니다.",
            "이 시기에는 실력만 갖고 있는 것보다, 실제로 팔 수 있는 상품이나 서비스를 분명히 내놓아야 돈이 됩니다.",
        ]
    if asset.section_key == "money_not_stay":
        return [
            f"한국 나이 {ages} 전후에는 돈이 들어와도 곧 나갈 곳이 함께 생깁니다.",
            "이 시기에는 버는 금액보다 남기는 금액이 실제 재물운으로 드러납니다.",
        ]
    if asset.section_key == "close_people_money_mix":
        return [
            f"한국 나이 {ages} 전후에는 가까운 사람과 수익, 비용, 역할이 얽히기 쉽습니다.",
            "이 시기에는 동업, 공동 비용, 가족 지출처럼 사람과 돈이 함께 움직이는 일을 더 엄밀히 봐야 합니다.",
        ]
    if asset.section_key == "practical_problem_solver":
        return [
            f"한국 나이 {ages} 전후에는 말보다 실제로 처리해본 일이 직업운의 중심으로 올라옵니다.",
            "이 시기에는 해본 일, 맡아본 일, 끝까지 끝낸 일이 평가와 기회로 이어집니다.",
        ]
    if asset.section_key == "responsibility_without_authority":
        return [
            f"한국 나이 {ages} 전후에는 맡는 일이 늘고, 책임의 범위가 넓어지기 쉽습니다.",
            "이 시기에는 직함보다 실제 결정권과 보고선을 먼저 확인해야 직업운이 안정됩니다.",
        ]
    return [f"한국 나이 {ages} 전후에는 {asset.title}의 성격이 더 분명하게 드러납니다."]


def _build_annual_sentences(asset: ReportSectionAsset, context: _SelectionContext) -> dict[int, list[str]]:
    packet = _best_packet_for_year(asset, context, CURRENT_FORTUNE_YEAR)
    if packet is None:
        return {}

    year = CURRENT_FORTUNE_YEAR
    if asset.section_key == "created_output_becomes_money":
        sentences = [
            f"{year}년에는 만든 결과물을 사람 앞에 꺼내는 일이 재물운의 핵심으로 뜹니다.",
            "기술, 서비스, 콘텐츠처럼 이미 손에 잡힌 것이 있다면 가격을 붙이고 판매 자리로 가져가야 합니다.",
        ]
    elif asset.section_key == "money_not_stay":
        sentences = [
            f"{year}년에는 수입이 생겨도 곧 나갈 곳이 같이 드러납니다.",
            "생활비, 고정비, 일에 들어가는 비용을 먼저 나누어야 손에 남는 돈이 생깁니다.",
        ]
    elif asset.section_key == "close_people_money_mix":
        sentences = [
            f"{year}년에는 사람을 통해 돈 이야기가 들어올 수 있습니다.",
            "좋은 제안처럼 보여도 정산 방식과 책임 범위는 처음부터 분명히 해야 합니다.",
        ]
    elif asset.section_key == "practical_problem_solver":
        sentences = [
            f"{year}년에는 숨어 있던 실무 능력을 밖으로 보여줄 일이 생깁니다.",
            "말로 설명하는 것보다 직접 처리한 결과를 보여주는 쪽이 유리합니다.",
        ]
    elif asset.section_key == "responsibility_without_authority":
        sentences = [
            f"{year}년에는 맡은 일이 밖으로 드러나고 평가받는 일이 많아질 수 있습니다.",
            "맡는 일이 늘어날수록 보고선, 결정권, 책임 범위를 먼저 확인해야 합니다.",
        ]
    else:
        sentences = [
            f"{year}년에는 {asset.title}의 성격이 실제 생활에서 더 분명하게 나타납니다.",
        ]
    return {year: sentences}


def _top_periods_for_asset(
    asset: ReportSectionAsset,
    context: _SelectionContext,
    *,
    limit: int,
) -> list[tuple[int, int | None, EventPacket]]:
    birth_year = _birth_year(context)
    packets = sorted(
        context.packets_for_domain(asset.domain),
        key=lambda packet: (
            packet.event_probability_score,
            packet.opportunity_score,
            packet.risk_score,
            packet.change_score,
        ),
        reverse=True,
    )
    periods: list[tuple[int, int | None, EventPacket]] = []
    used_years: set[int] = set()
    for packet in packets:
        packet_year = _packet_year(packet)
        if packet_year is None or packet_year in used_years:
            continue
        used_years.add(packet_year)
        age = packet_year - birth_year + 1 if birth_year is not None else None
        periods.append((packet_year, age, packet))
        if len(periods) >= limit:
            break
    return sorted(periods, key=lambda item: item[0])


def _best_packet_for_year(
    asset: ReportSectionAsset,
    context: _SelectionContext,
    year: int,
) -> EventPacket | None:
    packets = [packet for packet in context.packets_for_domain(asset.domain) if _packet_year(packet) == year]
    if not packets:
        return None
    return max(
        packets,
        key=lambda packet: (
            packet.event_probability_score,
            packet.opportunity_score,
            packet.risk_score,
            packet.change_score,
        ),
    )


def _packet_year(packet: EventPacket) -> int | None:
    label = str(packet.period_label)
    if label.isdigit():
        return int(label)
    return None


def _birth_year(context: _SelectionContext) -> int | None:
    value = context.analysis.trace.get("birth_year")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _age_label(ages: list[int]) -> str:
    unique = sorted({age for age in ages if isinstance(age, int)})
    if not unique:
        return ""
    if len(unique) == 1:
        return f"{unique[0]}세"
    if unique[-1] - unique[0] == len(unique) - 1:
        return f"{unique[0]}~{unique[-1]}세"
    return ", ".join(f"{age}세" for age in unique)


def _year_label(years: list[int]) -> str:
    unique = sorted({year for year in years if isinstance(year, int)})
    if not unique:
        return ""
    if len(unique) == 1:
        return f"{unique[0]}년"
    if unique[-1] - unique[0] == len(unique) - 1:
        return f"{unique[0]}~{unique[-1]}년"
    return ", ".join(f"{year}년" for year in unique)


def _build_judgments(context: _SelectionContext) -> list[SectionSelectionJudgment]:
    element_profile = context.structure.element_profile
    pattern_profile = context.structure.pattern_profile
    money_packet = context.best_packet("money")
    career_packet = context.best_packet("career")

    return [
        SectionSelectionJudgment(
            key="day_master",
            label="일간",
            value=context.structure.day_master_stem,
            score=100,
            basis_codes=["chart_day_master"],
        ),
        SectionSelectionJudgment(
            key="month_command",
            label="월령",
            value=f"{context.structure.month_branch}:{pattern_profile.month_command_ten_god}",
            score=100,
            basis_codes=["pattern_month_command"],
        ),
        SectionSelectionJudgment(
            key="day_master_strength",
            label="일간 강약",
            value=element_profile.day_master_strength,
            score=element_profile.day_master_strength_score,
            basis_codes=["element_day_master_strength"],
        ),
        SectionSelectionJudgment(
            key="wealth_presence",
            label="재성 작용",
            value=_level_label(context.group("wealth")),
            score=_clip(
                context.group("wealth") * 9
                + (money_packet.opportunity_score if money_packet else 0) * 0.35
            ),
            basis_codes=_matching_codes(context.codes, "wealth", "jae", "money", "income", "contract"),
        ),
        SectionSelectionJudgment(
            key="peer_wealth_contact",
            label="사람과 돈의 접점",
            value=_level_label(context.group("peer"), context.group("wealth")),
            score=_clip(
                context.group("peer") * 10
                + context.group("wealth") * 8
                + _code_bonus(context, "peer_wealth", "geob_jae", "bi_gyeon")
            ),
            basis_codes=_matching_codes(context.codes, "peer_wealth", "geob_jae", "bi_gyeon", "competition"),
        ),
        SectionSelectionJudgment(
            key="output_to_wealth",
            label="결과물과 수입의 연결",
            value=_level_label(context.group("output"), context.group("wealth")),
            score=_clip(
                context.group("output") * 11
                + context.group("wealth") * 8
                + _code_bonus(context, "output", "sik_sin", "sang_gwan", "income")
            ),
            basis_codes=_matching_codes(context.codes, "output", "sik_sin", "sang_gwan", "income", "result"),
        ),
        SectionSelectionJudgment(
            key="money_retention_pressure",
            label="돈을 남기는 압력",
            value=_retention_label(context),
            score=_money_retention_pressure_score(context),
            basis_codes=_matching_codes(context.codes, "cashflow", "asset_retention", "spending", "counter"),
            counter_signals=_matching_codes(context.codes, "cashflow_defense", "risk", "counter", "spending"),
        ),
        SectionSelectionJudgment(
            key="practical_output_under_pressure",
            label="어려운 일을 처리하는 실무력",
            value=_level_label(context.group("output"), context.group("officer")),
            score=_clip(
                context.group("output") * 10
                + context.group("officer") * 8
                + _code_bonus(context, "pyeon_gwan", "sik_sin", "responsibility", "operation")
            ),
            basis_codes=_matching_codes(context.codes, "pyeon_gwan", "sik_sin", "responsibility", "operation"),
        ),
        SectionSelectionJudgment(
            key="authority_responsibility_gap",
            label="책임과 결정권의 간격",
            value=_authority_gap_label(context),
            score=_authority_gap_score(context, career_packet),
            basis_codes=_matching_codes(context.codes, "responsibility_pressure", "officer", "authority"),
            counter_signals=_matching_codes(context.codes, "authority_gap", "responsibility_pressure", "counter"),
        ),
    ]


def _dedupe_by_narrative(
    candidates: list[SelectedReportSection],
    limit: int,
) -> tuple[list[SelectedReportSection], list[SelectedReportSection]]:
    ordered = sorted(candidates, key=lambda item: (-item.score, item.priority, item.section_key))
    selected: list[SelectedReportSection] = []
    suppressed: list[SelectedReportSection] = []
    used_groups: dict[str, str] = {}
    for candidate in ordered:
        if candidate.narrative_group in used_groups:
            suppressed.append(
                SelectedReportSection(
                    section_key=candidate.section_key,
                    title=candidate.title,
                    domain=candidate.domain,
                    narrative_group=candidate.narrative_group,
                    score=candidate.score,
                    priority=candidate.priority,
                    paragraphs=list(candidate.paragraphs),
                    compressed_summary=candidate.compressed_summary,
                    trigger_codes=list(candidate.trigger_codes),
                    judgment_keys=list(candidate.judgment_keys),
                    suppressed_by=used_groups[candidate.narrative_group],
                    source_key=candidate.source_key,
                    age_timing_sentences=list(candidate.age_timing_sentences),
                    annual_sentences={
                        year: list(sentences)
                        for year, sentences in candidate.annual_sentences.items()
                    },
                    wording_notes=list(candidate.wording_notes),
                )
            )
            continue
        selected.append(candidate)
        used_groups[candidate.narrative_group] = candidate.section_key
        if len(selected) >= limit:
            break
    return selected, suppressed


def _clip(value: float) -> int:
    return max(0, min(100, round(value)))


def _level_label(*values: float) -> str:
    score = max(values, default=0.0)
    if score >= 7:
        return "강하게 드러남"
    if score >= 4:
        return "분명하게 작용함"
    if score >= 2:
        return "보조적으로 작용함"
    return "약하게 작용함"


def _retention_label(context: _SelectionContext) -> str:
    asset_retention = context.feature_axis_score("asset_retention")
    spending_control = context.feature_axis_score("spending_control")
    if min(asset_retention or 100, spending_control or 100) < 45:
        return "수입 뒤의 정리가 약함"
    if context.group("peer") >= 5 and context.group("wealth") >= 4:
        return "분배와 정산이 중요함"
    return "관리하면 남는 돈이 있음"


def _authority_gap_label(context: _SelectionContext) -> str:
    responsibility = context.feature_axis_score("responsibility_capacity")
    organization = context.feature_axis_score("organization_adaptability")
    if responsibility and organization and responsibility < 50 <= organization:
        return "조직 안에서 책임 부담이 커짐"
    if context.has_code("responsibility_pressure", "authority_gap"):
        return "책임과 권한이 엇갈림"
    return "역할 기준 확인 필요"


def _code_bonus(context: _SelectionContext, *needles: str) -> int:
    return min(24, sum(4 for code in context.codes if any(needle in code for needle in needles)))


def _matching_codes(codes: list[str], *needles: str, limit: int = 8) -> list[str]:
    matched = [code for code in codes if any(needle in code for needle in needles)]
    return list(dict.fromkeys(matched))[:limit]


def _money_retention_pressure_score(context: _SelectionContext) -> int:
    money_packets = context.packets_for_domain("money")
    risk = max((packet.risk_score for packet in money_packets), default=0)
    asset_retention = context.feature_axis_score("asset_retention")
    spending_control = context.feature_axis_score("spending_control")
    weak_retention = 0
    if asset_retention and asset_retention < 50:
        weak_retention += 12
    if spending_control and spending_control < 50:
        weak_retention += 12
    if context.structure.element_profile.day_master_strength in {"weak", "very_weak"} and context.group("wealth") >= 3:
        weak_retention += 12
    return _clip(
        risk * 0.62
        + weak_retention
        + context.group("wealth") * 4
        + _code_bonus(context, "cashflow", "spending", "asset_retention")
    )


def _authority_gap_score(context: _SelectionContext, career_packet: EventPacket | None) -> int:
    risk = career_packet.risk_score if career_packet else 0
    responsibility = context.feature_axis_score("responsibility_capacity")
    authority_signal = 12 if context.has_code("responsibility_pressure", "authority_gap") else 0
    weak_base = 8 if responsibility and responsibility < 52 else 0
    return _clip(risk * 0.62 + context.group("officer") * 8 + authority_signal + weak_base)


def _score_money_not_stay(context: _SelectionContext) -> tuple[int, list[str], list[str]]:
    score = _money_retention_pressure_score(context)
    return (
        score,
        _matching_codes(context.codes, "cashflow", "spending", "asset_retention"),
        ["wealth_presence", "money_retention_pressure", "day_master_strength"],
    )


def _score_output_to_money(context: _SelectionContext) -> tuple[int, list[str], list[str]]:
    money_packet = context.best_packet("money")
    score = _clip(
        context.group("output") * 12
        + context.group("wealth") * 9
        + (money_packet.opportunity_score if money_packet else 0) * 0.28
        + _code_bonus(context, "sik_sin", "sang_gwan", "income_growth", "result")
    )
    return (
        score,
        _matching_codes(context.codes, "sik_sin", "sang_gwan", "income_growth", "result"),
        ["output_to_wealth", "wealth_presence"],
    )


def _score_people_money_mix(context: _SelectionContext) -> tuple[int, list[str], list[str]]:
    peer_score = context.group("peer")
    wealth_score = context.group("wealth")
    contact_base = min(peer_score, wealth_score) * 18
    explicit_bonus = _code_bonus(context, "peer_wealth", "geob_jae", "bi_gyeon", "competition")
    branch_noise = min(context.branch_relation_count("clash", "punishment", "harm", "break"), 4) * 2
    score = _clip(
        contact_base
        + peer_score * 4
        + wealth_score * 3
        + explicit_bonus
        + branch_noise
    )
    if peer_score < 2.5 or wealth_score < 2.5:
        score = max(0, score - 24)
    return (
        score,
        _matching_codes(context.codes, "peer_wealth", "geob_jae", "bi_gyeon", "competition"),
        ["peer_wealth_contact", "wealth_presence", "money_retention_pressure"],
    )


def _score_practical_problem_solving(context: _SelectionContext) -> tuple[int, list[str], list[str]]:
    career_packet = context.best_packet("career")
    score = _clip(
        context.group("output") * 11
        + context.group("officer") * 8
        + (career_packet.change_score if career_packet else 0) * 0.18
        + _code_bonus(context, "sik_sin", "pyeon_gwan", "operation", "responsibility")
    )
    return (
        score,
        _matching_codes(context.codes, "sik_sin", "pyeon_gwan", "operation", "responsibility"),
        ["practical_output_under_pressure", "authority_responsibility_gap"],
    )


def _score_responsibility_without_authority(context: _SelectionContext) -> tuple[int, list[str], list[str]]:
    career_packet = context.best_packet("career")
    score = _authority_gap_score(context, career_packet)
    return (
        score,
        _matching_codes(context.codes, "responsibility_pressure", "authority", "officer"),
        ["authority_responsibility_gap", "day_master_strength"],
    )


_SECTION_PROTOTYPES = (
    _SectionPrototype(
        section_key="money_not_stay",
        priority=10,
        scorer=_score_money_not_stay,
    ),
    _SectionPrototype(
        section_key="created_output_becomes_money",
        priority=20,
        scorer=_score_output_to_money,
    ),
    _SectionPrototype(
        section_key="close_people_money_mix",
        priority=15,
        scorer=_score_people_money_mix,
    ),
    _SectionPrototype(
        section_key="practical_problem_solver",
        priority=30,
        scorer=_score_practical_problem_solving,
    ),
    _SectionPrototype(
        section_key="responsibility_without_authority",
        priority=25,
        scorer=_score_responsibility_without_authority,
    ),
)
