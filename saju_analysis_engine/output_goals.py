"""Domain-level output goals for the analysis engine.

This module defines what the analysis engine must ultimately judge for each
life domain. It is not a scoring rule by itself. It is the target contract
that element balance, stem interactions, ten-god interactions, seasonal
strength, pattern judgment, and branch relations must project into.
"""

from __future__ import annotations

from dataclasses import dataclass


OUTPUT_GOAL_VERSION = "domain_output_goal_v9"


@dataclass(frozen=True)
class DomainOutputGoal:
    domain: str
    label: str
    primary_question: str
    judgment_targets: tuple[str, ...]
    required_conclusions: tuple[str, ...]
    calculation_inputs: tuple[str, ...]
    event_feature_axes: tuple[str, ...]
    supporting_feature_axes: tuple[str, ...]
    applicability_questions: tuple[str, ...]
    caution_questions: tuple[str, ...]
    customer_output_rule: str


@dataclass(frozen=True)
class TimingOutputGoal:
    label: str
    scope: str
    primary_question: str
    judgment_targets: tuple[str, ...]
    required_conclusions: tuple[str, ...]
    calculation_inputs: tuple[str, ...]
    domain_projection_rules: tuple[str, ...]
    customer_output_rule: str


DOMAIN_OUTPUT_GOAL_ORDER = ("money", "career", "love", "marriage", "personality")


