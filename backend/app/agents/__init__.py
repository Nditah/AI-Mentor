"""Agents phrase. They do not decide pedagogy, grades, or job requirements."""

from __future__ import annotations

import json

from app.domain.catalog import get_concept
from app.domain.grounding import grounded
from app.domain.prompt_guard import fence_untrusted
from app.domain.socratic import TurnPlan
from app.prompts import load_prompt
from app.services.llm import ProviderRouter


def _json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


class QuizAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def coach(self, concept_name: str, difficulty: str) -> str | None:
        return self.provider.complete(
            system=load_prompt("security", "quiz"),
            messages=[
                (
                    "user",
                    "COACH: two sentences on how to approach a "
                    f"{difficulty} quiz on {concept_name}. Do not reveal an answer key.",
                )
            ],
            max_tokens=200,
        )


class TutorAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def reply(
        self,
        plan: TurnPlan,
        history: list[tuple[str, str]],
        message: str,
        profile_note: str = "",
    ) -> str:
        return "".join(self.reply_stream(plan, history, message, profile_note))

    def reply_stream(
        self,
        plan: TurnPlan,
        history: list[tuple[str, str]],
        message: str,
        profile_note: str = "",
    ):
        """Yield the scripted opener for stages 0–1; otherwise stream the model."""

        if plan.mode == "socratic" and plan.stage < 2:
            yield plan.fallback_text
            return
        prompt_name = "socratic" if plan.mode == "socratic" else "tutor"
        system = load_prompt("security", prompt_name) + f"\n\nStage note:\n{plan.system_note}"
        if profile_note:
            system += f"\n\n{profile_note}"
        concept = get_concept(plan.concept_slug) if plan.concept_slug else None
        if concept is not None:
            system += f"\n\nCurriculum account:\n{concept.explanation}"
        messages = [*history, ("user", fence_untrusted("learner", message))]
        yielded = False
        for piece in self.provider.stream(system=system, messages=messages):
            if piece:
                yielded = True
                yield piece
        if not yielded:
            yield plan.fallback_text


class ResearchAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def critique(self, excerpts: list[tuple[str, str]]) -> dict[str, str]:
        """Return only fields that cite a label we supplied."""

        empty = {"summary": "", "critique": "", "gaps": "", "future_work": ""}
        if not excerpts:
            return empty
        labels = [label for label, _text in excerpts]
        body = "\n\n".join(fence_untrusted(label, text) for label, text in excerpts)
        system = load_prompt("security", "research")
        raw = self.provider.complete(
            system=system,
            messages=[("user", body)],
            max_tokens=900,
        )
        parsed = _json_object(raw or "")
        if parsed is None:
            return empty
        kept = dict(empty)
        for key in empty:
            value = parsed.get(key)
            if isinstance(value, str) and grounded(value, labels):
                kept[key] = value.strip()
        return kept


class CodingAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def narrate(self, code: str, notes: list[str], run: dict[str, str]) -> str | None:
        system = load_prompt("security", "coding")
        message = (
            "Notes already decided:\n- " + "\n- ".join(notes) + "\n\n"
            f"Run status: {run['status']}\n"
            f"{fence_untrusted('stdout', run.get('stdout', ''))}\n"
            f"{fence_untrusted('stderr', run.get('stderr', ''))}\n"
            f"{fence_untrusted('code', code)}"
        )
        return self.provider.complete(system=system, messages=[("user", message)], max_tokens=500)


class PlannerAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def explain(self, goal: str, titles: list[str]) -> str | None:
        system = load_prompt("security", "planner")
        sequence = "\n".join(f"{index}. {title}" for index, title in enumerate(titles, start=1))
        return self.provider.complete(
            system=system,
            messages=[("user", f"Goal:\n{goal}\n\nSequence:\n{sequence}")],
            max_tokens=400,
        )


class CareerAgent:
    def __init__(self, provider: ProviderRouter) -> None:
        self.provider = provider

    def explain(self, payload: str) -> str | None:
        return self.provider.complete(
            system=load_prompt("security", "career"),
            messages=[("user", payload)],
            max_tokens=400,
        )
