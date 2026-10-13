"""Static policy for learner code.

This is the first filter, not a security boundary. The subprocess runner adds a
restricted import hook and resource limits, and production keeps the lab off
until learner code runs in an isolated, secret-free, network-less runtime.
"""

from __future__ import annotations

import ast
from string import Formatter

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
ALLOWED_SUBMODULES = frozenset({"collections.abc"})
# Allowed modules re-export other modules under public names (`typing.sys`,
# `dataclasses.inspect`, `statistics.sys`). Strings reach attributes the AST cannot
# see (`operator.attrgetter`). Frames and code objects reach the harness globals.
BANNED_ATTRIBUTES = frozenset(
    {
        "attrgetter",
        "builtins",
        "contextlib",
        "copy",
        "copyreg",
        "ctypes",
        "gc",
        "get_type_hints",
        "importlib",
        "inspect",
        "io",
        "keyword",
        "methodcaller",
        "modules",
        "operator",
        "os",
        "re",
        "stdlib_re",
        "subprocess",
        "sys",
        "types",
        "warnings",
        "with_traceback",
    }
)
_INTROSPECTION_PREFIXES = ("f_", "gi_", "cr_", "ag_", "tb_", "co_")
_FORMAT_METHODS = frozenset({"format", "format_map"})


class SandboxPolicyError(ValueError):
    pass


def _attribute_issue(name: str) -> str | None:
    if name.startswith("_"):
        return f"Private attribute access is not allowed: {name}"
    if name in BANNED_ATTRIBUTES:
        return f"Attribute not allowed: {name}"
    if name.startswith(_INTROSPECTION_PREFIXES):
        return f"Frame and code introspection is not allowed: {name}"
    return None


def _format_issue(call: ast.Call) -> str | None:
    """`str.format` resolves `{0.attr}` and `{0[key]}` at runtime, out of the AST's sight."""

    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr not in _FORMAT_METHODS:
        return None
    receiver = func.value
    if not (isinstance(receiver, ast.Constant) and isinstance(receiver.value, str)):
        return "Call .format only on a string literal, or use an f-string."
    try:
        fields = [field for _text, field, _spec, _conv in Formatter().parse(receiver.value)]
    except ValueError:
        return "That format string is malformed."
    if any(field and ("." in field or "[" in field) for field in fields):
        return "Format fields cannot reach attributes or items. Use an f-string."
    return None


def _module_allowed(name: str) -> bool:
    return name in ALLOWED_IMPORTS or name in ALLOWED_SUBMODULES


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
                if not _module_allowed(alias.name):
                    raise SandboxPolicyError(f"Import not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                raise SandboxPolicyError("Relative imports are not allowed.")
            module = node.module or ""
            if not _module_allowed(module):
                raise SandboxPolicyError(f"Import not allowed: {module or 'unknown'}")
            for alias in node.names:
                issue = _attribute_issue(alias.name)
                if alias.name == "*" or issue:
                    raise SandboxPolicyError(issue or "Star imports are not allowed.")
        elif isinstance(node, ast.Attribute):
            issue = _attribute_issue(node.attr)
            if issue:
                raise SandboxPolicyError(issue)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
                raise SandboxPolicyError(f"Call not allowed: {node.func.id}")
            issue = _format_issue(node)
            if issue:
                raise SandboxPolicyError(issue)
        elif isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise SandboxPolicyError(f"Dunder names are not allowed: {node.id}")
            if node.id in BANNED_CALLS and isinstance(node.ctx, ast.Load):
                raise SandboxPolicyError(f"Name not allowed: {node.id}")
