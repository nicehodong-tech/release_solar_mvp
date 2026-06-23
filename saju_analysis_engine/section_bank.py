"""Customer-facing report section bank.

The selector decides which section is relevant. This module only stores section
assets and lightweight quality checks. Later prose patches should mainly touch
this file or successor bank modules, not report rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field


SECTION_BANK_VERSION = "section_bank_v1"


@dataclass(frozen=True)
class ReportSectionAsset:
    section_key: str
    source_key: str
    title: str
    domain: str
    narrative_group: str
    opening: tuple[str, ...]
    main_body: tuple[str, ...]
    compressed_summary: tuple[str, ...]
    selection_signal_hints: tuple[str, ...] = ()
    age_timing_sentences: tuple[str, ...] = ()
    annual_sentences: dict[int, tuple[str, ...]] = field(default_factory=dict)
    awkward_words_to_avoid: tuple[str, ...] = ()
    wording_notes: tuple[str, ...] = ()
    rule_version: str = SECTION_BANK_VERSION
    aliases: tuple[str, ...] = field(default_factory=tuple)


_AWKWARD_VISIBLE_FRAGMENTS = (
    "구조가 활성화",
    "내면의 에너지",
    "긍정적인 흐름",
    "재물의 경계가 흐려",
    "관계의 패턴",
    "좌우합니다",
    "좌우될 것입니다",
    "조건에 따라",
)

_REQUIRED_SECTION_KEYS = (
    "money_not_stay",
    "created_output_becomes_money",
    "close_people_money_mix",
    "practical_problem_solver",
    "responsibility_without_authority",
)


REPORT_SECTION_BANK: dict[str, ReportSectionAsset] = {
    "created_output_becomes_money": ReportSectionAsset(
        section_key="created_output_becomes_money",
        source_key="made_to_money",
        title="만든 것이 돈으로 바뀌는 사주",
        domain="money",
        narrative_group="money_creation",
        selection_signal_hints=(
            "직접 만든 결과물이 수입으로 이어짐",
            "기술, 수업, 콘텐츠, 서비스가 재물과 연결됨",
            "가격표와 반복 판매가 중요함",
            "말보다 손에 잡히는 상품이 필요함",
        ),
        opening=(
            "이 사주는 돈을 먼저 좇기보다, 자신이 만든 결과물에서 돈이 생깁니다.",
            "말, 기술, 수업, 콘텐츠, 서비스처럼 직접 내놓을 수 있는 것이 있어야 재물운이 살아납니다.",
            "가만히 기다리는 돈보다, 손으로 만들고 사람에게 보여준 뒤 들어오는 돈에 가깝습니다.",
        ),
        main_body=(
            "이 사주는 막연한 기대보다 결과물이 먼저입니다.",
            "무엇을 팔지 고민하기 전에, 무엇을 꾸준히 내놓을 수 있는지를 봐야 합니다.",
            "작은 기술이라도 반복해서 제공할 수 있으면 돈이 붙습니다.",
            "수업을 한다면 다시 듣는 사람이 생겨야 합니다.",
            "글이나 콘텐츠를 만든다면 꾸준히 찾는 독자가 생겨야 합니다.",
            "서비스를 한다면 한 번 이용한 사람이 다시 연락해야 합니다.",
            "이 사주는 한 번에 크게 터지는 돈보다, 계속 만들어서 쌓이는 돈에 더 강합니다.",
            "만들기만 하고 가격을 정하지 못하면 수입이 약해집니다.",
            "주변에서 좋다고 말해도 실제 결제나 계약으로 이어지지 않으면 재물로 남지 않습니다.",
            "그래서 이 사주는 실력과 가격표가 함께 있어야 합니다.",
            "좋은 것을 만드는 데서 끝나지 말고, 그것을 얼마에 제공할지까지 정해야 합니다.",
            "만든 것이 돈이 되려면 반복성, 가격, 고객이 함께 잡혀야 합니다.",
        ),
        compressed_summary=(
            "이 사주는 만든 것이 돈이 됩니다.",
            "기술, 콘텐츠, 수업, 서비스처럼 반복해서 내놓을 수 있는 것이 재물의 시작입니다.",
            "돈보다 먼저 자기 상품을 분명히 해야 합니다.",
        ),
        awkward_words_to_avoid=(
            "생산 구조가 활성화됩니다.",
            "재물 통로가 열립니다.",
            "돈의 흐름이 좋아집니다.",
        ),
        wording_notes=(
            "명리 용어보다 상품, 가격, 고객, 결제, 계약 같은 생활 단어를 먼저 쓴다.",
            "식상생재를 설명하더라도 앞에서는 결과물과 반복 판매로 말한다.",
        ),
        aliases=("made_to_money",),
    ),
    "responsibility_without_authority": ReportSectionAsset(
        section_key="responsibility_without_authority",
        source_key="responsibility_without_authority",
        title="책임은 많은데 결정권이 약한 자리",
        domain="career",
        narrative_group="career_authority",
        selection_signal_hints=(
            "맡는 일은 많지만 결정권이 약함",
            "상사, 윗선, 보고선 문제가 직업 부담으로 나타남",
            "실무와 평가 주체가 어긋남",
            "책임 범위가 불분명할 때 소모가 커짐",
        ),
        opening=(
            "이 사주는 일을 못해서 지치는 것이 아닙니다.",
            "맡은 일은 끝까지 해내려 하지만, 어디까지가 내 몫인지 불분명할 때 마음이 상하기 쉽습니다.",
            "책임은 넘어오는데 결정권이 없으면 오래 버티기 어렵습니다.",
        ),
        main_body=(
            "처음에는 일단 해보자는 마음으로 맡습니다.",
            "부탁을 받으면 쉽게 거절하지 못할 수 있습니다.",
            "문제가 생기면 어떻게든 수습하려고 합니다.",
            "하지만 시간이 지나면 다른 문제가 보입니다.",
            "일은 내가 하는데 결정은 다른 사람이 합니다.",
            "실무는 내 손을 거치는데 평가는 윗선에서 가져갈 수 있습니다.",
            "문제가 생겼을 때만 내 이름이 나오는 자리도 있습니다.",
            "이런 자리는 처음보다 나중에 더 지칩니다.",
            "책임을 맡는 것 자체가 나쁜 운은 아닙니다.",
            "이 사주는 책임이 분명할수록 실력이 나옵니다.",
            "결정할 권한도 함께 있어야 합니다.",
            "맡은 일, 결정할 수 있는 일, 보고해야 할 일이 구분될 때 직업운이 안정됩니다.",
        ),
        compressed_summary=(
            "이 사주는 책임을 피하는 사주가 아닙니다.",
            "책임만 있고 결정권이 없으면 오래 버티기 어렵습니다.",
            "좋은 자리는 큰 자리보다 내 몫이 분명한 자리입니다.",
        ),
        awkward_words_to_avoid=(
            "권한 구조가 활성화됩니다.",
            "직업적 압력이 누적됩니다.",
            "사회적 역할 패턴을 인식해야 합니다.",
        ),
        wording_notes=(
            "직업운은 직함보다 책임, 보고선, 결정권, 평가 주체를 중심으로 말한다.",
            "상담 문장에서는 조직론보다 사용자가 겪는 억울함과 소모감을 먼저 잡는다.",
        ),
    ),
    "practical_problem_solver": ReportSectionAsset(
        section_key="practical_problem_solver",
        source_key="practical_solves_pressure",
        title="실무로 어려운 일을 풀어가는 사주",
        domain="career",
        narrative_group="career_execution",
        selection_signal_hints=(
            "직접 처리해본 일에서 실력이 드러남",
            "문제가 생긴 자리에서 처리 순서를 잡음",
            "현장 경험, 운영, 고객 응대가 직업운과 연결됨",
            "말보다 결과로 평가받는 일이 중요함",
        ),
        opening=(
            "이 사주는 말보다 해본 일이 중요합니다.",
            "배운 것만 많은 자리보다, 직접 처리해본 일에서 실력이 드러납니다.",
            "어려운 상황이 와도 손에 익은 일이 있으면 버틸 수 있습니다.",
        ),
        main_body=(
            "이 사주는 책상 위의 계획만으로는 운이 살지 않습니다.",
            "직접 부딪쳐본 일에서 감각이 생깁니다.",
            "문제가 생겼을 때 무엇을 먼저 잡아야 하는지 아는 편입니다.",
            "사람들이 우왕좌왕할 때도 처리 순서를 찾으려 합니다.",
            "보고서보다 현장 경험이 더 큰 자산이 됩니다.",
            "직장에서라면 문제 해결, 운영, 고객 응대, 일정 정리, 기술 지원 같은 자리에서 쓰임이 생깁니다.",
            "사업을 한다면 손님을 실제로 상대해본 경험이 돈이 됩니다.",
            "준비 없이 어려운 일을 맡으면 쉽게 지칩니다.",
            "일은 계속 생기는데 처리 방식이 몸에 익지 않으면 오래 버티기 어렵습니다.",
            "이 사주는 무작정 큰일을 맡는 것보다, 반복해서 해본 일을 키우는 편이 좋습니다.",
            "작은 실무가 쌓이면 나중에는 남들이 맡기 어려운 일도 처리할 수 있습니다.",
            "결국 이 사주는 말보다 손에 남은 경험이 운을 만듭니다.",
        ),
        compressed_summary=(
            "이 사주는 실무가 운을 살립니다.",
            "직접 해본 일, 몸에 익은 일, 끝까지 처리한 일이 평가로 이어집니다.",
            "큰 말보다 손에 남은 경험이 더 중요합니다.",
        ),
        awkward_words_to_avoid=(
            "살기를 제어합니다.",
            "실무 구조가 작동합니다.",
            "문제 해결 에너지가 강화됩니다.",
        ),
        wording_notes=(
            "식신제살 계열은 손에 익은 일, 처리 순서, 현장 경험으로 풀어 쓴다.",
            "능력 찬양보다 실제로 어디에서 평가를 받는지까지 말한다.",
        ),
        aliases=("practical_solves_pressure",),
    ),
    "money_not_stay": ReportSectionAsset(
        section_key="money_not_stay",
        source_key="money_not_retained",
        title="돈이 들어와도 그냥 남지 않는 사주",
        domain="money",
        narrative_group="money_boundary",
        selection_signal_hints=(
            "수입과 지출이 함께 커짐",
            "생활비, 카드값, 대출, 가족 비용이 재물운을 건드림",
            "수입 이후 실제로 남는 금액이 줄어듦",
            "수입보다 지출 기준이 먼저 필요함",
        ),
        opening=(
            "이 사주는 돈이 전혀 안 들어오는 사주가 아닙니다.",
            "문제는 들어온 돈이 한곳에 오래 머물기 어렵다는 점입니다.",
            "수입이 생기면 곧바로 나갈 곳도 함께 보이는 편입니다.",
        ),
        main_body=(
            "이 사주는 돈이 들어와도 그냥 쌓이지 않습니다.",
            "생활비, 카드값, 대출, 가족 문제, 경조사비처럼 써야 할 일이 따라오기 쉽습니다.",
            "일을 키우면 운영비도 함께 늘어날 수 있습니다.",
            "수입이 생겼다고 생각했는데, 지나고 보면 손에 남은 돈이 약할 수 있습니다.",
            "큰 소비보다 작은 지출이 더 문제일 때도 많습니다.",
            "한 번에 큰돈을 쓰지 않아도 계속 빠지는 돈이 있으면 재물이 모이지 않습니다.",
            "이 사주는 돈을 버는 것만큼 돈의 자리를 정해야 합니다.",
            "들어온 돈을 어디에 쓰고, 얼마를 남기고, 누구에게 얼마까지 쓸 것인지 나눠야 합니다.",
            "가까운 사람의 부탁이나 가족 문제로 돈이 움직이면 더 신중해야 합니다.",
            "좋은 마음으로 쓴 돈도 반복되면 부담이 됩니다.",
            "돈이 들어오는 달보다 돈을 남기는 습관이 더 중요합니다.",
            "이 사주는 수입 규모보다 실제로 남기는 금액에서 재물운이 더 선명하게 드러납니다.",
        ),
        compressed_summary=(
            "이 사주는 돈이 안 들어오는 사주가 아닙니다.",
            "들어온 돈이 여러 갈래로 나가기 쉬운 편입니다.",
            "수입보다 남기는 기준이 재물운의 핵심입니다.",
        ),
        awkward_words_to_avoid=(
            "재물의 경계가 흐려집니다.",
            "돈의 흐름이 분산됩니다.",
            "현금 보존 구조가 약합니다.",
        ),
        wording_notes=(
            "재물운을 약하다고 단정하기보다 수입 이후의 지출 장면을 구체적으로 보여준다.",
            "생활비, 카드값, 대출, 가족 비용처럼 사용자가 바로 떠올리는 단어를 쓴다.",
        ),
        aliases=("money_not_retained",),
    ),
    "close_people_money_mix": ReportSectionAsset(
        section_key="close_people_money_mix",
        source_key="close_people_money_mix",
        title="가까운 사람과 돈이 섞이기 쉬운 사주",
        domain="money",
        narrative_group="money_boundary",
        selection_signal_hints=(
            "가족, 지인, 동료와 돈 문제가 얽힘",
            "정산, 공동 비용, 동업 문제가 중요함",
            "좋은 마음으로 시작한 일이 몫 문제로 바뀜",
            "사람과 돈이 함께 움직일 때 기준이 필요함",
        ),
        opening=(
            "이 사주는 가까운 사람과 돈이 섞이기 쉽습니다.",
            "가족, 지인, 동료, 동업자처럼 편하게 생각한 사람이 돈 문제 안으로 들어올 수 있습니다.",
            "처음부터 나쁜 의도로 시작되는 일은 아닙니다.",
            "오히려 좋은 마음으로 돕고, 같이 해보자는 말에서 일이 시작되는 경우가 많습니다.",
        ),
        main_body=(
            "처음에는 작은 비용을 그냥 넘기기 쉽습니다.",
            "누가 더 움직였는지도 따지지 않을 수 있습니다.",
            "아직 돈이 크지 않을 때는 별문제가 없어 보입니다.",
            "그런데 실제 수익이 생기거나 손해가 나면 이야기가 달라집니다.",
            "누가 더 많이 움직였는지가 문제가 됩니다.",
            "누가 먼저 시작했는지가 문제가 됩니다.",
            "누가 사람을 데려왔는지가 문제가 됩니다.",
            "누가 더 가져가야 하는지도 문제가 됩니다.",
            "이 사주는 돈이 없어서 문제가 생기는 쪽이 아닙니다.",
            "돈이 보이기 시작할 때 사람 사이의 몫이 예민해지는 쪽입니다.",
            "함께 만들 것이 분명하면 사람은 동료가 됩니다.",
            "나눌 돈부터 보이면 사람은 곧 몫을 따지는 상대가 됩니다.",
            "이 사주는 가까운 사람과 돈을 섞을수록 기준이 필요합니다.",
            "정이 없어서가 아닙니다.",
            "기준이 있어야 정이 오래 갑니다.",
        ),
        compressed_summary=(
            "이 사주는 돈보다 정산이 중요합니다.",
            "사람을 피할 필요는 없습니다.",
            "사람과 돈이 같이 들어오면 기준부터 세워야 합니다.",
        ),
        awkward_words_to_avoid=(
            "비겁이 재성을 침범합니다.",
            "재물의 경계가 흐려집니다.",
            "사람과 돈의 패턴을 인식해야 합니다.",
        ),
        wording_notes=(
            "비겁쟁재 계열을 말할 때 사람을 피하라는 식으로 몰지 않는다.",
            "동업, 가족 지출, 공동 비용, 정산처럼 생활 장면으로 말한다.",
        ),
    ),
}

SECTION_KEY_ALIASES = {
    alias: key
    for key, asset in REPORT_SECTION_BANK.items()
    for alias in asset.aliases
}


def section_asset_for(section_key: str) -> ReportSectionAsset | None:
    canonical_key = SECTION_KEY_ALIASES.get(section_key, section_key)
    return REPORT_SECTION_BANK.get(canonical_key)


def validate_section_bank() -> list[str]:
    """Return lightweight prose-bank contract issues."""

    issues: list[str] = []
    for key in _REQUIRED_SECTION_KEYS:
        if key not in REPORT_SECTION_BANK:
            issues.append(f"missing section asset: {key}")

    for key, asset in REPORT_SECTION_BANK.items():
        if asset.section_key != key:
            issues.append(f"section key mismatch: {key}")
        if asset.age_timing_sentences:
            issues.append(f"{key}: asset bank must not contain fixed age timing sentences")
        if asset.annual_sentences:
            issues.append(f"{key}: asset bank must not contain fixed annual sentences")
        if not asset.selection_signal_hints:
            issues.append(f"{key}: missing selection signal hints")
        if not asset.opening:
            issues.append(f"{key}: missing opening")
        if len(asset.opening) < 2:
            issues.append(f"{key}: opening too thin")
        if not asset.main_body:
            issues.append(f"{key}: missing main body")
        if len(asset.main_body) < 8:
            issues.append(f"{key}: main body too thin")
        if not asset.compressed_summary:
            issues.append(f"{key}: missing compressed summary")
        if len(asset.compressed_summary) < 2:
            issues.append(f"{key}: compressed summary too thin")

        visible_text = " ".join(
            list(asset.opening)
            + list(asset.main_body)
            + list(asset.age_timing_sentences)
            + [sentence for sentences in asset.annual_sentences.values() for sentence in sentences]
            + list(asset.compressed_summary)
        )
        for fragment in _AWKWARD_VISIBLE_FRAGMENTS:
            if fragment in visible_text:
                issues.append(f"{key}: awkward visible fragment: {fragment}")

    return issues
