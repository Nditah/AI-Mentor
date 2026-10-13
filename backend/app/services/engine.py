"""Application service. Domain rules decide; this module stores the result."""

from __future__ import annotations

import hashlib
import io
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents import CareerAgent, CodingAgent, PlannerAgent, QuizAgent, ResearchAgent, TutorAgent
from app.agents.orchestrator import dispatch
from app.core.config import Settings
from app.domain.career import match_roles
from app.domain.catalog import QUESTIONS, get_concept
from app.domain.chunking import chunk_text
from app.domain.code_review import review_notes
from app.domain.gamification import (
    BadgeContext,
    evaluate_badges,
    grant_for,
    learner_day,
    level_progress,
    next_streak,
    quiz_xp,
    requested_xp,
)
from app.domain.grading import grade_coding, grade_mcq, grade_research, grade_short
from app.domain.graph import mermaid, recommend
from app.domain.grounding import extract_equations
from app.domain.mastery import Evidence, band, score_evidence
from app.domain.planner import build_study_plan
from app.domain.prompt_guard import screen_user_input
from app.domain.scheduling import ScheduleState, SM2Scheduler
from app.domain.socratic import HistoryTurn, build_turn
from app.models import (
    CodeSubmission,
    Conversation,
    DocumentChunk,
    Flashcard,
    Question,
    Quiz,
    QuizResult,
    ResearchDocument,
    Review,
    StudyPlan,
    StudyPlanItem,
    User,
)
from app.repositories.sql import SqlRepository
from app.services.errors import ClientError
from app.services.llm import ProviderRouter
from app.services.retrieval import (
    IndexUnavailable,
    index_document,
    library_citations,
    search_document,
)
from app.services.sandbox_runner import run_student_code

log = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
LAB_OFF = (
    "The code lab is switched off until learner code runs in an isolated runner "
    "with no secrets and no network."
)


