# AI Mentor database architecture

This is the target PostgreSQL design for AI Mentor. It replaces the MVP schema in `backend/app/models/entities.py` (25 tables in `public`) with 97 tables in 12 domain schemas, built to scale to millions of learners and to feed analytics directly.

| Document | Contents |
| --- | --- |
| This file | Principles, schema map, each data model, keys, constraints, indexes, partitioning, scaling |
| [erd.md](erd.md) | Mermaid ER diagrams per domain |
| [migration-strategy.md](migration-strategy.md) | How to get from the current schema to this one without downtime |
| [data-retention.md](data-retention.md) | How long each kind of data is kept and how deletion is enforced |
| [ADR 0011](../adr/0011-target-database-architecture.md) | The decision record (proposed), including where it amends ADR 0003 |
| [`backend/db/schema/`](../../backend/db/schema) | SQL DDL, applied in file order |
| [`backend/db/tests/smoke.sql`](../../backend/db/tests/smoke.sql) | Executable checks of triggers, workflow, RLS, retention, and erasure |

```bash
backend/db/verify.sh        # build in a throwaway postgres:16 container and run the smoke tests
backend/db/verify.sh 17     # same on PostgreSQL 17
DATABASE_URL=postgresql://... backend/db/apply.sh   # apply to an empty database
```

## Design targets

The design is sized for the following load. These are planning numbers, not measurements. Revisit them once real traffic exists.

| Signal | Target | Daily rows it drives |
| --- | --- | --- |
| Registered learners | 1 million | |
| Daily active learners | 100,000 | |
| Tutor messages | 30 per active learner | ~3 M `chat.messages` |
| Product events | 200 per active learner | ~20 M `activity.events` |
| Question answers | 15 per active learner | ~1.5 M `learning.question_responses` |
| XP awards | 10 per active learner | ~1 M `game.xp_ledger` |
| Concepts in the graph | 2,000 | up to 2 B possible `concept_mastery` pairs, ~50 M real |

At 3 million messages a day (about 1.5 KB each with indexes), chat alone grows by roughly 130 GB a month. That number is why chat, events, and assessment evidence are partitioned by time from day one.

## Design principles

1. **One database, many schemas.** Domains are separated by PostgreSQL schema (`identity`, `curriculum`, `knowledge`, `vector`, `learning`, `chat`, `game`, `activity`, `analytics`, `audit`, plus `ref` and `util`). Grants, RLS, backups, and later extraction into separate services all follow schema boundaries.
2. **Language-neutral identity, localised content.** Progress, mastery, and answers point at language-neutral ids (`lesson_id`, `concept_id`, `question_id`). Text lives in per-locale rows (`lesson_contents`, `concept_translations`, `question_translations`). Switching language never forks a learner's record, which is a requirement in [Requirements.md](../Requirements.md).
3. **Ledgers over counters.** XP, mastery changes, workflow transitions, and audit are append-only ledgers. Counters (`game.user_stats`, `conversations.message_count`) are projections that can be rebuilt from them.
4. **Partition anything that grows with activity.** Partition by time when retention is time-based (messages, events, answers). Partition by hash when the table holds current state per learner (`concept_mastery`).
5. **The database enforces the rules that protect learners and content.** Examples: content cannot skip review, prerequisite graphs stay acyclic, XP awards are idempotent, and one learner cannot read another's chat. These live in constraints, triggers, and RLS rather than only in Python.
6. **Analytics is designed in, not bolted on.** Facts are denormalised at write time (`question_responses` carries `concept_id`, `difficulty`, `kind`). Daily rollups and a small star schema live in `analytics`. Everything streams to a warehouse by CDC.
7. **Vectors are derived data.** Qdrant holds embeddings. PostgreSQL records what was embedded, with which model, and in which collection, so a re-index is a controlled operation and the two stores can be reconciled.

## Schema map

