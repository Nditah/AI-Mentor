"""Grade a knowledge-check or assessment item. The answer key never leaves the server."""

from __future__ import annotations


def grade_item(kind: str, key: dict, response: object) -> bool:
    if kind in {"mcq", "true_false", "fill", "code"}:
        expected = str(key.get("correct", "")).strip().lower()
        return str(response).strip().lower() == expected
    if kind == "short":
        text = str(response).strip().lower()
        parts = [str(part).strip().lower() for part in key.get("contains", []) if str(part).strip()]
        return bool(parts) and all(part in text for part in parts)
    if kind == "order":
        given = response if isinstance(response, list) else []
        expected = key.get("order", [])
        return [str(item) for item in given] == [str(item) for item in expected]
    return False


def score_percent(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100 * correct / total, 1)