DOMAIN_OUTPUT_GOALS: dict[str, DomainOutputGoal] = {
    "money": DomainOutputGoal(
        domain="money",
        label="재물",
        primary_question="당신은 평생 어떤 방식으로 돈을 만들고, 어느 지점에서 자기 몫을 지키거나 잃기 쉬운가.",
        judgment_targets=(
            "재물이 생기는 원천과 금전 규모의 상한",
            "일상의 수입을 넘어 거래 단위와 자산 단위가 커지는 힘",
            "수입이 생기는 직업 장면과 거래 방식",
            "재능, 결과물, 전문성이 보수로 환산되는 방식",
            "성과가 계약금, 성과급, 매출, 지분으로 확정되는 방식",
            "수입이 현금, 명의, 소유권, 장기 자산으로 남는 방식",
            "수입 이후 생활비, 고정비, 예비 자금을 무리 없이 운용하는 정도",
            "가족, 지인, 동업자와 얽힌 공동자금의 득실",
            "가까운 사람의 부탁, 보증, 대여, 채무 관계를 감당하거나 피하는 힘",
            "부모·가족 재산, 상속성 자산, 원가족 지출과 자기 자산의 경계",
            "계약, 명의, 지급일, 보증에서 금전 권리가 흔들리는 지점",
            "사업, 투자, 외부 거래로 재물 단위가 커지는 시기와 조건",
            "투자, 거래, 회수, 명의 구조에서 유리함과 손실 위험이 나뉘는 지점",
            "미수금, 대여금, 지연 지급, 성과 보상의 회수 가능성",
            "나이가 들수록 재물 단위가 커지는지, 후반부에 자산이 굳어지는지",
            "돈 앞에서 체면, 정, 관계보다 자기 기준을 세우는 힘",
            "손실, 과소비, 체면성 지출, 보증이 커지는 원인",
        ),
        required_conclusions=(
            "재물 형성력",
            "재물 규모 확장력",
            "수입 창출력",
            "재주 수익화",
            "성과 보상력",
            "자산화 능력",
            "자금 운용 안정성",
            "투자·거래 판단력",
            "공동자금 운영력",
            "부채·보증 관리력",
            "가족재산 경계력",
            "계약·명의 안정성",
            "채권·미수금 회수력",
            "사업 확장성",
            "재정 방어력",
            "후반 축재력",
            "금전 기준성",
            "재물 강세 연도",
            "재물 주의 연도",
        ),
        calculation_inputs=(
            "월령과 격국에서 재성이 필요한지, 부담이 되는지, 현실 자원으로 허용되는지",
            "재성이 천간에 드러났는지, 지지에 뿌리내렸는지, 지장간에 숨어 있는지",
            "식상이 재성을 생하는지, 식상이 인성에 막히거나 관성과 충돌하는지",
            "비겁이 재성을 빼앗는지, 식상과 결합해 공동 생산으로 바뀌는지",
            "재성이 관성을 생해 계약, 직책, 보상 기준을 세우는지",
            "재극인이 인성의 과다를 제어해 현실 수입으로 내리는지, 문서 손상으로 기울어지는지",
            "관성이 비겁을 제어해 정산과 명의 기준을 세우는지",
            "부채, 보증, 대여가 비겁·재성·관성의 생극에서 어떻게 드러나는지",
            "인성과 재성이 가족 재산, 문서, 원가족 지출 문제로 어떻게 연결되는지",
            "편재와 정재가 투자, 고정 수입, 자산 보유 중 어디로 나뉘는지",
            "재물 규모가 고정 수입, 사업성 거래, 장기 자산 중 어디로 확장되는지",
            "재성의 지장간 발동이 대운·세운에서 계약, 명의, 회수 사건으로 올라오는지",
            "재성 지장간, 재물궁, 직업궁이 합충형파해로 발동되는지",
            "재성, 관성, 인성이 지급일, 회수 조건, 권리 확정으로 연결되는지",
            "대운과 세운에서 원국의 재물 구조가 수입, 손실, 자산화 중 어디로 현실화되는지",
        ),
        event_feature_axes=(
            "money_potential",
            "income_expansion",
            "liquidity_stability",
            "reward_claim_strength",
            "asset_retention",
            "ownership_clarity",
            "shared_asset_boundary",
            "investment_trading_sense",
            "deal_selection",
            "loss_avoidance",
            "late_life_money_growth",
            "money_attitude",
            "practical_planning",
            "spending_control",
            "business_expansion",
        ),
        supporting_feature_axes=(
            "decision_consistency",
            "organization_adaptability",
            "reputation_maintenance",
            "responsibility_capacity",
            "boundary_management",
        ),
        applicability_questions=(
            "돈이 들어오는 조건과 보상 기준이 분명한가.",
            "성과, 지분, 정산 방식이 사전에 정리되는가.",
            "자산을 지킬 문서, 계약, 관리 기준이 갖추어지는가.",
        ),
        caution_questions=(
            "사람 관계나 경쟁 때문에 실제로 남는 몫이 줄어드는가.",
            "수입보다 지출, 책임, 보증, 투자 부담이 먼저 커지는가.",
            "계약 조건을 확인하기 전에 돈이 움직이는가.",
        ),
        customer_output_rule=(
            "재물 판단은 좋은지 나쁜지로 끝내지 않는다. 돈의 원천, 수입화, 보상 환산, 자산화, "
            "공동자금, 계약 권리, 손실 원인을 분리해 결론부터 제시한다."
        ),
    ),
    "career": DomainOutputGoal(
        domain="career",
        label="직업과 사회적 성취",
        primary_question="당신은 어떤 역할에서 이름이 남고, 어떤 조직 조건에서 성취와 보상이 함께 커지는가.",
        judgment_targets=(
            "잘 맞는 일의 방식과 맞지 않는 업무 조건",
            "직업 분야와 실제 맡기 쉬운 역할",
            "성과가 실적, 이력, 직책으로 남는 방식",
            "성과가 평가, 명예, 직함으로 전환되는 방식",
            "실적이 승진, 직함, 공식 책임자로 올라갈 수 있는 실제 조건",
            "책임과 결정권, 보상이 함께 주어지는지",
            "성과가 연봉, 수수료, 지분, 성과급처럼 자기 몫으로 확정되는지",
            "사회적 지위와 영향력이 실제 역할 확대까지 이어지는지",
            "자격, 기술, 문서, 경험이 전문 자산으로 쌓이는지",
            "조직 안에서 자리를 잡는 방식과 충돌하는 지점",
            "소속, 부서, 직무, 고용 형태가 바뀔 때 손실보다 기회를 만들 수 있는지",
            "자기 이름, 거래처, 고객 기반으로 독립할 수 있는지",
            "성과보다 소모가 먼저 커지는 업무 조건을 피할 수 있는지",
            "이직, 승진, 독립, 역할 확대가 강하게 드러나는 연도",
        ),
        required_conclusions=(
            "직업 적성",
            "직업 분야",
            "성취 축적력",
            "평가·명예 전환력",
            "승진·직함 가능성",
            "사회적 도약성",
            "권한 확보력",
            "책임·권한 균형",
            "보상 협상력",
            "전문 자산화",
            "조직 적응력",
            "소속 전환력",
            "독립 가능성",
            "업무 조건 감별력",
            "직업 전환 연도",
        ),
        calculation_inputs=(
            "월령과 격국에서 관성, 인성, 식상, 재성 중 직업 축을 세우는 십신",
            "관성이 직책, 평가, 책임으로 안정되게 드러나는지",
            "관성과 인성이 승진, 직함, 공식 책임을 받을 수 있는 형태로 연결되는지",
            "인성이 관성을 받아 자격, 신뢰, 제도권 성취로 이어지는지",
            "식상이 성과물, 기술, 말, 기획으로 직업적 결과를 만드는지",
            "재성이 시장, 거래처, 실무 보상과 연결되는지",
            "재성과 관성이 결합해 직책, 보상, 계약 조건을 세우는지",
            "비겁이 협업, 경쟁, 독립성, 조직 밖 활동으로 작동하는지",
            "오행 배합이 교육, 기획, 금융, 운영, 기술, 공공, 사업성 중 어디로 기울어지는지",
            "월령이 허용하는 사회적 역할과 실제 직무 권한이 맞물리는지",
            "관성이 비겁을 정리하거나 재성이 관성을 생해 직책과 보상 기준을 세우는지",
            "월주, 시주, 직업궁에 걸린 합충형파해가 역할 변화로 발동되는지",
            "대운과 세운에서 직책, 소속, 독립, 보상 구조가 어느 연도에 바뀌는지",
        ),
        event_feature_axes=(
            "social_success_potential",
            "career_achievement",
            "work_domain_fit",
            "responsibility_capacity",
            "role_authority_alignment",
            "reputation_maintenance",
            "self_direction",
            "decision_consistency",
            "honor_recognition",
            "promotion_visibility",
            "leadership_potential",
            "organization_adaptability",
            "academic_expertise",
            "change_adaptability",
        ),
        supporting_feature_axes=(
            "business_expansion",
            "interpersonal_influence",
            "communication_expression",
            "practical_planning",
            "crisis_recovery",
        ),
        applicability_questions=(
            "책임을 맡을 때 권한과 평가 기준도 함께 주어지는가.",
            "성과를 공식적으로 인정받을 기준이 있는가.",
            "전문성, 자격, 문서, 실무 결과가 직업 신뢰로 연결되는가.",
        ),
        caution_questions=(
            "권한보다 책임이 먼저 커지는가.",
            "성과를 내도 평판 관리나 보고 기준이 흔들리는가.",
            "조직 기준과 자기 표현 방식이 충돌하는가.",
        ),
        customer_output_rule=(
            "직업 판단은 직무명만 나열하지 않는다. 일의 방식, 분야, 성취가 남는 자리, "
            "평가와 권한, 독립 가능성, 피해야 할 업무 조건을 분리해 제시한다."
        ),
    ),
    "love": DomainOutputGoal(
        domain="love",
        label="연애와 관계",
        primary_question="당신은 어떤 사람에게 끌리고, 어떤 방식으로 가까워지며, 무엇 때문에 관계가 어긋나는가.",
        judgment_targets=(
            "끌리는 상대의 성향과 반복되는 선택 기준",
            "인연이 생기는 장소, 활동, 사회적 접점",
            "호감이 실제 연애로 넘어가는 속도와 방식",
            "상대 선택이 끌림 위주인지, 안정성과 생활 감각까지 보는지",
            "호감이 생긴 뒤 상대의 말, 책임감, 생활 태도를 가려내는지",
            "관계 안에서 주도권을 잡는지, 상대의 속도에 끌려가는지",
            "관계가 빨리 붙는지, 천천히 확인하며 안정되는지",
            "좋아하는 마음이 말, 행동, 시간, 책임으로 전달되는 방식",
            "관계가 오래 유지되는 안정성과 쉽게 식는 지점",
            "연락 빈도, 개인 시간, 거리감이 맞지 않을 때 생기는 부담",
            "상대가 서운함을 느끼는 표현 지연, 연락 방식, 기대 차이",
            "자존심, 소유욕, 가족, 돈 문제가 관계 갈등으로 번지는 지점",
            "친구, 과거 인연, 가족, 직장 주변인이 관계에 끼어드는 정도",
            "지나간 관계가 다시 올라오거나 미련이 오래 남는지",
            "연애가 결혼 약속과 생활 논의로 이어지는 현실성",
        ),
        required_conclusions=(
            "끌림의 기준",
            "상대 선택력",
            "상대 신뢰 감별력",
            "인연 형성력",
            "관계 진전력",
            "관계 주도권",
            "관계 속도 조절력",
            "애정 표현성",
            "정서 수용력",
            "관계 지속력",
            "연락·거리 안정성",
            "오해 조정력",
            "갈등 관리력",
            "주변 개입 관리력",
            "재회 가능성",
            "결혼 연결력",
        ),
        calculation_inputs=(
            "일지와 배우자궁이 관계의 기본 태도와 배우자 체감을 어떻게 만드는지",
            "식상이 감정 표현, 말, 매력, 불만 표출로 드러나는지",
            "재성이 현실적 호감, 선택 기준, 남명 배우자성으로 작동하는지",
            "관성이 약속, 예의, 여명 배우자성, 관계 책임으로 작동하는지",
            "인성이 확인, 신뢰, 기억, 보호 욕구로 작동하는지",
            "비겁이 주도권, 비교, 질투, 가까운 사람과의 경쟁으로 작동하는지",
            "재성·관성·일지가 상대 선택 기준과 실제 배우자감 판단으로 어떻게 분화되는지",
            "배우자궁과 관성·재성·인성이 상대의 말, 책임감, 생활 태도를 가려내는 힘으로 작동하는지",
            "식상과 인성이 애정 표현과 정서 수용의 균형을 이루는지",
            "일지와 월지의 합충형파해가 관계 안정성 또는 반복 갈등으로 이어지는지",
            "배우자궁과 월지의 거리, 충합, 지장간 작용이 연락과 만남의 속도를 어떻게 만드는지",
            "비겁, 인성, 관성이 주변 사람의 말, 가족 조건, 과거 인연을 관계 안으로 끌어오는지",
            "대운과 세운에서 인연, 이별, 재회, 결혼 연결이 어느 연도에 발동되는지",
        ),
        event_feature_axes=(
            "interpersonal_influence",
            "attraction_selectivity",
            "relationship_progression",
            "affection_expression",
            "affection_receptivity",
            "emotional_alignment",
            "relationship_stability",
            "communication_expression",
            "boundary_management",
            "misunderstanding_prevention",
            "conflict_recovery",
            "reunion_closure",
            "crisis_recovery",
        ),
        supporting_feature_axes=(
            "self_direction",
            "decision_consistency",
            "change_adaptability",
            "money_attitude",
            "practical_planning",
        ),
        applicability_questions=(
            "호감 표현과 실제 생활 조건이 서로 어긋나지 않는가.",
            "연락, 거리, 기대치를 말로 조정할 수 있는가.",
            "주도권과 배려가 한쪽으로 치우치지 않는가.",
        ),
        caution_questions=(
            "감정은 깊어도 표현 방식이 충돌하는가.",
            "상대에게 맞추는 과정에서 자기 기준이 사라지는가.",
            "가까워질수록 비교, 통제, 거리 문제가 커지는가.",
        ),
        customer_output_rule=(
            "연애 판단은 인기나 만남의 수로 끝내지 않는다. 끌림, 만남의 자리, 진전 속도, "
            "표현 방식, 갈등 관리력, 재회와 결혼 연결을 따로 말한다."
        ),
    ),
    "marriage": DomainOutputGoal(
        domain="marriage",
        label="결혼과 가정",
        primary_question="당신은 어떤 배우자와 결혼이 안정되고, 어떤 생활 문제에서 결혼이 흔들리는가.",
        judgment_targets=(
            "결혼을 빨리 결정하는지, 늦게 안정되는지",
            "오래 맞는 배우자의 성격, 생활 태도, 책임 감각",
            "혼인 약속, 주거, 가족 협의가 강해지는 시기",
            "연애와 결혼 의사가 실제 혼인 절차로 굳어지는 현실화 정도",
            "주거, 생활비, 역할 분담이 안정되는 방식",
            "가정을 운영하는 생활 관리력과 반복 지출을 감당하는 힘",
            "집, 생활비, 시간 사용, 역할 분담을 설계하는 힘",
            "부부 사이의 명의, 공동 자산, 생활비 기준",
            "부부 생활비의 기준과 지출 통제 방식",
            "결혼 뒤 반복되기 쉬운 말투, 거리감, 책임 갈등",
            "감정 싸움 이후 생활 기준을 다시 맞출 수 있는 회복력",
            "양가, 가족 지원, 주거, 돌봄 부담이 끼어드는 정도",
            "배우자 가족과 원가족 사이에서 책임선을 지킬 수 있는지",
            "가족 문제, 돈 문제, 주거 문제가 겹칠 때 결혼 생활이 버티는 힘",
            "자녀, 양육, 돌봄 책임이 부부 생활과 재정에 어떤 부담 또는 안정으로 들어오는지",
            "배우자로 인해 얻는 안정과 함께 따라오는 부담",
            "결혼을 오래 지키는 지점과 위기가 커지는 연도",
        ),
        required_conclusions=(
            "혼인 성향",
            "배우자상",
            "결혼 적기",
            "결혼 현실화력",
            "생활 안정",
            "가정 운영력",
            "주거·생활 설계력",
            "부부 재정",
            "생활비 기준성",
            "부부 갈등 조정력",
            "부부 갈등 회복성",
            "가족 책임 경계력",
            "배우자 가족 경계",
            "자녀·양육 책임",
            "배우자 복",
            "혼인 위기 대응력",
            "결혼 지속력",
        ),
        calculation_inputs=(
            "일지 배우자궁의 안정성, 충돌, 합, 형, 파, 해의 현실 작용",
            "배우자성이 투출했는지, 지지에 뿌리내렸는지, 지장간에 숨어 있는지",
            "관성이 책임, 약속, 제도적 결합으로 작동하는지",
            "재성이 생활비, 자산, 배우자 경제 조건, 현실 조건으로 작동하는지",
            "재성이 부부 생활비와 명의 기준으로 작동하는지, 가족 지출 부담으로 흐르는지",
            "인성이 가족 보호, 주거, 문서, 인정 욕구로 작동하는지",
            "식상이 감정 표현, 불만 표출, 배우자성 손상으로 작동하는지",
            "비겁이 배우자와의 동등성, 경쟁, 가족 간 몫 문제로 작동하는지",
            "월령과 격국에서 결혼 안정 요소가 필요한지, 과한지, 손상되는지",
            "일지, 월지, 시지의 지장간이 주거, 생활비, 가족 책임으로 어떻게 현실화되는지",
            "일지와 월지의 충합, 가족성 십신, 재성·인성의 작용이 결혼 위기와 회복으로 어떻게 이어지는지",
            "식상과 관성이 자녀·양육 책임, 돌봄 부담, 가정 내 역할 배분으로 어떻게 작동하는지",
            "대운과 세운에서 결혼 적기, 가족 변수, 부부 재정, 위기 연도가 어떻게 나뉘는지",
        ),
        event_feature_axes=(
            "marriage_stability",
            "spouse_match_quality",
            "spouse_support_benefit",
            "marriage_timing_readiness",
            "household_stability",
            "household_finance_alignment",
            "relationship_stability",
            "conflict_recovery",
            "family_responsibility",
            "inlaw_boundary_strength",
            "marriage_crisis_management",
            "boundary_management",
            "decision_consistency",
            "practical_planning",
            "asset_retention",
            "money_attitude",
            "crisis_recovery",
        ),
        supporting_feature_axes=(
            "income_expansion",
            "spending_control",
            "responsibility_capacity",
            "communication_expression",
            "reputation_maintenance",
        ),
        applicability_questions=(
            "생활비, 주거, 가족 책임을 현실적으로 합의할 수 있는가.",
            "감정 표현과 책임 분담을 함께 조정할 수 있는가.",
            "결혼 결정 전에 돈, 가족, 역할 문제가 충분히 드러나는가.",
        ),
        caution_questions=(
            "사랑은 깊어도 생활 방식과 책임 범위가 충돌하는가.",
            "가족 조건, 돈 문제, 주거 문제가 감정 문제로 번지는가.",
            "한쪽에게 모든 부담이 몰리거나 결정이 계속 미루어지는가.",
        ),
        customer_output_rule=(
            "결혼 판단은 성사 여부만 말하지 않는다. 배우자상, 결혼 적기, 생활 안정, "
            "부부 재정, 가족 책임, 장기 지속과 위기 연도를 분리해 제시한다."
        ),
    ),
    "personality": DomainOutputGoal(
        domain="personality",
        label="성향",
        primary_question="당신은 어떤 기준으로 판단하고, 사람과 돈과 일 앞에서 어떤 성격으로 반복 반응하는가.",
        judgment_targets=(
            "중요한 선택 앞에서 끝까지 붙드는 기준",
            "사람을 받아들이는 속도와 가까워진 뒤 지키는 거리",
            "감정이 올라온 뒤 바로 드러나는지, 속으로 정리되는지",
            "책임과 압박이 커졌을 때 예민해지는 지점",
            "기회를 봤을 때 바로 움직이는지, 확인 후 실행하는지",
            "오래 몰입하는 분야와 금방 식는 관심사",
            "재물, 직업, 연애, 결혼 판단을 보정하는 성격의 반복성",
        ),
        required_conclusions=(
            "자기 주도성",
            "결정 지속성",
            "변화 적응력",
            "현실 설계력",
            "표현 전달력",
            "관계 경계 설정력",
            "갈등 회복력",
            "위기 회복력",
            "리더십 잠재력",
        ),
        calculation_inputs=(
            "일간의 기본 성정과 월령에서의 강약",
            "비겁이 자기 기준과 경쟁 의식으로 작동하는 정도",
            "식상이 표현, 기술, 말, 불만 표출로 작동하는 정도",
            "재성이 현실 감각, 선택, 비교, 실속으로 작동하는 정도",
            "관성이 책임, 규칙, 평가 민감성으로 작동하는 정도",
            "인성이 학습, 해석, 보호, 신뢰 확인으로 작동하는 정도",
            "합충형해파가 선택 속도, 관계 반응, 위기 대응에 주는 압력",
        ),
        event_feature_axes=(),
        supporting_feature_axes=(
            "self_direction",
            "decision_consistency",
            "change_adaptability",
            "practical_planning",
            "communication_expression",
            "boundary_management",
            "conflict_recovery",
            "crisis_recovery",
            "leadership_potential",
        ),
        applicability_questions=(
            "자신의 판단 기준이 현실 조건과 연결되는가.",
            "말과 행동의 속도가 상황의 요구와 맞는가.",
            "위험을 피하기보다 관리할 기준을 갖추는가.",
        ),
        caution_questions=(
            "자기 기준이 강해져 타인의 조건을 놓치는가.",
            "불안하거나 압박이 커질 때 표현이 과해지거나 닫히는가.",
            "결정을 오래 끌거나, 반대로 확인 없이 서두르는가.",
        ),
        customer_output_rule=(
            "성향 판단은 성격 묘사로 끝내지 않는다. 판단 기준, 대인 거리, 감정 반응, "
            "압박 대응, 실행 속도, 몰입 대상을 실제 운세 해석의 보정값으로 사용한다."
        ),
    ),
}


