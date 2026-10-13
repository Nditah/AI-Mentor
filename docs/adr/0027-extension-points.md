# ADR 0027 — Extension points for marketplace, mobile apps, and AI agent orchestration

- Status: Proposed
- Date: 2026-10-13

## Context

The v2 direction names three later capabilities: a content marketplace where third parties sell courses and learning paths, native mobile apps (Learner first, then Instructor), and AI agents that act on a person's behalf (for example "schedule a revision plan for my cohort before the exam"). [docs/platform/README.md](../platform/README.md#releases) places Learner mobile apps in R4 and the marketplace, agent orchestration, and Instructor mobile in R5.

None of these is designed in detail yet. Some decisions taken now (tenancy, content ownership, permissions, events) either keep them cheap or make them expensive. This record names the extension points so R1–R3 work does not close them off. It is proposed, not accepted: each area gets its own ADR before build.

## Problem

Decide what the platform must guarantee now so that a marketplace, mobile clients, and agent orchestration can be added without redesigning tenancy, authorisation, or content.

## Decision

**Marketplace.**

1. Sellers are organisations of kind `publisher`. They author in an `org` workspace with the full Content Studio workflow ([ADR 0019](0019-content-studio-releases.md)).
2. A listing points at a course or path release, with licence terms (per seat, per organisation, per learner purchase, term length), price per currency, and allowed locales.
3. Buying a listing creates a licence entitlement in `commerce`; the buyer gets read access to the release and may overlay it, but cannot derive it unless the terms allow.
4. Revenue share, payouts, and tax use Stripe Connect; the split is a commercial term per publisher, recorded on the listing.
5. Listings pass a platform review (rights, quality, safety) before going live; master-workspace quality rules apply.
6. Proposed new schema `marketplace` (`publishers`, `listings`, `listing_releases`, `orders`, `payouts`). It is not in the canonical schema list until this record is accepted.

**Mobile apps.**

1. The API stays the only business logic. Mobile clients call the same `/api/v1` roots with their own Clerk authorised party and the Learner App audience ([ADR 0013](0013-five-applications-shared-platform.md)).
2. Clerk native SDKs (iOS, Android, or Expo) handle sign-in, including enterprise SSO.
3. Push notifications are a `notification` channel; device tokens are stored per person.
4. Offline support is later: a read cache of the pinned release for downloaded modules, and an outbox of practice results synced on reconnect, idempotent on client-generated ids. Graded assessments are never offline.
5. React Native with Expo is the default candidate so `packages/api-client` and `packages/i18n` are reusable.

**AI agent orchestration.**

1. An agent acts on behalf of one person and holds exactly that person's permissions in the active tenant, never more. Authorisation goes through the same policy engine ([ADR 0016](0016-scoped-rbac-abac.md)); the subject carries `acting_via = agent:<agent_id>`.
2. Agents use tools from a registry. Each tool declares the permission it needs, its inputs and outputs, and whether it reads or writes.
3. Any write (creating a cohort plan, sending a message, changing a grade) requires explicit human approval in the UI before execution. Grade changes and publishing are never agent-executable.
4. Every tool call is audited with the agent, the person, the prompt release, and the approval.
5. Agents run in the `tutor` module's orchestration layer and call models through `ai_gateway`; they never receive database handles or shells (ADR 0010).

**Guarantees required now (R1–R3).** Every permission is server-side; every write endpoint is idempotent with a client-supplied key; every resource is addressable by a stable id; events are published for state changes; content releases are immutable; licences are entitlements, not hard-coded plan checks.

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| Design the marketplace now | No publisher demand data yet; detailed terms would be guesses. |
| Mobile web only | Push notifications, offline study, and app-store discovery matter for daily practice; the API-first rule keeps native cheap. |
| Agents with a service account and broad permissions | Privilege escalation through prompt injection; agents must be bounded by the person they act for. |
| Autonomous agent writes without approval | Unreviewed actions on learners' records and communications. |

## Trade-off analysis

Requiring idempotency keys and stable ids on every write costs a little in R1–R3 and removes the main obstacle to offline mobile sync and agent retries. Keeping the marketplace on the existing workspace and licence model limits what publishers can do (no custom player, no external hosting) in exchange for one content pipeline.

## Consequences

- Reviewers of R1–R3 changes check the guarantees above.
- Three follow-up ADRs are expected: marketplace (before R5), mobile clients (before R4), agent orchestration (before R5).

## Future considerations

- A partner API with OAuth client credentials for publishers and integrators (R5).
- Model Context Protocol servers exposing the tool registry to external agents, under the same per-person authorisation.
