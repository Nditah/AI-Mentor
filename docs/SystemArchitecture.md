# AI Mentor — System Architecture Document (SAD)

| Field | Value |
| --- | --- |
| Document | System Architecture Document |
| Product | AI Mentor |
| Version | 1.0 |
| Status | Approved for implementation |
| Date | 13 October 2026 |
| Owner | Principal Architect, Telixia |
| Related | [Requirements.md](Requirements.md), [Admin.md](Admin.md), [Architecture.md](Architecture.md), [Infrastructure.md](Infrastructure.md), [adr/README.md](adr/README.md), [README.md](../README.md) |

This document is the target architecture for AI Mentor on Azure. It also states where the current codebase (`backend/`, `frontend/`, `infrastructure/`) differs from that target and what has to change.

Current behaviour is [Architecture.md](Architecture.md). Decisions already implemented are in [adr/README.md](adr/README.md). The hosting layout that matches those decisions is [Infrastructure.md](Infrastructure.md): Vercel for the studio, one API container on Azure Container Apps. Section 17 and the decision table in [18.2](#182-architecture-decision-records) describe a later layout, including Next.js on Container Apps. That table does not replace ADR 0006.

## Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [Context Diagram](#3-context-diagram)
4. [Container Diagram](#4-container-diagram)
5. [Component Diagram](#5-component-diagram)
6. [Sequence Diagrams](#6-sequence-diagrams)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [AI Services Architecture](#8-ai-services-architecture)
9. [Knowledge Management Architecture](#9-knowledge-management-architecture)
10. [Gamification Architecture](#10-gamification-architecture)
11. [RAG Architecture](#11-rag-architecture)
12. [API Gateway Architecture](#12-api-gateway-architecture)
13. [Security Architecture](#13-security-architecture)
14. [Scalability Strategy](#14-scalability-strategy)
15. [Monitoring Architecture](#15-monitoring-architecture)
16. [Disaster Recovery Architecture](#16-disaster-recovery-architecture)
17. [Deployment Architecture](#17-deployment-architecture)
18. [Appendices](#18-appendices)

---

## 1. Architecture Overview

### 1.1 Purpose

AI Mentor is a personalised, gamified, multilingual learning platform for AI, ML, RL, robotics, and LLM engineering. A Socratic tutor teaches from a curated knowledge base. Learners practise with quizzes and a coding lab. Progress is tracked as concept mastery and rewarded with XP, levels, streaks, badges, and leaderboards. Administrators curate, version, and publish the content that the tutor is allowed to use.

### 1.2 Scope

In scope: the learner web app, the admin portal, the API, AI orchestration, retrieval, gamification, billing integration, and Azure infrastructure, observability, and disaster recovery.

Out of scope for v1, but the design leaves room for them: native mobile apps, voice tutoring, animated avatars, notebooks, and robotics simulators. Section 8.7 covers the extension points.

### 1.3 Quality attribute targets

| Attribute | Target | Measured by |
| --- | --- | --- |
| Tutor time to first token | p95 < 1.5 s | `ai.ttft_ms` histogram |
| Non-AI API latency | p95 < 300 ms, p99 < 800 ms | App Insights requests |
| Availability (learner flows) | 99.9% monthly | Front Door synthetic probes |
| Data loss on regional failure | RPO ≤ 15 min (PostgreSQL), ≤ 24 h (vectors, rebuildable) | DR drills |
| Recovery time | RTO ≤ 1 h primary-region loss, ≤ 15 min zonal loss | DR drills |
| Design load | 50,000 MAU, 5,000 concurrent, 200 tutor turns/s peak | Load tests |
| Grounded answers | ≥ 90% of curated-topic answers cite a published source | Langfuse eval |
| Security | No critical or high findings open > 14 days | Defender, Trivy, pip-audit |

### 1.4 Solution summary

```mermaid
flowchart LR
    U["Learner / Instructor / Admin<br/>browser"] --> FD["Azure Front Door Premium<br/>WAF, TLS, CDN"]
    FD -->|"/*"| WEB["Next.js web<br/>Container App"]
    FD -->|"/api/*"| API["FastAPI API<br/>Container App"]
    WEB -.->|"server components"| API
    API --> PG[("PostgreSQL<br/>Flexible Server")]
    API --> RD[("Azure Managed Redis")]
    API --> QD[("Qdrant")]
    API --> BLOB[("Blob Storage")]
    API --> SB[["Service Bus"]]
    SB --> WRK["Worker<br/>Container App"]
    WRK --> PG
    WRK --> QD
    WRK --> BLOB
    API --> LLM["Azure OpenAI<br/>+ fallback providers"]
    WRK --> LLM
    API --> SBX["Code sandbox<br/>ACA dynamic sessions"]
    API -.-> CLERK["Clerk"]
    API -.-> STRIPE["Stripe"]
```

### 1.5 Key architecture decisions

The full ADR list is in Appendix 18.2. Summary:

| # | Decision | Reason |
| --- | --- | --- |
| ADR-01 | Modular monolith API (FastAPI) plus one async worker, not microservices | Small team. Domain modules are already isolated in `backend/app/domain`. Split later along module seams if needed. |
| ADR-02 | Azure Container Apps for web, API, worker, and jobs | Managed scale-to-N with KEDA, revisions for blue/green, VNet integration, and no cluster to operate. |
| ADR-03 | Frontend moves from Vercel to Azure Container Apps | One cloud, one network boundary, same-origin `/api` routing through Front Door, so no CORS in production. |
| ADR-04 | PostgreSQL is the system of record. Qdrant holds only derived vectors. | Qdrant can be rebuilt from Blob and PostgreSQL. This keeps DR simple. |
| ADR-05 | Qdrant Cloud on Azure in the same region (managed) | Avoids operating a stateful vector cluster. Self-hosting on AKS is the fallback (ADR-05b). |
| ADR-06 | Azure OpenAI is the primary model provider. OpenAI, Anthropic, and Gemini are fallbacks behind the existing `ProviderRouter`. | Data residency, private networking, and quota under one contract. Fallback keeps the tutor available. |
| ADR-07 | Azure Container Apps dynamic sessions for learner code | Hyper-V isolated, no egress, per-session lifetime. The current subprocess runner is not a security boundary. |
| ADR-08 | Service Bus for durable jobs, Redis for rate limits, cache, and leaderboards | Ingestion and content generation must survive restarts. Leaderboards need sorted sets. |
| ADR-09 | Server-Sent Events for tutor streaming | One-way token stream, works through Front Door, and needs no WebSocket infrastructure. |
| ADR-10 | Clerk for identity. PostgreSQL `users` mirrors Clerk via webhook and JIT upsert. | Already integrated in `app/core/security.py` and `/webhooks/clerk`. |

### 1.6 Current baseline and required changes

These are the gaps between the current codebase and this architecture. Each row is a work item. Appendix 18.1 orders them.

| Area | Current state (code) | Required change | Section |
| --- | --- | --- | --- |
| Vector store | `engine.ingest` records `qdrant_point_id` but never upserts to Qdrant. `engine.analyze` re-embeds every chunk per request. | Add a `VectorStore` port with a Qdrant adapter. Embed once on ingest. Search Qdrant on analyze and tutor turns. | 11 |
| Ingestion | Synchronous inside the request, 10 MB limit, text formats only | Upload to Blob, enqueue a job, parse in the worker, report status | 9, 11 |
| Rate limiting | `SlidingWindowLimiter` is in-process and keyed by `request.client.host` | Redis token bucket keyed by user ID, with `X-Azure-ClientIP` for anonymous requests. Behind Front Door every user currently shares one IP. | 12 |
| Streaming | `POST /chat` returns the whole reply | Add `POST /chat/stream` (SSE) | 6.3, 12 |
| Concurrency | Handlers are `def` with sync SQLAlchemy and sync LLM SDKs. These saturate the 40-thread pool. | Make the AI paths `async def` with async SDK clients. DB stays sync in the threadpool until profiling says otherwise. | 14 |
| Sandbox | `subprocess.run` with an AST allow-list, 3 s timeout | Keep the AST check as the first filter. Execute in ACA dynamic sessions. | 13.8 |
| Frontend auth | `@clerk/nextjs` is installed but unused. `lib/api.ts` sends only `X-Dev-User-Id`. | Add `ClerkProvider` and `middleware.ts`, and attach `Authorization: Bearer` from `getToken()` | 13.2 |
| JWT checks | `verify_aud: False`, no `azp` check | Validate `azp` against allowed origins, with 5 s leeway | 13.2 |
| Migrations | API container runs `alembic upgrade head` on start | Separate ACA Job runs migrations before the revision shift | 17.6 |
| Gamification | Leaderboard is `ORDER BY xp` on `users`. No country or friends. | Add `country_code`, friendships, Redis ZSETs, seasons, daily challenges | 10 |
| Knowledge admin | Curriculum is code (`domain/catalog.py`). No asset, version, or workflow tables. | Add knowledge tables, workflow, and admin API. The catalog becomes the seed. | 9 |
| i18n | English only | `next-intl` UI and translation tables keyed by concept slug | 8.6, 9.6 |
| Hosting | README says Vercel plus App Service | Container Apps for all workloads | 17 |

---

## 2. Architecture Principles

| # | Principle | Rationale | Implication |
| --- | --- | --- | --- |
| P1 | **Grounded before generative** | Learners must be able to trust the tutor. | Retrieval runs before generation on curated topics. Answers cite sources or say they cannot. `domain/grounding.grounded()` gates critique output. |
| P2 | **Teaching logic lives in the domain** | The pedagogy has to be testable without HTTP or a model. | `backend/app/domain` stays pure: no I/O, ≥ 90% coverage. Routers only parse and delegate. |
| P3 | **Models are replaceable** | Providers, prices, and quality change monthly. | All model calls go through `ProviderRouter`. Prompts are versioned files. No provider SDK is imported outside `services/llm*`. |
| P4 | **Degrade, don't fail** | A model outage must not take the product down. | Provider fallback chain, then authored curriculum. Quizzes and grading never depend on a live model. |
| P5 | **System of record is PostgreSQL** | One authoritative store simplifies consistency and DR. | Redis and Qdrant are derived and rebuildable. Rebuild jobs exist and are tested. |
| P6 | **Untrusted input stays fenced** | Prompt injection is the main AI threat. | User text, uploads, and retrieved chunks are wrapped with `fence_untrusted`. Tools cannot act on instructions inside fenced content. |
| P7 | **Least privilege everywhere** | Limits blast radius. | Managed identities, private endpoints, per-route role checks, row ownership checks in repositories. |
| P8 | **Async for anything slow or retryable** | Keeps request latency predictable. | Ingestion, content generation, reports, and re-indexing run as jobs. The API returns `202` with a job ID. |
| P9 | **Idempotent writes for rewards and money** | Retries and webhooks repeat. | XP events, Stripe and Clerk webhooks, and job handlers carry idempotency keys with unique constraints. |
| P10 | **Observable by default** | AI systems fail quietly. | Every request has a trace. Every model call has a Langfuse generation with prompt version, tokens, cost, and citations. |
| P11 | **Infrastructure as code, immutable images** | Repeatable environments. | Bicep for Azure. One image per commit, promoted across environments. No portal changes in production. |
| P12 | **Language-independent progress** | Switching language must not reset progress. | Mastery, XP, and progress are keyed by concept and lesson slugs. Content has per-locale translations. |

---

## 3. Context Diagram

```mermaid
flowchart TB
    subgraph People
        L["Learner<br/>student, professional, researcher"]
        I["Instructor / SME<br/>authors and reviews content"]
        A["Administrator<br/>users, taxonomy, publishing, analytics"]
    end

    AIM(["AI Mentor platform"])

    subgraph External["External systems"]
        CLERK["Clerk<br/>identity, sessions, social login"]
        STRIPE["Stripe<br/>subscriptions, checkout"]
        AOAI["Azure OpenAI<br/>chat, embeddings, transcription"]
        ALT["OpenAI / Anthropic / Gemini<br/>fallback models"]
        CS["Azure AI Content Safety<br/>prompt shields, harm filters"]
        SPEECH["Azure AI Speech and Translator<br/>post-MVP voice, translation drafts"]
        LF["Langfuse<br/>LLM traces and evals"]
        MAIL["Email provider<br/>weekly reports"]
        SRC["Public sources<br/>URLs, YouTube, GitHub, arXiv"]
    end

    L -->|"learn, practise, upload papers"| AIM
    I -->|"author, review, generate content"| AIM
    A -->|"govern users and content"| AIM

    AIM -->|"verify JWT, receive user webhooks"| CLERK
    AIM -->|"checkout, receive billing webhooks"| STRIPE
    AIM -->|"completions, embeddings"| AOAI
    AIM -->|"fallback completions"| ALT
    AIM -->|"screen prompts and outputs"| CS
    AIM -->|"TTS, translation"| SPEECH
    AIM -->|"traces, scores"| LF
    AIM -->|"send reports"| MAIL
    AIM -->|"fetch admin-approved sources"| SRC
```

| Actor or system | Interaction | Protocol | Trust |
| --- | --- | --- | --- |
| Learner | Web app | HTTPS through Front Door | Untrusted |
| Instructor, Admin | Admin portal (same Next.js app, `/admin`) | HTTPS through Front Door | Authenticated, role-gated |
| Clerk | JWKS fetch, Svix-signed webhooks | HTTPS | Verified by signature |
| Stripe | Checkout API, signed webhooks | HTTPS | Verified by signature |
| Azure OpenAI | Private endpoint, managed identity | HTTPS | Trusted processor |
| Fallback models | Public API with key | HTTPS | Processor. No PII is sent (section 13.6). |
| Langfuse | Trace export | HTTPS | Processor. Prompts are redacted. |

---

## 4. Container Diagram

```mermaid
flowchart TB
    subgraph Client["Client"]
        BR["Browser<br/>React 19, Tailwind, shadcn/ui"]
    end

    subgraph Edge["Azure edge"]
        FD["Front Door Premium<br/>WAF policy, routing, caching"]
    end

    subgraph ACA["Container Apps environment (VNet-integrated)"]
        WEB["web<br/>Next.js 15 standalone<br/>SSR, RSC, Clerk middleware"]
        API["api<br/>FastAPI, Uvicorn<br/>REST + SSE /api/v1"]
        WRK["worker<br/>Python, Service Bus consumer<br/>ingestion, generation, reports"]
        JOBS["jobs<br/>ACA scheduled jobs<br/>daily challenges, leaderboard rebuild, migrations"]
        SBX["sandbox pool<br/>ACA dynamic sessions<br/>Python code interpreter"]
    end

    subgraph Data["Data services (private endpoints)"]
        PG[("PostgreSQL 16<br/>Flexible Server, zone-redundant HA")]
        RD[("Azure Managed Redis<br/>cache, limits, leaderboards")]
        BLOB[("Blob Storage<br/>raw uploads, asset versions, snapshots")]
        SB[["Service Bus<br/>queues: ingest, generate, reports<br/>topic: domain-events"]]
        KV["Key Vault"]
    end

    QD[("Qdrant Cloud on Azure<br/>kb_curated, user_docs")]

    subgraph AI["AI services"]
        AOAI["Azure OpenAI"]
        CS["Content Safety"]
    end

    BR -->|"HTTPS"| FD
    FD -->|"/*"| WEB
    FD -->|"/api/*, /webhooks/*"| API
    WEB -->|"internal HTTPS, Bearer JWT"| API
    API --> PG
    API --> RD
    API --> BLOB
    API -->|"enqueue"| SB
    API --> QD
    API --> AOAI
    API --> CS
    API -->|"execute code"| SBX
    SB --> WRK
    WRK --> PG
    WRK --> QD
    WRK --> BLOB
    WRK --> AOAI
    WRK --> RD
    JOBS --> PG
    JOBS --> RD
    JOBS --> SB
    API -.->|"secrets via managed identity"| KV
    WRK -.-> KV
```

### 4.1 Container catalogue

| Container | Technology | Azure service | Responsibility | State | Scale |
| --- | --- | --- | --- | --- | --- |
| `web` | Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, TanStack Query, Zustand | Container Apps | Learner UI, admin portal, SSR, i18n, Clerk session | Stateless | 2–20 replicas, HTTP concurrency |
| `api` | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2 | Container Apps | Auth, gateway policies, domain orchestration, SSE | Stateless | 2–40 replicas, HTTP concurrency |
| `worker` | Python 3.12, same image as `api`, `python -m app.worker` | Container Apps | Ingestion, embedding, AI content generation, reports, outbox relay | Stateless | 0–20 replicas, queue depth |
| `jobs` | Same image, `python -m app.jobs <name>` | Container Apps Jobs | Cron and one-off tasks | Stateless | Scheduled |
| `sandbox` | Python code interpreter session pool | ACA dynamic sessions | Run learner code with no egress | Ephemeral | Pool-managed |
| PostgreSQL | v16 with `pgcrypto`, `ltree`, `pg_trgm` | Flexible Server | System of record | Durable | Vertical, plus read replica |
| Redis | Redis 7 | Azure Managed Redis | Rate limits, cache, leaderboards, SSE cancel flags | Rebuildable | Vertical, clustered |
| Qdrant | v1.13+ | Qdrant Cloud (Azure region) | Dense and sparse vectors | Rebuildable | Shards and replicas |
| Blob | Hot tier with versioning | Storage Account (GZRS) | Original files, extracted text, Qdrant snapshots | Durable | Elastic |
| Service Bus | Standard (MVP), Premium (scale) | Service Bus | Durable jobs, domain events | Durable | Messaging units |

---

## 5. Component Diagram

### 5.1 API components

The API is a layered modular monolith. Arrows point in the direction of dependency. The domain layer depends on nothing.

```mermaid
flowchart TB
    subgraph Gateway["Gateway layer: app/middleware, app/core"]
        MW1["RequestContext<br/>request_id, trace"]
        MW2["SecurityHeaders"]
        MW3["Auth: Clerk JWT verify"]
        MW4["RateLimit: Redis token bucket"]
        MW5["Entitlements: plan tier"]
    end

    subgraph Routers["API layer: app/api/v1"]
        R1["me, onboarding, preferences"]
        R2["tutor: chat, chat/stream, conversations"]
        R3["practice: quiz, lab, flashcards"]
        R4["study: paths, graph, plans, progress, dashboard"]
        R5["gamification: leaderboard, challenges, badges"]
        R6["research: documents, analyze"]
        R7["admin: users, knowledge, taxonomy, workflow, analytics"]
        R8["billing and webhooks"]
    end

    subgraph Services["Application layer: app/services"]
        S1["MentorEngine (facade)"]
        S2["TutorService"]
        S3["AssessmentService"]
        S4["LearningService"]
        S5["GamificationService"]
        S6["KnowledgeService"]
        S7["RetrievalService"]
        S8["ResearchService"]
        S9["LabService"]
        S10["BillingService"]
    end

    subgraph Agents["AI layer: app/agents, app/services/llm"]
        A1["Orchestrator: intent routing"]
        A2["Tutor, Quiz, Planner, Coding, Research, Career agents"]
        A3["PromptRegistry"]
        A4["Guardrails"]
        A5["ProviderRouter"]
    end

    subgraph Domain["Domain layer: app/domain (pure)"]
        D1["catalog, graph"]
        D2["socratic, intent"]
        D3["mastery, scheduling, planner"]
        D4["grading, code_review, sandbox policy"]
        D5["gamification rules"]
        D6["chunking, grounding, prompt_guard"]
        D7["workflow state machine"]
    end

    subgraph Adapters["Infrastructure layer: app/repositories, app/adapters"]
        P1["SqlRepository"]
        P2["QdrantVectorStore"]
        P3["RedisCache, RedisLeaderboard"]
        P4["BlobStore"]
        P5["ServiceBusPublisher"]
        P6["SandboxClient"]
        P7["ClerkClient, StripeClient"]
    end

    Gateway --> Routers --> Services
    Services --> Agents
    Services --> Domain
    Agents --> Domain
    Services --> Adapters
    Agents --> Adapters
```

### 5.2 Target backend package layout

This extends the current tree. Existing modules keep their names.

```text
backend/app/
├── main.py                    # create_app(), middleware order (section 12.4)
├── worker.py                  # Service Bus consumer entrypoint
├── jobs/                      # ACA Job entrypoints: daily_challenges, leaderboard_rebuild, migrate, reindex
├── api/
│   ├── deps.py
│   └── v1/                    # split router.py by area: tutor.py, practice.py, admin_knowledge.py ...
├── middleware/                # request_context, security_headers, rate_limit (Redis), entitlements
├── core/                      # config, database, security (Clerk), telemetry, redis, errors (problem+json)
├── domain/                    # unchanged rule: no I/O
│   ├── workflow.py            # NEW: content state machine
│   ├── leaderboard.py         # NEW: period keys, percentile
│   └── difficulty.py          # NEW: adaptive difficulty policy
├── agents/                    # orchestrator + agent classes
├── prompts/                   # versioned *.md prompts, front-matter: id, version, model_tier
├── services/
│   ├── engine.py              # facade, shrinks as services are extracted
│   ├── llm.py                 # ProviderRouter (+ AzureOpenAI, streaming, circuit breaker)
│   ├── retrieval.py           # NEW: hybrid search, rerank, packing
│   ├── ingestion.py           # NEW: parse → chunk → embed → upsert
│   ├── gamification.py        # NEW: XP ledger, badges, leaderboards
│   └── knowledge.py           # NEW: assets, versions, workflow
├── adapters/                  # NEW: qdrant.py, blob.py, servicebus.py, sandbox_sessions.py, content_safety.py
├── repositories/sql.py
└── models/entities.py         # + knowledge, gamification, jobs, outbox tables
```

### 5.3 Frontend components

```mermaid
flowchart TB
    subgraph AppRouter["frontend/app"]
        MK["(marketing)<br/>landing, pricing"]
        AU["(auth)<br/>Clerk sign-in, sign-up"]
        ON["onboarding<br/>assessment wizard"]
        ST["(studio)<br/>dashboard, tutor, paths, lab, quiz, flashcards, research, leaderboard"]
        AD["admin<br/>library, taxonomy, curriculum builder, review queue, analytics"]
    end

    subgraph Shared["frontend/components, lib, stores"]
        UI["components/ui<br/>shadcn primitives"]
        MD["markdown-view<br/>remark-math, KaTeX, Mermaid"]
        CHAT["tutor/ChatStream<br/>SSE reader, citations panel"]
        API["lib/api.ts<br/>typed client, Bearer token"]
        GEN["lib/api-types.ts<br/>generated from OpenAPI"]
        Q["TanStack Query<br/>server state"]
        Z["Zustand<br/>UI state: tutor style, locale"]
        I18N["next-intl<br/>en, fr, es messages"]
    end

    MW["middleware.ts<br/>clerkMiddleware, locale, role gate for /admin"]

    MW --> AppRouter
    ST --> CHAT
    ST --> Q
    AD --> Q
    Q --> API
    CHAT --> API
    API --> GEN
    AppRouter --> UI
    AppRouter --> MD
    AppRouter --> I18N
    AppRouter --> Z
```

Frontend rules:

- Server Components fetch with `auth().getToken()` and call the API over the internal Container Apps FQDN. Client components call `/api/v1/*` on the same origin.
- `lib/api-types.ts` is generated with `openapi-typescript` from `/openapi.json` in CI. A schema change that breaks the client fails the build.
- `/admin/**` is gated in `middleware.ts` by the `role` claim. The API enforces the same check, so the UI gate is only convenience.
- Mermaid and KaTeX render lesson content. Rendered HTML is sanitised with `rehype-sanitize`.

---

## 6. Sequence Diagrams

### 6.1 Sign-up and user synchronisation

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant W as Next.js web
    participant C as Clerk
    participant API as FastAPI
    participant DB as PostgreSQL

    L->>W: Open /sign-up
    W->>C: Clerk hosted components
    L->>C: Email or Google sign-up
    C-->>W: Session cookie (__session)
    par Webhook path
        C->>API: POST /webhooks/clerk user.created (Svix-signed)
        API->>API: Verify svix-id, timestamp, signature
        API->>DB: Upsert users by clerk_id (idempotent)
        API-->>C: 200 received
    and First request path
        W->>W: getToken() returns short-lived JWT
        W->>API: GET /api/v1/me Bearer JWT
        API->>C: JWKS (cached 10 min)
        API->>API: Verify RS256, iss, azp, exp
        API->>DB: Upsert users by clerk_id (JIT)
        API-->>W: profile, onboarding_complete=false
    end
    W->>L: Redirect to /onboarding
```

Both paths upsert by `clerk_id`, so whichever arrives first creates the row. The JWT never sets the role on its own. `role` comes from Clerk `public_metadata`, which only the backend or an admin can write.

### 6.2 Onboarding assessment

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant W as web
    participant API as api
    participant D as domain (mastery, planner)
    participant DB as PostgreSQL

    W->>API: GET /api/v1/onboarding/questions?locale=fr
    API-->>W: Profile questions + 10 adaptive diagnostic items
    loop Each diagnostic item
        L->>W: Answer
        W->>API: POST /api/v1/onboarding/answer
        API->>D: next_item(theta, answered)
        D-->>API: Next item at adjusted difficulty
        API-->>W: Next item or done
    end
    W->>API: POST /api/v1/onboarding/complete (profile fields)
    API->>D: initial_mastery(answers), persona(profile), build_study_plan(goal, mastery)
    API->>DB: learner_profiles, concept_mastery seed, study_plans, preferences
    API-->>W: persona, starting path, first lesson
```

### 6.3 Streaming tutor turn with RAG

This is the critical path for the p95 time-to-first-token target of 1.5 s.

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant W as web (ChatStream)
    participant FD as Front Door
    participant API as api
    participant RL as Redis
    participant G as Guardrails
    participant R as RetrievalService
    participant Q as Qdrant
    participant DB as PostgreSQL
    participant LLM as ProviderRouter

    L->>W: Type message
    W->>FD: POST /api/v1/chat/stream Accept text/event-stream
    FD->>API: Forward (origin timeout 240 s)
    API->>API: Verify JWT
    API->>RL: Token bucket ai:user_id
    alt Over limit
        API-->>W: 429 problem+json, Retry-After
    end
    API->>G: screen_user_input + Content Safety prompt shield
    G-->>API: allowed, flags
    API->>DB: Load conversation (last 20 turns), learner profile, preferences
    API->>API: socratic.build_turn() returns concept, stage, mode
    par Retrieval
        API->>R: retrieve(query, concept, locale, depth)
        R->>Q: Hybrid query on kb_curated, filter status=published
        Q-->>R: Top 30 candidates
        R->>R: Rerank to top 6, expand with prerequisites from concept graph
        R-->>API: Context chunks + citation labels
    and Personalisation
        API->>DB: Mastery for concept and prerequisites
    end
    API-->>W: event meta (conversation_id, concept, stage)
    API->>LLM: stream(system prompt v, fenced context, history, message)
    loop Tokens
        LLM-->>API: delta
        API-->>W: event token
    end
    API->>G: Output check (grounding, harm)
    API-->>W: event citations (source ids, titles, urls)
    API->>DB: Persist user + assistant messages, retrieval log
    API->>DB: Grant practice XP (idempotent)
    API-->>W: event done (usage, message_id)
    Note over API,LLM: Provider failure mid-stream: retry next provider<br/>if no tokens were sent, else event error and partial message is saved
```

SSE event contract:

```text
event: meta        data: {"conversation_id":"…","concept_slug":"q-learning","stage":"probe","mode":"socratic"}
event: token       data: {"t":"The Bellman "}
event: citations   data: [{"label":"[1]","asset_id":"…","version":3,"title":"Intro to RL","url":"/library/…"}]
event: done        data: {"message_id":"…","tokens_in":1830,"tokens_out":412,"grounded":true}
event: error       data: {"type":"provider_unavailable","detail":"…"}
```

The client uses `fetch()` with a `ReadableStream` reader, not `EventSource`, because `EventSource` cannot send an `Authorization` header. If the learner presses stop, the client aborts the fetch. The API sees the disconnect, cancels the provider stream, and saves the partial reply.

### 6.4 Quiz generation, grading, mastery, and XP

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant API as api
    participant D as domain
    participant DB as PostgreSQL
    participant LLM as QuizAgent
    participant GS as GamificationService
    participant RD as Redis

    L->>API: POST /api/v1/quiz/generate (concept_slug, difficulty=auto)
    API->>DB: Mastery for concept
    API->>D: difficulty.select(mastery, learner_depth_cap)
    API->>DB: Authored and published items for concept, difficulty, locale
    alt Not enough items
        API->>LLM: Generate items from published chunks (JSON schema)
        LLM-->>API: Items + source citations
        API->>D: Validate schema and answer key
        API->>DB: Store as generated_unreviewed, scoped to this quiz only
    end
    API->>DB: quizzes, questions (answer_key never returned)
    API-->>L: Questions without answers
    L->>API: POST /api/v1/quiz/{id}/grade answers
    API->>D: grading.grade(question, response) per item
    API->>DB: quiz_results
    API->>D: mastery.update(prior, outcomes)
    API->>DB: concept_mastery upsert
    API->>GS: award(user, kind=quiz, source_id=quiz_id, amount=quiz_xp(ratio))
    GS->>DB: INSERT xp_events ON CONFLICT DO NOTHING, update users.xp, level, streak, outbox
    GS->>RD: ZINCRBY leaderboard keys (after commit)
    API-->>L: Score, feedback, explanations, xp_awarded, new badges
```

### 6.5 Coding lab execution

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant API as api
    participant P as domain.sandbox
    participant S as ACA dynamic session
    participant CA as CodingAgent
    participant DB as PostgreSQL

    L->>API: POST /api/v1/lab/run (code, project_slug)
    API->>P: validate_source(code) AST allow-list
    alt Policy violation
        API-->>L: status=rejected, reason
    end
    API->>S: POST /code/execute identifier=user_id, timeout 10 s
    Note over S: Hyper-V isolated, no network egress,<br/>session destroyed after 5 min idle
    S-->>API: stdout, stderr, exit status
    API->>API: Compare stdout to project expected output
    opt Review requested
        API->>CA: review(fenced code, fenced output, rubric)
        CA-->>API: Review markdown
    end
    API->>DB: code_submissions
    API->>API: GamificationService.award(kind=code_pass) when passing
    API-->>L: Output, pass or fail, review
```

### 6.6 Admin content ingestion and publishing

```mermaid
sequenceDiagram
    autonumber
    actor A as Instructor
    participant W as web /admin
    participant API as api
    participant BL as Blob Storage
    participant SB as Service Bus
    participant WK as worker
    participant DB as PostgreSQL
    participant Q as Qdrant
    participant LLM as Azure OpenAI
    actor R as Reviewer

    A->>W: Upload file + metadata
    W->>API: POST /api/v1/admin/knowledge/assets (metadata)
    API->>DB: knowledge_assets, asset_versions v1 status=draft
    API->>BL: Create user-delegation SAS (write-only, 15 min)
    API-->>W: version_id, upload_url
    W->>BL: PUT file directly
    W->>API: POST .../versions/{id}/uploaded
    API->>DB: ingestion_jobs status=queued
    API->>SB: ingest {version_id, idempotency_key}
    API-->>W: 202 job_id
    SB->>WK: Deliver message
    WK->>BL: Download original, Defender malware verdict
    WK->>WK: Parse, extract metadata, structure-aware chunking
    WK->>LLM: Embeddings in batches of 64
    WK->>Q: Upsert points status=draft
    WK->>DB: chunks, embeddings, concept links, job=succeeded
    A->>API: POST .../versions/{id}/transition to=review
    R->>API: POST .../versions/{id}/transition to=approved (comment)
    R->>API: POST .../versions/{id}/transition to=published
    API->>DB: Mark previous published version superseded
    API->>SB: reindex-status {version_id, previous_version_id}
    WK->>Q: set_payload status=published (new), status=superseded (old)
    WK->>DB: Audit log
```

### 6.7 Learner paper upload and analysis

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant API as api
    participant BL as Blob
    participant SB as Service Bus
    participant WK as worker
    participant Q as Qdrant user_docs
    participant RA as ResearchAgent

    L->>API: POST /api/v1/research/documents (multipart, max 25 MB, Research tier)
    API->>BL: Store under users/{user_id}/docs/{doc_id}
    API->>SB: ingest-user-doc
    API-->>L: 202 status=processing
    SB->>WK: Deliver
    WK->>Q: Upsert chunks with owner_id=user_id (tenant key)
    WK->>WK: Set research_documents.status=ready
    L->>API: POST /api/v1/research/analyze (document_id, question)
    API->>API: Ownership check document.user_id == user.id
    API->>Q: Search user_docs filter owner_id and document_id
    API->>RA: critique(fenced excerpts with labels)
    RA-->>API: summary, critique, gaps, future_work
    API->>API: grounded() drops any field without a citation
    API-->>L: Analysis + excerpts + equations
```

### 6.8 Daily challenge generation

```mermaid
sequenceDiagram
    autonumber
    participant CRON as daily-challenges job (cron 5 0 * * *)
    participant DB as PostgreSQL
    participant LLM as Azure OpenAI
    participant RD as Redis

    CRON->>DB: Load challenge templates, concept graph, last 30 days of challenges
    loop Each type: quiz, coding, debugging, research, robotics
        CRON->>CRON: Pick concept (rotation + popularity, no repeats in 14 days)
        CRON->>LLM: Generate from published chunks (JSON schema)
        CRON->>CRON: Validate, run coding solution in sandbox
        CRON->>DB: daily_challenges (date, type, locale variants, status=ready)
    end
    CRON->>RD: Cache challenge:YYYY-MM-DD for 26 h
    Note over CRON,DB: On failure, fall back to the pre-authored reserve pool and alert
```

### 6.9 Subscription checkout

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant API as api
    participant S as Stripe
    participant DB as PostgreSQL
    participant C as Clerk

    L->>API: POST /api/v1/billing/checkout tier=pro
    API->>API: Validate return URLs are same-origin
    API->>S: checkout.Session.create(metadata.clerk_id)
    API-->>L: Checkout URL
    L->>S: Pay
    S->>API: POST /webhooks/stripe checkout.session.completed
    API->>API: Verify signature, dedupe on event.id
    API->>DB: users.subscription_status=active, stripe_customer_id, plan=pro
    API->>C: Update public_metadata.plan=pro
    API-->>S: 200
```

---

## 7. Data Flow Diagrams

### 7.1 Level 0

```mermaid
flowchart LR
    L(["Learner"]) -->|"messages, answers, code, papers"| P0(("AI Mentor"))
    P0 -->|"explanations, feedback, progress, rewards"| L
    AD(["Admin / Instructor"]) -->|"content, taxonomy, decisions"| P0
    P0 -->|"analytics, review queue"| AD
    P0 -->|"prompts with fenced context"| LLM(["Model providers"])
    LLM -->|"completions, embeddings"| P0
    P0 <-->|"identity"| CL(["Clerk"])
    P0 <-->|"billing"| ST(["Stripe"])
```

### 7.2 Level 1

```mermaid
flowchart TB
    L(["Learner"])
    AD(["Admin"])
    LLM(["Model providers"])

    P1(("1.0 Authenticate<br/>and authorise"))
    P2(("2.0 Tutor<br/>conversation"))
    P3(("3.0 Assess<br/>quiz, lab"))
    P4(("4.0 Track progress<br/>mastery, plans"))
    P5(("5.0 Reward<br/>XP, badges, ranks"))
    P6(("6.0 Ingest<br/>knowledge"))
    P7(("7.0 Retrieve<br/>context"))
    P8(("8.0 Analytics<br/>and reports"))

    D1[("D1 users, profiles")]
    D2[("D2 conversations, messages")]
    D3[("D3 curriculum, knowledge assets")]
    D4[("D4 mastery, progress, results")]
    D5[("D5 xp_events, achievements")]
    D6[("D6 Qdrant vectors")]
    D7[("D7 Blob originals")]
    D8[("D8 Redis leaderboards")]

    L -->|"JWT"| P1 --> D1
    L -->|"message"| P2
    P2 -->|"query"| P7
    P7 --> D6
    P7 -->|"chunks"| P2
    P2 -->|"fenced prompt"| LLM
    LLM -->|"reply"| P2
    P2 --> D2
    P2 -->|"reply + citations"| L
    L -->|"answers, code"| P3
    P3 --> D3
    P3 -->|"outcomes"| P4 --> D4
    P3 -->|"reward events"| P5
    P4 -->|"lesson events"| P5
    P5 --> D5
    P5 --> D8
    P5 -->|"rank, badges"| L
    AD -->|"files, metadata"| P6
    P6 --> D7
    P6 --> D3
    P6 -->|"chunks"| LLM
    P6 --> D6
    D4 --> P8
    D5 --> P8
    D2 --> P8
    P8 -->|"dashboards"| AD
    P8 -->|"weekly report"| L
```

### 7.3 Data classification

| Class | Examples | Stores | Controls |
| --- | --- | --- | --- |
| C1 Public | Published lessons, taxonomy, leaderboard display names | PostgreSQL, Qdrant, CDN | Integrity only |
| C2 Internal | Draft content, analytics aggregates, prompts | PostgreSQL, Blob, Qdrant | Role-gated |
| C3 Personal | Email, name, country, learning profile, mastery, XP, conversations | PostgreSQL, Redis (IDs only) | Ownership checks, encryption at rest, DSAR export and delete |
| C4 Sensitive personal | Uploaded papers (may be unpublished research), code submissions | Blob (per-user prefix), Qdrant `user_docs` (tenant), PostgreSQL | Owner-only, never used for curated retrieval or training, 365-day retention by default |
| C5 Secrets | API keys, webhook secrets, DB credentials | Key Vault | Managed identity, rotation |

### 7.4 What leaves the platform

| Destination | Data sent | Data never sent |
| --- | --- | --- |
| Azure OpenAI (primary) | Learner message, fenced history, retrieved chunks, learner preferences (style, depth, locale) | Email, name, Clerk ID, payment data |
| Fallback providers | Same as above, with history trimmed to 6 turns | Same as above, plus C4 documents unless the learner opts in |
| Langfuse | Prompt template ID and version, token counts, latency, hashed user ID, citations | Raw learner text by default. A sampled 5% is kept with PII redaction in non-production only. |
| Content Safety | Learner message, model output | Identity |

---

## 8. AI Services Architecture

### 8.1 Overview

```mermaid
flowchart TB
    IN["Request: chat, quiz, plan, lab review, research"] --> ORC["Orchestrator<br/>classify_intent + explicit endpoint"]
    ORC --> TUT["TutorAgent<br/>Socratic stages"]
    ORC --> QZ["QuizAgent"]
    ORC --> PL["PlannerAgent"]
    ORC --> CO["CodingAgent"]
    ORC --> RE["ResearchAgent"]
    ORC --> CA["CareerAgent"]

    subgraph Context["Context assembly"]
        PROF["Learner profile<br/>persona, style, depth, math level, locale, avatar personality"]
        MAS["Mastery and prerequisites"]
        RET["RetrievalService"]
        HIS["Conversation memory<br/>last 20 turns + rolling summary"]
    end

    TUT --> Context
    QZ --> RET
    RE --> RET
    PL --> MAS

    subgraph Pipeline["Model call pipeline"]
        PR["PromptRegistry<br/>id, version, tier"]
        GI["Input guardrails"]
        RT["ProviderRouter<br/>tier routing, fallback, breaker"]
        GO["Output guardrails<br/>grounding, harm, schema"]
    end

    Context --> PR --> GI --> RT --> GO
    RT --> AOAI["Azure OpenAI"]
    RT --> ALT["OpenAI / Anthropic / Gemini"]
    RT --> CUR["Curriculum fallback<br/>authored content"]
    GO --> OUT["Response + citations + telemetry"]
```

### 8.2 Agent catalogue

| Agent | Input | Output | Model tier | Retrieval | Deterministic fallback |
| --- | --- | --- | --- | --- | --- |
| Tutor | Message, stage plan, profile, context | Streamed markdown | `fast` (escalate to `reasoning` for PhD or formal-math depth) | `kb_curated` | Authored lesson text for the concept |
| Quiz | Concept, difficulty, locale, chunks | JSON items (schema-validated) | `fast` | `kb_curated` | Authored question bank (`catalog.QUESTIONS`) |
| Planner | Goal, mastery map | Explanation of a plan built by `domain/planner` | `fast` | Graph only | Plan without explanation |
| Coding | Code, output, rubric | Review markdown | `code` | Project brief | `domain/code_review` static checks |
| Research | Owned document chunks | Summary, critique, gaps, future work (cited) | `reasoning` | `user_docs` | Extractive summary, critique withheld |
| Career | Profile, mastery | Roles, skill gaps, next steps | `fast` | Career guides | `domain/career` rules |
| Content generator (admin) | Asset version chunks | Lesson notes, flashcards, quizzes, exercises, concept map | `reasoning` | Single asset | None. The job fails and is retried. |

The domain decides *what* to teach: concept, stage, difficulty, and plan order. Agents decide *how to phrase it*. That keeps pedagogy testable and model-independent (principle P2).

### 8.3 Provider router

The current `ProviderRouter.complete()` tries providers in a fixed order. The target adds tiers, streaming, Azure OpenAI, timeouts, and a circuit breaker.

```python
# backend/app/services/llm.py (target interface)
from typing import AsyncIterator, Literal, Protocol

Tier = Literal["fast", "reasoning", "code", "embed"]

class ModelProvider(Protocol):
    name: str
    async def complete(self, req: "CompletionRequest") -> "Completion": ...
    def stream(self, req: "CompletionRequest") -> AsyncIterator["Delta"]: ...

class CompletionRequest(BaseModel):
    tier: Tier
    system: str
    messages: list[tuple[str, str]]
    max_tokens: int = 700
    temperature: float = 0.3
    json_schema: dict | None = None      # structured output for quiz and content generation
    prompt_id: str                       # e.g. "tutor.socratic"
    prompt_version: str                  # e.g. "2026-10-01"
    user_hash: str                       # sha256(user_id + pepper) for tracing and abuse

class ProviderRouter:
    """Tier → ordered providers. A provider with an open breaker is skipped."""
    async def complete(self, req: CompletionRequest) -> Completion | None: ...
    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]: ...
```

Routing table (configuration, not code):

| Tier | Primary (Azure OpenAI deployment) | Fallback 1 | Fallback 2 | Timeout (first token / total) |
| --- | --- | --- | --- | --- |
| `fast` | `chat-fast` (gpt-4o-mini class) | OpenAI `OPENAI_MODEL` | Anthropic `ANTHROPIC_MODEL` | 4 s / 30 s |
| `reasoning` | `chat-reasoning` (gpt-4o class or newer) | Anthropic | Gemini | 8 s / 90 s |
| `code` | `chat-code` | Anthropic | OpenAI | 6 s / 60 s |
| `embed` | `embed-small` (text-embedding-3-small, 1536 d) | none: same model on OpenAI | none | 10 s |

Rules:

- **Circuit breaker.** A provider opens after 5 failures in 30 s. After 60 s it lets one probe request through. Breaker state lives in Redis so all replicas share it.
- **Fallback during a stream.** If a provider fails before the first token, the router tries the next one. After tokens have been sent, it does not switch providers. It sends an `error` event so the learner never sees two voices in one reply.
- **Embedding consistency.** The embedding model is fixed per Qdrant collection, so embeddings never fall back to a different model. If embedding fails, ingestion retries. Query-time embedding failure falls back to sparse-only search.
- **Token budgets.** Daily per-user budgets are enforced in Redis: Free 50k, Pro 500k, Research 2M tokens. Past the budget, the router uses `fast` only, then curriculum fallback.
- **Async clients.** Use the async SDK clients (`AsyncAzureOpenAI`, `AsyncAnthropic`, `genai.Client().aio`). Create each once per process and reuse it. The current code builds a new client per call.

### 8.4 Prompt management

- Prompts live in `backend/app/prompts/*.md` with YAML front-matter: `id`, `version`, `tier`, `inputs`, `output_schema`.
- `PromptRegistry` loads them at startup and exposes `render(id, **vars)`, which returns the text and a `(id, version, sha256)` tuple. That tuple goes on every Langfuse generation.
- The system prompt is assembled in fixed order: the safety preamble (`security.md`), the role (`tutor.md`), the teaching style block, the learner profile block, `<untrusted>` retrieved context, and the citation rules.
- Changing a prompt requires an eval run (section 8.8) in CI. The PR is blocked if groundedness or answer quality falls by more than 2 points.

Teaching-style and personality blocks are small composable templates, so the 7 styles × 6 personalities × 6 depths do not need separate prompts:

```text
prompts/
├── security.md            # always first
├── tutor.md               # role and Socratic stage instructions
├── styles/{simple,storytelling,visual,mathematical,research,industry,mixed}.md
├── personalities/{friendly,professional,academic,motivational,strict,socratic}.md
├── depth/{beginner,intermediate,advanced,expert,researcher,phd}.md
└── locale/{en,fr,es}.md   # reply language, terminology glossary
```

### 8.5 Guardrails pipeline

```mermaid
flowchart LR
    IN["User text"] --> G1["prompt_guard.screen_user_input<br/>length, control chars, injection patterns"]
    G1 --> G2["Content Safety Prompt Shields<br/>jailbreak and indirect injection"]
    G2 --> G3["Topic policy<br/>off-topic soft redirect"]
    G3 --> FENCE["fence_untrusted for user text,<br/>retrieved chunks, uploaded docs, code"]
    FENCE --> LLM["Model"]
    LLM --> O1["Schema validation<br/>JSON outputs"]
    O1 --> O2["Grounding check<br/>citations present and valid"]
    O2 --> O3["Content Safety harm filters"]
    O3 --> O4["Leak check<br/>system prompt, answer keys"]
    O4 --> OUT["Response"]
    G1 -.->|"blocked"| REJ["400 with safe message, audit event"]
    G2 -.->|"blocked"| REJ
    O3 -.->|"blocked"| SAFE["Replace with safe refusal, audit"]
```

The tutor has no tools that write data or reach the internet. The model never sees quiz answer keys; grading is deterministic in `domain/grading`.

### 8.6 Personalisation and multilingual behaviour

- **Learner profile block.** Built from `learner_profiles` and `preferences`: persona, goal, style, personality, pace, depth, math level, breadth, and locale. About 120 tokens.
- **Mastery block.** Mastery for the current concept, its weakest prerequisite, and its strongest neighbouring concept, from the concept graph. The tutor uses it to choose analogies and to move back to a prerequisite first, as `socratic.build_turn` already does.
- **Adaptive difficulty.** Implemented in `domain/difficulty.select(mastery, depth_cap)`:

| Mastery score | Difficulty served | Capped by learner depth |
| --- | --- | --- |
| 0–39 | beginner | yes |
| 40–59 | intermediate | yes |
| 60–79 | advanced | yes |
| 80–91 | expert | yes |
| 92–100 | phd | yes |

  After three consecutive correct answers, difficulty steps up one level within a quiz. After two consecutive wrong answers, it steps down one level.

- **Language.** The reply language comes from `preferences.locale`. Retrieval prefers chunks in that locale and falls back to English. The answer is still given in the learner's locale, with an "English source" note on citations. Quizzes and lessons use human-reviewed translation rows when they exist. Otherwise a machine translation is generated and labelled. Progress is keyed by slug, so it is the same in every language.

### 8.7 Extension points (post-MVP)

| Capability | Integration | Contract |
| --- | --- | --- |
| Voice tutor | Azure AI Speech: STT and neural TTS voices en-GB, en-US, en-NG, fr-FR, es-ES | `POST /tutor/voice` returns an audio stream. The avatar profile maps to a voice name and speaking style. |
| Avatar | Avatar profile is stored in `preferences.avatar` and rendered client-side | Same personality key as the prompt block |
| Notebooks and ML labs | Custom-container ACA session pool with numpy, torch-cpu, and gymnasium | `SandboxClient.execute(kind="notebook")` |
| Robotics sims | Client-side Three.js and Pyodide, so no server compute | Lesson content embeds a `sim` block |
| Fine-tuned tutor | Azure OpenAI fine-tuned deployment added as a tier | New router tier and eval gate |

### 8.8 Evaluation

| Suite | When | Data | Metrics | Gate |
| --- | --- | --- | --- | --- |
| Unit (domain) | Every PR | pytest | Coverage ≥ 90% | Required |
| Prompt regression | PR touching `prompts/`, `agents/`, `services/llm*`, `retrieval*` | 200 golden Q&A per launch path, in Langfuse datasets | Groundedness, answer relevance, citation precision, Socratic adherence (LLM-as-judge with rubric) | No more than 2 points worse than `main` |
| Retrieval | PR touching chunking or retrieval | 300 labelled query → chunk pairs | Recall@6, MRR@10, nDCG@10 | Recall@6 ≥ 0.85 |
| Safety | Weekly + release | Injection and jailbreak set (OWASP LLM01) | Block rate | ≥ 98% |
| Online | Continuous | 5% of production traces | Thumbs up or down, abstention rate, judge score | Alert if 7-day judge score falls ≥ 5% |

---

## 9. Knowledge Management Architecture

### 9.1 Responsibilities

The knowledge management system (KMS) is the only way content reaches learners. It covers the asset library, taxonomy, concept graph, curriculum builder, versioning, the approval workflow, AI content generation, the recommendation inputs, and content analytics. `domain/catalog.py` becomes the seed for the KMS. After the KMS ships, the database is the source of truth and the catalog is used only for first-run seeding and tests.

### 9.2 Data model

```mermaid
erDiagram
    TAXONOMY_NODES ||--o{ TAXONOMY_NODES : parent
    TAXONOMY_NODES ||--o{ CONCEPTS : groups
    CONCEPTS ||--o{ CONCEPT_RELATIONS : source
    CONCEPTS ||--o{ CONCEPT_RELATIONS : target
    KNOWLEDGE_ASSETS ||--o{ ASSET_VERSIONS : has
    ASSET_VERSIONS ||--o{ KNOWLEDGE_CHUNKS : split_into
    KNOWLEDGE_CHUNKS ||--|| CHUNK_EMBEDDINGS : indexed_as
    ASSET_VERSIONS ||--o{ ASSET_CONCEPTS : covers
    CONCEPTS ||--o{ ASSET_CONCEPTS : covered_by
    ASSET_VERSIONS ||--o{ WORKFLOW_TRANSITIONS : moves_through
    ASSET_VERSIONS ||--o{ INGESTION_JOBS : processed_by
    ASSET_VERSIONS ||--o{ GENERATED_ARTIFACTS : source_of
    ASSET_VERSIONS ||--o{ ASSET_TRANSLATIONS : translated_as
    LEARNING_PATHS ||--o{ CURRICULUM_NODES : contains
    CURRICULUM_NODES ||--o{ CURRICULUM_NODES : parent
    CURRICULUM_NODES }o--o| ASSET_VERSIONS : references
    USERS ||--o{ WORKFLOW_TRANSITIONS : acts

    TAXONOMY_NODES {
        uuid id PK
        uuid parent_id FK
        string slug UK
        string name
        ltree path "e.g. ai.rl.mdp"
        int position
        timestamptz created_at
        timestamptz updated_at
    }
    KNOWLEDGE_ASSETS {
        uuid id PK
        string slug UK
        string kind "pdf, docx, pptx, md, url, video, repo, dataset, audio, image"
        uuid owner_id FK
        uuid current_published_version_id FK
        bool archived
        timestamptz created_at
        timestamptz updated_at
    }
    ASSET_VERSIONS {
        uuid id PK
        uuid asset_id FK
        int version_no
        string status "draft, review, approved, published, superseded, archived"
        string title
        text description
        string difficulty
        string language
        string author
        string source_url
        date publication_date
        jsonb learning_objectives
        int estimated_minutes
        jsonb tags
        string blob_path
        string content_sha256
        uuid editor_id FK
        text change_note
        timestamptz created_at
        timestamptz updated_at
    }
    KNOWLEDGE_CHUNKS {
        uuid id PK
        uuid version_id FK
        int ordinal
        text text
        string heading_path
        int page
        int token_count
        string locale
        string citation_label
        timestamptz created_at
    }
    CHUNK_EMBEDDINGS {
        uuid id PK
        uuid chunk_id FK
        string collection
        string model
        int dimensions
        string qdrant_point_id
        timestamptz created_at
    }
    WORKFLOW_TRANSITIONS {
        uuid id PK
        uuid version_id FK
        string from_status
        string to_status
        uuid actor_id FK
        text comment
        timestamptz created_at
    }
    INGESTION_JOBS {
        uuid id PK
        uuid version_id FK
        string status "queued, running, succeeded, failed"
        int attempts
        text error
        string idempotency_key UK
        timestamptz created_at
        timestamptz updated_at
    }
    GENERATED_ARTIFACTS {
        uuid id PK
        uuid source_version_id FK
        string kind "lesson_notes, flashcards, quiz, exercise, project, study_guide, concept_map"
        jsonb payload
        string status
        string prompt_version
        timestamptz created_at
        timestamptz updated_at
    }
    CURRICULUM_NODES {
        uuid id PK
        uuid path_id FK
        uuid parent_id FK
        string kind "course, module, lesson, assessment, project, resource"
        uuid asset_version_id FK
        string concept_slug
        int position
        timestamptz created_at
        timestamptz updated_at
    }
```

Implementation notes:

- `taxonomy_nodes.path` uses the `ltree` extension with a GiST index, so subtree queries are fast (`path <@ 'ai.rl'`).
- `asset_versions` has `UNIQUE (asset_id, version_no)` and a partial unique index `UNIQUE (asset_id) WHERE status = 'published'`. The database therefore guarantees at most one published version per asset.
- The existing `concepts` and `concept_relations` tables stay as the concept graph. Add `taxonomy_node_id` to `concepts`, and extend `relation_type` to `prerequisite | related | advanced | part_of`.
- The existing learner-owned `research_documents` and `document_chunks` tables stay separate from the curated library. The two never mix in retrieval.

### 9.3 Content workflow

```mermaid
stateDiagram-v2
    [*] --> Draft : create or new version
    Draft --> Draft : edit, re-ingest
    Draft --> Review : submit (author)
    Review --> Draft : request changes (reviewer)
    Review --> Approved : approve (reviewer, not author)
    Approved --> Published : publish (admin or reviewer)
    Approved --> Draft : withdraw
    Published --> Superseded : newer version published
    Published --> Archived : archive (admin)
    Superseded --> Published : restore (admin)
    Archived --> Draft : revive as new version
    Archived --> [*]
```

Rules, enforced in `domain/workflow.py` as a pure transition table with tests:

- The author of a version cannot approve it (four-eyes rule).
- Only `published` chunks are searchable by learners. The Qdrant payload `status` is updated in the same job that commits the transition, and retrieval always filters `status == "published"`.
- Restoring creates no copy. It flips statuses, and the payload update runs as a job.
- Every transition writes a `workflow_transitions` row and an `audit_log` row.

### 9.4 Roles and permissions

| Action | Student | Instructor | Reviewer* | Admin |
| --- | --- | --- | --- | --- |
| Read published content | ✓ | ✓ | ✓ | ✓ |
| Create assets and drafts |  | ✓ | ✓ | ✓ |
| Submit for review |  | ✓ (own) | ✓ | ✓ |
| Approve |  |  | ✓ (not own) | ✓ (not own) |
| Publish, archive, restore |  |  | ✓ | ✓ |
| Edit taxonomy and concept graph |  |  |  | ✓ |
| Run AI content generation |  | ✓ | ✓ | ✓ |
| Manage users and roles |  |  |  | ✓ |
| View content analytics |  | ✓ (own assets) | ✓ | ✓ |

\* `reviewer` is a new value in the `users.role` check constraint. `domain/access.normalize_role` must accept it.

### 9.5 Source connectors

| Source | Parser (worker) | Notes |
| --- | --- | --- |
| PDF | `pymupdf` for text, layout, and page numbers. `nougat`/OCR via Azure AI Document Intelligence for scanned PDFs. | Equations kept as LaTeX where extractable |
| DOCX, PPTX | `python-docx`, `python-pptx` | Slide number is the citation anchor |
| Markdown, TXT, HTML, URL | `markdown-it`, `trafilatura` | URL fetch uses an allow-list, ignores robots-disallowed pages, max 5 MB |
| CSV, JSON datasets | Schema and sample profile only | Rows are not embedded |
| YouTube, MP4, audio | Transcript API, else Azure OpenAI Whisper | Timestamps are the citation anchor |
| GitHub repo | Shallow clone of the README, docs, and docstrings at a pinned commit SHA | Code is chunked by symbol |
| Images | Caption with a vision model, plus alt text | Caption is labelled as AI-generated |

### 9.6 Translation

`asset_translations (version_id, locale, status, title, chunks…)` follows the same workflow as the source version. Machine translations are created as `draft` with `machine=true`. A reviewer who is fluent in the language publishes them. Chunks are embedded per locale into the same collection with a `locale` payload.

### 9.7 Recommendations

```mermaid
flowchart LR
    M["concept_mastery<br/>weak concepts"] --> RANK["Recommendation ranker<br/>domain/planner"]
    G["Concept graph<br/>prerequisites first"] --> RANK
    P["Learner profile<br/>goal, style, depth"] --> RANK
    E["Content effectiveness<br/>mastery uplift per asset"] --> RANK
    RANK --> OUT["Top 5 resources<br/>lesson, visual explainer, quiz, sim, paper"]
```

Score = 0.4 × prerequisite gap + 0.25 × style match + 0.2 × effectiveness + 0.15 × freshness. Assets the learner has already completed are excluded. Effectiveness is the mean mastery change on the linked concept within 7 days of engaging with the asset. A nightly job computes it into `asset_effectiveness`.

### 9.8 Content analytics

Learner events (`lesson_viewed`, `lesson_completed`, `quiz_graded`, `citation_clicked`, `asset_opened`) are written to `learning_events`. The table is partitioned by month. A nightly job aggregates them into `content_metrics_daily`. The admin dashboard reads only the aggregates, from the PostgreSQL read replica. The metrics are the ones in Admin.md: most visited lessons, hardest concepts, quiz pass rates, engagement, effectiveness, completion, and knowledge gaps.

---

## 10. Gamification Architecture

### 10.1 Design

Gamification is driven by events and backed by a ledger:

1. Learning actions emit a **reward intent**: kind, source ID, and requested amount.
2. `GamificationService.award()` applies the pure rules in `domain/gamification`: daily cap, quiz curve, and streak. In the **same transaction** as the learning write, it inserts an idempotent `xp_events` row and updates the totals cached on `users`. It also writes an `outbox_events` row.
3. After commit, the service updates the Redis leaderboards. This is best-effort, and the rebuild job repairs any drift.
4. The worker relays outbox events to the `domain-events` topic. Subscribers evaluate badges, titles, and challenge completion, and send notifications.

```mermaid
flowchart LR
    subgraph Txn["Single PostgreSQL transaction"]
        A["Learning write<br/>quiz_result, progress, submission"] --> B["xp_events INSERT<br/>ON CONFLICT DO NOTHING"]
        B --> C["users.xp, level, streak UPDATE"]
        C --> D["outbox_events INSERT"]
    end
    D -->|"after commit"| R["Redis ZINCRBY<br/>leaderboard keys"]
    D -->|"relay"| T[["Service Bus topic<br/>domain-events"]]
    T --> S1["Badge evaluator"]
    T --> S2["Title and rank evaluator"]
    T --> S3["Challenge completion"]
    T --> S4["Notification sender"]
    S1 --> DB[("user_achievements")]
    S2 --> DB2[("users.title")]
```

### 10.2 Rules

The current constants in `domain/gamification.py` stay. Additions:

| Event | XP | Notes |
| --- | --- | --- |
| Lesson completed (first time) | 40 | `LESSON_XP` |
| Quiz graded | 10 + 40 × score ratio | `quiz_xp` |
| Code passes | 25 | `CODE_XP`, first pass per project |
| Flashcard review | 5 | `REVIEW_XP`, at most 20 counted per day |
| Paper analysis | 20 | Once per document |
| Daily challenge | 50 / 75 / 100 by difficulty | Counts outside the daily cap |
| Streak milestone 7 / 30 / 100 days | 50 / 200 / 500 | Counts outside the daily cap |
| Community contribution (post-MVP) | 15 | Moderated |
| **Daily cap** | 400 | `DAILY_XP_CAP`, uses the learner's local day from `preferences.timezone` |

Levels: `level = 1 + xp // 250`. Titles are derived from level and stored for display:

| Levels | Title |
| --- | --- |
| 1–4 | AI Apprentice |
| 5–9 | Data Scientist |
| 10–14 | ML Engineer |
| 15–19 | RL Explorer |
| 20–29 | Robotics Engineer |
| 30–39 | AI Researcher |
| 40–59 | AI Master |
| 60+ | Grandmaster AI Engineer |

Track titles such as "RL Explorer" can also be earned by completing a path, independent of level. They come from `achievements` with `kind='title'`.

### 10.3 Schema additions

```mermaid
erDiagram
    USERS ||--o{ XP_EVENTS : earns
    USERS ||--o{ USER_ACHIEVEMENTS : holds
    ACHIEVEMENTS ||--o{ USER_ACHIEVEMENTS : granted_as
    USERS ||--o{ FRIENDSHIPS : requester
    USERS ||--o{ FRIENDSHIPS : addressee
    DAILY_CHALLENGES ||--o{ CHALLENGE_ATTEMPTS : attempted_in
    USERS ||--o{ CHALLENGE_ATTEMPTS : makes
    SEASONS ||--o{ LEADERBOARD_SNAPSHOTS : closes_with

    USERS {
        uuid id PK
        string country_code "ISO 3166-1 alpha-2, NEW"
        string region_code "optional, NEW"
        string title "NEW"
        bool leaderboard_opt_in "default true, NEW"
        int xp
        int level
        int streak_days
        date last_active_on
    }
    XP_EVENTS {
        uuid id PK
        uuid user_id FK
        int amount
        string reason
        string source_type "NEW"
        string source_id "NEW"
        date local_day "NEW"
        timestamptz created_at
    }
    FRIENDSHIPS {
        uuid id PK
        uuid requester_id FK
        uuid addressee_id FK
        string status "pending, accepted, blocked"
        timestamptz created_at
        timestamptz updated_at
    }
    DAILY_CHALLENGES {
        uuid id PK
        date challenge_date
        string kind "quiz, coding, research, debugging, robotics"
        string concept_slug
        string difficulty
        jsonb payload_by_locale
        int xp_reward
        string badge_slug
        timestamptz created_at
    }
    CHALLENGE_ATTEMPTS {
        uuid id PK
        uuid challenge_id FK
        uuid user_id FK
        float score
        bool completed
        timestamptz created_at
    }
    SEASONS {
        uuid id PK
        string key "2026-W42, 2026-10"
        date starts_on
        date ends_on
        timestamptz created_at
    }
    LEADERBOARD_SNAPSHOTS {
        uuid id PK
        uuid season_id FK
        string scope "global, country:NG, region:NG-LA"
        jsonb top_100
        timestamptz created_at
    }
```

Constraints and indexes:

- `xp_events`: `UNIQUE (user_id, source_type, source_id)` is the idempotency guarantee. Add `INDEX (user_id, local_day)` for the cap query. Partition by month once the table passes 50M rows.
- `friendships`: `UNIQUE (LEAST(requester_id, addressee_id), GREATEST(...))`, plus `INDEX (addressee_id, status)`.
- `challenge_attempts`: `UNIQUE (challenge_id, user_id)`.
- `daily_challenges`: `UNIQUE (challenge_date, kind)`.

### 10.4 Leaderboards

The ranking dimensions are XP, challenges, quizzes, projects, research, and community. Leaderboards rank on a **composite score**, which is stored as a separate ZSET from raw XP:

`score = xp + 30 × challenges_completed + 10 × quizzes_passed + 50 × projects_completed + 40 × research_contributions + 5 × community_actions`

Redis keys. The rebuild job recreates all of them from PostgreSQL.

| Key | Type | Content | TTL |
| --- | --- | --- | --- |
| `lb:global:all` | ZSET | user_id → composite score (all time) | none |
| `lb:global:w:2026-W42` | ZSET | Weekly season score | 35 days |
| `lb:global:m:2026-10` | ZSET | Monthly season score | 400 days |
| `lb:country:{CC}:all` and `:w:{week}` | ZSET | Per country | as above |
| `lb:region:{CC-RR}:w:{week}` | ZSET | Opt-in regional | 35 days |
| `lb:profile:{user_id}` | HASH | display name, level, title, country (for top-N rendering) | 1 h |

Queries:

- **Top 10:** `ZREVRANGE key 0 9 WITHSCORES`, then a pipelined `HGETALL` of the profiles.
- **Position:** `ZREVRANK key user_id` (0-based) + 1.
- **Percentile:** `100 × (1 − rank / ZCARD key)`.
- **Friends:** read friend IDs from PostgreSQL (capped at 500, cached 5 min), then `ZMSCORE lb:global:all ids…` and sort in the API. No per-user ZSETs.
- **Opt-out:** learners with `leaderboard_opt_in=false` are never added. They can still see their own percentile, which is computed from score with `ZCOUNT`.

Season close is a Monday 00:10 UTC job. It writes `leaderboard_snapshots`, awards season badges to the top 10 per scope, and lets the old week key expire.

API:

```text
GET /api/v1/leaderboard?scope=global|country|region|friends&period=all|week|month&limit=10
→ { "scope":"country", "period":"week", "entries":[{rank, display_name, level, title, country, score}],
    "me": {rank, score, percentile} }
GET /api/v1/me/standing  → { global:{rank,percentile}, country:{…}, region:{…}, friends:{…} }
```

### 10.5 Anti-abuse

- Server-side awards only. No client-reported XP endpoint exists.
- Idempotency on `(source_type, source_id)`.
- Daily cap per local day. Timezone changes are limited to once per 7 days.
- Quiz XP counts only the first two attempts per quiz per day. Repeated identical submissions earn nothing.
- Anomaly job: z-score on daily XP per user. Above 4σ, the account is flagged for review and its leaderboard entry is hidden until cleared.
- Leaderboard display names pass a profanity filter. Learners can report names.

---

## 11. RAG Architecture

### 11.1 Ingestion pipeline

```mermaid
flowchart LR
    SRC["Blob original<br/>or URL fetch"] --> SCAN["Malware scan<br/>Defender for Storage"]
    SCAN --> PARSE["Parse<br/>format-specific"]
    PARSE --> NORM["Normalise<br/>Unicode NFC, de-hyphenate,<br/>keep LaTeX, strip boilerplate"]
    NORM --> META["Extract metadata<br/>title, headings, pages, language"]
    META --> CHUNK["Chunk<br/>structure-aware, 450 tokens,<br/>15% overlap, equation-safe"]
    CHUNK --> LINK["Concept linking<br/>slug match + embedding similarity<br/>to concept summaries"]
    LINK --> EMB["Embed<br/>dense 1536 d + sparse BM25"]
    EMB --> UPS["Qdrant upsert<br/>status=draft"]
    UPS --> REC["PostgreSQL<br/>chunks, embeddings, asset_concepts"]
    REC --> DONE["Job succeeded<br/>searchable once published"]
```

Chunking upgrades the current `domain/chunking.chunk_text` (800 characters, 120 overlap). The function stays pure and gains these behaviours:

- Split on heading boundaries first, then paragraphs, then sentences.
- Target 450 tokens, hard maximum 700, overlap about 15%. Counting uses `tiktoken` `cl100k_base`, kept in the domain as an injected counter.
- Never split inside `$$…$$`, fenced code, or a table.
- Prefix each chunk with its heading path for embedding only (`"RL > MDP > Bellman equation\n\n…"`). The stored text stays clean.
- Point ID = UUIDv5(`version_id:ordinal`), which is deterministic, so re-ingesting a version overwrites its points instead of duplicating them.

### 11.2 Qdrant collections

| Collection (alias) | Physical name | Content | Tenancy |
| --- | --- | --- | --- |
| `kb_curated` | `kb_curated_v1_te3s1536` | Curated knowledge chunks, all locales | Shared |
| `user_docs` | `user_docs_v1_te3s1536` | Learner-uploaded papers | `owner_id` with `is_tenant=true` |
| `concepts` | `concepts_v1_te3s1536` | One point per concept summary (for linking and intent) | Shared |

Collection definition (run by `app/jobs/qdrant_bootstrap.py`, idempotent):

```python
from qdrant_client import QdrantClient, models

def create_kb(client: QdrantClient, name: str) -> None:
    client.create_collection(
        collection_name=name,
        vectors_config={"dense": models.VectorParams(size=1536, distance=models.Distance.COSINE, on_disk=True)},
        sparse_vectors_config={"sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128),
        quantization_config=models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(type=models.ScalarType.INT8, always_ram=True)
        ),
        replication_factor=2,          # 1 in dev/staging
        shard_number=2,
        on_disk_payload=True,
    )
    keyword = models.PayloadSchemaType.KEYWORD
    for field in ("asset_id", "version_id", "status", "locale", "concept_slugs",
                  "difficulty", "kind", "taxonomy_path"):
        client.create_payload_index(name, field, keyword)
    client.create_payload_index(name, "published_at", models.PayloadSchemaType.DATETIME)

def create_user_docs(client: QdrantClient, name: str) -> None:
    # same vectors config, plus tenant index so each owner's data is co-located
    client.create_payload_index(
        name, "owner_id",
        models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD, is_tenant=True),
    )
    client.create_payload_index(name, "document_id", models.PayloadSchemaType.KEYWORD)
```

Point payload (`kb_curated`):

```json
{
  "chunk_id": "6f0c…", "asset_id": "…", "version_id": "…", "version_no": 3,
  "status": "published", "locale": "en", "kind": "pdf",
  "title": "Introduction to Reinforcement Learning", "heading_path": "MDP > Bellman equation",
  "page": 14, "citation_label": "Intro RL v3 p.14",
  "concept_slugs": ["mdp", "bellman-equation"], "taxonomy_path": "ai.rl.mdp",
  "difficulty": "intermediate", "published_at": "2026-10-10T09:00:00Z"
}
```

The chunk text is **not** stored in Qdrant. It is fetched from PostgreSQL by `chunk_id` after reranking. This keeps PostgreSQL authoritative and Qdrant small.

### 11.3 Retrieval pipeline

```mermaid
flowchart TB
    Q["Learner query<br/>+ concept from socratic.build_turn"] --> RW["Query rewrite<br/>resolve pronouns from last 4 turns,<br/>translate to English if no locale hits"]
    RW --> E1["Dense embed"]
    RW --> E2["Sparse encode<br/>BM25 via fastembed"]
    E1 --> HQ["Qdrant Query API<br/>prefetch dense k=30 + sparse k=30<br/>fusion RRF"]
    E2 --> HQ
    F["Filter<br/>status=published AND locale in [user, en]<br/>AND difficulty within ±1 of learner depth"] --> HQ
    HQ --> BOOST["Concept boost<br/>+0.15 if concept_slugs contains current concept,<br/>+0.05 for prerequisites"]
    BOOST --> RR["Rerank top 30 to top 6<br/>cross-encoder: Cohere Rerank on Azure<br/>or bge-reranker in worker"]
    RR --> FETCH["Fetch chunk text from PostgreSQL"]
    FETCH --> PACK["Context packing<br/>dedupe by version, ≤ 2,400 tokens,<br/>order by asset then position"]
    PACK --> CIT["Assign labels [1]..[n]"]
    CIT --> GEN["Generation with fenced context<br/>and citation instructions"]
    GEN --> VER["Verify<br/>every [n] in output exists,<br/>grounded() for critique fields"]
    VER --> ABS{"Top rerank score<br/>below 0.35?"}
    ABS -->|"yes"| NOTE["Answer from authored lesson<br/>with no-source notice, log gap"]
    ABS -->|"no"| OUT["Answer + citations"]
```

Implementation contract:

```python
# backend/app/services/retrieval.py
class RetrievedChunk(BaseModel):
    chunk_id: UUID
    label: str            # "[1]"
    text: str
    score: float
    asset_id: UUID
    version_no: int
    title: str
    citation: str         # "Intro RL v3 p.14"
    url: str              # /library/{asset_slug}?v=3#p14

class RetrievalService:
    async def retrieve(
        self, *, query: str, concept_slug: str | None, locale: str,
        depth: str, collection: Literal["kb_curated", "user_docs"] = "kb_curated",
        owner_id: UUID | None = None, document_id: UUID | None = None,
        k: int = 6, budget_tokens: int = 2400,
    ) -> list[RetrievedChunk]: ...
```

Every retrieval writes a `retrieval_logs` row: query hash, concept, chunk IDs, scores, latency, and whether the answer abstained. This feeds the "knowledge gaps across learners" analytics. Topics where learners often get no source are content the KMS team needs to author.

### 11.4 Latency budget (tutor turn, p95)

| Step | Budget |
| --- | --- |
| Auth, rate limit, guardrails (local) | 25 ms |
| Content Safety prompt shield | 120 ms |
| DB load (conversation, profile, mastery) | 40 ms |
| Query embed | 120 ms |
| Qdrant hybrid query | 60 ms |
| Rerank | 150 ms |
| Chunk fetch + packing | 30 ms |
| Model time to first token | 900 ms |
| **Total to first token** | **≈ 1.45 s** |

Content Safety and the embedding run in parallel because neither depends on the other. Rerank is skipped when the top fused score is already above 0.8.

### 11.5 Re-indexing and model changes

1. Create `kb_curated_v2_<model>` with the new configuration.
2. A backfill job re-embeds every published and draft chunk from PostgreSQL.
3. Run the retrieval eval suite (section 8.8) against v2.
4. Swap the alias atomically with `update_collection_aliases`.
5. Keep v1 for 7 days for rollback, then delete it.

The same procedure rebuilds Qdrant during disaster recovery (section 16).

---

## 12. API Gateway Architecture

### 12.1 Layers

AI Mentor has one first-party client: its own web app. Azure API Management would add cost and complicate SSE without adding a needed capability. The gateway is therefore three layers. Azure API Management (Standard v2) is introduced only when partner or public APIs exist (ADR-11).

```mermaid
flowchart LR
    C["Client"] --> L1
    subgraph L1["Layer 1: Azure Front Door Premium"]
        WAF["WAF: OWASP DRS 2.1, bot manager,<br/>geo rules, rate rule 600 req/min/IP"]
        TLS["TLS 1.2+ termination, HSTS"]
        RT["Routing rules"]
        CACHE["Cache: /_next/static, /images<br/>no cache for /api"]
    end
    L1 -->|"Private Link origin"| L2
    subgraph L2["Layer 2: Container Apps ingress (Envoy)"]
        IP["Accept only Front Door<br/>X-Azure-FDID check"]
        SPLIT["Revision traffic split<br/>blue/green"]
    end
    L2 --> L3
    subgraph L3["Layer 3: FastAPI middleware"]
        M1["RequestContext"] --> M2["BodySizeLimit"] --> M3["Auth"] --> M4["RateLimit"] --> M5["Entitlements"] --> M6["Router"]
    end
```

### 12.2 Front Door routes

| Route | Pattern | Origin group | Caching | WAF policy | Timeout |
| --- | --- | --- | --- | --- | --- |
| `web-static` | `/_next/static/*`, `/images/*` | `web` | 1 year, immutable | default | 30 s |
| `api` | `/api/*` | `api` | disabled | default + API rules | 240 s (SSE) |
| `webhooks` | `/webhooks/*` | `api` | disabled | allow-list Stripe IPs, no bot rule | 30 s |
| `health` | `/health` | `api` | disabled | probe only | 10 s |
| `web` | `/*` | `web` | disabled (SSR) | default | 60 s |

The API router currently mounts webhooks at `/api/v1/webhooks/*`. Keep that path in the app and add a Front Door rewrite from `/webhooks/*` to `/api/v1/webhooks/*`, so a separate WAF policy can apply to webhooks. Health probes from Front Door hit `/health` every 30 s from each edge location.

### 12.3 Rate-limit and entitlement classes

These replace the per-process, IP-keyed `SlidingWindowLimiter`. The implementation is a Redis token bucket (Lua script, one round trip). The key is `rl:{class}:{user_id}`, or `rl:{class}:ip:{X-Azure-ClientIP}` when unauthenticated.

| Class | Routes | Free | Pro | Research | Burst |
| --- | --- | --- | --- | --- | --- |
| `api` | All other authenticated routes | 120/min | 300/min | 300/min | 2× |
| `ai` | `/chat*`, `/agents/run`, `/quiz/generate`, `/study-plan/*`, `/career/*`, `/flashcards/generate`, `/lab/review` | 20/min, 100/day | 60/min | 60/min | 1.5× |
| `exec` | `/lab/run` | 10/min | 30/min | 30/min | 1× |
| `upload` | `/research/documents`, admin uploads | 0 | 5/day | 50/day | 1× |
| `admin` | `/admin/*` | n/a | n/a | n/a (role) 300/min | 2× |
| `anon` | Unauthenticated | 30/min per IP | | | 1× |
| `webhook` | `/webhooks/*` | none (signature-verified) | | | |

Plan entitlements are read from `users.subscription_status` and `plan`, cached in Redis for 60 s. Responses carry `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset` headers (IETF draft), and `Retry-After` on a 429.

### 12.4 Middleware order

Starlette applies middleware in reverse order of `add_middleware` calls. The effective request order must be:

1. `RequestContextMiddleware`: request ID (`X-Request-Id` or a new UUIDv7), OpenTelemetry span, client IP from `X-Azure-ClientIP`.
2. `SecurityHeadersMiddleware` (existing). Add HSTS and a CSP for API responses (`default-src 'none'`).
3. `BodySizeLimitMiddleware`: 1 MB for JSON, 25 MB for upload routes, rejected with 413 before the body is read.
4. Auth is a dependency, not middleware, so open routes stay explicit. `user_dep` resolves the Clerk JWT.
5. `RateLimitMiddleware` (Redis). It runs after auth resolves the user ID. Implement it as a dependency, `rate_limit("ai")`, attached per router.
6. `require_plan("pro")` and `require_role("admin")` dependencies.

CORS: in production the web and API share one origin, so `CORS_ORIGINS` stays empty and CORS is effectively off. In development, keep `http://localhost:3000`.

### 12.5 API conventions

| Concern | Convention |
| --- | --- |
| Versioning | URI prefix `/api/v1`. Breaking changes go to `/api/v2`, and v1 is kept for 6 months. |
| Errors | RFC 9457 `application/problem+json`: `{type, title, status, detail, instance, request_id}`. The `ClientError` handler maps to this. |
| Idempotency | `Idempotency-Key` header on `POST` for checkout, upload, quiz grade, and challenge submit. Stored in Redis for 24 h with the response. |
| Pagination | Cursor based: `?cursor=…&limit=…` returns `{items, next_cursor}` |
| Long work | `202 Accepted` + `{job_id}`. `GET /api/v1/jobs/{id}` returns status. |
| Streaming | `text/event-stream`. Heartbeat comment every 15 s so idle proxies do not close the connection. |
| Contract | OpenAPI 3.1 from FastAPI. CI generates `frontend/lib/api-types.ts` and fails on drift. |
| Timeouts | API to provider: as in section 8.3. API to DB: `statement_timeout=5s` (30 s for admin analytics on the replica). |

### 12.6 Endpoint catalogue (target v1)

Existing endpoints stay as they are. New ones are marked ★.

| Area | Method and path | Auth | Rate class |
| --- | --- | --- | --- |
| Account | `GET /me`, ★`PATCH /me/preferences`, ★`GET /me/standing`, ★`GET /me/export`, ★`DELETE /me` | user | api |
| Onboarding | ★`GET /onboarding/questions`, ★`POST /onboarding/answer`, ★`POST /onboarding/complete` | user | api |
| Tutor | `POST /chat`, ★`POST /chat/stream`, `GET /conversations`, `GET /conversations/{id}`, `POST /agents/run` | user | ai |
| Practice | `POST /quiz/generate`, `POST /quiz/{id}/grade`, `GET /lab/projects`, `POST /lab/run`, `POST /lab/review` | user | ai / exec |
| Memory | `POST /flashcards/generate`, `GET /flashcards/due`, `POST /flashcards/{id}/review` | user | ai / api |
| Study | `GET /learning-paths`, `GET /learning-paths/{slug}`, `GET /knowledge-graph`, `GET /recommendations`, `POST /study-plan/create`, `GET /study-plans`, `GET /progress`, `POST /progress/lessons/{slug}/complete`, `GET /dashboard`, ★`GET /reports/weekly` | user | api |
| Library | ★`GET /library`, ★`GET /library/{slug}` (published only) | user | api |
| Gamification | `GET /leaderboard`, ★`GET /challenges/today`, ★`POST /challenges/{id}/submit`, ★`GET /achievements`, ★`POST /friends`, ★`PATCH /friends/{id}` | user | api |
| Research | `POST /research/documents`, `POST /research/analyze`, ★`GET /research/documents`, ★`DELETE /research/documents/{id}` | Research plan | upload / ai |
| Career | `POST /career/advise` | user | ai |
| Jobs | ★`GET /jobs/{id}` | owner | api |
| Admin: users | `GET /admin/users`, `PATCH /admin/users/{id}`, `GET /admin/analytics` | admin | admin |
| Admin: knowledge | ★`POST/GET /admin/knowledge/assets`, ★`POST /admin/knowledge/assets/{id}/versions`, ★`POST …/versions/{vid}/uploaded`, ★`POST …/versions/{vid}/transition`, ★`GET …/versions/{a}/diff/{b}`, ★`POST …/versions/{vid}/generate`, ★`GET /admin/knowledge/review-queue` | instructor+ | admin |
| Admin: taxonomy | ★`GET/POST/PATCH/DELETE /admin/taxonomy`, ★`/admin/concepts`, ★`/admin/concept-relations`, ★`/admin/curriculum/{path}` | admin | admin |
| Billing | `POST /billing/checkout`, ★`POST /billing/portal`, `POST /webhooks/stripe`, `POST /webhooks/clerk` | user / signature | api / webhook |

---

## 13. Security Architecture

### 13.1 Trust boundaries

```mermaid
flowchart TB
    subgraph TB0["Boundary 0: Internet (untrusted)"]
        BR["Browser"]
        EXT["Clerk, Stripe webhooks"]
    end
    subgraph TB1["Boundary 1: Azure edge"]
        FD["Front Door + WAF"]
    end
    subgraph TB2["Boundary 2: VNet, app subnet"]
        WEB["web"]
        API["api"]
        WRK["worker"]
    end
    subgraph TB3["Boundary 3: VNet, private endpoints subnet"]
        PG[("PostgreSQL")]
        RD[("Redis")]
        BL[("Blob")]
        KV["Key Vault"]
        AO["Azure OpenAI"]
    end
    subgraph TB4["Boundary 4: Isolated execution"]
        SBX["Dynamic sessions<br/>no egress"]
    end
    subgraph TB5["Boundary 5: Third-party processors"]
        QD[("Qdrant Cloud")]
        LLM["Fallback LLMs"]
        LF["Langfuse"]
    end
    BR --> FD
    EXT --> FD
    FD -->|"Private Link"| WEB
    FD -->|"Private Link"| API
    API --> TB3
    WRK --> TB3
    API --> SBX
    API -->|"TLS, API key, NAT IP allow-list"| QD
    API -->|"TLS, API key"| LLM
    API --> LF
```

### 13.2 Identity and authentication

| Item | Specification |
| --- | --- |
| Identity provider | Clerk. Email and password, magic link, and Google. MFA is required for `admin` and `reviewer`, enforced through a Clerk organization policy. |
| Session token | Clerk session JWT, RS256, 60 s lifetime, refreshed by the Clerk SDK |
| Custom claims | Session token template: `{"email": "{{user.primary_email_address}}", "name": "{{user.full_name}}", "metadata": "{{user.public_metadata}}"}` |
| Backend verification | `PyJWKClient` with JWKS cached 10 min. Checks: `alg=RS256`, `iss == CLERK_ISSUER`, `azp ∈ ALLOWED_AZP` (new setting, the production origin), `exp` and `nbf` with 5 s leeway, `sub` present. Replace `verify_aud: False` with an explicit `azp` check, since Clerk session tokens have no `aud`. |
| Frontend | `ClerkProvider` in `app/layout.tsx`. `clerkMiddleware()` in `middleware.ts` protects `/(studio)`, `/onboarding`, and `/admin`. `lib/api.ts` reads the token with `useAuth().getToken()` (client) or `auth().getToken()` (server) and sets `Authorization: Bearer`. |
| Dev auth | `X-Dev-User-Id` only when `resolved_dev_auth`. `Settings.production_guard` already refuses it in production. Keep that guard and add a CI test for it. |
| Service-to-service | Managed identities (user-assigned `id-api`, `id-worker`, `id-jobs`) to PostgreSQL (Entra auth), Blob, Key Vault, Service Bus, and Azure OpenAI. No connection-string secrets for Azure services. |
| Webhooks | Clerk via Svix signature (existing). Stripe via `construct_event` (existing). Add a dedupe table `webhook_events(provider, event_id) UNIQUE` and reject timestamps older than 5 min. |

### 13.3 Authorisation

- **Role-based access** with roles `student < instructor < reviewer < admin`, from `users.role`. Role changes go through `PATCH /admin/users/{id}`. That endpoint writes both PostgreSQL and Clerk `public_metadata`, so the JWT claim and the database agree. **The database is authoritative**: `user_dep` loads the role from PostgreSQL, and the claim is used only for UI gating.
- **Ownership (attribute-based)**: every repository method that reads learner data takes `user_id` and filters on it. The existing pattern `conversation(conversation_id, user.id)` is the standard. A lint rule (custom ruff plugin or test) asserts that repository functions on owned tables take `user_id`.
- **Plan entitlements**: `require_plan()` dependency checks Research for uploads and document analysis.
- **Admin actions** write to `audit_log (actor_id, action, target_type, target_id, before, after, ip, request_id, created_at)`. This table is append-only, enforced by a PostgreSQL role without `UPDATE` or `DELETE`.

### 13.4 Network security

- Container Apps environment on the workload-profiles plan, injected into `snet-apps` (/23). Ingress is restricted to Front Door through Private Link, with an `X-Azure-FDID` header check as defence in depth.
- PostgreSQL, Redis, Blob, Key Vault, Service Bus (Premium tier), Azure OpenAI, and ACR sit behind private endpoints in `snet-pe` with private DNS zones. Public network access is **disabled** on all of them.
- Egress goes through a NAT Gateway with a static IP. Qdrant Cloud and the fallback LLM providers allow-list that IP where they support it.
- NSGs: `snet-pe` allows inbound only from `snet-apps` and `snet-jobs`.
- Dynamic sessions run with network egress disabled.

### 13.5 Data protection

| Control | Implementation |
| --- | --- |
| In transit | TLS 1.2+ everywhere. HSTS `max-age=31536000; includeSubDomains; preload`. PostgreSQL `sslmode=require`. |
| At rest | Microsoft-managed keys by default. Customer-managed keys in Key Vault for PostgreSQL and Blob at the Scale phase or on enterprise demand. |
| Field-level | `users.email` gets a deterministic hash column for lookup. Raw email stays in PostgreSQL only. No PII in Redis or Qdrant: they hold IDs only. |
| Retention | Conversations 24 months. Uploaded papers 12 months after last access. Logs 90 days (App Insights), 1 year (archive). `xp_events` kept indefinitely (aggregates only after deletion). |
| Deletion and DSAR | `DELETE /me` queues an erasure job. It deletes PostgreSQL rows (cascade), Blob prefix `users/{id}/`, and Qdrant `user_docs` points filtered by `owner_id`. It removes the user from Redis ZSETs and deletes the Clerk user. Done within 30 days, recorded in the audit log. `GET /me/export` produces a JSON archive. |
| Residency | Primary EU region (section 17). Azure OpenAI deployment in an EU Data Zone. |
| Minors | Minimum age 13, or 16 where local law requires, captured at sign-up. Under-18 accounts get no public leaderboard name. They show initials only. |

### 13.6 AI security (OWASP Top 10 for LLM applications)

| Risk | Control |
| --- | --- |
| LLM01 Prompt injection | `screen_user_input`, Content Safety Prompt Shields (direct and document), `fence_untrusted` on all user, retrieved, and uploaded content, no tool use with side effects |
| LLM02 Sensitive information disclosure | No PII in prompts beyond first name (optional). Answer keys are never in context. Output leak check for system-prompt fragments. |
| LLM03 Supply chain | Pinned model deployment versions. Model change goes through the eval gate. SBOM for Python and Node. |
| LLM04 Data and model poisoning | Only `published` content is retrievable. Four-eyes approval. Source URL allow-list. Learner uploads are isolated in `user_docs`. |
| LLM05 Improper output handling | Markdown rendered with `rehype-sanitize`. No raw HTML. Mermaid in `securityLevel: 'strict'`. JSON outputs validated with Pydantic. |
| LLM06 Excessive agency | Agents are read-only. Domain code performs all writes after validation. |
| LLM07 System prompt leakage | No secrets in prompts. Leak check. Prompts treated as non-secret but internal. |
| LLM08 Vector and embedding weaknesses | Tenant index on `owner_id`. Every `user_docs` query has a mandatory filter added by the adapter, not the caller. Collection-level API keys. |
| LLM09 Misinformation | Grounding and citations, abstention threshold, "no source" notice, eval suite |
| LLM10 Unbounded consumption | Per-user token budgets, `max_tokens` per tier, rate classes, per-provider spend alerts |

### 13.7 Application security controls

- **Input validation.** Pydantic models with `max_length` bounds (already present) and `extra="forbid"` on request models.
- **Uploads.** Size limits, MIME sniffing with `python-magic` (not by file extension), Defender for Storage malware scanning (the worker refuses blobs not tagged `No threats found`), and PDF parsing in the worker with a 60 s timeout and memory cap.
- **SSRF.** URL connector resolves DNS and rejects private, link-local, and metadata ranges. Redirects are re-checked. It goes through the NAT egress only.
- **Web.** CSP: `default-src 'self'; script-src 'self' 'nonce-…' https://*.clerk.accounts.dev; connect-src 'self' https://*.clerk.accounts.dev; img-src 'self' data: https://img.clerk.com; frame-ancestors 'none'`. Clerk origins are adjusted for the production Clerk domain.
- **Dependencies.** Dependabot. `pip-audit` and `npm audit --omit=dev` in CI. Trivy image scan blocks on critical findings. Images are signed with Notation and verified at deploy.
- **Secrets.** Key Vault references in Container Apps. Rotation: webhook secrets yearly, provider keys every 90 days. Gitleaks pre-commit hook and CI step.

### 13.8 Code execution sandbox

| Layer | Control |
| --- | --- |
| 1. Policy | `domain/sandbox.validate_source` AST allow-list (existing): no imports outside the allow-list, no `exec`, `eval`, dunder access, or file I/O |
| 2. Isolation | ACA dynamic sessions, Python code-interpreter pool, Hyper-V isolation per session |
| 3. Network | Egress disabled on the pool |
| 4. Resources | 10 s execution timeout, 1 vCPU, 2 GiB, 5 min idle cooldown, output truncated to 8,000 characters (existing) |
| 5. Identity | Session identifier = `sha256(user_id)`, so learners never share a session |
| 6. Results | Pass or fail is decided by the API comparing expected output, never by code inside the sandbox |

`services/sandbox_runner.execute_restricted` (local subprocess) remains for development and tests only. Startup fails in production if `SANDBOX_POOL_ENDPOINT` is unset.

### 13.9 Threat model (STRIDE summary)

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Spoofing: forged JWT or dev header in production | Accounts | RS256 with JWKS, `iss`/`azp`, production guard on dev auth |
| Tampering: XP manipulation | Leaderboards | Server-side awards, idempotency, cap, anomaly detection |
| Repudiation: admin publishes harmful content | Content | Four-eyes approval, append-only audit log |
| Information disclosure: cross-tenant document retrieval | Papers | Ownership check + mandatory `owner_id` filter + tenant index |
| Denial of service: LLM cost exhaustion | Budget | Token budgets, rate classes, WAF, spend alerts |
| Elevation of privilege: role claim injection | Admin | DB-authoritative role. `public_metadata` writable only by the backend. |
| Sandbox escape | Infrastructure | Hyper-V isolation, no egress, no credentials in the session |
| Injection through uploaded content | Tutor integrity | Fencing, document prompt shields, isolation from curated retrieval |

---

## 14. Scalability Strategy

### 14.1 Capacity model (design load)

| Input | Value |
| --- | --- |
| Monthly active users | 50,000 |
| Peak concurrent | 5,000 (10% of MAU) |
| Tutor turns per active learner | 1 every 30 s while chatting. 40% of concurrent users are chatting. |
| Peak tutor turns | ≈ 70/s typical, 200/s burst (exam season) |
| Average tutor tokens | 2,000 in, 400 out |
| Peak tokens per minute | ≈ 29M TPM in, 5.8M TPM out at 200/s. Plan Azure OpenAI quota across 2 deployments (Global or Data Zone Standard) plus PTU at the Scale phase. |
| Concurrent SSE streams | ≈ 200/s × 6 s average stream ≈ 1,200 open streams |
| Non-AI API | ≈ 1,500 req/s peak |
| PostgreSQL size, year 1 | ≈ 60 GB (messages dominate) |
| Qdrant points | ≈ 2M curated (all locales) + 5M user docs at 1536 d with int8 quantisation ≈ 12 GB RAM for quantised vectors, originals on disk |

### 14.2 Per-component scaling

| Component | Scaling mechanism | MVP | Scale phase |
| --- | --- | --- | --- |
| `web` | KEDA HTTP, 80 concurrent per replica | 1–3 × 0.5 vCPU / 1 GiB | 3–20 × 1 vCPU / 2 GiB |
| `api` | KEDA HTTP, 50 concurrent per replica. SSE connections count toward concurrency. | 2–4 × 1 vCPU / 2 GiB | 4–40 × 2 vCPU / 4 GiB (dedicated D4 profile) |
| `worker` | KEDA Service Bus, 10 messages per replica | 0–3 × 1 vCPU / 2 GiB | 0–20 × 2 vCPU / 4 GiB |
| Sandbox | Session pool `maxConcurrentSessions` | 20 | 300 |
| PostgreSQL | Vertical, read replica, PgBouncer (built-in) | Burstable B2ms, 64 GB | GP D8ds_v5 zone-redundant HA + 1 read replica, 512 GB, 7.5k IOPS |
| Redis | Vertical, cluster | Balanced B1 | Balanced B5 with HA |
| Qdrant | Nodes, shards, replicas | 1 node 4 GB | 3 nodes × 16 GB, `shard_number=2`, `replication_factor=2` |
| Service Bus | Messaging units | Standard | Premium 1 MU (private endpoint) |

### 14.3 API concurrency

The current handlers are synchronous (`def`) and call blocking LLM SDKs. FastAPI runs them in a 40-thread pool, so 40 slow model calls would stall every request on that replica. Required changes:

1. Make tutor, quiz generation, research analysis, and other model paths `async def`, using async provider clients and `httpx.AsyncClient` for Qdrant (`AsyncQdrantClient`) and Content Safety.
2. Keep SQLAlchemy synchronous for now, with DB work wrapped in `run_in_threadpool`, and raise `anyio`'s default thread limiter to 100. Move to `AsyncSession` with `psycopg` async only if profiling shows DB thread contention.
3. Run Uvicorn with 2 workers per 2-vCPU replica (`--workers 2`).
4. Set SQLAlchemy `pool_size=10`, `max_overflow=10` per worker, through PgBouncer transaction pooling (port 6432). The budget across 40 replicas × 2 workers × 20 is 1,600 client connections, which PgBouncer multiplexes onto about 200 server connections.

### 14.4 Database scaling

- **Read replica** for admin analytics, leaderboard rebuilds, and reports. The route chooses the session (`get_db(read_only=True)`).
- **Partitioning.** Monthly partitions on `messages`, `xp_events`, `learning_events`, and `retrieval_logs`, managed with `pg_partman`. Partitions older than the retention window are detached.
- **Indexes.** The existing indexes stay. Add `messages (conversation_id, created_at)`, `xp_events (user_id, local_day)`, `concept_mastery (user_id)` (already unique), `asset_versions (status, language)`, and GIN on `asset_versions.tags`.
- **Hot rows.** `users.xp` updates are row-level and per user, so there is no global hot row. Leaderboards are in Redis, not SQL.

### 14.5 Caching

| Data | Cache | TTL | Invalidation |
| --- | --- | --- | --- |
| Learning paths, knowledge graph, published lesson content | Redis + Next.js `fetch` revalidate | 10 min | Tag invalidation on publish (`revalidateTag("content")` via webhook from the API) |
| JWKS | In-process | 10 min | On `kid` miss |
| Entitlements and role | Redis | 60 s | Explicit delete on change |
| Daily challenge | Redis | 26 h | Job overwrite |
| Leaderboard top 10 | Redis (ZSET is the cache) | n/a | n/a |
| Embeddings of frequent queries | Redis `emb:{sha256(text)}` | 7 days | None (deterministic) |
| Semantic answer cache | Not used | n/a | Personalised answers are not safely reusable |

### 14.6 Growth phases

| Phase | Users | Topology changes |
| --- | --- | --- |
| MVP | ≤ 2k MAU | Single region, burstable DB without HA, Qdrant 1 node, Service Bus Standard, `api` min 2 replicas |
| Growth | ≤ 50k MAU | Zone-redundant HA DB, read replica, Redis HA, Qdrant 3 nodes, dedicated workload profile for `api`, Azure OpenAI quota in 2 regions of the Data Zone |
| Scale | > 50k MAU | Warm standby region, PTU for the `fast` tier, Service Bus Premium, CMK, APIM if partners. Split `worker` into `ingest-worker` and `gen-worker` if queues interfere. |

### 14.7 Cost controls

- Budgets and alerts at 50%, 80%, and 100% per resource group, plus per-provider token spend dashboards in Langfuse.
- `worker` scales to zero. Dev and staging DBs stop out of hours.
- The `fast` tier is the default. `reasoning` is used only for research, content generation, and PhD depth.
- Qdrant int8 quantisation with original vectors on disk.

---

## 15. Monitoring Architecture

### 15.1 Telemetry pipeline

```mermaid
flowchart LR
    subgraph Apps
        WEB["web<br/>@vercel/otel or @opentelemetry/sdk-node"]
        API["api<br/>OTel SDK, FastAPI + SQLAlchemy +<br/>httpx + redis instrumentation"]
        WRK["worker, jobs<br/>OTel SDK"]
        BRW["Browser<br/>App Insights JS, web vitals"]
    end
    WEB --> AMX["Azure Monitor OpenTelemetry<br/>exporter"]
    API --> AMX
    WRK --> AMX
    BRW --> AI
    AMX --> AI["Application Insights<br/>workspace-based"]
    AI --> LA[("Log Analytics workspace")]
    ACA["Container Apps system logs"] --> LA
    PGM["PostgreSQL metrics, Query Store"] --> LA
    FDL["Front Door + WAF logs"] --> LA
    QDM["Qdrant Cloud metrics<br/>Prometheus"] --> AMP["Azure Monitor<br/>managed Prometheus"]
    API -->|"LLM generations"| LF["Langfuse"]
    WRK --> LF
    LA --> WB["Workbooks and Grafana dashboards"]
    AMP --> WB
    LA --> AL["Alert rules"]
    AMP --> AL
    LF -->|"score webhooks"| AL
    AL --> AG["Action groups<br/>PagerDuty or Opsgenie, Teams, email"]
```

`app/core/telemetry.py` already sets up OpenTelemetry. Add `azure-monitor-opentelemetry` with the `APPLICATIONINSIGHTS_CONNECTION_STRING` setting. Keep `OTEL_EXPORTER_OTLP_ENDPOINT` for local Jaeger.

### 15.2 Signals

| Signal | Name | Dimensions |
| --- | --- | --- |
| Request rate, errors, duration | OTel HTTP semantic conventions | route, method, status, revision |
| Time to first token | `ai.ttft_ms` (histogram) | agent, tier, provider |
| Model latency, tokens, cost | `ai.duration_ms`, `ai.tokens_in`, `ai.tokens_out`, `ai.cost_usd` | agent, tier, provider, model |
| Provider fallback | `ai.fallback_total` | from, to, reason |
| Breaker state | `ai.breaker_open` (gauge) | provider |
| Retrieval | `rag.latency_ms`, `rag.top_score`, `rag.abstained_total` | collection, locale |
| Guardrails | `guard.blocked_total` | stage, flag |
| Queue | Service Bus active and DLQ message count | queue |
| Jobs | `job.duration_ms`, `job.failed_total` | job name |
| Gamification | `xp.awarded_total`, `xp.capped_total`, `lb.drift` | reason |
| Business | sign-ups, onboarding completion, DAU, weekly retention, quiz completion, challenge participation | locale, country, plan |

### 15.3 Logging standards

- JSON logs to stdout with `timestamp, level, message, request_id, trace_id, span_id, user_hash, route, revision`.
- **Never** log prompt text, learner messages, uploaded content, emails, or tokens in App Insights. LLM content goes only to Langfuse, with redaction (section 7.4).
- Log levels: `INFO` for state changes, `WARNING` for provider fallbacks (already in `ProviderRouter`), `ERROR` with stack trace for unhandled exceptions.

### 15.4 SLOs

| SLO | Objective | Window | SLI |
| --- | --- | --- | --- |
| Learner API availability | 99.9% | 30 days | Non-5xx / all, excluding 429, from Front Door logs |
| Tutor TTFT | 95% < 1.5 s | 7 days | `ai.ttft_ms` |
| Tutor completion | 99% of streams end with `done` | 7 days | `done` / started |
| Non-AI latency | 95% < 300 ms | 7 days | request duration |
| Ingestion freshness | 95% of uploads ready in < 10 min | 7 days | job duration |
| Daily challenge readiness | 100% ready by 00:30 UTC | Daily | job status |
| Grounded answers | ≥ 90% | 7 days | Langfuse groundedness score |

Each SLO has a burn-rate alert: fast burn (14.4× over 1 h) pages, slow burn (6× over 6 h) creates a ticket.

### 15.5 Alerts

| Alert | Condition | Severity | Route |
| --- | --- | --- | --- |
| API 5xx | > 2% for 5 min | Sev 1 | Page |
| TTFT burn | Fast burn | Sev 1 | Page |
| All providers failing | `ai.breaker_open` = all for `fast` tier for 2 min | Sev 1 | Page |
| DB CPU | > 80% for 15 min | Sev 2 | Ticket + Teams |
| DB storage | > 85% | Sev 2 | Ticket |
| DB replication lag | > 60 s | Sev 2 | Teams |
| DLQ | > 0 messages on any queue | Sev 3 | Teams |
| Daily challenge job | Failed or not completed by 00:30 UTC | Sev 2 | Teams |
| WAF | Blocked requests > 5× baseline | Sev 3 | Teams |
| Token spend | Daily spend > 130% of the 7-day average | Sev 2 | Teams + email |
| Guardrail spike | `guard.blocked_total` > 5× baseline | Sev 3 | Security channel |
| Certificate expiry | < 21 days | Sev 3 | Ticket |
| Leaderboard drift | Rebuild job finds > 0.5% of entries differ | Sev 3 | Ticket |

### 15.6 Dashboards

1. **Service health:** golden signals per container, revisions, and replica counts.
2. **AI quality and cost:** TTFT, provider mix, fallbacks, tokens, cost per learner per day, groundedness, and abstention.
3. **RAG:** retrieval latency, top-score distribution, and abstentions by concept (content gap list).
4. **Learning and growth:** the MVP success metrics from README (retention, sessions per week, onboarding, quiz and challenge completion).
5. **Data tier:** PostgreSQL, Redis, Qdrant, and Service Bus.
6. **Security:** WAF, auth failures, guardrail blocks, and admin actions.

Synthetic monitoring uses an App Insights standard test every 5 min from 5 locations against `/health` and a scripted sign-in plus `GET /api/v1/dashboard` with a test account.

---

## 16. Disaster Recovery Architecture

### 16.1 Objectives by component

| Component | Data role | Backup and replication | RPO | RTO |
| --- | --- | --- | --- | --- |
| PostgreSQL | System of record | Zone-redundant HA (synchronous). PITR 35 days. Geo-redundant backup. Cross-region read replica at the Scale phase. | 0 zonal, ≤ 15 min regional (with replica ≈ 1 min) | 2 min zonal, 1 h regional |
| Blob Storage | Originals, snapshots | GZRS + soft delete 30 days + versioning + immutability policy on `audit/` | ≤ 15 min | 1 h |
| Qdrant | Derived | Daily snapshots to Blob (`qdrant-snapshots/`, 14 kept), replication factor 2 | 24 h (rebuildable to 0) | 2 h from snapshot, 6 h full rebuild |
| Redis | Derived | Zone-redundant HA. No backup needed. | n/a | Rebuild job 10 min |
| Service Bus | In-flight jobs | Geo-disaster recovery alias (Premium). On Standard, jobs are reconstructable from `ingestion_jobs` rows. | Minutes | 30 min |
| Key Vault | Secrets | Built-in regional pairing, soft delete + purge protection | 0 | Automatic |
| Container images | Artifacts | ACR Premium with geo-replication | 0 | 0 |
| Configuration | Infrastructure | Bicep in git, environment parameters in git | 0 | 30 min redeploy |
| Clerk, Stripe | External | Vendor SLAs | n/a | n/a |

### 16.2 Regional topology

Primary is **West Europe** and the secondary is **North Europe**. Both are parameters in the Bicep files, so they can be changed (for example to UK South with Sweden Central for UK residency).

```mermaid
flowchart TB
    FD["Azure Front Door<br/>global, priority-based origin groups"]
    subgraph P["Primary: West Europe (active)"]
        PW["web, api, worker<br/>3 zones"]
        PPG[("PostgreSQL<br/>zone-redundant HA")]
        PRD[("Redis HA")]
        PBL[("Blob GZRS")]
        PQD[("Qdrant Cloud<br/>3 nodes")]
    end
    subgraph S["Secondary: North Europe (warm standby at Scale, cold in MVP)"]
        SW["web, api, worker<br/>min replicas 1"]
        SPG[("PostgreSQL<br/>cross-region read replica")]
        SRD[("Redis<br/>empty, rebuilt on failover")]
        SBL[("Blob<br/>GZRS secondary")]
        SQD[("Qdrant<br/>restored from snapshot")]
    end
    FD -->|"priority 1"| PW
    FD -.->|"priority 2"| SW
    PPG -->|"async replication"| SPG
    PBL -->|"geo-replication"| SBL
    PQD -->|"daily snapshot via Blob"| SQD
```

### 16.3 Failover runbook (regional)

**Declare.** Primary is unavailable for more than 15 min with no Azure ETA, or a data-corruption incident has occurred. The incident commander approves the failover.

1. Freeze deployments. Post the status page notice.
2. **PostgreSQL.** Promote the North Europe read replica (`az postgres flexible-server replica stop-replication`). Without a replica (MVP), geo-restore from backup to North Europe, which takes about 1 h.
3. **Blob.** Initiate customer-managed account failover (`az storage account failover`) if primary storage is down.
4. **Qdrant.** Restore the latest snapshot to the North Europe cluster. Then run the `reindex --since <snapshot_time>` job, which re-embeds chunks created after the snapshot from PostgreSQL.
5. **Configuration.** Point `DATABASE_URL`, `QDRANT_URL`, and Service Bus to the secondary. These are pre-staged Key Vault secrets in the secondary vault. Restart revisions.
6. **Redis.** Run the `leaderboard-rebuild` job.
7. **Front Door.** Disable the primary origin, or let health probes fail it over. Verify synthetic tests pass.
8. Run smoke tests: sign-in, tutor stream, quiz grade, leaderboard.
9. **Failback.** Rebuild the primary from the secondary (new replica in the reverse direction), schedule a maintenance window, and reverse the steps.

### 16.4 Operational recovery scenarios

| Scenario | Recovery |
| --- | --- |
| Bad migration or data corruption | PITR restore to a new server at T-1 min, compare, then swap the connection string or replay. Expand/contract migrations (section 17.6) make rollback rarely necessary. |
| Accidental content publish or delete | Workflow restore (section 9.3). Blob soft delete and versioning. |
| Qdrant collection corrupted or bad embedding model | Alias back to the previous collection (section 11.5), or rebuild from PostgreSQL |
| Leaderboard corruption | `leaderboard-rebuild` job from `xp_events` |
| Provider outage | Automatic fallback (section 8.3). No DR action needed. |
| Clerk outage | Existing sessions keep working until token expiry (60 s, refresh fails), so sign-in is unavailable. Status banner. Vendor SLA. |
| Compromised secret | Rotate in Key Vault, restart revisions (they use Key Vault references), audit access logs |

### 16.5 Testing

- Quarterly: PITR restore drill to a scratch server, with row-count and checksum verification.
- Quarterly: Qdrant restore from snapshot plus incremental reindex, then the retrieval eval suite.
- Twice a year: full regional failover game day in staging, plus one in production during a maintenance window once warm standby exists.
- Every restore is timed and the RTO is recorded. A miss creates a corrective action.

---

## 17. Deployment Architecture

### 17.1 Azure topology (production, primary region)

```mermaid
flowchart TB
    subgraph Global
        FD["Front Door Premium + WAF<br/>afd-aimentor-prod"]
        DNS["Azure DNS<br/>aimentor.app"]
        ACR["ACR Premium<br/>geo-replicated"]
    end
    subgraph RG["rg-aimentor-prod-weu"]
        subgraph VNET["vnet-aimentor-prod 10.40.0.0/16"]
            subgraph SAPPS["snet-apps 10.40.0.0/23"]
                CAE["Container Apps environment<br/>workload profiles: Consumption + D4"]
                WEB["ca-web"]
                API["ca-api"]
                WRK["ca-worker"]
                JOB["caj-migrate, caj-daily-challenges,<br/>caj-leaderboard-rebuild, caj-season-close,<br/>caj-qdrant-snapshot, caj-reports"]
            end
            subgraph SPE["snet-pe 10.40.4.0/24"]
                PEPG["PE PostgreSQL"]
                PERD["PE Redis"]
                PEBL["PE Blob"]
                PEKV["PE Key Vault"]
                PESB["PE Service Bus"]
                PEAO["PE Azure OpenAI"]
                PEACR["PE ACR"]
            end
            NAT["NAT Gateway<br/>static egress IP"]
        end
        PG[("psql-aimentor-prod")]
        RD[("redis-aimentor-prod")]
        ST[("staimentorprod")]
        KV["kv-aimentor-prod"]
        SB[["sb-aimentor-prod"]]
        AO["oai-aimentor-prod"]
        CS["cs-aimentor-prod"]
        SESS["Dynamic sessions pool<br/>sp-aimentor-python"]
        LA[("log-aimentor-prod")]
        APPI["appi-aimentor-prod"]
        ID["Managed identities<br/>id-api, id-worker, id-jobs"]
    end
    QD[("Qdrant Cloud<br/>Azure West Europe")]

    DNS --> FD
    FD -->|"Private Link"| CAE
    CAE --> WEB
    CAE --> API
    CAE --> WRK
    CAE --> JOB
    PEPG --- PG
    PERD --- RD
    PEBL --- ST
    PEKV --- KV
    PESB --- SB
    PEAO --- AO
    PEACR --- ACR
    API --> SESS
    CAE --> NAT --> QD
    CAE -.-> LA
    CAE -.-> APPI
```

### 17.2 Environments

| Environment | Purpose | Subscription | Data | Scale | Deploy trigger |
| --- | --- | --- | --- | --- | --- |
| `local` | Development | n/a | Docker Compose, seed data, `DEV_AUTH` | 1 | `make up` |
| `preview` | Per-PR review app | `sub-aimentor-nonprod` | Shared staging DB, isolated schema | Scale-to-zero | PR opened |
| `staging` | Integration, load, and DR drills | `sub-aimentor-nonprod` | Synthetic + anonymised snapshot | Production shape, smaller SKUs | Merge to `main` |
| `prod` | Production | `sub-aimentor-prod` | Real | Section 14.2 | Tagged release + approval |

Clerk and Stripe have separate development and production instances. Preview and staging use Clerk development and Stripe test mode.

### 17.3 Infrastructure as code

Bicep, deployed through `az deployment sub create` from CI with OIDC federated credentials (no stored cloud secrets).

```text
infrastructure/
├── compose.yaml                       # local (section 17.8)
├── bicep/
│   ├── main.bicep                     # subscription scope: RGs, then modules
│   ├── params/{staging,prod}.bicepparam
│   └── modules/
│       ├── network.bicep              # VNet, subnets, NSGs, NAT, private DNS zones
│       ├── frontdoor.bicep            # AFD profile, endpoints, routes, WAF policy, Private Link origins
│       ├── containerapps-env.bicep    # environment, workload profiles, Log Analytics link
│       ├── containerapp.bicep         # generic app: image, env, secrets (KV refs), scale rules, probes
│       ├── containerapp-job.bicep     # cron / manual jobs
│       ├── sessions-pool.bicep        # dynamic sessions Python pool, egress disabled
│       ├── postgres.bicep             # Flexible Server, HA, Entra auth, extensions, PgBouncer, replica
│       ├── redis.bicep                # Azure Managed Redis
│       ├── storage.bicep              # GZRS, containers, versioning, soft delete, Defender
│       ├── servicebus.bicep           # namespace, queues, topic, subscriptions, DLQ
│       ├── keyvault.bicep             # RBAC mode, purge protection
│       ├── openai.bicep               # account, deployments (chat-fast, chat-reasoning, chat-code, embed-small)
│       ├── contentsafety.bicep
│       ├── monitoring.bicep           # LA workspace, App Insights, alerts, action groups, workbooks
│       ├── identity.bicep             # user-assigned identities + role assignments
│       └── acr.bicep
└── qdrant/
    └── terraform/                     # Qdrant Cloud provider: cluster, API keys (only non-Azure IaC)
```

Naming follows `<type>-aimentor-<env>-<region>` per the Azure Cloud Adoption Framework abbreviations. Required tags: `app=aimentor`, `env`, `owner`, `costCenter`, `dataClass`.

### 17.4 Container images

One backend image runs `api`, `worker`, and `jobs` with different commands. One frontend image runs `web`.

| Image | Base | Command | Health probes |
| --- | --- | --- | --- |
| `aimentor/api` | `python:3.12-slim` (distroless at the Scale phase) | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips='*'` | liveness `GET /health/live`, readiness `GET /health/ready` (DB + Redis), startup 60 s |
| `aimentor/api` as worker | same | `python -m app.worker` | liveness via a heartbeat file, TCP not exposed |
| `aimentor/api` as job | same | `python -m app.jobs <name>` | n/a |
| `aimentor/web` | `node:22-alpine` multi-stage (existing) | `node server.js` | `GET /api/healthz` (Next route handler) |

Required changes to the existing Dockerfiles:

- **`backend/Dockerfile`**: remove `alembic upgrade head` from `CMD`. Migrations run as `caj-migrate` (section 17.6). Running migrations from many replicas at once races. Add `--proxy-headers`. Install from a lock file (`uv pip sync` from `uv.lock`) for reproducible builds.
- **Split `/health`** into `/health/live` (process only) and `/health/ready` (DB `select 1`, Redis `PING`). The existing `/health` stays as an alias for `ready`.
- **`frontend/Dockerfile`**: the run stage copies `public/`, which does not exist yet. Create `frontend/public/` or guard the copy. Pass `NEXT_PUBLIC_*` values as build args, because Next.js inlines them at build time. Build once per environment, or use runtime config for anything that differs.

### 17.5 CI/CD pipeline

```mermaid
flowchart LR
    PR["Pull request"] --> CI1["Lint and type<br/>ruff, mypy, tsc, eslint"]
    CI1 --> CI2["Tests<br/>pytest unit + integration (Postgres, Qdrant, Redis service containers),<br/>domain coverage 90%"]
    CI2 --> CI3["Contract<br/>OpenAPI → TS types, diff check"]
    CI3 --> CI4["Security<br/>pip-audit, npm audit, gitleaks, Bicep what-if + PSRule"]
    CI4 --> CI5["Build images<br/>tag = git SHA, SBOM, Trivy"]
    CI5 --> CI6{"AI paths changed?"}
    CI6 -->|"yes"| EV["Eval suite<br/>Langfuse datasets"]
    CI6 -->|"no"| PV
    EV --> PV["Preview environment"]
    PV --> MERGE["Merge to main"]
    MERGE --> STG["Deploy staging<br/>migrate job, then new revision 100%"]
    STG --> E2E["Playwright E2E + k6 smoke"]
    E2E --> TAG["Release tag vX.Y.Z"]
    TAG --> APPROVE["Manual approval"]
    APPROVE --> PMIG["Prod: run caj-migrate (expand)"]
    PMIG --> CANARY["New revision 10% traffic, 15 min"]
    CANARY --> CHECK{"SLO checks<br/>5xx, TTFT, errors"}
    CHECK -->|"pass"| FULL["100% traffic, old revision kept 24 h"]
    CHECK -->|"fail"| RB["Shift to previous revision"]
```

The pipeline runs on GitHub Actions with `azure/login` OIDC. Images are promoted by digest. Production never rebuilds.

### 17.6 Database migrations

- Alembic runs only in the `caj-migrate` job, before the traffic shift, under the `id-jobs` identity with a role that has DDL rights. App identities have DML only.
- **Expand/contract.**
  - Release N adds new nullable columns or tables and writes to both shapes.
  - Release N+1 backfills (as a job) and reads the new shape.
  - Release N+2 drops the old shape.

  Any revision can therefore roll back without touching the database.
- Migrations set `lock_timeout = '5s'` and `statement_timeout = '15min'`. Indexes on large tables use `CREATE INDEX CONCURRENTLY` in their own migration with `transaction_per_migration`.
- `Base.metadata.create_all` in `main.py` lifespan stays for `development` and `test` only (existing behaviour). `seed_catalog` stays idempotent.

### 17.7 Configuration matrix

| Setting | local | staging | prod | Source |
| --- | --- | --- | --- | --- |
| `APP_ENV` | development | staging | production | env |
| `DEV_AUTH` | true | false | false (guarded) | env |
| `DATABASE_URL` | compose Postgres | Entra-auth DSN via PgBouncer :6432 | same | Key Vault ref |
| `QDRANT_URL` / `QDRANT_API_KEY` | `http://qdrant:6333` / none | Qdrant Cloud staging | Qdrant Cloud prod | Key Vault ref |
| `REDIS_URL` ★ | `redis://redis:6379` | Entra-auth Managed Redis | same | Key Vault ref |
| `SERVICEBUS_NAMESPACE` ★ | emulator | `sb-aimentor-stg` | `sb-aimentor-prod` | env |
| `BLOB_ACCOUNT_URL` ★ | Azurite | `https://staimentorstg.blob…` | `https://staimentorprod.blob…` | env |
| `AZURE_OPENAI_ENDPOINT` ★, deployments | optional | set | set | env |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | optional | set | set | Key Vault ref |
| `CONTENT_SAFETY_ENDPOINT` ★ | unset (skip) | set | set | env |
| `SANDBOX_POOL_ENDPOINT` ★ | unset (subprocess) | set | set (required) | env |
| `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`, `CLERK_ALLOWED_AZP` ★ | unset | Clerk dev | Clerk prod | Key Vault ref / env |
| `STRIPE_*` | unset | test mode | live | Key Vault ref |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` ★ | unset | set | set | env |
| `LANGFUSE_*` | optional | set | set | Key Vault ref |
| `CORS_ORIGINS` | `http://localhost:3000` | empty (same origin) | empty | env |
| `RATE_LIMIT_PER_MINUTE`, `AI_RATE_LIMIT_PER_MINUTE` | defaults | defaults | Replaced by plan classes (section 12.3) | env |

★ = new setting to add to `app/core/config.py`. Extend `production_guard` to require `REDIS_URL`, `SANDBOX_POOL_ENDPOINT`, and `CLERK_ALLOWED_AZP` in production.

### 17.8 Local development (Docker Compose target)

The current `infrastructure/compose.yaml` runs Postgres, Qdrant, and the API. The target adds Redis, Azurite, the Service Bus emulator, the worker, and the web app:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment: { POSTGRES_USER: mentor, POSTGRES_PASSWORD: mentor, POSTGRES_DB: mentor }
    ports: ["5432:5432"]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U mentor -d mentor"], interval: 5s, retries: 12 }
    volumes: [postgres:/var/lib/postgresql/data]

  qdrant:
    image: qdrant/qdrant:v1.13.4
    ports: ["6333:6333"]
    volumes: [qdrant:/qdrant/storage]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    ports: ["10000:10000"]

  servicebus:
    image: mcr.microsoft.com/azure-messaging/servicebus-emulator:latest
    environment: { ACCEPT_EULA: "Y", SQL_SERVER: sqledge, MSSQL_SA_PASSWORD: "Mentor!12345" }
    volumes: [./servicebus-config.json:/ServiceBus_Emulator/ConfigFiles/Config.json]
    ports: ["5672:5672"]
    depends_on: [sqledge]

  sqledge:
    image: mcr.microsoft.com/azure-sql-edge:latest
    environment: { ACCEPT_EULA: "Y", MSSQL_SA_PASSWORD: "Mentor!12345" }

  api: &backend
    build: { context: ../backend }
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    environment: &backend-env
      APP_ENV: development
      DEV_AUTH: "true"
      DATABASE_URL: postgresql+psycopg://mentor:mentor@postgres:5432/mentor
      QDRANT_URL: http://qdrant:6333
      REDIS_URL: redis://redis:6379/0
      BLOB_CONNECTION_STRING: "UseDevelopmentStorage=true;DevelopmentStorageProxyUri=http://azurite"
      SERVICEBUS_CONNECTION_STRING: "Endpoint=sb://servicebus;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"
      CORS_ORIGINS: http://localhost:3000
    ports: ["8000:8000"]
    depends_on: { postgres: { condition: service_healthy }, redis: { condition: service_started } }

  worker:
    <<: *backend
    command: python -m app.worker
    ports: []

  web:
    build: { context: ../frontend }
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_DEV_AUTH: "true"
    ports: ["3000:3000"]
    depends_on: [api]

volumes:
  postgres:
  qdrant:
```

Running migrations inside the API command is acceptable locally because there is one replica.

### 17.9 Release and rollback

- Container Apps runs in **multiple revision mode**. Each deploy creates a revision labelled with the git SHA.
- Canary: 10% for 15 min, then 100%. The automated gate queries App Insights for 5xx rate and TTFT p95 against the previous revision.
- Rollback: `az containerapp ingress traffic set --revision-weight <previous>=100`, which takes under 1 minute. The database is compatible by construction (section 17.6).
- Feature flags (Azure App Configuration, or a `feature_flags` table cached in Redis) gate new learner-facing features by percentage and plan, independently of deploys.

---

## 18. Appendices

### 18.1 Implementation roadmap

The work items are ordered so that each phase can ship on its own. Durations assume 3 to 4 engineers, matching the 8 to 12 week MVP estimate in README.

| Phase | Weeks | Work items |
| --- | --- | --- |
| **0. Foundations** | 1–2 | Bicep modules for staging. Container Apps for web and API. Front Door. Key Vault + managed identities. CI pipeline with tests, contract check, and image build. Migration job. Health endpoint split. Remove migrations from the API `CMD`. |
| **1. Identity and gateway** | 2–3 | Clerk in the frontend (`ClerkProvider`, `middleware.ts`, Bearer tokens). `azp` validation. Redis rate limiting by user ID. Problem+json errors. Request context and App Insights. `country_code` and preferences. Onboarding endpoints. |
| **2. Retrieval for real** | 3–5 | `VectorStore` port + Qdrant adapter. Collections bootstrap job. Blob uploads with SAS. Service Bus + worker. Ingestion pipeline (PDF, DOCX, PPTX, MD, URL). Hybrid search + rerank. Tutor and research use Qdrant. Retrieval logs. Retrieval eval suite. |
| **3. Streaming tutor** | 4–6 | Async `ProviderRouter` with Azure OpenAI, tiers, breaker, and budgets. `/chat/stream` SSE. `ChatStream` component with a citations panel. Prompt registry with style, personality, and depth blocks. Content Safety. Langfuse tracing with prompt versions. |
| **4. Knowledge management** | 5–8 | KMS tables and workflow state machine. Admin API and portal (library, upload, review queue, diff, taxonomy, curriculum builder). Catalog seeding into the KMS. AI content generation jobs. |
| **5. Gamification** | 6–9 | XP ledger idempotency and outbox. Redis leaderboards (global, country, friends, weekly). Titles. Daily challenge job and endpoints. Season close. Anti-abuse job. |
| **6. Hardening and launch** | 9–12 | ACA dynamic sessions sandbox. i18n (fr, es) UI and content translation workflow. DSAR export and delete. Alerts and SLO dashboards. Load test at 2× MVP. DR drill (PITR + Qdrant restore). Pen test. Production go-live. |
| **Post-MVP** | — | Warm standby region, PTU, voice, notebooks pool, mobile apps, APIM for partners |

### 18.2 Architecture decision records

The files in [adr/](adr/README.md) are the accepted records for the running system, and they use their own numbers. The table below is the target list. ADR-03 in this table (Next.js on Container Apps) is not [ADR 0006](adr/0006-azure-container-apps.md), which keeps the studio on Vercel.

| ADR | Title | Status |
| --- | --- | --- |
| ADR-01 | Modular monolith with a separate worker | Accepted |
| ADR-02 | Azure Container Apps as the compute platform | Accepted |
| ADR-03 | Host Next.js on Container Apps instead of Vercel | Accepted |
| ADR-04 | PostgreSQL as the system of record, Qdrant derived | Accepted |
| ADR-05 | Qdrant Cloud on Azure. ADR-05b: self-hosted on AKS if a private-network requirement appears. | Accepted |
| ADR-06 | Azure OpenAI primary with multi-provider fallback | Accepted |
| ADR-07 | ACA dynamic sessions for code execution | Accepted |
| ADR-08 | Service Bus for jobs, Redis for ephemeral state | Accepted |
| ADR-09 | SSE for streaming | Accepted |
| ADR-10 | Clerk identity with database-authoritative roles | Accepted |
| ADR-11 | No API Management until external API consumers exist | Accepted |
| ADR-12 | Hybrid dense and sparse retrieval with reranking | Accepted |
| ADR-13 | Leaderboards on Redis ZSETs, rebuilt from the `xp_events` ledger | Accepted |
| ADR-14 | Expand/contract migrations through a dedicated job | Accepted |

ADR files go in `docs/adr/NNNN-title.md` using the Michael Nygard template: context, decision, consequences.

### 18.3 Glossary

| Term | Meaning |
| --- | --- |
| ACA | Azure Container Apps |
| Concept graph | `concepts` and `concept_relations`. Prerequisite and related links that drive plans and recommendations. |
| Four-eyes rule | The author of a version cannot approve it |
| Grounded | An answer whose claims cite at least one supplied source |
| KMS | Knowledge Management System, the admin portal and content pipeline |
| Mastery | 0 to 100 score per learner per concept, from `domain/mastery` |
| PTU | Provisioned throughput units, reserved Azure OpenAI capacity |
| RRF | Reciprocal rank fusion, which merges dense and sparse result lists |
| SSE | Server-Sent Events |
| TTFT | Time to first token |
