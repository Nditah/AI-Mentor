"""The three faculties that sit above academies.

World lists learning paths. Faculty and level are filters on that list, not
pages the learner has to open first. Academies are a third filter.
"""

from __future__ import annotations

FACULTIES: tuple[dict[str, str], ...] = (
    {
        "slug": "ai",
        "title": "AI",
        "summary": "Foundations, machine learning, reinforcement learning, and LLMs.",
    },
    {
        "slug": "robotics",
        "title": "Robotics",
        "summary": "The robot loop, ROS 2, and where a policy may touch a motor.",
    },
    {
        "slug": "data-science",
        "title": "Data Science",
        "summary": "Asking questions of data: exploration, modelling, and evidence.",
    },
)

LEVELS: tuple[dict[str, str], ...] = (
    {"slug": "beginner", "title": "Beginner"},
    {"slug": "intermediate", "title": "Intermediate"},
    {"slug": "advanced", "title": "Advanced"},
)

FACULTY_SLUGS = frozenset(item["slug"] for item in FACULTIES)


def faculty_ref(slug: str | None) -> dict[str, str]:
    """Title and summary for a faculty slug, defaulting to AI when unknown."""

    key = slug if slug in FACULTY_SLUGS else "ai"
    return next(item for item in FACULTIES if item["slug"] == key)
