"""Career-field projection layer.

This layer converts the chart's elemental, ten-god, positional, combination,
and branch-relation evidence into practical career fields. It is intentionally
kept separate from event packets so future patches can improve field reasoning
without changing the yearly fortune product surface.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .constants import BRANCH_METADATA, MONTH_SEASON_MODIFIERS, STEM_METADATA, TEN_GOD_GROUPS
from .models import (
    BranchInteraction,
    CareerFieldProfile,
    CareerFieldScore,
    CareerSubRoleScore,
    CareerWorkStyleScore,
    Confidence,
    ElementCombinationProfile,
    ElementProfile,
    IntegratedSajuProfile,
    LifeFeatureProfile,
    PositionSignal,
    StemReceptionProfile,
    TenGodInteractionProfile,
    TenGodProfile,
)
from .ten_gods import ten_god_for


CAREER_FIELD_RULE_VERSION = "career_field_projection_v1"

FORBIDDEN_CUSTOMER_TERMS = ("흐름", "리듬", "패턴", "판", "통로", "구체화")
TEN_GOD_GROUP_KEYS = ("peer", "output", "wealth", "officer", "resource")
POSITIVE_BRANCH_RELATIONS = {"six_combine", "three_harmony", "three_harmony_half"}
NEGATIVE_BRANCH_RELATIONS = {"clash", "punishment", "self_punishment", "break", "harm"}


@dataclass(frozen=True)
class CareerFieldRule:
    key: str
    label: str
    category: str
    element_weights: dict[str, float]
    ten_god_group_weights: dict[str, float]
    ten_god_weights: dict[str, float]
    axis_weights: dict[str, float]
    suitable_fields: tuple[str, ...]
    unsuitable_conditions: tuple[str, ...]
    role_style: str
    income_link: str


@dataclass(frozen=True)
class CareerWorkStyleRule:
    key: str
    label: str
    element_weights: dict[str, float]
    ten_god_group_weights: dict[str, float]
    ten_god_weights: dict[str, float]
    axis_weights: dict[str, float]
    role_sentence: str


@dataclass(frozen=True)
class CareerSubRoleRule:
    key: str
    label: str
    parent_field_key: str
    element_weights: dict[str, float]
    ten_god_group_weights: dict[str, float]
    ten_god_weights: dict[str, float]
    axis_weights: dict[str, float]
    work_style_weights: dict[str, float]
    role_sentence: str


INTERPRETATION_PRINCIPLE = (
    "이 직업 해석은 특정 직업명을 단정하기보다, 당신의 선천 적성이 어떤 업무 활동에서 잘 쓰이는지를 보는 기준입니다."
)

DAY_MASTER_CAREER_MODES = {
    "gap": "큰 방향을 먼저 세우고, 직무의 기준과 책임 범위를 분명히 하려 합니다.",
    "eul": "사람, 일정, 세부 조건을 살피며 무리 없는 방식으로 일을 완성합니다.",
    "byeong": "해낸 일을 공개적으로 설명하고 인정받는 자리에서 역량을 잘 발휘합니다.",
    "jeong": "한 분야를 깊게 파고, 품질과 완성도를 높이는 방식으로 일합니다.",
    "mu": "넓은 범위의 업무를 맡아도 일정, 사람, 자원을 차분히 정리하며 전체 결과를 안정시키는 편입니다.",
    "gi": "현장 정보와 사람의 필요를 세밀히 다루며 실무를 조정합니다.",
    "gyeong": "기준을 세우고 불필요한 것을 정리해 결과를 명확하게 만듭니다.",
    "sin": "품질, 세부 차이, 가치 선별에 민감하게 반응하며 완성도를 높입니다.",
    "im": "큰 정보와 변화의 여지를 읽고 선택지를 넓히는 방식으로 일합니다.",
    "gye": "작은 단서와 반복 자료를 모아 섬세한 결론을 내리는 방식으로 일합니다.",
}

MONTH_BRANCH_CAREER_NOTES = {
    "in": "직업적으로는 새 일을 시작하고, 기획하며, 사람을 성장시키는 업무가 먼저 주어집니다.",
    "myo": "직업적으로는 사람 사이의 기준을 조율하고, 세부 일정과 역할을 조정하는 능력이 인정으로 이어집니다.",
    "jin": "직업적으로는 성장한 일을 현실적인 기준, 예산, 자원 관리로 옮기는 능력이 강점이 됩니다.",
    "sa": "직업적으로는 발표, 영업, 홍보, 고객 대응처럼 해낸 일이 밖에서 확인되는 업무가 강조됩니다.",
    "o": "직업적으로는 공개 평가, 설득, 주도적 의사결정이 필요한 자리에서 인정받습니다.",
    "mi": "직업적으로는 사람과 자원을 묶어 일이 돌아가게 만드는 관리 업무가 강점이 됩니다.",
    "sin": "직업적으로는 선별, 검토, 품질 관리, 규칙 적용 능력이 평가의 핵심이 됩니다.",
    "yu": "직업적으로는 완성도, 기준 준수, 결과물의 정밀함이 인정으로 이어집니다.",
    "sul": "직업적으로는 책임 범위, 보유 자원, 마감 기준을 분명히 하는 업무에서 안정적입니다.",
    "hae": "직업적으로는 정보 수집, 조사, 장기 계획처럼 충분한 검토가 필요한 업무에서 강점을 보입니다.",
    "ja": "직업적으로는 자료, 계산, 전략, 사전 검토 능력이 인정으로 이어집니다.",
    "chuk": "직업적으로는 정산, 보존, 실무 안정성처럼 오래 유지해야 하는 책임에서 신뢰를 얻습니다.",
}


CAREER_WORK_STYLE_RULES: dict[str, CareerWorkStyleRule] = {
    "organization": CareerWorkStyleRule(
        key="organization",
        label="조직형",
        element_weights={"earth": 1.0, "metal": 0.9, "water": 0.45},
        ten_god_group_weights={"officer": 1.2, "resource": 0.85, "wealth": 0.45},
        ten_god_weights={"jeong_gwan": 1.15, "jeong_in": 0.8, "jeong_jae": 0.45},
        axis_weights={"organization_adaptability": 1.25, "responsibility_capacity": 1.0, "honor_recognition": 0.7},
        role_sentence="기준과 절차가 분명한 자리에서 안정적으로 성과를 냅니다. 맡은 역할이 분명할수록 실력을 인정받습니다.",
    ),
    "independent": CareerWorkStyleRule(
        key="independent",
        label="독립형",
        element_weights={"wood": 0.85, "fire": 0.85, "water": 0.65},
        ten_god_group_weights={"wealth": 1.0, "output": 0.9, "peer": 0.75},
        ten_god_weights={"pyeon_jae": 1.0, "sang_gwan": 0.85, "geob_jae": 0.65},
        axis_weights={"business_expansion": 1.15, "self_direction": 1.0, "decision_consistency": 0.65},
        role_sentence="권한이 분명한 일을 직접 맡을 때 수익이 커집니다. 보상 기준이 분명해지며 인정도 빨라집니다.",
    ),
    "expert": CareerWorkStyleRule(
        key="expert",
        label="전문가형",
        element_weights={"water": 1.0, "metal": 0.9, "wood": 0.65},
        ten_god_group_weights={"resource": 1.2, "output": 0.75, "officer": 0.45},
        ten_god_weights={"pyeon_in": 1.0, "jeong_in": 0.9, "sik_sin": 0.65},
        axis_weights={"academic_expertise": 1.25, "decision_consistency": 0.85, "practical_planning": 0.75},
        role_sentence="지식, 기술, 자격, 분석 근거가 쌓일수록 직업적 설득력이 커지는 성향입니다.",
    ),
    "manager": CareerWorkStyleRule(
        key="manager",
        label="관리자형",
        element_weights={"earth": 1.0, "fire": 0.75, "metal": 0.65},
        ten_god_group_weights={"officer": 1.0, "wealth": 0.75, "peer": 0.55},
        ten_god_weights={"pyeon_gwan": 0.8, "jeong_gwan": 0.75, "jeong_jae": 0.55, "bi_gyeon": 0.45},
        axis_weights={"leadership_potential": 1.1, "responsibility_capacity": 1.0, "practical_planning": 0.75},
        role_sentence="사람과 자원을 나누고, 일정과 책임을 조정하는 자리에서 영향력이 커지는 성향입니다.",
    ),
}


CAREER_FIELD_RULES: dict[str, CareerFieldRule] = {
    "education_training": CareerFieldRule(
        key="education_training",
        label="교육·강의·인재 개발",
        category="knowledge_service",
        element_weights={"wood": 1.1, "fire": 0.9, "water": 0.7},
        ten_god_group_weights={"resource": 1.2, "output": 1.0, "officer": 0.5},
        ten_god_weights={"jeong_in": 1.2, "sik_sin": 0.9, "sang_gwan": 0.7, "jeong_gwan": 0.4},
        axis_weights={"academic_expertise": 1.2, "communication_expression": 1.0, "practical_planning": 0.7},
        suitable_fields=("교육 기획", "강의·코칭", "인재 개발", "전문 지식 콘텐츠", "자격 교육"),
        unsuitable_conditions=(
            "가르칠 내용보다 즉흥 대응과 감정 소모가 더 큰 자리",
            "수강자 관리 기준 없이 책임만 늘어나는 자리",
        ),
        role_style="지식과 경험을 이해하기 쉬운 순서로 정리하고, 다른 사람이 따라올 수 있게 만드는 일에서 인정받습니다.",
        income_link="강의력, 커리큘럼, 자격, 반복 의뢰가 보상으로 연결될 때 수입이 안정됩니다.",
    ),
    "planning_content_brand": CareerFieldRule(
        key="planning_content_brand",
        label="기획·콘텐츠·브랜드",
        category="creative_strategy",
        element_weights={"wood": 1.0, "fire": 1.15, "water": 0.55},
        ten_god_group_weights={"output": 1.25, "wealth": 0.8, "resource": 0.45},
        ten_god_weights={"sang_gwan": 1.15, "sik_sin": 0.9, "pyeon_jae": 0.75, "pyeon_in": 0.4},
        axis_weights={"communication_expression": 1.2, "business_expansion": 0.9, "interpersonal_influence": 0.65},
        suitable_fields=("브랜드 기획", "콘텐츠 전략", "마케팅 기획", "상품 기획", "캠페인 운영"),
        unsuitable_conditions=(
            "표현은 요구하지만 결정권과 검증 시간이 없는 자리",
            "아이디어만 계속 소비되고 평가 기준이 남지 않는 자리",
        ),
        role_style="사람들이 어떤 메시지에 반응하는지 읽고, 생각을 상품이나 브랜드 언어로 바꾸는 일에 강합니다.",
        income_link="평가 지표가 분명할수록 수입으로 이어집니다. 프로젝트 단가가 명확할 때 보상도 안정됩니다.",
    ),
    "sales_business_development": CareerFieldRule(
        key="sales_business_development",
        label="영업·사업 개발·제휴",
        category="commercial",
        element_weights={"fire": 1.0, "wood": 0.85, "water": 0.75},
        ten_god_group_weights={"wealth": 1.25, "output": 0.85, "peer": 0.65},
        ten_god_weights={"pyeon_jae": 1.25, "jeong_jae": 0.75, "sang_gwan": 0.7, "geob_jae": 0.55},
        axis_weights={"business_expansion": 1.2, "deal_selection": 1.0, "income_expansion": 0.85},
        suitable_fields=("B2B 영업", "사업 개발", "제휴 영업", "거래처 관리", "시장 개척"),
        unsuitable_conditions=(
            "권한은 작고 매출 압박만 큰 자리",
            "계약 조건이 자주 바뀌어 책임과 보상이 분리되는 자리",
        ),
        role_style="사람과 기회를 연결하고, 상대의 필요를 금액과 계약으로 바꾸는 일에서 수입이 납니다.",
        income_link="보너스, 계약 단가, 거래처 재구매, 제휴 수수료가 명확할 때 재물운과 직업운이 함께 좋아집니다.",
    ),
    "operations_project_management": CareerFieldRule(
        key="operations_project_management",
        label="운영·프로젝트 관리",
        category="management",
        element_weights={"earth": 1.15, "metal": 0.85, "fire": 0.55},
        ten_god_group_weights={"officer": 1.1, "resource": 0.75, "wealth": 0.6},
        ten_god_weights={"jeong_gwan": 1.05, "jeong_in": 0.75, "jeong_jae": 0.65, "pyeon_gwan": 0.55},
        axis_weights={"responsibility_capacity": 1.2, "organization_adaptability": 1.0, "practical_planning": 0.95},
        suitable_fields=("운영 관리", "PM·PO 보조", "프로젝트 관리", "프로세스 개선", "조직 관리"),
        unsuitable_conditions=(
            "책임 범위는 넓은데 의사결정 기준이 불분명한 자리",
            "일정과 자원이 계속 바뀌면서 정리 권한은 주어지지 않는 자리",
        ),
        role_style="복잡한 일을 순서대로 정리하는 자리에서 실력을 인정받습니다. 여러 사람의 역할을 맞추는 일에도 강합니다.",
        income_link="관리 범위가 넓어질수록 수입도 함께 늘어납니다. 책임 권한이 분명할 때 보상도 좋아집니다.",
    ),
    "finance_accounting_review": CareerFieldRule(
        key="finance_accounting_review",
        label="회계·세무·금융 심사",
        category="finance_control",
        element_weights={"earth": 1.05, "metal": 1.0, "water": 0.65},
        ten_god_group_weights={"wealth": 1.15, "resource": 0.85, "officer": 0.75},
        ten_god_weights={"jeong_jae": 1.25, "jeong_in": 0.8, "jeong_gwan": 0.7, "pyeon_jae": 0.45},
        axis_weights={"asset_retention": 1.2, "spending_control": 1.0, "loss_avoidance": 0.95},
        suitable_fields=("회계", "세무", "재무 관리", "여신·심사", "정산·손익 관리"),
        unsuitable_conditions=(
            "숫자 책임은 크지만 자료 접근 권한이 부족한 자리",
            "속도만 요구하고 검토 절차를 생략하는 자리",
        ),
        role_style="돈의 출처와 사용처를 확인하고, 손익과 책임을 분리하는 역할에 잘 맞습니다.",
        income_link="정확성, 검토 책임, 자격, 관리 규모가 보상으로 인정될 때 자산 유지력도 함께 좋아집니다.",
    ),
    "law_audit_compliance": CareerFieldRule(
        key="law_audit_compliance",
        label="법무·감사·컴플라이언스",
        category="standard_control",
        element_weights={"metal": 1.2, "water": 0.75, "earth": 0.7},
        ten_god_group_weights={"officer": 1.25, "resource": 0.85, "output": 0.45},
        ten_god_weights={"jeong_gwan": 1.25, "pyeon_gwan": 0.9, "jeong_in": 0.75, "sang_gwan": 0.35},
        axis_weights={"honor_recognition": 1.1, "responsibility_capacity": 1.05, "reputation_maintenance": 0.9},
        suitable_fields=("법무", "내부 감사", "컴플라이언스", "규정 관리", "공공 규제 대응"),
        unsuitable_conditions=(
            "책임 소재가 불명확한데 문제 처리만 개인에게 몰리는 자리",
            "규정을 지키려 할수록 조직 내부 갈등만 커지는 자리",
        ),
        role_style="기준을 세우고 위험을 미리 걸러내며, 말과 문서의 책임을 분명히 하는 일에서 강합니다.",
        income_link="전문 자격, 책임 권한, 검토 범위가 공식적으로 인정될수록 명예와 보상이 함께 올라갑니다.",
    ),
    "data_research_strategy": CareerFieldRule(
        key="data_research_strategy",
        label="데이터·리서치·전략 분석",
        category="analysis_strategy",
        element_weights={"water": 1.15, "metal": 0.9, "earth": 0.65},
        ten_god_group_weights={"resource": 1.05, "output": 0.75, "officer": 0.65},
        ten_god_weights={"pyeon_in": 1.1, "jeong_in": 0.85, "sang_gwan": 0.75, "jeong_gwan": 0.45},
        axis_weights={"academic_expertise": 1.15, "decision_consistency": 0.9, "practical_planning": 0.85},
        suitable_fields=("데이터 분석", "시장 조사", "전략 리서치", "정책 분석", "업무 지표 분석"),
        unsuitable_conditions=(
            "근거 확인 없이 결론만 빨리 내야 하는 자리",
            "분석 결과가 의사결정에 반영되지 않는 자리",
        ),
        role_style="흩어진 자료에서 근거를 찾고, 선택 가능한 결론으로 정리하는 일에 적합합니다.",
        income_link="분석 결과가 의사결정, 예산, 매출 개선에 반영될수록 직업적 가치가 커집니다.",
    ),
    "technology_quality_system": CareerFieldRule(
        key="technology_quality_system",
        label="기술·품질·시스템",
        category="technical_system",
        element_weights={"metal": 1.1, "water": 0.9, "earth": 0.8},
        ten_god_group_weights={"resource": 1.0, "output": 0.8, "officer": 0.7},
        ten_god_weights={"pyeon_in": 0.95, "jeong_in": 0.8, "sik_sin": 0.75, "jeong_gwan": 0.55},
        axis_weights={"academic_expertise": 1.0, "practical_planning": 0.95, "career_achievement": 0.85},
        suitable_fields=("품질 관리", "시스템 운영", "기술 지원", "개발 관리", "보안·인프라 관리"),
        unsuitable_conditions=(
            "문제 원인을 확인할 시간 없이 즉시 책임만 요구하는 자리",
            "기술 검토보다 정치적 대응이 더 큰 자리",
        ),
        role_style="문제의 원인을 찾고, 반복 가능한 절차와 기술 기준으로 안정시키는 일에 강합니다.",
        income_link="기술 숙련도, 장애 대응력, 품질 책임, 시스템 규모가 보상으로 이어질 때 유리합니다.",
    ),
    "counseling_hr_client_success": CareerFieldRule(
        key="counseling_hr_client_success",
        label="상담·HR·고객 관리",
        category="people_service",
        element_weights={"wood": 0.9, "water": 0.85, "fire": 0.65, "earth": 0.45},
        ten_god_group_weights={"resource": 0.95, "output": 0.8, "peer": 0.6, "officer": 0.45},
        ten_god_weights={"jeong_in": 0.9, "sik_sin": 0.75, "bi_gyeon": 0.55, "jeong_gwan": 0.4},
        axis_weights={"interpersonal_influence": 1.0, "boundary_management": 0.9, "conflict_recovery": 0.85},
        suitable_fields=("상담", "HR", "고객 성공 관리", "CS 리더", "조직문화 담당"),
        unsuitable_conditions=(
            "감정 노동만 커지고 권한과 보호 장치가 없는 자리",
            "사람 문제를 다루지만 기록과 기준이 남지 않는 자리",
        ),
        role_style="상대의 요구를 듣고, 감정과 현실 조건을 함께 정리하는 일에서 신뢰를 얻습니다.",
        income_link="고객 유지율, 상담 전문성, 조직 관리 책임이 보상에 반영될 때 안정적인 직업 성취로 이어집니다.",
    ),
    "public_administration_institution": CareerFieldRule(
        key="public_administration_institution",
        label="공공·행정·기관 업무",
        category="institutional",
        element_weights={"earth": 1.0, "metal": 0.95, "water": 0.6},
        ten_god_group_weights={"officer": 1.2, "resource": 0.9, "wealth": 0.45},
        ten_god_weights={"jeong_gwan": 1.15, "jeong_in": 0.85, "pyeon_gwan": 0.65, "jeong_jae": 0.4},
        axis_weights={"organization_adaptability": 1.2, "honor_recognition": 0.95, "responsibility_capacity": 0.9},
        suitable_fields=("행정", "공공기관", "정책 집행", "민원 조정", "기관 운영"),
        unsuitable_conditions=(
            "규정은 엄격하지만 실무 책임이 개인에게 과도하게 몰리는 자리",
            "절차를 지켜도 인정으로 이어지지 않는 자리",
        ),
        role_style="공식 기준 안에서 책임을 나누고, 문서와 절차로 일을 안정시키는 역할에 맞습니다.",
        income_link="직급, 자격, 근속, 평가 기준이 분명할수록 사회적 안정과 수입 안정이 함께 확보됩니다.",
    ),
    "real_estate_asset_facility": CareerFieldRule(
        key="real_estate_asset_facility",
        label="부동산·자산·시설 관리",
        category="asset_field",
        element_weights={"earth": 1.25, "metal": 0.75, "water": 0.55},
        ten_god_group_weights={"wealth": 1.1, "officer": 0.8, "resource": 0.55},
        ten_god_weights={"jeong_jae": 1.05, "pyeon_jae": 0.8, "jeong_gwan": 0.65, "jeong_in": 0.45},
        axis_weights={"asset_retention": 1.15, "deal_selection": 0.9, "loss_avoidance": 0.85},
        suitable_fields=("부동산 관리", "자산 관리", "시설 관리", "임대 운영", "건설·공간 운영"),
        unsuitable_conditions=(
            "큰돈이 움직이는데 검토 자료와 권리 관계가 불충분한 자리",
            "현장 책임은 크지만 계약 통제권이 없는 자리",
        ),
        role_style="공간, 자산, 계약, 유지 비용을 한꺼번에 보며 오래 남는 가치를 관리하는 일에 적합합니다.",
        income_link="권리 검토, 유지 비용 관리, 장기 계약, 자산 규모가 분명할수록 재물 축적에 유리합니다.",
    ),
    "media_marketing_public": CareerFieldRule(
        key="media_marketing_public",
        label="미디어·홍보·대외 커뮤니케이션",
        category="public_message",
        element_weights={"fire": 1.2, "wood": 0.75, "water": 0.6},
        ten_god_group_weights={"output": 1.2, "wealth": 0.65, "peer": 0.45},
        ten_god_weights={"sang_gwan": 1.2, "sik_sin": 0.75, "pyeon_jae": 0.55, "bi_gyeon": 0.35},
        axis_weights={"communication_expression": 1.2, "interpersonal_influence": 0.9, "reputation_maintenance": 0.7},
        suitable_fields=("홍보", "대외 협력", "미디어 운영", "광고 커뮤니케이션", "커뮤니티 운영"),
        unsuitable_conditions=(
            "노출은 많은데 메시지 권한과 보호 기준이 없는 자리",
            "말의 책임은 개인에게 남고 보상 배분은 불명확한 자리",
        ),
        role_style="사람들의 반응을 읽고, 표현과 관계 관리를 통해 대외 신뢰를 만드는 일에 강점이 있습니다.",
        income_link="평가 지표, 광고비, 계약 범위, 대외 신뢰 관리 책임이 분명할수록 보상이 안정됩니다.",
    ),
    "medical_welfare_care": CareerFieldRule(
        key="medical_welfare_care",
        label="의료·복지·돌봄 서비스",
        category="care_service",
        element_weights={"water": 0.9, "wood": 0.75, "earth": 0.75, "metal": 0.45},
        ten_god_group_weights={"resource": 1.05, "officer": 0.8, "output": 0.55},
        ten_god_weights={"jeong_in": 0.95, "pyeon_in": 0.75, "jeong_gwan": 0.65, "sik_sin": 0.45},
        axis_weights={"responsibility_capacity": 1.0, "conflict_recovery": 0.85, "practical_planning": 0.75},
        suitable_fields=("의료 행정", "복지 서비스", "재활·돌봄", "임상 지원", "보건 교육"),
        unsuitable_conditions=(
            "희생만 요구하고 인력·시간·책임 기준이 부족한 자리",
            "정서적 부담이 누적되는데 회복 시간이 보장되지 않는 자리",
        ),
        role_style="상대의 상태를 살피고 필요한 절차와 도움을 안정적으로 제공하는 일에 맞습니다.",
        income_link="전문 자격, 담당 범위, 근속 평가, 기관의 보호 체계가 갖춰질수록 오래 지속하기 좋습니다.",
    ),
    "entrepreneurship_management": CareerFieldRule(
        key="entrepreneurship_management",
        label="창업·사업 운영·리더십",
        category="independent_business",
        element_weights={"wood": 0.85, "fire": 0.85, "earth": 0.75, "water": 0.55},
        ten_god_group_weights={"wealth": 1.05, "peer": 0.85, "output": 0.8, "officer": 0.45},
        ten_god_weights={"pyeon_jae": 1.05, "geob_jae": 0.75, "sang_gwan": 0.7, "pyeon_gwan": 0.45},
        axis_weights={"business_expansion": 1.2, "leadership_potential": 1.0, "decision_consistency": 0.75},
        suitable_fields=("소규모 창업", "사업 운영", "팀 리더", "브랜드 운영", "신규 사업 책임"),
        unsuitable_conditions=(
            "사람과 돈을 동시에 끌어안지만 회계와 계약 기준이 없는 자리",
            "확장 속도만 빠르고 운영 책임을 나눌 사람이 없는 자리",
        ),
        role_style="기회를 발견하고 사람을 움직여 매출과 운영 체계를 만드는 일에서 수익이 납니다.",
        income_link="계약, 지분, 비용, 권한 배분을 초기에 분명히 할수록 큰 수입을 지킬 수 있습니다.",
    ),
}


CAREER_SUB_ROLE_RULES: dict[str, tuple[CareerSubRoleRule, ...]] = {
    "education_training": (
        CareerSubRoleRule(
            key="education_curriculum",
            label="교육 기획·커리큘럼 설계",
            parent_field_key="education_training",
            element_weights={"wood": 1.0, "water": 0.7, "earth": 0.55},
            ten_god_group_weights={"resource": 1.1, "output": 0.65},
            ten_god_weights={"jeong_in": 1.0, "sik_sin": 0.65},
            axis_weights={"academic_expertise": 1.1, "practical_planning": 0.9},
            work_style_weights={"expert": 1.0, "organization": 0.65},
            role_sentence="가르칠 내용을 체계적으로 나누고, 학습자가 따라올 수 있는 순서로 설계하는 역할",
        ),
        CareerSubRoleRule(
            key="lecture_coaching",
            label="강의·코칭",
            parent_field_key="education_training",
            element_weights={"fire": 1.0, "wood": 0.8},
            ten_god_group_weights={"output": 1.0, "resource": 0.75},
            ten_god_weights={"sik_sin": 0.9, "sang_gwan": 0.75, "jeong_in": 0.55},
            axis_weights={"communication_expression": 1.0, "interpersonal_influence": 0.65},
            work_style_weights={"expert": 0.85, "independent": 0.6},
            role_sentence="지식과 경험을 말과 사례로 풀어내어 사람을 변화시키는 역할",
        ),
        CareerSubRoleRule(
            key="talent_development",
            label="인재 개발·조직 교육",
            parent_field_key="education_training",
            element_weights={"wood": 0.85, "earth": 0.75},
            ten_god_group_weights={"resource": 0.9, "officer": 0.85},
            ten_god_weights={"jeong_in": 0.85, "jeong_gwan": 0.7},
            axis_weights={"organization_adaptability": 1.0, "responsibility_capacity": 0.75},
            work_style_weights={"organization": 0.9, "manager": 0.7},
            role_sentence="사람의 성장 과정을 조직의 목표와 연결해 관리하는 역할",
        ),
    ),
    "planning_content_brand": (
        CareerSubRoleRule(
            key="brand_planning",
            label="브랜드·상품 기획",
            parent_field_key="planning_content_brand",
            element_weights={"wood": 0.9, "fire": 0.85, "earth": 0.45},
            ten_god_group_weights={"output": 1.0, "wealth": 0.75},
            ten_god_weights={"sang_gwan": 0.95, "pyeon_jae": 0.65},
            axis_weights={"communication_expression": 1.0, "business_expansion": 0.8},
            work_style_weights={"independent": 0.85, "expert": 0.55},
            role_sentence="생각과 이미지를 상품의 방향으로 정리하는 역할",
        ),
        CareerSubRoleRule(
            key="content_strategy",
            label="콘텐츠 전략",
            parent_field_key="planning_content_brand",
            element_weights={"fire": 1.0, "water": 0.65},
            ten_god_group_weights={"output": 1.05, "resource": 0.55},
            ten_god_weights={"sang_gwan": 1.0, "pyeon_in": 0.55},
            axis_weights={"communication_expression": 1.1, "academic_expertise": 0.6},
            work_style_weights={"expert": 0.75, "independent": 0.7},
            role_sentence="사람들이 받아들일 만한 주제와 표현 방식을 찾아 콘텐츠로 만드는 역할",
        ),
        CareerSubRoleRule(
            key="marketing_campaign",
            label="마케팅 캠페인 운영",
            parent_field_key="planning_content_brand",
            element_weights={"fire": 0.9, "wood": 0.6},
            ten_god_group_weights={"output": 0.85, "wealth": 0.85},
            ten_god_weights={"sang_gwan": 0.75, "pyeon_jae": 0.7},
            axis_weights={"business_expansion": 0.95, "practical_planning": 0.7},
            work_style_weights={"manager": 0.65, "independent": 0.6},
            role_sentence="목표와 예산을 묶어 실행 결과를 만드는 역할",
        ),
    ),
    "sales_business_development": (
        CareerSubRoleRule(
            key="b2b_sales",
            label="B2B 영업",
            parent_field_key="sales_business_development",
            element_weights={"fire": 0.9, "water": 0.7},
            ten_god_group_weights={"wealth": 1.1, "output": 0.75},
            ten_god_weights={"pyeon_jae": 1.0, "sang_gwan": 0.65},
            axis_weights={"deal_selection": 1.0, "income_expansion": 0.85},
            work_style_weights={"independent": 0.8, "manager": 0.55},
            role_sentence="상대의 필요를 읽고 계약과 매출로 연결하는 역할",
        ),
        CareerSubRoleRule(
            key="partnership_development",
            label="제휴·사업 개발",
            parent_field_key="sales_business_development",
            element_weights={"wood": 0.8, "fire": 0.7, "water": 0.55},
            ten_god_group_weights={"wealth": 1.0, "peer": 0.65},
            ten_god_weights={"pyeon_jae": 0.9, "geob_jae": 0.55},
            axis_weights={"business_expansion": 1.05, "interpersonal_influence": 0.7},
            work_style_weights={"independent": 0.95, "manager": 0.55},
            role_sentence="사람과 조직의 이해관계를 조율하는 역할",
        ),
        CareerSubRoleRule(
            key="account_management",
            label="거래처 관리",
            parent_field_key="sales_business_development",
            element_weights={"earth": 0.75, "water": 0.65},
            ten_god_group_weights={"wealth": 0.95, "officer": 0.55},
            ten_god_weights={"jeong_jae": 0.85, "jeong_gwan": 0.45},
            axis_weights={"asset_retention": 0.8, "relationship_stability": 0.7},
            work_style_weights={"organization": 0.7, "manager": 0.65},
            role_sentence="기존 고객의 요구, 일정, 금액, 신뢰를 안정적으로 관리하는 역할",
        ),
    ),
    "operations_project_management": (
        CareerSubRoleRule(
            key="operations_management",
            label="운영 관리",
            parent_field_key="operations_project_management",
            element_weights={"earth": 1.0, "metal": 0.75},
            ten_god_group_weights={"officer": 1.0, "wealth": 0.55},
            ten_god_weights={"jeong_gwan": 0.9, "jeong_jae": 0.55},
            axis_weights={"organization_adaptability": 1.0, "responsibility_capacity": 0.85},
            work_style_weights={"organization": 0.9, "manager": 0.75},
            role_sentence="일정을 정리해 일이 안정적으로 돌아가게 만드는 역할",
        ),
        CareerSubRoleRule(
            key="project_management",
            label="프로젝트 관리",
            parent_field_key="operations_project_management",
            element_weights={"earth": 0.9, "fire": 0.6},
            ten_god_group_weights={"officer": 0.9, "output": 0.55},
            ten_god_weights={"pyeon_gwan": 0.75, "jeong_gwan": 0.7},
            axis_weights={"responsibility_capacity": 1.0, "practical_planning": 0.9},
            work_style_weights={"manager": 0.95, "organization": 0.75},
            role_sentence="일정과 담당자를 정리해 프로젝트를 끝까지 관리하는 역할",
        ),
        CareerSubRoleRule(
            key="process_improvement",
            label="프로세스 개선",
            parent_field_key="operations_project_management",
            element_weights={"metal": 0.9, "water": 0.6, "earth": 0.55},
            ten_god_group_weights={"resource": 0.85, "output": 0.75},
            ten_god_weights={"pyeon_in": 0.75, "sang_gwan": 0.65},
            axis_weights={"practical_planning": 1.0, "decision_consistency": 0.75},
            work_style_weights={"expert": 0.85, "manager": 0.55},
            role_sentence="비효율을 찾아 절차와 기준을 더 쓰기 좋게 바꾸는 역할",
        ),
    ),
    "finance_accounting_review": (
        CareerSubRoleRule(
            key="accounting_tax",
            label="회계·세무",
            parent_field_key="finance_accounting_review",
            element_weights={"earth": 1.0, "metal": 0.8},
            ten_god_group_weights={"wealth": 1.0, "resource": 0.65},
            ten_god_weights={"jeong_jae": 1.0, "jeong_in": 0.55},
            axis_weights={"asset_retention": 1.05, "spending_control": 0.85},
            work_style_weights={"expert": 0.8, "organization": 0.75},
            role_sentence="숫자, 증빙, 비용, 세금 기준을 정확히 정리하는 역할",
        ),
        CareerSubRoleRule(
            key="financial_review",
            label="금융 심사·리스크 검토",
            parent_field_key="finance_accounting_review",
            element_weights={"metal": 1.0, "water": 0.65},
            ten_god_group_weights={"wealth": 0.9, "officer": 0.85},
            ten_god_weights={"jeong_jae": 0.85, "jeong_gwan": 0.75},
            axis_weights={"loss_avoidance": 1.0, "decision_consistency": 0.75},
            work_style_weights={"expert": 0.8, "organization": 0.7},
            role_sentence="돈이 움직이기 전에 위험, 계약 기준, 회수 여지를 점검하는 역할",
        ),
        CareerSubRoleRule(
            key="settlement_profit",
            label="정산·손익 관리",
            parent_field_key="finance_accounting_review",
            element_weights={"earth": 0.85, "metal": 0.7},
            ten_god_group_weights={"wealth": 1.0, "officer": 0.55},
            ten_god_weights={"jeong_jae": 0.9, "jeong_gwan": 0.45},
            axis_weights={"spending_control": 0.95, "practical_planning": 0.75},
            work_style_weights={"organization": 0.75, "manager": 0.6},
            role_sentence="매출, 비용, 지급 시점, 책임 범위를 분명히 정리하는 역할",
        ),
    ),
    "law_audit_compliance": (
        CareerSubRoleRule(
            key="legal_affairs",
            label="법무",
            parent_field_key="law_audit_compliance",
            element_weights={"metal": 1.05, "water": 0.65},
            ten_god_group_weights={"officer": 1.1, "resource": 0.7},
            ten_god_weights={"jeong_gwan": 1.0, "jeong_in": 0.55},
            axis_weights={"honor_recognition": 0.95, "decision_consistency": 0.75},
            work_style_weights={"expert": 0.85, "organization": 0.7},
            role_sentence="계약, 규정, 책임 범위를 문서와 기준으로 분명히 하는 역할",
        ),
        CareerSubRoleRule(
            key="internal_audit",
            label="내부 감사",
            parent_field_key="law_audit_compliance",
            element_weights={"metal": 1.0, "earth": 0.65},
            ten_god_group_weights={"officer": 1.1, "resource": 0.6},
            ten_god_weights={"pyeon_gwan": 0.85, "jeong_gwan": 0.75},
            axis_weights={"responsibility_capacity": 1.0, "loss_avoidance": 0.75},
            work_style_weights={"organization": 0.8, "expert": 0.75},
            role_sentence="문제가 커지기 전에 절차, 권한, 책임의 허점을 찾아내는 역할",
        ),
        CareerSubRoleRule(
            key="compliance",
            label="컴플라이언스",
            parent_field_key="law_audit_compliance",
            element_weights={"metal": 0.95, "earth": 0.7},
            ten_god_group_weights={"officer": 1.0, "resource": 0.75},
            ten_god_weights={"jeong_gwan": 0.9, "jeong_in": 0.65},
            axis_weights={"reputation_maintenance": 1.0, "organization_adaptability": 0.8},
            work_style_weights={"organization": 0.85, "expert": 0.65},
            role_sentence="조직이 지켜야 할 기준을 실무 안에서 작동하게 만드는 역할",
        ),
    ),
    "data_research_strategy": (
        CareerSubRoleRule(
            key="data_analysis",
            label="데이터 분석",
            parent_field_key="data_research_strategy",
            element_weights={"water": 1.0, "metal": 0.85},
            ten_god_group_weights={"resource": 0.9, "output": 0.75},
            ten_god_weights={"pyeon_in": 0.9, "sang_gwan": 0.65},
            axis_weights={"academic_expertise": 1.0, "decision_consistency": 0.75},
            work_style_weights={"expert": 0.95, "organization": 0.45},
            role_sentence="자료를 해석해 숫자 뒤의 원인과 선택지를 찾아내는 역할",
        ),
        CareerSubRoleRule(
            key="market_research",
            label="시장 조사·리서치",
            parent_field_key="data_research_strategy",
            element_weights={"water": 0.9, "wood": 0.55},
            ten_god_group_weights={"resource": 0.9, "wealth": 0.55},
            ten_god_weights={"pyeon_in": 0.85, "pyeon_jae": 0.45},
            axis_weights={"academic_expertise": 0.85, "deal_selection": 0.65},
            work_style_weights={"expert": 0.85, "independent": 0.45},
            role_sentence="사람, 시장, 경쟁 상황을 조사해 사업 결정의 근거를 만드는 역할",
        ),
        CareerSubRoleRule(
            key="strategy_analysis",
            label="전략 분석",
            parent_field_key="data_research_strategy",
            element_weights={"water": 0.85, "fire": 0.45, "metal": 0.55},
            ten_god_group_weights={"resource": 0.85, "officer": 0.55},
            ten_god_weights={"pyeon_in": 0.75, "jeong_gwan": 0.45},
            axis_weights={"decision_consistency": 0.95, "practical_planning": 0.8},
            work_style_weights={"expert": 0.8, "manager": 0.55},
            role_sentence="복잡한 선택지를 비교해 실행 가능한 결론으로 정리하는 역할",
        ),
    ),
    "technology_quality_system": (
        CareerSubRoleRule(
            key="quality_management",
            label="품질 관리",
            parent_field_key="technology_quality_system",
            element_weights={"metal": 1.0, "earth": 0.65},
            ten_god_group_weights={"officer": 0.85, "resource": 0.75},
            ten_god_weights={"jeong_gwan": 0.75, "jeong_in": 0.65},
            axis_weights={"practical_planning": 0.95, "responsibility_capacity": 0.75},
            work_style_weights={"organization": 0.85, "expert": 0.65},
            role_sentence="결함을 줄이고, 기준에 맞는 결과가 반복되도록 관리하는 역할",
        ),
        CareerSubRoleRule(
            key="system_operations",
            label="시스템 운영",
            parent_field_key="technology_quality_system",
            element_weights={"metal": 0.9, "water": 0.85},
            ten_god_group_weights={"resource": 0.9, "officer": 0.65},
            ten_god_weights={"pyeon_in": 0.8, "jeong_gwan": 0.55},
            axis_weights={"academic_expertise": 0.85, "crisis_recovery": 0.7},
            work_style_weights={"expert": 0.85, "organization": 0.65},
            role_sentence="기술 환경이 안정적으로 유지되도록 원인과 절차를 관리하는 역할",
        ),
        CareerSubRoleRule(
            key="technical_support",
            label="기술 지원·문제 해결",
            parent_field_key="technology_quality_system",
            element_weights={"water": 0.85, "metal": 0.75, "fire": 0.4},
            ten_god_group_weights={"resource": 0.85, "output": 0.65},
            ten_god_weights={"pyeon_in": 0.7, "sik_sin": 0.55},
            axis_weights={"communication_expression": 0.75, "conflict_recovery": 0.65},
            work_style_weights={"expert": 0.75, "manager": 0.45},
            role_sentence="문제 상황을 듣고 원인을 찾아 실제 해결까지 연결하는 역할",
        ),
    ),
    "counseling_hr_client_success": (
        CareerSubRoleRule(
            key="counseling_coaching",
            label="상담·코칭",
            parent_field_key="counseling_hr_client_success",
            element_weights={"water": 0.85, "wood": 0.75},
            ten_god_group_weights={"resource": 0.95, "output": 0.55},
            ten_god_weights={"jeong_in": 0.85, "sik_sin": 0.45},
            axis_weights={"interpersonal_influence": 0.9, "boundary_management": 0.8},
            work_style_weights={"expert": 0.75, "organization": 0.45},
            role_sentence="상대의 말을 듣고 감정과 현실 문제를 정리해주는 역할",
        ),
        CareerSubRoleRule(
            key="hr_people_ops",
            label="HR·인사 운영",
            parent_field_key="counseling_hr_client_success",
            element_weights={"earth": 0.75, "wood": 0.65},
            ten_god_group_weights={"officer": 0.8, "resource": 0.75},
            ten_god_weights={"jeong_gwan": 0.65, "jeong_in": 0.65},
            axis_weights={"organization_adaptability": 0.95, "conflict_recovery": 0.75},
            work_style_weights={"organization": 0.85, "manager": 0.6},
            role_sentence="사람의 배치, 평가, 갈등, 적응 문제를 조직 기준 안에서 다루는 역할",
        ),
        CareerSubRoleRule(
            key="client_success",
            label="고객 성공 관리",
            parent_field_key="counseling_hr_client_success",
            element_weights={"water": 0.75, "fire": 0.6, "earth": 0.5},
            ten_god_group_weights={"output": 0.75, "wealth": 0.65},
            ten_god_weights={"sik_sin": 0.65, "jeong_jae": 0.45},
            axis_weights={"relationship_stability": 0.8, "income_expansion": 0.65},
            work_style_weights={"manager": 0.65, "organization": 0.55},
            role_sentence="고객의 사용 경험을 관리하고 장기 관계와 재구매를 만드는 역할",
        ),
    ),
    "public_administration_institution": (
        CareerSubRoleRule(
            key="administration",
            label="행정·문서 업무",
            parent_field_key="public_administration_institution",
            element_weights={"earth": 1.0, "metal": 0.75},
            ten_god_group_weights={"officer": 1.0, "resource": 0.7},
            ten_god_weights={"jeong_gwan": 0.9, "jeong_in": 0.6},
            axis_weights={"organization_adaptability": 1.0, "practical_planning": 0.75},
            work_style_weights={"organization": 1.0, "expert": 0.45},
            role_sentence="문서, 절차, 기준을 정확히 정리해 기관의 일을 안정시키는 역할",
        ),
        CareerSubRoleRule(
            key="policy_execution",
            label="정책 집행",
            parent_field_key="public_administration_institution",
            element_weights={"earth": 0.9, "fire": 0.45},
            ten_god_group_weights={"officer": 1.0, "wealth": 0.45},
            ten_god_weights={"jeong_gwan": 0.85, "pyeon_gwan": 0.55},
            axis_weights={"responsibility_capacity": 0.95, "honor_recognition": 0.7},
            work_style_weights={"organization": 0.9, "manager": 0.55},
            role_sentence="공식 기준을 실제 현장과 대상자에게 적용하는 역할",
        ),
        CareerSubRoleRule(
            key="civil_coordination",
            label="민원·이해관계 조정",
            parent_field_key="public_administration_institution",
            element_weights={"water": 0.7, "earth": 0.65},
            ten_god_group_weights={"officer": 0.8, "output": 0.55},
            ten_god_weights={"jeong_gwan": 0.7, "sik_sin": 0.45},
            axis_weights={"conflict_recovery": 0.9, "interpersonal_influence": 0.65},
            work_style_weights={"manager": 0.7, "organization": 0.65},
            role_sentence="서로 다른 요구를 듣고 규정 안에서 현실적인 결론을 만드는 역할",
        ),
    ),
    "real_estate_asset_facility": (
        CareerSubRoleRule(
            key="real_estate_management",
            label="부동산·임대 관리",
            parent_field_key="real_estate_asset_facility",
            element_weights={"earth": 1.05, "metal": 0.55},
            ten_god_group_weights={"wealth": 1.0, "officer": 0.55},
            ten_god_weights={"jeong_jae": 0.85, "jeong_gwan": 0.45},
            axis_weights={"asset_retention": 1.0, "deal_selection": 0.75},
            work_style_weights={"organization": 0.7, "manager": 0.6},
            role_sentence="계약, 권리, 임대 조건, 유지 비용을 안정적으로 관리하는 역할",
        ),
        CareerSubRoleRule(
            key="asset_management",
            label="자산 관리",
            parent_field_key="real_estate_asset_facility",
            element_weights={"earth": 0.95, "water": 0.55},
            ten_god_group_weights={"wealth": 1.05, "resource": 0.55},
            ten_god_weights={"jeong_jae": 0.85, "pyeon_jae": 0.55},
            axis_weights={"asset_retention": 1.05, "loss_avoidance": 0.75},
            work_style_weights={"expert": 0.65, "organization": 0.6},
            role_sentence="돈과 자산이 새지 않도록 보유, 운용, 위험을 관리하는 역할",
        ),
        CareerSubRoleRule(
            key="facility_operations",
            label="시설·공간 운영",
            parent_field_key="real_estate_asset_facility",
            element_weights={"earth": 0.9, "metal": 0.65},
            ten_god_group_weights={"officer": 0.8, "wealth": 0.65},
            ten_god_weights={"jeong_gwan": 0.65, "jeong_jae": 0.55},
            axis_weights={"practical_planning": 0.85, "responsibility_capacity": 0.75},
            work_style_weights={"manager": 0.7, "organization": 0.65},
            role_sentence="공간, 설비, 비용, 현장 책임을 일상적으로 점검하는 역할",
        ),
    ),
    "media_marketing_public": (
        CareerSubRoleRule(
            key="public_relations",
            label="홍보·대외 협력",
            parent_field_key="media_marketing_public",
            element_weights={"fire": 1.0, "wood": 0.55},
            ten_god_group_weights={"output": 1.0, "wealth": 0.45},
            ten_god_weights={"sang_gwan": 0.95, "pyeon_jae": 0.35},
            axis_weights={"communication_expression": 1.05, "reputation_maintenance": 0.75},
            work_style_weights={"independent": 0.65, "manager": 0.45},
            role_sentence="조직이나 상품의 이미지를 외부에 설득력 있게 전달하는 역할",
        ),
        CareerSubRoleRule(
            key="media_operations",
            label="미디어 운영",
            parent_field_key="media_marketing_public",
            element_weights={"fire": 1.0, "water": 0.55},
            ten_god_group_weights={"output": 1.0, "resource": 0.45},
            ten_god_weights={"sang_gwan": 0.9, "pyeon_in": 0.35},
            axis_weights={"communication_expression": 1.0, "practical_planning": 0.55},
            work_style_weights={"expert": 0.6, "independent": 0.55},
            role_sentence="콘텐츠, 노출 일정, 반응을 관리해 전달력을 높이는 역할",
        ),
        CareerSubRoleRule(
            key="community_management",
            label="커뮤니티 운영",
            parent_field_key="media_marketing_public",
            element_weights={"fire": 0.75, "water": 0.65, "wood": 0.45},
            ten_god_group_weights={"output": 0.75, "peer": 0.65},
            ten_god_weights={"sang_gwan": 0.65, "bi_gyeon": 0.45},
            axis_weights={"interpersonal_influence": 0.9, "boundary_management": 0.7},
            work_style_weights={"manager": 0.6, "independent": 0.5},
            role_sentence="사람들의 반응과 관계 기준을 관리해 참여를 유지하는 역할",
        ),
    ),
    "medical_welfare_care": (
        CareerSubRoleRule(
            key="medical_administration",
            label="의료 행정",
            parent_field_key="medical_welfare_care",
            element_weights={"earth": 0.9, "metal": 0.65},
            ten_god_group_weights={"officer": 0.9, "resource": 0.75},
            ten_god_weights={"jeong_gwan": 0.75, "jeong_in": 0.65},
            axis_weights={"responsibility_capacity": 0.95, "organization_adaptability": 0.75},
            work_style_weights={"organization": 0.9, "expert": 0.55},
            role_sentence="절차, 기록, 일정, 책임 기준을 정확히 정리하는 역할",
        ),
        CareerSubRoleRule(
            key="welfare_service",
            label="복지 서비스",
            parent_field_key="medical_welfare_care",
            element_weights={"water": 0.85, "wood": 0.65},
            ten_god_group_weights={"resource": 0.9, "officer": 0.6},
            ten_god_weights={"jeong_in": 0.8, "jeong_gwan": 0.45},
            axis_weights={"conflict_recovery": 0.9, "interpersonal_influence": 0.65},
            work_style_weights={"organization": 0.7, "expert": 0.6},
            role_sentence="도움이 필요한 사람의 상태와 제도적 지원을 연결하는 역할",
        ),
        CareerSubRoleRule(
            key="health_education",
            label="보건 교육·재활 지원",
            parent_field_key="medical_welfare_care",
            element_weights={"wood": 0.75, "water": 0.65, "fire": 0.45},
            ten_god_group_weights={"resource": 0.85, "output": 0.65},
            ten_god_weights={"jeong_in": 0.75, "sik_sin": 0.55},
            axis_weights={"academic_expertise": 0.8, "communication_expression": 0.65},
            work_style_weights={"expert": 0.75, "organization": 0.5},
            role_sentence="상대가 회복하고 생활 습관을 바꿀 수 있도록 설명하고 돕는 역할",
        ),
    ),
    "entrepreneurship_management": (
        CareerSubRoleRule(
            key="small_business_operations",
            label="소규모 창업·운영",
            parent_field_key="entrepreneurship_management",
            element_weights={"wood": 0.8, "earth": 0.65, "fire": 0.55},
            ten_god_group_weights={"wealth": 1.0, "output": 0.65},
            ten_god_weights={"pyeon_jae": 0.85, "sang_gwan": 0.55},
            axis_weights={"business_expansion": 1.0, "decision_consistency": 0.75},
            work_style_weights={"independent": 1.0, "manager": 0.55},
            role_sentence="아이템, 비용, 고객, 운영을 직접 묶어 매출을 만드는 역할",
        ),
        CareerSubRoleRule(
            key="team_leadership",
            label="팀 리더십",
            parent_field_key="entrepreneurship_management",
            element_weights={"fire": 0.75, "earth": 0.7},
            ten_god_group_weights={"peer": 0.8, "officer": 0.7},
            ten_god_weights={"bi_gyeon": 0.65, "pyeon_gwan": 0.55},
            axis_weights={"leadership_potential": 1.05, "responsibility_capacity": 0.8},
            work_style_weights={"manager": 0.9, "independent": 0.55},
            role_sentence="사람을 모으고 역할을 나누어 결과를 책임지는 역할",
        ),
        CareerSubRoleRule(
            key="new_business_owner",
            label="신규 사업 책임",
            parent_field_key="entrepreneurship_management",
            element_weights={"wood": 0.85, "fire": 0.75, "water": 0.45},
            ten_god_group_weights={"wealth": 0.95, "peer": 0.6, "output": 0.6},
            ten_god_weights={"pyeon_jae": 0.85, "geob_jae": 0.45, "sang_gwan": 0.45},
            axis_weights={"business_expansion": 1.05, "practical_planning": 0.65},
            work_style_weights={"independent": 0.95, "manager": 0.65},
            role_sentence="새 기회를 검토하고 사람과 자원을 배치해 사업으로 만드는 역할",
        ),
    ),
}


def _clip(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _element_strength(element_profile: ElementProfile, element: str) -> float:
    score = element_profile.scores[element]
    state_value = {
        "dominant": 7.5,
        "strong": 6.0,
        "balanced": 4.0,
        "weak": 1.4,
        "absent": -4.0,
    }[score.state]
    exposure_value = {"clear": 2.0, "present": 1.2, "hidden": 0.3, "absent": -1.2}[score.exposure]
    useful_delta = 1.6 if element in element_profile.useful_elements else 0.0
    caution_delta = -1.8 if element in element_profile.caution_elements else 0.0
    return state_value + exposure_value + useful_delta + caution_delta


def _ten_god_total(ten_god_profile: TenGodProfile, ten_god: str) -> float:
    return float(ten_god_profile.visible_counts.get(ten_god, 0.0)) + float(
        ten_god_profile.hidden_counts.get(ten_god, 0.0)
    ) * 0.7


def _group_weight_for_ten_god(rule: CareerFieldRule, ten_god: str) -> float:
    group = TEN_GOD_GROUPS.get(ten_god)
    if group is None:
        return 0.0
    return float(rule.ten_god_group_weights.get(group, 0.0))


def _rule_ten_gods(rule: CareerFieldRule) -> set[str]:
    return set(rule.ten_god_weights)


def _score_elements(rule: CareerFieldRule, element_profile: ElementProfile) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for element, weight in rule.element_weights.items():
        element_delta = _element_strength(element_profile, element) * weight
        delta += element_delta
        element_score = element_profile.scores[element]
        if element_score.state in {"balanced", "strong", "dominant"}:
            basis_codes.append(f"career_field_element_{rule.key}_{element}_{element_score.state}")
        if element_score.state in {"weak", "absent"} and weight >= 0.7:
            counter_signals.append(f"career_field_element_weak_{rule.key}_{element}")
        if element in element_profile.caution_elements and weight >= 0.7:
            counter_signals.append(f"career_field_element_caution_{rule.key}_{element}")
    return delta, basis_codes, counter_signals


def _score_ten_gods(rule: CareerFieldRule, ten_god_profile: TenGodProfile) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for group, weight in rule.ten_god_group_weights.items():
        group_score = float(ten_god_profile.group_scores.get(group, 0.0))
        delta += min(9.0, group_score * 3.2) * weight
        if group_score >= 1.1:
            basis_codes.append(f"career_field_ten_god_group_{rule.key}_{group}")
        elif group_score <= 0.32 and weight >= 0.7:
            counter_signals.append(f"career_field_ten_god_group_low_{rule.key}_{group}")
    for ten_god, weight in rule.ten_god_weights.items():
        total = _ten_god_total(ten_god_profile, ten_god)
        delta += min(7.0, total * 3.6) * weight
        if total >= 0.65:
            basis_codes.append(f"career_field_ten_god_{rule.key}_{ten_god}")
        elif total <= 0.15 and weight >= 0.75:
            counter_signals.append(f"career_field_ten_god_low_{rule.key}_{ten_god}")
    return delta, basis_codes, counter_signals


def _score_positions(
    rule: CareerFieldRule,
    *,
    day_master_stem: str,
    position_signals: dict[str, PositionSignal],
) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    position_weights = {"year": 0.8, "month": 2.2, "day": 1.55, "hour": 1.25}
    for position, signal in position_signals.items():
        position_weight = position_weights.get(position, 0.6)
        stem_element_weight = rule.element_weights.get(signal.stem_element, 0.0)
        branch_element_weight = rule.element_weights.get(signal.branch_element, 0.0)
        if stem_element_weight:
            delta += position_weight * stem_element_weight
            basis_codes.append(f"career_field_position_stem_{rule.key}_{position}_{signal.stem_element}")
        if branch_element_weight:
            delta += position_weight * branch_element_weight * 0.75
            basis_codes.append(f"career_field_position_branch_{rule.key}_{position}_{signal.branch_element}")
        for ten_god in (signal.stem_ten_god, signal.branch_main_ten_god, *signal.hidden_ten_gods):
            if ten_god == "self":
                continue
            ten_god_weight = rule.ten_god_weights.get(ten_god, 0.0) + _group_weight_for_ten_god(rule, ten_god) * 0.45
            if ten_god_weight:
                delta += position_weight * ten_god_weight * 0.75
                basis_codes.append(f"career_field_position_ten_god_{rule.key}_{position}_{ten_god}")
        for stem_key in signal.protruded_hidden_stems:
            stem_element = STEM_METADATA[stem_key]["element"]
            protruded_ten_god = ten_god_for(day_master_stem, stem_key)
            protruded_weight = rule.element_weights.get(stem_element, 0.0) + rule.ten_god_weights.get(
                protruded_ten_god, 0.0
            )
            protruded_weight += _group_weight_for_ten_god(rule, protruded_ten_god) * 0.4
            if protruded_weight:
                delta += position_weight * protruded_weight * 0.65
                basis_codes.append(f"career_field_protruded_hidden_{rule.key}_{position}_{stem_key}")
        if position == "month":
            if "career" in signal.domains or "social_role" in signal.domains:
                delta += 1.2
                basis_codes.append(f"career_field_month_role_anchor_{rule.key}")
            if not any(
                ten_god in _rule_ten_gods(rule) or _group_weight_for_ten_god(rule, ten_god)
                for ten_god in (signal.stem_ten_god, signal.branch_main_ten_god, *signal.hidden_ten_gods)
                if ten_god != "self"
            ):
                counter_signals.append(f"career_field_month_role_weak_{rule.key}")
    return delta, basis_codes, counter_signals


def _score_day_month_context(
    rule: CareerFieldRule,
    *,
    day_master_stem: str,
    element_profile: ElementProfile,
    position_signals: dict[str, PositionSignal],
) -> tuple[float, list[str], list[str], str, str, str]:
    day_element = STEM_METADATA[day_master_stem]["element"]
    month_branch = element_profile.month_branch
    month_signal = position_signals.get("month")
    month_element = (
        month_signal.branch_element if month_signal is not None else BRANCH_METADATA[month_branch]["element"]
    )
    season_modifiers = MONTH_SEASON_MODIFIERS[month_branch]
    weight_sum = sum(abs(weight) for weight in rule.element_weights.values()) or 1.0
    seasonal_fit = sum(
        rule.element_weights[element] * season_modifiers[element]
        for element in rule.element_weights
    ) / weight_sum

    delta = 0.0
    basis_codes: list[str] = [f"career_field_day_month_context_{rule.key}_{day_master_stem}_{month_branch}"]
    counter_signals: list[str] = []

    day_weight = rule.element_weights.get(day_element, 0.0)
    if day_weight >= 0.75:
        delta += 0.9 * day_weight
        basis_codes.append(f"career_field_day_master_fit_{rule.key}_{day_master_stem}_{day_element}")
    elif day_weight <= 0.15 and max(rule.element_weights.values()) >= 1.0:
        delta -= 0.25
        counter_signals.append(f"career_field_day_master_indirect_fit_{rule.key}_{day_master_stem}_{day_element}")

    month_weight = rule.element_weights.get(month_element, 0.0)
    if month_weight >= 0.7:
        delta += 1.05 * month_weight
        basis_codes.append(f"career_field_month_element_fit_{rule.key}_{month_branch}_{month_element}")
    elif month_weight <= 0.15 and max(rule.element_weights.values()) >= 1.0:
        delta -= 0.35
        counter_signals.append(f"career_field_month_element_indirect_fit_{rule.key}_{month_branch}_{month_element}")

    if seasonal_fit >= 1.12:
        delta += 1.0
        basis_codes.append(f"career_field_month_command_support_{rule.key}_{month_branch}")
    elif seasonal_fit <= 0.82:
        delta -= 0.75
        counter_signals.append(f"career_field_month_command_low_support_{rule.key}_{month_branch}")
    else:
        basis_codes.append(f"career_field_month_command_neutral_{rule.key}_{month_branch}")

    day_master_fit_mode = DAY_MASTER_CAREER_MODES[day_master_stem]
    seasonal_fit_note = MONTH_BRANCH_CAREER_NOTES[month_branch]
    fit_context_sentence = f"당신은 {rule.label} 분야를 맡을 때 {day_master_fit_mode} {seasonal_fit_note}"
    return delta, basis_codes, counter_signals, day_master_fit_mode, seasonal_fit_note, fit_context_sentence


def _score_life_axes(rule: CareerFieldRule, life_feature_profile: LifeFeatureProfile) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for axis_key, weight in rule.axis_weights.items():
        axis = life_feature_profile.axes.get(axis_key)
        if axis is None:
            continue
        delta += ((axis.score - 50) / 10) * weight
        if axis.score >= 66:
            basis_codes.append(f"career_field_life_axis_{rule.key}_{axis_key}")
        elif axis.score <= 43 and weight >= 0.75:
            counter_signals.append(f"career_field_life_axis_low_{rule.key}_{axis_key}")
    return delta, basis_codes, counter_signals


def _score_branch_interactions(rule: CareerFieldRule, branch_interactions: list[BranchInteraction]) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []
    for interaction in branch_interactions:
        related_to_work = "career" in interaction.domain_links or any(
            position in {"month", "year", "hour"} for position in interaction.positions
        )
        if not related_to_work:
            continue
        intensity = {"strong": 1.35, "moderate": 1.0, "low": 0.65}.get(interaction.intensity, 0.8)
        if interaction.relation_type in POSITIVE_BRANCH_RELATIONS:
            delta += 1.6 * intensity
            basis_codes.append(f"career_field_branch_relation_{rule.key}_{interaction.relation_type}")
        elif interaction.relation_type in NEGATIVE_BRANCH_RELATIONS:
            pressure = 2.1 * intensity
            if "month" in interaction.positions or "day" in interaction.positions:
                pressure += 0.9
            delta -= pressure
            counter_signals.append(f"career_field_branch_pressure_{rule.key}_{interaction.relation_type}")
    return delta, basis_codes, counter_signals


def _score_combination_profiles(
    rule: CareerFieldRule,
    element_combination_profile: ElementCombinationProfile,
    ten_god_interaction_profile: TenGodInteractionProfile,
    stem_reception_profile: StemReceptionProfile,
    integrated_saju_profile: IntegratedSajuProfile,
) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    basis_codes: list[str] = []
    counter_signals: list[str] = []

    element_top_ids = set(element_combination_profile.top_signal_ids)
    element_signals = (
        list(element_combination_profile.heavenly_stem_signals)
        + list(element_combination_profile.stem_branch_signals)
        + list(element_combination_profile.hidden_stem_signals)
    )
    for signal in element_signals:
        if signal.signal_id not in element_top_ids or not {"career", "money"}.intersection(signal.domain_links):
            continue
        overlap = sum(rule.element_weights.get(element, 0.0) for element in signal.elements)
        if overlap:
            strength = {"high": 1.4, "moderate": 1.0, "low": 0.55}.get(signal.strength, 0.8)
            delta += overlap * strength
            basis_codes.append(f"career_field_element_combo_{rule.key}_{signal.relation_type}")
            if signal.counter_signals:
                counter_signals.append(f"career_field_element_combo_counter_{rule.key}_{signal.signal_id}")

    ten_god_top_ids = set(ten_god_interaction_profile.top_signal_ids)
    ten_god_signals = (
        list(ten_god_interaction_profile.visible_stem_signals)
        + list(ten_god_interaction_profile.stem_branch_signals)
        + list(ten_god_interaction_profile.hidden_stem_signals)
    )
    for signal in ten_god_signals:
        if signal.signal_id not in ten_god_top_ids or not {"career", "money"}.intersection(signal.domain_links):
            continue
        relevant_weight = (
            rule.ten_god_weights.get(signal.source_ten_god, 0.0)
            + rule.ten_god_weights.get(signal.target_ten_god, 0.0)
            + _group_weight_for_ten_god(rule, signal.source_ten_god) * 0.4
            + _group_weight_for_ten_god(rule, signal.target_ten_god) * 0.4
        )
        if relevant_weight:
            strength = {"high": 1.25, "moderate": 0.9, "low": 0.45}.get(signal.strength, 0.75)
            delta += relevant_weight * strength
            basis_codes.append(f"career_field_ten_god_interaction_{rule.key}_{signal.direction_key}")
            if signal.counter_signals:
                counter_signals.append(f"career_field_ten_god_interaction_counter_{rule.key}_{signal.signal_id}")

    reception_top_ids = set(stem_reception_profile.top_signal_ids)
    reception_signals = (
        list(stem_reception_profile.visible_stem_signals)
        + list(stem_reception_profile.branch_main_signals)
        + list(stem_reception_profile.hidden_stem_signals)
    )
    for signal in reception_signals:
        if signal.signal_id not in reception_top_ids or "career" not in signal.domain_links:
            continue
        relevant_weight = rule.ten_god_weights.get(signal.target_ten_god, 0.0) + _group_weight_for_ten_god(
            rule, signal.target_ten_god
        ) * 0.55
        if relevant_weight:
            delta += relevant_weight * (1.2 + min(signal.priority_score, 90) / 100)
            basis_codes.append(f"career_field_stem_reception_{rule.key}_{signal.target_stem}_{signal.target_ten_god}")
            if signal.counter_signals:
                counter_signals.append(f"career_field_stem_reception_counter_{rule.key}_{signal.signal_id}")

    integrated_top_ids = set(integrated_saju_profile.top_signal_ids)
    integrated_signals = (
        list(integrated_saju_profile.visible_pair_signals)
        + list(integrated_saju_profile.stem_branch_pair_signals)
        + list(integrated_saju_profile.hidden_pair_signals)
    )
    for signal in integrated_signals:
        if signal.signal_id not in integrated_top_ids or "career" not in signal.domain_links:
            continue
        relevant_weight = (
            rule.element_weights.get(signal.source_element, 0.0)
            + rule.element_weights.get(signal.target_element, 0.0)
            + rule.ten_god_weights.get(signal.source_ten_god, 0.0)
            + rule.ten_god_weights.get(signal.target_ten_god, 0.0)
        )
        if relevant_weight:
            delta += relevant_weight * (0.65 + min(signal.priority_score, 90) / 140)
            basis_codes.append(f"career_field_integrated_saju_{rule.key}_{signal.source_stem}_{signal.target_stem}")
            if signal.counter_signals:
                counter_signals.append(f"career_field_integrated_saju_counter_{rule.key}_{signal.signal_id}")

    return delta, basis_codes, counter_signals


def _score_work_style(
    rule: CareerWorkStyleRule,
    *,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    branch_interactions: list[BranchInteraction],
    life_feature_profile: LifeFeatureProfile,
) -> CareerWorkStyleScore:
    score = 36.0
    basis_codes: list[str] = [f"career_work_style_rule_{rule.key}"]
    counter_signals: list[str] = []

    element_delta = 0.0
    for element, weight in rule.element_weights.items():
        element_delta += _element_strength(element_profile, element) * weight
        element_score = element_profile.scores[element]
        if element_score.state in {"balanced", "strong", "dominant"}:
            basis_codes.append(f"career_work_style_element_{rule.key}_{element}_{element_score.state}")
        elif element_score.state in {"weak", "absent"} and weight >= 0.75:
            counter_signals.append(f"career_work_style_element_low_{rule.key}_{element}")
    score += element_delta * 0.55

    ten_god_delta = 0.0
    for group, weight in rule.ten_god_group_weights.items():
        group_score = float(ten_god_profile.group_scores.get(group, 0.0))
        ten_god_delta += min(9.0, group_score * 3.2) * weight
        if group_score >= 1.1:
            basis_codes.append(f"career_work_style_ten_god_group_{rule.key}_{group}")
    for ten_god, weight in rule.ten_god_weights.items():
        total = _ten_god_total(ten_god_profile, ten_god)
        ten_god_delta += min(7.0, total * 3.6) * weight
        if total >= 0.65:
            basis_codes.append(f"career_work_style_ten_god_{rule.key}_{ten_god}")
    score += ten_god_delta * 0.45

    for axis_key, weight in rule.axis_weights.items():
        axis = life_feature_profile.axes.get(axis_key)
        if axis is None:
            continue
        score += ((axis.score - 50) / 10) * weight * 0.85
        if axis.score >= 66:
            basis_codes.append(f"career_work_style_axis_{rule.key}_{axis_key}")
        elif axis.score <= 43 and weight >= 0.75:
            counter_signals.append(f"career_work_style_axis_low_{rule.key}_{axis_key}")

    month_signal = position_signals.get("month")
    if month_signal is not None:
        for ten_god in (month_signal.stem_ten_god, month_signal.branch_main_ten_god, *month_signal.hidden_ten_gods):
            if ten_god == "self":
                continue
            group_weight = _group_weight_for_ten_god(
                CareerFieldRule(
                    key=rule.key,
                    label=rule.label,
                    category="work_style",
                    element_weights=rule.element_weights,
                    ten_god_group_weights=rule.ten_god_group_weights,
                    ten_god_weights=rule.ten_god_weights,
                    axis_weights=rule.axis_weights,
                    suitable_fields=(),
                    unsuitable_conditions=(),
                    role_style=rule.role_sentence,
                    income_link="",
                ),
                ten_god,
            )
            direct_weight = rule.ten_god_weights.get(ten_god, 0.0)
            if group_weight or direct_weight:
                score += (group_weight * 0.65 + direct_weight) * 1.1
                basis_codes.append(f"career_work_style_month_{rule.key}_{ten_god}")

    for interaction in branch_interactions:
        if not ("career" in interaction.domain_links or "month" in interaction.positions):
            continue
        if interaction.relation_type in POSITIVE_BRANCH_RELATIONS:
            score += 1.1
            basis_codes.append(f"career_work_style_branch_support_{rule.key}_{interaction.relation_type}")
        elif interaction.relation_type in NEGATIVE_BRANCH_RELATIONS:
            score -= 1.3
            counter_signals.append(f"career_work_style_branch_pressure_{rule.key}_{interaction.relation_type}")

    final_score = _clip(score)
    strength = _strength_label(final_score)
    if final_score >= 78 and len(basis_codes) >= 6:
        confidence: Confidence = "medium_high"
    elif final_score >= 58 and len(basis_codes) >= 4:
        confidence = "medium"
    elif final_score >= 45:
        confidence = "low"
    else:
        confidence = "restricted"
    if final_score >= 72:
        style_phrase = "강합니다"
    elif final_score >= 58:
        style_phrase = "비교적 분명합니다"
    elif final_score >= 52:
        style_phrase = "어느 정도 맞습니다"
    else:
        style_phrase = "보조 참고에 가깝습니다"
    customer_sentence = f"당신은 {rule.label} 업무 성향이 {style_phrase}. {rule.role_sentence}"
    return CareerWorkStyleScore(
        key=rule.key,
        label=rule.label,
        score=final_score,
        strength_label=strength,
        confidence=confidence,
        role_sentence=rule.role_sentence,
        basis_codes=_dedupe(basis_codes)[:12],
        counter_signals=_dedupe(counter_signals)[:8],
        customer_sentence=customer_sentence,
    )


def _build_work_style_scores(
    *,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    branch_interactions: list[BranchInteraction],
    life_feature_profile: LifeFeatureProfile,
) -> dict[str, CareerWorkStyleScore]:
    return {
        key: _score_work_style(
            rule,
            element_profile=element_profile,
            ten_god_profile=ten_god_profile,
            position_signals=position_signals,
            branch_interactions=branch_interactions,
            life_feature_profile=life_feature_profile,
        )
        for key, rule in CAREER_WORK_STYLE_RULES.items()
    }


def _sub_role_score(
    parent_rule: CareerFieldRule,
    parent_score: int,
    sub_rule: CareerSubRoleRule,
    *,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    life_feature_profile: LifeFeatureProfile,
    work_styles: dict[str, CareerWorkStyleScore],
) -> CareerSubRoleScore:
    score = 18.0 + parent_score * 0.45
    basis_codes: list[str] = [f"career_sub_role_rule_{parent_rule.key}_{sub_rule.key}"]
    counter_signals: list[str] = []

    for element, weight in sub_rule.element_weights.items():
        score += _element_strength(element_profile, element) * weight * 0.42
        element_score = element_profile.scores[element]
        if element_score.state in {"balanced", "strong", "dominant"}:
            basis_codes.append(f"career_sub_role_element_{sub_rule.key}_{element}_{element_score.state}")
        elif element_score.state in {"weak", "absent"} and weight >= 0.75:
            counter_signals.append(f"career_sub_role_element_low_{sub_rule.key}_{element}")

    for group, weight in sub_rule.ten_god_group_weights.items():
        group_score = float(ten_god_profile.group_scores.get(group, 0.0))
        score += min(8.0, group_score * 3.0) * weight * 0.4
        if group_score >= 1.1:
            basis_codes.append(f"career_sub_role_ten_god_group_{sub_rule.key}_{group}")
    for ten_god, weight in sub_rule.ten_god_weights.items():
        total = _ten_god_total(ten_god_profile, ten_god)
        score += min(7.0, total * 3.4) * weight * 0.38
        if total >= 0.65:
            basis_codes.append(f"career_sub_role_ten_god_{sub_rule.key}_{ten_god}")

    for axis_key, weight in sub_rule.axis_weights.items():
        axis = life_feature_profile.axes.get(axis_key)
        if axis is None:
            continue
        score += ((axis.score - 50) / 10) * weight * 0.8
        if axis.score >= 66:
            basis_codes.append(f"career_sub_role_axis_{sub_rule.key}_{axis_key}")
        elif axis.score <= 43 and weight >= 0.75:
            counter_signals.append(f"career_sub_role_axis_low_{sub_rule.key}_{axis_key}")

    for style_key, weight in sub_rule.work_style_weights.items():
        style = work_styles.get(style_key)
        if style is None:
            continue
        score += ((style.score - 50) / 10) * weight * 0.8
        if style.score >= 66:
            basis_codes.append(f"career_sub_role_work_style_{sub_rule.key}_{style_key}")
        elif style.score <= 43:
            counter_signals.append(f"career_sub_role_work_style_low_{sub_rule.key}_{style_key}")

    final_score = _clip(score)
    strength = _strength_label(final_score)
    confidence = _confidence(final_score, len(basis_codes), len(counter_signals))
    return CareerSubRoleScore(
        key=sub_rule.key,
        label=sub_rule.label,
        parent_field_key=sub_rule.parent_field_key,
        score=final_score,
        strength_label=strength,
        confidence=confidence,
        work_style_links=list(sub_rule.work_style_weights),
        role_sentence=sub_rule.role_sentence,
        basis_codes=_dedupe(basis_codes)[:10],
        counter_signals=_dedupe(counter_signals)[:6],
    )


def _build_sub_role_scores(
    parent_rule: CareerFieldRule,
    parent_score: int,
    *,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    life_feature_profile: LifeFeatureProfile,
    work_styles: dict[str, CareerWorkStyleScore],
) -> list[CareerSubRoleScore]:
    sub_rules = CAREER_SUB_ROLE_RULES[parent_rule.key]
    scores = [
        _sub_role_score(
            parent_rule,
            parent_score,
            sub_rule,
            element_profile=element_profile,
            ten_god_profile=ten_god_profile,
            life_feature_profile=life_feature_profile,
            work_styles=work_styles,
        )
        for sub_rule in sub_rules
    ]
    return sorted(scores, key=lambda item: item.score, reverse=True)


def _strength_label(score: int) -> str:
    if score >= 82:
        return "매우 강한 적합"
    if score >= 70:
        return "높은 적합"
    if score >= 58:
        return "선별 활용 가능"
    if score >= 46:
        return "선별 필요"
    return "주의 필요"


def _confidence(score: int, basis_count: int, counter_count: int) -> Confidence:
    if score >= 84 and basis_count >= 8 and counter_count <= 8:
        return "high"
    if score >= 84 and basis_count >= 8:
        return "medium_high"
    if score >= 76 and basis_count >= 6:
        return "medium_high"
    if score >= 70 and basis_count >= 6 and counter_count <= 10:
        return "medium_high"
    if score >= 58 and basis_count >= 4:
        return "medium"
    if score >= 45:
        return "low"
    return "restricted"


def _customer_sentence(
    rule: CareerFieldRule,
    score: int,
    *,
    display_priority: str,
    top_sub_role: CareerSubRoleScore,
    top_work_style: CareerWorkStyleScore,
    primary_unsuitable_condition: str,
    fit_context_sentence: str,
) -> str:
    if display_priority == "primary":
        sentence = (
            f"당신에게 {rule.label} 분야는 매우 잘 맞는 편입니다. "
            f"{rule.role_style} {fit_context_sentence} 현재 직업이 이 분야와 다르더라도, "
            f"업무 안에서 {top_sub_role.label}처럼 {top_sub_role.role_sentence}을 맡을수록 실력이 인정받습니다. "
            f"다만 {primary_unsuitable_condition}는 피하는 편이 좋습니다."
        )
    elif display_priority == "reference":
        sentence = (
            f"당신에게 참고할 만한 분야는 {rule.label}입니다. "
            f"직업을 완전히 이쪽으로 정하기보다, 현재 업무 안에서 {top_sub_role.label}처럼 "
            f"{top_sub_role.role_sentence}을 맡을 때 도움이 됩니다."
        )
    elif display_priority == "caution":
        sentence = (
            f"당신에게 {rule.label}은 우선순위를 낮게 보는 편이 좋습니다. "
            f"{primary_unsuitable_condition}에서는 소모가 커집니다."
        )
    else:
        sentence = (
            f"당신에게 {rule.label}은 보조적으로 참고할 수 있습니다. "
            f"{top_work_style.label} 성향이 필요한 자리보다 {top_sub_role.label}처럼 역할 기준이 분명한 업무에서 활용하기 좋습니다."
        )
    for term in FORBIDDEN_CUSTOMER_TERMS:
        sentence = sentence.replace(term, "")
    return sentence


def _field_score(
    rule: CareerFieldRule,
    *,
    day_master_stem: str,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    branch_interactions: list[BranchInteraction],
    life_feature_profile: LifeFeatureProfile,
    element_combination_profile: ElementCombinationProfile,
    ten_god_interaction_profile: TenGodInteractionProfile,
    stem_reception_profile: StemReceptionProfile,
    integrated_saju_profile: IntegratedSajuProfile,
    work_styles: dict[str, CareerWorkStyleScore],
) -> CareerFieldScore:
    score = 32.0
    basis_codes: list[str] = [f"career_field_rule_{rule.key}"]
    counter_signals: list[str] = []
    (
        context_delta,
        context_basis_codes,
        context_counter_signals,
        day_master_fit_mode,
        seasonal_fit_note,
        fit_context_sentence,
    ) = _score_day_month_context(
        rule,
        day_master_stem=day_master_stem,
        element_profile=element_profile,
        position_signals=position_signals,
    )

    weighted_layers = (
        (_score_elements(rule, element_profile), 0.45),
        (_score_ten_gods(rule, ten_god_profile), 0.45),
        (_score_positions(rule, day_master_stem=day_master_stem, position_signals=position_signals), 0.38),
        ((context_delta, context_basis_codes, context_counter_signals), 0.35),
        (_score_life_axes(rule, life_feature_profile), 0.75),
        (_score_branch_interactions(rule, branch_interactions), 0.9),
        (
            _score_combination_profiles(
                rule,
                element_combination_profile,
                ten_god_interaction_profile,
                stem_reception_profile,
                integrated_saju_profile,
            ),
            0.35,
        ),
    )
    for (delta, basis, counters), layer_weight in weighted_layers:
        score += delta * layer_weight
        basis_codes.extend(basis)
        counter_signals.extend(counters)

    final_score = _clip(score)
    basis_codes = _dedupe(basis_codes)[:18]
    counter_signals = _dedupe(counter_signals)[:12]
    strength = _strength_label(final_score)
    sub_roles = _build_sub_role_scores(
        rule,
        final_score,
        element_profile=element_profile,
        ten_god_profile=ten_god_profile,
        life_feature_profile=life_feature_profile,
        work_styles=work_styles,
    )
    top_sub_role_keys = [item.key for item in sub_roles[:3]]
    top_work_style = max(work_styles.values(), key=lambda item: item.score)
    primary_unsuitable_condition = rule.unsuitable_conditions[0]
    return CareerFieldScore(
        key=rule.key,
        label=rule.label,
        category=rule.category,
        score=final_score,
        strength_label=strength,
        confidence=_confidence(final_score, len(basis_codes), len(counter_signals)),
        suitable_fields=list(rule.suitable_fields),
        unsuitable_conditions=list(rule.unsuitable_conditions),
        primary_unsuitable_condition=primary_unsuitable_condition,
        day_master_fit_mode=day_master_fit_mode,
        seasonal_fit_note=seasonal_fit_note,
        fit_context_sentence=fit_context_sentence,
        fit_context_basis_codes=_dedupe(context_basis_codes)[:8],
        role_style=rule.role_style,
        income_link=rule.income_link,
        sub_roles=sub_roles,
        top_sub_role_keys=top_sub_role_keys,
        display_priority="supporting",
        basis_codes=basis_codes,
        counter_signals=counter_signals,
        customer_sentence=_customer_sentence(
            rule,
            final_score,
            display_priority="supporting",
            top_sub_role=sub_roles[0],
            top_work_style=top_work_style,
            primary_unsuitable_condition=primary_unsuitable_condition,
            fit_context_sentence=fit_context_sentence,
        ),
    )


def build_career_field_profile(
    *,
    day_master_stem: str,
    element_profile: ElementProfile,
    ten_god_profile: TenGodProfile,
    position_signals: dict[str, PositionSignal],
    branch_interactions: list[BranchInteraction],
    life_feature_profile: LifeFeatureProfile,
    element_combination_profile: ElementCombinationProfile,
    ten_god_interaction_profile: TenGodInteractionProfile,
    stem_reception_profile: StemReceptionProfile,
    integrated_saju_profile: IntegratedSajuProfile,
) -> CareerFieldProfile:
    """Build a stable career-field profile from chart-level evidence."""

    work_styles = _build_work_style_scores(
        element_profile=element_profile,
        ten_god_profile=ten_god_profile,
        position_signals=position_signals,
        branch_interactions=branch_interactions,
        life_feature_profile=life_feature_profile,
    )
    top_work_style_keys = sorted(work_styles, key=lambda key: work_styles[key].score, reverse=True)[:2]
    top_work_style = work_styles[top_work_style_keys[0]]

    field_scores = {
        key: _field_score(
            rule,
            day_master_stem=day_master_stem,
            element_profile=element_profile,
            ten_god_profile=ten_god_profile,
            position_signals=position_signals,
            branch_interactions=branch_interactions,
            life_feature_profile=life_feature_profile,
            element_combination_profile=element_combination_profile,
            ten_god_interaction_profile=ten_god_interaction_profile,
            stem_reception_profile=stem_reception_profile,
            integrated_saju_profile=integrated_saju_profile,
            work_styles=work_styles,
        )
        for key, rule in CAREER_FIELD_RULES.items()
    }
    ranked_keys = sorted(field_scores, key=lambda key: field_scores[key].score, reverse=True)
    top_score = field_scores[ranked_keys[0]].score
    primary_field_keys = [
        key for key in ranked_keys if field_scores[key].score >= 82 and top_score - field_scores[key].score <= 8
    ][:3]
    if not primary_field_keys:
        primary_field_keys = [ranked_keys[0]]
    reference_limit = max(3, 5 - len(primary_field_keys))
    reference_field_keys = [key for key in ranked_keys if key not in primary_field_keys][:reference_limit]
    top_field_keys = list(dict.fromkeys(primary_field_keys + reference_field_keys))[:5]
    caution_field_keys = sorted(
        [key for key in field_scores if key not in set(top_field_keys)],
        key=lambda key: (field_scores[key].score, key),
    )[:4]

    priority_by_key = {
        **{key: "primary" for key in primary_field_keys},
        **{key: "reference" for key in reference_field_keys},
        **{key: "caution" for key in caution_field_keys},
    }
    updated_field_scores: dict[str, CareerFieldScore] = {}
    for key, field in field_scores.items():
        priority = priority_by_key.get(key, "supporting")
        rule = CAREER_FIELD_RULES[key]
        updated_field_scores[key] = replace(
            field,
            display_priority=priority,
            customer_sentence=_customer_sentence(
                rule,
                field.score,
                display_priority=priority,
                top_sub_role=field.sub_roles[0],
                top_work_style=top_work_style,
                primary_unsuitable_condition=field.primary_unsuitable_condition,
                fit_context_sentence=field.fit_context_sentence,
            ),
        )
    field_scores = updated_field_scores

    summary_sentences = [INTERPRETATION_PRINCIPLE]
    summary_sentences.extend(field_scores[key].customer_sentence for key in primary_field_keys[:2])
    if reference_field_keys:
        summary_sentences.append(field_scores[reference_field_keys[0]].customer_sentence)
    if caution_field_keys:
        summary_sentences.append(field_scores[caution_field_keys[0]].customer_sentence)

    return CareerFieldProfile(
        fields=field_scores,
        work_styles=work_styles,
        top_field_keys=top_field_keys,
        primary_field_keys=primary_field_keys,
        reference_field_keys=reference_field_keys,
        caution_field_keys=caution_field_keys,
        top_work_style_keys=top_work_style_keys,
        summary_sentences=summary_sentences,
        interpretation_principle=INTERPRETATION_PRINCIPLE,
        rule_version=CAREER_FIELD_RULE_VERSION,
    )


def validate_career_field_static_contract() -> list[str]:
    errors: list[str] = []
    if set(CAREER_SUB_ROLE_RULES) != set(CAREER_FIELD_RULES):
        errors.append("career sub-role rule field keys mismatch")
    if set(CAREER_WORK_STYLE_RULES) != {"organization", "independent", "expert", "manager"}:
        errors.append("career work-style rule keys mismatch")
    if set(DAY_MASTER_CAREER_MODES) != set(STEM_METADATA):
        errors.append("day-master career mode keys mismatch")
    if set(MONTH_BRANCH_CAREER_NOTES) != set(MONTH_SEASON_MODIFIERS):
        errors.append("month-branch career note keys mismatch")
    static_customer_text = " ".join(
        list(DAY_MASTER_CAREER_MODES.values())
        + list(MONTH_BRANCH_CAREER_NOTES.values())
        + [INTERPRETATION_PRINCIPLE]
    )
    for term in FORBIDDEN_CUSTOMER_TERMS:
        if term in static_customer_text:
            errors.append(f"career context static text forbidden customer term {term}")
    for key, rule in CAREER_WORK_STYLE_RULES.items():
        if key != rule.key:
            errors.append(f"{key}: work-style key mismatch")
        if not rule.role_sentence:
            errors.append(f"{key}: work-style missing role sentence")
    for key, rule in CAREER_FIELD_RULES.items():
        if key != rule.key:
            errors.append(f"{key}: rule key mismatch")
        if len(rule.suitable_fields) < 4:
            errors.append(f"{key}: suitable fields too sparse")
        if len(rule.unsuitable_conditions) < 2:
            errors.append(f"{key}: unsuitable conditions too sparse")
        if not rule.element_weights:
            errors.append(f"{key}: missing element weights")
        if not rule.ten_god_group_weights and not rule.ten_god_weights:
            errors.append(f"{key}: missing ten-god weights")
        if any(group not in TEN_GOD_GROUP_KEYS for group in rule.ten_god_group_weights):
            errors.append(f"{key}: unsupported ten-god group")
        sub_roles = CAREER_SUB_ROLE_RULES.get(key, ())
        if len(sub_roles) != 3:
            errors.append(f"{key}: sub-role count must be 3")
        for sub_role in sub_roles:
            if sub_role.parent_field_key != key:
                errors.append(f"{key}: sub-role parent mismatch {sub_role.key}")
            if not sub_role.role_sentence:
                errors.append(f"{key}: sub-role missing role sentence {sub_role.key}")
            if not sub_role.work_style_weights:
                errors.append(f"{key}: sub-role missing work-style weights {sub_role.key}")
            unsupported_styles = set(sub_role.work_style_weights).difference(CAREER_WORK_STYLE_RULES)
            if unsupported_styles:
                errors.append(f"{key}: sub-role unsupported work styles {sorted(unsupported_styles)}")
        customer_text = " ".join(
            [
                INTERPRETATION_PRINCIPLE,
                rule.label,
                rule.role_style,
                rule.income_link,
                *rule.suitable_fields,
                *rule.unsuitable_conditions,
                *(work_style.role_sentence for work_style in CAREER_WORK_STYLE_RULES.values()),
                *(sub_role.role_sentence for sub_role in sub_roles),
            ]
        )
        for term in FORBIDDEN_CUSTOMER_TERMS:
            if term in customer_text:
                errors.append(f"{key}: forbidden customer term {term}")
    return errors
