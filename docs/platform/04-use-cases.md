# AI Mentor platform: Use cases (v2.0)

| Field | Value |
| --- | --- |
| Document | 04 Use cases |
| Version | 2.0 |
| Date | 13 October 2026 |
| Status | Draft for review. Target behaviour; most of it is not built yet |
| Owner | Product (CPO), with Learning (CLO) and Enterprise Architecture |
| Related | [README.md](README.md) (canonical vocabulary), [02-prd.md](02-prd.md), [03-srs.md](03-srs.md), [05-user-stories.md](05-user-stories.md), [10-rbac-matrix.md](10-rbac-matrix.md), [14-content-studio-specification.md](14-content-studio-specification.md), v1 [UseCases.md](../UseCases.md), ADR 0013 to ADR 0027 |

## Change record

| Area | What changed | Why | Impacted systems | Implementation implications |
| --- | --- | --- | --- | --- |
| Use case set | Added 66 use cases across the five applications and the platform (`UC-L`, `UC-I`, `UC-O`, `UC-A`, `UC-C`, `UC-P`). v1 UC-01 to UC-38 kept and assigned to an application | The platform now serves many organisations through five applications (ADR 0013) | All five apps, all backend modules | Every new endpoint, screen, and test case traces to a use case ID in this document |
| Actors | Replaced the four ranked v1 roles with the scoped role IDs from the README and added external systems: customer IdP, external LMS, SCIM client, email and push provider | Roles are now scoped assignments, not a rank (ADR 0016) | `authz`, `identity`, all apps | Use cases name the permission and the attribute conditions; there is no "higher role inherits everything" rule |
| Business rules | Added BR-101 to BR-154 for tenancy, seats, classrooms, assessment, content releases, gamification scopes, personalisation, and platform governance. BR-01 and BR-19 superseded; BR-22 extended | v1 rules covered one learner app with one tenant | `tenancy`, `classroom`, `assessment`, `content`, `gamification`, `personalisation`, `audit`, `config` | Values marked Proposed need product sign-off before the matching SRS requirement is approved |
| Tenancy in flows | Every use case states the tenant context it runs in and how learner-record ownership applies | Organisation tenancy (ADR 0015) and learner record ownership (ADR 0021) | API, RLS policies, events | Tests must run each flow in two tenants and assert no cross-tenant data |
| Template | Kept the v1 template and added two fields: **Permissions** (permission names, scope, ABAC conditions) and **References** (business rules, requirement area, release) | Reviewers need the authorisation decision and the release in the use case itself | Documentation, test plans | 10-rbac-matrix.md must contain every permission named here |
| Traceability | Added a table from use case to app, SRS requirement area, service module, and release | Release planning (R1 to R5) and SRS coverage checks | Roadmap, SRS | Coverage gaps appear as use cases without SRS requirements |

## Relationship to v1 documents

