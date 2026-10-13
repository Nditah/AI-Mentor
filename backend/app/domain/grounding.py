"""A critique that does not mention a supplied citation is discarded."""

from __future__ import annotations

import re


def extract_equations(text: str) -> list[str]:
    display = re.findall(r"\$\$(.+?)\$\$", text, flags=re.DOTALL)
    inline = re.findall(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", text)
    found = [item.strip() for item in display + inline if item.strip()]
    unique: list[str] = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique[:12]


def grounded(text: str, citations: list[str]) -> bool:
    if not text.strip() or not citations:
        return False
    return any(citation in text for citation in citations)
