"""Deterministic graders. The model may write questions; it does not silently mark them."""

from __future__ import annotations

import re


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def resolve_mcq(response: str, options: list[str]) -> str:
    text = response.strip()
    if len(text) == 1 and text.upper() in "ABCDEFGH":
        index = ord(text.upper()) - 65
        if 0 <= index < len(options):
            return options[index]
    return text


def grade_mcq(response: str, options: list[str], answer: str) -> tuple[bool, float]:
    chosen = _norm(resolve_mcq(response, options))
    return chosen == _norm(answer), 1.0 if chosen == _norm(answer) else 0.0


def grade_short(response: str, phrases: list[str]) -> tuple[bool, float]:
    if not phrases:
        return False, 0.0
    haystack = _norm(response)
    hits = sum(1 for phrase in phrases if _norm(phrase) in haystack)
    ratio = hits / len(phrases)
    return ratio >= 0.6, ratio


def grade_coding(stdout: str, expected: str) -> tuple[bool, float]:
    if not expected.strip():
        return False, 0.0
    ok = expected.strip() in stdout
    return ok, 1.0 if ok else 0.0


def grade_research(response: str, phrases: list[str]) -> tuple[bool, float, str]:
    """Phrase coverage only, and the score is capped. Argument quality needs a model pass."""

    _passed, ratio = grade_short(response, phrases)
    capped = min(ratio, 0.7)
    return (
        capped >= 0.6,
        capped,
        (
            "Scored from rubric phrases only, and capped at 0.70. "
            "This pass does not judge whether the argument is any good."
        ),
    )
