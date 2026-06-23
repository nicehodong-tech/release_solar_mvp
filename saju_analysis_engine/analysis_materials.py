"""Analysis-material contract for the saju engine.

This module fixes the second-stage contract: which materials the engine may
use, which layer each material belongs to, and which life domains each material
can influence. It does not perform analysis by itself. It keeps later rule
expansions aligned with the output goals fixed in ``output_goals.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


ANALYSIS_MATERIAL_CONTRACT_VERSION = "analysis_material_contract_v1"
INTERPRETATION_CONNECTION_VERSION = "interpretation_connection_v1"


@dataclass(frozen=True)
class AnalysisMaterialLayer:
    key: str
    label: str
    source_layer: str
    current_engine_refs: tuple[str, ...]
    calculation_role: tuple[str, ...]
    domain_targets: tuple[str, ...]
    domain_usage: dict[str, str]
    weighting_rules: tuple[str, ...]
    activation_rules: tuple[str, ...]
    exclusion_rules: tuple[str, ...]
    sentence_rule: str


ANALYSIS_MATERIAL_ORDER = (
    "chart_input_basis",
    "palace_positions",
    "element_distribution",
    "day_master_strength",
    "heavenly_stem_visibility",
    "earthly_branch_foundation",
    "hidden_stem_storage",
    "protrusion_and_rooting",
    "ten_god_distribution",
    "branch_relations",
    "element_pair_relations",
    "directional_stem_relations",
    "ten_god_pair_relations",
    "day_stem_reception",
    "integrated_pair_action",
    "cycle_regulation",
    "structure_useful_elements",
    "auxiliary_references",
    "fortune_activation",
    "flow_branch_relations",
    "calibration_feedback",
)


INTERPRETATION_STAGE_ORDER = (
    "source_confirmation",
    "single_material_reading",
    "bridge_activation",
    "relation_action",
    "synthesis_adjustment",
    "supporting_reference",
    "timing_activation",
    "calibration_adjustment",
)


INTERPRETATION_STAGE_LABELS = {
    "source_confirmation": "원자료 확정",
    "single_material_reading": "단일 재료 판독",
    "bridge_activation": "표면화와 지속성 확인",
    "relation_action": "관계 작용 계산",
    "synthesis_adjustment": "격국과 필요 요소 보정",
    "supporting_reference": "보조 신호 보강",
    "timing_activation": "운 자극 적용",
    "calibration_adjustment": "과거 사건 검증 보정",
}


MATERIAL_INTERPRETATION_STAGES = {
    "chart_input_basis": "source_confirmation",
    "palace_positions": "source_confirmation",
    "element_distribution": "single_material_reading",
    "day_master_strength": "single_material_reading",
    "heavenly_stem_visibility": "source_confirmation",
    "earthly_branch_foundation": "source_confirmation",
    "hidden_stem_storage": "source_confirmation",
    "protrusion_and_rooting": "bridge_activation",
    "ten_god_distribution": "single_material_reading",
    "branch_relations": "relation_action",
    "element_pair_relations": "relation_action",
    "directional_stem_relations": "relation_action",
    "ten_god_pair_relations": "relation_action",
    "day_stem_reception": "relation_action",
    "integrated_pair_action": "relation_action",
    "cycle_regulation": "relation_action",
    "structure_useful_elements": "synthesis_adjustment",
    "auxiliary_references": "supporting_reference",
    "fortune_activation": "timing_activation",
    "flow_branch_relations": "timing_activation",
    "calibration_feedback": "calibration_adjustment",
}


DOMAIN_PRIORITY_LEVELS = ("gate", "primary", "support", "modifier", "timing", "calibration")


MATERIAL_DOMAIN_PRIORITIES: dict[str, dict[str, str]] = {
    "chart_input_basis": {
        "money": "gate",
        "career": "gate",
        "love": "gate",
        "marriage": "gate",
        "personality": "gate",
    },
    "palace_positions": {
        "money": "support",
        "career": "primary",
        "love": "primary",
        "marriage": "primary",
        "personality": "support",
    },
    "element_distribution": {
        "money": "support",
        "career": "support",
        "love": "support",
        "marriage": "support",
        "personality": "primary",
    },
    "day_master_strength": {
        "money": "support",
        "career": "support",
        "love": "support",
        "marriage": "support",
        "personality": "primary",
    },
    "heavenly_stem_visibility": {
        "money": "support",
        "career": "primary",
        "love": "support",
        "marriage": "support",
        "personality": "primary",
    },
    "earthly_branch_foundation": {
        "money": "support",
        "career": "primary",
        "love": "primary",
        "marriage": "primary",
        "personality": "support",
    },
    "hidden_stem_storage": {
        "money": "support",
        "career": "support",
        "love": "support",
        "marriage": "support",
        "personality": "support",
    },
    "protrusion_and_rooting": {
        "money": "primary",
        "career": "primary",
        "love": "support",
        "marriage": "support",
        "personality": "support",
    },
    "ten_god_distribution": {
        "money": "primary",
        "career": "primary",
        "love": "primary",
        "marriage": "primary",
        "personality": "primary",
    },
    "branch_relations": {
        "money": "support",
        "career": "primary",
        "love": "primary",
        "marriage": "primary",
        "personality": "support",
    },
    "element_pair_relations": {
        "money": "support",
        "career": "primary",
        "love": "support",
        "marriage": "support",
        "personality": "primary",
    },
    "directional_stem_relations": {
        "money": "support",
        "career": "primary",
        "love": "primary",
        "marriage": "support",
        "personality": "primary",
    },
    "ten_god_pair_relations": {
        "money": "primary",
        "career": "primary",
        "love": "support",
        "marriage": "primary",
        "personality": "support",
    },
    "day_stem_reception": {
        "money": "support",
        "career": "support",
        "love": "primary",
        "marriage": "support",
        "personality": "primary",
    },
    "integrated_pair_action": {
        "money": "primary",
        "career": "primary",
        "love": "primary",
        "marriage": "primary",
        "personality": "primary",
    },
    "cycle_regulation": {
        "money": "primary",
        "career": "primary",
        "love": "support",
        "marriage": "primary",
        "personality": "primary",
    },
    "structure_useful_elements": {
        "money": "primary",
        "career": "primary",
        "love": "support",
        "marriage": "support",
        "personality": "primary",
    },
    "auxiliary_references": {
        "money": "modifier",
        "career": "modifier",
        "love": "modifier",
        "marriage": "modifier",
        "personality": "modifier",
    },
    "fortune_activation": {
        "money": "timing",
        "career": "timing",
        "love": "timing",
        "marriage": "timing",
        "personality": "timing",
    },
    "flow_branch_relations": {
        "money": "timing",
        "career": "timing",
        "love": "timing",
        "marriage": "timing",
        "personality": "timing",
    },
    "calibration_feedback": {
        "money": "calibration",
        "career": "calibration",
        "love": "calibration",
        "marriage": "calibration",
        "personality": "calibration",
    },
}


ANALYSIS_MATERIAL_LAYERS: dict[str, AnalysisMaterialLayer] = {
    "chart_input_basis": AnalysisMaterialLayer(
        key="chart_input_basis",
        label="정밀 명식 원자료",
        source_layer="source",
        current_engine_refs=(
            "BirthChartResult.four_pillars",
            "BirthChartResult.true_solar_datetime",
            "BirthChartResult.calculation_warnings",
        ),
        calculation_role=(
            "연월일시 네 기둥과 진태양시 보정 결과를 모든 분석의 출발점으로 삼는다.",
            "경계 민감 여부와 산출 경고는 해석 확신도를 낮추는 근거로 보존한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "명식 자체가 불안정하면 재물 규모와 시기 판단을 강하게 단정하지 않는다.",
            "career": "월주와 연주의 사회적 조건을 읽기 전에 명식 산출의 안정성을 먼저 확인한다.",
            "love": "일지와 시지의 관계 판단이 출생 시각 경계에 걸리는지 확인한다.",
            "marriage": "배우자궁 판단이 경계 보정으로 바뀔 수 있는지 확인한다.",
            "personality": "일간과 월령이 확정된 뒤에만 성향의 기본 방향을 말한다.",
        },
        weighting_rules=(
            "진태양시 기준 명식이 확정되면 기본 가중치를 유지한다.",
            "절기 또는 시주 경계가 가까우면 사건 단정 문장을 낮은 확신도로 조정한다.",
        ),
        activation_rules=(
            "모든 분석에서 가장 먼저 활성화한다.",
            "경계 민감 경고가 있으면 출력의 주의층에 근거를 남긴다.",
        ),
        exclusion_rules=(
            "명식 산출이 불안정한 상태에서 세부 연도와 월의 강한 결론을 내지 않는다.",
            "출생지와 시간 보정이 빠진 명식은 정밀 판단의 근거로 쓰지 않는다.",
        ),
        sentence_rule=(
            "고객에게는 내부 계산식보다 명식 기준이 안정적으로 확정되었는지, "
            "또는 조심스럽게 보아야 하는지를 먼저 설명한다."
        ),
    ),
    "palace_positions": AnalysisMaterialLayer(
        key="palace_positions",
        label="연월일시 위치와 궁성",
        source_layer="source",
        current_engine_refs=("ChartStructure.position_signals", "POSITION_DOMAINS"),
        calculation_role=(
            "같은 글자라도 연주, 월주, 일주, 시주 중 어디에 놓였는지에 따라 사건 영역을 나눈다.",
            "월주는 직업과 사회 환경, 일지는 관계와 배우자, 시주는 결과물과 장기 방향을 우선 본다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "월주와 시주의 재성, 식상, 지장간은 수입 방식과 후반 축적력을 판단하는 근거가 된다.",
            "career": "월주는 직업 환경과 사회적 역할의 중심 근거가 된다.",
            "love": "일지와 일간 주변의 작용은 가까운 관계에서 체감되는 태도를 판단하게 한다.",
            "marriage": "일지는 배우자궁으로 보며, 합충형해파가 걸리면 결혼 안정 조건을 다시 본다.",
            "personality": "일간 주변과 월령의 배치는 판단 속도와 사회적 반응을 보정한다.",
        },
        weighting_rules=(
            "월주는 사회적 사건과 직업 판단에서 가장 강하게 반영한다.",
            "일지는 관계와 결혼 판단에서 가장 민감하게 반영한다.",
            "시주는 장기 결과, 후반기, 자녀, 결과물 판단에 보조 가중치를 둔다.",
        ),
        activation_rules=(
            "모든 천간, 지지, 지장간 신호는 위치 정보와 함께 해석한다.",
            "운에서 들어온 글자가 특정 궁성을 자극하면 해당 영역의 사건 가능성을 높인다.",
        ),
        exclusion_rules=(
            "위치가 없는 글자 의미만으로 직업, 결혼, 재물 사건을 확정하지 않는다.",
            "연주 신호만으로 현재 직업과 결혼의 핵심 결론을 만들지 않는다.",
        ),
        sentence_rule=(
            "고객 문장에서는 위치명을 과도하게 설명하지 않고, 그 위치가 실제 생활에서 "
            "어떤 영역으로 드러나는지를 중심으로 말한다."
        ),
    ),
    "element_distribution": AnalysisMaterialLayer(
        key="element_distribution",
        label="오행 분포와 배합 기반",
        source_layer="single",
        current_engine_refs=("ChartStructure.element_profile", "ElementProfile.scores"),
        calculation_role=(
            "오행의 많고 적음, 드러남과 숨음, 계절 보정 뒤의 실제 힘을 계산한다.",
            "오행 자체의 물상과 배합 가능성을 십신 판단과 분리해서 보존한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재물을 담는 그릇, 생산력, 보존력, 손실 가능성의 기본 체질을 판단한다.",
            "career": "전문성, 표현력, 책임 수행, 조직 적응의 기본 재료를 판단한다.",
            "love": "감정 표현, 거리감, 반응 속도, 관계 지속력의 기초 성향을 본다.",
            "marriage": "생활 기반, 현실 부담, 가정 안정의 체질적 조건을 본다.",
            "personality": "판단 방식, 행동 속도, 위험 반응의 기본 성질을 본다.",
        },
        weighting_rules=(
            "월령 보정 뒤의 오행 힘을 기본값으로 사용한다.",
            "천간에 드러난 오행은 외부 표현력이 크고, 지장간에만 있는 오행은 조건부 재료로 본다.",
            "과한 오행은 장점과 부담을 함께 계산한다.",
        ),
        activation_rules=(
            "오행이 천간에 드러나거나 월령의 도움을 받을 때 강하게 활성화한다.",
            "운에서 같은 오행이 들어와 기존 과부족을 건드리면 사건 재료로 올린다.",
        ),
        exclusion_rules=(
            "오행 하나가 많다는 이유만으로 재물, 직업, 결혼의 결론을 단정하지 않는다.",
            "계절상 쓸 수 없는 오행은 겉으로 보여도 낮은 작용력으로 처리한다.",
        ),
        sentence_rule=(
            "오행 문장은 추상적인 성격론으로 끝내지 않고, 돈을 다루는 방식, 일하는 방식, "
            "관계에서 보이는 태도처럼 생활 장면으로 번역한다."
        ),
    ),
    "day_master_strength": AnalysisMaterialLayer(
        key="day_master_strength",
        label="일간 강약과 필요한 균형",
        source_layer="single",
        current_engine_refs=(
            "ElementProfile.day_master_strength_score",
            "ElementProfile.useful_elements",
            "ElementProfile.caution_elements",
            "ElementProfile.climate_needs",
        ),
        calculation_role=(
            "일간이 재성, 관성, 식상, 인성을 실제로 감당할 수 있는지 판단한다.",
            "조후와 병약 관점에서 필요한 오행과 부담이 되는 오행을 나눈다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "돈을 벌 기회가 있어도 감당 가능한 규모인지, 축적 가능한 힘인지 판단한다.",
            "career": "책임과 평가를 받아낼 수 있는지, 압박으로 무너지는지 판단한다.",
            "love": "관계에서 주도하거나 조율하는 힘의 균형을 판단한다.",
            "marriage": "가정 책임과 현실 조건을 오래 감당할 수 있는지 판단한다.",
            "personality": "자기 기준의 강도, 결정 지속성, 압박 대응 방식을 판단한다.",
        },
        weighting_rules=(
            "일간이 약하면 큰 재물과 책임은 기회이면서 부담으로 함께 계산한다.",
            "일간이 강하면 경쟁과 자기 주도성은 강점이 되지만 분배와 충돌 부담도 같이 본다.",
        ),
        activation_rules=(
            "재성, 관성, 식상이 강하게 들어오는 시기에는 반드시 일간 강약을 함께 확인한다.",
            "용신 후보와 조후 필요 요소가 운에서 들어오면 회복 또는 성취 재료로 본다.",
        ),
        exclusion_rules=(
            "일간 강약만으로 좋고 나쁨을 단정하지 않는다.",
            "약한 일간이라고 해서 재물과 사회 성취를 일괄적으로 낮게 보지 않는다.",
        ),
        sentence_rule=(
            "고객에게는 강약이라는 용어보다 감당 가능한 규모, 오래 유지하는 힘, "
            "무리하기 쉬운 조건으로 설명한다."
        ),
    ),
    "heavenly_stem_visibility": AnalysisMaterialLayer(
        key="heavenly_stem_visibility",
        label="천간 노출",
        source_layer="source",
        current_engine_refs=("BirthChartResult.*_pillar.stem_key", "PositionSignal.stem_ten_god"),
        calculation_role=(
            "겉으로 드러나는 의지, 역할, 표현, 평가 가능성을 계산한다.",
            "천간끼리의 배합과 일간별 수용값을 만들기 위한 표면 재료로 사용한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "돈을 버는 방식이 외부 거래, 성과, 계약으로 드러나는지 판단한다.",
            "career": "직업적 역할, 평가, 명예, 공식 책임으로 보이는 정도를 판단한다.",
            "love": "감정 표현과 호감 형성이 밖으로 드러나는 방식을 본다.",
            "marriage": "배우자와의 약속, 책임, 생활 기준을 말로 정리하는 힘을 본다.",
            "personality": "생각과 의지가 외부 행동으로 나타나는 속도를 본다.",
        },
        weighting_rules=(
            "천간의 글자는 외부 표현과 사회적 인식에서 지장간보다 높은 가중치를 둔다.",
            "월간과 일간 주변의 천간은 직업과 관계 판단에서 특히 중시한다.",
        ),
        activation_rules=(
            "운에서 같은 천간 또는 합을 이루는 천간이 들어오면 노출된 주제가 강해진다.",
            "천간 배합이 생과 극을 만들면 행동과 결과를 함께 계산한다.",
        ),
        exclusion_rules=(
            "천간에 보인다는 이유만으로 실제 기반이 있다고 보지 않는다.",
            "지지와 지장간의 뿌리가 없으면 지속성을 낮게 본다.",
        ),
        sentence_rule=(
            "천간 해석은 겉으로 드러나는 태도, 말, 직업 역할, 대외 평가로 번역한다."
        ),
    ),
    "earthly_branch_foundation": AnalysisMaterialLayer(
        key="earthly_branch_foundation",
        label="지지 기반",
        source_layer="source",
        current_engine_refs=("BirthChartResult.*_pillar.branch_key", "PositionSignal.branch_main_ten_god"),
        calculation_role=(
            "생활 기반, 실제 환경, 관계의 자리, 반복되는 조건을 계산한다.",
            "천간에 드러난 글자가 실제로 지지에서 버틸 수 있는지 확인한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "수입이 실제 자산과 생활 기반으로 이어지는지 판단한다.",
            "career": "직업 환경과 조직 조건이 안정적인지 판단한다.",
            "love": "관계가 말보다 실제 생활 조건에서 유지되는지 판단한다.",
            "marriage": "배우자궁과 가정 기반의 안정성을 판단한다.",
            "personality": "반복되는 생활 반응과 현실 감각을 판단한다.",
        },
        weighting_rules=(
            "월지는 계절과 사회 환경의 중심이므로 가장 높은 기반 가중치를 둔다.",
            "일지는 관계와 결혼 판단에서 독립적으로 높은 민감도를 둔다.",
        ),
        activation_rules=(
            "운에서 지지가 합, 충, 형, 해, 파로 기존 지지를 자극하면 사건 재료로 본다.",
            "천간 신호가 지지의 같은 오행이나 지장간에서 뿌리를 얻으면 지속성을 높인다.",
        ),
        exclusion_rules=(
            "지지 기반이 약한 천간 신호는 장기 결론으로 곧장 쓰지 않는다.",
            "지지 하나만으로 직업명이나 결혼 여부를 단정하지 않는다.",
        ),
        sentence_rule=(
            "지지는 고객에게 생활 기반, 환경, 가까운 관계, 오래 반복되는 조건으로 설명한다."
        ),
    ),
    "hidden_stem_storage": AnalysisMaterialLayer(
        key="hidden_stem_storage",
        label="지장간 잠재 신호",
        source_layer="source",
        current_engine_refs=("BRANCH_HIDDEN_STEMS", "TenGodProfile.hidden_counts", "PositionSignal.hidden_ten_gods"),
        calculation_role=(
            "겉으로 바로 보이지 않는 욕구와 능력이 어떤 상황에서 선택, 관계, 일의 부담으로 이어지는지 판단한다.",
            "투출 여부와 시기 신호를 함께 보아 숨은 성향이 생활 장면에서 직접 확인되는지 살핀다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "숨은 재성이 시기 신호와 만나 수입, 거래, 지출 문제로 이어지는지 본다.",
            "career": "숨은 관성, 인성, 식상이 직무 변화와 전문성 요구로 이어지는지 본다.",
            "love": "숨은 감정, 기대, 비교심이 관계 안에서 어떤 말과 선택으로 확인되는지 본다.",
            "marriage": "배우자궁 안의 지장간이 가족, 돈, 책임 문제로 이어지는지 본다.",
            "personality": "평소에는 잘 보이지 않는 반응이 압박 상황에서 어떤 선택으로 이어지는지 본다.",
        },
        weighting_rules=(
            "지장간은 천간보다 낮은 기본 가중치를 두되, 월지와 일지 안의 지장간은 민감하게 본다.",
            "투출된 지장간은 숨은 성향이 말, 행동, 선택으로 확인된 것으로 보아 비중을 높인다.",
        ),
        activation_rules=(
            "시기에서 같은 글자가 오거나 지지가 열리면 지장간의 판단 비중을 높인다.",
            "천간에 같은 글자가 있으면 해당 지장간은 실제 행동으로 이어질 가능성을 높인다.",
        ),
        exclusion_rules=(
            "투출되지 않은 지장간만으로 고객에게 강한 사건을 단정하지 않는다.",
            "지장간의 작은 비율은 보조 근거로만 사용한다.",
        ),
        sentence_rule=(
            "지장간은 겉으로 바로 보이지 않는 욕구, 잠재 능력, 오래 쌓인 부담이 실제 생활에서 어떻게 작동하는지를 설명한다."
        ),
    ),
    "protrusion_and_rooting": AnalysisMaterialLayer(
        key="protrusion_and_rooting",
        label="투출과 통근",
        source_layer="bridge",
        current_engine_refs=("PositionSignal.protruded_hidden_stems", "ElementScore.root_count"),
        calculation_role=(
            "천간에 드러난 글자가 지지에서 실제 기반을 얻는지 판단한다.",
            "지장간의 글자가 천간에 드러나 생활 속 판단으로 보이는지 판단한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재성과 식상이 투출 또는 통근하면 수입과 자산 판단의 현실성을 높인다.",
            "career": "관성과 인성이 투출 또는 통근하면 직책, 자격, 신뢰 판단을 강화한다.",
            "love": "감정 표현 요소가 투출하면 호감과 대화가 밖으로 드러나기 쉽다.",
            "marriage": "배우자궁의 재료가 투출하면 결혼 조건이 현실 문제로 나타나기 쉽다.",
            "personality": "숨은 기준이 밖으로 드러나는지, 말과 행동으로 이어지는지 판단한다.",
        },
        weighting_rules=(
            "천간 노출과 지지 통근이 함께 있으면 지속성과 실행력을 높인다.",
            "투출은 사건의 표면화, 통근은 유지력으로 나누어 가중한다.",
        ),
        activation_rules=(
            "운에서 같은 글자가 들어오면 투출과 통근 신호를 다시 평가한다.",
            "월지 안의 지장간이 투출하면 격국과 직업 판단에 강하게 반영한다.",
        ),
        exclusion_rules=(
            "투출만 있고 뿌리가 없으면 단기 표현으로 본다.",
            "통근만 있고 천간에 드러나지 않으면 잠재력 또는 내부 조건으로 본다.",
        ),
        sentence_rule=(
            "고객에게는 겉으로 드러나는 힘과 오래 유지되는 힘을 구분해서 설명한다."
        ),
    ),
    "ten_god_distribution": AnalysisMaterialLayer(
        key="ten_god_distribution",
        label="십신 분포",
        source_layer="single",
        current_engine_refs=("ChartStructure.ten_god_profile", "TenGodProfile.group_scores"),
        calculation_role=(
            "비겁, 식상, 재성, 관성, 인성의 역할이 어느 정도 존재하는지 계산한다.",
            "각 십신이 단독으로 강한지, 서로 이어져 행동과 결론을 만드는지 판단한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재성, 식상, 비겁, 인성, 관성이 돈을 만들고 지키고 나누는 방식을 판단한다.",
            "career": "관성, 인성, 식상, 재성이 직업 역할과 성취 방식을 만든다.",
            "love": "식상, 재성, 비겁, 인성이 호감, 표현, 거리 조절을 만든다.",
            "marriage": "관성, 재성, 인성, 비겁이 책임, 생활비, 가족 조건을 만든다.",
            "personality": "십신 분포는 판단 기준, 표현 방식, 책임 반응의 핵심 재료가 된다.",
        },
        weighting_rules=(
            "천간에 드러난 십신은 외부 행동과 사건성에 높은 가중치를 둔다.",
            "지장간의 십신은 조건부 재료로 두고 투출과 운 자극을 함께 본다.",
        ),
        activation_rules=(
            "중요한 십신 조합이 형성되면 단일 십신보다 조합 작용을 우선한다.",
            "운에서 부족한 십신이 들어와 필요한 역할을 채우면 해당 영역을 강화한다.",
        ),
        exclusion_rules=(
            "십신 하나의 이름만으로 고객 문장을 만들지 않는다.",
            "재성만으로 재물운, 관성만으로 직업운을 단정하지 않는다.",
        ),
        sentence_rule=(
            "십신은 고객에게 역할, 행동 방식, 책임과 욕구의 배치로 번역한다."
        ),
    ),
    "branch_relations": AnalysisMaterialLayer(
        key="branch_relations",
        label="합충형해파",
        source_layer="relation",
        current_engine_refs=("ChartStructure.branch_interactions", "FlowSignal.branch_interactions"),
        calculation_role=(
            "지지 사이의 결합, 충돌, 부담, 분리, 손상을 계산한다.",
            "어느 궁성과 어느 오행이 자극되는지에 따라 사건 영역을 좁힌다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재성 지지와 직업궁이 자극되면 수입, 지출, 계약 변화를 본다.",
            "career": "월지와 관성 관련 지지가 자극되면 직무, 조직, 평판 변화를 본다.",
            "love": "일지와 관계 관련 지지가 자극되면 만남, 거리, 감정 충돌을 본다.",
            "marriage": "배우자궁 자극은 결혼 조건, 가족, 주거 문제를 판단하게 한다.",
            "personality": "반복되는 충돌 지점은 선택 속도와 감정 반응을 보정한다.",
        },
        weighting_rules=(
            "월지와 일지에 걸린 합충형해파는 높은 가중치를 둔다.",
            "운에서 반복 자극되는 지지는 단기 사건 가능성을 높인다.",
        ),
        activation_rules=(
            "타고난 사주의 관계 신호가 운에서 반복되면 판단 비중을 높인다.",
            "지지 관계가 천간의 핵심 십신과 연결되면 사건 판단에 반영한다.",
        ),
        exclusion_rules=(
            "합충형해파 하나만으로 이혼, 파산, 사고 같은 극단 결론을 내지 않는다.",
            "궁성과 십신 연결이 약하면 생활 장면의 변화 정도로 낮춘다.",
        ),
        sentence_rule=(
            "고객에게는 충돌이라는 말만 쓰지 않고, 어떤 생활 조건이 흔들리고 "
            "무엇을 조정해야 하는지 설명한다."
        ),
    ),
    "element_pair_relations": AnalysisMaterialLayer(
        key="element_pair_relations",
        label="오행 배합",
        source_layer="relation",
        current_engine_refs=("ChartStructure.element_combination_profile", "ChartStructure.directional_interaction_profile"),
        calculation_role=(
            "오행 두 개 이상이 생하거나 극하면서 만드는 행동과 결과를 계산한다.",
            "십신 이름으로 바꾸기 전의 물상적 특성을 따로 보존한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "생산, 유통, 보존, 소비, 관리의 성질을 오행 배합으로 판단한다.",
            "career": "기획, 실행, 표현, 평가, 관리의 업무 성향을 판단한다.",
            "love": "감정 표현, 반응 속도, 거리 조절, 매력의 질감을 판단한다.",
            "marriage": "생활 기반, 따뜻함과 냉정함, 현실 처리 방식을 판단한다.",
            "personality": "행동의 속도, 사고의 방향, 압박 대응의 체질을 판단한다.",
        },
        weighting_rules=(
            "월령에서 필요한 오행 배합이면 높은 가중치를 둔다.",
            "이미 과한 오행을 더 키우는 배합은 장점보다 부담을 함께 계산한다.",
        ),
        activation_rules=(
            "천간에 함께 드러난 오행 배합은 대외 행동으로 강하게 활성화한다.",
            "지장간 배합은 투출되거나 운에서 자극될 때 활성화한다.",
        ),
        exclusion_rules=(
            "오행 배합만으로 십신 역할을 대체하지 않는다.",
            "월령과 일간 수용값을 보지 않고 배합 문장을 그대로 출력하지 않는다.",
        ),
        sentence_rule=(
            "오행 배합은 고객에게 행동의 질감과 결과가 만들어지는 방식으로 설명한다."
        ),
    ),
    "directional_stem_relations": AnalysisMaterialLayer(
        key="directional_stem_relations",
        label="천간 상호 수용",
        source_layer="relation",
        current_engine_refs=("ChartStructure.directional_interaction_profile", "STEM_DIRECTION_RULES"),
        calculation_role=(
            "甲이 乙을 보는 것과 乙이 甲을 보는 차이처럼 방향성을 계산한다.",
            "같은 두 글자라도 어느 쪽이 주체가 되는지에 따라 체감과 행동을 구분한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "돈과 사람, 계약, 기술을 어느 쪽이 주도하는지 판단한다.",
            "career": "역할 간의 주도권, 평가를 받는 방식, 전문성 사용 방식을 판단한다.",
            "love": "상대에게 다가가는 방식과 상대를 해석하는 방식을 구분한다.",
            "marriage": "배우자와 책임을 보는 방식, 생활 기준을 조율하는 방식을 판단한다.",
            "personality": "자신이 먼저 움직이는지, 외부 조건을 받아 해석하는지 판단한다.",
        },
        weighting_rules=(
            "일간이 주체가 되는 수용값은 성향과 체감 판단에 높은 가중치를 둔다.",
            "월간과 시간의 방향 관계는 직업과 장기 결과 판단에서 보조 가중치를 둔다.",
        ),
        activation_rules=(
            "천간 두 글자가 모두 드러나고 위치가 가까우면 강하게 활성화한다.",
            "운에서 한쪽 글자가 들어와 타고난 사주의 다른 글자와 관계를 만들면 해당 기간의 판단 비중을 높인다.",
        ),
        exclusion_rules=(
            "방향을 구분하지 않은 천간 쌍 문장은 고객 출력에 쓰지 않는다.",
            "일간과 무관한 천간 관계는 성향 결론으로 바로 올리지 않는다.",
        ),
        sentence_rule=(
            "천간 수용은 고객에게 무엇을 먼저 의식하고, 어떤 책임이나 기회를 어떻게 처리하는지로 설명한다."
        ),
    ),
    "ten_god_pair_relations": AnalysisMaterialLayer(
        key="ten_god_pair_relations",
        label="십신 배합",
        source_layer="relation",
        current_engine_refs=("ChartStructure.ten_god_interaction_profile", "TEN_GOD_DIRECTION_RULES"),
        calculation_role=(
            "십신 두 개가 만나 역할의 순서와 결론을 만드는 방식을 계산한다.",
            "식상생재, 재생관, 관인상생처럼 생산과 결실의 연결 여부를 본다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "수입 전환, 분배, 계약, 보존, 손실 방어의 역할 연결을 판단한다.",
            "career": "성과, 책임, 자격, 평가, 조직 신뢰의 연결을 판단한다.",
            "love": "표현, 호감, 책임, 확인 욕구가 어떻게 이어지는지 판단한다.",
            "marriage": "감정, 돈, 약속, 가족 책임이 어떤 순서로 연결되는지 판단한다.",
            "personality": "욕구, 표현, 책임, 신뢰 확인이 행동으로 이어지는 방식을 판단한다.",
        },
        weighting_rules=(
            "월령과 격국상 필요한 십신 연결이면 높은 가중치를 둔다.",
            "역할 연결이 중간에서 끊기거나 충돌하면 반대 신호를 함께 계산한다.",
        ),
        activation_rules=(
            "천간에 드러난 십신 배합은 외부 사건으로 강하게 활성화한다.",
            "운에서 빠진 십신이 들어와 연결을 완성하면 해당 영역의 사건 가능성을 높인다.",
        ),
        exclusion_rules=(
            "십신 배합 이름만으로 고객 문장을 만들지 않는다.",
            "오행 물상과 위치, 월령 보정을 거치지 않은 십신 배합은 최종 결론으로 쓰지 않는다.",
        ),
        sentence_rule=(
            "십신 배합은 고객에게 행동이 어떤 보상, 책임, 관계 결과로 이어지는지로 설명한다."
        ),
    ),
    "day_stem_reception": AnalysisMaterialLayer(
        key="day_stem_reception",
        label="일간별 천간 수용값",
        source_layer="relation",
        current_engine_refs=("ChartStructure.stem_reception_profile", "STEM_RECEPTION_RULES"),
        calculation_role=(
            "일간이 특정 천간을 어떤 사람, 책임, 돈, 표현으로 체감하는지 계산한다.",
            "오행으로 보는 체감과 십신으로 보는 역할을 함께 보존한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "일간이 재성, 식상, 비겁을 어떻게 받아 돈 문제로 처리하는지 판단한다.",
            "career": "일간이 관성, 인성, 식상을 어떻게 받아 직업 역할로 처리하는지 판단한다.",
            "love": "일간이 상대, 표현, 기대, 거리 문제를 어떻게 느끼고 처리하는지 판단한다.",
            "marriage": "일간이 책임, 생활비, 가족 조건을 어떤 부담이나 안정으로 느끼는지 판단한다.",
            "personality": "해당 글자를 만났을 때의 체감, 행동 성향, 피로 지점을 판단한다.",
        },
        weighting_rules=(
            "일간과 가까운 천간, 월간, 시간 신호는 체감 가중치를 높인다.",
            "월령이 해당 천간을 살리거나 약하게 만들면 수용값을 보정한다.",
        ),
        activation_rules=(
            "타고난 천간과 지장간 주기가 일간 수용값을 만들면 기본 판단값으로 둔다.",
            "운에서 같은 천간이 들어오면 해당 수용값을 시기 판단에 반영한다.",
        ),
        exclusion_rules=(
            "일간별 수용값만으로 영역 결론을 확정하지 않는다.",
            "맞는 조건과 맞지 않는 조건은 계산층이 아니라 적용층과 주의층에 둔다.",
        ),
        sentence_rule=(
            "일간 수용값은 고객에게 특정 사람, 책임, 돈, 표현을 어떻게 체감하고 처리하는지로 설명한다."
        ),
    ),
    "integrated_pair_action": AnalysisMaterialLayer(
        key="integrated_pair_action",
        label="오행과 십신의 결합 작용",
        source_layer="relation",
        current_engine_refs=("ChartStructure.integrated_saju_profile", "IntegratedSajuSignal.domain_projection"),
        calculation_role=(
            "오행 물상과 십신 역할을 합쳐 실제 행동과 결론을 계산한다.",
            "생과 극이 결합해 생산, 통제, 보상, 책임으로 이어지는지를 본다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "생산이 수입으로 이어지는지, 통제가 자산 보존으로 이어지는지 판단한다.",
            "career": "성과가 책임으로 이어지는지, 압박이 전문성으로 바뀌는지 판단한다.",
            "love": "표현이 호감으로 이어지는지, 책임이 안정으로 이어지는지 판단한다.",
            "marriage": "감정, 돈, 책임, 생활 기준이 서로 지탱하는지 판단한다.",
            "personality": "행동의 원인과 결과가 일관되는지, 중간에서 소모되는지 판단한다.",
        },
        weighting_rules=(
            "오행과 십신 판단이 같은 결론을 가리키면 높은 확신도로 본다.",
            "오행은 유리하지만 십신 역할이 불리하면 양면 판단으로 분리한다.",
        ),
        activation_rules=(
            "두 글자 이상이 위치, 월령, 투출, 통근에서 함께 힘을 얻으면 활성화한다.",
            "운에서 연결의 빠진 고리가 들어오면 해당 사건 영역을 강화한다.",
        ),
        exclusion_rules=(
            "오행 문장과 십신 문장을 단순히 이어 붙이지 않는다.",
            "중간 연결이 약한데도 완성된 결과처럼 말하지 않는다.",
        ),
        sentence_rule=(
            "결합 작용은 고객에게 어떤 성향이 어떤 행동을 만들고, 그 행동이 어떤 결과로 "
            "이어지는지 한 문단 안에서 설명한다."
        ),
    ),
    "cycle_regulation": AnalysisMaterialLayer(
        key="cycle_regulation",
        label="상생상극 순환과 제어",
        source_layer="relation",
        current_engine_refs=(
            "cycle_regulation.build_cycle_regulation_profile",
            "judgment_context.material_layers[layer=cycle_regulation]",
        ),
        calculation_role=(
            "오행 생극과 십신 생극을 분리 계산한 뒤 같은 결론을 가리키는지 확인한다.",
            "재생관으로 비겁을 제어하는지, 재극인으로 도식을 푸는지 같은 연쇄 조절을 계산한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "비겁극재, 식상생재, 재생관, 재극인의 길흉을 월령 기준으로 나누어 판단한다.",
            "career": "식상제살, 관인상생, 재생관이 직책, 평가, 실무 처리로 이어지는지 판단한다.",
            "love": "식상, 재성, 관성, 인성이 감정 표현과 책임 기준을 어떻게 조절하는지 판단한다.",
            "marriage": "재성, 관성, 인성이 생활비, 책임, 보호 기준을 서로 지탱하는지 판단한다.",
            "personality": "생조와 극제의 반복이 행동 속도, 판단 기준, 방어 방식을 어떻게 만드는지 판단한다.",
        },
        weighting_rules=(
            "월령과 격국상 필요한 기운이 부담 기운을 제어하면 높은 가중치를 둔다.",
            "필요한 기운이 극을 받아 손상되면 같은 조합이라도 감점한다.",
            "생하는 쪽이 부담 기운이면 장점이 아니라 부담 확대 신호로 계산한다.",
        ),
        activation_rules=(
            "원국에 약하게라도 존재하는 고리는 판단에 남기되, 투출·통근·월지 작용에 따라 강도를 조절한다.",
            "운에서 빠진 고리가 들어와 생극 연쇄가 완성되면 해당 시기 판단에 반영한다.",
            "오행 관계와 십신 역할이 같은 방향이면 강한 신호로 올린다.",
        ),
        exclusion_rules=(
            "상생이면 무조건 길하고 상극이면 무조건 흉하다고 판정하지 않는다.",
            "오행상 제어가 가능해 보여도 십신상 비겁극재처럼 손실을 동반하면 양면 판단으로 둔다.",
            "월령 기준에서 필요한 기운이 아닌 경우에는 생극 이름만으로 결론을 확정하지 않는다.",
        ),
        sentence_rule=(
            "고객에게 직접 보일 때는 생극 이름보다 돈, 책임, 몫, 문서, 결과물, 보호 장치가 "
            "어떻게 서로를 키우거나 막는지로 설명한다."
        ),
    ),
    "structure_useful_elements": AnalysisMaterialLayer(
        key="structure_useful_elements",
        label="격국과 필요한 요소",
        source_layer="synthesis",
        current_engine_refs=("ChartStructure.pattern_profile", "PatternProfile.useful_element_candidates"),
        calculation_role=(
            "월령을 중심으로 격국 후보와 필요한 요소를 판단한다.",
            "같은 조합이라도 명식에 필요한 요소인지, 이미 과한 요소인지 구분한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재성 또는 재성을 돕는 요소가 격국상 필요한지에 따라 재물 결론을 보정한다.",
            "career": "관성, 인성, 식상이 격국을 살리는지 해치는지에 따라 직업 결론을 보정한다.",
            "love": "관계 안정 요소가 명식에 필요한지, 부담을 키우는지 판단한다.",
            "marriage": "결혼 안정 요소가 필요한 균형인지 과한 책임인지 판단한다.",
            "personality": "명식이 요구하는 태도와 실제 성향의 차이를 판단한다.",
        },
        weighting_rules=(
            "월령이 지지하는 격국 후보는 기본 가중치를 높인다.",
            "격국을 살리는 요소와 해치는 요소는 같은 오행이라도 다르게 처리한다.",
        ),
        activation_rules=(
            "운에서 필요한 요소가 들어오면 회복, 성취, 정리의 재료로 본다.",
            "운에서 격국을 해치는 요소가 강해지면 주의층을 강화한다.",
        ),
        exclusion_rules=(
            "격국 후보의 확신도가 낮으면 강한 상품 결론으로 쓰지 않는다.",
            "격국명만 고객에게 노출해 설명을 대신하지 않는다.",
        ),
        sentence_rule=(
            "격국과 필요한 요소는 고객에게 당신의 사주가 무엇을 얻을 때 안정되고, "
            "무엇이 과해질 때 부담이 커지는지로 설명한다."
        ),
    ),
    "auxiliary_references": AnalysisMaterialLayer(
        key="auxiliary_references",
        label="보조 신호",
        source_layer="support",
        current_engine_refs=("ChartStructure.auxiliary_profile", "AuxiliaryProfile.sal_by_position"),
        calculation_role=(
            "십이운성, 12신살 등 보조 신호를 생활 장면의 보정 재료로 사용한다.",
            "정통 구조 판단을 대체하지 않고 세부 뉘앙스를 보완한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "이동, 대외 접촉, 반복 수입 같은 보조 장면을 보강한다.",
            "career": "활동성, 이동성, 대외 평가의 세부 모습을 보강한다.",
            "love": "매력, 접촉 증가, 관계 민감도를 보조적으로 판단한다.",
            "marriage": "가족 거리, 생활 변화, 장기 부담의 세부 장면을 보강한다.",
            "personality": "기본 성향 위에 활동성, 예민성, 회복력의 뉘앙스를 더한다.",
        },
        weighting_rules=(
            "보조 신호는 단독 가중치를 낮게 둔다.",
            "타고난 핵심 신호와 같은 결론을 가리킬 때만 문장 근거로 사용한다.",
        ),
        activation_rules=(
            "운 자극과 같은 영역을 가리킬 때 보조 설명으로 활성화한다.",
            "위치가 명확하고 기존 근거와 일치할 때 고객 문장에 제한적으로 반영한다.",
        ),
        exclusion_rules=(
            "보조 신호 하나만으로 결혼, 사고, 파산, 질병을 단정하지 않는다.",
            "핵심 구조와 반대되는 보조 신호는 고객 결론으로 올리지 않는다.",
        ),
        sentence_rule=(
            "보조 신호는 고객에게 단정적 사건명보다 성향의 세부 모습과 생활 장면의 보조 설명으로 쓴다."
        ),
    ),
    "fortune_activation": AnalysisMaterialLayer(
        key="fortune_activation",
        label="대운·세운·월운 자극",
        source_layer="fortune",
        current_engine_refs=("AnalysisResult.flow_signals", "FlowSignal.sub_period_signals"),
        calculation_role=(
            "타고난 사주 안의 성향과 역할이 언제 구체적인 선택과 사건으로 이어지는지 판단한다.",
            "대운, 세운, 월운을 나누어 넓은 환경과 구체적 사건 시점을 구분한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "재물 재료가 운에서 활성화될 때 수입, 지출, 계약, 투자 시기를 판단한다.",
            "career": "직업 재료가 운에서 활성화될 때 역할 변화, 평가, 책임 증가를 판단한다.",
            "love": "관계 재료가 운에서 활성화될 때 만남, 호감, 거리 조정을 판단한다.",
            "marriage": "결혼 재료가 운에서 활성화될 때 약속, 가족, 주거, 현실 조건을 판단한다.",
            "personality": "운 자극이 강해지는 시기에 평소 성향이 어떤 선택으로 드러나는지 판단한다.",
        },
        weighting_rules=(
            "대운은 환경, 세운은 연도 사건, 월운은 구체적 체감 시점으로 나누어 가중한다.",
            "타고난 사주에 약한 요소가 운에만 들어오면 단기 기회로 보되 지속성은 낮게 둔다.",
        ),
        activation_rules=(
            "운이 타고난 천간, 지지, 지장간, 궁성과 맞물릴 때 판단 비중을 높인다.",
            "대운과 세운이 같은 영역을 반복해서 건드리면 우선순위를 높인다.",
        ),
        exclusion_rules=(
            "운에 좋은 글자가 들어왔다는 이유만으로 사건을 확정하지 않는다.",
            "타고난 수용력과 격국 필요성을 보지 않은 시기 판단은 쓰지 않는다.",
        ),
        sentence_rule=(
            "운 판단은 고객에게 몇 년에 무엇이 좋아진다는 식으로만 말하지 않고, "
            "어떤 현실 기준이 갖춰질 때 사건으로 나타나는지 함께 설명한다."
        ),
    ),
    "flow_branch_relations": AnalysisMaterialLayer(
        key="flow_branch_relations",
        label="운에서 들어오는 합충형해파",
        source_layer="fortune",
        current_engine_refs=("FlowSignal.branch_interactions", "EventPacket.basis_codes"),
        calculation_role=(
            "세운과 대운이 타고난 지지를 건드릴 때 생기는 결합, 충돌, 반복 부담을 계산한다.",
            "해당 연도에 돈, 일, 관계, 결혼 사건이 어느 자리에서 발생하는지 구분한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "세운과 대운이 재물궁 또는 재성 지지를 건드리면 정산, 지출, 계약 사건을 판단한다.",
            "career": "세운과 대운이 월지 또는 관성 지지를 건드리면 역할 변화와 평가 문제를 판단한다.",
            "love": "세운과 대운이 일지 또는 관계 지지를 건드리면 만남, 거리, 감정 충돌을 판단한다.",
            "marriage": "세운과 대운이 배우자궁을 건드리면 생활 기준, 가족, 주거 논의를 판단한다.",
            "personality": "세운과 대운이 반복해서 건드리는 지지는 그 해 선택 방식과 감정 반응을 보정한다.",
        },
        weighting_rules=(
            "세운과 대운이 같은 지지를 함께 건드리면 해당 연도의 사건성을 높인다.",
            "일지와 월지에 걸린 운의 충·형·파·해는 관계와 직업 판단에서 높은 가중치를 둔다.",
        ),
        activation_rules=(
            "운의 지지 관계가 이벤트 패킷의 영역과 일치할 때 리포트 앞단 사건 문장으로 올린다.",
            "원국에 이미 있던 합충형해파가 운에서 반복되면 해당 사건의 반복성과 강도를 높인다.",
        ),
        exclusion_rules=(
            "운의 지지 관계 하나만으로 파산, 이혼, 사고 같은 극단 결론을 내지 않는다.",
            "궁성, 십신, 월령과 연결되지 않은 운 관계는 고객 결론보다 보조 설명으로 낮춘다.",
        ),
        sentence_rule=(
            "고객 문장에서는 그 해에 어느 문제가 먼저 불거지는지 말하고, "
            "합·충·형·파·해의 이름은 근거 문단에서만 짧게 밝힌다."
        ),
    ),
    "calibration_feedback": AnalysisMaterialLayer(
        key="calibration_feedback",
        label="과거 사건 검증",
        source_layer="calibration",
        current_engine_refs=("AnalysisResult.calibration_profile", "PastEventAnswer"),
        calculation_role=(
            "사용자가 입력한 과거 사건과 엔진 판단이 맞는지 비교한다.",
            "민감한 질문 없이 영역별 확신도와 시기 민감도를 보정한다.",
        ),
        domain_targets=("money", "career", "love", "marriage", "personality"),
        domain_usage={
            "money": "과거 수입, 지출, 직업 보상 사건이 맞으면 재물 시기 확신도를 높인다.",
            "career": "과거 역할 변화와 평가 사건이 맞으면 직업 판단의 우선순위를 조정한다.",
            "love": "관계 시작, 거리 조정, 갈등 경험이 맞으면 관계 판단을 보정한다.",
            "marriage": "결혼 준비, 가족, 주거, 책임 사건이 맞으면 결혼 조건 판단을 보정한다.",
            "personality": "사용자의 선택 방식이 반복적으로 확인되면 성향 보정값을 안정화한다.",
        },
        weighting_rules=(
            "과거 사건 검증은 타고난 구조를 바꾸지 않고 확신도와 우선순위만 보정한다.",
            "일치 사례가 많아도 명식에 없는 재료를 새로 만들지 않는다.",
        ),
        activation_rules=(
            "사용자가 사건 입력을 제공한 경우에만 활성화한다.",
            "영역과 연도가 함께 맞으면 해당 영역의 시기 판단을 강화한다.",
        ),
        exclusion_rules=(
            "사건 입력이 없을 때 임의로 과거를 꾸며 보정하지 않는다.",
            "불일치가 있어도 명식 산출 자체를 자동으로 바꾸지 않는다.",
        ),
        sentence_rule=(
            "과거 검증은 고객에게 부담을 주지 않도록 간단한 선택 결과로만 반영하고, "
            "강도나 피해 규모를 묻는 방식으로 확장하지 않는다."
        ),
    ),
}


def analysis_material_for(key: str) -> AnalysisMaterialLayer:
    try:
        return ANALYSIS_MATERIAL_LAYERS[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported analysis material key: {key}") from exc


def interpretation_stage_for(key: str) -> str:
    try:
        return MATERIAL_INTERPRETATION_STAGES[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported analysis material stage key: {key}") from exc


def material_domain_priority_for(key: str) -> dict[str, str]:
    try:
        return MATERIAL_DOMAIN_PRIORITIES[key]
    except KeyError as exc:
        raise ValueError(f"Unsupported analysis material priority key: {key}") from exc
