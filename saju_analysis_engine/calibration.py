"""Past-event calibration for confidence and domain priority."""

from __future__ import annotations

from dataclasses import replace

from .models import CalibrationProfile, EventPacket, PastEventAnswer


ANSWER_ALIASES = {
    "yes": "matched",
    "match": "matched",
    "matched": "matched",
    "partial": "partial",
    "some": "partial",
    "no": "unmatched",
    "unmatched": "unmatched",
    "unknown": "skipped",
    "skip": "skipped",
    "skipped": "skipped",
}

CONFIDENCE_ORDER = ["restricted", "low", "medium", "medium_high", "high"]


def _normalize_answer(answer: str) -> str:
    return ANSWER_ALIASES.get(answer.strip().lower(), "skipped")


def _clip(value: int) -> int:
    return max(0, min(100, value))


def _shift_confidence(confidence: str, step: int) -> str:
    index = CONFIDENCE_ORDER.index(confidence)
    return CONFIDENCE_ORDER[max(0, min(len(CONFIDENCE_ORDER) - 1, index + step))]


def build_calibration_profile(answers: list[PastEventAnswer] | None) -> CalibrationProfile:
    if not answers:
        return CalibrationProfile(
            status="not_checked",
            matched_count=0,
            partial_count=0,
            unmatched_count=0,
            skipped_count=0,
            domain_adjustments={},
            confidence_adjustment=0,
            basis_codes=[],
        )

    counts = {"matched": 0, "partial": 0, "unmatched": 0, "skipped": 0}
    domain_adjustments: dict[str, int] = {}
    basis_codes: list[str] = []

    for answer in answers:
        normalized = _normalize_answer(answer.answer)
        counts[normalized] += 1
        if answer.domain is not None:
            delta = {"matched": 6, "partial": 3, "unmatched": -6, "skipped": 0}[normalized]
            domain_adjustments[answer.domain] = domain_adjustments.get(answer.domain, 0) + delta
            if normalized != "skipped":
                basis_codes.append(f"past_{normalized}_{answer.domain}")

    confidence_adjustment = counts["matched"] * 2 + counts["partial"] - counts["unmatched"] * 2
    if counts["matched"] + counts["partial"] == 0 and counts["unmatched"] > 0:
        status = "weakly_matched"
    elif counts["matched"] >= 2:
        status = "matched"
    elif counts["partial"] or counts["matched"]:
        status = "partially_matched"
    else:
        status = "skipped"

    return CalibrationProfile(
        status=status,
        matched_count=counts["matched"],
        partial_count=counts["partial"],
        unmatched_count=counts["unmatched"],
        skipped_count=counts["skipped"],
        domain_adjustments={domain: max(-15, min(15, value)) for domain, value in domain_adjustments.items()},
        confidence_adjustment=max(-8, min(8, confidence_adjustment)),
        basis_codes=list(dict.fromkeys(basis_codes)),
    )


def apply_calibration_to_packets(packets: list[EventPacket], profile: CalibrationProfile) -> list[EventPacket]:
    if profile.status == "not_checked":
        return packets

    calibrated: list[EventPacket] = []
    for packet in packets:
        domain_delta = profile.domain_adjustments.get(packet.domain, 0)
        probability = _clip(packet.event_probability_score + domain_delta + profile.confidence_adjustment)
        confidence_step = 0
        if domain_delta + profile.confidence_adjustment >= 8:
            confidence_step = 1
        elif domain_delta + profile.confidence_adjustment <= -8:
            confidence_step = -1
        past_status = profile.status
        updated = replace(
            packet,
            event_probability_score=probability,
            confidence=_shift_confidence(packet.confidence, confidence_step),
            past_check_status=past_status,
            basis_codes=list(dict.fromkeys(packet.basis_codes + profile.basis_codes)),
            template_slots={
                **packet.template_slots,
                "confidence": _shift_confidence(packet.confidence, confidence_step),
                "past_check_status": past_status,
            },
        )
        from .rendering import render_event_preview

        calibrated.append(replace(updated, rendered_preview=render_event_preview(updated)))
    return calibrated
