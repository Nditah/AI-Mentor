# ADR 0003 — PostgreSQL as the system of record

- Status: Accepted
- Date: 2026-10-13

## Context

Learners accumulate lessons, quiz results, mastery, flashcard schedules, code submissions, uploaded documents, and XP. The curriculum is relational: courses, modules, lessons, paths, and prerequisite links. The API also has to run tests without a database server on every laptop.

## Problem

Choose the database that owns learner state, and decide what is allowed to live somewhere else.

## Decision

PostgreSQL 16 is the system of record in every shared environment. SQLAlchemy 2 models in `backend/app/models/entities.py` define the tables. Alembic revision `20261013_0001` creates that metadata. Later revisions are explicit operations.

JSON columns use portable JSON so the same models run on SQLite. SQLite is allowed when `APP_ENV` is `development` or `test`. Production startup refuses a `DATABASE_URL` that is not PostgreSQL.

Vectors are not stored as a second copy in Postgres. The `embeddings` table records provider, model, dimensions, and the Qdrant point id. See ADR 0004.

Roles live on `users.role` with a check constraint of `student`, `instructor`, or `admin`. Progress is unique on `(user_id, lesson_id)`. Mastery is an integer from 0 to 100.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| SQLite in production | One writer, no private-network story, and a backup model that does not match a hosted learner record. |
| MongoDB | The curriculum, progress, and quiz attempts are relational. A document store would reimplement joins the dashboard already needs. |
| Postgres plus pgvector as the only index | pgvector keeps operations simpler. It also pins retrieval scale and filtering to the same primary that holds XP and quiz keys. ADR 0004 separates them. |
| Event sourcing | Mastery and the dashboard are computed from current rows. An event log would add a projector before there is a replay requirement. |

## Trade-off analysis

Relational integrity matches the product: a lesson completion, a quiz result, and a mastery row for the same concept must agree. Postgres point-in-time restore is the disaster-recovery path in `docs/Infrastructure.md`.

Portable JSON and SQLite keep CI free of a database service. The cost is that CI does not prove PostgreSQL-specific SQL. A staging Alembic run is that proof.

The first migration calls `create_all`. That is acceptable once. Repeating it would hide destructive drift. Development still calls `create_all` on startup so a fresh SQLite file works. Production does not.

Catalog seed upserts curriculum rows on startup and does not delete lessons, because a delete would cascade learner progress.

## Consequences

- Learner data restoration is a Postgres restore. Qdrant can be rebuilt from `document_chunks`.
- Answer keys live in `questions.answer_key` and are never returned by quiz generation.
- `xp_events` is append-only. The daily cap is enforced in the domain before an insert.
- Connection pooling stays in SQLAlchemy until connection count, rather than replica count, is the bottleneck.

## Future considerations

- Add a read replica only when dashboard reads show up in Postgres CPU. The read model is still computed in the API.
- Introduce PgBouncer with the migration job, not before.
- Keep expand-then-contract migrations once more than one API revision can be alive during a deploy.
