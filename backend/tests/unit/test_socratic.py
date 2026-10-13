import pytest

from app.domain.socratic import HistoryTurn, build_turn


def test_reinforcement_learning_opens_with_the_agent_question() -> None:
    plan = build_turn("Teach me Reinforcement Learning", [], "socratic")
    assert plan.concept_slug == "agent-environment"
    assert plan.fallback_text == "What do you think an agent does in an environment?"
    assert "```mermaid" not in plan.fallback_text
    assert plan.stage == 0


def test_second_turn_still_asks_and_third_scaffolds() -> None:
    first = build_turn("Teach me Reinforcement Learning", [], "socratic")
    history = [
        HistoryTurn("user", "Teach me Reinforcement Learning"),
        HistoryTurn("assistant", first.fallback_text),
    ]
    second = build_turn(
        "It picks actions and gets rewards", history, "socratic", first.concept_slug
    )
    assert "?" in second.fallback_text
    assert "```mermaid" not in second.fallback_text
    longer = history + [
        HistoryTurn("user", "It picks actions and gets rewards"),
        HistoryTurn("assistant", second.fallback_text),
    ]
    third = build_turn("The environment does", longer, "socratic", first.concept_slug)
    assert "agent" in third.fallback_text.lower()
    assert "```mermaid" not in third.fallback_text


def test_later_turn_and_direct_mode_include_the_account() -> None:
    history = [HistoryTurn("assistant", "q") for _ in range(3)]
    plan = build_turn(
        "keep going on reinforcement learning", history, "socratic", "agent-environment"
    )
    assert "```mermaid" in plan.fallback_text
    direct = build_turn("Teach me Reinforcement Learning", [], "direct")
    assert "Try this" in direct.fallback_text


def test_answer_demand_does_not_dump_the_explanation() -> None:
    plan = build_turn("Just tell me what an MDP is", [], "socratic")
    assert (
        "Markov" in plan.fallback_text
        or "sufficient" in plan.fallback_text
        or "state" in plan.fallback_text.lower()
    )
    assert "$$" not in plan.fallback_text
    assert "Direct" in plan.fallback_text


def test_unknown_topic_and_bad_mode() -> None:
    plan = build_turn("hello there", [], "socratic")
    assert plan.concept_slug is None
    assert "reinforcement learning" in plan.fallback_text
    with pytest.raises(ValueError):
        build_turn("hello", [], "lecture")


def test_specific_concept_beats_the_track_name() -> None:
    plan = build_turn("How does Q-learning differ from reinforcement learning?", [], "socratic")
    assert plan.concept_slug == "q-learning"
