"""Channel separation is the control. Keyword flags only catch the obvious cases."""

from __future__ import annotations

import re
from dataclasses import dataclass

_INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior|above) (instructions|prompts)"
    r"|disregard (your|the) (system|previous)"
    r"|you are now (a|an)\b"
    r"|reveal (your|the) system prompt)",
    re.IGNORECASE,
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass(frozen=True)
class ScreenResult:
    allowed: bool
    flags: tuple[str, ...]
    text: str


def screen_user_input(text: str, max_length: int = 8000) -> ScreenResult:
    if "\x00" in text or _CONTROL.search(text):
        return ScreenResult(False, ("control_characters",), "")
    cleaned = text.strip()
    if not cleaned:
        return ScreenResult(False, ("empty",), "")
    if len(cleaned) > max_length:
        return ScreenResult(False, ("too_long",), "")
    flags: list[str] = []
    if _INJECTION.search(cleaned):
        flags.append("prompt_injection")
        residual = _INJECTION.sub(" ", cleaned)
        residual = re.sub(r"\s+", " ", residual).strip(" .!?:;,-")
        if len(residual) < 12:
            return ScreenResult(False, ("prompt_injection", "injection_only"), "")
    return ScreenResult(True, tuple(flags), cleaned)


def fence_untrusted(label: str, text: str) -> str:
    safe_label = re.sub(r"[^a-zA-Z0-9_.:-]", "", label)[:80] or "source"
    safe = text.replace("</untrusted", "< /untrusted")
    return f'<untrusted source="{safe_label}">\n{safe}\n</untrusted>'
