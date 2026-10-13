"""Static policy for learner code. The subprocess runner enforces a second line of defense."""

from __future__ import annotations

import ast

ALLOWED_IMPORTS = frozenset(
    {
        "math",
        "random",
        "statistics",
        "itertools",
        "functools",
        "collections",
        "dataclasses",
        "typing",
    }
)
BANNED_CALLS = frozenset(
    {
        "exec",
        "eval",
        "open",
        "compile",
        "__import__",
        "input",
        "breakpoint",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "vars",
        "help",
        "memoryview",
    }
)


class SandboxPolicyError(ValueError):
    pass


def validate_source(source: str, max_length: int = 20_000) -> None:
    if not source.strip():
        raise SandboxPolicyError("Write some Python before running it.")
    if len(source) > max_length:
        raise SandboxPolicyError("That file is over the 20,000 character lab limit.")
    if "\x00" in source:
        raise SandboxPolicyError("The file contains a null byte.")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SandboxPolicyError(f"Syntax error: {exc.msg}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise SandboxPolicyError(f"Import not allowed: {root}")
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                raise SandboxPolicyError("Relative imports are not allowed.")
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise SandboxPolicyError(f"Import not allowed: {root or 'unknown'}")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr.startswith("__")
            and node.attr.endswith("__")
        ):
            raise SandboxPolicyError(f"Dunder access is not allowed: {node.attr}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_CALLS:
                raise SandboxPolicyError(f"Call not allowed: {node.func.id}")
        elif (
            isinstance(node, ast.Name)
            and node.id in BANNED_CALLS
            and isinstance(node.ctx, ast.Load)
        ):
            raise SandboxPolicyError(f"Name not allowed: {node.id}")
