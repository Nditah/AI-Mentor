"""SQL repository. Queries stay here; teaching rules stay in the domain package."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Achievement,
    AssetChunk,
    AssetVersion,
    AuditEvent,
    CodeSubmission,
    ConceptMastery,
    Conversation,
    Flashcard,
    KnowledgeAsset,
    LearningPath,
    Lesson,
    Message,
    Progress,
    Project,
    Question,
    Quiz,
    QuizResult,
    ResearchDocument,
    Review,
    StudyPlan,
    User,
    UserAchievement,
    XpEvent,
)


def aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class SqlRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def user_by_clerk_id(self, clerk_id: str) -> User | None:
        return self.session.scalar(select(User).where(User.clerk_id == clerk_id))

    def user_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def upsert_user(
        self, *, clerk_id: str, email: str, display_name: str, role: str | None
    ) -> User:
        user = self.user_by_clerk_id(clerk_id)
        if user is None:
            user = User(
                clerk_id=clerk_id,
                email=email,
                display_name=display_name,
                role=role or "student",
            )
            self.session.add(user)
            self.session.flush()
            return user
        user.email = email
        if display_name:
            user.display_name = display_name
        if role:
            user.role = role
        return user

    def list_users(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.created_at)).all())

    def admin_count(self) -> int:
        return int(
            self.session.scalar(select(func.count()).select_from(User).where(User.role == "admin"))
            or 0
        )

    def paths(self) -> list[LearningPath]:
        return list(
            self.session.scalars(
                select(LearningPath)
                .options(selectinload(LearningPath.items))
                .order_by(LearningPath.title)
            ).all()
        )

    def path_by_slug(self, slug: str) -> LearningPath | None:
        return self.session.scalar(
            select(LearningPath)
            .options(selectinload(LearningPath.items))
            .where(LearningPath.slug == slug)
        )

    def lesson_by_slug(self, slug: str) -> Lesson | None:
        return self.session.scalar(select(Lesson).where(Lesson.slug == slug))

    def lessons_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Lesson]:
        if not ids:
            return {}
        rows = self.session.scalars(select(Lesson).where(Lesson.id.in_(ids))).all()
        return {row.id: row for row in rows}

    def conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        return self.session.scalar(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )

    def conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        return list(
            self.session.scalars(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
            ).all()
        )

    def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        concept_slug: str | None,
        created_at: datetime | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            concept_slug=concept_slug,
        )
        if created_at is not None:
            message.created_at = created_at
        self.session.add(message)
        self.session.flush()
        return message

    def mastery_map(self, user_id: uuid.UUID) -> dict[str, int]:
        rows = self.session.scalars(
            select(ConceptMastery).where(ConceptMastery.user_id == user_id)
        ).all()
        return {row.concept_slug: row.score for row in rows}

    def upsert_mastery(self, user_id: uuid.UUID, concept_slug: str, score: int) -> None:
        row = self.session.scalar(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_slug == concept_slug,
            )
        )
        if row is None:
            self.session.add(
                ConceptMastery(user_id=user_id, concept_slug=concept_slug, score=score)
            )
        else:
            row.score = score
        self.session.flush()

    def completed_lesson_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        rows = self.session.scalars(
            select(Progress.lesson_id).where(
                Progress.user_id == user_id, Progress.status == "completed"
            )
        ).all()
        return set(rows)

    def complete_lesson(self, user_id: uuid.UUID, lesson: Lesson) -> bool:
        existing = self.session.scalar(
            select(Progress).where(Progress.user_id == user_id, Progress.lesson_id == lesson.id)
        )
        if existing is not None:
            return False
        self.session.add(
            Progress(
                user_id=user_id,
                lesson_id=lesson.id,
                status="completed",
                completed_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return True

    def quiz_for_user(self, quiz_id: uuid.UUID, user_id: uuid.UUID) -> Quiz | None:
        return self.session.scalar(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == quiz_id, Quiz.user_id == user_id)
        )

    def projects(self) -> list[Project]:
        return list(self.session.scalars(select(Project).order_by(Project.title)).all())

    def project_by_slug(self, slug: str) -> Project | None:
        return self.session.scalar(select(Project).where(Project.slug == slug))

    def project_for_concept(self, concept_slug: str) -> Project | None:
        return self.session.scalar(select(Project).where(Project.concept_slug == concept_slug))

    def document_for_user(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> ResearchDocument | None:
        return self.session.scalar(
            select(ResearchDocument)
            .options(selectinload(ResearchDocument.chunks))
            .where(ResearchDocument.id == document_id, ResearchDocument.user_id == user_id)
        )

    def due_cards(self, user_id: uuid.UUID, now: datetime) -> list[Flashcard]:
        rows = self.session.scalars(select(Flashcard).where(Flashcard.user_id == user_id)).all()
        return [row for row in rows if aware(row.next_review_at) <= now]

    def card_for_user(self, card_id: uuid.UUID, user_id: uuid.UUID) -> Flashcard | None:
        return self.session.scalar(
            select(Flashcard).where(Flashcard.id == card_id, Flashcard.user_id == user_id)
        )

    def card_fronts(self, user_id: uuid.UUID, concept_slug: str) -> set[str]:
        rows = self.session.scalars(
            select(Flashcard.front).where(
                Flashcard.user_id == user_id, Flashcard.concept_slug == concept_slug
            )
        ).all()
        return set(rows)

    def xp_today(self, user_id: uuid.UUID, today: date) -> int:
        start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
        total = self.session.scalar(
            select(func.coalesce(func.sum(XpEvent.amount), 0)).where(
                XpEvent.user_id == user_id, XpEvent.created_at >= start
            )
        )
        return int(total or 0)

    def leaderboard(self, limit: int = 10) -> list[User]:
        return list(
            self.session.scalars(
                select(User).order_by(User.xp.desc(), User.display_name).limit(limit)
            ).all()
        )

    def study_plans(self, user_id: uuid.UUID) -> list[StudyPlan]:
        return list(
            self.session.scalars(
                select(StudyPlan)
                .options(selectinload(StudyPlan.items))
                .where(StudyPlan.user_id == user_id)
                .order_by(StudyPlan.created_at.desc())
            ).all()
        )

    def achievements(self) -> list[Achievement]:
        return list(self.session.scalars(select(Achievement).order_by(Achievement.name)).all())

    def earned_achievement_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        rows = self.session.scalars(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        ).all()
        return set(rows)

    def grant_achievement(self, user_id: uuid.UUID, achievement_id: uuid.UUID) -> None:
        self.session.add(UserAchievement(user_id=user_id, achievement_id=achievement_id))
        self.session.flush()

    def lesson_completion_count(self, user_id: uuid.UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(Progress)
                .where(Progress.user_id == user_id, Progress.status == "completed")
            )
            or 0
        )

    def has_perfect_quiz(self, user_id: uuid.UUID) -> bool:
        row = self.session.scalar(
            select(QuizResult.id).where(
                QuizResult.user_id == user_id,
                QuizResult.max_score > 0,
                QuizResult.score >= QuizResult.max_score,
            )
        )
        return row is not None

    def analysis_count(self, user_id: uuid.UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(ResearchDocument)
                .where(ResearchDocument.user_id == user_id, ResearchDocument.summary.is_not(None))
            )
            or 0
        )

    def code_pass_count(self, user_id: uuid.UUID) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(CodeSubmission)
                .where(CodeSubmission.user_id == user_id, CodeSubmission.status == "ok")
            )
            or 0
        )

    def max_mastery(self, user_id: uuid.UUID) -> int:
        value = self.session.scalar(
            select(func.max(ConceptMastery.score)).where(ConceptMastery.user_id == user_id)
        )
        return int(value or 0)

    def quiz_ratios(self, user_id: uuid.UUID, concept_slug: str) -> list[float]:
        quizzes = self.session.scalars(
            select(Quiz).where(Quiz.user_id == user_id, Quiz.concept_slug == concept_slug)
        ).all()
        ratios: list[float] = []
        for quiz in quizzes:
            result = self.session.scalar(
                select(QuizResult)
                .where(QuizResult.quiz_id == quiz.id)
                .order_by(QuizResult.created_at.desc())
            )
            if result is not None and result.max_score:
                ratios.append(result.score / result.max_score)
        return ratios

    def submissions_for_project(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[CodeSubmission]:
        return list(
            self.session.scalars(
                select(CodeSubmission).where(
                    CodeSubmission.user_id == user_id, CodeSubmission.project_id == project_id
                )
            ).all()
        )

    def recall_for_concept(self, user_id: uuid.UUID, concept_slug: str) -> float | None:
        ratings = self.session.scalars(
            select(Review.rating)
            .join(Flashcard, Flashcard.id == Review.flashcard_id)
            .where(Flashcard.user_id == user_id, Flashcard.concept_slug == concept_slug)
        ).all()
        if not ratings:
            return None
        return sum(ratings) / (5 * len(ratings))

    def question_map(self, quiz: Quiz) -> dict[uuid.UUID, Question]:
        return {question.id: question for question in quiz.questions}

    def counts(self) -> dict[str, int]:
        def count(model: type) -> int:
            return int(self.session.scalar(select(func.count()).select_from(model)) or 0)

        students = self.session.scalar(
            select(func.count()).select_from(User).where(User.role == "student")
        )
        return {
            "users": count(User),
            "students": int(students or 0),
            "conversations": count(Conversation),
            "quizzes_taken": count(QuizResult),
            "documents": count(ResearchDocument),
        }

    def assets(self, state: str | None = None) -> list[KnowledgeAsset]:
        query = select(KnowledgeAsset).order_by(KnowledgeAsset.updated_at.desc())
        if state:
            query = query.where(KnowledgeAsset.state == state)
        return list(self.session.scalars(query).all())

    def asset_by_id(self, asset_id: uuid.UUID) -> KnowledgeAsset | None:
        return self.session.get(KnowledgeAsset, asset_id)

    def asset_slug_taken(self, slug: str) -> bool:
        found = self.session.scalar(select(KnowledgeAsset.id).where(KnowledgeAsset.slug == slug))
        return found is not None

    def replace_chunks(self, asset: KnowledgeAsset, pieces: list[str]) -> None:
        for chunk in list(asset.chunks):
            self.session.delete(chunk)
        self.session.flush()
        for ordinal, piece in enumerate(pieces):
            self.session.add(
                AssetChunk(
                    asset_id=asset.id,
                    ordinal=ordinal,
                    text=piece,
                    citation_label=f"[{ordinal + 1}]",
                )
            )

    def snapshot(self, asset: KnowledgeAsset, editor_id: uuid.UUID, note: str) -> None:
        self.session.add(
            AssetVersion(
                asset_id=asset.id,
                version=asset.version,
                title=asset.title,
                body_md=asset.body_md,
                state=asset.state,
                editor_id=editor_id,
                change_note=note[:500],
            )
        )

    def versions(self, asset_id: uuid.UUID) -> list[AssetVersion]:
        return list(
            self.session.scalars(
                select(AssetVersion)
                .where(AssetVersion.asset_id == asset_id)
                .order_by(AssetVersion.version.desc(), AssetVersion.created_at.desc())
            ).all()
        )

    def audit(
        self,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        detail: dict,
    ) -> None:
        self.session.add(
            AuditEvent(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                detail=detail,
            )
        )

    def audit_events(self, limit: int = 100) -> list[AuditEvent]:
        return list(
            self.session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)).all()
        )

    def published_chunks(self) -> list[tuple[str, str, str]]:
        rows = self.session.execute(
            select(AssetChunk.citation_label, AssetChunk.text, KnowledgeAsset.title)
            .join(KnowledgeAsset, KnowledgeAsset.id == AssetChunk.asset_id)
            .where(KnowledgeAsset.state == "published")
        ).all()
        return [(label, text, title) for label, text, title in rows]