| Schema | Tables | Purpose | Partitioned tables |
| --- | --- | --- | --- |
| `ref` | 3 + enums | Languages, countries, voice accents, shared enum types | |
| `identity` | 10 | Users, profiles, preferences, tutor avatar, onboarding, interests, billing, consent, privacy requests, webhook log | |
| `curriculum` | 16 | Taxonomy, concepts, concept graph, courses, modules, lessons and their localised bodies, paths, question bank, assessments, coding exercises | |
| `knowledge` | 12 | Files, curated and personal assets, versions, approval workflow, ingestion jobs, chunks, tags, objectives, AI-generated artifacts, research analyses | |
| `vector` | 5 | Embedding models, Qdrant collections, chunk and entity embedding lineage, sync outbox | |
| `learning` | 15 | Enrolments, lesson progress, mastery, mastery events, quizzes, attempts, answers, code submissions, flashcards, study plans, recommendations | 7 |
| `chat` | 5 | Conversations, messages, citations, feedback, rolling summaries | 3 |
| `game` | 13 | XP ledger and rollup, stats, daily activity, badges, titles, challenges, leaderboards, friendships | 2 |
| `activity` | 4 | Event catalogue, sessions, product events, LLM invocations | 3 |
| `analytics` | 10 + views | Date and user dimensions, daily facts, concept / content / platform aggregates, cohorts, learner reports | 2 |
| `audit` | 3 | Row changes, security events, staff data access | 3 |
| `util` | 1 | Partition registry and helper functions | |

## Data models

### User profile model

`identity.users` is a narrow identity row: Clerk id, email, public handle, role, account status. Authentication stays in Clerk. Everything that changes often or belongs to a specific feature is split out 1:1 so the users row is rarely updated:

| Table | Holds | Requirement it serves |
| --- | --- | --- |
| `user_profiles` | Country, ISO 3166-2 region, timezone, locale, persona, education, experience, industry, career goal, leaderboard visibility | Onboarding profile, country and regional leaderboards |
| `learning_preferences` | Teaching style, pace, technical depth, mathematics depth, breadth, preferred difficulty, programming and maths comfort, weekly study time | "Fully adaptive teaching style", "adjustable learning depth" |
| `tutor_avatars` | Age appearance, gender presentation, voice accent, personality, TTS voice | "AI tutor avatar system" |
| `onboarding_assessments` | Raw answers (versioned questionnaire), knowledge level, initial skill score, assigned persona, recommended path | Intelligent onboarding; retakes allowed |
| `user_interests` | Weighted links to taxonomy nodes (topic, research, or career interest) | Recommendations by interest |
| `subscriptions`, `consents`, `data_subject_requests`, `webhook_events` | Billing history, consent ledger, privacy requests, Clerk / Stripe idempotency | Stripe tiers, GDPR / NDPA compliance |

XP, level, and streak have moved out of `users` into `game.user_stats`. Preference history comes free from the audit trigger, so "how often do learners switch teaching style" can be answered without another table.

### Knowledge graph and curriculum

- **Taxonomy** (`taxonomy_nodes`) is a tree with a materialised `ltree` path such as `artificial_intelligence.reinforcement_learning.mdp`. Triggers keep paths correct when a node is renamed or moved, and they block moving a node under its own descendant. Subtree queries (`path <@ 'artificial_intelligence.reinforcement_learning'`) use a GiST index.
- **Concepts** are the nodes learners master. **`concept_relations`** are typed, weighted edges (`prerequisite`, `related`, `extends`, `part_of`, `applies_to`). A trigger rejects any `prerequisite` edge that would form a cycle, using an advisory lock so two concurrent edits cannot slip one past. The planner's "teach the weak prerequisite first" logic depends on that guarantee.
- **Lessons** hold structure (module, position, primary concept). **`lesson_contents`** holds the body per locale, teaching style, and version, with a partial unique index allowing one published body per (lesson, locale, style). `mixed` is the fallback style. This is how the platform serves "the Bellman equation, in French, in visual mode" without forking the lesson.
- **Positions** (modules, lessons, path items, assessment questions) use `DEFERRABLE` unique constraints so the drag-and-drop curriculum builder can swap positions in one transaction.
- **Path items** point at exactly one of course, module, lesson, concept, assessment, exercise, or asset, enforced by `CHECK (num_nonnulls(...) = 1)`, which keeps real foreign keys instead of a polymorphic `item_type, item_id` pair.
- **Question bank** stores IRT parameters (`irt_difficulty`, `irt_discrimination`) fitted offline from `question_responses`, the input to adaptive quiz difficulty.

