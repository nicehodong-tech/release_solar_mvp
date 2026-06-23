"""Product catalog definitions separated from analysis calculations.

The analysis engine should produce structured judgment data. This module defines
how much of that data each product tier may expose and which menu entries each
customer-facing product promises. Future product or wording patches should start
here before touching analysis formulas.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Iterable
from typing import Literal

from .models import Domain, ProductTier


CatalogEntryKind = Literal["core", "domain", "advice", "annual", "timing"]


@dataclass(frozen=True)
class TierDefinition:
    tier: ProductTier
    label: str
    detail_level: str
    item_limit: int
    basis_limit: int
    timing_limit: int
    summary_limit: int
    includes_web_sections: bool
    includes_premium_sections: bool
    positioning: str
    is_public: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CatalogEntry:
    entry_id: str
    title: str
    kind: CatalogEntryKind
    source_domains: tuple[Domain, ...]
    tiers: tuple[ProductTier, ...]
    section_titles: tuple[str, ...]
    locked_in_tiers: tuple[ProductTier, ...] = ()
    unlock_tier: ProductTier | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_domains"] = list(self.source_domains)
        payload["tiers"] = list(self.tiers)
        payload["section_titles"] = list(self.section_titles)
        payload["locked_in_tiers"] = list(self.locked_in_tiers)
        payload["preview"] = CATALOG_ENTRY_PREVIEWS.get(self.entry_id, "")
        payload["display_group"] = CATALOG_ENTRY_DISPLAY_GROUPS.get(self.kind, "")
        payload["content_mode"] = CATALOG_ENTRY_CONTENT_MODES.get(self.entry_id, "")
        return payload


TIER_DEFINITIONS: dict[ProductTier, TierDefinition] = {
    "free": TierDefinition(
        tier="free",
        label="무료 종합 사주",
        detail_level="brief",
        item_limit=4,
        basis_limit=3,
        timing_limit=1,
        summary_limit=2,
        includes_web_sections=False,
        includes_premium_sections=False,
        positioning="광고 시청 후 총운, 성향, 재물, 직업, 관계, 올해 운세를 충분히 읽을 수 있게 하는 무료 상품입니다.",
    ),
    "basic": TierDefinition(
        tier="basic",
        label="내부 기본 리포트",
        detail_level="standard",
        item_limit=4,
        basis_limit=6,
        timing_limit=3,
        summary_limit=3,
        includes_web_sections=True,
        includes_premium_sections=False,
        positioning="현재 고객 상품에서는 제외하지만, 추후 중간 상품을 다시 열 수 있도록 남긴 내부 호환 등급입니다.",
        is_public=False,
    ),
    "premium": TierDefinition(
        tier="premium",
        label="프리미엄 종합 사주 리포트",
        detail_level="expanded",
        item_limit=999,
        basis_limit=12,
        timing_limit=5,
        summary_limit=6,
        includes_web_sections=True,
        includes_premium_sections=True,
        positioning="타고난 사주, 재물과 직업의 큰 시기, 관계와 결혼의 실제 조건까지 상담형 문단으로 확장하는 심층 상품입니다.",
    ),
}

PUBLIC_PRODUCT_TIERS: tuple[ProductTier, ...] = tuple(
    tier for tier, definition in TIER_DEFINITIONS.items() if definition.is_public
)


CATALOG_ENTRIES: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        entry_id="life_overview",
        title="나의 사주 총운",
        kind="core",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("나의 큰 운", "가장 강한 장점", "꼭 조심할 것"),
    ),
    CatalogEntry(
        entry_id="native_money",
        title="타고난 재물운",
        kind="domain",
        source_domains=("money",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "재물운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="native_career",
        title="타고난 직업운",
        kind="domain",
        source_domains=("career",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "직업운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="personality_overview",
        title="타고난 성향",
        kind="core",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("성향풀이", "강점", "주의할 점"),
    ),
    CatalogEntry(
        entry_id="native_love",
        title="타고난 연애운",
        kind="domain",
        source_domains=("love",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "애정운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="native_marriage",
        title="타고난 결혼운",
        kind="domain",
        source_domains=("marriage",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "결혼운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="reputation_success",
        title="명예·성공운",
        kind="domain",
        source_domains=("career",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "성공운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="business_expansion",
        title="사업운과 확장",
        kind="domain",
        source_domains=("money", "career"),
        tiers=("basic", "premium"),
        section_titles=("총운풀이", "포인트", "사업운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="relationship_social",
        title="대인운",
        kind="domain",
        source_domains=("love", "marriage"),
        tiers=("basic", "premium"),
        section_titles=("총운풀이", "포인트", "대인운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="success_advice",
        title="성공을 위한 조언",
        kind="advice",
        source_domains=("money", "career"),
        tiers=("basic", "premium"),
        section_titles=("성공을 위한 조언", "가장 중요한 기준"),
    ),
    CatalogEntry(
        entry_id="annual_overview",
        title="올해 총운",
        kind="annual",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("나에게 올해는", "올해 이것만은 꼭 조심하자"),
    ),
    CatalogEntry(
        entry_id="annual_money",
        title="올해 재물운",
        kind="annual",
        source_domains=("money",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "재물운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="annual_career",
        title="올해 직업운",
        kind="annual",
        source_domains=("career",),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "직업운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="annual_love",
        title="올해 애정운",
        kind="annual",
        source_domains=("love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("총운풀이", "포인트", "애정운을 좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="annual_best",
        title="올해 가장 좋은 것",
        kind="annual",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("가장 좋은 것", "좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="annual_caution",
        title="올해 조심할 것",
        kind="annual",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("주의가 필요한 것", "올해의 조언"),
    ),
    CatalogEntry(
        entry_id="annual_good_timing",
        title="올해 좋은 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("좋은 시기", "좋게 쓰는 법"),
    ),
    CatalogEntry(
        entry_id="annual_caution_timing",
        title="올해 조심할 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("free", "basic", "premium"),
        section_titles=("조심할 시기", "미리 챙길 것"),
    ),
    CatalogEntry(
        entry_id="timing_detail",
        title="좋은 시기와 조심할 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("basic", "premium"),
        section_titles=("좋은 시기", "조심할 시기", "좋게 쓰는 법"),
        locked_in_tiers=("free",),
        unlock_tier="premium",
    ),
    CatalogEntry(
        entry_id="long_term_years",
        title="큰돈이 들어오는 나이",
        kind="timing",
        source_domains=("money", "career"),
        tiers=("premium",),
        section_titles=("돈이 강해지는 나이", "조심할 나이", "그때의 선택"),
        locked_in_tiers=("free", "basic"),
        unlock_tier="premium",
    ),
    CatalogEntry(
        entry_id="life_strength_balance",
        title="인생 전반의 강한 영역과 약한 영역",
        kind="core",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("강한 영역", "관리할 영역", "인생 후반의 변화"),
    ),
    CatalogEntry(
        entry_id="money_attitude",
        title="돈을 대하는 태도",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("돈을 판단하는 방식", "소비와 축적", "주의할 습관"),
    ),
    CatalogEntry(
        entry_id="native_wealth_level",
        title="선천 재물 수준",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("타고난 재물 크기", "수입이 확대되는 방식", "현실적인 수준"),
    ),
    CatalogEntry(
        entry_id="income_expansion_method",
        title="수입을 키우는 방식",
        kind="domain",
        source_domains=("money", "career"),
        tiers=("premium",),
        section_titles=("수입이 커지는 방식", "보상 기준", "확대할 때의 주의점"),
    ),
    CatalogEntry(
        entry_id="wealth_retention_conditions",
        title="돈이 남는 방식",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("돈이 남는 구조", "자산으로 이어지는 방식", "관리 기준"),
    ),
    CatalogEntry(
        entry_id="money_leak_conditions",
        title="손실이 생기는 지점",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("손실이 생기는 지점", "지출 관리", "계약 주의점"),
    ),
    CatalogEntry(
        entry_id="wealth_potential",
        title="재물이 커지는 운",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("재물이 커지는 자리", "강하게 살아나는 자리", "약해지는 자리"),
    ),
    CatalogEntry(
        entry_id="income_expansion_power",
        title="수입이 늘어나는 운",
        kind="domain",
        source_domains=("money", "career"),
        tiers=("premium",),
        section_titles=("수입이 늘어나는 자리", "성과가 돈이 되는 자리", "거래가 넓어지는 자리"),
    ),
    CatalogEntry(
        entry_id="asset_retention_power",
        title="돈을 남기는 운",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("돈을 남기는 방식", "돈을 지키는 방식", "손실을 줄이는 기준"),
    ),
    CatalogEntry(
        entry_id="investment_trade_sense",
        title="투자·거래 감각",
        kind="domain",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("투자 판단", "거래 감각", "주의할 선택"),
    ),
    CatalogEntry(
        entry_id="money_caution_years",
        title="재물 문제로 조심할 나이",
        kind="timing",
        source_domains=("money",),
        tiers=("premium",),
        section_titles=("손실을 조심할 나이", "계약 주의", "지출 관리"),
    ),
    CatalogEntry(
        entry_id="career_precision",
        title="직업운 정밀 분석",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("일에서 남기는 성취", "역할 변화", "평가 기준"),
    ),
    CatalogEntry(
        entry_id="career_fit_fields",
        title="잘 맞는 직업 분야",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("추천 분야", "강점이 드러나는 역할", "직무 활용"),
    ),
    CatalogEntry(
        entry_id="career_mismatch_conditions",
        title="맞지 않는 업무 환경",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("소모가 커지는 자리", "피해야 할 업무", "조정 기준"),
    ),
    CatalogEntry(
        entry_id="organization_success_method",
        title="조직에서 성취하는 방식",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("조직 적응", "좋은 평가를 받는 방식", "책임 범위"),
    ),
    CatalogEntry(
        entry_id="expertise_recognition_method",
        title="전문성으로 인정받는 방식",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("전문성", "자격과 실력", "인정받는 조건"),
    ),
    CatalogEntry(
        entry_id="independence_business_potential",
        title="독립·사업운",
        kind="domain",
        source_domains=("money", "career"),
        tiers=("premium",),
        section_titles=("독립해서 일하는 힘", "사업 운영", "확장할 때 조심할 점"),
    ),
    CatalogEntry(
        entry_id="social_success_potential",
        title="사회적으로 인정받는 운",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("인정받는 자리", "평가와 성취", "커지는 역할"),
    ),
    CatalogEntry(
        entry_id="honor_reputation",
        title="명예운과 평판",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("명예운", "평판 관리", "공식 인정"),
    ),
    CatalogEntry(
        entry_id="leadership_potential",
        title="사람을 이끄는 운",
        kind="domain",
        source_domains=("career", "marriage"),
        tiers=("premium",),
        section_titles=("사람을 이끄는 자리", "신뢰를 얻는 방식", "부담이 커지는 자리"),
    ),
    CatalogEntry(
        entry_id="social_influence",
        title="사람에게 남기는 영향",
        kind="domain",
        source_domains=("love", "career"),
        tiers=("premium",),
        section_titles=("사람에게 남기는 영향", "신뢰를 얻는 방식", "갈등 지점"),
    ),
    CatalogEntry(
        entry_id="business_expansion_power",
        title="사업이 커지는 운",
        kind="domain",
        source_domains=("money", "career"),
        tiers=("premium",),
        section_titles=("사업이 커지는 자리", "거래 판단", "확장할 때 조심할 점"),
    ),
    CatalogEntry(
        entry_id="academic_expertise_achievement",
        title="전문성으로 성취하는 운",
        kind="domain",
        source_domains=("career",),
        tiers=("premium",),
        section_titles=("공부와 연구", "전문성이 깊어지는 자리", "자격과 실력"),
    ),
    CatalogEntry(
        entry_id="love_precision",
        title="연애운 정밀 분석",
        kind="domain",
        source_domains=("love",),
        tiers=("premium",),
        section_titles=("끌리는 방식", "관계가 시작되는 조건", "반복되는 문제"),
    ),
    CatalogEntry(
        entry_id="marriage_precision",
        title="결혼운 정밀 분석",
        kind="domain",
        source_domains=("marriage",),
        tiers=("premium",),
        section_titles=("결혼 안정성", "현실 조건", "장기 유지"),
    ),
    CatalogEntry(
        entry_id="spouse_conflict_points",
        title="배우자와 부딪히기 쉬운 부분",
        kind="domain",
        source_domains=("marriage", "love"),
        tiers=("premium",),
        section_titles=("충돌 지점", "감정과 생활", "조율 기준"),
    ),
    CatalogEntry(
        entry_id="marriage_stability_conditions",
        title="결혼 생활이 안정되는 방식",
        kind="domain",
        source_domains=("marriage",),
        tiers=("premium",),
        section_titles=("안정되는 방식", "돈과 주거", "역할 분담"),
    ),
    CatalogEntry(
        entry_id="children_family_luck",
        title="자식운·가정운",
        kind="domain",
        source_domains=("marriage",),
        tiers=("premium",),
        section_titles=("자식운", "가정 안의 역할", "생활 관리"),
    ),
    CatalogEntry(
        entry_id="health_life_management",
        title="건강운과 생활 관리",
        kind="advice",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("체력 사용 방식", "과로 주의", "생활 관리"),
    ),
    CatalogEntry(
        entry_id="ten_year_luck",
        title="10년 단위 대운 분석",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("대운의 큰 방향", "재물과 직업 변화", "관계 변화"),
    ),
    CatalogEntry(
        entry_id="near_years_luck",
        title="가까운 연도별 운세",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("가까운 연도", "좋은 연도", "주의할 연도"),
    ),
    CatalogEntry(
        entry_id="monthly_key_timing",
        title="월별 주요 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("월별 주요 시기", "좋은 월", "주의할 월"),
    ),
    CatalogEntry(
        entry_id="favorable_timing",
        title="좋게 써야 할 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("좋은 시기", "활용 기준", "기대할 수 있는 일"),
    ),
    CatalogEntry(
        entry_id="caution_timing",
        title="신중해야 할 시기",
        kind="timing",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("신중하게 다룰 시기", "주의할 일", "피할 선택"),
    ),
    CatalogEntry(
        entry_id="final_money_work_relationship_advice",
        title="최종 조언",
        kind="advice",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("돈의 기준", "일의 기준", "관계의 기준"),
    ),
    CatalogEntry(
        entry_id="premium_core_five",
        title="프리미엄 핵심 결론 5가지",
        kind="advice",
        source_domains=("money", "career", "love", "marriage"),
        tiers=("premium",),
        section_titles=("핵심 결론", "좋은 선택", "주의할 선택"),
    ),
)


CATALOG_ENTRY_PREVIEWS: dict[str, str] = {
    "life_overview": "올해 가장 강한 운과 전체 결론을 먼저 정리합니다.",
    "personality_overview": "돈, 일, 관계에서 반복되는 선택 방식과 타고난 성향이 정리됩니다.",
    "native_money": "타고난 재물 규모, 수입 방식, 손에 남는 돈의 크기를 봅니다.",
    "native_career": "직업에서 성취를 쌓는 방식과 맡는 자리가 커지는 지점을 봅니다.",
    "native_love": "연애에서 끌림이 생기는 방식과 애정 표현의 특징을 봅니다.",
    "native_marriage": "결혼 생활의 안정성, 책임 분담, 생활 기준의 핵심이 정리됩니다.",
    "reputation_success": "명예, 평판, 성취가 사회적으로 커지는 방식을 봅니다.",
    "business_expansion": "사업이 커지는 자리와 거래에서 조심할 지점을 같이 정리합니다.",
    "relationship_social": "사람을 대하는 태도와 신뢰를 얻는 자리를 정리합니다.",
    "success_advice": "성공을 크게 만드는 기준과 약점으로 남기 쉬운 부분이 정리됩니다.",
    "annual_overview": "올해 좋아지는 일과 조심해야 할 일을 먼저 정리합니다.",
    "annual_money": "올해 돈이 생기는 자리와 지출·정산에서 조심할 문제를 봅니다.",
    "annual_career": "올해 넓어지는 업무 범위, 좋은 평가, 책임 부담을 봅니다.",
    "annual_love": "올해 만남, 연락, 감정 표현에서 달라지는 애정운을 봅니다.",
    "annual_best": "올해 가장 좋게 살아나는 강점과 기대할 만한 기회가 정리됩니다.",
    "annual_caution": "올해 돈, 일, 관계에서 조심할 선택과 부담이 정리됩니다.",
    "annual_good_timing": "올해 운이 가장 잘 풀리는 시기와 그때 생기는 일을 봅니다.",
    "annual_caution_timing": "올해 신중해야 할 시기와 피하는 편이 좋은 선택이 정리됩니다.",
    "timing_detail": "좋은 시기와 조심할 시기를 날짜 단위로 정리합니다.",
    "long_term_years": "한국 나이 기준으로 돈과 성취가 강해지는 때, 조심할 때가 정리됩니다.",
    "life_strength_balance": "인생 전반에서 강하게 쓰이는 영역과 약점으로 남기 쉬운 영역을 정리합니다.",
    "money_attitude": "당신이 돈을 대하는 태도와 재물운의 체감 차이가 연결됩니다.",
    "native_wealth_level": "선천적으로 쥐고 태어난 재물 수준과 후반으로 갈수록 쌓이는 돈이 정리됩니다.",
    "income_expansion_method": "수입이 커지는 방식과 보상이 좋아지는 자리를 봅니다.",
    "wealth_retention_conditions": "벌어들인 돈이 손에 남고 자산으로 쌓이는 방식을 봅니다.",
    "money_leak_conditions": "손실로 이어지기 쉬운 지출, 계약, 정산 문제가 정리됩니다.",
    "wealth_potential": "재물이 커지는 자리와 돈으로 이어지기 쉬운 기회를 봅니다.",
    "income_expansion_power": "수입원이 넓어지고 보상이 커지는 자리를 정리합니다.",
    "asset_retention_power": "벌어들인 돈이 손에 남고 자산으로 쌓이는 방식을 봅니다.",
    "investment_trade_sense": "투자, 거래, 계약에서 유리한 선택과 조심할 선택을 정리합니다.",
    "money_caution_years": "재물 문제로 신중해야 할 나이와 피하는 편이 좋은 선택을 정리합니다.",
    "career_precision": "직업적 성취와 좋은 평가가 커지는 방식을 정밀하게 봅니다.",
    "career_fit_fields": "강점이 잘 쓰이는 직업 분야와 업무 역할이 정리됩니다.",
    "career_mismatch_conditions": "소모가 커지기 쉬운 업무 자리와 피하는 편이 좋은 환경을 봅니다.",
    "organization_success_method": "조직 안에서 좋은 평가를 받는 방식과 책임 범위가 정리됩니다.",
    "expertise_recognition_method": "전문성, 자격, 실력이 사회적으로 인정받는 방식을 봅니다.",
    "independence_business_potential": "독립해서 일할 때 강해지는 부분과 사업으로 이어질 가능성을 봅니다.",
    "social_success_potential": "사회적으로 인정받는 자리와 역할이 커지는 방식을 봅니다.",
    "honor_reputation": "명예, 평판, 공식 인정이 커지는 방식이 정리됩니다.",
    "leadership_potential": "사람을 이끌 때 강해지는 지점과 부담으로 남기 쉬운 부분을 정리합니다.",
    "social_influence": "상대가 당신을 신뢰하고 따르게 되는 방식을 봅니다.",
    "business_expansion_power": "사업이 커지는 자리와 확장 과정에서 커지는 위험을 같이 정리합니다.",
    "academic_expertise_achievement": "공부, 연구, 자격, 전문성으로 성취하는 방식을 정리합니다.",
    "love_precision": "연애가 시작되는 방식과 관계가 깊어질 때 반복되는 문제를 봅니다.",
    "marriage_precision": "결혼이 오래 안정되는 방식과 생활 기준이 정리됩니다.",
    "spouse_conflict_points": "배우자와 부딪히기 쉬운 감정 문제와 돈의 기준을 같이 정리합니다.",
    "marriage_stability_conditions": "결혼 생활이 안정되는 방식과 역할 분담의 핵심이 정리됩니다.",
    "children_family_luck": "자식운과 가정 안에서 맡기 쉬운 역할을 봅니다.",
    "health_life_management": "체력 사용 방식과 생활에서 무리가 쌓이는 부분이 정리됩니다.",
    "ten_year_luck": "10년 단위로 재물, 직업, 관계의 큰 방향이 바뀌는 시점을 봅니다.",
    "near_years_luck": "가까운 몇 해 사이에 좋아지는 영역과 조심할 영역을 정리합니다.",
    "monthly_key_timing": "월별로 강하게 나타나는 일과 조심할 일이 정리됩니다.",
    "favorable_timing": "좋게 써야 할 시기와 그때 기대할 수 있는 일을 봅니다.",
    "caution_timing": "신중해야 할 시기와 피하는 편이 좋은 선택이 정리됩니다.",
    "final_money_work_relationship_advice": "돈, 일, 관계에서 끝까지 지켜야 할 기준이 정리됩니다.",
    "premium_core_five": "프리미엄 리포트에서 가장 중요한 결론 다섯 가지를 정리합니다.",
}

CATALOG_ENTRY_DISPLAY_GROUPS: dict[CatalogEntryKind, str] = {
    "core": "핵심",
    "domain": "타고난 운",
    "advice": "조언",
    "annual": "올해 운세",
    "timing": "시기",
}

CATALOG_ENTRY_CONTENT_MODES: dict[str, str] = {
    "life_overview": "overview",
    "personality_overview": "personality",
    "native_money": "native_domain",
    "native_career": "native_domain",
    "native_love": "native_domain",
    "native_marriage": "native_domain",
    "reputation_success": "social_success",
    "business_expansion": "business",
    "relationship_social": "relationship",
    "success_advice": "advice",
    "annual_overview": "annual_overview",
    "annual_money": "annual_domain",
    "annual_career": "annual_domain",
    "annual_love": "annual_domain",
    "annual_best": "annual_best",
    "annual_caution": "annual_caution",
    "annual_good_timing": "free_timing_highlight",
    "annual_caution_timing": "free_timing_caution",
    "timing_detail": "timing_detail",
    "long_term_years": "long_term_timing",
    "life_strength_balance": "premium_life_balance",
    "money_attitude": "premium_money_attitude",
    "native_wealth_level": "premium_native_wealth",
    "income_expansion_method": "premiumIncomeGrowth",
    "wealth_retention_conditions": "premium_wealth_retention",
    "money_leak_conditions": "premium_money_leak",
    "wealth_potential": "premium_wealth_potential",
    "income_expansion_power": "premium_income_expansion",
    "asset_retention_power": "premium_asset_retention",
    "investment_trade_sense": "premium_investment_trade",
    "money_caution_years": "premium_money_caution_years",
    "career_precision": "premium_career_precision",
    "career_fit_fields": "premium_career_fields",
    "career_mismatch_conditions": "premium_career_mismatch",
    "organization_success_method": "premium_organization_success",
    "expertise_recognition_method": "premium_expertise_recognition",
    "independence_business_potential": "premium_independence_business",
    "social_success_potential": "premium_social_success",
    "honor_reputation": "premium_honor_reputation",
    "leadership_potential": "premium_leadership",
    "social_influence": "premium_social_influence",
    "business_expansion_power": "premium_business_expansion",
    "academic_expertise_achievement": "premium_academic_expertise",
    "love_precision": "premium_love_precision",
    "marriage_precision": "premium_marriage_precision",
    "spouse_conflict_points": "premium_spouse_conflict",
    "marriage_stability_conditions": "premium_marriage_stability",
    "children_family_luck": "premium_children_family",
    "health_life_management": "premium_health_life",
    "ten_year_luck": "premium_ten_year_luck",
    "near_years_luck": "premium_near_years",
    "monthly_key_timing": "premium_monthly_timing",
    "favorable_timing": "premium_favorable_timing",
    "caution_timing": "premium_caution_timing",
    "final_money_work_relationship_advice": "premium_final_advice",
    "premium_core_five": "premium_core_five",
}


def tier_definition(tier: ProductTier) -> TierDefinition:
    return TIER_DEFINITIONS[tier]


def catalog_entries_for_tier(tier: ProductTier) -> tuple[CatalogEntry, ...]:
    return tuple(
        entry
        for entry in CATALOG_ENTRIES
        if tier in entry.tiers or tier in entry.locked_in_tiers or is_catalog_entry_locked_for_tier(entry, tier)
    )


def visible_catalog_entries_for_tier(tier: ProductTier) -> tuple[CatalogEntry, ...]:
    return tuple(entry for entry in CATALOG_ENTRIES if tier in entry.tiers)


def is_catalog_entry_locked_for_tier(entry: CatalogEntry, tier: ProductTier) -> bool:
    if tier in entry.locked_in_tiers:
        return True
    return tier == "free" and "premium" in entry.tiers and tier not in entry.tiers


def catalog_payload_for_tier(
    tier: ProductTier,
    visible_domains: Iterable[Domain] | None = None,
) -> list[dict[str, object]]:
    visible_domain_list = list(visible_domains or [])
    payload: list[dict[str, object]] = []
    for entry in catalog_entries_for_tier(tier):
        item = entry.to_dict()
        is_locked = is_catalog_entry_locked_for_tier(entry, tier)
        linked_item_indexes = [
            index
            for index, domain in enumerate(visible_domain_list, start=1)
            if domain in entry.source_domains and not is_locked
        ]
        item["is_locked"] = is_locked
        item["unlock_tier"] = entry.unlock_tier or ("premium" if is_locked else None)
        item["surface_hint"] = "locked_upsell" if is_locked else "menu_entry"
        item["linked_item_indexes"] = linked_item_indexes
        item["availability_status"] = (
            "locked" if is_locked else "has_visible_detail" if linked_item_indexes else "menu_only"
        )
        payload.append(item)
    return payload
