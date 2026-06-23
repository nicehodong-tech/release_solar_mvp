"""Fixed counseling bridge sentences for customer report surfaces.

This module does not add chart judgments. It only provides stable connective
sentences that help product reports move from conclusion to lived meaning,
then from lived meaning to action and caution.
"""

from __future__ import annotations

from .models import Domain


COUNSELING_BRIDGE_SCHEMA_VERSION = "counseling_bridge_v1"


WEB_BRIDGE_LIMIT_BY_TIER = {
    "free": 1,
    "basic": 2,
    "premium": 2,
}


COUNSELING_BRIDGES: dict[Domain, dict[str, str]] = {
    "money": {
        "summary_to_feature": (
            "이 시기에는 받을 돈과 손에 남는 돈의 차이가 크게 벌어집니다."
        ),
        "feature_to_action": (
            "돈을 받는 기준을 먼저 세우게 됩니다. 지출 한도도 따로 정합니다."
        ),
        "action_to_caution": (
            "돈을 받는 기준이 늦게 정해지는 시기에는 생긴 돈도 작게 남습니다. 지출 한도가 흐려지면 재물의 실속이 줄어듭니다."
        ),
        "premium_narrative": (
            "결국 이 재물운은 벌어들인 돈이 생활 기반과 자산으로 남을 때 가장 확실합니다."
        ),
        "premium_strategy": (
            "받을 돈의 기준을 먼저 세웁니다. 손에 남는 금액도 바로 확인합니다. 지급 시점도 따로 챙깁니다. 지출 한도는 좁게 잡습니다."
        ),
    },
    "career": {
        "summary_to_feature": (
            "이 시기의 직업운은 맡는 책임과 공식 인정이 함께 커지는 시기입니다."
        ),
        "feature_to_action": (
            "맡게 되는 책임이 먼저 커집니다. 결정권 문제도 따로 다루게 됩니다."
        ),
        "action_to_caution": (
            "일의 범위가 흐린 자리는 부담이 먼저 커집니다. 결정권이 약하면 인정도 피로로 바뀝니다."
        ),
        "premium_narrative": (
            "결국 이 직업운은 해낸 일이 인정과 권한으로 돌아올 때 크게 강해집니다."
        ),
        "premium_strategy": (
            "일의 범위를 먼저 잡습니다. 맡게 되는 책임이 커집니다. 결정권도 또렷해집니다. 평가 기준도 선명해집니다."
        ),
    },
    "love": {
        "summary_to_feature": (
            "이 시기의 연애운은 마음이 연락 방식과 표현으로 확인되는 쪽이 강합니다."
        ),
        "feature_to_action": (
            "연락 방식이 달라지면서 호감이 전보다 잘 전달됩니다. 만남의 속도도 달라집니다."
        ),
        "action_to_caution": (
            "기대치가 말로 드러나지 않으면 오해가 반복됩니다. 표현 방식이 어긋나면 상대가 부담을 느낍니다."
        ),
        "premium_narrative": (
            "결국 이 연애운은 마음이 연락과 만남으로 이어질 때 오래 갑니다."
        ),
        "premium_strategy": (
            "연락 방식이 먼저 바뀝니다. 만남의 속도도 달라집니다. 기대치가 말로 정리됩니다."
        ),
    },
    "marriage": {
        "summary_to_feature": (
            "이 시기의 결혼운은 애정이 생활 방식과 약속으로 옮겨지는 쪽이 강합니다."
        ),
        "feature_to_action": (
            "돈의 기준을 먼저 세우게 됩니다. 주거 문제도 결혼 이야기에서 따로 다룹니다."
        ),
        "action_to_caution": (
            "생활 기준이 어긋나는 관계에서는 서로 깊이 사랑해도 결혼 생활이 쉽게 안정되지 않습니다. 역할 분담이 늦어지면 부담이 커집니다."
        ),
        "premium_narrative": (
            "결국 이 결혼운은 감정의 확신이 생활의 약속으로 옮겨질 때 안정됩니다."
        ),
        "premium_strategy": (
            "생활 기준을 먼저 세웁니다. 돈의 기준도 따로 정합니다. 주거 문제도 구체적으로 다룹니다. 역할 분담도 바로 말하게 됩니다."
        ),
    },
}


def counseling_bridge(domain: Domain, bridge_key: str) -> str:
    """Return a fixed counseling bridge sentence for a domain and role."""

    return COUNSELING_BRIDGES.get(domain, {}).get(bridge_key, "")


def web_bridge_limit(tier: str) -> int:
    return WEB_BRIDGE_LIMIT_BY_TIER.get(tier, WEB_BRIDGE_LIMIT_BY_TIER["free"])