TIMING_OUTPUT_GOAL = TimingOutputGoal(
    label="대운·세운",
    scope="20세부터 79세까지의 전체 구간",
    primary_question="어느 연도에 재물, 직업, 연애, 결혼, 가족 사건이 강해지고, 어느 연도에 손실과 갈등을 조심해야 하는가.",
    judgment_targets=(
        "대운 10년마다 삶의 중심 과제가 어느 영역으로 옮겨가는지",
        "세운이 원국의 어떤 천간, 지지, 지장간, 합충형파해를 발동하는지",
        "재물 강세 연도 안에서도 수입, 자산화, 공동자금, 계약·명의를 구분하는지",
        "받아야 할 돈, 성과 보상, 대여금, 지연 지급이 회수되는 연도를 따로 구분하는지",
        "재물 주의 연도 안에서도 부채, 보증, 문서, 가족 재산 문제를 구분하는지",
        "직업 상승 연도 안에서도 평가, 권한, 이직, 독립, 책임 부담을 구분하는지",
        "직업 분야가 바뀌거나 맞는 산업과 역할이 새로 드러나는 연도를 구분하는지",
        "직업 전환 연도 안에서도 보상 협상, 소속 변경, 직책 변화, 독립 준비를 구분하는지",
        "연애 시작, 관계 진전, 재회·정리, 이별, 결혼 논의가 강해지는 연도를 구분하는지",
        "관계 주의 연도 안에서도 오해, 거리, 자존심, 주변 사람 개입을 구분하는지",
        "결혼 결정, 주거 준비, 가족 책임, 부부 재정 문제가 현실화되는 연도를 구분하는지",
        "자녀, 양육, 돌봄, 교육비 책임이 결혼 생활 안에서 커지는 연도를 구분하는지",
        "결혼 주의 연도 안에서도 생활비, 배우자 가족, 주거, 책임 분담 문제를 구분하는지",
        "주의 연도가 단순 불운인지, 돈·직업·관계·가족 중 어느 영역의 문제인지",
        "회복 연도와 말년 안정 연도를 손실 이후의 재정비, 자산, 가족, 사회적 평가로 분리하는지",
    ),
    required_conclusions=(
        "대운 구간별 중심 과제",
        "상승 연도",
        "수입 강세 연도",
        "재물 강세 연도",
        "자산화 연도",
        "채권·미수금 회수 연도",
        "공동자금 주의 연도",
        "계약·명의 주의 연도",
        "부채·보증 주의 연도",
        "가족재산 주의 연도",
        "재물 주의 연도",
        "직업 상승 연도",
        "권한 상승 연도",
        "보상 상승 연도",
        "직업 분야 전환 연도",
        "직업 전환 연도",
        "소속 변화 연도",
        "직업 부담 연도",
        "직업 독립 연도",
        "관계 진전 연도",
        "재회·정리 연도",
        "연애 강세 연도",
        "새 인연 연도",
        "이별·정리 연도",
        "관계 주의 연도",
        "주변 개입 주의 연도",
        "혼인 결정 연도",
        "주거·생활 준비 연도",
        "부부 재정 연도",
        "가족·주거 변동 연도",
        "자녀·양육 책임 연도",
        "결혼 주의 연도",
        "인생 전환 연도",
        "주의 연도",
        "회복 연도",
        "말년 안정 연도",
    ),
    calculation_inputs=(
        "대운 천간과 지지가 월령, 격국, 조후에서 필요한 글자인지",
        "대운이 원국의 재관인식비 중 어느 십신 연쇄를 발동하는지",
        "세운 천간이 원국 천간과 합·충·극·생으로 어떤 사건 표지를 만드는지",
        "세운 지지가 월지, 일지, 시지와 합충형파해로 어느 궁을 건드리는지",
        "지장간의 숨은 재성, 관성, 인성, 식상이 세운에서 투출하거나 현실화되는지",
        "미수금, 대여금, 성과 보상이 세운의 재성·관성·인성 작용으로 회수 가능한지",
        "좋은 구조가 운에서 강화되는지, 부담 구조가 운에서 살아나는지",
        "약한 원국 요소가 대운·세운에서 발동되어 실제 사건으로 올라오는지",
        "관계와 결혼에서 비겁·인성·관성이 주변 사람, 가족, 자녀 책임으로 발동하는지",
        "동일한 연도 안에서도 재물, 직업, 관계, 결혼의 길흉이 서로 다르게 나뉘는지",
    ),
    domain_projection_rules=(
        "재물 연도는 수입 강세, 자산화, 공동자금, 계약·명의, 손실을 분리해 붙인다.",
        "채권·미수금 연도는 받을 돈, 지급일, 성과 보상, 대여금 회수 문제를 따로 붙인다.",
        "직업 연도는 평가, 권한, 직책, 이직, 독립, 책임 부담을 분리해 붙인다.",
        "직업 분야 연도는 산업, 역할, 전문 방향이 바뀌는 시점을 직업 전환과 별도로 붙인다.",
        "연애 연도는 인연, 진전, 오해, 재회·정리, 이별 가능성을 분리해 붙인다.",
        "주변 개입 연도는 가족, 친구, 과거 인연의 말이 관계에 끼어드는 시점을 따로 붙인다.",
        "결혼 연도는 혼인 결정, 주거 준비, 가족 협의, 부부 재정, 위기를 분리해 붙인다.",
        "자녀·양육 연도는 돌봄, 교육비, 가족 지원, 부부 역할 배분이 커지는 시점을 따로 붙인다.",
        "주의 연도는 나쁜 해로만 표시하지 않고, 무엇을 조심해야 하는지 영역명을 붙인다.",
        "좋은 연도도 하나로 합치지 않고, 어떤 영역에서 좋은지 함께 표시한다.",
    ),
    customer_output_rule=(
        "대세운은 현재 연도 운세가 아니다. 20세부터 79세까지의 전체 구간에서 "
        "좋은 연도와 주의 연도를 영역별로 분리하고, 각 연도에 드러나는 사건명을 짧게 붙인다."
    ),
)


