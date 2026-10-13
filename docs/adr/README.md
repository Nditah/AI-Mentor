# Architecture Decision Records

Each file stands alone. ADRs 0001–0010 and 0012 describe decisions already in the AI Mentor codebase. ADR 0011 and ADRs 0013–0026 are accepted target decisions for the multi-application platform and are not yet implemented. ADR 0027 is proposed. Names used in 0013–0027 (applications, roles, scopes, modules, events, schemas, releases R1–R5) come from [docs/platform/README.md](../platform/README.md), the canonical vocabulary.

[SystemArchitecture.md](../SystemArchitecture.md) section 18.2 lists a separate target set. Those numbers are not these files. ADR 0006 keeps the studio on Vercel. The target list's ADR-03 would move Next.js onto Container Apps, and it is not accepted yet.

In ADRs 0001–0012, "studio" means the learner frontend. From ADR 0013 on, that app is the Learner App and "studio" means Content Studio only.

| ADR | Decision |
| --- | --- |
| [0001](0001-nextjs-studio.md) | Next.js App Router for the studio (amended 2026-10-13: Next 16) |
| [0002](0002-fastapi-modular-monolith.md) | FastAPI modular monolith for the mentor |
| [0003](0003-postgresql-system-of-record.md) | PostgreSQL as the system of record |
| [0004](0004-qdrant-vector-index.md) | Qdrant as the vector index, with a hash fallback (amended 2026-10-13) |
| [0005](0005-clerk-authentication.md) | Clerk for identity, Postgres for roles (amended 2026-10-13) |
| [0006](0006-azure-container-apps.md) | Azure Container Apps for the API, Vercel for the studio (amended 2026-10-13) |
| [0007](0007-rag-architecture.md) | Grounded retrieval over uploaded documents (amended 2026-10-13) |
| [0008](0008-gamification-engine.md) | Deterministic XP, streaks, and SM-2 (amended 2026-10-13) |
| [0009](0009-knowledge-repository.md) | Catalog file plus Postgres curriculum rows (amended 2026-10-13) |
| [0010](0010-ai-tutor-architecture.md) | Policy-owned tutor with specialist agents |
| [0011](0011-target-database-architecture.md) | Target database architecture (accepted 2026-10-13; amends 0003) |
| [0012](0012-separate-admin-app.md) | Separate admin app on its own subdomain, one design system (amends 0001) |
| [0013](0013-five-applications-shared-platform.md) | Five applications on one shared platform (target; amends 0001, 0012) |
| [0014](0014-monorepo-shared-packages.md) | Monorepo with shared front-end packages (target) |
| [0015](0015-organisation-tenancy.md) | Organisation tenancy and org-unit hierarchy (target) |
| [0016](0016-scoped-rbac-abac.md) | Scoped RBAC with ABAC policy evaluation (target; amends 0005; replaces the linear role rank) |
| [0017](0017-bounded-contexts-platform-services.md) | Bounded contexts and shared platform services (target; amends 0002) |
| [0018](0018-event-outbox.md) | Event-driven integration through a transactional outbox (target) |
| [0019](0019-content-studio-releases.md) | Content Studio, content ownership, and versioned content releases (target; amends 0009) |
| [0020](0020-knowledge-graph-backbone.md) | Knowledge graph as the curriculum and adaptivity backbone (target) |
| [0021](0021-learner-record-ownership.md) | Learner record ownership and data controllership across tenants (target) |
| [0022](0022-configurable-ai-mentor.md) | Configurable AI mentor: modes and personas as policy profiles (target; amends 0010) |
| [0023](0023-localisation-architecture.md) | Localisation architecture for UI, content, AI, assessments, and reports (target) |
| [0024](0024-platform-gamification.md) | Platform-wide gamification with scoped leaderboards (target; amends 0008) |
| [0025](0025-assessment-platform.md) | Assessment platform with AI-assisted marking and human override (target) |
| [0026](0026-interoperability-standards.md) | Interoperability standards: SSO, SCIM, LTI 1.3, OneRoster, xAPI (target) |
| [0027](0027-extension-points.md) | Extension points for marketplace, mobile apps, and AI agent orchestration (proposed) |
| [0028](0028-sandbox-runner-pool.md) | Coding-lab runner: a gVisor or Firecracker pool we operate (accepted 2026-10-13; supersedes SAD ADR-07) |