| v1 source | Status under this document |
| --- | --- |
| `UseCases.md` sections 1 to 6 (scope, actors, permissions, business rules, use case map, UC-01 to UC-38) | UC-01 to UC-38 stay valid and keep their IDs. Section 2 (actors) and section 3 (permissions by role) are superseded by [Actors](#3-actors) and the **Permissions** field in each use case. BR-02 to BR-18 and BR-20 to BR-24 stay valid. BR-01 is superseded by BR-109 to BR-111 and ADR 0016. BR-19 is superseded by BR-126. BR-22 is extended by BR-136 |
| `UseCases.md` sections 7 to 11 (stories, traceability, delivery order, open questions) | Retained for the Learner App. v2 user stories are in [05-user-stories.md](05-user-stories.md) |
| `SRS.md` requirement IDs | Referenced where a v1 use case is unchanged. New use cases reference v2 requirement areas in [03-srs.md](03-srs.md) |

## Contents

1. [Scope and conventions](#1-scope-and-conventions)
2. [v1 use cases under v2](#2-v1-use-cases-under-v2)
3. [Actors](#3-actors)
4. [Business rules](#4-business-rules)
5. [Use case map](#5-use-case-map)
6. [Learner App use cases](#6-learner-app-use-cases)
7. [Instructor App use cases](#7-instructor-app-use-cases)
8. [Institution App use cases](#8-institution-app-use-cases)
9. [Admin App use cases](#9-admin-app-use-cases)
10. [Content Studio use cases](#10-content-studio-use-cases)
11. [Platform and system use cases](#11-platform-and-system-use-cases)
12. [Traceability](#12-traceability)
13. [Open questions](#13-open-questions)

---

## 1. Scope and conventions

This document describes how each user group and external system uses the platform described in [README.md](README.md). It covers the Learner App, Instructor App, Institution App, Admin App, Content Studio, and platform behaviour that has no human trigger. It does not describe screens (see 11-ux-specification.md) or API operations (see 08-api-specification.md).

**Template.** Each use case follows the v1 template in `UseCases.md` section 6: the heading carries the ID and name, then Goal, Actors (primary, then supporting; human actors by role ID), Preconditions, Trigger, Main success flow (numbered), Alternate flows (`A<n> (step x)`), Exception flows (`E<n> (step x)`), and Postconditions (including events emitted). Two fields are added: **Permissions** (each permission in `<context>.<resource>:<action>` form, the scope it must be held at, and the ABAC conditions that must pass, ADR 0016) and **References** (business rules, the requirement area prefix in 03-srs.md, and the release). The header fields are written as a list for density; the content is the same as v1.

**Conventions.**

- "The system" means the API and its modules. Apps render and route; they do not decide (README, the five applications).
- Every permission check is deny by default. A refusal returns 403 with a reason code and is written to `authz.decision_log`. Use cases list only refusals that change the flow.
- "Active tenant" is the organisation the request acts in (BR-101). "Scope" is the org unit or workspace a role assignment applies to.
- Permission names, event names, and organisation policy keys that are not in the README are proposed. They must be confirmed in 10-rbac-matrix.md and 06-system-architecture.md before implementation.

---

## 2. v1 use cases under v2

UC-01 to UC-38 remain valid with their v1 flows. They now belong to an application: the Learner App (UC-01 to UC-25), Content Studio (UC-26 to UC-33), and the Admin App (UC-34 to UC-38). The table records what changes for each under tenancy, scoped roles, and the five-application split. Where a new use case extends or replaces part of a v1 use case, the new ID is given.

| v1 ID | Name | App | What changes under v2 | Extended by |
| --- | --- | --- | --- | --- |
| UC-01 | Register an account | Learner App | Creates a `personal` account in the consumer organisation and a `learner` assignment there. Managed accounts never self-register; they are provisioned | UC-P-01, UC-I-01 |
| UC-02 | Sign in | Learner App (and every app) | Sign-in shows the app launcher and opens the last active tenant. An email domain with an SSO connection is redirected to the customer IdP. A user may sign in to any app their assignments open | UC-L-02, UC-P-01 |
| UC-03 | Reset password | Learner App | Applies only to accounts that sign in with a password through Clerk. SSO users are told to reset at their IdP | UC-O-07 |
| UC-04 | Provision and synchronise user identity | Learner App | Roles come from `authz.role_assignments`, never from the webhook or token. Creates `identity.account.created`. JIT provisioning from SSO is a separate path | UC-P-01 |
| UC-05 | Complete the onboarding assessment | Learner App | A managed learner whose cohort plan sets a path skips path selection (step 6). The diagnostic result is part of the learning record | UC-L-03 |
| UC-06 | Manage learning preferences and profile | Learner App | The six v1 preferences map to the five dimensions. Values may be locked or bounded by a cohort or organisation | UC-L-07 |
| UC-07 | Learn through a Socratic tutor conversation | Learner App | Socratic and Direct become a teaching technique inside the `tutor` mode. Assessment integrity mode restricts the flow during graded work | UC-L-06 |
| UC-08 | Receive a grounded answer with citations | Learner App | Retrieval is filtered to published content in the `master` workspace and the active tenant's `org` workspace, and to the release a cohort is pinned to | UC-C-09 |
| UC-09 | Route a request to a specialist agent | Learner App | The orchestrator routes to one of six mentor modes. Organisation policy may disable modes | UC-L-06 |
| UC-10 | Manage conversation history | Learner App | Conversations are part of the learning record (ADR 0021). For a managed account the organisation controls retention | UC-O-11 |
| UC-11 | Enrol in a learning path | Learner App | An enrolment is created in the active tenant. Organisation-assigned enrolments come through a cohort plan and cannot be dropped by the learner | UC-I-04, UC-L-03 |
| UC-12 | Complete a lesson | Learner App | The lesson body comes from the pinned release plus the cohort overlay. Completion emits `learning.lesson.completed` | UC-L-03 |
| UC-13 | Get the next recommendation | Learner App | Due cohort plan items rank ahead of self-directed recommendations. Graph-based ranking is UC-P-05 | UC-P-05 |
| UC-14 | Create a study plan | Learner App | A personal study plan may coexist with cohort plans. It never moves cohort due dates | UC-L-03 |
| UC-15 | Take a quiz | Learner App | Remains practice in `learning`. A graded quiz issued by an instructor is an assessment (UC-L-04) | UC-L-04 |
| UC-16 | Solve a coding exercise | Learner App | Remains practice. Coding assessments use the same sandbox rules (BR-13, BR-14) under `assessment` | UC-L-04 |
| UC-17 | Review flashcards | Learner App | Unchanged. Part of the learning record | none |
| UC-18 | Complete the daily challenge | Learner App | Platform-wide. Seasonal competitions are added | UC-L-08 |
| UC-19 | Award XP, levels, streaks, and badges | Learner App | Owned by `gamification`. BR-02 to BR-06 unchanged. Ledger rows carry the tenant they were earned in (BR-135) | UC-P-03 |
| UC-20 | View the progress dashboard | Learner App | Shows the active tenant's cohort deadlines and released grades beside personal progress | UC-L-03, UC-L-05 |
| UC-21 | View leaderboards | Learner App | Adds organisation, cohort, and friends scopes and season boards. Organisation policy may withdraw managed members from global and country boards | UC-L-08, UC-P-03 |
| UC-22 | Switch language | Learner App | Language applies to five surfaces. Graded items appear in a locale only when their translation is approved (BR-124) | UC-C-11 |
| UC-23 | Analyse my research paper | Learner App | Uploaded papers stay private to the account and are never shared with an organisation | none |
| UC-24 | Get career advice | Learner App | Becomes the `career_coach` mode and the career plan | UC-L-10 |
| UC-25 | Subscribe to a paid plan | Learner App | Only in the consumer organisation. Organisation members receive entitlements from the licence seat instead | UC-O-05 |
| UC-26 | Upload a knowledge asset | Content Studio | Actor becomes `content_author` in a workspace. Rights metadata is required (BR-131) | UC-C-01 |
| UC-27 | Ingest an asset into the knowledge base | Content Studio | Owned by `retrieval`. Chunks carry `workspace_id` and are retrievable only after `knowledge.asset_version.published` | UC-C-01 |
| UC-28 | Manage the knowledge taxonomy | Content Studio | Actor becomes `knowledge_steward` | UC-C-06 |
| UC-29 | Manage concept relationships | Content Studio | Actor becomes `knowledge_steward`. Edge types widen to six; `part_of` is also acyclic (BR-132) | UC-C-07 |
| UC-30 | Build a learning path | Content Studio | A path is now a sequence of courses (and optional standalone modules or projects), not modules. Lessons and modules are built in UC-C-02 and UC-C-03 | UC-C-02, UC-C-03, UC-C-04 |
| UC-31 | Generate content with AI | Content Studio | Generation runs through `ai_gateway` with a recorded prompt release | UC-C-10 |
| UC-32 | Move content through the approval workflow | Content Studio | State `review` is renamed `in_review`; `changes_requested` added. Two-person rule (BR-127) | UC-C-08 |
| UC-33 | Manage asset versions | Content Studio | Asset versions are unchanged. Course and path releases with semantic versions are new | UC-C-09 |
| UC-34 | Handle flagged tutor responses | Admin App | `tutor.message.flagged` lands in the Admin moderation queue. Triage is by platform staff; the content fix is drafted in Content Studio. v1 named the Instructor as primary actor; in v2 instructors in the Instructor App only see flags raised in their cohorts | UC-A-09 |
| UC-35 | Manage users and roles | Admin App | Platform scope only: platform staff roles, account status, platform leaderboard removal. Organisation roles are assigned in the Institution App and Instructor App | UC-A-02, UC-O-03, UC-I-01 |
| UC-36 | View platform and learning analytics | Admin App | Platform-wide and cross-tenant aggregates only. Organisation analytics move to the Institution App | UC-A-08, UC-O-09 |
| UC-37 | Configure and fail over LLM providers | Admin App | Actor becomes `ai_admin`. Route changes pass an evaluation gate (BR-145) | UC-A-03 |
| UC-38 | Monitor safety and abuse | Admin App | Actor becomes `security_auditor` (read) and `platform_operator` (act) | UC-A-06 |

v1 role mapping used in these flows follows the README. v1 `UseCases.md` also proposed a `content_manager` role that the README mapping does not list. This document treats it as `content_reviewer`, `content_publisher`, and `knowledge_steward` in the `master` workspace (see [Open questions](#13-open-questions), OQ-01).

---

## 3. Actors

### Human actors

Human actors are role IDs from the README. A person acts as an actor only through a role assignment at a scope that contains the target. One person can be several actors.

| Actor (role ID) | App | Scope types | Typical person |
| --- | --- | --- | --- |
| Guest | Marketing site, Learner App public pages | none | Visitor without an account |
| `learner` | Learner App | organisation, cohort | Student, employee, professional, self-registered learner |
| `teaching_assistant` | Instructor App | cohort | Postgraduate marker, bootcamp assistant |
| `instructor` | Instructor App | cohort, department | Lecturer, trainer, bootcamp instructor |
| `lead_instructor` | Instructor App | cohort, department, campus | Course leader, programme lead |
| `department_admin` | Institution App | department | Department manager, faculty administrator |
| `campus_admin` | Institution App | campus | Campus registrar |
| `org_admin` | Institution App | organisation | Learning and development manager, university IT administrator |
| `org_owner` | Institution App | organisation | Contract owner |
| `org_billing_manager` | Institution App | organisation | Procurement or finance contact |
| `org_report_viewer` | Institution App | organisation, campus, department | Dean, HR business partner |
| `org_compliance_officer` | Institution App | organisation | Data protection officer |
| `content_author` | Content Studio | workspace | Subject matter expert, curriculum designer |
| `content_reviewer` | Content Studio | workspace | Peer reviewer, academic editor |
| `content_publisher` | Content Studio | workspace | Content operations lead |
| `knowledge_steward` | Content Studio | workspace | Ontologist, taxonomy owner |
| `localisation_editor` | Content Studio | workspace | Translator for `fr` or `es` |
| `support_agent` | Admin App | platform | Customer support |
| `finance_admin` | Admin App | platform | Finance operations |
| `ai_admin` | Admin App | platform | AI platform engineer |
| `platform_operator` | Admin App | platform | Site reliability engineer |
| `security_auditor` | Admin App | platform | Security analyst, internal auditor |
| `platform_admin` | Admin App, Content Studio (read) | platform | Platform owner |

### System actors

| Actor | Kind | Description |
| --- | --- | --- |
| `system` principal | Internal | A non-human service principal scoped to one function: event relay, scheduler, leaderboard job, report job, retention job, erasure job, ingestion worker. Each has its own role assignment and appears as `actorid` on events |
| AI Mentor engine | Internal (`tutor`) | Orchestrator and agents for the six mentor modes. Domain rules decide pedagogy and policy; models only phrase output (carries forward v1) |
| AI marking agent | Internal (`assessment` via `ai_gateway`) | Produces proposed grades against a rubric. Never releases a grade |
| Clerk | External | Authenticates people, issues JWTs with `azp` and `fva`, brokers SAML and OIDC to customer IdPs, sends lifecycle webhooks. Decides no permissions |
| Customer IdP | External | An organisation's identity provider (Microsoft Entra ID, Okta, Google Workspace, Shibboleth) reached through SAML 2.0 or OIDC via Clerk |
| SCIM client | External | An organisation's IdP provisioning connector calling `/scim/v2/...` to create, update, and deactivate managed accounts and groups |
| External LMS | External | Canvas, Moodle, Blackboard, or Brightspace acting as an LTI 1.3 platform: launches AI Mentor, provides rosters (NRPS), receives grades (AGS) |
| Stripe | External | Consumer subscriptions, organisation invoices, payment methods, and billing webhooks |
| LLM providers | External | OpenAI, Anthropic, Gemini, and others behind `ai_gateway` routes. May be slow, rate-limited, or unavailable |
| Email and push provider | External | Delivers transactional email and mobile and web push for `notification`. Reports bounces and complaints |
| Azure Service Bus | Internal infrastructure | Carries the `domain-events` topic from the outbox relay to consumers (ADR 0018) |

---

## 4. Business rules

v1 rules BR-02 to BR-18 and BR-20 to BR-24 stay valid. New rules start at BR-101. **Specified** means the README or an accepted ADR states the rule. **Proposed** means this document sets a value that needs product sign-off.

### Tenancy, membership, and roles

| ID | Rule | Status |
| --- | --- | --- |
| BR-101 | A request acts in exactly one active tenant. Only an `active` membership opens a tenant context. A missing `X-Org-Id` on `/learn` defaults to the home tenant. A header that disagrees with the path is rejected with 400 | Specified (ADR 0015) |
| BR-102 | An invitation is single use, bound to one email address, expires 14 days after it is sent, and can be revoked before acceptance. Accepting with a different verified email is refused. Resending replaces the previous invitation | Proposed |
| BR-103 | An enrolment code is 10 characters from an alphabet without `0`, `O`, `1`, `I`, and `L`. It is scoped to an organisation or a cohort and has an optional expiry and maximum number of redemptions. A person may make 10 failed redemption attempts per hour | Proposed |
| BR-104 | A personal account joining an organisation sees a consent screen that lists what the organisation may see (ADR 0021). Consent is recorded per membership. Withdrawing consent ends the membership | Specified (README); withdrawal behaviour Proposed |
| BR-105 | A managed account belongs to one organisation. It cannot redeem codes or accept invitations from another organisation, and cannot buy a consumer subscription | Specified (README) |
| BR-106 | The system never converts a personal account into a managed account, and never merges two accounts, without an explicit action by the person | Proposed |
| BR-107 | In a seat-based licence a seat is consumed when a membership that holds `learner` becomes `active`, and released when the membership becomes `left` or the `learner` assignment is removed. Suspended memberships keep their seat | Proposed |
| BR-108 | Seat overage: activations may exceed the seat count by up to 5 percent for 30 days. After that, new learner activations are refused; existing learners keep access | Proposed |
| BR-109 | An organisation always has at least one `org_owner`. The last `org_owner` cannot be removed, demoted, or suspended. Only an `org_owner` can assign or remove `org_owner` and `org_admin` | Specified (README) |
| BR-110 | A person can assign a role only at a scope inside one where they hold `authz.role_assignment:grant`, and only roles that the matrix in 10-rbac-matrix.md marks as grantable by their role. Nobody can change their own assignments | Proposed (extends v1 UC-35 E2) |
| BR-111 | Platform-scope roles are assigned only from the Admin App (`azp` = Admin App) by `platform_admin`, with MFA verified in the last 10 minutes (`fva`) | Specified (README); 10 minutes Proposed |

### Classroom and delivery

| ID | Rule | Status |
| --- | --- | --- |
| BR-112 | A cohort plan pins exactly one release per course or path. An overlay may reorder, hide, add supplementary items, set dates, and add instructions. It never changes the master. Hiding an item that teaches a prerequisite of a later plan item produces a warning, not a block | Specified (README); warning Proposed |
| BR-113 | Plan item dates satisfy release ≤ due ≤ close. Dates are stored in UTC and shown in the cohort's single timezone. A plan item without a due date is optional | Proposed |
| BR-114 | Bulk import files are UTF-8 CSV, at most 5,000 data rows and 10 MB. `email` is required; `given_name`, `family_name`, `external_id`, `locale`, and `cohort_code` are optional. Validation covers the whole file before any write. Duplicate emails in one file are errors. A row whose email belongs to an existing personal account becomes an invitation, not a new account | Proposed |
| BR-115 | Risk signals are computed daily per cohort member: `inactivity` (no learning activity for 7 days during an active plan), `missed_due` (two or more missed due dates in 14 days), `mastery_drop` (mastery on a plan concept falls by 15 points or more in 14 days), `low_engagement` (weekly active minutes below 25 percent of the cohort median for two weeks). Each signal stores its evidence. Organisations may change thresholds | Proposed |
| BR-116 | Attendance status is `present`, `late`, `absent`, or `excused`. Every edit is audited. Edits more than 7 days after the session require a reason | Proposed |

### Assessment

| ID | Rule | Status |
| --- | --- | --- |
| BR-117 | A proposed grade is never visible to the learner until a human accepts or overrides it, unless the assignment is auto-graded (objective items only) | Specified (README, ADR 0025) |
| BR-118 | AI marking runs only when the assignment has a rubric, the flag `instructor.ai_marking` is on for the organisation, and organisation policy allows it. Each proposal stores the level per criterion, a rationale, evidence quotes from the submission, the model route, the prompt release, and a confidence from 0 to 1 | Specified (ADR 0025); fields Proposed |
| BR-119 | Proposals with confidence below 0.6, or with an integrity or safety flag, cannot be accepted in bulk. Before any bulk acceptance in an assignment, the marker must have reviewed individually at least 10 percent of the proposals or 5 proposals, whichever is larger | Proposed |
| BR-120 | A grade override needs a reason of at least 10 characters, is audited, and emits `assessment.grade.overridden`. When organisation policy `grades.override_approval` is on, an override of a released grade waits for approval by a `lead_instructor` who is not the person overriding | Specified (README); values Proposed |
| BR-121 | Grades are released per assignment to all or selected learners. A released grade cannot be withdrawn; corrections are overrides. Only released grades pass back to an external LMS | Proposed |
| BR-122 | A learner may request one regrade per assignment, within 14 days of release, with a reason of 20 to 2,000 characters. Staff other than the original marker review it when the cohort has other marking staff. The grade can be lowered only if organisation policy `grades.regrade_may_lower` is on (default off), and the learner is told this before submitting | Proposed |
| BR-123 | Assessment integrity mode applies to a learner from the start of an attempt until the assignment closes or the attempt is submitted. In it, `exam_coach` is unavailable and no mode discloses solutions to items in the assignment. Organisation policy may restrict further modes | Specified (README); scope of the window Proposed |
| BR-124 | A graded item is used in a locale only after its translation is approved (`translation_status = approved`). Otherwise the item is shown in its source locale with a notice | Specified (README); fallback Proposed |
| BR-125 | Accommodations (extra time, extra attempts, alternative format) are recorded per learner per assignment in `assessment.accommodations` and are visible only to staff with access to the cohort | Proposed |

### Content and knowledge

| ID | Rule | Status |
| --- | --- | --- |
| BR-126 | Every content type uses `draft → in_review → approved → published → archived`, with `changes_requested` returning to `draft`. Only published releases are served to learners and retrieved by the AI mentor (supersedes BR-19) | Specified (README) |
| BR-127 | Nobody who authored any change in the version under review can approve it. A MAJOR release can be published only by a `content_publisher` who authored no change in it | First part Specified (README); second part Proposed |
| BR-128 | Release versions follow semantic versioning. MAJOR: an item is removed or reordered, an outcome changes, or the answer or scoring of an assessed item changes. MINOR: items or optional content are added. PATCH: corrections that change no structure, outcome, or scoring. The system proposes the level from the diff; the publisher may raise it, never lower it | Proposed |
| BR-129 | PATCH releases apply automatically to cohorts pinned to the same MAJOR.MINOR, except items inside an open assignment window, which update after it closes. MINOR and MAJOR releases never apply automatically; an instructor accepts or declines them | Proposed |
| BR-130 | An archived release stays available to cohorts already pinned to it until their plan ends, and cannot be newly pinned. A takedown removes the item from every release and from retrieval within 1 hour and shows a placeholder | Proposed |
| BR-131 | An asset needs `rights` and `licence_terms` before it can be submitted for review. An asset with `rights = unknown` cannot be published | Proposed |
| BR-132 | `prerequisite_of` and `part_of` edges must stay acyclic. Self-edges are refused. Edge weights are between 0 and 1 | `prerequisite_of` Specified (README); `part_of` Proposed |
| BR-133 | AI-generated drafts record the model route and prompt release, cite source chunks, and go through review like any draft. A generated item with no citation cannot be submitted for review | Specified (v1 UC-31, extended) |
| BR-134 | A taxonomy node referenced by any content cannot be deleted; it can be merged into another node, which moves the references. Taxonomy depth is at most 6 levels | Proposed |

### Gamification, personalisation, and mentor

| ID | Rule | Status |
| --- | --- | --- |
| BR-135 | XP, levels, streaks, and badges follow BR-02 to BR-06 and are platform-wide per account. Each ledger row carries the `tenant_id` it was earned in | Specified (ADR 0015, ADR 0024) |
| BR-136 | Leaderboard scopes are `global` and `country` (top 10 plus own rank and percentile, BR-22), `organisation`, `cohort`, and `friends`. Global and country boards show pseudonymous display names. A scope with fewer than 5 participants is not shown | Extends BR-22; values Proposed |
| BR-137 | When organisation policy `leaderboards.public_participation` is off, the organisation's managed accounts are left off global and country boards. Personal-account members decide for themselves. Every learner can opt out of any scope | Proposed |
| BR-138 | Friends require mutual acceptance. A person has at most 500 friends | Proposed |
| BR-139 | A season has a start and end in UTC and its own season points, separate from XP. Ties are broken by the earlier time the score was reached. A season board is frozen at the end and kept read-only | Proposed |
| BR-140 | A personalisation dimension can be locked (one value) or bounded (minimum and maximum) by organisation policy or by a cohort. The learner adjusts only within the result. Locks apply only in the tenant and cohort that set them. Overlapping bounds intersect; a lock that leaves no allowed value is refused when it is created | Specified (README); intersection Proposed |
| BR-141 | Mentor persona attributes never change correctness, grounding, or safety rules. Organisation policy `mentor.allowed_modes` and `mentor.persona_attributes` may restrict modes and persona attributes in that tenant | Specified (README); policy names Proposed |

### Platform governance and compliance

| ID | Rule | Status |
| --- | --- | --- |
| BR-142 | Break-glass access to tenant data needs `platform.tenant_data:read`, a reason, a ticket reference, and MFA in the last 10 minutes. A session is read-only, lasts at most 60 minutes, and is logged in `audit.data_access_log`. Write access needs a second `platform_admin` to approve. The organisation's `org_owner` and `org_compliance_officer` are notified within 24 hours unless a `platform_admin` records a security-incident deferral of at most 7 days | Specified (README, ADR 0015); values Proposed |
| BR-143 | A feature flag change needs a reason. Percentage rollouts use a stable hash of the account id. A kill switch takes effect within 60 seconds | Proposed |
| BR-144 | Rate limits and noisy-neighbour limits are enforced per user (BR-12) and per tenant | Specified (ADR 0015) |
| BR-145 | A model route or prompt release reaches production only after its evaluation suite passes: no safety test fails, groundedness and task scores are no more than 2 points below the current baseline, and p95 latency is within 20 percent. It then serves a 5 percent canary for 24 hours before full rollout | Proposed |
| BR-146 | A data subject request is completed within 30 days. For a personal account AI Mentor is controller and handles it. For a managed account the organisation is controller; AI Mentor acts on the `org_compliance_officer`'s instruction | Specified (README); 30 days from GDPR |
| BR-147 | Each organisation sets retention per data category within platform minimum and maximum values. Expired data is deleted or anonymised by the retention job. A legal hold suspends deletion | Proposed |
| BR-148 | Erasure depends on account type. Personal: the account, learning record, conversations, and uploads are erased; academic records held by organisations are kept by those organisations with the person replaced by a pseudonymous identifier, unless the organisation also erases them. Managed: erasure is started by the organisation and removes the account and both records, after an optional passport export | Proposed (ADR 0021) |
| BR-149 | Domain events are delivered at least once; consumers are idempotent on event `id` and carry no free-text personal data | Specified (README, ADR 0018) |
| BR-150 | Report cells and analytics groups with fewer than 10 learners are suppressed. Generated export files are kept for 7 days | Extends v1 UC-36 E1; 7 days Proposed |
| BR-151 | SSO just-in-time provisioning requires a verified email domain in `tenancy.domains`. It creates a `managed` account with `learner` at organisation scope unless an IdP group mapping assigns other roles | Proposed |
| BR-152 | SCIM deactivation suspends the membership immediately and ends it after 30 days. The academic record is kept under the retention policy | Proposed |
| BR-153 | A custom domain is active only after DNS TXT verification and certificate issuance. One custom host per application per organisation | Proposed |
| BR-154 | A learning passport contains earned badges as Open Badges 3.0 credentials and a JSON transcript of completed courses, mastery by concept, and released grades the organisation allows. It never contains tutor conversations or instructor notes | Specified (README); contents Proposed |

---

## 5. Use case map

Each table lists the use cases for one application with the primary actor, the requirement area in [03-srs.md](03-srs.md) (prefix), the owning service modules, and the release. v1 use cases keep their v1 requirement IDs in `SRS.md`.

### Learner App

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-01 to UC-25 | v1 learner use cases | `learner` | v1 IDs | `identity`, `tutor`, `learning`, `gamification`, `commerce` | R1, R2 |
| UC-L-01 | Join an organisation by invitation or enrolment code | `learner` | `TEN`, `LRN` | `tenancy`, `commerce` | R3 |
| UC-L-02 | Switch tenant context | `learner` | `TEN`, `LRN` | `tenancy`, `authz` | R3 |
| UC-L-03 | Follow a scheduled cohort plan | `learner` | `LRN`, `INS` | `classroom`, `learning`, `content` | R3 |
| UC-L-04 | Submit a graded assignment | `learner` | `ASM`, `LRN` | `assessment`, `tutor` | R3 |
| UC-L-05 | View a released grade and request a regrade | `learner` | `ASM`, `LRN` | `assessment`, `notification` | R3 |
| UC-L-06 | Configure mentor persona and mode | `learner` | `TUT`, `PER` | `tutor`, `personalisation` | R2 |
| UC-L-07 | Adjust personalisation dimensions within locks | `learner` | `PER` | `personalisation` | R2 (locks R3) |
| UC-L-08 | Compete in a seasonal challenge and view scoped leaderboards | `learner` | `GAM` | `gamification` | R2 (organisation and cohort scopes R3) |
| UC-L-09 | Search knowledge | `learner` | `SRCH` | `search`, `retrieval` | R2 |
| UC-L-10 | Plan a career | `learner` | `LRN`, `TUT` | `learning`, `tutor`, `personalisation` | R2 |
| UC-L-11 | Export a learning passport | `learner` | `LRN`, `INT` | `learning`, `gamification`, `reporting` | R4 |

### Instructor App

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-I-01 | Create or invite a learner | `instructor` | `INS`, `TEN` | `tenancy`, `identity`, `classroom` | R3 |
| UC-I-02 | Bulk import learners from CSV | `instructor` | `INS`, `TEN` | `classroom`, `tenancy`, `identity` | R3 |
| UC-I-03 | Create a cohort | `lead_instructor` | `INS` | `classroom`, `authz` | R3 |
| UC-I-04 | Assign a release and schedule a learning journey with an overlay | `instructor` | `INS`, `CST` | `classroom`, `content`, `learning` | R3 |
| UC-I-05 | Create an assessment with the quiz builder | `instructor` | `ASM`, `INS` | `assessment`, `content` | R3 |
| UC-I-06 | Define a rubric | `instructor` | `ASM` | `assessment` | R3 |
| UC-I-07 | Mark a submission manually | `teaching_assistant` | `ASM` | `assessment` | R3 |
| UC-I-08 | Review AI-proposed marks and override | `instructor` | `ASM` | `assessment`, `ai_gateway` | R3 |
| UC-I-09 | Release grades | `instructor` | `ASM` | `assessment`, `notification`, `integration` | R3 |
| UC-I-10 | Monitor progress and risk, and record an intervention | `instructor` | `INS`, `ANL` | `classroom`, `analytics` | R3 |
| UC-I-11 | Record attendance and analyse engagement | `instructor` | `INS`, `ANL` | `classroom`, `analytics` | R3 |
| UC-I-12 | Message a cohort through the communication hub | `instructor` | `MSG`, `NTF` | `messaging`, `notification` | R3 |
| UC-I-13 | View performance analytics | `instructor` | `ANL`, `RPT` | `analytics`, `reporting` | R3 |
| UC-I-14 | Handle a content update to a pinned release | `instructor` | `INS`, `CST` | `content`, `classroom` | R3 |

### Institution App

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-O-01 | Set up the organisation | `org_owner` | `ORG`, `TEN` | `tenancy`, `authz` | R3 |
| UC-O-02 | Manage campus and department structure | `org_admin` | `ORG`, `TEN` | `tenancy` | R3 |
| UC-O-03 | Manage instructors and staff roles | `org_admin` | `ORG`, `AUTHZ` | `authz`, `tenancy` | R3 |
| UC-O-04 | Manage cohorts at scale | `department_admin` | `ORG`, `INS` | `classroom` | R3 |
| UC-O-05 | Manage licences, seats, billing, and invoices | `org_billing_manager` | `LIC` | `commerce` | R3 |
| UC-O-06 | Configure branding and a custom domain | `org_admin` | `ORG` | `tenancy` | R3 (custom domain R4) |
| UC-O-07 | Configure SSO with SAML or OIDC and JIT provisioning | `org_admin` | `IAM` | `identity`, `tenancy` | R3 |
| UC-O-08 | Connect SCIM provisioning | `org_admin` | `IAM`, `INT` | `integration`, `identity` | R4 |
| UC-O-09 | Run reports and schedule exports | `org_report_viewer` | `RPT`, `ANL` | `reporting`, `analytics` | R3 |
| UC-O-10 | Produce a workforce development report | `org_report_viewer` | `RPT` | `reporting`, `analytics`, `learning` | R4 |
| UC-O-11 | Handle a data subject request and set retention | `org_compliance_officer` | `ORG`, `NFR` | `audit` | R3 |
| UC-O-12 | Configure organisation policies | `org_admin` | `ORG`, `TEN` | `tenancy`, `config` | R3 |
| UC-O-13 | Connect an external LMS through LTI 1.3 | `org_admin` | `INT` | `integration` | R4 |

### Admin App

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-34 to UC-38 | v1 administration use cases | Platform staff roles | v1 IDs | `tutor`, `authz`, `analytics`, `ai_gateway`, `audit` | R1, R2 |
| UC-A-01 | Provision an organisation | `platform_admin` | `ADM`, `TEN` | `tenancy`, `commerce`, `authz` | R3 |
| UC-A-02 | Manage platform users and staff roles | `platform_admin` | `ADM`, `AUTHZ` | `identity`, `authz` | R2 |
| UC-A-03 | Configure AI services and model routing with an evaluation gate | `ai_admin` | `ADM`, `TUT` | `ai_gateway` | R2 |
| UC-A-04 | Manage feature flags, rollout, and platform settings | `platform_operator` | `ADM`, `PLT` | `config` | R2 |
| UC-A-05 | Review audit logs | `security_auditor` | `ADM` | `audit` | R2 |
| UC-A-06 | Monitor security events | `security_auditor` | `ADM`, `NFR` | `audit`, `identity` | R2 |
| UC-A-07 | Manage subscriptions and plans | `finance_admin` | `LIC` | `commerce` | R2 |
| UC-A-08 | Produce global reports | `platform_admin` | `RPT`, `ANL` | `reporting`, `analytics` | R2 |
| UC-A-09 | Resolve knowledge governance escalations | `platform_admin` | `ADM`, `KM` | `tutor`, `knowledge`, `content` | R2 |
| UC-A-10 | Use break-glass access to tenant data | `support_agent`, `platform_admin` | `ADM`, `AUTHZ` | `audit`, `authz` | R3 |

### Content Studio

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-26 to UC-33 | v1 knowledge portal use cases | Content Studio roles | v1 IDs | `knowledge`, `retrieval`, `content` | R1, R2 |
| UC-C-01 | Upload and ingest an asset with metadata and rights | `content_author` | `CST`, `KM` | `knowledge`, `retrieval` | R2 |
| UC-C-02 | Build a lesson | `content_author` | `CST` | `content` | R2 |
| UC-C-03 | Build a module and a course | `content_author` | `CST` | `content` | R2 |
| UC-C-04 | Build a learning path | `content_author` | `CST` | `content` | R2 |
| UC-C-05 | Build a quiz and item bank with localisation | `content_author` | `CST`, `ASM` | `content`, `assessment`, `i18n` | R2 |
| UC-C-06 | Manage the taxonomy | `knowledge_steward` | `KM` | `knowledge` | R2 |
| UC-C-07 | Edit the knowledge graph with cycle prevention | `knowledge_steward` | `KG` | `knowledge` | R2 |
| UC-C-08 | Review content under the two-person rule | `content_reviewer` | `CST` | `content` | R2 |
| UC-C-09 | Publish a release with impact analysis | `content_publisher` | `CST` | `content`, `classroom`, `retrieval` | R2 (impact on cohorts R3) |
| UC-C-10 | Generate content with AI and review it | `content_author` | `CST`, `KM` | `content`, `ai_gateway`, `retrieval` | R2 |
| UC-C-11 | Localise content | `localisation_editor` | `CST`, `I18N` | `content`, `i18n` | R2 |
| UC-C-12 | Retire, archive, or take down content | `content_publisher` | `CST`, `KM` | `content`, `knowledge`, `retrieval` | R2 |

### Platform and system

| ID | Use case | Primary actor | SRS area | Modules | Release |
| --- | --- | --- | --- | --- | --- |
| UC-P-01 | Provision an account through SSO just in time | Customer IdP, `system` | `IAM` | `identity`, `tenancy`, `authz` | R3 |
| UC-P-02 | Emit and consume domain events | `system` | `EVT` | all modules, `events` schema | R1 |
| UC-P-03 | Compute leaderboards | `system` | `GAM` | `gamification` | R1 (new scopes R2, R3) |
| UC-P-04 | Generate scheduled reports | `system` | `RPT` | `reporting`, `notification` | R3 |
| UC-P-05 | Recommend adaptively from the knowledge graph | `system` | `PER`, `KG` | `personalisation`, `knowledge`, `learning` | R2 |
| UC-P-06 | Erase an account according to its account type | `system` | `PLT`, `NFR` | `identity`, `audit`, all modules | R1 (managed accounts R3) |

---

## 6. Learner App use cases

### UC-L-01 Join an organisation by invitation or enrolment code
- **Goal:** A learner with a personal account becomes a member of an organisation and, where the code or invitation names one, a cohort.
- **Actors:** Primary: `learner`. Supporting: Email and push provider, Clerk.
- **Preconditions:** The person is signed in, or signs up during the flow (UC-01). The invitation or code is valid (BR-102, BR-103).
- **Trigger:** The person opens an invitation link, or enters an enrolment code under "Join an organisation".
- **Permissions:** None beyond authentication: joining is `/me` self-service on the account's own record (10-rbac-matrix.md §4.1). ABAC: account type is `personal` (BR-105); for an invitation, the verified email equals the invited email; the organisation's licence has a free seat or is within overage (BR-108).

**Main success flow:**
1. The system resolves the invitation or code to an organisation and, optionally, a cohort, and shows the organisation's name and branding.
2. The system shows the consent screen: which parts of the learning record the organisation may see (concepts in assigned curricula only), and that the academic record will belong to the organisation (BR-104).
3. The learner accepts.
4. The system creates or activates the membership, assigns `learner` at organisation scope, and adds the person to the cohort if one is named.
5. The system consumes a seat (BR-107) and emits `tenancy.membership.activated` and, for a cohort, `classroom.cohort_member.added`.
6. The system switches the Learner App to the new tenant context and shows the cohort plan, if any (UC-L-03).

**Alternate flows:**
- A1 (step 1) The person is not signed in. The system stores the invitation token, runs UC-01, then returns to step 2.
- A2 (step 1) The organisation has an SSO connection with enforced sign-in. The system sends the person through UC-P-01; a managed account is created instead and this use case ends.
- A3 (step 4) The person already has an `active` membership. The system only adds the cohort membership.

**Exception flows:**
- E1 (step 1) The invitation has expired, been revoked, or been used, or the code has reached its redemption limit. The system says so and suggests contacting the inviter.
- E2 (step 1) Ten failed code attempts in an hour. Further attempts are refused for the rest of the hour (BR-103).
- E3 (step 3) The learner declines consent. No membership is created and the invitation stays valid until expiry.
- E4 (step 5) No seat is available and overage is exhausted. The membership stays `invited` and the organisation's billing managers are notified.
- E5 (any step) The account is `managed`. The system refuses and explains that managed accounts belong to one organisation.

- **Postconditions:** An `active` membership with recorded consent exists. Learning record items earned before joining keep their original `tenant_id`.
- **References:** BR-102 to BR-108. Requirement area `TEN`, `LRN`. Release R3.

### UC-L-02 Switch tenant context
- **Goal:** A learner with several memberships moves between organisations without mixing their academic records.
- **Actors:** Primary: `learner`.
- **Preconditions:** The learner has two or more `active` memberships, for example the consumer organisation and a university.
- **Trigger:** The learner chooses another organisation in the organisation switcher, or opens a link that belongs to another tenant.
- **Permissions:** `tenancy.membership:read` at the account's own memberships. ABAC: the target membership is `active` (BR-101).

**Main success flow:**
1. The system lists the learner's active memberships with name, logo, and role summary.
2. The learner selects an organisation.
3. The Learner App sends the new `X-Org-Id` on every subsequent call; the API validates it against the membership.
4. The system loads the organisation's branding, locale default, policies, cohort plans, and assignments.
5. The dashboard shows organisation items first and personal learning (streak, XP, level) in the same place as before.

**Alternate flows:**
- A1 (trigger) A deep link to an assignment belongs to another tenant. The system asks the learner to switch, then opens the link.
- A2 (step 4) Organisation policy turns off a feature, for example a mentor mode. The feature is hidden in this context only.

**Exception flows:**
- E1 (step 3) The membership was suspended or ended since the list loaded. The API returns 403; the app returns to the home tenant.
- E2 (step 3) A stale header disagrees with a path parameter. The API returns 400 (BR-101).

- **Postconditions:** The active tenant is remembered per device. No data from the previous tenant is shown in the new one.
- **References:** BR-101, BR-135. Requirement area `TEN`, `LRN`. Release R3.

### UC-L-03 Follow a scheduled cohort plan
- **Goal:** A learner sees what the cohort expects this week and completes plan items on time.
- **Actors:** Primary: `learner`. Supporting: AI Mentor engine, Email and push provider.
- **Preconditions:** The learner is a cohort member. The cohort has a scheduled plan (UC-I-04).
- **Trigger:** The learner opens "My cohort", a plan item reminder, or the dashboard.
- **Permissions:** `learning.lesson:study` at cohort scope (covers viewing the plan and completing its items). ABAC: the learner is a member of the cohort; the plan item's release date has passed.

**Main success flow:**
1. The system shows the plan as a timeline: released items, due items with dates in the cohort timezone, and items not yet released (titles only).
2. The learner opens a released lesson. The system renders it from the pinned release with the overlay applied (instructions, supplementary items).
3. The learner completes the lesson (UC-12). The system records completion against the plan item.
4. The system updates progress, mastery, and XP and emits `learning.lesson.completed`.
5. The system shows the next due item.

**Alternate flows:**
- A1 (step 1) The learner also follows a personal study plan. Cohort items appear first; personal items follow (UC-13).
- A2 (step 2) The plan item is a live session. The system shows time, joining link, and attendance check-in (UC-I-11).
- A3 (step 3) The learner completes an item after its due date and before close. It is recorded as late.

**Exception flows:**
- E1 (step 2) The item is not yet released. The system shows the release date and refuses to open it.
- E2 (step 3) The item has closed. The system records practice evidence for mastery but not plan completion.

- **Postconditions:** Plan completion, timeliness, and mastery are stored. Instructors see the change in UC-I-10.
- **References:** BR-112, BR-113, BR-135. Requirement area `LRN`, `INS`. Release R3.

### UC-L-04 Submit a graded assignment
- **Goal:** A learner completes formal assessed work and submits it within the rules set by the instructor.
- **Actors:** Primary: `learner`. Supporting: AI Mentor engine (integrity mode), AI marking agent.
- **Preconditions:** The assignment is published to the learner's cohort and is open. The learner has attempts left.
- **Trigger:** The learner opens the assignment from the plan, the dashboard, or a notification.
- **Permissions:** `assessment.submission:submit` at cohort scope. ABAC: now is between open and close dates, adjusted by the learner's accommodations (BR-125); attempts used are below the limit; locale has approved items (BR-124); the IP allowlist passes if the organisation set one.

**Main success flow:**
1. The system shows instructions, dates, attempts, time limit, rubric (if visible to learners), and integrity rules.
2. The learner starts an attempt. The system starts integrity mode for the learner (BR-123) and the timer, if any.
3. The learner answers items: objective items, written responses, file uploads, or code (sandbox rules BR-13, BR-14).
4. The system autosaves responses every 30 seconds and on each item change.
5. The learner submits. The system freezes the responses and records the time.
6. The system auto-grades objective items, emits `assessment.submission.submitted`, and queues AI marking for rubric items if enabled (BR-118).
7. The system confirms submission with a receipt number. Integrity mode ends for the learner.

**Alternate flows:**
- A1 (step 2) The learner asks the mentor for help during the attempt. The mentor explains general concepts only and refuses to solve items in the assignment.
- A2 (step 5) The time limit ends. The system submits the saved responses automatically.
- A3 (step 6) The assignment is fully auto-graded and set to release immediately. The grade appears at once (UC-L-05).

**Exception flows:**
- E1 (step 2) The assignment is closed or attempts are exhausted. The system refuses and shows the dates and attempts.
- E2 (step 4) Connection drops. Responses saved so far are kept; the timer continues on the server.
- E3 (step 5) An upload is larger than the assignment limit or of a disallowed type. The system refuses that file.

- **Postconditions:** A submission exists with frozen responses, an attempt number, and timestamps. Marks are pending.
- **References:** BR-117, BR-118, BR-123 to BR-125. Requirement area `ASM`, `LRN`. Release R3.

### UC-L-05 View a released grade and request a regrade
- **Goal:** A learner sees their grade and feedback and can ask for a review if they think it is wrong.
- **Actors:** Primary: `learner`. Supporting: `instructor`, `teaching_assistant`.
- **Preconditions:** The grade for the learner's submission has been released (UC-I-09).
- **Trigger:** The learner opens a grade notification or the Grades page.
- **Permissions:** `assessment.grade:read` and `assessment.grade:appeal` at cohort scope. ABAC: the learner owns the submission; the grade is released; the request is within the regrade window (BR-122).

**Main success flow:**
1. The system shows the grade, rubric levels per criterion, feedback, and any marked-up responses.
2. The learner selects "Request a regrade".
3. The system shows the rules: one request, the deadline, and whether a regrade can lower the grade.
4. The learner selects the criteria in question and gives a reason.
5. The system records the request, emits `assessment.regrade.requested`, and notifies marking staff.
6. A staff member reviews it (UC-I-08, A3). The system notifies the learner of the outcome and the new grade, if changed.

**Alternate flows:** A1 (step 1) The feedback mentions an AI-assisted mark. The system shows that a human confirmed it; the AI rationale itself is shown only if the instructor chose to share it.

**Exception flows:**
- E1 (step 2) The window has passed or a request already exists. The option is not offered.
- E2 (step 4) The reason is shorter than 20 characters. The system asks for more detail.

- **Postconditions:** The request and its outcome are part of the academic record. Any grade change is an override (BR-120).
- **References:** BR-117, BR-120, BR-122. Requirement area `ASM`, `LRN`. Release R3.

### UC-L-06 Configure mentor persona and mode
- **Goal:** A learner chooses how the AI mentor presents itself and which job it is doing.
- **Actors:** Primary: `learner`. Supporting: AI Mentor engine.
- **Preconditions:** The learner is signed in.
- **Trigger:** The learner opens Mentor settings, or uses the mode selector in a conversation.
- **Permissions:** `tutor.persona:select` at the learner's own account; `tutor.conversation:use` in the active tenant. ABAC: the mode is in the organisation's `mentor.allowed_modes`; integrity mode is not active for the requested mode (BR-123); persona attributes are allowed by policy and by the subscription tier (voice options are a paid entitlement).

**Main success flow:**
1. The system shows the six modes (`tutor`, `mentor`, `research_supervisor`, `coding_coach`, `career_coach`, `exam_coach`) with a one-line description of each and which are available in this tenant.
2. The system shows persona attributes: personality, teaching style, voice style, age appearance, gender presentation, accent preference, coaching style.
3. The learner chooses values and a default mode. In `tutor`, the learner also chooses the technique (Socratic or Direct).
4. The system validates and saves the persona to `personalisation.mentor_personas`.
5. The next conversation turn uses the new persona and mode.

**Alternate flows:**
- A1 (trigger) The learner switches mode inside a conversation. The orchestrator starts a new turn in that mode and keeps the conversation history.
- A2 (step 3) The learner resets to the default persona.

**Exception flows:**
- E1 (step 1) A mode is disabled by policy. It is shown as unavailable with the reason "Turned off by your organisation".
- E2 (step 3) Integrity mode is active. `exam_coach` cannot be selected until the attempt ends.

- **Postconditions:** Persona and default mode are saved per account. Grounding, citation, and safety rules are unchanged (BR-141).
- **References:** BR-09, BR-10, BR-123, BR-141. Requirement area `TUT`, `PER`. Release R2.

### UC-L-07 Adjust personalisation dimensions within instructor locks
- **Goal:** A learner tunes depth, pace, approach, register, and breadth, within limits set by their cohort or organisation.
- **Actors:** Primary: `learner`. Supporting: Personalisation Engine.
- **Preconditions:** The learner is signed in.
- **Trigger:** The learner opens Learning preferences, or uses the style control in a lesson or conversation.
- **Permissions:** `personalisation.dimension:edit` at the learner's own account. ABAC: the new value lies within every `personalisation.dimension_locks` row that applies in the active tenant and current cohort (BR-140).

**Main success flow:**
1. The system shows five sliders with the current values and, for each locked or bounded dimension, the allowed range and who set it.
2. The learner moves one or more sliders within the allowed range.
3. The system saves the settings for the account.
4. Lessons, quizzes, and mentor turns use the effective value: the learner's value, clamped to the applicable bounds.

**Alternate flows:** A1 (step 2) The learner is in two cohorts with different bounds. Each cohort's bounds apply only to that cohort's plan items; personal learning uses the unbounded value.

**Exception flows:**
- E1 (step 2) The slider is locked. It is shown disabled with the lock source.
- E2 (step 3) A value outside the bounds is submitted directly to the API. It is refused with 422 and the allowed range.

- **Postconditions:** Settings are saved. Mastery and progress are unchanged.
- **References:** BR-140. Requirement area `PER`, `LRN`. Release R2 (locks R3).

### UC-L-08 Compete in a seasonal challenge and view scoped leaderboards
- **Goal:** A learner takes part in a time-boxed competition and compares progress at the scopes they care about.
- **Actors:** Primary: `learner`. Supporting: Gamification Platform, `system` (leaderboard job).
- **Preconditions:** A season is open. The learner has not opted out of the scope they view.
- **Trigger:** The learner opens Challenges or Leaderboards.
- **Permissions:** `learning.practice:use` (entering a competition) and `gamification.leaderboard:read` in the active tenant. ABAC: organisation and cohort boards require membership of that unit; organisation policy `leaderboards.public_participation` (BR-137); scope has at least 5 participants (BR-136).

**Main success flow:**
1. The system shows open seasons with dates, rules, eligible activities, and prizes or badges.
2. The learner joins a season.
3. Qualifying activities award season points as well as XP (BR-139).
4. The learner opens Leaderboards and picks a scope: global, country, organisation, cohort, or friends, and a period (this week, this season, all time).
5. The system shows the top 10 for the scope, the learner's rank and percentile, and the people just above and below.

**Alternate flows:**
- A1 (step 4) The learner adds a friend by username. The friend accepts (BR-138). The friends board updates at the next computation.
- A2 (step 4) The learner opts out of a scope. They disappear from it at the next computation and still see their own private rank.

**Exception flows:**
- E1 (step 5) The scope has fewer than 5 participants. The system shows "Not enough participants yet".
- E2 (step 3) An activity is flagged as XP farming (UC-38). Season points for it are held until review.

- **Postconditions:** Season membership and points are stored. Boards follow the computation in UC-P-03.
- **References:** BR-22, BR-135 to BR-139. Requirement area `GAM`, `LRN`. Release R2 (organisation and cohort scopes R3).

### UC-L-09 Search knowledge
- **Goal:** A learner finds lessons, concepts, assets, and past conversations relevant to a question.
- **Actors:** Primary: `learner`. Supporting: Search Platform, RAG Platform.
- **Preconditions:** The learner is signed in.
- **Trigger:** The learner types in the global search box or presses the search shortcut.
- **Permissions:** `learning.catalogue:read` in the active tenant. ABAC: results are filtered to published releases in `master` and the active tenant's `org` workspace, to the learner's own conversations and uploads, and to the learner's subscription tier for premium assets.

**Main success flow:**
1. The learner enters a query in any supported locale.
2. The system runs keyword and semantic search across the permitted sources.
3. The system groups results by type: concepts, lessons, courses, assets, my conversations.
4. Each result shows title, snippet, source, and locale. Concepts show the learner's mastery.
5. The learner opens a result, or chooses "Ask the mentor about this", which starts a conversation grounded on the result.

**Alternate flows:** A1 (step 3) A result exists only in another locale. It is shown with a locale label and an offer to translate the AI summary.

**Exception flows:**
- E1 (step 2) The search index is unavailable. The system falls back to catalogue title search and says results are limited.
- E2 (step 1) The query fails screening (BR-11). Nothing is searched.

- **Postconditions:** The query and clicked result are logged for search quality, without the query text if the learner turned off search history.
- **References:** BR-11, BR-126. Requirement area `SRCH`, `LRN`. Release R2.

### UC-L-10 Plan a career
- **Goal:** A learner sets a target role and gets a plan of skills, paths, and projects to reach it.
- **Actors:** Primary: `learner`. Supporting: AI Mentor engine (`career_coach`), LLM providers.
- **Preconditions:** The learner has completed onboarding or entered a career goal.
- **Trigger:** The learner opens Career, or asks a career question in `career_coach` mode.
- **Permissions:** None beyond authentication: the learner edits their own record (ABAC-15). An organisation sees the plan only if the learner shares it with that organisation.

**Main success flow:**
1. The learner chooses a target role from the role catalogue (for example "Reinforcement Learning Engineer") or describes one.
2. The system compares the role's concept profile with the learner's mastery and lists strengths and gaps.
3. The system proposes learning paths, projects, and a time estimate based on pace.
4. The learner adjusts the timeline and accepts the plan.
5. The system saves the career plan and adds recommended paths to the learner's suggestions.

**Alternate flows:**
- A1 (step 1) The role is not in the catalogue. The `career_coach` maps the description to the closest catalogue roles and says so.
- A2 (step 5) The learner shares the plan with an employer organisation. It becomes visible to that organisation's `org_report_viewer` in workforce reports (UC-O-10).

**Exception flows:** E1 (step 3) The LLM providers fail. The system shows the catalogue role's standard path without personal commentary.

- **Postconditions:** The career plan is part of the learning record.
- **References:** BR-16. Requirement area `LRN`, `TUT`. Release R2.

### UC-L-11 Export a learning passport
- **Goal:** A learner takes verifiable evidence of what they have learned to an employer or another institution.
- **Actors:** Primary: `learner`. Supporting: Reporting Platform.
- **Preconditions:** The learner has at least one badge or completed course.
- **Trigger:** The learner selects "Export learning passport" in Profile.
- **Permissions:** `learning.passport:export` at the learner's own account. ABAC: for a managed account, organisation policy `records.passport_export` is on; released grades are included only for organisations whose policy allows it (BR-154).

**Main success flow:**
1. The system shows what the passport will contain, grouped by organisation.
2. The learner chooses sections and a locale.
3. The system generates Open Badges 3.0 credentials, signed, and a JSON transcript, and a readable PDF summary.
4. The system offers a download and a revocable verification link.

**Alternate flows:** A1 (step 4) The learner revokes a verification link. Verifiers see that it was revoked.

**Exception flows:** E1 (trigger) The account is managed and the policy is off. The option is not shown; the learner is told to ask their organisation.

- **Postconditions:** The export is logged. The file is kept for 7 days (BR-150).
- **References:** BR-150, BR-154. Requirement area `LRN`, `INT`. Release R4.

---

## 7. Instructor App use cases

All Instructor App use cases run in the tenant of the cohort, sent as `{org_id}` on `/api/v1/orgs/{org_id}/...`. Staff hold roles at cohort, department, or campus scope; an assignment at a department covers every cohort below it.

### UC-I-01 Create or invite a learner
- **Goal:** An instructor adds one learner to a cohort, either by creating a managed account or by inviting an existing person.
- **Actors:** Primary: `instructor`. Supporting: Email and push provider, Clerk.
- **Preconditions:** The cohort exists. The organisation's licence has a free seat or is within overage (BR-108).
- **Trigger:** The instructor selects "Add learner" in a cohort.
- **Permissions:** `identity.account:create` and `classroom.cohort_member:add` at cohort scope, or `tenancy.membership:invite` for an invitation. ABAC: organisation policy `members.instructor_can_create` is on for account creation; the cohort is not archived.

**Main success flow:**
1. The instructor enters email, given name, family name, optional external id, and locale.
2. The system checks the email against existing accounts in the platform without revealing details to the instructor.
3. No account exists. The system creates a `managed` account with `home_tenant_id` set to the organisation, an `active` membership, `learner` at organisation scope, and cohort membership.
4. The system sends a welcome email with a sign-in link (or SSO instructions if the organisation enforces SSO) and emits `identity.account.created`, `tenancy.membership.activated`, and `classroom.cohort_member.added`.

**Alternate flows:**
- A1 (step 2) The email belongs to a personal account or to a managed account of this organisation. A personal account receives an invitation (BR-102, UC-L-01); an existing member of this organisation is added to the cohort directly.
- A2 (trigger) The instructor chooses "Invite" instead. The system creates an invitation only, and the membership stays `invited` until accepted.

**Exception flows:**
- E1 (step 2) The email belongs to a managed account in another organisation. The system says the person cannot be added and suggests a different email (BR-105).
- E2 (step 3) No seat is available. The system refuses and notifies `org_billing_manager` holders.

- **Postconditions:** The learner is a cohort member or has a pending invitation. Every creation is audited with the instructor as actor.
- **References:** BR-102, BR-105, BR-106, BR-107, BR-108. Requirement area `INS`, `TEN`. Release R3.

### UC-I-02 Bulk import learners from CSV
- **Goal:** An instructor adds many learners to a cohort in one operation with every row validated first.
- **Actors:** Primary: `instructor`. Supporting: `system` (import job), Email and push provider.
- **Preconditions:** The cohort exists. The instructor has a CSV file in the published template.
- **Trigger:** The instructor selects "Import learners" and uploads a file.
- **Permissions:** `classroom.cohort_member:import` at cohort scope. ABAC: as UC-I-01, plus the file passes the limits in BR-114.

**Main success flow:**
1. The system checks encoding, size, row count, and headers.
2. The system validates every row (email format, duplicates, locale code, cohort code, existing accounts) and the seat total, without writing anything.
3. The system shows a preview: rows to create, rows to invite, rows already members, and rows with errors with the reason per row.
4. The instructor confirms import of the valid rows.
5. The import job creates accounts, invitations, and cohort memberships in batches of 200 and shows progress.
6. The system emails a summary and offers an error report CSV for the rejected rows.

**Alternate flows:** A1 (step 4) The instructor fixes the file and uploads it again. The previous preview is discarded.

**Exception flows:**
- E1 (step 1) The file is too large, not UTF-8, or missing `email`. The system rejects it before validation.
- E2 (step 2) Valid rows exceed the available seats plus overage. Import is blocked until seats are added or rows removed.
- E3 (step 5) A batch fails. Completed batches stay; the job retries the failed batch three times, then reports the rows as failed.

- **Postconditions:** An import record stores counts, the file hash, and the actor. Running the same file twice adds no duplicates.
- **References:** BR-105, BR-106, BR-107, BR-108, BR-114. Requirement area `INS`, `TEN`. Release R3.

### UC-I-03 Create a cohort
- **Goal:** A lead instructor creates a cohort and assigns its teaching staff.
- **Actors:** Primary: `lead_instructor`. Supporting: `department_admin`.
- **Preconditions:** The department or campus exists in the org-unit tree.
- **Trigger:** The lead instructor selects "New cohort".
- **Permissions:** `classroom.cohort:create` at the department or campus scope where the cohort will sit; `classroom.cohort_staff:assign` for staff. ABAC: the parent org unit is inside the actor's scope; assigned staff are `active` members of the organisation.

**Main success flow:**
1. The lead instructor enters name, code, parent org unit, start and end dates, timezone, locale, and capacity.
2. The lead instructor adds instructors and teaching assistants from the organisation's staff.
3. The system creates the cohort and its org unit, and role assignments at cohort scope for each staff member.
4. The system creates an enrolment code for the cohort if requested (BR-103).

**Alternate flows:** A1 (step 1) The lead instructor copies an existing cohort. Staff, plan, and assessments are copied with dates shifted to the new start date; learners are not copied.

**Exception flows:** E1 (step 1) The code is already used in the organisation. The system asks for another.

- **Postconditions:** The cohort exists with staff. `classroom.cohort.created` is emitted.
- **References:** BR-103, BR-110, BR-113. Requirement area `INS`. Release R3.

### UC-I-04 Assign a release and schedule a learning journey with an overlay
- **Goal:** An instructor pins a course or learning path release to a cohort and turns it into a dated plan, customised without changing the master.
- **Actors:** Primary: `instructor`. Supporting: `system` (notification), Content Platform.
- **Preconditions:** The cohort exists. The organisation's licence entitles it to the course or path.
- **Trigger:** The instructor selects "Plan" in a cohort.
- **Permissions:** `learning.enrolment:create`, `classroom.cohort_plan:schedule`, and `content.overlay:edit` at cohort scope. ABAC: the release is `published` and not archived (BR-130); the content is in `master` or the organisation's `org` workspace; licence entitlement covers it.

**Main success flow:**
1. The instructor searches the catalogue and selects a course or path. The system offers the latest release and shows its version.
2. The system creates a draft plan: one plan item per release item, with suggested dates spread between the cohort start and end dates by estimated effort.
3. The instructor edits the overlay: reorders modules, hides lessons, adds supplementary items and instructions, adds live sessions, and sets release, due, and close dates.
4. The system validates dates (BR-113) and prerequisites (BR-112) and lists warnings.
5. The instructor schedules the plan. The system enrols every cohort member, emits `classroom.cohort_plan.scheduled`, and notifies learners of the first items.

**Alternate flows:**
- A1 (step 3) The instructor applies a department overlay template. Its changes are copied into the cohort overlay.
- A2 (after step 5) A learner joins later. The system enrols them; items already past due are marked as late-allowed or excused per the plan setting.

**Exception flows:** E1 (step 1) The release is not in the licence. The system shows it as unavailable and names the licence feature needed.

- **Postconditions:** A scheduled cohort plan with a pinned release and overlay exists. The master release is unchanged.
- **References:** BR-112, BR-113, BR-129, BR-130. Requirement area `INS`, `CST`. Release R3.

### UC-I-05 Create an assessment with the quiz builder
- **Goal:** An instructor builds a graded quiz or exam from the item bank and their own items, and issues it to a cohort.
- **Actors:** Primary: `instructor`. Supporting: AI marking agent (objective items only).
- **Preconditions:** The cohort has a scheduled plan or an open date range.
- **Trigger:** The instructor selects "New assessment".
- **Permissions:** `assessment.assessment:create` and `assessment.assignment:publish` at cohort scope. ABAC: item bank items are published in a workspace the organisation can use; cohort-local items stay in the organisation's tenant.

**Main success flow:**
1. The instructor chooses a type (quiz, exam, assignment, project, coding assessment, written response) and sets title, instructions, and concepts assessed.
2. The instructor adds items from the item bank by concept, difficulty, and type, or writes cohort-local items.
3. The instructor sets attempts, time limit, randomisation, open, due, and close dates, grading mode (auto, manual, AI-assisted), and feedback timing.
4. The system checks that every item has an approved translation for the cohort locale (BR-124) and that rubric items have a rubric (UC-I-06).
5. The instructor publishes the assignment. The system adds a plan item and emits `assessment.assignment.published`.

**Alternate flows:** A1 (step 2) The instructor asks for a random draw: for example 10 items from a concept pool at medium difficulty. Each learner receives a different draw from the same pool.

**Exception flows:**
- E1 (step 4) A required translation is missing. Publishing is blocked for that locale; the instructor can remove the item or publish in the source locale only.
- E2 (step 5) The assessment is already open and has submissions. Item changes are refused; dates can still change.

- **Postconditions:** The assignment is published and frozen for structure once the first attempt starts.
- **References:** BR-117, BR-123, BR-124. Requirement area `ASM`, `INS`. Release R3.

### UC-I-06 Define a rubric
- **Goal:** An instructor sets criteria and performance levels so that marking is consistent, manual or AI-assisted.
- **Actors:** Primary: `instructor`.
- **Preconditions:** An assignment with open-ended items exists in draft, or the instructor is building a reusable rubric.
- **Trigger:** The instructor selects "Add rubric".
- **Permissions:** `assessment.rubric:edit` at cohort or department scope. ABAC: a rubric attached to an assignment with submissions is read-only.

**Main success flow:**
1. The instructor adds criteria with a name, description, and weight. Weights must total 100.
2. For each criterion the instructor adds ordered levels with points and a descriptor, and optional exemplar answers.
3. The instructor marks which criteria AI marking may propose (default all).
4. The system validates and saves the rubric as a version attached to the assignment.

**Alternate flows:** A1 (trigger) The instructor copies a department rubric. A copy is attached; later edits to the department rubric do not change it.

**Exception flows:** E1 (step 1) Weights do not total 100. The system refuses to save and shows the difference.

- **Postconditions:** The rubric version is stored in `assessment.rubrics`, `assessment.rubric_criteria`, and `assessment.rubric_levels`.
- **References:** BR-118. Requirement area `ASM`. Release R3.

### UC-I-07 Mark a submission manually
- **Goal:** A marker assesses a submission against the rubric and gives feedback.
- **Actors:** Primary: `teaching_assistant`, `instructor`.
- **Preconditions:** The submission is submitted. The marker is staff on the cohort.
- **Trigger:** The marker opens the marking queue.
- **Permissions:** `assessment.submission:mark` at cohort scope. ABAC: the marker is TA of or cohort instructor of the cohort; the submission is not already locked by another marker; anonymous marking hides the learner name when the assignment requires it.

**Main success flow:**
1. The system lists unmarked submissions, oldest first, with any AI proposal status.
2. The marker opens one. The system locks it to the marker for 30 minutes.
3. The marker selects a level per criterion and writes feedback, inline or overall.
4. The marker saves the mark. The system computes the grade from rubric weights and stores it unreleased.

**Alternate flows:** A1 (step 3) An AI proposal exists. The marker sees it beside the rubric and continues in UC-I-08.

**Exception flows:** E1 (step 2) The lock expired and another marker took the submission. The first marker's unsaved changes are kept as a draft and the conflict is shown.

- **Postconditions:** A mark and an unreleased grade exist. The learner sees nothing yet (BR-117).
- **References:** BR-117, BR-121. Requirement area `ASM`. Release R3.

### UC-I-08 Review AI-proposed marks and override
- **Goal:** An instructor uses AI-proposed marks to speed up marking while every grade stays a human decision.
- **Actors:** Primary: `instructor`. Supporting: `teaching_assistant`, AI marking agent, `lead_instructor`.
- **Preconditions:** AI marking ran on the assignment (BR-118) and `assessment.submission.ai_marked` was emitted for the submissions.
- **Trigger:** The instructor opens "AI proposals" for an assignment.
- **Permissions:** `assessment.submission:mark` at cohort scope (includes accepting an AI proposal); `assessment.grade:override` to change a grade after it was saved or released. ABAC: as UC-I-07; bulk acceptance passes BR-119; a TA needs delegated `assessment.grade:override` to override.

**Main success flow:**
1. The system lists proposals with level per criterion, rationale, evidence quotes, and confidence, lowest confidence first.
2. The instructor opens a proposal and checks the evidence against the response.
3. The instructor accepts it, or changes levels and enters a reason. A change is recorded as an override of the proposal.
4. After meeting the sample in BR-119, the instructor accepts the remaining eligible proposals in bulk.
5. The system stores marks with the source (`ai_accepted`, `ai_modified`, `human`) and emits `assessment.grade.overridden` for each change.

**Alternate flows:**
- A1 (step 3) The instructor rejects a proposal entirely. The submission returns to the manual queue.
- A2 (step 3) The grade was already released and policy `grades.override_approval` is on. The override waits for a `lead_instructor` (BR-120).
- A3 (trigger) A regrade request arrives (UC-L-05). A staff member other than the original marker reviews and records the outcome as an override or a confirmation.

**Exception flows:**
- E1 (step 4) The sample requirement is not met, or a proposal is below 0.6 confidence or flagged. Those proposals are excluded from bulk acceptance.
- E2 (step 1) AI marking failed for some submissions. They appear in the manual queue with the reason.

- **Postconditions:** Every grade has a human actor. Proposal acceptance rates are recorded for AI quality monitoring.
- **References:** BR-117 to BR-120, BR-122. Requirement area `ASM`. Release R3.

### UC-I-09 Release grades
- **Goal:** An instructor makes grades and feedback visible to learners at a chosen time.
- **Actors:** Primary: `instructor`. Supporting: External LMS (grade passback), Email and push provider.
- **Preconditions:** Grades exist for the assignment.
- **Trigger:** The instructor selects "Release grades", or a scheduled release time arrives.
- **Permissions:** `assessment.grade:release` at cohort scope. ABAC: no pending override approvals for the selected learners; a TA needs delegation.

**Main success flow:**
1. The system shows marked, unmarked, and pending counts and the grade distribution.
2. The instructor chooses all marked learners or a selection, and optional release of the rubric rationale.
3. The system sets the grades as released, emits `assessment.grade.released`, and notifies the learners.
4. If an LTI line item is linked, the system sends released scores to the external LMS (UC-O-13).

**Alternate flows:** A1 (step 2) The instructor schedules release for a date and time in the cohort timezone.

**Exception flows:** E1 (step 4) LTI passback fails. The system retries with backoff for 24 hours and shows failures in the gradebook.

- **Postconditions:** Released grades are visible in the Learner App and count towards the gradebook and reports.
- **References:** BR-121. Requirement area `ASM`, `INT`. Release R3.

### UC-I-10 Monitor progress and risk, and record an intervention
- **Goal:** An instructor sees who is falling behind, why, and records what they did about it.
- **Actors:** Primary: `instructor`. Supporting: `teaching_assistant`, `system` (risk job).
- **Preconditions:** The cohort has a scheduled plan with at least 7 days of activity.
- **Trigger:** The instructor opens the cohort dashboard, or a risk notification.
- **Permissions:** `classroom.risk_signal:read` and `classroom.intervention:create` at cohort scope. ABAC: for personal-account members, learning record data is shown only for concepts in the cohort's curricula and within consent (ADR 0021).

**Main success flow:**
1. The system shows each learner's plan progress, mastery on plan concepts, last activity, and open risk signals.
2. The instructor filters by risk type and opens a learner.
3. The system shows the evidence for each signal (BR-115).
4. The instructor records an intervention: type (message, meeting, extension, referral), note, and follow-up date.
5. The system stores it in `classroom.interventions`, emits `classroom.intervention.recorded`, and reminds the instructor on the follow-up date.

**Alternate flows:** A1 (step 4) The instructor grants an extension. The system creates an accommodation (BR-125) and updates the learner's due dates.

**Exception flows:** E1 (step 1) The cohort has fewer than 5 learners. Cohort averages are hidden, individual rows are shown.

- **Postconditions:** Intervention notes are part of the academic record and are never shown to the learner unless the instructor marks them shared.
- **References:** BR-115, BR-125. Requirement area `INS`, `ANL`. Release R3.

### UC-I-11 Record attendance and analyse engagement
- **Goal:** An instructor records attendance at live sessions and sees how engagement relates to progress.
- **Actors:** Primary: `instructor`. Supporting: `teaching_assistant`, `learner` (check-in).
- **Preconditions:** The plan has a live session or a required activity window.
- **Trigger:** The session starts, or the instructor opens Attendance.
- **Permissions:** `classroom.attendance:record` and `analytics.dashboard:read` at cohort scope. ABAC: edits after 7 days need a reason (BR-116).

**Main success flow:**
1. The system opens a register with every cohort member and check-in status.
2. Learners check in with a session code during the window; the system marks them `present` or `late`.
3. The instructor corrects statuses and marks `excused` with a reason.
4. The instructor closes the register. The system emits `classroom.attendance.recorded`.
5. The engagement view shows attendance rate, weekly active minutes, and plan completion per learner and for the cohort.

**Alternate flows:** A1 (step 2) The window is an online activity. Attendance is derived from activity events in the window.

**Exception flows:** E1 (step 2) A check-in comes from outside the organisation's IP allowlist when one is required. The check-in is held unrecorded until the instructor accepts or rejects it.

- **Postconditions:** Attendance records exist and feed risk signals.
- **References:** BR-115, BR-116, BR-150. Requirement area `INS`, `ANL`. Release R3.

### UC-I-12 Message a cohort through the communication hub
- **Goal:** An instructor sends announcements and holds conversations with learners inside the platform.
- **Actors:** Primary: `instructor`. Supporting: `learner`, Email and push provider.
- **Preconditions:** The cohort has members.
- **Trigger:** The instructor selects "New announcement" or "Message".
- **Permissions:** `messaging.announcement:create` and `messaging.message:send` at cohort scope. ABAC: recipients are members of a cohort the sender teaches; learner-to-learner messages only if cohort setting allows.

**Main success flow:**
1. The instructor writes the message in a locale and optionally attaches a plan item link.
2. The instructor chooses recipients: whole cohort, a filtered group (for example learners with a risk signal), or one learner.
3. The system stores the announcement or thread and delivers in-app, plus email or push according to each learner's preferences.
4. Learners reply in a thread. The instructor sees read counts for announcements.

**Alternate flows:** A1 (step 3) The instructor schedules the announcement.

**Exception flows:** E1 (step 3) An email bounces. The provider reports it; the system marks the address undeliverable and shows it to the instructor.

- **Postconditions:** Messages are part of the academic record and follow the organisation's retention policy.
- **References:** BR-147. Requirement area `MSG`, `NTF`. Release R3.

### UC-I-13 View performance analytics
- **Goal:** An instructor sees how the cohort performs on concepts and assessments and where teaching should change.
- **Actors:** Primary: `instructor`. Supporting: `lead_instructor`.
- **Preconditions:** The cohort has graded or practice activity.
- **Trigger:** The instructor opens Analytics.
- **Permissions:** `analytics.dashboard:read` at cohort scope; department comparisons need the role at department scope. ABAC: groups under 10 learners are suppressed in comparisons (BR-150).

**Main success flow:**
1. The system shows mastery distribution per concept, item difficulty and discrimination, grade distribution per assignment, and completion over time.
2. The instructor drills into a concept to see which items and lessons learners struggled with.
3. The instructor exports the view as CSV or PDF in the cohort locale.

**Alternate flows:** A1 (step 1) A `lead_instructor` compares cohorts that share a release.

**Exception flows:** E1 (step 1) Data is older than the 15-minute analytics refresh. The system shows the last refresh time.

- **Postconditions:** Exports are logged and kept for 7 days.
- **References:** BR-150. Requirement area `ANL`, `RPT`. Release R3.

### UC-I-14 Handle a content update to a pinned release
- **Goal:** An instructor decides whether a cohort moves to a newer release of its course or path.
- **Actors:** Primary: `instructor`. Supporting: `content_publisher` (upstream), `system`.
- **Preconditions:** The cohort is pinned to a release and a newer release was published (UC-C-09).
- **Trigger:** The instructor receives the release notification produced from `content.release.published`.
- **Permissions:** `classroom.cohort_plan:edit` at cohort scope. ABAC: no assignment linked to changed items is open (or the instructor accepts that those items update after close, BR-129).

**Main success flow:**
1. The system shows the release notes, version change, and a diff against the pinned release: items added, changed, removed, and reordered.
2. The system shows the effect on this cohort: overlay conflicts, plan items affected, and learners with progress on changed items.
3. The instructor accepts the update. The system rebases the overlay onto the new release and keeps completed items' evidence.
4. The system emits `classroom.cohort_plan.rebased` and notifies learners of changed items.

**Alternate flows:**
- A1 (trigger) The release is a PATCH. The system has already applied it (BR-129) and the notification is informational.
- A2 (step 3) The instructor declines. The cohort stays on its release until the plan ends.

**Exception flows:** E1 (step 3) A hidden or reordered item no longer exists. The overlay entry is dropped and listed for the instructor.

- **Postconditions:** The cohort is pinned to exactly one release (BR-112).
- **References:** BR-112, BR-128 to BR-130. Requirement area `INS`, `CST`. Release R3.

## 8. Institution App use cases

Institution App use cases run in one organisation context. Campus and department roles see only their subtree.

### UC-O-01 Set up the organisation
- **Goal:** The first `org_owner` turns a provisioned organisation into a working tenant.
- **Actors:** Primary: `org_owner`. Supporting: `platform_admin` (provisioned it, UC-A-01).
- **Preconditions:** The organisation exists with a licence and the owner has accepted the owner invitation.
- **Trigger:** The owner signs in to the Institution App for the first time.
- **Permissions:** `tenancy.organisation:edit` at organisation scope. ABAC: MFA in the last 10 minutes for contract fields.

**Main success flow:**
1. The system runs a setup checklist: profile, structure, administrators, sign-in method, branding, policies, first cohort.
2. The owner enters the legal name, display name, kind, country, default locale, timezone, and data protection contact.
3. The owner invites one or more `org_admin` holders.
4. The system records each completed step and shows what is still needed before learners can join.

**Alternate flows:** A1 (step 1) The owner skips optional steps. The checklist stays on the home page until dismissed.

**Exception flows:** E1 (step 3) The owner tries to remove themselves as the only `org_owner`. Refused (BR-109).

- **Postconditions:** The organisation profile is complete and `tenancy.organisation.updated` is emitted.
- **References:** BR-109, BR-111. Requirement area `ORG`, `TEN`. Release R3.

### UC-O-02 Manage campus and department structure
- **Goal:** An administrator mirrors the organisation's real structure so that roles, reports, and cohorts follow it.
- **Actors:** Primary: `org_admin`. Supporting: `campus_admin`.
- **Preconditions:** The organisation is set up.
- **Trigger:** The administrator opens Structure.
- **Permissions:** `tenancy.org_unit:edit` at the scope of the parent unit. ABAC: the new parent is inside the actor's scope; the depth rules of ADR 0015 hold.

**Main success flow:**
1. The system shows the org-unit tree with counts of staff, cohorts, and learners per unit.
2. The administrator adds a campus or department, or a faculty with departments below it.
3. The administrator moves a department to a new parent. The system shows affected role assignments and reports before confirming.
4. The system updates `ltree` paths, and role assignments follow their unit.

**Alternate flows:** A1 (step 2) The administrator imports the structure from CSV with `code`, `name`, `kind`, and `parent_code` columns, validated as in BR-114.

**Exception flows:** E1 (step 2) A third department level is requested. Refused with the depth rule.

- **Postconditions:** The tree is valid. Moves and renames are audited.
- **References:** BR-110. Requirement area `ORG`, `TEN`. Release R3.

### UC-O-03 Manage instructors and staff roles
- **Goal:** An administrator gives staff the roles they need at the right scope, and removes them when they leave.
- **Actors:** Primary: `org_admin`. Supporting: `department_admin`, `campus_admin`, `org_owner`.
- **Preconditions:** The staff member is or will be a member of the organisation.
- **Trigger:** The administrator opens People and selects "Add staff" or a person.
- **Permissions:** `authz.role_assignment:grant` and `authz.role_assignment:revoke` at the target scope. ABAC: BR-109 to BR-110; the target role is grantable by the actor's role.

**Main success flow:**
1. The administrator invites a staff member by email, or selects an existing member.
2. The administrator assigns roles with scopes, for example `instructor` at the Computer Science department.
3. The system saves assignments, emits `authz.role_assignment.changed`, and the person sees the Instructor App in the app launcher on their next request.
4. The administrator reviews a person's assignments and removes those no longer needed.

**Alternate flows:** A1 (step 4) A staff member leaves. The administrator ends the membership; the system removes all assignments in the organisation and reassigns open marking to the cohort's other staff.

**Exception flows:** E1 (step 2) A `department_admin` tries to assign `org_admin`. Refused (BR-110).

- **Postconditions:** Assignments are stored and audited with actor, scope, and reason.
- **References:** BR-109, BR-110. Requirement area `ORG`, `AUTHZ`. Release R3.

### UC-O-04 Manage cohorts at scale
- **Goal:** An administrator creates and maintains hundreds of cohorts each term without doing it one by one.
- **Actors:** Primary: `department_admin`. Supporting: `org_admin`, `lead_instructor`.
- **Preconditions:** The structure and staff exist.
- **Trigger:** The administrator opens Cohorts at the start of a term.
- **Permissions:** `classroom.cohort:create`, `classroom.cohort:archive`, and `classroom.cohort_staff:assign` at department scope or above.

**Main success flow:**
1. The administrator uploads a cohort CSV with code, name, parent unit, dates, timezone, staff emails, and release to pin.
2. The system validates every row and shows a preview as in UC-I-02.
3. The administrator confirms. The system creates cohorts, staff assignments, and draft plans.
4. At term end, the administrator archives cohorts in bulk. Archived cohorts become read-only and their seats are not affected.

**Alternate flows:** A1 (step 1) Cohorts are synchronised from an SIS through OneRoster (R4) instead of CSV.

**Exception flows:** E1 (step 2) A staff email is not an organisation member. That row fails with the reason.

- **Postconditions:** Cohorts exist with staff and draft plans that instructors complete in UC-I-04.
- **References:** BR-113, BR-114. Requirement area `ORG`, `INS`. Release R3.

### UC-O-05 Manage licences, seats, billing, and invoices
- **Goal:** A billing manager controls who uses the organisation's seats and pays for them.
- **Actors:** Primary: `org_billing_manager`. Supporting: Stripe, `finance_admin`.
- **Preconditions:** The organisation has a licence (UC-A-01).
- **Trigger:** The billing manager opens Licences or Billing, or receives a seat warning.
- **Permissions:** `commerce.seat:assign`, `commerce.invoice:read`, and `commerce.payment_method:edit` at organisation scope. ABAC: MFA in the last 10 minutes for payment methods.

**Main success flow:**
1. The system shows each licence: plan, term, seat count, seats used, overage, and entitlements.
2. The billing manager assigns seat pools to campuses or departments, or reclaims seats from members inactive for 90 days.
3. The billing manager requests more seats. The system creates a quote; on acceptance Stripe issues a prorated invoice and the system emits `commerce.licence.changed`.
4. The billing manager views and downloads invoices and updates the payment method or purchase order number.

**Alternate flows:** A1 (step 3) The contract is invoiced offline. The request goes to `finance_admin`, who applies the change in UC-A-07.

**Exception flows:** E1 (step 4) A Stripe payment fails. The system notifies billing managers and, after 30 days unpaid, `finance_admin`; access is not cut automatically.

- **Postconditions:** Seat assignments match licence limits (BR-107, BR-108). Changes are audited.
- **References:** BR-107, BR-108. Requirement area `LIC`. Release R3.

### UC-O-06 Configure branding and a custom domain
- **Goal:** The organisation's learners and staff see its name, logo, and colours, and optionally its own domain.
- **Actors:** Primary: `org_admin`.
- **Preconditions:** The licence includes branding; custom domains need the white-label entitlement (R4).
- **Trigger:** The administrator opens Branding.
- **Permissions:** `tenancy.branding:edit` and, for domains, `tenancy.domain:verify` at organisation scope.

**Main success flow:**
1. The administrator uploads a logo (SVG or PNG, at most 1 MB) and chooses primary and accent colours.
2. The system checks colour contrast against WCAG 2.2 AA and previews the Learner App and Instructor App.
3. The administrator saves. Branding applies in this tenant context in every app.
4. For a custom domain, the administrator enters a host such as `learn.example.ac.uk`; the system shows DNS TXT and CNAME records, verifies them, and issues a certificate (BR-153).

**Alternate flows:** A1 (step 3) Branded email templates use the same logo and colours.

**Exception flows:** E1 (step 2) Contrast fails. The system proposes the nearest passing colour and refuses to save the failing pair.

- **Postconditions:** Branding is stored in `tenancy.branding`; domains in `tenancy.domains`.
- **References:** BR-153. Requirement area `ORG`. Release R3 (custom domain R4).

### UC-O-07 Configure SSO with SAML or OIDC and JIT provisioning
- **Goal:** Members sign in with the organisation's identity provider and accounts are created on first sign-in.
- **Actors:** Primary: `org_admin`. Supporting: Customer IdP, Clerk.
- **Preconditions:** The licence includes SSO. The administrator can configure the customer IdP.
- **Trigger:** The administrator opens Sign-in and selects "Add SSO connection".
- **Permissions:** `tenancy.sso_connection:configure` at organisation scope. ABAC: MFA in the last 10 minutes; the email domains are verified (BR-151).

**Main success flow:**
1. The administrator verifies each email domain by a DNS TXT record.
2. The administrator chooses SAML 2.0 (metadata URL or XML) or OIDC (issuer, client id, secret).
3. The administrator maps IdP attributes and groups: email, names, external id, and optional groups to roles at scopes.
4. The administrator tests the connection with their own sign-in. The system shows received attributes.
5. The administrator enables the connection and chooses whether SSO is required for the verified domains.

**Alternate flows:** A1 (step 5) SSO is optional. Members can still use password sign-in until the administrator enforces SSO.

**Exception flows:** E1 (step 4) The assertion is unsigned, expired, or for another audience. The test fails with the reason and the connection stays disabled.

- **Postconditions:** The connection is stored in `tenancy.sso_connections`. First sign-ins follow UC-P-01.
- **References:** BR-106, BR-151. Requirement area `IAM`. Release R3.

### UC-O-08 Connect SCIM provisioning
- **Goal:** The organisation's IdP creates, updates, and deactivates managed accounts automatically.
- **Actors:** Primary: `org_admin`. Supporting: SCIM client.
- **Preconditions:** An SSO connection is enabled (UC-O-07).
- **Trigger:** The administrator opens Provisioning and selects "Connect SCIM".
- **Permissions:** `integration.scim_client:configure` at organisation scope; the SCIM client acts as a `system` principal limited to `/scim/v2/...` for this organisation.

**Main success flow:**
1. The system generates a bearer token, shown once, and the SCIM base URL.
2. The administrator configures the IdP and maps groups to cohorts or roles.
3. The SCIM client creates users and groups. The system creates managed accounts, memberships, and mapped assignments.
4. When the IdP deactivates a user, the system suspends the membership and later ends it (BR-152).

**Alternate flows:** A1 (step 3) A SCIM user matches an existing account created by JIT. The system links it by IdP subject instead of creating another.

**Exception flows:** E1 (step 3) The token is revoked or expired. Calls fail with 401 and the administrator is notified after 10 failures in an hour.

- **Postconditions:** Each SCIM call is logged in `integration.scim_clients` activity with counts.
- **References:** BR-105, BR-107, BR-152. Requirement area `IAM`, `INT`. Release R4.

### UC-O-09 Run reports and schedule exports
- **Goal:** A report viewer answers questions about learning across the organisation and sends results to the people who need them.
- **Actors:** Primary: `org_report_viewer`. Supporting: `system` (report job, UC-P-04).
- **Preconditions:** The organisation has activity.
- **Trigger:** The viewer opens Reports.
- **Permissions:** `reporting.report:read` and `reporting.report:schedule` at the viewer's scope. ABAC: rows are limited to the viewer's subtree; BR-150 suppression; personal-account learning data within consent (ADR 0021).

**Main success flow:**
1. The viewer picks a report: enrolment and completion, mastery by concept, assessment results, engagement, licence use, or AI mentor use.
2. The viewer filters by unit, cohort, release, date range, and locale.
3. The system renders the report in the viewer's locale.
4. The viewer schedules it weekly or monthly to recipients who hold report access, as CSV, XLSX, or PDF.

**Alternate flows:** A1 (step 4) The viewer sends the export to an SFTP or webhook endpoint configured by an `org_admin`.

**Exception flows:** E1 (step 4) A recipient lacks report access at that scope. The system refuses to add them.

- **Postconditions:** Report runs and schedules are stored and audited.
- **References:** BR-150. Requirement area `RPT`, `ANL`. Release R3.

### UC-O-10 Produce a workforce development report
- **Goal:** An enterprise sees skill coverage against target roles across teams.
- **Actors:** Primary: `org_report_viewer`. Supporting: `org_admin`.
- **Preconditions:** The organisation has defined target roles for departments or teams, or uses the role catalogue.
- **Trigger:** The viewer opens Workforce.
- **Permissions:** `reporting.report:read` at organisation or department scope. ABAC: individual rows only for managed accounts or personal accounts that shared a career plan (UC-L-10, A2); BR-150.

**Main success flow:**
1. The viewer selects target roles and the org units to compare.
2. The system computes coverage per role: share of members at mastery 75 or more for each required concept, path completion, and certifications earned.
3. The system shows gaps by team and recommends paths that close the largest gaps.
4. The viewer exports the report or assigns a recommended path to a cohort (UC-I-04).

**Alternate flows:** A1 (step 2) The viewer compares two dates to show change over a quarter.

**Exception flows:** E1 (step 2) A team has fewer than 10 members. Its row is merged into the parent unit.

- **Postconditions:** The report run is stored for comparison.
- **References:** BR-08, BR-150. Requirement area `RPT`. Release R4.

### UC-O-11 Handle a data subject request and set retention
- **Goal:** The organisation meets its GDPR duties for the data it controls.
- **Actors:** Primary: `org_compliance_officer`. Supporting: `system` (erasure and retention jobs), `support_agent`.
- **Preconditions:** A data subject request was received by the organisation, or retention needs setting.
- **Trigger:** The officer opens Compliance and records a request, or edits retention.
- **Permissions:** `audit.dsar:process` and `audit.retention_policy:edit` at organisation scope. ABAC: MFA in the last 10 minutes; requests cover only data the organisation controls (BR-146).

**Main success flow:**
1. The officer records the request type (access, rectification, erasure, restriction, portability), the subject, and the identity check done.
2. The system shows what data exists for the subject in this tenant: academic record, and for managed accounts the learning record.
3. For access or portability, the system generates an export. For erasure, the system runs UC-P-06 for a managed account, or erases the academic record for a personal-account member.
4. The system tracks the 30-day deadline and records completion.
5. In Retention, the officer sets periods per category (submissions, grades, messages, conversations, attendance) within platform limits (BR-147).

**Alternate flows:** A1 (step 3) A legal hold applies. The officer records it and erasure waits.

**Exception flows:** E1 (step 2) The subject is a personal account and the request concerns its learning record. The system redirects the request to AI Mentor as controller and notifies `support_agent`.

- **Postconditions:** The request, actions, and evidence are stored in `audit`. Retention changes are audited.
- **References:** BR-146 to BR-148. Requirement area `ORG`, `NFR`. Release R3.

### UC-O-12 Configure organisation policies
- **Goal:** An administrator sets the rules that shape learning in the organisation.
- **Actors:** Primary: `org_admin`. Supporting: `org_compliance_officer`.
- **Preconditions:** The organisation is set up.
- **Trigger:** The administrator opens Policies.
- **Permissions:** `tenancy.org_policy:edit` at organisation scope. ABAC: policies that reduce privacy protections need `org_owner`.

**Main success flow:**
1. The system shows policy groups with current values and defaults: leaderboards (`leaderboards.public_participation`), mentor (`mentor.allowed_modes`, `mentor.persona_attributes`), personalisation bounds, grading (`grades.override_approval`, `grades.regrade_may_lower`), records (`records.passport_export`), members (`members.instructor_can_create`), locales, and IP allowlist.
2. The administrator changes values. The system explains the effect of each change.
3. The system saves the policy in `tenancy.org_policies` and emits `tenancy.org_policy.changed`.
4. The new values apply on the next request in this tenant.

**Alternate flows:** A1 (step 2) The administrator sets a policy for one campus or department, which overrides the organisation value below that unit.

**Exception flows:** E1 (step 2) A personalisation bound leaves no allowed value with an existing cohort lock. Refused with the conflicting cohorts (BR-140).

- **Postconditions:** Policy versions are kept and audited.
- **References:** BR-137, BR-140, BR-141. Requirement area `ORG`, `TEN`. Release R3.

### UC-O-13 Connect an external LMS through LTI 1.3
- **Goal:** Learners launch AI Mentor content from Canvas or Moodle and grades return to the LMS gradebook.
- **Actors:** Primary: `org_admin`. Supporting: External LMS.
- **Preconditions:** The licence includes LTI. The LMS administrator is available.
- **Trigger:** The administrator opens Integrations and selects "Add LTI platform".
- **Permissions:** `integration.lti_platform:configure` at organisation scope.

**Main success flow:**
1. The system shows the tool's OIDC login URL, launch URL, JWKS URL, and deep-linking URL.
2. The administrator enters the platform's issuer, client id, deployment ids, and JWKS URL.
3. An LMS course launches AI Mentor. The system validates the launch, finds or creates the cohort linked to the LMS context, and creates a membership for the launching user.
4. Instructors use deep linking to place plan items in the LMS; grade passback uses AGS line items (UC-I-09).

**Alternate flows:** A1 (step 3) Roster sync uses NRPS to add the whole LMS class to the cohort.

**Exception flows:** E1 (step 3) The launch has a wrong `iss`, `aud`, or nonce, or an unknown deployment. The launch is refused and logged.

- **Postconditions:** Platforms and deployments are stored in `integration.lti_platforms` and `integration.lti_deployments`.
- **References:** BR-105, BR-121. Requirement area `INT`. Release R4.

## 9. Admin App use cases

Admin App endpoints accept only tokens with the Admin App audience. Every action runs in the `platform` context and is audited.

### UC-A-01 Provision an organisation
- **Goal:** Platform staff create a new tenant with its licence and first owner.
- **Actors:** Primary: `platform_admin`. Supporting: `finance_admin`, Email and push provider.
- **Preconditions:** A signed contract or an approved pilot exists.
- **Trigger:** The admin selects "New organisation".
- **Permissions:** `tenancy.organisation:create` at platform scope. ABAC: Admin App audience; MFA in the last 10 minutes.

**Main success flow:**
1. The admin enters name, slug, kind, country, data region, and default locale.
2. `finance_admin` or the admin attaches a plan, seat count, term, and entitlements, creating a licence.
3. The admin invites the first `org_owner` by email.
4. The system creates the organisation root unit, the licence, and the invitation, and emits `tenancy.organisation.created` and `commerce.licence.changed`.

**Alternate flows:** A1 (step 1) The organisation is a `publisher`. The system also creates an `org` workspace in Content Studio.

**Exception flows:** E1 (step 1) The slug is taken or reserved (for example `ai-mentor-public`). The system asks for another.

- **Postconditions:** The tenant exists and is empty until the owner completes UC-O-01.
- **References:** BR-109, BR-111. Requirement area `ADM`, `TEN`. Release R3.

### UC-A-02 Manage platform users and staff roles
- **Goal:** A platform admin finds any account, changes its status, and manages platform staff roles (extends UC-35).
- **Actors:** Primary: `platform_admin`. Supporting: `support_agent`, Clerk.
- **Preconditions:** None.
- **Trigger:** The admin opens Users or Staff.
- **Permissions:** `identity.account:read`, `identity.account:suspend`, `authz.role_assignment:grant`, and `authz.role_assignment:revoke` at platform scope. ABAC: BR-111; nobody edits their own assignments (BR-110); organisation roles are not editable here.

**Main success flow:**
1. The admin searches accounts by email, name, or id. The system shows account type, home tenant, memberships (names only), plan, and status.
2. The admin suspends or reinstates an account with a reason. Suspension ends sessions through Clerk.
3. In Staff, the admin assigns or removes a platform role such as `ai_admin`.
4. The system writes the change to `authz.role_assignments` and the audit log.

**Alternate flows:** A1 (step 1) A `support_agent` performs the search with a ticket reference and sees a reduced view.

**Exception flows:** E1 (step 3) The change would leave no `platform_admin`. Refused.

- **Postconditions:** Changes apply on the next request and are audited.
- **References:** BR-110, BR-111. Requirement area `ADM`, `AUTHZ`. Release R2.

### UC-A-03 Configure AI services and model routing with an evaluation gate
- **Goal:** An AI admin changes models, routes, and prompts without lowering quality or safety (extends UC-37).
- **Actors:** Primary: `ai_admin`. Supporting: LLM providers, `system` (evaluation runner).
- **Preconditions:** Provider keys are in the secrets manager.
- **Trigger:** The AI admin opens Models or Prompts.
- **Permissions:** `ai.model:register`, `ai.model_route:edit`, and `ai.prompt_release:publish` at platform scope. ABAC: MFA in the last 10 minutes; promotion only after the gate passes (BR-145).

**Main success flow:**
1. The AI admin registers a model in `platform.model_registry` with provider, version, data-processing region, and cost.
2. The AI admin drafts a route change per task (tutor modes, embeddings, AI marking, content generation) or a new prompt release.
3. The system runs the evaluation suite and shows scores beside the baseline.
4. The gate passes. The system starts a 5 percent canary for 24 hours, then rolls out fully and emits `ai.model_route.changed`.

**Alternate flows:** A1 (step 4) Canary error or flag rates rise above baseline. The system rolls back automatically and alerts the AI admin.

**Exception flows:** E1 (step 3) A safety test fails. Promotion is blocked; only a `platform_admin` can record an exception, which is audited.

- **Postconditions:** Routes and prompt releases are versioned and every AI call records the version it used.
- **References:** BR-145. Requirement area `ADM`, `TUT`. Release R2.

### UC-A-04 Manage feature flags, rollout, and platform settings
- **Goal:** An operator turns features on gradually, switches them off fast, and maintains platform settings.
- **Actors:** Primary: `platform_operator`.
- **Preconditions:** The flag or setting is defined in code with a default.
- **Trigger:** The operator opens Flags or Settings.
- **Permissions:** `platform.feature_flag:edit` and `platform.setting:edit` at platform scope. ABAC: MFA in the last 10 minutes for settings marked sensitive (rate limits, data retention bounds).

**Main success flow:**
1. The operator selects a flag such as `instructor.ai_marking` and sees its rules and current exposure.
2. The operator adds rules: by app, organisation, plan, locale, or percentage of accounts (BR-143).
3. The operator saves with a reason. The system emits `config.feature_flag.changed`.
4. In Settings, the operator changes values such as global rate limits (BR-12) or retention bounds (BR-147), with the same reason and audit.

**Alternate flows:** A1 (step 2) The operator uses the kill switch. The flag is off everywhere within 60 seconds.

**Exception flows:** E1 (step 4) A value is outside the setting's allowed range. Refused.

- **Postconditions:** Flag and setting history is kept with actor and reason.
- **References:** BR-12, BR-143, BR-147. Requirement area `ADM`, `PLT`. Release R2.

### UC-A-05 Review audit logs
- **Goal:** An auditor reconstructs who did what, when, and in which tenant.
- **Actors:** Primary: `security_auditor`. Supporting: `org_compliance_officer` (organisation-scoped view in the Institution App).
- **Preconditions:** Audit entries exist.
- **Trigger:** The auditor opens Audit, or follows an alert.
- **Permissions:** `audit.log:read` at platform scope. ABAC: read-only; free-text fields with personal data are masked unless the auditor records a reason.

**Main success flow:**
1. The auditor filters by actor, tenant, action, resource, decision (allow or deny), and time.
2. The system shows entries from the audit trail, `authz.decision_log`, and `audit.data_access_log`, linked by `correlationid`.
3. The auditor exports the result as signed CSV for an investigation.

**Alternate flows:** A1 (step 1) An `org_compliance_officer` uses the same view limited to their organisation.

**Exception flows:** E1 (step 3) The export exceeds 1 million rows. The system asks the auditor to narrow the filter.

- **Postconditions:** Audit reads are themselves audited. The audit trail is append-only.
- **References:** BR-142, BR-150. Requirement area `ADM`. Release R2.

### UC-A-06 Monitor security events
- **Goal:** Security staff detect and respond to attacks and abuse across tenants (extends UC-38).
- **Actors:** Primary: `security_auditor`. Supporting: `platform_operator`, Clerk.
- **Preconditions:** Security events are collected.
- **Trigger:** An alert fires, or the auditor opens Security.
- **Permissions:** `audit.security_event:read` at platform scope; acting needs `identity.account:suspend` (`platform_admin`, or `support_agent` with a ticket).

**Main success flow:**
1. The system shows signals: failed sign-ins, token audience mismatches, cross-tenant denials, SCIM and LTI failures, prompt-injection rejections, sandbox violations, and XP anomalies.
2. The auditor opens an event with its context and related events.
3. The auditor escalates to an operator, who blocks an IP range, suspends an account, revokes an integration token, or tightens a per-tenant rate limit (BR-144).

**Alternate flows:** A1 (step 3) The event affects one organisation. Its `org_compliance_officer` is notified.

**Exception flows:** E1 (step 3) The account to suspend is an `org_owner`. The system warns that the organisation may lose its only owner and requires a reason.

- **Postconditions:** Events and responses are audited.
- **References:** BR-109, BR-144. Requirement area `ADM`, `NFR`. Release R2.

### UC-A-07 Manage subscriptions and plans
- **Goal:** Finance maintains consumer plans and organisation licences and resolves billing issues.
- **Actors:** Primary: `finance_admin`. Supporting: Stripe.
- **Preconditions:** Plans exist in `commerce.plans`.
- **Trigger:** The finance admin opens Plans, Subscriptions, or Licences.
- **Permissions:** `commerce.plan:edit`, `commerce.subscription:manage`, `commerce.licence:edit`, and `commerce.refund:issue` at platform scope. ABAC: MFA in the last 10 minutes for refunds.

**Main success flow:**
1. The finance admin edits a plan's price, entitlements, and Stripe price ids, effective from a date.
2. The finance admin opens a subscription or licence and changes term, seats, or entitlements.
3. The system updates Stripe and emits `commerce.subscription.changed` or `commerce.licence.changed`; `authz` refreshes entitlements.
4. The finance admin issues a refund or credit note with a reason.

**Alternate flows:** A1 (step 1) Existing subscribers keep the old price until renewal unless the change is a reduction.

**Exception flows:** E1 (step 3) Stripe is unavailable. The change is queued and retried; entitlements do not change until Stripe confirms.

- **Postconditions:** Commerce records agree with Stripe; webhook reconciliation runs daily.
- **References:** BR-107, BR-108. Requirement area `LIC`. Release R2.

### UC-A-08 Produce global reports
- **Goal:** Leadership sees platform-wide adoption, learning, AI, and revenue measures (extends UC-36).
- **Actors:** Primary: `platform_admin`. Supporting: `finance_admin`, `system` (report job).
- **Preconditions:** Analytics data exists.
- **Trigger:** The admin opens Global reports.
- **Permissions:** `analytics.dashboard:read` at platform scope. ABAC: tenant-level rows only as aggregates; BR-150 applies.

**Main success flow:**
1. The admin selects a report: active learners by app and tenant kind, retention, organisation adoption, AI cost and quality, content usage, or revenue.
2. The system renders it from the analytics warehouse with tenants grouped by kind and region.
3. The admin schedules or exports it (UC-P-04).

**Alternate flows:** A1 (step 2) The admin names one organisation. This is a tenant data read and requires a reason (UC-A-10).

**Exception flows:** E1 (step 2) The warehouse feed is delayed. The report shows its data freshness.

- **Postconditions:** Report runs are audited.
- **References:** BR-150. Requirement area `RPT`, `ANL`. Release R2.

### UC-A-09 Resolve knowledge governance escalations
- **Goal:** Platform staff deal with flagged tutor answers, content quality issues, and rights complaints that cross teams (extends UC-34).
- **Actors:** Primary: `platform_admin`. Supporting: `knowledge_steward`, `content_publisher`, `learner` (reporter).
- **Preconditions:** A flag, rights complaint, or quality alert exists.
- **Trigger:** An item enters the moderation queue from `tutor.message.flagged`, a takedown request, or a quality alert.
- **Permissions:** `tutor.flagged_message:review` at platform scope. ABAC: reading the conversation behind a flag in an organisation tenant is a tenant data read with a reason.

**Main success flow:**
1. The system shows the item with category, reporter, and linked assets, concepts, and releases.
2. The admin classifies it: incorrect, unsafe, rights issue, outdated, or not an issue.
3. The admin assigns a fix to the workspace that owns the content; a draft change opens in Content Studio.
4. The item closes when the fix is published, or when a takedown completes (UC-C-12).

**Alternate flows:** A1 (step 2) Unsafe output caused by a prompt. The item goes to `ai_admin` for a prompt release fix.

**Exception flows:** E1 (step 3) The content is in an organisation's `org` workspace. The fix goes to that organisation's content staff and its `org_admin` is notified.

- **Postconditions:** Outcomes are stored and feed content quality analytics.
- **References:** BR-130, BR-131. Requirement area `ADM`, `KM`. Release R2.

### UC-A-10 Use break-glass access to tenant data
- **Goal:** Platform staff read a tenant's data to solve a support case or incident, with a record of why.
- **Actors:** Primary: `support_agent`, `platform_admin`. Supporting: `org_owner`, `org_compliance_officer` (notified).
- **Preconditions:** A ticket or incident exists.
- **Trigger:** The staff member selects "Access tenant data" on an organisation.
- **Permissions:** `platform.tenant_data:read` at platform scope. ABAC: BR-142 conditions; `support_agent` limited to account, membership, and subscription data.

**Main success flow:**
1. The staff member enters the reason, ticket reference, and data categories needed.
2. The system checks MFA freshness and opens a read-only session for at most 60 minutes.
3. Every query in the session is logged in `audit.data_access_log` with the reason and session id.
4. The session ends at expiry or on request. The organisation's owner and compliance officer receive a notice within 24 hours.

**Alternate flows:** A1 (step 2) Write access is needed. A second `platform_admin` approves, and the session allows writes for the named categories only.

**Exception flows:** E1 (step 4) A security incident requires deferring the notice. A `platform_admin` records a deferral of at most 7 days.

- **Postconditions:** The session, its reads, and the notice are audited and visible to the organisation in UC-A-05, A1.
- **References:** BR-142. Requirement area `ADM`, `AUTHZ`. Release R3.

## 10. Content Studio use cases

Content Studio use cases run in a workspace: `master` for platform content or an organisation's `org` workspace. Role assignments are at workspace scope.

### UC-C-01 Upload and ingest an asset with metadata and rights
- **Goal:** An author adds a governed source that becomes retrievable once published (extends UC-26 and UC-27).
- **Actors:** Primary: `content_author`. Supporting: `system` (ingestion worker), LLM providers (embeddings).
- **Preconditions:** The author holds `content_author` in the workspace.
- **Trigger:** The author selects "Add asset".
- **Permissions:** `knowledge.asset:upload` at workspace scope. ABAC: the asset kind is enabled for the workspace; file size and type limits for the kind.

**Main success flow:**
1. The author uploads a file or link and chooses one of the 13 asset kinds.
2. The author enters metadata: title, locale, concepts, taxonomy nodes, level, authors, source, `rights`, and `licence_terms`.
3. The system stores a draft asset version and starts ingestion: extraction, chunking (BR-17), embedding, and concept tagging suggestions.
4. The author confirms suggested concepts and submits the asset for review (UC-C-08).

**Alternate flows:** A1 (step 3) The file is a new version of an existing asset. The system links it and keeps the previous version published until the new one is.

**Exception flows:** E1 (step 4) Rights metadata is missing or `unknown`. Submission is refused (BR-131).

- **Postconditions:** A draft asset version with chunks exists; chunks are retrievable only after `knowledge.asset_version.published`.
- **References:** BR-17, BR-126, BR-131. Requirement area `CST`, `KM`. Release R2.

### UC-C-02 Build a lesson
- **Goal:** An author creates the smallest learnable unit with a primary concept, objectives, and content per locale and teaching style.
- **Actors:** Primary: `content_author`.
- **Preconditions:** The primary concept exists in the knowledge graph.
- **Trigger:** The author selects "New lesson".
- **Permissions:** `content.item:edit` at workspace scope. ABAC: the author can edit only drafts; linked assets must be in the same workspace or `master`.

**Main success flow:**
1. The author sets title, primary concept, secondary concepts, objectives, level, and estimated minutes.
2. The author writes the body in the source locale, with variants for teaching approaches where needed.
3. The author links assets and adds checks (practice questions) that measure the concepts.
4. The system validates links, objectives, and accessibility (alt text, captions) and saves the draft.

**Alternate flows:** A1 (step 2) The author starts from an AI-generated draft (UC-C-10).

**Exception flows:** E1 (step 4) An image lacks alt text or a video lacks captions. Submission is blocked until fixed.

- **Postconditions:** A draft lesson exists, ready for review.
- **References:** BR-126. Requirement area `CST`. Release R2.

### UC-C-03 Build a module and a course
- **Goal:** An author groups lessons into modules and modules into a course with outcomes, prerequisites, and assessments.
- **Actors:** Primary: `content_author`. Supporting: `knowledge_steward`.
- **Preconditions:** Lessons exist in the workspace or in `master`.
- **Trigger:** The author selects "New module" or "New course".
- **Permissions:** `content.item:edit` at workspace scope.

**Main success flow:**
1. The author creates modules and orders lessons and checks in each.
2. The author creates the course: title, summary, outcomes, level, prerequisite concepts, and estimated hours.
3. The author orders modules and attaches course assessments from the item bank (UC-C-05).
4. The system checks that each lesson's concept follows its prerequisites in the order (as v1 UC-30), and saves the draft.

**Alternate flows:** A1 (step 3) An `org` workspace author creates a derived course from a `master` release. The system records the upstream link in `curriculum.derived_course_links`.

**Exception flows:** E1 (step 4) An order breaks a prerequisite. The item is flagged and submission is blocked until fixed or acknowledged with a reason.

- **Postconditions:** A draft course exists. Its first publication will be release `1.0.0`.
- **References:** BR-126, BR-128, BR-132. Requirement area `CST`. Release R2.

### UC-C-04 Build a learning path
- **Goal:** An author sequences courses, standalone modules, and projects towards a goal or role (replaces the structure in UC-30).
- **Actors:** Primary: `content_author`.
- **Preconditions:** Course releases exist.
- **Trigger:** The author selects "New path".
- **Permissions:** `content.item:edit` at workspace scope. ABAC: referenced courses are published releases in the same workspace or `master`.

**Main success flow:**
1. The author sets title, goal or target role, level range, and target personas.
2. The author adds course releases (by version range, for example `2.x`), standalone modules, and projects in order.
3. The system checks prerequisite order across courses and computes total effort.
4. The author submits the path for review.

**Alternate flows:** A1 (step 2) A course has a newer MAJOR release. The system shows it; the author chooses which major version the path uses.

**Exception flows:** E1 (step 2) A referenced course is archived. It cannot be added.

- **Postconditions:** A draft path exists with pinned course version ranges.
- **References:** BR-126, BR-128, BR-130. Requirement area `CST`. Release R2.

### UC-C-05 Build a quiz and item bank with localisation
- **Goal:** An author creates assessment items tagged by concept and difficulty, usable in practice and graded assessments in all locales.
- **Actors:** Primary: `content_author`. Supporting: `localisation_editor`.
- **Preconditions:** Concepts exist.
- **Trigger:** The author opens Item bank and selects "New item".
- **Permissions:** `content.item:edit` at workspace scope. ABAC: items used in an open assignment cannot change scoring.

**Main success flow:**
1. The author chooses a type (multiple choice, true or false, fill in the blank, short answer, coding, written response), concept, difficulty from beginner to research level, and marks.
2. The author writes stem, options, answer, feedback, and for coding the tests and expected output (BR-13, BR-14).
3. The author groups items into a quiz with sections and timing, or leaves them in pools.
4. The author requests translations; each translation gets `translation_status` and must be approved before graded use (BR-124).

**Alternate flows:** A1 (step 2) The item is open-ended. The author attaches a model answer and a default rubric.

**Exception flows:** E1 (step 2) A multiple-choice item has no correct option or two identical options. Refused.

- **Postconditions:** Draft items exist; they reach instructors after publication.
- **References:** BR-13, BR-14, BR-124, BR-126. Requirement area `CST`, `ASM`. Release R2.

### UC-C-06 Manage the taxonomy
- **Goal:** A steward keeps the subject hierarchy and controlled vocabularies consistent (extends UC-28).
- **Actors:** Primary: `knowledge_steward`.
- **Preconditions:** The taxonomy exists.
- **Trigger:** The steward opens Taxonomy.
- **Permissions:** `knowledge.taxonomy:edit` at workspace scope.

**Main success flow:**
1. The steward adds, renames, or moves nodes, with labels in `en`, `fr`, and `es`.
2. The steward merges duplicate nodes; references move to the surviving node (BR-134).
3. The steward edits controlled vocabularies used in metadata (levels, industries, roles).
4. The system saves, reindexes search, and audits the change.

**Alternate flows:** A1 (step 1) An author proposes a node. It waits in the steward's queue.

**Exception flows:** E1 (step 2) The steward deletes a referenced node. Refused with the referencing items.

- **Postconditions:** The taxonomy is valid and depth is at most 6.
- **References:** BR-134. Requirement area `KM`. Release R2.

### UC-C-07 Edit the knowledge graph with cycle prevention
- **Goal:** A steward maintains concepts and typed relations so that sequencing and recommendations stay valid (extends UC-29).
- **Actors:** Primary: `knowledge_steward`. Supporting: `content_author` (proposes).
- **Preconditions:** Concepts exist.
- **Trigger:** The steward opens a concept.
- **Permissions:** `knowledge.concept_relation:edit` at workspace scope.

**Main success flow:**
1. The system shows the concept's relations by type and its usage in lessons and items.
2. The steward adds a relation such as `q-learning prerequisite_of deep-q-networks` with a weight.
3. The system checks acyclicity for `prerequisite_of` and `part_of` and saves (BR-132).
4. The system emits `knowledge.concept_relation.changed`, and paths whose order this edge breaks are flagged to their authors.

**Alternate flows:** A1 (step 2) An author's proposed edge is accepted or rejected with a note.

**Exception flows:** E1 (step 3) The edge would create a cycle. The system refuses and shows the cycle.

- **Postconditions:** The graph is valid and the change is audited.
- **References:** BR-132. Requirement area `KG`. Release R2.

### UC-C-08 Review content under the two-person rule
- **Goal:** Only content checked by someone other than its author is approved (extends UC-32).
- **Actors:** Primary: `content_reviewer`. Supporting: `content_author`.
- **Preconditions:** An item is `in_review`.
- **Trigger:** The reviewer opens the review queue.
- **Permissions:** `content.item:review` at workspace scope. ABAC: the reviewer authored no change in the version (BR-127).

**Main success flow:**
1. The system lists items in review with type, author, age, and change summary.
2. The reviewer opens a diff against the last published version and checks accuracy, rights, accessibility, and alignment with outcomes.
3. The reviewer comments inline and approves. The system emits `content.item.state_changed`.

**Alternate flows:** A1 (step 3) The reviewer requests changes. The item moves to `changes_requested` and back to `draft`.

**Exception flows:** E1 (step 3) The reviewer is an author of the version. Approval is refused.

- **Postconditions:** State transitions record actor, time, and comment.
- **References:** BR-126, BR-127. Requirement area `CST`. Release R2.

### UC-C-09 Publish a release with impact analysis
- **Goal:** A publisher releases an approved course or path version knowing whom it affects.
- **Actors:** Primary: `content_publisher`. Supporting: `instructor` (notified), `system` (retrieval and search reindex).
- **Preconditions:** The course or path and its changed items are `approved`.
- **Trigger:** The publisher selects "Publish release".
- **Permissions:** `content.course:publish` or `content.path:publish` at workspace scope. ABAC: BR-127 for MAJOR releases.

**Main success flow:**
1. The system computes the diff and proposes a version level (BR-128).
2. The system shows impact: cohorts pinned to earlier releases, learners affected, open assignments touching changed items, and derived courses tracking it.
3. The publisher confirms the version and writes release notes in the source locale.
4. The system creates the immutable release, emits `content.release.published`, applies PATCH releases to pinned cohorts (BR-129), and notifies instructors of MINOR and MAJOR releases (UC-I-14).

**Alternate flows:** A1 (step 3) The publisher schedules publication for a date and time.

**Exception flows:** E1 (step 3) The publisher tries to lower the proposed level. Refused.

- **Postconditions:** The release is retrievable and searchable. Earlier releases are unchanged.
- **References:** BR-127 to BR-130. Requirement area `CST`. Release R2 (impact on cohorts R3).

### UC-C-10 Generate content with AI and review it
- **Goal:** An author drafts lessons, items, flashcards, and summaries from source assets faster, under the same review (extends UC-31).
- **Actors:** Primary: `content_author`. Supporting: LLM providers.
- **Preconditions:** The source assets are ingested.
- **Trigger:** The author selects "Generate".
- **Permissions:** `content.item:generate` at workspace scope. ABAC: flag `studio.ai_generation` is on; the workspace's monthly generation budget is not exceeded.

**Main success flow:**
1. The author chooses sources, output types, concepts, level, locale, and count.
2. The system generates through `ai_gateway` from the sources' chunks only and records the model route and prompt release.
3. Each output shows citations to source sections. The system saves them as drafts labelled "AI-generated".
4. The author edits, discards, or submits each draft for review.

**Alternate flows:** A1 (step 2) The generation is long. It runs as a job and notifies the author when done.

**Exception flows:** E1 (step 3) An output has no citation. It is marked ungrounded and cannot be submitted (BR-133).

- **Postconditions:** Generated drafts exist; nothing reaches learners without review.
- **References:** BR-126, BR-133. Requirement area `CST`, `KM`. Release R2.

### UC-C-11 Localise content
- **Goal:** A localisation editor translates lessons, items, and release notes so learners can study in `fr` and `es`.
- **Actors:** Primary: `localisation_editor`. Supporting: LLM providers (machine translation draft).
- **Preconditions:** The source item is `approved` or `published`.
- **Trigger:** A translation job appears in the editor's queue for their locale.
- **Permissions:** `content.translation:edit` and `content.translation:approve` at workspace scope. ABAC: the editor's assignment covers the target locale; approver is not the translator for graded items.

**Main success flow:**
1. The editor opens the job with source text, machine draft, glossary, and translation memory matches.
2. The editor translates and keeps formulas, code, and placeholders unchanged.
3. A second editor approves the translation. The system sets `translation_status = approved`.
4. The localised version ships with the next release of the parent course.

**Alternate flows:** A1 (step 4) The parent is already published. A translation-only change ships as a PATCH release.

**Exception flows:** E1 (step 3) The source changed after the translation started. The job is marked stale and shows the source diff.

- **Postconditions:** Each locale variant has a status and translator record.
- **References:** BR-124, BR-127, BR-128. Requirement area `CST`, `I18N`. Release R2.

### UC-C-12 Retire, archive, or take down content
- **Goal:** A publisher removes content from new use, or removes it at once for legal or safety reasons.
- **Actors:** Primary: `content_publisher`. Supporting: `platform_admin`, `instructor` (notified).
- **Preconditions:** The item or release is published.
- **Trigger:** The publisher selects "Archive", or a takedown arrives from UC-A-09.
- **Permissions:** `content.release:archive` at workspace scope; `content.item:take_down` for a takedown, which in `master` needs `platform_admin` approval (SoD-11 in 10-rbac-matrix.md).

**Main success flow:**
1. The system shows where the item is used: releases, cohorts, assignments, and derived courses.
2. The publisher archives it. New pins are refused; pinned cohorts keep access until their plans end (BR-130).
3. The system emits `content.release.archived` or `content.item.state_changed` and notifies affected instructors.

**Alternate flows:** A1 (step 2) Takedown. The system removes the item from every release and from retrieval within 1 hour, shows a placeholder, and emits `content.item.taken_down`.

**Exception flows:** E1 (step 2) The item is in an open assignment. Archive waits until it closes; takedown proceeds and the assignment item is voided for all learners.

- **Postconditions:** History is kept. Restore creates a new draft version.
- **References:** BR-130. Requirement area `CST`, `KM`. Release R2.

## 11. Platform and system use cases

### UC-P-01 Provision an account through SSO just in time
- **Goal:** A member of an organisation with SSO gets a managed account on first sign-in, with the right roles.
- **Actors:** Primary: Customer IdP. Supporting: Clerk, `system` (identity service).
- **Preconditions:** An enabled SSO connection with verified domains (UC-O-07).
- **Trigger:** A person enters an email in a verified domain, or launches from the IdP.
- **Permissions:** The `system` principal for identity holds `identity.account:create` limited to tenants with an enabled connection.

**Main success flow:**
1. The system discovers the connection by email domain and redirects through Clerk to the IdP.
2. The IdP authenticates the person and returns an assertion; Clerk verifies it and issues a session.
3. No account exists for the IdP subject. The system creates a `managed` account, an `active` membership, `learner` at organisation scope, and any mapped roles (BR-151).
4. The system emits `identity.account.created` and `tenancy.membership.activated` and opens the app the person requested.

**Alternate flows:** A1 (step 3) The account exists. The system updates names and group-mapped roles from the assertion.

**Exception flows:** E1 (step 3) The email belongs to a personal account. The system does not merge or convert it (BR-106); see OQ-03.

- **Postconditions:** One account per IdP subject in the organisation.
- **References:** BR-105, BR-106, BR-151. Requirement area `IAM`. Release R3.

### UC-P-02 Emit and consume domain events
- **Goal:** Modules react to each other's changes reliably without reading each other's tables.
- **Actors:** Primary: `system` (producer module, outbox relay, consumer module). Supporting: Azure Service Bus.
- **Preconditions:** The producer has a registered event type.
- **Trigger:** A state change in a producer module, for example a lesson completion.
- **Permissions:** Each consumer is a `system` principal subscribed to named event types only.

**Main success flow:**
1. The producer writes the change and an `events.outbox` row in one transaction.
2. The relay publishes the CloudEvents envelope with `tenantid`, `actorid`, and `correlationid` to `domain-events`.
3. A consumer receives it, checks `events.inbox` for the event `id`, processes it, and records the id.
4. The relay marks the outbox row as sent.

**Alternate flows:** A1 (step 3) The consumer has already processed the id. It acknowledges and does nothing.

**Exception flows:** E1 (step 3) Processing fails five times. The message goes to the dead-letter queue and `platform_operator` is alerted.

- **Postconditions:** Every committed change is delivered at least once (BR-149).
- **References:** BR-149. Requirement area `EVT`. Release R1.

### UC-P-03 Compute leaderboards
- **Goal:** Leaderboards at every scope are correct, private where required, and cheap to read.
- **Actors:** Primary: `system` (leaderboard job). Supporting: Gamification Platform.
- **Preconditions:** XP and season points are recorded.
- **Trigger:** `gamification.xp.awarded` events, and a scheduled full recompute every 15 minutes.
- **Permissions:** The job runs as the gamification `system` principal (one function, 10-rbac-matrix.md §2); no role permission applies.

**Main success flow:**
1. The job updates sorted totals for global, country, organisation, cohort, and season scopes.
2. It removes learners who opted out and managed accounts whose organisation withdrew public participation (BR-137).
3. It writes the top 10, ranks, and percentiles per scope, hiding scopes under 5 participants (BR-136).

**Alternate flows:** A1 (step 1) Friends boards are computed when a learner opens them, from the friends' totals.

**Exception flows:** E1 (step 1) An XP reversal (UC-38) arrives. The job recomputes the affected scopes immediately.

- **Postconditions:** Boards are at most 15 minutes old. Guests see only the pseudonymous global top 10.
- **References:** BR-22, BR-135 to BR-139. Requirement area `GAM`. Release R1 (new scopes R2, R3).

### UC-P-04 Generate scheduled reports
- **Goal:** Scheduled reports reach recipients on time, in their locale, with current permissions.
- **Actors:** Primary: `system` (report job). Supporting: Email and push provider.
- **Preconditions:** A schedule exists (UC-O-09, UC-A-08).
- **Trigger:** The schedule's time arrives.
- **Permissions:** The job runs each report as its owner, re-checking `reporting.report:read` at the owner's scope.

**Main success flow:**
1. The job re-evaluates the owner's and recipients' access.
2. It renders the report per recipient locale and applies suppression (BR-150).
3. It stores the file, sends a link that requires sign-in, and emits `reporting.report.generated`.

**Alternate flows:** A1 (step 3) The destination is SFTP or a webhook. The job delivers there and records the delivery.

**Exception flows:** E1 (step 1) The owner lost access. The schedule is paused and the owner's organisation admins are notified.

- **Postconditions:** Files expire after 7 days.
- **References:** BR-150. Requirement area `RPT`. Release R3.

### UC-P-05 Recommend adaptively from the knowledge graph
- **Goal:** Each learner gets a next step that respects prerequisites, mastery, plan dates, and their dimensions (extends UC-13).
- **Actors:** Primary: `system` (Personalisation Engine). Supporting: Knowledge Engine, Learning Delivery.
- **Preconditions:** The learner has mastery evidence or an onboarding result.
- **Trigger:** `learning.mastery.changed`, a new plan item, or the learner opening the dashboard.
- **Permissions:** The engine reads the learner's own data in the active tenant; it never reads another tenant's academic record.

**Main success flow:**
1. The engine gathers due plan items, concepts in the gap band (BR-08), and concepts due for review.
2. It walks `prerequisite_of` edges to find the nearest unmastered prerequisite of each candidate.
3. It ranks: due cohort items first, then prerequisites blocking them, then the personal goal, using the effective dimensions (BR-140).
4. It stores the decision and reason in `personalisation.adaptive_decisions` and returns the top three with explanations.

**Alternate flows:** A1 (step 1) No evidence exists. The engine recommends the start of the learner's path.

**Exception flows:** E1 (step 2) The graph changed since the last decision. Cached decisions are invalidated by `knowledge.concept_relation.changed`.

- **Postconditions:** Recommendations shown and accepted are logged for effectiveness analysis.
- **References:** BR-08, BR-16, BR-140. Requirement area `PER`, `KG`. Release R2.

### UC-P-06 Erase an account according to its account type
- **Goal:** Erasure removes the data the right controller asked to remove, and nothing an organisation must keep.
- **Actors:** Primary: `system` (erasure job). Supporting: Clerk, `org_compliance_officer`, `learner`.
- **Preconditions:** An erasure was requested by the person (personal) or by the organisation (managed, UC-O-11).
- **Trigger:** The request passes its 7-day cancellation period.
- **Permissions:** The job holds `identity.account:erase` at platform scope.

**Main success flow:**
1. The job determines the account type and the records each tenant holds.
2. For a personal account it erases the account, learning record, conversations, uploads, and vectors, and pseudonymises the person in academic records held by organisations (BR-148).
3. For a managed account it erases the account and both records in the organisation, after any passport export.
4. It deletes the Clerk user, emits `identity.account.erased`, and stores a completion record with no personal data.

**Alternate flows:** A1 (step 2) An organisation holds the academic record under a legal hold. Pseudonymisation proceeds; deletion of that record waits for the hold.

**Exception flows:** E1 (step 4) A consumer fails to erase its copy. The job retries and alerts `platform_operator` after 24 hours.

- **Postconditions:** No module retains personal data for the account except under a recorded hold.
- **References:** BR-146 to BR-149. Requirement area `PLT`, `NFR`. Release R1 (managed accounts R3).
---

## 12. Traceability

The tables in [section 5](#5-use-case-map) give, for every use case, the application, the requirement area in 03-srs.md, the service modules, and the release. This view groups the new use cases by release for planning.

| Release | Use cases |
| --- | --- |
| R1 Foundation and Learner MVP | UC-P-02, UC-P-03 (global and country scopes), UC-P-06 (personal accounts); v1 UC-01 to UC-38 as scoped in v1 |
| R2 Public launch and Content Studio | UC-L-06 to UC-L-10, UC-A-02 to UC-A-09, UC-C-01 to UC-C-12, UC-P-05 |
| R3 Classrooms | UC-L-01 to UC-L-05, UC-I-01 to UC-I-14, UC-O-01 to UC-O-07, UC-O-09, UC-O-11, UC-O-12, UC-A-01, UC-A-10, UC-P-01, UC-P-04, UC-P-06 (managed accounts) |
| R4 Enterprise | UC-L-11, UC-O-06 (custom domain), UC-O-08, UC-O-10, UC-O-13, OneRoster in UC-O-04 A1 |
| R5 Ecosystem | None yet. Marketplace, partner API, and agent orchestration use cases follow ADR 0027 |

---

## 13. Open questions

| ID | Question | Proposed answer |
| --- | --- | --- |
| OQ-01 | v1 `UseCases.md` proposed `content_manager`, which the README role mapping does not list. What does it map to? | `content_reviewer`, `content_publisher`, and `knowledge_steward` in `master` |
| OQ-02 | Item bank authoring is a Content Studio workflow (`content`), but `assessment_items` sits in the `assessment` schema. Which module owns authored items? | `content` owns authoring and workflow; `assessment` owns use in assignments. This document uses `content.item:edit` |
| OQ-03 | When an SSO user's email matches an existing personal account, can the person link it as a member instead of getting a managed account, given Clerk's email uniqueness? | Allow linking only if organisation policy permits personal members, with the consent screen of UC-L-01 |
| OQ-04 | Which rules apply to learners under 18 in `school` organisations (leaderboards, persona attributes, consent)? | Default `leaderboards.public_participation` off and persona attributes limited for `school`; needs legal review |
| OQ-05 | Permission contexts `ai.*` and `platform.*` do not match module names `ai_gateway` and `config`. Is the context the module, the schema, or a product area? | Keep the README names; record the context-to-module mapping in 10-rbac-matrix.md |
| OQ-06 | Is cohort membership a `learner` assignment at cohort scope or a `classroom.cohort_members` row? | A row in `classroom.cohort_members` plus `learner` at organisation scope; cohort-scope `learner` only for cohort-only guests |
| OQ-07 | How is delegation to a teaching assistant (override, release) modelled? | A per-cohort delegation grant in `classroom.cohort_staff`, checked as an ABAC relationship |
| OQ-08 | Do season points count towards the daily XP cap (BR-03)? | No. Season points have their own daily cap set per season |
