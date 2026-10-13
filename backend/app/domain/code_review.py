"""Heuristic review that is always available, with or without a model."""

from __future__ import annotations

import ast

from app.domain.sandbox import SandboxPolicyError, validate_source


def review_notes(source: str) -> list[str]:
    notes: list[str] = []
    try:
        validate_source(source)
    except SandboxPolicyError as exc:
        return [str(exc)]
    tree = ast.parse(source)
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    loops = [node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))]
    bare = [
        node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and node.type is None
    ]
    if not functions:
        notes.append("Define at least one function so the next reader can test a single idea.")
    else:
        for function in functions:
            if ast.get_docstring(function) is None and function.name != "main":
                notes.append(f"`{function.name}` has no docstring. Say what it returns.")
                break
    if bare:
        notes.append(
            "A bare `except` also catches KeyboardInterrupt-style control flow. Name the error."
        )
    if not loops and "GridWorld" in source:
        notes.append(
            "A Q-learning update needs a loop over episodes or steps. This file has none yet."
        )
    if not notes:
        notes.append(
            "The structure is readable. Next, check the update rule against a hand-computed step."
        )
    return notes
