# ADR 0017 — Bounded contexts and shared platform services

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13
- Amends: [ADR 0002](0002-fastapi-modular-monolith.md) (layers become per-module; one worker process is added)

## Context

ADR 0002 organises the backend by technical layer: `app/domain`, `app/models`, `app/repositories`, `app/services`, `app/agents`, `app/api`. Any service may query any table. That works for one learner product. With five apps, 23 shared services, and 14 new schemas, layer-only structure lets the gradebook read gamification tables directly and the tutor write mastery rows, and no seam is left to extract a service later.

ADR 0002 also has no queue and no worker. Ingestion is synchronous; the vector outbox in ADR 0011 needs a drain.

## Problem

Decide how the monolith is divided into modules, what each module may touch, how modules communicate, which processes run, and when a module may leave the monolith.

## Decision

The backend stays one deployable image and one database. It is divided into bounded-context modules, one per shared service in [docs/platform/README.md](../platform/README.md#shared-platform-services): `identity`, `authz`, `tenancy`, `tutor`, `knowledge`, `content`, `retrieval`, `assessment`, `learning`, `classroom`, `personalisation`, `gamification`, `analytics`, `reporting`, `notification`, `messaging`, `search`, `i18n`, `commerce`, `integration`, `ai_gateway`, `audit`, `config`.

**Layout.** Each module lives in `backend/app/modules/<module>/` with the ADR 0002 layers inside it (`domain/`, `models.py`, `repositories/`, `services/`, `api/`) and one public file, `interface.py`. Shared kernel code (ids, time, money, locale types, the authz engine) stays in `backend/app/core` and `backend/app/domain/authz`.

**Ownership rules.**

1. A module owns its schema or schemas. Only that module's repositories write to them.
2. Another module reads through the owner's `interface.py` (synchronous function call in the same transaction) or through a read model the consumer builds from events. No cross-schema writes; no cross-schema joins outside `analytics` and `reporting` read models.
3. Cross-module side effects that can be eventual go through domain events ([ADR 0018](0018-event-outbox.md)). Effects that must be atomic (grade a quiz, update mastery, award XP in one transaction, ADR 0002) are a call to the owner's interface inside the caller's transaction.
4. Modules never import another module's `models`, `repositories`, or `services`.

Schema ownership where the module and schema names differ:

| Module | Owns schemas |
| --- | --- |
| `content` | `curriculum` |
| `tutor` | `chat` |
| `retrieval` | `vector` |
| `gamification` | `game` |
| `analytics` | `activity`, `analytics` |
| `ai_gateway` | `platform.model_registry`, `platform.model_routes`, `platform.prompt_releases` |
| `config` | `platform.feature_flags`, `platform.flag_rules`, `platform.settings` |
| Shared kernel (`app.core.events`) | `events` (outbox and inbox are infrastructure every module writes through one API) |
| `i18n`, `search`, `reporting` | Their own schemas of the same name (`i18n`, `search`, `reporting`); `ref.languages` stays shared reference data |

**Processes.** One image, two commands: `api` (Uvicorn) and `worker` (`python -m app.worker`). The worker runs the outbox relay, event consumers, the vector sync drain, ingestion jobs, report rendering, leaderboard refresh, and scheduled jobs. Both run as Azure Container Apps from the same digest ([ADR 0006](0006-azure-container-apps.md)).

**Fitness tests.** `import-linter` contracts run in CI: each module may import only its own package, `app.core`, `app.domain.authz`, and other modules' `interface` modules. A schema-access test fails if a repository references a table outside its module's schemas.

**Extraction criteria.** A module leaves the monolith only when at least one holds, measured in production: it needs independent scaling (expected first: `ai_gateway` for model call concurrency, `retrieval` for embedding and search, `analytics` ingestion for event volume); it needs a different runtime or isolation (the code runner); or its release cadence is blocked by the rest. Its `interface.py` becomes an HTTP or message contract, and its schema moves with it.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Microservices per service now | 23 deployables, distributed transactions between grading and mastery, and an operations load the team cannot carry. ADR 0002's reasoning still holds. |
| Keep layer-only layout | No enforced boundary; extraction later means untangling every query. |
| Separate databases per module | Cross-module reads become network calls before there is load to justify them. Schemas give the same ownership signal inside one database. |
| Celery or Dramatiq for the worker | The outbox already persists work in PostgreSQL with `FOR UPDATE SKIP LOCKED`. Service Bus carries events. A third queue is not needed. |

## Trade-off analysis

Module boundaries add `interface.py` boilerplate and forbid convenient joins. Reads that span contexts (a gradebook row with learner name and mastery) cost a second query or a read model. That cost buys the ability to extract `ai_gateway` or `retrieval` without rewriting callers.

Keeping atomic calls in-transaction means some modules stay coupled at runtime (assessment, learning, gamification). That coupling is accepted because the alternative is eventual consistency between a grade and the XP it earns.

## Consequences

- R1 moves existing code into `identity`, `content`, `knowledge`, `retrieval`, `learning`, `tutor`, `gamification`, `analytics`, `audit`, and `commerce`. Other modules start empty and are created by the feature that needs them.
- The ADR 0002 rule "new teaching behaviour lands in `app/domain` first" becomes "in `modules/<module>/domain` first".
- The worker has its own health probe and scales separately (minimum one replica in production).

## Future considerations

- Move the code runner to its own Container App pool (ADR 0002 future consideration) as the first extraction.
- Per-module OpenAPI tags so [08-api-specification.md](../platform/08-api-specification.md) can be checked against ownership.
