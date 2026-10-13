# ruff: noqa: E501
"""Idempotent Microsoft Learn-style curriculum.

The Reinforcement Learning Academy is the worked example. Every other catalog
lesson gets topic pages so the reader never opens a single long article.
Restarting the API refreshes seed-owned pages and leaves authored pages and
learner progress alone.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Academy,
    Achievement,
    Assessment,
    AssessmentQuestion,
    Course,
    KnowledgeAsset,
    KnowledgeCheck,
    KnowledgeCheckQuestion,
    LearningPath,
    Lesson,
    LessonResource,
    Module,
    TopicPage,
)

STATE_PAGES: tuple[dict, ...] = (
    {
        "slug": "introduction",
        "title": "Introduction",
        "kind": "reading",
        "minutes": 4,
        "body": """A state is the information an agent needs about *now* in order to decide what to do next.

In a grid, that is often the cell the agent occupies. In a robot, it may be position and velocity. In a game, it is the board. The state is not the whole history of the episode. It is the summary that makes the future independent of the past.

You will use this idea on every later page of this path. When a formula writes *s*, it means this summary.""",
    },
    {
        "slug": "formal-definition",
        "title": "Formal Definition",
        "kind": "reading",
        "minutes": 5,
        "body": """A **state** *s* is an element of a state space *S*.

The Markov property says that the next state and the reward depend on the current state and the action, not on how the agent arrived there:

$$P(s_{t+1}, r_{t+1} \\mid s_t, a_t, s_{t-1}, a_{t-1}, \\ldots) = P(s_{t+1}, r_{t+1} \\mid s_t, a_t)$$

If that equality fails, the description is not yet a state. Add the missing fact (a velocity, a charge level, the previous card) until it holds.""",
    },
    {
        "slug": "real-world-example",
        "title": "Real World Example",
        "kind": "reading",
        "minutes": 4,
        "body": """A warehouse robot carries a parcel to a dock.

- The cell on the map is not enough if the parcel can fall. "Holding the parcel" has to be part of the state.
- Battery percentage matters when the robot can fail mid-aisle. Otherwise two visits to the same cell are not the same situation.
- The colour of the floor does not change the next cell, so it stays out of the state.

A good state is the smallest description that still lets you predict what happens next.""",
    },
    {
        "slug": "mathematical-representation",
        "title": "Mathematical Representation",
        "kind": "reading",
        "minutes": 5,
        "body": """Write a finite state as an index, a tuple, or a one-hot vector.

| Form | Example | When to use it |
| --- | --- | --- |
| Index | *s = 7* | A small grid, a lookup table |
| Tuple | *(x, y, holding)* | Several facts that combine |
| Vector | a bit for each fact | The input to a neural network later |

The set of every legal tuple is *S*. An illegal tuple (a robot outside the warehouse) is not a state of this problem.""",
    },
    {
        "slug": "visualization",
        "title": "Visualization",
        "kind": "reading",
        "minutes": 3,
        "body": """A 2×2 grid has four states. The agent is the filled cell.

```
[A] .     . [A]     .  .     .  .
 .  .     .  .     [A] .     . [A]
 s=0      s=1      s=2      s=3
```

Moving right from *s = 0* can only reach *s = 1*. The picture is the state space. The arrow is an action, which is the next lesson.""",
    },
    {
        "slug": "watch",
        "title": "Watch",
        "kind": "video",
        "minutes": 8,
        "body": "Watch the lecture introduction, then come back and name the state in your own words.",
        "catalog": {
            "slug": "david-silver-rl-intro",
            "title": "David Silver: Introduction to Reinforcement Learning",
            "url": "https://www.youtube.com/watch?v=2pWv7GOvuf0",
            "resource_type": "video",
            "tags": ["reinforcement-learning", "mdp"],
            "topic": "mdp",
            "skills": ["markov-decision-process"],
        },
    },
    {
        "slug": "name-the-state",
        "title": "Interactive exercise",
        "kind": "exercise",
        "minutes": 6,
        "body": (
            "A robot vacuum sees four squares. Write down a state that is enough to choose "
            "the next move, and one fact you would leave out because it does not change the choice."
        ),
        "catalog": {
            "slug": "name-the-grid-state",
            "title": "Name the state of a four-square room",
            "url": "",
            "resource_type": "coding_challenge",
            "tags": ["reinforcement-learning", "state"],
            "topic": "mdp",
            "skills": ["state-representation"],
        },
    },
    {
        "slug": "summary",
        "title": "Summary",
        "kind": "summary",
        "minutes": 2,
        "body": """- A state is a sufficient summary of the present.
