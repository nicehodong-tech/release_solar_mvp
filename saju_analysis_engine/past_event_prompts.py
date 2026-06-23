"""Customer-facing past-event prompt contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .constants import DOMAIN_ORDER
from .models import Domain, PastEventAnswer


@dataclass(frozen=True)
class PastEventPromptOption:
    key: str
    label: str
    answer: str
    help_text: str

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "answer": self.answer,
            "help_text": self.help_text,
        }


@dataclass(frozen=True)
class PastEventPrompt:
    prompt_id: str
    domain: Domain
    question: str
    options: tuple[PastEventPromptOption, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "prompt_id": self.prompt_id,
            "domain": self.domain,
            "question": self.question,
            "options": [option.to_dict() for option in self.options],
        }


PROMPT_OPTIONS: tuple[PastEventPromptOption, ...] = (
    PastEventPromptOption(
        key="yes",
        label="예, 있었습니다",
        answer="matched",
        help_text="오래 생각하지 않아도 바로 떠오를 때 선택합니다.",
    ),
    PastEventPromptOption(
        key="some",
        label="조금 있었습니다",
        answer="partial",
        help_text="비슷한 일은 있었지만 확신하기 어려울 때 선택합니다.",
    ),
    PastEventPromptOption(
        key="no",
        label="아니요",
        answer="unmatched",
        help_text="비슷한 일이 거의 떠오르지 않을 때 선택합니다.",
    ),
    PastEventPromptOption(
        key="skip",
        label="잘 모르겠습니다",
        answer="skipped",
        help_text="기억이 애매하거나 답하고 싶지 않을 때 선택합니다.",
    ),
)

DOMAIN_PROMPT_QUESTIONS: dict[Domain, str] = {
    "money": "최근 몇 년 사이, 수입이 늘었거나 돈을 관리하는 기준이 달라진 일이 있으셨습니까?",
    "career": "최근 몇 년 사이, 맡은 일이나 평가받는 방식이 달라진 일이 있으셨습니까?",
    "love": "최근 몇 년 사이, 마음이 가는 사람과의 연락이나 감정 표현에서 변화가 있었습니까?",
    "marriage": "최근 몇 년 사이, 결혼·동거·가족 책임처럼 함께 정해야 하는 문제가 중요해진 적이 있으셨습니까?",
}


def build_past_event_prompts(
    domains: Iterable[Domain] | None = None,
    *,
    max_prompts: int = 4,
) -> list[PastEventPrompt]:
    """Build light-weight past-event prompts for optional calibration."""

    if not isinstance(max_prompts, int) or isinstance(max_prompts, bool):
        raise ValueError("max_prompts must be a non-negative integer")
    if max_prompts < 0:
        raise ValueError("max_prompts must be a non-negative integer")
    if max_prompts == 0:
        return []

    if domains is None:
        selected_domains = list(DOMAIN_ORDER)
    elif isinstance(domains, str):
        selected_domains = [domains]
    else:
        selected_domains = list(domains)
    unsupported_domains = sorted(set(selected_domains).difference(DOMAIN_ORDER))
    if unsupported_domains:
        raise ValueError(f"Unsupported prompt domains: {', '.join(unsupported_domains)}")

    prompts: list[PastEventPrompt] = []
    seen_domains: set[str] = set()
    for domain in selected_domains:
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        prompts.append(
            PastEventPrompt(
                prompt_id=f"past_event_{domain}",
                domain=domain,
                question=DOMAIN_PROMPT_QUESTIONS[domain],
                options=PROMPT_OPTIONS,
            )
        )
        if len(prompts) >= max_prompts:
            break
    return prompts


def answer_from_prompt(
    prompt: PastEventPrompt,
    option_key: str,
    *,
    year: int | None = None,
) -> PastEventAnswer:
    """Convert one customer-facing option selection into engine input."""

    option_by_key = {option.key: option for option in prompt.options}
    if option_key not in option_by_key:
        raise ValueError(f"Unsupported past-event option: {option_key}")
    option = option_by_key[option_key]
    return PastEventAnswer(
        event_key=prompt.prompt_id,
        answer=option.answer,
        year=year,
        domain=prompt.domain,
    )
