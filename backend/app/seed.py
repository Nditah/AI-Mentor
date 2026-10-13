"""Idempotent catalog seed. Restarts refresh lesson text and do not reset learner progress."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.catalog import ACHIEVEMENTS, CONCEPTS, PATHS, PROJECTS, Concept
from app.models import (
    Achievement,
    ConceptRelation,
    Course,
    LearningPath,
    LearningPathItem,
    Lesson,
    Module,
    Project,
    User,
)
from app.models import (
    Concept as ConceptRow,
)

_MINUTES = {"beginner": 20, "intermediate": 30, "advanced": 40, "expert": 45, "phd": 50}
_DEMOS = (
    ("demo-student", "student@mentor.local", "Demo Student", "student"),
    ("demo-instructor", "instructor@mentor.local", "Demo Instructor", "instructor"),
    ("demo-admin", "admin@mentor.local", "Demo Admin", "admin"),
)


def lesson_markdown(concept: Concept) -> str:
    return f"# {concept.name}\n\n{concept.explanation}\n\n## Exercise\n\n{concept.exercise}\n"


def seed_catalog(session: Session) -> None:
    concepts: dict[str, ConceptRow] = {}
    for concept in CONCEPTS:
        row = session.scalar(select(ConceptRow).where(ConceptRow.slug == concept.slug))
        if row is None:
            row = ConceptRow(slug=concept.slug)
            session.add(row)
        row.name = concept.name
        row.domain = concept.domain
        row.difficulty = concept.difficulty
        row.summary = concept.scaffold
        concepts[concept.slug] = row
    session.flush()

    for concept in CONCEPTS:
        source = concepts[concept.slug]
        for prerequisite in concept.prerequisites:
            target = concepts[prerequisite]
            exists = session.scalar(
                select(ConceptRelation).where(
                    ConceptRelation.source_id == source.id,
                    ConceptRelation.target_id == target.id,
                    ConceptRelation.relation_type == "prerequisite",
                )
            )
            if exists is None:
                session.add(
                    ConceptRelation(
                        source_id=source.id,
                        target_id=target.id,
                        relation_type="prerequisite",
                    )
                )
    session.flush()

    lessons: dict[str, Lesson] = {}
    for path in PATHS:
        course = session.scalar(select(Course).where(Course.slug == path.slug))
        if course is None:
            course = Course(slug=path.slug)
            session.add(course)
        course.title = path.title
        course.description = path.description
        course.level = path.level
        course.published = True
        session.flush()
        module = session.scalar(
            select(Module).where(Module.course_id == course.id, Module.title == "Core")
        )
        if module is None:
            module = Module(course_id=course.id, title="Core", position=0)
            session.add(module)
            session.flush()
        learning_path = session.scalar(select(LearningPath).where(LearningPath.slug == path.slug))
        if learning_path is None:
            learning_path = LearningPath(slug=path.slug)
            session.add(learning_path)
        learning_path.title = path.title
        learning_path.description = path.description
        learning_path.level = path.level
        session.flush()
        for position, slug in enumerate(path.concepts):
            concept = next(item for item in CONCEPTS if item.slug == slug)
            lesson = session.scalar(select(Lesson).where(Lesson.slug == slug))
            if lesson is None:
                lesson = Lesson(slug=slug, module_id=module.id)
                session.add(lesson)
            lesson.module_id = module.id
            lesson.concept_id = concepts[slug].id
            lesson.title = concept.name
            lesson.content_md = lesson_markdown(concept)
            lesson.position = position
            lesson.estimated_minutes = _MINUTES.get(concept.difficulty, 30)
            lessons[slug] = lesson
            session.flush()
            item = session.scalar(
                select(LearningPathItem).where(
                    LearningPathItem.path_id == learning_path.id,
                    LearningPathItem.position == position,
                )
            )
            if item is None:
                item = LearningPathItem(path_id=learning_path.id, position=position)
                session.add(item)
            item.concept_id = concepts[slug].id
            item.lesson_id = lesson.id

    for achievement in ACHIEVEMENTS:
        row = session.scalar(select(Achievement).where(Achievement.slug == achievement.slug))
        if row is None:
            row = Achievement(slug=achievement.slug)
            session.add(row)
        row.name = achievement.name
        row.description = achievement.description
        row.xp_reward = achievement.xp_reward
        row.icon = achievement.icon

    for project in PROJECTS:
        row = session.scalar(select(Project).where(Project.slug == project.slug))
        if row is None:
            row = Project(slug=project.slug)
            session.add(row)
        row.title = project.title
        row.brief_md = project.brief
        row.language = project.language
        row.difficulty = project.difficulty
        row.starter_code = project.starter
        row.concept_slug = project.concept

    for clerk_id, email, name, role in _DEMOS:
        if session.scalar(select(User).where(User.clerk_id == clerk_id)) is None:
            session.add(User(clerk_id=clerk_id, email=email, display_name=name, role=role))
    session.flush()


def main() -> None:
    from app.core.database import session_scope

    with session_scope() as session:
        seed_catalog(session)


if __name__ == "__main__":
    main()
