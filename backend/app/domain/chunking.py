"""Paragraph chunker for retrieval. Overlap keeps equations from being cut in half."""

from __future__ import annotations

import re


def chunk_text(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    if size < 100:
        raise ValueError("chunk size must be at least 100 characters")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        stripped = text.strip()
        return [stripped] if stripped else []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}"
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= size:
            tail = current[-overlap:].strip() if current and overlap else ""
            current = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
            continue
        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + size])
            if start + size >= len(paragraph):
                break
            start += size - overlap
        current = ""
    if current:
        chunks.append(current)
    return chunks
