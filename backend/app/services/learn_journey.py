"""Read and write the guided learning journey. Answer keys stay in this module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.access import is_allowed
from app.domain.catalog import get_concept
from app.domain.gamification import card_tier, near_win
from app.domain.learn.faculties import FACULTIES, LEVELS, faculty_ref
from app.domain.learn.grading import grade_item, score_percent
from app.models import (
    Academy,
    Achievement,
    Assessment,
    AssessmentAttempt,
    AssessmentQuestion,
    Bookmark,
    Course,
    KnowledgeAsset,
    KnowledgeCheck,
    KnowledgeCheckAttempt,
    KnowledgeCheckQuestion,
    LearningPath,
    LearningPreference,
    Lesson,
    LessonResource,
    Module,
    PageNote,
    PageProgress,
    Progress,
    TopicPage,
    User,
    UserAchievement,
)
from app.services.errors import ClientError

_GROUPS = {
    "related": "Related resources",
    "further": "Further reading",
    "research": "Recommended research",
}


def _percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return round(100 * done / total)


class LearnJourney:
    def __init__(self, session: Session, engine=None) -> None:
        self.session = session
        self.engine = engine

    def academies(self, user: User) -> list[dict]:
        rows = list(
            self.session.scalars(
                select(Academy)
                .where(Academy.published.is_(True))
                .order_by(Academy.position, Academy.title)
            ).all()
        )
        prefs = self.session.get(LearningPreference, user.id)
        goal = None if prefs is None else prefs.career_goal
        if goal:
            rows.sort(key=lambda row: (0 if row.slug == goal else 1, row.position, row.title))
        cards = []
        for row in rows:
            card = self._academy_card(user, row)
            card["yours"] = goal == row.slug
            cards.append(card)
        return cards

    def world(self, user: User) -> dict:
        """Learning paths across faculties. Faculty and level are filters, not pages."""

        prefs = self.session.get(LearningPreference, user.id)
        goal = None if prefs is None else prefs.career_goal
        academies = list(
            self.session.scalars(
                select(Academy)
                .where(Academy.published.is_(True))
                .order_by(Academy.position, Academy.title)
            ).all()
        )
        faculty_order = {item["slug"]: index for index, item in enumerate(FACULTIES)}
        ranked: list[tuple[tuple, dict]] = []
        for academy in academies:
            paths = list(
                self.session.scalars(
                    select(LearningPath)
                    .where(LearningPath.academy_id == academy.id)
                    .order_by(LearningPath.position)
                ).all()
            )
            previous_open = True
            yours = goal == academy.slug
            for path in paths:
                progress = self._path_progress(user, path)
                locked = bool(path.gated and not previous_open)
                card = self._program_card(
                    user,
                    path,
                    academy=academy,
                    progress=progress,
                    locked=locked,
                    yours=yours,
                )
                ranked.append(
                    (
                        (
                            0 if yours else 1,
                            faculty_order.get(academy.faculty, 99),
                            academy.position,
                            path.position,
                        ),
                        card,
                    )
                )
                previous_open = progress >= 100
        ranked.sort(key=lambda pair: pair[0])
        return {
            "filters": {
                "faculties": [dict(item) for item in FACULTIES],
                "levels": [dict(item) for item in LEVELS],
                "academies": [
                    {
                        "slug": row.slug,
                        "title": row.title,
                        "summary": row.summary,
                        "faculty": row.faculty,
                        "yours": goal == row.slug,
                    }
                    for row in academies
                ],
            },
            "programs": [card for _, card in ranked],
        }

    def academy(self, user: User, slug: str) -> dict:
        row = self._academy(slug)
        paths = self.session.scalars(
            select(LearningPath)
            .where(LearningPath.academy_id == row.id)
            .order_by(LearningPath.position)
        ).all()
        previous_open = True
        listed = []
        for path in paths:
            progress = self._path_progress(user, path)
            locked = bool(path.gated and not previous_open)
            listed.append({**self._path_card(path), "progress": progress, "locked": locked})
            previous_open = progress >= 100
        card = self._academy_card(user, row)
        card["faculty"] = faculty_ref(row.faculty)
        card["paths"] = listed
        card["tree"] = self._skill_tree(user, row.id)
        return card

    def path(self, user: User, slug: str) -> dict:
        path = self._path(slug)
        self._require_open(user, path)
        courses = self.session.scalars(
            select(Course)
            .where(Course.path_id == path.id, Course.published.is_(True))
            .order_by(Course.position)
        ).all()
        return {
            **self._path_card(path),
            "academy": None if path.academy_id is None else self._academy_ref(path.academy_id),
            "progress": self._path_progress(user, path),
            "courses": [self._course_card(user, course) for course in courses],
            "assessment": self._assessment_ref(user, path_id=path.id),
            "next_path": self._next_path(user, path),
        }

    def course(self, user: User, slug: str) -> dict:
        course = self._course(slug)
        modules = self.session.scalars(
            select(Module).where(Module.course_id == course.id).order_by(Module.position)
        ).all()
        return {
            **self._course_card(user, course),
            "path": None if course.path_id is None else self._path_ref(course.path_id),
            "academy": None if course.academy_id is None else self._academy_ref(course.academy_id),
            "modules": [self._module_card(user, module) for module in modules],
            "assessment": self._assessment_ref(user, course_id=course.id),
        }

    def module(self, user: User, slug: str) -> dict:
        module = self._module(slug)
        lessons = self.session.scalars(
            select(Lesson).where(Lesson.module_id == module.id).order_by(Lesson.position)
        ).all()
        return {
            **self._module_card(user, module),
            "course": self._course_ref(module.course_id),
            "lessons": [self._lesson_card(user, lesson) for lesson in lessons],
            "assessment": self._assessment_ref(user, module_id=module.id),
        }

    def open_page(self, user: User, lesson_slug: str, page_slug: str) -> dict:
        lesson = self._lesson(lesson_slug)
        pages = self._pages(lesson.id)
        page = next((item for item in pages if item.slug == page_slug), None)
        if page is None:
            raise ClientError("That page was not found.", 404)
        self._touch_page(user, page, seconds=0, complete=False)
        return self._page_payload(user, lesson, pages, page)

    def complete_page(self, user: User, page_id: uuid.UUID, seconds: int) -> dict:
        page = self.session.get(TopicPage, page_id)
        if page is None:
            raise ClientError("That page was not found.", 404)
        if page.kind == "knowledge_check":
            check = self.session.scalar(
                select(KnowledgeCheck).where(KnowledgeCheck.page_id == page.id)
            )
            if check is not None and not self._check_passed(user, check.id):
                raise ClientError("Pass the knowledge check before leaving this page.", 409)
        self._touch_page(user, page, seconds=max(0, min(seconds, 60 * 60)), complete=True)
        lesson = self.session.get(Lesson, page.lesson_id)
        granted = 0
        if lesson is not None and self._lesson_done(user, lesson.id):
            granted = self._complete_lesson(user, lesson)
        return {"completed": True, "xp": granted, "continue": self.continue_for(user)}

    def toggle_bookmark(self, user: User, page_id: uuid.UUID) -> dict:
        page = self.session.get(TopicPage, page_id)
        if page is None:
            raise ClientError("That page was not found.", 404)
        row = self.session.scalar(
            select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.page_id == page.id)
        )
        if row is None:
            self.session.add(Bookmark(user_id=user.id, page_id=page.id))
            saved = True
        else:
            self.session.delete(row)
            saved = False
        self.session.flush()
        return {"bookmarked": saved}

    def save_note(self, user: User, page_id: uuid.UUID, body: str) -> dict:
        page = self.session.get(TopicPage, page_id)
        if page is None:
            raise ClientError("That page was not found.", 404)
        note = self.session.scalar(
            select(PageNote).where(PageNote.user_id == user.id, PageNote.page_id == page.id)
        )
        if note is None:
            note = PageNote(user_id=user.id, page_id=page.id)
            self.session.add(note)
        note.body = body[:4000]
        self.session.flush()
        return {"saved": True}

    def submit_check(self, user: User, check_id: uuid.UUID, answers: list[dict]) -> dict:
        check = self.session.get(KnowledgeCheck, check_id)
        if check is None:
            raise ClientError("That knowledge check was not found.", 404)
        questions = self.session.scalars(
            select(KnowledgeCheckQuestion)
            .where(KnowledgeCheckQuestion.check_id == check.id)
            .order_by(KnowledgeCheckQuestion.position)
        ).all()
        return self._grade(
            user,
            questions,
            answers,
            pass_score=check.pass_score,
            store=lambda score, passed, payload: self.session.add(
                KnowledgeCheckAttempt(
                    user_id=user.id,
                    check_id=check.id,
                    score=score,
                    passed=passed,
                    answers=payload,
                )
            ),
            xp_source=("knowledge_check", str(check.id), None)
            if not self._check_passed(user, check.id)
            else None,
        )

    def assessment(self, user: User, assessment_id: uuid.UUID) -> dict:
        row = self._assessment(assessment_id)
        questions = self._assessment_questions(row.id)
        attempt = self._best_attempt(user, row.id)
        return {
            "id": row.id,
            "title": row.title,
            "scope": row.scope,
            "pass_score": row.pass_score,
            "xp_reward": row.xp_reward,
            "passed": bool(attempt and attempt.passed),
            "best_score": None if attempt is None else attempt.score,
            "questions": [self._public_question(item) for item in questions],
        }

    def submit_assessment(self, user: User, assessment_id: uuid.UUID, answers: list[dict]) -> dict:
        row = self._assessment(assessment_id)
        questions = self._assessment_questions(row.id)
        already = self._best_attempt(user, row.id)
        result = self._grade(
            user,
            questions,
            answers,
            pass_score=row.pass_score,
            store=lambda score, passed, payload: self.session.add(
                AssessmentAttempt(
                    user_id=user.id,
                    assessment_id=row.id,
                    score=score,
                    passed=passed,
                    answers=payload,
                    xp_awarded=0,
                )
            ),
            xp_source=None,
        )
        if result["passed"] and (already is None or not already.passed) and self.engine is not None:
            awarded = self.engine.grant(user, "assessment", str(row.id), row.xp_reward)
            result["xp"] = awarded
            if row.scope == "path" and row.path_id is not None:
                path = self.session.get(LearningPath, row.path_id)
                if path is not None:
                    result["xp"] += self.engine.grant(user, "path", str(path.id), path.xp_reward)
                    self._award_path_badge(user, path)
        return result

    def continue_for(self, user: User) -> dict | None:
        seen = self.session.scalar(
            select(PageProgress)
            .where(PageProgress.user_id == user.id, PageProgress.status != "completed")
            .order_by(PageProgress.updated_at.desc())
        )
        page = None if seen is None else self.session.get(TopicPage, seen.page_id)
        if page is None:
            preferred = self.session.scalar(select(Lesson).where(Lesson.slug == "what-is-a-state"))
            if preferred is not None:
                page = self.session.scalar(
                    select(TopicPage)
                    .where(TopicPage.lesson_id == preferred.id)
                    .order_by(TopicPage.position)
                )
            if page is None:
                page = self.session.scalar(select(TopicPage).order_by(TopicPage.position).limit(1))
        if page is None:
            return None
        lesson = self.session.get(Lesson, page.lesson_id)
        if lesson is None:
            return None
        return {
            "lesson": lesson.slug,
            "page": page.slug,
            "title": page.title,
            "lesson_title": lesson.title,
            "href": f"/learn/{lesson.slug}/{page.slug}",
        }

    def metrics(self, actor: User) -> dict:
        if not is_allowed(actor.role, "admin"):
            raise ClientError("Admin role required.", 403)
        completed = (
            select(PageProgress.page_id, func.count().label("n"))
            .where(PageProgress.status == "completed")
            .group_by(PageProgress.page_id)
            .subquery()
        )
        lesson_done = self.session.execute(
            select(Lesson.title, func.count(Progress.id))
            .join(Progress, Progress.lesson_id == Lesson.id)
            .group_by(Lesson.title)
            .order_by(func.count(Progress.id).desc())
            .limit(8)
        ).all()
        dropoff = self.session.execute(
            select(
                TopicPage.title,
                Lesson.title,
                func.coalesce(completed.c.n, 0),
                func.count(PageProgress.id),
            )
            .join(Lesson, Lesson.id == TopicPage.lesson_id)
            .outerjoin(PageProgress, PageProgress.page_id == TopicPage.id)
            .outerjoin(completed, completed.c.page_id == TopicPage.id)
            .group_by(TopicPage.id, TopicPage.title, Lesson.title, completed.c.n)
            .limit(200)
        ).all()
        ranked = []
        for page_title, lesson_title, done, seen in dropoff:
            seen_n = int(seen or 0)
            done_n = int(done or 0)
            if seen_n == 0:
                continue
            ranked.append(
                {
                    "page": page_title,
                    "lesson": lesson_title,
                    "seen": seen_n,
                    "completed": done_n,
                    "drop_off": round(100 * (seen_n - done_n) / seen_n),
                }
            )
        ranked.sort(key=lambda item: item["drop_off"], reverse=True)
        attempt_rows = self.session.execute(
            select(Assessment.title, Assessment.scope, AssessmentAttempt.passed).join(
                AssessmentAttempt, AssessmentAttempt.assessment_id == Assessment.id
            )
        ).all()
        buckets: dict[tuple[str, str], list[bool]] = {}
        for title, scope, passed in attempt_rows:
            buckets.setdefault((title, scope), []).append(bool(passed))
        assessments = [
            {
                "title": title,
                "scope": scope,
                "attempts": len(flags),
                "pass_rate": _percent(sum(flags), len(flags)),
            }
            for (title, scope), flags in buckets.items()
        ]
        return {
            "most_completed_lessons": [
                {"title": title, "completions": count} for title, count in lesson_done
            ],
            "highest_drop_off_pages": ranked[:8],
            "assessment_pass_rates": assessments,
            "course_completion": self._scope_rates("course"),
            "path_completion": self._scope_rates("path"),
            "time_on_lesson": self._time_on_lesson(),
        }

    def outline(self) -> list[dict]:
        academies = self.session.scalars(select(Academy).order_by(Academy.position)).all()
        tree = []
        for academy in academies:
            paths = self.session.scalars(
                select(LearningPath)
                .where(LearningPath.academy_id == academy.id)
                .order_by(LearningPath.position)
            ).all()
            tree.append(
                {
                    "slug": academy.slug,
                    "title": academy.title,
                    "paths": [
                        {
                            "slug": path.slug,
                            "title": path.title,
                            "courses": [
                                {"slug": course.slug, "title": course.title}
                                for course in self.session.scalars(
                                    select(Course)
                                    .where(Course.path_id == path.id)
                                    .order_by(Course.position)
                                ).all()
                            ],
                        }
                        for path in paths
                    ],
                }
            )
        return tree

    def add_page(
        self, lesson_slug: str, title: str, body_md: str, kind: str, asset_url: str = ""
    ) -> dict:
        lesson = self._lesson(lesson_slug)
        if kind not in {"reading", "video", "exercise", "knowledge_check", "summary"}:
            raise ClientError("Unknown topic page kind.", 422)
        last = self.session.scalar(
            select(func.max(TopicPage.position)).where(TopicPage.lesson_id == lesson.id)
        )
        slug = _slug(title)
        if self.session.scalar(
            select(TopicPage).where(TopicPage.lesson_id == lesson.id, TopicPage.slug == slug)
        ):
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
        page = TopicPage(
            lesson_id=lesson.id,
            slug=slug,
            title=title,
            body_md=body_md,
            kind=kind,
            position=0 if last is None else int(last) + 1,
            origin="authored",
        )
        if asset_url:
            resource_type = "coding_challenge" if kind == "exercise" else "video"
            page.asset_id = self._catalog_for_url(asset_url, title, resource_type).id
        self.session.add(page)
        self.session.flush()
        if kind == "knowledge_check":
            self.session.add(KnowledgeCheck(page_id=page.id, title=title))
        return {"id": str(page.id), "slug": page.slug, "lesson": lesson.slug}

    def reorder_pages(self, lesson_slug: str, page_ids: list[uuid.UUID]) -> dict:
        lesson = self._lesson(lesson_slug)
        pages = {page.id: page for page in self._pages(lesson.id)}
        if set(pages) != set(page_ids):
            raise ClientError("Reorder must include every page of the lesson once.", 422)
        for position, page_id in enumerate(page_ids):
            pages[page_id].position = position
        self.session.flush()
        return {"reordered": True}

    def add_resource(
        self,
        lesson_slug: str,
        group_name: str,
        *,
        asset_id: uuid.UUID | None = None,
        url: str = "",
        title: str = "",
        resource_type: str = "documentation",
    ) -> dict:
        """Attach a catalog record to a lesson. A pasted URL becomes a catalog record first."""

        lesson = self._lesson(lesson_slug)
        if asset_id is not None:
            asset = self.session.get(KnowledgeAsset, asset_id)
            if asset is None:
                raise ClientError("That catalog resource does not exist.", 422)
        elif url.startswith(("http://", "https://")):
            asset = self._catalog_for_url(url, title or url, resource_type)
        else:
            raise ClientError("Attach a catalog resource, or an http(s) URL to add one.", 422)
        row = LessonResource(lesson_id=lesson.id, asset_id=asset.id, group_name=group_name)
        self.session.add(row)
        self.session.flush()
        return {"id": str(row.id), "asset_id": str(asset.id)}

    def _catalog_for_url(self, url: str, title: str, resource_type: str) -> KnowledgeAsset:
        asset = self.session.scalar(select(KnowledgeAsset).where(KnowledgeAsset.url == url))
        if asset is not None:
            return asset
        asset = KnowledgeAsset(
            slug=f"ref-{uuid.uuid4().hex[:16]}",
            title=title[:200],
            description=title,
            url=url,
            resource_type=resource_type,
            kind="link",
            state="published",
            source_type="curated",
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def _grade(self, user, questions, answers, *, pass_score, store, xp_source) -> dict:
        if not questions:
            raise ClientError("This check has no questions yet.", 422)
        given = {str(item["question_id"]): item.get("response") for item in answers}
        results = []
        correct = 0
        for question in questions:
            response = given.get(str(question.id))
            ok = grade_item(question.kind, question.answer_key or {}, response)
            correct += int(ok)
            results.append(
                {
                    "question_id": question.id,
                    "correct": ok,
                    "explanation": question.explanation,
                }
            )
        score = score_percent(correct, len(questions))
        passed = score >= pass_score
        store(score, passed, {"answers": given})
        self.session.flush()
        xp = 0
        if passed and xp_source is not None and self.engine is not None:
            source, source_id, computed = xp_source
            xp = self.engine.grant(user, source, source_id, computed)
        return {
            "score": score,
            "passed": passed,
            "pass_score": pass_score,
            "results": results,
            "xp": xp,
        }

    def _page_payload(
        self, user: User, lesson: Lesson, pages: list[TopicPage], page: TopicPage
    ) -> dict:
        module = self.session.get(Module, lesson.module_id)
        course = None if module is None else self.session.get(Course, module.course_id)
        path = (
            None
            if course is None or course.path_id is None
            else self.session.get(LearningPath, course.path_id)
        )
        academy = None
        if path is not None and path.academy_id is not None:
            academy = self.session.get(Academy, path.academy_id)
        completed = self._completed_page_ids(user, [item.id for item in pages])
        index = pages.index(page)
        resources = self.session.scalars(
            select(LessonResource)
            .where(LessonResource.lesson_id == lesson.id)
            .order_by(LessonResource.position)
        ).all()
        grouped: dict[str, list[dict]] = {key: [] for key in _GROUPS}
        for resource in resources:
            view = self._resource_view(resource)
            if view is not None:
                grouped.setdefault(resource.group_name, []).append(view)
        note = self.session.scalar(
            select(PageNote).where(PageNote.user_id == user.id, PageNote.page_id == page.id)
        )
        bookmarked = (
            self.session.scalar(
                select(Bookmark.id).where(Bookmark.user_id == user.id, Bookmark.page_id == page.id)
            )
            is not None
        )
        check = None
        if page.kind == "knowledge_check":
            row = self.session.scalar(
                select(KnowledgeCheck).where(KnowledgeCheck.page_id == page.id)
            )
            if row is not None:
                questions = self.session.scalars(
                    select(KnowledgeCheckQuestion)
                    .where(KnowledgeCheckQuestion.check_id == row.id)
                    .order_by(KnowledgeCheckQuestion.position)
                ).all()
                check = {
                    "id": row.id,
                    "title": row.title,
                    "pass_score": row.pass_score,
                    "passed": self._check_passed(user, row.id),
                    "questions": [self._public_question(item) for item in questions],
                }
        siblings = self.session.scalars(
            select(Lesson).where(Lesson.module_id == lesson.module_id).order_by(Lesson.position)
        ).all()
        return {
            "breadcrumbs": [
                item
                for item in (
                    None
                    if academy is None
                    else {"label": academy.title, "href": f"/academies/{academy.slug}"},
                    None if path is None else {"label": path.title, "href": f"/paths/{path.slug}"},
                    None
                    if course is None
                    else {"label": course.title, "href": f"/courses/{course.slug}"},
                    None
                    if module is None
                    else {"label": module.title, "href": f"/modules/{module.slug}"},
                    {"label": lesson.title, "href": f"/learn/{lesson.slug}/{pages[0].slug}"},
                    {"label": page.title, "href": None},
                )
                if item is not None
            ],
            "objectives": list(lesson.objectives or []),
            "resources": [
                {"heading": label, "items": grouped[key]}
                for key, label in _GROUPS.items()
                if grouped[key]
            ],
            "outline": {
                "module": None if module is None else module.title,
                "lessons": [
                    {
                        "slug": item.slug,
                        "title": item.title,
                        "current": item.id == lesson.id,
                        "progress": self._lesson_percent(user, item.id),
                    }
                    for item in siblings
                ],
                "pages": [
                    {
                        "slug": item.slug,
                        "title": item.title,
                        "current": item.id == page.id,
                        "completed": item.id in completed,
                    }
                    for item in pages
                ],
            },
            "page": {
                "id": page.id,
                "slug": page.slug,
                "title": page.title,
                "kind": page.kind,
                "body_md": page.body_md,
                "estimated_minutes": page.estimated_minutes,
                "index": index + 1,
                "total": len(pages),
                "bookmarked": bookmarked,
                "note": "" if note is None else note.body,
                "check": check,
                "asset": self._asset_view(page.asset_id),
            },
            "progress": {
                "lesson": self._lesson_percent(user, lesson.id),
                "module": 0 if module is None else self._module_percent(user, module.id),
                "course": 0 if course is None else self._course_percent(user, course.id),
                "path": 0 if path is None else self._path_progress(user, path),
            },
            "previous": None
            if index == 0
            else {"lesson": lesson.slug, "page": pages[index - 1].slug},
            "next": None
            if index + 1 >= len(pages)
            else {"lesson": lesson.slug, "page": pages[index + 1].slug},
            "lesson": {"slug": lesson.slug, "title": lesson.title},
        }

    def _resource_view(self, link: LessonResource) -> dict | None:
        return self._asset_view(link.asset_id)

    def _asset_view(self, asset_id: uuid.UUID | None) -> dict | None:
        if asset_id is None:
            return None
        asset = self.session.get(KnowledgeAsset, asset_id)
        if asset is None:
            return None
        extra = asset.extra or {}
        return {
            "asset_id": asset.id,
            "title": asset.title,
            "url": asset.url or "",
            "kind": asset.resource_type,
            "tags": list(asset.tags or []),
            "topic": asset.topic,
            "skills": list(extra.get("skills") or []),
        }

    def _touch_page(self, user: User, page: TopicPage, *, seconds: int, complete: bool) -> None:
        row = self.session.scalar(
            select(PageProgress).where(
                PageProgress.user_id == user.id, PageProgress.page_id == page.id
            )
        )
        if row is None:
            row = PageProgress(user_id=user.id, page_id=page.id, status="seen")
            self.session.add(row)
        row.seconds_spent = (row.seconds_spent or 0) + seconds
        if complete:
            row.status = "completed"
            row.completed_at = row.completed_at or datetime.now(UTC)
        self.session.flush()

    def _complete_lesson(self, user: User, lesson: Lesson) -> int:
        existing = self.session.scalar(
            select(Progress).where(Progress.user_id == user.id, Progress.lesson_id == lesson.id)
        )
        if existing is not None or self.engine is None:
            return 0
        self.session.add(
            Progress(
                user_id=user.id,
                lesson_id=lesson.id,
                status="completed",
                completed_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return self.engine.grant(user, "lesson", str(lesson.id))

    def _award_path_badge(self, user: User, path: LearningPath) -> None:
        achievement = self.session.scalar(select(Achievement).where(Achievement.slug == path.slug))
        if achievement is None:
            return
        exists = self.session.scalar(
            select(UserAchievement).where(
                UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id
            )
        )
        if exists is None:
            self.session.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))

    def _academy_card(self, user: User, row: Academy) -> dict:
        paths = self.session.scalars(
            select(LearningPath).where(LearningPath.academy_id == row.id)
        ).all()
        progress = (
            0
            if not paths
            else round(sum(self._path_progress(user, path) for path in paths) / len(paths))
        )
        lessons = self._academy_lessons(row.id)
        done = set(self._completed_lesson_ids(user.id))
        remaining = sum(1 for lesson in lessons if lesson.id not in done)
        next_unlock = None
        for path in paths:
            if self._path_progress(user, path) < 100:
                next_unlock = path.title
                break
        return {
            "slug": row.slug,
            "title": row.title,
            "summary": row.summary,
            "faculty": row.faculty,
            "paths": len(paths),
            "progress": progress,
            "remaining_lessons": remaining,
            "cue": near_win(
                remaining_lessons=remaining if progress > 0 else None,
                next_unlock=next_unlock if progress > 0 else None,
                percent=progress,
            ),
        }

    def _program_card(
        self,
        user: User,
        path: LearningPath,
        *,
        academy: Academy,
        progress: int,
        locked: bool,
        yours: bool,
    ) -> dict:
        lessons = self._path_lessons(path.id)
        done = set(self._completed_lesson_ids(user.id))
        remaining = sum(1 for lesson in lessons if lesson.id not in done)
        courses = len(
            self.session.scalars(select(Course.id).where(Course.path_id == path.id)).all()
        )
        return {
            **self._path_card(path),
            "faculty": faculty_ref(academy.faculty),
            "academy": {"slug": academy.slug, "title": academy.title, "faculty": academy.faculty},
            "progress": progress,
            "locked": locked,
            "yours": yours,
            "courses": int(courses),
            "remaining_lessons": remaining,
            "href": None if locked else f"/paths/{path.slug}",
            "cue": near_win(
                remaining_lessons=remaining if progress > 0 else None,
                next_unlock=None if locked or progress >= 100 else path.title,
                percent=progress,
            ),
        }

    def _path_lessons(self, path_id: uuid.UUID) -> list[Lesson]:
        return list(
            self.session.scalars(
                select(Lesson)
                .join(Module, Lesson.module_id == Module.id)
                .join(Course, Module.course_id == Course.id)
                .where(Course.path_id == path_id)
                .order_by(Course.position, Module.position, Lesson.position)
            ).all()
        )

    def _academy_lessons(self, academy_id: uuid.UUID) -> list[Lesson]:
        return list(
            self.session.scalars(
                select(Lesson)
                .join(Module, Lesson.module_id == Module.id)
                .join(Course, Module.course_id == Course.id)
                .join(LearningPath, Course.path_id == LearningPath.id)
                .where(LearningPath.academy_id == academy_id)
                .order_by(LearningPath.position, Course.position, Module.position, Lesson.position)
            ).all()
        )

    def _completed_lesson_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        return list(
            self.session.scalars(
                select(Progress.lesson_id).where(
                    Progress.user_id == user_id, Progress.status == "completed"
                )
            ).all()
        )

    def _skill_tree(self, user: User, academy_id: uuid.UUID) -> list[dict]:
        from app.models import ConceptMastery

        lessons = self._academy_lessons(academy_id)
        done = set(self._completed_lesson_ids(user.id))
        scores = {
            row.concept_slug: row.score
            for row in self.session.scalars(
                select(ConceptMastery).where(ConceptMastery.user_id == user.id)
            ).all()
        }
        tree = []
        for lesson in lessons:
            catalog = get_concept(lesson.slug)
            score = scores.get(lesson.slug, 0)
            unlocked = lesson.id in done or score >= 60
            tree.append(
                {
                    "slug": lesson.slug,
                    "name": lesson.title,
                    "unlocked": unlocked,
                    "mastery": score,
                    "tier": card_tier(score),
                    "prerequisites": [] if catalog is None else list(catalog.prerequisites),
                }
            )
        return tree

    def _path_card(self, path: LearningPath) -> dict:
        return {
            "slug": path.slug,
            "title": path.title,
            "description": path.description,
            "level": path.level,
            "gated": path.gated,
            "xp_reward": path.xp_reward,
        }

    def _course_card(self, user: User, course: Course) -> dict:
        return {
            "slug": course.slug,
            "title": course.title,
            "description": course.description,
            "level": course.level,
            "progress": self._course_percent(user, course.id),
            "pass_score": course.pass_score,
        }

    def _module_card(self, user: User, module: Module) -> dict:
        return {
            "slug": module.slug,
            "title": module.title,
            "summary": module.summary,
            "progress": self._module_percent(user, module.id),
            "pass_score": module.pass_score,
        }

    def _lesson_card(self, user: User, lesson: Lesson) -> dict:
        first = self.session.scalar(
            select(TopicPage).where(TopicPage.lesson_id == lesson.id).order_by(TopicPage.position)
        )
        return {
            "slug": lesson.slug,
            "title": lesson.title,
            "summary": lesson.summary,
            "estimated_minutes": lesson.estimated_minutes,
            "progress": self._lesson_percent(user, lesson.id),
            "href": None if first is None else f"/learn/{lesson.slug}/{first.slug}",
        }

    def _path_progress(self, user: User, path: LearningPath) -> int:
        courses = self.session.scalars(select(Course.id).where(Course.path_id == path.id)).all()
        if not courses:
            return 0
        return round(
            sum(self._course_percent(user, course_id) for course_id in courses) / len(courses)
        )

    def _course_percent(self, user: User, course_id: uuid.UUID) -> int:
        modules = self.session.scalars(select(Module.id).where(Module.course_id == course_id)).all()
        if not modules:
            return 0
        return round(
            sum(self._module_percent(user, module_id) for module_id in modules) / len(modules)
        )

    def _module_percent(self, user: User, module_id: uuid.UUID) -> int:
        lessons = self.session.scalars(select(Lesson.id).where(Lesson.module_id == module_id)).all()
        if not lessons:
            return 0
        return round(
            sum(self._lesson_percent(user, lesson_id) for lesson_id in lessons) / len(lessons)
        )

    def _lesson_percent(self, user: User, lesson_id: uuid.UUID) -> int:
        pages = self.session.scalars(
            select(TopicPage.id).where(TopicPage.lesson_id == lesson_id)
        ).all()
        if not pages:
            return 0
        done = self._completed_page_ids(user, list(pages))
        return _percent(len(done), len(pages))

    def _lesson_done(self, user: User, lesson_id: uuid.UUID) -> bool:
        return self._lesson_percent(user, lesson_id) == 100

    def _completed_page_ids(self, user: User, page_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not page_ids:
            return set()
        rows = self.session.scalars(
            select(PageProgress.page_id).where(
                PageProgress.user_id == user.id,
                PageProgress.page_id.in_(page_ids),
                PageProgress.status == "completed",
            )
        ).all()
        return set(rows)

    def _check_passed(self, user: User, check_id: uuid.UUID) -> bool:
        row = self.session.scalar(
            select(KnowledgeCheckAttempt.id).where(
                KnowledgeCheckAttempt.user_id == user.id,
                KnowledgeCheckAttempt.check_id == check_id,
                KnowledgeCheckAttempt.passed.is_(True),
            )
        )
        return row is not None

    def _best_attempt(self, user: User, assessment_id: uuid.UUID) -> AssessmentAttempt | None:
        return self.session.scalar(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user.id,
                AssessmentAttempt.assessment_id == assessment_id,
            )
            .order_by(AssessmentAttempt.passed.desc(), AssessmentAttempt.score.desc())
        )

    def _assessment_ref(self, user: User, **parent) -> dict | None:
        row = self.session.scalar(
            select(Assessment).where(
                *[getattr(Assessment, key) == value for key, value in parent.items()]
            )
        )
        if row is None:
            return None
        attempt = self._best_attempt(user, row.id)
        return {
            "id": row.id,
            "title": row.title,
            "scope": row.scope,
            "pass_score": row.pass_score,
            "passed": bool(attempt and attempt.passed),
            "best_score": None if attempt is None else attempt.score,
        }

    def _require_open(self, user: User, path: LearningPath) -> None:
        if not path.gated or path.academy_id is None:
            return
        earlier = self.session.scalars(
            select(LearningPath)
            .where(
                LearningPath.academy_id == path.academy_id, LearningPath.position < path.position
            )
            .order_by(LearningPath.position)
        ).all()
        for item in earlier:
            if self._path_progress(user, item) < 100:
                raise ClientError(f"Finish {item.title} before opening this path.", 409)

    def _next_path(self, user: User, path: LearningPath) -> dict | None:
        if path.academy_id is None:
            return None
        nxt = self.session.scalar(
            select(LearningPath)
            .where(
                LearningPath.academy_id == path.academy_id, LearningPath.position > path.position
            )
            .order_by(LearningPath.position)
        )
        if nxt is None:
            return None
        return {
            "slug": nxt.slug,
            "title": nxt.title,
            "locked": self._path_progress(user, path) < 100,
        }

    def _scope_rates(self, scope: str) -> list[dict]:
        rows = self.session.scalars(select(Assessment).where(Assessment.scope == scope)).all()
        listed = []
        for row in rows:
            flags = self.session.scalars(
                select(AssessmentAttempt.passed).where(AssessmentAttempt.assessment_id == row.id)
            ).all()
            listed.append(
                {
                    "title": row.title,
                    "attempts": len(flags),
                    "pass_rate": _percent(sum(bool(flag) for flag in flags), len(flags)),
                }
            )
        return listed

    def _time_on_lesson(self) -> list[dict]:
        rows = self.session.execute(
            select(Lesson.title, func.coalesce(func.sum(PageProgress.seconds_spent), 0))
            .join(TopicPage, TopicPage.lesson_id == Lesson.id)
            .outerjoin(PageProgress, PageProgress.page_id == TopicPage.id)
            .group_by(Lesson.id, Lesson.title)
            .order_by(func.coalesce(func.sum(PageProgress.seconds_spent), 0).desc())
            .limit(8)
        ).all()
        return [{"title": title, "minutes": round(int(seconds) / 60, 1)} for title, seconds in rows]

    def _public_question(self, question) -> dict:
        return {
            "id": question.id,
            "kind": question.kind,
            "prompt": question.prompt,
            "options": list(question.options or []),
        }

    def _pages(self, lesson_id: uuid.UUID) -> list[TopicPage]:
        return list(
            self.session.scalars(
                select(TopicPage)
                .where(TopicPage.lesson_id == lesson_id)
                .order_by(TopicPage.position)
            ).all()
        )

    def _assessment_questions(self, assessment_id: uuid.UUID) -> list[AssessmentQuestion]:
        return list(
            self.session.scalars(
                select(AssessmentQuestion)
                .where(AssessmentQuestion.assessment_id == assessment_id)
                .order_by(AssessmentQuestion.position)
            ).all()
        )

    def _academy(self, slug: str) -> Academy:
        row = self.session.scalar(select(Academy).where(Academy.slug == slug))
        if row is None:
            raise ClientError("That academy was not found.", 404)
        return row

    def _path(self, slug: str) -> LearningPath:
        row = self.session.scalar(select(LearningPath).where(LearningPath.slug == slug))
        if row is None:
            raise ClientError("That learning path was not found.", 404)
        return row

    def _course(self, slug: str) -> Course:
        row = self.session.scalar(select(Course).where(Course.slug == slug))
        if row is None:
            raise ClientError("That course was not found.", 404)
        return row

    def _module(self, slug: str) -> Module:
        row = self.session.scalar(select(Module).where(Module.slug == slug))
        if row is None:
            raise ClientError("That module was not found.", 404)
        return row

    def _lesson(self, slug: str) -> Lesson:
        row = self.session.scalar(select(Lesson).where(Lesson.slug == slug))
        if row is None:
            raise ClientError("That lesson was not found.", 404)
        return row

    def _assessment(self, assessment_id: uuid.UUID) -> Assessment:
        row = self.session.get(Assessment, assessment_id)
        if row is None:
            raise ClientError("That assessment was not found.", 404)
        return row

    def _academy_ref(self, academy_id: uuid.UUID) -> dict | None:
        row = self.session.get(Academy, academy_id)
        if row is None:
            return None
        return {"slug": row.slug, "title": row.title, "faculty": row.faculty}

    def _path_ref(self, path_id: uuid.UUID) -> dict | None:
        row = self.session.get(LearningPath, path_id)
        if row is None:
            return None
        return {"slug": row.slug, "title": row.title}

    def _course_ref(self, course_id: uuid.UUID) -> dict | None:
        row = self.session.get(Course, course_id)
        if row is None:
            return None
        return {"slug": row.slug, "title": row.title}


def _slug(title: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in title)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:80] or "page"
