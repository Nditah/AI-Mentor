"""Run learner code in a short-lived interpreter. This is not a microVM."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.domain.sandbox import SandboxPolicyError, validate_source
from app.services.harness_source import HARNESS


def execute_restricted(source: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code_path = root / "student.py"
        harness_path = root / "harness.py"
        code_path.write_text(source, encoding="utf-8")
        harness_path.write_text(HARNESS, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(harness_path), str(code_path)],
                capture_output=True,
                text=True,
                timeout=3,
                cwd=tmp,
                env={
                    "PATH": os.defpath,
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", "replace")
            return {
                "status": "error",
                "stdout": stdout[:8000],
                "stderr": "Timed out after 3 seconds.",
            }
        return {
            "status": "ok" if completed.returncode == 0 else "error",
            "stdout": (completed.stdout or "")[:8000],
            "stderr": (completed.stderr or "")[:8000],
        }


def run_student_code(source: str) -> dict[str, str]:
    try:
        validate_source(source)
    except SandboxPolicyError as exc:
        return {"status": "rejected", "stdout": "", "stderr": str(exc)}
    return execute_restricted(source)