### Knowledge repository model

Curated library content and a learner's own uploaded papers share one pipeline:

```text
files ──> assets ──> asset_versions ──> ingestion_jobs (parse → extract_metadata → chunk → embed → index → link)
                          │
                          └──> chunks ──> vector.chunk_embeddings ──> vector.sync_outbox ──> Qdrant
```

- `assets.scope` is `curated` or `personal`. A check constraint ties `owner_user_id` to `personal`. RLS hides personal assets and their chunks from everyone but the owner. Personal vectors go to a separate multitenant Qdrant collection.
- **Versioning.** `asset_versions` are immutable snapshots (file, content hash, extracted metadata, change summary, editor). Compare and restore work by version number. One version per asset may be `published` (partial unique index).
- **Approval workflow.** A trigger enforces `draft → review → approved → published → archived` (plus the backward moves `review → draft`, `approved → draft`, `archived → draft`). It refuses curated versions created in any state but `draft`, stamps `approved_by` / `published_at`, and writes every transition to `workflow_transitions` with an optional reviewer comment. This is how "only approved content becomes available to students" is enforced in the database.
- **Chunks** keep page range, section path, and citation label for citations, plus a generated `tsvector` (`simple` configuration, so it works for all three languages). That supports hybrid lexical-plus-vector retrieval and gives the tutor a fallback when Qdrant is unavailable.
- **AI content generation.** `generated_artifacts` holds lesson notes, flashcards, quizzes, exercises, study guides, and concept maps produced from a source version. They wait in `draft`/`review` and record which entity they became once published.
- **Research assistant.** `document_analyses` stores summaries, equation explanations, gap analyses, methodology critiques, and reviewer simulations per document version.

### Vector storage model

Qdrant holds the vectors. PostgreSQL holds the lineage.

| Table | Role |
| --- | --- |
| `embedding_models` | Provider, model, revision, dimensions, distance metric |
| `collections` | Physical Qdrant collection, its logical `alias`, purpose, HNSW and quantisation settings, multitenancy flag, last reconciled point count. One active collection per alias. |
| `chunk_embeddings` | Which chunk is embedded in which collection, with the content hash it was embedded from. The Qdrant point id equals `chunks.id`. |
| `entity_embeddings` | Embeddings of concepts, lesson bodies, questions (duplicate detection, similar-question search), learner memories, and cache entries |
| `sync_outbox` | Transactional outbox: Qdrant operations enqueued in the same transaction as the source change, drained by a worker with `FOR UPDATE SKIP LOCKED` |

Triggers enqueue a Qdrant delete when a chunk embedding row disappears, including by cascade when an asset or user is deleted. They enqueue a payload update when an asset's status changes, so archived content stops being retrieved without a re-index.

**Re-embedding with a new model** is blue/green: register the model, create a `building` collection, backfill `chunk_embeddings` for it, compare retrieval quality, then flip the alias and mark the old collection `draining`. Because `chunk_embeddings` is keyed by (chunk, collection), both collections stay consistent during the switch.

Qdrant payload per point (indexed fields in bold):

| Field | Source |
| --- | --- |
| `chunk_id`, `asset_id`, `asset_version_id` | Lineage back to PostgreSQL |
| **`scope`**, **`owner_user_id`** | `personal_documents` is multitenant: every query filters on `owner_user_id` |
| **`status`** | Retrieval filters on `published`; updated through the outbox |
| **`concept_ids`**, **`taxonomy_path`** | From `asset_concepts` and the taxonomy, for concept-scoped retrieval |
| **`locale`**, **`difficulty`**, `kind` | Language and level filtering |
| `citation_label`, `page_start`, `page_end` | Rendered citations without a database round trip |

pgvector is not used. If a small deployment wants to drop Qdrant, a `vector(1536)` column on `chunk_embeddings` with an HNSW index is a contained change, since the lineage model stays the same.

### Learning analytics model

