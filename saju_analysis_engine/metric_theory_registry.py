"""Theory contracts for customer-facing metric adjudication.

This module does not alter scores by itself.  It fixes the theoretical evidence
that each public metric must be able to consume before the scoring layer is
expanded.  The registry is deliberately separate from prose and UI code so a
metric cannot gain authority merely because it has a persuasive description.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TheoryStatus = Literal["active", "partial", "support_only", "planned"]
SemanticAxis = Literal["quality", "managed_risk", "magnitude"]


METRIC_THEORY_REGISTRY_VERSION = "metric_theory_registry_v4_relation_two_axis"


REQUIRED_KEYWORD_ASSETS = (
    "오행_핵심어사전_v1.md",
    "10천간_핵심어사전_v1.md",
    "12지지_핵심어사전_v1.md",
    "지장간_핵심어사전_v1.md",
    "오행배합_핵심어사전_v1.md",
    "10천간배합_핵심어사전_v1.md",
    "십신_핵심어사전_v1_1.md",
    "십신배합_핵심어사전_v1.md",
    "12지지배합_핵심어사전_v1.md",
    "지지관계_핵심어사전_v1.md",
    "합충형파해_핵심어사전_v1.md",
    "신살_잡설_핵심어사전_v1.md",
    "60일주_핵심키워드_v1.md",
    "12월지_보정핵심키워드_v1.md",
    "월령_핵심어사전_v1.md",
    "격국_핵심어사전_v1.md",
)


@dataclass(frozen=True)
class MetricTheoryLayer:
    key: str
    label: str
    family: str
    priority: int
    status: TheoryStatus
    scoring_role: str
    engine_fields: tuple[str, ...]
    source_modules: tuple[str, ...]
    source_assets: tuple[str, ...]
    adjudication_questions: tuple[str, ...]
    anti_double_count_group: str


@dataclass(frozen=True)
class MetricTheoryRequirement:
    metric_key: str
    label: str
    domain: str
    semantic_axis: SemanticAxis
    primary_layers: tuple[str, ...]
    confirming_layers: tuple[str, ...]
    pressure_layers: tuple[str, ...]
    required_positions: tuple[str, ...]
    classical_chains: tuple[str, ...]
    minimum_independent_families: int
    prohibited_shortcuts: tuple[str, ...]


def _layer(
    key: str,
    label: str,
    family: str,
    priority: int,
    status: TheoryStatus,
    scoring_role: str,
    fields: str,
    modules: str,
    assets: str,
    questions: tuple[str, ...],
    dedupe: str,
) -> MetricTheoryLayer:
    split = lambda value: tuple(item for item in value.split() if item)
    return MetricTheoryLayer(
        key=key,
        label=label,
        family=family,
        priority=priority,
        status=status,
        scoring_role=scoring_role,
        engine_fields=split(fields),
        source_modules=split(modules),
        source_assets=tuple(item for item in assets.split("|") if item),
        adjudication_questions=questions,
        anti_double_count_group=dedupe,
    )


METRIC_THEORY_LAYERS: dict[str, MetricTheoryLayer] = {
    "month_environment": _layer(
        "month_environment", "월령 환경과 당령", "month", 1, "active", "gate",
        "month_branch season_label month_governance_profile",
        "month_governance.py structure.py",
        "월령_핵심어사전_v1.md|12월지_보정핵심키워드_v1.md|월령.pdf",
        ("월지가 요구하는 사회적 기능은 무엇인가?", "해당 지표의 기능이 월령에서 쓸모를 얻는가?"),
        "month_authority",
    ),
    "month_hidden_phase": _layer(
        "month_hidden_phase", "월률분야와 실제 사령", "month", 1, "active", "gate",
        "month_governance_profile.month_hidden_phase gyeokguk_profile.active_hidden_stem",
        "month_hidden_phase.py month_governance.py gyeokguk.py",
        "월령_핵심어사전_v1.md|지장간_핵심어사전_v1.md|지지의 지장간과 월률분야 표.pdf",
        ("절입 뒤 실제로 당번을 맡은 지장간은 무엇인가?", "본기와 사령이 다를 때 어느 기능을 우선하는가?"),
        "month_authority",
    ),
    "seasonal_element_strength": _layer(
        "seasonal_element_strength", "오행의 계절 왕쇠", "element", 1, "active", "gate",
        "element_profile.scores.*.seasonal_score element_profile.scores.*.state",
        "elements.py",
        "오행_핵심어사전_v1.md|오행의 특성과 오행의 배합 정리.pdf",
        ("해당 오행이 계절의 도움을 받는가?", "수량은 있어도 계절상 실제 작용력이 약한가?"),
        "element_state",
    ),
    "day_master_capacity": _layer(
        "day_master_capacity", "일간의 감당력", "capacity", 1, "partial", "gate",
        "element_profile.day_master_strength_score element_profile.day_master_strength position_signals",
        "elements.py features.py expert_adjudication.py",
        "오행_핵심어사전_v1.md|일간별 오행에 대응하는 십신.pdf|사주명리 집대성.pdf",
        ("일간이 재·관·식상의 결과와 부담을 감당하는가?", "신강·신약을 기계적인 길흉으로 오용하지 않았는가?"),
        "day_master_capacity",
    ),
    "climate_temperature": _layer(
        "climate_temperature", "조후의 한난", "climate", 1, "active", "gate",
        "element_profile.temperature_balance element_profile.climate_needs",
        "elements.py expert_adjudication.py",
        "월령_핵심어사전_v1.md|궁통보감 정리본.pdf",
        ("한난의 치우침이 기능 발휘를 막는가?", "필요한 온도 조건을 실제 오행이 충족하는가?"),
        "climate_balance",
    ),
    "climate_moisture": _layer(
        "climate_moisture", "조후의 조습", "climate", 1, "active", "gate",
        "element_profile.moisture_balance element_profile.climate_needs",
        "elements.py expert_adjudication.py",
        "월령_핵심어사전_v1.md|궁통보감 정리본.pdf",
        ("조습의 치우침이 순환과 생산을 막는가?", "필요한 수분 조건을 실제 오행이 충족하는가?"),
        "climate_balance",
    ),
    "illness_medicine": _layer(
        "illness_medicine", "병약과 복구", "climate", 2, "active", "conditional",
        "element_profile.illness_medicine gyeokguk_profile.*.disease_medicine_logic",
        "elements.py gyeokguk_dual_ten_god_actions.py",
        "병약론 정리.pdf|격국_핵심어사전_v1.md",
        ("구조의 병은 무엇인가?", "약이 실제로 존재하고 뿌리와 작용력을 갖추었는가?"),
        "disease_medicine",
    ),
    "element_distribution": _layer(
        "element_distribution", "오행 분포", "element", 2, "active", "base",
        "element_profile.scores.*.raw_score element_profile.scores.*.ratio",
        "elements.py",
        "오행_핵심어사전_v1.md",
        ("어느 오행이 많고 적은가?", "개수와 작용력을 구별했는가?"),
        "element_state",
    ),
    "element_quality": _layer(
        "element_quality", "오행의 질과 현실성", "element", 1, "active", "base",
        "element_profile.scores.*.exposure element_profile.scores.*.root_count element_profile.scores.*.visible_count",
        "elements.py",
        "오행_핵심어사전_v1.md|오행의 특성과 오행의 배합 정리.pdf",
        ("오행이 드러나고 뿌리를 두었는가?", "강한 오행이 이 지표에 유용한가 부담인가?"),
        "element_state",
    ),
    "element_circulation": _layer(
        "element_circulation", "오행 순환과 통관", "element", 1, "active", "chain",
        "element_profile.circulation_level element_profile.circulation_notes cycle_regulation_profile",
        "elements.py cycle_regulation.py",
        "오행배합_핵심어사전_v1.md|오행의 특성과 오행의 배합 정리.pdf",
        ("생극이 막히지 않고 다음 기능으로 이어지는가?", "과도한 생·극을 통관하는 오행이 있는가?"),
        "element_chain",
    ),
    "element_combinations": _layer(
        "element_combinations", "오행 배합", "element", 1, "active", "chain",
        "element_combination_profile",
        "element_combinations.py",
        "오행배합_핵심어사전_v1.md",
        ("두세 오행의 배합이 어떤 기능을 생산하는가?", "같은 오행 조합이라도 순서·월령·일간에 따라 달라지는가?"),
        "element_chain",
    ),
    "yin_yang_balance": _layer(
        "yin_yang_balance", "음양의 발현 방식", "element", 3, "partial", "conditional",
        "day_master_yin_yang four_pillars",
        "structure.py constants.py",
        "10천간_핵심어사전_v1.md|일간별 오행에 대응하는 십신.pdf",
        ("같은 오행 기능이 양적으로 직진하는가 음적으로 조절되는가?", "음양을 좋고 나쁨으로 단정하지 않았는가?"),
        "yin_yang",
    ),
    "visible_stems": _layer(
        "visible_stems", "천간 투출과 표면 작용", "visibility", 1, "active", "reality",
        "four_pillars position_signals combination_profile.heavenly_stem_signals",
        "structure.py combinations.py",
        "10천간_핵심어사전_v1.md|10천간배합_핵심어사전_v1.md",
        ("외부에서 직접 확인되는 기능인가?", "어느 궁위에서 사회적 행동으로 드러나는가?"),
        "visibility_reality",
    ),
    "hidden_stems": _layer(
        "hidden_stems", "지장간의 잠재 작용", "visibility", 1, "active", "reality",
        "ten_god_profile.hidden_counts position_signals.*.hidden_ten_gods",
        "ten_gods.py structure.py",
        "지장간_핵심어사전_v1.md|지지의 지장간과 월률분야 표.pdf",
        ("기능이 지지 내부에 잠재해 있는가?", "투출·운의 발동 전에는 어느 정도만 인정할 것인가?"),
        "visibility_reality",
    ),
    "protrusion_rooting": _layer(
        "protrusion_rooting", "투출·통근·무근", "visibility", 1, "active", "reality",
        "position_signals.*.protruded_hidden_stems gyeokguk_profile.candidates.*.rooted stem_reception_profile",
        "structure.py gyeokguk.py stem_receptions.py",
        "십신_핵심어사전_v1_1.md|지장간_핵심어사전_v1.md|위치에 따른 십신의 해석.pdf",
        ("드러난 기능이 실제 뿌리를 가졌는가?", "숨은 기능이 투출되어 현실 사건으로 이어지는가?"),
        "visibility_reality",
    ),
    "stem_combinations": _layer(
        "stem_combinations", "천간 배합과 합극", "relation", 1, "active", "chain",
        "combination_profile.heavenly_stem_signals combination_profile.stem_branch_signals",
        "combinations.py",
        "10천간배합_핵심어사전_v1.md",
        ("천간끼리 생·극·합하며 어떤 기능을 만드는가?", "합이 묶음인지 변화인지 조건을 확인했는가?"),
        "stem_pair",
    ),
    "stem_transformation": _layer(
        "stem_transformation", "천간합화의 성립 조건", "relation", 2, "active", "conditional",
        "combination_profile.heavenly_stem_signals cycle_regulation_profile",
        "combinations.py cycle_regulation.py",
        "10천간배합_핵심어사전_v1.md|오행배합_핵심어사전_v1.md",
        ("천간합이 결박·유정에 머무는가 실제 합화하는가?", "월령·화신·방해 조건 없이 합화를 선언하지 않았는가?"),
        "stem_pair",
    ),
    "stem_reception": _layer(
        "stem_reception", "일간의 천간 수용", "relation", 1, "active", "chain",
        "stem_reception_profile",
        "stem_receptions.py",
        "10천간배합_핵심어사전_v1.md|일간별 오행에 대응하는 십신.pdf",
        ("일간이 상대 천간의 기능을 어떻게 받아들이는가?", "계절·지지 관계가 수용력을 보정하는가?"),
        "stem_pair",
    ),
    "directional_interactions": _layer(
        "directional_interactions", "천간·지장간 작용의 방향", "relation", 1, "active", "chain",
        "directional_interaction_profile",
        "directional_interactions.py",
        "10천간배합_핵심어사전_v1.md|오행배합_핵심어사전_v1.md",
        ("누가 누구를 생·극하여 작용의 주체와 대상이 되는가?", "같은 두 글자의 순서를 뒤집어 같은 결과로 처리하지 않았는가?"),
        "directional_pair",
    ),
    "branch_pairs": _layer(
        "branch_pairs", "모든 지지 쌍의 현실 배합", "relation", 1, "active", "reality",
        "branch_pair_combinations",
        "interactions.py branch_reality_profiles.py",
        "12지지배합_핵심어사전_v1.md|12지지_핵심어사전_v1.md",
        ("합충형파해가 아니어도 두 지지가 어떤 현실 조건을 만드는가?", "궁위 간 생활 장면이 무엇인가?"),
        "branch_pair",
    ),
    "formal_branch_relations": _layer(
        "formal_branch_relations", "합충형파해와 방합·삼합", "relation", 1, "active", "pressure_or_support",
        "branch_interactions branch_pair_combinations.*.formal_relation_types",
        "interactions.py relation_polarity.py",
        "지지관계_핵심어사전_v1.md|합충형파해_핵심어사전_v1.md",
        ("관계가 묶고 움직이고 압박하고 손상하는 방식은 무엇인가?", "필요한 구조의 충과 불필요한 구조의 충을 구별했는가?"),
        "branch_pair",
    ),
    "branch_transformation": _layer(
        "branch_transformation", "합국의 성립과 불성립", "relation", 2, "partial", "conditional",
        "branch_interactions.*.effect_element element_profile",
        "interactions.py relation_polarity.py",
        "지지관계_핵심어사전_v1.md|합충형파해_핵심어사전_v1.md",
        ("합국이 계절·투간·방해 조건을 얻어 실제로 성립하는가?", "형식적 조합을 곧바로 변한 오행으로 계산하지 않았는가?"),
        "branch_pair",
    ),
    "storage_opening": _layer(
        "storage_opening", "진술축미의 고장과 개고", "relation", 3, "planned", "conditional",
        "branch_pair_combinations branch_interactions",
        "interactions.py",
        "12지지_핵심어사전_v1.md|지장간_핵심어사전_v1.md|사주명리 집대성.pdf",
        ("묘고 속 기능이 저장되는가 열리는가?", "충을 무조건 개고로 처리하지 않았는가?"),
        "branch_storage",
    ),
    "position_palaces": _layer(
        "position_palaces", "년·월·일·시의 궁위", "position", 1, "active", "reality",
        "position_signals",
        "structure.py",
        "위치에 따른 십신의 해석.pdf|십신_핵심어사전_v1_1.md",
        ("같은 기능이 어느 생활 영역에서 현실화되는가?", "월주는 사회·직업, 일주는 자기·배우자, 시주는 결과·후반으로 구별했는가?"),
        "position",
    ),
    "life_stage_positions": _layer(
        "life_stage_positions", "궁위별 생애 단계", "position", 2, "active", "conditional",
        "position_signals.*.age_scope position_signals.*.life_stage",
        "structure.py",
        "위치에 따른 십신의 해석.pdf|태어난 시간에 따른 시주.pdf",
        ("초·중·후반의 발현 시점을 궁위와 혼동하지 않았는가?", "시주 부재 시 후반 판단의 확신을 낮추는가?"),
        "position",
    ),
    "exact_ten_gods": _layer(
        "exact_ten_gods", "정·편을 구분한 십신", "ten_god", 1, "active", "base",
        "ten_god_profile.visible_counts ten_god_profile.hidden_counts position_signals",
        "ten_gods.py",
        "십신_핵심어사전_v1_1.md|십신의 특성과 배합.pdf",
        ("정재와 편재, 정관과 편관처럼 기능 차이를 보존했는가?", "같은 십신도 위치·투출·월령에 따라 다르게 보았는가?"),
        "ten_god_presence",
    ),
    "ten_god_groups": _layer(
        "ten_god_groups", "십신 오대 기능군", "ten_god", 2, "active", "base",
        "ten_god_profile.group_scores",
        "ten_gods.py",
        "십신_핵심어사전_v1_1.md",
        ("비겁·식상·재성·관성·인성의 대략적 자원량은 어떠한가?", "기능군 수량을 최종 결론으로 오용하지 않았는가?"),
        "ten_god_presence",
    ),
    "ten_god_interactions": _layer(
        "ten_god_interactions", "십신 상호작용과 방향", "ten_god", 1, "active", "chain",
        "ten_god_interaction_profile",
        "ten_god_interactions.py directional_interactions.py",
        "십신배합_핵심어사전_v1.md|십신의 특성과 배합.pdf",
        ("어느 십신이 어느 십신을 생·극하는가?", "순서와 방향에 따라 현실 결과가 달라지는가?"),
        "ten_god_chain",
    ),
    "pattern_formation": _layer(
        "pattern_formation", "격의 성립과 파격", "pattern", 1, "active", "gate",
        "gyeokguk_profile.formation_state gyeokguk_profile.candidates pattern_profile",
        "gyeokguk.py patterns.py expert_adjudication.py",
        "격국_핵심어사전_v1.md|격국에 대한 모든 것들_최신화버전.pdf",
        ("월령의 기능이 실제 격으로 성립하는가?", "이름뿐인 격과 작동하는 격을 구별했는가?"),
        "pattern_state",
    ),
    "pattern_clarity": _layer(
        "pattern_clarity", "격국의 청탁과 혼잡", "pattern", 1, "active", "gate",
        "gyeokguk_profile.clarity_state gyeokguk_profile.candidates.*.clarity_state",
        "gyeokguk.py",
        "격국_핵심어사전_v1.md|격국에 대한 모든 것들_최신화버전.pdf",
        ("역할이 맑고 일관되는가 혼잡한가?", "혼잡을 단순 감점하지 않고 정리·복구 조건을 확인했는가?"),
        "pattern_state",
    ),
    "pattern_single_actions": _layer(
        "pattern_single_actions", "격국별 단일 십신 작용", "pattern", 1, "active", "chain",
        "gyeokguk_profile.ten_god_action_matches",
        "gyeokguk_ten_god_actions.py gyeokguk_contextual.py",
        "격국_핵심어사전_v1.md|십신배합_핵심어사전_v1.md",
        ("같은 재극인이라도 재격과 인수격에서 역할이 어떻게 다른가?", "상신·기신·구신 관계가 실제 배합에 맞는가?"),
        "pattern_action",
    ),
    "pattern_dual_actions": _layer(
        "pattern_dual_actions", "격국별 이중 십신 연쇄", "pattern", 1, "active", "chain",
        "gyeokguk_profile.dual_ten_god_action_matches",
        "gyeokguk_dual_ten_god_actions.py gyeokguk_contextual.py",
        "격국_핵심어사전_v1.md|십신배합_핵심어사전_v1.md",
        ("격을 중심으로 두 십신이 어떤 순서로 작동하는가?", "복구·손상·전환의 선후 관계를 반영했는가?"),
        "pattern_action",
    ),
    "useful_element_roles": _layer(
        "useful_element_roles", "용신 역할의 분리", "pattern", 1, "active", "conditional",
        "expert_adjudication.useful_element_decisions pattern_profile.useful_element_candidates month_governance_profile",
        "expert_adjudication.py patterns.py month_governance.py",
        "격국_핵심어사전_v1.md|월령_핵심어사전_v1.md|궁통보감 정리본.pdf|병약론 정리.pdf",
        ("격국용·억부용·조후용·병약·통관 역할을 구별했는가?", "한 오행이 여러 역할을 할 때 한 번만 점수화했는가?"),
        "useful_role",
    ),
    "special_pattern_exceptions": _layer(
        "special_pattern_exceptions", "종격·화격·전왕격 예외", "pattern", 2, "partial", "gate",
        "pattern_profile.special_pattern_flags pattern_profile.pattern_family",
        "patterns.py gyeokguk.py",
        "격국_핵심어사전_v1.md|격국에 대한 모든 것들_최신화버전.pdf",
        ("일반 억부 규칙을 뒤집는 외격 조건이 실제로 충족되는가?", "외격이 불완전하면 정격 논리로 복귀하는가?"),
        "pattern_exception",
    ),
    "integrated_saju_signals": _layer(
        "integrated_saju_signals", "오행·십신·수용의 통합 신호", "integration", 1, "active", "synthesis",
        "integrated_saju_profile",
        "stem_receptions.py",
        "10천간배합_핵심어사전_v1.md|십신배합_핵심어사전_v1.md|오행배합_핵심어사전_v1.md",
        ("같은 두 글자를 오행·십신·일간 수용 관점에서 종합했는가?", "통합 신호가 원재료 신호를 중복 가산하지 않는가?"),
        "integrated_pair",
    ),
    "spouse_star_gender": _layer(
        "spouse_star_gender", "성별별 배우자성과 일지", "kinship", 1, "active", "conditional",
        "gender day_master_stem position_signals.day ten_god_profile",
        "metric_adjudication.py structure.py ten_gods.py",
        "십신_핵심어사전_v1_1.md|위치에 따른 십신의 해석.pdf",
        ("성별에 따른 배우자성을 구별했는가?", "배우자성만으로 혼인 전체를 단정하지 않고 일지·관계 구조를 함께 보는가?"),
        "spouse_evidence",
    ),
    "kinship_projection": _layer(
        "kinship_projection", "육친과 관계 투사", "kinship", 2, "partial", "conditional",
        "gender position_signals ten_god_profile",
        "structure.py ten_gods.py",
        "십신_핵심어사전_v1_1.md|위치에 따른 십신의 해석.pdf",
        ("십신의 육친 의미를 궁위와 성별에 맞게 제한했는가?", "육친 표상을 성격 점수로 중복 사용하지 않았는가?"),
        "kinship",
    ),
    "day_pillar_profile": _layer(
        "day_pillar_profile", "일주 성정", "personality_source", 3, "support_only", "support_only",
        "source_personality_profile.day_pillar_profile",
        "source_personality_profiles.py",
        "60일주_핵심키워드_v1.md|일주의 성격.pdf",
        ("일주 성정이 구조 판단을 보조하는가?", "일주 문구를 객관적 재물·직업 점수로 직접 전환하지 않았는가?"),
        "personality_source",
    ),
    "month_day_archetype": _layer(
        "month_day_archetype", "월지별 일주 기질", "personality_source", 3, "support_only", "support_only",
        "source_personality_profile.month_day_pillar_profile source_personality_profile.month_branch_profile",
        "source_personality_profiles.py",
        "12월지_보정핵심키워드_v1.md|60일주_핵심키워드_v1.md",
        ("월지 환경이 일주의 표현을 어떻게 보정하는가?", "고객 유형화와 실제 구조 점수를 구별했는가?"),
        "personality_source",
    ),
    "twelve_growth": _layer(
        "twelve_growth", "십이운성", "auxiliary", 3, "support_only", "support_only",
        "auxiliary_profile.twelve_growth_by_position",
        "auxiliary.py",
        "십이운성의 십신 배치에 따른 해석.pdf",
        ("기능의 생장·쇠퇴 단계를 보조로 확인하는가?", "십이운성 하나로 강약이나 길흉을 뒤집지 않았는가?"),
        "auxiliary",
    ),
    "auxiliary_shinsal": _layer(
        "auxiliary_shinsal", "신살·잡설 보조 신호", "auxiliary", 4, "support_only", "support_only",
        "auxiliary_profile.sal_by_position auxiliary_profile.misc_shinsal_signals",
        "auxiliary.py",
        "신살_잡설_핵심어사전_v1.md",
        ("원국 구조와 일치할 때만 장면을 보조하는가?", "신살이 점수의 주근거 또는 단독 결론이 되지 않았는가?"),
        "auxiliary",
    ),
    "timing_activation": _layer(
        "timing_activation", "대운·세운의 발동", "timing", 1, "active", "dynamic_only",
        "flow_signals sub_period_signals",
        "flows.py output.py",
        "대세운.txt|격국_핵심어사전_v1.md|십신_핵심어사전_v1_1.md",
        ("원국의 잠재 기능을 운이 발동·강화·손상하는가?", "시기 신호를 타고난 총운 점수에 섞지 않았는가?"),
        "timing",
    ),
    "relationship_status": _layer(
        "relationship_status", "현재 관계 상태", "context", 2, "active", "selection_only",
        "relationship_status",
        "models.py report_service.py",
        "",
        ("미혼·연애·기혼에 맞는 지표만 선택했는가?", "현재 상태가 원국 점수를 임의로 바꾸지 않고 노출 항목만 조정하는가?"),
        "user_context",
    ),
    "birth_time_confidence": _layer(
        "birth_time_confidence", "생시 유무와 신뢰도", "confidence", 1, "partial", "confidence_gate",
        "four_pillars warnings position_signals.hour",
        "structure.py engine.py",
        "태어난 시간에 따른 시주.pdf",
        ("생시 미상일 때 시주·후반·자녀·결과 판단을 제외하거나 낮추는가?", "임시 시주를 실제 근거로 사용하지 않는가?"),
        "confidence",
    ),
    "evidence_materiality": _layer(
        "evidence_materiality", "근거의 강도와 현실성", "confidence", 1, "active", "weighting",
        "*.strength *.priority_score *.presence_score *.reality_score *.confidence",
        "features.py expert_adjudication.py metric_adjudication.py",
        "분석 엔진 내부 계약",
        ("약한 신호도 존재는 인정하되 비중을 낮추는가?", "투출·통근·월령·위치가 강한 근거를 우선하는가?"),
        "evidence_weight",
    ),
    "independent_evidence_accounting": _layer(
        "independent_evidence_accounting", "독립 근거 합산과 중복 방지", "confidence", 1, "partial", "weighting",
        "basis_codes counter_signals",
        "features.py metric_adjudication.py annual_metric_contracts.py",
        "분석 엔진 내부 계약",
        ("같은 원재료가 오행·십신·격국 이름으로 세 번 가산되지 않는가?", "최소 두 개 이상의 독립 근거군이 결론을 지지하는가?"),
        "evidence_weight",
    ),
    "past_event_calibration": _layer(
        "past_event_calibration", "과거 사건 교정", "confidence", 4, "support_only", "calibration_only",
        "calibration_profile",
        "calibration.py past_event_prompts.py",
        "",
        ("사용자 확인값은 신뢰도 보정에만 쓰이는가?", "확인 응답이 원국 구조를 새로 만들어내지 않는가?"),
        "calibration",
    ),
}


def _metric(
    key: str,
    label: str,
    domain: str,
    primary: str,
    confirming: str,
    pressure: str,
    positions: str,
    chains: str,
    *,
    semantic: SemanticAxis = "quality",
    minimum: int = 6,
) -> MetricTheoryRequirement:
    split = lambda value: tuple(item for item in value.split() if item)
    return MetricTheoryRequirement(
        metric_key=key,
        label=label,
        domain=domain,
        semantic_axis=semantic,
        primary_layers=split(primary),
        confirming_layers=split(confirming),
        pressure_layers=split(pressure),
        required_positions=split(positions),
        classical_chains=tuple(item for item in chains.split("|") if item),
        minimum_independent_families=minimum,
        prohibited_shortcuts=(
            "십신 기능군 수량 하나로 결론내지 않는다.",
            "월령 적합성 없이 오행의 많고 적음만 가산하지 않는다.",
            "같은 basis_code 계열을 다른 이론명으로 중복 합산하지 않는다.",
            "보조 신살과 일주 성정은 단독 점수 근거로 쓰지 않는다.",
        ),
    )


_COMMON = "month_environment month_hidden_phase seasonal_element_strength day_master_capacity element_distribution element_quality ten_god_groups special_pattern_exceptions evidence_materiality independent_evidence_accounting"
_REALITY = "visible_stems hidden_stems protrusion_rooting position_palaces branch_pairs formal_branch_relations"


METRIC_THEORY_REQUIREMENTS: dict[str, MetricTheoryRequirement] = {
    # Money
    "wealth_formation": _metric("wealth_formation", "재물 형성력", "money", f"{_COMMON} exact_ten_gods ten_god_interactions element_circulation", f"{_REALITY} pattern_single_actions", "pattern_dual_actions formal_branch_relations", "month", "식상생재|재성의 현실성|비겁분재"),
    "income_generation": _metric("income_generation", "수입 창출력", "money", f"{_COMMON} exact_ten_gods ten_god_interactions visible_stems", "element_combinations position_palaces pattern_single_actions directional_interactions stem_combinations", "illness_medicine formal_branch_relations stem_transformation", "month", "식상생재|재생관|인성의 식상 제약"),
    "asset_consolidation": _metric("asset_consolidation", "자산화 성향", "money", f"{_COMMON} exact_ten_gods ten_god_interactions position_palaces", "pattern_clarity hidden_stems branch_pairs life_stage_positions", "formal_branch_relations pattern_dual_actions", "day hour", "재성·인성·관성의 보존 연쇄|비겁쟁재|재극인의 균형"),
    "cashflow_stability": _metric("cashflow_stability", "현금 운용력", "money", f"{_COMMON} exact_ten_gods element_circulation branch_pairs", "position_palaces ten_god_interactions pattern_clarity", "formal_branch_relations pattern_dual_actions", "month day", "정재의 반복성|편재의 변동성|관성의 통제"),
    "contract_title_stability": _metric("contract_title_stability", "계약 안정성", "money", f"{_COMMON} exact_ten_gods pattern_clarity position_palaces", "visible_stems protrusion_rooting ten_god_interactions", "formal_branch_relations branch_transformation", "month day", "재관인 연결|상관견관|비겁의 명의 침범"),
    "shared_money_control": _metric("shared_money_control", "공동재 관리", "money", f"{_COMMON} exact_ten_gods position_palaces branch_pairs", "ten_god_interactions spouse_star_gender formal_branch_relations", "pattern_dual_actions kinship_projection", "day month", "관성제비겁|비겁쟁재|재생관"),
    "financial_loss_defense": _metric("financial_loss_defense", "손실 회피력", "money", f"{_COMMON} exact_ten_gods ten_god_interactions pattern_clarity", "branch_pairs formal_branch_relations illness_medicine", "pattern_dual_actions branch_transformation", "day hour", "인성의 검토|관성의 통제|비겁쟁재·상관견관 방어"),
    "investment_trading_judgment": _metric("investment_trading_judgment", "투자 판단력", "money", f"{_COMMON} exact_ten_gods element_circulation ten_god_interactions", "visible_stems pattern_single_actions stem_reception", "formal_branch_relations illness_medicine", "month day", "편재의 기회 감지|인성의 검증|식상의 실행|비겁의 과열"),
    "performance_reward": _metric("performance_reward", "보상 회수력", "money", f"{_COMMON} ten_god_interactions pattern_single_actions visible_stems", "position_palaces pattern_clarity element_circulation", "formal_branch_relations pattern_dual_actions", "month", "식상생재|재생관|성과와 직책 보상의 연결"),
    "late_life_wealth_growth": _metric("late_life_wealth_growth", "후반 축재성", "money", f"{_COMMON} exact_ten_gods position_palaces life_stage_positions", "hidden_stems protrusion_rooting branch_pairs", "formal_branch_relations birth_time_confidence", "hour day", "재성의 시주 현실성|식상생재의 장기 반복|비겁분재"),

    # Career
    "achievement_accumulation": _metric("achievement_accumulation", "직업 성취도", "career", f"{_COMMON} pattern_formation pattern_single_actions ten_god_interactions", "position_palaces visible_stems integrated_saju_signals", "pattern_dual_actions formal_branch_relations", "month hour", "식상→재성→관성|관인상생|격의 성격·파격"),
    "organization_fit": _metric("organization_fit", "조직 적응성", "career", f"{_COMMON} exact_ten_gods pattern_clarity position_palaces", "ten_god_interactions branch_pairs useful_element_roles", "formal_branch_relations pattern_dual_actions", "month", "관인상생|재생관|상관견관의 조정"),
    "promotion_title_readiness": _metric("promotion_title_readiness", "직책 상승성", "career", f"{_COMMON} exact_ten_gods pattern_formation pattern_single_actions", "visible_stems protrusion_rooting position_palaces", "pattern_dual_actions formal_branch_relations", "month year", "재생관|관인상생|관살혼잡 정리"),
    "professional_depth": _metric("professional_depth", "전문성 축적", "career", f"{_COMMON} exact_ten_gods ten_god_interactions hidden_stems", "protrusion_rooting position_palaces pattern_single_actions", "illness_medicine formal_branch_relations", "month hour", "인성→식신|관성의 자격 공인|편인도식의 조정"),
    "practical_execution": _metric("practical_execution", "실무 처리력", "career", f"{_COMMON} exact_ten_gods ten_god_interactions element_circulation", "visible_stems position_palaces stem_reception directional_interactions", "illness_medicine formal_branch_relations", "month", "식신의 생산|식신제살|인성 과다의 지연"),
    "planning_judgment": _metric("planning_judgment", "기획 판단력", "career", f"{_COMMON} exact_ten_gods pattern_single_actions element_combinations", "ten_god_interactions position_palaces integrated_saju_signals", "pattern_dual_actions illness_medicine", "month", "인성의 설계|재성의 현실 검증|관성의 기준화"),
    "authority_scope": _metric("authority_scope", "권한 확보력", "career", f"{_COMMON} exact_ten_gods pattern_formation pattern_clarity", "position_palaces visible_stems ten_god_interactions", "pattern_dual_actions formal_branch_relations", "month hour", "관성제비겁|재생관|인성의 명분 보강"),
    "evaluation_management": _metric("evaluation_management", "평가 관리력", "career", f"{_COMMON} exact_ten_gods pattern_clarity position_palaces", "visible_stems ten_god_interactions branch_pairs", "formal_branch_relations pattern_dual_actions", "month year", "관인상생|식상의 성과 공개|상관견관 조정"),
    "independent_work": _metric("independent_work", "독립 업무성", "career", f"{_COMMON} exact_ten_gods visible_stems ten_god_interactions", "position_palaces element_circulation stem_reception", "pattern_formation formal_branch_relations", "month hour", "식상생재|비겁의 자립|관성 통제와 자율의 균형"),
    "career_continuity": _metric("career_continuity", "직업 지속성", "career", f"{_COMMON} pattern_formation pattern_clarity position_palaces", "exact_ten_gods ten_god_interactions life_stage_positions", "formal_branch_relations illness_medicine", "month hour", "관인상생|식상의 반복 생산|격의 손상과 복구"),

    # Personality
    "self_direction": _metric("self_direction", "자기 기준", "personality", f"{_COMMON} exact_ten_gods stem_reception position_palaces", "day_pillar_profile month_day_archetype branch_pairs", "formal_branch_relations illness_medicine", "day", "비겁의 주체성|관성의 자기 규율|인성의 확신"),
    "emotional_alignment": _metric("emotional_alignment", "감정 조절", "personality", f"{_COMMON} element_circulation exact_ten_gods branch_pairs", "climate_temperature climate_moisture ten_god_interactions", "formal_branch_relations illness_medicine", "day month", "인성의 수용|관성의 절제|식상의 배출"),
    "action_pace": _metric("action_pace", "실행 속도", "personality", f"{_COMMON} visible_stems exact_ten_gods element_circulation", "stem_reception position_palaces yin_yang_balance", "illness_medicine pattern_clarity", "month day", "식상의 발동|비겁의 추진|재성의 현실 착수"),
    "decision_consistency": _metric("decision_consistency", "신중성", "personality", f"{_COMMON} exact_ten_gods pattern_clarity position_palaces", "element_combinations ten_god_interactions integrated_saju_signals", "formal_branch_relations illness_medicine", "day month", "인성의 검토|관성의 기준|재성의 결과 계산"),
    "focus_depth": _metric("focus_depth", "몰입 성향", "personality", f"{_COMMON} exact_ten_gods hidden_stems protrusion_rooting", "position_palaces day_pillar_profile element_quality", "formal_branch_relations illness_medicine", "day hour", "인성의 집중|식신의 반복 숙련|비겁의 지속"),
    "boundary_management": _metric("boundary_management", "관계 거리 조절력", "personality", f"{_COMMON} position_palaces branch_pairs exact_ten_gods", "formal_branch_relations spouse_star_gender day_pillar_profile", "kinship_projection illness_medicine", "day year", "관성의 경계|비겁의 독립|인성의 내적 거리"),
    "crisis_recovery": _metric("crisis_recovery", "문제 해결력", "personality", f"{_COMMON} ten_god_interactions illness_medicine element_circulation", "pattern_dual_actions branch_pairs stem_reception", "formal_branch_relations pattern_clarity", "day month", "식신제살|재극인의 현실화|관인상생의 복구"),
    "change_adaptability": _metric("change_adaptability", "변화 수용성", "personality", f"{_COMMON} element_circulation branch_pairs exact_ten_gods", "visible_stems stem_reception formal_branch_relations", "illness_medicine pattern_clarity", "month day", "식상의 전환|편재의 기회 대응|인성의 수정 능력"),
    "communication_expression": _metric("communication_expression", "표현 방식", "personality", f"{_COMMON} exact_ten_gods visible_stems stem_reception", "element_combinations position_palaces day_pillar_profile directional_interactions stem_combinations", "formal_branch_relations illness_medicine", "day month year", "식상의 표현|인성의 언어 정리|관성의 표현 통제"),
    "responsibility_capacity": _metric("responsibility_capacity", "책임 감각", "personality", f"{_COMMON} exact_ten_gods pattern_formation position_palaces", "ten_god_interactions pattern_single_actions day_master_capacity", "pattern_dual_actions formal_branch_relations", "month day year", "관성의 책임|인성의 지속|재성의 현실 부담"),
    "honor_recognition": _metric("honor_recognition", "인정 욕구", "personality", f"{_COMMON} exact_ten_gods visible_stems position_palaces", "pattern_formation ten_god_interactions day_pillar_profile", "formal_branch_relations pattern_clarity", "year month", "관성의 명예|식상의 노출|비겁의 승부욕", semantic="magnitude"),
    "loss_avoidance": _metric("loss_avoidance", "위험 감지", "personality", f"{_COMMON} exact_ten_gods pattern_clarity branch_pairs", "illness_medicine formal_branch_relations stem_reception", "pattern_dual_actions climate_moisture", "day month hour", "인성의 검토|관성의 제한|재성의 손익 계산"),

    # Love
    "opposite_sex_appeal": _metric("opposite_sex_appeal", "이성 대상 호감도", "love", f"{_COMMON} spouse_star_gender visible_stems exact_ten_gods", "position_palaces element_combinations auxiliary_shinsal", "formal_branch_relations illness_medicine", "day month", "식상의 매력 표현|배우자성의 현실성|도화는 보조"),
    "affection_expression": _metric("affection_expression", "애정 표현", "love", f"{_COMMON} exact_ten_gods visible_stems position_palaces", "stem_reception branch_pairs spouse_star_gender directional_interactions", "formal_branch_relations illness_medicine", "day month", "식상의 표현|재성의 돌봄|인성의 정서 수용"),
    "relationship_stability": _metric("relationship_stability", "관계 지속성", "love", f"{_COMMON} spouse_star_gender position_palaces branch_pairs", "exact_ten_gods pattern_clarity life_stage_positions", "formal_branch_relations pattern_dual_actions", "day hour", "관인·재관의 지속 구조|비겁 충돌|일지 안정"),
    "romantic_emotional_stability": _metric("romantic_emotional_stability", "감정 안정성", "love", f"{_COMMON} climate_temperature climate_moisture branch_pairs", "exact_ten_gods position_palaces stem_reception", "formal_branch_relations illness_medicine", "day month", "인성의 수용|관성의 절제|식상의 감정 배출"),
    "partner_selection": _metric("partner_selection", "선택 신중성", "love", f"{_COMMON} spouse_star_gender exact_ten_gods pattern_clarity", "position_palaces branch_pairs integrated_saju_signals", "formal_branch_relations illness_medicine", "day month year", "인성의 검증|관성의 기준|재성의 현실 적합성"),
    "conflict_recovery": _metric("conflict_recovery", "갈등 회복력", "love", f"{_COMMON} branch_pairs formal_branch_relations ten_god_interactions", "illness_medicine spouse_star_gender position_palaces", "pattern_dual_actions pattern_clarity", "day month", "식상의 소통|인성의 수용|관성의 합의"),
    "partner_dependency_control": _metric("partner_dependency_control", "상대 의존도", "love", f"{_COMMON} exact_ten_gods spouse_star_gender position_palaces", "branch_pairs day_pillar_profile stem_reception", "formal_branch_relations illness_medicine", "day year", "비겁의 자립|인성의 의존|배우자성 쏠림", semantic="magnitude"),
    "relationship_agency": _metric("relationship_agency", "관계 주도성", "love", f"{_COMMON} exact_ten_gods visible_stems spouse_star_gender", "position_palaces branch_pairs yin_yang_balance", "formal_branch_relations illness_medicine", "day month", "비겁의 주도|식상의 표현|관성의 관계 규칙"),
    "bond_continuity": _metric("bond_continuity", "인연 지속성", "love", f"{_COMMON} spouse_star_gender position_palaces branch_pairs", "exact_ten_gods life_stage_positions pattern_clarity", "formal_branch_relations pattern_dual_actions", "day hour", "배우자성 통근|일지 안정|관인·재관의 유지"),
    "breakup_resilience": _metric("breakup_resilience", "이별 위험도", "love", f"{_COMMON} position_palaces branch_pairs formal_branch_relations", "spouse_star_gender exact_ten_gods illness_medicine", "pattern_dual_actions branch_transformation", "day month hour", "일지 충형파해|배우자성 손상|복구 신호", semantic="managed_risk"),

    # Marriage
    "marriage_overall_stability": _metric("marriage_overall_stability", "결혼 안정성", "marriage", f"{_COMMON} spouse_star_gender position_palaces branch_pairs", "pattern_clarity exact_ten_gods life_stage_positions", "formal_branch_relations pattern_dual_actions", "day hour", "배우자성·일지·재관인의 종합 안정"),
    "spouse_match": _metric("spouse_match", "배우자 인연", "marriage", f"{_COMMON} spouse_star_gender position_palaces exact_ten_gods", "branch_pairs protrusion_rooting relationship_status", "formal_branch_relations illness_medicine", "day", "배우자성의 존재·현실성|일지 수용|관계 발동"),
    "household_coordination": _metric("household_coordination", "생활 조율성", "marriage", f"{_COMMON} position_palaces branch_pairs ten_god_interactions", "exact_ten_gods formal_branch_relations spouse_star_gender", "pattern_dual_actions illness_medicine", "day hour", "식상의 소통|인성의 수용|관성의 역할 분담"),
    "family_responsibility": _metric("family_responsibility", "가정 책임감", "marriage", f"{_COMMON} exact_ten_gods position_palaces pattern_formation", "ten_god_interactions spouse_star_gender kinship_projection", "formal_branch_relations pattern_dual_actions", "day year", "관성의 책임|재성의 생활 부담|인성의 보호"),
    "marital_financial_agreement": _metric("marital_financial_agreement", "재정 합의성", "marriage", f"{_COMMON} spouse_star_gender position_palaces exact_ten_gods", "ten_god_interactions branch_pairs pattern_clarity", "formal_branch_relations pattern_dual_actions", "day month", "재관인의 합의|비겁쟁재|재극인의 현실 조정"),
    "family_relationship_stability": _metric("family_relationship_stability", "가족 관계성", "marriage", f"{_COMMON} position_palaces branch_pairs kinship_projection", "exact_ten_gods formal_branch_relations spouse_star_gender", "pattern_dual_actions illness_medicine", "day year", "인성의 보호|관성의 경계|비겁의 가족 경쟁"),
    "long_term_marriage": _metric("long_term_marriage", "장기 유지성", "marriage", f"{_COMMON} spouse_star_gender life_stage_positions position_palaces", "branch_pairs pattern_clarity exact_ten_gods", "formal_branch_relations birth_time_confidence", "day hour", "일지·시주의 지속|배우자성 통근|손상 복구"),
    "spouse_conflict_control": _metric("spouse_conflict_control", "배우자 충돌도", "marriage", f"{_COMMON} branch_pairs formal_branch_relations spouse_star_gender", "ten_god_interactions illness_medicine position_palaces", "pattern_dual_actions branch_transformation", "day month year", "일지 충형파해|비겁 경쟁|식상·관성의 조정", semantic="managed_risk"),
    "marriage_decision": _metric("marriage_decision", "결혼 시기성", "marriage", f"{_COMMON} spouse_star_gender position_palaces timing_activation", "exact_ten_gods pattern_formation relationship_status", "formal_branch_relations illness_medicine", "day month", "배우자성·일지의 운 발동|재관인의 현실 준비"),
    "post_marriage_stability": _metric("post_marriage_stability", "결혼 후 안정도", "marriage", f"{_COMMON} position_palaces branch_pairs spouse_star_gender", "exact_ten_gods life_stage_positions pattern_clarity", "formal_branch_relations pattern_dual_actions", "day hour", "생활·재정·가족 궁위의 종합 유지"),

    # Honor
    "honor_social_recognition": _metric("honor_social_recognition", "사회적 인정", "honor", f"{_COMMON} pattern_formation visible_stems exact_ten_gods", "position_palaces ten_god_interactions pattern_single_actions", "pattern_dual_actions formal_branch_relations", "year month", "식상의 성과 공개|관성의 공인|인성의 명분"),
    "honor_reputation_formation": _metric("honor_reputation_formation", "평판 형성", "honor", f"{_COMMON} pattern_clarity position_palaces exact_ten_gods", "visible_stems ten_god_interactions branch_pairs", "formal_branch_relations pattern_dual_actions", "year month", "관인상생|식상의 표현 관리|상관견관 조정"),
    "honor_title_rise": _metric("honor_title_rise", "직함 상승성", "honor", f"{_COMMON} pattern_formation exact_ten_gods pattern_single_actions", "visible_stems protrusion_rooting position_palaces", "pattern_dual_actions formal_branch_relations", "month", "재생관|관인상생|관살혼잡 정리"),
    "honor_public_trust": _metric("honor_public_trust", "공적 신뢰도", "honor", f"{_COMMON} pattern_clarity exact_ten_gods position_palaces", "ten_god_interactions visible_stems branch_pairs", "formal_branch_relations pattern_dual_actions", "year month", "관인상생|재생관|상관의 공적 기준 충돌"),
    "honor_responsibility_acceptance": _metric("honor_responsibility_acceptance", "책임 수용도", "honor", f"{_COMMON} day_master_capacity exact_ten_gods pattern_formation", "position_palaces ten_god_interactions useful_element_roles", "pattern_dual_actions illness_medicine", "month day", "관성의 책임|인성의 감당|재성의 현실 자원"),
    "honor_organizational_presence": _metric("honor_organizational_presence", "조직 내 존재감", "honor", f"{_COMMON} visible_stems exact_ten_gods position_palaces", "pattern_formation ten_god_interactions yin_yang_balance", "formal_branch_relations illness_medicine", "month day", "식상의 노출|비겁의 존재감|관성의 역할"),
    "honor_authority_establishment": _metric("honor_authority_establishment", "권위 확보력", "honor", f"{_COMMON} pattern_formation exact_ten_gods pattern_clarity", "position_palaces visible_stems ten_god_interactions", "pattern_dual_actions formal_branch_relations", "month year", "관성제비겁|관인상생|재생관"),
    "honor_legitimacy_management": _metric("honor_legitimacy_management", "명분 관리", "honor", f"{_COMMON} exact_ten_gods pattern_clarity ten_god_interactions", "position_palaces visible_stems useful_element_roles", "formal_branch_relations pattern_dual_actions", "year month", "인성의 근거|관성의 공인|재성의 현실 정당성"),

    # Social
    "social_affinity": _metric("social_affinity", "친화성", "social", f"{_COMMON} exact_ten_gods visible_stems branch_pairs", "position_palaces element_combinations day_pillar_profile", "formal_branch_relations illness_medicine", "month day", "식상의 교류|비겁의 동료성|인성의 수용"),
    "social_trust_formation": _metric("social_trust_formation", "신뢰 형성", "social", f"{_COMMON} exact_ten_gods pattern_clarity position_palaces", "branch_pairs ten_god_interactions visible_stems", "formal_branch_relations pattern_dual_actions", "month day", "관인상생|재성의 약속 이행|식상의 언행 일치"),
    "social_relationship_continuity": _metric("social_relationship_continuity", "관계 유지성", "social", f"{_COMMON} branch_pairs position_palaces exact_ten_gods", "formal_branch_relations ten_god_interactions life_stage_positions", "pattern_dual_actions illness_medicine", "day month", "인성의 수용|관성의 경계|비겁의 상호성"),
    "social_distance_control": _metric("social_distance_control", "거리 조절", "social", f"{_COMMON} position_palaces branch_pairs exact_ten_gods", "formal_branch_relations day_pillar_profile stem_reception", "kinship_projection illness_medicine", "day month", "관성의 경계|비겁의 독립|인성의 선택적 수용"),
    "social_cooperation": _metric("social_cooperation", "협력성", "social", f"{_COMMON} ten_god_interactions branch_pairs position_palaces", "exact_ten_gods pattern_single_actions element_circulation", "formal_branch_relations pattern_dual_actions", "month day", "식상생재의 분업|관성의 역할 배분|인성의 지원"),
    "social_competition_control": _metric("social_competition_control", "경쟁 노출도", "social", f"{_COMMON} exact_ten_gods branch_pairs pattern_clarity", "formal_branch_relations position_palaces ten_god_interactions", "pattern_dual_actions illness_medicine", "month day", "비겁 경쟁|관성제비겁|식상의 비교 노출", semantic="managed_risk"),
    "social_speech_influence": _metric("social_speech_influence", "말의 영향력", "social", f"{_COMMON} exact_ten_gods visible_stems position_palaces", "stem_reception pattern_formation element_combinations directional_interactions stem_combinations", "formal_branch_relations illness_medicine", "month day", "식상의 표현|관성의 공신력|인성의 논리"),
    "social_conflict_avoidance": _metric("social_conflict_avoidance", "갈등 회피력", "social", f"{_COMMON} branch_pairs formal_branch_relations ten_god_interactions", "position_palaces illness_medicine exact_ten_gods", "pattern_dual_actions pattern_clarity", "day month", "관성의 합의|인성의 수용|식상의 설명"),
    "social_benefactor_support": _metric("social_benefactor_support", "지인 덕", "social", f"{_COMMON} branch_pairs position_palaces exact_ten_gods", "ten_god_interactions formal_branch_relations auxiliary_shinsal", "pattern_dual_actions illness_medicine", "month year", "인성의 지원|관성의 추천|식상의 연결"),
    "social_acquaintance_loss_defense": _metric("social_acquaintance_loss_defense", "지인 피해/손실", "social", f"{_COMMON} branch_pairs formal_branch_relations exact_ten_gods", "position_palaces ten_god_interactions pattern_clarity", "pattern_dual_actions illness_medicine", "year day", "비겁쟁재|지인 보증·공동책임|관성의 경계", semantic="managed_risk"),
}


SUPPORT_ONLY_LAYER_KEYS = frozenset(
    key for key, layer in METRIC_THEORY_LAYERS.items() if layer.status == "support_only"
)
PLANNED_LAYER_KEYS = frozenset(
    key for key, layer in METRIC_THEORY_LAYERS.items() if layer.status == "planned"
)
REQUIRED_COMMON_GATE_KEYS = frozenset(
    {
        "month_environment",
        "seasonal_element_strength",
        "day_master_capacity",
        "evidence_materiality",
        "independent_evidence_accounting",
    }
)


def metric_theory_registry_audit() -> dict[str, object]:
    layer_keys = set(METRIC_THEORY_LAYERS)
    referenced_layer_keys: set[str] = set()
    missing_references: dict[str, list[str]] = {}
    primary_support_only: dict[str, list[str]] = {}
    primary_planned: dict[str, list[str]] = {}
    missing_common_gates: dict[str, list[str]] = {}
    insufficient_families: dict[str, int] = {}
    missing_positions: list[str] = []
    missing_chains: list[str] = []

    for key, requirement in METRIC_THEORY_REQUIREMENTS.items():
        referenced = set(requirement.primary_layers + requirement.confirming_layers + requirement.pressure_layers)
        referenced_layer_keys.update(referenced)
        missing = sorted(referenced - layer_keys)
        if missing:
            missing_references[key] = missing

        invalid_primary = sorted(set(requirement.primary_layers).intersection(SUPPORT_ONLY_LAYER_KEYS))
        if invalid_primary:
            primary_support_only[key] = invalid_primary

        unimplemented_primary = sorted(set(requirement.primary_layers).intersection(PLANNED_LAYER_KEYS))
        if unimplemented_primary:
            primary_planned[key] = unimplemented_primary

        absent_gates = sorted(REQUIRED_COMMON_GATE_KEYS - referenced)
        if absent_gates:
            missing_common_gates[key] = absent_gates

        families = {
            METRIC_THEORY_LAYERS[layer_key].family
            for layer_key in referenced
            if layer_key in METRIC_THEORY_LAYERS
            and METRIC_THEORY_LAYERS[layer_key].status != "support_only"
        }
        if len(families) < requirement.minimum_independent_families:
            insufficient_families[key] = len(families)
        if not requirement.required_positions:
            missing_positions.append(key)
        if not requirement.classical_chains:
            missing_chains.append(key)

    return {
        "registry_version": METRIC_THEORY_REGISTRY_VERSION,
        "layer_count": len(METRIC_THEORY_LAYERS),
        "metric_count": len(METRIC_THEORY_REQUIREMENTS),
        "status_counts": {
            status: sum(layer.status == status for layer in METRIC_THEORY_LAYERS.values())
            for status in ("active", "partial", "support_only", "planned")
        },
        "missing_references": missing_references,
        "support_only_used_as_primary": primary_support_only,
        "planned_used_as_primary": primary_planned,
        "missing_common_gates": missing_common_gates,
        "insufficient_independent_families": insufficient_families,
        "missing_positions": missing_positions,
        "missing_classical_chains": missing_chains,
        "unused_scoring_layers": sorted(
            key
            for key, layer in METRIC_THEORY_LAYERS.items()
            if layer.status in {"active", "partial"} and key not in referenced_layer_keys
        ),
    }
