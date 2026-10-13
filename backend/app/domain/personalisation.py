"""How stored preferences change teaching, ranking, and plans.

The five-dimension model in the platform SRS is later. This module maps the
fields we already store onto tutor copy, catalog ranking, and study-plan size.
"""

from __future__ import annotations

STYLE_NOTES = {
    "visual": "Prefer a sketch, a mermaid process, or a concrete picture over a long paragraph.",
    "reading": "Prefer short, well-structured paragraphs and a definition before an example.",
    "hands_on": "Prefer a tiny experiment, a table of values, or a few lines of code they can run.",
    "auditory": "Prefer spoken rhythm and one analogy. Avoid dense notation until they ask.",
    "balanced": "Mix a definition, one example, and one check.",
}

MATHS_NOTES = {
    "none": "Do not use formulas. Explain in words.",
    "light": "At most one simple formula, then unpack it in words.",
    "moderate": "Standard notation is fine. Skip full proofs unless they ask.",
    "formal": "Proofs and derivations are welcome when they serve the question.",
}

PROGRAMMING_NOTES = {
    "none": "Do not show code unless they ask.",
    "some": "Short Python is fine. Name what each line does.",
    "daily": "Complete snippets and API names are welcome.",
}

ACADEMY_ROLES = {
    "reinforcement-learning-academy": "rl-engineer",
    "robotics-academy": "robotics-engineer",
    "llm-academy": "llm-engineer",
    "computer-vision-academy": "cv-engineer",
    "natural-language-processing-academy": "nlp-engineer",
    "federated-learning-academy": "fl-engineer",
    "modelling-and-simulation-academy": "simulation-engineer",
    "data-science-academy": "data-scientist",
}

ACADEMY_DOMAINS = {
    "foundations-academy": ("Python", "Statistics", "Linear Algebra", "Artificial Intelligence"),
    "reinforcement-learning-academy": ("Reinforcement Learning", "Machine Learning"),
    "robotics-academy": ("Robotics",),
    "llm-academy": ("LLM Engineering", "AI Research Methods"),
    "computer-vision-academy": ("Computer Vision", "Deep Learning"),
    "natural-language-processing-academy": ("LLM Engineering", "AI Research Methods"),
    "programming-academy": ("Python",),
    "data-science-academy": ("Statistics", "Python"),
}


def career_slug(goal: str | None) -> str | None:
    """Map an academy slug to a catalog career role, or pass a role through."""

    if not goal:
        return None
    if goal in ACADEMY_ROLES:
        return ACADEMY_ROLES[goal]
    return goal


def preferred_domains(goal: str | None) -> tuple[str, ...]:
    if not goal:
        return ()
    return ACADEMY_DOMAINS.get(goal, ())


def plan_limit(weekly_minutes: int | None) -> int:
    """About 25 minutes per concept, clamped so a plan stays readable."""

    if weekly_minutes is None:
        return 14
    return max(3, min(14, weekly_minutes // 25))


def plan_gap_days(weekly_minutes: int | None) -> int:
    if weekly_minutes is None or weekly_minutes >= 90:
        return 1
    return 2


def session_minutes(weekly_minutes: int | None) -> int | None:
    if weekly_minutes is None:
        return None
    return max(15, min(45, weekly_minutes // 3 or weekly_minutes))


def tutor_brief(
    *,
    learning_style: str | None = None,
    maths_comfort: str | None = None,
    programming_experience: str | None = None,
    career_goal: str | None = None,
    weekly_minutes: int | None = None,
    display_name: str | None = None,
) -> str:
    """System-note fragment. Do not mention that this came from a settings form."""

    lines = ["Learner profile (adapt to this; do not recite it):"]
    if display_name:
        lines.append(f"- Call them {display_name} if you greet them.")
    if career_goal:
        label = career_goal.replace("-", " ").replace(" academy", "")
        lines.append(f"- Their goal academy is {label}. Tie examples there when it helps.")
    style = learning_style or "balanced"
    style_note = STYLE_NOTES.get(style, STYLE_NOTES["balanced"])
    lines.append(f"- Style ({style.replace('_', '-')}): {style_note}")
    if maths_comfort:
        maths_note = MATHS_NOTES.get(maths_comfort, MATHS_NOTES["moderate"])
        lines.append(f"- Maths ({maths_comfort}): {maths_note}")
    if programming_experience:
        prog_note = PROGRAMMING_NOTES.get(
            programming_experience, PROGRAMMING_NOTES["some"]
        )
        lines.append(f"- Programming ({programming_experience}): {prog_note}")
    minutes = session_minutes(weekly_minutes)
    if minutes:
        lines.append(
            f"- Keep this turn to about {minutes} minutes of work: one idea and one check."
        )
    return "\n".join(lines)