Analytics is built in three layers:

1. **Evidence (OLTP, partitioned).** `question_responses`, `mastery_events`, `code_submissions`, `flashcard_reviews`, `recommendations`, `chat.messages`, `activity.events`. Each row carries the dimensions analytics needs (`user_id`, `concept_id`, `difficulty`, `kind`, `latency_ms`) so queries rarely join back to content tables.
2. **Current state.** `concept_mastery` (score, confidence, evidence count, a generated `band` of weak / developing / strong / mastered, and `next_review_at` for retention checks), `lesson_progress`, `enrollments`.
3. **Rollups (`analytics` schema).** Built by incremental jobs tracked in `etl_watermarks`.

| Requirement | Where it comes from |
| --- | --- |
| Knowledge mastery, strong and weak concepts | `learning.concept_mastery`, `analytics.v_learner_strengths` |
| Learning velocity | `learning.mastery_events` → `analytics.v_learning_velocity_weekly`, `fact_concept_mastery_daily` |
| Retention rates | `concept_mastery.next_review_at` checks, `source = 'decay'` events, `analytics.cohort_retention` for product retention |
| Quiz analytics | `question_responses` → `agg_concept_daily` (correct rate, latency, struggling learners) |
| Coding performance | `code_submissions`, `exercise_completions`, `fact_user_daily.code_passes` |
| Weekly and monthly reports | `analytics.learner_reports` (metrics, strengths, weaknesses, recommendations, AI narrative) |
| Admin: most visited lessons, completion rates, resource effectiveness | `agg_content_daily`, `mv_content_engagement_30d` (including mastery gain within 7 days of using a resource) |
| Admin: most difficult concepts, knowledge gaps | `agg_concept_daily`, `mv_concept_difficulty_30d` |
| Platform health: DAU/WAU/MAU, onboarding completion, TTFT, LLM cost | `agg_platform_daily`, `activity.llm_invocations` |

`analytics.dim_user` is a type 2 slowly changing dimension, so a learner who moved from `student` to `professional` is counted under the persona they had at the time.

### Chat history model

- `conversations` record the agent (tutor, quiz, planner, coding, research, career) and a snapshot of teaching style, personality, depth, and locale at the start. That makes "do learners in mathematical mode retain more?" answerable.
- `messages` are partitioned monthly. Each carries `user_id` (denormalised for RLS and erasure), router `intent`, Socratic step, whether the answer was `grounded` in the curated repository, token counts, latency, and time to first token.
- `message_citations` link answers to the exact chunk and asset version cited, with retrieval and rerank scores. This feeds "resource effectiveness" and retrieval evaluation.
- `message_feedback` captures thumbs up or down with a reason (incorrect, not grounded, wrong language, and so on).
- `conversation_summaries` hold rolling summaries that keep long threads inside the model's context window.
- Citations and feedback are **co-partitioned** with messages (partitioned on `message_created_at`). A foreign key to a partitioned parent blocks detaching a partition that still has referencing rows, so dropping a month of chat means dropping citations, feedback, and messages for that month together. The smoke test checks this.
- To read a thread, query `WHERE conversation_id = $1 AND created_at >= $conversation_created_at` so the planner prunes partitions older than the conversation.

### Gamification data model

