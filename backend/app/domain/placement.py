"""Authored placement items. The diagnostic never awards XP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlacementItem:
    id: str
    prompt: str
    options: tuple[str, ...]
    answer: str
    academy_slug: str


ITEMS: tuple[PlacementItem, ...] = (
    PlacementItem(
        id="agent-loop",
        prompt="An agent in reinforcement learning mainly does which of these?",
        options=(
            "A. Compresses a dataset into a smaller table",
            "B. Chooses actions, then sees a new state and a reward",
            "C. Labels images that a human already classified",
            "D. Translates a prompt into another language",
        ),
        answer="B",
        academy_slug="reinforcement-learning-academy",
    ),
    PlacementItem(
        id="python-return",
        prompt="In Python, a function with no `return` statement evaluates to which value?",
        options=("A. 0", "B. False", "C. None", "D. An empty string"),
        answer="C",
        academy_slug="foundations-academy",
    ),
    PlacementItem(
        id="robot-loop",
        prompt="ROS 2 is most useful because it gives a robot which of these?",
        options=(
            "A. A proof that the policy is optimal",
            "B. Named topics, nodes, and a clock so software can share sensor and command messages",
            "C. A GPU compiler for transformer weights",
            "D. A replacement for the motor drivers",
        ),
        answer="B",
        academy_slug="robotics-academy",
    ),
    PlacementItem(
        id="grounded-llm",
        prompt="Why ground a language-model answer in retrieved passages?",
        options=(
            "A. So the model can skip the tokenizer",
            "B. So the reply can cite text the system actually has, instead of inventing a source",
            "C. So every user shares one conversation",
            "D. So the context window becomes infinite",
        ),
        answer="B",
        academy_slug="llm-academy",
    ),
)


def public_items() -> list[dict]:
    """Questions without answer keys, for the onboarding diagnostic."""

    return [
        {
            "id": item.id,
            "prompt": item.prompt,
            "options": list(item.options),
            "academy_slug": item.academy_slug,
        }
        for item in ITEMS
    ]


def grade_answers(answers: list[dict]) -> dict[str, bool]:
    """Map item id to whether the chosen letter matches the authored key."""

    keyed = {item.id: item for item in ITEMS}
    result: dict[str, bool] = {}
    for row in answers:
        item_id = str(row.get("id") or "")
        item = keyed.get(item_id)
        if item is None:
            continue
        chosen = str(row.get("response") or "").strip().upper()[:1]
        result[item_id] = chosen == item.answer
    return result


def recommend_academy(
    *,
    goal_slug: str,
    programming_experience: str | None,
    results: dict[str, bool],
) -> str:
    """Prefer the chosen academy, unless the learner still needs Foundations first."""

    if programming_experience == "none":
        return "foundations-academy"
    foundations = next((item for item in ITEMS if item.academy_slug == "foundations-academy"), None)
    if foundations and results.get(foundations.id) is False:
        return "foundations-academy"
    return goal_slug
