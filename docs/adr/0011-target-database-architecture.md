# ADR 0011 — Target database architecture

- Status: Accepted 2026-10-13 (amends ADR 0003; extends ADR 0004)
- Date: 2026-10-13

## Context

The MVP schema is 25 tables in `public`, defined by SQLAlchemy and created by `create_all`. It is portable to SQLite so tests need no database server (ADR 0003). That fits the MVP. It does not fit the product in `Requirements.md` and `Admin.md`: three languages over one learner record, seven teaching styles, a governed knowledge library with versioning and approval, global and country leaderboards, weekly learner reports, and admin analytics over every learner.

At the planning target of 100,000 daily learners, chat alone adds about 3 million rows a day and product events about 20 million. Retention rules in `Security-Compliance.md` (24-month chat, 12-month code, 1–2 year audit) need deletion by time, and erasure has to reach every table, Qdrant, and blob storage.

## Problem

Choose a database design that scales with activity, enforces content and privacy rules, and feeds analytics, without losing the operational simplicity of one PostgreSQL system of record.

## Decision

Adopt the design in [`docs/database`](../database/README.md), with DDL in `backend/db/schema`:

- One PostgreSQL 16+ database, 12 domain schemas, 97 tables.
- Time-range partitioning for activity-driven tables (messages, events, answers, XP, audit) and hash partitioning for per-learner current state (`concept_mastery`). Retention is enforced by dropping partitions according to `util.partition_registry`.
- Integrity rules in the database: workflow transitions for curated content, acyclic prerequisites, idempotent XP, one published body per lesson, locale, and teaching style.
- Row-level security on learner-private data; the API connects as `mentor_app` and sets `app.current_user_id` per transaction.
- Trigger-based audit on governed tables, with personal identifiers redacted.
- Qdrant stays the vector index (ADR 0004). PostgreSQL adds collection and model lineage and a transactional outbox so deletes always reach Qdrant.
- `identity.erase_user()` implements erasure across schemas.

This amends ADR 0003 in three places:

| ADR 0003 said | This ADR proposes |
| --- | --- |
| Portable JSON so models run on SQLite | `jsonb`, `ltree`, `citext`, enums, partitioning: PostgreSQL only |
| CI does not need a database service; staging proves PostgreSQL SQL | Integration tests run on PostgreSQL in CI; `backend/db/verify.sh` builds the schema and runs smoke tests. SQLite stays for unit tests that never touch the database. |
| Pooling in SQLAlchemy until connection count is the bottleneck | PgBouncer (transaction mode) arrives with the role split, because `SET LOCAL` request context is what RLS and audit depend on |

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Keep the MVP schema and add tables as features land | No partitioning means retention becomes row-by-row deletes on the largest tables, and multilingual content would fork lesson rows and therefore learner progress |
| Separate databases per domain | Cross-domain joins (mastery with curriculum, citations with assets) become service calls. One database with schema boundaries keeps the option to split later. |
| Event-sourced learner state | Still not needed: ledgers (XP, mastery events, workflow transitions) give history where it matters, while current-state tables serve reads directly |
| Citus or a distributed SQL engine now | Operational cost before the load exists. Every learner table carries `user_id`, so Citus remains a later option. |
| pgvector instead of Qdrant | Same reasoning as ADR 0004; the lineage tables would also support a pgvector column if a small deployment wanted one |

## Trade-off analysis

PostgreSQL-only features remove the SQLite test path for anything touching the database. The cost is a database service in CI. The gain is that CI proves the SQL production runs, which ADR 0003 left to staging.

Partitioned tables need the partition key in every primary key and unique constraint. Foreign keys into them carry a timestamp column (`message_created_at`, `attempt_started_at`). That is extra ceremony in the ORM, in return for dropping a month of data in milliseconds.

Database-enforced rules (workflow, RLS, audit) mean some errors surface as SQL exceptions rather than domain errors. The API must map `check_violation` and `insufficient_privilege` to clear 4xx responses.

## Consequences

- The migration follows [migration-strategy.md](../database/migration-strategy.md): freeze revision 0001, expand, dual-write and backfill, switch reads, contract.
- `backend/app/models/entities.py` is rewritten to map onto the new schemas; partitioned tables are declared with `postgresql_partition_by`.
- `docs/Database.md` describes the current MVP schema until the migration completes.
- Retention changes go through `util.partition_registry`, `docs/database/data-retention.md`, and Security-Compliance.md §11.5 together.

## Future considerations

- Read replica for analytics jobs and dashboards at around 10,000 daily learners; CDC to a warehouse at around 25,000.
- Redis sorted sets for live leaderboard ranks once leaderboard reads show up in PostgreSQL CPU.
- Per-learner encryption keys if crypto-shredding of backups (Security-Compliance.md §11.5) is kept as a requirement.

## Acceptance — 2026-10-13

Accepted by the product owner. Migration follows [migration-strategy.md](../database/migration-strategy.md).

Phase 0 status: revision 0001 lists every table explicitly; `create_all` runs only on SQLite in development and test; CI runs the suite on PostgreSQL 16, runs `alembic check`, verifies `backend/db/schema` with `verify.sh`, and lints post-baseline migrations with squawk; every authenticated request sets the transaction-local `app.current_user_id`, `app.user_role`, `app.request_id`, and `app.client_ip` that the audit triggers and RLS policies read. Remaining phase 0 work is on the platform: the `mentor_owner`, `mentor_app`, `mentor_worker`, and `mentor_readonly` roles (the API must stop connecting as the owner, which bypasses RLS), the Flexible Server extension allow-list, and PgBouncer.

The target's 30-day cancellable deletion window (`pending_deletion`) replaces today's immediate erasure when the `identity` schema and the worker land. Immediate erasure already meets FR-ACC-008.