- **`xp_ledger`** is the source of truth: one row per award with source, reference, and requested amount before the daily cap. It is partitioned by the learner's **local** date, which does two things. The idempotency key (`quiz:<attempt_id>`) can be unique per partition (`UNIQUE (user_id, idempotency_key, local_date)`), and the 400 XP daily cap and streaks use the day boundary the learner actually sees. Negative amounts are only allowed for `admin_adjustment` and `reversal`.
- **`user_stats`** is the projection (total XP, level, achievement points, current and longest streak, counters for badge rules), updated in the same transaction as the ledger insert. `fillfactor = 70` leaves room for HOT updates on this hot row.
- **`daily_activity`** has one row per learner per local day: XP earned and refused by the cap, goal met, streak freeze used. It drives the cap check, the streak calendar, and the heatmap.
- **Badges and titles** are admin-managed catalogs with `*_i18n` JSON names. The seeded badge slugs match `evaluate_badges()` in `backend/app/domain/gamification.py`. The seven titles from the requirements (AI Apprentice to Grandmaster AI Engineer) are seeded with level thresholds. One equipped title per learner is enforced by a partial unique index.
- **Daily challenges** are unique per (date, kind, difficulty, audience persona) using `NULLS NOT DISTINCT`, so the generator cannot create duplicates. Participation records score and XP.
- **Leaderboards.** Live rank lookups ("you are #4,512, top 3%") come from Redis sorted sets, which answer rank queries in O(log n). PostgreSQL stores materialised standings per (scope, scope key, period, metric). A refresh builds a new board in `building`, then flips it to `live` and marks the old one `superseded`, so readers never see a half-built ranking. Friends ranking is computed on read by joining `v_friends` to the global board, since friend lists are small. Leaderboards cover all six ranking metrics from the requirements (XP, challenges, quiz performance, projects, research, community) plus a composite.

### Activity tracking

- `activity.events` is the product event stream, partitioned **daily** by server `received_at`. Client clocks cannot be trusted, and partitioning on `occurred_at` would let a skewed client write into a dropped or future partition. Event ids are client-generated, so retries de-duplicate. There are no foreign keys, for ingest throughput; event names are validated at the API against `activity.event_types`, which also records schema version and whether the event contains personal data.
- `activity.sessions` stores device, platform, geo-IP country, and a keyed hash of the IP. Raw IPs are never stored.
- `activity.llm_invocations` stores cost, tokens, latency, TTFT, status, and Langfuse `trace_id` for every model call, including quiz generation, embeddings, and code review. Prompts and completions stay in Langfuse under its own shorter retention.

### Audit

- `audit.row_changes` is filled by one generic `SECURITY DEFINER` trigger attached to 26 governed tables: identity, curriculum, curated knowledge, vector configuration, gamification catalogs. It records actor, role, request id, and client IP from `SET LOCAL app.*` settings. Inserts store the new row, deletes the old row, and updates only the changed columns. No-op updates write nothing. Per-table redaction removes personal identifiers (email, names, handle, Clerk id, free-text profile fields, as Security-Compliance.md AL-4 requires), secrets (`answer_key`, `reference_solution`), and large bodies (`body_md`, `payload`). The application role cannot write to the table directly, and only owner-role logins can pause auditing for a bulk backfill (`app.skip_audit`).
- `audit.security_events` is application-written: sign-ins, role changes, impersonation, prompt-injection blocks, sandbox violations, erasures.
- `audit.data_access_log` records every time staff open a learner's personal data, with a purpose. It is indexed by subject so a learner's "who accessed my data" request is one query.
- High-volume learner tables are not row-audited, since they are already append-only ledgers.

## Keys, foreign keys, and constraints

**Primary keys.** UUIDv7 everywhere (`util.uuid_v7()`; on PostgreSQL 18 swap in the built-in `uuidv7()`). Ids stay globally unique, so Qdrant point ids, event ids, and client-generated ids just work. Being time-ordered, they keep B-tree inserts append-mostly, unlike random v4 UUIDs, which scatter writes across the index. Small admin catalogs (`badges`, `titles`, `tags`, `embedding_models`, `collections`) use `smallint`/`integer` identity. Audit tables use `bigint` identity. Composite natural keys are used where the pair is the identity (`lesson_progress (user_id, lesson_id)`, `concept_mastery (user_id, concept_id)`). On partitioned tables the partition key is part of the primary key, as PostgreSQL requires.

**Foreign key policy.**

| Relationship | `ON DELETE` | Reason |
| --- | --- | --- |
| Learner-owned data → `identity.users` | `CASCADE` | Erasure deletes the user row and everything follows |
| Billing → `identity.users` | `SET NULL` | Invoices are kept for tax; the user link is removed |
| Authorship (`created_by`, `reviewed_by`, `editor_id`) | `SET NULL` | Content outlives staff accounts |
| Structure: path items, assessment questions → content | `RESTRICT` | Cannot delete a lesson a published path depends on |
| Analytics references (quiz items, responses → questions) | `SET NULL` | History survives content removal; snapshots keep the text |
| Children of a parent (versions, chunks, modules) | `CASCADE` | Lifecycle is owned by the parent |
| Event stream, facts, LLM invocations | none | Ingest throughput and retention independence; erasure handles them explicitly |

