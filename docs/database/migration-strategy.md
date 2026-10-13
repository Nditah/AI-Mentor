# Migration strategy

How to move from the current MVP schema to the target design in [`backend/db/schema`](../../backend/db/schema) without downtime, and the rules every later migration follows.

## Where we are today

| Fact | Consequence |
| --- | --- |
| 32 tables in `public`, defined in `backend/app/models/entities.py` | All of them map onto the new schemas (table below) |
| Alembic revision `20261013_0001` lists every table with explicit `op.create_table` calls | Frozen. Later changes are new revisions; `alembic check` in CI catches drift |
| Only a SQLite development or test process calls `create_all`; the migrate job seeds | Staging and production change only through `python -m app.cli migrate` |
| The test suite runs on SQLite locally and on migrated PostgreSQL 16 in CI (`make test-pg`) | PostgreSQL-specific features (partitioning, RLS, `ltree`, `citext`, triggers) can be tested once the target schemas land |
| Every authenticated request sets transaction-local `app.current_user_id`, `app.user_role`, `app.request_id`, `app.client_ip` | Audit triggers and RLS policies have their context from the first target revision |
| The API connects as the database owner | Owners bypass RLS. The API must connect as `mentor_app` before RLS is relied on |
| `embeddings.point_id` equals the chunk id; collections are `learner_docs_v1` and `knowledge_v1` | Matches the target. Moving chunks to new tables re-indexes, it does not copy vectors |

## Principles

1. **Expand, migrate, contract.** New structures are added next to old ones, data is copied and kept in sync, reads switch over, and old structures are removed only after a full release cycle of verification.
2. **Every step is reversible until contract.** Expand steps can be undone by dropping the new schemas. Contract happens only after verification and a fresh backup.
3. **The DDL files are the source of truth for PostgreSQL-specific features.** SQLAlchemy models describe the tables for the ORM, but partitioning, RLS, triggers, and partial indexes are owned by hand-written Alembic revisions. Autogenerate is used only to detect drift (`alembic check`), never to write migrations.
4. **Released migrations are immutable.** A change to a released DDL file is a new revision, never an edit.

## Phase 0: foundations (before any schema change)

