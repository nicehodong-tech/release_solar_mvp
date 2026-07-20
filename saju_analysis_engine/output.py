"""Product-tier output assembly and risk-language filtering."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import re

from .models import (
    AnalysisResult,
    EventPacket,
    ProductOutput,
    ProductOutputItem,
    ProductOutputSection,
    ProductTier,
    RiskFilterResult,
)
from .constants import DOMAIN_ORDER
from .manifest import build_engine_manifest
from .catalog_content import CURRENT_FORTUNE_YEAR, attach_catalog_content_blocks
from .judgment_core import PATTERN_LABELS, build_domain_judgment_context
from .product_catalog import TIER_DEFINITIONS, catalog_payload_for_tier, tier_definition
from .premium_category_topics import (
    premium_product_surface_contract,
    premium_profile_category_contract,
)
from .output_goals import output_goal_contracts
from .rendering import DOMAIN_LABELS, PHASE_LABELS
from .timing_scoring import timing_activation_modifier, timing_base_score
from .section_candidate_output import build_candidate_report_sections
from .section_selection import build_section_selection
from .premium_detail_selection import build_premium_detail_selection
from .source_personality_profiles import source_personality_profile_payload
from .source_reading_profiles import source_reading_profile_payload
from .auxiliary import (
    TWELVE_SINSAL_LABELS,
    TWELVE_SINSAL_MEANINGS,
    build_annual_shinsal_signals,
)
from .features import DOMAIN_AXIS_LINKS, GYEOKGUK_CLASSICAL_AXIS_EFFECTS, GYEOKGUK_DOMAIN_ALIASES
from .gyeokguk_ten_god_actions import (
    CLASSICAL_ACTION_MECHANICS,
    CLASSICAL_ACTION_MECHANIC_TEXTS,
    TEN_GOD_EXACT_ACTION_PROFILE,
    TEN_GOD_EXACT_NUANCE,
)
from .gyeokguk_dual_ten_god_actions import TEN_GOD_OPERATION_FACE
from .keyword_profiles import (
    annotate_shinsal_structure_alignment,
    branch_relation_keyword_profiles,
    shinsal_keyword_profiles,
)
from .metric_adjudication import adjudicate_natal_metric


PROHIBITED_DETERMINISTIC_TERMS = {
    "반드시": "deterministic_claim",
    "확정": "deterministic_claim",
    "무조건": "deterministic_claim",
    "사망": "high_risk_health",
    "암": "high_risk_health",
    "질병": "high_risk_health",
    "소송": "legal_claim",
    "파산": "financial_claim",
}

TIER_LIMITS = {tier: definition.item_limit for tier, definition in TIER_DEFINITIONS.items()}

PRODUCT_OUTPUT_SCHEMA_VERSION = "analysis_product_v1"

SECTION_DETAIL_LEVEL = {tier: definition.detail_level for tier, definition in TIER_DEFINITIONS.items()}

ELEMENT_LABELS = {
    "wood": "목",
    "fire": "화",
    "earth": "토",
    "metal": "금",
    "water": "수",
}

TEN_GOD_LABELS = {
    "bi_gyeon": "비견",
    "geob_jae": "겁재",
    "sik_sin": "식신",
    "sang_gwan": "상관",
    "pyeon_jae": "편재",
    "jeong_jae": "정재",
    "pyeon_gwan": "편관",
    "jeong_gwan": "정관",
    "pyeon_in": "편인",
    "jeong_in": "정인",
}

BRANCH_LABELS = {
    "ja": "子",
    "chuk": "丑",
    "in": "寅",
    "myo": "卯",
    "jin": "辰",
    "sa": "巳",
    "o": "午",
    "mi": "未",
    "sin": "申",
    "yu": "酉",
    "sul": "戌",
    "hae": "亥",
}

SEASON_LABELS = {
    "spring": "봄",
    "summer": "여름",
    "autumn": "가을",
    "winter": "겨울",
    "late_spring": "늦봄",
    "late_summer": "환절기",
    "late_autumn": "늦가을",
    "late_winter": "늦겨울",
}

POSITION_LABELS = {
    "year": "연지",
    "month": "월지",
    "day": "일지",
    "hour": "시지",
}

BRANCH_RELATION_LABELS = {
    "six_combine": "육합",
    "clash": "충",
    "punishment": "형",
    "harm": "해",
    "break": "파",
    "self_punishment": "자형",
    "three_harmony": "삼합",
    "three_harmony_half": "반합",
    "three_meeting": "방합",
}

COVERAGE_LABELS = {
    "included": "이번 상품에 포함된 영역입니다.",
    "omitted_by_tier": "분석은 되었지만 현재 상품 등급에서는 생략된 영역입니다.",
    "restricted": "신뢰도 또는 안전 기준상 출력이 제한된 영역입니다.",
    "not_generated": "이번 요청에서 생성되지 않은 영역입니다.",
}

CALIBRATION_LABELS = {
    "not_checked": "과거 사건 검증을 적용하지 않은 결과입니다.",
    "matched": "입력한 과거 사건과 명식의 시기 반응이 강하게 맞아 신뢰도를 보강했습니다.",
    "partially_matched": "입력한 과거 사건과 일부 시기 반응이 맞아 신뢰도를 부분 보강했습니다.",
    "weakly_matched": "입력한 과거 사건과 일부 차이가 있어 확인 가능한 시기 반응 위주로 정리했습니다.",
    "skipped": "과거 사건 검증을 건너뛰어 기본 판단으로 출력합니다.",
}

RELATIONSHIP_STATUS_LABELS = {
    "single": "미혼/현재 관계 없음",
    "interested": "관심 대상 있음",
    "dating": "연애 중",
    "long_term": "장기 연애 중",
    "preparing_marriage": "결혼 준비 중",
    "married": "기혼",
    "unknown": "관계 상태 미입력",
}

BASIS_EXPLANATION_RULES = (
    ("year_stem_", "해당 연도의 천간 십신이 이 영역을 직접 자극한다."),
    ("year_branch_", "해당 연도의 지지와 지장간이 사건의 실제 형태를 정한다."),
    ("daeun_stem_", "대운 천간이 장기적인 방향을 정한다."),
    ("daeun_branch_", "대운 지지가 타고난 배열과 부딪히며 사건 압력을 높인다."),
    ("useful_element_", "필요한 오행이 이 영역의 판단을 받쳐 준다."),
    ("annual_pillar_", "해당 세운이 타고난 성향과 연결됩니다."),
    ("annual_travel_horse", "역마 성향이 이동, 변동, 외부 활동을 키운다."),
    ("annual_peach_blossom", "도화 성향이 매력, 노출, 관계 접점을 키운다."),
    ("daeun_fire_trine", "대운의 삼합·반합이 특정 오행의 힘을 장기적으로 키웁니다."),
    ("daeun_water_trine", "대운의 삼합·반합이 특정 오행의 힘을 장기적으로 키웁니다."),
    ("daeun_metal_trine", "대운의 삼합·반합이 특정 오행의 힘을 장기적으로 키웁니다."),
    ("daeun_wood_trine", "대운의 삼합·반합이 특정 오행의 힘을 장기적으로 키웁니다."),
    ("year_water_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("year_fire_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("year_metal_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("year_wood_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("fire_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("water_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("metal_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("wood_trine", "삼합·반합 계열이 특정 오행의 힘을 키웁니다."),
    ("flow_relation_", "해당 시기의 합·충·형·해·파가 사건성을 높입니다."),
    ("annual_stem_useful_element_", "세운 천간이 격국과 월령에 필요한 기운을 겉으로 올립니다."),
    ("annual_branch_main_useful_element_", "세운 지지가 필요한 기운을 생활 속 사건으로 바꿉니다."),
    ("annual_branch_hidden_", "세운 지지의 지장간이 숨은 재료를 움직입니다."),
    ("daeun_stem_useful_element_", "대운 천간이 장기적으로 필요한 기운을 보강합니다."),
    ("daeun_branch_main_useful_element_", "대운 지지가 장기적인 생활 기반에서 필요한 기운을 움직입니다."),
    ("daeun_branch_hidden_", "대운 지지의 지장간에 있던 숨은 재료가 장기 배경이 됩니다."),
    ("pattern_month_command_", "월령의 십신이 이 영역에서 가장 먼저 보아야 할 기준이 됩니다."),
    ("month_governance_supports_month_command", "월령 기준에서 필요한 기운이 살아 판단의 중심 근거가 됩니다."),
    ("month_governance_usable_by_month_command", "월령 기준에서 활용 가능한 기운으로 판단에 반영됩니다."),
    ("month_governance_mixed_by_month_command", "월령 기준에서 장점과 부담이 함께 있는 기운으로 구분됩니다."),
    ("month_governance_neutral_to_month_command", "월령 기준에서는 보조적으로만 쓰이는 기운입니다."),
    ("month_governance_touches_month_branch", "월지와 직접 맞닿은 신호라 현실 작용 비중이 높습니다."),
    ("month_governance_flow_activation", "대운·세운에서 원국의 월령 구조를 건드린 신호입니다."),
    ("month_governance_element_useful_", "월령과 격국에서 필요성이 확인된 오행입니다."),
    ("month_governance_johu_need_", "조후상 보완이 필요한 오행으로 판단에 반영됩니다."),
    ("month_governance_visible_", "천간에 드러나 실제 선택과 행동으로 나타나기 쉽습니다."),
    ("month_governance_rooted_", "지지와 지장간에 뿌리를 두어 생활 기반에서 작용합니다."),
    ("month_governance_role_", "오행을 십신 역할로 바꿔 월령 기준에 맞추어 판정했습니다."),
    ("element_dominance", "특정 오행이 강하게 모여 사주의 성향과 사건 방향을 분명하게 만듭니다."),
    ("wood_excess", "목 기운이 강해 성장, 확장, 관계 형성의 성향이 두드러집니다."),
    ("fire_excess", "화 기운이 강해 표현, 노출, 속도감이 두드러집니다."),
    ("earth_excess", "토 기운이 강해 현실 판단, 보유력, 책임 의식이 두드러집니다."),
    ("metal_excess", "금 기운이 강해 기준, 정리, 판단의 선명함이 두드러집니다."),
    ("water_excess", "수 기운이 강해 사고력, 정보 감각, 유연성이 두드러집니다."),
    ("wood_lack", "목 기운이 약해 성장 방향과 관계 확장력을 따로 보완해야 합니다."),
    ("fire_lack", "화 기운이 약해 표현력과 추진 속도를 따로 보완해야 합니다."),
    ("earth_lack", "토 기운이 약해 현실 기반과 보유력을 따로 보완해야 합니다."),
    ("metal_lack", "금 기운이 약해 기준 설정과 정리 능력을 따로 보완해야 합니다."),
    ("water_lack", "수 기운이 약해 정보력과 유연한 판단을 따로 보완해야 합니다."),
    ("johu_needs_wood", "조후상 목 기운이 보완될 때 성장 방향과 생동감이 살아납니다."),
    ("johu_needs_fire", "조후상 화 기운이 보완될 때 표현력과 추진력이 살아납니다."),
    ("johu_needs_earth", "조후상 토 기운이 보완될 때 현실 기반과 균형감이 살아납니다."),
    ("johu_needs_metal", "조후상 금 기운이 보완될 때 기준과 정리력이 살아납니다."),
    ("johu_needs_water", "조후상 수 기운이 보완될 때 사고력과 조절력이 살아납니다."),
    ("month_branch_element_", "월지의 본기가 판단의 기본 환경으로 작용합니다."),
    ("month_hidden_element_", "월지 지장간에 깔린 기운이 현실 배경을 이룹니다."),
    ("month_hidden_protruded_", "월지 지장간의 기운이 천간으로 드러나 작동력이 높습니다."),
    ("month_command_", "월령 십신이 판단의 기본 기준으로 작용합니다."),
    ("regular_pattern_", "월령에서 잡힌 격국 후보가 판단에 반영됩니다."),
    ("season_", "월령의 계절 조건이 판단 기준에 들어갑니다."),
    ("yangren_needs_officer_control", "양인격에서는 강한 자기 기운을 관성으로 정리할 때 책임과 성취가 분명해집니다."),
    ("yangren_uses_output_release", "양인격에서는 강한 기운을 식상으로 풀어낼 때 기술과 결과물이 살아납니다."),
    ("peer_pattern_needs_officer", "비겁격에서는 관성이 들어와야 자기 기준이 책임과 질서로 정리됩니다."),
    ("peer_pattern_uses_output", "비겁격에서는 식상으로 풀어낼 때 독립성과 주도성이 결과물로 바뀝니다."),
    ("weak_day_master", "일간의 힘이 약해 보완 기운과 생활 기반을 먼저 살핍니다."),
    ("very_weak_day_master", "일간의 힘이 매우 약해 받쳐 주는 기운과 뿌리를 우선합니다."),
    ("balanced_day_master", "일간의 힘이 한쪽으로 치우치지 않아 결과, 재물, 책임의 연결을 판단합니다."),
    ("strong_day_master", "일간의 힘이 강해 그 힘을 결과, 재물, 책임으로 돌리는지가 중요합니다."),
    ("very_strong_day_master", "일간의 힘이 매우 강해 힘을 제어하고 밖으로 쓰는 구조를 우선합니다."),
    ("output_use", "식상으로 기운을 풀어 결과물과 실무 능력을 만드는 구조입니다."),
    ("wealth_use", "재성으로 힘을 현실 이익과 선택으로 바꾸는 구조입니다."),
    ("officer_use", "관성으로 강한 기운에 질서와 책임을 세우는 구조입니다."),
    ("resource_support", "인성이 일간을 받쳐 판단과 기반을 보강합니다."),
    ("same_element_root", "같은 오행의 뿌리가 일간을 받쳐 줍니다."),
    ("eating_god_generates_wealth", "식신이 재성으로 이어져 만든 결과가 수입과 재물로 연결됩니다."),
    ("eating_god_results_enter_responsibility", "식신의 결과물이 책임 있는 자리와 평가로 이어집니다."),
    ("eating_god_controls_seven_killings", "식신이 편관의 압박을 다스려 어려운 일을 실무로 풀어냅니다."),
    ("seven_killings_transforms_to_resource", "편관의 압박이 인성으로 이어져 자격, 근거, 신뢰로 바뀝니다."),
    ("hurting_officer_generates_wealth", "상관이 재성으로 이어져 기획, 말, 개선 능력이 수입으로 연결됩니다."),
    ("hurting_officer_needs_resource_refinement", "상관의 표현력은 인성의 근거와 자격을 얻을 때 평가가 안정됩니다."),
    ("indirect_wealth_supports_officer", "편재가 관성을 받쳐 외부 기회가 책임 있는 자리로 이어집니다."),
    ("output_sources_indirect_wealth", "식상이 편재로 이어져 만든 결과가 거래와 외부 수입으로 바뀝니다."),
    ("direct_wealth_supports_officer", "정재가 관성을 받쳐 안정 수입과 책임 기준이 함께 잡힙니다."),
    ("output_sources_direct_wealth", "식상이 정재로 이어져 꾸준한 결과가 안정 수입으로 바뀝니다."),
    ("officer_resource_sequence", "관성이 인성으로 이어져 책임이 자격, 문서, 신뢰로 정리됩니다."),
    ("wealth_supports_officer", "재성이 관성을 받쳐 돈, 성과, 책임이 공식적인 평가로 이어집니다."),
    ("pattern_useful_event_", "격국상 필요한 기운이 이 시기의 좋은 결과를 키웁니다."),
    ("pattern_reason_support_", "격국의 세부 작용이 이 영역에서 좋은 결과를 만드는 근거가 됩니다."),
    ("pattern_useful_active_", "운에서 필요한 기운이 강해져 결과가 또렷해집니다."),
    ("pattern_caution_also_needed_", "필요한 기운의 과도한 작용도 따로 기록합니다."),
    ("cycle_regulation_", "상생상극의 생조와 극제가 이 영역의 기회와 부담을 조절합니다."),
    ("cycle_flow_activation_", "대운·세운이 원국의 생극 사슬을 건드리는 지점입니다."),
    ("cycle_flow_governance_", "대운·세운이 월령·격국 기준으로 중요한 생극 지점을 다시 건드립니다."),
    ("cycle_flow_pattern_", "대운·세운이 해당 격국에서 중요하게 쓰는 생극을 다시 건드립니다."),
    ("cycle_flow_condition_", "대운·세운이 강약, 조후, 지지 조건이 붙은 생극을 다시 건드립니다."),
    ("flow_compound_daeun_supports_annual_support", "대운의 장기 환경과 세운의 연도 사건이 같은 방향으로 겹칩니다."),
    ("flow_compound_daeun_supports_annual_burden", "장기 기반은 유지되지만 해당 연도에 조정할 사안이 생깁니다."),
    ("flow_compound_daeun_burden_annual_support", "장기 부담이 있는 가운데 해당 연도에 활용할 기회가 들어옵니다."),
    ("flow_compound_daeun_burden_annual_burden", "장기 부담과 해당 연도 문제가 겹쳐 신중한 판단이 필요합니다."),
    ("flow_compound_daeun_annual_mixed", "대운과 세운의 길흉이 한쪽으로만 기울지 않고 교차합니다."),
    ("flow_annual_supportive_event", "세운이 원국에 필요한 글자를 해당 연도의 사건으로 드러냅니다."),
    ("flow_daeun_supportive_environment", "대운이 원국에 필요한 글자를 장기 환경으로 받쳐 줍니다."),
    ("flow_daeun_annual_relation_", "대운 지지와 세운 지지의 관계가 해당 연도의 사건성을 높입니다."),
    ("cycle_element_bridge_", "상극을 중간 오행이 통관으로 풀어 주는지 확인했습니다."),
    ("cycle_element_exception_", "반극, 과생, 설기 과다처럼 일반 생극이 뒤집히는 지점을 확인했습니다."),
    ("cycle_branch_relation_", "지지의 합충형해파가 원국 생극을 살리는지 흔드는지 확인했습니다."),
    ("cycle_branch_elements_", "지지 관계가 움직인 오행을 생극 판단에 반영했습니다."),
    ("cycle_stem_combine_", "천간합이 실제 합화로 이어지는지, 원래 생극을 묶는지 확인했습니다."),
    ("cycle_hidden_protrusion_", "지장간의 글자가 천간으로 투출되어 숨은 생극이 표면 작용으로 올라옵니다."),
    ("cycle_visible_root_", "천간의 글자가 지지에 통근하여 생극 작용의 지속력을 얻습니다."),
    ("cycle_rooting_", "투출과 통근으로 해당 오행의 현실 작용이 얼마나 버티는지 확인했습니다."),
    ("cycle_root_position_", "생극이 뿌리내린 지지 위치가 판단에 들어갑니다."),
    ("cycle_hidden_position_", "생극이 숨어 있던 지장간 위치가 판단에 들어갑니다."),
    ("cycle_classical_", "명리의 생극 작용명이 내부 판단 근거로 반영됩니다."),
    ("cycle_judgment_", "생극이 필요한 기운을 돕는지, 부담 기운을 키우는지 판정했습니다."),
    ("cycle_month_verdict_", "월령과 격국 기준에서 생극의 작용 방향을 확정했습니다."),
    ("cycle_governance_month_command_", "월령의 십신을 기준으로 해당 생극이 중심 구조와 닿아 있는지 확인했습니다."),
    ("cycle_governance_month_group_", "월령이 중심으로 삼는 십신 그룹이 생극 판정에 들어갑니다."),
    ("cycle_governance_month_branch_", "월지가 만든 계절과 현실 환경을 생극 판단의 기준으로 삼았습니다."),
    ("cycle_governance_regular_pattern_", "월령에서 잡힌 격국의 필요와 부담을 생극 판단에 반영했습니다."),
    ("cycle_governance_pattern_family_", "격국의 큰 성격을 생극 작용의 배경으로 반영했습니다."),
    ("cycle_governance_verdict_", "월령·격국 기준에서 이 생극이 도움, 부담, 혼합 작용 중 어디에 가까운지 판정했습니다."),
    ("cycle_governance_net_", "월령·격국 기준의 순작용과 부담 작용 차이가 판정에 들어갑니다."),
    ("cycle_governance_reality_", "해당 생극이 원국에서 실제로 작동할 현실성이 판정에 들어갑니다."),
    ("cycle_governance_tag_", "월령·격국 판단에서 실제로 걸린 세부 역할입니다."),
    ("cycle_governance_useful_", "격국과 월령이 필요로 하는 오행입니다."),
    ("cycle_governance_caution_", "격국과 월령에서 부담으로 커질 수 있는 오행입니다."),
    ("cycle_pattern_regular_", "정격별로 어떤 생극을 쓰는지 확인했습니다."),
    ("cycle_pattern_month_command_", "월령 십신에 따른 격국 생극 규칙을 반영했습니다."),
    ("cycle_pattern_verdict_", "이 생극이 해당 격국에서 쓰는 작용인지, 주의해야 할 작용인지 판정했습니다."),
    ("cycle_pattern_rule_", "해당 격국에서 적용된 세부 생극 규칙입니다."),
    ("cycle_pattern_support_", "해당 격국에서 살려 쓰는 생극 작용입니다."),
    ("cycle_pattern_caution_", "해당 격국에서 조심해야 하는 생극 작용입니다."),
    ("cycle_condition_strength_", "일간의 강약에 따라 이 생극을 감당하거나 활용할 수 있는지 확인했습니다."),
    ("cycle_condition_temperature_", "조후의 온도 조건을 생극 판단에 반영했습니다."),
    ("cycle_condition_moisture_", "조후의 습도 조건을 생극 판단에 반영했습니다."),
    ("cycle_condition_climate_need_", "조후상 필요한 오행이 이 생극 안에 들어 있는지 확인했습니다."),
    ("cycle_condition_verdict_", "강약, 조후, 지지 관계를 종합해 이 생극의 실제 조건을 판정했습니다."),
    ("cycle_condition_support_", "이 생극을 실제로 살리는 조건입니다."),
    ("cycle_condition_pressure_", "이 생극에 비용이나 부담을 붙이는 조건입니다."),
    ("cycle_condition_branch_", "지지의 합충형해파가 이 생극의 현실 작용에 미치는 영향입니다."),
    ("cycle_polarity_", "생극 작용을 길한 쪽, 혼합 작용, 부담 작용으로 나누어 반영했습니다."),
    ("cycle_source_fit_", "생극을 거는 쪽이 월령과 격국 기준에 맞는지 확인했습니다."),
    ("cycle_target_fit_", "생극을 받는 쪽이 월령과 격국 기준에 맞는지 확인했습니다."),
    ("cycle_flow_element_", "대운·세운에서 움직인 오행이 원국 생극과 연결됩니다."),
    ("cycle_flow_group_", "대운·세운에서 움직인 십신 역할이 원국 생극과 연결됩니다."),
    ("cycle_role_", "오행을 십신 역할로 바꾸어 생극 작용을 판단했습니다."),
    ("cycle_month_fit_", "생극 관계가 월령과 격국 기준에 맞는지 판정합니다."),
    ("cycle_position_", "생극 관계가 작용하는 궁성과 위치가 판단에 들어갑니다."),
    ("element_cycle_", "오행 자체의 생극 관계를 월령 기준으로 다시 판정했습니다."),
    ("natal_month_command_", "월령이 해당 영역의 기본 체질과 우선순위를 정합니다."),
    ("natal_palace_", "해당 궁성이 이 영역의 현실 체감도를 높입니다."),
    ("natal_position_", "타고난 지지와 지장간의 십신이 이 영역의 결론을 보강합니다."),
    ("natal_hidden_protrusion_", "지장간이 천간으로 투출되어 숨은 재료가 행동과 선택으로 확인됩니다."),
    ("natal_hidden_", "지장간의 숨은 재료가 해당 영역의 현실 장면을 만듭니다."),
    ("natal_branch_six_combine_", "타고난 합이 해당 영역에서 연결과 약속을 강화합니다."),
    ("natal_branch_three_harmony_half_", "타고난 반합이 해당 영역의 방향을 보강합니다."),
    ("natal_branch_three_harmony_", "타고난 삼합이 해당 영역의 방향을 강하게 모읍니다."),
    ("natal_branch_three_meeting_", "타고난 방합이 계절의 기세를 한 방향으로 모읍니다."),
    ("pattern_useful_", "격국과 월령이 필요로 하는 기운이 해당 영역을 밀어 줍니다."),
    ("pattern_caution_", "격국과 월령에서 부담이 되는 기운을 따로 살핍니다."),
    ("regular_pattern_", "월령에서 올라오는 격국 성질이 판단에 반영됩니다."),
    ("pattern_", "격국과 필요한 기운을 같이 놓고 판단합니다."),
    ("feature_axis_", "타고난 세부 특성이 해당 영역의 실제 모습으로 이어집니다."),
    ("combo_heavenly_stem_", "타고난 천간 배합에서 책임, 자격, 실행 방식이 확인됩니다."),
    ("combo_hidden_stem_", "지지의 지장간 배합에서 겉으로 드러나지 않는 욕구와 생활 기반을 확인합니다."),
    ("combo_stem_branch_", "천간과 지지의 연결에서 겉으로 보이는 성향과 생활 기반이 동시에 움직입니다."),
    ("combo_ten_god_chain_", "십신의 연결 관계가 수입, 직업 책임, 관계 판단이 생활 속 일로 이어지는 방식을 풀이합니다."),
    ("branch_six_combine", "합이 생겨 관계, 계약, 연결이 만들어집니다."),
    ("branch_combine", "합이 생겨 관계, 계약, 연결이 만들어집니다."),
)

COUNTER_EXPLANATION_RULES = (
    ("year_stem_geob_jae", "겁재가 경쟁, 분산, 급한 재정 부담을 만듭니다."),
    ("year_stem_bi_gyeon", "비겁이 경쟁, 분산, 재정 부담을 만듭니다."),
    ("daeun_stem_bi_gyeon", "대운 천간의 비견이 장기적인 경쟁과 분산을 만듭니다."),
    ("daeun_stem_geob_jae", "대운 천간의 겁재가 장기적인 손익 분산과 경쟁을 만듭니다."),
    ("year_stem_sang_gwan", "세운의 상관이 규칙, 권위, 일정과 마찰을 만듭니다."),
    ("daeun_stem_sang_gwan", "대운의 상관이 장기적인 규칙·권위 마찰을 만듭니다."),
    ("year_branch_sang_gwan", "세운 지지의 상관이 실무 압박이나 표현 마찰을 키웁니다."),
    ("daeun_branch_sang_gwan", "상관이 규칙, 권위, 일정과 마찰을 만듭니다."),
    ("daeun_branch_bi_gyeon", "대운 지지의 비견이 경쟁과 분산을 장기화합니다."),
    ("daeun_branch_geob_jae", "대운 지지의 겁재가 경쟁, 손익 분산, 급한 지출을 키웁니다."),
    ("year_branch_bi_gyeon", "세운 지지의 비견이 경쟁, 분산, 독립 판단을 키웁니다."),
    ("year_branch_geob_jae", "세운 지지의 겁재가 경쟁, 손익 분산, 급한 지출을 키웁니다."),
    ("annual_stem_caution_element_", "세운 천간이 격국과 월령에서 부담이 되는 기운을 드러냅니다."),
    ("annual_branch_main_caution_element_", "세운 지지가 부담이 되는 기운을 생활 속 문제로 드러냅니다."),
    ("annual_branch_hidden_", "세운 지지의 지장간이 숨어 있던 부담 재료를 움직입니다."),
    ("daeun_stem_caution_element_", "대운 천간이 장기적으로 부담이 되는 기운을 키웁니다."),
    ("daeun_branch_main_caution_element_", "대운 지지가 장기적인 생활 기반에서 부담 기운을 움직입니다."),
    ("daeun_branch_hidden_", "대운 지지의 지장간에 있던 숨은 부담이 장기 배경으로 작용합니다."),
    ("pattern_caution_event_", "격국상 부담 기운이 이 영역의 주의점이 됩니다."),
    ("month_governance_harms_month_command", "월령 기준에서 격국의 방향을 흔드는 기운으로 분류됩니다."),
    ("month_governance_burdensome_by_month_command", "월령 기준에서 부담이 되는 기운으로 분류됩니다."),
    ("month_governance_element_caution_", "월령과 격국에서 부담이 커지는 오행입니다."),
    ("month_governance_element_dominant_load_", "한쪽 오행이 과해져 판단의 균형을 무겁게 만듭니다."),
    ("month_body_pressures_pattern_", "월지의 본기가 격국상 부담으로 작용하는 지점입니다."),
    ("wealth_drains_weak_day_master", "일간이 약할 때 재성이 부담으로 작용하는 지점입니다."),
    ("officer_controls_weak_day_master", "일간이 약할 때 관성이 압박으로 작용하는 지점입니다."),
    ("month_command_", "월령 십신이 부담 방향의 기준으로 작용합니다."),
    ("regular_pattern_", "월령에서 잡힌 격국 후보 중 주의해야 할 작용을 반영합니다."),
    ("indirect_resource_excess", "편인성 기운이 과해져 판단이나 실행을 늦출 수 있습니다."),
    ("direct_resource_excess", "정인성 기운이 과해져 실행보다 보호와 보류가 앞설 수 있습니다."),
    ("resource_overprotects_day_master", "인성이 일간을 지나치게 감싸 실제 행동이 늦어질 수 있습니다."),
    ("yangren_excess_competition", "양인격에서 비겁이 과해지면 경쟁, 분배, 독립 판단이 부담으로 커집니다."),
    ("yangren_resource_overfeeds", "양인격에서 인성이 과해지면 고집과 보류가 강해져 실행이 늦어질 수 있습니다."),
    ("peer_pattern_excess_peer", "비겁격에서 비겁이 더 과해지면 경쟁, 분배, 주도권 문제가 부담으로 커집니다."),
    ("peer_pattern_resource_overfeeds", "비겁격에서 인성이 과해지면 자기 기준이 강해져 조율이 늦어질 수 있습니다."),
    ("strong_day_master", "일간의 힘이 강해 자기 기준이 과해질 수 있습니다."),
    ("very_strong_day_master", "일간의 힘이 매우 강해 경쟁과 고집이 커질 수 있습니다."),
    ("peer_excess", "비겁이 과해져 경쟁, 분배, 독립 판단이 부담으로 커집니다."),
    ("resource_excess", "인성이 과해져 판단 보류와 자기 확신이 부담으로 커질 수 있습니다."),
    ("weak_day_master", "일간의 힘이 약해 부담 기운을 감당하는 힘을 보수적으로 봅니다."),
    ("very_weak_day_master", "일간의 힘이 매우 약해 책임, 지출, 압박을 감당하기 어렵습니다."),
    ("balanced_day_master", "일간의 힘이 중화되어 있어 부담과 결과의 균형이 중요합니다."),
    ("weak_support_base", "일간을 받쳐 주는 기반이 약해 현실 대응력이 흔들릴 수 있습니다."),
    ("dominant_", "한쪽 기운이 지나치게 강해 판단의 균형을 무겁게 만듭니다."),
    ("element_dominance", "특정 오행이 과하게 모이면 한쪽 판단과 사건이 반복될 수 있습니다."),
    ("wood_excess", "목 기운이 과해지면 확장 욕구와 관계 문제가 부담으로 커질 수 있습니다."),
    ("fire_excess", "화 기운이 과해지면 감정 표현과 속도감이 부담으로 커질 수 있습니다."),
    ("earth_excess", "토 기운이 과해지면 책임, 고집, 정체감이 부담으로 커질 수 있습니다."),
    ("metal_excess", "금 기운이 과해지면 기준과 통제가 지나쳐 부담으로 커질 수 있습니다."),
    ("water_excess", "수 기운이 과해지면 생각과 변동성이 지나쳐 부담으로 커질 수 있습니다."),
    ("wood_lack", "목 기운이 약해 성장 방향과 관계 확장이 쉽게 막힐 수 있습니다."),
    ("fire_lack", "화 기운이 약해 표현과 추진력이 늦어질 수 있습니다."),
    ("earth_lack", "토 기운이 약해 현실 기반과 보유력이 흔들릴 수 있습니다."),
    ("metal_lack", "금 기운이 약해 기준과 정리가 흐려질 수 있습니다."),
    ("water_lack", "수 기운이 약해 정보 판단과 유연성이 부족해질 수 있습니다."),
    ("johu_needs_wood", "조후상 목 기운이 부족하면 성장 방향과 생동감이 약해질 수 있습니다."),
    ("johu_needs_fire", "조후상 화 기운이 부족하면 표현력과 추진력이 약해질 수 있습니다."),
    ("johu_needs_earth", "조후상 토 기운이 부족하면 현실 기반과 균형감이 흔들릴 수 있습니다."),
    ("johu_needs_metal", "조후상 금 기운이 부족하면 기준과 정리력이 약해질 수 있습니다."),
    ("johu_needs_water", "조후상 수 기운이 부족하면 사고력과 조절력이 약해질 수 있습니다."),
    ("resource_can_damage_eating_god", "인성이 식신을 누르면 생각과 준비가 많아져 결과물이 늦어질 수 있습니다."),
    ("hurting_officer_clashes_with_officer", "상관이 관성과 부딪히면 말, 규칙, 평가, 권위 문제가 예민해질 수 있습니다."),
    ("peer_competes_for_indirect_wealth", "비겁이 편재를 건드리면 큰돈, 거래, 수익 배분을 두고 경쟁이 커질 수 있습니다."),
    ("resource_slows_wealth_movement", "인성이 편재의 속도를 늦추면 거래 판단과 돈의 움직임이 지연될 수 있습니다."),
    ("peer_competes_for_direct_wealth", "비겁이 정재를 건드리면 안정 수입과 생활비의 몫 문제가 예민해질 수 있습니다."),
    ("resource_slows_wealth_accumulation", "인성이 정재를 늦추면 안정만 보다가 축적과 결정이 지연될 수 있습니다."),
    ("wealth_feeds_seven_killings", "재성이 편관을 키우면 돈, 성과, 계약이 곧 책임 압박으로 이어질 수 있습니다."),
    ("killing_pressure_excess", "편관이 과해지면 책임, 평가, 긴장감이 부담으로 커질 수 있습니다."),
    ("output_harms_officer_order", "식상이 관성의 질서를 치면 말, 결과물, 규칙, 평가가 부딪힐 수 있습니다."),
    ("peer_disrupts_officer_order", "비겁이 관성의 질서를 흔들면 자기 기준과 공식 책임이 부딪힐 수 있습니다."),
    ("pattern_reason_pressure_", "격국의 세부 작용 중 부담으로 기우는 부분이 이 영역의 주의점입니다."),
    ("pattern_reason_overuse_", "필요한 기운이 과도하게 작용하는 세부 근거를 보조 주의 신호로 기록합니다."),
    ("pattern_caution_active_", "운에서 부담 기운이 강해져 주의점이 또렷해집니다."),
    ("pattern_useful_excess_watch_", "필요한 기운이 과도하게 작용하는 지점을 보조 주의 신호로 기록합니다."),
    ("cycle_regulation_", "상생상극의 연결 속에서 비용, 손상, 충돌 가능성이 판정됩니다."),
    ("cycle_flow_activation_", "대운·세운이 원국의 생극 사슬을 건드리며 부담 작용까지 자극합니다."),
    ("cycle_flow_governance_", "대운·세운이 월령·격국 기준의 부담 생극을 다시 건드리는 지점입니다."),
    ("cycle_flow_pattern_", "대운·세운이 해당 격국에서 주의할 생극을 다시 건드리는 지점입니다."),
    ("cycle_flow_condition_", "대운·세운이 강약, 조후, 지지 조건이 붙은 부담 생극을 다시 건드립니다."),
    ("flow_annual_burdensome_event", "세운이 원국에서 부담이 되는 글자를 해당 연도 문제로 드러냅니다."),
    ("flow_daeun_burdensome_environment", "대운이 원국에서 부담이 되는 글자를 장기 환경으로 키웁니다."),
    ("cycle_element_bridge_", "상극을 풀 통관 오행이 약하거나 부담을 받는 지점입니다."),
    ("cycle_element_exception_", "반극, 과생, 설기 과다로 생극이 부담스럽게 나타나는 지점입니다."),
    ("cycle_branch_relation_", "지지의 합충형해파가 필요한 생극을 흔드는 지점입니다."),
    ("cycle_branch_elements_", "지지 관계가 움직인 오행이 부담 쪽으로 작용하는지 확인했습니다."),
    ("cycle_stem_combine_", "천간합이 합화되지 못하거나 부담 오행으로 기울 수 있는지 확인했습니다."),
    ("cycle_hidden_protrusion_", "지장간 투출로 숨어 있던 부담 생극이 겉으로 드러나는지 확인했습니다."),
    ("cycle_visible_root_", "천간 통근으로 부담 생극이 오래 유지되는지 확인했습니다."),
    ("cycle_rooting_", "투출과 통근이 부담 작용의 현실성을 높이는지 확인했습니다."),
    ("cycle_root_position_", "부담 생극이 뿌리내린 지지 위치가 판단에 들어갑니다."),
    ("cycle_hidden_position_", "부담 생극이 숨어 있던 지장간 위치가 판단에 들어갑니다."),
    ("cycle_judgment_", "생극 관계가 부담 쪽으로 기울 수 있는지 따로 판정했습니다."),
    ("cycle_month_verdict_", "월령과 격국 기준에서 부담으로 기우는 생극인지 확인했습니다."),
    ("cycle_governance_month_command_", "월령의 십신을 기준으로 부담 작용이 중심 구조와 닿아 있는지 확인했습니다."),
    ("cycle_governance_month_group_", "월령이 잡은 십신 그룹 안에서 부담이 커지는지 판정합니다."),
    ("cycle_governance_month_branch_", "월지가 만든 계절과 현실 환경에서 부담 작용이 커지는지 확인했습니다."),
    ("cycle_governance_regular_pattern_", "격국의 필요와 부담 중 부담 쪽으로 기우는 지점을 생극 판단에 반영했습니다."),
    ("cycle_governance_pattern_family_", "격국의 큰 성격을 부담 판단의 배경으로 반영했습니다."),
    ("cycle_governance_verdict_", "월령·격국 기준에서 이 생극이 부담, 혼합, 보조 작용 중 어디에 가까운지 판정했습니다."),
    ("cycle_governance_net_", "월령·격국 기준의 순작용과 부담 작용 차이가 판정에 들어갑니다."),
    ("cycle_governance_reality_", "해당 부담 생극이 원국에서 실제로 작동할 현실성이 판정에 들어갑니다."),
    ("cycle_governance_tag_", "월령·격국 판단에서 부담으로 걸린 세부 역할입니다."),
    ("cycle_governance_useful_", "필요한 오행이라도 과하거나 충돌하면 보조 주의 신호로 기록합니다."),
    ("cycle_governance_caution_", "격국과 월령에서 부담으로 커질 수 있는 오행입니다."),
    ("cycle_pattern_regular_", "정격별 생극 규칙에서 부담으로 기울 수 있는지 확인했습니다."),
    ("cycle_pattern_month_command_", "월령 십신에 따른 격국 생극 규칙을 반영했습니다."),
    ("cycle_pattern_verdict_", "이 생극이 해당 격국에서 쓰는 작용인지, 주의해야 할 작용인지 판정했습니다."),
    ("cycle_pattern_rule_", "해당 격국에서 적용된 세부 생극 규칙입니다."),
    ("cycle_pattern_support_", "필요한 작용이더라도 비용이나 부담이 붙는지 보조 판정합니다."),
    ("cycle_pattern_caution_", "해당 격국에서 조심해야 하는 생극 작용입니다."),
    ("cycle_condition_strength_", "일간의 강약 때문에 이 생극이 부담으로 커지는지 확인했습니다."),
    ("cycle_condition_temperature_", "조후의 온도 조건이 부담을 키우는지 확인했습니다."),
    ("cycle_condition_moisture_", "조후의 습도 조건이 부담을 키우는지 확인했습니다."),
    ("cycle_condition_climate_need_", "조후상 필요한 오행이 손상되거나 과하게 쓰이는지 확인했습니다."),
    ("cycle_condition_verdict_", "강약, 조후, 지지 관계를 종합해 이 생극의 부담 조건을 판정했습니다."),
    ("cycle_condition_support_", "부담 속에서도 이 생극을 살리는 보조 조건입니다."),
    ("cycle_condition_pressure_", "이 생극에 비용이나 부담을 붙이는 조건입니다."),
    ("cycle_condition_branch_", "지지의 합충형해파가 이 생극의 현실 작용에 미치는 영향입니다."),
    ("cycle_polarity_", "생극 작용의 혼합성과 부담 가능성을 분리해 반영했습니다."),
    ("cycle_flow_element_", "대운·세운에서 움직인 오행이 부담 신호와 연결됩니다."),
    ("cycle_flow_group_", "대운·세운에서 움직인 십신 역할이 부담 신호와 연결됩니다."),
    ("cycle_month_fit_", "월령 기준에서 생극 관계의 부담 여부를 판정합니다."),
    ("cycle_position_", "생극 관계가 작용하는 위치에서 부담이 판정됩니다."),
    ("element_cycle_", "오행의 극제 작용이 해당 영역에서 부담으로 나타날 수 있습니다."),
    ("year_branch_clash", "세운 지지의 충이 변화 속도와 충돌성을 올립니다."),
    ("year_branch_punishment", "세운 지지의 형이 압박, 긴장, 반복 문제를 키웁니다."),
    ("year_branch_self_punishment", "세운 지지의 자기형이 내적 압박과 반복 고민을 키웁니다."),
    ("year_branch_break", "세운 지지의 파가 약속, 일정, 기준의 어긋남을 만듭니다."),
    ("year_branch_harm", "세운 지지의 해가 보이지 않는 불편함이나 오해를 누적시킵니다."),
    ("branch_clash", "충이 생겨 변화 속도와 충돌성이 올라갑니다."),
    ("branch_punishment", "형이 생겨 심리적 압박이나 관계 긴장이 커집니다."),
    ("branch_self_punishment", "자기형이 생겨 같은 문제를 반복 점검하게 만듭니다."),
    ("branch_break", "파가 생겨 약속, 일정, 기준의 어긋남이 커집니다."),
    ("branch_harm", "해가 생겨 보이지 않는 불편함이나 오해가 누적됩니다."),
    ("branch_six_combine", "합은 연결을 만들지만 동시에 묶이는 부담도 만듭니다."),
    ("natal_position_counter_", "타고난 지지와 지장간의 십신이 해당 영역의 부담을 만듭니다."),
    ("natal_hidden_counter_", "지장간의 숨은 재료가 해당 영역의 피로 지점이 됩니다."),
    ("natal_branch_clash_", "타고난 충이 해당 영역에서 변화와 충돌을 키웁니다."),
    ("natal_branch_punishment_", "타고난 형이 해당 영역에서 반복 압박을 키웁니다."),
    ("natal_branch_harm_", "타고난 해가 해당 영역에서 말하기 어려운 불편을 키웁니다."),
    ("natal_branch_break_", "타고난 파가 해당 영역에서 약속과 기준의 어긋남을 만듭니다."),
    ("natal_branch_self_punishment_", "타고난 자형이 해당 영역에서 같은 문제를 반복하게 만듭니다."),
    ("caution_element_", "주의 오행이 과해지며 판단 영역의 부담이 커집니다."),
    ("annual_peach_blossom", "도화가 노출과 인기를 키우지만 관계 피로도 키웁니다."),
    ("boundary_sensitive", "출생 시간이 경계에 가까워 일부 시기 판단은 보수적으로 적용됩니다."),
    ("feature_axis_", "타고난 세부 특성의 약한 부분이 해당 영역의 부담을 키웁니다."),
    ("daeun_branch_clash", "대운 지지의 충이 장기 변화 압력을 만듭니다."),
    ("daeun_branch_punishment", "대운 지지의 형이 장기적인 압박과 반복 문제를 만듭니다."),
    ("daeun_branch_self_punishment", "대운 지지의 자기형이 장기적인 내적 압박을 만듭니다."),
    ("daeun_branch_break", "대운 지지의 파가 장기 기준의 불안정성을 만듭니다."),
    ("daeun_branch_harm", "대운 지지의 해가 장기 관계의 이면 부담을 만듭니다."),
    ("daeun_fire_trine", "대운 삼합·반합이 특정 오행을 과하게 밀어 부담을 만듭니다."),
    ("natal_hurting_officer_meets_officer", "타고난 상관견관 성향이 규칙·평판·권위 문제를 자극합니다."),
    ("natal_peer_wealth_competition", "타고난 비겁·재성 경쟁 구도가 손익 분산과 경쟁 부담을 만듭니다."),
    ("combo_counter_officer_self_pressure", "책임과 평가가 직접 압박으로 들어와 직업과 관계에서 긴장감을 키웁니다."),
    ("combo_counter_officer_peer_pressure", "규칙과 경쟁심이 동시에 들어와 동료, 조직, 금전 판단에서 부담이 생깁니다."),
    ("combo_counter_peer_wealth_competition", "비겁과 재성이 맞물려 수익 기회와 분산 부담이 동시에 커집니다."),
    ("combo_counter_hurting_officer_meets_officer", "표현력과 규칙성이 부딪혀 평가, 일정, 권위 문제가 예민해집니다."),
    ("combo_counter_resource_output_friction", "생각과 실행 사이의 검열이 커져 결정이 늦어집니다."),
    ("combo_counter_indirect_resource_food_block", "편인의 검열이 식신의 실행력을 누르며 행동이 늦어집니다."),
    ("combo_counter_peer_density", "비견과 겁재 성분이 겹쳐 경쟁, 분산, 독립 판단이 커집니다."),
)


def filter_risk_language(text: str) -> RiskFilterResult:
    filtered = text
    flags: list[str] = []
    for term, flag in PROHIBITED_DETERMINISTIC_TERMS.items():
        if term in filtered:
            flags.append(flag)
            if flag == "deterministic_claim":
                filtered = filtered.replace(term, "강하게")
            else:
                filtered = filtered.replace(term, "주의 신호")
    flags = list(dict.fromkeys(flags))
    output_allowed = not any(flag in {"high_risk_health", "legal_claim"} for flag in flags)
    return RiskFilterResult(
        original_text=text,
        filtered_text=filtered,
        flags=flags,
        output_allowed=output_allowed,
    )


def _title(packet: EventPacket) -> str:
    return f"{packet.period_label} {DOMAIN_LABELS[packet.domain]}운"


def _summary(packet: EventPacket) -> str:
    if packet.rendered_preview:
        return packet.rendered_preview
    return f"{packet.period_label} {packet.domain} flow: {packet.sub_event_type}"


def _detail(packet: EventPacket, tier: ProductTier) -> str:
    if tier == "free":
        return packet.primary_scene_sentence
    if tier == "basic":
        return f"{packet.primary_scene_sentence}. {packet.main_action}이 핵심입니다."
    return (
        f"{packet.primary_scene_sentence}. {packet.realization_path}으로 나타납니다. "
        f"이때는 {_risk_detail_target(packet.risk_path)} 조심해야 합니다. {packet.personality_filter}."
    )


def _risk_detail_target(risk_path: str) -> str:
    text = risk_path.strip()
    replacements = {
        "수입은 커지지만": "수입이 커져도",
        "역할은 커지지만": "역할이 커져도",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text.endswith("상황"):
        return f"{text}을"
    if text.endswith(("부담", "문제", "충돌", "압박")):
        return f"{text}을"
    return f"{text}을"


def _explain_code(code: str, rules: tuple[tuple[str, str], ...]) -> str:
    if code.endswith("_useful_relation"):
        return "합충형파해가 월령과 격국에 필요한 기운을 움직입니다. 해당 영역에는 좋은 변화가 생깁니다."
    if code.endswith("_burden_relation"):
        return "합충형파해로 원국에서 부담이 되는 기운도 힘을 받습니다. 해당 영역에는 정리해야 할 문제가 생깁니다."
    for prefix, explanation in rules:
        if code.startswith(prefix) or code == prefix:
            return _polite_explanation(explanation)
    return "원국의 세부 신호가 판단을 보강합니다."


def _polite_explanation(text: str) -> str:
    replacements = (
        ("만든다.", "만듭니다."),
        ("키운다.", "키웁니다."),
        ("올린다.", "올립니다."),
        ("드러낸다.", "드러냅니다."),
        ("높인다.", "높입니다."),
        ("보탠다.", "받쳐 줍니다."),
        ("정한다.", "정합니다."),
        ("보수적으로 보아야 한다.", "보수적으로 보아야 합니다."),
        ("연결된다.", "연결됩니다."),
        ("강화한다.", "강화합니다."),
        ("자극한다.", "자극합니다."),
        ("따라온다.", "함께 생깁니다."),
        ("생긴다.", "생깁니다."),
        ("열린다.", "생깁니다."),
        ("열어 준다.", "만듭니다."),
        ("있다.", "있습니다."),
        ("된다.", "됩니다."),
        ("한다.", "합니다."),
    )
    polite = text
    for old, new in replacements:
        if polite.endswith(old):
            return polite[: -len(old)] + new
    return polite


def _summarize_codes(codes: list[str], rules: tuple[tuple[str, str], ...], limit: int) -> list[str]:
    summaries: list[str] = []
    for code in codes:
        summary = _explain_code(code, rules)
        if summary not in summaries:
            summaries.append(summary)
        if len(summaries) >= limit:
            break
    return summaries


def _strength_label(value: int) -> str:
    if value >= 80:
        return "매우 강함"
    if value >= 68:
        return "강함"
    if value >= 55:
        return "보통 이상"
    if value >= 42:
        return "약함"
    return "매우 약함"


def _risk_label(value: int) -> str:
    if value >= 75:
        return "강한 주의"
    if value >= 62:
        return "주의"
    if value >= 48:
        return "관리 가능"
    return "낮음"


def _score_labels(packet: EventPacket) -> dict[str, str]:
    return {
        "opportunity": _strength_label(packet.opportunity_score),
        "risk": _risk_label(packet.risk_score),
        "change": _strength_label(packet.change_score),
        "probability": _strength_label(packet.event_probability_score),
        "confidence": packet.confidence,
    }


def _relationship_context(packet: EventPacket) -> str:
    if packet.domain not in {"love", "marriage"}:
        return ""
    contexts = {
        "single": "현재 관계를 전제하지 않고 새 인연과 선택 가능성, 만남의 질을 정리합니다.",
        "interested": "관심 대상과의 접점, 속도 조절, 상대의 조건 확인이 뚜렷하게 드러납니다.",
        "dating": "현재 관계는 진전 속도와 현실 기준 조율에서 결론이 납니다.",
        "long_term": "장기 관계에서는 안정성, 반복되는 역할 문제, 생활 기준 조율이 뚜렷하게 드러납니다.",
        "preparing_marriage": "결혼 준비 과정에서는 역할 분담, 가족 변수, 주거·재정 조건이 뚜렷하게 드러납니다.",
        "married": "부부 관계에서는 안정성, 생활 기준, 역할 분담, 가족 책임이 뚜렷하게 드러납니다.",
        "unknown": "",
    }
    return contexts[packet.relationship_status]


def _select_packets(analysis: AnalysisResult, tier: ProductTier) -> list[EventPacket]:
    limit = tier_definition(tier).item_limit
    packets = sorted(
        analysis.event_packets,
        key=lambda item: (
            item.output_allowed_level == "restricted",
            -item.event_probability_score,
            -item.opportunity_score,
        ),
    )
    usable = [packet for packet in packets if packet.output_allowed_level != "restricted"]
    if tier in {"free", "basic"}:
        target_years = analysis.trace.get("target_years", [])
        current_period = str(CURRENT_FORTUNE_YEAR) if CURRENT_FORTUNE_YEAR in set(target_years) else ""
        selected: list[EventPacket] = []
        selected_ids: set[str] = set()
        for domain in DOMAIN_ORDER:
            domain_packet = next(
                (
                    packet
                    for packet in usable
                    if packet.domain == domain and current_period and packet.period_label == current_period
                ),
                None,
            )
            if domain_packet is None:
                domain_packet = next((packet for packet in usable if packet.domain == domain), None)
            if domain_packet is None:
                continue
            selected.append(domain_packet)
            selected_ids.add(domain_packet.packet_id)
            if len(selected) >= limit:
                return selected
        for packet in usable:
            if packet.packet_id in selected_ids:
                continue
            selected.append(packet)
            if len(selected) >= limit:
                break
        return selected
    return sorted(usable, key=_premium_packet_display_key)[:limit]


def _premium_packet_display_key(packet: EventPacket) -> tuple[int, int, int, int]:
    year_match = re.search(r"\d{4}", packet.period_label)
    year = int(year_match.group(0)) if year_match else 9999
    domain_order = DOMAIN_ORDER.index(packet.domain) if packet.domain in DOMAIN_ORDER else len(DOMAIN_ORDER)
    return (year, domain_order, -packet.event_probability_score, -packet.opportunity_score)


def _surface_packet_score(packet: EventPacket) -> float:
    """Score packets for compact UI surfaces without changing the analysis result."""
    return max(
        float(packet.event_probability_score or 0),
        float(packet.opportunity_score or 0),
        float(packet.risk_score or 0),
        float(packet.change_score or 0),
    ) + float(packet.event_probability_score or 0) * 0.12


def _limit_packets_for_surface(packets: list[EventPacket], limit: int | None) -> list[EventPacket]:
    if limit is None or limit <= 0 or len(packets) <= limit:
        return packets

    selected: list[EventPacket] = []
    selected_ids: set[str] = set()

    def add_candidates(candidates: list[EventPacket], quota: int) -> None:
        for packet in candidates:
            if len(selected) >= limit or quota <= 0:
                return
            if packet.packet_id in selected_ids:
                continue
            selected.append(packet)
            selected_ids.add(packet.packet_id)
            quota -= 1

    domain_quota = max(6, limit // max(len(DOMAIN_ORDER), 1))
    risk_quota = max(2, domain_quota // 4)
    for domain in DOMAIN_ORDER:
        domain_packets = [packet for packet in packets if packet.domain == domain]
        add_candidates(sorted(domain_packets, key=_surface_packet_score, reverse=True), domain_quota)
        add_candidates(sorted(domain_packets, key=lambda packet: packet.risk_score, reverse=True), risk_quota)

    add_candidates(sorted(packets, key=_surface_packet_score, reverse=True), limit - len(selected))
    return sorted(selected[:limit], key=_premium_packet_display_key)


def _timing_sentence(item: ProductOutputItem) -> str:
    if not item.timing_windows:
        return "특정 월보다 전체 연도를 기준으로 정리합니다."
    first = item.timing_windows[0]
    phase = PHASE_LABELS.get(str(first.get("monthly_phase")), "상황을 관찰해야 하는 국면")
    start = str(first.get("start_datetime") or "")[:10]
    end = str(first.get("end_datetime") or "")[:10]
    period = f"{start}부터 {end}까지" if start and end else str(first.get("period_label"))
    return (
        f"가장 뚜렷한 시기는 {period}이며, "
        f"{phase}으로 봅니다."
    )


def _build_section(item: ProductOutputItem, tier: ProductTier) -> ProductOutputSection:
    paragraphs = [item.detail]
    if tier in {"basic", "premium"}:
        paragraphs.append(f"핵심 키워드는 {', '.join(item.event_keywords[:4])}입니다.")
    if item.feature_axes and tier in {"basic", "premium"}:
        feature_phrase = ", ".join(f"{axis['label']} {axis['percentile_label']}" for axis in item.feature_axes[:3])
        paragraphs.append(f"세부 특성에서는 {feature_phrase}이 결론을 더 구체적으로 만듭니다.")
    if item.relationship_context and tier in {"basic", "premium"}:
        paragraphs.append(item.relationship_context)
    if tier == "premium":
        if item.basis_summary:
            paragraphs.append(f"이 해석은 {', '.join(item.basis_summary[:4])}를 근거로 정리됩니다.")
        if item.counter_summary:
            paragraphs.append(f"주의할 반대 신호는 {', '.join(item.counter_summary[:4])}입니다.")
        paragraphs.append(_timing_sentence(item))

    category_contract = (
        premium_profile_category_contract(
            item.domain,
            feature_axes=item.feature_axes,
            risk_score=item.risk_score,
        )
        if tier == "premium"
        else {}
    )
    topic_items = (
        list(category_contract.get("topic_items") or [])
        if tier == "premium"
        else []
    )
    return ProductOutputSection(
        section_id=f"{item.packet_id}_{tier}_section",
        packet_id=item.packet_id,
        product_tier=tier,
        detail_level=tier_definition(tier).detail_level,
        domain=item.domain,
        domain_label=item.domain_label,
        period_label=item.period_label,
        heading=item.title,
        lead=item.summary,
        paragraphs=paragraphs,
        key_points=list(dict.fromkeys(item.event_keywords + item.basis_summary[:2])),
        timing_windows=item.timing_windows,
        template_ids={
            "common": item.common_template_id,
            "domain": item.domain_template_id,
            "type": item.type_template_id,
        },
        relationship_status=item.relationship_status,
        relationship_status_label=item.relationship_status_label,
        feature_axes=list(item.feature_axes),
        topic_items=topic_items,
        category_contract=category_contract,
    )


def _domain_coverage(analysis: AnalysisResult, items: list[ProductOutputItem]) -> dict[str, str]:
    included_domains = {item.domain for item in items}
    packet_domains = {packet.domain for packet in analysis.event_packets}
    restricted_domains = {
        packet.domain
        for packet in analysis.event_packets
        if packet.output_allowed_level == "restricted"
    }
    coverage: dict[str, str] = {}
    for domain in DOMAIN_ORDER:
        if domain in included_domains:
            coverage[domain] = "included"
        elif domain in restricted_domains:
            coverage[domain] = "restricted"
        elif domain in packet_domains:
            coverage[domain] = "omitted_by_tier"
        else:
            coverage[domain] = "not_generated"
    return coverage


def _domain_coverage_labels(coverage: dict[str, str]) -> dict[str, str]:
    return {domain: COVERAGE_LABELS[status] for domain, status in coverage.items()}


def _warning_label(warning: str) -> str:
    if "Pre-1954" in warning:
        return "1954년 이전 한국 시간대 이력 차이를 반영해 시기 판단은 신중하게 적용합니다."
    if "UTC+08:30" in warning:
        return "해당 출생 시점에는 한국 역사 표준시 UTC+08:30 보정이 적용되었습니다."
    if "birth_chart_boundary_sensitive" in warning:
        return "출생 시간이 시주 또는 절기 경계에 가까워 시기 판단은 신중하게 적용합니다."
    if "daeun_boundary_sensitive" in warning:
        return "대운 시작 시점이 경계에 가까워 전환 시기는 신중하게 적용합니다."
    if "Analysis confidence is lowered" in warning:
        return "명식 경계 신호가 있어 시기 판단은 확인 가능한 내용 위주로 정리했습니다."
    return "추가 검토가 필요한 계산 경고가 있습니다."


def _warning_labels(warnings: list[str]) -> list[str]:
    return list(dict.fromkeys(_warning_label(warning) for warning in warnings))


GYEOKGUK_CLASSICAL_ACTION_PREFIXES: tuple[str, ...] = (
    "gyeokguk_single_classical_action:",
    "gyeokguk_dual_classical_action:",
    "gyeokguk_dual_first_single_classical_action:",
    "gyeokguk_dual_second_single_classical_action:",
)

GYEOKGUK_FACET_DOMAIN_ALIASES: dict[str, set[str]] = {
    "money": {"money"},
    "career": {"career", "honor", "reputation"},
    "love": {"love", "relationship", "social"},
    "marriage": {"marriage"},
    "personality": {"personality", "social"},
}

GYEOKGUK_CYCLE_CLASSICAL_TAG_HINTS: dict[str, set[str]] = {
    "output_generates_wealth": {"siksang_saengjae"},
    "generates_output_to_wealth": {"siksang_saengjae", "bigeop_generates_siksang"},
    "output_generates_wealth_then_officer": {
        "siksang_saengjae",
        "jaesaenggwan",
        "jaeseong_generates_gwanseong",
    },
    "wealth_generates_officer": {"jaesaenggwan", "jaeseong_generates_gwanseong"},
    "generates_wealth_to_officer": {"jaesaenggwan", "jaeseong_generates_gwanseong"},
    "wealth_generates_officer_controls_peer": {
        "jaesaenggwan",
        "jaeseong_generates_gwanseong",
        "gwanseong_controls_bigeop",
    },
    "controls_peer_to_wealth": {"bigeop_jaengjae", "bigeop_controls_wealth", "gwanseong_controls_bigeop"},
    "peer_to_wealth": {"bigeop_jaengjae", "bigeop_controls_wealth"},
    "controls_officer_to_peer": {"gwanseong_controls_bigeop"},
    "wealth_controls_resource": {"jaegeukin", "wealth_controls_resource"},
    "controls_wealth_to_resource": {"jaegeukin", "wealth_controls_resource"},
    "officer_generates_resource": {"gwanin_sangsaeng", "gwanseong_generates_inseong", "salin_sangsaeng"},
    "controls_resource_to_output": {"inseong_dosik", "inseong_controls_output"},
    "output_controls_officer": {"siksin_jesal", "siksang_controls_gwanseong", "sanggwan_gyeongwan"},
    "element_generates": {
        "siksang_saengjae",
        "jaesaenggwan",
        "gwanin_sangsaeng",
        "salin_sangsaeng",
        "bigeop_generates_siksang",
        "inseong_generates_bigeop",
    },
}


def _gyeokguk_classical_tags_from_basis(basis_codes: list[str]) -> list[str]:
    tags: list[str] = []
    for code in list(basis_codes or []):
        text = str(code)
        for prefix in GYEOKGUK_CLASSICAL_ACTION_PREFIXES:
            if text.startswith(prefix):
                tags.append(text.removeprefix(prefix))
                break
    return list(dict.fromkeys(tags))


def _gyeokguk_match_classical_tags(match: object) -> list[str]:
    direct_tags = [str(tag) for tag in list(getattr(match, "classical_action_tags", []) or [])]
    component_tags = [
        str(tag)
        for tag in [
            *list(getattr(match, "first_single_classical_action_tags", []) or []),
            *list(getattr(match, "second_single_classical_action_tags", []) or []),
        ]
    ]
    basis_tags = _gyeokguk_classical_tags_from_basis(
        [str(code) for code in list(getattr(match, "basis_codes", []) or [])]
    )
    return list(dict.fromkeys([*direct_tags, *component_tags, *basis_tags]))


def _gyeokguk_center_axis_from_match(source: str, match: object, tags: list[str]) -> dict[str, object]:
    tag_set = {str(tag) for tag in list(tags or [])}
    if source == "single":
        resolution_state = str(getattr(match, "pattern_resolution_state", "") or "")
        grade_state = str(getattr(match, "role_grade", "") or "")
    else:
        resolution_state = str(getattr(match, "combination_resolution_state", "") or "")
        grade_state = str(getattr(match, "chain_grade", "") or "")

    hard_pagyeok = (
        "pagyeok" in resolution_state
        or "disease" in resolution_state
        or grade_state in {"risk_chain", "compounded_burden_chain", "danger", "breaker", "core_overload"}
    )
    if "byeongyak" in resolution_state or "medicine" in resolution_state or grade_state in {
        "medicine_chain",
        "breaker_or_medicine",
    }:
        return {"code": "byeongyak_medicine", "label": "병약 조절", "score": 13}
    if hard_pagyeok:
        return {"code": "pagyeok_or_disease", "label": "파격·병증", "score": 12}
    if "seonggyeok" in resolution_state or grade_state in {
        "constructive_chain",
        "supportive_chain",
        "core",
        "support",
        "source",
    }:
        caution_tags = {
            "sanggwan_gyeongwan",
            "bigeop_jaengjae",
            "inseong_dosik",
            "jaeda_sinyak_risk",
            "gwansal_honhap",
            "gwansal_overload",
            "inbi_overload",
            "siksang_overload",
            "jaesaengsal",
        }
        if bool(tag_set & caution_tags):
            return {"code": "seonggyeok_with_caution", "label": "성격 작용·병증 점검", "score": 12}
        return {"code": "seonggyeok", "label": "성격 작용", "score": 12}
    if "conditional" in resolution_state or "mixed" in resolution_state or grade_state in {"conditional_chain", "mixed_chain", "mixed"}:
        return {"code": "conditional_axis", "label": "조건부 성패", "score": 7}
    return {"code": "secondary_axis", "label": "보조 작용", "score": 4}


def _gyeokguk_action_title(source: str, match: object) -> str:
    if source == "dual":
        return str(getattr(match, "exact_pair_name", "") or getattr(match, "exact_pair_key", "") or getattr(match, "rule_key", ""))
    ten_god = str(getattr(match, "acting_ten_god", "") or "")
    return f"{TEN_GOD_LABELS.get(ten_god, ten_god)} 중심 작용" if ten_god else str(getattr(match, "rule_key", ""))


def _prepare_gyeokguk_action_matches(gyeokguk_profile: object | None) -> list[dict[str, object]]:
    """Normalize invariant gyeokguk match metadata once per chart."""

    if gyeokguk_profile is None:
        return []
    matches: list[tuple[str, object]] = [
        *[
            ("dual", match)
            for match in list(getattr(gyeokguk_profile, "dual_ten_god_action_matches", []) or [])
        ],
        *[
            ("single", match)
            for match in list(getattr(gyeokguk_profile, "ten_god_action_matches", []) or [])
        ],
    ]
    prepared: list[dict[str, object]] = []
    for source, match in matches:
        tags = _gyeokguk_match_classical_tags(match)
        prepared.append(
            {
                "source": source,
                "match": match,
                "tags": tags,
                "tag_set": frozenset(str(tag) for tag in tags),
                "match_domains": frozenset(
                    str(item) for item in list(getattr(match, "domain_priority", []) or [])
                ),
                "center_axis": _gyeokguk_center_axis_from_match(source, match, tags),
                "context_state": str(getattr(match, "context_judgment_state", "") or ""),
                "month_fit_state": str(getattr(match, "month_fit_state", "") or ""),
                "presence_score": int(getattr(match, "presence_score", 0) or 0),
                "domain_projections": getattr(match, "domain_projections", {}) or {},
                "title": _gyeokguk_action_title(source, match),
            }
        )
    return prepared


def _domain_facet_gyeokguk_action_sources(
    *,
    gyeokguk_profile: object | None,
    domain: str,
    rule: dict[str, object],
    basis_codes: list[str],
    counter_signals: list[str],
    prepared_matches: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    if gyeokguk_profile is None:
        return []

    rule_cycle_tags = {str(tag) for tag in list(rule.get("cycle_tags") or [])}
    desired_tags = {
        tag
        for cycle_tag in rule_cycle_tags
        for tag in GYEOKGUK_CYCLE_CLASSICAL_TAG_HINTS.get(cycle_tag, set())
    }
    code_text = " ".join([*basis_codes, *counter_signals])
    domain_aliases = GYEOKGUK_FACET_DOMAIN_ALIASES.get(domain, {domain})
    candidates: list[tuple[float, dict[str, object]]] = []
    match_rows = (
        prepared_matches
        if prepared_matches is not None
        else _prepare_gyeokguk_action_matches(gyeokguk_profile)
    )

    for match_row in match_rows:
        source = str(match_row["source"])
        match = match_row["match"]
        tags = list(match_row["tags"])
        tag_set = match_row["tag_set"]
        match_domains = match_row["match_domains"]
        domain_overlap = bool(match_domains & domain_aliases)
        tag_overlap = bool(tag_set & desired_tags)
        axis_overlap = any(str(tag) in code_text for tag in tag_set)
        if not (domain_overlap or tag_overlap or axis_overlap):
            continue

        center_axis = match_row["center_axis"]
        axis_code = str(center_axis.get("code") or "")
        context_state = str(match_row["context_state"])
        month_fit_state = str(match_row["month_fit_state"])
        presence_score = int(match_row["presence_score"])
        salience = (
            presence_score
            + (20 if domain_overlap else 0)
            + (16 if tag_overlap else 0)
            + (10 if axis_overlap else 0)
            + int(center_axis.get("score") or 0)
        )
        if context_state in {
            "context_strengthens_action",
            "context_strengthens_pair",
            "medicine_can_work",
            "constructive_by_context",
            "risk_is_reinforced",
            "month_pressure_confirms_risk",
        }:
            salience += 10
        if month_fit_state in {"supports_month_command", "usable_by_month_command", "both_supported_by_month_command"}:
            salience += 6
        if axis_code == "pagyeok_or_disease":
            salience += 6

        domain_projections = match_row["domain_projections"]
        if isinstance(domain_projections, dict):
            projection = next(
                (
                    str(domain_projections.get(alias))
                    for alias in domain_aliases
                    if domain_projections.get(alias)
                ),
                "",
            )
        else:
            projection = ""
        candidates.append(
            (
                float(salience),
                {
                    "source": source,
                    "title": str(match_row["title"]),
                    "center_axis": center_axis,
                    "classical_tags": tags[:6],
                    "presence_score": presence_score,
                    "month_fit_state": month_fit_state,
                    "context_judgment_state": context_state,
                    "domain_relevant": domain_overlap,
                    "cycle_tag_relevant": tag_overlap,
                    "axis_source_relevant": axis_overlap,
                    "domain_projection": projection,
                },
            )
        )

    candidates.sort(key=lambda item: (-item[0], str(item[1]["title"])))
    seen: set[tuple[str, str]] = set()
    selected: list[dict[str, object]] = []
    for salience, payload in candidates:
        signature = (str(payload["source"]), str(payload["title"]))
        if signature in seen:
            continue
        seen.add(signature)
        payload["salience"] = round(salience, 2)
        selected.append(payload)
        if len(selected) >= 3:
            break
    return selected


def _domain_facet_gyeokguk_delta(sources: list[dict[str, object]]) -> float:
    if not sources:
        return 0.0
    deltas: list[float] = []
    for source in sources[:3]:
        axis = source.get("center_axis", {})
        axis_code = str(axis.get("code") if isinstance(axis, dict) else "")
        if axis_code == "seonggyeok":
            delta = 3.2
        elif axis_code == "seonggyeok_with_caution":
            delta = 1.4
        elif axis_code == "byeongyak_medicine":
            delta = 2.6
        elif axis_code == "pagyeok_or_disease":
            delta = -3.4
        elif axis_code == "conditional_axis":
            delta = 0.8
        else:
            delta = 0.3
        relevance = 0.45
        if bool(source.get("cycle_tag_relevant")):
            relevance += 0.3
        if bool(source.get("axis_source_relevant")):
            relevance += 0.2
        if bool(source.get("domain_relevant")):
            relevance += 0.1
        delta *= min(1.0, relevance)
        deltas.append(delta)
    return max(-5.0, min(5.0, sum(deltas) / max(1, len(deltas)) * 1.6))


DOMAIN_DECISION_FACET_RULES: dict[str, list[dict[str, object]]] = {
    "money": [
        {
            "key": "wealth_formation",
            "label": "재물 형성력",
            "meaning": "일생에서 돈이 붙기 시작하는 자리와 금전 기회가 현실 수입으로 커지는 힘입니다.",
            "axis_keys": ["money_potential", "income_expansion", "liquidity_stability", "business_expansion"],
            "axis_weights": {"money_potential": 1.55, "business_expansion": 1.15, "income_expansion": 0.75, "liquidity_stability": 0.6},
            "cycle_tags": ["output_generates_wealth", "generates_output_to_wealth", "element_generates"],
        },
        {
            "key": "wealth_scale_expansion",
            "label": "재물 규모 확장력",
            "meaning": "일상의 수입을 넘어 거래 단위, 보유 자산, 사업 단위가 커지는 힘입니다.",
            "axis_keys": ["money_potential", "business_expansion", "investment_trading_sense", "asset_retention", "deal_selection"],
            "axis_weights": {"money_potential": 1.45, "business_expansion": 1.35, "investment_trading_sense": 1.1, "asset_retention": 0.95, "deal_selection": 0.75},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_output_to_wealth", "wealth_generates_officer", "element_generates"],
        },
        {
            "key": "income_generation",
            "label": "수입 창출력",
            "meaning": "일, 거래, 성과가 월급·매출·계약금처럼 실제 현금으로 회수되는 힘입니다.",
            "axis_keys": ["income_expansion", "liquidity_stability", "career_achievement", "money_potential"],
            "axis_weights": {"income_expansion": 1.55, "liquidity_stability": 1.25, "career_achievement": 0.9, "money_potential": 0.55},
            "cycle_tags": ["output_generates_wealth", "generates_output_to_wealth"],
        },
        {
            "key": "talent_monetization",
            "label": "재주 수익화",
            "meaning": "기술, 말, 콘텐츠, 서비스가 가격표를 가진 상품과 보수로 이어지는 힘입니다.",
            "axis_keys": ["income_expansion", "business_expansion", "communication_expression", "career_achievement"],
            "axis_weights": {"communication_expression": 1.45, "business_expansion": 1.25, "income_expansion": 0.95, "career_achievement": 0.65},
            "cycle_tags": ["output_generates_wealth", "generates_peer_to_output", "generates_output_to_wealth", "wealth_controls_resource_releases_output"],
        },
        {
            "key": "performance_reward",
            "label": "성과 보상력",
            "meaning": "해낸 일이 공로로만 끝나지 않고 직책, 보수, 성과급, 계약 조건으로 확정되는 힘입니다.",
            "axis_keys": ["reward_claim_strength", "career_achievement", "honor_recognition", "role_authority_alignment", "income_expansion"],
            "axis_weights": {"reward_claim_strength": 1.65, "role_authority_alignment": 1.25, "honor_recognition": 1.05, "career_achievement": 0.75, "income_expansion": 0.5},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_wealth_to_officer", "wealth_generates_officer_controls_peer"],
        },
        {
            "key": "asset_consolidation",
            "label": "자산화 능력",
            "meaning": "들어온 돈이 소비로 흩어지지 않고 소유권, 지분, 예치금, 장기 자산으로 남는 힘입니다.",
            "axis_keys": ["asset_retention", "ownership_clarity", "spending_control", "loss_avoidance", "practical_planning"],
            "axis_weights": {"asset_retention": 1.55, "ownership_clarity": 1.25, "spending_control": 1.0, "loss_avoidance": 0.85, "practical_planning": 0.65},
            "cycle_tags": ["controls_wealth_to_resource", "wealth_controls_resource", "visible_root", "hidden_protrusion"],
        },
        {
            "key": "cashflow_stability",
            "label": "자금 운용 안정성",
            "meaning": "수입 이후 생활비, 고정비, 예비 자금까지 안정적으로 배분하는 힘입니다.",
            "axis_keys": ["liquidity_stability", "spending_control", "practical_planning", "asset_retention", "loss_avoidance"],
            "axis_weights": {"liquidity_stability": 1.65, "spending_control": 1.25, "practical_planning": 1.05, "asset_retention": 0.75, "loss_avoidance": 0.7},
            "cycle_tags": ["output_generates_wealth", "controls_wealth_to_resource", "wealth_controls_resource"],
        },
        {
            "key": "shared_money_control",
            "label": "공동자금 운영력",
            "meaning": "가족, 지인, 동업자와 자금을 함께 다룰 때 자기 몫과 명의를 지키는 힘입니다.",
            "axis_keys": ["shared_asset_boundary", "ownership_clarity", "deal_selection", "boundary_management", "loss_avoidance"],
            "axis_weights": {"shared_asset_boundary": 1.6, "ownership_clarity": 1.25, "boundary_management": 1.05, "deal_selection": 0.85, "loss_avoidance": 0.75},
            "cycle_tags": ["controls_peer_to_wealth", "peer_to_wealth", "wealth_generates_officer_controls_peer", "controls_officer_to_peer"],
        },
        {
            "key": "debt_guarantee_control",
            "label": "부채·보증 관리력",
            "meaning": "대여, 보증, 채무 관계에서 책임 범위와 회수 가능성을 분명히 하는 힘입니다.",
            "axis_keys": ["loss_avoidance", "shared_asset_boundary", "ownership_clarity", "deal_selection", "boundary_management"],
            "axis_weights": {"loss_avoidance": 1.6, "shared_asset_boundary": 1.35, "ownership_clarity": 1.15, "deal_selection": 0.95, "boundary_management": 0.9},
            "cycle_tags": ["controls_peer_to_wealth", "wealth_generates_officer_controls_peer", "controls_officer_to_peer", "wealth_controls_resource"],
        },
        {
            "key": "family_asset_boundary",
            "label": "가족재산 경계력",
            "meaning": "부모, 형제, 친척과 얽힌 자산·상속성 돈에서 자기 몫과 책임선을 지키는 힘입니다.",
            "axis_keys": ["shared_asset_boundary", "ownership_clarity", "asset_retention", "boundary_management", "family_responsibility"],
            "axis_weights": {"shared_asset_boundary": 1.45, "ownership_clarity": 1.3, "asset_retention": 1.05, "boundary_management": 0.95, "family_responsibility": 0.85},
            "cycle_tags": ["controls_peer_to_wealth", "controls_officer_to_peer", "officer_generates_resource", "wealth_controls_resource"],
        },
        {
            "key": "contract_title_stability",
            "label": "계약·명의 안정성",
            "meaning": "계약서, 명의, 지분, 보증에서 자기 권리와 수령액을 보존하는 힘입니다.",
            "axis_keys": ["ownership_clarity", "deal_selection", "loss_avoidance", "practical_planning", "role_authority_alignment"],
            "axis_weights": {"ownership_clarity": 1.55, "deal_selection": 1.3, "loss_avoidance": 1.1, "role_authority_alignment": 0.85, "practical_planning": 0.7},
            "cycle_tags": ["generates_wealth_to_officer", "wealth_generates_officer", "controls_officer_to_peer", "officer_generates_resource"],
        },
        {
            "key": "receivables_recovery",
            "label": "채권·미수금 회수력",
            "meaning": "받아야 할 돈, 성과 보상, 대여금, 지연 지급을 자기 권리로 회수하는 힘입니다.",
            "axis_keys": ["ownership_clarity", "deal_selection", "liquidity_stability", "loss_avoidance", "reward_claim_strength"],
            "axis_weights": {"ownership_clarity": 1.45, "reward_claim_strength": 1.25, "deal_selection": 1.15, "liquidity_stability": 1.0, "loss_avoidance": 0.95},
            "cycle_tags": ["generates_wealth_to_officer", "wealth_generates_officer", "controls_officer_to_peer", "officer_generates_resource", "wealth_controls_resource"],
        },
        {
            "key": "investment_trading_judgment",
            "label": "투자·거래 판단력",
            "meaning": "수익 가능성, 회수 조건, 상대 신뢰도, 기간, 명의 문제를 함께 가려내는 힘입니다.",
            "axis_keys": ["investment_trading_sense", "deal_selection", "money_attitude", "loss_avoidance"],
            "axis_weights": {"investment_trading_sense": 1.55, "deal_selection": 1.25, "loss_avoidance": 1.05, "money_attitude": 0.75},
            "cycle_tags": ["output_generates_wealth", "generates_output_to_wealth", "wealth_controls_resource", "controls_wealth_to_resource"],
        },
        {
            "key": "financial_loss_defense",
            "label": "재정 방어력",
            "meaning": "급한 제안, 보증, 공동 지출, 무리한 확장 앞에서 손실을 줄이는 힘입니다.",
            "axis_keys": ["loss_avoidance", "shared_asset_boundary", "spending_control", "deal_selection", "boundary_management"],
            "axis_weights": {"loss_avoidance": 1.55, "shared_asset_boundary": 1.2, "spending_control": 1.05, "boundary_management": 1.0, "deal_selection": 0.85},
            "cycle_tags": ["controls_officer_to_peer", "controls_wealth_to_resource", "wealth_controls_resource", "officer_generates_resource"],
        },
        {
            "key": "late_life_wealth_growth",
            "label": "후반 축재력",
            "meaning": "나이가 들수록 수입 방식이 안정되고 자산 단위가 커지는 힘입니다.",
            "axis_keys": ["late_life_money_growth", "asset_retention", "income_expansion", "practical_planning"],
            "axis_weights": {"late_life_money_growth": 1.65, "asset_retention": 1.25, "practical_planning": 0.9, "income_expansion": 0.6},
            "cycle_tags": ["visible_root", "hidden_protrusion", "officer_generates_resource", "wealth_generates_officer"],
        },
        {
            "key": "money_standard",
            "label": "금전 기준성",
            "meaning": "돈 앞에서 체면이나 분위기보다 소유권, 보상 원칙, 지출 한계를 세우는 힘입니다.",
            "axis_keys": ["money_attitude", "deal_selection", "spending_control", "decision_consistency"],
            "axis_weights": {"money_attitude": 1.5, "decision_consistency": 1.15, "deal_selection": 1.0, "spending_control": 0.9},
            "cycle_tags": ["wealth_controls_resource", "controls_wealth_to_resource", "officer_generates_resource", "controls_officer_to_peer"],
        },
        {
            "key": "business_expansion",
            "label": "사업 확장성",
            "meaning": "고객, 거래처, 판매 단위를 넓혀 고정 수입 밖의 재물 규모를 키우는 힘입니다.",
            "axis_keys": ["business_expansion", "interpersonal_influence", "income_expansion", "change_adaptability"],
            "axis_weights": {"business_expansion": 1.6, "interpersonal_influence": 1.1, "change_adaptability": 0.95, "income_expansion": 0.75},
            "cycle_tags": ["generates_output_to_wealth", "output_generates_wealth", "element_generates"],
        },
    ],
    "career": [
        {
            "key": "field_fit",
            "label": "직업 적성",
            "meaning": "타고난 기질이 실제 일의 방식과 맞물려 성취로 남는 정도입니다.",
            "axis_keys": ["work_domain_fit", "career_achievement", "academic_expertise", "organization_adaptability"],
            "axis_weights": {"work_domain_fit": 1.55, "career_achievement": 1.05, "academic_expertise": 0.9, "organization_adaptability": 0.75},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_officer_to_resource", "visible_root"],
        },
        {
            "key": "career_field_domain",
            "label": "직업 분야",
            "meaning": "어떤 산업과 역할에서 직업적 성취가 가장 자연스럽게 살아나는지입니다.",
            "axis_keys": ["work_domain_fit", "career_achievement", "academic_expertise", "business_expansion", "organization_adaptability"],
            "axis_weights": {"work_domain_fit": 1.5, "career_achievement": 1.15, "academic_expertise": 0.95, "business_expansion": 0.8, "organization_adaptability": 0.75},
            "cycle_tags": ["element_generates", "stem_reception", "integrated_saju", "visible_root"],
        },
        {
            "key": "achievement_accumulation",
            "label": "성취 축적력",
            "meaning": "맡은 일이 실적, 이력, 직책으로 남아 경력의 값이 되는 정도입니다.",
            "axis_keys": ["career_achievement", "responsibility_capacity", "reputation_maintenance", "decision_consistency"],
            "axis_weights": {"career_achievement": 1.55, "responsibility_capacity": 1.15, "reputation_maintenance": 0.95, "decision_consistency": 0.75},
            "cycle_tags": ["output_generates_wealth_then_officer", "officer_generates_resource", "visible_root"],
        },
        {
            "key": "professional_depth",
            "label": "전문성 자산화",
            "meaning": "경험, 자격, 문서, 기술이 대체되기 어려운 경력 자산으로 쌓이는 정도입니다.",
            "axis_keys": ["academic_expertise", "career_achievement", "decision_consistency"],
            "axis_weights": {"academic_expertise": 1.65, "career_achievement": 0.95, "decision_consistency": 0.85},
            "cycle_tags": ["officer_generates_resource", "generates_officer_to_resource", "controls_resource_to_output"],
        },
        {
            "key": "authority_scope",
            "label": "권한 확보력",
            "meaning": "책임을 맡을 때 결정권과 재량권까지 함께 확보되는 정도입니다.",
            "axis_keys": ["role_authority_alignment", "responsibility_capacity", "leadership_potential", "organization_adaptability"],
            "axis_weights": {"role_authority_alignment": 1.6, "responsibility_capacity": 1.25, "leadership_potential": 1.0, "organization_adaptability": 0.65},
            "cycle_tags": ["wealth_generates_officer_controls_peer", "controls_officer_to_peer", "generates_wealth_to_officer"],
        },
        {
            "key": "recognition",
            "label": "평가·명예 전환력",
            "meaning": "성과가 직함, 평판, 공식 인정으로 올라가는 정도입니다.",
            "axis_keys": ["promotion_visibility", "honor_recognition", "reputation_maintenance", "career_achievement"],
            "axis_weights": {"promotion_visibility": 1.55, "honor_recognition": 1.3, "reputation_maintenance": 0.95, "career_achievement": 0.75},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_wealth_to_officer", "officer_generates_resource"],
        },
        {
            "key": "promotion_title_readiness",
            "label": "승진·직함 가능성",
            "meaning": "실적이 내부 평가, 직함, 승진 후보, 공식 책임자로 연결되는 정도입니다.",
            "axis_keys": ["promotion_visibility", "honor_recognition", "role_authority_alignment", "organization_adaptability", "career_achievement"],
            "axis_weights": {"promotion_visibility": 1.55, "role_authority_alignment": 1.2, "honor_recognition": 1.1, "organization_adaptability": 0.9, "career_achievement": 0.75},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "output_generates_wealth_then_officer"],
        },
        {
            "key": "social_ascent",
            "label": "사회적 도약성",
            "meaning": "개인의 실적이 조직 안팎의 지위, 영향력, 기회 확대로 이어지는 정도입니다.",
            "axis_keys": ["social_success_potential", "leadership_potential", "career_achievement", "honor_recognition"],
            "axis_weights": {"social_success_potential": 1.55, "leadership_potential": 1.2, "honor_recognition": 1.05, "career_achievement": 0.8},
            "cycle_tags": ["output_generates_wealth_then_officer", "wealth_generates_officer", "generates_wealth_to_officer"],
        },
        {
            "key": "responsibility_authority_balance",
            "label": "책임·권한 균형",
            "meaning": "직무 책임이 커질 때 결정권, 보고 체계, 보상 기준까지 같이 확보되는 정도입니다.",
            "axis_keys": ["role_authority_alignment", "responsibility_capacity", "organization_adaptability", "decision_consistency", "boundary_management"],
            "axis_weights": {"role_authority_alignment": 1.45, "responsibility_capacity": 1.3, "boundary_management": 0.95, "decision_consistency": 0.85, "organization_adaptability": 0.75},
            "cycle_tags": ["wealth_generates_officer_controls_peer", "controls_officer_to_peer", "officer_generates_resource"],
        },
        {
            "key": "compensation_negotiation",
            "label": "보상 협상력",
            "meaning": "성과를 낸 뒤 연봉, 수수료, 지분, 성과급으로 자기 몫을 확정하는 정도입니다.",
            "axis_keys": ["reward_claim_strength", "role_authority_alignment", "deal_selection", "communication_expression", "decision_consistency"],
            "axis_weights": {"reward_claim_strength": 1.6, "role_authority_alignment": 1.25, "deal_selection": 1.1, "communication_expression": 0.85, "decision_consistency": 0.75},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_wealth_to_officer", "wealth_generates_officer_controls_peer"],
        },
        {
            "key": "organization_fit",
            "label": "조직 적응력",
            "meaning": "규칙, 상하관계, 평가 체계 안에서 자기 자리를 오래 유지하는 정도입니다.",
            "axis_keys": ["organization_adaptability", "responsibility_capacity", "decision_consistency"],
            "axis_weights": {"organization_adaptability": 1.6, "responsibility_capacity": 1.1, "decision_consistency": 0.9},
            "cycle_tags": ["officer_generates_resource", "controls_officer_to_peer", "controls_output_to_officer"],
        },
        {
            "key": "affiliation_transition",
            "label": "소속 전환력",
            "meaning": "부서, 회사, 직무, 고용 형태가 바뀔 때 손실보다 새 기회를 만들 수 있는 정도입니다.",
            "axis_keys": ["change_adaptability", "organization_adaptability", "self_direction", "career_achievement", "crisis_recovery"],
            "axis_weights": {"change_adaptability": 1.55, "self_direction": 1.15, "organization_adaptability": 1.0, "career_achievement": 0.9, "crisis_recovery": 0.85},
            "cycle_tags": ["branch_cycle", "officer_generates_resource", "generates_peer_to_output"],
        },
        {
            "key": "unsuitable_work_filter",
            "label": "업무 조건 감별력",
            "meaning": "성과가 나기 어려운 자리, 권한이 약한 자리, 소모가 큰 업무를 미리 걸러내는 힘입니다.",
            "axis_keys": ["role_authority_alignment", "boundary_management", "change_adaptability", "decision_consistency", "crisis_recovery"],
            "axis_weights": {"boundary_management": 1.45, "role_authority_alignment": 1.2, "crisis_recovery": 1.0, "change_adaptability": 0.85, "decision_consistency": 0.8},
            "cycle_tags": ["controls_resource_to_output", "controls_output_to_officer", "officer_generates_resource"],
        },
        {
            "key": "independent_work",
            "label": "독립 가능성",
            "meaning": "조직 밖에서도 고객, 결과물, 보수 체계를 스스로 세울 수 있는 정도입니다.",
            "axis_keys": ["business_expansion", "self_direction", "communication_expression", "deal_selection"],
            "axis_weights": {"business_expansion": 1.45, "self_direction": 1.3, "deal_selection": 1.1, "communication_expression": 0.85},
            "cycle_tags": ["generates_peer_to_output", "generates_output_to_wealth", "output_generates_wealth"],
        },
        {
            "key": "practical_execution",
            "label": "실무 처리력",
            "meaning": "복잡한 업무를 순서대로 정리하고 실제 결과까지 마무리하는 정도입니다.",
            "axis_keys": ["career_achievement", "crisis_recovery", "responsibility_capacity", "organization_adaptability"],
            "axis_weights": {"career_achievement": 1.45, "crisis_recovery": 1.2, "responsibility_capacity": 1.0, "organization_adaptability": 0.75},
            "cycle_tags": ["eating_god_controls_seven_killings", "officer_generates_resource", "visible_root"],
        },
        {
            "key": "planning_judgment",
            "label": "기획 판단력",
            "meaning": "목표, 순서, 위험과 필요한 자원을 함께 검토하여 실행안을 세우는 정도입니다.",
            "axis_keys": ["practical_planning", "decision_consistency", "work_domain_fit", "loss_avoidance"],
            "axis_weights": {"practical_planning": 1.55, "decision_consistency": 1.25, "work_domain_fit": 0.95, "loss_avoidance": 0.8},
            "cycle_tags": ["officer_generates_resource", "wealth_controls_resource", "visible_root"],
        },
        {
            "key": "evaluation_management",
            "label": "평가 관리력",
            "meaning": "성과와 책임 이력을 조직의 평가와 신뢰로 안정적으로 연결하는 정도입니다.",
            "axis_keys": ["reputation_maintenance", "promotion_visibility", "decision_consistency", "communication_expression"],
            "axis_weights": {"reputation_maintenance": 1.45, "promotion_visibility": 1.15, "decision_consistency": 1.0, "communication_expression": 0.75},
            "cycle_tags": ["officer_generates_resource", "output_generates_wealth_then_officer", "visible_root"],
        },
        {
            "key": "career_continuity",
            "label": "직업 지속성",
            "meaning": "경력의 방향을 잃지 않고 전문성과 성과를 장기간 축적하는 정도입니다.",
            "axis_keys": ["career_achievement", "academic_expertise", "organization_adaptability", "change_adaptability", "crisis_recovery"],
            "axis_weights": {"career_achievement": 1.35, "academic_expertise": 1.2, "organization_adaptability": 1.1, "change_adaptability": 0.9, "crisis_recovery": 0.75},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
    ],
    "love": [
        {
            "key": "relationship_opening",
            "label": "인연 형성력",
            "meaning": "새 인연이 생기고 연락과 만남이 실제 관계의 가능성으로 이어지는 정도입니다.",
            "axis_keys": ["relationship_progression", "interpersonal_influence", "affection_expression", "affection_receptivity"],
            "axis_weights": {"relationship_progression": 1.55, "interpersonal_influence": 1.2, "affection_expression": 0.95, "affection_receptivity": 0.85},
            "cycle_tags": ["branch_cycle", "generates_peer_to_output", "element_generates"],
        },
        {
            "key": "attraction_standard",
            "label": "끌림의 기준",
            "meaning": "어떤 사람에게 마음이 움직이고 무엇을 매력으로 받아들이는지입니다.",
            "axis_keys": ["attraction_selectivity", "spouse_match_quality", "interpersonal_influence"],
            "axis_weights": {"attraction_selectivity": 1.6, "spouse_match_quality": 1.0, "interpersonal_influence": 0.8},
            "cycle_tags": ["wealth", "officer", "stem_combine"],
        },
        {
            "key": "partner_selection",
            "label": "상대 선택력",
            "meaning": "끌림만으로 움직이지 않고 관계 안정성과 생활 감각까지 보고 상대를 고르는 정도입니다.",
            "axis_keys": ["attraction_selectivity", "boundary_management", "emotional_alignment", "decision_consistency", "spouse_match_quality"],
            "axis_weights": {"attraction_selectivity": 1.35, "boundary_management": 1.2, "emotional_alignment": 1.0, "decision_consistency": 0.9, "spouse_match_quality": 0.85},
            "cycle_tags": ["wealth", "officer", "officer_generates_resource", "controls_officer_to_peer"],
        },
        {
            "key": "partner_trust_filter",
            "label": "상대 신뢰 감별력",
            "meaning": "호감이 생겨도 상대의 말, 책임감, 생활 태도, 관계 이력을 가려내는 정도입니다.",
            "axis_keys": ["attraction_selectivity", "boundary_management", "misunderstanding_prevention", "emotional_alignment", "spouse_match_quality"],
            "axis_weights": {"attraction_selectivity": 1.35, "boundary_management": 1.25, "misunderstanding_prevention": 1.05, "emotional_alignment": 0.95, "spouse_match_quality": 0.85},
            "cycle_tags": ["officer_generates_resource", "controls_officer_to_peer", "wealth", "branch_cycle"],
        },
        {
            "key": "affection_expression",
            "label": "애정 표현성",
            "meaning": "좋아하는 마음이 말, 연락, 행동으로 상대에게 전달되는 정도입니다.",
            "axis_keys": ["affection_expression", "affection_receptivity", "communication_expression", "relationship_progression"],
            "axis_weights": {"affection_expression": 1.6, "communication_expression": 1.2, "affection_receptivity": 1.0, "relationship_progression": 0.75},
            "cycle_tags": ["generates_peer_to_output", "controls_resource_to_output", "output"],
        },
        {
            "key": "emotional_receptivity",
            "label": "정서 수용력",
            "meaning": "상대의 표현, 불안, 서운함을 방어적으로 밀어내지 않고 관계 안에서 받아내는 정도입니다.",
            "axis_keys": ["affection_receptivity", "emotional_alignment", "relationship_stability", "conflict_recovery", "misunderstanding_prevention"],
            "axis_weights": {"affection_receptivity": 1.45, "emotional_alignment": 1.25, "relationship_stability": 0.95, "conflict_recovery": 0.85, "misunderstanding_prevention": 0.75},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "visible_root"],
        },
        {
            "key": "relationship_progress",
            "label": "관계 진전력",
            "meaning": "호감이 실제 만남, 고백, 공식적인 관계로 이어지는 정도입니다.",
            "axis_keys": ["relationship_progression", "marriage_timing_readiness", "boundary_management"],
            "axis_weights": {"relationship_progression": 1.55, "marriage_timing_readiness": 0.95, "boundary_management": 0.85},
            "cycle_tags": ["output_generates_wealth_then_officer", "generates_wealth_to_officer", "branch_cycle"],
        },
        {
            "key": "relationship_agency",
            "label": "관계 주도권",
            "meaning": "상대의 속도에 끌려가기보다 관계의 방향과 거리를 스스로 정하는 정도입니다.",
            "axis_keys": ["self_direction", "relationship_progression", "boundary_management", "affection_expression", "decision_consistency"],
            "axis_weights": {"self_direction": 1.45, "boundary_management": 1.2, "relationship_progression": 0.95, "decision_consistency": 0.85, "affection_expression": 0.75},
            "cycle_tags": ["controls_officer_to_peer", "generates_peer_to_output", "branch_cycle"],
        },
        {
            "key": "relationship_tempo_control",
            "label": "관계 속도 조절력",
            "meaning": "마음이 움직인 뒤에도 연락, 만남, 고백의 속도를 안정적으로 맞추는 정도입니다.",
            "axis_keys": ["relationship_progression", "emotional_alignment", "boundary_management", "decision_consistency"],
            "axis_weights": {"emotional_alignment": 1.4, "boundary_management": 1.2, "decision_consistency": 1.0, "relationship_progression": 0.8},
            "cycle_tags": ["branch_cycle", "officer_generates_resource", "controls_officer_to_peer"],
        },
        {
            "key": "relationship_stability",
            "label": "관계 지속력",
            "meaning": "감정이 깊어진 뒤에도 관계가 쉽게 끊어지지 않고 유지되는 정도입니다.",
            "axis_keys": ["relationship_stability", "emotional_alignment", "conflict_recovery", "boundary_management"],
            "axis_weights": {"relationship_stability": 1.6, "conflict_recovery": 1.1, "emotional_alignment": 1.0, "boundary_management": 0.85},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "misunderstanding_prevention",
            "label": "오해 조정력",
            "meaning": "표현 지연, 연락 방식, 기대 차이처럼 상대가 서운함을 느끼는 지점입니다.",
            "axis_keys": ["misunderstanding_prevention", "communication_expression", "emotional_alignment", "boundary_management"],
            "axis_weights": {"misunderstanding_prevention": 1.6, "communication_expression": 1.1, "emotional_alignment": 0.95, "boundary_management": 0.85},
            "cycle_tags": ["controls_resource_to_output", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "conflict_trigger",
            "label": "갈등 관리력",
            "meaning": "표현, 거리, 자존심, 가족, 돈처럼 관계를 흔드는 요인을 관리하는 정도입니다.",
            "axis_keys": ["misunderstanding_prevention", "emotional_alignment", "boundary_management", "conflict_recovery", "money_attitude"],
            "axis_weights": {"misunderstanding_prevention": 1.35, "emotional_alignment": 1.2, "boundary_management": 1.1, "conflict_recovery": 0.85, "money_attitude": 0.65},
            "cycle_tags": ["branch_cycle", "controls_resource_to_output", "controls_officer_to_peer", "controls_peer_to_wealth"],
        },
        {
            "key": "external_interference_control",
            "label": "주변 개입 관리력",
            "meaning": "친구, 과거 인연, 가족, 직장 주변인의 말이 관계 안으로 들어올 때 흔들림을 줄이는 정도입니다.",
            "axis_keys": ["boundary_management", "misunderstanding_prevention", "relationship_stability", "conflict_recovery", "interpersonal_influence"],
            "axis_weights": {"boundary_management": 1.45, "misunderstanding_prevention": 1.2, "relationship_stability": 1.0, "conflict_recovery": 0.95, "interpersonal_influence": 0.75},
            "cycle_tags": ["branch_cycle", "controls_officer_to_peer", "controls_peer_to_wealth", "officer_generates_resource"],
        },
        {
            "key": "conflict_recovery",
            "label": "갈등 회복력",
            "meaning": "오해와 거리감이 생겼을 때 관계를 다시 정리할 수 있는 정도입니다.",
            "axis_keys": ["conflict_recovery", "misunderstanding_prevention", "communication_expression", "boundary_management"],
            "axis_weights": {"conflict_recovery": 1.55, "misunderstanding_prevention": 1.05, "communication_expression": 0.95, "boundary_management": 0.85},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "reconnection_capacity",
            "label": "재회 가능성",
            "meaning": "끊어진 관계가 다시 이어질 여지와 끝내야 할 관계를 정리하는 힘입니다.",
            "axis_keys": ["reunion_closure", "conflict_recovery", "relationship_stability", "communication_expression", "decision_consistency"],
            "axis_weights": {"reunion_closure": 1.55, "conflict_recovery": 1.15, "relationship_stability": 0.95, "decision_consistency": 0.75, "communication_expression": 0.7},
            "cycle_tags": ["officer_generates_resource", "visible_root", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "contact_distance_stability",
            "label": "연락·거리 안정성",
            "meaning": "가까워진 뒤에도 연락 빈도, 개인 시간, 관계의 거리를 무리 없이 맞추는 정도입니다.",
            "axis_keys": ["boundary_management", "communication_expression", "relationship_stability"],
            "axis_weights": {"boundary_management": 1.55, "relationship_stability": 1.0, "communication_expression": 0.85},
            "cycle_tags": ["controls_officer_to_peer", "branch_cycle", "visible_root"],
        },
        {
            "key": "marriage_bridge",
            "label": "결혼 연결력",
            "meaning": "연애가 생활 약속과 결혼 논의로 넘어가는 현실성입니다.",
            "axis_keys": ["marriage_timing_readiness", "marriage_stability", "spouse_match_quality"],
            "axis_weights": {"marriage_timing_readiness": 1.55, "marriage_stability": 1.1, "spouse_match_quality": 0.95},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "output_generates_wealth_then_officer"],
        },
        {
            "key": "opposite_sex_appeal",
            "label": "이성 대상 호감도",
            "meaning": "말과 태도, 표현 방식이 이성의 관심과 호감으로 이어지는 정도입니다.",
            "axis_keys": ["interpersonal_influence", "affection_expression", "relationship_progression", "affection_receptivity"],
            "axis_weights": {"interpersonal_influence": 1.55, "affection_expression": 1.25, "relationship_progression": 1.0, "affection_receptivity": 0.8},
            "cycle_tags": ["generates_peer_to_output", "element_generates", "branch_cycle"],
        },
        {
            "key": "romantic_emotional_stability",
            "label": "감정 안정성",
            "meaning": "연애 관계에서 감정의 기복을 조절하고 상대의 반응을 안정적으로 받아들이는 정도입니다.",
            "axis_keys": ["emotional_alignment", "affection_receptivity", "conflict_recovery", "misunderstanding_prevention"],
            "axis_weights": {"emotional_alignment": 1.55, "affection_receptivity": 1.15, "conflict_recovery": 1.0, "misunderstanding_prevention": 0.8},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "partner_dependency_control",
            "label": "상대 의존 조절력",
            "meaning": "연애 중에도 자기 기준과 생활의 균형을 잃지 않는 정도입니다.",
            "axis_keys": ["self_direction", "boundary_management", "emotional_alignment", "relationship_stability"],
            "axis_weights": {"self_direction": 1.55, "boundary_management": 1.3, "emotional_alignment": 1.0, "relationship_stability": 0.8},
            "cycle_tags": ["controls_officer_to_peer", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "bond_continuity",
            "label": "인연 지속성",
            "meaning": "환경과 감정의 변화 속에서도 중요한 인연을 오래 이어가는 정도입니다.",
            "axis_keys": ["relationship_stability", "conflict_recovery", "affection_receptivity", "decision_consistency"],
            "axis_weights": {"relationship_stability": 1.55, "conflict_recovery": 1.2, "affection_receptivity": 0.95, "decision_consistency": 0.8},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "breakup_resilience",
            "label": "이별 위험 방어력",
            "meaning": "거리감과 갈등이 커져도 관계가 단절로 넘어가지 않도록 조정하는 정도입니다.",
            "axis_keys": ["relationship_stability", "conflict_recovery", "boundary_management", "misunderstanding_prevention"],
            "axis_weights": {"relationship_stability": 1.55, "conflict_recovery": 1.3, "boundary_management": 1.0, "misunderstanding_prevention": 0.9},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
    ],
    "marriage": [
        {
            "key": "marriage_decision",
            "label": "혼인 성향",
            "meaning": "결혼을 막연히 미루지 않고 현실적인 약속으로 옮기는 정도입니다.",
            "axis_keys": ["marriage_timing_readiness", "decision_consistency", "responsibility_capacity"],
            "axis_weights": {"marriage_timing_readiness": 1.55, "decision_consistency": 1.1, "responsibility_capacity": 0.95},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "stem_combine"],
        },
        {
            "key": "marriage_realization",
            "label": "결혼 현실화력",
            "meaning": "연애와 결혼 의사가 혼인 절차, 주거 결정, 가족 협의로 실제 굳어지는 정도입니다.",
            "axis_keys": ["marriage_timing_readiness", "practical_planning", "household_stability", "decision_consistency", "spouse_match_quality"],
            "axis_weights": {"marriage_timing_readiness": 1.55, "practical_planning": 1.15, "household_stability": 1.0, "decision_consistency": 0.9, "spouse_match_quality": 0.8},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "output_generates_wealth_then_officer"],
        },
        {
            "key": "spouse_match",
            "label": "배우자상",
            "meaning": "배우자와 성격, 책임, 생활 기준이 맞는 정도입니다.",
            "axis_keys": ["spouse_match_quality", "spouse_support_benefit", "marriage_stability", "relationship_stability"],
            "axis_weights": {"spouse_match_quality": 1.55, "spouse_support_benefit": 1.15, "marriage_stability": 1.0, "relationship_stability": 0.75},
            "cycle_tags": ["officer", "wealth", "branch_cycle"],
        },
        {
            "key": "household_stability",
            "label": "생활 안정",
            "meaning": "주거, 생활비, 역할 분담이 결혼 생활의 기반으로 자리 잡는 정도입니다.",
            "axis_keys": ["household_stability", "asset_retention", "practical_planning"],
            "axis_weights": {"household_stability": 1.6, "asset_retention": 1.0, "practical_planning": 0.9},
            "cycle_tags": ["controls_wealth_to_resource", "officer_generates_resource", "visible_root"],
        },
        {
            "key": "household_management",
            "label": "가정 운영력",
            "meaning": "결혼 뒤 집안의 일정, 지출, 역할, 가족 책임을 안정적으로 운영하는 정도입니다.",
            "axis_keys": ["household_stability", "household_finance_alignment", "practical_planning", "family_responsibility", "responsibility_capacity"],
            "axis_weights": {"household_stability": 1.45, "household_finance_alignment": 1.2, "practical_planning": 1.05, "family_responsibility": 0.95, "responsibility_capacity": 0.8},
            "cycle_tags": ["officer_generates_resource", "controls_wealth_to_resource", "visible_root"],
        },
        {
            "key": "housing_life_design",
            "label": "주거·생활 설계력",
            "meaning": "집, 생활비, 시간 사용, 역할 분담을 결혼 생활의 현실 조건으로 정리하는 힘입니다.",
            "axis_keys": ["household_stability", "practical_planning", "asset_retention", "money_attitude"],
            "axis_weights": {"household_stability": 1.45, "practical_planning": 1.25, "asset_retention": 0.9, "money_attitude": 0.85},
            "cycle_tags": ["controls_wealth_to_resource", "wealth_controls_resource", "officer_generates_resource"],
        },
        {
            "key": "couple_finance",
            "label": "부부 재정",
            "meaning": "결혼 뒤 생활비, 명의, 공동 자산을 안정적으로 맞추는 정도입니다.",
            "axis_keys": ["household_finance_alignment", "asset_retention", "ownership_clarity", "deal_selection", "household_stability", "spending_control"],
            "axis_weights": {"household_finance_alignment": 1.55, "ownership_clarity": 1.15, "asset_retention": 1.0, "spending_control": 0.9, "deal_selection": 0.8, "household_stability": 0.7},
            "cycle_tags": ["wealth_generates_officer_controls_peer", "controls_peer_to_wealth", "generates_wealth_to_officer"],
        },
        {
            "key": "living_cost_standard",
            "label": "생활비 기준성",
            "meaning": "부부 생활비, 반복 지출, 저축 기준을 감정 문제가 되기 전에 정리하는 정도입니다.",
            "axis_keys": ["household_finance_alignment", "spending_control", "money_attitude", "ownership_clarity", "asset_retention"],
            "axis_weights": {"household_finance_alignment": 1.45, "spending_control": 1.2, "money_attitude": 1.0, "ownership_clarity": 0.9, "asset_retention": 0.8},
            "cycle_tags": ["wealth_controls_resource", "controls_wealth_to_resource", "wealth_generates_officer_controls_peer"],
        },
        {
            "key": "spouse_benefit",
            "label": "배우자 복",
            "meaning": "배우자로 인해 얻는 안정과 함께 따라오는 부담의 크기를 구분하는 기준입니다.",
            "axis_keys": ["spouse_support_benefit", "spouse_match_quality", "marriage_stability", "household_stability"],
            "axis_weights": {"spouse_support_benefit": 1.6, "spouse_match_quality": 1.1, "marriage_stability": 0.95, "household_stability": 0.75},
            "cycle_tags": ["officer_generates_resource", "generates_wealth_to_officer", "wealth_generates_officer"],
        },
        {
            "key": "marital_conflict_trigger",
            "label": "부부 갈등 조정력",
            "meaning": "생활비, 가족 개입, 역할 분담, 말투와 거리감에서 생기는 갈등을 조정하는 힘입니다.",
            "axis_keys": ["marriage_crisis_management", "family_responsibility", "household_finance_alignment", "communication_expression", "boundary_management"],
            "axis_weights": {"marriage_crisis_management": 1.45, "family_responsibility": 1.2, "boundary_management": 1.05, "household_finance_alignment": 0.9, "communication_expression": 0.7},
            "cycle_tags": ["branch_cycle", "controls_output_to_officer", "controls_officer_to_peer", "controls_peer_to_wealth"],
        },
        {
            "key": "family_responsibility",
            "label": "가족 책임 경계력",
            "meaning": "배우자 가족, 부모, 자녀 문제에서 어디까지 맡고 어디서 선을 그을지 정리하는 정도입니다.",
            "axis_keys": ["family_responsibility", "inlaw_boundary_strength", "responsibility_capacity", "boundary_management"],
            "axis_weights": {"family_responsibility": 1.55, "inlaw_boundary_strength": 1.2, "responsibility_capacity": 0.95, "boundary_management": 0.9},
            "cycle_tags": ["controls_officer_to_peer", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "inlaw_family_boundary",
            "label": "배우자 가족 경계",
            "meaning": "배우자 가족과 원가족 사이에서 책임, 돈, 간섭의 선을 세우는 정도입니다.",
            "axis_keys": ["inlaw_boundary_strength", "family_responsibility", "boundary_management", "responsibility_capacity", "conflict_recovery"],
            "axis_weights": {"inlaw_boundary_strength": 1.6, "family_responsibility": 1.2, "boundary_management": 1.05, "responsibility_capacity": 0.85, "conflict_recovery": 0.75},
            "cycle_tags": ["controls_officer_to_peer", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "child_rearing_responsibility",
            "label": "자녀·양육 책임",
            "meaning": "자녀, 양육, 돌봄 책임이 결혼 생활과 부부 재정 안에서 안정적으로 배분되는 정도입니다.",
            "axis_keys": ["family_responsibility", "household_stability", "responsibility_capacity", "practical_planning", "conflict_recovery"],
            "axis_weights": {"family_responsibility": 1.45, "household_stability": 1.2, "responsibility_capacity": 1.05, "practical_planning": 0.95, "conflict_recovery": 0.8},
            "cycle_tags": ["generates_peer_to_output", "officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "marriage_maintenance",
            "label": "결혼 지속력",
            "meaning": "갈등 이후에도 관계와 생활을 다시 정돈할 수 있는 정도입니다.",
            "axis_keys": ["marriage_stability", "marriage_crisis_management", "conflict_recovery", "household_stability"],
            "axis_weights": {"marriage_stability": 1.5, "marriage_crisis_management": 1.2, "conflict_recovery": 1.0, "household_stability": 0.85},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "marriage_crisis_tolerance",
            "label": "혼인 위기 대응력",
            "meaning": "돈, 가족, 주거, 역할 문제가 커졌을 때 결혼 생활이 무너지지 않고 버티는 정도입니다.",
            "axis_keys": ["marriage_crisis_management", "conflict_recovery", "family_responsibility", "household_finance_alignment", "household_stability"],
            "axis_weights": {"marriage_crisis_management": 1.5, "conflict_recovery": 1.15, "family_responsibility": 1.05, "household_finance_alignment": 0.95, "household_stability": 0.8},
            "cycle_tags": ["branch_cycle", "controls_officer_to_peer", "officer_generates_resource", "controls_peer_to_wealth"],
        },
        {
            "key": "couple_conflict_repair",
            "label": "부부 갈등 회복성",
            "meaning": "감정이 상한 뒤에도 대화, 생활 기준, 책임 범위를 다시 맞추는 힘입니다.",
            "axis_keys": ["marriage_crisis_management", "conflict_recovery", "marriage_stability", "boundary_management", "communication_expression"],
            "axis_weights": {"marriage_crisis_management": 1.4, "conflict_recovery": 1.25, "marriage_stability": 1.0, "boundary_management": 0.9, "communication_expression": 0.75},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "marriage_overall_stability",
            "label": "결혼 안정성",
            "meaning": "부부 관계와 생활 기반이 외부 변수에도 크게 흔들리지 않고 유지되는 정도입니다.",
            "axis_keys": ["marriage_stability", "household_stability", "marriage_crisis_management", "relationship_stability"],
            "axis_weights": {"marriage_stability": 1.55, "household_stability": 1.2, "marriage_crisis_management": 1.0, "relationship_stability": 0.8},
            "primary_axis_key": "marriage_stability",
            "corroboration_weights": {"household_stability": 0.15, "marriage_crisis_management": 0.12, "relationship_stability": 0.10},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "household_coordination",
            "label": "생활 조율성",
            "meaning": "주거, 시간, 역할과 생활 습관을 부부가 현실적으로 맞추는 정도입니다.",
            "axis_keys": ["household_stability", "household_finance_alignment", "family_responsibility", "conflict_recovery"],
            "axis_weights": {"household_stability": 1.35, "household_finance_alignment": 1.2, "family_responsibility": 1.0, "conflict_recovery": 0.8},
            "primary_axis_key": "household_stability",
            "corroboration_weights": {"household_finance_alignment": 0.14, "family_responsibility": 0.10, "conflict_recovery": 0.14},
            "cycle_tags": ["officer_generates_resource", "controls_peer_to_wealth", "branch_cycle"],
        },
        {
            "key": "marital_financial_agreement",
            "label": "재정 합의성",
            "meaning": "생활비, 저축, 투자와 공동 지출의 기준을 부부가 합의하는 정도입니다.",
            "axis_keys": ["household_finance_alignment", "money_attitude", "decision_consistency", "boundary_management"],
            "axis_weights": {"household_finance_alignment": 1.55, "money_attitude": 1.15, "decision_consistency": 1.0, "boundary_management": 0.8},
            "primary_axis_key": "household_finance_alignment",
            "corroboration_weights": {"money_attitude": 0.15, "decision_consistency": 0.12, "boundary_management": 0.10},
            "cycle_tags": ["controls_peer_to_wealth", "wealth_generates_officer_controls_peer", "officer_generates_resource"],
        },
        {
            "key": "family_relationship_stability",
            "label": "가족 관계성",
            "meaning": "원가족과 배우자 가족 사이의 책임과 개입 범위를 안정적으로 정리하는 정도입니다.",
            "axis_keys": ["inlaw_boundary_strength", "family_responsibility", "conflict_recovery", "household_stability"],
            "axis_weights": {"inlaw_boundary_strength": 1.35, "family_responsibility": 1.2, "conflict_recovery": 1.0, "household_stability": 0.8},
            "primary_axis_key": "inlaw_boundary_strength",
            "corroboration_weights": {"family_responsibility": 0.16, "conflict_recovery": 0.14, "household_stability": 0.08},
            "cycle_tags": ["controls_officer_to_peer", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "long_term_marriage",
            "label": "장기 유지성",
            "meaning": "시간이 지나도 결혼 생활의 책임, 신뢰와 생활 기반을 유지하는 정도입니다.",
            "axis_keys": ["marriage_stability", "marriage_crisis_management", "household_stability", "conflict_recovery"],
            "axis_weights": {"marriage_stability": 1.55, "marriage_crisis_management": 1.3, "household_stability": 1.0, "conflict_recovery": 0.9},
            "primary_axis_key": "marriage_crisis_management",
            "corroboration_weights": {"marriage_stability": 0.18, "household_stability": 0.12, "conflict_recovery": 0.12},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "spouse_conflict_control",
            "label": "배우자 충돌 조정력",
            "meaning": "반복되는 의견 차이와 감정 충돌이 관계 단절로 번지지 않게 조정하는 정도입니다.",
            "axis_keys": ["marriage_crisis_management", "conflict_recovery", "emotional_alignment", "household_finance_alignment", "boundary_management"],
            "axis_weights": {"marriage_crisis_management": 1.45, "conflict_recovery": 1.25, "emotional_alignment": 1.0, "household_finance_alignment": 0.8, "boundary_management": 0.75},
            "primary_axis_key": "conflict_recovery",
            "corroboration_weights": {"marriage_crisis_management": 0.16, "emotional_alignment": 0.12, "household_finance_alignment": 0.08, "boundary_management": 0.08},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "post_marriage_stability",
            "label": "결혼 후 안정도",
            "meaning": "결혼 이후 주거, 재정, 가족 책임과 부부 관계가 안정적으로 자리 잡는 정도입니다.",
            "axis_keys": ["spouse_support_benefit", "household_stability", "household_finance_alignment", "family_responsibility", "marriage_stability"],
            "axis_weights": {"spouse_support_benefit": 1.55, "household_stability": 1.2, "household_finance_alignment": 1.0, "family_responsibility": 0.85, "marriage_stability": 0.75},
            "primary_axis_key": "spouse_support_benefit",
            "corroboration_weights": {"household_stability": 0.24, "household_finance_alignment": 0.10, "family_responsibility": 0.08, "marriage_stability": 0.12},
            "cycle_tags": ["officer_generates_resource", "controls_peer_to_wealth", "visible_root"],
        },
    ],
    "personality": [
        {
            "key": "self_direction",
            "label": "자기 기준",
            "meaning": "타인의 기대나 분위기에 휩쓸리지 않고 자신의 가치관과 판단 원칙에 따라 선택하는 정도입니다.",
            "axis_keys": ["self_direction", "decision_consistency", "practical_planning", "academic_expertise"],
            "axis_weights": {"self_direction": 1.55, "decision_consistency": 1.25, "practical_planning": 1.0, "academic_expertise": 0.65},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "visible_root"],
        },
        {
            "key": "emotional_alignment",
            "label": "감정 조절",
            "meaning": "감정이 올라왔을 때 충동적으로 반응하지 않고 상황과 관계에 맞게 정리하는 정도입니다.",
            "axis_keys": ["emotional_alignment", "conflict_recovery", "misunderstanding_prevention", "communication_expression"],
            "axis_weights": {"emotional_alignment": 1.55, "conflict_recovery": 1.15, "misunderstanding_prevention": 0.95, "communication_expression": 0.7},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "branch_cycle"],
        },
        {
            "key": "action_pace",
            "label": "실행 속도",
            "meaning": "판단한 내용을 실제 행동으로 옮기고 결과를 확인하는 속도입니다.",
            "axis_keys": ["change_adaptability", "self_direction", "business_expansion", "communication_expression"],
            "axis_weights": {"change_adaptability": 1.5, "self_direction": 1.2, "business_expansion": 0.95, "communication_expression": 0.75},
            "cycle_tags": ["generates_peer_to_output", "output", "element_generates"],
        },
        {
            "key": "decision_consistency",
            "label": "신중성",
            "meaning": "행동하기 전에 정보, 결과, 위험과 타인에게 미칠 영향을 검토하는 정도입니다.",
            "axis_keys": ["decision_consistency", "practical_planning", "loss_avoidance", "deal_selection"],
            "axis_weights": {"decision_consistency": 1.55, "practical_planning": 1.25, "loss_avoidance": 1.0, "deal_selection": 0.8},
            "cycle_tags": ["officer_generates_resource", "visible_root", "wealth_controls_resource"],
        },
        {
            "key": "focus_depth",
            "label": "몰입 성향",
            "meaning": "한 대상이나 과제에 주의와 에너지를 깊게 집중하고 지속하는 정도입니다.",
            "axis_keys": ["academic_expertise", "career_achievement", "self_direction", "responsibility_capacity"],
            "axis_weights": {"academic_expertise": 1.45, "career_achievement": 1.15, "self_direction": 1.0, "responsibility_capacity": 0.85},
            "cycle_tags": ["visible_root", "same_element_root", "officer_generates_resource"],
        },
        {
            "key": "boundary_management",
            "label": "관계 거리 조절력",
            "meaning": "사람과 가까워지는 속도와 개인 영역의 범위를 관계의 단계와 상황에 맞게 조절하는 능력입니다.",
            "axis_keys": ["boundary_management", "interpersonal_influence", "conflict_recovery", "misunderstanding_prevention"],
            "axis_weights": {"boundary_management": 1.55, "interpersonal_influence": 1.0, "conflict_recovery": 0.95, "misunderstanding_prevention": 0.8},
            "cycle_tags": ["controls_officer_to_peer", "wealth_generates_officer_controls_peer", "branch_cycle"],
        },
        {
            "key": "crisis_recovery",
            "label": "문제 해결력",
            "meaning": "문제가 생겼을 때 원인을 구분하고 대안을 실행해 상황을 개선하는 정도입니다.",
            "axis_keys": ["crisis_recovery", "responsibility_capacity", "practical_planning", "change_adaptability"],
            "axis_weights": {"crisis_recovery": 1.55, "responsibility_capacity": 1.2, "practical_planning": 1.0, "change_adaptability": 0.85},
            "cycle_tags": ["eating_god_controls_seven_killings", "officer_generates_resource", "visible_root"],
        },
        {
            "key": "change_adaptability",
            "label": "변화 수용성",
            "meaning": "예상과 다른 상황이 생겼을 때 기존 방식을 조정하고 새 조건에 적응하는 정도입니다.",
            "axis_keys": ["change_adaptability", "crisis_recovery", "organization_adaptability", "self_direction"],
            "axis_weights": {"change_adaptability": 1.55, "crisis_recovery": 1.15, "organization_adaptability": 1.0, "self_direction": 0.75},
            "cycle_tags": ["branch_cycle", "element_generates", "controls_resource_to_output"],
        },
        {
            "key": "communication_expression",
            "label": "표현 방식",
            "meaning": "생각과 감정을 말, 글, 표정과 행동으로 전달하는 방식의 안정성입니다.",
            "axis_keys": ["communication_expression", "affection_expression", "interpersonal_influence", "emotional_alignment"],
            "axis_weights": {"communication_expression": 1.55, "affection_expression": 1.1, "interpersonal_influence": 0.95, "emotional_alignment": 0.75},
            "cycle_tags": ["generates_peer_to_output", "controls_resource_to_output", "output"],
        },
        {
            "key": "responsibility_capacity",
            "label": "책임 감각",
            "meaning": "맡은 역할의 범위와 결과를 인식하고 끝까지 감당하는 정도입니다.",
            "axis_keys": ["responsibility_capacity", "family_responsibility", "role_authority_alignment", "asset_retention"],
            "axis_weights": {"responsibility_capacity": 1.55, "family_responsibility": 1.1, "role_authority_alignment": 1.0, "asset_retention": 0.75},
            "cycle_tags": ["officer_generates_resource", "visible_root", "generates_wealth_to_officer"],
        },
        {
            "key": "honor_recognition",
            "label": "인정 욕구",
            "meaning": "자신의 능력과 성과가 타인과 사회에서 인정받기를 바라는 정도입니다.",
            "axis_keys": ["honor_recognition", "promotion_visibility", "social_success_potential", "interpersonal_influence"],
            "axis_weights": {"honor_recognition": 1.55, "promotion_visibility": 1.2, "social_success_potential": 1.0, "interpersonal_influence": 0.75},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "visible_root"],
        },
        {
            "key": "loss_avoidance",
            "label": "위험 감지",
            "meaning": "손실, 갈등, 실수로 이어질 수 있는 신호를 미리 알아차리고 대비하는 정도입니다.",
            "axis_keys": ["loss_avoidance", "deal_selection", "misunderstanding_prevention", "crisis_recovery"],
            "axis_weights": {"loss_avoidance": 1.55, "deal_selection": 1.2, "misunderstanding_prevention": 1.0, "crisis_recovery": 0.8},
            "cycle_tags": ["controls_peer_to_wealth", "branch_cycle", "visible_root"],
        },
    ],
    "honor": [
        {
            "key": "honor_social_recognition",
            "label": "사회적 인정",
            "meaning": "능력과 성과가 조직과 사회의 공식 평가로 확인되는 정도입니다.",
            "axis_keys": ["honor_recognition", "promotion_visibility", "reputation_maintenance", "social_success_potential", "career_achievement"],
            "axis_weights": {"honor_recognition": 1.55, "promotion_visibility": 1.25, "reputation_maintenance": 1.05, "social_success_potential": 0.9, "career_achievement": 0.75},
            "primary_axis_key": "honor_recognition",
            "corroboration_weights": {"promotion_visibility": 0.12, "reputation_maintenance": 0.08, "social_success_potential": 0.08, "career_achievement": 0.06},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "output_generates_wealth_then_officer"],
        },
        {
            "key": "honor_reputation_formation",
            "label": "평판 형성",
            "meaning": "반복된 결과와 책임 이력이 안정된 평판으로 축적되는 정도입니다.",
            "axis_keys": ["reputation_maintenance", "decision_consistency", "responsibility_capacity", "misunderstanding_prevention", "communication_expression"],
            "axis_weights": {"reputation_maintenance": 1.55, "decision_consistency": 1.2, "responsibility_capacity": 1.05, "misunderstanding_prevention": 0.9, "communication_expression": 0.7},
            "primary_axis_key": "reputation_maintenance",
            "corroboration_weights": {"decision_consistency": 0.12, "responsibility_capacity": 0.10, "misunderstanding_prevention": 0.10, "communication_expression": 0.05},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "visible_root"],
        },
        {
            "key": "honor_title_rise",
            "label": "직함 상승성",
            "meaning": "실적과 책임이 승진, 직급, 자격, 공식 직함으로 이어지는 정도입니다.",
            "axis_keys": ["promotion_visibility", "role_authority_alignment", "honor_recognition", "organization_adaptability", "career_achievement"],
            "axis_weights": {"promotion_visibility": 1.55, "role_authority_alignment": 1.25, "honor_recognition": 1.1, "organization_adaptability": 0.9, "career_achievement": 0.75},
            "primary_axis_key": "promotion_visibility",
            "corroboration_weights": {"role_authority_alignment": 0.12, "honor_recognition": 0.10, "organization_adaptability": 0.08, "career_achievement": 0.06},
            "cycle_tags": ["generates_wealth_to_officer", "officer_generates_resource", "wealth_generates_officer_controls_peer"],
        },
        {
            "key": "honor_public_trust",
            "label": "공적 신뢰도",
            "meaning": "공식 역할과 약속을 맡길 만한 사람으로 신뢰받는 정도입니다.",
            "axis_keys": ["reputation_maintenance", "responsibility_capacity", "decision_consistency", "organization_adaptability", "misunderstanding_prevention"],
            "axis_weights": {"reputation_maintenance": 1.45, "responsibility_capacity": 1.3, "decision_consistency": 1.1, "organization_adaptability": 0.9, "misunderstanding_prevention": 0.8},
            "primary_axis_key": "organization_adaptability",
            "corroboration_weights": {"responsibility_capacity": 0.14, "reputation_maintenance": 0.12, "decision_consistency": 0.08, "misunderstanding_prevention": 0.08},
            "cycle_tags": ["officer_generates_resource", "controls_officer_to_peer", "visible_root"],
        },
        {
            "key": "honor_responsibility_acceptance",
            "label": "책임 수용도",
            "meaning": "공적인 책임의 범위와 결과를 인식하고 끝까지 감당하는 정도입니다.",
            "axis_keys": ["responsibility_capacity", "role_authority_alignment", "practical_planning", "crisis_recovery", "decision_consistency"],
            "axis_weights": {"responsibility_capacity": 1.55, "role_authority_alignment": 1.2, "practical_planning": 1.0, "crisis_recovery": 0.9, "decision_consistency": 0.75},
            "primary_axis_key": "responsibility_capacity",
            "corroboration_weights": {"role_authority_alignment": 0.12, "practical_planning": 0.08, "crisis_recovery": 0.08, "decision_consistency": 0.08},
            "cycle_tags": ["officer_generates_resource", "controls_officer_to_peer", "eating_god_controls_seven_killings"],
        },
        {
            "key": "honor_organizational_presence",
            "label": "조직 내 존재감",
            "meaning": "조직 안에서 의견과 성과가 주변의 판단과 결정에 영향을 미치는 정도입니다.",
            "axis_keys": ["social_success_potential", "interpersonal_influence", "leadership_potential", "career_achievement", "communication_expression"],
            "axis_weights": {"social_success_potential": 1.45, "interpersonal_influence": 1.25, "leadership_potential": 1.1, "career_achievement": 0.9, "communication_expression": 0.75},
            "primary_axis_key": "leadership_potential",
            "corroboration_weights": {"social_success_potential": 0.12, "interpersonal_influence": 0.12, "career_achievement": 0.08, "communication_expression": 0.08},
            "cycle_tags": ["generates_peer_to_output", "output_generates_wealth_then_officer", "generates_wealth_to_officer"],
        },
        {
            "key": "honor_authority_establishment",
            "label": "권위 확보력",
            "meaning": "책임을 맡을 때 결정권과 공식 권한까지 함께 확보되는 정도입니다.",
            "axis_keys": ["role_authority_alignment", "leadership_potential", "promotion_visibility", "responsibility_capacity", "decision_consistency"],
            "axis_weights": {"role_authority_alignment": 1.55, "leadership_potential": 1.25, "promotion_visibility": 1.1, "responsibility_capacity": 0.95, "decision_consistency": 0.8},
            "primary_axis_key": "role_authority_alignment",
            "corroboration_weights": {"leadership_potential": 0.16, "promotion_visibility": 0.12, "responsibility_capacity": 0.10, "decision_consistency": 0.08},
            "cycle_tags": ["wealth_generates_officer_controls_peer", "controls_officer_to_peer", "generates_wealth_to_officer"],
        },
        {
            "key": "honor_legitimacy_management",
            "label": "명분 관리",
            "meaning": "결정과 행동의 근거를 분명히 하여 공식적인 정당성을 지키는 정도입니다.",
            "axis_keys": ["decision_consistency", "reputation_maintenance", "communication_expression", "loss_avoidance", "misunderstanding_prevention"],
            "axis_weights": {"decision_consistency": 1.45, "reputation_maintenance": 1.25, "communication_expression": 1.0, "loss_avoidance": 0.9, "misunderstanding_prevention": 0.8},
            "primary_axis_key": "decision_consistency",
            "corroboration_weights": {"reputation_maintenance": 0.12, "communication_expression": 0.08, "loss_avoidance": 0.10, "misunderstanding_prevention": 0.10},
            "cycle_tags": ["officer_generates_resource", "controls_resource_to_output", "wealth_controls_resource"],
        },
    ],
    "social": [
        {
            "key": "social_affinity",
            "label": "친화성",
            "meaning": "새로운 사람과 자연스럽게 접점을 만들고 관계의 문을 여는 정도입니다.",
            "axis_keys": ["interpersonal_influence", "affection_receptivity", "communication_expression", "relationship_progression"],
            "axis_weights": {"interpersonal_influence": 1.55, "affection_receptivity": 1.2, "communication_expression": 1.0, "relationship_progression": 0.85},
            "cycle_tags": ["generates_peer_to_output", "element_generates", "branch_cycle"],
        },
        {
            "key": "social_trust_formation",
            "label": "신뢰 형성",
            "meaning": "말과 행동의 일관성을 통해 다른 사람의 신뢰를 얻는 정도입니다.",
            "axis_keys": ["reputation_maintenance", "relationship_stability", "decision_consistency", "misunderstanding_prevention", "responsibility_capacity"],
            "axis_weights": {"reputation_maintenance": 1.45, "relationship_stability": 1.25, "decision_consistency": 1.05, "misunderstanding_prevention": 0.9, "responsibility_capacity": 0.75},
            "cycle_tags": ["officer_generates_resource", "visible_root", "branch_cycle"],
        },
        {
            "key": "social_relationship_continuity",
            "label": "관계 유지성",
            "meaning": "가까워진 관계를 갈등과 환경 변화 속에서도 오래 유지하는 정도입니다.",
            "axis_keys": ["relationship_stability", "conflict_recovery", "boundary_management", "misunderstanding_prevention", "interpersonal_influence"],
            "axis_weights": {"relationship_stability": 1.55, "conflict_recovery": 1.25, "boundary_management": 1.0, "misunderstanding_prevention": 0.9, "interpersonal_influence": 0.7},
            "cycle_tags": ["branch_cycle", "officer_generates_resource", "controls_resource_to_output"],
        },
        {
            "key": "social_distance_control",
            "label": "거리 조절",
            "meaning": "관계의 친밀도와 책임 범위를 상황에 맞게 조절하는 정도입니다.",
            "axis_keys": ["boundary_management", "emotional_alignment", "conflict_recovery", "self_direction", "interpersonal_influence"],
            "axis_weights": {"boundary_management": 1.55, "emotional_alignment": 1.2, "conflict_recovery": 1.0, "self_direction": 0.9, "interpersonal_influence": 0.75},
            "cycle_tags": ["controls_officer_to_peer", "wealth_generates_officer_controls_peer", "branch_cycle"],
        },
        {
            "key": "social_cooperation",
            "label": "협력성",
            "meaning": "역할과 책임을 나누어 공동의 결과를 만드는 정도입니다.",
            "axis_keys": ["interpersonal_influence", "organization_adaptability", "communication_expression", "responsibility_capacity", "conflict_recovery"],
            "axis_weights": {"interpersonal_influence": 1.45, "organization_adaptability": 1.25, "communication_expression": 1.05, "responsibility_capacity": 0.9, "conflict_recovery": 0.8},
            "cycle_tags": ["officer_generates_resource", "generates_peer_to_output", "controls_officer_to_peer"],
        },
        {
            "key": "social_competition_control",
            "label": "경쟁 관리력",
            "meaning": "비교와 경쟁이 강해져도 관계와 자기 몫을 안정적으로 지키는 정도입니다.",
            "axis_keys": ["boundary_management", "loss_avoidance", "emotional_alignment", "role_authority_alignment", "misunderstanding_prevention"],
            "axis_weights": {"boundary_management": 1.5, "loss_avoidance": 1.25, "emotional_alignment": 1.05, "role_authority_alignment": 0.9, "misunderstanding_prevention": 0.8},
            "cycle_tags": ["controls_peer_to_wealth", "controls_officer_to_peer", "wealth_generates_officer_controls_peer"],
        },
        {
            "key": "social_speech_influence",
            "label": "말의 영향력",
            "meaning": "말과 설명이 주변의 판단과 행동에 영향을 미치는 정도입니다.",
            "axis_keys": ["communication_expression", "interpersonal_influence", "reputation_maintenance", "emotional_alignment", "misunderstanding_prevention"],
            "axis_weights": {"communication_expression": 1.55, "interpersonal_influence": 1.25, "reputation_maintenance": 1.0, "emotional_alignment": 0.85, "misunderstanding_prevention": 0.75},
            "cycle_tags": ["generates_peer_to_output", "controls_resource_to_output", "output"],
        },
        {
            "key": "social_conflict_avoidance",
            "label": "갈등 회피력",
            "meaning": "오해와 감정 충돌이 커지기 전에 관계를 조정하는 정도입니다.",
            "axis_keys": ["misunderstanding_prevention", "conflict_recovery", "emotional_alignment", "boundary_management", "communication_expression"],
            "axis_weights": {"misunderstanding_prevention": 1.5, "conflict_recovery": 1.25, "emotional_alignment": 1.05, "boundary_management": 0.9, "communication_expression": 0.75},
            "cycle_tags": ["controls_resource_to_output", "officer_generates_resource", "branch_cycle"],
        },
        {
            "key": "social_benefactor_support",
            "label": "지인 덕",
            "meaning": "주변 인연이 소개, 정보, 협력과 실질적인 도움으로 이어지는 정도입니다.",
            "axis_keys": ["interpersonal_influence", "reputation_maintenance", "relationship_stability", "organization_adaptability", "affection_receptivity"],
            "axis_weights": {"interpersonal_influence": 1.45, "reputation_maintenance": 1.2, "relationship_stability": 1.05, "organization_adaptability": 0.9, "affection_receptivity": 0.75},
            "cycle_tags": ["officer_generates_resource", "element_generates", "branch_cycle"],
        },
        {
            "key": "social_acquaintance_loss_defense",
            "label": "지인 손실 방어력",
            "meaning": "지인의 부탁, 금전 거래, 공동 책임에서 손실을 줄이는 정도입니다.",
            "axis_keys": ["loss_avoidance", "boundary_management", "shared_asset_boundary", "deal_selection", "misunderstanding_prevention"],
            "axis_weights": {"loss_avoidance": 1.55, "boundary_management": 1.3, "shared_asset_boundary": 1.1, "deal_selection": 0.9, "misunderstanding_prevention": 0.75},
            "cycle_tags": ["controls_peer_to_wealth", "wealth_generates_officer_controls_peer", "controls_officer_to_peer"],
        },
    ],
}


DOMAIN_DECISION_FACET_LAYER_FOCUS: dict[str, list[str]] = {
    "wealth_formation": ["월령·격국", "오행·조후", "십신·생극"],
    "wealth_scale_expansion": ["월령·격국", "십신·생극", "오행·조후", "지지·지장간"],
    "income_generation": ["월령·격국", "십신·생극", "천간·투출", "지지·지장간"],
    "talent_monetization": ["오행·조후", "십신·생극", "수용·배합"],
    "performance_reward": ["월령·격국", "십신·생극", "천간·투출"],
    "asset_consolidation": ["지지·지장간", "십신·생극", "천간·투출"],
    "cashflow_stability": ["월령·격국", "십신·생극", "지지·지장간"],
    "shared_money_control": ["십신·생극", "지지·지장간", "합충형파해"],
    "debt_guarantee_control": ["십신·생극", "합충형파해", "천간·투출"],
    "family_asset_boundary": ["지지·지장간", "십신·생극", "합충형파해"],
    "contract_title_stability": ["십신·생극", "천간·투출", "지지·지장간"],
    "receivables_recovery": ["십신·생극", "천간·투출", "월령·격국"],
    "investment_trading_judgment": ["오행·조후", "십신·생극", "수용·배합"],
    "financial_loss_defense": ["월령·격국", "십신·생극", "합충형파해"],
    "late_life_wealth_growth": ["월령·격국", "지지·지장간", "천간·투출"],
    "money_standard": ["월령·격국", "십신·생극", "수용·배합"],
    "business_expansion": ["오행·조후", "십신·생극", "합충형파해"],
    "field_fit": ["월령·격국", "오행·조후", "십신·생극"],
    "career_field_domain": ["월령·격국", "오행·조후", "수용·배합"],
    "achievement_accumulation": ["월령·격국", "십신·생극", "지지·지장간"],
    "professional_depth": ["십신·생극", "천간·투출", "지지·지장간"],
    "authority_scope": ["월령·격국", "십신·생극", "천간·투출"],
    "recognition": ["월령·격국", "십신·생극", "수용·배합"],
    "promotion_title_readiness": ["월령·격국", "십신·생극", "천간·투출"],
    "social_ascent": ["월령·격국", "십신·생극", "오행·조후"],
    "responsibility_authority_balance": ["월령·격국", "십신·생극", "합충형파해"],
    "compensation_negotiation": ["십신·생극", "천간·투출", "월령·격국"],
    "organization_fit": ["월령·격국", "십신·생극", "지지·지장간"],
    "affiliation_transition": ["합충형파해", "십신·생극", "지지·지장간"],
    "unsuitable_work_filter": ["십신·생극", "합충형파해", "수용·배합"],
    "independent_work": ["오행·조후", "십신·생극", "수용·배합"],
    "practical_execution": ["월령·격국", "십신·생극", "지지·지장간"],
    "planning_judgment": ["월령·격국", "십신·생극", "수용·배합"],
    "evaluation_management": ["월령·격국", "십신·생극", "천간·투출"],
    "career_continuity": ["월령·격국", "지지·지장간", "십신·생극"],
    "relationship_opening": ["합충형파해", "오행·조후", "십신·생극"],
    "attraction_standard": ["십신·생극", "수용·배합", "지지·지장간"],
    "partner_selection": ["십신·생극", "지지·지장간", "수용·배합"],
    "partner_trust_filter": ["십신·생극", "지지·지장간", "합충형파해"],
    "affection_expression": ["오행·조후", "십신·생극", "수용·배합"],
    "emotional_receptivity": ["십신·생극", "지지·지장간", "수용·배합"],
    "relationship_progress": ["십신·생극", "합충형파해", "지지·지장간"],
    "relationship_agency": ["십신·생극", "수용·배합", "합충형파해"],
    "relationship_tempo_control": ["십신·생극", "합충형파해", "수용·배합"],
    "relationship_stability": ["지지·지장간", "합충형파해", "십신·생극"],
    "misunderstanding_prevention": ["십신·생극", "수용·배합", "합충형파해"],
    "conflict_trigger": ["합충형파해", "지지·지장간", "십신·생극"],
    "external_interference_control": ["지지·지장간", "합충형파해", "십신·생극"],
    "conflict_recovery": ["십신·생극", "합충형파해", "수용·배합"],
    "reconnection_capacity": ["지지·지장간", "합충형파해", "십신·생극"],
    "contact_distance_stability": ["지지·지장간", "십신·생극", "수용·배합"],
    "marriage_bridge": ["십신·생극", "지지·지장간", "천간·투출"],
    "opposite_sex_appeal": ["오행·조후", "십신·생극", "수용·배합"],
    "romantic_emotional_stability": ["십신·생극", "합충형파해", "수용·배합"],
    "partner_dependency_control": ["십신·생극", "지지·지장간", "합충형파해"],
    "bond_continuity": ["지지·지장간", "십신·생극", "합충형파해"],
    "breakup_resilience": ["지지·지장간", "십신·생극", "합충형파해"],
    "marriage_decision": ["월령·격국", "십신·생극", "천간·투출"],
    "marriage_realization": ["십신·생극", "지지·지장간", "천간·투출"],
    "spouse_match": ["지지·지장간", "십신·생극", "합충형파해"],
    "household_stability": ["지지·지장간", "십신·생극", "천간·투출"],
    "household_management": ["지지·지장간", "십신·생극", "월령·격국"],
    "housing_life_design": ["지지·지장간", "십신·생극", "수용·배합"],
    "couple_finance": ["십신·생극", "지지·지장간", "천간·투출"],
    "living_cost_standard": ["십신·생극", "지지·지장간", "수용·배합"],
    "spouse_benefit": ["십신·생극", "지지·지장간", "월령·격국"],
    "marital_conflict_trigger": ["합충형파해", "지지·지장간", "십신·생극"],
    "family_responsibility": ["십신·생극", "지지·지장간", "합충형파해"],
    "inlaw_family_boundary": ["십신·생극", "합충형파해", "수용·배합"],
    "child_rearing_responsibility": ["십신·생극", "지지·지장간", "월령·격국"],
    "marriage_maintenance": ["지지·지장간", "십신·생극", "합충형파해"],
    "marriage_crisis_tolerance": ["합충형파해", "지지·지장간", "십신·생극"],
    "couple_conflict_repair": ["십신·생극", "합충형파해", "수용·배합"],
    "marriage_overall_stability": ["월령·격국", "지지·지장간", "십신·생극"],
    "household_coordination": ["지지·지장간", "십신·생극", "수용·배합"],
    "marital_financial_agreement": ["십신·생극", "지지·지장간", "천간·투출"],
    "family_relationship_stability": ["지지·지장간", "합충형파해", "십신·생극"],
    "long_term_marriage": ["지지·지장간", "십신·생극", "합충형파해"],
    "spouse_conflict_control": ["합충형파해", "십신·생극", "수용·배합"],
    "post_marriage_stability": ["지지·지장간", "십신·생극", "월령·격국"],
    "self_direction": ["월령·격국", "십신·생극", "수용·배합"],
    "emotional_alignment": ["오행·조후", "십신·생극", "합충형파해"],
    "action_pace": ["십신·생극", "천간·투출", "수용·배합"],
    "decision_consistency": ["월령·격국", "십신·생극", "수용·배합"],
    "focus_depth": ["지지·지장간", "천간·투출", "십신·생극"],
    "boundary_management": ["지지·지장간", "십신·생극", "합충형파해"],
    "crisis_recovery": ["월령·격국", "십신·생극", "합충형파해"],
    "change_adaptability": ["오행·조후", "십신·생극", "합충형파해"],
    "communication_expression": ["오행·조후", "십신·생극", "수용·배합"],
    "responsibility_capacity": ["월령·격국", "지지·지장간", "십신·생극"],
    "honor_recognition": ["월령·격국", "천간·투출", "십신·생극"],
    "loss_avoidance": ["월령·격국", "십신·생극", "합충형파해"],
    "honor_social_recognition": ["월령·격국", "십신·생극", "천간·투출"],
    "honor_reputation_formation": ["월령·격국", "십신·생극", "수용·배합"],
    "honor_title_rise": ["월령·격국", "십신·생극", "천간·투출"],
    "honor_public_trust": ["월령·격국", "십신·생극", "지지·지장간"],
    "honor_responsibility_acceptance": ["월령·격국", "십신·생극", "지지·지장간"],
    "honor_organizational_presence": ["십신·생극", "천간·투출", "수용·배합"],
    "honor_authority_establishment": ["월령·격국", "십신·생극", "천간·투출"],
    "honor_legitimacy_management": ["월령·격국", "십신·생극", "수용·배합"],
    "social_affinity": ["오행·조후", "십신·생극", "수용·배합"],
    "social_trust_formation": ["월령·격국", "십신·생극", "지지·지장간"],
    "social_relationship_continuity": ["지지·지장간", "십신·생극", "합충형파해"],
    "social_distance_control": ["지지·지장간", "십신·생극", "합충형파해"],
    "social_cooperation": ["십신·생극", "수용·배합", "지지·지장간"],
    "social_competition_control": ["십신·생극", "합충형파해", "지지·지장간"],
    "social_speech_influence": ["오행·조후", "십신·생극", "수용·배합"],
    "social_conflict_avoidance": ["십신·생극", "합충형파해", "수용·배합"],
    "social_benefactor_support": ["월령·격국", "십신·생극", "지지·지장간"],
    "social_acquaintance_loss_defense": ["십신·생극", "합충형파해", "지지·지장간"],
}


def _facet_strength_label(score: int) -> str:
    if score >= 86:
        return "높음"
    if score >= 76:
        return "다소 높음"
    if score >= 64:
        return "보통"
    if score >= 52:
        return "보통"
    if score >= 40:
        return "다소 낮음"
    return "낮음"


def _domain_facet_layer_coverage(
    *,
    basis_codes: list[str],
    counter_signals: list[str],
    cycle_sources: list[dict[str, object]],
    principle_edges: list[dict[str, object]] | None = None,
) -> list[str]:
    code_text = " ".join(list(basis_codes) + list(counter_signals))
    source_text = " ".join(
        " ".join(
            str(source.get(key) or "")
            for key in ("signal_id", "relation", "status", "classical_name", "cycle_judgment")
        )
        for source in cycle_sources
    )
    edge_text = " ".join(
        " ".join(
            str(edge.get(key) or "")
            for key in ("edge_key", "classical_name", "scope", "domain_projection")
        )
        for edge in list(principle_edges or [])
    )
    layers: list[str] = []

    def has(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    if has(code_text, ("month_governance", "month_command", "regular_pattern", "feature_pattern_")) or any(
        str(source.get("month_cycle_fit_verdict") or "") for source in cycle_sources
    ):
        layers.append("월령·격국")
    if has(code_text, ("feature_element", "element_", "johu", "climate")) or has(source_text, ("element_", "element_generates", "element_controls")):
        layers.append("오행·조후")
    if cycle_sources or principle_edges or has(code_text, ("cycle_regulation", "ten_god", "generates_", "controls_")):
        layers.append("십신·생극")
    if has(code_text, ("branch_", "hidden_", "rooted", "protrusion")) or has(source_text, ("branch_cycle", "hidden_protrusion", "visible_root")):
        layers.append("지지·지장간")
    if has(code_text, ("stem_", "visible_", "heavenly")) or has(source_text, ("stem_combine", "hidden_protrusion")):
        layers.append("천간·투출")
    if has(code_text, ("six_combine", "three_harmony", "clash", "punishment", "break", "harm")) or has(source_text, ("branch_cycle",)):
        layers.append("합충형파해")
    if has(code_text, ("stem_reception", "integrated_saju", "combination")) or has(source_text + " " + edge_text, ("stem_reception", "integrated_saju", "combination")):
        layers.append("수용·배합")
    return layers


CHAIN_TAG_TO_PRINCIPLE_EDGES: dict[str, tuple[str, ...]] = {
    "wealth_generates_officer_controls_peer": ("wealth_generates_officer", "officer_controls_peer"),
    "wealth_controls_resource_releases_output": ("wealth_controls_resource", "resource_controls_output"),
    "output_controls_officer_reduces_pressure": ("output_controls_officer",),
    "officer_generates_resource_protects_body": ("officer_generates_resource",),
    "output_generates_wealth_then_officer": ("output_generates_wealth", "wealth_generates_officer"),
    "resource_controls_output_dosik": ("resource_controls_output",),
}


def _principle_edge_aliases(cycle_tags: list[str]) -> set[str]:
    aliases: set[str] = set()
    for tag in cycle_tags:
        if not tag:
            continue
        aliases.add(tag)
        aliases.update(CHAIN_TAG_TO_PRINCIPLE_EDGES.get(tag, ()))
        if tag.startswith("generates_") and "_to_" in tag:
            source_target = tag.removeprefix("generates_")
            aliases.add(source_target.replace("_to_", "_generates_"))
        elif tag.startswith("controls_") and "_to_" in tag:
            source_target = tag.removeprefix("controls_")
            aliases.add(source_target.replace("_to_", "_controls_"))
        elif tag == "peer_to_wealth":
            aliases.add("peer_controls_wealth")
    return aliases


def _principle_edge_scope_rank(scope: str) -> int:
    return {
        "active_support": 60,
        "active_mixed": 52,
        "active_pressure": 48,
        "reference": 40,
        "latent_reference": 34,
        "trace_reference": 24,
    }.get(scope, 0)


def _domain_facet_principle_edges(
    *,
    cycle_regulation_profile: dict[str, object] | None,
    domain: str,
    cycle_tags: list[str],
) -> list[dict[str, object]]:
    if not cycle_regulation_profile:
        return []
    matrix = cycle_regulation_profile.get("principle_matrix")
    if not isinstance(matrix, dict):
        return []
    aliases = _principle_edge_aliases(cycle_tags)
    role_edges = [edge for edge in list(matrix.get("role_edges") or []) if isinstance(edge, dict)]
    matched: list[dict[str, object]] = []
    for edge in role_edges:
        scope = str(edge.get("scope") or "")
        if scope == "not_present":
            continue
        projection = edge.get("domain_projection") if isinstance(edge.get("domain_projection"), dict) else {}
        domain_projection = str(projection.get(domain) or "")
        haystack = " ".join(
            str(edge.get(key) or "")
            for key in ("edge_key", "classical_name", "source_group", "target_group", "relation")
        )
        if aliases and not any(alias and alias in haystack for alias in aliases):
            continue
        matched.append(
            {
                "edge_key": str(edge.get("edge_key") or ""),
                "classical_name": str(edge.get("classical_name") or ""),
                "relation": str(edge.get("relation") or ""),
                "scope": scope,
                "source_presence_grade": str(edge.get("source_presence_grade") or ""),
                "target_presence_grade": str(edge.get("target_presence_grade") or ""),
                "source_force_index": edge.get("source_force_index"),
                "target_force_index": edge.get("target_force_index"),
                "force_balance": str(edge.get("force_balance") or ""),
                "force_effect": str(edge.get("force_effect") or ""),
                "force_balance_context": dict(edge.get("force_balance_context") or {})
                if isinstance(edge.get("force_balance_context"), dict)
                else {},
                "touches_month_command": bool(edge.get("touches_month_command")),
                "domain_projection": domain_projection,
                "basis_codes": [str(code) for code in list(edge.get("basis_codes") or [])[:8] if str(code)],
            }
        )
    matched.sort(
        key=lambda edge: (
            _principle_edge_scope_rank(str(edge.get("scope") or "")),
            1 if edge.get("touches_month_command") else 0,
            str(edge.get("edge_key") or ""),
        ),
        reverse=True,
    )
    return matched[:4]


def _domain_facet_cycle_sources(
    *,
    cycle_regulation_profile: dict[str, object] | None,
    domain: str,
    cycle_tags: list[str],
) -> list[dict[str, object]]:
    if not cycle_regulation_profile:
        return []

    def effective_score(signal: dict[str, object]) -> int:
        score = int(signal.get("score") or 0)
        fit = signal.get("month_cycle_fit_context")
        if not isinstance(fit, dict):
            return score
        latent_edges = int(fit.get("latent_edge_count") or 0)
        costly_edges = int(fit.get("costly_edge_count") or 0)
        burden_edges = int(fit.get("burden_edge_count") or 0)
        verdict = str(fit.get("verdict") or "")
        score -= latent_edges * 14
        score -= burden_edges * 10
        score -= max(0, costly_edges - latent_edges - burden_edges) * 5
        if verdict == "month_cycle_needed":
            score += 4
        elif verdict == "month_cycle_needed_with_cost":
            score -= 2
        elif verdict == "month_cycle_pressure_with_use":
            score -= 7
        elif verdict == "month_cycle_burdens_month":
            score -= 12
        return max(0, min(100, score))

    def effective_polarity(signal: dict[str, object]) -> str:
        raw = str(signal.get("polarity") or "mixed")
        fit = signal.get("month_cycle_fit_context")
        if not isinstance(fit, dict):
            return raw
        verdict = str(fit.get("verdict") or "")
        latent_edges = int(fit.get("latent_edge_count") or 0)
        costly_edges = int(fit.get("costly_edge_count") or 0)
        burden_edges = int(fit.get("burden_edge_count") or 0)
        if verdict == "month_cycle_burdens_month":
            return "pressure"
        if raw == "support" and (latent_edges or costly_edges or burden_edges or verdict == "month_cycle_needed_with_cost"):
            return "mixed"
        if raw == "mixed" and burden_edges:
            return "pressure"
        return raw

    signals = [signal for signal in list(cycle_regulation_profile.get("signals") or []) if isinstance(signal, dict)]
    matched: list[dict[str, object]] = []
    for signal in signals:
        domain_links = {str(item) for item in list(signal.get("domain_links") or []) if str(item)}
        haystack = " ".join(
            str(signal.get(key) or "")
            for key in (
                "signal_id",
                "relation",
                "status",
                "cycle_judgment",
                "classical_name",
                "source_group",
                "target_group",
                "bridge_group",
            )
        )
        if domain not in domain_links and not any(tag in haystack for tag in cycle_tags):
            continue
        if cycle_tags and not any(tag in haystack for tag in cycle_tags):
            continue
        matched.append(signal)
    matched.sort(
        key=lambda item: (
            effective_score(item) + int(item.get("reality_score") or 0),
            str(item.get("signal_id") or ""),
        ),
        reverse=True,
    )
    return [
        {
            "signal_id": str(signal.get("signal_id") or ""),
            "classical_name": str(signal.get("classical_name") or ""),
            "relation": str(signal.get("relation") or ""),
            "polarity": effective_polarity(signal),
            "raw_polarity": str(signal.get("polarity") or "mixed"),
            "score": int(signal.get("score") or 0),
            "effective_score": effective_score(signal),
            "reality_score": int(signal.get("reality_score") or 0),
            "cycle_judgment": str(signal.get("cycle_judgment") or ""),
            "force_balance": str((signal.get("force_balance_context") or {}).get("balance") or "")
            if isinstance(signal.get("force_balance_context"), dict)
            else "",
            "force_effect": str((signal.get("force_balance_context") or {}).get("effect") or "")
            if isinstance(signal.get("force_balance_context"), dict)
            else "",
            "source_force_index": (signal.get("force_balance_context") or {}).get("source_force_index")
            if isinstance(signal.get("force_balance_context"), dict)
            else None,
            "target_force_index": (signal.get("force_balance_context") or {}).get("target_force_index")
            if isinstance(signal.get("force_balance_context"), dict)
            else None,
            "force_balance_context": dict(signal.get("force_balance_context") or {})
            if isinstance(signal.get("force_balance_context"), dict)
            else {},
            "force_context": dict(signal.get("force_context") or {})
            if isinstance(signal.get("force_context"), dict)
            else {},
            "month_cycle_fit_verdict": str(
                (signal.get("month_cycle_fit_context") or {}).get("verdict")
                if isinstance(signal.get("month_cycle_fit_context"), dict)
                else ""
            ),
            "latent_edge_count": int(
                (signal.get("month_cycle_fit_context") or {}).get("latent_edge_count") or 0
                if isinstance(signal.get("month_cycle_fit_context"), dict)
                else 0
            ),
            "costly_edge_count": int(
                (signal.get("month_cycle_fit_context") or {}).get("costly_edge_count") or 0
                if isinstance(signal.get("month_cycle_fit_context"), dict)
                else 0
            ),
            "decision_reason": str(signal.get("decision_reason") or ""),
        }
        for signal in matched[:4]
    ]


def _domain_facet_cycle_delta(cycle_sources: list[dict[str, object]]) -> float:
    delta = 0.0
    for source in cycle_sources[:3]:
        polarity = str(source.get("polarity") or "mixed")
        score = int(source.get("effective_score") or source.get("score") or 0)
        weight = 2.0 + min(2.0, max(0, score - 55) / 18)
        if polarity == "support":
            delta += weight
        elif polarity == "pressure":
            delta -= weight + 0.8
        else:
            delta += 0.4
    return delta


def _domain_facet_principle_delta(principle_edges: list[dict[str, object]]) -> tuple[float, list[dict[str, object]]]:
    """Apply classical role-edge material without pretending every weak edge is decisive."""
    delta = 0.0
    contributions: list[dict[str, object]] = []
    scope_weights = {
        "active_support": 2.2,
        "active_mixed": 0.75,
        "active_pressure": -2.4,
        "reference": 0.65,
        "latent_reference": 0.45,
        "trace_reference": 0.25,
    }
    grade_weights = {
        "clear": 0.35,
        "strong": 0.28,
        "rooted": 0.24,
        "present": 0.18,
        "weak": -0.18,
        "trace": -0.28,
        "absent": -0.45,
    }
    for edge in principle_edges[:4]:
        scope = str(edge.get("scope") or "")
        value = scope_weights.get(scope, 0.0)
        if not value:
            continue
        source_grade = str(edge.get("source_presence_grade") or "")
        target_grade = str(edge.get("target_presence_grade") or "")
        grade_delta = grade_weights.get(source_grade, 0.0) + grade_weights.get(target_grade, 0.0)
        if value < 0:
            grade_delta = -abs(grade_delta) * 0.45
        else:
            grade_delta *= 0.45
        if edge.get("touches_month_command"):
            value += 0.35 if value >= 0 else -0.35
        basis_text = " ".join(str(code) for code in list(edge.get("basis_codes") or []))
        if "burdens_month" in basis_text or "pressure_with_use" in basis_text:
            value -= 0.45
        if "needed" in basis_text or "useful" in basis_text:
            value += 0.25
        contribution = round(value + grade_delta, 2)
        if scope in {"latent_reference", "trace_reference"}:
            contribution = max(min(contribution, 0.9), -0.45)
        delta += contribution
        contributions.append(
            {
                "edge_key": str(edge.get("edge_key") or ""),
                "classical_name": str(edge.get("classical_name") or ""),
                "scope": scope,
                "delta": contribution,
                "touches_month_command": bool(edge.get("touches_month_command")),
                "source_presence_grade": source_grade,
                "target_presence_grade": target_grade,
            }
        )
    return delta, contributions


def _domain_facet_layer_delta(
    *,
    required_layers: list[str],
    inferred_layers: list[str],
    counter_signals: list[str],
) -> float:
    if not required_layers:
        return 0.0
    required = list(dict.fromkeys(required_layers))
    inferred = set(inferred_layers)
    matched = [layer for layer in required if layer in inferred]
    missing = [layer for layer in required if layer not in inferred]
    delta = min(1.8, 0.35 * len(matched))
    for layer in missing:
        if layer == "월령·격국":
            delta -= 0.9
        elif layer in {"지지·지장간", "십신·생극"}:
            delta -= 0.65
        else:
            delta -= 0.35
    if "월령·격국" in inferred:
        delta += 0.35
    if "지지·지장간" in inferred:
        delta += 0.25
    if "합충형파해" in inferred and counter_signals:
        delta -= 0.25
    return max(-2.4, min(2.4, delta))


def _domain_facet_pressure_profile(
    *,
    score: int,
    counter_signals: list[str],
    cycle_sources: list[dict[str, object]],
    principle_edges: list[dict[str, object]],
    layer_delta: float,
) -> dict[str, object]:
    pressure_score = 0.0
    reasons: list[str] = []
    if score < 45:
        pressure_score += 3.0
        reasons.append("점수 약세")
    elif score < 55:
        pressure_score += 2.0
        reasons.append("보완 구간")
    elif score < 65:
        pressure_score += 0.9

    counter_count = len(counter_signals)
    if counter_count >= 6:
        pressure_score += 2.4
        reasons.append("반대 신호 다수")
    elif counter_count >= 3:
        pressure_score += 1.4
        reasons.append("반대 신호")
    elif counter_count:
        pressure_score += 0.6

    cycle_pressure_count = sum(
        1 for source in cycle_sources if str(source.get("polarity") or "") == "pressure"
    )
    if cycle_pressure_count >= 2:
        pressure_score += 2.2
        reasons.append("생극 부담")
    elif cycle_pressure_count == 1:
        pressure_score += 1.2
        reasons.append("생극 부담")

    active_pressure_edges = sum(
        1 for edge in principle_edges if str(edge.get("scope") or "") == "active_pressure"
    )
    latent_pressure_edges = sum(
        1
        for edge in principle_edges
        if str(edge.get("scope") or "") in {"latent_pressure", "trace_pressure"}
    )
    if active_pressure_edges:
        pressure_score += min(2.6, 1.4 * active_pressure_edges)
        reasons.append("작용 충돌")
    elif latent_pressure_edges:
        pressure_score += min(1.2, 0.45 * latent_pressure_edges)

    if layer_delta <= -1.2:
        pressure_score += 1.4
        reasons.append("판단층 결손")
    elif layer_delta < 0:
        pressure_score += 0.6

    if pressure_score >= 5.2:
        level = "severe"
    elif pressure_score >= 3.0:
        level = "clear"
    elif pressure_score >= 1.2:
        level = "light"
    else:
        level = "none"
    return {
        "pressure_score": round(pressure_score, 2),
        "pressure_level": level,
        "pressure_reasons": list(dict.fromkeys(reasons))[:4],
    }


def _domain_decision_facet_payload(
    profile: object,
    cycle_regulation_profile: dict[str, object] | None,
    gyeokguk_profile: object | None = None,
    chart_structure: object | None = None,
    expert_adjudication: object | None = None,
) -> dict[str, list[dict[str, object]]]:
    axes = getattr(profile, "axes", {})
    result: dict[str, list[dict[str, object]]] = {}
    prepared_gyeokguk_matches = _prepare_gyeokguk_action_matches(gyeokguk_profile)
    for domain, rules in DOMAIN_DECISION_FACET_RULES.items():
        domain_items: list[dict[str, object]] = []
        for rule in rules:
            axis_keys = [str(key) for key in list(rule.get("axis_keys") or [])]
            selected_axes = [axes[key] for key in axis_keys if key in axes]
            axis_weights_raw = rule.get("axis_weights") or {}
            axis_weights = axis_weights_raw if isinstance(axis_weights_raw, dict) else {}
            primary_axis_key = str(rule.get("primary_axis_key") or "")
            primary_axis = axes.get(primary_axis_key) if primary_axis_key else None
            corroboration_weights_raw = rule.get("corroboration_weights") or {}
            corroboration_weights = (
                corroboration_weights_raw
                if isinstance(corroboration_weights_raw, dict)
                else {}
            )
            weighted_axes: list[tuple[object, float]] = []
            corroboration_delta_decimal = Decimal("0")
            if primary_axis is not None:
                weighted_axes.append((primary_axis, 1.0))
                primary_axis_score_decimal = Decimal(str(getattr(primary_axis, "score", 50)))
                for axis_key, raw_weight in corroboration_weights.items():
                    axis = axes.get(str(axis_key))
                    if axis is None or str(axis_key) == primary_axis_key:
                        continue
                    try:
                        weight = float(raw_weight)
                    except (TypeError, ValueError):
                        continue
                    if weight <= 0:
                        continue
                    weighted_axes.append((axis, weight))
                    # A corroborating axis confirms or qualifies the primary
                    # capacity. It must not become an unconditional bonus from
                    # the neutral score, which allowed several good axes to
                    # push a bounded 0-100 capacity above 100. Measure each
                    # corroborator against the primary axis instead.
                    corroboration_delta_decimal += (
                        Decimal(str(getattr(axis, "score", 50))) - primary_axis_score_decimal
                    ) * Decimal(str(weight))
                base_score_decimal = primary_axis_score_decimal + corroboration_delta_decimal
                base_score = float(primary_axis_score_decimal)
                weight_total = sum((weight for _, weight in weighted_axes), 0.0)
                score_method = "primary_axis_with_corroboration"
            elif selected_axes:
                for axis in selected_axes:
                    try:
                        weight = float(axis_weights.get(getattr(axis, "key", ""), 1.0))
                    except (TypeError, ValueError):
                        weight = 1.0
                    weighted_axes.append((axis, max(0.1, weight)))
                decimal_weight_total = sum(
                    (Decimal(str(weight)) for _, weight in weighted_axes),
                    Decimal("0"),
                )
                weighted_score_total = sum(
                    (
                        Decimal(str(getattr(axis, "score", 50))) * Decimal(str(weight))
                        for axis, weight in weighted_axes
                    ),
                    Decimal("0"),
                )
                weight_total = float(decimal_weight_total)
                base_score_decimal = (
                    weighted_score_total / decimal_weight_total
                    if decimal_weight_total > 0
                    else Decimal("50")
                )
                base_score = float(base_score_decimal)
                score_method = "declared_weighted_engine_axes"
            else:
                weight_total = 0.0
                base_score = 50.0
                base_score_decimal = Decimal("50")
                score_method = "neutral_no_engine_axis"
            basis_codes = list(
                dict.fromkeys(
                    code
                    for axis in selected_axes
                    for code in list(axis.basis_codes)
                    if str(code)
                )
            )
            counter_signals = list(
                dict.fromkeys(
                    code
                    for axis in selected_axes
                    for code in list(axis.counter_signals)
                    if str(code)
                )
            )
            cycle_sources = _domain_facet_cycle_sources(
                cycle_regulation_profile=cycle_regulation_profile,
                domain=domain,
                cycle_tags=[str(tag) for tag in list(rule.get("cycle_tags") or [])],
            )
            principle_edges = _domain_facet_principle_edges(
                cycle_regulation_profile=cycle_regulation_profile,
                domain=domain,
                cycle_tags=[str(tag) for tag in list(rule.get("cycle_tags") or [])],
            )
            gyeokguk_action_sources = _domain_facet_gyeokguk_action_sources(
                gyeokguk_profile=gyeokguk_profile,
                domain=domain,
                rule=rule,
                basis_codes=basis_codes,
                counter_signals=counter_signals,
                prepared_matches=prepared_gyeokguk_matches,
            )
            inferred_layer_coverage = _domain_facet_layer_coverage(
                basis_codes=basis_codes,
                counter_signals=counter_signals,
                cycle_sources=cycle_sources,
                principle_edges=principle_edges,
            )
            rule_key = str(rule.get("key") or "")
            required_layers = list(DOMAIN_DECISION_FACET_LAYER_FOCUS.get(rule_key, inferred_layer_coverage))
            cycle_delta = _domain_facet_cycle_delta(cycle_sources)
            principle_delta, principle_delta_sources = _domain_facet_principle_delta(principle_edges)
            gyeokguk_delta = _domain_facet_gyeokguk_delta(gyeokguk_action_sources)
            layer_delta = _domain_facet_layer_delta(
                required_layers=required_layers,
                inferred_layers=inferred_layer_coverage,
                counter_signals=counter_signals,
            )
            # Public-facing facets may name one semantic primary axis and use
            # the remaining axes only as centered corroboration. This keeps
            # multiple structural signals without averaging distinct metrics
            # back toward the same middle score. Cycle, principle, gyeokguk,
            # and layer values remain diagnostic because they already
            # participate in the upstream axes and must not be counted twice.
            adjudication = adjudicate_natal_metric(
                metric_key=rule_key,
                base_score=float(base_score_decimal),
                structure=chart_structure,  # type: ignore[arg-type]
                cycle_delta=cycle_delta,
                principle_delta=principle_delta,
                gyeokguk_delta=gyeokguk_delta,
                layer_delta=layer_delta,
                expert_adjudication=expert_adjudication,  # type: ignore[arg-type]
            )
            score = max(0, min(100, int(adjudication["score"])))
            layer_coverage = list(
                dict.fromkeys(
                    required_layers
                )
            )
            pressure_profile = _domain_facet_pressure_profile(
                score=score,
                counter_signals=counter_signals,
                cycle_sources=cycle_sources,
                principle_edges=principle_edges,
                layer_delta=layer_delta,
            )
            pressure_level = str(pressure_profile.get("pressure_level") or "none")
            domain_items.append(
                {
                    "key": rule_key,
                    "label": str(rule.get("label") or ""),
                    "meaning": str(rule.get("meaning") or ""),
                    "score": score,
                    "value": _facet_strength_label(score),
                    "score_components": {
                        "axis_base": round(base_score, 2),
                        "score_method": score_method,
                        "primary_axis_key": (
                            primary_axis_key
                            if primary_axis is not None
                            else str(getattr(selected_axes[0], "key", "")) if selected_axes else ""
                        ),
                        "corroboration_delta": round(float(corroboration_delta_decimal), 2),
                        "composite_score_unrounded": round(float(base_score_decimal), 2),
                        "adjudicated_score": score,
                        "judgment_contract_grade": adjudication.get("contract_grade", "D"),
                        "judgment_contract_applied": bool(adjudication.get("contract_applied")),
                        "judgment_components": {
                            key: value
                            for key, value in adjudication.items()
                            if key not in {"score", "contract_grade", "contract_applied"}
                            and value is not None
                        },
                        "axis_weight_total": round(weight_total, 2),
                        "cycle_delta": round(cycle_delta, 2),
                        "principle_delta": round(principle_delta, 2),
                        "gyeokguk_delta": round(gyeokguk_delta, 2),
                        "layer_delta": round(layer_delta, 2),
                    },
                    "axis_sources": [
                        {
                            "key": axis.key,
                            "label": axis.label,
                            "score": axis.score,
                            "strength_label": axis.strength_label,
                            "weight": round(weight, 2),
                        }
                        for axis, weight in weighted_axes
                    ],
                    "cycle_sources": cycle_sources,
                    "principle_edges": principle_edges,
                    "principle_delta_sources": principle_delta_sources,
                    "gyeokguk_action_sources": gyeokguk_action_sources,
                    "layer_coverage": layer_coverage,
                    "raw_layer_coverage": inferred_layer_coverage,
                    "basis_codes": basis_codes[:24],
                    "counter_signals": counter_signals[:16],
                    "pressure_score": pressure_profile["pressure_score"],
                    "pressure_level": pressure_level,
                    "pressure_reasons": pressure_profile["pressure_reasons"],
                    "has_pressure": bool(score < 52 or pressure_level in {"clear", "severe"}),
                }
            )
        result[domain] = domain_items
    return result


OUTPUT_GOAL_DOMAIN_SOURCE_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "money": {
        "사업 확장력": ("사업 확장성",),
        "채권·미수금 회수력": ("채권 회수력", "미수금 회수력", "receivables_recovery"),
        "재물 강세 연도": ("재물 강세 연도", "money_peak"),
        "재물 주의 연도": ("계약 주의 연도", "contract_caution"),
    },
    "career": {
        "직업 분야": ("career_field_profile",),
        "전문 자산화": ("전문성 자산화",),
        "조직 적응력": ("조직 안착력",),
        "독립 가능성": ("독립 기반",),
        "업무 조건 감별력": ("부적합 업무 조건", "부적합 업무 감별력"),
        "직업 전환 연도": ("직업 전환 연도", "career_change"),
    },
    "love": {
        "애정 표현성": ("애정 표현력",),
        "오해 조정력": ("오해 발생점", "오해 관리력"),
        "갈등 관리력": ("갈등 원인",),
        "주변 개입 관리력": ("주변 변수 관리력", "외부 개입 관리력"),
        "재회 가능성": ("재회·정리 가능성",),
    },
    "marriage": {
        "혼인 성향": ("혼인 결정력",),
        "배우자상": ("배우자 적합도",),
        "결혼 적기": ("혼인 성사 연도", "marriage_decision"),
        "생활 안정": ("생활 안정성",),
        "부부 재정": ("부부 재정 안정성",),
        "부부 갈등 조정력": ("부부 갈등",),
        "가족 변수": ("가족 변수 대응력",),
        "배우자 가족 경계": ("배우자 가족 경계력",),
        "자녀·양육 책임": ("자녀 양육 책임", "양육 책임", "자녀운"),
        "결혼 지속력": ("유지와 위기",),
    },
}


OUTPUT_GOAL_TIMING_SOURCE_ALIASES: dict[str, tuple[str, ...]] = {
    "대운 구간별 중심 과제": ("decade_profile",),
    "상승 연도": ("good_years",),
    "수입 강세 연도": ("income_peak",),
    "재물 강세 연도": ("money_peak",),
    "자산화 연도": ("asset_year",),
    "채권·미수금 회수 연도": ("receivables_recovery_year", "contract_caution"),
    "공동자금 주의 연도": ("shared_money_caution",),
    "계약·명의 주의 연도": ("contract_caution", "caution_years"),
    "부채·보증 주의 연도": ("debt_guarantee_caution", "shared_money_caution", "contract_caution"),
    "가족재산 주의 연도": ("family_asset_caution", "shared_money_caution", "family_caution"),
    "재물 주의 연도": ("contract_caution",),
    "직업 상승 연도": ("career_rise",),
    "권한 상승 연도": ("authority_year",),
    "보상 상승 연도": ("compensation_rise", "career_rise", "authority_year"),
    "직업 분야 전환 연도": ("career_domain_shift", "career_change"),
    "직업 전환 연도": ("career_change",),
    "소속 변화 연도": ("career_change", "good_years"),
    "직업 부담 연도": ("career_burden",),
    "직업 독립 연도": ("career_independence_year", "career_change", "good_years"),
    "관계 진전 연도": ("relationship_progress_year",),
    "재회·정리 연도": ("relationship_recovery_year",),
    "연애 강세 연도": ("love_opening", "relationship_progress_year"),
    "새 인연 연도": ("love_opening", "relationship_progress_year", "good_years"),
    "이별·정리 연도": ("separation_closure_year", "relationship_recovery_year", "love_caution"),
    "관계 주의 연도": ("love_caution",),
    "주변 개입 주의 연도": ("external_interference_caution", "love_caution"),
    "혼인 결정 연도": ("marriage_decision",),
    "주거·생활 준비 연도": ("housing_preparation_year",),
    "부부 재정 연도": ("couple_finance_year", "housing_preparation_year", "marriage_decision"),
    "가족·주거 변동 연도": ("family_caution",),
    "자녀·양육 책임 연도": ("child_rearing_year", "family_caution"),
    "결혼 주의 연도": ("family_caution", "love_caution", "caution_years"),
    "인생 전환 연도": ("good_years", "caution_years"),
    "주의 연도": ("caution_years",),
    "회복 연도": ("good_years",),
    "말년 안정 연도": ("decade_profile",),
}


def _compact_output_goal_label(value: object) -> str:
    return re.sub(r"[\s·ㆍ\-\(\)\[\]\{\}:：,./]+", "", str(value or ""))


def _output_goal_source_aliases(domain: str, required: str) -> tuple[str, ...]:
    domain_aliases = OUTPUT_GOAL_DOMAIN_SOURCE_ALIASES.get(domain, {})
    return (required, *domain_aliases.get(required, ()))


def _goal_coverage_from_facet(
    *,
    required: str,
    domain: str,
    domain_facets: dict[str, list[dict[str, object]]],
) -> dict[str, object] | None:
    candidates = {
        _compact_output_goal_label(candidate)
        for candidate in _output_goal_source_aliases(domain, required)
        if candidate != "career_field_profile"
    }
    if not candidates:
        return None
    for item in list(domain_facets.get(domain, []) or []):
        label = str(item.get("label") or "")
        if _compact_output_goal_label(label) not in candidates:
            continue
        return {
            "required_conclusion": required,
            "status": "covered",
            "source_type": "domain_decision_facet",
            "source_key": item.get("key"),
            "source_label": label,
            "score": item.get("score"),
            "value": item.get("value"),
            "layer_coverage": list(item.get("layer_coverage") or []),
        }
    return None


def _goal_coverage_from_career_fields(
    *,
    required: str,
    domain: str,
    career_field_profile: object,
) -> dict[str, object] | None:
    if domain != "career" or required != "직업 분야":
        return None
    field_keys = list(getattr(career_field_profile, "primary_field_keys", []) or [])
    if not field_keys:
        field_keys = list(getattr(career_field_profile, "top_field_keys", []) or [])[:3]
    fields = getattr(career_field_profile, "fields", {}) or {}
    selected = [fields[key] for key in field_keys if key in fields]
    if not selected:
        return None
    top = selected[0]
    return {
        "required_conclusion": required,
        "status": "covered",
        "source_type": "career_field_profile",
        "source_key": getattr(top, "key", ""),
        "source_label": getattr(top, "label", ""),
        "score": getattr(top, "score", None),
        "value": getattr(top, "strength_label", ""),
        "candidate_count": len(selected),
        "candidate_labels": [str(getattr(field, "label", "")) for field in selected[:4]],
    }


def _goal_coverage_from_feature_axis(
    *,
    required: str,
    profile: object,
) -> dict[str, object] | None:
    axes = getattr(profile, "axes", {}) or {}
    required_key = _compact_output_goal_label(required)
    for axis in axes.values():
        label = str(getattr(axis, "label", "") or "")
        if _compact_output_goal_label(label) != required_key:
            continue
        return {
            "required_conclusion": required,
            "status": "covered",
            "source_type": "feature_axis",
            "source_key": getattr(axis, "key", ""),
            "source_label": label,
            "score": getattr(axis, "score", None),
            "value": getattr(axis, "strength_label", ""),
        }
    return None


def _timing_collection_payload(
    *,
    required: str,
    timing_decision: dict[str, object],
    collection_key: str,
) -> dict[str, object] | None:
    collection = timing_decision.get(collection_key)
    if isinstance(collection, list) and collection:
        first = collection[0]
        return {
            "required_conclusion": required,
            "status": "indirect",
            "source_type": "timing_year_list",
            "source_key": collection_key,
            "source_label": str(first.get("focus") or first.get("domain_label") or collection_key) if isinstance(first, dict) else collection_key,
            "count": len(collection),
        }
    if isinstance(collection, dict) and collection:
        return {
            "required_conclusion": required,
            "status": "indirect",
            "source_type": "timing_collection",
            "source_key": collection_key,
            "source_label": collection_key,
            "count": len(collection),
        }
    return None


def _goal_coverage_from_timing(
    *,
    required: str,
    domain: str | None,
    timing_decision: dict[str, object],
) -> dict[str, object] | None:
    aliases = list(OUTPUT_GOAL_TIMING_SOURCE_ALIASES.get(required, ()))
    if domain:
        aliases.extend(OUTPUT_GOAL_DOMAIN_SOURCE_ALIASES.get(domain, {}).get(required, ()))
    aliases.append(required)
    event_years = timing_decision.get("event_years")
    if not isinstance(event_years, dict):
        event_years = {}
    label_candidates = {_compact_output_goal_label(alias) for alias in aliases}
    for alias in aliases:
        if alias in {"good_years", "caution_years", "decade_profile", "domain_years"}:
            payload = _timing_collection_payload(
                required=required,
                timing_decision=timing_decision,
                collection_key=alias,
            )
            if payload:
                return payload
            continue
        if alias in event_years and isinstance(event_years[alias], dict):
            event = event_years[alias]
            return {
                "required_conclusion": required,
                "status": "covered",
                "source_type": "timing_event",
                "source_key": alias,
                "source_label": event.get("event_label"),
                "year": event.get("year"),
                "age": event.get("age"),
                "focus": event.get("focus"),
                "score": event.get("score"),
            }
    for key, event in event_years.items():
        if not isinstance(event, dict):
            continue
        label = str(event.get("event_label") or "")
        if _compact_output_goal_label(label) not in label_candidates:
            continue
        return {
            "required_conclusion": required,
            "status": "covered",
            "source_type": "timing_event",
            "source_key": key,
            "source_label": label,
            "year": event.get("year"),
            "age": event.get("age"),
            "focus": event.get("focus"),
            "score": event.get("score"),
        }
    return None


def _missing_output_goal_coverage(required: str) -> dict[str, object]:
    return {
        "required_conclusion": required,
        "status": "missing",
        "source_type": "",
        "source_key": "",
        "source_label": "",
    }


def _output_goal_coverage_payload(
    *,
    output_goal_contract: dict[str, object],
    domain_facets: dict[str, list[dict[str, object]]],
    timing_decision: dict[str, object],
    career_field_profile: object,
    profile: object,
) -> dict[str, object]:
    domains_payload: dict[str, list[dict[str, object]]] = {}
    for domain, goal_payload in dict(output_goal_contract.get("domains") or {}).items():
        required_items = list(dict(goal_payload).get("required_conclusions") or [])
        entries: list[dict[str, object]] = []
        for required_value in required_items:
            required = str(required_value)
            entry = (
                _goal_coverage_from_career_fields(
                    required=required,
                    domain=str(domain),
                    career_field_profile=career_field_profile,
                )
                or _goal_coverage_from_facet(
                    required=required,
                    domain=str(domain),
                    domain_facets=domain_facets,
                )
                or _goal_coverage_from_timing(
                    required=required,
                    domain=str(domain),
                    timing_decision=timing_decision,
                )
                or _goal_coverage_from_feature_axis(
                    required=required,
                    profile=profile,
                )
                or _missing_output_goal_coverage(required)
            )
            entries.append(entry)
        domains_payload[str(domain)] = entries

    timing_required = list(dict(output_goal_contract.get("timing") or {}).get("required_conclusions") or [])
    timing_payload = [
        _goal_coverage_from_timing(
            required=str(required),
            domain=None,
            timing_decision=timing_decision,
        )
        or _missing_output_goal_coverage(str(required))
        for required in timing_required
    ]
    all_entries = [item for entries in domains_payload.values() for item in entries] + timing_payload
    missing_count = sum(1 for item in all_entries if item.get("status") == "missing")
    covered_count = sum(1 for item in all_entries if item.get("status") in {"covered", "indirect"})
    return {
        "schema_version": "output_goal_coverage_v1",
        "status": "complete" if missing_count == 0 else "partial",
        "covered_count": covered_count,
        "missing_count": missing_count,
        "domains": domains_payload,
        "timing": timing_payload,
    }


TIMING_DECISION_DOMAIN_LABELS = {
    "money": "재물",
    "career": "직업",
    "love": "연애",
    "marriage": "결혼",
}


TIMING_DECISION_EVENT_RULES: tuple[dict[str, object], ...] = (
    {
        "key": "income_peak",
        "label": "수입 강세 연도",
        "domain": "money",
        "kind": "good",
        "focus": "수입 상승",
        "weights": {"opportunity": 0.5, "probability": 0.34, "change": 0.1, "risk": -0.16},
        "preferred_sub_events": ("income_growth", "managed_income_expansion"),
    },
    {
        "key": "money_peak",
        "label": "재물 강세 연도",
        "domain": "money",
        "kind": "good",
        "focus": "수입·자산 형성",
        "weights": {"opportunity": 0.46, "probability": 0.34, "change": 0.12, "risk": -0.18},
        "preferred_sub_events": ("income_growth", "managed_income_expansion", "income_structure_change"),
    },
    {
        "key": "asset_year",
        "label": "자산화 연도",
        "domain": "money",
        "kind": "good",
        "focus": "자산 확보",
        "weights": {"opportunity": 0.34, "probability": 0.42, "change": 0.08, "risk": -0.2},
        "preferred_sub_events": ("money_flow_adjustment", "managed_income_expansion"),
    },
    {
        "key": "receivables_recovery_year",
        "label": "채권·미수금 회수 연도",
        "domain": "money",
        "kind": "good",
        "focus": "미수금·성과 보상 회수",
        "weights": {"opportunity": 0.28, "probability": 0.34, "change": 0.22, "risk": -0.12},
        "preferred_sub_events": ("managed_income_expansion", "income_structure_change"),
    },
    {
        "key": "shared_money_caution",
        "label": "공동자금 주의 연도",
        "domain": "money",
        "kind": "caution",
        "focus": "공동자금·보증 주의",
        "weights": {"risk": 0.58, "change": 0.2, "opportunity": -0.08, "probability": -0.03},
        "preferred_sub_events": ("cashflow_defense", "money_flow_adjustment"),
    },
    {
        "key": "debt_guarantee_caution",
        "label": "부채·보증 주의 연도",
        "domain": "money",
        "kind": "caution",
        "focus": "대여·보증·채무 책임",
        "weights": {"risk": 0.64, "change": 0.18, "opportunity": -0.1, "probability": -0.04},
        "preferred_sub_events": ("cashflow_defense", "managed_income_expansion", "money_flow_adjustment"),
    },
    {
        "key": "family_asset_caution",
        "label": "가족재산 주의 연도",
        "domain": "money",
        "kind": "caution",
        "focus": "가족재산·원가족 지출",
        "weights": {"risk": 0.58, "change": 0.24, "opportunity": -0.08, "probability": -0.03},
        "preferred_sub_events": ("cashflow_defense", "money_flow_adjustment", "income_structure_change"),
    },
    {
        "key": "contract_caution",
        "label": "계약·명의 주의 연도",
        "domain": "money",
        "kind": "caution",
        "focus": "계약·명의 주의",
        "weights": {"risk": 0.62, "change": 0.18, "opportunity": -0.08, "probability": -0.04},
        "preferred_sub_events": ("income_structure_change", "cashflow_defense"),
    },
    {
        "key": "career_rise",
        "label": "직업 상승 연도",
        "domain": "career",
        "kind": "good",
        "focus": "평가·직책 상승",
        "weights": {"opportunity": 0.44, "probability": 0.3, "change": 0.18, "risk": -0.12},
        "preferred_sub_events": ("career_recognition", "role_expansion_or_transition"),
    },
    {
        "key": "authority_year",
        "label": "권한 상승 연도",
        "domain": "career",
        "kind": "good",
        "focus": "권한·직책 확보",
        "weights": {"opportunity": 0.36, "change": 0.3, "probability": 0.22, "risk": -0.1},
        "preferred_sub_events": ("role_expansion_or_transition", "career_recognition"),
    },
    {
        "key": "compensation_rise",
        "label": "보상 상승 연도",
        "domain": "career",
        "kind": "good",
        "focus": "연봉·성과급·지분 보상",
        "weights": {"opportunity": 0.34, "probability": 0.28, "change": 0.22, "risk": -0.1},
        "preferred_sub_events": ("career_recognition", "role_expansion_or_transition"),
    },
    {
        "key": "career_change",
        "label": "직업 전환 연도",
        "domain": "career",
        "kind": "good",
        "focus": "이직·역할 변화",
        "weights": {"change": 0.46, "opportunity": 0.32, "probability": 0.18, "risk": -0.06},
        "preferred_sub_events": ("work_environment_change", "career_pace_adjustment"),
    },
    {
        "key": "career_domain_shift",
        "label": "직업 분야 전환 연도",
        "domain": "career",
        "kind": "good",
        "focus": "직업 분야·역할 전환",
        "weights": {"change": 0.42, "opportunity": 0.26, "probability": 0.2, "risk": -0.08},
        "preferred_sub_events": ("work_environment_change", "role_expansion_or_transition", "career_pace_adjustment"),
    },
    {
        "key": "career_independence_year",
        "label": "직업 독립 연도",
        "domain": "career",
        "kind": "good",
        "focus": "독립·개인 기반",
        "weights": {"change": 0.38, "opportunity": 0.3, "probability": 0.2, "risk": -0.1},
        "age_window": (30, 58),
        "preferred_sub_events": ("role_expansion_or_transition", "work_environment_change", "career_recognition"),
    },
    {
        "key": "career_burden",
        "label": "직업 주의 연도",
        "domain": "career",
        "kind": "caution",
        "focus": "권한 불균형",
        "weights": {"risk": 0.58, "change": 0.22, "opportunity": -0.1, "probability": -0.04},
        "preferred_sub_events": ("responsibility_pressure", "work_environment_change", "career_pace_adjustment"),
    },
    {
        "key": "love_opening",
        "label": "인연 성립 연도",
        "domain": "love",
        "kind": "good",
        "focus": "인연 성립",
        "weights": {"opportunity": 0.42, "probability": 0.36, "change": 0.16, "risk": -0.1},
        "preferred_sub_events": ("relationship_opening", "relationship_contact_increase"),
    },
    {
        "key": "relationship_progress_year",
        "label": "관계 진전 연도",
        "domain": "love",
        "kind": "good",
        "focus": "관계 진전",
        "weights": {"opportunity": 0.34, "probability": 0.32, "change": 0.24, "risk": -0.08},
        "preferred_sub_events": ("relationship_expression_alignment", "relationship_contact_increase"),
    },
    {
        "key": "relationship_recovery_year",
        "label": "재회·정리 연도",
        "domain": "love",
        "kind": "good",
        "focus": "재회·관계 정리",
        "weights": {"change": 0.34, "probability": 0.3, "opportunity": 0.24, "risk": -0.06},
        "preferred_sub_events": ("relationship_recovery_check", "relationship_temperature_shift"),
    },
    {
        "key": "separation_closure_year",
        "label": "이별·정리 연도",
        "domain": "love",
        "kind": "caution",
        "focus": "관계 정리·이별 주의",
        "weights": {"risk": 0.5, "change": 0.34, "opportunity": -0.06, "probability": -0.02},
        "preferred_sub_events": ("relationship_temperature_shift", "relationship_friction", "relationship_boundary_check"),
    },
    {
        "key": "love_caution",
        "label": "관계 주의 연도",
        "domain": "love",
        "kind": "caution",
        "focus": "오해·단절 주의",
        "weights": {"risk": 0.6, "change": 0.18, "opportunity": -0.08, "probability": -0.04},
        "preferred_sub_events": ("relationship_friction", "relationship_boundary_check", "relationship_with_conditions"),
    },
    {
        "key": "external_interference_caution",
        "label": "주변 개입 주의 연도",
        "domain": "love",
        "kind": "caution",
        "focus": "주변 개입",
        "weights": {"risk": 0.54, "change": 0.24, "opportunity": -0.06, "probability": -0.03},
        "preferred_sub_events": ("relationship_boundary_check", "relationship_with_conditions", "relationship_friction"),
    },
    {
        "key": "marriage_decision",
        "label": "혼인 성사 연도",
        "domain": "marriage",
        "kind": "good",
        "focus": "혼인·주거 결정",
        "weights": {"change": 0.36, "opportunity": 0.34, "probability": 0.24, "risk": -0.1},
        "preferred_sub_events": ("marriage_commitment_readiness", "marriage_decision_alignment", "marriage_stability_opening"),
    },
    {
        "key": "housing_preparation_year",
        "label": "주거·생활 준비 연도",
        "domain": "marriage",
        "kind": "good",
        "focus": "주거·생활 준비",
        "weights": {"change": 0.32, "probability": 0.28, "opportunity": 0.26, "risk": -0.08},
        "preferred_sub_events": ("marriage_practical_planning", "marriage_stability_opening", "marriage_decision_alignment"),
    },
    {
        "key": "couple_finance_year",
        "label": "부부 재정 연도",
        "domain": "marriage",
        "kind": "good",
        "focus": "생활비·공동자산 기준",
        "weights": {"change": 0.3, "probability": 0.28, "opportunity": 0.24, "risk": -0.06},
        "preferred_sub_events": ("marriage_practical_planning", "marriage_asset_condition_check", "marriage_decision_alignment"),
    },
    {
        "key": "family_caution",
        "label": "가족 책임 연도",
        "domain": "marriage",
        "kind": "caution",
        "focus": "가족·주거 부담",
        "weights": {"risk": 0.56, "change": 0.22, "opportunity": -0.08, "probability": -0.04},
        "preferred_sub_events": ("marriage_pressure", "marriage_asset_condition_check", "marriage_condition_check"),
    },
    {
        "key": "child_rearing_year",
        "label": "자녀·양육 책임 연도",
        "domain": "marriage",
        "kind": "caution",
        "focus": "자녀·양육 책임",
        "weights": {"risk": 0.44, "change": 0.34, "probability": 0.08, "opportunity": -0.04},
        "age_window": (24, 55),
        "preferred_sub_events": ("marriage_pressure", "marriage_condition_check", "marriage_asset_condition_check"),
    },
)


TIMING_EVENT_SELECTION_ORDER: dict[str, int] = {
    "income_peak": 10,
    "money_peak": 20,
    "asset_year": 30,
    "receivables_recovery_year": 35,
    "contract_caution": 40,
    "debt_guarantee_caution": 45,
    "shared_money_caution": 50,
    "family_asset_caution": 55,
    "compensation_rise": 8,
    "career_rise": 10,
    "authority_year": 20,
    "career_change": 30,
    "career_domain_shift": 35,
    "career_independence_year": 38,
    "career_burden": 40,
    "love_opening": 10,
    "relationship_progress_year": 20,
    "relationship_recovery_year": 30,
    "separation_closure_year": 36,
    "external_interference_caution": 38,
    "love_caution": 40,
    "marriage_decision": 10,
    "housing_preparation_year": 20,
    "couple_finance_year": 24,
    "child_rearing_year": 28,
    "family_caution": 30,
}


TIMING_EVENT_SELECTION_FAMILIES: dict[str, str] = {
    "income_peak": "money_good",
    "money_peak": "money_good",
    "asset_year": "money_good",
    "receivables_recovery_year": "money_good",
    "shared_money_caution": "money_caution",
    "contract_caution": "money_caution",
    "debt_guarantee_caution": "money_caution",
    "family_asset_caution": "money_caution",
    "career_rise": "career_good",
    "authority_year": "career_good",
    "compensation_rise": "career_good",
    "career_change": "career_good",
    "career_domain_shift": "career_good",
    "career_independence_year": "career_good",
    "career_burden": "career_caution",
    "love_opening": "love_good",
    "relationship_progress_year": "love_good",
    "relationship_recovery_year": "love_good",
    "separation_closure_year": "love_caution",
    "external_interference_caution": "love_caution",
    "love_caution": "love_caution",
    "marriage_decision": "marriage_good",
    "housing_preparation_year": "marriage_good",
    "couple_finance_year": "marriage_good",
    "child_rearing_year": "marriage_caution",
    "family_caution": "marriage_caution",
}


TIMING_SUB_EVENT_TONES = {
    "income_growth": "favorable",
    "managed_income_expansion": "favorable",
    "cashflow_defense": "caution",
    "income_structure_change": "transition",
    "money_flow_adjustment": "adjustment",
    "role_expansion_or_transition": "favorable",
    "career_recognition": "favorable",
    "responsibility_pressure": "caution",
    "work_environment_change": "transition",
    "career_pace_adjustment": "adjustment",
    "relationship_opening": "favorable",
    "relationship_with_conditions": "caution",
    "relationship_friction": "caution",
    "relationship_boundary_check": "caution",
    "relationship_expression_alignment": "favorable",
    "relationship_recovery_check": "adjustment",
    "relationship_contact_increase": "favorable",
    "relationship_temperature_shift": "adjustment",
    "marriage_stability_opening": "favorable",
    "marriage_condition_check": "caution",
    "marriage_pressure": "caution",
    "marriage_commitment_readiness": "favorable",
    "marriage_practical_planning": "favorable",
    "marriage_asset_condition_check": "caution",
    "marriage_decision_alignment": "favorable",
    "marriage_timing_adjustment": "adjustment",
}


TIMING_SUB_EVENT_FOCUS = {
    "income_growth": {"good": "수입 상승", "caution": "보상 기준"},
    "managed_income_expansion": {"good": "수입 강세", "caution": "정산 손실"},
    "cashflow_defense": {"good": "자금 보존", "caution": "금전 손실"},
    "income_structure_change": {"good": "수입 구조 전환", "caution": "수입 구조 변화"},
    "money_flow_adjustment": {"good": "자산 재편", "caution": "재정 부담"},
    "role_expansion_or_transition": {"good": "직책 상승", "caution": "직무 변동"},
    "career_recognition": {"good": "평가 상승", "caution": "평판 관리"},
    "responsibility_pressure": {"good": "책임 확대", "caution": "책임 과중"},
    "work_environment_change": {"good": "직업 변동", "caution": "조직 변동"},
    "career_pace_adjustment": {"good": "업무 재정비", "caution": "업무 과중"},
    "relationship_opening": {"good": "인연 형성", "caution": "관계 속도"},
    "relationship_with_conditions": {"good": "관계 조건 확인", "caution": "기대 차이"},
    "relationship_friction": {"good": "관계 재정리", "caution": "관계 마찰"},
    "relationship_boundary_check": {"good": "관계 안정", "caution": "거리 충돌"},
    "relationship_expression_alignment": {"good": "호감 표현", "caution": "표현 차이"},
    "relationship_recovery_check": {"good": "재회 가능성", "caution": "반복 갈등"},
    "relationship_contact_increase": {"good": "만남 증가", "caution": "관계 부담"},
    "relationship_temperature_shift": {"good": "호감 변화", "caution": "관계 불안"},
    "marriage_stability_opening": {"good": "혼인 안정", "caution": "생활 기준"},
    "marriage_condition_check": {"good": "혼인 조건", "caution": "현실 조건"},
    "marriage_pressure": {"good": "결혼 결정 압박", "caution": "결혼 압박"},
    "marriage_commitment_readiness": {"good": "혼인 약속", "caution": "책임 확인"},
    "marriage_practical_planning": {"good": "주거 준비", "caution": "생활비 부담"},
    "marriage_asset_condition_check": {"good": "재정 합의", "caution": "재정 조건"},
    "marriage_decision_alignment": {"good": "혼인 결정", "caution": "결정 지연"},
    "marriage_timing_adjustment": {"good": "결혼 시기 조정", "caution": "시기 지연"},
}


def _timing_packet_year(packet: object) -> int:
    period_label = str(getattr(packet, "period_label", "") or "")
    try:
        return int(period_label)
    except ValueError:
        return 0


def _timing_packet_score(packet: object) -> float:
    return (
        float(getattr(packet, "event_probability_score", 0) or 0) * 0.42
        + float(getattr(packet, "opportunity_score", 0) or 0) * 0.28
        + float(getattr(packet, "change_score", 0) or 0) * 0.12
        - float(getattr(packet, "risk_score", 0) or 0) * 0.14
    )


def _timing_packet_index(event_packets: list[object] | None) -> dict[tuple[int, str], object]:
    index: dict[tuple[int, str], object] = {}
    for packet in list(event_packets or []):
        year = _timing_packet_year(packet)
        domain = str(getattr(packet, "domain", "") or "")
        if not year or not domain:
            continue
        key = (year, domain)
        current = index.get(key)
        if current is None or _timing_packet_score(packet) > _timing_packet_score(current):
            index[key] = packet
    return index


def _timing_packet_for_flow(
    packet_index: dict[tuple[int, str], object],
    flow: object,
    domain: str,
) -> object | None:
    year = int(getattr(flow, "year", 0) or 0)
    return packet_index.get((year, domain))


def _timing_packet_tone(event_packet: object | None) -> str:
    if event_packet is None:
        return ""
    sub_event_type = str(getattr(event_packet, "sub_event_type", "") or "")
    return TIMING_SUB_EVENT_TONES.get(sub_event_type, "")


def _timing_packet_kind_modifier(kind: str, event_packet: object | None) -> float:
    tone = _timing_packet_tone(event_packet)
    if not tone:
        return 0.0
    if kind == "good":
        return {
            "favorable": 4.5,
            "transition": 0.8,
            "adjustment": -5.5,
            "caution": -18.0,
        }.get(tone, 0.0)
    return {
        "favorable": -10.0,
        "transition": 2.0,
        "adjustment": 4.0,
        "caution": 7.5,
    }.get(tone, 0.0)


def _timing_tone_selection_penalty(kind: str, event_packet: object | None) -> float:
    tone = _timing_packet_tone(event_packet)
    if not tone:
        return 0.0
    if kind == "good" and tone == "caution":
        return -42.0
    if kind == "caution" and tone == "favorable":
        return -12.0
    return 0.0


def _timing_packet_focus(kind: str, event_packet: object | None) -> str:
    if event_packet is None:
        return ""
    sub_event_type = str(getattr(event_packet, "sub_event_type", "") or "")
    focus = TIMING_SUB_EVENT_FOCUS.get(sub_event_type)
    if not focus:
        return ""
    return str(focus.get(kind) or "")


def _timing_domain_numbers(flow: object, domain: str, event_packet: object | None = None) -> dict[str, float]:
    if event_packet is not None:
        return {
            "opportunity": float(getattr(event_packet, "opportunity_score", 0) or 0),
            "risk": float(getattr(event_packet, "risk_score", 0) or 0),
            "change": float(getattr(event_packet, "change_score", 0) or 0),
            "probability": float(getattr(event_packet, "event_probability_score", 0) or 0),
        }
    scores = getattr(flow, "domain_scores", {}) or {}
    data = scores.get(domain) or {}
    if not isinstance(data, dict):
        data = {}
    return {
        "opportunity": float(data.get("opportunity") or 0),
        "risk": float(data.get("risk") or 0),
        "change": float(data.get("change") or 0),
        "probability": float(data.get("probability") or 0),
    }


def _timing_candidate_score(flow: object, domain: str, kind: str, event_packet: object | None = None) -> float:
    parts = _timing_domain_numbers(flow, domain, event_packet)
    score = timing_base_score(parts, kind)
    return (
        score
        + _timing_packet_kind_modifier(kind, event_packet)
        + _timing_tone_selection_penalty(kind, event_packet)
        + _flow_activation_score_modifier(flow, kind)
    )


def _timing_candidate_focus(domain: str, kind: str, parts: dict[str, float]) -> str:
    opportunity = parts["opportunity"]
    risk = parts["risk"]
    change = parts["change"]
    probability = parts["probability"]
    if kind == "good":
        if domain == "money":
            if opportunity >= 84 and probability >= 76:
                return "자산 형성"
            if change >= 58:
                return "거래·확장 고점"
            return "수입 강세"
        if domain == "career":
            if change >= 58:
                return "이직·역할 전환"
            if opportunity >= 82:
                return "직책·권한 상승"
            return "평가 상승"
        if domain == "love":
            if change >= 50:
                return "관계 확정"
            if probability >= 74:
                return "강한 인연"
            return "인연 성립"
        if domain == "marriage":
            if change >= 50:
                return "혼인 성사"
            if opportunity >= 78:
                return "가정 기반 형성"
            return "생활 안정"
    else:
        if domain == "money":
            if risk >= 70 and change >= 52:
                return "계약 손실"
            if risk >= 66:
                return "보증·채무 손실"
            return "공동자금 손실"
        if domain == "career":
            if risk >= 72 and change >= 52:
                return "권한·책임 불균형"
            if risk >= 68:
                return "평판 손상"
            return "업무 과중"
        if domain == "love":
            if risk >= 66 and change >= 45:
                return "관계 단절 주의"
            if risk >= 60:
                return "오해·거리감"
            return "연락 약화"
        if domain == "marriage":
            if risk >= 68 and change >= 45:
                return "가정 비용 부담"
            if risk >= 62:
                return "가족 개입"
            return "혼인 지연"
    return "주요 사건"


TIMING_RELATION_LABELS = {
    "six_combine": "지지 합",
    "three_harmony": "삼합",
    "three_harmony_half": "반합",
    "three_meeting": "방합",
    "clash": "충",
    "punishment": "형",
    "self_punishment": "자형",
    "harm": "해",
    "break": "파",
}


def _flow_activation_keywords(flow: object, kind: str = "") -> list[str]:
    context = getattr(flow, "activation_context", {}) or {}
    context = context if isinstance(context, dict) else {}
    keywords: list[str] = []
    compound = context.get("compound_direction") if isinstance(context.get("compound_direction"), dict) else {}
    compound_grade = str((compound or {}).get("grade") or "")
    compound_labels = {
        "daeun_supports_annual_support": "대운·세운 동조",
        "daeun_supports_annual_burden": "장기 기반 양호·연도 주의",
        "daeun_burden_annual_support": "장기 부담·연도 기회",
        "daeun_burden_annual_burden": "대운·세운 동시 주의",
        "daeun_annual_mixed": "길흉 교차",
    }
    if compound_grade in compound_labels:
        keywords.append(compound_labels[compound_grade])
    elif getattr(flow, "daeun_pillar", None):
        keywords.append("대운 장기 과제")
    if int(context.get("useful_hit_count") or 0):
        keywords.append("필요 오행 강화")
    if int(context.get("caution_hit_count") or 0):
        keywords.append("부담 오행 강화")
    if int(context.get("phase_hit_count") or 0):
        keywords.append("월령 지장간 표출")
    relation_hits = context.get("relation_hits") if isinstance(context.get("relation_hits"), list) else []
    relation_labels = [
        TIMING_RELATION_LABELS.get(str(item.get("relation_type") or ""), "")
        for item in relation_hits
        if isinstance(item, dict)
    ]
    keywords.extend([label for label in relation_labels if label][:2])
    daeun_annual_hits = context.get("daeun_annual_relation_hits") if isinstance(context.get("daeun_annual_relation_hits"), list) else []
    daeun_annual_labels = [
        TIMING_RELATION_LABELS.get(str(item.get("relation_type") or ""), "")
        for item in daeun_annual_hits
        if isinstance(item, dict)
    ]
    keywords.extend([f"대운·세운 {label}" for label in daeun_annual_labels if label][:1])
    if kind == "good" and "필요 오행 강화" in keywords and "부담 오행 강화" in keywords:
        keywords.append("길흉 교차")
    return list(dict.fromkeys(keywords))[:5]


def _flow_activation_label(flow: object, kind: str = "") -> str:
    keywords = _flow_activation_keywords(flow, kind)
    if not keywords:
        return ""
    if "대운·세운 동조" in keywords:
        return "장기 과제와 해당 연도의 사건이 같은 방향으로 모이는 연도"
    if "대운·세운 동시 주의" in keywords and kind != "good":
        return "장기 부담과 해당 연도의 문제가 겹치는 연도"
    if "장기 기반 양호·연도 주의" in keywords and kind != "good":
        return "전체 기반은 유지되지만 해당 연도에 손실 관리가 필요한 연도"
    if "장기 부담·연도 기회" in keywords and kind == "good":
        return "어려운 장기 환경 속에서 기회가 잡히는 연도"
    if "길흉 교차" in keywords:
        return "좋은 재료와 부담 재료가 함께 드러나는 연도"
    if "부담 오행 강화" in keywords and kind != "good":
        return "부담 글자가 현실 문제로 드러나는 연도"
    if "필요 오행 강화" in keywords:
        return "원국에 필요한 글자가 힘을 얻는 연도"
    if "월령 지장간 표출" in keywords:
        return "월령의 숨은 글자가 밖으로 드러나는 연도"
    if any(keyword in keywords for keyword in ("충", "형", "해", "파", "자형")):
        return "지지의 충돌이 사건을 움직이는 연도"
    if getattr(flow, "daeun_pillar", None):
        return "대운의 장기 과제가 그해 사건으로 드러나는 연도"
    return ""


def _flow_activation_score_modifier(flow: object, kind: str = "") -> float:
    """Score how strongly a flow year is activated by month command and daeun-seun context."""
    context = getattr(flow, "activation_context", {}) or {}
    return timing_activation_modifier(context, kind)


def _timing_candidate_payload(
    flow: object,
    domain: str,
    kind: str,
    event_packet: object | None = None,
) -> dict[str, object]:
    birth_year = None
    year = int(getattr(flow, "year", 0) or 0)
    parts = _timing_domain_numbers(flow, domain, event_packet)
    score = round(_timing_candidate_score(flow, domain, kind, event_packet), 2)
    activation_modifier = _flow_activation_score_modifier(flow, kind)
    focus = _timing_packet_focus(kind, event_packet) or _timing_candidate_focus(domain, kind, parts)
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    event_keywords: list[str] = []
    if event_packet is not None:
        basis_codes = [str(code) for code in list(getattr(event_packet, "basis_codes", []) or []) if str(code)]
        counter_signals = [str(code) for code in list(getattr(event_packet, "counter_signals", []) or []) if str(code)]
        event_keywords = [str(item) for item in list(getattr(event_packet, "event_keywords", []) or []) if str(item)]
    else:
        data = (getattr(flow, "domain_scores", {}) or {}).get(domain) or {}
        if not isinstance(data, dict):
            data = {}
        basis_codes = [str(code) for code in list(data.get("basis_codes") or []) if str(code)]
        counter_signals = [str(code) for code in list(data.get("counter_signals") or []) if str(code)]
    payload: dict[str, object] = {
        "year": year,
        "domain": domain,
        "domain_label": TIMING_DECISION_DOMAIN_LABELS.get(domain, domain),
        "kind": kind,
        "focus": focus,
        "score": score,
        "score_parts": parts,
        "year_pillar": str(getattr(flow, "year_pillar", "") or ""),
        "daeun_pillar": str(getattr(flow, "daeun_pillar", "") or ""),
        "year_stem_ten_god": str(getattr(flow, "year_stem_ten_god", "") or ""),
        "year_branch_main_ten_god": str(getattr(flow, "year_branch_main_ten_god", "") or ""),
        "daeun_stem_ten_god": str(getattr(flow, "daeun_stem_ten_god", "") or ""),
        "daeun_branch_main_ten_god": str(getattr(flow, "daeun_branch_main_ten_god", "") or ""),
        "activated_elements": list(getattr(flow, "activated_elements", []) or []),
        "activation_context": dict(getattr(flow, "activation_context", {}) or {}),
        "activation_label": _flow_activation_label(flow, kind),
        "activation_score_modifier": activation_modifier,
        "structure_keywords": _flow_activation_keywords(flow, kind),
        "basis_codes": list(dict.fromkeys(basis_codes))[:16],
        "counter_signals": list(dict.fromkeys(counter_signals))[:12],
        "engine_score_source": "event_packet" if event_packet is not None else "flow_signal",
    }
    if event_packet is not None:
        sub_event_type = str(getattr(event_packet, "sub_event_type", "") or "")
        raw_event_tone = TIMING_SUB_EVENT_TONES.get(sub_event_type, "")
        effective_event_tone = raw_event_tone
        if kind == "caution" and raw_event_tone == "favorable":
            effective_event_tone = "caution"
        elif kind == "good" and raw_event_tone == "caution":
            effective_event_tone = "mixed"
        payload.update(
            {
                "event_packet_id": str(getattr(event_packet, "packet_id", "") or ""),
                "sub_event_type": sub_event_type,
                "event_tone": effective_event_tone,
                "raw_event_tone": raw_event_tone,
                "confidence": str(getattr(event_packet, "confidence", "") or ""),
                "timing_strength": str(getattr(event_packet, "timing_strength", "") or ""),
                "event_keywords": list(dict.fromkeys(event_keywords))[:8],
            }
        )
    return payload


def _timing_event_rule_score(
    flow: object,
    rule: dict[str, object],
    event_packet: object | None = None,
    selection_context: dict[str, set[object]] | None = None,
    birth_year: int | None = None,
) -> float:
    domain = str(rule.get("domain") or "")
    parts = _timing_domain_numbers(flow, domain, event_packet)
    weights = rule.get("weights") if isinstance(rule.get("weights"), dict) else {}
    score = 0.0
    for key, weight in dict(weights).items():
        score += parts.get(str(key), 0.0) * float(weight or 0)
    kind = str(rule.get("kind") or "good")
    score += _timing_packet_kind_modifier(kind, event_packet)
    score += _timing_tone_selection_penalty(kind, event_packet)
    score += _flow_activation_score_modifier(flow, kind) * 0.85
    preferred_sub_events = {
        str(value)
        for value in list(rule.get("preferred_sub_events") or [])
        if str(value)
    }
    if preferred_sub_events and event_packet is not None:
        sub_event_type = str(getattr(event_packet, "sub_event_type", "") or "")
        if sub_event_type in preferred_sub_events:
            score += 14.0
        elif _timing_packet_tone(event_packet):
            score -= 3.5
    if selection_context is not None:
        year = int(getattr(flow, "year", 0) or 0)
        packet_id = str(getattr(event_packet, "packet_id", "") or "") if event_packet is not None else ""
        sub_event_type = str(getattr(event_packet, "sub_event_type", "") or "") if event_packet is not None else ""
        if year and year in selection_context.get("years", set()):
            score -= 22.0
        if packet_id and packet_id in selection_context.get("packet_ids", set()):
            score -= 14.0
        if sub_event_type and sub_event_type in selection_context.get("sub_event_types", set()):
            score -= 6.0
    age_window = rule.get("age_window")
    if isinstance(age_window, (list, tuple)) and len(age_window) == 2:
        age = _timing_age(int(getattr(flow, "year", 0) or 0), birth_year)
        if age is not None:
            min_age = int(age_window[0] or 0)
            max_age = int(age_window[1] or 0)
            if min_age and max_age and age < min_age:
                score -= min(90.0, float(min_age - age) * 5.0)
            elif min_age and max_age and age > max_age:
                score -= min(90.0, float(age - max_age) * 5.0)
    return round(score, 2)


def _timing_event_rule_payload(
    flows: list[object],
    rule: dict[str, object],
    birth_year: int | None,
    packet_index: dict[tuple[int, str], object] | None = None,
    selection_context: dict[str, set[object]] | None = None,
) -> dict[str, object]:
    domain = str(rule.get("domain") or "")
    kind = str(rule.get("kind") or "good")
    packet_index = packet_index or {}
    scored: list[tuple[float, object, object | None]] = []
    for flow in flows:
        if not int(getattr(flow, "year", 0) or 0):
            continue
        event_packet = _timing_packet_for_flow(packet_index, flow, domain)
        scored.append(
            (
                _timing_event_rule_score(
                    flow,
                    rule,
                    event_packet,
                    selection_context=selection_context,
                    birth_year=birth_year,
                ),
                flow,
                event_packet,
            )
        )
    if not scored:
        return {}
    if kind == "good":
        clean_scored = [item for item in scored if _timing_packet_tone(item[2]) != "caution"]
        if not clean_scored:
            return {}
        scored = clean_scored
    elif kind == "caution":
        caution_scored = [item for item in scored if _timing_packet_tone(item[2]) != "favorable"]
        if caution_scored:
            scored = caution_scored
    score, flow, event_packet = max(scored, key=lambda item: (item[0], -int(getattr(item[1], "year", 0) or 0)))
    candidate = _with_timing_age(_timing_candidate_payload(flow, domain, kind, event_packet), birth_year)
    candidate["score"] = score
    candidate["event_key"] = str(rule.get("key") or "")
    candidate["event_label"] = str(rule.get("label") or "")
    candidate["focus"] = str(rule.get("focus") or candidate.get("focus") or "")
    candidate["preferred_sub_events"] = [
        str(value) for value in list(rule.get("preferred_sub_events") or []) if str(value)
    ]
    return candidate


def _timing_event_years(
    flows: list[object],
    birth_year: int | None,
    packet_index: dict[tuple[int, str], object] | None = None,
) -> dict[str, dict[str, object]]:
    events: dict[str, dict[str, object]] = {}
    family_contexts: dict[str, dict[str, set[object]]] = {}
    ordered_rules = sorted(
        TIMING_DECISION_EVENT_RULES,
        key=lambda item: TIMING_EVENT_SELECTION_ORDER.get(str(item.get("key") or ""), 100),
    )
    for rule in ordered_rules:
        key = str(rule.get("key") or "")
        if not key:
            continue
        family = TIMING_EVENT_SELECTION_FAMILIES.get(key, "")
        selection_context = family_contexts.get(family) if family else None
        payload = _timing_event_rule_payload(
            flows,
            rule,
            birth_year,
            packet_index,
            selection_context=selection_context,
        )
        if payload:
            events[key] = payload
            if family:
                context = family_contexts.setdefault(
                    family,
                    {"years": set(), "packet_ids": set(), "sub_event_types": set()},
                )
                year = int(payload.get("year") or 0)
                packet_id = str(payload.get("event_packet_id") or "")
                sub_event_type = str(payload.get("sub_event_type") or "")
                if year:
                    context["years"].add(year)
                if packet_id:
                    context["packet_ids"].add(packet_id)
                if sub_event_type:
                    context["sub_event_types"].add(sub_event_type)
    return events


def _timing_age(year: int, birth_year: int | None) -> int | None:
    if not year or not birth_year:
        return None
    return year - birth_year + 1


def _with_timing_age(candidate: dict[str, object], birth_year: int | None) -> dict[str, object]:
    year = int(candidate.get("year") or 0)
    age = _timing_age(year, birth_year)
    if age is not None:
        candidate = dict(candidate)
        candidate["age"] = age
        candidate["age_label"] = f"{age}세"
    return candidate


def _pick_timing_candidates(candidates: list[dict[str, object]], limit: int) -> list[dict[str, object]]:
    if candidates and str(candidates[0].get("kind") or "") == "good":
        clean_candidates = [
            candidate for candidate in candidates if str(candidate.get("event_tone") or "") != "caution"
        ]
        if len(clean_candidates) >= limit:
            candidates = clean_candidates
    elif candidates and str(candidates[0].get("kind") or "") == "caution":
        caution_candidates = [
            candidate for candidate in candidates if str(candidate.get("event_tone") or "") != "favorable"
        ]
        if len(caution_candidates) >= limit:
            candidates = caution_candidates
    selected: list[dict[str, object]] = []
    seen_domains: set[str] = set()
    seen_years: set[int] = set()
    for candidate in sorted(candidates, key=lambda item: (-float(item.get("score") or 0), int(item.get("year") or 0))):
        year = int(candidate.get("year") or 0)
        domain = str(candidate.get("domain") or "")
        if year in seen_years:
            continue
        if domain in seen_domains and len(seen_domains) < min(limit, len(TIMING_DECISION_DOMAIN_LABELS)):
            continue
        selected.append(candidate)
        seen_years.add(year)
        seen_domains.add(domain)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        seen_years = {int(item.get("year") or 0) for item in selected}
        for candidate in sorted(candidates, key=lambda item: (-float(item.get("score") or 0), int(item.get("year") or 0))):
            year = int(candidate.get("year") or 0)
            if year in seen_years:
                continue
            selected.append(candidate)
            seen_years.add(year)
            if len(selected) >= limit:
                break
    return sorted(selected, key=lambda item: int(item.get("year") or 0))


def _partition_timing_candidates_by_year(
    good_candidates: list[dict[str, object]],
    caution_candidates: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best_good_by_year: dict[int, float] = {}
    best_caution_by_year: dict[int, float] = {}
    for candidate in good_candidates:
        year = int(candidate.get("year") or 0)
        if year:
            best_good_by_year[year] = max(
                best_good_by_year.get(year, float("-inf")),
                float(candidate.get("score") or 0),
            )
    for candidate in caution_candidates:
        year = int(candidate.get("year") or 0)
        if year:
            best_caution_by_year[year] = max(
                best_caution_by_year.get(year, float("-inf")),
                float(candidate.get("score") or 0),
            )

    directions = {
        year: (
            "caution"
            if best_caution_by_year.get(year, float("-inf"))
            > best_good_by_year.get(year, float("-inf"))
            else "good"
        )
        for year in set(best_good_by_year) | set(best_caution_by_year)
    }
    directed_good = [
        candidate
        for candidate in good_candidates
        if directions.get(int(candidate.get("year") or 0)) == "good"
    ]
    directed_caution = [
        candidate
        for candidate in caution_candidates
        if directions.get(int(candidate.get("year") or 0)) == "caution"
    ]
    return directed_good or good_candidates, directed_caution or caution_candidates


def build_timing_decision_payload_from_flows(
    flows: list[object],
    *,
    birth_year: int | None = None,
    target_years: list[int] | None = None,
    event_packets: list[object] | None = None,
) -> dict[str, object]:
    target_years = [int(year) for year in list(target_years or []) if isinstance(year, int)]
    if not flows:
        return {
            "range": "",
            "target_years": target_years,
            "good_years": [],
            "caution_years": [],
            "domain_years": {},
            "event_years": {},
            "decade_profile": [],
        }

    packet_index = _timing_packet_index(event_packets)
    good_candidates: list[dict[str, object]] = []
    caution_candidates: list[dict[str, object]] = []
    for flow in flows:
        for domain in TIMING_DECISION_DOMAIN_LABELS:
            event_packet = _timing_packet_for_flow(packet_index, flow, domain)
            good_candidates.append(_with_timing_age(_timing_candidate_payload(flow, domain, "good", event_packet), birth_year))
            caution_candidates.append(_with_timing_age(_timing_candidate_payload(flow, domain, "caution", event_packet), birth_year))
    all_good_candidates = good_candidates
    all_caution_candidates = caution_candidates
    good_candidates, caution_candidates = _partition_timing_candidates_by_year(
        all_good_candidates,
        all_caution_candidates,
    )

    years = sorted({int(getattr(flow, "year", 0) or 0) for flow in flows if int(getattr(flow, "year", 0) or 0)})
    ages = [_timing_age(year, birth_year) for year in years]
    ages = [age for age in ages if age is not None]
    range_label = ""
    if ages:
        range_label = f"{min(ages)}세~{max(ages)}세"
    elif years:
        range_label = f"{years[0]}년~{years[-1]}년"

    domain_years: dict[str, dict[str, object]] = {}
    for domain in TIMING_DECISION_DOMAIN_LABELS:
        domain_good = [
            candidate for candidate in all_good_candidates if candidate.get("domain") == domain
        ]
        domain_caution = [
            candidate for candidate in all_caution_candidates if candidate.get("domain") == domain
        ]
        domain_years[domain] = {
            "good": max(domain_good, key=lambda item: float(item.get("score") or 0), default={}),
            "caution": max(domain_caution, key=lambda item: float(item.get("score") or 0), default={}),
        }

    decade_profile: list[dict[str, object]] = []
    if ages and birth_year:
        for start_age in range((min(ages) // 10) * 10, max(ages) + 1, 10):
            end_age = min(start_age + 9, max(ages))
            band_years = {
                birth_year + age - 1
                for age in range(max(start_age, min(ages)), end_age + 1)
            }
            band_good = [candidate for candidate in good_candidates if int(candidate.get("year") or 0) in band_years]
            band_caution = [candidate for candidate in caution_candidates if int(candidate.get("year") or 0) in band_years]
            if not band_good and not band_caution:
                continue
            decade_profile.append(
                {
                    "age_band": f"{max(start_age, min(ages))}세~{end_age}세",
                    "good": max(band_good, key=lambda item: float(item.get("score") or 0), default={}),
                    "caution": max(band_caution, key=lambda item: float(item.get("score") or 0), default={}),
                }
            )

    return {
        "range": range_label,
        "target_years": years,
        "good_years": _pick_timing_candidates(good_candidates, 5),
        "caution_years": _pick_timing_candidates(caution_candidates, 5),
        "domain_years": domain_years,
        "event_years": _timing_event_years(flows, birth_year, packet_index),
        "decade_profile": decade_profile,
    }


def _timing_decision_payload(analysis: AnalysisResult) -> dict[str, object]:
    birth_year_value = analysis.trace.get("birth_year")
    birth_year = birth_year_value if isinstance(birth_year_value, int) else None
    target_years = [int(year) for year in list(analysis.trace.get("target_years", []) or []) if isinstance(year, int)]
    return build_timing_decision_payload_from_flows(
        list(getattr(analysis, "flow_signals", []) or []),
        birth_year=birth_year,
        target_years=target_years,
        event_packets=list(getattr(analysis, "event_packets", []) or []),
    )


def _life_feature_summary(analysis: AnalysisResult) -> dict[str, object]:
    profile = analysis.chart_structure.life_feature_profile
    combination_profile = analysis.chart_structure.combination_profile
    element_combination_profile = analysis.chart_structure.element_combination_profile
    directional_interaction_profile = analysis.chart_structure.directional_interaction_profile
    ten_god_interaction_profile = analysis.chart_structure.ten_god_interaction_profile
    stem_reception_profile = analysis.chart_structure.stem_reception_profile
    integrated_saju_profile = analysis.chart_structure.integrated_saju_profile
    career_field_profile = analysis.chart_structure.career_field_profile
    month_governance_profile = analysis.chart_structure.month_governance_profile
    source_personality_profile = analysis.chart_structure.source_personality_profile
    source_reading_profile = analysis.chart_structure.source_reading_profile
    cycle_regulation_profile = analysis.chart_structure.cycle_regulation_profile
    gyeokguk_profile = analysis.chart_structure.gyeokguk_profile
    gyeokguk_contextual_profile = analysis.chart_structure.gyeokguk_contextual_profile
    branch_keyword_profiles = branch_relation_keyword_profiles(
        analysis.chart_structure.branch_interactions,
        limit=10,
    )
    auxiliary_profile = analysis.chart_structure.auxiliary_profile
    requested_target_years = {
        int(year)
        for year in list(analysis.trace.get("target_years") or [])
        if isinstance(year, int)
    }
    annual_product_years = {CURRENT_FORTUNE_YEAR, CURRENT_FORTUNE_YEAR + 1}
    target_years = sorted(
        annual_product_years
        | {year for year in requested_target_years if year in annual_product_years}
    )
    annual_shinsal_signal_items = build_annual_shinsal_signals(
        analysis.chart_structure,
        target_years,
    )
    gyeokguk_contextual_payload = (
        dict(gyeokguk_contextual_profile)
        if isinstance(gyeokguk_contextual_profile, dict)
        else {}
    )
    shinsal_keyword_profile_items = annotate_shinsal_structure_alignment(
        shinsal_keyword_profiles(
            [
                *auxiliary_profile.twelve_shinsal_signals,
                *auxiliary_profile.misc_shinsal_signals,
                *annual_shinsal_signal_items,
            ],
            limit=24,
            product_only=True,
        ),
        gyeokguk_contextual_payload,
    )
    if branch_keyword_profiles:
        gyeokguk_contextual_payload["branch_relation_keyword_profiles"] = branch_keyword_profiles
    if shinsal_keyword_profile_items:
        gyeokguk_contextual_payload["shinsal_keyword_profiles"] = shinsal_keyword_profile_items

    def season_context_payload() -> dict[str, object]:
        element_profile = analysis.chart_structure.element_profile
        month_signal = analysis.chart_structure.position_signals.get("month")
        ranked_scores = sorted(
            element_profile.scores.values(),
            key=lambda score: score.ratio,
            reverse=True,
        )
        return {
            "month_branch": element_profile.month_branch,
            "month_branch_label": BRANCH_LABELS.get(element_profile.month_branch, element_profile.month_branch),
            "month_element": month_signal.branch_element if month_signal else "",
            "month_element_label": ELEMENT_LABELS.get(month_signal.branch_element, month_signal.branch_element) if month_signal else "",
            "season": element_profile.season_label,
            "season_label": SEASON_LABELS.get(element_profile.season_label, element_profile.season_label),
            "day_master_strength": element_profile.day_master_strength,
            "temperature_balance": element_profile.temperature_balance,
            "moisture_balance": element_profile.moisture_balance,
            "useful_elements": list(element_profile.useful_elements),
            "useful_element_labels": [ELEMENT_LABELS.get(element, element) for element in element_profile.useful_elements],
            "caution_elements": list(element_profile.caution_elements),
            "caution_element_labels": [ELEMENT_LABELS.get(element, element) for element in element_profile.caution_elements],
            "climate_needs": list(element_profile.climate_needs),
            "climate_need_labels": [ELEMENT_LABELS.get(element, element) for element in element_profile.climate_needs],
            "dominant_elements": [
                {
                    "element": score.element,
                    "label": ELEMENT_LABELS.get(score.element, score.element),
                    "ratio": score.ratio,
                    "state": score.state,
                    "visible_count": score.visible_count,
                    "root_count": score.root_count,
                }
                for score in ranked_scores[:3]
            ],
            "hidden_heavy_elements": [
                {
                    "element": score.element,
                    "label": ELEMENT_LABELS.get(score.element, score.element),
                    "ratio": score.ratio,
                    "state": score.state,
                    "root_count": score.root_count,
                }
                for score in ranked_scores
                if score.visible_count == 0 and score.root_count > 0
            ],
        }

    def month_governance_payload() -> dict[str, object]:
        support_fits = sorted(
            month_governance_profile.element_fits.values(),
            key=lambda item: (item.support_score - item.pressure_score, item.reality_score),
            reverse=True,
        )
        pressure_fits = sorted(
            month_governance_profile.element_fits.values(),
            key=lambda item: (item.pressure_score - item.support_score, item.reality_score),
            reverse=True,
        )
        month_hidden_phase = month_governance_profile.month_hidden_phase
        month_hidden_phase_payload = None
        if month_hidden_phase is not None:
            month_hidden_phase_payload = {
                "rule_version": month_hidden_phase.rule_version,
                "day_index_from_boundary": month_hidden_phase.day_index_from_boundary,
                "active_phase": month_hidden_phase.active_phase,
                "active_stem": month_hidden_phase.active_stem,
                "active_element": month_hidden_phase.active_element,
                "active_ten_god": month_hidden_phase.active_ten_god,
                "active_ten_god_group": month_hidden_phase.active_ten_god_group,
                "entries": [
                    {
                        "phase": entry.phase,
                        "stem": entry.stem,
                        "element": entry.element,
                        "ten_god": entry.ten_god,
                        "ten_god_group": entry.ten_god_group,
                        "days": entry.days,
                        "start_day": entry.start_day,
                        "end_day": entry.end_day,
                        "active": entry.active,
                        "repeated_stem": entry.repeated_stem,
                    }
                    for entry in month_hidden_phase.entries
                ],
                "basis_codes": list(month_hidden_phase.basis_codes),
            }
        return {
            "rule_version": month_governance_profile.rule_version,
            "month_branch": month_governance_profile.month_branch,
            "month_branch_label": BRANCH_LABELS.get(month_governance_profile.month_branch, month_governance_profile.month_branch),
            "month_element": month_governance_profile.month_element,
            "month_element_label": ELEMENT_LABELS.get(month_governance_profile.month_element, month_governance_profile.month_element),
            "month_command_ten_god": month_governance_profile.month_command_ten_god,
            "month_command_label": TEN_GOD_LABELS.get(month_governance_profile.month_command_ten_god, month_governance_profile.month_command_ten_god),
            "month_command_group": month_governance_profile.month_command_group,
            "regular_pattern": month_governance_profile.regular_pattern,
            "useful_elements": list(month_governance_profile.useful_elements),
            "caution_elements": list(month_governance_profile.caution_elements),
            "support_fits": [
                {
                    "element": fit.element,
                    "label": ELEMENT_LABELS.get(fit.element, fit.element),
                    "status": fit.status,
                    "support_score": fit.support_score,
                    "pressure_score": fit.pressure_score,
                    "reality_score": fit.reality_score,
                    "month_authority": fit.month_authority,
                }
                for fit in support_fits[:3]
            ],
            "pressure_fits": [
                {
                    "element": fit.element,
                    "label": ELEMENT_LABELS.get(fit.element, fit.element),
                    "status": fit.status,
                    "support_score": fit.support_score,
                    "pressure_score": fit.pressure_score,
                    "reality_score": fit.reality_score,
                    "month_authority": fit.month_authority,
                }
                for fit in pressure_fits[:3]
            ],
            "hidden_command_stems": list(month_governance_profile.command_hidden_stems),
            "month_hidden_phase": month_hidden_phase_payload,
            "decision_notes": list(month_governance_profile.decision_notes),
        }

    def branch_reality_payload() -> dict[str, object]:
        position_signals = []
        for position in ("month", "day", "hour", "year"):
            signal = analysis.chart_structure.position_signals.get(position)
            if signal is None:
                continue
            position_signals.append(
                {
                    "position": position,
                    "position_label": POSITION_LABELS.get(position, position),
                    "branch": signal.branch_key,
                    "branch_label": BRANCH_LABELS.get(signal.branch_key, signal.branch_key),
                    "branch_element": signal.branch_element,
                    "branch_element_label": ELEMENT_LABELS.get(signal.branch_element, signal.branch_element),
                    "branch_main_ten_god": signal.branch_main_ten_god,
                    "hidden_ten_gods": list(signal.hidden_ten_gods),
                    "protruded_hidden_stems": list(signal.protruded_hidden_stems),
                    "domains": list(signal.domains),
                    "supports_day_master": signal.supports_day_master,
                    "controls_day_master": signal.controls_day_master,
                    "age_scope": signal.age_scope,
                    "life_stage": signal.life_stage,
                    "primary_context": signal.primary_context,
                    "stem_visibility_weight": signal.stem_visibility_weight,
                    "branch_reality_weight": signal.branch_reality_weight,
                    "hidden_reality_weight": signal.hidden_reality_weight,
                    "position_basis_codes": list(signal.position_basis_codes),
                }
            )
        interactions = []
        for interaction in analysis.chart_structure.branch_interactions:
            interactions.append(
                {
                    "relation_type": interaction.relation_type,
                    "relation_label": BRANCH_RELATION_LABELS.get(interaction.relation_type, interaction.relation_type),
                    "branches": list(interaction.branches),
                    "branch_labels": [BRANCH_LABELS.get(branch, branch) for branch in interaction.branches],
                    "positions": list(interaction.positions),
                    "position_labels": [POSITION_LABELS.get(position, position) for position in interaction.positions],
                    "effect_element": interaction.effect_element,
                    "effect_element_label": ELEMENT_LABELS.get(interaction.effect_element, interaction.effect_element)
                    if interaction.effect_element
                    else "",
                    "intensity": interaction.intensity,
                    "domain_links": list(interaction.domain_links),
                    "basis_code": interaction.basis_code,
                }
            )
        pair_combinations = []
        for pair in analysis.chart_structure.branch_pair_combinations:
            pair_combinations.append(
                {
                    "pair_id": pair.pair_id,
                    "branches": list(pair.branches),
                    "branch_labels": [BRANCH_LABELS.get(branch, branch) for branch in pair.branches],
                    "positions": list(pair.positions),
                    "position_labels": [POSITION_LABELS.get(position, position) for position in pair.positions],
                    "elements": list(pair.elements),
                    "element_labels": [ELEMENT_LABELS.get(element, element) for element in pair.elements],
                    "element_relation": pair.element_relation,
                    "relation_label": pair.relation_label,
                    "source_element": pair.source_element,
                    "source_element_label": ELEMENT_LABELS.get(pair.source_element, pair.source_element),
                    "target_element": pair.target_element,
                    "target_element_label": ELEMENT_LABELS.get(pair.target_element, pair.target_element),
                    "formal_relation_types": list(pair.formal_relation_types),
                    "formal_relation_labels": [
                        BRANCH_RELATION_LABELS.get(relation, relation)
                        for relation in pair.formal_relation_types
                    ],
                    "intensity": pair.intensity,
                    "domain_links": list(pair.domain_links),
                    "basis_codes": list(pair.basis_codes),
                    "trait_keywords": list(pair.trait_keywords),
                    "interpretation": pair.interpretation,
                }
            )
        return {
            "position_signals": position_signals,
            "interactions": interactions,
            "pair_combinations": pair_combinations,
        }

    def cycle_regulation_payload() -> dict[str, object]:
        profile_payload = dict(cycle_regulation_profile or {})
        raw_signals = [signal for signal in profile_payload.get("signals") or [] if isinstance(signal, dict)]
        top_ids = [str(signal_id) for signal_id in profile_payload.get("top_signal_ids") or [] if signal_id]
        needed_ids = set(top_ids)
        domain_summary = profile_payload.get("domain_summary")
        if isinstance(domain_summary, dict):
            for summary in domain_summary.values():
                if not isinstance(summary, dict):
                    continue
                needed_ids.update(str(signal_id) for signal_id in summary.get("top_signal_ids") or [] if signal_id)
                needed_ids.update(str(signal_id) for signal_id in summary.get("support_signal_ids") or [] if signal_id)
                needed_ids.update(str(signal_id) for signal_id in summary.get("caution_signal_ids") or [] if signal_id)
        if needed_ids:
            signals = [
                signal
                for signal in raw_signals
                if str(signal.get("signal_id") or "") in needed_ids
            ]
        else:
            signals = sorted(raw_signals, key=lambda item: int(item.get("score") or 0), reverse=True)[:12]
        return {
            "version": profile_payload.get("version", ""),
            "top_signal_ids": top_ids,
            "domain_summary": domain_summary if isinstance(domain_summary, dict) else {},
            "personality_summary": profile_payload.get("personality_summary")
            if isinstance(profile_payload.get("personality_summary"), dict)
            else {},
            "principle_coverage": profile_payload.get("principle_coverage")
            if isinstance(profile_payload.get("principle_coverage"), dict)
            else {},
            "signals": signals,
        }

    def auxiliary_context_payload() -> dict[str, object]:
        auxiliary = analysis.chart_structure.auxiliary_profile

        def sal_payload(sal_by_position: dict[str, list[str]]) -> dict[str, list[dict[str, str]]]:
            return {
                position: [
                    {
                        "key": sal,
                        "label": TWELVE_SINSAL_LABELS.get(sal, sal),
                        "meaning": TWELVE_SINSAL_MEANINGS.get(sal, ""),
                    }
                    for sal in values
                ]
                for position, values in sal_by_position.items()
            }

        def signal_payload(signals) -> list[dict[str, object]]:
            return [
                {
                    "key": signal.key,
                    "label": signal.label,
                    "grade": signal.grade,
                    "lineage": signal.lineage,
                    "formula_name": signal.formula_name,
                    "positions": list(signal.positions),
                    "pillar_labels": list(signal.pillar_labels),
                    "domains": list(signal.domains),
                    "intensity": signal.intensity,
                    "allowed_use": signal.allowed_use,
                    "meaning": signal.meaning,
                    "caution": signal.caution,
                    "basis_codes": list(signal.basis_codes),
                }
                for signal in signals
            ]

        return {
            "twelve_growth_by_position": dict(auxiliary.twelve_growth_by_position),
            "day_branch_group": auxiliary.day_branch_group,
            "year_branch_group": auxiliary.year_branch_group,
            "day_basis_sal_by_position": sal_payload(auxiliary.day_sal_by_position or auxiliary.sal_by_position),
            "year_basis_sal_by_position": sal_payload(auxiliary.year_sal_by_position),
            "twelve_shinsal_signals": signal_payload(auxiliary.twelve_shinsal_signals),
            "misc_shinsal_signals": signal_payload(auxiliary.misc_shinsal_signals),
            "annual_shinsal_signals": signal_payload(annual_shinsal_signal_items),
        }

    def pattern_context_payload() -> dict[str, object]:
        pattern_profile = analysis.chart_structure.pattern_profile

        def candidate_payload(candidate) -> dict[str, object]:
            return {
                "name": candidate.name,
                "role": candidate.role,
                "score": candidate.score,
                "confidence": candidate.confidence,
                "basis_codes": list(candidate.basis_codes),
            }

        def element_candidate_payload(candidate) -> dict[str, object]:
            return {
                "element": candidate.element,
                "element_label": ELEMENT_LABELS.get(candidate.element, candidate.element),
                "role": candidate.role,
                "score": candidate.score,
                "confidence": candidate.confidence,
                "basis_codes": list(candidate.basis_codes),
            }

        return {
            "primary_pattern": pattern_profile.primary_pattern,
            "pattern_confidence": pattern_profile.pattern_confidence,
            "regular_pattern": pattern_profile.regular_pattern,
            "pattern_family": pattern_profile.pattern_family,
            "month_command_ten_god": pattern_profile.month_command_ten_god,
            "month_command_ten_god_label": TEN_GOD_LABELS.get(
                pattern_profile.month_command_ten_god,
                pattern_profile.month_command_ten_god,
            ),
            "candidates": [candidate_payload(candidate) for candidate in pattern_profile.candidates[:4]],
            "useful_elements": [
                element_candidate_payload(candidate)
                for candidate in pattern_profile.useful_element_candidates[:4]
            ],
            "caution_elements": [
                element_candidate_payload(candidate)
                for candidate in pattern_profile.caution_element_candidates[:4]
            ],
            "decision_notes": list(pattern_profile.decision_notes),
            "special_pattern_flags": list(pattern_profile.special_pattern_flags),
        }

    def gyeokguk_context_payload() -> dict[str, object]:
        profile = analysis.chart_structure.gyeokguk_profile

        flow_source_labels = {
            "annual_stem": "세운 천간",
            "annual_branch_main": "세운 지지 본기",
            "daeun_stem": "대운 천간",
            "daeun_branch_main": "대운 지지 본기",
        }

        def flow_ten_god_sources(flow, ten_god: str) -> list[str]:
            sources: list[str] = []
            if getattr(flow, "year_stem_ten_god", None) == ten_god:
                sources.append("annual_stem")
            if getattr(flow, "year_branch_main_ten_god", None) == ten_god:
                sources.append("annual_branch_main")
            if getattr(flow, "daeun_stem_ten_god", None) == ten_god:
                sources.append("daeun_stem")
            if getattr(flow, "daeun_branch_main_ten_god", None) == ten_god:
                sources.append("daeun_branch_main")
            return sources

        def flow_domain_activation_score(flow, domains: list[str]) -> tuple[float, str, str]:
            best_score = 0.0
            best_domain = ""
            best_polarity = "mixed"
            scores = getattr(flow, "domain_scores", {}) or {}
            for domain in domains or list(DOMAIN_ORDER):
                data = scores.get(domain) if isinstance(scores, dict) else {}
                if not isinstance(data, dict):
                    data = {}
                opportunity = float(data.get("opportunity") or 0)
                risk = float(data.get("risk") or 0)
                change = float(data.get("change") or 0)
                probability = float(data.get("probability") or 0)
                score = max(opportunity, risk) * 0.56 + change * 0.22 + probability * 0.22
                if score > best_score:
                    best_score = score
                    best_domain = str(domain)
                    if opportunity >= risk + 8:
                        best_polarity = "supportive"
                    elif risk >= opportunity + 8:
                        best_polarity = "burdensome"
                    else:
                        best_polarity = "mixed"
            return best_score, best_domain, best_polarity

        def compound_flow_grade(flow) -> str:
            context = getattr(flow, "activation_context", {}) or {}
            if not isinstance(context, dict):
                return ""
            compound = context.get("compound_direction") if isinstance(context.get("compound_direction"), dict) else {}
            return str((compound or {}).get("grade") or "")

        def single_action_timing_hits(match, limit: int = 5) -> list[dict[str, object]]:
            hits: list[dict[str, object]] = []
            for flow in analysis.flow_signals:
                sources = flow_ten_god_sources(flow, match.acting_ten_god)
                if not sources:
                    continue
                domain_score, domain, polarity = flow_domain_activation_score(flow, list(match.domain_priority))
                source_bonus = sum(
                    {
                        "annual_stem": 8,
                        "annual_branch_main": 10,
                        "daeun_stem": 6,
                        "daeun_branch_main": 8,
                    }.get(source, 0)
                    for source in sources
                )
                hit_score = int(
                    round(
                        min(
                            100,
                            match.presence_score * 0.42 + domain_score * 0.46 + source_bonus,
                        )
                    )
                )
                hits.append(
                    {
                        "year": int(getattr(flow, "year", 0) or 0),
                        "period_label": str(getattr(flow, "period_label", "") or ""),
                        "ten_god": match.acting_ten_god,
                        "ten_god_label": TEN_GOD_LABELS.get(match.acting_ten_god, match.acting_ten_god),
                        "sources": sources,
                        "source_labels": [flow_source_labels.get(source, source) for source in sources],
                        "domain": domain,
                        "domain_label": DOMAIN_LABELS.get(domain, domain),
                        "polarity": polarity,
                        "compound_grade": compound_flow_grade(flow),
                        "activation_score": hit_score,
                    }
                )
            return sorted(hits, key=lambda item: (-int(item["activation_score"]), int(item["year"])))[:limit]

        def dual_action_timing_hits(match, limit: int = 5) -> list[dict[str, object]]:
            hits: list[dict[str, object]] = []
            for flow in analysis.flow_signals:
                first_sources = flow_ten_god_sources(flow, match.first_ten_god)
                second_sources = flow_ten_god_sources(flow, match.second_ten_god)
                if not first_sources and not second_sources:
                    continue
                domain_score, domain, polarity = flow_domain_activation_score(flow, list(match.domain_priority))
                first_source_weight = 12 if first_sources else 0
                second_source_weight = 12 if second_sources else 0
                simultaneous_bonus = 8 if first_sources and second_sources else 0
                hit_score = int(
                    round(
                        min(
                            100,
                            match.presence_score * 0.38
                            + domain_score * 0.42
                            + first_source_weight
                            + second_source_weight
                            + simultaneous_bonus,
                        )
                    )
                )
                if any(source.startswith("daeun") for source in first_sources) and any(
                    source.startswith("annual") for source in second_sources
                ):
                    sequence_state = "first_decade_second_year"
                elif any(source.startswith("daeun") for source in second_sources) and any(
                    source.startswith("annual") for source in first_sources
                ):
                    sequence_state = "second_decade_first_year"
                elif first_sources and second_sources:
                    sequence_state = "same_period_chain"
                elif first_sources:
                    sequence_state = "first_actor_only"
                else:
                    sequence_state = "second_actor_only"
                hits.append(
                    {
                        "year": int(getattr(flow, "year", 0) or 0),
                        "period_label": str(getattr(flow, "period_label", "") or ""),
                        "first_ten_god": match.first_ten_god,
                        "first_ten_god_label": TEN_GOD_LABELS.get(match.first_ten_god, match.first_ten_god),
                        "second_ten_god": match.second_ten_god,
                        "second_ten_god_label": TEN_GOD_LABELS.get(match.second_ten_god, match.second_ten_god),
                        "first_sources": first_sources,
                        "first_source_labels": [flow_source_labels.get(source, source) for source in first_sources],
                        "second_sources": second_sources,
                        "second_source_labels": [flow_source_labels.get(source, source) for source in second_sources],
                        "sequence_state": sequence_state,
                        "domain": domain,
                        "domain_label": DOMAIN_LABELS.get(domain, domain),
                        "polarity": polarity,
                        "compound_grade": compound_flow_grade(flow),
                        "activation_score": hit_score,
                    }
                )
            return sorted(hits, key=lambda item: (-int(item["activation_score"]), int(item["year"])))[:limit]

        def single_action_rank(match) -> tuple[int, int, int, str]:
            # Center lists must represent the natal structure. Timing hits are
            # still exposed on each match, but they should not decide which
            # natal action is called "center".
            timing_score = 0
            role_rank = {
                "core": 5,
                "core_overload": 5,
                "strong_regulator": 5,
                "danger": 5,
                "breaker": 5,
                "breaker_or_medicine": 4,
                "regulator_or_breaker": 4,
                "support": 4,
                "regulator": 4,
                "burden": 3,
                "conditioned_support": 3,
                "mixed": 2,
                "source": 2,
            }.get(str(match.role_grade), 0)
            critical_rank = 3 if any(
                str(code).startswith("gyeokguk_single_critical_action:")
                for code in list(getattr(match, "basis_codes", []) or [])
            ) else 0
            context_rank = {
                "constructive_by_context": 5,
                "medicine_or_regulator": 5,
                "risk_by_context": 5,
                "context_strengthens_action": 4,
                "conditional_by_context": 2,
                "context_weakens_action": 1,
                "not_activated": 0,
            }.get(str(getattr(match, "context_judgment_state", "")), 0)
            return (
                -(match.presence_score + timing_score + role_rank * 8 + critical_rank * 6 + context_rank * 7),
                -timing_score,
                -(role_rank + critical_rank + context_rank),
                match.rule_key,
            )

        def dual_action_rank(match) -> tuple[int, int, int, str]:
            # Center dual actions are selected by monthly command, pattern,
            # role grade, and contextual strength. Luck-cycle activation is
            # handled downstream as timing data, not as natal-center priority.
            timing_score = 0
            chain_rank = {
                "medicine_chain": 5,
                "constructive_chain": 5,
                "supportive_chain": 4,
                "mediated_tension_chain": 4,
                "success_chain": 4,
                "support_chain": 4,
                "risk_chain": 4,
                "compounded_burden_chain": 4,
                "conditional_chain": 3,
                "mixed_chain": 2,
                "disease_chain": 1,
            }.get(str(match.chain_grade), 0)
            exact_pair_rank = 2 if bool(getattr(match, "exact_pair_category", "")) else 0
            context_rank = {
                "structure_supports_expression": 5,
                "medicine_can_work": 5,
                "month_pressure_confirms_risk": 5,
                "risk_is_reinforced": 5,
                "context_strengthens_pair": 4,
                "conditional_by_context": 2,
                "context_weakens_pair": 1,
                "not_activated": 0,
            }.get(str(getattr(match, "context_judgment_state", "")), 0)
            return (
                -(match.presence_score + timing_score + chain_rank * 8 + exact_pair_rank * 6 + context_rank * 7),
                -timing_score,
                -(chain_rank + exact_pair_rank + context_rank),
                match.rule_key,
            )

        def dual_pair_center_signature(match) -> tuple[object, ...]:
            unordered_pair = tuple(sorted([match.first_ten_god, match.second_ten_god]))
            category = str(getattr(match, "exact_pair_category", "") or "")
            if not category:
                category = str(getattr(match, "first_to_second_relation", "") or "")
            return (
                category,
                unordered_pair,
            )

        def center_dual_action_matches(limit: int = 3):
            selected = []
            seen: set[tuple[object, ...]] = set()
            for match in sorted(profile.dual_ten_god_action_matches, key=dual_action_rank):
                signature = dual_pair_center_signature(match)
                if signature in seen:
                    continue
                seen.add(signature)
                selected.append(match)
                if len(selected) >= limit:
                    break
            return selected

        def extract_classical_action_tags(prefix: str, basis_codes) -> list[str]:
            tags: list[str] = []
            for code in list(basis_codes or []):
                value = str(code)
                if value.startswith(prefix):
                    tag = value.split(":", 1)[1]
                    if tag not in tags:
                        tags.append(tag)
            return tags

        def match_classical_action_tags(match, prefix: str) -> list[str]:
            direct_tags = list(getattr(match, "classical_action_tags", []) or [])
            if direct_tags:
                return direct_tags
            return extract_classical_action_tags(prefix, getattr(match, "basis_codes", []))

        def match_component_classical_action_tags(match) -> list[str]:
            direct_tags = [
                *list(getattr(match, "first_single_classical_action_tags", []) or []),
                *list(getattr(match, "second_single_classical_action_tags", []) or []),
            ]
            if direct_tags:
                return direct_tags
            return [
                *extract_classical_action_tags("gyeokguk_dual_first_single_classical_action:", match.basis_codes),
                *extract_classical_action_tags("gyeokguk_dual_second_single_classical_action:", match.basis_codes),
            ]

        def extract_mechanic_codes(prefix: str, basis_codes) -> list[str]:
            return [
                str(code)
                for code in list(basis_codes or [])
                if str(code).startswith(prefix)
            ]

        def month_fit_attention_weight(state: str) -> int:
            return {
                "supports_month_command": 18,
                "usable_by_month_command": 15,
                "mixed_by_month_command": 11,
                "harms_month_command": 17,
                "burdensome_by_month_command": 17,
                "both_supported_by_month_command": 20,
                "both_pressure_by_month_command": 20,
                "one_side_pressure_by_month_command": 16,
                "mixed_or_neutral_by_month_command": 10,
                "not_evaluated_by_month_command": 3,
            }.get(str(state), 3)

        def month_fit_label_for_selection(state: str) -> str:
            return {
                "supports_month_command": "월령이 해당 작용을 성격 방향으로 받침",
                "usable_by_month_command": "월령상 사용할 수 있는 작용",
                "mixed_by_month_command": "월령상 성패가 갈리는 작용",
                "harms_month_command": "월령 기준에서 파격 가능성이 있는 작용",
                "burdensome_by_month_command": "월령 기준에서 부담이 커지는 작용",
                "both_supported_by_month_command": "두 작용 모두 월령상 쓸 수 있음",
                "both_pressure_by_month_command": "두 작용 모두 월령상 부담 가능",
                "one_side_pressure_by_month_command": "한쪽은 쓰이고 한쪽은 부담",
                "mixed_or_neutral_by_month_command": "월령 판단이 혼합 또는 중립",
                "not_evaluated_by_month_command": "월령 적합성 미평가",
            }.get(str(state), str(state))

        def single_role_attention_weight(role_grade: str) -> int:
            return {
                "core": 18,
                "core_overload": 18,
                "danger": 18,
                "breaker": 18,
                "strong_regulator": 17,
                "breaker_or_medicine": 16,
                "regulator_or_breaker": 16,
                "support": 15,
                "regulator": 15,
                "burden": 13,
                "conditioned_support": 11,
                "mixed": 9,
                "source": 8,
            }.get(str(role_grade), 5)

        def dual_chain_attention_weight(chain_grade: str) -> int:
            return {
                "medicine_chain": 22,
                "constructive_chain": 21,
                "risk_chain": 21,
                "compounded_burden_chain": 20,
                "supportive_chain": 18,
                "mediated_tension_chain": 18,
                "success_chain": 18,
                "support_chain": 17,
                "conditional_chain": 15,
                "mixed_chain": 11,
                "disease_chain": 10,
            }.get(str(chain_grade), 6)

        def context_attention_weight(state: str) -> int:
            return {
                "constructive_by_context": 16,
                "medicine_or_regulator": 16,
                "risk_by_context": 16,
                "structure_supports_expression": 16,
                "medicine_can_work": 16,
                "month_pressure_confirms_risk": 16,
                "risk_is_reinforced": 16,
                "context_strengthens_action": 13,
                "context_strengthens_pair": 13,
                "conditional_by_context": 9,
                "context_weakens_action": 6,
                "context_weakens_pair": 6,
                "not_activated": 0,
            }.get(str(state), 4)

        MAJOR_CLASSICAL_ACTION_TAGS = {
                "siksang_saengjae",
                "jaesaenggwan",
                "gwanin_sangsaeng",
                "salin_sangsaeng",
                "siksin_jesal",
                "sanggwan_gyeongwan",
                "jaegeukin",
                "bigeop_jaengjae",
                "inseong_dosik",
                "jaesaengsal",
                "gwansal_honhap",
                "inbi_overload",
                "siksang_overload",
                "jaeda_sinyak_risk",
                "gwansal_overload",
        }
        CATEGORY_CLASSICAL_ACTION_TAGS = {
                "bigeop_generates_siksang",
                "jaeseong_generates_gwanseong",
                "gwanseong_generates_inseong",
                "inseong_generates_bigeop",
                "bigeop_controls_wealth",
                "wealth_controls_resource",
                "inseong_controls_output",
                "siksang_controls_gwanseong",
                "gwanseong_controls_bigeop",
                "bigeop_same_group",
                "siksang_same_group",
                "wealth_same_group",
                "gwanseong_same_group",
                "inseong_same_group",
        }
        SAME_GROUP_CLASSICAL_ACTION_TAGS = {
            "bigeop_same_group",
            "siksang_same_group",
            "wealth_same_group",
            "gwanseong_same_group",
            "inseong_same_group",
        }
        GENERIC_CLASSICAL_ACTION_TAGS = {
            "gyeokguk_specific_adjustment",
        }
        CENTER_DEDUPE_CLASSICAL_ACTION_TAGS = (
            MAJOR_CLASSICAL_ACTION_TAGS
            | CATEGORY_CLASSICAL_ACTION_TAGS
            | SAME_GROUP_CLASSICAL_ACTION_TAGS
        ) - GENERIC_CLASSICAL_ACTION_TAGS

        def classical_attention_weight(tags: list[str]) -> int:
            score = 0
            if any(tag in MAJOR_CLASSICAL_ACTION_TAGS for tag in tags):
                score += 18
            if any(tag in CATEGORY_CLASSICAL_ACTION_TAGS for tag in tags):
                score += 10
            return score

        def component_classical_attention_weight(tags: list[str]) -> int:
            tag_set = {str(tag) for tag in list(tags or [])}
            major_count = len(tag_set & MAJOR_CLASSICAL_ACTION_TAGS)
            category_count = len(tag_set & CATEGORY_CLASSICAL_ACTION_TAGS)
            return min(18, major_count * 7 + category_count * 4)

        def center_judgment_axis_from_resolution(
            resolution_state: str,
            grade_state: str,
            tags: set[str],
        ) -> dict[str, object]:
            """Expose whether a candidate is seonggyeok, pagyeok, or byeong-yak."""

            state = str(resolution_state or "")
            grade = str(grade_state or "")
            hard_pagyeok = (
                "pagyeok" in state
                or "disease" in state
                or grade in {"risk_chain", "compounded_burden_chain", "danger", "breaker", "core_overload"}
            )
            if "byeongyak" in state or "medicine" in state or grade in {"medicine_chain", "breaker_or_medicine"}:
                return {
                    "code": "byeongyak_medicine",
                    "label": "병약 조절",
                    "summary": "격국의 병을 덜거나 과한 작용을 쓸모로 돌리는 축",
                    "score": 13,
                }
            if hard_pagyeok:
                return {
                    "code": "pagyeok_or_disease",
                    "label": "파격·병증",
                    "summary": "격국의 중심을 흔들거나 현실 사건에서 부담으로 드러나는 축",
                    "score": 12,
                }
            if "seonggyeok" in state or grade in {"constructive_chain", "supportive_chain", "core", "support", "source"}:
                if bool(tags & CAUTION_CLASSICAL_ACTION_TAGS):
                    return {
                        "code": "seonggyeok_with_caution",
                        "label": "성격 작용·병증 점검",
                        "summary": "격국을 세우는 작용이지만 과하면 병증으로 기울 수 있는 축",
                        "score": 12,
                    }
                return {
                    "code": "seonggyeok",
                    "label": "성격 작용",
                    "summary": "격국의 성립과 현실 성과를 받치는 축",
                    "score": 12,
                }
            if "conditional" in state or "mixed" in state or grade in {"conditional_chain", "mixed_chain", "mixed"}:
                return {
                    "code": "conditional_axis",
                    "label": "조건부 성패",
                    "summary": "월령, 강약, 위치에 따라 성패가 갈리는 축",
                    "score": 7,
                }
            return {
                "code": "secondary_axis",
                "label": "보조 작용",
                "summary": "격국 중심을 보조하거나 세부 사건으로 드러나는 축",
                "score": 4,
            }

        def ten_god_operation_depth_basis(
            source: str,
            match,
            tags: list[str],
            component_tags: list[str] | None = None,
        ) -> dict[str, object]:
            """Score how deeply the candidate explains the pattern by ten-god logic."""

            tag_set = {str(tag) for tag in list(tags or [])}
            component_set = {str(tag) for tag in list(component_tags or [])}
            all_tags = tag_set | component_set
            major_tags = sorted(all_tags & MAJOR_CLASSICAL_ACTION_TAGS)
            category_tags = sorted(all_tags & CATEGORY_CLASSICAL_ACTION_TAGS)
            support_tags = sorted(all_tags & SUPPORT_CLASSICAL_ACTION_TAGS)
            caution_tags = sorted(all_tags & CAUTION_CLASSICAL_ACTION_TAGS)
            has_generation_chain = any(
                tag in all_tags
                for tag in {
                    "siksang_saengjae",
                    "jaesaenggwan",
                    "gwanin_sangsaeng",
                    "salin_sangsaeng",
                    "jaesaengsal",
                    "jaeseong_generates_gwanseong",
                    "gwanseong_generates_inseong",
                    "bigeop_generates_siksang",
                    "inseong_generates_bigeop",
                }
            )
            has_control_chain = any(
                tag in all_tags
                for tag in {
                    "siksin_jesal",
                    "sanggwan_gyeongwan",
                    "jaegeukin",
                    "bigeop_jaengjae",
                    "inseong_dosik",
                    "siksang_controls_gwanseong",
                    "wealth_controls_resource",
                    "bigeop_controls_wealth",
                    "inseong_controls_output",
                    "gwanseong_controls_bigeop",
                }
            )
            has_overload_chain = any(
                tag in all_tags
                for tag in {
                    "gwansal_honhap",
                    "inbi_overload",
                    "siksang_overload",
                    "jaeda_sinyak_risk",
                    "gwansal_overload",
                }
            )
            activation_order_profile = (
                dict(getattr(match, "activation_order_profile", {}) or {})
                if source == "dual"
                else {}
            )
            first_order = dict(activation_order_profile.get("first_then_second", {}) or {})
            second_order = dict(activation_order_profile.get("second_then_first", {}) or {})
            activation_order_score = 0
            if first_order and second_order:
                if first_order.get("entry_ten_god") and second_order.get("entry_ten_god"):
                    activation_order_score += 2
                if first_order.get("entry_event_targets") and first_order.get("result_event_targets"):
                    activation_order_score += 2
                if second_order.get("entry_event_targets") and second_order.get("result_event_targets"):
                    activation_order_score += 2
                if first_order.get("entry_event_targets") != second_order.get("entry_event_targets"):
                    activation_order_score += 2
                activation_order_score = min(8, activation_order_score)
            if source == "single":
                resolution_state = str(getattr(match, "pattern_resolution_state", "") or "")
                grade_state = str(getattr(match, "role_grade", "") or "")
                relation_state = str(getattr(match, "relation_to_pattern", "") or "")
                relation_score = {
                    "actor_controls_pattern": 8,
                    "pattern_controls_actor": 8,
                    "actor_generates_pattern": 7,
                    "pattern_generates_actor": 7,
                    "same_group": 5,
                    "indirect_relation": 2,
                }.get(relation_state, 1 if relation_state else 0)
                resolution_score = {
                    "seonggyeok_center": 12,
                    "seonggyeok_support": 11,
                    "seonggyeok_source": 10,
                    "byeongyak_medicine": 12,
                    "medicine_or_pagyeok": 10,
                    "pagyeok_or_medicine": 10,
                    "pagyeok_risk": 11,
                    "strong_pagyeok_risk": 12,
                    "disease_overload": 11,
                    "disease_burden": 10,
                    "conditional_seonggyeok": 8,
                    "conditional_mixed": 6,
                }.get(resolution_state, 3)
                grade_score = {
                    "core": 10,
                    "core_overload": 10,
                    "strong_regulator": 10,
                    "regulator": 9,
                    "breaker": 10,
                    "danger": 10,
                    "breaker_or_medicine": 9,
                    "regulator_or_breaker": 9,
                    "support": 8,
                    "source": 6,
                    "burden": 7,
                    "conditioned_support": 6,
                    "mixed": 5,
                }.get(grade_state, 3)
            else:
                resolution_state = str(getattr(match, "combination_resolution_state", "") or "")
                grade_state = str(getattr(match, "chain_grade", "") or "")
                relation_state = str(getattr(match, "first_to_second_relation", "") or "")
                relation_score = {
                    "first_generates_second": 8,
                    "second_generates_first": 8,
                    "first_controls_second": 9,
                    "second_controls_first": 9,
                    "same_group": 5,
                }.get(relation_state, 2 if relation_state else 0)
                resolution_score = {
                    "seonggyeok_chain": 12,
                    "seonggyeok_support_chain": 11,
                    "byeongyak_medicine_chain": 13,
                    "pagyeok_chain": 12,
                    "compounded_disease_chain": 12,
                    "mediated_condition_chain": 10,
                    "conditional_chain": 8,
                    "mixed_chain": 6,
                }.get(resolution_state, 3)
                grade_score = {
                    "medicine_chain": 11,
                    "constructive_chain": 10,
                    "supportive_chain": 9,
                    "success_chain": 9,
                    "support_chain": 8,
                    "mediated_tension_chain": 8,
                    "risk_chain": 11,
                    "compounded_burden_chain": 11,
                    "conditional_chain": 7,
                    "mixed_chain": 5,
                    "disease_chain": 10,
                }.get(grade_state, 3)

            classical_score = min(10, len(major_tags) * 4 + len(category_tags) * 2)
            chain_score = 0
            if has_generation_chain:
                chain_score = max(chain_score, 4)
            if has_control_chain:
                chain_score = max(chain_score, 5)
            if has_overload_chain:
                chain_score = max(chain_score, 4)
            support_caution_score = min(6, len(support_tags) * 2 + len(caution_tags) * 2)
            center_axis = center_judgment_axis_from_resolution(resolution_state, grade_state, all_tags)
            center_axis_score = int(center_axis.get("score") or 0)
            raw_score = (
                relation_score
                + resolution_score
                + grade_score
                + classical_score
                + chain_score
                + support_caution_score
                + center_axis_score
                + activation_order_score
            )
            return {
                "state": resolution_state,
                "grade_state": grade_state,
                "relation_state": relation_state,
                "score": min(64, raw_score),
                "relation_score": relation_score,
                "resolution_score": resolution_score,
                "grade_score": grade_score,
                "classical_score": classical_score,
                "chain_score": chain_score,
                "support_caution_score": support_caution_score,
                "activation_order_score": activation_order_score,
                "center_judgment_axis": center_axis,
                "center_axis_score": center_axis_score,
                "major_tags": major_tags,
                "category_tags": category_tags,
                "support_tags": support_tags,
                "caution_tags": caution_tags,
                "has_generation_chain": has_generation_chain,
                "has_control_chain": has_control_chain,
                "has_overload_chain": has_overload_chain,
            }

        def center_dedupe_tags(tags: list[str]) -> set[str]:
            return {
                str(tag)
                for tag in list(tags or [])
                if str(tag) in CENTER_DEDUPE_CLASSICAL_ACTION_TAGS
            }

        def center_candidate_repeats_existing(candidate_tags: set[str], seen_tags: set[str]) -> bool:
            if not candidate_tags or not seen_tags:
                return False
            overlap = candidate_tags & seen_tags
            if not overlap:
                return False
            new_tags = candidate_tags - seen_tags
            if not new_tags:
                return True
            return len(overlap) >= 2 and len(overlap) >= len(new_tags)

        def center_flow_activation_score(timing_score: int) -> int:
            # The center action is selected from the natal structure first.
            # Luck-cycle activation is preserved separately as timing_score and
            # raw_selection_basis, but it must not decide the natal center.
            return 0

        def center_specificity_adjustment(tags: list[str]) -> int:
            tag_set = {str(tag) for tag in list(tags or [])}
            has_major = bool(tag_set & MAJOR_CLASSICAL_ACTION_TAGS)
            has_same_group = bool(tag_set & SAME_GROUP_CLASSICAL_ACTION_TAGS)
            if has_same_group and not has_major:
                return -22
            if has_major:
                return 6
            return 0

        CAUTION_CLASSICAL_ACTION_TAGS = {
            "sanggwan_gyeongwan",
            "jaegeukin",
            "bigeop_jaengjae",
            "inseong_dosik",
            "jaesaengsal",
            "gwansal_honhap",
            "inbi_overload",
            "siksang_overload",
            "jaeda_sinyak_risk",
            "gwansal_overload",
            "bigeop_controls_wealth",
            "wealth_controls_resource",
            "inseong_controls_output",
        }
        SUPPORT_CLASSICAL_ACTION_TAGS = {
            "siksang_saengjae",
            "jaesaenggwan",
            "gwanin_sangsaeng",
            "salin_sangsaeng",
            "siksin_jesal",
            "jaeseong_generates_gwanseong",
            "gwanseong_generates_inseong",
            "siksang_controls_gwanseong",
            "gwanseong_controls_bigeop",
            "bigeop_generates_siksang",
            "inseong_generates_bigeop",
        }

        def has_pattern_center_bridge(match) -> bool:
            return any(
                str(code).startswith("gyeokguk_dual_pattern_center_bridge:")
                for code in list(getattr(match, "basis_codes", []) or [])
            )

        def pattern_center_relevance(source: str, match) -> dict[str, object]:
            pattern_ten_god = str(profile.primary_ten_god)
            pattern_group = str(profile.primary_group)
            if source == "single":
                direct = str(getattr(match, "acting_ten_god", "")) == pattern_ten_god
                same_group = str(getattr(match, "acting_group", "")) == pattern_group
                relation = str(getattr(match, "relation_to_pattern", ""))
                bridge = False
                if direct:
                    score = 42
                    label = "격국 중심 십신이 직접 작용"
                elif same_group:
                    score = 30
                    label = "격국 중심과 같은 계열의 작용"
                elif relation:
                    score = 8
                    label = "격국 중심과 간접 연결"
                else:
                    score = -8
                    label = "격국 중심과의 연결 약함"
                return {
                    "direct_center_actor": direct,
                    "same_group_as_center": same_group,
                    "pattern_center_bridge": bridge,
                    "label": label,
                    "score": score,
                }

            first_direct = str(getattr(match, "first_ten_god", "")) == pattern_ten_god
            second_direct = str(getattr(match, "second_ten_god", "")) == pattern_ten_god
            first_same_group = str(getattr(match, "first_group", "")) == pattern_group
            second_same_group = str(getattr(match, "second_group", "")) == pattern_group
            bridge = has_pattern_center_bridge(match)
            direct = first_direct or second_direct
            same_group = first_same_group or second_same_group
            if direct:
                score = 46
                label = "격국 중심 십신이 이중 작용 안에 직접 포함"
            elif bridge:
                score = 28
                label = "두 십신 작용이 격국 중심을 경유"
            elif same_group:
                score = 32
                label = "격국 중심 계열이 이중 작용 안에 포함"
            else:
                score = -10
                label = "격국 중심 밖에서 이어지는 보조 작용"
            return {
                "direct_center_actor": direct,
                "same_group_as_center": same_group,
                "pattern_center_bridge": bridge,
                "label": label,
                "score": score,
            }

        def exact_ten_god_specificity_basis(source: str, match) -> dict[str, object]:
            """Keep exact ten-god faces visible in center-action selection."""

            if source == "single":
                ten_gods = [str(getattr(match, "acting_ten_god", "") or "")]
                pair_bonus = 0
                pair_state = ""
            else:
                ten_gods = [
                    str(getattr(match, "first_ten_god", "") or ""),
                    str(getattr(match, "second_ten_god", "") or ""),
                ]
                pair_state = str(getattr(match, "exact_pair_category", "") or "")
                pair_bonus = 6 if pair_state else 0
                if str(getattr(match, "exact_pair_effect", "") or "") and str(getattr(match, "exact_pair_risk", "") or ""):
                    pair_bonus += 4

            domains: list[str] = []
            exact_faces: list[str] = []
            for ten_god in ten_gods:
                exact_nuance = str(TEN_GOD_EXACT_NUANCE.get(ten_god, "") or "")
                exact_profile = TEN_GOD_EXACT_ACTION_PROFILE.get(ten_god, {})
                if exact_nuance:
                    exact_faces.append(ten_god)
                if isinstance(exact_profile, dict):
                    domains.extend(str(domain) for domain in list(exact_profile.get("domains", []) or []) if domain)

            domain_score = min(10, len(set(domains)) * 2)
            face_score = min(8, len(exact_faces) * 4)
            score = min(28, domain_score + face_score + pair_bonus)
            return {
                "score": score,
                "ten_gods": ten_gods,
                "exact_faces": exact_faces,
                "domains": sorted(set(domains)),
                "pair_state": pair_state,
                "domain_score": domain_score,
                "face_score": face_score,
                "pair_bonus": pair_bonus,
            }

        def selection_role_for_candidate(source: str, match, tags: list[str]) -> dict[str, str]:
            tag_set = {str(tag) for tag in list(tags or [])}
            month_state = str(getattr(match, "month_fit_state", ""))
            context_state = str(getattr(match, "context_judgment_state", ""))
            risk_by_context = context_state in {
                "risk_by_context",
                "risk_is_reinforced",
                "month_pressure_confirms_risk",
                "context_weakens_action",
                "context_weakens_pair",
            }
            month_pressure = month_state in {
                "harms_month_command",
                "burdensome_by_month_command",
                "both_pressure_by_month_command",
                "one_side_pressure_by_month_command",
            }
            if source == "dual":
                chain_grade = str(getattr(match, "chain_grade", ""))
                if chain_grade in {"risk_chain", "compounded_burden_chain", "disease_chain"}:
                    return {
                        "code": "caution",
                        "label": "주의 작용",
                        "reason": "두 십신이 결합하면서 손상, 부담, 충돌 쪽으로 기울 수 있음",
                    }
                if chain_grade == "medicine_chain":
                    return {
                        "code": "primary",
                        "label": "대표 작용",
                        "reason": "격국의 병을 제어하거나 과한 작용을 쓰임으로 돌리는 병약 작용",
                    }
                if tag_set & CAUTION_CLASSICAL_ACTION_TAGS and (
                    risk_by_context or month_pressure or has_pattern_center_bridge(match)
                ):
                    return {
                        "code": "caution",
                        "label": "주의 작용",
                        "reason": "주의 태그가 월령·맥락 보정에서 강화됨",
                    }
                if chain_grade == "constructive_chain":
                    return {
                        "code": "primary",
                        "label": "대표 작용",
                        "reason": "격국 성립이나 병약 조절을 직접 이끄는 이중 작용",
                    }
                if chain_grade in {"supportive_chain", "success_chain", "support_chain", "mediated_tension_chain"}:
                    return {
                        "code": "support",
                        "label": "보조 작용",
                        "reason": "격국 중심을 보조하거나 결과로 이어 주는 작용",
                    }
                return {
                    "code": "conditional",
                    "label": "조건부 작용",
                    "reason": "월령, 강약, 위치에 따라 성패가 갈리는 작용",
                }

            role_grade = str(getattr(match, "role_grade", ""))
            if role_grade in {"breaker", "danger", "burden", "core_overload"}:
                return {
                    "code": "caution",
                    "label": "주의 작용",
                    "reason": "격국 중심을 흔들거나 부담을 더하는 단일 작용",
                }
            if role_grade in {"regulator_or_breaker", "breaker_or_medicine"} and (
                risk_by_context or month_pressure or bool(tag_set & CAUTION_CLASSICAL_ACTION_TAGS)
            ):
                return {
                    "code": "caution",
                    "label": "주의 작용",
                    "reason": "약으로도 쓰이나 조건이 어긋나면 파격으로 기울 수 있음",
                }
            if role_grade in {"core", "strong_regulator", "regulator"}:
                return {
                    "code": "primary",
                    "label": "대표 작용",
                    "reason": "격국 중심이나 병약 조절에 직접 관여하는 작용",
                }
            if role_grade in {"source", "support", "conditioned_support"} or bool(tag_set & SUPPORT_CLASSICAL_ACTION_TAGS):
                return {
                    "code": "support",
                    "label": "보조 작용",
                    "reason": "격국 성립을 받치거나 현실 결과를 보조하는 작용",
                }
            return {
                "code": "conditional",
                "label": "조건부 작용",
                "reason": "월령, 강약, 위치에 따라 작용 방향이 갈리는 십신",
            }

        def center_reason_parts(
            *,
            month_fit_state: str,
            context_state: str,
            tags: list[str],
            timing_score: int,
            relation_text: str,
        ) -> list[str]:
            reasons = []
            if month_fit_attention_weight(month_fit_state) >= 10:
                reasons.append("월령 기준에서 해석 비중이 큼")
            if context_attention_weight(context_state) >= 13:
                reasons.append("강약·조후·위치 보정 후 중심 작용으로 강화")
            if tags:
                reasons.append("핵심 십신 작용 태그 확인")
            if timing_score >= 50:
                reasons.append("대운·세운에서 발동 가능성 확인")
            if relation_text:
                reasons.append(relation_text)
            return reasons[:5]

        def context_score_delta_from_basis(basis_codes, prefix: str) -> int:
            for code in list(basis_codes or []):
                value = str(code)
                if value.startswith(prefix):
                    raw = value.split(":", 1)[1]
                    try:
                        return int(raw)
                    except ValueError:
                        return 0
            return 0

        def position_attention_from_context(position_context) -> tuple[int, str]:
            if not isinstance(position_context, dict):
                return 0, "위치 판단 미평가"
            subcontexts = []
            if "first" in position_context or "second" in position_context:
                for key in ("first", "second"):
                    data = position_context.get(key)
                    if isinstance(data, dict):
                        subcontexts.append(data)
            else:
                subcontexts.append(position_context)

            score = 0
            labels: list[str] = []
            for data in subcontexts:
                grade = str(data.get("grade", "") or "")
                visible = list(data.get("visible_positions", []) or [])
                branch_main = list(data.get("branch_main_positions", []) or [])
                hidden = list(data.get("hidden_positions", []) or [])
                if "month" in visible or "month" in branch_main:
                    score += 13
                    labels.append("월주·월지에서 확인")
                elif "day" in branch_main or "day" in hidden:
                    score += 10
                    labels.append("일지·생활 자리에서 확인")
                elif visible:
                    score += 8
                    labels.append("천간 투출")
                elif branch_main:
                    score += 7
                    labels.append("지지 본기")
                elif hidden:
                    score += 5
                    labels.append("지장간 잠복")
                elif grade:
                    labels.append(grade)
            return min(20, score), ", ".join(dict.fromkeys(labels)) or "위치 신호 약함"

        def protrusion_attention_from_position_context(position_context) -> tuple[int, str]:
            if not isinstance(position_context, dict):
                return 0, "투출 판단 미평가"
            subcontexts = []
            if "first" in position_context or "second" in position_context:
                for key in ("first", "second"):
                    data = position_context.get(key)
                    if isinstance(data, dict):
                        subcontexts.append(data)
            else:
                subcontexts.append(position_context)

            visible_positions: list[str] = []
            for data in subcontexts:
                visible_positions.extend(str(item) for item in list(data.get("visible_positions", []) or []))
            if "month" in visible_positions:
                return 10, "월간 투출"
            if visible_positions:
                return 7, "천간 투출"
            return 1, "투출 약함"

        def rooting_attention_from_position_context(position_context) -> tuple[int, str]:
            if not isinstance(position_context, dict):
                return 0, "통근 판단 미평가"
            subcontexts = []
            if "first" in position_context or "second" in position_context:
                for key in ("first", "second"):
                    data = position_context.get(key)
                    if isinstance(data, dict):
                        subcontexts.append(data)
            else:
                subcontexts.append(position_context)

            branch_main_positions: list[str] = []
            hidden_positions: list[str] = []
            for data in subcontexts:
                branch_main_positions.extend(str(item) for item in list(data.get("branch_main_positions", []) or []))
                hidden_positions.extend(str(item) for item in list(data.get("hidden_positions", []) or []))
            if "month" in branch_main_positions:
                return 10, "월지 본기 통근"
            if branch_main_positions:
                return 7, "지지 본기 통근"
            if hidden_positions:
                return 4, "지장간 뿌리"
            return 1, "통근 약함"

        def hidden_attention_from_position_context(position_context) -> tuple[int, str]:
            if not isinstance(position_context, dict):
                return 0, "지장간 판단 미평가"
            subcontexts = []
            if "first" in position_context or "second" in position_context:
                for key in ("first", "second"):
                    data = position_context.get(key)
                    if isinstance(data, dict):
                        subcontexts.append(data)
            else:
                subcontexts.append(position_context)

            hidden_positions: list[str] = []
            branch_main_positions: list[str] = []
            for data in subcontexts:
                hidden_positions.extend(str(item) for item in list(data.get("hidden_positions", []) or []))
                branch_main_positions.extend(str(item) for item in list(data.get("branch_main_positions", []) or []))
            if "month" in hidden_positions or "month" in branch_main_positions:
                return 8, "월지 본기·지장간 작용"
            if hidden_positions:
                return 6, "지장간 잠복 작용"
            if branch_main_positions:
                return 5, "지지 본기 작용"
            return 1, "지장간 작용 약함"

        def branch_attention_from_context(branch_context) -> tuple[int, str]:
            if not isinstance(branch_context, dict):
                return 0, "합충형파해 미평가"
            subcontexts = []
            if "first" in branch_context or "second" in branch_context:
                for key in ("first", "second"):
                    data = branch_context.get(key)
                    if isinstance(data, dict):
                        subcontexts.append(data)
            else:
                subcontexts.append(branch_context)

            score = 0
            labels: list[str] = []
            for data in subcontexts:
                grade = str(data.get("grade", "") or "")
                relations = list(data.get("relations", []) or [])
                if grade == "branch_relation_pressures_actor":
                    score += 12
                    labels.append("충·형·파·해 압력")
                elif grade == "branch_relation_supports_actor":
                    score += 9
                    labels.append("합·회합 보조")
                elif grade == "branch_relation_mixed_actor":
                    score += 7
                    labels.append("성립과 흔들림 공존")
                elif relations:
                    score += 5
                    labels.append("지지 작용 확인")
            return min(18, score), ", ".join(dict.fromkeys(labels)) or "직접 작용 약함"

        def strength_attention_from_label(label: str) -> int:
            value = str(label)
            if "보강" in value or "배출" in value or "제어" in value:
                return 10
            if "부담" in value or "편중" in value:
                return 9
            if "중립" in value:
                return 4
            return 2 if value else 0

        def climate_attention_from_label(label: str) -> int:
            value = str(label)
            if "조후상 필요한" in value:
                return 12
            if "쓸 수 있는" in value or "구조상" in value:
                return 7
            if "과해지기 쉬운" in value or "불필요" in value:
                return 9
            return 2 if value else 0

        def compact_basis_label(label: str) -> str:
            parts = [part.strip() for part in str(label or "").split(" / ") if part.strip()]
            if not parts:
                return ""
            return " / ".join(dict.fromkeys(parts))

        def formation_label_for_selection(state: str) -> str:
            return {
                "properly_formed": "격이 분명하게 성립함",
                "formed_with_conditions": "격은 성립하나 병약과 조건을 함께 봄",
                "partially_formed": "격의 중심은 있으나 투출·통근 보강이 필요함",
                "latent_but_usable": "격의 씨앗은 있으나 발동 조건이 필요함",
                "weak_or_fragmented": "격의 힘이 흩어져 보조 구조를 함께 봄",
                "undetermined": "격국 성립도 미정",
            }.get(str(state), "격국 성립도 점검")

        def formation_attention_weight(state: str) -> int:
            return {
                "properly_formed": 14,
                "formed_with_conditions": 12,
                "partially_formed": 10,
                "latent_but_usable": 8,
                "weak_or_fragmented": 7,
                "undetermined": 0,
            }.get(str(state), 5)

        def single_selection_basis(match, tags: list[str], timing_score: int) -> dict[str, object]:
            position_score, position_label = position_attention_from_context(match.position_context)
            protrusion_score, protrusion_label = protrusion_attention_from_position_context(match.position_context)
            rooting_score, rooting_label = rooting_attention_from_position_context(match.position_context)
            hidden_score, hidden_label = hidden_attention_from_position_context(match.position_context)
            branch_score, branch_label = branch_attention_from_context(match.branch_relation_context)
            context_delta = context_score_delta_from_basis(match.basis_codes, "gyeokguk_single_context_score_delta:")
            operation_depth = ten_god_operation_depth_basis("single", match, tags)
            exact_specificity = exact_ten_god_specificity_basis("single", match)
            basis = {
                "order": [
                    "month_command",
                    "gyeokguk_role",
                    "gyeokguk_formation",
                    "day_master_strength",
                    "climate",
                    "protrusion",
                    "rooting",
                    "position",
                    "hidden_stems",
                    "branch_interactions",
                    "flow_activation",
                ],
                "month_command": {
                    "state": match.month_fit_state,
                    "label": month_fit_label_for_selection(match.month_fit_state),
                    "score": month_fit_attention_weight(match.month_fit_state),
                },
                "gyeokguk_role": {
                    "state": match.role_grade,
                    "label": match.pattern_effect_state,
                    "score": single_role_attention_weight(match.role_grade),
                },
                "gyeokguk_formation": {
                    "state": profile.formation_state,
                    "clarity_state": profile.clarity_state,
                    "label": formation_label_for_selection(profile.formation_state),
                    "score": formation_attention_weight(profile.formation_state),
                },
                "day_master_strength": {
                    "label": compact_basis_label(match.day_master_strength_context),
                    "score": strength_attention_from_label(match.day_master_strength_context),
                },
                "climate": {
                    "label": compact_basis_label(match.climate_context),
                    "score": climate_attention_from_label(match.climate_context),
                },
                "protrusion": {
                    "label": protrusion_label,
                    "score": protrusion_score,
                },
                "rooting": {
                    "label": rooting_label,
                    "score": rooting_score,
                },
                "position": {
                    "label": position_label,
                    "score": position_score,
                },
                "hidden_stems": {
                    "label": hidden_label,
                    "score": hidden_score,
                },
                "branch_interactions": {
                    "label": branch_label,
                    "score": branch_score,
                },
                "flow_activation": {
                    "label": "대운·세운 발동성",
                    "score": timing_score,
                },
                "context_score_delta": context_delta,
                "classical_action_score": classical_attention_weight(tags),
                "component_classical_action_score": 0,
                "pattern_center_relevance": pattern_center_relevance("single", match),
                "ten_god_operation_depth": operation_depth,
                "exact_ten_god_specificity": exact_specificity,
            }
            return basis

        def dual_selection_basis(match, tags: list[str], timing_score: int) -> dict[str, object]:
            position_score, position_label = position_attention_from_context(match.position_context)
            protrusion_score, protrusion_label = protrusion_attention_from_position_context(match.position_context)
            rooting_score, rooting_label = rooting_attention_from_position_context(match.position_context)
            hidden_score, hidden_label = hidden_attention_from_position_context(match.position_context)
            branch_score, branch_label = branch_attention_from_context(match.branch_relation_context)
            context_delta = context_score_delta_from_basis(match.basis_codes, "gyeokguk_dual_context_score_delta:")
            component_tags = match_component_classical_action_tags(match)
            operation_depth = ten_god_operation_depth_basis("dual", match, tags, component_tags)
            exact_specificity = exact_ten_god_specificity_basis("dual", match)
            basis = {
                "order": [
                    "month_command",
                    "gyeokguk_chain",
                    "gyeokguk_formation",
                    "day_master_strength",
                    "climate",
                    "protrusion",
                    "rooting",
                    "position",
                    "hidden_stems",
                    "branch_interactions",
                    "flow_activation",
                ],
                "month_command": {
                    "state": match.month_fit_state,
                    "label": month_fit_label_for_selection(match.month_fit_state),
                    "score": month_fit_attention_weight(match.month_fit_state),
                },
                "gyeokguk_chain": {
                    "state": match.chain_grade,
                    "label": match.pattern_combination_state,
                    "score": dual_chain_attention_weight(match.chain_grade),
                },
                "gyeokguk_formation": {
                    "state": profile.formation_state,
                    "clarity_state": profile.clarity_state,
                    "label": formation_label_for_selection(profile.formation_state),
                    "score": formation_attention_weight(profile.formation_state),
                },
                "day_master_strength": {
                    "label": compact_basis_label(match.day_master_strength_context),
                    "score": strength_attention_from_label(match.day_master_strength_context),
                },
                "climate": {
                    "label": compact_basis_label(match.climate_context),
                    "score": climate_attention_from_label(match.climate_context),
                },
                "protrusion": {
                    "label": protrusion_label,
                    "score": protrusion_score,
                },
                "rooting": {
                    "label": rooting_label,
                    "score": rooting_score,
                },
                "position": {
                    "label": position_label,
                    "score": position_score,
                },
                "hidden_stems": {
                    "label": hidden_label,
                    "score": hidden_score,
                },
                "branch_interactions": {
                    "label": branch_label,
                    "score": branch_score,
                },
                "flow_activation": {
                    "label": "대운·세운 발동성",
                    "score": timing_score,
                },
                "context_score_delta": context_delta,
                "classical_action_score": classical_attention_weight(tags),
                "component_classical_action_score": component_classical_attention_weight(component_tags),
                "pattern_center_relevance": pattern_center_relevance("dual", match),
                "ten_god_operation_depth": operation_depth,
                "exact_ten_god_specificity": exact_specificity,
            }
            return basis

        def basis_attention_total(basis: dict[str, object]) -> int:
            total = 0
            for key in list(basis.get("order", []) or []):
                item = basis.get(key)
                if isinstance(item, dict):
                    total += int(item.get("score") or 0)
            total += int(basis.get("classical_action_score") or 0)
            total += int(basis.get("component_classical_action_score") or 0)
            pattern_relevance = basis.get("pattern_center_relevance")
            if isinstance(pattern_relevance, dict):
                total += int(pattern_relevance.get("score") or 0)
            operation_depth = basis.get("ten_god_operation_depth")
            if isinstance(operation_depth, dict):
                total += int(operation_depth.get("score") or 0)
            exact_specificity = basis.get("exact_ten_god_specificity")
            if isinstance(exact_specificity, dict):
                total += int(exact_specificity.get("score") or 0)
            total += max(0, min(16, abs(int(basis.get("context_score_delta") or 0))))
            return total

        EVENT_AXIS_LABELS = {
            "money": "돈",
            "asset": "자산",
            "income": "수입",
            "work": "직장",
            "authority": "권한",
            "people": "사람",
            "partner": "배우자",
            "document": "문서",
            "responsibility": "책임",
            "evaluation": "평가",
            "output": "결과물",
            "personality": "성격",
            "tendency": "경향",
            "judgment": "판단 방식",
            "timing": "시기",
        }

        DOMAIN_EVENT_AXES = {
            "money": ["money", "income", "asset"],
            "career": ["work", "authority", "responsibility"],
            "relationship": ["people"],
            "marriage": ["partner", "money", "responsibility"],
            "personality": ["personality", "tendency", "judgment"],
            "reputation": ["evaluation", "authority"],
            "timing": ["timing"],
        }

        TAG_EVENT_AXES = {
            "siksang_saengjae": ["output", "income", "money"],
            "jaesaenggwan": ["money", "responsibility", "evaluation"],
            "jaeseong_generates_gwanseong": ["money", "work", "responsibility"],
            "gwanin_sangsaeng": ["work", "document", "evaluation"],
            "salin_sangsaeng": ["responsibility", "document", "work"],
            "gwanseong_generates_inseong": ["responsibility", "document", "evaluation"],
            "siksin_jesal": ["output", "responsibility", "work"],
            "sanggwan_gyeongwan": ["evaluation", "work", "authority"],
            "siksang_controls_gwanseong": ["output", "authority", "evaluation"],
            "jaegeukin": ["money", "document", "asset"],
            "wealth_controls_resource": ["money", "document", "tendency"],
            "bigeop_jaengjae": ["money", "people", "asset"],
            "bigeop_controls_wealth": ["people", "money", "asset"],
            "gwanseong_controls_bigeop": ["work", "responsibility", "people"],
            "inseong_dosik": ["document", "output", "tendency"],
            "inseong_controls_output": ["document", "output", "tendency"],
            "jaesaengsal": ["money", "responsibility", "work"],
            "gwansal_honhap": ["work", "responsibility", "evaluation"],
            "gwanseong_same_group": ["work", "responsibility", "evaluation"],
            "inbi_overload": ["personality", "document", "people"],
            "inseong_generates_bigeop": ["document", "personality", "people"],
            "siksang_overload": ["output", "evaluation", "work"],
            "siksang_same_group": ["output", "evaluation", "tendency"],
            "jaeda_sinyak_risk": ["money", "asset", "responsibility"],
            "wealth_same_group": ["money", "asset", "income"],
            "gwansal_overload": ["responsibility", "work", "evaluation"],
            "bigeop_generates_siksang": ["people", "output", "work"],
            "inseong_same_group": ["document", "personality", "tendency"],
            "bigeop_same_group": ["people", "money"],
        }

        AXIS_STATEMENTS = {
            "money": "금전의 발생, 분배, 손익 판단으로 드러난다.",
            "asset": "소유권, 자산화, 공동 명의 문제로 이어질 수 있다.",
            "income": "수입 구조와 보상 방식에 직접 연결된다.",
            "work": "직장, 직무, 조직 안의 역할 문제로 나타난다.",
            "authority": "권한, 결정권, 직책의 범위가 중요해진다.",
            "people": "가까운 사람, 동업자, 지인과의 이해관계로 드러난다.",
            "partner": "배우자와의 생활 기준, 책임 분담으로 나타난다.",
            "document": "계약서, 자격, 문서, 명분의 안정성이 핵심이 된다.",
            "responsibility": "책임, 압박, 맡아야 할 범위로 사건화된다.",
            "evaluation": "평판, 인정, 공식 평가의 문제로 올라온다.",
            "output": "기술, 결과물, 서비스, 표현물이 현실 성과의 근거가 된다.",
            "personality": "반응 방식, 자기 기준, 사람을 대하는 태도로 드러난다.",
            "tendency": "반복되는 선택 습관과 관심의 방향으로 이어진다.",
            "judgment": "판단 습관, 고집, 보류, 실행 속도의 문제로 드러난다.",
            "timing": "대운·세운에서 해당 작용이 들어올 때 사건성이 커진다.",
        }

        def event_axes_for_candidate(match, tags: list[str]) -> list[str]:
            axes: list[str] = []
            for tag in tags:
                axes.extend(TAG_EVENT_AXES.get(str(tag), []))
            for domain in list(getattr(match, "domain_priority", []) or []):
                axes.extend(DOMAIN_EVENT_AXES.get(str(domain), []))
            for domain in list((getattr(match, "domain_projections", {}) or {}).keys()):
                axes.extend(DOMAIN_EVENT_AXES.get(str(domain), []))
            return list(dict.fromkeys(axis for axis in axes if axis in EVENT_AXIS_LABELS))[:7]

        def real_world_projection_payload(match, tags: list[str]) -> dict[str, object]:
            axes = event_axes_for_candidate(match, tags)
            domain_projections = dict(getattr(match, "domain_projections", {}) or {})
            primary_domains = list(getattr(match, "domain_priority", []) or [])[:4]
            return {
                "primary_axes": axes[:4],
                "axis_labels": [EVENT_AXIS_LABELS[axis] for axis in axes[:4]],
                "all_axes": axes,
                "all_axis_labels": [EVENT_AXIS_LABELS[axis] for axis in axes],
                "axis_statements": {
                    axis: AXIS_STATEMENTS[axis]
                    for axis in axes
                    if axis in AXIS_STATEMENTS
                },
                "primary_domains": primary_domains,
                "domain_projections": {
                    domain: domain_projections.get(domain, "")
                    for domain in primary_domains
                    if domain in domain_projections
                },
            }

        def feature_axis_impacts_payload(
            tags: object,
            domains: object,
            *,
            source: str,
            limit: int = 8,
        ) -> list[dict[str, object]]:
            tag_values = [str(tag) for tag in list(tags or []) if str(tag or "").strip()]
            domain_values = [str(domain) for domain in list(domains or []) if str(domain or "").strip()]
            life_axes = analysis.chart_structure.life_feature_profile.axes
            domain_axis_keys: set[str] = set()
            for domain in domain_values:
                for alias in GYEOKGUK_DOMAIN_ALIASES.get(domain, (domain,)):
                    domain_axis_keys.update(DOMAIN_AXIS_LINKS.get(alias, ()))
            impacts: list[dict[str, object]] = []
            seen: set[tuple[str, str]] = set()
            for tag in tag_values:
                effects = GYEOKGUK_CLASSICAL_AXIS_EFFECTS.get(tag, {})
                if not effects:
                    continue
                ranked = sorted(effects.items(), key=lambda item: abs(float(item[1])), reverse=True)
                for axis_key, raw_delta in ranked:
                    if axis_key not in life_axes:
                        continue
                    if domain_axis_keys and axis_key not in domain_axis_keys and abs(float(raw_delta)) < 3.0:
                        continue
                    key = (tag, axis_key)
                    if key in seen:
                        continue
                    seen.add(key)
                    axis = life_axes[axis_key]
                    delta = float(raw_delta)
                    impacts.append(
                        {
                            "source": source,
                            "classical_tag": tag,
                            "axis_key": axis.key,
                            "axis_label": axis.label,
                            "axis_category": axis.category,
                            "current_score": axis.score,
                            "current_strength_label": axis.strength_label,
                            "raw_score_delta": round(delta, 2),
                            "direction": "support" if delta >= 0 else "burden",
                            "domain_priority": domain_values,
                        }
                    )
                    if len(impacts) >= limit:
                        return impacts
            return impacts

        def classical_action_mechanics_payload(tags: list[str]) -> dict[str, object]:
            payload: dict[str, object] = {}
            for tag in tags:
                key = str(tag)
                mechanic = CLASSICAL_ACTION_MECHANICS.get(key)
                if not mechanic:
                    continue
                mechanic_text = CLASSICAL_ACTION_MECHANIC_TEXTS.get(key, {})
                payload[key] = {
                    "flow": str(mechanic.get("flow", "")),
                    "disease": str(mechanic.get("disease", "")),
                    "medicine": str(mechanic.get("medicine", "")),
                    "events": list(mechanic.get("events", []) or []),
                    "principle_text": str(mechanic_text.get("principle", "")),
                    "disease_text": str(mechanic_text.get("disease", "")),
                    "medicine_text": str(mechanic_text.get("medicine", "")),
                }
            return payload

        def ten_god_operation_face_payload(ten_god: str) -> dict[str, object]:
            key = str(ten_god)
            face = TEN_GOD_OPERATION_FACE.get(key, {})
            exact_profile = TEN_GOD_EXACT_ACTION_PROFILE.get(key, {})
            exact_profile_domains = (
                list(exact_profile.get("domains", []) or [])
                if isinstance(exact_profile, dict)
                else []
            )
            return {
                "ten_god": key,
                "label": TEN_GOD_LABELS.get(key, key),
                "action": str(face.get("action", "")),
                "result": str(face.get("result", "")),
                "risk": str(face.get("risk", "")),
                "timing": str(face.get("timing", "")),
                "exact_nuance": str(TEN_GOD_EXACT_NUANCE.get(key, "")),
                "exact_profile_domains": exact_profile_domains,
            }

        def operation_faces_payload(ten_gods: list[str]) -> list[dict[str, object]]:
            seen: set[str] = set()
            faces: list[dict[str, object]] = []
            for ten_god in ten_gods:
                key = str(ten_god)
                if not key or key in seen:
                    continue
                seen.add(key)
                faces.append(ten_god_operation_face_payload(key))
            return faces

        def pattern_center_bridge_payload(basis_codes: list[str]) -> dict[str, object]:
            payload = {
                "keys": [],
                "directions": [],
                "patterns": [],
            }
            for code in basis_codes:
                text = str(code)
                if text.startswith("gyeokguk_dual_pattern_center_bridge:"):
                    payload["keys"].append(text.split(":", 1)[1])
                elif text.startswith("gyeokguk_dual_pattern_center_bridge_direction:"):
                    payload["directions"].append(text.split(":", 1)[1])
                elif text.startswith("gyeokguk_dual_pattern_center_bridge_pattern:"):
                    payload["patterns"].append(text.split(":", 1)[1])
            return {
                key: list(dict.fromkeys(values))
                for key, values in payload.items()
                if values
            }

        def exact_profile_domain_basis_payload(basis_codes: list[str]) -> dict[str, object]:
            payload: dict[str, list[str]] = {
                "single": [],
                "first": [],
                "second": [],
                "all": [],
            }
            prefixes = {
                "single": "gyeokguk_action_exact_profile_domain:",
                "first": "gyeokguk_dual_first_exact_profile_domain:",
                "second": "gyeokguk_dual_second_exact_profile_domain:",
            }
            for code in basis_codes:
                text = str(code)
                for key, prefix in prefixes.items():
                    if text.startswith(prefix):
                        domain = text.split(":", 1)[1]
                        payload[key].append(domain)
                        payload["all"].append(domain)
            return {
                key: list(dict.fromkeys(values))
                for key, values in payload.items()
                if values
            }

        def relation_to_pattern_role_payload(ten_god: str, relation: str) -> dict[str, object]:
            relation_key = str(relation)
            relation_profiles = {
                "same_group": {
                    "role_code": "same_class_as_pattern_center",
                    "role_label": "격국 중심과 같은 계열",
                    "function": "격의 성격을 선명하게 하지만 과하면 편중을 만든다.",
                    "risk": "강하면 중심이 또렷해지고, 지나치면 같은 작용이 겹쳐 병이 된다.",
                },
                "actor_generates_pattern": {
                    "role_code": "source_of_pattern_center",
                    "role_label": "격국 중심을 생하는 근거",
                    "function": "격국 중심에 힘을 공급해 성격 조건을 받친다.",
                    "risk": "약하면 격을 받칠 근거가 부족하고, 과하면 생하는 쪽이 소모된다.",
                },
                "pattern_generates_actor": {
                    "role_code": "extension_from_pattern_center",
                    "role_label": "격국 중심에서 뻗어 나가는 작용",
                    "function": "격국 중심의 힘이 다른 영역으로 흘러 결과와 사건을 만든다.",
                    "risk": "과하면 격의 중심이 새고, 약하면 결과가 밖으로 나오지 못한다.",
                },
                "actor_controls_pattern": {
                    "role_code": "controller_or_breaker_of_pattern_center",
                    "role_label": "격국 중심을 제어하는 작용",
                    "function": "필요한 극이면 병을 다스리는 약이 되고, 불필요하면 격의 중심을 손상시킨다.",
                    "risk": "월령과 통근이 받치지 않으면 조절이 아니라 파격으로 기울 수 있다.",
                },
                "pattern_controls_actor": {
                    "role_code": "regulated_by_pattern_center",
                    "role_label": "격국 중심의 제어를 받는 작용",
                    "function": "격국 중심이 과한 작용을 묶어 질서를 세운다.",
                    "risk": "대상이 약하면 제어가 억압으로 바뀌고, 과하면 통제가 어려워진다.",
                },
            }
            profile = relation_profiles.get(
                relation_key,
                {
                    "role_code": "conditional_relation_to_pattern_center",
                    "role_label": "격국 중심과 조건부로 얽힌 작용",
                    "function": "월령, 위치, 투출, 통근에 따라 작용 방향이 갈린다.",
                    "risk": "한 가지 태그만으로 길흉을 확정하면 판단이 얕아진다.",
                },
            )
            return {
                "ten_god": str(ten_god),
                "label": TEN_GOD_LABELS.get(str(ten_god), str(ten_god)),
                "relation_to_pattern": relation_key,
                **profile,
            }

        def dual_pair_function_payload(match, classical_tags: list[str], bridge_payload: dict[str, object]) -> dict[str, object]:
            tags = {str(tag) for tag in classical_tags}
            control_tags = {
                "siksin_jesal",
                "sanggwan_gyeongwan",
                "jaegeukin",
                "bigeop_jaengjae",
                "inseong_dosik",
                "siksang_controls_gwanseong",
                "wealth_controls_resource",
                "bigeop_controls_wealth",
                "inseong_controls_output",
                "gwanseong_controls_bigeop",
            }
            generation_tags = {
                "siksang_saengjae",
                "jaesaenggwan",
                "jaesaengsal",
                "gwanin_sangsaeng",
                "salin_sangsaeng",
                "jaeseong_generates_gwanseong",
                "gwanseong_generates_inseong",
                "bigeop_generates_siksang",
                "inseong_generates_bigeop",
            }
            overload_tags = {
                "gwansal_overload",
                "gwansal_honhap",
                "inbi_overload",
                "siksang_overload",
                "jaeda_sinyak_risk",
            }
            function_profiles = {
                "constructive_chain": (
                    "pattern_formation_expansion",
                    "성격 조건을 넓히는 조합",
                    "두 십신이 원인과 결론으로 이어져 격국이 현실 사건으로 뻗는다.",
                ),
                "supportive_chain": (
                    "pattern_support",
                    "성격을 보조하는 조합",
                    "두 십신이 함께 격국 중심을 받쳐 성립 조건을 보강한다.",
                ),
                "medicine_chain": (
                    "disease_medicine_regulation",
                    "병을 다스리는 조합",
                    "한쪽의 과한 작용을 다른 쪽이 제어하여 약으로 쓴다.",
                ),
                "mediated_tension_chain": (
                    "requires_pattern_center_mediation",
                    "격국 중심의 매개가 필요한 조합",
                    "두 십신은 직접 부딪히지만 월령의 중심을 거치면 사건 구조가 성립한다.",
                ),
                "conditional_chain": (
                    "conditional_by_force_and_position",
                    "강약과 위치로 갈리는 조합",
                    "같은 조합이라도 투출, 통근, 지장간, 합충형파해에 따라 길흉이 갈린다.",
                ),
                "risk_chain": (
                    "pattern_break_risk",
                    "파격 위험이 있는 조합",
                    "한쪽 작용이 격국 중심을 흔들어 손상, 충돌, 부담으로 기울 수 있다.",
                ),
                "compounded_burden_chain": (
                    "burden_amplification",
                    "부담이 겹치는 조합",
                    "두 십신이 함께 병으로 작동하면 파격 가능성이 커진다.",
                ),
                "mixed_chain": (
                    "mixed_operation",
                    "조건부 혼합 조합",
                    "좋고 나쁨이 고정되지 않고 월령과 실제 힘의 배치로 다시 판정한다.",
                ),
            }
            function_code, function_label, function_summary = function_profiles.get(
                str(match.chain_grade),
                (
                    "mixed_operation",
                    "조건부 혼합 조합",
                    "좋고 나쁨이 고정되지 않고 월령과 실제 힘의 배치로 다시 판정한다.",
                ),
            )
            if str(match.sequence_key) == "same_role_amplification":
                function_code = "same_group_amplification"
                function_label = "동류 편중 조합"
                function_summary = "같은 계열의 장점과 병이 함께 커지므로 강약 판정이 중요하다."

            if str(match.first_to_second_relation) == "first_controls_second":
                controller = str(match.first_ten_god)
                controlled = str(match.second_ten_god)
            elif str(match.first_to_second_relation) == "second_controls_first":
                controller = str(match.second_ten_god)
                controlled = str(match.first_ten_god)
            else:
                controller = ""
                controlled = ""

            return {
                "function_code": function_code,
                "function_label": function_label,
                "function_summary": function_summary,
                "has_generation_axis": bool(tags & generation_tags),
                "has_control_axis": bool(tags & control_tags),
                "has_overload_axis": bool(tags & overload_tags),
                "control_axis": {
                    "controller": controller,
                    "controller_label": TEN_GOD_LABELS.get(controller, controller) if controller else "",
                    "controlled": controlled,
                    "controlled_label": TEN_GOD_LABELS.get(controlled, controlled) if controlled else "",
                    "classical_tags": sorted(tags & control_tags),
                },
                "generation_axis": {
                    "classical_tags": sorted(tags & generation_tags),
                },
                "overload_axis": {
                    "classical_tags": sorted(tags & overload_tags),
                },
                "pattern_center_mediation": bridge_payload,
            }

        def dual_operation_assessment_payload(match, classical_tags: list[str], bridge_payload: dict[str, object]) -> dict[str, object]:
            first_role = relation_to_pattern_role_payload(
                str(match.first_ten_god),
                str(match.first_relation_to_pattern),
            )
            second_role = relation_to_pattern_role_payload(
                str(match.second_ten_god),
                str(match.second_relation_to_pattern),
            )
            primary_actor = str(match.primary_actor)
            secondary_actor = str(match.secondary_actor)
            return {
                "pattern_center": str(match.pattern_ten_god),
                "pattern_center_label": TEN_GOD_LABELS.get(str(match.pattern_ten_god), str(match.pattern_ten_god)),
                "first_role_in_pattern": first_role,
                "second_role_in_pattern": second_role,
                "first_to_second_relation": str(match.first_to_second_relation),
                "pair_function": dual_pair_function_payload(match, classical_tags, bridge_payload),
                "component_single_actions": {
                    "first_classical_tags": list(
                        getattr(match, "first_single_classical_action_tags", []) or extract_classical_action_tags(
                            "gyeokguk_dual_first_single_classical_action:",
                            match.basis_codes,
                        )
                    ),
                    "second_classical_tags": list(
                        getattr(match, "second_single_classical_action_tags", []) or extract_classical_action_tags(
                            "gyeokguk_dual_second_single_classical_action:",
                            match.basis_codes,
                        )
                    ),
                    "pair_classical_tags": list(classical_tags),
                },
                "primary_actor": primary_actor,
                "primary_actor_label": TEN_GOD_LABELS.get(primary_actor, primary_actor),
                "secondary_actor": secondary_actor,
                "secondary_actor_label": TEN_GOD_LABELS.get(secondary_actor, secondary_actor),
                "actor_hierarchy_logic": str(match.actor_hierarchy_logic),
                "pattern_combination_state": str(match.pattern_combination_state),
                "combination_resolution_state": str(match.combination_resolution_state),
                "combination_resolution_logic": str(match.combination_resolution_logic),
                "chain_grade": str(match.chain_grade),
                "sequence_key": str(match.sequence_key),
                "exact_pair_axis": {
                    "exact_pair_key": str(match.exact_pair_key),
                    "exact_pair_category": str(match.exact_pair_category),
                    "exact_pair_name": str(match.exact_pair_name),
                    "exact_pair_effect": str(match.exact_pair_effect),
                    "exact_pair_risk": str(match.exact_pair_risk),
                    "exact_pair_timing": str(match.exact_pair_timing),
                },
                "disease_medicine_axis": {
                    "disease_medicine_logic": str(match.disease_medicine_logic),
                    "pattern_combination_state": str(match.pattern_combination_state),
                    "combination_resolution_state": str(match.combination_resolution_state),
                    "combination_resolution_logic": str(match.combination_resolution_logic),
                    "chain_nature": str(match.chain_nature),
                    "actor_hierarchy_logic": str(match.actor_hierarchy_logic),
                },
                "interaction_judgment": dict(match.interaction_judgment),
                "visibility_axis": dict(match.visibility_interaction),
                "timing_order": {
                    "first_then_second": str(match.first_then_second_activation),
                    "second_then_first": str(match.second_then_first_activation),
                    "timing_activation": str(match.timing_activation),
                    "activation_order_profile": dict(getattr(match, "activation_order_profile", {}) or {}),
                    "event_manifestations": dict(match.event_manifestations),
                },
                "domain_axis": {
                    "domain_priority": list(match.domain_priority),
                    "domain_projections": dict(match.domain_projections),
                    "event_manifestations": dict(match.event_manifestations),
                },
                "context_axis": {
                    "context_judgment_state": str(match.context_judgment_state),
                    "context_judgment_summary": str(match.context_judgment_summary),
                    "context_judgment_path": list(match.context_judgment_path),
                },
            }

        def single_operation_function_payload(match, classical_tags: list[str]) -> dict[str, object]:
            role_profiles = {
                "core": (
                    "pattern_center",
                    "격국 중심",
                    "격국의 중심 작용을 직접 강화한다.",
                    "지나치면 중심이 편중되어 병이 된다.",
                ),
                "core_overload": (
                    "pattern_center_overload",
                    "중심 과다",
                    "격국 중심과 같은 힘이 겹쳐 작용한다.",
                    "과하면 장점이 병으로 바뀌어 균형을 잃는다.",
                ),
                "source": (
                    "source_support",
                    "근원 보조",
                    "격국 중심을 생하거나 받쳐 성립 근거를 만든다.",
                    "약하면 격을 받칠 근거가 부족하다.",
                ),
                "support": (
                    "pattern_support",
                    "성격 보조",
                    "격국의 좋은 성립 조건을 보강한다.",
                    "과하면 보조 작용이 중심을 대신하려 한다.",
                ),
                "conditioned_support": (
                    "conditional_support",
                    "조건부 성격",
                    "월령, 강약, 위치가 맞을 때 격의 성립을 돕는다.",
                    "조건이 맞지 않으면 장점이 현실 사건으로 굳지 않는다.",
                ),
                "regulator": (
                    "disease_medicine_regulator",
                    "병약 조절",
                    "과한 작용을 제어하거나 격의 병을 약으로 바꾼다.",
                    "제어 대상이 약하면 조절이 손상으로 바뀐다.",
                ),
                "strong_regulator": (
                    "strong_regulation",
                    "강한 조절",
                    "격국의 부담을 강하게 정리하고 질서를 세운다.",
                    "과하면 통제가 지나쳐 생동감이 줄어든다.",
                ),
                "regulator_or_breaker": (
                    "regulator_or_breaker",
                    "조절·파격 경계",
                    "필요하면 약이 되지만 불필요하면 격국 중심을 친다.",
                    "월령과 통근을 보지 않으면 길흉 판단이 뒤집힌다.",
                ),
                "breaker_or_medicine": (
                    "breaker_or_medicine",
                    "파격·약성 경계",
                    "격을 치는 작용이지만 과한 중심을 덜어 내면 약이 된다.",
                    "중심이 약한데 들어오면 파격으로 기운다.",
                ),
                "breaker": (
                    "pattern_breaker",
                    "파격 위험",
                    "격국 중심을 직접 흔들거나 제어한다.",
                    "강하면 손상, 충돌, 명분 훼손으로 나타난다.",
                ),
                "danger": (
                    "danger_pressure",
                    "강한 파격 위험",
                    "격국의 핵심 조건을 거칠게 압박한다.",
                    "대운·세운에서 발동되면 사건성이 커진다.",
                ),
                "burden": (
                    "pattern_burden",
                    "부담 작용",
                    "격국 성립에 부담을 더한다.",
                    "해소하는 약이 없으면 결핍보다 부담이 먼저 드러난다.",
                ),
                "mixed": (
                    "mixed_operation",
                    "혼합 작용",
                    "좋고 나쁨이 고정되지 않고 조건에 따라 갈린다.",
                    "투출, 통근, 위치, 합충형파해를 함께 보아야 한다.",
                ),
            }
            function_code, function_label, function_summary, risk_summary = role_profiles.get(
                str(match.role_grade),
                (
                    "conditional_operation",
                    "조건부 작용",
                    "월령, 격국, 실제 힘의 배치에 따라 작용 방향이 갈린다.",
                    "한 가지 십신명만으로 판단하면 실제 사건을 놓친다.",
                ),
            )
            return {
                "function_code": function_code,
                "function_label": function_label,
                "function_summary": function_summary,
                "risk_summary": risk_summary,
                "role_grade": str(match.role_grade),
                "pattern_effect_state": str(match.pattern_effect_state),
                "action_nature": str(match.action_nature),
                "classical_tags": list(classical_tags),
                "has_critical_lens": any(
                    str(code).startswith("gyeokguk_single_critical_action:")
                    for code in list(getattr(match, "basis_codes", []) or [])
                ),
            }

        def single_operation_assessment_payload(match, classical_tags: list[str]) -> dict[str, object]:
            acting_role = relation_to_pattern_role_payload(
                str(match.acting_ten_god),
                str(match.relation_to_pattern),
            )
            acting_ten_god = str(match.acting_ten_god)
            pattern_center = str(profile.primary_ten_god)
            return {
                "pattern_center": pattern_center,
                "pattern_center_label": TEN_GOD_LABELS.get(pattern_center, pattern_center),
                "acting_operation_face": ten_god_operation_face_payload(acting_ten_god),
                "pattern_center_operation_face": ten_god_operation_face_payload(pattern_center),
                "acting_role_in_pattern": acting_role,
                "single_function": single_operation_function_payload(match, classical_tags),
                "role_axis": {
                    "role_grade": str(match.role_grade),
                    "action_nature": str(match.action_nature),
                    "center_effect": str(match.center_effect),
                    "role_in_pattern_logic": str(match.role_in_pattern_logic),
                },
                "disease_medicine_axis": {
                    "excess_disease": str(match.excess_disease),
                    "deficiency_gap": str(match.deficiency_gap),
                    "pattern_effect_state": str(match.pattern_effect_state),
                    "pattern_resolution_state": str(match.pattern_resolution_state),
                    "pattern_resolution_logic": str(match.pattern_resolution_logic),
                },
                "visibility_axis": {
                    "protrusion_effect": str(match.protrusion_effect),
                    "hidden_effect": str(match.hidden_effect),
                    "rooting_effect": str(match.rooting_effect),
                    "unrooted_effect": str(match.unrooted_effect),
                },
                "timing_axis": {
                    "timing_activation": str(match.timing_activation),
                    "timing_hits": single_action_timing_hits(match),
                    "event_manifestations": dict(match.event_manifestations),
                },
                "domain_axis": {
                    "domain_priority": list(match.domain_priority),
                    "domain_projections": dict(match.domain_projections),
                    "event_manifestations": dict(match.event_manifestations),
                },
                "context_axis": {
                    "context_judgment_state": str(match.context_judgment_state),
                    "context_judgment_summary": str(match.context_judgment_summary),
                    "context_judgment_path": list(match.context_judgment_path),
                },
            }

        def single_center_candidate(match) -> dict[str, object]:
            timing_hits = single_action_timing_hits(match, limit=1)
            timing_score = int(timing_hits[0]["activation_score"]) if timing_hits else 0
            tags = match_classical_action_tags(match, "gyeokguk_single_classical_action:")
            dedupe_tags = center_dedupe_tags(tags)
            center_timing_score = center_flow_activation_score(timing_score)
            basis = single_selection_basis(match, tags, center_timing_score)
            raw_basis = single_selection_basis(match, tags, timing_score)
            score = int(
                round(
                    match.presence_score * 0.34
                    + basis_attention_total(basis) * 0.68
                    + context_attention_weight(getattr(match, "context_judgment_state", ""))
                    + center_specificity_adjustment(tags)
                )
            )
            reasons = center_reason_parts(
                month_fit_state=match.month_fit_state,
                context_state=getattr(match, "context_judgment_state", ""),
                tags=tags,
                timing_score=timing_score,
                relation_text="단일 십신이 격국 중심을 직접 건드림",
            )
            selection_role = selection_role_for_candidate("single", match, tags)
            ten_god_label = TEN_GOD_LABELS.get(match.acting_ten_god, match.acting_ten_god)
            action_title = (
                str(match.action_nature)
                if str(match.action_nature).startswith(str(ten_god_label))
                else f"{ten_god_label} {match.action_nature}"
            )
            return {
                "source": "single",
                "match": match,
                "score": score,
                "selection_role": selection_role,
                "tags": tags,
                "component_tags": [],
                "dedupe_tags": sorted(dedupe_tags),
                "signature": tuple(tags[:2] or [match.action_key]),
                "title": action_title,
                "reason": reasons,
                "timing_score": timing_score,
                "center_timing_score": center_timing_score,
                "selection_basis": basis,
                "raw_selection_basis": raw_basis,
            }

        def dual_center_candidate(match) -> dict[str, object]:
            timing_hits = dual_action_timing_hits(match, limit=1)
            timing_score = int(timing_hits[0]["activation_score"]) if timing_hits else 0
            tags = match_classical_action_tags(match, "gyeokguk_dual_classical_action:")
            component_tags = match_component_classical_action_tags(match)
            dedupe_tags = center_dedupe_tags([*tags, *component_tags])
            center_timing_score = center_flow_activation_score(timing_score)
            basis = dual_selection_basis(match, tags, center_timing_score)
            raw_basis = dual_selection_basis(match, tags, timing_score)
            score = int(
                round(
                    match.presence_score * 0.32
                    + basis_attention_total(basis) * 0.7
                    + context_attention_weight(getattr(match, "context_judgment_state", ""))
                    + center_specificity_adjustment(tags)
                )
            )
            reasons = center_reason_parts(
                month_fit_state=match.month_fit_state,
                context_state=getattr(match, "context_judgment_state", ""),
                tags=tags,
                timing_score=timing_score,
                relation_text="두 십신의 생극 관계가 하나의 사건 구조를 이룸",
            )
            selection_role = selection_role_for_candidate("dual", match, tags)
            return {
                "source": "dual",
                "match": match,
                "score": score,
                "selection_role": selection_role,
                "tags": tags,
                "component_tags": component_tags,
                "dedupe_tags": sorted(dedupe_tags),
                "signature": dual_pair_center_signature(match),
                "title": match.exact_pair_name,
                "reason": reasons,
                "timing_score": timing_score,
                "center_timing_score": center_timing_score,
                "selection_basis": basis,
                "raw_selection_basis": raw_basis,
            }

        def all_center_core_action_candidates() -> list[dict[str, object]]:
            candidates = [
                *(single_center_candidate(match) for match in profile.ten_god_action_matches),
                *(dual_center_candidate(match) for match in profile.dual_ten_god_action_matches),
            ]
            candidates.sort(
                key=lambda item: (
                    -int(item["score"]),
                    0 if item["source"] == "dual" else 1,
                    str(item["title"]),
                )
            )
            return candidates

        def center_core_action_candidates(limit: int = 3) -> list[dict[str, object]]:
            candidates = all_center_core_action_candidates()

            def preserve_single_pattern_action(selected_items: list[dict[str, object]]) -> list[dict[str, object]]:
                if limit <= 1 or any(item["source"] == "single" for item in selected_items):
                    return selected_items
                if not selected_items:
                    return selected_items

                selected_tags = {
                    str(tag)
                    for item in selected_items
                    for tag in list(item.get("dedupe_tags", []) or [])
                }
                selected_signatures = {tuple(item["signature"]) for item in selected_items}
                lowest_selected_score = min(int(item["score"]) for item in selected_items)
                fallback_single: dict[str, object] | None = None
                for candidate in candidates:
                    if candidate["source"] != "single":
                        continue
                    candidate_tags = {str(tag) for tag in list(candidate.get("dedupe_tags", []) or [])}
                    candidate_signature = tuple(candidate["signature"])
                    if candidate_signature in selected_signatures:
                        continue
                    candidate_relevance = (
                        candidate.get("selection_basis", {})
                        .get("pattern_center_relevance", {})
                        if isinstance(candidate.get("selection_basis"), dict)
                        else {}
                    )
                    is_core_single = (
                        isinstance(candidate_relevance, dict)
                        and (
                            bool(candidate_relevance.get("direct_center_actor"))
                            or bool(candidate_relevance.get("same_group_as_center"))
                        )
                    )
                    if is_core_single and int(candidate["score"]) >= lowest_selected_score - 70:
                        if fallback_single is None or int(candidate["score"]) > int(fallback_single["score"]):
                            fallback_single = candidate
                    if not is_core_single:
                        continue
                    if center_candidate_repeats_existing(candidate_tags, selected_tags):
                        continue
                    if int(candidate["score"]) < lowest_selected_score - 35:
                        continue
                    adjusted = list(selected_items)
                    adjusted[-1] = candidate
                    adjusted.sort(
                        key=lambda item: (
                            -int(item["score"]),
                            0 if item["source"] == "single" else 1,
                            str(item["title"]),
                        )
                    )
                    return adjusted[:limit]
                if fallback_single is not None:
                    adjusted = list(selected_items)
                    fallback = dict(fallback_single)
                    fallback["selection_adjusted_score"] = int(fallback["score"])
                    fallback["selection_overlap_penalty"] = 0
                    adjusted[-1] = fallback
                    adjusted.sort(
                        key=lambda item: (
                            -int(item["score"]),
                            0 if item["source"] == "dual" else 1,
                            str(item["title"]),
                        )
                    )
                    return adjusted[:limit]
                return selected_items

            def candidate_pattern_relevance(candidate: dict[str, object]) -> dict[str, object]:
                basis = candidate.get("selection_basis", {})
                if not isinstance(basis, dict):
                    return {}
                relevance = basis.get("pattern_center_relevance", {})
                return relevance if isinstance(relevance, dict) else {}

            def candidate_selection_role_code(candidate: dict[str, object]) -> str:
                role = candidate.get("selection_role", {})
                if not isinstance(role, dict):
                    return ""
                return str(role.get("code", "") or "")

            def candidate_has_direct_center(candidate: dict[str, object]) -> bool:
                relevance = candidate_pattern_relevance(candidate)
                return bool(relevance.get("direct_center_actor")) or bool(relevance.get("same_group_as_center"))

            def candidate_has_pattern_bridge(candidate: dict[str, object]) -> bool:
                relevance = candidate_pattern_relevance(candidate)
                return bool(relevance.get("pattern_center_bridge"))

            def candidate_is_primary_center_flow(candidate: dict[str, object]) -> bool:
                role_code = candidate_selection_role_code(candidate)
                tags = {str(tag) for tag in list(candidate.get("tags", []) or [])}
                return (
                    candidate_has_direct_center(candidate)
                    and role_code == "primary"
                    and bool(tags & SUPPORT_CLASSICAL_ACTION_TAGS)
                )

            def candidate_is_bridge_medicine(candidate: dict[str, object]) -> bool:
                basis = candidate.get("selection_basis", {})
                operation_depth = (
                    basis.get("ten_god_operation_depth", {})
                    if isinstance(basis, dict)
                    else {}
                )
                return (
                    candidate_has_pattern_bridge(candidate)
                    and candidate_selection_role_code(candidate) == "primary"
                    and isinstance(operation_depth, dict)
                    and str(operation_depth.get("grade_state", "")) == "medicine_chain"
                )

            def candidate_is_bridge_caution(candidate: dict[str, object]) -> bool:
                return candidate_has_pattern_bridge(candidate) and candidate_selection_role_code(candidate) == "caution"

            def candidate_is_single_center(candidate: dict[str, object]) -> bool:
                return str(candidate.get("source", "")) == "single" and candidate_has_direct_center(candidate)

            def candidate_with_selection_defaults(candidate: dict[str, object]) -> dict[str, object]:
                item = dict(candidate)
                item.setdefault("selection_adjusted_score", int(item["score"]))
                item.setdefault("selection_overlap_penalty", 0)
                return item

            def best_candidate(predicate) -> dict[str, object] | None:
                matches = [candidate for candidate in candidates if predicate(candidate)]
                if not matches:
                    return None
                matches.sort(
                    key=lambda item: (
                        -int(item["score"]),
                        0 if item["source"] == "dual" else 1,
                        str(item["title"]),
                    )
                )
                return candidate_with_selection_defaults(matches[0])

            def balance_center_action_roles(selected_items: list[dict[str, object]]) -> list[dict[str, object]]:
                if limit < 3:
                    return selected_items
                balanced: list[dict[str, object]] = []
                seen_signatures_for_balance: set[tuple[object, ...]] = set()
                seen_raw_tags_for_balance: set[str] = set()

                def add(candidate: dict[str, object] | None) -> None:
                    if candidate is None:
                        return
                    signature = tuple(candidate["signature"])
                    if signature in seen_signatures_for_balance:
                        return
                    raw_tags = {str(tag) for tag in list(candidate.get("tags", []) or [])}
                    if raw_tags:
                        existing_tag_sets = [
                            {str(tag) for tag in list(item.get("tags", []) or [])}
                            for item in balanced
                        ]
                        if any(raw_tags <= existing_tags for existing_tags in existing_tag_sets if existing_tags):
                            return
                        if any(existing_tags < raw_tags for existing_tags in existing_tag_sets if existing_tags):
                            balanced[:] = [
                                item
                                for item in balanced
                                if not (
                                    {str(tag) for tag in list(item.get("tags", []) or [])}
                                    and {str(tag) for tag in list(item.get("tags", []) or [])} < raw_tags
                                )
                            ]
                            seen_signatures_for_balance.clear()
                            seen_signatures_for_balance.update(tuple(item["signature"]) for item in balanced)
                            seen_raw_tags_for_balance.clear()
                            seen_raw_tags_for_balance.update(
                                str(tag)
                                for item in balanced
                                for tag in list(item.get("tags", []) or [])
                            )
                    seen_signatures_for_balance.add(signature)
                    seen_raw_tags_for_balance.update(raw_tags)
                    balanced.append(candidate_with_selection_defaults(candidate))

                add(best_candidate(candidate_is_bridge_medicine))
                add(best_candidate(candidate_is_primary_center_flow))
                add(best_candidate(candidate_is_bridge_caution))
                add(best_candidate(candidate_is_single_center))

                for candidate in [*selected_items, *candidates]:
                    if len(balanced) >= limit:
                        break
                    add(candidate)

                return balanced[:limit] if balanced else selected_items

            def overlap_penalty(candidate_tags: set[str], seen_tags: set[str], selected_count: int) -> int:
                if not candidate_tags:
                    return 12 if selected_count else 0
                overlap = candidate_tags & seen_tags
                if not overlap:
                    return 0
                new_tags = candidate_tags - seen_tags
                if not new_tags:
                    return 70
                return min(54, len(overlap) * 16)

            selected: list[dict[str, object]] = []
            seen_tags: set[str] = set()
            seen_signatures: set[tuple[object, ...]] = set()
            remaining = list(candidates)
            while remaining and len(selected) < limit:
                ranked: list[tuple[int, int, int, str, dict[str, object], int]] = []
                for candidate in remaining:
                    signature = tuple(candidate["signature"])
                    if signature in seen_signatures:
                        continue
                    tags = {str(tag) for tag in list(candidate.get("dedupe_tags", []) or [])}
                    penalty = overlap_penalty(tags, seen_tags, len(selected))
                    adjusted_score = int(candidate["score"]) - penalty
                    ranked.append(
                        (
                            adjusted_score,
                            int(candidate["score"]),
                            0 if candidate["source"] == "dual" else 1,
                            str(candidate["title"]),
                            candidate,
                            penalty,
                        )
                    )
                if not ranked:
                    break
                ranked.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
                selected_candidate = dict(ranked[0][4])
                selected_candidate["selection_adjusted_score"] = int(ranked[0][0])
                selected_candidate["selection_overlap_penalty"] = int(ranked[0][5])
                selected.append(selected_candidate)
                seen_signatures.add(tuple(selected_candidate["signature"]))
                seen_tags.update(str(tag) for tag in list(selected_candidate.get("dedupe_tags", []) or []))
                selected_signature = tuple(selected_candidate["signature"])
                remaining = [candidate for candidate in remaining if tuple(candidate["signature"]) != selected_signature]
            result = balance_center_action_roles(preserve_single_pattern_action(selected))
            result.sort(
                key=lambda item: (
                    -int(item["score"]),
                    0 if item["source"] == "dual" else 1,
                    str(item["title"]),
                )
            )
            return result

        def flow_activated_core_action_candidates(limit: int = 5) -> list[dict[str, object]]:
            candidates = [
                candidate
                for candidate in all_center_core_action_candidates()
                if int(candidate.get("timing_score") or 0) > 0
            ]
            candidates.sort(
                key=lambda item: (
                    -int(item.get("timing_score") or 0),
                    -int(item.get("score") or 0),
                    0 if item.get("source") == "dual" else 1,
                    str(item.get("title") or ""),
                )
            )
            selected: list[dict[str, object]] = []
            seen_signatures: set[tuple[object, ...]] = set()
            for candidate in candidates:
                signature = (
                    str(candidate.get("source") or ""),
                    *tuple(candidate.get("signature") or ()),
                )
                if signature in seen_signatures:
                    continue
                seen_signatures.add(signature)
                selected.append(candidate)
                if len(selected) >= limit:
                    break
            return selected

        def candidate_payload(candidate) -> dict[str, object]:
            return {
                "pattern": candidate.pattern,
                "source_ten_god": candidate.source_ten_god,
                "source_ten_god_label": TEN_GOD_LABELS.get(candidate.source_ten_god, candidate.source_ten_god),
                "source_group": candidate.source_group,
                "source_stem": candidate.source_stem,
                "source_element": candidate.source_element,
                "source_element_label": ELEMENT_LABELS.get(candidate.source_element, candidate.source_element),
                "source_weight": candidate.source_weight,
                "source_priority": candidate.source_priority,
                "source_phase": candidate.source_phase,
                "protruded": candidate.protruded,
                "protrusion_positions": list(candidate.protrusion_positions),
                "rooted": candidate.rooted,
                "root_positions": list(candidate.root_positions),
                "month_authority": candidate.month_authority,
                "clarity_state": candidate.clarity_state,
                "formation_state": candidate.formation_state,
                "support_roles": list(candidate.support_roles),
                "burden_roles": list(candidate.burden_roles),
                "favorable_elements": list(candidate.favorable_elements),
                "unfavorable_elements": list(candidate.unfavorable_elements),
                "score": candidate.score,
                "confidence": candidate.confidence,
                "basis_codes": list(candidate.basis_codes),
                "counter_signals": list(candidate.counter_signals),
            }

        def action_match_payload(match) -> dict[str, object]:
            classical_tags = match_classical_action_tags(match, "gyeokguk_single_classical_action:")
            operation_assessment = single_operation_assessment_payload(match, classical_tags)
            return {
                "rule_key": match.rule_key,
                "pattern": match.pattern,
                "acting_ten_god": match.acting_ten_god,
                "acting_ten_god_label": TEN_GOD_LABELS.get(match.acting_ten_god, match.acting_ten_god),
                "acting_group": match.acting_group,
                "relation_to_pattern": match.relation_to_pattern,
                "action_key": match.action_key,
                "action_nature": match.action_nature,
                "role_grade": match.role_grade,
                "center_effect": match.center_effect,
                "role_in_pattern_logic": match.role_in_pattern_logic,
                "presence_state": match.presence_state,
                "presence_score": match.presence_score,
                "month_fit_state": match.month_fit_state,
                "verdict": match.verdict,
                "functional_role": match.functional_role,
                "functional_role_label": match.functional_role_label,
                "pattern_effect_state": match.pattern_effect_state,
                "pattern_resolution_state": match.pattern_resolution_state,
                "pattern_resolution_logic": match.pattern_resolution_logic,
                "activation_context": match.activation_context,
                "context_judgment_state": match.context_judgment_state,
                "context_judgment_summary": match.context_judgment_summary,
                "context_judgment_path": list(match.context_judgment_path),
                "classical_action_tags": classical_tags,
                "mechanic_codes": extract_mechanic_codes("gyeokguk_single_mechanic:", match.basis_codes),
                "day_master_strength_context": match.day_master_strength_context,
                "climate_context": match.climate_context,
                "position_context": dict(match.position_context),
                "branch_relation_context": dict(match.branch_relation_context),
                "excess_disease": match.excess_disease,
                "deficiency_gap": match.deficiency_gap,
                "protrusion_effect": match.protrusion_effect,
                "hidden_effect": match.hidden_effect,
                "rooting_effect": match.rooting_effect,
                "unrooted_effect": match.unrooted_effect,
                "timing_activation": match.timing_activation,
                "timing_hits": single_action_timing_hits(match),
                "event_manifestations": dict(match.event_manifestations),
                "domain_priority": list(match.domain_priority),
                "expert_summary": match.expert_summary,
                "domain_projections": dict(match.domain_projections),
                "classical_action_mechanics": classical_action_mechanics_payload(classical_tags),
                "operation_faces": operation_faces_payload([match.acting_ten_god]),
                "exact_profile_domain_basis": exact_profile_domain_basis_payload(list(match.basis_codes)),
                "single_operation_assessment": operation_assessment,
                "judgment_order": list(match.judgment_order),
                "basis_codes": list(match.basis_codes),
                "counter_signals": list(match.counter_signals),
            }

        def dual_action_match_payload(match) -> dict[str, object]:
            classical_tags = match_classical_action_tags(match, "gyeokguk_dual_classical_action:")
            bridge_payload = pattern_center_bridge_payload(list(match.basis_codes))
            operation_assessment = dual_operation_assessment_payload(match, classical_tags, bridge_payload)
            return {
                "rule_key": match.rule_key,
                "pattern": match.pattern,
                "pattern_ten_god": match.pattern_ten_god,
                "pattern_ten_god_label": TEN_GOD_LABELS.get(match.pattern_ten_god, match.pattern_ten_god),
                "pattern_group": match.pattern_group,
                "first_ten_god": match.first_ten_god,
                "first_ten_god_label": TEN_GOD_LABELS.get(match.first_ten_god, match.first_ten_god),
                "first_group": match.first_group,
                "second_ten_god": match.second_ten_god,
                "second_ten_god_label": TEN_GOD_LABELS.get(match.second_ten_god, match.second_ten_god),
                "second_group": match.second_group,
                "first_relation_to_pattern": match.first_relation_to_pattern,
                "second_relation_to_pattern": match.second_relation_to_pattern,
                "first_to_second_relation": match.first_to_second_relation,
                "pattern_center_bridge_profile": dict(match.pattern_center_bridge),
                "sequence_key": match.sequence_key,
                "chain_grade": match.chain_grade,
                "chain_nature": match.chain_nature,
                "presence_state": match.presence_state,
                "presence_score": match.presence_score,
                "month_fit_state": match.month_fit_state,
                "verdict": match.verdict,
                "functional_role": match.functional_role,
                "functional_role_label": match.functional_role_label,
                "pattern_combination_state": match.pattern_combination_state,
                "combination_resolution_state": match.combination_resolution_state,
                "combination_resolution_logic": match.combination_resolution_logic,
                "exact_pair_key": match.exact_pair_key,
                "exact_pair_category": match.exact_pair_category,
                "exact_pair_name": match.exact_pair_name,
                "exact_pair_effect": match.exact_pair_effect,
                "exact_pair_risk": match.exact_pair_risk,
                "exact_pair_timing": match.exact_pair_timing,
                "activation_context": match.activation_context,
                "context_judgment_state": match.context_judgment_state,
                "context_judgment_summary": match.context_judgment_summary,
                "context_judgment_path": list(match.context_judgment_path),
                "classical_action_tags": classical_tags,
                "mechanic_codes": extract_mechanic_codes("gyeokguk_dual_mechanic:", match.basis_codes),
                "day_master_strength_context": match.day_master_strength_context,
                "climate_context": match.climate_context,
                "position_context": dict(match.position_context),
                "branch_relation_context": dict(match.branch_relation_context),
                "primary_actor": match.primary_actor,
                "secondary_actor": match.secondary_actor,
                "actor_hierarchy_logic": match.actor_hierarchy_logic,
                "disease_medicine_logic": match.disease_medicine_logic,
                "first_then_second_activation": match.first_then_second_activation,
                "second_then_first_activation": match.second_then_first_activation,
                "timing_activation": match.timing_activation,
                "activation_order_profile": dict(match.activation_order_profile),
                "timing_hits": dual_action_timing_hits(match),
                "event_manifestations": dict(match.event_manifestations),
                "interaction_judgment": dict(match.interaction_judgment),
                "visibility_interaction": dict(match.visibility_interaction),
                "domain_priority": list(match.domain_priority),
                "expert_summary": match.expert_summary,
                "domain_projections": dict(match.domain_projections),
                "classical_action_mechanics": classical_action_mechanics_payload(classical_tags),
                "operation_faces": operation_faces_payload([match.first_ten_god, match.second_ten_god]),
                "exact_profile_domain_basis": exact_profile_domain_basis_payload(list(match.basis_codes)),
                "pattern_center_bridge": {
                    **bridge_payload,
                    **({"profile": dict(match.pattern_center_bridge)} if getattr(match, "pattern_center_bridge", {}) else {}),
                },
                "dual_operation_assessment": operation_assessment,
                "judgment_order": list(match.judgment_order),
                "basis_codes": list(match.basis_codes),
                "counter_signals": list(match.counter_signals),
            }

        def basis_step_payload(basis: dict[str, object], raw_basis: dict[str, object], key: str) -> dict[str, object]:
            item = basis.get(key)
            if not isinstance(item, dict):
                return {}
            raw_item = raw_basis.get(key)
            payload = dict(item)
            if isinstance(raw_item, dict):
                payload["raw_score"] = int(raw_item.get("score") or 0)
                payload["raw_label"] = str(raw_item.get("label") or raw_item.get("state") or "")
            return payload

        def eventization_conditions_payload(candidate: dict[str, object]) -> dict[str, object]:
            basis = dict(candidate["selection_basis"])
            raw_basis = dict(candidate["raw_selection_basis"])
            match = candidate["match"]
            source = str(candidate["source"])
            gyeokguk_step_key = "gyeokguk_chain" if source == "dual" else "gyeokguk_role"
            ordered_steps = list(basis.get("order", []) or [])
            raw_flow_activation = dict(raw_basis.get("flow_activation", {}) or {})
            raw_flow_activation["raw_score"] = int(raw_flow_activation.get("score") or 0)
            return {
                "judgment_order": list(getattr(match, "judgment_order", []) or []),
                "ordered_steps": ordered_steps,
                "monthly_authority": {
                    "pattern": profile.primary_pattern,
                    "month_branch": profile.month_branch,
                    "month_branch_label": BRANCH_LABELS.get(profile.month_branch, profile.month_branch),
                    "month_command_ten_god": profile.month_command_ten_god,
                    "month_command_label": TEN_GOD_LABELS.get(
                        profile.month_command_ten_god,
                        profile.month_command_ten_god,
                    ),
                    "active_hidden_ten_god": profile.active_hidden_ten_god,
                    "active_hidden_ten_god_label": TEN_GOD_LABELS.get(
                        profile.active_hidden_ten_god,
                        profile.active_hidden_ten_god,
                    ),
                },
                "month_command": basis_step_payload(basis, raw_basis, "month_command"),
                "gyeokguk_step_key": gyeokguk_step_key,
                "gyeokguk_step": basis_step_payload(basis, raw_basis, gyeokguk_step_key),
                "gyeokguk_formation": basis_step_payload(basis, raw_basis, "gyeokguk_formation"),
                "day_master_strength": basis_step_payload(basis, raw_basis, "day_master_strength"),
                "climate": basis_step_payload(basis, raw_basis, "climate"),
                "protrusion": basis_step_payload(basis, raw_basis, "protrusion"),
                "rooting": basis_step_payload(basis, raw_basis, "rooting"),
                "position": basis_step_payload(basis, raw_basis, "position"),
                "hidden_stems": basis_step_payload(basis, raw_basis, "hidden_stems"),
                "branch_interactions": basis_step_payload(basis, raw_basis, "branch_interactions"),
                "flow_activation": basis_step_payload(basis, raw_basis, "flow_activation"),
                "raw_flow_activation": raw_flow_activation,
                "selection_scoring": {
                    "center_score": int(candidate["score"]),
                    "selection_adjusted_score": int(candidate.get("selection_adjusted_score", candidate["score"])),
                    "selection_overlap_penalty": int(candidate.get("selection_overlap_penalty", 0)),
                    "context_score_delta": int(basis.get("context_score_delta") or 0),
                    "classical_action_score": int(basis.get("classical_action_score") or 0),
                    "component_classical_action_score": int(basis.get("component_classical_action_score") or 0),
                    "ten_god_operation_depth_score": int(
                        dict(basis.get("ten_god_operation_depth", {}) or {}).get("score") or 0
                    ),
                },
            }

        def operation_hierarchy_payload(
            source: str,
            match,
            match_payload: dict[str, object],
            candidate: dict[str, object],
        ) -> dict[str, object]:
            event_conditions = eventization_conditions_payload(candidate)
            real_world_focus = real_world_projection_payload(match, list(candidate["tags"]))
            if source == "single":
                assessment = dict(match_payload.get("single_operation_assessment", {}) or {})
                return {
                    "main_operation": {
                        "kind": "single",
                        "title": str(candidate["title"]),
                        "acting_ten_god": str(match_payload.get("acting_ten_god", "")),
                        "acting_ten_god_label": str(match_payload.get("acting_ten_god_label", "")),
                        "classical_tags": list(candidate["tags"]),
                        "role_in_pattern": dict(assessment.get("acting_role_in_pattern", {}) or {}),
                        "function": dict(assessment.get("single_function", {}) or {}),
                        "disease_medicine_axis": dict(assessment.get("disease_medicine_axis", {}) or {}),
                        "visibility_axis": dict(assessment.get("visibility_axis", {}) or {}),
                        "timing_axis": dict(assessment.get("timing_axis", {}) or {}),
                        "domain_axis": dict(assessment.get("domain_axis", {}) or {}),
                        "context_axis": dict(assessment.get("context_axis", {}) or {}),
                    },
                    "supporting_operations": [
                        {
                            "kind": "pattern_center",
                            "ten_god": profile.primary_ten_god,
                            "ten_god_label": TEN_GOD_LABELS.get(profile.primary_ten_god, profile.primary_ten_god),
                            "operation_face": ten_god_operation_face_payload(profile.primary_ten_god),
                            "formation_state": profile.formation_state,
                            "clarity_state": profile.clarity_state,
                        }
                    ],
                    "eventization_conditions": event_conditions,
                    "real_world_focus": real_world_focus,
                }

            assessment = dict(match_payload.get("dual_operation_assessment", {}) or {})
            component_actions = dict(assessment.get("component_single_actions", {}) or {})
            first_ten_god = str(match_payload.get("first_ten_god", ""))
            second_ten_god = str(match_payload.get("second_ten_god", ""))
            return {
                "main_operation": {
                    "kind": "dual_pair",
                    "title": str(candidate["title"]),
                    "first_ten_god": first_ten_god,
                    "first_ten_god_label": TEN_GOD_LABELS.get(first_ten_god, first_ten_god),
                    "second_ten_god": second_ten_god,
                    "second_ten_god_label": TEN_GOD_LABELS.get(second_ten_god, second_ten_god),
                    "first_to_second_relation": str(match_payload.get("first_to_second_relation", "")),
                    "classical_tags": list(candidate["tags"]),
                    "pair_classical_tags": list(component_actions.get("pair_classical_tags", []) or []),
                    "pair_function": dict(assessment.get("pair_function", {}) or {}),
                    "exact_pair_axis": dict(assessment.get("exact_pair_axis", {}) or {}),
                    "disease_medicine_axis": dict(assessment.get("disease_medicine_axis", {}) or {}),
                    "interaction_judgment": dict(assessment.get("interaction_judgment", {}) or {}),
                    "visibility_axis": dict(assessment.get("visibility_axis", {}) or {}),
                    "timing_order": dict(assessment.get("timing_order", {}) or {}),
                    "domain_axis": dict(assessment.get("domain_axis", {}) or {}),
                    "context_axis": dict(assessment.get("context_axis", {}) or {}),
                    "primary_actor": str(assessment.get("primary_actor", "")),
                    "primary_actor_label": str(assessment.get("primary_actor_label", "")),
                    "secondary_actor": str(assessment.get("secondary_actor", "")),
                    "secondary_actor_label": str(assessment.get("secondary_actor_label", "")),
                    "actor_hierarchy_logic": str(assessment.get("actor_hierarchy_logic", "")),
                    "pattern_combination_state": str(assessment.get("pattern_combination_state", "")),
                    "combination_resolution_state": str(assessment.get("combination_resolution_state", "")),
                    "combination_resolution_logic": str(assessment.get("combination_resolution_logic", "")),
                },
                "supporting_operations": [
                    {
                        "kind": "component_single_action",
                        "component": "first",
                        "ten_god": first_ten_god,
                        "ten_god_label": TEN_GOD_LABELS.get(first_ten_god, first_ten_god),
                        "role_in_pattern": dict(assessment.get("first_role_in_pattern", {}) or {}),
                        "classical_tags": list(component_actions.get("first_classical_tags", []) or []),
                        "operation_face": ten_god_operation_face_payload(first_ten_god),
                    },
                    {
                        "kind": "component_single_action",
                        "component": "second",
                        "ten_god": second_ten_god,
                        "ten_god_label": TEN_GOD_LABELS.get(second_ten_god, second_ten_god),
                        "role_in_pattern": dict(assessment.get("second_role_in_pattern", {}) or {}),
                        "classical_tags": list(component_actions.get("second_classical_tags", []) or []),
                        "operation_face": ten_god_operation_face_payload(second_ten_god),
                    },
                ],
                "eventization_conditions": event_conditions,
                "real_world_focus": real_world_focus,
            }

        def center_core_action_payload(candidate: dict[str, object]) -> dict[str, object]:
            source = str(candidate["source"])
            match = candidate["match"]
            match_payload = action_match_payload(match) if source == "single" else dual_action_match_payload(match)
            selection_basis = dict(candidate["selection_basis"])
            operation_depth = selection_basis.get("ten_god_operation_depth", {})
            center_judgment_axis = (
                dict(operation_depth.get("center_judgment_axis", {}))
                if isinstance(operation_depth, dict)
                else {}
            )
            operation_ten_gods = (
                [match.acting_ten_god]
                if source == "single"
                else [match.first_ten_god, match.second_ten_god]
            )
            pattern_identity = {
                "pattern": match.pattern,
                "pattern_label": PATTERN_LABELS.get(match.pattern, match.pattern),
                "pattern_center_ten_god": profile.primary_ten_god,
                "pattern_center_ten_god_label": TEN_GOD_LABELS.get(
                    profile.primary_ten_god,
                    profile.primary_ten_god,
                ),
                "month_command_ten_god": profile.month_command_ten_god,
                "month_command_ten_god_label": TEN_GOD_LABELS.get(
                    profile.month_command_ten_god,
                    profile.month_command_ten_god,
                ),
                "pattern_family": profile.family,
                "formation_state": profile.formation_state,
                "clarity_state": profile.clarity_state,
            }
            action_identity = (
                {
                    **pattern_identity,
                    "acting_ten_god": match.acting_ten_god,
                    "acting_ten_god_label": TEN_GOD_LABELS.get(match.acting_ten_god, match.acting_ten_god),
                    "relation_to_pattern": match.relation_to_pattern,
                    "action_key": match.action_key,
                    "action_nature": match.action_nature,
                    "center_effect": match.center_effect,
                }
                if source == "single"
                else {
                    **pattern_identity,
                    "first_ten_god": match.first_ten_god,
                    "first_ten_god_label": TEN_GOD_LABELS.get(match.first_ten_god, match.first_ten_god),
                    "second_ten_god": match.second_ten_god,
                    "second_ten_god_label": TEN_GOD_LABELS.get(match.second_ten_god, match.second_ten_god),
                    "pattern_ten_god": match.pattern_ten_god,
                    "pattern_ten_god_label": TEN_GOD_LABELS.get(match.pattern_ten_god, match.pattern_ten_god),
                    "pattern_group": match.pattern_group,
                    "first_relation_to_pattern": match.first_relation_to_pattern,
                    "second_relation_to_pattern": match.second_relation_to_pattern,
                    "first_to_second_relation": match.first_to_second_relation,
                    "pattern_center_bridge_profile": dict(match.pattern_center_bridge),
                    "sequence_key": match.sequence_key,
                    "chain_grade": match.chain_grade,
                    "chain_nature": match.chain_nature,
                    "pattern_combination_state": match.pattern_combination_state,
                    "combination_resolution_state": match.combination_resolution_state,
                    "combination_resolution_logic": match.combination_resolution_logic,
                    "primary_actor": match.primary_actor,
                    "primary_actor_label": TEN_GOD_LABELS.get(match.primary_actor, match.primary_actor),
                    "secondary_actor": match.secondary_actor,
                    "secondary_actor_label": TEN_GOD_LABELS.get(match.secondary_actor, match.secondary_actor),
                    "actor_hierarchy_logic": match.actor_hierarchy_logic,
                    "disease_medicine_logic": match.disease_medicine_logic,
                    "exact_pair_key": match.exact_pair_key,
                    "exact_pair_category": match.exact_pair_category,
                    "exact_pair_name": match.exact_pair_name,
                    "exact_pair_effect": match.exact_pair_effect,
                    "exact_pair_risk": match.exact_pair_risk,
                    "exact_pair_timing": match.exact_pair_timing,
                    "first_then_second_activation": match.first_then_second_activation,
                    "second_then_first_activation": match.second_then_first_activation,
                    "activation_order_profile": dict(match.activation_order_profile),
                }
            )
            return {
                "source": source,
                "title": str(candidate["title"]),
                "action_identity": action_identity,
                "center_score": int(candidate["score"]),
                "selection_adjusted_score": int(candidate.get("selection_adjusted_score", candidate["score"])),
                "selection_overlap_penalty": int(candidate.get("selection_overlap_penalty", 0)),
                "selection_reasons": list(candidate["reason"]),
                "selection_role": dict(candidate.get("selection_role", {}) or {}),
                "center_judgment_axis": center_judgment_axis,
                "center_axis_score": int(center_judgment_axis.get("score") or 0),
                "selection_basis": selection_basis,
                "raw_selection_basis": dict(candidate["raw_selection_basis"]),
                "presence_state": str(getattr(match, "presence_state", "") or ""),
                "presence_score": int(getattr(match, "presence_score", 0) or 0),
                "activation_context": str(getattr(match, "activation_context", "") or ""),
                "month_fit_state": str(getattr(match, "month_fit_state", "") or ""),
                "position_context": dict(getattr(match, "position_context", {}) or {}),
                "counter_signals": list(getattr(match, "counter_signals", []) or []),
                "judgment_order": list(getattr(match, "judgment_order", [])),
                "classical_action_tags": list(candidate["tags"]),
                "component_classical_action_tags": list(candidate.get("component_tags", []) or []),
                "dedupe_classical_action_tags": list(candidate.get("dedupe_tags", []) or []),
                "classical_action_mechanics": classical_action_mechanics_payload(list(candidate["tags"])),
                "feature_axis_impacts": feature_axis_impacts_payload(
                    candidate["tags"],
                    getattr(match, "domain_priority", []),
                    source=source,
                ),
                "operation_faces": operation_faces_payload(operation_ten_gods),
                "pattern_center_operation_face": ten_god_operation_face_payload(profile.primary_ten_god),
                "exact_profile_domain_basis": exact_profile_domain_basis_payload(
                    list(getattr(match, "basis_codes", []) or [])
                ),
                "pattern_center_bridge": (
                    pattern_center_bridge_payload(list(getattr(match, "basis_codes", []) or []))
                    if source == "dual"
                    else {}
                ),
                "single_operation_assessment": (
                    match_payload.get("single_operation_assessment", {})
                    if source == "single"
                    else {}
                ),
                "dual_operation_assessment": (
                    match_payload.get("dual_operation_assessment", {})
                    if source == "dual"
                    else {}
                ),
                "operation_hierarchy": operation_hierarchy_payload(source, match, match_payload, candidate),
                "real_world_projection": real_world_projection_payload(match, list(candidate["tags"])),
                "event_manifestations": dict(getattr(match, "event_manifestations", {}) or {}),
                "interaction_judgment": dict(getattr(match, "interaction_judgment", {}) or {}),
                "visibility_interaction": dict(getattr(match, "visibility_interaction", {}) or {}),
                "timing_hits": (
                    single_action_timing_hits(match, limit=3)
                    if source == "single"
                    else dual_action_timing_hits(match, limit=3)
                ),
                "timing_score": int(candidate["timing_score"]),
                "center_timing_score": int(candidate["center_timing_score"]),
                "formation_state": profile.formation_state,
                "clarity_state": profile.clarity_state,
                "domain_priority": list(getattr(match, "domain_priority", []) or []),
                "context_judgment_state": str(getattr(match, "context_judgment_state", "")),
                "context_judgment_summary": str(getattr(match, "context_judgment_summary", "")),
                "context_judgment_path": list(getattr(match, "context_judgment_path", []) or []),
                "match": match_payload,
            }

        def flow_activated_core_action_payload(candidate: dict[str, object]) -> dict[str, object]:
            payload = center_core_action_payload(candidate)
            payload["flow_activation_score"] = int(candidate.get("timing_score") or 0)
            payload["flow_selection_basis"] = dict(candidate.get("raw_selection_basis", {}) or {})
            payload["flow_activation_basis"] = dict(
                dict(candidate.get("raw_selection_basis", {}) or {}).get("flow_activation", {}) or {}
            )
            payload["flow_timing_hits"] = list(payload.get("timing_hits", []) or [])[:3]
            return payload

        def unique_limited(values: object, limit: int = 6) -> list[str]:
            result: list[str] = []
            sequence = list(values or []) if isinstance(values, (list, tuple, set)) else []
            for value in sequence:
                text = str(value).strip()
                if text and text not in result:
                    result.append(text)
                if len(result) >= limit:
                    break
            return result

        def domain_label_list(codes: object, limit: int = 4) -> list[str]:
            fallback_labels = {
                "relationship": "관계",
                "reputation": "명예",
                "personality": "성향",
                "work": "직업",
            }
            labels: list[str] = []
            for code in unique_limited(codes, limit=limit):
                label = DOMAIN_LABELS.get(code, fallback_labels.get(code, code))
                if label not in labels:
                    labels.append(label)
            return labels

        def card_axis_labels(values: object, limit: int = 4) -> list[str]:
            replacements = {
                "돈": "재물",
                "사람": "대인",
                "직장": "직업",
                "판단 방식": "판단",
            }
            labels: list[str] = []
            for label in unique_limited(values, limit=limit):
                normalized = replacements.get(label, label)
                if normalized not in labels:
                    labels.append(normalized)
            return labels

        def join_labels(labels: list[str], limit: int = 3) -> str:
            return ", ".join(labels[:limit])

        def ro_particle(label: str) -> str:
            if not label:
                return "으로"
            last = label[-1]
            code = ord(last)
            if 0xAC00 <= code <= 0xD7A3:
                jong = (code - 0xAC00) % 28
                return "로" if jong in {0, 8} else "으로"
            return "로"

        def center_card_basis_summary(center_item: dict[str, object]) -> dict[str, object]:
            basis = dict(center_item.get("selection_basis", {}) or {})
            source = str(center_item.get("source") or "")
            order = list(basis.get("order", []) or [])
            axis_labels = {
                "month_command": "월령",
                "gyeokguk_role": "격국",
                "gyeokguk_chain": "격국",
                "gyeokguk_formation": "격국 성립",
                "day_master_strength": "일간 강약",
                "climate": "조후",
                "protrusion": "투출",
                "rooting": "통근",
                "position": "위치",
                "hidden_stems": "지장간",
                "branch_interactions": "합충형파해",
                "flow_activation": "대운·세운",
            }
            axis_evidence: list[dict[str, object]] = []
            for key in order:
                step = dict(basis.get(str(key), {}) or {})
                axis_evidence.append(
                    {
                        "key": str(key),
                        "axis": axis_labels.get(str(key), str(key)),
                        "judgment": str(step.get("label") or step.get("state") or ""),
                        "score": int(step.get("score") or 0),
                    }
                )

            decisive_axes = sorted(
                [axis for axis in axis_evidence if int(axis.get("score") or 0) > 0],
                key=lambda axis: -int(axis.get("score") or 0),
            )[:5]
            reality_keys = {"protrusion", "rooting", "position", "hidden_stems", "branch_interactions"}
            reality_axes = [axis for axis in axis_evidence if axis["key"] in reality_keys]
            operation_depth = dict(basis.get("ten_god_operation_depth", {}) or {})
            exact_specificity = dict(basis.get("exact_ten_god_specificity", {}) or {})
            relevance = dict(basis.get("pattern_center_relevance", {}) or {})
            return {
                "source": source,
                "judgment_order": [axis["axis"] for axis in axis_evidence],
                "monthly_authority": {
                    "pattern": profile.primary_pattern,
                    "month_branch": profile.month_branch,
                    "month_branch_label": BRANCH_LABELS.get(profile.month_branch, profile.month_branch),
                    "month_command_ten_god": profile.month_command_ten_god,
                    "month_command_label": TEN_GOD_LABELS.get(
                        profile.month_command_ten_god,
                        profile.month_command_ten_god,
                    ),
                    "active_hidden_ten_god": profile.active_hidden_ten_god,
                    "active_hidden_ten_god_label": TEN_GOD_LABELS.get(
                        profile.active_hidden_ten_god,
                        profile.active_hidden_ten_god,
                    ),
                },
                "axis_evidence": axis_evidence,
                "decisive_axes": decisive_axes,
                "reality_axes": reality_axes,
                "pattern_center_relevance": {
                    "label": str(relevance.get("label") or ""),
                    "score": int(relevance.get("score") or 0),
                    "direct_center_actor": bool(relevance.get("direct_center_actor")),
                    "same_group_as_center": bool(relevance.get("same_group_as_center")),
                    "pattern_center_bridge": bool(relevance.get("pattern_center_bridge")),
                },
                "operation_depth": {
                    "state": str(operation_depth.get("state") or ""),
                    "grade_state": str(operation_depth.get("grade_state") or ""),
                    "relation_state": str(operation_depth.get("relation_state") or ""),
                    "score": int(operation_depth.get("score") or 0),
                    "major_tags": unique_limited(operation_depth.get("major_tags"), limit=5),
                    "support_tags": unique_limited(operation_depth.get("support_tags"), limit=5),
                    "caution_tags": unique_limited(operation_depth.get("caution_tags"), limit=5),
                },
                "exact_ten_god_specificity": {
                    "score": int(exact_specificity.get("score") or 0),
                    "ten_gods": unique_limited(exact_specificity.get("ten_gods"), limit=3),
                    "domains": unique_limited(exact_specificity.get("domains"), limit=5),
                    "pair_state": str(exact_specificity.get("pair_state") or ""),
                },
            }

        def center_core_action_card_payload(center_item: dict[str, object], rank: int) -> dict[str, object]:
            source = str(center_item.get("source") or "")
            action_identity = dict(center_item.get("action_identity", {}) or {})
            projection = dict(center_item.get("real_world_projection", {}) or {})
            role = dict(center_item.get("selection_role", {}) or {})
            center_axis = dict(center_item.get("center_judgment_axis", {}) or {})

            primary_axes = card_axis_labels(projection.get("axis_labels"), limit=4)
            primary_domains = unique_limited(
                projection.get("primary_domains") or projection.get("primary_axes"),
                limit=4,
            )
            primary_domain_labels = domain_label_list(primary_domains, limit=4)
            judgment_label = str(center_axis.get("label") or "중심 작용")

            if source == "dual":
                first_label = str(action_identity.get("first_ten_god_label") or "")
                second_label = str(action_identity.get("second_ten_god_label") or "")
                primary_label = str(action_identity.get("primary_actor_label") or first_label)
                secondary_label = str(action_identity.get("secondary_actor_label") or second_label)
                activation_profile = dict(action_identity.get("activation_order_profile", {}) or {})
                first_order = dict(activation_profile.get("first_then_second", {}) or {})
                second_order = dict(activation_profile.get("second_then_first", {}) or {})
                first_targets = unique_limited(first_order.get("entry_event_targets"), limit=5)
                first_results = unique_limited(first_order.get("result_event_targets"), limit=5)
                second_targets = unique_limited(second_order.get("entry_event_targets"), limit=5)
                second_results = unique_limited(second_order.get("result_event_targets"), limit=5)
                event_targets = unique_limited(
                    [
                        *first_targets,
                        *first_results,
                        *second_targets,
                        *second_results,
                    ],
                    limit=7,
                )
                card_title = f"{first_label}·{second_label} 작용"
                actors = {
                    "primary_actor_label": primary_label,
                    "secondary_actor_label": secondary_label,
                }
                timing_order = {
                    "first_then_second": {
                        "entry_label": str(first_order.get("entry_ten_god_label") or first_label),
                        "result_label": str(first_order.get("follow_ten_god_label") or second_label),
                        "entry_targets": first_targets,
                        "result_targets": first_results,
                    },
                    "second_then_first": {
                        "entry_label": str(second_order.get("entry_ten_god_label") or second_label),
                        "result_label": str(second_order.get("follow_ten_god_label") or first_label),
                        "entry_targets": second_targets,
                        "result_targets": second_results,
                    },
                }
                summary_items = unique_limited(
                    [
                        f"중심 십신은 {primary_label}, 보조 십신은 {secondary_label}입니다.",
                        f"{judgment_label}{ro_particle(judgment_label)} 판정합니다.",
                        f"현실 영역은 {join_labels(primary_axes)}입니다." if primary_axes else "",
                        f"사건은 {join_labels(event_targets)}에서 먼저 드러납니다." if event_targets else "",
                    ],
                    limit=4,
                )
            else:
                acting_label = str(action_identity.get("acting_ten_god_label") or "")
                event_manifestations = dict(center_item.get("event_manifestations", {}) or {})
                event_targets = unique_limited(
                    [
                        *primary_axes,
                        *domain_label_list(event_manifestations.keys(), limit=5),
                    ],
                    limit=7,
                )
                card_title = f"{acting_label} 작용"
                actors = {
                    "acting_ten_god_label": acting_label,
                    "relation_to_pattern": str(action_identity.get("relation_to_pattern") or ""),
                }
                timing_order = {
                    "single_activation": {
                        "entry_label": acting_label,
                        "event_targets": event_targets,
                    }
                }
                summary_items = unique_limited(
                    [
                        f"중심 십신은 {acting_label}입니다.",
                        f"{judgment_label}{ro_particle(judgment_label)} 판정합니다.",
                        f"현실 영역은 {join_labels(primary_axes)}입니다." if primary_axes else "",
                        f"사건은 {join_labels(event_targets)}에서 먼저 드러납니다." if event_targets else "",
                    ],
                    limit=4,
                )

            return {
                "rank": rank,
                "source": source,
                "title": card_title,
                "original_title": str(center_item.get("title") or ""),
                "center_score": int(center_item.get("center_score") or 0),
                "role": {
                    "code": str(role.get("code") or ""),
                    "label": str(role.get("label") or ""),
                },
                "judgment": {
                    "code": str(center_axis.get("code") or ""),
                    "label": str(center_axis.get("label") or ""),
                    "score": int(center_axis.get("score") or 0),
                },
                "actors": actors,
                "primary_axes": primary_axes,
                "primary_domains": primary_domains,
                "primary_domain_labels": primary_domain_labels,
                "event_targets": event_targets,
                "timing_order": timing_order,
                "basis_summary": center_card_basis_summary(center_item),
                "summary_items": summary_items,
            }

        center_core_candidates = center_core_action_candidates()
        center_core_payloads = [
            center_core_action_payload(candidate)
            for candidate in center_core_candidates
        ]
        flow_activated_core_payloads = [
            flow_activated_core_action_payload(candidate)
            for candidate in flow_activated_core_action_candidates()
        ]
        center_core_cards = [
            center_core_action_card_payload(center_item, rank)
            for rank, center_item in enumerate(center_core_payloads, start=1)
        ]

        return {
            "rule_version": profile.rule_version,
            "primary_pattern": profile.primary_pattern,
            "primary_ten_god": profile.primary_ten_god,
            "primary_ten_god_label": TEN_GOD_LABELS.get(profile.primary_ten_god, profile.primary_ten_god),
            "primary_ten_god_operation_face": ten_god_operation_face_payload(profile.primary_ten_god),
            "primary_group": profile.primary_group,
            "family": profile.family,
            "formation_state": profile.formation_state,
            "clarity_state": profile.clarity_state,
            "month_branch": profile.month_branch,
            "month_branch_label": BRANCH_LABELS.get(profile.month_branch, profile.month_branch),
            "month_command_stem": profile.month_command_stem,
            "month_command_ten_god": profile.month_command_ten_god,
            "month_command_label": TEN_GOD_LABELS.get(profile.month_command_ten_god, profile.month_command_ten_god),
            "active_hidden_stem": profile.active_hidden_stem,
            "active_hidden_ten_god": profile.active_hidden_ten_god,
            "active_hidden_ten_god_label": TEN_GOD_LABELS.get(
                profile.active_hidden_ten_god,
                profile.active_hidden_ten_god,
            ),
            "protruded_month_stems": list(profile.protruded_month_stems),
            "favorable_elements": list(profile.favorable_elements),
            "favorable_element_labels": [ELEMENT_LABELS.get(element, element) for element in profile.favorable_elements],
            "unfavorable_elements": list(profile.unfavorable_elements),
            "unfavorable_element_labels": [ELEMENT_LABELS.get(element, element) for element in profile.unfavorable_elements],
            "success_conditions": list(profile.success_conditions),
            "failure_conditions": list(profile.failure_conditions),
            "basis_codes": list(profile.basis_codes),
            "decision_notes": list(profile.decision_notes),
            "candidates": [candidate_payload(candidate) for candidate in profile.candidates[:6]],
            "ten_god_action_matches": [
                action_match_payload(match)
                for match in profile.ten_god_action_matches[:8]
            ],
            "dual_ten_god_action_matches": [
                dual_action_match_payload(match)
                for match in profile.dual_ten_god_action_matches[:10]
            ],
            "center_ten_god_action_matches": [
                action_match_payload(match)
                for match in sorted(profile.ten_god_action_matches, key=single_action_rank)[:3]
            ],
            "center_dual_ten_god_action_matches": [
                dual_action_match_payload(match)
                for match in center_dual_action_matches()
            ],
            "center_core_action_matches": [
                *center_core_payloads
            ],
            "flow_activated_core_action_matches": [
                *flow_activated_core_payloads
            ],
            "center_core_action_cards": center_core_cards,
        }

    def combination_payload(signal) -> dict[str, object]:
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "relation_type": signal.relation_type,
            "combination_key": signal.combination_key,
            "positions": list(signal.positions),
            "stems": list(signal.stems),
            "branches": list(signal.branches),
            "ten_gods": list(signal.ten_gods),
            "strength": signal.strength,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "interpretation": signal.interpretation,
        }

    def element_combination_payload(signal) -> dict[str, object]:
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "relation_type": signal.relation_type,
            "combination_key": signal.combination_key,
            "positions": list(signal.positions),
            "stems": list(signal.stems),
            "ordered_stems": list(signal.ordered_stems),
            "branches": list(signal.branches),
            "elements": list(signal.elements),
            "source_rule": signal.source_rule,
            "strength": signal.strength,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "trait_keywords": list(signal.trait_keywords),
            "interpretation": signal.interpretation,
            "monthly_variant_note": signal.monthly_variant_note,
            "day_master_variant_note": signal.day_master_variant_note,
        }

    def element_combination_evidence_signals() -> list[object]:
        visible_pairs = [
            signal
            for signal in element_combination_profile.heavenly_stem_signals
            if len(signal.stems) == 2
        ]

        def visible_rank(signal) -> tuple[int, int, str]:
            positions = {str(position).split(":", 1)[0] for position in signal.positions}
            return (
                0 if "day" in positions else 1,
                0 if "month" in positions else 1,
                signal.signal_id,
            )

        selected_visible: list[object] = []
        seen_element_pairs: set[tuple[str, ...]] = set()
        for signal in sorted(visible_pairs, key=visible_rank):
            element_pair = tuple(sorted(set(signal.elements)))
            if element_pair in seen_element_pairs:
                continue
            seen_element_pairs.add(element_pair)
            selected_visible.append(signal)
        return selected_visible + list(element_combination_profile.month_hidden_visible_signals)

    def directional_interaction_payload(signal) -> dict[str, object]:
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "direction_key": signal.direction_key,
            "element_direction_key": signal.element_direction_key,
            "direction_type": signal.direction_type,
            "source_position": signal.source_position,
            "target_position": signal.target_position,
            "source_stem": signal.source_stem,
            "target_stem": signal.target_stem,
            "source_branch": signal.source_branch,
            "target_branch": signal.target_branch,
            "source_element": signal.source_element,
            "target_element": signal.target_element,
            "source_rule": signal.source_rule,
            "strength": signal.strength,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "trait_keywords": list(signal.trait_keywords),
            "interpretation": signal.interpretation,
            "element_interpretation": signal.element_interpretation,
        }

    def ten_god_interaction_payload(signal) -> dict[str, object]:
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "direction_key": signal.direction_key,
            "source_position": signal.source_position,
            "target_position": signal.target_position,
            "source_stem": signal.source_stem,
            "target_stem": signal.target_stem,
            "source_branch": signal.source_branch,
            "target_branch": signal.target_branch,
            "source_ten_god": signal.source_ten_god,
            "target_ten_god": signal.target_ten_god,
            "source_rule": signal.source_rule,
            "strength": signal.strength,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "trait_keywords": list(signal.trait_keywords),
            "interpretation": signal.interpretation,
            "source_core": signal.source_core,
            "target_core": signal.target_core,
            "position_context": signal.position_context,
            "month_context_note": signal.month_context_note,
        }

    def reception_layer_payload(signal) -> dict[str, object]:
        return {
            "calculation_layer": {
                "strength": signal.strength,
                "priority_score": signal.priority_score,
                "seasonal_modifier": getattr(signal, "seasonal_modifier", None),
                "branch_relation_score_modifier": signal.branch_relation_score_modifier,
                "basis_codes": list(signal.basis_codes),
                "counter_signals": list(signal.counter_signals),
            },
            "interpretation_layer": {
                "core_interpretation": signal.core_interpretation,
                "felt_experience": getattr(signal, "felt_experience", ""),
                "behavior_tendency": getattr(signal, "behavior_tendency", ""),
                "domain_projection": dict(signal.domain_projection),
            },
            "applicability_layer": {
                "fitting_conditions": {
                    domain: list(values)
                    for domain, values in signal.fitting_conditions.items()
                },
            },
            "caution_layer": {
                "misfitting_conditions": {
                    domain: list(values)
                    for domain, values in signal.misfitting_conditions.items()
                },
                "fatigue_or_loss": {
                    domain: list(values)
                    for domain, values in signal.fatigue_or_loss.items()
                },
            },
        }

    def stem_reception_payload(signal) -> dict[str, object]:
        layers = reception_layer_payload(signal)
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "day_stem": signal.day_stem,
            "target_stem": signal.target_stem,
            "target_element": signal.target_element,
            "target_ten_god": signal.target_ten_god,
            "position": signal.position,
            "branch": signal.branch,
            "source": signal.source,
            "strength": signal.strength,
            "priority_score": signal.priority_score,
            "seasonal_modifier": signal.seasonal_modifier,
            "protruded": signal.protruded,
            "branch_relation_modifiers": list(signal.branch_relation_modifiers),
            "branch_relation_score_modifier": signal.branch_relation_score_modifier,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "trait_keywords": list(signal.trait_keywords),
            "core_interpretation": signal.core_interpretation,
            "felt_experience": signal.felt_experience,
            "behavior_tendency": signal.behavior_tendency,
            "calculation_layer": layers["calculation_layer"],
            "interpretation_layer": layers["interpretation_layer"],
            "applicability_layer": layers["applicability_layer"],
            "caution_layer": layers["caution_layer"],
            "fitting_conditions": {
                domain: list(values)
                for domain, values in signal.fitting_conditions.items()
            },
            "misfitting_conditions": {
                domain: list(values)
                for domain, values in signal.misfitting_conditions.items()
            },
            "fatigue_or_loss": {
                domain: list(values)
                for domain, values in signal.fatigue_or_loss.items()
            },
            "domain_projection": dict(signal.domain_projection),
            "evidence": list(signal.evidence),
        }

    def integrated_saju_payload(signal) -> dict[str, object]:
        layers = reception_layer_payload(signal)
        return {
            "signal_id": signal.signal_id,
            "layer": signal.layer,
            "source_position": signal.source_position,
            "target_position": signal.target_position,
            "source_stem": signal.source_stem,
            "target_stem": signal.target_stem,
            "source_element": signal.source_element,
            "target_element": signal.target_element,
            "source_ten_god": signal.source_ten_god,
            "target_ten_god": signal.target_ten_god,
            "element_direction_key": signal.element_direction_key,
            "ten_god_direction_key": signal.ten_god_direction_key,
            "source_reception_key": signal.source_reception_key,
            "target_reception_key": signal.target_reception_key,
            "strength": signal.strength,
            "priority_score": signal.priority_score,
            "branch_relation_score_modifier": signal.branch_relation_score_modifier,
            "domain_links": list(signal.domain_links),
            "basis_codes": list(signal.basis_codes),
            "counter_signals": list(signal.counter_signals),
            "trait_keywords": list(signal.trait_keywords),
            "core_interpretation": signal.core_interpretation,
            "combined_interpretation": signal.combined_interpretation,
            "calculation_layer": layers["calculation_layer"],
            "interpretation_layer": {
                **layers["interpretation_layer"],
                "combined_interpretation": signal.combined_interpretation,
            },
            "applicability_layer": layers["applicability_layer"],
            "caution_layer": layers["caution_layer"],
            "fitting_conditions": {
                domain: list(values)
                for domain, values in signal.fitting_conditions.items()
            },
            "misfitting_conditions": {
                domain: list(values)
                for domain, values in signal.misfitting_conditions.items()
            },
            "fatigue_or_loss": {
                domain: list(values)
                for domain, values in signal.fatigue_or_loss.items()
            },
            "domain_projection": dict(signal.domain_projection),
            "evidence": list(signal.evidence),
        }

    def axis_payload(key: str) -> dict[str, object]:
        axis = profile.axes[key]
        return {
            "key": axis.key,
            "category": axis.category,
            "label": axis.label,
            "score": axis.score,
            "percentile_label": axis.percentile_label,
            "strength_label": axis.strength_label,
            "confidence": axis.confidence,
            "basis_codes": list(axis.basis_codes),
            "counter_signals": list(axis.counter_signals),
            "customer_sentence": axis.customer_sentence,
        }

    def career_field_payload(key: str) -> dict[str, object]:
        field = career_field_profile.fields[key]
        return {
            "key": field.key,
            "label": field.label,
            "category": field.category,
            "score": field.score,
            "strength_label": field.strength_label,
            "confidence": field.confidence,
            "suitable_fields": list(field.suitable_fields),
            "unsuitable_conditions": list(field.unsuitable_conditions),
            "primary_unsuitable_condition": field.primary_unsuitable_condition,
            "day_master_fit_mode": field.day_master_fit_mode,
            "seasonal_fit_note": field.seasonal_fit_note,
            "fit_context_sentence": field.fit_context_sentence,
            "fit_context_basis_codes": list(field.fit_context_basis_codes),
            "role_style": field.role_style,
            "income_link": field.income_link,
            "sub_roles": [
                {
                    "key": sub_role.key,
                    "label": sub_role.label,
                    "parent_field_key": sub_role.parent_field_key,
                    "score": sub_role.score,
                    "strength_label": sub_role.strength_label,
                    "confidence": sub_role.confidence,
                    "work_style_links": list(sub_role.work_style_links),
                    "role_sentence": sub_role.role_sentence,
                    "basis_codes": list(sub_role.basis_codes),
                    "counter_signals": list(sub_role.counter_signals),
                }
                for sub_role in field.sub_roles
            ],
            "top_sub_role_keys": list(field.top_sub_role_keys),
            "display_priority": field.display_priority,
            "basis_codes": list(field.basis_codes),
            "counter_signals": list(field.counter_signals),
            "customer_sentence": field.customer_sentence,
        }

    def career_work_style_payload(key: str) -> dict[str, object]:
        style = career_field_profile.work_styles[key]
        return {
            "key": style.key,
            "label": style.label,
            "score": style.score,
            "strength_label": style.strength_label,
            "confidence": style.confidence,
            "role_sentence": style.role_sentence,
            "basis_codes": list(style.basis_codes),
            "counter_signals": list(style.counter_signals),
            "customer_sentence": style.customer_sentence,
        }

    output_goal_contract = output_goal_contracts()
    domain_decision_facets = _domain_decision_facet_payload(
        profile,
        cycle_regulation_profile if isinstance(cycle_regulation_profile, dict) else None,
        gyeokguk_profile,
        analysis.chart_structure,
        analysis.expert_adjudication,
    )
    timing_decision_facets = _timing_decision_payload(analysis)
    output_goal_coverage = _output_goal_coverage_payload(
        output_goal_contract=output_goal_contract,
        domain_facets=domain_decision_facets,
        timing_decision=timing_decision_facets,
        career_field_profile=career_field_profile,
        profile=profile,
    )

    return {
        "top_axes": [axis_payload(key) for key in profile.top_axis_keys],
        "caution_axes": [axis_payload(key) for key in profile.caution_axis_keys],
        "summary_sentences": list(profile.summary_sentences),
        "source_personality_profile": source_personality_profile_payload(source_personality_profile),
        "source_reading_profile": source_reading_profile_payload(source_reading_profile),
        "season_context": season_context_payload(),
        "month_governance_context": month_governance_payload(),
        "branch_reality_context": branch_reality_payload(),
        "cycle_regulation_context": cycle_regulation_payload(),
        "gyeokguk_contextual_context": gyeokguk_contextual_payload,
        "output_goal_contract": output_goal_contract,
        "domain_decision_facets": domain_decision_facets,
        "timing_decision_facets": timing_decision_facets,
        "output_goal_coverage": output_goal_coverage,
        "auxiliary_context": auxiliary_context_payload(),
        "pattern_context": pattern_context_payload(),
        "gyeokguk_context": gyeokguk_context_payload(),
        "career_field_rule_version": career_field_profile.rule_version,
        "career_interpretation_principle": career_field_profile.interpretation_principle,
        "career_field_summary": list(career_field_profile.summary_sentences),
        "career_work_styles": [
            career_work_style_payload(key)
            for key in sorted(
                career_field_profile.work_styles,
                key=lambda item: career_field_profile.work_styles[item].score,
                reverse=True,
            )
        ],
        "top_career_work_styles": [
            career_work_style_payload(key) for key in career_field_profile.top_work_style_keys
        ],
        "primary_career_fields": [career_field_payload(key) for key in career_field_profile.primary_field_keys],
        "reference_career_fields": [career_field_payload(key) for key in career_field_profile.reference_field_keys],
        "top_career_fields": [career_field_payload(key) for key in career_field_profile.top_field_keys],
        "caution_career_fields": [career_field_payload(key) for key in career_field_profile.caution_field_keys],
        "combination_summary": list(combination_profile.summary_sentences),
        "combination_domain_notes": {
            domain: list(notes)
            for domain, notes in combination_profile.domain_notes.items()
        },
        "top_combination_signals": [
            combination_payload(signal)
            for signal in (
                list(combination_profile.heavenly_stem_signals)
                + list(combination_profile.ten_god_chain_signals)
                + list(combination_profile.stem_branch_signals)
                + list(combination_profile.hidden_stem_signals)
            )
            if signal.signal_id in set(combination_profile.top_signal_ids)
        ],
        "element_combination_summary": list(element_combination_profile.summary_sentences),
        "element_combination_domain_notes": {
            domain: list(notes)
            for domain, notes in element_combination_profile.domain_notes.items()
        },
        "element_combination_evidence_signals": [
            element_combination_payload(signal)
            for signal in element_combination_evidence_signals()
        ],
        "top_element_combination_signals": [
            element_combination_payload(signal)
            for signal in (
                list(element_combination_profile.heavenly_stem_signals)
                + list(element_combination_profile.stem_branch_signals)
                + list(element_combination_profile.hidden_stem_signals)
                + list(element_combination_profile.month_hidden_visible_signals)
            )
            if signal.signal_id in set(element_combination_profile.top_signal_ids)
        ],
        "directional_interaction_summary": list(directional_interaction_profile.summary_sentences),
        "top_directional_interaction_signals": [
            directional_interaction_payload(signal)
            for signal in (
                list(directional_interaction_profile.heavenly_stem_signals)
                + list(directional_interaction_profile.stem_branch_signals)
                + list(directional_interaction_profile.hidden_stem_signals)
            )
            if signal.signal_id in set(directional_interaction_profile.top_signal_ids)
        ],
        "ten_god_interaction_summary": list(ten_god_interaction_profile.summary_sentences),
        "top_ten_god_interaction_signals": [
            ten_god_interaction_payload(signal)
            for signal in (
                list(ten_god_interaction_profile.visible_stem_signals)
                + list(ten_god_interaction_profile.stem_branch_signals)
                + list(ten_god_interaction_profile.hidden_stem_signals)
            )
            if signal.signal_id in set(ten_god_interaction_profile.top_signal_ids)
        ],
        "stem_reception_summary": list(stem_reception_profile.summary_sentences),
        "top_stem_reception_signals": [
            stem_reception_payload(signal)
            for signal in (
                list(stem_reception_profile.visible_stem_signals)
                + list(stem_reception_profile.branch_main_signals)
                + list(stem_reception_profile.hidden_stem_signals)
            )
            if signal.signal_id in set(stem_reception_profile.top_signal_ids)
        ],
        "integrated_saju_summary": list(integrated_saju_profile.summary_sentences),
        "top_integrated_saju_signals": [
            integrated_saju_payload(signal)
            for signal in (
                list(integrated_saju_profile.visible_pair_signals)
                + list(integrated_saju_profile.stem_branch_pair_signals)
                + list(integrated_saju_profile.hidden_pair_signals)
            )
            if signal.signal_id in set(integrated_saju_profile.top_signal_ids)
        ],
    }


def build_product_output(
    analysis: AnalysisResult,
    tier: ProductTier = "basic",
    *,
    item_limit_override: int | None = None,
    include_candidate_sections: bool = True,
) -> ProductOutput:
    if tier not in TIER_LIMITS:
        raise ValueError(f"Unsupported product tier: {tier}")
    tier_config = tier_definition(tier)
    selected = _limit_packets_for_surface(_select_packets(analysis, tier), item_limit_override)
    selected_ids = {packet.packet_id for packet in selected}
    omitted = [packet.packet_id for packet in analysis.event_packets if packet.packet_id not in selected_ids]
    items: list[ProductOutputItem] = []
    birth_year = analysis.trace.get("birth_year")
    shared_judgment_materials: dict[Domain, dict[str, Any]] = {}

    for packet in selected:
        summary_filter = filter_risk_language(_summary(packet))
        detail_filter = filter_risk_language(_detail(packet, tier))
        risk_filter = filter_risk_language(packet.risk_path)
        if not (summary_filter.output_allowed and detail_filter.output_allowed and risk_filter.output_allowed):
            omitted.append(packet.packet_id)
            continue

        basis_limit = tier_config.basis_limit
        timing_limit = tier_config.timing_limit
        summary_limit = tier_config.summary_limit
        items.append(
            ProductOutputItem(
                packet_id=packet.packet_id,
                product_tier=tier,
                domain=packet.domain,
                domain_label=f"{DOMAIN_LABELS[packet.domain]}운",
                period_label=packet.period_label,
                title=_title(packet),
                summary=summary_filter.filtered_text,
                detail=detail_filter.filtered_text,
                timing=packet.timing_markers[:timing_limit],
                timing_windows=packet.timing_windows[:timing_limit],
                action=packet.main_action,
                risk=risk_filter.filtered_text,
                basis_codes=packet.basis_codes[:basis_limit],
                filter_flags=list(dict.fromkeys(summary_filter.flags + detail_filter.flags + risk_filter.flags)),
                event_keywords=list(packet.event_keywords),
                opportunity_score=packet.opportunity_score,
                risk_score=packet.risk_score,
                change_score=packet.change_score,
                event_probability_score=packet.event_probability_score,
                confidence=packet.confidence,
                expression_strength=packet.expression_strength,
                score_labels=_score_labels(packet),
                basis_summary=_summarize_codes(packet.basis_codes, BASIS_EXPLANATION_RULES, summary_limit),
                counter_summary=_summarize_codes(packet.counter_signals, COUNTER_EXPLANATION_RULES, summary_limit),
                common_template_id=packet.common_template_id,
                domain_template_id=packet.domain_template_id,
                type_template_id=packet.type_template_id,
                template_slots={
                    **dict(packet.template_slots),
                    **({"birth_year": birth_year} if isinstance(birth_year, int) else {}),
                },
                past_check_status=packet.past_check_status,
                relationship_status=packet.relationship_status,
                relationship_status_label=RELATIONSHIP_STATUS_LABELS[packet.relationship_status],
                relationship_context=_relationship_context(packet),
                feature_axes=list(packet.feature_axes),
                judgment_context=build_domain_judgment_context(
                    analysis,
                    packet,
                    shared_materials_by_domain=shared_judgment_materials,
                ),
                expert_projection_summary=dict(packet.expert_projection_summary),
            )
        )

    sections = [_build_section(item, tier) for item in items]
    domain_coverage = _domain_coverage(analysis, items)
    target_years = list(analysis.trace.get("target_years", []))
    life_feature_summary = _life_feature_summary(analysis)
    expert_summary = dict(analysis.expert_adjudication.summary) if analysis.expert_adjudication is not None else {}
    if expert_summary:
        life_feature_summary["expert_summary"] = expert_summary
    if isinstance(birth_year, int):
        life_feature_summary["birth_year"] = birth_year
    catalog_entries = attach_catalog_content_blocks(
        catalog_payload_for_tier(tier, [item.domain for item in items]),
        items,
        life_feature_summary,
        target_years,
        tier,
    )
    section_selection = build_section_selection(analysis) if include_candidate_sections else None
    premium_candidate_sections = (
        build_candidate_report_sections(analysis)
        if tier == "premium" and include_candidate_sections
        else []
    )
    premium_detail_sections = (
        build_premium_detail_selection(analysis).matches
        if tier == "premium"
        else []
    )
    return ProductOutput(
        product_tier=tier,
        items=items,
        omitted_packet_ids=list(dict.fromkeys(omitted)),
        sections=sections,
        target_years=target_years,
        schema_version=PRODUCT_OUTPUT_SCHEMA_VERSION,
        engine_manifest=build_engine_manifest(tier),
        calibration_status=analysis.calibration_profile.status,
        calibration_label=CALIBRATION_LABELS.get(
            analysis.calibration_profile.status,
            "과거 사건 검증 상태를 추가 확인해야 합니다.",
        ),
        calibration_basis_codes=list(analysis.calibration_profile.basis_codes),
        warnings=list(analysis.warnings),
        warning_labels=_warning_labels(list(analysis.warnings)),
        domain_coverage=domain_coverage,
        domain_coverage_labels=_domain_coverage_labels(domain_coverage),
        life_feature_summary=life_feature_summary,
        catalog_entries=catalog_entries,
        section_selection_judgments=section_selection.judgments if section_selection is not None else [],
        selected_report_sections=section_selection.selected_sections if section_selection is not None else [],
        premium_candidate_sections=premium_candidate_sections,
        premium_detail_sections=premium_detail_sections,
        premium_profile_contract=premium_product_surface_contract(tier),
        expert_summary=expert_summary,
    )
