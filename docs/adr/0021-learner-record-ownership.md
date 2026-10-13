# ADR 0021 — Learner record ownership and data controllership across tenants

- Status: Accepted (target architecture; not yet implemented)
- Date: 2026-10-13

## Context

In v1 every learner is a self-registered individual. AI Mentor is the controller of all personal data, and `identity.erase_user()` (ADR 0011) removes a person across schemas.

With tenancy ([ADR 0015](0015-organisation-tenancy.md)), the same person can be a self-registered learner who later joins a university cohort, or a student whose account was created by the university through SSO or SCIM. Universities and employers act as controllers for their students and staff and expect AI Mentor to process data on their instructions. They also need grades and attendance to survive a student's departure. Learners expect mastery and badges earned on their own time to stay theirs.

## Problem

Decide who owns which parts of a learner's data, what an organisation can see, what happens when a membership ends, and how erasure works for each account type.

## Decision

**Account types** (`identity.users.account_type`):

| Type | Created by | Home tenant | Controller | Joins other organisations |
| --- | --- | --- | --- | --- |
| `personal` | Self sign-up | Consumer organisation | AI Mentor | Yes, by invite or enrolment code, with consent at join |
| `managed` | Organisation provisioning (SSO JIT, SCIM, CSV import, instructor creation) | The provisioning organisation | The organisation; AI Mentor is processor under a data processing agreement | No |

**Two records.**

| Record | Contents | Owner | Stored with |
| --- | --- | --- | --- |
| Learning record | Mastery, XP, streaks, badges, practice history, flashcards, tutor conversations | The account. For `managed`, the organisation | `tenant_id` of the context where it was earned |
| Academic record | Enrolments through a cohort, cohort plans, assignments, submissions, grades, attendance, instructor notes, risk signals | The organisation that issued the work | That organisation's `tenant_id` |

**Visibility to an organisation** for a personal-account member:

1. Only concepts in curricula the organisation assigned (through cohort plans or organisation enrolments).
2. Only while the membership is `active`.
3. Only within the consent scope accepted at join, recorded in `identity.consents` with the organisation id: `profile_basic` and `assigned_progress` (both required to join), `mastery_detail`, `tutor_summaries` (never raw conversations), `leaderboard_listing`.
4. Learning earned in the consumer organisation before joining is never visible unless the learner shares it explicitly per item.

The policy engine ([ADR 0016](0016-scoped-rbac-abac.md)) evaluates `consent granted` as a context attribute; repositories never bypass it.

**Membership end.** When a personal account leaves, the organisation keeps the academic record (it is the organisation's) and loses access to the learning record immediately. When a managed account is deprovisioned, the account is suspended; the organisation's retention policy decides deletion.

**Learning passport.** Any personal account, and a managed account if the organisation policy `records.passport_export` is on, can export verified achievements as Open Badges 3.0 credentials signed by AI Mentor and a JSON transcript of mastery per concept. Badges issued in an organisation context name that organisation as the achievement context.

**Erasure** (`identity.account.erased`):

| Account type | Request from | Effect |
| --- | --- | --- |
| `personal` | The learner | AI Mentor erases the learning record everywhere, including Qdrant and blob storage. Academic records held by organisations are pseudonymised (name and email replaced; grades kept) and each organisation is notified to handle its own obligations as controller |
| `managed` | The organisation (on its own decision or a forwarded learner request) | AI Mentor erases within 30 days as processor. A learner request received directly is routed to the organisation's compliance officer and not actioned by AI Mentor alone |

## Alternatives considered

| Alternative | Why it lost |
| --- | --- |
| The organisation owns everything a member does | A self-registered learner who joins a course would lose their own history on leaving, and would be deterred from joining. |
| The learner owns everything, including grades | Institutions have legal duties to keep assessment records. A learner could not be allowed to erase a grade from a transcript. |
| Separate accounts per organisation | Duplicates mastery, splits XP and streaks, and forces multiple sign-ins. One person, many memberships is the README model. |
| AI Mentor as joint controller for managed accounts | Institutions' procurement and DPAs expect a processor relationship. |

## Trade-off analysis

Splitting records by kind rather than by tenant makes queries carry two filters (tenant and consent) and makes the consent screen at join a product requirement, not a formality. It is the only split under which both learners and institutions can keep what they need.

Pseudonymising rather than deleting academic records on personal erasure leaves rows that still describe a person's performance. That is lawful only because the organisation is controller of those rows; the organisation is notified so it can decide.

## Consequences

- `identity.users` gains `account_type` and `home_tenant_id` (R1). Managed accounts cannot create memberships elsewhere (database check plus API rule).
- The Institution App shows the consent scope per member; the Learner App shows "who can see my progress" per organisation.
- Audit records every organisation read of a personal account's learning record.
- [09-security-model.md](../platform/09-security-model.md) carries the DPA, sub-processor, and retention details.

## Future considerations

- Account conversion: a managed account that leaves may claim a new personal account seeded from its learning passport.
- Verifiable credential wallets and the European Learning Model for cross-border recognition.