- *S* is the set of those summaries.
- If two histories need different decisions, they are different states.
- Extra detail that never changes the next outcome can stay out of *S*.""",
    },
    {
        "slug": "knowledge-check",
        "title": "Knowledge Check",
        "kind": "knowledge_check",
        "minutes": 4,
        "body": "Answer from this lesson. You can retry. A pass is 70%.",
        "questions": (
            {
                "kind": "mcq",
                "prompt": "What must a state let the agent do?",
                "options": [
                    "A. Recite the whole episode",
                    "B. Decide the next action from the present",
                    "C. Store every reward it has ever seen",
                ],
                "answer": {"correct": "b"},
                "explanation": "A state is a sufficient summary of the present, not the full history.",
            },
            {
                "kind": "true_false",
                "prompt": "If two visits to the same place need different actions, they are the same state.",
                "options": ["True", "False"],
                "answer": {"correct": "false"},
                "explanation": "Different decisions mean the description is missing a fact, so they are different states.",
            },
            {
                "kind": "fill",
                "prompt": "The set of all states is written with which letter?",
                "options": [],
                "answer": {"correct": "s"},
                "explanation": "The state space is S. A single state is s.",
            },
        ),
    },
)


def _reading(title: str, idea: str) -> tuple[dict, ...]:
    return (
        {
            "slug": "introduction",
            "title": "Introduction",
            "kind": "reading",
            "minutes": 4,
            "body": f"# {title}\n\n{idea}\n\nRead this page, then the example, then take the check.",
        },
        {
            "slug": "example",
            "title": "Worked example",
            "kind": "reading",
            "minutes": 4,
            "body": f"## A concrete case\n\nApply **{title}** to a small grid world. Name the objects, the choice the agent makes, and what changes on the next step. If you cannot point at it on the grid, the idea is still abstract.",
        },
        {
            "slug": "knowledge-check",
            "title": "Knowledge Check",
            "kind": "knowledge_check",
            "minutes": 3,
            "body": "Pass mark 70%. You may retry.",
            "questions": (
                {
                    "kind": "mcq",
                    "prompt": f"This lesson is about {title}. Which statement matches it?",
                    "options": [
                        f"A. {idea}",
                        "B. A state is only the colour of the floor.",
                        "C. Rewards are chosen by the agent.",
                    ],
                    "answer": {"correct": "a"},
                    "explanation": idea,
                },
                {
                    "kind": "true_false",
                    "prompt": f"You can skip {title} and still claim the module.",
                    "options": ["True", "False"],
                    "answer": {"correct": "false"},
                    "explanation": "The module assessment assumes every lesson on this list.",
                },
            ),
        },
    )


def _lesson(slug: str, title: str, objectives: tuple[str, ...], pages: tuple[dict, ...]) -> dict:
    return {"slug": slug, "title": title, "objectives": objectives, "pages": pages}


RL_ACADEMY: dict = {
    "slug": "reinforcement-learning-academy",
    "title": "Reinforcement Learning Academy",
    "summary": "From the agent loop to policy optimisation, one page at a time.",
    "faculty": "ai",
    "paths": (
        {
            "slug": "rl-foundations",
            "title": "RL Foundations",
            "level": "beginner",
            "description": "The agent loop, Markov decision processes, Bellman equations, and Q-learning.",
            "gated": False,
            "courses": (
                {
                    "slug": "introduction-to-rl",
                    "title": "Introduction to RL",
                    "description": "Agents, environments, and why the reward is not the action.",
                    "modules": (
                        {
                            "slug": "the-agent-loop",
                            "title": "The agent loop",
                            "summary": "What acts, what responds, and what is scored.",
                            "lessons": (
                                _lesson(
                                    "agent-acts-environment-responds",
                                    "Agent and environment",
                                    ("Name the agent and the environment.",),
                                    _reading(
                                        "Agent and environment",
                                        "The agent chooses an action. The environment returns the next state and a reward.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
                {
                    "slug": "markov-decision-processes",
                    "title": "Markov Decision Processes",
                    "description": "States, actions, policies, and rewards as one decision process.",
                    "modules": (
                        {
                            "slug": "mdp-concepts",
                            "title": "MDP Concepts",
                            "summary": "The five pieces of an MDP.",
                            "lessons": (
                                _lesson(
                                    "what-is-an-mdp",
                                    "What is an MDP?",
                                    ("List the elements of an MDP.",),
                                    _reading(
                                        "What is an MDP?",
                                        "An MDP is a state space, an action space, transition probabilities, a reward function, and a discount.",
                                    ),
                                ),
                            ),
                        },
                        {
                            "slug": "states-and-actions",
                            "title": "States & Actions",
                            "summary": "What the agent can observe and what it can do.",
                            "lessons": (
                                _lesson(
                                    "what-is-a-state",
                                    "What is a State?",
                                    (
                                        "Explain a state as a sufficient summary of the present.",
                                        "Write a small state space S.",
                                        "Tell when two situations are different states.",
                                    ),
                                    STATE_PAGES,
                                ),
                                _lesson(
                                    "what-is-an-action",
                                    "What is an Action?",
                                    ("Distinguish a state from an action.",),
                                    _reading(
                                        "What is an Action?",
                                        "An action is a choice the agent makes in a state. The environment, not the agent, produces the next state.",
                                    ),
                                ),
                                _lesson(
                                    "state-spaces",
                                    "State Spaces",
                                    ("Describe a finite state space.",),
                                    _reading(
                                        "State Spaces",
                                        "The state space S is every state the problem allows. A grid cell outside the walls is not in S.",
                                    ),
                                ),
                                _lesson(
                                    "action-spaces",
                                    "Action Spaces",
                                    ("Describe a finite action space.",),
                                    _reading(
                                        "Action Spaces",
                                        "The action space A is every choice the agent can make. In a grid that is often up, down, left, and right.",
                                    ),
                                ),
                            ),
                        },
                        {
                            "slug": "policies",
                            "title": "Policies",
                            "summary": "A rule from states to actions.",
                            "lessons": (
                                _lesson(
                                    "what-is-a-policy",
                                    "What is a Policy?",
                                    ("Define a policy.",),
                                    _reading(
                                        "What is a Policy?",
                                        "A policy π maps a state to an action, or to probabilities over actions.",
                                    ),
                                ),
                            ),
                        },
                        {
                            "slug": "rewards",
                            "title": "Rewards",
                            "summary": "The scalar the environment emits.",
                            "lessons": (
                                _lesson(
                                    "what-is-a-reward",
                                    "What is a Reward?",
                                    ("Say who emits the reward.",),
                                    _reading(
                                        "What is a Reward?",
                                        "The environment emits a scalar reward. The agent does not choose it.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
                {
                    "slug": "bellman-equations",
                    "title": "Bellman Equations",
                    "description": "Value as an immediate reward plus a discounted next value.",
                    "modules": (
                        {
                            "slug": "bellman-idea",
                            "title": "The Bellman idea",
                            "summary": "Why value splits into now and later.",
                            "lessons": (
                                _lesson(
                                    "why-bellman",
                                    "Why the Bellman equation",
                                    ("State the Bellman backup in words.",),
                                    _reading(
                                        "Why the Bellman equation",
                                        "The value of a state is the expected reward now plus the discounted value of the next state.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
                {
                    "slug": "q-learning-course",
                    "title": "Q-Learning",
                    "description": "Learn an action value from sampled transitions.",
                    "modules": (
                        {
                            "slug": "q-learning-update",
                            "title": "The Q-learning update",
                            "summary": "One sample, one backup.",
                            "lessons": (
                                _lesson(
                                    "one-q-update",
                                    "One Q update",
                                    ("Write the Q-learning target.",),
                                    _reading(
                                        "One Q update",
                                        "The target is the reward plus gamma times the best next Q. The update moves the current Q toward that target.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
        {
            "slug": "deep-rl",
            "title": "Deep RL",
            "level": "intermediate",
            "description": "Function approximation when the table of states no longer fits.",
            "gated": True,
            "courses": (
                {
                    "slug": "value-networks",
                    "title": "Value networks",
                    "description": "Replace the Q table with a network.",
                    "modules": (
                        {
                            "slug": "from-tables-to-networks",
                            "title": "From tables to networks",
                            "summary": "Why a table stops scaling.",
                            "lessons": (
                                _lesson(
                                    "why-a-network",
                                    "Why a network",
                                    ("Say when a Q table is the wrong store.",),
                                    _reading(
                                        "Why a network",
                                        "A table needs one cell per state-action pair. A network shares weights across similar states.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
        {
            "slug": "policy-optimization",
            "title": "Policy Optimization",
            "level": "intermediate",
            "description": "Search directly over policies: policy gradient, PPO, and SAC.",
            "gated": True,
            "courses": (
                {
                    "slug": "policy-gradients",
                    "title": "Policy gradients",
                    "description": "Increase the probability of actions that led to return.",
                    "modules": (
                        {
                            "slug": "the-policy-gradient",
                            "title": "The policy gradient",
                            "summary": "A direction in policy space.",
                            "lessons": (
                                _lesson(
                                    "what-a-policy-gradient-does",
                                    "What a policy gradient does",
                                    ("Describe the policy gradient in one sentence.",),
                                    _reading(
                                        "What a policy gradient does",
                                        "A policy gradient raises the probability of actions that were followed by higher return.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
        {
            "slug": "advanced-rl",
            "title": "Advanced RL",
            "level": "advanced",
            "description": "Multi-agent settings and where a policy may touch a real robot.",
            "gated": True,
            "courses": (
                {
                    "slug": "beyond-the-single-agent",
                    "title": "Beyond one agent",
                    "description": "Other agents, and the gap between a simulator and a motor.",
                    "modules": (
                        {
                            "slug": "many-agents",
                            "title": "Many agents",
                            "summary": "When the environment contains other learners.",
                            "lessons": (
                                _lesson(
                                    "other-agents-are-not-noise",
                                    "Other agents are not noise",
                                    (
                                        "Explain why another learner is not a stationary transition.",
                                    ),
                                    _reading(
                                        "Other agents are not noise",
                                        "Another learning agent changes its policy, so the transition the first agent sees is not fixed.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
    ),
}

DS_ACADEMY: dict = {
    "slug": "data-science-academy",
    "title": "Data Science Academy",
    "summary": "Ask a question of a table before you fit a model.",
    "faculty": "data-science",
    "paths": (
        {
            "slug": "data-science-foundations",
            "title": "Data Science Foundations",
            "level": "beginner",
            "description": "What the table is, what the question is, and why a plot can change both.",
            "gated": False,
            "courses": (
                {
                    "slug": "asking-questions-of-data",
                    "title": "Asking questions of data",
                    "description": "A dataset is not a result. A question plus a table is the start of the work.",
                    "modules": (
                        {
                            "slug": "tables-and-questions",
                            "title": "Tables and questions",
                            "summary": "Name the rows, the columns, and the claim you want to test.",
                            "lessons": (
                                _lesson(
                                    "what-is-a-dataset",
                                    "What is a dataset?",
                                    ("Name the unit of a row and the question the table could answer.",),
                                    _reading(
                                        "What is a dataset?",
                                        "A dataset is a table you can ask a question of. Each row is one unit — a person, a trial, a day. Each column is a measurement of that unit. A chart that does not change what you would do next is decoration, not analysis.",
                                    ),
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
    ),
}

WRAPS = (
    (
        "foundations-academy",
        "Foundations Academy",
        "The maths and Python the later academies assume.",
        "ai-fundamentals",
        0,
        "ai",
    ),
    (
        "robotics-academy",
        "Robotics Academy",
        "The robot loop, ROS 2, and where a policy may touch a motor.",
        "robotics",
        2,
        "robotics",
    ),
    (
        "llm-academy",
        "LLM Engineering Academy",
        "Grounded language-model systems.",
        "llm-engineering",
        3,
        "ai",
    ),
)


def _upsert_page(session: Session, lesson: Lesson, spec: dict, position: int) -> TopicPage:
    page = session.scalar(
        select(TopicPage).where(TopicPage.lesson_id == lesson.id, TopicPage.slug == spec["slug"])
    )
    if page is None:
        page = TopicPage(lesson_id=lesson.id, slug=spec["slug"], origin="seed")
        session.add(page)
    if page.origin != "seed":
        return page
    page.title = spec["title"]
    page.kind = spec["kind"]
    page.body_md = spec["body"]
    page.position = position
    page.estimated_minutes = spec["minutes"]
    catalog = spec.get("catalog")
    if catalog:
        page.asset_id = _ensure_asset(session, catalog).id
    session.flush()
    questions = spec.get("questions")
    if questions:
        check = session.scalar(select(KnowledgeCheck).where(KnowledgeCheck.page_id == page.id))
        if check is None:
            check = KnowledgeCheck(page_id=page.id, title=spec["title"])
            session.add(check)
            session.flush()
        existing = session.scalars(
            select(KnowledgeCheckQuestion).where(KnowledgeCheckQuestion.check_id == check.id)
        ).all()
        if not existing:
            for index, question in enumerate(questions):
                session.add(
                    KnowledgeCheckQuestion(
                        check_id=check.id,
                        kind=question["kind"],
                        prompt=question["prompt"],
                        options=list(question["options"]),
                        answer_key=dict(question["answer"]),
                        explanation=question["explanation"],
                        position=index,
                    )
                )
    return page


def _ensure_assessment(
    session: Session,
    *,
    scope: str,
    title: str,
    module_id=None,
    course_id=None,
    path_id=None,
    prompt: str,
    correct_option: str,
    wrong_a: str,
    wrong_b: str,
) -> None:
    filters = [Assessment.scope == scope]
    if module_id is not None:
        filters.append(Assessment.module_id == module_id)
    if course_id is not None:
        filters.append(Assessment.course_id == course_id)
    if path_id is not None:
        filters.append(Assessment.path_id == path_id)
    row = session.scalar(select(Assessment).where(*filters))
    if row is not None:
        return
    row = Assessment(
        scope=scope,
        title=title,
        module_id=module_id,
        course_id=course_id,
        path_id=path_id,
        pass_score=70,
        xp_reward=40 if scope != "path" else 80,
    )
    session.add(row)
    session.flush()
    session.add(
        AssessmentQuestion(
            assessment_id=row.id,
            kind="mcq",
            prompt=prompt,
            options=[correct_option, wrong_a, wrong_b],
            answer_key={"correct": "a"},
            explanation=correct_option,
            position=0,
        )
    )


def _ensure_catalog_pages(session: Session, lesson: Lesson) -> None:
    existing = session.scalar(select(TopicPage.id).where(TopicPage.lesson_id == lesson.id))
    if existing is not None:
        return
    body = lesson.content_md or f"# {lesson.title}\n\nRead the idea, then try the check."
    parts = body.split("## Exercise", 1)
    _upsert_page(
        session,
        lesson,
        {
            "slug": "read",
            "title": "Read",
            "kind": "reading",
            "minutes": max(3, lesson.estimated_minutes // 2),
            "body": parts[0].strip(),
        },
        0,
    )
    if len(parts) > 1:
        _upsert_page(
            session,
            lesson,
            {
                "slug": "exercise",
                "title": "Exercise",
                "kind": "reading",
                "minutes": 5,
                "body": "## Exercise\n" + parts[1].strip(),
            },
            1,
        )
    word = next((part for part in lesson.title.split() if len(part) > 3), lesson.title)
    _upsert_page(
        session,
        lesson,
        {
            "slug": "knowledge-check",
            "title": "Knowledge Check",
            "kind": "knowledge_check",
            "minutes": 3,
            "body": "Pass mark 70%.",
            "questions": (
                {
                    "kind": "short",
                    "prompt": f"Name the subject of this lesson in a short phrase that includes “{word}”.",
                    "options": [],
                    "answer": {"contains": [word.lower()]},
                    "explanation": f"The lesson is {lesson.title}.",
                },
            ),
        },
        2 if len(parts) > 1 else 1,
    )


def seed_guided(session: Session) -> None:
    _seed_spec(session, RL_ACADEMY, 1)
    _seed_spec(session, DS_ACADEMY, 4)

    for slug, title, summary, path_slug, position, faculty in WRAPS:
        wrapped = _academy(session, slug, title, summary, position, faculty)
        path = session.scalar(select(LearningPath).where(LearningPath.slug == path_slug))
        if path is not None:
            path.academy_id = wrapped.id
        course = session.scalar(select(Course).where(Course.slug == path_slug))
        if course is not None and path is not None:
            course.path_id = path.id
            course.academy_id = wrapped.id

    badge = session.scalar(select(Achievement).where(Achievement.slug == "rl-foundations"))
    if badge is None:
        session.add(
            Achievement(
                slug="rl-foundations",
                name="RL Foundations",
                description="Completed the RL Foundations learning path.",
                xp_reward=0,
                icon="seal",
            )
        )

    for lesson in session.scalars(select(Lesson)).all():
        if lesson.module.slug is None:
            lesson.module.slug = f"{lesson.module.course.slug}-core"[:80]
        _ensure_catalog_pages(session, lesson)
    session.flush()


def _seed_spec(session: Session, spec: dict, position: int) -> None:
    academy = _academy(
        session, spec["slug"], spec["title"], spec["summary"], position, spec["faculty"]
    )
    for path_index, path_spec in enumerate(spec["paths"]):
        path = _path(session, academy, path_spec, path_index)
        for course_index, course_spec in enumerate(path_spec["courses"]):
            course = _course(session, academy, path, course_spec, course_index)
            for module_index, module_spec in enumerate(course_spec["modules"]):
                module = _module(session, course, module_spec, module_index)
                for lesson_index, lesson_spec in enumerate(module_spec["lessons"]):
                    lesson = _lesson_row(session, module, lesson_spec, lesson_index)
                    for page_index, page_spec in enumerate(lesson_spec["pages"]):
                        _upsert_page(session, lesson, page_spec, page_index)
                    if lesson.slug == "what-is-a-state":
                        _state_resources(session, lesson)
                _ensure_assessment(
                    session,
                    scope="module",
                    title=f"{module.title} assessment",
                    module_id=module.id,
                    prompt=f"Which lesson belongs in {module.title}?",
                    correct_option=f"A. {module_spec['lessons'][0]['title']}",
                    wrong_a="B. A leaderboard of click counts",
                    wrong_b="C. An uncited paper summary",
                )
            _ensure_assessment(
                session,
                scope="course",
                title=f"{course.title} assessment",
                course_id=course.id,
                prompt=f"You are finishing {course.title}. What should you be able to do?",
                correct_option=f"A. {course.description}",
                wrong_a="B. Skip every module and open the certificate",
                wrong_b="C. Treat the reward as something the agent chooses",
            )
        _ensure_assessment(
            session,
            scope="path",
            title=f"{path.title} completion",
            path_id=path.id,
            prompt=f"Completing {path.title} means you can:",
            correct_option=f"A. {path.description}",
            wrong_a="B. Ignore the module assessments",
            wrong_b="C. Memorise a video without a check",
        )


def _academy(
    session: Session, slug: str, title: str, summary: str, position: int, faculty: str
) -> Academy:
    row = session.scalar(select(Academy).where(Academy.slug == slug))
    if row is None:
        row = Academy(slug=slug)
        session.add(row)
    row.title = title
    row.summary = summary
    row.faculty = faculty
    row.position = position
    row.published = True
    session.flush()
    return row


def _path(session: Session, academy: Academy, spec: dict, position: int) -> LearningPath:
    row = session.scalar(select(LearningPath).where(LearningPath.slug == spec["slug"]))
    if row is None:
        row = LearningPath(slug=spec["slug"])
        session.add(row)
    row.title = spec["title"]
    row.description = spec["description"]
    row.level = spec["level"]
    row.academy_id = academy.id
    row.position = position
    row.gated = spec["gated"]
    row.xp_reward = 80
    session.flush()
    return row


def _course(
    session: Session, academy: Academy, path: LearningPath, spec: dict, position: int
) -> Course:
    row = session.scalar(select(Course).where(Course.slug == spec["slug"]))
    if row is None:
        row = Course(slug=spec["slug"])
        session.add(row)
    row.title = spec["title"]
    row.description = spec["description"]
    row.level = path.level
    row.published = True
    row.path_id = path.id
    row.academy_id = academy.id
    row.position = position
    row.pass_score = 70
    session.flush()
    return row


def _module(session: Session, course: Course, spec: dict, position: int) -> Module:
    row = session.scalar(select(Module).where(Module.slug == spec["slug"]))
    if row is None:
        row = Module(slug=spec["slug"], course_id=course.id, title=spec["title"])
        session.add(row)
    row.course_id = course.id
    row.title = spec["title"]
    row.summary = spec["summary"]
    row.position = position
    row.pass_score = 70
    session.flush()
    return row


def _lesson_row(session: Session, module: Module, spec: dict, position: int) -> Lesson:
    row = session.scalar(select(Lesson).where(Lesson.slug == spec["slug"]))
    if row is None:
        row = Lesson(slug=spec["slug"], module_id=module.id)
        session.add(row)
    row.module_id = module.id
    row.title = spec["title"]
    row.summary = spec["objectives"][0] if spec["objectives"] else ""
    row.objectives = list(spec["objectives"])
    row.position = position
    row.estimated_minutes = sum(page["minutes"] for page in spec["pages"])
    row.content_md = spec["pages"][0]["body"]
    session.flush()
    return row


def _ensure_asset(session: Session, spec: dict) -> KnowledgeAsset:
    """One catalog record per slug or URL. A lesson never stores a second copy of the file."""

    url = spec.get("url") or None
    row = session.scalar(select(KnowledgeAsset).where(KnowledgeAsset.slug == spec["slug"]))
    if row is None and url:
        row = session.scalar(select(KnowledgeAsset).where(KnowledgeAsset.url == url))
    if row is None:
        row = KnowledgeAsset(slug=spec["slug"][:80], title=spec["title"][:200])
        session.add(row)
    if row.slug.startswith("ref-") and row.slug != spec["slug"]:
        row.slug = spec["slug"][:80]
    owned = row.slug == spec["slug"]
    if owned:
        row.title = spec["title"][:200]
        row.description = spec["title"]
        row.url = url
        row.resource_type = spec["resource_type"]
        row.kind = "link" if url else "exercise"
        row.state = "published"
        row.topic = spec.get("topic") or ""
        row.tags = list(spec.get("tags") or [])
        row.source_type = "curated"
        row.extra = {**(row.extra or {}), "skills": list(spec.get("skills") or [])}
    session.flush()
    return row


def _state_resources(session: Session, lesson: Lesson) -> None:
    wanted = (
        {
            "slug": "sutton-barto-rl-book",
            "title": "Sutton and Barto, Reinforcement Learning: An Introduction",
            "url": "http://incompleteideas.net/book/RLbook2020.pdf",
            "resource_type": "paper",
            "group": "research",
            "tags": ["reinforcement-learning", "mdp"],
            "topic": "mdp",
            "skills": ["markov-decision-process"],
        },
        {
            "slug": "farama-gymnasium",
            "title": "Gymnasium, the maintained successor of OpenAI Gym",
            "url": "https://github.com/Farama-Foundation/Gymnasium",
            "resource_type": "repository",
            "group": "related",
            "tags": ["reinforcement-learning", "environment"],
            "topic": "mdp",
            "skills": ["environment-simulation"],
        },
        {
            "slug": "wikipedia-mdp",
            "title": "Markov decision process",
            "url": "https://en.wikipedia.org/wiki/Markov_decision_process",
            "resource_type": "documentation",
            "group": "further",
            "tags": ["mdp"],
            "topic": "mdp",
            "skills": ["markov-decision-process"],
        },
    )
    for position, spec in enumerate(wanted):
        asset = _ensure_asset(session, spec)
        link = session.scalar(
            select(LessonResource).where(
                LessonResource.lesson_id == lesson.id, LessonResource.asset_id == asset.id
            )
        )
        if link is None:
            link = LessonResource(lesson_id=lesson.id, asset_id=asset.id)
            session.add(link)
        link.group_name = spec["group"]
        link.position = position
