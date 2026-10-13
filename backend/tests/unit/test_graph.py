import pytest

from app.domain.catalog import CONCEPTS, PATHS, QUESTIONS, get_concept
from app.domain.graph import (
    expand_with_prerequisites,
    mermaid,
    missing_prerequisites,
    recommend,
    topological,
)


def test_catalog_prerequisites_exist_and_do_not_cycle() -> None:
    slugs = {concept.slug for concept in CONCEPTS}
    for concept in CONCEPTS:
        assert set(concept.prerequisites) <= slugs
        assert len(concept.checks) >= 1
    assert topological(slugs)
    for path in PATHS:
        assert set(path.concepts) <= slugs
    for question in QUESTIONS:
        assert get_concept(question.concept) is not None


def test_new_learner_is_not_sent_to_ppo() -> None:
    slugs = [item.slug for item in recommend({}, limit=6)]
    assert "ai-fundamentals" in slugs
    assert "python-for-ml" in slugs
    assert "ppo" not in slugs
    assert "q-learning" not in slugs


def test_mastered_fundamentals_unlock_the_next_concepts() -> None:
    slugs = [item.slug for item in recommend({"ai-fundamentals": 80}, limit=6)]
    assert "ai-fundamentals" not in slugs
    assert "agent-environment" in slugs


def test_ppo_plan_includes_the_mdp_before_ppo() -> None:
    order = expand_with_prerequisites(["ppo"])
    assert order.index("mdp") < order.index("ppo")
    assert order.index("policy-gradient") < order.index("ppo")


def test_missing_prerequisites_and_cycle_guard() -> None:
    assert "mdp" in missing_prerequisites("bellman", set())
    assert missing_prerequisites("bellman", {"mdp"}) == []
    with pytest.raises(KeyError):
        missing_prerequisites("not-a-concept", set())


def test_mermaid_contains_the_agent_loop_concept() -> None:
    diagram = mermaid("Reinforcement Learning")
    assert "flowchart TD" in diagram
    assert "Agent and Environment" in diagram
