# Architecture Decision Records

These records describe decisions that are already in the AI Mentor codebase. Each file stands alone.

[SystemArchitecture.md](../SystemArchitecture.md) section 18.2 lists a separate target set. Those numbers are not these files. ADR 0006 keeps the studio on Vercel. The target list's ADR-03 would move Next.js onto Container Apps, and it is not accepted yet.

| ADR | Decision |
| --- | --- |
| [0001](0001-nextjs-studio.md) | Next.js 15 App Router for the studio |
| [0002](0002-fastapi-modular-monolith.md) | FastAPI modular monolith for the mentor |
| [0003](0003-postgresql-system-of-record.md) | PostgreSQL as the system of record |
| [0004](0004-qdrant-vector-index.md) | Qdrant as the vector index, with a hash fallback |
| [0005](0005-clerk-authentication.md) | Clerk for identity, Postgres for roles |
| [0006](0006-azure-container-apps.md) | Azure Container Apps for the API, Vercel for the studio |
| [0007](0007-rag-architecture.md) | Grounded retrieval over uploaded documents |
| [0008](0008-gamification-engine.md) | Deterministic XP, streaks, and SM-2 |
| [0009](0009-knowledge-repository.md) | Catalog file plus Postgres curriculum rows |
| [0010](0010-ai-tutor-architecture.md) | Policy-owned tutor with specialist agents |
| [0011](0011-target-database-architecture.md) | Target database architecture (proposed; amends 0003) |
| [0012](0012-separate-admin-app.md) | Separate admin app on its own subdomain, one design system (amends 0001) |
