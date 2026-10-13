"""Load the agent prompts shipped with the package."""

from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent


def load_prompt(*names: str) -> str:
    parts = []
    for name in names:
        path = _DIR / f"{name}.md"
        if not path.is_file():
            raise FileNotFoundError(f"Missing prompt: {name}")
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts)