class MentorEngine:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repo = SqlRepository(session)
        provider = ProviderRouter(settings)
        self.tutor = TutorAgent(provider)
        self.quiz_agent = QuizAgent(provider)
        self.research_agent = ResearchAgent(provider)
        self.coding_agent = CodingAgent(provider)
        self.planner_agent = PlannerAgent(provider)
        self.career_agent = CareerAgent(provider)

    def chat(self, user: User, message: str, conversation_id: uuid.UUID | None, mode: str) -> dict:
        screened = self._screen(message)
        if conversation_id is None:
            conversation = Conversation(user_id=user.id, title=screened[:80], mode=mode)
            self.session.add(conversation)
            self.session.flush()
        else:
            conversation = self.repo.conversation(conversation_id, user.id)
            if conversation is None:
                raise ClientError("Conversation not found.", 404)
        prior = list(conversation.messages)[-20:]
        history = [HistoryTurn(item.role, item.content) for item in prior]
        sticky = next((item.concept_slug for item in reversed(prior) if item.concept_slug), None)
        plan = build_turn(screened, history, mode, sticky)
        reply = self.tutor.reply(plan, [(item.role, item.content) for item in history], screened)
        if mode == "direct":
            cites = library_citations(self.settings, self.session, self.repo, screened)
            if cites:
                lines = "\n".join(f"- {item['citation']} {item['title']}" for item in cites)
                reply = f"{reply}\n\nFurther reading from the library\n{lines}"
        now = datetime.now(UTC)
        self.repo.add_message(conversation, "user", screened, plan.concept_slug, now)
        saved = self.repo.add_message(
            conversation, "assistant", reply, plan.concept_slug, now + timedelta(milliseconds=1)
        )
        self.touch(user)
        return {
            "conversation_id": conversation.id,
            "mode": plan.mode,
            "stage": plan.stage,
            "concept_slug": plan.concept_slug,
            "reply": {"id": saved.id, "role": "assistant", "content": saved.content},
        }

    def orchestrate(self, user: User, message: str) -> dict:
        return dispatch(self, user, message)

    def generate_quiz(self, user: User, concept_slug: str, difficulty: str) -> dict:
        concept = get_concept(concept_slug)
        if concept is None:
            raise ClientError("Unknown concept.", 404)
        lab = self.settings.resolved_lab_enabled
        available = [
            item
            for item in QUESTIONS
            if item.concept == concept_slug and (lab or item.kind != "coding")
        ]
        matched = [item for item in available if item.difficulty == difficulty]
        note = None
        if not matched:
            matched = available
            note = (
                "No items were authored at that difficulty, so this quiz uses the available items."
            )
        if not matched:
            raise ClientError("No authored questions for that concept yet.", 404)
        quiz = Quiz(
            user_id=user.id,
            concept_slug=concept_slug,
            title=f"{concept.name} · {difficulty}",
            difficulty=difficulty,
        )
        self.session.add(quiz)
        self.session.flush()
        public = []
        for position, item in enumerate(matched[:5]):
            row = Question(
                quiz_id=quiz.id,
                kind=item.kind,
                prompt=item.prompt,
                options=list(item.options),
                answer_key={
                    "answer": item.answer,
                    "phrases": list(item.phrases),
                    "expected_stdout": item.expected_stdout,
                },
                explanation=item.explanation,
                position=position,
            )
            self.session.add(row)
            self.session.flush()
            public.append(
                {
                    "id": row.id,
                    "kind": row.kind,
                    "prompt": row.prompt,
                    "options": row.options or [],
                    "position": position,
                }
            )
        return {
            "id": quiz.id,
            "title": quiz.title,
            "difficulty": difficulty,
            "concept_slug": concept_slug,
            "difficulty_note": note,
            "coach_note": self.quiz_agent.coach(concept.name, difficulty),
            "questions": public,
        }

    def grade_quiz(self, user: User, quiz_id: uuid.UUID, answers: list[dict]) -> dict:
        quiz = self.repo.quiz_for_user(quiz_id, user.id)
        if quiz is None:
            raise ClientError("Quiz not found.", 404)
        if self.repo.quiz_result(quiz.id) is not None:
            raise ClientError("This quiz was already submitted. Generate a new one to retry.", 409)
        by_id = self.repo.question_map(quiz)
        graded = []
        score = 0.0
        seen: set[uuid.UUID] = set()
        for answer in answers:
            question = by_id.get(answer["question_id"])
            if question is None:
                raise ClientError("That question is not part of this quiz.")
            if question.id in seen:
                continue
            seen.add(question.id)
            ratio, feedback, correct = self._grade_question(question, answer["response"])
            score += ratio
            graded.append(
                {
                    "question_id": str(question.id),
                    "correct": correct,
                    "score": ratio,
                    "feedback": feedback,
                    "explanation": question.explanation,
                }
            )
        result = QuizResult(
            quiz_id=quiz.id,
            user_id=user.id,
            score=score,
            max_score=float(len(quiz.questions)),
            answers={"items": graded},
        )
        self.session.add(result)
        try:
            with self.session.begin_nested():
                self.session.flush()
        except IntegrityError as exc:
            raise ClientError("This quiz was already submitted.", 409) from exc
        self.recompute(user, quiz.concept_slug)
        ratio = score / result.max_score if result.max_score else 0
        self.grant(user, "quiz", str(quiz.id), quiz_xp(ratio))
        return {
            "quiz_id": quiz.id,
            "score": score,
            "max_score": result.max_score,
            "results": graded,
        }

    def complete_lesson(self, user: User, slug: str) -> dict:
        lesson = self.repo.lesson_by_slug(slug)
        if lesson is None:
            raise ClientError("Lesson not found.", 404)
        created = self.repo.complete_lesson(user.id, lesson)
        if created:
            self.grant(user, "lesson", str(lesson.id))
        self.recompute(user, slug)
        return {
            "slug": slug,
            "completed": True,
            "newly_completed": created,
            "content_md": lesson.content_md,
        }

    def create_plan(self, user: User, goal: str) -> dict:
        screened = self._screen(goal, max_length=2000)
        today = learner_day(datetime.now(UTC), user.timezone)
        items = build_study_plan(screened, self.repo.mastery_map(user.id), today)
        plan = StudyPlan(user_id=user.id, title=screened[:80], goal=screened)
        self.session.add(plan)
        self.session.flush()
        payload = []
        for position, item in enumerate(items):
            lesson = self.repo.lesson_by_slug(item.slug)
            row = StudyPlanItem(
                plan_id=plan.id,
                concept_slug=item.slug,
                lesson_id=None if lesson is None else lesson.id,
                title=item.title,
                scheduled_for=item.scheduled_for,
                position=position,
            )
            self.session.add(row)
            payload.append(
                {
                    "title": item.title,
                    "slug": item.slug,
                    "scheduled_for": item.scheduled_for.isoformat(),
                }
            )
        explanation = self.planner_agent.explain(screened, [item.title for item in items])
        return {"id": plan.id, "goal": screened, "explanation": explanation, "items": payload}

    def list_plans(self, user: User) -> list[dict]:
        plans = []
        for plan in self.repo.study_plans(user.id):
            plans.append(
                {
                    "id": plan.id,
                    "goal": plan.goal,
                    "items": [
                        {
                            "title": item.title,
                            "slug": item.concept_slug,
                            "scheduled_for": item.scheduled_for.isoformat(),
                            "status": item.status,
                        }
                        for item in sorted(plan.items, key=lambda row: row.position)
                    ],
                }
            )
        return plans

    def ingest(self, user: User, filename: str, data: bytes) -> dict:
        text = parse_upload(filename, data)
        pieces = chunk_text(text)
        document = ResearchDocument(
            user_id=user.id,
            title=Path(filename).name,
            filename=Path(filename).name,
            media_type=_media_type(filename),
            status="processing",
        )
        self.session.add(document)
        self.session.flush()
        chunks = [
            DocumentChunk(
                document_id=document.id,
                ordinal=ordinal,
                text=piece,
                token_count=max(1, len(piece) // 4),
                citation_label=f"[{ordinal + 1}]",
            )
            for ordinal, piece in enumerate(pieces)
        ]
        self.session.add_all(chunks)
        self.session.flush()
        indexed = True
        try:
            index_document(self.settings, self.session, user.id, chunks)
        except IndexUnavailable:
            log.warning("document %s stored without vectors", document.id, exc_info=True)
            indexed = False
        document.status = "ready" if indexed else "unindexed"
        return {
            "id": document.id,
            "title": document.title,
            "chunks": len(chunks),
            "status": document.status,
        }

    def analyze(self, user: User, document_id: uuid.UUID, question: str) -> dict:
        screened = self._screen(question, max_length=2000)
        document = self.repo.document_for_user(document_id, user.id)
        if document is None:
            raise ClientError("Document not found.", 404)
        chunks = sorted(document.chunks, key=lambda item: item.ordinal)
        if not chunks:
            raise ClientError("That document has no extractable text.")
        retrieval_note = None
        try:
            ranked = search_document(
                self.settings, self.session, self.repo, user.id, document.id, screened
            )
        except IndexUnavailable:
            ranked = []
            retrieval_note = "Search was unavailable, so these are the opening passages."
        if not ranked:
            ranked = chunks[:4]
        excerpts = [(chunk.citation_label, chunk.text[:1200]) for chunk in ranked]
        model_fields = self.research_agent.critique(excerpts)
        extractive = "\n\n".join(f"{label} {text[:400]}" for label, text in excerpts)
        full_text = "\n\n".join(chunk.text for chunk in chunks)
        summary = model_fields["summary"] or extractive
        mode = "model" if model_fields["summary"] else "extractive"
        document.summary = summary[:4000]
        self.grant(user, "analysis", str(document.id))
        limitation = None
        if mode == "extractive":
            limitation = (
                "This pass is extractive. Critique, gaps, and future work are withheld "
                "until a model can tie them to a citation, so nothing is invented."
            )
        if retrieval_note:
            limitation = f"{retrieval_note} {limitation or ''}".strip()
        return {
            "document_id": document.id,
            "mode": mode,
            "summary": summary,
            "excerpts": [{"citation": label, "text": text} for label, text in excerpts],
            "equations": extract_equations(full_text),
            "critique": model_fields["critique"] or None,
            "gaps": model_fields["gaps"] or None,
            "future_work": model_fields["future_work"] or None,
            "limitations_of_this_pass": limitation,
        }

    def run_code(self, user: User, code: str, project_slug: str | None) -> dict:
        if not self.settings.resolved_lab_enabled:
            raise ClientError(LAB_OFF, 503)
        project = self.repo.project_by_slug(project_slug) if project_slug else None
        if project_slug and project is None:
            raise ClientError("Project not found.", 404)
        outcome = run_student_code(code)
        notes = review_notes(code)
        narration = self.coding_agent.narrate(code, notes, outcome)
        review = "\n".join(f"- {note}" for note in notes)
        if narration:
            review += f"\n\n{narration}"
        submission = CodeSubmission(
            project_id=None if project is None else project.id,
            user_id=user.id,
            code=code,
            stdout=outcome["stdout"],
            stderr=outcome["stderr"],
            review_md=review,
            status=outcome["status"],
        )
        self.session.add(submission)
        self.session.flush()
        if outcome["status"] == "ok" and project is not None:
            self.grant(user, "project", str(project.id))
            if project.concept_slug:
                self.recompute(user, project.concept_slug)
        else:
            self.touch(user)
        return {
            "id": submission.id,
            "status": outcome["status"],
            "stdout": outcome["stdout"],
            "stderr": outcome["stderr"],
            "review": review,
        }

    def projects(self) -> list[dict]:
        return [
            {
                "slug": project.slug,
                "title": project.title,
                "brief_md": project.brief_md,
                "starter_code": project.starter_code,
                "language": project.language,
                "difficulty": project.difficulty,
            }
            for project in self.repo.projects()
        ]

    def generate_cards(self, user: User, concept_slug: str) -> dict:
        concept = get_concept(concept_slug)
        if concept is None:
            raise ClientError("Unknown concept.", 404)
        existing = self.repo.card_fronts(user.id, concept_slug)
        created = 0
        pairs = (
            (f"Explain {concept.name} in plain language.", concept.scaffold),
            (concept.opener, concept.scaffold),
        )
        now = datetime.now(UTC)
        for front, back in pairs:
            if front in existing:
                continue
            self.session.add(
                Flashcard(
                    user_id=user.id,
                    concept_slug=concept_slug,
                    front=front,
                    back=back,
                    next_review_at=now,
                )
            )
            created += 1
        return {"concept_slug": concept_slug, "created": created}

    def due_cards(self, user: User) -> list[dict]:
        now = datetime.now(UTC)
        return [
            {
                "id": card.id,
                "front": card.front,
                "back": card.back,
                "concept_slug": card.concept_slug,
                "interval_days": card.interval_days,
            }
            for card in self.repo.due_cards(user.id, now)
        ]

    def review_card(self, user: User, card_id: uuid.UUID, rating: int) -> dict:
        card = self.repo.card_for_user(card_id, user.id)
        if card is None:
            raise ClientError("Card not found.", 404)
        updated = SM2Scheduler().review(
            ScheduleState(card.ease_factor, card.interval_days, card.repetitions),
            rating,
        )
        card.ease_factor = updated.ease_factor
        card.interval_days = updated.interval_days
        card.repetitions = updated.repetitions
        card.next_review_at = datetime.now(UTC) + timedelta(days=updated.interval_days)
        review = Review(
            flashcard_id=card.id,
            user_id=user.id,
            rating=rating,
            ease_factor=updated.ease_factor,
            interval_days=updated.interval_days,
            repetitions=updated.repetitions,
        )
        self.session.add(review)
        self.session.flush()
        if card.concept_slug:
            self.recompute(user, card.concept_slug)
        self.grant(user, "review", str(review.id))
        return {
            "id": card.id,
            "interval_days": card.interval_days,
            "next_review_at": card.next_review_at.isoformat(),
            "ease_factor": card.ease_factor,
        }

    def career(self, user: User) -> dict:
        matches = match_roles(self.repo.mastery_map(user.id))
        payload = [
            {
                "title": match.title,
                "summary": match.summary,
                "readiness": match.readiness,
                "missing": list(match.missing),
            }
            for match in matches
        ]
        lines = [
            (
                f"{item['title']}: readiness {item['readiness']}; "
                f"missing {', '.join(item['missing']) or 'none'}"
            )
            for item in payload
        ]
        return {"roles": payload, "explanation": self.career_agent.explain("\n".join(lines))}

    def dashboard(self, user: User) -> dict:
        mastery = self.repo.mastery_map(user.id)
        level, into, per = level_progress(user.xp)
        grouped: dict[str, list[dict]] = {"strength": [], "developing": [], "gap": []}
        for slug, score in mastery.items():
            concept = get_concept(slug)
            item = {"slug": slug, "name": concept.name if concept else slug, "score": score}
            key = band(score)
            if key in grouped:
                grouped[key].append(item)
        completed = self.repo.completed_lesson_ids(user.id)
        paths = []
        for path in self.repo.paths():
            ids = [item.lesson_id for item in path.items if item.lesson_id is not None]
            paths.append(
                {
                    "slug": path.slug,
                    "title": path.title,
                    "description": path.description,
                    "level": path.level,
                    "completed": sum(1 for lesson_id in ids if lesson_id in completed),
                    "total": len(ids),
                }
            )
        earned = self.repo.earned_achievement_ids(user.id)
        badges = [
            {
                "slug": achievement.slug,
                "name": achievement.name,
                "description": achievement.description,
                "earned": achievement.id in earned,
            }
            for achievement in self.repo.achievements()
        ]
        scores = list(mastery.values())
        return {
            "display_name": user.display_name,
            "role": user.role,
            "xp": user.xp,
            "level": level,
            "xp_into_level": into,
            "xp_per_level": per,
            "streak_days": user.streak_days,
            "subscription_status": user.subscription_status,
            "mastery": int(round(sum(scores) / len(scores))) if scores else 0,
            "strengths": grouped["strength"],
            "developing": grouped["developing"],
            "weaknesses": grouped["gap"],
            "recommendations": [
                {"slug": item.slug, "name": item.name, "reason": item.reason}
                for item in recommend(mastery, limit=4)
            ],
            "paths": paths,
            "badges": badges,
            "lessons_completed": self.repo.lesson_completion_count(user.id),
            "quizzes_taken": self._user_quiz_count(user),
        }

    def progress(self, user: User) -> dict:
        level, into, per = level_progress(user.xp)
        concepts = []
        for slug, score in sorted(self.repo.mastery_map(user.id).items()):
            concept = get_concept(slug)
            concepts.append(
                {
                    "slug": slug,
                    "name": concept.name if concept else slug,
                    "score": score,
                    "band": band(score),
                }
            )
        return {
            "xp": user.xp,
            "level": level,
            "xp_into_level": into,
            "xp_per_level": per,
            "streak_days": user.streak_days,
            "lessons_completed": self.repo.lesson_completion_count(user.id),
            "concepts": concepts,
        }

    def paths(self) -> list[dict]:
        return [
            {
                "slug": path.slug,
                "title": path.title,
                "description": path.description,
                "level": path.level,
                "concepts": len(path.items),
            }
            for path in self.repo.paths()
        ]

    def path_detail(self, user: User, slug: str) -> dict:
        path = self.repo.path_by_slug(slug)
        if path is None:
            raise ClientError("Learning path not found.", 404)
        lessons = self.repo.lessons_by_ids(
            [item.lesson_id for item in path.items if item.lesson_id]
        )
        completed = self.repo.completed_lesson_ids(user.id)
        steps = []
        for item in sorted(path.items, key=lambda row: row.position):
            lesson = lessons.get(item.lesson_id) if item.lesson_id else None
            concept = get_concept(lesson.slug) if lesson is not None else None
            steps.append(
                {
                    "position": item.position,
                    "slug": None if lesson is None else lesson.slug,
                    "title": lesson.title if lesson is not None else "Lesson",
                    "estimated_minutes": None if lesson is None else lesson.estimated_minutes,
                    "completed": bool(lesson and lesson.id in completed),
                    "prerequisites": [] if concept is None else list(concept.prerequisites),
                    "content_md": None if lesson is None else lesson.content_md,
                }
            )
        return {
            "slug": path.slug,
            "title": path.title,
            "description": path.description,
            "level": path.level,
            "steps": steps,
        }

    def graph(self, domain: str | None) -> dict:
        from app.domain.catalog import CONCEPTS

        nodes = [
            {
                "slug": concept.slug,
                "name": concept.name,
                "domain": concept.domain,
                "difficulty": concept.difficulty,
                "prerequisites": list(concept.prerequisites),
            }
            for concept in CONCEPTS
            if domain is None or concept.domain == domain
        ]
        return {"nodes": nodes, "mermaid": mermaid(domain)}

    def leaderboard(self) -> list[dict]:
        """Pseudonymous: a chosen handle or a stable alias, never a name or email (SRS §5.1)."""

        return [
            {
                "rank": rank,
                "display_name": user.handle or pseudonym(user.id),
                "xp": user.xp,
                "level": user.level,
                "streak_days": user.streak_days,
            }
            for rank, user in enumerate(self.repo.leaderboard(), start=1)
        ]

    def profile(self, user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "handle": user.handle,
            "locale": user.locale,
            "timezone": user.timezone,
            "country_code": user.country_code,
            "leaderboard_opt_out": user.leaderboard_opt_out,
            "subscription_status": user.subscription_status,
        }

    def update_profile(self, user: User, changes: dict) -> dict:
        from app.domain.gamification import valid_timezone

        if "timezone" in changes and not valid_timezone(changes["timezone"]):
            raise ClientError("Use an IANA time zone such as Africa/Lagos.", 422)
        handle = changes.get("handle")
        if handle and self.repo.handle_taken(handle, user.id):
            raise ClientError("That handle is taken.", 409)
        for key, value in changes.items():
            setattr(user, key, value)
        return self.profile(user)

    def set_role(self, actor: User, user_id: uuid.UUID, role: str, reason: str = "") -> dict:
        from app.domain.access import ROLES, is_allowed, role_change_issue

        if not is_allowed(actor.role, "admin"):
            raise ClientError("Admin role required.", 403)
        target = self.repo.user_by_id(user_id)
        if target is None:
            raise ClientError("User not found.", 404)
        issue = role_change_issue(
            actor_id=actor.id,
            target_id=target.id,
            current=target.role,
            requested=role,
            admin_count=self.repo.admin_count(),
        )
        if issue:
            raise ClientError(issue, 422 if role not in ROLES else 409)
        previous = target.role
        target.role = role
        self.repo.audit(
            actor.id,
            "user.role",
            "user",
            str(target.id),
            {"from": previous, "to": role, "reason": reason[:500]},
        )
        return {"id": target.id, "role": target.role}

    def users(self, actor: User) -> list[dict]:
        from app.domain.access import is_allowed

        if not is_allowed(actor.role, "admin"):
            raise ClientError("Admin role required.", 403)
        return [
            {
                "id": user.id,
                "display_name": user.display_name,
                "email": user.email,
                "role": user.role,
                "xp": user.xp,
                "streak_days": user.streak_days,
            }
            for user in self.repo.list_users()
        ]

    def analytics(self, actor: User) -> dict:
        from sqlalchemy import func, select

        from app.domain.access import is_allowed
        from app.models import ConceptMastery

        if not is_allowed(actor.role, "instructor"):
            raise ClientError("Instructor role required.", 403)
        counts = self.repo.counts()
        average = self.session.scalar(select(func.avg(ConceptMastery.score)))
        counts["average_mastery"] = float(average or 0)
        return counts

    def recompute(self, user: User, concept_slug: str) -> None:
        if get_concept(concept_slug) is None:
            return
        lesson = self.repo.lesson_by_slug(concept_slug)
        project = self.repo.project_for_concept(concept_slug)
        submissions = []
        if project is not None:
            submissions = self.repo.submissions_for_project(user.id, project.id)
        completed = self.repo.completed_lesson_ids(user.id)
        evidence = Evidence(
            quiz_scores=tuple(self.repo.quiz_ratios(user.id, concept_slug)),
            lessons_completed=1 if lesson is not None and lesson.id in completed else 0,
            lessons_available=1 if lesson is not None else 0,
            projects_passed=sum(1 for item in submissions if item.status == "ok"),
            projects_attempted=len(submissions),
            recall=self.repo.recall_for_concept(user.id, concept_slug),
        )
        self.repo.upsert_mastery(user.id, concept_slug, score_evidence(evidence))

    def touch(self, user: User) -> date:
        """Record activity for the streak without awarding XP (GAM-004)."""

        today = learner_day(datetime.now(UTC), user.timezone)
        user.streak_days = next_streak(user.streak_days, user.last_active_on, today)
        user.last_active_on = today
        return today

    def grant(
        self, user: User, source_type: str, source_id: str, computed: int | None = None
    ) -> int:
        """Award XP once per source on the learner's local day (GAM-001..003)."""

        today = self.touch(user)
        if self.repo.xp_event_exists(user.id, source_type, source_id):
            return 0
        requested = requested_xp(source_type, computed)
        granted = grant_for(
            source_type,
            requested,
            earned_today=self.repo.xp_on(user.id, today),
            awards_today=self.repo.xp_awards_on(user.id, source_type, today),
        )
        recorded = self.repo.add_xp_event(
            user_id=user.id,
            source_type=source_type,
            source_id=source_id,
            requested=requested,
            granted=granted,
            local_date=today,
        )
        if not recorded:
            return 0
        if granted:
            user.xp += granted
            user.level = level_progress(user.xp)[0]
        self._sync_badges(user)
        return granted

    def _sync_badges(self, user: User) -> None:
        earned = evaluate_badges(
            BadgeContext(
                lessons_completed=self.repo.lesson_completion_count(user.id),
                streak_days=user.streak_days,
                perfect_quiz=self.repo.has_perfect_quiz(user.id),
                max_mastery=self.repo.max_mastery(user.id),
                analyses=self.repo.analysis_count(user.id),
                code_passes=self.repo.code_pass_count(user.id),
            )
        )
        have = self.repo.earned_achievement_ids(user.id)
        for achievement in self.repo.achievements():
            if achievement.slug in earned and achievement.id not in have:
                self.repo.grant_achievement(user.id, achievement.id)

    def _user_quiz_count(self, user: User) -> int:
        from sqlalchemy import func, select

        return int(
            self.session.scalar(
                select(func.count()).select_from(QuizResult).where(QuizResult.user_id == user.id)
            )
            or 0
        )

    def _grade_question(self, question: Question, response: str) -> tuple[float, str, bool]:
        key = question.answer_key or {}
        if question.kind == "mcq":
            correct, ratio = grade_mcq(
                response, list(question.options or []), str(key.get("answer", ""))
            )
            return (
                ratio,
                "Matched the authored answer." if correct else "Not the authored answer.",
                correct,
            )
        if question.kind == "short":
            correct, ratio = grade_short(response, list(key.get("phrases") or []))
            return (
                ratio,
                "Covered the required ideas." if correct else "Missing required ideas.",
                correct,
            )
        if question.kind == "coding":
            if not self.settings.resolved_lab_enabled:
                raise ClientError(LAB_OFF, 503)
            outcome = run_student_code(response)
            if outcome["status"] != "ok":
                return 0.0, outcome["stderr"] or "The code did not run.", False
            correct, ratio = grade_coding(outcome["stdout"], str(key.get("expected_stdout", "")))
            return (
                ratio,
                "Output matched." if correct else "Output did not contain the expected result.",
                correct,
            )
        _correct, ratio, feedback = grade_research(response, list(key.get("phrases") or []))
        return ratio, feedback, ratio >= 0.6

    def _screen(self, text: str, max_length: int = 8000) -> str:
        result = screen_user_input(text, max_length=max_length)
        if not result.allowed:
            raise ClientError(
                "That message can't be used. Ask the learning question in plain text."
            )
        return result.text


def pseudonym(user_id: uuid.UUID) -> str:
    return f"Learner-{hashlib.sha256(user_id.bytes).hexdigest()[:6]}"


def parse_upload(filename: str, data: bytes) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ClientError("Files must be 10 MB or smaller.", 413)
    name = Path(filename or "upload.txt").name.lower()
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise ClientError("That file does not look like a PDF.")
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    elif name.endswith(".docx"):
        if not data.startswith(b"PK"):
            raise ClientError("That file does not look like a DOCX document.")
        from docx import Document

        document = Document(io.BytesIO(data))
        text = "\n\n".join(
            paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()
        )
    elif name.endswith(".md") or name.endswith(".txt"):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ClientError("Text uploads must be UTF-8.") from exc
    else:
        raise ClientError("Upload a PDF, DOCX, Markdown, or text file.")
    if not text.strip():
        raise ClientError(
            "No text could be extracted. Scanned pages need OCR, which this version does not do."
        )
    return text


def _media_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if name.endswith(".md"):
        return "text/markdown"
    return "text/plain"
