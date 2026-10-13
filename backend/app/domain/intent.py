"""Coarse intent routing for the orchestrator. Dedicated endpoints remain the stable API."""

from __future__ import annotations

import re

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("quiz", re.compile(r"\b(quiz|test me|multiple choice)\b", re.I)),
    ("plan", re.compile(r"\b(study plan|schedule|what should i study)\b", re.I)),
    ("research", re.compile(r"\b(paper|pdf|summarize this|literature)\b", re.I)),
    ("code", re.compile(r"\b(review this code|my code|debug this|sandbox)\b", re.I)),
    ("career", re.compile(r"\b(job|career|hire|role should i)\b", re.I)),
)


def classify_intent(message: str) -> str:
    for name, pattern in _RULES:
        if pattern.search(message):
            return name
    return "tutor"