Cross-schema foreign keys whose target is created later are added with `ALTER TABLE` at the end of the later file. `assets.current_version_id` is `DEFERRABLE INITIALLY DEFERRED` because assets and versions reference each other.

**Constraints that encode business rules** (267 check constraints in total):

- Score ranges (`score BETWEEN 0 AND 100`), non-negative counters, `correct_count <= evidence_count`, `tests_passed <= tests_total`, `longest_streak >= current_streak`.
- State coherence: `(status = 'completed') = (completed_at IS NOT NULL)` on progress, enrolments, attempts, and participations.
- Shape checks on JSON (`jsonb_typeof(options) = 'array'`, MCQ has two or more options, `name_i18n ? 'en'`).
- Size caps on free text, code, stdout, and event properties, so a single row cannot bloat a partition.
- Exactly-one-target checks (`num_nonnulls`) instead of polymorphic references.
- Partial unique indexes for "at most one": one published version per asset, one published body per lesson/locale/style, one live subscription, one equipped title, one active collection per alias, email unique among non-deleted users.

## Index strategy

252 indexes in total, including primary keys and unique constraints (plus 175 foreign keys). The rules behind them:

1. **Every foreign key used for lookups or cascades is indexed.** Cascading deletes on unindexed foreign keys are the classic cause of slow erasure and slow content deletion.
2. **Composite indexes follow the access path: equality columns first, then the range or sort column.** Examples: `(user_id, created_at)` for "my recent X", `(conversation_id, created_at)` for thread reads, `(concept_id, difficulty, kind)` for quiz assembly, `(user_id, next_review_at)` for due flashcards and retention checks.
3. **Partial indexes for queues and hot subsets.** Review queues (`status IN ('review','approved')`), ingestion and outbox backlogs, due flashcards (`NOT suspended`), published questions, live subscriptions, soft-deleted conversations awaiting purge, negative feedback. These stay tiny no matter how large the table grows.
4. **Indexes on partitioned parents are declared once** and propagate to every partition, including future ones. Each partition's index stays small enough to fit in memory, and dropping a partition drops its indexes with no bloat.
5. **GIN for search.** Weighted `tsvector` on concepts and assets, a `simple` `tsvector` on chunks for hybrid retrieval, and trigram (`gin_trgm_ops`) on titles for typo-tolerant admin search.
6. **GiST on `ltree`** for taxonomy subtree queries.
7. **BRIN** on `llm_invocations.created_at` for cheap time-range scans inside a month.
8. **Deliberately not indexed:** `activity.events.properties` (analysed in the warehouse), and message content full-text (high write cost on the hottest table; add a separate search service if "search my chats" ships).

