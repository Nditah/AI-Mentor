from datetime import date

from app.domain.graph import recommend
from app.domain.personalisation import career_slug, plan_limit, tutor_brief
from app.domain.planner import build_study_plan


def test_tutor_brief_adapts_style_and_maths():
    note = tutor_brief(
        learning_style="hands_on",
        maths_comfort="none",
        programming_experience="none",
        career_goal="reinforcement-learning-academy",
        weekly_minutes=60,
        display_name="Ada",
    )
    assert "hands-on" in note
    assert "Do not use formulas" in note
    assert "Do not show code" in note
    assert "Ada" in note
    assert "20 minutes" in note or "15 minutes" in note or "45 minutes" in note


def test_academy_slug_maps_to_career_role():
    assert career_slug("reinforcement-learning-academy") == "rl-engineer"
    assert career_slug("rl-engineer") == "rl-engineer"


def test_recommend_prefers_goal_domain():
    hits = recommend({"ai-fundamentals": 80}, limit=4, prefer_domains=("Reinforcement Learning",))
    assert hits
    from app.domain.catalog import get_concept

    assert get_concept(hits[0].slug).domain == "Reinforcement Learning"


def test_short_week_makes_a_shorter_plan():
    assert plan_limit(30) < plan_limit(300)
    dense = build_study_plan("I want to learn PPO", {}, date(2026, 10, 13), weekly_minutes=300)
    light = build_study_plan("I want to learn PPO", {}, date(2026, 10, 13), weekly_minutes=30)
    assert len(light) <= len(dense)
    assert light[1].scheduled_for > light[0].scheduled_for
