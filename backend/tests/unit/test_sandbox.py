import pytest

from app.domain.code_review import review_notes
from app.domain.sandbox import SandboxPolicyError, validate_source


def test_validate_allows_a_small_gridworld_step() -> None:
    validate_source("import math\nenv = GridWorld()\nprint(env.reset())\n")


def test_validate_allows_ordinary_learner_code() -> None:
    validate_source(
        "import random\nfrom collections import defaultdict\n"
        "from collections.abc import Iterable\nfrom dataclasses import dataclass\n"
        "q = defaultdict(float)\nx = random.random()\n"
        "print('{} {:.2f}'.format('reward', x), f'{q[0]}')\n"
    )


def test_validate_blocks_os_dunder_and_open() -> None:
    with pytest.raises(SandboxPolicyError):
        validate_source("import os\nos.system('ls')\n")
    with pytest.raises(SandboxPolicyError):
        validate_source("x = ().__class__\n")
    with pytest.raises(SandboxPolicyError):
        validate_source("open('secrets.txt')\n")


@pytest.mark.parametrize(
    "source",
    [
        "import random\nrandom._os.system('id')\n",
        "import random\nprint(random._os.getcwd())\n",
        "import typing\ntyping.sys.modules['os'].system('id')\n",
        "import dataclasses\nprint(dataclasses.inspect.stack())\n",
        "import statistics\nprint(statistics.sys.modules)\n",
        "from typing import sys\n",
        "from collections import *\n",
        "import collections.abc as c\nc.sys\n",
        "import os.path\n",
        "import functools\nfunctools.reduce.__self__\n",
        "def g():\n    yield g.gi_frame.f_back.f_globals\n",
        "try:\n    1 / 0\nexcept Exception as e:\n    e.with_traceback(None)\n",
        "import random\n'{0._os}'.format(random)\n",
        "import random\n'{0[x]}'.format_map({'x': random})\n",
        "fmt = '{0.x}'\nfmt.format(1)\n",
        "print(__builtins__)\n",
        "f = lambda: 0\nprint(f.co_consts)\n",
    ],
)
def test_validate_blocks_known_escapes(source: str) -> None:
    with pytest.raises(SandboxPolicyError):
        validate_source(source)


def test_validate_rejects_empty_oversized_and_null_sources() -> None:
    for source in ("   ", "x = 1\n" * 5000, "print(1)\x00", "def ("):
        with pytest.raises(SandboxPolicyError):
            validate_source(source)


def test_review_notes_flag_missing_structure() -> None:
    notes = review_notes("env = GridWorld()\nprint(env.reset())\n")
    assert any("function" in note.lower() for note in notes)
    assert any("loop" in note.lower() for note in notes)


def test_review_notes_accept_a_documented_function() -> None:
    source = 'def one_step():\n    """Take one step east."""\n    return 1\n'
    notes = review_notes(source)
    assert any("readable" in note.lower() for note in notes)
