import pytest

from app.domain.code_review import review_notes
from app.domain.sandbox import SandboxPolicyError, validate_source


def test_validate_allows_a_small_gridworld_step() -> None:
    validate_source("import math\nenv = GridWorld()\nprint(env.reset())\n")


def test_validate_blocks_os_dunder_and_open() -> None:
    with pytest.raises(SandboxPolicyError):
        validate_source("import os\nos.system('ls')\n")
    with pytest.raises(SandboxPolicyError):
        validate_source("x = ().__class__\n")
    with pytest.raises(SandboxPolicyError):
        validate_source("open('secrets.txt')\n")


def test_review_notes_flag_missing_structure() -> None:
    notes = review_notes("env = GridWorld()\nprint(env.reset())\n")
    assert any("function" in note.lower() for note in notes)
    assert any("loop" in note.lower() for note in notes)


def test_review_notes_accept_a_documented_function() -> None:
    source = 'def one_step():\n    """Take one step east."""\n    return 1\n'
    notes = review_notes(source)
    assert any("readable" in note.lower() for note in notes)