| Step | Detail | Status |
| --- | --- | --- |
| Freeze revision 0001 | Replace `Base.metadata.create_all()` with explicit `op.create_table` calls that reproduce today's 25 tables exactly (generate once with `alembic revision --autogenerate` against an empty database, then review). Existing databases are already at this revision, so nothing runs. | **Done.** |
| Stop `create_all` outside development | Guard the startup path on `APP_ENV == "development"`. Staging and production change only through `alembic upgrade`. | **Done** (SQLite in development and test only). |
| PostgreSQL in CI | Run integration tests against PostgreSQL 16 (Testcontainers or a CI service container). Keep SQLite only for unit tests that never touch the database (`app/domain` tests do not). Add `backend/db/verify.sh` as a CI job. | **Done**, including `verify.sh`. |
| Migration linting | Run [squawk](https://squawkhq.com) on every new revision's SQL to catch locking operations (non-concurrent index builds, volatile defaults, type changes). | **Done** (`make lint-migrations`, CI). |
| Roles | Create `mentor_owner`, `mentor_app`, `mentor_worker`, `mentor_readonly` (from `14_security.sql`). Migrations log in as a member of `mentor_owner`; the API logs in as `mentor_app`; jobs as `mentor_worker`. | Open (platform). |
| Request context | In `get_db()`, after acquiring the session, run `SET LOCAL app.current_user_id`, `app.user_role`, and `app.request_id` from the authenticated request. Workers set `app.context = 'system'`. Audit and RLS depend on this. | **Done** in `user_dep` via `bind_request_context`. Workers do not exist yet. |
| Extensions | On Azure Flexible Server, allow-list `pgcrypto, citext, pg_trgm, ltree, pg_cron` in `azure.extensions`, set `cron.database_name`, restart. | Open (platform). |
| Connection pooling | PgBouncer in transaction mode. `SET LOCAL` is transaction-scoped, so it is safe with transaction pooling; plain `SET` is not. | Open (platform). |

## Phase 1: expand (additive, zero downtime)

One Alembic revision per DDL file, applied in order. Each revision executes its file:

```python
"""Target schema: 05 learning."""

from pathlib import Path

from alembic import op

revision = "20261101_0105"
down_revision = "20261101_0104"

SQL = Path(__file__).resolve().parents[2] / "db" / "schema" / "05_learning.sql"


def upgrade() -> None:
    op.execute(SQL.read_text())


def downgrade() -> None:
    op.execute("DROP SCHEMA learning CASCADE")
```

Nothing reads from the new schemas yet, so this is invisible to users. The old `public` tables keep serving traffic.

Update the SQLAlchemy models in parallel: new classes with `__table_args__ = {"schema": "learning"}` etc., and partitioned tables declared with `postgresql_partition_by` so the ORM metadata matches (for drift detection) even though Alembic never creates them from metadata.

## Phase 2: backfill and dual-write

**Dual-write first, then backfill.** Deploy code that writes every change to both the old and the new tables in the same transaction. Then copy history in batches. Rows written after the backfill cursor are already in both places.

Backfill rules:

- Keyset pagination by primary key (`WHERE id > $last ORDER BY id LIMIT 5000`), one transaction per batch, sleep between batches to keep replication lag low.
- `INSERT ... ON CONFLICT DO NOTHING` so batches are idempotent and restartable.
- Existing ids are UUIDv4 and are kept as-is. Only new rows get UUIDv7. Mixed ids are fine; ordering benefits arrive as new data dominates.
- Partitioned targets receive historical rows into historical partitions. Create those partitions first (`util.create_time_partitions(parent, 'month', '<earliest month>', n)`) so nothing lands in the default partition.
- Run the backfill as a member of `mentor_owner` with `SET LOCAL app.skip_audit = 'on'` so the copy does not flood `audit.row_changes`. The trigger honours this setting only for owner-role logins, so the API cannot switch auditing off.

### Table mapping

| Current table | Target | Transformation |
| --- | --- | --- |
| `users` | `identity.users`, `identity.user_profiles`, `game.user_stats`, `identity.subscriptions` | `xp`, `level`, `streak_days`, `last_active_on` move to `user_stats`. `stripe_customer_id` and `subscription_status` become a `subscriptions` row when not `free`. Generate `handle` from `display_name` with a uniqueness suffix. |
| `concepts` | `curriculum.taxonomy_nodes`, `curriculum.concepts` | Create a taxonomy node per distinct `domain`, then link concepts to it. Map `difficulty` text to the enum. |
| `concept_relations` | `curriculum.concept_relations` | `source_id` → `from_concept_id`, `target_id` → `to_concept_id`. Load prerequisites in topological order; the cycle trigger rejects bad data, which is a feature. |
| `courses`, `modules`, `lessons` | `curriculum.courses`, `modules`, `lessons`, `lesson_contents` | `lessons.content_md` becomes one `lesson_contents` row (`locale='en'`, `teaching_style='mixed'`, `version=1`, `status='published'`). |
| `learning_paths`, `learning_path_items` | `curriculum.learning_paths`, `learning_path_items` | Rows with both `concept_id` and `lesson_id` keep `lesson_id` only (exactly-one rule). |
| `progress` | `learning.lesson_progress` | `completed_at` required when `status='completed'`; default it to `updated_at`. |
| `concept_mastery` | `learning.concept_mastery` | `concept_slug` → `concept_id` lookup; integer score to numeric. |
| `conversations`, `messages` | `chat.conversations`, `chat.messages` | `messages.user_id` from the parent conversation. `concept_slug` → `concept_id`. Recompute `message_count` and `last_message_at` after the backfill (the trigger only counts new inserts). |
| `quizzes`, `questions`, `quiz_results` | `learning.quizzes`, `quiz_items`, `quiz_attempts`, `question_responses` | Today's questions are per-quiz, so each becomes a `quiz_items` row with the question as `question_snapshot` (no bank `question_id`). Each `quiz_results` row becomes a submitted attempt. Split `answers` JSON into `question_responses` where it can be parsed. |
| `projects` | `curriculum.coding_exercises` | `kind='project'`. |
| `code_submissions` | `learning.code_submissions` | Map `status` (`ok` → `passed`, otherwise `failed`/`error`). Compute `code_sha256`. Backfill `exercise_completions` from the latest passing submission per (user, exercise). |
| `research_documents`, `document_chunks`, `embeddings` | `knowledge.files`, `assets` (`scope='personal'`), `asset_versions`, `chunks`, `vector.chunk_embeddings` | `summary` becomes a `document_analyses` row (`kind='summary'`). Re-embed chunks into the new `personal_documents__te3s_v1` collection; do not copy old point ids. |
| `study_plans`, `study_plan_items` | `learning.study_plans`, `study_plan_items` | `concept_slug` → `concept_id`. |
| `achievements`, `user_achievements` | `game.badges`, `game.user_badges` | Slugs match; `name` becomes `name_i18n = {"en": name}`. |
| `flashcards`, `reviews` | `learning.flashcards`, `learning.flashcard_reviews` | `concept_slug` → `concept_id`. `reviews.created_at` → `reviewed_at`; the old row holds only post-review state, so `ease_before`/`interval_before` come from the previous review (window function). |
| `xp_events` | `game.xp_ledger` | `local_date = (created_at AT TIME ZONE profile.timezone)::date`; `idempotency_key = 'legacy:' || id`; `requested_amount = amount`. Then rebuild `game.daily_activity` and verify `sum(amount)` against `user_stats.total_xp`. |

### Verification before switching reads

For every mapped table, compare between old and new:

- row counts per day,
- sums of key numeric columns (XP, scores, time spent),
- a sample of 1,000 random ids compared field by field,
- application-level checks: dashboard totals, leaderboard top 100, and a learner's mastery map rendered from both sources.

Run the comparison as a scheduled job during the dual-write period and alert on any mismatch.

## Phase 3: switch reads

Move reads to the new tables behind a feature flag, one domain at a time, lowest risk first: curriculum, then knowledge and vector, gamification, learning, and chat last. Keep dual-writing so a rollback is just flipping the flag back.

Turn on the remaining target features in this phase:

1. The API connects as `mentor_app`, so RLS is enforced. Watch for `insufficient_privilege` errors, which mean a code path is missing the request context.
2. Schedule partition maintenance, the XP compaction job, and the purge job (pg_cron jobs are created by `11_partitions.sql` and `12_privacy.sql` when the extension is present).
3. Start the vector outbox worker and the nightly Qdrant reconciler (compare `chunk_embeddings` counts per collection with Qdrant `count`, and re-enqueue missing points).
4. Start CDC to the warehouse from the read replica.

## Phase 4: contract

After at least one full release cycle with reads on the new schema and no mismatches:

1. Stop dual-writing.
2. Take a backup and confirm point-in-time recovery covers the moment before the drop.
3. Rename the old tables (`ALTER TABLE public.messages RENAME TO messages_legacy`), wait one week, then drop them.
4. Remove the legacy models from `entities.py` and the dual-write code.

## Zero-downtime rules for every migration

These apply to every revision after the initial cut-over.

| Operation | Do | Don't |
| --- | --- | --- |
| Any DDL | Start with `SET lock_timeout = '3s'; SET statement_timeout = '15min';` and retry on timeout | Wait indefinitely on a lock behind a long query |
| New index | `CREATE INDEX CONCURRENTLY` inside `op.get_context().autocommit_block()` | Plain `CREATE INDEX` on a populated table |
| Index on a partitioned table | `CREATE INDEX ... ON ONLY parent` (invalid), then `CREATE INDEX CONCURRENTLY` on each partition, then `ALTER INDEX parent_idx ATTACH PARTITION partition_idx` | Plain `CREATE INDEX` on the parent (locks every partition) |
| New column | Nullable, or `NOT NULL DEFAULT <constant>` (no rewrite since PostgreSQL 11) | Volatile defaults such as `now()` or `gen_random_uuid()` on big tables |
| New `NOT NULL` on existing column | Add `CHECK (col IS NOT NULL) NOT VALID`, backfill, `VALIDATE CONSTRAINT`, then `SET NOT NULL` (uses the validated check, no scan) | `SET NOT NULL` directly on a large table |
| New foreign key or check | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a separate transaction | Validating in the same statement |
| Change column type | Add a new column, dual-write, backfill, switch reads, drop the old column | `ALTER COLUMN TYPE` (rewrites the table) |
| Rename | Add new name, dual-write, switch, drop old (or a view during transition) | Rename a column the running code reads |
| New enum value | `ALTER TYPE ... ADD VALUE` in its own revision; code using it ships in the next deploy | Use the new value in the same transaction |
| Remove enum value | Convert the column to a new type via the column-swap pattern | Expect `ALTER TYPE` to drop values (it cannot) |
| Backfill | Batches of 1,000 to 10,000 rows by key, each its own transaction, outside the schema migration | One giant `UPDATE` |
| Convert a big table to partitioned | Create the partitioned table; add `CHECK` constraints matching each range on the old table (`NOT VALID`, then `VALIDATE`); attach the old table as the historical partition (validated check means no scan) | Copy hundreds of millions of rows during a deploy |

## Rollback

| Phase | Rollback |
| --- | --- |
| 0 | Revert the code; revision 0001 is unchanged in effect |
| 1 | `alembic downgrade` drops the new schemas; nothing reads them |
| 2 | Stop dual-writing; truncate the new tables if needed and re-run the backfill later |
| 3 | Flip the feature flag back to old reads; dual-writes keep old tables current |
| 4 | Restore from the pre-contract backup (point-in-time recovery). This is why contract waits a full cycle. |
