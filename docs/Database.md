# Database

This page describes the current MVP schema. The proposed target architecture (domain schemas, partitioning, RLS, audit, retention) is in [docs/database](database/README.md) and [ADR 0011](adr/0011-target-database-architecture.md).

PostgreSQL is the system of record. The SQLAlchemy models in `backend/app/models/entities.py` define the tables. Alembic revision `20261013_0001` creates that metadata. Later revisions should be explicit operations, not another `create_all`.

UUIDs are primary keys. Most tables have `created_at` and `updated_at`. `xp_events` is append-only and has `created_at` only. JSON columns are portable JSON, not JSONB, so the same models run on SQLite in tests.

## Entity map

```mermaid
erDiagram
  users ||--o{ conversations : owns
  users ||--o{ messages : writes
  conversations ||--o{ messages : contains
  users ||--o{ quizzes : takes
  quizzes ||--o{ questions : contains
  users ||--o{ quiz_results : scores
  quizzes ||--o{ quiz_results : graded
  courses ||--o{ modules : contains
  modules ||--o{ lessons : contains
  learning_paths ||--o{ learning_path_items : orders
  lessons ||--o{ learning_path_items : appears
  users ||--o{ progress : completes
  lessons ||--o{ progress : tracked
  users ||--o{ concept_mastery : scores
  users ||--o{ research_documents : uploads
  research_documents ||--o{ document_chunks : split
  document_chunks ||--o| embeddings : indexed
  users ||--o{ study_plans : plans
  study_plans ||--o{ study_plan_items : steps
  users ||--o{ flashcards : reviews
  flashcards ||--o{ reviews : history
  users ||--o{ code_submissions : submits
  projects ||--o{ code_submissions : receives
  users ||--o{ xp_events : earns
  achievements ||--o{ user_achievements : granted
  users ||--o{ user_achievements : holds
  concepts ||--o{ concept_relations : links
```

## Notes that are easy to get wrong

- `embeddings` stores `provider`, `model`, `dimensions`, and `qdrant_point_id`. It does not store the vector. Qdrant holds the vector when configured. The hash index is recomputed and is not duplicated in Postgres.
- Lesson slugs match concept slugs. Completing a lesson and scoring a concept use the same key.
- `progress` is unique on `(user_id, lesson_id)`.
- `concept_mastery.score` is an integer 0–100.
- `users.role` is constrained to `student`, `instructor`, `admin`.
- Quiz answer keys live on `questions.answer_key` and are never returned by the generate endpoint.
- Seeded catalog rows (courses, lessons, paths, achievements, projects, demo users) are upserted. Seed does not delete lessons, because that would cascade learner progress.
- Demo users: `demo-student`, `demo-instructor`, `demo-admin`, with emails `student@mentor.local`, `instructor@mentor.local`, `admin@mentor.local`.

## Local migration

```bash
cd backend
DATABASE_URL=postgresql+psycopg://mentor:mentor@localhost:5432/mentor ../.venv/bin/alembic upgrade head
```

Development also calls `create_all` on startup so a fresh SQLite file works without a migration step. Production should run `alembic upgrade head` before serving, which the API container does.
