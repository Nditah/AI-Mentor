from datetime import date

from app.domain.career import match_roles
from app.domain.planner import build_study_plan


def test_ppo_plan_orders_prerequisites_and_dates_them() -> None:
    items = build_study_plan("I want to learn PPO", mastery={}, start=date(2026, 10, 13))
    slugs = [item.slug for item in items]
    assert slugs[0] != "ppo"
    assert slugs.index("mdp") < slugs.index("ppo")
    assert items[1].scheduled_for == date(2026, 10, 14)


def test_plan_skips_mastered_concepts() -> None:
    items = build_study_plan(
        "PPO",
        mastery={"mdp": 90, "agent-environment": 90, "ai-fundamentals": 90},
        start=date(2026, 1, 1),
    )
    assert "mdp" not in [item.slug for item in items]


def test_unknown_goal_uses_recommendations() -> None:
    items = build_study_plan("help me get started", mastery={}, start=date(2026, 1, 1))
    assert items
    assert items[0].slug == "ai-fundamentals"


def test_career_matches_do_not_invent_requirements() -> None:
    matches = match_roles({"q-learning": 80, "mdp": 80, "ppo": 20})
    rl = next(match for match in matches if match.title == "Reinforcement learning engineer")
    assert "Proximal Policy Optimization" in rl.missing
    assert rl.readiness < 80