Operational rules for new indexes are in [migration-strategy.md](migration-strategy.md#zero-downtime-rules-for-every-migration).

## Partitioning strategy

20 tables are partitioned. Range partitions are created ahead of time and dropped after retention by `util.run_partition_maintenance()`, driven by `util.partition_registry`, scheduled daily with pg_cron (or any external scheduler).

| Table | Method | Grain | Retention in PostgreSQL | Notes |
| --- | --- | --- | --- | --- |
| `activity.events` | range `received_at` | day | 90 days | Highest volume; warehouse keeps history |
| `activity.sessions`, `activity.llm_invocations` | range | month | 13 months | |
| `chat.messages` | range `created_at` | month | 24 months | Rolling window from Security-Compliance.md §11.5 |
| `chat.message_citations`, `chat.message_feedback` | range `message_created_at` | month | 24 months | Co-partitioned with messages |
| `learning.quiz_attempts` | range `started_at` | month | 25 months | |
| `learning.question_responses` | range `attempt_started_at` | month | 25 months | Co-partitioned with attempts |
| `learning.mastery_events` | range `occurred_at` | month | 25 months | Velocity history kept in facts |
| `learning.code_submissions` | range `submitted_at` | month | 12 months | Best solution kept in `exercise_completions` |
| `learning.flashcard_reviews`, `learning.recommendations` | range | month | 13 months | |
| `learning.concept_mastery` | **hash** `user_id` | 16 partitions | none | Current state; spreads vacuum and index size |
| `game.xp_ledger` | range `local_date` | month | 25 months | Compacted to `xp_monthly_rollup` first |
| `game.daily_activity` | range `activity_date` | month | 25 months | |
| `analytics.fact_user_daily`, `analytics.fact_concept_mastery_daily` | range | month | 25 months | User-level ceiling; aggregates are kept |
| `audit.row_changes`, `audit.data_access_log` | range | month | 2 years | Admin actions (AL-5); exported to WORM storage before drop |
| `audit.security_events` | range | month | 1 year | AL-5 |

Design notes:

- **Why monthly by default:** at the design target, monthly partitions of the big tables hold tens of millions of rows. That is small enough for fast vacuum and index rebuilds, and the partition count stays low enough that planning stays cheap. Events are the exception at around 20 million rows a day, so they are daily.
- **Default partitions** exist on every parent so a missing partition never fails a write. They should stay empty; `util.v_partition_health` reports both how far ahead partitions exist and whether any default partition has rows. Alert on either.
- **Co-partitioning** (citations and feedback with messages, responses with attempts) keeps cross-partition foreign keys valid and lets retention drop matching months together. `drop_order` in the registry drops referencing tables first.
- **Archive before drop.** Registry entries with `archive_before_drop = true` are only detached. An archiver job exports the detached table to Parquet in object storage, then drops it.
- **Hash for current state.** `concept_mastery` is updated in place and has no time dimension, so hash partitioning by learner keeps per-learner reads on one partition and spreads autovacuum work. To grow beyond 16, split one partition at a time: detach it, create two partitions with modulus 32 (remainders r and r + 16), and re-insert its rows. PostgreSQL allows mixed moduli as long as each divides the next.

## Scaling and analytics path

| Stage | Trigger | Action |
| --- | --- | --- |
| Now | MVP | Single Azure Flexible Server (General Purpose), PgBouncer in transaction mode, this schema |
| ~10k DAU | Read load from dashboards | Read replica for dashboards and analytics jobs; route `analytics.*` reads and report generation there |
| ~25k DAU | Analytics queries compete with OLTP | Logical replication / CDC (Debezium or Azure Data Factory) of evidence tables to a warehouse (Fabric, BigQuery, Snowflake, or ClickHouse); shorten `activity.events` retention in PostgreSQL |
| ~50k DAU | Leaderboard reads | Redis sorted sets for live ranks; PostgreSQL boards refreshed every 5 to 15 minutes |
| ~100k DAU+ | Write volume on chat and events | Move `activity.events` ingestion to a stream (Event Hubs / Kafka) that batches into PostgreSQL or straight to the warehouse; consider Citus with `user_id` as distribution column (already present on every learner table) |

Every learner-scoped table already carries `user_id`. That is what makes sharding by learner a realistic later step rather than a rewrite.

## Known gaps and decisions to revisit

- **Cross-midnight XP retries.** XP idempotency is unique per local day. A retry that crosses the learner's midnight could double-award. The service should also check `source_ref` before inserting.
- **Leaderboard entries at full scale.** Rewriting complete all-time boards hourly is fine to about a million learners. Beyond that, store only the top N in PostgreSQL and serve individual ranks from Redis.
- **Children's data.** Learners are 16 and over at launch (Security-Compliance.md §11.6). An under-16 consent and safeguarding model is not represented in the schema.
- **Crypto-shredding.** Security-Compliance.md §11.5 relies on crypto-shredded keys to make erased learners unrecoverable from backups. The schema has no per-learner keys; it relies on 35-day backup expiry plus erasure replay. One of the two documents needs to change.
- **SQLAlchemy models.** The DDL is the source of truth for PostgreSQL-specific features (partitioning, RLS, triggers, `ltree`). The ORM models still need updating to map onto these tables; see the migration strategy.