def output_goal_for(domain: str) -> DomainOutputGoal:
    try:
        return DOMAIN_OUTPUT_GOALS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported output goal domain: {domain}") from exc


def _domain_goal_payload(goal: DomainOutputGoal) -> dict[str, object]:
    return {
        "domain": goal.domain,
        "label": goal.label,
        "primary_question": goal.primary_question,
        "judgment_targets": list(goal.judgment_targets),
        "required_conclusions": list(goal.required_conclusions),
        "calculation_inputs": list(goal.calculation_inputs),
        "event_feature_axes": list(goal.event_feature_axes),
        "supporting_feature_axes": list(goal.supporting_feature_axes),
        "applicability_questions": list(goal.applicability_questions),
        "caution_questions": list(goal.caution_questions),
        "customer_output_rule": goal.customer_output_rule,
    }


def _timing_goal_payload(goal: TimingOutputGoal) -> dict[str, object]:
    return {
        "label": goal.label,
        "scope": goal.scope,
        "primary_question": goal.primary_question,
        "judgment_targets": list(goal.judgment_targets),
        "required_conclusions": list(goal.required_conclusions),
        "calculation_inputs": list(goal.calculation_inputs),
        "domain_projection_rules": list(goal.domain_projection_rules),
        "customer_output_rule": goal.customer_output_rule,
    }


def output_goal_contracts() -> dict[str, object]:
    """Return the product questions the engine must preserve in its output."""

    return {
        "schema_version": OUTPUT_GOAL_VERSION,
        "domain_order": list(DOMAIN_OUTPUT_GOAL_ORDER),
        "domains": {
            domain: _domain_goal_payload(DOMAIN_OUTPUT_GOALS[domain])
            for domain in DOMAIN_OUTPUT_GOAL_ORDER
        },
        "timing": _timing_goal_payload(TIMING_OUTPUT_GOAL),
    }
