"""Socratic policy. The model may phrase the turn. It does not choose the pedagogy."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.catalog import Concept, detect_concept, get_concept

_WANTS_ANSWER = re.compile(
    r"\b(just tell me|give me the answer|stop asking|explain it directly)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HistoryTurn:
    role: str
    content: str


@dataclass(frozen=True)
class TurnPlan:
    mode: str
    stage: int
    concept_slug: str | None
    system_note: str
    fallback_text: str


def build_turn(
    message: str,
    history: list[HistoryTurn],
    mode: str,
    sticky_slug: str | None = None,
) -> TurnPlan:
    if mode not in {"socratic", "direct"}:
        raise ValueError("mode must be socratic or direct")
    stage = sum(1 for turn in history if turn.role == "assistant")
    detected = detect_concept(message)
    sticky = get_concept(sticky_slug) if sticky_slug else None
    concept = detected or sticky
    wants_answer = _WANTS_ANSWER.search(message) is not None
    return TurnPlan(
        mode=mode,
        stage=stage,
        concept_slug=None if concept is None else concept.slug,
        system_note=_system_note(mode, stage, wants_answer),
        fallback_text=_fallback(concept, mode, stage, wants_answer),
    )


def _system_note(mode: str, stage: int, wants_answer: bool) -> str:
    if mode == "direct":
        return (
            "Explain the concept with the supplied account and the exercise. "
            "You may add one short example. Do not invent a different definition."
        )
    if wants_answer and stage < 3:
        return (
            "The learner asked for the answer. Give the short scaffold only, then one question. "
            "Tell them Direct mode exists. Do not dump the full explanation yet."
        )
    if stage <= 0:
        return "Ask the opening question and nothing else. Do not define the term."
    if stage == 1:
        return (
            "Reflect the learner's idea in one sentence. Ask the next check. Do not explain fully."
        )
    if stage == 2:
        return "Give only the scaffold paragraph, then one check question."
    return "Give the explanation and the exercise. Stop there and wait for an attempt."


def _fallback(concept: Concept | None, mode: str, stage: int, wants_answer: bool) -> str:
    if concept is None:
        return (
            "I can teach this properly once the target is specific. "
            "Do you want AI fundamentals, Python, reinforcement learning, "
            "robotics, or research methods? "
            "What are you trying to become able to do?"
        )
    if mode == "direct" or stage >= 3:
        return f"## {concept.name}\n\n{concept.explanation}\n\n### Try this\n\n{concept.exercise}"
    if wants_answer:
        return (
            f"{concept.scaffold}\n\n"
            "Switch the tutor to Direct if you want the full account now. "
            f"Otherwise: {concept.checks[0]}"
        )
    if stage <= 0:
        return concept.opener
    if stage == 1:
        return f"You're on a real part of {concept.name}.\n\n{concept.checks[0]}"
    return f"{concept.scaffold}\n\n{concept.checks[min(1, len(concept.checks) - 1)]}"
